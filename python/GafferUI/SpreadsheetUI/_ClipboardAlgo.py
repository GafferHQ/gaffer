##########################################################################
#
#  Copyright (c) 2020, Cinesite VFX Ltd. All rights reserved.
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

## Returns True if the supplied plug matrix can be copied to the clipboard.
# Copy is possible if:
#
#   - There is a single row or column.
#   - There is a contiguous selection across multiple rows/columns.
#
# `plugMatrix` should be a row-major list of value plugs,
# as returned by createPlugMatrixFromCells, ie: [ [ r1c1, ... ], [ r2c1, ... ] ]
#
# \note Triggers compute of the source plugs.
def canCopyPlugs( plugMatrix ) :

	return _objectMatrixFromPlugMatrix( plugMatrix ) is not None

## Copies `plugMatrix` to the clipboard.
# For Spreadsheet rows, the matrix should consist of a single column
# containing the Spreadsheet.RowPlug for each row to be copied.
# \see copyRows
def copyPlugs( plugMatrix ) :

	assert( canCopyPlugs( plugMatrix ) )

	objectMatrix = _objectMatrixFromPlugMatrix( plugMatrix )
	plugMatrix[0][0].ancestor( Gaffer.ApplicationRoot ).setClipboardContents( objectMatrix )

## Returns True if the supplied data can be pasted on to the supplied
# spreadsheet cell plugs, in that the cell value types are compatible with the
# provided data.
def canPasteCells( data, plugMatrix ) :

	objectMatrix = __objectMatrixFromData( data )
	pasteFunctionsOrReason = __pasteFunctionsOrNonPasteableReason( plugMatrix, objectMatrix, 0 )

	return not isinstance( pasteFunctionsOrReason, str )

## Returns the reason why the supplied data could not be pasted on to the supplied
# spreadsheet cell plugs.
## \todo On paste failure, this reason should be presented to the user as an ephemeral
# pop-up, like we do in _InspectorColumn.
def nonPasteableReason( data, plugMatrix ) :

	objectMatrix = __objectMatrixFromData( data )
	pasteFunctionsOrReason = __pasteFunctionsOrNonPasteableReason( plugMatrix, objectMatrix, 0 )

	if isinstance( pasteFunctionsOrReason, str ) :
		return pasteFunctionsOrReason

	return ""

## Pastes the supplied data on to the provided spreadsheet cell plugs.
def pasteCells( data, plugMatrix, atTime ) :

	assert( canPasteCells( data, plugMatrix ) )

	objectMatrix = __objectMatrixFromData( data )
	for f in __pasteFunctionsOrNonPasteableReason( plugMatrix, objectMatrix, atTime ) :
		f()

## Copies the provided Spreadsheet RowPlugs to the clipboard.
def copyRows( rowPlugs ) :

	objectMatrix = _objectMatrixFromPlugMatrix( [ [ row ] for row in rowPlugs ] )
	if objectMatrix :
		rowPlugs[0].ancestor( Gaffer.ApplicationRoot ).setClipboardContents( objectMatrix )

## Returns True if the supplied objectMatrix can be pasted as new rows at the
# end of the supplied Spreadsheet rows plug.
def canPasteRows( objectMatrix, rowsPlug ) :

	if not isinstance( objectMatrix, IECore.ObjectMatrix ) :
		return False

	if Gaffer.MetadataAlgo.readOnly( rowsPlug ) :
		return False

	for rowIndex in range( objectMatrix.numRows() ) :
		if not __rowPlugMatchingCells( rowsPlug.defaultRow(), objectMatrix[rowIndex, 0] ) :
			return False

	return canPasteCells( objectMatrix, [ [ rowsPlug.defaultRow() ] ] )

# Pastes the supplied data as new rows at the end of the supplied rows plug.
# Columns are matched by name (and type), allowing rows to be copied
# between Spreadsheets with different configurations. Cells in the
# target Spreadsheet with no data will be set to the default value for
# that column.
def pasteRows( objectMatrix, rowsPlug ) :

	assert( canPasteRows( objectMatrix, rowsPlug ) )

	# addRows currently returns None, so this is easier
	newRows = [ rowsPlug.addRow() for _ in range( objectMatrix.numRows() ) ]
	# We know these aren't animated as we've just made them so time is irrelevant
	pasteCells( objectMatrix, [ [ row ] for row in newRows ], 0 )

