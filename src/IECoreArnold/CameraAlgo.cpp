//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2016, Image Engine Design Inc. All rights reserved.
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#include "IECoreArnold/CameraAlgo.h"

#include "IECoreArnold/NodeAlgo.h"
#include "IECoreArnold/ParameterAlgo.h"

#include "IECoreScene/Camera.h"

#include "IECore/MessageHandler.h"
#include "IECore/SimpleTypedData.h"
#include "IECore/SplineData.h"

#include "OpenEXR/OpenEXRConfig.h"
#if OPENEXR_VERSION_MAJOR < 3
#include "OpenEXR/ImathFun.h"
#else
#include "Imath/ImathFun.h"
#endif

#include "ai_array.h"
#include "ai_msg.h" // Required for __AI_FILE__ macro used by `ai_array.h`

using namespace IECore;
using namespace IECoreScene;
using namespace IECoreArnold;

namespace
{

NodeAlgo::ConverterDescription<Camera> g_description( CameraAlgo::convert, CameraAlgo::convert );

const AtString g_perspCameraArnoldString("persp_camera");
const AtString g_orthoCameraArnoldString("ortho_camera");
const AtString g_fovArnoldString("fov");
const AtString g_nearClipArnoldString("near_clip");
const AtString g_farClipArnoldString("far_clip");
const AtString g_shutterCurveArnoldString("shutter_curve");
const AtString g_shutterStartArnoldString("shutter_start");
const AtString g_shutterEndArnoldString("shutter_end");
const AtString g_screenWindowMinArnoldString("screen_window_min");
const AtString g_screenWindowMaxArnoldString("screen_window_max");
const AtString g_apertureSizeArnoldString("aperture_size");
const AtString g_focusDistanceArnoldString("focus_distance");
const AtString g_motionStartArnoldString("motion_start");
const AtString g_motionEndArnoldString("motion_end");

AtVector2 curvePoint( const Splineff::Point &point )
{
	// Clamping enforces constraints specified in Arnold docs.
	// Not likely to be an issue in the X-axis, but in Y it's
	// easy to go over 1 accidentally if using a cubic basis.
	return AtVector2(
		Imath::clamp( point.first, 0.0f, 1.0f ),
		Imath::clamp( point.second, 0.0f, 1.0f )
	);
}

void setShutterCurveParameter( AtNode *camera, const IECore::Data *value )
{
	auto *splineData = runTimeCast<const SplineffData>( value );
	if( !splineData )
	{
		msg( Msg::Warning, "setShutterCurveParameter", boost::format( "Unsupported value type \"%s\" (expected SplineffData)." ) % value->typeName() );
		return;
	}


	AtArray *array;
	const Splineff &spline = splineData->readable();
	if( spline.basis == CubicBasisf::linear() )
	{
		array = AiArrayAllocate( spline.points.size(), 1, AI_TYPE_VECTOR2 );
		size_t index = 0;
		for( const auto &p : spline.points )
		{
			AiArraySetVec2( array, index++, curvePoint( p ) );
		}
	}
	else
	{
		// Cubic curve, but Arnold only supports linear. Just apply a fixed
		// sampling for now. From SolidAngle support : "Looking at the code, a
		// larger number of points in the shutter curve should have negligible
		// overhead."
		const int numSamples = 25;
		array = AiArrayAllocate( numSamples, 1, AI_TYPE_VECTOR2 );
		for( int i = 0; i < numSamples; ++i )
		{
			const float x = (float)i / (float)( numSamples - 1 );
			const float y = spline( x );
			AiArraySetVec2( array, i, curvePoint( { x, y } ) );
		}
	}

	AiNodeSetArray( camera, g_shutterCurveArnoldString, array );
}

// Performs the part of the conversion that is shared by both animated and non-animated cameras.
AtNode *convertCommon( const IECoreScene::Camera *camera, AtUniverse *universe, const std::string &nodeName, const AtNode *parentNode )
{
	// Use projection to decide what sort of camera node to create
	const std::string projection = camera->getProjection();

	AtNode *result = nullptr;
	if( projection=="perspective" )
	{
		result = AiNode( universe, g_perspCameraArnoldString, AtString( nodeName.c_str() ), parentNode );
	}
	else if( projection=="orthographic" )
	{
		result = AiNode( universe, g_orthoCameraArnoldString, AtString( nodeName.c_str() ), parentNode );
	}
	else
	{
		result = AiNode( universe, AtString( projection.c_str() ), AtString( nodeName.c_str() ), parentNode );
	}

	// Set clipping planes
	const Imath::V2f &clippingPlanes = camera->getClippingPlanes();
	AiNodeSetFlt( result, g_nearClipArnoldString, clippingPlanes[0] );
	AiNodeSetFlt( result, g_farClipArnoldString, clippingPlanes[1] );

	// Set shutter
	const Imath::V2f &shutter = camera->getShutter();
	AiNodeSetFlt( result, g_shutterStartArnoldString, shutter[0] );
	AiNodeSetFlt( result, g_shutterEndArnoldString, shutter[1] );

	// Set any Arnold-specific parameters
	const AtNodeEntry *nodeEntry = AiNodeGetNodeEntry( result );
	for( CompoundDataMap::const_iterator it = camera->parameters().begin(), eIt = camera->parameters().end(); it != eIt; ++it )
	{
		AtString paramNameArnold( it->first.c_str() );
		if( it->first == "mesh" )
		{
			// We have special handling in the renderer backend to translate a mesh path string
			// into a node pointer, so don't touch this here
			continue;
		}
		if( AiNodeEntryLookUpParameter( nodeEntry, paramNameArnold ) )
		{
			if( paramNameArnold == g_shutterCurveArnoldString )
			{
				setShutterCurveParameter( result, it->second.get() );
			}
			else
			{
				ParameterAlgo::setParameter( result, paramNameArnold, it->second.get() );
			}
		}
	}

	return result;
}

Imath::Box2f screenWindow( const IECoreScene::Camera *camera )
{
	Imath::Box2f result = camera->frustum();

	if( camera->getProjection() == "perspective" || camera->getProjection() == "lentil_camera" )
	{
		// Normalise so that Arnold's NDC space goes from 0-1 across the aperture.
		// This is helpful when using Arnold `uv_remap` shaders.
		const float width = ( result.max.x - result.min.x ) * 0.5f;
		result.min *= 1.0f / width;
		result.max *= 1.0f / width;
	}

	// Arnold automatically adjusts the vertical dimension to compensate for
	// the resolution and pixel aspect. This is handy when hand-editing .ass
	// files, but since we already take care of this ourselves, we have to
	// reverse their correction by multiplying the y values by aspect.
	const Imath::V2i resolution = camera->getResolution();
	const float aspect = camera->getPixelAspectRatio() * (float)resolution.x / (float)resolution.y;
	result.min.y *= aspect;
	result.max.y *= aspect;

	return result;
}

float fieldOfView( const IECoreScene::Camera *camera )
{
	// Calculate a FOV matching the focal length and aperture, accounting
	// for the normalisation performed in `screenWindow()`.
	const Imath::Box2f frustum = camera->frustum();
	const float width = ( frustum.max.x - frustum.min.x ) * 0.5f;
	return 2.0f * atan( width ) * 180.0f / M_PI;
}

float apertureSize( const IECoreScene::Camera *camera )
{
	if( camera->getFStop() <= 0.0f )
	{
		return 0.0f;
	}
	// Note the factor of 0.5 because Arnold stores aperture as radius, not diameter.
	return 0.5f * camera->getFocalLength() * camera->getFocalLengthWorldScale() / camera->getFStop();
}

template<typename F>
auto parameterSamples( const std::vector<const IECoreScene::Camera *> &cameraSamples, F &&parameterFunction )
{
	using SampleType = std::invoke_result_t<F, const IECoreScene::Camera *>;
	std::vector<SampleType> result;
	result.reserve( cameraSamples.size() );
	for( const auto &camera : cameraSamples )
	{
		result.push_back( parameterFunction( camera ) );
	}
	if( std::all_of( result.begin(), result.end(), [&]( const SampleType &x ) { return x == result.front(); } ) )
	{
		// If all samples are identical, then deduplicate them down to a single sample.
		result.resize( 1 );
	}
	return result;
}

void setAnimatedFloat( AtNode *node, AtString name, const std::vector<const IECoreScene::Camera *> &cameraSamples, float (*parameterFunction)( const IECoreScene::Camera * ) )
{
	const auto samples = parameterSamples( cameraSamples, parameterFunction );
	if( samples.size() > 1 )
	{
		AiNodeSetArray( node, name, AiArrayConvert( 1, samples.size(), AI_TYPE_FLOAT, samples.data() ) );
	}
	else
	{
		AiNodeSetFlt( node, name, samples[0] );
	}
}

} // namespace

