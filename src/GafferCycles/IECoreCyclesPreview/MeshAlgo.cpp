//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2018, Alex Fuller. All rights reserved.
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

#include "GafferCycles/IECoreCyclesPreview/AttributeAlgo.h"
#include "GafferCycles/IECoreCyclesPreview/GeometryAlgo.h"

#include "IECoreScene/MeshNormalsOp.h"
#include "IECoreScene/MeshPrimitive.h"
#include "IECoreScene/MeshAlgo.h"

#include "IECore/Interpolator.h"
#include "IECore/SimpleTypedData.h"

// Cycles
#include "kernel/types.h"
#include "scene/geometry.h"
#include "scene/mesh.h"
#include "subd/dice.h"
#include "util/param.h"
#include "util/types.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace IECoreCycles;

namespace
{

std::array<std::string, 6> g_defautUVsetCandidates = { {
	"st_0",
	"st0",
	"uv_0",
	"uv0",
	"st",
	"uv",
} };

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

	interpolation = thisInterpolation;
	return n;
}

const BoolVectorData *getSmooth( const IECoreScene::MeshPrimitive *mesh )
{
	PrimitiveVariableMap::const_iterator it = mesh->variables.find( "_smooth" );
	if( it == mesh->variables.end() )
	{
		return nullptr;
	}

	if( it->second.interpolation != PrimitiveVariable::Uniform )
	{
		return nullptr;
	}

	const BoolVectorData *s = runTimeCast<const BoolVectorData>( it->second.data.get() );
	return s;
}

const IntVectorData *getFaceset( const IECoreScene::MeshPrimitive *mesh )
{
	PrimitiveVariableMap::const_iterator it = mesh->variables.find( "_facesetIndex" );
	if( it == mesh->variables.end() )
	{
		return nullptr;
	}

	if( it->second.interpolation != PrimitiveVariable::Uniform )
	{
		return nullptr;
	}

	const IntVectorData *f = runTimeCast<const IntVectorData>( it->second.data.get() );
	return f;
}

ccl::AttributeStandard normalAttributeStandard( PrimitiveVariable::Interpolation &interpolation )
{
#ifdef WITH_CYCLES_CORNER_NORMALS
	if( interpolation == PrimitiveVariable::Uniform || interpolation == PrimitiveVariable::FaceVarying )
	{
		return ccl::ATTR_STD_CORNER_NORMAL;
	}
	else
	{
		return ccl::ATTR_STD_VERTEX_NORMAL;
	}
#else
	return ccl::ATTR_STD_VERTEX_NORMAL;
#endif
}

