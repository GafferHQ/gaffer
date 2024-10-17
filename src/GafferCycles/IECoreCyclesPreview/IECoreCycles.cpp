//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2020, Alex Fuller. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//     * Redistributions of source code must retain the above copyright
//       notice, this list of conditions and the following disclaimer.
//
//     * Redistributions in binary form must reproduce the above copyright
//       notice, this list of conditions and the following disclaimer in the
//       documentation and/or other materials provided with the distribution.
//
//     * Neither the name of Image Engine Design nor the names of any
//       other contributors to this software may be used to endorse or
//       promote products derived from this software without specific prior
//       written permission.
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

#include "GafferCycles/IECoreCyclesPreview/IECoreCycles.h"

// Cycles
#include "util/log.h"
#include "util/path.h"
#include "util/version.h"

#include "IECore/MessageHandler.h"
#include "IECore/SimpleTypedData.h"

#include "boost/algorithm/string.hpp"

#include "fmt/format.h"

#include <filesystem>

// Cycles
IECORE_PUSH_DEFAULT_VISIBILITY
#include "device/device.h"
#include "graph/node.h"
#include "util/openimagedenoise.h"
IECORE_POP_DEFAULT_VISIBILITY

namespace
{

// Version
std::string cyclesVersion = CYCLES_VERSION_STRING;

// Data for binding
IECore::CompoundDataPtr g_deviceData;
IECore::CompoundDataPtr g_nodeData;
IECore::CompoundDataPtr g_shaderData;
IECore::CompoundDataPtr g_lightData;
IECore::CompoundDataPtr g_passData;

// Get sockets data
IECore::CompoundDataPtr getSockets( const ccl::NodeType *nodeType, const bool output )
{
	IECore::CompoundDataPtr result = new IECore::CompoundData();
	IECore::CompoundDataMap &sockets = result->writable();

	if( !output )
	{
		for( const ccl::SocketType &socketType : nodeType->inputs )
		{
			IECore::CompoundDataPtr socket = new IECore::CompoundData();
			IECore::CompoundDataMap &s = socket->writable();
			std::string name( socketType.name.c_str() );
			std::string uiName( socketType.ui_name.c_str() );
			if( boost::contains( name, "." ) )
			{
				std::vector<std::string> split;
				boost::split( split, name, boost::is_any_of( "." ) );
				if( split[0] == "tex_mapping" )
				{
					s["category"] = new IECore::StringData( "Texture Mapping" );
				}
			}
			s["ui_name"] = new IECore::StringData( uiName );

			s["type"] = new IECore::StringData( ccl::SocketType::type_name( socketType.type ).c_str() );
			if( socketType.type == ccl::SocketType::ENUM )
			{
				const ccl::NodeEnum *enums = socketType.enum_values;
				IECore::CompoundDataPtr enumData = new IECore::CompoundData();
				IECore::CompoundDataMap &e = enumData->writable();
				for( auto it = enums->begin(), eIt = enums->end(); it != eIt; ++it )
				{
					std::string uiEnumName( it->first.c_str() );
					uiEnumName[0] = toupper( uiEnumName[0] );
					boost::replace_all( uiEnumName, "_", " " );

					e[uiEnumName.c_str()] = new IECore::StringData( it->first.c_str() );
				}
				s["enum_values"] = std::move( enumData );
			}
			s["is_array"] = new IECore::BoolData( socketType.is_array() );
			s["flags"] = new IECore::IntData( socketType.flags );

			// Some of the texture mapping nodes have a dot in them, replace here with 2 underscores
			std::string actualName = boost::replace_first_copy( name, ".", "__" );
			sockets[actualName] = std::move( socket );
		}
	}
	else
	{
		for( const ccl::SocketType &socketType : nodeType->outputs )
		{
			IECore::CompoundDataPtr socket = new IECore::CompoundData();
			IECore::CompoundDataMap &s = socket->writable();
			s["ui_name"] = new IECore::StringData( socketType.ui_name.c_str() );
			s["type"] = new IECore::StringData( ccl::SocketType::type_name( socketType.type ).c_str() );
			s["is_array"] = new IECore::BoolData( socketType.is_array() );
			s["flags"] = new IECore::IntData( socketType.flags );
			sockets[socketType.name.c_str()] = std::move( socket );
		}
	}

	return IECore::CompoundDataPtr( result );
}

IECore::CompoundDataPtr deviceData()
{
	IECore::CompoundDataPtr result = new IECore::CompoundData();
	IECore::CompoundDataMap &devices = result->writable();

	for( const ccl::DeviceInfo &device : ccl::Device::available_devices() )
	{
		IECore::CompoundDataPtr dev = new IECore::CompoundData();
		IECore::CompoundDataMap &d = dev->writable();

		d["type"] = new IECore::StringData( ccl::Device::string_from_type( device.type ) );
		d["description"] = new IECore::StringData( device.description );
		d["id"] = new IECore::StringData( device.id );
		d["num"] = new IECore::IntData( device.num );
		d["display_device"] = new IECore::BoolData( device.display_device );
		d["has_nanovdb"] = new IECore::BoolData( device.has_nanovdb );
		d["has_osl"] = new IECore::BoolData( device.has_osl );
		d["has_profiling"] = new IECore::BoolData( device.has_profiling );
		d["has_peer_memory"] = new IECore::BoolData( device.has_peer_memory );
		d["has_gpu_queue"] = new IECore::BoolData( device.has_gpu_queue );
		d["cpu_threads"] = new IECore::IntData( device.cpu_threads );
		d["denoisers"] = new IECore::IntData( device.denoisers );

		devices[device.id] = std::move( dev );
	}
	return result;
}

IECore::CompoundDataPtr nodeData()
{
	IECore::CompoundDataPtr result = new IECore::CompoundData();
	IECore::CompoundDataMap &nodes = result->writable();

	for( const auto& nodeType : ccl::NodeType::types() )
	{
		const ccl::NodeType *cNodeType = ccl::NodeType::find( nodeType.first );
		if( cNodeType )
		{
			// We skip "ShaderNode" types here
			if( cNodeType->type == ccl::NodeType::SHADER )
				continue;

			// The shader node we skip
			if( nodeType.first == "shader" )
				continue;

			IECore::CompoundDataPtr node = new IECore::CompoundData();
			IECore::CompoundDataMap &n = node->writable();
			n["in"] = getSockets( cNodeType, false );
			n["out"] = getSockets( cNodeType, true );
			nodes[nodeType.first.c_str()] = std::move( node );
		}
	}
	return result;
}

IECore::CompoundDataPtr shaderData()
{
	IECore::CompoundDataPtr result = new IECore::CompoundData();
	IECore::CompoundDataMap &shaders = result->writable();

	for( const auto& nodeType : ccl::NodeType::types() )
	{
		// Skip over the "output" ShaderNode, as this is a part of the main
		// "shader" node.
		if( std::string( nodeType.first.c_str() ) == "output" )
			continue;

		const ccl::NodeType *cNodeType = ccl::NodeType::find( nodeType.first );
		if( cNodeType )
		{
			if( cNodeType->type == ccl::NodeType::SHADER )
			{
				IECore::CompoundDataPtr shader = new IECore::CompoundData();
				IECore::CompoundDataMap &s = shader->writable();
				s["in"] = getSockets( cNodeType, false );
				s["out"] = getSockets( cNodeType, true );

				std::string type( nodeType.first.c_str() );

				if( boost::ends_with( type, "bsdf" ) )
				{
					s["type"] = new IECore::StringData( "surface" );
					s["category"] = new IECore::StringData( "Shader" );
				}
				else if( boost::starts_with( type, "convert" ) )
				{
					s["type"] = new IECore::StringData( "emission" );
					s["category"] = new IECore::StringData( "Converter" );
				}
				else if( boost::ends_with( type, "closure" ) )
				{
					s["type"] = new IECore::StringData( "surface" );
					s["category"] = new IECore::StringData( "Shader" );
				}
				else if( boost::equals( type, "subsurface_scattering" ) )
				{
					s["type"] = new IECore::StringData( "surface" );
					s["category"] = new IECore::StringData( "Shader" );
				}
				else if( boost::equals( type, "emission" ) )
				{
					s["type"] = new IECore::StringData( "surface" );
					s["category"] = new IECore::StringData( "Shader" );
				}
				else if( boost::equals( type, "background_shader" ) )
				{
					s["type"] = new IECore::StringData( "surface" );
					s["category"] = new IECore::StringData( "Shader" );
				}
				else if( boost::equals( type, "holdout" ) )
				{
					s["type"] = new IECore::StringData( "surface" );
					s["category"] = new IECore::StringData( "Shader" );
				}
				else if( boost::ends_with( type, "volume" ) )
				{
					s["type"] = new IECore::StringData( "volume" );
					s["category"] = new IECore::StringData( "Shader" );
				}
				else if( boost::ends_with( type, "texture" ) )
				{
					s["type"] = new IECore::StringData( "emission" );
					s["category"] = new IECore::StringData( "Texture" );
				}
				else if( boost::ends_with( type, "displacement" ) )
				{
					s["type"] = new IECore::StringData( "displacement" );
					s["category"] = new IECore::StringData( "Vector" );
				}
				else if( boost::starts_with( type, "combine" ) )
				{
					s["type"] = new IECore::StringData( "emission" );
					s["category"] = new IECore::StringData( "Converter" );
				}
				else if( boost::starts_with( type, "separate" ) )
				{
					s["type"] = new IECore::StringData( "emission" );
					s["category"] = new IECore::StringData( "Converter" );
				}
				else if( boost::ends_with( type, "info" ) )
				{
					s["type"] = new IECore::StringData( "emission" );
					s["category"] = new IECore::StringData( "Input" );
				}
				else if( ( boost::equals( type, "ambient_occlusion" ) )
					|| ( boost::equals( type, "attribute" ) )
					|| ( boost::equals( type, "bevel" ) )
					|| ( boost::equals( type, "camera" ) )
					|| ( boost::equals( type, "fresnel" ) )
					|| ( boost::equals( type, "geometry" ) )
					|| ( boost::equals( type, "layer_weight" ) )
					|| ( boost::equals( type, "light_path" ) )
					|| ( boost::equals( type, "rgb" ) )
					|| ( boost::equals( type, "tangent" ) )
					|| ( boost::equals( type, "texture_coordinate" ) )
					|| ( boost::equals( type, "uvmap" ) )
					|| ( boost::equals( type, "value" ) )
					|| ( boost::equals( type, "wireframe" ) )
				)
				{
					s["type"] = new IECore::StringData( "emission" );
					s["category"] = new IECore::StringData( "Input" );
				}
				else if( ( boost::equals( type, "brightness_contrast" ) )
					|| ( boost::equals( type, "gamma" ) )
					|| ( boost::equals( type, "hsv" ) )
					|| ( boost::equals( type, "invert" ) )
					|| ( boost::equals( type, "light_falloff" ) )
					|| ( boost::equals( type, "mix" ) )
					|| ( boost::equals( type, "rgb_curves" ) )
				)
				{
					s["type"] = new IECore::StringData( "emission" );
					s["category"] = new IECore::StringData( "Color" );
				}
				else if( ( boost::equals( type, "bump" ) )
					|| ( boost::equals( type, "mapping" ) )
					|| ( boost::equals( type, "normal" ) )
					|| ( boost::equals( type, "normal_map" ) )
					|| ( boost::equals( type, "vector_curves" ) )
					|| ( boost::equals( type, "vector_transform" ) )
				)
				{
					s["type"] = new IECore::StringData( "emission" );
					s["category"] = new IECore::StringData( "Vector" );
				}
				else if( ( boost::equals( type, "blackbody" ) )
					|| ( boost::equals( type, "rgb_ramp" ) )
					|| ( boost::equals( type, "math" ) )
					|| ( boost::equals( type, "rgb_to_bw" ) )
					|| ( boost::equals( type, "vector_math" ) )
					|| ( boost::equals( type, "wavelength" ) )
				)
				{
					s["type"] = new IECore::StringData( "emission" );
					s["category"] = new IECore::StringData( "Converter" );
				}
				else if( boost::equals( type, "ies_light" ) )
				{
					s["type"] = new IECore::StringData( "emission" );
					s["category"] = new IECore::StringData( "Texture" );
				}
				else
				{
					s["type"] = new IECore::StringData( "emission" );
					s["category"] = new IECore::StringData( "Misc" );
				}

				shaders[type] = std::move( shader );
			}
		}
	}

	return result;
}

IECore::CompoundDataPtr lightData()
{
	IECore::CompoundDataPtr result = new IECore::CompoundData();
	IECore::CompoundDataMap &lights = result->writable();

	const ccl::NodeType *cNodeType = ccl::NodeType::find( ccl::ustring( "light" ) );
	if( cNodeType )
	{
		IECore::CompoundDataPtr _sockets = getSockets( cNodeType, false );
		IECore::CompoundDataMap _in = _sockets->readable();

		const ccl::SocketType *socketType = cNodeType->find_input( ccl::ustring( "light_type" ) );
		const ccl::NodeEnum *enums = socketType->enum_values;

		int portalEnum = -1;

		for( auto it = enums->begin(), eIt = enums->end(); it != eIt; ++it )
		{
			IECore::CompoundDataPtr light = new IECore::CompoundData();
			IECore::CompoundDataMap &l = light->writable();
			IECore::CompoundDataPtr sockets = new IECore::CompoundData();
			IECore::CompoundDataMap &in = sockets->writable();

			std::string type( it->first.c_str() );
			type += "_light";

			in["size"] = _in["size"]->copy();
			in["cast_shadow"] = _in["cast_shadow"]->copy();
			in["use_camera"] = _in["use_camera"]->copy();
			in["use_mis"] = _in["use_mis"]->copy();
			in["use_diffuse"] = _in["use_diffuse"]->copy();
			in["use_glossy"] = _in["use_glossy"]->copy();
			in["use_transmission"] = _in["use_transmission"]->copy();
			in["use_scatter"] = _in["use_scatter"]->copy();
			in["use_caustics"] = _in["use_caustics"]->copy();
			in["max_bounces"] = _in["max_bounces"]->copy();
			in["strength"] = _in["strength"]->copy();
			in["lightgroup"] = _in["lightgroup"]->copy();

			if( type == "background_light" )
			{
				in["map_resolution"] = _in["map_resolution"]->copy();
				l["in"] = std::move( sockets );
				l["enum"] = new IECore::IntData( it->second );
				lights[type] = std::move( light );
			}
			else if( type == "area_light" )
			{
				in["sizeu"] = _in["sizeu"]->copy();
				in["sizev"] = _in["sizev"]->copy();
				in["spread"] = _in["spread"]->copy();
				l["in"] = std::move( sockets );
				l["enum"] = new IECore::IntData( it->second );
				portalEnum = it->second;
				lights["disk_light"] = light->copy();
				lights["quad_light"] = light->copy();
			}
			else if( type == "spot_light" )
			{
				in["spot_angle"] = _in["spot_angle"]->copy();
				in["spot_smooth"] = _in["spot_smooth"]->copy();
				in["is_sphere"] = _in["is_sphere"]->copy();
				l["in"] = std::move( sockets );
				l["enum"] = new IECore::IntData( it->second );
				lights[type] = std::move( light );
			}
			else if( type == "point_light" )
			{
				in["is_sphere"] = _in["is_sphere"]->copy();
				l["in"] = std::move( sockets );
				l["enum"] = new IECore::IntData( it->second );
				lights[type] = std::move( light );
			}
			else
			{
				l["in"] = std::move( sockets );
				l["enum"] = new IECore::IntData( it->second );
				lights[type] = std::move( light );
			}
		}
		// Portal
		IECore::CompoundDataPtr light = new IECore::CompoundData();
		IECore::CompoundDataMap &l = light->writable();
		IECore::CompoundDataPtr sockets = new IECore::CompoundData();
		IECore::CompoundDataMap &in = sockets->writable();

		in["is_portal"] = _in["is_portal"]->copy();
		in["sizeu"] = _in["sizeu"]->copy();
		in["sizev"] = _in["sizev"]->copy();
		l["enum"] = new IECore::IntData( portalEnum );
		l["in"] = std::move( sockets );
		lights["portal"] = std::move( light );
	}
	return result;
}

IECore::CompoundDataPtr passData()
{
	IECore::CompoundDataPtr result = new IECore::CompoundData();
	IECore::CompoundDataMap &passes = result->writable();

	const ccl::NodeEnum *enums = ccl::Pass::get_type_enum();

	for( auto it = enums->begin(), eIt = enums->end(); it != eIt; ++it )
	{
		IECore::CompoundDataPtr info = new IECore::CompoundData();
		IECore::CompoundDataMap &i = info->writable();
		ccl::PassInfo passInfo = ccl::Pass::get_info( static_cast<ccl::PassType>( it->second ) );

		i["num_components"] = new IECore::IntData( passInfo.num_components );
		i["use_filter"] = new IECore::BoolData( passInfo.use_filter );
		i["use_exposure"] = new IECore::BoolData( passInfo.use_exposure );
		i["is_written"] = new IECore::BoolData( passInfo.is_written );
		i["use_compositing"] = new IECore::BoolData( passInfo.use_compositing );
		i["use_denoising_albedo"] = new IECore::BoolData( passInfo.use_denoising_albedo );
		i["support_denoise"] = new IECore::BoolData( passInfo.support_denoise );

		passes[it->first.c_str()] = std::move( info );
	}

	return result;
}

} // namespace

