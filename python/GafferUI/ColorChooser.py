##########################################################################
#
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
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

import collections
import enum
import functools
import math
import sys
import imath
import enum

import IECore

import Gaffer
import GafferUI

from Qt import QtCore
from Qt import QtGui
from Qt import QtWidgets

__tmiToRGBMatrix = imath.M33f(
	-1.0 / 2.0, 0.0, 1.0 / 2.0,
	1.0 / 3.0, -2.0 / 3.0, 1.0 / 3.0,
	1.0, 1.0, 1.0
)
__rgb2tmiMatrix = __tmiToRGBMatrix.inverse()

def _tmiToRGB( c ) :
	rgb = imath.V3f( c.r, c.g, c.b ) * __tmiToRGBMatrix

	result = c.__class__( c )
	result.r = rgb.x
	result.g = rgb.y
	result.b = rgb.z

	return result

def _rgbToTMI( c ) :
	tmi = imath.V3f( c.r, c.g, c.b ) * __rgb2tmiMatrix

	result = c.__class__( c )
	result.r = tmi.x
	result.g = tmi.y
	result.b = tmi.z

	return result

__Range = collections.namedtuple( "__Range", [ "min", "max", "hardMin", "hardMax" ] )

_ranges = {
	# We don't _really_ want to allow negative values for RGB, but
	# they can arise from TMI values in the allowed TMI range. It's
	# better to allow these to be displayed (as an "out of range"
	# triangle in the sliders) than to show inconsistent values between
	# components.
	"r" : __Range( 0, 1, -sys.float_info.max, sys.float_info.max ),
	"g" : __Range( 0, 1, -sys.float_info.max, sys.float_info.max ),
	"b" : __Range( 0, 1, -sys.float_info.max, sys.float_info.max ),
	"a" : __Range( 0, 1, 0, 1 ),
	"h" : __Range( 0, 1, 0, 1 ),
	"s" : __Range( 0, 1, 0, 1 ),
	# As above, we're allowing out-of-regular-range values here too,
	# because they can arise when authoring in-range values via RGB.
	"v" : __Range( 0, 1, -sys.float_info.max, sys.float_info.max ),
	"t" : __Range( -1, 1, -sys.float_info.max, sys.float_info.max ),
	"m" : __Range( -1, 1, -sys.float_info.max, sys.float_info.max ),
	"i" : __Range( 0, 1, -sys.float_info.max, sys.float_info.max ),
}

def _drawIndicator( painter, position ) :

	painter.setBrush( QtCore.Qt.transparent )

	pen = QtGui.QPen( QtGui.QColor( 0, 0, 0, 255 ) )
	pen.setWidth( 1 )
	painter.setPen( pen )

	painter.drawEllipse( position, 4.5, 4.5 )

	pen.setColor( QtGui.QColor( 255, 255, 255, 255 ) )
	painter.setPen( pen )
	painter.drawEllipse( position, 3.5, 3.5 )

