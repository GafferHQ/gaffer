##########################################################################
#
#  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

	GafferScene.FilterResults,

	"description",
	"""
	Searches an input scene for all locations matched
	by a filter.

	> Caution : This can be an arbitrarily expensive operation
	depending on the size of the input scene and the filter
	used. In particular it should be noted that the usage of
	`...` in a PathFilter will cause the entire input scene to
	be searched even if there are no matches to be found.
	""",

	plugs = {

		"scene" : [

			"description",
			"""
			The scene to be searched for matching
			locations.
			""",

		],

		"filter" : [

			"description",
			"""
			The filter to be used when searching for
			matching locations.
			""",

			"plugValueWidget:type", "GafferUI.ConnectionPlugValueWidget",

		],

		"root" : [

			"description",
			"""
			Isolates the search to this location and its descendants.
			""",

			"plugValueWidget:type", "GafferSceneUI.ScenePathPlugValueWidget",
			"scenePathPlugValueWidget:scene", "scene",
			"nodule:type", "",

		],

		"out" : [

			"description",
			"""
			The results of the search, as an `IECore::PathMatcher` object. This
			is most useful for performing hierarchical queries and for iterating
			through the paths without an expensive conversion to strings.
			""",

			"plugValueWidget:type", "",

		],

		"outStrings" : [

			"description",
			"""
			The results of the search, converted to a list of strings. This is
			useful for connecting directly to other plugs, such as
			`Wedge.strings` or `CollectScenes.rootNames`.
			""",

			"plugValueWidget:type", "",

		],

	}

)
