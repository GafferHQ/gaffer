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
import GafferUI

import GafferScene
import GafferSceneUI

Gaffer.Metadata.registerNode(

	GafferScene.AttributeVisualiser,

	"description",
	"""
	Visualises attribute values by applying a constant
	shader to display them as a colour.
	""",

	"layout:activator:modeIsColorOrFalseColor", lambda node : node["mode"].getValue() in ( node.Mode.Color, node.Mode.FalseColor ),
	"layout:activator:modeIsFalseColor", lambda node : node["mode"].getValue() == node.Mode.FalseColor,

	plugs = {

		"attributeName" : {

			"description" :
			"""
			The name of the attribute to be visualised. The value of the
			attribute will be converted to a colour using the chosen mode
			and then assigned using a constant shader.
			""",

		},

		"mode" : {

			"description" :
			"""
			The method used to turn the attribute value into a colour for
			visualisation.

			- Color : This only works for attributes which already contain a colour
			  or numeric value. The value is converted directly to a colour, using the
			  min and max values to perform a remapping.
			- FalseColor : This only works for numeric attributes. Values between min
			  and max are used to look up a colour in the ramp below.
			- Random : This works for any attribute type - a random colour is chosen
			  for each unique attribute value.
			- Shader Node Color : This only works when visualising a shader attribute. It
			  uses the node colour for the shader node which is assigned.
			""",

			"preset:Color" : GafferScene.AttributeVisualiser.Mode.Color,
			"preset:FalseColor" : GafferScene.AttributeVisualiser.Mode.FalseColor,
			"preset:Random" : GafferScene.AttributeVisualiser.Mode.Random,
			"preset:Shader Node Color" : GafferScene.AttributeVisualiser.Mode.ShaderNodeColor,

			"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",

		},

		"min" : {

			"description" :
			"""
			Used in the Color and False Color modes to define the value which is mapped
			to black or the left end of the ramp respectively.
			""",

			"layout:activator" : "modeIsColorOrFalseColor",

		},

		"max" : {

			"description" :
			"""
			Used in the Color and False Color modes to define the value which is mapped
			to white or the right end of the ramp respectively.
			""",

			"layout:activator" : "modeIsColorOrFalseColor",

		},

		"ramp" : {

			"description" :
			"""
			Provides the colour mapping for the False Color mode. Values between min and
			max are remapped using the colours from the ramp (left to right).
			""",

			"layout:activator" : "modeIsFalseColor",

		},

		"shaderType" : {

			"description" :
			"""
			The type of shader used to perform the visualisation. The default value
			is for an OpenGL shader which will be used in the viewport. It's possible
			to perform a visualisation for other renderers by entering a different
			shader type here.
			""",

			"layout:section" : "Advanced",

		},

		"shaderName" : {

			"description" :
			"""
			The name of the shader used to perform the visualisation. The default value
			is for an OpenGL shader which will be used in the viewport. It's possible
			to perform a visualisation for other renderers by entering a different
			shader name here.
			""",

			"layout:section" : "Advanced",

		},

		"shaderParameter" : {

			"description" :
			"""
			The name of the shader parameter used to perform the visualisation. The default
			value is for an OpenGL shader which will be used in the viewport.
			""",

			"layout:section" : "Advanced",

		},

	}

)
