##########################################################################
#  
#  Copyright (c) 2011, John Haddon. All rights reserved.
#  Copyright (c) 2011-2012, Image Engine Design Inc. All rights reserved.
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

from __future__ import with_statement

import os
import time
import warnings

import IECore

import Gaffer
import GafferUI

QtCore = GafferUI._qtImport( "QtCore" )
QtGui = GafferUI._qtImport( "QtGui" )

## The PathListingWidget displays the contents of a Path, updating the Path to represent the
# current directory as the user navigates around. It supports both a list and a tree view, 
# allows customisable column listings, and supports both single and multiple selection.
class PathListingWidget( GafferUI.Widget ) :

	## This simple class defines the content of a column.
	class Column( object ) :
	
		__slots__ = ( "infoField", "label", "displayFunction", "sortFunction" )
		
		def __init__( self, infoField, label, displayFunction=str, sortFunction=str ) :
		
			self.infoField = infoField
			self.label = label
			self.displayFunction = displayFunction
			self.sortFunction = sortFunction
		
	## A collection of handy column definitions for FileSystemPaths
	defaultNameColumn = Column( infoField = "name", label = "Name" )
	defaultFileSystemOwnerColumn = Column( infoField = "fileSystem:owner", label = "Owner" )
	defaultFileSystemModificationTimeColumn = Column( infoField = "fileSystem:modificationTime", label = "Modified", displayFunction = time.ctime )
	defaultFileSystemIconColumn = Column(
		infoField = "fullName",
		label = "Type",
		displayFunction = lambda x, provider = QtGui.QFileIconProvider() : provider.icon( QtCore.QFileInfo( x ) ),
		sortFunction = lambda x : os.path.splitext( x )[-1],
	)
		
	defaultFileSystemColumns = (
		defaultNameColumn,
		defaultFileSystemOwnerColumn,
		defaultFileSystemModificationTimeColumn,
		defaultFileSystemIconColumn,
	)
	
	## A collection of handy column definitions for IndexedIOPaths
	defaultIndexedIOEntryTypeColumn = Column( infoField = "indexedIO:entryType", label = "Entry Type" )
	defaultIndexedIODataTypeColumn = Column( infoField = "indexedIO:dataType", label = "Data Type" )
	defaultIndexedIOArrayLengthColumn = Column( infoField = "indexedIO:arrayLength", label = "Array Length" )

	defaultIndexedIOColumns = (
		defaultNameColumn,
		defaultIndexedIOEntryTypeColumn,
		defaultIndexedIODataTypeColumn,
		defaultIndexedIOArrayLengthColumn,
	)

	DisplayMode = IECore.Enum.create( "List", "Tree" )

	def __init__(
		self,
		path,
		columns = defaultFileSystemColumns,
		allowMultipleSelection = False,
		displayMode = DisplayMode.List,
		**kw
	) :
	
		GafferUI.Widget.__init__( self, _TreeView(), **kw )
				
		self._qtWidget().setAlternatingRowColors( True )
		self._qtWidget().setEditTriggers( QtGui.QTreeView.NoEditTriggers )
		self._qtWidget().activated.connect( Gaffer.WeakMethod( self.__activated ) )
		self._qtWidget().header().setMovable( False )
		self._qtWidget().setSortingEnabled( True )
		self._qtWidget().header().setSortIndicator( 0, QtCore.Qt.AscendingOrder )
		
		self._qtWidget().expanded.connect( Gaffer.WeakMethod( self.__expanded ) )
		self._qtWidget().collapsed.connect( Gaffer.WeakMethod( self.__collapsed ) )
		self.__expandedPaths = set()
		
		self.__sortProxyModel = QtGui.QSortFilterProxyModel()
		self.__sortProxyModel.setSortRole( QtCore.Qt.UserRole )
		
		self._qtWidget().setModel( self.__sortProxyModel )
		
		self.__selectionModel = QtGui.QItemSelectionModel( self.__sortProxyModel )
		self._qtWidget().setSelectionModel( self.__selectionModel )
		self._qtWidget().selectionModel().selectionChanged.connect( Gaffer.WeakMethod( self.__selectionChanged ) )
		if allowMultipleSelection :
			self._qtWidget().setSelectionMode( QtGui.QAbstractItemView.ExtendedSelection )			

		self.__columns = columns
		self.__displayMode = displayMode
		
		self.__path = None
		self.setPath( path )
		
		self.__pathSelectedSignal = GafferUI.WidgetSignal()
		self.__selectionChangedSignal = GafferUI.WidgetSignal()
		self.__displayModeChangedSignal = GafferUI.WidgetSignal()
		self.__expansionChangedSignal = GafferUI.WidgetSignal()
	
	def setPath( self, path ) :
	
		if path is self.__path :
			return
		
		self.__path = path
		self.__pathChangedConnection = self.__path.pathChangedSignal().connect( Gaffer.WeakMethod( self.__pathChanged ) )
		self.__currentDir = None
		self.__currentPath = ""
		self.__expandedPaths.clear()
		self.__update()

	def getPath( self ) :
	
		return self.__path
	
	def scrollToPath( self, path ) :
	
		index = self.__indexForPath( path )
		if index.isValid() :
			self._qtWidget().scrollTo( index, self._qtWidget().EnsureVisible )	
	
	## \deprecated Use setPathExpanded() instead.
	def setPathCollapsed( self, path, collapsed ) :
	
		warnings.warn( "PathListingWidget.setPathCollapsed() is deprecated, use PathListingWidget.setPathExpanded() instead.", DeprecationWarning, 2 )		
		self.setPathExpanded( self, path, not collapsed )
		
	## \deprecated Use getPathExpanded() instead.
	def getPathCollapsed( self, path ) :
	
		warnings.warn( "PathListingWidget.getPathCollapsed() is deprecated, use PathListingWidget.getPathExpanded() instead.", DeprecationWarning, 2 )		
		return not self.getPathExpaned( self, path )
		
	def setPathExpanded( self, path, expanded ) :
	
		index = self.__indexForPath( path )
		if index.isValid() :
			self._qtWidget().setExpanded( index, expanded )
				
	def getPathExpanded( self, path ) :
	
		index = self.__indexForPath( path )
		if index.isValid() :
			return self._qtWidget().isExpanded( index )
		
		return False
		
	def setExpandedPaths( self, paths ) :
	
		self._qtWidget().collapseAll()
		for path in paths :
			self.setPathExpanded( path, True )
		self.__expandedPaths = set( paths )
		
	def getExpandedPaths( self ) :
	
		return self.__expandedPaths
		
	def expansionChangedSignal( self ) :
	
		return self.__expansionChangedSignal
		
	def getDisplayMode( self ) :
	
		return self.__displayMode
		
	def setDisplayMode( self, displayMode ) :
	
		if displayMode == self.__displayMode :
			return
			
		self.__displayMode = displayMode
		self.__currentDir = None # force update to do something
		self.__update()
		self.__displayModeChangedSignal( self )
		
	def displayModeChangedSignal( self ) :
	
		return self.__displayModeChangedSignal
	
	## Returns a list of all currently selected paths. Note that a list is returned
	# even when in single selection mode.
	def getSelectedPaths( self ) :
	
		result = []
		selectedRows = self._qtWidget().selectionModel().selectedRows()
		selectedSourceRows = [ self.__sortProxyModel.mapToSource( x ) for x in selectedRows ]
		return [ x.internalPointer().path() for x in selectedSourceRows ]
	
	## Sets the currently selected paths. Paths which are not currently being displayed
	# will be discarded, such that subsequent calls to getSelectedPaths will not include them.
	def setSelectedPaths( self, pathOrPaths, scrollToFirst=True, expandNonLeaf=True ) :
	
		paths = pathOrPaths
		if isinstance( pathOrPaths, Gaffer.Path ) :
			paths = [ pathOrPaths ]

		if self._qtWidget().selectionMode() != QtGui.QAbstractItemView.ExtendedSelection :
			assert( len( paths ) <= 1 )
				
		selectionModel = self._qtWidget().selectionModel()
		selectionModel.clear()
		
		for path in paths :
		
			indexToSelect = self.__indexForPath( path )
			if indexToSelect.isValid() :
				selectionModel.select( indexToSelect, selectionModel.Select | selectionModel.Rows )
				if scrollToFirst :
					self._qtWidget().scrollTo( indexToSelect, self._qtWidget().EnsureVisible )
					scrollToFirst = False
				if expandNonLeaf and not path.isLeaf() :
					self._qtWidget().setExpanded( indexToSelect, True )
					
	## \deprecated Use getSelectedPaths() instead.
	# \todo Remove me
	def selectedPaths( self ) :

		warnings.warn( "PathListingWidget.selectedPaths() is deprecated, use PathListingWidget.getSelectdPaths() instead.", DeprecationWarning, 2 )		
	
		return self.getSelectedPaths()
	
	## This signal is emitted when the selected items change. Use getSelectedPaths()
	# to get a list of those items.
	def selectionChangedSignal( self ) :
	
		return self.__selectionChangedSignal
	
	## This signal is emitted when the user double clicks on a leaf path.
	def pathSelectedSignal( self ) :
	
		return self.__pathSelectedSignal
			
	def __update( self ) :
				
		# update the listing if necessary. when the path itself changes, we only
		# want to update if the directory being viewed has changed. if the path
		# hasn't changed at all then we assume that the filter has changed and
		# we therefore have to update the listing anyway.
		# \todo Add an argument to Path.pathChangedSignal() to specify whether it
		# is the path or the filtering that has changed, and remove self.__currentPath
				
		dirPath = self.__dirPath()
		if self.__currentDir!=dirPath or str( self.__path )==self.__currentPath :

			selectedPaths = self.getSelectedPaths()
						
			self.__sortProxyModel.setSourceModel(
				_PathModel(
					dirPath,
					self.__columns,
					recurse = self.__displayMode != self.DisplayMode.List,
				)
			)

			self.setSelectedPaths( selectedPaths, scrollToFirst = False )
	
			self.__currentDir = dirPath
		
		self.__currentPath = str( self.__path )
									
	def __dirPath( self ) :
	
		p = self.__path.copy()
		if p.isLeaf() :
			# if it's a leaf then take the parent
			del p[-1]
		else :
			# it's not a leaf.
			if not p.isValid() :
				# it's not valid. if we can make it
				# valid by trimming the last element
				# then do that
				pp = p.copy()
				del pp[-1]
				if pp.isValid() :
					p = pp
			else :
				# it's valid and not a leaf, and
				# that's what we want.
				pass
						
		return p

	def __activated( self, modelIndex ) :
				
		activatedPath = self.__pathForIndex( modelIndex )
		
		if self.__displayMode == self.DisplayMode.List :
			self.__path[:] = activatedPath[:]
				
		if activatedPath.isLeaf() :
			self.pathSelectedSignal()( self )
			return True
			
		return False
		
	def __selectionChanged( self, selected, deselected ) :
		 				
		self.selectionChangedSignal()( self )
		return True
			
	def __pathChanged( self, path ) :
		
		self.__update()
		
	def __indexForPath( self, path ) :
	
		indexToSelect = self.__sortProxyModel.sourceModel().indexForPath( path )
		indexToSelect = self.__sortProxyModel.mapFromSource( indexToSelect )
		
		return indexToSelect
		
	def __pathForIndex( self, modelIndex ) :
	
		return self.__sortProxyModel.mapToSource( modelIndex ).internalPointer().path()
		
	def __expanded( self, modelIndex ) :
	
		self.__expandedPaths.add( self.__pathForIndex( modelIndex ) )
		self.__expansionChangedSignal( self )

	def __collapsed( self, modelIndex ) :
	
		self.__expandedPaths.remove( self.__pathForIndex( modelIndex ) )
		self.__expansionChangedSignal( self )
		
