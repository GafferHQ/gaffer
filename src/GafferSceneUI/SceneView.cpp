//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012-2014, John Haddon. All rights reserved.
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

#include "boost/bind.hpp"
#include "boost/bind/placeholders.hpp"

#include "IECore/ParameterisedProcedural.h"
#include "IECore/VectorTypedData.h"
#include "IECore/MatrixTransform.h"

#include "IECoreGL/GL.h"
#include "IECoreGL/State.h"
#include "IECoreGL/Camera.h"

#include "Gaffer/Context.h"
#include "Gaffer/BlockedConnection.h"

#include "GafferUI/Style.h"

#include "GafferScene/SceneProcedural.h"
#include "GafferScene/PathMatcherData.h"
#include "GafferScene/StandardOptions.h"
#include "GafferScene/StandardAttributes.h"
#include "GafferScene/PathFilter.h"
#include "GafferScene/Grid.h"

#include "GafferSceneUI/SceneView.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferUI;
using namespace GafferScene;
using namespace GafferSceneUI;

//////////////////////////////////////////////////////////////////////////
// Implementation of a ParameterisedProcedural wrapping a SceneProcedural.
// We need this to allow us to use the RenderableGadget for doing our
// display.
/// \todo Build our own scene representation.
//////////////////////////////////////////////////////////////////////////

class WrappingProcedural : public IECore::ParameterisedProcedural
{

	public :

		WrappingProcedural( SceneProceduralPtr sceneProcedural )
			:	ParameterisedProcedural( "" ), m_sceneProcedural( sceneProcedural )
		{
		}

	protected :

		virtual Imath::Box3f doBound( ConstCompoundObjectPtr args ) const
		{
			return m_sceneProcedural->bound();
		}

		virtual void doRender( RendererPtr renderer, ConstCompoundObjectPtr args ) const
		{
			m_sceneProcedural->render( renderer.get() );
		}

	private :

		SceneProceduralPtr m_sceneProcedural;

};

IE_CORE_DECLAREPTR( WrappingProcedural );

//////////////////////////////////////////////////////////////////////////
// SceneView::Grid implementation
//////////////////////////////////////////////////////////////////////////

class SceneView::Grid
{

	public :

		Grid( SceneView *view )
			:	m_view( view ), m_node( new GafferScene::Grid ), m_gadget( new RenderableGadget )
		{
			m_node->transformPlug()->rotatePlug()->setValue( V3f( 90, 0, 0 ) );

			CompoundPlugPtr plug = new CompoundPlug( "grid" );
			view->addChild( plug );

			plug->addChild( new BoolPlug( "visible", Plug::In, true ) );

			PlugPtr dimensionsPlug(
				m_node->dimensionsPlug()->createCounterpart(
					m_node->dimensionsPlug()->getName(),
					Plug::In
				)
			);
			plug->addChild( dimensionsPlug );

			m_node->dimensionsPlug()->setInput( dimensionsPlug );

			view->viewportGadget()->setChild( "__grid", m_gadget );

			view->plugDirtiedSignal().connect( boost::bind( &Grid::plugDirtied, this, ::_1 ) );

			update();
		}

		Gaffer::CompoundPlug *plug()
		{
			return m_view->getChild<Gaffer::CompoundPlug>( "grid" );
		}

		const Gaffer::CompoundPlug *plug() const
		{
			return m_view->getChild<Gaffer::CompoundPlug>( "grid" );
		}

		Gadget *gadget()
		{
			return m_gadget.get();
		}

		const Gadget *gadget() const
		{
			return m_gadget.get();
		}

	private :

		void plugDirtied( Gaffer::Plug *plug )
		{
			if( plug == this->plug() )
			{
				update();
			}
		}

		void update()
		{
			m_gadget->setRenderable(
				new WrappingProcedural(
					new SceneProcedural( m_node->outPlug(), m_view->getContext() )
				)
			);
			m_gadget->setVisible( plug()->getChild<BoolPlug>( "visible" )->getValue() );
		}

