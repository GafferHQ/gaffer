//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2026, Cinesite VFX Ltd. All rights reserved.
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
//      * Neither the name of Image Engine Design Inc nor the names of
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

#include "GafferVDB/LevelSetSmooth.h"

#include "GafferVDB/Interrupter.h"

#include "IECoreVDB/VDBObject.h"

#include "Gaffer/StringPlug.h"

#include "openvdb/openvdb.h"
#include "openvdb/tools/LevelSetFilter.h"

#include "fmt/format.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreVDB;
using namespace Gaffer;
using namespace GafferVDB;

namespace
{

template<typename GridType>
void filterGrid( GridType &grid, LevelSetSmooth::Mode mode, int radius, int iterations, const IECore::Canceller *canceller )
{
	Interrupter interrupter( canceller );
	openvdb::tools::LevelSetFilter<GridType, GridType, Interrupter> filter( grid, &interrupter );

	for( int i = 0; i < iterations; ++i )
	{
		Canceller::check( canceller );

		switch( mode )
		{
			case GafferVDB::LevelSetSmooth::Mode::Box :
				filter.mean( radius );
				break;
			case GafferVDB::LevelSetSmooth::Mode::Gaussian :
				filter.gaussian( radius );
				break;
			case GafferVDB::LevelSetSmooth::Mode::Median :
				filter.median( radius );
				break;
			case GafferVDB::LevelSetSmooth::Mode::MeanCurvature :
				filter.meanCurvature();
				break;
			case GafferVDB::LevelSetSmooth::Mode::Laplacian :
				filter.laplacian();
				break;
			case GafferVDB::LevelSetSmooth::Mode::Fillet :
#if OPENVDB_LIBRARY_MAJOR_VERSION_NUMBER > 11
				filter.fillet();
#else
				/// \todo Remove from Gaffer 1.8 once we're building with OpenVDB 12 as a minimum.
				throw IECore::Exception( "Fillet mode is only available when Gaffer is built with OpenVDB 12 and above." );
#endif
				break;
		}
	}
}

bool affectedByRadius( LevelSetSmooth::Mode mode )
{
	return
		mode == GafferVDB::LevelSetSmooth::Mode::Box ||
		mode == GafferVDB::LevelSetSmooth::Mode::Gaussian ||
		mode == GafferVDB::LevelSetSmooth::Mode::Median;
}

} // namespace

GAFFER_NODE_DEFINE_TYPE( LevelSetSmooth );

size_t LevelSetSmooth::g_firstPlugIndex = 0;

LevelSetSmooth::LevelSetSmooth( const std::string &name )
	:	Deformer( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new StringPlug( "grids", Plug::In, "surface" ) );
	addChild( new IntPlug( "mode", Plug::In, (int)Mode::Box, (int)Mode::Box, (int)Mode::Fillet ) );
	addChild( new IntPlug( "radius", Plug::In, 1, 0 ) );
	addChild( new IntPlug( "iterations", Plug::In, 1, 0 ) );
}

LevelSetSmooth::~LevelSetSmooth()
{
}

Gaffer::StringPlug *LevelSetSmooth::gridsPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *LevelSetSmooth::gridsPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::IntPlug *LevelSetSmooth::modePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::IntPlug *LevelSetSmooth::modePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

Gaffer::IntPlug *LevelSetSmooth::radiusPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::IntPlug *LevelSetSmooth::radiusPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 2 );
}

Gaffer::IntPlug *LevelSetSmooth::iterationsPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::IntPlug *LevelSetSmooth::iterationsPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 3 );
}

bool LevelSetSmooth::affectsProcessedObject( const Gaffer::Plug *input ) const
{
	return
		Deformer::affectsProcessedObject( input ) ||
		input == gridsPlug() ||
		input == modePlug() ||
		input == radiusPlug() ||
		input == iterationsPlug()
	;
}

void LevelSetSmooth::hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	const bool requiresRadius = affectedByRadius( (Mode)modePlug()->getValue() );

	if( iterationsPlug()->getValue() == 0 || ( requiresRadius && radiusPlug()->getValue() == 0 ) )
	{
		h = inPlug()->objectPlug()->hash();
		return;
	}

	Deformer::hashProcessedObject( path, context, h );

	iterationsPlug()->hash( h );
	gridsPlug()->hash( h );
	modePlug()->hash( h );

	if( requiresRadius )
	{
		radiusPlug()->hash( h );
	}
}

IECore::ConstObjectPtr LevelSetSmooth::computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, const IECore::Object *inputObject ) const
{
	const int iterations = iterationsPlug()->getValue();
	if( iterations == 0 )
	{
		return inputObject;
	}

	const Mode mode = (Mode)modePlug()->getValue();
	const int radius = radiusPlug()->getValue();
	if( affectedByRadius( mode ) && radius == 0 )
	{
		return inputObject;
	}

	const VDBObject *vdbObject = runTimeCast<const VDBObject>( inputObject );
	if( !vdbObject )
	{
		return inputObject;
	}

	const std::string grids = gridsPlug()->getValue();
	VDBObjectPtr result;

	for( const auto &gridName : vdbObject->gridNames() )
	{
		if( !StringAlgo::matchMultiple( gridName, grids ) )
		{
			continue;
		}

		openvdb::GridBase::ConstPtr gridBase = vdbObject->findGrid( gridName );
		if( gridBase->getGridClass() != openvdb::GRID_LEVEL_SET )
		{
			throw IECore::Exception( fmt::format( "Grid '{}' is not a level set", gridName ) );
		}

		openvdb::GridBase::Ptr newGrid;

		if( openvdb::FloatGrid::ConstPtr floatGrid = openvdb::GridBase::constGrid<openvdb::FloatGrid>( gridBase ) )
		{
			openvdb::FloatGrid::Ptr newFloatGrid = openvdb::GridBase::grid<openvdb::FloatGrid> ( floatGrid->deepCopyGrid() );
			newGrid = newFloatGrid;
			filterGrid( *newFloatGrid, mode, radius, iterations, context->canceller() );
		}
		else if( openvdb::DoubleGrid::ConstPtr doubleGrid = openvdb::GridBase::constGrid<openvdb::DoubleGrid>( gridBase ) )
		{
			openvdb::DoubleGrid::Ptr newDoubleGrid = openvdb::GridBase::grid<openvdb::DoubleGrid>( doubleGrid->deepCopyGrid() );
			newGrid = newDoubleGrid;
			filterGrid( *newDoubleGrid, mode, radius, iterations, context->canceller() );
		}
		else
		{
			throw IECore::Exception( fmt::format( "Unable to smooth LevelSet grid: '{}' with type: {}", gridName, gridBase->type() ) );
		}

		// If the interrupter has stopped the VDB operation, throw
		// so that we don't return a partial result.
		Canceller::check( context->canceller() );

		if( !result )
		{
			result = vdbObject->copy();
		}
		result->insertGrid( newGrid );
	}

	return result ? result.get() : inputObject;
}

Gaffer::ValuePlug::CachePolicy LevelSetSmooth::processedObjectComputeCachePolicy() const
{
	return ValuePlug::CachePolicy::TaskCollaboration;
}

bool LevelSetSmooth::adjustBounds() const
{
	return
		Deformer::adjustBounds() &&
		iterationsPlug()->getValue() > 0 &&
		( !affectedByRadius( (Mode)modePlug()->getValue() ) || radiusPlug()->getValue() > 0 )
	;
}
