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

import collections
import enum
import math
import warnings

import imath

import IECore

import Gaffer
from . import _GafferUI
from ._StyleSheet import _styleColors
import GafferUI

import Qt
from Qt import QtCore
from Qt import QtGui
from Qt import QtWidgets

## The PathListingWidget displays the contents of a Path, updating the Path to represent the
# current directory as the user navigates around. It supports both a list and a tree view,
# allows customisable column listings, and supports both single and multiple selection.
class PathListingWidget( GafferUI.Widget ) :

	Column = _GafferUI.PathColumn
	StandardColumn = _GafferUI.StandardPathColumn
	IconColumn = _GafferUI.IconPathColumn

	## A collection of handy column definitions for FileSystemPaths
	defaultNameColumn = StandardColumn( "Name", "name", GafferUI.PathColumn.SizeMode.Stretch )
	defaultFileSystemOwnerColumn = StandardColumn( "Owner", "fileSystem:owner" )
	defaultFileSystemModificationTimeColumn = StandardColumn( "Modified", "fileSystem:modificationTime" )
	defaultFileSystemIconColumn = GafferUI.FileIconPathColumn()

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

	DisplayMode = enum.Enum( "DisplayMode", [ "List", "Tree" ] )
	SelectionMode = enum.Enum( "SelectionMode", [ "Row", "Rows", "Cell", "Cells" ] )

	def __init__(
		self,
		path,
		columns = defaultFileSystemColumns,
		selectionMode = SelectionMode.Row,
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

		# Install an empty model. We'll update the model contents shortly in setPath().

		_GafferUI._pathListingWidgetUpdateModel( GafferUI._qtAddress( self._qtWidget() ), None )
		self.setColumns( columns )

		# Turn off selection in Qt. QItemSelectionModel is full of quadratic performance
		# hazards so we rely entirely on our own PathMatcher instead. We update the PathMatcher
		# directly in `__buttonPress`, `__buttonRelease` and `__keyPress`.

		self._qtWidget().setSelectionMode( QtWidgets.QAbstractItemView.NoSelection )
		self.__selectionMode = selectionMode
		self.__lastSelectedIndex = None

		# Enable item hover tracking, so `PathListingWidgetItemDelegate::initStyleOption()` is
		# provided with hover state via the `QStyle::State_MouseOver` flag. Also set the selection
		# behaviour to be per-item rather than per-row (even though we're not using Qt selection),
		# because otherwise Qt sets `State_MouseOver` for entire rows.

		self._qtWidget().viewport().setAttribute( QtCore.Qt.WA_Hover )
		self._qtWidget().setSelectionBehavior( QtWidgets.QAbstractItemView.SelectItems )

		# Set up our various signals.

		self._qtWidget().model().selectionChanged.connect( Gaffer.WeakMethod( self.__selectionChanged ) )
		self._qtWidget().model().expansionChanged.connect( Gaffer.WeakMethod( self.__expansionChanged ) )
		self._qtWidget().model().updateFinished.connect( Gaffer.WeakMethod( self.__updateFinished ) )

		self.__pathSelectedSignal = GafferUI.WidgetSignal()
		self.__selectionChangedSignal = GafferUI.WidgetSignal()
		self.__displayModeChangedSignal = GafferUI.WidgetSignal()
		self.__expansionChangedSignal = GafferUI.WidgetSignal()
		self.__updateFinishedSignal = GafferUI.WidgetSignal()
		self.__columnContextMenuSignal = Gaffer.Signal3()

		# Connections for implementing selection and drag and drop.
		self.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ) )
		self.buttonPressSignal().connect( Gaffer.WeakMethod( self.__buttonPress ) )
		self.buttonReleaseSignal().connect( Gaffer.WeakMethod( self.__buttonRelease ) )
		self.buttonDoubleClickSignal().connect( Gaffer.WeakMethod( self.__buttonDoubleClick ) )
		self.mouseMoveSignal().connect( Gaffer.WeakMethod( self.__mouseMove ) )
		self.dragBeginSignal().connect( Gaffer.WeakMethod( self.__dragBegin ) )
		self.dragEndSignal().connect( Gaffer.WeakMethod( self.__dragEnd ) )
		self.dragEnterSignal().connect( Gaffer.WeakMethod( self.__dragEnter ) )
		self.dragMoveSignal().connect( Gaffer.WeakMethod( self.__dragMove ) )
		self.dragLeaveSignal().connect( Gaffer.WeakMethod( self.__dragLeave ) )
		self.dropSignal().connect( Gaffer.WeakMethod( self.__drop ) )
		self.contextMenuSignal().connect( Gaffer.WeakMethod( self.__contextMenu ) )
		self.__dragPointer = "paths"
		self.__dragBeginIndex = None
		self.__currentDragIndex = None
		self.__path = None

		self.setDisplayMode( displayMode )
		self.setPath( path )

		self._displayTransformChanged()

	def setPath( self, path ) :

		if path.isSame( self.__path ) :
			return

		self.__path = path
		self.__pathChangedConnection = self.__path.pathChangedSignal().connect( Gaffer.WeakMethod( self.__pathChanged ), scoped = True )
		self.__currentDir = None
		self.__currentPath = ""
		self.__update()

	def getPath( self ) :

		return self.__path

	def scrollToPath( self, path ) :

		index = self.__indexForPath( path )
		if index.isValid() :
			self._qtWidget().scrollTo( index, self._qtWidget().EnsureVisible )

	## Scrolls to the first path found in the provided
	# `IECore.PathMatcher`.
	def scrollToFirst( self, paths ) :

		assert( isinstance( paths, IECore.PathMatcher ) )
		GafferUI._GafferUI._pathListingWidgetScrollToFirst( GafferUI._qtAddress( self._qtWidget() ), paths )

	## Returns the path being displayed at the specified
	# position within the widget. May return None if no path
	# exists at that position.
	def pathAt( self, position ) :

		index = self.__indexAt( position )
		if index is None :
			return None

		return self.__pathForIndex( index )

	## Returns the column being displayed at the specified
	# position within the widget.
	def columnAt( self, position ) :

		point = self._qtWidget().viewport().mapFrom(
			self._qtWidget(),
			QtCore.QPoint( position.x, position.y )
		)

		return self.getColumns()[self._qtWidget().columnAt( point.x())]

	## Sets which paths are currently expanded
	# using an `IECore.PathMatcher` object.
	def setExpansion( self, paths ) :

		assert( isinstance( paths, IECore.PathMatcher ) )
		_GafferUI._pathListingWidgetSetExpansion( GafferUI._qtAddress( self._qtWidget() ), paths )

	## Returns an `IECore.PathMatcher` object containing
	# the currently expanded paths.
	def getExpansion( self ) :

		return _GafferUI._pathListingWidgetGetExpansion( GafferUI._qtAddress( self._qtWidget() ) )

	def setPathExpanded( self, path, expanded ) :

		e = self.getExpansion()
		if expanded :
			if e.addPath( str( path ) ) :
				self.setExpansion( e )
		else :
			if e.removePath( str( path ) ) :
				self.setExpansion( e )

	def getPathExpanded( self, path ) :

		return bool( self.getExpansion().match( str( path ) ) & IECore.PathMatcher.Result.ExactMatch )

	## \deprecated Use `setExpansion()` instead
	def setExpandedPaths( self, paths ) :

		self.setExpansion(
			IECore.PathMatcher(
				[ str( x ) for x in paths ]
			)
		)

	## \deprecated Use `getExpansion()` instead
	def getExpandedPaths( self ) :

		# Note : This doesn't follow the semantics of `getExpansion()` with
		# respect to paths that are not currently in the model. It is probably
		# time it was removed.
		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( self._qtWidget().model() ) )
		return _GafferUI._pathListingWidgetPathsForPathMatcher(
			GafferUI._qtAddress( self._qtWidget() ),
			self.getExpansion()
		)

	def expandTo( self, paths ) :

		assert( isinstance( paths, IECore.PathMatcher ) )
		expansion = self.getExpansion()
		expansion.addPaths( _GafferUI._pathListingWidgetAncestorPaths( paths ) )
		self.setExpansion( expansion )

	def expandToSelection( self ) :

		self.expandTo( self.getSelection() )

	def expansionChangedSignal( self ) :

		return self.__expansionChangedSignal

	def updateFinishedSignal( self ) :

		return self.__updateFinishedSignal

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
		self._qtWidget().updateColumnWidths()

	def getColumns( self ) :

		return _GafferUI._pathListingWidgetGetColumns( GafferUI._qtAddress( self._qtWidget() ) )

	def setHeaderVisible( self, visible ) :

		self._qtWidget().header().setVisible( visible )

	def getHeaderVisible( self ) :

		return not self._qtWidget().header().isHidden()

	def setSortable( self, sortable ) :

		if sortable == self.getSortable() :
			return

		self._qtWidget().setSortingEnabled( sortable )
		if not sortable :
			self._qtWidget().model().sort( -1 )

	def getSortable( self ) :

		return self._qtWidget().isSortingEnabled()

	## Sets the currently selected paths. Accepts a single `IECore.PathMatcher`
	# for `Row` and `Rows` modes, and a list of `IECore.PathMatcher`, one for
	# each column, for `Cell` and `Cells` modes.
	def setSelection( self, paths, scrollToFirst=True ) :

		if self.__rowSelectionMode() :
			assert( isinstance( paths, IECore.PathMatcher ) )

			if self.__selectionMode == self.SelectionMode.Row and paths.size() > 1 :
				raise ValueError( "More than one row selected" )

		elif self.__cellSelectionMode() :
			assert( isinstance( paths, list ) )
			assert( all( isinstance( p, IECore.PathMatcher ) for p in paths  ) )

			if len( self.getColumns() ) != len( paths ) :
				raise ValueError( "Number of PathMatchers must match the number of columns" )

			if (
				self.__selectionMode == self.SelectionMode.Cell and
				sum( [ p.size() for p in paths ] ) > 1
			) :
				raise ValueError( "More than one cell selected" )

		self.__setSelectionInternal( paths, scrollToFirst )

	## Returns an `IECore.PathMatcher` object containing the currently selected
	# paths for `Row` or `Rows` modes, and a list of `IECore.PathMatcher`
	# objects, one for each column, for `Cell` or `Cells` modes.
	def getSelection( self ) :

		selection = self.__getSelectionInternal()

		if self.__rowSelectionMode() :
			return selection[0] if len( selection ) > 0 else IECore.PathMatcher()

		return selection


	## \deprecated
	def getSelectedPaths( self ) :

		_GafferUI._pathModelWaitForPendingUpdates( GafferUI._qtAddress( self._qtWidget().model() ) )
		return _GafferUI._pathListingWidgetPathsForPathMatcher(
			GafferUI._qtAddress( self._qtWidget() ),
			self.getSelection()
		)

	## \deprecated
	def setSelectedPaths( self, pathOrPaths, scrollToFirst=True ) :

		paths = pathOrPaths
		if isinstance( pathOrPaths, Gaffer.Path ) :
			paths = [ pathOrPaths ]

		self.setSelection(
			IECore.PathMatcher( [ str( path ) for path in paths ] ),
			scrollToFirst
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

	## Signal emitted to generate a context menu for a column. This allows
	# multiple clients to collaborate in the construction of a menu, with each
	# providing different items. It should be preferred to the generic
	# `Widget.contextMenuSignal()`.
	#
	# Slots must have the following signature, with the `menuDefinition` being
	# edited directly in place :
	#
	# `slot( column, pathListingWidget, menuDefinition )`
	def columnContextMenuSignal( self ) :

		return self.__columnContextMenuSignal

	def setDragPointer( self, dragPointer ) :

		self.__dragPointer = dragPointer

	def getDragPointer( self ) :

		return self.__dragPointer

	def _displayTransformChanged( self ) :

		GafferUI.Widget._displayTransformChanged( self )

		displayTransform = self.displayTransform()
		_GafferUI._pathListingWidgetUpdateDelegate(
			GafferUI._qtAddress( self._qtWidget() ),
			displayTransform if displayTransform is not GafferUI.Widget.identityDisplayTransform else None
		)

	def __setSelectionInternal( self, paths, scrollToFirst=True ) :

		paths = paths if isinstance( paths, list ) else [paths] * len( self.getColumns() )

		_GafferUI._pathListingWidgetSetSelection(
			GafferUI._qtAddress( self._qtWidget() ),
			paths, scrollToFirst
		)

	def __getSelectionInternal( self ) :

		# Within `PathListingWidget` we standardise on using a list of `PathMatcher`.
		return _GafferUI._pathListingWidgetGetSelection( GafferUI._qtAddress( self._qtWidget() ) )

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

			_GafferUI._pathListingWidgetUpdateModel( GafferUI._qtAddress( self._qtWidget() ), dirPath.copy() )
			self.__currentDir = dirPath

		self.__currentPath = str( self.__path )

	def __dirPath( self ) :

		p = self.__path.copy()
		if not len( p ) :
			return p

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

		if self.getDisplayMode() == self.DisplayMode.List :
			self.__path[:] = activatedPath[:]

		if activatedPath.isLeaf() :
			self.pathSelectedSignal()( self )
			return True

		return False

	def __selectionChanged( self ) :

		self._qtWidget().update()
		self.selectionChangedSignal()( self )

	def __pathChanged( self, path ) :

		self.__update()

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

	def __pathsForIndexRange( self, index0, index1 ) :

		assert( isinstance( index0, QtCore.QModelIndex ) )
		assert( isinstance( index1, QtCore.QModelIndex ) )
		assert( index0.isValid() )
		assert( index1.isValid() )

		return _GafferUI._pathListingWidgetPathsForIndexRange(
			GafferUI._qtAddress( self._qtWidget() ),
			GafferUI._qtAddress( index0 ),
			GafferUI._qtAddress( index1 ),
		)

	def __expansionChanged( self ) :

		self.__expansionChangedSignal( self )

	def __updateFinished( self ) :

		self.__updateFinishedSignal( self )

	def __keyPress( self, widget, event ) :

		# Use `__lastSelectedIndex` if available so that shift + keypress
		# accumulates selection.
		index = self.__lastSelectedIndex
		assert( isinstance( index, ( type( None ), QtCore.QPersistentModelIndex ) ) )
		if index is not None and index.isValid() :
			# Convert from persistent index
			index = QtCore.QModelIndex( index )
		else :
			index = self._qtWidget().currentIndex()

		if (
			event.key in ( "Up", "Down" ) or (
				event.key in ( "Left", "Right" ) and self.__cellSelectionMode()
			)
		):

			if not index.isValid() :
				return True
			if event.key == "Up" :
				newIndex = self._qtWidget().indexAbove( index )
			elif event.key == "Down" :
				newIndex = self._qtWidget().indexBelow( index )
			elif event.key == "Left" :
				newIndex = index.siblingAtColumn( index.column() - 1 )
			else :
				newIndex = index.siblingAtColumn( index.column() + 1 )

			if not newIndex.isValid() :
				return True

			if self.__multiSelectionMode() :

				if event.modifiers & event.Modifiers.Shift :
					self.__rangeSelect( newIndex )
					return True

				if event.modifiers == event.Modifiers.Control :
					self.__toggleSelect( newIndex )
					return True

			self.__singleSelect( newIndex )

			return True

		elif event.key == "A" and event.modifiers == event.Modifiers.Control :

			lastVisibleIndex = self._qtWidget().lastVisibleIndex()
			if lastVisibleIndex.isValid() :
				selection = [
					self.__pathsForIndexRange(
						self._qtWidget().model().index( 0, 0 ),
						lastVisibleIndex
					)
				] * len( self.getColumns() )
			else :
				selection = [IECore.PathMatcher()] * len( self.getColumns() )

			self.__setSelectionInternal( selection, scrollToFirst=False )
			return True

		# Delegate the keyPress to the PathColumn, if it wants it.

		elif index.isValid() and self.getColumns()[index.column()].keyPressSignal()(
			self.getColumns()[index.column()], self, event
		) :
			return True

		return False

	# Handles interactions for selection and expansion. Done at the level
	# of `GafferUI.Widget` events rather than `QWidget::mousePressEvent()`
	# for compatibility with `GafferUI.Widget.dragBeginSignal()`.
	def __buttonPress( self, widget, event ) :

		self.__updateSelectionInButtonRelease = False

		# Get model index under cursor.

		index = self.__indexAt( event.line.p0 )
		if index is None :
			return False

		# Delegate the click to the PathColumn, if it wants it.

		if self.getColumns()[index.column()].buttonPressSignal()(
			self.__pathForIndex( index ), self, event
		) :
			return True

		# Otherwise, perform expansion and selection as appropriate.

		if event.buttons != event.Buttons.Left :
			return False

		# Do expansion/collapsing if the arrow was clicked on. QTreeView doesn't
		# expose any queries for the arrow position, but we know it is to the
		# left of the rect used to draw the item.

		qPoint = self._qtWidget().viewport().mapFrom(
			self._qtWidget(),
			QtCore.QPoint( event.line.p0.x, event.line.p0.y )
		)

		if self._qtWidget().model().hasChildren( index ) :
			rect = self._qtWidget().visualRect( index )
			if qPoint.x() < rect.x() and qPoint.x() >= rect.x() - 20 :
				self._qtWidget().setExpanded( index, not self._qtWidget().isExpanded( index ) )
				## \todo It would be more natural to trigger recursive expansion
				# from here rather than `PathModel::treeViewExpanded()`.
				return True

		if self.__multiSelectionMode() :
			if event.modifiers & event.Modifiers.Shift :
				self.__rangeSelect( index )
				return True

			if event.modifiers & event.Modifiers.Control :
				self.__toggleSelect( index )
				return True

		selection = self.__getSelectionInternal()
		path = str( self.__pathForIndex( index ) )
		pathSelected = selection[ index.column() ].match( path ) & IECore.PathMatcher.Result.ExactMatch

		if not pathSelected :
			self.__singleSelect( index )
		else :
			# The item is selected, Return True so that we have the option of
			# starting a drag if we want. If a drag doesn't follow, we'll adjust
			# selection in `__buttonRelease`.
			self.__updateSelectionInButtonRelease = True

		return True

	def __buttonRelease( self, widget, event ) :

		index = self.__indexAt( event.line.p0 )
		if index is None :
			return False

		if self.__updateSelectionInButtonRelease :
			self.__singleSelect( index )
			return True
		else :
			return self.getColumns()[index.column()].buttonReleaseSignal()(
				self.__pathForIndex( index ), self, event
			)

	def __buttonDoubleClick( self, widget, event ) :

		index = self.__indexAt( event.line.p0 )
		if index is None :
			return False

		if self.getColumns()[index.column()].buttonDoubleClickSignal()(
			self.__pathForIndex( index ), self, event
		) :
			return True

		if event.buttons == event.Buttons.Left :
			self.__activated( index )
			return True

		return False

	def __mouseMove( self, widget, event ) :

		# Take the event so that the underlying QTreeView doesn't get it.
		return True

	def __dragBegin( self, widget, event ) :

		path = self.pathAt( imath.V2f( event.line.p0.x, event.line.p0.y ) )

		selection = self.__getSelectionInternal()

		if selection[0].match( str( path ) ) & IECore.PathMatcher.Result.ExactMatch :
			GafferUI.Pointer.setCurrent( self.__dragPointer )
			return IECore.StringVectorData( selection[0].paths() )

		index = self.__indexAt( event.line.p0 )
		if index is not None :
			value = self.getColumns()[index.column()].cellData( path ).value
			if value is not None :
				GafferUI.Pointer.setCurrent( "values" )
				self.__dragBeginIndex = QtCore.QPersistentModelIndex( index )

				return value

		return None

	def __dragEnd( self, widget, event ) :

		GafferUI.Pointer.setCurrent( None )
		self.__dragBeginIndex = None
		self.__currentDragIndex = None

	def __dragEnter( self, widget, event ) :

		index = self.__indexAt( event.line.p0 )
		if index is None :
			return False

		if self.getColumns()[index.column()].dragEnterSignal()(
			self.getColumns()[index.column()], self.__pathForIndex( index ), self, event
		) :
			self.__currentDragIndex = QtCore.QPersistentModelIndex( index )
			self.__setHighlightedIndex( index )
			return True

	def __dragMove( self, widget, event ) :

		assert( isinstance( self.__currentDragIndex, ( type( None ), QtCore.QPersistentModelIndex ) ) )
		if self.__currentDragIndex is not None and self.__currentDragIndex.isValid() :
			previousIndex = QtCore.QModelIndex( self.__currentDragIndex )
		else :
			previousIndex = None

		index = self.__indexAt( event.line.p0 )

		# We've moved out of the previous index
		if previousIndex is not None and previousIndex != index :
			self.__currentDragIndex = None
			self.__setHighlightedIndex( None )
			self.getColumns()[previousIndex.column()].dragLeaveSignal()(
				self.getColumns()[previousIndex.column()], self.__pathForIndex( previousIndex ), self, event
			)

		if index is None or index == self.__dragBeginIndex :
			return False

		# We've moved into a new index
		if previousIndex is None or previousIndex != index :
			if self.getColumns()[index.column()].dragEnterSignal()(
				self.getColumns()[index.column()], self.__pathForIndex( index ), self, event
			) :
				self.__currentDragIndex = QtCore.QPersistentModelIndex( index )
				self.__setHighlightedIndex( index )
				return True
		elif previousIndex == index :
			# We've moved within the same index
			return self.getColumns()[index.column()].dragMoveSignal()(
				self.getColumns()[index.column()], self.__pathForIndex( index ), self, event
			)

		return False

	def __dragLeave( self, widget, event ) :

		self.__setHighlightedIndex( None )

		assert( isinstance( self.__currentDragIndex, ( type( None ), QtCore.QPersistentModelIndex ) ) )
		if self.__currentDragIndex is not None and self.__currentDragIndex.isValid() :
			index = QtCore.QModelIndex( self.__currentDragIndex )

			return self.getColumns()[index.column()].dragLeaveSignal()(
				self.getColumns()[index.column()], self.__pathForIndex( index ), self, event
			)

		return False

	def __drop( self, widget, event ) :

		self.__setHighlightedIndex( None )

		index = self.__indexAt( event.line.p0 )
		if index is None or index != self.__currentDragIndex :
			return False

		return self.getColumns()[index.column()].dropSignal()(
			self.getColumns()[index.column()], self.__pathForIndex( index ), self, event
		)

	def __contextMenu( self, widget ) :

		mousePosition = GafferUI.Widget.mousePosition( relativeTo = self )
		column = self.columnAt( mousePosition )
		if not column.contextMenuSignal().numSlots() and not self.columnContextMenuSignal().numSlots() :
			# Allow legacy clients connected to `Widget.contextMenuSignal()` to
			# do their own thing instead.
			return False

		# Select the path under the mouse, if it's not already selected.
		# The user will expect to be operating on the thing under the mouse.

		path = self.pathAt( mousePosition )
		if path is not None :
			path = str( path )
			selection = self.getSelection()
			if isinstance( selection, IECore.PathMatcher ) :
				# Row or Rows mode.
				if not selection.match( path ) & IECore.PathMatcher.Result.ExactMatch :
					selection = IECore.PathMatcher( [ path ] )
					self.setSelection( selection )
			else :
				# Cell or Cells mode.
				columnIndex = self.getColumns().index( column )
				if not selection[columnIndex].match( path ) & IECore.PathMatcher.Result.ExactMatch :
					for i in range( 0, len( selection ) ) :
						selection[i] = IECore.PathMatcher() if columnIndex != i else IECore.PathMatcher( [ path ] )
					self.setSelection( selection )

		# Use signals to build menu and display it.

		menuDefinition = IECore.MenuDefinition()
		column.contextMenuSignal()( column, self, menuDefinition )
		self.columnContextMenuSignal()( column, self, menuDefinition )

		if menuDefinition.size() :
			self.__columnContextMenu = GafferUI.Menu( menuDefinition )
			self.__columnContextMenu.popup( self )

		return True

	def __indexAt( self, position ) :

		point = self._qtWidget().viewport().mapFrom(
			self._qtWidget(),
			QtCore.QPoint( position.x, position.y )
		)

		# A small corner area below the vertical scroll bar may pass through
		# to us, causing odd selection behavior. Check that we're within the
		# scroll area.
		if point.x() > self._qtWidget().viewport().size().width() or point.y() > self._qtWidget().viewport().size().height() :
			return None

		index = self._qtWidget().indexAt( point )
		if not index.isValid() :
			return None

		return index

	def __rangeSelect( self, index ) :

		selection = self.__getSelectionInternal()

		last = self.__lastSelectedIndex
		assert( isinstance( last, ( type( None ), QtCore.QPersistentModelIndex ) ) )
		if last is not None and last.isValid() :
			# Convert from persistent index
			last = QtCore.QModelIndex( last )
		else :
			last = self._qtWidget().currentIndex()

		currentIndex = self._qtWidget().currentIndex()
		if last.isValid() and currentIndex.isValid() :
			lastPaths = self.__pathsForIndexRange( last, currentIndex )
			if self.__rowSelectionMode() :
				for i in range( 0, len( self.getColumns() ) ) :
					selection[i].removePaths( lastPaths )
			elif self.__cellSelectionMode() :
				for i in range(
					min( currentIndex.column(), last.column() ),
					max( currentIndex.column(), last.column() ) + 1
				) :
					selection[i].removePaths( lastPaths )

			newPaths = self.__pathsForIndexRange( index, currentIndex )
			if self.__rowSelectionMode() :
				for i in range( 0, len( self.getColumns() ) ) :
					selection[i].addPaths( newPaths )
			elif self.__cellSelectionMode() :
				for i in range(
					min( currentIndex.column(), index.column() ),
					max( currentIndex.column(), index.column() ) + 1
				) :
					selection[i].addPaths( newPaths )

			self.__setSelectionInternal( selection, scrollToFirst=False )
			self.__lastSelectedIndex = QtCore.QPersistentModelIndex( index )

	def __toggleSelect( self, index ) :

		selection = self.__getSelectionInternal()

		path = str( self.__pathForIndex( index ) )
		pathSelected = selection[ index.column() ].match( path ) & IECore.PathMatcher.Result.ExactMatch

		if pathSelected :
			if self.__rowSelectionMode() :
				for i in range( 0, len( self.getColumns() ) ) :
					selection[i].removePath( path )
			elif self.__cellSelectionMode() :
				selection[index.column()].removePath( path )
		else :
			if self.__rowSelectionMode() :
				for i in range( 0, len( self.getColumns() ) ) :
					selection[i].addPath( path )
			elif self.__cellSelectionMode() :
				selection[index.column()].addPath( path )
		# Although we're managing our own selection state, we
		# do still update the current index because Qt uses it
		# for doing keyboard-based expansion, and we can make use
		# of if in our Shift-click range selection.
		self._qtWidget().setCurrentIndex( index )
		self.__setSelectionInternal( selection, scrollToFirst=False )

		self.__lastSelectedIndex = QtCore.QPersistentModelIndex( index )

	def __singleSelect( self, index ) :

		path = str( self.__pathForIndex( index ) )

		self._qtWidget().setCurrentIndex( index )
		if self.__rowSelectionMode() :
			paths = IECore.PathMatcher( [ path ] )
		elif self.__cellSelectionMode :
			paths = [ IECore.PathMatcher( [ path ] ) if i == index.column() else IECore.PathMatcher() for i in range( 0, len( self.getColumns() ) ) ]
		self.setSelection( paths, scrollToFirst=False )

		self.__lastSelectedIndex = QtCore.QPersistentModelIndex( index )

	def __rowSelectionMode( self ) :

		return self.__selectionMode == self.SelectionMode.Row or self.__selectionMode == self.SelectionMode.Rows

	def __cellSelectionMode( self ) :

		return self.__selectionMode == self.SelectionMode.Cell or self.__selectionMode == self.SelectionMode.Cells

	def __multiSelectionMode( self ) :

		return self.__selectionMode == self.SelectionMode.Rows or self.__selectionMode == self.SelectionMode.Cells

	def __setHighlightedIndex( self, index ) :

		self._qtWidget().setHighlightedIndex( index )

# Private implementation - a QTreeView with some specific size behaviour,
# and knowledge of how to draw our PathMatcher selection.
class _TreeView( QtWidgets.QTreeView ) :

	def __init__( self ) :

		QtWidgets.QTreeView.__init__( self )

		# Our `sizeHint()` depends on the header's size, so we need to
		# ask for a geometry update any time it changes.
		self.header().geometriesChanged.connect( self.updateGeometry )
		self.header().sectionResized.connect( self.__sectionResized )

		# Disable Qt's stretchLastSection behaviour as it will claim any available space in the header
		# before our stretch columns have a chance to resize themselves. We control our own equivalent
		# behaviour based on the result of _shouldStretchLastColumn()
		self.header().setStretchLastSection( False )
		# width of the last column after being automatically stretched to use available space
		self.__lastColumnWidth = 0

		self.__recalculatingColumnWidths = False

		# we track the previous viewport width to aid in determining whether stretchable columns should
		# be resized when the viewport width changes
		self.__previousViewportWidth = 0
		# the ideal size for each column. we cache these because they're slow to compute
		self.__idealColumnWidths = collections.defaultdict( int )
		# offsets to the ideal sizes made by the user
		self.__columnWidthAdjustments = collections.defaultdict( int )

		self.__currentEventModifiers = QtCore.Qt.NoModifier

		self.__highlightedIndex = None

	def setHighlightedIndex( self, index ) :

		self.__highlightedIndex = QtCore.QPersistentModelIndex( index ) if index is not None else None
		self.update()

	def setModel( self, model ) :

		QtWidgets.QTreeView.setModel( self, model )

		## \todo We may want more granular behaviour on model update.
		# Currently column widths are updated when a location is
		# expanded for the first time and requires a model update.
		# This can lead to situations where first expanding and collapsing
		# /a/veryLongName followed by /b/shortName leaves the column
		# resized to /b/shortName. Expanding /a/veryLongName again will
		# not update the column width and truncate to /a/veryLo...
		model.updateFinished.connect( self.updateColumnWidths )

		self.updateColumnWidths()

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

	def resizeEvent( self, event ) :

		viewportWidth = self.viewport().width()
		if viewportWidth != self.__previousViewportWidth :
			if self.__previousViewportWidth == 0 or self.header().length() <= self.__previousViewportWidth or self.header().length() < viewportWidth :
				# We use the previous viewport width to help determine whether the columns should be resized,
				# if the columns fit within the previous width, then we should maintain that relationship and
				# resize to fit the new width. If the columns are narrower than the current viewport width,
				# then we resize to make use of the newly available space.
				self.__resizeStretchColumns()
			self.__previousViewportWidth = viewportWidth

		QtWidgets.QTreeView.resizeEvent( self, event )

	def lastVisibleIndex( self, parentIndex = None ) :

		if parentIndex is None :
			# Root
			parentIndex = QtCore.QModelIndex()
		elif not self.isExpanded( parentIndex ) :
			return parentIndex

		model = self.model()
		rowCount = model.rowCount( parentIndex )
		if rowCount :
			return self.lastVisibleIndex( model.index( rowCount - 1, 0, parentIndex ) )
		else :
			return parentIndex

	def updateColumnWidths( self ) :

		self.__recalculatingColumnWidths = True

		header = self.header()
		numColumnsToResize = header.count()
		stretchLastColumn = self._shouldStretchLastColumn()
		if stretchLastColumn :
			numColumnsToResize -= 1 # leave the last section alone, as it's expandable

		columns = self.__getColumns()
		columnWidthsChanged = False
		for i in range( 0, numColumnsToResize ) :
			if columns[i].getSizeMode() == GafferUI.PathColumn.SizeMode.Interactive :
				idealWidth = max( header.sectionSizeHint( i ), self.sizeHintForColumn( i ) )
				self.__idealColumnWidths[columns[i]] = idealWidth
				adjustedWidth = idealWidth + self.__columnWidthAdjustments[columns[i]]
				if i == header.count() - 1  :
					# the last column may have been automatically extended to fill available space
					# reuse that extended width to provide some consistency between column width updates
					## \todo this may be better handled as a proportion of the overall width
					adjustedWidth = max( adjustedWidth, self.__lastColumnWidth )
				if header.sectionSize( i ) != adjustedWidth :
					header.resizeSection( i, adjustedWidth )
					columnWidthsChanged = True

		if columnWidthsChanged :
			# an update to column widths can require resizing columns configured to stretch
			# to make use of any change in available space
			self.__resizeStretchColumns()

		if stretchLastColumn :
			# finally, resize the last column to make use of any remaining available width
			self.__resizeLastColumnToAvailableWidth()

		self.__recalculatingColumnWidths = False

	def keyPressEvent( self, event ) :

		# When the tree view has focus, the base class steals most
		# keypresses to perform a search for a matching item. We don't
		# like that because it prevents our own hotkeys from working,
		# including the `P` and `N` shortcuts for managing editor focus.
		# There is no way of turning off this behaviour, so we override
		# `keyboardSearch()` to do nothing, and then reject the event
		# after the fact.
		self.__didKeyboardSearch = False
		QtWidgets.QTreeView.keyPressEvent( self, event )
		if self.__didKeyboardSearch :
			event.setAccepted( False )

	def keyboardSearch( self, search ) :

		self.__didKeyboardSearch = True

	def paintEvent( self, event ) :

		QtWidgets.QTreeView.paintEvent( self, event )

		painter = QtGui.QPainter( self.viewport() )
		painter.setPen( QtGui.QColor( *GafferUI._StyleSheet._styleColors["tintDarker"] ) )

		header = self.header()
		height = self.viewport().height()

		for i in range( 1, header.count() ) :
			x = header.sectionViewportPosition( i ) - 1
			painter.drawLine( x, 0, x, height )

		if self.__highlightedIndex is not None and self.__highlightedIndex.isValid() :

			painter.setPen( QtGui.QColor( *(_styleColors["brightColor"]) ) )
			painter.drawRect( self.visualRect( self.__highlightedIndex ) )

	def drawRow( self, painter, option, index ) :

		# Because we're handling selection ourselves using a PathMatcher, we
		# need to draw the selection ourselves. Ideally we'd draw selection as
		# an overlay on top of the row background colour, with the row contents
		# being drawn over that. But both those things are drawn inside
		# `QTreeView.drawRow()`, and we don't want to have to reproduce that
		# entire function ourselves. So we use a little cheat : we draw the
		# selection _under_ everything, and then use partially-transparent row
		# background colours that blend on top of it - see
		# `TreeView.alternate-background-color` in _StyleSheet.py.

		self.__drawRowSelectionHighlight( painter, option.rect, index )

		QtWidgets.QTreeView.drawRow( self, painter, option, index )

	def drawBranches( self, painter, rect, index ) :

		# Qt has a bug whereby it double-draws the row background in the branch
		# area, once in `drawRow()` and then once in `drawBranches()`. This causes
		# partially-transparent backgrounds to be drawn too heavy. Refill with the
		# default background colour before drawing our highlight and deferring the
		# rest to Qt.
		painter.fillRect( rect, QtGui.QColor( *(_styleColors["backgroundRaised"]) ) )

		self.__drawBranchSelectionHighlight( painter, rect, index )

		QtWidgets.QTreeView.drawBranches( self, painter, rect, index )

	def __drawBranchSelectionHighlight( self, painter, rect, index ) :

		pathMatch = index.model().data( index, QtCore.Qt.UserRole )

		if pathMatch & IECore.PathMatcher.Result.ExactMatch :
			self.__drawHighlight( painter, rect, 200 )

		elif pathMatch & IECore.PathMatcher.Result.DescendantMatch :
			self.__drawHighlight( painter, rect, 50 )

	def __drawRowSelectionHighlight( self, painter, rect, index ) :

		header = self.header()

		cellMatches = [
			index.model().data(
				index.siblingAtColumn( i ),
				QtCore.Qt.UserRole
			) for i in range( 0, header.count() )
		]

		descendantMatch = any( m & IECore.PathMatcher.Result.DescendantMatch for m in cellMatches )
		rowMatch = any( m & IECore.PathMatcher.Result.ExactMatch for m in cellMatches )

		for i in range( 0, header.count() ) :
			cellMatch = cellMatches[i]

			left = header.sectionViewportPosition( i )
			width = ( header.sectionViewportPosition( i + 1 ) - left ) if ( i < header.count() - 1 ) else ( rect.right() - left )

			cellRect = QtCore.QRectF(left, rect.top(), width, rect.height() )

			if cellMatch & IECore.PathMatcher.Result.ExactMatch :
				self.__drawHighlight( painter, cellRect, 200 )
			elif descendantMatch :
				self.__drawHighlight( painter, cellRect, 50 )
			elif rowMatch :
				self.__drawHighlight( painter, cellRect, 25 )

	def __drawHighlight( self, painter, rect, alpha ) :

		color = QtGui.QColor( *(_styleColors["brightColor"]) )
		color.setAlpha( alpha )
		painter.fillRect( rect, color )

	def __sectionResized( self, index, oldWidth, newWidth ) :

		if self.__recalculatingColumnWidths :
			# we're only interested in resizing being done by the user
			return

		# store the difference between the ideal size and what the user would prefer, so
		# we can apply it again in updateColumnWidths
		column = self.__getColumns()[index]
		self.__columnWidthAdjustments[column] = newWidth - self.__idealColumnWidths[column]

		# When any column is user resized, automatically adjust the last column's width
		# in order to make use of any empty space.
		if index == self.header().count() - 1 :
			# We prevent the last column from being user resized narrower than the
			# available empty space in the header, but still allow it to be enlarged
			# by providing the user specified column width as the minimum.
			self.__resizeLastColumnToAvailableWidth( newWidth )
		else :
			self.__resizeLastColumnToAvailableWidth()

	def __resizeLastColumnToAvailableWidth( self, minimumSuggestedWidth = 0 ) :

		header = self.header()
		availableWidth = header.width()
		lastColumn = header.count() - 1
		for i in range( 0, lastColumn ) :
			availableWidth -= header.sectionSize( i )

		minimumSectionWidth = max( header.minimumSectionSize(), header.sectionSizeHint( lastColumn ) )
		minimumWidth = max( minimumSectionWidth, minimumSuggestedWidth )

		# take column width adjustment into account when resizing, so we don't
		# inadvertently truncate the last column after a user has extended it
		column = self.__getColumns()[lastColumn]
		if self.__columnWidthAdjustments[ column ] != 0 :
			preferredWidth = self.__idealColumnWidths[ column ] + self.__columnWidthAdjustments[ column ]
			minimumWidth = max( preferredWidth, minimumWidth )

		adjustedWidth = max( minimumWidth, availableWidth )
		self.__lastColumnWidth = adjustedWidth

		self.__recalculatingColumnWidths = True
		header.resizeSection( lastColumn, adjustedWidth )
		self.__recalculatingColumnWidths = False

	def __resizeStretchColumns( self ) :

		header = self.header()
		availableWidth = self.viewport().width()
		stretchColumnWidth = 0
		columnsToStretch = []

		columns = self.__getColumns()
		stretchLastColumn = self._shouldStretchLastColumn()
		for i in range( 0, header.count() ) :
			if (
				columns[i].getSizeMode() == GafferUI.PathColumn.SizeMode.Stretch or
				( stretchLastColumn and i == header.count() - 1 )
			) :
				stretchColumnWidth += header.sectionSize( i )
				columnsToStretch.append( i )
			else :
				availableWidth -= header.sectionSize( i )

		if len( columnsToStretch ) == 0 or availableWidth <= 0 :
			return

		self.__recalculatingColumnWidths = True

		weight = 1.0 / len( columnsToStretch )
		for c in columnsToStretch :
			if stretchColumnWidth > 0 :
				# preserve any existing column proportions
				weight = header.sectionSize( c ) / stretchColumnWidth

			## \todo A very small resize with multiple stretch columns can result in the
			# larger column(s) taking all available space. Doing this repeatedly, such as a
			# slow interactive resize, makes only the larger column(s) appear to stretch.

			minimumWidth = max( header.minimumSectionSize(), header.sectionSizeHint( c ) )
			idealWidth = max( math.floor( availableWidth * weight ), minimumWidth )
			self.__idealColumnWidths[columns[c]] = idealWidth

			header.resizeSection( c, idealWidth )

		self.__recalculatingColumnWidths = False

	def __getColumns( self ) :

		if self.header().count() == 0 :
			return []

		return _GafferUI._pathListingWidgetGetColumns( GafferUI._qtAddress( self ) )

	# Protected rather than private to allow access by PathListingWidgetTest
	def _shouldStretchLastColumn( self ) :

		if self.header().count() == 0 :
			return False

		# automatically stretch the last column to fill available space in the header
		# when no other columns are configured to stretch
		return not any( c.getSizeMode() == GafferUI.PathColumn.SizeMode.Stretch for c in self.__getColumns() )