AtNode *CameraAlgo::convert( const IECoreScene::Camera *camera, AtUniverse *universe, const std::string &nodeName, const AtNode *parentNode )
{
	AtNode *result = convertCommon( camera, universe, nodeName, parentNode );
	if( camera->getProjection()=="perspective" )
	{
		AiNodeSetFlt( result, g_fovArnoldString, fieldOfView( camera ) );
		AiNodeSetFlt( result, g_apertureSizeArnoldString, apertureSize( camera ) );
		AiNodeSetFlt( result, g_focusDistanceArnoldString, camera->getFocusDistance() );
	}

	const Imath::Box2f sw = screenWindow( camera );
	AiNodeSetVec2( result, g_screenWindowMinArnoldString, sw.min.x, sw.min.y );
	AiNodeSetVec2( result, g_screenWindowMaxArnoldString, sw.max.x, sw.max.y );

	return result;
}

AtNode *CameraAlgo::convert( const std::vector<const IECoreScene::Camera *> &samples, float motionStart, float motionEnd, AtUniverse *universe, const std::string &nodeName, const AtNode *parentNode )
{
	AtNode *result = convertCommon( samples[0], universe, nodeName, parentNode );
	if( samples[0]->getProjection()=="perspective" )
	{
		setAnimatedFloat( result, g_fovArnoldString, samples, fieldOfView );
		setAnimatedFloat( result, g_apertureSizeArnoldString, samples, apertureSize );
		setAnimatedFloat( result, g_focusDistanceArnoldString, samples, []( auto camera ) { return camera->getFocusDistance(); } );
	}

	const auto sw = parameterSamples( samples, screenWindow );
	if( sw.size() > 1 )
	{
		AtArray *minArray = AiArrayAllocate( 1, sw.size(), AI_TYPE_VECTOR2 );
		AtArray *maxArray = AiArrayAllocate( 1, sw.size(), AI_TYPE_VECTOR2 );
		for( size_t i = 0, e = sw.size(); i < e; ++i )
		{
			AiArraySetVec2( minArray, i, AtVector2( sw[i].min.x, sw[i].min.y ) );
			AiArraySetVec2( maxArray, i, AtVector2( sw[i].max.x, sw[i].max.y ) );
		}
		AiNodeSetArray( result, g_screenWindowMinArnoldString, minArray );
		AiNodeSetArray( result, g_screenWindowMaxArnoldString, maxArray );
	}
	else
	{
		AiNodeSetVec2( result, g_screenWindowMinArnoldString, sw[0].min.x, sw[0].min.y );
		AiNodeSetVec2( result, g_screenWindowMaxArnoldString, sw[0].max.x, sw[0].max.y );
	}

	AiNodeSetFlt( result, g_motionStartArnoldString, motionStart );
	AiNodeSetFlt( result, g_motionEndArnoldString, motionEnd );

	return result;
}
