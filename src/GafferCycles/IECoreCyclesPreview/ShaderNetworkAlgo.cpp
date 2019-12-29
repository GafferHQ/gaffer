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

#include "IECore/LRUCache.h"
#include "IECore/MessageHandler.h"
#include "IECore/SearchPath.h"
#include "IECore/SimpleTypedData.h"
#include "IECore/SplineData.h"
#include "IECore/VectorTypedData.h"

#include "boost/algorithm/string.hpp"
#include "boost/algorithm/string/predicate.hpp"
#include "boost/lexical_cast.hpp"
#include "boost/filesystem.hpp"
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

std::string shaderCacheGetter( const std::string &shaderName, size_t &cost )
{
	cost = 1;
	const char *oslShaderPaths = getenv( "OSL_SHADER_PATHS" );
	SearchPath searchPath( oslShaderPaths ? oslShaderPaths : "" );
	boost::filesystem::path path = searchPath.find( shaderName + ".oso" );
	if( path.empty() )
	{
		return shaderName;
	}
	else
	{
		return path.string();
	}
}

typedef IECore::LRUCache<std::string, std::string> ShaderSearchPathCache;
ShaderSearchPathCache g_shaderSearchPathCache( shaderCacheGetter, 10000 );

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
	MAP_NODE( "map_range", ccl::MapRangeNode() );
	MAP_NODE( "clamp", ccl::ClampNode() );
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
	MAP_NODE( "volume_info", ccl::VolumeInfoNode() );
	MAP_NODE( "vertex_color", ccl::VertexColorNode() );
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
	MAP_NODE( "white_noise_texture", ccl::WhiteNoiseTextureNode() );
	MAP_NODE( "normal_map", ccl::NormalMapNode() );
	MAP_NODE( "tangent", ccl::TangentNode() );
	MAP_NODE( "uvmap", ccl::UVMapNode() );
	MAP_NODE( "point_density_texture", ccl::PointDensityTextureNode() );
	MAP_NODE( "bevel", ccl::BevelNode() );
	MAP_NODE( "displacement", ccl::DisplacementNode() );
	MAP_NODE( "vector_displacement", ccl::VectorDisplacementNode() );
	MAP_NODE( "aov_output", ccl::OutputAOVNode() );
#undef MAP_NODE
	return nullptr;
}

