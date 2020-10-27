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
#   label with the name of the NameValuePlug.  This is the same behaviour you get by default if the plug
#   is not dynamic
class NameValuePlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, childPlug ) :

		if isinstance( childPlug, Gaffer.Plug ) :
			childPlugs = { childPlug }
		else :
			childPlugs = childPlug or set()

		self.__row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 )

		GafferUI.PlugValueWidget.__init__( self, self.__row, childPlugs )

		assert( len( childPlugs ) > 0 )

		# We use a non-editable label for the name for non-dynamic plugs, or any that request it

		anyStatic = any( [ not p.getFlags( Gaffer.Plug.Flags.Dynamic ) for p in childPlugs ] )
		anyIgnoreName = any( [ Gaffer.Metadata.value( p, "nameValuePlugPlugValueWidget:ignoreNamePlug" ) for p in childPlugs ] )

		if anyStatic or anyIgnoreName :
			nameWidget = GafferUI.LabelPlugValueWidget(
				childPlugs,
				horizontalAlignment = GafferUI.Label.HorizontalAlignment.Right,
				verticalAlignment = GafferUI.Label.VerticalAlignment.Center,
			)
			nameWidget.label()._qtWidget().setFixedWidth( GafferUI.PlugWidget.labelWidth() )
			# cheat to get the height of the label to match the height of a line edit
			# so the label and plug widgets align nicely. ideally we'd get the stylesheet
			# sorted for the QLabel so that that happened naturally, but QLabel sizing appears
			# somewhat unpredictable (and is sensitive to HTML in the text as well), making this
			# a tricky task.
			nameWidget.label()._qtWidget().setFixedHeight( 20 )
		else :
			nameWidget = GafferUI.StringPlugValueWidget( { plug["name"] for plug in childPlugs } )
			nameWidget.textWidget()._qtWidget().setFixedWidth( GafferUI.PlugWidget.labelWidth() )

		self.__row.append( nameWidget,
			verticalAlignment = GafferUI.Label.VerticalAlignment.Top
		)

		if all( [ "enabled" in plug for plug in childPlugs ] ) :
			self.__row.append(
				GafferUI.BoolPlugValueWidget(
					{ plug["enabled"] for plug in childPlugs },
					displayMode = GafferUI.BoolWidget.DisplayMode.Switch
				),
				verticalAlignment = GafferUI.Label.VerticalAlignment.Top,
			)

		self.__row.append( GafferUI.PlugValueWidget.create( { plug["value"] for plug in childPlugs } ), expand = True )

		self._updateFromPlugs()

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

	def setReadOnly( self, readOnly ) :

		if readOnly == self.getReadOnly() :
			return

		GafferUI.PlugValueWidget.setReadOnly( self, readOnly )

		for w in self.__row :
			w.setReadOnly( readOnly )

	def setNameVisible( self, visible ) :

		self.__row[0].setVisible( visible )

	def getNameVisible( self ) :

		return self.__row[0].getVisible()

	def _updateFromPlugs( self ) :

		if all( [ "enabled" in plug for plug in self.getPlugs()] ) :
			with self.getContext() :
				enabled = sole( [ plug["enabled"].getValue() for plug in self.getPlugs() ] )

			if isinstance( self.__row[0], GafferUI.StringPlugValueWidget ) :
				self.__row[0].setEnabled( enabled is True )

			self.__row[-1].setEnabled( enabled is True )

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
