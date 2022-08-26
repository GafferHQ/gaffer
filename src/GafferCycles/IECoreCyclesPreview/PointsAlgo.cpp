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

#include "GafferCycles/IECoreCyclesPreview/PointsAlgo.h"

#include "GafferCycles/IECoreCyclesPreview/AttributeAlgo.h"
#include "GafferCycles/IECoreCyclesPreview/ObjectAlgo.h"
#include "GafferCycles/IECoreCyclesPreview/SocketAlgo.h"

#include "IECoreScene/PointsPrimitive.h"

#include "IECore/Interpolator.h"
#include "IECore/MessageHandler.h"
#include "IECore/SimpleTypedData.h"

// Cycles
#include "scene/geometry.h"
#include "scene/pointcloud.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace IECoreCycles;

namespace
{

ccl::PointCloud *convertCommon( const IECoreScene::PointsPrimitive *points )
{
	assert( points->typeId() == IECoreScene::PointsPrimitive::staticTypeId() );
	ccl::PointCloud *pointcloud = new ccl::PointCloud();

	PrimitiveVariableMap variablesToConvert = points->variables;
/*
	pointcloud->set_point_style( ccl::POINT_CLOUD_POINT_SPHERE );
	if( const StringData *typeData = points->variableData<StringData>( "type", PrimitiveVariable::Constant ) )
	{
		std::string type = typeData->readable();
		if( type == "disk" || type == "particle" || type == "patch" )
		{
			if( variablesToConvert.find("N") != variablesToConvert.end() &&
				points->variableData<V3fVectorData>( "N", PrimitiveVariable::Vertex ) )
			{
				pointcloud->set_point_style( ccl::POINT_CLOUD_POINT_DISC_ORIENTED );
			}
			else
			{
				pointcloud->set_point_style( ccl::POINT_CLOUD_POINT_DISC );
			}
		}
	}
*/
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

	for( PrimitiveVariableMap::iterator it = variablesToConvert.begin(), eIt = variablesToConvert.end(); it != eIt; ++it )
	{
		AttributeAlgo::convertPrimitiveVariable( it->first, it->second, pointcloud->attributes );
	}
	return pointcloud;
}

ObjectAlgo::ConverterDescription<PointsPrimitive> g_description( PointsAlgo::convert, PointsAlgo::convert );

} // namespace

//////////////////////////////////////////////////////////////////////////
// Implementation of public API
//////////////////////////////////////////////////////////////////////////

namespace IECoreCycles

{

namespace PointsAlgo

{

ccl::Object *convert( const IECoreScene::PointsPrimitive *points, const std::string &nodeName, ccl::Scene *scene )
{
	ccl::Object *cobject = new ccl::Object();
	cobject->set_geometry( (ccl::Geometry*)convertCommon(points) );
	cobject->name = ccl::ustring(nodeName.c_str());
	return cobject;
}

ccl::Object *convert( const vector<const IECoreScene::PointsPrimitive *> &points, const std::vector<float> &times, const int frameIdx, const std::string &nodeName, ccl::Scene *scene )
{
	const int numSamples = points.size();

	ccl::PointCloud *pointcloud = nullptr;
	std::vector<const IECoreScene::PointsPrimitive *> samples;
	IECoreScene::PointsPrimitivePtr midMesh;

	if( frameIdx != -1 ) // Start/End frames
	{
		pointcloud = convertCommon(points[frameIdx]);

		if( numSamples == 2 ) // Make sure we have 3 samples
		{
			const V3fVectorData *p1 = points[0]->variableData<V3fVectorData>( "P", PrimitiveVariable::Vertex );
			const V3fVectorData *p2 = points[1]->variableData<V3fVectorData>( "P", PrimitiveVariable::Vertex );
			if( p1 && p2 )
			{
				midMesh = points[frameIdx]->copy();
				V3fVectorData *midP = midMesh->variableData<V3fVectorData>( "P", PrimitiveVariable::Vertex );
				IECore::LinearInterpolator<std::vector<V3f>>()( p1->readable(), p2->readable(), 0.5f, midP->writable() );

				samples.push_back( midMesh.get() );
			}
		}

		for( int i = 0; i < numSamples; ++i )
		{
			if( i == frameIdx )
				continue;
			samples.push_back( points[i] );
		}
	}
	else if( numSamples % 2 ) // Odd numSamples
	{
		int _frameIdx = ( numSamples+1 ) / 2;
		pointcloud = convertCommon( points[_frameIdx] );

		for( int i = 0; i < numSamples; ++i )
		{
			if( i == _frameIdx )
				continue;
			samples.push_back( points[i] );
		}
	}
	else // Even numSamples
	{
		int _frameIdx = numSamples / 2 - 1;
		const V3fVectorData *p1 = points[_frameIdx]->variableData<V3fVectorData>( "P", PrimitiveVariable::Vertex );
		const V3fVectorData *p2 = points[_frameIdx+1]->variableData<V3fVectorData>( "P", PrimitiveVariable::Vertex );
		if( p1 && p2 )
		{
			midMesh = points[_frameIdx]->copy();
			V3fVectorData *midP = midMesh->variableData<V3fVectorData>( "P", PrimitiveVariable::Vertex );
			IECore::LinearInterpolator<std::vector<V3f>>()( p1->readable(), p2->readable(), 0.5f, midP->writable() );
			pointcloud = convertCommon( midMesh.get() );
		}

		for( int i = 0; i < numSamples; ++i )
		{
			samples.push_back( points[i] );
		}
	}

	// Add the motion position/normal attributes
	pointcloud->set_use_motion_blur( true );
	pointcloud->set_motion_steps( samples.size() + 1 );
	ccl::Attribute *attr_mP = pointcloud->attributes.add( ccl::ATTR_STD_MOTION_VERTEX_POSITION, ccl::ustring("motion_P") );
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
					msg( Msg::Warning, "IECoreCycles::PointsAlgo::convert", "Variable \"Position\" has unsupported interpolation type - not generating sampled Position." );
					pointcloud->attributes.remove( attr_mP );
					pointcloud->set_motion_steps( 0 );
					pointcloud->set_use_motion_blur( false );
				}
			}
			else
			{
				msg( Msg::Warning, "IECoreCycles::PointsAlgo::convert", boost::format( "Variable \"Position\" has unsupported type \"%s\" (expected V3fVectorData)." ) % pIt->second.data->typeName() );
				pointcloud->attributes.remove( attr_mP );
				pointcloud->set_motion_steps( 0 );
				pointcloud->set_use_motion_blur( false );
			}
		}
	}
	mP = attr_mP->data_float3();

	ccl::Object *cobject = new ccl::Object();
	cobject->set_geometry( pointcloud );
	cobject->name = ccl::ustring(nodeName.c_str());
	return cobject;
}

} // namespace PointsAlgo

} // namespace IECoreCycles