		SceneView *m_view;
		GafferScene::GridPtr m_node;
		GafferUI::RenderableGadgetPtr m_gadget;

};

//////////////////////////////////////////////////////////////////////////
// SceneView::Gnomon implementation
//////////////////////////////////////////////////////////////////////////

namespace
{

class GnomonPlane : public GafferUI::Gadget
{

	public :

		GnomonPlane()
			:	Gadget(), m_hovering( false )
		{
			enterSignal().connect( boost::bind( &GnomonPlane::enter, this ) );
			leaveSignal().connect( boost::bind( &GnomonPlane::leave, this ) );
		}

		Imath::Box3f bound() const
		{
			return Box3f( V3f( 0 ), V3f( 1, 1, 0 ) );
		}

	protected :

		virtual void doRender( const Style *style ) const
		{
			if( m_hovering || IECoreGL::Selector::currentSelector() )
			{
				/// \todo Really the style should be choosing the colours.
				glColor4f( 0.5f, 0.7f, 1.0f, 0.5f );
				style->renderSolidRectangle( Box2f( V2f( 0 ), V2f( 1, 1 ) ) );
			}
		}

	private :

		void enter()
		{
			m_hovering = true;
			renderRequestSignal()( this );
		}

		void leave()
		{
			m_hovering = false;
			renderRequestSignal()( this );
		}

		bool m_hovering;

};

class GnomonGadget : public GafferUI::Gadget
{

	public :

		GnomonGadget()
		{
		}

	protected :

		virtual void doRender( const Style *style ) const
		{
			const float pixelWidth = 30.0f;
			const V2i viewport = ancestor<ViewportGadget>()->getViewport();

			// we want to draw our children with an orthographic projection
			// from the same angle as the main camera, but transformed into
			// the bottom left corner of the viewport.
			//
			// first we compose a new projection matrix with the orthographic
			// projection and a post-projection transform that moves eveything
			// into the corner.

			glMatrixMode( GL_PROJECTION );
			glPushMatrix();
			glLoadIdentity();

			// if we're drawing for selection, the selector will have its own
			// post-projection matrix which needs taking into account as well.
			if( IECoreGL::Selector *selector = IECoreGL::Selector::currentSelector() )
			{
				glMultMatrixd( selector->postProjectionMatrix().getValue() );
			}

			// this is our post projection matrix, which scales down to the size we want and
			// translates into the corner.
			glTranslatef( -1.0f + pixelWidth / (float)viewport.x, -1.0f + pixelWidth / (float)viewport.y, 0.0f ),
			glScalef( pixelWidth / (float)viewport.x, pixelWidth / (float)viewport.y, 1 );

			// this is our projection matrix - a simple orthographic projection.
			glOrtho( -1, 1, -1, 1, 0, 10 );

			// now for our model-view matrix. this is the same as is used by the main
			// view, but with the translation reset. this means when we draw our
			// children at the origin, they will be centred within camera space.

			glMatrixMode( GL_MODELVIEW );
			glPushMatrix();

			M44f m = IECoreGL::Camera::matrix();
			m[3][0] = 0;
			m[3][1] = 0;
			m[3][2] = -2;

			glMatrixMode( GL_MODELVIEW );
			glLoadIdentity();
			glMultMatrixf( m.getValue() );

			// now we can render our axes and our children

			style->renderTranslateHandle( 0 );
			style->renderTranslateHandle( 1 );
			style->renderTranslateHandle( 2 );

			Gadget::doRender( style );

			// and pop the matrices back to their original values

			glMatrixMode( GL_PROJECTION );
			glPopMatrix();
			glMatrixMode( GL_MODELVIEW );
			glPopMatrix();

		}

};

} // namespace

class SceneView::Gnomon
{

	public :

