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

import collections
import functools
import sys
import weakref

import imath

import IECore

import Gaffer
import GafferUI

from Qt import QtCore
from Qt import QtGui
from Qt import QtWidgets

# Note: 'preferredBound' is a bottom-left origin NDC (available area)
# representation of a windows on-screen geometry. This is persisted in saved
# layouts to maximise compatibility between different screen configurations.
# @see _preferredBound

class CompoundEditor( GafferUI.Editor ) :

	class _DetachedPanel( GafferUI.Window ) :

		def __init__( self, scriptNode, children = None, preferredBound = None, **kwargs ) :

			GafferUI.Window.__init__( self, **kwargs )
			self.__titleManger = GafferUI.ScriptWindow._WindowTitleBehaviour( self, scriptNode )

			self.__splitContainer = _SplitContainer()
			self.__splitContainer.append( _TabbedContainer() )
			self.setChild( self.__splitContainer )

			self._gafferParent = None

			if children :
				self.__splitContainer.addChildren( children )

			self.__preferredBound = preferredBound or {}

		## As were technically not in the Qt hierarchy, but do want to be logically
		# owned by a CompoundEditor, we re-implement this to re-direct ancestor
		# calls to which ever editor we were added to (CompoundEditor fills this
		# in for us when we're added).
		def parent( self ) :

			return self._gafferParent() if self._gafferParent else None

		def editors( self, type = GafferUI.Editor ) :

			return self.__splitContainer.editors( type = type )

		def addEditor( self, editor ) :

			self.__splitContainer.addEditor( editor )

		def replaceEditors( self, splitContainer ) :

			self.__splitContainer = splitContainer
			self.setChild( self.__splitContainer )

		def restorePreferredBound( self ) :

			if self.__preferredBound :
				_restorePreferredBound( self, self.__preferredBound )

		def updatePreferredBound( self ) :

			self.__preferredBound = _preferredBound( self )

		# A detached panel is considered empty if it has a single split with
		# no editors.
		def isEmpty( self ) :

			if len(self.__splitContainer) == 1 :
				c = self.__splitContainer[0]
				if isinstance( c, _TabbedContainer ) and len(c) == 0 :
					return True

			return False

		def _setGafferParent( self, gafferWidget ) :

			self._gafferParent = None
			if gafferWidget :
				self._gafferParent = weakref.ref( gafferWidget )

		def __repr__( self ) :

			return "GafferUI.CompoundEditor._DetachedPanel( scriptNode, children=%s, preferredBound=%s )" \
					% (
						_serialiseSplits( self.__splitContainer ),
						_imathRepr( self.__preferredBound )
					)

	def __init__( self, scriptNode, children=None, detachedPanels=None, preferredBound=None, **kw ) :

		self.__splitContainer = _SplitContainer()

		GafferUI.Editor.__init__( self, self.__splitContainer, scriptNode, **kw )

		self.__visibilityChangedConnection = self.visibilityChangedSignal().connect( Gaffer.WeakMethod( self.__visibilityChanged ) )

		self.__splitContainer.append( _TabbedContainer() )

		self.__keyPressConnection = self.__splitContainer.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ) )

		if children :
			self.__splitContainer.addChildren( children )

		self.__preferredBound = preferredBound or {}

		self.__detachedPanels = []

		if detachedPanels :
			for p in detachedPanels :
				self._addDetachedPanel( p )

	## Returns all the editors that comprise this CompoundEditor, optionally
	# filtered by type.
	def editors( self, type = GafferUI.Editor ) :

		editors = self.__splitContainer.editors( type = type )
		for p in self._detachedPanels() :
			editors.extend( p.editors( type = type ) )
		return editors

	## Adds an editor to the layout, trying to place it in the same place
	# as editors of the same type.
	def addEditor( self, editor ) :

		self.__splitContainer.addEditor( editor )

	__nodeSetMenuSignal = Gaffer.Signal2()
	## A signal emitted to populate a menu for manipulating
	# the node set of a NodeSetEditor - the signature is
	# `slot( nodeSetEditor, menuDefinition )`.
	@classmethod
	def nodeSetMenuSignal( cls ) :

		return CompoundEditor.__nodeSetMenuSignal

	# Restores the preferred geometry, if this is known for the main window and
	# any detached panels. This must only be called when the editor is part of a
	# window hierarchy so that screen affinity can be properly applied.
	def restorePreferredBound( self ) :

		if self.__preferredBound :
			_restorePreferredBound( self.ancestor( GafferUI.ScriptWindow ), self.__preferredBound )

		for p in self.__detachedPanels :
			p.restorePreferredBound()

	# Updates the stored preferred geometry for this layout
	def updatePreferredBound( self ) :

		window = self.ancestor( GafferUI.ScriptWindow )
		if window :
			self.__preferredBound = _preferredBound( window )

		for p in self.__detachedPanels :
			p.updatePreferredBound()

	def _detachedPanels( self ) :

		return list(self.__detachedPanels)

	def _addDetachedPanel( self, panel ) :

		oldParent = panel.parent()
		if oldParent is self :
			return

		if oldParent is not None :
			oldParent._removeDetachedPanel( panel )

		panel.__removeOnCloseConnection = panel.closedSignal().connect( lambda w : w.parent()._removeDetachedPanel( w ) )

		# Technically the widget isn't in the Qt hierarchy, but we want
		# to be able to use GafferUI.Widget.ancestor, so we sneak ourselves
		# in there. @see _DetachedPanel.parent
		panel._setGafferParent( self )
		self.__detachedPanels.append( panel )

	def _removeDetachedPanel( self, panel ) :

		panel._setGafferParent( None )
		self.__detachedPanels.remove( panel )
		panel.__removeOnCloseConnection = None
		panel._applyVisibility()

	def _preferredBound( self ) :

		return self.__preferredBound

	def __visibilityChanged(self, widget) :

		v = self.visible()
		for p in self._detachedPanels() :
			p.setVisible( v )

	def __repr__( self ) :

		window = self.ancestor( GafferUI.ScriptWindow )

		return "GafferUI.CompoundEditor( scriptNode, children = %s, detachedPanels = %s, preferredBound = %s )" \
				% (
					_serialiseSplits( self.__splitContainer ),
					self._detachedPanels(),
					_imathRepr( _preferredBound( window ) ) if window else {}
				)

	def __keyPress( self, unused, event ) :

		if event.key == "Space" :

			# Minimise/maximise the current panel. We do this by adjusting the
			# handle position of all ancestor containers.

			widget = GafferUI.Widget.widgetAt( GafferUI.Widget.mousePosition() )

			Ancestor = collections.namedtuple( "Ancestor", [ "splitContainer", "childIndex", "handlePosition" ] )
			ancestors = []

			while widget is not None :
				parent = widget.parent()
				if isinstance( parent, _SplitContainer ) and parent.isSplit() :
					childIndex = parent.index( widget )
					ancestors.append(
						Ancestor(
							parent, childIndex, self.__handlePosition( parent )
						)
					)
				widget = parent

			maximised = all( a.handlePosition == 1 - a.childIndex for a in ancestors )
			if maximised :
				for ancestor in reversed( ancestors ) :
					h = getattr( ancestor.splitContainer, "__spaceBarHandlePosition", 0.5 )
					ancestor.splitContainer.setSizes( [ h, 1.0 - h ] )
			else :
				for ancestor in ancestors :
					if ancestor.handlePosition != 1 and ancestor.handlePosition != 0 :
						setattr( ancestor.splitContainer, "__spaceBarHandlePosition", ancestor.handlePosition )
					ancestor.splitContainer.setSizes( [ 1 - ancestor.childIndex, ancestor.childIndex ] )

			return True

		elif event.key == "T" and event.modifiers == event.Modifiers.Control :

			tabbedContainer = GafferUI.Widget.widgetAt( GafferUI.Widget.mousePosition(), _TabbedContainer )
			if tabbedContainer is not None :
				tabbedContainer.setTabsVisible( not tabbedContainer.getTabsVisible() )
				return True

		return False


	@staticmethod
	def __handlePosition( splitContainer ) :

		assert( len( splitContainer ) == 2 )

		sizes = splitContainer.getSizes()
		return float( sizes[0] ) / sum( sizes )

