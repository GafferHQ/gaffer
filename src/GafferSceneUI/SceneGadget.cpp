//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//      * Redistributions of source code must retain the above
//        copyright notice, this list of conditions and the following
//        disclaimer.
//
//      * Redistributions in binary form must reproduce the above
//        copyright notice, this list of conditions and the following
//        disclaimer in the documentation and/or other materials provided with
//        the distribution.
//
//      * Neither the name of John Haddon nor the names of
//        any other contributors to this software may be used to endorse or
//        promote products derived from this software without specific prior
//        written permission.
//
//  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
//  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
//  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
//  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
//  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
//  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
//  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
//  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
//  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
//  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
//  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
//
//////////////////////////////////////////////////////////////////////////

#include "GafferSceneUI/SceneGadget.h"

#include "GafferUI/ViewportGadget.h"

#include "GafferScene/Private/IECoreScenePreview/CompoundRenderer.h"
#include "GafferScene/SceneAlgo.h"

#include "Gaffer/BackgroundTask.h"

#include "boost/bind/bind.hpp"
#include "boost/bind/placeholders.hpp"

#include "tbb/enumerable_thread_specific.h"

#include <math.h>

using namespace std;
using namespace boost::placeholders;
using namespace Imath;
using namespace IECore;
using namespace IECoreGL;
using namespace Gaffer;
using namespace GafferUI;
using namespace GafferScene;
using namespace GafferSceneUI;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

/// \todo Could this find a home in SceneAlgo?
Box3f sceneBound( const ScenePlug *scene, const PathMatcher *include, const PathMatcher *exclude )
{
	tbb::enumerable_thread_specific<Box3f> threadBounds;

	auto f = [&exclude, &threadBounds] ( const ScenePlug *scene, const ScenePlug::ScenePath &path ) {

		const unsigned m = exclude ? exclude->match( path ) : (unsigned)PathMatcher::NoMatch;
		if( m & PathMatcher::ExactMatch )
		{
			// Stop traversal to omit this location and all its descendants.
			return false;
		}
		else if( m & PathMatcher::DescendantMatch )
		{
			// We'll be excluding a descendant, so can't take the bound at
			// this point, but do want to continue traversal to get the
			// bounds of the non-excluded descendants.
			return true;
		}
		else
		{
			// Not excluding. Get the bound for this location (which will include
			// its descendants) and prune traversal.
			Box3f bound = scene->boundPlug()->getValue();
			bound = transform( bound, scene->fullTransform( path ) );
			threadBounds.local().extendBy( bound );
			return false;
		}
	};

	if( include )
	{
		SceneAlgo::filteredParallelTraverse( scene, *include, f );
	}
	else
	{
		SceneAlgo::parallelTraverse( scene, f );
	}

	return threadBounds.combine(
		[] ( const Box3f b1, const Box3f b2 ) {
			Box3f bc;
			bc.extendBy( b1 );
			bc.extendBy( b2 );
			return bc;
		}
	);
}

vector<IECore::TypeId> typeIdsFromTypeNames( const vector<string> &typeNames )
{
	vector<IECore::TypeId> typeIds;
	for( auto &typeName : typeNames )
	{
		typeIds.push_back( RunTimeTyped::typeIdFromTypeName( typeName.c_str() ) );
	}
	return typeIds;
}

bool isObjectInstanceOf( const ScenePlug *scene, const vector<IECore::TypeId> &typeIds )
{
	/// \todo In an ideal world we'd be able to determine object type without loading
	/// the whole object. Perhaps a `ScenePlug::objectTypePlug()` could be useful?
	const IECore::TypeId objectType = scene->objectPlug()->getValue()->typeId();
	for( auto typeId : typeIds )
	{
		if( typeId == objectType || RunTimeTyped::inheritsFrom( objectType, typeId ) )
		{
			return true;
		}
	}
	return false;
}

