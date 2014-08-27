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

from __future__ import with_statement

import IECore

import Gaffer
import GafferUI
from GLWidget import GLWidget
from _GafferUI import ButtonEvent, ModifiableEvent, ContainerGadget, DragDropEvent, KeyEvent

# import lazily to improve startup of apps which don't use GL functionality
GL = Gaffer.lazyImport( "OpenGL.GL" )
IECoreGL = Gaffer.lazyImport( "IECoreGL" )

QtCore = GafferUI._qtImport( "QtCore" )
QtGui = GafferUI._qtImport( "QtGui" )

## The GadgetWidget class provides a means of
# hosting a Gadget within a Widget based interface.
class GadgetWidget( GafferUI.GLWidget ) :

	## The gadget may either be a ViewportGadget in which case it will be used in a call
	# to setViewportGadget, otherwise a suitable viewport will be created and the gadget will
	# be placed within it.
	def __init__( self, gadget=None, bufferOptions=set(), **kw ) :

		GLWidget.__init__( self, bufferOptions, **kw )

		self._qtWidget().setFocusPolicy( QtCore.Qt.ClickFocus )

		# Force the IECoreGL lazy loading to kick in /now/. Otherwise we can get IECoreGL objects
		# being returned from the GafferUIBindings without the appropriate boost::python converters
		# having been registered first.
		IECoreGL.Renderer

		self.__requestedDepthBuffer = self.BufferOptions.Depth in bufferOptions

		self.__enterConnection = self.enterSignal().connect( Gaffer.WeakMethod( self.__enter ) )
		self.__leaveConnection = self.leaveSignal().connect( Gaffer.WeakMethod( self.__leave ) )
		self.__keyPressConnection = self.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ) )
		self.__keyReleaseConnection = self.keyReleaseSignal().connect( Gaffer.WeakMethod( self.__keyRelease ) )
		self.__buttonPressConnection = self.buttonPressSignal().connect( Gaffer.WeakMethod( self.__buttonPress ) )
		self.__buttonReleaseConnection = self.buttonReleaseSignal().connect( Gaffer.WeakMethod( self.__buttonRelease ) )
		self.__buttonDoubleClickConnection = self.buttonDoubleClickSignal().connect( Gaffer.WeakMethod( self.__buttonDoubleClick ) )
		self.__mouseMoveConnection = self.mouseMoveSignal().connect( Gaffer.WeakMethod( self.__mouseMove ) )
		self.__dragBeginConnection = self.dragBeginSignal().connect( Gaffer.WeakMethod( self.__dragBegin ) )
		self.__dragEnterConnection = self.dragEnterSignal().connect( Gaffer.WeakMethod( self.__dragEnter ) )
		self.__dragMoveConnection = self.dragMoveSignal().connect( Gaffer.WeakMethod( self.__dragMove ) )
		self.__dragLeaveConnection = self.dragLeaveSignal().connect( Gaffer.WeakMethod( self.__dragLeave ) )
		self.__dropConnection = self.dropSignal().connect( Gaffer.WeakMethod( self.__drop ) )
		self.__dragEndConnection = self.dragEndSignal().connect( Gaffer.WeakMethod( self.__dragEnd ) )

		self.__wheelConnection = self.wheelSignal().connect( Gaffer.WeakMethod( self.__wheel ) )

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

		self.__viewportGadget = viewportGadget
		self.__renderRequestConnection = self.__viewportGadget.renderRequestSignal().connect( Gaffer.WeakMethod( self.__renderRequest ) )
		size = self.size()
		if size.x and size.y :
			self.__viewportGadget.setViewport( size )
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

		if not isinstance( QtGui.QApplication.focusWidget(), ( QtGui.QLineEdit, QtGui.QPlainTextEdit ) ) :
			self._qtWidget().setFocus()

	def __leave( self, widget ) :

		self._qtWidget().clearFocus()

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

		return self.__viewportGadget.wheelSignal()( self.__viewportGadget, event )

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
					IECore.V3f( qEvent.x(), qEvent.y(), 1 ),
					IECore.V3f( qEvent.x(), qEvent.y(), 0 )
				)
			 )

			QtGui.QToolTip.showText( qEvent.globalPos(), toolTip, qObject )

			return True

		return False

# this single instance is used by all widgets
_eventFilter = _EventFilter()
