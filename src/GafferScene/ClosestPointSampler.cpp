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

#include "GafferScene/ClosestPointSampler.h"

using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( ClosestPointSampler );

size_t ClosestPointSampler::g_firstPlugIndex = 0;

ClosestPointSampler::ClosestPointSampler( const std::string &name )
	:	PrimitiveSampler( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new StringPlug( "position", Plug::In, "P" ) );
}

ClosestPointSampler::~ClosestPointSampler()
{
}

Gaffer::StringPlug *ClosestPointSampler::positionPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *ClosestPointSampler::positionPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

bool ClosestPointSampler::affectsSamplingFunction( const Gaffer::Plug *input ) const
{
	return PrimitiveSampler::affectsSamplingFunction( input ) || input == positionPlug();
}

void ClosestPointSampler::hashSamplingFunction( IECore::MurmurHash &h ) const
{
	PrimitiveSampler::hashSamplingFunction( h );
	positionPlug()->hash( h );
}

PrimitiveSampler::SamplingFunction ClosestPointSampler::computeSamplingFunction( const IECoreScene::Primitive *primitive, IECoreScene::PrimitiveVariable::Interpolation &interpolation ) const
{
	const std::string position = positionPlug()->getValue();
	if( position.empty() )
	{
		return SamplingFunction();
	}

	auto it = primitive->variables.find( position );
	if( it == primitive->variables.end() )
	{
		throw IECore::Exception( "No primitive variable named \"" + position + "\"" );
	}

	interpolation = it->second.interpolation;
	PrimitiveVariable::IndexedView<V3f> positionView( it->second );

	return [positionView] ( const PrimitiveEvaluator &evaluator, size_t index, const M44f &transform, PrimitiveEvaluator::Result &result ) {
		return evaluator.closestPoint( positionView[index] * transform, &result );
	};
}

