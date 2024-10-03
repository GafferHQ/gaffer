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

import imath

import IECore

import Gaffer
import GafferUI

## The PathVectorDataWidget provides a list view for IECore.StringVectorData,
# with additional features for editing the strings as paths.
class PathVectorDataWidget( GafferUI.VectorDataWidget ) :

	## The pathChooserDialogueKeywords are passed to the PathChooserDialogue
	# that is opened when the user wishes to browse for a new path - they can
	# be specified to customise the path chooser appropriately. They may be
	# passed either as a dictionary, or as a callable which returns a dictionary -
	# in the latter case the callable will be evaluated just prior to opening
	# the dialogue each time.
	def __init__( self, data=None, editable=True, header=False, showIndices=True, path=None, pathChooserDialogueKeywords={}, **kw ) :

		GafferUI.VectorDataWidget.__init__( self, data=data, editable=editable, header=header, showIndices=showIndices, **kw )

		self.__path = path if path is not None else Gaffer.FileSystemPath( "/" )
		self.__pathChooserDialogueKeywords = pathChooserDialogueKeywords

		self.editSignal().connect( Gaffer.WeakMethod( self.__edit ) )

	def path( self ) :

		return self.__path

	def setData( self, data ) :

		if isinstance( data, list ) :
			assert( len( data ) == 1 )
			assert( isinstance( data[0], ( IECore.StringVectorData, type( None ) ) ) )
		else :
			assert( isinstance( data, ( IECore.StringVectorData, type( None ) ) ) )

		GafferUI.VectorDataWidget.setData( self, data )

	def _createRows( self ) :

		pathChooserDialogueKeywords = self._pathChooserDialogueKeywords()

		path = self.__path.copy()
		bookmarks = pathChooserDialogueKeywords.get( "bookmarks", None )
		if bookmarks is not None :
			path.setFromString( bookmarks.getDefault() )

		dialogue = GafferUI.PathChooserDialogue( path, allowMultipleSelection=True, **pathChooserDialogueKeywords )
		paths = dialogue.waitForPaths( parentWindow = self.ancestor( GafferUI.Window ) )
		if not paths :
			return None

		return [ IECore.StringVectorData( [ str( p ) for p in paths ] ) ]

	def _pathChooserDialogueKeywords( self ) :

		result = self.__pathChooserDialogueKeywords
		if callable( result ) :
			result = result()

		return result

	def __edit( self, vectorDataWidget, column, row ) :

		return _Editor( self.__path.copy() )

class _Editor( GafferUI.ListContainer ) :

	def __init__( self, path ) :

		GafferUI.ListContainer.__init__( self, orientation = GafferUI.ListContainer.Orientation.Horizontal, spacing = 2 )

		with self :
			GafferUI.PathWidget( path )
			button = GafferUI.Button( image = "pathChooser.png", hasFrame = False )
			button.clickedSignal().connect( Gaffer.WeakMethod( self.__buttonClicked ) )

			GafferUI.Spacer( imath.V2i( 2 ) )

		# needed to give the focus to our main editable field when editing starts.
		self._qtWidget().setFocusProxy( self.__pathWidget()._qtWidget() )

		self.__dialogue = None
		GafferUI.Widget.focusChangedSignal().connect( Gaffer.WeakMethod( self.__focusChanged ) )

	def setValue( self, value ) :

		self.__pathWidget().getPath().setFromString( value )

	def getValue( self ) :

		return str( self.__pathWidget().getPath() )

	def __pathWidget( self ) :

		return self[0]

	def __buttonClicked( self, button ) :

		parent = self.ancestor( PathVectorDataWidget )
		pathChooserDialogueKeywords = parent._pathChooserDialogueKeywords()

		path = self.__pathWidget().getPath().copy()
		if path.isEmpty() :
			bookmarks = pathChooserDialogueKeywords.get( "bookmarks", None )
			if bookmarks is not None :
				path.setFromString( bookmarks.getDefault() )

		self.__dialogue = GafferUI.PathChooserDialogue( path, **pathChooserDialogueKeywords )
		chosenPath = self.__dialogue.waitForPath( parentWindow = self.ancestor( GafferUI.Window ) )
		self.__dialogue = None

		if chosenPath is not None :
			self.__pathWidget().getPath().setFromString( str( chosenPath ) )

		# finish editing
		self.setVisible( False )

	def __focusChanged( self, oldWidget, newWidget ) :

		if not self.isAncestorOf( newWidget ) and self.__dialogue is None :
			# the focus has moved to another widget - finish editing.
			self.setVisible( False )
