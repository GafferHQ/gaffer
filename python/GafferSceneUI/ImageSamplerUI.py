##########################################################################
#
#  Copyright (c) 2020, Hypothetical Inc. All rights reserved.
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

	GafferScene.ImageSampler,

	"description",
	"""
	Samples image data and transfers the values onto a primitive
	variable on the sampling objects. Values of \"Cs\", \"N\", 
	\"P\", \"Pref\", \"scale\", \"uv\", \"velocity\" and \"width\" 
	will define their interpretation appropriately when the correct 
	number of channels are sampled. Other variables will create a 
	float primitive variable per channel sampled.
	""",

	plugs = {

		"image" : [

			"description",
			"""
			The image to sample primitive variable data from.
			""",
			"plugValueWidget:type", "",
			"nodule:type", "GafferUI::StandardNodule",
			"noduleLayout:spacing", 2.0,

		],

		"primitiveVariable" : [

			"description",
			"""
			The primitive variable to sample image data onto.
			""",

		],

		"uvPrimitiveVariable" : [

			"description",
			"""
			The primitive variable holding uv data used to sample the image.
			""",
			
		],

		"channels" : [

			"description",
			"""
			The image channels to sample. Multiple channels are separated by spaces. 
			For vector primitive variables the order of the channels corresponds to 
			the indices of the vector. Wildcard expressions are not supported.
			""",

		],

		"uvBoundsMode" : [

				"description",
				"""
				The method to use to handle uv data outside the range of 0.0 - 1.0.
				- Clamp : Values below 0.0 will be reset to 0.0, values above 1.0 
				will be reset to 1.0 and values in between are unchanged.
				- Tile : Values wrap on integer boundaries.
				""",
				"preset:Clamp", 0,
				"preset:Tile", 1,
				"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
		],

	}

)