# Private implementation - a QTreeView with some specific size behaviour
class _TreeView( QtGui.QTreeView ) :

	def __init__( self ) :
	
		QtGui.QTreeView.__init__( self )
		
		self.setHorizontalScrollBarPolicy( QtCore.Qt.ScrollBarAlwaysOff )
				
		self.header().geometriesChanged.connect( self.updateGeometry )
		self.header().sectionResized.connect( self.__sectionResized )
		
		self.collapsed.connect( self.__recalculateColumnSizes )
		self.expanded.connect( self.__recalculateColumnSizes )
	
		self.__recalculatingColumnWidths = False
		# the ideal size for each column. we cache these because they're slow to compute
		self.__idealColumnWidths = [] 
		# offsets to the ideal sizes made by the user
		self.__columnWidthAdjustments = [] 
	
	def setModel( self, model ) :
	
		QtGui.QTreeView.setModel( self, model )
		
		model.modelReset.connect( self.__recalculateColumnSizes )

		self.__recalculateColumnSizes()
	
	def sizeHint( self ) :
	
		result = QtGui.QTreeView.sizeHint( self )
		
		margins = self.contentsMargins()
		result.setWidth( self.header().length() + margins.left() + margins.right() )

		result.setHeight( max( result.width() * .5, result.height() ) )
		
		return result
		
	def __recalculateColumnSizes( self, *unusedArgs ) :
		
		self.__recalculatingColumnWidths = True
	
		header = self.header()
		for i in range( 0, header.count() - 1 ) : # leave the last section alone, as it's expandable

			idealWidth = max( header.sectionSizeHint( i ), self.sizeHintForColumn( i ) )
			if i >= len( self.__idealColumnWidths ) :
				self.__idealColumnWidths.append( idealWidth )
				self.__columnWidthAdjustments.append( 0 )
			else :
				self.__idealColumnWidths[i] = idealWidth
						
			header.resizeSection( i, idealWidth + self.__columnWidthAdjustments[i] )

		self.__recalculatingColumnWidths = False

	def __sectionResized( self, index, oldWidth, newWidth ) :
		
		if self.__recalculatingColumnWidths :
			# we're only interested in resizing being done by the user
			return
		
		# store the difference between the ideal size and what the user would prefer, so
		# we can apply it again in __recalculateColumnSizes
		if len( self.__idealColumnWidths ) > index :
			self.__columnWidthAdjustments[index] = newWidth - self.__idealColumnWidths[index]
		
