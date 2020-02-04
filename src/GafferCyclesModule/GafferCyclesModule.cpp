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

#include "boost/algorithm/string.hpp"
#include "boost/python.hpp"

#include "GafferBindings/DependencyNodeBinding.h"

#include "GafferDispatchBindings/TaskNodeBinding.h"

#include "GafferCycles/CyclesAttributes.h"
#include "GafferCycles/CyclesBackground.h"
#include "GafferCycles/CyclesOptions.h"
#include "GafferCycles/CyclesLight.h"
#include "GafferCycles/CyclesMeshLight.h"
#include "GafferCycles/CyclesShader.h"
#include "GafferCycles/CyclesRender.h"
#include "GafferCycles/InteractiveCyclesRender.h"

#include "IECore/MessageHandler.h"
#include "IECore/SearchPath.h"

// Cycles
#include "device/device.h"
#include "graph/node.h"
#include "util/util_logging.h"
#include "util/util_path.h"

namespace py = boost::python;
using namespace GafferBindings;
using namespace GafferDispatchBindings;
using namespace GafferCycles;

namespace
{

static py::list getDevices()
{
	py::list result;

	ccl::vector<ccl::DeviceInfo> devices = ccl::Device::available_devices( ccl::DEVICE_MASK_CPU | ccl::DEVICE_MASK_OPENCL | ccl::DEVICE_MASK_CUDA
#ifdef WITH_OPTIX
	| ccl::DEVICE_MASK_OPTIX
#endif
	);
	devices.push_back( ccl::Device::get_multi_device( devices, 0, true ) );
	for( const ccl::DeviceInfo &device : devices ) 
	{
		py::dict d;
		d["type"] = ccl::Device::string_from_type( device.type );
		d["description"] = device.description;
		d["id"] = device.id;
		d["num"] = device.num;
		d["display_device"] = device.display_device;
		//d["advanced_shading"] = device.advanced_shading;
		d["has_half_images"] = device.has_half_images;
		d["has_volume_decoupled"] = device.has_volume_decoupled;
		d["has_osl"] = device.has_osl;
		d["use_split_kernel"] = device.use_split_kernel;
		d["has_profiling"] = device.has_profiling;
		d["cpu_threads"] = device.cpu_threads;

		result.append(d);
	}
	return result;
}

static py::dict getSockets( const ccl::NodeType *nodeType, const bool output )
{
	py::dict result;

	if( !output )
	{
		for( const ccl::SocketType socketType : nodeType->inputs )
		{
			py::dict d;
			std::string name( socketType.name.c_str() );
			std::string uiName( socketType.ui_name.c_str() );
			if( boost::contains( name, "." ) )
			{
				std::vector<std::string> split;
				boost::split( split, name, boost::is_any_of( "." ) );
				if( split[0] == "tex_mapping" )
					d["category"] = "Texture Mapping";
			}
			d["ui_name"] = uiName;

			d["type"] = ccl::SocketType::type_name( socketType.type ).c_str();
			if( socketType.type == ccl::SocketType::ENUM )
			{
				const ccl::NodeEnum *enums = socketType.enum_values;
				py::dict enumDict;
				for( auto it = enums->begin(), eIt = enums->end(); it != eIt; ++it )
				{
					enumDict[it->first.c_str()] = it->second;
				}
				d["enum_values"] = enumDict;
			}
			d["is_array"] = socketType.is_array();
			d["flags"] = socketType.flags;

			// Some of the texture mapping nodes have a dot in them, replace here with 2 underscores
			std::string actualName = boost::replace_first_copy( name, ".", "__" );
			result[actualName] = d;
		}
	}
	else
	{
		for( const ccl::SocketType socketType : nodeType->outputs )
		{
			py::dict d;
			d["ui_name"] = socketType.ui_name.c_str();
			d["type"] = ccl::SocketType::type_name( socketType.type ).c_str();
			d["is_array"] = socketType.is_array();
			d["flags"] = socketType.flags;
			result[socketType.name.c_str()] = d;
		}
	}

	return result;
}

static py::dict getNodes()
{
	py::dict result;

	for( const auto& nodeType : ccl::NodeType::types() )
	{
		const ccl::NodeType *cNodeType = ccl::NodeType::find( nodeType.first );
		if( cNodeType )
		{
			// We skip "ShaderNode" types here
			if( cNodeType->type == ccl::NodeType::SHADER )
				continue;

			py::dict d;
			d["in"] = getSockets( cNodeType, false );
			d["out"] = getSockets( cNodeType, true );
			
			// The "Shader" type is the main shader interface, not to be
			// confused with "ShaderNode" types which plug into this main
			// one. We combine the "Output" ShaderNode's inputs to this one
			// to simplify things.
			if( nodeType.first == "shader" )
			{
				py::dict output;
				const ccl::NodeType *outputNodeType = ccl::NodeType::find( ccl::ustring( "output" ) );
				if( outputNodeType )
				{
					output["in"] = getSockets( outputNodeType, false );
				}
				d["in"]["surface"] = output["in"]["surface"];
				d["in"]["volume"] = output["in"]["volume"];
				d["in"]["displacement"] = output["in"]["displacement"];
				d["in"]["normal"] = output["in"]["normal"];
				d["type"] = "surface";
				d["category"] = "Shader";

				result["shader"] = d;
			}
			else
			{
				result[nodeType.first.c_str()] = d;
			}
		}
	}
	return result;
}

static py::dict getShaders()
{
	py::dict result;

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
				py::dict d;
				d["in"] = getSockets( cNodeType, false );
				d["out"] = getSockets( cNodeType, true );

				std::string type = nodeType.first.c_str();

				if( boost::ends_with( type, "bsdf" ) )
				{
					d["type"] = "surface";
					d["category"] = "Shader";
				}
				else if( boost::starts_with( type, "convert" ) )
				{
					d["type"] = "emission";
					d["category"] = "Converter";
				}
				else if( boost::ends_with( type, "closure" ) )
				{
					d["type"] = "surface";
					d["category"] = "Shader";
				}
				else if( boost::equals( type, "subsurface_scattering" ) )
				{
					d["type"] = "surface";
					d["category"] = "Shader";
				}
				else if( boost::equals( type, "emission" ) )
				{
					d["type"] = "surface";
					d["category"] = "Shader";
				}
				else if( boost::equals( type, "background_shader" ) )
				{
					d["type"] = "surface";
					d["category"] = "Shader";
				}
				else if( boost::equals( type, "holdout" ) )
				{
					d["type"] = "surface";
					d["category"] = "Shader";
				}
				else if( boost::ends_with( type, "volume" ) )
				{
					d["type"] = "volume";
					d["category"] = "Shader";
				}
				else if( boost::ends_with( type, "texture" ) )
				{
					d["type"] = "emission";
					d["category"] = "Texture";
				}
				else if( boost::ends_with( type, "displacement" ) )
				{
					d["type"] = "displacement";
					d["category"] = "Vector";
				}
				else if( boost::starts_with( type, "combine" ) )
				{
					d["type"] = "emission";
					d["category"] = "Converter";
				}
				else if( boost::starts_with( type, "separate" ) )
				{
					d["type"] = "emission";
					d["category"] = "Converter";
				}
				else if( boost::ends_with( type, "info" ) )
				{
					d["type"] = "emission";
					d["category"] = "Input";
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
					d["type"] = "emission";
					d["category"] = "Input";
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
					d["type"] = "emission";
					d["category"] = "Color";
				}
				else if( ( boost::equals( type, "bump" ) )
					|| ( boost::equals( type, "mapping" ) )
					|| ( boost::equals( type, "normal" ) )
					|| ( boost::equals( type, "normal_map" ) )
					|| ( boost::equals( type, "vector_curves" ) )
					|| ( boost::equals( type, "vector_transform" ) )
				)
				{
					d["type"] = "emission";
					d["category"] = "Vector";
				}
				else if( ( boost::equals( type, "blackbody" ) )
					|| ( boost::equals( type, "rgb_ramp" ) )
					|| ( boost::equals( type, "math" ) )
					|| ( boost::equals( type, "rgb_to_bw" ) )
					//|| type == "shader_to_rgb"
					|| ( boost::equals( type, "vector_math" ) )
					|| ( boost::equals( type, "wavelength" ) )
				)
				{
					d["type"] = "emission";
					d["category"] = "Converter";
				}
				else if( boost::equals( type, "ies_light" ) )
				{
					d["type"] = "emission";
					d["category"] = "Texture";
				}
				else
				{
					d["type"] = "emission";
					d["category"] = "Misc";
				}

				result[type] = d;
			}
		}
	}

	return result;
}

