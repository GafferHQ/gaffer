##########################################################################
#  
#  Copyright (c) 2011, Image Engine Design Inc. All rights reserved.
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
import array

import IECore

import GafferUI

QtGui = GafferUI._qtImport( "QtGui" )

## The Image widget displays an image. This can be specified
# as either a filename, in which case the image is loaded using
# the IECore.Reader mechanism, or an IECore.ImagePrimitive.
## \todo Consider colorspace issues.
class Image( GafferUI.Widget ) :

	def __init__( self, imagePrimitiveOrFileName ) :
	
		GafferUI.Widget.__init__( self, QtGui.QLabel() )
		
		if isinstance( imagePrimitiveOrFileName, basestring ) :
			pixmap = self._qtPixmapFromFile( str( imagePrimitiveOrFileName ) )
		else :
			pixmap = self._qtPixmapFromImagePrimitive( imagePrimitiveOrFileName )
		
		if pixmap is not None :	
			self._qtWidget().setPixmap( pixmap )

	def _qtPixmap( self ) :
	
		return self._qtWidget().pixmap()

	@staticmethod
	def _qtPixmapFromImagePrimitive( image ) :
		
		assert( image.arePrimitiveVariablesValid() )
	
		y = image["Y"].data if "Y" in image else None
		r = image["R"].data if "R" in image else None
		g = image["G"].data if "G" in image else None
		b = image["B"].data if "B" in image else None
		
		if r and g and b :
			channels = [ r, g, b ]
		elif y :
			channels = [ y, y, y ]
		else :
			raise ValueError( "Expected RGB or Y channels in image" )
		
		if "A" in image :
			channels.reverse()
			channels.append( image["A"].data )
			format = QtGui.QImage.Format_ARGB32_Premultiplied
		else :
			format = QtGui.QImage.Format_RGB888
							
		interleaved = IECore.DataInterleaveOp()(
			data = IECore.ObjectVector( channels ),
			targetType = IECore.UCharVectorData.staticTypeId(),
		)
		
		imageSize = image.dataWindow.size() + IECore.V2i( 1 )
		
		image = QtGui.QImage( interleaved.toString(), imageSize.x, imageSize.y, format )
		
		return QtGui.QPixmap( image )

	__pixmapCache = None
	@classmethod
	def _qtPixmapFromFile( cls, fileName ) :
	
		if cls.__pixmapCache is None :
			cls.__pixmapCache = IECore.LRUCache( cls.__cacheGetter )
	
		return cls.__pixmapCache.get( fileName )
		
	__imageSearchPaths = IECore.SearchPath( os.environ.get( "GAFFERUI_IMAGE_PATHS", "" ), ":" )
	@classmethod
	def __cacheGetter( cls, fileName ) :
	
		resolvedFileName = cls.__imageSearchPaths.find( fileName )
		if not resolvedFileName :
			raise Exception( "Unable to find file \"%s\"" % fileName )
							
		try :
			reader = IECore.Reader.create( resolvedFileName )
		except : 
			reader = None
		
		if reader is not None :	
			
			image = reader.read()
			if not isinstance( image, IECore.ImagePrimitive ) :
				raise Exception( "File \"%s\" is not an image file" % resolvedFileName )
		
			result = cls._qtPixmapFromImagePrimitive( image )
		
		else :
		
			result = QtGui.QPixmap( resolvedFileName, "png" )
			
		cost = result.width() * result.height() * ( 4 if result.hasAlpha() else 3 )
		
		return ( result, cost )
