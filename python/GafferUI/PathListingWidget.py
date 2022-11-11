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
	defaultNameColumn = StandardColumn( "Name", "name" )
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

	DisplayMode = IECore.Enum.create( "List", "Tree" )
	SelectionMode = IECore.Enum.create( "Row", "Rows", "Cell", "Cells" )

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
		_GafferUI._pathListingWidgetSetColumns( GafferUI._qtAddress( self._qtWidget() ), columns )

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

		# Connections for implementing selection and drag and drop.
		self.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ), scoped = False )
		self.buttonPressSignal().connect( Gaffer.WeakMethod( self.__buttonPress ), scoped = False )
		self.buttonReleaseSignal().connect( Gaffer.WeakMethod( self.__buttonRelease ), scoped = False )
		self.buttonDoubleClickSignal().connect( Gaffer.WeakMethod( self.__buttonDoubleClick ), scoped = False )
		self.mouseMoveSignal().connect( Gaffer.WeakMethod( self.__mouseMove ), scoped = False )
		self.dragBeginSignal().connect( Gaffer.WeakMethod( self.__dragBegin ), scoped = False )
		self.dragEndSignal().connect( Gaffer.WeakMethod( self.__dragEnd ), scoped = False )
		self.__dragPointer = "paths"

		GafferUI.DisplayTransform.changedSignal().connect( Gaffer.WeakMethod( self.__displayTransformChanged ), scoped = False )

		self.__path = None

		self.setDisplayMode( displayMode )
		self.setPath( path )

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
	def setSelection( self, paths, scrollToFirst=True, expandNonLeaf=True ) :

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

		self.__setSelectionInternal( paths, scrollToFirst, expandNonLeaf )

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
	def setSelectedPaths( self, pathOrPaths, scrollToFirst=True, expandNonLeaf=True ) :

		paths = pathOrPaths
		if isinstance( pathOrPaths, Gaffer.Path ) :
			paths = [ pathOrPaths ]

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

	def __setSelectionInternal( self, paths, scrollToFirst=True, expandNonLeaf=True ) :

		paths = paths if isinstance( paths, list ) else [paths] * len( self.getColumns() )

		_GafferUI._pathListingWidgetSetSelection(
			GafferUI._qtAddress( self._qtWidget() ),
			paths, scrollToFirst, expandNonLeaf
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

		if (
			event.key in ( "Up", "Down" ) or (
				event.key in ( "Left", "Right" ) and self.__cellSelectionMode()
			)
		):
			# Use `__lastSelectedIndex` if available so that shift + keypress
			# accumulates selection.
			index = self.__lastSelectedIndex
			assert( isinstance( index, ( type( None ), QtCore.QPersistentModelIndex ) ) )
			if index is not None and index.isValid() :
				# Convert from persistent index
				index = QtCore.QModelIndex( index )
			else :
				index = self._qtWidget().currentIndex()

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

			self.__setSelectionInternal( selection, scrollToFirst=False, expandNonLeaf=False )
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
			GafferUI.Pointer.setCurrent( "values" )

			return self.getColumns()[index.column()].cellData( path ).value

		return None

	def __dragEnd( self, widget, event ) :

		GafferUI.Pointer.setCurrent( None )

	def __displayTransformChanged( self ) :

		# The PathModel bakes the display transform into icon colours,
		# so when the transform changes we need to trigger an update.
		self.__path.pathChangedSignal()( self.__path )

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

			self.__setSelectionInternal( selection, scrollToFirst=False, expandNonLeaf=False )
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
		self.__setSelectionInternal( selection, scrollToFirst=False, expandNonLeaf=False )

		self.__lastSelectedIndex = QtCore.QPersistentModelIndex( index )

	def __singleSelect( self, index ) :

		path = str( self.__pathForIndex( index ) )

		self._qtWidget().setCurrentIndex( index )
		if self.__rowSelectionMode() :
			paths = IECore.PathMatcher( [ path ] )
		elif self.__cellSelectionMode :
			paths = [ IECore.PathMatcher( [ path ] ) if i == index.column() else IECore.PathMatcher() for i in range( 0, len( self.getColumns() ) ) ]
		self.setSelection( paths, scrollToFirst=False, expandNonLeaf=False )

		self.__lastSelectedIndex = QtCore.QPersistentModelIndex( index )

	def __rowSelectionMode( self ) :

		return self.__selectionMode == self.SelectionMode.Row or self.__selectionMode == self.SelectionMode.Rows

	def __cellSelectionMode( self ) :

		return self.__selectionMode == self.SelectionMode.Cell or self.__selectionMode == self.SelectionMode.Cells

	def __multiSelectionMode( self ) :

		return self.__selectionMode == self.SelectionMode.Rows or self.__selectionMode == self.SelectionMode.Cells

# Private implementation - a QTreeView with some specific size behaviour,
# and knowledge of how to draw our PathMatcher selection.
class _TreeView( QtWidgets.QTreeView ) :

	def __init__( self ) :

		QtWidgets.QTreeView.__init__( self )

		self.header().geometriesChanged.connect( self.updateGeometry )
		self.header().sectionResized.connect( self.__sectionResized )

		self.__recalculatingColumnWidths = False
		# the ideal size for each column. we cache these because they're slow to compute
		self.__idealColumnWidths = []
		# offsets to the ideal sizes made by the user
		self.__columnWidthAdjustments = []

		self.__currentEventModifiers = QtCore.Qt.NoModifier

	def setModel( self, model ) :

		QtWidgets.QTreeView.setModel( self, model )

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

	def paintEvent( self, event ) :

		QtWidgets.QTreeView.paintEvent( self, event )

		painter = QtGui.QPainter( self.viewport() )
		painter.setPen( QtGui.QColor( *GafferUI._StyleSheet._styleColors["tintDarker"] ) )

		header = self.header()
		height = self.viewport().height()

		for i in range( 1, header.count() ) :
			x = header.sectionViewportPosition( i ) - 1
			painter.drawLine( x, 0, x, height )

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

		for i in range( 0, header.count() ) :
			cellMatch = cellMatches[i]

			left = header.sectionViewportPosition( i )
			width = ( header.sectionViewportPosition( i + 1 ) - left ) if ( i < header.count() - 1 ) else ( rect.right() - left )

			cellRect = QtCore.QRectF(left, rect.top(), width, rect.height() )

			if descendantMatch and not( cellMatch & IECore.PathMatcher.Result.ExactMatch ) :
				self.__drawHighlight( painter, cellRect, 50 )
			elif cellMatch & IECore.PathMatcher.Result.ExactMatch :
				self.__drawHighlight( painter, cellRect, 200 )

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
		if len( self.__idealColumnWidths ) > index :
			self.__columnWidthAdjustments[index] = newWidth - self.__idealColumnWidths[index]
