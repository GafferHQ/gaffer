##########################################################################
#
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2011-2014, Image Engine Design Inc. All rights reserved.
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

import warnings

import IECore

import Gaffer
from . import _GafferUI
import GafferUI

import Qt
from Qt import QtCore
from Qt import QtGui
from Qt import QtWidgets

## The PathListingWidget displays the contents of a Path, updating the Path to represent the
# current directory as the user navigates around. It supports both a list and a tree view,
# allows customisable column listings, and supports both single and multiple selection.
class PathListingWidget( GafferUI.Widget ) :

	Column = _GafferUI._PathListingWidgetColumn
	StandardColumn = _GafferUI._PathListingWidgetStandardColumn
	IconColumn = _GafferUI._PathListingWidgetIconColumn

	## A collection of handy column definitions for FileSystemPaths
	defaultNameColumn = StandardColumn( "Name", "name" )
	defaultFileSystemOwnerColumn = StandardColumn( "Owner", "fileSystem:owner" )
	defaultFileSystemModificationTimeColumn = StandardColumn( "Modified", "fileSystem:modificationTime" )
	defaultFileSystemIconColumn = _GafferUI._PathListingWidgetFileIconColumn()

	defaultFileSystemColumns = (
		defaultNameColumn,
		defaultFileSystemOwnerColumn,
		defaultFileSystemModificationTimeColumn,
		defaultFileSystemIconColumn,
	)

	## A collection of handy column definitions for IndexedIOPaths
	## \todo Perhaps these belong in GafferCortexUI?
	defaultIndexedIOEntryTypeColumn = StandardColumn( "Entry Type", "indexedIO:entryType" )
	defaultIndexedIODataTypeColumn = StandardColumn( "Data Type", "indexedIO:dataType" )
	defaultIndexedIOArrayLengthColumn = StandardColumn( "Array Length", "indexedIO:arrayLength" )

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
		sortable = True,
		horizontalScrollMode = GafferUI.ScrollMode.Never,
		**kw
	) :

		GafferUI.Widget.__init__( self, _TreeView(), **kw )

		self._qtWidget().setAlternatingRowColors( True )
		self._qtWidget().setUniformRowHeights( True )
		self._qtWidget().setEditTriggers( QtWidgets.QTreeView.NoEditTriggers )
		self._qtWidget().activated.connect( Gaffer.WeakMethod( self.__activated ) )
		self._qtWidget().setHorizontalScrollBarPolicy( GafferUI.ScrollMode._toQt( horizontalScrollMode ) )

		self._qtWidget().header().setSectionsMovable( False )

		self._qtWidget().header().setSortIndicator( 0, QtCore.Qt.AscendingOrder )
		self._qtWidget().setSortingEnabled( sortable )

		self._qtWidget().expansionChanged.connect( Gaffer.WeakMethod( self.__expansionChanged ) )

		# install an empty model, so we an construct our selection model
		# around it. we'll update the model contents shortly in setPath().
		_GafferUI._pathListingWidgetUpdateModel( GafferUI._qtAddress( self._qtWidget() ), None )
		_GafferUI._pathListingWidgetSetColumns( GafferUI._qtAddress( self._qtWidget() ), columns )

		self.__selectionModel = QtCore.QItemSelectionModel( self._qtWidget().model() )
		self._qtWidget().setSelectionModel( self.__selectionModel )
		self.__selectionChangedSlot = Gaffer.WeakMethod( self.__selectionChanged )
		self._qtWidget().selectionModel().selectionChanged.connect( self.__selectionChangedSlot )
		if allowMultipleSelection :
			self._qtWidget().setSelectionMode( QtWidgets.QAbstractItemView.ExtendedSelection )

		self.__pathSelectedSignal = GafferUI.WidgetSignal()
		self.__selectionChangedSignal = GafferUI.WidgetSignal()
		self.__displayModeChangedSignal = GafferUI.WidgetSignal()
		self.__expansionChangedSignal = GafferUI.WidgetSignal()

		# members for implementing drag and drop
		self.__emittingButtonPress = False
		self.__borrowedButtonPress = None
		self.buttonPressSignal().connect( Gaffer.WeakMethod( self.__buttonPress ), scoped = False )
		self.buttonReleaseSignal().connect( Gaffer.WeakMethod( self.__buttonRelease ), scoped = False )
		self.mouseMoveSignal().connect( Gaffer.WeakMethod( self.__mouseMove ), scoped = False )
		self.dragBeginSignal().connect( Gaffer.WeakMethod( self.__dragBegin ), scoped = False )
		self.dragEndSignal().connect( Gaffer.WeakMethod( self.__dragEnd ), scoped = False )
		self.__dragPointer = "paths"

		self.__path = None

		self.setDisplayMode( displayMode )
		self.setPath( path )

	def setPath( self, path ) :

		if path.isSame( self.__path ) :
			return

		self.__path = path
		self.__pathChangedConnection = self.__path.pathChangedSignal().connect( Gaffer.WeakMethod( self.__pathChanged ) )
		self.__currentDir = None
		self.__currentPath = ""
		self.__update()

	def getPath( self ) :

		return self.__path

	def scrollToPath( self, path ) :

		index = self.__indexForPath( path )
		if index.isValid() :
			self._qtWidget().scrollTo( index, self._qtWidget().EnsureVisible )

	## Returns the path being displayed at the specified
	# position within the widget. May return None if no path
	# exists at that position.
	def pathAt( self, position ) :

		point = self._qtWidget().viewport().mapFrom(
			self._qtWidget(),
			QtCore.QPoint( position.x, position.y )
		)

		index = self._qtWidget().indexAt( point )
		if not index.isValid() :
			return None

		return self.__pathForIndex( index )

	## Sets which paths are currently expanded
	# using an `IECore.PathMatcher` object.
	def setExpansion( self, paths ) :

		assert( isinstance( paths, IECore.PathMatcher ) )
		self._qtWidget().setExpansion( paths )

	## Returns an `IECore.PathMatcher` object containing
	# the currently expanded paths.
	def getExpansion( self ) :

		return _GafferUI._pathListingWidgetGetExpansion( GafferUI._qtAddress( self._qtWidget() ) )

	def setPathExpanded( self, path, expanded ) :

		index = self.__indexForPath( path )
		if index.isValid() :
			self._qtWidget().setExpanded( index, expanded )

	def getPathExpanded( self, path ) :

		index = self.__indexForPath( path )
		if index.isValid() :
			return self._qtWidget().isExpanded( index )

		return False

	## \deprecated Use `setExpansion()` instead
	def setExpandedPaths( self, paths ) :

		self.setExpansion(
			IECore.PathMatcher(
				[ str( x ) for x in paths ]
			)
		)

	## \deprecated Use `getExpansion()` instead
	def getExpandedPaths( self ) :

		return _GafferUI._pathListingWidgetPathsForPathMatcher(
			GafferUI._qtAddress( self._qtWidget() ),
			self.getExpansion()
		)

	def expansionChangedSignal( self ) :

		return self.__expansionChangedSignal

	def getDisplayMode( self ) :

		if _GafferUI._pathListingWidgetGetFlat( GafferUI._qtAddress( self._qtWidget() ) ) :
			return self.DisplayMode.List
		else :
			return self.DisplayMode.Tree

	def setDisplayMode( self, displayMode ) :

		if displayMode == self.getDisplayMode() :
			return

		# It is possible to implement list mode as follows :
		#
		# ```
		# self._qtWidget().setItemsExpandable( False )
		# self._qtWidget().setRootIsDecorated( False )
		# ```
		#
		# However, even when doing this QTreeView will call
		# QModel::hasChildren() anyway, causing our model to
		# recurse one level deeper than strictly necessary.
		# This can be costly, so instead we implement list
		# view by making the model flat.

		_GafferUI._pathListingWidgetSetFlat( GafferUI._qtAddress( self._qtWidget() ), displayMode == self.DisplayMode.List )

		self.__displayModeChangedSignal( self )

	def displayModeChangedSignal( self ) :

		return self.__displayModeChangedSignal

	def setColumns( self, columns ) :

		if columns == self.getColumns() :
			return

		_GafferUI._pathListingWidgetSetColumns( GafferUI._qtAddress( self._qtWidget() ), columns )

	def getColumns( self ) :

		return _GafferUI._pathListingWidgetGetColumns( GafferUI._qtAddress( self._qtWidget() ) )

	def setHeaderVisible( self, visible ) :

		self._qtWidget().header().setVisible( visible )

	def getHeaderVisible( self ) :

		return not self._qtWidget().header().isHidden()

	## \deprecated Use constructor argument instead.
	def setSortable( self, sortable ) :

		if sortable == self.getSortable() :
			return

		self._qtWidget().setSortingEnabled( sortable )
		if not sortable :
			self._qtWidget().model().sort( -1 )

	## \deprecated
	def getSortable( self ) :

		return self._qtWidget().isSortingEnabled()

	## Sets the currently selected paths using an
	# `IECore.PathMatcher` object.
	def setSelection( self, paths, scrollToFirst=True, expandNonLeaf=True ) :

		assert( isinstance( paths, IECore.PathMatcher ) )

		# If there are pending changes to our path model, we must perform
		# them now, so that the model is valid with respect to the paths
		# we're trying to select.
		self.__updateLazily.flush( self )

		assert( isinstance( paths, IECore.PathMatcher ) )

		selectionModel = self._qtWidget().selectionModel()
		selectionModel.selectionChanged.disconnect( self.__selectionChangedSlot )

		selectionModel.clear()

		_GafferUI._pathListingWidgetSetSelection(
			GafferUI._qtAddress( self._qtWidget() ),
			paths, scrollToFirst, expandNonLeaf
		)

		selectionModel.selectionChanged.connect( self.__selectionChangedSlot )

		self.selectionChangedSignal()( self )

	## Returns an `IECore.PathMatcher` object containing
	# the currently selected paths.
	def getSelection( self ) :

		return _GafferUI._pathListingWidgetGetSelection( GafferUI._qtAddress( self._qtWidget() ) )

	## \deprecated
	def getSelectedPaths( self ) :

		return _GafferUI._pathListingWidgetPathsForPathMatcher(
			GafferUI._qtAddress( self._qtWidget() ),
			self.getSelection()
		)

	## \deprecated
	def setSelectedPaths( self, pathOrPaths, scrollToFirst=True, expandNonLeaf=True ) :

		paths = pathOrPaths
		if isinstance( pathOrPaths, Gaffer.Path ) :
			paths = [ pathOrPaths ]

		if self._qtWidget().selectionMode() != QtWidgets.QAbstractItemView.ExtendedSelection :
			assert( len( paths ) <= 1 )

		self.setSelection(
			IECore.PathMatcher( [ str( path ) for path in paths ] ),
			scrollToFirst, expandNonLeaf
		)

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
		# is the path or the filtering that has changed, and remove self.__currentPath.
		# Also consider whether it might be easier for the C++ PathModel to be
		# doing the signal handling at that point.

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

			_GafferUI._pathListingWidgetUpdateModel( GafferUI._qtAddress( self._qtWidget() ), dirPath.copy() )

			if expandedPaths is not None :
				self.setExpandedPaths( expandedPaths )

			self.setSelectedPaths( selectedPaths, scrollToFirst = False, expandNonLeaf = False )

			self.__currentDir = dirPath

		self.__currentPath = str( self.__path )

	@GafferUI.LazyMethod()
	def __updateLazily( self ) :

		self.__update()

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

		if self.getDisplayMode() == self.DisplayMode.List :
			self.__path[:] = activatedPath[:]

		if activatedPath.isLeaf() :
			self.pathSelectedSignal()( self )
			return True

		return False

	def __selectionChanged( self, selected, deselected ) :

		self.selectionChangedSignal()( self )
		return True

	def __pathChanged( self, path ) :

		# Updates can be expensive, so we coalesce and
		# defer them until the last minute.
		self.__updateLazily()

	def __indexForPath( self, path ) :

		result = QtCore.QModelIndex()
		_GafferUI._pathListingWidgetIndexForPath(
			GafferUI._qtAddress( self._qtWidget() ),
			path,
			GafferUI._qtAddress( result ),
		)

		return result

	def __pathForIndex( self, modelIndex ) :

		return _GafferUI._pathListingWidgetPathForIndex(
			GafferUI._qtAddress( self._qtWidget() ),
			GafferUI._qtAddress( modelIndex ),
		)

	def __expansionChanged( self ) :

		self.__expansionChangedSignal( self )

	def __buttonPress( self, widget, event ) :

		if self.__emittingButtonPress :
			return False

		self.__borrowedButtonPress = None
		if event.buttons == event.Buttons.Left and event.modifiers == event.Modifiers.None_ :

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

			point = self._qtWidget().viewport().mapFrom(
				self._qtWidget(),
				QtCore.QPoint( event.line.p0.x, event.line.p0.y )
			)
			index = self._qtWidget().indexAt( point )

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

		# nothing to drag if there's no valid list entry under the pointer
		point = self._qtWidget().viewport().mapFrom(
			self._qtWidget(),
			QtCore.QPoint( event.line.p0.x, event.line.p0.y )
		)
		index = self._qtWidget().indexAt( point )
		if not index.isValid() :
			return None

		selection = self.getSelection()
		if not( selection.isEmpty() ) :
			GafferUI.Pointer.setCurrent( self.__dragPointer )
			return IECore.StringVectorData( selection.paths() )

		return None

	def __dragEnd( self, widget, event ) :

		GafferUI.Pointer.setCurrent( None )

	def __emitButtonPress( self, event ) :

		point = self._qtWidget().viewport().mapFrom(
			self._qtWidget(),
			QtCore.QPoint( event.line.p0.x, event.line.p0.y )
		)

		qEvent = QtGui.QMouseEvent(
			QtCore.QEvent.MouseButtonPress,
			point,
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
class _TreeView( QtWidgets.QTreeView ) :

	# This signal is called when some items are either collapsed or
	# expanded. It can be preferable to use this over the expanded or
	# collapsed signals as it is emitted only once when making several
	# changes.
	expansionChanged = QtCore.Signal()

	def __init__( self ) :

		QtWidgets.QTreeView.__init__( self )

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

		QtWidgets.QTreeView.setModel( self, model )

		model.modelReset.connect( self.__recalculateColumnSizes )

		self.__recalculateColumnSizes()

	def setExpansion( self, paths ) :

		self.collapsed.disconnect( self.__collapsed )
		self.expanded.disconnect( self.__expanded )

		self.collapseAll()
		# This call is critical to performance - without
		# it an update is triggered for every call to
		# setExpanded().
		self.scheduleDelayedItemsLayout()

		_GafferUI._pathListingWidgetSetExpansion( GafferUI._qtAddress( self ), paths )

		self.collapsed.connect( self.__collapsed )
		self.expanded.connect( self.__expanded )

		self.__recalculateColumnSizes()

		self.expansionChanged.emit()

	def sizeHint( self ) :

		result = QtWidgets.QTreeView.sizeHint( self )

		margins = self.contentsMargins()
		result.setWidth( self.header().length() + margins.left() + margins.right() )

		result.setHeight( max( result.width() * .5, result.height() ) )

		return result

	def event( self, event ) :

		if event.type() == event.ShortcutOverride :
			if event.key() in ( QtCore.Qt.Key_Up, QtCore.Qt.Key_Down, QtCore.Qt.Key_Left, QtCore.Qt.Key_Right ) :
				event.accept()
				return True

		return QtWidgets.QTreeView.event( self, event )

	def mousePressEvent( self, event ) :

		# we store the modifiers so that we can turn single
		# expands/collapses into recursive ones in __propagateExpanded.
		self.__currentEventModifiers = event.modifiers()
		QtWidgets.QTreeView.mousePressEvent( self, event )
		self.__currentEventModifiers = QtCore.Qt.NoModifier

	def mouseReleaseEvent( self, event ) :

		# we store the modifiers so that we can turn single
		# expands/collapses into recursive ones in __propagateExpanded.
		self.__currentEventModifiers = event.modifiers()
		QtWidgets.QTreeView.mouseReleaseEvent( self, event )
		self.__currentEventModifiers = QtCore.Qt.NoModifier

	def mouseDoubleClickEvent( self, event ) :

		self.__currentEventModifiers = event.modifiers()
		QtWidgets.QTreeView.mouseDoubleClickEvent( self, event )
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

		numLevels = 0
		if self.__currentEventModifiers & QtCore.Qt.ShiftModifier :
			numLevels = 10000
		elif self.__currentEventModifiers & QtCore.Qt.ControlModifier :
			numLevels = 1

		if numLevels :

			self.collapsed.disconnect( self.__collapsed )
			self.expanded.disconnect( self.__expanded )

			# This call is critical for performance. Without it,
			# QTreeView will start doing relayout for every single
			# call to setExpanded() that we make inside
			# _pathListingWidgetPropagateExpanded(). With it, it
			# waits nicely till the end and does it all at once.
			self.scheduleDelayedItemsLayout()

			# Defer to C++ to do the heavy lifting.
			_GafferUI._pathListingWidgetPropagateExpanded(
				GafferUI._qtAddress( self ),
				GafferUI._qtAddress( index ),
				expanded,
				numLevels
			)

			self.collapsed.connect( self.__collapsed )
			self.expanded.connect( self.__expanded )
