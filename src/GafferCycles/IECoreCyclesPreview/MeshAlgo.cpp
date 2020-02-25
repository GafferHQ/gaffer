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

#include "IECore/Interpolator.h"
#include "IECore/SimpleTypedData.h"

// Cycles
#include "kernel/kernel_types.h"
#include "render/mesh.h"
#include "subd/subd_dice.h"
#include "util/util_param.h"
#include "util/util_types.h"

// MikkTspace
#include "Mikktspace/mikktspace.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace IECoreCycles;

namespace
{

struct MikkUserData {
	MikkUserData( const char *layer_name,
				  const ccl::Mesh *mesh,
				  ccl::float3 *tangent,
				  float *tangent_sign )
		: mesh( mesh ), texface( NULL ), tangent( tangent ), tangent_sign( tangent_sign )
	{
		const ccl::AttributeSet &attributes = (mesh->subd_faces.size()) ? mesh->subd_attributes :
																		  mesh->attributes;

		ccl::Attribute *attr_vN = attributes.find( ccl::ATTR_STD_VERTEX_NORMAL );
		vertex_normal = attr_vN->data_float3();

		ccl::Attribute *attr_uv = attributes.find( ccl::ustring( layer_name ) );
		if( attr_uv != NULL )
		{
			texface = attr_uv->data_float2();
		}
	}

	const ccl::Mesh *mesh;
	int num_faces;

	ccl::float3 *vertex_normal;
	ccl::float2 *texface;

	ccl::float3 *tangent;
	float *tangent_sign;
};

static int mikk_get_num_faces( const SMikkTSpaceContext *context )
{
	const MikkUserData *userdata = (const MikkUserData *)context->m_pUserData;
	if( userdata->mesh->subd_faces.size() )
	{
		return userdata->mesh->subd_faces.size();
	}
	else
	{
		return userdata->mesh->num_triangles();
	}
}

static int mikk_get_num_verts_of_face( const SMikkTSpaceContext *context, const int face_num )
{
	const MikkUserData *userdata = (const MikkUserData *)context->m_pUserData;
	if( userdata->mesh->subd_faces.size() )
	{
		const ccl::Mesh *mesh = userdata->mesh;
		return mesh->subd_faces[face_num].num_corners;
	}
	else
	{
		return 3;
	}
}

static int mikk_vertex_index( const ccl::Mesh *mesh, const int face_num, const int vert_num )
{
	if( mesh->subd_faces.size() )
	{
		const ccl::Mesh::SubdFace &face = mesh->subd_faces[face_num];
		return mesh->subd_face_corners[face.start_corner + vert_num];
	}
	else
	{
		return mesh->triangles[face_num * 3 + vert_num];
	}
}

static int mikk_corner_index( const ccl::Mesh *mesh, const int face_num, const int vert_num )
{
	if( mesh->subd_faces.size() )
	{
		const ccl::Mesh::SubdFace &face = mesh->subd_faces[face_num];
		return face.start_corner + vert_num;
	}
	else
	{
		return face_num * 3 + vert_num;
	}
}

static void mikk_get_position( const SMikkTSpaceContext *context,
							   float P[3],
							   const int face_num,
							   const int vert_num )
{
	const MikkUserData *userdata = (const MikkUserData *)context->m_pUserData;
	const ccl::Mesh *mesh = userdata->mesh;
	const int vertex_index = mikk_vertex_index(mesh, face_num, vert_num);
	const ccl::float3 vP = mesh->verts[vertex_index];
	P[0] = vP.x;
	P[1] = vP.y;
	P[2] = vP.z;
}

static void mikk_get_texture_coordinate( const SMikkTSpaceContext *context,
										 float uv[2],
										 const int face_num,
										 const int vert_num )
{
	const MikkUserData *userdata = (const MikkUserData *)context->m_pUserData;
	const ccl::Mesh *mesh = userdata->mesh;
	if( userdata->texface != NULL )
	{
		const int corner_index = mikk_corner_index( mesh, face_num, vert_num );
		ccl::float2 tfuv = userdata->texface[corner_index];
		uv[0] = tfuv.x;
		uv[1] = tfuv.y;
	}
	else
	{
		uv[0] = 0.0f;
		uv[1] = 0.0f;
	}
}

static void mikk_get_normal( const SMikkTSpaceContext *context,
							 float N[3],
							 const int face_num,
							 const int vert_num)
{
	const MikkUserData *userdata = (const MikkUserData *)context->m_pUserData;
	const ccl::Mesh *mesh = userdata->mesh;
	ccl::float3 vN;
	if( mesh->subd_faces.size() )
	{
		const ccl::Mesh::SubdFace &face = mesh->subd_faces[face_num];
		if( face.smooth )
		{
			const int vertex_index = mikk_vertex_index( mesh, face_num, vert_num );
			vN = userdata->vertex_normal[vertex_index];
		}
		else
		{
			vN = face.normal( mesh );
		}
	}
	else
	{
		if( mesh->smooth[face_num] )
		{
			const int vertex_index = mikk_vertex_index( mesh, face_num, vert_num );
			vN = userdata->vertex_normal[vertex_index];
		}
		else
		{
			const ccl::Mesh::Triangle tri = mesh->get_triangle( face_num );
			vN = tri.compute_normal(&mesh->verts[0]);
		}
	}
	N[0] = vN.x;
	N[1] = vN.y;
	N[2] = vN.z;
}

static void mikk_set_tangent_space(const SMikkTSpaceContext *context,
								   const float T[],
								   const float sign,
								   const int face_num,
								   const int vert_num)
{
	MikkUserData *userdata = (MikkUserData *)context->m_pUserData;
	const ccl::Mesh *mesh = userdata->mesh;
	const int corner_index = mikk_corner_index( mesh, face_num, vert_num );
	userdata->tangent[corner_index] = ccl::make_float3( T[0], T[1], T[2] );
	if (userdata->tangent_sign != NULL)
	{
		userdata->tangent_sign[corner_index] = sign;
	}
}

static void mikk_compute_tangents( const char *layer_name, ccl::Mesh *mesh, bool need_sign, bool active_render )
{
	/* Create tangent attributes. */
	ccl::AttributeSet &attributes = ( mesh->subd_faces.size() ) ? mesh->subd_attributes : mesh->attributes;
	ccl::Attribute *attr;
	ccl::ustring name;

	name = ccl::ustring( ( string( layer_name ) + ".tangent" ).c_str() );

	if( active_render )
	{
		attr = attributes.add( ccl::ATTR_STD_UV_TANGENT, name);
	}
	else
	{
		attr = attributes.add( name, ccl::TypeDesc::TypeVector, ccl::ATTR_ELEMENT_CORNER );
	}
	ccl::float3 *tangent = attr->data_float3();
	/* Create bitangent sign attribute. */
	float *tangent_sign = NULL;
	if( need_sign )
	{
		ccl::Attribute *attr_sign;
		ccl::ustring name_sign = ccl::ustring( ( string( layer_name ) + ".tangent_sign" ).c_str() );

		if( active_render )
		{
			attr_sign = attributes.add( ccl::ATTR_STD_UV_TANGENT_SIGN, name_sign );
		}
		else
		{
			attr_sign = attributes.add( name_sign, ccl::TypeDesc::TypeFloat, ccl::ATTR_ELEMENT_CORNER );
		}
		tangent_sign = attr_sign->data_float();
	}
	/* Setup userdata. */
	MikkUserData userdata( layer_name, mesh, tangent, tangent_sign );
	/* Setup interface. */
	SMikkTSpaceInterface sm_interface;
	memset( &sm_interface, 0, sizeof( sm_interface ) );
	sm_interface.m_getNumFaces = mikk_get_num_faces;
	sm_interface.m_getNumVerticesOfFace = mikk_get_num_verts_of_face;
	sm_interface.m_getPosition = mikk_get_position;
	sm_interface.m_getTexCoord = mikk_get_texture_coordinate;
	sm_interface.m_getNormal = mikk_get_normal;
	sm_interface.m_setTSpaceBasic = mikk_set_tangent_space;
	/* Setup context. */
	SMikkTSpaceContext context;
	memset( &context, 0, sizeof( context ) );
	context.m_pUserData = &userdata;
	context.m_pInterface = &sm_interface;
	/* Compute tangents. */
	genTangSpaceDefault( &context );
}

} // namespace

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

