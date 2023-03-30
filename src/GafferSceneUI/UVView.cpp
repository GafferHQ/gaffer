//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2018, John Haddon. All rights reserved.
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

#include "GafferSceneUI/UVView.h"

#include "GafferSceneUI/ContextAlgo.h"
#include "GafferSceneUI/SceneGadget.h"

#include "GafferScene/Isolate.h"
#include "GafferScene/PathFilter.h"
#include "GafferScene/ScenePlug.h"
#include "GafferScene/Transform.h"
#include "GafferScene/UDIMQuery.h"
#include "GafferScene/Wireframe.h"

#include "GafferImage/ColorSpace.h"
#include "GafferImage/ImageReader.h"
#include "GafferImage/Resize.h"

#include "GafferImageUI/ImageView.h"
#include "GafferImageUI/OpenColorIOAlgo.h"

#include "GafferUI/Style.h"
#include "GafferUI/ViewportGadget.h"

#include "Gaffer/StringPlug.h"

#include "IECore/Math.h"

#include "OpenEXR/OpenEXRConfig.h"
#if OPENEXR_VERSION_MAJOR < 3
#include "OpenEXR/ImathFun.h"
#else
#include "Imath/ImathFun.h"
#endif

#include "boost/algorithm/string/replace.hpp"
#include "boost/bind/bind.hpp"
#include "boost/bind/placeholders.hpp"
#include "boost/regex.hpp"

#include <unordered_map>
#include <unordered_set>

using namespace std;
using namespace boost::placeholders;
using namespace Imath;
using namespace IECore;
using namespace IECoreGL;
using namespace Gaffer;
using namespace GafferUI;
using namespace GafferImage;
using namespace GafferImageUI;
using namespace GafferScene;
using namespace GafferSceneUI;

//////////////////////////////////////////////////////////////////////////
// UVView::UVScene
//////////////////////////////////////////////////////////////////////////

// Captures the names of attributes referred to using `<attr:foo>` syntax.
static const boost::regex g_attrRegex( "<attr:([^>]+)>" );

class UVView::UVScene : public SceneProcessor
{

	public :

		GAFFER_NODE_DECLARE_TYPE( GafferSceneUI::UVView::UVScene, UVSceneTypeId, SceneProcessor );

		UVScene( const std::string &name = defaultName<UVScene>() )
			:	SceneProcessor( name )
		{
			storeIndexOfNextChild( g_firstPlugIndex );

			addChild( new StringVectorDataPlug( "visiblePaths", Plug::In, new StringVectorData ) );
			addChild( new StringPlug( "uvSet", Plug::In, "uv" ) );
			addChild( new StringPlug( "textureFileName", Plug::In, "" ) );
			addChild( new CompoundObjectPlug( "textures", Plug::Out, new CompoundObject ) );

			addChild( new StringVectorDataPlug( "__udimQueryPaths", Plug::Out, new StringVectorData ) );
			addChild( new StringPlug( "__udimQueryAttributes", Plug::Out ) );
			addChild( new CompoundObjectPlug( "__udimQuery", Plug::In, new CompoundObject ) );
			addChild( new StringVectorDataPlug( "__isolatePaths", Plug::Out, new StringVectorData ) );

			PathFilterPtr udimQueryFilter = new PathFilter( "__udimQueryFilter" );
			udimQueryFilter->pathsPlug()->setInput( udimQueryPathsPlug() );
			addChild( udimQueryFilter );

			UDIMQueryPtr udimQuery = new UDIMQuery( "__udimQuery" );
			udimQuery->inPlug()->setInput( inPlug() );
			udimQuery->filterPlug()->setInput( udimQueryFilter->outPlug() );
			udimQuery->uvSetPlug()->setInput( uvSetPlug() );
			udimQuery->attributesPlug()->setInput( udimQueryAttributesPlug() );
			udimQueryPlug()->setInput( udimQuery->outPlug() );
			addChild( udimQuery );

			PathFilterPtr isolateFilter = new PathFilter( "__isolateFilter" );
			isolateFilter->pathsPlug()->setInput( isolatePathsPlug() );
			addChild( isolateFilter );

			IsolatePtr isolate = new Isolate( "__isolate" );
			isolate->inPlug()->setInput( inPlug() );
			isolate->filterPlug()->setInput( isolateFilter->outPlug() );
			addChild( isolate );

			PathFilterPtr wireframeFilter = new PathFilter( "__wireframeFilter" );
			wireframeFilter->pathsPlug()->setValue( new IECore::StringVectorData( { "/..." } ) );
			addChild( wireframeFilter );

			WireframePtr wireframe = new Wireframe( "__wireframe" );
			wireframe->inPlug()->setInput( isolate->outPlug() );
			wireframe->filterPlug()->setInput( wireframeFilter->outPlug() );
			wireframe->positionPlug()->setInput( uvSetPlug() );
			addChild( wireframe );

			TransformPtr transform = new Transform( "__transform" );
			transform->inPlug()->setInput( wireframe->outPlug() );
			transform->filterPlug()->setInput( wireframeFilter->outPlug() );
			transform->spacePlug()->setValue( Transform::ResetLocal );
			addChild( transform );

			outPlug()->setInput( transform->outPlug() );
		}

