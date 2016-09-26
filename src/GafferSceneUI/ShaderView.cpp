//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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
#include "boost/algorithm/string/predicate.hpp"
#include "boost/container/flat_map.hpp"
#include "boost/asio.hpp"
#include "boost/lexical_cast.hpp"

#include "Gaffer/Context.h"
#include "Gaffer/Box.h"
#include "Gaffer/Reference.h"
#include "Gaffer/StringPlug.h"

#include "GafferImage/Display.h"

#include "GafferScene/Shader.h"
#include "GafferScene/DeleteOutputs.h"
#include "GafferScene/Outputs.h"
#include "GafferScene/ShaderPlug.h"
#include "GafferScene/InteractiveRender.h"
#include "GafferScene/Preview/InteractiveRender.h"

#include "GafferSceneUI/ShaderView.h"

using namespace Gaffer;
using namespace GafferImage;
using namespace GafferScene;
using namespace GafferSceneUI;

//////////////////////////////////////////////////////////////////////////
// Private utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

typedef boost::container::flat_map<IECore::InternedString, ShaderView::RendererCreator> Renderers;
Renderers &renderers()
{
	static Renderers r;
	return r;
}

typedef std::pair<std::string, std::string> PrefixAndName;
typedef boost::container::flat_map<PrefixAndName, ShaderView::SceneCreator> SceneCreators;

SceneCreators &sceneCreators()
{
	static SceneCreators sc;
	return sc;
}

typedef boost::signal<void ( const PrefixAndName & )> SceneRegistrationChangedSignal;
SceneRegistrationChangedSignal &sceneRegistrationChangedSignal()
{
	static SceneRegistrationChangedSignal s;
	return s;
}

