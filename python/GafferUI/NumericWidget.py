##########################################################################
#  
#  Copyright (c) 2011, John Haddon. All rights reserved.
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

import Gaffer
import GafferUI

QtGui = GafferUI._qtImport( "QtGui" )

## \todo Fix bug when pressing up arrow with cursor to left of minus sign
class NumericWidget( GafferUI.TextWidget ) :

	def __init__( self, value, **kw ) :
	
		GafferUI.TextWidget.__init__( self, str( value ), **kw )
		
		assert( isinstance( value, int ) or isinstance( value, float ) )
		
		self.__numericType = type( value )
		
		if self.__numericType is int :
			validator = QtGui.QIntValidator( self._qtWidget() )
		else :
			validator = QtGui.QDoubleValidator( self._qtWidget() )
		
		self._qtWidget().setValidator( validator )
		
		self.__keyPressConnection = self.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ) )
	
	def setValue( self, value ) :
	
		self.setText( str( self.__numericType( value ) ) )
		
	def getValue( self ) :
	
		return self.__numericType( self.getText() )
		
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
