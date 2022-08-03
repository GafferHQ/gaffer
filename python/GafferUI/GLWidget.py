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
from Qt import QtGui
from Qt import QtWidgets
from Qt import QtOpenGL

## The GLWidget is a base class for all widgets which wish to draw using OpenGL.
# Derived classes override the _draw() method to achieve this.
class GLWidget( GafferUI.Widget ) :

	## This enum defines the optional elements of the GL buffer used
	# for display.
	BufferOptions = IECore.Enum.create(
		"Alpha",
		"Depth",
		"Double",
		"AntiAlias"
	)

	## Note that you won't always get the buffer options you ask for - a best fit is found
	# among the available formats. In particular it appears that a depth buffer is often present
	# even when not requested.
	def __init__( self, bufferOptions = set(), **kw ) :

		format = QtOpenGL.QGLFormat()
		format.setRgba( True )

		format.setAlpha( self.BufferOptions.Alpha in bufferOptions )
		format.setDepth( self.BufferOptions.Depth in bufferOptions )
		format.setDoubleBuffer( self.BufferOptions.Double in bufferOptions )

		self.__multisample = self.BufferOptions.AntiAlias in bufferOptions
		if self.__multisample:
			format.setSampleBuffers( True )
			format.setSamples( 8 )

		if hasattr( format, "setVersion" ) : # setVersion doesn't exist in qt prior to 4.7.
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
		if Qt.__binding__ in ( "PySide2", "PyQt5" ) :
			# Force Qt to use a raster drawing path for the overlays.
			#
			# - On Mac, this avoids "QMacCGContext:: Unsupported painter devtype type 1"
			#   errors. See https://bugreports.qt.io/browse/QTBUG-32639 for
			#   further details.
			# - On Linux, this avoids an unknown problem which manifests as
			#   a GL error that appears to occur inside Qt's code, and which
			#   is accompanied by text drawing being scrambled in the overlay.
			#
			## \todo When we no longer need to support Qt4, we should be
			# able to stop using a QGLWidget for the viewport, and this
			# should no longer be needed.
			overlay._qtWidget().setWindowOpacity( 0.9999 )

		self.__graphicsScene.addOverlay( overlay )

	def removeOverlay( self, overlay ) :

		self.removeChild( overlay )

	def removeChild( self, child ) :

		assert( child in self.__overlays )
		self.__graphicsScene.removeOverlay( child )
		self.__overlays.remove( child )

	## Called whenever the widget is resized. May be reimplemented by derived
	# classes if necessary. The appropriate OpenGL context will already be current
	# when this is called.
	def _resize( self, size ) :

		GL.glViewport( 0, 0, size.x, size.y )

	## Derived classes must override this to draw their contents using
	# OpenGL calls. The appropriate OpenGL context will already be current
	# when this is called.
	def _draw( self ) :

		pass

	## Derived classes may call this when they wish to trigger a redraw.
	def _redraw( self ) :

		self._glWidget().update()

	## May be used by derived classes to get access to the internal
	# QGLWidget. Note that _makeCurrent() should be used in preference
	# to _glWidget().makeCurrent(), for the reasons stated in the
	# documentation for that method.
	def _glWidget( self ) :

		return self._qtWidget().viewport()

	## May be used by derived classes to make the OpenGL context
	# for this widget current. Returns True if the operation was
	# successful and False if not. In an ideal world, the return
	# value would always be True, but it appears that there are
	# Qt/Mac bugs which cause it not to be from time to time -
	# typically for newly created Widgets. If False is returned,
	# no OpenGL operations should be undertaken subsequently by
	# the caller.
	def _makeCurrent( self ) :

		self._qtWidget().viewport().makeCurrent()
		return self.__framebufferValid()

	def __framebufferValid( self ) :

		import OpenGL.GL.framebufferobjects
		return GL.framebufferobjects.glCheckFramebufferStatus( GL.framebufferobjects.GL_FRAMEBUFFER ) == GL.framebufferobjects.GL_FRAMEBUFFER_COMPLETE

	def __draw( self ) :

		if not self.__framebufferValid() :
			return

		# we need to call the init method after a GL context has been
		# created, and this seems like the only place that is guaranteed.
		# calling it here does mean we call init() way more than needed,
		# but it's safe.
		## \todo: this might be removable if we can prove resizeEvent
		# is always called first.
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

		glWidget = self.__createQGLWidget( format )
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

			owner._makeCurrent()

			# clear any existing errors that may trigger
			# error checking code in _resize implementations.
			while GL.glGetError() :
				pass

			# We need to call the init method after a GL context has been
			# created, but before any events requiring GL have been triggered.
			# We had been doing this from GLWidget.__draw(), but it was still
			# possible to trigger mouseMove events prior to drawing by hovering
			# over top of an about-to-become-visible GLWidget. resizeEvent
			# seems to always be triggered prior to both draw and mouseMove,
			# ensuring GL is initialized in time for those other events.
			# Calling it here does mean we call init() more than needed,
			# but it's safe.
			IECoreGL.init( True )

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

	# We keep a single hidden widget which owns the texture and display lists
	# and then share those with all the widgets we really want to make.
	__shareWidget = None
	@classmethod
	def __createQGLWidget( cls, format ) :

		# try to make a host specific widget if necessary.
		result = cls.__createMayaQGLWidget( format )
		if result is not None :
			return result

		result = cls.__createHoudiniQGLWidget( format )
		if result is not None :
			return result

		# and if it wasn't necessary, just breathe a sigh of relief
		# and make a nice normal one.
		if cls.__shareWidget is None :
			cls.__shareWidget = QtOpenGL.QGLWidget()

		return QtOpenGL.QGLWidget( format, shareWidget = cls.__shareWidget )

	@classmethod
	def __createHostedQGLWidget( cls, format ) :

		# When running Gaffer embedded in a host application such as Maya
		# or Houdini, we want to be able to share OpenGL resources between
		# gaffer uis and host viewport uis, because IECoreGL will be used
		# in both. So we implement our own QGLContext class which creates a
		# context which shares with the host. The custom QGLContext is
		# implemented in GLWidgetBinding.cpp, and automatically shares with
		# the context which is current at the time of its creation. The host
		# context should therefore be made current before calling this
		# method.

		result = QtOpenGL.QGLWidget()
		_GafferUI._glWidgetSetHostedContext( GafferUI._qtAddress( result ), GafferUI._qtAddress( format ) )
		return result

	@classmethod
	def __createMayaQGLWidget( cls, format ) :

		try :
			import maya.OpenMayaRender
		except ImportError :
			# we're not in maya - createQGLWidget() will just make a
			# normal widget.
			return None

		mayaRenderer = maya.OpenMayaRender.MHardwareRenderer.theRenderer()
		mayaRenderer.makeResourceContextCurrent( mayaRenderer.backEndString() )
		return cls.__createHostedQGLWidget( format )

	@classmethod
	def __createHoudiniQGLWidget( cls, format ) :

		try :
			import hou
		except ImportError :
			# we're not in houdini - createQGLWidget() will just make a
			# normal widget.
			return None

		import IECoreHoudini

		if hasattr( IECoreHoudini, "sharedGLWidget" ) :
			# In Houdini 14 and 15, Qt is the native UI, and we can access
			# Houdini's shared QGLWidget directly.
			return QtOpenGL.QGLWidget( format, shareWidget = GafferUI._qtObject( IECoreHoudini.sharedGLWidget(), QtOpenGL.QGLWidget ) )

		# While Qt is the native UI in Houdini 16.0, they have moved away
		# from QGLWidgets for their Qt5 builds, so we need to force the
		# Houdini GL context to be current, and share it.
		IECoreHoudini.makeMainGLContextCurrent()
		return cls.__createHostedQGLWidget( format )

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
