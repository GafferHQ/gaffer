##########################################################################
#
#  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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
import GafferArnold

Gaffer.Metadata.registerNode(

	GafferArnold.ArnoldCameraShaders,

	"description",
	"""
	Creates shaders for use with Arnold cameras. Use a ShaderAssignment
	node to assign the shaders to the cameras they should affect.
	""",

	plugs = {

		"name" : {

			"plugValueWidget:type" : "",

		},

		"filterMap" : {

			"description" :
			"""
			A shader used to weight the samples taken by an
			Arnold camera. This can be used to create vignetting effects
			or to completely mask out areas of the render, causing no
			rays to be fired for those pixels. The shader is evaluated
			across a 0-1 UV range that is mapped to the camera's screen
			space.
			""",

			"nodule:type" : "GafferUI::StandardNodule",
			"noduleLayout:section" : "left",

		},

		"uvRemap" : {

			"description" :
			"""
			A shader used to simulate lens distortion effects. The shader
			is evaluated across a 0-1 UV range that is mapped to the camera's
			screen space, and should output a red/green UV image of distorted
			UV positions.
			""",

			"nodule:type" : "GafferUI::StandardNodule",
			"noduleLayout:section" : "left",

		},

	}

)
