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

from _PlugTableModel import _PlugTableModel

class __PlugTableProxyModel( QtCore.QAbstractProxyModel ) :

	def index( self, row, column, parent = QtCore.QModelIndex() ) :

		if parent.isValid() :
			return QtCore.QModelIndex()

		return self.createIndex( row, column )

	def parent( self, index ) :

		return QtCore.QModelIndex()

	def setSourceModel( self, model ) :

		assert( isinstance( model, _PlugTableModel ) )

		oldModel = self.sourceModel()

		# We don't encounter column changes so we don't need to bother with those signals here.
		for signal in (
			"dataChanged", "modelReset",
			"rowsAboutToBeInserted", "rowsInserted", "rowsAboutToBeRemoved", "rowsRemoved", "rowsAboutToBeMoved", "rowsMoved",
			"columnsAboutToBeInserted", "columnsInserted", "columnsAboutToBeRemoved", "columnsRemoved", "columnsAboutToBeMoved", "columnsMoved"
		) :
			slot = getattr( self, signal )
			if oldModel :
				getattr( oldModel, signal ).disconnect( slot )
			if model :
				getattr( model, signal ).connect( slot )

		self.beginResetModel()
		QtCore.QAbstractProxyModel.setSourceModel( self, model )
		self.endResetModel()

	def rowsPlug( self ) :

		return self.sourceModel().rowsPlug()

	def plugForIndex( self, index ) :

		return self.sourceModel().plugForIndex( self.mapToSource( index ) )

	def valuePlugForIndex( self, index ) :

		return self.sourceModel().valuePlugForIndex( self.mapToSource( index ) )

	def indexForPlug( self, plug ) :

		return self.mapFromSource( self.sourceModel().indexForPlug( plug ) )

class RowNamesProxyModel( __PlugTableProxyModel ) :

	def columnCount( self, parent ) :

		if parent.isValid() :
			return 0

		return 2

	def rowCount( self, parent ) :

		if parent.isValid() :
			return 0

		return self.sourceModel().rowCount() - 1

	def mapFromSource( self, sourceIndex )  :

		if not sourceIndex.isValid() or sourceIndex.row() < 1 :
			return QtCore.QModelIndex()

		return self.index( sourceIndex.row() - 1, sourceIndex.column() )

	def mapToSource( self, proxyIndex ) :

		if not proxyIndex.isValid() or proxyIndex.row() < 0 :
			return QtCore.QModelIndex()

		return self.sourceModel().index( proxyIndex.row() + 1, proxyIndex.column() )

class DefaultsProxyModel( __PlugTableProxyModel ) :

	def columnCount( self, parent ) :

		if parent.isValid() :
			return 0

		return self.sourceModel().columnCount() - 2

	def rowCount( self, parent ) :

		if parent.isValid() :
			return 0

		return 1

	def mapFromSource( self, sourceIndex )  :

		if not sourceIndex.isValid() or sourceIndex.row() != 0 :
			return QtCore.QModelIndex()

		return self.index( 0, sourceIndex.column() - 2 )

	def mapToSource( self, proxyIndex ) :

		if not proxyIndex.isValid() or proxyIndex.row() != 0 :
			return QtCore.QModelIndex()

		return self.sourceModel().index( 0, proxyIndex.column() + 2 )

class CellsProxyModel( __PlugTableProxyModel ) :

	def columnCount( self, parent ) :

		if parent.isValid() :
			return 0

		return self.sourceModel().columnCount() - 2

	def rowCount( self, parent ) :

		if parent.isValid() :
			return 0

		return self.sourceModel().rowCount() - 1

	def mapFromSource( self, sourceIndex )  :

		if not sourceIndex.isValid() or sourceIndex.row() < 1 or sourceIndex.column() < 2 :
			return QtCore.QModelIndex()

		return self.index( sourceIndex.row() - 1, sourceIndex.column() - 2 )

	def mapToSource( self, proxyIndex ) :

		if not proxyIndex.isValid() or proxyIndex.row() < 0 or proxyIndex.column() < 0 :
			return QtCore.QModelIndex()

		return self.sourceModel().index( proxyIndex.row() + 1, proxyIndex.column() + 2 )
