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

#include "IECore/SimpleTypedData.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace IECoreScene;

void IECoreCycles::CameraAlgo::convert( const IECoreScene::Camera *source, ccl::Camera *destination )
{
	// Projection type
	const string &projection = source->getProjection();
	if( projection == "perspective" )
	{
		destination->set_camera_type( ccl::CameraType::CAMERA_PERSPECTIVE );
		destination->set_fov( M_PI_2 );
		if( source->getFStop() > 0.0f )
		{
			destination->set_aperturesize( 0.5f * source->getFocalLength() * source->getFocalLengthWorldScale() / source->getFStop() );
			destination->set_focaldistance( source->getFocusDistance() );
		}
	}
	else if( projection == "orthographic" )
	{
		destination->set_camera_type( ccl::CameraType::CAMERA_ORTHOGRAPHIC );
	}
	else
	{
		destination->set_camera_type( ccl::CameraType::CAMERA_PERSPECTIVE );
		destination->set_fov( M_PI_2 );
	}

	// Screen window/resolution TODO: full_ might be something to do with cropping?
	const Imath::Box2f &frustum = source->frustum();
	const Imath::V2i &resolution = source->renderResolution();
	const float pixelAspectRatio = source->getPixelAspectRatio();
	destination->set_full_width( resolution[0] );
	destination->set_full_height( resolution[1] );
	destination->set_viewplane_left( frustum.min.x );
	destination->set_viewplane_right( frustum.max.x );
	// Invert the viewplane in Y so Gaffer's aperture offsets and overscan are applied in the correct direction
	destination->set_viewplane_bottom( -frustum.max.y );
	destination->set_viewplane_top( -frustum.min.y );
	destination->set_aperture_ratio( pixelAspectRatio ); // This is more for the bokeh, maybe it should be a separate parameter?

	// Clipping planes
	const Imath::V2f &clippingPlanes = source->getClippingPlanes();
	destination->set_nearclip( clippingPlanes.x );
	destination->set_farclip( clippingPlanes.y );

	// Crop window
	if( source->hasCropWindow() )
	{
		const Imath::Box2f &cropWindow = source->getCropWindow();
		destination->set_border_left( cropWindow.min.x );
		destination->set_border_right( cropWindow.max.x );
		destination->set_border_top( cropWindow.max.y );
		destination->set_border_bottom( cropWindow.min.y );
	}

	// Shutter TODO: Need to see if this is correct or not, cycles also has a shutter curve...
	const Imath::V2f &shutter = source->getShutter();
	destination->set_shuttertime( abs(shutter.x) + abs(shutter.y) );
	if( (shutter.x == 0.0) && (shutter.y > shutter.x) )
	{
		destination->set_motion_position( ccl::MOTION_POSITION_START );
	}
	else if( (shutter.x < shutter.y) && (shutter.y == 0.0) )
	{
		destination->set_motion_position( ccl::MOTION_POSITION_END );
	}
	else
	{
		destination->set_motion_position( ccl::MOTION_POSITION_CENTER );
	}

	for( CompoundDataMap::const_iterator it = source->parameters().begin(), eIt = source->parameters().end(); it != eIt; ++it )
	{
		if( it->first == "panoramaType" )
		{
			if( const StringData *data = static_cast<const StringData *>( it->second.get() ) )
			{
				/// \todo We have set camera type already in the projection section, so
				/// setting it here will result in `destination->is_modified()` even when
				/// nothing actually changed. Fix it. Perhaps these should all be special
				/// `ccl:*` values for "projection" anyway, rather than a parameter?
				std::string panoType = data->readable();

				if( panoType == "equirectangular" )
				{
					destination->set_camera_type( ccl::CAMERA_PANORAMA );
					destination->set_panorama_type( ccl::PANORAMA_EQUIRECTANGULAR );
				}
				else if( panoType == "mirrorball" )
				{
					destination->set_camera_type( ccl::CAMERA_PANORAMA );
					destination->set_panorama_type( ccl::PANORAMA_MIRRORBALL );
				}
				else if( panoType == "fisheyeEquidistant" )
				{
					destination->set_camera_type( ccl::CAMERA_PANORAMA );
					destination->set_panorama_type( ccl::PANORAMA_FISHEYE_EQUIDISTANT );
				}
				else if( panoType == "fisheyeEquisolid" )
				{
					destination->set_camera_type( ccl::CAMERA_PANORAMA );
					destination->set_panorama_type( ccl::PANORAMA_FISHEYE_EQUISOLID );
				}
			}
		}
		else if( auto socket = destination->type->find_input( ccl::ustring( it->first.c_str() ) ) )
		{
			SocketAlgo::setSocket( destination, socket, it->second.get() );
		}
	}
}
