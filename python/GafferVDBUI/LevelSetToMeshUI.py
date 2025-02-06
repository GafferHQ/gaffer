##########################################################################
#
#  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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
	GafferVDB.LevelSetToMesh,
	'description',
	"""Converts a level set VDB object to a mesh primitive .""",

	plugs={
		"filter" : [
			"description",
			"""
			The filter used to choose the vdbs to be converted. Source locations are
			pruned from the output scene, unless they are reused as part of a destination location
			(or a separate source scene is connected).
			"""
		],
		"source" : [
			"description",
			"""
			An optional alternate scene to provide the vdbs to be converted. When connected :

			- The `filter` chooses locations to be merged from the `source` scene rather than then `in` scene.
			- Source locations are not pruned from the output scene.
			"""
		],
		"destination" : [
			"description",
			"""
			By default, vdbs will be replaced with a mesh in place, using the destination `${scene:path}`.
			The destination can be modified to change where the outputs are placed. If multiple filtered locations
			have the same destination, the vdbs will be merged into one mesh.

			The destination location will be created if it doesn't exist already. If the name overlaps
			with an existing location that isn't filtered, the name will get a suffix.
			""",
		],
		'grid' : [
			'description',
			"""
			Name of the level set grid to create a mesh primitive from.
			"""
		],
		'isoValue' : [
			'description',
			"""
			Value which defines the isosurface to convert to a mesh primitive.
			Usually this is set to zero but setting a small positive number will generate a dilated mesh and negative will create an eroded mesh.
			"""
		],
		'adaptivity' : [
			'description',
			"""
			Adaptively generate fewer polygons from level set. 0 - uniform meshing, 1 - maximum level of adaptivity.
			"""
		]
	}
)
