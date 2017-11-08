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

#include "boost/algorithm/string/predicate.hpp"
#include "boost/unordered_map.hpp"
#include "boost/lexical_cast.hpp"

#include "IECore/Shader.h"
#include "IECore/MessageHandler.h"
#include "IECore/SimpleTypedData.h"
#include "IECore/VectorTypedData.h"
#include "IECore/SplineData.h"

#include "IECoreArnold/ParameterAlgo.h"

#include "GafferArnold/Private/IECoreArnoldPreview/ShaderAlgo.h"
#include "GafferOSL/OSLShader.h"

using namespace std;
using namespace IECore;
using namespace IECoreArnold;

namespace
{

const IECore::InternedString g_handleString( "__handle" );

const AtString g_catmullRomArnoldString( "catmull-rom" );
const AtString g_bezierArnoldString( "bezier" );
const AtString g_bsplineArnoldString( "bspline" );
const AtString g_linearArnoldString( "linear" );
const AtString g_shaderNameArnoldString( "shadername" );

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

} // namespace

namespace IECoreArnoldPreview
{

namespace ShaderAlgo
{

std::vector<AtNode *> convert( const IECore::ObjectVector *shaderNetwork, const std::string &namePrefix, const AtNode *parentNode )
{
	typedef boost::unordered_map<std::string, AtNode *> ShaderMap;
	ShaderMap shaderMap; // Maps handles to nodes

	vector<AtNode *> result;
	for( ObjectVector::MemberContainer::const_iterator it = shaderNetwork->members().begin(), eIt = shaderNetwork->members().end(); it != eIt; ++it )
	{
		const char *nodeType = nullptr;
		const char *oslShaderName = nullptr;
		const CompoundDataMap *parameters = nullptr;
		if( const Shader *shader = runTimeCast<const Shader>( it->get() ) )
		{
			if( boost::starts_with( shader->getType(), "osl:" ) )
			{
				nodeType = "osl";
				oslShaderName = shader->getName().c_str();
			}
			else
			{
				nodeType = shader->getName().c_str();
			}
			parameters = &shader->parameters();
		}

		if( !nodeType )
		{
			continue;
		}

		std::string nodeName = boost::lexical_cast<string>( result.size() );
		auto handleIt = parameters->find( g_handleString );
		const StringData *handleData = nullptr;
		if( handleIt != parameters->end() )
		{
			handleData = runTimeCast<const StringData>( handleIt->second.get() );
			if( handleData )
			{
				nodeName = handleData->readable();
			}
		}

		AtNode *node = AiNode( AtString( nodeType ), AtString( (namePrefix + nodeName).c_str() ), parentNode );

		if( !node )
		{
			msg( Msg::Warning, "IECoreArnold::ShaderAlgo", boost::format( "Couldn't load shader \"%s\"" ) % nodeType );
			continue;
		}

		if( handleData )
		{
			shaderMap[nodeName] = node;
		}

		if( oslShaderName )
		{
			AiNodeSetStr( node, g_shaderNameArnoldString, AtString( oslShaderName ) );
		}

		for( CompoundDataMap::const_iterator pIt = parameters->begin(), peIt = parameters->end(); pIt != peIt; ++pIt )
		{
			std::string parameterNameString = pIt->first;
			if( oslShaderName )
			{
				parameterNameString = "param_" + parameterNameString;
			}
			AtString parameterName( parameterNameString.c_str() );

			if( const StringData *stringData = runTimeCast<const StringData>( pIt->second.get() ) )
			{
				const string &value = stringData->readable();
				if( boost::starts_with( value, "link:" ) )
				{
					string linkHandle = value.c_str() + 5;
					const size_t dotIndex = linkHandle.find_first_of( '.' );
					if( dotIndex != string::npos )
					{
						// Arnold does not support multiple outputs from OSL
						// shaders, so we must strip off any suffix specifying
						// a specific output.
						linkHandle = linkHandle.substr( 0, dotIndex );
					}

					ShaderMap::const_iterator shaderIt = shaderMap.find( linkHandle );
					if( shaderIt != shaderMap.end() )
					{
						const AtParamEntry *parmEntry = AiNodeEntryLookUpParameter( AiNodeGetNodeEntry( node ), parameterName );
						// If the parameter is a node pointer, we just set it to the source node.
						// Otherwise we assume that it is of a matching type to the output of the
						// source node, and try to link it
						if( AiParamGetType( parmEntry ) == AI_TYPE_NODE )
						{
							AiNodeSetPtr( node, parameterName, shaderIt->second );
						}
						else
						{
							AiNodeLinkOutput( shaderIt->second, "", node, parameterName );
						}
					}
					else
					{
						msg( Msg::Warning, "IECoreArnold::ShaderAlgo", boost::format( "Couldn't find shader handle \"%s\" for linking" ) % linkHandle );
					}
					continue;
				}
				else if( pIt->first.value() == "__handle" )
				{
					continue;
				}
			}
			else if( const StringVectorData *stringVectorData = runTimeCast<const StringVectorData>( pIt->second.get() ) )
			{
				const vector<string> &values = stringVectorData->readable();

				vector<AtNode *> nodes;
				for( unsigned int i = 0; i < values.size(); i++ )
				{
					const string &value = values[i];
					if( boost::starts_with( value, "link:" ) )
					{
						const string linkHandle = value.c_str() + 5;
						ShaderMap::const_iterator shaderIt = shaderMap.find( linkHandle );
						if( shaderIt != shaderMap.end() )
						{
							nodes.push_back( shaderIt->second );
						}
						else
						{
							msg( Msg::Warning, "IECoreArnold::ShaderAlgo", boost::format( "Couldn't find shader handle \"%s\" for linking" ) % linkHandle );
						}
					}
				}

				if( nodes.size() )
				{
					const AtParamEntry *parmEntry = AiNodeEntryLookUpParameter( AiNodeGetNodeEntry( node ), parameterName );
					if( AiParamGetType( parmEntry ) == AI_TYPE_ARRAY )
					{
						const AtParamValue *def = AiParamGetDefault( parmEntry );

						// Appropriately use SetArray vs LinkOutput depending on target type, as above
						if( AiArrayGetType( def->ARRAY() ) == AI_TYPE_NODE )
						{
							AtArray *nodesArray = AiArrayConvert( nodes.size(), 1, AI_TYPE_POINTER, &nodes[0] );
							AiNodeSetArray( node, parameterName, nodesArray );
						}
						else
						{
							for( unsigned int i = 0; i < nodes.size(); i++ )
							{
								AiNodeLinkOutput(
									nodes[i], "", node,
									( parameterNameString + "[" + boost::lexical_cast<string>( i ) + "]" ).c_str()
								);
							}
						}

						continue;
					}
				}
			}
			else if( const SplineffData *splineData = runTimeCast<const SplineffData>( pIt->second.get() ) )
			{
				setSplineParameter( node, parameterNameString, splineData->readable() );
				continue;
			}
			else if( const SplinefColor3fData *splineData = runTimeCast<const SplinefColor3fData>( pIt->second.get() ) )
			{
				setSplineParameter( node, parameterNameString, splineData->readable() );
				continue;
			}

			ParameterAlgo::setParameter( node, parameterName, pIt->second.get() );
		}

		result.push_back( node );
	}

	return result;
}

} // namespace ShaderAlgo

} // namespace IECoreArnoldPreview
