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
#include "IECore/AngleConversion.h"

#include "IECoreGL/GL.h"
#include "IECoreGL/State.h"
#include "IECoreGL/Camera.h"
#include "IECoreGL/Primitive.h"
#include "IECoreGL/CurvesPrimitive.h"

#include "Gaffer/Context.h"
#include "Gaffer/BlockedConnection.h"
#include "Gaffer/StringPlug.h"

#include "GafferUI/ImageGadget.h"
#include "GafferUI/Pointer.h"
#include "GafferUI/Style.h"

#include "GafferScene/PathMatcherData.h"
#include "GafferScene/StandardAttributes.h"
#include "GafferScene/PathFilter.h"
#include "GafferScene/SetFilter.h"
#include "GafferScene/Grid.h"
#include "GafferScene/SceneAlgo.h"
#include "GafferScene/StandardOptions.h"
#include "GafferScene/LightToCamera.h"

#include "GafferSceneUI/ContextAlgo.h"
#include "GafferSceneUI/SceneView.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferUI;
using namespace GafferScene;
using namespace GafferSceneUI;

//////////////////////////////////////////////////////////////////////////
// SceneView::DrawingMode implementation
//////////////////////////////////////////////////////////////////////////

class SceneView::DrawingMode : public boost::signals::trackable
{

	public :

		DrawingMode( SceneView *view )
			:	m_view( view )
		{
			ValuePlugPtr drawingMode = new ValuePlug( "drawingMode" );
			m_view->addChild( drawingMode );

			ValuePlugPtr solid = new ValuePlug( "solid" );
			drawingMode->addChild( solid );
			solid->addChild( new BoolPlug( "enabled", Plug::In, true ) );
			solid->addChild( new BoolPlug( "override" ) );

			ValuePlugPtr wireframe = new ValuePlug( "wireframe" );
			drawingMode->addChild( wireframe );
			wireframe->addChild( new BoolPlug( "enabled" ) );
			wireframe->addChild( new BoolPlug( "override" ) );

			ValuePlugPtr points = new ValuePlug( "points" );
			drawingMode->addChild( points );
			points->addChild( new BoolPlug( "enabled" ) );
			points->addChild( new BoolPlug( "override" ) );

			ValuePlugPtr bound = new ValuePlug( "bound" );
			drawingMode->addChild( bound );
			bound->addChild( new BoolPlug( "enabled" ) );
			bound->addChild( new BoolPlug( "override" ) );

			ValuePlugPtr curves = new ValuePlug( "curves" );
			drawingMode->addChild( curves );

			ValuePlugPtr curvesUseGLLines = new ValuePlug( "useGLLines" );
			curves->addChild( curvesUseGLLines );
			curvesUseGLLines->addChild( new BoolPlug( "enabled", Plug::In, /* defaultValue = */ true ) );
			curvesUseGLLines->addChild( new BoolPlug( "override" ) );

			ValuePlugPtr curvesInterpolate = new ValuePlug( "interpolate" );
			curves->addChild( curvesInterpolate );
			curvesInterpolate->addChild( new BoolPlug( "enabled" ) );
			curvesInterpolate->addChild( new BoolPlug( "override" ) );

			updateBaseState();

			view->plugSetSignal().connect( boost::bind( &DrawingMode::plugSet, this, ::_1 ) );
		}

	private :

		Gaffer::Plug *drawingModePlug()
		{
			return m_view->getChild<Plug>( "drawingMode" );
		}

		SceneGadget *sceneGadget()
		{
			return static_cast<SceneGadget *>( m_view->viewportGadget()->getPrimaryChild() );
		}

		void plugSet( const Plug *plug )
		{
			if( plug == drawingModePlug() )
			{
				updateBaseState();
			}
		}

