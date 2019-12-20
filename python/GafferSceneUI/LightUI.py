##########################################################################
#
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

import GafferScene

Gaffer.Metadata.registerNode(

	GafferScene.Light,

	"description",
	"""
	Creates a scene with a single light in it.
	""",

	plugs = {

		"parameters" : [

			"description",
			"""
			The parameters of the light shader - these will vary based on the light type.
			""",

			"plugValueWidget:type", "GafferUI.LayoutPlugValueWidget",
			"nodule:type", "GafferUI::CompoundNodule",
			"noduleLayout:section", "left",
			"noduleLayout:spacing", 0.2,


		],

		"parameters.*" : [

			# Although the parameters plug is positioned
			# as we want above, we must also register
			# appropriate values for each individual parameter,
			# for the case where they get promoted to a box
			# individually.
			"noduleLayout:section", "left",
			"nodule:type", "",

		],

		"defaultLight" : [

			"description",
			"""
			Whether this light illuminates all geometry by default. When
			toggled, the light will be added to the \"defaultLights\" set, which
			can be referenced in set expressions and manipulated by downstream
			nodes.
			""",

			"layout:section", "Light Linking",

		],

		"visualiserAttributes" : [

			"description",
			"""
			Attributes that affect the visualisation of this Light in the Viewer.
			""",

			"layout:section", "Visualisation",

		],

		"visualiserAttributes.lightDrawingMode" : [

			"description",
			"""
			Controls how lights are presented in the Viewer.
			""",

			"label", "Light Drawing Mode",

		],

		"visualiserAttributes.maxTextureResolution" : [

			"description",
			"""
			Visualisers that load textures will respect this setting to
			limit their resolution.
			""",

		],

		"visualiserAttributes.ornamentScale" : [

			"description",
			"""
			Scales non-geometric visualisations in the viewport to make them
			easier to work with.
			""",

		],

		"visualiserAttributes.lightDrawingMode.value" : [

			"preset:Wireframe", "wireframe",
			"preset:Color", "color",
			"preset:Texture", "texture",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget"
		]

	}

)
