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

from __future__ import with_statement

import os

import IECore

import Gaffer
import GafferUI

class PathPlugValueWidget( GafferUI.PlugValueWidget ) :

	## path should be an instance of Gaffer.Path, optionally with
	# filters applied. It will be updated with the contents of the plug.
	def __init__( self, plug, path=None, pathChooserDialogueKeywords={}, **kw ) :
	
		self.__row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 )
			
		GafferUI.PlugValueWidget.__init__( self, self.__row, plug, **kw )

		self.__path = path if path is not None else Gaffer.FileSystemPath( "/" )
		self.__pathChooserDialogueKeywords = pathChooserDialogueKeywords

		pathWidget = GafferUI.PathWidget( self.__path )
		self._addPopupMenu( pathWidget )
		self.__row.append( pathWidget )
	
		button = GafferUI.Button( image = "pathChooser.png", hasFrame=False )
		self.__buttonClickedConnection = button.clickedSignal().connect( Gaffer.WeakMethod( self.__buttonClicked ) )
		self.__row.append( button )
	
		self.__editingFinishedConnection = pathWidget.editingFinishedSignal().connect( Gaffer.WeakMethod( self.__setPlugValue ) )
	
		self._updateFromPlug()
	
	## Returns the PathWidget used to display the path.
	def pathWidget( self ) :
	
		return self.__row[0]
	
	def getToolTip( self ) :
	
		result = GafferUI.PlugValueWidget.getToolTip( self )
		
		result += "<ul>"
		result += "<li>Tab to auto-complete</li>"
		result += "<li>Cursor down to list</li>"
		result += "<ul>"

		return result
	
	def _updateFromPlug( self ) :

		with self.getContext() :
			with IECore.IgnoredExceptions( ValueError ) :
				self.__path.setFromString( self.getPlug().getValue() )

		self.pathWidget().setEditable( self._editable() )
		self.__row[1].setEnabled( self._editable() ) # button
		
	def __setPlugValue( self, *args ) :
		
		if not self._editable() :
			return
								
		with Gaffer.UndoContext( self.getPlug().ancestor( Gaffer.ScriptNode.staticTypeId() ) ) :
			self.getPlug().setValue( str( self.__path ) )

	def __buttonClicked( self, widget ) :
	
		# make a copy so we're not updating the main path as users browse
		pathCopy = self.__path.copy()
		## \todo Currently we can't distinguish between "/" and an empty path. There are a lot
		# more occurrences of empty paths (parameter default values) than there are "/" root paths,
		# so start browsing from the current directory rather than the root if the path is "/".
		# We should update the path class to have the concept of empty paths and relative paths
		# and remove this code.
		if isinstance( pathCopy, ( Gaffer.SequencePath, Gaffer.FileSystemPath ) ) and len( pathCopy ) == 0 :
			pathCopy.setFromString( os.getcwd() )
		
		dialogue = GafferUI.PathChooserDialogue( pathCopy, **self.__pathChooserDialogueKeywords )
		chosenPath = dialogue.waitForPath( parentWindow = self.ancestor( GafferUI.Window ) )
		
		if chosenPath is not None :
			self.__path[:] = chosenPath[:]
			self.__setPlugValue()
