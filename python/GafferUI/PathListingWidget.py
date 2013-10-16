##########################################################################
#  
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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
		self._qtWidget().setUniformRowHeights( True )
		self._qtWidget().setEditTriggers( QtGui.QTreeView.NoEditTriggers )
		self._qtWidget().activated.connect( Gaffer.WeakMethod( self.__activated ) )
		self._qtWidget().header().setMovable( False )
		self._qtWidget().setSortingEnabled( True )
		self._qtWidget().header().setSortIndicator( 0, QtCore.Qt.AscendingOrder )
		
		self._qtWidget().expansionChanged.connect( Gaffer.WeakMethod( self.__expansionChanged ) )
				
		self.__sortProxyModel = QtGui.QSortFilterProxyModel()
		self.__sortProxyModel.setSortRole( QtCore.Qt.UserRole )
		
		self._qtWidget().setModel( self.__sortProxyModel )
		
		self.__selectionModel = QtGui.QItemSelectionModel( self.__sortProxyModel )
		self._qtWidget().setSelectionModel( self.__selectionModel )
		self.__selectionChangedSlot = Gaffer.WeakMethod( self.__selectionChanged )
		self._qtWidget().selectionModel().selectionChanged.connect( self.__selectionChangedSlot )
		if allowMultipleSelection :
			self._qtWidget().setSelectionMode( QtGui.QAbstractItemView.ExtendedSelection )			

		self.__columns = columns
		self.__displayMode = displayMode
				
		self.__pathSelectedSignal = GafferUI.WidgetSignal()
		self.__selectionChangedSignal = GafferUI.WidgetSignal()
		self.__displayModeChangedSignal = GafferUI.WidgetSignal()
		self.__expansionChangedSignal = GafferUI.WidgetSignal()
		
		# members for implementing drag and drop
		self.__emittingButtonPress = False
		self.__borrowedButtonPress = None
		self.__buttonPressConnection = self.buttonPressSignal().connect( Gaffer.WeakMethod( self.__buttonPress ) )
		self.__buttonReleaseConnection = self.buttonReleaseSignal().connect( Gaffer.WeakMethod( self.__buttonRelease ) )
		self.__mouseMoveConnection = self.mouseMoveSignal().connect( Gaffer.WeakMethod( self.__mouseMove ) )
		self.__dragBeginConnection = self.dragBeginSignal().connect( Gaffer.WeakMethod( self.__dragBegin ) )
		self.__dragEndConnection = self.dragEndSignal().connect( Gaffer.WeakMethod( self.__dragEnd ) )
		self.__dragPointer = "paths.png"
		
		self.__path = None
		self.setPath( path )

	def setPath( self, path ) :
	
		if path is self.__path :
			return
		
		self.__path = path
		self.__pathChangedConnection = self.__path.pathChangedSignal().connect( Gaffer.WeakMethod( self.__pathChanged ) )
		self.__pathChangedUpdatePending = False
		self.__currentDir = None
		self.__currentPath = ""
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
	
		indices = []
		for path in paths :
			index = self.__indexForPath( path )
			if index.isValid() :
				indices.append( index )
		
		self._qtWidget().setExpandedIndices( indices )
		
	def getExpandedPaths( self ) :
	
		return [ self.__pathForIndex( i ) for i in self._qtWidget().getExpandedIndices() ]
		
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
	
	def setColumns( self, columns ) :
	
		if columns == self.__columns :
			return
		
		self.__columns = columns
		self.__currentDir = None # force update to do something
		self.__update()
		
	def getColumns( self ) :
		
		return self.__columns
	
	## Returns a list of all currently selected paths. Note that a list is returned
	# even when in single selection mode.
	def getSelectedPaths( self ) :
	
		selectedRows = self._qtWidget().selectionModel().selectedRows()
		return [ self.__pathForIndex( index ) for index in selectedRows ]
	
	## Sets the currently selected paths. Paths which are not currently being displayed
	# will be discarded, such that subsequent calls to getSelectedPaths will not include them.
	def setSelectedPaths( self, pathOrPaths, scrollToFirst=True, expandNonLeaf=True ) :
	
		paths = pathOrPaths
		if isinstance( pathOrPaths, Gaffer.Path ) :
			paths = [ pathOrPaths ]

		if self._qtWidget().selectionMode() != QtGui.QAbstractItemView.ExtendedSelection :
			assert( len( paths ) <= 1 )
				
		selectionModel = self._qtWidget().selectionModel()
		selectionModel.selectionChanged.disconnect( self.__selectionChangedSlot )

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

		selectionModel.selectionChanged.connect( self.__selectionChangedSlot )
		
		self.selectionChangedSignal()( self )		
					
	## \deprecated Use getSelectedPaths() instead.
	# \todo Remove me
	def selectedPaths( self ) :

		warnings.warn( "PathListingWidget.selectedPaths() is deprecated, use PathListingWidget.getSelectedPaths() instead.", DeprecationWarning, 2 )		
	
		return self.getSelectedPaths()
	
	## This signal is emitted when the selected items change. Use getSelectedPaths()
	# to get a list of those items.
	def selectionChangedSignal( self ) :
	
		return self.__selectionChangedSignal
	
	## This signal is emitted when the user double clicks on a leaf path.
	def pathSelectedSignal( self ) :
	
		return self.__pathSelectedSignal
	
	def setDragPointer( self, dragPointer ) :
	
		self.__dragPointer = dragPointer
		
	def getDragPointer( self ) :
	
		return self.__dragPointer
		
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
			expandedPaths = None
			if str( self.__path ) == self.__currentPath :
				# the path location itself hasn't changed so we are assuming that just the filter has.
				# if we're in the tree view mode, the user would probably be very happy
				# if we didn't forget what was expanded.
				if self.getDisplayMode() == self.DisplayMode.Tree :
					expandedPaths = self.getExpandedPaths()

			self.__sortProxyModel.setSourceModel(
				_PathModel(
					dirPath,
					self.__columns,
					recurse = self.__displayMode != self.DisplayMode.List,
				)
			)

			if expandedPaths is not None :
				self.setExpandedPaths( expandedPaths )

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
				if len( p ) :
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
		
		if not self.__pathChangedUpdatePending :
			self.__pathChangedUpdatePending = True
			GafferUI.EventLoop.addIdleCallback( self.__pathChangedUpdate )
			
	def __pathChangedUpdate( self ) :
	
		self.__pathChangedUpdatePending = False
		self.__update()
		
		return False # cause this idle callback to run once only
		
	def __indexForPath( self, path ) :
	
		indexToSelect = self.__sortProxyModel.sourceModel().indexForPath( path )
		indexToSelect = self.__sortProxyModel.mapFromSource( indexToSelect )
		
		return indexToSelect
		
	def __pathForIndex( self, modelIndex ) :
	
		return self.__sortProxyModel.mapToSource( modelIndex ).internalPointer().path()
		
	def __expansionChanged( self ) :
	
		self.__expansionChangedSignal( self )
	
	def __buttonPress( self, widget, event ) :
			
		if self.__emittingButtonPress :
			return False
	
		self.__borrowedButtonPress = None
		if event.buttons == event.Buttons.Left and event.modifiers == event.Modifiers.None :
			
			# We want to implement drag and drop of the selected items, which means borrowing
			# mouse press events that the QTreeView needs to perform selection and expansion.
			# This makes things a little tricky. There are are two cases :
			#
			#  1) There is an existing selection, and it's been clicked on. We borrow the event
			#     so we can get a dragBeginSignal(), and to prevent the QTreeView reducing a current
			#     multi-selection down to the single clicked item. If a drag doesn't materialise we'll
			#     re-emit the event straight to the QTreeView in __buttonRelease so the QTreeView can
			#     do its thing.
			#
			#  2) There is no existing selection. We pass the event to the QTreeView
			#     to see if it will select something which we can subsequently drag.
			#
			# This is further complicated by the fact that the button presses we simulate for Qt
			# will end up back in this function, so we have to be careful to ignore those.
			
			index = self._qtWidget().indexAt( QtCore.QPoint( event.line.p0.x, event.line.p0.y ) )
			if self._qtWidget().selectionModel().isSelected( index ) :
				# case 1 : existing selection. 
				self.__borrowedButtonPress = event
				return True
			else :
				# case 2 : no existing selection.
				# allow qt to update the selection first.
				self.__emitButtonPress( event ) 
				# we must always return True to prevent the event getting passed
				# to the QTreeView again, and so we get a chance to start a drag.
				return True
				
		return False

	def __buttonRelease( self, widget, event ) :
				
		if self.__borrowedButtonPress is not None :
			self.__emitButtonPress( self.__borrowedButtonPress )
			self.__borrowedButtonPress = None
			
		return False
	
	def __mouseMove( self, widget, event ) :
	
		if event.buttons :
			# take the event so that the underlying QTreeView doesn't
			# try to do drag-selection, which would ruin our own upcoming drag.
			return True
		
		return False
		
	def __dragBegin( self, widget, event ) :

		self.__borrowedButtonPress = None
		selectedPaths = self.getSelectedPaths()
		if len( selectedPaths ) :	
			GafferUI.Pointer.setFromFile( self.__dragPointer )	
			return IECore.StringVectorData(
				[ str( p ) for p in selectedPaths ],
			)
		
		return None
		
	def __dragEnd( self, widget, event ) :
	
		GafferUI.Pointer.set( None )
		
	def __emitButtonPress( self, event ) :
	
		qEvent = QtGui.QMouseEvent(
			QtCore.QEvent.MouseButtonPress,
			QtCore.QPoint( event.line.p0.x, event.line.p0.y ),
			QtCore.Qt.LeftButton,
			QtCore.Qt.LeftButton,
			QtCore.Qt.NoModifier
		)
	
		try :
			self.__emittingButtonPress = True
			# really i think we should be using QApplication::sendEvent()
			# here, but it doesn't seem to be working. it works with the qObject
			# in the Widget event filter, but for some reason that differs from
			# Widget._owner( qObject )._qtWidget() which is what we have here.
			self._qtWidget().mousePressEvent( qEvent )
		finally :
			self.__emittingButtonPress = False
				
