//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2018, Alex Fuller. All rights reserved.
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

#include "GafferCycles/CyclesLight.h"

#include "GafferCycles/CyclesShader.h"
#include "GafferCycles/SocketHandler.h"

#include "GafferScene/Shader.h"

#include "Gaffer/PlugAlgo.h"
#include "Gaffer/StringPlug.h"

#include "IECoreScene/ShaderNetworkAlgo.h"

#include "IECore/Exception.h"

#include "boost/format.hpp"

// Cycles
#include "render/nodes.h"

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;
using namespace GafferCycles;

IE_CORE_DEFINERUNTIMETYPED( CyclesLight );

size_t CyclesLight::g_firstPlugIndex = 0;

CyclesLight::CyclesLight( const std::string &name )
	:	GafferScene::Light( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "__shaderName", Plug::In, "", Plug::Default & ~Plug::Serialisable ) );
}

CyclesLight::~CyclesLight()
{
}

void CyclesLight::loadShader( const std::string &shaderName )
{
	// First populate all the Gaffer plugs for lights
	const ccl::NodeType *lightNodeType = ccl::NodeType::find( ccl::ustring( "light" ) );

	if( lightNodeType )
	{
		SocketHandler::setupLightPlugs( shaderName, lightNodeType, parametersPlug() );
		shaderNamePlug()->setValue( shaderName );
	}
}

void CyclesLight::hashLight( const Gaffer::Context *context, IECore::MurmurHash &h ) const
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

