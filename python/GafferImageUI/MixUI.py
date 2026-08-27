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
import GafferImage

Gaffer.Metadata.registerNode(

	GafferImage.Mix,

	"description",
	"""
	Blends two images together based on a mask.
	If the mask is 0 you get the first input, if it is 1 you get the second.
	""",

	plugs = {

		"in.in0" : {

			"description" :
			"""
			The B input.
			""",

		},

		"in.in1" : {

			"description" :
			"""
			The A input.
			""",

		},

		"mask" : {

			"description" :
			"""
			The image which contains the mask channel.
			""",
			"noduleLayout:section" : "right",
		},

		"mix" : {

			"description" :
			"""
			Control the blend between the two input images.
			0 to take first input, 1 to take second input.
			Multiplied together with the mask.
			""",
		},

		"maskChannel" : {

			"description" :
			"""
			The channel which controls the blend.  Clamped between 0 and 1.
			0 to take first input, 1 to take second input.
			""",
			"plugValueWidget:type" : "GafferImageUI.ChannelPlugValueWidget",
			"channelPlugValueWidget:imagePlugName" : "mask",

		},

	}

)
