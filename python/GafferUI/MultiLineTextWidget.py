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
import math

import imath

import IECore

import Gaffer
import GafferUI
from ._StyleSheet import _styleColors

from Qt import QtGui
from Qt import QtWidgets
from Qt import QtCore

class MultiLineTextWidget( GafferUI.Widget ) :

	WrapMode = enum.Enum( "WrapNode", [ "None_", "Word", "Character", "WordOrCharacter" ] )
	Role = enum.Enum( "Role", [ "Text", "Code" ] )

	def __init__( self, text="", editable=True, wrapMode=WrapMode.WordOrCharacter, fixedLineHeight=None, role=Role.Text, placeholderText = "", lineNumbersVisible = False, **kw ) :

		GafferUI.Widget.__init__( self, _PlainTextEdit( lineNumbersVisible ), **kw )

		## \todo This should come from the Style when we get Styles applied to Widgets
		# (and not just Gadgets as we have currently).
		self._qtWidget().document().setDefaultStyleSheet(
			"""
			h1 { font-weight : bold; font-size : large; }
			h1[class="ERROR"] { color : #ff5555 }
			h1[class="WARNING"] { color : #ffb655 }
			h1[class="INFO"] { color : #80b3ff }
			h1[class="DEBUG"] { color : #aaffcc }
			body { color : red }
			pre[class="message"] { color : #999999 }
			"""
		)

		self.setText( text )
		self.setEditable( editable )
		self.setWrapMode( wrapMode )
		self.setFixedLineHeight( fixedLineHeight )
		self.setRole( role )
		self.setPlaceholderText( placeholderText )

		self.dragEnterSignal().connect( Gaffer.WeakMethod( self.__dragEnter ) )
		self.dragMoveSignal().connect( Gaffer.WeakMethod( self.__dragMove ) )
		self.dragLeaveSignal().connect( Gaffer.WeakMethod( self.__dragLeave ) )
		self.dropSignal().connect( Gaffer.WeakMethod( self.__drop ) )
		self.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ) )

		self._qtWidget().setTabStopWidth( 20 ) # pixels

		self.__editingFinishedSignal = GafferUI.WidgetSignal()
		self.__activatedSignal = GafferUI.WidgetSignal()

	def getText( self ) :

		return self._qtWidget().toPlainText()

	def setText( self, text ) :

		if text == self.getText() :
			return

		return self._qtWidget().setPlainText( text )

	## Inserts at the current cursor position.
	def insertText( self, text ) :

		self._qtWidget().insertPlainText( text )

	def appendText( self, text ) :

		self._qtWidget().appendPlainText( text )

	## Appends HTML-formatted text - when links within
	# this are clicked, the linkActivatedSignal will be
	# triggered.
	def appendHTML( self, html ) :

		self._qtWidget().appendHtml( html )

	def setEditable( self, editable ) :

		self._qtWidget().setReadOnly( not editable )
		self._repolish()

	def getEditable( self ) :

		return not self._qtWidget().isReadOnly()

	def setWrapMode( self, wrapMode ) :

		self._qtWidget().setWordWrapMode(
			{
				self.WrapMode.None_ : QtGui.QTextOption.NoWrap,
				self.WrapMode.Word : QtGui.QTextOption.WordWrap,
				self.WrapMode.Character : QtGui.QTextOption.WrapAnywhere,
				self.WrapMode.WordOrCharacter : QtGui.QTextOption.WrapAtWordBoundaryOrAnywhere,
			}[wrapMode]
		)

	def getWrapMode( self ) :

		return {
			QtGui.QTextOption.NoWrap : self.WrapMode.None_,
			QtGui.QTextOption.WordWrap : self.WrapMode.Word,
			QtGui.QTextOption.WrapAnywhere : self.WrapMode.Character,
			QtGui.QTextOption.WrapAtWordBoundaryOrAnywhere : self.WrapMode.WordOrCharacter,
		}[self._qtWidget().wordWrapMode()]

	def setFixedLineHeight( self, fixedLineHeight ) :

		self._qtWidget().setFixedLineHeight( fixedLineHeight )

	def getFixedLineHeight( self ) :

		return self._qtWidget().getFixedLineHeight()

	def setErrored( self, errored ) :

		if errored == self.getErrored() :
			return

		self._qtWidget().setProperty( "gafferError", GafferUI._Variant.toVariant( bool( errored ) ) )
		self._repolish()

	def getErrored( self ) :

		return GafferUI._Variant.fromVariant( self._qtWidget().property( "gafferError" ) ) or False

	def setCursorPosition( self, position ) :

		cursor = self._qtWidget().textCursor()
		cursor.setPosition( position )
		self._qtWidget().setTextCursor( cursor )

	def getCursorPosition( self ) :

		return self._qtWidget().textCursor().position()

	def cursorPositionAt( self, position ) :

		return self._qtWidget().cursorForPosition(
			QtCore.QPoint( position[0], position[1] )
		).position()

	def cursorBound( self, relativeTo = None ) :

		b = self._qtWidget().cursorRect()
		b = imath.Box2i(
			imath.V2i( b.left(), b.top() ),
			imath.V2i( b.right(), b.bottom() )
		)

		if relativeTo is not self :
			p = self.bound( relativeTo ).min()
			b.setMin( b.min() + p )
			b.setMax( b.max() + p )

		return b

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

		cursor = self._qtWidget().textCursor()
		cursor.setPosition( start ) # Moves anchor too
		cursor.setPosition( end, cursor.KeepAnchor )
		self._qtWidget().setTextCursor( cursor )

	## Returns a `( start, end )` tuple.
	def getSelection( self ) :

		cursor = self._qtWidget().textCursor()
		if not cursor.hasSelection() :
			return 0, 0

		position = cursor.position()
		anchor = cursor.anchor()
		return ( min( anchor, position ), max( anchor, position ) )

	def selectedText( self ) :

		cursor = self._qtWidget().textCursor()
		return cursor.selection().toPlainText()

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

	## \todo Should this be at the Widget level?
	# QWidgets aren't focussable by default so it's
	# up for debate. setFocussed( True ) could make
	# them focussable, but then the question is should
	# setFocussed( False ) make them unfocussable again?
	# Or maybe the first connection to keyPressSignal() should
	# make them focussable?
	## \todo If we don't move this to Widget, then
	# at least make TextWidget match this interface (it
	# currently has grabFocus())
	def setFocussed( self, focussed ) :

		if focussed == self.getFocussed() :
			return

		if focussed :
			self._qtWidget().setFocus()
		else :
			self._qtWidget().clearFocus()

	def getFocussed( self ) :

		return self._qtWidget().hasFocus()

	def setRole( self, role ) :

		if role == self.getRole() :
			return

		self._qtWidget().setProperty( "gafferRole", GafferUI._Variant.toVariant( role.name ) )
		self._repolish()

	def getRole( self ) :

		role = GafferUI._Variant.fromVariant( self._qtWidget().property( "gafferRole" ) )
		if role is None :
			return self.Role.Text

		return getattr( self.Role, role )

	## Sets what text is displayed when the main text is empty.
	def setPlaceholderText( self, text ) :

		self._qtWidget().setPlaceholderText( text )

	def getPlaceholderText( self ) :

		return self._qtWidget().placeholderText()

	## A signal emitted whenever the user has finished editing the text either
	# by activating it via `Enter` or `Ctrl + Return`, or by moving focus to
	# another Widget.
	def editingFinishedSignal( self ) :

		return self.__editingFinishedSignal

	## A signal emitted when `Enter` or `Ctrl + Return` is pressed.
	def activatedSignal( self ) :

		return self.__activatedSignal

	def linkActivatedSignal( self ) :

		try :
			return self.__linkActivatedSignal
		except :
			self.__linkActivatedSignal = GafferUI.WidgetEventSignal()
			self.mouseMoveSignal().connect( Gaffer.WeakMethod( self.__mouseMove ) )
			self.buttonPressSignal().connect( Gaffer.WeakMethod( self.__buttonPress ) )

		return self.__linkActivatedSignal

	## A signal emitted when the widget wants to generate some text
	# to be inserted from a drag/drop operation. Signature is
	# ( widget, dragData ). By default, only StringData is accepted,
	# but by connecting to this signal and returning an appropriate
	# string value based on dragData, any other type can be
	# accommodated.
	def dropTextSignal( self ) :

		try :
			return self.__dropTextSignal
		except :
			self.__dropTextSignal = Gaffer.Signals.Signal2()

		return self.__dropTextSignal

	def setLineNumbersVisible( self, visible ) :

		self._qtWidget().setLineNumbersVisible( visible )

	def getLineNumbersVisible( self ) :

		return self._qtWidget().getLineNumbersVisible()

	def _emitEditingFinished( self ) :

		self.editingFinishedSignal()( self )
		# Hide our activation hint
		self._qtWidget().document().setModified( False )

	def __textChanged( self ) :

		self.__textChangedSignal( self )

	def __keyPress( self, widget, event ) :

		assert( widget is self )

		if event.key=="Enter" or ( event.key=="Return" and event.modifiers==event.Modifiers.Control ) :
			self.__activatedSignal( self )
			self._emitEditingFinished()
			return True
		elif event.key == "Return" and event.modifiers == event.Modifiers.Shift :
			self._qtWidget().textCursor().insertBlock()
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

	def __dropText( self, dragData ) :

		signal = None
		with IECore.IgnoredExceptions( AttributeError ) :
			signal = self.__dropTextSignal

		text = None
		if signal is not None :
			text = signal( self, dragData )

		if text is None and isinstance( dragData, IECore.StringData ) :
			text = dragData.value

		return text

	def __dragEnter( self, widget, event ) :

		if not self.getEditable() :
			return False

		if self.__dropText( event.data ) is not None :
			self.setFocussed( True )
			return True

		return False

	def __dragMove( self, widget, event ) :

		cursorPosition = self.cursorPositionAt( event.line.p0 )
		self.setCursorPosition( cursorPosition )

		return True

	def __dragLeave( self, widget, event ) :

		self.setFocussed( False )

	def __drop( self, widget, event ) :

		self.insertText( self.__dropText( event.data ) )
		return True

