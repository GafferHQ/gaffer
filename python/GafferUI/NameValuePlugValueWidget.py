##########################################################################
#
#  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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

import re

import IECore

import Gaffer
import GafferUI
import GafferUI.SpreadsheetUI

from GafferUI.PlugValueWidget import sole

## Supported plug metadata :
#
# - "nameValuePlugPlugValueWidget:ignoreNamePlug", set to True to ignore the name plug and instead show a
#   label with the name of the NameValuePlug.
class NameValuePlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, childPlug ) :

		self.__row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 )

		GafferUI.PlugValueWidget.__init__( self, self.__row, childPlug )

		## \todo We should support no plugs here. Move the UI configuration into setPlugs
		assert( len( self.getPlugs() ) > 0 )

		# We use a non-editable label if requested by "nameValuePlugPlugValueWidget:ignoreNamePlug" metadata.

		if any( Gaffer.Metadata.value( p, "nameValuePlugPlugValueWidget:ignoreNamePlug" ) for p in self.getPlugs() ) :
			nameWidget = GafferUI.LabelPlugValueWidget(
				self.getPlugs(),
				horizontalAlignment = GafferUI.Label.HorizontalAlignment.Right,
			)
			nameWidget.label()._qtWidget().setFixedWidth( GafferUI.PlugWidget.labelWidth() )
			nameWidget.dropSignal().connectFront( Gaffer.WeakMethod( self.__drop ) )
		else :
			nameWidget = GafferUI.StringPlugValueWidget( { plug["name"] for plug in self.getPlugs() } )
			nameWidget.textWidget()._qtWidget().setFixedWidth( GafferUI.PlugWidget.labelWidth() )

		self.__row.append( nameWidget,
			verticalAlignment = GafferUI.Label.VerticalAlignment.Top
		)

		if all( [ "enabled" in plug for plug in self.getPlugs() ] ) :
			self.__row.append(
				GafferUI.BoolPlugValueWidget(
					{ plug["enabled"] for plug in self.getPlugs() },
					displayMode = GafferUI.BoolWidget.DisplayMode.Switch
				),
				verticalAlignment = GafferUI.Label.VerticalAlignment.Top,
			)

		self.__row.append( GafferUI.PlugValueWidget.create( { plug["value"] for plug in self.getPlugs() } ), expand = True )

	def setPlugs( self, plugs ) :

		GafferUI.PlugValueWidget.setPlugs( self, plugs )

		if isinstance( self.__row[0], GafferUI.LabelPlugValueWidget ) :
			self.__row[0].setPlugs( plugs )
		else :
			self.__row[0].setPlugs({ plug["name"] for plug in plugs } )

		if all( [ "enabled" in plug for plug in plugs ] ) :
			self.__row[1].setPlugs( { plug["enabled"] for plug in plugs } )

		self.__row[-1].setPlugs( { plug["value"] for plug in plugs } )

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

	@staticmethod
	def _valuesForUpdate( plugs, auxiliaryPlugs ) :

		return [
			p["enabled"].getValue() if "enabled" in p else True
			for p in plugs
		]

	def _updateFromValues( self, values, exception ) :

		enabled = all( values )
		if isinstance( self.__row[0], GafferUI.StringPlugValueWidget ) :
			self.__row[0].setEnabled( enabled )
		self.__row[-1].setEnabled( enabled )

	def __drop( self, widget, event ) :

		if not isinstance( event.data, Gaffer.Plug ) :
			return False

		# The PlugValueWidget base class for the label has accepted a drag from
		# a plug, and it is about to connect it to our plug in
		# `PlugValueWidget.__drop()`. But we don't want our `name` plug to be
		# connected, because it isn't user-facing and we need it to keep its
		# original value. So we do our own drop handling to connect all the
		# child plugs _except_ `name`.

		widget.setHighlighted( False )
		with Gaffer.UndoScope( self.scriptNode() ) :
			for p in self.getPlugs() :
				for c in p.children() :
					if c.getName() != "name" :
						c.setInput( event.data[c.getName()] )

		return True

GafferUI.PlugValueWidget.registerType( Gaffer.NameValuePlug, NameValuePlugValueWidget )

# Spreadsheet integration
# =======================

Gaffer.Metadata.registerValue( Gaffer.NameValuePlug, "spreadsheet:plugMenu:includeAsAncestor", True )
Gaffer.Metadata.registerValue( Gaffer.NameValuePlug, "spreadsheet:plugMenu:ancestorLabel", "Value and Switch" )

def __spreadsheetColumnName( plug ) :

	if isinstance( plug, Gaffer.NameValuePlug ) :
		nameValuePlug = plug
	else :
		nameValuePlug = plug.parent()

	# Use some heuristics to come up with a more helpful
	# column name.

	name = nameValuePlug.getName()
	if name.startswith( "member" ) and nameValuePlug["name"].source().direction() != Gaffer.Plug.Direction.Out :
		name = nameValuePlug["name"].getValue()
		name = re.sub( "[^0-9a-zA-Z_]+", "_", name )

	if not name :
		return plug.getName()

	if plug == nameValuePlug :
		return name
	else :
		return name + plug.getName().title()

Gaffer.Metadata.registerValue( Gaffer.NameValuePlug, "spreadsheet:columnName", __spreadsheetColumnName )
Gaffer.Metadata.registerValue( Gaffer.NameValuePlug, "enabled", "spreadsheet:columnName", __spreadsheetColumnName )
Gaffer.Metadata.registerValue( Gaffer.NameValuePlug, "value", "spreadsheet:columnName", __spreadsheetColumnName )

def __spreadsheetFormatter( plug, forToolTip ) :

	value = GafferUI.SpreadsheetUI.formatValue( plug["value"], forToolTip )
	if "enabled" not in plug.parent() :
		return value

	enabled = "On" if plug["enabled"].getValue() else "Off"
	separator = " : \n" if forToolTip and "\n" in value else " : "
	return enabled + separator + value

GafferUI.SpreadsheetUI.registerValueFormatter( Gaffer.NameValuePlug, __spreadsheetFormatter )

def __spreadsheetDecorator( plug ) :

	return GafferUI.SpreadsheetUI.decoration( plug["value"] )

GafferUI.SpreadsheetUI.registerDecoration( Gaffer.NameValuePlug, __spreadsheetDecorator )

def __spreadsheetValueWidget( plug ) :

	w = GafferUI.NameValuePlugValueWidget( plug )
	w.setNameVisible( False )
	return w

GafferUI.SpreadsheetUI.registerValueWidget( Gaffer.NameValuePlug, __spreadsheetValueWidget )
