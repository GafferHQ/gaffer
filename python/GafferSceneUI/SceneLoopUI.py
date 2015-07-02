##########################################################################
#
#  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

	GafferScene.SceneLoop,

	"description",
	"""
	Applies a user defined processing loop to a scene. The content
	of the loop is defined by the node network placed between the
	previous and next plugs. The input scene is sent around this
	loop for a set number of iterations and then emerges as the
	output scene.
	""",

	plugs = {

		"previous" : [

			"description",
			"""
			The result from the previous iteration of the loop, or
			the input scene if no iterations have been performed yet.
			The content of the loop is defined by feeding this previous
			result through the scene processing nodes of choice and back
			around into the next plug.
			""",

		],

		"next" : [

			"description",
			"""
			The scene to be used as the start of the next iteration of
			the loop.
			""",

		],

		"iterations" : [

			"description",
			"""
			The number of times the loop is applied to form the output
			scene.
			""",

		],

		"indexVariable" : [

			"description",
			"""
			The name of a context variable used to specify the index
			of the current iteration. This can be referenced from
			expressions within the loop network to modify the operations
			performed during each iteration of the loop.
			"""

		],

	}

)
