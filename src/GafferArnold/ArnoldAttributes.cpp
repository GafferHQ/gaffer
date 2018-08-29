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

IE_CORE_DEFINERUNTIMETYPED( ArnoldAttributes );

ArnoldAttributes::ArnoldAttributes( const std::string &name )
	:	GafferScene::Attributes( name )
{
	Gaffer::CompoundDataPlug *attributes = attributesPlug();

	// Visibility parameters

	attributes->addOptionalMember( "ai:visibility:camera", new IECore::BoolData( true ), "cameraVisibility", Gaffer::Plug::Default, false );
	attributes->addOptionalMember( "ai:visibility:shadow", new IECore::BoolData( true ), "shadowVisibility", Gaffer::Plug::Default, false );
	attributes->addOptionalMember( "ai:visibility:shadow_group", new IECore::StringData( "" ), "shadowGroup", Gaffer::Plug::Default, false );
	attributes->addOptionalMember( "ai:visibility:diffuse_reflect", new IECore::BoolData( true ), "diffuseReflectionVisibility", Gaffer::Plug::Default, false );
	attributes->addOptionalMember( "ai:visibility:specular_reflect", new IECore::BoolData( true ), "specularReflectionVisibility", Gaffer::Plug::Default, false );
	attributes->addOptionalMember( "ai:visibility:diffuse_transmit", new IECore::BoolData( true ), "diffuseTransmissionVisibility", Gaffer::Plug::Default, false );
	attributes->addOptionalMember( "ai:visibility:specular_transmit", new IECore::BoolData( true ), "specularTransmissionVisibility", Gaffer::Plug::Default, false );
	attributes->addOptionalMember( "ai:visibility:volume", new IECore::BoolData( true ), "volumeVisibility", Gaffer::Plug::Default, false );
	attributes->addOptionalMember( "ai:visibility:subsurface", new IECore::BoolData( true ), "subsurfaceVisibility", Gaffer::Plug::Default, false );

	// Transform parameters

	attributes->addOptionalMember( "ai:transform_type", new StringPlug( "value", Plug::In, "rotate_about_center" ), "transformType", false );

	// Shading parameters

	attributes->addOptionalMember( "ai:matte", new IECore::BoolData( false ), "matte", Gaffer::Plug::Default, false );
	attributes->addOptionalMember( "ai:opaque", new IECore::BoolData( true ), "opaque", Gaffer::Plug::Default, false );
	attributes->addOptionalMember( "ai:receive_shadows", new IECore::BoolData( true ), "receiveShadows", Gaffer::Plug::Default, false );
	attributes->addOptionalMember( "ai:self_shadows", new IECore::BoolData( true ), "selfShadows", Gaffer::Plug::Default, false );
	attributes->addOptionalMember( "ai:sss_setname", new StringPlug( "value", Plug::In, "" ), "sssSetName", false );

	// Subdivision parameters

	attributes->addOptionalMember( "ai:polymesh:subdiv_iterations", new IntPlug( "value", Plug::In, 1, 1 ), "subdivIterations", false );
	attributes->addOptionalMember( "ai:polymesh:subdiv_adaptive_error", new FloatPlug( "value", Plug::In, 0.0f, 0.0f ), "subdivAdaptiveError", false );
	attributes->addOptionalMember( "ai:polymesh:subdiv_adaptive_metric", new StringPlug( "value", Plug::In, "auto" ), "subdivAdaptiveMetric", false );
	attributes->addOptionalMember( "ai:polymesh:subdiv_adaptive_space", new StringPlug( "value", Plug::In, "raster" ), "subdivAdaptiveSpace", false );
	attributes->addOptionalMember( "ai:polymesh:subdiv_uv_smoothing", new StringPlug( "value", Plug::In, "pin_corners" ), "subdivUVSmoothing", false );
	attributes->addOptionalMember( "ai:polymesh:subdiv_smooth_derivs", new BoolPlug( "value" ), "subdivSmoothDerivs", false );
	attributes->addOptionalMember( "ai:polymesh:subdivide_polygons", new BoolPlug( "value" ), "subdividePolygons", false );

	// Curves parameters

	attributes->addOptionalMember( "ai:curves:mode", new StringPlug( "value", Plug::In, "ribbon" ), "curvesMode", false );
	attributes->addOptionalMember( "ai:curves:min_pixel_width", new FloatPlug( "value", Plug::In, 0.0f, 0.0f ), "curvesMinPixelWidth", false );

	// Volume parameters

	attributes->addOptionalMember( "ai:volume:step_size", new FloatPlug( "value", Plug::In, 0.0f, 0.0f ), "volumeStepSize", false );
	attributes->addOptionalMember( "ai:volume:step_scale", new FloatPlug( "value", Plug::In, 1.0f, 0.0f ), "volumeStepScale", false );

	attributes->addOptionalMember( "ai:shape:step_size", new FloatPlug( "value", Plug::In, 0.0f, 0.0f ), "shapeStepSize", false );
	attributes->addOptionalMember( "ai:shape:step_scale", new FloatPlug( "value", Plug::In, 1.0f, 0.0f ), "shapeStepScale", false );

	attributes->addOptionalMember( "ai:shape:volume_padding", new FloatPlug( "value", Plug::In, 0.0f, 0.0f ), "volumePadding", false );
	attributes->addOptionalMember( "ai:volume:velocity_scale", new FloatPlug( "value", Plug::In, 1.0f, 0.0f ), "velocityScale", false );
	attributes->addOptionalMember( "ai:volume:velocity_fps", new FloatPlug( "value", Plug::In, 24.0f, 0.0f ), "velocityFPS", false );
	attributes->addOptionalMember( "ai:volume:velocity_outlier_threshold", new FloatPlug( "value", Plug::In, 0.001f, 0.0f ), "velocityOutlierThreshold", false );

}

ArnoldAttributes::~ArnoldAttributes()
{
}
