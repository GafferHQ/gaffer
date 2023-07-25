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

#include "GafferCycles/IECoreCyclesPreview/GeometryAlgo.h"

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

#include "fmt/format.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace IECoreCycles;

namespace
{

// Notes on Cycles normals :
//
// - Cycles meshes store two sets of normals as attributes :
//    - A vertex normal ("N", ATTR_STD_VERTEX_NORMAL)
//    - A face normal ("Ng", ATTR_STD_FACE_NORMAL)
// - If we don't specify these attributes, they are computed for us
//   and added to the mesh by Cycles itself by `Mesh::add_vertex_normals()`
//   and `Mesh::add_face_normals()` respectively.
// - Which normal is actually used for shading is determined on a
//  triangle-by-triangle basis using the `smooth` flag passed
//  to `Mesh::add_triangle()`.
// - Cycles does not support facevarying normals.
bool hasSmoothNormals( const IECoreScene::MeshPrimitive *mesh )
{
	auto it = mesh->variables.find( "N" );
	if( it == mesh->variables.end() )
	{
		return false;
	}

	switch( it->second.interpolation )
	{
		case PrimitiveVariable::Constant :
		case PrimitiveVariable::Uniform :
			// These are definitely intended to be faceted.
			return false;
		case PrimitiveVariable::FaceVarying :
			// Could be a mix of faceted and non-faceted triangles, including
			// triangles with a mix of soft and hard edges, which aren't
			// representable in Cycles. Plump for faceted, among other things
			// because the native Cortex cube geometry has FaceVarying normals.
			return false;
		default :
			return true;
	}
}

ccl::Mesh *convertCommon( const IECoreScene::MeshPrimitive *mesh )
{
	assert( mesh->typeId() == IECoreScene::MeshPrimitive::staticTypeId() );

	// Triangulate if necessary

	ConstMeshPrimitivePtr triangulatedMesh;
	if( mesh->interpolation() != "catmullClark" && mesh->maxVerticesPerFace() > 3 )
	{
		// Polygon meshes in Cycles must consist of triangles only.
		triangulatedMesh = MeshAlgo::triangulate( mesh );
		mesh = triangulatedMesh.get();
	}

	// Convert topology and points

	ccl::Mesh *cmesh = new ccl::Mesh();

	if( mesh->interpolation() == "catmullClark" )
	{
		cmesh->set_subdivision_type( ccl::Mesh::SUBDIVISION_CATMULL_CLARK );

		const size_t numFaces = mesh->numFaces();
		const V3fVectorData *p = mesh->variableData<V3fVectorData>( "P", PrimitiveVariable::Vertex );
		const vector<Imath::V3f> &points = p->readable();
		const vector<int> &vertexIds = mesh->vertexIds()->readable();
		const size_t numVerts = points.size();

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
			cmesh->add_subd_face(
				const_cast<int*>(&vertexIds[indexOffset]), vertsPerFace[i],
				/* shader = */ 0, /* smooth = */ true
			);
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
		const V3fVectorData *p = mesh->variableData<V3fVectorData>( "P", PrimitiveVariable::Vertex );
		const vector<Imath::V3f> &points = p->readable();
		const size_t numVerts = points.size();
		const std::vector<int> &vertexIds = mesh->vertexIds()->readable();

		const size_t numFaces = mesh->numFaces();
		cmesh->reserve_mesh( numVerts, numFaces );

		for( size_t i = 0; i < numVerts; i++ )
			cmesh->add_vertex( ccl::make_float3( points[i].x, points[i].y, points[i].z ) );

		const bool smooth = hasSmoothNormals( mesh );
		for( size_t i = 0; i < vertexIds.size(); i+= 3 )
			cmesh->add_triangle(
				vertexIds[i], vertexIds[i+1], vertexIds[i+2],
				/* shader = */ 0, /* smooth = */ smooth
			);
	}

	// Convert primitive variables.

	ccl::AttributeSet &attributes = cmesh->get_subdivision_type() != ccl::Mesh::SUBDIVISION_NONE ? cmesh->subd_attributes : cmesh->attributes;
	for( const auto &[name, variable] : mesh->variables )
	{
		if( name == "P" )
		{
			// Converted above already
			continue;
		}
		switch( variable.interpolation )
		{
			case PrimitiveVariable::Constant :
				GeometryAlgo::convertPrimitiveVariable( name, variable, attributes, ccl::ATTR_ELEMENT_MESH );
				break;
			case PrimitiveVariable::Uniform :
				GeometryAlgo::convertPrimitiveVariable( name, variable, attributes, ccl::ATTR_ELEMENT_FACE );
				break;
			case PrimitiveVariable::Vertex :
			case PrimitiveVariable::Varying :
				GeometryAlgo::convertPrimitiveVariable( name, variable, attributes, ccl::ATTR_ELEMENT_VERTEX );
				break;
			case PrimitiveVariable::FaceVarying :
				GeometryAlgo::convertPrimitiveVariable( name, variable, attributes, ccl::ATTR_ELEMENT_CORNER );
				break;
			default :
				break;
		}
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
			cmesh = convertCommon( midMesh.get() );
		}

		for( int i = 0; i < numSamples; ++i )
		{
			samples.push_back( meshes[i] );
		}
	}

	// Add the motion position attributes
	cmesh->set_use_motion_blur( true );
	cmesh->set_motion_steps( samples.size() + 1 );
	ccl::Attribute *attr_mP = cmesh->attributes.add( ccl::ATTR_STD_MOTION_VERTEX_POSITION, ccl::ustring("motion_P") );
	ccl::float3 *mP = attr_mP->data_float3();

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
				msg( Msg::Warning, "IECoreCyles::MeshAlgo::convert", fmt::format( "Variable \"Position\" has unsupported type \"{}\" (expected V3fVectorData).", pIt->second.data->typeName() ) );
				cmesh->attributes.remove( attr_mP );
				cmesh->set_motion_steps( 0) ;
				cmesh->set_use_motion_blur( true );
			}
		}
	}

	cmesh->name = ccl::ustring( nodeName.c_str() );
	return cmesh;
}

GeometryAlgo::ConverterDescription<MeshPrimitive> g_description( convert, convert );

} // namespace
