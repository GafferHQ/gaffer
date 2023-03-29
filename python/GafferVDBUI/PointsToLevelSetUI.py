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

import GafferUI
import GafferVDB

GafferUI.Metadata.registerNode(

	GafferVDB.PointsToLevelSet,

	"description",
	"""
	Converts a points primitive to an OpenVDB level set.
	""",

	"layout:activator:usingVelocity", lambda node : node["useVelocity"].getValue(),

	plugs = {

		"width" : [

			"description",
			"""
			The name of a `float` primitive variable specifying the width of each point.
			The primitive variable may have either `Vertex` or `Constant` interpolation.
			If the primitive variable doesn't exist, a width of 1.0 is used.

			> Note : A point's width needs to be at least 3x `voxelSize` to contribute to
			> the level set. Smaller points will be ignored, and reported as a warning.
			"""

		],

		"widthScale" : [

			"description",
			"""
			An additional multiplier on the width of each point.
			"""

		],

		"useVelocity" : [

			"description",
			"""
			Enables the creation of trails behind the points, based
			on the `velocity` primitive variable.
			""",

		],

		"velocity" : [

			"description",
			"""
			The name of a `V3f` primitive variable specifying the velocity
			of each point. Velocity is specified in local-space units per
			second, and the trail is automatically scaled to represent the
			motion within a single frame.
			""",

			"layout:activator", "usingVelocity",

		],

		"velocityScale" : [

			"description",
			"""
			An additional multiplier applied to the velocity of each point.
			""",

			"layout:activator", "usingVelocity",

		],

		"grid" : [

			"description",
			"""
			Name of the level set grid to be created.
			"""

		],

		"voxelSize" : [

			"description",
			"""
			Size of a voxel in the level set grid, specified in local space. Smaller voxel
			sizes will increase resolution, but take more memory and computation time.
			"""
		],

		"halfBandwidth" : [

			"description",
			"""
			Defines the exterior and interior width of the level set in voxel units.
			"""

		],

	}

)