# Internal widget classes
# =======================
#
# These assist in creating the layout but are not part of the public API,
# which is provided solely by the methods of the CompoundEditor itself.
#
# > Todo : We could further insulate the CompoundEditor from the details
# > of these classes by not exposing the SplitContainer/TabbedContainer as
# > base classes but instead using a has-a relationship. We could also move
# > the keypress handling out of CompoundEditor.

# The internal class used to allow hierarchical splitting of the layout.
class _SplitContainer( GafferUI.SplitContainer ) :

	def __init__( self, **kw ) :

		GafferUI.SplitContainer.__init__( self, **kw )
		self._qtWidget().setObjectName( "gafferCompoundEditor" )

	def isSplit( self ) :

		return len( self ) == 2

	def split( self, orientation, subPanelIndex ) :

		assert( not self.isSplit() )

		sc1 = _SplitContainer()
		sc1.append( self[0] )

		assert( len( self ) == 0 )

		sc2 = _SplitContainer()
		sc2.append( _TabbedContainer() )

		if subPanelIndex==1 :
			self.append( sc1 )
			self.append( sc2 )
		else :
			self.append( sc2 )
			self.append( sc1 )

		assert( len( self ) == 2 )

		self.setOrientation( orientation )

	def join( self, subPanelIndex ) :

		assert( self.isSplit() )

		subPanelToKeepFrom = self[subPanelIndex]
		del self[:]
		for w in subPanelToKeepFrom[:] :
			self.append( w )

		self.setOrientation( subPanelToKeepFrom.getOrientation() )

	def editors( self, type = GafferUI.Editor ) :

		def __recurse( w ) :
			assert( isinstance( w, _SplitContainer ) )
			if w.isSplit() :
				return __recurse( w[0] ) + __recurse( w[1] )
			else :
				return [ e for e in w[0] if isinstance( e, type ) ]

		return __recurse( self )

	def addEditor( self, editor ) :

		def __findContainer( w, editorType ) :
			if w.isSplit() :
				ideal, backup = __findContainer( w[0], editorType )
				if ideal is not None :
					return ideal, backup
				return __findContainer( w[1], editorType )
			else :
				for e in w[0] :
					if isinstance( e, editorType ) :
						return w, w
				return None, w

		ideal, backup = __findContainer( self, editor.__class__ )
		container = ideal if ideal is not None else backup

		container[0].addEditor( editor )

	def addChildren( self, children ) :

		if isinstance( children, tuple ) and len( children ) and isinstance( children[0], GafferUI.SplitContainer.Orientation ) :

			self.split( children[0], 0 )
			self[0].addChildren( children[2][0] )
			self[1].addChildren( children[2][1] )
			self.setSizes( [ children[1], 1.0 - children[1] ] )

		else :
			if isinstance( children, tuple ) :
				# backwards compatibility - tabs provided as a tuple
				for c in children :
					self[0].addEditor( c )
			else :
				# new format - various fields provided by a dictionary
				for i, c in enumerate( children["tabs"] ) :
					editor = self[0].addEditor( c )
					if "pinned" in children and isinstance( editor, GafferUI.NodeSetEditor ) and children["pinned"][i] :
						editor.setNodeSet( Gaffer.StandardSet() )

				if "currentTab" in children :
					self[0].setCurrent( self[0][children["currentTab"]] )

				self[0].setTabsVisible( children.get( "tabsVisible", True ) )

