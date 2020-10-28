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

#include "IECoreVDB/VDBObject.h"

#include "Gaffer/StringPlug.h"

#include "IECoreScene/MeshPrimitive.h"

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

	CortexMeshAdapter( const MeshPrimitive *mesh, const openvdb::math::Transform *transform )
		:	m_numFaces( mesh->numFaces() ),
			m_numVertices( mesh->variableSize( PrimitiveVariable::Vertex ) ),
			m_verticesPerFace( mesh->verticesPerFace()->readable() ),
			m_vertexIds( mesh->vertexIds()->readable() ),
			m_transform( transform )
	{
		size_t offset = 0;
		m_faceOffsets.reserve( m_numFaces );
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
		/// \todo Threaded pretransform in constructor?
		const V3f p = (*m_points)[ m_vertexIds[ m_faceOffsets[polygonIndex] + polygonVertexIndex ] ];
		pos = m_transform->worldToIndex( openvdb::math::Vec3s( p.x, p.y, p.z ) );
	}

	private :

		const size_t m_numFaces;
		const size_t m_numVertices;
		const vector<int> &m_verticesPerFace;
		const vector<int> &m_vertexIds;
		vector<int> m_faceOffsets;
		const vector<V3f> *m_points;
		const openvdb::math::Transform *m_transform;

};

} // namespace

//////////////////////////////////////////////////////////////////////////
// MeshToLevelSet implementation
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( MeshToLevelSet );

size_t MeshToLevelSet::g_firstPlugIndex = 0;

MeshToLevelSet::MeshToLevelSet( const std::string &name )
	:	SceneElementProcessor( name, IECore::PathMatcher::NoMatch )
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
	return  getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *MeshToLevelSet::gridPlug() const
{
	return  getChild<StringPlug>( g_firstPlugIndex );
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

void MeshToLevelSet::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	SceneElementProcessor::affects( input, outputs );

	if(
		input == gridPlug() ||
		input == voxelSizePlug() ||
		input == exteriorBandwidthPlug() ||
		input == interiorBandwidthPlug()
	)
	{
		outputs.push_back( outPlug()->objectPlug() );
	}
}

bool MeshToLevelSet::processesObject() const
{
	return true;
}

void MeshToLevelSet::hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	SceneElementProcessor::hashProcessedObject( path, context, h );

	gridPlug()->hash( h );
	voxelSizePlug()->hash( h );
	exteriorBandwidthPlug()->hash ( h );
	interiorBandwidthPlug()->hash ( h );
}

IECore::ConstObjectPtr MeshToLevelSet::computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::ConstObjectPtr inputObject ) const
{
	const MeshPrimitive *mesh = runTimeCast<const MeshPrimitive>( inputObject.get() );
	if( !mesh )
	{
		return inputObject;
	}

	const float voxelSize = voxelSizePlug()->getValue();
	const float exteriorBandwidth = exteriorBandwidthPlug()->getValue();
	const float interiorBandwidth = interiorBandwidthPlug()->getValue();

	openvdb::math::Transform::Ptr transform = openvdb::math::Transform::createLinearTransform( voxelSize );

	openvdb::FloatGrid::Ptr grid = openvdb::tools::meshToVolume<openvdb::FloatGrid>(
		CortexMeshAdapter( mesh, transform.get() ),
		*transform,
		exteriorBandwidth, //in voxel units
		interiorBandwidth, //in voxel units
		0 //conversionFlags,
		//primitiveIndexGrid.get()
	);

	grid->setName( gridPlug()->getValue() );

	VDBObjectPtr newVDBObject =  new VDBObject();
	newVDBObject->insertGrid( grid );

	return newVDBObject;
}
