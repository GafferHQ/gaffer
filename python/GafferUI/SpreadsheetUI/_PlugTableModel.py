##########################################################################
#
#  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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

import IECore
import imath

import Gaffer
import GafferUI

from Qt import QtCore

class _PlugTableModel( QtCore.QAbstractTableModel ) :

	Mode = IECore.Enum.create( "RowNames", "Defaults", "Cells" )
	CellPlugEnabledRole = QtCore.Qt.UserRole

	def __init__( self, rowsPlug, context, mode, parent = None ) :

		QtCore.QAbstractTableModel.__init__( self, parent )

		self.__rowsPlug = rowsPlug
		self.__context = context
		self.__mode = mode

		self.__plugDirtiedConnection = rowsPlug.node().plugDirtiedSignal().connect( Gaffer.WeakMethod( self.__plugDirtied ) )
		self.__rowAddedConnection = rowsPlug.childAddedSignal().connect( Gaffer.WeakMethod( self.__rowAdded ) )
		self.__rowRemovedConnection = rowsPlug.childRemovedSignal().connect( Gaffer.WeakMethod( self.__rowRemoved ) )
		self.__columnAddedConnection = rowsPlug.defaultRow()["cells"].childAddedSignal().connect( Gaffer.WeakMethod( self.__columnAdded ) )
		self.__columnRemovedConnection = rowsPlug.defaultRow()["cells"].childRemovedSignal().connect( Gaffer.WeakMethod( self.__columnRemoved ) )
		self.__plugMetadataChangedConnection = Gaffer.Metadata.plugValueChangedSignal().connect( Gaffer.WeakMethod( self.__plugMetadataChanged ) )
		self.__contextChangedConnection = self.__context.changedSignal().connect( Gaffer.WeakMethod( self.__contextChanged ) )

	# Methods of our own
	# ------------------

	def mode( self ) :

		return self.__mode

	def rowsPlug( self ) :

		return self.__rowsPlug

	def plugForIndex( self, index ) :

		if not index.isValid() :
			return None

		if self.__mode in ( self.Mode.Cells, self.Mode.RowNames ) :
			row = self.__rowsPlug[index.row()+1]
		else :
			row = self.__rowsPlug[0]

		if self.__mode == self.Mode.RowNames :
			return row[index.column()]
		else :
			return row["cells"][index.column()]

	def valuePlugForIndex( self, index ) :

		plug = self.plugForIndex( index )
		if isinstance( plug, Gaffer.Spreadsheet.CellPlug ) :
			plug = plug["value"]

		return plug

	def indexForPlug( self, plug ) :

		rowPlug = plug.ancestor( Gaffer.Spreadsheet.RowPlug )
		if rowPlug is None :
			return QtCore.QModelIndex()

		if self.__mode in ( self.Mode.Cells, self.Mode.RowNames ) :
			rowIndex = rowPlug.parent().children().index( rowPlug )
			if rowIndex == 0 :
				return QtCore.QModelIndex()
			else :
				rowIndex -= 1
		else :
			rowIndex = 0

		if self.__mode == self.Mode.RowNames :
			if plug == rowPlug["name"] :
				columnIndex = 0
			elif plug == rowPlug["enabled"] :
				columnIndex = 1
			else :
				return QtCore.QModelIndex()
		else :
			cellPlug = plug if isinstance( plug, Gaffer.Spreadsheet.CellPlug ) else plug.ancestor( Gaffer.Spreadsheet.CellPlug )
			if cellPlug is not None :
				columnIndex = rowPlug["cells"].children().index( cellPlug )
			else :
				return QtCore.QModelIndex()

		return self.index( rowIndex, columnIndex )

	# Value Formatting
	# ================

	## Returns the value of the plug as it will be formatted in a Spreadsheet.
	@classmethod
	def formatValue( cls, plug, forToolTip = False ) :

		currentPreset = Gaffer.NodeAlgo.currentPreset( plug )
		if currentPreset is not None :
			return currentPreset

		formatter = cls.__valueFormatters.get( plug.__class__, cls.__defaultValueFormatter )
		return formatter( plug, forToolTip )

	## Registers a custom formatter for the specified `plugType`.
	# `formatter` must have the same signature as `formatValue()`.
	@classmethod
	def registerValueFormatter( cls, plugType, formatter ) :

		cls.__valueFormatters[plugType] = formatter

	__valueFormatters = {}

	@classmethod
	def __defaultValueFormatter( cls, plug, forToolTip ) :

		if not hasattr( plug, "getValue" ) :
			return ""

		value = plug.getValue()
		if isinstance( value, str ) :
			return value
		elif isinstance( value, ( int, float ) ) :
			return GafferUI.NumericWidget.valueToString( value )
		elif isinstance( value, ( imath.V2i, imath.V2f, imath.V3i, imath.V3f ) ) :
			return ", ".join( GafferUI.NumericWidget.valueToString( v ) for v in value )

		try :
			# Unknown type. If iteration is supported then use that.
			separator = "\n" if forToolTip else ", "
			return separator.join( str( x ) for x in value )
		except :
			# Otherwise just cast to string
			return str( value )

	# Decorations
	# ===========

	## Returns the decoration for the specified plug.
	@classmethod
	def decoration( cls, plug ) :

		decorator = cls.__valueDecorators.get( plug.__class__ )
		return decorator( plug ) if decorator is not None else None

	## Registers a function to return a decoration to be shown
	# alongside the formatted value. Currently the only supported
	# return type is `Color3f`.
	@classmethod
	def registerDecoration( cls, plugType, decorator ) :

		cls.__valueDecorators[plugType] = decorator

	__valueDecorators = {}

	# Overrides for methods inherited from QAbstractTableModel
	# --------------------------------------------------------

	def rowCount( self, parent = QtCore.QModelIndex() ) :

		if parent.isValid() :
			return 0

		if self.__mode == self.Mode.Defaults :
			return 1
		else :
			return len( self.__rowsPlug ) - 1

	def columnCount( self, parent = QtCore.QModelIndex() ) :

		if parent.isValid() :
			return 0

		if self.__mode == self.Mode.RowNames :
			return 2
		else :
			return len( self.__rowsPlug[0]["cells"] )

	def headerData( self, section, orientation, role ) :

		if role == QtCore.Qt.DisplayRole :
			if orientation == QtCore.Qt.Horizontal and self.__mode != self.Mode.RowNames :
				cellPlug = self.__rowsPlug.defaultRow()["cells"][section]
				label = Gaffer.Metadata.value( cellPlug, "spreadsheet:columnLabel" )
				if not label :
					label = IECore.CamelCase.toSpaced( cellPlug.getName() )
				return label
			return section

	def flags( self, index ) :

		result = QtCore.Qt.ItemIsSelectable

		# We use the ItemIsEnabled flag to reflect the state of
		# `RowPlug::enabledPlug()` for the row `index` is in.
		enabled = True
		plug = self.valuePlugForIndex( index )
		rowPlug = plug.ancestor( Gaffer.Spreadsheet.RowPlug )
		if plug != rowPlug["enabled"] :
			with self.__context :
				try :
					enabled = rowPlug["enabled"].getValue()
				except :
					pass

		if enabled :
			result |= QtCore.Qt.ItemIsEnabled

		# We use the ItemIsEditable flag to reflect the state of
		# readOnly metadata.

		if not Gaffer.MetadataAlgo.readOnly( plug ) :
			result |= QtCore.Qt.ItemIsEditable
			if isinstance( plug, Gaffer.BoolPlug ) :
				result |= QtCore.Qt.ItemIsUserCheckable

		return result

	def data( self, index, role ) :

		if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole :

			return self.__formatValue( index )

		elif role == QtCore.Qt.BackgroundColorRole :

			if index.row() % 2 == 0 :
				return GafferUI._Variant.toVariant( GafferUI._StyleSheet.styleColor( "background" ) )
			else:
				return GafferUI._Variant.toVariant( GafferUI._StyleSheet.styleColor( "backgroundAlt" ) )

		elif role == QtCore.Qt.DecorationRole :

			plug = self.valuePlugForIndex( index )
			with self.__context :
				try :
					value = self.decoration( plug )
				except :
					return None

			if value is None :
				return None
			elif isinstance( value, imath.Color3f ) :
				displayTransform = GafferUI.DisplayTransform.get()
				return GafferUI.Widget._qtColor( displayTransform( value ) )
			else :
				IECore.msg( IECore.Msg.Level.Error, "Spreadsheet Decoration", "Unsupported type {}".format( type( value ) ) )
				return None

		elif role == QtCore.Qt.CheckStateRole :

			plug = self.__checkStatePlug( index )
			if plug is not None :
				with self.__context :
					try :
						value = plug.getValue()
					except :
						return None
				return QtCore.Qt.Checked if value else QtCore.Qt.Unchecked

		elif role == QtCore.Qt.ToolTipRole :

			return self.__formatValue( index, forToolTip = True )

		elif role == self.CellPlugEnabledRole :

			plug = self.plugForIndex( index )
			enabled = True
			if isinstance( plug, Gaffer.Spreadsheet.CellPlug ) :
				with self.__context :
					try :
						enabled = plug.enabledPlug().getValue()
					except :
						return None
			return enabled

		return None

	def setData( self, index, value, role ) :

		# We use Qt's built-in direct editing of check states
		# as it is convenient, but all other editing is done
		# separately via `_EditWindow`.

		assert( role == QtCore.Qt.CheckStateRole )
		plug = self.__checkStatePlug( index )
		assert( isinstance( plug, Gaffer.BoolPlug ) )

		with Gaffer.UndoScope( plug.ancestor( Gaffer.ScriptNode ) ) :
			plug.setValue( value )

		return True

	# Methods of our own
	# ------------------

	def __checkStatePlug( self, index ) :

		valuePlug = self.valuePlugForIndex( index )
		if isinstance( valuePlug, Gaffer.BoolPlug ) :
			return valuePlug

		return None

	def __rowAdded( self, rowsPlug, row ) :

		## \todo Is there any benefit in finer-grained signalling?
		self.__emitModelReset()
		self.headerDataChanged.emit( QtCore.Qt.Vertical, 0, self.rowCount() )

	def __rowRemoved( self, rowsPlug, row ) :

		## \todo Is there any benefit in finer-grained signalling?
		self.__emitModelReset()

	def __columnAdded( self, cellsPlug, cellPlug ) :

		## \todo Is there any benefit in finer-grained signalling?
		self.__emitModelReset()
		self.headerDataChanged.emit( QtCore.Qt.Horizontal, 0, self.columnCount() )

	def __columnRemoved( self, cellsPlug, cellPlug ) :

		## \todo Is there any benefit in finer-grained signalling?
		self.__emitModelReset()

	def __plugDirtied( self, plug ) :

		if not self.__rowsPlug.isAncestorOf( plug ) :
			return

		parentPlug = plug.parent()
		if isinstance( parentPlug, Gaffer.Spreadsheet.RowPlug ) and plug.getName() == "enabled" :
			# Special case. The enabled plug affects the flags for the entire row.
			# Qt doesn't have a mechanism for signalling flag changes, so we emit `dataChanged`
			# instead, giving our delegate the kick it needs to redraw.
			rowIndex = parentPlug.parent().children().index( parentPlug )
			self.dataChanged.emit( self.index( rowIndex, 0 ), self.index( rowIndex, self.columnCount() - 1 ) )
			return

		# Regular case. Emit `dataChanged` for just this one plug.
		index = self.indexForPlug( plug )
		if index.isValid() :
			self.dataChanged.emit( index, index )

	def __plugMetadataChanged( self, nodeTypeId, plugPath, key, plug ) :

		if plug is None :
			return

		index = self.indexForPlug( plug )
		if not index.isValid() :
			return

		if key == "spreadsheet:columnLabel" :
			self.headerDataChanged.emit( QtCore.Qt.Horizontal, index.column(), index.column() )
		elif Gaffer.MetadataAlgo.readOnlyAffectedByChange( key ) :
			# Read-only metadata is actually reflected in `flags()`, but there's no signal to emit
			# when they change. Emitting `dataChanged` is enough to kick a redraw off.
			self.dataChanged.emit( index, index )

	def __contextChanged( self, context, key ) :

		if key.startswith( "ui:" ) :
			return

		self.__emitModelReset()

	def __emitModelReset( self ) :

		self.beginResetModel()
		self.endResetModel()

	def __formatValue( self, index, forToolTip = False ) :

		plug = self.valuePlugForIndex( index )

		if isinstance( plug, Gaffer.BoolPlug ) :
			# Dealt with via CheckStateRole
			return None

		try :
			with self.__context :
				return self.formatValue( plug, forToolTip )
		except :
			return None

# Value formatters
# ----------------

def __transformPlugFormatter( plug, forToolTip ) :

	separator = "\n" if forToolTip else "  "
	return separator.join(
		"{label} : {value}".format(
			label = c.getName().title() if forToolTip else c.getName()[0].title(),
			value = _PlugTableModel.formatValue( c, forToolTip )
		)
		for c in plug.children()
	)

_PlugTableModel.registerValueFormatter( Gaffer.TransformPlug, __transformPlugFormatter )

# Plug decorators
# ---------------

def __colorPlugDecorator( plug ) :

	return plug.getValue()

_PlugTableModel.registerDecoration( Gaffer.Color3fPlug, __colorPlugDecorator )
