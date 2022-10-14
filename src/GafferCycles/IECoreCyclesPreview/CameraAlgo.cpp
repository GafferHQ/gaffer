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
#include "scene/camera.h"
#include "kernel/types.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;
using namespace IECoreCycles;

namespace
{

ccl::Camera *convertCommon( const IECoreScene::Camera *camera, const std::string &nodeName )
{
	assert( camera->typeId() == IECoreScene::Camera::staticTypeId() );
	ccl::Camera *ccam = new ccl::Camera();
	ccam->name = ccl::ustring(nodeName.c_str());

	// Projection type
	const string &projection = camera->getProjection();
	if( projection == "perspective" )
	{
		ccam->set_camera_type( ccl::CameraType::CAMERA_PERSPECTIVE );
		ccam->set_fov( M_PI_2 );
		if( camera->getFStop() > 0.0f )
		{
			ccam->set_aperturesize( 0.5f * camera->getFocalLength() * camera->getFocalLengthWorldScale() / camera->getFStop() );
			ccam->set_focaldistance( camera->getFocusDistance() );
		}
	}
	else if( projection == "orthographic" )
	{
		ccam->set_camera_type( ccl::CameraType::CAMERA_ORTHOGRAPHIC );
	}
	else
	{
		ccam->set_camera_type( ccl::CameraType::CAMERA_PERSPECTIVE );
		ccam->set_fov( M_PI_2 );
	}

	// Screen window/resolution TODO: full_ might be something to do with cropping?
	const Imath::Box2f &frustum = camera->frustum();
	const Imath::V2i &resolution = camera->renderResolution();
	const float pixelAspectRatio = camera->getPixelAspectRatio();
	ccam->set_full_width( resolution[0] );
	ccam->set_full_height( resolution[1] );
	ccam->set_viewplane_left( frustum.min.x );
	ccam->set_viewplane_right( frustum.max.x );
	// Invert the viewplane in Y so Gaffer's aperture offsets and overscan are applied in the correct direction
	ccam->set_viewplane_bottom( -frustum.max.y );
	ccam->set_viewplane_top( -frustum.min.y );
	ccam->set_aperture_ratio( pixelAspectRatio ); // This is more for the bokeh, maybe it should be a separate parameter?

	// Clipping planes
	const Imath::V2f &clippingPlanes = camera->getClippingPlanes();
	ccam->set_nearclip( clippingPlanes.x );
	ccam->set_farclip( clippingPlanes.y );

	// Crop window
	if ( camera->hasCropWindow() )
	{
		const Imath::Box2f &cropWindow = camera->getCropWindow();
		ccam->set_border_left( cropWindow.min.x );
		ccam->set_border_right( cropWindow.max.x );
		ccam->set_border_top( cropWindow.max.y );
		ccam->set_border_bottom( cropWindow.min.y );
	}

	// Shutter TODO: Need to see if this is correct or not, cycles also has a shutter curve...
	const Imath::V2f &shutter = camera->getShutter();
	ccam->set_shuttertime( abs(shutter.x) + abs(shutter.y) );
	if( (shutter.x == 0.0) && (shutter.y > shutter.x) )
	{
		ccam->set_motion_position( ccl::MOTION_POSITION_START );
	}
	else if( (shutter.x < shutter.y) && (shutter.y == 0.0) )
	{
		ccam->set_motion_position( ccl::MOTION_POSITION_END );
	}
	else
	{
		ccam->set_motion_position( ccl::MOTION_POSITION_CENTER );
	}

	for( CompoundDataMap::const_iterator it = camera->parameters().begin(), eIt = camera->parameters().end(); it != eIt; ++it )
	{
		if( it->first == "panoramaType" )
		{
			if( const StringData *data = static_cast<const StringData *>( it->second.get() ) )
			{
				std::string panoType = data->readable();

				if( panoType == "equirectangular" )
				{
					ccam->set_camera_type( ccl::CAMERA_PANORAMA );
					ccam->set_panorama_type( ccl::PANORAMA_EQUIRECTANGULAR );
				}
				else if( panoType == "mirrorball" )
				{
					ccam->set_camera_type( ccl::CAMERA_PANORAMA );
					ccam->set_panorama_type( ccl::PANORAMA_MIRRORBALL );
				}
				else if( panoType == "fisheyeEquidistant" )
				{
					ccam->set_camera_type( ccl::CAMERA_PANORAMA );
					ccam->set_panorama_type( ccl::PANORAMA_FISHEYE_EQUIDISTANT );
				}
				else if( panoType == "fisheyeEquisolid" )
				{
					ccam->set_camera_type( ccl::CAMERA_PANORAMA );
					ccam->set_panorama_type( ccl::PANORAMA_FISHEYE_EQUISOLID );
				}
			}
		}
		else
		{
			SocketAlgo::setSocket( ccam, it->first, it->second.get() );
		}
	}

	return ccam;
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// Implementation of public API
//////////////////////////////////////////////////////////////////////////

namespace IECoreCycles

{

namespace CameraAlgo

{

ccl::Camera *convert( const IECoreScene::Camera *camera, const std::string &nodeName, ccl::Scene *scene )
{
	return convertCommon( camera, nodeName );
}

} // namespace CameraAlgo

} // namespace IECoreCycles
