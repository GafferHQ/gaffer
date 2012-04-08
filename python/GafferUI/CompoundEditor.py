##########################################################################
#  
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
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

import gc
import types
import traceback

import IECore

import Gaffer
import GafferUI

QtCore = GafferUI._qtImport( "QtCore" )
QtGui = GafferUI._qtImport( "QtGui" )

## \todo Implement an option to float in a new window, and an option to anchor back - drag and drop of tabs?
class CompoundEditor( GafferUI.EditorWidget ) :

	__transitionDuration = 400

	def __init__( self, scriptNode=None, children=None, **kw ) :
		
		self.__splitContainer = GafferUI.SplitContainer()
		
		GafferUI.EditorWidget.__init__( self, self.__splitContainer, scriptNode, **kw )
		
		self.__splitContainer.append( GafferUI.TabbedContainer() )
		self.__addCornerWidget( self.__splitContainer )
		
		self.__buttonPressConnection = self.__splitContainer.buttonPressSignal().connect( Gaffer.WeakMethod( self.__buttonPress ) )
		self.__keyPressConnection = self.__splitContainer.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ) )

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
	
	## Returns all the editors that comprise this CompoundEditor, optionally
	# filtered by type.
	def editors( self, type = GafferUI.EditorWidget ) :
	
		result = []
		def __recurse( w ) :
			assert( isinstance( w, GafferUI.SplitContainer ) )
			if len( w ) > 1 :
				# it's split
				__recurse( w[0] )
				__recurse( w[1] )
			else :
				for e in w[0][:] :
					if isinstance( e, type ) :
						result.append( e )
				
		__recurse( self.__splitContainer )
		
		return result
		
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

	def __buttonPress( self, splitContainer, event ) :
		
		if event.buttons != event.Buttons.Right :
			return False

		if len( splitContainer ) != 1 :
			# Can only do things at the leaf level
			return False

		self.__popupLayoutMenu( splitContainer )
		return True
		
	def __popupLayoutMenu( self, splitContainer ) :
	
		m = IECore.MenuDefinition()

		for c in GafferUI.EditorWidget.types() :
			m.append( "/" + IECore.CamelCase.toSpaced( c ), { "command" : IECore.curry( self.__addChild, splitContainer, c ) } )

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
		
	def __keyPress( self, unused, event ) :
	
		if event.key == "Space" :
			
			# we receive the event for whichever SplitContainer has keyboard focus, but that's not
			# necessarily the one we want to modify. examine the splitter hierarchy and find
			# the target container we want to modify, and the new state we want to put it in.
			## \todo Decide how and where we provide this widget-under-the-cursor functionality in
			# the public api.
			qWidget = QtGui.QApplication.instance().widgetAt( QtGui.QCursor.pos() )
			widget = GafferUI.Widget._owner( qWidget )
						
			State = IECore.Enum.create( "None", "Open", "Closed", "Opening", "Closing" )
					
			targetContainer, targetState, targetIndex = None, State.None, -1
			prevContainer, prevState, prevIndex = None, State.None, -1
			while widget is not None :
				widgetParent = widget.parent()
				if isinstance( widgetParent, GafferUI.SplitContainer ) and hasattr( widgetParent, "_CompoundEditor__preferredHandlePosition" ) :
					currentContainer = widgetParent
					currentIndex = 1 - currentContainer.index( widget )
					currentDestSizes = currentContainer.targetSizes()
					if len( currentContainer ) == 1 :
						currentState = State.None
					elif 0 in currentContainer.getSizes() :
						currentState = State.Closed
					elif currentDestSizes is not None :
						if currentDestSizes[currentIndex] == 0 :
							currentState = State.Closing
						else :
							currentState = State.Opening
					else :
						currentState = State.Open

					if prevState in ( State.Closing, State.None ) and currentState in ( State.Open, State.Opening ) :
						targetContainer, targetState, targetIndex = currentContainer, State.Closing, currentIndex
						break
					if prevState == State.Closed and currentState in ( State.Open, State.Opening ) :
						targetContainer, targetState, targetIndex = prevContainer, State.Opening, prevIndex
						break
					elif currentState == State.Closed and currentContainer.parent() is self :
						targetContainer, targetState, targetIndex = currentContainer, State.Opening, currentIndex
						break

					prevContainer, prevState, prevIndex = currentContainer, currentState, currentIndex

				widget = widgetParent

			if targetContainer is None :
				return False

			if targetState == State.Closing :
				newSizes = [ 0, 1 ]
				if targetIndex :
					newSizes.reverse()
			else :
				newSizes = [ targetContainer.__preferredHandlePosition, 1 - targetContainer.__preferredHandlePosition ]

			targetContainer.setSizes( newSizes, self.__transitionDuration )
			for child in targetContainer :
				child.__enterConnection = None

			return True
			
		return False

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
		tabbedContainer.setLabel( editor, IECore.CamelCase.toSpaced( editor.__class__.__name__ ) )
		tabbedContainer.setCurrent( editor )
		
	def __split( self, splitContainer, orientation, subPanelIndex ) :
	
		assert( len( splitContainer ) == 1 ) # we should not be split already
		
		sc1 = GafferUI.SplitContainer()
		sc1.append( splitContainer[0] )
		sc1.__buttonPressConnection = sc1.buttonPressSignal().connect( Gaffer.WeakMethod( self.__buttonPress ) )					

		assert( len( splitContainer ) == 0 )
		
		sc2 = GafferUI.SplitContainer()
		sc2.append( GafferUI.TabbedContainer() )
		sc2.__buttonPressConnection = sc2.buttonPressSignal().connect( Gaffer.WeakMethod( self.__buttonPress ) )					
		self.__addCornerWidget( sc2 )
		
		if subPanelIndex==1 :
			splitContainer.append( sc1 )
			splitContainer.append( sc2 )
		else :
			splitContainer.append( sc2 )
			splitContainer.append( sc1 )
			
		assert( len( splitContainer ) == 2 )
		
		handle = splitContainer.handle( 0 )
		splitContainer.__handleEnterConnection = handle.enterSignal().connect( CompoundEditor.__handleEnter )
		splitContainer.__handleButtonReleaseConnection = handle.buttonReleaseSignal().connect( CompoundEditor.__handleButtonRelease )
		splitContainer.__preferredHandlePosition = 0.5 # where the user put it last
		
		splitContainer.setOrientation( orientation )
	
	def __addCornerWidget( self, splitContainer ) :
	
		assert( len( splitContainer ) == 1 )
		assert( isinstance( splitContainer[0], GafferUI.TabbedContainer ) )
		
		with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, borderWidth=1 ) as row :
		
			# node target button
			_TargetButton( splitContainer[0] ) 
		
			# layout button
			layoutButton = GafferUI.Button( image="layoutButton.png", hasFrame=False )
			layoutButton.setToolTip( "Click to modify the layout" )
			splitContainer.__layoutButtonClickedConnection = layoutButton.clickedSignal().connect( Gaffer.WeakMethod( self.__layoutButtonClicked ) )
		
		splitContainer[0].setCornerWidget( row )
				
	def __layoutButtonClicked( self, button ) :
	
		splitContainer = button.ancestor( type=GafferUI.SplitContainer )
		self.__popupLayoutMenu( splitContainer )
			
	def __join( self, splitContainer, subPanelIndex ) :
			
		# although subPanelToKeepFrom might seem to be a redundant variable,
		# it is not. it's essential that we keep a temporary reference to it
		# in addition to the toKeep variable we're actually interested in.
		# see below.
		subPanelToKeepFrom = splitContainer[subPanelIndex]	
		toKeep = subPanelToKeepFrom[0]
		
		# here we remove the entire contents of splitContainer. without the subPanelToKeepFrom
		# variable, there would be no python references to the splitContainer contents any more.
		# that would mean that the C++ QWidgets would be deleted (it appears that noone wants them).
		# that would mean that the C++ QWidget for toKeep would also be deleted (by the dying parent).
		# which would mean that we'd lose the C++ contents of toKeep, even though we need them.
		# by maintaining a reference to subPanelToKeepFrom, we keep the old parent alive long enough
		# to reparent toKeep properly - we may then let the old parent die peacefully.
		del splitContainer[:]
		splitContainer.append( toKeep )
		
		# schedule some garbage collection to hoover up the remains. we do this in a delayed
		# way in case the menu we're called from is holding on to references to the ui elements
		# which are going to die.
		## \todo I don't think this should be necessary now we're using WeakMethods for slots. It
		# may be a good idea to remove it, as it may otherwise mask problems temporarily.
		GafferUI.EventLoop.addIdleCallback( self.__collect )

	def __removeCurrentTab( self, tabbedContainer ) :
	
		currentTab = tabbedContainer.getCurrent()
		tabbedContainer.remove( currentTab )

		# schedule some garbage collection to hoover up the remains. we do this in a delayed
		# way in case the menu we're called from is holding on to references to the ui elements
		# which are going to die.
		GafferUI.EventLoop.addIdleCallback( self.__collect )

	@staticmethod
	def __handlePosition( splitContainer ) :
	
		assert( len( splitContainer ) == 2 )
		
		sizes = splitContainer.getSizes()
		return float( sizes[0] ) / sum( sizes )

	## Used to remember where people like the handle to be.
	@staticmethod
	def __handleButtonRelease( handle, event ) :
	
		splitContainer = handle.parent()
		handlePosition = CompoundEditor.__handlePosition( splitContainer )
		if handlePosition != 0 and handlePosition != 1 :
			splitContainer.__preferredHandlePosition = handlePosition
		for child in splitContainer :
			child.__enterConnection = None

		return False
		
	## Used to dynamically show collapsed editors when the handle is entered
	@staticmethod
	def __handleEnter( handle ) :
	
		splitContainer = handle.parent()
		sizes = splitContainer.getSizes()
		if 0 in sizes :
			preferredContainer = splitContainer[ 1 - sizes.index( 0 ) ]
			preferredContainer.__enterConnection = preferredContainer.enterSignal().connect( CompoundEditor.__preferredIndexEnter )
			sizes = [ splitContainer.__preferredHandlePosition, 1 - splitContainer.__preferredHandlePosition ]
			splitContainer.setSizes( sizes, CompoundEditor.__transitionDuration )
	
		return False
	
	## Used to dynamically hide editors automatically after being dynamically shown	
	@staticmethod
	def __preferredIndexEnter( splitContainer ) :
		
		parent = splitContainer.parent()
		index = parent.index( splitContainer )
		sizes = [ 1 if index==0 else 0, 0 if index==0 else 1 ]
		parent.setSizes( sizes, CompoundEditor.__transitionDuration )
		
		splitContainer.__enterConnection = None

	@staticmethod
	def __collect() :
		
		try :
			while gc.collect() :
				pass
		except :
			pass
					
		return False

