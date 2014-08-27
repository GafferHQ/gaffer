##########################################################################
#
#  Copyright (c) 2011, John Haddon. All rights reserved.
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

import os
import ctypes
import logging

# the OpenGL module loves spewing things into logs, and for some reason
# when running in maya 2012 the default log level allows info messages through.
# so we set a specific log level on the OpenGL logger to keep it quiet.
logging.getLogger( "OpenGL" ).setLevel( logging.WARNING )

import IECore

import Gaffer
import GafferUI

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

	## Adds a Widget as an overlay.
	## \todo Support more than one overlay, and provide grid-based
	# placement options. Perhaps GLWidget should also derive from Container
	# to support auto-parenting and appropriate removeChild() behaviour.
	def addOverlay( self, overlay ) :

		assert( overlay.parent() is None )

		self.__overlay = overlay
		self.__overlay._setStyleSheet()

		item = self.__graphicsScene.addWidget( self.__overlay._qtWidget() )

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
	def __createHostedQGLWidget( cls, format, hostContextActivator ) :

		# When running Gaffer embedded in a host application such as Maya
		# or Houdini, we want to be able to share OpenGL resources between
		# gaffer uis and host viewport uis, because IECoreGL will be used
		# in both. So we implement our own QGLContext class which creates a
		# context which shares with the host.

		import OpenGL.GLX

		# This is our custom context class which allows us to share gl
		# resources with the hosts's contexts. We define it in here rather than
		# at the top level because we want to import QtOpenGL lazily and
		# don't want to trigger a full import until the last minute.
		## \todo Call glXDestroyContext appropriately, although as far as I
		# can tell this is impossible. The base class implementation calls it
		# in reset(), but that's not virtual, and we can't store it in d->cx
		# (which is what the base class destroys) because that's entirely
		# on the C++ side of things.
		class HostedGLContext( QtOpenGL.QGLContext ) :

			def __init__( self, format, paintDevice, hostContextActivator ) :

				QtOpenGL.QGLContext.__init__( self, format, paintDevice )

				self.__paintDevice = paintDevice
				self.__context = None
				self.__hostContextActivator = hostContextActivator

			def chooseContext( self, shareContext ) :

				assert( self.__context is None )

				# We have to call this to get d->vi set in the base class, because
				# QGLWidget::setContext() accesses it directly, and will crash if we don't.
				QtOpenGL.QGLContext.chooseContext( self, shareContext )

				# Get the host's main OpenGL context. It is the responsibility
				# of the hostContextActivator passed to __init__ to make the host
				# context current so we can access it.
				self.__hostContextActivator()
				hostContext = OpenGL.GLX.glXGetCurrentContext()
				self.__display = OpenGL.GLX.glXGetCurrentDisplay()

				# Get a visual - we let the base class figure this out, but then we need
				# to convert it from the form given by the qt bindings into the ctypes form
				# needed by PyOpenGL.
				visual = self.chooseVisual()
				visual = ctypes.cast( int( visual ), ctypes.POINTER( OpenGL.raw._GLX.XVisualInfo ) )

				# Make our context.
				self.__context = OpenGL.GLX.glXCreateContext(
					self.__display[0],
					visual,
					hostContext,
					True
				)

				return True

			def makeCurrent( self ) :

				success = OpenGL.GLX.glXMakeCurrent( self.__display, self.__paintDevice.effectiveWinId(), self.__context )
				assert( success )

		result = QtOpenGL.QGLWidget()
		result.setContext( HostedGLContext( format, result, hostContextActivator ) )
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
		return cls.__createHostedQGLWidget( format, IECore.curry( mayaRenderer.makeResourceContextCurrent, mayaRenderer.backEndString() ) )

	@classmethod
	def __createHoudiniQGLWidget( cls, format ) :

		try :
			import hou
		except ImportError :
			# we're not in houdini - createQGLWidget() will just make a
			# normal widget.
			return None

		import IECoreHoudini
		return cls.__createHostedQGLWidget( format, IECoreHoudini.makeMainGLContextCurrent )

class _GLGraphicsScene( QtGui.QGraphicsScene ) :

	def __init__( self, parent, backgroundDrawFunction ) :

		QtGui.QGraphicsScene.__init__( self, parent )

		self.__backgroundDrawFunction = backgroundDrawFunction
		self.sceneRectChanged.connect( self.__sceneRectChanged )

	def addWidget( self, widget ) :

		if widget.layout() is not None :
			# removing the size constraint is necessary to keep the widget the
			# size we tell it to be in __updateItemGeometry.
			widget.layout().setSizeConstraint( QtGui.QLayout.SetNoConstraint )

		item = QtGui.QGraphicsScene.addWidget( self, widget )
		self.__updateItemGeometry( item, self.sceneRect() )

		return item

	def drawBackground( self, painter, rect ) :

		self.__backgroundDrawFunction()

	def __sceneRectChanged( self, sceneRect ) :

		for item in self.items() :
			self.__updateItemGeometry( item, sceneRect )

	def __updateItemGeometry( self, item, sceneRect ) :

		geometry = item.widget().geometry()
		item.widget().setGeometry( QtCore.QRect( 0, 0, sceneRect.width(), item.widget().sizeHint().height() ) )
