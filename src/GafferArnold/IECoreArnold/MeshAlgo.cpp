//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2016, Image Engine Design Inc. All rights reserved.
//  Copyright (c) 2012, John Haddon. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//     * Redistributions of source code must retain the above copyright
//       notice, this list of conditions and the following disclaimer.
//
//     * Redistributions in binary form must reproduce the above copyright
//       notice, this list of conditions and the following disclaimer in the
//       documentation and/or other materials provided with the distribution.
//
//     * Neither the name of Image Engine Design nor the names of any
//       other contributors to this software may be used to endorse or
//       promote products derived from this software without specific prior
//       written permission.
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

#include "GafferArnold/Private/IECoreArnold/NodeAlgo.h"
#include "GafferArnold/Private/IECoreArnold/ParameterAlgo.h"
#include "GafferArnold/Private/IECoreArnold/ShapeAlgo.h"

#include "IECoreScene/MeshPrimitive.h"

#include "IECore/Exception.h"
#include "IECore/MessageHandler.h"

#include "boost/algorithm/string/predicate.hpp"

#include "ai.h"

#include <algorithm>

using namespace std;
using namespace IECore;
using namespace IECoreScene;
using namespace IECoreArnold;

namespace
{

const AtString g_catclarkArnoldString("catclark");
const AtString g_motionStartArnoldString("motion_start");
const AtString g_motionEndArnoldString("motion_end");
const AtString g_nidxsArnoldString("nidxs");
const AtString g_nlistArnoldString("nlist");
const AtString g_nsidesArnoldString("nsides");
const AtString g_polymeshArnoldString("polymesh");
const AtString g_smoothingArnoldString("smoothing");
const AtString g_subdivTypeArnoldString("subdiv_type");
const AtString g_uvidxsArnoldString("uvidxs");
const AtString g_uvlistArnoldString("uvlist");
const AtString g_vidxsArnoldString("vidxs");
const AtString g_vlistArnoldString("vlist");
const AtString g_creaseIdxsArnoldString("crease_idxs");
const AtString g_creaseSharpnessArnoldString("crease_sharpness");

AtArray *identityIndices( size_t size )
{
	AtArray *result = AiArrayAllocate( size, 1, AI_TYPE_UINT );
	for( size_t i=0; i < size; ++i )
	{
		AiArraySetInt( result, i, i );
	}
	return result;
}

template<typename T>
const T *variableData( const PrimitiveVariableMap &variables, const std::string &name, PrimitiveVariable::Interpolation interpolation = PrimitiveVariable::Invalid )
{
	PrimitiveVariableMap::const_iterator it = variables.find( name );
	if( it==variables.end() )
	{
		return NULL;
	}
	if( interpolation != PrimitiveVariable::Invalid && it->second.interpolation != interpolation )
	{
		return NULL;
	}
	return runTimeCast<T>( it->second.data.get() );
}

void convertUVSet( const std::string &uvSet, const PrimitiveVariable &uvVariable, const vector<int> &vertexIds, AtNode *node )
{
	const V2fVectorData *uvData = runTimeCast<V2fVectorData>( uvVariable.data.get() );

	if( !uvData )
	{
		return;
	}

	if( uvVariable.interpolation != PrimitiveVariable::Varying && uvVariable.interpolation != PrimitiveVariable::Vertex && uvVariable.interpolation != PrimitiveVariable::FaceVarying )
	{
		msg(
			Msg::Warning, "ToArnoldMeshConverter::doConversion",
			boost::format( "Variable \"%s\" has an invalid interpolation type - not generating uvs." ) % uvSet
		);
		return;
	}

	const vector<Imath::V2f> &uvs = uvData->readable();

	AtArray *uvsArray = AiArrayAllocate( uvs.size(), 1, AI_TYPE_VECTOR2 );
	for( size_t i = 0, e = uvs.size(); i < e; ++i )
	{
		AtVector2 uv = { uvs[i][0], uvs[i][1] };
		AiArraySetVec2( uvsArray, i, uv );
	}

	AtArray *indicesArray = nullptr;
	if( uvVariable.indices )
	{
		if( uvVariable.interpolation == PrimitiveVariable::FaceVarying )
		{
			const vector<int> &indices = uvVariable.indices->readable();
			indicesArray = AiArrayAllocate( indices.size(), 1, AI_TYPE_UINT );
			for( size_t i = 0, e = indices.size(); i < e; ++i )
			{
				AiArraySetUInt( indicesArray, i, indices[i] );
			}
		}
		else // Varying or Vertex - we need to expands the indices to face varying
		{
			const vector<int> &indices = uvVariable.indices->readable();
			indicesArray = AiArrayAllocate( vertexIds.size(), 1, AI_TYPE_UINT );
			for( size_t i = 0, e = vertexIds.size(); i < e; ++i )
			{
				AiArraySetUInt( indicesArray, i, indices[vertexIds[i]] );
			}
		}
	}
	else if( uvVariable.interpolation == PrimitiveVariable::FaceVarying )
	{
		indicesArray = identityIndices( vertexIds.size() );
	}
	else
	{
		indicesArray = AiArrayAllocate( vertexIds.size(), 1, AI_TYPE_UINT );
		for( size_t i = 0, e = vertexIds.size(); i < e; ++i )
		{
			AiArraySetUInt( indicesArray, i, vertexIds[i] );
		}
	}

	if( uvSet == "uv" )
	{
		AiNodeSetArray( node, g_uvlistArnoldString, uvsArray );
		AiNodeSetArray( node, g_uvidxsArnoldString, indicesArray );
	}
	else
	{
		AtString uvSetName( uvSet.c_str() );
		AiNodeDeclare( node, uvSetName, "indexed POINT2" );
		AiNodeSetArray( node, uvSetName, uvsArray );
		AiNodeSetArray( node, AtString( (uvSet + "idxs").c_str() ), indicesArray );
	}
}

void convertCornersAndCreases( const IECoreScene::MeshPrimitive *mesh, AtNode *node )
{
	// Arnold treats all creased edges individually, with no concept of
	// a chain of edges forming a single crease. It represents corners as
	// "edges" where both vertices are identical. Figure out how many edges
	// we have in Arnold's format.

	size_t numEdges = mesh->cornerIds()->readable().size();
	for( int length : mesh->creaseLengths()->readable() )
	{
		numEdges += length - 1;
	}

	if( !numEdges )
	{
		return;
	}

	AtArray *idsArray = AiArrayAllocate( numEdges * 2, 1, AI_TYPE_UINT );
	AtArray *sharpnessesArray = AiArrayAllocate( numEdges, 1, AI_TYPE_FLOAT );

	auto id = mesh->creaseIds()->readable().begin();
	auto sharpness = mesh->creaseSharpnesses()->readable().begin();
	size_t arrayIndex = 0;
	for( int length : mesh->creaseLengths()->readable() )
	{
		for( int j = 0; j < length - 1; ++j )
		{
			AiArraySetFlt( sharpnessesArray, arrayIndex, *sharpness );
			AiArraySetUInt( idsArray, arrayIndex * 2, *id++ );
			AiArraySetUInt( idsArray, arrayIndex * 2 + 1, *id );
			arrayIndex++;
		}
		id++;
		sharpness++;
	}

	sharpness = mesh->cornerSharpnesses()->readable().begin();
	for( int cornerId : mesh->cornerIds()->readable() )
	{
		AiArraySetFlt( sharpnessesArray, arrayIndex, *sharpness++ );
		AiArraySetUInt( idsArray, arrayIndex * 2, cornerId );
		AiArraySetUInt( idsArray, arrayIndex * 2 + 1, cornerId );
		arrayIndex++;
	}

	AiNodeSetArray( node, g_creaseIdxsArnoldString, idsArray );
	AiNodeSetArray( node, g_creaseSharpnessArnoldString, sharpnessesArray );
}

AtNode *convertCommon( const IECoreScene::MeshPrimitive *mesh, AtUniverse *universe, const std::string &nodeName, const AtNode *parentNode = nullptr )
{

	// Make the result mesh and add topology

	AtNode *result = AiNode( universe, g_polymeshArnoldString, AtString( nodeName.c_str() ), parentNode );

	const std::vector<int> &verticesPerFace = mesh->verticesPerFace()->readable();
	AiNodeSetArray(
		result,
		g_nsidesArnoldString,
		AiArrayConvert( verticesPerFace.size(), 1, AI_TYPE_INT, (void *)&( verticesPerFace[0] ) )
	);

	const std::vector<int> &vertexIds = mesh->vertexIds()->readable();
	AiNodeSetArray(
		result,
		g_vidxsArnoldString,
		AiArrayConvert( vertexIds.size(), 1, AI_TYPE_INT, (void *)&( vertexIds[0] ) )
	);

	// Set subdivision

	if( mesh->interpolation()=="catmullClark" )
	{
		AiNodeSetStr( result, g_subdivTypeArnoldString, g_catclarkArnoldString );
		AiNodeSetBool( result, g_smoothingArnoldString, true );
		convertCornersAndCreases( mesh, result );
	}

	// Convert primitive variables.

	PrimitiveVariableMap variablesToConvert = mesh->variables;
	variablesToConvert.erase( "P" ); // These will be converted
	variablesToConvert.erase( "N" ); // outside of this function.

	// Find all UV sets and convert them explicitly.
	for( auto it = variablesToConvert.begin(); it != variablesToConvert.end(); )
	{
		if( const V2fVectorData *data = runTimeCast<const V2fVectorData>( it->second.data.get() ) )
		{
			if( data->getInterpretation() == GeometricData::UV )
			{
				::convertUVSet( it->first, it->second, vertexIds, result );
				it = variablesToConvert.erase( it );
			}
			else
			{
				++it;
			}
		}
		else
		{
			++it;
		}
	}

	// Finally, do a generic conversion of anything that remains.
	for( PrimitiveVariableMap::iterator it = variablesToConvert.begin(), eIt = variablesToConvert.end(); it != eIt; ++it )
	{
		ShapeAlgo::convertPrimitiveVariable( mesh, it->second, result, AtString( it->first.c_str() ) );
	}

	return result;
}

const V3fVectorData *normal( const IECoreScene::MeshPrimitive *mesh, PrimitiveVariable::Interpolation &interpolation )
{
	PrimitiveVariableMap::const_iterator it = mesh->variables.find( "N" );
	if( it == mesh->variables.end() )
	{
		return nullptr;
	}

	const V3fVectorData *n = runTimeCast<const V3fVectorData>( it->second.data.get() );
	if( !n )
	{
		msg( Msg::Warning, "MeshAlgo", boost::format( "Variable \"N\" has unsupported type \"%s\" (expected V3fVectorData)." ) % it->second.data->typeName() );
		return nullptr;
	}

	const PrimitiveVariable::Interpolation thisInterpolation = it->second.interpolation;
	if( interpolation != PrimitiveVariable::Invalid && thisInterpolation != interpolation )
	{
		msg( Msg::Warning, "MeshAlgo", "Variable \"N\" has inconsistent interpolation types - not generating normals." );
		return nullptr;
	}

	if( thisInterpolation != PrimitiveVariable::Varying && thisInterpolation != PrimitiveVariable::Vertex && thisInterpolation != PrimitiveVariable::FaceVarying )
	{
		msg( Msg::Warning, "MeshAlgo", "Variable \"N\" has unsupported interpolation type - not generating normals." );
		return nullptr;
	}

	interpolation = thisInterpolation;
	return n;
}

void convertNormalIndices( const IECoreScene::MeshPrimitive *mesh, AtNode *node, PrimitiveVariable::Interpolation interpolation )
{
	const IECore::IntVectorData* nIndices = mesh->variables.find( "N" )->second.indices.get();

	if( interpolation == PrimitiveVariable::FaceVarying )
	{
		if( !nIndices )
		{
			AiNodeSetArray(
				node,
				g_nidxsArnoldString,
				identityIndices( mesh->variableSize( PrimitiveVariable::FaceVarying ) )
			);
		}
		else
		{
			AiNodeSetArray(
				node,
				g_nidxsArnoldString,
				AiArrayConvert( nIndices->readable().size(), 1, AI_TYPE_INT, (void *)&( nIndices->readable()[0] ) )
			);
		}
	}
	else
	{
		const std::vector<int> &vertexIds = mesh->vertexIds()->readable();
		if( !nIndices )
		{
			AiNodeSetArray(
				node,
				g_nidxsArnoldString,
				AiArrayConvert( vertexIds.size(), 1, AI_TYPE_INT, (void *)&( vertexIds[0] ) )
			);
		}
		else
		{
			AtArray *result = AiArrayAllocate( vertexIds.size(), 1, AI_TYPE_UINT );
			for( size_t i=0; i < vertexIds.size(); ++i )
			{
				AiArraySetInt( result, i, nIndices->readable()[vertexIds[i]] );
			}
			AiNodeSetArray( node, g_nidxsArnoldString, result );
		}
	}
}


AtNode *convert( const IECoreScene::MeshPrimitive *mesh, AtUniverse *universe, const std::string &nodeName, const AtNode *parentNode )
{
	AtNode *result = convertCommon( mesh, universe, nodeName, parentNode );

	ShapeAlgo::convertP( mesh, result, g_vlistArnoldString );

	// add normals

	PrimitiveVariable::Interpolation nInterpolation = PrimitiveVariable::Invalid;
	if( const V3fVectorData *n = normal( mesh, nInterpolation ) )
	{
		AiNodeSetArray(
			result,
			g_nlistArnoldString,
			AiArrayConvert( n->readable().size(), 1, AI_TYPE_VECTOR, &n->readable().front() )
		);
		convertNormalIndices( mesh, result, nInterpolation );
		AiNodeSetBool( result, g_smoothingArnoldString, true );
	}

	return result;
}

AtNode *convert( const std::vector<const IECoreScene::MeshPrimitive *> &samples, float motionStart, float motionEnd, AtUniverse *universe, const std::string &nodeName, const AtNode *parentNode )
{
	AtNode *result = convertCommon( samples.front(), universe, nodeName, parentNode );

	std::vector<const IECoreScene::Primitive *> primitiveSamples( samples.begin(), samples.end() );
	ShapeAlgo::convertP( primitiveSamples, result, g_vlistArnoldString );

	// add normals

	vector<const Data *> nSamples;
	nSamples.reserve( samples.size() );
	PrimitiveVariable::Interpolation nInterpolation = PrimitiveVariable::Invalid;
	for( vector<const MeshPrimitive *>::const_iterator it = samples.begin(), eIt = samples.end(); it != eIt; ++it )
	{
		if( const V3fVectorData *n = normal( *it, nInterpolation ) )
		{
			nSamples.push_back( n );
		}
		else
		{
			break;
		}
	}

	if( nSamples.size() == samples.size() )
	{
		AiNodeSetArray(
			result,
			g_nlistArnoldString,
			ParameterAlgo::dataToArray( nSamples, AI_TYPE_VECTOR )
		);
		convertNormalIndices( samples.front(), result, nInterpolation );
		AiNodeSetBool( result, g_smoothingArnoldString, true );
	}

	// add time sampling

	AiNodeSetFlt( result, g_motionStartArnoldString, motionStart );
	AiNodeSetFlt( result, g_motionEndArnoldString, motionEnd );

	return result;
}

NodeAlgo::ConverterDescription<MeshPrimitive> g_description( ::convert, ::convert );

} // namespace
