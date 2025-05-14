//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
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

#include "IECoreRenderMan/ShaderNetworkAlgo.h"

#include "ParamListAlgo.h"

#include "IECoreScene/ShaderNetworkAlgo.h"

#include "IECore/DataAlgo.h"
#include "IECore/LRUCache.h"
#include "IECore/MessageHandler.h"
#include "IECore/SearchPath.h"

#include "OSL/oslquery.h"

#include "boost/algorithm/string.hpp"
#include "boost/container/flat_map.hpp"
#include "boost/property_tree/xml_parser.hpp"

#include "fmt/format.h"

#include <regex>
#include <unordered_set>

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace IECoreRenderMan;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

struct ShaderInfo
{
	riley::ShadingNode::Type type = riley::ShadingNode::Type::k_Invalid;
	using ParameterTypeMap = std::unordered_map<RtUString, pxrcore::DataType>;
	ParameterTypeMap parameterTypes;
};

using ConstShaderInfoPtr = std::shared_ptr<const ShaderInfo>;

void loadParameterTypes( const boost::property_tree::ptree &tree, ShaderInfo::ParameterTypeMap &typeMap )
{
	for( const auto &child : tree )
	{
		if( child.first == "param" )
		{
			const RtUString name( child.second.get<string>( "<xmlattr>.name" ).c_str() );
			const string type = child.second.get<string>( "<xmlattr>.type" );
			if( type == "int" )
			{
				typeMap[name] = pxrcore::DataType::k_integer;
			}
			else if( type == "float" )
			{
				typeMap[name] = pxrcore::DataType::k_float;
			}
			else if( type == "color" )
			{
				typeMap[name] = pxrcore::DataType::k_color;
			}
			else if( type == "point" )
			{
				typeMap[name] = pxrcore::DataType::k_point;
			}
			else if( type == "vector" )
			{
				typeMap[name] = pxrcore::DataType::k_vector;
			}
			else if( type == "normal" )
			{
				typeMap[name] = pxrcore::DataType::k_normal;
			}
			else if( type == "matrix" )
			{
				typeMap[name] = pxrcore::DataType::k_matrix;
			}
			else if( type == "string" )
			{
				typeMap[name] = pxrcore::DataType::k_string;
			}
			else if( type == "bxdf" )
			{
				typeMap[name] = pxrcore::DataType::k_bxdf;
			}
			else if( type == "lightfilter" )
			{
				typeMap[name] = pxrcore::DataType::k_lightfilter;
			}
			else if( type == "samplefilter" )
			{
				typeMap[name] = pxrcore::DataType::k_samplefilter;
			}
			else if( type == "displayfilter" )
			{
				typeMap[name] = pxrcore::DataType::k_displayfilter;
			}
			else if( type == "struct" )
			{
				typeMap[name] = pxrcore::DataType::k_struct;
			}
			else
			{
				IECore::msg( IECore::Msg::Warning, "IECoreRenderMan", fmt::format( "Unknown type `{}` for parameter \"{}\".", type, name.CStr() ) );
			}
		}
		else if( child.first == "page" )
		{
			loadParameterTypes( child.second, typeMap );
		}
	}
}

ConstShaderInfoPtr shaderInfoFromArgsFile( const boost::filesystem::path file )
{
	std::ifstream argsStream( file.string() );

	boost::property_tree::ptree tree;
	boost::property_tree::read_xml( argsStream, tree );

	auto result = std::make_shared<ShaderInfo>();

	// Get type

	const string shaderType = tree.get<string>( "args.shaderType.tag.<xmlattr>.value" );
	if( shaderType == "pattern" )
	{
		result->type = riley::ShadingNode::Type::k_Pattern;
	}
	else if( shaderType == "bxdf" )
	{
		result->type = riley::ShadingNode::Type::k_Bxdf;
	}
	else if( shaderType == "integrator" )
	{
		result->type = riley::ShadingNode::Type::k_Integrator;
	}
	else if( shaderType == "light" )
	{
		result->type = riley::ShadingNode::Type::k_Light;
	}
	else if( shaderType == "lightfilter" )
	{
		result->type = riley::ShadingNode::Type::k_LightFilter;
	}
	else if( shaderType == "projection" )
	{
		result->type = riley::ShadingNode::Type::k_Projection;
	}
	else if( shaderType == "displacement" )
	{
		result->type = riley::ShadingNode::Type::k_Displacement;
	}
	else if( shaderType == "samplefilter" )
	{
		result->type = riley::ShadingNode::Type::k_SampleFilter;
	}
	else if( shaderType == "displayfilter" )
	{
		result->type = riley::ShadingNode::Type::k_DisplayFilter;
	}

	// Load parameters

	loadParameterTypes( tree.get_child( "args" ), result->parameterTypes );

	return result;
}

