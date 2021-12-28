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

#include "GafferCycles/IECoreCyclesPreview/CurvesAlgo.h"

#include "GafferCycles/IECoreCyclesPreview/AttributeAlgo.h"
#include "GafferCycles/IECoreCyclesPreview/ObjectAlgo.h"

#include "IECoreScene/CurvesPrimitive.h"

#include "IECore/Interpolator.h"
#include "IECore/MessageHandler.h"
#include "IECore/SimpleTypedData.h"

// Cycles
#include "scene/geometry.h"
#include "scene/hair.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace IECoreCycles;

namespace
{

ccl::Hair *convertCommon( const IECoreScene::CurvesPrimitive *curve )
{
	assert( curve->typeId() == IECoreScene::CurvesPrimitive::staticTypeId() );
	ccl::Hair *hair = new ccl::Hair();

	size_t numCurves = curve->numCurves();
	size_t numKeys = 0;

	const IntVectorData *v = curve->verticesPerCurve();
	const vector<int> &verticesPerCurve = curve->verticesPerCurve()->readable();
	for( int i = 0; i < verticesPerCurve.size(); ++i )
		numKeys += verticesPerCurve[i];

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
			for( size_t j = 0; j < verticesPerCurve[i]; ++j, ++key )
				hair->add_curve_key( ccl::make_float3( points[key].x, points[key].y, points[key].z ), width[key] / 2.0f );

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
			for( size_t j = 0; j < verticesPerCurve[i]; ++j, ++key )
				hair->add_curve_key( ccl::make_float3( points[key].x, points[key].y, points[key].z ), constantWidth / 2.0f );

			hair->add_curve( firstKey, 0 );
		}
	}

	// Convert primitive variables.
	PrimitiveVariableMap variablesToConvert = curve->variables;
	variablesToConvert.erase( "P" );
	variablesToConvert.erase( "width" );

	for( PrimitiveVariableMap::iterator it = variablesToConvert.begin(), eIt = variablesToConvert.end(); it != eIt; ++it )
	{
		AttributeAlgo::convertPrimitiveVariable( it->first, it->second, hair->attributes );
	}
	return hair;
}

ObjectAlgo::ConverterDescription<CurvesPrimitive> g_description( CurvesAlgo::convert, CurvesAlgo::convert );

} // namespace

//////////////////////////////////////////////////////////////////////////
// Implementation of public API
//////////////////////////////////////////////////////////////////////////

namespace IECoreCycles

