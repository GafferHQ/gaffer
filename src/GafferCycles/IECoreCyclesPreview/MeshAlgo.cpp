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

#include "SceneAlgo.h"

#include "IECoreScene/MeshPrimitive.h"
#include "IECoreScene/MeshAlgo.h"

// Cycles
#include "kernel/types.h"
#include "scene/geometry.h"
#include "scene/mesh.h"
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
// - Cycles meshes store vertex normals as ("N", ATTR_STD_VERTEX_NORMAL)
// - If we don't specify vertex normals, they are computed for us
//   and added to the mesh by Cycles itself by `Mesh::add_vertex_normals()`
// - Face normals are always computed on demand in the Cycles kernel, so we
//   resample custom uniform normals to face-varying.
// - Which normal is actually used for shading is determined on a
//  triangle-by-triangle basis using the `smooth` flag passed
//  to `Mesh::add_triangle()`.
// - Cycles as of 5.1 now supports face-varying normals as
//  ("N", ATTR_STD_CORNER_NORMAL)
//
// Also see `GeometryAlgo::convertPrimitiveVariable()` where we handle the
// tagging of normal attributes with ATTR_STD_VERTEX_NORMAL or
// ATTR_STD_CORNER_NORMAL. This also handles octahedral packing of normals
// via the `ccl::packed_normal()` utility function.
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
		default :
			return true;
	}
}

