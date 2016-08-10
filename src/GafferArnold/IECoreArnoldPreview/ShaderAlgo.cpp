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

#include "IECoreArnold/ParameterAlgo.h"

#include "GafferArnold/Private/IECoreArnoldPreview/ShaderAlgo.h"

using namespace std;
using namespace IECore;
using namespace IECoreArnold;

namespace IECoreArnoldPreview
{

namespace ShaderAlgo
{

std::vector<AtNode *> convert( const IECore::ObjectVector *shaderNetwork, const std::string &namePrefix )
{
	typedef boost::unordered_map<std::string, AtNode *> ShaderMap;
	ShaderMap shaderMap; // Maps handles to nodes

	vector<AtNode *> result;
	for( ObjectVector::MemberContainer::const_iterator it = shaderNetwork->members().begin(), eIt = shaderNetwork->members().end(); it != eIt; ++it )
	{
		const char *nodeType = NULL;
		const CompoundDataMap *parameters = NULL;
		if( const Shader *shader = runTimeCast<const Shader>( it->get() ) )
		{
			nodeType = shader->getName().c_str();
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

		AtNode *node = AiNode( nodeType );
		if( !node )
		{
			msg( Msg::Warning, "IECoreArnold::ShaderAlgo", boost::format( "Couldn't load shader \"%s\"" ) % nodeType );
			continue;
		}

		std::string nodeName = boost::lexical_cast<string>( result.size() );
		for( CompoundDataMap::const_iterator pIt = parameters->begin(), peIt = parameters->end(); pIt != peIt; ++pIt )
		{
			if( const StringData *stringData = runTimeCast<const StringData>( pIt->second.get() ) )
			{
				const string &value = stringData->readable();
				if( boost::starts_with( value, "link:" ) )
				{
					const string linkHandle = value.c_str() + 5;
					ShaderMap::const_iterator shaderIt = shaderMap.find( linkHandle );
					if( shaderIt != shaderMap.end() )
					{
						const char *parmName = pIt->first.value().c_str();
						const AtParamEntry *parmEntry = AiNodeEntryLookUpParameter( AiNodeGetNodeEntry( node ), parmName );
						// If the parameter is a node pointer, we just set it to the source node.
						// Otherwise we assume that it is of a matching type to the output of the
						// source node, and try to link it
						if( AiParamGetType( parmEntry ) == AI_TYPE_NODE )
						{
							AiNodeSetPtr( node, parmName, shaderIt->second );
						}
						else
						{
							AiNodeLinkOutput( shaderIt->second, "", node, parmName );
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
					shaderMap[value] = node;
					nodeName = value;
					continue;
				}
			}

			if( const StringVectorData *stringVectorData = runTimeCast<const StringVectorData>( pIt->second.get() ) )
			{
				const vector<string> &values = stringVectorData->readable();

				std::vector< AtNode* > filters;
				for( unsigned int i = 0; i < values.size(); i++ )
				{
					const string &value = values[i];
					if( boost::starts_with( value, "link:" ) )
					{
						const string linkHandle = value.c_str() + 5;
						ShaderMap::const_iterator shaderIt = shaderMap.find( linkHandle );
						if( shaderIt != shaderMap.end() )
						{
							filters.push_back( shaderIt->second );
						}
						else
						{
							msg( Msg::Warning, "IECoreArnold::ShaderAlgo", boost::format( "Couldn't find shader handle \"%s\" for linking" ) % linkHandle );
						}
					}
				}
			
				if( filters.size() )
				{
					const char *parmName = pIt->first.value().c_str();
					const AtParamEntry *parmEntry = AiNodeEntryLookUpParameter( AiNodeGetNodeEntry( node ), parmName );
					if( AiParamGetType( parmEntry ) == AI_TYPE_ARRAY )
					{
						const AtParamValue *def = AiParamGetDefault( parmEntry );
						
						// Appropriately use SetArray vs LinkOutput depending on target type, as above
						if( def->ARRAY->type == AI_TYPE_NODE )
						{
							AtArray *filterArray = AiArrayConvert( filters.size(), 1, AI_TYPE_POINTER, &filters[0] );
							AiNodeSetArray( node, pIt->first.value().c_str(), filterArray );
						}
						else
						{
							for( unsigned int i = 0; i < filters.size(); i++ )
							{
								AiNodeLinkOutput( filters[i], "", node,
									( pIt->first.value() + "[" + boost::lexical_cast<string>( i ) + "]" ).c_str() );
							}
						}

						continue;
					}
				}
			}


			ParameterAlgo::setParameter( node, pIt->first.value().c_str(), pIt->second.get() );
		}

		nodeName = namePrefix + nodeName;
		AiNodeSetStr( node, "name", nodeName.c_str() );
		result.push_back( node );
	}

	return result;
}

} // namespace ShaderAlgo

} // namespace IECoreArnoldPreview
