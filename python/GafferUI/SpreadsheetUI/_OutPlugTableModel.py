##########################################################################
#
#  Copyright (c) 2026, Cinesite VFX Ltd. All rights reserved.
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

from . import _Formatting
from ._PlugTableModel import _PlugTableModel

## A model providing data for the Output TableView in the SpreadsheetUI.
# Data is sourced from the values of a Spreadsheet's `out` plug.
class _OutPlugTableModel( QtCore.QAbstractTableModel ) :

	CellPlugEnabledRole = _PlugTableModel.CellPlugEnabledRole

	def __init__( self, outPlug, rowsPlug, parent = None ) :

		QtCore.QAbstractTableModel.__init__( self, parent )

		self.__outPlug = outPlug
		self.__rowsPlug = rowsPlug

		self.__plugDirtiedConnection = self.__outPlug.node().plugDirtiedSignal().connect( Gaffer.WeakMethod( self.__plugDirtied ), scoped = True )
		self.__columnAddedConnection = self.__outPlug.childAddedSignal().connect( Gaffer.WeakMethod( self.__columnsChanged ), scoped = True )
		self.__columnRemovedConnection = self.__outPlug.childRemovedSignal().connect( Gaffer.WeakMethod( self.__columnsChanged ), scoped = True )

		self.__contextTracker = GafferUI.ContextTracker.acquireForFocus( rowsPlug )
		self.__contextTrackerChangedConnection = self.__contextTracker.changedSignal().connect( Gaffer.WeakMethod( self.__contextTrackerChanged ), scoped = True )
		self.__context = None
		self.__contextTrackerChanged( self.__contextTracker )

	# Methods of our own
	# ------------------

	def rowsPlug( self ) :

		return self.__rowsPlug

	def plugForIndex( self, index ) :

		if not index.isValid() or index.column() >= len( self.__outPlug ) :
			return None

		return self.__outPlug[ index.column() ]

	def valuePlugForIndex( self, index ) :

		return self.plugForIndex( index )

	def indexForPlug( self, plug ) :

		for column, outChild in enumerate( self.__outPlug ) :
			if plug == outChild or outChild.isAncestorOf( plug ) :
				return self.index( 0, column )

		return QtCore.QModelIndex()

	# Overrides for methods inherited from QAbstractTableModel
	# --------------------------------------------------------

	def rowCount( self, parent = QtCore.QModelIndex() ) :

		if parent.isValid() :
			return 0

		return 1

	def columnCount( self, parent = QtCore.QModelIndex() ) :

		if parent.isValid() :
			return 0

		return len( self.__outPlug )

	def headerData( self, section, orientation, role ) :

		# The Output table header is always hidden, so we provide no header data (see _PlugTableView).
		return None

	def flags( self, index ) :

		# Always selectable and enabled, but never editable.
		return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled

	def data( self, index, role ) :

		if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole :

			return self.__formatValue( index )

		elif role == QtCore.Qt.DecorationRole :

			plug = self.valuePlugForIndex( index )
			with self.__context :
				try :
					value = GafferUI.SpreadsheetUI.decoration( plug )
				except :
					return None

			if value is None :
				return None
			elif isinstance( value, imath.Color3f ) :
				displayTransform = GafferUI.Widget._owner( self.parent() ).displayTransform()
				return GafferUI.Widget._qtColor( displayTransform( value ) )
			else :
				IECore.msg( IECore.Msg.Level.Error, "Spreadsheet Decoration", "Unsupported type {}".format( type( value ) ) )
				return None

		elif role == QtCore.Qt.CheckStateRole :

			plug = self.valuePlugForIndex( index )
			if not isinstance( plug, Gaffer.BoolPlug ) :
				return None

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
			if isinstance( plug, ( Gaffer.NameValuePlug, Gaffer.OptionalValuePlug, Gaffer.TweakPlug ) ) :
				with self.__context :
					try :
						enabled = plug["enabled"].getValue()
					except :
						return None

			return enabled

		return None

	def presentsCheckstate( self, index ) :

		return isinstance( self.valuePlugForIndex( index ), Gaffer.BoolPlug )

	# Methods of our own
	# ------------------

	def __plugDirtied( self, plug ) :

		index = self.indexForPlug( plug )
		if index.isValid() :
			self.dataChanged.emit( index, index )

	def __columnsChanged( self, outPlug, childPlug ) :

		self.__emitModelReset()

	def __contextTrackerChanged( self, contextTracker ) :

		context = self.__contextTracker.context( self.rowsPlug() )
		if self.__context is None or self.__context.hash() != context.hash() :
			self.__context = context
			self.__emitModelReset()

	def __emitModelReset( self ) :

		self.beginResetModel()
		self.endResetModel()

	def __formatValue( self, index, forToolTip = False ) :

		plug = self.valuePlugForIndex( index )

		if not forToolTip and isinstance( plug, Gaffer.BoolPlug ) :
			# Dealt with via CheckStateRole
			return None

		try :
			with self.__context :
				return _Formatting.formatValue( plug, forToolTip )
		except :
			return None
