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

#include "GafferSceneUI/SceneView.h"

#include "GafferSceneUI/ScriptNodeAlgo.h"

#include "GafferScene/AttributeQuery.h"
#include "GafferScene/CustomAttributes.h"
#include "GafferScene/DeleteObject.h"
#include "GafferScene/DeleteOutputs.h"
#include "GafferScene/Grid.h"
#include "GafferScene/LightToCamera.h"
#include "GafferScene/PathFilter.h"
#include "GafferScene/SceneAlgo.h"
#include "GafferScene/SetFilter.h"
#include "GafferScene/StandardOptions.h"

#include "GafferUI/ImageGadget.h"
#include "GafferUI/Pointer.h"
#include "GafferUI/Style.h"

#include "Gaffer/Context.h"
#include "Gaffer/MetadataAlgo.h"
#include "Gaffer/NameSwitch.h"
#include "Gaffer/PlugAlgo.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/StringPlug.h"

#include "IECoreGL/Camera.h"
#include "IECoreGL/CurvesPrimitive.h"
#include "IECoreGL/GL.h"
#include "IECoreGL/PointsPrimitive.h"
#include "IECoreGL/Primitive.h"
#include "IECoreGL/State.h"

#include "IECore/AngleConversion.h"
#include "IECore/VectorTypedData.h"

#include "Imath/ImathMatrixAlgo.h"

#include "boost/algorithm/string/predicate.hpp"
#include "boost/bind/bind.hpp"
#include "boost/bind/placeholders.hpp"

#include "fmt/format.h"

#include <unordered_map>

using namespace std;
using namespace boost::placeholders;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferUI;
using namespace GafferScene;
using namespace GafferSceneUI;

//////////////////////////////////////////////////////////////////////////
// SceneView::Render implementation
//////////////////////////////////////////////////////////////////////////

class SceneView::Renderer : public Gaffer::Signals::Trackable
{

	public :

		Renderer( SceneView *view )
			:	m_view( view )
		{
			view->addChild( new Plug( "renderer" ) );
			rendererPlug()->addChild( new StringPlug( "name", Plug::In, "OpenGL" ) );

			m_sceneProcessor = new SceneProcessor;
			m_sceneProcessor->inPlug()->setInput( m_view->inPlug() );

			NameSwitchPtr settingsSwitch = new NameSwitch( "SettingsSwitch" );
			settingsSwitch->setup( m_sceneProcessor->inPlug() );
			settingsSwitch->inPlugs()->getChild<NameValuePlug>( 0 )->valuePlug()->setInput( m_sceneProcessor->inPlug() );
			settingsSwitch->selectorPlug()->setInput( rendererNamePlug() );
			m_sceneProcessor->addChild( settingsSwitch );

			for( auto &r : rendererMap() )
			{
				SceneProcessorPtr settingsNode = r.second();
				settingsNode->setName( r.first + "Settings" );
				settingsNode->inPlug()->setInput( m_sceneProcessor->inPlug() );
				NameValuePlug *next = static_cast<NameValuePlug *>( settingsSwitch->inPlugs()->next() );
				next->namePlug()->setValue( r.first );
				next->valuePlug()->setInput( settingsNode->outPlug() );
				m_sceneProcessor->addChild( settingsNode );

				string settingsPlugName = r.first;
				settingsPlugName[0] = std::tolower( settingsPlugName[0] );
				PlugPtr settingsPlug = new Plug( settingsPlugName );
				for( auto &plug : Plug::InputRange( *settingsNode ) )
				{
					if( plug == settingsNode->inPlug() || !plug->getFlags( Plug::AcceptsInputs ) )
					{
						continue;
					}
					PlugPtr promoted = plug->createCounterpart( plug->getName(), plug->direction() );
					settingsPlug->addChild( promoted );
					plug->setInput( promoted );
					MetadataAlgo::copy( plug.get(), promoted.get() );
				}
				rendererPlug()->addChild( settingsPlug );
			}

			DeleteOutputsPtr deleteOutputs = new DeleteOutputs;
			deleteOutputs->inPlug()->setInput( static_cast<NameValuePlug *>( settingsSwitch->outPlug() )->valuePlug() );
			deleteOutputs->namesPlug()->setValue( "*" );
			m_sceneProcessor->addChild( deleteOutputs );

			m_sceneProcessor->outPlug()->setInput( deleteOutputs->outPlug() );

			m_view->plugSetSignal().connect( boost::bind( &Renderer::plugSet, this, ::_1 ) );
		}

		using SettingsCreator = std::function<GafferScene::SceneProcessorPtr ()>;

		static void registerRenderer( const std::string &name, const SettingsCreator &settingsCreator )
		{
			rendererMap()[name] = settingsCreator;
		}

		static std::vector<std::string> registeredRenderers()
		{
			vector<string> result;
			for( const auto &r : rendererMap() )
			{
				result.push_back( r.first );
			}
			return result;
		}

		GafferScene::SceneProcessor *preprocessor()
		{
			return m_sceneProcessor.get();
		}

	private :

		Plug *rendererPlug()
		{
			return m_view->getChild<Plug>( "renderer" );
		}

		StringPlug *rendererNamePlug()
		{
			return rendererPlug()->getChild<StringPlug>( "name" );
		}

		void plugSet( const Gaffer::Plug *plug )
		{
			if( plug == rendererNamePlug() )
			{
				static_cast<SceneGadget *>( m_view->viewportGadget()->getPrimaryChild() )->setRenderer(
					rendererNamePlug()->getValue()
				);
			}
		}

		using RendererMap = unordered_map<string, SettingsCreator>;
		static RendererMap &rendererMap()
		{
			static RendererMap g_m = {
				{
					"OpenGL",
					[] {
						SceneProcessorPtr result = new SceneProcessor;
						result->outPlug()->setInput( result->inPlug() );
						return result;
					}
				}
			};
			return g_m;
		}

		GafferScene::SceneProcessorPtr m_sceneProcessor;
		SceneView *m_view;

};

//////////////////////////////////////////////////////////////////////////
// SceneView::SelectionMask implementation
//////////////////////////////////////////////////////////////////////////

class SceneView::SelectionMask : public Signals::Trackable
{

	public :

		SelectionMask( SceneView *view )
			:	m_view( view )
		{
			view->addChild(
				new StringVectorDataPlug(
					"selectionMask",
					Plug::In,
					new StringVectorData( { "Renderable", "NullObject" } )
				)
			);

			updateSelectionMask();

			view->plugSetSignal().connect( boost::bind( &SelectionMask::plugSet, this, ::_1 ) );
		}

	private :

		Gaffer::StringVectorDataPlug *selectionMaskPlug()
		{
			return m_view->getChild<StringVectorDataPlug>( "selectionMask" );
		}

		SceneGadget *sceneGadget()
		{
			return static_cast<SceneGadget *>( m_view->viewportGadget()->getPrimaryChild() );
		}

		void plugSet( const Plug *plug )
		{
			if( plug == selectionMaskPlug() )
			{
				updateSelectionMask();
			}
		}

		void updateSelectionMask()
		{
			sceneGadget()->setSelectionMask(
				selectionMaskPlug()->isSetToDefault() ? nullptr : selectionMaskPlug()->getValue().get()
			);
		}

		SceneView *m_view;

};

//////////////////////////////////////////////////////////////////////////
// SceneView::DrawingMode implementation
//////////////////////////////////////////////////////////////////////////

class SceneView::DrawingMode : public Signals::Trackable
{

	public :

