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
#   - There is a contiguous selection across multiple rows/columns.
#   - Non-contiguous selections have consistent column types per row.
#
# `plugMatrix` should be a row-major list of value plugs,
# as returned by createPlugMatrixFromCells, ie: [ [ r1c1, ... ], [ r2c1, ... ] ]
#
# \note Triggers compute of the source plugs to determine value compatibility.
def canCopyPlugs( plugMatrix ) :

	if not plugMatrix :
		return False

	if not plugMatrix[0] :
		return False

	# Check each row has the same column configuration
	if len( plugMatrix ) > 1 :

		def rowData( row ) :
			return [ ValueAdaptor.get( cell ) for cell in row ]

		columnTemplate = rowData( plugMatrix[0] )
		for row in plugMatrix[ 1 : ] :
			if not ValueAdaptor.dataSchemaMatches( rowData( row ), columnTemplate )  :
				return False

	return True

## Builds a 'paste-able' data for the supplied plug matrix
# For Spreadsheet rows, the matrix should consist of a single column
# containing the Spreadsheet.RowPlug for each row to be copied.
# \see copyRows
def valueMatrix( plugMatrix ) :

	assert( canCopyPlugs( plugMatrix ) )
	return IECore.ObjectVector(
		[ IECore.ObjectVector( [ ValueAdaptor.get( column ) for column in row ] ) for row in plugMatrix ]
	)

# Returns True if the supplied object appears to be pasteable cell data
def isValueMatrix( data ) :

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
		if not ValueAdaptor.dataSchemaMatches( data[i], templateRow ) :
			return False

	return True

# Returns True if the supplied data can be pasted on to the supplied
# spreadsheet cell plugs, in that the cell value types are compatible with the
# corresponding valueMatrix.
# \note Triggers compute of the target plugs to determine value compatibility.
def canPasteCells( valueMatrix, plugMatrix ) :

	valueMatrix = __coerceToValueMatrixIfRequired( valueMatrix )

	if not isValueMatrix( valueMatrix ) :
		return False

	# Check global read-only status, early out if none can be modified
	rowsPlug = plugMatrix[0][0].ancestor( Gaffer.Spreadsheet.RowsPlug )
	if rowsPlug and Gaffer.MetadataAlgo.readOnly( rowsPlug ) :
		return False

	# Though we know valueMatrix is coherent, we still need to check the
	# full target cell matrix as it may be of different dimensions
	# and/or made from a non-contiguous selection.
	# This allows us to support copy/paste entirely by compatible value type,
	# rather than any semantics of the plugs themselves, which maximises the
	# potential re-use between columns.
	for targetRowIndex, row in enumerate( plugMatrix ) :
		for targetColumnIndex, cell in enumerate( row ) :
			data = __dataForPlug( targetRowIndex, targetColumnIndex, valueMatrix )
			if not ValueAdaptor.canSet( data, cell ) :
				return False

	return True

def pasteCells( valueMatrix, plugs, atTime ) :

	valueMatrix = __coerceToValueMatrixIfRequired( valueMatrix )

	assert( canPasteCells( valueMatrix, plugs ) )

	for rowIndex, row in enumerate( plugs ) :
		for columnIndex, cell in enumerate( row ) :
			ValueAdaptor.set( __dataForPlug( rowIndex, columnIndex, valueMatrix ), cell, atTime )

## Returns a value matrix for the supplied row plugs.
def copyRows( rowPlugs ) :

	return valueMatrix( [ [ row ] for row in rowPlugs ] )

## Returns True if the supplied data can be pasted as new rows.
# Columns are matched by name (and type), allowing rows to be copied
# between Spreadsheets with different configurations. Cells in the
# target Spreadsheet with no data will be set to the default value for
# that column.
def canPasteRows( data, rowsPlug ) :

	if not isValueMatrix( data ) :
		return False

	# Check global read-only status, early out if none can be modified
	if Gaffer.MetadataAlgo.readOnly( rowsPlug ) :
		return False

	return canPasteCells( data, [ [ rowsPlug.defaultRow() ] ] )

