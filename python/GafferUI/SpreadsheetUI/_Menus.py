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

import functools

import IECore

import Gaffer
import GafferUI

from . import _Algo
from ._RowsPlugValueWidget import _RowsPlugValueWidget
from ._SectionChooser import _SectionChooser

# _Menus
# ------
#
# Code that provides extensions to standard Gaffer menus.
#
# \todo Determine if menu additions that are only relevant due to the specific
# implementation of another class (eg: plug context menu additions due to the
# reuse if PlugValueWidget in _CellPlugValueWidget) should be moved to those
# classes instead of here.

# Plug context menu
# =================

def __setPlugValue( plug, value ) :

	with Gaffer.UndoScope( plug.ancestor( Gaffer.ScriptNode ) ) :
		plug.setValue( value )

def __deleteRow( rowPlug ) :

	with Gaffer.UndoScope( rowPlug.ancestor( Gaffer.ScriptNode ) ) :
		rowPlug.parent().removeChild( rowPlug )

def __setRowNameWidth( rowPlug, width, *unused ) :

	with Gaffer.UndoScope( rowPlug.ancestor( Gaffer.ScriptNode ) ) :
		_RowsPlugValueWidget._setRowNameWidth( rowPlug.parent(), width )

def __prependRowAndCellMenuItems( menuDefinition, plugValueWidget ) :

	plug = plugValueWidget.getPlug()
	rowPlug = plug.ancestor( Gaffer.Spreadsheet.RowPlug )
	if rowPlug is None :
		return

	isDefaultRow = rowPlug == rowPlug.parent().defaultRow()

	def ensureDivider() :
		if menuDefinition.item( "/__SpreadsheetRowAndCellDivider__" ) is None :
			menuDefinition.prepend( "/__SpreadsheetRowAndCellDivider__", { "divider" : True } )

	# Row menu items

	if plug.parent() == rowPlug and not isDefaultRow :

		ensureDivider()

		menuDefinition.prepend(
			"/Delete Row",
			{
				"command" : functools.partial( __deleteRow, rowPlug ),
				"active" : (
					not plugValueWidget.getReadOnly() and
					not Gaffer.MetadataAlgo.readOnly( rowPlug ) and
					_Algo.dimensionsEditable( rowPlug.parent() )
				)
			}
		)

		widths = [
			( "Half", GafferUI.PlugWidget.labelWidth() * 0.5 ),
			( "Single", GafferUI.PlugWidget.labelWidth() ),
			( "Double", GafferUI.PlugWidget.labelWidth() * 2 ),
		]

		currentWidth = _RowsPlugValueWidget._getRowNameWidth( rowPlug.parent() )
		for label, width in reversed( widths ) :
			menuDefinition.prepend(
				"/Width/{}".format( label ),
				{
					"command" : functools.partial( __setRowNameWidth, rowPlug, width ),
					"active" : not plugValueWidget.getReadOnly() and not Gaffer.MetadataAlgo.readOnly( rowPlug ),
					"checkBox" : width == currentWidth,
				}
			)

	# Cell menu items

	cellPlug = plug if isinstance( plug, Gaffer.Spreadsheet.CellPlug ) else plug.ancestor( Gaffer.Spreadsheet.CellPlug )
	if cellPlug is not None :

		if not isDefaultRow or "enabled" not in cellPlug :

			ensureDivider()

			enabled = None
			enabledPlug = cellPlug.enabledPlug()
			with plugValueWidget.getContext() :
				with IECore.IgnoredExceptions( Gaffer.ProcessException ) :
					enabled = enabledPlug.getValue()

			menuDefinition.prepend(
				"/Disable Cell" if enabled else "/Enable Cell",
				{
					"command" : functools.partial( __setPlugValue, enabledPlug, not enabled ),
					"active" : not plugValueWidget.getReadOnly() and not Gaffer.MetadataAlgo.readOnly( enabledPlug ) and enabledPlug.settable()
				}
			)

def __spreadsheetSubMenu( plug, command, showSections = True ) :

	menuDefinition = IECore.MenuDefinition()

	if isinstance( plug.node(), Gaffer.ScriptNode ) :
		spreadsheetParent = plug.node()
	else :
		spreadsheetParent = plug.node().parent()

	alreadyConnected = []
	other = []
	for spreadsheet in Gaffer.Spreadsheet.Range( spreadsheetParent ) :

		if spreadsheet == plug.ancestor( Gaffer.Spreadsheet ) :
			continue

		connected = False
		for output in spreadsheet["out"] :
			for destination in output.outputs() :
				if destination.node() == plug.node() :
					connected = True
					break
			if connected :
				break

		if connected :
			alreadyConnected.append( spreadsheet )
		else :
			other.append( spreadsheet )

	if not alreadyConnected and not other :
		menuDefinition.append(
			"/No Spreadsheets Available",
			{
				"active" : False,
			}
		)
		return menuDefinition

	alreadyConnected.sort( key = Gaffer.GraphComponent.getName )
	other.sort( key = Gaffer.GraphComponent.getName )

	def addItems( spreadsheet ) :

		sectionNames = _SectionChooser.sectionNames( spreadsheet["rows"].source() ) if showSections else None
		if sectionNames :

			for sectionName in sectionNames :

				menuDefinition.append(
					"/{}/{}".format( spreadsheet.getName(), sectionName ),
					{
						"command" : functools.partial( command, spreadsheet, sectionName )
					}
				)

		else :

			menuDefinition.append(
				"/" + spreadsheet.getName(),
				{
					"command" : functools.partial( command, spreadsheet )
				}
			)

	if alreadyConnected and other :
		menuDefinition.append( "/__ConnectedDivider__", { "divider" : True, "label" : "Connected" } )

	for spreadsheet in alreadyConnected :
		addItems( spreadsheet )

	if alreadyConnected and other :
		menuDefinition.append( "/__OtherDivider__", { "divider" : True, "label" : "Other" } )

	for spreadsheet in other :
		addItems( spreadsheet )

	return menuDefinition

