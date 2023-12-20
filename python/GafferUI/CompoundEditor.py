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

class CompoundEditor( GafferUI.Editor ) :

	# The CompoundEditor constructor args are considered 'private', used only
	# by the persistent layout system.
	def __init__( self, scriptNode, _state={}, **kw ) :

		# We have 1px extra padding within the splits themselves to accommodate highlighting
		self.__splitContainer = _SplitContainer( borderWidth = 5 )

		GafferUI.Editor.__init__( self, self.__splitContainer, scriptNode, **kw )

		self.__splitContainer.append( _TabbedContainer() )

		self.__splitContainer.keyPressSignal().connect( CompoundEditor.__keyPress, scoped = False )
		self.visibilityChangedSignal().connect( Gaffer.WeakMethod( self.__visibilityChanged ), scoped = False )

		self.__windowState = _state.get( "windowState", {} )

		self.__splitContainer.restoreChildren( _state.get( "children", () ) )

		self.__detachedPanels = []
		detachedPanels = _state.get( "detachedPanels", () )
		for panelArgs in detachedPanels  :
			self._createDetachedPanel( **panelArgs )

		# By Now, all Editors will have been created, so we can restore any state
		self.__restoreEditorState( _state.get( "editorState", {} ) )

		self.parentChangedSignal().connect( Gaffer.WeakMethod( self.__parentChanged ), scoped=False )

	# Returns the editor of the specified type that the user is most likely to
	# be interested in. If `focussedOnly` is true, only editors with the keyboard
	# focus are considered. If `visibleOnly` is true, only visible editors are
	# considered. Returns None if no suitable editor can be found.
	def editor( self, type = GafferUI.Editor, focussedOnly = False, visibleOnly = False ) :

		candidates = []

		for editor in self.editors( type ) :

			visible = editor.visible()
			if visibleOnly and not visible :
				continue

			window = editor.ancestor( GafferUI.Window )
			qtWindow = window._qtWidget().windowHandle()
			windowIsActive = qtWindow and qtWindow.isActive()
			windowFocusWidget = GafferUI.Widget._owner( window._qtWidget().focusWidget() )
			hasWindowFocus = editor == windowFocusWidget or editor.isAncestorOf( windowFocusWidget )

			if focussedOnly and not ( windowIsActive and hasWindowFocus ) :
				continue

			candidates.append( {
				"editor" : editor,
				"visible" : visible,
				"hasWindowFocus" : hasWindowFocus,
				"windowIsActive" : windowIsActive,
			} )

		if not candidates :
			return None

		# Sort on visibility first, so that an invisible editor never takes precedence over a visible one.
		# Then prefer editors in the active window, and of those, the one with the focus.
		candidates.sort( key = lambda x : ( x["visible"], x["windowIsActive"], x["hasWindowFocus"] ), reverse = True )
		return candidates[0]["editor"]

	## Returns all the editors that comprise this CompoundEditor, optionally
	# filtered by type.
	def editors( self, type = GafferUI.Editor ) :

		editors = self.__splitContainer.editors( type = type )
		for p in self.__detachedPanels :
			editors.extend( p.editors( type = type ) )
		return editors

	## Adds an editor to the layout, trying to place it in the same place
	# as editors of the same type.
	def addEditor( self, editor ) :

		self.__splitContainer.addEditor( editor )

	__nodeSetMenuSignal = Gaffer.Signals.Signal2()
	## A signal emitted to populate a menu for manipulating the node set of a
	# NodeSetEditor - the signature is `slot( nodeSetEditor, menuDefinition )`.
	@classmethod
	def nodeSetMenuSignal( cls ) :

		return CompoundEditor.__nodeSetMenuSignal

	# Restores the preferred size and position of the editor window and any
	# detached panels if this is known.  This should only be called when the
	# editor is part of a window hierarchy so that screen affinity can be
	# properly applied.
	def restoreWindowState( self ) :

		if self.__windowState :
			_restoreWindowState( self.ancestor( GafferUI.ScriptWindow ), self.__windowState )

		for p in self.__detachedPanels :
			p.restoreWindowState()

	# Test Harness use only
	def _detachedPanels( self ) :

		return list(self.__detachedPanels)

	# This method should be used by friend code to instantiate a new detached
	# panel. Don't directly create a _DetachedPanel instance.
	def _createDetachedPanel( self, *args, **kwargs ) :

		panel = _DetachedPanel( self,  *args, **kwargs )
		panel.__removeOnCloseConnection = panel.closedSignal().connect( lambda w : w.parent()._removeDetachedPanel( w ), scoped = True )
		panel.keyPressSignal().connect( CompoundEditor.__keyPress, scoped = False )

		scriptWindow = self.ancestor( GafferUI.ScriptWindow )
		if scriptWindow :
			panel.setTitle( scriptWindow.getTitle() )
			weakSetTitle = Gaffer.WeakMethod( panel.setTitle )
			panel.__titleChangedConnection = scriptWindow.titleChangedSignal().connect( lambda w, t : weakSetTitle( t ), scoped = True )
			# It's not directly in the qt hierarchy so shortcut events don't make it to the MenuBar
			scriptWindow.menuBar().addShortcutTarget( panel )

		self.__detachedPanels.append( panel )
		return panel

	def _removeDetachedPanel( self, panel ) :

		self.__detachedPanels.remove( panel )
		panel.__removeOnCloseConnection = None
		panel.__titleChangedConnection = None
		panel._applyVisibility()

		assert( not panel.visible() )
		GafferUI.WidgetAlgo.keepUntilIdle( panel )

	def __visibilityChanged(self, widget) :

		v = self.visible()
		for p in self.__detachedPanels :
			p.setVisible( v )

	def __parentChanged( self, widget ) :

		# Make sure we have the correct keyboard shortcut listeners
		scriptWindow = self.ancestor( GafferUI.ScriptWindow )
		if scriptWindow is not None :
			for panel in self._detachedPanels() :
				scriptWindow.menuBar().addShortcutTarget( panel )

	def __repr__( self ) :

		# Editors are public classes and so they are stored by repr.
		# We don't want to expose the implementation of detached panels
		# (considered private) so instead we save their construction args.
		return "GafferUI.CompoundEditor( scriptNode, _state={ 'children' : %s, 'detachedPanels' : %s, 'windowState' : %s, 'editorState' : %s } )" \
				% (
					self.__splitContainer.serialiseChildren(),
					self.__serialiseDetachedPanels(),
					self._serializeWindowState(),
					self.__captureEditorState()
				)

	# We use the path to the editor in the UI to allow us to find
	# the same editor again after restoring from a layout.
	# NOTE: This is only stable as long as the layout hasn't been
	# altered since the path was generated
	def __pathToEditor( self, editor ) :

		path = []

		child = editor
		parent = child.parent()

		while parent is not None :

			# The last (will be first) part of the path indicates where
			# the target lives, 'c' for child, 'p' for panel
			if isinstance( parent, GafferUI.CompoundEditor ) :
				path.append( "c" )
				break
			elif isinstance( parent, _DetachedPanel ) :
				path.append( str(self.__detachedPanels.index( parent )) )
				path.append( "p" )
				# We don't append the index of the split container
				# as we'll skip it later
				break

			# The rest of the path in then simply the index of the child under
			# its parent.

			path.append( str(parent.index( child )) )

			child = parent
			parent = child.parent()

		# Store in load order
		path.reverse()

		# By now we have something like "c-0-1-1-0"
		return "-".join( path )

	# Finds the editor given the string from __pathToEditor
	def __editorAtPath( self, path ) :

		path = path.split( "-" )

		# The first element indicates where the path is rooted, the second
		# element is the corresponding index. We have to manually unpack the
		# initial Widget from the appropriate place, the rest we can recursively
		# unpack using the subscript method of indexed child retrieval from
		# gaffer layout widgets.

		if path[0] == "p" :
			obj = self.__detachedPanels[ int(path[1]) ]._splitContainer()
		elif path[0] == "c" :
			obj = self.__splitContainer[ int(path[1]) ]
		else :
			return None

		# We consumed the first two elements getting to the root of the
		# hierarchy we need to search below.
		for i in path[2:] :
			obj = obj[ int(i) ]

		if not isinstance( obj, GafferUI.Editor ) :
			raise RuntimeError( "Unable to find an editor at path %s" % path )

		return obj

	def __captureEditorState( self ) :

		state = {}

		# Store the driver (if set) for any NodeSetEditors
		nodeSetEditors = [ e for e in self.editors() if isinstance( e, GafferUI.NodeSetEditor ) ]
		for n in nodeSetEditors :
			nodeSet = n.getNodeSet()
			# NumericBookmarkSet doesn't support repr as we don't want to
			# couple the layout-centric serialisation that assumes 'scriptNode'
			# is a global into Sets, so we keep it all contained here.
			if isinstance( nodeSet, Gaffer.NumericBookmarkSet ) :
				state[ self.__pathToEditor(n) ] = {
					"nodeSet" : "Gaffer.NumericBookmarkSet( scriptNode, %d )" % nodeSet.getBookmark()
				}
			elif nodeSet.isSame( self.scriptNode().focusSet() ) :
				state[ self.__pathToEditor(n) ] = {
					"nodeSet" : "scriptNode.focusSet()"
				}

		return state

	def __restoreEditorState( self, editorState ) :

		if not editorState :
			return

		for path, state in editorState.items() :

			editor = self.__editorAtPath( path )

			try :

				if "driver" in state :

					# Connecting an editor as the driver of another editor is deprecated.  The closest
					# equivalent is following the focus node - since multiple editors can all follow
					# focus node
					editor.setNodeSet( self.scriptNode().focusSet() )

				elif "nodeSet" in state :

					g = {
						"scriptNode" : self.scriptNode(),
						"Gaffer" : Gaffer
					}
					nodeSet = eval( state["nodeSet"], g )
					editor.setNodeSet( nodeSet )

			except Exception as e :
				IECore.msg(
					IECore.Msg.Level.Error, "CompoundEditor",
					"Unable to restore editor state for {editor}: {error}\n".format(
						editor = "%s (%s)" % ( path, type(editor).__name__ ),
						error = "%s: %s" % ( type(e).__name__, e )
					)
				)

	# visibility for Test Harness
	def _serializeWindowState( self ) :

		window = self.ancestor( GafferUI.ScriptWindow )
		return _reprDict( _getWindowState( window ) if window else {} )

	def __serialiseDetachedPanels( self ) :

		if len(self.__detachedPanels) == 0 :
			return "()"

		# We need the 'force list' syntax or a single panel gets unwrapped
		# when we restore later which errors if we try to pass to __init__.
		return "( %s, )" % ", ".join(
			[ p.reprArgs() for p in self.__detachedPanels ]
		)

	@staticmethod
	def __keyPress( unused, event ) :

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
							parent, childIndex, CompoundEditor.__handlePosition( parent )
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

	def serialiseChildren( self, scriptNode = None ) :

		if not scriptNode :
			scriptNode = self.ancestor( GafferUI.CompoundEditor ).scriptNode()

		if self.isSplit() :
			sizes = self.getSizes()
			splitPosition = ( float( sizes[0] ) / sum( sizes ) ) if sum( sizes ) else 0
			return "( GafferUI.SplitContainer.{}, {}, ( {}, {} ) )".format(
				str( self.getOrientation() ), splitPosition,
				self[0].serialiseChildren( scriptNode ), self[1].serialiseChildren( scriptNode )
			)
		else :
			# not split - a tabbed container full of editors
			tabbedContainer = self[0]
			tabDict = { "tabs" : tuple( tabbedContainer[:] ) }
			if tabbedContainer.getCurrent() is not None :
				tabDict["currentTab"] = tabbedContainer.index( tabbedContainer.getCurrent() )
			tabDict["tabsVisible"] = tabbedContainer.getTabsVisible()
			return repr( tabDict )

	def restoreChildren( self, children ) :

		if not children :
			return

		if isinstance( children, tuple ) and len( children ) and isinstance( children[0], GafferUI.SplitContainer.Orientation ) :

			self.split( children[0], 0 )
			self[0].restoreChildren( children[2][0] )
			self[1].restoreChildren( children[2][1] )
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

				if "currentTab" in children :
					self[0].setCurrent( self[0][children["currentTab"]] )

				self[0].setTabsVisible( children.get( "tabsVisible", True ) )

