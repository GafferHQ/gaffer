##########################################################################
#
#  Copyright (c) 2023, Cinesite VFX Ltd. All rights reserved.
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

Gaffer.Metadata.registerValues( {

	"option:dl:oversampling" : [

		"defaultValue", 4,
		"description",
		"""
		The number of camera rays to fire for each pixel of
		the image. Higher values may be needed to resolve fine
		geometric detail such as hair, or to reduce noise in
		heavily motion blurred renders.
		""",
		"label", "Oversampling",

	],

	"option:dl:quality.shadingsamples" : [

		"defaultValue", 1,
		"description",
		"""
		The number of samples to take when evaluating shading.
		This is the primary means of improving image quality and
		reducing shading noise.
		""",
		"label", "Shading Samples",

	],

	"option:dl:quality.volumesamples" : [

		"defaultValue", 1,
		"description",
		"""
		The number of samples to take when evaluating volumes.
		""",
		"label", "Volume Samples",

	],

	"option:dl:maximumraydepth.diffuse" : [

		"defaultValue", 1,
		"description",
		"""
		The maximum bounce depth a diffuse ray can reach. A depth
		of 1 specifies one additional bounce compared to purely
		local illumination.
		""",
		"label", "Diffuse",

	],

	"option:dl:maximumraydepth.hair" : [

		"defaultValue", 4,
		"description",
		"""
		The maximum bounce depth a hair ray can reach. Note that hair
		is akin to volumetric primitives and might need elevated ray
		depth to properly capture the illumination.
		""",
		"label", "Hair",

	],

	"option:dl:maximumraydepth.reflection" : [

		"defaultValue", 1,
		"description",
		"""
		The maximum bounce depth a reflection ray can reach. Setting
		the reflection depth to 0 will only compute local illumination
		meaning that only emissive surfaces will appear in the reflections.
		""",
		"label", "Reflection",

	],

	"option:dl:maximumraydepth.refraction" : [

		"defaultValue", 4,
		"description",
		"""
		The maximum bounce depth a refraction ray can reach. A value of 4
		allows light to shine through a properly modeled object such as a
		glass.
		""",
		"label", "Refraction",

	],

	"option:dl:maximumraydepth.volume" : [

		"defaultValue", 0,
		"description",
		"""
		The maximum bounce depth a volume ray can reach.
		""",
		"label", "Volume",

	],

} )
