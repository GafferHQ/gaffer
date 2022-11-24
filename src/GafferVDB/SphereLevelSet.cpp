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

#include "GafferVDB/SphereLevelSet.h"
#include "GafferVDB/Interrupter.h"

#include "Gaffer/StringPlug.h"

#include "IECoreVDB/VDBObject.h"

#include "openvdb/tools/LevelSetSphere.h"

using namespace Gaffer;
using namespace GafferScene;
using namespace GafferVDB;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace IECoreVDB;

IE_CORE_DEFINERUNTIMETYPED( SphereLevelSet );

size_t SphereLevelSet::g_firstPlugIndex = 0;

SphereLevelSet::SphereLevelSet( const std::string &name )
: ObjectSource( name, "sphere" )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "grid", Plug::In, "surface") );
	addChild( new FloatPlug( "radius", Plug::In, 1.0f, 0.0f ) );
	addChild( new V3fPlug( "center", Plug::In, V3f( 0.0f, 0.0f, 0.0f ) ) );
	addChild( new FloatPlug( "voxelSize", Plug::In, 0.1f, 0.0001f ) );
	addChild( new FloatPlug( "halfWidth", Plug::In, (float) openvdb::LEVEL_SET_HALF_WIDTH, 1.0001f ) );
}

SphereLevelSet::~SphereLevelSet()
{
}

Gaffer::StringPlug *SphereLevelSet::gridPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *SphereLevelSet::gridPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::FloatPlug *SphereLevelSet::radiusPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::FloatPlug *SphereLevelSet::radiusPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 1 );
}

Gaffer::V3fPlug *SphereLevelSet::centerPlug()
{
	return getChild<V3fPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::V3fPlug *SphereLevelSet::centerPlug() const
{
	return getChild<V3fPlug>( g_firstPlugIndex + 2 );
}

Gaffer::FloatPlug *SphereLevelSet::voxelSizePlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::FloatPlug *SphereLevelSet::voxelSizePlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 3 );
}

Gaffer::FloatPlug *SphereLevelSet::halfWidthPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::FloatPlug *SphereLevelSet::halfWidthPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 4 );
}

void SphereLevelSet::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	ObjectSource::affects( input, outputs );

	if(
		input == gridPlug() ||
		input == radiusPlug() ||
		input->parent() == centerPlug() ||
		input == voxelSizePlug() ||
		input == halfWidthPlug()
	)
	{
		outputs.push_back( sourcePlug() );
	}
}

void SphereLevelSet::hashSource( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	gridPlug()->hash( h );
	radiusPlug()->hash( h );
	centerPlug()->hash( h );
	voxelSizePlug()->hash( h );
	halfWidthPlug()->hash( h );
}

IECore::ConstObjectPtr SphereLevelSet::computeSource( const Context *context ) const
{
	Interrupter interrupter( context->canceller() );

	const auto center = centerPlug()->getValue();

	openvdb::FloatGrid::Ptr grid = openvdb::tools::createLevelSetSphere<openvdb::FloatGrid, Interrupter>(
		radiusPlug()->getValue(),
		openvdb::Vec3f(center.x, center.y, center.z),
		voxelSizePlug()->getValue(),
		halfWidthPlug()->getValue(),
		&interrupter
	);

	Canceller::check( context->canceller() );

	grid->addStatsMetadata();
	grid->setName( gridPlug()->getValue() );

	VDBObjectPtr newVDBObject = new VDBObject();
	newVDBObject->insertGrid( grid );

	return newVDBObject;

}

Gaffer::ValuePlug::CachePolicy SphereLevelSet::computeCachePolicy( const Gaffer::ValuePlug *output ) const
{
	if( output == sourcePlug() )
	{
		return ValuePlug::CachePolicy::TaskCollaboration;
	}
	return ObjectSource::computeCachePolicy( output );
}
