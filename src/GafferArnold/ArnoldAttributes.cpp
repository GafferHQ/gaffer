//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//      * Redistributions of source code must retain the above
//        copyright notice, this list of conditions and the following
//        disclaimer.
//
//      * Redistributions in binary form must reproduce the above
//        copyright notice, this list of conditions and the following
//        disclaimer in the documentation and/or other materials provided with
//        the distribution.
//
//      * Neither the name of John Haddon nor the names of
//        any other contributors to this software may be used to endorse or
//        promote products derived from this software without specific prior
//        written permission.
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

#include "GafferArnold/ArnoldAttributes.h"

#include "Gaffer/StringPlug.h"

using namespace Imath;
using namespace Gaffer;
using namespace GafferArnold;

GAFFER_NODE_DEFINE_TYPE( ArnoldAttributes );

ArnoldAttributes::ArnoldAttributes( const std::string &name )
	:	GafferScene::Attributes( name )
{
	Gaffer::CompoundDataPlug *attributes = attributesPlug();

	// Visibility parameters

	attributes->addChild( new Gaffer::NameValuePlug( "ai:visibility:camera", new IECore::BoolData( true ), false, "cameraVisibility" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "ai:visibility:shadow", new IECore::BoolData( true ), false, "shadowVisibility" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "ai:visibility:shadow_group", new IECore::StringData( "" ), false, "shadowGroup" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "ai:visibility:diffuse_reflect", new IECore::BoolData( true ), false, "diffuseReflectionVisibility" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "ai:visibility:specular_reflect", new IECore::BoolData( true ), false, "specularReflectionVisibility" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "ai:visibility:diffuse_transmit", new IECore::BoolData( true ), false, "diffuseTransmissionVisibility" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "ai:visibility:specular_transmit", new IECore::BoolData( true ), false, "specularTransmissionVisibility" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "ai:visibility:volume", new IECore::BoolData( true ), false, "volumeVisibility" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "ai:visibility:subsurface", new IECore::BoolData( true ), false, "subsurfaceVisibility" ) );

	// Displacement parameters

	attributes->addChild( new Gaffer::NameValuePlug( "ai:disp_autobump", new IECore::BoolData( false ), false, "autoBump" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "ai:autobump_visibility:camera", new IECore::BoolData( true ), false, "cameraAutoBumpVisibility" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "ai:autobump_visibility:diffuse_reflect", new IECore::BoolData( false ), false, "diffuseReflectionAutoBumpVisibility" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "ai:autobump_visibility:specular_reflect", new IECore::BoolData( false ), false, "specularReflectionAutoBumpVisibility" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "ai:autobump_visibility:diffuse_transmit", new IECore::BoolData( false ), false, "diffuseTransmissionAutoBumpVisibility" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "ai:autobump_visibility:specular_transmit", new IECore::BoolData( false ), false, "specularTransmissionAutoBumpVisibility" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "ai:autobump_visibility:volume", new IECore::BoolData( false ), false, "volumeAutoBumpVisibility" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "ai:autobump_visibility:subsurface", new IECore::BoolData( false ), false, "subsurfaceAutoBumpVisibility" ) );

	// Transform parameters

	attributes->addChild( new Gaffer::NameValuePlug( "ai:transform_type", new StringPlug( "value", Plug::In, "rotate_about_center" ), false, "transformType" ) );

	// Shading parameters

	attributes->addChild( new Gaffer::NameValuePlug( "ai:matte", new IECore::BoolData( false ), false, "matte" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "ai:opaque", new IECore::BoolData( true ), false, "opaque" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "ai:receive_shadows", new IECore::BoolData( true ), false, "receiveShadows" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "ai:self_shadows", new IECore::BoolData( true ), false, "selfShadows" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "ai:sss_setname", new StringPlug( "value", Plug::In, "" ), false, "sssSetName" ) );

	// Subdivision parameters

	attributes->addChild( new Gaffer::NameValuePlug( "ai:polymesh:subdiv_iterations", new IntPlug( "value", Plug::In, 1, 0 ), false, "subdivIterations" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "ai:polymesh:subdiv_adaptive_error", new FloatPlug( "value", Plug::In, 0.0f, 0.0f ), false, "subdivAdaptiveError" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "ai:polymesh:subdiv_adaptive_metric", new StringPlug( "value", Plug::In, "auto" ), false, "subdivAdaptiveMetric" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "ai:polymesh:subdiv_adaptive_space", new StringPlug( "value", Plug::In, "raster" ), false, "subdivAdaptiveSpace" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "ai:polymesh:subdiv_uv_smoothing", new StringPlug( "value", Plug::In, "pin_corners" ), false, "subdivUVSmoothing" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "ai:polymesh:subdiv_smooth_derivs", new BoolPlug( "value" ), false, "subdivSmoothDerivs" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "ai:polymesh:subdiv_frustum_ignore", new BoolPlug( "value" ), false, "subdivFrustumIgnore" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "ai:polymesh:subdivide_polygons", new BoolPlug( "value" ), false, "subdividePolygons" ) );

	// Curves parameters

	attributes->addChild( new Gaffer::NameValuePlug( "ai:curves:mode", new StringPlug( "value", Plug::In, "ribbon" ), false, "curvesMode" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "ai:curves:min_pixel_width", new FloatPlug( "value", Plug::In, 0.0f, 0.0f ), false, "curvesMinPixelWidth" ) );

	// Volume parameters

	attributes->addChild( new Gaffer::NameValuePlug( "ai:volume:step_size", new FloatPlug( "value", Plug::In, 0.0f, 0.0f ), false, "volumeStepSize" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "ai:volume:step_scale", new FloatPlug( "value", Plug::In, 1.0f, 0.0f ), false, "volumeStepScale" ) );

	attributes->addChild( new Gaffer::NameValuePlug( "ai:shape:step_size", new FloatPlug( "value", Plug::In, 0.0f, 0.0f ), false, "shapeStepSize" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "ai:shape:step_scale", new FloatPlug( "value", Plug::In, 1.0f, 0.0f ), false, "shapeStepScale" ) );

	attributes->addChild( new Gaffer::NameValuePlug( "ai:shape:volume_padding", new FloatPlug( "value", Plug::In, 0.0f, 0.0f ), false, "volumePadding" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "ai:volume:velocity_scale", new FloatPlug( "value", Plug::In, 1.0f, 0.0f ), false, "velocityScale" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "ai:volume:velocity_fps", new FloatPlug( "value", Plug::In, 24.0f, 0.0f ), false, "velocityFPS" ) );
	attributes->addChild( new Gaffer::NameValuePlug( "ai:volume:velocity_outlier_threshold", new FloatPlug( "value", Plug::In, 0.001f, 0.0f ), false, "velocityOutlierThreshold" ) );

	attributes->addChild( new Gaffer::NameValuePlug( "ai:toon_id", new StringPlug( "value", Plug::In ), false, "toonId" ) );

}

ArnoldAttributes::~ArnoldAttributes()
{
}