		DrawingMode( SceneView *view )
			:	m_view( view )
		{

			// Plugs controlling OpenGL render options. We use these to
			// drive `SceneGadget::setOpenGLOptions()` directly.

			ValuePlugPtr drawingMode = new ValuePlug( "drawingMode" );
			m_view->addChild( drawingMode );

			drawingMode->addChild( new BoolPlug( "solid", Plug::In, true ) );
			drawingMode->addChild( new BoolPlug( "wireframe" ) );
			drawingMode->addChild( new BoolPlug( "points" ) );

			ValuePlugPtr curves = new ValuePlug( "curvesPrimitive" );
			drawingMode->addChild( curves );
			curves->addChild( new BoolPlug( "useGLLines", Plug::In, true ) );
			curves->addChild( new BoolPlug( "interpolate" ) );

			ValuePlugPtr points = new ValuePlug( "pointsPrimitive" );
			drawingMode->addChild( points );
			points->addChild( new BoolPlug( "useGLPoints", Plug::In, true ) );

			// A preprocessor which modifies the scene before it is displayed by
			// the SceneGadget. We use this for drawing settings that aren't
			// simple OpenGL options.

			m_preprocessor = new SceneProcessor();

			CustomAttributesPtr customAttributes = new CustomAttributes();
			m_preprocessor->addChild( customAttributes );
			customAttributes->inPlug()->setInput( m_preprocessor->inPlug() );
			customAttributes->globalPlug()->setValue( true );
			CompoundDataPlug *attr = customAttributes->attributesPlug();

			StandardOptionsPtr standardOptions = new StandardOptions();
			m_preprocessor->addChild( standardOptions );
			standardOptions->inPlug()->setInput( customAttributes->outPlug() );
			m_preprocessor->outPlug()->setInput( standardOptions->outPlug() );

			// Included purposes

			auto *includedPurposesPlug = standardOptions->optionsPlug()->getChild<NameValuePlug>( "includedPurposes" );
			auto viewIncludedPurposesPlug = boost::static_pointer_cast<NameValuePlug>(
				includedPurposesPlug->createCounterpart( "includedPurposes", Plug::In )
			);
			viewIncludedPurposesPlug->enabledPlug()->setValue( true );
			drawingMode->addChild( viewIncludedPurposesPlug );
			includedPurposesPlug->setInput( viewIncludedPurposesPlug );

			// Visualiser settings.

			ValuePlugPtr visualiser = new ValuePlug( "visualiser" );
			drawingMode->addChild( visualiser );

			//    gl:visualiser:frustum

			StringPlugPtr frustrumAttrValuePlug = new StringPlug( "value", Plug::In, "whenSelected" );

			NameValuePlugPtr frustumAttrPlug = new Gaffer::NameValuePlug( "gl:visualiser:frustum", frustrumAttrValuePlug, true, "frustum" );
			attr->addChild( frustumAttrPlug );
			PlugPtr frustumViewPlug = frustrumAttrValuePlug->createCounterpart( "frustum", Plug::In );
			visualiser->addChild( frustumViewPlug );
			frustrumAttrValuePlug->setInput( frustumViewPlug );

			//    gl:visualiser:scale

			FloatPlugPtr visualiserScaleAttrValuePlug = new FloatPlug( "value", Plug::In, 1.0f, 0.01f );

			NameValuePlugPtr visualiserScaleAttrPlug = new Gaffer::NameValuePlug( "gl:visualiser:scale", visualiserScaleAttrValuePlug, true, "scale" );
			attr->addChild( visualiserScaleAttrPlug );
			PlugPtr visualiserScaleViewPlug = visualiserScaleAttrValuePlug->createCounterpart( "scale", Plug::In );
			visualiser->addChild( visualiserScaleViewPlug );
			visualiserScaleAttrValuePlug->setInput( visualiserScaleViewPlug );

			// Light specific :

			ValuePlugPtr light = new ValuePlug( "light" );
			drawingMode->addChild( light );

			//    gl:light:drawingMode

			StringPlugPtr lightModeAttrValuePlug = new StringPlug( "value", Plug::In, "texture" );

			NameValuePlugPtr lightModeAttrPlug = new Gaffer::NameValuePlug( "gl:light:drawingMode", lightModeAttrValuePlug, true, "lightDrawingMode" );
			attr->addChild( lightModeAttrPlug );
			PlugPtr lightModeViewPlug = lightModeAttrValuePlug->createCounterpart( "drawingMode", Plug::In );
			light->addChild( lightModeViewPlug );
			lightModeAttrValuePlug->setInput( lightModeViewPlug );

			//    gl:light:frustumScale

			FloatPlugPtr lightFrustumScaleAttrValuePlug = new FloatPlug( "value", Plug::In , 1.0f, 0.01f );

			NameValuePlugPtr lightFrustumScaleAttrPlug = new Gaffer::NameValuePlug( "gl:light:frustumScale", lightFrustumScaleAttrValuePlug, true, "lightFrustumScale" );
			attr->addChild( lightFrustumScaleAttrPlug );
			PlugPtr lightFrustumScaleViewPlug = lightFrustumScaleAttrValuePlug->createCounterpart( "frustumScale", Plug::In );
			light->addChild( lightFrustumScaleViewPlug );
			lightFrustumScaleAttrValuePlug->setInput( lightFrustumScaleViewPlug );

			// Initialise renderer and event tracking

			updateOpenGLOptions();

			view->plugSetSignal().connect( boost::bind( &DrawingMode::plugSet, this, ::_1 ) );
		}

		/// @see SceneProcessor::preprocessor
		SceneProcessor *preprocessor()
		{
			return m_preprocessor.get();
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
				updateOpenGLOptions();
			}
		}

		void updateOpenGLOptions()
		{
			IECore::CompoundObjectPtr options = sceneGadget()->getOpenGLOptions()->copy();
			GraphComponent *curvesPlug = drawingModePlug()->getChild( "curvesPrimitive" );
			GraphComponent *pointsPlug = drawingModePlug()->getChild( "pointsPrimitive" );

			options->members()["gl:primitive:solid"] = new BoolData( drawingModePlug()->getChild<BoolPlug>( "solid" )->getValue() );
			options->members()["gl:primitive:wireframe"] = new BoolData( drawingModePlug()->getChild<BoolPlug>( "wireframe" )->getValue() );
			options->members()["gl:primitive:points"] = new BoolData( drawingModePlug()->getChild<BoolPlug>( "points" )->getValue() );
			options->members()["gl:curvesPrimitive:useGLLines"] = new BoolData( curvesPlug->getChild<BoolPlug>( "useGLLines" )->getValue() );
			/// \todo As a general rule we strive for a one-to-one mapping between cortex/gaffer/ui,
			/// but in this case IgnoreBasis is far too technical a term. Consider changing the name
			/// in Cortex.
			options->members()["gl:curvesPrimitive:ignoreBasis"] = new BoolData( !curvesPlug->getChild<BoolPlug>( "interpolate" )->getValue() );
			options->members()["gl:pointsPrimitive:useGLPoints"] = new StringData(
				pointsPlug->getChild<BoolPlug>( "useGLPoints" )->getValue() ?
				"forAll" :
				"forGLPoints"
			);

			sceneGadget()->setOpenGLOptions( options.get() );
		}

		SceneProcessorPtr m_preprocessor;

		SceneView *m_view;

};

//////////////////////////////////////////////////////////////////////////
// SceneView::ShadingMode implementation
//////////////////////////////////////////////////////////////////////////

class SceneView::ShadingMode : public Signals::Trackable
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

			SceneProcessorPtr shadingMode = nullptr;
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

		using ShadingModeCreatorMap = std::map<std::string, SceneView::ShadingModeCreator>;
		using ShadingModes = std::map<std::string, SceneProcessorPtr>;

		static ShadingModeCreatorMap &shadingModeCreators()
		{
			static auto g_creators = new ShadingModeCreatorMap;
			return *g_creators;
		}

		SceneView *m_view;
		ShadingModes m_shadingModes;
		SceneProcessorPtr m_preprocessor;

};

//////////////////////////////////////////////////////////////////////////
// SceneView::Grid implementation
//////////////////////////////////////////////////////////////////////////

