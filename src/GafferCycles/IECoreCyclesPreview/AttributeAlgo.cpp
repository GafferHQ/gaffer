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
#include "GafferCycles/IECoreCyclesPreview/ObjectAlgo.h"
#include "GafferCycles/IECoreCyclesPreview/SocketAlgo.h"

#include "IECore/SimpleTypedData.h"

// Cycles
#include "kernel/types.h"
#include "scene/mesh.h"
#include "util/param.h"
#include "util/types.h"

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
				  ccl::Mesh *mesh,
				  ccl::float3 *tangent,
				  float *tangent_sign )
		: mesh( mesh ), texface( nullptr ), tangent( tangent ), tangent_sign( tangent_sign )
	{
		const ccl::AttributeSet &attributes = (mesh->get_num_subd_faces()) ? mesh->subd_attributes :
																		  mesh->attributes;

		ccl::Attribute *attr_vN = attributes.find( ccl::ATTR_STD_VERTEX_NORMAL );
#ifdef WITH_CYCLES_CORNER_NORMALS
		ccl::Attribute* attr_cN = attributes.find( ccl::ATTR_STD_CORNER_NORMAL );
		if( !attr_vN && !attr_cN )
#else
		if( !attr_vN )
#endif
		{
			mesh->add_face_normals();
			mesh->add_vertex_normals();
			attr_vN = attributes.find( ccl::ATTR_STD_VERTEX_NORMAL );
		}

#ifdef WITH_CYCLES_CORNER_NORMALS
		// This preference depends on what Cycles does inside the hood.
		// Works for now, but there should be a more clear way of knowing
		// which normals are used for rendering.
		if (attr_cN)
		{
			corner_normal = attr_cN->data_float3();
		}
		else
		{
			vertex_normal = attr_vN->data_float3();
		}
#else
		vertex_normal = attr_vN->data_float3();
#endif

		ccl::Attribute *attr_uv = attributes.find( ccl::ustring( layer_name ) );
		if( attr_uv != nullptr )
		{
			texface = attr_uv->data_float2();
		}
	}

	ccl::Mesh *mesh;
	int num_faces;

	ccl::float3* corner_normal;
	ccl::float3 *vertex_normal;
	ccl::float2 *texface;
	ccl::float3 *orco;
	ccl::float3 orco_loc, orco_size;

	ccl::float3 *tangent;
	float *tangent_sign;
};

int mikk_get_num_faces( const SMikkTSpaceContext *context )
{
	const MikkUserData *userdata = (const MikkUserData *)context->m_pUserData;
	if( userdata->mesh->get_num_subd_faces() )
	{
		return userdata->mesh->get_num_subd_faces();
	}
	else
	{
		return userdata->mesh->num_triangles();
	}
}

int mikk_get_num_verts_of_face( const SMikkTSpaceContext *context, const int face_num )
{
	const MikkUserData *userdata = (const MikkUserData *)context->m_pUserData;
	if( userdata->mesh->get_num_subd_faces() )
	{
		const ccl::Mesh *mesh = userdata->mesh;
		return mesh->get_subd_num_corners()[face_num];
	}
	else
	{
		return 3;
	}
}

int mikk_vertex_index( const ccl::Mesh *mesh, const int face_num, const int vert_num )
{
	if( mesh->get_num_subd_faces() )
	{
		const ccl::Mesh::SubdFace &face = mesh->get_subd_face(face_num);
		return mesh->get_subd_face_corners()[face.start_corner + vert_num];
	}
	else
	{
		return mesh->get_triangles()[face_num * 3 + vert_num];
	}
}

int mikk_corner_index( const ccl::Mesh *mesh, const int face_num, const int vert_num )
{
	if( mesh->get_num_subd_faces() )
	{
		const ccl::Mesh::SubdFace &face = mesh->get_subd_face(face_num);
		return face.start_corner + vert_num;
	}
	else
	{
		return face_num * 3 + vert_num;
	}
}

void mikk_get_position( const SMikkTSpaceContext *context,
							   float P[3],
							   const int face_num,
							   const int vert_num )
{
	const MikkUserData *userdata = (const MikkUserData *)context->m_pUserData;
	const ccl::Mesh *mesh = userdata->mesh;
	const int vertex_index = mikk_vertex_index(mesh, face_num, vert_num);
	const ccl::float3 vP = mesh->get_verts()[vertex_index];
	P[0] = vP.x;
	P[1] = vP.y;
	P[2] = vP.z;
}

