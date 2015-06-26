//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

#include "IECore/CurvesPrimitive.h"
#include "IECore/CubicBasis.h"

#include "Gaffer/StringPlug.h"

#include "GafferScene/CurvesType.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( CurvesType );

size_t CurvesType::g_firstPlugIndex = 0;

CurvesType::CurvesType( const std::string &name )
	:	SceneElementProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "basis", Plug::In, "" ) );

	// Fast pass-throughs for things we don't modify
	outPlug()->attributesPlug()->setInput( inPlug()->attributesPlug() );
	outPlug()->transformPlug()->setInput( inPlug()->transformPlug() );
	outPlug()->boundPlug()->setInput( inPlug()->boundPlug() );
}

CurvesType::~CurvesType()
{
}

Gaffer::StringPlug *CurvesType::basisPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *CurvesType::basisPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

void CurvesType::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	SceneElementProcessor::affects( input, outputs );

	if( input == basisPlug() )
	{
		outputs.push_back( outPlug()->objectPlug() );
	}
}

bool CurvesType::processesObject() const
{
	return true;
}

void CurvesType::hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	basisPlug()->hash( h );
}

IECore::ConstObjectPtr CurvesType::computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::ConstObjectPtr inputObject ) const
{
	const CurvesPrimitive *inputGeometry = runTimeCast<const CurvesPrimitive>( inputObject.get() );
	if( !inputGeometry )
	{
		return inputObject;
	}

	std::string basisType = basisPlug()->getValue();
	if( basisType == "" )
	{
		// unchanged
		return inputObject;
	}

	IECore::CurvesPrimitivePtr result = inputGeometry->copy();
	IECore::CubicBasisf basis = CubicBasisf::linear();
	if( basisType == "linear" )
	{
		basis = IECore::CubicBasisf::linear();
	}
	else if( basisType == "catmullRom" )
	{
		basis = IECore::CubicBasisf::catmullRom();
	}
	else if( basisType == "bSpline" )
	{
		basis = IECore::CubicBasisf::bSpline();
	}
	else
	{
		throw Exception( "CurvesType::computeProcessedObject: Unrecognized basis " + basisType );
	}

	result->setTopology( result->verticesPerCurve(), basis, result->periodic() );

	return result;
}
