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
import six

import IECore

import Gaffer
import GafferUI

from Qt import QtCore
from Qt import QtGui
from Qt import QtWidgets

class Slider( GafferUI.Widget ) :

	ValueChangedReason = IECore.Enum.create( "Invalid", "SetValues", "Click", "IndexAdded", "IndexRemoved", "DragBegin", "DragMove", "DragEnd", "Increment" )

	# The min and max arguments define the numeric values at the ends of the slider.
	# By default, values outside this range will be clamped, but hardMin and hardMax
	# may be specified to move the point at which the clamping happens outside of the
	# slider itself.
	#
	# A single slider may show more than one value. Multiple values may be specified
	# by passing a list to the `values` argument, or calling `setValues()` after
	# construction.
	def __init__( self, values=0.5, min=0, max=1, hardMin=None, hardMax=None, **kw ) :

		if "value" in kw :
			# Backwards compatibility with old `value` argument
			assert( values == 0.5 )
			values = kw["value"]
			del kw["value"]

		GafferUI.Widget.__init__( self, _Widget(), **kw )

		self.__min = min
		self.__max = max
		self.__hardMin = hardMin if hardMin is not None else self.__min
		self.__hardMax = hardMax if hardMax is not None else self.__max

		self.__selectedIndex = None
		self.__sizeEditable = False
		self.__minimumSize = 1
		self.__increment = None
		self._entered = False

		self.enterSignal().connect( Gaffer.WeakMethod( self.__enter ), scoped = False )
		self.leaveSignal().connect( Gaffer.WeakMethod( self.__leave ), scoped = False )
		self.mouseMoveSignal().connect( Gaffer.WeakMethod( self.__mouseMove ), scoped = False )
		self.buttonPressSignal().connect( Gaffer.WeakMethod( self.__buttonPress ), scoped = False )
		self.dragBeginSignal().connect( Gaffer.WeakMethod( self.__dragBegin ), scoped = False )
		self.dragEnterSignal().connect( Gaffer.WeakMethod( self.__dragEnter ), scoped = False )
		self.dragMoveSignal().connect( Gaffer.WeakMethod( self.__dragMove ), scoped = False )
		self.dragEndSignal().connect( Gaffer.WeakMethod( self.__dragEnd ), scoped = False )
		self.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ), scoped = False )

		self.__values = []
		if isinstance( values, ( six.integer_types, float ) ) :
			self.__setValuesInternal( [ values ], self.ValueChangedReason.SetValues )
		else :
			self.__setValuesInternal( values, self.ValueChangedReason.SetValues )

	## Convenience function to call setValues( [ value ] )
	def setValue( self, value ) :

		self.setValues( [ value ] )

	## Convenience function returning getValues()[0] if there
	# is only one value, and raising ValueError if not.
	def getValue( self ) :

		if len( self.__values ) != 1 :
			raise ValueError

		return self.__values[0]

	def setValues( self, values ) :

		self.__setValuesInternal( values, self.ValueChangedReason.SetValues )

	def getValues( self ) :

		return self.__values

	## A signal emitted whenever a value has been changed. Slots should
	# have the signature slot( Slider, ValueChangedReason ).
	def valueChangedSignal( self ) :

		try :
			return self.__valueChangedSignal
		except :
			self.__valueChangedSignal = Gaffer.Signal2()

		return self.__valueChangedSignal

	## Returns True if a user would expect the specified sequence
	# of changes to be merged into one undoable event.
	@classmethod
	def changesShouldBeMerged( cls, firstReason, secondReason ) :

		if type( firstReason ) != type( secondReason ) :
			return False

		return ( firstReason, secondReason ) in (
			# click and drag
			( cls.ValueChangedReason.Click, cls.ValueChangedReason.DragBegin ),
			( cls.ValueChangedReason.DragBegin, cls.ValueChangedReason.DragMove ),
			( cls.ValueChangedReason.DragMove, cls.ValueChangedReason.DragMove ),
			( cls.ValueChangedReason.DragMove, cls.ValueChangedReason.DragEnd ),
			# increment
			( cls.ValueChangedReason.Increment, cls.ValueChangedReason.Increment ),
		)

	def setRange( self, min, max, hardMin=None, hardMax=None ) :

		if hardMin is None :
			hardMin = min
		if hardMax is None :
			hardMax = max

		if min==self.__min and max==self.__max and hardMin==self.__hardMin and hardMax==self.__hardMax :
			return

		self.__min = min
		self.__max = max
		self.__hardMin = hardMin
		self.__hardMax = hardMax

		self.__setValuesInternal( self.__values, self.ValueChangedReason.Invalid ) # reclamps the values to the range if necessary
		self._qtWidget().update()

	def getRange( self ) :

		return self.__min, self.__max, self.__hardMin, self.__hardMax

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
			if not len( self.__values ) or index < 0 or index >= len( self.__values ) :
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

	## Determines whether or not values may be added/removed
	def setSizeEditable( self, editable ) :

		self.__sizeEditable = editable

	def getSizeEditable( self ) :

		return self.__sizeEditable

	## Sets a size after which no more values can
	# be removed.
	def setMinimumSize( self, minimumSize ) :

		self.__minimumSize = minimumSize

	def getMinimumSize( self ) :

		return self.__minimumSize

	## Sets the value increment added/subtracted
	# when using the cursor keys. The default value of None
	# uses an increment equivalent to the size of one pixel at
	# the current slider size. An increment of 0 can be specified
	# to disable the behaviour entirely.
	def setIncrement( self, increment ) :

		self.__increment = increment

	def getIncrement( self ) :

		return self.__increment

	def __setValuesInternal( self, values, reason ) :

		# We _always_ clamp to the hard min and max, as those are not optional.
		# Optional clamping to soft min and max is performed before calling this
		# function.
		values = [ max( self.__hardMin, min( self.__hardMax, x ) ) for x in values ]

		dragBeginOrEnd = reason in ( self.ValueChangedReason.DragBegin, self.ValueChangedReason.DragEnd )
		if values == self.__values and not dragBeginOrEnd :
			# early out if the values haven't changed, but not if the
			# reason is either end of a drag - we always signal those so
			# that they will always come in matching pairs.
			return

		self.__values = values
		self._qtWidget().update()

		self.__emitValueChanged( reason )

	## \todo Colours should come from some unified style somewhere
	def _drawBackground( self, painter ) :

		size = self.size()
		valueRange = self.__max - self.__min
		if valueRange == 0 :
			return

		idealSpacing = 10
		idealNumTicks = float( size.x ) / idealSpacing
		tickStep = valueRange / idealNumTicks

		logTickStep = math.log10( tickStep )
		flooredLogTickStep = math.floor( logTickStep )
		tickStep = math.pow( 10, flooredLogTickStep )
		blend = (logTickStep - flooredLogTickStep)

		tickValue = math.floor( self.__min / tickStep ) * tickStep
		i = 0
		while tickValue <= self.__max :
			x = size.x * ( tickValue - self.__min ) / valueRange
			if i % 100 == 0 :
				height0 = height1 = 0.75
				alpha0 = alpha1 = 1
			elif i % 50 == 0 :
				height0 = 0.75
				height1 = 0.5
				alpha0 = alpha1 = 1
			elif i % 10 == 0 :
				height0 = 0.75
				height1 = 0.25
				alpha0 = alpha1 = 1
			elif i % 5 == 0 :
				height0 = 0.5
				height1 = 0
				alpha0 = 1
				alpha1 = 0
			else :
				height0 = 0.25
				height1 = 0
				alpha0 = 1
				alpha1 = 0

			alpha = alpha0 + (alpha1 - alpha0) * blend
			height = height0 + (height1 - height0) * blend

			pen = QtGui.QPen()
			pen.setWidth( 0 )
			pen.setColor( QtGui.QColor( 0, 0, 0, alpha * 255 ) )
			painter.setPen( pen )

			painter.drawLine( x, size.y, x, size.y * ( 1 - height ) )
			tickValue += tickStep
			i += 1

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
		elif position > size.x :
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
			painter.drawEllipse( QtCore.QPoint( position, size.y / 2 ), size.y / 4, size.y / 4 )

	def _indexUnderMouse( self ) :

		size = self.size()
		mousePosition = GafferUI.Widget.mousePosition( relativeTo = self ).x

		result = None
		for i, v in enumerate( self.__values ) :
			# clamp value inside range so we can select
			# handles representing points outside the widget.
			v = max( min( v, self.__max ), self.__min )
			dist = math.fabs( mousePosition - self.__valueToPosition( v ) )
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
			if minDist < size.y / 2.0 :
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
			if len( self.getValues() ) == 1 :
				self.__setValueInternal( index, self.__positionToValue( event.line.p0.x, clamp = True ), self.ValueChangedReason.Click )
		elif self.getSizeEditable() :
			values = self.getValues()[:]
			values.append( self.__positionToValue( event.line.p0.x, clamp = True ) )
			self.__setValuesInternal( values, self.ValueChangedReason.IndexAdded )
			self.setSelectedIndex( len( self.getValues() ) - 1 )

		return True

	def __dragBegin( self, widget, event ) :

		if event.buttons == GafferUI.ButtonEvent.Buttons.Left and self.getSelectedIndex() is not None :
			return IECore.NullObject.defaultNullObject()

		return None

	def __dragEnter( self, widget, event ) :

		if event.sourceWidget is self :
			return True

		return False

	def __dragMove( self, widget, event ) :

		self.__setValueInternal(
			self.getSelectedIndex(),
			self.__positionToValue(
				event.line.p0.x,
				clamp = not (event.modifiers & event.modifiers.Shift )
			),
			self.ValueChangedReason.DragMove
		)

	def __dragEnd( self, widget, event ) :

		self.__dragMove( widget, event )

	def __keyPress( self, widget, event ) :

		if self.getSelectedIndex() is None :
			return False

		if event.key in ( "Left", "Right", "Up", "Down" ) :

			if self.__increment == 0 :
				return False

			if self.__increment is None :
				increment = ( self.__max - self.__min ) / float( self.size().x )
			else :
				increment = self.__increment

			x = self.getValues()[self.getSelectedIndex()]
			x += increment if event.key in ( "Right", "Up" ) else -increment
			if not (event.modifiers & event.modifiers.Shift ) :
				x = max( self.__min, min( self.__max, x ) )

			self.__setValueInternal(
				self.getSelectedIndex(), x,
				self.ValueChangedReason.Increment,
			)
			return True

		elif event.key in ( "Backspace", "Delete" ) :

			index = self.getSelectedIndex()
			if index is not None and self.getSizeEditable() and len( self.getValues() ) > self.getMinimumSize() :

				del self.__values[index]
				signal = getattr( self, "_indexRemovedSignal", None )
				if signal is not None :
					signal( self, index )
				self.__emitValueChanged( self.ValueChangedReason.IndexRemoved )

				self._qtWidget().update()
				return True

		return False

	def __setValueInternal( self, index, value, reason ) :

		values = self.getValues()[:]
		values[index] = value
		self.__setValuesInternal( values, reason )

	def __emitValueChanged( self, reason ) :

		try :
			signal = self.__valueChangedSignal
		except :
			return

		signal( self, reason )

	def __positionToValue( self, position, clamp = False ) :

		f = position / float( self.size().x )
		value = self.__min + ( self.__max - self.__min ) * f
		if clamp :
			value = max( self.__min, min( self.__max, value ) )

		return value

	def __valueToPosition( self, value ) :

		f = ( value - self.__min ) / ( self.__max - self.__min )
		return f * self.size().x

