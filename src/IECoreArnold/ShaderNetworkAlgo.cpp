//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

#include "IECoreArnold/ShaderNetworkAlgo.h"

#include "GafferOSL/OSLShader.h"

#include "IECoreArnold/ParameterAlgo.h"

#include "IECoreScene/Shader.h"
#include "IECoreScene/ShaderNetworkAlgo.h"

#include "IECore/AngleConversion.h"
#include "IECore/MessageHandler.h"
#include "IECore/SimpleTypedData.h"
#include "IECore/Spline.h"
#include "IECore/VectorTypedData.h"

#include "boost/algorithm/string/predicate.hpp"
#include "boost/lexical_cast.hpp"
#include "boost/unordered_map.hpp"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace IECoreArnold;

namespace
{

const AtString g_emptyArnoldString( "" );
const AtString g_outputArnoldString( "output" );
const AtString g_shaderNameArnoldString( "shadername" );
const AtString g_oslArnoldString( "osl" );
const AtString g_nameArnoldString( "name" );

using ShaderMap = std::unordered_map<IECore::InternedString, AtNode *>;

template<typename NodeCreator>
AtNode *convertWalk( const ShaderNetwork::Parameter &outputParameter, const IECoreScene::ShaderNetwork *shaderNetwork, const std::string &name, const NodeCreator &nodeCreator, vector<AtNode *> &nodes, ShaderMap &converted, std::vector<IECoreArnold::ShaderNetworkAlgo::NodeParameter> &nodeParameters )
{
	// Reuse previously created node if we can. OSL shaders
	// can have multiple outputs, but each Arnold shader node
	// can have only a single output, so we have to emit OSL
	// shaders multiple times, once for each distinct top-level
	// output that is used.

	const IECoreScene::Shader *shader = shaderNetwork->getShader( outputParameter.shader );
	auto inserted = converted.insert( { outputParameter.shader, nullptr } );
	AtNode *&node = inserted.first->second;
	if( !inserted.second )
	{
		return node;
	}

	// Create the AtNode for this shader output

	string nodeName = name;
	if( outputParameter != shaderNetwork->getOutput() )
	{
		nodeName += ":" + outputParameter.shader.string();
	}

	const bool isOSLShader = boost::starts_with( shader->getType(), "osl:" );
	if( isOSLShader )
	{
		node = nodeCreator( g_oslArnoldString, AtString( nodeName.c_str() ) );
		AiNodeSetStr( node, g_shaderNameArnoldString, AtString( shader->getName().c_str() ) );
	}
	else
	{
		node = nodeCreator(
			AtString( shader->getName().c_str() ),
			AtString( nodeName.c_str() )
		);
	}

	if( !node )
	{
		msg( Msg::Warning, "IECoreArnold::ShaderNetworkAlgo", fmt::format( "Couldn't load shader \"{}\"", shader->getName() ) );
		return node;
	}

	// Set the shader parameters

	IECore::ConstCompoundDataPtr expandedParameters = IECoreScene::ShaderNetworkAlgo::expandSplineParameters(
		shader->parametersData()
	);

	for( const auto &namedParameter : expandedParameters->readable() )
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

		const AtString arnoldParameterName( parameterName.c_str() );

		if( AiParamGetType( AiNodeEntryLookUpParameter( AiNodeGetNodeEntry( node ), arnoldParameterName ) ) == AI_TYPE_NODE )
		{
			if( auto stringValue = runTimeCast<StringData>( namedParameter.second ) )
			{
				nodeParameters.emplace_back( node, arnoldParameterName, AtString( stringValue->readable().c_str() ) );
				continue;
			}
		}

		ParameterAlgo::setParameter( node, arnoldParameterName, namedParameter.second.get() );
	}

	// Recurse through input connections

	for( const auto &connection : shaderNetwork->inputConnections( outputParameter.shader ) )
	{
		AtNode *sourceNode = convertWalk( connection.source, shaderNetwork, name, nodeCreator, nodes, converted, nodeParameters );
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

		if( parameterName == "color" && ( shader->getName() == "quad_light" || shader->getName() == "skydome_light" || shader->getName() == "mesh_light" ) )
		{
			// In general, Arnold should be able to form a connection onto a parameter even if the
			// parameter already has a value.  Something weird happens with the "color" parameter
			// on "quad_light" and "skydome_light" though, where the connection is not evaluated
			// properly unless the parameter is reset first ( possibly due to some special importance
			// map building that needs to happen when a connection is made to the color parameter )
			AiNodeResetParameter( node, "color" );
		}

		const AtString parameterNameArnold( parameterName.c_str() );
		const uint8_t paramType = AiParamGetType(
			AiNodeEntryLookUpParameter(
				AiNodeGetNodeEntry( node ), parameterNameArnold
			)
		);

		if( paramType == AI_TYPE_NODE )
		{
			AiNodeSetPtr( node, parameterNameArnold, sourceNode );
		}
		else
		{
			string output = connection.source.name;
			const IECoreScene::Shader *sourceShader = shaderNetwork->getShader( connection.source.shader );
			if( boost::starts_with( sourceShader->getType(), "osl:" ) )
			{
				output = "param_" + output;
			}

			if( output == "out" && AiNodeEntryGetNumOutputs( AiNodeGetNodeEntry( sourceNode ) ) == 0 )
			{
				output = "";
			}
			AiNodeLinkOutput( sourceNode, output.c_str(), node, parameterName.c_str() );
		}
	}

	nodes.push_back( node );
	return node;
}

AtString g_name( "name" );
AtString g_lightBlockerNodeEntryName( "light_blocker" );

const std::vector<AtString> g_protectedLightParameters = {
	AtString( "matrix" ),
	AtString( "filters" ),
	AtString( "mesh" )
};

const std::vector<AtString> g_protectedLightFilterParameters = {
	AtString( "geometry_matrix" ),
};

