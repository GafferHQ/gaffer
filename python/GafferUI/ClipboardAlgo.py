##########################################################################
#
#  Copyright (c) 2025, Cinesite VFX Ltd. All rights reserved.
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

class _ClipboardAdaptor( object ) :

	def __init__( self, source ) :

		if isinstance( source, Gaffer.ObjectMatrix ) :
			self.__data = source
		elif isinstance( source, IECore.Data ) :
			self.__data = Gaffer.ObjectMatrix( 1, 1, [ source ] )
		else :
			self.__data = None

	def data( self ) :

		return self.__data

	def setData( self, data ) :

		self.__data = data

	def isValid( self ) :

		if not isinstance( self.__data, Gaffer.ObjectMatrix ) :
			return False

		for columnIndex in range( self.__data.width() ) :
			for rowIndex in range( 1, self.__data.height() ) :
				return _ClipboardAdaptor.__compatibleData( self.__data.value( columnIndex, 0 ), self.__data.value( columnIndex, rowIndex ) )

		return True

	def value( self, row, column, extractValue = False ) :

		value = self.__data.value( column % self.__data.width(), row % self.__data.height() )

		if extractValue and isinstance( value, IECore.CompoundData ) and "value" in value :
			value = value["value"]
			# Values copied from spreadsheets are nested within a CellPlug,
			# we want `CellPlug.value.value`.
			if isinstance( value, IECore.CompoundData ) and "value" in value :
				value = value["value"]

		return value

	def canPaste( self, target ) :

		if not self.isValid() :
			return False

		return self.nonPasteableReason( target ) == ""

	def paste( self, target, atTime = 0.0 ) :

		pasteFunctions, nonPasteableReason = self._pasteFunctionsAndNonPasteableReason( target, atTime )

		if nonPasteableReason != "" :
			return

		for f in pasteFunctions :
			f()

	def nonPasteableReason( self, target ) :

		_, reason = self._pasteFunctionsAndNonPasteableReason( target, 0 )
		return reason

	## Must be implemented by derived classes to return a tuple containing a list of callables
	# that perform the work of pasting the values in `self.data()` to `target` at `time`, and
	# a string describing why values are unable to be pasted to `target`, or "" if all values
	# can be pasted.
	def _pasteFunctionsAndNonPasteableReason( self, target, atTime = 0.0 ) :

		raise NotImplementedError

	@staticmethod
	def __compatibleData( data, otherData ) :

		if isinstance( data, ( dict, IECore.CompoundData ) ) :

			if type( data ) != type( otherData ) :
				return False
			if data.keys() != otherData.keys() :
				return False
			for a, b in zip( data.values(), otherData.values() ) :
				if not _ClipboardAdaptor.__compatibleData( a, b ) :
					return False

		elif isinstance( data, ( list, tuple, IECore.ObjectVector ) ) :

			if type( data ) != type( otherData ) :
				return False
			if len( data ) != len( otherData ) :
				return False
			for a, b in zip( data, otherData ) :
				if not _ClipboardAdaptor.__compatibleData( a, b ) :
					return False

		elif isinstance( data, IECore.Data ) :

			if type( data ) == type( otherData ) :
				return True
			## \todo Another situation where I'm creating a temporary plug to test whether data can be set on it
			# might need a way to test this from two Data types directly?
			testPlug = Gaffer.PlugAlgo.createPlugFromData( "value", Gaffer.Plug.Direction.In, Gaffer.Plug.Flags.Default, data )
			if not Gaffer.PlugAlgo.canSetValueFromData( testPlug, otherData ) :
				return False

		return True

