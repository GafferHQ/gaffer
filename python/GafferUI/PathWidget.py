##########################################################################
#
#  Copyright (c) 2011, John Haddon. All rights reserved.
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

import os
import warnings
import functools
import imath

import IECore

import Gaffer
import GafferUI

from Qt import QtCore

class PathWidget( GafferUI.TextWidget ) :

	def __init__( self, path, **kw ) :

		GafferUI.TextWidget.__init__( self, str( path ), **kw )

		# we can be fairly sure that the average path requires a bit more space
		# than the other things that go in TextWidgets.
		self.setPreferredCharacterWidth( 60 )

		self.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ), scoped = False )
		self.selectingFinishedSignal().connect( Gaffer.WeakMethod( self.__selectingFinished ), scoped = False )

		self.textChangedSignal().connect( Gaffer.WeakMethod( self.__textChanged ), scoped = False )

		self.__popupMenu = None

		self.__path = None
		self.setPath( path )

	def path( self ) :

		warnings.warn( "PathWidget.path() is deprecated, use PathWidget.getPath() instead.", DeprecationWarning, 2 )
		return self.__path

	def setPath( self, path ) :

		self.__path = path
		self.__pathChangedConnection = self.__path.pathChangedSignal().connect( Gaffer.WeakMethod( self.__pathChanged, fallbackResult = None ) )
		self.setText( str( self.__path ) )

	def getPath( self ) :

		return self.__path

	def __keyPress( self, widget, event ) :

		if not self.getEditable() :
			return False

		if event.key=="Tab" :

			# do tab completion

			position = self.getCursorPosition()

			truncatedPath = self.__path.copy()
			truncatedPath.setFromString( str( truncatedPath )[:position] )
			if len( truncatedPath ) :
				matchStart = truncatedPath[-1]
				del truncatedPath[-1]
			else :
				matchStart = ""

			matches = [ x[-1] for x in truncatedPath.children() if x[-1].startswith( matchStart ) ]
			match = os.path.commonprefix( matches )

			if match :

				self.__path[:] = truncatedPath[:] + [ match ]
				if len( matches )==1 and not self.__path.isLeaf() :
					text = self.getText()
					if not text.endswith( "/" ) :
						self.setText( text + "/" )

				self.setCursorPosition( len( self.getText() ) )

			return True

		elif event.key == "Down" :

			if event.modifiers & GafferUI.ModifiableEvent.Modifiers.Shift :
				# select all!
				self.setSelection( None, None )
			else :
				text = self.getText()
				position = self.getCursorPosition()
				if position == len( text ) and len( text ) and text[-1]=="/" :
					# select last character to trigger menu for next path entry
					self.setSelection( -1, None )
				else :
					# select path entry around the cursor
					low = text.rfind( "/", 0, position )
					high = text.find( "/", position )
					if low != -1 :
						self.setSelection( low+1, high if high != -1 else None )

			self.__popupMenuForSelection()
			return True

		return False

	def __selectingFinished( self, widget ) :

		assert( widget is self )

		if self.getEditable() :
			self.__popupMenuForSelection()

	def __popupMenuForSelection( self ) :

		start, end = self.getSelection()
		if start == end :
			return

		text = self.getText()
		selectedText = text[start:end]

		if text == selectedText :
			self.__popupHierarchy()
		elif selectedText == "/" and end == len( text ) :
			# the final slash was selected
			self.__popupListing( end )
		elif "/" not in selectedText and text[start-1] == "/" and ( end >= len( text ) or text[end] == "/" ) :
			self.__popupListing( start )

	def __popupHierarchy( self ) :

		pathCopy = self.__path.copy()
		md = IECore.MenuDefinition()
		i = 0
		while len( pathCopy ) :
			md.append(
				"/" + str( i ),
				IECore.MenuItemDefinition(
					label = str( pathCopy ),
					command = functools.partial( Gaffer.WeakMethod( self.__path.setFromString ), str( pathCopy ) ),
				)
			)
			del pathCopy[-1]
			i += 1

		self.__popupMenu = GafferUI.Menu( md )
		self.__popupMenu.popup( parent = self, position = self.__popupPosition( 0 ), forcePosition=True, grabFocus=False )

	def __popupListing( self, textIndex ) :

		dirPath = self.__path.copy()
		n = os.path.dirname( self.getText()[:textIndex] ) or "/"
		dirPath.setFromString( n )

		options = dirPath.children()
		options = [ x[-1] for x in options ]

		if len( options ) :

			md = IECore.MenuDefinition()
			for o in options :
				md.append( "/" + o,
					IECore.MenuItemDefinition(
						label=o,
						command = functools.partial( Gaffer.WeakMethod( self.__replacePathEntry ), len( dirPath ), o )
					)
				)

			self.__popupMenu = GafferUI.Menu( md )
			self.__popupMenu.popup( parent = self, position = self.__popupPosition( textIndex ), forcePosition=True, grabFocus=False )

	def __replacePathEntry( self, position, newEntry ) :

		if position==len( self.__path ) :
			self.__path.append( newEntry )
		else :
			self.__path[position] = newEntry
			self.__path.truncateUntilValid()

		if position==len( self.__path )-1 and not self.__path.isLeaf() :
			self.setText( self.getText() + "/" )

	def __popupPosition( self, textIndex ) :

		## \todo Surely there's a better way?
		for x in range( 0, 10000 ) :
			if self._qtWidget().cursorPositionAt( QtCore.QPoint( x, 5 ) ) >= textIndex :
				break

		bound = self.bound()
		return imath.V2i( bound.min().x + x, bound.max().y )

	def __pathChanged( self, path ) :

		self.setText( str( path ) )

	def __textChanged( self, widget ) :

		text = self.getText()
		with Gaffer.BlockedConnection( self.__pathChangedConnection ) :
			try :
				self.__path.setFromString( self.getText() )
			except :
				# no need to worry too much - it's up to the user to enter
				# something valid. maybe they'll get it right next time.
				pass