// Similar to `AiNodeReset()`, but avoids resetting light parameters
// which we know to be unrelated to ShaderNetwork translation.
void resetNode( AtNode *node )
{
	const AtNodeEntry *nodeEntry = AiNodeGetNodeEntry( node );
	const bool isLight = AiNodeEntryGetType( nodeEntry ) == AI_NODE_LIGHT;
	const bool isShader = AiNodeEntryGetType( nodeEntry ) == AI_NODE_SHADER;
	const bool isLightFilter = isShader && AtString( AiNodeEntryGetName( nodeEntry ) ) == g_lightBlockerNodeEntryName;

	AtParamIterator *it = AiNodeEntryGetParamIterator( nodeEntry );
	while( !AiParamIteratorFinished( it ) )
	{
		const AtParamEntry *param = AiParamIteratorGetNext( it );
		const AtString name = AiParamGetName( param );

		if( name == g_name )
		{
			continue;
		}

		if(
			isLight &&
			std::find(
				g_protectedLightParameters.begin(),
				g_protectedLightParameters.end(),
				name
			) != g_protectedLightParameters.end()
		)
		{
			continue;
		}

		if(
			isLightFilter &&
			std::find(
				g_protectedLightFilterParameters.begin(),
				g_protectedLightFilterParameters.end(),
				name
			) != g_protectedLightFilterParameters.end()
		)
		{
			continue;
		}

		// We've seen cases where AiNodeResetParameter doesn't unlink
		// connections hence the call directly to AiNodeUnlink.
		AiNodeUnlink( node, name );
		AiNodeResetParameter( node, name );
	}
	AiParamIteratorDestroy( it );

	AtUserParamIterator *itUser = AiNodeGetUserParamIterator( node );
	while ( !AiUserParamIteratorFinished( itUser ) )
	{
		const AtUserParamEntry *param = AiUserParamIteratorGetNext( itUser );
		const char *name = AiUserParamGetName( param );
		AiNodeResetParameter( node, name );
	}
	AiUserParamIteratorDestroy( itUser );
}

template<typename T>
T parameterValue( const Shader *shader, InternedString parameterName, const T &defaultValue )
{
	if( auto d = shader->parametersData()->member<TypedData<T>>( parameterName ) )
	{
		return d->readable();
	}

	if constexpr( is_same_v<remove_cv_t<T>, Color3f> )
	{
		// Correction for USD files which author `float3` instead of `color3f`.
		// See `ShaderNetworkAlgoTest.testConvertUSDFloat3ToColor3f()`.
		if( auto d = shader->parametersData()->member<V3fData>( parameterName ) )
		{
			return d->readable();
		}
		// Conversion of Color4 to Color3, for cases like converting `UsdUVTexture.scale`
		// to `image.multiply`.
		if( auto d = shader->parametersData()->member<Color4fData>( parameterName ) )
		{
			const Color4f &c = d->readable();
			return Color3f( c[0], c[1], c[2] );
		}
	}
	else if constexpr( is_same_v<remove_cv_t<T>, string> )
	{
		// Support for USD `token`, which will be loaded as `InternedString`, but which
		// we want to translate to `string`.
		if( auto d = shader->parametersData()->member<InternedStringData>( parameterName ) )
		{
			return d->readable().string();
		}
	}

	return defaultValue;
}

ShaderNetworkPtr preprocessedNetwork( const IECoreScene::ShaderNetwork *shaderNetwork )
{
	ShaderNetworkPtr result = shaderNetwork->copy();
	/// \todo : pass in the actual OSL version.  We should be able to use a recent enough
	/// version of OSL that Arnold supports actual component connections, and we don't have
	/// to force the insertion of old OSL adapters.
	///
	/// While we're at it, if we can get onto recent enough Arnold, then we can connect to
	/// specific outputs, and can stop needing to duplicate shaders when more than 1 output
	/// is used.
	IECoreScene::ShaderNetworkAlgo::convertToOSLConventions( result.get(), 10900 );
	IECoreArnold::ShaderNetworkAlgo::convertUSDShaders( result.get() );

	/// Convert `quad_light` width and height, if needed.
	if( result->outputShader()->getName() == "quad_light" )
	{
		ShaderNetwork::Parameter outputParameter = result->getOutput();

		ShaderPtr newShader = result->getShader( outputParameter.shader )->copy();

		const auto verticesDataIt = newShader->parameters().find( "vertices" );
		if( verticesDataIt == newShader->parameters().end() )
		{
			float width = parameterValue<float>( newShader.get(), "width", 2.f );
			float height = parameterValue<float>( newShader.get(), "height", 2.f );

			newShader->parameters()["vertices"] = new V3fVectorData( {
				V3f( -width / 2, -height / 2, 0 ),
				V3f( -width / 2, height / 2 , 0 ),
				V3f( width / 2, height / 2, 0 ),
				V3f( width / 2, -height / 2, 0 )
			} );

			newShader->parameters().erase( "width" );
			newShader->parameters().erase( "height" );

			result->setShader( outputParameter.shader, std::move( newShader ) );
		}
	}

	return result;
}


} // namespace

