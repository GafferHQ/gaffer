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

import IECore

import Gaffer
import GafferUI

QtCore = GafferUI._qtImport( "QtCore" )
QtGui = GafferUI._qtImport( "QtGui" )

## The ColorSwatch simply displays a flat patch of colour. The colour is specified
# in linear space, but the GafferUI.DisplayTransform is used to ensure it is correctly
# corrected when displayed.
class ColorSwatch( GafferUI.Widget ) :

	def __init__( self, color=IECore.Color4f( 1 ), **kw ) :
	
		GafferUI.Widget.__init__( self, _Checker(), **kw )
	
		## \todo Should this be an option? Should it be an option for all Widgets?
		self._qtWidget().setMinimumSize( 12, 12 )

		self.__displayTransformChangedConnection = GafferUI.DisplayTransform.changedSignal().connect( Gaffer.WeakMethod( self.__displayTransformChanged ) )

		self.__linearColor = color
		self.__updateCheckerColors()
	
	def setHighlighted( self, highlighted ) :

		if highlighted == self.getHighlighted() :
			return

		GafferUI.Widget.setHighlighted( self, highlighted )

		self.__updateCheckerColors()

	## Colours are expected to be in linear space, and in the case of Color4fs,
	# are /not/ expected to be premultiplied.	
	def setColor( self, color ) :
	
		if color != self.__linearColor :
			self.__linearColor = color
			self.__updateCheckerColors()
		
	def getColor( self ) :
	
		return self.__linearColor
	
	def __updateCheckerColors( self ) :
	
		displayTransform = GafferUI.DisplayTransform.get()
		
		if self.__linearColor.dimensions()==3 :
			displayColor = self._qtColor( displayTransform( self.__linearColor ) )
			self._qtWidget().color0 = self._qtWidget().color1 = displayColor
		else :
			c = self.__linearColor
			color0 = IECore.Color3f( 0.1 ) * ( 1.0 - c.a ) + IECore.Color3f( c.r, c.g, c.b ) * c.a
			color1 = IECore.Color3f( 0.2 ) * ( 1.0 - c.a ) + IECore.Color3f( c.r, c.g, c.b ) * c.a
			self._qtWidget().color0 = self._qtColor( displayTransform( color0 ) )
			self._qtWidget().color1 = self._qtColor( displayTransform( color1 ) )

		## \todo Colour should come from the style when we have styles applying to Widgets as well as Gadgets
		self._qtWidget().borderColor = QtGui.QColor( 119, 156, 255 ) if self.getHighlighted() else None

		self._qtWidget().update()
	
	def __displayTransformChanged( self ) :
	
		self.__updateCheckerColors()
	
# Private implementation - a QWidget derived class which just draws a checker with
# no knowledge of colour spaces or anything.
class _Checker( QtGui.QWidget ) :

	def __init__( self ) :
	
		QtGui.QWidget.__init__( self )
		
	def paintEvent( self, event ) :
	
		painter = QtGui.QPainter( self )
		rect = event.rect()
		
		if self.color0 != self.color1 :
			
			# draw checkerboard if colours differ
			checkSize = 6
						
			min = IECore.V2i( rect.x() / checkSize, rect.y() / checkSize )
			max = IECore.V2i( 1 + (rect.x() + rect.width()) / checkSize, 1 + (rect.y() + rect.height()) / checkSize )
						
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
			pen = QtGui.QPen( self.borderColor )
			pen.setWidth( 4 )
			painter.setPen( pen )
			painter.drawRect( 0, 0, self.width(), self.height() )