# The internal class used to keep a bunch of editors in tabs, updating the titles
# when appropriate, and keeping a track of the pinning of nodes.
class _TabbedContainer( GafferUI.TabbedContainer ) :

	def __init__( self, cornerWidget=None, **kw ) :

		GafferUI.TabbedContainer.__init__( self, cornerWidget, **kw )

		with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 2, borderWidth=1 ) as cornerWidget :

			self.__pinningButton = GafferUI.Button( image="targetNodesUnlocked.png", hasFrame=False )

			layoutButton = GafferUI.MenuButton( image="layoutButton.png", hasFrame=False )
			layoutButton.setMenu( GafferUI.Menu( Gaffer.WeakMethod( self.__layoutMenuDefinition ) ) )
			layoutButton.setToolTip( "Click to modify the layout" )

		self.setCornerWidget( cornerWidget )

		self.__pinningButtonClickedConnection = self.__pinningButton.clickedSignal().connect( Gaffer.WeakMethod( self.__pinningButtonClicked ) )
		self.__pinningButtonContextMenuConnection = self.__pinningButton.contextMenuSignal().connect( Gaffer.WeakMethod( self.__pinningButtonContextMenu ) )
		self.__currentTabChangedConnection = self.currentChangedSignal().connect( Gaffer.WeakMethod( self.__currentTabChanged ) )
		self.__dragEnterConnection = self.dragEnterSignal().connect( Gaffer.WeakMethod( self.__dragEnter ) )
		self.__dragLeaveConnection = self.dragLeaveSignal().connect( Gaffer.WeakMethod( self.__dragLeave ) )
		self.__dropConnection = self.dropSignal().connect( Gaffer.WeakMethod( self.__drop ) )

		self.__tabDragBehaviour = _TabDragBehaviour( self )

	def addEditor( self, nameOrEditor ) :

		if isinstance( nameOrEditor, basestring ) :
			editor = GafferUI.Editor.create( nameOrEditor, self.ancestor( CompoundEditor ).scriptNode() )
		else :
			editor = nameOrEditor

		self.insert( len( self ), editor )
		self.setCurrent( editor )

		self.setLabel( editor, editor.getTitle() )
		editor.__titleChangedConnection = editor.titleChangedSignal().connect( Gaffer.WeakMethod( self.__titleChanged ) )

		return editor

	def removeEditor( self, editor ) :

		editor.__titleChangedConnection = None
		self.removeChild( editor )
		self.__updatePinningButton( None )

	def setTabsVisible( self, tabsVisible ) :

		GafferUI.TabbedContainer.setTabsVisible( self, tabsVisible )

		# This is a shame-faced hack to make sure the timeline in the default layout can't be compressed
		# or stretched vertically. Fixing this properly is quite involved, because we'd need to find a sensible
		# generic way for TabbedContainer to set a min/max height based on it's children, and then a sensible
		# generic rule for what SplitContainer should do in its __applySizePolicy() method.
		if len( self ) == 1 and isinstance( self[0], GafferUI.Timeline ) :
			if not tabsVisible :
				# Fix height so timeline is not resizable
				self._qtWidget().setFixedHeight( self[0]._qtWidget().sizeHint().height() )
				self.parent()._qtWidget().setSizePolicy( QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Fixed )
			else :
				# Undo the above
				QWIDGETSIZE_MAX = 16777215 # Macro not exposed by Qt.py, but needed to remove fixed height
				self._qtWidget().setFixedHeight( QWIDGETSIZE_MAX )
				self.parent()._qtWidget().setSizePolicy( QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored )

	def __layoutMenuDefinition( self ) :

		m = IECore.MenuDefinition()

		layouts = GafferUI.Layouts.acquire( self.ancestor( CompoundEditor ).scriptNode().applicationRoot() )
		for c in layouts.registeredEditors() :
			m.append( "/" + IECore.CamelCase.toSpaced( c ), { "command" : functools.partial( Gaffer.WeakMethod( self.addEditor ), c ) } )

		m.append( "/divider", { "divider" : True } )

		splitContainer = self.ancestor( _SplitContainer )
		splitContainerParent = splitContainer.parent()
		currentTab = self.getCurrent()

		detatchItemAdded = False

		if isinstance( splitContainerParent, _SplitContainer ) :
			m.append( "/Detach Panel", { "command" : Gaffer.WeakMethod( self.__detachPanel ) } )
			detatchItemAdded = True

		if currentTab is not None :
			m.append( "/Detach " + self.getLabel( currentTab ), { "command" : Gaffer.WeakMethod( self.__detachCurrentTab ) } )
			detatchItemAdded = True

		if detatchItemAdded :
			m.append( "/divider2", { "divider" : True } )

		removeItemAdded = False

		if isinstance( splitContainerParent, _SplitContainer ) :
			m.append( "Remove Panel", { "command" : Gaffer.WeakMethod( self.__removePanel ) } )
			removeItemAdded = True

		if currentTab is not None :
			m.append( "/Remove " + self.getLabel( currentTab ), { "command" : Gaffer.WeakMethod( self.__removeCurrentTab ) } )
			removeItemAdded = True

		if removeItemAdded :
			m.append( "/divider3", { "divider" : True } )

		tabsVisible = self.getTabsVisible()
		# Because the menu isn't visible most of the time, the Ctrl+T shortcut doesn't work - it's just there to let
		# users know it exists. It is actually implemented directly in __keyPress.
		m.append( "/Hide Tabs" if tabsVisible else "/Show Tabs", { "command" : functools.partial( Gaffer.WeakMethod( self.setTabsVisible ), not tabsVisible ), "shortCut" : "Ctrl+T" } )
		m.append( "/TabsDivider", { "divider" : True } )

		m.append( "/Split Left", { "command" : functools.partial( Gaffer.WeakMethod( splitContainer.split ), GafferUI.SplitContainer.Orientation.Horizontal, 0 ) } )
		m.append( "/Split Right", { "command" : functools.partial( Gaffer.WeakMethod( splitContainer.split ), GafferUI.SplitContainer.Orientation.Horizontal, 1 ) } )
		m.append( "/Split Bottom", { "command" : functools.partial( Gaffer.WeakMethod( splitContainer.split ), GafferUI.SplitContainer.Orientation.Vertical, 1 ) } )
		m.append( "/Split Top", { "command" : functools.partial( Gaffer.WeakMethod( splitContainer.split ), GafferUI.SplitContainer.Orientation.Vertical, 0 ) } )

		return m

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

	def __pinningButtonContextMenu( self, button ) :

		m = IECore.MenuDefinition()
		CompoundEditor.nodeSetMenuSignal()( self.getCurrent(), m )

		if not len( m.items() ) :
			return False

		self.__pinningMenu = GafferUI.Menu( m )

		buttonBound = button.bound()
		self.__pinningMenu.popup(
			parent = self.ancestor( GafferUI.Window ),
			position = imath.V2i( buttonBound.min().x, buttonBound.max().y )
		)

		return True

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

	def __detachCurrentTab( self ) :

		editor = self.getCurrent()

		window = CompoundEditor._DetachedPanel( editor.scriptNode() )
		self.__moveWindowOverWidget( window, editor, 10 )

		self.ancestor( GafferUI.CompoundEditor )._addDetachedPanel( window )

		self.removeEditor( editor )

		window.addEditor( editor )
		window.setVisible( True )

	def __detachPanel( self ) :

		# Fetch them now, or we'll be out of the hierarchy after we have
		# collapsed our old parent split container and won't be able to find them
		splitContainer = self.ancestor( _SplitContainer )
		compoundEditor = self.ancestor( GafferUI.CompoundEditor )

		window = CompoundEditor._DetachedPanel( self.ancestor( GafferUI.ScriptWindow ).scriptNode() )
		self.__moveWindowOverWidget( window, splitContainer, 10 )

		compoundEditor._addDetachedPanel( window )

		# We must join the parent or we end up with nested split containers in the hierarchy
		parent = splitContainer.parent()
		parent.join( 1 - parent.index( splitContainer ) )

		window.replaceEditors( splitContainer )
		window.setVisible( True )

	@staticmethod
	def __moveWindowOverWidget( window, targetWidget, offsetPixels ) :

		# TODO: Does this need to consider which screen we're on if its not a
		# virtual desktop spanning multiple?
		qWidget = targetWidget._qtWidget()
		topLeft = qWidget.mapToGlobal( qWidget.rect().topLeft() )
		window.setPosition( imath.V2i( topLeft.x() + offsetPixels, topLeft.y() + offsetPixels ) )

	def __removeCurrentTab( self ) :

		self.removeEditor( self.getCurrent() )

	def __removePanel( self ) :

		splitContainer = self.ancestor( _SplitContainer )
		splitContainerParent = splitContainer.parent()
		# we defer the call to an idle callback to workaround widget lifetime
		# issues in certain circumstances (eg hosting Gaffer in other Qt DCC).
		## \todo: consider doing this for all Menu commands in GafferUI.Menu
		GafferUI.EventLoop.addIdleCallback( functools.partial( Gaffer.WeakMethod( splitContainerParent.join ), 1 - splitContainerParent.index( splitContainer ) ) )



