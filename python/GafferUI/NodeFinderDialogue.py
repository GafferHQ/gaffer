##########################################################################
#
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

import re
import fnmatch

import Gaffer
import GafferUI

class NodeFinderDialogue( GafferUI.Dialogue ) :

	def __init__( self, scope, **kw ) :

		GafferUI.Dialogue.__init__( self, "", sizeMode = self.SizeMode.Automatic, **kw )

		with GafferUI.GridContainer( spacing = 4 ) as grid :

			# criteria row

			GafferUI.Label(
				"Find",
				parenting = {
					"index" : ( 0, 0 ),
					"alignment" : ( GafferUI.HorizontalAlignment.Right, GafferUI.VerticalAlignment.Center ),
				}
			)

			self.__matchString = GafferUI.MultiSelectionMenu(
				allowMultipleSelection = False,
				allowEmptySelection = False,
				parenting = { "index" : ( 1, 0 ) }
			)

			# match text row

			GafferUI.Label(
				"Matching",
				parenting = {
					"index" : ( 0, 2 ),
					"alignment" : ( GafferUI.HorizontalAlignment.Right, GafferUI.VerticalAlignment.Center ),
				}
			)

			self.__matchPattern =  GafferUI.TextWidget( parenting = { "index" : ( 1, 2 ) } )
			self.__matchPattern.setToolTip( "Use * to match any text and ? to match any single character.\nDrag a node here to get the text for selecting similar nodes." )

			self.__matchPattern.dragEnterSignal().connect( Gaffer.WeakMethod( self.__dragEnter ) )
			self.__matchPattern.dragLeaveSignal().connect( Gaffer.WeakMethod( self.__dragLeave ) )
			self.__matchPattern.dropSignal().connect( Gaffer.WeakMethod( self.__drop ) )

		self._setWidget( grid )

		self.__cancelButton = self._addButton( "Cancel" )
		self.__selectNextButton = self._addButton( "Select Next" )
		self.__selectAllButton = self._addButton( "Select All" )

		self.__matchPattern.activatedSignal().connect( Gaffer.WeakMethod( self.__activated ) )

		self.__cancelButton.clickedSignal().connect( Gaffer.WeakMethod( self.__buttonClicked ) )
		self.__selectNextButton.clickedSignal().connect( Gaffer.WeakMethod( self.__buttonClicked ) )
		self.__selectAllButton.clickedSignal().connect( Gaffer.WeakMethod( self.__buttonClicked ) )

		self.visibilityChangedSignal().connect( Gaffer.WeakMethod( self.__visibilityChanged ) )

		self.__scope = None
		self.setScope( scope )

	def setScope( self, scope ) :

		if scope.isSame( self.__scope ) :
			return

		self.__scope = scope
		if isinstance( self.__scope, Gaffer.ScriptNode ) :
			self.setTitle( "Find nodes" )
		else :
			self.setTitle( "Find nodes in %s" % self.__scope.getName() )

	def getScope( self ) :

		return self.__scope

	__modes = []
	@classmethod
	def registerMode( cls, label, stringExtractor ) :

		cls.__modes.append( ( label, stringExtractor ) )

	def __visibilityChanged( self, widget ) :

		if self.visible() :

			# update modes in case more have been added
			self.__matchString[:] = [ m[0] for m in self.__modes ]
			self.__matchPattern.grabFocus()
			self.__matchPattern.setSelection( None, None ) # all text

	def __dragEnter( self, widget, event ) :

		if self.__nodeFromDragData( event.data ) is not None :
			widget.setHighlighted( True )
			return True

		return False

	def __dragLeave( self, widget, event ) :

		widget.setHighlighted( False )

	def __drop( self, widget, event ) :

		widget.setText( self.__matchStringExtractor()( self.__nodeFromDragData( event.data ) ) )
		widget.setSelection( None, None ) # all text
		widget.setHighlighted( False )

	def __nodeFromDragData( self, dragData ) :

		if isinstance( dragData, Gaffer.Node ) :
			return dragData
		elif isinstance( dragData, Gaffer.Set ) and len( dragData ) == 1 and isinstance( dragData[0], Gaffer.Node ) :
			return dragData[0]

		return None

	def __matchStringExtractor( self ) :

		for m in self.__modes :
			if m[0] == self.__matchString.getSelection()[0] :
				return m[1]

		assert( False )

	def __buttonClicked( self, button ) :

		if button is self.__cancelButton :
			self.setVisible( False )
		elif button is self.__selectAllButton :
			self.__selectAll()
		elif button is self.__selectNextButton :
			self.__selectNext()

	def __activated( self, text ) :

		self.__selectAll()

	def __selectAll( self ) :

		script = self.__scope.scriptNode() if not isinstance( self.__scope, Gaffer.ScriptNode ) else self.__scope
		selection = script.selection()

		extractor = self.__matchStringExtractor()
		regex = re.compile( fnmatch.translate( self.__matchPattern.getText() ) )

		newSelection = Gaffer.StandardSet()
		for node in self.__scope.children( Gaffer.Node ) :
			if regex.match( extractor( node ) ) :
				newSelection.add( node )

		if len( newSelection ) :
			selection.clear()
			selection.add( newSelection )
			self.__frameSelection()

	def __selectNext( self ) :

		script = self.__scope.scriptNode() if not isinstance( self.__scope, Gaffer.ScriptNode ) else self.__scope
		selection = script.selection()

		extractor = self.__matchStringExtractor()
		regex = re.compile( fnmatch.translate( self.__matchPattern.getText() ) )

		startIndex = 0
		if len( selection ) :
			lastSelectedNode = selection[-1]
			if self.__scope.isSame( lastSelectedNode.parent() ) :
				for i, c in enumerate( self.__scope.children() ) :
					if c.isSame( lastSelectedNode ) :
						startIndex = i + 1
						break

		for i in range( startIndex, startIndex + len( self.__scope ) ) :
			c = self.__scope[ i % len( self.__scope ) ]
			if isinstance( c, Gaffer.Node ) :
				if regex.match( extractor( c ) ) :
					selection.clear()
					selection.add( c )
					self.__frameSelection()
					break

	def __frameSelection( self ) :

		scriptWindow = self.ancestor( GafferUI.ScriptWindow )
		graphEditors = scriptWindow.getLayout().editors( GafferUI.GraphEditor )

		for graphEditor in graphEditors :
			if graphEditor.graphGadget().getRoot().isSame( self.__scope ) :
				graphEditor.frame( scriptWindow.scriptNode().selection() )

def __nodeNameExtractor( node ) :

	return node.getName()

def __nodeTypeExtractor( node ) :

	return node.typeName()

NodeFinderDialogue.registerMode( "Node Names", __nodeNameExtractor )
NodeFinderDialogue.registerMode( "Node Types", __nodeTypeExtractor )
