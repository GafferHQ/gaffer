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

	def __init__( self, definition, _qtMenu=None, **kw ) :
	
		GafferUI.Widget.__init__( self, _qtMenu if _qtMenu else QtGui.QMenu(), **kw )
			
		self._qtWidget().aboutToShow.connect( IECore.curry( Gaffer.WeakMethod( self.__show ), self._qtWidget(), definition ) )
		
		self._setStyleSheet()
		
		self.__popupParent = None
		
	## Displays the menu at the specified position, and attached to
	# an optional parent. If position is not specified then it 
	# defaults to the current cursor position. If forcePosition is specified
	# then the menu will be shown exactly at the requested position, even if
	# doing so means some of it will be off screen.
	def popup( self, parent=None, position=None, forcePosition=False ) :
	
		if parent is not None :
			self.__popupParent = weakref.ref( parent )
		else :
			self.__popupParent = None
			
		if position is None :
			position = QtGui.QCursor.pos()
		else :
			position = QtCore.QPoint( position.x, position.y )
			
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
		
	def __commandWrapper( self, qtAction, command, toggled ) :
	
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

	def __show( self, qtMenu, definition ) :
		
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
					subMenu.aboutToShow.connect( IECore.curry( Gaffer.WeakMethod( self.__show ), subMenu, subMenuDefinition ) )
					
				else :
				
					label = name
					with IECore.IgnoredExceptions( AttributeError ) :
						label = item.label
					
					if item.subMenu is not None :
										
						subMenu = qtMenu.addMenu( label )
						subMenu.aboutToShow.connect( IECore.curry( Gaffer.WeakMethod( self.__show ), subMenu, item.subMenu ) )
					
					else :
				
						# it's not a submenu

						qtAction = QtGui.QAction( label, qtMenu )

						if item.checkBox is not None :
							qtAction.setCheckable( True )
							checked = item.checkBox
							if callable( checked ) :
								kwArgs = {}
								if "menu" in inspect.getargspec( checked )[0] :
									kwArgs["menu"] = self
								checked = checked( **kwArgs )
							qtAction.setChecked( checked )

						if item.divider :
							qtAction.setSeparator( True )

						if item.command :

							if item.checkBox :	
								signal = qtAction.toggled[bool]
							else :
								signal = qtAction.triggered[bool]

							signal.connect( IECore.curry( Gaffer.WeakMethod( self.__commandWrapper ), qtAction, item.command ) )

						active = item.active
						if callable( active ) :
							active = active()
						qtAction.setEnabled( active )

						qtMenu.addAction( qtAction )

				done.add( name )