static py::dict getLights()
{
	py::dict result;

	const ccl::NodeType *cNodeType = ccl::NodeType::find( ccl::ustring( "light" ) );
	if( cNodeType )
	{
		py::dict _in;
		_in = getSockets( cNodeType, false );
		// Change name of lightgroups UI name, Blender has light groups as a bitmask
		// so that a single light can be in multiple light group outputs hence the plural.
		// We limit this so a light only participates in one light group.
#ifdef WITH_CYCLES_LIGHTGROUPS
		_in["lightgroups"]["ui_name"] = "Light Group";
#endif

		const ccl::SocketType *socketType = cNodeType->find_input( ccl::ustring( "type" ) );
		const ccl::NodeEnum *enums = socketType->enum_values;

		for( auto it = enums->begin(), eIt = enums->end(); it != eIt; ++it )
		{
			py::dict d;
			py::dict in;
			std::string type = it->first.c_str();
			type += "_light";

			in["size"] = _in["size"];
			in["cast_shadow"] = _in["cast_shadow"];
			in["use_mis"] = _in["use_mis"];
			in["use_diffuse"] = _in["use_diffuse"];
			in["use_glossy"] = _in["use_glossy"];
			in["use_transmission"] = _in["use_transmission"];
			in["use_scatter"] = _in["use_scatter"];
			in["max_bounces"] = _in["max_bounces"];
			in["samples"] = _in["samples"];
			in["strength"] = _in["strength"];
#ifdef WITH_CYCLES_LIGHTGROUPS
			in["lightgroups"] = _in["lightgroups"];
#endif

			if( type == "background_light" )
			{
				in["map_resolution"] = _in["map_resolution"];
				d["enum"] = it->second;
				d["in"] = in;
				result[type] = d;
			}
			else if( type == "area_light" )
			{
				in["axisu"] = _in["axisu"];
				in["axisv"] = _in["axisv"];
				in["sizeu"] = _in["sizeu"];
				in["sizev"] = _in["sizev"];
				d["in"] = in;
				d["enum"] = it->second;
				result["disk_light"] = d;
				result["quad_light"] = d;
			}
			else if( type == "spot_light" )
			{
				in["spot_angle"] = _in["spot_angle"];
				in["spot_smooth"] = _in["spot_smooth"];
				d["in"] = in;
				d["enum"] = it->second;
				result[type] = d;
			}
			else
			{
				d["in"] = in;
				d["enum"] = it->second;
				result[type] = d;
			}
		}
		// Portal
		py::dict d;
		py::dict in;
		in["is_portal"] = _in["is_portal"];
		in["size"] = _in["size"];
		d["enum"] = result["quad_light"]["enum"];
		d["in"] = in;
		result["portal"] = d;
	}
	return result;
}

} // namespace

