##########################################################################
#
#  Copyright (c) 2011-2012, Image Engine Design Inc. All rights reserved.
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
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

from .PlugValueWidget import sole
from .StringPlugValueWidget import addSubstitutionsPopup

import os

## Supported plug metadata - used to provide arguments to a
# PathChooserDialogue :
#
# - "path:leaf"
# - "path:valid"
# - "path:bookmarks"
class PathPlugValueWidget( GafferUI.PlugValueWidget ) :

	## path should be an instance of Gaffer.Path, optionally with
	# filters applied. It will be updated with the contents of the plug.
	#
	# \deprecated The pathChooserDialogueKeywords argument will be removed
	# in a future version - use metadata instead.
	def __init__( self, plug, path=None, pathChooserDialogueKeywords=None, **kw ) :

		self.__row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 )

		GafferUI.PlugValueWidget.__init__( self, self.__row, plug, **kw )

		self.__path = path if path is not None else Gaffer.FileSystemPath()

		self.__pathChooserDialogueKeywords = pathChooserDialogueKeywords

		with self.__row :

			pathWidget = GafferUI.PathWidget( self.__path )
			self._addPopupMenu( pathWidget )
			addSubstitutionsPopup( pathWidget )

			button = GafferUI.Button( image = "pathChooser.png", hasFrame=False )
			button.clickedSignal().connect( Gaffer.WeakMethod( self.__buttonClicked ) )

		pathWidget.editingFinishedSignal().connect( Gaffer.WeakMethod( self.__setPlugValue ) )

	def path( self ) :

		return self.__path

	## Returns the PathWidget used to display the path.
	def pathWidget( self ) :

		return self.__row[0]

	def setHighlighted( self, highlighted ) :

		GafferUI.PlugValueWidget.setHighlighted( self, highlighted )
		self.pathWidget().setHighlighted( highlighted )

	def getToolTip( self ) :

		result = GafferUI.PlugValueWidget.getToolTip( self )

		if result :
			result += "\n\n"

		result += "## Actions\n\n"
		result += "- <kbd>Tab</kbd> to autocomplete path component\n"
		result += "- Select path component (or hit <kbd>&darr;</kbd>) to show path-level contents menu\n"
		result += "- Select all to show path hierarchy menu\n"
		result += "- <kbd>Alt</kbd> + middle-click to show context variable substitutions\n"

		return result

	## May be reimplemented in derived classes to customise the
	# creation of the PathChooserDialogue. Implementations should
	# call the base class method and apply customisations to the
	# result, rather than construct their own dialogue directly.
	def _pathChooserDialogue( self ) :

		# make a copy so we're not updating the main path as users browse
		pathCopy = self.__path.copy()

		# get the keywords for the dialogue constructor
		# from the plug metadata.
		pathChooserDialogueKeywords = {}
		pathChooserDialogueKeywords["leaf"] = self.__metadataValue( "leaf" )
		pathChooserDialogueKeywords["valid"] = self.__metadataValue( "valid" )

		bookmarks = self.__metadataValue( "bookmarks" )
		if bookmarks is not None :
			pathChooserDialogueKeywords["bookmarks"] = GafferUI.Bookmarks.acquire( self.getPlug(), type( pathCopy ), bookmarks )

		# support deprecated keywords passed to our constructor
		if self.__pathChooserDialogueKeywords is not None :
			if callable( self.__pathChooserDialogueKeywords ) :
				pathChooserDialogueKeywords.update( self.__pathChooserDialogueKeywords() )
			else :
				pathChooserDialogueKeywords.update( self.__pathChooserDialogueKeywords )

		# choose a sensible starting location if the path is empty.
		if pathCopy.isEmpty() :
			bookmarks = pathChooserDialogueKeywords.get( "bookmarks", None )
			if bookmarks is not None :
				pathCopy.setFromString( bookmarks.getDefault() )
			elif isinstance( pathCopy, Gaffer.FileSystemPath ) :
				pathCopy.setFromString( os.path.expanduser( "~" ) )

		return GafferUI.PathChooserDialogue( pathCopy, **pathChooserDialogueKeywords )

	def _updateFromValues( self, values, exception ) :

		self.pathWidget().setErrored( exception is not None )
		self.__path.setFromString( sole( values ) or "" )

	def _updateFromEditable( self ) :

		self.pathWidget().setEditable( self._editable() )
		self.__row[1].setEnabled( self._editable() ) # button

	def _setPlugFromPath( self, path ) :

		self.getPlug().setValue( str( self.__path ) )

	def __setPlugValue( self, *args ) :

		if not self._editable() :
			return

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			self._setPlugFromPath( self.__path )

		# now we've transferred the text changes to the global undo queue, we remove them
		# from the widget's private text editing undo queue. it will then ignore undo shortcuts,
		# allowing them to fall through to the global undo shortcut.
		self.pathWidget().clearUndo()

	def __buttonClicked( self, widget ) :

		dialogue = self._pathChooserDialogue()
		chosenPath = dialogue.waitForPath( parentWindow = self.ancestor( GafferUI.Window ) )

		if chosenPath is not None :
			self.__path.setFromString( str( chosenPath ) )
			self.__setPlugValue()

	def __metadataValue( self, name ) :

		v = Gaffer.Metadata.value( self.getPlug(), "path:" + name )
		if v is None :
			# Fall back to old metadata names
			v = Gaffer.Metadata.value( self.getPlug(), "pathPlugValueWidget:" + name )

		return v
