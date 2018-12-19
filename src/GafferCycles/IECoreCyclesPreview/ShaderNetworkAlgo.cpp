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

#include "GafferCycles/IECoreCycles/ShaderNetworkAlgo.h"

#include "GafferOSL/OSLShader.h"

#include "IECoreCycles/SocketAlgo.h"

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

using namespace std;
using namespace IECore;
using namespace IECoreScene;
using namespace IECoreCycles;

namespace
{

ccl::ShaderNode *getShaderNode( const std::string &name )
{
#define MAP_NODE(nodeTypeName, nodeType) if( name = nodeTypeName ){ auto *shaderNode = new nodeType; return (ccl::ShaderNode*)shaderNode }
	MAP_NODE( "RGBCurvesNode", ccl::RGBCurvesNode() );
	MAP_NODE( "VectorCurvesNode", ccl::VectorCurvesNode() );
	MAP_NODE( "RGBRampNode", ccl::RGBRampNode() );
	MAP_NODE( "ColorNode", ccl::ColorNode() );
	MAP_NODE( "VectorCurvesNode", ccl::VectorCurvesNode() );
	MAP_NODE( "RGBRampNode", ccl::RGBRampNode() );
	MAP_NODE( "ColorNode", ccl::ColorNode() );
	MAP_NODE( "ValueNode", ccl::ValueNode() );
	MAP_NODE( "CameraNode", ccl::CameraNode() );
	MAP_NODE( "InvertNode", ccl::InvertNode() );
	MAP_NODE( "GammaNode", ccl::GammaNode() );
	MAP_NODE( "BrightContrastNode", ccl::BrightContrastNode() );
	MAP_NODE( "MixNode", ccl::MixNode() );
	MAP_NODE( "SeparateRGBNode", ccl::SeparateRGBNode() );
	MAP_NODE( "CombineRGBNode", ccl::CombineRGBNode() );
	MAP_NODE( "SeparateHSVNode", ccl::SeparateHSVNode() );
	MAP_NODE( "CombineHSVNode", ccl::CombineHSVNode() );
	MAP_NODE( "SeparateXYZNode", ccl::SeparateXYZNode() );
	MAP_NODE( "CombineXYZNode", ccl::CombineXYZNode() );
	MAP_NODE( "HSVNode", ccl::HSVNode() );
	MAP_NODE( "RGBToBWNode", ccl::RGBToBWNode() );
	MAP_NODE( "MathNode", ccl::MathNode() );
	MAP_NODE( "VectorMathNode", ccl::VectorMathNode() );
	MAP_NODE( "VectorTransformNode", ccl::VectorTransformNode() );
	MAP_NODE( "NormalNode", ccl::NormalNode() );
	MAP_NODE( "MappingNode", ccl::MappingNode() );
	MAP_NODE( "FresnelNode", ccl::FresnelNode() );
	MAP_NODE( "LayerWeightNode", ccl::LayerWeightNode() );
	MAP_NODE( "AddClosureNode", ccl::AddClosureNode() );
	MAP_NODE( "MixClosureNode", ccl::MixClosureNode() );
	MAP_NODE( "AttributeNode", ccl::AttributeNode() );
	MAP_NODE( "BackgroundNode", ccl::BackgroundNode() );
	MAP_NODE( "HoldoutNode", ccl::HoldoutNode() );
	MAP_NODE( "AnisotropicBsdfNode", ccl::AnisotropicBsdfNode() );
	MAP_NODE( "DiffuseBsdfNode", ccl::DiffuseBsdfNode() );
	MAP_NODE( "SubsurfaceScatteringNode", ccl::SubsurfaceScatteringNode() );
	MAP_NODE( "GlossyBsdfNode", ccl::GlossyBsdfNode() );
	MAP_NODE( "GlassBsdfNode", ccl::GlassBsdfNode() );
	MAP_NODE( "RefractionBsdfNode", ccl::RefractionBsdfNode() );
	MAP_NODE( "ToonBsdfNode", ccl::ToonBsdfNode() );
	MAP_NODE( "HairBsdfNode", ccl::HairBsdfNode() );
	MAP_NODE( "PrincipledHairBsdfNode", ccl::PrincipledHairBsdfNode() );
	MAP_NODE( "PrincipledBsdfNode", ccl::PrincipledBsdfNode() );
	MAP_NODE( "TranslucentBsdfNode", ccl::TranslucentBsdfNode() );
	MAP_NODE( "TransparentBsdfNode", ccl::TransparentBsdfNode() );
	MAP_NODE( "VelvetBsdfNode", ccl::VelvetBsdfNode() );
	MAP_NODE( "EmissionNode", ccl::EmissionNode() );
	MAP_NODE( "AmbientOcclusionNode", ccl::AmbientOcclusionNode() );
	MAP_NODE( "ScatterVolumeNode", ccl::ScatterVolumeNode() );
	MAP_NODE( "AbsorptionVolumeNode", ccl::AbsorptionVolumeNode() );
	MAP_NODE( "PrincipledVolumeNode", ccl::PrincipledVolumeNode() );
	MAP_NODE( "GeometryNode", ccl::GeometryNode() );
	MAP_NODE( "WireframeNode", ccl::WireframeNode() );
	MAP_NODE( "WavelengthNode", ccl::WavelengthNode() );
	MAP_NODE( "BlackbodyNode", ccl::BlackbodyNode() );
	MAP_NODE( "LightPathNode", ccl::LightPathNode() );
	MAP_NODE( "LightFalloffNode", ccl::LightFalloffNode() );
	MAP_NODE( "ObjectInfoNode", ccl::ObjectInfoNode() );
	MAP_NODE( "ParticleInfoNode", ccl::ParticleInfoNode() );
	MAP_NODE( "HairInfoNode", ccl::HairInfoNode() );
	MAP_NODE( "BumpNode", ccl::BumpNode() );
	MAP_NODE( "ImageTextureNode", ccl::ImageTextureNode() );
	MAP_NODE( "EnvironmentTextureNode", ccl::EnvironmentTextureNode() );
	MAP_NODE( "GradientTextureNode", ccl::GradientTextureNode() );
	MAP_NODE( "VoronoiTextureNode", ccl::VoronoiTextureNode() );
	MAP_NODE( "MagicTextureNode", ccl::MagicTextureNode() );
	MAP_NODE( "WaveTextureNode", ccl::WaveTextureNode() );
	MAP_NODE( "CheckerTextureNode", ccl::CheckerTextureNode() );
	MAP_NODE( "BrickTextureNode", ccl::BrickTextureNode() );
	MAP_NODE( "NoiseTextureNode", ccl::NoiseTextureNode() );
	MAP_NODE( "MusgraveTextureNode", ccl::MusgraveTextureNode() );
	MAP_NODE( "TextureCoordinateNode", ccl::TextureCoordinateNode() );
	MAP_NODE( "SkyTextureNode", ccl::SkyTextureNode() );
	MAP_NODE( "IESLightNode", ccl::IESLightNode() );
	MAP_NODE( "NormalMapNode", ccl::NormalMapNode() );
	MAP_NODE( "TangentNode", ccl::TangentNode() );
	MAP_NODE( "UVMapNode", ccl::UVMapNode() );
	MAP_NODE( "PointDensityTextureNode", ccl::PointDensityTextureNode() );
	MAP_NODE( "BevelNode", ccl::BevelNode() );
	MAP_NODE( "DisplacementNode", ccl::DisplacementNode() );
	MAP_NODE( "VectorDisplacementNode", ccl::VectorDisplacementNode() );
#undef MAP_NODE
	default:
		return nullptr;
}

template<typename Spline>
void setSplineParameter( AtNode *node, const std::string &name, const Spline &spline )
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

