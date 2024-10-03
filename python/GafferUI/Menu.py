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

import inspect
import enum
import functools
import weakref
import types
import re

import IECore

import Gaffer
import GafferUI

from Qt import QtCore
from Qt import QtGui
from Qt import QtWidgets

class Menu( GafferUI.Widget ) :

	## A dynamic menu constructed from the supplied IECore.MenuDefinition.
	#
	# Along with the standard IECore.MenuItemDefinition fields, the Gaffer Menu
	# implementation also supports:
	#
	#  - 'enter' and 'leave', to optionally provide callables to be invoked
	#    when the mouse enters and leaves an item's on-screen representation.
	#
	# - 'label' in conjunction with 'divider' = True, displays a textual
	#   divider as opposed to a simple line.
	#
	# - 'hasShortCuts' = False in conjunction with `subMenu`, instructs the Menu
	#   to ignore the subMenu when building for keyboard shortcut discovery.
	#   This can avoid long blocking waits when the user first presses a key whilst
	#   the action map is built if your subMenu is particularly slow to build.
	def __init__( self, definition, _qtParent=None, searchable=False, title=None, **kw ) :

		GafferUI.Widget.__init__( self, _Menu( _qtParent ), **kw )

		self.__searchable = searchable

		self.__title = title
		# this property is used by the stylesheet to fix up menu padding bugs
		self._qtWidget().setProperty( "gafferHasTitle", GafferUI._Variant.toVariant( title is not None ) )

		self._qtWidget().__definition = definition
		self._qtWidget().aboutToShow.connect( Gaffer.WeakMethod( self.__show ) )
		self._qtWidget().aboutToHide.connect( Gaffer.WeakMethod( self.__hide ) )
		self._qtWidget().hovered.connect( Gaffer.WeakMethod( self.__actionHovered ) )

		self.__lastHoverAction = None

		if searchable :
			self.__lastAction = None

		self._setStyleSheet()

		self.__popupParent = None
		self.__popupPosition = None

		self.__previousSearchText = ''
		self.__cachedSearchStructureKeys = []


	## Displays the menu at the specified position, and attached to
	# an optional parent. If position is not specified then it
	# defaults to the current cursor position. If forcePosition is specified
	# then the menu will be shown exactly at the requested position, even if
	# doing so means some of it will be off screen. If grabFocus is False, then
	# the menu will not take keyboard events unless the first such event is a
	# press of the up or down arrows.
	def popup( self, parent=None, position=None, forcePosition=False, grabFocus=True, modal=False ) :

		if parent is not None :
			self.__popupParent = weakref.ref( parent )
		else :
			self.__popupParent = None

		if position is None :
			position = GafferUI.Widget.mousePosition()

		self.__popupPosition = position

		position = QtCore.QPoint( position.x, position.y )

		self._qtWidget().keyboardMode = _Menu.KeyboardMode.Grab if grabFocus else _Menu.KeyboardMode.Close

		if modal :
			self._qtWidget().exec_( position )
		else :
			self._qtWidget().popup( position )

		# qt is helpful and tries to keep you menu on screen, but this isn't always
		# what you want, so we override the helpfulness if requested.
		if forcePosition :
			self._qtWidget().move( position )

	## Reimplemented from Widget to report the parent passed to popup().
	def parent( self ) :

		if self.__popupParent is not None :
			p = self.__popupParent()
			if p is not None :
				return p

		return GafferUI.Widget.parent( self )

	## Returns the position for the last popup request, before it
	# was adjusted to keep the menu on screen.
	def popupPosition( self, relativeTo = None ) :

		result = self.__popupPosition
		if result is None :
			return result

		if relativeTo is not None :
			result = result - relativeTo.bound().min()

		return result

	def searchable( self ) :

		return self.__searchable

	def __argNames( self, function ) :

		if isinstance( function, types.FunctionType ) :
			return inspect.getfullargspec( function ).args
		elif isinstance( function, types.MethodType ) :
			return self.__argNames( function.__func__ )[1:]
		elif isinstance( function, Gaffer.WeakMethod ) :
			return self.__argNames( function.method() )[1:]
		elif isinstance( function, functools.partial ) :
			return self.__argNames( function.func )

		return []

	def __actionTriggered( self, qtActionWeakRef, toggled ) :

		qtAction = qtActionWeakRef()
		item = qtAction.item

		if not self.__evaluateItemValue( item.active ) :
			# Because an item's active status can change
			# dynamically, the status can change between
			# the time the menu is built and the time a
			# shortcut triggers an action. The shortcut
			# triggering code in MenuBar therefore ignores
			# the active status, and we early-out for
			# inactive items at the last minute here.
			return

		args = []
		kw = {}

		commandArgs = self.__argNames( item.command )

		if "menu" in commandArgs :
			kw["menu"] = self

		if "checkBox" in commandArgs :
			kw["checkBox"] = toggled
		elif qtAction.isCheckable() :
			# workaround for the fact that curried functions
			# don't have arguments we can query right now. we
			# just assume that if it's a check menu item then
			# there must be an argument to receive the check
			# status.
			args.append( toggled )

		item.command( *args, **kw )

	def __show( self ) :

		# we rebuild each menu every time it's shown, to support the use of callable items to provide
		# dynamic submenus and item states.
		self.__build( self._qtWidget() )

		if self.__searchable :
			# Searchable menus need to initialize a search structure so they can be searched without
			# expanding each submenu. The definition is fully expanded, so dynamic submenus that
			# exist will be expanded and searched.
			self.__searchStructure = {}
			self.__initSearch( self._qtWidget().__definition )

			# Searchable menus require an extra submenu to display the search results.
			searchWidget = QtWidgets.QWidgetAction( self._qtWidget() )
			searchWidget.setObjectName( "GafferUI.Menu.__searchWidget" )
			self.__searchMenu = _Menu( self._qtWidget(), "" )
			self.__searchMenu.aboutToShow.connect( Gaffer.WeakMethod( self.__searchMenuShow ) )
			self.__searchLine = QtWidgets.QLineEdit()
			self.__searchLine.setAttribute( QtCore.Qt.WA_MacShowFocusRect, False )
			self.__searchLine.textEdited.connect( Gaffer.WeakMethod( self.__updateSearchMenu ) )
			self.__searchLine.returnPressed.connect( Gaffer.WeakMethod( self.__searchReturnPressed ) )
			self.__searchLine.setObjectName( "gafferSearchField" )
			self.__searchLine.setPlaceholderText( "Search..." )
			if self.__lastAction :
				self.__searchLine.setText( self.__lastAction.text() )
				self.__searchMenu.setDefaultAction( self.__lastAction )

			self.__searchLine.selectAll()
			searchWidget.setDefaultWidget( self.__searchLine )

			insertIndex = 1 if self.__title else 0
			firstAction = self._qtWidget().actions()[insertIndex] if len( self._qtWidget().actions() ) > insertIndex else None
			self._qtWidget().insertAction( firstAction, searchWidget )
			self._qtWidget().insertSeparator( firstAction )
			self._qtWidget().setActiveAction( searchWidget )
			self.__searchLine.setFocus()

	def __hide( self ) :

		if self.__searchable and self.__searchMenu :
			self.__searchLine.clearFocus()
			self.__searchMenu.hide()

		self.__doActionUnhover()
		self.__lastHoverAction = None

	# May be called to fully build the menu /now/, rather than only do it lazily
	# when it's shown. This is used by the MenuBar. forShortCuts should be set
	# if the build is for short cut discovery as it will skip dynamic subMenus
	# that declare they have no shortcuts.
	#   See https://github.com/GafferHQ/gaffer/issues/3651)
	def _buildFully( self, forShortCuts=False ) :

		self.__build( self._qtWidget(), recurse=True, forShortCuts=forShortCuts )

	def __build( self, qtMenu, recurse=False, forShortCuts=False ) :

		if isinstance( qtMenu, weakref.ref ) :
			qtMenu = qtMenu()

		definition = qtMenu.__definition
		if callable( definition ) :
			if "menu" in self.__argNames( definition ) :
				definition = definition( self )
			else :
				definition = definition()

		qtMenu.clear()

		needsBottomSpacer = False

		done = set()
		for path, item in definition.items() :

			pathComponents = path.strip( "/" ).split( "/" )
			name = pathComponents[0]

			if not name in done :

				if len( pathComponents ) > 1 :

					# it's an intermediate submenu we need to make
					# to construct the path to something else

					subMenu = _Menu( qtMenu, name )
					qtMenu.addMenu( subMenu )

					subMenu.__definition = definition.reRooted( "/" + name + "/" )
					subMenu.aboutToShow.connect( IECore.curry( Gaffer.WeakMethod( self.__build ), weakref.ref( subMenu ) ) )
					if recurse :
						self.__build( subMenu, recurse, forShortCuts=forShortCuts )

				else :

					if item.subMenu is not None :

						# Skip any subMenus that declare they have no short cuts.
						# _buildFully can be called blocking on the UI thread so
						# this facilities to skip potentially expensive custom menus.
						if forShortCuts and not getattr( item, 'hasShortCuts', True ) :
							continue

						subMenu = _Menu( qtMenu, name )
						active = self.__evaluateItemValue( item.active )
						subMenu.setEnabled( active )

						icon = getattr( item, "icon", None )
						if icon is not None :
							if isinstance( icon, str ) :
								image = GafferUI.Image( icon )
							else :
								assert( isinstance( icon, GafferUI.Image ) )
								image = icon
							subMenu.setIcon( QtGui.QIcon( image._qtPixmap() ) )

						qtMenu.addMenu( subMenu )

						subMenu.__definition = item.subMenu
						subMenu.aboutToShow.connect( IECore.curry( Gaffer.WeakMethod( self.__build ), weakref.ref( subMenu ) ) )
						if recurse :
							self.__build( subMenu, recurse, forShortCuts=forShortCuts )

					else :

						# it's not a submenu
						action = self.__buildAction( item, name, qtMenu )

						# Wrangle some divider/menu spacing issues
						if isinstance( action, _DividerAction ) :
							if len( qtMenu.actions() ) :
								qtMenu.addAction( _SpacerAction( qtMenu ) )
							elif action.hasText :
								qtMenu.setProperty( "gafferHasLeadingLabelledDivider", GafferUI._Variant.toVariant( True ) )
								needsBottomSpacer = True

						qtMenu.addAction( action )

				done.add( name )

		# add a title if required.
		if self.__title is not None and qtMenu is self._qtWidget() :

			titleWidget = QtWidgets.QLabel( self.__title )
			titleWidget.setIndent( 0 )
			titleWidget.setObjectName( "gafferMenuTitle" )
			titleWidgetAction = QtWidgets.QWidgetAction( qtMenu )
			titleWidgetAction.setDefaultWidget( titleWidget )
			titleWidgetAction.setEnabled( False )
			qtMenu.insertAction( qtMenu.actions()[0], titleWidgetAction )
			needsBottomSpacer = True

		if needsBottomSpacer :
			qtMenu.addAction( _SpacerAction( qtMenu ) )

		self._repolish()

	def __buildAction( self, item, name, parent ) :

		label = name
		with IECore.IgnoredExceptions( AttributeError ) :
			label = item.label

		if item.divider :
			qtAction = _DividerAction( item, parent )
		else :
			qtAction = _Action( item, label, parent )

		if item.checkBox is not None :
			qtAction.setCheckable( True )
			checked = self.__evaluateItemValue( item.checkBox )
			# if a callable was passed as the "checkBox" parameter it may return None
			if checked is not None :
				qtAction.setChecked( checked )

		if item.command :

			if item.checkBox :
				signal = qtAction.toggled[bool]
			else :
				signal = qtAction.triggered[bool]

			if self.__searchable :
				signal.connect( IECore.curry( Gaffer.WeakMethod( self.__menuActionTriggered ), qtAction ) )

			signal.connect( IECore.curry( Gaffer.WeakMethod( self.__actionTriggered ), weakref.ref( qtAction ) ) )

		active = self.__evaluateItemValue( item.active )
		qtAction.setEnabled( active )

		shortCut = getattr( item, "shortCut", None )
		if shortCut is not None :
			qtAction.setShortcuts( [ QtGui.QKeySequence( s.strip() ) for s in shortCut.split( "," ) ] )
			# If we allow shortcuts to be created at the window level (the default),
			# then we can easily get into a situation where our shortcuts conflict
			# with those of the host when embedding our MenuBars in an application like Maya.
			# Here we're limiting the scope so that conflicts don't occur, deferring
			# to the code in MenuBar to manage triggering of the action with manual
			# shortcut processing.
			qtAction.setShortcutContext( QtCore.Qt.WidgetShortcut )

		# when an icon file path is defined in the menu definition
		icon = getattr( item, "icon", None )
		# Qt is unable to display a checkbox and icon at the same time.
		# Unhelpfully, the icon overrides the checkbox so we only display
		# the icon when there is no checkbox.
		if icon is not None and not qtAction.isChecked() :
			if isinstance( icon, str ) :
				image = GafferUI.Image( icon )
			else :
				assert( isinstance( icon, GafferUI.Image ) )
				image = icon
			qtAction.setIcon( QtGui.QIcon( image._qtPixmap() ) )

		if item.description :
			qtAction.setStatusTip( item.description )

		return qtAction

	def __initSearch( self, definition, dirname = "" ) :

		if callable( definition ) :
			if "menu" in self.__argNames( definition ) :
				definition = definition( self )
			else :
				definition = definition()

		done = set()
		for path, item in definition.items() :

			name = path.split( "/" )[-1]
			fullPath = dirname + path

			if item.divider or not getattr( item, "searchable", True ) :
				continue

			elif item.subMenu is not None :

				self.__initSearch( item.subMenu, dirname=fullPath )

			else :
				label = getattr( item, "searchText", getattr( item, "label", name ) )
				if label in self.__searchStructure :
					self.__searchStructure[label].append( ( item, fullPath ) )
				else :
					self.__searchStructure[label] = [ ( item, fullPath ) ]

	def __evaluateItemValue( self, itemValue ) :

		if callable( itemValue ) :
			kwArgs = {}
			if "menu" in self.__argNames( itemValue ) :
				kwArgs["menu"] = self
			itemValue = itemValue( **kwArgs )

		return itemValue

	def __getSearchBoxErrorState(self):

		return GafferUI._Variant.fromVariant( self.__searchLine.property( "gafferError" ) ) or False

	def __setSearchBoxErrorState(self, errored):

		if errored is self.__getSearchBoxErrorState():
			return

		self.__searchLine.setProperty( "gafferError", GafferUI._Variant.toVariant( errored ) )
		self._repolish()

	def __updateSearchMenu( self, text ) :

		if not self.__searchable :
			return

		self.__searchMenu.setUpdatesEnabled( False )
		self.__searchMenu.hide()
		self.__searchMenu.clear()
		self.__searchMenu.setDefaultAction( None )

		if not text :
			return

		text = str(text)
		errored = False
		matched = self.__matchingActions( text )

		if not matched:

			errored = True

			if len( text ) > 1:
				matched = self.__matchingActions( text[:-1] )

			# cut of after first character that gives no results anymore
			if not matched and len( text ) > 2:
				self.__searchLine.setText( text[:-1] )
				matched = self.__matchingActions( text[:-2] )

		self.__setSearchBoxErrorState(errored)

		# sort first by weight, then position of the first matching character, then alphabetically
		matchedItems = [ ( k, v['pos'], v['weight'], v['actions']  ) for k, v in matched.items() ]
		matchedItems = sorted(matchedItems, key = lambda x : (x[2], x[1], x[0]))

		numActions = 0
		maxActions = 30
		overflowMenu = None

		for match in matchedItems:

			name = match[0]
			actions = match[3]

			if len( actions ) > 1 :
				for ( action, path ) in actions :
					action.setText( self.__disambiguate( name, path ) )

			# since all have the same name, sorting alphabetically on disambiguation text
			for ( action, path ) in sorted( actions, key = lambda x : x[0].text() ) :

				if numActions < maxActions :
					self.__searchMenu.addAction( action )
				else :
					if overflowMenu is None :
						self.__searchMenu.addSeparator()
						overflowMenu = _Menu( self.__searchMenu, "More Results" )
						self.__searchMenu.addMenu( overflowMenu )
					overflowMenu.addAction( action )

				numActions += 1

		finalActions = self.__searchMenu.actions()
		if len(finalActions) :
			self.__searchMenu.setDefaultAction( finalActions[0] )
			self.__searchMenu.setActiveAction( finalActions[0] )
			pos = self.__searchLine.mapToGlobal( QtCore.QPoint( 0, 0 ) )
			self.__searchMenu.popup( QtCore.QPoint( pos.x() + self.__searchLine.width(), pos.y() ) )
			self.__searchLine.setFocus()
			self.__searchMenu.setUpdatesEnabled( True )

	def __matchingActions( self, searchText ) :

		searchText = searchText[:99]  # re matching only supports up to 100 groups
		results = {}

		# split on spaces so we can search words in random order with a lookaround
		# and do a non greedy search of all the characters.
		# for example: (?=.*?(t).*?(e).*?(s).*?(t))(?=.*?(w).*?(o).*?(r).*?(d))
		spaceSeparated = [ s for s in searchText.split(' ') if s ]
		if not spaceSeparated:
			return results

		wordLengths = [ len(s) for s in spaceSeparated ]
		wordSearch =  [ '.*?' + '.*?'.join( [ '(' + re.escape(s[i]) + ')' for i in range(len(s))] ) for s in spaceSeparated ]
		regex = ''.join( [ '(?=' + s + ')' for s in wordSearch ] )

		matcher = re.compile( regex, re.IGNORECASE )

		# Narrow down the cachedSearchStructure with every typed character, so we only search previously matched items.
		if searchText.startswith( self.__previousSearchText ) and len( searchText ) != 1:
			searchStructureKeys = self.__cachedSearchStructureKeys
		# Revert that cache to the full searchStructure otherwise
		else:
			searchStructureKeys = self.__searchStructure.keys()

		self.__cachedSearchStructureKeys = []

		for name in searchStructureKeys :

			match = matcher.search( name )

			if match :

				weight = 0
				wordWeight = 1
				currentWordPos = 0

				# go through match groups per word
				# for the weight calculation per word we reward:
				# - (d) short distances of the matching characters (penalizing gaps)
				# - (p) small index of the matches (matches in the beginning of the word)
				# - (wordWeight) small index of the space separated word
				for wordLength in wordLengths:

					wordGroups = range( currentWordPos+1, currentWordPos+wordLength+1 )
					hitPositions = [ match.span( g )[0] for g in wordGroups ]
					hitPositionDistances = [ j - i for i, j in zip( hitPositions[:-1], hitPositions[1:] ) ]

					weight += wordWeight * sum( [ ( p + 1 ) * d for p, d in zip( hitPositions[:-1], hitPositionDistances ) ] )

					currentWordPos += wordLength
					wordWeight += 1

				# position of the first matching character
				pos = match.span( 1 )[0]

				self.__cachedSearchStructureKeys.append( name )

				for item, path in self.__searchStructure[name] :

					action = self.__buildAction( item, name, self.__searchMenu )
					if name not in results :
						results[name] = { "pos" : pos, "weight" : weight, "actions" : [], 'grp' : match.groups() }

					results[name]["actions"].append( ( action, path ) )


		self.__previousSearchText = searchText

		return results

	def __disambiguate( self, name, path, remove=False ) :

		result = str(name).partition( " (" + path + ")" )[0]
		if remove :
			return result

		return result + " (" + path + ")"

	def __searchMenuShow( self ) :

		self.__searchMenu.keyboardMode = _Menu.KeyboardMode.Forward

	def __searchReturnPressed( self ) :

		if self.__searchMenu and self.__searchMenu.defaultAction() :
			self.__searchMenu.defaultAction().trigger()

	def __menuActionTriggered( self, action, checked ) :

		self.__lastAction = action if action.objectName() != "GafferUI.Menu.__searchWidget" else None
		if self.__lastAction is not None :
			self.__searchMenu.addAction( self.__lastAction )

		self._qtWidget().hide()

	def __actionHovered( self, action ) :

		# Hovered is called every time the mouse moves
		if action == self.__lastHoverAction :
			return

		self.__doActionUnhover()

		self.__lastHoverAction = action

		# Sub-menus are normal QActions
		if isinstance( action, _Action ) and hasattr( action.item, "enter" ) :
			action.item.enter()

	def __doActionUnhover( self ) :

		if self.__lastHoverAction is None :
			return

		# Sub-menus are normal QActions
		if isinstance( self.__lastHoverAction, _Action ) and hasattr( self.__lastHoverAction.item, "leave" ) :
			self.__lastHoverAction.item.leave()

		self.__lastHoverAction = None