## Takes an arbitrary list of spreadsheet CellPlugs (perhaps as obtained from a
# selection, which may be in a jumbled order) and groups them, ordered by row
# then by column to be compatible with copy/paste.
def createPlugMatrixFromCells( cellPlugs ) :

	if not cellPlugs :
		return []

	rowsPlug = next( iter( cellPlugs ) ).ancestor( Gaffer.Spreadsheet.RowsPlug )
	assert( rowsPlug is not None )

	# Build a matrix of rows/columns in ascending order. We don't actually
	# care what the original row/column indices were, we just need them
	# to be ascending so the matrix represents the logical order of the cells.

	matrix = []

	# First, group cells by row
	rows = {}
	for cell in cellPlugs :
		rowPlug = cell.ancestor( Gaffer.Spreadsheet.RowPlug )
		rows.setdefault( rowPlug, [] ).append( cell )

	# Then sort the rows, and their cells
	spreadsheetRows = rowsPlug.children()
	for rowPlug, cells in sorted( rows.items(), key = lambda item : spreadsheetRows.index( item[0] ) ) :
		rowCells = rowPlug["cells"].children()
		matrix.append( sorted( cells, key = rowCells.index ) )

	return matrix

# Protected rather than private to allow access by SpreadsheetUITest.
## \todo Maybe there is merit in adding something like this to PlugAlgo?
def _objectMatrixFromPlugMatrix( plugMatrix ) :

	def fromPlug( plug ) :

		if hasattr( plug, "getValue" ) :
			return plug.getValue()

		return IECore.CompoundData( { child.getName() : fromPlug( child ) for child in plug } )

	if not __isPlugMatrix( plugMatrix ) :
		return None

	objectMatrix = IECore.ObjectMatrix( len( plugMatrix ), len( plugMatrix[0] ) )
	for rowIndex, row in enumerate( plugMatrix ) :
		for columnIndex, column in enumerate( row ) :
			objectMatrix[ rowIndex, columnIndex ] = fromPlug( column )

	return objectMatrix

def __objectMatrixFromData( data ) :

	## \todo Also convert ObjectVector to ObjectMatrix
	if isinstance( data, IECore.ObjectMatrix ) :
		return data
	elif isinstance( data, IECore.Data ) :
		objectMatrix = IECore.ObjectMatrix( 1, 1 )
		objectMatrix[0, 0] = data
		return objectMatrix

	return None

def __pasteFunctionsOrNonPasteableReason( plugMatrix, objectMatrix, atTime ) :

	if not isinstance( objectMatrix, IECore.ObjectMatrix ) :
		return "No ObjectMatrix to paste"

	if not __isPlugMatrix( plugMatrix ) :
		return "No plugs to edit"

	# Check global read-only status, early out if none can be modified
	rowsPlug = plugMatrix[0][0].ancestor( Gaffer.Spreadsheet.RowsPlug )
	if rowsPlug and Gaffer.MetadataAlgo.readOnly( rowsPlug ) :
		return "Spreadsheet is read-only"

	pasteFunctions = []

	for rowIndex, row in enumerate( plugMatrix ) :
		for columnIndex, cell in enumerate( row ) :
			# Allow values to repeat if the selection being pasted into is larger than what was copied
			value = objectMatrix[ rowIndex % objectMatrix.numRows(), columnIndex % objectMatrix.numColumns() ]
			if isinstance( cell, Gaffer.Spreadsheet.RowPlug ) :
				for c in __rowPlugMatchingCells( cell, value ) :
					reason = __plugNotPasteableReason( c, value["cells"][ c.getName() ] )
					if reason != "" :
						return reason

				pasteFunctions.append( functools.partial( __setRowPlug, cell, atTime, value ) )

			else :
				reason = __plugNotPasteableReason( cell, value )
				if reason != "" :
					return reason

				if __isRowPlugData( value ) :
					return "Cannot paste row data to cell"

				pasteFunctions.append( functools.partial( __setPlug, cell, atTime, value ) )

				# Set cell enabled state last, such that when copying from a cell that doesn't adopt
				# an enabled plug, to one that does, the final 'enabled' state matches.
				enabledPlug = __cellEnabledPlug( cell )
				if enabledPlug is not None :
					pasteFunctions.append( functools.partial( __setPlug, enabledPlug, atTime, __enabledValue( value ) ) )

	return pasteFunctions

def __plugNotPasteableReason( plug, value ) :

	if isinstance( value, IECore.CompoundData ) :
		for k, v in value.items() :
			if k in plug :
				reason = __plugNotPasteableReason( plug[k], v )
				if reason != "" :
					return reason

	elif isinstance( value, IECore.Data ) :
		if "value" in plug :
			if "value" in plug["value"] :
				# CellPlug with NameValuePlug
				destination = plug["value"]["value"]
			else :
				destination = plug["value"]
		else :
			destination = plug

		if not __plugSettable( destination ) :
			return "Plug is not settable {}".format( destination.relativeName( destination.ancestor( Gaffer.Spreadsheet.RowsPlug ) ) )

		if not Gaffer.PlugAlgo.canSetValueFromData( destination, value) :
			return "Value of type {} is not compatible with plug {}".format( value.typeName(), destination.relativeName( destination.ancestor( Gaffer.Spreadsheet.RowsPlug ) ) )

	return ""