## An internal eventFilter class managing all tab drag-drop events and logic.
# Tab dragging is an exception and is implemented entirely using native Qt
# events. This was decided after trying all combinations of Qt-only/Gaffer-only
# and Gaffer/Qt hybrid as:
#
#  - We wanted the visual sophistication of QTabBar.setMovable() for
#    re-arranging tabs within their parent container.
#  - Qt doesn't use its own drag mechanism for setMoveable so we have to
#    interact at a lower level that we'd otherwise like.
#  - We can't programmatically start a Gaffer drag.
#  - We had issues propagating style-changes during a Gaffer drag.
#
# As such, it is somewhat of an outlier compared to how the rest of the
# application works. To avoid polluting the code base, it has been structured
# so that as much logic and Qt interaction is contained within this class.
#
# The broad responsibilities of the _TabDragEventManager are:
#
#  - Capture the starting state of any TabBar drag.
#  - Abort the built-in tab-move behaviour of QTabBar when the cursor leaves
#    the logical are of the TabbedContainer in-which the tab lives.
#  - Manage hover states during a drag operation.
#  - Coordinate the re-parenting of Tab widgets.
#  - Manage the life-cycle of detached panels affected by the drag.
#  - Correct the cursor appearance as much as possible.
#
class _TabDragBehaviour( QtCore.QObject ) :

	__tabMimeType = "application/x-gaffer.compoundEditor.tab"

	# Qt has a somewhat hard-coded handling of the drag/drop cursor which draws
	# the 'forbidden' shape when outside of our windows. QDragManager also
	# uses setOverrideCursor so setCursor doesn't have any effect. This is a
	# nasty brute-force global event filter that attempts to wrangle back some
	# control over the mouse cursor during a drag.
	class _CursorBehaviour( QtCore.QObject ) :

		def eventFilter( self, o, e ) :
			# We always get a MetaCall as well as Move. This helps us trump
			# DragManager which seems to update in Move - lol.
			if e.type() in ( QtCore.QEvent.MetaCall, QtCore.QEvent.Move ) :
				# We use the DragMoveCursor to minimise visual flicker
				# (as its the 'allowed' version of the 'forbidden' cursor
				# it's overriding).
				QtWidgets.QApplication.instance().changeOverrideCursor(  QtCore.Qt.DragMoveCursor )

			return False

		def cleanup( self ) :
			# Sometimes we end up with a lingering override cursor
			QtWidgets.QApplication.instance().restoreOverrideCursor()

	def __init__( self, tabbedContainer ) :

		QtCore.QObject.__init__( self )

		self.__eventMask = set ( (
			QtCore.QEvent.MouseButtonPress,
			QtCore.QEvent.MouseButtonRelease,
			QtCore.QEvent.MouseMove,
			QtCore.QEvent.DragEnter,
			QtCore.QEvent.DragLeave,
			QtCore.QEvent.Drop
		) )

		self.__abortedInitialRearrange = False

		self.__tabbedContainer = weakref.ref( tabbedContainer )

		# Install ourselves as an event filter

		# Gaffer.Widget makes use of a custom event filter, but it is
		# initialised lazily. Fortunately, TabbedContainer connects to tabBar
		# signals during __init__ before were created, so we should then always
		# be a 'later' handler, and so called first.
		tabWidget = tabbedContainer._qtWidget()
		tabWidget.installEventFilter( self )
		tabWidget.setAcceptDrops( True )

		tabBar = tabWidget.tabBar()
		tabBar.installEventFilter( self )
		tabBar.setMovable( True )
		tabBar.setAcceptDrops( True )

		self.__dragCursorBehaviour = _TabDragBehaviour._CursorBehaviour()

	def eventFilter( self, qObject, qEvent ) :

		qEventType = qEvent.type()
		if qEventType not in self.__eventMask :
			return False

		if isinstance( qObject, QtWidgets.QTabBar ) :

			if qEventType == qEvent.MouseButtonPress :

				return self.__tabBarMousePress( qObject, qEvent )

			elif qEventType == qEvent.MouseButtonRelease :

				return self.__tabBarMouseRelease( qObject, qEvent )

			elif qEventType == qEvent.MouseMove :

				return self.__tabBarMouseMove( qObject, qEvent )

		if qEventType == qEvent.DragEnter :

			return self.__dragEnter( qEvent )

		elif qEventType == qEvent.DragLeave :

			return self.__dragLeave( qEvent )

		elif qEventType == qEvent.Drop :

			return self.__drop( qObject, qEvent )

		return False


	def __tabBarMousePress( self, qTabBar, event ) :

		if event.button() == QtCore.Qt.LeftButton :

			self.__abortedInitialRearrange = False

			# As the tab the user clicks on to drag may have been re-ordered
			# before they leave the bounds of the widget, we track which tab
			# was originally picked, and where it started. Then we can put it
			# back if we need to later. We also track which tab was current as
			# the user can initiate a drag from an unselected tab.

			self.__draggedTab = None
			self.__currentTabAtDragStart = None

			self.__draggedTabOriginalIndex = qTabBar.tabAt( event.pos() )
			if self.__draggedTabOriginalIndex > -1 :
				tabbedContainer = self.__tabbedContainer()
				self.__draggedTab = tabbedContainer[ self.__draggedTabOriginalIndex ]
				self.__currentTabAtDragStart = tabbedContainer.getCurrent()

		# We never consume this event to allow the native Qt drag-rearrange
		# implementation to work (which is internally done in press/move/release)
		return False

	def __tabBarMouseRelease( self, qTabBar, event ) :

		# State reset
		self.__draggedTab = None
		self.__draggedTabOriginalIndex = -1
		self.__currentTabAtDragStart = None

		# We only consume this event if we've been messing with events and
		# starting drags. This ensures we don't send the QTabBar a double release
		if self.__abortedInitialRearrange :
			return True

		return False

	def __tabBarMouseMove( self, qTabBar, event ):

		# This is only called during initial dragging whilst re-ordering the
		# tab bar the user clicked on.
		#
		# If the user moves the mouse out of the tab bar, we need to make the
		# underlying TabBar think the user let go of the mouse so it aborts
		# any in-progress move of the tab (constrained to this TabBar) So we
		# can venture off into our own brave new world.
		#
		# All further mouse moves need be handled (by this class) in
		# response to DragMove if any in-drag logic is required.

		if event.buttons() & QtCore.Qt.LeftButton \
		   and not self.__abortedInitialRearrange \
		   and self.__shouldAbortInitialRearrange( qTabBar, event ) :

			self.__abortTabBarRearrange( qTabBar )
			self.__abortedInitialRearrange = True

			# Remove the dragged tab from container to make sure its obvious to
			# the user that it will move as opposed to copy.
			self.__tabbedContainer().removeEditor( self.__draggedTab )

			# If the dragged editor was in a detached panel, hide it if its now empty.
			# We can't delete it now as Qt references it in DropEvent and we get a crash
			# We'll come back and delete it on idle later.
			cleanupCallback = None
			detachedPanel = self.__tabbedContainer().ancestor( CompoundEditor._DetachedPanel )
			if detachedPanel and detachedPanel.isEmpty() :
				detachedPanel.setVisible( False )
				parentEditor = detachedPanel.ancestor( CompoundEditor )
				cleanupCallback = functools.partial( parentEditor._removeDetachedPanel, detachedPanel )

			# Initiate the drag of the tab and handle the drop action
			self.__doDragForTabBarMove( qTabBar )

			if cleanupCallback :
				GafferUI.EventLoop.addIdleCallback( cleanupCallback )

			return True

		elif self.__abortedInitialRearrange :
			# We don't want the underlying widget to see the continuing moves
			# after we faked the end of the mouse-down move...
			return True

		return False

	def __handleDropAction( self, dropAction ) :

		tabbedContainer = self.__tabbedContainer()

		if dropAction == QtCore.Qt.MoveAction :

			# If the dragged tab wasn't current, restore the original
			# widget, unless the dragged tab was re-placed in this container.
			# We do this as the drag-rearrange/remove can change the current tab
			if self.__getSharedDragWidget().parent() is not tabbedContainer \
			   and self.__currentTabAtDragStart.parent() is tabbedContainer :
				tabbedContainer.setCurrent( self.__currentTabAtDragStart )

		else :

			# Create a new window. We want the center of the tab title to be
			# roughly under the cursor
			draggedEditor = self.__getSharedDragWidget()
			parentEditor = tabbedContainer.ancestor( GafferUI.CompoundEditor )

			window = CompoundEditor._DetachedPanel( draggedEditor.scriptNode() )

			# We have to add the editor early so we can work out the center of
			# the tab header widget otherwise it has no parent so no tab bar...
			window.addEditor( draggedEditor )

			tabCenter = self.__getTabCenter( draggedEditor )
			windowPos = QtGui.QCursor.pos() - tabCenter
			window.setPosition( imath.V2i( windowPos.x(), windowPos.y() ) )

			parentEditor._addDetachedPanel( window )
			window.setVisible( True )

		self.__setSharedDragWidget( None )

	def __dragEnter( self, event ) :

		if not event.mimeData().hasFormat( self.__tabMimeType ) :
			return False

		if self.__getSharedDragWidget() :
			event.acceptProposedAction()
			self.__tabbedContainer().parent().setHighlighted( True )
		else :
			event.ignore()

		return True

	def __dragLeave( self, event ) :

		self.__tabbedContainer().parent().setHighlighted( False )
		return True

	def __drop( self, qWidget, event ) :

		if not event.mimeData().hasFormat( self.__tabMimeType ) :
			return False

		event.acceptProposedAction()

		widget = self.__getSharedDragWidget()
		if widget.parent() is not self.__tabbedContainer() :
			self.__tabbedContainer().addEditor( widget )

		self.__tabbedContainer().parent().setHighlighted( False )

		return True

	def __shouldAbortInitialRearrange( self, qTabBar, event ) :

		if qTabBar.geometry().contains( event.pos() ) :
			return False

		# To avoid aborting as soon as the user slips off the tab bar (which
		# can be annoying as its easily done) we don't abort if they slip into
		# the parent tab container.

		return not qTabBar.parent().geometry().contains( event.pos() )

	def __abortTabBarRearrange( self, qTabBar ) :

		# We don't reliably have much of the data we need in the incoming
		# event (eg: dragLeave) so we make all of it up. Telling the tabbar
		# the user has released the mouse (in the implementation at the time
		# of going to press) stops the re-arrange. The tabs are moved (in terms
		# of indices) on the fly during mouseMove.

		pos = qTabBar.mapFromGlobal( QtGui.QCursor.pos() )

		fakeReleaseEvent = QtGui.QMouseEvent(
			QtCore.QEvent.MouseButtonRelease,
			pos,
			QtCore.Qt.LeftButton, QtCore.Qt.LeftButton,
			QtCore.Qt.NoModifier
		)
		qTabBar.mouseReleaseEvent( fakeReleaseEvent )

	def __doDragForTabBarMove( self, qTabBar ) :

		# As we can't send pointers though the dray data system, we store it
		# in a dark and dirty place. This means we don't actually have any data
		# to send in the end...

		mimeData = QtCore.QMimeData()
		mimeData.setData( self.__tabMimeType, "" )
		self.__setSharedDragWidget( self.__draggedTab )

		drag = QtGui.QDrag( qTabBar )
		drag.setMimeData( mimeData )

		# Install our cursor behaviour so we can override Qt's
		app = QtWidgets.QApplication.instance()
		app.installEventFilter( self.__dragCursorBehaviour )
		try :

			self.__handleDropAction( drag.exec_( QtCore.Qt.MoveAction ) )

		finally :
			app.removeEventFilter( self.__dragCursorBehaviour )
			self.__dragCursorBehaviour.cleanup()

	@staticmethod
	def __getTabCenter( targetTab ) :

		container = targetTab.ancestor( GafferUI.TabbedContainer )
		tabBar = container._qtWidget().tabBar()
		return tabBar.tabRect( container.index( targetTab ) ).center()

	# nasty-fudge
	#
	# We can't pass widgets around using Gaffer or Qt's drag systems, but during a
	# drag we wish to re-parent the existing widget. So, we stash the currently
	# dragged tab widget in the script window. This makes it easy to prevent
	# cross-document drag.

	def __setSharedDragWidget( self, widget ) :

		e = self.__tabbedContainer().ancestor( GafferUI.CompoundEditor )
		e._sharedDraggedWidget = widget

	def __getSharedDragWidget( self ) :

		e = self.__tabbedContainer().ancestor( GafferUI.CompoundEditor )
		if hasattr( e, '_sharedDraggedWidget' ) :
			return e._sharedDraggedWidget

		return None

	# /nasty-fudge