class _PathListingAdaptor( _ClipboardAdaptor ) :

	def __init__( self, source ) :

		_ClipboardAdaptor.__init__( self, source )

		if isinstance( source, GafferUI.PathListingWidget ) :
			self.__dataFromPathListing( source )

	def __dataFromPathListing( self, pathListing ) :

		values = []

		path = pathListing.getPath().copy()
		selection = self.__orderedSelection( pathListing )
		for pathString, columns in selection :
			path.setFromString( pathString )

			for column in columns :
				## \todo Store values as a CompoundData including the column name so values could be pasted to a row and matched by name.
				values.append( column.cellData( path ).value )

		rows = len( selection )
		columns = len( selection[0][1] )
		if len( values ) == rows * columns :
			self.setData( Gaffer.ObjectMatrix( columns, rows, values ) )

	## \todo Support `atTime` once `Inspection::edit()` has support for it.
	def _pasteFunctionsAndNonPasteableReason( self, pathListing, atTime ) :

		if not self.isValid() :
			return [], "Clipboard contents not pasteable"

		pasteFunctions = []

		path = pathListing.getPath().copy()
		selection = self.__orderedSelection( pathListing )
		for rowIndex, (pathString, columns) in enumerate( selection ) :
			sourceIndex = 0
			path.setFromString( pathString )
			inspectionContext = path.inspectionContext()
			if inspectionContext is None :
					continue

			with inspectionContext :
				for column in columns :
					if not hasattr( column, "inspector" ) :
						return [], "Column \"{}\" does not support pasting.".format( column.headerData().value )

					inspection = column.inspector().inspect()
					if inspection is None :
						return "Path \"{}\" is not editable.".format( pathString ), []

					value = self.value( rowIndex, sourceIndex, extractValue = True )
					sourceIndex += 1

					if inspection.canEdit( value ) :
						pasteFunctions.append( functools.partial( inspection.edit, value ) )
					elif len( columns ) > 1 :
						return [], "{} : {}".format( column.headerData().value, inspection.nonEditableReason( value ) )
					else :
						return [], inspection.nonEditableReason( value )

		return pasteFunctions, ""

	@staticmethod
	def __orderedSelection( pathListing ) :

		# Returns the current selection ordered based on the
		# current sort order of the PathListingWidget.

		rows = {}
		for selection, column in zip( pathListing.getSelection(), pathListing.getColumns() ) :
			for path in selection.paths() :
				rows.setdefault( path, [] ).append( column )

		matrix = []
		sortedSelection = pathListing.getSortedSelection()
		for path, columns in sorted( rows.items(), key = lambda item : sortedSelection.index( item[0] ) ) :
			matrix.append( ( path, columns ) )

		return matrix

