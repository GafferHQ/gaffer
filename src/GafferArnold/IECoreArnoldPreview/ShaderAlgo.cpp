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
#include "IECore/Light.h"
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

template<typename Spline>
void setSplineParameter( AtNode *node, const InternedString &name, const Spline &spline )
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


	const char *basis = "catmull-rom";
	if( spline.basis == Spline::Basis::bezier() )
	{
		basis = "bezier";
	}
	else if( spline.basis == Spline::Basis::bSpline() )
	{
		basis = "bspline";
	}
	else if( spline.basis == Spline::Basis::linear() )
	{
		basis = "linear";
	}

	GafferOSL::OSLShader::prepareSplineCVsForOSL( positions, values, basis );
	ParameterAlgo::setParameter( node, ( name.string() + "Positions" ).c_str(), positionsData.get() );
	ParameterAlgo::setParameter( node, ( name.string() + "Values" ).c_str(), valuesData.get() );
	AiNodeSetStr( node, ( name.string() + "Basis" ).c_str(), basis );
}

} // namespace

namespace IECoreArnoldPreview
{

namespace ShaderAlgo
{

std::vector<AtNode *> convert( const IECore::ObjectVector *shaderNetwork, const std::string &namePrefix )
{
	typedef boost::unordered_map<std::string, AtNode *> ShaderMap;
	ShaderMap shaderMap; // Maps handles to nodes

	vector<AtNode *> result;

	// \todo - We need to hack around Arnold's lack of support for multiple outputs by outputting
	// nodes multiple times if they have multiple outputs that are used.  For this reason, we first
	// collect a list of all outputs that are used.  If in the future Arnold makes it possible to
	// just use all the outputs of OSL nodes, we can remove all this.
	std::vector<std::string> usedHandles;
	for( ObjectVector::MemberContainer::const_iterator it = shaderNetwork->members().begin(), eIt = shaderNetwork->members().end(); it != eIt; ++it )
	{
		const Shader *shader = runTimeCast<const Shader>( it->get() );
		if( !shader )
		{
			continue;
		}
		const CompoundDataMap *parameters = &shader->parameters();
		for( CompoundDataMap::const_iterator pIt = parameters->begin(), peIt = parameters->end(); pIt != peIt; ++pIt )
		{
			if( const StringData *stringData = runTimeCast<const StringData>( pIt->second.get() ) )
			{
				const string &value = stringData->readable();
				if( boost::starts_with( value, "link:" ) )
				{
					usedHandles.push_back( value.c_str() + 5 );
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
						usedHandles.push_back( value.c_str() + 5 );
					}
				}
			}
		}
	}

	// Sort and remove duplicates using silly std syntax
	std::sort( usedHandles.begin(), usedHandles.end() );
	usedHandles.erase( std::unique( usedHandles.begin(), usedHandles.end() ), usedHandles.end() );