	GafferOSL::OSLShader::prepareSplineCVsForOSL( positions, values, basis );
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

ccl::ShaderNode *convertWalk( const ShaderNetwork::Parameter &outputParameter, const IECoreScene::ShaderNetwork *shaderNetwork, const std::string &namePrefix, const ccl::Scene *scene, ccl::Shader *shader, ShaderMap &converted )
{
	// Reuse previously created node if we can. OSL shaders
	// can have multiple outputs, but each Arnold shader node
	// can have only a single output, so we have to emit OSL
	// shaders multiple times, once for each distinct top-level
	// output that is used.

	const IECoreScene::Shader *shader = shaderNetwork->getShader( outputParameter.shader );
	const bool isOSLShader = boost::starts_with( shader->getType(), "osl:" );
	//const InternedString oslOutput = isOSLShader ? partitionStart( outputParameter.name, '.' ) : InternedString();

	auto inserted = converted.insert( { { outputParameter.shader, oslOutput }, nullptr } );
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
	//if( oslOutput.string().size() )
	//{
	//	nodeName += ":" + oslOutput.string();
	//}
	node.name = nodeName.c_str();

	if( isOSLShader )
	{
		if( scene->params.shadingsystem == SHADINGSYSTEM_OSL )
		{
			OSLShaderManager *manager = (OSLShaderManager*)scene->shader_manager;
			node = manager->osl_node( shader->getName().c_str(), "" );
		}
		else
		{
			msg( Msg::Warning, "IECoreCycles::ShaderNetworkAlgo", boost::format( "Couldn't load OSL shader \"%s\" as the shading system is not set to OSL." ) % shader->getName() );
			return node;
		}
	}
	else
	{
		node = getShaderNode( shader->getName() );
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
		ccl::ShaderNode *sourceNode = convertWalk( connection.source, shaderNetwork, namePrefix, scene, shader, converted );
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
		if( boost::starts_with( sourceShader->getType(), "osl:" ) )
		{
			sourceName = partitionEnd( sourceName, '.' );
		}

		//AiNodeLinkOutput( sourceNode, sourceName.c_str(), node, parameterName.c_str() );
		//shader->graph.connect();
	}

	return shader->graph.add( node );
}

} // namespace

namespace IECoreCycles
{

namespace ShaderNetworkAlgo
{

ccl::Shader *convert( const IECoreScene::ShaderNetwork *shaderNetwork, const std::string &namePrefix, const ccl::Scene *scene )
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