		StringVectorDataPlug *visiblePathsPlug()
		{
			return getChild<StringVectorDataPlug>( g_firstPlugIndex );
		}

		const StringVectorDataPlug *visiblePathsPlug() const
		{
			return getChild<StringVectorDataPlug>( g_firstPlugIndex );
		}

		StringPlug *uvSetPlug()
		{
			return getChild<StringPlug>( g_firstPlugIndex + 1 );
		}

		const StringPlug *uvSetPlug() const
		{
			return getChild<StringPlug>( g_firstPlugIndex + 1 );
		}

		StringPlug *textureFileNamePlug()
		{
			return getChild<StringPlug>( g_firstPlugIndex + 2 );
		}

		const StringPlug *textureFileNamePlug() const
		{
			return getChild<StringPlug>( g_firstPlugIndex + 2 );
		}

		CompoundObjectPlug *texturesPlug()
		{
			return getChild<CompoundObjectPlug>( g_firstPlugIndex + 3 );
		}

		const CompoundObjectPlug *texturesPlug() const
		{
			return getChild<CompoundObjectPlug>( g_firstPlugIndex + 3 );
		}

		void affects( const Plug *input, AffectedPlugsContainer &outputs ) const override
		{
			ComputeNode::affects( input, outputs );

			if( input == visiblePathsPlug() )
			{
				outputs.push_back( udimQueryPathsPlug() );
			}

			if( input == textureFileNamePlug() )
			{
				outputs.push_back( udimQueryAttributesPlug() );
			}

			if( input == udimQueryPlug() )
			{
				outputs.push_back( isolatePathsPlug() );
				outputs.push_back( texturesPlug() );
			}
		}

	protected :

		void hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const override
		{
			SceneProcessor::hash( output, context, h );

			if( output == udimQueryPathsPlug() )
			{
				visiblePathsPlug()->hash( h );
			}
			else if( output == udimQueryAttributesPlug() )
			{
				textureFileNamePlug()->hash( h );
			}
			else if( output == isolatePathsPlug() )
			{
				udimQueryPlug()->hash( h );
			}
			else if( output == texturesPlug() )
			{
				textureFileNamePlug()->hash( h );
				udimQueryPlug()->hash( h );
			}
		}