# Private implementation - a QTreeView with some specific size behaviour, and shift
# clicking for recursive expand/collapse.
class _TreeView( QtGui.QTreeView ) :

	# This signal is called when some items are either collapsed or
	# expanded. It can be preferable to use this over the expanded or
	# collapsed signals as it is emitted only once when making several
	# changes.
	expansionChanged = QtCore.Signal()

	def __init__( self ) :
	
		QtGui.QTreeView.__init__( self )
		
		self.setHorizontalScrollBarPolicy( QtCore.Qt.ScrollBarAlwaysOff )
				
		self.header().geometriesChanged.connect( self.updateGeometry )
		self.header().sectionResized.connect( self.__sectionResized )
		
		self.collapsed.connect( self.__collapsed )
		self.expanded.connect( self.__expanded )
	
		self.__recalculatingColumnWidths = False
		# the ideal size for each column. we cache these because they're slow to compute
		self.__idealColumnWidths = [] 
		# offsets to the ideal sizes made by the user
		self.__columnWidthAdjustments = []
		
		self.__currentEventModifiers = QtCore.Qt.NoModifier
	
	def setModel( self, model ) :
	
		QtGui.QTreeView.setModel( self, model )
		
		model.modelReset.connect( self.__recalculateColumnSizes )

		self.__recalculateColumnSizes()
	
	def setExpandedIndices( self, indices ) :
	
		self.collapsed.disconnect( self.__collapsed )
		self.expanded.disconnect( self.__expanded )

		self.collapseAll()
		for index in indices :
			self.setExpanded( index, True )

		self.collapsed.connect( self.__collapsed )
		self.expanded.connect( self.__expanded )
	
		self.__recalculateColumnSizes()

		self.expansionChanged.emit()
	
	## \todo This isn't returning expanded items which are
	# parented below collapsed items. Changing this either
	# means a full traversal of the entire tree, or keeping
	# track of a set of expanded indices in __collapsed/__expanded.
	# Traversing the entire tree might not be too expensive
	# if we get the model populated lazily using fetchMore()
	# though.	
	def getExpandedIndices( self ) :
	
		result = []		
		model = self.model()
		def walk( index ) :
			for i in range( 0, model.rowCount( index ) ) :
				childIndex = model.index( i, 0, index )
				if self.isExpanded( childIndex ) :
					result.append( childIndex )
					walk( childIndex )
									
		walk( QtCore.QModelIndex() )		
		return result
	
	def sizeHint( self ) :
	
		result = QtGui.QTreeView.sizeHint( self )
		
		margins = self.contentsMargins()
		result.setWidth( self.header().length() + margins.left() + margins.right() )

		result.setHeight( max( result.width() * .5, result.height() ) )
		
		return result
	
	def mousePressEvent( self, event ) :
	
		# we store the modifiers so that we can turn single
		# expands/collapses into recursive ones in __propagateExpanded.
		self.__currentEventModifiers = event.modifiers()
		QtGui.QTreeView.mousePressEvent( self, event )
		self.__currentEventModifiers = QtCore.Qt.NoModifier
		
	def mouseReleaseEvent( self, event ) :
	
		# we store the modifiers so that we can turn single
		# expands/collapses into recursive ones in __propagateExpanded.
		self.__currentEventModifiers = event.modifiers()
		QtGui.QTreeView.mouseReleaseEvent( self, event )
		self.__currentEventModifiers = QtCore.Qt.NoModifier
	
	def mouseDoubleClickEvent( self, event ) :
	
		self.__currentEventModifiers = event.modifiers()
		QtGui.QTreeView.mouseDoubleClickEvent( self, event )
		self.__currentEventModifiers = QtCore.Qt.NoModifier
		
	def __recalculateColumnSizes( self ) :
				
		self.__recalculatingColumnWidths = True
	
		header = self.header()
		numColumnsToResize = header.count() - 1 # leave the last section alone, as it's expandable
		
		if numColumnsToResize != len( self.__columnWidthAdjustments ) :
			# either the first time in here, or the number of columns has
			# changed and we want to start again with the offsets.
			self.__columnWidthAdjustments = [ 0 ] * numColumnsToResize
		
		del self.__idealColumnWidths[:]
		for i in range( 0, numColumnsToResize ) : 

			idealWidth = max( header.sectionSizeHint( i ), self.sizeHintForColumn( i ) )
			self.__idealColumnWidths.append( idealWidth )
						
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
	
	def __collapsed( self, index ) :
	
		self.__propagateExpanded( index, False )
		self.__recalculateColumnSizes()

		self.expansionChanged.emit()
		
	def __expanded( self, index ) :
	
		self.__propagateExpanded( index, True )
		self.__recalculateColumnSizes()
		
		self.expansionChanged.emit()
	
	def __propagateExpanded( self, index, expanded ) :
	
		def __walk( index, expanded, numLevels ) :
	
			model = self.model()
			while model.canFetchMore( index ) :
				model.fetchMore( index )
		
			for i in range( 0, model.rowCount( index ) ) :
				childIndex = model.index( i, 0, index )
				self.setExpanded( childIndex, expanded )
				if numLevels - 1 :
					__walk( childIndex, expanded, numLevels - 1 )

		numLevels = 0
		if self.__currentEventModifiers & QtCore.Qt.ShiftModifier :
			numLevels = 10000
		elif self.__currentEventModifiers & QtCore.Qt.ControlModifier :
			numLevels = 1
		
		if numLevels :
			
			self.collapsed.disconnect( self.__collapsed )
			self.expanded.disconnect( self.__expanded )
			
			__walk( index, expanded, numLevels )
			
			self.collapsed.connect( self.__collapsed )
			self.expanded.connect( self.__expanded )
							
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
		if row >=0 and row < len( childItems ) and column >= 0 and column < len( self.__columns ) :
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
