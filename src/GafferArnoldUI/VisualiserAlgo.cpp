//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2020, Cinesite VFX Ltd. All rights reserved.
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
//      * Neither the name of Cinesite VFX Ltd. nor the names of
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

#include "GafferArnoldUI/Private/VisualiserAlgo.h"

#include "Gaffer/Private/IECorePreview/LRUCache.h"

#include "IECoreScene/Shader.h"
#include "IECoreScene/ShaderNetworkAlgo.h"

#include "IECore/MessageHandler.h"
#include "IECore/SimpleTypedData.h"

#include "boost/algorithm/string/predicate.hpp"
#include "boost/algorithm/string/join.hpp"
#include "boost/container/flat_set.hpp"

#include "OSL/oslquery.h"


using namespace OSL;
using namespace IECore;
using namespace IECoreScene;

namespace
{

//////////////////////////////////////////////////////////////////////////
// OSL query LRU cache
//////////////////////////////////////////////////////////////////////////

const char *g_oslSearchPaths = getenv( "OSL_SHADER_PATHS" );

typedef std::shared_ptr<OSLQuery> OSLQueryPtr;

OSLQueryPtr oslQueryGetter( const std::string &shaderName, size_t &cost, const IECore::Canceller *canceller )
{
	cost = 1;

	OSLQueryPtr result( new OSLQuery() );
	if( result->open( shaderName, g_oslSearchPaths ? g_oslSearchPaths : "" ) )
	{
		return result;
	}

	return nullptr;
}

typedef IECorePreview::LRUCache<std::string, OSLQueryPtr, IECorePreview::LRUCachePolicy::Parallel> OSLQueryCache;
OSLQueryCache g_oslQueryCache( oslQueryGetter, 128 );

//////////////////////////////////////////////////////////////////////////
// Network conversion helpers
//////////////////////////////////////////////////////////////////////////

// Re-connects any connections from oldName on oldShader to newName on newShader
void remapOutputConnections( const InternedString &shader, const InternedString &oldName, const InternedString &newName, ShaderNetwork *network )
{
	ShaderNetwork::Parameter newSource( shader, newName );

	ShaderNetwork::ConnectionRange inputConnections = network->outputConnections( shader );
	for( ShaderNetwork::ConnectionIterator it = inputConnections.begin(); it != inputConnections.end(); )
	{
		// Copy and increment now so we still have a valid iterator
		// if we remove the connection.
		const ShaderNetwork::Connection connection = *it++;

		if( connection.source.name == oldName )
		{
			ShaderNetwork::Parameter dest( connection.destination.shader, connection.destination.name );
			network->removeConnection( connection );
			network->addConnection( ShaderNetwork::Connection( newSource, dest ) );
		}
	}

	ShaderNetwork::Parameter out = network->getOutput();
	if( out.shader == shader && out.name == oldName )
	{
		network->setOutput( newSource );
	}
}

void remapInputConnections( const InternedString &shader, const InternedString &oldName, const InternedString &newName, ShaderNetwork *network )
{
	ShaderNetwork::Parameter newDestination( shader, newName );

	ShaderNetwork::ConnectionRange outputConnections = network->inputConnections( shader );
	for( ShaderNetwork::ConnectionIterator it = outputConnections.begin(); it != outputConnections.end(); )
	{
		// Copy and increment now so we still have a valid iterator
		// if we remove the connection.
		const ShaderNetwork::Connection connection = *it++;

		if( connection.destination.name == oldName )
		{
			ShaderNetwork::Parameter source( connection.source.shader, connection.source.name );
			network->removeConnection( connection );
			network->addConnection( ShaderNetwork::Connection( source, newDestination ) );
		}
	}
}

// Sets outName in outParams if inName is set in inParams.
// Arnold data types not representable in OSL will be converted accordingly
void copyAndConvertIfSet( const InternedString &inName,  const CompoundDataMap &inParams, const InternedString &outName, CompoundDataMap &outParams )
{
	const auto &it = inParams.find( inName );
	if( it != inParams.end() )
	{
		if( const BoolData *boolData = dynamic_cast<const BoolData *>( it->second.get() ) )
		{
			outParams[ outName ] = new IntData( 1 ? boolData->readable() : 0 );
		}
		else
		{
			outParams[ outName ] = it->second;
		}
	};
}

// Attempts to substitute the Arnold shader with the supplied handle with an
// OSL stand-in shader. Returns true upon success.
//
// If a stand-in is found, any parameters that exist on the stand-in shader
// will be populated by the value of the equivalent parameter on the source shader.
// Input/output connections will be remapped if required.
//
// The network is left un-touched if no stand-in is available.
bool substituteWithOSL( const IECore::InternedString &handle, ShaderNetwork *network )
{
	const Shader *arnoldShader = network->getShader( handle );

	const std::string oslShaderName = "__viewer/__arnold_" + arnoldShader->getName();
	const OSLQueryPtr query = g_oslQueryCache.get( oslShaderName );
	if( !query )
	{
		return false;
	}

	ShaderPtr oslShader = new IECoreScene::Shader();
	oslShader->setType( "osl:shader" );
	oslShader->setName( oslShaderName );

	const IECore::CompoundDataMap &aiParams = arnoldShader->parameters();
	IECore::CompoundDataMap &oslParams = oslShader->parameters();
	for( size_t i = 0; i < query->nparams(); ++i )
	{
		const OSLQuery::Parameter *parameter = query->getparam( i );

		if( parameter->isoutput )
		{
			continue;
		}

		const std::string oslParamName = parameter->name.string();

		// Skip struct members
		if( oslParamName.find( "." ) != std::string::npos )
		{
			continue;
		}

		// We have to avoid collisions with function names and other language
		// keywords, so some stand-in shaders prefix param names with '_'.
		//   eg: normalize -> normalize_
		std::string aiParamName = oslParamName;
		if( aiParamName.back() == '_' )
		{
			aiParamName.pop_back();
			remapInputConnections( handle, aiParamName, oslParamName, network );
		}

		copyAndConvertIfSet( aiParamName, aiParams, oslParamName, oslParams );
	}

	network->setShader( handle, std::move( oslShader ) );
	remapOutputConnections( handle, "", "out", network );

	return true;
}

} // anon namespace