namespace IECoreArnold
{

namespace ShaderNetworkAlgo
{

NodeParameter::NodeParameter( AtNode *node, AtString parameterName, AtString parameterValue )
	:	m_node( node ), m_parameterName( parameterName ), m_parameterValue( parameterValue )
{
}

void NodeParameter::updateParameter() const
{
	if( m_parameterValue == g_emptyArnoldString )
	{
		AiNodeResetParameter( m_node, m_parameterName );
	}
	else
	{
		if( AtNode *n = AiNodeLookUpByName( AiNodeGetUniverse( m_node ), m_parameterValue ) )
		{
			AiNodeSetPtr( m_node, m_parameterName, n );
		}
		else
		{
			AiNodeResetParameter( m_node, m_parameterName );
			msg(
				Msg::Warning, "NodeParameter",
				fmt::format( "{}.{} : Node \"{}\" not found", AiNodeGetName( m_node ), m_parameterName, m_parameterValue )
			);
		}
	}
}

std::vector<AtNode *> convert( const IECoreScene::ShaderNetwork *shaderNetwork, AtUniverse *universe, const std::string &name, std::vector<NodeParameter> &nodeParameters, const AtNode *parentNode )
{
	ConstShaderNetworkPtr network = preprocessedNetwork( shaderNetwork );

	ShaderMap converted;
	vector<AtNode *> result;
	const InternedString output = network->getOutput().shader;
	if( output.string().empty() )
	{
		msg( Msg::Warning, "IECoreArnold::ShaderNetworkAlgo", "Shader has no output" );
	}
	else
	{
		auto nodeCreator = [universe, parentNode]( const AtString &nodeType, const AtString &nodeName ) {
			return AiNode( universe, nodeType, nodeName, parentNode );
		};
		convertWalk( network->getOutput(), network.get(), name, nodeCreator, result, converted, nodeParameters );
		for( const auto &kv : network->outputShader()->blindData()->readable() )
		{
			ParameterAlgo::setParameter( result.back(), AtString( kv.first.c_str() ), kv.second.get() );
		}
	}
	return result;
}

std::vector<AtNode *> convert( const IECoreScene::ShaderNetwork *shaderNetwork, AtUniverse *universe, const std::string &name, const AtNode *parentNode )
{
	std::vector<NodeParameter> nodeParameters;
	auto result = convert( shaderNetwork, universe, name, nodeParameters, parentNode );
	if( nodeParameters.size() )
	{
		msg( Msg::Warning, "IECoreArnold::ShaderNetworkAlgo", fmt::format( "{} NodeParameter{} ignored", nodeParameters.size(), nodeParameters.size() > 1 ? "s" : "" ) );
	}
	return result;
}

bool update( std::vector<AtNode *> &nodes, std::vector<NodeParameter> &nodeParameters, const IECoreScene::ShaderNetwork *shaderNetwork )
{
	if( !nodes.size() )
	{
		return false;
	}

	ConstShaderNetworkPtr network = preprocessedNetwork( shaderNetwork );

	AtUniverse *universe = AiNodeGetUniverse( nodes.back() );
	AtNode *parentNode = AiNodeGetParent( nodes.back() );
	const std::string &name = AiNodeGetName( nodes.back() );

	boost::unordered_map<AtString, AtNode *, AtStringHash> originalNodes;
	for( const auto &n : nodes )
	{
		originalNodes[AtString(AiNodeGetName(n))] = n;
	}
	std::unordered_set<AtNode *> reusedNodes;
	nodes.clear();

	auto nodeCreator = [universe, parentNode, &originalNodes, &reusedNodes]( const AtString &nodeType, const AtString &nodeName ) {
		auto it = originalNodes.find( nodeName );
		if( it != originalNodes.end() )
		{
			if( AtString( AiNodeEntryGetName( AiNodeGetNodeEntry( it->second ) ) ) == nodeType )
			{
				// Reuse original node
				AtNode *node = it->second;
				originalNodes.erase( it );
				reusedNodes.insert( node );
				resetNode( node );
				return node;
			}
			else
			{
				// Can't reuse original node. Delete it so that we
				// can reuse the name in `AiNode()` below.
				AiNodeDestroy( it->second );
				originalNodes.erase( it );
			}
		}
		return AiNode( universe, nodeType, nodeName, parentNode );
	};

	ShaderMap converted;
	nodeParameters.clear();
	convertWalk( network->getOutput(), network.get(), name, nodeCreator, nodes, converted, nodeParameters );

	for( const auto &n : originalNodes )
	{
		AiNodeDestroy( n.second );
	}

	return nodes.size() && reusedNodes.count( nodes.back() );
}

bool update( std::vector<AtNode *> &nodes, const IECoreScene::ShaderNetwork *shaderNetwork )
{
	std::vector<NodeParameter> nodeParameters;
	const bool result = update( nodes, nodeParameters, shaderNetwork );
	if( nodeParameters.size() )
	{
		msg( Msg::Warning, "IECoreArnold::ShaderNetworkAlgo", fmt::format( "{} NodeParameter{} ignored", nodeParameters.size(), nodeParameters.size() > 1 ? "s" : "" ) );
	}
	return result;
}

} // namespace ShaderNetworkAlgo

} // namespace IECoreArnold

//////////////////////////////////////////////////////////////////////////
// USD conversion code
//////////////////////////////////////////////////////////////////////////

namespace
{

// Traits class to handle the GeometricTypedData fiasco.
template<typename T>
struct DataTraits
{

	using DataType = IECore::TypedData<T>;

};

template<typename T>
struct DataTraits<Vec2<T> >
{

	using DataType = IECore::GeometricTypedData<Vec2<T>>;

};

template<typename T>
struct DataTraits<Vec3<T> >
{

