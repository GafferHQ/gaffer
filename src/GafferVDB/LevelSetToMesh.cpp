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

#include "GafferVDB/Interrupter.h"

#include "Gaffer/StringPlug.h"

#include "IECoreVDB/VDBObject.h"

#include "IECoreScene/MeshPrimitive.h"

#include "openvdb/openvdb.h"
#include "openvdb/tools/Composite.h"
#include "openvdb/tools/GridTransformer.h"
#include "openvdb/tools/VolumeToMesh.h"

#include "fmt/format.h"

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

template<class F, typename... Args>
void dispatchForVdbType( const openvdb::GridBase *grid, F &&functor, Args&&... args )
{
	const std::string &type = grid->type();

	// Currently, we're just supporting FloatGrid. We could add cases here for
	// DoubleGrid, Int32Grid, Int64Grid, and BoolGrid ... the only reason we
	// haven't currently is that we're not aware of anyone who needs them, and
	// compiling for the other types adds another 60 seconds of compile time for this file,
	// and makes this compilation unit too big too compile on Windows without /bigobj.
	if( type == openvdb::FloatGrid::gridType() )
	{
		return functor( static_cast<const openvdb::FloatGrid *>( grid ), std::forward<Args>( args )... );
	}
	else
	{
		throw IECore::Exception( fmt::format( "Incompatible Grid found name: '{}' type: '{}' ", grid->getName(), grid->type() ) );
	}
}

template< typename T>
openvdb::GridBase::ConstPtr mergeGrids(
	const std::vector< std::pair< openvdb::GridBase::ConstPtr, Imath::M44f > > &grids,
	const openvdb::math::Transform &vdbTransform,
	const IECore::Canceller *canceller
)
{
	typename T::ConstPtr resultGrid;
	typename T::Ptr editableResultGrid;

	Interrupter interrupter( canceller );

	static const Imath::M44f identity;
	for( const auto &[untypedGrid, transform] : grids )
	{
		typename T::ConstPtr grid = openvdb::GridBase::grid< T >( untypedGrid );

		// We check the grid types match when we put them in the grids list
		assert( grid.get() );
		typename T::ConstPtr gridWithTransform;

		bool transformMatches;
		if( transform == identity )
		{
			gridWithTransform = grid;
			transformMatches = openvdb::tools::ABTransform( grid->transform(), vdbTransform ).isIdentity();
		}
		else
		{
			openvdb::math::Transform::Ptr toSource = grid->transformPtr()->copy();
			toSource->postMult( openvdb::math::Mat4d(
				transform[0][0], transform[0][1], transform[0][2], transform[0][3],
				transform[1][0], transform[1][1], transform[1][2], transform[1][3],
				transform[2][0], transform[2][1], transform[2][2], transform[2][3],
				transform[3][0], transform[3][1], transform[3][2], transform[3][3]
			) );
			gridWithTransform = openvdb::GridBase::constGrid< T >( grid->copyGridReplacingTransform( toSource ) );

			transformMatches = false;
		}


		if( transformMatches && !resultGrid )
		{
			resultGrid = grid;
		}
		else if( transformMatches )
		{
			if( !editableResultGrid )
			{
				editableResultGrid = openvdb::deepCopyTypedGrid<T>( resultGrid );
				resultGrid = editableResultGrid;
			}

			openvdb::tools::csgUnion( *editableResultGrid, *openvdb::deepCopyTypedGrid<T>( grid ) );

		}
		else
		{
			// We need to set up a fresh grid to hold the data transformed into the correct space for
			// merging. Currently we use this call which keeps the metadata from the original grid
			// We could probably just call T::create() instead to create totally fresh grid, but I'm
			// not confident that there isn't metadata that could affect VolumeToMesh
			typename T::Ptr destSpaceGrid = grid->copyWithNewTree();
			destSpaceGrid->setTransform( vdbTransform.copy() );


			// Our goal here is not actually to produce a "level set" ... the goal is to produce a grid that
			// has the maximum of all the source level sets at each point. This actually makes a difference
			// when doing a resample to a different scale - if we directly take the source values, the result
			// is not a proper level set, because the sources at different scales have different gradients.
			//
			// The usual way to resample a level set is to use tool::resampleToMatch, which has a special code
			// path for level sets that recomputes their distannces. However, that would change the values in
			// the source grids, so selecting an iso value with the isoValue plug would no longer have the same
			// effect. This would mean that if you merged level sets with different scales, the resulting
			// meshes would end up in different places than if you converted to meshes before merging.
			//
			// Instead, we use the helpfully named tool::doResampleToMatch, which does not have a special path
			// for level sets, and just takes the iso values from the source grids directly. The resulting grid
			// is not technically a proper level set, but it has the right iso values to ensure that the
			// conversion to mesh works correctly. It doesn't matter that it doesn't have other properties of
			// a level set, because we know we're just feeding this grid to VolumeToMesh and then discarding
			// it - it cannot possibly be used for something else where not being a "proper" level set would
			// be a problem. ( As an added bonus, doResampleToMatch is about twice as fast as resampleToMesh
			// on level sets ).
			//
			// It would be reasonable to offer a control for the sampler to use here. PointSampler is fastest
			// but noticeably blocky. QuadraticSampler gives higher quality results for smooth surfaces but
			// is slower, and can make hard edged models look a bit wobbly. BoxSampler is a basic trilinear,
			// which seems like a reasonable default.
			openvdb::tools::doResampleToMatch<openvdb::tools::BoxSampler>( *gridWithTransform, *destSpaceGrid, interrupter );
			// If we've been cancelled, the interrupter will have stopped
			// `resampleToMatch()` and we'll have a partial result in the grid.
			// We need to throw rather than allow this partial result to be
			// returned.
			Canceller::check( canceller );

			if( !resultGrid )
			{
				resultGrid = destSpaceGrid;
			}
			else
			{
				if( !editableResultGrid )
				{
					editableResultGrid = openvdb::deepCopyTypedGrid<T>( resultGrid );
					resultGrid = editableResultGrid;
				}
				openvdb::tools::csgUnion( *editableResultGrid, *destSpaceGrid );
			}

		}
	}

	return resultGrid;
}

