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

	"option:cycles:session:samples" : [

		"defaultValue", 1024,
		"description",
		"""
		Number of samples to render for each pixel.
		""",
		"label", "Samples",

	],

	"option:cycles:integrator:use_adaptive_sampling" : [

		"defaultValue", False,
		"description",
		"""
		Automatically determine the number of samples
		per pixel based on a variance estimation.
		""",
		"label", "Adaptive Sampling",

	],

	"option:cycles:integrator:adaptive_threshold" : [

		"defaultValue", 0.0,
		"description",
		"""
		Noise level step to stop sampling at, lower values reduce noise the cost of render time.
		`0` for automatic setting based on number of AA samples.
		""",
		"label", "Adaptive Threshold",

	],

	"option:cycles:integrator:use_guiding" : [

		"defaultValue", False,
		"description",
		"""
		Use path guiding for sampling paths. Path guiding incrementally
		learns the light distribution of the scene and guides paths into directions
		with high direct and indirect light contributions.
		""",
		"label", "Path Guiding",

	],

	"option:cycles:integrator:min_bounce" : [

		"defaultValue", 0,
		"description",
		"""
		Minimum number of light bounces. Setting this higher reduces noise in the first bounces,
		but can also be less efficient for more complex geometry like hair and volumes.
		""",
		"label", "Min Bounces",

	],

	"option:cycles:integrator:max_bounce" : [

		"defaultValue", 7,
		"description",
		"""
		Total maximum number of bounces.
		""",
		"label", "Max Bounces",

	],

	"option:cycles:integrator:max_diffuse_bounce" : [

		"defaultValue", 7,
		"description",
		"""
		Maximum number of diffuse reflection bounces, bounded by total maximum.
		""",
		"label", "Diffuse",

	],

	"option:cycles:integrator:max_glossy_bounce" : [

		"defaultValue", 7,
		"description",
		"""
		Maximum number of glossy reflection bounces, bounded by total maximum.
		""",
		"label", "Glossy",

	],

	"option:cycles:integrator:max_transmission_bounce" : [

		"defaultValue", 7,
		"description",
		"""
		Maximum number of transmission reflection bounces, bounded by total maximum.
		""",
		"label", "Transmission",

	],

	"option:cycles:integrator:max_volume_bounce" : [

		"defaultValue", 7,
		"description",
		"""
		Maximum number of volumetric scattering events.
		""",
		"label", "Volume",

	],

	"option:cycles:integrator:transparent_max_bounce" : [

		"defaultValue", 7,
		"description",
		"""
		Maximum number of transparent bounces.
		""",
		"label", "Transparency",

	],

} )
