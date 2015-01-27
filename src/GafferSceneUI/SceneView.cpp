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
#include "boost/algorithm/string/predicate.hpp"

#include "IECore/ParameterisedProcedural.h"
#include "IECore/VectorTypedData.h"
#include "IECore/MatrixTransform.h"

#include "IECoreGL/GL.h"
#include "IECoreGL/State.h"
#include "IECoreGL/Camera.h"

#include "Gaffer/Context.h"
#include "Gaffer/BlockedConnection.h"

#include "GafferUI/Style.h"
#include "GafferUI/Pointer.h"

#include "GafferScene/SceneProcedural.h"
#include "GafferScene/PathMatcherData.h"
#include "GafferScene/StandardAttributes.h"
#include "GafferScene/PathFilter.h"
#include "GafferScene/Grid.h"
#include "GafferScene/SceneAlgo.h"
#include "GafferScene/StandardOptions.h"

#include "GafferSceneUI/SceneView.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferUI;
using namespace GafferScene;
using namespace GafferSceneUI;

//////////////////////////////////////////////////////////////////////////
// SceneView::Grid implementation
//////////////////////////////////////////////////////////////////////////

class SceneView::Grid
{

	public :

		Grid( SceneView *view )
			:	m_view( view ), m_node( new GafferScene::Grid ), m_gadget( new SceneGadget )
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

			m_gadget->setMinimumExpansionDepth( 1 );
			m_gadget->setScene( m_node->outPlug() );
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
			m_gadget->setVisible( plug()->getChild<BoolPlug>( "visible" )->getValue() );
		}

		SceneView *m_view;
		GafferScene::GridPtr m_node;
		SceneGadgetPtr m_gadget;

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
// SceneView::LookThrough implementation
//////////////////////////////////////////////////////////////////////////

namespace
{

/// \todo If we made CropWindowTool::Rectangle public, we
/// could ditch this class.
class CameraOverlay : public GafferUI::Gadget
{

	public :

		CameraOverlay()
			:	Gadget()
		{
		}

		virtual Imath::Box3f bound() const
		{
			// we draw in raster space so don't have a sensible bound
			return Box3f();
		}

		// Specified in raster space.
		void setResolutionGate( const Box2f &resolutionGate )
		{
			if( resolutionGate == m_resolutionGate )
			{
				return;
			}
			m_resolutionGate = resolutionGate;
			renderRequestSignal()( this );
		}

		const Box2f &getResolutionGate() const
		{
			return m_resolutionGate;
		}

		// Specified in 0-1 space relative to resolution gate
		void setCropWindow( const Box2f &cropWindow )
		{
			if( cropWindow == m_cropWindow )
			{
				return;
			}
			m_cropWindow = cropWindow;
			renderRequestSignal()( this );
		}

		const Box2f &getCropWindow() const
		{
			return m_cropWindow;
		}

		void setCaption( const std::string &caption )
		{
			if( caption == m_caption )
			{
				return;
			}
			m_caption = caption;
			renderRequestSignal()( this );
		}

		const std::string &getCaption() const
		{
			return m_caption;
		}

	protected :

		virtual void doRender( const Style *style ) const
		{
			if( IECoreGL::Selector::currentSelector() || m_resolutionGate.isEmpty() )
			{
				return;
			}

			const ViewportGadget *viewportGadget = ancestor<ViewportGadget>();
			ViewportGadget::RasterScope rasterScope( viewportGadget );

			glPushAttrib( GL_CURRENT_BIT | GL_LINE_BIT | GL_ENABLE_BIT );

				glEnable( GL_LINE_SMOOTH );
				glLineWidth( 1.5f );

				glColor4f( 0.5, 0.5, 0.5, 0.5 );
				style->renderRectangle( Box2f(
					V2f(
						lerp( m_resolutionGate.min.x, m_resolutionGate.max.x, m_cropWindow.min.x ),
						lerp( m_resolutionGate.min.y, m_resolutionGate.max.y, m_cropWindow.min.y )
					),
					V2f(
						lerp( m_resolutionGate.min.x, m_resolutionGate.max.x, m_cropWindow.max.x ),
						lerp( m_resolutionGate.min.y, m_resolutionGate.max.y, m_cropWindow.max.y )
					)
				) );

				glColor4f( 0, 0.25, 0, 1.0f );
				style->renderRectangle( m_resolutionGate );

				glPushMatrix();

					glTranslatef( m_resolutionGate.min.x + 5, m_resolutionGate.max.y + 10, 0.0f );
					glScalef( 10.0f, -10.0f, 10.0f );
					style->renderText( Style::LabelText, m_caption );

				glPopMatrix();

			glPopAttrib();
		}

