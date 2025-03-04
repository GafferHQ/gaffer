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

#include "ShaderNetworkAlgo.h"

#include "ParamListAlgo.h"

#include "IECore/DataAlgo.h"
#include "IECore/LRUCache.h"
#include "IECore/MessageHandler.h"
#include "IECore/SearchPath.h"

#include "OSL/oslquery.h"

#include "boost/container/flat_map.hpp"
#include "boost/property_tree/xml_parser.hpp"

#include "fmt/format.h"

#include <regex>
#include <unordered_set>

using namespace std;
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

	auto it = shaderInfo->parameterTypes.find( destination );
	if( it == shaderInfo->parameterTypes.end() )
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
	if( !connection.source.name.string().empty() )
	{
		reference += ":" + connection.source.name.string();
	}
	const RtUString referenceU( reference.c_str() );

	if( !destinationIndex )
	{
		RtParamList::ParamInfo const info = {
			destination,
			it->second,
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

} // namespace

//////////////////////////////////////////////////////////////////////////
// External API
//////////////////////////////////////////////////////////////////////////

std::vector<riley::ShadingNode> IECoreRenderMan::ShaderNetworkAlgo::convert( const IECoreScene::ShaderNetwork *network )
{
	vector<riley::ShadingNode> result;
	result.reserve( network->size() );

	HandleSet visited;
	convertShaderNetworkWalk( network->getOutput(), network, result, visited );

	return result;
}
