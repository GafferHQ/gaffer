##########################################################################
#
#  Copyright (c) 2022, Cinesite VFX Ltd. All rights reserved.
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

from re import M
import Gaffer
import GafferScene

Gaffer.Metadata.registerNode(

	GafferScene.SetQuery,

	"description",
	"""
	Queries the set memberships of a location, and outputs a list of
	the sets that it belongs to.
	""",

	plugs = {

		"scene" : [

			"description",
			"""
			The scene to query.
			""",

		],

		"location" : [

			"description",
			"""
			The location to query the set memberships for.
			""",

			"plugValueWidget:type", "GafferSceneUI.ScenePathPlugValueWidget",
			"scenePathPlugValueWidget:scene", "scene",
			"nodule:type", "",

		],

		"sets" : [

			"description",
			"""
			The sets to query.
			""",

			"nodule:type", "",

		],

		"inherit" : [

			"description",
			"""
			When on, locations are treated as being in a set if an
			ancestor location is in that set.
			""",

			"nodule:type", "",

		],

		"matches" : [

			"description",
			"""
			The list of sets that the `location` is a member of. Returned in the
			order they are listed in the `sets` plug.

			> Note : When matches are inherited from a parent location, these
			> are returned _before_ matches at this location, regardless of the
			> order they are listed in the `sets` plug. This makes `firstMatch`
			> consistent throughout the scene hierarchy, with children sharing
			> the `firstMatch` of their parent.
			""",

			"layout:section", "Settings.Outputs",

		],

		"firstMatch" : [

			"description",
			"""
			The first set from the `matches` output, or `""` if there were no matches.
			This is particularly convenient for use in a Spreadsheet's selector, to
			select rows based on the set membership of a location.
			""",

			"layout:section", "Settings.Outputs",

		]

	}

)