		void compute( ValuePlug *output, const Context *context ) const override
		{
			if( output == udimQueryPathsPlug() )
			{
				ConstStringVectorDataPtr visiblePathsData = visiblePathsPlug()->getValue();
				const vector<string> &visiblePaths = visiblePathsData->readable();

				StringVectorDataPtr resultData = new StringVectorData;
				vector<string> &result = resultData->writable();
				result.reserve( visiblePaths.size() * 2 );

				for( const auto &path : visiblePaths )
				{
					result.push_back( path );
					result.push_back( path + "/..." );
				}

				static_cast<StringVectorDataPlug *>( output )->setValue( resultData );
			}
			else if( output == udimQueryAttributesPlug() )
			{
				const string fileName = textureFileNamePlug()->getValue();

				string result;
				boost::sregex_iterator it( fileName.begin(), fileName.end(), g_attrRegex );
				while( it != boost::sregex_iterator() )
				{
					if( result.size() )
					{
						result += " ";
					}
					result += it->str( 1 );
					++it;
				}
				static_cast<StringPlug *>( output )->setValue( result );
			}
			else if( output == isolatePathsPlug() )
			{
				unordered_set<string> pathsSet;

				ConstCompoundObjectPtr udimQuery = udimQueryPlug()->getValue();
				for( const auto &udim : udimQuery->members() )
				{
					for( const auto &mesh : static_cast<const CompoundObject *>( udim.second.get() )->members() )
					{
						pathsSet.insert( mesh.first );
					}
				}

				static_cast<StringVectorDataPlug *>( output )->setValue(
					new StringVectorData( vector<string>( pathsSet.begin(), pathsSet.end() ) )
				);
			}
			else if( output == texturesPlug() )
			{
				ConstCompoundObjectPtr udimQuery = udimQueryPlug()->getValue();
				const string textureFileName = textureFileNamePlug()->getValue();

				CompoundObjectPtr result = new CompoundObject;
				for( const auto &udim : udimQuery->members() )
				{
					set<string> udimFileNames;
					const CompoundObject *objects = static_cast<const CompoundObject *>( udim.second.get() );
					for( const auto &object : objects->members() )
					{
						string substitutedFileName = textureFileName;
						const auto *attributes = static_cast<const CompoundObject *>( object.second.get() );
						boost::sregex_iterator it( textureFileName.begin(), textureFileName.end(), g_attrRegex );
						while( it != boost::sregex_iterator() )
						{
							string attribute;
							if( auto *s = attributes->member<StringData>( it->str( 1 ) ) )
							{
								attribute = s->readable();
							}
							boost::replace_all( substitutedFileName, it->str( 0 ), attribute );
							++it;
						}

						boost::replace_all( substitutedFileName, "<UDIM>", udim.first.string() );
						udimFileNames.insert( substitutedFileName );
					}

					result->members()[udim.first] = new StringVectorData(
						vector<string>( udimFileNames.begin(), udimFileNames.end() )
					);
				}
				static_cast<CompoundObjectPlug *>( output )->setValue( result );
			}
			else
			{
				SceneProcessor::compute( output, context );
			}
		}

	private :

		StringVectorDataPlug *udimQueryPathsPlug()
		{
			return getChild<StringVectorDataPlug>( g_firstPlugIndex + 4 );
		}

		const StringVectorDataPlug *udimQueryPathsPlug() const
		{
			return getChild<StringVectorDataPlug>( g_firstPlugIndex + 4 );
		}

		StringPlug *udimQueryAttributesPlug()
		{
			return getChild<StringPlug>( g_firstPlugIndex + 5 );
		}

		const StringPlug *udimQueryAttributesPlug() const
		{
			return getChild<StringPlug>( g_firstPlugIndex + 5 );
		}

		CompoundObjectPlug *udimQueryPlug()
		{
			return getChild<CompoundObjectPlug>( g_firstPlugIndex + 6 );
		}

		const CompoundObjectPlug *udimQueryPlug() const
		{
			return getChild<CompoundObjectPlug>( g_firstPlugIndex + 6 );
		}

		StringVectorDataPlug *isolatePathsPlug()
		{
			return getChild<StringVectorDataPlug>( g_firstPlugIndex + 7 );
		}

		const StringVectorDataPlug *isolatePathsPlug() const
		{
			return getChild<StringVectorDataPlug>( g_firstPlugIndex + 7 );
		}

		static size_t g_firstPlugIndex;

};

GAFFER_NODE_DEFINE_TYPE( UVView::UVScene );
size_t UVView::UVScene::g_firstPlugIndex;

//////////////////////////////////////////////////////////////////////////
// GridGadget
//////////////////////////////////////////////////////////////////////////