# The class that implements the node target button used in the tabbed container corner widget
class _TargetButton( GafferUI.Button ) :

	def __init__( self, tabbedContainer ) :
	
		GafferUI.Button.__init__( self, image="targetNodesLocked.png", hasFrame=False )
		
		self.__currentTabChangedConnection = tabbedContainer.currentChangedSignal().connect( Gaffer.WeakMethod( self.__currentTabChanged ) )
		self.__clickedConnection = self.clickedSignal().connect( Gaffer.WeakMethod( self.__clicked ) )
	
		self.__update( tabbedContainer.getCurrent() )
	
	def __currentTabChanged( self, tabbedContainer, currentEditor ) :
		
		if isinstance( currentEditor, GafferUI.NodeSetEditor ) :
			self.__nodeSetChangedConnection = currentEditor.nodeSetChangedSignal().connect( Gaffer.WeakMethod( self.__update ) )
		else :
			self.__nodeSetChangedConnection = None
		
		self.__update( currentEditor )
		
	def __update( self, editor ) :
	
		if isinstance( editor, GafferUI.NodeSetEditor ) and editor.getScriptNode() is not None :
									 
			self.setVisible( True )
			
			if editor.getNodeSet().isSame( editor.getScriptNode().selection() ) :
				self.setToolTip( "Click to lock view to current selection" )
				self.setImage( "targetNodesUnlocked.png" )
			else :
				self.setToolTip( "Click to unlock view and follow selection" )
				self.setImage( "targetNodesLocked.png" )
		
		else :
		
			self.setVisible( False )
	
	def __clicked( self, button ) :
			
		splitContainer = self.ancestor( type=GafferUI.SplitContainer )
		assert( len( splitContainer ) == 1 )
		assert( isinstance( splitContainer[0], GafferUI.TabbedContainer ) )
		
		editor = splitContainer[0].getCurrent()
		assert( isinstance( editor, GafferUI.NodeSetEditor ) )
	
		nodeSet = editor.getNodeSet()
		selectionSet = editor.getScriptNode().selection()
		if nodeSet.isSame( selectionSet ) :
			nodeSet = Gaffer.StandardSet( list( nodeSet ) )
		else :
			nodeSet = selectionSet
		editor.setNodeSet( nodeSet )
	