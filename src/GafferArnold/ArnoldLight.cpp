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

#include "boost/format.hpp"

#include "IECore/Exception.h"

#include "IECoreArnold/UniverseBlock.h"

#include "Gaffer/CompoundDataPlug.h"
#include "Gaffer/StringPlug.h"

#include "GafferScene/Shader.h"

#include "GafferArnold/ArnoldLight.h"
#include "GafferArnold/ArnoldShader.h"
#include "GafferArnold/ParameterHandler.h"

using namespace Gaffer;
using namespace GafferScene;
using namespace GafferArnold;

IE_CORE_DEFINERUNTIMETYPED( ArnoldLight );

size_t ArnoldLight::g_firstPlugIndex = 0;

ArnoldLight::ArnoldLight( const std::string &name )
	:	GafferScene::Light( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "__shaderName" ) );
}

ArnoldLight::~ArnoldLight()
{
}

void ArnoldLight::loadShader( const std::string &shaderName )
{
	IECoreArnold::UniverseBlock arnoldUniverse( /* writable = */ false );

	const AtNodeEntry *shader = AiNodeEntryLookUp( shaderName.c_str() );
	if( !shader )
	{
		throw IECore::Exception( boost::str( boost::format( "Shader \"%s\" not found" ) % shaderName ) );
	}

	ParameterHandler::setupPlugs( shader, parametersPlug() );

	shaderNamePlug()->setValue( shaderName );
}

void ArnoldLight::hashLight( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	for( ValuePlugIterator it( parametersPlug() ); !it.done(); ++it )
	{
		if( const Shader *shader = (*it)->source<Plug>()->ancestor<Shader>() )
		{
			shader->stateHash( h );
		}
		else
		{
			(*it)->hash( h );
		}
	}
	shaderNamePlug()->hash( h );
}

IECore::ObjectVectorPtr ArnoldLight::computeLight( const Gaffer::Context *context ) const
{
	IECore::ObjectVectorPtr result = new IECore::ObjectVector;
	IECore::ShaderPtr lightShader = new IECore::Shader( shaderNamePlug()->getValue(), "ai:light" );
	for( InputValuePlugIterator it( parametersPlug() ); !it.done(); ++it )
	{
		if( const Shader *shader = (*it)->source<Plug>()->ancestor<Shader>() )
		{
			/// \todo We should generalise Shader::NetworkBuilder so we can
			/// use it directly to do the whole of the light generation, instead
			/// of dealing with input networks manually one by one here.
			IECore::ConstObjectVectorPtr inputNetwork = shader->state();
			if( inputNetwork->members().empty() )
			{
				continue;
			}

			// Add input network into our result.
			result->members().insert( result->members().end(), inputNetwork->members().begin(), inputNetwork->members().end() );
			// Update endpoint of network with a handle we can refer to it with.
			result->members().back() = result->members().back()->copy();
			IECore::Shader *endpoint = static_cast<IECore::Shader *>( result->members().back().get() );
			endpoint->parameters()["__handle"] = new IECore::StringData( (*it)->getName() );
			// Add a parameter value linking to the input network.
			lightShader->parameters()[(*it)->getName()] = new IECore::StringData( "link:" + (*it)->getName().string() );
		}
		else
		{
			lightShader->parameters()[(*it)->getName()] = CompoundDataPlug::extractDataFromPlug( it->get() );
		}
	}

	result->members().push_back( lightShader );
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
