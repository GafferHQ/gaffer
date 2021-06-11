//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Image Engine. All rights reserved.
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
//      * Neither the name of Image Engine nor the names of
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

#include "GafferVDB/LevelSetOffset.h"

#include "GafferVDB/Interrupter.h"

#include "IECoreVDB/VDBObject.h"

#include "Gaffer/StringPlug.h"

#include "openvdb/openvdb.h"
#include "openvdb/tools/LevelSetFilter.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreVDB;
using namespace Gaffer;
using namespace GafferVDB;

GAFFER_NODE_DEFINE_TYPE( LevelSetOffset );

size_t LevelSetOffset::g_firstPlugIndex = 0;

LevelSetOffset::LevelSetOffset( const std::string &name )
	:	Deformer( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new StringPlug( "grid", Plug::In, "surface") );
	addChild( new FloatPlug( "offset", Plug::In, 0.5) );
}

LevelSetOffset::~LevelSetOffset()
{
}

Gaffer::StringPlug *LevelSetOffset::gridPlug()
{
	return  getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *LevelSetOffset::gridPlug() const
{
	return  getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::FloatPlug *LevelSetOffset::offsetPlug()
{
	return  getChild<FloatPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::FloatPlug *LevelSetOffset::offsetPlug() const
{
	return  getChild<FloatPlug>( g_firstPlugIndex + 1 );
}

bool LevelSetOffset::affectsProcessedObject( const Gaffer::Plug *input ) const
{
	return input == gridPlug() || input == offsetPlug();
}

void LevelSetOffset::hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	Deformer::hashProcessedObject( path, context, h );

	gridPlug()->hash( h );
	offsetPlug()->hash( h );
}

IECore::ConstObjectPtr LevelSetOffset::computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, const IECore::Object *inputObject ) const
{
	const VDBObject *vdbObject = runTimeCast<const VDBObject>( inputObject );
	if( !vdbObject )
	{
		return inputObject;
	}

	std::string gridName = gridPlug()->getValue();

	openvdb::GridBase::ConstPtr gridBase = vdbObject->findGrid( gridName );

	if (!gridBase)
	{
		return inputObject;
	}

	openvdb::GridBase::Ptr newGrid;
	Interrupter interrupter( context->canceller() );

	if ( openvdb::FloatGrid::ConstPtr floatGrid = openvdb::GridBase::constGrid<openvdb::FloatGrid>( gridBase ) )
	{
		openvdb::FloatGrid::Ptr newFloatGrid = openvdb::GridBase::grid<openvdb::FloatGrid> ( floatGrid->deepCopyGrid() );
		newGrid = newFloatGrid;
		openvdb::tools::LevelSetFilter<openvdb::FloatGrid, openvdb::FloatGrid, Interrupter> filter( *newFloatGrid, &interrupter );
		filter.offset( offsetPlug()->getValue() );
	}
	else if ( openvdb::DoubleGrid::ConstPtr doubleGrid = openvdb::GridBase::constGrid<openvdb::DoubleGrid>( newGrid ) )
	{
		openvdb::DoubleGrid::Ptr newDoubleGrid = openvdb::GridBase::grid<openvdb::DoubleGrid>( doubleGrid->deepCopyGrid() );
		newGrid = newDoubleGrid;
		openvdb::tools::LevelSetFilter<openvdb::DoubleGrid, openvdb::DoubleGrid, Interrupter> filter( *newDoubleGrid, &interrupter );
		filter.offset( offsetPlug()->getValue() );
	}
	else
	{
		throw IECore::Exception( boost::str( boost::format( "Unable to Offset LevelSet grid: '%1%' with type: %2% " ) % gridName % newGrid->type()) );
	}

	VDBObjectPtr newVDBObject = vdbObject->copy();

	newVDBObject->insertGrid( newGrid );

	return newVDBObject;
}

bool LevelSetOffset::affectsProcessedObjectBound( const Gaffer::Plug *input ) const
{
	return
		input == inPlug()->boundPlug() ||
		input == offsetPlug()
	;
}

void LevelSetOffset::hashProcessedObjectBound( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	inPlug()->boundPlug()->hash( h );
	offsetPlug()->hash( h );
}

Imath::Box3f LevelSetOffset::computeProcessedObjectBound( const ScenePath &path, const Gaffer::Context *context ) const
{
	/// \todo `in.bound` includes the child bounds. Ideally we
	/// would have a separate `in.objectBound` with just the bounds
	/// of the input object.
	Imath::Box3f newBound = inPlug()->boundPlug()->getValue();
	float offset = -offsetPlug()->getValue();

	newBound.min -= Imath::V3f(offset, offset, offset);
	newBound.max += Imath::V3f(offset, offset, offset);

	return newBound;
}
