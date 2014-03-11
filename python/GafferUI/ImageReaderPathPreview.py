##########################################################################
#  
#  Copyright (c) 2012-2014, Image Engine Design Inc. All rights reserved.
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

import IECore

import Gaffer
import GafferUI

class ImageReaderPathPreview( GafferUI.DeferredPathPreview ) :

	def __init__( self, path ) :
	
		self.__renderableGadget = GafferUI.RenderableGadget( None )
		self.__gadgetWidget = GafferUI.GadgetWidget(
			self.__renderableGadget,
			bufferOptions = set( (
				GafferUI.GLWidget.BufferOptions.Depth,
				GafferUI.GLWidget.BufferOptions.Double,
			) ),
		)
	
		GafferUI.DeferredPathPreview.__init__( self, self.__gadgetWidget, path )
		
		self._updateFromPath()
		
	def isValid( self ) :
	
		if not isinstance( self.getPath(), Gaffer.FileSystemPath ) :
			return False
			
		ext = os.path.splitext( str( self.getPath() ) )[1]
		if not ext :
			return False
			
		return ext[1:].lower() in IECore.Reader.supportedExtensions( IECore.TypeId.ImageReader )
		
	def _load( self ) :
	
		reader = None
		with IECore.IgnoredExceptions( RuntimeError ) :
			reader = IECore.ImageReader.create( str( self.getPath() ) )
	
		if reader is None :
			return None
			
		o = None
		with IECore.IgnoredExceptions( RuntimeError ) :
			o = reader.read()
			
		if not isinstance( o, IECore.VisibleRenderable ) :
			return None
			
		if isinstance( o, IECore.ImagePrimitive ) :
			## \todo Deal with colorspace uniformly everywhere, doing the
			# transformations in the viewers themselves.
			IECore.LinearToSRGBOp()( input=o, copyInput=False )

		return o
	
	def _deferredUpdate( self, o ) :
	
		self.__renderableGadget.setRenderable( o )
		
		if isinstance( o, IECore.ImagePrimitive ) :
			camera = IECore.Camera( parameters = { "projection" : "orthographic" } )
		else :
			camera = IECore.Camera( parameters = { "projection" : "perspective" } )
		
		self.__gadgetWidget.getViewportGadget().setCamera( camera )
		self.__gadgetWidget.getViewportGadget().frame( o.bound(), IECore.V3f( 0, 0, -1 ) )

GafferUI.PathPreviewWidget.registerType( "Preview", ImageReaderPathPreview )
