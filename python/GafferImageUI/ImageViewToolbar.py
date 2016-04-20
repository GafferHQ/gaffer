##########################################################################
#
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

import IECore

import Gaffer
import GafferUI
import GafferImageUI

##########################################################################
# _TogglePlugValueWidget
##########################################################################

# Toggles between default value and the last non-default value
class _TogglePlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, parenting = None ) :

		row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 2 )

		GafferUI.PlugValueWidget.__init__( self, row, plug, parenting = parenting )

		self.__imagePrefix = Gaffer.Metadata.plugValue( plug, "togglePlugValueWidget:imagePrefix" )
		with row :

			self.__button = GafferUI.Button( "", self.__imagePrefix + "Off.png", hasFrame=False )
			self.__clickedConnection = self.__button.clickedSignal().connect( Gaffer.WeakMethod( self.__clicked ) )

			if not isinstance( plug, Gaffer.BoolPlug ) :
				plugValueWidget = GafferUI.PlugValueWidget.create( plug, useTypeOnly=True )
				plugValueWidget.numericWidget().setFixedCharacterWidth( 5 )

		self.__toggleValue = Gaffer.Metadata.plugValue( plug, "togglePlugValueWidget:defaultToggleValue" )
		self._updateFromPlug()

	def hasLabel( self ) :

		return True

	def getToolTip( self ) :

		result = GafferUI.PlugValueWidget.getToolTip( self )

		result += "<ul>"
		result += "<li>Click to toggle to/from default value</li>"
		result += "<ul>"

		return result

	def _updateFromPlug( self ) :

		with self.getContext() :
			value = self.getPlug().getValue()

		if value != self.getPlug().defaultValue() :
			self.__toggleValue = value
			self.__button.setImage( self.__imagePrefix + "On.png" )
		else :
			self.__button.setImage( self.__imagePrefix + "Off.png" )

		self.setEnabled( self.getPlug().settable() )

	def __clicked( self, button ) :

		with self.getContext() :
			value = self.getPlug().getValue()

		if value == self.getPlug().defaultValue() and self.__toggleValue is not None :
			self.getPlug().setValue( self.__toggleValue )
		else :
			self.getPlug().setToDefault()

##########################################################################
# _DisplayTransformPlugValueWidget
##########################################################################

class _DisplayTransformPlugValueWidget( GafferUI.PresetsPlugValueWidget ) :

	def __init__( self, plug, parenting = None ) :

		GafferUI.PresetsPlugValueWidget.__init__( self, plug, parenting = parenting )

		## \todo Perhaps the layout could do this sort of thing for us
		# based on a metadata value?
		self._qtWidget().setFixedWidth( 100 )

##########################################################################
# _ColorInspectorPlugValueWidget
##########################################################################

class _ColorInspectorPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, parenting = None ) :

		frame = GafferUI.Frame( borderWidth = 4 )
		frame._qtWidget().setObjectName( "gafferDarker" )

		GafferUI.PlugValueWidget.__init__( self, frame, plug, parenting = parenting )

		with frame :

			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 ) :

				self.__positionLabel = GafferUI.Label()
				self.__positionLabel._qtWidget().setFixedWidth( 90 )

				self.__swatch = GafferUI.ColorSwatch()
				self.__swatch._qtWidget().setFixedWidth( 12 )
				self.__swatch._qtWidget().setFixedHeight( 12 )

				self.__rgbLabel = GafferUI.Label()

				GafferUI.Spacer( IECore.V2i( 20, 10 ), IECore.V2i( 20, 10 ) )

				self.__hsvLabel = GafferUI.Label()

	def _updateFromPlug( self ) :

		view = self.getPlug().node()

		## \todo We're getting the context from the view because our
		# own context hasn't been set properly. We need to fix that
		# properly, I think by having some sort of ContextSensitiveWidget
		# base class which inherits contexts from parents.
		with view.getContext() :
			pixel = self.getPlug()["pixel"].getValue()
			try :
				channelNames = view.viewportGadget().getPrimaryChild().getImage()["channelNames"].getValue()
				color = self.getPlug()["color"].getValue()
			except :
				channelNames = view.viewportGadget().getPrimaryChild().getImage()["channelNames"].defaultValue()
				color = self.getPlug()["color"].defaultValue()

		if "A" not in channelNames :
			color = IECore.Color3f( color[0], color[1], color[2] )

		self.__positionLabel.setText( "<b>XY : %d %d</b>" % ( pixel.x, pixel.y ) )
		self.__swatch.setColor( color )

		if isinstance( color, IECore.Color4f ) :
			self.__rgbLabel.setText( "<b>RGBA : %.3f %.3f %.3f %.3f</b>" % ( color.r, color.g, color.b, color.a ) )
		else :
			self.__rgbLabel.setText( "<b>RGB : %.3f %.3f %.3f</b>" % ( color.r, color.g, color.b ) )

		hsv = color.rgbToHSV()
		self.__hsvLabel.setText( "<b>HSV : %.3f %.3f %.3f</b>" % ( hsv.r, hsv.g, hsv.b ) )

##########################################################################
# Metadata registration.
##########################################################################

Gaffer.Metadata.registerNode(

	GafferImageUI.ImageView,

	"nodeToolbar:bottom:type", "GafferUI.StandardNodeToolbar.bottom",

	plugs = {

		"clipping" : [

			"description",
			"""
			Highlights the regions in which the colour values go above 1 or below 0.
			""",

			"plugValueWidget:type", "GafferImageUI.ImageViewToolbar._TogglePlugValueWidget",
			"togglePlugValueWidget:imagePrefix", "clipping",
			"togglePlugValueWidget:defaultToggleValue", True,
			"toolbarLayout:divider", True,

		],

		"exposure" : [

			"description",
			"""
			Applies an exposure adjustment to the image.
			""",

			"plugValueWidget:type", "GafferImageUI.ImageViewToolbar._TogglePlugValueWidget",
			"togglePlugValueWidget:imagePrefix", "exposure",
			"togglePlugValueWidget:defaultToggleValue", 1,

		],

		"gamma" : [

			"description",
			"""
			Applies a gamma correction to the image.
			""",

			"plugValueWidget:type", "GafferImageUI.ImageViewToolbar._TogglePlugValueWidget",
			"togglePlugValueWidget:imagePrefix", "gamma",
			"togglePlugValueWidget:defaultToggleValue", 2,

		],

		"displayTransform" : [

			"description",
			"""
			Applies colour space transformations for viewing the image correctly.
			""",


			"plugValueWidget:type", "GafferImageUI.ImageViewToolbar._DisplayTransformPlugValueWidget",
			"label", "",

			"presetNames", lambda plug : IECore.StringVectorData( GafferImageUI.ImageView.registeredDisplayTransforms() ),
			"presetValues", lambda plug : IECore.StringVectorData( GafferImageUI.ImageView.registeredDisplayTransforms() ),

		],

		"colorInspector" : [

			"plugValueWidget:type", "GafferImageUI.ImageViewToolbar._ColorInspectorPlugValueWidget",
			"label", "",
			"toolbarLayout:section", "Bottom",

		],

	}

)
