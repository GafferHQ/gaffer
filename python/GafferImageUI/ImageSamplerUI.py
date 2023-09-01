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
import GafferImage

Gaffer.Metadata.registerNode(

	GafferImage.ImageSampler,

	"description",
	"""
	Samples image colour at a specified pixel location.
	""",

	plugs = {

		"image" : [

			"description",
			"""
			The image to be sampled.
			""",

		],

		"view" : [

			"description",
			"""
			The view to be sampled.
			""",

			"nodule:type", "",
			"plugValueWidget:type", "GafferImageUI.ViewPlugValueWidget",
			"viewPlugValueWidget:allowUseCurrentContext", True,

		],

		"channels" : [

			"description",
			"""
			The names of the four channels to be sampled.
			""",

			"plugValueWidget:type", "GafferImageUI.RGBAChannelsPlugValueWidget",

		],

		"pixel" : [

			"description",
			"""
			The coordinates of the pixel to sample. These can have
			fractional values and bilinear interpolation will be used
			to interpolate between adjacent pixels.

			Note though that the coordinates at pixel centres are not integers.
			For example, the centre of the bottom left pixel of an image is
			at 0.5, 0.5.
			""",

		],

		"interpolate" : [

			"description",
			"""
			Turn on to blend with adjacent pixels when sampling away from the center of the pixel at 0.5, 0.5.
			If off, you always sample exactly one pixel.
			""",

			"userDefault", False,

		],

		"color" : [

			"description",
			"""
			The sampled colour.
			""",

		]

	}

)