def __plugSettable( plug ) :

	def settable( p ) :
		if Gaffer.Animation.isAnimated( p ) :
			curve = Gaffer.Animation.acquire( p )
			return not Gaffer.MetadataAlgo.readOnly( curve )
		else :
			return p.settable()

	if Gaffer.MetadataAlgo.readOnly( plug ) or not settable( plug ) :
		return False

	for p in Gaffer.Plug.RecursiveRange( plug ) :
		if Gaffer.MetadataAlgo.getReadOnly( p ) :
			return False

	return True

## \todo This check is only necessary to satisfy some of the tests from the prior implementation
# and to enforce the constraint of only allowing copy/paste with a consistent number of columns
# selected per row. Remove this once we relax that constraint.
def __isPlugMatrix( plugMatrix ) :

	if not plugMatrix :
		return False

	if not isinstance( plugMatrix, list ) :
		return False

	if len( plugMatrix ) == 0 :
		return False

	if not isinstance( plugMatrix[0], ( list, tuple ) ) :
		return False

	if len( plugMatrix[0] ) == 0 :
		return False

	## \todo It could be worth relaxing this constraint and support copy/paste
	# of selections with varying row lengths.
	if not all( [ len( x ) == len( plugMatrix[0] ) for x in plugMatrix[1:] ] ) :
		return False

	if not all( [ isinstance( x, Gaffer.Plug ) for row in plugMatrix for x in row ] ) :
		return False

	return True

def __cellEnabledPlug( plug ) :

	cellPlug = plug if isinstance( plug, Gaffer.Spreadsheet.CellPlug ) else plug.ancestor( Gaffer.Spreadsheet.CellPlug )
	if cellPlug is not None :
		return cellPlug.enabledPlug()

	return None

def __enabledValue( data ) :

	enabled = IECore.BoolData( True )

	if isinstance( data, IECore.CompoundData ) and "value" in data :
		valueData = data["value"]
		if "enabled" in data :
			enabled = data["enabled"]
		elif "enabled" in valueData :
			enabled = valueData["enabled"]

	return enabled

def __setPlug( cell, atTime, value ) :

	if isinstance( value, IECore.CompoundData ) :
		__setPlugFromCompoundData( cell, atTime, value )
	elif isinstance( value, IECore.Data ) :
		if "value" in cell :
			if "value" in cell["value"] :
				# Redirect to `value.value` plug when pasting to a NameValuePlug
				destination = cell["value"]["value"]
			else :
				destination = cell["value"]
		else :
			destination = cell

		Gaffer.PlugAlgo.setValueOrInsertKeyFromData( destination, atTime, value )

def __setPlugFromCompoundData( plug, atTime, compoundData ) :

	for k, v in compoundData.items() :
		if k == "name" and isinstance( plug, Gaffer.NameValuePlug ) :
			# We don't ever want to set the "name" plug of a NameValuePlug
			continue

		if isinstance( v, IECore.CompoundData ) and k in plug :
			__setPlugFromCompoundData( plug[k], atTime, v )
			continue

		destination = None
		if k == "value" and k in plug and k in plug[k] :
			# Redirect to `value.value` plug when pasting to a NameValuePlug
			destination = plug[k]["value"]
		elif k in plug :
			# Otherwise look for a plug matching our key
			destination = plug[k]
		elif k == "value" :
			destination = plug
		elif k == "enabled" :
			destination = __cellEnabledPlug( plug )

		if destination is not None :
			Gaffer.PlugAlgo.setValueOrInsertKeyFromData( destination, atTime, v )

def __setRowPlug( row, atTime, value ) :

	for plugName in ( "name", "enabled" ) :
		__setPlug( row[plugName], atTime, value[plugName] )

	for c in row["cells"].children() :
		if c.getName() in value["cells"] :
			__setPlug( c, atTime, value["cells"][c.getName()] )

def __isRowPlugData( data ) :

	return isinstance( data, IECore.CompoundData ) and set( data.keys() ) == { "name", "enabled", "cells" }

def __rowPlugMatchingCells( rowPlug, data ) :

	if not __isRowPlugData( data ) :
		return []

	return [ cell for cell in rowPlug["cells"].children() if cell.getName() in data["cells"] ]
