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

#include "GafferScene/ResamplePrimitiveVariables.h"

#include "IECoreScene/CurvesAlgo.h"
#include "IECoreScene/CurvesPrimitive.h"
#include "IECoreScene/MeshAlgo.h"
#include "IECoreScene/MeshPrimitive.h"
#include "IECoreScene/PointsAlgo.h"
#include "IECoreScene/PointsPrimitive.h"

#include "boost/format.hpp"

using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferScene;

GAFFER_NODE_DEFINE_TYPE( ResamplePrimitiveVariables );

size_t ResamplePrimitiveVariables::g_firstPlugIndex = 0;

ResamplePrimitiveVariables::ResamplePrimitiveVariables( const std::string &name ) : PrimitiveVariableProcessor( name, IECore::PathMatcher::NoMatch )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new IntPlug( "interpolation", Plug::In, PrimitiveVariable::Vertex, PrimitiveVariable::Constant, PrimitiveVariable::FaceVarying ) );
}

ResamplePrimitiveVariables::~ResamplePrimitiveVariables()
{
}

Gaffer::IntPlug *ResamplePrimitiveVariables::interpolationPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

const Gaffer::IntPlug *ResamplePrimitiveVariables::interpolationPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

void ResamplePrimitiveVariables::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	PrimitiveVariableProcessor::affects( input, outputs );

	if( input == interpolationPlug() )
	{
		outputs.push_back( outPlug()->objectPlug() );
	}
}

void ResamplePrimitiveVariables::hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	PrimitiveVariableProcessor::hashProcessedObject( path, context, h );

	interpolationPlug()->hash( h );
}

void ResamplePrimitiveVariables::processPrimitiveVariable( const ScenePath &path, const Gaffer::Context *context, IECoreScene::ConstPrimitivePtr inputGeometry, IECoreScene::PrimitiveVariable &variable ) const
{
	PrimitiveVariable::Interpolation interpolation = static_cast<PrimitiveVariable::Interpolation> ( interpolationPlug()->getValue() );

	if( const MeshPrimitive *meshPrimitive = IECore::runTimeCast<const MeshPrimitive>( inputGeometry.get() ) )
	{
		MeshAlgo::resamplePrimitiveVariable( meshPrimitive, variable, interpolation );
	}
	else if( const CurvesPrimitive *curvesPrimitive = IECore::runTimeCast<const CurvesPrimitive>( inputGeometry.get() ) )
	{
		CurvesAlgo::resamplePrimitiveVariable( curvesPrimitive, variable, interpolation );
	}
	else if( const PointsPrimitive *pointsPrimitive = IECore::runTimeCast<const PointsPrimitive>( inputGeometry.get() ) )
	{
		PointsAlgo::resamplePrimitiveVariable( pointsPrimitive, variable, interpolation );
	}
	else
	{
		throw IECore::Exception( "ResamplePrimitiveVariables : Primitive type must be either Mesh, Curves or Points " );
	}
}