# The internal class used to keep a bunch of editors in tabs, updating the titles
# when appropriate, and keeping a track of the pinning of nodes.
class _TabbedContainer( GafferUI.TabbedContainer ) :

	def __init__( self, cornerWidget=None, **kw ) :

		GafferUI.TabbedContainer.__init__( self, cornerWidget, **kw )

		with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4, borderWidth=2 ) as cornerWidget :

			self.__pinningWidget = _PinningWidget()

			layoutButton = GafferUI.MenuButton( image="layoutButton.png", hasFrame=False )
			layoutButton.setMenu( GafferUI.Menu( Gaffer.WeakMethod( self.__layoutMenuDefinition ), title = "Layout" ) )
			layoutButton.setToolTip( "Click to modify the layout" )
			layoutButton._qtWidget().setFixedHeight( 15 )

		cornerWidget._qtWidget().setObjectName( "gafferCompoundEditorTools" )
		self.setCornerWidget( cornerWidget )

		self.currentChangedSignal().connect( Gaffer.WeakMethod( self.__currentTabChanged ), scoped = False )
		self.dragEnterSignal().connect( Gaffer.WeakMethod( self.__dragEnter ), scoped = False )
		self.dragLeaveSignal().connect( Gaffer.WeakMethod( self.__dragLeave ), scoped = False )
		self.dropSignal().connect( Gaffer.WeakMethod( self.__drop ), scoped = False )

		tabBar = self._qtWidget().tabBar()
		tabBar.setProperty( "gafferHasTabCloseButtons", GafferUI._Variant.toVariant( True ) )
		tabBar.setContextMenuPolicy( QtCore.Qt.CustomContextMenu )
		tabBar.customContextMenuRequested.connect( Gaffer.WeakMethod( self.__tabContextMenu ) )

		self.__tabDragBehaviour = _TabDragBehaviour( self )

		self.__updateStyles()
		self.__updatePinningWidget()

	# This method MUST be used (along with removeEditor) whenever the children
	# of a _TabbedContainer are being changed. Do not use TabbedContainer methods
	# such as add/remove/insert directly or state tracking will fail.
	def addEditor( self, nameOrEditor ) :

		if isinstance( nameOrEditor, str ) :
			editor = GafferUI.Editor.create( nameOrEditor, self.ancestor( CompoundEditor ).scriptNode() )
		else :
			editor = nameOrEditor

		# We need to make sure we properly remove this, the base class won't
		# call removeEditor, so we miss the appropriate cleanup
		oldParent = editor.parent()
		if oldParent is not None and isinstance( oldParent, _TabbedContainer ) :
			oldParent.removeEditor( editor )

		self.insert( len( self ), editor )
		self.setCurrent( editor )

		self.setLabel( editor, editor.getTitle() )
		editor.__titleChangedConnection = editor.titleChangedSignal().connect( Gaffer.WeakMethod( self.__titleChanged ), scoped = True )
		editor.__keyPressConnection = editor.keyPressSignal().connect( self.__pinningWidget.editorKeyPress, scoped = True )

		self.__updateStyles()

		self.__configureTab( editor )

		return editor

	# This method MUST be used (along with addEditor) whenever the children
	# of a _TabbedContainer are being changed. Do not use TabbedContainer methods
	# such as add/remove/insert directly or state tracking will fail.
	def removeEditor( self, editor ) :

		editor.__titleChangedConnection = None
		editor.__keyPressConnection = None
		self.removeChild( editor )
		self.__updatePinningWidget()
		self.__updateStyles()

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

	def __updateStyles( self ) :

		# Had issues using ints
		self._qtWidget().setProperty( "gafferNumChildren", GafferUI._Variant.toVariant( "%d" % len(self) ) )
		self._repolish()

	def __configureTab( self, editor ) :

		button = GafferUI.Button( image="deleteSmall.png", hasFrame=False )
		button._qtWidget().setFixedSize( 11, 11 )

		editor.__removeButton = button
		button.clickedSignal().connect(
			functools.partial(
				lambda editor, container, _ : container().removeEditor( editor() ),
				weakref.ref( editor ), weakref.ref( self )
			),
			scoped = False
		)

		tabIndex = self.index( editor )
		self._qtWidget().tabBar().setTabButton( tabIndex, QtWidgets.QTabBar.RightSide, button._qtWidget() )

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

		if currentTab is not None :
			m.append( "/Detach " + self.getLabel( currentTab ), { "command" : Gaffer.WeakMethod( self.__detachTab ) } )
			detatchItemAdded = True

		if isinstance( splitContainerParent, _SplitContainer ) :
			m.append( "/Detach Panel", { "command" : Gaffer.WeakMethod( self.__detachPanel ) } )
			detatchItemAdded = True

		if detatchItemAdded :
			m.append( "/divider2", { "divider" : True } )

		removeItemAdded = False

		if currentTab is not None :
			m.append( "/Remove " + self.getLabel( currentTab ), { "command" : Gaffer.WeakMethod( self.__removeTab ) } )
			removeItemAdded = True

		if isinstance( splitContainerParent, _SplitContainer ) :
			m.append( "Remove Panel", { "command" : Gaffer.WeakMethod( self.__removePanel ) } )
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

		# see __updatePinningButton
		if not GafferUI._qtObjectIsValid( self._qtWidget() ) :
			return

		self.setLabel( editor, editor.getTitle() )

	def __currentTabChanged( self, tabbedContainer, currentEditor ) :

		if isinstance( currentEditor, GafferUI.NodeSetEditor ) :
			self.__nodeSetChangedConnection = currentEditor.nodeSetChangedSignal().connect( Gaffer.WeakMethod( self.__updatePinningWidget ), scoped = True )
		else :
			self.__nodeSetChangedConnection = None

		self.__updatePinningWidget()

	def __updatePinningWidget( self, unused = None ) :

		# This method will get called during the deletion of a layout
		# containing linked editor chains if the current editor's driver gets
		# deleted before it does.
		# Due to https://github.com/GafferHQ/gaffer/pull/3179, the c++ widget
		# hierarchy will have been deleted before we are deleted, so we end up
		# with 'Underlying C++ object has been deleted' errors. Sanity check
		# that we're not just further down the deletion list...
		# \todo : Now that linked editor chains no longer exist, this should
		# be unnecessary
		if not GafferUI._qtObjectIsValid( self._qtWidget() ) :
			return

		self.__pinningWidget.update()

	def __tabContextMenu( self, pos ) :

		tabIndex = self._qtWidget().tabBar().tabAt( pos )

		m = IECore.MenuDefinition()
		m.append( '/Detach', { "command" : functools.partial( Gaffer.WeakMethod( self.__detachTab ), tabIndex ) } )
		m.append( '/Remove', { "command" : functools.partial( Gaffer.WeakMethod( self.__removeTab ), tabIndex ) } )

		self.__popupMenu = GafferUI.Menu( m, title = "Tab Actions" )
		self.__popupMenu.popup( parent = self )

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

		return result

	def __dragLeave( self, tabbedContainer, event ) :

		self.setHighlighted( False )

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

		return True

	def __detachTab( self, index = None ) :

		editor = self.getCurrent() if index is None else self[ index ]

		window = self.ancestor( GafferUI.CompoundEditor )._createDetachedPanel()
		self.__matchWindowToWidget( window, editor, 10 )

		self.removeEditor( editor )

		window.addEditor( editor )
		window.setVisible( True )

	def __detachPanel( self ) :

		# Fetch them now, or we'll be out of the hierarchy after we have
		# collapsed our old parent split container and won't be able to find them
		splitContainer = self.ancestor( _SplitContainer )

		window = self.ancestor( GafferUI.CompoundEditor )._createDetachedPanel()
		self.__matchWindowToWidget( window, splitContainer, 10 )

		# We must join the parent or we end up with nested split containers in the hierarchy
		parent = splitContainer.parent()
		parent.join( 1 - parent.index( splitContainer ) )

		window.replaceEditors( splitContainer )
		window.setVisible( True )

	@staticmethod
	def __matchWindowToWidget( window, targetWidget, offsetPixels ) :

		# TODO: Does this need to consider which screen we're on if its not a
		# virtual desktop spanning multiple?
		qWidget = targetWidget._qtWidget()
		targetRect = qWidget.rect()
		topLeft = qWidget.mapToGlobal( targetRect.topLeft() )
		window.setPosition( imath.V2i( topLeft.x() + offsetPixels, topLeft.y() + offsetPixels ) )
		window._qtWidget().resize( targetRect.width(), targetRect.height() )

	def __removeTab( self, index = None ) :

		self.removeEditor( self.getCurrent() if index is None else self[ index ] )

	def __removePanel( self ) :

		splitContainer = self.ancestor( _SplitContainer )
		splitContainerParent = splitContainer.parent()
		# we defer the call to an idle callback to workaround widget lifetime
		# issues in certain circumstances (eg hosting Gaffer in other Qt DCC).
		## \todo: consider doing this for all Menu commands in GafferUI.Menu
		GafferUI.EventLoop.addIdleCallback( functools.partial( Gaffer.WeakMethod( splitContainerParent.join ), 1 - splitContainerParent.index( splitContainer ) ) )

