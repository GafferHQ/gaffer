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

def postCreateState( state ) :
	def postCreateFunc( node, menu ) :
		node["deepState"].setValue( state )

	return postCreateFunc

Gaffer.Metadata.registerNode(

	GafferImage.ImageState,

	"description",
	"""
	Modifies the samples in the input image to ensure
	that the resulting State includes the checked state flags.
	""",

	plugs = {

		"in" : [

			"description",
			"""
			The input image data.
			""",

		],

		"deepState" : [

			"description",
			"""
			The deep state to convert the image into.
			This will ensure that the resulting image is
			at least the specified state. If the input image
			has flags already set, they will remain set in
			the resulting image. So if an already Tidy image
			is passed in and requested that the output be
			Sorted, the result will be Tidy (as Tidy images
			are already Sorted by definition).
			""",

			"preset:Sorted", GafferImage.ImagePlug.DeepState.Sorted,
			"preset:Tidy", GafferImage.ImagePlug.DeepState.Tidy,
			"preset:Flat", GafferImage.ImagePlug.DeepState.Flat,

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

	}

)
