##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
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

QtCore = GafferUI._qtImport( "QtCore" )
QtGui = GafferUI._qtImport( "QtGui" )

class PopupWindow( GafferUI.Window ) :

	def __init__( self, title="GafferUI.Window", borderWidth=8, child=None, sizeMode=GafferUI.Window.SizeMode.Automatic, closeOnLeave=False, **kw ) :

		GafferUI.Window.__init__( self, title, borderWidth, child=child, sizeMode=sizeMode, **kw )

		self._qtWidget().setWindowFlags( self._qtWidget().windowFlags() | QtCore.Qt.FramelessWindowHint | QtCore.Qt.Tool )

		self._qtWidget().setAttribute( QtCore.Qt.WA_TranslucentBackground )
		self._qtWidget().setMouseTracking( True )

		self._qtWidget().paintEvent = Gaffer.WeakMethod( self.__paintEvent )
		self._qtWidget().mousePressEvent = Gaffer.WeakMethod( self.__mousePressEvent )
		self._qtWidget().mouseReleaseEvent = Gaffer.WeakMethod( self.__mouseReleaseEvent )
		self._qtWidget().mouseMoveEvent = Gaffer.WeakMethod( self.__mouseMoveEvent )
		self._qtWidget().enterEvent = Gaffer.WeakMethod( self.__enterEvent )
		self._qtWidget().leaveEvent = Gaffer.WeakMethod( self.__leaveEvent )

		# setVisible() will animate this to 1
		self._qtWidget().setWindowOpacity( 0 )
		self.__visibilityAnimation = None

		self.__dragOffset = None
		self.__cursor = None

		self.setCloseOnLeave( closeOnLeave )

	## Reimplemented from base class to make nice opacity animations
	def setVisible( self, visible ) :

		if visible == self.getVisible() :
			return

		self.__visibilityAnimation = _VisibilityAnimation( self._qtWidget(), visible )
		self.__visibilityAnimation.start()

	## Reimplemented from base class to account for nice opacity animations
	def getVisible( self ) :

		result = GafferUI.Window.getVisible( self )
		# account for the fact that we might be animating towards invisibility
		if self.__visibilityAnimation is not None and self.__visibilityAnimation.state() == self.__visibilityAnimation.Running :
			if GafferUI._Variant.fromVariant( self.__visibilityAnimation.endValue() ) == 0 :
				result = False

		return result

	def setCloseOnLeave( self, closeOnLeave ) :

		self.__closeOnLeave = closeOnLeave

	def getCloseOnLeave( self ) :

		return self.__closeOnLeave

	def __mousePressEvent( self, event ) :

		if event.button() == QtCore.Qt.LeftButton :
			if self.__cursor == QtCore.Qt.SizeFDiagCursor :
				size = self._qtWidget().size()
				self.__dragOffset = QtCore.QPoint( size.width(), size.height() ) - event.globalPos()
			else :
				self.__dragOffset = self._qtWidget().frameGeometry().topLeft() - event.globalPos()

	def __mouseReleaseEvent( self, event ) :

		if event.button() == QtCore.Qt.LeftButton :
			self.__dragOffset = None

		self.__setCursorFromPosition( event )

	def __mouseMoveEvent( self, event ) :

		if event.buttons() & QtCore.Qt.LeftButton and self.__dragOffset is not None :
			if self.__cursor == QtCore.Qt.SizeFDiagCursor :
				newSize = event.globalPos() + self.__dragOffset
				self._qtWidget().resize( newSize.x(), newSize.y() )
			else :
				self._qtWidget().move( event.globalPos() + self.__dragOffset )
		elif self.getResizeable() :
			self.__setCursorFromPosition( event )

	def __enterEvent( self, event ) :

		if self.__closeOnLeave and self.__visibilityAnimation is not None :
			if self.__visibilityAnimation.state() == self.__visibilityAnimation.Running :
				# we currently visible, but we have an animation, so we must be
				# in the process of becoming invisible. reverse that.
				self.setVisible( True )

	def __leaveEvent( self, event ) :

		self.__setCursor( None )

		if self.__closeOnLeave :
			self.setVisible( False )

	def __paintEvent( self, event ) :

		painter = QtGui.QPainter( self._qtWidget() )
		painter.setRenderHint( QtGui.QPainter.Antialiasing )

		painter.setBrush( QtGui.QColor( 76, 76, 76 ) )
		painter.setPen( QtGui.QColor( 0, 0, 0, 0 ) )

		radius = self._qtWidget().layout().contentsMargins().left()
		size = self.size()
		painter.drawRoundedRect( QtCore.QRectF( 0, 0, size.x, size.y ), radius, radius )

		if self.getResizeable() :
			painter.drawRect( size.x - radius, size.y - radius, radius, radius )

	def __setCursorFromPosition( self, event ) :

		radius = self._qtWidget().layout().contentsMargins().left()
		size = self.size()
		p = event.pos()
		if p.x() > size.x - radius and p.y() > size.y - radius :
			self.__setCursor( QtCore.Qt.SizeFDiagCursor )
		else :
			self.__setCursor( None )

	def __setCursor( self, cursor ) :

		if cursor == self.__cursor :
			return

		if self.__cursor is not None :
			QtGui.QApplication.restoreOverrideCursor()

		if cursor is not None :
			QtGui.QApplication.setOverrideCursor( QtGui.QCursor( cursor ) )

		self.__cursor = cursor

	def __closeIfLeft( self ) :

		self.close()

class _VisibilityAnimation( QtCore.QVariantAnimation ) :

	def __init__( self, window, visible ) :

		QtCore.QVariantAnimation.__init__( self )

		self.__window = window

		startValue = self.__window.windowOpacity()
		endValue = 1.0 if visible else 0.0

		self.setStartValue( startValue )
		self.setEndValue( endValue )
		self.setDuration( abs( startValue - endValue ) * 500  )

	def updateCurrentValue( self, value ) :

		value = GafferUI._Variant.fromVariant( value )
		self.__window.setWindowOpacity( value )
		if value == 0 :
			self.__window.hide()
		elif not self.__window.isVisible() :
			self.__window.show()