class SceneView::Grid : public Gaffer::Node
{

	public :

		Grid( SceneView *view )
			:	m_gadget( new SceneGadget )
		{
			// Add plugs to represent our settings

			storeIndexOfNextChild( g_firstChildIndex );

			addChild( new BoolPlug( "visible", Plug::In, true ) );
			addChild( new V2fPlug( "dimensions", Plug::In, V2f( 10.0f ), V2f( 0.0f ) ) );

			// Wire up an internal grid node

			addChild( new GafferScene::Grid( "__grid" ) );

			grid()->dimensionsPlug()->setInput( dimensionsPlug() );
			grid()->transformPlug()->rotatePlug()->setValue( V3f( 90, 0, 0 ) );
			grid()->gridColorPlug()->setValue( Color3f( 0.21 ) );
			grid()->gridPixelWidthPlug()->setValue( 1 );
			grid()->borderColorPlug()->setValue( Color3f( 0.1 ) );

			// And create a gadget for displaying it

			m_gadget->setMinimumExpansionDepth( 1 );
			m_gadget->setScene( grid()->outPlug() );
			m_gadget->setLayer( Gadget::Layer::MidFront );

			view->viewportGadget()->setChild( "__grid", m_gadget );

			// Parent ourselves to the View, and promote our plugs so that
			// they can be edited publicly.

			view->setChild( "__grid", this );
			PlugPtr promoted = new Plug();
			view->setChild( "grid", promoted );

			for( size_t i = g_firstChildIndex; i < children().size() - 1; ++i )
			{
				PlugAlgo::promote( getChild<Plug>( i ), promoted.get() );
			}

			// Connect to `plugDirtied()` so we can update when our settings
			// change.

			plugDirtiedSignal().connect( boost::bind( &Grid::plugDirtied, this, ::_1 ) );
		}

		SceneGadget *gadget()
		{
			return m_gadget.get();
		}

		const SceneGadget *gadget() const
		{
			return m_gadget.get();
		}

	private :

		BoolPlug *visiblePlug()
		{
			return getChild<BoolPlug>( g_firstChildIndex );
		}

		V2fPlug *dimensionsPlug()
		{
			return getChild<V2fPlug>( g_firstChildIndex + 1 );
		}

		GafferScene::Grid *grid()
		{
			return getChild<GafferScene::Grid>( g_firstChildIndex + 2 );
		}

		void plugDirtied( Gaffer::Plug *plug )
		{
			if( plug == visiblePlug() )
			{
				m_gadget->setVisible( visiblePlug()->getValue() );
			}
		}

		SceneGadgetPtr m_gadget;

		static size_t g_firstChildIndex;

};

size_t SceneView::Grid::g_firstChildIndex = 0;

//////////////////////////////////////////////////////////////////////////
// SceneView::Gnomon implementation
//////////////////////////////////////////////////////////////////////////

namespace
{

class GnomonGadget : public GafferUI::Gadget
{

	public :

		GnomonGadget()
		{
		}

	protected :

		Imath::Box3f renderBound() const override
		{
			// We have no fixed object-space bound.
			Box3f b;
			b.makeInfinite();
			return b;
		}

		void renderLayer( Layer layer, const Style *style, RenderReason reason ) const final
		{
			assert( layer == Layer::MidFront );

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
			if( isSelectionRender( reason ) )
			{
				glMultMatrixd( IECoreGL::Selector::currentSelector()->postProjectionMatrix().getValue() );
			}

			// this is our post projection matrix, which scales down to the size we want and
			// translates into the corner.
			glTranslatef( -1.0f + pixelWidth / (float)viewport.x, -1.0f + pixelWidth / (float)viewport.y, 0.0f ),
			glScalef( pixelWidth / (float)viewport.x, pixelWidth / (float)viewport.y, 1 );

			// this is our projection matrix - a simple orthographic projection.
			glOrtho( -1, 1, -1, 1, 0, 10 );

			// now for our model-view matrix. this is the same as is used by the main
			// view, but with the translation reset. this means when we draw our
			// children at the origin, they will be centered within camera space.

			glMatrixMode( GL_MODELVIEW );
			glPushMatrix();

			M44f m = IECoreGL::Camera::matrix();
			m[3][0] = 0;
			m[3][1] = 0;
			m[3][2] = -2;

			glMatrixMode( GL_MODELVIEW );
			glLoadIdentity();
			glMultMatrixf( m.getValue() );

			// now we can defer to the derived class to draw
			// the required content

			renderGnomon( style );

			// and pop the matrices back to their original values

			glMatrixMode( GL_PROJECTION );
			glPopMatrix();
			glMatrixMode( GL_MODELVIEW );
			glPopMatrix();

		}

		unsigned layerMask() const override
		{
			return (unsigned)Layer::MidFront;
		}

		virtual void renderGnomon( const Style *style ) const = 0;

};

class GnomonAxes : public GnomonGadget
{

	protected :

		void renderGnomon( const Style *style ) const override
		{
			style->renderTranslateHandle( Style::X );
			style->renderTranslateHandle( Style::Y );
			style->renderTranslateHandle( Style::Z );
		}

};

class GnomonPlane : public GnomonGadget
{

	public :

		GnomonPlane()
			:	GnomonGadget(), m_hovering( false )
		{
			enterSignal().connect( boost::bind( &GnomonPlane::enter, this ) );
			leaveSignal().connect( boost::bind( &GnomonPlane::leave, this ) );
		}

	protected :

		void renderGnomon( const Style *style ) const override
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
			dirty( DirtyType::Render );
		}

		void leave()
		{
			m_hovering = false;
			dirty( DirtyType::Render );
		}

		bool m_hovering;

};

} // namespace

class SceneView::Gnomon : public Signals::Trackable
{

	public :

		Gnomon( SceneView *view )
			:	m_view( view ), m_gadget( new Gadget() )
		{
			ValuePlugPtr plug = new ValuePlug( "gnomon" );
			view->addChild( plug );

			plug->addChild( new BoolPlug( "visible", Plug::In, true ) );

			m_gadget->setChild( "axes", new GnomonAxes() );

			GadgetPtr xyPlane = new GnomonPlane();
			GadgetPtr yzPlane = new GnomonPlane();
			GadgetPtr xzPlane = new GnomonPlane();

			yzPlane->setTransform( M44f().rotate( V3f( 0, -M_PI / 2.0f, 0 ) ) );
			xzPlane->setTransform( M44f().rotate( V3f( M_PI / 2.0f, 0, 0 ) ) );

			// Gadget names correspond to the names of the free cameras they
			// will switch to when pressed.
			m_gadget->setChild( "front", xyPlane );
			m_gadget->setChild( "side", yzPlane );
			m_gadget->setChild( "top", xzPlane );

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
			if(
				plug == this->plug() ||
				plug == m_view->cameraPlug()->getChild<BoolPlug>( "lookThroughEnabled" )
			)
			{
				update();
			}
		}

		void update()
		{
			m_gadget->setVisible( plug()->getChild<BoolPlug>( "visible" )->getValue() );
			const bool planesVisible = !m_view->cameraPlug()->getChild<BoolPlug>( "lookThroughEnabled" )->getValue();
			for( auto &name : { "top", "front", "side" } )
			{
				m_gadget->getChild<Gadget>( name )->setVisible( planesVisible );
			}
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

			auto freeCameraPlug = m_view->cameraPlug()->getChild<StringPlug>( "freeCamera" );
			freeCameraPlug->setValue(
				freeCameraPlug->getValue() == "perspective" ? gadget->getName() : "perspective"
			);

			return true;
		}

		SceneView *m_view;
		GadgetPtr m_gadget;

};

class SceneView::FPS : public Signals::Trackable
{

	public :

