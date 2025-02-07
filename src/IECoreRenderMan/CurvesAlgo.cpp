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

#include "IECoreScene/CurvesPrimitive.h"

#include "RixPredefinedStrings.hpp"

using namespace IECore;
using namespace IECoreScene;
using namespace IECoreRenderMan;

namespace
{

void convertCurvesTopology( const IECoreScene::CurvesPrimitive *curves, RtPrimVarList &primVars, const std::string &messageContext )
{
	primVars.SetDetail(
		curves->variableSize( PrimitiveVariable::Uniform ),
		curves->variableSize( PrimitiveVariable::Vertex ),
		curves->variableSize( PrimitiveVariable::Varying ),
		curves->variableSize( PrimitiveVariable::FaceVarying )
	);

	if( curves->basis().standardBasis() == StandardCubicBasis::Unknown )
	{
		IECore::msg( IECore::Msg::Warning, messageContext, "Unsupported CubicBasis" );
		primVars.SetString( Rix::k_Ri_type, Rix::k_linear );
	}
	else if( curves->basis().standardBasis() == StandardCubicBasis::Linear )
	{
		primVars.SetString( Rix::k_Ri_type, Rix::k_linear );
	}
	else
	{
		primVars.SetString( Rix::k_Ri_type, Rix::k_cubic );
		switch( curves->basis().standardBasis() )
		{
			case StandardCubicBasis::Bezier :
				primVars.SetString( Rix::k_Ri_Basis, Rix::k_bezier );
				break;
			case StandardCubicBasis::BSpline :
				primVars.SetString( Rix::k_Ri_Basis, Rix::k_bspline );
				break;
			case StandardCubicBasis::CatmullRom :
				primVars.SetString( Rix::k_Ri_Basis, Rix::k_catmullrom );
				break;
			default :
				// Should have dealt with Unknown and Linear above
				assert( false );
		}
	}

	primVars.SetString( Rix::k_Ri_wrap, curves->periodic() ? Rix::k_periodic : Rix::k_nonperiodic );
	primVars.SetIntegerDetail( Rix::k_Ri_nvertices, curves->verticesPerCurve()->readable().data(), RtDetailType::k_uniform );
}

RtUString convertStaticCurves( const IECoreScene::CurvesPrimitive *curves, RtPrimVarList &primVars, const std::string &messageContext )
{
	convertCurvesTopology( curves, primVars, messageContext );
	GeometryAlgo::convertPrimitiveVariables( curves, primVars, messageContext );
	return Rix::k_Ri_Curves;
}

RtUString convertAnimatedCurves( const std::vector<const IECoreScene::CurvesPrimitive *> &samples, const std::vector<float> &sampleTimes, RtPrimVarList &primVars, const std::string &messageContext )
{
	convertCurvesTopology( samples[0], primVars, messageContext );
	GeometryAlgo::convertPrimitiveVariables( reinterpret_cast<const std::vector<const IECoreScene::Primitive *> &>( samples ), sampleTimes, primVars, messageContext );
	return Rix::k_Ri_Curves;
}

GeometryAlgo::ConverterDescription<CurvesPrimitive> g_curvesConverterDescription( convertStaticCurves, convertAnimatedCurves );

} // namespace
