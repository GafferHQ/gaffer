##########################################################################
#  
#  Copyright (c) 2011-2012, Image Engine Design Inc. All rights reserved.
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

## The VectorDataWidget provides a list view for IECore.StringVectorData,
# with additional features for editing the strings as paths
class PathVectorDataWidget( GafferUI.VectorDataWidget ) :

	def __init__( self, data=None, editable=True, header=False, showIndices=True, path=None, pathChooserDialogueKeywords={}, **kw ) :
	
		GafferUI.VectorDataWidget.__init__( self, data=data, editable=editable, header=header, showIndices=showIndices, **kw )
						
		self.__path = path if path is not None else Gaffer.FileSystemPath( "/" )
		self.__pathChooserDialogueKeywords = pathChooserDialogueKeywords
	
	def setData( self, data ) :
		
		if isinstance( data, list ) :
			assert( len( data ) == 1 )
			assert( isinstance( data[0], ( IECore.StringVectorData, type( None ) ) ) )
		else :
			assert( isinstance( data, ( IECore.StringVectorData, type( None ) ) ) )
		
		GafferUI.VectorDataWidget.setData( self, data )

	def _contextMenuDefinition( self, selectedIndices ) :
	
		m = GafferUI.VectorDataWidget._contextMenuDefinition( self, selectedIndices )
		
		if self.getEditable() and len( selectedIndices ) :
		
			m.prepend( "/PathDivider", { "divider" : True } )
			m.prepend( "/Choose path...", { "command" : IECore.curry( Gaffer.WeakMethod( self.__editPath ), selectedIndices[0] ) } )
			
		return m
	
	def _createRows( self ) :
	
		path = self.__path.copy()
		bookmarks = self.__pathChooserDialogueKeywords.get( "bookmarks", None )
		if bookmarks is not None :
			path.setFromString( bookmarks.getDefault() )
		
		dialogue = GafferUI.PathChooserDialogue( path, allowMultipleSelection=True, **self.__pathChooserDialogueKeywords )
		paths = dialogue.waitForPaths( parentWindow = self.ancestor( GafferUI.Window ) )
		if not paths :
			return None
			
		return [ IECore.StringVectorData( [ str( p ) for p in paths ] ) ]
		
	def __editPath( self, index ) :
		
		data = self.getData()[0]
		
		path = self.__path.copy()
		if index < len( data ) and len( data[index] ) :
			path.setFromString( data[index] )
		else :
			bookmarks = self.__pathChooserDialogueKeywords.get( "bookmarks", None )
			if bookmarks is not None :
				path.setFromString( bookmarks.getDefault() )
		
		dialogue = GafferUI.PathChooserDialogue( path, **self.__pathChooserDialogueKeywords )
		path = dialogue.waitForPath( parentWindow = self.ancestor( GafferUI.Window ) )
		
		if path is not None :
			
			if index < len( data ) :
				data[index] = str( path )
			else :
				data.append( str( path ) )
				
			self.dataChangedSignal()( self )
