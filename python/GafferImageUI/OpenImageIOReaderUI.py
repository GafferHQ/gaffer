##########################################################################
#
#  Copyright (c) 2014-2015, Image Engine Design Inc. All rights reserved.
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
import GafferUI
import GafferImage

Gaffer.Metadata.registerNode(

	GafferImage.OpenImageIOReader,

	"description",
	"""
	Utility node which reads image files from disk using OpenImageIO.
	All file types supported by OpenImageIO are supported by the
	OpenImageIOReader.
	""",

	plugs = {

		"fileName" : [

			"description",
			"""
			The name of the file to be read. File sequences with
			arbitrary padding may be specified using the '#' character
			as a placeholder for the frame numbers. If this file sequence
			format is used, then missingFrameMode will be activated.
			""",

			"plugValueWidget:type", "GafferUI.FileSystemPathPlugValueWidget",
			"path:leaf", True,
			"path:bookmarks", "image",
			"fileSystemPath:extensions", " ".join( GafferImage.OpenImageIOReader.supportedExtensions() ),
			"fileSystemPath:extensionsLabel", "Show only image files",
			"fileSystemPath:includeSequences", True,

		],

		"refreshCount" : [

			"description",
			"""
			May be incremented to force a reload if the file has
			changed on disk - otherwise old contents may still
			be loaded via Gaffer's cache.
			""",

			"plugValueWidget:type", "GafferUI.RefreshPlugValueWidget",
			"layout:label", "",
			"layout:accessory", True,

		],

		"missingFrameMode" : [

			"description",
			"""
			Determines how missing frames are handled when the input
			fileName is a file sequence (uses the '#' character).
			The default behaviour is to throw an exception, but it
			can also hold the last valid frame in the sequence, or
			return a black image which matches the data window and
			display window of the previous valid frame in the sequence.
			""",

			"preset:Error", GafferImage.OpenImageIOReader.MissingFrameMode.Error,
			"preset:Black", GafferImage.OpenImageIOReader.MissingFrameMode.Black,
			"preset:Hold", GafferImage.OpenImageIOReader.MissingFrameMode.Hold,

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"availableFrames" : [

			"description",
			"""
			An output of the available frames for the given file sequence.
			Returns an empty vector when the input fileName is not a file
			sequence, even if it has a file-sequence-like structure.
			""",

			## \todo: consider making this visible using a TextWidget with
			## FrameList syntax (e.g. "1-100x5")
			"plugValueWidget:type", "",

		],

		"channelInterpretation" : [
			"description",
			"Documented in ImageReader, where it is exposed to users."
		],

		"fileValid" : [

			"description",
			"""
			Whether or not the files exists and can be read into memory,
			value calculated per frame if an image sequence.
			""",

			"plugValueWidget:type", "",

		]

	}

)