ccl::Mesh *convertPrimary( const IECoreScene::MeshPrimitive *mesh, ccl::Scene *scene )
{
	assert( mesh->typeId() == IECoreScene::MeshPrimitive::staticTypeId() );

	const V3fVectorData *p = mesh->variableData<V3fVectorData>( "P", PrimitiveVariable::Vertex );
	if( !p )
	{
		msg( Msg::Warning, "IECoreCyles::MeshAlgo", "MeshPrimitive does not have \"P\" primitive variable of interpolation type Vertex." );
		return nullptr;
	}

	// Triangulate if necessary

	ConstMeshPrimitivePtr triangulatedMesh;
	if( mesh->interpolation() != "catmullClark" && mesh->maxVerticesPerFace() > 3 )
	{
		// Polygon meshes in Cycles must consist of triangles only.
		triangulatedMesh = MeshAlgo::triangulate( mesh );
		mesh = triangulatedMesh.get();
	}

	// Convert topology and points

	const size_t numFaces = mesh->numFaces();
	const vector<Imath::V3f> &points = p->readable();
	const vector<int> &vertexIds = mesh->vertexIds()->readable();
	const size_t numVerts = points.size();

	ccl::Mesh *cmesh = SceneAlgo::createNodeWithLock<ccl::Mesh>( scene );

	if( mesh->interpolation() == "catmullClark" )
	{
		cmesh->set_subdivision_type( ccl::Mesh::SUBDIVISION_CATMULL_CLARK );

		const std::vector<int> &vertsPerFace = mesh->verticesPerFace()->readable();
		size_t ncorners = 0;
		for( size_t i = 0; i < vertsPerFace.size(); i++ )
		{
			ncorners += vertsPerFace[i];
		}
		cmesh->resize_subd_faces( numFaces, ncorners );

		cmesh->resize_mesh( numVerts, 0 );

		ccl::Attribute *pos = cmesh->subd_attributes.add( ccl::ATTR_STD_POSITION );
		std::copy_n( reinterpret_cast<const ccl::packed_float3 *>( points.data() ), points.size(), pos->data_for_write<ccl::packed_float3>() );

		std::copy( vertexIds.begin(), vertexIds.end(), cmesh->get_subd_face_corners().data() );

		int *subdStartCorner = cmesh->get_subd_start_corner().data();
		int *subdNumCorners = cmesh->get_subd_num_corners().data();
		int *subdPtexOffset = cmesh->get_subd_ptex_offset().data();

		int cornerIndex = 0;
		int ptexOffset = 0;
		for( size_t i = 0; i < vertsPerFace.size(); i++ )
		{
			subdStartCorner[i] = cornerIndex;
			subdNumCorners[i] = vertsPerFace[i];
			cornerIndex += vertsPerFace[i];

			subdPtexOffset[i] = ptexOffset;
			const int numPtex = ( vertsPerFace[i] == 4 ) ? 1 : vertsPerFace[i];
			ptexOffset += numPtex;
		}

		// Creases
		size_t numEdges = mesh->cornerIds()->readable().size();
		for( const int &length : mesh->creaseLengths()->readable() )
		{
			numEdges += length - 1;
		}

		if( numEdges )
		{
			cmesh->reserve_subd_creases( numEdges );

			auto id = mesh->creaseIds()->readable().begin();
			auto sharpness = mesh->creaseSharpnesses()->readable().begin();
			for( const int &length : mesh->creaseLengths()->readable() )
			{
				for( int j = 0; j < length - 1; ++j )
				{
					const int v0 = *id++;
					const int v1 = *id;
					cmesh->add_edge_crease( v0, v1, (*sharpness) * 0.1f );
				}
				id++;
				sharpness++;
			}

			sharpness = mesh->cornerSharpnesses()->readable().begin();
			for( const int &cornerId : mesh->cornerIds()->readable() )
			{
				cmesh->add_vertex_crease( cornerId, (*sharpness) * 0.1f );
				sharpness++;
			}
		}

		std::ranges::fill( cmesh->get_subd_shader(), 0 );
		std::ranges::fill( cmesh->get_subd_smooth(), true );

		cmesh->tag_position_modified();
		cmesh->tag_subd_face_corners_modified();
		cmesh->tag_subd_start_corner_modified();
		cmesh->tag_subd_num_corners_modified();
		cmesh->tag_subd_shader_modified();
		cmesh->tag_subd_smooth_modified();
		cmesh->tag_subd_ptex_offset_modified();
	}
	else
	{
		cmesh->resize_mesh( numVerts, numFaces );

		std::copy_n( reinterpret_cast<const ccl::packed_float3 *>( points.data() ), points.size(), cmesh->get_position_for_write() );

		std::copy( vertexIds.begin(), vertexIds.end(), cmesh->get_triangles().data() );

		const bool smooth = hasSmoothNormals( mesh );
		std::ranges::fill( cmesh->get_shader(), 0 );
		std::ranges::fill( cmesh->get_smooth(), smooth );

		cmesh->tag_position_modified();
		cmesh->tag_triangles_modified();
		cmesh->tag_shader_modified();
		cmesh->tag_smooth_modified();
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
		if( name == "N" && variable.interpolation == PrimitiveVariable::Uniform )
		{
			// Resample "N" to FaceVarying as Cycles doesn't accept custom uniform normals.
			PrimitiveVariable resampledN = variable;
			IECoreScene::MeshAlgo::resamplePrimitiveVariable( mesh, resampledN, PrimitiveVariable::FaceVarying );
			GeometryAlgo::convertPrimitiveVariable( name, resampledN, attributes, ccl::ATTR_ELEMENT_CORNER );
			continue;
		}
		const V2fVectorData *uv = static_cast<const V2fVectorData *>( variable.data.get() );
		if( ( name == "uv" || ( uv && uv->getInterpretation() == GeometricData::UV ) ) &&
			variable.interpolation != PrimitiveVariable::FaceVarying )
		{
			// Resample UVs to FaceVarying as Cycles doesn't accept any other for UVs.
			PrimitiveVariable resampledUV = variable;
			IECoreScene::MeshAlgo::resamplePrimitiveVariable( mesh, resampledUV, PrimitiveVariable::FaceVarying );
			GeometryAlgo::convertPrimitiveVariable( name, resampledUV, attributes, ccl::ATTR_ELEMENT_CORNER );
			continue;
		}
		switch( variable.interpolation )
		{
			case PrimitiveVariable::Constant :
				// Constant primitive variables always go on `Mesh::attributes` rather than `Mesh::subd_attributes`,
				// because they do not require subdivision.
				GeometryAlgo::convertPrimitiveVariable( name, variable, cmesh->attributes, ccl::ATTR_ELEMENT_MESH );
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

	// \todo This works around subdivision bugs in Cycles. Remove once bugs are fixed there.
	if( cmesh->get_subdivision_type() == ccl::Mesh::SUBDIVISION_CATMULL_CLARK )
	{
		// A Catmull-Clark mesh shouldn't need vertex normals, but Cycles has a code path
		// that calls `add_vertex_normals()`, which crashes when run from a previously
		// tessellated mesh. So we call this up-front to avoid the crash.
		cmesh->add_vertex_normals();
		// Add `ATTR_STD_GENERATED` to prevent Cycles from crashing when generating it
		// from a previously tessellated mesh. If we want to match Blender, this should
		// be generated from a rest pose and normalised 0-1. The below matches Cycles'
		// fallback behaviour when `ATTR_STD_GENERATED` is not provided by the host.
		if( ccl::Attribute *positionAttribute = cmesh->subd_attributes.find( ccl::ATTR_STD_POSITION ) )
		{
			ccl::Attribute *generated = cmesh->subd_attributes.add( ccl::ATTR_STD_GENERATED );
			std::copy_n( positionAttribute->data<ccl::packed_float3>(), positionAttribute->element_size( cmesh, ccl::ATTR_ELEMENT_VERTEX, ccl::ATTR_PRIM_SUBD ), generated->data_for_write<ccl::packed_float3>() );
		}
	}

	return cmesh;
}

ccl::Geometry *convert( const IECoreScenePreview::Renderer::Samples<const IECoreScene::MeshPrimitive *> &samples, const IECoreScenePreview::Renderer::SampleTimes &times, size_t primarySampleIndex, ccl::Scene *scene )
{
	if( ccl::Mesh *result = convertPrimary( samples[primarySampleIndex], scene ) )
	{
		GeometryAlgo::convertMotion( IECoreScenePreview::Renderer::staticSamplesCast<const IECoreScene::Primitive *>( samples ), primarySampleIndex, *result );
		return result;
	}

	return nullptr;
}

GeometryAlgo::ConverterDescription<MeshPrimitive> g_description( convert );

} // namespace
