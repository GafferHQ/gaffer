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

from GafferUI.PlugValueWidget import sole

## Supported plug metadata :
#
# - "boolPlugValueWidget:displayMode", with a value of "checkBox", "switch" or "tool"
# - "boolPlugValueWidget:image", with the name of an image to display when displayMode is "tool"
class BoolPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plugs, displayMode=GafferUI.BoolWidget.DisplayMode.CheckBox, **kw ) :

		self.__boolWidget = GafferUI.BoolWidget( displayMode = displayMode )
		GafferUI.PlugValueWidget.__init__( self, self.__boolWidget, plugs, **kw )

		self._addPopupMenu( self.__boolWidget )

		self.__stateChangedConnection = self.__boolWidget.stateChangedSignal().connect( Gaffer.WeakMethod( self.__stateChanged ), scoped = False )

	def boolWidget( self ) :

		return self.__boolWidget

	def setHighlighted( self, highlighted ) :

		GafferUI.PlugValueWidget.setHighlighted( self, highlighted )
		self.__boolWidget.setHighlighted( highlighted )

	def _updateFromValues( self, values, exception ) :

		# Value and error status

		value = sole( values )
		with Gaffer.Signals.BlockedConnection( self.__stateChangedConnection ) :
			self.__boolWidget.setState( value if value is not None else self.__boolWidget.State.Indeterminate )

		self.__boolWidget.setErrored( exception is not None )

		# Animation state

		animated = any( Gaffer.Animation.isAnimated( p ) for p in self.getPlugs() )
		## \todo Perhaps this styling should be provided by the BoolWidget itself?
		widgetAnimated = GafferUI._Variant.fromVariant( self.__boolWidget._qtWidget().property( "gafferAnimated" ) ) or False
		if widgetAnimated != animated :
			self.__boolWidget._qtWidget().setProperty( "gafferAnimated", GafferUI._Variant.toVariant( bool( animated ) ) )
			self.__boolWidget._repolish()

	def _updateFromMetadata( self ) :

		self.__boolWidget.setImage(
			sole( Gaffer.Metadata.value( p, "boolPlugValueWidget:image" ) for p in self.getPlugs() )
		)

		displayMode = sole( Gaffer.Metadata.value( p, "boolPlugValueWidget:displayMode" ) for p in self.getPlugs() )
		if displayMode is not None :
			displayMode = {
				"switch" : self.__boolWidget.DisplayMode.Switch,
				"checkBox" : self.__boolWidget.DisplayMode.CheckBox,
				"tool" : self.__boolWidget.DisplayMode.Tool,
			}.get( displayMode, self.__boolWidget.DisplayMode.CheckBox )
			self.__boolWidget.setDisplayMode( displayMode )

	def _updateFromEditable( self ) :

		self.__boolWidget.setEnabled( self._editable( canEditAnimation = True ) )

	def __stateChanged( self, widget ) :

		self.__setPlugValues()

		return False

	def __setPlugValues( self ) :

		value = self.__boolWidget.getState()
		assert( value != self.__boolWidget.State.Indeterminate ) # Should be set by us, not by user action

		with Gaffer.UndoScope( next( iter( self.getPlugs() ) ).ancestor( Gaffer.ScriptNode ) ) :
			for plug in self.getPlugs() :

				if Gaffer.Animation.isAnimated( plug ) :
					curve = Gaffer.Animation.acquire( plug )
					curve.addKey(
						Gaffer.Animation.Key(
							time = self.getContext().getTime(),
							value = value,
							interpolation = Gaffer.Animation.Interpolation.Constant
						)
					)
				else :
					plug.setValue( value )

GafferUI.PlugValueWidget.registerType( Gaffer.BoolPlug, BoolPlugValueWidget )
