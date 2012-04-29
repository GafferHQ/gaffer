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
		self.__row.append( pathWidget )
	
		button = GafferUI.Button( image = "pathChooser.png" )
		self.__buttonClickedConnection = button.clickedSignal().connect( Gaffer.WeakMethod( self.__buttonClicked ) )
		self.__row.append( button )
	
		self.__pathChangedConnection = self.__path.pathChangedSignal().connect( Gaffer.WeakMethod( self.__pathChanged ) )
	
		self._updateFromPlug()
	
	## Returns the PathWidget used to display the path.
	def pathWidget( self ) :
	
		return self.__row[0]
		
	def _updateFromPlug( self ) :

		if not hasattr( self, "_PathPlugValueWidget__path" ) :
			# still constructing
			return

		with self.getContext() :
			with IECore.IgnoredExceptions( ValueError ) :
				self.__path.setFromString( self.getPlug().getValue() )
		
	def __pathChanged( self, path ) :
				
		assert( path is self.__path )
		
		with Gaffer.UndoContext( self.getPlug().ancestor( Gaffer.ScriptNode.staticTypeId() ) ) :
			self.getPlug().setValue( str( self.__path ) )

	def __buttonClicked( self, widget ) :
	
		# make a copy so we're not updating the main path (and therefore plug) as users browse
		pathCopy = self.__path.copy()
		dialogue = GafferUI.PathChooserDialogue( pathCopy, **self.__pathChooserDialogueKeywords )
		chosenPath = dialogue.waitForPath( parentWindow = self.ancestor( GafferUI.Window ) )
		
		if chosenPath is not None :
			self.__path[:] = chosenPath[:]
