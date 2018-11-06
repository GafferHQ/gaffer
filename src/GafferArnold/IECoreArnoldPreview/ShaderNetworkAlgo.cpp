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

AtNode *convertWalk( const ShaderNetwork::Parameter &outputParameter, const IECoreScene::ShaderNetwork *shaderNetwork, const std::string &namePrefix, const AtNode *parentNode, vector<AtNode *> &nodes, ShaderMap &converted )
{
	// Reuse previously created node if we can

	auto inserted = converted.insert( { outputParameter, nullptr } );
	AtNode *&node = inserted.first->second;
	if( !inserted.second )
	{
		return node;
	}

	// Create the AtNode for this shader output

	const string nodeName(
		namePrefix +
		outputParameter.shader.string() +
		outputParameter.name.string()
	);

	const IECoreScene::Shader *shader = shaderNetwork->getShader( outputParameter.shader );
	const bool isOSLShader = boost::starts_with( shader->getType(), "osl:" );
	if( isOSLShader )
	{
		node = AiNode( g_oslArnoldString, AtString( nodeName.c_str() ), parentNode );
		if( outputParameter.name.string().size() )
		{
			AiNodeDeclare( node, g_outputArnoldString, "constant STRING" );
			AiNodeSetStr( node, g_outputArnoldString, AtString( outputParameter.name.c_str() ) );
		}
		AiNodeSetStr( node, g_shaderNameArnoldString, AtString( shader->getName().c_str() ) );
	}
	else
	{
		node = AiNode(
			AtString( shader->getName().c_str() ),
			AtString( nodeName.c_str() ),
			parentNode
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
		AtNode *sourceNode = convertWalk( connection.source, shaderNetwork, namePrefix, parentNode, nodes, converted );
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

		AiNodeLinkOutput( sourceNode, "", node, parameterName.c_str() );
	}

	nodes.push_back( node );
	return node;
}

} // namespace

namespace IECoreArnoldPreview
{

namespace ShaderNetworkAlgo
{

std::vector<AtNode *> convert( const IECoreScene::ShaderNetwork *shaderNetwork, const std::string &namePrefix, const AtNode *parentNode )
{
	ShaderMap converted;
	vector<AtNode *> result;
	const InternedString output = shaderNetwork->getOutput().shader;
	if( output.string().empty() )
	{
		msg( Msg::Warning, "IECoreArnold::ShaderNetworkAlgo", "Shader has no output" );
	}
	else
	{
		convertWalk( shaderNetwork->getOutput(), shaderNetwork, namePrefix, parentNode, result, converted );
	}
	return result;
}

} // namespace ShaderNetworkAlgo

} // namespace IECoreArnoldPreview
