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

import enum
import warnings

import Gaffer
import GafferUI

from Qt import QtCore
from Qt import QtGui
from Qt import QtWidgets

class TextWidget( GafferUI.Widget ) :

	DisplayMode = enum.Enum( "DisplayMode", [ "Normal", "Password" ] )

	def __init__( self, text="", editable=True, displayMode=DisplayMode.Normal, characterWidth=None, placeholderText="", **kw ) :

		GafferUI.Widget.__init__( self, _LineEdit(), **kw )

		self.setText( text )
		self.setEditable( editable )
		self.setDisplayMode( displayMode )
		self.setFixedCharacterWidth( characterWidth )
		self.setPlaceholderText( placeholderText )

	def setText( self, text ) :

		self._qtWidget().setText( text )

	def getText( self ) :

		return self._qtWidget().text()

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
				self.DisplayMode.Normal : QtWidgets.QLineEdit.Normal,
				self.DisplayMode.Password : QtWidgets.QLineEdit.Password,
			}[displayMode]
		)

	def getDisplayMode( self ) :

		return {
			QtWidgets.QLineEdit.Normal : self.DisplayMode.Normal,
			QtWidgets.QLineEdit.Password : self.DisplayMode.Password,
		}[self._qtWidget().echoMode()]

	def setErrored( self, errored ) :

		if errored == self.getErrored() :
			return

		self._qtWidget().setProperty( "gafferError", GafferUI._Variant.toVariant( bool( errored ) ) )
		self._repolish()

	def getErrored( self ) :

		return GafferUI._Variant.fromVariant( self._qtWidget().property( "gafferError" ) ) or False

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

	def selectedText( self ) :

		return self._qtWidget().selectedText()

	## Sets the preferred width for the widget in terms of the
	# number of characters which can be displayed. The widget can still
	# contract and expand, but will request to be this width if possible.
	# Use setFixedCharacterWidth() to request an unchanging width.
	def setPreferredCharacterWidth( self, numCharacters ) :

		self._qtWidget().setPreferredCharacterWidth( numCharacters )

	## Returns the preferred width in characters.
	def getPreferredCharacterWidth( self ) :

		return self._qtWidget().getPreferredCharacterWidth()

	## Sets the width for the widget to a constant size measured
	# in characters, overriding the preferred width. Pass
	# numCharacters=None to remove the fixed width and make the
	# widget resizeable again.
	def setFixedCharacterWidth( self, numCharacters ) :

		self._qtWidget().setFixedCharacterWidth( numCharacters )

	## Returns the current fixed width, or None if the preferred
	# width is in effect.
	def getFixedCharacterWidth ( self ) :

		return self._qtWidget().getFixedCharacterWidth()

	## Sets what text is displayed when the main text is empty.
	def setPlaceholderText( self, text ) :

		self._qtWidget().setPlaceholderText( text )

	def getPlaceholderText( self ) :

		return self._qtWidget().placeholderText()

	## \deprecated Use setFixedCharacterWidth() instead.
	def setCharacterWidth( self, numCharacters ) :

		warnings.warn( "TextWidget.setCharacterWidth() is deprecated, use TextWidget.setFixedCharacterWidth() instead.", DeprecationWarning, 2 )
		self.setFixedCharacterWidth( numCharacters )

	## \deprecated Use getFixedCharacterWidth() instead.
	def getCharacterWidth( self ) :

		warnings.warn( "TextWidget.getCharacterWidth() is deprecated, use TextWidget.getFixedCharacterWidth() instead.", DeprecationWarning, 2 )
		return self.getFixedCharacterWidth()

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
			self._qtWidget().editingFinished.connect( Gaffer.WeakMethod( self.__editingFinished, fallbackResult = None ) )

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
			self.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ), scoped = False )
			self.keyReleaseSignal().connect( Gaffer.WeakMethod( self.__keyRelease ), scoped = False )
			self.buttonPressSignal().connect( Gaffer.WeakMethod( self.__buttonPress ), scoped = False )
			self.buttonReleaseSignal().connect( Gaffer.WeakMethod( self.__buttonRelease ), scoped = False )
			self.__lastSelection = self.getSelection()
			self.__numSelectionPossiblyFinishedEvents = 0

		return self.__selectingFinishedSignal

	## Returns the character index underneath the specified
	# ButtonEvent.
	def _eventPosition( self, event ) :

		return self._qtWidget().cursorPositionAt( QtCore.QPoint( event.line.p0.x, event.line.p0.y ) )

	def __textChanged( self, text ) :

		self.__textChangedSignal( self )

	def __returnPressed( self ) :

		self.__activatedSignal( self )

	def __editingFinished( self ) :

		self.__editingFinishedSignal( self )

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
		QtCore.QTimer.singleShot( QtWidgets.QApplication.doubleClickInterval(), self.__selectionPossiblyFinished )

	def __selectionPossiblyFinished( self ) :

		assert( self.__numSelectionPossiblyFinishedEvents > 0 )

		self.__numSelectionPossiblyFinishedEvents -= 1
		if self.__numSelectionPossiblyFinishedEvents == 0 :
			selection = self.getSelection()
			if selection != ( 0, 0 ) and selection != self.__lastSelection :
				self.__selectingFinishedSignal( self )
			self.__lastSelection = selection

