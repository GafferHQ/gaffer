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

import enum
import sys
import imath

import Gaffer
import GafferUI

from Qt import QtGui

# A custom slider for drawing the backgrounds.
class _ComponentSlider( GafferUI.Slider ) :

	def __init__( self, color, component, **kw ) :

		min = hardMin = 0
		max = hardMax = 1

		if component in ( "r", "g", "b", "v" ) :
			hardMax = sys.float_info.max

		GafferUI.Slider.__init__( self, 0.0, min, max, hardMin, hardMax, **kw )

		self.color = color
		self.component = component

	# Sets the slider color in RGB space for RGBA channels and
	# HSV space for HSV channels.
	def setColor( self, color ) :

		self.color = color
		self._qtWidget().update()

	def getColor( self ) :

		return self.color

	def _drawBackground( self, painter ) :

		size = self.size()
		grad = QtGui.QLinearGradient( 0, 0, size.x, 0 )

		displayTransform = self.displayTransform()

		if self.component == "a" :
			c1 = imath.Color3f( 0 )
			c2 = imath.Color3f( 1 )
		else :
			c1 = imath.Color3f( self.color[0], self.color[1], self.color[2] )
			c2 = imath.Color3f( self.color[0], self.color[1], self.color[2] )
			a = { "r" : 0, "g" : 1, "b" : 2, "h" : 0, "s" : 1, "v": 2 }[self.component]
			c1[a] = 0
			c2[a] = 1

		numStops = max( 2, size.x // 2 )
		for i in range( 0, numStops ) :

			t = float( i ) / (numStops-1)
			c = c1 + (c2-c1) * t
			if self.component in "hsv" :
				c = c.hsv2rgb()

			grad.setColorAt( t, self._qtColor( displayTransform( c ) ) )

		brush = QtGui.QBrush( grad )
		painter.fillRect( 0, 0, size.x, size.y, brush )

	def _displayTransformChanged( self ) :

		GafferUI.Slider._displayTransformChanged( self )
		self._qtWidget().update()

class ColorChooser( GafferUI.Widget ) :

	ColorChangedReason = enum.Enum( "ColorChangedReason", [ "Invalid", "SetColor", "Reset" ] )

	def __init__( self, color=imath.Color3f( 1 ), **kw ) :

		self.__column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical, spacing = 4 )

		GafferUI.Widget.__init__( self, self.__column, **kw )

		self.__color = color
		self.__colorHSV = self.__color.rgb2hsv()
		self.__defaultColor = color

		self.__sliders = {}
		self.__numericWidgets = {}
		self.__componentValueChangedConnections = []

		with self.__column :

			# sliders and numeric widgets
			for component in "rgbahsv" :
				with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :

					with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 8 ) :
						GafferUI.Label( component.capitalize() )
						numericWidget = GafferUI.NumericWidget( 0.0 )

					numericWidget.setFixedCharacterWidth( 6 )
					numericWidget.component = component
					self.__numericWidgets[component] = numericWidget

					slider = _ComponentSlider( color, component )
					self.__sliders[component] = slider

					self.__componentValueChangedConnections.append(
						numericWidget.valueChangedSignal().connect( Gaffer.WeakMethod( self.__componentValueChanged ), scoped = False )
					)

					self.__componentValueChangedConnections.append(
						slider.valueChangedSignal().connect( Gaffer.WeakMethod( self.__componentValueChanged ), scoped = False )
					)

			# initial and current colour swatches
			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) as self.__swatchRow :

				self.__initialColorSwatch = GafferUI.ColorSwatch( color, parenting = { "expand" : True } )
				self.__initialColorSwatch._qtWidget().setFixedHeight( 40 )
				self.__initialColorSwatch.buttonPressSignal().connect( Gaffer.WeakMethod( self.__initialColorPress ), scoped = False )

				self.__colorSwatch = GafferUI.ColorSwatch( color, parenting = { "expand" : True } )
				self.__colorSwatch._qtWidget().setFixedHeight( 40 )

		self.__colorChangedSignal = Gaffer.Signals.Signal2()

		self.__updateUIFromColor()

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

		self.__swatchRow.setVisible( False )

	def getSwatchesVisible( self ) :

		return self.__swatchRow.getVisible()

	def setErrored( self, errored ) :

		for n in self.__numericWidgets.values():
			n.setErrored( errored )

	def getErrored( self ) :
		return any( w.getErrored() for w in self.__numericWidgets.values() )

	## A signal emitted whenever the color is changed. Slots should
	# have the signature slot( ColorChooser, reason ). The reason
	# argument may be passed either a ColorChooser.ColorChangedReason,
	# a Slider.ValueChangedReason or a NumericWidget.ValueChangedReason
	# to describe the reason for the change.
	def colorChangedSignal( self ) :

		return self.__colorChangedSignal

	## Returns True if a user would expect the specified sequence
	# of changes to be merged into a single undoable event.
	@classmethod
	def changesShouldBeMerged( cls, firstReason, secondReason ) :

		if isinstance( firstReason, GafferUI.Slider.ValueChangedReason ) :
			return GafferUI.Slider.changesShouldBeMerged( firstReason, secondReason )
		elif isinstance( firstReason, GafferUI.NumericWidget.ValueChangedReason ) :
			return GafferUI.NumericWidget.changesShouldBeMerged( firstReason, secondReason )

		return False

	def __initialColorPress( self, button, event ) :

		self.__setColorInternal( self.getInitialColor(), self.ColorChangedReason.Reset )

	def __componentValueChanged( self, componentWidget, reason ) :

		## \todo We're doing the clamping here because NumericWidget
		# doesn't provide the capability itself. Add the functionality
		# into the NumericWidget and remove this code.
		componentValue = componentWidget.getValue()
		componentValue = max( componentValue, 0 )
		if componentWidget.component in ( "a", "h", "s" ) :
			componentValue = min( componentValue, 1 )

		if componentWidget.component in ( "r", "g", "b", "a" ) :
			newColor = self.__color.__class__( self.__color )

			a = { "r" : 0, "g" : 1, "b" : 2, "a" : 3 }[componentWidget.component]
			newColor[a] = componentValue

			self.__setColorInternal( newColor, reason )
		else :
			newColor = self.__colorHSV.__class__( self.__colorHSV )

			a = { "h" : 0, "s" : 1, "v" : 2 }[componentWidget.component]
			newColor[a] = componentValue

			self.__setColorInternal( newColor, reason, True )

	def __setColorInternal( self, color, reason, hsv = False ) :

		dragBeginOrEnd = reason in (
			GafferUI.Slider.ValueChangedReason.DragBegin,
			GafferUI.Slider.ValueChangedReason.DragEnd,
			GafferUI.NumericWidget.ValueChangedReason.DragBegin,
			GafferUI.NumericWidget.ValueChangedReason.DragEnd,
		)

		colorChanged = color != ( self.__colorHSV if hsv else self.__color )

		if colorChanged :
			colorRGB = color.hsv2rgb() if hsv else color
			self.__color = colorRGB
			self.__colorSwatch.setColor( colorRGB )

			hsv = color if hsv else color.rgb2hsv()

			hsv[0] = hsv[0] if hsv[1] > 1e-7 and hsv[2] > 1e-7 else self.__colorHSV[0]
			hsv[1] = hsv[1] if hsv[2] > 1e-7 else self.__colorHSV[1]

			self.__colorHSV = hsv

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

		with Gaffer.Signals.BlockedConnection( self.__componentValueChangedConnections ) :

			c = self.getColor()

			for slider in [ v for k, v in self.__sliders.items() if k in "rgba" ] :
				slider.setColor( c )

			for component, index in ( ( "r", 0 ), ( "g", 1 ), ( "b", 2 ) ) :
				self.__sliders[component].setValue( c[index] )
				self.__numericWidgets[component].setValue( c[index] )

			if c.dimensions() == 4 :
				self.__sliders["a"].setValue( c[3] )
				self.__numericWidgets["a"].setValue( c[3] )
				self.__sliders["a"].parent().setVisible( True )
			else :
				self.__sliders["a"].parent().setVisible( False )

			for slider in [ v for k, v in self.__sliders.items() if k in "hsv" ] :
				slider.setColor( self.__colorHSV )

			for component, index in ( ( "h", 0 ), ( "s", 1 ), ( "v", 2 ) ) :
				self.__sliders[component].setValue( self.__colorHSV[index] )
				self.__numericWidgets[component].setValue( self.__colorHSV[index] )
