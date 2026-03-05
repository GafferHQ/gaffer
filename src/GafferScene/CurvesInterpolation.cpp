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

#include "GafferScene/CurvesInterpolation.h"

#include "IECoreScene/CurvesAlgo.h"
#include "IECoreScene/CurvesPrimitive.h"

using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;

GAFFER_NODE_DEFINE_TYPE( CurvesInterpolation );

size_t CurvesInterpolation::g_firstPlugIndex = 0;

CurvesInterpolation::CurvesInterpolation( const std::string &name )
	:	ObjectProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	using Basis = IECore::StandardCubicBasis;
	addChild( new OptionalValuePlug( "basis", new IntPlug( "value", Plug::In, (int)Basis::Linear, (int)Basis::Linear, (int)Basis::CatmullRom ) ) );
	using Wrap = IECoreScene::CurvesPrimitive::Wrap;
	addChild( new OptionalValuePlug( "wrap", new IntPlug( "value", Plug::In, (int)Wrap::NonPeriodic, (int)Wrap::NonPeriodic, (int)Wrap::Pinned ) ) );
	addChild( new BoolPlug( "expandPinned" ) );
}

CurvesInterpolation::~CurvesInterpolation()
{
}

Gaffer::OptionalValuePlug *CurvesInterpolation::basisPlug()
{
	return getChild<OptionalValuePlug>( g_firstPlugIndex );
}

const Gaffer::OptionalValuePlug *CurvesInterpolation::basisPlug() const
{
	return getChild<OptionalValuePlug>( g_firstPlugIndex );
}

Gaffer::OptionalValuePlug *CurvesInterpolation::wrapPlug()
{
	return getChild<OptionalValuePlug>( g_firstPlugIndex + 1 );
}

const Gaffer::OptionalValuePlug *CurvesInterpolation::wrapPlug() const
{
	return getChild<OptionalValuePlug>( g_firstPlugIndex + 1 );
}

Gaffer::BoolPlug *CurvesInterpolation::expandPinnedPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::BoolPlug *CurvesInterpolation::expandPinnedPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 2 );
}

bool CurvesInterpolation::affectsProcessedObject( const Gaffer::Plug *input ) const
{
	return
		ObjectProcessor::affectsProcessedObject( input ) ||
		input->parent() == basisPlug() ||
		input->parent() == wrapPlug() ||
		input == expandPinnedPlug()
	;
}

void CurvesInterpolation::hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	const bool basisEnabled = basisPlug()->enabledPlug()->getValue();
	const bool wrapEnabled = wrapPlug()->enabledPlug()->getValue();

	if( !wrapEnabled && !basisEnabled )
	{
		h = inPlug()->objectPlug()->hash();
		return;
	}

	ObjectProcessor::hashProcessedObject( path, context, h );

	h.append( basisEnabled );
	if( basisEnabled )
	{
		basisPlug()->valuePlug()->hash( h );
	}

	h.append( wrapEnabled );
	if( wrapEnabled )
	{
		wrapPlug()->valuePlug()->hash( h );
		expandPinnedPlug()->hash( h );
	}
}

IECore::ConstObjectPtr CurvesInterpolation::computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, const IECore::Object *inputObject ) const
{
	const CurvesPrimitive *inputCurves = runTimeCast<const CurvesPrimitive>( inputObject );
	if( !inputCurves )
	{
		return inputObject;
	}

	const bool basisEnabled = basisPlug()->enabledPlug()->getValue();
	const bool wrapEnabled = wrapPlug()->enabledPlug()->getValue();
	if( !wrapEnabled && !basisEnabled )
	{
		return inputObject;
	}

	CubicBasisf basis = inputCurves->basis();
	if( basisEnabled )
	{
		basis = CubicBasisf(
			(StandardCubicBasis)basisPlug()->valuePlug<IntPlug>()->getValue()
		);
	}

	CurvesPrimitive::Wrap wrap = inputCurves->wrap();
	if( wrapEnabled )
	{
		wrap = (CurvesPrimitive::Wrap)wrapPlug()->valuePlug<IntPlug>()->getValue();
	}

	if( wrap == inputCurves->wrap() && basis == inputCurves->basis() )
	{
		return inputObject;
	}

	IECoreScene::CurvesPrimitivePtr result = inputCurves->copy();

	if(
		CurvesAlgo::isPinned( inputCurves ) &&
		wrap == CurvesPrimitive::Wrap::NonPeriodic &&
		expandPinnedPlug()->getValue()
	)
	{
		CurvesAlgo::convertPinnedToNonPeriodic( result.get(), context->canceller() );
	}
	else
	{
		result->setTopology( result->verticesPerCurve(), basis, wrap );
	}

	return result;
}
