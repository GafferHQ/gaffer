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

	GafferImage.Grade,

	"description",
	"""
	Performs a simple per-channel colour grading operation
	as follows :

	A = multiply * (gain - lift) / (whitePoint - blackPoint)
	B = offset + lift - A * blackPoint
	result = pow( A * input + B, 1/gamma )

	See the descriptions for individual plug for a slightly
	more practical explanation of the formula.
	""",

	plugs = {

		"blackPoint" : {

			"description" :
			"""
			The input colour which is considered to be
			"black". This colour is remapped to the
			lift value in the output image.
			""",

		},

		"whitePoint" : {

			"description" :
			"""
			The input colour which is considered to be
			"white". This colour is remapped to the
			gain value in the output image.
			""",

		},

		"lift" : {

			"description" :
			"""
			The colour that input pixels at the blackPoint
			become in the output image. This can be thought
			of as lifting the darker values of the image.
			""",

		},

		"gain" : {

			"description" :
			"""
			The colour that input pixels at the whitePoint
			become in the output image. This can be thought
			of as defining the lighter values of the image.
			""",

		},

		"multiply" : {

			"description" :
			"""
			An additional multiplier on the output values.
			""",

		},

		"offset" : {

			"description" :
			"""
			An additional offset added to the output values.
			""",

		},

		"gamma" : {

			"description" :
			"""
			A gamma correction applied after all the remapping
			defined above.
			""",

		},

		"blackClamp" : {

			"description" :
			"""
			Clamps input values so they don't go below 0.
			""",

		},

		"whiteClamp" : {

			"description" :
			"""
			Clamps output values so they don't go above 1.
			""",

		},

	}

)