	private :

		Box2f m_resolutionGate;
		Box2f m_cropWindow;
		std::string m_caption;

};

IE_CORE_DECLAREPTR( CameraOverlay )

} // namespace

class SceneView::LookThrough
{

	public :

		LookThrough( SceneView *view )
			:	m_view( view ),
				m_framed( false ),
				m_standardOptions( new StandardOptions ),
				m_originalCamera( m_view->viewportGadget()->getCamera() ),
				m_lookThroughCameraDirty( true ),
				m_lookThroughCamera( NULL ),
				m_viewportCameraDirty( true ),
				m_overlay( new CameraOverlay )
		{

			// Set up our plugs

			CompoundPlugPtr lookThrough = new CompoundPlug( "lookThrough", Plug::In, Plug::Default & ~Plug::AcceptsInputs );
			lookThrough->addChild( new BoolPlug( "enabled", Plug::In, false, Plug::Default & ~Plug::AcceptsInputs ) );
			lookThrough->addChild( new StringPlug( "camera", Plug::In, "", Plug::Default & ~Plug::AcceptsInputs ) );
			view->addChild( lookThrough );

			// Set up our nodes. We use a standard options node to disable camera motion blur
			// and overscan because we don't want them applied to the cameras we retrieve with SceneAlgo.
			// We also must disable transform blur and deformation blur, because if either of those is
			// on, the shutter range becomes non-zero and the SceneAlgo transform() method will evaluate the
			// camera at the shutter start rather than the current time, even though its only evaluating a
			// single time sample.

			m_standardOptions->inPlug()->setInput( view->inPlug<ScenePlug>() );
			m_standardOptions->optionsPlug()->getChild<CompoundDataPlug::MemberPlug>( "cameraBlur" )->enabledPlug()->setValue( true );
			m_standardOptions->optionsPlug()->getChild<CompoundDataPlug::MemberPlug>( "cameraBlur" )->valuePlug<BoolPlug>()->setValue( false );
			m_standardOptions->optionsPlug()->getChild<CompoundDataPlug::MemberPlug>( "transformBlur" )->enabledPlug()->setValue( true );
			m_standardOptions->optionsPlug()->getChild<CompoundDataPlug::MemberPlug>( "transformBlur" )->valuePlug<BoolPlug>()->setValue( false );
			m_standardOptions->optionsPlug()->getChild<CompoundDataPlug::MemberPlug>( "deformationBlur" )->enabledPlug()->setValue( true );
			m_standardOptions->optionsPlug()->getChild<CompoundDataPlug::MemberPlug>( "deformationBlur" )->valuePlug<BoolPlug>()->setValue( false );
			m_standardOptions->optionsPlug()->getChild<CompoundDataPlug::MemberPlug>( "overscan" )->enabledPlug()->setValue( true );
			m_standardOptions->optionsPlug()->getChild<CompoundDataPlug::MemberPlug>( "overscan" )->valuePlug<BoolPlug>()->setValue( false );

			// Set up our gadgets

			view->viewportGadget()->setChild( "__cameraOverlay", m_overlay );
			m_overlay->setVisible( false );

			// Connect to the signals we need

			m_standardOptions->plugDirtiedSignal().connect( boost::bind( &LookThrough::plugDirtied, this, ::_1 ) );
			view->plugDirtiedSignal().connect( boost::bind( &LookThrough::plugDirtied, this, ::_1 ) );
			view->viewportGadget()->preRenderSignal().connect( boost::bind( &LookThrough::preRender, this ) );
			view->viewportGadget()->viewportChangedSignal().connect( boost::bind( &LookThrough::viewportChanged, this ) );

			connectToViewContext();
			view->contextChangedSignal().connect( boost::bind( &LookThrough::connectToViewContext, this ) );

		}

