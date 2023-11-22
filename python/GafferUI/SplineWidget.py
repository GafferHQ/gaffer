##########################################################################
#
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2012-2013, Image Engine Design Inc. All rights reserved.
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

import enum

import imath

import IECore

import Gaffer
import GafferUI

from Qt import QtCore
from Qt import QtGui
from Qt import QtWidgets

## This Widget simply displays an IECore.Spline object.
class SplineWidget( GafferUI.Widget ) :

	DrawMode = enum.Enum( "DrawMode", [ "Invalid", "Ramp", "Splines" ] )

	def __init__( self, spline=None, drawMode=DrawMode.Splines, **kw ) :

		# using QFrame rather than QWidget because it supports computing the contentsRect() based on
		# the stylesheet.
		GafferUI.Widget.__init__( self, QtWidgets.QFrame(), **kw )

		self._qtWidget().setSizePolicy( QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding )

		self.setDrawMode( drawMode )

		if spline==None :
			spline = IECore.Splineff(
				IECore.CubicBasisf.catmullRom(),
				(
					( 0, 0 ),
					( 0, 0 ),
					( 1, 1 ),
					( 1, 1 ),
				)
			)

		self.setSpline( spline )

		self._qtWidget().paintEvent = Gaffer.WeakMethod( self.__paintEvent )

	def setSpline( self, spline ) :

		try :
			if spline==self.__spline :
				return
		except :
			pass

		self.__spline = spline
		self.__splinesToDraw = None
		self.__gradientToDraw = None
		self._qtWidget().update()

	def getSpline( self ) :

		return self.__spline

	def setDrawMode( self, drawMode ) :

		try :
			if drawMode==self.__drawMode :
				return
		except :
			pass

		self.__drawMode = drawMode
		self._qtWidget().update()

	def getDrawMode( self ) :

		return self.__drawMode

	def __paintEvent( self, event ) :

		painter = QtGui.QPainter( self._qtWidget() )
		painter.setRenderHint( QtGui.QPainter.Antialiasing )

		o = QtWidgets.QStyleOption()
		o.initFrom( self._qtWidget() )
		self._qtWidget().style().drawPrimitive( QtWidgets.QStyle.PE_Widget, o, painter, self._qtWidget() )

		if self.__drawMode == self.DrawMode.Ramp :
			self.__paintRamp( painter )
		elif self.__drawMode == self.DrawMode.Splines :
			self.__paintSplines( painter )

	def __paintRamp( self, painter ) :

		numStops = 500
		if self.__gradientToDraw is None :

			self.__gradientToDraw = QtGui.QImage( QtCore.QSize( numStops, 1 ), QtGui.QImage.Format.Format_RGB32 )

			displayTransform = self.displayTransform()

			for i in range( 0, numStops ) :
				t = float( i + 0.5 ) / numStops
				c = self.__spline( t )
				if isinstance( c, float ) :
					c = imath.Color3f( c, c, c )
				else :
					c = imath.Color3f( c[0], c[1], c[2] )

				c = displayTransform( c )
				self.__gradientToDraw.setPixel( i, 0, self._qtColor( c ).rgb() )

		painter.drawImage( self._qtWidget().contentsRect(), self.__gradientToDraw )

	def __paintSplines( self, painter ) :

		# update the evaluation of our splines if necessary
		numPoints = 200
		if not self.__splinesToDraw :
			self.__splinesToDraw = []
			if isinstance( self.__spline, IECore.Splineff ) :
				spline = IECore.Struct()
				spline.color = imath.Color3f( 1 )
				spline.path = QtGui.QPainterPath()
				for i in range( 0, numPoints ) :
					t = float( i ) / ( numPoints - 1 )
					c = self.__spline( t )
					if i==0 :
						spline.path.moveTo( t, c )
					else :
						spline.path.lineTo( t, c )
				self.__splinesToDraw.append( spline )
			else :
				for i in range( 0, self.__spline( 0 ).dimensions() ) :
					spline = IECore.Struct()
					if i==3 :
						spline.color = imath.Color3f( 1 )
					else :
						c = imath.Color3f( 0 )
						c[i] = 1
						spline.color = c
					spline.path = QtGui.QPainterPath()
					self.__splinesToDraw.append( spline )

				for i in range( 0, numPoints ) :
					t = float( i ) / ( numPoints - 1 )
					c = self.__spline( t )
					for j in range( 0, c.dimensions() ) :
						if i == 0 :
							self.__splinesToDraw[j].path.moveTo( t, c[j] )
						else :
							self.__splinesToDraw[j].path.lineTo( t, c[j] )

			self.__splineBound = QtCore.QRectF( 0, 0, 1, 1 )
			for s in self.__splinesToDraw :
				self.__splineBound = self.__splineBound.united( s.path.controlPointRect() )

		# Set view transform
		rect = self._qtWidget().contentsRect()
		transform = QtGui.QTransform()
		if self.__splineBound.width() :
			transform.translate( rect.x(), 0 )
			transform.scale( rect.width() / self.__splineBound.width(), 1 )
		if self.__splineBound.height() :
			transform.translate( 0, rect.y() + rect.height() )
			transform.scale( 1, -rect.height() / self.__splineBound.height() )
			transform.translate( 0, -self.__splineBound.top() )

		painter.setTransform( transform )

		painter.setCompositionMode( QtGui.QPainter.CompositionMode.CompositionMode_SourceOver )

		# Draw axis lines at y=0 and y=1
		if self.__splineBound.top() < 0:
			pen = QtGui.QPen( self._qtColor( imath.Color3f( 0.2 ) ) )
			pen.setCosmetic( True )
			painter.setPen( pen )
			zeroLine = QtGui.QPainterPath()
			zeroLine.moveTo( 0, 0 )
			zeroLine.lineTo( 1, 0 )
			painter.drawPath( zeroLine )

		if self.__splineBound.bottom() > 1:
			pen = QtGui.QPen( self._qtColor( imath.Color3f( 0.4 ) ) )
			pen.setCosmetic( True )
			painter.setPen( pen )
			oneLine = QtGui.QPainterPath()
			oneLine.moveTo( 0, 1 )
			oneLine.lineTo( 1, 1 )
			painter.drawPath( oneLine )

		# draw the splines
		painter.setCompositionMode( QtGui.QPainter.CompositionMode.CompositionMode_Plus )
		for s in self.__splinesToDraw :
			pen = QtGui.QPen( self._qtColor( s.color ) )
			pen.setCosmetic( True )
			painter.setPen( pen )
			painter.drawPath( s.path )

	def _displayTransformChanged( self ) :

		GafferUI.Widget._displayTransformChanged( self )

		self.__gradientToDraw = None
		self._qtWidget().update()
