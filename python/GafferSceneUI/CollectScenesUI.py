##########################################################################
#
#  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

	GafferScene.CollectScenes,

	"description",
	"""
	Builds a scene by bundling multiple input scenes together, each
	under their own root location. Instead of using an array of inputs
	like the Group node, a single input is used instead, and a Context
	Variable is provided so that a different hierarchy can be generated
	under each root location. This is especially powerful for building
	dynamic scenes where the number of inputs is not known prior to
	building the node graph.

	Since merging globals from multiple scenes often doesn't make sense,
	the output globals are taken directly from the scene corresponding to
	`rootNames[0]`.
	""",

	"ui:spreadsheet:activeRowNamesConnection", "rootNames",
	"ui:spreadsheet:selectorContextVariablePlug", "rootNameVariable",

	plugs = {

		"rootNames" : [

			"description",
			"""
			The names of the locations to create at the root of
			the output scene. The input scene is copied underneath
			each of these root locations.

			Often the rootNames will be driven by an expression that generates
			a dynamic number of root locations, perhaps by querying an asset
			management system or listing cache files on disk.
			""",

		],

		"rootNameVariable" : [

			"description",
			"""
			The name of a Context Variable that is set to the current
			root name when evaluating the input scene. This can be used
			in upstream expressions and string substitutions to generate
			a different hierarchy under each root location.
			""",

		],

		"sourceRoot" : [

			"description",
			"""
			Specifies the root of the subtree to be copied from the input
			scene. The default value causes the whole scene to be collected.

			The rootName variable may be used in expressions and string
			substitutions for this plug, allowing different subtrees to be
			collected for each root name in the output.

			> Tip :
			> By specifying a leaf location as the root, it is possible to
			> collect single objects from the input scene.
			"""

		],

	}

)
