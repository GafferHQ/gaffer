//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2015, Image Engine. All rights reserved.
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

#include "openvdb/openvdb.h"
#include "openvdb/tools/LevelSetFilter.h"

#include "Gaffer/StringPlug.h"

#include "GafferVDB/VDBObject.h"
#include "GafferVDB/VDBLevelSetOffset.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferVDB;

IE_CORE_DEFINERUNTIMETYPED( VDBLevelSetOffset );

size_t VDBLevelSetOffset::g_firstPlugIndex = 0;

VDBLevelSetOffset::VDBLevelSetOffset( const std::string &name )
	:	SceneElementProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new StringPlug( "gridName", Plug::In, "density") );
	addChild( new FloatPlug( "offset", Plug::In, 0.5) );
}

VDBLevelSetOffset::~VDBLevelSetOffset()
{
}

Gaffer::StringPlug *VDBLevelSetOffset::gridNamePlug()
{
	return  getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *VDBLevelSetOffset::gridNamePlug() const
{
	return  getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::FloatPlug *VDBLevelSetOffset::offsetPlug()
{
	return  getChild<FloatPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::FloatPlug *VDBLevelSetOffset::offsetPlug() const
{
	return  getChild<FloatPlug>( g_firstPlugIndex + 1 );
}

void VDBLevelSetOffset::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	SceneElementProcessor::affects( input, outputs );

	if( input == gridNamePlug() || input == offsetPlug() )
	{
		outputs.push_back( outPlug()->objectPlug() );
	}
}

bool VDBLevelSetOffset::processesObject() const
{
	return true;
}

void VDBLevelSetOffset::hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	SceneElementProcessor::hashProcessedObject( path, context, h );

	gridNamePlug()->hash( h );
	offsetPlug()->hash( h );
}

IECore::ConstObjectPtr VDBLevelSetOffset::computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::ConstObjectPtr inputObject ) const
{
	const VDBObject *vdbObject = runTimeCast<const VDBObject>(inputObject.get());
	if( !vdbObject )
	{
		return inputObject;
	}

	std::string gridName = gridNamePlug()->getValue();

	openvdb::GridBase::ConstPtr gridBase = vdbObject->findGrid( gridName );

	if (!gridBase)
	{
		return inputObject;
	}

	openvdb::GridBase::Ptr newGrid;

	if ( openvdb::FloatGrid::ConstPtr floatGrid = openvdb::GridBase::constGrid<openvdb::FloatGrid>( gridBase ) )
	{
		openvdb::FloatGrid::Ptr newFloatGrid = openvdb::GridBase::grid<openvdb::FloatGrid> ( floatGrid->deepCopyGrid() );
		newGrid = newFloatGrid;
		openvdb::tools::LevelSetFilter <openvdb::FloatGrid> filter( *newFloatGrid );
		filter.offset( offsetPlug()->getValue() );
	}
	else if ( openvdb::DoubleGrid::ConstPtr doubleGrid = openvdb::GridBase::constGrid<openvdb::DoubleGrid>( newGrid ) )
	{
		openvdb::DoubleGrid::Ptr newDoubleGrid = openvdb::GridBase::grid<openvdb::DoubleGrid>( doubleGrid->deepCopyGrid() );
		newGrid = newDoubleGrid;
		openvdb::tools::LevelSetFilter <openvdb::DoubleGrid> filter( *newDoubleGrid );
		filter.offset( offsetPlug()->getValue() );
	}
	else
	{
		throw IECore::Exception( boost::str( boost::format( "Unable to Offset LevelSet grid: '%1%' with type: %2% " ) % gridName % newGrid->type()) );
	}

	VDBObjectPtr newVDBObject = vdbObject->copy();

	newVDBObject->removeGrid( gridName );
	newVDBObject->addGrid( newGrid );

	return newVDBObject;
}
