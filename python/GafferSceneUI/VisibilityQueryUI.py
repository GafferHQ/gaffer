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

	GafferScene.VisibilityQuery,

	"description",
	"""
	Queries a scene location to see if it is visible, taking
	into account the `scene:visible` attribute on it and all of
	its ancestors.

	> Note : If an ancestor is invisible, then all its descendants
	> are too, no matter the value of their own `scene:visible`
	> attribute. In other words, invisible locations prune entire
	> subhierarchies from the scene.
	""",


	"layout:section:Settings.Outputs:collapsed", False,

	plugs = {

		"scene" : {

			"description" :
			"""
			The scene to query the visibility from.
			""",

		},

		"location" : {

			"description" :
			"""
			The location within to query the visibility for.

			> Note : If the location does not exist then the query will not be
			> performed and all outputs will be set to their default values.
			""",

			"plugValueWidget:type" : "GafferSceneUI.ScenePathPlugValueWidget",
			"scenePathPlugValueWidget:scene" : "scene",
			"nodule:type" : "",

		},

		"visible" : {

			"description" :
			"""
			Outputs `True` if the location is visible, and `False` otherwise.
			""",

			"layout:section" : "Settings.Outputs"

		},

		"invisibleAncestors" : {

			"description" :
			"""
			Outputs the list of all ancestors of `location` which have a
			`scene:visible` attribute set to `False`. This is the minimal
			list of locations that would need to be made visible in
			order for the location to be seen.

			> Note : Also includes the location itself if it has `scene:visible`
			> set to `False`.

			> Tip : To make the location visible, use DeleteAttributes to delete
			> the `scene:visible` attribute, filtering via a PathFilter driven
			> by `invisibleAncestors`.
			""",

			"layout:section" : "Settings.Outputs"

		},

	}

)