		FPS( SceneView *view )
			:	m_view( view ), m_gadget( new FPSGadget() )
		{
			ValuePlugPtr plug = new ValuePlug( "fps" );
			view->addChild( plug );

			plug->addChild( new BoolPlug( "visible", Plug::In, false ) );

			view->viewportGadget()->setChild( "__fps", m_gadget );

			view->plugDirtiedSignal().connect( boost::bind( &FPS::plugDirtied, this, ::_1 ) );

			update();
		}

		Gaffer::ValuePlug *plug()
		{
			return m_view->getChild<Gaffer::ValuePlug>( "fps" );
		}

		const Gaffer::ValuePlug *plug() const
		{
			return m_view->getChild<Gaffer::ValuePlug>( "fps" );
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
		FPSGadgetPtr m_gadget;

};

//////////////////////////////////////////////////////////////////////////
// SceneView::Camera implementation
//////////////////////////////////////////////////////////////////////////

namespace
{

class CameraOverlay : public GafferUI::Gadget
{

	public :

		CameraOverlay()
			:	Gadget()
		{
		}

		Imath::Box3f bound() const override
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
			dirty( DirtyType::Render );
		}

		const Box2f &getResolutionGate() const
		{
			return m_resolutionGate;
		}

		// Specified in raster space.
		void setApertureGate( const Box2f &apertureGate )
		{
			if( apertureGate == m_apertureGate )
			{
				return;
			}
			m_apertureGate = apertureGate;
			dirty( DirtyType::Render );
		}

		const Box2f &getApertureGate() const
		{
			return m_apertureGate;
		}

		// Specified in 0-1 space relative to resolution gate
		void setCropWindow( const Box2f &cropWindow )
		{
			if( cropWindow == m_cropWindow )
			{
				return;
			}
			m_cropWindow = cropWindow;
			dirty( DirtyType::Render );
		}

		const Box2f &getCropWindow() const
		{
			return m_cropWindow;
		}

		// left, top, right, bottom
		void setOverscan( const V4f &overscan )
		{
			if( overscan == m_overscan )
			{
				return;
			}
			m_overscan = overscan;
			dirty( DirtyType::Render );
		}

		const V4f &getOverscan() const
		{
			return m_overscan;
		}

		void setCaption( const std::string &caption )
		{
			if( caption == m_caption )
			{
				return;
			}
			m_caption = caption;
			dirty( DirtyType::Render );
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
			dirty( DirtyType::Render );
		}

		const std::string &getIcon() const
		{
			return m_icon;
		}

	protected :

		void renderLayer( Layer layer, const Style *style, RenderReason reason ) const override
		{
			assert( layer == Layer::MidFront );

			if( isSelectionRender( reason ) || ( m_resolutionGate.isEmpty() && m_apertureGate.isEmpty() ) )
			{
				return;
			}

			const ViewportGadget *viewportGadget = ancestor<ViewportGadget>();
			ViewportGadget::RasterScope rasterScope( viewportGadget );

			glPushAttrib( GL_CURRENT_BIT | GL_LINE_BIT | GL_ENABLE_BIT );

			if( !m_apertureGate.isEmpty() )
			{
				glEnable( GL_LINE_SMOOTH );
				glColor4f( 0.4, 0, 0, 1.0 );
				glLineWidth( 0.5f );
				style->renderRectangle( m_apertureGate );
				glLineWidth( 2.0f );

				// The start and end distance for the crop marks
				const float startDist = 5;
				const float endDist = 20;

				for( int up = 0; up < 2; up++ )
				{
					for( int right = 0; right < 2; right++ )
					{
						V2f curCorner(
							right ? m_apertureGate.max.x : m_apertureGate.min.x,
							up ? m_apertureGate.max.y : m_apertureGate.min.y
						);

						V2f dirX( right ? 1 : -1, 0 );
						V2f dirY( 0, up ? 1 : -1 );

						style->renderRectangle(
							Box2f( curCorner + startDist * dirY, curCorner + endDist * dirY )
						);
						style->renderRectangle(
							Box2f( curCorner + startDist * dirX, curCorner + endDist * dirX )
						);
					}
				}
			}

			if( !m_resolutionGate.isEmpty() )
			{
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

				if( m_overscan[0] != 0.0f || m_overscan[1] != 0.0f || m_overscan[2] != 0.0f || m_overscan[3] != 0.0f )
				{
					glLineStipple( 2, 0x3333 );
					glEnable( GL_LINE_STIPPLE );

					const V2f gateSize = m_resolutionGate.size();
					style->renderRectangle( Box2f(
						V2f(
							m_resolutionGate.min.x - ( m_overscan[0] * gateSize.x ),
							m_resolutionGate.min.y - ( m_overscan[1] * gateSize.y )
						),
						V2f(
							m_resolutionGate.max.x + ( m_overscan[2] * gateSize.x ),
							m_resolutionGate.max.y + ( m_overscan[3] * gateSize.y )
						)
					) );

					glDisable( GL_LINE_STIPPLE );
				}

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
			}

			glPopAttrib();
		}

		unsigned layerMask() const override
		{
			return (unsigned)Layer::MidFront;
		}

		Imath::Box3f renderBound() const override
		{
			// we draw in raster space so don't have a sensible bound
			Box3f b;
			b.makeInfinite();
			return b;
		}

	private :

		Box2f m_resolutionGate;
		Box2f m_apertureGate;
		Box2f m_cropWindow;
		V4f m_overscan;
		std::string m_caption;
		std::string m_icon;

};

IE_CORE_DECLAREPTR( CameraOverlay )

struct FreeCamera
{

	static FreeCamera createFromViewport( const ViewportGadget *viewport )
	{
		return {
			viewport->getCamera()->copy(),
			viewport->getCameraTransform(),
			viewport->getCenterOfInterest()
		};
	}

	static FreeCamera createOrthographic( int viewAxis )
	{
		CameraPtr camera = new Camera;
		camera->setProjection( "orthographic" );
		camera->setAperture( V2f( 20 ) );
		camera->setFilmFit( Camera::FilmFit::Fit );

		const float offset = 1000;
		M44f transform;
		switch( viewAxis )
		{
			case 0 :
				transform = computeLocalFrame( V3f( offset, 0, 0 ), V3f( 0, 0, -1 ), V3f( 1, 0, 0 ) );
				break;
			case 1 :
				transform = computeLocalFrame( V3f( 0, offset, 0 ), V3f( 1, 0, 0 ), V3f( 0, 1, 0 ) );
				break;
			case 2 :
				transform = computeLocalFrame( V3f( 0, 0, offset ), V3f( 1, 0, 0 ), V3f( 0, 0, 1 ) );
				break;
		}

		return {
			camera,
			transform,
			1.0f
		};
	}

	void applyToViewport( ViewportGadget *viewport ) const
	{
		viewport->setCamera( camera.get() );
		viewport->setCameraTransform( transform );
		viewport->setCenterOfInterest( centerOfInterest );
		viewport->setTumblingEnabled( camera->getProjection() == "perspective" );
	}

	void applyToPlugs( FloatPlug *fieldOfViewPlug, V2fPlug *clippingPlanesPlug )
	{
		clippingPlanesPlug->setValue( camera->getClippingPlanes() );
		if( camera->getProjection() == "perspective" )
		{
			fieldOfViewPlug->setValue( camera->calculateFieldOfView()[0] );
		}
	}

	void updateFromPlugs( FloatPlug *fieldOfViewPlug, V2fPlug *clippingPlanesPlug )
	{
		V2f clippingPlanes = clippingPlanesPlug->getValue();
		if( clippingPlanes[1] < clippingPlanes[0] )
		{
			std::swap( clippingPlanes[0], clippingPlanes[1] );
		}
		else if( clippingPlanes[1] == clippingPlanes[0] )
		{
			clippingPlanes[1] += 0.001;
		}
		camera->setClippingPlanes( clippingPlanes );

		if( camera->getProjection() == "perspective" )
		{
			// Adjust aperture to match FOV
			camera->setFocalLengthFromFieldOfView( fieldOfViewPlug->getValue() );
		}
	}

