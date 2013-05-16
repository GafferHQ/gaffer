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

import IECore

import Gaffer
import GafferUI

QtGui = GafferUI._qtImport( "QtGui" )

## \todo Fix bug when pressing up arrow with cursor to left of minus sign
class NumericWidget( GafferUI.TextWidget ) :

	def __init__( self, value, **kw ) :
	
		assert( isinstance( value, int ) or isinstance( value, float ) )
		self.__numericType = type( value )
		
		GafferUI.TextWidget.__init__( self, self.__valueToText( value ), **kw )
		
		if self.__numericType is int :
			validator = QtGui.QIntValidator( self._qtWidget() )
		else :
			validator = QtGui.QDoubleValidator( self._qtWidget() )
			validator.setDecimals( 4 )
			validator.setNotation( QtGui.QDoubleValidator.StandardNotation )
		
		self._qtWidget().setValidator( validator )
		
		self.__dragValue = None
		self.__dragStart = None
		
		self.__keyPressConnection = self.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ) )
		self.__buttonPressConnection = self.buttonPressSignal().connect( Gaffer.WeakMethod( self.__buttonPress ) )
		self.__dragBeginConnection = self.dragBeginSignal().connect( Gaffer.WeakMethod( self.__dragBegin ) )
		self.__dragEnterConnection = self.dragEnterSignal().connect( Gaffer.WeakMethod( self.__dragEnter ) )
		self.__dragMoveConnection = self.dragMoveSignal().connect( Gaffer.WeakMethod( self.__dragMove ) )
		self.__dragEndConnection = self.dragEndSignal().connect( Gaffer.WeakMethod( self.__dragEnd ) )
	
	def setValue( self, value ) :
	
		text = self.__valueToText( value )
		if text == self.getText() :
			return
			
		self.setText( text )
		self.__emitValueChanged()
		
	def getValue( self ) :
	
		return self.__numericType( self.getText() )
	
	## A signal emitted whenever the value has been changed and the user would expect
	# to see that change reflected in whatever the field controls.
	def valueChangedSignal( self ) :
	
		try :
			return self.__valueChangedSignal
		except AttributeError :
			self.__valueChangedSignal = GafferUI.WidgetSignal()
			self.__editingFinishedConnection = self.editingFinishedSignal().connect( Gaffer.WeakMethod( self.__editingFinished ) )
			
		return self.__valueChangedSignal
	
	def __valueToText( self, value ) :
	
		value = self.__numericType( value )
		if self.__numericType is int :
			return str( value )
		else :
			return ( "%.4f" % value ).rstrip( '0' ).rstrip( '.' )
		
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
		if '.' in text :
			decimalIndex = text.find( "." )
			if decimalIndex >= index :
				index += 1
		else :
			decimalIndex = len( text ) - 1
			
		powIndex = decimalIndex - index
		
		value = self.__numericType( text )			
		value += increment * self.__numericType( pow( 10, powIndex ) )
		
		self.setValue( value )
			
		# adjust the cursor position to be in the same column as before
		newText = self.getText()
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
		
		self.__dragValue = self.getValue()
		return True
	
	def __dragBegin( self, widget, event ) :
		
		if self.__dragValue is None :
			return None
		
		self.__dragStart = event.line.p0.x
		# IECore.NullObject is the convention for data for drags which are intended
		# only for the purposes of the originating widget.
		return IECore.NullObject.defaultNullObject()
	
	def __dragEnter( self, widget, event ) :
				
		if event.sourceWidget is self and self.__dragStart is not None :
			return True
		
		return False
	
	def __dragMove( self, widget, event ) : 
		
		move = event.line.p0.x - self.__dragStart
		
		offset = 0
		## \todo: come up with an official scheme after some user testing
		if event.modifiers == GafferUI.ModifiableEvent.Modifiers.Control :
			offset = 0.01 * move
		elif event.modifiers == GafferUI.ModifiableEvent.Modifiers.ShiftControl :
			offset = 0.00001 * math.pow( move, 3 )
		
		self.setValue( self.__dragValue + offset )
		return True
	
	def __dragEnd( self, widget, event ) :
		
		self.__dragValue = None
		self.__dragStart = None
		return True
	
	def __editingFinished( self, widget ) :
	
		assert( widget is self )
		
		self.__emitValueChanged()		
		
	def __emitValueChanged( self ) :
	
		try :
			signal = self.__valueChangedSignal
		except AttributeError :
			return
			
		signal( self )
