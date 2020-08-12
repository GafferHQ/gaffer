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

#include "Gaffer/BackgroundTask.h"

#include "boost/bind.hpp"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferUI;
using namespace GafferScene;
using namespace GafferSceneUI;

namespace
{
	float lineariseDepthBufferSample( float bufferDepth, float *m )
	{
		// Heavily optimised extraction that works with our orthogonal clipping planes
		//   Fast Extraction of Viewing Frustum Planes from the WorldView-Projection Matrix
		//   http://www.cs.otago.ac.nz/postgrads/alexis/planeExtraction.pdf
		const float n = - ( m[15] + m[14] ) / ( m[11] + m[10] );
		const float f = - ( m[15] - m[14] ) / ( m[11] - m[10] );
		return ( 2.0f * n * f ) / ( f + n - ( bufferDepth * 2.0f - 1.0f ) * ( f - n ) );
	}
}

//////////////////////////////////////////////////////////////////////////
// SceneGadget implementation
//////////////////////////////////////////////////////////////////////////

SceneGadget::SceneGadget()
	:	Gadget( defaultName<SceneGadget>() ),
		m_paused( false ),
		m_renderer( IECoreScenePreview::Renderer::create( "OpenGL", IECoreScenePreview::Renderer::Interactive ) ),
		m_controller( nullptr, nullptr, m_renderer ),
		m_updateErrored( false ),
		m_renderRequestPending( false )
{
	typedef CompoundObject::ObjectMap::value_type Option;
	CompoundObjectPtr openGLOptions = new CompoundObject;
	openGLOptions->members().insert( {
		Option( "gl:primitive:wireframeColor", new Color4fData( Color4f( 0.2f, 0.2f, 0.2f, 1.0f ) ) ),
		Option( "gl:primitive:pointColor", new Color4fData( Color4f( 0.9f, 0.9f, 0.9f, 1.0f ) ) ),
		Option( "gl:primitive:pointWidth", new FloatData( 2.0f ) )
	} );
	setOpenGLOptions( openGLOptions.get() );

	m_controller.updateRequiredSignal().connect(
		boost::bind( &SceneGadget::requestRender, this )
	);

	visibilityChangedSignal().connect( boost::bind( &SceneGadget::visibilityChanged, this ) );

	setContext( new Context );
}

SceneGadget::~SceneGadget()
{
	// Make sure background task completes before anything
	// it relies on is destroyed.
	m_updateTask.reset();
}

void SceneGadget::setScene( GafferScene::ConstScenePlugPtr scene )
{
	m_controller.setScene( scene );
}

const GafferScene::ScenePlug *SceneGadget::getScene() const
{
	return m_controller.getScene();
}

void SceneGadget::setContext( Gaffer::ConstContextPtr context )
{
	m_controller.setContext( context );
}

const Gaffer::Context *SceneGadget::getContext() const
{
	return m_controller.getContext();
}

void SceneGadget::setExpandedPaths( const IECore::PathMatcher &expandedPaths )
{
	m_controller.setExpandedPaths( expandedPaths );
}

const IECore::PathMatcher &SceneGadget::getExpandedPaths() const
{
	return m_controller.getExpandedPaths();
}

void SceneGadget::setMinimumExpansionDepth( size_t depth )
{
	m_controller.setMinimumExpansionDepth( depth );
}

