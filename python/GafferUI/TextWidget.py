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

import IECore

import Gaffer
import GafferUI

QtCore = GafferUI._qtImport( "QtCore" )
QtGui = GafferUI._qtImport( "QtGui" )

class TextWidget( GafferUI.Widget ) :

	DisplayMode = IECore.Enum.create( "Normal", "Password" )

	def __init__( self, text="", editable=True, displayMode=DisplayMode.Normal, **kw ) :
	
		GafferUI.Widget.__init__( self, QtGui.QLineEdit(), **kw )

		self._qtWidget().textChanged.connect( Gaffer.WeakMethod( self.__textChanged ) )
		self._qtWidget().returnPressed.connect( Gaffer.WeakMethod( self.__returnPressed ) )
		self._qtWidget().editingFinished.connect( Gaffer.WeakMethod( self.__editingFinished ) )

		self.setText( text )
		self.setEditable( editable )
		self.setDisplayMode( displayMode )
		
	def setText( self, text ) :
	
		self._qtWidget().setText( text )
		
	def getText( self ) :
	
		return str( self._qtWidget().text() )

	def setEditable( self, editable ) :
	
		self._qtWidget().setReadOnly( not editable )

	def getEditable( self ) :
		
		return not self._qtWidget().isReadOnly()
		
	def setDisplayMode( self, displayMode ) :
	
		self._qtWidget().setEchoMode(
			{
				self.DisplayMode.Normal : QtGui.QLineEdit.Normal,
				self.DisplayMode.Password : QtGui.QLineEdit.Password,
			}[displayMode]
		)
		
	def getDisplayMode( self ) :
	
		return {
			QtGui.QLineEdit.Normal : self.DisplayMode.Normal,
			QtGui.QLineEdit.Password : self.DisplayMode.Password,
		}[self._qtWidget().echoMode()]
	
	def setCursorPosition( self, position ) :
	
		self._qtWidget().setCursorPosition( position )
		
	def getCursorPosition( self ) :
	
		return self._qtWidget().cursorPosition()
	
	## \todo Should this be moved to the Widget class?
	def grabFocus( self ) :
	
		self._qtWidget().setFocus( QtCore.Qt.OtherFocusReason )

	## A signal emitted whenever the text changes. If the user is typing
	# then a signal will be emitted for every character entered.
	def textChangedSignal( self ) :
	
		try :
			return self.__textChangedSignal
		except :
			self.__textChangedSignal = GafferUI.WidgetSignal()
			
		return self.__textChangedSignal

	## A signal emitted whenever the user has edited the text and
	# completed that process either by hitting enter, or by moving
	# focus to another Widget.
	def editingFinishedSignal( self ) :
	
		try :
			return self.__editingFinishedSignal
		except :
			self.__editingFinishedSignal = GafferUI.WidgetSignal()
			
		return self.__editingFinishedSignal

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

	def __textChanged( self, text ) :
						
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
	
	def __editingFinished( self ) :
	
		try :
			signal = self.__editingFinishedSignal
		except :
			return
			
		signal( self )		