ccl::SocketType::Type getSocketType( const std::string &name )
{
    if( name == "float" ) return ccl::SocketType::Type::FLOAT;
    if( name == "int" ) return ccl::SocketType::Type::INT;
    if( name == "color" ) return ccl::SocketType::Type::COLOR;
    if( name == "vector" ) return ccl::SocketType::Type::VECTOR;
    if( name == "point" ) return ccl::SocketType::Type::POINT;
    if( name == "normal" ) return ccl::SocketType::Type::NORMAL;
    if( name == "closure" ) return ccl::SocketType::Type::CLOSURE;
    if( name == "string" ) return ccl::SocketType::Type::STRING;
	return ccl::SocketType::Type::UNDEFINED;
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

ccl::ShaderNode *convertWalk( const ShaderNetwork::Parameter &outputParameter, const IECoreScene::ShaderNetwork *shaderNetwork, const std::string &namePrefix, const ccl::ShaderManager *shaderManager, ccl::ShaderGraph *shaderGraph, ShaderMap &converted )
{
	// Reuse previously created node if we can. It is ideal for all assigned
	// shaders in the graph to funnel through the default "output" so
	// that things like MIS/displacement/etc. can be set, however it isn't a
	// requirement. Regardless, we look out for this special node as it already
	// exists in the graph and we simply point to it.
	const IECoreScene::Shader *shader = shaderNetwork->getShader( outputParameter.shader );
	const bool isOutput = ( boost::starts_with( shader->getType(), "ccl:" ) ) && ( shader->getName() == "output" );
	const bool isOSLShader = boost::starts_with( shader->getType(), "osl:" );
	const bool isConverter = boost::starts_with( shader->getName(), "convert" );
	const bool isAOV = boost::starts_with( shader->getType(), "ccl:aov:" );

	auto inserted = converted.insert( { outputParameter.shader, nullptr } );
	ccl::ShaderNode *&node = inserted.first->second;
	if( !inserted.second )
	{
		return node;
	}

	if( isOutput )
	{
		node = (ccl::ShaderNode*)shaderGraph->output();
	}
	else if( isOSLShader )
	{
#ifdef WITH_OSL
		if( shaderManager )
		{
			ccl::OSLShaderManager *manager = (ccl::OSLShaderManager*)shaderManager;
			std::string shaderFileName = g_shaderSearchPathCache.get( shader->getName() );
			node = manager->osl_node( shaderFileName.c_str() );
			node = shaderGraph->add( node );
		}
		else
#endif
		{
#ifdef WITH_OSL
			msg( Msg::Warning, "IECoreCycles::ShaderNetworkAlgo", boost::format( "Couldn't load OSL shader \"%s\" as the shading system is not set to OSL." ) % shader->getName() );
#else
			msg( Msg::Warning, "IECoreCycles::ShaderNetworkAlgo", boost::format( "Couldn't load OSL shader \"%s\" as GafferCycles wasn't compiled with OSL support." ) % shader->getName() );
#endif
			return node;
		}
	}
	else if( isConverter )
	{
		vector<string> split;
		boost::split( split, shader->getName(), boost::is_any_of( "_" ) );
		if( split.size() >= 4 ) // should be 4 eg. "convert, X, to, Y"
		{
			ccl::ConvertNode *convertNode = new ccl::ConvertNode( getSocketType( split[1] ), getSocketType( split[3] ), true );
			node = (ccl::ShaderNode*)convertNode;
			if( node )
				node = shaderGraph->add( node );
		}
	}
	else
	{
		node = getShaderNode( shader->getName() );
		if( node )
			node = shaderGraph->add( node );
	}

	if( !node )
	{
		msg( Msg::Warning, "IECoreCycles::ShaderNetworkAlgo", boost::format( "Couldn't load shader \"%s\"" ) % shader->getName() );
		return node;
	}

	// Create the ShaderNode for this shader output

	string nodeName(
		namePrefix +
		outputParameter.shader.string()
	);
	node->name = ccl::ustring( nodeName.c_str() );

	// Set the shader parameters

	for( const auto &namedParameter : shader->parameters() )
	{
		// We needed to change any "." found in the socket input names to
		// "__", revert that change here.
		string parameterName = boost::replace_first_copy( namedParameter.first.string(), "__", "." );

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
			SocketAlgo::setSocket( node, parameterName, namedParameter.second.get() );
		}
	}

	// Recurse through input connections

	for( const auto &connection : shaderNetwork->inputConnections( outputParameter.shader ) )
	{
		ccl::ShaderNode *sourceNode = convertWalk( connection.source, shaderNetwork, namePrefix, shaderManager, shaderGraph, converted );
		if( !sourceNode )
		{
			continue;
		}

		// We needed to change any "." found in the socket input names to
		// "__", revert that change here.
		string parameterName = boost::replace_first_copy( connection.destination.name.string(), "__", "." );
		if( isOSLShader )
		{
			parameterName = "param_" + connection.destination.name.string();
		}

		InternedString sourceName = connection.source.name;
		const IECoreScene::Shader *sourceShader = shaderNetwork->getShader( connection.source.shader );

		if( ccl::ShaderOutput *shaderOutput = IECoreCycles::ShaderNetworkAlgo::output( sourceNode, sourceName ) )
			if( ccl::ShaderInput *shaderInput = IECoreCycles::ShaderNetworkAlgo::input( node, parameterName ) )
				shaderGraph->connect( shaderOutput, shaderInput );
	}

	if( !isOutput && ( shaderNetwork->outputShader() == shader ) && !isAOV )
	{
		// In the cases where there is no cycles output attached in the network
		// we just connect to the main output node of the cycles shader graph.
		// Either ccl:surface, ccl:volume or ccl:displacement.
		ccl::ShaderNode *outputNode = (ccl::ShaderNode*)shaderGraph->output();
		string input = string( shader->getType().c_str() + 4 );
		if( ccl::ShaderOutput *shaderOutput = IECoreCycles::ShaderNetworkAlgo::output( node, outputParameter.name ) )
		    if( ccl::ShaderInput *shaderInput = IECoreCycles::ShaderNetworkAlgo::input( outputNode, input ) )
				shaderGraph->connect( shaderOutput, shaderInput );
	}

	return node;
}

} // namespace

