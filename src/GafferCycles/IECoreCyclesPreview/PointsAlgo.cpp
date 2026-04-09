//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2021, Alex Fuller. All rights reserved.
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
//     * Neither the name of Alex Fuller nor the names of any
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
#include "GafferCycles/IECoreCyclesPreview/SocketAlgo.h"

#include "SceneAlgo.h"

#include "IECoreScene/PointsPrimitive.h"

#include "IECore/Interpolator.h"
#include "IECore/MessageHandler.h"
#include "IECore/SimpleTypedData.h"

// Cycles
#include "scene/geometry.h"
#include "scene/pointcloud.h"

#include "fmt/format.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace IECoreCycles;

namespace
{

ccl::PointCloud *convertPrimary( const IECoreScene::PointsPrimitive *points, ccl::Scene *scene )
{
	assert( points->typeId() == IECoreScene::PointsPrimitive::staticTypeId() );
	ccl::PointCloud *pointcloud = SceneAlgo::createNodeWithLock<ccl::PointCloud>( scene );

	PrimitiveVariableMap variablesToConvert = points->variables;

	size_t numPoints = points->getNumPoints();
	pointcloud->reserve( numPoints );

	const V3fVectorData *p = points->variableData<V3fVectorData>( "P", PrimitiveVariable::Vertex );
	const vector<Imath::V3f> &pos = p->readable();

	if( const FloatVectorData *w = points->variableData<FloatVectorData>( "width", PrimitiveVariable::Vertex ) )
	{
		const vector<float> &width = w->readable();

		for( size_t i = 0; i < numPoints; ++i )
		{
			pointcloud->add_point( SocketAlgo::setVector( pos[i] ), width[i] * 0.5f, 0);
		}
		variablesToConvert.erase( "width" );
	}
	else if( const FloatVectorData *w = points->variableData<FloatVectorData>( "radius", PrimitiveVariable::Vertex ) )
	{
		const vector<float> &width = w->readable();

		for( size_t i = 0; i < numPoints; ++i )
		{
			pointcloud->add_point( SocketAlgo::setVector( pos[i] ), width[i], 0);
		}
		variablesToConvert.erase( "radius" );
	}
	else
	{
		float width = 1.0f;

		if( const FloatData *w = points->variableData<FloatData>( "width", PrimitiveVariable::Constant ) )
		{
			width = w->readable() * 0.5f;
			variablesToConvert.erase( "width" );
		}

		if( const FloatData *w = points->variableData<FloatData>( "radius", PrimitiveVariable::Constant ) )
		{
			width = w->readable();
			variablesToConvert.erase( "radius" );
		}

		for( size_t i = 0; i < numPoints; ++i )
		{
			pointcloud->add_point( SocketAlgo::setVector( pos[i] ), width, 0);
		}
	}

	// Convert primitive variables. P is done, and width/radius if found (removed above).
	variablesToConvert.erase( "P" );

	for( const auto &[name, variable] : variablesToConvert )
	{
		switch( variable.interpolation )
		{
			case PrimitiveVariable::Constant :
			case PrimitiveVariable::Uniform :
				GeometryAlgo::convertPrimitiveVariable( name, variable, pointcloud->attributes, ccl::ATTR_ELEMENT_OBJECT );
				break;
			case PrimitiveVariable::Vertex :
			case PrimitiveVariable::Varying :
			case PrimitiveVariable::FaceVarying :
				GeometryAlgo::convertPrimitiveVariable( name, variable, pointcloud->attributes, ccl::ATTR_ELEMENT_VERTEX );
				break;
			default :
				break;
		}
	}

	return pointcloud;
}

ccl::Geometry *convert( const IECoreScenePreview::Renderer::Samples<const IECoreScene::PointsPrimitive *> &samples, const IECoreScenePreview::Renderer::SampleTimes &times, size_t primarySampleIndex, ccl::Scene *scene )
{
	ccl::PointCloud *result = convertPrimary( samples[primarySampleIndex], scene );
	GeometryAlgo::convertMotion( IECoreScenePreview::Renderer::staticSamplesCast<const IECoreScene::Primitive *>( samples ), primarySampleIndex, *result );
	return result;
}

GeometryAlgo::ConverterDescription<PointsPrimitive> g_description( convert );

} // namespace