void convertN( const IECoreScene::MeshPrimitive *mesh, const V3fVectorData *normalData, ccl::Attribute *attr, PrimitiveVariable::Interpolation interpolation )
{
	const size_t numFaces = mesh->numFaces();
	const std::vector<int> &vertsPerFace = mesh->verticesPerFace()->readable();
	const vector<Imath::V3f> &normals = normalData->readable();
	const IECore::IntVectorData* nIndices = mesh->variables.find( "N" )->second.indices.get();
	ccl::float3 *cdata = attr->data_float3();

	if( !nIndices )
	{
		if( interpolation == PrimitiveVariable::Constant )
		{
			for( size_t i = 0; i < normals.size(); ++i )
			{
				*(cdata++) = ccl::make_float3( normals[0].x, normals[0].y, normals[0].z );
			}
		}
		else if( interpolation == PrimitiveVariable::Uniform )
		{
			for( size_t i = 0; i < numFaces; ++i )
			{
				for( int j = 0; j < vertsPerFace[i]; ++j )
				{
					*(cdata++) = ccl::make_float3( normals[i].x, normals[i].y, normals[i].z );
				}
			}
		}
#ifdef WITH_CYCLES_CORNER_NORMALS
		else if( interpolation == PrimitiveVariable::FaceVarying )
		{
			for( size_t i = 0; i < numFaces; ++i )
			{
				for( size_t j = 0; j < vertsPerFace[i]; ++j, ++vertex )
				{
					*(cdata++) = ccl::make_float3( normals[vertex].x, normals[vertex].y, normals[vertex].z );
				}
			}
		}
#endif // WITH_CYCLES_CORNER_NORMALS
		else // per-vertex
		{
			for( size_t i = 0; i < normals.size(); ++i )
			{
				*(cdata++) = ccl::make_float3( normals[i].x, normals[i].y, normals[i].z );
			}
		}
	}
	else
	{
		const vector<int> indices = nIndices->readable();

		size_t numVerts = 0;
		for( auto vert : vertsPerFace )
		{
			numVerts += vert;
		}

		if( ( indices.size() < numVerts ) && interpolation != PrimitiveVariable::Vertex )
		{
			msg(
				Msg::Warning, "IECoreCycles::MeshAlgo::convertN",
				boost::format( "Normal has an invalid index size \"%d\" to vertex size \"%d\"." ) % indices.size() % numVerts
			);
			return;
		}

		if( interpolation == PrimitiveVariable::Uniform )
		{
			for( size_t i = 0; i < numFaces; ++i )
			{
				for( int j = 0; j < vertsPerFace[i]; ++j )
				{
					*(cdata++) = ccl::make_float3( normals[indices[i]].x, normals[indices[i]].y, normals[indices[i]].z );
				}
			}
		}
#ifdef WITH_CYCLES_CORNER_NORMALS
		else if( interpolation == PrimitiveVariable::FaceVarying )
		{
			for( size_t i = 0; i < numFaces; ++i )
			{
				for( size_t j = 0; j < vertsPerFace[i]; ++j, ++vertex )
				{
					*(cdata++) = ccl::make_float3( normals[indices[vertex]].x, normals[indices[vertex]].y, normals[indices[vertex]].z );
				}
			}
		}
#endif // WITH_CYCLES_CORNER_NORMALS
		else // per-vertex
		{
			for( size_t i = 0; i < normals.size(); ++i )
			{
				*(cdata++) = ccl::make_float3( normals[indices[i]].x, normals[indices[i]].y, normals[indices[i]].z );
			}
		}
	}

}

void convertUVSet( const string &uvSet, const IECoreScene::PrimitiveVariable &uvVariable, const IECoreScene::MeshPrimitive *mesh, ccl::AttributeSet &attributes, bool subdivision_uvs, bool defaultUV )//, ccl::Mesh *cmesh )
{
	size_t numFaces = mesh->numFaces();
	const V2fVectorData *uvData = runTimeCast<V2fVectorData>( uvVariable.data.get() );

	if( !uvData )
	{
		return;
	}

	if( uvVariable.interpolation != PrimitiveVariable::Varying && uvVariable.interpolation != PrimitiveVariable::Vertex && uvVariable.interpolation != PrimitiveVariable::FaceVarying )
	{
		msg(
			Msg::Warning, "IECoreCycles::MeshAlgo::convertUVSet",
			boost::format( "Variable \"%s\" has an invalid interpolation type - not generating uvs." ) % uvSet
		);
		return;
	}

	const vector<Imath::V2f> &uvs = uvData->readable();
	const std::vector<int> &vertexIds = mesh->vertexIds()->readable();

	ccl::Attribute *uv_attr = nullptr;
	if( defaultUV )
		uv_attr = attributes.add( ccl::ATTR_STD_UV, ccl::ustring(uvSet.c_str()) );
	else
		uv_attr = attributes.add( ccl::ustring(uvSet.c_str()), ccl::TypeFloat2, ccl::ATTR_ELEMENT_CORNER );
	ccl::float2 *fdata = uv_attr->data_float2();

	if( subdivision_uvs )
		uv_attr->flags |= ccl::ATTR_SUBDIVIDED;

	// We need to know how many verts there are
	const vector<int> &vertsPerFace = mesh->verticesPerFace()->readable();

	size_t vertex = 0;
	if( uvVariable.indices )
	{
		const vector<int> &indices = uvVariable.indices->readable();

		size_t numVerts = 0;
		for( auto vert : vertsPerFace )
		{
			numVerts += vert;
		}

		if( ( indices.size() < numVerts ) && uvVariable.interpolation != PrimitiveVariable::Vertex )
		{
			msg(
				Msg::Warning, "IECoreCycles::MeshAlgo::convertUVSet",
				boost::format( "Variable \"%s\" has an invalid index size \"%d\" to vertex size \"%d\"." ) % uvSet % indices.size() % numVerts
			);
			attributes.remove( uv_attr );
			return;
		}

		if( uvVariable.interpolation == PrimitiveVariable::Vertex )
		{
			for( size_t i = 0; i < numFaces; ++i )
			{
				for( int j = 0; j < vertsPerFace[i]; ++j, ++vertex )
				{
					*(fdata++) = ccl::make_float2(uvs[indices[vertexIds[vertex]]].x, uvs[indices[vertexIds[vertex]]].y);
				}
			}
		}
		else // FaceVarying/Varying
		{
			for( size_t i = 0; i < numFaces; ++i )
			{
				for( int j = 0; j < vertsPerFace[i]; ++j, ++vertex )
				{
					*(fdata++) = ccl::make_float2(uvs[indices[vertex]].x, uvs[indices[vertex]].y);
				}
			}
		}
	}
	else
	{
		if( uvVariable.interpolation == PrimitiveVariable::Vertex )
		{
			for( size_t i = 0; i < numFaces; ++i )
			{
				for( int j = 0; j < vertsPerFace[i]; ++j, ++vertex )
				{
					*(fdata++) = ccl::make_float2(uvs[vertexIds[vertex]].x, uvs[vertexIds[vertex]].y);
				}
			}
		}
		else // FaceVarying/Varying
		{
			for( size_t i = 0; i < numFaces; ++i )
			{
				for( int j = 0; j < vertsPerFace[i]; ++j, ++vertex )
				{
					*(fdata++) = ccl::make_float2(uvs[vertex].x, uvs[vertex].y);
				}
			}
		}
	}
}