## A detached panel is a _SplitContainer in its own window. They are considered
# child windows of a ScriptWindow, and as such, their lifetime and visibility
# are managed by their parent CompoundEditor. By effect, they are logically
# associated with a particular open script, rather than the Gaffer process.
# They do not have a menu bar and their placement, size and editor list is
# stored and recalled by a layout.
#
# They are considered a private implementation detail rather than a public API
# and so are not directly serialised within a saved layout, only their
# configuration is exposed.
class _DetachedPanel( GafferUI.Window ) :

	def __init__( self, parentEditor, children = None, windowState = None ) :

		GafferUI.Window.__init__( self )

		self.__splitContainer = _SplitContainer( borderWidth = 2 )
		self.__splitContainer.append( _TabbedContainer() )
		self.setChild( self.__splitContainer )

		# @see parent() As we can't be moved between CompoundEditors
		# (scriptNode references in editors will be wrong), we don't need
		# accessors for this.
		self.__parentEditor = weakref.ref( parentEditor )

		self.__splitContainer.restoreChildren( children )

		self.__windowState = windowState or {}

	## As were technically not in the Qt hierarchy, but do want to be logically
	# owned by a CompoundEditor, we re-implement this to re-direct ancestor
	# calls to which ever editor we were added to (CompoundEditor fills this
	# in for us when we're constructed).
	def parent( self ) :

		return self.__parentEditor() if self.__parentEditor else None

	def editors( self, type = GafferUI.Editor ) :

		return self.__splitContainer.editors( type = type )

	def addEditor( self, editor ) :

		self.__splitContainer.addEditor( editor )

	def replaceEditors( self, splitContainer ) :

		self.__splitContainer = splitContainer
		self.setChild( self.__splitContainer )

	def restoreWindowState( self ) :

		if self.__windowState :
			_restoreWindowState( self, self.__windowState )

	# A detached panel is considered empty if it has a single split with no editors.
	def isEmpty( self ) :

		if len(self.__splitContainer) == 1 :
			c = self.__splitContainer[0]
			if isinstance( c, _TabbedContainer ) and len(c) == 0 :
				return True

		return False

	## As not to leak ourselves as an implementation detail, we serialise
	## ourselves as a list of constructor args instead of the usual repr.
	def reprArgs( self ) :

		return "{ 'children' : %s, 'windowState' : %s }" % (
			self.__splitContainer.serialiseChildren(),
			_reprDict( _getWindowState( self ) )
		)

	# Required for editor path introspection
	def _splitContainer( self ) :
		return self.__splitContainer

