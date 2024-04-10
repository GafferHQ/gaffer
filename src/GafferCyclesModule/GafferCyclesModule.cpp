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

#include "GafferCycles/IECoreCyclesPreview/IECoreCycles.h"
#include "GafferCycles/IECoreCyclesPreview/ShaderNetworkAlgo.h"
#include "GafferCycles/CyclesAttributes.h"
#include "GafferCycles/CyclesBackground.h"
#include "GafferCycles/CyclesOptions.h"
#include "GafferCycles/CyclesLight.h"
#include "GafferCycles/CyclesMeshLight.h"
#include "GafferCycles/CyclesShader.h"
#include "GafferCycles/CyclesRender.h"
#include "GafferCycles/InteractiveCyclesRender.h"

#include "IECore/MessageHandler.h"

// Cycles
#include "device/device.h"
#include "graph/node.h"
#include "util/openimagedenoise.h"
#include "util/path.h"

namespace py = boost::python;
using namespace boost::python;
using namespace GafferBindings;
using namespace GafferDispatchBindings;
using namespace GafferCycles;

namespace
{

py::list getDevices()
{
	py::scope().attr( "hasOptixDenoise" ) = false;

	py::list result;

	for( const ccl::DeviceInfo &device : ccl::Device::available_devices() )
	{
		py::dict d;
		d["type"] = ccl::Device::string_from_type( device.type );
		d["description"] = device.description;
		d["id"] = device.id;
		d["num"] = device.num;
		d["display_device"] = device.display_device;
		d["has_nanovdb"] = device.has_nanovdb;
		d["has_osl"] = device.has_osl;
		d["has_profiling"] = device.has_profiling;
		d["has_peer_memory"] = device.has_peer_memory;
		d["has_gpu_queue"] = device.has_gpu_queue;
		d["cpu_threads"] = device.cpu_threads;
		d["denoisers"] = device.denoisers;

		if( device.type == ccl::DEVICE_OPTIX )
			py::scope().attr( "hasOptixDenoise" ) = true;

		result.append(d);
	}
	return result;
}

py::dict getSockets( const ccl::NodeType *nodeType, const bool output )
{
	py::dict result;

	if( !output )
	{
		for( const ccl::SocketType &socketType : nodeType->inputs )
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
					std::string uiEnumName( it->first.c_str() );
					uiEnumName[0] = toupper( uiEnumName[0] );
					boost::replace_all( uiEnumName, "_", " " );

					enumDict[uiEnumName.c_str()] = it->first.c_str();
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
		for( const ccl::SocketType &socketType : nodeType->outputs )
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

py::dict getNodes()
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

			// The shader node we skip
			if( nodeType.first == "shader" )
				continue;

			py::dict d;
			d["in"] = getSockets( cNodeType, false );
			d["out"] = getSockets( cNodeType, true );
			result[nodeType.first.c_str()] = d;
		}
	}
	return result;
}

py::dict getShaders()
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

py::dict getLights()
{
	py::dict result;

	const ccl::NodeType *cNodeType = ccl::NodeType::find( ccl::ustring( "light" ) );
	if( cNodeType )
	{
		py::dict _in;
		_in = getSockets( cNodeType, false );

		const ccl::SocketType *socketType = cNodeType->find_input( ccl::ustring( "light_type" ) );
		const ccl::NodeEnum *enums = socketType->enum_values;

		for( auto it = enums->begin(), eIt = enums->end(); it != eIt; ++it )
		{
			py::dict d;
			py::dict in;
			std::string type = it->first.c_str();
			type += "_light";

			in["size"] = _in["size"];
			in["cast_shadow"] = _in["cast_shadow"];
			in["use_camera"] = _in["use_camera"];
			in["use_mis"] = _in["use_mis"];
			in["use_diffuse"] = _in["use_diffuse"];
			in["use_glossy"] = _in["use_glossy"];
			in["use_transmission"] = _in["use_transmission"];
			in["use_scatter"] = _in["use_scatter"];
			in["use_caustics"] = _in["use_caustics"];
			in["max_bounces"] = _in["max_bounces"];
			in["strength"] = _in["strength"];
			in["lightgroup"] = _in["lightgroup"];

			if( type == "background_light" )
			{
				in["map_resolution"] = _in["map_resolution"];
				d["enum"] = it->second;
				d["in"] = in;
				result[type] = d;
			}
			else if( type == "area_light" )
			{
				in["sizeu"] = _in["sizeu"];
				in["sizev"] = _in["sizev"];
				in["spread"] = _in["spread"];
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
		in["sizeu"] = _in["sizeu"];
		in["sizev"] = _in["sizev"];
		d["enum"] = result["quad_light"]["enum"];
		d["in"] = in;
		result["portal"] = d;
	}
	return result;
}

py::dict getPasses()
{
	py::dict result;

	const ccl::NodeEnum *enums = ccl::Pass::get_type_enum();

	for( auto it = enums->begin(), eIt = enums->end(); it != eIt; ++it )
	{
		py::dict info;
		ccl::PassInfo passInfo = ccl::Pass::get_info( static_cast<ccl::PassType>( it->second ) );

		info["num_components"] = passInfo.num_components;
		info["use_filter"] = passInfo.use_filter;
		info["use_exposure"] = passInfo.use_exposure;
		info["is_written"] = passInfo.is_written;
		info["use_compositing"] = passInfo.use_compositing;
		info["use_denoising_albedo"] = passInfo.use_denoising_albedo;
		info["support_denoise"] = passInfo.support_denoise;

		result[it->first.c_str()] = info;
	}

	return result;
}

} // namespace

BOOST_PYTHON_MODULE( _GafferCycles )
{

	IECoreCycles::init();

	// Must be initialized to ensure the statically linked Cycles module
	// we are linked to can find the binaries for GPU rendering.
	ccl::path_init( IECoreCycles::cyclesRoot() );

	py::scope().attr( "devices" ) = getDevices();
	py::scope().attr( "nodes" ) = getNodes();
	py::scope().attr( "shaders" ) = getShaders();
	py::scope().attr( "lights" ) = getLights();
	py::scope().attr( "passes" ) = getPasses();

	if( ccl::openimagedenoise_supported() )
		py::scope().attr( "hasOpenImageDenoise" ) = true;
	else
		py::scope().attr( "hasOpenImageDenoise" ) = false;

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

	{
		object ieCoreCyclesModule( borrowed( PyImport_AddModule( "GafferCycles.IECoreCyclesPreview" ) ) );
		scope().attr( "IECoreCyclesPreview" ) = ieCoreCyclesModule;
		scope ieCoreCyclesScope( ieCoreCyclesModule );

		object shaderNetworkAlgoModule( borrowed( PyImport_AddModule( "GafferCycles.IECoreCyclesPreview.ShaderNetworkAlgo" ) ) );
		scope().attr( "ShaderNetworkAlgo" ) = shaderNetworkAlgoModule;
		scope shaderNetworkAlgoScope( shaderNetworkAlgoModule );

		def( "convertUSDShaders", &IECoreCycles::ShaderNetworkAlgo::convertUSDShaders );
	}

}