namespace IECoreCycles
{

const char *cyclesRoot()
{
	const char *cyclesRoot = getenv( "CYCLES_ROOT" );
	if( !cyclesRoot )
	{
		IECore::msg( IECore::Msg::Error, "IECoreCycles::init", "CYCLES_ROOT environment variable not set" );
		return "";
	}
	return cyclesRoot;
}

bool init()
{
	const char *cyclesRootValue = cyclesRoot();
	auto kernelFile = std::filesystem::path( cyclesRootValue ) / "source" / "kernel" / "types.h";
	if( !std::filesystem::is_regular_file( kernelFile ) )
	{
		IECore::msg( IECore::Msg::Error, "IECoreCycles::init", fmt::format( "File \"{}\" not found", kernelFile ) );
		return false;
	}

	ccl::path_init( cyclesRootValue );

	// This is a global thing for logging
	const char* argv[] = { "-", "v", "1" };
	ccl::util_logging_init( argv[0] );
	ccl::util_logging_start();
	ccl::util_logging_verbosity_set( 0 );

	// Store data for binding
	g_deviceData = deviceData();
	g_nodeData = nodeData();
	g_shaderData = shaderData();
	g_lightData = lightData();
	g_passData = passData();

	return true;
}

int majorVersion()
{
	return CYCLES_VERSION_MAJOR;
}

int minorVersion()
{
	return CYCLES_VERSION_MINOR;
}

int patchVersion()
{
	return CYCLES_VERSION_PATCH;
}

const std::string &versionString()
{
	return cyclesVersion;
}

const IECore::CompoundData *devices()
{
	return g_deviceData.get();
}

const IECore::CompoundData *nodes()
{
	return g_nodeData.get();
}

const IECore::CompoundData *shaders()
{
	return g_shaderData.get();
}

const IECore::CompoundData *lights()
{
	return g_lightData.get();
}

const IECore::CompoundData *passes()
{
	return g_passData.get();
}

bool openImageDenoiseSupported()
{
	return ccl::openimagedenoise_supported();
}

bool optixDenoiseSupported()
{
	for( const ccl::DeviceInfo &device : ccl::Device::available_devices() )
	{
		if( device.type == ccl::DEVICE_OPTIX )
			return true;
	}
	return false;
}

}