		Gnomon( SceneView *view )
			:	m_view( view ), m_gadget( new GnomonGadget() )
		{
			CompoundPlugPtr plug = new CompoundPlug( "gnomon" );
			view->addChild( plug );

			plug->addChild( new BoolPlug( "visible", Plug::In, true ) );

			GadgetPtr xyPlane = new GnomonPlane();
			GadgetPtr yzPlane = new GnomonPlane();
			GadgetPtr xzPlane = new GnomonPlane();

			yzPlane->setTransform( M44f().rotate( V3f( 0, -M_PI / 2.0f, 0 ) ) );
			xzPlane->setTransform( M44f().rotate( V3f( M_PI / 2.0f, 0, 0 ) ) );

			m_gadget->setChild( "xy", xyPlane );
			m_gadget->setChild( "yz", yzPlane );
			m_gadget->setChild( "xz", xzPlane );

			xyPlane->buttonPressSignal().connect( boost::bind( &Gnomon::buttonPress, this, ::_1, ::_2 ) );
			yzPlane->buttonPressSignal().connect( boost::bind( &Gnomon::buttonPress, this, ::_1, ::_2 ) );
			xzPlane->buttonPressSignal().connect( boost::bind( &Gnomon::buttonPress, this, ::_1, ::_2 ) );

			view->viewportGadget()->setChild( "__gnomon", m_gadget );

			view->plugDirtiedSignal().connect( boost::bind( &Gnomon::plugDirtied, this, ::_1 ) );

			update();
		}

		Gaffer::CompoundPlug *plug()
		{
			return m_view->getChild<Gaffer::CompoundPlug>( "gnomon" );
		}

		const Gaffer::CompoundPlug *plug() const
		{
			return m_view->getChild<Gaffer::CompoundPlug>( "gnomon" );
		}

		Gadget *gadget()
		{
			return m_gadget.get();
		}

		const Gadget *gadget() const
		{
			return m_gadget.get();
		}

	private :

		void plugDirtied( Gaffer::Plug *plug )
		{
			if( plug == this->plug() )
			{
				update();
			}
		}

		void update()
		{
			m_gadget->setVisible( plug()->getChild<BoolPlug>( "visible" )->getValue() );
		}

		bool buttonPress( Gadget *gadget, const ButtonEvent &event )
		{
			if( event.buttons != ButtonEvent::Left )
			{
				return false;
			}

			if( !m_view->viewportGadget()->getCameraEditable() )
			{
				return true;
			}

			V3f direction( 0, 0, -1 );
			V3f upVector( 0, 1, 0 );

			if( gadget->getName() == "yz" )
			{
				direction = V3f( -1, 0, 0 );
			}
			else if( gadget->getName() == "xz" )
			{
				direction = V3f( 0, -1, 0 );
				upVector = V3f( -1, 0, 0 );
			}

			/// \todo We should probably have default persp/top/front/side cameras
			/// in the SceneView, and then we could toggle between them here.
			m_view->viewportGadget()->frame( m_view->framingBound(), direction, upVector );

			return true;
		}

		SceneView *m_view;
		GadgetPtr m_gadget;

};

//////////////////////////////////////////////////////////////////////////
// SceneView implementation
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( SceneView );

size_t SceneView::g_firstPlugIndex = 0;
SceneView::ViewDescription<SceneView> SceneView::g_viewDescription( GafferScene::ScenePlug::staticTypeId() );

