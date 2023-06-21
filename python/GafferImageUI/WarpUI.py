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
import GafferImage

Gaffer.Metadata.registerNode(

	GafferImage.Warp,

	"description",
	"""
	Base class for nodes which apply warps to the input image.
	""",

	plugs = {

		"boundingMode" : [

			"description",
			"""
			The method used when accessing pixels outside the
			input data window.
			""",

			"preset:Black", GafferImage.Sampler.BoundingMode.Black,
			"preset:Clamp", GafferImage.Sampler.BoundingMode.Clamp,

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"filter" : [

			"description",
			"""
			The filter used to perform the resampling. The name
			of any OIIO filter may be specified, but this UI
			only exposes a limited range of 5 options which perform
			well for warping, ordered from softest to sharpest. Plus
			the extra "bilinear" mode which is lower quality, but
			fast.
			""",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

			"preset:Blackman-Harris", "blackman-harris",
			"preset:Cubic", "cubic",
			"preset:Keys", "keys",
			"preset:Simon", "simon",
			"preset:Rifman", "rifman",
			"preset:Bilinear", "bilinear",

		],

		"useDerivatives" : [

			"description",
			"""
			Whether accurate filter sizes should be computed that take into account the amount
			of distortion in the size and shape of pixels.  Should have minimal impact on warps
			that mostly preserve the size of pixels, but could have a large impact if there is
			heavy distortion.  Fixes problems with aliasing, at the cost of some extra calculations.
			""",

			"userDefault", False,
			"layout:activator", lambda plug : plug.node()["filter"].getValue() != "bilinear",
		],

	}

)
