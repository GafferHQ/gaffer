##########################################################################
#
#  Copyright (c) 2011, John Haddon. All rights reserved.
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
import re
import operator

import six

import IECore

import Gaffer
import GafferUI

from Qt import QtGui

## \todo Fix bug when pressing up arrow with cursor to left of minus sign
class NumericWidget( GafferUI.TextWidget ) :

	ValueChangedReason = IECore.Enum.create( "Invalid", "SetValue", "DragBegin", "DragMove", "DragEnd", "Increment", "Edit", "InvalidEdit" )

	def __init__( self, value, **kw ) :

		GafferUI.TextWidget.__init__( self, "", **kw )

		self.__dragValue = None
		self.__dragStart = None

		self.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ), scoped = False )
		self.buttonPressSignal().connect( Gaffer.WeakMethod( self.__buttonPress ), scoped = False )
		self.dragBeginSignal().connect( Gaffer.WeakMethod( self.__dragBegin ), scoped = False )
		self.dragEnterSignal().connect( Gaffer.WeakMethod( self.__dragEnter ), scoped = False )
		self.dragMoveSignal().connect( Gaffer.WeakMethod( self.__dragMove ), scoped = False )
		self.dragEndSignal().connect( Gaffer.WeakMethod( self.__dragEnd ), scoped = False )
		self.editingFinishedSignal().connect( Gaffer.WeakMethod( self.__editingFinished ), scoped = False )

		self.setPreferredCharacterWidth( 10 )

		self.__numericType = None
		self.setValue( value )

	def setValue( self, value ) :

		self.__setValueInternal( value, self.ValueChangedReason.SetValue )

	def getValue( self ) :

		# Call `fixup()` so that we can always return a valid value,
		# even if the user is part way through entering an expression.
		value = self._qtWidget().validator().fixup( self.getText() )
		return self.__numericType( value )

	## A signal emitted whenever the value has been changed and the user would expect
	# to see that change reflected in whatever the field controls. Slots should have
	# the signature slot( NumericWidget, ValueChangedReason ).
	def valueChangedSignal( self ) :

		try :
			return self.__valueChangedSignal
		except AttributeError :
			self.__valueChangedSignal = Gaffer.Signal2()

		return self.__valueChangedSignal

	## Returns True if a user would expect the specified sequence
	# of changes to be merged into a single undoable event.
	@classmethod
	def changesShouldBeMerged( cls, firstReason, secondReason ) :

		if type( firstReason ) != type( secondReason ) :
			return False

		return ( firstReason, secondReason ) in (
			# drag
			( cls.ValueChangedReason.DragBegin, cls.ValueChangedReason.DragMove ),
			( cls.ValueChangedReason.DragMove, cls.ValueChangedReason.DragMove ),
			( cls.ValueChangedReason.DragMove, cls.ValueChangedReason.DragEnd ),
			# increment
			( cls.ValueChangedReason.Increment, cls.ValueChangedReason.Increment ),
		)

	## Returns the string used to display the given value.
	@staticmethod
	def valueToString( value ) :

		if type( value ) in six.integer_types :
			return str( value )
		else :
			return ( "%.4f" % value ).rstrip( '0' ).rstrip( '.' )

	def __valueToString( self, value ) :

		return self.valueToString( self.__numericType( value ) )

	def __keyPress( self, widget, event ) :

		assert( widget is self )

		if not self.getEditable() :
			return False

		if event.key=="Up" :
			self.__incrementIndex( self.getCursorPosition(), 1 )
			return True
		elif event.key=="Down" :
			self.__incrementIndex( self.getCursorPosition(), -1 )
			return True

		return False

	def __incrementIndex( self, index, increment ) :

		text = self.getText()
		if text == "" :
			return

		if '.' in text :
			decimalIndex = text.find( "." )
			if decimalIndex >= index :
				index += 1
		else :
			decimalIndex = len( text ) - 1

		powIndex = decimalIndex - index

		value = self.__numericType( text )
		value += increment * self.__numericType( pow( 10, powIndex ) )

		self.__setValueInternal( value, self.ValueChangedReason.Increment )

		newText = self.getText()

		# add any required leading or trailing 0 to ensure that
		# keyboard increments are consistent

		oldLengthBefore, oldHasPeriod, oldLengthAfter = [ len( item ) for item in text.lstrip( "-" ).partition( "." ) ]
		newLengthBefore, newHasPeriod, newLengthAfter = [ len( item ) for item in newText.lstrip( "-" ).partition( "." ) ]

		headPadding = "0" * max(0, oldLengthBefore - newLengthBefore )
		tailPadding = "0" * max(0, oldLengthAfter - newLengthAfter )

		if not newHasPeriod and tailPadding :
			tailPadding = "." + tailPadding

		if newText[0] == "-" :
			newText = "-" + headPadding + newText[1:] + tailPadding
		else:
			newText = headPadding + newText + tailPadding

		self.setText( newText )

		# adjust the cursor position to be in the same column as before
		if '.' in newText :
			newDecimalIndex = newText.find( "." )
			newIndex = newDecimalIndex - powIndex
			if powIndex >= 0 :
				newIndex -= 1
		else :
			newIndex = len( newText ) - 1 - powIndex
		if newIndex < 0 :
			newIndex = 0

		self.setCursorPosition( newIndex )

	def __buttonPress( self, widget, event ) :

		if not self.getEditable() :
			return False

		if event.buttons != GafferUI.ButtonEvent.Buttons.Left :
			return False

		if event.modifiers != GafferUI.ModifiableEvent.Modifiers.Control and event.modifiers != GafferUI.ModifiableEvent.Modifiers.ShiftControl :
			return False

		try :
			self.__dragValue = self.getValue()
			return True
		except :
			# `getValue()` may fail if the field is empty,
			# in which case we don't have a value to drag.
			return False

	def __dragBegin( self, widget, event ) :

		if self.__dragValue is None :
			return None

		self.__dragStart = event.line.p0.x
		# IECore.NullObject is the convention for data for drags which are intended
		# only for the purposes of the originating widget.
		return IECore.NullObject.defaultNullObject()

	def __dragEnter( self, widget, event ) :

		if event.sourceWidget is self and self.__dragStart is not None :
			self.__setValueFromDrag( event, self.ValueChangedReason.DragBegin )
			return True

		return False

	def __dragMove( self, widget, event ) :

		self.__setValueFromDrag( event, self.ValueChangedReason.DragMove )
		return True

	def __dragEnd( self, widget, event ) :

		self.__setValueFromDrag( event, self.ValueChangedReason.DragEnd )
		self.__dragValue = None
		self.__dragStart = None
		return True

	def __setValueFromDrag( self, event, reason ) :

		move = event.line.p0.x - self.__dragStart

		offset = 0
		## \todo: come up with an official scheme after some user testing
		if event.modifiers == GafferUI.ModifiableEvent.Modifiers.Control :
			offset = 0.01 * move
		elif event.modifiers == GafferUI.ModifiableEvent.Modifiers.ShiftControl :
			offset = 0.00001 * math.pow( move, 3 )

		newValue = self.__numericType( float( self.__dragValue ) + offset )

		self.__setValueInternal( newValue, reason )

	def __editingFinished( self, widget ) :

		assert( widget is self )

		reason = self.ValueChangedReason.Edit

		# In __incrementIndex we temporarily pad with leading
		# zeroes in order to achieve consistent editing. Revert
		# back to our standard form now so we don't leave it in
		# this state.
		try :
			self.setText( self.__valueToString( self.getValue() ) )
		except ValueError as e :
			reason = self.ValueChangedReason.InvalidEdit

		self.__emitValueChanged( reason )

	def __setValueInternal( self, value, reason ) :

		# update our validator based on the type of the value
		numericType = type( value )
		assert( numericType in six.integer_types or numericType is float )
		if self.__numericType is not numericType :

			self.__numericType = numericType
			self._qtWidget().setValidator( _ExpressionValidator( self._qtWidget(), self.__numericType ) )

		# update our textual value
		text = self.__valueToString( value )
		dragBeginOrEnd = reason in ( self.ValueChangedReason.DragBegin, self.ValueChangedReason.DragEnd )

		if text == self.getText() and not dragBeginOrEnd :
			# early out if the text hasn't changed. we never early out if the reason is
			# drag start or drag end, as we want to maintain matching pairs so things
			# make sense to client code.
			return

		self.setText( text )
		self.__emitValueChanged( reason )

	def __emitValueChanged( self, reason ) :

		try :
			signal = self.__valueChangedSignal
		except AttributeError :
			return

		signal( self, reason )

