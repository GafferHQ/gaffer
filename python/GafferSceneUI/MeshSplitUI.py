##########################################################################
#
#  Copyright (c) 2023, Image Engine Design Inc. All rights reserved.
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
import GafferScene

Gaffer.Metadata.registerNode(

	GafferScene.MeshSplit,

	"description",
	"""
	Splits a mesh into separate meshes for each unique value of a chosen
	Uniform ( per-face ) primitive variable.  The meshes will be created as children
	of the original mesh, and the original mesh will be removed.
	""",

	plugs = {

		"parent" : [

			"description",
			"""
			Legacy plug. Do not use.
			"""

		],

		"segment" : [

			"description",
			"""
			The name of the primitive variable to split based on.  Must be a
			Uniform ( per-face ) primitive variable.  A separate mesh will be
			created for each unique value of this primitive variable.
			""",
		],

		"nameFromSegment" : [

			"description",
			"""
			If true, the resulting meshes will be named based on the value of
			the primitive variable chosen by `segment`.  Requires that the chosen
			primitive variable be a string.

			Otherwise, the resulting meshes will just be named based on an integer index.
			""",
		],

		"preciseBounds" : [

			"description",
			"""
			Create tightly fitted bounding boxes that exactly fit each split child mesh.
			This requires visiting the vertices of the input mesh, so is more expensive.
			If false, the bounding box of the original mesh is used for all new meshes
			- this is technically correct, since they are all contained within this
			bounding box, but isn't as informative.
			""",
		],

	}

)