size_t SceneGadget::getMinimumExpansionDepth() const
{
	return m_controller.getMinimumExpansionDepth();
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
	else if( m_controller.updateRequired() )
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

	return m_controller.updateRequired() ? Running : Complete;
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
	float projectionMatrix[16];

	std::vector<IECoreGL::HitRecord> selection;
	{
		ViewportGadget::SelectionScope selectionScope( lineInGadgetSpace, this, selection, IECoreGL::Selector::IDRender );
		//  Fetch the matrix so we can work out our clipping planes to extract
		//  a real-world depth from the buffer. We do this here in case
		//  SelectionScope ever affects the matrix/planes.
		glGetFloatv( GL_PROJECTION_MATRIX, projectionMatrix );
		renderScene();
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

	// Notes:
	//  - depthMin is in respect to +ve z, we're looking down -z, so we need to invert it.
	//  - depthMin is orthogonal to the camera's xy plane not from its origin.
	//  - There may be intermediate transforms between us and the ViewportGadget.

	V3f viewDir;
	const M44f cameraWorldTransform = ancestor<ViewportGadget>()->getCameraTransform();
	const M44f cameraTransform = cameraWorldTransform * fullTransform().inverse();
	cameraTransform.multDirMatrix( V3f( 0.0f, 0.0f, -1.0f ), viewDir );

	const V3f traceDir = lineInGadgetSpace.normalizedDirection();

	float hitDepth = - lineariseDepthBufferSample( depthMin, projectionMatrix );
	hitDepth /= max( 0.00001f, viewDir.dot( traceDir ) );

	const V3f origin = V3f( 0.0f ) * cameraTransform;
	hitPoint = origin + ( traceDir * hitDepth );

	return true;
}

size_t SceneGadget::objectsAt(
	const Imath::V3f &corner0InGadgetSpace,
	const Imath::V3f &corner1InGadgetSpace,
	IECore::PathMatcher &paths
) const
{

	vector<IECoreGL::HitRecord> selection;
	{
		ViewportGadget::SelectionScope selectionScope( corner0InGadgetSpace, corner1InGadgetSpace, this, selection, IECoreGL::Selector::OcclusionQuery );
		renderScene();
	}

	UIntVectorDataPtr ids = new UIntVectorData;
	std::transform(
		selection.begin(), selection.end(), std::back_inserter( ids->writable() ),
		[]( const IECoreGL::HitRecord &h ) { return h.name; }
	);

	PathMatcher selectedPaths = convertSelection( ids );
	paths.addPaths( selectedPaths );

	return selectedPaths.size();
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
	dirty( DirtyType::Render );
}

Imath::Box3f SceneGadget::selectionBound() const
{
	DataPtr d = m_renderer->command( "gl:queryBound", { { "selection", new BoolData( true ) } } );
	return static_cast<Box3fData *>( d.get() )->readable();
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
	if( m_updateErrored )
	{
		return Box3f();
	}
	DataPtr d = m_renderer->command( "gl:queryBound" );
	return static_cast<Box3fData *>( d.get() )->readable();
}

void SceneGadget::doRenderLayer( Layer layer, const GafferUI::Style *style ) const
{
	if( layer != Layer::Main )
	{
		return;
	}

	if( IECoreGL::Selector::currentSelector() )
	{
		return;
	}

	const_cast<SceneGadget *>( this )->updateRenderer();
	renderScene();
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

	if( !m_controller.updateRequired() )
	{
		return;
	}

	auto progressCallback = [this] ( BackgroundTask::Status progress ) {

		if( !refCount() )
		{
			return;
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

	if( !m_blockingPaths.isEmpty() )
	{
		try
		{
			m_controller.updateMatchingPaths( m_blockingPaths );
		}
		catch( std::exception &e )
		{
			// Leave it to the rest of the UI to report the error.
			m_updateErrored = true;
		}
	}

	m_updateErrored = false;
	m_updateTask = m_controller.updateInBackground( progressCallback, m_priorityPaths );
	stateChangedSignal()( this );

	// Give ourselves a 0.1s grace period in which we block
	// the UI while our updates occur. This means that for reasonably
	// interactive animation or manipulation, we only show the final
	// result, rathen than a series of partial intermediate results.
	// It also prevents a "cancellation storm" where new UI events
	// cancel our background updates faster than we can show them.
	m_updateTask->waitFor( 0.1 );
}

void SceneGadget::renderScene() const
{
	if( m_updateErrored )
	{
		return;
	}
	m_renderer->render();
}

void SceneGadget::visibilityChanged()
{
	if( !visible() && m_updateTask )
	{
		m_updateTask->cancelAndWait();
	}
}
