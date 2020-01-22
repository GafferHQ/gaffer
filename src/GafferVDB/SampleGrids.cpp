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

#include "GafferVDB/SampleGrids.h"

#include "IECore/StringAlgo.h"

#include "IECoreScene/PointsPrimitive.h"

#include "IECoreVDB/VDBObject.h"

#include "Gaffer/StringPlug.h"
#include "GafferScene/ScenePlug.h"

#include "openvdb/openvdb.h"
#include "openvdb/tools/Interpolation.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreVDB;
using namespace Gaffer;
using namespace GafferScene;
using namespace GafferVDB;

IE_CORE_DEFINERUNTIMETYPED(SampleGrids );

size_t SampleGrids::g_firstPlugIndex = 0;

SampleGrids::SampleGrids(const std::string &name )
: SceneElementProcessor( name, IECore::PathMatcher::NoMatch )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new ScenePlug( "in", Gaffer::Plug::In ) );

	addChild( new StringPlug( "vdbLocation", Gaffer::Plug::In, "/vdb" ) );
	addChild( new StringPlug( "grids", Plug::In, "*" ) );
	addChild( new StringPlug( "position", Plug::In, "P" ) );
	addChild( new IntPlug( "interpolation", Plug::In, 0 ) );


	outPlug()->boundPlug()->setInput( inPlug()->boundPlug() );
	outPlug()->attributesPlug()->setInput( inPlug()->attributesPlug() );
}

SampleGrids::~SampleGrids()
{
}

GafferScene::ScenePlug *SampleGrids::otherPlug()
{
	return  getChild<ScenePlug>( g_firstPlugIndex );
}

const GafferScene::ScenePlug *SampleGrids::otherPlug() const
{
	return  getChild<ScenePlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *SampleGrids::vdbLocationPlug()
{
	return  getChild<StringPlug>( g_firstPlugIndex + 1);
}

const Gaffer::StringPlug *SampleGrids::vdbLocationPlug() const
{
	return  getChild<StringPlug>( g_firstPlugIndex + 1);
}

Gaffer::StringPlug *SampleGrids::gridsPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::StringPlug *SampleGrids::gridsPlug() const
{
	return getChild<const StringPlug>( g_firstPlugIndex + 2);
}

Gaffer::StringPlug *SampleGrids::positionPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::StringPlug *SampleGrids::positionPlug() const
{
	return getChild<const StringPlug>( g_firstPlugIndex + 3 );
}

Gaffer::IntPlug *SampleGrids::interpolationPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::IntPlug *SampleGrids::interpolationPlug() const
{
	return getChild<const IntPlug>( g_firstPlugIndex + 4 );
}

void SampleGrids::affects(const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	SceneElementProcessor::affects( input, outputs );

	if ( input == gridsPlug() ||
		input == positionPlug() ||
		input->parent() == otherPlug() ||
		input ==  positionPlug() ||
		input == vdbLocationPlug() ||
		input == interpolationPlug() )
	{
		outputs.push_back( outPlug()->objectPlug() );
	}
}

bool SampleGrids::processesObject() const
{
	return true;
}

void SampleGrids::hashProcessedObject(const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	SceneElementProcessor::hashProcessedObject( path, context, h );

	ScenePlug::ScenePath p ;
	ScenePlug::stringToPath(vdbLocationPlug()->getValue(), p);

	h.append( positionPlug()->hash() );
	h.append( otherPlug()->objectHash( p ) );
	h.append( otherPlug()->fullTransformHash( p ) );
	h.append( vdbLocationPlug()->hash() );
	h.append( gridsPlug()->hash() );
	h.append( interpolationPlug()->hash() );
}

IECore::ConstObjectPtr SampleGrids::computeProcessedObject(const ScenePath &path, const Gaffer::Context *context, IECore::ConstObjectPtr inputObject ) const
{
	const IECoreScene::Primitive *primitive = runTimeCast<const IECoreScene::Primitive>(inputObject.get());
	if( !primitive )
	{
		return primitive;
	}

	ScenePlug::ScenePath p ;
	ScenePlug::stringToPath(vdbLocationPlug()->getValue(), p);

	IECoreVDB::ConstVDBObjectPtr  vdbObject = runTimeCast<const IECoreVDB::VDBObject>(otherPlug()->object( p ) );
	if( !vdbObject )
	{
		return inputObject;
	}

	auto optionalPositionView = primitive->variableIndexedView<IECore::V3fVectorData>( positionPlug()->getValue() );

	if ( !optionalPositionView )
	{
		return inputObject;
	}

	// todo transform to vdb objects space.
	auto positionView = *optionalPositionView;

	IECoreScene::PrimitiveVariable::Interpolation  interpolation = primitive->variables.find( positionPlug()->getValue() )->second.interpolation;

	std::vector<std::string> grids = vdbObject->gridNames();

	std::string gridsToSample = gridsPlug()->getValue();

	IECoreScene::PrimitivePtr newPrimitive = primitive->copy();

	for (const auto &gridName : grids )
	{
		if ( !IECore::StringAlgo::matchMultiple( gridName, gridsToSample ) )
		{
			continue;
		}

		openvdb::GridBase::ConstPtr grid = vdbObject->findGrid( gridName );
		openvdb::FloatGrid::ConstPtr floatGrid = openvdb::GridBase::constGrid<openvdb::FloatGrid>( grid );

		if ( !floatGrid )
		{
			continue;
		}

		// todo template function for sampler type (box, point, quadratic)
		openvdb::tools::GridSampler<openvdb::FloatGrid , openvdb::tools::BoxSampler> sampler( *floatGrid );

		// todo template function for dispatching to various GridTypes
		IECore::FloatVectorDataPtr newPrimvarData = new IECore::FloatVectorData();


		// sample the grid with multiple threads
		for ( size_t i = 0; i < positionView.size(); ++i )
		{
			// todo convert template for openvdb <-> imath types
			openvdb::FloatGrid::ValueType worldValue = sampler.wsSample(openvdb::Vec3R(positionView[i][0], positionView[i][1], positionView[i][2]));
			newPrimvarData->writable().push_back(worldValue);

			if ( i % 1024 == 0)
			{
				IECore::Canceller::check( context->canceller() );
			}
		}

		// todo think about overwriting existing primvar data
		newPrimitive->variables[gridName] = IECoreScene::PrimitiveVariable(interpolation, newPrimvarData);
	}

	return newPrimitive;
}