namespace IECoreCycles
{

namespace ShaderNetworkAlgo
{

// These functions do exist in Cycles, however they check the 'ui_name' and not
// the true 'name' which is really annoying, so we check the 'name' with these.
// We might as well use IECore::InternedString here also for a cleaner API.

ccl::ShaderInput *input( ccl::ShaderNode *node, IECore::InternedString name )
{
	ccl::ustring cname = ccl::ustring( name.c_str() );
	for( ccl::ShaderInput *socket : node->inputs )
	{
		if( socket->socket_type.name == cname )
			return socket;
	}

	msg( Msg::Warning, "IECoreCycles::ShaderNetworkAlgo", boost::format( "Couldn't find socket input \"%s\" on shaderNode \"%s\"" ) % name.string() % string( node->name.c_str() ) );
	return nullptr;
}

ccl::ShaderOutput *output( ccl::ShaderNode *node, IECore::InternedString name )
{
	// If the output connector has no explicit name, we pick the first output
	if( name == "" )
	{
		if ( node->outputs.size() )
			return node->outputs.front();
		else
			return nullptr;
	}

	ccl::ustring cname = ccl::ustring( name.c_str() );

	for( ccl::ShaderOutput *socket : node->outputs )
	{
		if( socket->socket_type.name == cname )
			return socket;
	}

	msg( Msg::Warning, "IECoreCycles::ShaderNetworkAlgo", boost::format( "Couldn't find socket output \"%s\" on shaderNode \"%s\"" ) % name.string() % string ( node->name.c_str() ) );
	return nullptr;
}

ccl::Shader *convert( const IECoreScene::ShaderNetwork *shaderNetwork, const ccl::ShaderManager *shaderManager, const std::string &namePrefix )
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
	ccl::ShaderGraph *graph = new ccl::ShaderGraph();
	const InternedString output = shaderNetwork->getOutput().shader;
	if( output.string().empty() )
	{
		msg( Msg::Warning, "IECoreCycles::ShaderNetworkAlgo", "Shader has no output" );
	}
	else
	{
		if( shaderNetwork->outputShader()->getType() == "ccl:light" )
		{
			// The first shader is an emission node
			for( const auto &connection : shaderNetwork->inputConnections( output ) )
			{
				ccl::ShaderNode *outputNode = convertWalk( connection.source, shaderNetwork, namePrefix, shaderManager, graph, converted );
				ccl::ShaderNode *inputNode = (ccl::ShaderNode*)graph->output();
				if( ccl::ShaderOutput *shaderOutput = IECoreCycles::ShaderNetworkAlgo::output( outputNode, "emission" ) )
				{
					if( ccl::ShaderInput *shaderInput = IECoreCycles::ShaderNetworkAlgo::input( inputNode, "surface" ) )
					{
						graph->connect( shaderOutput, shaderInput );
						break;
					}
				}
				else if( ccl::ShaderOutput *shaderOutput = IECoreCycles::ShaderNetworkAlgo::output( outputNode, "background" ) )
				{
					if( ccl::ShaderInput *shaderInput = IECoreCycles::ShaderNetworkAlgo::input( inputNode, "surface" ) )
					{
						graph->connect( shaderOutput, shaderInput );
						break;
					}
				}
				else
				{
					continue;
				}
			}
		}
		else
			convertWalk( shaderNetwork->getOutput(), shaderNetwork, namePrefix, shaderManager, graph, converted );
	}

	result->set_graph( graph );

