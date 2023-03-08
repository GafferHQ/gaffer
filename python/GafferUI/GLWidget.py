##########################################################################
#
#  Copyright (c) 2011, John Haddon. All rights reserved.
#  Copyright (c) 2011-2015, Image Engine Design Inc. All rights reserved.
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

import sys
import logging
import collections

# the OpenGL module loves spewing things into logs, and for some reason
# when running in maya 2012 the default log level allows info messages through.
# so we set a specific log level on the OpenGL logger to keep it quiet.
logging.getLogger( "OpenGL" ).setLevel( logging.WARNING )
import imath

import IECore
import IECoreGL

import Gaffer
import GafferUI
from . import _GafferUI

import OpenGL.GL as GL

import Qt
from Qt import QtCore

# Importing directly rather than via Qt.py because Qt.py won't expose the
# Qt-5-only QOpenGLWidget and QSurfaceFormat classes that we need. Their mantra
# is to provide only what is available in Qt4/PySide1 - see
# https://github.com/mottosso/Qt.py/issues/341.
## \todo Now that Qt 4 is long gone, and PySide is an official
# Qt project, Qt.py isn't much help. Remove across the board, or see
# if we can coax the project into bridging Qt 5/6 instead of 4/5?
from PySide2 import QtGui
from PySide2 import QtWidgets

## The GLWidget is a base class for all widgets which wish to draw using OpenGL.
# Derived classes override the _draw() method to achieve this.
class GLWidget( GafferUI.Widget ) :

	## This enum defines the optional elements of the GL buffer used
	# for display.
	BufferOptions = IECore.Enum.create(
		"Alpha",
		"Depth",
		"AntiAlias",
	)

	## Note that you won't always get the buffer options you ask for - a best fit is found
	# among the available formats. In particular it appears that a depth buffer is often present
	# even when not requested.
	def __init__( self, bufferOptions = set(), **kw ) :

		format = QtGui.QSurfaceFormat()

		if self.BufferOptions.Alpha in bufferOptions :
			format.setAlphaBufferSize( 8 )
		if self.BufferOptions.Depth in bufferOptions :
			format.setDepthBufferSize( 24 )

		self.__multisample = self.BufferOptions.AntiAlias in bufferOptions
		if self.__multisample:
			format.setSamples( 8 )

		format.setVersion( 2, 1 )

		graphicsView = _GLGraphicsView( format )
		self.__graphicsScene = _GLGraphicsScene( graphicsView, Gaffer.WeakMethod( self.__draw ) )
		graphicsView.setScene( self.__graphicsScene )

		GafferUI.Widget.__init__( self, graphicsView, **kw )

		self.__overlays = set()
		self.visibilityChangedSignal().connect( Gaffer.WeakMethod( self.__visibilityChanged ), scoped = False )

	## Adds a widget to be overlaid on top of the GL rendering,
	# stretched to fill the frame.
	def addOverlay( self, overlay ) :

		if overlay in self.__overlays :
			return

		oldParent = overlay.parent()
		if oldParent is not None :
			oldParent.removeChild( child )

		self.__overlays.add( overlay )
		overlay._setStyleSheet()

		self.__graphicsScene.addOverlay( overlay )

	def removeOverlay( self, overlay ) :

		self.removeChild( overlay )

	def removeChild( self, child ) :

		assert( child in self.__overlays )
		self.__graphicsScene.removeOverlay( child )
		self.__overlays.remove( child )

	## Called whenever the widget is resized. May be reimplemented by derived
	# classes if necessary.
	# > Note : An OpenGL context is not available when this function is called.
	def _resize( self, size ) :

		return

	## Derived classes must override this to draw their contents using
	# OpenGL calls. The appropriate OpenGL context will already be current
	# when this is called.
	def _draw( self ) :

		pass

	## Derived classes may call this when they wish to trigger a redraw.
	def _redraw( self ) :

		self._glWidget().update()

	## May be used by derived classes to get access to the internal
	# QOpenGLWidget. Note that `_makeCurrent()` should be used in preference
	# to `_glWidget().makeCurrent()`, for the reasons stated in the
	# documentation for that method.
	def _glWidget( self ) :

		return self._qtWidget().viewport()

	## May be used by derived classes to make the OpenGL context
	# for this widget current. Returns True if the operation was
	# successful and False if not.
	## \todo This function was originally introduced to work around
	# bugs in Qt's QGLWidget. It may be unnecessary now that we are
	# using a QOpenGLWidget.
	def _makeCurrent( self ) :

		if self._qtWidget().viewport().context() is None :
			return False

		self._qtWidget().viewport().makeCurrent()
		return True

	def __draw( self ) :

		# we need to call the init method after a GL context has been
		# created, and this seems like the only place that is guaranteed.
		# calling it here does mean we call init() way more than needed,
		# but it's safe.
		IECoreGL.init( True )

		if self.__multisample:
			GL.glEnable( GL.GL_MULTISAMPLE )

		try :
			self._draw()
		except Exception as e :
			IECore.msg( IECore.Msg.Level.Error, "GLWidget", str( e ) )

	def __visibilityChanged( self, widget ) :

		# Transfer our visibility to our overlay widgets, so that
		# their `visibilityChangedSignal()` is emitted as well (Qt
		# doesn't handle this for us). This is particularly important
		# for overlays which use LazyMethod and BackgroundMethod, both
		# of which react to visibility changes.
		for overlay in self.__overlays :
			overlay._qtWidget().setVisible( self.visible() )

