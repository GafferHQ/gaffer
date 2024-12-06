##########################################################################
#
#  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
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
import GafferSceneUI

Gaffer.Metadata.registerNode(

	GafferSceneUI.VisualiserTool,

	"description",
	"""
	Tool for displaying named primitive variables of type float, V2f or V3f as a colored overlay.
	""",

	"viewer:shortCut", "S",
	"viewer:shouldAutoActivate", False,
	"order", 8,
	"tool:exclusive", False,

	plugs = {

		"dataName" : [

			"description",
			"""
			Specifies the name of the primitive variable to visualise. The data should
			be of type float, V2f or V3f.
			""",

			"toolbarLayout:section", "Bottom",
			"toolbarLayout:width", 150,

		],
		"opacity" : [

			"description",
			"""
			The amount the visualiser will occlude the scene locations being visualised.
			""",

			"toolbarLayout:section", "Bottom",
			"toolbarLayout:width", 100,

		],
		"valueMin" : [

			"description",
			"""
			The minimum data channel value that will be mapped to 0.

			For float data only the first channel is used. For V2f data only the first
			and second channels are used. For V3f data all three channels are used.
			""",

			"toolbarLayout:section", "Bottom",
			"toolbarLayout:width", 175,

		],
		"valueMax" : [

			"description",
			"""
			The maximum data channel value that will be mapped to 1.

			For float data only the first channel is used. For V2f data only the first
			and second channels are used. For V3f data all three channels are used.
			""",

			"toolbarLayout:section", "Bottom",
			"toolbarLayout:width", 175,

		],
		"size": [

			"description",
			"""
			Specifies the size of the displayed text.
			""",

			"plugValueWidget:type", ""

		],

	},
)
