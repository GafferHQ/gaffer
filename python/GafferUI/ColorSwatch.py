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

## The ColorSwatch simply displays a flat patch of colour. By default, the colour
# is specified in linear space and GafferUI.DisplayTransform is used to ensure it
# is correctly corrected when displayed. To specify the colour directly in display
# space, pass `useDisplayTransform = False` to the constructor.
class ColorSwatch( GafferUI.Widget ) :

	__linearBackgroundColor0 = imath.Color3f( 0.1 )
	__linearBackgroundColor1 = imath.Color3f( 0.2 )

	def __init__( self, color=imath.Color4f( 1 ), useDisplayTransform = True, **kw ) :

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

		self.__useDisplayTransform = useDisplayTransform
		self.__color = color

		GafferUI.DisplayTransform.changedSignal().connect( Gaffer.WeakMethod( self.__displayTransformChanged ), scoped = False )

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

	def __updateCheckerColors( self ) :

		displayTransform = GafferUI.DisplayTransform.get()
		effectiveDisplayTransform = displayTransform if self.__useDisplayTransform else lambda x : x

		opaqueDisplayColor = self._qtColor( effectiveDisplayTransform( self.__color ) )
		self.__opaqueChecker.color0 = self.__opaqueChecker.color1 = opaqueDisplayColor
		if self.__color.dimensions()==3 :
			self.__transparentChecker.color0 = self.__transparentChecker.color1 = opaqueDisplayColor
		else :
			c = self.__color
			# We want the background colour to be the same whether or not we're using the display transform for
			# the main colour, so if we're not using the display transform later after compositing, we pre-apply
			# it to the background colours before compositing.
			bg0 = self.__linearBackgroundColor0 if self.__useDisplayTransform else displayTransform( self.__linearBackgroundColor0 )
			bg1 = self.__linearBackgroundColor1 if self.__useDisplayTransform else displayTransform( self.__linearBackgroundColor1 )
			# Now composite the main colour with the background colour. This is happening in linear space
			# if __useDisplayTransform is True, and in display space otherwise.
			color0 = bg0 * ( 1.0 - c.a ) + imath.Color3f( c.r, c.g, c.b ) * c.a
			color1 = bg1 * ( 1.0 - c.a ) + imath.Color3f( c.r, c.g, c.b ) * c.a

			self.__transparentChecker.color0 = self._qtColor( effectiveDisplayTransform( color0 ) )
			self.__transparentChecker.color1 = self._qtColor( effectiveDisplayTransform( color1 ) )

		## \todo Colour should come from the style when we have styles applying to Widgets as well as Gadgets
		if not self.__errored:
			self.__opaqueChecker.borderColor = QtGui.QColor( 119, 156, 255 ) if self.getHighlighted() else None
			self.__transparentChecker.borderColor = QtGui.QColor( 119, 156, 255 ) if self.getHighlighted() else None
		else:
			self.__opaqueChecker.borderColor = QtGui.QColor( 255, 85, 85 )
			self.__transparentChecker.borderColor = QtGui.QColor( 255, 85, 85 )

		self._qtWidget().update()

	def __displayTransformChanged( self ) :

		self.__updateCheckerColors()

	def setErrored( self, errored ) :

		if errored == self.getErrored() :
			return

		self.__errored = errored
		self.__updateCheckerColors()

	def getErrored( self ) :

		return self.__errored


# Private implementation - a QWidget derived class which just draws a checker with
# no knowledge of colour spaces or anything.
class _Checker( QtWidgets.QWidget ) :

	def __init__( self, borderTop=True, borderBottom=True ) :

		QtWidgets.QWidget.__init__( self )
		self.__borderTop = borderTop
		self.__borderBottom = borderBottom

	def paintEvent( self, event ) :

		painter = QtGui.QPainter( self )
		rect = event.rect()

		if self.color0 != self.color1 :

			# draw checkerboard if colours differ
			checkSize = 6

			min = imath.V2i( rect.x() / checkSize, rect.y() / checkSize )
			max = imath.V2i( 1 + (rect.x() + rect.width()) / checkSize, 1 + (rect.y() + rect.height()) / checkSize )

			for x in range( min.x, max.x ) :
				for y in range( min.y, max.y ) :
					if ( x + y ) % 2 :
						painter.fillRect( QtCore.QRectF( x * checkSize, y * checkSize, checkSize, checkSize ), self.color0 )
					else :
						painter.fillRect( QtCore.QRectF( x * checkSize, y * checkSize, checkSize, checkSize ), self.color1 )

		else :

			# otherwise just draw a flat colour cos it'll be quicker
			painter.fillRect( QtCore.QRectF( rect.x(), rect.y(), rect.x() + rect.width(), rect.y() + rect.height() ), self.color0 )

		if self.borderColor is not None :
			w = self.width()
			h = self.height()
			pen = QtGui.QPen( self.borderColor )
			lines = [
				QtCore.QLine( 0, 0, 0, h ),
				QtCore.QLine( w, 0, w, h ),
			]
			if self.__borderTop :
				lines.append( QtCore.QLine( 0, 0, w, 0 ) )
			if self.__borderBottom :
				lines.append( QtCore.QLine( 0, h, w, h ) )
			pen.setWidth( 4 )
			painter.setPen( pen )
			painter.drawLines( lines )