BOOST_PYTHON_MODULE( _GafferCycles )
{

	// Set path to find shaders & cuda cubins
	#ifdef _WIN32
	std::string paths = boost::str( boost::format( "%s;%s\\\\cycles;%s" ) % getenv( "GAFFERCYCLES" ) %  getenv( "GAFFER_ROOT" ) % getenv( "GAFFER_EXTENSION_PATHS" ) );
	#else
	std::string paths = boost::str( boost::format( "%s:%s/cycles:%s" ) % getenv( "GAFFERCYCLES" ) % getenv( "GAFFER_ROOT" ) % getenv( "GAFFER_EXTENSION_PATHS" ) );
	#endif
	const char *kernelFile = "source/kernel/kernel_globals.h";
	IECore::SearchPath searchPath( paths );
	boost::filesystem::path path = searchPath.find( kernelFile );
	if( path.empty() )
	{
		IECore::msg( IECore::Msg::Error, "CyclesRenderer", "Cannot find GafferCycles location. Have you set the GAFFERCYCLES environment variable?" );
	}
	else
	{
		std::string cclPath = path.string();
		cclPath.erase( cclPath.end() - strlen( kernelFile ), cclPath.end() );
		ccl::path_init( cclPath );
	}

	// This is a global thing for logging
	const char* argv[] = { "-", "v", "1" };
	ccl::util_logging_init( argv[0] );
	ccl::util_logging_start();
	ccl::util_logging_verbosity_set( 0 );

	py::scope().attr( "devices" ) = getDevices();
	py::scope().attr( "nodes" ) = getNodes();
	py::scope().attr( "shaders" ) = getShaders();
	py::scope().attr( "lights" ) = getLights();

#ifdef WITH_CYCLES_ADAPTIVE_SAMPLING
	py::scope().attr( "withAdaptiveSampling" ) = true;
#else
	py::scope().attr( "withAdaptiveSampling" ) = false;
#endif
#ifdef WITH_CYCLES_TEXTURE_CACHE
	py::scope().attr( "withTextureCache" ) = true;
#else
	py::scope().attr( "withTextureCache" ) = false;
#endif
#ifdef WITH_CYCLES_OPENVDB
	py::scope().attr( "withOpenVDB" ) = true;
#else
	py::scope().attr( "withOpenVDB" ) = false;
#endif
#ifdef WITH_CYCLES_LIGHTGROUPS
	py::scope().attr( "withLightGroups" ) = true;
#else
	py::scope().attr( "withLightGroups" ) = false;
#endif

	DependencyNodeClass<CyclesAttributes>();
	DependencyNodeClass<CyclesBackground>();
	DependencyNodeClass<CyclesOptions>();
	DependencyNodeClass<CyclesLight>()
		.def( "loadShader", (void (CyclesLight::*)( const std::string & ) )&CyclesLight::loadShader )
	;
	DependencyNodeClass<CyclesMeshLight>();
	DependencyNodeClass<CyclesShader>();
	TaskNodeClass<CyclesRender>();
	NodeClass<InteractiveCyclesRender>();

}