namespace
{

class GridGadget : public GafferUI::Gadget
{

	public :

		GridGadget()
		{
		}

	protected :

		void renderLayer( Layer layer, const Style *style, RenderReason reason ) const override
		{
			if( layer != Layer::Main && layer != Layer::MidBack && layer != Layer::Front )
			{
				return;
			}

			const ViewportGadget *viewport = ancestor<ViewportGadget>();
			Box3f bound;
			bound.extendBy( viewport->rasterToGadgetSpace( V2f( 0 ), this ).p0 );
			bound.extendBy( viewport->rasterToGadgetSpace( viewport->getViewport(), this ).p0 );

			const int divisions = layer == Layer::MidBack ? 10 : 1;
			const float divisionDensity = bound.size().x * (float)divisions / (float)viewport->getViewport().x;

			if( layer == Layer::Main || layer == Layer::MidBack )
			{
				// Grid layer

				const float alpha = 1.0f - IECore::smoothstep( 0.1f, 0.4f, divisionDensity );
				if( alpha <= 0.0f )
				{
					return;
				}

				const float lineWidth = (layer == Layer::Main ? 2.0f : 1.0f) * bound.size().x / viewport->getViewport().x;
				const Color4f lineColor( 0.23, 0.23, 0.23, alpha );

				for( float x = floor( bound.min.x ); x <= bound.max.x; x += 1.0f / (float)divisions )
				{
					style->renderLine( IECore::LineSegment3f(
						V3f( x, bound.min.y, bound.min.z ), V3f( x, bound.max.y, bound.min.z ) ),
						lineWidth, &lineColor
					);
				}

				for( float y = floor( bound.min.y ); y <= bound.max.y; y += 1.0f / (float)divisions )
				{
					style->renderLine( IECore::LineSegment3f(
						V3f( bound.min.x, y, bound.min.z ), V3f( bound.max.x, y, bound.min.z ) ),
						lineWidth, &lineColor
					);
				}
			}
			else
			{
				// UDIM label layer

				const float alpha = 1.0f - IECore::smoothstep( 0.005f, 0.01f, divisionDensity );
				if( alpha <= 0.0f )
				{
					return;
				}

				const Color4f textColor( 1, 1, 1, alpha * 0.5 );

				ViewportGadget::RasterScope rasterScope( viewport );
				for( int u = floor( bound.min.x ); u <= bound.max.x; ++u )
				{
					for( int v = floor( bound.min.y ); v <= bound.max.y; ++v )
					{
						string label = std::to_string( u ) + ", " + std::to_string( v );
						if( u >= 0 && u < 10 && v >= 0 )
						{
							label += " (" + std::to_string( 1001 + v * 10 + u ) + ")";
						}
						const V2f rasterPosition = viewport->gadgetToRasterSpace( V3f( u + 0.02, v + 0.02, 0.0f ), this );
						glPushMatrix();
						glTranslate( rasterPosition );
						glScalef( 10, -10, 10 );
						style->renderText( Style::LabelText, label, Style::NormalState, &textColor );
						glPopMatrix();
					}
				}
			}
		}

		Box3f renderBound() const override
		{
			Box3f b;
			b.makeInfinite();
			return b;
		}

		unsigned layerMask() const override
		{
			return Layer::Main | Layer::MidBack | Layer::Front;
		}

};

} // namespace

//////////////////////////////////////////////////////////////////////////
// TextureGadget
//////////////////////////////////////////////////////////////////////////

namespace
{

InternedString g_imageGadgetName( "imageGadget" );

class TextureGadget : public GafferUI::Gadget
{

	public :

		IE_CORE_DECLAREMEMBERPTR( TextureGadget )

		TextureGadget()
			:	m_imageReader( new ImageReader ), m_resize( new Resize )
		{
			m_resize->inPlug()->setInput( m_imageReader->outPlug() );
			m_resize->formatPlug()->setValue( Format( 256, 256 ) );
			m_resize->fitModePlug()->setValue( Resize::Distort );

			setChild( g_imageGadgetName, new ImageGadget );
			imageGadget()->setLabelsVisible( false );
			imageGadget()->setImage( m_resize->outPlug() );
		}

