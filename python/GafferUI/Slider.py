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

import math

import Gaffer
import GafferUI

QtCore = GafferUI._qtImport( "QtCore" )
QtGui = GafferUI._qtImport( "QtGui" )

## The Slider class allows a user to specify a position on a scale of 0.0 at one end
# of the Widget and 1.0 at the other. Positions off the ends of the widget are mapped
# to negative numbers and numbers greater than 1.0 respectively. Derived classes may
# provide alternative interpretations for the scale and clamp values as appropriate. In
# particular see the NumericSlider which allows the specification of the values at either
# end of the scale along with hard minimum and maximum values.
class Slider( GafferUI.Widget ) :

	def __init__( self, position = 0.5, **kw ) :
	
		GafferUI.Widget.__init__( self, _Widget(), **kw )
				
		self.__position = position

		self.__buttonPressConnection = self.buttonPressSignal().connect( Gaffer.WeakMethod( self.__buttonPress ) )
		self.__mouseMoveConnection = self.mouseMoveSignal().connect( Gaffer.WeakMethod( self.__mouseMove ) )
		self.__enterConnection = self.enterSignal().connect( Gaffer.WeakMethod( self.__enter ) )
		self.__leaveConnection = self.leaveSignal().connect( Gaffer.WeakMethod( self.__leave ) )
		
	def setPosition( self, p ) :
				
		if p!=self.__position :
		
			self.__position = p
			self._qtWidget().update()
			
			try :
				signal = self.__positionChangedSignal
			except :
				return
			
			signal( self )
			
	def getPosition( self ) :
	
		return self.__position	
	
	def positionChangedSignal( self ) :
	
		try :
			return self.__positionChangedSignal
		except :
			self.__positionChangedSignal = GafferUI.WidgetSignal()
			
		return self.__positionChangedSignal
	
	## \todo Colours should come from some unified style somewhere
	def _drawBackground( self, painter ) :
	
		size = self.size()

		pen = QtGui.QPen( QtGui.QColor( 0, 0, 0 ) )
		pen.setWidth( 1 )
		painter.setPen( pen )
		
		painter.drawLine( 0, size.y / 2, size.x, size.y / 2 )
		
	def _drawPosition( self, painter ) :
	
		size = self.size()

		pen = QtGui.QPen( QtGui.QColor( 0, 0, 0 ) )
		pen.setWidth( 1 )
		painter.setPen( pen )
		
		## \todo These colours need to come from the style, once we've
		# unified the Gadget and Widget styling.
		if self.getHighlighted() :
			brush = QtGui.QBrush( QtGui.QColor( 119, 156, 255 ) )
		else :
			brush = QtGui.QBrush( QtGui.QColor( 128, 128, 128 ) )
			
		painter.setBrush( brush )
		
		if self.__position < 0 :
			painter.drawPolygon(
				QtCore.QPoint( 8, 4 ),
				QtCore.QPoint( 8, size.y - 4 ),
				QtCore.QPoint( 2, size.y / 2 ),
			)
		elif self.__position > 1 :
			painter.drawPolygon(
				QtCore.QPoint( size.x - 8, 4 ),
				QtCore.QPoint( size.x - 8, size.y - 4 ),
				QtCore.QPoint( size.x - 2, size.y / 2 ),
			)
		else :
			painter.drawEllipse( QtCore.QPoint( self.__position * size.x, size.y / 2 ), size.y / 4, size.y / 4 )
					
	def __buttonPress( self, widget, event ) :
	
		if event.buttons & GafferUI.ButtonEvent.Buttons.Left :
			self.setPosition( float( event.line.p0.x ) / self.size().x )
			return True
			
		return False

	def __mouseMove( self, widget, event ) :
	
		if event.buttons & GafferUI.ButtonEvent.Buttons.Left :
			self.setPosition( float( event.line.p0.x ) / self.size().x )

	def __enter( self, widget ) :
	
		self.setHighlighted( True )
		
	def __leave( self, widget ) :
	
		self.setHighlighted( False )
		
class _Widget( QtGui.QWidget ) :

	def __init__( self, parent=None ) :
	
		QtGui.QWidget.__init__( self, parent )
		
		self.setSizePolicy( QtGui.QSizePolicy( QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum ) )

	def sizeHint( self ) :
	
		return QtCore.QSize( 150, 18 )
		
	def paintEvent( self, event ) :
	
		owner = GafferUI.Widget._owner( self )
		
		painter = QtGui.QPainter( self )
		painter.setRenderHint( QtGui.QPainter.Antialiasing )
		
		owner._drawBackground( painter )
		owner._drawPosition( painter )
	