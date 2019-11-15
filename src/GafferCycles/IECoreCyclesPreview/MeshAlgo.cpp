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

#include "GafferCycles/IECoreCyclesPreview/MeshAlgo.h"

#include "GafferCycles/IECoreCyclesPreview/AttributeAlgo.h"
#include "GafferCycles/IECoreCyclesPreview/ObjectAlgo.h"

#include "IECoreScene/MeshPrimitive.h"
#include "IECoreScene/MeshAlgo.h"

#include "IECore/SimpleTypedData.h"

// Cycles
#include "kernel/kernel_types.h"
#include "render/mesh.h"
#include "subd/subd_dice.h"
#include "util/util_param.h"
#include "util/util_types.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace IECoreCycles;

namespace
{

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

	if( thisInterpolation != PrimitiveVariable::Varying && thisInterpolation != PrimitiveVariable::Vertex ) //&& thisInterpolation != PrimitiveVariable::FaceVarying )
	{
		msg( Msg::Warning, "MeshAlgo", "Variable \"N\" has unsupported interpolation type - not generating normals." );
		return nullptr;
	}

	interpolation = thisInterpolation;
	return n;
}

void convertN( const IECoreScene::MeshPrimitive *mesh, const V3fVectorData *normalData, ccl::Attribute *attr, PrimitiveVariable::Interpolation interpolation )
{
	const size_t numFaces = mesh->numFaces();
	const std::vector<int> &vertsPerFace = mesh->verticesPerFace()->readable();
	const vector<Imath::V3f> &normals = normalData->readable();
	ccl::float3 *cdata = attr->data_float3();
	size_t vertex = 0;
	if( interpolation == PrimitiveVariable::Uniform )
	{
		for( size_t i = 0; i < numFaces; ++i )
		{
			*(cdata++) = ccl::make_float3( normals[i].x, normals[i].y, normals[i].z );
		}
	}
	else if( interpolation == PrimitiveVariable::FaceVarying )
	{
		const std::vector<int> &vertexIds = mesh->vertexIds()->readable();
		for( size_t i = 0; i < numFaces; ++i )
		{
			for( size_t j = 0; j < vertsPerFace[i]; ++j, ++vertex )
			{
				*(cdata++) = ccl::make_float3( normals[vertex].x, normals[vertex].y, normals[vertex].z );
			}
		}
	}
	else
	{
		for( size_t i = 0; i < normals.size(); ++i )
		{
			*(cdata++) = ccl::make_float3( normals[i].x, normals[i].y, normals[i].z );
		}
	}
}