	IECoreScene::CameraPtr camera;
	M44f transform;
	float centerOfInterest;

};

} // namespace

class SceneView::Camera : public Signals::Trackable
{

	public :

		Camera( SceneView *view )
			:	m_view( view ),
				m_framed( false ),
				m_lightToCamera( new LightToCamera ),
				m_distantApertureAttributeQuery( new AttributeQuery ),
				m_clippingPlanesAttributeQuery( new AttributeQuery ),
				m_lookThroughCameraDirty( true ),
				m_lookThroughCamera( nullptr ),
				m_viewportCameraDirty( true ),
				m_overlay( new CameraOverlay )
		{
			// Set up our plugs

			ValuePlugPtr plug = new ValuePlug( "camera", Plug::In, Plug::Default & ~Plug::AcceptsInputs );

			plug->addChild( new StringPlug( "freeCamera", Plug::In, "perspective", Plug::Default & ~Plug::AcceptsInputs ) );

			plug->addChild(
				new Gaffer::FloatPlug(
					"fieldOfView",
					Plug::In,
					54.43f,
					0.01f,
					179.99f,
					Plug::Default & ~Plug::AcceptsInputs
				)
			);
			plug->addChild(
				new Gaffer::V2fPlug(
					"clippingPlanes", Plug::In,
					V2f( 0.1, 100000 ),
					V2f( 0.0001 ),
					V2f( std::numeric_limits<float>::max() ),
					Plug::Default & ~Plug::AcceptsInputs
				)
			);

			plug->addChild( new BoolPlug( "lookThroughEnabled", Plug::In, false, Plug::Default & ~Plug::AcceptsInputs ) );
			plug->addChild( new StringPlug( "lookThroughCamera", Plug::In, "", Plug::Default & ~Plug::AcceptsInputs ) );
			plug->addChild(
				new Gaffer::FloatPlug(
					"lightLookThroughDefaultDistantAperture", Plug::In,
					2.0f,
					0.0f,
					std::numeric_limits<float>::max(),
					Plug::Default & ~Plug::AcceptsInputs
				)
			);

			plug->addChild(
				new Gaffer::V2fPlug(
					"lightLookThroughDefaultClippingPlanes", Plug::In,
					V2f( -100000, 100000 ),
					V2f( std::numeric_limits<float>::lowest() ),
					V2f( std::numeric_limits<float>::max() ),
					Plug::Default & ~Plug::AcceptsInputs
				)
			);

			view->addChild( plug );

			// Set up our nodes.
			// We use a LightToCamera node filtered to all lights to create camera standins so that we can
			// look through lights
			SetFilterPtr lightFilter = new SetFilter;
			lightFilter->setExpressionPlug()->setValue( "__lights" );

			m_distantApertureAttributeQuery->scenePlug()->setInput( view->inPlug<ScenePlug>() );
			FloatPlugPtr defaultFloatPlug = new Gaffer::FloatPlug( "defaultFloatPlug" );
			m_distantApertureAttributeQuery->setup( defaultFloatPlug.get() );
			m_distantApertureAttributeQuery->attributePlug()->setValue( "gl:light:lookThroughAperture" );
			m_distantApertureAttributeQuery->defaultPlug()->setInput( lightLookThroughDefaultDistantAperturePlug() );
			m_clippingPlanesAttributeQuery->scenePlug()->setInput( view->inPlug<ScenePlug>() );
			V2fPlugPtr defaultV2fPlug = new Gaffer::V2fPlug( "defaultV2fPlug" );
			m_clippingPlanesAttributeQuery->setup( defaultV2fPlug.get() );
			m_clippingPlanesAttributeQuery->attributePlug()->setValue( "gl:light:lookThroughClippingPlanes" );
			m_clippingPlanesAttributeQuery->defaultPlug()->setInput( lightLookThroughDefaultClippingPlanesPlug() );

			m_lightToCamera->inPlug()->setInput( view->inPlug<ScenePlug>() );
			m_lightToCamera->filterPlug()->setInput( lightFilter->outPlug() );
			m_lightToCamera->distantAperturePlug()->setInput( m_distantApertureAttributeQuery->valuePlug() );
			m_lightToCamera->clippingPlanesPlug()->setInput( m_clippingPlanesAttributeQuery->valuePlug() );

			m_internalNodes.push_back( lightFilter );

			// Set up our gadgets

			view->viewportGadget()->setChild( "__cameraOverlay", m_overlay );
			m_overlay->setVisible( false );

			// Initialise the free cameras

			m_freeCameras["perspective"] = FreeCamera::createFromViewport( m_view->viewportGadget() );
			m_freeCameras["side"] = FreeCamera::createOrthographic( 0 );
			m_freeCameras["top"] = FreeCamera::createOrthographic( 1 );
			m_freeCameras["front"] = FreeCamera::createOrthographic( 2 );

			for( auto &camera : m_freeCameras )
			{
				camera.second.updateFromPlugs( fieldOfViewPlug(), clippingPlanesPlug() );
			}

			// Connect to the signals we need

			m_lightToCamera->plugDirtiedSignal().connect( boost::bind( &Camera::plugDirtied, this, ::_1 ) );
			m_plugSetConnection = view->plugSetSignal().connect( boost::bind( &Camera::plugSet, this, ::_1 ) );
			view->plugDirtiedSignal().connect( boost::bind( &Camera::plugDirtied, this, ::_1 ) );
			view->viewportGadget()->preRenderSignal().connect( boost::bind( &Camera::preRender, this ) );
			view->viewportGadget()->viewportChangedSignal().connect( boost::bind( &Camera::viewportChanged, this ) );
			m_viewportCameraChangedConnection = view->viewportGadget()->cameraChangedSignal().connect( boost::bind( &Camera::viewportCameraChanged, this ) );

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

		string lookThroughCameraPath() const
		{
			return lookThroughCameraPlug()->getValue();
		}

	private :

		const GafferScene::ScenePlug *scenePlug() const
		{
			return m_lightToCamera->outPlug();
		}

		Gaffer::StringPlug *freeCameraPlug()
		{
			return plug()->getChild<Gaffer::StringPlug>( 0 );
		}

		const Gaffer::StringPlug *freeCameraPlug() const
		{
			return plug()->getChild<Gaffer::StringPlug>( 0 );
		}

		Gaffer::FloatPlug *fieldOfViewPlug()
		{
			return plug()->getChild<Gaffer::FloatPlug>( 1 );
		}

		const Gaffer::FloatPlug *fieldOfViewPlug() const
		{
			return plug()->getChild<Gaffer::FloatPlug>( 1 );
		}

		Gaffer::V2fPlug *clippingPlanesPlug()
		{
			return plug()->getChild<Gaffer::V2fPlug>( 2 );
		}

		const Gaffer::V2fPlug *clippingPlanesPlug() const
		{
			return plug()->getChild<Gaffer::V2fPlug>( 2 );
		}

		const Gaffer::BoolPlug *lookThroughEnabledPlug() const
		{
			return plug()->getChild<BoolPlug>( 3 );
		}

		const Gaffer::StringPlug *lookThroughCameraPlug() const
		{
			return plug()->getChild<StringPlug>( 4 );
		}

		const Gaffer::FloatPlug *lightLookThroughDefaultDistantAperturePlug() const
		{
			return plug()->getChild<FloatPlug>( 5 );
		}

		Gaffer::FloatPlug *lightLookThroughDefaultDistantAperturePlug()
		{
			return plug()->getChild<FloatPlug>( 5 );
		}

		const Gaffer::V2fPlug *lightLookThroughDefaultClippingPlanesPlug() const
		{
			return plug()->getChild<V2fPlug>( 6 );
		}

		Gaffer::V2fPlug *lightLookThroughDefaultClippingPlanesPlug()
		{
			return plug()->getChild<V2fPlug>( 6 );
		}

		SceneGadget *sceneGadget()
		{
			return static_cast<SceneGadget *>( m_view->viewportGadget()->getPrimaryChild() );
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
				plug == clippingPlanesPlug() ||
				plug == fieldOfViewPlug()
			)
			{
				// Camera settings changed. Transfer onto free cameras.
				for( auto &camera : m_freeCameras )
				{
					camera.second.updateFromPlugs( fieldOfViewPlug(), clippingPlanesPlug() );
				}
				// `updateFromPlugs()` applies constraints to clipping planes. Apply them
				// back to the plugs.
				Signals::BlockedConnection plugValueSetBlocker( m_plugSetConnection );
				freeCamera().applyToPlugs( fieldOfViewPlug(), clippingPlanesPlug() );
				// Schedule viewport update.
				m_lookThroughCameraDirty = true;
				m_view->viewportGadget()->renderRequestSignal()( m_view->viewportGadget() );
			}
		}

