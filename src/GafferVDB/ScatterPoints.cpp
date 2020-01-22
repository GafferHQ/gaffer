//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2020, Don Boogert. All rights reserved.
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
//      * Neither the name of Don Boogert nor the names of
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


#include "GafferVDB/ScatterPoints.h"
#include "GafferVDB/Interrupter.h"

#include "IECore/StringAlgo.h"

#include "IECoreScene/PointsPrimitive.h"

#include "IECoreVDB/VDBObject.h"

#include "Gaffer/StringPlug.h"

#include "openvdb/openvdb.h"
#include "openvdb/tools/PointScatter.h"


using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreVDB;
using namespace Gaffer;
using namespace GafferVDB;

IE_CORE_DEFINERUNTIMETYPED( ScatterPoints );

size_t ScatterPoints::g_firstPlugIndex = 0;

ScatterPoints::ScatterPoints( const std::string &name )
	: SceneElementProcessor( name, IECore::PathMatcher::NoMatch )
{
	storeIndexOfNextChild(g_firstPlugIndex);

	addChild( new IntPlug( "outputType", Plug::In, 0 ) );
	addChild( new StringPlug( "grid", Plug::In, "density" ) );
	addChild( new BoolPlug( "nonuniform", Plug::In, false ) );
	addChild( new IntPlug( "pointCount", Plug::In, 1000 ) );
	addChild( new FloatPlug( "probability", Plug::In, 1.0f ) );
}

ScatterPoints::~ScatterPoints()
{
}

Gaffer::IntPlug *ScatterPoints::outputTypePlug()
{
	return  getChild<IntPlug>( g_firstPlugIndex );
}

const Gaffer::IntPlug *ScatterPoints::outputTypePlug() const
{
	return  getChild<IntPlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *ScatterPoints::gridPlug()
{
	return  getChild<StringPlug>( g_firstPlugIndex + 1);
}

const Gaffer::StringPlug *ScatterPoints::gridPlug() const
{
	return  getChild<StringPlug>( g_firstPlugIndex + 1);
}

Gaffer::BoolPlug *ScatterPoints::nonuniformPlug()
{
	return  getChild<BoolPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::BoolPlug *ScatterPoints::nonuniformPlug() const
{
	return  getChild<BoolPlug>( g_firstPlugIndex + 2 );
}

Gaffer::IntPlug *ScatterPoints::pointCountPlug()
{
	return  getChild<IntPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::IntPlug *ScatterPoints::pointCountPlug() const
{
	return  getChild<IntPlug>( g_firstPlugIndex + 3 );
}

Gaffer::FloatPlug *ScatterPoints::probabilityPlug()
{
	return  getChild<FloatPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::FloatPlug *ScatterPoints::probabilityPlug() const
{
	return  getChild<FloatPlug>( g_firstPlugIndex + 4 );
}

void ScatterPoints::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	SceneElementProcessor::affects( input, outputs );

	if( input == outputTypePlug()
	 || input == pointCountPlug()
	 || input == probabilityPlug()
	 || input == nonuniformPlug()
	 || input == gridPlug() )
	{
		outputs.push_back( outPlug()->objectPlug() );
		outputs.push_back( outPlug()->boundPlug() );
	}
}

bool ScatterPoints::processesObject() const
{
	return true;
}

void ScatterPoints::hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	SceneElementProcessor::hashProcessedObject( path, context, h );

	outputTypePlug()->hash( h );
	h.append( pointCountPlug()->getValue() );
	h.append( probabilityPlug()->getValue() );
	h.append( nonuniformPlug()->getValue() );
	h.append( gridPlug()->hash() );
}

class PointsWriter {
public:

	PointsWriter()
	: pointsData(new  IECore::V3fVectorData()),
	  points( pointsData->writable() )
	{}

	void add(const openvdb::Vec3R &pos)
	{
		points.emplace_back(pos.x(), pos.y(), pos.z());
	}

	IECore::V3fVectorDataPtr  pointsData;
	std::vector<Imath::V3f> & points;
};

IECore::ConstObjectPtr ScatterPoints::computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::ConstObjectPtr inputObject ) const
{
	const VDBObject *vdbObject = runTimeCast<const VDBObject>(inputObject.get());
	if( !vdbObject )
	{
		return inputObject;
	}

	std::string gridName = gridPlug()->getValue();

	openvdb::GridBase::ConstPtr grid = vdbObject->findGrid( gridName );

	if ( !grid )
	{
		return inputObject;
		// todo raise exception
	}

	Interrupter interrupter( context->canceller() );

	PointsWriter pointWriter;
	std::default_random_engine generator;

	// todo case to other grid types ( dispatch grid type template function? )
	openvdb::FloatGrid::ConstPtr floatGrid = openvdb::GridBase::constGrid<openvdb::FloatGrid>( grid );
	const float spread = 1.0f;

	if ( nonuniformPlug()->getValue() )
	{
		openvdb::tools::NonUniformPointScatter<PointsWriter, std::default_random_engine, Interrupter> nonuniformPointScatter(pointWriter, probabilityPlug()->getValue(), generator, spread, &interrupter);
		nonuniformPointScatter ( *floatGrid );
	}
	else
	{
		openvdb::tools::UniformPointScatter<PointsWriter, std::default_random_engine, Interrupter> uniformPointScatter(pointWriter, (openvdb::Index64) pointCountPlug()->getValue(), generator, spread, &interrupter);
		uniformPointScatter( *floatGrid );
	}

	if ( interrupter.wasInterrupted() )
	{
		throw IECore::Cancelled();
	}

	IECoreScene::PointsPrimitivePtr pointsPrimitive = new IECoreScene::PointsPrimitive( pointWriter.pointsData );
	return pointsPrimitive;
}

bool ScatterPoints::processesBound() const
{
	return true;
}

void ScatterPoints::hashProcessedBound( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	SceneElementProcessor::hashProcessedBound( path, context, h );

	//gridsPlug()->hash( h );
}

Imath::Box3f ScatterPoints::computeProcessedBound( const ScenePath &path, const Gaffer::Context *context, const Imath::Box3f &inputBound ) const
{
	// todo calculate bounds from vdb grids
	return inputBound;
}

// todo output either PointsPrimitive or VDBPoints (drop down option)

