##########################################################################
#
#  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

import functools

import IECore

import Gaffer
import GafferUI

from GafferUI.PlugValueWidget import sole

Gaffer.Metadata.registerNode(

	GafferUI.View,

	"nodeToolbar:top:type", "GafferUI.StandardNodeToolbar.top",

	plugs = {

		"*" : [

			"toolbarLayout:section", "Top",

		],

		"in" : [

			"plugValueWidget:type", "",

		],

		"editScope" : [

			# Most Views don't yet have any functionality that
			# uses EditScopes, so we'll opt in to showing the
			# widget on specific subclasses.
			"plugValueWidget:type", "",

		],

		"user" : [

			"plugValueWidget:type", "",

		],

	}

)

##########################################################################
# DisplayTransform
##########################################################################

Gaffer.Metadata.registerNode(

	GafferUI.View,

	plugs = {

		"displayTransform" : [

			"plugValueWidget:type", "GafferUI.LayoutPlugValueWidget",
			"layoutPlugValueWidget:orientation", "horizontal",
			"label", "",

		],

		"displayTransform.name" : [

			"description",
			"""
			The colour transform used for correcting the Viewer output for display.
			""",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
			"label", "",
			"layout:width", 100,

			"presetNames", lambda plug : IECore.StringVectorData( GafferUI.View.DisplayTransform.registeredDisplayTransforms() ),
			"presetValues", lambda plug : IECore.StringVectorData( GafferUI.View.DisplayTransform.registeredDisplayTransforms() ),

		],

		"displayTransform.soloChannel" : [

			"plugValueWidget:type", "GafferUI.ViewUI._SoloChannelPlugValueWidget",
			"label", "",

		],

		"displayTransform.clipping" : [

			"description",
			"""
			Highlights the regions in which the colour values go above 1 or below 0.
			""",

			"plugValueWidget:type", "GafferUI.ViewUI._TogglePlugValueWidget",
			"togglePlugValueWidget:imagePrefix", "clipping",
			"togglePlugValueWidget:defaultToggleValue", True,

		],

		"displayTransform.exposure" : [

			"description",
			"""
			Applies an exposure adjustment to the image.
			""",

			"plugValueWidget:type", "GafferUI.ViewUI._TogglePlugValueWidget",
			"togglePlugValueWidget:imagePrefix", "exposure",
			"togglePlugValueWidget:defaultToggleValue", 1,

		],

		"displayTransform.gamma" : [

			"description",
			"""
			Applies a gamma correction to the image.
			""",

			"plugValueWidget:type", "GafferUI.ViewUI._TogglePlugValueWidget",
			"togglePlugValueWidget:imagePrefix", "gamma",
			"togglePlugValueWidget:defaultToggleValue", 2,

		],

		"displayTransform.absolute" : [

			"description",
			"""
			Converts negative values to positive.
			""",

			"layout:visibilityActivator", False,

		],

	}

)

class _SoloChannelPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		self.__button = GafferUI.MenuButton(
			image = "soloChannel-1.png",
			hasFrame = False,
			menu = GafferUI.Menu(
				Gaffer.WeakMethod( self.__menuDefinition ),
				title = "Channel",
			)
		)

		GafferUI.PlugValueWidget.__init__( self, self.__button, plug, **kw )

	def _updateFromValues( self, values, exception ) :

		self.__button.setImage( "soloChannel{0}.png".format( sole( values ) ) )

	def _updateFromEditable( self ) :

		self.__button.setEnabled( self._editable() )

	def __menuDefinition( self ) :

		with self.getContext() :
			soloChannel = self.getPlug().getValue()

		m = IECore.MenuDefinition()
		m.append(
			"/All",
			{
				"command" : functools.partial( Gaffer.WeakMethod( self.__setValue ), -1 ),
				"checkBox" : soloChannel == -1
			}
		)
		for name, value in [
			( "R", 0 ),
			( "G", 1 ),
			( "B", 2 ),
			( "A", 3 ),
		] :
			m.append(
				"/" + name,
				{
					"command" : functools.partial( Gaffer.WeakMethod( self.__setValue ), value ),
					"checkBox" : soloChannel == value,
					"shortCut" : name
				}
			)

		m.append( "/LuminanceDivider", { "divider" : True, })

		m.append(
				"/Luminance",
				{
					"command" : functools.partial( Gaffer.WeakMethod( self.__setValue ), -2 ),
					"checkBox" : soloChannel == -2,
					"shortCut" : "L"
				}
			)

		return m

	def __setValue( self, value, *unused ) :

		self.getPlug().setValue( value )

# Toggles between default value and the last non-default value
class _TogglePlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 2 )

		GafferUI.PlugValueWidget.__init__( self, row, plug, **kw )

		self.__imagePrefix = Gaffer.Metadata.value( plug, "togglePlugValueWidget:imagePrefix" )
		with row :

			self.__button = GafferUI.Button( "", self.__imagePrefix + "Off.png", hasFrame=False )
			self.__button.clickedSignal().connect( Gaffer.WeakMethod( self.__clicked ), scoped = False )

			if not isinstance( plug, Gaffer.BoolPlug ) :
				plugValueWidget = GafferUI.PlugValueWidget.create( plug, useTypeOnly=True )
				plugValueWidget.numericWidget().setFixedCharacterWidth( 5 )

		self.__toggleValue = Gaffer.Metadata.value( plug, "togglePlugValueWidget:defaultToggleValue" )

	def hasLabel( self ) :

		return True

	def getToolTip( self ) :

		result = GafferUI.PlugValueWidget.getToolTip( self )

		if result :
			result += "\n"
		result += "## Actions\n\n"
		result += "- Click to toggle to/from default value\n"

		return result

	def _updateFromValues( self, values, exception ) :

		value = sole( values )
		if value != self.getPlug().defaultValue() :
			self.__toggleValue = value
			self.__button.setImage( self.__imagePrefix + "On.png" )
		else :
			self.__button.setImage( self.__imagePrefix + "Off.png" )

	def _updateFromEditable( self ) :

		self.__button.setEnabled( self._editable() )

	def __clicked( self, button ) :

		with self.getContext() :
			value = self.getPlug().getValue()

		if value == self.getPlug().defaultValue() and self.__toggleValue is not None :
			self.getPlug().setValue( self.__toggleValue )
		else :
			self.getPlug().setToDefault()
