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

#include "GafferArnold/Private/IECoreArnoldPreview/ShaderNetworkAlgo.h"

#include "GafferOSL/OSLShader.h"

#include "IECoreArnold/ParameterAlgo.h"

#include "IECoreScene/Shader.h"
#include "IECoreScene/ShaderNetworkAlgo.h"

#include "IECore/MessageHandler.h"
#include "IECore/SimpleTypedData.h"
#include "IECore/SplineData.h"
#include "IECore/VectorTypedData.h"

#include "boost/algorithm/string/predicate.hpp"
#include "boost/lexical_cast.hpp"
#include "boost/unordered_map.hpp"

using namespace std;
using namespace IECore;
using namespace IECoreScene;
using namespace IECoreArnold;

namespace
{

const AtString g_catmullRomArnoldString( "catmull-rom" );
const AtString g_bezierArnoldString( "bezier" );
const AtString g_bsplineArnoldString( "bspline" );
const AtString g_linearArnoldString( "linear" );
const AtString g_outputArnoldString( "output" );
const AtString g_shaderNameArnoldString( "shadername" );
const AtString g_oslArnoldString( "osl" );
const AtString g_nameArnoldString( "name" );

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

	GafferOSL::OSLShader::prepareSplineCVsForOSL( positions, values, basis );
	ParameterAlgo::setParameter( node, ( name + "Positions" ).c_str(), positionsData.get() );
	ParameterAlgo::setParameter( node, ( name + "Values" ).c_str(), valuesData.get() );
	AiNodeSetStr( node, AtString( ( name + "Basis" ).c_str() ), basis );
}

typedef boost::unordered_map<ShaderNetwork::Parameter, AtNode *> ShaderMap;

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

template<typename NodeCreator>
AtNode *convertWalk( const ShaderNetwork::Parameter &outputParameter, const IECoreScene::ShaderNetwork *shaderNetwork, const std::string &name, const NodeCreator &nodeCreator, vector<AtNode *> &nodes, ShaderMap &converted )
{
	// Reuse previously created node if we can. OSL shaders
	// can have multiple outputs, but each Arnold shader node
	// can have only a single output, so we have to emit OSL
	// shaders multiple times, once for each distinct top-level
	// output that is used.

	const IECoreScene::Shader *shader = shaderNetwork->getShader( outputParameter.shader );
	const bool isOSLShader = boost::starts_with( shader->getType(), "osl:" );
	const InternedString oslOutput = isOSLShader ? partitionStart( outputParameter.name, '.' ) : InternedString();

	auto inserted = converted.insert( { { outputParameter.shader, oslOutput }, nullptr } );
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
	if( oslOutput.string().size() )
	{
		nodeName += ":" + oslOutput.string();
	}

	if( isOSLShader )
	{
		node = nodeCreator( g_oslArnoldString, AtString( nodeName.c_str() ) );
		if( oslOutput.string().size() )
		{
			AiNodeDeclare( node, g_outputArnoldString, "constant STRING" );
			AiNodeSetStr( node, g_outputArnoldString, AtString( oslOutput.c_str() ) );
		}
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
		msg( Msg::Warning, "IECoreArnold::ShaderNetworkAlgo", boost::format( "Couldn't load shader \"%s\"" ) % shader->getName() );
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
			ParameterAlgo::setParameter( node, AtString( parameterName.c_str() ), namedParameter.second.get() );
		}
	}

	// Recurse through input connections

	for( const auto &connection : shaderNetwork->inputConnections( outputParameter.shader ) )
	{
		AtNode *sourceNode = convertWalk( connection.source, shaderNetwork, name, nodeCreator, nodes, converted );
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

		AiNodeLinkOutput( sourceNode, sourceName.c_str(), node, parameterName.c_str() );
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
}

} // namespace

namespace IECoreArnoldPreview
{

namespace ShaderNetworkAlgo
{

std::vector<AtNode *> convert( const IECoreScene::ShaderNetwork *shaderNetwork, const std::string &name, const AtNode *parentNode )
{
	// \todo: remove this conversion once Arnold supports it natively
	ShaderNetworkPtr networkCopy = shaderNetwork->copy();
	IECoreScene::ShaderNetworkAlgo::convertOSLComponentConnections( networkCopy.get() );
	shaderNetwork = networkCopy.get();

	ShaderMap converted;
	vector<AtNode *> result;
	const InternedString output = shaderNetwork->getOutput().shader;
	if( output.string().empty() )
	{
		msg( Msg::Warning, "IECoreArnold::ShaderNetworkAlgo", "Shader has no output" );
	}
	else
	{
		auto nodeCreator = [parentNode]( const AtString &nodeType, const AtString &nodeName ) {
			return AiNode( nodeType, nodeName, parentNode );
		};
		convertWalk( shaderNetwork->getOutput(), shaderNetwork, name, nodeCreator, result, converted );
		for( const auto &kv : shaderNetwork->outputShader()->blindData()->readable() )
		{
			ParameterAlgo::setParameter( result.back(), AtString( kv.first.c_str() ), kv.second.get() );
		}
	}
	return result;
}

bool update( std::vector<AtNode *> &nodes, const IECoreScene::ShaderNetwork *shaderNetwork )
{
	assert( nodes.size() );
	AtNode *parentNode = AiNodeGetParent( nodes.back() );
	const std::string &name = AiNodeGetName( nodes.back() );

	boost::unordered_map<AtString, AtNode *, AtStringHash> originalNodes;
	for( const auto &n : nodes )
	{
		originalNodes[AtString(AiNodeGetName(n))] = n;
	}
	std::unordered_set<AtNode *> reusedNodes;
	nodes.clear();

	auto nodeCreator = [parentNode, &originalNodes, &reusedNodes]( const AtString &nodeType, const AtString &nodeName ) {
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
		return AiNode( nodeType, nodeName, parentNode );
	};

	ShaderMap converted;
	convertWalk( shaderNetwork->getOutput(), shaderNetwork, name, nodeCreator, nodes, converted );

	for( const auto &n : originalNodes )
	{
		AiNodeDestroy( n.second );
	}

	return nodes.size() && reusedNodes.count( nodes.back() );
}

} // namespace ShaderNetworkAlgo

} // namespace IECoreArnoldPreview