		void updateBaseState()
		{
			IECoreGL::State *baseState = sceneGadget()->baseState();

			const ValuePlug *solid = drawingModePlug()->getChild<ValuePlug>( "solid" );
			baseState->add(
				new IECoreGL::Primitive::DrawSolid( solid->getChild<BoolPlug>( "enabled" )->getValue() ),
				solid->getChild<BoolPlug>( "override" )->getValue()
			);

			const ValuePlug *wireframe = drawingModePlug()->getChild<ValuePlug>( "wireframe" );
			baseState->add(
				new IECoreGL::Primitive::DrawWireframe( wireframe->getChild<BoolPlug>( "enabled" )->getValue() ),
				wireframe->getChild<BoolPlug>( "override" )->getValue()
			);

			const ValuePlug *points = drawingModePlug()->getChild<ValuePlug>( "points" );
			baseState->add(
				new IECoreGL::Primitive::DrawPoints( points->getChild<BoolPlug>( "enabled" )->getValue() ),
				points->getChild<BoolPlug>( "override" )->getValue()
			);

			const ValuePlug *bound = drawingModePlug()->getChild<ValuePlug>( "bound" );
			baseState->add(
				new IECoreGL::Primitive::DrawBound( bound->getChild<BoolPlug>( "enabled" )->getValue() ),
				bound->getChild<BoolPlug>( "override" )->getValue()
			);

			const ValuePlug *curves = drawingModePlug()->getChild<ValuePlug>( "curves" );
			const ValuePlug *curvesUseGLLines = curves->getChild<ValuePlug>( "useGLLines" );
			baseState->add(
				new IECoreGL::CurvesPrimitive::UseGLLines( curvesUseGLLines->getChild<BoolPlug>( "enabled" )->getValue() ),
				curvesUseGLLines->getChild<BoolPlug>( "override" )->getValue()
			);

			const ValuePlug *curvesInterpolate = curves->getChild<ValuePlug>( "interpolate" );
			baseState->add(
				/// \todo As a general rule we strive for a one-to-one mapping between cortex/gaffer/ui,
				/// but in this case IgnoreBasis is far too technical a term. Consider changing the name
				/// in Cortex.
				new IECoreGL::CurvesPrimitive::IgnoreBasis( !curvesInterpolate->getChild<BoolPlug>( "enabled" )->getValue() ),
				curvesInterpolate->getChild<BoolPlug>( "override" )->getValue()
			);

			sceneGadget()->renderRequestSignal()( sceneGadget() );
		}

		SceneView *m_view;

};

//////////////////////////////////////////////////////////////////////////
// SceneView::ShadingMode implementation
//////////////////////////////////////////////////////////////////////////

class SceneView::ShadingMode : public boost::signals::trackable
{

	public :

		ShadingMode( SceneView *view )
			:	m_view( view )
		{
			view->addChild( new StringPlug( "shadingMode" ) );

			m_preprocessor = new SceneProcessor();
			m_preprocessor->outPlug()->setInput( m_preprocessor->inPlug() );

			view->plugSetSignal().connect( boost::bind( &ShadingMode::plugSet, this, ::_1 ) );
		}

		/// \todo This is exposed so that the SceneView can insert it into
		/// the main preprocessor. We should modify the View base class so
		/// that instead anyone can insert a preprocessor into a chain of preprocessors,
		/// and then individual components like this one can be more self
		/// sufficient.
		SceneProcessor *preprocessor()
		{
			return m_preprocessor.get();
		}

		static void registerShadingMode( const std::string &name, ShadingModeCreator creator )
		{
			shadingModeCreators()[name] = creator;
		}

		static void registeredShadingModes( std::vector<std::string> &names )
		{
			const ShadingModeCreatorMap &m = shadingModeCreators();
			names.clear();
			for( ShadingModeCreatorMap::const_iterator it = m.begin(), eIt = m.end(); it != eIt; ++it )
			{
				names.push_back( it->first );
			}
		}

	private :

		Gaffer::StringPlug *shadingModePlug()
		{
			return m_view->getChild<StringPlug>( "shadingMode" );
		}

		const Gaffer::StringPlug *shadingModePlug() const
		{
			return m_view->getChild<StringPlug>( "shadingMode" );
		}

