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

	PositionChangedReason = IECore.Enum.create( "Invalid", "SetPositions", "Click", "IndexAdded", "IndexRemoved", "DragBegin", "DragMove", "DragEnd", "Increment" )

	def __init__( self, position=None, positions=None, **kw ) :
	
		GafferUI.Widget.__init__( self, _Widget(), **kw )
		
		assert( ( position is None ) or ( positions is None ) )
		
		if positions is not None :
			self.__positions = positions
		else :
			self.__positions = [ 0.5 if position is None else position ]
		
		self.__selectedIndex = None
		self.__sizeEditable = False
		self.__minimumSize = 1
		self.__positionIncrement = None
		self._entered = False
		
		self.__enterConnection = self.enterSignal().connect( Gaffer.WeakMethod( self.__enter ) )
		self.__leaveConnection = self.leaveSignal().connect( Gaffer.WeakMethod( self.__leave ) )
		self.__mouseMoveConnection = self.mouseMoveSignal().connect( Gaffer.WeakMethod( self.__mouseMove ) )
		self.__buttonPressConnection = self.buttonPressSignal().connect( Gaffer.WeakMethod( self.__buttonPress ) )
		self.__dragBeginConnection = self.dragBeginSignal().connect( Gaffer.WeakMethod( self.__dragBegin ) )
		self.__dragEnterConnection = self.dragEnterSignal().connect( Gaffer.WeakMethod( self.__dragEnter ) )
		self.__dragMoveConnection = self.dragMoveSignal().connect( Gaffer.WeakMethod( self.__dragMove ) )
		self.__dragEndConnection = self.dragEndSignal().connect( Gaffer.WeakMethod( self.__dragEnd ) )
		self.__keyPressConnection = self.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ) )
		
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
	
		self._setPositionsInternal( positions, self.PositionChangedReason.SetPositions )
				
	def getPositions( self ) :
	
		return self.__positions
	
	## A signal emitted whenever a position has been changed. Slots should
	# have the signature slot( Slider, PositionChangedReason ).
	def positionChangedSignal( self ) :
	
		signal = getattr( self, "_positionChangedSignal", None )
		if signal is None :
			signal = Gaffer.Signal2()
			self._positionChangedSignal = signal
			
		return signal
	
	## Returns True if a user would expect the specified sequence
	# of changes to be merged into one undoable event.
	@classmethod
	def changesShouldBeMerged( cls, firstReason, secondReason ) :
	
		if type( firstReason ) != type( secondReason ) :
			return False
	
		return ( firstReason, secondReason ) in (
			# click and drag
			( cls.PositionChangedReason.Click, cls.PositionChangedReason.DragBegin ),
			( cls.PositionChangedReason.DragBegin, cls.PositionChangedReason.DragMove ),
			( cls.PositionChangedReason.DragMove, cls.PositionChangedReason.DragMove ),
			( cls.PositionChangedReason.DragMove, cls.PositionChangedReason.DragEnd ),
			# increment
			( cls.PositionChangedReason.Increment, cls.PositionChangedReason.Increment ),			
		)
	
	def indexRemovedSignal( self ) :
	
		signal = getattr( self, "_indexRemovedSignal", None )
		if signal is None :
			signal = GafferUI.WidgetEventSignal()
			self._indexRemovedSignal = signal
			
		return signal
			
	def setSelectedIndex( self, index ) :
	
		if self.__selectedIndex == index :
			return
	
		if index is not None :
			if not len( self.__positions ) or index < 0 or index >= len( self.__positions ) :
				raise IndexError
			
		self.__selectedIndex = index
		self._qtWidget().update()

		signal = getattr( self, "_selectedIndexChangedSignal", None )
		if signal is not None :		
			signal( self )
			
	## May return None to indicate that no index is selected.
	def getSelectedIndex( self ) :
	
		return self.__selectedIndex

	def selectedIndexChangedSignal( self ) :
	
		signal = getattr( self, "_selectedIndexChangedSignal", None )
		if signal is None :
			signal = GafferUI.WidgetSignal()
			self._selectedIndexChangedSignal = signal
			
		return signal
	
	## Determines whether or not positions may be added/removed	
	def setSizeEditable( self, editable ) :
	
		self.__sizeEditable = editable
		
	def getSizeEditable( self ) :
	
		return self.__sizeEditable
	
	## Sets a size after which no more positions can
	# be removed.
	def setMinimumSize( self, minimumSize ) :
	
		self.__minimumSize = minimumSize
	
	def getMinimumSize( self ) :
	
		return self.__minimumSize
	
	## Sets the size of the position increment added/subtracted
	# when using the cursor keys. The default value of None
	# uses an increment equivalent to the size of one pixel at
	# the current slider size. An increment of 0 can be specified
	# to disable the behaviour entirely.
	## \todo Add setValueIncrement() method on NumericSlider.
	def setPositionIncrement( self, increment ) :
		
		self.__positionIncrement = increment
	
	def getPositionIncrement( self ) :
	
		return self.__positionIncrement
	
	## May be overridden by derived classes if necessary, but
	# implementations must call the base class implementation
	# after performing their own work, as the base class is
	# responsible for emitting positionChangedSignal().
	def _setPositionsInternal( self, positions, reason ) :
	
		dragBeginOrEnd = reason in ( self.PositionChangedReason.DragBegin, self.PositionChangedReason.DragEnd )
		if positions == self.__positions and not dragBeginOrEnd :
			# early out if the positions haven't changed, but not if the
			# reason is either end of a drag - we always signal those so
			# that they will always come in matching pairs.
			return
				
		self.__positions = positions
		self._qtWidget().update()
		
		self.__emitPositionChanged( reason )

	## \todo Colours should come from some unified style somewhere
	def _drawBackground( self, painter ) :
	
		size = self.size()

		pen = QtGui.QPen( QtGui.QColor( 0, 0, 0 ) )
		pen.setWidth( 1 )
		painter.setPen( pen )
		
		painter.drawLine( 0, size.y / 2, size.x, size.y / 2 )
		
	def _drawPosition( self, painter, position, highlighted, opacity=1 ) :
	
		size = self.size()

		pen = QtGui.QPen( QtGui.QColor( 0, 0, 0, 255 * opacity ) )
		pen.setWidth( 1 )
		painter.setPen( pen )
		
		## \todo These colours need to come from the style, once we've
		# unified the Gadget and Widget styling.
		if highlighted :
			brush = QtGui.QBrush( QtGui.QColor( 119, 156, 255, 255 * opacity ) )
		else :
			brush = QtGui.QBrush( QtGui.QColor( 128, 128, 128, 255 * opacity ) )
			
		painter.setBrush( brush )
		
		if position < 0 :
			painter.drawPolygon(
				QtGui.QPolygonF(
					[
						QtCore.QPointF( 8, 4 ),
						QtCore.QPointF( 8, size.y - 4 ),
						QtCore.QPointF( 2, size.y / 2 ),
					]
				)
			)
		elif position > 1 :
			painter.drawPolygon(
				QtGui.QPolygonF(
					[
						QtCore.QPointF( size.x - 8, 4 ),
						QtCore.QPointF( size.x - 8, size.y - 4 ),
						QtCore.QPointF( size.x - 2, size.y / 2 ),
					]
				)
			)
		else :
			painter.drawEllipse( QtCore.QPoint( position * size.x, size.y / 2 ), size.y / 4, size.y / 4 )
	
	def _indexUnderMouse( self ) :

		size = self.size()
		mousePosition = GafferUI.Widget.mousePosition( relativeTo = self ).x / float( size.x )
		
		result = None
		for i, p in enumerate( self.__positions ) :
			# clamp position inside 0-1 range so we can select
			# handles representing points outside the widget.
			p = max( min( p, 1.0 ), 0.0 )
			dist = math.fabs( mousePosition - p ) 
			if result is None or dist < minDist :
				result = i
				minDist = dist
		
		if not self.getSizeEditable() :
			# when the size isn't editable, we consider the closest
			# position to be under the mouse, this makes it easy
			# to just click anywhere to move the closest point.
			return result
		else :
			# but when the size is editable, we consider points to
			# be under the mouse when they genuinely are beneath it,
			# so that clicks elsewhere can add points.
			pixelDist = minDist * size.x
			if pixelDist < size.y / 2.0 :
				return result
			else :
				return None
	
	def __enter( self, widget ) :
	
		self._entered = True
		self._qtWidget().update()

	def __leave( self, widget ) :
	
		self._entered = False
		self._qtWidget().update()
	
	def __mouseMove( self, widget, event ) :
	
		self._qtWidget().update()

	def __buttonPress( self, widget, event ) :
	
		if event.buttons != GafferUI.ButtonEvent.Buttons.Left :
			return
		
		index = self._indexUnderMouse()
		if index is not None :
			self.setSelectedIndex( index )
			if len( self.getPositions() ) == 1 :
				self.__setPositionInternal( index, event.line.p0.x, self.PositionChangedReason.Click, clamp=True  )
		elif self.getSizeEditable() :
			positions = self.getPositions()[:]
			positions.append( float( event.line.p0.x ) / self.size().x )
			self._setPositionsInternal( positions, self.PositionChangedReason.IndexAdded )
			self.setSelectedIndex( len( positions ) - 1 )
			
		return True
	
	def __dragBegin( self, widget, event ) :
	
		if event.buttons == GafferUI.ButtonEvent.Buttons.Left and self.getSelectedIndex() is not None :
			return IECore.NullObject.defaultNullObject()
		
		return None
		
	def __dragEnter( self, widget, event ) :
	
		if event.sourceWidget is self :
			self.__setPositionInternal(
				self.getSelectedIndex(), event.line.p0.x,
				self.PositionChangedReason.DragBegin,
				clamp = not (event.modifiers & event.modifiers.Shift ),
			)
			return True
			
		return False
		
	def __dragMove( self, widget, event ) :
	
		self.__setPositionInternal(
			self.getSelectedIndex(), event.line.p0.x,
			self.PositionChangedReason.DragMove,
			clamp = not (event.modifiers & event.modifiers.Shift ),
		)

	def __dragEnd( self, widget, event ) :
	
		self.__setPositionInternal(
			self.getSelectedIndex(), event.line.p0.x,
			self.PositionChangedReason.DragEnd,
			clamp = not (event.modifiers & event.modifiers.Shift ),
		)
		
	def __keyPress( self, widget, event ) :
	
		if self.getSelectedIndex() is None :
			return False
		
		if event.key in ( "Left", "Right", "Up", "Down" ) :
			
			if self.__positionIncrement == 0 :
				return False
			
			if self.__positionIncrement is None :
				pixelIncrement = 1
			else :
				pixelIncrement = self.__positionIncrement * self.size().x
			
			x = self.getPositions()[self.getSelectedIndex()] * self.size().x
			x += pixelIncrement if event.key in ( "Right", "Up" ) else -pixelIncrement
			self.__setPositionInternal(
				self.getSelectedIndex(), x,
				self.PositionChangedReason.Increment,
				clamp = not (event.modifiers & event.modifiers.Shift ),
			)
			return True
		
		elif event.key in ( "Backspace", "Delete" ) :
		
			index = self.getSelectedIndex()
			if index is not None and self.getSizeEditable() and len( self.getPositions() ) > self.getMinimumSize() :
		
				del self.__positions[index]
				signal = getattr( self, "_indexRemovedSignal", None )
				if signal is not None :
					signal( self, index )
				self.__emitPositionChanged( self.PositionChangedReason.IndexRemoved )
				
				self._qtWidget().update()
				return True
					
		return False
		
	def __setPositionInternal( self, index, widgetX, reason, clamp ) :

		position = float( widgetX ) / self.size().x
		if clamp :
			position = min( 1.0, max( 0.0, position ) )
		
		positions = self.getPositions()[:]
		positions[index] = position
		self._setPositionsInternal( positions, reason )
		
	def __emitPositionChanged( self, reason ) :
	
		signal = getattr( self, "_positionChangedSignal", None )
		if signal is not None :
			signal( self, reason )
		