int freePort()
{
	typedef boost::asio::ip::tcp::resolver Resolver;
	typedef boost::asio::io_service Service;
	typedef boost::asio::ip::tcp::socket Socket;

	// It is totally unclear why this would be so, but if we use the
	// default constructor we get crashes when using `--std=c++11`.
	// So we use the form that takes a concurrency hint instead. It
	// doesn't seem to matter what value we pass (we can even pass the
	// same value used internally by the default constructor), but we
	// pass 1 because we don't really care about concurrency at all.
	// An alternative workaround appears to be to make `service` static.
	Service service( /* concurrency_hint = */ 1 );
	Resolver resolver( service );
	Resolver::iterator it = resolver.resolve( Resolver::query( "localhost", "" ) );
	Socket socket( service, it->endpoint() );

	return socket.local_endpoint().port();
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// ShaderView
//////////////////////////////////////////////////////////////////////////


IE_CORE_DEFINERUNTIMETYPED( ShaderView );

ShaderView::ViewDescription<ShaderView> ShaderView::g_viewDescription( GafferScene::Shader::staticTypeId(), "out" );

ShaderView::ShaderView( const std::string &name )
	:	ImageView( name ), m_framed( false )
{
	// Create a converter to generate an image
	// from the input shader.

	m_imageConverter = new Box;

	PlugPtr in = new ShaderPlug( "in" );
	m_imageConverter->addChild( in );

	DeleteOutputsPtr deleteOutputs = new DeleteOutputs();
	m_imageConverter->addChild( deleteOutputs );
	deleteOutputs->namesPlug()->setValue( "*" );

	const int port = freePort();

	OutputsPtr outputs = new Outputs();
	m_imageConverter->addChild( outputs );
	outputs->inPlug()->setInput( deleteOutputs->outPlug() );
	IECore::DisplayPtr output = new IECore::Display( "beauty", "ieDisplay", "rgba" );
	output->parameters()["quantize"] = new IECore::IntVectorData( std::vector<int>( 4, 0 ) );
	output->parameters()["driverType"] = new IECore::StringData( "ClientDisplayDriver" );
	output->parameters()["displayHost"] = new IECore::StringData( "localhost" );
	output->parameters()["displayPort"] = new IECore::StringData( boost::lexical_cast<std::string>( port ) );
	output->parameters()["remoteDisplayType"] = new IECore::StringData( "GafferImage::GafferDisplayDriver" );
	outputs->addOutput( "Beauty", output.get() );

	DisplayPtr display = new Display;
	display->portPlug()->setValue( port );
	m_imageConverter->addChild( display );
	m_imageConverter->promotePlug( display->outPlug() );

	insertConverter( m_imageConverter );

	// Add the plugs that form our public interface.

	addChild( new StringPlug( "scene", Plug::In, "Default" ) );

	// Connect to signals we need.

	viewportGadget()->visibilityChangedSignal().connect( boost::bind( &ShaderView::viewportVisibilityChanged, this ) );
	viewportGadget()->preRenderSignal().connect( boost::bind( &ShaderView::preRender, this ) );
	plugSetSignal().connect( boost::bind( &ShaderView::plugSet, this, ::_1 ) );
	plugDirtiedSignal().connect( boost::bind( &ShaderView::plugDirtied, this, ::_1 ) );
	sceneRegistrationChangedSignal().connect( boost::bind( &ShaderView::sceneRegistrationChanged, this, ::_1 ) );

}

ShaderView::~ShaderView()
{
}

Gaffer::StringPlug *ShaderView::scenePlug()
{
	return getChild<StringPlug>( "scene" );
}

const Gaffer::StringPlug *ShaderView::scenePlug() const
{
	return getChild<StringPlug>( "scene" );
}

std::string ShaderView::shaderPrefix() const
{
	IECore::ConstCompoundObjectPtr attributes = inPlug<ShaderPlug>()->attributes();
	const char *shaders[] = { "surface", "displacement", "shader", NULL };
	for( IECore::CompoundObject::ObjectMap::const_iterator it = attributes->members().begin(), eIt = attributes->members().end(); it != eIt; ++it )
	{
		for( const char **shader = shaders; *shader; ++shader )
		{
			if( it->first == *shader )
			{
				return "";
			}
			else if( boost::ends_with( it->first.string(), std::string( ":" ) + *shader ) )
			{
				return it->first.string().substr( 0, it->first.string().find_first_of( ':' ) );
			}
		}
	}

	return "";
}

Gaffer::Node *ShaderView::scene()
{
	updateScene();
	return m_scene.get();
}

const Gaffer::Node *ShaderView::scene() const
{
	const_cast<ShaderView *>( this )->updateScene();
	return m_scene.get();
}

ShaderView::SceneChangedSignal &ShaderView::sceneChangedSignal()
{
	return m_sceneChangedSignal;
}

void ShaderView::setContext( Gaffer::ContextPtr context )
{
	ImageView::setContext( context );
	updateRendererContext();
}

void ShaderView::viewportVisibilityChanged()
{
	updateRendererState();
}

void ShaderView::plugSet( Gaffer::Plug *plug )
{
	if( plug == scenePlug() )
	{
		updateScene();
	}
}

void ShaderView::plugDirtied( Gaffer::Plug *plug )
{
	if( plug == inPlug<Plug>() )
	{
		// The shader has changed, so we may need to update
		// our scene and renderer. But we're not allowed to
		// rewire the graph while dirtiness is being signalled,
		// so must defer the work to the next idle moment.
		if( !m_idleConnection.connected() )
		{
			m_idleConnection = GafferUI::Gadget::idleSignal().connect(
				boost::bind( &ShaderView::idleUpdate, ShaderViewPtr( this ) )
			);
		}
	}
}

void ShaderView::sceneRegistrationChanged( const PrefixAndName &prefixAndName )
{
	if( prefixAndName == m_scenePrefixAndName )
	{
		m_scenePrefixAndName = PrefixAndName();
		m_scenes.erase( prefixAndName );
		updateScene();
	}
}

void ShaderView::idleUpdate()
{
	// We only need to run once.
	m_idleConnection.disconnect();
	// If we need to make a new renderer node,
	// then make one.
	updateRenderer();
	// Then update the scene if we need to.
	updateScene();
	// Finally update the renderer state. We
	// do this last so that when making a new
	// renderer, we do not ask it to render
	// an out-of-date scene prior to it being
	// updated.
	updateRendererState();
}

void ShaderView::updateRenderer()
{
	const std::string shaderPrefix = this->shaderPrefix();
	if( m_renderer && shaderPrefix == m_rendererShaderPrefix )
	{
		return;
	}

	m_renderer = NULL;
	m_rendererShaderPrefix = shaderPrefix;
	if( !inPlug<Plug>()->getInput<Plug>() )
	{
		return;
	}

	const Renderers &r = renderers();
	Renderers::const_iterator it = r.find( shaderPrefix );
	if( it == r.end() )
	{
		return;
	}

	m_renderer = it->second();
	m_renderer->getChild<ScenePlug>( "in" )->setInput(
		m_imageConverter->getChild<SceneNode>( "Outputs" )->outPlug()
	);

	updateRendererContext();
}

void ShaderView::updateRendererContext()
{
	if( InteractiveRender *renderer = IECore::runTimeCast<InteractiveRender>( m_renderer.get() ) )
	{
		renderer->setContext( getContext() );
	}
	else if( Preview::InteractiveRender *renderer = IECore::runTimeCast<Preview::InteractiveRender>( m_renderer.get() ) )
	{
		renderer->setContext( getContext() );
	}
}

void ShaderView::updateRendererState()
{
	if( !m_renderer )
	{
		return;
	}

	m_renderer->getChild<IntPlug>( "state" )->setValue(
		viewportGadget()->visible() ? InteractiveRender::Running : InteractiveRender::Stopped
	);
}

void ShaderView::updateScene()
{
	PrefixAndName prefixAndName( shaderPrefix(), scenePlug()->getValue() );
	if( m_scene && m_scenePrefixAndName == prefixAndName )
	{
		return;
	}

	m_scene = NULL;
	m_scenePrefixAndName = prefixAndName;

	Scenes::const_iterator it = m_scenes.find( prefixAndName );
	if( it != m_scenes.end() )
	{
		// Reuse previously created scene
		m_scene = it->second;
	}
	else
	{
		// Make new scene from scratch
		const SceneCreators &sc = sceneCreators();
		SceneCreators::const_iterator it = sc.find( prefixAndName );
		if( it == sc.end() )
		{
			it = sc.find( PrefixAndName( prefixAndName.first, "Default" ) );
		}

		if( it == sc.end() )
		{
			sceneChangedSignal()( this );
			return;
		}

		m_scene = it->second();
		m_scenes[prefixAndName] = m_scene;
	}

	Plug *shaderPlug = m_scene->getChild<Plug>( "shader" );
	if( !shaderPlug || shaderPlug->direction() != Plug::In )
	{
		throw IECore::Exception( "Scene does not have a \"shader\" input plug" );
	}

	shaderPlug->setInput( m_imageConverter->getChild<Plug>( "in" ) );

	ScenePlug *outPlug = m_scene->getChild<ScenePlug>( "out" );
	if( !outPlug || outPlug->direction() != Plug::Out )
	{
		throw IECore::Exception( "Scene does not have an \"out\" output scene plug" );
	}
	m_imageConverter->getChild<DeleteOutputs>( "DeleteOutputs" )->inPlug()->setInput( outPlug );

	sceneChangedSignal()( this );
}

void ShaderView::preRender()
{
	if( m_framed || !m_scene )
	{
		return;
	}

	// Do our best to give a sensible framing the first time the
	// shader ball image is viewed. Because the render may not have
	// opened the display driver yet, the internal Display node that
	// we are viewing may well be outputting a blank image of default
	// format, which is likely totally different to the shader ball
	// resolution, and the ImageViewer has just framed for that. So
	// we get the resolution of the upcoming render from the render
	// globals and frame ready for that.

	Context::Scope scopedContext( getContext() );
	/// \todo Maybe we should wrap this up into a `SceneAlgo::resolution()`
	/// method that also takes care of overscan, multiplier etc?
	IECore::ConstCompoundObjectPtr globals = m_scene->getChild<ScenePlug>( "out" )->globalsPlug()->getValue();
	Imath::V2i resolution( 640, 480 );
	if( const IECore::V2iData *resolutionData = globals->member<const IECore::V2iData>( "option:render:resolution" ) )
	{
		resolution = resolutionData->readable();
	}

	viewportGadget()->frame( Imath::Box3f( Imath::V3f( 0 ), Imath::V3f( resolution.x, resolution.y, 0.0f ) ) );
	m_framed = true;
}

void ShaderView::registerRenderer( const std::string &shaderPrefix, RendererCreator rendererCreator )
{
	renderers()[shaderPrefix] = rendererCreator;
}

void ShaderView::registerScene( const std::string &shaderPrefix, const std::string &name, const std::string &fileName )
{
	// See ShaderViewBinding.cpp for details.
	throw IECore::Exception( "ShaderView::registerScene currently only implemented in Python" );
}

void ShaderView::registerScene( const std::string &shaderPrefix, const std::string &name, SceneCreator sceneCreator )
{
	const PrefixAndName prefixAndName( shaderPrefix, name );
	sceneCreators()[prefixAndName] = sceneCreator;
	sceneRegistrationChangedSignal()( prefixAndName );
}

void ShaderView::registeredScenes( const std::string &shaderPrefix, std::vector<std::string> &names )
{
	const SceneCreators &sc = sceneCreators();
	for( SceneCreators::const_iterator it = sc.begin(), eIt = sc.end(); it != eIt; ++it )
	{
		if( it->first.first == shaderPrefix )
		{
			names.push_back( it->first.second );
		}
	}
}