# When we stuck arbitrary attributes on QAction (eg. __item) these would get
# lost when the action was returned by Qt via a signal (eg: menu.hovered).
# Creating a subclass seemed to resolve this. Never got to the bottom of why,
# as the addresses of the python objects _seemed_ to be the same.
class _Action( QtWidgets.QAction ) :

	def __init__( self, item, *args, **kwarg ) :
		self.item = item
		QtWidgets.QAction.__init__( self, *args, **kwarg )

class _DividerAction( QtWidgets.QWidgetAction ) :

	def __init__( self, item, *args, **kwarg ) :

		self.item = item

		QtWidgets.QWidgetAction.__init__( self, *args, **kwarg )

		if hasattr( item, 'label' ) and item.label :
			titleWidget = QtWidgets.QLabel( item.label )
			titleWidget.setIndent( 0 )
			titleWidget.setObjectName( "gafferMenuLabeledDivider" )
			titleWidget.setEnabled( False )
			self.setDefaultWidget( titleWidget )
			self.hasText = True
		else :
			self.setSeparator( True )
			self.hasText = False

class _SpacerAction( QtWidgets.QWidgetAction ) :

	def __init__( self, *args, **kwarg ) :

		QtWidgets.QWidgetAction.__init__( self, *args, **kwarg )
		# qt stylesheets ignore the padding-bottom for menus and
		# use padding-top instead. we need padding-top to be 0 when
		# we have a title, so we have to fake the bottom padding like so.
		spacerWidget = QtWidgets.QWidget()
		spacerWidget.setFixedSize( 5, 5 )
		self.setDefaultWidget( spacerWidget )
		self.setEnabled( False )

