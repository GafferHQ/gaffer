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
import re

import IECore

import Gaffer
import GafferUI

from Qt import QtWidgets

# Widget for TweakPlug, which is used to build tweak nodes such as ShaderTweaks
# and CameraTweaks.  Shows a value plug that you can use to specify a tweak value, along with
# a target parameter name, an enabled plug, and a mode.  The mode can be "Replace",
# or "Add"/"Subtract"/"Multiply"/"Min"/"Max" if the plug is numeric,
# or "ListAppend"/"ListPrepend"/"ListRemove" if the plug is a list,
# or "Remove" if the metadata "tweakPlugValueWidget:allowRemove" is set,
# or "Create" if the metadata "tweakPlugValueWidget:allowCreate" is set.
class TweakPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plugs ) :

		valueWidget = GafferUI.PlugValueWidget.create( self.__childPlugs( plugs, "value" ) )

		self.__row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 )

		GafferUI.PlugValueWidget.__init__( self, self.__row, plugs )

		nameWidget = GafferUI.StringPlugValueWidget( self.__childPlugs( plugs, "name" ) )
		nameWidget.textWidget()._qtWidget().setFixedWidth( GafferUI.PlugWidget.labelWidth() )

		self.__row.append( nameWidget,
			verticalAlignment = GafferUI.Label.VerticalAlignment.Top
		)

		self.__row.append(
			GafferUI.BoolPlugValueWidget(
				self.__childPlugs( plugs, "enabled" ),
				displayMode = GafferUI.BoolWidget.DisplayMode.Switch
			),
			verticalAlignment = GafferUI.Label.VerticalAlignment.Top,
		)

		modeWidget = GafferUI.PlugValueWidget.create( self.__childPlugs( plugs, "mode" ) )
		modeWidget._qtWidget().setFixedWidth( 80 )
		modeWidget._qtWidget().layout().setSizeConstraint( QtWidgets.QLayout.SetDefaultConstraint )
		self.__row.append( modeWidget, verticalAlignment = GafferUI.Label.VerticalAlignment.Top )

		self.__row.append( valueWidget, expand = True )

		self._updateFromPlugs()

	def setPlugs( self, plugs ) :

		GafferUI.PlugValueWidget.setPlugs( self, plugs )

		self.__row[0].setPlugs( { p["name"] for p in plugs } )
		self.__row[1].setPlugs( { p["enabled"] for p in plugs } )
		self.__row[2].setPlugs( { p["mode"] for p in plugs } )
		self.__row[3].setPlugs( { p["value"] for p in plugs } )

	def hasLabel( self ) :

		return True

	def childPlugValueWidget( self, childPlug ) :

		for w in self.__row :
			if childPlug in w.getPlugs() :
				return w

		return None

	def setNameVisible( self, visible ) :

		self.__row[0].setVisible( visible )

	def getNameVisible( self ) :

		return self.__row[0].getVisible()

	def _updateFromPlugs( self ) :

		with self.getContext() :
			enabled = all( p["enabled"].getValue() for p in self.getPlugs() )

		for i in ( 0, 2, 3 ) :
			self.__row[i].setEnabled( enabled )

	@staticmethod
	def __childPlugs( plugs, childName ) :

		# Special cases to provide plugs in a form compatible
		# with old PlugValueWidgets constructors which don't
		# yet support multiple plugs.
		if isinstance( plugs, Gaffer.Plug ) :
			return plugs[childName]
		elif plugs is None or not len( plugs ) :
			return None
		elif len( plugs ) == 1 :
			return next( iter( plugs ) )[childName]
		else :
			# Standard case. Once all PlugValueWidgets have
			# been updated to support multiple plugs, we can
			# use this all the time.
			return { p[childName] for p in plugs }

GafferUI.PlugValueWidget.registerType( Gaffer.TweakPlug, TweakPlugValueWidget )

# Metadata

Gaffer.Metadata.registerValue( Gaffer.TweakPlug, "deletable", lambda plug : plug.getFlags( Gaffer.Plug.Flags.Dynamic ) )

Gaffer.Metadata.registerValue(
	Gaffer.TweakPlug, "name",
	"description", "The name of the parameter to apply the tweak to."
)

Gaffer.Metadata.registerValue(
	Gaffer.TweakPlug, "mode",
	"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget"
)

