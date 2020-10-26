//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

#include "GafferArnold/ArnoldVDB.h"

#include "Gaffer/StringPlug.h"

#include "IECoreScene/ExternalProcedural.h"

#include "IECore/CompoundData.h"
#include "IECore/StringAlgo.h"

#include "openvdb/openvdb.h"

#include <set>

using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;
using namespace GafferArnold;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

Box3f boundAndAutoStepSize( const std::string &fileName, const std::set<std::string> &sets, float &autoStepSize )
{
	openvdb::initialize();
	openvdb::io::File file( fileName );
	// VDB has the crazy default behaviour of making a local
	// copy of the file and then opening that instead. Even if
	// the file is local already. Even if all you do is query
	// metadata. Restore sanity!
	file.setCopyMaxBytes( 0 );
	file.open();

	autoStepSize = Imath::limits<float>::max();

	openvdb::BBoxd result;
	for( std::set<std::string>::const_iterator it = sets.begin(), eIt = sets.end(); it != eIt; ++it )
	{
		openvdb::GridBase::Ptr grid = file.readGridMetadata( *it );
		const openvdb::Vec3i &min = grid->metaValue<openvdb::Vec3i>( openvdb::GridBase::META_FILE_BBOX_MIN );
		const openvdb::Vec3i &max = grid->metaValue<openvdb::Vec3i>( openvdb::GridBase::META_FILE_BBOX_MAX );
		result.expand( grid->transform().indexToWorld( openvdb::BBoxd( min - 0.5, max + 0.5 ) ) );

		const openvdb::Vec3d voxelSize = grid->voxelSize();
		autoStepSize = std::min( std::min( (double)autoStepSize, voxelSize.x() ), std::min( voxelSize.y(), voxelSize.z() ) );
	}

	return Box3f(
		V3f( result.min().x(), result.min().y(), result.min().z() ),
		V3f( result.max().x(), result.max().y(), result.max().z() )
	);
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// ArnoldVDB
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( ArnoldVDB );

size_t ArnoldVDB::g_firstPlugIndex = 0;

ArnoldVDB::ArnoldVDB( const std::string &name )
	:	ObjectSource( name, "volume" )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "fileName" ) );
	addChild( new StringPlug( "grids", Plug::In, "density" ) );
	addChild( new StringPlug( "velocityGrids" ) );
	addChild( new FloatPlug( "velocityScale", Plug::In, 1.0f ) );
	addChild( new FloatPlug( "stepSize", Plug::In, 0.0f, 0.0f ) );
	addChild( new FloatPlug( "stepScale", Plug::In, 1.0f, 0.0f ) );
}

ArnoldVDB::~ArnoldVDB()
{
}

Gaffer::StringPlug *ArnoldVDB::fileNamePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *ArnoldVDB::fileNamePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *ArnoldVDB::gridsPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *ArnoldVDB::gridsPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

Gaffer::StringPlug *ArnoldVDB::velocityGridsPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::StringPlug *ArnoldVDB::velocityGridsPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

Gaffer::FloatPlug *ArnoldVDB::velocityScalePlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::FloatPlug *ArnoldVDB::velocityScalePlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 3 );
}

Gaffer::FloatPlug *ArnoldVDB::stepSizePlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::FloatPlug *ArnoldVDB::stepSizePlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 4 );
}

Gaffer::FloatPlug *ArnoldVDB::stepScalePlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 5 );
}

const Gaffer::FloatPlug *ArnoldVDB::stepScalePlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 5 );
}

void ArnoldVDB::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ObjectSource::affects( input, outputs );

	if(
		input == fileNamePlug() ||
		input == gridsPlug() ||
		input == velocityGridsPlug() ||
		input == velocityScalePlug() ||
		input == stepSizePlug() ||
		input == stepScalePlug()
	)
	{
		outputs.push_back( sourcePlug() );
	}
}

void ArnoldVDB::hashSource( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	fileNamePlug()->hash( h );
	gridsPlug()->hash( h );
	velocityGridsPlug()->hash( h );
	velocityScalePlug()->hash( h );
	stepSizePlug()->hash( h );
	stepScalePlug()->hash( h );
	h.append( context->getFramesPerSecond() );
}

IECore::ConstObjectPtr ArnoldVDB::computeSource( const Context *context ) const
{
	IECoreScene::ExternalProceduralPtr result = new ExternalProcedural( "volume" );
	const std::string fileName = fileNamePlug()->getValue();
	const std::string gridsString = gridsPlug()->getValue();
	if( fileName.empty() || gridsString.empty() )
	{
		result->setBound( Box3f( V3f( -0.5 ), V3f( 0.5 ) ) );
		return result;
	}

	CompoundDataMap &parameters = result->parameters()->writable();

	parameters["filename"] = new StringData( fileNamePlug()->getValue() );

	StringVectorDataPtr grids = new StringVectorData();
	StringAlgo::tokenize( gridsString, ' ', grids->writable() );
	parameters["grids"] = grids;

	StringVectorDataPtr velocityGrids = new StringVectorData();
	StringAlgo::tokenize( velocityGridsPlug()->getValue(), ' ', velocityGrids->writable() );
	parameters["velocity_grids"] = velocityGrids;

	parameters["velocity_scale"] = new FloatData( velocityScalePlug()->getValue() );
	parameters["velocity_fps"] = new FloatData( context->getFramesPerSecond() );

	std::set<std::string> allGrids;
	allGrids.insert( grids->readable().begin(), grids->readable().end() );
	allGrids.insert( velocityGrids->readable().begin(), velocityGrids->readable().end() );

	float autoStepSize = 0;
	const Box3f bound = boundAndAutoStepSize( fileName, allGrids, autoStepSize );

	result->setBound( bound );

	const float stepSize = stepSizePlug()->getValue();
	const float stepScale = stepScalePlug()->getValue();
	parameters["step_size"] = new FloatData(
		( stepSize <= 0.0f ? autoStepSize : stepSize ) * stepScale
	);

	return result;
}