# Pastes the supplied data as new rows at the end of the supplied rows plug.
def pasteRows( valueMatrix, rowsPlug ) :

	assert( canPasteRows( valueMatrix, rowsPlug ) )

	# addRows currently returns None, so this is easier
	newRows = [ rowsPlug.addRow() for _ in valueMatrix ]
	# We know these aren't animated as we've just made them so time is irrelevant
	pasteCells( valueMatrix, [ [ row ] for row in newRows ], 0 )

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

def __coerceToValueMatrixIfRequired( data ) :

	if isinstance( data, IECore.Data ) :
		data = IECore.ObjectVector( [ IECore.ObjectVector( [ data ] ) ] )

	return data

# Wraps the lookup indices into the available data space
def __dataForPlug( targetRowIndex, targetColumnIndex, data ) :

	return data[ targetRowIndex % len(data) ][ targetColumnIndex % len(data[0]) ]

## Value Adaptors bridge plugs and data within a value matrix.
# They allow custom extraction of plug data for copy or mis-matched types to be
# adapted to a target plug for paste. Adaptors are registered via plug class.
# Callers should always use the base class ValueAdaptor get/canSet/set methods.
# Derived classes should re-implement _canSet, _set or _get as required.
#
# Note: At present, unless overridden, ValueAdaptors are not recursive. ie: An
# adaptor will only be used if there is one registered for the specific plug
# passed to get/canSet/set. Some adaptors may choose to call get/canSet/set
# themselves to allow other registered adaptors to run for their child plugs.
# This prohibits per-leaf/nested value adaption, but hopefully simplifies
# understanding of when a specific adaptor may run.
class ValueAdaptor :

	__registry = {}

	# \return An IECore.Data that represents either the plug value, or a hierarchy
	# of CompoundData representing the values of the plug's leaves.
	@staticmethod
	def get( plug ) :

		return ValueAdaptor.__adaptor( plug )._get( plug )

	## \return True if the supplied data can be set on the specified plug either
	# directly, or via some transformation.
	# \note Triggers compute of the target plugs.
	@staticmethod
	def canSet( data, plug ) :

		return ValueAdaptor.__adaptor( plug )._canSet( data, plug )

	## Sets the specified plug's value at the given time, keyframing animated values.
	# \note This should be called from within an UndoScope.
	@staticmethod
	def set( data, plug, atTime ) :

		ValueAdaptor.__adaptor( plug )._set( data, plug, atTime )

	## \return True if the schema (ie. class hierarchy) of the two supplied
	# objects match, regardless of their values.
	@staticmethod
	def dataSchemaMatches( data, otherData ) :

		if type( data ) != type( otherData ) :
			return False

		if isinstance( data, ( dict, IECore.CompoundData ) ) :

			if data.keys() != otherData.keys() :
				return False
			for a, b in zip( data.values(), otherData.values() ) :
				if not ValueAdaptor.dataSchemaMatches( a, b ) :
					return False

		elif isinstance( data, ( list, tuple, IECore.ObjectVector ) ) :

			if len( data ) != len( otherData ) :
				return False
			for a, b in zip( data, otherData ) :
				if not ValueAdaptor.dataSchemaMatches( a, b ) :
					return False

		return True

	@staticmethod
	def registerAdaptor( plugType, cls ) :

		ValueAdaptor.__registry[ plugType ] = cls

	@classmethod
	def _get( cls, plug ) :

		if hasattr( plug, 'getValue' ) :
			return IECore.CompoundData( { "v" : plug.getValue() } )["v"]

		return IECore.CompoundData( { child.getName() : cls._get( child ) for child in plug } )

	## Derived classes should take care to ensure that _canSet only returns True
	# when _set is capable of transforming the supplied data so that it can be
	# set on the specified plug.
	@classmethod
	def _canSet( cls, data, plug ) :

		if not cls._canSetKeyOrValue( plug ) :
			return False

		plugData = ValueAdaptor.get( plug )

		if cls.dataSchemaMatches( data, plugData ) :
			return True

		# Support basic value embedding for NameValuePlug -> ValuePlug
		if isinstance( data, IECore.CompoundData ) and "value" in data :
			return ValueAdaptor.dataSchemaMatches( data[ "value" ], plugData )

		return False

	## Derived classes should re-implement _canSet to match any custom logic added here.
	@classmethod
	def _set( cls, data, plug, atTime ) :

		if isinstance( data, IECore.CompoundData ) :
			# Only perform schema check for compound data types, to allow value coercion for basic types
			if not ValueAdaptor.dataSchemaMatches( data, ValueAdaptor.get( plug ) ) and "value" in data :
				data = data[ "value" ]

		if hasattr( plug, 'setValue' ) :
			ValueAdaptor._setOrKeyValue( plug, data, atTime )
		else :
			for childName, childData in data.items() :
				cls._set( childData, plug[ childName ], atTime )

	@staticmethod
	def _canSetKeyOrValue( plug ) :

		def settable( p ) :
			if Gaffer.Animation.isAnimated( p ) :
				curve = Gaffer.Animation.acquire( p )
				return not Gaffer.MetadataAlgo.readOnly( curve )
			else :
				return p.settable()

		# Ensure we consider child plugs, eg: components of a V3fPlug
		if Gaffer.MetadataAlgo.readOnly( plug ) or not settable( plug ) :
			return False
		for p in Gaffer.Plug.RecursiveRange( plug ) :
			if Gaffer.MetadataAlgo.getReadOnly( p ) :
				return False

		return True

	@staticmethod
	def _setOrKeyValue( plug, value, atTime ) :

		if hasattr( value, 'value' ) :
			value = value.value

		if Gaffer.Animation.isAnimated( plug ) :
			curve = Gaffer.Animation.acquire( plug )
			curve.addKey( Gaffer.Animation.Key( atTime, value, Gaffer.Animation.Interpolation.Linear ) )
		else :
			plug.setValue( value )

	@staticmethod
	def __adaptor( plug ) :

		return ValueAdaptor.__registry.get( type( plug ), ValueAdaptor )

