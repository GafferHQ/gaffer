##########################################################################
#
#  Copyright (c) 2023, Image Engine Design Inc. All rights reserved.
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

	GafferImage.DeepSlice,

	"description",
	"""
	Takes a slice out of an image with depth defined by Z ( and optionally ZBack ) channels by
	discarding everything outside of a clipping range. The range is half open, including point samples
	exactly at the near clip, but excluding point samples exactly at the far clip. This means that if
	you split an image into a front and back with two DeepSlices, they will composite back together to
	match the original.  Optionally also flattens the image.
	""",

	plugs = {

		"nearClip" : [

			"description",
			"""
			Removes everything with Z less than the near clip depth.
			""",

		],
		"nearClip.enabled" : [ "description", "Enables near clip." ],
		"nearClip.value" : [ "description", "Depth for near clip." ],
		"farClip" : [

			"description",
			"""
			Removes everything with Z greater than or equal to the far clip depth.
			""",

		],
		"farClip.enabled" : [ "description", "Enables far clip." ],
		"farClip.value" : [ "description", "Depth for far clip." ],
		"flatten" : [

			"description",
			"""
			Outputs a flat image, instead of output a deep image with any samples within the range.
			Flattening as part of DeepSlice is up to 2X faster than flattening afterwards, and is
			convenient if you're using a DeepSlice to preview the contents of a deep image by
			scrubbing through depth.
			""",

		],
	}

)