class _GLGraphicsView( QtWidgets.QGraphicsView ) :

	def __init__( self, format ) :

		QtWidgets.QGraphicsView.__init__( self )

		self.setHorizontalScrollBarPolicy( QtCore.Qt.ScrollBarAlwaysOff )
		self.setVerticalScrollBarPolicy( QtCore.Qt.ScrollBarAlwaysOff )

		glWidget = QtWidgets.QOpenGLWidget()
		# Avoid `QOpenGLFramebufferObject: Framebuffer incomplete attachment`
		# errors caused by Qt trying to make a framebuffer with zero size.
		glWidget.setMinimumSize( 1, 1 )
		glWidget.setFormat( format )
		self.setViewport( glWidget )
		self.setViewportUpdateMode( self.FullViewportUpdate )

	# QAbstractScrollArea (one of our base classes), implements
	# minimumSizeHint() to include enough room for scrollbars.
	# But we know we'll never show scrollbars, and don't want
	# a minimum size, so we reimplement it.
	def minimumSizeHint( self ) :

		return QtCore.QSize()

	def resizeEvent( self, event ) :

		if self.scene() is not None :

			self.scene().setSceneRect( 0, 0, event.size().width(), event.size().height() )
			owner = GafferUI.Widget._owner( self )
			owner._resize( imath.V2i( event.size().width(), event.size().height() ) )

	def keyPressEvent( self, event ) :

		# We have to reimplement this method to prevent QAbstractScrollArea
		# from stealing the cursor keypresses, preventing them from
		# being used by GLWidget subclasses. QAbstractScrollArea uses
		# those keypresses to move the scrollbars, but we don't want the
		# scrolling functionality at all. Our implementation of this method
		# is functionally identical to the QGraphicsView one, except it
		# passes unused events to QFrame, bypassing QAbstractScrollArea.

		if self.scene() is not None and self.isInteractive() :
			QtWidgets.QApplication.sendEvent( self.scene(), event )
			if event.isAccepted() :
				return

		QtWidgets.QFrame.keyPressEvent( self, event )