IECoreScene::MeshPrimitivePtr volumeToMesh( openvdb::GridBase::ConstPtr grid, double isoValue, double adaptivity )
{
	openvdb::tools::VolumeToMesh mesher( isoValue, adaptivity );

	dispatchForVdbType(
		grid.get(),
		[ &mesher ]( const auto *typedGrid )
		{
			mesher( *typedGrid );
		}
	);

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
// LevelSetToMesh implementation
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( LevelSetToMesh );

size_t LevelSetToMesh::g_firstPlugIndex = 0;

LevelSetToMesh::LevelSetToMesh( const std::string &name )
	:	MergeObjects( name, "${scene:path}" )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new StringPlug( "grid", Plug::In, "surface" ) );
	addChild( new FloatPlug( "isoValue", Plug::In, 0.0f ) );
	addChild( new FloatPlug( "adaptivity", Plug::In, 0.0f, 0.0f, 1.0f ) );
}

LevelSetToMesh::~LevelSetToMesh()
{
}

Gaffer::StringPlug *LevelSetToMesh::gridPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *LevelSetToMesh::gridPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
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

bool LevelSetToMesh::affectsMergedObject( const Gaffer::Plug *input ) const
{
	return
		MergeObjects::affectsMergedObject( input ) ||
		input == isoValuePlug() ||
		input == adaptivityPlug() ||
		input == gridPlug()
	;
}

void LevelSetToMesh::hashMergedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	MergeObjects::hashMergedObject( path, context, h );

	gridPlug()->hash( h );
	isoValuePlug()->hash( h );
	adaptivityPlug()->hash( h );
}

IECore::ConstObjectPtr LevelSetToMesh::computeMergedObject( const std::vector< std::pair< IECore::ConstObjectPtr, Imath::M44f > > &sources, const Gaffer::Context *context ) const
{
	std::string gridName = gridPlug()->getValue();

	float smallestVoxel = 0;

	// We need to decide on a resolution for our intermediate grid if we're merging to a different location
	// than the source. The voxel size is determined by the VDB's transform, so we take the transform that
	// results in the smallest voxels. This has been chosen just as a reasonable heuristic that will likely
	// preserve the meaningful detail in the source volume - we don't include the Gaffer location scale in
	// this heuristic, so if someone merges two volumes where one of them has been scaled down tiny in Gaffer,
	// you'll get the voxel size at a default scale, rather than trying to cature the detail in the scaled
	// down volume by resampling the large volume to have a massive number of voxels ( which could be
	// very expensive ). If you really want to capture detail across different scales, you might be better
	// converting to mesh without merging, and then merging the meshes.
	openvdb::math::Transform::ConstPtr mostPreciseIndexing;
	std::string gridType;

	std::vector< std::pair< openvdb::GridBase::ConstPtr, Imath::M44f > > grids;

	for( const auto &[object, transform] : sources )
	{
		const IECoreVDB::VDBObject * v = IECore::runTimeCast< const IECoreVDB::VDBObject >( object.get() );
		if( !v )
		{
			// Just skip anything that's not a vdb
			continue;
		}

		openvdb::GridBase::ConstPtr grid = v->findGrid( gridPlug()->getValue() );

		if (!grid)
		{
			continue;
		}

		if( !gridType.size() )
		{
			gridType = grid->type();
		}
		else if( gridType != grid->type() )
		{
			throw IECore::Exception( fmt::format( "Incompatible grid types: '{}' vs '{}' ", gridType, grid->type() ) );
		}

		openvdb::Vec3d voxelSize3 = grid->transform().voxelSize();
		float voxelSize = std::min( voxelSize3[0], std::min( voxelSize3[1], voxelSize3[2] ) );

		if( !mostPreciseIndexing || voxelSize < smallestVoxel )
		{
			smallestVoxel = voxelSize;
			mostPreciseIndexing = grid->transformPtr();
		}

		grids.emplace_back( std::make_pair( grid, transform ) );
	}

	if( !grids.size() )
	{
		// If there are no grids, return a mesh with no faces.
		// There's a question whether NullObject would be more consistent, but this makes it consistent with
		// the result you get for a grid with no voxels matching the iso value.
		return new IECoreScene::MeshPrimitive();
	}

	openvdb::GridBase::ConstPtr resultGrid;
	dispatchForVdbType(
		grids[0].first.get(),
		[ &grids, &mostPreciseIndexing, &context, &resultGrid ]( const auto *typedGrid )
		{
			using GridType = typename std::remove_const_t< std::remove_pointer_t<decltype( typedGrid )> >;
			resultGrid = mergeGrids<GridType>( grids, *mostPreciseIndexing, context->canceller() );
		}
	);

	return volumeToMesh( resultGrid, isoValuePlug()->getValue(), adaptivityPlug()->getValue() );
}
