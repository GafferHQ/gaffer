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
import weakref
import types
import re

import IECore

import Gaffer
import GafferUI

QtCore = GafferUI._qtImport( "QtCore" )
QtGui = GafferUI._qtImport( "QtGui" )

class Menu( GafferUI.Widget ) :

	def __init__( self, definition, _qtParent=None, searchable=False, **kw ) :
	
		GafferUI.Widget.__init__( self, _Menu( _qtParent ), **kw )
		
		self.__definition = definition
		self.__searchable = searchable
		
		self._qtWidget().aboutToShow.connect( Gaffer.WeakMethod( self.__show ) )
		
		if searchable :
			self._qtWidget().aboutToHide.connect( Gaffer.WeakMethod( self.__hide ) )
			self._qtWidget().triggered.connect( Gaffer.WeakMethod( self.__menuActionTriggered ) )
			self.__lastAction = None
		
		self._setStyleSheet()		
		
		self.__popupParent = None

	## Displays the menu at the specified position, and attached to
	# an optional parent. If position is not specified then it 
	# defaults to the current cursor position. If forcePosition is specified
	# then the menu will be shown exactly at the requested position, even if
	# doing so means some of it will be off screen. If grabFocus is False, then
	# the menu will not take keyboard events unless the first such event is a
	# press of the up or down arrows.
	def popup( self, parent=None, position=None, forcePosition=False, grabFocus=True ) :
	
		if parent is not None :
			self.__popupParent = weakref.ref( parent )
		else :
			self.__popupParent = None
			
		if position is None :
			position = QtGui.QCursor.pos()
		else :
			position = QtCore.QPoint( position.x, position.y )

		self._qtWidget().keyboardMode = _Menu.KeyboardMode.Grab if grabFocus else _Menu.KeyboardMode.Close
			
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
	
	def searchable( self ) :
		
		return self.__searchable
	
	def __argNames( self, function ) :
	
		if isinstance( function, types.FunctionType ) :
			return inspect.getargspec( function )[0]
		elif isinstance( function, Gaffer.WeakMethod ) :
			return inspect.getargspec( function.method() )[0][1:]
		
		return []
		
	def __commandWrapper( self, qtAction, command, active, toggled ) :
	
		if not self.__evaluateItemValue( active ) :
			return
		
		args = []
		kw = {}
		
		commandArgs = self.__argNames( command )
		
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
		
		command( *args, **kw )
	
	def __show( self ) :
		
		# we rebuild each menu every time it's shown, to support the use of callable items to provide
		# dynamic submenus and item states.
		self.__build( self._qtWidget(), self.__definition )
		
		if self.__searchable :
			# Searchable menus need to initialize a search structure so they can be searched without
			# expanding each submenu. The definition is fully expanded, so dynamic submenus that
			# exist will be expanded and searched.
			self.__searchStructure = {}
			self.__initSearch( self.__definition )
			
			# Searchable menus require an extra submenu to display the search results. 
			searchWidget = QtGui.QWidgetAction( self._qtWidget() )
			searchWidget.setObjectName( "GafferUI.Menu.__searchWidget" )
			self.__searchMenu = _Menu( self._qtWidget(), "" )
			self.__searchMenu.aboutToShow.connect( Gaffer.WeakMethod( self.__searchMenuShow ) )
			self.__searchMenu.triggered.connect( Gaffer.WeakMethod( self.__menuActionTriggered ) )
			self.__searchLine = QtGui.QLineEdit()
			self.__searchLine.textEdited.connect( Gaffer.WeakMethod( self.__updateSearchMenu ) )
			self.__searchLine.returnPressed.connect( Gaffer.WeakMethod( self.__searchReturnPressed ) )
			self.__searchLine.setObjectName( "search" )
			self.__searchLine.setPlaceholderText( "Search..." )
			if self.__lastAction :
				self.__searchLine.setText( self.__lastAction.text() )
				self.__searchMenu.setDefaultAction( self.__lastAction )
			
			self.__searchLine.selectAll()
			searchWidget.setDefaultWidget( self.__searchLine )
			
			firstAction = self._qtWidget().actions()[0]
			self._qtWidget().insertAction( firstAction, searchWidget )
			self._qtWidget().insertSeparator( firstAction )
			self._qtWidget().setActiveAction( searchWidget )
			self.__searchLine.setFocus()
	
	def __hide( self ) :
		
		if self.__searchable and self.__searchMenu :
			self.__searchMenu.hide()
	
	# May be called to fully build the menu /now/, rather than only do it lazily
	# when it's shown. This is used by the MenuBar to make sure that keyboard shortcuts
	# are available even before the menu has been shown.
	def _buildFully( self ) :
	
		# Because we're building the menu before it's shown, we don't really know whether
		# the items should be active or not - those which pass a callable for item.active
		# may change status all the time, and we have no way of knowing. So we pass
		# activeOverride=True so that all menu items are active while they're not on screen.
		# We early-out in __commandWrapper if we later find out that a keyboard shortcut
		# has triggered an item which is currently inactive (although we told qt it was
		# active). See also hideEvent below().

		self.__build( self._qtWidget(), self.__definition, activeOverride=True, recurse=True )

	def __build( self, qtMenu, definition, activeOverride=None, recurse=False ) :
		
		if callable( definition ) :
			if "menu" in self.__argNames( definition ) :
				definition = definition( self )
			else :
				definition = definition()
			
		qtMenu.clear()
			
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
					
					subMenuDefinition = definition.reRooted( "/" + name + "/" )					
					subMenu.aboutToShow.connect( IECore.curry( Gaffer.WeakMethod( self.__build ), subMenu, subMenuDefinition ) )
					if recurse :
						self.__build( subMenu, subMenuDefinition, activeOverride, recurse )
					
				else :
				
					if item.subMenu is not None :
										
						subMenu = _Menu( qtMenu, name )
						qtMenu.addMenu( subMenu )
					
						subMenu.aboutToShow.connect( IECore.curry( Gaffer.WeakMethod( self.__build ), subMenu, item.subMenu ) )
						if recurse :
							self.__build( subMenu, item.subMenu, activeOverride, recurse )
							
					else :
						
						# it's not a submenu
						qtMenu.addAction( self.__buildAction( item, name, qtMenu, activeOverride ) )
				
				done.add( name )
	
	def __buildAction( self, item, name, parent, activeOverride=None ) :
		
		label = name
		with IECore.IgnoredExceptions( AttributeError ) :
			label = item.label
		
		qtAction = QtGui.QAction( label, parent )
		
		if item.checkBox is not None :
			qtAction.setCheckable( True )
			checked = self.__evaluateItemValue( item.checkBox )
			qtAction.setChecked( checked )
		
		if item.divider :
			qtAction.setSeparator( True )
		
		if item.command :
			
			if item.checkBox :	
				signal = qtAction.toggled[bool]
			else :
				signal = qtAction.triggered[bool]
			
			signal.connect( IECore.curry( Gaffer.WeakMethod( self.__commandWrapper ), qtAction, item.command, item.active ) )
		
		active = item.active if activeOverride is None else activeOverride
		active = self.__evaluateItemValue( active )
		qtAction.setEnabled( active )
		
		shortCut = getattr( item, "shortCut", None )
		if shortCut is not None :
			qtAction.setShortcuts( [ QtGui.QKeySequence( s.strip() ) for s in shortCut.split( "," ) ] )
		
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
			if "menu" in inspect.getargspec( itemValue )[0] :
				kwArgs["menu"] = self
			itemValue = itemValue( **kwArgs )
				
		return itemValue
	
	def __updateSearchMenu( self, text ) :
		
		if not self.__searchable :
			return
		
		self.__searchMenu.setUpdatesEnabled( False )
		self.__searchMenu.hide()
		self.__searchMenu.clear()
		self.__searchMenu.setDefaultAction( None )
		
		if not text :
			return
		
		matched = self.__matchingActions( str(text) )
		
		# sorting on match position within the name
		matchIndexMap = {}
		for name, info in matched.items() :
			if info["pos"] not in matchIndexMap :
				matchIndexMap[info["pos"]] = []
			matchIndexMap[info["pos"]].append( ( name, info["actions"] ) )
		
		numActions = 0
		maxActions = 30
		overflowMenu = None
		
		# sorting again alphabetically within each match position
		for matchIndex in sorted( matchIndexMap ) :
			
			for ( name, actions ) in sorted( matchIndexMap[matchIndex], key = lambda x : x[0] ) :
				
				if len(actions) > 1 :
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
	
	def __matchingActions( self, searchText, path = "" ) :
		
		results = {}
		# find all actions matching a case-insensitive regex
		matcher = re.compile( "".join( [ "[%s|%s]" % ( c.upper(), c.lower() ) for c in searchText ] ) )
		
		for name in self.__searchStructure :
			
			match = matcher.search( name )
			if match :
				
				for item, path in self.__searchStructure[name] :
					
					action = self.__buildAction( item, name, self.__searchMenu )
					if name not in results :
						results[name] = { "pos" : match.start(), "actions" : [] }
					
					results[name]["actions"].append( ( action, path ) )
		
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
	
	def __menuActionTriggered( self, action ) :
		
		self.__lastAction = action if action.objectName() != "GafferUI.Menu.__searchWidget" else None
		self._qtWidget().hide()

