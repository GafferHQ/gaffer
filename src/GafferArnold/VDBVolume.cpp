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

#include <set>

#include "openvdb/openvdb.h"

#include "IECore/ExternalProcedural.h"
#include "IECore/CompoundData.h"

#include "Gaffer/StringPlug.h"
#include "Gaffer/StringAlgo.h"

#include "GafferArnold/VDBVolume.h"

using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;
using namespace GafferArnold;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

Box3f bound( const std::string &fileName, const std::set<std::string> &sets )
{
	openvdb::initialize();
	openvdb::io::File file( fileName );
	file.open();

	openvdb::BBoxd result;
	for( std::set<std::string>::const_iterator it = sets.begin(), eIt = sets.end(); it != eIt; ++it )
	{
		openvdb::GridBase::Ptr grid = file.readGridMetadata( *it );
		const openvdb::Vec3i &min = grid->metaValue<openvdb::Vec3i>( openvdb::GridBase::META_FILE_BBOX_MIN );
		const openvdb::Vec3i &max = grid->metaValue<openvdb::Vec3i>( openvdb::GridBase::META_FILE_BBOX_MAX );
		result.expand( grid->transform().indexToWorld( openvdb::BBoxd( min - 0.5, max + 0.5 ) ) );
	}

	return Box3f(
		V3f( result.min().x(), result.min().y(), result.min().z() ),
		V3f( result.max().x(), result.max().y(), result.max().z() )
	);
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// VDBVolume
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( VDBVolume );

size_t VDBVolume::g_firstPlugIndex = 0;

VDBVolume::VDBVolume( const std::string &name )
	:	ObjectSource( name, "volume" )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "fileName" ) );
	addChild( new StringPlug( "grids", Plug::In, "density" ) );
	addChild( new StringPlug( "velocityGrids" ) );
	addChild( new FloatPlug( "velocityScale", Plug::In, 1.0f ) );
	addChild( new FloatPlug( "stepSize", Plug::In, 1.0f, 0.0f ) );
	addChild( new StringPlug( "dso", Plug::In, "volume_vdb.so" ) );
}

VDBVolume::~VDBVolume()
{
}

Gaffer::StringPlug *VDBVolume::fileNamePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *VDBVolume::fileNamePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *VDBVolume::gridsPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *VDBVolume::gridsPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

Gaffer::StringPlug *VDBVolume::velocityGridsPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::StringPlug *VDBVolume::velocityGridsPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

Gaffer::FloatPlug *VDBVolume::velocityScalePlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::FloatPlug *VDBVolume::velocityScalePlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 3 );
}

Gaffer::FloatPlug *VDBVolume::stepSizePlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::FloatPlug *VDBVolume::stepSizePlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 4 );
}

Gaffer::StringPlug *VDBVolume::dsoPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 5 );
}

const Gaffer::StringPlug *VDBVolume::dsoPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 5 );
}

void VDBVolume::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ObjectSource::affects( input, outputs );

	if(
		input == fileNamePlug() ||
		input == gridsPlug() ||
		input == stepSizePlug() ||
		input == velocityGridsPlug() ||
		input == velocityScalePlug() ||
		input == dsoPlug()
	)
	{
		outputs.push_back( sourcePlug() );
	}
}

void VDBVolume::hashSource( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	fileNamePlug()->hash( h );
	gridsPlug()->hash( h );
	stepSizePlug()->hash( h );
	velocityGridsPlug()->hash( h );
	velocityScalePlug()->hash( h );
	dsoPlug()->hash( h );
	h.append( context->getFramesPerSecond() );
}

IECore::ConstObjectPtr VDBVolume::computeSource( const Context *context ) const
{
	IECore::ExternalProceduralPtr result = new ExternalProcedural( dsoPlug()->getValue() );

	CompoundDataMap &parameters = result->parameters()->writable();

	parameters["ai:nodeType"] = new StringData( "volume" );
	const std::string fileName = fileNamePlug()->getValue();
	parameters["filename"] = new StringData( fileNamePlug()->getValue() );
	parameters["step_size"] = new FloatData( stepSizePlug()->getValue() );

	StringVectorDataPtr grids = new StringVectorData();
	tokenize( gridsPlug()->getValue(), ' ', grids->writable() );
	parameters["grids"] = grids;

	StringVectorDataPtr velocityGrids = new StringVectorData();
	tokenize( velocityGridsPlug()->getValue(), ' ', velocityGrids->writable() );
	parameters["velocity_grids"] = velocityGrids;

	parameters["velocity_scale"] = new FloatData( velocityScalePlug()->getValue() );
	parameters["velocity_fps"] = new FloatData( context->getFramesPerSecond() );

	if( !fileName.empty() )
	{
		std::set<std::string> allGrids;
		allGrids.insert( grids->readable().begin(), grids->readable().end() );
		allGrids.insert( velocityGrids->readable().begin(), velocityGrids->readable().end() );
		result->setBound( bound( fileName, allGrids ) );
	}
	else
	{
		result->setBound( Box3f( V3f( -0.5 ), V3f( 0.5 ) ) );
	}

	return result;
}
