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

class __AttributesPlugProxy( object ) :

	__renames = {
		"cameraVisibility" : "ai:visibility:camera",
		"shadowVisibility" : "ai:visibility:shadow",
		"shadowGroup" : "ai:visibility:shadow_group",
		"diffuseReflectionVisibility" : "ai:visibility:diffuse_reflect",
		"specularReflectionVisibility" : "ai:visibility:specular_reflect",
		"diffuseTransmissionVisibility" : "ai:visibility:diffuse_transmit",
		"specularTransmissionVisibility" : "ai:visibility:specular_transmit",
		"volumeVisibility" : "ai:visibility:volume",
		"subsurfaceVisibility" : "ai:visibility:subsurface",
		"autoBump" : "ai:disp_autobump",
		"cameraAutoBumpVisibility" : "ai:autobump_visibility:camera",
		"shadowAutoBumpVisibility" : "ai:autobump_visibility:shadow",
		"diffuseReflectionAutoBumpVisibility" : "ai:autobump_visibility:diffuse_reflect",
		"specularReflectionAutoBumpVisibility" : "ai:autobump_visibility:specular_reflect",
		"diffuseTransmissionAutoBumpVisibility" : "ai:autobump_visibility:diffuse_transmit",
		"specularTransmissionAutoBumpVisibility" : "ai:autobump_visibility:specular_transmit",
		"volumeAutoBumpVisibility" : "ai:autobump_visibility:volume",
		"subsurfaceAutoBumpVisibility" : "ai:autobump_visibility:subsurface",
		"transformType" : "ai:transform_type",
		"matte" : "ai:matte",
		"opaque" : "ai:opaque",
		"receiveShadows" : "ai:receive_shadows",
		"selfShadows" : "ai:self_shadows",
		"sssSetName" : "ai:sss_setname",
		"subdivIterations" : "ai:polymesh:subdiv_iterations",
		"subdivAdaptiveError" : "ai:polymesh:subdiv_adaptive_error",
		"subdivAdaptiveMetric" : "ai:polymesh:subdiv_adaptive_metric",
		"subdivAdaptiveSpace" : "ai:polymesh:subdiv_adaptive_space",
		"subdivUVSmoothing" : "ai:polymesh:subdiv_uv_smoothing",
		"subdivSmoothDerivs" : "ai:polymesh:subdiv_smooth_derivs",
		"subdivFrustumIgnore" : "ai:polymesh:subdiv_frustum_ignore",
		"subdividePolygons" : "ai:polymesh:subdivide_polygons",
		"curvesMode" : "ai:curves:mode",
		"curvesMinPixelWidth" : "ai:curves:min_pixel_width",
		"pointsMinPixelWidth" : "ai:points:min_pixel_width",
		"volumeStepSize" : "ai:volume:step_size",
		"volumeStepScale" : "ai:volume:step_scale",
		"shapeStepSize" : "ai:shape:step_size",
		"shapeStepScale" : "ai:shape:step_scale",
		"volumePadding" : "ai:shape:volume_padding",
		"velocityScale" : "ai:volume:velocity_scale",
		"velocityFPS" : "ai:volume:velocity_fps",
		"velocityOutlierThreshold" : "ai:volume:velocity_outlier_threshold",
		"toonId" : "ai:toon_id",
	}

	def __init__( self, attributesPlug ) :

		self.__attributesPlug = attributesPlug

	def __getitem__( self, key ) :

		return self.__attributesPlug[self.__renames.get( key, key )]

def __attributesGetItem( originalGetItem ) :

	def getItem( self, key ) :

		result = originalGetItem( self, key )
		if key == "attributes" :
			scriptNode = self.ancestor( Gaffer.ScriptNode )
			if scriptNode is not None and scriptNode.isExecuting() :
				return __AttributesPlugProxy( result )

		return result

	return getItem

GafferArnold.ArnoldAttributes.__getitem__ = __attributesGetItem( GafferArnold.ArnoldAttributes.__getitem__ )