void mikk_get_texture_coordinate( const SMikkTSpaceContext *context,
										 float uv[2],
										 const int face_num,
										 const int vert_num )
{
	const MikkUserData *userdata = (const MikkUserData *)context->m_pUserData;
	const ccl::Mesh *mesh = userdata->mesh;
	if( userdata->texface != nullptr )
	{
		const int corner_index = mikk_corner_index( mesh, face_num, vert_num );
		ccl::float2 tfuv = userdata->texface[corner_index];
		uv[0] = tfuv.x;
		uv[1] = tfuv.y;
	}
	else if (userdata->orco != nullptr)
	{
		const int vertex_index = mikk_vertex_index(mesh, face_num, vert_num);
		const ccl::float3 orco_loc = userdata->orco_loc;
		const ccl::float3 orco_size = userdata->orco_size;
		const ccl::float3 orco = (userdata->orco[vertex_index] + orco_loc) / orco_size;

		const ccl::float2 tmp = map_to_sphere(orco);
		uv[0] = tmp.x;
		uv[1] = tmp.y;
	}
	else
	{
		uv[0] = 0.0f;
		uv[1] = 0.0f;
	}
}

void mikk_get_normal( const SMikkTSpaceContext *context,
							 float N[3],
							 const int face_num,
							 const int vert_num)
{
	const MikkUserData *userdata = (const MikkUserData *)context->m_pUserData;
	const ccl::Mesh *mesh = userdata->mesh;
	ccl::float3 vN;
	if( mesh->get_num_subd_faces() )
	{
		const ccl::Mesh::SubdFace &face = mesh->get_subd_face(face_num);
		if (userdata->corner_normal)
		{
			vN = userdata->corner_normal[face.start_corner + vert_num];
		}
		else if( face.smooth )
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
		if (userdata->corner_normal)
		{
			vN = userdata->corner_normal[face_num * 3 + vert_num];
		}
		if( mesh->get_smooth()[face_num] )
		{
			const int vertex_index = mikk_vertex_index( mesh, face_num, vert_num );
			vN = userdata->vertex_normal[vertex_index];
		}
		else
		{
			const ccl::Mesh::Triangle tri = mesh->get_triangle( face_num );
			vN = tri.compute_normal(&mesh->get_verts()[0]);
		}
	}
	N[0] = vN.x;
	N[1] = vN.y;
	N[2] = vN.z;
}

void mikk_set_tangent_space(const SMikkTSpaceContext *context,
								   const float T[],
								   const float sign,
								   const int face_num,
								   const int vert_num)
{
	MikkUserData *userdata = (MikkUserData *)context->m_pUserData;
	const ccl::Mesh *mesh = userdata->mesh;
	const int corner_index = mikk_corner_index( mesh, face_num, vert_num );
	userdata->tangent[corner_index] = ccl::make_float3( T[0], T[1], T[2] );
	if (userdata->tangent_sign != nullptr)
	{
		userdata->tangent_sign[corner_index] = sign;
	}
}

