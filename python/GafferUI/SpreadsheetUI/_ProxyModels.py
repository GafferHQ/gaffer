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

from Qt import QtCore

from ._PlugTableModel import _PlugTableModel

class __PlugTableProxyModel( QtCore.QAbstractProxyModel ) :

	def __init__( self, startRow = 0, startColumn = 0, rowCount = None, columnCount = 0, parent = None ) :

		QtCore.QAbstractProxyModel.__init__( self, parent = parent )

		self.__startRow = startRow
		self.__startColumn = startColumn
		self.__rowCount = rowCount
		self.__columnCount = columnCount

	def index( self, row, column, parent = QtCore.QModelIndex() ) :

		if parent.isValid() :
			return QtCore.QModelIndex()

		return self.createIndex( row, column )

	def parent( self, index ) :

		return QtCore.QModelIndex()

	def setSourceModel( self, model ) :

		assert( isinstance( model, _PlugTableModel ) )

		# _PlugTableModel only emits modelReset and [header]DataChanged signals (for now)
		# so we can avoid the headache of remapping the plethora of row/column signals.

		oldModel = self.sourceModel()
		if oldModel :
			oldModel.disconnect( self )

		if model :
			model.dataChanged.connect( self.__dataChanged )
			model.headerDataChanged.connect( self.__headerDataChanged )
			model.modelReset.connect( self.modelReset )

		self.beginResetModel()
		QtCore.QAbstractProxyModel.setSourceModel( self, model )
		self.endResetModel()

	def columnCount( self, parent = QtCore.QModelIndex() ) :

		if parent.isValid() :
			return 0

		if self.__columnCount :
			return self.__columnCount
		else :
			return self.sourceModel().columnCount() - self.__startColumn

	def rowCount( self, parent = QtCore.QModelIndex() ) :

		if parent.isValid() :
			return 0

		if self.__rowCount :
			return self.__rowCount
		else :
			return self.sourceModel().rowCount() - self.__startRow

	def mapFromSource( self, sourceIndex )  :

		if not sourceIndex.isValid() :
			return QtCore.QModelIndex()

		row = sourceIndex.row() - self.__startRow
		column = sourceIndex.column() - self.__startColumn

		if row < 0 or row >= self.rowCount() :
			return QtCore.QModelIndex()

		if column < 0 or column >= self.columnCount() :
			return QtCore.QModelIndex()

		return self.index( row, column )

	def mapToSource( self, proxyIndex ) :

		if not proxyIndex.isValid():
			return QtCore.QModelIndex()

		row = proxyIndex.row() + self.__startRow
		column = proxyIndex.column() + self.__startColumn
		return self.sourceModel().index( row, column )

	def rowsPlug( self ) :

		return self.sourceModel().rowsPlug()

	def plugForIndex( self, index ) :

		return self.sourceModel().plugForIndex( self.mapToSource( index ) )

	def valuePlugForIndex( self, index ) :

		return self.sourceModel().valuePlugForIndex( self.mapToSource( index ) )

	def indexForPlug( self, plug ) :

		return self.mapFromSource( self.sourceModel().indexForPlug( plug ) )

	def __dataChanged( self, topLeft, bottomRight, roles ) :

		# Early out if the changed range doesn't intersect the remapped model

		if bottomRight.row() < self.__startRow or bottomRight.column() < self.__startColumn :
			return

		if topLeft.row() - self.__startRow >= self.rowCount() \
		   or topLeft.column() - self.__startColumn >= self.columnCount() :
			return

		# Clamp to presented range

		proxyTopLeft = self.mapFromSource( topLeft )
		if not proxyTopLeft.isValid() :
			proxyTopLeft = self.index( 0, 0 )

		proxyBottomRight = self.mapFromSource( bottomRight )
		if not proxyBottomRight.isValid() :
			proxyBottomRight = self.index( self.rowCount() - 1, self.columnCount() - 1 )

		self.dataChanged.emit( proxyTopLeft, proxyBottomRight, roles )

	def __headerDataChanged( self, orientation, first, last ) :

		if orientation == QtCore.Qt.Vertical :
			limit = self.rowCount() - 1
			offset = self.__startRow
		else :
			limit = self.columnCount() - 1
			offset = self.__startColumn

		# Don't propagate if the changed range is outside of our remapping
		if first - offset > limit or last < offset :
			return

		first = max( first - offset, 0 )
		last = min( last - offset, limit )

		self.headerDataChanged.emit( orientation, first, last )

class RowNamesProxyModel( __PlugTableProxyModel ) :

	def __init__( self, parent = None ) :

		super( RowNamesProxyModel, self ).__init__( startRow = 1, columnCount = 2, parent = parent )

class DefaultsProxyModel( __PlugTableProxyModel ) :

	def __init__( self, parent = None ) :

		super( DefaultsProxyModel, self ).__init__( startColumn = 2, rowCount = 1, parent = parent )

class CellsProxyModel( __PlugTableProxyModel ) :

	def __init__( self, parent = None ) :

		super( CellsProxyModel, self ).__init__( startRow = 1, startColumn = 2, parent = parent )
