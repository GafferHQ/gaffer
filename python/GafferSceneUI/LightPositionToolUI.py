##########################################################################
#
#  Copyright (c) 2023, Cinesite VFX Ltd. All rights reserved.
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

import imath

import IECore

import Gaffer
import GafferUI
import GafferSceneUI

def __toolTip( tool ) :

	mode = tool["mode"].getValue()
	result = None
	if mode == GafferSceneUI.LightPositionTool.Mode.Shadow :
		result = "Hold 'Shift' + 'V' to place shadow pivot\nHold 'V' to place shadow target"
	elif mode == GafferSceneUI.LightPositionTool.Mode.Highlight :
		result = "Hold 'V' to place highlight target"
	else :
		result = "Hold 'V' to place diffuse target"

	return result

Gaffer.Metadata.registerNode(

	GafferSceneUI.LightPositionTool,

	"description",
	"""
	Tool for placing lights.
	""",

	"viewer:shortCut", "D",
	"order", 7,
	"tool:exclusive", True,

	"ui:transformTool:toolTip", __toolTip,

	plugs = {

		"mode": [

			"description",
			"""
			The method to use for placing the light.

			- Shadow : Places the light so that it casts a shadow from the pivot point
			onto the target point.
			- Highlight : Places the light so that it creates a specular highlight at
			the target point.
			""",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

			"toolbarLayout:section", "Bottom",
			"toolbarLayout:width", 100,

			"preset:Shadow", GafferSceneUI.LightPositionTool.Mode.Shadow,
			"preset:Highlight", GafferSceneUI.LightPositionTool.Mode.Highlight,
			"preset:Diffuse", GafferSceneUI.LightPositionTool.Mode.Diffuse,

			"viewer:cyclePresetShortcut", "O",

		]

	}

)
