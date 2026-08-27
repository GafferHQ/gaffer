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

#include "GafferVDB/DeleteGrids.h"

#include "IECoreVDB/VDBObject.h"

#include "Gaffer/StringPlug.h"

#include "fmt/format.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreVDB;
using namespace Gaffer;
using namespace GafferVDB;

GAFFER_NODE_DEFINE_TYPE( DeleteGrids );

size_t DeleteGrids::g_firstPlugIndex = 0;

DeleteGrids::DeleteGrids( const std::string &name )
	:	ObjectProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new IntPlug( "mode", Plug::In, Delete, Delete, Keep ) );
	addChild( new StringPlug( "grids", Plug::In, "") );
}

DeleteGrids::~DeleteGrids()
{
}

Gaffer::IntPlug *DeleteGrids::modePlug()
{
	return getChild<Gaffer::IntPlug>( g_firstPlugIndex + 0 );
}

const Gaffer::IntPlug *DeleteGrids::modePlug() const
{
	return getChild<Gaffer::IntPlug>( g_firstPlugIndex + 0 );
}

Gaffer::StringPlug *DeleteGrids::gridsPlug()
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *DeleteGrids::gridsPlug() const
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 1 );
}

bool DeleteGrids::affectsProcessedObject( const Gaffer::Plug *input ) const
{
	return
		ObjectProcessor::affectsProcessedObject( input ) ||
		input == modePlug() ||
		input == gridsPlug()
	;
}

void DeleteGrids::hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ObjectProcessor::hashProcessedObject( path, context, h );
	modePlug()->hash( h );
	gridsPlug()->hash( h );
}

IECore::ConstObjectPtr DeleteGrids::computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, const IECore::Object *inputObject ) const
{
	const VDBObject *vdbObject = runTimeCast<const VDBObject>( inputObject );
	if( !vdbObject )
	{
		return inputObject;
	}

	auto mode = (Mode)modePlug()->getValue();
	const std::string &grids = gridsPlug()->getValue();

	if( mode == Mode::Delete && grids == "" )
	{
		return inputObject;
	}

	VDBObjectPtr result = vdbObject->copy();
	for( const auto &gridName : result->gridNames() )
	{
		const bool match = StringAlgo::matchMultiple( gridName, grids );
		if( match != ( mode == Keep ) )
		{
			result->removeGrid( gridName );
		}
	}

	return result;
}
