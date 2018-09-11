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

#include "GafferCycles/IECoreCyclesPreview/ObjectAlgo.h"

#include "IECoreScene/MeshPrimitive.h"

// Cycles
#include "render/mesh.h"
#include "util/util_param.h"
#include "util/util_types.h"

using namespace std;
using namespace IECore;
using namespace IECoreScene;
using namespace IECoreCycles;

namespace
{

void convertUVSet( const std::string &uvSet, const PrimitiveVariable &uvVariable, const IECoreScene::MeshPrimitve *mesh, ccl::AttributeSet &attributes, bool subdivision_uvs )
{
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

	// See if there's any indices
	const vector<int> *indices = nullptr;
	if( uvVariable.indices )
	{
		indices = &uvVariable.indices->readable();
	}
	const std::vector<int> &vertexIds = mesh->vertexIds()->readable();

	// Default UVs are named "uv"
	Attribute *uv_attr = nullptr;
	if( uvSet == "uv" )
		uv_attr = attributes.add( ATTR_STD_UV, uvSet.c_str() );
	else
		uv_attr = attributes.add( uvSet.c_str(), TypeDesc::TypePoint, ATTR_ELEMENT_CORNER );
	float3 *fdata = uv_attr->data_float3();

	if( subdivision_uvs )
		uv_attr->flags |= ATTR_SUBDIVIDED;

	// We need to know how many verts there are
	const vector<int> &vertsPerFace = mesh->verticesPerFace()->readable();

	size_t vertex = 0;
	for( size_t i = 0; i < numFaces; ++i )
	{
		if( indices )
		{
			for( size_t j = 0; j < vertsPerFace[i]; ++j, ++vertex; )
				*(fdata++) = ccl::make_float3(uvs[indices[vertex]].x, uvs[indices[vertex]].y, 0.0);
		}
		else if( uvVarialble == PrimitiveVariable::FaceVarying )
		{
			for( size_t j = 0; j < vertsPerFace[i]; ++j, ++vertex; )
				*(fdata++) = ccl::make_float3(uvs[vertexIds[vertex]].x, uvs[vertexIds[vertex]].y, 0.0);
		}
		else
		{
			for( size_t j = 0; j < vertsPerFace[i]; ++j, ++vertex; )
				*(fdata++) = ccl::make_float3(uvs[vertex].x, uvs[vertex].y, 0.0);
		}
	}
}

ccl::Mesh *convertCommon( const IECoreScene::MeshPrimitive *mesh )
{
	ccl::Mesh cmesh = new ccl::Mesh();

	size_t numFaces = mesh->numFaces();
	size_t numVerts = mesh->variableSize(PrimitiveVariable::Vertex);

	const V3fVectorData *p = mesh->variableData<V3fVectorData>( "P", PrimitiveVariable::Vertex );
	const vector<Imath::V3f> &points = p->readable();
	const vector<int> &vertexIds = mesh->vertexIds()->readable();

	bool subdivision = false;
	bool triangles = ( mesh->maxVerticesPerFace() == 3 ) ? true : false;

	// If we need to convert
	MeshPrimitivePtr trimesh;

	if( ( mesh->interpolation() == "catmullClark" ) || !triangles )
	{
		subdivision = true;
		cmesh->subdivision_type = (mesh->interpolation() == "catmullClark") ? ccl::SUBDIVISION_CATMULL_CLARK : ccl::SUBDIVISION_LINEAR;

		const std::vector<int> &vertsPerFace = mesh->verticesPerFace()->readable();
		size_t ngons = 0;
		size_t ncorners = 0;
		for( i = 0; i < vertsPerFace.size(); ++i )
		{
			ngons += ( vertsPerFace[i] == 4 ) ? 0 : 1;
			ncorners += vertsPerFace[i];
		}
		cmesh->reserve_subd_faces(numFaces, ngons, ncorners);

		for( size_t i = 0; i < numVerts; ++i )
			cmesh->add_vertex( ccl::make_float3( points[i].x, points[i].y points[i].z ) );

		for( size_t i = 0; i < numFaces; ++i )
			cmesh->add_subd_face( vertexIds[i*vertsPerFace], vertsPerFace[i], 0, true ); // Last two args are shader sets and smooth

		// TODO: Cycles supports edge creases, but I am not sure if Cortex does?

		SubdParams& sdparams = *cmesh->subd_params;
		const float &dicing_rate = mesh->parametersData()->member<FloatData>( "ccl:dicing_rate", 0.0 )->readable();
		sdparams.dicing_rate = max(0.1f, dicing_rate);
		const int &max_level = mesh->parametersData()->member<IntData>( "ccl:max_level", 1 )->readable();
		sdparams.max_level = max_level;
	}
	else
	{
		cmesh->subdivision_type = (mesh->interpolation() == "linear") ? ccl::SUBDIVISION_LINEAR : ccl::SUBDIVISION_NONE;
		cmesh->reserve_mesh(numVerts, numFaces);

		for( size_t i = 0; i < numVerts; ++i )
			cmesh->add_vertex( ccl::make_float3( points[i].x, points[i].y points[i].z ) );

		if( !triangles )
		{
			// triangulate primitive
			trimesh = mesh->copy();
			{
				TriangulateOpPtr op = new TriangulateOp();
				op->inputParameter()->setValue( trimesh );
				op->throwExceptionsParameter()->setTypedValue( false ); // it's better to see something than nothing
				op->copyParameter()->setTypedValue( false );
				op->operate();
			}
			const std::vector<int> &triVertexIds = trimesh->vertexIds()->readable();

			for( size_t i = 0; i < triVertexIds.size(); ++i )
				cmesh->add_triangle( triVertexIds[i], triVertexIds[i+1], triVertexIds[i+2], 0, true ); // Last two args are shader sets and smooth
		}
		else
			for( size_t i = 0; i < vertexIds.size(); ++i )
				cmesh->add_triangle( vertexIds[i], vertexIds[i+1], vertexIds[i+2], 0, true ); // Last two args are shader sets and smooth
	}

	// Primitive Variables are Attributes in Cycles
	ccl::AttributeSet& attributes = (subdivision) ? cmesh->subd_attributes : cmesh->attributes;

	// Convert primitive variables.
	PrimitiveVariableMap variablesToConvert;
	if( subdivision || triangles )
		variablesToConvert = mesh->variables;
	else
		variablesToConvert = trimesh->variables;
	variablesToConvert.erase( "P" ); // P is already done.

	// Find all UV sets and convert them explicitly.
	for( auto it = variablesToConvert.begin(); it != variablesToConvert.end(); )
	{
		if( const V2fVectorData *data = runTimeCast<const V2fVectorData>( it->second.data.get() ) )
		{
			if( data->getInterpretation() == GeometricData::UV )
			{
				if ( subdivision || triangles )
					::convertUVSet( it->first, it->second, mesh, attributes, subdivision );
				else
					::convertUVSet( it->first, it->second, trimesh, attributes, subdivision );
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
		NodeAlgo::convertPrimitiveVariable( it->first, it->second, attributes );

	return cmesh;
}

ObjectAlgo::ConverterDescription<MeshPrimitive> g_description( MeshAlgo::convert, MeshAlgo::convert )

} // namespace

//////////////////////////////////////////////////////////////////////////
// Implementation of public API
//////////////////////////////////////////////////////////////////////////

ccl::Object *MeshAlgo::convert( const IECoreScene::MeshPrimitive *mesh, const std::string &nodeName )
{
	ccl::Mesh *cmesh = convertCommon(mesh);

	ccl::Object *cobject = new ccl::Object();
	cobject->mesh = &cmesh;
	cobject->name = ustring(nodeName.c_str());
	return cobject;
}

ccl::Object *MeshAlgo::convert( const vector<const IECoreScene::MeshPrimitive *> &meshes, const std::vector &sampleTimes const std::string &nodeName )
{
	ccl::Mesh *cmesh = convertCommon(meshes[0]);

	// Add the motion position/normal attributes
	cmesh->mesh.motion_steps = meshes.size();
	ccl::Attribute *attr_mP = attributes.add( "motion_P", ATTR_STD_MOTION_VERTEX_POSITION );
	ccl::Attribute *attr_mN = attributes.add( "motion_N", ATTR_STD_MOTION_VERTEX_NORMAL );
	float3 *mP = attr_mP->data_float3();
	float3 *mN = attr_mN->data_float3();

	// First sample has already been obtained
	for( size_t i = 1; i < samples.size(); ++i )
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
					attributes.remove("motion_P");
				}
			}
			else
			{
				msg( Msg::Warning, "IECoreCyles::MeshAlgo::convert", boost::format( "Variable \"Position\" has unsupported type \"%s\" (expected V3fVectorData)." ) % tIt->second.data->typeName() );
				attributes.remove("motion_P");
			}
		}