class NameValuePlugValueAdaptor( ValueAdaptor ) :

	@classmethod
	def _canSet( cls, data, nameValuePlug ) :

		if isinstance( data, IECore.CompoundData ) and "value" in data :
			valueData = data[ "value" ]
			if "enabled" in nameValuePlug :
				if "enabled" in data and not ValueAdaptor.canSet( data[ "enabled" ], nameValuePlug[ "enabled" ] ) :
					return False
		else :
			# Allow simple data to be pasted onto the value plug
			valueData = data

		return ValueAdaptor.canSet( valueData, nameValuePlug[ "value" ] )

	@classmethod
	def _set( cls, data, nameValuePlug, atTime ) :

		# We should _never_ set the name of an NVP as it's not exposed in the
		# UI. It's only there as it simplifies things greatly if we don't
		# special case plugs in the general case in the Spreadsheet. If we did,
		# and you pasted across columns, it would duplicate the plug name,
		# which can have catastrophic results for nodes such as StandardOptions.

		if isinstance( data, IECore.CompoundData ) and "value" in data :
			valueData = data[ "value" ]
			enabledData = data[ "enabled" ] if "enabled" in data else None
		else :
			# Allow simple data to be pasted onto the value plug
			valueData = data
			enabledData = None

		ValueAdaptor.set( valueData, nameValuePlug[ "value" ], atTime )

		if "enabled" in nameValuePlug and enabledData is not None :
			ValueAdaptor.set( enabledData, nameValuePlug[ "enabled" ], atTime )

ValueAdaptor.registerAdaptor( Gaffer.NameValuePlug, NameValuePlugValueAdaptor )