class _PlugMatrixAdaptor( _ClipboardAdaptor ) :

	def __init__( self, source ) :

		_ClipboardAdaptor.__init__( self, source )

		if self._isPlugMatrix( source ) :

			self.setData( Gaffer.ObjectMatrix( len( source[0] ), len( source ), [ self.__fromPlug( column ) for row in source for column in row ] ) )

	def canPasteRows( self, rowsPlug ) :

		if not self.isValid() :
			return False

		if Gaffer.MetadataAlgo.readOnly( rowsPlug ) :
			return False

		for rowIndex in range( self.data().height() ) :
			if not self.__rowPlugMatchingCells( rowsPlug.defaultRow(), self.data()[0, rowIndex] ) :
				return False

		return self.canPaste( [ [ rowsPlug.defaultRow() ] ] )

	def pasteRows( self, rowsPlug ) :

		# addRows currently returns None, so this is easier
		newRows = [ rowsPlug.addRow() for _ in range( self.data().height() ) ]

		# We know these aren't animated as we've just made them so time is irrelevant
		self.paste( [ [ row ] for row in newRows ], 0 )

	def _pasteFunctionsAndNonPasteableReason( self, plugMatrix, atTime ) :

		if not self._isPlugMatrix( plugMatrix ) :
			return [], "No plugs to edit"

		# Check global read-only status, early out if none can be modified
		rowsPlug = plugMatrix[0][0].ancestor( Gaffer.Spreadsheet.RowsPlug )
		if rowsPlug and Gaffer.MetadataAlgo.readOnly( rowsPlug ) :
			return [], "Spreadsheet is read-only"

		pasteFunctions = []

		for rowIndex, row in enumerate( plugMatrix ) :
			for columnIndex, cell in enumerate( row ) :
				value = self.value( rowIndex, columnIndex )
				if isinstance( cell, Gaffer.Spreadsheet.RowPlug ) :
					for c in self.__rowPlugMatchingCells( cell, value ) :
						reason = self.__plugNotPasteableReason( c, value["cells"][ c.getName() ] )
						if reason != "" :
							return [], reason

					pasteFunctions.append( functools.partial( self.__setRowPlug, cell, atTime, value ) )

				else :
					reason = self.__plugNotPasteableReason( cell, value )
					if reason != "" :
						return [], reason

					if self.__isRowPlugData( value ) :
						return [], "Cannot paste row data to cell"

					pasteFunctions.append( functools.partial( self.__setPlug, cell, atTime, value ) )

					# Set cell enabled state last, such that when copying from a cell that doesn't adopt
					# an enabled plug, to one that does, the final 'enabled' state matches.
					enabledPlug = self.__cellEnabledPlug( cell )
					if enabledPlug is not None :
						pasteFunctions.append( functools.partial( self.__setPlug, enabledPlug, atTime, self.__enabledValue( value ) ) )

		return pasteFunctions, ""

	@staticmethod
	def _isPlugMatrix( plugMatrix ) :

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

		if not all( [ len( x ) == len( plugMatrix[0] ) for x in plugMatrix[1:] ] ) :
			return False

		if not all( [ isinstance( x, Gaffer.Plug ) for row in plugMatrix for x in row ] ) :
			return False

		return True

	@staticmethod
	def __fromPlug( plug ) :

		if hasattr( plug, "getValue" ) :
			return plug.getValue()

		return IECore.CompoundData( { child.getName() : _PlugMatrixAdaptor.__fromPlug( child ) for child in plug } )

	@staticmethod
	def __setRowPlug( row, atTime, value ) :

		for plugName in ( "name", "enabled" ) :
			_PlugMatrixAdaptor.__setPlug( row[plugName], atTime, value[plugName] )

		for c in row["cells"].children() :
			if c.getName() in value["cells"] :
				_PlugMatrixAdaptor.__setPlug( c, atTime, value["cells"][c.getName()] )

	@staticmethod
	def __setPlug( cell, atTime, value ) :

		if isinstance( value, IECore.CompoundData ) :
			_PlugMatrixAdaptor.__setPlugFromCompoundData( cell, atTime, value )
		elif isinstance( value, IECore.Data ) :
			if "value" in cell :
				if "value" in cell["value"] :
					# Redirect to `value.value` plug when pasting to a NameValuePlug
					destination = cell["value"]["value"]
				else :
					destination = cell["value"]
			else :
				destination = cell

			Gaffer.PlugAlgo.setValueOrAddKeyFromData( destination, atTime, value )

	@staticmethod
	def __setPlugFromCompoundData( plug, atTime, compoundData ) :

		for k, v in compoundData.items() :
			if k == "name" and isinstance( plug, Gaffer.NameValuePlug ) :
				# We don't ever want to set the "name" plug of a NameValuePlug
				continue

			if isinstance( v, IECore.CompoundData ) and k in plug :
				_PlugMatrixAdaptor.__setPlugFromCompoundData( plug[k], atTime, v )
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
				destination = _PlugMatrixAdaptor.__cellEnabledPlug( plug )

			if destination is not None :
				Gaffer.PlugAlgo.setValueOrAddKeyFromData( destination, atTime, v )

	@staticmethod
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

	@staticmethod
	def __cellEnabledPlug( plug ) :

		cellPlug = plug if isinstance( plug, Gaffer.Spreadsheet.CellPlug ) else plug.ancestor( Gaffer.Spreadsheet.CellPlug )
		if cellPlug is not None :
			return cellPlug.enabledPlug()

		return None

	@staticmethod
	def __plugNotPasteableReason( plug, value ) :

		if isinstance( value, IECore.CompoundData ) :
			for k, v in value.items() :
				if k in plug :
					reason = _PlugMatrixAdaptor.__plugNotPasteableReason( plug[k], v )
					if reason != "" :
						return reason

		elif isinstance( value, IECore.Data ) :
			if "value" in plug :
				if "value" in plug["value"] :
					# cell plug with NameValuePlug
					destination = plug["value"]["value"]
				else :
					destination = plug["value"]
			else :
				destination = plug

			if not _PlugMatrixAdaptor.__plugSettable( destination ) :
				return "Plug is not settable {}".format( destination.relativeName( destination.ancestor( Gaffer.Spreadsheet.RowsPlug ) ) )

			if not Gaffer.PlugAlgo.canSetValueFromData( destination, value) :
				return "Value of type {} is not compatible {}".format( type( value ), destination.relativeName( destination.ancestor( Gaffer.Spreadsheet.RowsPlug ) ) )

		return ""

	@staticmethod
	def __enabledValue( data ) :

		enabled = IECore.BoolData( True )

		if isinstance( data, IECore.CompoundData ) and "value" in data :
			valueData = data["value"]
			if "enabled" in data :
				enabled = data["enabled"]
			elif "enabled" in valueData :
				enabled = valueData["enabled"]

		return enabled

	@staticmethod
	def __isRowPlugData( data ) :

		return isinstance( data, IECore.CompoundData ) and set( data.keys() ) == { "name", "enabled", "cells" }

	@staticmethod
	def __rowPlugMatchingCells( rowPlug, data ) :

		if not _PlugMatrixAdaptor.__isRowPlugData( data ) :
			return []

		return [ cell for cell in rowPlug["cells"].children() if cell.getName() in data["cells"] ]