def __prependSpreadsheetCreationMenuItems( menuDefinition, plugValueWidget ) :

	plug = plugValueWidget.getPlug()
	if not isinstance( plug, Gaffer.ValuePlug ) :
		return

	node = plug.node()
	if node is None or node.parent() is None :
		return

	if plug.getInput() is not None or not plugValueWidget._editable() or Gaffer.MetadataAlgo.readOnly( plug ) :
		return

	plugsAndSuffixes = [ ( plug, "" ) ]

	ancestorPlug = plug.parent()
	while isinstance( ancestorPlug, Gaffer.Plug ) :

		if any( p.getInput() is not None for p in Gaffer.Plug.RecursiveRange( ancestorPlug ) ) :
			break

		if Gaffer.Metadata.value( ancestorPlug, "spreadsheet:plugMenu:includeAsAncestor" ) :
			label = Gaffer.Metadata.value( ancestorPlug, "spreadsheet:plugMenu:ancestorLabel" )
			label = label or ancestorPlug.typeName().rpartition( ":" )[2]
			plugsAndSuffixes.append( ( ancestorPlug, " ({})".format( label ) ) )

		ancestorPlug = ancestorPlug.parent()

	for plug, suffix in reversed( plugsAndSuffixes ) :

		menuDefinition.prepend( "/__SpreadsheetCreationDivider__" + suffix, { "divider" : True } )

		menuDefinition.prepend(
			"/Add to Spreadsheet{}".format( suffix ),
			{
				"subMenu" :  functools.partial( __spreadsheetSubMenu, plug, functools.partial( _Algo.addToSpreadsheet, plug ) )
			}
		)
		menuDefinition.prepend(
			"/Create Spreadsheet{}...".format( suffix ),
			{
				"command" : functools.partial( _Algo.createSpreadsheet, plug )
			}
		)

def __plugPopupMenu( menuDefinition, plugValueWidget ) :

	## \todo We're prepending rather than appending so that we get the ordering we
	# want with respect to the Expression menu items. Really we need external control
	# over this ordering.
	__prependRowAndCellMenuItems( menuDefinition, plugValueWidget )
	__prependSpreadsheetCreationMenuItems( menuDefinition, plugValueWidget )

GafferUI.PlugValueWidget.popupMenuSignal().connect( __plugPopupMenu, scoped = False )

for plugType in ( Gaffer.TransformPlug, Gaffer.Transform2DPlug ) :
	Gaffer.Metadata.registerValue( plugType, "spreadsheet:plugMenu:includeAsAncestor", True )
	Gaffer.Metadata.registerValue( plugType, "spreadsheet:plugMenu:ancestorLabel", "Transform" )

# NodeEditor tool menu
# ====================

def __nodeEditorToolMenu( nodeEditor, node, menuDefinition ) :

	if node.parent() is None :
		return

	activeRowNamesConnection = Gaffer.Metadata.value( node, "ui:spreadsheet:activeRowNamesConnection" )
	if not activeRowNamesConnection :
		return
	else :
		activeRowNamesConnection = node.descendant( activeRowNamesConnection )
		assert( activeRowNamesConnection is not None )

	selectorContextVariablePlug = Gaffer.Metadata.value( node, "ui:spreadsheet:selectorContextVariablePlug" )
	if selectorContextVariablePlug :
		selectorContextVariablePlug = node.descendant( selectorContextVariablePlug )
		assert( selectorContextVariablePlug is not None )

	selectorValue = Gaffer.Metadata.value( node, "ui:spreadsheet:selectorValue" )
	assert( not ( selectorValue and selectorContextVariablePlug ) )

	menuDefinition.append( "/SpreadsheetDivider", { "divider" : True } )

	itemsActive = (
		not nodeEditor.getReadOnly()
		and not Gaffer.MetadataAlgo.readOnly( node )
		and not Gaffer.MetadataAlgo.readOnly( activeRowNamesConnection )
		and activeRowNamesConnection.getInput() is None
	)

	menuDefinition.append(
		"/Create Spreadsheet...",
		{
			"command" : functools.partial( _Algo.createSpreadsheetForNode, node, activeRowNamesConnection, selectorContextVariablePlug, selectorValue ),
			"active" : itemsActive
		}
	)

	connectCommand = functools.partial( _Algo.connectPlugToRowNames, activeRowNamesConnection, selectorContextVariablePlug, selectorValue )
	menuDefinition.append(
		"/Connect to Spreadsheet",
		{
			"subMenu" :  functools.partial( __spreadsheetSubMenu, activeRowNamesConnection, connectCommand, showSections = False ),
			"active" : itemsActive
		}
	)

GafferUI.NodeEditor.toolMenuSignal().connect( __nodeEditorToolMenu, scoped = False )
