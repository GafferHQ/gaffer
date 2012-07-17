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

QtGui = GafferUI._qtImport( "QtGui" )
QtCore = GafferUI._qtImport( "QtCore" )

class MultiLineTextWidget( GafferUI.Widget ) :

	WrapMode = IECore.Enum.create( "None", "Word", "Character", "WordOrCharacter" )

	def __init__( self, text="", editable=True, wrapMode=WrapMode.WordOrCharacter, **kw ) :
	
		GafferUI.Widget.__init__( self, QtGui.QPlainTextEdit(), **kw )

		self.setText( text )
		self.setEditable( editable )
		self.setWrapMode( wrapMode )
		
		self._qtWidget().setTabStopWidth( 20 ) # pixels

	def getText( self ) :
	
		return str( self._qtWidget().toPlainText() )
	
	def setText( self, text ) :
	
		return self._qtWidget().setPlainText( text )
	
	def appendText( self, text ) :
	
		self._qtWidget().appendPlainText( text )
	
	## Appends HTML-formatted text - when links within
	# this are clicked, the linkActivatedSignal will be
	# triggered.
	def appendHTML( self, html ) :
	
		self._qtWidget().appendHtml( html )
			
	def setEditable( self, editable ) :
	
		self._qtWidget().setReadOnly( not editable )
		
	def getEditable( self ) :
	
		return not self._qtWidget().isReadOnly()
	
	def setWrapMode( self, wrapMode ) :
	
		self._qtWidget().setWordWrapMode( 
			{
				self.WrapMode.None : QtGui.QTextOption.NoWrap,
				self.WrapMode.Word : QtGui.QTextOption.WordWrap,
				self.WrapMode.Character : QtGui.QTextOption.WrapAnywhere,
				self.WrapMode.WordOrCharacter : QtGui.QTextOption.WrapAtWordBoundaryOrAnywhere,
			}[wrapMode]
		)
	
	def getWrapMode( self ) :
	
		return {
			QtGui.QTextOption.NoWrap : self.WrapMode.None,
			QtGui.QTextOption.WordWrap : self.WrapMode.Word,
			QtGui.QTextOption.WrapAnywhere : self.WrapMode.Character,
			QtGui.QTextOption.WrapAtWordBoundaryOrAnywhere : self.WrapMode.WordOrCharacter,
		}[self._qtWidget().wordWrapMode()]
		
	def selectedText( self ) :
	
		cursor = self._qtWidget().textCursor()
		text = cursor.selectedText()
		text = text.replace( u"\u2029", "\n" )
		return str( text )
		
	def linkAt( self, position ) :
	
		link = self._qtWidget().anchorAt( QtCore.QPoint( position[0], position[1] ) )
		return str( link )
				
	def textChangedSignal( self ) :
	
		try :
			return self.__textChangedSignal
		except :
			self.__textChangedSignal = GafferUI.WidgetSignal()
			self._qtWidget().textChanged.connect( Gaffer.WeakMethod( self.__textChanged ) )

		return self.__textChangedSignal
	
	## A signal emitted when the widget loses focus.
	def editingFinishedSignal( self ) :
	
		try :
			return self.__editingFinishedSignal
		except :
			self.__editingFinishedSignal = GafferUI.WidgetSignal()
			self._qtWidget().installEventFilter( _focusOutEventFilter )
			
		return self.__editingFinishedSignal
	
	## A signal emitted when enter (or Ctrl-Return) is pressed.	
	def activatedSignal( self ) :
	
		try :
			return self.__activatedSignal
		except :
			self.__activatedSignal = GafferUI.WidgetSignal()
			self.__keyPressConnection = self.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ) )
						
		return self.__activatedSignal
		
	def linkActivatedSignal( self ) :
	
		try :
			return self.__linkActivatedSignal
		except :
			self.__linkActivatedSignal = GafferUI.WidgetEventSignal()
			self.__mouseMoveConnection = self.mouseMoveSignal().connect( Gaffer.WeakMethod( self.__mouseMove ) )
			self.__buttonPressConnection = self.buttonPressSignal().connect( Gaffer.WeakMethod( self.__buttonPress ) )
			
		return self.__linkActivatedSignal
		
	def __textChanged( self ) :
	
		self.__textChangedSignal( self )

	def __keyPress( self, widget, event ) :
	
		assert( widget is self )
		
		if event.key=="Enter" or ( event.key=="Return" and event.modifiers==event.Modifiers.Control ) :
			self.__activatedSignal( self )
			return True
			
		return False
		
	def __mouseMove( self, widget, event ) :
	
		link = self.linkAt( event.line.p0 )
		if link :
			self._qtWidget().viewport().setCursor( QtGui.QCursor( QtCore.Qt.PointingHandCursor ) )
		else :
			self._qtWidget().viewport().setCursor( QtGui.QCursor( QtCore.Qt.IBeamCursor ) )
			
		return False
		
	def __buttonPress( self, widget, event ) :
	
		if event.buttons & GafferUI.ButtonEvent.Buttons.Left :
			link = self.linkAt( event.line.p0 )
			if link :
				return self.__linkActivatedSignal( self, link )
		
		return False
		
class _FocusOutEventFilter( QtCore.QObject ) :

	def __init__( self ) :
	
		QtCore.QObject.__init__( self )
		
	def eventFilter( self, qObject, qEvent ) :
	
		if qEvent.type()==QtCore.QEvent.FocusOut :
			widget = GafferUI.Widget._owner( qObject )
			widget.editingFinishedSignal()( widget )
			
		return False

# this single instance is used by all MultiLineTextWidgets		
_focusOutEventFilter = _FocusOutEventFilter()