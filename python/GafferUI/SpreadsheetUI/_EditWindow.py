##########################################################################
#
#  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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

from Qt import QtCore
from Qt import QtGui

from ._CellPlugValueWidget import _CellPlugValueWidget

class _EditWindow( GafferUI.Window ) :

	# Considered private - use `_EditWindow.popupEditor()` instead.
	def __init__( self, plugValueWidget, **kw ) :

		GafferUI.Window.__init__( self, "", child = plugValueWidget, borderWidth = 8, sizeMode=GafferUI.Window.SizeMode.Automatic, **kw )

		self._qtWidget().setWindowFlags( QtCore.Qt.Popup )

		self._qtWidget().setAttribute( QtCore.Qt.WA_TranslucentBackground )
		self._qtWidget().paintEvent = Gaffer.WeakMethod( self.__paintEvent )

		self.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ), scoped = False )

	@classmethod
	def popupEditor( cls, plug, plugBound ) :

		plugValueWidget = GafferUI.PlugValueWidget.create( plug )
		cls.__currentWindow = _EditWindow( plugValueWidget )

		if isinstance( plugValueWidget, _CellPlugValueWidget ) :
			valuePlugValueWidget = plugValueWidget.childPlugValueWidget( plug["value"] )
			if isinstance( valuePlugValueWidget, GafferUI.PresetsPlugValueWidget ) :
				if not Gaffer.Metadata.value( valuePlugValueWidget.getPlug(), "presetsPlugValueWidget:isCustom" ) :
					valuePlugValueWidget.menu().popup()
					return

		cls.__currentWindow.resizeToFitChild()
		windowSize = cls.__currentWindow.bound().size()
		cls.__currentWindow.setPosition( plugBound.center() - windowSize / 2 )
		cls.__currentWindow.setVisible( True )

		textWidget = cls.__textWidget( plugValueWidget )
		if textWidget is not None :
			if isinstance( textWidget, GafferUI.TextWidget ) :
				textWidget.grabFocus()
				textWidget.setSelection( 0, len( textWidget.getText() ) )
			else :
				textWidget.setFocussed( True )
			textWidget._qtWidget().activateWindow()

	def __paintEvent( self, event ) :

		painter = QtGui.QPainter( self._qtWidget() )
		painter.setRenderHint( QtGui.QPainter.Antialiasing )

		painter.setBrush( QtGui.QColor( 35, 35, 35 ) )
		painter.setPen( QtGui.QColor( 0, 0, 0, 0 ) )

		radius = self._qtWidget().layout().contentsMargins().left()
		size = self.size()
		painter.drawRoundedRect( QtCore.QRectF( 0, 0, size.x, size.y ), radius, radius )

	def __keyPress( self, widget, event ) :

		if event.key == "Return" :
			self.close()

	@classmethod
	def __textWidget( cls, plugValueWidget ) :

		def widgetUsable( w ) :
			return w.visible() and w.enabled() and w.getEditable()

		widget = None

		if isinstance( plugValueWidget, GafferUI.StringPlugValueWidget ) :
			widget = plugValueWidget.textWidget()
		elif isinstance( plugValueWidget, GafferUI.NumericPlugValueWidget ) :
			widget = plugValueWidget.numericWidget()
		elif isinstance( plugValueWidget, GafferUI.PathPlugValueWidget ) :
			widget = plugValueWidget.pathWidget()
		elif isinstance( plugValueWidget, GafferUI.MultiLineStringPlugValueWidget ) :
			widget = plugValueWidget.textWidget()

		if widget is not None and widgetUsable( widget ) :
			return widget

		for childPlug in Gaffer.Plug.Range( plugValueWidget.getPlug() ) :
			childWidget = plugValueWidget.childPlugValueWidget( childPlug )
			if childWidget is not None :
				childTextWidget = cls.__textWidget( childWidget )
				if childTextWidget is not None :
					return childTextWidget

		return None
