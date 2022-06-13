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

import Gaffer
import GafferUI
import GafferUSD

Gaffer.Metadata.registerNode(

	GafferUSD.USDLayerWriter,

	"description",
	"""
	Takes two input scenes and writes a minimal USD file containing the
	differences between them. This new file can then be layered in a USD
	composition to transform the first scene into the second. This is useful for
	baking modifications made in Gaffer into a USD file for consumption in other
	hosts.

	A typical use case might be to share lookdev authored in Gaffer, with a
	workflow like the following :

	- A SceneReader brings `model.usd` into Gaffer.
	- Shaders and attributes are applied in Gaffer, using Gaffer's standard scene
	  processing nodes.
	- A USDLayerWriter is used to bake this lookdev into a new `look.usd` layer on
	  disk, with the SceneReader for `model.usd` connected to the `base` input
	  and the lookdev connected into the `layer` input.
	- A new USD file is created that layers `look.usd` over `model.usd`. This is
	  loaded into Gaffer or another host for lighting.

	> Note : To write a complete USD file (rather than a layer containing differences)
	> use the standard SceneWriter node.
	""",

	plugs = {

		"base" : [

			"description",
			"""
			The base scene that the `layer` input is compared to.
			""",

			"nodule:type", "GafferUI::StandardNodule",

		],

		"layer" : [

			"description",
			"""
			The scene to be written to `fileName`. This is compared to the
			`base` scene, and only differences are written to the file.
			""",

			"nodule:type", "GafferUI::StandardNodule",

		],

		"fileName" : [

			"description",
			"""
			The name of the USD file to be written.
			""",

			"plugValueWidget:type", "GafferUI.FileSystemPathPlugValueWidget",
			"path:leaf", True,
			"path:bookmarks", "sceneCache",
			"fileSystemPath:extensions", "usd usda usdc",
			"fileSystemPath:extensionsLabel", "Show only USD files",

		],

		"out" : [

			"description",
			"""
			A direct pass-through of the `layer` input.
			""",

		],

	}

)