## Returns the preferred bound for a widget's window in NDC space
# (relative to the available screen area). We use the relative area to
# help with portability between platforms/window managers.
# '-1' is used to indicate windows that are on the primary screen.
# If a window is full screen, we still include the bound as otherwise
# the resultant placement when the window is un-fullscreen'd can be a bit small.
#
# Note: We use bottom-left NDC coordinates to be consistent with Gaffer
def _preferredBound( gafferWindow ) :

	qWidget = gafferWindow._qtWidget()

	window = qWidget.windowHandle()
	if not window :
		return {}

	widgetScreen = window.screen()
	widgetScreenNumber = QtWidgets.QApplication.desktop().screenNumber( qWidget )

	if widgetScreen == QtWidgets.QApplication.primaryScreen():
		widgetScreenNumber = -1

	screenGeom = widgetScreen.availableGeometry()
	screenW = float( screenGeom.width() )
	screenH = float( screenGeom.height() )

	# Ideally we'd use frameGeometry for portability, but have seen a variety
	# of issues where the window has been made visible, but doesn't yet
	# have a frame, as we rely on asking for the margins (as you can't
	# setFrameGeometry) we end up with unreliable window placement. As such
	# we compromise and store the widgets geometry instead.
	windowGeom = qWidget.normalGeometry()

	x = ( windowGeom.x() - screenGeom.x() ) / screenW
	y = 1.0 - ( ( windowGeom.y() - screenGeom.y() ) / screenH )
	w = windowGeom.width() / screenW
	h = windowGeom.height() / screenH

	return {
		"screen" :  widgetScreenNumber,
		"fullScreen" : gafferWindow.getFullScreen(),
		"maximized" : bool(window.windowState() & QtCore.Qt.WindowMaximized),
		# As we're bottom-left not top-left the y values are the other way around
		"bound" : imath.Box2f( imath.V2f( x, y - h ), imath.V2f( x + w, y ) )
	}

