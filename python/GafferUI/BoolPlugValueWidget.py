##########################################################################
#
#  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
#  Copyright (c) 2012-2013, John Haddon. All rights reserved.
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

## Supported plug metadata :
#
# - "boolPlugValueWidget:displayMode", with a value of "checkBox", "switch" or "tool"
# - "boolPlugValueWidget:image", with the name of an image to display when displayMode is "tool"
class BoolPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, displayMode=GafferUI.BoolWidget.DisplayMode.CheckBox, **kw ) :

		self.__boolWidget = GafferUI.BoolWidget(
			displayMode = displayMode,
			image = Gaffer.Metadata.value( plug, "boolPlugValueWidget:image" )
		)

		GafferUI.PlugValueWidget.__init__( self, self.__boolWidget, plug, **kw )

		self._addPopupMenu( self.__boolWidget )

		self.__stateChangedConnection = self.__boolWidget.stateChangedSignal().connect( Gaffer.WeakMethod( self.__stateChanged ) )

		self._updateFromPlug()

	def boolWidget( self ) :

		return self.__boolWidget

	def setHighlighted( self, highlighted ) :

		GafferUI.PlugValueWidget.setHighlighted( self, highlighted )
		self.__boolWidget.setHighlighted( highlighted )

	def _updateFromPlug( self ) :

		if self.getPlug() is not None :

			with self.getContext() :
				try :
					value = self.getPlug().getValue()
				except :
					value = None

			if value is not None :
				with Gaffer.BlockedConnection( self.__stateChangedConnection ) :
					self.__boolWidget.setState( value )

			self.__boolWidget.setErrored( value is None )

			displayMode = Gaffer.Metadata.value( self.getPlug(), "boolPlugValueWidget:displayMode" )
			if displayMode is not None :
				displayMode = {
					"switch" : self.__boolWidget.DisplayMode.Switch,
					"checkBox" : self.__boolWidget.DisplayMode.CheckBox,
					"tool" : self.__boolWidget.DisplayMode.Tool,
				}.get( displayMode, self.__boolWidget.DisplayMode.CheckBox )
				self.__boolWidget.setDisplayMode( displayMode )

			## \todo Perhaps this styling should be provided by the BoolWidget itself?
			animated = Gaffer.Animation.isAnimated( self.getPlug() )
			widgetAnimated = GafferUI._Variant.fromVariant( self.__boolWidget._qtWidget().property( "gafferAnimated" ) ) or False
			if widgetAnimated != animated :
				self.__boolWidget._qtWidget().setProperty( "gafferAnimated", GafferUI._Variant.toVariant( bool( animated ) ) )
				self.__boolWidget._repolish()

		self.__boolWidget.setEnabled( self._editable( canEditAnimation = True ) )

	def __stateChanged( self, widget ) :

		self.__setPlugValue()

		return False

	def __setPlugValue( self ) :

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :

			if Gaffer.Animation.isAnimated( self.getPlug() ) :
				curve = Gaffer.Animation.acquire( self.getPlug() )
				curve.addKey(
					Gaffer.Animation.Key(
						time = self.getContext().getTime(),
						value = self.__boolWidget.getState(),
						type = Gaffer.Animation.Type.Step
					)
				)
			else :
				self.getPlug().setValue( self.__boolWidget.getState() )

GafferUI.PlugValueWidget.registerType( Gaffer.BoolPlug, BoolPlugValueWidget )