		void plugSet( const Plug *plug )
		{
			if( plug != shadingModePlug() )
			{
				return;
			}

			const std::string name = shadingModePlug()->getValue();

			SceneProcessorPtr shadingMode = NULL;
			ShadingModes::const_iterator it = m_shadingModes.find( name );
			if( it != m_shadingModes.end() )
			{
				shadingMode = it->second;
			}
			else
			{
				ShadingModeCreatorMap &m = shadingModeCreators();
				ShadingModeCreatorMap::const_iterator it = m.find( name );
				if( it != m.end() )
				{
					shadingMode = it->second();
				}
				if( shadingMode )
				{
					m_shadingModes[name] = shadingMode;
					m_preprocessor->addChild( shadingMode );
				}
			}

			if( shadingMode )
			{
				shadingMode->inPlug()->setInput( m_preprocessor->inPlug() );
				m_preprocessor->outPlug()->setInput( shadingMode->outPlug() );
			}
			else
			{
				m_preprocessor->outPlug()->setInput( m_preprocessor->inPlug() );
			}
		}

		typedef std::map<std::string, SceneView::ShadingModeCreator> ShadingModeCreatorMap;
		typedef std::map<std::string, SceneProcessorPtr> ShadingModes;

		static ShadingModeCreatorMap &shadingModeCreators()
		{
			static ShadingModeCreatorMap g_creators;
			return g_creators;
		}

		SceneView *m_view;
		ShadingModes m_shadingModes;
		SceneProcessorPtr m_preprocessor;

};

//////////////////////////////////////////////////////////////////////////
// SceneView::Grid implementation
//////////////////////////////////////////////////////////////////////////

class SceneView::Grid : public boost::signals::trackable
{

	public :

		Grid( SceneView *view )
			:	m_view( view ), m_node( new GafferScene::Grid ), m_gadget( new SceneGadget )
		{
			m_node->transformPlug()->rotatePlug()->setValue( V3f( 90, 0, 0 ) );

			ValuePlugPtr plug = new ValuePlug( "grid" );
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

		Gaffer::ValuePlug *plug()
		{
			return m_view->getChild<Gaffer::ValuePlug>( "grid" );
		}

		const Gaffer::ValuePlug *plug() const
		{
			return m_view->getChild<Gaffer::ValuePlug>( "grid" );
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
			requestRender();
		}

		void leave()
		{
			m_hovering = false;
			requestRender();
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

			style->renderTranslateHandle( Style::X );
			style->renderTranslateHandle( Style::Y );
			style->renderTranslateHandle( Style::Z );

			Gadget::doRender( style );

			// and pop the matrices back to their original values

			glMatrixMode( GL_PROJECTION );
			glPopMatrix();
			glMatrixMode( GL_MODELVIEW );
			glPopMatrix();

		}

};

} // namespace

class SceneView::Gnomon : public boost::signals::trackable
{

	public :

		Gnomon( SceneView *view )
			:	m_view( view ), m_gadget( new GnomonGadget() )
		{
			ValuePlugPtr plug = new ValuePlug( "gnomon" );
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

		Gaffer::ValuePlug *plug()
		{
			return m_view->getChild<Gaffer::ValuePlug>( "gnomon" );
		}

		const Gaffer::ValuePlug *plug() const
		{
			return m_view->getChild<Gaffer::ValuePlug>( "gnomon" );
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
// SceneView::Camera implementation
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
			requestRender();
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
			requestRender();
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
			requestRender();
		}

		const std::string &getCaption() const
		{
			return m_caption;
		}

		void setIcon( const std::string &icon )
		{
			if( icon == m_icon )
			{
				return;
			}
			m_icon = icon;
			requestRender();
		}

		const std::string &getIcon() const
		{
			return m_icon;
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

				if( !m_icon.empty() )
				{
					IECoreGL::ConstTexturePtr texture = ImageGadget::loadTexture( m_icon );
					const V2f size(
						std::min(
							std::min( m_resolutionGate.size().x, m_resolutionGate.size().y ) / 4.0f,
							100.0f
						)
					);
					style->renderImage(
						Box2f(
							m_resolutionGate.center() + size / 2.0f,
							m_resolutionGate.center() - size / 2.0f
						),
						texture.get()
					);
				}

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
		std::string m_icon;

};

IE_CORE_DECLAREPTR( CameraOverlay )

} // namespace

class SceneView::Camera : public boost::signals::trackable
{

