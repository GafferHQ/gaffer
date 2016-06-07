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

import logging

# the OpenGL module loves spewing things into logs, and for some reason
# when running in maya 2012 the default log level allows info messages through.
# so we set a specific log level on the OpenGL logger to keep it quiet.
logging.getLogger( "OpenGL" ).setLevel( logging.WARNING )

import IECore

import Gaffer
import GafferUI
import _GafferUI

# import lazily to improve startup of apps which don't use GL functionality
GL = Gaffer.lazyImport( "OpenGL.GL" )
IECoreGL = Gaffer.lazyImport( "IECoreGL" )

QtCore = GafferUI._qtImport( "QtCore" )
QtGui = GafferUI._qtImport( "QtGui" )
QtOpenGL = GafferUI._qtImport( "QtOpenGL", lazy=True )

## The GLWidget is a base class for all widgets which wish to draw using OpenGL.
# Derived classes override the _draw() method to achieve this.
class GLWidget( GafferUI.Widget ) :

	## This enum defines the optional elements of the GL buffer used
	# for display.
	BufferOptions = IECore.Enum.create(
		"Alpha",
		"Depth",
		"Double"
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

		if hasattr( format, "setVersion" ) : # setVersion doesn't exist in qt prior to 4.7.
			format.setVersion( 2, 1 )

		graphicsView = _GLGraphicsView( format )
		self.__graphicsScene = _GLGraphicsScene( graphicsView, Gaffer.WeakMethod( self.__draw ) )
		graphicsView.setScene( self.__graphicsScene )

		GafferUI.Widget.__init__( self, graphicsView, **kw )

		self.__overlay = None

	## Specifies a widget to be overlaid on top of the GL rendering,
	# stretched to fill the frame. To add multiple widgets and/or gain
	# more control over the layout, use a Container as the overlay and
	# use it to layout multiple child widgets.
	def setOverlay( self, overlay ) :

		if overlay is self.__overlay :
			return

		if self.__overlay is not None :
			self.removeChild( self.__overlay )

		if overlay is not None :
			oldParent = overlay.parent()
			if oldParent is not None :
				oldParent.removeChild( child )

		self.__overlay = overlay
		self.__overlay._setStyleSheet()

		self.__graphicsScene.setOverlay( self.__overlay )

	def getOverlay( self ) :

		return self.__overlay

	def removeChild( self, child ) :

		assert( child is self.__overlay )
		self.__overlay = None
		self.__graphicsScene.setOverlay( None )

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

		# Qt sometimes enters our GraphicsScene.drawBackground() method
		# with a GL error flag still set. We unset it here so it won't
		# trigger our own error checking.
		while GL.glGetError() :
			pass

		if not self.__framebufferValid() :
			return

		# we need to call the init method after a GL context has been
		# created, and this seems like the only place that is guaranteed.
		# calling it here does mean we call init() way more than needed,
		# but it's safe.
		## \todo: this might be removable if we can prove resizeEvent
		# is always called first.
		IECoreGL.init( True )

		self._draw()

class _GLGraphicsView( QtGui.QGraphicsView ) :

	def __init__( self, format ) :

		QtGui.QGraphicsView.__init__( self )

		self.setObjectName( "gafferGLWidget" )
		self.setHorizontalScrollBarPolicy( QtCore.Qt.ScrollBarAlwaysOff )
		self.setVerticalScrollBarPolicy( QtCore.Qt.ScrollBarAlwaysOff )

		glWidget = self.__createQGLWidget( format )

		# On mac, we need to hide the GL widget until the last
		# possible moment, otherwise we get "invalid drawable"
		# errors spewing all over the place. See event() for the
		# spot where we show the widget.
		glWidget.hide()

		self.setViewport( glWidget )
		self.setViewportUpdateMode( self.FullViewportUpdate )

	# QAbstractScrollArea (one of our base classes), implements
	# minimumSizeHint() to include enough room for scrollbars.
	# But we know we'll never show scrollbars, and don't want
	# a minimum size, so we reimplement it.
	def minimumSizeHint( self ) :

		return QtCore.QSize()

	def event( self, event ) :

		if event.type() == event.PolishRequest :
			# This seems to be the one signal that reliably
			# lets us know we're becoming genuinely visible
			# on screen. We use it to show the GL widget we
			# hid in our constructor.
			self.viewport().show()

		return QtGui.QGraphicsView.event( self, event )

	def resizeEvent( self, event ) :

		if self.scene() is not None :

			self.scene().setSceneRect( 0, 0, event.size().width(), event.size().height() )
			owner = GafferUI.Widget._owner( self )

			# clear any existing errors that may trigger
			# error checking code in _resize implementations.
			while GL.glGetError() :
				pass

			owner._makeCurrent()

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

			owner._resize( IECore.V2i( event.size().width(), event.size().height() ) )

	def keyPressEvent( self, event ) :

		# We have to reimplement this method to prevent QAbstractScrollArea
		# from stealing the cursor keypresses, preventing them from
		# being used by GLWidget subclasses. QAbstractScrollArea uses
		# those keypresses to move the scrollbars, but we don't want the
		# scrolling functionality at all. Our implementation of this method
		# is functionally identical to the QGraphicsView one, except it
		# passes unused events to QFrame, bypassing QAbstractScrollArea.

		if self.scene() is not None and self.isInteractive() :
			QtGui.QApplication.sendEvent( self.scene(), event )
			if event.isAccepted() :
				return

		QtGui.QFrame.keyPressEvent( self, event )

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

		# Prior to Houdini 14 we are running embedded on the hou.ui idle loop,
		# so we needed to force the Houdini GL context to be current, and share
		# it, similar to how we do this in Maya.
		if hou.applicationVersion()[0] < 14 :
			IECoreHoudini.makeMainGLContextCurrent()
			return cls.__createHostedQGLWidget( format )

		# In Houdini 14 and beyond, Qt is the native UI, and we can access
		# Houdini's shared QGLWidget directly, provided we are using a recent
		# Cortex version.
		return QtOpenGL.QGLWidget( format, shareWidget = GafferUI._qtObject( IECoreHoudini.sharedGLWidget(), QtOpenGL.QGLWidget ) )

class _GLGraphicsScene( QtGui.QGraphicsScene ) :

	def __init__( self, parent, backgroundDrawFunction ) :

		QtGui.QGraphicsScene.__init__( self, parent )

		self.__backgroundDrawFunction = backgroundDrawFunction
		self.sceneRectChanged.connect( self.__sceneRectChanged )

		self.__overlay = None # Stores the GafferUI.Widget
		self.__overlayProxy = None # Stores the _OverlayProxyWidget

	def setOverlay( self, widget ) :

		if self.__overlay is not None :
			self.__overlayProxy.setWidget( None )
			self.removeItem( self.__overlayProxy )
			self.__overlay = None
			self.__overlayProxy = None

		if widget is None :
			return

		self.__overlay = widget
		if widget._qtWidget().layout() is not None :
			# removing the size constraint is necessary to keep the widget the
			# size we tell it to be in __updateItemGeometry.
			widget._qtWidget().layout().setSizeConstraint( QtGui.QLayout.SetNoConstraint )

		self.__overlayProxy = _OverlayProxyWidget()
		self.__overlayProxy.setWidget( self.__overlay._qtWidget() )

		self.addItem( self.__overlayProxy )
		self.__updateItemGeometry( self.__overlayProxy, self.sceneRect() )

	def drawBackground( self, painter, rect ) :

		self.__backgroundDrawFunction()

		# Reset pixel store setting back to the default. IECoreGL
		# (and the ImageGadget) meddle with this, and it throws off
		# the QGraphicsEffects.
		GL.glPixelStorei( GL.GL_UNPACK_ALIGNMENT, 4 );

	def __sceneRectChanged( self, sceneRect ) :

		if self.__overlayProxy is not None :
			self.__updateItemGeometry( self.__overlayProxy, sceneRect )

	def __updateItemGeometry( self, item, sceneRect ) :

		geometry = item.widget().geometry()
		item.widget().setGeometry( QtCore.QRect( 0, 0, sceneRect.width(), sceneRect.height() ) )

## A QGraphicsProxyWidget whose shape is composed from the
# bounds of its child widgets. This allows our overlays to
# pass through events in the regions where there isn't a
# child widget.
class _OverlayProxyWidget( QtGui.QGraphicsProxyWidget ) :

	def __init__( self ) :

		QtGui.QGraphicsProxyWidget.__init__( self )

	def shape( self ) :

		path = QtGui.QPainterPath()
		path.addRegion( self.widget().childrenRegion() )
		return path