	for( ObjectVector::MemberContainer::const_iterator it = shaderNetwork->members().begin(), eIt = shaderNetwork->members().end(); it != eIt; ++it )
	{
		const char *nodeType = NULL;
		const char *oslShaderName = NULL;
		const CompoundDataMap *parameters = NULL;
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
		else if( const Light *light = runTimeCast<const Light>( it->get() ) )
		{
			/// \todo We don't really have much need for IECore::Lights any more.
			/// Just use shaders everywhere instead.
			nodeType = light->getName().c_str();
			if( boost::starts_with( nodeType, "ai:" ) )
			{
				/// \todo This is working around the addition of prefixes in Gaffer.
				/// We should find a way of not needing the prefixes.
				nodeType += 3;
			}
			parameters = &light->parameters();
		}

		if( !nodeType )
		{
			continue;
		}

		std::string nodeName = boost::lexical_cast<string>( result.size() );
		CompoundDataMap::const_iterator handleIt = parameters->find( g_handleString );
		const StringData *handleData = NULL;
		if( handleIt != parameters->end() )
		{
			handleData = runTimeCast<const StringData>( handleIt->second.get() );
			if( handleData )
			{
				nodeName = handleData->readable();
			}
		}

		std::vector<std::string> outputNames;
		if( oslShaderName )
		{
			// Find all outputs of this node which are used
			std::string outputPrefix = nodeName + ".";
			std::vector<std::string>::iterator matchStart = std::lower_bound(usedHandles.begin(), usedHandles.end(), outputPrefix );
			while( matchStart != usedHandles.end() && boost::starts_with( *matchStart, outputPrefix ) )
			{
				outputNames.push_back( matchStart->c_str() + outputPrefix.length() );
				matchStart++;
			}
		}

		if( outputNames.size() == 0 )
		{
			// Either not an OSL shader, or the final shader in the chain
			outputNames.push_back( "" );
		}

		// Output the node repeatedly for each output, because Arnold does not currently support
		// multiple outputs from a node
		for( unsigned int nI = 0; nI < outputNames.size(); nI++ )
		{
			std::string &outputName = outputNames[nI];

			AtNode *node = AiNode( AtString( nodeType ), AtString( (namePrefix + nodeName + outputName).c_str() ) );

			if( !node )
			{
				msg( Msg::Warning, "IECoreArnold::ShaderAlgo", boost::format( "Couldn't load shader \"%s\"" ) % nodeType );
				continue;
			}

			if( handleData )
			{
				if( outputName == "" )
				{
					shaderMap[nodeName] = node;
				}
				else
				{
					shaderMap[nodeName + "." + outputName] = node;
				}
			}

			if( outputName != "" )
			{
				AiNodeDeclare( node, "output", "constant STRING" );
				AiNodeSetStr( node, "output", AtString( outputName.c_str() ) );
			}

			if( oslShaderName )
			{
				AiNodeSetStr( node, "shadername", oslShaderName );
			}

			for( CompoundDataMap::const_iterator pIt = parameters->begin(), peIt = parameters->end(); pIt != peIt; ++pIt )
			{
				std::string parameterName = pIt->first;
				if( oslShaderName )
				{
					parameterName = "param_" + parameterName;
				}

				if( const StringData *stringData = runTimeCast<const StringData>( pIt->second.get() ) )
				{
					const string &value = stringData->readable();
					if( boost::starts_with( value, "link:" ) )
					{
						string linkHandle = value.c_str() + 5;

						ShaderMap::const_iterator shaderIt = shaderMap.find( linkHandle );
						if( shaderIt != shaderMap.end() )
						{
							const AtParamEntry *parmEntry = AiNodeEntryLookUpParameter( AiNodeGetNodeEntry( node ), parameterName.c_str() );
							// If the parameter is a node pointer, we just set it to the source node.
							// Otherwise we assume that it is of a matching type to the output of the
							// source node, and try to link it
							if( AiParamGetType( parmEntry ) == AI_TYPE_NODE )
							{
								AiNodeSetPtr( node, parameterName.c_str(), shaderIt->second );
							}
							else
							{
								AiNodeLinkOutput( shaderIt->second, "", node, parameterName.c_str() );
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
						const AtParamEntry *parmEntry = AiNodeEntryLookUpParameter( AiNodeGetNodeEntry( node ), parameterName.c_str() );
						if( AiParamGetType( parmEntry ) == AI_TYPE_ARRAY )
						{
							const AtParamValue *def = AiParamGetDefault( parmEntry );

							// Appropriately use SetArray vs LinkOutput depending on target type, as above
							if( AiArrayGetType( def->ARRAY() ) == AI_TYPE_NODE )
							{
								AtArray *nodesArray = AiArrayConvert( nodes.size(), 1, AI_TYPE_POINTER, &nodes[0] );
								AiNodeSetArray( node, parameterName.c_str(), nodesArray );
							}
							else
							{
								for( unsigned int i = 0; i < nodes.size(); i++ )
								{
									AiNodeLinkOutput(
										nodes[i], "", node,
										( parameterName + "[" + boost::lexical_cast<string>( i ) + "]" ).c_str()
									);
								}
							}

							continue;
						}
					}
				}
				else if( const SplineffData *splineData = runTimeCast<const SplineffData>( pIt->second.get() ) )
				{
					setSplineParameter( node, parameterName.c_str(), splineData->readable() );
					continue;
				}
				else if( const SplinefColor3fData *splineData = runTimeCast<const SplinefColor3fData>( pIt->second.get() ) )
				{
					setSplineParameter( node, parameterName.c_str(), splineData->readable() );
					continue;
				}

				ParameterAlgo::setParameter( node, parameterName.c_str(), pIt->second.get() );
			}

			result.push_back( node );
		}
	}

	return result;
}

} // namespace ShaderAlgo

} // namespace IECoreArnoldPreview