	using DataType = IECore::GeometricTypedData<Vec3<T>>;

};

Color3f blackbody( float kelvins )
{
	// Table borrowed from `UsdLuxBlackbodyTemperatureAsRgb()`, which in
	// turn is borrowed from Colour Rendering of Spectra by John Walker.
	static SplinefColor3f g_spline(
		CubicBasisf::catmullRom(),
		{
			{  1000.0f, Color3f( 1.000000f, 0.027490f, 0.000000f ) },
			{  1000.0f, Color3f( 1.000000f, 0.027490f, 0.000000f ) },
			{  1500.0f, Color3f( 1.000000f, 0.149664f, 0.000000f ) },
			{  2000.0f, Color3f( 1.000000f, 0.256644f, 0.008095f ) },
			{  2500.0f, Color3f( 1.000000f, 0.372033f, 0.067450f ) },
			{  3000.0f, Color3f( 1.000000f, 0.476725f, 0.153601f ) },
			{  3500.0f, Color3f( 1.000000f, 0.570376f, 0.259196f ) },
			{  4000.0f, Color3f( 1.000000f, 0.653480f, 0.377155f ) },
			{  4500.0f, Color3f( 1.000000f, 0.726878f, 0.501606f ) },
			{  5000.0f, Color3f( 1.000000f, 0.791543f, 0.628050f ) },
			{  5500.0f, Color3f( 1.000000f, 0.848462f, 0.753228f ) },
			{  6000.0f, Color3f( 1.000000f, 0.898581f, 0.874905f ) },
			{  6500.0f, Color3f( 1.000000f, 0.942771f, 0.991642f ) },
			{  7000.0f, Color3f( 0.906947f, 0.890456f, 1.000000f ) },
			{  7500.0f, Color3f( 0.828247f, 0.841838f, 1.000000f ) },
			{  8000.0f, Color3f( 0.765791f, 0.801896f, 1.000000f ) },
			{  8500.0f, Color3f( 0.715255f, 0.768579f, 1.000000f ) },
			{  9000.0f, Color3f( 0.673683f, 0.740423f, 1.000000f ) },
			{  9500.0f, Color3f( 0.638992f, 0.716359f, 1.000000f ) },
			{ 10000.0f, Color3f( 0.609681f, 0.695588f, 1.000000f ) },
			{ 10000.0f, Color3f( 0.609681f, 0.695588f, 1.000000f ) },
		}
	);

	Color3f c = g_spline( kelvins );
	c /= c.dot( V3f( 0.2126f, 0.7152f, 0.0722f ) ); // Normalise luminance
	return Color3f( max( c[0], 0.0f ), max( c[1], 0.0f ), max( c[2], 0.0f ) );
}

template<typename T>
void transferUSDParameter( ShaderNetwork *network, InternedString shaderHandle, const Shader *usdShader, InternedString usdName, Shader *shader, InternedString name, const T &defaultValue )
{
	shader->parameters()[name] = new typename DataTraits<T>::DataType( parameterValue( usdShader, usdName, defaultValue ) );

	if( ShaderNetwork::Parameter input = network->input( { shaderHandle, usdName } ) )
	{
		network->addConnection( { input, { shaderHandle, name } } );
		network->removeConnection( { input, { shaderHandle, usdName } } );
	}
}

const InternedString g_aParameter( "a" );
const InternedString g_angleParameter( "angle" );
const InternedString g_attributeParameter( "attribute" );
const InternedString g_biasParameter( "bias" );
const InternedString g_bParameter( "b" );
const InternedString g_baseColorParameter( "base_color" );
const InternedString g_bottomParameter( "bottom" );
const InternedString g_castShadowsParameter( "cast_shadows" );
const InternedString g_clearcoatParameter( "clearcoat" );
const InternedString g_clearcoatRoughnessParameter( "clearcoatRoughness" );
const InternedString g_coatParameter( "coat" );
const InternedString g_coatRoughnessParameter( "coat_roughness" );
const InternedString g_colorParameter( "color" );
const InternedString g_colorModeParameter( "color_mode" );
const InternedString g_colorSpaceParameter( "color_space" );
const InternedString g_colorTemperatureParameter( "colorTemperature" );
const InternedString g_colorToSignedParameter( "color_to_signed" );
const InternedString g_coneAngleParameter( "cone_angle" );
const InternedString g_cosinePowerParameter( "cosine_power" );
const InternedString g_defaultParameter( "default" );
const InternedString g_diffuseParameter( "diffuse" );
const InternedString g_diffuseColorParameter( "diffuseColor" );
const InternedString g_emissionParameter( "emission" );
const InternedString g_emissiveColorParameter( "emissiveColor" );
const InternedString g_emissionColorParameter( "emission_color" );
const InternedString g_enableColorTemperatureParameter( "enableColorTemperature" );
const InternedString g_exposureParameter( "exposure" );
const InternedString g_fallbackParameter( "fallback" );
const InternedString g_fileParameter( "file" );
const InternedString g_filenameParameter( "filename" );
const InternedString g_formatParameter( "format" );
const InternedString g_gParameter( "g" );
const InternedString g_heightParameter( "height" );
const InternedString g_ignoreMissingTexturesParameter( "ignore_missing_textures" );
const InternedString g_inParameter( "in" );
const InternedString g_inputParameter( "input" );
const InternedString g_input1Parameter( "input1" );
const InternedString g_input2Parameter( "input2" );
const InternedString g_input2RParameter( "input2.r" );
const InternedString g_input2GParameter( "input2.g" );
const InternedString g_input2BParameter( "input2.b" );
const InternedString g_intensityParameter( "intensity" );
const InternedString g_iorParameter( "ior" );
const InternedString g_lengthParameter( "length" );
const InternedString g_matrixParameter( "matrix" );
const InternedString g_metallicParameter( "metallic" );
const InternedString g_metalnessParameter( "metalness" );
const InternedString g_missingTextureColorParameter( "missing_texture_color" );
const InternedString g_multiplyParameter( "multiply" );
const InternedString g_normalizeParameter( "normalize" );
const InternedString g_normalParameter( "normal" );
const InternedString g_offsetParameter( "offset" );
const InternedString g_opacityParameter( "opacity" );
const InternedString g_opacityThresholdParameter( "opacityThreshold" );
const InternedString g_penumbraAngleParameter( "penumbra_angle" );
const InternedString g_rParameter( "r" );
const InternedString g_radiusParameter( "radius" );
const InternedString g_roughnessParameter( "roughness" );
const InternedString g_rotationParameter( "rotation" );
const InternedString g_scaleParameter( "scale" );
const InternedString g_shadeModeParameter( "shade_mode" );
const InternedString g_shadowEnableParameter( "shadow:enable" );
const InternedString g_shadowColorParameter( "shadow:color" );
const InternedString g_shadowColorArnoldParameter( "shadow_color" );
const InternedString g_shapingConeAngleParameter( "shaping:cone:angle" );
const InternedString g_shapingConeSoftnessParameter( "shaping:cone:softness" );
const InternedString g_shapingSoftnessParameter( "shaping:softness" );
const InternedString g_sourceColorSpaceParameter( "sourceColorSpace" );
const InternedString g_specularParameter( "specular" );
const InternedString g_specularColorParameter( "specularColor" );
const InternedString g_specularColorArnoldParameter( "specular_color" );
const InternedString g_specularIORParameter( "specular_IOR" );
const InternedString g_specularRoughnessParameter( "specular_roughness" );
const InternedString g_stParameter( "st" );
const InternedString g_sWrapParameter( "swrap" );
const InternedString g_testParameter( "test" );
const InternedString g_textureFileParameter( "texture:file" );
const InternedString g_textureFormatParameter( "texture:format" );
const InternedString g_topParameter( "top" );
const InternedString g_translationParameter( "translation" );
const InternedString g_treatAsLineParameter( "treatAsLine" );
const InternedString g_treatAsPointParameter( "treatAsPoint" );
const InternedString g_tWrapParameter( "twrap" );
const InternedString g_useSpecularWorkflowParameter( "useSpecularWorkflow" );
const InternedString g_uvCoordsParameter( "uvcoords" );
const InternedString g_uvSetParameter( "uvset" );
const InternedString g_varnameParameter( "varname" );
const InternedString g_verticesParameter( "vertices" );
const InternedString g_widthParameter( "width" );
const InternedString g_wrapSParameter( "wrapS" );
const InternedString g_wrapTParameter( "wrapT" );

void transferUSDLightParameters( ShaderNetwork *network, InternedString shaderHandle, const Shader *usdShader, Shader *shader )
{
	Color3f color = parameterValue( usdShader, g_colorParameter, Color3f( 1 ) );
	if( parameterValue( usdShader, g_enableColorTemperatureParameter, false ) )
	{
		color *= blackbody( parameterValue( usdShader, g_colorTemperatureParameter, 6500.0f ) );
	}
	shader->parameters()[g_colorParameter] = new Color3fData( color );

	transferUSDParameter( network, shaderHandle, usdShader, g_diffuseParameter, shader, g_diffuseParameter, 1.0f );
	transferUSDParameter( network, shaderHandle, usdShader, g_exposureParameter, shader, g_exposureParameter, 0.0f );
	transferUSDParameter( network, shaderHandle, usdShader, g_intensityParameter, shader, g_intensityParameter, 1.0f );
	transferUSDParameter( network, shaderHandle, usdShader, g_normalizeParameter, shader, g_normalizeParameter, false );
	transferUSDParameter( network, shaderHandle, usdShader, g_specularParameter, shader, g_specularParameter, 1.0f );

	transferUSDParameter( network, shaderHandle, usdShader, g_shadowEnableParameter, shader, g_castShadowsParameter, true );
	transferUSDParameter( network, shaderHandle, usdShader, g_shadowColorParameter, shader, g_shadowColorArnoldParameter, Color3f( 0 ) );
}

void transferUSDShapingParameters( ShaderNetwork *network, InternedString shaderHandle, const Shader *usdShader, Shader *shader )
{
	if( auto d = usdShader->parametersData()->member<FloatData>( g_shapingConeAngleParameter ) )
	{
		shader->setName( "spot_light" );
		shader->parameters()[g_coneAngleParameter] = new FloatData( d->readable() * 2.0f );
		// USD docs don't currently specify any semantics for `shaping:cone:softness`, but we assume
		// the semantics documented for RenderMan's PxrSphereLight, where it's basically specifying
		// a penumbra as a 0-1 proportion of the cone. Relevant conversations on usd-interest :
		//
		// - https://groups.google.com/u/1/g/usd-interest/c/A6bc4OZjSB0/m/hwUL7Wf1AwAJ, in
		//   which the opportunity to define semantics is declined.
		// - https://groups.google.com/u/1/g/usd-interest/c/Ybe4aroAKbc/m/0Ui3DKMyCgAJ, in
		//   which folks take their best guess.
		const float softness = parameterValue( usdShader, g_shapingConeSoftnessParameter, 0.0f );
		if( softness > 1.0 )
		{
			// Houdini apparently has (or had?) its own interpretation of softness, with the "bar scene"
			// containing lights with an angle of 20 degrees and a softness of 60! We have no idea how
			// to interpret that, so punt for now.
			/// \todo Hopefully things get more standardised and we can remove this, because the RenderMan
			/// docs do imply that values above one are allowed.
			IECore::msg( IECore::Msg::Warning, "transferUSDShapingParameters", "Ignoring `shaping:cone:softness` as it is greater than 1" );
		}
		else
		{
			shader->parameters()[g_penumbraAngleParameter] = new FloatData( d->readable() * 2.0f * softness );
		}
		// Same here.
		shader->parameters()[g_cosinePowerParameter] = new FloatData( parameterValue( usdShader, g_shapingSoftnessParameter, 0.0f ) );
	}
}

// Should be called after `transferUSDLightParameters()`, as it needs to examine
// the transferred `color` parameter.
void transferUSDTextureFile( ShaderNetwork *network, InternedString shaderHandle, const Shader *usdShader, const Shader *shader )
{
	const string textureFile = parameterValue( usdShader, g_textureFileParameter, string() );
	if( !textureFile.empty() )
	{
		ShaderPtr imageShader = new Shader( "image" );
		imageShader->parameters()[g_filenameParameter] = new StringData( textureFile );
		const InternedString imageHandle = network->addShader( shaderHandle.string() + "Image", std::move( imageShader ) );

		const Color3f color = parameterValue( shader, g_colorParameter, Color3f( 1 ) );
		if( color != Color3f( 1 ) )
		{
			// Multiply image with color
			ShaderPtr multiplyShader = new Shader( "multiply" );
			multiplyShader->parameters()[g_input2Parameter] = new Color3fData( color );
			const InternedString multiplyHandle = network->addShader( shaderHandle.string() + "Multiply", std::move( multiplyShader ) );
			network->addConnection( ShaderNetwork::Connection( multiplyHandle, { shaderHandle, g_colorParameter } ) );
			network->addConnection( ShaderNetwork::Connection( imageHandle, { multiplyHandle, g_input1Parameter } ) );
		}
		else
		{
			// Connect image directly
			network->addConnection( ShaderNetwork::Connection( imageHandle, { shaderHandle, g_colorParameter } ) );
		}
	}
}

template<typename VecType, typename ColorType>
void convertVecToColor( Shader *shader, InternedString parameterName )
{
	const VecType v = parameterValue( shader, parameterName, VecType( 0 ) );
	ColorType c;
	for( size_t i = 0; i < ColorType::dimensions(); ++i )
	{
		c[i] = i < VecType::dimensions() ? v[i] : 0.0f;
	}

	shader->parameters()[parameterName] = new typename DataTraits<ColorType>::DataType( c );
}

void removeInput( ShaderNetwork *network, const ShaderNetwork::Parameter &parameter )
{
	if( auto i = network->input( parameter ) )
	{
		network->removeConnection( { i, parameter } );
	}
}

void replaceUSDShader( ShaderNetwork *network, InternedString handle, ShaderPtr &&newShader )
{
	// Replace original shader with the new.
	network->setShader( handle, std::move( newShader ) );

	// Convert output connections as necessary. Our Arnold shaders
	// all have a single output, which does not need to be named as
	// the source of a connection. We only need to keep the source
	// name if it refers to a subcomponent of the output.

	// Iterating over a copy because we will modify the range during iteration.
	ShaderNetwork::ConnectionRange range = network->outputConnections( handle );
	vector<ShaderNetwork::Connection> outputConnections( range.begin(), range.end() );
	for( auto &c : outputConnections )
	{
		if( c.source.name != g_rParameter && c.source.name != g_gParameter && c.source.name != g_bParameter && c.source.name != g_aParameter )
		{
			network->removeConnection( c );
			c.source.name = InternedString();
			network->addConnection( c );
		}
	}
}

void convertUSDUVTextures( ShaderNetwork *network )
{
	for( const auto &[handle, shader] : network->shaders() )
	{
		if( shader->getName() != "UsdUVTexture" )
		{
			continue;
		}

		ShaderPtr imageShader = new Shader( "image", "ai:shader" );
		transferUSDParameter( network, handle, shader.get(), g_fileParameter, imageShader.get(), g_filenameParameter, string() );
		transferUSDParameter( network, handle, shader.get(), g_sourceColorSpaceParameter, imageShader.get(), g_colorSpaceParameter, string( "auto" ) );
		imageShader->parameters()[g_ignoreMissingTexturesParameter] = new BoolData( true );

		using NamePair = pair<InternedString, InternedString>;
		for( const auto &[usdName, name] : { NamePair( g_wrapSParameter, g_sWrapParameter ), NamePair( g_wrapTParameter, g_tWrapParameter ) } )
		{
			string mode = parameterValue( shader.get(), usdName, string( "useMetadata" ) );
			if( mode == "useMetadata" )
			{
				mode = "file";
			}
			else if( mode == "repeat" )
			{
				mode = "periodic";
			}
			imageShader->parameters()[name] = new StringData( mode );
		}

		transferUSDParameter( network, handle, shader.get(), g_fallbackParameter, imageShader.get(), g_missingTextureColorParameter, Color4f( 0, 0, 0, 1 ) );
		transferUSDParameter( network, handle, shader.get(), g_scaleParameter, imageShader.get(), g_multiplyParameter, Color3f( 1 ) );
		transferUSDParameter( network, handle, shader.get(), g_biasParameter, imageShader.get(), g_offsetParameter, Color3f( 0 ) );

		// Arnold gives up on proper texturing filtering if the `image.uvcoords`
		// input is used. So do what we can to avoid that, by converting a
		// `UsdPrimvarReader_float2` input into a simple `uvset` parameter.

		if( auto input = network->input( { handle, g_stParameter } ) )
		{
			const Shader *inputShader = network->getShader( input.shader );
			if( inputShader->getName() == "UsdPrimvarReader_float2" )
			{
				const string st = parameterValue( inputShader, g_varnameParameter, string() );
				imageShader->parameters()[g_uvSetParameter] = new StringData( st == "st" ? "" : st );
				network->removeConnection( { input, { handle, g_stParameter } } );
			}
			else
			{
				transferUSDParameter( network, handle, shader.get(), g_stParameter, imageShader.get(), g_uvCoordsParameter, V2f( 0 ) );
			}
		}

		replaceUSDShader( network, handle, std::move( imageShader ) );
	}
}

} // namespace

