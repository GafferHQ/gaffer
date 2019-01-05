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
#include "GafferCycles/CyclesOptions.h"
#include "GafferCycles/CyclesLight.h"
#include "GafferCycles/CyclesShader.h"
#include "GafferCycles/CyclesRender.h"
#include "GafferCycles/InteractiveCyclesRender.h"

// Cycles
#include "device/device.h"
#include "graph/node.h"

namespace py = boost::python;
using namespace GafferBindings;
using namespace GafferDispatchBindings;
using namespace GafferCycles;

namespace
{

// No way of finding how many enums presets exist, so we make up an upper 
// limit of 24 (math node has 24). Lights are defined by an enum as well, so we
// make an upper-bound of 5.
#define CCL_MAX_ENUMS 24
#define CCL_MAX_LIGHTS 5

py::list getDevices()
{
	py::list result;

	ccl::vector<ccl::DeviceInfo> &devices = ccl::Device::available_devices();
	for( const ccl::DeviceInfo &device : devices ) 
	{
		py::dict d;
		d["type"] = ccl::Device::string_from_type( device.type );
		d["description"] = device.description;
		d["id"] = device.id;
		d["num"] = device.num;
		d["display_device"] = device.display_device;
		d["advanced_shading"] = device.advanced_shading;
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

py::dict getSockets( const ccl::NodeType *nodeType, const bool output )
{
	py::dict result;

	if( !output )
	{
		for( const ccl::SocketType socketType : nodeType->inputs )
		{
			py::dict d;
			d["ui_name"] = socketType.ui_name.c_str();
			d["type"] = ccl::SocketType::type_name( socketType.type ).c_str();
			if( socketType.type == ccl::SocketType::ENUM )
			{
				const ccl::NodeEnum *enums = socketType.enum_values;
				py::list enumList;
				// No way of finding how many enums presets exist, so we make up
				// an upper limit of 24 (math node has 24).
				for( int i = 0; i < CCL_MAX_ENUMS; ++i )
				{
					if( enums->exists( i ) )
					{
						enumList.append( enums->operator[](i).c_str() );
					}
					else
					{
						// No more enums
						break;
					}
				}
				d["enum_values"] = enumList;
			}
			d["is_array"] = socketType.is_array();
			d["flags"] = socketType.flags;
			result[socketType.name.c_str()] = d;
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

				result["cycles_shader"] = d;
			}
			else
			{
				result[nodeType.first.c_str()] = d;
			}
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
		if( nodeType.first == "output" )
			continue;

		const ccl::NodeType *cNodeType = ccl::NodeType::find( nodeType.first );
		if( cNodeType )
		{
			if( cNodeType->type == ccl::NodeType::SHADER )
			{
				py::dict d;
				d["in"] = getSockets( cNodeType, false );
				d["out"] = getSockets( cNodeType, true );

				if( boost::ends_with( nodeType.first.c_str(), "bsdf" ) )
				{
					d["type"] = "surface";
					d["category"] = "Shader";
				}
				else if( boost::ends_with( nodeType.first.c_str(), "closure" ) )
				{
					d["type"] = "surface";
					d["category"] = "Shader";
				}
				else if( nodeType.first.c_str() == "subsurface_scattering" )
				{
					d["type"] = "surface";
					d["category"] = "Shader";
				}
				else if( nodeType.first.c_str() == "emission" )
				{
					d["type"] = "surface";
					d["category"] = "Shader";
				}
				else if( nodeType.first.c_str() == "background_shader" )
				{
					d["type"] = "surface";
					d["category"] = "Shader";
				}
				else if( nodeType.first.c_str() == "holdout" )
				{
					d["type"] = "surface";
					d["category"] = "Shader";
				}
				else if( boost::ends_with( nodeType.first.c_str(), "volume" ) )
				{
					d["type"] = "volume";
					d["category"] = "Shader";
				}
				else if( boost::ends_with( nodeType.first.c_str(), "texture" ) )
				{
					d["type"] = "emission";
					d["category"] = "Texture";
				}
				else if( boost::ends_with( nodeType.first.c_str(), "displacement" ) )
				{
					d["type"] = "displacement";
					d["category"] = "Vector";
				}
				else if( boost::starts_with( nodeType.first.c_str(), "combine" ) )
				{
					d["type"] = "emission";
					d["category"] = "Converter";
				}
				else if( boost::starts_with( nodeType.first.c_str(), "separate" ) )
				{
					d["type"] = "emission";
					d["category"] = "Converter";
				}
				else if( boost::ends_with( nodeType.first.c_str(), "info" ) )
				{
					d["type"] = "emission";
					d["category"] = "Input";
				}
				else if( nodeType.first.c_str() == "ambient_occlusion"
					|| nodeType.first.c_str() == "attribute"
					|| nodeType.first.c_str() == "bevel"
					|| nodeType.first.c_str() == "camera"
					|| nodeType.first.c_str() == "fresnel"
					|| nodeType.first.c_str() == "geometry"
					|| nodeType.first.c_str() == "layer_weight"
					|| nodeType.first.c_str() == "light_path"
					|| nodeType.first.c_str() == "rgb"
					|| nodeType.first.c_str() == "tangent"
					|| nodeType.first.c_str() == "texture_coordinate"
					|| nodeType.first.c_str() == "uvmap"
					|| nodeType.first.c_str() == "value"
					|| nodeType.first.c_str() == "wireframe"
				)
				{
					d["type"] = "emission";
					d["category"] = "Input";
				}
				else if( nodeType.first.c_str() == "brightness_contrast"
					|| nodeType.first.c_str() == "gamma"
					|| nodeType.first.c_str() == "hsv"
					|| nodeType.first.c_str() == "invert"
					|| nodeType.first.c_str() == "light_falloff"
					|| nodeType.first.c_str() == "mix"
					|| nodeType.first.c_str() == "rgb_curves"
				)
				{
					d["type"] = "emission";
					d["category"] = "Color";
				}
				else if( nodeType.first.c_str() == "bump"
					|| nodeType.first.c_str() == "mapping"
					|| nodeType.first.c_str() == "normal"
					|| nodeType.first.c_str() == "normal_map"
					|| nodeType.first.c_str() == "vector_curves"
					|| nodeType.first.c_str() == "vector_transform"
				)
				{
					d["type"] = "emission";
					d["category"] = "Vector";
				}
				else if( nodeType.first.c_str() == "blackbody"
					|| nodeType.first.c_str() == "rgb_ramp"
					|| nodeType.first.c_str() == "math"
					|| nodeType.first.c_str() == "rgb_to_bw"
					//|| nodeType.first.c_str() == "shader_to_rgb"
					|| nodeType.first.c_str() == "vector_math"
					|| nodeType.first.c_str() == "wavelength"
				)
				{
					d["type"] = "emission";
					d["category"] = "Converter";
				}
				else if( nodeType.first.c_str() == "ies_light" )
				{
					d["type"] = "emission";
					d["category"] = "Texture";
				}

				result[nodeType.first.c_str()] = d;
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

		const ccl::SocketType *socketType = cNodeType->find_input( ccl::ustring( "type" ) );
		const ccl::NodeEnum *enums = socketType->enum_values;

		for( int i = 0; i < CCL_MAX_LIGHTS; ++i )
		{
			py::dict d;
			if ( enums->exists(i) )
			{
				py::dict in;
				std::string type = enums->operator[](i).c_str();

				in["size"] = _in["size"];
				in["cast_shadow"] = _in["cast_shadow"];
				in["use_mis"] = _in["use_mis"];
				in["use_diffuse"] = _in["use_diffuse"];
				in["use_glossy"] = _in["use_glossy"];
				in["use_transmission"] = _in["use_transmission"];
				in["use_scatter"] = _in["use_scatter"];
				in["max_bounces"] = _in["max_bounces"];
				in["samples"] = _in["samples"];

				if( type == "background" )
				{
					// Part of CyclesOptions
					continue;
				}
				else if( type == "area" )
				{
					py::dict shape;
					py::list shapeList;
					shapeList.append( "ellipse" );
					shapeList.append( "disk" );
					shapeList.append( "rectangle" );
					shapeList.append( "square" );
					shape["enum_values"] = shapeList;
					shape["ui_name"] = "Shape";
					shape["type"] = "enum";
					shape["is_array"] = false;
					shape["flags"] = 0;
					//in["axisu"] = _in["axisu"];
					//in["axisv"] = _in["axisv"];
					//in["sizeu"] = _in["sizeu"];
					//in["sizev"] = _in["sizev"];
					in["shape"] = shape;
				}
				else if( type == "spot" )
				{
					in["spot_angle"] = _in["spot_angle"];
					in["spot_smooth"] = _in["spot_smooth"];
				}

				d["in"] = in;
				result[type] = d;
			}
		}
		// Portal
		py::dict in;
		py::dict shape;
		shape["shape"] = result["area"]["in"]["shape"];
		in["in"] = shape;
		result["portal"] = in;
	}
	return result;
}

} // namespace

BOOST_PYTHON_MODULE( _GafferCycles )
{

	py::scope().attr( "devices" ) = getDevices();
	py::scope().attr( "nodes" ) = getNodes();
	py::scope().attr( "shaders" ) = getShaders();
	py::scope().attr( "lights" ) = getLights();

	DependencyNodeClass<CyclesAttributes>();
	DependencyNodeClass<CyclesOptions>();
	DependencyNodeClass<CyclesLight>();
	DependencyNodeClass<CyclesShader>();
	TaskNodeClass<CyclesRender>();
	NodeClass<InteractiveCyclesRender>();

}