# Private implementation - QLineEdit with a sizeHint that implements the
# fixed/preferred widths measured in characters. It is necessary to implement
# these using sizeHint() so that they can adjust automatically to changes in
# the style.
class _LineEdit( QtWidgets.QLineEdit ) :

	def __init__( self, parent = None ) :

		QtWidgets.QLineEdit.__init__( self )

		self.__preferredCharacterWidth = 20
		self.__fixedCharacterWidth = None

	def setPreferredCharacterWidth( self, numCharacters ) :

		if self.__preferredCharacterWidth == numCharacters :
			return

		self.__preferredCharacterWidth = numCharacters
		if self.__fixedCharacterWidth is None :
			self.updateGeometry()

	def getPreferredCharacterWidth( self ) :

		return self.__preferredCharacterWidth

	def setFixedCharacterWidth( self, numCharacters ) :

		if self.__fixedCharacterWidth == numCharacters :
			return

		self.__fixedCharacterWidth = numCharacters
		self.setSizePolicy(
			QtWidgets.QSizePolicy.Expanding if self.__fixedCharacterWidth is None else QtWidgets.QSizePolicy.Fixed,
			QtWidgets.QSizePolicy.Fixed
		)

		# we need to make sure that the geometry is up-to-date with the current character width
		if self.__fixedCharacterWidth is not None:
			self.updateGeometry()

	def getFixedCharacterWidth( self ) :

		return self.__fixedCharacterWidth

	def sizeHint( self ) :

		# call the base class to get the height
		result = QtWidgets.QLineEdit.sizeHint( self )

		# but then calculate our own width
		numChars = self.__fixedCharacterWidth if self.__fixedCharacterWidth is not None else self.__preferredCharacterWidth
		textMargins = self.getTextMargins()
		contentsMargins = self.getContentsMargins()

		width = self.fontMetrics().boundingRect( "M" * numChars ).width()
		width += contentsMargins[0] + contentsMargins[2] + textMargins[0] + textMargins[2]

		options = QtWidgets.QStyleOptionFrame()
		self.initStyleOption( options )
		size = self.style().sizeFromContents(
			QtWidgets.QStyle.CT_LineEdit,
			options,
			QtCore.QSize( width, 20 ),
			self
		)

		result.setWidth( width )
		return result

	def event(self, event):

		if event.type() == event.ShortcutOverride :
			if event == QtGui.QKeySequence.Undo :
				if not self.isModified() or not self.isUndoAvailable() :
					return False
			elif event == QtGui.QKeySequence.Redo :
				if not self.isModified() or not self.isRedoAvailable() :
					return False

		return QtWidgets.QLineEdit.event( self, event )