		Gaffer::CompoundPlug *plug()
		{
			return m_view->getChild<Gaffer::CompoundPlug>( "lookThrough" );
		}

		const Gaffer::CompoundPlug *plug() const
		{
			return m_view->getChild<Gaffer::CompoundPlug>( "lookThrough" );
		}

		const Imath::Box2f &resolutionGate() const
		{
			const_cast<LookThrough *>( this )->updateLookThroughCamera();
			const_cast<LookThrough *>( this )->updateViewportCameraAndOverlay();
			return m_overlay->getResolutionGate();
		}

	private :

		const GafferScene::ScenePlug *scenePlug() const
		{
			return m_standardOptions->outPlug();
		}

		const Gaffer::BoolPlug *enabledPlug() const
		{
			return plug()->getChild<BoolPlug>( 0 );
		}

		const Gaffer::StringPlug *cameraPlug() const
		{
			return plug()->getChild<StringPlug>( 1 );
		}

		void connectToViewContext()
		{
			m_contextChangedConnection = m_view->getContext()->changedSignal().connect( boost::bind( &LookThrough::contextChanged, this, ::_2 ) );
		}

		void contextChanged( const IECore::InternedString &name )
		{
			if( !boost::starts_with( name.value(), "ui:" ) )
			{
				m_lookThroughCameraDirty = m_viewportCameraDirty = true;
			}
		}

		void plugDirtied( Gaffer::Plug *plug )
		{
			if(
				plug == scenePlug()->childNamesPlug() ||
				plug == scenePlug()->globalsPlug() ||
				plug == scenePlug()->objectPlug() ||
				plug == scenePlug()->transformPlug() ||
				plug == enabledPlug() ||
				plug == cameraPlug()
			)
			{
				m_lookThroughCameraDirty = m_viewportCameraDirty = true;
				if( plug == enabledPlug() && enabledPlug()->getValue() )
				{
					m_originalCamera = m_view->viewportGadget()->getCamera();
				}
				m_view->viewportGadget()->renderRequestSignal()( m_view->viewportGadget() );
			}
		}

		void viewportChanged()
		{
			m_viewportCameraDirty = true;
			m_view->viewportGadget()->renderRequestSignal()( m_view->viewportGadget() );
		}

		void preRender()
		{
			if( !m_framed )
			{
				m_view->viewportGadget()->frame( m_view->framingBound() );
				m_framed = true;
			}
			else
			{
				updateLookThroughCamera();
				updateViewportCameraAndOverlay();
			}
		}

		void updateLookThroughCamera()
		{
			if( !m_lookThroughCameraDirty )
			{
				return;
			}

			m_lookThroughCameraDirty = false;
			m_lookThroughCamera = NULL;
			if( !enabledPlug()->getValue() )
			{
				m_view->viewportGadget()->setCamera( m_originalCamera.get() );
				m_view->viewportGadget()->setCameraEditable( true );
				m_view->hideFilter()->pathsPlug()->setToDefault();
				return;
			}

			// We want to look through a specific camera.
			// Retrieve it.

			Context::Scope scopedContext( m_view->getContext() );

			try
			{
				const string cameraPathString = cameraPlug()->getValue();
				if( cameraPathString.empty() )
				{
					m_lookThroughCamera = GafferScene::camera( scenePlug() ); // primary render camera
				}
				else
				{
					ScenePlug::ScenePath cameraPath;
					ScenePlug::stringToPath( cameraPathString, cameraPath );
					m_lookThroughCamera = GafferScene::camera( scenePlug(), cameraPath );
				}
			}
			catch( ... )
			{
				// If an invalid path has been entered for the camera, computation will fail.
				// We just ignore that and lock to the current camera instead.
				m_lookThroughCamera = NULL;
			}

			m_view->viewportGadget()->setCameraEditable( false );
			if( m_lookThroughCamera )
			{
				StringVectorDataPtr invisiblePaths = new StringVectorData();
				invisiblePaths->writable().push_back( m_lookThroughCamera->getName() );
				m_view->hideFilter()->pathsPlug()->setValue( invisiblePaths );
			}
			else
			{
				m_view->hideFilter()->pathsPlug()->setToDefault();
			}
		}

