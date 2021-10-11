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
import GafferScene
import GafferSceneUI

def filmFitMetadata():
	# Take the metadata from StandardOptionsUI, except not the layout section
	allOptions = GafferSceneUI.StandardOptionsUI.plugsMetadata[ "options.filmFit" ] + GafferSceneUI.StandardOptionsUI.plugsMetadata[ "options.filmFit.value" ]
	optionPairs = zip( allOptions[::2], allOptions[1::2] )
	return sum( [ [i,j] for i,j in optionPairs if i != "layout:section" ], [] )

Gaffer.Metadata.registerNode(

	GafferScene.LightToCamera,

	"description",
	"""
	Converts lights into cameras. Spotlights are converted to a perspective
	camera with the field of view matching the cone angle, and distant lights are
	converted to an orthographic camera.
	""",

	plugs = {

		"filmFit" : filmFitMetadata(),

		"distantAperture" : [

			"description",
			"""
			The orthographic aperture used when converting distant lights
			( which are theoretically infinite in extent )
			""",

		],

		"clippingPlanes" : [

			"description",
			"""
			Clipping planes for the created cameras.  When creating a perspective camera, a near clip
			<= 0 is invalid, and will be replaced with 0.01.  Also, certain lights only start casting
			light at some distance - if near clip is less than this, it will be increased.
			""",

		],

		"filter" : [

			"description",
			"""
			Specifies which lights to convert.
			""",

		],
	}

)
