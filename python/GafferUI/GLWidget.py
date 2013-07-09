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
				
		GafferUI.Widget.__init__( self, self.__createQGLWidget( format ), **kw )
		
		self._qtWidget().resizeGL = Gaffer.WeakMethod( self.__resizeGL )
		self._qtWidget().paintGL = Gaffer.WeakMethod( self.__paintGL )

	## Called whenever the widget is resized. May be reimplemented by derived
	# classes if necessary.
	def _resize( self, size ) :
	
		GL.glViewport( 0, 0, size.x, size.y )
	
	## Derived classes must override this to draw their contents using
	# OpenGL calls.
	def _draw( self ) :
	
		raise NotImplementedError
		
	## Derived classes may call this when they wish to trigger a redraw.
	def _redraw( self, immediate=False ) :
		
		if immediate :
			self._qtWidget().updateGL()
		else :
			self._qtWidget().update()
	
	def __resizeGL( self, width, height ) :
		
		self._resize( IECore.V2i( width, height ) )

	def __paintGL( self ) :
	
		# we need to call the init method after a GL context has been
		# created. ideally we'd call it in a QGLWidget.initializeGL override but
		# at the time of writing that's not getting called. calling it here does
		# mean we call init() way more than needed, but it's safe.
		IECoreGL.init( True )
		
		self._draw()

	# We keep a single hidden widget which owns the texture and display lists
	# and then share those with all the widgets we really want to make.
	__shareWidget = None
	@classmethod
	def __createQGLWidget( cls, format ) :
	
		# try to make a host specific widget if necessary.
		result = cls.__createMayaQGLWidget( format )
		if result is not None :
			return result
		
		# and if it wasn't necessary, just breathe a sigh of relief
		# and make a nice normal one.
		if cls.__shareWidget is None :
			cls.__shareWidget = QtOpenGL.QGLWidget()
			
		return QtOpenGL.QGLWidget( format, shareWidget = cls.__shareWidget )
			
	@classmethod
	def __createMayaQGLWidget( cls, format ) :
	
		# We want to be able to share OpenGL resources between gaffer uis
		# and maya viewport uis, because IECoreGL will be used in both.
		# So we implement our own QGLContext class which creates a context
		# which shares with maya.
				
		try :
			import maya.OpenMayaRender
		except ImportError :
			# we're not in maya - createQGLWidget() will just make a
			# normal widget.
			return None

		import OpenGL.GLX
		
		# This is our custom context class which allows us to share gl
		# resources with maya's contexts. We define it in here rather than
		# at the top level because we want to import QtOpenGL lazily and
		# don't want to trigger a full import until the last minute.
		## \todo Call glXDestroyContext appropriately, although as far as I
		# can tell this is impossible. The base class implementation calls it
		# in reset(), but that's not virtual, and we can't store it in d->cx
		# (which is what the base class destroys) because that's entirely
		# on the C++ side of things.
		class MayaGLContext( QtOpenGL.QGLContext ) :
		
			def __init__( self, format, paintDevice ) :
			
				QtOpenGL.QGLContext.__init__( self, format, paintDevice )
				
				self.__paintDevice = paintDevice
				self.__context = None
		
			def chooseContext( self, shareContext ) :
				
				assert( self.__context is None )

				# We have to call this to get d->vi set in the base class, because
				# QGLWidget::setContext() accesses it directly, and will crash if we don't.
				QtOpenGL.QGLContext.chooseContext( self, shareContext )

				# Get maya's global resource context - we'll create our context
				# to be sharing with this one.
				import maya.OpenMayaRender
				mayaRenderer = maya.OpenMayaRender.MHardwareRenderer.theRenderer()
				mayaRenderer.makeResourceContextCurrent( mayaRenderer.backEndString() )
				mayaResourceContext = OpenGL.GLX.glXGetCurrentContext()
				self.__display = OpenGL.GLX.glXGetCurrentDisplay()
				
				# Get a visual - we let the base class figure this out, but then we need
				# to convert it from the form given by the qt bindings into the ctypes form
				# needed by PyOpenGL.
				visual = self.chooseVisual()
				visual = ctypes.cast( int( visual ), ctypes.POINTER( OpenGL.raw._GLX.XVisualInfo ) )
				
				# Make our context.
				self.__context = OpenGL.GLX.glXCreateContext(
					OpenGL.GLX.glXGetCurrentDisplay()[0],
					visual,
					OpenGL.GLX.glXGetCurrentContext(),
					True
				)

				return True

			def makeCurrent( self ) :

				success = OpenGL.GLX.glXMakeCurrent( self.__display, self.__paintDevice.effectiveWinId(), self.__context )
				assert( success )
				
		result = QtOpenGL.QGLWidget()
		result.setContext( MayaGLContext( format, result ) )
		return result
