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

#include "GafferVDB/LevelSetToMesh.h"

#include "Gaffer/StringPlug.h"

#include "IECoreVDB/VDBObject.h"

#include "IECoreScene/MeshPrimitive.h"

#include "openvdb/openvdb.h"
#include "openvdb/tools/VolumeToMesh.h"

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

struct MesherDispatch
{
	MesherDispatch( openvdb::GridBase::ConstPtr grid, openvdb::tools::VolumeToMesh &mesher ) : m_grid( grid ), m_mesher( mesher )
	{
	}

	template<typename GridType>
	void execute()
	{
		if( typename GridType::ConstPtr t = openvdb::GridBase::constGrid<GridType>( m_grid ) )
		{
			m_mesher( *t );
		}
	}

	openvdb::GridBase::ConstPtr m_grid;
	openvdb::tools::VolumeToMesh &m_mesher;
};

std::map<std::string, std::function<void( MesherDispatch& dispatch )> > meshers =
{
	{ openvdb::typeNameAsString<bool>(), []( MesherDispatch& dispatch ) { dispatch.execute<openvdb::BoolGrid>(); } },
	{ openvdb::typeNameAsString<double>(), []( MesherDispatch& dispatch ) { dispatch.execute<openvdb::DoubleGrid>(); } },
	{ openvdb::typeNameAsString<float>(), []( MesherDispatch& dispatch ) { dispatch.execute<openvdb::FloatGrid>(); } },
	{ openvdb::typeNameAsString<int32_t>(), []( MesherDispatch& dispatch ) { dispatch.execute<openvdb::Int32Grid>(); } },
	{ openvdb::typeNameAsString<int64_t>(), []( MesherDispatch& dispatch ) { dispatch.execute<openvdb::Int64Grid>(); } }
};


IECoreScene::MeshPrimitivePtr volumeToMesh( openvdb::GridBase::ConstPtr grid, double isoValue, double adaptivity )
{
	openvdb::tools::VolumeToMesh mesher( isoValue, adaptivity );
	MesherDispatch dispatch( grid, mesher );

	const auto it = meshers.find( grid->valueType() );
	if( it != meshers.end() )
	{
		it->second( dispatch );
	}
	else
	{
		throw IECore::InvalidArgumentException( boost::str( boost::format( "Incompatible Grid found name: '%1%' type: '%2' " ) % grid->valueType() % grid->getName() ) );
	}

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

GAFFER_NODE_DEFINE_TYPE( LevelSetToMesh );

size_t LevelSetToMesh::g_firstPlugIndex = 0;

LevelSetToMesh::LevelSetToMesh( const std::string &name )
	:	Deformer( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new StringPlug( "grid", Plug::In, "surface" ) );
	addChild( new FloatPlug( "isoValue", Plug::In, 0.0f ) );
	addChild( new FloatPlug( "adaptivity", Plug::In, 0.0f, 0.0f, 1.0f ) );

	// The output mesh will always be bounded by the input level set, and only
	// in rare cases will it be shrunk enough to warrant the cost of computing
	// exact bounds. So we default `adjustBounds` to `false`.
	adjustBoundsPlug()->setValue( false );
	adjustBoundsPlug()->resetDefault();
}

LevelSetToMesh::~LevelSetToMesh()
{
}

Gaffer::StringPlug *LevelSetToMesh::gridPlug()
{
	return  getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *LevelSetToMesh::gridPlug() const
{
	return  getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::FloatPlug *LevelSetToMesh::isoValuePlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 1);
}

const Gaffer::FloatPlug *LevelSetToMesh::isoValuePlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 1);
}

Gaffer::FloatPlug *LevelSetToMesh::adaptivityPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::FloatPlug *LevelSetToMesh::adaptivityPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 2 );
}

bool LevelSetToMesh::affectsProcessedObject( const Gaffer::Plug *input ) const
{
	return
		Deformer::affectsProcessedObject( input ) ||
		input == isoValuePlug() ||
		input == adaptivityPlug() ||
		input == gridPlug()
	;
}

void LevelSetToMesh::hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	Deformer::hashProcessedObject( path, context, h );

	gridPlug()->hash( h );
	isoValuePlug()->hash( h );
	adaptivityPlug()->hash( h );
}

IECore::ConstObjectPtr LevelSetToMesh::computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, const IECore::Object *inputObject ) const
{
	const VDBObject *vdbObject = runTimeCast<const VDBObject>( inputObject );
	if( !vdbObject )
	{
		return inputObject;
	}

	openvdb::GridBase::ConstPtr grid = vdbObject->findGrid( gridPlug()->getValue() );

	if (!grid)
	{
		return inputObject;
	}

	return volumeToMesh( grid, isoValuePlug()->getValue(), adaptivityPlug()->getValue() );
}