ConstShaderInfoPtr shaderInfoFromOSLQuery( OSL::OSLQuery &query )
{
	auto result = std::make_shared<ShaderInfo>();
	result->type = riley::ShadingNode::Type::k_Pattern;

	for( const auto &parameter : query )
	{
		const RtUString name( parameter.name.c_str() );
		OIIO::TypeDesc type = parameter.type;
		type.unarray();
		if( type == OIIO::TypeInt )
		{
			result->parameterTypes[name] = pxrcore::DataType::k_integer;
		}
		else if( type == OIIO::TypeFloat )
		{
			result->parameterTypes[name] = pxrcore::DataType::k_float;
		}
		else if( type == OIIO::TypeColor )
		{
			result->parameterTypes[name] = pxrcore::DataType::k_color;
		}
		else if( type == OIIO::TypePoint )
		{
			result->parameterTypes[name] = pxrcore::DataType::k_point;
		}
		else if( type == OIIO::TypeVector )
		{
			result->parameterTypes[name] = pxrcore::DataType::k_vector;
		}
		else if( type == OIIO::TypeNormal )
		{
			result->parameterTypes[name] = pxrcore::DataType::k_normal;
		}
		else if( type == OIIO::TypeMatrix44 )
		{
			result->parameterTypes[name] = pxrcore::DataType::k_matrix;
		}
		else if( type == OIIO::TypeString )
		{
			result->parameterTypes[name] = pxrcore::DataType::k_string;
		}
		else if( parameter.isstruct )
		{
			result->parameterTypes[name] = pxrcore::DataType::k_struct;
		}
		else
		{
			IECore::msg(
				IECore::Msg::Warning, "IECoreRenderMan",
				fmt::format(
					"Unknown type `{}` for parameter \"{}\" on shader \"{}\".",
					parameter.type, parameter.name, query.shadername()
				)
			);
		}
	}

	return result;
}

using ShaderInfoCache = IECore::LRUCache<string, ConstShaderInfoPtr>;

ShaderInfoCache g_shaderInfoCache(

	[]( const std::string &shaderName, size_t &cost ) -> ConstShaderInfoPtr {

		cost = 1;

		const char *rixPluginPath = getenv( "RMAN_RIXPLUGINPATH" );
		SearchPath rixSearchPath( rixPluginPath ? rixPluginPath : "" );
		boost::filesystem::path argsFileName = rixSearchPath.find( "Args/" + shaderName + ".args" );
		if( !argsFileName.empty() )
		{
			return shaderInfoFromArgsFile( argsFileName );
		}

		const char *oslSearchPath = getenv( "OSL_SHADER_PATHS" );
		OSL::OSLQuery oslQuery;
		if( oslQuery.open( shaderName, oslSearchPath ? oslSearchPath : "" ) )
		{
			return shaderInfoFromOSLQuery( oslQuery );
		}

		IECore::msg( IECore::Msg::Warning, "IECoreRenderMan", fmt::format( "Unable to find shader \"{}\".", shaderName ) );
		return nullptr;
	},

	/* maxCost = */ 10000

);

using ArrayConnections = std::unordered_map<RtUString, vector<RtUString>>;
const std::regex g_arrayIndexRegex( R"((\w+)\[([0-9]+)\])" );