void convertUVSet( const string &uvSet, const IECoreScene::PrimitiveVariable &uvVariable, const IECoreScene::MeshPrimitive *mesh, ccl::AttributeSet &attributes, bool subdivision_uvs )//, ccl::Mesh *cmesh )
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
	{
		uv_attr = attributes.add( ccl::ATTR_STD_UV, ccl::ustring(uvSet.c_str()) );
	}
	else if( uvSet == "st" )
	{
		// First check if UV exists on the mesh already so we don't override it, otherwise we will use it as a second uvset.
		if( mesh->variables.find( "uv" ) != mesh->variables.end() )
		{
			uv_attr = attributes.add( ccl::ustring(uvSet.c_str()), ccl::TypeFloat2, ccl::ATTR_ELEMENT_CORNER );
		}
		else
		{
			uv_attr = attributes.add( ccl::ATTR_STD_UV, ccl::ustring(uvSet.c_str()) );
		}
	}
	else
	{
		uv_attr = attributes.add( ccl::ustring(uvSet.c_str()), ccl::TypeFloat2, ccl::ATTR_ELEMENT_CORNER );
	}
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
				for( size_t j = 0; j < vertsPerFace[i]; ++j, ++vertex )
				{
					*(fdata++) = ccl::make_float2(uvs[indices[vertexIds[vertex]]].x, uvs[indices[vertexIds[vertex]]].y);
				}
			}
		}
		else // FaceVarying/Varying
		{
			for( size_t i = 0; i < numFaces; ++i )
			{
				for( size_t j = 0; j < vertsPerFace[i]; ++j, ++vertex )
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
				for( size_t j = 0; j < vertsPerFace[i]; ++j, ++vertex )
				{
					*(fdata++) = ccl::make_float2(uvs[vertexIds[vertex]].x, uvs[vertexIds[vertex]].y);
				}
			}
		}
		else // FaceVarying/Varying
		{
			for( size_t i = 0; i < numFaces; ++i )
			{
				for( size_t j = 0; j < vertsPerFace[i]; ++j, ++vertex )
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

		// Creases
		size_t numEdges = mesh->cornerIds()->readable().size();
		for( int length : mesh->creaseLengths()->readable() )
		{
			numEdges += length - 1;
		}

		if( numEdges )
		{
			cmesh->subd_creases.resize( numEdges );
			ccl::Mesh::SubdEdgeCrease *crease = cmesh->subd_creases.data();

			auto id = mesh->creaseIds()->readable().begin();
			auto sharpness = mesh->creaseSharpnesses()->readable().begin();
			for( int length : mesh->creaseLengths()->readable() )
			{
				for( int j = 0; j < length - 1; ++j )
				{
					crease->v[0] = *id++;
					crease->v[1] = *id;
					crease->crease = (*sharpness) * 0.1f;
					crease++;
				}
				id++;
				sharpness++;
			}

			sharpness = mesh->cornerSharpnesses()->readable().begin();
			for( int cornerId : mesh->cornerIds()->readable() )
			{
				crease->v[0] = cornerId;
				crease->v[1] = cornerId;
				crease->crease = (*sharpness) * 0.1f;
				sharpness++;
				crease++;
			}
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
			if( ( data->getInterpretation() == GeometricData::UV ) ||
				( data->getInterpretation() == GeometricData::Numeric ) )
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

ccl::Object *convert( const IECoreScene::MeshPrimitive *mesh, const std::string &nodeName, const ccl::Scene *scene )
{
	ccl::Object *cobject = new ccl::Object();
	cobject->mesh = convertCommon(mesh);
	cobject->name = ccl::ustring(nodeName.c_str());
	return cobject;
}

ccl::Object *convert( const std::vector<const IECoreScene::MeshPrimitive *> &meshes, const std::vector<float> &times, const int frameIdx, const std::string &nodeName, const ccl::Scene *scene )
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
		int _frameIdx = ( numSamples+1 ) / 2;
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
	cmesh->use_motion_blur = true;
	cmesh->motion_steps = samples.size() + 1;
	ccl::Attribute *attr_mP = cmesh->attributes.add( ccl::ATTR_STD_MOTION_VERTEX_POSITION, ccl::ustring("motion_P") );
	ccl::float3 *mP = attr_mP->data_float3();
	ccl::Attribute *attr_mN = nullptr;
	PrimitiveVariable::Interpolation nInterpolation = PrimitiveVariable::Invalid;
	if( normal( meshes[0], nInterpolation ) )
	{
		if( nInterpolation == PrimitiveVariable::Uniform )
		{
			msg( Msg::Warning, "IECoreCyles::MeshAlgo::convert", "Variable \"N\" has unsupported interpolation type \"Uniform\" for motion steps - not generating normals." );
		}
		else
		{
			attr_mN = cmesh->attributes.add( ccl::ATTR_STD_MOTION_VERTEX_NORMAL, ccl::ustring("motion_N") );
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
					cmesh->attributes.remove(attr_mP);
					cmesh->motion_steps = 0;
				}
			}
			else
			{
				msg( Msg::Warning, "IECoreCyles::MeshAlgo::convert", boost::format( "Variable \"Position\" has unsupported type \"%s\" (expected V3fVectorData)." ) % pIt->second.data->typeName() );
				cmesh->attributes.remove(attr_mP);
				cmesh->motion_steps = 0;
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

	ccl::Object *cobject = new ccl::Object();
	cobject->mesh = cmesh;
	cobject->name = ccl::ustring(nodeName.c_str());
	return cobject;
}

void computeTangents( ccl::Mesh *cmesh, const IECoreScene::MeshPrimitive *mesh, bool needsign )
{
	const ccl::AttributeSet &attributes = (cmesh->subd_faces.size()) ? cmesh->subd_attributes :
																	   cmesh->attributes;

	ccl::Attribute *attr = attributes.find( ccl::ATTR_STD_UV );
	if( attr )
		mikk_compute_tangents( attr->standard_name( ccl::ATTR_STD_UV ), cmesh, needsign, true );

	// Secondary UVsets
	PrimitiveVariableMap variables = mesh->variables;
	if( mesh->variables.find( "uv" ) == mesh->variables.end() )
	{
		variables.erase( "st" );
	}
	variables.erase( "uv" );

	for( auto it = variables.begin(); it != variables.end(); )
	{
		if( const V2fVectorData *data = runTimeCast<const V2fVectorData>( it->second.data.get() ) )
		{
			if( ( data->getInterpretation() == GeometricData::UV ) ||
				( data->getInterpretation() == GeometricData::Numeric ) )
			{
				mikk_compute_tangents( it->first.c_str(), cmesh, needsign, false );
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
}

} // namespace MeshAlgo

} // namespace IECoreCycles