	return result;
}

ccl::Light *convert( const IECoreScene::ShaderNetwork *shaderNetwork )
{
	ShaderNetworkPtr networkCopy;
	if( true ) // todo : make conditional on OSL < 1.10
	{
		networkCopy = shaderNetwork->copy();
		IECoreScene::ShaderNetworkAlgo::convertOSLComponentConnections( networkCopy.get() );
		shaderNetwork = networkCopy.get();
	}

	ccl::Light *result = new ccl::Light();

	const InternedString output = shaderNetwork->getOutput().shader;
	if( output.string().empty() )
	{
		msg( Msg::Warning, "IECoreCycles::ShaderNetworkAlgo", "Output has no light shader" );
	}
	else
	{
		// First apply the parameters to the light
		const IECoreScene::Shader *lightShader = shaderNetwork->getShader( output );
		for( const auto &namedParameter : lightShader->parameters() )
		{
			// Skip the ones which don't exist but we need for the Gaffer UI widget updates
			if( namedParameter.first == "exposure" ||
				namedParameter.first == "intensity" ||
				namedParameter.first == "color" ||
				namedParameter.first == "image" ||
				namedParameter.first == "coneAngle" ||
				namedParameter.first == "penumbraAngle" )
				{
					continue;
				}
			SocketAlgo::setSocket( (ccl::Node*)result, namedParameter.first, namedParameter.second.get() );
		}
	}
	return result;
}

ccl::Shader *convertAOV( const IECoreScene::ShaderNetwork *shaderNetwork, ccl::Shader *cshader, const ccl::ShaderManager *shaderManager, const std::string &namePrefix  )
{
	ShaderMap converted;
	convertWalk( shaderNetwork->getOutput(), shaderNetwork, namePrefix, shaderManager, cshader->graph, converted );
	return cshader;
}

ccl::Shader *setSingleSided( ccl::Shader *cshader )
{
	// Cycles doesn't natively support setting single-sided on objects, however we can build
	// a shader which does it for us by checking for backfaces and using a transparentBSDF
	// to emulate the effect.
	ccl::ShaderGraph *graph = cshader->graph;
	ccl::ShaderNode *mixClosure = graph->add( (ccl::ShaderNode*)new ccl::MixClosureNode() );
	ccl::ShaderNode *transparentBSDF = graph->add( (ccl::ShaderNode*)new ccl::TransparentBsdfNode() );
	ccl::ShaderNode *geometry = graph->add( (ccl::ShaderNode*)new ccl::GeometryNode() );

	if( ccl::ShaderOutput *shaderOutput = ShaderNetworkAlgo::output( geometry, "backfacing" ) )
		if( ccl::ShaderInput *shaderInput = ShaderNetworkAlgo::input( mixClosure, "fac" ) )
			graph->connect( shaderOutput, shaderInput );
	
	if( ccl::ShaderOutput *shaderOutput = ShaderNetworkAlgo::output( transparentBSDF, "BSDF" ) )
		if( ccl::ShaderInput *shaderInput = ShaderNetworkAlgo::input( mixClosure, "closure2" ) )
			graph->connect( shaderOutput, shaderInput );

	ccl::OutputNode *output = graph->output();

	if( ccl::ShaderInput *shaderInput = ShaderNetworkAlgo::input( (ccl::ShaderNode*)output, "surface" ) )
	{
		ccl::ShaderOutput *shaderOutput = shaderInput->link;
		if( shaderOutput )
		{
			shaderInput->disconnect();
			if( ccl::ShaderInput *shaderInput2 = ShaderNetworkAlgo::input( mixClosure, "closure1" ) )
				graph->connect( shaderOutput, shaderInput2 );

			if( ccl::ShaderOutput *shaderOutput2 = ShaderNetworkAlgo::output( mixClosure, "closure" ) )
				graph->connect( shaderOutput2, shaderInput );
		}
	}

	return cshader;
}

ccl::Shader *createDefaultShader()
{
	// This creates a camera dot-product shader/facing ratio.
	ccl::Shader *cshader = new ccl::Shader();
	ccl::ShaderGraph *cgraph = new ccl::ShaderGraph();
	cshader->name = ccl::ustring( "defaultSurfaceShader" );
	ccl::ShaderNode *outputNode = (ccl::ShaderNode*)cgraph->output();
	ccl::VectorMathNode *vecMath = new ccl::VectorMathNode();
	vecMath->type = ccl::NODE_VECTOR_MATH_DOT_PRODUCT;
	ccl::GeometryNode *geo = new ccl::GeometryNode();
	ccl::ShaderNode *vecMathNode = cgraph->add( (ccl::ShaderNode*)vecMath );
	ccl::ShaderNode *geoNode = cgraph->add( (ccl::ShaderNode*)geo );
	cgraph->connect( ShaderNetworkAlgo::output( geoNode, "normal" ), 
						ShaderNetworkAlgo::input( vecMathNode, "vector1" ) );
	cgraph->connect( ShaderNetworkAlgo::output( geoNode, "incoming" ), 
						ShaderNetworkAlgo::input( vecMathNode, "vector2" ) );
	cgraph->connect( ShaderNetworkAlgo::output( vecMathNode, "value" ), 
						ShaderNetworkAlgo::input( outputNode, "surface" ) );
	cshader->set_graph( cgraph );

	return cshader;
}

} // namespace ShaderNetworkAlgo

} // namespace IECoreCycles