ccl::Mesh *convertCommon( const IECoreScene::MeshPrimitive *mesh )
{
	assert( mesh->typeId() == IECoreScene::MeshPrimitive::staticTypeId() );
	ccl::Mesh *cmesh = new ccl::Mesh();

	bool subdivision = false;
	bool triangles = ( mesh->maxVerticesPerFace() == 3 ) ? true : false;

	// If we need to convert
	MeshPrimitivePtr trimesh;

	// Smooth/hard normals
	bool smooth = true;
	PrimitiveVariable::Interpolation sInterpolation = PrimitiveVariable::Invalid;
	PrimitiveVariableMap::const_iterator sIt = mesh->variables.find( "_smooth" );
	if( sIt != mesh->variables.end() )
	{
		if( sIt->second.interpolation == PrimitiveVariable::Constant ||
			sIt->second.interpolation == PrimitiveVariable::Uniform )
		{
			sInterpolation = sIt->second.interpolation;
		}
		if( sInterpolation == PrimitiveVariable::Constant )
		{
			if( const BoolData *data = runTimeCast<const BoolData>( sIt->second.data.get() ) )
			{
				smooth = data->readable();
			}
		}
	}

	if( ( mesh->interpolation() == "catmullClark" ) )//|| !triangles )
	{
		const size_t numFaces = mesh->numFaces();
		const V3fVectorData *p = mesh->variableData<V3fVectorData>( "P", PrimitiveVariable::Vertex );
		const vector<Imath::V3f> &points = p->readable();
		const vector<int> &vertexIds = mesh->vertexIds()->readable();
		const size_t numVerts = points.size();
		subdivision = true;
		cmesh->set_subdivision_type( (mesh->interpolation() == "catmullClark") ? ccl::Mesh::SUBDIVISION_CATMULL_CLARK : ccl::Mesh::SUBDIVISION_LINEAR );
		const BoolVectorData *s = getSmooth( mesh );
		const IntVectorData *f = getFaceset( mesh );

		cmesh->reserve_mesh( numVerts, numFaces );
		for( size_t i = 0; i < numVerts; i++ )
			cmesh->add_vertex( ccl::make_float3( points[i].x, points[i].y, points[i].z ) );

		const std::vector<int> &vertsPerFace = mesh->verticesPerFace()->readable();
		size_t ngons = 0;
		size_t ncorners = 0;
		for( size_t i = 0; i < vertsPerFace.size(); i++ )
		{
			ngons += ( vertsPerFace[i] == 4 ) ? 0 : 1;
			ncorners += vertsPerFace[i];
		}
		cmesh->reserve_subd_faces(numFaces, ngons, ncorners);

		int indexOffset = 0;
		for( size_t i = 0; i < vertsPerFace.size(); i++ )
		{
			cmesh->add_subd_face( const_cast<int*>(&vertexIds[indexOffset]), vertsPerFace[i],
				f ? f->readable()[i] : 0, s ? s->readable()[i] : smooth ); // Last two args are shader sets and smooth
			indexOffset += vertsPerFace[i];
		}

		// Creases
		size_t numEdges = mesh->cornerIds()->readable().size();
		for( int length : mesh->creaseLengths()->readable() )
		{
			numEdges += length - 1;
		}

		if( numEdges )
		{
			cmesh->reserve_subd_creases( numEdges );

			auto id = mesh->creaseIds()->readable().begin();
			auto sharpness = mesh->creaseSharpnesses()->readable().begin();
			for( int length : mesh->creaseLengths()->readable() )
			{
				for( int j = 0; j < length - 1; ++j )
				{
					int v0 = *id++;
					int v1 = *id;
					float weight = (*sharpness) * 0.1f;
					cmesh->add_edge_crease( v0, v1, weight );
				}
				id++;
				sharpness++;
			}

			sharpness = mesh->cornerSharpnesses()->readable().begin();
			for( int cornerId : mesh->cornerIds()->readable() )
			{
				cmesh->add_vertex_crease( cornerId, (*sharpness) * 0.1f );
				sharpness++;
			}
		}
	}
	else
	{
		cmesh->set_subdivision_type( (mesh->interpolation() == "linear") ? ccl::Mesh::SUBDIVISION_LINEAR : ccl::Mesh::SUBDIVISION_NONE );

		if( !triangles )
		{
			// triangulate primitive
			trimesh = IECoreScene::MeshAlgo::triangulate( mesh );
			const V3fVectorData *p = trimesh->variableData<V3fVectorData>( "P", PrimitiveVariable::Vertex );
			const vector<Imath::V3f> &points = p->readable();
			const size_t numVerts = points.size();
			const std::vector<int> &triVertexIds = trimesh->vertexIds()->readable();
			const BoolVectorData *s = getSmooth( trimesh.get() );
			const IntVectorData *f = getFaceset( trimesh.get() );

			const size_t triNumFaces = trimesh->numFaces();
			cmesh->reserve_mesh( numVerts, triNumFaces );

			for( size_t i = 0; i < numVerts; i++ )
				cmesh->add_vertex( ccl::make_float3( points[i].x, points[i].y, points[i].z ) );

			int faceOffset = 0;
			for( size_t i = 0; i < triVertexIds.size(); i+= 3, ++faceOffset )
				cmesh->add_triangle( triVertexIds[i], triVertexIds[i+1], triVertexIds[i+2],
					f ? f->readable()[faceOffset] : 0, s ? s->readable()[faceOffset] : smooth ); // Last two args are shader sets and smooth
		}
		else
		{
			const size_t numFaces = mesh->numFaces();
			const V3fVectorData *p = mesh->variableData<V3fVectorData>( "P", PrimitiveVariable::Vertex );
			const vector<Imath::V3f> &points = p->readable();
			const vector<int> &vertexIds = mesh->vertexIds()->readable();
			const size_t numVerts = points.size();
			cmesh->reserve_mesh(numVerts, numFaces);
			const BoolVectorData *s = getSmooth( mesh );
			const IntVectorData *f = getFaceset( mesh );

			for( size_t i = 0; i < numVerts; i++ )
				cmesh->add_vertex( ccl::make_float3( points[i].x, points[i].y, points[i].z ) );

			int faceOffset = 0;
			for( size_t i = 0; i < vertexIds.size(); i+= 3, ++faceOffset )
				cmesh->add_triangle( vertexIds[i], vertexIds[i+1], vertexIds[i+2],
					f ? f->readable()[faceOffset] : 0, s ? s->readable()[faceOffset] : smooth ); // Last two args are shader sets and smooth
		}
	}

	// Primitive Variables are Attributes in Cycles
	ccl::AttributeSet& attributes = (subdivision) ? cmesh->subd_attributes : cmesh->attributes;

	// Convert Normals
	PrimitiveVariable::Interpolation nInterpolation = PrimitiveVariable::Invalid;
	if( ( !triangles ) && ( mesh->interpolation() == "catmullClark" ) )
	{
		if( const V3fVectorData *normals = normal( mesh, nInterpolation ) )
		{
			ccl::Attribute *attr_N = attributes.add( normalAttributeStandard( nInterpolation ) );
			convertN( mesh, normals, attr_N, nInterpolation );
		}
	}
	else if( !triangles )
	{
		if( const V3fVectorData *normals = normal( trimesh.get(), nInterpolation ) )
		{
			ccl::Attribute *attr_N = attributes.add( normalAttributeStandard( nInterpolation ) );
			convertN( trimesh.get(), normals, attr_N, nInterpolation );
		}
		else
		{
			IECoreScene::MeshNormalsOpPtr normalOp = new IECoreScene::MeshNormalsOp();
			normalOp->inputParameter()->setValue( trimesh );
			normalOp->copyParameter()->setTypedValue( false );
			normalOp->operate();
			if( const V3fVectorData *normals = normal( trimesh.get(), nInterpolation ) )
			{
				ccl::Attribute *attr_N = attributes.add( normalAttributeStandard( nInterpolation ) );
				convertN( trimesh.get(), normals, attr_N, nInterpolation );
			}
		}
	}
	else
	{
		if( const V3fVectorData *normals = normal( mesh, nInterpolation ) )
		{
			ccl::Attribute *attr_N = attributes.add( normalAttributeStandard( nInterpolation ) );
			convertN( mesh, normals, attr_N, nInterpolation );
		}
		else if( mesh->interpolation() != "catmullClark" )
		{
			IECoreScene::MeshPrimitivePtr normalmesh = mesh->copy();
			IECoreScene::MeshNormalsOpPtr normalOp = new IECoreScene::MeshNormalsOp();
			normalOp->inputParameter()->setValue( normalmesh );
			normalOp->copyParameter()->setTypedValue( false );
			normalOp->operate();
			if( const V3fVectorData *normals = normal( normalmesh.get(), nInterpolation ) )
			{
				ccl::Attribute *attr_N = attributes.add( normalAttributeStandard( nInterpolation ) );
				convertN( normalmesh.get(), normals, attr_N, nInterpolation );
			}
		}
	}

	// Convert primitive variables.
	PrimitiveVariableMap variablesToConvert;
	if( subdivision || triangles )
		variablesToConvert = mesh->variables;
	else
		variablesToConvert = trimesh->variables;
	variablesToConvert.erase( "P" ); // P is already done.
	variablesToConvert.erase( "N" ); // As well as N.
	variablesToConvert.erase( "_smooth" ); // Was already processed (if it existed)
	variablesToConvert.erase( "_facesetIndex" );

	// Find all UV sets and convert them explicitly.
	PrimitiveVariableMap uvsets;
	for( auto it = variablesToConvert.begin(); it != variablesToConvert.end(); )
	{
		if( const V2fVectorData *data = runTimeCast<const V2fVectorData>( it->second.data.get() ) )
		{
			if( ( data->getInterpretation() == GeometricData::UV ) ||
				( data->getInterpretation() == GeometricData::Numeric ) )
			{
				uvsets[it->first] = it->second;
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
	// Find the best candidate for the first UVset.
	int rank = -1;
	for( auto it = uvsets.begin(); it != uvsets.end(); )
	{
		for( int i = 0; i < (int)g_defautUVsetCandidates.size(); ++i )
		{
			if( it->first == g_defautUVsetCandidates[i] )
			{
				if( i > rank )
				{
					rank = i;
				}
			}
		}
		++it;
	}
	if( rank != -1 )
	{
		convertUVSet( g_defautUVsetCandidates[rank], uvsets[g_defautUVsetCandidates[rank]], ( subdivision || triangles ) ? mesh : trimesh.get(), attributes, subdivision, true );
		uvsets.erase( g_defautUVsetCandidates[rank] );
	}

	for( auto it = uvsets.begin(); it != uvsets.end(); )
	{
		// If we didn't find a default UVset, the first one we find will be the one.
		convertUVSet( it->first, it->second, ( subdivision || triangles ) ? mesh : trimesh.get(), attributes, subdivision, (rank == -1) ? true : false );
		// Just set rank to not be -1 so that the next UVs are not converted as a default one.
		rank = 0;
		uvsets.erase( it );
		++it;
	}

	// Finally, do a generic conversion of anything that remains.
	for( PrimitiveVariableMap::iterator it = variablesToConvert.begin(), eIt = variablesToConvert.end(); it != eIt; ++it )
	{
		AttributeAlgo::convertPrimitiveVariable( it->first, it->second, attributes );
	}
	return cmesh;
}

ccl::Geometry *convert( const IECoreScene::MeshPrimitive *mesh, const std::string &nodeName, ccl::Scene *scene )
{
	ccl::Mesh *cmesh = convertCommon( mesh );
	cmesh->name = ccl::ustring( nodeName.c_str() );
	return cmesh;
}

ccl::Geometry *convert( const std::vector<const IECoreScene::MeshPrimitive *> &meshes, const std::vector<float> &times, const int frameIdx, const std::string &nodeName, ccl::Scene *scene )
{
	const int numSamples = meshes.size();

	ccl::Mesh *cmesh = nullptr;
	std::vector<const IECoreScene::MeshPrimitive *> samples;
	IECoreScene::MeshPrimitivePtr midMesh;

	if( frameIdx != -1 ) // Start/End frames
	{
		cmesh = convertCommon(meshes[frameIdx]);

		if( numSamples == 2 ) // Make sure we have 3 samples
		{
			const V3fVectorData *p1 = meshes[0]->variableData<V3fVectorData>( "P", PrimitiveVariable::Vertex );
			const V3fVectorData *p2 = meshes[1]->variableData<V3fVectorData>( "P", PrimitiveVariable::Vertex );
			if( p1 && p2 )
			{
				midMesh = meshes[frameIdx]->copy();
				V3fVectorData *midP = midMesh->variableData<V3fVectorData>( "P", PrimitiveVariable::Vertex );
				IECore::LinearInterpolator<std::vector<V3f>>()( p1->readable(), p2->readable(), 0.5f, midP->writable() );

				PrimitiveVariable::Interpolation nInterpolation = PrimitiveVariable::Invalid;
				if( normal( meshes[0], nInterpolation ) )
				{
					const V3fVectorData *n1 = meshes[0]->variableData<V3fVectorData>( "N", nInterpolation );
					const V3fVectorData *n2 = meshes[1]->variableData<V3fVectorData>( "N", nInterpolation );
					V3fVectorData *midN = midMesh->variableData<V3fVectorData>( "N", nInterpolation );
					IECore::LinearInterpolator<std::vector<V3f>>()( n1->readable(), n2->readable(), 0.5f, midN->writable() );
				}

				samples.push_back( midMesh.get() );
			}
		}

		for( int i = 0; i < numSamples; ++i )
		{
			if( i == frameIdx )
				continue;
			samples.push_back( meshes[i] );
		}
	}
	else if( numSamples % 2 ) // Odd numSamples
	{
		int _frameIdx = numSamples / 2;
		cmesh = convertCommon(meshes[_frameIdx]);

		for( int i = 0; i < numSamples; ++i )
		{
			if( i == _frameIdx )
				continue;
			samples.push_back( meshes[i] );
		}
	}
	else // Even numSamples
	{
		int _frameIdx = numSamples / 2 - 1;
		const V3fVectorData *p1 = meshes[_frameIdx]->variableData<V3fVectorData>( "P", PrimitiveVariable::Vertex );
		const V3fVectorData *p2 = meshes[_frameIdx+1]->variableData<V3fVectorData>( "P", PrimitiveVariable::Vertex );
		if( p1 && p2 )
		{
			midMesh = meshes[_frameIdx]->copy();
			V3fVectorData *midP = midMesh->variableData<V3fVectorData>( "P", PrimitiveVariable::Vertex );
			IECore::LinearInterpolator<std::vector<V3f>>()( p1->readable(), p2->readable(), 0.5f, midP->writable() );

			PrimitiveVariable::Interpolation nInterpolation = PrimitiveVariable::Invalid;
			if( normal( meshes[0], nInterpolation ) )
			{
				const V3fVectorData *n1 = meshes[0]->variableData<V3fVectorData>( "N", nInterpolation );
				const V3fVectorData *n2 = meshes[1]->variableData<V3fVectorData>( "N", nInterpolation );
				V3fVectorData *midN = midMesh->variableData<V3fVectorData>( "N", nInterpolation );
				IECore::LinearInterpolator<std::vector<V3f>>()( n1->readable(), n2->readable(), 0.5f, midN->writable() );
			}

			cmesh = convertCommon( midMesh.get() );
		}

		for( int i = 0; i < numSamples; ++i )
		{
			samples.push_back( meshes[i] );
		}
	}

	// Add the motion position/normal attributes
	cmesh->set_use_motion_blur( true );
	cmesh->set_motion_steps( samples.size() + 1 );
	ccl::Attribute *attr_mP = cmesh->attributes.add( ccl::ATTR_STD_MOTION_VERTEX_POSITION, ccl::ustring("motion_P") );
	ccl::float3 *mP = attr_mP->data_float3();
	ccl::Attribute *attr_mN = nullptr;
	PrimitiveVariable::Interpolation nInterpolation = PrimitiveVariable::Invalid;
	if( normal( meshes[0], nInterpolation ) )
	{
		if( nInterpolation == PrimitiveVariable::Vertex )
		{
			attr_mN = cmesh->attributes.add( ccl::ATTR_STD_MOTION_VERTEX_NORMAL, ccl::ustring("motion_N") );
		}
#ifdef WITH_CYCLES_CORNER_NORMALS
		else if( nInterpolation == PrimitiveVariable::FaceVarying )
		{
			attr_mN = cmesh->attributes.add( ccl::ATTR_STD_MOTION_CORNER_NORMAL, ccl::ustring("motion_Nc") );
		}
#endif
		else
		{
			msg( Msg::Warning, "IECoreCyles::MeshAlgo::convert", "Variable \"N\" has unsupported interpolation type for motion steps - not generating normals." );
		}
	}

	for( size_t i = 0; i < samples.size(); ++i )
	{
		PrimitiveVariableMap::const_iterator pIt = samples[i]->variables.find( "P" );
		if( pIt != samples[i]->variables.end() )
		{
			const V3fVectorData *p = runTimeCast<const V3fVectorData>( pIt->second.data.get() );
			if( p )
			{
				PrimitiveVariable::Interpolation pInterpolation = pIt->second.interpolation;
				if( pInterpolation == PrimitiveVariable::Varying || pInterpolation == PrimitiveVariable::Vertex || pInterpolation == PrimitiveVariable::FaceVarying )
				{
					// Vertex positions
					const V3fVectorData *p = samples[i]->variableData<V3fVectorData>( "P", PrimitiveVariable::Vertex );
					const std::vector<V3f> &points = p->readable();
					size_t numVerts = p->readable().size();

					for( size_t j = 0; j < numVerts; ++j, ++mP )
						*mP = ccl::make_float3( points[j].x, points[j].y, points[j].z );
				}
				else
				{
					msg( Msg::Warning, "IECoreCyles::MeshAlgo::convert", "Variable \"Position\" has unsupported interpolation type - not generating sampled Position." );
					cmesh->attributes.remove( attr_mP );
					cmesh->set_motion_steps( 0 );
					cmesh->set_use_motion_blur( false );
				}
			}
			else
			{
				msg( Msg::Warning, "IECoreCyles::MeshAlgo::convert", boost::format( "Variable \"Position\" has unsupported type \"%s\" (expected V3fVectorData)." ) % pIt->second.data->typeName() );
				cmesh->attributes.remove( attr_mP );
				cmesh->set_motion_steps( 0) ;
				cmesh->set_use_motion_blur( true );
			}
		}

		if( attr_mN )
		{
			if( const V3fVectorData *normals = normal( samples[i], nInterpolation ) )
			{
				convertN( samples[i], normals, attr_mN, nInterpolation );
			}
		}
	}

	cmesh->name = ccl::ustring( nodeName.c_str() );
	return cmesh;
}

GeometryAlgo::ConverterDescription<MeshPrimitive> g_description( convert, convert );

} // namespace
