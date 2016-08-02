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

using namespace std;
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

int freePort()
{
	typedef boost::asio::ip::tcp::resolver Resolver;
	typedef boost::asio::io_service Service;
	typedef boost::asio::ip::tcp::socket Socket;

	Service service;
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
	:	ImageView( name )
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
	output->parameters()["quantize"] = new IECore::IntVectorData( vector<int>( 4, 0 ) );
	output->parameters()["driverType"] = new IECore::StringData( "ClientDisplayDriver" );
	output->parameters()["displayHost"] = new IECore::StringData( "localhost" );
	output->parameters()["displayPort"] = new IECore::StringData( boost::lexical_cast<string>( port ) );
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

	plugSetSignal().connect( boost::bind( &ShaderView::plugSet, this, ::_1 ) );
	plugInputChangedSignal().connect( boost::bind( &ShaderView::plugInputChanged, this, ::_1 ) );

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
			else if( boost::ends_with( it->first.string(), string( ":" ) + *shader ) )
			{
				return it->first.string().substr( 0, it->first.string().find_first_of( ':' ) );
			}
		}
	}

	return "";
}

Gaffer::Node *ShaderView::scene()
{
	return m_scene.get();
}

const Gaffer::Node *ShaderView::scene() const
{
	return m_scene.get();
}

ShaderView::SceneChangedSignal &ShaderView::sceneChangedSignal()
{
	return m_sceneChangedSignal;
}

void ShaderView::setContext( Gaffer::ContextPtr context )
{
	ImageView::setContext( context );
	if( InteractiveRender *renderer = IECore::runTimeCast<InteractiveRender>( m_renderer.get() ) )
	{
		renderer->setContext( context );
	}
	else if( Preview::InteractiveRender *renderer = IECore::runTimeCast<Preview::InteractiveRender>( m_renderer.get() ) )
	{
		renderer->setContext( context );
	}
}

void ShaderView::plugSet( Gaffer::Plug *plug )
{
	if( plug == scenePlug() )
	{
		updateScene();
	}
}

void ShaderView::plugInputChanged( Gaffer::Plug *plug )
{
	if( plug == inPlug<Plug>() )
	{
		updateRenderer();
		updateScene();
	}
}

void ShaderView::updateRenderer()
{
	const string shaderPrefix = this->shaderPrefix();
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
	m_renderer->getChild<IntPlug>( "state" )->setValue(
		InteractiveRender::Running
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
	sceneCreators()[PrefixAndName( shaderPrefix, name)] = sceneCreator;
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