IECoreScene::ShaderNetworkPtr GafferArnoldUI::Private::VisualiserAlgo::conformToOSLNetwork( const IECoreScene::ShaderNetwork::Parameter &output, const IECoreScene::ShaderNetwork *shaderNetwork )
{
	ShaderNetworkPtr oslNetwork = shaderNetwork->copy();

	oslNetwork->setOutput( output );
	ShaderNetworkAlgo::removeUnusedShaders( oslNetwork.get() );

	boost::container::flat_set<std::string> unsupportedShaders;
	InternedString fallbackImageHandle;

	for( const auto &s : oslNetwork->shaders() )
	{
		const Shader *shader = s.second.get();
		if( boost::starts_with( shader->getType(), "ai:" ) )
		{
			if( !substituteWithOSL( s.first, oslNetwork.get() ) )
			{
				unsupportedShaders.insert( shader->getName() );
				continue;
			}

			if( shader->getName() == "image" )
			{
				fallbackImageHandle = s.first;
			}
		}
	}

	if( unsupportedShaders.size() > 0 )
	{
		std::string message = "Unsupported Arnold shaders in network";
		message += " (" + boost::join( unsupportedShaders, ", " ) + ")";

		if( fallbackImageHandle != "" )
		{
			message += ", falling back on " + fallbackImageHandle.string() + ".";
			msg( Msg::Warning, "GafferArnold::VisualiserAlgo", message );

			ShaderNetworkPtr minimalNetwork = new ShaderNetwork();
			minimalNetwork->addShader( "image", oslNetwork->getShader( fallbackImageHandle ) );
			minimalNetwork->setOutput( ShaderNetwork::Parameter( "image", "out" ) );

			oslNetwork = minimalNetwork;
		}
		else
		{
			message += ", unable to convert network to OSL.";
			msg( Msg::Error, "GafferArnold::VisualiserAlgo", message );

			return nullptr;
		}
	}

	return oslNetwork;
}