## An internal eventFilter class managing all tab drag-drop events and logic.
# Tab dragging is an exception and is implemented entirely using mouse-move
# events. This was the only practical option after trying all combinations of
# Qt-only/Gaffer-only and Gaffer/Qt hybrid as:
#
#  - We wanted the visual sophistication of QTabBar.setMovable() for
#    re-arranging tabs within their parent container.
#  - Qt doesn't use its own drag mechanism for setMoveable so we have to
#    interact at a lower level that we'd otherwise like.
#  - We had issues propagating style-changes during a Gaffer drag.
#  - We can't programmatically start a Gaffer drag.
#  - Even if we could, the widget hierarchy precludes the required event
#    routing between TabbedContainer > TabBar.
#  - Using Qt's drag mechanism:
#     - Precludes cursor customisation (tried all sorts of hacks based on
#       setOverrideCursor, but it fights qdnd).
#     - Dragging out of a gaffer window fully interacts with the desktop and
#       other applications (which makes no sense).
#  - Because were only ever dragging between _SplitContainers there is no need
#    for public access to the in-drag data.
#
# As such, it is somewhat of an outlier compared to how the rest of the
# application works. To avoid polluting the code base, it has been structured
# so that as much logic and Qt interaction is contained within this class.
#
# The broad responsibilities of the _TabDragBehaviour are:
#
#  - Capture the starting state of any TabBar drag.
#  - Abort the built-in tab-move behaviour of QTabBar when the cursor leaves
#    the logical are of the TabbedContainer in-which the tab lives.
#  - Capture the mouse such that we track all events (even outside the window)
#    and ensure other widgets don't misinterpret the mouse-move as hover.
#  - Manage hover states for potential recipients during a drag operation.
#  - Coordinate the re-parenting of Tab widgets.
#  - Manage the life-cycle of detached panels created/affected by the drag.
#  - Manage cursor appearance.
#
class _TabDragBehaviour( QtCore.QObject ) :

	def __init__( self, tabbedContainer ) :

		QtCore.QObject.__init__( self )

		self.__eventMask = set( (
			QtCore.QEvent.MouseButtonPress,
			QtCore.QEvent.MouseButtonRelease,
			QtCore.QEvent.MouseMove
		) )

		self.__tabbedContainer = weakref.ref( tabbedContainer )

		self.__mouseGrabber = None
		self.__initializeDragState()

		# Install ourselves as an event filter only on the TabBar, as this
		# is the only place drags can be initiated.

		# Gaffer.Widget makes use of a custom event filter, but it is
		# initialised lazily. Fortunately, TabbedContainer connects to tabBar
		# signals during __init__ before were created, so we should then always
		# be a 'later' handler, and so called first.
		tabBar = tabbedContainer._qtWidget().tabBar()
		tabBar.installEventFilter( self )
		tabBar.setMovable( True )

	def __initializeDragState( self, qTabBar = None ) :

		# We keep a reference for the life of the drag to the originating
		# QTabBar as we have to install ourselves on another widget during
		# drag to ensure we don't loose events.
		self.__qTabBar = qTabBar

		# This tracks the transition from drag re-arrange to re-parenting
		self.__abortedInitialRearrange = False

		# As the user can re-arrange tabs before detaching/re-parenting them
		# we need to track some initial state so we can ensure we 'fix up'
		# the final state once drag is concluded.
		self.__draggedTab = None
		self.__currentTabAtDragStart = None
		self.__draggedTabOriginalIndex = -1

		# Tracks potential drop targets (TabbedContainers) so highlight state
		# can be managed during a drag.
		self.__lastTarget = None

		# Depending on the final state, some cleanup may be required, that
		# can't be performed at the time due to Qt lifetime management issues.
		self.__cleanupCallback = None

	def eventFilter( self, qObject, qEvent ) :

		qEventType = qEvent.type()
		if qEventType not in self.__eventMask :
			return False

		if qEventType == qEvent.MouseButtonPress :

			return self.__mousePress( qObject, qEvent )

		elif qEventType == qEvent.MouseMove :

			return self.__mouseMove( qObject, qEvent )

		elif qEventType == qEvent.MouseButtonRelease :

			return self.__mouseRelease( qObject, qEvent )

		return False

	def __mousePress( self, qTabBar, event ) :

		# If someone presses another mouse button whilst we're in a drag this
		# won't be the case as we get moved up to the outer parent of the
		# original tab bar once a re-parent drag has begun.
		if not isinstance( qTabBar, QtWidgets.QTabBar ) :
			return False

		if event.button() != QtCore.Qt.LeftButton :
			return False

		self.__initializeDragState( qTabBar )

		# Qt's setMovable allows you to drag a tab to the right, out of the
		# TabBar which results in the tab being clipped some fraction of the
		# way across the TabbedContainer, which looks terrible. We constrain
		# the event.pos() seen by the TabBar to keep it looking nice.
		self.__setTabDragConstraints( qTabBar, event )

		# Ensure we can leave the UI in a predictable state for the user
		# post-drag.

		self.__draggedTabOriginalIndex = qTabBar.tabAt( event.pos() )
		if self.__draggedTabOriginalIndex == -1 :
			return False

		tabbedContainer = self.__tabbedContainer()
		self.__draggedTab = tabbedContainer[ self.__draggedTabOriginalIndex ]
		self.__currentTabAtDragStart = tabbedContainer.getCurrent()

		# Drags are considered modal so this ensures no-one else gets mouse
		# events (@see qdnd-*.cpp).
		self.__captureMouse( qTabBar )

		# Only consume this event inside of our drags, this allows the native Qt
		# drag-rearrange implementation to work (which is internally done in
		# press/move/release) and for right-click, etc...
		# This works even if we've just captured the mouse we did it after this
		# event propagation chain started, so this particular one will continue...
		return self.__abortedInitialRearrange

	def __mouseRelease( self, _, event ) :

		if event.button() != QtCore.Qt.LeftButton :
			return False

		if not self.__qTabBar :
			# We can end up here from drag interactions with the close button
			return False

		try :

			# We only consume this event if we've been messing with events and
			# starting drags. This ensures we don't send the QTabBar a double release
			#
			# We need to forward this to our TabBar ourselves though as we've
			# grabbed the mouse by this point so it won't get it otherwise.
			# Don't forget qWidget is going to be the outer parent of the
			# original QTabBar, not the QTabBar.
			if not self.__abortedInitialRearrange :
				self.__forwardTabBarEvent( 'mouseReleaseEvent', event )
				return True

			sourceContainer = self.__tabbedContainer()

			if self.__lastTarget is not None :

				self.__lastTarget.addEditor( self.__draggedTab )
				self.__lastTarget.parent().setHighlighted( False )
				self.__lastTarget = None

			else :

				# Create a new window. We want the center of the tab title to be
				# roughly under the cursor

				oldSize = self.__draggedTab._qtWidget().rect()

				window = sourceContainer.ancestor( GafferUI.CompoundEditor )._createDetachedPanel()

				# We have to add the editor early so we can work out the center of
				# the tab header widget otherwise it has no parent so no tab bar...
				window.addEditor( self.__draggedTab )

				tabCenter = self.__getTabCenter( self.__draggedTab )
				windowPos = QtGui.QCursor.pos() - tabCenter
				window.setPosition( imath.V2i( windowPos.x(), windowPos.y() ) )
				window._qtWidget().resize( oldSize.width(), oldSize.height() )

				window.setVisible( True )

			# If the dragged tab wasn't current, restore the original front tab
			# We do this as the drag-rearrange/remove can change the current tab
			if self.__currentTabAtDragStart.parent() is sourceContainer :
				sourceContainer.setCurrent( self.__currentTabAtDragStart )

		finally :

			# Make sure we always clear our state regardless of how the drag ends

			GafferUI.Pointer.setCurrent( None )

			if self.__cleanupCallback is not None :
				GafferUI.EventLoop.addIdleCallback( self.__cleanupCallback )

			self.__initializeDragState()
			self.__releaseMouse()

		return True

	def __mouseMove( self, _, event ):

		if not event.buttons() & QtCore.Qt.LeftButton :
			return False

		if not self.__qTabBar :
			# We can end up here from drag interactions with the close button
			return False

		# If the user moves the mouse out of the tab bar, we need to make the
		# underlying TabBar think the user let go of the mouse so it aborts
		# any in-progress move of the tab (constrained to this TabBar) So we
		# can venture off into our own brave new world.

		if not self.__abortedInitialRearrange \
		   and self.__shouldAbortInitialRearrange( self.__qTabBar, event ) :

			self.__abortTabBarRearrange( event )
			self.__abortedInitialRearrange = True

			if sys.platform == "darwin" and len(self.__tabbedContainer()) == 1 :
				# We can't remove the last tab as the drag breaks, the trick
				# of hoisting the mouse grabber that works on linux doesn't
				# work on OSX... so we just to our best to 'hide' the tab...
				index = self.__tabbedContainer().index( self.__draggedTab )
				tabBar = self.__tabbedContainer()._qtWidget().tabBar()
				tabBar.setTabEnabled( index, False )
				self.__draggedTab._qtWidget().setVisible( False )
			else :
				# Remove the dragged tab from container to make sure its obvious to
				# the user that it will move as opposed to copy.
				self.__tabbedContainer().removeEditor( self.__draggedTab )

			GafferUI.Pointer.setCurrent( "tab" )

			# If the dragged editor was in a detached panel, that is now empty
			# remove it after we're done.
			# It'd be nice to hide it here, but haven't managed to work around
			# an issue whereby we no longer receive events once we're hidden.
			# Even spawning a new top level window and anchoring to that fails.
			detachedPanel = self.__tabbedContainer().ancestor( _DetachedPanel )
			if detachedPanel :
				self.__cleanupCallback = functools.partial(
					_TabDragBehaviour.__removeDetachedPanelIfEmpty,
					detachedPanel
				)

		elif self.__abortedInitialRearrange :

			# If we're over another TabbedContainer then we adjust focus etc...
			target = self.__targetUnderMouse( event )
			if target is not self.__lastTarget :

				# Highlight is set on the Splitter, not the TabbedContainer
				# otherwise it highlights the current tab.

				if self.__lastTarget is not None :
					self.__lastTarget.parent().setHighlighted( False )

				self.__lastTarget = target

				if target is None :
					GafferUI.Pointer.setCurrent( "detachedPanel" )
				else :
					self.__tryToRaiseWindow( target._qtWidget().windowHandle() )
					target.parent().setHighlighted( True )
					GafferUI.Pointer.setCurrent( "tab" )

		else :
			# Because we've captured the mouse, we need to pass the event through
			# to the underlying TabWidget to allow its own drag re-arrange behaviour
			self.__forwardTabBarEvent( 'mouseMoveEvent', event )

		return True

	def __captureMouse( self, initialQWidget ) :

		# There is an unusual happening, in that, if we pin all event handling
		# on the originating QTabBar, in some situations, when the last tab is
		# removed, and the mouse leaves the bounds of the parent QWindow, all
		# events stop until the mouse re-enders the window. This doesn't always
		# happen, generally when exiting the top left - and only when the last
		# tab has been removed. Turns out, if you hoist the eventFilter up to
		# the top widget in that window, it always works.

		p = initialQWidget.parent()
		while p.parent() :
			p = p.parent()

		p.grabMouse()
		p.installEventFilter( self )

		self.__mouseGrabber = p

	def __releaseMouse( self ) :

		if self.__mouseGrabber is None:
			return

		self.__mouseGrabber.removeEventFilter( self )
		self.__mouseGrabber.releaseMouse()

		self.__mouseGrabber = None

	def __shouldAbortInitialRearrange( self, qTabBar, event ) :

		# We don't reliably know where this event comes from
		pos = qTabBar.mapFromGlobal( event.globalPos() )

		if qTabBar.geometry().contains( pos ) :
			return False

		# To avoid aborting as soon as the user slips off the tab bar (which
		# can be annoying as its easily done) we don't abort if they slip into
		# the parent tab container.
		return not qTabBar.parent().geometry().contains( pos )

	def __abortTabBarRearrange( self, moveEvent ) :

		# Telling the tabbar the user has released the mouse (in the Qt
		# implementation at the time of going to press) stops the re-arrange.
		# The tabs are moved (in terms of indices) on the fly during mouseMove.
		# So they will already be in their correct places.

		fakeReleaseEvent = QtGui.QMouseEvent(
			QtCore.QEvent.MouseButtonRelease,
			self.__constrainGlobalPosTo( moveEvent.globalPos(), self.__qTabBar ),
			QtCore.Qt.LeftButton, QtCore.Qt.LeftButton,
			QtCore.Qt.NoModifier
		)
		self.__qTabBar.mouseReleaseEvent( fakeReleaseEvent )

	def __forwardTabBarEvent( self, method, event ) :

		modifiedEvent = QtGui.QMouseEvent(
			event.type(),
			# Keep the mouse in sensible bounds to prevent tab clipping
			self.__constrainGlobalPosTo( event.globalPos(), self.__qTabBar ),
			event.button(), event.buttons(),
			event.modifiers()
		)
		getattr( self.__qTabBar, method )( modifiedEvent )

	def __setTabDragConstraints( self, qTabBar, event ) :

		# We need to work out some min/max X coordinates (in the tab bars local
		# space) such that when the user drags left/right the left/right edges
		# of the tab never leave the TabBar.
		barRect = qTabBar.rect()
		tabRect = qTabBar.tabRect( qTabBar.tabAt( event.pos() ) )
		mouseX = event.pos().x()

		self.__dragMinX = mouseX - tabRect.x() # cursorToTabLeftEdge

		tabRightEdge = tabRect.x() + tabRect.width()
		if tabRightEdge > barRect.width() :
			# Already as far right as it can go
			self.__dragMaxX = mouseX
		else :
			cursorToTabRightEdge = tabRightEdge - mouseX
			self.__dragMaxX = barRect.width() - cursorToTabRightEdge

	def __targetUnderMouse( self, event ) :

		mousePos = imath.V2i( event.globalPos().x(), event.globalPos().y() )
		target = GafferUI.Widget.widgetAt( mousePos, _TabbedContainer )

		if target is not None :
			# We need to check it is from the same ScriptWindow, as we can't move
			# editors between ScriptWindows as their scriptNode references will be
			# wrong, and does it really make any sense anyway?
			ourScriptWindow = self.__tabbedContainer().ancestor( GafferUI.ScriptWindow )
			if target.ancestor( GafferUI.ScriptWindow ) is ourScriptWindow :
				return target

		return None

	def __constrainGlobalPosTo( self, globalPos, qTabBar ) :

		pos = qTabBar.mapFromGlobal( globalPos )
		return QtCore.QPoint( min( max( pos.x(), self.__dragMinX ), self.__dragMaxX ), pos.y() )

	@staticmethod
	def __removeDetachedPanelIfEmpty( detachedPanel ) :

		if detachedPanel and detachedPanel.isEmpty() :
			parentEditor = detachedPanel.ancestor( CompoundEditor )
			parentEditor._removeDetachedPanel( detachedPanel )

	@staticmethod
	def __tryToRaiseWindow( qWindow ) :

		if qWindow is None :
			return
		# Some versions of PySide2 dont suffix 'raise', lol
		if hasattr( qWindow, 'raise_' ) :
			qWindow.raise_()
		elif hasattr( qWindow, 'raise' ) :
			getattr( qWindow, 'raise' )()

	@staticmethod
	def __getTabCenter( targetTab ) :

		container = targetTab.ancestor( GafferUI.TabbedContainer )
		tabBar = container._qtWidget().tabBar()
		return tabBar.tabRect( container.index( targetTab ) ).center()

