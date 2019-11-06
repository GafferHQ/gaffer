//////////////////////////////////////////////////////////////////////////
//
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

#include "GafferArnold/ArnoldLight.h"

#include "GafferArnold/ArnoldShader.h"
#include "GafferArnold/ParameterHandler.h"

#include "GafferScene/Shader.h"

#include "Gaffer/PlugAlgo.h"
#include "Gaffer/StringPlug.h"

#include "IECoreArnold/UniverseBlock.h"

#include "IECoreScene/ShaderNetworkAlgo.h"

#include "IECore/Exception.h"

#include "boost/format.hpp"

using namespace std;
using namespace Gaffer;
using namespace GafferScene;
using namespace GafferArnold;

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( ArnoldLight );

size_t ArnoldLight::g_firstPlugIndex = 0;

ArnoldLight::ArnoldLight( const std::string &name )
	:	GafferScene::Light( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "__shaderName", Plug::In, "", Plug::Default & ~Plug::Serialisable ) );
}

ArnoldLight::~ArnoldLight()
{
}

void ArnoldLight::loadShader( const std::string &shaderName )
{
	IECoreArnold::UniverseBlock arnoldUniverse( /* writable = */ false );

	const AtNodeEntry *shader = AiNodeEntryLookUp( AtString( shaderName.c_str() ) );
	if( !shader )
	{
		throw IECore::Exception( boost::str( boost::format( "Shader \"%s\" not found" ) % shaderName ) );
	}

	shaderNamePlug()->setValue( shaderName );
	ParameterHandler::setupPlugs( shader, parametersPlug() );
}

void ArnoldLight::hashLight( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	for( ValuePlugIterator it( parametersPlug() ); !it.done(); ++it )
	{
		if( const Shader *shader = IECore::runTimeCast<const Shader>( (*it)->source()->node() ) )
		{
			shader->attributesHash( h );
		}
		else
		{
			(*it)->hash( h );
		}
	}
	shaderNamePlug()->hash( h );
}

IECoreScene::ShaderNetworkPtr ArnoldLight::computeLight( const Gaffer::Context *context ) const
{
	IECoreScene::ShaderNetworkPtr result = new IECoreScene::ShaderNetwork;
	IECoreScene::ShaderPtr lightShader = new IECoreScene::Shader( shaderNamePlug()->getValue(), "ai:light" );
	vector<IECoreScene::ShaderNetwork::Connection> connections;
	for( InputPlugIterator it( parametersPlug() ); !it.done(); ++it )
	{
		if( const Shader *shader = IECore::runTimeCast<const Shader>( (*it)->source()->node() ) )
		{
			/// \todo Take the approach that OSLLight takes, and use an internal
			/// ArnoldShader to do all the shader loading and network generation.
			/// This would avoid manually splicing in networks here, and would
			/// generalise nicely to the other Light subclasses too.
			IECore::ConstCompoundObjectPtr inputAttributes = shader->attributes();
			IECoreScene::ShaderNetwork const *inputNetwork = inputAttributes->member<const IECoreScene::ShaderNetwork>( "ai:surface" );
			if( !inputNetwork ) {
				inputNetwork = inputAttributes->member<const IECoreScene::ShaderNetwork>( "osl:shader" );
			}
			if( !inputNetwork || !inputNetwork->size() )
			{
				continue;
			}

			// Add input network into our result.
			IECoreScene::ShaderNetwork::Parameter sourceParameter = IECoreScene::ShaderNetworkAlgo::addShaders( result.get(), inputNetwork );
			connections.push_back(
				{ sourceParameter, { IECore::InternedString(), (*it)->getName() } }
			);
		}
		else if( ValuePlug *valuePlug = IECore::runTimeCast<ValuePlug>( it->get() ) )
		{
			lightShader->parameters()[valuePlug->getName()] = PlugAlgo::extractDataFromPlug( valuePlug );
		}
	}

	const IECore::InternedString handle = result->addShader( "light", std::move( lightShader ) );
	for( const auto &c : connections )
	{
		result->addConnection( { c.source, { handle, c.destination.name } } );
	}
	result->setOutput( handle );

	return result;
}

Gaffer::StringPlug *ArnoldLight::shaderNamePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *ArnoldLight::shaderNamePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}
