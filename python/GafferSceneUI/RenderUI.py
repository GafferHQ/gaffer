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

	GafferScene.Preview.Render,

	"description",
	"""
	""",

	"layout:activator:modeIsSceneDescription", lambda node : node["mode"].getValue() == node.Mode.SceneDescriptionMode,

	plugs = {

		"*" : [

			"nodule:type", "",

		],

		"in" : [

			"description",
			"""
			The scene to be rendered.
			""",

			"nodule:type", "GafferUI::StandardNodule",

		],

		"renderer" : [

			"description",
			"""
			The renderer to use.
			""",

		],

		"mode" : [

			"description",
			"""
			The type of render to perform.
			""",

			"preset:Render", GafferScene.Preview.Render.Mode.RenderMode,
			"preset:Scene Description", GafferScene.Preview.Render.Mode.SceneDescriptionMode,

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"fileName" : [

			"description",
			"""
			The name of the file to be generated when in scene description mode.
			""",

			"plugValueWidget:type", "GafferUI.FileSystemPathPlugValueWidget",
			"pathPlugValueWidget:leaf", True,

			"layout:activator", "modeIsSceneDescription",

		],

		"out" : [

			"description",
			"""
			A direct pass-through of the input scene.
			""",

		],

	}
)