	public :

		Camera( SceneView *view )
			:	m_view( view ),
				m_framed( false ),
				m_standardOptions( new StandardOptions ),
				m_originalCamera( m_view->viewportGadget()->getCamera()->copy() ),
				m_originalCameraTransform( m_view->viewportGadget()->getCameraTransform() ),
				m_lookThroughCameraDirty( false ),
				m_lookThroughCamera( NULL ),
				m_viewportCameraDirty( true ),
				m_overlay( new CameraOverlay )
		{

			// Set up our plugs

			ValuePlugPtr plug = new ValuePlug( "camera", Plug::In, Plug::Default & ~Plug::AcceptsInputs );

			plug->addChild(
				new Gaffer::FloatPlug(
					"fieldOfView",
					Plug::In,
					54.43f,
					0.01f,
					Imath::limits<float>::max(),
					Plug::Default & ~Plug::AcceptsInputs
				)
			);
			plug->addChild(
				new Gaffer::V2fPlug(
					"clippingPlanes", Plug::In,
					V2f( 0.01, 100000 ),
					V2f( 0.0001 ),
					V2f( Imath::limits<float>::max() ),
					Plug::Default & ~Plug::AcceptsInputs
				)
			);

			plug->addChild( new BoolPlug( "lookThroughEnabled", Plug::In, false, Plug::Default & ~Plug::AcceptsInputs ) );
			plug->addChild( new StringPlug( "lookThroughCamera", Plug::In, "", Plug::Default & ~Plug::AcceptsInputs ) );

			view->addChild( plug );

			// Set up our nodes.
			// We use a LightToCamera node filtered to all lights to create camera standins so that we can
			// look through lights
			SetFilterPtr lightFilter = new SetFilter;
			lightFilter->setExpressionPlug()->setValue( "__lights" );

			LightToCameraPtr lightConverter = new LightToCamera;
			lightConverter->inPlug()->setInput( view->inPlug<ScenePlug>() );
			lightConverter->filterPlug()->setInput( lightFilter->outPlug() );

			m_internalNodes.push_back( lightFilter );
			m_internalNodes.push_back( lightConverter );

			// We use a standard options node to disable camera motion blur
			// and overscan because we don't want them applied to the cameras we retrieve with SceneAlgo.
			// We also must disable transform blur and deformation blur, because if either of those is
			// on, the shutter range becomes non-zero and the SceneAlgo transform() method will evaluate the
			// camera at the shutter start rather than the current time, even though its only evaluating a
			// single time sample.

			m_standardOptions->inPlug()->setInput( lightConverter->outPlug() );
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

			m_standardOptions->plugDirtiedSignal().connect( boost::bind( &Camera::plugDirtied, this, ::_1 ) );
			m_plugSetConnection = view->plugSetSignal().connect( boost::bind( &Camera::plugSet, this, ::_1 ) );
			view->plugDirtiedSignal().connect( boost::bind( &Camera::plugDirtied, this, ::_1 ) );
			view->viewportGadget()->preRenderSignal().connect( boost::bind( &Camera::preRender, this ) );
			view->viewportGadget()->viewportChangedSignal().connect( boost::bind( &Camera::viewportChanged, this ) );
			view->viewportGadget()->cameraChangedSignal().connect( boost::bind( &Camera::viewportCameraChanged, this ) );

			connectToViewContext();
			view->contextChangedSignal().connect( boost::bind( &Camera::connectToViewContext, this ) );

		}

