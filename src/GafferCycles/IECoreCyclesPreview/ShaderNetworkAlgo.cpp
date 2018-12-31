//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2018, Alex Fuller, Image Engine Design Inc.
//  All rights reserved.
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

#include "GafferCycles/IECoreCyclesPreview/ShaderNetworkAlgo.h"

#include "GafferOSL/OSLShader.h"

#include "GafferCycles/IECoreCyclesPreview/SocketAlgo.h"

#include "IECoreScene/Shader.h"
#include "IECoreScene/ShaderNetworkAlgo.h"

#include "IECore/MessageHandler.h"
#include "IECore/SimpleTypedData.h"
#include "IECore/SplineData.h"
#include "IECore/VectorTypedData.h"

#include "boost/algorithm/string/predicate.hpp"
#include "boost/lexical_cast.hpp"
#include "boost/unordered_map.hpp"

// Cycles
#include "render/nodes.h"
#include "render/osl.h"

using namespace std;
using namespace IECore;
using namespace IECoreScene;
using namespace IECoreCycles;

namespace
{

ccl::ShaderNode *getShaderNode( const std::string &name )
{
#define MAP_NODE(nodeTypeName, nodeType) if( name == nodeTypeName ){ auto *shaderNode = new nodeType; return (ccl::ShaderNode*)shaderNode; }
	MAP_NODE( "rgb_curves", ccl::RGBCurvesNode() );
	MAP_NODE( "vector_curves", ccl::VectorCurvesNode() );
	MAP_NODE( "rgb_ramp", ccl::RGBRampNode() );
	MAP_NODE( "color", ccl::ColorNode() );
	MAP_NODE( "value", ccl::ValueNode() );
	MAP_NODE( "camera", ccl::CameraNode() );
	MAP_NODE( "invert", ccl::InvertNode() );
	MAP_NODE( "gamma", ccl::GammaNode() );
	MAP_NODE( "brightness_contrast", ccl::BrightContrastNode() );
	MAP_NODE( "mix", ccl::MixNode() );
	MAP_NODE( "separate_rgb", ccl::SeparateRGBNode() );
	MAP_NODE( "combine_rgb", ccl::CombineRGBNode() );
	MAP_NODE( "separate_hsv", ccl::SeparateHSVNode() );
	MAP_NODE( "combine_hsv", ccl::CombineHSVNode() );
	MAP_NODE( "separate_xyz", ccl::SeparateXYZNode() );
	MAP_NODE( "combine_xyz", ccl::CombineXYZNode() );
	MAP_NODE( "hsv", ccl::HSVNode() );
	MAP_NODE( "rgb_to_bw", ccl::RGBToBWNode() );
	MAP_NODE( "math", ccl::MathNode() );
	MAP_NODE( "vector_math", ccl::VectorMathNode() );
	MAP_NODE( "vector_transform", ccl::VectorTransformNode() );
	MAP_NODE( "normal", ccl::NormalNode() );
	MAP_NODE( "mapping", ccl::MappingNode() );
	MAP_NODE( "fresnel", ccl::FresnelNode() );
	MAP_NODE( "layer_weight", ccl::LayerWeightNode() );
	MAP_NODE( "add_closure", ccl::AddClosureNode() );
	MAP_NODE( "mix_closure", ccl::MixClosureNode() );
	MAP_NODE( "attribute", ccl::AttributeNode() );
	MAP_NODE( "background_shader", ccl::BackgroundNode() );
	MAP_NODE( "holdout", ccl::HoldoutNode() );
	MAP_NODE( "anisotropic_bsdf", ccl::AnisotropicBsdfNode() );
	MAP_NODE( "diffuse_bsdf", ccl::DiffuseBsdfNode() );
	MAP_NODE( "subsurface_scattering", ccl::SubsurfaceScatteringNode() );
	MAP_NODE( "glossy_bsdf", ccl::GlossyBsdfNode() );
	MAP_NODE( "glass_bsdf", ccl::GlassBsdfNode() );
	MAP_NODE( "refraction_bsdf", ccl::RefractionBsdfNode() );
	MAP_NODE( "toon_bsdf", ccl::ToonBsdfNode() );
	MAP_NODE( "hair_bsdf", ccl::HairBsdfNode() );
	MAP_NODE( "principled_hair_bsdf", ccl::PrincipledHairBsdfNode() );
	MAP_NODE( "principled_bsdf", ccl::PrincipledBsdfNode() );
	MAP_NODE( "translucent_bsdf", ccl::TranslucentBsdfNode() );
	MAP_NODE( "transparent_bsdf", ccl::TransparentBsdfNode() );
	MAP_NODE( "velvet_bsdf", ccl::VelvetBsdfNode() );
	MAP_NODE( "emission", ccl::EmissionNode() );
	MAP_NODE( "ambient_occlusion", ccl::AmbientOcclusionNode() );
	MAP_NODE( "scatter_volume", ccl::ScatterVolumeNode() );
	MAP_NODE( "absorption_volume", ccl::AbsorptionVolumeNode() );
	MAP_NODE( "principled_volume", ccl::PrincipledVolumeNode() );
	MAP_NODE( "geometry", ccl::GeometryNode() );
	MAP_NODE( "wireframe", ccl::WireframeNode() );
	MAP_NODE( "wavelength", ccl::WavelengthNode() );
	MAP_NODE( "blackbody", ccl::BlackbodyNode() );
	MAP_NODE( "light_path", ccl::LightPathNode() );
	MAP_NODE( "light_falloff", ccl::LightFalloffNode() );
	MAP_NODE( "object_info", ccl::ObjectInfoNode() );
	MAP_NODE( "particle_info", ccl::ParticleInfoNode() );
	MAP_NODE( "hair_info", ccl::HairInfoNode() );
	MAP_NODE( "bump", ccl::BumpNode() );
	MAP_NODE( "image_texture", ccl::ImageTextureNode() );
	MAP_NODE( "environment_texture", ccl::EnvironmentTextureNode() );
	MAP_NODE( "gradient_texture", ccl::GradientTextureNode() );
	MAP_NODE( "voronoi_texture", ccl::VoronoiTextureNode() );
	MAP_NODE( "magic_texture", ccl::MagicTextureNode() );
	MAP_NODE( "wave_texture", ccl::WaveTextureNode() );
	MAP_NODE( "checker_texture", ccl::CheckerTextureNode() );
	MAP_NODE( "brick_texture", ccl::BrickTextureNode() );
	MAP_NODE( "noise_texture", ccl::NoiseTextureNode() );
	MAP_NODE( "musgrave_texture", ccl::MusgraveTextureNode() );
	MAP_NODE( "texture_coordinate", ccl::TextureCoordinateNode() );
	MAP_NODE( "sky_texture", ccl::SkyTextureNode() );
	MAP_NODE( "ies_light", ccl::IESLightNode() );
	MAP_NODE( "normal_map", ccl::NormalMapNode() );
	MAP_NODE( "tangent", ccl::TangentNode() );
	MAP_NODE( "uvmap", ccl::UVMapNode() );
	MAP_NODE( "point_density_texture", ccl::PointDensityTextureNode() );
	MAP_NODE( "bevel", ccl::BevelNode() );
	MAP_NODE( "displacement", ccl::DisplacementNode() );
	MAP_NODE( "vector_displacement", ccl::VectorDisplacementNode() );
	MAP_NODE( "add_closure", ccl::AddClosureNode() );
#undef MAP_NODE
	return nullptr;
}

template<typename Spline>
void setSplineParameter( ccl::ShaderNode *node, const std::string &name, const Spline &spline )
{
	typedef vector<typename Spline::XType> PositionsVector;
	typedef vector<typename Spline::YType> ValuesVector;
	typedef TypedData<PositionsVector> PositionsData;
	typedef TypedData<ValuesVector> ValuesData;

	typename PositionsData::Ptr positionsData = new PositionsData;
	typename ValuesData::Ptr valuesData = new ValuesData;

	PositionsVector &positions = positionsData->writable();
	ValuesVector &values = valuesData->writable();
	positions.reserve( spline.points.size() );
	values.reserve( spline.points.size() );

	for( typename Spline::PointContainer::const_iterator it = spline.points.begin(), eIt = spline.points.end(); it != eIt; ++it )
	{
		positions.push_back( it->first );
		values.push_back( it->second );
	}

/*
	AtString basis( g_catmullRomArnoldString );
	if( spline.basis == Spline::Basis::bezier() )
	{
		basis = g_bezierArnoldString;
	}
	else if( spline.basis == Spline::Basis::bSpline() )
	{
		basis = g_bsplineArnoldString;
	}
	else if( spline.basis == Spline::Basis::linear() )
	{
		basis = g_linearArnoldString;
	}
*/

	//GafferOSL::OSLShader::prepareSplineCVsForOSL( positions, values, basis );
	SocketAlgo::setSocket( node, ( name + "Positions" ).c_str(), positionsData.get() );
	SocketAlgo::setSocket( node, ( name + "Values" ).c_str(), valuesData.get() );
	//SocketAlgo::setSocket( node, name + "Basis", basis );
}

typedef boost::unordered_map<ShaderNetwork::Parameter, ccl::ShaderNode *> ShaderMap;

// Equivalent to Python's `s.partition( c )[0]`.
InternedString partitionStart( const InternedString &s, char c )
{
	const size_t index = s.string().find_first_of( '.' );
	if( index == string::npos )
	{
		return s;
	}
	else
	{
		return InternedString( s.c_str(), index );
	}
}

// Equivalent to Python's `s.partition( c )[2]`.
InternedString partitionEnd( const InternedString &s, char c )
{
	const size_t index = s.string().find_first_of( '.' );
	if( index == string::npos )
	{
		return InternedString();
	}
	else
	{
		return InternedString( s.c_str() + index + 1 );
	}
}

ccl::ShaderNode *convertWalk( const ShaderNetwork::Parameter &outputParameter, const IECoreScene::ShaderNetwork *shaderNetwork, const std::string &namePrefix, const ccl::Scene *scene, ccl::Shader *cshader, ShaderMap &converted )
{
	// Reuse previously created node if we can. It is ideal for all assigned
	// shaders in the graph to funnel through the default "cycles_shader" so
	// that things like MIS/displacement/etc. can be set, however it isn't a
	// requirement. Regardless, we look out for this special node as it already
	// exists in the graph and we simply point to it.
	const IECoreScene::Shader *shader = shaderNetwork->getShader( outputParameter.shader );
	const bool isOutput = ( boost::starts_with( shader->getType(), "ccl:" ) ) && ( shader->getName() == "cycles_shader" );
	const bool isOSLShader = boost::starts_with( shader->getType(), "osl:" );

	auto inserted = converted.insert( { outputParameter.shader, nullptr } );
	ccl::ShaderNode *&node = inserted.first->second;
	if( !inserted.second )
	{
		return node;
	}

	// Create the ShaderNode for this shader output

	string nodeName(
		namePrefix +
		outputParameter.shader.string()
	);
	node->name = nodeName.c_str();

	if( isOutput )
	{
		node = (ccl::ShaderNode*)cshader->graph->output();
	}
	else if( isOSLShader )
	{
#ifdef WITH_OSL
		if( scene->params.shadingsystem == ccl::SHADINGSYSTEM_OSL )
		{
			ccl::OSLShaderManager *manager = (ccl::OSLShaderManager*)scene->shader_manager;
			node = manager->osl_node( shader->getName().c_str(), "" );
			node = cshader->graph->add( node );
		}
		else
#endif
		{
			msg( Msg::Warning, "IECoreCycles::ShaderNetworkAlgo", boost::format( "Couldn't load OSL shader \"%s\" as the shading system is not set to OSL." ) % shader->getName() );
			return node;
		}
	}
	else
	{
		node = getShaderNode( shader->getName() );
		if( node )
			node = cshader->graph->add( node );
	}

	if( !node )
	{
		msg( Msg::Warning, "IECoreCycles::ShaderNetworkAlgo", boost::format( "Couldn't load shader \"%s\"" ) % shader->getName() );
		return node;
	}

	// Set the shader parameters

	for( const auto &namedParameter : shader->parameters() )
	{
		string parameterName;
		if( isOSLShader )
		{
			parameterName = "param_" + namedParameter.first.string();
		}
		else
		{
			parameterName = namedParameter.first.string();
		}

		if( const SplineffData *splineData = runTimeCast<const SplineffData>( namedParameter.second.get() ) )
		{
			setSplineParameter( node, parameterName, splineData->readable() );
		}
		else if( const SplinefColor3fData *splineData = runTimeCast<const SplinefColor3fData>( namedParameter.second.get() ) )
		{
			setSplineParameter( node, parameterName, splineData->readable() );
			continue;
		}
		else
		{
			SocketAlgo::setSocket( node, parameterName.c_str(), namedParameter.second.get() );
		}
	}

	// Recurse through input connections

	for( const auto &connection : shaderNetwork->inputConnections( outputParameter.shader ) )
	{
		ccl::ShaderNode *sourceNode = convertWalk( connection.source, shaderNetwork, namePrefix, scene, cshader, converted );
		if( !sourceNode )
		{
			continue;
		}

		string parameterName;
		if( isOSLShader )
		{
			parameterName = "param_" + connection.destination.name.string();
		}
		else
		{
			parameterName = connection.destination.name.string();
		}

		InternedString sourceName = connection.source.name;
		const IECoreScene::Shader *sourceShader = shaderNetwork->getShader( connection.source.shader );
		//if( boost::starts_with( sourceShader->getType(), "osl:" ) )
		//{
		//	sourceName = partitionEnd( sourceName, '.' );
		//}
		cshader->graph->connect( sourceNode->output( sourceName.c_str() ), node->input( parameterName.c_str() ) );
	}

	if( !isOutput && ( shaderNetwork->outputShader() == shader ) )
	{
		// In the cases where there is no cycles_shader attached in the network
		// we just connect to the main output node of the cycles shader graph.
		// Either ccl:surface, ccl:volume or ccl:displacement.
		auto *outputNode = (ccl::ShaderNode*)cshader->graph->output();
		string input = string( shader->getType().c_str() + 4 );
		cshader->graph->connect( node->output( outputParameter.name.string().c_str() ), outputNode->input( input.c_str() ) );
	}

	return node;
}

} // namespace

namespace IECoreCycles
{

namespace ShaderNetworkAlgo
{

ccl::Shader *convert( const IECoreScene::ShaderNetwork *shaderNetwork, const ccl::Scene *scene, const std::string &namePrefix )
{
	ShaderNetworkPtr networkCopy;
	if( true ) // todo : make conditional on OSL < 1.10
	{
		networkCopy = shaderNetwork->copy();
		IECoreScene::ShaderNetworkAlgo::convertOSLComponentConnections( networkCopy.get() );
		shaderNetwork = networkCopy.get();
	}

	ShaderMap converted;
	ccl::Shader *result = new ccl::Shader();
	const InternedString output = shaderNetwork->getOutput().shader;
	if( output.string().empty() )
	{
		msg( Msg::Warning, "IECoreArnold::ShaderNetworkAlgo", "Shader has no output" );
	}
	else
	{
		convertWalk( shaderNetwork->getOutput(), shaderNetwork, namePrefix, scene, result, converted );
	}
	return result;
}

} // namespace ShaderNetworkAlgo

} // namespace IECoreCycles