{

namespace CurvesAlgo

{

ccl::Object *convert( const IECoreScene::CurvesPrimitive *curve, const std::string &nodeName, ccl::Scene *scene )
{
	ccl::Object *cobject = new ccl::Object();
	cobject->set_geometry( convertCommon( curve ) );
	cobject->name = ccl::ustring(nodeName.c_str());
	return cobject;
}

ccl::Object *convert( const vector<const IECoreScene::CurvesPrimitive *> &curves, const std::vector<float> &times, const int frameIdx, const std::string &nodeName, ccl::Scene *scene )
{
	const int numSamples = curves.size();

	ccl::Hair *hair = nullptr;
	std::vector<const IECoreScene::CurvesPrimitive *> samples;
	IECoreScene::CurvesPrimitivePtr midMesh;

	if( frameIdx != -1 ) // Start/End frames
	{
		hair = convertCommon(curves[frameIdx]);

		if( numSamples == 2 ) // Make sure we have 3 samples
		{
			const V3fVectorData *p1 = curves[0]->variableData<V3fVectorData>( "P", PrimitiveVariable::Vertex );
			const V3fVectorData *p2 = curves[1]->variableData<V3fVectorData>( "P", PrimitiveVariable::Vertex );
			if( p1 && p2 )
			{
				midMesh = curves[frameIdx]->copy();
				V3fVectorData *midP = midMesh->variableData<V3fVectorData>( "P", PrimitiveVariable::Vertex );
				IECore::LinearInterpolator<std::vector<V3f>>()( p1->readable(), p2->readable(), 0.5f, midP->writable() );

				samples.push_back( midMesh.get() );
			}
		}

		for( int i = 0; i < numSamples; ++i )
		{
			if( i == frameIdx )
				continue;
			samples.push_back( curves[i] );
		}
	}
	else if( numSamples % 2 ) // Odd numSamples
	{
		int _frameIdx = ( numSamples+1 ) / 2;
		hair = convertCommon(curves[_frameIdx]);

		for( int i = 0; i < numSamples; ++i )
		{
			if( i == _frameIdx )
				continue;
			samples.push_back( curves[i] );
		}
	}
	else // Even numSamples
	{
		int _frameIdx = numSamples / 2 - 1;
		const V3fVectorData *p1 = curves[_frameIdx]->variableData<V3fVectorData>( "P", PrimitiveVariable::Vertex );
		const V3fVectorData *p2 = curves[_frameIdx+1]->variableData<V3fVectorData>( "P", PrimitiveVariable::Vertex );
		if( p1 && p2 )
		{
			midMesh = curves[_frameIdx]->copy();
			V3fVectorData *midP = midMesh->variableData<V3fVectorData>( "P", PrimitiveVariable::Vertex );
			IECore::LinearInterpolator<std::vector<V3f>>()( p1->readable(), p2->readable(), 0.5f, midP->writable() );
			hair = convertCommon( midMesh.get() );
		}

		for( int i = 0; i < numSamples; ++i )
		{
			samples.push_back( curves[i] );
		}
	}

	// Add the motion position/normal attributes
	hair->set_use_motion_blur( true );
	hair->set_motion_steps( samples.size() + 1 );
	ccl::Attribute *attr_mP = hair->attributes.add( ccl::ATTR_STD_MOTION_VERTEX_POSITION, ccl::ustring("motion_P") );
	ccl::float3 *mP = attr_mP->data_float3();

	for( size_t i = 0; i < samples.size(); ++i )
	{
		PrimitiveVariableMap::const_iterator pIt = samples[i]->variables.find( "P" );
		if( pIt != samples[i]->variables.end() )
		{
			const V3fVectorData *p = runTimeCast<const V3fVectorData>( pIt->second.data.get() );
			if( p )
			{
				PrimitiveVariable::Interpolation pInterpolation = pIt->second.interpolation;
				if( pInterpolation == PrimitiveVariable::Varying || pInterpolation == PrimitiveVariable::Vertex || pInterpolation == PrimitiveVariable::FaceVarying )
				{
					// Vertex positions
					const V3fVectorData *p = samples[i]->variableData<V3fVectorData>( "P", PrimitiveVariable::Vertex );
					const std::vector<V3f> &points = p->readable();
					size_t numVerts = p->readable().size();

					for( size_t j = 0; j < numVerts; ++j, ++mP )
						*mP = ccl::make_float3( points[j].x, points[j].y, points[j].z );
				}
				else
				{
					msg( Msg::Warning, "IECoreCycles::CurvesAlgo::convert", "Variable \"Position\" has unsupported interpolation type - not generating sampled Position." );
					hair->attributes.remove( attr_mP );
					hair->set_motion_steps( 0 );
					hair->set_use_motion_blur( false );
				}
			}
			else
			{
				msg( Msg::Warning, "IECoreCycles::CurvesAlgo::convert", boost::format( "Variable \"Position\" has unsupported type \"%s\" (expected V3fVectorData)." ) % pIt->second.data->typeName() );
				hair->attributes.remove( attr_mP );
				hair->set_motion_steps( 0 );
				hair->set_use_motion_blur( false );
			}
		}
	}
	mP = attr_mP->data_float3();

	ccl::Object *cobject = new ccl::Object();
	cobject->set_geometry( hair );
	cobject->name = ccl::ustring(nodeName.c_str());
	return cobject;
}

} // namespace CurvesAlgo

} // namespace IECoreCycles