		void plugDirtied( Gaffer::Plug *plug )
		{
			if( plug != lookThroughEnabledPlug() && plug != freeCameraPlug() && !lookThroughEnabledPlug()->getValue() )
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
				plug == lookThroughCameraPlug() ||
				plug == freeCameraPlug()
			)
			{
				m_lookThroughCameraDirty = m_viewportCameraDirty = true;
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
				FreeCamera &freeCam = freeCamera();
				freeCam = FreeCamera::createFromViewport( m_view->viewportGadget() );

				Signals::BlockedConnection plugValueSetBlocker( m_plugSetConnection );
				freeCam.applyToPlugs( fieldOfViewPlug(), clippingPlanesPlug() );

				// We assume that if the viewport camera is set explicitly before
				// the first frame is drawn, we shouldn't do any automatic framing.
				m_framed = true;
			}
		}

		void preRender()
		{
			updateLookThroughCamera();
			updateViewportCameraAndOverlay();

			if( !m_framed && !lookThroughEnabledPlug()->getValue() )
			{
				m_view->viewportGadget()->frame( m_view->framingBound() );
				m_framed = true;
			}
		}

		FreeCamera &freeCamera()
		{
			const string name = freeCameraPlug()->getValue();
			auto it = m_freeCameras.find( name );
			if( it != m_freeCameras.end() )
			{
				return it->second;
			}

			IECore::msg( IECore::Msg::Warning, "SceneView", fmt::format( "Free camera \"{}\" does not exist", name ) );
			return m_freeCameras.at( "perspective" );
		}

		void updateLookThroughCamera()
		{
			if( !m_lookThroughCameraDirty )
			{
				return;
			}

			m_lookThroughCameraDirty = false;
			m_lookThroughCamera = nullptr;
			if( !lookThroughEnabledPlug()->getValue() )
			{
				Signals::BlockedConnection cameraChangedBlock( m_viewportCameraChangedConnection );
				freeCamera().applyToViewport( m_view->viewportGadget() );
				m_view->viewportGadget()->setCameraEditable( true );
				m_view->deleteObjectFilter()->pathsPlug()->setToDefault();
				sceneGadget()->setBlockingPaths( IECore::PathMatcher() );
				return;
			}

			// We want to look through a specific camera.
			// Retrieve it, along with the scene globals
			// and the camera set.

			Context::Scope scopedContext( m_view->getContext() );

			string cameraPathString = lookThroughCameraPath();
			ConstCompoundObjectPtr globals;
			ConstPathMatcherDataPtr cameraSet;
			M44f cameraTransform;
			string errorMessage;

			m_clippingPlanesAttributeQuery->locationPlug()->setValue( cameraPathString );
			m_distantApertureAttributeQuery->locationPlug()->setValue( cameraPathString );
			try
			{
				globals = scenePlug()->globals();
				cameraSet = m_view->inPlug<ScenePlug>()->set( "__cameras" );

				if( cameraPathString.empty() )
				{
					if( const StringData *cameraData = globals->member<StringData>( "option:render:camera" ) )
					{
						cameraPathString = cameraData->readable();
					}
				}

				if( !cameraPathString.empty() )
				{
					ScenePlug::ScenePath cameraPath;
					ScenePlug::stringToPath( cameraPathString, cameraPath );
					if( !scenePlug()->exists( cameraPath ) )
					{
						throw IECore::Exception( "Camera \"" + cameraPathString + "\" does not exist" );
					}

					IECoreScene::ConstCameraPtr constCamera = runTimeCast<const IECoreScene::Camera>( scenePlug()->object( cameraPath ) );
					if( !constCamera )
					{
						throw IECore::Exception( "Location \"" + cameraPathString + "\" does not have a camera" );
					}
					cameraTransform = scenePlug()->fullTransform( cameraPath );

					IECoreScene::CameraPtr camera = constCamera->copy();
					SceneAlgo::applyCameraGlobals( camera.get(), globals.get(), scenePlug() );
					m_lookThroughCamera = camera;
				}
				else
				{
					CameraPtr defaultCamera = new IECoreScene::Camera;
					SceneAlgo::applyCameraGlobals( defaultCamera.get(), globals.get(), scenePlug() );
					m_lookThroughCamera = defaultCamera;
				}
			}
			catch( const std::exception &e )
			{
				// If an invalid path has been entered for the camera, computation will fail.
				// Record the error to go in the caption, and make a default camera to lock to.
				m_lookThroughCamera = new IECoreScene::Camera();
				cameraSet = new PathMatcherData;
				globals = new CompoundObject;
				errorMessage = e.what();
			}

			m_view->viewportGadget()->setCameraTransform( cameraTransform );

			m_view->viewportGadget()->setCameraEditable( false );
			m_view->viewportGadget()->setTumblingEnabled( true ); // For when CameraTool calls `setCameraEditable( true )`.
			m_view->deleteObjectFilter()->pathsPlug()->setToDefault();

			// When looking through a camera, we delete the camera, since the overlay
			// tells us everything we need to know about the camera. If looking through
			// something else, such as a light, we may want to see the viewport
			// visualisation of what we're looking through.
			const bool isCamera = cameraSet->readable().match( cameraPathString );
			if( isCamera )
			{
				m_view->deleteObjectFilter()->pathsPlug()->setValue(
					new StringVectorData( { cameraPathString } )
				);
			}

			// Make sure that the camera and anything parented below it are always
			// updated before drawing, rather than being updated asynchronously with
			// the rest of the scene. This keeps the visualisations of lights in sync
			// with the position of the look-through camera.

			PathMatcher blockingPaths;
			blockingPaths.addPath( cameraPathString );
			sceneGadget()->setBlockingPaths( blockingPaths );

			// Set up the static parts of the overlay. The parts that change when the
			// viewport changes will be updated in updateViewportCameraAndOverlay().
			if( isCamera && m_lookThroughCamera->hasCropWindow() )
			{
				m_overlay->setCropWindow( m_lookThroughCamera->getCropWindow() );
			}
			else
			{
				m_overlay->setCropWindow( Box2f( V2f( 0 ), V2f( 1 ) ) );
			}
			if( isCamera && m_lookThroughCamera->getOverscan() )
			{
				const float left = m_lookThroughCamera->getOverscanLeft();
				const float top = m_lookThroughCamera->getOverscanTop();
				const float right = m_lookThroughCamera->getOverscanRight();
				const float bottom = m_lookThroughCamera->getOverscanBottom();
				m_overlay->setOverscan( V4f( left, top, right, bottom ) );
			}
			else
			{
				m_overlay->setOverscan( V4f( 0.0f ) );
			}

			if( errorMessage.empty() )
			{
				const V2i resolution = m_lookThroughCamera->getResolution();
				const float pixelAspectRatio = m_lookThroughCamera->getPixelAspectRatio();
				m_overlay->setCaption( fmt::format(
					"{}x{}, {:.3f}, {}",
					resolution.x, resolution.y,
					pixelAspectRatio,
					!cameraPathString.empty() ? cameraPathString : "default"
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
				m_overlay->setApertureGate( Box2f() );
				m_overlay->setVisible( false );
				return;
			}

			// The camera will have a resolution and screen window set from the scene
			// globals. We need to adjust them to fit the viewport appropriately, placing
			// the resolution gate centrally with a border around it. Start by figuring
			// out where we'll draw the resolution gate in raster space.


			const float borderPixels = 40;
			const V2f viewport = m_view->viewportGadget()->getViewport();
			const V2f insetViewport(
				max( viewport.x - borderPixels * 2.0f, min( viewport.x, 50.0f ) ),
				max( viewport.y - borderPixels * 2.0f, min( viewport.y, 50.0f ) )
			);
			const float insetViewportAspectRatio = insetViewport.x / insetViewport.y;

			const V2f resolution = m_lookThroughCamera->getResolution();
			const float pixelAspectRatio = fabsf( m_lookThroughCamera->getPixelAspectRatio() );

			Box2f apertureGate = m_lookThroughCamera->frustum( IECoreScene::Camera::Distort );
			Box2f resolutionGate = m_lookThroughCamera->frustum( m_lookThroughCamera->getFilmFit(),
				resolution.x * pixelAspectRatio / resolution.y
			);

			// We want the aspect ratio of the resolution gate to match the aspect ratio of the resolution
			// When using Distort film fit, they won't match by default, so we apply this squish factor
			// to the resolutionGate, the apertureGate, and the aperture of the viewportCamera.  This keeps
			// everything aligned, with the correct aspect ratio ( though the objects in the view are now
			// distorted )
			float horizSquish = ( resolutionGate.size().x * resolution.y ) / ( resolutionGate.size().y * resolution.x * pixelAspectRatio );

			apertureGate.min.x /= horizSquish;
			apertureGate.max.x /= horizSquish;
			resolutionGate.min.x /= horizSquish;
			resolutionGate.max.x /= horizSquish;

			// Find the screen window box that we want to be visible in the viewport
			Box2f viewportTarget = resolutionGate;
			if( m_lookThroughCamera->getFilmFit() != IECoreScene::Camera::Horizontal )
			{
				// Unless we're doing a horizontal fit that ignores it,
				// enlarge the viewport to see the vertical aperture
				viewportTarget.min.y = min( viewportTarget.min.y, apertureGate.min.y );
				viewportTarget.max.y = max( viewportTarget.max.y, apertureGate.max.y );
			}
			if( m_lookThroughCamera->getFilmFit() != IECoreScene::Camera::Vertical )
			{
				// Unless we're doing a vertical fit that ignores it,
				// enlarge the viewport to see the horizontal aperture
				viewportTarget.min.x = min( viewportTarget.min.x, apertureGate.min.x );
				viewportTarget.max.x = max( viewportTarget.max.x, apertureGate.max.x );
			}

			Box2f insetScreenWindow = IECoreScene::Camera::fitWindow( viewportTarget, IECoreScene::Camera::Fit, insetViewportAspectRatio );
			V2f insetCenter = insetScreenWindow.center();
			V2f insetScale = insetViewport / viewport;

			// Compute a normalized screen window, large enough that the viewportTarget is inside it,
			// taking the inset border into account
			Box2f viewportScreenWindow;
			viewportScreenWindow.min = ( insetScreenWindow.min - insetCenter ) / insetScale + insetCenter;
			viewportScreenWindow.max = ( insetScreenWindow.max - insetCenter ) / insetScale + insetCenter;

			m_overlay->setResolutionGate( Box2f(
					( resolutionGate.min - viewportScreenWindow.min ) / viewportScreenWindow.size() * viewport,
					( resolutionGate.max - viewportScreenWindow.min ) / viewportScreenWindow.size() * viewport
			) );
			m_overlay->setApertureGate( Box2f(
					( apertureGate.min - viewportScreenWindow.min ) / viewportScreenWindow.size() * viewport,
					( apertureGate.max - viewportScreenWindow.min ) / viewportScreenWindow.size() * viewport
			) );
			m_overlay->setVisible( true );

			// Now set up a camera that can see all of the aperture and resolution gates.
			IECoreScene::CameraPtr viewportCamera = new IECoreScene::Camera();
			viewportCamera->setFilmFit( IECoreScene::Camera::Distort );
			viewportCamera->setProjection( m_lookThroughCamera->getProjection() );
			viewportCamera->setFocalLength( 1.0f );
			viewportCamera->setAperture( viewportScreenWindow.size() * V2f( horizSquish, 1.0f ) );
			viewportCamera->setApertureOffset( viewportScreenWindow.center() * V2f( horizSquish, 1.0f ) );
			viewportCamera->setClippingPlanes( m_lookThroughCamera->getClippingPlanes() );
			m_view->viewportGadget()->setCamera( viewportCamera.get() );
			m_view->viewportGadget()->setCameraEditable( false );

			m_viewportCameraDirty = false;
		}

		SceneView *m_view;
		bool m_framed;

		LightToCameraPtr m_lightToCamera;

		AttributeQueryPtr m_distantApertureAttributeQuery;
		AttributeQueryPtr m_clippingPlanesAttributeQuery;

		/// Nodes used in an internal processing network.
		/// Don't need to do anything with them once their set up, but need to hold onto a pointer
		/// so they don't get destroyed
		std::vector< Gaffer::ConstNodePtr > m_internalNodes;

		Signals::ScopedConnection m_plugSetConnection;
		Signals::ScopedConnection m_viewportCameraChangedConnection;
		Signals::ScopedConnection m_contextChangedConnection;

		// Cameras that don't exist in the Gaffer scene, so are
		// always available for use.
		std::unordered_map<std::string, FreeCamera> m_freeCameras;
		// Camera we want to look through - retrieved from scene
		// and dirtied on plug and context changes.
		bool m_lookThroughCameraDirty;
		IECoreScene::ConstCameraPtr m_lookThroughCamera;
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

GAFFER_NODE_DEFINE_TYPE( SceneView );

size_t SceneView::g_firstPlugIndex = 0;
SceneView::ViewDescription<SceneView> SceneView::g_viewDescription( GafferScene::ScenePlug::staticTypeId() );

SceneView::SceneView( ScriptNodePtr scriptNode )
	:	View( defaultName<SceneView>(), scriptNode, new GafferScene::ScenePlug() ),
		m_sceneGadget( new SceneGadget )
{

	// set up a sensible default camera

	IECoreScene::CameraPtr camera = new IECoreScene::Camera();
	camera->setProjection( "perspective" );

	// Some default 35mm lens geometry
	camera->setFocalLength( 35.0f );
	camera->setAperture( V2f( 36.0f, 24.0f ) );

	viewportGadget()->setPlanarMovement( false );
	viewportGadget()->setCamera( camera.get() );

	// NOTE: This offset of 1.0 in Z is kind weird - but it will never show up in practice.
	// We rely on SceneView::Camera to start with m_framed set to false, so that it will
	// reposition itself during preRender()
	M44f matrix;
	matrix.translate( V3f( 0, 0, 1 ) );
	matrix.rotate( IECore::degreesToRadians( V3f( -25, 45, 0 ) ) );
	viewportGadget()->setCameraTransform( matrix );

	// add plugs and signal handling for them

	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new IntPlug( "minimumExpansionDepth", Plug::In, 0, 0, std::numeric_limits<int>::max(), Plug::Default & ~Plug::AcceptsInputs ) );

	plugSetSignal().connect( boost::bind( &SceneView::plugSet, this, ::_1 ) );

	// set up our gadgets

	viewportGadget()->setPrimaryChild( m_sceneGadget );
	viewportGadget()->keyPressSignal().connect( boost::bind( &SceneView::keyPress, this, ::_1, ::_2 ) );

	m_sceneGadget->setContext( getContext() );

	m_renderer.reset( new Renderer( this ) );
	m_selectionMask.reset( new SelectionMask( this ) );
	m_drawingMode.reset( new DrawingMode( this ) );
	m_shadingMode.reset( new ShadingMode( this ) );
	m_camera.reset( new Camera( this ) );
	new Grid( this );
	m_gnomon.reset( new Gnomon( this ) );
	m_fps.reset( new FPS( this ) );

	[[maybe_unused]] auto displayTransform = new DisplayTransform( this );
	assert( displayTransform->parent() == this );

	//////////////////////////////////////////////////////////////////////////
	// add a preprocessor which monkeys with the scene before it is displayed.
	//////////////////////////////////////////////////////////////////////////

	NodePtr preprocessor = new Node();
	ScenePlugPtr preprocessorInput = new ScenePlug( "in" );
	preprocessor->addChild( preprocessorInput );

	// add a node for deleting objects

	DeleteObjectPtr deleteObject = new GafferScene::DeleteObject( "deleteObject" );

	preprocessor->addChild( deleteObject );
	deleteObject->inPlug()->setInput( preprocessorInput );

	PathFilterPtr deleteObjectFilter = new PathFilter( "deleteObjectFilter" );
	preprocessor->addChild( deleteObjectFilter );
	deleteObject->filterPlug()->setInput( deleteObjectFilter->outPlug() );

	// add in any render adaptors that might have been registered

	SceneProcessorPtr adaptors = SceneAlgo::createRenderAdaptors();
	preprocessor->addChild( adaptors );
	adaptors->getChild<StringPlug>( "client" )->setValue( "SceneView" );
	adaptors->inPlug()->setInput( deleteObject->outPlug() );

	// add in the node from the ShadingMode

	preprocessor->addChild( m_shadingMode->preprocessor() );
	m_shadingMode->preprocessor()->inPlug()->setInput( adaptors->outPlug() );

	// add in the node from the DrawingMode

	preprocessor->addChild( m_drawingMode->preprocessor() );
	m_drawingMode->preprocessor()->inPlug()->setInput( m_shadingMode->preprocessor()->outPlug() );

	// add in the node from the Renderer

	preprocessor->addChild( m_renderer->preprocessor() );
	m_renderer->preprocessor()->inPlug()->setInput( m_drawingMode->preprocessor()->outPlug() );
	adaptors->getChild<StringPlug>( "renderer" )->setInput( getChild<Plug>( "renderer" )->getChild<StringPlug>( "name" ) );

	// remove motion blur, because the opengl renderer doesn't support it.

	StandardOptionsPtr standardOptions = new StandardOptions( "disableBlur" );
	standardOptions->optionsPlug()->getChild<NameValuePlug>( "transformBlur" )->enabledPlug()->setValue( true );
	standardOptions->optionsPlug()->getChild<NameValuePlug>( "transformBlur" )->valuePlug<BoolPlug>()->setValue( false );
	standardOptions->optionsPlug()->getChild<NameValuePlug>( "deformationBlur" )->enabledPlug()->setValue( true );
	standardOptions->optionsPlug()->getChild<NameValuePlug>( "deformationBlur" )->valuePlug<BoolPlug>()->setValue( false );

	preprocessor->addChild( standardOptions );
	standardOptions->inPlug()->setInput( m_renderer->preprocessor()->outPlug() );

	// make the output for the preprocessor

	ScenePlugPtr preprocessorOutput = new ScenePlug( "out", Plug::Out );
	preprocessor->addChild( preprocessorOutput );
	preprocessorOutput->setInput( standardOptions->outPlug() );

	setPreprocessor( preprocessor );

	// connect up our scene gadget

	m_sceneGadget->setScene( preprocessedInPlug<ScenePlug>() );

	// Connect to ScriptNodeAlgo for selection and visible set updates.

	ScriptNodeAlgo::selectedPathsChangedSignal( scriptNode.get() ).connect( boost::bind( &SceneView::selectedPathsChanged, this ) );
	ScriptNodeAlgo::visibleSetChangedSignal( scriptNode.get() ).connect( boost::bind( &SceneView::visibleSetChanged, this ) );

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

Gaffer::ValuePlug *SceneView::gnomonPlug()
{
	return m_gnomon->plug();
}

const Gaffer::ValuePlug *SceneView::gnomonPlug() const
{
	return m_gnomon->plug();
}

GafferScene::PathFilter *SceneView::deleteObjectFilter()
{
	return getPreprocessor()->getChild<PathFilter>( "deleteObjectFilter" );
}

const GafferScene::PathFilter *SceneView::deleteObjectFilter() const
{
	return getPreprocessor()->getChild<PathFilter>( "deleteObjectFilter" );
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

void SceneView::registerRenderer( const std::string &name, const RendererSettingsCreator &settingsCreator )
{
	return Renderer::registerRenderer( name, settingsCreator );
}

std::vector<std::string> SceneView::registeredRenderers()
{
	return Renderer::registeredRenderers();
}

Imath::Box3f SceneView::framingBound() const
{
	PathMatcher omitted;
	std::string lookThroughPath = m_camera->lookThroughCameraPath();
	if( lookThroughPath.size() )
	{
		omitted.addPath( lookThroughPath );
	}

	Imath::Box3f b = m_sceneGadget->bound( true, &omitted );
	if( !b.isEmpty() )
	{
		return b;
	}

	b = m_sceneGadget->bound( false, &omitted );
	if( b.isEmpty() )
	{
		SceneGadget *gridGadget = const_cast<SceneGadget *>( getChild<Grid>( "__grid" )->gadget() );
		if( gridGadget->visible() )
		{
			gridGadget->waitForCompletion();
			b.extendBy( gridGadget->bound() );
		}
	}

	return b;
}

void SceneView::selectedPathsChanged()
{
	m_sceneGadget->setSelection( ScriptNodeAlgo::getSelectedPaths( scriptNode() ) );
}

void SceneView::visibleSetChanged()
{
	m_sceneGadget->setVisibleSet( ScriptNodeAlgo::getVisibleSet( scriptNode() ) );
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
	else if( event.key == "Escape" )
	{
		m_sceneGadget->setPaused( true );
	}

	return false;
}

void SceneView::frame( const PathMatcher &filter, const Imath::V3f &direction )
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
	Context::Scope scope( getContext() );
	PathMatcher selection = ScriptNodeAlgo::expandDescendantsInVisibleSet( scriptNode(), m_sceneGadget->getSelection(), preprocessedInPlug<ScenePlug>(), depth - 1 );
	ScriptNodeAlgo::setSelectedPaths( scriptNode(), selection );
}

void SceneView::collapseSelection()
{
	PathMatcher selection = m_sceneGadget->getSelection();
	if( selection.isEmpty() )
	{
		return;
	}

	VisibleSet visibleSet = ScriptNodeAlgo::getVisibleSet( scriptNode() );

	for( PathMatcher::Iterator it = selection.begin(), eIt = selection.end(); it != eIt; ++it )
	{
		if( !visibleSet.expansions.removePath( *it ) )
		{
			if( it->size() <= 1 )
			{
				continue;
			}
			selection.removePath( *it );
			ScenePlug::ScenePath parentPath( it->begin(), it->end() - 1 );
			visibleSet.expansions.removePath( parentPath );
			selection.addPath( parentPath );
		}
	}

	ScriptNodeAlgo::setVisibleSet( scriptNode(), visibleSet );
	ScriptNodeAlgo::setSelectedPaths( scriptNode(), selection );
}

void SceneView::plugSet( Gaffer::Plug *plug )
{
	if( plug == minimumExpansionDepthPlug() )
	{
		m_sceneGadget->setMinimumExpansionDepth( minimumExpansionDepthPlug()->getValue() );
	}
}