# A custom slider for drawing the backgrounds.
class _ComponentSlider( GafferUI.Slider ) :

	def __init__( self, color, component, dynamicBackground = True, **kw ) :

		GafferUI.Slider.__init__(
			self, 0.0,
			min = _ranges[component].min, max = _ranges[component].max,
			hardMin = _ranges[component].hardMin, hardMax = _ranges[component].hardMax,
			**kw
		)

		self.color = color
		self.component = component
		self.__dynamicBackground = dynamicBackground
		self.__gradientToDraw = None
		self.__size = self.size()

	# Sets the slider color in RGB space for RGBA channels,
	# HSV space for HSV channels and TMI space for TMI channels.
	def setColor( self, color ) :

		if (
			( self.__dynamicBackground and color != self.color ) or
			( not self.__dynamicBackground and self.component == "s" )
		) :
			self.__gradientToDraw = None
		self.color = color
		self._qtWidget().update()

	def getColor( self ) :

		return self.color

	def setDynamicBackground( self, dynamicBackground ) :

		self.__dynamicBackground = dynamicBackground
		self.__gradientToDraw = None
		self._qtWidget().update()

	def getDynamicBackground( self ) :

		return self.__dynamicBackground

	def _drawBackground( self, painter ) :

		size = self.size()

		if self.__gradientToDraw is None or size != self.__size :
			self.__gradientToDraw = QtGui.QLinearGradient( 0, 0, size.x, 0 )

			displayTransform = self.displayTransform()

			if self.component == "a" :
				c1 = imath.Color3f( 0 )
				c2 = imath.Color3f( 1 )
			else :
				if self.__dynamicBackground :
					c1 = imath.Color3f( self.color[0], self.color[1], self.color[2] )
				elif self.component in "rgbvi" :
					c1 = imath.Color3f( 0 )
				elif self.component == "h" :
					c1 = imath.Color3f( 0, 1, 1 )
				elif self.component == "s" :
					c1 = imath.Color3f( self.color[0], 0, 1 )
				elif self.component in "tm" :
					c1 = imath.Color3f( 0, 0, 0.5 )
				c2 = imath.Color3f( c1 )
				a = { "r" : 0, "g" : 1, "b" : 2, "h" : 0, "s" : 1, "v": 2, "t" : 0, "m" : 1, "i" : 2 }[self.component]
				c1[a] = -1 if self.component in "tm" else 0
				c2[a] = 1

			numStops = max( 2, size.x // 2 )
			for i in range( 0, numStops ) :

				t = float( i ) / (numStops-1)
				c = c1 + (c2-c1) * t
				if self.component in "hsv" :
					c = c.hsv2rgb()
				elif self.component in "tmi" :
					c = _tmiToRGB( c )

				self.__gradientToDraw.setColorAt( t, self._qtColor( displayTransform( c ) ) )

		brush = QtGui.QBrush( self.__gradientToDraw )
		painter.fillRect( 0, 0, size.x, size.y, brush )
		self.__size = size

	def _drawValue( self, painter, value, position, state ) :

		size = self.size()

		if position >= 0 and position <= size.x :
			_drawIndicator( painter, QtCore.QPoint( position, size.y / 2 ) )
			return

		pen = QtGui.QPen( QtGui.QColor( 0, 0, 0, 255 ) )
		pen.setWidth( 1 )
		painter.setPen( pen )
		painter.setBrush( QtGui.QColor( 255, 255, 255, 255 ) )

		if position < 0 :
			painter.drawPolygon(
				QtGui.QPolygonF(
					[
						QtCore.QPointF( 8, 4 ),
						QtCore.QPointF( 8, size.y - 4 ),
						QtCore.QPointF( 2, size.y / 2 ),
					]
				)
			)
		elif position > size.x :
			painter.drawPolygon(
				QtGui.QPolygonF(
					[
						QtCore.QPointF( size.x - 8, 4 ),
						QtCore.QPointF( size.x - 8, size.y - 4 ),
						QtCore.QPointF( size.x - 2, size.y / 2 ),
					]
				)
			)

	def _displayTransformChanged( self ) :

		GafferUI.Slider._displayTransformChanged( self )
		self.__gradientToDraw = None
		self._qtWidget().update()

class _ColorField( GafferUI.Widget ) :

	__DragConstraints = enum.Flag( "__DragConstraints", [ "X", "Y" ] )

	def __init__( self, color = imath.Color3f( 1.0 ), staticComponent = "v", dynamicBackground = True, **kw ) :

		GafferUI.Widget.__init__( self, QtWidgets.QWidget(), **kw )

		self._qtWidget().paintEvent = Gaffer.WeakMethod( self.__paintEvent )

		self.buttonPressSignal().connect( Gaffer.WeakMethod( self.__buttonPress ) )
		self.buttonReleaseSignal().connect( Gaffer.WeakMethod( self.__buttonRelease ) )
		self.dragBeginSignal().connect( Gaffer.WeakMethod( self.__dragBegin ) )
		self.dragEnterSignal().connect( Gaffer.WeakMethod( self.__dragEnter ) )
		self.dragMoveSignal().connect( Gaffer.WeakMethod( self.__dragMove ) )
		self.dragEndSignal().connect( Gaffer.WeakMethod( self.__dragEnd ) )

		self.__valueChangedSignal = Gaffer.Signals.Signal2()

		self.__minDraggableHueRadius = 4.0

		self.__color = color
		self.__staticComponent = staticComponent
		self.__colorFieldToDraw = None
		self.__dragConstraints = None
		self.__constraintPosition = None
		self.__constraintPath = None
		self.setColor( color, staticComponent )

		self.setDynamicBackground( dynamicBackground )

	# Sets the color and the static component. `color` is in
	# RGB space for RGB static components, HSV space for
	# HSV static components and TMI space for TMI components.
	def setColor( self, color, staticComponent ) :

		self.__setColorInternal( color, staticComponent, GafferUI.Slider.ValueChangedReason.SetValues )

	# Returns a tuple of the color and static component.
	def getColor( self ) :

		return self.__color, self.__staticComponent

	def setDynamicBackground( self, dynamicBackground ) :

		self.__dynamicBackground = dynamicBackground
		self.__colorFieldToDraw = None
		self._qtWidget().update()

	def getDynamicBackground( self ) :

		return self.__dynamicBackground

	## A signal emitted whenever a value has been changed. Slots should
	# have the signature slot( _ColorField, GafferUI.Slider.ValueChangedReason )
	def valueChangedSignal( self ) :

		return self.__valueChangedSignal

	# Returns a tuple consisting of the components that will be used for the X and Y
	# axes for the color field.
	def xyAxes( self ) :
		xAxis = { "r": "g", "g": "r", "b": "r", "h": "s", "s": "h", "v": "h", "t": "m", "m": "t", "i": "t" }[self.__staticComponent]
		yAxis = { "r": "b", "g": "b", "b": "g", "h": "v", "s": "v", "v": "s", "t": "i", "m": "i", "i": "m" }[self.__staticComponent]

		return xAxis, yAxis

	def _displayTransformChanged( self ) :

		GafferUI.Widget._displayTransformChanged( self )
		self.__colorFieldToDraw = None
		self._qtWidget().update()

	def __setColorInternal( self, color, staticComponent, reason ) :

		dragBeginOrEnd = reason in ( GafferUI.Slider.ValueChangedReason.DragBegin, GafferUI.Slider.ValueChangedReason.DragEnd )
		if self.__color == color and self.__staticComponent == staticComponent and not dragBeginOrEnd :
			return

		zIndex = self.__zIndex()
		if (
			staticComponent != self.__staticComponent or
			( self.__dynamicBackground and color[zIndex] != self.__color[zIndex] ) or
			( not self.__dynamicBackground and staticComponent == "h" )
		) :
			self.__colorFieldToDraw = None

		self.__color = color
		self.__staticComponent = staticComponent

		self._qtWidget().update()

		self.valueChangedSignal()( self, reason )

	def __xyIndices( self ) :

		xIndex = { "r": 1, "g": 0, "b": 0, "h": 1, "s": 0, "v": 0, "t": 1, "m": 0, "i": 0 }[self.__staticComponent]
		yIndex = { "r": 2, "g": 2, "b": 1, "h": 2, "s": 2, "v": 1, "t": 2, "m": 2, "i": 1 }[self.__staticComponent]

		return xIndex, yIndex

	def __zIndex( self ) :
		zIndex = { "r": 0, "g": 1, "b": 2, "h": 0, "s": 1, "v": 2, "t": 0, "m": 1, "i": 2 }[self.__staticComponent]

		return zIndex

	def __useWheel( self ) :

		return self.__staticComponent in "sv"

	def __cartesianToPolar( self, p, center, maxRadius ) :

		p = p - center
		radius = p.length()
		theta = math.atan2( p.y, p.x )
		twoPi = math.pi * 2.0
		theta = theta if theta > 0 else twoPi + theta

		return imath.V2f( theta / twoPi, radius / maxRadius )

	def __polarToCartesian( self, p, center, maxRadius ) :

		a = p.x * math.pi * 2.0
		return imath.V2f(
			math.cos( a ) * p.y * maxRadius + center.x,
			math.sin( a ) * p.y * maxRadius + center.y
		)

	def __colorToPosition( self, color ) :

		xIndex, yIndex = self.__xyIndices()
		color = imath.V2f( color[xIndex], color[yIndex] )

		if self.__useWheel() :
			theta = 2 * math.pi * color.x
			return imath.V2f( self.bound().size() ) * 0.5 * (
				imath.V2f( color.y * math.cos( theta ), -color.y * math.sin( theta ) ) + imath.V2f( 1.0 )
			)

		xComponent, yComponent = self.xyAxes()
		minC = imath.V2f( _ranges[xComponent].min, _ranges[yComponent].min )
		maxC = imath.V2f( _ranges[xComponent].max, _ranges[yComponent].max )

		p = ( ( color - minC ) / ( maxC - minC ) ) * self.bound().size()
		p.y = self.bound().size().y - p.y

		return p

	def __positionToColor( self, position ) :

		xIndex, yIndex = self.__xyIndices()

		c, staticComponent = self.getColor()
		c = c.__class__( c )

		size = self.bound().size()

		xComponent, yComponent = self.xyAxes()

		if self.__useWheel() :
			halfSize = imath.V2f( size ) * 0.5
			p = self.__cartesianToPolar( imath.V2f( position.x, size.y - position.y ), halfSize, halfSize.x )
			if p.y > 0 :
				c[xIndex] = p.x
			c[yIndex] = p.y
		else :
			c[xIndex] = ( position.x / float( size.x ) ) * ( _ranges[xComponent].max - _ranges[xComponent].min ) + _ranges[xComponent].min
			c[yIndex] = ( 1.0 - ( position.y / float( size.y ) ) ) * ( _ranges[yComponent].max - _ranges[yComponent].min ) + _ranges[yComponent].min

		return c

	def __clampPosition( self, position ) :

		size = self.bound().size()
		if self.__useWheel() :
			halfSize = imath.V2f( size ) * 0.5
			centeredPosition = position - halfSize
			radiusOriginal = centeredPosition.length()

			if radiusOriginal == 0 :
				return halfSize

			return halfSize + ( centeredPosition / imath.V2f( radiusOriginal )  ) * min( radiusOriginal, halfSize.x )

		return imath.V2f( min( size.x, max( 0.0, position.x ) ), min( size.y, max( 0.0, position.y ) ) )

	def __constrainPosition( self, position ) :

		if self.__dragConstraints is None :
			return position

		assert( bool( self.__dragConstraints ) )

		if not self.__useWheel() :
			# Determine if `position` is closer to the horizontal line going through
			# `__constraintPosition` or the vertical line. The distance to the
			# horizontal line is the vertical difference from `position` to
			# `__constraintPosition`. The distance to the vertical line is the
			# horizontal difference.
			delta = self.__constraintPosition - position
			delta.x = abs( delta.x )
			delta.y = abs( delta.y )

			if delta.y < delta.x and (
				self.__DragConstraints.X in self.__dragConstraints or not self.__DragConstraints.Y in self.__dragConstraints
			) :
				# Constrain to horizontal line
				return imath.V2f( position.x, self.__constraintPosition.y )
			# Constrain to vertical line
			return imath.V2f( self.__constraintPosition.x, position.y )

		center = imath.V2f( self.bound().size() ) * 0.5
		distanceToCenter = ( position - center ).length()

		polarConstraintPosition = self.__cartesianToPolar( self.__constraintPosition, center, center.x )

		# Extend line segment past the widget for distance check
		extended = self.__polarToCartesian( imath.V2f( polarConstraintPosition.x, 2.0 ), center, center.x )

		radiusLine = imath.Line3f( imath.V3f( center.x, center.y, 0 ), imath.V3f( extended.x, extended.y, 0 ) )
		position3 = imath.V3f( position.x, position.y, 0 )
		closestPointOnRadiusLine = radiusLine.closestPointTo( position3 )
		distanceToRadiusLine = ( closestPointOnRadiusLine - position3 ).length()

		constraintRadius = polarConstraintPosition.y * center.x
		distanceToCircle = abs( distanceToCenter - constraintRadius )

		dot = ( position - center ).dot( self.__constraintPosition - center )

		polarPosition = self.__cartesianToPolar( position, center, center.x )

		if self.__DragConstraints.X in self.__dragConstraints :
			if (
				abs( distanceToCircle ) < distanceToRadiusLine or
				( dot < 0 and distanceToCenter > constraintRadius * 0.5 )
			) :
				# If we're closer to the circle than the radius line, or we're behind the center
				# (from the point of view of `__constraintPosition`) and reasonably far from the center,
				# constrain to the circle.
				return self.__polarToCartesian(
					imath.V2f( polarPosition.x, polarConstraintPosition.y ), center, center.x
				)

		if dot < 0 :
			# If we're not constrained to the circle, but "behind" the center, snap to the center.
			return center

		# If no constraints are enforced yet, constrain to the radius line.
		polarClosestPoint = self.__cartesianToPolar(
			imath.V2f( closestPointOnRadiusLine.x, closestPointOnRadiusLine.y ), center, center.x
		)
		return self.__polarToCartesian(
			imath.V2f( polarConstraintPosition.x, polarClosestPoint.y ),
			center,
			center.x
		)

	def __setupConstraints( self, event ) :

		c, staticComponent = self.getColor()

		self.__constraintPosition = self.__colorToPosition( c )

		center = imath.V2f( self.bound().size() ) * 0.5

		# Set `__dragConstraints` with `__constraintPosition` based on actual color
		self.__dragConstraints = None
		if event.modifiers == GafferUI.ButtonEvent.Modifiers.Control :
			if not self.__useWheel() :
				self.__dragConstraints = self.__DragConstraints.X | self.__DragConstraints.Y
			else :
				self.__dragConstraints = self.__DragConstraints.Y

				center = imath.V2f( self.bound().size() ) * 0.5
				if ( self.__constraintPosition - center ).length() > self.__minDraggableHueRadius :
					self.__dragConstraints |= self.__DragConstraints.X
				else :
					# Adjust `__constraintPosition` to be along the hue angle, slightly off center. This
					# allows the radius line constraint to work properly.
					polarPosition = self.__cartesianToPolar(
						self.__colorToPosition( imath.Color3f( c.r, 1.0, 1.0 ) ), center, center.x
					)
					self.__constraintPosition = self.__polarToCartesian( imath.V2f( polarPosition.x, 1.0 / center.x ), center, center.x )

	def __buttonPress( self, widget, event ) :

		if event.buttons != GafferUI.ButtonEvent.Buttons.Left :
			return False

		center = imath.V2f( self.bound().size() ) * 0.5
		if ( imath.V2f( event.line.p0.x, event.line.p0.y ) - center ).length() > center.x :
			return False

		self.__setupConstraints( event )

		self.__constraintPath = None

		c, staticComponent = self.getColor()

		self.__setColorInternal(
			self.__positionToColor(
				self.__clampPosition( self.__constrainPosition( imath.V2f( event.line.p0.x, event.line.p0.y ) ) )
			),
			staticComponent,
			GafferUI.Slider.ValueChangedReason.Click
		)

		return True

	def __buttonRelease( self, widget, event ) :

		if event.buttons == GafferUI.ButtonEvent.Buttons.Left :
			return False

		self.__constraintPosition = None
		self.__dragConstraints = None
		self.__constraintPath = None

		self._qtWidget().update()

	def __dragBegin( self, widget, event ) :

		if event.buttons == GafferUI.ButtonEvent.Buttons.Left :
			self.__constraintPath = None

			c, staticComponent = self.getColor()
			self.__setColorInternal(
				self.__positionToColor(
					self.__clampPosition( self.__constrainPosition( imath.V2f( event.line.p0.x, event.line.p0.y ) ) )
				),
				staticComponent,
				GafferUI.Slider.ValueChangedReason.DragBegin
			)
			return IECore.NullObject.defaultNullObject()

		return None

	def __dragEnter( self, widget, event ) :

		if event.sourceWidget is self :
			return True

		return False

	def __dragMove( self, widget, event ) :

		c, staticComponent = self.getColor()

		if self.__dragConstraints is None and event.modifiers == GafferUI.ButtonEvent.Modifiers.Control :
			self.__setupConstraints( event )
			self.__constraintPath = None
		elif self.__dragConstraints is not None and event.modifiers != GafferUI.ButtonEvent.Modifiers.Control :
			self.__constraintPath = None
			self.__dragConstraints = None


		self.__setColorInternal(
			self.__positionToColor(
				self.__clampPosition( self.__constrainPosition( imath.V2f( event.line.p0.x, event.line.p0.y ) ) )
			),
			staticComponent,
			GafferUI.Slider.ValueChangedReason.DragMove
		)
		return True

	def __dragEnd( self, widget, event ) :

		c, staticComponent = self.getColor()

		self.__setColorInternal(
			self.__positionToColor(
				self.__clampPosition( self.__constrainPosition( imath.V2f( event.line.p0.x, event.line.p0.y ) ) )
			),
			staticComponent,
			GafferUI.Slider.ValueChangedReason.DragEnd
		)

		self.__constraintPosition = None
		self.__dragConstraints = None
		self.__constraintPath = None

		return True

	def __drawBackground( self, painter ) :

		numStops = 50
		if self.__colorFieldToDraw is None :
			self.__colorFieldToDraw = QtGui.QImage( QtCore.QSize( numStops, numStops ), QtGui.QImage.Format.Format_RGB32 )

			displayTransform = self.displayTransform()

			xIndex, yIndex = self.__xyIndices()
			zIndex = self.__zIndex()

			c = imath.Color3f()
			if self.__dynamicBackground or self.__staticComponent == "h" :
				c[zIndex] = self.__color[zIndex]
			elif self.__staticComponent in "rgbtm" :
				c[zIndex] = 0.0
			elif self.__staticComponent in "sv" :
				c[zIndex] = 1.0
			elif self.__staticComponent == "i" :
				c[zIndex] = 0.5

			ColorSpace = enum.Enum( "ColorSpace", [ "RGB", "HSV", "TMI" ] )
			if self.__staticComponent in "rgb" :
				colorSpace = ColorSpace.RGB
			elif self.__staticComponent in "hsv" :
				colorSpace = ColorSpace.HSV
			else :
				colorSpace = ColorSpace.TMI

			xComponent, yComponent = self.xyAxes()

			if self.__useWheel() :
				maxRadius = float( numStops - 1 ) * 0.5
				for x in range( 0, numStops ) :
					for y in range( 0, numStops ) :
						p = self.__cartesianToPolar( imath.V2f( x, y ), imath.V2f( maxRadius ), maxRadius )

						c[xIndex] = p.x
						c[yIndex] = p.y

						cRGB = c.hsv2rgb()
						cRGB = displayTransform( cRGB )
						self.__colorFieldToDraw.setPixel( x, numStops - 1 - y, self._qtColor( cRGB ).rgb() )
			else :
				for x in range( 0, numStops ) :
					tx = float( x ) / ( numStops - 1 )
					c[xIndex] = _ranges[xComponent].min + ( _ranges[xComponent].max - _ranges[xComponent].min ) * tx

					for y in range( 0, numStops ) :
						ty = float( y ) / ( numStops - 1 )

						c[yIndex] = _ranges[yComponent].min + ( _ranges[yComponent].max - _ranges[yComponent].min ) * ty

						if colorSpace == ColorSpace.RGB :
							cRGB = c
						elif colorSpace == ColorSpace.HSV :
							cRGB = c.hsv2rgb()
						else :
							cRGB = _tmiToRGB( c )

						cRGB = displayTransform( cRGB )
						self.__colorFieldToDraw.setPixel( x, numStops - 1 - y, self._qtColor( cRGB ).rgb() )

		painter.drawImage( self._qtWidget().contentsRect(), self.__colorFieldToDraw )

		if self.__constraintPath is None and self.__dragConstraints is not None and self.__constraintPosition is not None :
			path = QtGui.QPainterPath()

			if self.__useWheel() :
				center = imath.V2f( self.bound().size() ) * 0.5

				if self.__DragConstraints.X in self.__dragConstraints :
					radius = ( self.__constraintPosition - center ).length()
					path.addEllipse( QtCore.QPoint( center.x, center.y ), radius, radius )

				if self.__DragConstraints.Y in self.__dragConstraints :
					radiusEnd = center + ( self.__constraintPosition - center ).normalized() * center.x

					path.moveTo( center.x, center.y )
					path.lineTo( radiusEnd.x, radiusEnd.y )
			else :
				if self.__dragConstraints.X in self.__dragConstraints :
					path.moveTo( 0, self.__constraintPosition.y )
					path.lineTo( self.bound().max().x, self.__constraintPosition.y )
				if self.__DragConstraints.Y in self.__dragConstraints :
					path.moveTo( self.__constraintPosition.x, 0 )
					path.lineTo( self.__constraintPosition.x, self.bound().max().y )

			strokedPath = QtGui.QPainterPathStroker()
			strokedPath.setWidth( 2 )

			self.__constraintPath = strokedPath.createStroke( path )

		if self.__constraintPath is not None :
			pen = QtGui.QPen( QtGui.QColor( 0, 0, 0, 60 ) )
			pen.setWidth( 1 )
			painter.setPen( pen )
			painter.setBrush( QtGui.QBrush( QtGui.QColor( 255, 255, 255, 60 ) ) )

			painter.drawPath( self.__constraintPath )

	def __drawValue( self, painter ) :

		position = self.__colorToPosition( self.__color )

		size = self.size()

		# Use a dot when both axes are a valid value.
		positionClamped = self.__clampPosition( position )
		delta = position - positionClamped

		if abs( delta.x ) < 1e-3 and abs( delta.y ) < 1e-3 :
			_drawIndicator( painter, QtCore.QPoint( position.x, position.y ) )
			return

		triangleWidth = 5.0
		triangleSpacing = 2.0

		pen = QtGui.QPen( QtGui.QColor( 0, 0, 0, 255 ) )
		pen.setWidth( 1 )
		painter.setPen( pen )

		color = QtGui.QColor( 255, 255, 255, 255 )

		painter.setBrush( QtGui.QBrush( color ) )

		offset = imath.V2f( 0 )

		if self.__useWheel() :
			rotation = math.atan2( delta.y, delta.x )
		else :
			# Use a corner triangle if both axes are invalid values.
			if position.x > size.x and position.y < 0 :
				rotation = math.radians( -45.0 )  # Triangle pointing to the top-right
				offset = imath.V2f( -triangleSpacing, triangleSpacing )
			elif position.x < 0 and position.y < 0 :
				rotation = math.radians( -135.0 )  # Top-left
				offset = imath.V2f( triangleSpacing, triangleSpacing )
			elif position.x < 0 and position.y > size.y :
				rotation = math.radians( -225.0 )  # Bottom-left
				offset = imath.V2f( triangleSpacing, -triangleSpacing )
			elif position.x > size.x and position.y > size.y :
				rotation = math.radians( -315.0 )  # Bottom-right
				offset = imath.V2f( -triangleSpacing, -triangleSpacing )

			# Finally, use a top / left / bottom / right triangle if one axis is an invalid value.
			elif position.y < 0 :
				rotation = math.radians( -90.0 )  # Top
				offset = imath.V2f( 0, triangleSpacing )
				# Clamp it in more to account for the triangle size
				positionClamped.x = min( max( triangleWidth + triangleSpacing, positionClamped.x ), size.x - triangleWidth - triangleSpacing )
			elif position.x < 0 :
				rotation = math.radians( -180.0 )  # Left
				offset = imath.V2f( triangleSpacing, 0 )
				positionClamped.y = min( max( triangleWidth + triangleSpacing, positionClamped.y ), size.y - triangleWidth - triangleSpacing )
			elif position.y > size.y :
				rotation = math.radians( -270.0 )  # Bottom
				offset = imath.V2f( 0, -triangleSpacing )
				positionClamped.x = min( max( triangleWidth + triangleSpacing, positionClamped.x ), size.x - triangleWidth - triangleSpacing )
			else :
				rotation = 0.0  # Right
				offset = imath.V2f( -triangleSpacing, 0 )
				positionClamped.y = min( max( triangleWidth + triangleSpacing, positionClamped.y ), size.y - triangleWidth - triangleSpacing )

		rightPoints = [ imath.V2f( 0, 0 ), imath.V2f( -6, triangleWidth ), imath.V2f( -6, -triangleWidth ) ]
		xform = imath.M33f().rotate( rotation ) * imath.M33f().translate(
			positionClamped + offset
		)
		points = [ p * xform for p in rightPoints ]
		# Transforming the points introduces slight precision errors which can be noticeable
		# when drawing polygons. Round the values to compensate.
		points = [ QtCore.QPoint( round( p.x ), round( p.y ) ) for p in points ]

		painter.drawConvexPolygon( points )

	def __paintEvent( self, event ) :

		painter = QtGui.QPainter( self._qtWidget() )
		painter.setRenderHint( QtGui.QPainter.Antialiasing )
		painter.setRenderHint( QtGui.QPainter.SmoothPixmapTransform)

		if self.__useWheel() :
			mask = QtGui.QPainterPath()
			mask.addEllipse( 0, 0, self.size().x, self.size().y )
			painter.setClipPath( mask )

		self.__drawBackground( painter )

		self.__drawValue( painter )

class _ColorFieldRowLayout( QtWidgets.QLayout ) :

	def __init__( self ) :

		QtWidgets.QLayout.__init__( self, None )

		# No spacing between color field and sliders so the active component icons
		# line up against the color field.
		self.setSpacing( 0 )
		self.__minColorFieldSize = 66  # Height of 3 sliders

		self.__items = []

	def addItem( self, item ) :

		self.__items.append( item )

	def count( self ) :

		return len( self.__items )

	def expandingDirections( self ) :

		return QtCore.Qt.Orientations( QtCore.Qt.Orientation( 0 ) )

	def itemAt( self, index ) :

		return self.__items[index] if index >= 0 and index < len( self.__items ) else None

	def takeAt( self, index ) :

		return self.__items.pop( index ) if index >= 0 and index < len( self.__items ) else None

	def minimumSize( self ) :

		assert( len( self.__items ) == 2 )

		size1 = self.__items[1].minimumSize()
		return QtCore.QSize(
			self.__minColorFieldSize + size1.width(),
			max( self.__minColorFieldSize, size1.height() )
		)

	def maximumSize( self ) :

		return QtCore.QSize( QtWidgets.QLayout.maximumSize( self ).width(), self.sizeHint().height() )

	def sizeHint( self ) :

		assert( len( self.__items ) == 2 )

		size1 = self.__items[1].sizeHint()
		return QtCore.QSize(
			size1.height() + size1.width(),
			max( self.__minColorFieldSize, size1.height() )
		)

	def setGeometry( self, rect ) :

		assert( len( self.__items ) == 2 )

		size1 = self.__items[1].sizeHint()

		leftSize = 0
		if not self.__items[0].isEmpty() :
			leftSize = max( self.__minColorFieldSize, min( size1.height(), rect.width() / 2 ) )
			self.__items[0].setGeometry( QtCore.QRect( rect.left(), rect.top(), leftSize, leftSize ) )

		self.__items[1].setGeometry(
			QtCore.QRect(
				rect.left() + leftSize,
				rect.top(),
				rect.width() - leftSize,
				size1.height()
			)
		)

class _ColorFieldRowContainer( GafferUI.ContainerWidget ) :

	def __init__( self, **kw ) :

		GafferUI.ContainerWidget.__init__( self, QtWidgets.QWidget(), **kw )

		self.__qtLayout = _ColorFieldRowLayout()
		self.__qtLayout.setSizeConstraint( QtWidgets.QLayout.SetMinAndMaxSize )

		self._qtWidget().setLayout( self.__qtLayout )

		self.__widgets = []

	def addChild( self, child ) :

		assert( isinstance( child, GafferUI.Widget ) )
		assert( len( self.__widgets ) < 2 )

		oldParent = child.parent()
		if oldParent is not None :
			oldParent.removeChild( child )

		self.__widgets.append( child )

		self.__qtLayout.addWidget( child._qtWidget() )

		child._applyVisibility()

	def removeChild( self, child ) :

		self.__widgets.remove( child )
		child._qtWidget().setParent( None )
		child._applyVisibility()

class ColorChooser( GafferUI.Widget ) :

	ColorChangedReason = enum.Enum( "ColorChangedReason", [ "Invalid", "SetColor", "Reset" ] )

	__ColorSpace = enum.Enum( "__ColorSpace", [ "RGB", "HSV", "TMI" ] )

	def __init__( self, color=imath.Color3f( 1 ), **kw ) :

		self.__column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing = 4 )

		GafferUI.Widget.__init__( self, self.__column, **kw )

		self.__color = color
		self.__colorHSV = self.__color.rgb2hsv()
		self.__colorTMI = _rgbToTMI( self.__color )
		self.__defaultColor = color

		self.__sliders = {}
		self.__numericWidgets = {}
		self.__channelLabels = {}
		self.__channelFrames = {}
		# For the icons indicating the components used in the color field, we use
		# a `GafferUI.Frame` as a container for the icon. Setting a fixed size for
		# an empty `QFrame` within the `GafferUI.Frame` is not working, so we
		# reserve space for each channel with an empty `GafferUI.Image` of the right size.
		self.__channelIconPlaceholders = { k : GafferUI.Image( "colorFieldEmptyIcon.png" ) for k in "rgbahsvtmi" }
		self.__spacers = {}
		self.__componentValueChangedConnections = []

		self.__componentToolTip = "Click to use this component in the color field."

		with self.__column :
			with _ColorFieldRowContainer() :

				self.__colorField = _ColorField( color )
				self.__colorValueChangedConnection = self.__colorField.valueChangedSignal().connect( Gaffer.WeakMethod( self.__colorValueChanged ) )

				with GafferUI.GridContainer( spacing = 0 ) as grid :

					# sliders and numeric widgets
					for component in "rgbahsvtmi" :
						row = { "r" : 0, "g" : 1, "b" : 2, "a" : 4, "h" : 6, "s" : 7, "v" : 8, "t" : 10, "m" : 11, "i" : 12 }[component]
						self.__channelFrames[component] = GafferUI.Frame(
							self.__channelIconPlaceholders[component],
							borderWidth = 0,
							borderStyle = GafferUI.Frame.BorderStyle.None_,
							toolTip = self.__componentToolTip if component != "a" else "",
							parenting = { "index" : ( 0, row ) }
						)
						# Remove the `gafferBorderStyle` property to remove padding that `_StyleSheet` adds. This way
						# the icons connect without gaps.
						self.__channelFrames[component]._qtWidget().setProperty( "gafferBorderStyle", GafferUI._Variant.toVariant( None ) )

						self.__channelLabels[component] = GafferUI.Label(
							component.capitalize(),
							toolTip = self.__componentToolTip if component != "a" else "",
							parenting = { "index" : ( 1, row ), "alignment" : ( GafferUI.HorizontalAlignment.Center, GafferUI.VerticalAlignment.Center ) }
						)
						# Match the label height to the icon height to maintain spacing when the icons
						# are hidden.
						self.__channelLabels[component]._qtWidget().setFixedHeight( 22 )

						# We could use the internal Qt `QGridLayout.setHorizontalSpacing()` to accomplish almost the same
						# effect, but it would add space between the component icon and the label which creates gap in the
						# hover regions for the color field component selection.
						GafferUI.Spacer( imath.V2i( 4, 0 ), parenting = { "index" : ( 2, row ) } )

						if component != "a" :
							self.__channelLabels[component].buttonReleaseSignal().connect(
								functools.partial(
									Gaffer.WeakMethod( self.__channelLabelReleased ),
									component = component
								)
							)
							self.__channelLabels[component].enterSignal().connect(
								functools.partial(
									Gaffer.WeakMethod( self.__labelEnter ),
									component = component
								)
							)
							self.__channelLabels[component].leaveSignal().connect(
								functools.partial(
									Gaffer.WeakMethod( self.__labelLeave ),
									component = component
								)
							)
							self.__channelFrames[component].buttonReleaseSignal().connect(
								functools.partial(
									Gaffer.WeakMethod( self.__channelLabelReleased ),
									component = component
								)
							)
							self.__channelFrames[component].enterSignal().connect(
								functools.partial(
									Gaffer.WeakMethod( self.__labelEnter ),
									component = component
								)
							)
							self.__channelFrames[component].leaveSignal().connect(
								functools.partial(
									Gaffer.WeakMethod( self.__labelLeave ),
									component = component
								)
							)

						numericWidget = GafferUI.NumericWidget( 0.0, parenting = { "index" : ( 3, row ) } )

						GafferUI.Spacer( imath.V2i( 4, 0 ), parenting = { "index" : ( 4, row ) } )

						numericWidget.setFixedCharacterWidth( 6 )
						numericWidget.component = component
						self.__numericWidgets[component] = numericWidget

						slider = _ComponentSlider( color, component, parenting = { "index" : ( 5, row ) } )
						self.__sliders[component] = slider

						self.__componentValueChangedConnections.append(
							numericWidget.valueChangedSignal().connect( Gaffer.WeakMethod( self.__componentValueChanged ) )
						)

						self.__componentValueChangedConnections.append(
							slider.valueChangedSignal().connect( Gaffer.WeakMethod( self.__componentValueChanged ) )
						)

					spacerHeight = 2
					self.__spacers["a"] = GafferUI.Spacer( imath.V2i( 0, spacerHeight ), parenting = { "index" : ( 0, 3 ) } )
					self.__spacers["hsv"] = GafferUI.Spacer( imath.V2i( 0, spacerHeight ), parenting = {  "index" : ( 0, 5 ) } )
					self.__spacers["tmi"] = GafferUI.Spacer( imath.V2i( 0, spacerHeight ), parenting = { "index" : ( 0, 9 ) } )

					# Options Button.

					GafferUI.Spacer( imath.V2i( 4, 0 ), parenting = { "index" : ( 6, slice( 0, grid.gridSize().y ) ) } )
					GafferUI.MenuButton(
						image = "gear.png",
						menu = GafferUI.Menu( Gaffer.WeakMethod( self.__optionsMenuDefinition ) ),
						hasFrame = False,
						# Occupy an entire column of the grid, but aligned to the top of the column.
						# This keeps the button aligned with the top of the first visible slider, no
						# matter which that is.
						parenting = { "index" : ( 7, slice( 0, grid.gridSize().y ) ), "alignment" : ( GafferUI.HorizontalAlignment.None_, GafferUI.VerticalAlignment.Top ) }
					)

			# initial and current colour swatches
			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) as self.__swatchRow :

				self.__initialColorSwatch = GafferUI.ColorSwatch( color, parenting = { "expand" : True } )
				self.__initialColorSwatch._qtWidget().setFixedHeight( 40 )
				self.__initialColorSwatch.buttonPressSignal().connect( Gaffer.WeakMethod( self.__initialColorPress ) )

				self.__colorSwatch = GafferUI.ColorSwatch( color, parenting = { "expand" : True } )
				self.__colorSwatch._qtWidget().setFixedHeight( 40 )

		self.__colorChangedSignal = Gaffer.Signals.Signal2()
		self.__visibleComponentsChangedSignal = Gaffer.Signals.Signal1()
		self.__staticComponentChangedSignal = Gaffer.Signals.Signal1()
		self.__colorFieldVisibleChangedSignal = Gaffer.Signals.Signal1()
		self.__dynamicSliderBackgroundsChangedSignal = Gaffer.Signals.Signal1()
		self.__optionsMenuSignal = Gaffer.Signals.Signal2()

		self.__colorFieldPrimaryIcon = GafferUI.Image( "colorFieldPrimaryIcon.png" )
		self.__colorFieldPrimaryHighlightedIcon = GafferUI.Image( "colorFieldPrimaryHighlightedIcon.png" )
		self.__colorFieldSecondaryIcon = GafferUI.Image( "colorFieldSecondaryIcon.png" )
		self.__colorFieldSpacerIcon = GafferUI.Image( "colorFieldSpacerIcon.png" )

		self.__updateUIFromColor()
		self.__updateComponentIcons()

	## The default color starts as the value passed when creating the widget.
	# It is represented with a swatch which when clicked will revert the current
	# selection back to the original.
	def setInitialColor( self, color ) :

		self.__initialColorSwatch.setColor( color )

	def getInitialColor( self ) :

		return self.__initialColorSwatch.getColor()

	def setColor( self, color ) :

		self.__setColorInternal( color, self.ColorChangedReason.SetColor )

	def getColor( self ) :

		return self.__color

	def setSwatchesVisible( self, visible ) :

		self.__swatchRow.setVisible( visible )

	def getSwatchesVisible( self ) :

		return self.__swatchRow.getVisible()

	def setErrored( self, errored ) :

		for n in self.__numericWidgets.values():
			n.setErrored( errored )

	def getErrored( self ) :
		return any( w.getErrored() for w in self.__numericWidgets.values() )

	def setVisibleComponents( self, components ) :

		self.__setVisibleComponentsInternal( components )

	def getVisibleComponents( self ) :

		return "".join( [ k for k, v in self.__sliders.items() if v.getVisible() ] )

	def setColorFieldStaticComponent( self, component ) :

		c, previousComponent = self.__colorField.getColor()
		if component == previousComponent :
			return

		assert( component in "rgbhsvtmi" )
		if component in "rgb" :
			self.__colorField.setColor( self.__color, component )
		elif component in "hsv" :
			self.__colorField.setColor( self.__colorHSV, component )
		else :
			self.__colorField.setColor( self.__colorTMI, component )

		if self.__colorField.getVisible() :
			self.__updateComponentIcons()

		self.__staticComponentChangedSignal( self )

	def getColorFieldStaticComponent( self ) :

		c, staticComponent = self.__colorField.getColor()
		return staticComponent

	def setColorFieldVisible( self, visible ) :

		self.__setColorFieldVisibleInternal( visible )

	def getColorFieldVisible( self ) :

		return self.__colorField.getVisible()

	def setDynamicSliderBackgrounds( self, dynamic ) :

		for component, slider in self.__sliders.items() :
			slider.setDynamicBackground( dynamic )
		self.__colorField.setDynamicBackground( dynamic )

		self.__dynamicSliderBackgroundsChangedSignal( self )

	def getDynamicSliderBackgrounds( self ) :

		return self.__sliders["r"].getDynamicBackground()

	## A signal emitted whenever the color is changed. Slots should
	# have the signature slot( ColorChooser, reason ). The reason
	# argument may be passed either a ColorChooser.ColorChangedReason,
	# a Slider.ValueChangedReason or a NumericWidget.ValueChangedReason
	# to describe the reason for the change.
	def colorChangedSignal( self ) :

		return self.__colorChangedSignal

	## A signal emitted whenever the visible components are changed. Slots
	# should have the signature slot( ColorChooser ).
	def visibleComponentsChangedSignal( self ) :

		return self.__visibleComponentsChangedSignal

	## A signal emitted whenever the static component is changed. Slots
	# should have the signature slot( ColorChooser ).
	def staticComponentChangedSignal( self ) :

		return self.__staticComponentChangedSignal

	## A signal emitted whenever the visibility of the color field changes.
	# Slots should have the signature slot( ColorChooser ).
	def colorFieldVisibleChangedSignal( self ) :

		return self.__colorFieldVisibleChangedSignal

	## A signal emitted whenever the dynamic colors option is changed.
	# Slots should have the signature slot( ColorChooser ).
	def dynamicSliderBackgroundsChangedSignal( self ) :

		return self.__dynamicSliderBackgroundsChangedSignal

	## A signal emitted whenever the options menu is opened.
	# Slots should have the signature slot( ColorChooser, menuDefinition )
	# and add menu items to `menuDefinition`.
	def optionsMenuSignal( self ) :

		return self.__optionsMenuSignal

	## Returns True if a user would expect the specified sequence
	# of changes to be merged into a single undoable event.
	@classmethod
	def changesShouldBeMerged( cls, firstReason, secondReason ) :

		if isinstance( firstReason, GafferUI.Slider.ValueChangedReason ) :
			return GafferUI.Slider.changesShouldBeMerged( firstReason, secondReason )
		elif isinstance( firstReason, GafferUI.NumericWidget.ValueChangedReason ) :
			return GafferUI.NumericWidget.changesShouldBeMerged( firstReason, secondReason )

		return False

	def __optionsMenuDefinition( self ) :

		result = IECore.MenuDefinition()

		result.append( "/__widgetsDivider__", { "divider": True, "label": "Visible Controls" } )

		for channels in [ "rgb", "hsv", "tmi" ] :
			result.append(
				"/{} Sliders".format( channels.upper() ),
				{
					"command": functools.partial( Gaffer.WeakMethod( self.__toggleComponentTriplet ), channels ),
					"checkBox": self.__channelLabels[channels[0]].getVisible()
				}
			)

		result.append(
			"/Color Field",
			{
				"command": functools.partial( Gaffer.WeakMethod( self.__toggleColorField ) ),
				"checkBox": self.__colorField.getVisible()
			}
		)

		result.append( "/__colorField__", { "divider": True, "label": "Color Field" } )

		weakSet = Gaffer.WeakMethod( self.setColorFieldStaticComponent )
		for label, component in [
			( "Hue/Saturation", "v" ),
			( "Hue/Value", "s" ),
			( "Saturation/Value", "h" ),
			( "Red/Green", "b" ),
			( "Red/Blue", "g" ),
			( "Green/Blue", "r" ),
			( "Temperature/Magenta", "i" ),
			( "Temperature/Intensity", "m" ),
			( "Magenta/Intensity", "t" ),
		] :
			result.append(
				"{}/{}".format( "/Other" if component not in "hsv" else "", component ),
				{
					"command": lambda checked, c = component, weakSet = weakSet : weakSet( c ),
					"checkBox": self.getColorFieldStaticComponent() == component,
					"active": self.__colorField.getVisible(),
					"label" : label,
				}
			)

		result.append( "/__sliders__", { "divider": True, "label": "Sliders" } )

		result.append(
			"/Dynamic Backgrounds",
			{
				"command": Gaffer.WeakMethod( self.setDynamicSliderBackgrounds ),
				"checkBox": self.getDynamicSliderBackgrounds(),
				"description": """With Dynamic Backgrounds enabled, the backgrounds of the color sliders will
update to show the color that will result from moving the indicator to a given
position. When disabled, a static range of values is displayed."""
			}
		)

		self.__optionsMenuSignal( self, result )

		return result

	def __channelLabelReleased( self, widget, event, component ) :

		if not self.__colorField.visible() :
			return False

		yCandidates = { "r": "gb", "g": "rb", "b": "rg", "h": "sv", "s": "hv", "v": "hs", "t": "mi", "m": "ti", "i" : "tm" }[component]

		menuDefinition = IECore.MenuDefinition()
		menuDefinition.append( "/__colorField__", { "divider" : True, "label": "Color Field" } )

		currentComponents = sorted( list( self.__colorField.xyAxes() ), key = lambda c : "rgbhsvtmi".index( c ) )

		weakSet = Gaffer.WeakMethod( self.setColorFieldStaticComponent )
		for index, otherAxis in enumerate( yCandidates ) :
			components = sorted( [ component, otherAxis ], key = lambda c : "rgbhsvtmi".index( c ) )
			menuDefinition.append(
				"/" + "".join( [ i.upper() for i in components ] ),
				{
					"command": lambda checked, yc = yCandidates, i = index, weakSet = weakSet : weakSet( yc[ 1 - i ] ),
					"checkBox": components == currentComponents,
				}
		)

		self.__axisMenu = GafferUI.Menu( menuDefinition )
		self.__axisMenu.popup()

		return True

	def __toggleComponentTriplet( self, channels, *unused ) :

		visibleComponents = set( self.getVisibleComponents() )
		for c in channels :
			if c in visibleComponents :
				visibleComponents.remove( c )
			elif c != "a" or self.getColor().dimensions() == 4 :
				visibleComponents.add( c )

		self.__setVisibleComponentsInternal( "".join( visibleComponents ) )

	def __toggleColorField( self, *unused ) :

		self.__setColorFieldVisibleInternal( not self.__colorField.getVisible() )

	def __initialColorPress( self, button, event ) :

		self.__setColorInternal( self.getInitialColor(), self.ColorChangedReason.Reset )

	def __componentValueChanged( self, componentWidget, reason ) :

		## \todo We're doing the clamping here because NumericWidget
		# doesn't provide the capability itself. Add the functionality
		# into the NumericWidget and remove this code.
		componentValue = componentWidget.getValue()
		componentValue = max( componentValue, _ranges[componentWidget.component].hardMin )
		componentValue = min( componentValue, _ranges[componentWidget.component].hardMax )

		if componentWidget.component in ( "r", "g", "b", "a" ) :
			newColor = self.__color.__class__( self.__color )

			a = { "r" : 0, "g" : 1, "b" : 2, "a" : 3 }[componentWidget.component]
			newColor[a] = componentValue

			self.__setColorInternal( newColor, reason )
		elif componentWidget.component in ( "h", "s", "v" ) :
			newColor = self.__colorHSV.__class__( self.__colorHSV )

			a = { "h" : 0, "s" : 1, "v" : 2 }[componentWidget.component]
			newColor[a] = componentValue

			self.__setColorInternal( newColor, reason, self.__ColorSpace.HSV )
		elif componentWidget.component in ( "t", "m", "i" ) :
			newColor = self.__colorTMI.__class__( self.__colorTMI )

			a = { "t" : 0, "m" : 1, "i" : 2 }[componentWidget.component]
			newColor[a] = componentValue

			self.__setColorInternal( newColor, reason, self.__ColorSpace.TMI )

	def __colorValueChanged( self, colorWidget, reason ) :

		c, staticComponent = colorWidget.getColor()
		if staticComponent in "rgb" :
			colorSpace = self.__ColorSpace.RGB
		elif staticComponent in "hsv" :
			colorSpace = self.__ColorSpace.HSV
		else :
			colorSpace = self.__ColorSpace.TMI

		self.__setColorInternal( c, reason, colorSpace )

	def __setColorInternal( self, color, reason, colorSpace = __ColorSpace.RGB ) :

		dragBeginOrEnd = reason in (
			GafferUI.Slider.ValueChangedReason.DragBegin,
			GafferUI.Slider.ValueChangedReason.DragEnd,
			GafferUI.NumericWidget.ValueChangedReason.DragBegin,
			GafferUI.NumericWidget.ValueChangedReason.DragEnd,
		)

		colorChanged = color != {
			self.__ColorSpace.RGB : self.__color,
			self.__ColorSpace.HSV : self.__colorHSV,
			self.__ColorSpace.TMI : self.__colorTMI
		}[colorSpace]

		if colorChanged :
			if colorSpace == self.__ColorSpace.RGB :
				colorRGB = color
				colorHSV = color.rgb2hsv()
				colorTMI = _rgbToTMI( colorRGB )
			elif colorSpace == self.__ColorSpace.HSV :
				colorRGB = color.hsv2rgb()
				colorHSV = color
				colorTMI = _rgbToTMI( colorRGB )
			elif colorSpace == self.__ColorSpace.TMI :
				colorRGB = _tmiToRGB( color )
				colorHSV = colorRGB.rgb2hsv()
				colorTMI = color

			if colorSpace != self.__ColorSpace.HSV :
				colorHSV[0] = colorHSV[0] if colorHSV[1] > 1e-7 and colorHSV[2] > 1e-7 else self.__colorHSV[0]
				colorHSV[1] = colorHSV[1] if colorHSV[2] > 1e-7 else self.__colorHSV[1]

			self.__color = colorRGB
			self.__colorHSV = colorHSV
			self.__colorTMI = colorTMI

			self.__colorSwatch.setColor( colorRGB )

		## \todo This is outside the conditional because the clamping we do
		# in __componentValueChanged means the color value may not correspond
		# to the value in the ui, even if it hasn't actually changed. Move this
		# back inside the conditional when we get the clamping performed internally
		# in NumericWidget.
		self.__updateUIFromColor()

		if colorChanged or dragBeginOrEnd :
			# We never optimise away drag begin or end, because it's important
			# that they emit in pairs.
			self.__colorChangedSignal( self, reason )

	def __updateUIFromColor( self ) :

		with Gaffer.Signals.BlockedConnection(
			self.__componentValueChangedConnections + [ self.__colorValueChangedConnection ]
		) :

			c = self.getColor()

			for slider in [ v for k, v in self.__sliders.items() if k in "rgba" ] :
				slider.setColor( c )

			for component, index in ( ( "r", 0 ), ( "g", 1 ), ( "b", 2 ) ) :
				self.__sliders[component].setValue( c[index] )
				self.__numericWidgets[component].setValue( c[index] )

			if c.dimensions() == 4 :
				self.__sliders["a"].setValue( c[3] )
				self.__numericWidgets["a"].setValue( c[3] )

				self.__setComponentVisible( "a", True )
			else :
				self.__setComponentVisible( "a", False )

			for slider in [ v for k, v in self.__sliders.items() if k in "hsv" ] :
				slider.setColor( self.__colorHSV )

			for component, index in ( ( "h", 0 ), ( "s", 1 ), ( "v", 2 ) ) :
				self.__sliders[component].setValue( self.__colorHSV[index] )
				self.__numericWidgets[component].setValue( self.__colorHSV[index] )

			for slider in [ v for k, v in self.__sliders.items() if k in "tmi" ] :
				slider.setColor( self.__colorTMI )

			for component, index in ( ( "t", 0 ), ( "m", 1 ), ( "i", 2 ) ) :
				self.__sliders[component].setValue( self.__colorTMI[index] )
				self.__numericWidgets[component].setValue( self.__colorTMI[index] )

			c, staticComponent = self.__colorField.getColor()
			assert( staticComponent in "rgbhsvtmi" )
			if staticComponent in "rgb" :
				self.__colorField.setColor( self.__color, staticComponent )
			elif staticComponent in "hsv" :
				self.__colorField.setColor( self.__colorHSV, staticComponent )
			else :
				self.__colorField.setColor( self.__colorTMI, staticComponent )

	def __componentIcon( self, component ) :

		assert( component in "rgbhsvtmi" )

		c, staticComponent = self.__colorField.getColor()

		icons = {
			"r" : { "g" : self.__colorFieldPrimaryIcon, "b" : self.__colorFieldSecondaryIcon },
			"g" : { "r" : self.__colorFieldPrimaryIcon, "g" : self.__colorFieldSpacerIcon, "b" : self.__colorFieldSecondaryIcon },
			"b" : { "r" : self.__colorFieldPrimaryIcon, "g" : self.__colorFieldSecondaryIcon },
			"h" : { "s" : self.__colorFieldPrimaryIcon, "v" : self.__colorFieldSecondaryIcon },
			"s" : { "h" : self.__colorFieldPrimaryIcon, "s" : self.__colorFieldSpacerIcon, "v" : self.__colorFieldSecondaryIcon },
			"v" : { "h" : self.__colorFieldPrimaryIcon, "s" : self.__colorFieldSecondaryIcon },
			"t" : { "m" : self.__colorFieldPrimaryIcon, "i" : self.__colorFieldSecondaryIcon },
			"m" : { "t" : self.__colorFieldPrimaryIcon, "m" : self.__colorFieldSpacerIcon, "i" : self.__colorFieldSecondaryIcon },
			"i" : { "t" : self.__colorFieldPrimaryIcon, "m" : self.__colorFieldSecondaryIcon },
		}[staticComponent]

		return icons.get( component, self.__channelIconPlaceholders[component] )

	def __clearComponentIcons( self ) :

		for c in "rgbhsvtmi" :
			self.__channelFrames[c].setChild( self.__channelIconPlaceholders[c] )

	def __updateComponentIcons( self ) :

		self.__clearComponentIcons()

		c, staticComponent = self.__colorField.getColor()
		self.__channelFrames[staticComponent].setChild( self.__componentIcon( staticComponent ) )

		xAxis, yAxis = self.__colorField.xyAxes()
		self.__channelFrames[xAxis].setChild( self.__componentIcon( xAxis ) )
		self.__channelFrames[yAxis].setChild( self.__componentIcon( yAxis ) )

	def __setChildCallback( self, component, icon ) :

		# We don't just use `GafferUI.Frame.setChild()` directly because it may encounter
		# a race condition when calling it in `__labelEnter()` or `__labelLeave()`. It's
		# possible to have a second call to those functions before `setChild()` completes.
		# This means the check in `GafferUI.Frame.setChild()` that the child being removed
		# is in fact the child held by `Frame` would fail. By putting the calls on the main
		# event loop, we ensure they are called sequentially.

		self.__channelFrames[component].setChild( icon )

		return False

	def __labelEnter( self, widget, component ) :

		if not self.__colorField.getVisible() :
			return

		GafferUI.EventLoop.addIdleCallback(
			functools.partial( self.__setChildCallback, component, self.__colorFieldPrimaryHighlightedIcon )
		)

		return True

	def __labelLeave( self, widget, component ) :

		if not self.__colorField.getVisible() :
			return

		GafferUI.EventLoop.addIdleCallback(
			functools.partial( self.__setChildCallback, component, self.__componentIcon( component ) )
		)

		return True

	def __setComponentVisible( self, component, visible ) :

		self.__channelFrames[component].setVisible( visible and self.__colorField.getVisible() )
		self.__channelLabels[component].setVisible( visible )
		self.__numericWidgets[component].setVisible( visible )
		self.__sliders[component].setVisible( visible )

		if component == "a" :
			self.__spacers["a"].setVisible( visible and any( self.__channelLabels[c].getVisible() for c in "rgb" ) )
		elif component in "hsv" :
			self.__spacers["hsv"].setVisible( visible and any( self.__channelLabels[c].getVisible() for c in "rgba" ) )
		elif component in "tmi" :
			self.__spacers["tmi"].setVisible( visible and any( self.__channelLabels[c].getVisible() for c in "rgbahsv" ) )

	def __setVisibleComponentsInternal( self, components ) :

		componentsSet = set( components )

		if self.getColor().dimensions() == 4 :
			componentsSet.add( "a" )
		elif "a" in componentsSet :
			componentsSet.remove( "a" )

		if componentsSet == set( self.getVisibleComponents() ) :
			return

		for c in self.__sliders.keys() :
			self.__setComponentVisible( c, c in componentsSet )

		self.__visibleComponentsChangedSignal( self )

	def __setColorFieldVisibleInternal( self, visible ) :

		if visible == self.__colorField.getVisible() :
			return

		self.__colorField.setVisible( visible )

		if visible :
			self.__updateComponentIcons()
			for c, label in self.__channelLabels.items() :
				label.setToolTip( self.__componentToolTip if c != "a" else "" )
			for c, frame in self.__channelFrames.items() :
				frame.setToolTip( self.__componentToolTip if c != "a" else "" )
		else :
			for label in self.__channelLabels.values() :
				label.setToolTip( "" )
			for frame in self.__channelFrames.values() :
				frame.setToolTip( "" )

		for c in self.getVisibleComponents() :
			self.__channelFrames[c].setVisible( visible )

		self.__colorFieldVisibleChangedSignal( self )