void mikk_compute_tangents( const char *layer_name, ccl::Mesh *mesh, bool need_sign, bool active_render )
{
	/* Create tangent attributes. */
	ccl::AttributeSet &attributes = ( mesh->get_num_subd_faces() ) ? mesh->subd_attributes : mesh->attributes;
	ccl::Attribute *attr;
	ccl::ustring name;

	if (layer_name != nullptr)
	{
		name = ccl::ustring( ( std::string( layer_name ) + ".tangent" ).c_str() );
	}
	else
	{
		name = ccl::ustring( "orco.tangent" );
	}

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
	float *tangent_sign = nullptr;
	if( need_sign )
	{
		ccl::Attribute *attr_sign;
		ccl::ustring name_sign;

		if (layer_name != nullptr)
		{
			name_sign = ccl::ustring( ( std::string( layer_name ) + ".tangent_sign" ).c_str() );
		}
		else
		{
			name_sign = ccl::ustring( "orco.tangent_sign" );
		}

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

//////////////////////////////////////////////////////////////////////////
// Implementation of public API
//////////////////////////////////////////////////////////////////////////

namespace IECoreCycles

{

namespace AttributeAlgo

{

ccl::TypeDesc typeDesc( IECore::TypeId dataType )
{
	switch( dataType )
	{
		case FloatVectorDataTypeId :
		case IntVectorDataTypeId :
		case IntDataTypeId:
			return ccl::TypeDesc::TypeFloat;
		case Color3fVectorDataTypeId :
		case Color4fVectorDataTypeId :
			return ccl::TypeDesc::TypeColor;
		case V2fVectorDataTypeId :
		case V2iVectorDataTypeId :
			return ccl::TypeFloat2;
		case V3fVectorDataTypeId :
		case V3iVectorDataTypeId :
			return ccl::TypeDesc::TypeVector;
		case M44fVectorDataTypeId :
		case M44fDataTypeId :
			return ccl::TypeDesc::TypeMatrix;
		default :
			return ccl::TypeDesc::TypeVector;
	}
}

ccl::TypeDesc typeFromGeometricDataInterpretation( IECore::GeometricData::Interpretation dataType )
{
	switch( dataType )
	{
		case GeometricData::Numeric :
			return ccl::TypeDesc::TypeVector;
		case GeometricData::Point :
			return ccl::TypeDesc::TypePoint;
		case GeometricData::Normal :
			return ccl::TypeDesc::TypeNormal;
		case GeometricData::Vector :
			return ccl::TypeDesc::TypeVector;
		case GeometricData::Color :
			return ccl::TypeDesc::TypeColor;
		case GeometricData::UV :
			return ccl::TypeDesc::TypePoint;
		default :
			return ccl::TypeDesc::TypeVector;
	}
}

void convertPrimitiveVariable( const std::string &name, const IECoreScene::PrimitiveVariable &primitiveVariable, ccl::AttributeSet &attributes )
{
	IECore::TypeId dataType = primitiveVariable.data.get()->typeId();
	if( dataType == StringDataTypeId )
	{
		//msg( Msg::Warning, "IECoreCyles::AttributeAlgo::convertPrimitiveVariable", boost::format( "Variable \"%s\" has unsupported type \"%s\"." ) % name % primitiveVariable.data->typeName() );
		return;
	}
	ccl::TypeDesc ctype = typeDesc( dataType );
	ccl::Attribute *attr = nullptr;
	if( name == "N" )
	{
		attr = attributes.find( ccl::ATTR_STD_VERTEX_NORMAL );
		if(!attr)
			attr = attributes.add( ccl::ATTR_STD_VERTEX_NORMAL, ccl::ustring(name.c_str()) );
	}
	else if( name == "uv" )
	{
		attr = attributes.find( ccl::ATTR_STD_UV );
		if(!attr)
			attr = attributes.add( ccl::ATTR_STD_UV, ccl::ustring(name.c_str()) );
	}
	else if( name == "uTangent" )
	{
		attr = attributes.find( ccl::ATTR_STD_UV_TANGENT );
		if(!attr)
			attr = attributes.add( ccl::ATTR_STD_UV_TANGENT, ccl::ustring(name.c_str()) );
	}
	else
	{
		if( ctype != ccl::TypeDesc::TypeFloat )
		{
			// We need to determine what kind of vector it is
			const V3fVectorData *data = runTimeCast<const V3fVectorData>( primitiveVariable.data.get() );
			if( data )
				ctype = typeFromGeometricDataInterpretation( data->getInterpretation() );
		}
		ccl::AttributeElement celem = ccl::ATTR_ELEMENT_NONE;
		switch( primitiveVariable.interpolation )
		{
			case PrimitiveVariable::Constant :
				celem = ccl::ATTR_ELEMENT_MESH;
				break;
			case PrimitiveVariable::Vertex :
				if( attributes.geometry->geometry_type == ccl::Geometry::HAIR )
				{
					celem = ccl::ATTR_ELEMENT_CURVE_KEY;
				}
				else
				{
					celem = ccl::ATTR_ELEMENT_VERTEX;
				}
				break;
			case PrimitiveVariable::Varying :
			case PrimitiveVariable::FaceVarying :
				celem = ccl::ATTR_ELEMENT_CORNER;
				break;
			case PrimitiveVariable::Uniform :
				celem = ccl::ATTR_ELEMENT_FACE;
				break;
			default :
				break;
		}
		attr = attributes.find( ccl::ustring(name.c_str()) );
		if( !attr )
			attr = attributes.add( ccl::ustring(name.c_str()), ctype, celem );
	}

	if( primitiveVariable.interpolation != PrimitiveVariable::Constant && ctype == ccl::TypeDesc::TypeFloat )
	{
		if( const FloatVectorData *data = runTimeCast<const FloatVectorData>( primitiveVariable.data.get() ) )
		{
			const std::vector<float> &floatData = data->readable();

			size_t num = floatData.size();
			float *cdata = attr->data_float();

			if( cdata )
			{
				for( size_t i = 0; i < num; ++i )
					*(cdata++) = floatData[i];
				cdata = attr->data_float();
				return;
			}
		}

		if( const IntVectorData *data = runTimeCast<const IntVectorData>( primitiveVariable.data.get() ) )
		{
			const std::vector<int> &intData = data->readable();

			size_t num = intData.size();
			float *cdata = attr->data_float();

			if( cdata )
			{
				for( size_t i = 0; i < num; ++i )
					*(cdata++) = (float)intData[i];
				cdata = attr->data_float();
				return;
			}
		}

		msg( Msg::Warning, "IECoreCyles::AttributeAlgo::convertPrimitiveVariable", boost::format( "Variable \"%s\" has unsupported type \"%s\" (expected FloatVectorData or IntVectorData)." ) % name % primitiveVariable.data->typeName() );
		attributes.remove( attr );
		return;
	}
	else if( primitiveVariable.interpolation != PrimitiveVariable::Constant )
	{
		if( const V3fVectorData *data = runTimeCast<const V3fVectorData>( primitiveVariable.data.get() ) )
		{
			const std::vector<V3f> &v3fData = data->readable();
			size_t num = v3fData.size();
			ccl::float3 *cdata = attr->data_float3();

			if( cdata )
			{
				for( size_t i = 0; i < num; ++i )
					*(cdata++) = ccl::make_float3( v3fData[i].x, v3fData[i].y, v3fData[i].z );
				cdata = attr->data_float3();
				return;
			}
		}

		if( const V3iVectorData *data = runTimeCast<const V3iVectorData>( primitiveVariable.data.get() ) )
		{
			const std::vector<V3i> &v3iData = data->readable();
			size_t num = v3iData.size();
			ccl::float3 *cdata = attr->data_float3();

			if( cdata )
			{
				for( size_t i = 0; i < num; ++i )
					*(cdata++) = ccl::make_float3( (float)v3iData[i].x, (float)v3iData[i].y, (float)v3iData[i].z );
				cdata = attr->data_float3();
				return;
			}
		}

		if( const V2fVectorData *data = runTimeCast<const V2fVectorData>( primitiveVariable.data.get() ) )
		{
			const std::vector<V2f> &v2fData = data->readable();
			size_t num = v2fData.size();
			ccl::float2 *cdata = attr->data_float2();

			if( cdata )
			{
				for( size_t i = 0; i < num; ++i )
					*(cdata++) = ccl::make_float2( v2fData[i].x, v2fData[i].y );
				cdata = attr->data_float2();
				return;
			}
		}

		if( const V2iVectorData *data = runTimeCast<const V2iVectorData>( primitiveVariable.data.get() ) )
		{
			const std::vector<V2i> &v2iData = data->readable();
			size_t num = v2iData.size();
			ccl::float2 *cdata = attr->data_float2();

			if( cdata )
			{
				for( size_t i = 0; i < num; ++i )
					*(cdata++) = ccl::make_float2( (float)v2iData[i].x, (float)v2iData[i].y );
				cdata = attr->data_float2();
				return;
			}
		}

		if( const Color3fVectorData *data = runTimeCast<const Color3fVectorData>( primitiveVariable.data.get() ) )
		{
			const std::vector<Color3f> &colorData = data->readable();
			size_t num = colorData.size();
			ccl::float3 *cdata = attr->data_float3();

			if( cdata )
			{
				for( size_t i = 0; i < num; ++i )
					*(cdata++) = ccl::make_float3( colorData[i].x, colorData[i].y, colorData[i].z );
				cdata = attr->data_float3();
				return;
			}
		}

		msg( Msg::Warning, "IECoreCyles::AttributeAlgo::convertPrimitiveVariable", boost::format( "Variable \"%s\" has unsupported type \"%s\" (expected V3fVectorData, Color3fVectorData or V2fVectorData)." ) % name % primitiveVariable.data->typeName() );
		attributes.remove( attr );
		return;
	}
	else if( primitiveVariable.interpolation == PrimitiveVariable::Constant )
	{
		if( const FloatData *data = runTimeCast<const FloatData>( primitiveVariable.data.get() ) )
		{
			const float &floatData = data->readable();
			float *cdata = attr->data_float();

			if( cdata )
			{
				*(cdata) = floatData;
				return;
			}
		}

		if( const IntData *data = runTimeCast<const IntData>( primitiveVariable.data.get() ) )
		{
			const int &intData = data->readable();
			float *cdata = attr->data_float();

			if( cdata )
			{
				*(cdata) = (float)intData;
				return;
			}
		}

		if( const V2fData *data = runTimeCast<const V2fData>( primitiveVariable.data.get() ) )
		{
			const Imath::V2f &v2fData = data->readable();
			ccl::float2 *cdata = attr->data_float2();

			if( cdata )
			{
				*(cdata) = ccl::make_float2( v2fData.x, v2fData.y );
				return;
			}
		}

		if( const V2iData *data = runTimeCast<const V2iData>( primitiveVariable.data.get() ) )
		{
			const Imath::V2i &v2iData = data->readable();
			ccl::float2 *cdata = attr->data_float2();

			if( cdata )
			{
				*(cdata) = ccl::make_float2( (float)v2iData.x, (float)v2iData.y );
				return;
			}
		}

		if( const V3fData *data = runTimeCast<const V3fData>( primitiveVariable.data.get() ) )
		{
			const Imath::V3f &v3fData = data->readable();
			ccl::float3 *cdata = attr->data_float3();

			if( cdata )
			{
				*(cdata) = SocketAlgo::setVector( v3fData );
				return;
			}
		}

		if( const V3iData *data = runTimeCast<const V3iData>( primitiveVariable.data.get() ) )
		{
			const Imath::V3i &v3iData = data->readable();
			ccl::float3 *cdata = attr->data_float3();

			if( cdata )
			{
				*(cdata) = ccl::make_float3( (float)v3iData.x, (float)v3iData.y, (float)v3iData.z );
				return;
			}
		}

		if( const Color3fData *data = runTimeCast<const Color3fData>( primitiveVariable.data.get() ) )
		{
			const Imath::Color3f &colorData = data->readable();
			ccl::float3 *cdata = attr->data_float3();

			if( cdata )
			{
				*(cdata) = SocketAlgo::setColor( colorData );
				return;
			}
		}

		if( const M44fData *data = runTimeCast<const M44fData>( primitiveVariable.data.get() ) )
		{
			const Imath::M44f &m44fData = data->readable();
			ccl::Transform *cdata = attr->data_transform();

			if( cdata )
			{
				*(cdata) = SocketAlgo::setTransform( m44fData );
				return;
			}
		}

		msg( Msg::Warning, "IECoreCyles::AttributeAlgo::convertPrimitiveVariable", boost::format( "Variable \"%s\" has unsupported type \"%s\" (expected FloatData, IntData, V3fData, Color3fData or M44fData)." ) % name % primitiveVariable.data->typeName() );
		attributes.remove( attr );
		return;
	}
}

void computeTangents( ccl::Mesh *cmesh, const IECoreScene::MeshPrimitive *mesh, bool needsign )
{
	const ccl::AttributeSet &attributes = (cmesh->get_num_subd_faces()) ? cmesh->subd_attributes :
																		  cmesh->attributes;

	ccl::Attribute *attr = attributes.find( ccl::ATTR_STD_UV );
	if( attr )
		mikk_compute_tangents( attr->standard_name( ccl::ATTR_STD_UV ), cmesh, needsign, true );

	// Secondary UVsets
	// TODO: Currently seeing Cycles not working with normal maps and secondary UVs.
}

} // AttributeAlgo

} // IECoreCycles
