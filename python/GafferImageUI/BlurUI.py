##########################################################################
#
#  Copyright (c) 2015, John Haddon. All rights reserved.
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

# Command suitable for use with `NodeMenu.append()`.
def nodeMenuCreateCommand( menu ) :

	blur = GafferImage.Blur()
	blur["radius"].gang()

	return blur

Gaffer.Metadata.registerNode(

	GafferImage.Blur,

	"description",
	"""
	Applies a gaussian blur to the image.
	""",

	plugs = {

		"radius" : {

			"description" :
			"""
			The size of the blur in pixels. This can be varied independently
			in the x and y directions, and fractional values are supported for
			fine control.
			""",

		},

		"boundingMode" : {

			"description" :
			"""
			The method used when the filter references pixels outside the
			input data window.
			""",

			"preset:Black" : GafferImage.Sampler.BoundingMode.Black,
			"preset:Clamp" : GafferImage.Sampler.BoundingMode.Clamp,

			"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",

		},

		"expandDataWindow" : {

			"description" :
			"""
			Expands the data window to include the external pixels
			which the blur will bleed onto.
			"""

		}

	}

)
