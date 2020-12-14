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

#include "GafferScene/DeleteCurves.h"

#include "Gaffer/StringPlug.h"

#include "IECoreScene/CurvesAlgo.h"
#include "IECoreScene/CurvesPrimitive.h"

#include "boost/algorithm/string.hpp"
#include "boost/format.hpp"

using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;

GAFFER_NODE_DEFINE_TYPE( DeleteCurves );

size_t DeleteCurves::g_firstPlugIndex = 0;

DeleteCurves::DeleteCurves( const std::string &name )
	:	Deformer( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new StringPlug( "curves", Plug::In, "deleteCurves" ) );
	addChild( new BoolPlug( "invert", Plug::In, false ) );
	addChild( new BoolPlug( "ignoreMissingVariable", Plug::In, false ) );
}

DeleteCurves::~DeleteCurves()
{
}

Gaffer::StringPlug *DeleteCurves::curvesPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *DeleteCurves::curvesPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::BoolPlug *DeleteCurves::invertPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1);
}

const Gaffer::BoolPlug *DeleteCurves::invertPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1);
}

Gaffer::BoolPlug *DeleteCurves::ignoreMissingVariablePlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::BoolPlug *DeleteCurves::ignoreMissingVariablePlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 2 );
}

bool DeleteCurves::affectsProcessedObject( const Gaffer::Plug *input ) const
{
	return
		Deformer::affectsProcessedObject( input ) ||
		input == curvesPlug() ||
		input == invertPlug() ||
		input == ignoreMissingVariablePlug()
	;
}


void DeleteCurves::hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	Deformer::hashProcessedObject( path, context, h );
	curvesPlug()->hash( h );
	invertPlug()->hash( h );
	ignoreMissingVariablePlug()->hash( h );
}

IECore::ConstObjectPtr DeleteCurves::computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, const IECore::Object *inputObject ) const
{
	const CurvesPrimitive *curves = runTimeCast<const CurvesPrimitive>( inputObject );
	if( !curves )
	{
		return inputObject;
	}

	std::string deletePrimVarName = curvesPlug()->getValue();

	/// \todo Remove. We take values verbatim everywhere else in Gaffer, and I don't
	/// see any good reason to differ here.
	if( boost::trim_copy( deletePrimVarName ).empty() )
	{
		return inputObject;
	}

	PrimitiveVariableMap::const_iterator it = curves->variables.find( deletePrimVarName );
	if (it == curves->variables.end())
	{
		if( ignoreMissingVariablePlug()->getValue() )
		{
			return inputObject;
		}

		throw InvalidArgumentException( boost::str( boost::format( "DeleteCurves : No primitive variable \"%s\" found" ) % deletePrimVarName ) );
	}

	return CurvesAlgo::deleteCurves(curves, it->second, invertPlug()->getValue());
}