void convertConnection( const IECoreScene::ShaderNetwork::Connection &connection, const ShaderInfo *shaderInfo, RtParamList &paramList, ArrayConnections &arrayConnections )
{
	RtUString destination;
	std::optional<size_t> destinationIndex;

	std::smatch arrayIndexMatch;
	if( std::regex_match( connection.destination.name.string(), arrayIndexMatch, g_arrayIndexRegex ) )
	{
		destination = RtUString( arrayIndexMatch.str( 1 ).c_str() );
		destinationIndex = std::stoi( arrayIndexMatch.str( 2 ) );
	}
	else
	{
		destination = RtUString( connection.destination.name.c_str() );
	}

	auto typeIt = shaderInfo->parameterTypes.find( destination );
	if( typeIt == shaderInfo->parameterTypes.end() )
	{
		IECore::msg(
			IECore::Msg::Warning, "IECoreRenderMan",
			fmt::format(
				"Unable to translate connection to `{}.{}` because its type is not known",
				connection.destination.shader.string(), connection.destination.name.string()
			)
		);
		return;
	}

	std::string reference = connection.source.shader;
	if(
		connection.source.name.string().size() &&
		// Several node types don't have named outputs, and
		// connections will silently fail if we include a name.
		typeIt->second != pxrcore::DataType::k_displayfilter &&
		typeIt->second != pxrcore::DataType::k_samplefilter &&
		typeIt->second != pxrcore::DataType::k_bxdf &&
		typeIt->second != pxrcore::DataType::k_lightfilter
	)
	{
		reference += ":" + connection.source.name.string();
	}
	const RtUString referenceU( reference.c_str() );

	if( !destinationIndex )
	{
		RtParamList::ParamInfo const info = {
			destination,
			typeIt->second,
			pxrcore::DetailType::k_reference,
			1,
			false,
			false,
			false
		};

		paramList.SetParam( info, &referenceU );
	}
	else
	{
		// We must connect all array elements at once. Buffer up for
		// later connection.
		auto &array = arrayConnections[destination];
		array.resize( max( array.size(), *destinationIndex + 1 ) );
		array[*destinationIndex] = referenceU;
	}
}

using HandleSet = std::unordered_set<InternedString>;

void convertShaderNetworkWalk( const ShaderNetwork::Parameter &outputParameter, const IECoreScene::ShaderNetwork *shaderNetwork, vector<riley::ShadingNode> &shadingNodes, HandleSet &visited )
{
	if( !visited.insert( outputParameter.shader ).second )
	{
		return;
	}

	const IECoreScene::Shader *shader = shaderNetwork->getShader( outputParameter.shader );
	ConstShaderInfoPtr shaderInfo = g_shaderInfoCache.get( shader->getName() );
	if( !shaderInfo )
	{
		return;
	}

	riley::ShadingNode node = {
		shaderInfo->type,
		RtUString( shader->getName().c_str() ),
		RtUString( outputParameter.shader.c_str() ),
		RtParamList()
	};

	for( const auto &[parameterName, parameterValue] : shader->parameters() )
	{
		if( std::regex_match( parameterName.string(), g_arrayIndexRegex ) )
		{
			// Ignore array element values for now. Gaffer generates these when
			// we use ArrayPlugs to represent shader parameters, but RenderMan
			// only accepts whole arrays as values. In practice, we're only using
			// ArrayPlugs where RenderMan is only interested in connections and not
			// values anyway, so we're not losing anything.
		}
		else
		{
			ParamListAlgo::convertParameter( RtUString( parameterName.c_str() ), parameterValue.get(), node.params );
		}
	}

	ArrayConnections arrayConnections;
	for( const auto &connection : shaderNetwork->inputConnections( outputParameter.shader ) )
	{
		convertShaderNetworkWalk( connection.source, shaderNetwork, shadingNodes, visited );
		convertConnection( connection, shaderInfo.get(), node.params, arrayConnections );
	}

	for( const auto &[destination, references] : arrayConnections )
	{
		RtParamList::ParamInfo const info = {
			destination,
			shaderInfo->parameterTypes.at( destination ),
			pxrcore::DetailType::k_reference,
			(uint32_t)references.size(),
			true,
			false,
			false
		};

		node.params.SetParam( info, references.data() );
	}

	shadingNodes.push_back( node );
}

