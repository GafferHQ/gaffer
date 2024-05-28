//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2024, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/ShaderTweakProxy.h"

#include "Gaffer/StringPlug.h"
#include "Gaffer/PlugAlgo.h"

#include <boost/algorithm/string/join.hpp>

using namespace Gaffer;
using namespace GafferScene;

namespace
{

const std::string g_shaderTweakProxyIdentifier = "__SHADER_TWEAK_PROXY";

} // namespace


GAFFER_NODE_DEFINE_TYPE( ShaderTweakProxy );

size_t ShaderTweakProxy::g_firstPlugIndex;

ShaderTweakProxy::ShaderTweakProxy( const std::string &name )
	:	Shader( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new Plug( "out", Plug::Out ) );
	parametersPlug()->addChild( new StringPlug( "targetShader", Plug::Direction::In, "" ) );
}

ShaderTweakProxy::~ShaderTweakProxy()
{
}

ShaderTweakProxy::ShaderLoaderCreatorMap &ShaderTweakProxy::shaderLoaderCreators()
{
	// Deliberately "leaking" list, as it may contain Python functors which
	// cannot be destroyed during program exit (because Python will have been
	// shut down first).
	static auto g_creators = new ShaderLoaderCreatorMap;
	return *g_creators;
}

void ShaderTweakProxy::typePrefixAndSourceShaderName( std::string &typePrefix, std::string &sourceShaderName ) const
{
	std::string shaderName = namePlug()->getValue();
	if( shaderName == "autoProxy" )
	{
		typePrefix = "autoProxy";
		sourceShaderName = "";
		return;
	}

	size_t sep = shaderName.find(":");
	if( sep == std::string::npos )
	{
		throw IECore::Exception( fmt::format(
			"Malformed ShaderTweakProxy shader name \"{}\". Must include type prefix.", shaderName
		) );
	}

	typePrefix = shaderName.substr(0, sep );
	sourceShaderName = shaderName.substr( sep + 1 );
}


void ShaderTweakProxy::loadShader( const std::string &shaderName, bool keepExistingValues )
{
	typePlug()->setValue( g_shaderTweakProxyIdentifier );
	namePlug()->setValue( shaderName );
	if( shaderName == "autoProxy" )
	{
		// Auto-proxies use dynamic plugs to represent their outputs instead of serializing a specific
		// shader type.
		return;
	}

	// If we're proxying a specific node type, we need to find out what the outputs of that node type are
	outPlug()->clearChildren();

	std::string shaderTypePrefix, sourceShaderName;
	typePrefixAndSourceShaderName( shaderTypePrefix, sourceShaderName );

	ShaderPtr loaderNode;

	// Find the correct node type to load this shader with, and create a temporary loader node
	const ShaderLoaderCreatorMap& creatorMap = shaderLoaderCreators();
	auto match = creatorMap.find( shaderTypePrefix );
	if( match != creatorMap.end() )
	{
		loaderNode = match->second();
	}
	else
	{
		std::vector<std::string> possibilityList;
		for( const auto &i : creatorMap )
		{
			possibilityList.push_back( "\"" + i.first + "\"" );
		}
		std::string possibilities = boost::algorithm::join( possibilityList, ", " );
		throw IECore::Exception( fmt::format( "No ShaderTweakProxy shader loader registered for type prefix \"{}\", options are {}", shaderTypePrefix, possibilities ) );
	}

	loaderNode->loadShader( sourceShaderName );

	if( loaderNode->outPlug()->isInstanceOf( Gaffer::ValuePlug::staticTypeId() ) )
	{
		outPlug()->addChild( loaderNode->outPlug()->createCounterpart( "out", Plug::Direction::Out ) );
	}
	else
	{
		// Not a value plug, which means it should have children
		for( const auto &untypedChild : loaderNode->outPlug()->children() )
		{
			Plug *child = IECore::runTimeCast< Plug >( untypedChild.get() );
			outPlug()->addChild( child->createCounterpart( child->getName(), Plug::Direction::Out ) );
		}
	}
}

void ShaderTweakProxy::setupAutoProxy( const Plug* referencePlug )
{
	loadShader( "autoProxy" );
	PlugPtr newPlug = referencePlug->createCounterpart( "auto", Plug::Direction::Out );
	newPlug->setFlags( Plug::Flags::Dynamic, true );
	outPlug()->addChild( newPlug );
}

bool ShaderTweakProxy::isProxy( const IECoreScene::Shader *shader )
{
	return shader->getType() == g_shaderTweakProxyIdentifier;
}

void ShaderTweakProxy::registerShaderLoader( const std::string &typePrefix, ShaderLoaderCreator creator )
{
	shaderLoaderCreators()[typePrefix] = creator;
}
