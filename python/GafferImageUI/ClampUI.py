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

	GafferImage.Clamp,

	"description",
	"""
	Clamps channel values so that they fit within a specified
	range. Clamping is performed for each channel individually,
	and out-of-range colours may be highlighted by setting them
	to a value different to the clamp threshold itself.
	""",

	plugs = {

		"min" : {

			"description" :
			"""
			The minimum value - values below this will
			be clamped if minEnabled is on.
			""",

		},

		"max" : {

			"description" :
			"""
			The maximum value - values above this will
			be clamped if maxEnabled is on.
			""",

		},

		"minClampTo" : {

			"description" :
			"""
			By default, values below the minimum value are
			clamped to the minimum value itself. If minClampToEnabled
			is on, they are instead set to this value. This can
			be useful for highlighting out-of-range values.
			""",

		},

		"maxClampTo" : {

			"description" :
			"""
			By default, values above the maximum value are
			clamped to the maximum value itself. If maxClampToEnabled
			is on, they are instead set to this value. This can
			be useful for highlighting out-of-range values.
			""",

		},

		"minEnabled" : {

			"description" :
			"""
			Turns on clamping for values below the min value.
			""",

		},

		"maxEnabled" : {

			"description" :
			"""
			Turns on clamping for values above the max value.
			""",

		},

		"minClampToEnabled" : {

			"description" :
			"""
			Turns on the effect of minClampTo, allowing out
			of range values to be highlighted.
			""",

		},

		"maxClampToEnabled" : {

			"description" :
			"""
			Turns on the effect of maxClampTo, allowing out
			of range values to be highlighted.
			""",

		},

	}

)
