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

import inspect
import weakref
import types

import IECore

import Gaffer
import GafferUI

QtCore = GafferUI._qtImport( "QtCore" )
QtGui = GafferUI._qtImport( "QtGui" )

class Menu( GafferUI.Widget ) :

	def __init__( self, definition, _qtParent=None, **kw ) :
	
		GafferUI.Widget.__init__( self, _Menu( _qtParent ), **kw )
		
		self.__definition = definition
		
		# we rebuild each menu every time it's shown, to support the use of callable items to provide
		# dynamic submenus and item states.
		self._qtWidget().aboutToShow.connect( IECore.curry( Gaffer.WeakMethod( self.__build ), self._qtWidget(), self.__definition ) )
		
		self._setStyleSheet()		
		
		self.__popupParent = None

	## Displays the menu at the specified position, and attached to
	# an optional parent. If position is not specified then it 
	# defaults to the current cursor position. If forcePosition is specified
	# then the menu will be shown exactly at the requested position, even if
	# doing so means some of it will be off screen. If grabFocus is False, then
	# the menu will not take keyboard events unless the first such event is a
	# press of the down arrow.
	def popup( self, parent=None, position=None, forcePosition=False, grabFocus=True ) :
	
		if parent is not None :
			self.__popupParent = weakref.ref( parent )
		else :
			self.__popupParent = None
			
		if position is None :
			position = QtGui.QCursor.pos()
		else :
			position = QtCore.QPoint( position.x, position.y )

		self._qtWidget().grabFocus = grabFocus
			
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
		
	def __commandWrapper( self, qtAction, command, active, toggled ) :
	
		if not self.__evaluateItemValue( active ) :
			return
		
		args = []
		kw = {}
		
		commandArgs = []
		if isinstance( command, types.FunctionType ) :
			commandArgs = inspect.getargspec( command )[0]
		elif isinstance( command, Gaffer.WeakMethod ) :
			commandArgs = inspect.getargspec( command.method() )[0][1:]

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
			definition = definition()
			
		qtMenu.clear()
			
		done = set()
		for path, item in definition.items() :
		
			pathComponents = path.strip( "/" ).split( "/" )
			name = pathComponents[0]
						
			if not name in done :

				menuItem = None
				if len( pathComponents ) > 1 :
					
					# it's an intermediate submenu we need to make
					# to construct the path to something else
										
					subMenu = qtMenu.addMenu( name )
					subMenuDefinition = definition.reRooted( "/" + name + "/" )					
					subMenu.aboutToShow.connect( IECore.curry( Gaffer.WeakMethod( self.__build ), subMenu, subMenuDefinition ) )
					if recurse :
						self.__build( subMenu, subMenuDefinition, activeOverride, recurse )
					
				else :
				
					label = name
					with IECore.IgnoredExceptions( AttributeError ) :
						label = item.label
					
					if item.subMenu is not None :
										
						subMenu = qtMenu.addMenu( label )
						subMenu.aboutToShow.connect( IECore.curry( Gaffer.WeakMethod( self.__build ), subMenu, item.subMenu ) )
						if recurse :
							self.__build( subMenu, subMenuDefinition, activeOverride, recurse )
							
					else :
				
						# it's not a submenu

						qtAction = QtGui.QAction( label, qtMenu )

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
							qtAction.setShortcut( QtGui.QKeySequence( shortCut ) ) 
						
						qtMenu.addAction( qtAction )

				done.add( name )
				
	def __evaluateItemValue( self, itemValue ) :
	
		if callable( itemValue ) :
			kwArgs = {}
			if "menu" in inspect.getargspec( itemValue )[0] :
				kwArgs["menu"] = self
				itemValue = itemValue( **kwArgs )
				
		return itemValue

class _Menu( QtGui.QMenu ) :

	def __init__( self, parent ) :
	
		QtGui.QMenu.__init__( self, parent )

		self.grabFocus = True
			
	def keyPressEvent( self, qEvent ) :
	
		if not self.grabFocus :
			if qEvent.key() == QtCore.Qt.Key_Down :
				self.grabFocus = True
			else :
				# pass the event on to the rightful recipient
				self.hide()	
				app = QtGui.QApplication.instance()
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