class _PathItem() :

	def __init__( self, path, columns, parent = None, row = 0 ) :
	
		self.__path = path
		self.__childItems = None
		# yes, this does make reference cycles, but just storing a weak reference to parent
		# seems to allow the parent to die in some cases. we'll just have to let the
		# garbage collector tidy things up.
		self.__parent = parent
		self.__columns = columns
		self.__row = row
		
		self.__displayData = []
		self.__decorationData = []
		self.__sortData = []
				
	def path( self ) :
	
		return self.__path
	
	def parent( self ) :
		
		return self.__parent
			
	def row( self ) :
	
		return self.__row
		
	def data( self, columnIndex, role ) :
	
		# populate all data the first time we're asked for any element, to avoid wasted calls
		# to info(). chances are if we've been asked for one piece we're gonna be asked for the
		# others really soon.
		if not self.__displayData :
			info = self.__path.info()
			for column in self.__columns :
				if info is not None and column.infoField in info :
					value = column.displayFunction( info[column.infoField] )		
					if isinstance( value, GafferUI.Image ) :
						value = value._qtPixmap()
					if isinstance( value, basestring ) :
						self.__displayData.append( GafferUI._Variant.toVariant( value ) )
						self.__decorationData.append( GafferUI._Variant.toVariant( None ) )
					else :
						self.__displayData.append( GafferUI._Variant.toVariant( None ) )
						self.__decorationData.append( GafferUI._Variant.toVariant( value ) )
					self.__sortData.append( GafferUI._Variant.toVariant( column.sortFunction( info[column.infoField] ) ) )
				else :	
					self.__displayData.append( GafferUI._Variant.toVariant( None ) )
					self.__decorationData.append( GafferUI._Variant.toVariant( None ) )
					self.__sortData.append( GafferUI._Variant.toVariant( None ) )

		if role == QtCore.Qt.DisplayRole :
			return self.__displayData[columnIndex]
		elif role == QtCore.Qt.DecorationRole :
			return self.__decorationData[columnIndex]
		elif role == QtCore.Qt.UserRole :
			return self.__sortData[columnIndex]
					
		return GafferUI._Variant.toVariant( None )
	
	def childItems( self ) :
	
		if self.__childItems is None :
			self.__childItems = [ _PathItem( p, self.__columns, self, i ) for i, p in enumerate( self.__path.children() ) ]
	
		return self.__childItems