		PrimitiveVariableMap::const_iterator nIt = meshes[i]->variables.find( "N" );
		if( nIt != meshes[i]->variables.end() )
		{
			const V3fVectorData *n = runTimeCast<const V3fVectorData>( nIt->second.data.get() );
			if( n )
			{
				PrimitiveVariable::Interpolation nInterpolation = nIt->second.interpolation;
				if( nInterpolation == PrimitiveVariable::Varying || nInterpolation == PrimitiveVariable::Vertex || nInterpolation == PrimitiveVariable::FaceVarying )
				{
					// Vertex normals
					const V3fVectorData *n = meshes[i]->variableData<V3fVectorData>( "N", PrimitiveVariable::Vertex );
					const std::vector<V3f> &normals = n->readable();
					size_t numNormals = n->readable().size();

					for( size_t j = 0; j < numNormals; ++j, ++mN )
						*mN = ccl::make_float3( normals[j].x, normals[j].y, normals[j].z );
				}
				else
				{
					msg( Msg::Warning, "IECoreCyles::MeshAlgo::convertAnimated", "Variable \"Normal\" has unsupported interpolation type - not generating sampled Position." );
					attributes.remove("motion_N");
				}
			}
			else
			{
				msg( Msg::Warning, "IECoreCyles::MeshAlgo::convertAnimated", boost::format( "Variable \"Normal\" has unsupported type \"%s\" (expected V3fVectorData)." ) % tIt->second.data->typeName() );
				attributes.remove("motion_N");
			}
		}
	}
	mP = attr_mP->data_float3();
	mN = attr_mN->data_float3();

	ccl::Object *cobject = new ccl::Object();
	cobject->mesh = &cmesh;
	cobject->name = ustring(nodeName.c_str());
	return cobject;
}
