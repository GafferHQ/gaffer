##########################################################################
#
#  Copyright (c) 2020, Don Boogert. All rights reserved.
#  Copyright (c) 2023, Image Engine Design. All rights reserved.
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
#      * Neither the name of Don Boogert nor the names of
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

	GafferVDB.VolumeScatter,

	"description",
	"""
	Scatter points according the voxel values of a VDB grid.
	""",

	plugs = {

		"name" : [

			"description",
			"""
			The name given to the PointsPrimitive -
			this will be placed under the location specified by
			"destination".
			""",

		],

		"grid" : [

			"description",
			"""
			Name of grid in VDBObject in which points will be scattered.
			""",

		],

		"density" : [

			"description",
			"""
			This density is multiplied with the value of the grid to produce a number of points per unit volume.
			""",
		],

		"pointType" : [

			"description",
			"""
			The render type of the points. This defaults to
			"gl:point" so that the points are rendered in a
			lightweight manner in the viewport.
			""",

			"preset:GL Point", "gl:point",
			"preset:Particle", "particle",
			"preset:Sphere", "sphere",
			"preset:Disk", "disk",
			"preset:Patch", "patch",
			"preset:Blobby", "blobby",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"destination" : [

			"description",
			"""
			The location where the points primitives will be placed in the output scene.
			When the destination is evaluated, the `${scene:path}` variable holds
			the location of the source mesh, so the default value parents the points
			under the mesh.

			> Tip : `${scene:path}/..` may be used to place the points alongside the
			> source mesh.
			""",

		],

		"parent" : [

			"description",
			"""
			This plug has been deprecated in favour of using a filter to select the volume.
			"""
		],

	}
)