class _PathModel( QtCore.QAbstractItemModel ) :

	def __init__( self, path, columns, recurse=True, parent = None ) :
	
		QtCore.QAbstractItemModel.__init__( self, parent )
		
		self.__rootItem = _PathItem( path.copy(), columns )
		self.__columns = columns
		self.__recurse = recurse
		
	def columnCount( self, parentIndex ) :
		
		return len( self.__columns )
		
	def rowCount( self, parentIndex ) :
	
		parentItem = parentIndex.internalPointer() if parentIndex.isValid() else self.__rootItem
		if not self.__recurse and parentItem is not self.__rootItem :
			return 0
		else :
			return len( parentItem.childItems() )
			
	def index( self, row, column, parentIndex ) :
	
		parentItem = parentIndex.internalPointer() if parentIndex.isValid() else self.__rootItem
		
		childItems = parentItem.childItems()
		if row < len( childItems ) :
			return self.createIndex( row, column, childItems[row] )
		else :
			return QtCore.QModelIndex()
	
	def parent( self, index ) :
	
		if not index.isValid() :
			return QtCore.QModelIndex()
			
		parentItem = index.internalPointer().parent()
		if parentItem is None or parentItem is self.__rootItem :
			return QtCore.QModelIndex()
			
		return self.createIndex( parentItem.row(), 0, parentItem )
	
	def headerData( self, section, orientation, role ) :
	
		if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole :
			return GafferUI._Variant.toVariant( self.__columns[section].label )
			
		return GafferUI._Variant.toVariant( None )
	
	def data( self, index, role ) :
	
		if not index.isValid() :
			return GafferUI._Variant.toVariant( None )
		
		item = index.internalPointer()
		return item.data( index.column(), role )
		
	def indexForPath( self, path ) :
		
		rootPath = self.__rootItem.path()
		if len( path ) <= len( rootPath ) or path[:len(rootPath)] != rootPath[:] :
			return QtCore.QModelIndex()
				
		index = QtCore.QModelIndex()
		item = self.__rootItem
		for i in range( len( rootPath ), len( path ) ) :
			foundNextItem = False
			for j, childItem in enumerate( item.childItems() ) :
				if childItem.path()[i] == path[i] :
					item = childItem
					index = self.index( j, 0, index )
					foundNextItem = True
					break
			if not foundNextItem :
				break
				
		if foundNextItem :
			return index
			
		return QtCore.QModelIndex()
