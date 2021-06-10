##########################################################################
#
#  Copyright (c) 2021, Cinesite VFX Ltd. All rights reserved.
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

	GafferScene.TransformQuery,

	"description",
	"""
	Queries a particular location in a scene and outputs the transform.
	""",

	"layout:activator:spaceIsRelative", lambda node : node["space"].getValue() == GafferScene.TransformQuery.Space.Relative,

	plugs = {

		"scene" : [

			"description",
			"""
			The scene to query the transform for.
			"""

		],

		"location" : [

			"description",
			"""
			The location within the scene to query the transform at.

			> Note : If the location does not exist then the query will not be
			> performed and all outputs will be set to their default values.
			""",

			"plugValueWidget:type", "GafferSceneUI.ScenePathPlugValueWidget",
			"scenePathPlugValueWidget:scene", "scene",
			"nodule:type", ""

		],

		"space" : [

			"description",
			"""
			The space to query the transform.
			""",

			"preset:Local", GafferScene.TransformQuery.Space.Local,
			"preset:World", GafferScene.TransformQuery.Space.World,
			"preset:Relative", GafferScene.TransformQuery.Space.Relative,

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
			"nodule:type", ""
		],

		"relativeLocation" : [

			"description",
			"""
			The location within the scene to query the transform for relative space mode.

			> Note : If the location does not exist then the query will not be
			> performed and all outputs will be set to their default values.
			""",

			"plugValueWidget:type", "GafferSceneUI.ScenePathPlugValueWidget",
			"scenePathPlugValueWidget:scene", "scene",
			"layout:activator", "spaceIsRelative",
			"nodule:type", ""

		],

		"invert" : [

			"description",
			"""
			Invert the result transform.
			""",
			"nodule:type", ""

		],

		"matrix" : [

			"description",
			"""
			4x4 matrix of the requested transform.
			""",

			"layout:section", "Settings.Outputs"

		],

		"translate" : [
			"description",
			"""
			Translation component of requested transform.
			""",

			"layout:section", "Settings.Outputs"
		],

		"rotate" : [
			"description",
			"""
			Rotation component of requested transform (degrees).
			""",

			"layout:section", "Settings.Outputs"
		],

		"scale" : [
			"description",
			"""
			Scaling component of requested transform.
			""",

			"layout:section", "Settings.Outputs"
		],
	}
)
