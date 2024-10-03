//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2016, Image Engine Design Inc. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//     * Redistributions of source code must retain the above copyright
//       notice, this list of conditions and the following disclaimer.
//
//     * Redistributions in binary form must reproduce the above copyright
//       notice, this list of conditions and the following disclaimer in the
//       documentation and/or other materials provided with the distribution.
//
//     * Neither the name of Image Engine Design nor the names of any
//       other contributors to this software may be used to endorse or
//       promote products derived from this software without specific prior
//       written permission.
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

#include "IECoreArnold/NodeAlgo.h"
#include "IECoreArnold/ParameterAlgo.h"
#include "IECoreArnold/ShapeAlgo.h"

#include "IECoreScene/CurvesAlgo.h"
#include "IECoreScene/CurvesPrimitive.h"

#include "IECore/MessageHandler.h"

#include "ai_array.h"
#include "ai_msg.h" // Required for __AI_FILE__ macro used by `ai_array.h`

#include "fmt/format.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace IECoreArnold;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

const AtString g_pointsArnoldString("points");
const AtString g_basisArnoldString("basis");
const AtString g_bezierArnoldString("bezier");
const AtString g_bSplineArnoldString("b-spline");
const AtString g_catmullRomArnoldString("catmull-rom");
const AtString g_curvesArnoldString("curves");
const AtString g_linearArnoldString("linear");
const AtString g_modeArnoldString("mode");
const AtString g_motionStartArnoldString("motion_start");
const AtString g_motionEndArnoldString("motion_end");
const AtString g_numPointsArnoldString("num_points");
const AtString g_orientationsArnoldString("orientations");
const AtString g_orientedArnoldString("oriented");
const AtString g_uvsArnoldString( "uvs" );

ConstCurvesPrimitivePtr resampleCurves( const CurvesPrimitive *curves, const std::string &messageContext )
{
	if( curves->basis().standardBasis() == StandardCubicBasis::Linear )
	{
		return curves;
	}

	CurvesPrimitivePtr updatedCurves = nullptr;
	for( const auto &it : curves->variables )
	{
		if( it.second.interpolation == PrimitiveVariable::Vertex && it.first != "P" && it.first != "N" )
		{
			if( !updatedCurves )
			{
				updatedCurves = curves->copy();
			}

			// NOTE : Arnold does not support quaternion data and we don't know how to resample it
			//        so remove the primitive variable and issue a warning as we do for linear curves.

			if( it.second.data->typeId() == IECore::QuatfVectorDataTypeId )
			{
				updatedCurves->variables.erase( it.first );
				msg(
					Msg::Warning,
					messageContext,
					fmt::format(
						"Unable to create user parameter \"{}\" for primitive variable of type \"{}\"",
						it.first, it.second.data->typeName()
					)
				);
				continue;
			}

			IECoreScene::CurvesAlgo::resamplePrimitiveVariable( updatedCurves.get(), updatedCurves->variables[it.first], PrimitiveVariable::Varying );
		}
	}

	return updatedCurves ? updatedCurves.get() : curves;
}

void convertUVs( const IECoreScene::CurvesPrimitive *curves, AtNode *node, const std::string &messageContext )
{
	auto it = curves->variables.find( "uv" );
	if( it == curves->variables.end() )
	{
		return;
	}

	if( !runTimeCast<const V2fVectorData>( it->second.data.get() ) )
	{
		msg( Msg::Warning, messageContext, fmt::format( "Variable \"uv\" has unsupported type \"{}\" (expected V2fVectorData).", it->second.data->typeName() ) );
		return;
	}

	PrimitiveVariable::IndexedView<V2f> uvs( it->second );
	AtArray *array = AiArrayAllocate( uvs.size(), 1, AI_TYPE_VECTOR2 );
	for( size_t i = 0, e = uvs.size(); i < e; ++i )
	{
		const V2f &uv = uvs[i];
		AiArraySetVec2( array, i, AtVector2( uv[0], uv[1] ) );
	}

	AiNodeSetArray( node, g_uvsArnoldString, array );
}

