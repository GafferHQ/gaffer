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

## \todo Migrate ArnoldOptions to use this metadata so we have one source of truth.
Gaffer.Metadata.registerValues( {

	"option:ai:AA_samples" : [

		"defaultValue", 3,
		"description",
		"""
		Controls the number of rays per pixel
		traced from the camera. The more samples,
		the better the quality of antialiasing,
		motion blur and depth of field. The actual
		number of rays per pixel is the square of
		the AA Samples value - so a value of 3
		means 9 rays are traced, 4 means 16 rays are
		traced and so on.
		""",
		"label", "AA Samples",

	],

	"option:ai:enable_adaptive_sampling" : [

		"defaultValue", False,
		"description",
		"""
		If adaptive sampling is enabled, Arnold will
		take a minimum of ( AA Samples * AA Samples )
		samples per pixel, and will then take up to
		( AA Samples Max * AA Samples Max ) samples per
		pixel, or until the remaining estimated noise
		gets lower than aaAdaptiveThreshold.
		""",
		"label", "Enable Adaptive Sampling",

	],

	"option:ai:AA_samples_max" : [

		"defaultValue", 0,
		"description",
		"""
		The maximum sampling rate during adaptive
		sampling. Like AA Samples, this value is
		squared. So AA Samples Max == 6 means up to
		36 samples per pixel.
		""",
		"label", "AA Samples Max",

	],

	"option:ai:AA_adaptive_threshold" : [

		"defaultValue", 0.05,
		"description",
		"""
		How much leftover noise is acceptable when
		terminating adaptive sampling. Higher values
		accept more noise, lower values keep rendering
		longer to achieve smaller amounts of noise.
		""",
		"label", "AA Adaptive Threshold",

	],

	"option:ai:GI_diffuse_samples" : [

		"defaultValue", 2,
		"description",
		"""
		Controls the number of rays traced when
		computing indirect illumination.
		""",
		"label", "Diffuse Samples",

	],

	"option:ai:GI_specular_samples" : [

		"defaultValue", 2,
		"description",
		"""
		Controls the number of rays traced when
		computing specular reflections.
		""",
		"label", "Specular Samples",

	],

	"option:ai:GI_transmission_samples" : [

		"defaultValue", 2,
		"description",
		"""
		Controls the number of rays traced when
		computing specular refractions.
		""",
		"label", "Transmission Samples",

	],

	"option:ai:GI_sss_samples" : [

		"defaultValue", 2,
		"description",
		"""
		Controls the number of rays traced when
		computing subsurface scattering.
		""",
		"label", "SSS Samples",

	],

	"option:ai:GI_volume_samples" : [

		"defaultValue", 2,
		"description",
		"""
		Controls the number of rays traced when
		computing indirect lighting for volumes.
		""",
		"label", "Volume Samples",

	],

	"option:ai:light_samples" : [

		"defaultValue", 0,
		"description",
		"""
		Specifies a fixed number of light samples to be taken at each
		shading point. This enables "Global Light Sampling", which provides
		significantly improved performance for scenes containing large numbers
		of lights. In this mode, the `samples` setting on each light is ignored,
		and instead the fixed number of samples is distributed among all the
		lights according to their contribution at the shading point.

		A value of `0` disables Global Light Sampling, reverting to the original
		per-light sampling algorithm.
		""",
		"label", "Light Samples",

	],

	"option:ai:GI_total_depth" : [

		"defaultValue", 10,
		"description",
		"""
		The maximum depth of any ray (Diffuse + Specular +
		Transmission + Volume).
		""",
		"label", "Total Depth",

	],

	"option:ai:GI_diffuse_depth" : [

		"defaultValue", 2,
		"description",
		"""
		Controls the number of ray bounces when
		computing indirect illumination ("bounce light").
		""",
		"label", "Diffuse Depth",

	],

	"option:ai:GI_specular_depth" : [

		"defaultValue", 2,
		"description",
		"""
		Controls the number of ray bounces when
		computing specular reflections.
		""",
		"label", "Specular Depth",

	],

	"option:ai:GI_transmission_depth" : [

		"defaultValue", 2,
		"description",
		"""
		Controls the number of ray bounces when
		computing specular refractions.
		""",
		"label", "Transmission Depth",

	],

	"option:ai:GI_volume_depth" : [

		"defaultValue", 0,
		"description",
		"""
		Controls the number of ray bounces when
		computing indirect lighting on volumes.
		""",
		"label", "Volume Depth",

	],

	"option:ai:auto_transparency_depth" : [

	"defaultValue", 10,
	"description",
	"""
	The number of allowable transparent layers - after
	this the last object will be treated as opaque.
	""",
	"label", "Transparency Depth",

	]

} )