		void updateViewportCameraAndOverlay()
		{
			if( !m_viewportCameraDirty )
			{
				return;
			}

			if( !m_lookThroughCamera )
			{
				m_overlay->setResolutionGate( Box2f() );
				m_overlay->setVisible( false );
				return;
			}

			// The camera will have a resolution and screen window set from the scene
			// globals. We need to adjust them to fit the viewport appropriately, placing
			// the resolution gate centrally with a border around it. Start by figuring
			// out where we'll draw the resolution gate in raster space.

			IECore::CameraPtr camera = m_lookThroughCamera->copy();

			const float borderPixels = 40;
			const V2f viewport = m_view->viewportGadget()->getViewport();
			const V2f insetViewport(
				max( viewport.x - borderPixels * 2.0f, min( viewport.x, 50.0f ) ),
				max( viewport.y - borderPixels * 2.0f, min( viewport.y, 50.0f ) )
			);
			const float insetViewportAspectRatio = insetViewport.x / insetViewport.y;

			const V2f resolution = camera->parametersData()->member<V2iData>( "resolution" )->readable();
			const float pixelAspectRatio = camera->parametersData()->member<FloatData>( "pixelAspectRatio" )->readable();

			V2f resolutionGateSize = resolution;
			resolutionGateSize.x *= pixelAspectRatio;
			const float resolutionGateAspectRatio = resolutionGateSize.x / resolutionGateSize.y;
			if( resolutionGateAspectRatio > insetViewportAspectRatio )
			{
				// fit horizontally
				resolutionGateSize *= insetViewport.x / resolutionGateSize.x;
			}
			else
			{
				// fit vertically
				resolutionGateSize *= insetViewport.y / resolutionGateSize.y;
			}

			const V2f offset = ( viewport - resolutionGateSize ) / 2.0f;

			m_overlay->setResolutionGate( Box2f( V2f( offset ), V2f( resolutionGateSize + offset ) ) );
			m_overlay->setCropWindow( camera->parametersData()->member<Box2fData>( "cropWindow" )->readable() );
			m_overlay->setCaption( boost::str( boost::format( "%dx%d, %.3f, %s" ) % resolution.x % resolution.y % pixelAspectRatio % camera->getName() ) );
			m_overlay->setVisible( true );

			// Now modify the camera, so that the view through the resolution gate we've calculated
			// represents the rendered image - this means extending the resolution and screen
			// window to account for the border area outside the resolution gate.

			Box2f &screenWindow = camera->parametersData()->member<Box2fData>( "screenWindow" )->writable();
			const V2f newScreenWindowSize = screenWindow.size() * viewport / resolutionGateSize;
			const V2f screenWindowCenter = screenWindow.center();
			screenWindow.min = screenWindowCenter - newScreenWindowSize / 2.0f;
			screenWindow.max = screenWindowCenter + newScreenWindowSize / 2.0f;

			camera->parameters()["resolution"] = new V2iData( m_view->viewportGadget()->getViewport() );
			m_view->viewportGadget()->setCamera( camera.get() );
			m_view->viewportGadget()->setCameraEditable( false );

		}

		SceneView *m_view;
		bool m_framed;

		StandardOptionsPtr m_standardOptions;

		boost::signals::scoped_connection m_contextChangedConnection;

		/// The default viewport camera - we store this so we can
		/// return to it after looking through a scene camera.
		IECore::ConstCameraPtr m_originalCamera;
		// Camera we want to look through - retrieved from scene
		// and dirtied on plug and context changes.
		bool m_lookThroughCameraDirty;
		IECore::ConstCameraPtr m_lookThroughCamera;
		// We transfer the look through camera onto the viewport,
		// adjusting it to fit when we do. This needs repeating when
		// the viewport changes, which is tracked by this flag.
		bool m_viewportCameraDirty;
		// Overlay for displaying resolution gate etc. Needs updating
		// when the viewport camera is dirty.
		CameraOverlayPtr m_overlay;

};

//////////////////////////////////////////////////////////////////////////
// SceneView implementation
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( SceneView );

size_t SceneView::g_firstPlugIndex = 0;
SceneView::ViewDescription<SceneView> SceneView::g_viewDescription( GafferScene::ScenePlug::staticTypeId() );

