//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, John Haddon. All rights reserved.
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

#include "GafferVDB/MeshToLevelSet.h"

#include "GafferVDB/Interrupter.h"

#include "IECoreVDB/VDBObject.h"

#include "Gaffer/StringPlug.h"

#include "IECoreScene/MeshPrimitive.h"
#include "GafferScene/Private/IECoreScenePreview/PrimitiveAlgo.h"

#include "openvdb/openvdb.h"
#include "openvdb/tools/MeshToVolume.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace IECoreVDB;
using namespace Gaffer;
using namespace GafferVDB;

//////////////////////////////////////////////////////////////////////////
// Utilities. Perhaps these belong in Cortex one day?
//////////////////////////////////////////////////////////////////////////

namespace
{

struct CortexMeshAdapter
{
	CortexMeshAdapter( const MeshPrimitive *mesh )
		:	m_numFaces( mesh->numFaces() ),
			m_numVertices( mesh->variableSize( PrimitiveVariable::Vertex ) ),
			m_verticesPerFace( mesh->verticesPerFace()->readable() ),
			m_vertexIds( mesh->vertexIds()->readable() )
	{
		size_t offset = 0;
		m_faceOffsets.reserve( m_numFaces );

		// \todo - Preparing this list of face offsets is not an effective way to prepare topology for
		// OpenVDB. If we wanted to be optimal, we would probably just convert everything to quads, where
		// the 4 vertex is set to openvdb::util::INVALID_IDX if the face is actually a triangle ( this is
		// the convention used by OpenVDB in their adapter ). If we were going to do this, we would also
		// want to process n-gons with > 4 verts somehow to preserve watertightness. Currently, we pass
		// n-gons through unchanged, and then VDB discards them, which breaks watertightness and causes
		// level set conversion to completely fail on meshes with n-gons.
		for( vector<int>::const_iterator it = m_verticesPerFace.begin(), eIt = m_verticesPerFace.end(); it != eIt; ++it )
		{
			m_faceOffsets.push_back( offset );
			offset += *it;
		}

		const V3fVectorData *points = mesh->variableData<V3fVectorData>( "P", PrimitiveVariable::Vertex );
		m_points = &points->readable();
	}

	size_t polygonCount() const
	{
		return m_numFaces;
	}

	size_t pointCount() const
	{
		return m_numVertices;
	}

	size_t vertexCount( size_t polygonIndex ) const
	{
		return m_verticesPerFace[polygonIndex];
	}

	// Return position pos in local grid index space for polygon n and vertex v
	void getIndexSpacePoint( size_t polygonIndex, size_t polygonVertexIndex, openvdb::Vec3d &pos ) const
	{
		const V3f &p = (*m_points)[ m_vertexIds[ m_faceOffsets[polygonIndex] + polygonVertexIndex ] ];
		pos = openvdb::math::Vec3s( p.x, p.y, p.z );
	}

	private :

		const size_t m_numFaces;
		const size_t m_numVertices;
		const vector<int> &m_verticesPerFace;
		const vector<int> &m_vertexIds;
		vector<int> m_faceOffsets;
		const vector<V3f> *m_points;
};

} // namespace

//////////////////////////////////////////////////////////////////////////
// MeshToLevelSet implementation
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( MeshToLevelSet );

size_t MeshToLevelSet::g_firstPlugIndex = 0;

MeshToLevelSet::MeshToLevelSet( const std::string &name )
	:	MergeObjects( name, "${scene:path}" )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new StringPlug( "grid", Plug::In, "surface") );
	addChild( new FloatPlug( "voxelSize", Plug::In, 0.1f, 0.0001f ) );
	addChild( new FloatPlug( "exteriorBandwidth", Plug::In, 3.0f, 0.0001f ) );
	addChild( new FloatPlug( "interiorBandwidth", Plug::In, 3.0f, 0.0001f ) );
}

MeshToLevelSet::~MeshToLevelSet()
{
}

Gaffer::StringPlug *MeshToLevelSet::gridPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *MeshToLevelSet::gridPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

FloatPlug *MeshToLevelSet::voxelSizePlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 1 );
}

const FloatPlug *MeshToLevelSet::voxelSizePlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 1 );
}