class CellPlugValueAdaptor( ValueAdaptor ) :

	@classmethod
	def _canSet( cls, data, cellPlug ) :

		enabledData, valueData = CellPlugValueAdaptor.__enabledAndValueData( data )

		if enabledData is not None and not ValueAdaptor.canSet( enabledData, cellPlug.enabledPlug() ) :
			return False

		return ValueAdaptor.canSet( valueData, cellPlug[ "value" ] )

	@classmethod
	def _set( cls, data, cellPlug, atTime ) :

		enabledData, valueData = CellPlugValueAdaptor.__enabledAndValueData( data )

		ValueAdaptor.set( valueData, cellPlug[ "value" ], atTime )

		# Set enabled state last, such that when copying from a cell that doesn't adopt
		# an enabled plug, to one that does, the final 'enabled' state matches.
		if enabledData is not None :
			ValueAdaptor.set( enabledData, cellPlug.enabledPlug(), atTime )

	@staticmethod
	def __enabledAndValueData( data ) :

		enabledData = None

		if isinstance( data, IECore.CompoundData ) and "value" in data :
			valueData = data[ "value" ]
			if "enabled" in data :
				enabledData = data[ "enabled" ]
			elif "enabled" in valueData :
				enabledData = valueData[ "enabled" ]
		else :
			valueData = data

		return enabledData, valueData

ValueAdaptor.registerAdaptor( Gaffer.Spreadsheet.CellPlug, CellPlugValueAdaptor )

class FloatPlugValueAdaptor( ValueAdaptor ) :

	@classmethod
	def _canSet( cls, data, plug ) :

		# FloatPlug.setValue will take care conversion for us
		if isinstance( data, ( IECore.FloatData, IECore.IntData ) ) :
			return cls._canSetKeyOrValue( plug )

		return ValueAdaptor._canSet( data, plug )

ValueAdaptor.registerAdaptor( Gaffer.FloatPlug, FloatPlugValueAdaptor )

class StringPlugValueAdaptor( ValueAdaptor ) :

	@classmethod
	def _canSet( cls, data, plug ) :

		if isinstance( data, IECore.StringVectorData ) :
			if len( data ) < 2 :
				return cls._canSetKeyOrValue( plug )

		return ValueAdaptor._canSet( data, plug )

	@classmethod
	def _set( cls, data, plug, atTime ) :

		if isinstance( data, IECore.StringVectorData ) :
			if len( data ) == 1 :
				data = IECore.StringData( data[ 0 ] )
			else :
				data = IECore.StringData( "" )

		ValueAdaptor._set( data, plug, atTime )

ValueAdaptor.registerAdaptor( Gaffer.StringPlug, StringPlugValueAdaptor )

class StringVectorDataPlugValueAdaptor( ValueAdaptor ) :

	@classmethod
	def _canSet( cls, data, plug ) :

		if isinstance( data, IECore.StringData ) :
			return cls._canSetKeyOrValue( plug )

		return ValueAdaptor._canSet( data, plug )

	@classmethod
	def _set( cls, data, plug, atTime ) :

		if isinstance( data, IECore.StringData ) :
			data = IECore.StringVectorData( [ data.value ] )

		ValueAdaptor._set( data, plug, atTime )

ValueAdaptor.registerAdaptor( Gaffer.StringVectorDataPlug, StringVectorDataPlugValueAdaptor )

## Allows RowPlugs to be copy/pasted across different column configurations,
# matching by the column names.
class RowPlugValueAdaptor( ValueAdaptor ) :

	@classmethod
	def _canSet( cls, data, rowPlug ) :

		if not isinstance( data, IECore.CompoundData ) or set( data.keys() ) != { "name", "enabled", "cells" } :
			return False

		cellData = data[ "cells" ]
		matchingCells = [ cell for cell in rowPlug[ "cells" ].children() if cell.getName() in cellData ]
		if not matchingCells :
			return False

		return all( [ ValueAdaptor.canSet( cellData[ cell.getName() ], cell ) for cell in matchingCells ] )

	@classmethod
	def _set( cls, rowData, rowPlug, atTime ) :

		# Name/enabled
		for plugName in ( "name", "enabled" ) :
			ValueAdaptor.set( rowData[ plugName ], rowPlug[ plugName ], atTime )

		# Cells
		cellData = rowData[ "cells" ]
		for cell in rowPlug[ "cells" ].children() :
			data = cellData.get( cell.getName(), None )
			if data is not None :
				ValueAdaptor.set( data, cell, atTime )

ValueAdaptor.registerAdaptor( Gaffer.Spreadsheet.RowPlug, RowPlugValueAdaptor )
