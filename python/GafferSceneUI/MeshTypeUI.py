##########################################################################
#
#  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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
import GafferUI
import GafferScene

##########################################################################
# Metadata
##########################################################################

Gaffer.Metadata.registerNode(

	GafferScene.MeshType,

	"description",
	"""
	Changes between polygon and subdivision representations
	for mesh objects, and optionally recalculates vertex
	normals for polygon meshes.

	Note that currently the Gaffer viewport does not display
	subdivision meshes with smoothing, so the results of using
	this node will not be seen until a render is performed.
	""",

	plugs = {

		"meshType" : [

			"description",
			"""
			The interpolation type to apply to the mesh.
			""",

			"preset:Unchanged", "",
			"preset:Polygon", "linear",
			"preset:Subdivision Surface", "catmullClark",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"calculatePolygonNormals" : [

			"description",
			"""
			Causes new vertex normals to be calculated for
			polygon meshes. Has no effect for subdivision
			surfaces, since those are naturally smooth and do
			not require surface normals. Vertex normals are
			represented as primitive variables named "N".
			""",

		],

		"overwriteExistingNormals" : [

			"description",
			"""
			By default, vertex normals will only be calculated for
			polygon meshes which don't already have them. Turning
			this on will force new normals to be calculated even for
			meshes which had them already.
			""",

		],

	}

)