def __validModes( plug ) :

	result = []
	if Gaffer.Metadata.value( plug.parent(), "tweakPlugValueWidget:allowCreate" ) :
		result += [ Gaffer.TweakPlug.Mode.Create ]

	result += [ Gaffer.TweakPlug.Mode.Replace ]
	if hasattr( plug.parent()["value"], "hasMinValue" ) :
		result += [
			Gaffer.TweakPlug.Mode.Add,
			Gaffer.TweakPlug.Mode.Subtract,
			Gaffer.TweakPlug.Mode.Multiply,
			Gaffer.TweakPlug.Mode.Min,
			Gaffer.TweakPlug.Mode.Max,
		]

	if type( plug.parent()["value"] ) in [
		Gaffer.BoolVectorDataPlug,
		Gaffer.IntVectorDataPlug,
		Gaffer.FloatVectorDataPlug,
		Gaffer.StringVectorDataPlug,
		Gaffer.InternedStringVectorDataPlug,
		Gaffer.V2iVectorDataPlug,
		Gaffer.V3fVectorDataPlug,
		Gaffer.Color3fVectorDataPlug,
		Gaffer.M44fVectorDataPlug,
		Gaffer.M33fVectorDataPlug,
	] :
		result += [
			Gaffer.TweakPlug.Mode.ListAppend,
			Gaffer.TweakPlug.Mode.ListPrepend,
			Gaffer.TweakPlug.Mode.ListRemove
		]

	if Gaffer.Metadata.value( plug.parent(), "tweakPlugValueWidget:allowRemove" ) :
		result += [ Gaffer.TweakPlug.Mode.Remove ]

	return result

Gaffer.Metadata.registerValue(
	Gaffer.TweakPlug, "mode",
	"presetNames", lambda plug : IECore.StringVectorData( [ IECore.CamelCase.toSpaced( str( x ) ) for x in __validModes( plug ) ] )
)

Gaffer.Metadata.registerValue(
	Gaffer.TweakPlug, "mode",
	"presetValues", lambda plug : IECore.IntVectorData( [ int( x ) for x in __validModes( plug ) ] )
)

def __noduleLabel( plug ) :

	if not isinstance( plug, Gaffer.TweakPlug ) :
		plug = plug.parent()

	name = None
	with IECore.IgnoredExceptions( Exception ) :
		name = plug["name"].getValue()

	return name or plug.getName()

Gaffer.Metadata.registerValue( Gaffer.TweakPlug, "nodule:type", "GafferUI::CompoundNodule" )
Gaffer.Metadata.registerValue( Gaffer.TweakPlug, "*", "nodule:type", "" )
Gaffer.Metadata.registerValue( Gaffer.TweakPlug, "value", "nodule:type", "GafferUI::StandardNodule" )
Gaffer.Metadata.registerValue( Gaffer.TweakPlug, "noduleLayout:label", __noduleLabel )
Gaffer.Metadata.registerValue( Gaffer.TweakPlug, "value", "noduleLayout:label", __noduleLabel )

# Spreadsheet Interoperability
# ============================

Gaffer.Metadata.registerValue( Gaffer.TweakPlug, "spreadsheet:plugMenu:includeAsAncestor", True )
Gaffer.Metadata.registerValue( Gaffer.TweakPlug, "spreadsheet:plugMenu:ancestorLabel", "Tweak" )

def __spreadsheetColumnName( plug ) :

	if isinstance( plug, Gaffer.TweakPlug ) :
		tweakPlug = plug
	else :
		tweakPlug = plug.parent()

	# Use some heuristics to come up with a more helpful
	# column name.

	name = tweakPlug.getName()
	if name.startswith( "tweak" ) and tweakPlug["name"].source().direction() != Gaffer.Plug.Direction.Out :
		name = tweakPlug["name"].getValue()
		name = re.sub( "[^0-9a-zA-Z_]+", "_", name )

	if not name :
		return plug.getName()

	if plug == tweakPlug :
		return name
	else :
		return name + plug.getName().title()

Gaffer.Metadata.registerValue( Gaffer.TweakPlug, "spreadsheet:columnName", __spreadsheetColumnName )
Gaffer.Metadata.registerValue( Gaffer.TweakPlug, "enabled", "spreadsheet:columnName", __spreadsheetColumnName )
Gaffer.Metadata.registerValue( Gaffer.TweakPlug, "mode", "spreadsheet:columnName", __spreadsheetColumnName )
Gaffer.Metadata.registerValue( Gaffer.TweakPlug, "value", "spreadsheet:columnName", __spreadsheetColumnName )

def __spreadsheetFormatter( plug, forToolTip ) :

	result = ""
	if "enabled" in plug.parent() :
		result = "On, " if plug["enabled"].getValue() else "Off, "

	result += str( Gaffer.TweakPlug.Mode.values[plug["mode"].getValue()] )

	value = GafferUI.SpreadsheetUI.formatValue( plug["value"], forToolTip )
	separator = " : \n" if forToolTip and "\n" in value else " : "
	result += separator + value

	return result

GafferUI.SpreadsheetUI.registerValueFormatter( Gaffer.TweakPlug, __spreadsheetFormatter )

def __spreadsheetDecorator( plug ) :

	return GafferUI.SpreadsheetUI.decoration( plug["value"] )

GafferUI.SpreadsheetUI.registerDecoration( Gaffer.TweakPlug, __spreadsheetDecorator )

def __spreadsheetValueWidget( plug ) :

	w = TweakPlugValueWidget( plug )
	w.setNameVisible( False )
	return w

GafferUI.SpreadsheetUI.registerValueWidget( Gaffer.TweakPlug, __spreadsheetValueWidget )
