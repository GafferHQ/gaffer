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

import imath

import IECore

import Gaffer
import GafferUI

from Qt import QtCore
from Qt import QtGui
from Qt import QtWidgets

## The ColorSwatch simply displays a flat patch of colour. The colour is assumed to
# be in a linear space : use `Widget.setDisplayTransform()` to control how it is displayed.
class ColorSwatch( GafferUI.Widget ) :

	__linearBackgroundColor0 = imath.Color3f( 0.1 )
	__linearBackgroundColor1 = imath.Color3f( 0.2 )

	def __init__( self, color=imath.Color4f( 1 ), **kw ) :

		GafferUI.Widget.__init__( self, QtWidgets.QWidget(), **kw )

		self.__errored = False

		self.__opaqueChecker = _Checker( borderBottom = False )
		self.__transparentChecker = _Checker( borderTop = False )

		layout = QtWidgets.QVBoxLayout()
		layout.setSpacing( 0 )
		layout.setContentsMargins( 0, 0, 0, 0 )
		layout.addWidget( self.__opaqueChecker )
		layout.addWidget( self.__transparentChecker )
		self._qtWidget().setLayout( layout )

		## \todo Should this be an option? Should it be an option for all Widgets?
		self.__opaqueChecker.setMinimumSize( 12, 6 )
		self.__transparentChecker.setMinimumSize( 12, 6 )

		self.__color = color
		self.__updateCheckerColors()

	def setHighlighted( self, highlighted ) :

		if highlighted == self.getHighlighted() :
			return

		GafferUI.Widget.setHighlighted( self, highlighted )

		self.__updateCheckerColors()

	## Colours are expected to be in linear space, and in the case of Color4fs,
	# are /not/ expected to be premultiplied.
	def setColor( self, color ) :

		if color != self.__color :
			self.__color = color
			self.__updateCheckerColors()

	def getColor( self ) :

		return self.__color

	def setErrored( self, errored ) :

		if errored == self.getErrored() :
			return

		self.__errored = errored
		self.__updateCheckerColors()

	def getErrored( self ) :

		return self.__errored

	def _displayTransformChanged( self ) :

		GafferUI.Widget._displayTransformChanged( self )
		self.__updateCheckerColors()

	def __updateCheckerColors( self ) :

		displayTransform = self.displayTransform()

		opaqueDisplayColor = self._qtColor( displayTransform( self.__color ) )
		self.__opaqueChecker.color0 = self.__opaqueChecker.color1 = opaqueDisplayColor
		if self.__color.dimensions()==3 :
			self.__transparentChecker.color0 = self.__transparentChecker.color1 = opaqueDisplayColor
		else :
			c = self.__color
			color0 = self.__linearBackgroundColor0 * ( 1.0 - c.a ) + imath.Color3f( c.r, c.g, c.b ) * c.a
			color1 = self.__linearBackgroundColor1 * ( 1.0 - c.a ) + imath.Color3f( c.r, c.g, c.b ) * c.a
			self.__transparentChecker.color0 = self._qtColor( displayTransform( color0 ) )
			self.__transparentChecker.color1 = self._qtColor( displayTransform( color1 ) )

		## \todo Colour should come from the style when we have styles applying to Widgets as well as Gadgets
		if not self.__errored:
			self.__opaqueChecker.borderColor = QtGui.QColor( 119, 156, 255 ) if self.getHighlighted() else None
			self.__transparentChecker.borderColor = QtGui.QColor( 119, 156, 255 ) if self.getHighlighted() else None
		else:
			self.__opaqueChecker.borderColor = QtGui.QColor( 255, 85, 85 )
			self.__transparentChecker.borderColor = QtGui.QColor( 255, 85, 85 )

		self._qtWidget().update()

# Private implementation - a QWidget derived class which just draws a checker with
# no knowledge of colour spaces or anything.
class _Checker( QtWidgets.QWidget ) :

	def __init__( self, borderTop=True, borderBottom=True ) :

		QtWidgets.QWidget.__init__( self )
		self.__borderTop = borderTop
		self.__borderBottom = borderBottom

	def paintEvent( self, event ) :

		_Checker._paintRectangle(
			QtGui.QPainter( self ),
			event.rect(),
			self.color0,
			self.color1,
			self.borderColor,
			self.__borderTop,
			self.__borderBottom,
			self.width(),
			self.height()
		)

	@staticmethod
	def _paintRectangle(
		painter,
		rect,
		color0,
		color1,
		borderColor = None,
		borderTop = False,
		borderBottom = False,
		borderWidth = 0,
		borderHeight = 0
	) :

		if color0 != color1 :

			# draw checkerboard if colours differ
			checkSize = 6

			gridSize = imath.V2i( rect.width() / checkSize + 1, rect.height() / checkSize + 1 )

			for i in range( 0, gridSize.x ) :
				for j in range( 0, gridSize.y ) :
					offset = imath.V2i( i * checkSize, j * checkSize )
					square = QtCore.QRectF(
						rect.x() + offset.x,
						rect.y() + offset.y,
						min( rect.width() - offset.x, checkSize ),
						min( rect.height() - offset.y, checkSize )
					)
					if ( i + j ) % 2 :
						painter.fillRect( square, color0 )
					else :
						painter.fillRect( square, color1 )

		else :

			# otherwise just draw a flat colour cos it'll be quicker
			painter.fillRect( QtCore.QRectF( rect.x(), rect.y(), rect.width(), rect.height() ), color0 )

		if borderColor is not None :
			pen = QtGui.QPen( borderColor )
			lines = [
				QtCore.QLine( 0, 0, 0, borderHeight ),
				QtCore.QLine( borderWidth, 0, borderWidth, borderHeight ),
			]
			if borderTop :
				lines.append( QtCore.QLine( 0, 0, borderWidth, 0 ) )
			if borderBottom :
				lines.append( QtCore.QLine( 0, borderHeight, borderWidth, borderHeight ) )
			pen.setWidth( 4 )
			painter.setPen( pen )
			painter.drawLines( lines )
