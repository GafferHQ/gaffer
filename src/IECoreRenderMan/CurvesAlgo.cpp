//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2025, Cinesite VFX Ltd. All rights reserved.
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

#include "GeometryAlgo.h"
#include "Loader.h"

#include "IECoreScene/CurvesAlgo.h"
#include "IECoreScene/CurvesPrimitive.h"

using namespace IECore;
using namespace IECoreScene;
using namespace IECoreRenderMan;

namespace
{

void convertCurvesTopology( const IECoreScene::CurvesPrimitive *curves, RtPrimVarList &primVars, const std::string &messageContext )
{
	if( curves->basis().standardBasis() == StandardCubicBasis::Unknown )
	{
		IECore::msg( IECore::Msg::Warning, messageContext, "Unsupported CubicBasis" );
		primVars.SetString( Loader::strings().k_Ri_type, Loader::strings().k_linear );
	}
	else if( curves->basis().standardBasis() == StandardCubicBasis::Linear )
	{
		primVars.SetString( Loader::strings().k_Ri_type, Loader::strings().k_linear );
	}
	else
	{
		primVars.SetString( Loader::strings().k_Ri_type, Loader::strings().k_cubic );
		switch( curves->basis().standardBasis() )
		{
			case StandardCubicBasis::Bezier :
				primVars.SetString( Loader::strings().k_Ri_Basis, Loader::strings().k_bezier );
				break;
			case StandardCubicBasis::BSpline :
				primVars.SetString( Loader::strings().k_Ri_Basis, Loader::strings().k_bspline );
				break;
			case StandardCubicBasis::CatmullRom :
				primVars.SetString( Loader::strings().k_Ri_Basis, Loader::strings().k_catmullrom );
				break;
			default :
				// Should have dealt with Unknown and Linear above
				assert( false );
		}
	}

	primVars.SetString( Loader::strings().k_Ri_wrap, curves->periodic() ? Loader::strings().k_periodic : Loader::strings().k_nonperiodic );
	primVars.SetIntegerDetail( Loader::strings().k_Ri_nvertices, curves->verticesPerCurve()->readable().data(), RtDetailType::k_uniform );
}

RtUString convertCurves( const IECoreScenePreview::Renderer::Samples<const IECoreScene::CurvesPrimitive *> &samples, const IECoreScenePreview::Renderer::SampleTimes &sampleTimes, RtPrimVarList &primVars, const std::string &messageContext )
{
	if( CurvesAlgo::isPinned( samples[0] ) )
	{
		IECoreScenePreview::Renderer::Samples<CurvesPrimitivePtr> processedSamples;
		processedSamples.reserve( samples.size() );
		for( auto sample : samples )
		{
			processedSamples.push_back( sample->copy() );
			CurvesAlgo::convertPinnedToNonPeriodic( processedSamples.back().get() );
		}
		return convertCurves( IECoreScenePreview::Renderer::staticSamplesCast<const IECoreScene::CurvesPrimitive *>( processedSamples ), sampleTimes, primVars, messageContext );
	}

	GeometryAlgo::convertPrimitive( IECoreScenePreview::Renderer::staticSamplesCast<const IECoreScene::Primitive *>( samples ), sampleTimes, primVars, messageContext );
	convertCurvesTopology( samples[0], primVars, messageContext );
	return Loader::strings().k_Ri_Curves;
}

GeometryAlgo::ConverterDescription<CurvesPrimitive> g_curvesConverterDescription( convertCurves );

} // namespace
