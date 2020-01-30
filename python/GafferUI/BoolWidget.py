##########################################################################
#
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

import types

import IECore

import Gaffer
import GafferUI

from Qt import QtCore
from Qt import QtGui
from Qt import QtWidgets

class BoolWidget( GafferUI.Widget ) :

	DisplayMode = IECore.Enum.create( "CheckBox", "Switch", "Tool" )

	def __init__( self, text="", checked=False, displayMode=DisplayMode.CheckBox, image = None, **kw ) :

		GafferUI.Widget.__init__( self, _CheckBox( text ), **kw )

		self.__defaultFocusPolicy = self._qtWidget().focusPolicy()

		self.setState( checked )
		self.setDisplayMode( displayMode )
		self.setImage( image )

		self.__stateChangedSignal = GafferUI.WidgetSignal()

		self._qtWidget().stateChanged.connect( Gaffer.WeakMethod( self.__stateChanged ) )

	def setText( self, text ) :

		self._qtWidget().setText( text )

	def getText( self ) :

		return str( self._qtWidget().text() )

	def setImage( self, image ) :

		if isinstance( image, basestring ) :
			self.__image = GafferUI.Image( image )
		else :
			assert( isinstance( image, ( GafferUI.Image, type( None ) ) ) )
			self.__image = image

		if self.__image is None :
			self._qtWidget().setIcon( QtGui.QIcon() )
		else :
			self._qtWidget().setIcon( QtGui.QIcon( self.__image._qtPixmap() ) )
			self._qtWidget().setIconSize( self.__image._qtPixmap().size() )

	def getImage( self ) :

		return self.__image

	def setState( self, checked ) :

		self._qtWidget().setCheckState( QtCore.Qt.Checked if checked else QtCore.Qt.Unchecked )

	def getState( self ) :

		return self._qtWidget().checkState() == QtCore.Qt.Checked

	def setDisplayMode( self, displayMode ) :

		self._qtWidget().setProperty( "gafferDisplayMode", str( displayMode ) )
		self._qtWidget().setHitMode(
			_CheckBox.HitMode.Button if displayMode == self.DisplayMode.Tool else _CheckBox.HitMode.CheckBox
		)

		if displayMode == self.DisplayMode.Tool :
			self._qtWidget().setFocusPolicy( QtCore.Qt.NoFocus )
		else :
			self._qtWidget().setFocusPolicy( self.__defaultFocusPolicy )

	def getDisplayMode( self ) :

		return getattr(
			self.DisplayMode,
			GafferUI._Variant.fromVariant(
				self._qtWidget().property( "gafferDisplayMode" )
			)
		)

	def setErrored( self, errored ) :

		if errored == self.getErrored() :
			return

		self._qtWidget().setProperty( "gafferError", GafferUI._Variant.toVariant( bool( errored ) ) )
		self._repolish()

	def getErrored( self ) :

		return GafferUI._Variant.fromVariant( self._qtWidget().property( "gafferError" ) ) or False

	def stateChangedSignal( self ) :

		return self.__stateChangedSignal

	def __stateChanged( self, state ) :

		self.__stateChangedSignal( self )

class _CheckBox( QtWidgets.QCheckBox ) :

	HitMode = IECore.Enum.create( "Button", "CheckBox" )

	def __init__( self, text, parent = None ) :

		QtWidgets.QCheckBox.__init__( self, text, parent )

		self.__hitMode = self.HitMode.CheckBox

		self.setSizePolicy( QtWidgets.QSizePolicy(
			QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
		) )

	def setHitMode( self, hitMode ) :

		self.__hitMode = hitMode

	def getHidMode( self ) :

		return self.__hitMode

	def hitButton( self, pos ) :

		if self.__hitMode == self.HitMode.Button :
			return QtWidgets.QAbstractButton.hitButton( self, pos )
		else :
			return QtWidgets.QCheckBox.hitButton( self, pos )

## \todo Backwards compatibility - remove for version 1.0
CheckBox = BoolWidget
