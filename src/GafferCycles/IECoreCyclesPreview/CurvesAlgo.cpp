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

#include "IECore/MessageHandler.h"
#include "IECore/SimpleTypedData.h"

// Cycles
#include "render/mesh.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace IECoreCycles;

namespace
{

ccl::Mesh *convertCommon( const IECoreScene::CurvesPrimitive *curve )
{
	assert( curve->typeId() == IECoreScene::CurvesPrimitive::staticTypeId() );
	ccl::Mesh *cmesh = new ccl::Mesh();

	size_t numCurves = curve->numCurves();
	size_t numKeys = 0;

	const IntVectorData *v = curve->verticesPerCurve();
	const vector<int> &verticesPerCurve = curve->verticesPerCurve()->readable();
	for( int i = 0; i < verticesPerCurve.size(); ++i )
		numKeys += verticesPerCurve[i];

	cmesh->reserve_curves( numCurves, numKeys );

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
				cmesh->add_curve_key( ccl::make_float3( points[key].x, points[key].y, points[key].z ), width[key] / 2.0f );

			cmesh->add_curve( firstKey, 0 );
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
				cmesh->add_curve_key( ccl::make_float3( points[key].x, points[key].y, points[key].z ), constantWidth / 2.0f );

			cmesh->add_curve( firstKey, 0 );
		}
	}

	// Convert primitive variables.
	PrimitiveVariableMap variablesToConvert = curve->variables;
	variablesToConvert.erase( "P" );
	variablesToConvert.erase( "width" );

	for( PrimitiveVariableMap::iterator it = variablesToConvert.begin(), eIt = variablesToConvert.end(); it != eIt; ++it )
	{
		AttributeAlgo::convertPrimitiveVariable( it->first, it->second, cmesh->curve_attributes );
	}
	return cmesh;
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

ccl::Object *convert( const IECoreScene::CurvesPrimitive *curve, const std::string &nodeName, const ccl::Scene *scene )
{
	ccl::Object *cobject = new ccl::Object();
	cobject->mesh = convertCommon(curve);
	cobject->name = ccl::ustring(nodeName.c_str());
	return cobject;
}

ccl::Object *convert( const vector<const IECoreScene::CurvesPrimitive *> &curves, const std::string &nodeName, const ccl::Scene *scene )
{
	ccl::Mesh *cmesh = convertCommon(curves[0]);

	// Add the motion position/normal attributes
	cmesh->motion_steps = curves.size();
	ccl::Attribute *attr_mP = cmesh->attributes.add( ccl::ATTR_STD_MOTION_VERTEX_POSITION, ccl::ustring("motion_P") );
	ccl::float3 *mP = attr_mP->data_float3();

	// First sample has already been obtained
	for( size_t i = 1; i < curves.size(); ++i )
	{
		PrimitiveVariableMap::const_iterator pIt = curves[i]->variables.find( "P" );
		if( pIt != curves[i]->variables.end() )
		{
			const V3fVectorData *p = runTimeCast<const V3fVectorData>( pIt->second.data.get() );
			if( p )
			{
				PrimitiveVariable::Interpolation pInterpolation = pIt->second.interpolation;
				if( pInterpolation == PrimitiveVariable::Varying || pInterpolation == PrimitiveVariable::Vertex || pInterpolation == PrimitiveVariable::FaceVarying )
				{
					// Vertex positions
					const V3fVectorData *p = curves[i]->variableData<V3fVectorData>( "P", PrimitiveVariable::Vertex );
					const std::vector<V3f> &points = p->readable();
					size_t numVerts = p->readable().size();

					for( size_t j = 0; j < numVerts; ++j, ++mP )
						*mP = ccl::make_float3( points[j].x, points[j].y, points[j].z );
				}
				else
				{
					msg( Msg::Warning, "IECoreCycles::CurvesAlgo::convert", "Variable \"Position\" has unsupported interpolation type - not generating sampled Position." );
					cmesh->attributes.remove(attr_mP);
				}
			}
			else
			{
				msg( Msg::Warning, "IECoreCycles::CurvesAlgo::convert", boost::format( "Variable \"Position\" has unsupported type \"%s\" (expected V3fVectorData)." ) % pIt->second.data->typeName() );
				cmesh->attributes.remove(attr_mP);
			}
		}
	}
	mP = attr_mP->data_float3();

	ccl::Object *cobject = new ccl::Object();
	cobject->mesh = cmesh;
	cobject->name = ccl::ustring(nodeName.c_str());
	return cobject;
}

} // namespace CurvesAlgo

} // namespace IECoreCycles
