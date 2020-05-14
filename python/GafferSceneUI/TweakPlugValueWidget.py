##########################################################################
#
#  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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
import GafferScene

from Qt import QtWidgets

# Widget for TweakPlug, which is used to build tweak nodes such as ShaderTweaks
# and CameraTweaks.  Shows a value plug that you can use to specify a tweak value, along with
# a target parameter name, an enabled plug, and a mode.  The mode can be "Replace",
# or "Add"/"Subtract"/"Multiply" if the plug is numeric,
# or "Remove" if the metadata "tweakPlugValueWidget:allowRemove" is set
class TweakPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug ) :

		self.__row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 )

		GafferUI.PlugValueWidget.__init__( self, self.__row, plug )

		nameWidget = GafferUI.StringPlugValueWidget( plug["name"] )
		nameWidget.textWidget()._qtWidget().setFixedWidth( GafferUI.PlugWidget.labelWidth() )

		self.__row.append( nameWidget,
			verticalAlignment = GafferUI.Label.VerticalAlignment.Top
		)

		self.__row.append(
			GafferUI.BoolPlugValueWidget(
				plug["enabled"],
				displayMode = GafferUI.BoolWidget.DisplayMode.Switch
			),
			verticalAlignment = GafferUI.Label.VerticalAlignment.Top,
		)

		modeWidget = GafferUI.PlugValueWidget.create( plug["mode"] )
		modeWidget._qtWidget().setFixedWidth( 80 )
		modeWidget._qtWidget().layout().setSizeConstraint( QtWidgets.QLayout.SetDefaultConstraint )
		self.__row.append( modeWidget )

		self.__row.append( GafferUI.PlugValueWidget.create( plug["value"] ), expand = True )

		self._updateFromPlug()

	def setPlug( self, plug ) :

		GafferUI.PlugValueWidget.setPlug( self, plug )

		self.__row[0].setPlug( plug["name"] )
		self.__row[1].setPlug( plug["enabled"] )
		self.__row[2].setPlug( plug["mode"] )
		self.__row[3].setPlug( plug["value"] )

	def hasLabel( self ) :

		return True

	def childPlugValueWidget( self, childPlug ) :

		for w in self.__row :
			if w.getPlug().isSame( childPlug ) :
				return w

		return None

	def setReadOnly( self, readOnly ) :

		if readOnly == self.getReadOnly() :
			return

		GafferUI.PlugValueWidget.setReadOnly( self, readOnly )

		for w in self.__row :
			w.setReadOnly( readOnly )

	def _updateFromPlug( self ) :

		with self.getContext() :
			enabled = self.getPlug()["enabled"].getValue()

		for i in ( 0, 2, 3 ) :
			self.__row[i].setEnabled( enabled )

def __deletePlug( plug ) :

	with Gaffer.UndoScope( plug.ancestor( Gaffer.ScriptNode ) ) :
		plug.parent().removeChild( plug )

def __plugPopupMenu( menuDefinition, plugValueWidget ):

	plug = plugValueWidget.getPlug()
	if not isinstance( plug, GafferScene.TweakPlug ) :
		plug = plug.ancestor( GafferScene.TweakPlug )

	if not isinstance( plug, GafferScene.TweakPlug ):
		return

	menuDefinition.append( "/DeleteDivider", { "divider" : True } )
	menuDefinition.append(
		"/Delete",
		{
			"command" : functools.partial( __deletePlug, plug ),
			"active" : not plugValueWidget.getReadOnly() and not Gaffer.MetadataAlgo.readOnly( plug.parent() )
		}
	)

GafferUI.PlugValueWidget.popupMenuSignal().connect( __plugPopupMenu, scoped = False )

GafferUI.PlugValueWidget.registerType( GafferScene.TweakPlug, TweakPlugValueWidget )

# Metadata for child plugs

Gaffer.Metadata.registerValue(
	GafferScene.TweakPlug, "name",
	"description", "The name of the parameter to apply the tweak to."
)

Gaffer.Metadata.registerValue(
	GafferScene.TweakPlug, "mode",
	"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget"
)

def __validModes( plug ) :

	result = [ GafferScene.TweakPlug.Mode.Replace ]
	if hasattr( plug.parent()["value"], "hasMinValue" ) :
		result += [
			GafferScene.TweakPlug.Mode.Add,
			GafferScene.TweakPlug.Mode.Subtract,
			GafferScene.TweakPlug.Mode.Multiply
		]

	if Gaffer.Metadata.value( plug.parent(), "tweakPlugValueWidget:allowRemove" ) :
		result += [ GafferScene.TweakPlug.Mode.Remove ]

	return result

Gaffer.Metadata.registerValue(
	GafferScene.TweakPlug, "mode",
	"presetNames", lambda plug : IECore.StringVectorData( [ str( x ) for x in __validModes( plug ) ] )
)

Gaffer.Metadata.registerValue(
	GafferScene.TweakPlug, "mode",
	"presetValues", lambda plug : IECore.IntVectorData( [ int( x ) for x in __validModes( plug ) ] )
)

def __noduleLabel( plug ) :

	if not isinstance( plug, GafferScene.TweakPlug ) :
		plug = plug.parent()

	name = None
	with IECore.IgnoredExceptions( Exception ) :
		name = plug["name"].getValue()

	return name or plug.getName()

def __spreadsheetColumnName( plug ) :

	tweakPlug = plug.parent()
	if plug == tweakPlug["name"] :
		return plug.getName()

	# Use some heuristics to come up with a more helpful
	# column name.

	name = tweakPlug.getName()
	if name.startswith( "tweak" ) and tweakPlug["name"].source().direction() != Gaffer.Plug.Direction.Out :
		name = tweakPlug["name"].getValue()

	if name :
		return name + plug.getName().title()
	else :
		return plug.getName()

Gaffer.Metadata.registerValue( GafferScene.TweakPlug, "nodule:type", "GafferUI::CompoundNodule" )
Gaffer.Metadata.registerValue( GafferScene.TweakPlug, "*", "nodule:type", "" )
Gaffer.Metadata.registerValue( GafferScene.TweakPlug, "value", "nodule:type", "GafferUI::StandardNodule" )
Gaffer.Metadata.registerValue( GafferScene.TweakPlug, "noduleLayout:label", __noduleLabel )
Gaffer.Metadata.registerValue( GafferScene.TweakPlug, "value", "noduleLayout:label", __noduleLabel )
Gaffer.Metadata.registerValue( GafferScene.TweakPlug, "*", "spreadsheet:columnName", __spreadsheetColumnName )