		Gaffer::ValuePlug *plug()
		{
			return m_view->getChild<Gaffer::ValuePlug>( "camera" );
		}

		const Gaffer::ValuePlug *plug() const
		{
			return m_view->getChild<Gaffer::ValuePlug>( "camera" );
		}

		const Imath::Box2f &resolutionGate() const
		{
			const_cast<Camera *>( this )->updateLookThroughCamera();
			const_cast<Camera *>( this )->updateViewportCameraAndOverlay();
			return m_overlay->getResolutionGate();
		}

	private :

		const GafferScene::ScenePlug *scenePlug() const
		{
			return m_standardOptions->outPlug();
		}

		Gaffer::FloatPlug *fieldOfViewPlug()
		{
			return plug()->getChild<Gaffer::FloatPlug>( 0 );
		}

		const Gaffer::FloatPlug *fieldOfViewPlug() const
		{
			return plug()->getChild<Gaffer::FloatPlug>( 0 );
		}

		Gaffer::V2fPlug *clippingPlanesPlug()
		{
			return plug()->getChild<Gaffer::V2fPlug>( 1 );
		}

		const Gaffer::V2fPlug *clippingPlanesPlug() const
		{
			return plug()->getChild<Gaffer::V2fPlug>( 1 );
		}

		const Gaffer::BoolPlug *lookThroughEnabledPlug() const
		{
			return plug()->getChild<BoolPlug>( 2 );
		}

		const Gaffer::StringPlug *lookThroughCameraPlug() const
		{
			return plug()->getChild<StringPlug>( 3 );
		}

		void connectToViewContext()
		{
			m_contextChangedConnection = m_view->getContext()->changedSignal().connect( boost::bind( &Camera::contextChanged, this, ::_2 ) );
		}

		void contextChanged( const IECore::InternedString &name )
		{
			if( !boost::starts_with( name.value(), "ui:" ) )
			{
				if( lookThroughEnabledPlug()->getValue() )
				{
					m_lookThroughCameraDirty = m_viewportCameraDirty = true;
				}
			}
		}

		void plugSet( Gaffer::Plug *plug )
		{
			if(
				plug != clippingPlanesPlug() &&
				plug != fieldOfViewPlug()
			)
			{
				return;
			}

			updateLookThroughCamera();

			CameraPtr camera = m_lookThroughCamera ? m_originalCamera : m_view->viewportGadget()->getCamera()->copy();

			V2f clippingPlanes = clippingPlanesPlug()->getValue();
			if( clippingPlanes[1] < clippingPlanes[0] )
			{
				std::swap( clippingPlanes[0], clippingPlanes[1] );
			}
			else if( clippingPlanes[1] == clippingPlanes[0] )
			{
				clippingPlanes[1] += 0.001;
			}
			camera->parameters()["clippingPlanes"] = new V2fData( clippingPlanes );

			camera->parameters()["projection:fov"] = new FloatData( fieldOfViewPlug()->getValue() );

			if( !m_lookThroughCamera )
			{
				m_view->viewportGadget()->setCamera( camera.get() );
			}
		}

		void plugDirtied( Gaffer::Plug *plug )
		{
			if( plug != lookThroughEnabledPlug() && !lookThroughEnabledPlug()->getValue() )
			{
				// No need to do anything if we're turned off.
				return;
			}

			if(
				plug == scenePlug()->childNamesPlug() ||
				plug == scenePlug()->globalsPlug() ||
				plug == scenePlug()->objectPlug() ||
				plug == scenePlug()->transformPlug() ||
				plug == lookThroughEnabledPlug() ||
				plug == lookThroughCameraPlug()
			)
			{
				m_lookThroughCameraDirty = m_viewportCameraDirty = true;
				if( plug == lookThroughEnabledPlug() && lookThroughEnabledPlug()->getValue() )
				{
					m_originalCamera = m_view->viewportGadget()->getCamera()->copy();
				}
				m_view->viewportGadget()->renderRequestSignal()( m_view->viewportGadget() );
			}
		}