void convertUVSet( const string &uvSet, const IECoreScene::PrimitiveVariable &uvVariable, const IECoreScene::MeshPrimitive *mesh, ccl::AttributeSet &attributes, bool subdivision_uvs )
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

	// Default UVs are named "uv"
	ccl::Attribute *uv_attr = nullptr;
	if( uvSet == "uv" )
		uv_attr = attributes.add( ccl::ATTR_STD_UV, ccl::ustring(uvSet.c_str()) );
	else
		uv_attr = attributes.add( ccl::ustring(uvSet.c_str()), ccl::TypeFloat2, ccl::ATTR_ELEMENT_CORNER );
	ccl::float2 *fdata = uv_attr->data_float2();

	if( subdivision_uvs )
		uv_attr->flags |= ccl::ATTR_SUBDIVIDED;

	// We need to know how many verts there are
	const vector<int> &vertsPerFace = mesh->verticesPerFace()->readable();

	size_t vertex = 0;
	for( size_t i = 0; i < numFaces; ++i )
	{
		if( uvVariable.indices )
		{
			const vector<int> &indices = uvVariable.indices->readable();
			for( size_t j = 0; j < vertsPerFace[i]; ++j, ++vertex )
			{
				*(fdata++) = ccl::make_float2(uvs[indices[vertex]].x, uvs[indices[vertex]].y);
			}
		}
		else if( uvVariable.interpolation == PrimitiveVariable::FaceVarying )
		{
			for( size_t j = 0; j < vertsPerFace[i]; ++j, ++vertex )
			{
				*(fdata++) = ccl::make_float2(uvs[vertexIds[vertex]].x, uvs[vertexIds[vertex]].y);
			}
		}
		else
		{
			for( size_t j = 0; j < vertsPerFace[i]; ++j, ++vertex )
			{
				*(fdata++) = ccl::make_float2(uvs[vertex].x, uvs[vertex].y);
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

	if( ( mesh->interpolation() == "catmullClark" ) )//|| !triangles )
	{
		const size_t numFaces = mesh->numFaces();
		const V3fVectorData *p = mesh->variableData<V3fVectorData>( "P", PrimitiveVariable::Vertex );
		const vector<Imath::V3f> &points = p->readable();
		const vector<int> &vertexIds = mesh->vertexIds()->readable();
		const size_t numVerts = points.size();
		subdivision = true;
		cmesh->subdivision_type = (mesh->interpolation() == "catmullClark") ? ccl::Mesh::SUBDIVISION_CATMULL_CLARK : ccl::Mesh::SUBDIVISION_LINEAR;

		const std::vector<int> &vertsPerFace = mesh->verticesPerFace()->readable();
		size_t ngons = 0;
		size_t ncorners = 0;
		for( int i = 0; i < vertsPerFace.size(); i++ )
		{
			ngons += ( vertsPerFace[i] == 4 ) ? 0 : 1;
			ncorners += vertsPerFace[i];
		}
		cmesh->reserve_mesh( numVerts, numFaces );
		cmesh->reserve_subd_faces(numFaces, ngons, ncorners);

		for( size_t i = 0; i < numVerts; i++ )
			cmesh->add_vertex( ccl::make_float3( points[i].x, points[i].y, points[i].z ) );

		int index_offset = 0;
		for( size_t i = 0; i < vertsPerFace.size(); i++ )
		{
			cmesh->add_subd_face( const_cast<int*>(&vertexIds[index_offset]), vertsPerFace[i], 0, true ); // Last two args are shader sets and smooth
			index_offset += vertsPerFace[i];
		}
	}
	else
	{
		cmesh->subdivision_type = (mesh->interpolation() == "linear") ? ccl::Mesh::SUBDIVISION_LINEAR : ccl::Mesh::SUBDIVISION_NONE;

		if( !triangles )
		{
			// triangulate primitive
			trimesh = IECoreScene::MeshAlgo::triangulate( mesh );
			const size_t numFaces = trimesh->numFaces();
			const V3fVectorData *p = trimesh->variableData<V3fVectorData>( "P", PrimitiveVariable::Vertex );
			const vector<Imath::V3f> &points = p->readable();
			const size_t numVerts = points.size();
			const std::vector<int> &triVertexIds = trimesh->vertexIds()->readable();

			const size_t triNumFaces = trimesh->numFaces();
			cmesh->reserve_mesh( numVerts, triNumFaces );

			for( size_t i = 0; i < numVerts; i++ )
				cmesh->add_vertex( ccl::make_float3( points[i].x, points[i].y, points[i].z ) );

			for( size_t i = 0; i < triVertexIds.size(); i+= 3 )
				cmesh->add_triangle( triVertexIds[i], triVertexIds[i+1], triVertexIds[i+2], 0, true ); // Last two args are shader sets and smooth
		}
		else
		{
			const size_t numFaces = mesh->numFaces();
			const V3fVectorData *p = mesh->variableData<V3fVectorData>( "P", PrimitiveVariable::Vertex );
			const vector<Imath::V3f> &points = p->readable();
			const vector<int> &vertexIds = mesh->vertexIds()->readable();
			const size_t numVerts = points.size();
			cmesh->reserve_mesh(numVerts, numFaces);

			for( size_t i = 0; i < numVerts; i++ )
				cmesh->add_vertex( ccl::make_float3( points[i].x, points[i].y, points[i].z ) );

			for( size_t i = 0; i < vertexIds.size(); i+= 3 )
				cmesh->add_triangle( vertexIds[i], vertexIds[i+1], vertexIds[i+2], 0, true ); // Last two args are shader sets and smooth
		}
	}

	// TODO: Maybe move this to attibutes so it can be shared between meshes?
	if( ( subdivision ) && ( cmesh->subdivision_type != ccl::Mesh::SUBDIVISION_NONE ) && ( !cmesh->subd_params ) )
		cmesh->subd_params = new ccl::SubdParams( cmesh );

	// Primitive Variables are Attributes in Cycles
	ccl::AttributeSet& attributes = (subdivision) ? cmesh->subd_attributes : cmesh->attributes;

	// Convert Normals
	PrimitiveVariable::Interpolation nInterpolation = PrimitiveVariable::Invalid;
	if( const V3fVectorData *normals = normal( mesh, nInterpolation ) )
	{
		ccl::Attribute *attr_N = attributes.add( nInterpolation == PrimitiveVariable::Uniform ? ccl::ATTR_STD_FACE_NORMAL : ccl::ATTR_STD_VERTEX_NORMAL, ccl::ustring("N") );
		convertN( mesh, normals, attr_N, nInterpolation );
	}

	// Convert primitive variables.
	PrimitiveVariableMap variablesToConvert;
	if( subdivision || triangles )
		variablesToConvert = mesh->variables;
	else
		variablesToConvert = trimesh->variables;
	variablesToConvert.erase( "P" ); // P is already done.
	variablesToConvert.erase( "N" ); // As well as N.

	// Find all UV sets and convert them explicitly.
	for( auto it = variablesToConvert.begin(); it != variablesToConvert.end(); )
	{
		if( const V2fVectorData *data = runTimeCast<const V2fVectorData>( it->second.data.get() ) )
		{
			if( data->getInterpretation() == GeometricData::UV )
			{
				if ( subdivision || triangles )
					convertUVSet( it->first, it->second, mesh, attributes, subdivision );
				else
					convertUVSet( it->first, it->second, trimesh.get(), attributes, subdivision );
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
		AttributeAlgo::convertPrimitiveVariable( it->first, it->second, attributes );
	}
	return cmesh;
}

ObjectAlgo::ConverterDescription<MeshPrimitive> g_description( IECoreCycles::MeshAlgo::convert, IECoreCycles::MeshAlgo::convert );

} // namespace

//////////////////////////////////////////////////////////////////////////
// Implementation of public API
//////////////////////////////////////////////////////////////////////////

namespace IECoreCycles

{

namespace MeshAlgo

{

ccl::Object *convert( const IECoreScene::MeshPrimitive *mesh, const std::string &nodeName )
{
	ccl::Object *cobject = new ccl::Object();
	cobject->mesh = convertCommon(mesh);
	cobject->name = ccl::ustring(nodeName.c_str());
	return cobject;
}

ccl::Object *convert( const std::vector<const IECoreScene::MeshPrimitive *> &meshes, const std::string &nodeName )
{
	ccl::Mesh *cmesh = convertCommon(meshes[0]);

	// Add the motion position/normal attributes
	cmesh->motion_steps = meshes.size();
	ccl::Attribute *attr_mP = cmesh->attributes.add( ccl::ATTR_STD_MOTION_VERTEX_POSITION, ccl::ustring("motion_P") );
	ccl::float3 *mP = attr_mP->data_float3();
	ccl::Attribute *attr_mN = nullptr;
	PrimitiveVariable::Interpolation nInterpolation = PrimitiveVariable::Invalid;
	if( normal( meshes[0], nInterpolation ) )
	{
		if( nInterpolation == PrimitiveVariable::Uniform )
		{
			msg( Msg::Warning, "MeshAlgo", "Variable \"N\" has unsupported interpolation type \"Uniform\" for motion steps - not generating normals." );
		}
		else
		{
			attr_mN = cmesh->attributes.add( ccl::ATTR_STD_MOTION_VERTEX_NORMAL, ccl::ustring("motion_N") );
		}
	}

	// First sample has already been obtained, so we start at 1
	for( size_t i = 1; i < meshes.size(); ++i )
	{
		PrimitiveVariableMap::const_iterator pIt = meshes[i]->variables.find( "P" );
		if( pIt != meshes[i]->variables.end() )
		{
			const V3fVectorData *p = runTimeCast<const V3fVectorData>( pIt->second.data.get() );
			if( p )
			{
				PrimitiveVariable::Interpolation pInterpolation = pIt->second.interpolation;
				if( pInterpolation == PrimitiveVariable::Varying || pInterpolation == PrimitiveVariable::Vertex || pInterpolation == PrimitiveVariable::FaceVarying )
				{
					// Vertex positions
					const V3fVectorData *p = meshes[i]->variableData<V3fVectorData>( "P", PrimitiveVariable::Vertex );
					const std::vector<V3f> &points = p->readable();
					size_t numVerts = p->readable().size();

					for( size_t j = 0; j < numVerts; ++j, ++mP )
						*mP = ccl::make_float3( points[j].x, points[j].y, points[j].z );
				}
				else
				{
					msg( Msg::Warning, "IECoreCyles::MeshAlgo::convert", "Variable \"Position\" has unsupported interpolation type - not generating sampled Position." );
					cmesh->attributes.remove(attr_mP);
				}
			}
			else
			{
				msg( Msg::Warning, "IECoreCyles::MeshAlgo::convert", boost::format( "Variable \"Position\" has unsupported type \"%s\" (expected V3fVectorData)." ) % pIt->second.data->typeName() );
				cmesh->attributes.remove(attr_mP);
			}
		}

		if( attr_mN )
		{
			if( const V3fVectorData *normals = normal( meshes[i], nInterpolation ) )
			{
				convertN( meshes[i], normals, attr_mN, nInterpolation );
			}
		}
	}

	ccl::Object *cobject = new ccl::Object();
	cobject->mesh = cmesh;
	cobject->name = ccl::ustring(nodeName.c_str());
	return cobject;
}

} // namespace MeshAlgo

} // namespace IECoreCycles