//////////////////////////////////////////////////////////////////////////
// USD conversion code
//////////////////////////////////////////////////////////////////////////

template<typename T>
T parameterValue( const Shader *shader, InternedString parameterName, const T &defaultValue )
{
	if( auto d = shader->parametersData()->member<TypedData<T>>( parameterName ) )
	{
		return d->readable();
	}

	if constexpr( is_same_v<remove_cv_t<T>, Color3f > )
	{
		// Correction for USD files which author `float3` instead of `color3f`.
		// See `ShaderNetworkAlgoTest.testConvertUSDFloat3ToColor3f()`.
		if( auto d = shader->parametersData()->member<V3fData>( parameterName ) )
		{
			return d->readable();
		}
		// Conversion of Color4 to Color3, for cases like converting `UsdUVTexture.scale`
		// to `PxrTexture.colorScale`.
		if( auto d = shader->parametersData()->member<Color4fData>( parameterName ) )
		{
			const Color4f &c = d->readable();
			return Color3f( c[0], c[1], c[2] );
		}
	}
	else if constexpr( is_same_v<remove_cv_t<T>, V3f > )
	{
		// Conversion of V2f to V3f, for cases like converting `UsdPrimvarReader_float2.fallback`
		// to `PxrPrimvar.defaultFloat3`
		if( auto d = shader->parametersData()->member<V2fData>( parameterName ) )
		{
			const V2f &v = d->readable();
			return V3f( v[0], v[1], 0.f );
		}
	}
	else if constexpr( is_same_v<remove_cv_t<T>, std::string> )
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

template<typename T>
void transferUSDParameter( ShaderNetwork *network, InternedString shaderHandle, const Shader *usdShader, InternedString usdName, Shader *shader, InternedString name, const T &defaultValue )
{
	shader->parameters()[name] = new typename DataTraits<T>::DataType( parameterValue( usdShader, usdName, defaultValue ) );

	if( ShaderNetwork::Parameter input = network->input( { shaderHandle, usdName } ) )
	{
		if( name != usdName )
		{
			network->addConnection( { input, { shaderHandle, name } } );
			network->removeConnection( { input, { shaderHandle, usdName } } );
		}
	}
}

const InternedString g_angleParameter( "angle" );
const InternedString g_angleExtentParameter( "angleExtent" );
const InternedString g_areaNormalizeParameter( "areaNormalize" );
const InternedString g_bumpNormalParameter( "bumpNormal" );
const InternedString g_clearcoatDoubleSidedParameter( "clearcoatDoubleSided" );
const InternedString g_clearcoatFaceColorParameter( "clearcoatFaceColor" );
const InternedString g_clearcoatEdgeColorParameter( "clearcoatEdgeColor" );
const InternedString g_clearcoatRoughnessParameter( "clearcoatRoughness" );
const InternedString g_colorParameter( "color" );
const InternedString g_colorTemperatureParameter( "colorTemperature" );
const InternedString g_defaultFloatParameter( "defaultFloat" );
const InternedString g_defaultFloat3Parameter( "defaultFloat3" );
const InternedString g_defaultIntParameter( "defaultInt" );
const InternedString g_diffuseParameter( "diffuse" );
const InternedString g_diffuseColorParameter( "diffuseColor" );
const InternedString g_diffuseDoubleSidedParameter( "diffuseDoubleSided" );
const InternedString g_diffuseGainParameter( "diffuseGain") ;
const InternedString g_enableColorTemperatureParameter( "enableColorTemperature" );
const InternedString g_enableShadowsParameter( "enableShadows" );
const InternedString g_enableTemperatureParameter( "enableTemperature" );
const InternedString g_exposureParameter( "exposure" );
const InternedString g_fallbackParameter( "fallback" );
const InternedString g_glassIorParameter( "glassIor" );
const InternedString g_glassRoughnessParameter( "glassRoughness" );
const InternedString g_glowColorParameter( "glowColor" );
const InternedString g_glowGainParameter( "glowGain" );
const InternedString g_heightParameter( "height" );
const InternedString g_intensityParameter( "intensity" );
const InternedString g_lightColorParameter( "lightColor" );
const InternedString g_lightColorMapParameter( "lightColorMap" );
const InternedString g_normalParameter( "normal" );
const InternedString g_normalInParameter( "normalIn" );
const InternedString g_normalizeParameter( "normalize" );
const InternedString g_presenceParameter( "presence" );
const InternedString g_radiusParameter( "radius" );
const InternedString g_refractionGainParameter( "refractionGain" );
const InternedString g_resultFParameter( "resultF" );
const InternedString g_resultIParameter( "resultI" );
const InternedString g_resultRGBParameter( "resultRGB" );
const InternedString g_roughSpecularDoubleSidedParameter( "roughSpecularDoubleSided" );
const InternedString g_shadowColorParameter( "shadowColor" );
const InternedString g_shadowColorUSDParameter( "shadow:color" );
const InternedString g_shadowDistanceParameter( "shadowDistance" );
const InternedString g_shadowDistanceUSDParameter( "shadow:distance" );
const InternedString g_shadowEnableParameter( "shadow:enable" );
const InternedString g_shadowFalloffParameter( "shadowFalloff" );
const InternedString g_shadowFalloffUSDParameter( "shadow:falloff" );
const InternedString g_shadowFalloffGammaParameter( "shadowFalloffGamma");
const InternedString g_shadowFalloffGammaUSDParameter( "shadow:falloffGamma" );
const InternedString g_specularParameter( "specular" );
const InternedString g_specularDoubleSidedParameter( "specularDoubleSided" );
const InternedString g_specularEdgeColorParameter( "specularEdgeColor" );
const InternedString g_specularFaceColorParameter( "specularFaceColor" );
const InternedString g_specularIorParameter( "specularIor" );
const InternedString g_specularModelTypeParameter( "specularModelType" );
const InternedString g_specularRoughnessParameter( "specularRoughness" );
const InternedString g_temperatureParameter( "temperature" );
const InternedString g_textureFileParameter( "texture:file" );
const InternedString g_textureFormatParameter( "texture:format" );
const InternedString g_typeParameter( "type" );
const InternedString g_usdPrimvarReaderIntShaderName( "UsdPrimvarReader_int" );
const InternedString g_usdPrimvarReaderFloatShaderName( "UsdPrimvarReader_float" );
const InternedString g_varnameParameter( "varname" );
const InternedString g_widthParameter( "width" );

const std::string g_renderManLightNamespace( "ri:light:" );

const std::vector<InternedString> g_pxrSurfaceParameters = {
	g_diffuseGainParameter,
	g_diffuseColorParameter,
	g_specularFaceColorParameter,
	g_specularEdgeColorParameter,
	g_specularRoughnessParameter,
	g_specularIorParameter,
	g_clearcoatFaceColorParameter,
	g_clearcoatEdgeColorParameter,
	g_clearcoatRoughnessParameter,
	g_glowGainParameter,
	g_glowColorParameter,
	g_bumpNormalParameter,
	g_glassIorParameter,
	g_glassRoughnessParameter,
	g_refractionGainParameter,
	g_presenceParameter
};

const std::unordered_map<std::string, std::tuple<std::string, InternedString, std::variant<float, V3f, int>>> g_primVarMap = {
	{ "UsdPrimvarReader_float", { "float", g_defaultFloatParameter, 0.f } },
	{ "UsdPrimvarReader_float2", { "float2", g_defaultFloat3Parameter, V3f( 0.f ) } },
	{ "UsdPrimvarReader_float3", { "vector", g_defaultFloat3Parameter, V3f( 0.f ) } },
	{ "UsdPrimvarReader_normal", { "normal", g_defaultFloat3Parameter, V3f( 0.f ) } },
	{ "UsdPrimvarReader_point", { "point", g_defaultFloat3Parameter, V3f( 0.f ) } },
	{ "UsdPrimvarReader_vector", { "vector", g_defaultFloat3Parameter, V3f( 0.f ) } },
	{ "UsdPrimvarReader_int", { "int", g_defaultIntParameter, 0 } }
};

void transferUSDLightParameters( ShaderNetwork *network, InternedString shaderHandle, const Shader *usdShader, Shader *shader, const float defaultIntensity = 1.f )
{
	transferUSDParameter( network, shaderHandle, usdShader, g_colorParameter, shader, g_lightColorParameter, Color3f( 1.f, 1.f, 1.f ) );
	transferUSDParameter( network, shaderHandle, usdShader, g_diffuseParameter, shader, g_diffuseParameter, 1.0f );
	transferUSDParameter( network, shaderHandle, usdShader, g_exposureParameter, shader, g_exposureParameter, 0.0f );
	transferUSDParameter( network, shaderHandle, usdShader, g_intensityParameter, shader, g_intensityParameter, defaultIntensity );
	transferUSDParameter( network, shaderHandle, usdShader, g_specularParameter, shader, g_specularParameter, 1.0f );
	transferUSDParameter( network, shaderHandle, usdShader, g_enableColorTemperatureParameter, shader, g_enableTemperatureParameter, false );
	transferUSDParameter( network, shaderHandle, usdShader, g_colorTemperatureParameter, shader, g_temperatureParameter, 6500.f );

	transferUSDParameter( network, shaderHandle, usdShader, g_shadowEnableParameter, shader, g_enableShadowsParameter, true );
	transferUSDParameter( network, shaderHandle, usdShader, g_shadowColorUSDParameter, shader, g_shadowColorParameter, Color3f( 0 ) );
	transferUSDParameter( network, shaderHandle, usdShader, g_shadowDistanceUSDParameter, shader, g_shadowDistanceParameter, -1.f );
	transferUSDParameter( network, shaderHandle, usdShader, g_shadowFalloffUSDParameter, shader, g_shadowFalloffParameter, -1.f );
	transferUSDParameter( network, shaderHandle, usdShader, g_shadowFalloffGammaUSDParameter, shader, g_shadowFalloffGammaParameter, 1.f );

	for( const auto &[name, value] : usdShader->parameters() )
	{
		if( boost::starts_with( name.string(), g_renderManLightNamespace ) )
		{
			shader->parameters()[name.string().substr(g_renderManLightNamespace.size())] = value;
		}
	}
}

const InternedString remapOutputParameterName( const InternedString name, const InternedString shaderName )
{
	if( boost::starts_with( shaderName.string(), "UsdPrimvarReader" ) )
	{
		if( shaderName == g_usdPrimvarReaderFloatShaderName )
		{
			return g_resultFParameter;
		}
		else if( shaderName == g_usdPrimvarReaderIntShaderName )
		{
			return g_resultIParameter;
		}
		else
		{
			return g_resultRGBParameter;
		}
	}

	return name;
}

void replaceUSDShader( ShaderNetwork *network, InternedString handle, ShaderPtr &&newShader )
{
	const InternedString shaderName = network->getShader( handle )->getName();

	// Replace original shader with the new.
	network->setShader( handle, std::move( newShader ) );

	// Iterating over a copy because we will modify the range during iteration
	ShaderNetwork::ConnectionRange range = network->outputConnections( handle );
	std::vector<ShaderNetwork::Connection> outputConnections( range.begin(), range.end() );
	for( auto &c : outputConnections )
	{
		const InternedString remappedName = remapOutputParameterName( c.source.name, shaderName );
		if( remappedName != c.source.name )
		{
			network->removeConnection( c );
			c.source.name = remapOutputParameterName( c.source.name, shaderName );
			network->addConnection( c );
		}
	}
}

ShaderNetworkPtr preprocessedNetwork( const IECoreScene::ShaderNetwork *shaderNetwork )
{
	ShaderNetworkPtr result = shaderNetwork->copy();

	IECoreRenderMan::ShaderNetworkAlgo::convertUSDShaders( result.get() );

	return result;
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// External API
//////////////////////////////////////////////////////////////////////////

namespace IECoreRenderMan::ShaderNetworkAlgo
{

std::vector<riley::ShadingNode> convert( const IECoreScene::ShaderNetwork *network )
{
	ConstShaderNetworkPtr preprocessedNetwork = ::preprocessedNetwork( network );
	vector<riley::ShadingNode> result;
	result.reserve( preprocessedNetwork->size() );

	HandleSet visited;
	convertShaderNetworkWalk( preprocessedNetwork->getOutput(), preprocessedNetwork.get(), result, visited );

	return result;
}

IECoreScene::ConstShaderNetworkPtr combineLightFilters( const std::vector<const IECoreScene::ShaderNetwork *> networks )
{
	if( networks.empty() )
	{
		return nullptr;
	}

	if( networks.size() == 1 )
	{
		return networks[0];
	}

	unordered_map<string, size_t> numConnections;

	ShaderNetworkPtr combinedNetwork = new ShaderNetwork;
	auto combinerHandle = combinedNetwork->addShader(
		"combiner", new Shader( "PxrCombinerLightFilter", "lightFilter" )
	);
	combinedNetwork->setOutput( { combinerHandle, "out" } );

	for( auto network : networks )
	{
		const Shader *outputShader = network->outputShader();
		if( !outputShader )
		{
			continue;
		}

		string combineMode = "mult";
		if( auto combineModeData = outputShader->parametersData()->member<StringData>( "combineMode" ) )
		{
			combineMode = combineModeData->readable();
		}

		ShaderNetwork::Parameter filterHandle = IECoreScene::ShaderNetworkAlgo::addShaders( combinedNetwork.get(), network );

		const size_t connectionIndex = numConnections[combineMode]++;
		combinedNetwork->addConnection(
			ShaderNetwork::Connection( filterHandle, { combinerHandle, fmt::format( "{}[{}]", combineMode, connectionIndex ) } )
		);
	}

	return combinedNetwork;
}

void convertUSDShaders( ShaderNetwork *shaderNetwork )
{
	for( const auto &[handle, shader] : shaderNetwork->shaders() )
	{
		ShaderPtr newShader;
		if( shader->getName() == "UsdPreviewSurface" )
		{
			newShader = new Shader( "__usd/__UsdPreviewSurfaceParameters", "osl:shader" );

			// `UsdPreviewSurface` and `UsdPreviewSurfaceParameters` match except for `normal` -> `normalIn`.
			for( const auto &[p, v] : shader->parameters() )
			{
				newShader->parameters()[p != g_normalParameter ? p : g_normalInParameter] = v;
			}

			ShaderPtr pxrSurfaceShader = new Shader( "PxrSurface", "ri:surface" );
			// Use GGX instead of Beckman specular model.
			pxrSurfaceShader->parameters()[g_specularModelTypeParameter] = new IECore::IntData( 1 );
			pxrSurfaceShader->parameters()[g_diffuseDoubleSidedParameter] = new IECore::IntData( 1 );
			pxrSurfaceShader->parameters()[g_specularDoubleSidedParameter] = new IECore::IntData( 1 );
			pxrSurfaceShader->parameters()[g_roughSpecularDoubleSidedParameter] = new IECore::IntData( 1 );
			pxrSurfaceShader->parameters()[g_clearcoatDoubleSidedParameter] = new IECore::IntData( 1 );

			const InternedString pxrSurfaceHandle = shaderNetwork->addShader( handle.string() + "PxrSurface", std::move( pxrSurfaceShader ) );

			for( const auto &p : g_pxrSurfaceParameters )
			{
				shaderNetwork->addConnection( ShaderNetwork::Connection( { handle, InternedString( p.string() + "Out" ) }, { pxrSurfaceHandle, p } ) );
			}

			shaderNetwork->setOutput( { pxrSurfaceHandle, "" } );
		}
		else if( shader->getName() == "SphereLight" )
		{
			newShader = new Shader( "PxrSphereLight", "ri:light" );
			transferUSDLightParameters( shaderNetwork, handle, shader.get(), newShader.get() );
			transferUSDParameter( shaderNetwork, handle, shader.get(), g_normalizeParameter, newShader.get(), g_areaNormalizeParameter, false );
		}
		else if( shader->getName() == "DiskLight" )
		{
			newShader = new Shader( "PxrDiskLight", "ri:light" );
			transferUSDLightParameters( shaderNetwork, handle, shader.get(), newShader.get() );
			transferUSDParameter( shaderNetwork, handle, shader.get(), g_normalizeParameter, newShader.get(), g_areaNormalizeParameter, false );
		}
		else if( shader->getName() == "RectLight" )
		{
			newShader = new Shader( "PxrRectLight", "ri:light" );
			transferUSDLightParameters( shaderNetwork, handle, shader.get(), newShader.get() );
			transferUSDParameter( shaderNetwork, handle, shader.get(), g_normalizeParameter, newShader.get(), g_areaNormalizeParameter, false );

			const std::string textureFile = parameterValue( shader.get(), g_textureFileParameter, std::string() );
			if( !textureFile.empty() )
			{
				newShader->parameters()[g_lightColorMapParameter] = new StringData( textureFile );
			}
		}
		else if( shader->getName() == "DistantLight" )
		{
			newShader = new Shader( "PxrDistantLight", "ri:light" );
			transferUSDLightParameters( shaderNetwork, handle, shader.get(), newShader.get(), 50000.f );
			transferUSDParameter( shaderNetwork, handle, shader.get(), g_normalizeParameter, newShader.get(), g_areaNormalizeParameter, false );

			const float angle = parameterValue( shader.get(), g_angleParameter, 0.53f );
			newShader->parameters()[g_angleExtentParameter] = new FloatData( angle );
		}
		else if( shader->getName() == "DomeLight" )
		{
			newShader = new Shader( "PxrDomeLight", "ri:light" );
			transferUSDLightParameters( shaderNetwork, handle, shader.get(), newShader.get() );

			const std::string textureFile = parameterValue( shader.get(), g_textureFileParameter, std::string() );
			if( !textureFile.empty() )
			{
				newShader->parameters()[g_lightColorMapParameter] = new StringData( textureFile );
			}

			const std::string textureFormat = parameterValue( shader.get(), g_textureFormatParameter, std::string() );
			if( textureFormat != "automatic" )
			{
				IECore::msg(
					IECore::Msg::Warning,
					"convertUSDShaders",
					fmt::format( "Unsupported value \"{}\" for DomeLight.format. Only \"automatic\" is supported. Format will be read from texture file.", textureFormat )
				);
			}
		}

		const auto it = g_primVarMap.find( shader->getName() );
		if( it != g_primVarMap.end() )
		{
			newShader = new Shader( "PxrAttribute", "osl:shader" );
			const auto &[typeName, defaultParameter, defaultValue] = it->second;

			newShader->parameters()[g_typeParameter] = new StringData( typeName );
			transferUSDParameter( shaderNetwork, handle, shader.get(), g_varnameParameter, newShader.get(), g_varnameParameter, string() );
			std::visit(
				[&shaderNetwork, &handle, &shader, &newShader, &defaultParameter]( auto &&v )
				{
					transferUSDParameter( shaderNetwork, handle, shader.get(), g_fallbackParameter, newShader.get(), defaultParameter, v );
				},
				defaultValue
			);
		}

		if( newShader )
		{
			replaceUSDShader( shaderNetwork, handle, std::move( newShader ) );
		}
	}
	IECoreScene::ShaderNetworkAlgo::removeUnusedShaders( shaderNetwork );
}

M44f usdLightTransform( const Shader *lightShader )
{
	assert( lightShader );

	if( lightShader->getName() == "SphereLight" || lightShader->getName() == "DiskLight" )
	{
		const float radius = parameterValue( lightShader, g_radiusParameter, 0.5f );
		return M44f().scale( V3f( radius * 2.f ) );
	}
	else if( lightShader->getName() == "RectLight" )
	{
		const float width = parameterValue( lightShader, g_widthParameter, 1.f );
		const float height = parameterValue( lightShader, g_heightParameter, 1.f );
		return M44f().scale( V3f( width, height, 1.f ) );
	}

	return M44f();
}

} // namespace IECoreRenderMan::ShaderNetworkAlgo