FloatPlug *MeshToLevelSet::exteriorBandwidthPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 2 );
}

const FloatPlug *MeshToLevelSet::exteriorBandwidthPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 2 );
}

FloatPlug *MeshToLevelSet::interiorBandwidthPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 3 );
}

const FloatPlug *MeshToLevelSet::interiorBandwidthPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 3 );
}

bool MeshToLevelSet::affectsMergedObject( const Gaffer::Plug *input ) const
{
	return
		MergeObjects::affectsMergedObject( input ) ||
		input == gridPlug() ||
		input == voxelSizePlug() ||
		input == exteriorBandwidthPlug() ||
		input == interiorBandwidthPlug()
	;
}

void MeshToLevelSet::hashMergedObject(
	const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h
) const
{
	MergeObjects::hashMergedObject( path, context, h );

	gridPlug()->hash( h );
	voxelSizePlug()->hash( h );
	exteriorBandwidthPlug()->hash ( h );
	interiorBandwidthPlug()->hash ( h );
}

IECore::ConstObjectPtr MeshToLevelSet::computeMergedObject( const std::vector< std::pair< IECore::ConstObjectPtr, Imath::M44f > > &sources, const Gaffer::Context *context ) const
{
	std::vector< IECoreScene::MeshPrimitivePtr > meshStorage;
	std::vector< std::pair< const IECoreScene::Primitive *, Imath::M44f > > meshes;

	const float voxelSize = voxelSizePlug()->getValue();

	openvdb::math::Transform::Ptr vdbTransform = openvdb::math::Transform::createLinearTransform( voxelSize );
	Imath::M44f worldToIndex;
	worldToIndex.setScale( 1.0f / voxelSize );

	for( const auto &[object, transform] : sources )
	{
		const IECoreScene::MeshPrimitive * m = IECore::runTimeCast< const IECoreScene::MeshPrimitive >( object.get() );
		if( !m )
		{
			// Just skip anything that's not a mesh
			continue;
		}

		// Create a simplified mesh with only basic topology and P - OpenVDB won't use anything else,
		// and we don't want to spend time merging primvars or creases that won't be used.
		// The copy-on-write mechanism should ensure that we don't actually duplicate this data.
		IECoreScene::MeshPrimitivePtr simpleMesh = new IECoreScene::MeshPrimitive();
		simpleMesh->setTopologyUnchecked(
			m->verticesPerFace(), m->vertexIds(), m->variableSize( PrimitiveVariable::Interpolation::Vertex )
		);
		simpleMesh->variables["P"] = m->variables.at("P");
		meshStorage.push_back( simpleMesh );

		meshes.push_back( std::make_pair( simpleMesh.get(), transform * worldToIndex ) );
	}

	openvdb::FloatGrid::Ptr grid;
	if( !meshes.size() )
	{
		// None of the filtered sources were actually meshes. We could consider this an exception,
		// but I guess the most consistent thing is just to return an empty grid with the correct voxel size.
		grid = openvdb::FloatGrid::create();
		grid->setTransform( vdbTransform );
	}
	else
	{
		IECoreScene::MeshPrimitivePtr mergedMesh = IECore::runTimeCast<MeshPrimitive>(
			IECoreScenePreview::PrimitiveAlgo::mergePrimitives( meshes, context->canceller() )
		);
		assert( mergedMesh );

		const float exteriorBandwidth = exteriorBandwidthPlug()->getValue();
		const float interiorBandwidth = interiorBandwidthPlug()->getValue();

		Interrupter interrupter( context->canceller() );

		grid = openvdb::tools::meshToVolume<openvdb::FloatGrid>(
			interrupter,
			CortexMeshAdapter( mergedMesh.get() ),
			*vdbTransform,
			exteriorBandwidth, //in voxel units
			interiorBandwidth, //in voxel units
			0 //conversionFlags
		);

		// If we've been cancelled, the interrupter will have stopped
		// `meshToVolume()` and we'll have a partial result in the grid.
		// We need to throw rather than allow this partial result to be
		// returned.
		Canceller::check( context->canceller() );
	}

	grid->setName( gridPlug()->getValue() );

	VDBObjectPtr newVDBObject = new VDBObject();
	newVDBObject->insertGrid( grid );

	return newVDBObject;
}
