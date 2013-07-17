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

import weakref

import IECore

import Gaffer
import GafferUI

QtCore = GafferUI._qtImport( "QtCore" )
QtGui = GafferUI._qtImport( "QtGui" )

class TextWidget( GafferUI.Widget ) :

	DisplayMode = IECore.Enum.create( "Normal", "Password" )

	def __init__( self, text="", editable=True, displayMode=DisplayMode.Normal, characterWidth=None, **kw ) :
	
		GafferUI.Widget.__init__( self, _LineEdit(), **kw )

		self.setText( text )
		self.setEditable( editable )
		self.setDisplayMode( displayMode )
		self.setCharacterWidth( characterWidth )
		
	def setText( self, text ) :
	
		self._qtWidget().setText( text )
		
	def getText( self ) :
	
		return str( self._qtWidget().text() )

	def setEditable( self, editable ) :
	
		if editable == self.getEditable() :
			return
			
		self._qtWidget().setReadOnly( not editable )
		self._repolish()
		
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
	
	## Start and end are indexes into the text, and support the same
	# indexing as a standard python string (negative indices index relative
	# to the end etc).
	def setSelection( self, start, end ) :
	
		if start is None :
			start = 0
		elif start < 0 :
			start += len( self.getText() )
			
		if end is None :
			end = len( self.getText() )	
		elif end < 0 :
			end += len( self.getText() )
			
		self._qtWidget().setSelection( start, end - start )
	
	## Returns a ( start, end ) tuple.
	def getSelection( self ) :
	
		if not self._qtWidget().hasSelectedText() :
			return 0, 0
	
		selectionStart = self._qtWidget().selectionStart()
		return ( selectionStart, selectionStart + len( self._qtWidget().selectedText() ) )
	
	def setCharacterWidth( self, numCharacters ) :
	
		self._qtWidget().setCharacterWidth( numCharacters )
					
	def getCharacterWidth ( self ) :
	
		return self._qtWidget().getCharacterWidth()
	
	## Clears the undo stack local to this widget - when
	# the stack is empty the widget will ignore any
	# undo/redo shortcuts, allowing any equivalent shortcuts
	# elsewhere to be triggered.
	def clearUndo( self ) :
	
		self._qtWidget().setModified( False )
		
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
			self._qtWidget().textChanged.connect( Gaffer.WeakMethod( self.__textChanged ) )
			
		return self.__textChangedSignal

	## A signal emitted whenever the user has edited the text and
	# completed that process either by hitting enter, or by moving
	# focus to another Widget.
	def editingFinishedSignal( self ) :
	
		try :
			return self.__editingFinishedSignal
		except :
			self.__editingFinishedSignal = GafferUI.WidgetSignal()
			self._qtWidget().editingFinished.connect( IECore.curry( TextWidget.__editingFinished, weakref.ref( self._qtWidget() ) ) )
			
		return self.__editingFinishedSignal

	## A signal emitted when enter is pressed.
	def activatedSignal( self ) :
	
		try :
			return self.__activatedSignal
		except :
			self.__activatedSignal = GafferUI.WidgetSignal()
			self._qtWidget().returnPressed.connect( Gaffer.WeakMethod( self.__returnPressed ) )
			
		return self.__activatedSignal

	## A signal emitted whenever the selection changes.
	def selectionChangedSignal( self ) :
	
		try :
			return self.__selectionChangedSignal
		except :	
			self.__selectionChangedSignal = GafferUI.WidgetSignal()
			self._qtWidget().selectionChanged.connect( Gaffer.WeakMethod( self.__selectionChanged ) )
		
		return self.__selectionChangedSignal
	
	## A signal emitted when the user has finished selecting some text, but hasn't
	# immediately started editing it.
	def selectingFinishedSignal( self ) :
	
		try :
			return self.__selectingFinishedSignal
		except :
			self.__selectingFinishedSignal = GafferUI.WidgetSignal()
			self.__keyPressConnection = self.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ) )
			self.__keyReleaseConnection = self.keyReleaseSignal().connect( Gaffer.WeakMethod( self.__keyRelease ) )
			self.__buttonPressConnection = self.buttonPressSignal().connect( Gaffer.WeakMethod( self.__buttonPress ) )
			self.__buttonReleaseConnection = self.buttonReleaseSignal().connect( Gaffer.WeakMethod( self.__buttonRelease ) )
			self.__lastSelection = self.getSelection()
			self.__numSelectionPossiblyFinishedEvents = 0
			
		return self.__selectingFinishedSignal
	
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
			
		self.__activatedSignal( self )
	
	@staticmethod
	def __editingFinished( qtWidgetWeakRef ) :
		
		# We're handling editingFinished slightly differently than the other
		# qt signals we use to emit our own signals. Instead of connecting the qt
		# editingFinished signal to a method of the TextWidget via WeakMethod,
		# we're connecting to a staticmethod instead, and passing a weak reference to
		# the QWidget, and using that to recover the owning Widget. When closing Gaffer,
		# it seems that sometimes Qt will send editingFinished for a QWidget that no
		# longer has a Widget owner, in which case the WeakMethod approach would raise.
		# Possibly this approach may be needed in other cases, but we're just using it
		# in this one case for now, as that's the only one to rear its ugly head so far.
		
		qtWidget = qtWidgetWeakRef()
		widget = GafferUI.Widget._owner( qtWidget )
		if widget is not None :	
			widget.__editingFinishedSignal( widget )		

	def __selectionChanged( self ) :
	
		self.__selectionChangedSignal( self )
		
	def __keyPress( self, widget, event ) :
	
		assert( widget is self )
		
		if event.key == "Shift" :
			self.__lastSelection = self.getSelection()
		
	def __keyRelease( self, widget, event ) :
	
		assert( widget is self )
		
		if event.key == "Shift" and self.getSelection() != ( 0, 0 ) :
			self.__startSelectionFinishedTimer()
			
		return False
	
	def __buttonPress( self, widget, event ) :
	
		assert( widget is self )
		self.__lastSelection = self.getSelection()
		return False
	
	def __buttonRelease( self, widget, event ) :
	
		assert( widget is self )
		self.__startSelectionFinishedTimer()
		return False
	
	def __startSelectionFinishedTimer( self ) :
			
		self.__numSelectionPossiblyFinishedEvents += 1
		QtCore.QTimer.singleShot( QtGui.QApplication.doubleClickInterval(), self.__selectionPossiblyFinished )
	
	def __selectionPossiblyFinished( self ) :
	
		assert( self.__numSelectionPossiblyFinishedEvents > 0 )
		
		self.__numSelectionPossiblyFinishedEvents -= 1
		if self.__numSelectionPossiblyFinishedEvents == 0 :
			selection = self.getSelection() 
			if selection != ( 0, 0 ) and selection != self.__lastSelection :
				self.__selectingFinishedSignal( self )
			self.__lastSelection = selection

