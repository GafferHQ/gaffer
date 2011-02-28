##########################################################################
#  
#  Copyright (c) 2011, John Haddon. All rights reserved.
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

from PySide import QtCore
from PySide import QtGui

import IECore

import GafferUI

class TextWidget( GafferUI.Widget ) :

	def __init__( self, text="", editable=True ) :
	
		GafferUI.Widget.__init__( self, QtGui.QLineEdit() )

		self._qtWidget().textChanged.connect( self.__textChanged )
		self._qtWidget().returnPressed.connect( self.__returnPressed )

		self.setText( text )
		self.setEditable( editable )
		
	def setText( self, text ) :
	
		self._qtWidget().setText( text )
		
	def getText( self ) :
	
		return str( self._qtWidget().text() )

	def setEditable( self, editable ) :
	
		self._qtWidget().setReadOnly( not editable )

	def getEditable( self ) :
		
		return not self._qtWidget().isReadOnly()
	
	def setCursorPosition( self, position ) :
	
		self._qtWidget().setCursorPosition( position )
		
	def getCursorPosition( self ) :
	
		return self._qtWidget().cursorPosition()
	
	def textChangedSignal( self ) :
	
		try :
			return self.__textChangedSignal
		except :
			self.__textChangedSignal = GafferUI.WidgetSignal()
			
		return self.__textChangedSignal

	## \todo Should this be moved to the Widget class?
	def grabFocus( self ) :
	
		self._qtWidget().setFocus( QtCore.Qt.OtherFocusReason )

	## A signal emitted when enter is pressed.
	def activatedSignal( self ) :
	
		try :
			return self.__activatedSignal
		except :
			self.__activatedSignal = GafferUI.WidgetSignal()
			
		return self.__activatedSignal

	## Returns the character index underneath the specified
	# ButtonEvent.
	def _eventPosition( self, event ) :
	
		return self._qtWidget().cursorPositionAt( QtCore.QPoint( event.line.p0.x, event.line.p0.y ) )

	def __textChanged( self ) :
				
		try :
			signal = self.__textChangedSignal
		except :
			return
						
		signal( self )		
		
	def __returnPressed( self ) :
	
		try :
			signal = self.__activatedSignal
		except :
			return
			
		signal( self )		
