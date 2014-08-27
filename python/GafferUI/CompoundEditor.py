##########################################################################
#
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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

	def __init__( self, scriptNode, children=None, **kw ) :

		self.__splitContainer = _SplitContainer()

		GafferUI.EditorWidget.__init__( self, self.__splitContainer, scriptNode, **kw )

		self.__splitContainer.append( _TabbedContainer() )

		self.__keyPressConnection = self.__splitContainer.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ) )

		self.__editorAddedSignal = Gaffer.Signal2()

		if children :
			self.__addChildren( self.__splitContainer, children )

	## Returns all the editors that comprise this CompoundEditor, optionally
	# filtered by type.
	def editors( self, type = GafferUI.EditorWidget ) :

		def __recurse( w ) :
			assert( isinstance( w, GafferUI.SplitContainer ) )
			if len( w ) > 1 :
				# it's split
				return __recurse( w[0] ) + __recurse( w[1] )
			else :
				return [ e for e in w[0] if isinstance( e, type ) ]

		return __recurse( self.__splitContainer )

	## Adds an editor to the layout, trying to place it in the same place
	# as editors of the same type.
	def addEditor( self, editor ) :

		def __findContainer( w, editorType ) :
			if len( w ) > 1 :
				ideal, backup = __findContainer( w[0], editorType )
				if ideal is not None :
					return ideal, backup
				return __findContainer( w[1], editorType )
			else :
				for e in w[0] :
					if isinstance( e, editorType ) :
						return w, w
				return None, w

		ideal, backup = __findContainer( self.__splitContainer, editor.__class__ )
		container = ideal if ideal is not None else backup

		self.__addChild( container, editor )

	## A signal emitted whenever an editor is added -
	# the signature is ( compoundEditor, childEditor ).
	def editorAddedSignal( self ) :

		return self.__editorAddedSignal

	def __repr__( self ) :

		def __serialise( w ) :

			assert( isinstance( w, GafferUI.SplitContainer ) )

			if len( w ) > 1 :
				# it's split
				sizes = w.getSizes()
				splitPosition = ( float( sizes[0] ) / sum( sizes ) ) if sum( sizes ) else 0
				return "( GafferUI.SplitContainer.Orientation.%s, %f, ( %s, %s ) )" % ( str( w.getOrientation() ), splitPosition, __serialise( w[0] ), __serialise( w[1] ) )
			else :
				# not split - a tabbed container full of editors
				tabbedContainer = w[0]
				tabDict = { "tabs" : tuple( tabbedContainer[:] ) }
				if tabbedContainer.getCurrent() is not None :
					tabDict["currentTab"] = tabbedContainer.index( tabbedContainer.getCurrent() )
				tabDict["tabsVisible"] = tabbedContainer.getTabsVisible()

				tabDict["pinned"] = []
				for editor in tabbedContainer :
					if isinstance( editor, GafferUI.NodeSetEditor ) :
						tabDict["pinned"].append( not editor.getNodeSet().isSame( self.scriptNode().selection() ) )
					else :
						tabDict["pinned"].append( None )

				return repr( tabDict )

		return "GafferUI.CompoundEditor( scriptNode, children = %s )" % __serialise( self.__splitContainer )

	def _layoutMenuDefinition( self, tabbedContainer ) :

		splitContainer = tabbedContainer.ancestor( _SplitContainer )

		m = IECore.MenuDefinition()

		layouts = GafferUI.Layouts.acquire( self.scriptNode().applicationRoot() )
		for c in layouts.registeredEditors() :
			m.append( "/" + IECore.CamelCase.toSpaced( c ), { "command" : IECore.curry( self.__addChild, splitContainer, c ) } )

		m.append( "/divider", { "divider" : True } )

		removeItemAdded = False

		splitContainerParent = splitContainer.parent()
		if isinstance( splitContainerParent, GafferUI.SplitContainer ) :
			m.append( "Remove Panel", { "command" : IECore.curry( self.__join, splitContainerParent, 1 - splitContainerParent.index( splitContainer ) ) } )
			removeItemAdded = True

		currentTab = tabbedContainer.getCurrent()
		if currentTab :
			m.append( "/Remove " + tabbedContainer.getLabel( currentTab ), { "command" : IECore.curry( self.__removeCurrentTab, tabbedContainer ) } )
			removeItemAdded = True

		if removeItemAdded :
			m.append( "/divider2", { "divider" : True } )

		tabsVisible = tabbedContainer.getTabsVisible()
		# because the menu isn't visible most of the time, the Ctrl+T shortcut doesn't work - it's just there to let
		# users know it exists. it is actually implemented directly in __keyPress.
		m.append( "/Hide Tabs" if tabsVisible else "/Show Tabs", { "command" : IECore.curry( Gaffer.WeakMethod( tabbedContainer.setTabsVisible ), not tabsVisible ), "shortCut" : "Ctrl+T" } )
		m.append( "/TabsDivider", { "divider" : True } )

		m.append( "/Split Left", { "command" : IECore.curry( self.__split, splitContainer, GafferUI.SplitContainer.Orientation.Horizontal, 0 ) } )
		m.append( "/Split Right", { "command" : IECore.curry( self.__split, splitContainer, GafferUI.SplitContainer.Orientation.Horizontal, 1 ) } )
		m.append( "/Split Bottom", { "command" : IECore.curry( self.__split, splitContainer, GafferUI.SplitContainer.Orientation.Vertical, 1 ) } )
		m.append( "/Split Top", { "command" : IECore.curry( self.__split, splitContainer, GafferUI.SplitContainer.Orientation.Vertical, 0 ) } )

		return m

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

		elif event.key == "T" and event.modifiers == event.Modifiers.Control :

			tabbedContainer = GafferUI.Widget.widgetAt( GafferUI.Widget.mousePosition(), _TabbedContainer )
			if tabbedContainer is not None :
				tabbedContainer.setTabsVisible( not tabbedContainer.getTabsVisible() )

		return False

	def __addChildren( self, splitContainer, children ) :

		if isinstance( children, tuple ) and len( children ) and isinstance( children[0], GafferUI.SplitContainer.Orientation ) :

			self.__split( splitContainer, children[0], 0 )
			self.__addChildren( splitContainer[0], children[2][0] )
			self.__addChildren( splitContainer[1], children[2][1] )
			splitContainer.setSizes( [ children[1], 1.0 - children[1] ] )

		else :
			if isinstance( children, tuple ) :
				# backwards compatibility - tabs provided as a tuple
				for c in children :
					self.__addChild( splitContainer, c )
			else :
				# new format - various fields provided by a dictionary
				for i, c in enumerate( children["tabs"] ) :
					editor = self.__addChild( splitContainer, c )
					if "pinned" in children and isinstance( editor, GafferUI.NodeSetEditor ) and children["pinned"][i] :
						editor.setNodeSet( Gaffer.StandardSet() )

				if "currentTab" in children :
					splitContainer[0].setCurrent( splitContainer[0][children["currentTab"]] )

				splitContainer[0].setTabsVisible( children.get( "tabsVisible", True ) )

				# this is a shame-faced hack to make sure the timeline in the default layout can't be compressed
				# or stretched vertically. fixing this properly is quite involved, because we'd need to find a sensible
				# generic way for TabbedContainer to set a min/max height based on it's children, and then a sensible
				# generic rule for what SplitContainer should do in its __applySizePolicy() method.
				if len( splitContainer[0] ) == 1 and isinstance( splitContainer[0][0], GafferUI.Timeline ) :
					splitContainer[0]._qtWidget().setFixedHeight( splitContainer[0][0]._qtWidget().sizeHint().height() )
					splitContainer._qtWidget().setSizePolicy( QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed )

	def __addChild( self, splitContainer, nameOrEditor ) :

		assert( len( splitContainer ) == 1 )

		tabbedContainer = splitContainer[0]

		if isinstance( nameOrEditor, basestring ) :
			editor = GafferUI.EditorWidget.create( nameOrEditor, self.scriptNode() )
		else :
			editor = nameOrEditor
			assert( editor.scriptNode().isSame( self.scriptNode() ) )

		tabbedContainer.insert( len( tabbedContainer ), editor )
		tabbedContainer.setCurrent( editor )

		return editor

	def __split( self, splitContainer, orientation, subPanelIndex ) :

		assert( len( splitContainer ) == 1 ) # we should not be split already

		sc1 = _SplitContainer()
		sc1.append( splitContainer[0] )

		assert( len( splitContainer ) == 0 )

		sc2 = _SplitContainer()
		sc2.append( _TabbedContainer() )

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

	def __join( self, splitContainer, subPanelIndex ) :

		subPanelToKeepFrom = splitContainer[subPanelIndex]
		del splitContainer[:]
		for w in subPanelToKeepFrom[:] :
			splitContainer.append( w )

		splitContainer.setOrientation( subPanelToKeepFrom.getOrientation() )

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