def _imathRepr( data ) :

	# Neither IECore.repr or repr include the module name
	s = IECore.repr( data )
	for ss in ( 'Box2f', 'V2f' ) :
		s = s.replace( ss, "imath.%s" % ss )
	return s

def _restorePreferredBound( gafferWindow, boundData ) :

	window = gafferWindow._qtWidget().windowHandle()
	if not window :
		return

	# If we don't clear the full-screen flag then restoring geometry won't
	# work, as its overridden by the full-screen state.  Doing it conditionally
	# improves fullscreen - fullscreen layout transitions (avoids pointless
	# re-scale animations), but does mean that we don't properly restore the
	# non-fullscreen size of the window and it will keep that of the first
	# fullscreen layout loaded. Seems a reasonable trade-off though.
	if not ( boundData["fullScreen"] and window.windowState() == QtCore.Qt.WindowFullScreen ) :
		window.setWindowState( QtCore.Qt.WindowNoState )

	targetScreen = QtWidgets.QApplication.primaryScreen()

	if boundData["screen"] > -1 :
		screens = QtWidgets.QApplication.screens()
		if boundData["screen"] < len(screens) :
			targetScreen = screens[ boundData["screen"] ]
			window.setScreen( targetScreen )

	screenGeom = targetScreen.availableGeometry()
	window.setGeometry(
		( boundData["bound"].min()[0] * screenGeom.width() ) + screenGeom.x(),
		( ( 1.0 - boundData["bound"].max()[1] ) * screenGeom.height() ) + screenGeom.y(),
		( boundData["bound"].size()[0] * screenGeom.width() ),
		( boundData["bound"].size()[1] * screenGeom.height() )
	)

	if boundData["fullScreen"] :
		window.setWindowState( QtCore.Qt.WindowFullScreen )
	elif boundData["maximized"] and sys.platform != "darwin" :
		window.setWindowState( QtCore.Qt.WindowMaximized )
	else :
		window.setWindowState( QtCore.Qt.WindowNoState )

