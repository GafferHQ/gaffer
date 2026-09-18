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

	GafferScene.PointInstancerQuery,

	"description",
	"""
	Queries the properties of a single instance within a PointInstancer.
	""",

	"layout:section:Settings.Outputs:collapsed", False,

	plugs = {

		"scene" : {

			"description" :
			"""
			The scene to query.
			""",

		},

		"location" : {

			"description" :
			"""
			The location of the PointInstancer object.

			> Note : If the location does not exist or does not contain a PointInstancer
			> then the query will not be performed and all outputs will be set to their
			> default values.
			""",

			"plugValueWidget:type" : "GafferSceneUI.ScenePathPlugValueWidget",
			"scenePathPlugValueWidget:scene" : "scene",
			"nodule:type" : "",

		},

		"id" : {

			"description" :
			"""
			The ID of the instance to query.

			> Note : If the ID does not exist then the query will not be
			> performed and all outputs will be set to their default values.
			""",

			"noduleLayout:visible" : False,

		},

		"exists" : {

			"description" :
			"""
			Outputs true if the location contains a PointInstancer and the
			`id` exists within it.
			""",

			"layout:section" : "Settings.Outputs"

		},

		"prototype" : {

			"description" :
			"""
			Outputs the location of the prototype referenced by the instance.
			""",

			"layout:section" : "Settings.Outputs"

		},

		"transform" : {

			"description" :
			"""
			Outputs the transform for the instance.
			""",

			"layout:section" : "Settings.Outputs"

		},

		"visible" : {

			"description" :
			"""
			Outputs the visibility of the instance, as defined by
			the `invisibleIds` primitive variable on the PointInstancer.
			""",

			"layout:section" : "Settings.Outputs"

		},

		"attributes" : {

			"description" :
			"""
			Outputs the attributes for the instance, as defined
			by the vertex primitive variables on the PointInstancer.
			""",

			"layout:section" : "Settings.Outputs"

		},

	}

)