class _Widget( QtWidgets.QWidget ) :

	def __init__( self, parent=None ) :

		QtWidgets.QWidget.__init__( self, parent )

		self.setSizePolicy( QtWidgets.QSizePolicy( QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum ) )
		self.setFocusPolicy( QtCore.Qt.ClickFocus )

	def sizeHint( self ) :

		return QtCore.QSize( 200, 18 )

	def paintEvent( self, event ) :

		owner = GafferUI.Widget._owner( self )

		painter = QtGui.QPainter( self )
		painter.setRenderHint( QtGui.QPainter.Antialiasing )

		owner._drawBackground( painter )

		indexUnderMouse = owner._indexUnderMouse()
		for index, value in enumerate( owner.getValues() ) :
			owner._drawPosition(
				painter,
				owner._Slider__valueToPosition( value ),
				highlighted = index == indexUnderMouse or index == owner.getSelectedIndex()
			)

		if indexUnderMouse is None and owner.getSizeEditable() and owner._entered :
			owner._drawPosition(
				painter,
				GafferUI.Widget.mousePosition( relativeTo = owner ).x,
				highlighted = True,
				opacity = 0.5
			)

	def event( self, event ) :

		if event.type() == event.ShortcutOverride :
			if event.key() in ( QtCore.Qt.Key_Delete, QtCore.Qt.Key_Backspace ) :
				event.accept()
				return True
			if event.key() in ( QtCore.Qt.Key_Up, QtCore.Qt.Key_Down, QtCore.Qt.Key_Left, QtCore.Qt.Key_Right ) :
				if GafferUI.Widget._owner( self ).getIncrement() != 0 :
					event.accept()
					return True

		return QtWidgets.QWidget.event( self, event )
