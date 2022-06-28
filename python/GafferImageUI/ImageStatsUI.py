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
import GafferImageUI

## A function suitable as the postCreator in a NodeMenu.append() call. It
# sets the region of interest for the node to cover the entire format.
def postCreate( node, menu ) :

	with node.scriptNode().context() :
		if node["in"].getInput() :
			format = node["in"]["format"].getValue()
		else:
			format = GafferImage.FormatPlug.getDefaultFormat( node.scriptNode().context() )

	node["area"].setValue( format.getDisplayWindow() )

Gaffer.Metadata.registerNode(

	GafferImage.ImageStats,

	"description",
	"""
	Calculates minimum, maximum and average colours for a region of
	an image. These outputs can then be used to drive other plugs
	within the node graph.
	""",

	plugs = {

		"in" : [

			"description",
			"""
			The input image to be analysed.
			""",

		],

		"view" : [

			"description",
			"""
			The view to be analysed.
			""",

			"nodule:type", "",
			"plugValueWidget:type", "GafferImageUI.ViewPlugValueWidget",
			"viewPlugValueWidget:allowUseCurrentContext", True,

		],

		"channels" : [

			"description",
			"""
			The names of the four channels to be analysed.
			""",

			"nodule:type", "",
			"plugValueWidget:type", "GafferImageUI.RGBAChannelsPlugValueWidget",

		],

		"area" : [

			"description",
			"""
			The area of the image to be analysed.
			""",

			"nodule:type", "",

		],

		"average" : [

			"description",
			"""
			The per-channel mean values computed from the input image region.
			""",

		],

		"min" : [

			"description",
			"""
			The per-channel minimum values computed from the input image region.
			""",

		],

		"max" : [

			"description",
			"""
			The per-channel maximum values computed from the input image region.
			""",

		],

	}

)
