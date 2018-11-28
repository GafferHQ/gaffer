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

import IECore

import Gaffer
import GafferImage

## A function suitable as the postCreator in a NodeMenu.append() call. It
# sets the region of interest for the node to cover the entire format.
def postCreate( node, menu ) :

	with node.scriptNode().context() :
		if node["in"].getInput() :
			format = node["in"]["format"].getValue()
		else:
			format = GafferImage.FormatPlug.getDefaultFormat( node.scriptNode().context() )

	node['area'].setValue( format.getDisplayWindow() )

Gaffer.Metadata.registerNode(

	GafferImage.Text,

	"description",
	"""
	Renders text over an input image.
	""",

	plugs = {

		"color" : [

			"description",
			"""
			The colour of the text.
			""",

		],

		"text" : [

			"description",
			"""
			The text to be rendered.
			""",

			"plugValueWidget:type", "GafferUI.MultiLineStringPlugValueWidget",
			"multiLineStringPlugValueWidget:continuousUpdate", True,

		],

		"font" : [

			"description",
			"""
			The font to render the text with. This should be a .ttf font file which
			is located on the paths specified by the IECORE_FONT_PATHS
			environment variable.
			""",

			"path:bookmarks", "font",
			"path:leaf", True,
			"path:valid", True,
			"fileSystemPath:extensions", "ttf",

		],

		"size" : [

			"description",
			"""
			The size of the font in pixels. For best quality results
			for constant sized text prefer this over the scale setting
			on the transform, which is better suited for smoothly animating
			the size.
			""",

		],

		"area" : [

			"description",
			"""
			The area of the image within which the text is rendered.
			The text will be word wrapped to fit within the area and
			justified as specified by the justification setting. If the
			area is empty, then the full display window will be used
			instead.
			""",

		],

		"horizontalAlignment" : [

			"description",
			"""
			Determines whether the text is aligned to the left or
			right of the text area, or centered within it.
			""",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

			"preset:Left", GafferImage.Text.HorizontalAlignment.Left,
			"preset:Right", GafferImage.Text.HorizontalAlignment.Right,
			"preset:Center", GafferImage.Text.HorizontalAlignment.Center,

		],

		"verticalAlignment" : [

			"description",
			"""
			Determines whether the text is aligned to the bottom or
			top of the text area, or centered within it.
			""",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

			"preset:Bottom", GafferImage.Text.VerticalAlignment.Bottom,
			"preset:Top", GafferImage.Text.VerticalAlignment.Top,
			"preset:Center", GafferImage.Text.VerticalAlignment.Center,

		],

		"transform" : [

			"description",
			"""
			A transformation applied to the entire text area after
			layout has been performed. The translate and pivot values
			are specified in pixels, and the rotate value is specified
			in degrees.
			""",

			"plugValueWidget:type", "GafferUI.LayoutPlugValueWidget",
			"layout:section", "Transform",

		],

	}

)
