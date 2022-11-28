##########################################################################
#
#  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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

	GafferScene.CopyPrimitiveVariables,

	"description",
	"""
	Copies primitive variables from a source scene, adding them to the objects
	of the main input scene.
	""",

	plugs = {

		"source" : [

			"description",
			"""
			The scene from which the primitive variables are copied.
			""",

		],

		"primitiveVariables" : [

			"description",
			"""
			The names of the primitive variables to be copied. These should be
			separated by spaces and can use Gaffer's standard wildcards
			to match multiple variables.
			""",

		],

		"sourceLocation" : [

			"description",
			"""
			The location in the source scene that primitive variables are copied from.
			By default, variables are copied from the location equivalent to the one
			they are being copied to. It is not an error if the location to be copied from
			does not exist; instead, no variables are copied.
			""",

			"plugValueWidget:type", "GafferSceneUI.ScenePathPlugValueWidget",
			"scenePathPlugValueWidget:scene", "source",

		],

		"prefix" : [

			"description",
			"""
			A prefix applied to the names of the copied primitive variables.
			""",

		],

		"ignoreIncompatible" : [

			"description",
			"""
			Causes the node to not error when attempting to copy primitive variables from
			the source object that are not compatible with the destination object.
			""",
		]

	}

)
