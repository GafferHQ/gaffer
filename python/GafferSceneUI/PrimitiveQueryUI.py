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

	GafferScene.PrimitiveQuery,

	"description",
	"""
	Queries the geometric primitive at a scene location, outputting its type and the
	sizes for each type of primitive variable interpolation (`Uniform`, `Vertex` etc).
	""",

	"noduleLayout:section:bottom:spacing", 0.4,

	plugs = {

		"scene" : {

			"description" :
			"""
			The scene to query.
			"""

		},

		"location" : {

			"description" :
			"""
			The location within the scene to query.
			> Note : If the location does not exist, or contains no primitive,
			> all outputs will be set to their default values.
			""",

			"plugValueWidget:type" : "GafferSceneUI.ScenePathPlugValueWidget",
			"scenePathPlugValueWidget:scene" : "scene",
			"nodule:type" : ""

		},

		"type" : {

			"description" :
			"""
			The type of primitive at the queried location, for example
			`MeshPrimitive` or `PointsPrimitive`. Empty if there is no
			primitive at the location.
			""",

			"layout:section" : "Settings.Outputs"

		},

		"uniform" : {

			"description" :
			"""
			The number of values needed for `Uniform` primitive variables
			at the queried location. Zero if there is no primitive at the
			location.

			> Info : For mesh primitives, this is the number of faces. For
			> curve primitives it is the number of individual curves.
			""",

			"layout:section" : "Settings.Outputs"

		},

		"vertex" : {

			"description" :
			"""
			The number of values needed for `Vertex` primitive variables
			at the queried location. Zero if there is no primitive at
			the location.
			""",

			"layout:section" : "Settings.Outputs"

		},

		"varying" : {

			"description" :
			"""
			The number of values needed for `Varying` primitive variables
			at the queried location. Zero if there is no primitive at the
			location.
			""",

			"layout:section" : "Settings.Outputs"

		},

		"faceVarying" : {

			"description" :
			"""
			The number of values needed for `FaceVarying` primitive variables
			at the queried location. Zero if there is no primitive at the
			location.
			""",

			"layout:section" : "Settings.Outputs"

		},

		"primitive" : {

			"description" :
			"""
			The complete Primitive from the queried location, or a NullObject
			if there is no primitive.
			""",

			"layout:section" : "Settings.Outputs",

		},

	}

)
