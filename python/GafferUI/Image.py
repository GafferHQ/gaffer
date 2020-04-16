##########################################################################
#
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
import imath

import IECore
import IECoreImage

import GafferUI

from Qt import QtCore
from Qt import QtGui
from Qt import QtWidgets

## The Image widget displays an image. This can be specified
# as either a filename, in which case the image is loaded using
# the IECore.Reader mechanism, or an IECore.ImagePrimitive.
class Image( GafferUI.Widget ) :

	def __init__( self, imagePrimitiveOrFileName, **kw ) :

		GafferUI.Widget.__init__( self, QtWidgets.QLabel(), **kw )

		# by default the widget would accept both shrinking and growing, but we'd rather it just stubbornly stayed
		# the same size.
		self._qtWidget().setSizePolicy( QtWidgets.QSizePolicy( QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed ) )

		if isinstance( imagePrimitiveOrFileName, basestring ) :
			pixmap = self._qtPixmapFromFile( str( imagePrimitiveOrFileName ) )
		else :
			pixmap = self._qtPixmapFromImagePrimitive( imagePrimitiveOrFileName )

		if pixmap is not None :
			self._qtWidget().setPixmap( pixmap )

	def _qtPixmap( self ) :

		return self._qtWidget().pixmap()

	def _qtPixmapHighlighted( self ) :

		pixmap = self._qtWidget().pixmap()

		graphicsScene = QtWidgets.QGraphicsScene()
		pixmapItem = graphicsScene.addPixmap( pixmap )
		pixmapItem.setVisible( True )

		effect = QtWidgets.QGraphicsColorizeEffect()
		effect.setColor( QtGui.QColor( 119, 156, 189, 255 ) )
		effect.setStrength( 0.85 )
		pixmapItem.setGraphicsEffect( effect )
		pixmapItem.setShapeMode( pixmapItem.BoundingRectShape )

		graphicsView = QtWidgets.QGraphicsView()
		graphicsView.setScene( graphicsScene )

		image = QtGui.QImage(
			pixmap.width(),
			pixmap.height(),
			QtGui.QImage.Format_ARGB32_Premultiplied if pixmap.hasAlpha() else QtGui.QImage.Format_RGB888
		)
		image.fill( 0 )

		painter = QtGui.QPainter( image )
		graphicsView.render(
			painter,
			QtCore.QRectF(),
			QtCore.QRect(
				graphicsView.mapFromScene( pixmapItem.boundingRect().topLeft() ),
				graphicsView.mapFromScene( pixmapItem.boundingRect().bottomRight() )
			)
		)
		del painter # must delete painter before image

		return QtGui.QPixmap( image )

	# Qt's native disabled state generation often looks 'more enabled' than
	# standard icons do when the app is using a dark theme.
	def _qtPixmapDisabled( self ) :

		pixmap = self._qtWidget().pixmap()

		graphicsScene = QtWidgets.QGraphicsScene()
		pixmapItem = graphicsScene.addPixmap( pixmap )
		pixmapItem.setVisible( True )

		effect = QtWidgets.QGraphicsOpacityEffect()
		effect.setOpacity( 0.4 )
		pixmapItem.setGraphicsEffect( effect )
		pixmapItem.setShapeMode( pixmapItem.BoundingRectShape )

		graphicsView = QtWidgets.QGraphicsView()
		graphicsView.setScene( graphicsScene )

		image = QtGui.QImage( pixmap.width(), pixmap.height(), QtGui.QImage.Format_ARGB32_Premultiplied )
		image.fill( 0 )

		painter = QtGui.QPainter( image )
		graphicsView.render(
			painter,
			QtCore.QRectF(),
			QtCore.QRect(
				graphicsView.mapFromScene( pixmapItem.boundingRect().topLeft() ),
				graphicsView.mapFromScene( pixmapItem.boundingRect().bottomRight() )
			)
		)
		del painter # must delete painter before image

		return QtGui.QPixmap( image )

	@staticmethod
	def _qtPixmapFromImagePrimitive( image ) :

		image = image.copy()
		IECoreImage.ColorAlgo.transformImage( image, "linear", "sRGB" )

		y = image["Y"] if "Y" in image else None
		r = image["R"] if "R" in image else None
		g = image["G"] if "G" in image else None
		b = image["B"] if "B" in image else None

		if r and g and b :
			channels = [ r, g, b ]
		elif y :
			channels = [ y, y, y ]
		else :
			raise ValueError( "Expected RGB or Y channels in image" )

		if "A" in image :
			channels.reverse()
			channels.append( image["A"] )
			format = QtGui.QImage.Format_ARGB32_Premultiplied
		else :
			format = QtGui.QImage.Format_RGB888

		interleaved = IECore.DataInterleaveOp()(
			data = IECore.ObjectVector( channels ),
			targetType = IECore.UCharVectorData.staticTypeId(),
		)

		imageSize = image.dataWindow.size() + imath.V2i( 1 )

		s = interleaved.toString()
		image = QtGui.QImage( s, imageSize.x, imageSize.y, format )
		# The image is referencing the data we provided directly (s), and
		# expects us to keep it alive as long as the image/pixmap is
		# used. Since we don't want to do that, we make a deep copy of
		# the image so we can dispose of s.
		image = image.copy()

		pixmap = QtGui.QPixmap( image )

		return pixmap

	__pixmapCache = None
	@classmethod
	def _qtPixmapCache( cls ) :

		if cls.__pixmapCache is None :
			cacheSize = int( os.environ.get( "GAFFERUI_IMAGECACHE_MEMORY", 100 ) ) * 1024 * 1024
			cls.__pixmapCache = IECore.LRUCache( cls.__cacheGetter, cacheSize )

		return cls.__pixmapCache

	@classmethod
	def _qtPixmapFromFile( cls, fileName ) :

		return cls._qtPixmapCache().get( fileName )

	__imageSearchPaths = IECore.SearchPath( os.environ.get( "GAFFERUI_IMAGE_PATHS", "" ) )
	@classmethod
	def __cacheGetter( cls, fileName ) :

		resolvedFileName = cls.__imageSearchPaths.find( fileName )
		if not resolvedFileName :
			raise Exception( "Unable to find file \"%s\"" % fileName )

		reader = IECore.Reader.create( resolvedFileName )

		image = reader.read()
		if not isinstance( image, IECoreImage.ImagePrimitive ) :
			raise Exception( "File \"%s\" is not an image file" % resolvedFileName )

		result = cls._qtPixmapFromImagePrimitive( image )

		cost = result.width() * result.height() * ( 4 if result.hasAlpha() else 3 )

		return ( result, cost )
