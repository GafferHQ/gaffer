//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2014, Esteban Tovagliari. All rights reserved.
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

#include "GafferAppleseed/AppleseedLight.h"

#include "Gaffer/PlugAlgo.h"
#include "Gaffer/StringPlug.h"

#include "IECoreScene/Shader.h"

#include "IECore/Exception.h"

#include "foundation/core/version.h"
#include "renderer/api/edf.h"
#include "renderer/api/environmentedf.h"
#include "renderer/api/light.h"

#include "boost/format.hpp"

using namespace Gaffer;
using namespace GafferAppleseed;

namespace asf = foundation;
namespace asr = renderer;

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( AppleseedLight );

size_t AppleseedLight::g_firstPlugIndex = 0;

AppleseedLight::AppleseedLight( const std::string &name )
	:	GafferScene::Light( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "__model", Plug::In, "", Plug::Default & ~Plug::Serialisable ) );
}

AppleseedLight::~AppleseedLight()
{
}

void AppleseedLight::loadShader( const std::string &shaderName )
{
	asf::DictionaryArray metadata;

	// first, try environment lights.
	if( asr::EnvironmentEDFFactoryRegistrar().lookup( shaderName.c_str() ) )
	{
		asr::EnvironmentEDFFactoryRegistrar registrar;
		const asr::IEnvironmentEDFFactory *factory = registrar.lookup( shaderName.c_str() );
		metadata = factory->get_input_metadata();
	}
	// next, singular lights
	else if( asr::LightFactoryRegistrar().lookup( shaderName.c_str() ) )
	{
		asr::LightFactoryRegistrar registrar;
		const asr::ILightFactory *factory = registrar.lookup( shaderName.c_str() );
		metadata = factory->get_input_metadata();
	}
	// finally, area lights
	else if( asr::EDFFactoryRegistrar().lookup( shaderName.c_str() ) )
	{
		asr::EDFFactoryRegistrar registrar;
		const asr::IEDFFactory *factory = registrar.lookup( shaderName.c_str() );
		metadata = factory->get_input_metadata();
	}
	else // unknown model
	{
		throw IECore::Exception( boost::str( boost::format( "Light or Environment model \"%s\" not found" ) % shaderName ) );
	}

	setupPlugs( shaderName, metadata );
	modelPlug()->setValue( shaderName );
}

void AppleseedLight::hashLight( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	for( ValuePlugIterator it( parametersPlug() ); !it.done(); ++it )
	{
		(*it)->hash( h );
	}
	modelPlug()->hash( h );
}

IECoreScene::ConstShaderNetworkPtr AppleseedLight::computeLight( const Gaffer::Context *context ) const
{
	IECoreScene::ShaderPtr shader = new IECoreScene::Shader( modelPlug()->getValue(), "as:light" );
	for( InputValuePlugIterator it( parametersPlug() ); !it.done(); ++it )
	{
		shader->parameters()[(*it)->getName()] = PlugAlgo::extractDataFromPlug( it->get() );
	}

	IECoreScene::ShaderNetworkPtr result = new IECoreScene::ShaderNetwork();
	result->addShader( "light", std::move( shader ) );
	result->setOutput( { "light" } );
	return result;
}

Gaffer::StringPlug *AppleseedLight::modelPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *AppleseedLight::modelPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

namespace
{

float get_min_max_value( const asf::Dictionary &inputMetadata, const std::string &key )
{
#if APPLESEED_VERSION >= 10800
	const asf::Dictionary& m = inputMetadata.dictionary( key.c_str() );
	return m.get<float>( "value" );
#else
	return inputMetadata.get<float>( key + "_value" );
#endif
}

}

void AppleseedLight::setupPlugs( const std::string &shaderName, const asf::DictionaryArray &metadata )
{
	bool needsRadianceTexture = shaderName.find( "map" ) != std::string::npos;

	for( size_t i = 0, e = metadata.size(); i < e; ++i )
	{
		const asf::Dictionary &inputMetadata = metadata[i];
		std::string inputName = inputMetadata.get( "name" );
		std::string inputType = inputMetadata.get( "type" );

		Gaffer::Plug *plug = nullptr;

		// some environment lights need their radiance color input
		// replaced by a texture input: latlong map and mirrorball map.
		if( needsRadianceTexture && inputName == "radiance" )
		{
			plug = new Gaffer::StringPlug( "radiance_map", Gaffer::Plug::In );
		}
		else
		{
			if( inputType == "numeric" )
			{
				float defaultValue = inputMetadata.get<float>( "default" );
				float minValue = get_min_max_value( inputMetadata, "min" );
				float maxValue = get_min_max_value( inputMetadata, "max" );
				plug = new Gaffer::FloatPlug( inputName, Gaffer::Plug::In, defaultValue, minValue, maxValue );
			}
			else if( inputType == "colormap" )
			{
				// override the plug type for the exposure param (usually it's a color in appleseed).
				if ( inputName == "exposure" )
				{
					plug = new Gaffer::FloatPlug( inputName, Gaffer::Plug::In, 0.0f );
				}
				// multiplier inputs make more sense in Gaffer as float plugs.
				else if( inputName.find( "multiplier" ) != std::string::npos )
				{
					plug = new Gaffer::FloatPlug( inputName, Gaffer::Plug::In, 1.0f, 0.0f );
				}
				else
				{
					plug = new Gaffer::Color3fPlug( inputName, Gaffer::Plug::In, Imath::Color3f( 1.0f ) );
				}
			}
			else if( inputType == "boolean" )
			{
				bool defaultValue = strcmp( inputMetadata.get( "default" ), "true" ) == 0;
				plug = new Gaffer::BoolPlug( inputName, Gaffer::Plug::In, defaultValue );
			}
			// text are non-texturable float inputs.
			else if( inputType == "text" )
			{
				float defaultValue = inputMetadata.get<float>( "default" );
				plug = new Gaffer::FloatPlug( inputName, Gaffer::Plug::In, defaultValue );
			}
		}

		if( plug )
		{
			parametersPlug()->addChild( plug );
		}
	}
}
