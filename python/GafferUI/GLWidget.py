##########################################################################
#  
#  Copyright (c) 2011, John Haddon. All rights reserved.
#  Copyright (c) 2011-2012, Image Engine Design Inc. All rights reserved.
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

	# we keep a single hidden widget which owns the texture and display lists
	# and then share those with all the widgets we really want to make.
	__sharingWidget = None
			
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
		
		glwidget = QtOpenGL.QGLWidget( format, shareWidget = GLWidget.__retrieveSharingWidget() )
		
		GafferUI.Widget.__init__( self, glwidget, **kw )
		
		self._qtWidget().resizeGL = Gaffer.WeakMethod( self.__resizeGL )
		self._qtWidget().paintGL = Gaffer.WeakMethod( self.__paintGL )
		self._qtWidget().setFocusPolicy( QtCore.Qt.StrongFocus )

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
	
	## This retrieves a gl widget whose gl context all subsequent GafferUI.GLWidgets 
	# will share. In maya this tries to grab one of the model panels, in case you're
	# doing some IECoreGL drawing in maya as well as gaffer - this is because IECoreGL
	# currently only works reliably in a single GL context.
	@classmethod
	def __retrieveSharingWidget( cls ) :
		
		if GLWidget.__sharingWidget is None :
		
			try:
				
				import maya.OpenMayaUI
				import maya.OpenMaya
				import maya.cmds
				import sip
				modelPanels = maya.cmds.getPanel( type="modelPanel" )
				
				glWidget = None

				for panel in modelPanels:
					ptr = maya.OpenMayaUI.MQtUtil.findLayout( panel )
					widget = sip.wrapinstance(long(ptr), QtGui.QWidget)
					glWidget = GLWidget.__findGLWidget( widget )
					if glWidget:
						break
				
				GLWidget.__sharingWidget = glWidget
				
				def newScene( clientData ):
					import GafferUI
					import maya.OpenMaya
					GafferUI.GLWidget.__sharingWidget = None
					maya.OpenMaya.MMessage.removeCallback( GafferUI.GLWidget.__beforeNewCallbackId )
					maya.OpenMaya.MMessage.removeCallback( GafferUI.GLWidget.__beforeOpenCallbackId )
				
				cls.__beforeNewCallbackId = maya.OpenMaya.MSceneMessage.addCallback( maya.OpenMaya.MSceneMessage.kBeforeNew, newScene )
				cls.__beforeOpenCallbackId = maya.OpenMaya.MSceneMessage.addCallback( maya.OpenMaya.MSceneMessage.kBeforeOpen, newScene )
				
			except ImportError, e:
				
				GLWidget.__sharingWidget = QtOpenGL.QGLWidget()
			
		return GLWidget.__sharingWidget

	
	## this method finds a gl widget somewhere in the hierarchy under the supplied
	# widget. 
	@staticmethod
	def __findGLWidget( widget ) :
		
		# is this a gl widget? If so, we're laughing!
		if isinstance( widget, QtOpenGL.QGLWidget ):
			return widget

		layout = widget.layout()
		
		# no layout = no children - this is not the widget you are looking for...
		if layout is None:
			return None
		
		# recurse through children:
		i = 0
		while 1:
			childItem = layout.itemAt(i)

			if childItem is None:
				break

			i = i + 1
			ret = GLWidget.__findGLWidget( childItem.widget() )
			if ret:
				# woop - we've found a gl widget!
				return ret

		return None
	