		ImageGadget *imageGadget()
		{
			return getChild<ImageGadget>( g_imageGadgetName );
		}

		void setFileName( const std::string &fileName )
		{
			if( fileName == getFileName() )
			{
				return;
			}

			m_imageReader->fileNamePlug()->setValue( fileName );

			// Transform ImageGadget into 0-1 space.
			const Box3f b = imageGadget()->bound();
			M44f m;
			m.translate( -b.min );
			m.scale( V3f( 1 / b.size().x, 1 / b.size().y, 1 ) );
			imageGadget()->setTransform( m );
		}

		string getFileName() const
		{
			return m_imageReader->fileNamePlug()->getValue();
		}

		std::string getToolTip( const IECore::LineSegment3f &position ) const override
		{
			const std::string t = Gadget::getToolTip( position );
			if( t.size() )
			{
				return t;
			}

			return getFileName();
		}

	private :

		ImageReaderPtr m_imageReader;
		ResizePtr m_resize;

};

IE_CORE_DECLAREPTR( TextureGadget )

using TextureGadgetIterator = FilteredChildIterator<TypePredicate<TextureGadget> >;

} // namespace

//////////////////////////////////////////////////////////////////////////
// UVView implementation
//////////////////////////////////////////////////////////////////////////

size_t UVView::g_firstPlugIndex = 0;
static InternedString g_textureGadgetsName( "textureGadgets" );
static InternedString g_gridGadgetName( "gridGadget" );

GAFFER_NODE_DEFINE_TYPE( UVView )

UVView::UVView( const std::string &name )
	:	View( name, new ScenePlug ), m_textureGadgetsDirty( true ), m_framed( false ), m_displayTransformDirty( true )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new StringPlug( "uvSet", Plug::In, "uv" ) );
	addChild( new StringPlug( "textureFileName" ) );
	addChild( new StringPlug( "displayTransform", Plug::In, "Default" ) );
	addChild( new CompoundObjectPlug( "__textures", Plug::In, new CompoundObject ) );

	addChild( new UVScene( "__uvScene" ) );
	uvScene()->inPlug()->setInput( inPlug() );
	uvScene()->uvSetPlug()->setInput( uvSetPlug() );
	uvScene()->textureFileNamePlug()->setInput( textureFileNamePlug() );
	texturesPlug()->setInput( uvScene()->texturesPlug() );

	viewportGadget()->setChild( g_textureGadgetsName, new Gadget );
	viewportGadget()->setChild( g_gridGadgetName, new GridGadget );

	viewportGadget()->setPrimaryChild( new SceneGadget() );
	sceneGadget()->setScene( uvScene()->outPlug() );
	sceneGadget()->setContext( getContext() );
	CompoundObjectPtr openGLOptions = sceneGadget()->getOpenGLOptions()->copy();
	openGLOptions->members()["gl:curvesPrimitive:useGLLines"] = new BoolData( true );
	openGLOptions->members()["gl:primitive:solid"] = new BoolData( false );
	openGLOptions->members()["gl:primitive:wireframe"] = new BoolData( true );
	openGLOptions->members()["gl:primitive:wireframeColor"] = new Color4fData( Color4f( 0.7, 0.7, 0.7, 1 ) );
	sceneGadget()->setOpenGLOptions( openGLOptions.get() );
	sceneGadget()->setMinimumExpansionDepth( 99999 );
	sceneGadget()->stateChangedSignal().connect( [this]( SceneGadget *g ) { this->gadgetStateChanged( g, g->state() == SceneGadget::Running ); } );

	plugSetSignal().connect( boost::bind( &UVView::plugSet, this, ::_1 ) );
	plugDirtiedSignal().connect( boost::bind( &UVView::plugDirtied, this, ::_1 ) );
	viewportGadget()->preRenderSignal().connect( boost::bind( &UVView::preRender, this ) );
	viewportGadget()->visibilityChangedSignal().connect( boost::bind( &UVView::visibilityChanged, this ) );
}

