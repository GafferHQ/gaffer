##########################################################################
#
#  Copyright (c) 2026, Cinesite VFX Ltd. All rights reserved.
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

import os
import functools

import imath

import IECore

import Gaffer
import GafferUI

from Qt import QtWidgets

class BreadCrumbsWidget( GafferUI.Widget ) :

	def __init__( self, path, popupMenuTitle = "Path Item", **kw ) :

		self.__row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, borderWidth = 1, spacing = 7 )

		GafferUI.Widget.__init__( self, self.__row, **kw )

		with self.__row :
			self.__pathButtonContainer = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 )

			self.__textWidget = GafferUI.TextWidget( toolTip =
				"## Actions\n\n"
				"- Right-click for contents menu.\n"
				"- <kbd>Down</kbd> to show children.\n"
				"- <kbd>Up</kbd> to go to parent.\n"
				"- <kbd>Tab</kbd> for auto-complete.\n"
				"- <kbd>Home</kbd> to return to root."
			)

			self.__textWidget.keyPressSignal().connect( Gaffer.WeakMethod( self.__textKeyPress ) )
			self.__textWidget.editingFinishedSignal().connect( Gaffer.WeakMethod( self.__textEditingFinished ) )
			self.__textWidget.activatedSignal().connect( Gaffer.WeakMethod( self.__textActivated ) )
			self.__textWidget.contextMenuSignal().connect( Gaffer.WeakMethod( self.__textContextMenu ) )
			self.__textWidget.textChangedSignal().connect( Gaffer.WeakMethod( self.__textChanged ) )

		self.__popupMenu = None

		self.__popupMenuTitle = popupMenuTitle

		self.setPath( path )

	def setPath( self, path ) :

		self.__path = path
		self.__pathChangedConnection = self.__path.pathChangedSignal().connect( Gaffer.WeakMethod( self.__pathChanged ), scoped = True )
		self.__updateWidgets()

	def getPath( self ) :

		return self.__path

	def __updateWidgets( self ) :

		del self.__pathButtonContainer[:]

		path = self.__path.copy()
		path.setFromString( path.root() )

		for w in self.__pathWidgets( path.copy() ) :
			self.__pathButtonContainer.append( w )

		for i in range( 0, len( self.__path ) ) :
			path.append( self.__path[i] )
			if path.isValid() :
				for w in self.__pathWidgets( path.copy() ) :
					self.__pathButtonContainer.append( w )
			else :
				break

		self.__textWidget.setText( path[-1] if ( len( path ) > 0 and not path.isValid() ) else "" )

	def __pathWidgets( self, path ) :

		pathButton = GafferUI.Button(
			path[-1] if len( path ) > 0 else "",
			image = "home.png" if len( path ) == 0 else None,
			hasFrame = False,
			highlightOnOver = True,
			toolTip = "Click to set as current path." + ( "<br>Right-click for adjacent paths menu." if len( path ) > 0 else "" )
		)
		pathButton.buttonPressSignal().connect( functools.partial( Gaffer.WeakMethod( self.__pathButtonPress ), path ) )

		return ( pathButton, GafferUI.Label( "/" ) )

	def __copyPathToClipboard( self, pathString ) :

		self.ancestor( GafferUI.ScriptWindow ).scriptNode().applicationRoot().setClipboardContents( IECore.StringData( pathString ) )

	def __acquireGraphEditor( self, pathString ) :

		scriptNode = self.ancestor( GafferUI.ScriptWindow ).scriptNode()
		n = scriptNode.descendant( pathString ) if pathString else scriptNode
		GafferUI.GraphEditor.acquire( n )

	def __pathButtonPress( self, path, button, event ) :

		if event.buttons == GafferUI.ButtonEvent.Buttons.Right :
			menuDefinition = IECore.MenuDefinition()

			if len( path ) > 0 :
				parentPath = path.copy()
				del parentPath[-1]

				menuDefinition.update( self.__pathMenuDefinition( parentPath ) )

				menuDefinition.append(
					"/copyDivider",
					{
						"divider" : True
					}
				)
				menuDefinition.append(
					"Copy Path",
					{
						"command" : functools.partial( Gaffer.WeakMethod( self.__copyPathToClipboard ), pathString = str( path ) ),
					}
				)

			menuDefinition.append(
				"Open in new Graph Editor",
				{
					"command" : functools.partial( Gaffer.WeakMethod( self.__acquireGraphEditor ), pathString = str( path ) ),
					"active" : path != self.__path,
				}
			)

			self.__popupListing( menuDefinition, button )

			return True

		elif event.button == event.Buttons.Left :
			self.__path[:] = path[:]
			return True

		return False

	def __textChanged( self, textWidget ) :

		popupRequested = False
		if self.__popupMenu is not None and self.__popupMenu.visible() :
			GafferUI.WidgetAlgo.keepUntilIdle( self.__popupMenu )
			self.__popupMenu = None
			popupRequested = True

		text = textWidget.getText()
		newPath = self.__validatedPath( self.__path, text )

		if newPath is not None and ( ( len( text ) > 0 and text[-1] == "/" ) or len( newPath ) == 0 ) :
			self.__path[:] = newPath[:]
			return

		if popupRequested :
			self.__popupListing( self.__pathMenuDefinition( self.__path, text ), self.__textWidget )

	def __textEditingFinished( self, textWidget ) :

		# This signal is also emitted when the menu pops up. If that's the case,
		# don't clear the text. Also leave the text intact if we still have focus,
		# i.e. the enter key was pressed. `__textActivated()` takes care of the contents
		# in that case.`
		if ( self.__popupMenu is None or not self.__popupMenu.visible() ) and not self.__textWidget._qtWidget().hasFocus() :
			self.__textWidget.setText( "" )

		return True

	def __textActivated( self, textWidget ) :

		if self.__popupMenu is not None and self.__popupMenu.visible() :
			self.__popupMenu = None

		text = textWidget.getText()
		newPath = self.__validatedPath( self.__path, text )

		if newPath is not None :
			self.__path[:] = newPath[:]

		return True

	def __validatedPath( self, path, suffix ) :

		newPath = path.copy()

		if suffix == "" :
			return None

		suffix = suffix.replace( ".", "/" )
		newPath.setFromString( str( path ) + "/" + suffix )

		passesFilter = True
		if path.getFilter() is not None :
			passesFilter = path.getFilter().filter( [newPath] ) == [newPath]

		return newPath if ( newPath.isValid() and passesFilter ) else None

	def __textKeyPress( self, widget, event ) :

		if not self.__textWidget.getEditable() :
			# \todo This is copied from the `PathWidget`, is it possible to arrive here?
			# Does it belong on `self` instead?
			return False

		if event.key == "Backspace" and self.__textWidget.getText() == "" and len( self.__path ) > 0 :
			t = self.__path[-1]
			del self.__path[-1]
			self.__textWidget.setText( t )
			return True

		elif event.key=="Tab" :
			self.__tabComplete()
			return True

		elif event.key == "Down" :
			self.__popupListing( self.__pathMenuDefinition( self.__path ), self.__textWidget )
			return True

		elif event.key == "Up" :
			if self.__textWidget.getText() != "" :
				self.__textWidget.setText( "" )
			elif len( self.__path ) > 0 :
				del self.__path[-1]
			return True

		elif event.key == "Home" :
			self.__path.setFromString( self.__path.root() )
			return True

		return False

	def __textContextMenu( self, widget ) :

		self.__popupListing( self.__pathMenuDefinition( self.__path ), None )
		return True

	def __tabComplete( self ) :

		position = self.__textWidget.getCursorPosition()
		text = self.__textWidget.getText()

		matches = [ x[-1] for x in self.__path.children() if x[-1].startswith( text[:position] ) ]

		match = os.path.commonprefix( matches )
		if match :
			self.__textWidget.setText( match )
		self.__popupListing( self.__pathMenuDefinition( self.__path, match or text ), self.__textWidget )

		self.__textWidget.setCursorPosition( len( self.__textWidget.getText() ) )

	def __setPathEntry( self, path ) :

		if path == self.__path :
			return

		newPath = self.__path.copy()
		newPath.setFromString( newPath.root() )
		pathLength = len( path )
		for i in range( 0, max( pathLength, len( self.__path ) ) ) :
			newPath.append( path[i] if i < pathLength else self.__path[i] )

		newPath.truncateUntilValid()
		self.__path[:] = newPath[:]

		self.__textWidget.grabFocus()

	def __pathMenuDefinition( self, path, prefix = "" ) :

		result = IECore.MenuDefinition()

		sortedChildren = sorted( path.children(), key = lambda v : v[-1] )

		pathPrefix = "/"
		for i, childPath in enumerate( [ i for i in sortedChildren if i[-1].startswith( prefix ) ] ) :
			result.append(
				pathPrefix + childPath[-1],
				{
					"command" : functools.partial( Gaffer.WeakMethod( self.__setPathEntry ), childPath ),
				}
			)

			if i == 10 :
				pathPrefix = "/More/"
				result.append( "/Divider", { "divider" : True } )

		if result.size() == 0 :
			result.append( "/No viewable children", { "active" : False, } )

		return result

	def __popupListing( self, menuDefinition, parentWidget ) :

		bound = None
		if parentWidget is not None :
			bound = parentWidget.bound()
			xOffset = 0
			if isinstance( parentWidget, GafferUI.TextWidget ) :
				xOffset = parentWidget._qtWidget().cursorRect().left()

		self.__popupMenu = GafferUI.Menu( menuDefinition, title = self.__popupMenuTitle )
		self.__popupMenu.visibilityChangedSignal().connect( Gaffer.WeakMethod( self.__popupMenuVisibilityChanged ) )
		self.__popupMenu.popup(
			parent = self.ancestor( GafferUI.GadgetWidget ) or self.__textWidget,
			position = imath.V2i( bound.min().x + xOffset, bound.max().y ) if bound is not None else None,
		)

		## \todo Expose KeyboardMode publicly in `popup()`?

		## \todo Is this valid for uses outside the GraphEditor?
		self.__popupMenu._qtWidget().keyboardMode = self.__popupMenu._qtWidget().KeyboardMode.Forward

	def __popupMenuVisibilityChanged( self, widget ) :

		# \todo Determine if `__textWidget` needs to be cleared. It should be if it
		# no longer has focus after the popup is hidden.
		pass

	def __pathChanged( self, path ) :

		self.__updateWidgets()