## Returns the preferred bound for a widget's window in NDC space
# (relative to the available screen area). We use the relative area to
# help with portability between platforms/window managers.
# '-1' is used to indicate windows that are on the primary screen.
# If a window is full screen, we still include the bound as otherwise
# the resultant placement when the window is un-fullscreen'd can be a bit small.
#
# Note: We use bottom-left NDC coordinates to be consistent with Gaffer
def _getWindowState( gafferWindow ) :

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

def _restoreWindowState( gafferWindow, boundData ) :

	window = gafferWindow._qtWidget().windowHandle()
	if not window :
		return

	targetScreen = QtWidgets.QApplication.primaryScreen()

	if boundData["screen"] > -1 :
		screens = QtWidgets.QApplication.screens()
		if boundData["screen"] < len(screens) :
			targetScreen = screens[ boundData["screen"] ]
			window.setScreen( targetScreen )

	if boundData["fullScreen"] :
		window.setWindowState( QtCore.Qt.WindowFullScreen )
	elif boundData["maximized"] and sys.platform != "darwin" :
		window.setWindowState( QtCore.Qt.WindowMaximized )
	else :
		window.setWindowState( QtCore.Qt.WindowNoState )
		screenGeom = targetScreen.availableGeometry()
		window.setGeometry(
			( boundData["bound"].min()[0] * screenGeom.width() ) + screenGeom.x(),
			( ( 1.0 - boundData["bound"].max()[1] ) * screenGeom.height() ) + screenGeom.y(),
			( boundData["bound"].size()[0] * screenGeom.width() ),
			( boundData["bound"].size()[1] * screenGeom.height() )
		)