UVView::~UVView()
{
	// Make sure background task completes before anything
	// it relies on is destroyed.
	m_texturesTask.reset();
}

void UVView::setContext( Gaffer::ContextPtr context )
{
	View::setContext( context );
	sceneGadget()->setContext( context );
	for( TextureGadgetIterator it( textureGadgets() ); !it.done(); ++it )
	{
		(*it)->imageGadget()->setContext( context );
	}
}

void UVView::contextChanged( const IECore::InternedString &name )
{
	if( ContextAlgo::affectsSelectedPaths( name ) )
	{
		const PathMatcher paths = ContextAlgo::getSelectedPaths( getContext() );
		StringVectorDataPtr data = new StringVectorData;
		paths.paths( data->writable() );
		uvScene()->visiblePathsPlug()->setValue( data );
	}
}

Gaffer::StringPlug *UVView::uvSetPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *UVView::uvSetPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *UVView::textureFileNamePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *UVView::textureFileNamePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

Gaffer::StringPlug *UVView::displayTransformPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::StringPlug *UVView::displayTransformPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

Gaffer::CompoundObjectPlug *UVView::texturesPlug()
{
	return getChild<CompoundObjectPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::CompoundObjectPlug *UVView::texturesPlug() const
{
	return getChild<CompoundObjectPlug>( g_firstPlugIndex + 3 );
}

UVView::UVScene *UVView::uvScene()
{
	return getChild<UVScene>( g_firstPlugIndex + 4 );
}

const UVView::UVScene *UVView::uvScene() const
{
	return getChild<UVScene>( g_firstPlugIndex + 4 );
}

void UVView::setPaused( bool paused )
{
	if( paused == sceneGadget()->getPaused() )
	{
		return;
	}

	if( paused )
	{
		m_texturesTask.reset();
	}
	sceneGadget()->setPaused( paused );
	for( TextureGadgetIterator it( textureGadgets() ); !it.done(); ++it )
	{
		(*it)->imageGadget()->setPaused( paused );
	}

	stateChangedSignal()( this );
}

bool UVView::getPaused() const
{
	return sceneGadget()->getPaused();
}

UVView::State UVView::state() const
{
	if( getPaused() )
	{
		return State::Paused;
	}

	return m_runningGadgets.empty() ? State::Complete : State::Running;
}

UVView::UVViewSignal &UVView::stateChangedSignal()
{
	return m_stateChangedSignal;
}

SceneGadget *UVView::sceneGadget()
{
	return static_cast<SceneGadget *>( viewportGadget()->getPrimaryChild() );
}

const SceneGadget *UVView::sceneGadget() const
{
	return static_cast<const SceneGadget *>( viewportGadget()->getPrimaryChild() );
}

GafferUI::Gadget *UVView::textureGadgets()
{
	return viewportGadget()->getChild<Gadget>( g_textureGadgetsName );
}

const GafferUI::Gadget *UVView::textureGadgets() const
{
	return viewportGadget()->getChild<Gadget>( g_textureGadgetsName );
}

void UVView::plugSet( const Gaffer::Plug *plug )
{
	if( plug == displayTransformPlug() )
	{
		m_displayTransformDirty = true;
		viewportGadget()->renderRequestSignal()( viewportGadget() );
	}
}

void UVView::plugDirtied( const Gaffer::Plug *plug )
{
	if( plug == texturesPlug() )
	{
		m_textureGadgetsDirty = true;
	}
}

void UVView::preRender()
{
	if( !m_framed )
	{
		viewportGadget()->frame( Box3f( V3f( -0.05 ), V3f( 1.05 ) ) );
		m_framed = true;
	}

	// We use an OpenGL display transform, so we can't set it up until GL is initialized - once
	// we get the preRender call, we should be good.
	if( m_displayTransformDirty )
	{
		updateDisplayTransform();
		m_displayTransformDirty = false;
	}

	if( getPaused() || !m_textureGadgetsDirty )
	{
		return;
	}

	if( m_texturesTask )
	{
		const auto status = m_texturesTask->status();
		if( status == BackgroundTask::Pending || status == BackgroundTask::Running )
		{
			return;
		}
	}

	Context::Scope scopedContext( getContext() );
	m_texturesTask = ParallelAlgo::callOnBackgroundThread(
		// Subject
		texturesPlug(),
		// OK to capture `this` via raw pointer, because ~UVView waits for
		// the background process to complete.
		[this] {
			ConstCompoundObjectPtr textures = texturesPlug()->getValue();
			if( refCount() )
			{
				UVViewPtr thisRef = this;
				ParallelAlgo::callOnUIThread(
					[thisRef, textures] {
						thisRef->updateTextureGadgets( textures );
					}
				);
			}
		}
	);

	gadgetStateChanged( textureGadgets(), /* running = */ true );
}

void UVView::visibilityChanged()
{
	if( !viewportGadget()->visible() && m_texturesTask )
	{
		m_texturesTask->cancelAndWait();
	}
}

void UVView::updateTextureGadgets( const IECore::ConstCompoundObjectPtr &textures )
{
	m_textureGadgetsDirty = false;

	const string gadgetNamePrefix = "texture";

	for( const auto &texture : textures->members() )
	{
		InternedString gadgetName = gadgetNamePrefix + texture.first.string();
		TextureGadget *textureGadget = textureGadgets()->getChild<TextureGadget>( gadgetName );
		if( !textureGadget )
		{
			TextureGadgetPtr g = new TextureGadget();
			g->imageGadget()->setContext( this->getContext() );
			textureGadgets()->setChild( gadgetName, g );
			textureGadget = g.get();

			const int udim = stoi( texture.first.string() );
			const int u = ( udim - 1001 ) % 10;
			const int v = ( udim - 1001 ) / 10;

			g->setTransform( M44f().translate( V3f( u, v, 0 ) ) );

			g->imageGadget()->stateChangedSignal().connect(
				[this]( ImageGadget *g ) { this->gadgetStateChanged( g, g->state() == ImageGadget::Running ); }
			);
		}

		auto &fileNames = static_cast<const StringVectorData *>( texture.second.get() )->readable();
		textureGadget->setFileName(
			fileNames.size() == 1 ? fileNames[0] : ""
		);

		textureGadget->setVisible( !textureGadget->getFileName().empty() );
	}

	// Hide any texture gadgets we don't need this time round.

	for( Gadget::Iterator it( textureGadgets() ); !it.done(); ++it )
	{
		if( !textures->member<Data>( (*it)->getName().c_str() + gadgetNamePrefix.size() ) )
		{
			(*it)->setVisible( false );
		}
	}

	gadgetStateChanged( textureGadgets(), /* running = */ false );
}

void UVView::updateDisplayTransform()
{
	const string displayTransformName = displayTransformPlug()->getValue();

	const ImageProcessor *displayTransform;

	const auto it = m_displayTransforms.find( displayTransformName );
	if( it == m_displayTransforms.end() )
	{
		ImageProcessorPtr newDisplayTransform = ImageView::createDisplayTransform( displayTransformName );
		m_displayTransforms[displayTransformName] = newDisplayTransform;
		displayTransform = newDisplayTransform.get();
	}
	else
	{
		displayTransform = it->second.get();
	}

	const OpenColorIOTransform *ocioTrans = runTimeCast<const OpenColorIOTransform>( displayTransform );

	const OCIO_NAMESPACE::Processor *ocioProcessor = nullptr;
	if( ocioTrans )
	{
		ocioProcessor = ocioTrans->processor().get();
	}

	viewportGadget()->setPostProcessShader( OpenColorIOAlgo::displayTransformToFramebufferShader( ocioProcessor ) );
}

void UVView::gadgetStateChanged( const Gadget *gadget, bool running )
{
	const State oldState = state();
	if( running )
	{
		m_runningGadgets.insert( gadget );
	}
	else
	{
		m_runningGadgets.erase( gadget );
	}

	if( state() != oldState )
	{
		stateChangedSignal()( this );
	}
}
