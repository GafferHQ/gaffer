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

#include "GafferCycles/IECoreCyclesPreview/CameraAlgo.h"

#include "GafferCycles/IECoreCyclesPreview/SocketAlgo.h"

#include "IECoreScene/Camera.h"

#include "IECore/SimpleTypedData.h"

// Cycles
#include "render/camera.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace IECoreCycles;

namespace
{

ccl::Camera *convertCommon( const IECoreScene::Camera *camera, const std::string &nodeName )
{
	CameraPtr cameraCopy = camera->copy();
	cameraCopy->addStandardParameters();

	ccl::Camera *ccam = new ccl::Camera();
	ccam->name = nodeName.c_str();

	// Projection type
	const string &projection = cameraCopy->parametersData()->member<StringData>( "projection", true )->readable();
	if( projection == "perspective" )
		ccam->type = ccl::CAMERA_PERSPECTIVE;
	else if( projection == "orthographic" )
		ccam->type = ccl::CAMERA_ORTHOGRAPHIC;
	else if( projection == "panorama" )
		ccam->type = ccl::CAMERA_PANORAMA;
	else
		ccam->type = ccl::CAMERA_PERSPECTIVE;

	// FOV
	const float &fov = cameraCopy->parametersData()->member<FloatData>( "projection:fov", true )->readable();
	ccam->fov = fov;

	// Screen window/resolution TODO: full_ might be something to do with cropping?
	const Imath::Box2f &screenWindow = cameraCopy->parametersData()->member<Box2fData>( "screenWindow", true )->readable();
	const V2i &resolution = cameraCopy->parametersData()->member<V2iData>( "resolution", true )->readable();
	const float pixelAspectRatio = cameraCopy->parametersData()->member<FloatData>( "pixelAspectRatio", true )->readable();
	ccam->width = resolution[0];
	ccam->height = resolution[1];
	ccam->full_width = resolution[0];
	ccam->full_height = resolution[1];
	ccam->viewplane.left = screenWindow.min.x;
	ccam->viewplane.right = screenWindow.max.x;
	ccam->viewplane.top = screenWindow.min.y;
	ccam->viewplane.bottom = screenWindow.max.y;
	ccam->aperture_ratio = pixelAspectRatio; // This is more for the bokeh, maybe it should be a separate parameter?

	// Clipping planes
	const Imath::V2f &clippingPlanes = cameraCopy->parametersData()->member<V2fData>( "clippingPlanes", true )->readable();
	ccam->nearclip = clippingPlanes[0];
	ccam->farclip = clippingPlanes[1];

	// Shutter TODO: Need to see if this is correct or not, cycles also has a shutter curve...
	const V2d shutter = cameraCopy->parametersData()->member<V2fData>( "shutter", true )->readable();
	if ((shutter[0] > 0.0) && (shutter[1] > 0.0))
	{
		ccam->motion_position = ccl::Camera::MOTION_POSITION_START;
		ccam->shuttertime = shutter[0] + shutter[1];
	}
	else if ((shutter[0] < 0.0) && (shutter[1] > 0.0))
	{
		ccam->motion_position = ccl::Camera::MOTION_POSITION_CENTER;
		ccam->shuttertime = abs(shutter[0]) + shutter[1];
	}
	else if ((shutter[0] < 0.0) && (shutter[1] <= 0.0))
	{
		ccam->motion_position = ccl::Camera::MOTION_POSITION_END;
		ccam->shuttertime = abs(shutter[0]) + abs(shutter[1]);
	}
	else
	{
		ccam->motion_position = ccl::Camera::MOTION_POSITION_CENTER;
		ccam->shuttertime = 1.0;
	}

	return ccam;
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// Implementation of public API
//////////////////////////////////////////////////////////////////////////

ccl::Camera *CameraAlgo::convert( const IECoreScene::Camera *camera, const std::string &nodeName )
{
	return convertCommon( camera, nodeName );
}

ccl::Camera *CameraAlgo::convert( const std::vector<const IECoreScene::Camera *> &samples, const std::string &nodeName )
{
	// Not sure if Cortex can even do motion blurred cameras?
	return convertCommon( samples[0], nodeName );
}