class _QLineNumberArea( QtWidgets.QWidget ) :

	def __init__( self, codeEditor ) :

		assert( isinstance( codeEditor, _PlainTextEdit ) )
		QtWidgets.QWidget.__init__( self, codeEditor )

	def sizeHint( self ) :

		return QtCore.QSize( self.parentWidget().lineNumberAreaWidth(), 0 )

	def paintEvent( self, event ) :

		self.parentWidget().lineNumberAreaPaintEvent( event )

class _PlainTextEdit( QtWidgets.QPlainTextEdit ) :

	def __init__( self, lineNumbersVisible, parent = None ) :

		QtWidgets.QPlainTextEdit.__init__( self, parent )

		self.__lineNumberAreaWidget = _QLineNumberArea( self )
		self.setLineNumbersVisible( lineNumbersVisible )

		self.__fixedLineHeight = None

		self.blockCountChanged.connect( self.__updateLineNumberAreaWidth )
		self.updateRequest.connect( self.__updateLineNumberArea )
		self.document().modificationChanged.connect( self.update )

	def setFixedLineHeight( self, fixedLineHeight ) :

		self.__fixedLineHeight = fixedLineHeight

		self.setSizePolicy(
			self.sizePolicy().horizontalPolicy(),
			QtWidgets.QSizePolicy.Expanding if self.__fixedLineHeight is None else QtWidgets.QSizePolicy.Fixed
		)

		self.updateGeometry()

	def getFixedLineHeight( self ) :

		return self.__fixedLineHeight

	def setLineNumbersVisible( self, visible ) :

		self.__lineNumbersVisible = visible
		self.__lineNumberAreaWidget.setVisible( visible )
		self.__updateLineNumberAreaWidth( 0 )

	def getLineNumbersVisible( self ) :

		return self.__lineNumbersVisible

	def lineNumberAreaWidth( self ) :

		if not self.getLineNumbersVisible() :
			return 0

		digits = 1 + math.floor( math.log10( self.blockCount() ) )

		return 3 + self.fontMetrics().horizontalAdvance( '9' ) * digits

	def lineNumberAreaPaintEvent( self, event ) :

		block = self.firstVisibleBlock()

		top = round( self.blockBoundingGeometry( block ).translated( self.contentOffset() ).top() )
		bottom = top + round( self.blockBoundingRect( block ).height() )

		width = self.lineNumberAreaWidth()

		painter = QtGui.QPainter( self.__lineNumberAreaWidget )
		painter.setFont( self.property( "font" ) )

		nonCursorLineColor = QtGui.QColor( *( _styleColors["backgroundLight"] ) )
		cursorLineColor = QtGui.QColor( *( _styleColors["foregroundFaded"] ) )

		while block.isValid() and top <= event.rect().bottom() :
			if block.isVisible() :
				painter.setPen( cursorLineColor if block == self.textCursor().block() else nonCursorLineColor )

				painter.drawText(
					0,
					top,
					width,
					self.fontMetrics().height(),
					QtCore.Qt.AlignRight,
					str( block.blockNumber() + 1 )
				)
			block = block.next()
			top = bottom
			bottom = top + round( self.blockBoundingRect( block ).height() )

	def __computeHeight( self, size ) :

		fixedLineHeight = self.getFixedLineHeight()

		# when the multiline is displaying fixed lines
		if fixedLineHeight is not None :

			# computing the font metrics based on the number of lines
			height = self.fontMetrics().boundingRect( "M" ).height() * fixedLineHeight

			# also, we need to compute the widget margins to frame the fixed lines nicely
			margin = self.contentsMargins().top() + self.contentsMargins().bottom() + self.document().documentMargin()

			height += margin

			size.setHeight(height)

		return size

	def sizeHint( self ) :

		size = QtWidgets.QPlainTextEdit.sizeHint( self )

		return self.__computeHeight( size )

	def minimumSizeHint( self ) :

		size = QtWidgets.QPlainTextEdit.minimumSizeHint( self )

		return self.__computeHeight( size )

	def event( self, event ) :

		if event.type() == QtCore.QEvent.ShortcutOverride and event == QtGui.QKeySequence.Copy :
			# QPlainTextEdit doesn't accept this when it's
			# read only. so we accept it ourselves, which is
			# enough to reenable copying from a read only
			# widget with Ctrl+C.
			event.accept()
			return True

		return QtWidgets.QPlainTextEdit.event( self, event )

	def resizeEvent ( self, event ) :

		QtWidgets.QPlainTextEdit.resizeEvent( self, event )

		contentsRect = self.contentsRect()
		self.__lineNumberAreaWidget.setGeometry(
			QtCore.QRect(
				contentsRect.left(),
				contentsRect.top(),
				self.lineNumberAreaWidth(),
				contentsRect.height()
			)
		)

	def focusOutEvent( self, event ) :

		widget = GafferUI.Widget._owner( self )
		if widget is not None :
			widget._emitEditingFinished()

		QtWidgets.QPlainTextEdit.focusOutEvent( self, event )

	def paintEvent( self, event ) :

		QtWidgets.QPlainTextEdit.paintEvent( self, event )

		painter = QtGui.QPainter( self.viewport() )

		if self.isEnabled() :
			self.__paintActivationHint( painter )
			return

		# Disabled. We want the text to use faded colours but we can't
		# do that with a stylesheet because we may have embedded HTML
		# colours and/or a highlighter. So instead we draw a semi-transparent
		# overlay the same colour as our background.

		color = self.palette().base().color()
		color.setAlpha( 128 )
		painter.fillRect( 0, 0, self.width(), self.height(), color )

	def __paintActivationHint( self, painter ) :

		if self.isReadOnly() or not self.document().isModified() :
			return

		widget = GafferUI.Widget._owner( self )
		if widget is None or ( widget.activatedSignal().empty() and widget.editingFinishedSignal().empty() ) :
			return

		viewport = self.viewport()
		pixmap = GafferUI.Image._qtPixmapFromFile( "ctrlEnter.png" )
		painter.setOpacity( 0.75 )
		painter.drawPixmap( viewport.width() - ( pixmap.width() + 4 ), viewport.height() - ( pixmap.height() + 4 ), pixmap )

	def __updateLineNumberAreaWidth( self, newBlockCount ) :

		lineNumberAreaWidth = self.lineNumberAreaWidth()
		self.setViewportMargins( lineNumberAreaWidth + ( 8 if lineNumberAreaWidth > 0 else 0 ), 0, 0, 0 )

	def __updateLineNumberArea( self, rect, scrollY ) :

		if scrollY != 0 :
			self.__lineNumberAreaWidget.scroll( 0, scrollY )
		else :
			self.__lineNumberAreaWidget.update( 0, rect.y(), self.__lineNumberAreaWidget.width(), rect.height() )

		if rect.contains( self.viewport().rect() ) :
			self.__updateLineNumberAreaWidth( 0 )