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

from GafferUI.PlugValueWidget import sole

from . import OpenColorIOTransformUI

from GafferUI.PlugValueWidget import sole

Gaffer.Metadata.registerNode(

	GafferImage.ImageReader,

	"description",
	"""
	Reads image files from disk using OpenImageIO. All file
	types supported by OpenImageIO are supported by the ImageReader
	and all channel data will be converted to linear using OpenColorIO.
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
			"fileSystemPath:extensions", " ".join( GafferImage.ImageReader.supportedExtensions() ),
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

			"preset:Error", GafferImage.ImageReader.MissingFrameMode.Error,
			"preset:Black", GafferImage.ImageReader.MissingFrameMode.Black,
			"preset:Hold", GafferImage.ImageReader.MissingFrameMode.Hold,

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"start" : [

			"description",
			"""
			Masks frames which preceed the specified start frame.
			The default is to treat them based on the MissingFrameMode,
			but they can also be clamped to the start frame, or
			return a black image which matches the data window
			and display window of the start frame.
			""",

			"plugValueWidget:type", "GafferUI.LayoutPlugValueWidget",
			"layoutPlugValueWidget:orientation", "horizontal",

			"layout:activator:modeIsNotNone", lambda plug : plug["mode"].getValue() != GafferImage.ImageReader.FrameMaskMode.None_,

		],

		"start.mode" : [

			"description",
			"""
			The mode used detemine the mask behaviour for the start frame.
			""",

			"preset:None", GafferImage.ImageReader.FrameMaskMode.None_,
			"preset:Black Outside", GafferImage.ImageReader.FrameMaskMode.BlackOutside,
			"preset:Clamp to Range", GafferImage.ImageReader.FrameMaskMode.ClampToFrame,

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
			"layout:label", "",

		],

		"start.frame" : [

			"description",
			"""
			The start frame of the masked range.
			""",

			"presetNames", lambda plug : IECore.StringVectorData( [ str(x) for x in plug.node()["__oiioReader"]["availableFrames"].getValue() ] ),
			"presetValues", lambda plug : plug.node()["__oiioReader"]["availableFrames"].getValue(),

			"layout:label", "",
			"layout:activator", "modeIsNotNone",

		],

		"end" : [

			"description",
			"""
			Masks frames which follow the specified end frame.
			The default is to treat them based on the MissingFrameMode,
			but they can also be clamped to the end frame, or
			return a black image which matches the data window
			and display window of the end frame.
			""",

			"plugValueWidget:type", "GafferUI.LayoutPlugValueWidget",
			"layoutPlugValueWidget:orientation", "horizontal",

			"layout:activator:modeIsNotNone", lambda plug : plug["mode"].getValue() != GafferImage.ImageReader.FrameMaskMode.None_,

		],

		"end.mode" : [

			"description",
			"""
			The mode used detemine the mask behaviour for the end frame.
			""",

			"preset:None", GafferImage.ImageReader.FrameMaskMode.None_,
			"preset:Black Outside", GafferImage.ImageReader.FrameMaskMode.BlackOutside,
			"preset:Clamp to Range", GafferImage.ImageReader.FrameMaskMode.ClampToFrame,

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
			"layout:label", "",

		],

		"end.frame" : [

			"description",
			"""
			The end frame of the masked range.
			""",

			"presetNames", lambda plug : IECore.StringVectorData( [ str(x) for x in plug.node()["__oiioReader"]["availableFrames"].getValue() ] ),
			"presetValues", lambda plug : plug.node()["__oiioReader"]["availableFrames"].getValue(),

			"layout:label", "",
			"layout:activator", "modeIsNotNone",

		],

		"colorSpace" : [

			"description",
			"""
			The colour space of the input image, used to convert the input to
			the working space. When set to `Automatic`, the colour space is
			determined automatically using the function registered with
			`ImageReader::setDefaultColorSpaceFunction()`.
			""",

			"presetNames", OpenColorIOTransformUI.colorSpacePresetNames,
			"presetValues", OpenColorIOTransformUI.colorSpacePresetValues,
			"openColorIO:categories", "file-io",
			"openColorIO:extraPresetNames", IECore.StringVectorData( [ "Automatic" ] ),
			"openColorIO:extraPresetValues", IECore.StringVectorData( [ "" ] ),

			"plugValueWidget:type", "GafferImageUI.ImageReaderUI._ColorSpacePlugValueWidget",

		],

		"channelInterpretation" : [

			"description",
			"""
			Controls how we create channels based on the contents of the file.  Unfortunately,
			some software, such as Nuke, does not produce EXR files which follow the EXR specification,
			so the mode "Default" uses heuristics to guess what the channels mean.

			"Default" mode should support most files coming from either Nuke or standards compliant software.
			It can't handle every possibility in the spec though - in corner cases, it could get confused and
			think something comes from Nuke, and incorrectly prepend the part name to the channel name.

			If you know your EXR is compliant, you can "EXR Specification" mode which disables the heuristics,
			and just uses the channel names directly from the file.

			"Legacy" mode matches Gaffer <= 0.61 behaviour for compatibility reasons - it should not be used.
			""",

			"preset:Legacy", GafferImage.ImageReader.ChannelInterpretation.Legacy,
			"preset:Default", GafferImage.ImageReader.ChannelInterpretation.Default,
			"preset:EXR Specification", GafferImage.ImageReader.ChannelInterpretation.Specification,

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"availableFrames" : [

			"description",
			"""
			A list of the available frames for the current file sequence.
			Empty when the input `fileName` is not a file sequence.
			""",

			"layout:section", "Frames",
			"plugValueWidget:type", "GafferImageUI.ImageReaderUI._AvailableFramesPlugValueWidget",

		],

		"fileValid" : [
			"description",
			"""
			Whether or not the files exists and can be read into memory,
			value calculated per frame if an image sequence.
			""",

			"layout:section", "Frames",

		]

	}

)

# Augments PresetsPlugValueWidget label with the computed colour space
# when preset is "Automatic". Since this involves opening the file to
# read metadata, we do the work in the background via an auxiliary plug
# passed to `_valuesForUpdate()`.
class _ColorSpacePlugValueWidget( GafferUI.PresetsPlugValueWidget ) :

	def __init__( self, plugs, **kw ) :

		GafferUI.PresetsPlugValueWidget.__init__( self, plugs, **kw )

	@staticmethod
	def _valuesForUpdate( plugs, auxiliaryPlugs ) :

		presets = GafferUI.PresetsPlugValueWidget._valuesForUpdate( plugs, [ [] for p in plugs ] )

		result = []
		for preset, colorSpacePlugs in zip( presets, auxiliaryPlugs ) :

			automaticSpace = ""
			if len( colorSpacePlugs ) and preset == "Automatic" :
				with IECore.IgnoredExceptions( Gaffer.ProcessException ) :
					automaticSpace = colorSpacePlugs[0].getValue() or "Working Space"

			result.append( {
				"preset" : preset,
				"automaticSpace" : automaticSpace
			} )

		return result

	def _updateFromValues( self, values, exception ) :

		GafferUI.PresetsPlugValueWidget._updateFromValues( self, [ v["preset"] for v in values ], exception )

		if self.menuButton().getText() == "Automatic" :
			automaticSpace = sole( v["automaticSpace"] for v in values )
			if automaticSpace != "" :
				self.menuButton().setText( "Automatic ({})".format( automaticSpace or "---" ) )

	def _auxiliaryPlugs( self, plug ) :

		node = plug.node()
		if isinstance( node, GafferImage.ImageReader ) :
			return [ node["__intermediateColorSpace"] ]

class _AvailableFramesPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		self.__textWidget = GafferUI.TextWidget( editable = False )
		GafferUI.PlugValueWidget.__init__( self, self.__textWidget, plug, **kw )

	def _updateFromValues( self, values, exception ) :

		value = sole( values )
		if value is None :
			self.__textWidget.setText( "---" )
		else :
			self.__textWidget.setText( str( IECore.frameListFromList( list( value ) ) ) )

		self.__textWidget.setErrored( exception is not None )