PathMatcher findTypedObjects( const ScenePlug *scene, const PathMatcher &paths, const vector<string> &typeNames )
{
	tbb::enumerable_thread_specific<PathMatcher> threadResults;

	vector<IECore::TypeId> typeIds = typeIdsFromTypeNames( typeNames );

	auto f = [&typeIds, &threadResults] ( const ScenePlug *scene, const ScenePlug::ScenePath &path ) {
		if( isObjectInstanceOf( scene, typeIds ) )
		{
			threadResults.local().addPath( path );
		}
		return true;
	};

	SceneAlgo::filteredParallelTraverse( scene, paths, f );

	return threadResults.combine(
		[] ( const PathMatcher &a, const PathMatcher &b ) {
			PathMatcher c = a;
			c.addPaths( b );
			return c;
		}
	);
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// SceneGadget implementation
//////////////////////////////////////////////////////////////////////////

namespace
{

const ConstStringDataPtr g_cameraName = new StringData( "/__sceneGadget:camera" );
const IECore::StringDataPtr g_sceneColorSpace = new StringData( "scene" );
const IECore::StringDataPtr g_displayColorSpace = new StringData( "display" );

} // namespace

SceneGadget::SceneGadget()
	:	Gadget( defaultName<SceneGadget>() ),
		m_paused( false ),
		m_updateErrored( false ),
		m_renderRequestPending( false ),
		m_layer( Gadget::Layer::Main )
{
	using Option = CompoundObject::ObjectMap::value_type;
	CompoundObjectPtr openGLOptions = new CompoundObject;
	openGLOptions->members().insert( {
		Option( "gl:primitive:wireframeColor", new Color4fData( Color4f( 0.2f, 0.2f, 0.2f, 1.0f ) ) ),
		Option( "gl:primitive:pointColor", new Color4fData( Color4f( 0.9f, 0.9f, 0.9f, 1.0f ) ) ),
		Option( "gl:primitive:pointWidth", new FloatData( 2.0f ) )
	} );
	m_openGLOptions = openGLOptions;

	visibilityChangedSignal().connect( boost::bind( &SceneGadget::visibilityChanged, this ) );

	setRenderer( "OpenGL" );
	setContext( new Context );
}

SceneGadget::~SceneGadget()
{
	// Make sure background task completes before anything
	// it relies on is destroyed.
	m_updateTask.reset();
	// Then destroy controller and renderer before our OutputBuffer is
	// destroyed, because the renderer might send pixels to it during shutdown.
	m_controller.reset();
	m_camera.reset();
	m_renderer.reset();
}

void SceneGadget::setScene( GafferScene::ConstScenePlugPtr scene )
{
	m_controller->setScene( scene );
}

const GafferScene::ScenePlug *SceneGadget::getScene() const
{
	return m_controller->getScene();
}

void SceneGadget::setContext( Gaffer::ConstContextPtr context )
{
	m_controller->setContext( context );
}

const Gaffer::Context *SceneGadget::getContext() const
{
	return m_controller->getContext();
}

void SceneGadget::setVisibleSet( const GafferScene::VisibleSet &visibleSet )
{
	m_controller->setVisibleSet( visibleSet );
}

const GafferScene::VisibleSet &SceneGadget::getVisibleSet() const
{
	return m_controller->getVisibleSet();
}

void SceneGadget::setMinimumExpansionDepth( size_t depth )
{
	m_controller->setMinimumExpansionDepth( depth );
}

size_t SceneGadget::getMinimumExpansionDepth() const
{
	return m_controller->getMinimumExpansionDepth();
}

void SceneGadget::setPaused( bool paused )
{
	if( paused == m_paused )
	{
		return;
	}

	m_paused = paused;
	if( m_paused )
	{
		if( m_updateTask )
		{
			m_updateTask->cancelAndWait();
			m_updateTask.reset();
		}
		stateChangedSignal()( this );
	}
	else if( m_controller->updateRequired() )
	{
		dirty( DirtyType::Bound );
	}
}

bool SceneGadget::getPaused() const
{
	return m_paused;
}

void SceneGadget::setBlockingPaths( const IECore::PathMatcher &blockingPaths )
{
	if( m_updateTask )
	{
		m_updateTask->cancelAndWait();
		m_updateTask.reset();
	}
	m_blockingPaths = blockingPaths;
	dirty( DirtyType::Bound );
}

const IECore::PathMatcher &SceneGadget::getBlockingPaths() const
{
	return m_blockingPaths;
}

void SceneGadget::setPriorityPaths( const IECore::PathMatcher &priorityPaths )
{
	if( m_updateTask )
	{
		m_updateTask->cancelAndWait();
		m_updateTask.reset();
	}
	m_priorityPaths = priorityPaths;
	dirty( DirtyType::Bound );
}

const IECore::PathMatcher &SceneGadget::getPriorityPaths() const
{
	return m_priorityPaths;
}

SceneGadget::State SceneGadget::state() const
{
	if( m_paused )
	{
		return Paused;
	}

	return m_controller->updateRequired() ? Running : Complete;
}

SceneGadget::SceneGadgetSignal &SceneGadget::stateChangedSignal()
{
	return m_stateChangedSignal;
}

void SceneGadget::waitForCompletion()
{
	updateRenderer();
	if( m_updateTask )
	{
		m_updateTask->wait();
	}
}

void SceneGadget::setRenderer( IECore::InternedString name )
{
	if( name == m_rendererName )
	{
		return;
	}

	// Cancel any updates/renders we're currently doing.

	cancelUpdateAndPauseRenderer();

	// Make new renderer, controller and output buffer.

	m_rendererName = name;
	IECoreScenePreview::RendererPtr newRenderer;
	std::unique_ptr<OutputBuffer> newOutputBuffer;
	if( m_rendererName == "OpenGL" )
	{
		newRenderer = IECoreScenePreview::Renderer::create( m_rendererName, IECoreScenePreview::Renderer::Interactive );
	}
	else
	{
		newRenderer = new IECoreScenePreview::CompoundRenderer( {
			IECoreScenePreview::Renderer::create( "OpenGL", IECoreScenePreview::Renderer::Interactive ),
			IECoreScenePreview::Renderer::create( m_rendererName, IECoreScenePreview::Renderer::Interactive ),
		} );
		ConstBoolDataPtr renderObjectsData = new BoolData( false );
		newRenderer->option( "gl:renderObjects", renderObjectsData.get() );
		newOutputBuffer = std::make_unique<OutputBuffer>( newRenderer.get() );
		newOutputBuffer->bufferChangedSignal().connect( boost::bind( &SceneGadget::bufferChanged, this ) );
	}

	auto newController = std::make_unique<RenderController>(
		m_controller ? m_controller->getScene() : nullptr,
		m_controller ? m_controller->getContext() : nullptr,
		newRenderer
	);

	if( m_controller )
	{
		newController->setVisibleSet( m_controller->getVisibleSet() );
		newController->setMinimumExpansionDepth( m_controller->getMinimumExpansionDepth() );
	}

	// Replace old controller and renderer, being careful to delete controller
	// and camera first, since ObjectInterfaces must be deleted _before_ the
	// renderer. We must also be careful to delete the old OutputBuffer after
	// the old renderer, as the renderer may send pixels during destruction.

	m_controller = std::move( newController );
	m_camera.reset();
	m_renderer = newRenderer;
	m_outputBuffer = std::move( newOutputBuffer );

	m_controller->updateRequiredSignal().connect(
		boost::bind( &SceneGadget::dirty, this, DirtyType::Layout )
	);

	// Give our OpenGL options, selection and viewport camera to the new
	// renderer.

	setSelection( getSelection() );

	ConstCompoundObjectPtr openGLOptions = getOpenGLOptions();
	m_openGLOptions = nullptr; // Force update
	setOpenGLOptions( openGLOptions.get() );

	if( ancestor<ViewportGadget>() )
	{
		updateCamera( ViewportGadget::CameraFlags::All );
	}
}

IECore::InternedString SceneGadget::getRenderer()
{
	return m_rendererName;
}

void SceneGadget::setOpenGLOptions( const IECore::CompoundObject *options )
{
	if( m_openGLOptions && *m_openGLOptions == *options )
	{
		return;
	}

	// Output anything that has changed or was added

	for( const auto &option : options->members() )
	{
		bool changedOrAdded = true;
		if( m_openGLOptions )
		{
			if( const Object *previousOption = m_openGLOptions->member<Object>( option.first ) )
			{
				changedOrAdded = *previousOption != *option.second;
			}
		}
		if( changedOrAdded )
		{
			m_renderer->option( option.first, option.second.get() );
		}
	}

	// Remove anything that was removed

	if( m_openGLOptions )
	{
		for( const auto &oldOption : m_openGLOptions->members() )
		{
			if( !options->member<Object>( oldOption.first ) )
			{
				m_renderer->option( oldOption.first, nullptr );
			}
		}
	}

	m_openGLOptions = options->copy();
	dirty( DirtyType::Bound );
}

const IECore::CompoundObject *SceneGadget::getOpenGLOptions() const
{
	return m_openGLOptions.get();
}

void SceneGadget::setLayer( Gadget::Layer layer )
{
	if( layer == m_layer )
	{
		return;
	}
	m_layer = layer;
	dirty( DirtyType::Render );
}

Gadget::Layer SceneGadget::getLayer() const
{
	return m_layer;
}

void SceneGadget::setSelectionMask( const IECore::StringVectorData *typeNames )
{
	m_selectionMask = typeNames ? typeNames->copy() : nullptr;
}

const IECore::StringVectorData *SceneGadget::getSelectionMask() const
{
	return m_selectionMask.get();
}

bool SceneGadget::objectAt( const IECore::LineSegment3f &lineInGadgetSpace, GafferScene::ScenePlug::ScenePath &path ) const
{
	V3f unused;
	return objectAt( lineInGadgetSpace, path, unused );
}

bool SceneGadget::objectAt( const IECore::LineSegment3f &lineInGadgetSpace, GafferScene::ScenePlug::ScenePath &path, V3f &hitPoint ) const
{
	if( m_updateErrored )
	{
		return false;
	}

	float depth = std::numeric_limits<float>::max();
	bool hit = openGLObjectAt( lineInGadgetSpace, path, depth );

	auto viewportGadget = ancestor<ViewportGadget>();
	if( m_outputBuffer )
	{
		const V2f rasterPosition = viewportGadget->gadgetToRasterSpace( lineInGadgetSpace.p1, this );
		float bufferDepth;
		if( uint32_t id = m_outputBuffer->idAt( rasterPosition / viewportGadget->getViewport(), bufferDepth ) )
		{
			if( bufferDepth < depth )
			{
				if( auto bufferPath = m_controller->pathForID( id ) )
				{
					if( m_selectionMask )
					{
						ScenePlug::PathScope pathScope( getContext(), &*bufferPath );
						if( !isObjectInstanceOf( getScene(), typeIdsFromTypeNames( m_selectionMask->readable() ) ) )
						{
							return false;
						}
					}
					depth = bufferDepth;
					path = *bufferPath;
					hit = true;
				}
			}
		}
	}

	if( !hit )
	{
		return false;
	}

	V3f viewDir;
	const M44f cameraWorldTransform = viewportGadget->getCameraTransform();
	const M44f cameraTransform = cameraWorldTransform * fullTransform().inverse();
	cameraTransform.multDirMatrix( V3f( 0.0f, 0.0f, -1.0f ), viewDir );

	const V3f traceDir = lineInGadgetSpace.normalizedDirection();

	depth /= max( 0.00001f, viewDir.dot( traceDir ) );

	const V3f origin = V3f( 0.0f ) * cameraTransform;
	hitPoint = origin + ( traceDir * depth );

	return true;
}

bool SceneGadget::openGLObjectAt( const IECore::LineSegment3f &lineInGadgetSpace, GafferScene::ScenePlug::ScenePath &path, float &depth ) const
{
	std::vector<IECoreGL::HitRecord> selection;
	{
		ViewportGadget::SelectionScope selectionScope( lineInGadgetSpace, this, selection, IECoreGL::Selector::IDRender );

		IECore::CompoundDataMap parameters;
		parameters["colorSpace"] = g_sceneColorSpace;
		m_renderer->command( "gl:renderToCurrentContext", parameters );
		parameters["colorSpace"] = g_displayColorSpace;
		m_renderer->command( "gl:renderToCurrentContext", parameters );
	}

	if( !selection.size() )
	{
		return false;
	}

	float depthMin = selection[0].depthMin;
	unsigned int name = selection[0].name;
	for( const auto &i : selection )
	{
		if( i.depthMin < depthMin )
		{
			depthMin = i.depthMin;
			name = i.name;
		}
	}

	PathMatcher paths = convertSelection( new UIntVectorData( { name } ) );
	if( paths.isEmpty() )
	{
		return false;
	}

	path = *PathMatcher::Iterator( paths.begin() );
	depth = ( selection[0].depthMin + selection[0].depthMax ) * 0.5f;

	return true;
}

size_t SceneGadget::objectsAt(
	const Imath::V3f &corner0InGadgetSpace,
	const Imath::V3f &corner1InGadgetSpace,
	IECore::PathMatcher &paths
) const
{
	if( m_updateErrored )
	{
		return false;
	}

	vector<IECoreGL::HitRecord> selection;
	{
		ViewportGadget::SelectionScope selectionScope( corner0InGadgetSpace, corner1InGadgetSpace, this, selection, IECoreGL::Selector::OcclusionQuery );
		IECore::CompoundDataMap parameters;
		parameters["colorSpace"] = g_sceneColorSpace;
		m_renderer->command( "gl:renderToCurrentContext", parameters );
		parameters["colorSpace"] = g_displayColorSpace;
		m_renderer->command( "gl:renderToCurrentContext", parameters );
	}

	UIntVectorDataPtr ids = new UIntVectorData;
	std::transform(
		selection.begin(), selection.end(), std::back_inserter( ids->writable() ),
		[]( const IECoreGL::HitRecord &h ) { return h.name; }
	);

	PathMatcher selectedPaths = convertSelection( ids );
	paths.addPaths( selectedPaths );

	if( m_outputBuffer )
	{
		auto viewportGadget = ancestor<ViewportGadget>();
		Box2f ndcBox;
		ndcBox.extendBy( viewportGadget->gadgetToRasterSpace( corner0InGadgetSpace, this ) / viewportGadget->getViewport() );
		ndcBox.extendBy( viewportGadget->gadgetToRasterSpace( corner1InGadgetSpace, this ) / viewportGadget->getViewport() );
		PathMatcher bufferPaths = m_controller->pathsForIDs( m_outputBuffer->idsAt( ndcBox ) );
		if( m_selectionMask )
		{
			Context::Scope scope( getContext() );
			bufferPaths = findTypedObjects( getScene(), bufferPaths, m_selectionMask->readable() );
		}
		paths.addPaths( bufferPaths );
	}

	return paths.size();
}

std::optional<V3f> SceneGadget::normalAt( const IECore::LineSegment3f &lineInGadgetSpace ) const
{
	V3f centerP;
	ScenePlug::ScenePath centerPath;

	auto viewportGadget = ancestor<ViewportGadget>();

	// Transforming from raster to gadget space (done by `Widget`) and back to raster space
	// can introduce enough floating point error to make positions, and therefore normals,
	// incorrect. We expect that `lineInGadgetSpace` corresponds to the center of a pixel,
	// so we snap to the nearest center as a corrective.
	V2f centerRasterP = viewportGadget->gadgetToRasterSpace( lineInGadgetSpace.p0, this );
	centerRasterP.x = (int)centerRasterP.x + 0.5f;
	centerRasterP.y = (int)centerRasterP.y + 0.5f;

	if( objectAt( viewportGadget->rasterToGadgetSpace( centerRasterP, this ), centerPath, centerP ) )
	{
		// Find the average normal of the triangles formed by `pixelPosition` and
		// left + top, right + top, left + bottom and right + bottom depth samples
		// where each pair has the same object ID as the center pixel.

		const float spread = 1.f;

		int sampleCount = 0;
		V3f gadgetNormal( 0 );

		ScenePlug::ScenePath prevPath;
		V3f prevP;
		bool prevHit = objectAt(
			viewportGadget->rasterToGadgetSpace( centerRasterP + V2f( -spread, 0 ), this ),
			prevPath,
			prevP
		);

		std::array<V2f, 4> offsetList{
			V2f( 0, -spread ),
			V2f( spread, 0 ),
			V2f( 0, spread ),
			V2f( -spread, 0 )  // wrap back to left for final comparison
		};

		for( const auto &offset : offsetList )
		{
			V2f rasterP = centerRasterP + offset;
			ScenePlug::ScenePath hitPath;
			V3f hitP;
			bool hit = objectAt( viewportGadget->rasterToGadgetSpace( rasterP, this ), hitPath, hitP );

			if( hit && prevHit && prevPath == centerPath && hitPath == centerPath )
			{
				gadgetNormal += ( hitP - centerP ).cross( prevP - centerP ).normalized();
				sampleCount++;
			}

			prevPath = hitPath;
			prevP = hitP;
			prevHit = hit;
		}

		if( sampleCount > 0 )
		{
			gadgetNormal /= sampleCount;
			return gadgetNormal;
		}
	}

	return std::nullopt;
}

IECore::PathMatcher SceneGadget::convertSelection( IECore::UIntVectorDataPtr ids ) const
{
	CompoundDataMap parameters = { { "selection", ids } };
	if( m_selectionMask )
	{
		parameters["mask"] = m_selectionMask;
	}

	auto pathsData = static_pointer_cast<PathMatcherData>(
		m_renderer->command(
			"gl:querySelection",
			parameters
		)
	);

	PathMatcher result = pathsData->readable();

	// Unexpanded locations are represented with
	// objects named __unexpandedChildren__ to allow
	// locations to have an object _and_ children.
	// We want to replace any such locations with their
	// parent location.
	const InternedString unexpandedChildren = "__unexpandedChildren__";
	vector<InternedString> parent;

	PathMatcher toAdd;
	PathMatcher toRemove;
	for( PathMatcher::Iterator it = result.begin(), eIt = result.end(); it != eIt; ++it )
	{
		if( it->size() && it->back() == unexpandedChildren )
		{
			toRemove.addPath( *it );
			parent.assign( it->begin(), it->end() - 1 );
			toAdd.addPath( parent );
		}
	}

	result.addPaths( toAdd );
	result.removePaths( toRemove );

	return result;
}

const IECore::PathMatcher &SceneGadget::getSelection() const
{
	return m_selection;
}

void SceneGadget::setSelection( const IECore::PathMatcher &selection )
{
	m_selection = selection;
	ConstDataPtr d = new IECore::PathMatcherData( selection );
	m_renderer->option( "gl:selection", d.get() );
	if( m_outputBuffer )
	{
		m_outputBuffer->setSelection( m_controller->idsForPaths( selection, /* createIfMissing = */ true ) );
	}
	dirty( DirtyType::Render );
}

Imath::Box3f SceneGadget::selectionBound() const
{
	return bound( true, nullptr );
}

Imath::Box3f SceneGadget::bound( bool selected, const PathMatcher *userOmitted ) const
{
	if( m_updateErrored )
	{
		return Box3f();
	}

	// We never want to include the bounds for the camera we make
	// ourselves.

	PathMatcher omitted;
	if( userOmitted )
	{
		omitted.addPaths( *userOmitted );
	}
	omitted.addPath( g_cameraName->readable() );

	// Get bounds from OpenGL renderer. This gives us the bounds for any
	// visualisations, and when it is the sole renderer it also gets the scene
	// bounds cheaply, without any need to perform computations.

	ConstDataPtr d = m_renderer->command( "gl:queryBound", { { "selection", new BoolData( selected ) }, { "omitted", new PathMatcherData( omitted ) } } );
	Box3f result = static_cast<const Box3fData *>( d.get() )->readable();

	// If we're using another renderer as well, then the GL renderer won't have
	// bounds for any expanded geometry. There's no way to query bounds from the
	// other renderer, so we resort to computing bounds from the scene itself.

	if( m_rendererName != "OpenGL" )
	{
		Context::Scope scope( getContext() );
		result.extendBy( sceneBound( getScene(), selected ? &m_selection : nullptr, &omitted ) );
	}

	return result;
}

std::string SceneGadget::getToolTip( const IECore::LineSegment3f &line ) const
{
	std::string result = Gadget::getToolTip( line );
	if( result.size() )
	{
		return result;
	}

	ScenePlug::ScenePath path;
	if( objectAt( line, path ) )
	{
		ScenePlug::pathToString( path, result );
	}

	return result;
}

Imath::Box3f SceneGadget::bound() const
{
	return bound( /* selection = */ false );
}

void SceneGadget::snapshotToFile(
	const std::filesystem::path &fileName,
	const Box2f &resolutionGate,
	const CompoundData *metadata
) const
{
	if( !m_outputBuffer )
	{
		return;
	}

	m_outputBuffer->snapshotToFile( fileName, resolutionGate, metadata );
}

void SceneGadget::renderLayer( Layer layer, const GafferUI::Style *style, RenderReason reason ) const
{
	assert( layer == m_layer || layer == Layer::MidFront );

	if( isSelectionRender( reason ) )
	{
		return;
	}

	const_cast<SceneGadget *>( this )->updateRenderer();
	if( m_updateErrored )
	{
		return;
	}

	if( m_outputBuffer )
	{
		if( layer == m_layer )
		{
			m_outputBuffer->render();
		}
		else
		{
			// Selection is rendered as an overlay so that it isn't
			// affected by the display transform and solo channel.
			m_outputBuffer->renderSelection();
		}
	}

	IECore::CompoundDataMap parameters;
	parameters["colorSpace"] = layer == m_layer ? g_sceneColorSpace : g_displayColorSpace;
	m_renderer->command( "gl:renderToCurrentContext", parameters );
}

unsigned SceneGadget::layerMask() const
{
	return m_layer | Layer::MidFront;
}

Imath::Box3f SceneGadget::renderBound() const
{
	// The SceneGadget can render things outside it's layout, such as a Camera frustum, so it
	// needs an infinite render bound
	Box3f b;
	b.makeInfinite();
	return b;
}

void SceneGadget::updateRenderer()
{
	if( m_paused )
	{
		return;
	}

	if( m_updateTask )
	{
		if( m_updateTask->status() == BackgroundTask::Running )
		{
			return;
		}
		m_updateTask.reset();
	}

	if( !m_controller->updateRequired() )
	{
		return;
	}

	auto progressCallback = [this] ( BackgroundTask::Status progress ) {

		if( !refCount() )
		{
			return;
		}

		if( progress == BackgroundTask::Completed )
		{
			// Start render now, rather than on UI thread, to avoid latency.
			// We want pixels to be available as soon as possible.
			if( m_camera )
			{
				m_renderer->option( "camera", g_cameraName.get() );
				m_renderer->render();
			}
		}

		bool shouldRequestRender = !m_renderRequestPending.exchange( true );
		bool shouldEmitStateChange =
			progress == BackgroundTask::Completed ||
			progress == BackgroundTask::Errored
		;

		if( shouldRequestRender || shouldEmitStateChange )
		{
			// Must hold a reference to stop us dying before our UI thread call is scheduled.
			SceneGadgetPtr thisRef = this;
			ParallelAlgo::callOnUIThread(
				[thisRef, shouldRequestRender, shouldEmitStateChange, progress] {
					if( progress == BackgroundTask::Errored )
					{
						thisRef->m_updateErrored = true;
					}
					if( shouldEmitStateChange )
					{
						thisRef->stateChangedSignal()( thisRef.get() );
					}
					if( shouldRequestRender )
					{
						thisRef->m_renderRequestPending = false;
						thisRef->dirty( DirtyType::Bound );
					}
				}
			);
		}

	};

	m_renderer->pause();

	if( !m_blockingPaths.isEmpty() )
	{
		try
		{
			m_controller->updateMatchingPaths( m_blockingPaths );
		}
		catch( std::exception & )
		{
			// Leave it to the rest of the UI to report the error.
			m_updateErrored = true;
		}
	}

	m_updateErrored = false;
	m_updateTask = m_controller->updateInBackground( progressCallback, m_priorityPaths );
	stateChangedSignal()( this );

	// Give ourselves a 0.1s grace period in which we block
	// the UI while our updates occur. This means that for reasonably
	// interactive animation or manipulation, we only show the final
	// result, rathen than a series of partial intermediate results.
	// It also prevents a "cancellation storm" where new UI events
	// cancel our background updates faster than we can show them.
	m_updateTask->waitFor( 0.1 );
}

void SceneGadget::updateCamera( GafferUI::ViewportGadget::CameraFlags changes )
{
	cancelUpdateAndPauseRenderer();

	const ViewportGadget *viewport = ancestor<ViewportGadget>();

	if( !m_camera || static_cast<bool>( changes & ViewportGadget::CameraFlags::Camera ) )
	{
		m_camera.reset();
		m_camera = m_renderer->camera( g_cameraName->readable(), viewport->getCamera().get() );
		changes |= ViewportGadget::CameraFlags::Transform;
	}

	if( static_cast<bool>( changes & ViewportGadget::CameraFlags::Transform ) )
	{
		m_camera->transform( viewport->getCameraTransform() );
	}

	if( !m_controller->updateRequired() )
	{
		m_renderer->render();
	}
	else
	{
		// Render will be started by next update
	}
}

void SceneGadget::bufferChanged()
{
	if( !refCount() )
	{
		// We're in the process of destruction, receiving the
		// final pixels while waiting for the renderer to be
		// destroyed.
		return;
	}

	// Using `thisRef` to stop us dying before our UI thread call is scheduled.
	ParallelAlgo::callOnUIThread(
		[thisRef = Ptr( this )] {
			thisRef->Gadget::dirty( DirtyType::Render );
		}
	);
}

void SceneGadget::visibilityChanged()
{
	m_viewportChangedConnection.disconnect();
	m_viewportCameraChangedConnection.disconnect();
	if( visible() )
	{
		if( auto viewport = ancestor<ViewportGadget>() )
		{
			m_viewportChangedConnection = viewport->viewportChangedSignal().connect(
				boost::bind( &SceneGadget::updateCamera, this, ViewportGadget::CameraFlags::Camera )
			);
			m_viewportCameraChangedConnection = viewport->cameraChangedSignal().connect(
				boost::bind( &SceneGadget::updateCamera, this, ::_2 )
			);
		}
	}
	else
	{
		cancelUpdateAndPauseRenderer();
	}
}

void SceneGadget::cancelUpdateAndPauseRenderer()
{
	if( m_updateTask )
	{
		m_updateTask->cancelAndWait();
	}
	if( m_renderer )
	{
		m_renderer->pause();
	}
}