SceneView::SceneView( const std::string &name )
	:	View3D( name, new GafferScene::ScenePlug() ),
		m_sceneGadget( new SceneGadget )
{

	// add plugs and signal handling for them

	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new IntPlug( "minimumExpansionDepth", Plug::In, 0, 0, Imath::limits<int>::max(), Plug::Default & ~Plug::AcceptsInputs ) );

	plugSetSignal().connect( boost::bind( &SceneView::plugSet, this, ::_1 ) );

	// set up our gadgets

	viewportGadget()->setPrimaryChild( m_sceneGadget );

	viewportGadget()->keyPressSignal().connect( boost::bind( &SceneView::keyPress, this, ::_1, ::_2 ) );

	m_sceneGadget->baseState()->add( const_cast<IECoreGL::State *>( baseState() ) );
	m_sceneGadget->setContext( getContext() );
	baseStateChangedSignal().connect( boost::bind( &SceneView::baseStateChanged, this ) );

	m_lookThrough = boost::shared_ptr<LookThrough>( new LookThrough( this ) );
	m_grid = boost::shared_ptr<Grid>( new Grid( this ) );
	m_gnomon = boost::shared_ptr<Gnomon>( new Gnomon( this ) );

	//////////////////////////////////////////////////////////////////////////
	// add a preprocessor which monkeys with the scene before it is displayed.
	//////////////////////////////////////////////////////////////////////////

	NodePtr preprocessor = new Node();
	ScenePlugPtr preprocessorInput = new ScenePlug( "in" );
	preprocessor->addChild( preprocessorInput );

	// add a node for hiding things

	StandardAttributesPtr hide = new StandardAttributes( "hide" );
	hide->attributesPlug()->getChild<CompoundPlug>( "visibility" )->getChild<BoolPlug>( "enabled" )->setValue( true );
	hide->attributesPlug()->getChild<CompoundPlug>( "visibility" )->getChild<BoolPlug>( "value" )->setValue( false );

	preprocessor->addChild( hide );
	hide->inPlug()->setInput( preprocessorInput );

	PathFilterPtr hideFilter = new PathFilter( "hideFilter" );
	preprocessor->addChild( hideFilter );
	hide->filterPlug()->setInput( hideFilter->matchPlug() );

	// make the output for the preprocessor

	ScenePlugPtr preprocessorOutput = new ScenePlug( "out", Plug::Out );
	preprocessor->addChild( preprocessorOutput );
	preprocessorOutput->setInput( hide->outPlug() );

	setPreprocessor( preprocessor );

	// connect up our scene gadget

	m_sceneGadget->setScene( preprocessedInPlug<ScenePlug>() );

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
	return m_lookThrough->plug();
}