#ifdef GAFFER_MAJOR_VERSION > 55
IECoreScene::ConstShaderNetworkPtr CyclesLight::computeLight( const Gaffer::Context *context ) const
#else
IECoreScene::ShaderNetworkPtr CyclesLight::computeLight( const Gaffer::Context *context ) const
#endif
{
	IECoreScene::ShaderNetworkPtr result = new IECoreScene::ShaderNetwork;
	// Light shader
	IECoreScene::ShaderPtr lightShader = new IECoreScene::Shader( shaderNamePlug()->getValue(), "ccl:light" );

	auto shaderName = shaderNamePlug()->getValue();
	if( shaderName == "spot_light" )
	{
		lightShader->parameters()["type"] = new IntData( (int)ccl::LIGHT_SPOT );
	}
	else if( ( shaderName == "quad_light" )
	      || ( shaderName == "disk_light" )
	      || ( shaderName == "portal" ) )	
	{
		lightShader->parameters()["type"] = new IntData( (int)ccl::LIGHT_AREA );
	}
	else if( shaderName == "background_light" )
	{
		lightShader->parameters()["type"] = new IntData( (int)ccl::LIGHT_BACKGROUND );
	}
	else if( shaderName == "distant_light" )
	{
		lightShader->parameters()["type"] = new IntData( (int)ccl::LIGHT_DISTANT );
	}
	else
	{
		lightShader->parameters()["type"] = new IntData( (int)ccl::LIGHT_POINT );
	}

	if( shaderName == "portal" )
	{
		lightShader->parameters()["is_portal"] = new BoolData( true );
	}
	else if( shaderName == "quad_light" )
	{
		lightShader->parameters()["size"] = new FloatData( 2.0f );
	}

	// Emit shader (color/strength)
	IECoreScene::ShaderPtr emitShader = new IECoreScene::Shader( "emission", "ccl:surface" );
	emitShader->parameters()["color"] = new Color3fData( Imath::Color3f( 1.0f ) );
	emitShader->parameters()["strength"] = new FloatData( 1.0f );
	// Bg shader
	IECoreScene::ShaderPtr bgShader = new IECoreScene::Shader( "background_shader", "ccl:surface" );
	bgShader->parameters()["color"] = new Color3fData( Imath::Color3f( 1.0f ) );
	bgShader->parameters()["strength"] = new FloatData( 1.0f );
	// Environment texture
	IECoreScene::ShaderPtr envShader = new IECoreScene::Shader( "environment_texture", "ccl:surface" );
	// Blender is Z-up, so we need to switcheroo
	envShader->parameters()["tex_mapping__y_mapping"] = new IntData( 3 ); //Z
	envShader->parameters()["tex_mapping__z_mapping"] = new IntData( 2 ); //Y
	envShader->parameters()["tex_mapping__scale"] = new V3fData( Imath::V3f( -1.0f, 1.0f, 1.0f ) );
	// Image texture
	IECoreScene::ShaderPtr texShader = new IECoreScene::Shader( "image_texture", "ccl:surface" );
	IECoreScene::ShaderPtr geoShader = new IECoreScene::Shader( "geometry", "ccl:surface" );
	// Mult
	IECoreScene::ShaderPtr tintShader = new IECoreScene::Shader( "vector_math", "ccl:surface" );
	tintShader->parameters()["type"] = new IntData( 2 ); //Multiply
	tintShader->parameters()["vector2"] = new V3fData( Imath::V3f( 1.0f, 1.0f, 1.0f ) );
	// If we want to connect a texture to color
	IECoreScene::ShaderNetwork::Connection colorEmitConnection;
	// Parameters we need to modify depending on other parameters found.
	float exposure = 0.0f;
	float intensity = 1.0f;
	bool squareSamples = true;
	float samples = 1.0f;
	bool textureInput = false;
	float coneAngle = 30.0f;
	float penumbraAngle = 0.0f;
	Imath::Color3f color = Imath::Color3f( 1.0f );
	for( InputPlugIterator it( parametersPlug() ); !it.done(); ++it )
	{
		if( const Shader *shader = IECore::runTimeCast<const Shader>( (*it)->source()->node() ) )
		{
			// We only allow shaders to connect to color
			auto parameterName = (*it)->getName();
			if( parameterName != "color" )
				continue;

			IECore::ConstCompoundObjectPtr inputAttributes = shader->attributes();
			const IECoreScene::ShaderNetwork *inputNetwork = inputAttributes->member<const IECoreScene::ShaderNetwork>( "ccl:surface" );
			if( !inputNetwork || !inputNetwork->size() )
			{
				continue;
			}

			// Add input network into our emission color
			IECoreScene::ShaderNetwork::Parameter sourceParameter = IECoreScene::ShaderNetworkAlgo::addShaders( result.get(), inputNetwork );
			colorEmitConnection = { sourceParameter, { IECore::InternedString(), parameterName } };
		}
		else if( ValuePlug *valuePlug = IECore::runTimeCast<ValuePlug>( it->get() ) )
		{
			auto parameterName = valuePlug->getName();

			if( parameterName == "exposure" )
			{
				exposure = static_cast<const FloatPlug *>( valuePlug )->getValue();
				// For the UI
				lightShader->parameters()[parameterName] = PlugAlgo::extractDataFromPlug( valuePlug );
			}
			else if( parameterName == "intensity" )
			{
				intensity = static_cast<const FloatPlug *>( valuePlug )->getValue();
				// For the UI
				lightShader->parameters()[parameterName] = PlugAlgo::extractDataFromPlug( valuePlug );
			}
			else if( parameterName == "squareSamples")
			{
				squareSamples = true;
			}
			else if( parameterName == "samples" )
			{
				samples = static_cast<const IntPlug *>( valuePlug )->getValue();
			}
			else if( parameterName == "color" )
			{
				color = static_cast<const Color3fPlug *>( valuePlug )->getValue();
				// For the UI
				lightShader->parameters()[parameterName] = PlugAlgo::extractDataFromPlug( valuePlug );
				tintShader->parameters()["vector2"] = PlugAlgo::extractDataFromPlug( valuePlug );
			}
			else if( parameterName == "image" )
			{
				std::string image = static_cast<const StringPlug *>( valuePlug )->getValue();
				if( image == "" )
				{
					continue;
				}
				textureInput = true;
				texShader->parameters()["filename"] = PlugAlgo::extractDataFromPlug( valuePlug );
				envShader->parameters()["filename"] = PlugAlgo::extractDataFromPlug( valuePlug );
				// For the UI
				lightShader->parameters()[parameterName] = PlugAlgo::extractDataFromPlug( valuePlug );
			}
			else if( parameterName == "coneAngle" )
			{
				coneAngle = static_cast<const FloatPlug *>( valuePlug )->getValue();
				// For the UI
				lightShader->parameters()[parameterName] = PlugAlgo::extractDataFromPlug( valuePlug );
			}
			else if( parameterName == "penumbraAngle" )
			{
				penumbraAngle = static_cast<const FloatPlug *>( valuePlug )->getValue();
				// For the UI
				lightShader->parameters()[parameterName] = PlugAlgo::extractDataFromPlug( valuePlug );
			}
			else if( parameterName == "lightgroups" )
			{
				// LightGroups are stored in a 32-bit bitmask (32 lightGroups max)
				int lightGroup = static_cast<const IntPlug *>( valuePlug )->getValue();
				if( ( lightGroup > 0 ) && ( lightGroup <= 32 ) )
					lightShader->parameters()[parameterName] = new IntData( 1 << ( lightGroup - 1 ) );
				else
					lightShader->parameters()[parameterName] = new IntData( 0 );
				
			}
			else
			{
				lightShader->parameters()[parameterName] = PlugAlgo::extractDataFromPlug( valuePlug );
			}
		}
	}

	if( shaderNamePlug()->getValue() == "spot_light" )
	{
		float sumAngle = coneAngle + penumbraAngle;
		float spotAngle = 2 * M_PI * ( sumAngle / 360.0f );
        lightShader->parameters()["spot_angle"] = new FloatData( spotAngle );
		lightShader->parameters()["spot_smooth"] = new FloatData( Imath::clamp( penumbraAngle / sumAngle, 0.0f, 1.0f ) );
	}

	lightShader->parameters()["samples"] = new IntData( squareSamples ? samples * samples : samples );
	lightShader->parameters()["strength"] = new Color3fData( color * ( intensity * pow( 2.0f, exposure ) ) );
	tintShader->parameters()["strength"] = new FloatData( intensity * pow( 2.0f, exposure ) );
	const IECore::InternedString handle = result->addShader( "light", std::move( lightShader ) );
	const IECore::InternedString emitHandle = result->addShader( "emission", std::move( emitShader ) );

	if( colorEmitConnection.source )
	{
		result->addConnection( { colorEmitConnection.source, { emitHandle, "color" } } );
	}
	else if( textureInput )
	{
		if( shaderNamePlug()->getValue() == "background_light" )
		{
			const IECore::InternedString envHandle = result->addShader( "environment_texture", std::move( envShader ) );
			const IECore::InternedString tintHandle = result->addShader( "vector_math", std::move( tintShader ) );
			const IECore::InternedString bgHandle = result->addShader( "background_shader", std::move( bgShader ) );
			result->addConnection( { { envHandle, "color" }, { tintHandle, "vector1" } } );
			result->addConnection( { { tintHandle, "vector" }, { bgHandle, "color" } } );
			result->addConnection( { { bgHandle, "background" }, { handle, "shader" } } );
		}
		else
		{
			// https://developer.blender.org/rB1272ee455e7aeed3f6acb0b8a8366af5ad6aec99
			const IECore::InternedString geoHandle = result->addShader( "geometry", std::move( geoShader ) );
			const IECore::InternedString texHandle = result->addShader( "image_texture", std::move( texShader ) );
			result->addConnection( { { geoHandle, "parametric" }, { texHandle, "vector" } } );
			result->addConnection( { { texHandle, "color" }, { emitHandle, "color" } } );

			result->addConnection( { { emitHandle, "emission" }, { handle, "shader" } } );
		}
	}
	else
	{
		result->addConnection( { { emitHandle, "emission" }, { handle, "shader" } } );
	}

	result->setOutput( handle );

	return result;
}

Gaffer::StringPlug *CyclesLight::shaderNamePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *CyclesLight::shaderNamePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}
