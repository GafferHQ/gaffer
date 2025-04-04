##########################################################################
#
#  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
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

# RenderManShaderUI derives UI metadata from `.args` files automatically. But
# this doesn't cover everything we need for a good user experience, so here we
# manually register additional Gaffer-specific metadata for that.

shaderMetadata = {

	"ri:surface:PxrDisney" : {

		"noduleLayout:defaultVisibility" : False,

		"parameters" : {

			k : { "noduleLayout:visible" : True }
			for k in [ "baseColor", "subsurfaceColor", "metallic", "specular", "roughness", "bumpNormal" ]

		},

	},

	"ri:surface:PxrDisneyBsdf" : {

		"noduleLayout:defaultVisibility" : False,

		"parameters" : {

			k : { "noduleLayout:visible" : True }
			for k in [ "baseColor", "subsurfaceColor", "metallic", "specularTint", "roughness", "bumpNormal" ]

		},

	},

	"ri:surface:LamaConductor" : {

		"noduleLayout:defaultVisibility" : False,

		"parameters" : {

			k : { "noduleLayout:visible" : True }
			for k in [ "tint", "reflectivity", "edgeColor", "roughness", "conductorNormal" ]

		},

	},

	"ri:surface:LamaDielectric" : {

		"noduleLayout:defaultVisibility" : False,

		"parameters" : {

			k : { "noduleLayout:visible" : True }
			for k in [ "reflectionTint", "transmissionTint", "roughness", "normal" ]

		},

	},

	"ri:surface:LamaGeneralizedSchlick" : {

		"noduleLayout:defaultVisibility" : False,

		"parameters" : {

			k : { "noduleLayout:visible" : True }
			for k in [ "reflectionTint", "transmissionTint", "roughness", "normal" ]

		},

	},

	"ri:surface:LamaHairChiang" : {

		"noduleLayout:defaultVisibility" : False,

		"parameters" : {

			k : { "noduleLayout:visible" : True }
			for k in [ "colorR", "colorTT", "colorTintTT" ]

		},

	},

	"ri:surface:LamaIridescence" : {

		"noduleLayout:defaultVisibility" : False,

		"parameters" : {

			"roughness" : { "noduleLayout:visible" : True }

		},

	},

	"ri:surface:LamaSSS" : {

		"noduleLayout:defaultVisibility" : False,

		"parameters" : {

			k : { "noduleLayout:visible" : True }
			for k in [ "sssColor", "sssNormal" ]

		},

	},

	"ri:surface:LamaTricolorSSS" : {

		"noduleLayout:defaultVisibility" : False,

		"parameters" : {

			k : { "noduleLayout:visible" : True }
			for k in [ "nearColor", "farColor", "shadowColor", "sssNormal" ]

		},

	},

	"ri:surface:PxrLayerSurface" : {

		"noduleLayout:defaultVisibility" : False,

	},

	"ri:surface:PxrMarschnerHair" : {

		"noduleLayout:defaultVisibility" : False,

		"parameters" : {

			k : { "noduleLayout:visible" : True }
			for k in [ "diffuseGain", "diffuseColor", "specularColorR", "specularColorTRT", "specularColorTT" ]

		},

	},

	"ri:surface:PxrSurface" : {

		"noduleLayout:defaultVisibility" : False,

		"parameters" : {

			k : { "noduleLayout:visible" : True }
			for k in [ "diffuseGain", "diffuseColor", "specularFaceColor", "specularEdgeColor", "specularRoughness", "subsurfaceColor", "bumpNormal" ]

		},

	},

	"ri:surface:PxrVolume" : {

		"noduleLayout:defaultVisibility" : False,

		"parameters" : {

			k : { "noduleLayout:visible" : True }
			for k in [ "diffuseColor", "emitColor", "densityFloat", "densityColor" ]

		},

	},

	"ri:integrator:PxrUnified" : {

		"parameters" : {

			k : { "nodule:type" : "" }
			for k in [
				"accumOpacity", "allowMultilobeIndirect", "catchAllLights", "causticClamp", "directClamp", "emissionMultiplier", "enableSampleTimers",
				"enableShadingTimers", "enableVolumeCaustics", "indirectClamp", "indirectDirectionalBlurRadius", "indirectOversampling", "indirectSpatialBlurRadius",
				"indirectTrainingSamples", "jointSampling", "manifoldWalk", "maxIndirectBounces", "maxInterfaces", "maxIterations", "maxNonStochasticOpacityEvents",
				"maxRayDistance", "numBxdfSamples", "numIndirectSamples", "numLightSamples", "numVolumeAggregateSamples", "photonAdaptive", "photonEstimationNumber",
				"photonEstimationRadius", "photonVisibilityRod", "photonVisibilityRodDirectProb", "photonVisibilityRodMax", "photonVisibilityRodMin", "risPathGuiding",
				"rouletteDepth", "rouletteLightDepth", "rouletteThreshold", "sssOversampling", "suppressNaNs", "traceLightPaths", "useTraceDepth", "volumeAggregate",
				"volumeAggregateNameCamera", "volumeAggregateNameIndirect", "volumeAggregateNameTransmission", "walkThreshold"
			]

		},

	},

}

for shader, metadata in shaderMetadata.items() :

	for key, value in metadata.items() :

		if key == "parameters" :
			for parameterName, parameterMetadata in value.items() :
				for parameterKey, parameterValue in parameterMetadata.items() :
					Gaffer.Metadata.registerValue( shader + ":" + parameterName, parameterKey, parameterValue )

		else :

			Gaffer.Metadata.registerValue( shader, key, value )