SceneView::SceneView( const std::string &name )
	:	View3D( name, new GafferScene::ScenePlug() ),
		m_renderableGadget( new RenderableGadget )
{

	// add plugs and signal handling for them

	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new IntPlug( "minimumExpansionDepth", Plug::In, 0, 0, Imath::limits<int>::max(), Plug::Default & ~Plug::AcceptsInputs ) );

	CompoundPlugPtr lookThrough = new CompoundPlug( "lookThrough", Plug::In, Plug::Default & ~Plug::AcceptsInputs );
	lookThrough->addChild( new BoolPlug( "enabled", Plug::In, false, Plug::Default & ~Plug::AcceptsInputs ) );
	lookThrough->addChild( new StringPlug( "camera", Plug::In, "", Plug::Default & ~Plug::AcceptsInputs ) );
	addChild( lookThrough );

	plugSetSignal().connect( boost::bind( &SceneView::plugSet, this, ::_1 ) );

	// set up our gadgets

	viewportGadget()->setPrimaryChild( m_renderableGadget );

	m_selectionChangedConnection = m_renderableGadget->selectionChangedSignal().connect( boost::bind( &SceneView::selectionChanged, this, ::_1 ) );
	viewportGadget()->keyPressSignal().connect( boost::bind( &SceneView::keyPress, this, ::_1, ::_2 ) );

	m_renderableGadget->baseState()->add( const_cast<IECoreGL::State *>( baseState() ) );
	baseStateChangedSignal().connect( boost::bind( &SceneView::baseStateChanged, this ) );

	m_grid = boost::shared_ptr<Grid>( new Grid( this ) );
	m_gnomon = boost::shared_ptr<Gnomon>( new Gnomon( this ) );

	//////////////////////////////////////////////////////////////////////////
	// add a preprocessor which monkeys with the scene before it is displayed.
	//////////////////////////////////////////////////////////////////////////

	NodePtr preprocessor = new Node();
	ScenePlugPtr preprocessorInput = new ScenePlug( "in" );
	preprocessor->addChild( preprocessorInput );

	// remove motion blur, because the opengl renderer doesn't support it.

	StandardOptionsPtr standardOptions = new StandardOptions( "disableBlur" );
	standardOptions->optionsPlug()->getChild<CompoundPlug>( "transformBlur" )->getChild<BoolPlug>( "enabled" )->setValue( true );
	standardOptions->optionsPlug()->getChild<CompoundPlug>( "transformBlur" )->getChild<BoolPlug>( "value" )->setValue( false );
	standardOptions->optionsPlug()->getChild<CompoundPlug>( "deformationBlur" )->getChild<BoolPlug>( "enabled" )->setValue( true );
	standardOptions->optionsPlug()->getChild<CompoundPlug>( "deformationBlur" )->getChild<BoolPlug>( "value" )->setValue( false );

	preprocessor->addChild( standardOptions );
	standardOptions->inPlug()->setInput( preprocessorInput );

	// add a node for hiding things

	StandardAttributesPtr hide = new StandardAttributes( "hide" );
	hide->attributesPlug()->getChild<CompoundPlug>( "visibility" )->getChild<BoolPlug>( "enabled" )->setValue( true );
	hide->attributesPlug()->getChild<CompoundPlug>( "visibility" )->getChild<BoolPlug>( "value" )->setValue( false );

	preprocessor->addChild( hide );
	hide->inPlug()->setInput( standardOptions->outPlug() );

	PathFilterPtr hideFilter = new PathFilter( "hideFilter" );
	preprocessor->addChild( hideFilter );
	hide->filterPlug()->setInput( hideFilter->matchPlug() );

	// make the output for the preprocessor

	ScenePlugPtr preprocessorOutput = new ScenePlug( "out", Plug::Out );
	preprocessor->addChild( preprocessorOutput );
	preprocessorOutput->setInput( hide->outPlug() );

	setPreprocessor( preprocessor );
}

SceneView::~SceneView()
{
}

Gaffer::IntPlug *SceneView::minimumExpansionDepthPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

const Gaffer::IntPlug *SceneView::minimumExpansionDepthPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