class _Menu( QtGui.QMenu ) :

	KeyboardMode = IECore.Enum.create( "Grab", "Close", "Forward" )
	
	def __init__( self, parent, title=None ) :
	
		QtGui.QMenu.__init__( self, parent )

		if title is not None :
			self.setTitle( title )

		self.keyboardMode = _Menu.KeyboardMode.Grab
	
	def event( self, qEvent ) :
	
		if qEvent.type() == QtCore.QEvent.ToolTip :
			action = self.actionAt( qEvent.pos() )
			if action and action.statusTip() :
				QtGui.QToolTip.showText( qEvent.globalPos(), action.statusTip(), self )
				return True
	
		return QtGui.QMenu.event( self, qEvent )
	
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
				app = QtGui.QApplication.instance()
				if app.focusWidget() != self :
					app.sendEvent( app.focusWidget(), qEvent )
					return
		
		QtGui.QMenu.keyPressEvent( self, qEvent )

	def hideEvent( self, qEvent ) :
		
		# Make all the menu items active, in case inactive items become active
		# while the menu is hidden (in which case we need them to have active
		# status for keyboard shortcuts to work). See also _buildFully() above.
		for action in self.actions() :
			action.setEnabled( True )
		
		QtGui.QMenu.hideEvent( self, qEvent )
