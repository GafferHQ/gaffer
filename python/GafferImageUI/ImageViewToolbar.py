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

import Gaffer
import GafferUI
import GafferImageUI

# Toggles between default value and the last non-default value
class _TogglePlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, imagePrefix, defaultToggleValue = None, **kw ) :

		row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 2 )

		GafferUI.PlugValueWidget.__init__( self, row, plug, **kw )

		self.__imagePrefix = imagePrefix
		with row :

			self.__button = GafferUI.Button( "", self.__imagePrefix + "Off.png", hasFrame=False )
			self.__clickedConnection = self.__button.clickedSignal().connect( Gaffer.WeakMethod( self.__clicked ) )

			if not isinstance( plug, Gaffer.BoolPlug ) :
				plugValueWidget = GafferUI.PlugValueWidget.create( plug, useTypeOnly=True )
				plugValueWidget.numericWidget().setFixedCharacterWidth( 5 )

		self.__toggleValue = defaultToggleValue
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

## Clipping, exposure and gamma

GafferUI.PlugValueWidget.registerCreator(
	GafferImageUI.ImageView,
	"clipping",
	_TogglePlugValueWidget,
	imagePrefix ="clipping",
	defaultToggleValue = True,
)

Gaffer.Metadata.registerPlugValue( GafferImageUI.ImageView, "clipping", "divider", True )

Gaffer.Metadata.registerPlugDescription( GafferImageUI.ImageView, "clipping",
	"Highlights the regions in which the colour values go above 1 or below 0."
)

GafferUI.PlugValueWidget.registerCreator(
	GafferImageUI.ImageView,
	"exposure",
	_TogglePlugValueWidget,
	imagePrefix ="exposure",
	defaultToggleValue = 1,
)

Gaffer.Metadata.registerPlugDescription( GafferImageUI.ImageView, "exposure",
	"Applies an exposure adjustment to the image."
)

GafferUI.PlugValueWidget.registerCreator(
	GafferImageUI.ImageView,
	"gamma",
	_TogglePlugValueWidget,
	imagePrefix ="gamma",
	defaultToggleValue = 2,
)

Gaffer.Metadata.registerPlugDescription( GafferImageUI.ImageView, "gamma",
	"Applies a gamma correction to the image."
)

## Display Transform

Gaffer.Metadata.registerPlugValue( GafferImageUI.ImageView, "displayTransform", "label", "" )

def __displayTransformPlugValueWidgetCreator( plug ) :

	widget = GafferUI.EnumPlugValueWidget(
		plug,
		labelsAndValues = zip(
			GafferImageUI.ImageView.registeredDisplayTransforms(),
			GafferImageUI.ImageView.registeredDisplayTransforms(),
		),
	)

	widget.selectionMenu()._qtWidget().setFixedWidth( 100 )

	return widget

GafferUI.PlugValueWidget.registerCreator(
	GafferImageUI.ImageView,
	"displayTransform",
	__displayTransformPlugValueWidgetCreator
)

Gaffer.Metadata.registerPlugDescription( GafferImageUI.ImageView, "displayTransform",
	"Applies colour space transformations for viewing the image correctly."
)
