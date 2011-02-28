##########################################################################
#  
#  Copyright (c) 2011, John Haddon. All rights reserved.
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

import gc
import types
import traceback

from PySide import QtGui

import IECore

import GafferUI

## \todo Implement an option to float in a new window, and an option to anchor back - drag and drop of tabs?
class CompoundEditor( GafferUI.EditorWidget ) :

	def __init__( self, scriptNode=None, children=None ) :
		
		GafferUI.EditorWidget.__init__( self, QtGui.QWidget(), scriptNode )
		
		self.__qtLayout = QtGui.QGridLayout()
		self.__qtLayout.setContentsMargins( 0, 0, 0, 0 )
		self._qtWidget().setLayout( self.__qtLayout )
		
		self.__splitContainer = GafferUI.SplitContainer()
		self.__qtLayout.addWidget( self.__splitContainer._qtWidget(), 0, 0 )
		self.__splitContainer.append( GafferUI.TabbedContainer() )
		
		self.__splitContainer._qtWidget().contextMenuEvent = types.MethodType( self.__contextMenuEvent, self.__splitContainer._qtWidget() )					

		if children :		
			self.__addChildren( self.__splitContainer, children )
			
	def setScriptNode( self, scriptNode ) :
	
		GafferUI.EditorWidget.setScriptNode( self, scriptNode )
	
		if not hasattr( self, "_CompoundEditor__splitContainer" ) :
			return
				
		def __set( w, scriptNode ) :
		
			if isinstance( w, GafferUI.EditorWidget ) :
				w.setScriptNode( scriptNode )
			else :
				for c in w :
					__set( c, scriptNode )
								
		__set( self.__splitContainer, scriptNode )
		
	def __repr__( self ) :
	
		def __serialise( w ) :
		
			assert( isinstance( w, GafferUI.SplitContainer ) )
		
			if len( w ) > 1 :
				# it's split
				return "( GafferUI.SplitContainer.Orientation.%s, ( %s, %s ) )" % ( str( w.getOrientation() ), __serialise( w[0] ), __serialise( w[1] ) )		
			else :
				# not split
				return repr( tuple( w[0][:] ) )
			
		return "GafferUI.CompoundEditor( children = %s )" % __serialise( self.__splitContainer )

	def __contextMenuEvent( self, qtWidget, event ) :
		
		splitContainer = GafferUI.Widget._owner( qtWidget )

		if len( splitContainer ) != 1 :
			# Can only do things at the leaf level
			return False

		m = IECore.MenuDefinition()

		for c in GafferUI.EditorWidget.types() :
			m.append( "/" + GafferUI.CamelCase.toSpaced( c ), { "command" : IECore.curry( self.__addChild, splitContainer, c ) } )

		m.append( "/divider", { "divider" : True } )

		removeItemAdded = False

		splitContainerParent = splitContainer.parent()
		if isinstance( splitContainerParent, GafferUI.SplitContainer ) :
			m.append( "Remove Panel", { "command" : IECore.curry( self.__join, splitContainerParent, 1 - splitContainerParent.index( splitContainer ) ) } )
			removeItemAdded = True

		tabbedContainer = splitContainer[0]
		if tabbedContainer :
			currentTab = tabbedContainer.getCurrent()
			if currentTab :
				m.append( "/Remove " + tabbedContainer.getLabel( currentTab ), { "command" : IECore.curry( self.__removeCurrentTab, tabbedContainer ) } )
				removeItemAdded = True

		if removeItemAdded :		
			m.append( "/divider2", { "divider" : True } )

		m.append( "/Split Left", { "command" : IECore.curry( self.__split, splitContainer, GafferUI.SplitContainer.Orientation.Horizontal, 0 ) } )
		m.append( "/Split Right", { "command" : IECore.curry( self.__split, splitContainer, GafferUI.SplitContainer.Orientation.Horizontal, 1 ) } )
		m.append( "/Split Bottom", { "command" : IECore.curry( self.__split, splitContainer, GafferUI.SplitContainer.Orientation.Vertical, 1 ) } )
		m.append( "/Split Top", { "command" : IECore.curry( self.__split, splitContainer, GafferUI.SplitContainer.Orientation.Vertical, 0 ) } )

		m = GafferUI.Menu( m )
		m.popup()
		
		return True

	def __addChildren( self, splitContainer, children ) :
		
		if len( children ) and isinstance( children[0], GafferUI.SplitContainer.Orientation ) :
		
			self.__split( splitContainer, children[0], 0 )
			self.__addChildren( splitContainer[0], children[1][0] )
			self.__addChildren( splitContainer[1], children[1][1] )

		else :
		
			for c in children :
				self.__addChild( splitContainer, c )		
			
	def __addChild( self, splitContainer, nameOrEditor ) :
	
		assert( len( splitContainer ) == 1 )
				
		tabbedContainer = splitContainer[0]
		
		if isinstance( nameOrEditor, basestring ) :
			editor = GafferUI.EditorWidget.create( nameOrEditor, self.getScriptNode() )
		else :
			editor = nameOrEditor
			editor.setScriptNode( self.getScriptNode() )
			
		tabbedContainer.append( editor )
		tabbedContainer.setLabel( editor, GafferUI.CamelCase.toSpaced( editor.__class__.__name__ ) )
		tabbedContainer.setCurrent( editor )
		
	def __split( self, splitContainer, orientation, subPanelIndex ) :
	
		assert( len( splitContainer ) == 1 ) # we should not be split already
		
		sc1 = GafferUI.SplitContainer()
		sc1.append( splitContainer[0] )
		sc1._qtWidget().contextMenuEvent = types.MethodType( self.__contextMenuEvent, sc1._qtWidget() )					

		assert( len( splitContainer ) == 0 )
		
		sc2 = GafferUI.SplitContainer()
		sc2.append( GafferUI.TabbedContainer() )
		sc2._qtWidget().contextMenuEvent = types.MethodType( self.__contextMenuEvent, sc2._qtWidget() )					
		
		if subPanelIndex==1 :
			splitContainer.append( sc1 )
			splitContainer.append( sc2 )
		else :
			splitContainer.append( sc2 )
			splitContainer.append( sc1 )
			
		assert( len( splitContainer ) == 2 )
		
		splitContainer.setOrientation( orientation )
		
	def __join( self, splitContainer, subPanelIndex ) :
	
		toKeep = splitContainer[subPanelIndex][0]
		del splitContainer[:]
		splitContainer.append( toKeep )
		
		# schedule some garbage collection to hoover up the remains. we do this in a delayed
		# way in case the menu we're called from is holding on to references to the ui elements
		# which are going to die.
		GafferUI.EventLoop.addIdleCallback( self.__collect )

	def __removeCurrentTab( self, tabbedContainer ) :
	
		currentTab = tabbedContainer.getCurrent()
		tabbedContainer.remove( currentTab )

		# schedule some garbage collection to hoover up the remains. we do this in a delayed
		# way in case the menu we're called from is holding on to references to the ui elements
		# which are going to die.
		GafferUI.EventLoop.addIdleCallback( self.__collect )

	@staticmethod
	def __collect() :
		
		try :
			while gc.collect() :
				pass
		except :
			pass
					
		return False