class _SpreadsheetAdaptor( _PlugMatrixAdaptor ) :

	def __init__( self, source ) :

		if isinstance( source, GafferUI.SpreadsheetUI._PlugTableView._PlugTableView ) :
			source = self._createPlugMatrixFromCells( source.selectedPlugs() )

		_PlugMatrixAdaptor.__init__( self, source )

	@staticmethod
	def _createPlugMatrixFromCells( cellPlugs ) :

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

	def _pasteFunctionsAndNonPasteableReason( self, spreadsheet, atTime ) :

		return _PlugMatrixAdaptor._pasteFunctionsAndNonPasteableReason( self, self._createPlugMatrixFromCells( spreadsheet.selectedPlugs() ), atTime )

## Returns True if `source` can be copied to the clipboard.
def canCopy( source ) :

	adaptor = __createAdaptor( source )
	return adaptor is not None and adaptor.isValid()

## Copies `source` to the clipboard.
def copy( source ) :

	assert( canCopy( source ) )
	__applicationRoot( source ).setClipboardContents( __createAdaptor( source ).data() )

## Returns the reason why the current clipboard cannot be pasted to `target`.
def nonPasteableReason( target ) :

	return __createAdaptorFromClipboard( target ).nonPasteableReason( target )

## Returns True if the current clipboard contents can be pasted to `target`.
def canPaste( target ) :

	return __createAdaptorFromClipboard( target ).canPaste( target )

## Paste the current clipboard contents to `target`.
def paste( target, atTime = 0.0 ) :

	adaptor = __createAdaptorFromClipboard( target )
	assert( adaptor.canPaste( target ) )
	adaptor.paste( target, atTime )

## Copies the provided Spreadsheet `rowPlugs` to the clipboard.
def copyRows( rowPlugs ) :

	adaptor = _PlugMatrixAdaptor( [ [ row ] for row in rowPlugs ] )
	if adaptor.isValid() :
		rowPlugs[0].ancestor( Gaffer.ApplicationRoot ).setClipboardContents( adaptor.data() )

## Returns True if the clipboard contents can be pasted as new rows at the
# end of the supplied Spreadsheet rows plug.
def canPasteRows( rowsPlug ) :

	return _PlugMatrixAdaptor( rowsPlug.ancestor( Gaffer.ApplicationRoot ).getClipboardContents() ).canPasteRows( rowsPlug )

## Pastes the clipboard data as new rows at the end of the supplied rows plug.
# Columns are matched by name (and type), allowing rows to be copied
# between Spreadsheets with different configurations. Cells in the
# target Spreadsheet with no data will be set to the default value for
# that column.
def pasteRows( rowsPlug ) :

	adaptor = _PlugMatrixAdaptor( rowsPlug.ancestor( Gaffer.ApplicationRoot ).getClipboardContents() )
	assert( adaptor.canPasteRows( rowsPlug ) )

	adaptor.pasteRows( rowsPlug )

def __applicationRoot( target ) :

	if isinstance( target, GafferUI.Widget ) :
		scriptNode = target.ancestor( GafferUI.Editor ).scriptNode()
		return scriptNode.ancestor( Gaffer.ApplicationRoot )
	elif _PlugMatrixAdaptor._isPlugMatrix( target ) :
		return target[0][0].ancestor( Gaffer.ApplicationRoot )

	return None

def __createAdaptorFromClipboard( target ) :

	clipboard = __applicationRoot( target ).getClipboardContents()

	if isinstance( target, GafferUI.PathListingWidget ) :
		return _PathListingAdaptor( clipboard )
	elif isinstance( target, GafferUI.SpreadsheetUI._PlugTableView._PlugTableView ) :
		return _SpreadsheetAdaptor( clipboard )
	elif _PlugMatrixAdaptor._isPlugMatrix( target ) :
		return _PlugMatrixAdaptor( clipboard )

	return None

def __createAdaptor( source ) :

	if isinstance( source, GafferUI.PathListingWidget ) :
		return _PathListingAdaptor( source )
	elif isinstance( source, GafferUI.SpreadsheetUI._PlugTableView._PlugTableView ) :
		return _SpreadsheetAdaptor( source )
	elif _PlugMatrixAdaptor._isPlugMatrix( source ) :
		return _PlugMatrixAdaptor( source )

	return None