AtNode *convertCommon( const IECoreScene::CurvesPrimitive *curves, AtUniverse *universe, const std::string &nodeName, const AtNode *parentNode, const std::string &messageContext )
{

	AtNode *result = AiNode( universe, g_curvesArnoldString, AtString( nodeName.c_str() ), parentNode );

	const std::vector<int> verticesPerCurve = curves->verticesPerCurve()->readable();
	AiNodeSetArray(
		result,
		g_numPointsArnoldString,
		AiArrayConvert( verticesPerCurve.size(), 1, AI_TYPE_INT, (void *)&( verticesPerCurve[0] ) )
	);

	// set basis

	if( curves->basis() == CubicBasisf::bezier() )
	{
		AiNodeSetStr( result, g_basisArnoldString, g_bezierArnoldString );
	}
	else if( curves->basis() == CubicBasisf::bSpline() )
	{
		AiNodeSetStr( result, g_basisArnoldString, g_bSplineArnoldString );
	}
	else if( curves->basis() == CubicBasisf::catmullRom() )
	{
		AiNodeSetStr( result, g_basisArnoldString, g_catmullRomArnoldString );
	}
	else if( curves->basis() == CubicBasisf::linear() )
	{
		AiNodeSetStr( result, g_basisArnoldString, g_linearArnoldString );
	}
	else
	{
		// just accept the default
	}

	// Add UVs and arbitrary user parameters

	convertUVs( curves, result, messageContext );

	const char *ignore[] = { "P", "N", "width", "radius", "uv", nullptr };
	ShapeAlgo::convertPrimitiveVariables( curves, result, ignore, messageContext );

	return result;

}

AtNode *convert( const IECoreScene::CurvesPrimitive *curves, AtUniverse *universe, const std::string &nodeName, const AtNode *parentNode, const std::string &messageContext )
{
	// Arnold (and IECoreArnold::ShapeAlgo) does not support Vertex PrimitiveVariables for
	// cubic CurvesPrimitives, so we resample the variables to Varying first.
	ConstCurvesPrimitivePtr resampledCurves = ::resampleCurves( curves, messageContext );

	AtNode *result = convertCommon( resampledCurves.get(), universe, nodeName, parentNode, messageContext );
	ShapeAlgo::convertP( resampledCurves.get(), result, g_pointsArnoldString, messageContext );
	ShapeAlgo::convertRadius( resampledCurves.get(), result, messageContext );

	// Convert "N" to orientations

	if( const V3fVectorData *n = resampledCurves.get()->variableData<V3fVectorData>( "N", PrimitiveVariable::Vertex ) )
	{
		AiNodeSetStr( result, g_modeArnoldString, g_orientedArnoldString );
		AiNodeSetArray(
			result,
			g_orientationsArnoldString,
			AiArrayConvert( n->readable().size(), 1, AI_TYPE_VECTOR, (void *)&( n->readable()[0] ) )
		);
	}

	return result;
}

AtNode *convert( const std::vector<const IECoreScene::CurvesPrimitive *> &samples, float motionStart, float motionEnd, AtUniverse *universe, const std::string &nodeName, const AtNode *parentNode, const std::string &messageContext )
{
	// Arnold (and IECoreArnold::ShapeAlgo) does not support Vertex PrimitiveVariables for
	// cubic CurvesPrimitives, so we resample the variables to Varying first.
	std::vector<ConstCurvesPrimitivePtr> updatedSamples;
	std::vector<const Primitive *> primitiveSamples;
	// Also convert "N" to orientations
	std::vector<const Data *> nSamples;
	updatedSamples.reserve( samples.size() );
	primitiveSamples.reserve( samples.size() );
	nSamples.reserve( samples.size() );
	for( const CurvesPrimitive *curves : samples )
	{
		ConstCurvesPrimitivePtr resampledCurves = ::resampleCurves( curves, messageContext );
		updatedSamples.push_back( resampledCurves );
		primitiveSamples.push_back( resampledCurves.get() );

		if( const V3fVectorData *n = curves->variableData<V3fVectorData>( "N", PrimitiveVariable::Vertex ) )
		{
			nSamples.push_back( n );
		}
	}

	AtNode *result = convertCommon( updatedSamples.front().get(), universe, nodeName, parentNode, messageContext );

	ShapeAlgo::convertP( primitiveSamples, result, g_pointsArnoldString, messageContext );
	ShapeAlgo::convertRadius( primitiveSamples, result, messageContext );
	if( nSamples.size() == samples.size() )
	{
		AiNodeSetStr( result, g_modeArnoldString, g_orientedArnoldString );
		AtArray *array = ParameterAlgo::dataToArray( nSamples, AI_TYPE_VECTOR );
		AiNodeSetArray( result, g_orientationsArnoldString, array );
	}
	else if( nSamples.size() )
	{
		IECore::msg( IECore::Msg::Warning, messageContext, "Missing sample for primitive variable \"N\" - not setting orientations." );
	}

	AiNodeSetFlt( result, g_motionStartArnoldString, motionStart );
	AiNodeSetFlt( result, g_motionEndArnoldString, motionEnd );

	return result;
}

NodeAlgo::ConverterDescription<CurvesPrimitive> g_description( ::convert, ::convert );

} // namespace
