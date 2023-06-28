##########################################################################
#
#  Copyright (c) 2013-2014, John Haddon. All rights reserved.
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

import GafferOSL

import imath
import functools

_channelNamesOptions = {
	"RGB" : IECore.Color3fData( imath.Color3f( 1 ) ),
	"RGBA" : IECore.Color4fData( imath.Color4f( 1 ) ),
	"R" : IECore.FloatData( 1 ),
	"G" : IECore.FloatData( 1 ),
	"B" : IECore.FloatData( 1 ),
	"A" : IECore.FloatData( 1 ),
	"customChannel" : IECore.FloatData( 1 ),
	"customLayer" : IECore.Color3fData( imath.Color3f( 1 ) ),
	"customLayerRGBA" : IECore.Color4fData( imath.Color4f( 1 ) ),
	"closure" : None,
}

##########################################################################
# _ChannelsFooter
##########################################################################

class _ChannelsFooter( GafferUI.PlugValueWidget ) :

	def __init__( self, plug ) :

		row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal )

		GafferUI.PlugValueWidget.__init__( self, row, plug )

		with row :

				GafferUI.Spacer( imath.V2i( GafferUI.PlugWidget.labelWidth(), 1 ) )

				self.__menuButton = GafferUI.MenuButton(
					image = "plus.png",
					hasFrame = False,
					menu = GafferUI.Menu(
						Gaffer.WeakMethod( self.__menuDefinition ),
						title = "Add Input"
					),
					toolTip = "Add Input"
				)

				GafferUI.Spacer( imath.V2i( 1 ), imath.V2i( 999999, 1 ), parenting = { "expand" : True } )

	def _updateFromEditable( self ) :

		self.__menuButton.setEnabled( self._editable() )

	def __menuDefinition( self ) :

		result = IECore.MenuDefinition()
		usedNames = set()
		for p in self.getPlug().children():
			if not Gaffer.PlugAlgo.dependsOnCompute( p ) :
				usedNames.add( p["name"].getValue() )

		# Use a fixed order for some standard options that we want to list in a specific order
		sortedOptions = []
		for label in ["RGB", "RGBA", "R", "G", "B", "A" ]:
			sortedOptions.append( (label, _channelNamesOptions[label] ) )

		for label, defaultData in sorted( _channelNamesOptions.items() ):
			if not label in [ i[0] for i in sortedOptions ]:
				sortedOptions.append( (label, defaultData) )

		categories = { "Standard" : [], "Custom" : [], "Advanced" : [] }
		for label, defaultData in sortedOptions:
			if label == "closure":
				categories["Advanced"].append( ( label, label, defaultData ) )
			else:
				bareLabel = label.replace( "RGBA", "" ).replace( "RGB", "" )
				channelName = bareLabel
				if label.startswith( "custom" ):
					if channelName in usedNames:
						suffix = 2
						while True:
							channelName = bareLabel + str( suffix )
							if not channelName in usedNames:
								break
							suffix += 1
					categories["Custom"].append( ( label, channelName, defaultData ) )
				else:
					if channelName in usedNames:
						continue
					categories["Standard"].append( ( label, channelName, defaultData ) )


		for category in [ "Standard", "Custom", "Advanced" ]:
			for ( menuLabel, channelName, defaultData ) in categories[category]:
				result.append(
					"/" + category + "/" + menuLabel,
					{
						"command" : functools.partial( Gaffer.WeakMethod( self.__addPlug ), channelName, defaultData ),
					}
				)

		return result

	def __addPlug( self, name, defaultData ) :

		alphaValue = None

		if isinstance( defaultData, IECore.Color4fData ):
			alphaValue = Gaffer.FloatPlug( "value", Gaffer.Plug.Direction.In, defaultData.value.a )
			defaultData = IECore.Color3fData( imath.Color3f( defaultData.value.r, defaultData.value.g, defaultData.value.b ) )

		if defaultData == None:
			plugName = "closure"
			name = ""
			valuePlug = GafferOSL.ClosurePlug( "value" )
		else:
			plugName = "channel"
			valuePlug = Gaffer.PlugAlgo.createPlugFromData( "value", Gaffer.Plug.Direction.In, Gaffer.Plug.Flags.Default, defaultData )

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			self.getPlug().addChild( Gaffer.NameValuePlug( name, valuePlug, True, plugName, Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
			if alphaValue:
				self.getPlug().addChild(
					Gaffer.NameValuePlug( name + ".A" if name else "A", alphaValue, True, plugName, Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
				)

def __channelLabelFromPlug( plug ):
	if plug.typeId() == GafferOSL.ClosurePlug.staticTypeId():
		return plug.parent().getName()
	elif plug.typeId() == Gaffer.Color3fPlug.staticTypeId() and plug.parent()["name"].getValue() == "":
		return "[RGB]"
	else:
		return plug.parent()["name"].getValue()

##########################################################################
# Metadata
##########################################################################

Gaffer.Metadata.registerNode(

	GafferOSL.OSLImage,

	"description",
	"""
	Executes OSL shaders to perform image processing. Use the shaders from
	the OSL/ImageProcessing menu to read values from the input image and
	then write values back to it.
	""",

	"plugAdderOptions", IECore.CompoundData( _channelNamesOptions ),

	"layout:activator:defaultFormatActive", lambda node : not node["in"].getInput(),

	plugs = {
		"defaultFormat" : [
			"description",
			"""
			The resolution and aspect ratio to output when there is no input image provided.
			""",
			"layout:activator", "defaultFormatActive",
		],
		"channels" : [
			"description",
			"""
			Define image channels to output by adding child plugs and connecting
			corresponding OSL shaders.  You can drive RGB layers with a color,
			or connect individual channels to a float.

			If you want to add multiple channels at once, you can also add a closure plug,
			which can accept a connection from an OSLCode with a combined output closure.
 			""",
			"layout:customWidget:footer:widgetType", "GafferOSLUI.OSLImageUI._ChannelsFooter",
			"layout:customWidget:footer:index", -1,
			"nodule:type", "GafferUI::CompoundNodule",
			"noduleLayout:section", "left",
			"noduleLayout:spacing", 0.2,
			"plugValueWidget:type", "GafferUI.LayoutPlugValueWidget",

			# Add + button for showing and hiding parameters in the GraphEditor
			"noduleLayout:customGadget:addButton:gadgetType", "GafferOSLUI.OSLImageUI.PlugAdder",
		],
		"channels.*" : [

			"deletable", True,
			# Although the parameters plug is positioned
			# as we want above, we must also register
			# appropriate values for each individual parameter,
			# for the case where they get promoted to a box
			# individually.
			"noduleLayout:section", "left",
			"nodule:type", "GafferUI::CompoundNodule",
			"nameValuePlugPlugValueWidget:ignoreNamePlug", lambda plug : isinstance( plug["value"], GafferOSL.ClosurePlug ),
		],
		"channels.*.name" : [
			"nodule:type", "",
			"stringPlugValueWidget:placeholderText", lambda plug : "[RGB]" if isinstance( plug.parent()["value"], Gaffer.Color3fPlug ) else None,
		],
		"channels.*.enabled" : [
			"nodule:type", "",
		],
		"channels.*.value" : [

			# Although the parameters plug is positioned
			# as we want above, we must also register
			# appropriate values for each individual parameter,
			# for the case where they get promoted to a box
			# individually.
			"noduleLayout:section", "left",
			"noduleLayout:label", __channelLabelFromPlug,
			"ui:visibleDimensions", lambda plug : 2 if hasattr( plug, "interpretation" ) and plug.interpretation() == IECore.GeometricData.Interpretation.UV else None,
		],
	}

)
