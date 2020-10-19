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

import Gaffer

import IECore

## Returns True if the supplied plugs are sufficiently consistent
# to copy values from. Copy is possible if:
#
#   - There is a single row or column.
#   - Non-contiguous selections are consistent across columns.
#
# `plugs` should be a row-major list of spreadsheet plugs
def canCopyCells( cellPlugMatrix ) :

	if len( cellPlugMatrix ) == 0 :
		return False

	if len( cellPlugMatrix[0] ) == 0 :
		return False

	# Check each row has the same column configuration
	if len( cellPlugMatrix ) > 1 :

		def rowData( row ) :
			return [ __getValueAsData( cell ) for cell in row ]

		columnTemplate = rowData( cellPlugMatrix[0] )
		for row in cellPlugMatrix[ 1 : ] :
			if not __dataSchemaMatches( rowData( row ), columnTemplate )  :
				return False

	return True

## Builds a 'paste-able' data for the supplied cell plugs
def cellData( cellPlugMatrix ) :

	assert( canCopyCells( cellPlugMatrix ) )
	return IECore.ObjectVector( [ IECore.ObjectVector( [ __getValueAsData( cell ) for cell in row ] ) for row in cellPlugMatrix ] )

def isCellData( data ) :

	if not data :
		return False

	if not isinstance( data, IECore.ObjectVector ) :
		return False

	if not all( [ isinstance( row, IECore.ObjectVector ) and row for row in data ] ) :
		return False

	templateRow = data[ 0 ]

	if not all( [ isinstance( valueData, IECore.Data ) for valueData in templateRow ] ) :
		return False

	for i in range( 1, len(data) ) :
		if not __dataSchemaMatches( data[i], templateRow ) :
			return False

	return True

def canPasteCells( cellData, cellPlugMatrix ) :

	assert( isCellData( cellData ) )

	# Check global read-only status, early out if none can be modified
	rowsPlug = cellPlugMatrix[0][0].ancestor( Gaffer.Spreadsheet.RowsPlug )
	if rowsPlug and Gaffer.MetadataAlgo.readOnly( rowsPlug ) :
		return False

	for targetRowIndex, row in enumerate( cellPlugMatrix ) :
		for targetColumnIndex, cell in enumerate( row ) :
			data = __dataForCell( targetRowIndex, targetColumnIndex, cellData )
			if not __dataSchemaMatches( data, __getValueAsData( cell ) ) :
				return False

	return True

def pasteCells( cellData, plugs ) :

	assert( canPasteCells( cellData, plugs ) )

	for targetRowIndex, row in enumerate( plugs ) :
		for targetColumnIndex, cell in enumerate( row ) :
			__setValueFromData( cell, __dataForCell( targetRowIndex, targetColumnIndex, cellData ) )

## Takes an arbitrary list of cell plugs and groups them by row, ordered by
# column to be compatible with copy/paste. Non-cell plugs are discarded.
def createPlugMatrix( cellPlugs ) :

	if len( cellPlugs ) == 0 :
		return []

	rowsPlug = next( iter( cellPlugs ) ).ancestor( Gaffer.Spreadsheet.RowsPlug )
	assert( rowsPlug is not None )

	allRowPlugs = rowsPlug.children()

	rows = {}
	for cell in cellPlugs :

		rowPlug = cell.ancestor( Gaffer.Spreadsheet.RowPlug )
		rowIndex = allRowPlugs.index( rowPlug )
		columnIndex = rowPlug["cells"].children().index( cell )

		if rowIndex == -1 or columnIndex == -1 :
			continue

		rows.setdefault( rowIndex, {} )[ columnIndex ] = cell

	return [ [ row[column] for column in sorted(row) ] for _, row in sorted( rows.items() ) ]

def __dataForCell( targetRowIndex, targetColumnIndex, data ) :

	return data[ targetRowIndex % len(data) ][ targetColumnIndex % len(data[0]) ]

def __getValueAsData( plug ) :

	if hasattr( plug, 'getValue' ) :
		return IECore.CompoundData( { "v" : plug.getValue() } )["v"]

	return IECore.CompoundData( { child.getName() : __getValueAsData( child ) for child in plug } )

def __setValueFromData( plug, data ) :

	if Gaffer.MetadataAlgo.readOnly( plug ) :
		return

	if hasattr( plug, 'setValue' ) :

		if hasattr( data, 'value' ) :
			data = data.value

		if Gaffer.Animation.isAnimated( plug ) :
			context = Gaffer.Context.current()
			curve = Gaffer.Animation.acquire( plug )
			if not Gaffer.MetadataAlgo.readOnly( curve ) :
				curve.addKey( Gaffer.Animation.Key( context.getTime(), data, Gaffer.Animation.Type.Linear ) )
		elif plug.settable() :
			plug.setValue( data )

	else :

		for childName, childData in data.items() :
			__setValueFromData( plug[ childName ], childData )

def __dataSchemaMatches( data, otherData ) :

	if type( data ) != type( otherData ) :
		return False

	if isinstance( data, ( dict, IECore.CompoundData ) ) :

		if data.keys() != otherData.keys() :
			return False
		for a, b in zip( data.values(), otherData.values() ) :
			if not __dataSchemaMatches( a, b ) :
				return False

	elif isinstance( data, ( list, tuple, IECore.ObjectVector ) ) :

		if len( data ) != len( otherData ) :
			return False
		for a, b in zip( data, otherData ) :
			if not __dataSchemaMatches( a, b ) :
				return False

	return True
