##########################################################################
#
#  Copyright (c) 2025, Cinesite VFX Ltd. All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#
#      * Redistributions of source code must retain the above
#        copyright notice, this list of conditions and the following
#        disclaimer.
#
#      * Redistributions in binary form must reproduce the above
#        copyright notice, this list of conditions and the following
#        disclaimer in the documentation and/or other materials provided with
#        the distribution.
#
#      * Neither the name of John Haddon nor the names of
#        any other contributors to this software may be used to endorse or
#        promote products derived from this software without specific prior
#        written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
#  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
#  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
#  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
##########################################################################

import Gaffer
import GafferArnold

__aliases = {
	"ai:visibility:camera" : "cameraVisibility",
	"ai:visibility:shadow" : "shadowVisibility",
	"ai:visibility:shadow_group" : "shadowGroup",
	"ai:visibility:diffuse_reflect" : "diffuseReflectionVisibility",
	"ai:visibility:specular_reflect" : "specularReflectionVisibility",
	"ai:visibility:diffuse_transmit" : "diffuseTransmissionVisibility",
	"ai:visibility:specular_transmit" : "specularTransmissionVisibility",
	"ai:visibility:volume" : "volumeVisibility",
	"ai:visibility:subsurface" : "subsurfaceVisibility",
	"ai:disp_autobump" : "autoBump",
	"ai:autobump_visibility:camera" : "cameraAutoBumpVisibility",
	"ai:autobump_visibility:shadow" : "shadowAutoBumpVisibility",
	"ai:autobump_visibility:diffuse_reflect" : "diffuseReflectionAutoBumpVisibility",
	"ai:autobump_visibility:specular_reflect" : "specularReflectionAutoBumpVisibility",
	"ai:autobump_visibility:diffuse_transmit" : "diffuseTransmissionAutoBumpVisibility",
	"ai:autobump_visibility:specular_transmit" : "specularTransmissionAutoBumpVisibility",
	"ai:autobump_visibility:volume" : "volumeAutoBumpVisibility",
	"ai:autobump_visibility:subsurface" : "subsurfaceAutoBumpVisibility",
	"ai:transform_type" : "transformType",
	"ai:matte" : "matte",
	"ai:opaque" : "opaque",
	"ai:receive_shadows" : "receiveShadows",
	"ai:self_shadows" : "selfShadows",
	"ai:sss_setname" : "sssSetName",
	"ai:polymesh:subdiv_iterations" : "subdivIterations",
	"ai:polymesh:subdiv_adaptive_error" : "subdivAdaptiveError",
	"ai:polymesh:subdiv_adaptive_metric" : "subdivAdaptiveMetric",
	"ai:polymesh:subdiv_adaptive_space" : "subdivAdaptiveSpace",
	"ai:polymesh:subdiv_uv_smoothing" : "subdivUVSmoothing",
	"ai:polymesh:subdiv_smooth_derivs" : "subdivSmoothDerivs",
	"ai:polymesh:subdiv_frustum_ignore" : "subdivFrustumIgnore",
	"ai:polymesh:subdivide_polygons" : "subdividePolygons",
	"ai:curves:mode" : "curvesMode",
	"ai:curves:min_pixel_width" : "curvesMinPixelWidth",
	"ai:points:min_pixel_width" : "pointsMinPixelWidth",
	"ai:volume:step_size" : "volumeStepSize",
	"ai:volume:step_scale" : "volumeStepScale",
	"ai:shape:step_size" : "shapeStepSize",
	"ai:shape:step_scale" : "shapeStepScale",
	"ai:shape:volume_padding" : "volumePadding",
	"ai:volume:velocity_scale" : "velocityScale",
	"ai:volume:velocity_fps" : "velocityFPS",
	"ai:volume:velocity_outlier_threshold" : "velocityOutlierThreshold",
	"ai:toon_id" : "toonId",
}

# Provide compatibility for ArnoldAttributes plugs renamed in Gaffer 1.6
for k, v in __aliases.items() :
	Gaffer.Metadata.registerValue( GafferArnold.ArnoldAttributes, "attributes", f"compatibility:childAlias:{k}", v )
