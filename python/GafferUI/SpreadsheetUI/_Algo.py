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

import Gaffer
import GafferUI

from ._SectionChooser import _SectionChooser

# _Algo
# -----

# Functions with aspirations to live in a public Gaffer.SpreadsheetAlgo
# namespace one day. They are currently too intertwined with the UI to be
# suitable for that, but they do represent useful functionality we would like
# to be more generally available.

## \todo Needs UndoScope removing
def createSpreadsheet( plug ) :

	spreadsheet = Gaffer.Spreadsheet()
	spreadsheet["selector"].setValue( Gaffer.Metadata.value( plug,"ui:spreadsheet:selectorValue" ) or "" )

	addColumn( spreadsheet, plug )
	spreadsheet["rows"].addRow()

	if isinstance( plug.node(), Gaffer.ScriptNode ) :
		spreadsheetParent = plug.node()
		Gaffer.Metadata.registerValue( spreadsheet, "nodeGadget:type", "GafferUI::StandardNodeGadget" )
	else :
		spreadsheetParent = plug.node().parent()

	with Gaffer.UndoScope( plug.ancestor( Gaffer.ScriptNode ) ) :
		spreadsheetParent.addChild( spreadsheet )
		plug.setInput( spreadsheet["out"][0] )

	GafferUI.NodeEditor.acquire( spreadsheet )

## \todo Needs UndoScope removing
def addToSpreadsheet( plug, spreadsheet, sectionName = None ) :

	with Gaffer.UndoScope( spreadsheet.ancestor( Gaffer.ScriptNode ) ) :
		columnIndex = addColumn( spreadsheet, plug )
		if sectionName is not None :
			_SectionChooser.setSection(
				spreadsheet["rows"].defaultRow()["cells"][columnIndex].source(),
				sectionName
			)
		plug.setInput( spreadsheet["out"][columnIndex] )

def addColumn( spreadsheet, plug ) :

	# We allow the name of a column to be overridden by metadata, so that NameValuePlug and
	# TweakPlug can provide more meaningful names than "name" or "enabled" when their child
	# plugs are added to spreadsheets.
	columnName = Gaffer.Metadata.value( plug, "spreadsheet:columnName" ) or plug.getName()

	# If the plug already has a child `enabled` plug, then we always adopt
	# it to enable the cell. This makes for a much simpler user experience
	# for NameValuePlugs and TweakPlugs. In an ideal world we would have
	# made this the standard behaviour from the start.
	adoptEnabledPlug = isinstance( plug.getChild( "enabled" ), Gaffer.BoolPlug )

	# Rows plug may have been promoted, in which case we need to edit
	# the source, which will automatically propagate the new column to
	# the spreadsheet.
	rowsPlug = spreadsheet["rows"].source()
	columnIndex = rowsPlug.addColumn( plug, columnName, adoptEnabledPlug )
	valuePlug = rowsPlug.defaultRow()["cells"][columnIndex]["value"]
	Gaffer.MetadataAlgo.copy( plug, valuePlug, exclude = "spreadsheet:columnName layout:* deletable" )

	return columnIndex

# UI Helpers
# ----------

# Returns True if all the supplied cells can be disabled. This may be false if
# the list contains cells in the default row that aren't adopting the enabled
# plug from their value plug.
def cellsCanBeDisabled( cellPlugs ) :

	if not cellPlugs :
		return False

	defaultRow = next( iter( cellPlugs ) ).ancestor( Gaffer.Spreadsheet.RowsPlug ).defaultRow()
	defaultRowCells = [ cell for cell in cellPlugs if cell.ancestor( Gaffer.Spreadsheet.RowPlug ).isSame( defaultRow ) ]
	for cell in defaultRowCells :
		if "enabled" in cell :
			return False

	return True

# Note, function may present dialogues.
## \todo Needs UndoScope removing
def createSpreadsheetForNode( node, enabledRowNamesConnection, selectorContextVariablePlug, selectorValue, menu ) :

	with Gaffer.UndoScope( node.scriptNode() ) :

		spreadsheet = Gaffer.Spreadsheet( node.getName() + "Spreadsheet" )
		connectPlugToRowNames( enabledRowNamesConnection, selectorContextVariablePlug, selectorValue, spreadsheet, menu )
		node.parent().addChild( spreadsheet )

	GafferUI.NodeEditor.acquire( spreadsheet )

# Note, function may present dialogues.
## \todo This needs splitting into the pre-check + confirm and algo to affect the actual change without UndoScope
def connectPlugToRowNames( enabledRowNamesConnection, selectorContextVariablePlug, selectorValue, spreadsheet, menu ) :

	node = enabledRowNamesConnection.node()

	# We defer locking the plug until we know we're going ahead
	lockSelectorVarPlug = False
	if selectorValue is None :
		selectorValue = "${" + selectorContextVariablePlug.getValue() + "}"
		lockSelectorVarPlug = True

	# Check that the sheet's selector meets requirements before making any changes

	existingSelector = spreadsheet["selector"].getValue()
	if existingSelector and selectorValue and existingSelector != selectorValue :

		message = "{sheetName}'s selector is set to: '{sheetSelector}'.\n\n" + \
			"The '{plugName}' plug requires a different selector to work\n" + \
			"properly. Continuing will reset the selector to '{selector}'."

		confirm = GafferUI.ConfirmationDialogue(
			"Invalid Selector",
			message.format(
				sheetName = spreadsheet.getName(), sheetSelector = existingSelector,
				plugName = enabledRowNamesConnection.getName(), selector = selectorValue
			),
			confirmLabel = "Continue"
		)

		if not confirm.waitForConfirmation( parentWindow = menu.ancestor( GafferUI.Window ) ) :
			return

	with Gaffer.UndoScope( node.scriptNode() ) :

		if lockSelectorVarPlug :
			Gaffer.MetadataAlgo.setReadOnly( selectorContextVariablePlug, True )

		if selectorValue :
			spreadsheet["selector"].setValue( selectorValue )
			Gaffer.MetadataAlgo.setReadOnly( spreadsheet["selector"], True )

		with node.scriptNode().context() :
			rowNames = enabledRowNamesConnection.getValue()
		enabledRowNamesConnection.setInput( spreadsheet["enabledRowNames"] )

		if rowNames :
			for rowName in rowNames :
				spreadsheet["rows"].addRow()["name"].setValue( rowName )
		else :
			# Only a new row to an empty spreadsheet
			if len( spreadsheet["rows"].children() ) == 1 :
				spreadsheet["rows"].addRow()

		node.parent().addChild( spreadsheet )
