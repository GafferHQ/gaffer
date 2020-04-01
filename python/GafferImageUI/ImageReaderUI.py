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
from . import OpenColorIOTransformUI

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

			"plugValueWidget:type", "GafferImageUI.ImageReaderUI._FrameMaskPlugValueWidget",

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

		],

		"start.frame" : [

			"description",
			"""
			The start frame of the masked range.
			""",

			"presetNames", lambda plug : IECore.StringVectorData( [ str(x) for x in plug.node()["__oiioReader"]["availableFrames"].getValue() ] ),
			"presetValues", lambda plug : plug.node()["__oiioReader"]["availableFrames"].getValue(),

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

			"plugValueWidget:type", "GafferImageUI.ImageReaderUI._FrameMaskPlugValueWidget",

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

		],

		"end.frame" : [

			"description",
			"""
			The end frame of the masked range.
			""",

			"presetNames", lambda plug : IECore.StringVectorData( [ str(x) for x in plug.node()["__oiioReader"]["availableFrames"].getValue() ] ),
			"presetValues", lambda plug : plug.node()["__oiioReader"]["availableFrames"].getValue(),

		],

		"colorSpace" : [

			"description",
			"""
			The colour space of the input image, used to convert the input image to
			the scene linear colorspace defined by the OpenColorIO config. The default
			behaviour is to automatically determine the colorspace by calling the function
			registered with `ImageReader::setDefaultColorSpaceFunction()`.
			""",

			"presetNames", OpenColorIOTransformUI.colorSpacePresetNames,
			"presetValues", OpenColorIOTransformUI.colorSpacePresetValues,

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

	}

)

class _FrameMaskPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing=4 ) as self.__row :

			GafferUI.PlugValueWidget.create( plug["mode"] )
			GafferUI.PlugValueWidget.create( plug["frame"] )

		GafferUI.PlugValueWidget.__init__( self, self.__row, plug, **kw )

	def setPlug( self, plug ) :

		assert( len( plug ) == len( self.getPlug() ) )

		GafferUI.PlugValueWidget.setPlug( self, plug )

		for index, plug in enumerate( plug.children() ) :
			self.__row[index].setPlug( plug )

	def setHighlighted( self, highlighted ) :

		GafferUI.PlugValueWidget.setHighlighted( self, highlighted )

		for i in range( 0, len( self.getPlug() ) ) :
			self.__row[i].setHighlighted( highlighted )

	def setReadOnly( self, readOnly ) :

		if readOnly == self.getReadOnly() :
			return

		GafferUI.PlugValueWidget.setReadOnly( self, readOnly )

		for w in self.__row :
			if isinstance( w, GafferUI.PlugValueWidget ) :
				w.setReadOnly( readOnly )

	def childPlugValueWidget( self, childPlug ) :

		for i, p in enumerate( self.getPlug().children() ) :
			if p.isSame( childPlug ) :
				return self.__row[i]

		return None

	def _updateFromPlug( self ) :

		with self.getContext() :
			mode = self.getPlug()["mode"].getValue()

		self.childPlugValueWidget( self.getPlug()["frame"] ).setEnabled( mode != GafferImage.ImageReader.FrameMaskMode.None_ )