const Gaffer::CompoundPlug *SceneView::lookThroughPlug() const
{
	return m_lookThrough->plug();
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

void SceneView::setContext( Gaffer::ContextPtr context )
{
	View3D::setContext( context );
	m_sceneGadget->setContext( context );
}

const Box2f &SceneView::resolutionGate() const
{
	return m_lookThrough->resolutionGate();
}

void SceneView::contextChanged( const IECore::InternedString &name )
{
	if( name.value() == "ui:scene:selectedPaths" )
	{
		// If only the selection has changed then we can just update the selection
		// on our existing scene representation.
		const StringVectorData *sc = getContext()->get<StringVectorData>( "ui:scene:selectedPaths" );
		/// \todo Store selection as PathMatcherData within the context, so we don't need
		/// this conversion.
		GafferScene::PathMatcherDataPtr sg = new GafferScene::PathMatcherData;
		sg->writable().init( sc->readable().begin(), sc->readable().end() );
		m_sceneGadget->setSelection( sg );
		return;
	}
	else if( name.value() == "ui:scene:expandedPaths" )
	{
		const GafferScene::PathMatcherData *expandedPaths = getContext()->get<GafferScene::PathMatcherData>( "ui:scene:expandedPaths" );
		m_sceneGadget->setExpandedPaths( expandedPaths );
		return;
	}
	else if( boost::starts_with( name.value(), "ui:" ) )
	{
		// ui context entries shouldn't affect computation.
		return;
	}
}

Imath::Box3f SceneView::framingBound() const
{
	Imath::Box3f b = m_sceneGadget->selectionBound();
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

	PathMatcher &selection = const_cast<GafferScene::PathMatcherData *>( m_sceneGadget->getSelection() )->writable();
	PathMatcher &expanded = expandedPaths()->writable();

	std::vector<string> toExpand;
	selection.paths( toExpand );

	bool needUpdate = false;
	for( std::vector<string>::const_iterator it = toExpand.begin(), eIt = toExpand.end(); it != eIt; ++it )
	{
		/// \todo It would be nice to be able to get ScenePaths out of
		/// PathMatcher::paths() directly.
		ScenePlug::ScenePath path;
		ScenePlug::stringToPath( *it, path );
		needUpdate |= expandWalk( path, depth, expanded, selection );
	}

	if( needUpdate )
	{
		// We modified the expanded paths in place to avoid unecessary copying,
		// so the context doesn't know they've changed. So we emit the changed
		// signal ourselves - this will then update the SceneGadget via contextChanged().
		getContext()->changedSignal()( getContext(), "ui:scene:expandedPaths" );
		// Transfer the new selection to the context - we'd like to use the same
		// trick as above for that, but can't yet because the context selection isn't
		// stored as PathMatcherData.
		transferSelectionToContext();
	}
}

bool SceneView::expandWalk( const GafferScene::ScenePlug::ScenePath &path, size_t depth, PathMatcher &expanded, PathMatcher &selected )
{
	bool result = false;

	ConstInternedStringVectorDataPtr childNamesData = preprocessedInPlug<ScenePlug>()->childNames( path );
	const vector<InternedString> &childNames = childNamesData->readable();

	if( childNames.size() )
	{
		// expand ourselves to show our children, and make sure we're
		// not selected - we only want selection at the leaf levels of
		// our expansion.
		result |= expanded.addPath( path );
		result |= selected.removePath( path );

		ScenePlug::ScenePath childPath = path;
		childPath.push_back( InternedString() ); // room for the child name
		for( vector<InternedString>::const_iterator cIt = childNames.begin(), ceIt = childNames.end(); cIt != ceIt; cIt++ )
		{
			childPath.back() = *cIt;
			if( depth == 1 )
			{
				// at the bottom of the expansion - just select the child
				result |= selected.addPath( childPath );
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
		result |= selected.addPath( path );
	}

	return result;
}

void SceneView::collapseSelection()
{
	PathMatcher &selection = const_cast<GafferScene::PathMatcherData *>( m_sceneGadget->getSelection() )->writable();

	std::vector<string> toCollapse;
	selection.paths( toCollapse );

	if( !toCollapse.size() )
	{
		return;
	}

	GafferScene::PathMatcherData *expandedData = expandedPaths();
	PathMatcher &expanded = expandedData->writable();

	for( vector<string>::const_iterator it = toCollapse.begin(), eIt = toCollapse.end(); it != eIt; ++it )
	{
		/// \todo It would be nice to be able to get ScenePaths out of
		/// PathMatcher::paths() directly.
		ScenePlug::ScenePath path;
		ScenePlug::stringToPath( *it, path );

		if( !expanded.removePath( path ) )
		{
			if( path.size() <= 1 )
			{
				continue;
			}
			selection.removePath( path );
			path.pop_back(); // now the parent path
			expanded.removePath( path );
			selection.addPath( path );
		}
	}

	// See comment in expandSelection().
	getContext()->changedSignal()( getContext(), "ui:scene:expandedPaths" );
	// See comment in expandSelection().
	transferSelectionToContext();
}

void SceneView::transferSelectionToContext()
{
	/// \todo Use PathMatcherData for the context variable so we don't need
	/// to do this copying into StringVectorData. See related comments
	/// in SceneHierarchy.__transferSelectionFromContext
	StringVectorDataPtr s = new StringVectorData();
	m_sceneGadget->getSelection()->readable().paths( s->writable() );
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
	m_sceneGadget->baseState()->add( const_cast<IECoreGL::State *>( baseState() ) );
	m_sceneGadget->renderRequestSignal()( m_sceneGadget.get() );
}

void SceneView::plugSet( Gaffer::Plug *plug )
{
	if( plug == minimumExpansionDepthPlug() )
	{
		m_sceneGadget->setMinimumExpansionDepth( minimumExpansionDepthPlug()->getValue() );
	}
}