		void viewportChanged()
		{
			m_viewportCameraDirty = true;
			m_view->viewportGadget()->renderRequestSignal()( m_view->viewportGadget() );
		}

		void viewportCameraChanged()
		{
			if( !lookThroughEnabledPlug()->getValue() )
			{
				BlockedConnection plugValueSetBlocker( m_plugSetConnection );

				const IECoreScene::Camera *camera = m_view->viewportGadget()->getCamera();
				if( auto clippingPlanes = camera->parametersData()->member<V2fData>( "clippingPlanes" ) )
				{
					clippingPlanesPlug()->setValue( clippingPlanes->readable() );
				}
				if( auto fieldOfView = camera->parametersData()->member<FloatData>( "projection:fov" ) )
				{
					fieldOfViewPlug()->setValue( fieldOfView->readable() );
				}
			}
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
			if( !lookThroughEnabledPlug()->getValue() )
			{
				m_view->viewportGadget()->setCamera( m_originalCamera.get() );
				m_view->viewportGadget()->setCameraEditable( true );
				m_view->hideFilter()->pathsPlug()->setToDefault();
				return;
			}

			// We want to look through a specific camera.
			// Retrieve it.

			Context::Scope scopedContext( m_view->getContext() );

			string cameraPathString = lookThroughCameraPlug()->getValue();
			ConstCompoundObjectPtr globals;
			ConstPathMatcherDataPtr cameraSet;
			M44f cameraTransform;
			string errorMessage;
			try
			{
				const string cameraPathString = cameraPlug()->getValue();
				if( cameraPathString.empty() )
				{
					m_lookThroughCamera = GafferScene::SceneAlgo::camera( scenePlug() ); // primary render camera
				}
				else
				{
					ScenePlug::ScenePath cameraPath;
					ScenePlug::stringToPath( cameraPathString, cameraPath );
					m_lookThroughCamera = GafferScene::SceneAlgo::camera( scenePlug(), cameraPath );
				}
			}
			catch( const std::exception &e )
			{
				// If an invalid path has been entered for the camera, computation will fail.
				// Record the error to go in the caption, and make a default camera to lock to.
				CameraPtr defaultCamera = new IECoreScene::Camera;
				defaultCamera->addStandardParameters();
				m_lookThroughCamera = defaultCamera;
				cameraSet = new PathMatcherData;
				globals = new CompoundObject;
				errorMessage = e.what();
			}

			m_view->viewportGadget()->setCameraEditable( false );
			m_view->hideFilter()->pathsPlug()->setToDefault();

			// When looking through a camera, we hide the camera, since the overlay
			// tells us everything we need to know about the camera. If looking through
			// something else, such as a light, we may want to see the viewport
			// visualisation of what we're looking through.
			const bool isCamera = cameraSet->readable().match( cameraPathString );
			if( isCamera )
			{
				StringVectorDataPtr invisiblePaths = new StringVectorData();
				invisiblePaths->writable().push_back( cameraPathString );
				m_view->hideFilter()->pathsPlug()->setValue( invisiblePaths );
			}

			// Set up the static parts of the overlay. The parts that change when the
			// viewport changes will be updated in updateViewportCameraAndOverlay().

			const Box2fData *cropWindowData = globals->member<Box2fData>( "option:render:cropWindow" );
			if( isCamera && cropWindowData )
			{
				m_overlay->setCropWindow( cropWindowData->readable() );
			}
			else
			{
				m_view->hideFilter()->pathsPlug()->setToDefault();
			}

			if( errorMessage.empty() )
			{
				const V2i resolution = m_lookThroughCamera->parametersData()->member<V2iData>( "resolution" )->readable();
				const float pixelAspectRatio = m_lookThroughCamera->parametersData()->member<FloatData>( "pixelAspectRatio" )->readable();
				m_overlay->setCaption( boost::str(
					boost::format( "%dx%d, %.3f, %s" ) %
						resolution.x % resolution.y %
						pixelAspectRatio %
						(!cameraPathString.empty() ? cameraPathString : "default")
				) );
				m_overlay->setIcon( "" );
			}
			else
			{
				m_overlay->setCaption( "ERROR : " + errorMessage );
				m_overlay->setIcon( "gadgetError.png" );
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

		/// Nodes used in an internal processing network.
		/// Don't need to do anything with them once their set up, but need to hold onto a pointer
		/// so they don't get destroyed
		std::vector< Gaffer::ConstNodePtr > m_internalNodes;

		boost::signals::scoped_connection m_plugSetConnection;
		boost::signals::scoped_connection m_contextChangedConnection;

		/// The default viewport camera - we store this so we can
		/// return to it after looking through a scene camera.
		IECore::CameraPtr m_originalCamera;
		M44f m_originalCameraTransform;
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
	:	View( name, new GafferScene::ScenePlug() ),
		m_sceneGadget( new SceneGadget )
{

	// set up a sensible default camera

	IECore::CameraPtr camera = new IECore::Camera();

	camera->parameters()["projection"] = new IECore::StringData( "perspective" );
	camera->parameters()["projection:fov"] = new IECore::FloatData( 54.43 ); // 35 mm focal length

	M44f matrix;
	matrix.translate( V3f( 0, 0, 1 ) );
	matrix.rotate( IECore::degreesToRadians( V3f( -25, 45, 0 ) ) );
	camera->setTransform( new IECore::MatrixTransform( matrix ) );

	viewportGadget()->setCamera( camera.get() );

	// add plugs and signal handling for them

	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new IntPlug( "minimumExpansionDepth", Plug::In, 0, 0, Imath::limits<int>::max(), Plug::Default & ~Plug::AcceptsInputs ) );

	plugSetSignal().connect( boost::bind( &SceneView::plugSet, this, ::_1 ) );

	// set up our gadgets

	viewportGadget()->setPrimaryChild( m_sceneGadget );
	viewportGadget()->keyPressSignal().connect( boost::bind( &SceneView::keyPress, this, ::_1, ::_2 ) );

	m_sceneGadget->setContext( getContext() );

	m_drawingMode = boost::make_shared<DrawingMode>( this );
	m_shadingMode = boost::make_shared<ShadingMode>( this );
	m_camera = boost::make_shared<LookThrough>( this );
	m_grid = boost::make_shared<Grid>( this );
	m_gnomon = boost::make_shared<Gnomon>( this );

	//////////////////////////////////////////////////////////////////////////
	// add a preprocessor which monkeys with the scene before it is displayed.
	//////////////////////////////////////////////////////////////////////////

	NodePtr preprocessor = new Node();
	ScenePlugPtr preprocessorInput = new ScenePlug( "in" );
	preprocessor->addChild( preprocessorInput );

	// add a node for hiding things

	StandardAttributesPtr hide = new StandardAttributes( "hide" );
	hide->attributesPlug()->getChild<ValuePlug>( "visibility" )->getChild<BoolPlug>( "enabled" )->setValue( true );
	hide->attributesPlug()->getChild<ValuePlug>( "visibility" )->getChild<BoolPlug>( "value" )->setValue( false );

	preprocessor->addChild( hide );
	hide->inPlug()->setInput( preprocessorInput );

	PathFilterPtr hideFilter = new PathFilter( "hideFilter" );
	preprocessor->addChild( hideFilter );
	hide->filterPlug()->setInput( hideFilter->outPlug() );

	// add in the node from the ShadingMode

	preprocessor->addChild( m_shadingMode->preprocessor() );
	m_shadingMode->preprocessor()->inPlug()->setInput( hide->outPlug() );

	// make the output for the preprocessor

	ScenePlugPtr preprocessorOutput = new ScenePlug( "out", Plug::Out );
	preprocessor->addChild( preprocessorOutput );
	preprocessorOutput->setInput( m_shadingMode->preprocessor()->outPlug() );

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

Gaffer::ValuePlug *SceneView::cameraPlug()
{
	return m_camera->plug();
}

const Gaffer::ValuePlug *SceneView::cameraPlug() const
{
	return m_camera->plug();
}

Gaffer::ValuePlug *SceneView::gridPlug()
{
	return m_grid->plug();
}

const Gaffer::ValuePlug *SceneView::gridPlug() const
{
	return m_grid->plug();
}

Gaffer::ValuePlug *SceneView::gnomonPlug()
{
	return m_gnomon->plug();
}

const Gaffer::ValuePlug *SceneView::gnomonPlug() const
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
	View::setContext( context );
	m_sceneGadget->setContext( context );
}

const Box2f &SceneView::resolutionGate() const
{
	return m_camera->resolutionGate();
}

void SceneView::registerShadingMode( const std::string &name, ShadingModeCreator creator )
{
	ShadingMode::registerShadingMode( name, creator );
}

void SceneView::registeredShadingModes( std::vector<std::string> &names )
{
	ShadingMode::registeredShadingModes( names );
}

void SceneView::contextChanged( const IECore::InternedString &name )
{
	if( name.value() == "ui:scene:selectedPaths" )
	{
		// If only the selection has changed then we can just update the selection
		// on our existing scene representation.
		PathMatcher selection = ContextAlgo::getSelectedPaths( getContext() );
		/// \todo Store selection as PathMatcherData within the context, so we don't need
		/// to contruct a new one.
		GafferScene::PathMatcherDataPtr sg = new GafferScene::PathMatcherData( selection );
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

	b = m_sceneGadget->bound();
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
	else if( event.key == "F" )
	{
		Imath::Box3f b = framingBound();
		if( !b.isEmpty() && viewportGadget()->getCameraEditable() )
		{
			viewportGadget()->frame( b );
			if( event.modifiers == KeyEvent::Control )
			{
				viewportGadget()->fitClippingPlanes( b );
			}
			return true;
		}
	}
	else if( event.key == "K" && event.modifiers == KeyEvent::Control )
	{
		if( viewportGadget()->getCameraEditable() )
		{
			viewportGadget()->fitClippingPlanes( framingBound() );
		}
	}

	return false;
}

void SceneView::frame( const GafferScene::PathMatcher &filter, const Imath::V3f &direction )
{
	Imath::Box3f bound;

	Context::Scope scope( getContext() );

	PathMatcher paths;
	const ScenePlug *scene = inPlug<const ScenePlug>();
	SceneAlgo::matchingPaths( filter, scene, paths );

	for( PathMatcher::Iterator it = paths.begin(); it != paths.end(); ++it )
	{
		Imath::Box3f objectBound = scene->bound( *it );
		Imath::M44f objectFullTransform = scene->fullTransform( *it );
		bound.extendBy( transform( objectBound, objectFullTransform ) );
	}

	viewportGadget()->frame( bound, direction );
}

void SceneView::expandSelection( size_t depth )
{
	PathMatcher &selection = const_cast<GafferScene::PathMatcherData *>( m_sceneGadget->getSelection() )->writable();

	Context::Scope scope( getContext() );
	selection = ContextAlgo::expandDescendants( getContext(), selection, preprocessedInPlug<ScenePlug>(), depth - 1 );

	ContextAlgo::setSelectedPaths( getContext(), selection );
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

	PathMatcher expanded = ContextAlgo::getExpandedPaths( getContext() );

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

	// \todo: add ContextAlgo::collapse() so we can do the collapse in-place
	ContextAlgo::setExpandedPaths( getContext(), expanded );
	ContextAlgo::setSelectedPaths( getContext(), m_sceneGadget->getSelection()->readable() );
}

void SceneView::plugSet( Gaffer::Plug *plug )
{
	if( plug == minimumExpansionDepthPlug() )
	{
		m_sceneGadget->setMinimumExpansionDepth( minimumExpansionDepthPlug()->getValue() );
	}
}
