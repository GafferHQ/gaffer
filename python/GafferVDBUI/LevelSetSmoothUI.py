##########################################################################
#
#  Copyright (c) 2026, Cinesite VFX Ltd. All rights reserved.
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
#      * Neither the name of Image Engine Design Inc nor the names of
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
import GafferVDB

Gaffer.Metadata.registerNode(

	GafferVDB.LevelSetSmooth,
	"description",
	"""
	Smooths a level set VDB.
	""",

	"layout:activator:modeHasRadius", lambda node : node["mode"].getValue() in ( GafferVDB.LevelSetSmooth.Mode.Box, GafferVDB.LevelSetSmooth.Mode.Gaussian, GafferVDB.LevelSetSmooth.Mode.Median ),

	plugs = {

		"grids" : {

			"description" :
			"""
			The names of the level set grids to smooth in the VDB object.
			Names should be separated by spaces and may contain any of
			Gaffer's standard wildcards.
			"""

		},

		"mode" : {

			"description" :
			"""
			The smoothing filter to apply to the level set.

			- Box : A separable box/mean filter. Fast to compute and provides simple and predictable
			  smoothing.
			- Gaussian : Produces smooth, gradual blurring, with nearby voxels contributing more
			  strongly than distant ones. Approximately four times slower than Box.
			- Median : Suppresses noise and outliers while generally preserving sharp details better than
			  Box or Gaussian. Relatively slow because the filter is not separable.
			- Mean Curvature : Smooths the surface according to how sharply it bends, affecting bumps and
			  sharp areas more strongly than flatter areas.
			- Laplacian : Diffuses values to neighbouring voxels, often producing similar results to
			  Mean Curvature while being faster to compute.
			- Fillet : Rounds off concave edges while leaving other areas unchanged. Useful for
			  smoothing internal corners and junctions between intersecting surfaces.
			""",

			"preset:Box" : GafferVDB.LevelSetSmooth.Mode.Box,
			"preset:Gaussian" : GafferVDB.LevelSetSmooth.Mode.Gaussian,
			"preset:Median" : GafferVDB.LevelSetSmooth.Mode.Median,
			"preset:Mean Curvature" : GafferVDB.LevelSetSmooth.Mode.MeanCurvature,
			"preset:Laplacian" : GafferVDB.LevelSetSmooth.Mode.Laplacian,
			"preset:Fillet" : GafferVDB.LevelSetSmooth.Mode.Fillet,

			"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget"

		},

		"radius" : {

			"description" :
			"""
			The radius of the Box, Gaussian, and Median smoothing kernels in voxel units.
			""",

			"layout:activator" : "modeHasRadius",

		},

		"iterations" : {

			"description" :
			"""
			The number of smoothing iterations.
			""",

		},

	}

)
