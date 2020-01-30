##########################################################################
#
#  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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

import itertools

import Gaffer
import GafferUI
import GafferImage

Gaffer.Metadata.registerNode(

	GafferImage.ImageTransform,

	"description",
	"""
	Scales, rotates and translates an image within its display window.
	Note that although the format is not changed, the data window is
	expanded to include the portions of the image which have been
	transformed outside of the display window, and these out-of-frame
	pixels can still be used by downstream nodes.
	""",

	plugs = {

		"transform" : [

			"description",
			"""
			The transformation to be applied to the image. The translate
			and pivot values are specified in pixels, and the rotate
			value is specified in degrees.
			""",

			"plugValueWidget:type", "GafferUI.LayoutPlugValueWidget",

		],

		"filter" : [

			"description",
			"""
			The pixel filter used when transforming the image. Each
			filter provides different tradeoffs between sharpness and
			the danger of aliasing or ringing.
			""",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		] + list( itertools.chain(

			# Disk doesn't make much sense as a resizing filter, and also causes artifacts because
			# its default width is small enough to fall into the gaps between pixels.
			*[ ( "preset:" + x.title(), x ) for x in GafferImage.FilterAlgo.filterNames() if x != "disk" ]

		) ),

		"invert" : [
			"description",
			"""
			Apply the inverse transformation to the image.
			"""
		],

		"concatenate" : [

			"description",

			"""
			Combines the processing for a series of ImageTransforms so that
			transformation and filtering is only applied once. This gives better
			image quality and performance.

			> Note : When concatenation is in effect, the filter settings on upstream
			> ImageTransforms are ignored.
			""",

			"layout:section", "Node",
			"layout:index", -1,

		],

	}

)
