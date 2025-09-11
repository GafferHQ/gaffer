##########################################################################
#
#  Copyright (c) 2025, Cinesite VFX Ltd. All rights reserved.
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

from GafferUI.PlugValueWidget import sole

## PlugValueWidget with two main components :
#
# - A toggle to switch quickly between the default value and the last non-default value.
# - A second PlugValueWidget for editing the value directly as usual (omitted for BoolPlugs).
#
# Required metadata :
#
# - "togglePlugValueWidget:image:on" : The name of the image to be shown for non-default values.
# - "togglePlugValueWidget:image:on" : The name of the image to be shown for default values.
#
# Optional metadata :
#
# - "togglePlugValueWidget:defaultToggleValue" : The value to toggle to when first pressed.
# - "togglePlugValueWidget:customWidgetType" : Specifies the widget type to be used for editing
#   the value directly.
class TogglePlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 2 )

		GafferUI.PlugValueWidget.__init__( self, row, plug, **kw )

		self.__onImage = Gaffer.Metadata.value( plug, "togglePlugValueWidget:image:on" ) or "warningSmall.png"
		self.__offImage = Gaffer.Metadata.value( plug, "togglePlugValueWidget:image:off" ) or "warningSmall.png"
		with row :

			self.__button = GafferUI.Button( "", self.__offImage, hasFrame=False )
			self.__button.clickedSignal().connect( Gaffer.WeakMethod( self.__clicked ) )

			self.__plugValueWidget = None
			if not isinstance( plug, Gaffer.BoolPlug ) :
				self.__plugValueWidget = GafferUI.PlugValueWidget.create( plug, typeMetadata = "togglePlugValueWidget:customWidgetType" )

		self.__toggleValue = Gaffer.Metadata.value( plug, "togglePlugValueWidget:defaultToggleValue" )
		if self.__toggleValue is None and isinstance( plug, Gaffer.BoolPlug ) :
			self.__toggleValue = not plug.defaultValue()

	def hasLabel( self ) :

		return True

	def getToolTip( self ) :

		result = GafferUI.PlugValueWidget.getToolTip( self )

		if result :
			result += "\n\n"
		result += "## Actions\n\n"
		result += "- Click to toggle to/from default value\n"

		return result

	def _updateFromValues( self, values, exception ) :

		value = sole( values )
		if value != self.getPlug().defaultValue() :
			self.__toggleValue = value
			self.__button.setImage( self.__onImage )
		else :
			self.__button.setImage( self.__offImage )

	def _updateFromEditable( self ) :

		self.__button.setEnabled( self._editable() )

	def __clicked( self, button ) :

		with self.context() :
			value = self.getPlug().getValue()

		if value == self.getPlug().defaultValue() :
			if self.__toggleValue is not None :
				self.getPlug().setValue( self.__toggleValue )
			if isinstance( self.__plugValueWidget, GafferUI.StringPlugValueWidget ) :
				# Hack to update TextWidget now, otherwise StringPlugValueWidget won't update
				# it until the next idle event. This allows us to select the incoming text for
				# easy editing.
				self.__plugValueWidget.textWidget().setText( self.__toggleValue )
				self.__plugValueWidget.textWidget().setSelection( 0, None ) # All
				self.__plugValueWidget.textWidget().grabFocus()
		else :
			self.getPlug().setToDefault()
