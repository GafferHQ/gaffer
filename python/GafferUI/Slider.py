##########################################################################
#  
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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

import IECore

import Gaffer
import GafferUI

QtCore = GafferUI._qtImport( "QtCore" )
QtGui = GafferUI._qtImport( "QtGui" )

## The Slider class allows a user to specify a number of positions on a scale of 0.0 at one end
# of the Widget and 1.0 at the other. Positions off the ends of the widget are mapped
# to negative numbers and numbers greater than 1.0 respectively. Derived classes may
# provide alternative interpretations for the scale and clamp values as appropriate. In
# particular see the NumericSlider which allows the specification of the values at either
# end of the scale along with hard minimum and maximum values.
class Slider( GafferUI.Widget ) :

	def __init__( self, position=None, positions=None, **kw ) :
	
		GafferUI.Widget.__init__( self, _Widget(), **kw )
		
		assert( ( position is None ) or ( positions is None ) )
		
		if positions is not None :
			self.__positions = positions
		else :
			self.__positions = [ 0.5 if position is None else position ]
		
		self.__selectedIndex = None
		
		self.__mouseMoveConnection = self.mouseMoveSignal().connect( Gaffer.WeakMethod( self.__mouseMove ) )
		self.__buttonPressConnection = self.buttonPressSignal().connect( Gaffer.WeakMethod( self.__buttonPress ) )
		self.__dragBeginConnection = self.dragBeginSignal().connect( Gaffer.WeakMethod( self.__dragBegin ) )
		self.__dragEnterConnection = self.dragEnterSignal().connect( Gaffer.WeakMethod( self.__dragEnter ) )
		self.__dragMoveConnection = self.dragMoveSignal().connect( Gaffer.WeakMethod( self.__dragMove ) )

	## Convenience function to call setPositions( [ position ] )	
	def setPosition( self, p ) :
	
		self.setPositions( [ p ] )
		
	## Convenience function returning getPositions()[0] if there
	# is only one position, and raising ValueError if not.
	def getPosition( self ) :
		
		if len( self.__positions ) != 1 :
			raise ValueError
			
		return self.__positions[0]

	def setPositions( self, positions ) :
	
		if positions == self.__positions :
			return
				
		self.__positions = positions
		self._qtWidget().update()
			
		try :
			signal = self.__positionChangedSignal
		except :
			return
		
		signal( self )
		
	def getPositions( self ) :
	
		return self.__positions
		
	def positionChangedSignal( self ) :
	
		try :
			return self.__positionChangedSignal
		except :
			self.__positionChangedSignal = GafferUI.WidgetSignal()
			
		return self.__positionChangedSignal
	
	def setSelectedIndex( self, index ) :
	
		if self.__selectedIndex == index :
			return
	
		if index is not None :
			if not len( self.__positions ) or index < 0 or index >= len( self.__positions ) :
				raise IndexError
			
		self.__selectedIndex = index
		self._qtWidget().update()

		try :
			signal = self.__selectedIndexChangedSignal
		except :
			return
			
		signal( self )
			
	## May return None to indicate that no index is selected.
	def getSelectedIndex( self ) :
	
		return self.__selectedIndex

	def selectedIndexChangedSignal( self ) :
	
		try :
			return self.__selectedIndexChangedSignal
		except :
			self.__selectedIndexChangedSignal = GafferUI.WidgetSignal()
			
		return self.__selectedIndexChangedSignal
	
	## \todo Colours should come from some unified style somewhere
	def _drawBackground( self, painter ) :
	
		size = self.size()

		pen = QtGui.QPen( QtGui.QColor( 0, 0, 0 ) )
		pen.setWidth( 1 )
		painter.setPen( pen )
		
		painter.drawLine( 0, size.y / 2, size.x, size.y / 2 )
		
	def _drawPosition( self, painter, position, selected, highlighted, opacity=1 ) :
	
		size = self.size()

		pen = QtGui.QPen( QtGui.QColor( 0, 0, 0, 255 * opacity ) )
		pen.setWidth( 1 )
		painter.setPen( pen )
		
		## \todo These colours need to come from the style, once we've
		# unified the Gadget and Widget styling.
		if selected :
			brush = QtGui.QBrush( QtGui.QColor( 119, 156, 255, 255 * opacity ) )
		elif highlighted :
			brush = QtGui.QBrush( QtGui.QColor( 124, 142, 191, 255 * opacity ) )
		else :
			brush = QtGui.QBrush( QtGui.QColor( 128, 128, 128, 255 * opacity ) )
			
		painter.setBrush( brush )
		
		if position < 0 :
			painter.drawPolygon(
				QtCore.QPoint( 8, 4 ),
				QtCore.QPoint( 8, size.y - 4 ),
				QtCore.QPoint( 2, size.y / 2 ),
			)
		elif position > 1 :
			painter.drawPolygon(
				QtCore.QPoint( size.x - 8, 4 ),
				QtCore.QPoint( size.x - 8, size.y - 4 ),
				QtCore.QPoint( size.x - 2, size.y / 2 ),
			)
		else :
			painter.drawEllipse( QtCore.QPoint( position * size.x, size.y / 2 ), size.y / 4, size.y / 4 )
	
	def _closestIndex( self, position ) :

		result = None
		for i, p in enumerate( self.__positions ) :
			dist = math.fabs( position - p ) 
			if result is None or dist < minDist :
				result = i
				minDist = dist
			
		return result
		
	def __mouseMove( self, widget, event ) :
	
		self._qtWidget().update()

	def __buttonPress( self, widget, event ) :
	
		if event.buttons != GafferUI.ButtonEvent.Buttons.Left :
			return
			
		position = float( event.line.p0.x ) / self.size().x
		self.setSelectedIndex( self._closestIndex( position ) )
		
		if len( self.getPositions() ) == 1 :
			positions = self.getPositions()[:]
			positions[self.getSelectedIndex()] = position
			self.setPositions( positions )
		
		return True
	
	def __dragBegin( self, widget, event ) :
	
		if event.buttons == GafferUI.ButtonEvent.Buttons.Left and self.getSelectedIndex() is not None :
			return IECore.NullObject.defaultNullObject()
		
		return None
		
	def __dragEnter( self, widget, event ) :
	
		return event.sourceWidget is self
		
	def __dragMove( self, widget, event ) :
	
		positions = self.getPositions()[:]
		positions[self.getSelectedIndex()] = float( event.line.p0.x ) / self.size().x
		self.setPositions( positions )
		
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
		
		closestIndex = owner._closestIndex( GafferUI.Widget.mousePosition( relativeTo = owner ).x / float( owner.size().x ) )
		for index, position in enumerate( owner.getPositions() ) :
			owner._drawPosition(
				painter,
				position,
				selected = index == owner.getSelectedIndex(),
				highlighted = index == closestIndex
			)
	