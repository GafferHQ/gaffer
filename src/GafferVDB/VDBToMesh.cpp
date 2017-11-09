//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, John Haddon. All rights reserved.
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

#include <boost/mpl/for_each.hpp>
#include <boost/mpl/list.hpp>

#include "openvdb/openvdb.h"
#include "openvdb/tools/VolumeToMesh.h"

#include "IECore/MeshPrimitive.h"

#include "Gaffer/StringPlug.h"

#include "GafferVDB/VDBObject.h"
#include "GafferVDB/VDBToMesh.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferVDB;

//////////////////////////////////////////////////////////////////////////
// Utilities. Perhaps these belong in Cortex one day?
//////////////////////////////////////////////////////////////////////////

namespace
{


//! list of grid types which can be converted to a mesh
//! AccorindCall with scalar typed grid.
typedef boost::mpl::list
<
	openvdb::BoolGrid,
	openvdb::DoubleGrid,
	openvdb::FloatGrid,
	openvdb::Int32Grid,
	openvdb::Int64Grid
> VDBScalarGridList;

struct Dispatcher
{
	Dispatcher( openvdb::GridBase::ConstPtr grid, openvdb::tools::VolumeToMesh &mesher ) : m_grid( grid ), m_mesher( mesher ), m_matchingTypeFound( false )
	{
	}

	template<typename GridType>
	void operator()( GridType )
	{
		if ( m_matchingTypeFound )
		{
			return;
		}

		if( typename GridType::ConstPtr t = openvdb::GridBase::constGrid<GridType>( m_grid ) )
		{
			m_matchingTypeFound = true;
			m_mesher( *t );
		}
	}

	openvdb::GridBase::ConstPtr m_grid;
	openvdb::tools::VolumeToMesh &m_mesher;
	bool m_matchingTypeFound;
};

IECore::MeshPrimitivePtr volumeToMesh( openvdb::GridBase::ConstPtr grid, double isoValue, double adaptivity )
{
	openvdb::tools::VolumeToMesh mesher( isoValue, adaptivity );
	boost::mpl::for_each<VDBScalarGridList> ( Dispatcher( grid, mesher ) );

	// Copy out topology

	IntVectorDataPtr verticesPerFaceData = new IntVectorData;
	vector<int> &verticesPerFace = verticesPerFaceData->writable();

	IntVectorDataPtr vertexIdsData = new IntVectorData;
	vector<int> &vertexIds = vertexIdsData->writable();

	size_t numPolygons = 0;
	size_t numVerts = 0;
	for( size_t i = 0, n = mesher.polygonPoolListSize(); i < n; ++i )
	{
		const openvdb::tools::PolygonPool &polygonPool = mesher.polygonPoolList()[i];
		numPolygons += polygonPool.numQuads() + polygonPool.numTriangles();
		numVerts += polygonPool.numQuads() * 4 + polygonPool.numTriangles() * 3;
	}

	verticesPerFace.reserve( numPolygons );
	vertexIds.reserve( numVerts );

	for( size_t i = 0, n = mesher.polygonPoolListSize(); i < n; ++i )
	{
		const openvdb::tools::PolygonPool &polygonPool = mesher.polygonPoolList()[i];
		for( size_t qi = 0, qn = polygonPool.numQuads(); qi < qn; ++qi )
		{
			openvdb::math::Vec4ui quad = polygonPool.quad( qi );
			verticesPerFace.push_back( 4 );
			vertexIds.push_back( quad[0] );
			vertexIds.push_back( quad[1] );
			vertexIds.push_back( quad[2] );
			vertexIds.push_back( quad[3] );
		}

		for( size_t ti = 0, tn = polygonPool.numTriangles(); ti < tn; ++ti )
		{
			openvdb::math::Vec3ui triangle = polygonPool.triangle( ti );
			verticesPerFace.push_back( 3 );
			vertexIds.push_back( triangle[0] );
			vertexIds.push_back( triangle[1] );
			vertexIds.push_back( triangle[2] );
		}
	}

	// Copy out points
	V3fVectorDataPtr pointsData = new V3fVectorData;
	vector<V3f> &points = pointsData->writable();

	points.reserve( mesher.pointListSize() );
	for( size_t i = 0, n = mesher.pointListSize(); i < n; ++i )
	{
		const openvdb::math::Vec3s v = mesher.pointList()[i];
		points.push_back( V3f( v.x(), v.y(), v.z() ) );
	}

	return new MeshPrimitive( verticesPerFaceData, vertexIdsData, "linear", pointsData );
}


} // namespace

//////////////////////////////////////////////////////////////////////////
// VolumeToMesh implementation
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( VDBToMesh );

size_t VDBToMesh::g_firstPlugIndex = 0;

VDBToMesh::VDBToMesh( const std::string &name )
	:	SceneElementProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new StringPlug( "gridName", Plug::In, "levelset" ) );
	addChild( new FloatPlug( "isoValue", Plug::In, 0.0f ) );
	addChild( new FloatPlug( "adaptivity", Plug::In, 0.0f, 0.0f, 1.0f ) );

}

VDBToMesh::~VDBToMesh()
{
}

Gaffer::StringPlug *VDBToMesh::gridNamePlug()
{
	return  getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *VDBToMesh::gridNamePlug() const
{
	return  getChild<StringPlug>( g_firstPlugIndex );
}


Gaffer::FloatPlug *VDBToMesh::isoValuePlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 1);
}

const Gaffer::FloatPlug *VDBToMesh::isoValuePlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 1);
}

Gaffer::FloatPlug *VDBToMesh::adaptivityPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::FloatPlug *VDBToMesh::adaptivityPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 2 );
}

void VDBToMesh::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	SceneElementProcessor::affects( input, outputs );

	if(
		input == isoValuePlug() ||
		input == adaptivityPlug() ||
		input == gridNamePlug()
	)
	{
		outputs.push_back( outPlug()->objectPlug() );
	}
}

bool VDBToMesh::processesObject() const
{
	return true;
}

void VDBToMesh::hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	SceneElementProcessor::hashProcessedObject( path, context, h );

	gridNamePlug()->hash( h );
	isoValuePlug()->hash( h );
	adaptivityPlug()->hash( h );
}

IECore::ConstObjectPtr VDBToMesh::computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::ConstObjectPtr inputObject ) const
{
	const VDBObject *vdbObject = runTimeCast<const VDBObject>( inputObject.get() );
	if( !vdbObject )
	{
		return inputObject;
	}

	openvdb::GridBase::ConstPtr grid = vdbObject->findGrid( gridNamePlug()->getValue() );

	if (!grid)
	{
		return inputObject;
	}

	return volumeToMesh( grid, isoValuePlug()->getValue(), adaptivityPlug()->getValue() );
}
