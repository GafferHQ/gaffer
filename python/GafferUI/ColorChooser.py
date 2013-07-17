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

import sys

import IECore

import Gaffer
import GafferUI

QtGui = GafferUI._qtImport( "QtGui" )

# A custom slider for drawing the backgrounds.
class ColorSlider( GafferUI.NumericSlider ) :

	def __init__( self, color, component, **kw ) :
	
		min = hardMin = 0
		max = hardMax = 1
		
		if component in ( "r", "g", "b", "v" ) :
			hardMax = sys.float_info.max
	
		GafferUI.NumericSlider.__init__( self, 0.0, min, max, hardMin, hardMax, **kw )
		
		self.color = color
		self.component = component
		
		self.__displayTransformChangedConnection = GafferUI.DisplayTransform.changedSignal().connect( Gaffer.WeakMethod( self.__displayTransformChanged ) )
		
	def setColor( self, color ) :
	
		self.color = color
		self._qtWidget().update()
		
	def getColor( self ) :
	
		return self.color	
		
	def _drawBackground( self, painter ) :
	
		size = self.size()		
		grad = QtGui.QLinearGradient( 0, 0, size.x, 0 )
		
		displayTransform = GafferUI.DisplayTransform.get()

		if self.component == "a" :
			c1 = IECore.Color3f( 0 )
			c2 = IECore.Color3f( 1 )
		else :
			c1 = IECore.Color3f( self.color[0], self.color[1], self.color[2] )
			c2 = IECore.Color3f( self.color[0], self.color[1], self.color[2] )
			if self.component in "hsv" :
				c1 = c1.rgbToHSV()
				c2 = c2.rgbToHSV()
			a = { "r" : 0, "g" : 1, "b" : 2, "h" : 0, "s" : 1, "v": 2 }[self.component]
			c1[a] = 0
			c2[a] = 1
					
		numStops = max( 2, size.x / 2 )
		for i in range( 0, numStops ) :
			
			t = float( i ) / (numStops-1)	
			c = c1 + (c2-c1) * t
			if self.component in "hsv" :
				c = c.hsvToRGB()
			
			grad.setColorAt( t, self._qtColor( displayTransform( c ) ) )
					
		brush = QtGui.QBrush( grad )
		painter.fillRect( 0, 0, size.x, size.y, brush )
	
	def __displayTransformChanged( self ) :
		
		self._qtWidget().update()
				
class ColorChooser( GafferUI.Widget ) :

	ColorChangedReason = IECore.Enum.create( "Invalid", "SetColor", "Reset" )

	def __init__( self, color=IECore.Color3f( 1 ) ) :
	
		self.__column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical )
		
		GafferUI.Widget.__init__( self, self.__column )

		self.__color = color
		self.__defaultColor = color

		self.__sliders = {}

		self.__sliders["r"] = ColorSlider( color, "r" )
		self.__sliders["g"] = ColorSlider( color, "g" )
		self.__sliders["b"] = ColorSlider( color, "b" )
		self.__sliders["a"] = ColorSlider( color, "a" )
		self.__column.append( self.__sliders["r"] )
		self.__column.append( self.__sliders["g"] )
		self.__column.append( self.__sliders["b"] )
		self.__column.append( self.__sliders["a"] )

		self.__sliders["h"] = ColorSlider( color, "h" )
		self.__sliders["s"] = ColorSlider( color, "s" )
		self.__sliders["v"] = ColorSlider( color, "v" )
		self.__column.append( self.__sliders["h"] )
		self.__column.append( self.__sliders["s"] )
		self.__column.append( self.__sliders["v"] )

		self.__sliderConnections = []
		for s in self.__sliders.values() :
			self.__sliderConnections.append( s.valueChangedSignal().connect( Gaffer.WeakMethod( self.__sliderChanged ) ) )

		swatchRow = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal )
		self.__initialColorSwatch = GafferUI.ColorSwatch( color )		
		self.__initialColorPressConnection = self.__initialColorSwatch.buttonPressSignal().connect( Gaffer.WeakMethod( self.__initialColorPress ) )
		swatchRow.append( self.__initialColorSwatch, expand=True )
		self.__colorSwatch = GafferUI.ColorSwatch( color )
		swatchRow.append( self.__colorSwatch, expand=True )
		self.__column.append( swatchRow, expand=True )

		self.__colorChangedSignal = Gaffer.Signal2()
		
		self.__setSlidersFromColor()
	
	## The default color starts as the value passed when creating the dialogue.
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

	## A signal emitted whenever the color is changed. Slots should
	# have the signature slot( ColorChooser, reason ). The reason
	# argument may be passed either a ColorChooser.ColorChangedReason
	# or a Slider.PositionChangedReason to describe the reason for the
	# change.
	def colorChangedSignal( self ) :
	
		return self.__colorChangedSignal

	def __initialColorPress( self, button, event ) :
	
		self.__setColorInternal( self.getInitialColor(), self.ColorChangedReason.Reset )

	def __sliderChanged( self, slider, reason ) :
		
		newColor = self.__color.__class__( self.__color )	
		if slider.component in ( "r", "g", "b", "a" ) :
			a = { "r" : 0, "g" : 1, "b" : 2, "a" : 3 }[slider.component]
			newColor[a] = slider.getValue()
		else :
			newColor[0] = self.__sliders["h"].getValue()
			newColor[1] = self.__sliders["s"].getValue()
			newColor[2] = self.__sliders["v"].getValue()
			newColor = newColor.hsvToRGB()
			
		for slider in self.__sliders.values() :
			slider.setColor( newColor )		

		self.__setColorInternal( newColor, reason )
	
	def __setColorInternal( self, color, reason ) :
	
		dragBeginOrEnd = reason in (
			GafferUI.NumericSlider.PositionChangedReason.DragBegin,
			GafferUI.NumericSlider.PositionChangedReason.DragEnd
		)
		if color != self.__color or dragBeginOrEnd :
			# we never optimise away drag begin or end, because it's important
			# that they emit in pairs.		
			self.__color = color
			self.__setSlidersFromColor()
			self.__colorSwatch.setColor( color )
		
			self.__colorChangedSignal( self, reason )
		
	def __setSlidersFromColor( self ) :
	
		with Gaffer.BlockedConnection( self.__sliderConnections ) :
	
			c = self.getColor()

			for slider in self.__sliders.values() :
				slider.setColor( c )		

			self.__sliders["r"].setValue( c[0] )
			self.__sliders["g"].setValue( c[1] )
			self.__sliders["b"].setValue( c[2] )
			
			if c.dimensions() == 4 :
				self.__sliders["a"].setValue( c[3] )
				self.__sliders["a"].setVisible( True )
			else :
				self.__sliders["a"].setVisible( False )

			c = c.rgbToHSV()
			self.__sliders["h"].setValue( c[0] )
			self.__sliders["s"].setValue( c[1] )
			self.__sliders["v"].setValue( c[2] )