class _Menu( QtWidgets.QMenu ) :

	KeyboardMode = enum.Enum( "KeyboardMode", [ "Grab", "Close", "Forward" ] )

	def __init__( self, parent, title=None ) :

		QtWidgets.QMenu.__init__( self, parent )

		if title is not None :
			self.setTitle( title )

		self.keyboardMode = _Menu.KeyboardMode.Grab

	def event( self, qEvent ) :

		if qEvent.type() == QtCore.QEvent.ToolTip :
			action = self.actionAt( qEvent.pos() )
			if action and action.statusTip() :
				QtWidgets.QToolTip.showText( qEvent.globalPos(), action.statusTip(), self )
				return True
			elif QtWidgets.QToolTip.isVisible() :
				QtWidgets.QToolTip.hideText()
				return True

		return QtWidgets.QMenu.event( self, qEvent )

	def keyPressEvent( self, qEvent ) :

		if qEvent.key() == QtCore.Qt.Key_Escape :
			parent = self
			while isinstance( parent, _Menu ) :
				parent.close()
				parent = parent.parentWidget()

			return

		if not self.keyboardMode == _Menu.KeyboardMode.Grab :

			if qEvent.key() == QtCore.Qt.Key_Up or qEvent.key() == QtCore.Qt.Key_Down :
				self.keyboardMode = _Menu.KeyboardMode.Grab
			else :
				if self.keyboardMode == _Menu.KeyboardMode.Close :
					self.hide()

				# pass the event on to the rightful recipient
				app = QtWidgets.QApplication.instance()
				if app.focusWidget() != self :
					app.sendEvent( app.focusWidget(), qEvent )
					return

		QtWidgets.QMenu.keyPressEvent( self, qEvent )