# Private implementation - QLineEdit with a sizeHint that implements the
# fixed character width. Initially tried to simply call setFixedWidth() on
# a standard QLineEdit, but when the style changes the calculated width is
# no longer correct - doing it in the sizeHint allows it to respond to
# style changes.			
class _LineEdit( QtGui.QLineEdit ) :

	def __init__( self, parent = None ) :
	
		QtGui.QLineEdit.__init__( self )
	
		self.__characterWidth = None
	
	def setCharacterWidth( self, numCharacters ) :
	
		if self.__characterWidth == numCharacters :
			return
			
		self.__characterWidth = numCharacters
		self.setSizePolicy(
			QtGui.QSizePolicy.Expanding if self.__characterWidth is None else QtGui.QSizePolicy.Fixed,
			QtGui.QSizePolicy.Fixed
		)
	
	def getCharacterWidth( self ) :
	
		return self.__characterWidth
	
	def sizeHint( self ) :
	
		result = QtGui.QLineEdit.sizeHint( self )
			
		if self.__characterWidth is not None :
			
			width = self.fontMetrics().boundingRect( "M" * self.__characterWidth ).width()
			margins = self.getTextMargins()
			width += margins[0] + margins[2]
	
			options = QtGui.QStyleOptionFrameV2()
			self.initStyleOption( options )
			size = self.style().sizeFromContents(
				QtGui.QStyle.CT_LineEdit,
				options,
				QtCore.QSize( width, 20, ),
				self
			)

			## \todo The + 6 shouldn't be necessary at all, but otherwise the code
			# above seems to be consistently a bit too small. Not sure if the problem
			# is here or in qt.
			result.setWidth( width + 6 )
			
		return result
		
	def event(self, event):
       
		if event.type() == event.ShortcutOverride :
			if event == QtGui.QKeySequence.Undo :
				if not self.isModified() or not self.isUndoAvailable() :
					return False
			elif event == QtGui.QKeySequence.Redo :
				if not self.isModified() or not self.isRedoAvailable() :
					return False
           
		return QtGui.QLineEdit.event( self, event )