def _serialiseSplits( splitContainer, scriptNode = None ) :

	assert( isinstance( splitContainer, _SplitContainer ) )

	if not scriptNode :
		scriptNode = splitContainer.ancestor( GafferUI.CompoundEditor ).scriptNode()

	if splitContainer.isSplit() :
		sizes = splitContainer.getSizes()
		splitPosition = ( float( sizes[0] ) / sum( sizes ) ) if sum( sizes ) else 0
		return "( GafferUI.SplitContainer.Orientation.%s, %f, ( %s, %s ) )" % (
			str( splitContainer.getOrientation() ), splitPosition,
			_serialiseSplits( splitContainer[0], scriptNode ), _serialiseSplits( splitContainer[1], scriptNode )
		)
	else :
		# not split - a tabbed container full of editors
		tabbedContainer = splitContainer[0]
		tabDict = { "tabs" : tuple( tabbedContainer[:] ) }
		if tabbedContainer.getCurrent() is not None :
			tabDict["currentTab"] = tabbedContainer.index( tabbedContainer.getCurrent() )
		tabDict["tabsVisible"] = tabbedContainer.getTabsVisible()

		tabDict["pinned"] = []
		for editor in tabbedContainer :
			if isinstance( editor, GafferUI.NodeSetEditor ) :
				tabDict["pinned"].append( not editor.getNodeSet().isSame( scriptNode.selection() ) )
			else :
				tabDict["pinned"].append( None )

		return repr( tabDict )
