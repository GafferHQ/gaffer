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

import IECore

import Gaffer
import GafferScene

##########################################################################
# Metadata
##########################################################################

Gaffer.Metadata.registerNode(

	GafferScene.ImageScatter,

	"description",
	"""
	Scatters points across an image, using pixel values to control the density
	of the points. Arbitrary image channels may be converted to additional
	primitive variables on the points, and point width may also be driven by an
	image channel.

	> Note : Only the area of the `displayWindow` is considered. To
	> include overscan pixels, use a Crop node to extend the display
	> window.
	""",

	plugs = {

		"sets" : [

			"layout:divider", True,

		],

		"image" : [

			"description",
			"""
			The image used to drive the point scattering process.
			""",

			"nodule:type", "GafferUI::StandardNodule",

		],

		"view" : [

			"description",
			"""
			The view within the image to be used by the scattering process.
			""",

			"plugValueWidget:type", "GafferImageUI.ViewPlugValueWidget",
			"layout:divider", True,

		],

		"density" : [

			"description",
			"""
			The overall density of the scattered points, defined in points
			per pixel.
			"""

		],

		"densityChannel" : [

			"description",
			"""
			The image channel used to modulate the density of the scattered points.
			Black pixels will receive no points and white pixels will receive the
			full amount as defined by the `density` plug.
			"""

		],

		"primitiveVariables" : [

			"description",
			"""
			The image channels to be converted to primitive variables on
			the points. The chosen channels are converted using the
			following rules :

			- The main `RGB` channels are converted to a colour primitive variable called `Cs`.
			- `<layerName>.RGB` channels are converted to a colour primitive variable called `<layerName>`.
			- Other channels are converted to individual float primitive variables.
			""",

			"plugValueWidget:type", "GafferImageUI.ChannelMaskPlugValueWidget",

		],

		"width" : [

			"description",
			"""
			The width of the points. If `widthChannel` is used as well, then this acts as
			a multiplier on the channel values.
			"""

		],

		"widthChannel" : [

			"description",
			"""
			The channel used to provide per-point width values for the points.
			""",

			"plugValueWidget:type", "GafferImageUI.ChannelPlugValueWidget",
			"channelPlugValueWidget:imagePlugName", "image",
			"channelPlugValueWidget:extraChannels", IECore.StringVectorData( [ "" ] ),
			"channelPlugValueWidget:extraChannelLabels", IECore.StringVectorData( [ "None" ] ),
			"layout:divider", True,

		],

	}

)
