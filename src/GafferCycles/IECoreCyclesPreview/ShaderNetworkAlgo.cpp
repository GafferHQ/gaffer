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

#include "GafferCycles/IECoreCyclesPreview/SocketAlgo.h"

#include "IECoreScene/Shader.h"
#include "IECoreScene/ShaderNetworkAlgo.h"

#include "IECore/AngleConversion.h"
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
IECORE_PUSH_DEFAULT_VISIBILITY
#include "scene/shader_nodes.h"
#include "scene/osl.h"
#include "util/path.h"
IECORE_POP_DEFAULT_VISIBILITY

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

ccl::ShaderNode *getShaderNode( ccl::ShaderGraph *graph, const std::string &name )
{
#define MAP_NODE(nodeTypeName, nodeType) if( name == nodeTypeName ){ auto *shaderNode = graph->create_node<nodeType>(); return (ccl::ShaderNode*)shaderNode; }
	MAP_NODE( "rgb_curves", ccl::RGBCurvesNode );
	MAP_NODE( "vector_curves", ccl::VectorCurvesNode );
	MAP_NODE( "rgb_ramp", ccl::RGBRampNode );
	MAP_NODE( "color", ccl::ColorNode );
	MAP_NODE( "value", ccl::ValueNode );
	MAP_NODE( "camera", ccl::CameraNode );
	MAP_NODE( "invert", ccl::InvertNode );
	MAP_NODE( "gamma", ccl::GammaNode );
	MAP_NODE( "brightness_contrast", ccl::BrightContrastNode );
	MAP_NODE( "mix", ccl::MixNode );
	MAP_NODE( "separate_rgb", ccl::SeparateRGBNode );
	MAP_NODE( "combine_rgb", ccl::CombineRGBNode );
	MAP_NODE( "separate_hsv", ccl::SeparateHSVNode );
	MAP_NODE( "combine_hsv", ccl::CombineHSVNode );
	MAP_NODE( "separate_xyz", ccl::SeparateXYZNode );
	MAP_NODE( "combine_xyz", ccl::CombineXYZNode );
	MAP_NODE( "hsv", ccl::HSVNode );
	MAP_NODE( "rgb_to_bw", ccl::RGBToBWNode );
	MAP_NODE( "map_range", ccl::MapRangeNode );
	MAP_NODE( "clamp", ccl::ClampNode );
	MAP_NODE( "math", ccl::MathNode );
	MAP_NODE( "vector_math", ccl::VectorMathNode );
	MAP_NODE( "vector_rotate", ccl::VectorRotateNode );
	MAP_NODE( "vector_transform", ccl::VectorTransformNode );
	MAP_NODE( "normal", ccl::NormalNode );
	MAP_NODE( "mapping", ccl::MappingNode );
	MAP_NODE( "fresnel", ccl::FresnelNode );
	MAP_NODE( "layer_weight", ccl::LayerWeightNode );
	MAP_NODE( "add_closure", ccl::AddClosureNode );
	MAP_NODE( "mix_closure", ccl::MixClosureNode );
	MAP_NODE( "attribute", ccl::AttributeNode );
	MAP_NODE( "background_shader", ccl::BackgroundNode );
	MAP_NODE( "holdout", ccl::HoldoutNode );
	MAP_NODE( "anisotropic_bsdf", ccl::AnisotropicBsdfNode );
	MAP_NODE( "diffuse_bsdf", ccl::DiffuseBsdfNode );
	MAP_NODE( "subsurface_scattering", ccl::SubsurfaceScatteringNode );
	MAP_NODE( "glossy_bsdf", ccl::GlossyBsdfNode );
	MAP_NODE( "glass_bsdf", ccl::GlassBsdfNode );
	MAP_NODE( "refraction_bsdf", ccl::RefractionBsdfNode );
	MAP_NODE( "toon_bsdf", ccl::ToonBsdfNode );
	MAP_NODE( "hair_bsdf", ccl::HairBsdfNode );
	MAP_NODE( "principled_hair_bsdf", ccl::PrincipledHairBsdfNode );
	MAP_NODE( "principled_bsdf", ccl::PrincipledBsdfNode );
	MAP_NODE( "translucent_bsdf", ccl::TranslucentBsdfNode );
	MAP_NODE( "transparent_bsdf", ccl::TransparentBsdfNode );
	MAP_NODE( "velvet_bsdf", ccl::VelvetBsdfNode );
	MAP_NODE( "emission", ccl::EmissionNode );
	MAP_NODE( "ambient_occlusion", ccl::AmbientOcclusionNode );
	MAP_NODE( "scatter_volume", ccl::ScatterVolumeNode );
	MAP_NODE( "absorption_volume", ccl::AbsorptionVolumeNode );
	MAP_NODE( "principled_volume", ccl::PrincipledVolumeNode );
	MAP_NODE( "geometry", ccl::GeometryNode );
	MAP_NODE( "wireframe", ccl::WireframeNode );
	MAP_NODE( "wavelength", ccl::WavelengthNode );
	MAP_NODE( "blackbody", ccl::BlackbodyNode );
	MAP_NODE( "light_path", ccl::LightPathNode );
	MAP_NODE( "light_falloff", ccl::LightFalloffNode );
	MAP_NODE( "object_info", ccl::ObjectInfoNode );
	MAP_NODE( "particle_info", ccl::ParticleInfoNode );
	MAP_NODE( "hair_info", ccl::HairInfoNode );
	MAP_NODE( "volume_info", ccl::VolumeInfoNode );
	MAP_NODE( "vertex_color", ccl::VertexColorNode );
	MAP_NODE( "bump", ccl::BumpNode );
	MAP_NODE( "image_texture", ccl::ImageTextureNode );
	MAP_NODE( "environment_texture", ccl::EnvironmentTextureNode );
	MAP_NODE( "gradient_texture", ccl::GradientTextureNode );
	MAP_NODE( "voronoi_texture", ccl::VoronoiTextureNode );
	MAP_NODE( "magic_texture", ccl::MagicTextureNode );
	MAP_NODE( "wave_texture", ccl::WaveTextureNode );
	MAP_NODE( "checker_texture", ccl::CheckerTextureNode );
	MAP_NODE( "brick_texture", ccl::BrickTextureNode );
	MAP_NODE( "noise_texture", ccl::NoiseTextureNode );
	MAP_NODE( "musgrave_texture", ccl::MusgraveTextureNode );
	MAP_NODE( "texture_coordinate", ccl::TextureCoordinateNode );
	MAP_NODE( "sky_texture", ccl::SkyTextureNode );
	MAP_NODE( "ies_light", ccl::IESLightNode );
	MAP_NODE( "white_noise_texture", ccl::WhiteNoiseTextureNode );
	MAP_NODE( "normal_map", ccl::NormalMapNode );
	MAP_NODE( "tangent", ccl::TangentNode );
	MAP_NODE( "uvmap", ccl::UVMapNode );
	MAP_NODE( "point_density_texture", ccl::PointDensityTextureNode );
	MAP_NODE( "bevel", ccl::BevelNode );
	MAP_NODE( "displacement", ccl::DisplacementNode );
	MAP_NODE( "vector_displacement", ccl::VectorDisplacementNode );
	MAP_NODE( "aov_output", ccl::OutputAOVNode );
	MAP_NODE( "set_normal", ccl::SetNormalNode );
#if WITH_CYCLES_SDF
	MAP_NODE( "sdf_primitive", ccl::SdfPrimitiveNode );
	MAP_NODE( "sdf_op", ccl::SdfOpNode );
	MAP_NODE( "sdf_vector_op", ccl::SdfVectorOpNode );
#endif
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
	using PositionsVector = vector<typename Spline::XType>;
	using ValuesVector = vector<typename Spline::YType>;
	using PositionsData = TypedData<PositionsVector>;
	using ValuesData = TypedData<ValuesVector>;

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

ccl::ShaderNode *convertWalk( const ShaderNetwork::Parameter &outputParameter, const IECoreScene::ShaderNetwork *shaderNetwork, const std::string &namePrefix, ccl::ShaderManager *shaderManager, ccl::ShaderGraph *shaderGraph, ShaderMap &converted )
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
	const bool isImageTexture = shader->getName() == "image_texture";

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
		if( shaderManager && shaderManager->use_osl() )
		{
			ccl::OSLShaderManager *manager = (ccl::OSLShaderManager*)shaderManager;
			std::string shaderFileName = g_shaderSearchPathCache.get( shader->getName() );
			node = manager->osl_node( shaderGraph, shaderManager, shaderFileName.c_str() );
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
			ccl::ConvertNode *convertNode = shaderGraph->create_node<ccl::ConvertNode>( getSocketType( split[1] ), getSocketType( split[3] ), true );
			node = (ccl::ShaderNode*)convertNode;
			if( node )
				node = shaderGraph->add( node );
		}
	}
	else
	{
		node = getShaderNode( shaderGraph, shader->getName() );
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
			if( !isOSLShader )
			{
				if( const ccl::SocketType *socket = node->type->find_input( ccl::ustring( parameterName.c_str() ) ) )
					SocketAlgo::setRampSocket( node, socket, splineData->readable() );
			}
			else
			{
				setSplineParameter( node, parameterName, splineData->readable() );
			}
		}
		else if( const SplinefColor3fData *splineData = runTimeCast<const SplinefColor3fData>( namedParameter.second.get() ) )
		{
			if( !isOSLShader )
			{
				if( const ccl::SocketType *socket = node->type->find_input( ccl::ustring( parameterName.c_str() ) ) )
					SocketAlgo::setRampSocket( node, socket, splineData->readable() );
			}
			else
			{
				setSplineParameter( node, parameterName, splineData->readable() );
			}
		}
		else if( isImageTexture && parameterName == "filename" )
		{
			if( const StringData *stringData = runTimeCast<const StringData>( namedParameter.second.get() ) )
			{
				string pathFileName( stringData->readable() );
				string fileName = ccl::path_filename( pathFileName );
				size_t offset = fileName.find( "<UDIM>" );
				ccl::ImageTextureNode *imgTexNode = (ccl::ImageTextureNode*)node;
				if( offset != string::npos )
				{
					// Workaround to find all available tiles
					string baseFileName = fileName.substr( 0, offset );
					vector<string> files;
					boost::filesystem::path path( ccl::path_dirname( pathFileName ) );
					for( boost::filesystem::directory_iterator it( path ); it != boost::filesystem::directory_iterator(); ++it )
					{
						if( boost::filesystem::is_regular_file( it->status() ) || boost::filesystem::is_symlink( it->status() ) )
						{
							string foundFile = it->path().stem().string();
							if( baseFileName == ( foundFile.substr( 0, offset ) ) )
							{
								files.push_back( foundFile );
							}
						}
					}

					ccl::array<int> tiles;
					for( string file : files )
					{
						tiles.push_back_slow( atoi( file.substr( offset, offset+3 ).c_str() ) );
					}
					imgTexNode->set_tiles( tiles );
				}
				imgTexNode->set_filename( ccl::ustring( pathFileName ) );
			}
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

		InternedString sourceName = connection.source.name;

		// Need to create converters if only one of a color or vector's components is connected
		std::vector<std::string> splitName;
		boost::split( splitName, sourceName.string(), boost::is_any_of( "." ) );
		if( splitName.size() > 1 )
		{
			ccl::ShaderNode *snode;
			std::string baseSourceName = splitName.front();
			std::string component = splitName.back();
			std::string input;
			if( ( component == "r" ) || ( component == "g" ) || ( component == "b" ) )
			{
				input = "color";
				ccl::SeparateRGBNode *separateRGBNode = shaderGraph->create_node<ccl::SeparateRGBNode>();
				snode = (ccl::ShaderNode*)separateRGBNode;
				snode = shaderGraph->add( snode );
			}
			else if( ( component == "x" ) || ( component == "y" ) || ( component == "z" ) )
			{
				input = "vector";
				ccl::SeparateXYZNode *separateXYZNode = shaderGraph->create_node<ccl::SeparateXYZNode>();
				snode = (ccl::ShaderNode*)separateXYZNode;
				snode = shaderGraph->add( snode );
			}
			else
			{
				continue;
			}

			if( ccl::ShaderOutput *shaderOutput = IECoreCycles::ShaderNetworkAlgo::output( sourceNode, baseSourceName ) )
			{
				if( ccl::ShaderInput *shaderSepInput = IECoreCycles::ShaderNetworkAlgo::input( snode, input ) )
				{
					shaderGraph->connect( shaderOutput, shaderSepInput );
					if( ccl::ShaderOutput *shaderSepOutput = IECoreCycles::ShaderNetworkAlgo::output( snode, component ) )
					{
						if( ccl::ShaderInput *shaderInput = IECoreCycles::ShaderNetworkAlgo::input( node, parameterName ) )
						{
							shaderGraph->connect( shaderSepOutput, shaderInput );
						}
					}
				}
			}
			continue;
		}

		if( ccl::ShaderOutput *shaderOutput = IECoreCycles::ShaderNetworkAlgo::output( sourceNode, sourceName ) )
		{
			if( ccl::ShaderInput *shaderInput = IECoreCycles::ShaderNetworkAlgo::input( node, parameterName ) )
			{
				shaderGraph->connect( shaderOutput, shaderInput );
			}
		}
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

template<typename T>
T parameterValue( const IECore::Data *data, const IECore::InternedString &name, const T &defaultValue )
{
	using DataType = IECore::TypedData<T>;
	if( auto d = runTimeCast<const DataType>( data ) )
	{
		return d->readable();
	}

	IECore::msg( IECore::Msg::Warning, "IECoreCycles::ShaderNetworkAlgo", boost::format( "Expected %s but got %s for parameter \"%s\"." ) % DataType::staticTypeName() % data->typeName() % name.c_str() );
	return defaultValue;
}

template<typename T>
T parameterValue( const IECore::CompoundDataMap &parameters, const IECore::InternedString &name, const T &defaultValue )
{
	auto it = parameters.find( name );
	if( it != parameters.end() )
	{
		return parameterValue<T>( it->second.get(), name, defaultValue );
	}

	return defaultValue;
}

// Cycles lights just have a single `strength` parameter which
// we want to present as separate "virtual" parameters for
// intensity, color and exposure.
bool contributesToLightStrength( InternedString parameterName )
{
	return
		parameterName == "intensity" ||
		parameterName == "color" ||
		parameterName == "exposure"
	;
}

Imath::Color3f constantLightStrength( const IECoreScene::ShaderNetwork *light )
{
	const IECoreScene::Shader *lightShader = light->outputShader();

	Imath::Color3f strength( 1 );
	if( !light->input( { light->getOutput().shader, "intensity" } ) )
	{
		strength *= parameterValue<float>( lightShader->parameters(), "intensity", 1.0f );
	}

	if( !light->input( { light->getOutput().shader, "color" } ) )
	{
		strength *= parameterValue<Imath::Color3f>( lightShader->parameters(), "color", Imath::Color3f( 1.0f ) );
	}

	// We don't support input connections to exposure - it seems unlikely that
	// you'd want to texture that.
	strength *= powf( 2.0f, parameterValue<float>( lightShader->parameters(), "exposure", 0.0f ) );

	return strength;;
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

ccl::ShaderGraph *convertGraph( const IECoreScene::ShaderNetwork *surfaceShader,
								const IECoreScene::ShaderNetwork *displacementShader,
								const IECoreScene::ShaderNetwork *volumeShader,
								ccl::ShaderManager *shaderManager,
								const std::string &namePrefix )
{
	ccl::ShaderGraph *graph = new ccl::ShaderGraph();
	if( surfaceShader && surfaceShader->getOutput().shader.string().empty() )
	{
		msg( Msg::Warning, "IECoreCycles::ShaderNetworkAlgo", "Shader has no output" );
	}
	else if( volumeShader && volumeShader->getOutput().shader.string().empty() )
	{
		msg( Msg::Warning, "IECoreCycles::ShaderNetworkAlgo", "Shader has no output" );
	}
	else
	{
		if( surfaceShader )
		{
			ShaderMap converted;
			convertWalk( surfaceShader->getOutput(), surfaceShader, namePrefix, shaderManager, graph, converted );
		}
		if( displacementShader )
		{
			ShaderMap converted;
			convertWalk( displacementShader->getOutput(), displacementShader, namePrefix, shaderManager, graph, converted );
		}
		if( volumeShader )
		{
			ShaderMap converted;
			convertWalk( volumeShader->getOutput(), volumeShader, namePrefix, shaderManager, graph, converted );
		}
	}

	return graph;
}

ccl::Shader *convert( const IECoreScene::ShaderNetwork *surfaceShader,
					  const IECoreScene::ShaderNetwork *displacementShader,
					  const IECoreScene::ShaderNetwork *volumeShader,
					  ccl::ShaderManager *shaderManager,
					  const std::string &namePrefix )
{
	string shaderName(
		namePrefix +
		surfaceShader->getOutput().shader.string()
	);

	ccl::ShaderGraph *graph = convertGraph( surfaceShader, displacementShader, volumeShader, shaderManager, namePrefix );

	ccl::Shader *result = new ccl::Shader();
	result->name = ccl::ustring( shaderName.c_str() );
	result->set_graph( graph );

	return result;
}

void convertAOV( const IECoreScene::ShaderNetwork *shaderNetwork, ccl::ShaderGraph *graph, ccl::ShaderManager *shaderManager, const std::string &namePrefix )
{
	ShaderMap converted;
	convertWalk( shaderNetwork->getOutput(), shaderNetwork, namePrefix, shaderManager, graph, converted );
}

void setSingleSided( ccl::ShaderGraph *graph )
{
	// Cycles doesn't natively support setting single-sided on objects, however we can build
	// a shader which does it for us by checking for backfaces and using a transparentBSDF
	// to emulate the effect.
	ccl::ShaderNode *mixClosure = graph->add( (ccl::ShaderNode*)graph->create_node<ccl::MixClosureNode>() );
	ccl::ShaderNode *transparentBSDF = graph->add( (ccl::ShaderNode*)graph->create_node<ccl::TransparentBsdfNode>() );
	ccl::ShaderNode *geometry = graph->add( (ccl::ShaderNode*)graph->create_node<ccl::GeometryNode>() );

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
}

ccl::Shader *createDefaultShader()
{
	// This creates a camera dot-product shader/facing ratio.
	ccl::Shader *cshader = new ccl::Shader();
	ccl::ShaderGraph *cgraph = new ccl::ShaderGraph();
	cshader->name = ccl::ustring( "defaultSurfaceShader" );
	ccl::ShaderNode *outputNode = (ccl::ShaderNode*)cgraph->output();
	ccl::VectorMathNode *vecMath = cgraph->create_node<ccl::VectorMathNode>();
	vecMath->set_math_type( ccl::NODE_VECTOR_MATH_DOT_PRODUCT );
	ccl::GeometryNode *geo = cgraph->create_node<ccl::GeometryNode>();
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

bool hasOSL( const ccl::Shader *cshader )
{
	for( ccl::ShaderNode *snode : cshader->graph->nodes )
	{
		if( snode->special_type == ccl::SHADER_SPECIAL_TYPE_OSL )
			return true;
	}
	return false;
}

void convertLight( const IECoreScene::ShaderNetwork *light, ccl::Light *cyclesLight )
{
	const IECoreScene::Shader *lightShader = light->outputShader();
	if( !lightShader )
	{
		msg( Msg::Warning, "IECoreCycles::ShaderNetworkAlgo::convertLight", "ShaderNetwork has no output shader" );
		return;
	}

	// Convert type

	if( lightShader->getName() == "spot_light" )
	{
		cyclesLight->set_light_type( ccl::LIGHT_SPOT );
	}
	else if( lightShader->getName() == "distant_light" )
	{
		cyclesLight->set_light_type( ccl::LIGHT_DISTANT );
	}
	else if( lightShader->getName() == "background_light" )
	{
		cyclesLight->set_light_type( ccl::LIGHT_BACKGROUND );
	}
	else if(
		lightShader->getName() == "quad_light" ||
		lightShader->getName() == "portal"
	)
	{
		cyclesLight->set_light_type( ccl::LIGHT_AREA );
		cyclesLight->set_size( 2.0f );
	}
	else if( lightShader->getName() == "disk_light" )
	{
		cyclesLight->set_light_type( ccl::LIGHT_AREA );
		cyclesLight->set_size( 2.0f );
		cyclesLight->set_round( true );
	}
	else
	{
		cyclesLight->set_light_type( ccl::LIGHT_POINT );
	}

	// Convert parameters

	for( const auto &[name, value] : lightShader->parameters() )
	{
		if( contributesToLightStrength( name ) )
		{
			continue;
		}
		// Convert angle-based parameters, where we use degress and Cycles uses radians.
		else if( name == "angle" )
		{
			cyclesLight->set_angle( IECore::degreesToRadians( parameterValue<float>( value.get(), name, 0.0f ) ) );
		}
		else if( name == "spot_angle" )
		{
			cyclesLight->set_spot_angle( IECore::degreesToRadians( parameterValue<float>( value.get(), name, 45.0f ) ) );
		}
		else if( name == "spread" )
		{
			cyclesLight->set_spread( IECore::degreesToRadians( parameterValue<float>( value.get(), name, 180.0f ) ) );
		}
		// Convert generic parameters.
		else
		{
			SocketAlgo::setSocket( cyclesLight, name, value.get() );
		}
	}

	// Convert "virtual" parameters to strength. We can't do this for background
	// lights because Cycles will ignore it - we deal with that in
	// `convertLightShader()` instead.
	if( cyclesLight->get_light_type() != ccl::LIGHT_BACKGROUND )
	{
		const Imath::Color3f strength = constantLightStrength( light );
		cyclesLight->set_strength( ccl::make_float3( strength[0], strength[1], strength[2] ) );
	}
	else
	{
		cyclesLight->set_strength( ccl::one_float3() );
	}
}

IECoreScene::ShaderNetworkPtr convertLightShader( const IECoreScene::ShaderNetwork *light )
{
	// Take a copy and replace the output shader (the light itself) with a
	// Cycles emission or background shader as appropriate.

	ShaderNetworkPtr result = light->copy();
	result->removeShader( result->getOutput().shader );

	IECoreScene::ShaderPtr outputShader;
	if( light->outputShader()->getName() == "background_light" )
	{
		outputShader = new IECoreScene::Shader( "background_shader", "ccl:surface" );
	}
	else
	{
		outputShader = new IECoreScene::Shader( "emission", "ccl:surface" );
	}

	outputShader->parameters()["color"] = new Color3fData( Imath::Color3f( 1.0f ) );
	outputShader->parameters()["strength"] = new FloatData( 1.0f );
	InternedString outputHandle = result->addShader( "output", std::move( outputShader ) );
	result->setOutput( outputHandle );

	// Connect up intensity and color to the emission shader if necessary.

	if( auto intensityInput = light->input( { light->getOutput().shader, "intensity" } ) )
	{
		result->addConnection( { intensityInput, { outputHandle, "strength" } } );
	}

	const auto colorInput = light->input( { light->getOutput().shader, "color" } );
	if( colorInput )
	{
		result->addConnection( { colorInput, { outputHandle, "color" } } );
	}

	// Workaround for Cycles ignoring strength for background lights - insert a
	// shader to multiply it into the input `color`. Hopefully we can remove
	// this at some point.
	if( light->outputShader()->getName() == "background_light" )
	{
		const Imath::Color3f strength = constantLightStrength( light );
		if( strength != Imath::Color3f( 1 ) )
		{
			if( colorInput )
			{
				IECoreScene::ShaderPtr tintShader = new IECoreScene::Shader( "vector_math", "ccl:surface" );
				tintShader->parameters()["math_type"] = new StringData( "multiply" );
				tintShader->parameters()["vector2"] = new V3fData( strength );
				const IECore::InternedString tintHandle = result->addShader( "tint", std::move( tintShader ) );
				result->addConnection( { colorInput, { tintHandle, "vector1" } } );
				result->removeConnection( { colorInput, { outputHandle, "color" } } );
				result->addConnection( { { tintHandle, "vector" }, { outputHandle, "color" } } );
			}
			else
			{
				outputShader = result->getShader( outputHandle )->copy();
				outputShader->parameters()["color"] = new Color3fData( strength );
				result->setShader( outputHandle, std::move( outputShader ) );
			}
		}
	}

	return result;
}

} // namespace ShaderNetworkAlgo

} // namespace IECoreCycles
