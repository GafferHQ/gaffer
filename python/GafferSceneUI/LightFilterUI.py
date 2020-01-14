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

import functools

import Gaffer
import GafferUI

import GafferScene

Gaffer.Metadata.registerNode(

	GafferScene.LightFilter,

	"description",
	"""
	Creates a scene with a single light filter in it.
	""",

	plugs = {

		"name" : [

			"layout:index", 0,

		],

		"filteredLights" : [

			"description",
			"""
			The lights that are being filtered. Accepts a SetExpression. You
			might want to set it to 'defaultLights' to have the filter affect
			all lights that haven't been excluded from that set.
			""",

			"layout:index", 1,
		],

		"sets" : [

			"layout:divider", True,
			"layout:index", 3,

		],

		"parameters" : [

			"description",
			"""
			The parameters of the light filter shader - these will vary based on the type.
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

	}

)

# Defer parameter metadata lookups to the internal shader
# node.

def __parameterMetadata( plug, key ) :

	node = plug.node()
	return Gaffer.Metadata.value( node["__shader"]["parameters"].descendant( plug.relativeName( node["parameters"] ) ), key )

for key in [
	"description",
	"label",
	"noduleLayout:label",
	"layout:divider",
	"layout:section",
	"presetNames",
	"presetValues",
	"plugValueWidget:type",
	"nodule:type",
	"noduleLayout:visible",
	"noduleLayout:label",
] :
	Gaffer.Metadata.registerValue( GafferScene.LightFilter, "parameters.*", key, functools.partial( __parameterMetadata, key = key ) )
