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

import six

import Gaffer
import GafferUI

from Qt import QtGui
from Qt import QtWidgets
from Qt import QtCore

class Button( GafferUI.Widget ) :

	__palette = None

	def __init__( self, text="", image=None, hasFrame=True, highlightOnOver=True, **kw ) :

		GafferUI.Widget.__init__( self, QtWidgets.QPushButton(), **kw )

		self._qtWidget().setAttribute( QtCore.Qt.WA_LayoutUsesWidgetRect )
		# allow return and enter keys to click button
		self._qtWidget().setAutoDefault( True )

		self.setText( text )
		self.setImage( image )
		self.setHasFrame( hasFrame )

		# using a WeakMethod to avoid circular references which would otherwise
		# never be broken.
		self._qtWidget().clicked.connect( Gaffer.WeakMethod( self.__clicked ) )

		self.__clickedSignal = GafferUI.WidgetSignal()

		# buttons appear to totally ignore the etch-disabled-text stylesheet option,
		# and we really don't like the etching. the only effective way of disabling it
		# seems to be to apply this palette which makes the etched text transparent.
		if Button.__palette is None :
			Button.__palette = QtGui.QPalette( QtWidgets.QApplication.instance().palette( self._qtWidget() ) )
			Button.__palette.setColor( QtGui.QPalette.Disabled, QtGui.QPalette.Light, QtGui.QColor( 0, 0, 0, 0 ) )

		self._qtWidget().setPalette( Button.__palette )

		if highlightOnOver :
			self.enterSignal().connect( Gaffer.WeakMethod( self.__enter ), scoped = False )
			self.leaveSignal().connect( Gaffer.WeakMethod( self.__leave ), scoped = False )

	def setHighlighted( self, highlighted ) :

		GafferUI.Widget.setHighlighted( self, highlighted )

		self.__updateIcon()

	def setText( self, text ) :

		assert( isinstance( text, six.string_types ) )

		self._qtWidget().setText( text )

	def getText( self ) :

		return self._qtWidget().text()

	def setImage( self, imageOrImageFileName ) :

		assert( isinstance( imageOrImageFileName, ( six.string_types, GafferUI.Image, type( None ) ) ) )

		if isinstance( imageOrImageFileName, six.string_types ) :
			self.__image = GafferUI.Image( imageOrImageFileName )
		else :
			self.__image = imageOrImageFileName

		self.__updateIcon()

	def getImage( self ) :

		return self.__image

	def setHasFrame( self, hasFrame ) :

		self._qtWidget().setProperty( "gafferWithFrame", hasFrame )
		self._qtWidget().setSizePolicy(
			QtWidgets.QSizePolicy.Minimum if hasFrame else QtWidgets.QSizePolicy.Fixed,
			QtWidgets.QSizePolicy.Fixed
		)
		self._repolish()

	def getHasFrame( self ) :

		return self._qtWidget().property( "gafferWithFrame" )

	def clickedSignal( self ) :

		return self.__clickedSignal

	def __clicked( self, *unusedArgs ) : # currently PyQt passes a "checked" argument and PySide doesn't

		# workaround problem whereby not all text fields will have committed their contents
		# into plugs when the button is pressed - this occurs particularly in the OpDialogue, and causes
		# the op to run without the values the user sees in the ui. normally editingFinished is emitted by
		# the text widget itself on a loss of focus, but unfortunately clicking on a button doesn't cause that
		# focus loss. so we helpfully emit the signal ourselves here.
		focusWidget = GafferUI.Widget._owner( QtWidgets.QApplication.focusWidget() )
		if focusWidget is not None and hasattr( focusWidget, "editingFinishedSignal" ) :
			focusWidget.editingFinishedSignal()( focusWidget )

		self.clickedSignal()( self )

	def __updateIcon( self ) :

		if self.__image is None :
			self._qtWidget().setIcon( QtGui.QIcon() )
			return

		if not self.getHighlighted() :
			pixmap = self.__image._qtPixmap()
		else :
			pixmap = self.__image._qtPixmapHighlighted()

		# Qt's built-in disabled state generation doesn't work well with dark schemes
		icon = QtGui.QIcon( pixmap )
		icon.addPixmap( self.__image._qtPixmapDisabled(), QtGui.QIcon.Disabled )

		self._qtWidget().setIcon( icon )
		self._qtWidget().setIconSize( pixmap.size() )

	def __enter( self, widget ) :

		self.setHighlighted( True )

	def __leave( self, widget ) :

		self.setHighlighted( False )