class _GLGraphicsScene( QtWidgets.QGraphicsScene ) :

	__Overlay = collections.namedtuple( "__Overlay", [ "widget", "proxy" ] )

	def __init__( self, parent, backgroundDrawFunction ) :

		QtWidgets.QGraphicsScene.__init__( self, parent )

		self.__backgroundDrawFunction = backgroundDrawFunction
		self.sceneRectChanged.connect( self.__sceneRectChanged )

		self.__overlays = {} # Mapping from GafferUI.Widget to _OverlayProxyWidget

	def addOverlay( self, widget ) :

		if widget._qtWidget().layout() is not None :
			# removing the size constraint is necessary to keep the widget the
			# size we tell it to be in __updateItemGeometry.
			widget._qtWidget().layout().setSizeConstraint( QtWidgets.QLayout.SetNoConstraint )

		proxy = _OverlayProxyWidget()
		proxy.setWidget( widget._qtWidget() )
		self.__overlays[widget] = proxy

		self.addItem( proxy )
		self.__updateItemGeometry( proxy, self.sceneRect() )

	def removeOverlay( self, widget ) :

		item = self.__overlays[widget]
		item.setWidget( None )
		self.removeItem( item )
		del self.__overlays[widget]

	def drawBackground( self, painter, rect ) :

		painter.beginNativePainting()

		# Qt sometimes enters this method with a GL error flag still set.
		# We unset it here so it won't trigger our own error checking.
		## \todo Determine if this is still necessary now that we've
		# transitioned from QGLWidget to QOpenGLWidget.
		while GL.glGetError() :
			pass

		GL.glPushAttrib( GL.GL_ALL_ATTRIB_BITS )
		GL.glPushClientAttrib( GL.GL_CLIENT_ALL_ATTRIB_BITS )

		self.__backgroundDrawFunction()

		GL.glPopClientAttrib()
		GL.glPopAttrib()

		painter.endNativePainting()

	## QGraphicsScene consumes all drag events by default, which is unhelpful
	# for us as it breaks any Qt based drag-drop we may be attempting.
	def dragEnterEvent( self, event ) :

		event.ignore()

	def __sceneRectChanged( self, sceneRect ) :

		for proxy in self.__overlays.values() :
			self.__updateItemGeometry( proxy, sceneRect )

	def __updateItemGeometry( self, item, sceneRect ) :

		item.widget().setGeometry( QtCore.QRect( 0, 0, sceneRect.width(), sceneRect.height() ) )

## A QGraphicsProxyWidget whose shape is derived from the opaque parts of its
# child widgets. This allows our overlays to pass through events in the regions
# where there isn't a visible child widget.
#
# shape() is called frequently but our mask is relatively expensive to calculate.
# As transparency is stylesheet dependent, we need to render our child widgets
# and work out a mask from the resultant alpha.
#
# To minimise impact, We only re-calculate our mask whenever our layout
# changes. This covers 99% of common use cases, with the only exception that
# mouse-driven opacity changes won't be considered.
class _OverlayProxyWidget( QtWidgets.QGraphicsProxyWidget ) :

	def __init__( self ) :

		QtWidgets.QGraphicsProxyWidget.__init__( self )
		self.__shape = None

	def setWidget( self, widget ) :

		QtWidgets.QGraphicsProxyWidget.setWidget( self, widget )
		self.__shape = None

	def shape( self ) :

		if self.__shape is None :

			self.__shape = QtGui.QPainterPath()
			if self.widget() :
				pixmap = self.widget().grab()
				if pixmap.size() != self.widget().size() :
					# Account for the widget being grabbed at a higher resolution
					# when using high resolution displays.
					pixmap = pixmap.scaled( self.widget().size() )
				self.__shape.addRegion( QtGui.QRegion( pixmap.mask() ) )

		return self.__shape

	# This covers re-layouts due to child changes, and parent changes (such as window resizing)
	def setGeometry( self, *args, **kwargs ) :

		QtWidgets.QGraphicsProxyWidget.setGeometry( self, *args, **kwargs )
		self.__shape = None
