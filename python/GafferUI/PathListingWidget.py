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

		# Install an empty model. We'll update the model contents shortly in setPath().

		_GafferUI._pathListingWidgetUpdateModel( GafferUI._qtAddress( self._qtWidget() ), None )
		_GafferUI._pathListingWidgetSetColumns( GafferUI._qtAddress( self._qtWidget() ), columns )

		# Turn off selection in Qt. QItemSelectionModel is full of quadratic performance
		# hazards so we rely entirely on our own PathMatcher instead. We update the PathMatcher
		# directly in `__buttonPress`, `__buttonRelease` and `__keyPress`.

		self._qtWidget().setSelectionMode( QtWidgets.QAbstractItemView.NoSelection )
		self.__allowMultipleSelection = allowMultipleSelection
		self.__lastShiftSelectedIndex = None

		# Set up our various signals.

		self._qtWidget().model().selectionChanged.connect( Gaffer.WeakMethod( self.__selectionChanged ) )
		self._qtWidget().model().expansionChanged.connect( Gaffer.WeakMethod( self.__expansionChanged ) )

		self.__pathSelectedSignal = GafferUI.WidgetSignal()
		self.__selectionChangedSignal = GafferUI.WidgetSignal()
		self.__displayModeChangedSignal = GafferUI.WidgetSignal()
		self.__expansionChangedSignal = GafferUI.WidgetSignal()

		# Connections for implementing selection and drag and drop.
		self.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ), scoped = False )
		self.buttonPressSignal().connect( Gaffer.WeakMethod( self.__buttonPress ), scoped = False )
		self.buttonReleaseSignal().connect( Gaffer.WeakMethod( self.__buttonRelease ), scoped = False )
		self.buttonDoubleClickSignal().connect( Gaffer.WeakMethod( self.__buttonDoubleClick ), scoped = False )
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

	## Sets the currently selected paths using an
	# `IECore.PathMatcher` object.
	def setSelection( self, paths, scrollToFirst=True, expandNonLeaf=True ) :

		assert( isinstance( paths, IECore.PathMatcher ) )
		if not self.__allowMultipleSelection and paths.size() > 1 :
			raise ValueError( "More than one path selected" )

		_GafferUI._pathListingWidgetSetSelection(
			GafferUI._qtAddress( self._qtWidget() ),
			paths, scrollToFirst, expandNonLeaf
		)

	## Returns an `IECore.PathMatcher` object containing
	# the currently selected paths.
	def getSelection( self ) :

		return _GafferUI._pathListingWidgetGetSelection( GafferUI._qtAddress( self._qtWidget() ) )

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

	def __keyPress( self, widget, event ) :

		if event.key in ( "Up", "Down" ) :

			index = self._qtWidget().currentIndex()
			if not index.isValid() :
				return True
			if event.key == "Up" :
				newIndex = self._qtWidget().indexAbove( index )
			else :
				newIndex = self._qtWidget().indexBelow( index )
			if not newIndex.isValid() :
				return True

			newPath = str( self.__pathForIndex( newIndex ) )
			if event.modifiers == event.Modifiers.Shift and self.__allowMultipleSelection :
				selection = self.getSelection()
				selected = selection.match( newPath ) & IECore.PathMatcher.Result.ExactMatch
				if selected :
					selection.removePath( str( self.__pathForIndex( index ) ) )
				else :
					selection.addPath( newPath )
			else :
				selection = IECore.PathMatcher( [ newPath ] )

			self._qtWidget().setCurrentIndex( newIndex )
			self.setSelection( selection, scrollToFirst=False, expandNonLeaf=False )
			return True

		return False

	# Handles interactions for selection and expansion. Done at the level
	# of `GafferUI.Widget` events rather than `QWidget::mousePressEvent()`
	# for compatibility with `GafferUI.Widget.dragBeginSignal()`.
	def __buttonPress( self, widget, event ) :

		self.__updateSelectionInButtonRelease = False
		if event.buttons != event.Buttons.Left :
			return False

		# Get model index under cursor.

		qPoint = self._qtWidget().viewport().mapFrom(
			self._qtWidget(),
			QtCore.QPoint( event.line.p0.x, event.line.p0.y )
		)
		index = self._qtWidget().indexAt( qPoint )
		if not index.isValid() :
			return False

		# Do expansion/collapsing if the arrow was clicked on. QTreeView doesn't
		# expose any queries for the arrow position, but we know it is to the
		# left of the rect used to draw the item.

		if self._qtWidget().model().hasChildren( index ) :
			rect = self._qtWidget().visualRect( index )
			if qPoint.x() < rect.x() and qPoint.x() >= rect.x() - 20 :
				self._qtWidget().setExpanded( index, not self._qtWidget().isExpanded( index ) )
				## \todo It would be more natural to trigger recursive expansion
				# from here rather than `PathModel::treeViewExpanded()`.
				return True

		# Do range selection if Shift is held.

		selection = self.getSelection()

		if event.modifiers & event.Modifiers.Shift and self.__allowMultipleSelection :
			last = self.__lastShiftSelectedIndex
			if last is not None and last.isValid() :
				# Convert from persistent index
				last = QtCore.QModelIndex( last )
			else :
				last = self._qtWidget().currentIndex()

			if last.isValid() and self._qtWidget().currentIndex().isValid() :
				selection.removePaths( self.__pathsForIndexRange( last, self._qtWidget().currentIndex() ) )
				selection.addPaths( self.__pathsForIndexRange( index, self._qtWidget().currentIndex() ) )
				self.setSelection( selection, scrollToFirst=False, expandNonLeaf=False )
				self.__lastShiftSelectedIndex = QtCore.QPersistentModelIndex( index )
				return True
			else :
				# Fall through to regular selection case.
				pass

		self.__lastShiftSelectedIndex = None

		# Toggle item selection if Control is held.

		path = str( self.__pathForIndex( index ) )
		selected = selection.match( path ) & IECore.PathMatcher.Result.ExactMatch

		if event.modifiers & event.Modifiers.Control :
			if selected :
				selection.removePath( path )
			else :
				if not self.__allowMultipleSelection :
					selection.clear()
				selection.addPath( path )
			# Although we're managing our own selection state, we
			# do still update the current index because Qt uses it
			# for doing keyboard-based expansion, and we can make use
			# of if in our Shift-click range selection.
			self._qtWidget().setCurrentIndex( index )
			self.setSelection( selection, scrollToFirst=False, expandNonLeaf=False )
			return True

		# Select item if not already selected.

		if not selected :
			self._qtWidget().setCurrentIndex( index )
			self.setSelection( IECore.PathMatcher( [ path ] ), scrollToFirst=False, expandNonLeaf=False )
			return True

		# The item is selected, Return True so that we have the option of
		# starting a drag if we want. If a drag doesn't follow, we'll adjust
		# selection in `__buttonRelease`.
		self.__updateSelectionInButtonRelease = True

		return True

	def __buttonRelease( self, widget, event ) :

		if not self.__updateSelectionInButtonRelease :
			return False

		qPoint = self._qtWidget().viewport().mapFrom(
			self._qtWidget(),
			QtCore.QPoint( event.line.p0.x, event.line.p0.y )
		)
		index = self._qtWidget().indexAt( qPoint )
		if not index.isValid() :
			return False

		path = self.__pathForIndex( index )
		self._qtWidget().setCurrentIndex( index )
		self.setSelection( IECore.PathMatcher( [ str( path ) ] ), scrollToFirst=False, expandNonLeaf=False )
		return True

	def __buttonDoubleClick( self, widget, event ) :

		if event.buttons != event.Buttons.Left :
			return False

		qPoint = self._qtWidget().viewport().mapFrom(
			self._qtWidget(),
			QtCore.QPoint( event.line.p0.x, event.line.p0.y )
		)
		index = self._qtWidget().indexAt( qPoint )
		if index.isValid() :
			self.__activated( index )
			return True

		return False

	def __mouseMove( self, widget, event ) :

		# Take the event so that the underlying QTreeView doesn't get it.
		return True

	def __dragBegin( self, widget, event ) :

		path = self.pathAt( imath.V2f( event.line.p0.x, event.line.p0.y ) )
		selection = self.getSelection()
		if selection.match( str( path ) ) & IECore.PathMatcher.Result.ExactMatch :
			GafferUI.Pointer.setCurrent( self.__dragPointer )
			return IECore.StringVectorData( selection.paths() )

		return None

	def __dragEnd( self, widget, event ) :

		GafferUI.Pointer.setCurrent( None )

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

		self.__drawSelectionHighlight( painter, option.rect, index )

		QtWidgets.QTreeView.drawRow( self, painter, option, index )

	def drawBranches( self, painter, rect, index ) :

		# Qt has a bug whereby it double-draws the row background in the branch
		# area, once in `drawRow()` and then once in `drawBranches()`. This causes
		# partially-transparent backgrounds to be drawn too heavy. Refill with the
		# default background colour before drawing our highlight and deferring the
		# rest to Qt.
		painter.fillRect( rect, QtGui.QColor( *(_styleColors["backgroundRaised"]) ) )

		self.__drawSelectionHighlight( painter, rect, index )

		QtWidgets.QTreeView.drawBranches( self, painter, rect, index )

	def __drawSelectionHighlight( self, painter, rect, index ) :

		match = index.model().data( index, QtCore.Qt.UserRole )
		if match & IECore.PathMatcher.Result.ExactMatch :
			alpha = 200
		elif match & IECore.PathMatcher.Result.DescendantMatch :
			alpha = 50
		else :
			alpha = None

		if alpha :
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
