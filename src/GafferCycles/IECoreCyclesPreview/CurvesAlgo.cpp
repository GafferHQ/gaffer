//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2018, Alex Fuller. All rights reserved.
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

#include "GafferCycles/IECoreCyclesPreview/GeometryAlgo.h"

#include "SceneAlgo.h"

#include "IECoreScene/CurvesPrimitive.h"

#include "IECore/Interpolator.h"
#include "IECore/MessageHandler.h"
#include "IECore/SimpleTypedData.h"

// Cycles
#include "scene/geometry.h"
#include "scene/hair.h"

#include "fmt/format.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace IECoreCycles;

namespace
{

ccl::Hair *convertCommon( const IECoreScene::CurvesPrimitive *curve, ccl::Scene *scene )
{
	assert( curve->typeId() == IECoreScene::CurvesPrimitive::staticTypeId() );
	ccl::Hair *hair = SceneAlgo::createNodeWithLock<ccl::Hair>( scene );
	/// \todo Support per-object `curve_shape` configured via an attribute.
	hair->curve_shape = scene->params.hair_shape;

	size_t numCurves = curve->numCurves();
	size_t numKeys = 0;

	const vector<int> &verticesPerCurve = curve->verticesPerCurve()->readable();
	for( size_t i = 0; i < verticesPerCurve.size(); ++i )
	{
		numKeys += verticesPerCurve[i];
	}

	hair->reserve_curves( numCurves, numKeys );

	const V3fVectorData *p = curve->variableData<V3fVectorData>( "P", PrimitiveVariable::Vertex );
	const vector<Imath::V3f> &points = p->readable();

	if( const FloatVectorData *w = curve->variableData<FloatVectorData>( "width", PrimitiveVariable::Vertex ) )
	{
		const vector<float> &width = w->readable();

		size_t key = 0;
		for( size_t i = 0; i < numCurves; ++i )
		{
			size_t firstKey = key;
			for( int j = 0; j < verticesPerCurve[i]; ++j, ++key )
			{
				hair->add_curve_key( ccl::make_float3( points[key].x, points[key].y, points[key].z ), width[key] / 2.0f );
			}

			hair->add_curve( firstKey, 0 );
		}
	}
	else
	{
		float constantWidth = 1.0f;

		if( const FloatData *cw = curve->variableData<FloatData>( "width", PrimitiveVariable::Constant ) )
		{
			constantWidth = cw->readable();
		}

		size_t key = 0;
		for( size_t i = 0; i < numCurves; ++i )
		{
			size_t firstKey = key;
			for( int j = 0; j < verticesPerCurve[i]; ++j, ++key )
			{
				hair->add_curve_key( ccl::make_float3( points[key].x, points[key].y, points[key].z ), constantWidth / 2.0f );
			}

			hair->add_curve( firstKey, 0 );
		}
	}

	// Convert primitive variables.
	PrimitiveVariableMap variablesToConvert = curve->variables;
	variablesToConvert.erase( "P" );
	variablesToConvert.erase( "width" );

	for( const auto &[name, variable] : variablesToConvert )
	{
		switch( variable.interpolation )
		{
			case PrimitiveVariable::Constant :
				GeometryAlgo::convertPrimitiveVariable( name, variable, hair->attributes, ccl::ATTR_ELEMENT_OBJECT );
				break;
			case PrimitiveVariable::Uniform :
				GeometryAlgo::convertPrimitiveVariable( name, variable, hair->attributes, ccl::ATTR_ELEMENT_CURVE );
				break;
			case PrimitiveVariable::Vertex :
				GeometryAlgo::convertPrimitiveVariable( name, variable, hair->attributes, ccl::ATTR_ELEMENT_CURVE_KEY );
				break;
			default :
				// Varying and FaceVarying define values at the end of each cubic curve
				// segment. Not supported by Cycles.
				break;
		}
	}
	return hair;
}

ccl::Geometry *convert( const IECoreScene::CurvesPrimitive *curve, ccl::Scene *scene )
{
	ccl::Hair *hair = convertCommon( curve, scene );
	return hair;
}

ccl::Geometry *convert( const IECoreScenePreview::Renderer::Samples<const IECoreScene::CurvesPrimitive *> &curves, const IECoreScenePreview::Renderer::SampleTimes &times, size_t primarySampleIndex, ccl::Scene *scene )
{
	ccl::Hair *result = convertCommon( curves[primarySampleIndex], scene );
	GeometryAlgo::convertMotion( IECoreScenePreview::Renderer::staticSamplesCast<const IECoreScene::Primitive *>( curves ), primarySampleIndex, *result );
	return result;
}

GeometryAlgo::ConverterDescription<CurvesPrimitive> g_description( convert, convert );

} // namespace
