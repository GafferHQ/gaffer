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

	def __init__( self, plug, image, defaultToggleValue = None, **kw ) :
		
		row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal )
		
		GafferUI.PlugValueWidget.__init__( self, row, plug, **kw )

		with row :
			
			button = GafferUI.Button( "", image, hasFrame=False )
			self.__clickedConnection = button.clickedSignal().connect( Gaffer.WeakMethod( self.__clicked ) )
			
			plugValueWidget = GafferUI.PlugValueWidget.create( plug, useTypeOnly=True )
			plugValueWidget.numericWidget().setCharacterWidth( 5 )
		
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
		
		self.setEnabled( self.getPlug().settable() )
		
	def __clicked( self, button ) :
	
		with self.getContext() :
			value = self.getPlug().getValue()

		if value == self.getPlug().defaultValue() and self.__toggleValue is not None :
			self.getPlug().setValue( self.__toggleValue )
		else :
			self.getPlug().setToDefault()

## Exposure and gamma
	
GafferUI.PlugValueWidget.registerCreator(
	GafferImageUI.ImageView.staticTypeId(),
	"exposure",
	_TogglePlugValueWidget,
	image ="exposure.png",
	defaultToggleValue = 1,
)

GafferUI.PlugValueWidget.registerCreator(
	GafferImageUI.ImageView.staticTypeId(),
	"gamma",
	_TogglePlugValueWidget,
	image ="gamma.png",
	defaultToggleValue = 2,
)

## Display Transform

GafferUI.Metadata.registerPlugValue( GafferImageUI.ImageView, "displayTransform", "label", "" )

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
	GafferImageUI.ImageView.staticTypeId(),
	"displayTransform",
	__displayTransformPlugValueWidgetCreator
)