def _reprDict( d ) :

	# IECore.repr has a bug in that it won't 'fix' dict values
	# TODO: replace call sites with `IECore.repr( d )` when fixed

	if not d :
		return "{}"

	return "{ %s }" % ", ".join( [
		"'%s' : %s" % ( k, IECore.repr(v) ) for k,v in d.items()
	] )


from GafferUI.Frame import Frame as _Frame

class _PinningWidget( _Frame ) :

	def __init__( self ) :

		_Frame.__init__( self, borderWidth = 0, borderStyle = GafferUI.Frame.BorderStyle.None_ )

		self._qtWidget().setFixedHeight( 15 )

		row = GafferUI.ListContainer( orientation = GafferUI.ListContainer.Orientation.Horizontal )
		with row :

			self.__bookmarkNumber = GafferUI.Label( horizontalAlignment=GafferUI.Label.HorizontalAlignment.Right )
			self.__bookmarkNumber.buttonPressSignal().connect( Gaffer.WeakMethod( self.__showEditorFocusMenu ), scoped=False )

			self.__icon = GafferUI.Button( hasFrame=False, highlightOnOver=False )
			self.__icon._qtWidget().setFixedHeight( 13 )
			self.__icon._qtWidget().setFixedWidth( 13 )
			self.__icon.buttonPressSignal().connect( Gaffer.WeakMethod( self.__showEditorFocusMenu ), scoped=False )


			self.__menuButton = GafferUI.Button( image="menuIndicator.png", hasFrame=False, highlightOnOver=False )
			self.__menuButton._qtWidget().setObjectName( "menuDownArrow" )
			self.__menuButton.buttonPressSignal().connect( Gaffer.WeakMethod( self.__showEditorFocusMenu ), scoped=False )

		self.addChild( row )

		self.buttonPressSignal().connect( Gaffer.WeakMethod( self.__showEditorFocusMenu ), scoped=False )

	@staticmethod
	def editorKeyPress( editor, event ) :

		if not isinstance( editor, GafferUI.NodeSetEditor ) :
			return False

		if event.key == "N" and not event.modifiers :
			_PinningWidget.__followNodeSelection( editor )
			return True
		elif event.key == "QuoteLeft" :
			_PinningWidget.__followFocusNode( editor )
			return True
		elif event.key == "P" and not event.modifiers :
			_PinningWidget.__pinToNodeSelection( editor )
			return True

		return False

	def update( self ) :

		editor = self.__getNodeSetEditor()
		if editor is None or editor.scriptNode() is None:
			self.setVisible( False )
			return
		else :
			self.setVisible( True )

		# Icon

		if editor.getNodeSet().isSame( editor.scriptNode().selection() ) :
			icon = "nodeSetNodeSelection.png"
		elif editor.getNodeSet().isSame( editor.scriptNode().focusSet() ) :
			icon = "nodeSetFocusNode.png"
		else :
			icon = "nodeSet%s.png"  % editor.getNodeSet().__class__.__name__

		self.__icon.setImage( icon )

		# Bookmark set numeric indicator

		bookmarkSet = self.__getBookmarkSet()
		if bookmarkSet is not None :
			self.__bookmarkNumber.setText( "%d" % bookmarkSet.getBookmark() )
			self.__bookmarkNumber.setVisible( True )
		else :
			self.__bookmarkNumber.setVisible( False )
			self.__bookmarkNumber.setText( "" )

		self._repolish()

	# Disclaimer:
	# In order to defer the highlighting of related editors, avoiding brief
	# flashes whilst general mousing around, we abuse the tooltip mechanism.
	# Otherwise, we'd have to reimplement the entire set-timeout/cancel/etc...
	# behaviour or figure some way to hook up to Qt's tooltip event directly.
	# As this is technically a private implementation class, no one should be
	# calling getToolTip themselves anyway so were going to try and get away
	# with it.  We'll have to fix this up should we need to call this in other
	# presentation scenarios.
	def getToolTip( self ) :

		editor = self.__getNodeSetEditor()
		if editor is None :
			return ""

		toolTipElements = []

		nodeSet = editor.getNodeSet()
		if nodeSet == editor.scriptNode().selection() :
			toolTipElements.append( "" )
			toolTipElements.append( "Following the node selection." )
		if nodeSet == editor.scriptNode().focusSet() :
			toolTipElements.append( "" )
			toolTipElements.append( "Following the Focus Node." )
		elif isinstance( nodeSet, Gaffer.NumericBookmarkSet ) :
			toolTipElements.append( "" )
			toolTipElements.append( "Following Numeric Bookmark %d." % nodeSet.getBookmark()  )
		elif isinstance( nodeSet, Gaffer.StandardSet ) :
			toolTipElements.append( "" )
			n = len(nodeSet)
			if n == 0 :
				s = "Pinned to nothing."
			else :
				s = "Pinned to %d node%s." % ( n, "" if n == 1 else "s" )
			toolTipElements.append( s )

		return "\n".join( toolTipElements )

	@staticmethod
	def __pinToNodeSelection( editor, *unused ) :

		if not isinstance( editor, GafferUI.NodeSetEditor ) :
			editor = editor()

		editor.setNodeSet( Gaffer.StandardSet( list( editor.scriptNode().selection() ) ) )

	@staticmethod
	def __followNodeSelection( editor, *unused ) :

		if not isinstance( editor, GafferUI.NodeSetEditor ) :
			editor = editor()

		editor.setNodeSet( editor.scriptNode().selection() )

	@staticmethod
	def __followFocusNode( editor, *unused ) :

		if not isinstance( editor, GafferUI.NodeSetEditor ) :
			editor = editor()

		editor.setNodeSet( editor.scriptNode().focusSet() )

	def __showEditorFocusMenu( self, *unused ) :

		e = self.__getNodeSetEditor()

		m = IECore.MenuDefinition()

		self.__addStandardItems( e, m )
		CompoundEditor.nodeSetMenuSignal()( e, m )

		self.__pinningMenu = GafferUI.Menu( m, title = "Editor Focus" )

		buttonBound = self.__icon.bound()
		self.__pinningMenu.popup(
			parent = self.ancestor( GafferUI.Window ),
			position = imath.V2i( buttonBound.min().x, buttonBound.max().y )
		)

		return True

	def __addStandardItems( self, editor, m ) :

		selection = editor.scriptNode().selection()

		if len(selection) == 0 :
			label = "Pin To Nothing"
		elif len(selection) == 1 :
			label = "Pin %s" % selection[0].getName()
		else :
			label = "Pin %d Selected Nodes" % len(selection)

		m.append( "/Pin Node Selection", {
			"command" : functools.partial( self.__pinToNodeSelection, weakref.ref( editor ) ),
			"label" : label,
			"shortCut" : "p"
		} )

		m.append( "/Follow Divider", { "divider" : True, "label" : "Follow" } )

		m.append( "/Focus Node", {
			"command" : functools.partial( self.__followFocusNode, weakref.ref( editor ) ),
			"checkBox" : editor.getNodeSet().isSame( editor.scriptNode().focusSet() ),
			"shortCut" : "`"
		} )

		m.append( "/Node Selection", {
			"command" : functools.partial( self.__followNodeSelection, weakref.ref( editor ) ),
			"checkBox" : editor.getNodeSet().isSame( editor.scriptNode().selection() ),
			"shortCut" : "n"
		} )

	def __getNodeSetEditor( self ) :

		tabbedContainer = self.ancestor( _TabbedContainer )
		editor = tabbedContainer.getCurrent()
		if editor is not None and isinstance( editor, GafferUI.NodeSetEditor ) :
			return editor

		return None

	def __getBookmarkSet( self ) :

		editor = self.__getNodeSetEditor()
		if editor is None:
			return None

		nodeSet = editor.getNodeSet()
		if isinstance( nodeSet, Gaffer.NumericBookmarkSet ) :
			return nodeSet

		return None
