##########################################################################
#
#  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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
import GafferImage

# Command suitable for use with `NodeMenu.append()`.
def nodeMenuCreateCommand( menu ) :

	checkerboard = GafferImage.Checkerboard()
	checkerboard["size"].gang()

	return checkerboard

Gaffer.Metadata.registerNode(

	GafferImage.Checkerboard,

	"description",
	"""
	Outputs an image of a checkerboard pattern.
	""",

	plugs = {

		"format" : {

			"description" :
			"""
			The resolution and aspect ratio of the image.
			""",

		},

		"colorA" : {

			"description" :
			"""
			The colour of half of the squares of the pattern.
			""",

		},

		"colorB" : {

			"description" :
			"""
			The colour of the other half of the squares of the pattern.
			""",

		},

		"size" : {

			"description" :
			"""
			The size of the squares in pixels. This can be varied independently
			in the x and y directions.
			""",

		},

		"layer" : {

			"description" :
			"""
			The layer to generate. The output channels will
			be named ( layer.R, layer.G, layer.B and layer.A ).
			""",
			"stringPlugValueWidget:placeholderText" : "[RGBA]",
		},

		"transform" : {

			"description" :
			"""
			A transformation applied to the entire checkerboard pattern.
			The translate and pivot values are specified in pixels,
			and the rotate value is specified in degrees.
			""",

			"plugValueWidget:type" : "GafferUI.LayoutPlugValueWidget",
			"layout:section" : "Transform",

		},


	}

)
