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

import imath

import IECore
import IECoreGL

import Gaffer
import GafferUI

import OpenGL.GL as GL

from Qt import QtCore
from Qt import QtWidgets

## The GadgetWidget class provides a means of
# hosting a Gadget within a Widget based interface.
class GadgetWidget( GafferUI.GLWidget ) :

	## The gadget may either be a ViewportGadget in which case it will be used in a call
	# to setViewportGadget, otherwise a suitable viewport will be created and the gadget will
	# be placed within it.
	def __init__( self, gadget=None, bufferOptions=set(), **kw ) :

		GafferUI.GLWidget.__init__( self, bufferOptions, **kw )

		self._qtWidget().setFocusPolicy( QtCore.Qt.ClickFocus )

		self.__requestedDepthBuffer = self.BufferOptions.Depth in bufferOptions

		self.enterSignal().connect( Gaffer.WeakMethod( self.__enter ), scoped = False )
		self.leaveSignal().connect( Gaffer.WeakMethod( self.__leave ), scoped = False )
		self.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ), scoped = False )
		self.keyReleaseSignal().connect( Gaffer.WeakMethod( self.__keyRelease ), scoped = False )
		self.buttonPressSignal().connect( Gaffer.WeakMethod( self.__buttonPress ), scoped = False )
		self.buttonReleaseSignal().connect( Gaffer.WeakMethod( self.__buttonRelease ), scoped = False )
		self.buttonDoubleClickSignal().connect( Gaffer.WeakMethod( self.__buttonDoubleClick ), scoped = False )
		self.mouseMoveSignal().connect( Gaffer.WeakMethod( self.__mouseMove ), scoped = False )
		self.dragBeginSignal().connect( Gaffer.WeakMethod( self.__dragBegin ), scoped = False )
		self.dragEnterSignal().connect( Gaffer.WeakMethod( self.__dragEnter ), scoped = False )
		self.dragMoveSignal().connect( Gaffer.WeakMethod( self.__dragMove ), scoped = False )
		self.dragLeaveSignal().connect( Gaffer.WeakMethod( self.__dragLeave ), scoped = False )
		self.dropSignal().connect( Gaffer.WeakMethod( self.__drop ), scoped = False )
		self.dragEndSignal().connect( Gaffer.WeakMethod( self.__dragEnd ), scoped = False )

		self.wheelSignal().connect( Gaffer.WeakMethod( self.__wheel ), scoped = False )

		self.visibilityChangedSignal().connect( Gaffer.WeakMethod( self.__visibilityChanged ), scoped = False )

		self.__viewportGadget = None
		if isinstance( gadget, GafferUI.ViewportGadget ) :
			self.setViewportGadget( gadget )
		else :
			self.setViewportGadget( GafferUI.ViewportGadget( gadget ) )

		self._qtWidget().installEventFilter( _eventFilter )

	## Returns the ViewportGadget used to render this Widget. You can
	# modify this freely to change the Gadgets being rendered.
	def getViewportGadget( self ) :

		return self.__viewportGadget

	## Sets the ViewportGadget used to render this Widget.
	def setViewportGadget( self, viewportGadget ) :

		assert( isinstance( viewportGadget, GafferUI.ViewportGadget ) )

		if viewportGadget.isSame( self.__viewportGadget ) :
			return

		if self.__viewportGadget is not None :
			self.__viewportGadget.setVisible( False )

		self.__viewportGadget = viewportGadget
		self.__viewportGadget.renderRequestSignal().connect( Gaffer.WeakMethod( self.__renderRequest ), scoped = False )
		size = self.size()
		if size.x and size.y :
			self.__viewportGadget.setViewport( size )

		self.__viewportGadget.setVisible( self.visible() )

		self._redraw()

	def _resize( self, size ) :

		GafferUI.GLWidget._resize( self, size )
		if size.x and size.y :
			# avoid resizing if resolution has hit 0, as then
			# the reframing maths breaks down
			self.__viewportGadget.setViewport( size )

	def _draw( self ) :

		self.__viewportGadget.render()

	def __enter( self, widget ) :

		if not isinstance( QtWidgets.QApplication.focusWidget(), ( QtWidgets.QLineEdit, QtWidgets.QPlainTextEdit ) ) :
			self._qtWidget().setFocus()

		## \todo Widget.enterSignal() should be providing this
		# event itself.
		p = self.mousePosition( relativeTo = self )
		event = GafferUI.ButtonEvent(
			GafferUI.ButtonEvent.Buttons.None_,
			GafferUI.ButtonEvent.Buttons.None_,
			IECore.LineSegment3f(
				imath.V3f( p.x, p.y, 1 ),
				imath.V3f( p.x, p.y, 0 )
			)
		)

		if not self._makeCurrent() :
			return False

		self.__viewportGadget.enterSignal()( self.__viewportGadget, event )

	def __leave( self, widget ) :

		self._qtWidget().clearFocus()

		p = self.mousePosition( relativeTo = self )
		event = GafferUI.ButtonEvent(
			GafferUI.ButtonEvent.Buttons.None_,
			GafferUI.ButtonEvent.Buttons.None_,
			IECore.LineSegment3f(
				imath.V3f( p.x, p.y, 1 ),
				imath.V3f( p.x, p.y, 0 )
			)
		)

		if not self._makeCurrent() :
			return False

		self.__viewportGadget.leaveSignal()( self.__viewportGadget, event )

	def __renderRequest( self, gadget ) :

		self._redraw()

	def __buttonPress( self, widget, event ) :

		# we get given button presses before they're given to the overlay items,
		# so we must ignore them so they can be used by the overlay.
		if self._qtWidget().itemAt( event.line.p0.x, event.line.p0.y ) is not None :
			return False

		# but if we're outside the overlay item then we should take the
		# keyboard focus back from the overlay.
		focusItem = self._qtWidget().scene().focusItem()
		if focusItem is not None :
			self._qtWidget().scene().clearFocus()
			if focusItem.widget().focusWidget() is not None :
				focusItem.widget().focusWidget().clearFocus()

		if not self._makeCurrent() :
			return False

		return self.__viewportGadget.buttonPressSignal()( self.__viewportGadget, event )

	def __buttonRelease( self, widget, event ) :

		if not self._makeCurrent() :
			return False

		return self.__viewportGadget.buttonReleaseSignal()( self.__viewportGadget, event )

	def __buttonDoubleClick( self, widget, event ) :

		if not self._makeCurrent() :
			return False

		return self.__viewportGadget.buttonDoubleClickSignal()( self.__viewportGadget, event )

	def __mouseMove( self, widget, event ) :

		if not self._makeCurrent() :
			return False

		self.__viewportGadget.mouseMoveSignal()( self.__viewportGadget, event )

		# we always return false so that any overlay items will get appropriate
		# move/enter/leave events, otherwise highlighting for buttons etc can go
		# awry.
		return False

	def __dragBegin( self, widget, event ) :

		if not self._makeCurrent() :
			return False

		return self.__viewportGadget.dragBeginSignal()( self.__viewportGadget, event )

	def __dragEnter( self, widget, event ) :

		if not self._makeCurrent() :
			return False

		return self.__viewportGadget.dragEnterSignal()( self.__viewportGadget, event )

	def __dragMove( self, widget, event ) :

		if not self._makeCurrent() :
			return False

		return self.__viewportGadget.dragMoveSignal()( self.__viewportGadget, event )

	def __dragLeave( self, widget, event ) :

		if not self._makeCurrent() :
			return False

		return self.__viewportGadget.dragLeaveSignal()( self.__viewportGadget, event )

	def __drop( self, widget, event ) :

		if not self._makeCurrent() :
			return False

		return self.__viewportGadget.dropSignal()( self.__viewportGadget, event )

	def __dragEnd( self, widget, event ) :

		if not self._makeCurrent() :
			return False

		return self.__viewportGadget.dragEndSignal()( self.__viewportGadget, event )

	def __keyPress( self, widget, event ) :

		# we get given keypresses before the graphicsview does, so we
		# need to make sure we don't stop them going to a focussed overlay widget.
		if self._qtWidget().scene().focusItem() is not None :
			if self._qtWidget().scene().focusItem().widget().focusWidget() is not None :
				return False

		if not self._makeCurrent() :
			return False

		return self.__viewportGadget.keyPressSignal()( self.__viewportGadget, event )

	def __keyRelease( self, widget, event ) :

		if self._qtWidget().scene().focusItem() is not None :
			if self._qtWidget().scene().focusItem().widget().focusWidget() is not None :
				return False

		if not self._makeCurrent() :
			return False

		return self.__viewportGadget.keyReleaseSignal()( self.__viewportGadget, event )

	def __wheel( self, widget, event ) :

		if not self._makeCurrent() :
			return False

		# We get given wheel events before they're given to the overlay items,
		# so we must ignore them so they can be used by the overlay.
		if self._qtWidget().itemAt( event.line.p0.x, event.line.p0.y ) is not None :
			return False

		return self.__viewportGadget.wheelSignal()( self.__viewportGadget, event )

	def __visibilityChanged( self, widget ) :

		self.__viewportGadget.setVisible( self.visible() )

## Used to make the tooltips dependent on which gadget is under the mouse
class _EventFilter( QtCore.QObject ) :

	def __init__( self ) :

		QtCore.QObject.__init__( self )

	def eventFilter( self, qObject, qEvent ) :

		if qEvent.type()==QtCore.QEvent.ToolTip :

			widget = GafferUI.Widget._owner( qObject )
			assert( isinstance( widget, GadgetWidget ) )

			if not widget._makeCurrent() :
				return False

			toolTip = widget.getViewportGadget().getToolTip(
				IECore.LineSegment3f(
					imath.V3f( qEvent.x(), qEvent.y(), 1 ),
					imath.V3f( qEvent.x(), qEvent.y(), 0 )
				)
			)

			if not toolTip :
				return False

			toolTip = GafferUI.DocumentationAlgo.markdownToHTML( toolTip )
			QtWidgets.QToolTip.showText( qEvent.globalPos(), toolTip, qObject )

			return True

		return False

# this single instance is used by all widgets
_eventFilter = _EventFilter()