# The internal class used to allow hierarchical splitting of the layout.
class _SplitContainer( GafferUI.SplitContainer ) :

	def __init__( self, **kw ) :

		GafferUI.SplitContainer.__init__( self, **kw )

# The internal class used to keep a bunch of editors in tabs, updating the titles
# when appropriate, and keeping a track of the pinning of nodes.
class _TabbedContainer( GafferUI.TabbedContainer ) :

	def __init__( self, cornerWidget=None, **kw ) :

		GafferUI.TabbedContainer.__init__( self, cornerWidget, **kw )

		with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, borderWidth=1 ) as cornerWidget :

			self.__pinningButton = GafferUI.Button( image="targetNodesUnlocked.png", hasFrame=False )

			layoutButton = GafferUI.MenuButton( image="layoutButton.png", hasFrame=False )
			layoutButton.setMenu( GafferUI.Menu( Gaffer.WeakMethod( self.__layoutMenuDefinition ) ) )
			layoutButton.setToolTip( "Click to modify the layout" )

		self.setCornerWidget( cornerWidget )

		self.__pinningButtonClickedConnection = self.__pinningButton.clickedSignal().connect( Gaffer.WeakMethod( self.__pinningButtonClicked ) )
		self.__currentTabChangedConnection = self.currentChangedSignal().connect( Gaffer.WeakMethod( self.__currentTabChanged ) )
		self.__dragEnterConnection = self.dragEnterSignal().connect( Gaffer.WeakMethod( self.__dragEnter ) )
		self.__dragLeaveConnection = self.dragLeaveSignal().connect( Gaffer.WeakMethod( self.__dragLeave ) )
		self.__dropConnection = self.dropSignal().connect( Gaffer.WeakMethod( self.__drop ) )

	## \todo We're overriding this so we can connect to titleChanged(). This works OK
	# because we know that CompoundEditor only uses insert(), and not any other means of
	# adding a child. A more general solution might be to have a Container.childAddedSignal()
	# method so we can get called no matter how we get a new child.
	def insert( self, index, editor ) :

		GafferUI.TabbedContainer.insert( self, index, editor )

		self.setLabel( editor, editor.getTitle() )
		editor.__titleChangedConnection = editor.titleChangedSignal().connect( Gaffer.WeakMethod( self.__titleChanged ) )

		self.ancestor( CompoundEditor ).editorAddedSignal()( self.ancestor( CompoundEditor ), editor )

	def __layoutMenuDefinition( self ) :

		# the menu definition for the layout is dealt with by the CompoundEditor, because only it
		# has the high-level view necessary to do splitting of layouts and so on.
		return self.ancestor( CompoundEditor )._layoutMenuDefinition( self )

	def __titleChanged( self, editor ) :

		self.setLabel( editor, editor.getTitle() )

	def __currentTabChanged( self, tabbedContainer, currentEditor ) :

		if isinstance( currentEditor, GafferUI.NodeSetEditor ) :
			self.__nodeSetChangedConnection = currentEditor.nodeSetChangedSignal().connect( Gaffer.WeakMethod( self.__updatePinningButton ) )
		else :
			self.__nodeSetChangedConnection = None

		self.__updatePinningButton()

	def __updatePinningButton( self, *unused ) :

		editor = self.getCurrent()
		if isinstance( editor, GafferUI.NodeSetEditor ) and editor.scriptNode() is not None :

			self.__pinningButton.setVisible( True )

			if editor.getNodeSet().isSame( editor.scriptNode().selection() ) :
				self.__pinningButton.setToolTip( "Click to lock view to current selection" )
				self.__pinningButton.setImage( "targetNodesUnlocked.png" )
			else :
				self.__pinningButton.setToolTip( "Click to unlock view and follow selection" )
				self.__pinningButton.setImage( "targetNodesLocked.png" )

		else :

			self.__pinningButton.setVisible( False )

	def __pinningButtonClicked( self, button ) :

		editor = self.getCurrent()
		assert( isinstance( editor, GafferUI.NodeSetEditor ) )

		nodeSet = editor.getNodeSet()
		selectionSet = editor.scriptNode().selection()
		if nodeSet.isSame( selectionSet ) :
			nodeSet = Gaffer.StandardSet( list( nodeSet ) )
		else :
			nodeSet = selectionSet
		editor.setNodeSet( nodeSet )

	def __dragEnter( self, tabbedContainer, event ) :

		currentEditor = self.getCurrent()
		if not isinstance( currentEditor, GafferUI.NodeSetEditor ) :
			return False

		if currentEditor.isAncestorOf( event.sourceWidget ) :
			return False

		result = False
		if isinstance( event.data, Gaffer.Node ) :
			result = True
		elif isinstance( event.data, Gaffer.Set ) :
			if event.data.size() and isinstance( event.data[0], Gaffer.Node ) :
				result = True

		if result :
			self.setHighlighted( True )
			self.__pinningButton.setHighlighted( True )

		return result

	def __dragLeave( self, tabbedContainer, event ) :

		self.setHighlighted( False )
		self.__pinningButton.setHighlighted( False )

	def __drop( self, tabbedContainer, event ) :

		if isinstance( event.data, Gaffer.Node ) :
			nodeSet = Gaffer.StandardSet( [ event.data ] )
		else :
			nodeSet = Gaffer.StandardSet( [ x for x in event.data if isinstance( x, Gaffer.Node ) ] )

		if event.modifiers & event.Modifiers.Shift :
			currentEditor = self.getCurrent()
			newEditor = currentEditor.__class__( currentEditor.scriptNode() )
			newEditor.setNodeSet( nodeSet )
			self.insert( 0, newEditor )
			self.setCurrent( newEditor )
		else :
			self.getCurrent().setNodeSet( nodeSet )

		self.setHighlighted( False )
		self.__pinningButton.setHighlighted( False )

		return True