# A basic validator/evaluator that supports simple maths
# operators [+-/*] along with standard number validation, eg:
#   2 + 3
#   4.4 / 2
# Qt will call validate/fixup as part of the edit cycle.
class _ExpressionValidator( QtGui.QValidator ) :

	def __init__( self, parent, numericType ) :

		QtGui.QValidator.__init__( self, parent )

		self.__numericType = numericType
		if self.__numericType in six.integer_types :
			operand = r"-?[0-9]*"
		else :
			operand = r"-?[0-9]*\.?[0-9]{0,4}"

		# Captures `( operand1, operator, operand2 )``, with the latter
		# two being optional. Note that the regex for the operands is
		# deliberately loose and accepts incomplete text such as "", "-"
		# and ".". This is dealt with in `validate()` and `fixup()`.
		self.__expression = re.compile(
			r"^\s*({operand})\s*(?:([-+*/%])\s*({operand}))?\s*$".format(
				operand = operand
			)
		)

	def fixup( self, text ) :

		match = re.match( self.__expression, text )
		try :
			operand1 = self.__numericType( match.group( 1 ) )
		except :
			return text

		try :
			operand2 = self.__numericType( match.group( 3 ) )
		except :
			# Incomplete expression, return first number
			return match.group( 1 )

		# Evaluate expression

		op = {
			"/" : operator.floordiv if self.__numericType in six.integer_types else operator.truediv,
			"*" : operator.mul,
			"+" : operator.add,
			"-" : operator.sub,
			"%" : operator.mod
		}[match.group(2)]

		try :
			return str( op( operand1, operand2 ) )
		except ZeroDivisionError :
			return match.group( 1 )

	def validate( self, text, pos ) :

		# Work around https://bugreports.qt.io/browse/PYSIDE-106. Because
		# that prevents `fixup()` from working, it stops Qt automatically
		# fixing `Intermediate` input when editing finishes, which in turn stops
		# `QLineEdit.editingFinished` from being emitted. We return `Acceptable`
		# instead of `Intermediate` and then apply `fixup()` ourselves via
		# `__editingFinished()` and `getValue()`.
		## \todo Remove once we've moved to GafferHQ/dependencies 2.0.0, which
		# contains the relevant PySide fix. Include a grace period for folks
		# building with their own older dependencies.
		Intermediate = QtGui.QValidator.Acceptable

		match = re.match( self.__expression, text )
		if match is None :
			return QtGui.QValidator.Invalid, text, pos

		# Check first operand
		try :
			self.__numericType( match.group( 1 ) )
		except :
			return (
				Intermediate if not match.group( 2 ) else QtGui.QValidator.Invalid,
				text, pos
			)

		# If operator is present, check second operand
		if match.group( 2 ) :
			try :
				self.__numericType( match.group( 3 ) )
			except :
				return Intermediate, text, pos

		return QtGui.QValidator.Acceptable, text, pos