Gaffer::CompoundPlug *SceneView::lookThroughPlug()
{
	return getChild<CompoundPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::CompoundPlug *SceneView::lookThroughPlug() const
{
	return getChild<CompoundPlug>( g_firstPlugIndex + 1 );
}

Gaffer::BoolPlug *SceneView::lookThroughEnabledPlug()
{
	return lookThroughPlug()->getChild<BoolPlug>( 0 );
}

const Gaffer::BoolPlug *SceneView::lookThroughEnabledPlug() const
{
	return lookThroughPlug()->getChild<BoolPlug>( 0 );
}

Gaffer::StringPlug *SceneView::lookThroughCameraPlug()
{
	return lookThroughPlug()->getChild<StringPlug>( 1 );
}

const Gaffer::StringPlug *SceneView::lookThroughCameraPlug() const
{
	return lookThroughPlug()->getChild<StringPlug>( 1 );
}

Gaffer::CompoundPlug *SceneView::gridPlug()
{
	return m_grid->plug();
}

const Gaffer::CompoundPlug *SceneView::gridPlug() const
{
	return m_grid->plug();
}

Gaffer::CompoundPlug *SceneView::gnomonPlug()
{
	return m_gnomon->plug();
}

const Gaffer::CompoundPlug *SceneView::gnomonPlug() const
{
	return m_gnomon->plug();
}

GafferScene::PathFilter *SceneView::hideFilter()
{
	return getPreprocessor<Node>()->getChild<PathFilter>( "hideFilter" );
}

const GafferScene::PathFilter *SceneView::hideFilter() const
{
	return getPreprocessor<Node>()->getChild<PathFilter>( "hideFilter" );
}

void SceneView::contextChanged( const IECore::InternedString &name )
{
	if( name.value() == "ui:scene:selectedPaths" )
	{
		// if only the selection has changed then we can just update the selection
		// on our existing scene representation.
		const StringVectorData *sc = getContext()->get<StringVectorData>( "ui:scene:selectedPaths" );
		RenderableGadget::Selection sr;
		sr.insert( sc->readable().begin(), sc->readable().end() );

		BlockedConnection blockedConnection( m_selectionChangedConnection );
		m_renderableGadget->setSelection( sr );
		return;
	}

	if(
		name.value().compare( 0, 3, "ui:" ) == 0 &&
		name.value() != "ui:scene:expandedPaths"
	)
	{
		// if it's just a ui context entry that has changed, and it doesn't
		// affect our expansion, then early out.
		return;
	}

	// the context change might affect the scene itself, so we must
	// schedule an update.
	updateRequestSignal()( this );
}

void SceneView::update()
{
	SceneProceduralPtr p = new SceneProcedural(
		preprocessedInPlug<ScenePlug>(), getContext(), ScenePlug::ScenePath(),
		expandedPaths(), minimumExpansionDepthPlug()->getValue()
	);
	WrappingProceduralPtr wp = new WrappingProcedural( p );

	bool hadRenderable = m_renderableGadget->getRenderable();
	m_renderableGadget->setRenderable( wp );
	if( !hadRenderable )
	{
		viewportGadget()->frame( framingBound() );
	}

	updateLookThrough();
}

Imath::Box3f SceneView::framingBound() const
{
	Imath::Box3f b = m_renderableGadget->selectionBound();
	if( !b.isEmpty() )
	{
		return b;
	}

	b = View3D::framingBound();
	if( m_grid->gadget()->getVisible() )
	{
		b.extendBy( m_grid->gadget()->bound() );
	}

	return b;
}

void SceneView::selectionChanged( GafferUI::RenderableGadgetPtr renderableGadget )
{
	BlockedConnection blockedConnection( contextChangedConnection() );
	transferSelectionToContext();
}

bool SceneView::keyPress( GafferUI::GadgetPtr gadget, const GafferUI::KeyEvent &event )
{
	if( event.key == "Down" )
	{
		expandSelection( event.modifiers & KeyEvent::Shift ? 999 : 1 );
		return true;
	}
	else if( event.key == "Up" )
	{
		collapseSelection();
		return true;
	}

	return false;
}

void SceneView::expandSelection( size_t depth )
{
	Context::Scope scopedContext( getContext() );

	RenderableGadget::Selection &selection = m_renderableGadget->getSelection();
	PathMatcher &expanded = expandedPaths()->writable();

	// must take a copy of the selection to iterate over, because we'll modify the
	// selection inside expandWalk().
	const std::vector<string> toExpand( selection.begin(), selection.end() );

	bool needUpdate = false;
	for( std::vector<string>::const_iterator it = toExpand.begin(), eIt = toExpand.end(); it != eIt; ++it )
	{
		needUpdate |= expandWalk( *it, depth, expanded, selection );
	}

	if( needUpdate )
	{
		// we were naughty and modified the expanded paths in place (to avoid
		// unecessary copying), so the context doesn't know they've changed.
		// so we emit the changed signal ourselves. this will then trigger update()
		// via contextChanged().
		getContext()->changedSignal()( getContext(), "ui:scene:expandedPaths" );
		// and this will trigger a selection update also via contextChanged().
		transferSelectionToContext();
	}
}

bool SceneView::expandWalk( const std::string &path, size_t depth, PathMatcher &expanded, RenderableGadget::Selection &selected )
{
	bool result = false;

	ScenePlug::ScenePath scenePath;
	ScenePlug::stringToPath( path, scenePath );
	ConstInternedStringVectorDataPtr childNamesData = preprocessedInPlug<ScenePlug>()->childNames( scenePath );
	const vector<InternedString> &childNames = childNamesData->readable();

	if( childNames.size() )
	{
		// expand ourselves to show our children, and make sure we're
		// not selected - we only want selection at the leaf levels of
		// our expansion.
		result |= expanded.addPath( path );
		result |= selected.erase( path );
		for( vector<InternedString>::const_iterator cIt = childNames.begin(), ceIt = childNames.end(); cIt != ceIt; cIt++ )
		{
			std::string childPath( path );
			if( *childPath.rbegin() != '/' )
			{
				childPath += '/';
			}
			childPath += cIt->string();
			if( depth == 1 )
			{
				// at the bottom of the expansion - just select the child
				result |= selected.insert( childPath ).second;
			}
			else
			{
				// continue the expansion
				result |= expandWalk( childPath, depth - 1, expanded, selected );
			}
		}
	}
	else
	{
		// we have no children, just make sure we're selected to mark the
		// leaf of the expansion.
		result |= selected.insert( path ).second;
	}

	return result;
}

void SceneView::collapseSelection()
{
	RenderableGadget::Selection &selection = m_renderableGadget->getSelection();
	if( !selection.size() )
	{
		return;
	}

	set<string> pathsToSelect;
	vector<const string *> pathsToDeselect;
	GafferScene::PathMatcherData *expandedData = expandedPaths();
	PathMatcher &expanded = expandedData->writable();

	for( RenderableGadget::Selection::const_iterator it = selection.begin(), eIt = selection.end(); it != eIt; it++ )
	{
		if( !expanded.removePath( *it ) )
		{
			if( *it == "/" )
			{
				continue;
			}
			pathsToDeselect.push_back( &(*it) );
			std::string parentPath( *it, 0, it->rfind( '/' ) );
			if( parentPath == "" )
			{
				parentPath = "/";
			}
			expanded.removePath( parentPath );
			pathsToSelect.insert( parentPath );
		}
	}

	for( set<string>::const_iterator it = pathsToSelect.begin(), eIt = pathsToSelect.end(); it != eIt; it++ )
	{
		selection.insert( *it );
	}
	for( vector<const string *>::const_iterator it = pathsToDeselect.begin(), eIt = pathsToDeselect.end(); it != eIt; it++ )
	{
		selection.erase( **it );
	}

	// see comment in expandSelection().
	getContext()->changedSignal()( getContext(), "ui:scene:expandedPaths" );
	// and this will trigger a selection update also via contextChanged().
	transferSelectionToContext();
}

void SceneView::transferSelectionToContext()
{
	/// \todo If RenderableGadget used PathMatcherData, then we might not need
	/// to copy data here.
	const RenderableGadget::Selection &selection = m_renderableGadget->getSelection();
	StringVectorDataPtr s = new StringVectorData();
	s->writable().insert( s->writable().end(), selection.begin(), selection.end() );
	getContext()->set( "ui:scene:selectedPaths", s.get() );
}

GafferScene::PathMatcherData *SceneView::expandedPaths()
{
	const GafferScene::PathMatcherData *m = getContext()->get<GafferScene::PathMatcherData>( "ui:scene:expandedPaths", 0 );
	if( !m )
	{
		GafferScene::PathMatcherDataPtr rootOnly = new GafferScene::PathMatcherData;
		rootOnly->writable().addPath( "/" );
		BlockedConnection blockedConnection( contextChangedConnection() );
		getContext()->set( "ui:scene:expandedPaths", rootOnly.get() );
		m = getContext()->get<GafferScene::PathMatcherData>( "ui:scene:expandedPaths", 0 );
	}
	return const_cast<GafferScene::PathMatcherData *>( m );
}

void SceneView::baseStateChanged()
{
	/// \todo This isn't transferring the override state properly. Probably an IECoreGL problem.
	m_renderableGadget->baseState()->add( const_cast<IECoreGL::State *>( baseState() ) );
	m_renderableGadget->renderRequestSignal()( m_renderableGadget.get() );
}

void SceneView::plugSet( Gaffer::Plug *plug )
{
	if( plug == minimumExpansionDepthPlug() )
	{
		updateRequestSignal()( this );
	}
	else if( plug == lookThroughPlug() )
	{
		updateLookThrough();
	}
}

void SceneView::updateLookThrough()
{
	Context::Scope scopedContext( getContext() );

	const ScenePlug *scene = preprocessedInPlug<ScenePlug>();
	ConstCompoundObjectPtr globals = scene->globalsPlug()->getValue();

	string cameraPathString;
	IECore::CameraPtr camera;
	if( lookThroughEnabledPlug()->getValue() )
	{
		cameraPathString = lookThroughCameraPlug()->getValue();
		if( cameraPathString.empty() )
		{
			if( const StringData *cameraPathData = globals->member<StringData>( "option:render:camera" ) )
			{
				cameraPathString = cameraPathData->readable();
			}
		}

		if( !cameraPathString.empty() )
		{
			ScenePlug::ScenePath cameraPath;
			ScenePlug::stringToPath( cameraPathString, cameraPath );

			try
			{
				ConstCameraPtr constCamera = runTimeCast<const IECore::Camera>( scene->object( cameraPath ) );
				if( constCamera )
				{
					camera = constCamera->copy();
					camera->setTransform( new MatrixTransform( scene->fullTransform( cameraPath ) ) );

					// if the camera has an existing screen window, remove it.
					// if we didn't, it would conflict with the resolution we set
					// below, yielding squashed/stretched images.
					/// \todo Properly specify how cameras are represented in Gaffer
					/// (the Cortex representation is very renderer-centric, with no
					/// real world parameters like film back) so that this isn't necessary,
					/// and add nice overlays for resolution gate etc.
					camera->parameters().erase( "screenWindow" );
				}
			}
			catch( ... )
			{
				// if an invalid path has been entered for the camera, computation will fail.
				// we can just ignore that and fall through to lock to the current camera instead.
				cameraPathString = "";
			}
		}

		if( !camera )
		{
			// we couldn't find a render camera to lock to, but we can lock to the current
			// camera instead.
			camera = viewportGadget()->getCamera()->copy();
		}
	}

	if( camera )
	{
		camera->parameters()["resolution"] = new V2iData( viewportGadget()->getViewport() );
		viewportGadget()->setCamera( camera.get() );
		viewportGadget()->setCameraEditable( false );

		StringVectorDataPtr invisiblePaths = new StringVectorData();
		invisiblePaths->writable().push_back( cameraPathString );
		hideFilter()->pathsPlug()->setValue( invisiblePaths );
	}
	else
	{
		viewportGadget()->setCameraEditable( true );
		hideFilter()->pathsPlug()->setToDefault();
	}
}
