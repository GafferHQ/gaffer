##########################################################################
#
#  Copyright (c) 2024, Image Engine Design Inc. All rights reserved.
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

import IECore

import Gaffer
import GafferUI

import GafferScene
import GafferSceneUI

##########################################################################
# Metadata
##########################################################################

Gaffer.Metadata.registerNode(

	GafferScene.MergeObjects,

	"description",
	"""
	The base type for scene nodes that merge locations into combined
	locations. Appropriate for nodes which merge primitives, or convert
	transforms to points.
	""",

	"layout:activator:sortKeyIsPrimVar", lambda node : node["sortKey"].getValue() == GafferScene.MergeObjects.SortKey.PrimitiveVariable,

	"layout:section:Settings.Merge Order:collapsed", False,

	plugs = {

		"filter" : {

			"description" :
			"""
			The filter used to choose the source locations to be merged. Source locations are
			pruned from the output scene, unless they are reused as part of a destination location
			(or a separate source scene is connected).
			"""
		},

		"source" : {

			"description" :
			"""
			An optional alternate scene to provide the locations to be merged. When connected :

			- The `filter` chooses locations to be merged from the `source` scene rather than then `in` scene.
			- Source locations are not pruned from the output scene.
			"""

		},


		"destination" : {

			"description" :
			"""
			The destination location where filtered locations will be merged to. The destination
			location will be created if it doesn't exist already. If the name overlaps with an existing
			location that isn't filtered, the name will get a suffix. May depend on the current value
			of scene:path in order to individually map input locations to different destinations.
			""",

		},

		"sortKey" : {

			"description" :
			"""
			Determines the order in which source objects are merged into the destination.

			- Location Name : Sources are sorted alphabetically by location.
			- Primitive Variable : Sources are sorted by the values of a primitive variable they each contain.
			""",

			"layout:section" : "Settings.Merge Order",
			"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",
			"preset:Location Name" : GafferScene.MergeObjects.SortKey.LocationName,
			"preset:Primitive Variable" : GafferScene.MergeObjects.SortKey.PrimitiveVariable

		},

		"sortPrimitiveVariable" : {

			"description" :
			"""
			A primitive variable on each input that defines the sort order. All inputs must define
			the named primitive variable with a Constant interpolation, and a matching type, either
			int, float, or Color3f.
			""",

			"layout:section" : "Settings.Merge Order",
			"layout:activator" : "sortKeyIsPrimVar",
		},

		"sortOrder" : {

			"description" :
			"""
			Allows reversing the sort order.
			""",

			"layout:section" : "Settings.Merge Order",
			"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",
			"preset:Ascending" : GafferScene.MergeObjects.SortOrder.Ascending,
			"preset:Descending" : GafferScene.MergeObjects.SortOrder.Descending

		},

	},

)
