//////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/DeletePoints.h"

#include "Gaffer/StringPlug.h"

#include "IECoreScene/PointsAlgo.h"
#include "IECoreScene/PointsPrimitive.h"

#include "boost/algorithm/string.hpp"
#include "boost/format.hpp"

using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;

GAFFER_NODE_DEFINE_TYPE( DeletePoints );

size_t DeletePoints::g_firstPlugIndex = 0;

DeletePoints::DeletePoints( const std::string &name )
	:	Deformer( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new StringPlug( "points", Plug::In, "deletePoints" ) );
	addChild( new BoolPlug( "invert", Plug::In, false ) );
}

DeletePoints::~DeletePoints()
{
}

Gaffer::StringPlug *DeletePoints::pointsPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *DeletePoints::pointsPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::BoolPlug *DeletePoints::invertPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1);
}

const Gaffer::BoolPlug *DeletePoints::invertPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1);
}

bool DeletePoints::affectsProcessedObject( const Gaffer::Plug *input ) const
{
	return
		Deformer::affectsProcessedObject( input ) ||
		input == pointsPlug() ||
		input == invertPlug()
	;
}

void DeletePoints::hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	Deformer::hashProcessedObject( path, context, h );
	pointsPlug()->hash( h );
	invertPlug()->hash( h );
}

IECore::ConstObjectPtr DeletePoints::computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, const IECore::Object *inputObject ) const
{
	const PointsPrimitive *points = runTimeCast<const PointsPrimitive>( inputObject );
	if( !points )
	{
		return inputObject;
	}

	std::string deletePrimVarName = pointsPlug()->getValue();

	if( deletePrimVarName.empty() )
	{
		return inputObject;
	}

	PrimitiveVariableMap::const_iterator it = points->variables.find( deletePrimVarName );
	if( it == points->variables.end() )
	{
		throw InvalidArgumentException( boost::str( boost::format( "DeletePoints : No primitive variable \"%s\" found" ) % deletePrimVarName ) );
	}

	return PointsAlgo::deletePoints( points, it->second, invertPlug()->getValue() );
}
