##########################################################################
#
#  Copyright (c) 2020, Cinesite VFX Ltd. All rights reserved.
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

	GafferScene.PrimitiveSampler,

	"description",
	"""
	Base class for nodes which sample primitive variables from
	another primitive.
	""",

	plugs = {

		"filter" : [

			"description",
			"""
			The filter used to determine which objects in the
			`in` scene will receive primitive variables sampled
			from the `sourceLocation` in the `source` scene.
			""",

		],

		"source" : [

			"description",
			"""
			The scene that contains the source primitive that
			primitive variables will be sampled from.
			""",

		],

		"sourceLocation" : [

			"description",
			"""
			The location of the primitive in the `source` scene that
			will be sampled from.
			""",

			"plugValueWidget:type", "GafferSceneUI.ScenePathPlugValueWidget",
			"scenePathPlugValueWidget:scene", "source",

		],

		"primitiveVariables" : [

			"description",
			"""
			The names of the primitive variables to be sampled from the source
			primitive. These should be separated by spaces and can use Gaffer's
			standard wildcards to match multiple variables. The sampled variables
			are prefixed with `prefix` before being added to the sampling object.
			""",

		],

		"prefix" : [

			"description",
			"""
			A prefix applied to the names of the sampled primitive variables before
			they are added to the sampling object. This is particularly useful when
			sampling something like "P", and not not wanting to modify the true
			vertex positions of the sampling primitive.
			""",

			"layout:section", "Settings.Output",

		],

		"status" : [

			"description",
			"""
			The name of a boolean primitive variable created to record the success or
			failure of the sampling operation.
			""",

			"layout:section", "Settings.Output",

		],

	}

)
