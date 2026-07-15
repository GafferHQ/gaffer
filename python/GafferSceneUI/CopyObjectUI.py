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

	GafferScene.CopyObject,

	"description",
	"""
	Copies objects from a source scene, replacing the filtered objects
	in the input scene. Objects include geometry such as meshes and curves,
	volumes, cameras etc.
	""",

	plugs = {

		"source" : {

			"description" :
			"""
			The scene from which the object is copied.
			""",

		},

		"sourceLocation" : {

			"description" :
			"""
			The location in the source scene that the copy is copied from.
			By default, objects are copied from the location equivalent to the one
			they are being copied to. It is not an error if the location to be copied from
			does not exist; instead, nothing is copied.
			""",

			"plugValueWidget:type" : "GafferSceneUI.ScenePathPlugValueWidget",
			"pathPlugValueWidget:placeholderText" : "${scene:path}",
			"scenePathPlugValueWidget:scene" : "source",

		},

		"adjustBounds" : {

			"description" :
			"""
			Adjusts bounding boxes to account for the copied objects.

			> Caution : Adjusting boundings boxes has a performance penalty.
			> If you do not need accurate bounds or you know that the bounds
			> will only change slightly, you may prefer to turn this off.
			""",

		},

	}

)
