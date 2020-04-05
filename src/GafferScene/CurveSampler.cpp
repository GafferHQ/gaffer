//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2020, John Haddon. All rights reserved.
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

#include "GafferScene/CurveSampler.h"

#include "IECoreScene/CurvesPrimitive.h"
#include "IECoreScene/CurvesPrimitiveEvaluator.h"

using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( CurveSampler );

size_t CurveSampler::g_firstPlugIndex = 0;

CurveSampler::CurveSampler( const std::string &name )
	:	PrimitiveSampler( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new StringPlug( "curveIndex", Plug::In, "" ) );
	addChild( new StringPlug( "v", Plug::In, "" ) );
}

CurveSampler::~CurveSampler()
{
}

Gaffer::StringPlug *CurveSampler::curveIndexPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *CurveSampler::curveIndexPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *CurveSampler::vPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *CurveSampler::vPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

bool CurveSampler::affectsSamplingFunction( const Gaffer::Plug *input ) const
{
	return
		PrimitiveSampler::affectsSamplingFunction( input ) ||
		input == curveIndexPlug() ||
		input == vPlug()
	;
}

void CurveSampler::hashSamplingFunction( IECore::MurmurHash &h ) const
{
	PrimitiveSampler::hashSamplingFunction( h );
	curveIndexPlug()->hash( h );
	vPlug()->hash( h );
}

PrimitiveSampler::SamplingFunction CurveSampler::computeSamplingFunction( const IECoreScene::Primitive *primitive, IECoreScene::PrimitiveVariable::Interpolation &interpolation ) const
{
	const std::string curveIndex = curveIndexPlug()->getValue();
	const std::string v = vPlug()->getValue();

	boost::optional<PrimitiveVariable::IndexedView<int>> curveIndexView;
	boost::optional<PrimitiveVariable::IndexedView<float>> vView;

	if( !curveIndex.empty() )
	{
		auto it = primitive->variables.find( curveIndex );
		if( it == primitive->variables.end() )
		{
			throw IECore::Exception( "No primitive variable named \"" + curveIndex + "\"" );
		}
		curveIndexView.emplace( it->second );
		interpolation = it->second.interpolation;
	}

	if( !v.empty() )
	{
		auto it = primitive->variables.find( v );
		if( it == primitive->variables.end() )
		{
			throw IECore::Exception( "No primitive variable named \"" + v + "\"" );
		}
		vView.emplace( it->second );
		if( !curveIndex.empty() )
		{
			if( interpolation != it->second.interpolation )
			{
				throw IECore::Exception( "Primitive variables \"" + curveIndex + "\" and \"" + v + "\" have different interpolation" );
			}
		}
		else
		{
			interpolation = it->second.interpolation;
		}
	}

	return [curveIndexView, vView] ( const PrimitiveEvaluator &evaluator, size_t index, const M44f &transform, PrimitiveEvaluator::Result &result ) {
		auto curvesEvaluator = runTimeCast<const CurvesPrimitiveEvaluator>( &evaluator );
		if( !curvesEvaluator )
		{
			return false;
		}

		return curvesEvaluator->pointAtV(
			curveIndexView ? (*curveIndexView)[index] : 0,
			vView ? (*vView)[index] : 0.0f,
			&result
		);
	};
}

