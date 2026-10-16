##########################################################################
#
#  Copyright (c) 2026, Cinesite VFX Ltd. All rights reserved.
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

# Registers MCP Server tools that depend on GafferUI.

import Gaffer
import GafferUI

from Qt import QtCore
from Qt import QtGui

class CaptureEditorTool( Gaffer.MCP.BasicTool ) :

	def __init__( self ) :

		Gaffer.MCP.BasicTool.__init__(

			self,

			"captureEditor",

			"""
			Captures an image of an editor and returns it as a PNG.
			Doesn't modify the script.
			""",

			{
				"editor" :
				"""
				The type of editor to capture, as it appears to the user, such as `Viewer`, `GraphEditor`
				or `NodeEditor`..
				""",
				"maxSize" : "Maximum width or height of the returned image. Larger images are scaled down.",
			}

		)

	def _call( self, target, editor: str, maxSize: int = 1024 ) :

		scriptWindow = GafferUI.ScriptWindow.acquire( target.scriptNode(), createIfNecessary = False )
		if scriptWindow is None :
			return self.errorResult( "No UI connected to `target`" )

		editorType = self.__editorTypeFromString( editor )
		if editorType is None :
			return self.errorResult(
				"{} is not an editor type. Types are {}".format(
					editor, ", ".join( GafferUI.Editor.types() )
				)
			)

		editorWidget = scriptWindow.getLayout().editor( editorType )
		if editorWidget is None :
			return self.errorResult( f"There is no {editor}" )

		if not editorWidget.visible() :
			return self.errorResult( f"The {editor} is not visible" )

		# We use `QWidget.grab()` rather than `WidgetAlgo.grab()`, because the
		# latter grabs from the screen, and therefore can't grab widgets which
		# are obscured by other windows. And we grab the editor's region of the
		# window rather than the editor itself, so that we include the
		# backgrounds drawn by the editor's ancestors.
		qtWidget = editorWidget._qtWidget()
		window = qtWidget.window()
		image = window.grab( QtCore.QRect( qtWidget.mapTo( window, QtCore.QPoint( 0, 0 ) ), qtWidget.size() ) ).toImage()
		pngData, size = self.__qImageToPNG( image, maxSize )
		return self.imageResult(
			"Captured {} ({}x{}), returned at {}x{}".format( editor, image.width(), image.height(), size.width(), size.height() ),
			pngData
		)

	@staticmethod
	def __editorTypeFromString( typeName ) :

		def __walk( editorType ) :

			if editorType.__name__ == typeName :
				return editorType

			for childType in editorType.__subclasses__() :
				t = __walk( childType )
				if t is not None :
					return t

			return None

		return __walk( GafferUI.Editor )

	# Returns `( pngData, size )`, scaling the image down if necessary.
	@staticmethod
	def __qImageToPNG( image, maxSize ) :

		if max( image.width(), image.height() ) > maxSize :
			image = image.scaled(
				maxSize, maxSize,
				QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation
			)

		# We don't want any transparency, which clients might display
		# inconsistently.
		image = image.convertToFormat( QtGui.QImage.Format_RGB888 )

		buffer = QtCore.QBuffer()
		buffer.open( QtCore.QIODevice.WriteOnly )
		image.save( buffer, "PNG" )

		return bytes( buffer.data() ), image.size()

Gaffer.MCP.Tool.registerTool( CaptureEditorTool() )
