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

import fnmatch

import Gaffer
import GafferUI
import GafferImageUI
import GafferImage

Gaffer.Metadata.registerNode(

	GafferImage.ImageWriter,

	"description",
	"""
	Writes image files to disk using OpenImageIO. All file
	types supported by OpenImageUI are supported by the
	ImageWriter.
	""",

	plugs = {

		"in" : [

			"description",
			"""
			The image to be written to disk.
			""",

		],

		"fileName" : [

			"description",
			"""
			The name of the file to be written. File sequences with
			arbitrary padding may be specified using the '#' character
			as a placeholder for the frame numbers.
			""",

			"nodule:type", "",

		],

		"writeMode" : [

			"description",
			"""
			Whether the image is written using tiles or scanlines.
			Not all file formats support both modes - in the case
			of the specified mode being unsupported, a fallback mode
			is chosen automatically.
			""",

			# \todo Bind the enum and don't hardcode values.
			"preset:Scanline", 0,
			"preset:Tile", 1,

			"nodule:type", "",

		],

		"channels" : [

			"description",
			"""
			The channels to be written to the file.
			""",

			"nodule:type", "",

		],

		"out" : [

			"description",
			"""
			A pass-through of the input image.
			""",

			"nodule:type", "",

		]

	}

)

GafferUI.PlugValueWidget.registerCreator(
	GafferImage.ImageWriter,
	"fileName",
	lambda plug : GafferUI.PathPlugValueWidget( plug,
		path = Gaffer.FileSystemPath(
			"/",
			filter = Gaffer.FileSystemPath.createStandardFilter(
				extensions = GafferImage.ImageReader.supportedExtensions(),
				extensionsLabel = "Show only image files",
			)
		),
		pathChooserDialogueKeywords = {
			"bookmarks" : GafferUI.Bookmarks.acquire( plug, category = "image" ),
			"leaf" : True,
		},
	)
)

GafferUI.PlugValueWidget.registerCreator( GafferImage.ImageWriter, "channels", GafferImageUI.ChannelMaskPlugValueWidget, inputImagePlug = "in" )
GafferUI.PlugValueWidget.registerCreator( GafferImage.ImageWriter, "writeMode", GafferUI.PresetsPlugValueWidget )