void IECoreArnold::ShaderNetworkAlgo::convertUSDShaders( ShaderNetwork *shaderNetwork )
{
	// Must convert these first, before we convert the connected
	// UsdPrimvarReader inputs.
	convertUSDUVTextures( shaderNetwork );

	for( const auto &[handle, shader] : shaderNetwork->shaders() )
	{
		ShaderPtr newShader;
		if( shader->getName() == "UsdPreviewSurface" )
		{
			newShader = new Shader( "standard_surface" );

			// Easy stuff with a one-to-one correspondence between `UsdPreviewSurface` and `standard_surface`.

			transferUSDParameter( shaderNetwork, handle, shader.get(), g_diffuseColorParameter, newShader.get(),g_baseColorParameter, Color3f( 0.18 ) );
			transferUSDParameter( shaderNetwork, handle, shader.get(), g_roughnessParameter, newShader.get(), g_specularRoughnessParameter, 0.5f );
			transferUSDParameter( shaderNetwork, handle, shader.get(), g_clearcoatParameter, newShader.get(), g_coatParameter, 0.0f );
			transferUSDParameter( shaderNetwork, handle, shader.get(), g_clearcoatRoughnessParameter, newShader.get(), g_coatRoughnessParameter, 0.01f );
			transferUSDParameter( shaderNetwork, handle, shader.get(), g_iorParameter, newShader.get(), g_specularIORParameter, 1.5f );

			// Emission. UsdPreviewSurface only has `emissiveColor`, which we transfer to `emission_color`. But then
			// we need to turn on Arnold's `emission` to that the `emission_color` is actually used.

			transferUSDParameter( shaderNetwork, handle, shader.get(), g_emissiveColorParameter, newShader.get(), g_emissionColorParameter, Color3f( 0 ) );
			const bool hasEmission =
				shaderNetwork->input( { handle, g_emissionColorParameter } ) ||
				parameterValue( newShader.get(), g_emissionColorParameter, Color3f( 0 ) ) != Color3f( 0 );
			;
			newShader->parameters()[g_emissionParameter] = new FloatData( hasEmission ? 1.0f : 0.0f );

			// Specular.

			if( parameterValue<int>( shader.get(), g_useSpecularWorkflowParameter, 0 ) )
			{
				// > Note : Not completely equivalent to USD's specification.
				// USD's colour is for the facing angle, and the edge colour is
				// always white. But Arnold's is a tint applied uniformly
				// everywhere, so we use a fallback value of `1.0` rather than
				// the `0.0` from the USD spec.
				transferUSDParameter( shaderNetwork, handle, shader.get(), g_specularColorParameter, newShader.get(), g_specularColorArnoldParameter, Color3f( 1.0f ) );
			}
			else
			{
				transferUSDParameter( shaderNetwork, handle, shader.get(), g_metallicParameter, newShader.get(), g_metalnessParameter, 0.0f );
			}

			removeInput( shaderNetwork, { handle, g_metallicParameter } );
			removeInput( shaderNetwork, { handle, g_specularColorParameter } );

			// Opacity. This is a float in USD and a colour in Arnold. And USD
			// has a funky `opacityThreshold` thing too, that we need to implement
			// with a little compare/multiply network.

			float opacity = parameterValue( shader.get(), g_opacityParameter, 1.0f );
			const float opacityThreshold = parameterValue( shader.get(), g_opacityThresholdParameter, 0.0f );
			if( const ShaderNetwork::Parameter opacityInput = shaderNetwork->input( { handle, g_opacityParameter } ) )
			{
				if( opacityThreshold != 0.0f )
				{
					ShaderPtr compareShader = new Shader( "compare" );
					compareShader->parameters()[g_input2Parameter] = new FloatData( opacityThreshold );
					compareShader->parameters()[g_testParameter] = new StringData( ">" );
					const InternedString compareHandle = shaderNetwork->addShader( handle.string() + "OpacityCompare", std::move( compareShader ) );
					shaderNetwork->addConnection( ShaderNetwork::Connection( opacityInput, { compareHandle, g_input1Parameter } ) );
					ShaderPtr multiplyShader = new Shader( "multiply" );
					const InternedString multiplyHandle = shaderNetwork->addShader( handle.string() + "OpacityMultiply", std::move( multiplyShader ) );
					shaderNetwork->addConnection( ShaderNetwork::Connection( opacityInput, { multiplyHandle, g_input1Parameter } ) );
					shaderNetwork->addConnection( ShaderNetwork::Connection( compareHandle, { multiplyHandle, g_input2RParameter } ) );
					shaderNetwork->addConnection( ShaderNetwork::Connection( compareHandle, { multiplyHandle, g_input2GParameter } ) );
					shaderNetwork->addConnection( ShaderNetwork::Connection( compareHandle, { multiplyHandle, g_input2BParameter } ) );
					shaderNetwork->removeConnection( ShaderNetwork::Connection( opacityInput, { handle, g_opacityParameter } ) );
					shaderNetwork->addConnection( ShaderNetwork::Connection( multiplyHandle, { handle, g_opacityParameter } ) );
				}
			}
			else
			{
				opacity = opacity > opacityThreshold ? opacity : 0.0f;
			}

			newShader->parameters()[g_opacityParameter] = new Color3fData( Color3f( opacity ) );

			// Normal

			if( const ShaderNetwork::Parameter normalInput = shaderNetwork->input( { handle, g_normalParameter } ) )
			{
				ShaderPtr normalShader = new Shader( "normal_map" );
				normalShader->parameters()[g_colorToSignedParameter] = new BoolData( false );
				const InternedString normalHandle = shaderNetwork->addShader( handle.string() + "Normal", std::move( normalShader ) );
				shaderNetwork->addConnection( ShaderNetwork::Connection( normalInput, { normalHandle, g_inputParameter } ) );
				shaderNetwork->removeConnection( ShaderNetwork::Connection( normalInput, { handle, g_normalParameter } ) );
				shaderNetwork->addConnection( ShaderNetwork::Connection( normalHandle, { handle, g_normalParameter } ) );
			}
		}
		else if( shader->getName() == "UsdTransform2d" )
		{
			newShader = new Shader( "matrix_multiply_vector" );
			transferUSDParameter( shaderNetwork, handle, shader.get(), g_inParameter, newShader.get(), g_inputParameter, string() );
			const V2f t = parameterValue( shader.get(), g_translationParameter, V2f( 0 ) );
			const float r = parameterValue( shader.get(), g_rotationParameter, 0.0f );
			const V2f s = parameterValue( shader.get(), g_scaleParameter, V2f( 1 ) );
			M44f m;
			m.translate( V3f( t.x, t.y, 0 ) );
			m.rotate( V3f( 0, 0, IECore::degreesToRadians( r ) ) );
			m.scale( V3f( s.x, s.y, 1 ) );
			newShader->parameters()[g_matrixParameter] = new M44fData( m );

		}
		else if( shader->getName() == "UsdPrimvarReader_float" )
		{
			newShader = new Shader( "user_data_float" );
			transferUSDParameter( shaderNetwork, handle, shader.get(), g_varnameParameter, newShader.get(), g_attributeParameter, string() );
			transferUSDParameter( shaderNetwork, handle, shader.get(), g_fallbackParameter, newShader.get(), g_defaultParameter, 0.0f );
		}
		else if( shader->getName() == "UsdPrimvarReader_float2" )
		{
			if( parameterValue<string>( shader.get(), g_varnameParameter, "" ) == "st" )
			{
				// Default texture coordinates. These aren't accessible from a `user_data_rgb` shader,
				// so we must use a `utility` shader instead.
				newShader = new Shader( "utility" );
				newShader->parameters()[g_colorModeParameter] = new StringData( "uv" );
				newShader->parameters()[g_shadeModeParameter] = new StringData( "flat" );
			}
			else
			{
				newShader = new Shader( "user_data_rgb" );
				transferUSDParameter( shaderNetwork, handle, shader.get(), g_varnameParameter, newShader.get(), g_attributeParameter, string() );
				transferUSDParameter( shaderNetwork, handle, shader.get(), g_fallbackParameter, newShader.get(), g_defaultParameter, V2f( 0 ) );
				convertVecToColor<V2f, Color3f>( newShader.get(), g_defaultParameter );
			}
		}
		else if(
			shader->getName() == "UsdPrimvarReader_float3" ||
			shader->getName() == "UsdPrimvarReader_normal" ||
			shader->getName() == "UsdPrimvarReader_point" ||
			shader->getName() == "UsdPrimvarReader_vector"
		)
		{
			newShader = new Shader( "user_data_rgb" );
			transferUSDParameter( shaderNetwork, handle, shader.get(), g_varnameParameter, newShader.get(), g_attributeParameter, string() );
			transferUSDParameter( shaderNetwork, handle, shader.get(), g_fallbackParameter, newShader.get(), g_defaultParameter, V3f( 0 ) );
			convertVecToColor<V3f, Color3f>( newShader.get(), g_defaultParameter );
		}
		else if( shader->getName() == "UsdPrimvarReader_float4" )
		{
			newShader = new Shader( "user_data_rgba" );
			transferUSDParameter( shaderNetwork, handle, shader.get(), g_varnameParameter, newShader.get(), g_attributeParameter, string() );
			transferUSDParameter( shaderNetwork, handle, shader.get(), g_fallbackParameter, newShader.get(), g_defaultParameter, Color4f( 0 ) );
		}
		else if( shader->getName() == "UsdPrimvarReader_int" )
		{
			newShader = new Shader( "user_data_int" );
			transferUSDParameter( shaderNetwork, handle, shader.get(), g_varnameParameter, newShader.get(), g_attributeParameter, string() );
			transferUSDParameter( shaderNetwork, handle, shader.get(), g_fallbackParameter, newShader.get(), g_defaultParameter, 0 );
		}
		else if( shader->getName() == "UsdPrimvarReader_string" )
		{
			newShader = new Shader( "user_data_string" );
			transferUSDParameter( shaderNetwork, handle, shader.get(), g_varnameParameter, newShader.get(), g_attributeParameter, string() );
			transferUSDParameter( shaderNetwork, handle, shader.get(), g_fallbackParameter, newShader.get(), g_defaultParameter, string() );
		}
		else if( shader->getName() == "SphereLight" )
		{
			newShader = new Shader( "point_light", "ai:light" );
			transferUSDLightParameters( shaderNetwork, handle, shader.get(), newShader.get() );
			transferUSDShapingParameters( shaderNetwork, handle, shader.get(), newShader.get() );
			transferUSDParameter( shaderNetwork, handle, shader.get(), g_radiusParameter, newShader.get(), g_radiusParameter, 0.5f );
			if( parameterValue( shader.get(), g_treatAsPointParameter, false ) )
			{
				newShader->parameters()[g_radiusParameter] = new FloatData( 0.0 );
				newShader->parameters()[g_normalizeParameter] = new BoolData( true );
			}
		}
		else if( shader->getName() == "DiskLight" )
		{
			newShader = new Shader( "disk_light", "ai:light" );
			transferUSDLightParameters( shaderNetwork, handle, shader.get(), newShader.get() );
			transferUSDShapingParameters( shaderNetwork, handle, shader.get(), newShader.get() );
			transferUSDParameter( shaderNetwork, handle, shader.get(), g_radiusParameter, newShader.get(), g_radiusParameter, 0.5f );
		}
		else if( shader->getName() == "CylinderLight" )
		{
			newShader = new Shader( "cylinder_light", "ai:light" );
			transferUSDLightParameters( shaderNetwork, handle, shader.get(), newShader.get() );
			transferUSDShapingParameters( shaderNetwork, handle, shader.get(), newShader.get() );
			transferUSDParameter( shaderNetwork, handle, shader.get(), g_radiusParameter, newShader.get(), g_radiusParameter, 0.5f );
			const float length = parameterValue( shader.get(), g_lengthParameter, 1.0f );
			// From USD schema : "The cylinder is centered at the origin and has its major axis on the X axis"
			newShader->parameters()[g_topParameter] = new V3fData( V3f( length/2, 0, 0 ) );
			newShader->parameters()[g_bottomParameter] = new V3fData( V3f( -length/2, 0, 0 ) );
			if( parameterValue( shader.get(), g_treatAsLineParameter, false ) )
			{
				// Should be 0.0, but that triggers an Arnold bug that loses the
				// shape of the cylinder completely.
				newShader->parameters()[g_radiusParameter] = new FloatData( 0.001 );
				newShader->parameters()[g_normalizeParameter] = new BoolData( true );
			}
		}
		else if( shader->getName() == "DistantLight" )
		{
			newShader = new Shader( "distant_light", "ai:light" );
			transferUSDLightParameters( shaderNetwork, handle, shader.get(), newShader.get() );
			transferUSDShapingParameters( shaderNetwork, handle, shader.get(), newShader.get() );
			transferUSDParameter( shaderNetwork, handle, shader.get(), g_angleParameter, newShader.get(), g_angleParameter, 0.53f );
		}
		else if( shader->getName() == "DomeLight" )
		{
			newShader = new Shader( "skydome_light", "ai:light" );
			transferUSDLightParameters( shaderNetwork, handle, shader.get(), newShader.get() );
			transferUSDTextureFile( shaderNetwork, handle, shader.get(), newShader.get() );
			string format = parameterValue( shader.get(), g_textureFormatParameter, string( "automatic" ) );
			if( format == "mirroredBall" )
			{
				format = "mirrored_ball";
			}
			else if( format != "angular" && format != "latlong" )
			{
				IECore::msg( IECore::Msg::Warning, "convertUSDShaders", fmt::format( "Unsupported value \"{}\" for DomeLight.format", format ) );
				format = "latlong";
			}
			newShader->parameters()[g_formatParameter] = new StringData( format );
		}
		else if( shader->getName() == "RectLight" )
		{
			newShader = new Shader( "quad_light", "ai:light" );
			transferUSDLightParameters( shaderNetwork, handle, shader.get(), newShader.get() );
			const float width = parameterValue( shader.get(), g_widthParameter, 1.0f );
			const float height = parameterValue( shader.get(), g_heightParameter, 1.0f );
			newShader->parameters()[g_verticesParameter] = new V3fVectorData( {
				V3f( width / 2, -height / 2, 0 ),
				V3f( -width / 2, -height / 2, 0 ),
				V3f( -width / 2, height / 2, 0 ),
				V3f( width / 2, height / 2, 0 )
			} );
			transferUSDTextureFile( shaderNetwork, handle, shader.get(), newShader.get() );
		}

		if( newShader )
		{
			replaceUSDShader( shaderNetwork, handle, std::move( newShader ) );
		}
	}

	IECoreScene::ShaderNetworkAlgo::removeUnusedShaders( shaderNetwork );
}