class _Widget( QtGui.QWidget ) :

	def __init__( self, parent=None ) :
	
		QtGui.QWidget.__init__( self, parent )
		
		self.setSizePolicy( QtGui.QSizePolicy( QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum ) )
		self.setFocusPolicy( QtCore.Qt.ClickFocus )
		
	def sizeHint( self ) :
	
		return QtCore.QSize( 200, 18 )
		
	def paintEvent( self, event ) :
		
		owner = GafferUI.Widget._owner( self )
		
		painter = QtGui.QPainter( self )
		painter.setRenderHint( QtGui.QPainter.Antialiasing )
		
		owner._drawBackground( painter )
		
		indexUnderMouse = owner._indexUnderMouse()
		for index, position in enumerate( owner.getPositions() ) :
			owner._drawPosition(
				painter,
				position,
				highlighted = index == indexUnderMouse or index == owner.getSelectedIndex()
			)
		
		if indexUnderMouse is None and owner.getSizeEditable() and owner._entered :
			mousePosition = GafferUI.Widget.mousePosition( relativeTo = owner ).x / float( owner.size().x )
			owner._drawPosition(
				painter,
				mousePosition,
				highlighted = True,
				opacity = 0.5
			)
			
	def event( self, event ) :
	
		if event.type() == event.ShortcutOverride :
			if event.key() in ( QtCore.Qt.Key_Delete, QtCore.Qt.Key_Backspace ) :
				event.accept()
				return True
			if event.key() in ( QtCore.Qt.Key_Up, QtCore.Qt.Key_Down, QtCore.Qt.Key_Left, QtCore.Qt.Key_Right ) :
				if GafferUI.Widget._owner( self ).getPositionIncrement() != 0 :
					event.accept()
					return True
				
		return QtGui.QWidget.event( self, event )
