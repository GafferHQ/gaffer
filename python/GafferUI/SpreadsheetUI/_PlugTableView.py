##########################################################################
#
#  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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

import functools

import imath

import IECore

import Gaffer
import GafferUI

from GafferUI.PlugValueWidget import sole

from Qt import QtCore
from Qt import QtWidgets
from Qt import QtCompat

from . import _Algo
from . import _ClipboardAlgo
from . import _ProxyModels
from ._CellPlugValueWidget import _CellPlugValueWidget
from ._PlugTableDelegate import _PlugTableDelegate
from ._PlugTableModel import _PlugTableModel
from ._ProxySelectionModel import _ProxySelectionModel
from ._SectionChooser import _SectionChooser

from .._TableView import _TableView

class _PlugTableView( GafferUI.Widget ) :

	Mode = IECore.Enum.create( "RowNames", "Defaults", "Cells" )

	def __init__( self, selectionModel, mode, **kw ) :

		tableView = _NavigableTable()
		GafferUI.Widget.__init__( self, tableView, **kw )

		self.__mode = mode
		self.__setupModels( selectionModel )

		# Headers and column sizing

		QtCompat.setSectionResizeMode( tableView.verticalHeader(), QtWidgets.QHeaderView.Fixed )
		tableView.verticalHeader().setDefaultSectionSize( 25 )
		tableView.verticalHeader().setVisible( False )

		self.__horizontalHeader = GafferUI.Widget( QtWidgets.QHeaderView( QtCore.Qt.Horizontal, tableView ) )
		self.__horizontalHeader._qtWidget().setDefaultAlignment( QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter )
		tableView.setHorizontalHeader( self.__horizontalHeader._qtWidget() )
		self.__horizontalHeader.buttonPressSignal().connect( Gaffer.WeakMethod( self.__headerButtonPress ), scoped = False )

		if mode in ( self.Mode.Cells, self.Mode.Defaults ) :

			self.__applyColumnWidthMetadata()
			self.__applyColumnOrderMetadata()

			tableView.horizontalHeader().sectionResized.connect( Gaffer.WeakMethod( self.__columnResized ) )
			tableView.horizontalHeader().sectionMoved.connect( Gaffer.WeakMethod( self.__columnMoved ) )

			self.__ignoreColumnResized = False
			self.__ignoreColumnMoved = False

		else : # RowNames mode

			if self.__canReorderRows() :
				tableView.verticalHeader().setVisible( True )
				tableView.verticalHeader().sectionMoved.connect( Gaffer.WeakMethod( self.__rowMoved ) )
				self.__ignoreRowMoved = False

			tableView.horizontalHeader().resizeSection( 1, 22 )
			self.__applyRowNamesWidth()
			# Style the row enablers as toggles rather than checkboxes.
			## \todo Do the same for cells containing NameValuePlugs with enablers. This is tricky
			# because we need to do it on a per-cell basis, so will need to use `_CellPlugItemDelegate.paint()`
			# instead.
			tableView.setProperty( "gafferToggleIndicator", True )

		self.__plugMetadataChangedConnection = Gaffer.Metadata.plugValueChangedSignal( tableView.model().rowsPlug().node() ).connect(
			Gaffer.WeakMethod( self.__plugMetadataChanged ), scoped = False
		)
		Gaffer.Metadata.nodeValueChangedSignal().connect( Gaffer.WeakMethod( self.__nodeMetadataChanged ), scoped = False )

		self.dragEnterSignal().connect( Gaffer.WeakMethod( self.__dragEnter ), scoped = False )
		self.dragMoveSignal().connect( Gaffer.WeakMethod( self.__dragMove ), scoped = False )
		self.dragLeaveSignal().connect( Gaffer.WeakMethod( self.__dragLeave ), scoped = False )
		self.dropSignal().connect( Gaffer.WeakMethod( self.__drop ), scoped = False )

		if mode != self.Mode.Defaults :
			tableView.horizontalHeader().setVisible( False )

		self.__applyReadOnlyMetadata()

		# Column visibility

		self.__visibleSection = None
		tableView.model().modelReset.connect( Gaffer.WeakMethod( self.__modelReset ) )

		# Selection and editing. We disable all edit triggers so that
		# the QTableView itself won't edit anything, and we then implement
		# our own editing via PlugValueWidgets in _EditWindow.

		tableView.setEditTriggers( tableView.NoEditTriggers )
		tableView.setSelectionMode( tableView.ExtendedSelection )
		tableView.setSelectionBehavior( tableView.SelectItems )
		self.buttonPressSignal().connect( Gaffer.WeakMethod( self.__buttonPress ), scoped = False )
		self.buttonDoubleClickSignal().connect( Gaffer.WeakMethod( self.__buttonDoubleClick ), scoped = False )
		self.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ), scoped = False )

		# Drawing

		tableView.setItemDelegate( _PlugTableDelegate( tableView ) )

		# Size and scrolling

		tableView.setVerticalScrollBarPolicy( QtCore.Qt.ScrollBarAlwaysOff )
		tableView.setHorizontalScrollBarPolicy( QtCore.Qt.ScrollBarAlwaysOff )
		tableView.setHorizontalScrollMode( tableView.ScrollPerPixel )

		tableView.setSizePolicy(
			QtWidgets.QSizePolicy.Fixed if mode == self.Mode.RowNames else QtWidgets.QSizePolicy.Maximum,
			QtWidgets.QSizePolicy.Fixed if mode == self.Mode.Defaults else QtWidgets.QSizePolicy.Maximum,
		)

	def plugAt( self, position ) :

		point = self._qtWidget().viewport().mapFrom(
			self._qtWidget(),
			QtCore.QPoint( position.x, position.y )
		)
		index = self._qtWidget().indexAt( point )
		return self._qtWidget().model().plugForIndex( index )

	def selectedPlugs( self ) :

		selection = self._qtWidget().selectionModel().selectedIndexes()
		model = self._qtWidget().model()
		return [ model.plugForIndex( i ) for i in selection ]

	def editPlugs( self, plugs, scrollTo = True, allowDirectEditing = True, position = None ) :

		tableView = self._qtWidget()
		selectionModel = tableView.selectionModel()

		indexes = [ tableView.model().indexForPlug( plug ) for plug in plugs ]
		assert( all( [ index.isValid() for index in indexes ] ) )

		if not all( [ index.flags() & ( QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable ) for index in indexes ] ) :
			return

		if scrollTo :
			tableView.scrollTo( indexes[ -1 ] )

		self.__selectIndexes( indexes )

		if position is None :

			visibleRect = tableView.visualRect( selectionModel.currentIndex() )
			rect = QtCore.QRect(
				tableView.viewport().mapToGlobal( visibleRect.topLeft() ),
				tableView.viewport().mapToGlobal( visibleRect.bottomRight() )
			)
			bound = imath.Box2i( imath.V2i( rect.left(), rect.bottom() ), imath.V2i( rect.right(), rect.top() ) )

		else :

			bound = imath.Box2i( position, position )

		self.__showEditor( plugs, bound, allowDirectEditing )

	def setVisibleSection( self, sectionName ) :

		if self.__visibleSection == sectionName :
			return

		self.__visibleSection = sectionName
		self.__applyColumnVisibility()

	def getVisibleSection( self ) :

		return self.__visibleSection

	def __setupModels( self, selectionModel ) :

		tableView = self._qtWidget()

		if self.__mode == self.Mode.RowNames :
			viewProxy = _ProxyModels.RowNamesProxyModel( tableView )
		elif self.__mode == self.Mode.Cells :
			viewProxy = _ProxyModels.CellsProxyModel( tableView )
		else :
			viewProxy = _ProxyModels.DefaultsProxyModel( tableView )

		viewProxy.setSourceModel( selectionModel.model() )
		tableView.setModel( viewProxy )

		selectionProxy = _ProxySelectionModel( viewProxy, selectionModel, tableView )
		tableView.setSelectionModel( selectionProxy )

	def __columnMoved( self, logicalIndex, oldVisualIndex, newVisualIndex ) :

		if self.__ignoreColumnMoved :
			return

		model = self._qtWidget().model()
		header = self._qtWidget().horizontalHeader()

		with Gaffer.UndoScope( model.rowsPlug().ancestor( Gaffer.ScriptNode ) ) :
			with Gaffer.Signals.BlockedConnection( self.__plugMetadataChangedConnection ) :
				for logicalIndex in range( 0, header.count() ) :
					plug = model.plugForIndex( model.index( 0, logicalIndex ) )
					Gaffer.Metadata.registerValue( plug, "spreadsheet:columnIndex", header.visualIndex( logicalIndex ) )

	def __columnResized( self, logicalIndex, oldSize, newSize ) :

		if self.__ignoreColumnResized :
			return

		model = self._qtWidget().model()
		plug = model.plugForIndex( model.index( 0, logicalIndex ) )

		with Gaffer.UndoScope( plug.ancestor( Gaffer.ScriptNode ), mergeGroup = "_PlugTableView{}{}".format( id( self ), logicalIndex ) ) :
			with Gaffer.Signals.BlockedConnection( self.__plugMetadataChangedConnection ) :
				Gaffer.Metadata.registerValue( plug, "spreadsheet:columnWidth", newSize )

	def __applyReadOnlyMetadata( self ) :

		readOnly = Gaffer.MetadataAlgo.readOnly( self._qtWidget().model().rowsPlug() )

		if self.__mode in ( self.Mode.Cells, self.Mode.Defaults ) :

			self._qtWidget().horizontalHeader().setSectionsMovable( not readOnly )
			QtCompat.setSectionResizeMode(
				self._qtWidget().horizontalHeader(),
				QtWidgets.QHeaderView.Fixed if readOnly else QtWidgets.QHeaderView.Interactive
			)

		else :

			# Rows mode
			self._qtWidget().verticalHeader().setSectionsMovable( not readOnly )

	def __applyColumnWidthMetadata( self, cellPlug = None ) :

		if self.__mode == self.Mode.RowNames :
			return

		defaultCells = self._qtWidget().model().rowsPlug().defaultRow()["cells"]

		if cellPlug is not None :
			indicesAndPlugs = [ ( defaultCells.children().index( cellPlug ), cellPlug ) ]
		else :
			indicesAndPlugs = enumerate( defaultCells )

		try :

			self.__ignoreColumnResized = True

			for index, plug in indicesAndPlugs :

				width = Gaffer.Metadata.value( plug, "spreadsheet:columnWidth" )
				if width is None :
					width = self._qtWidget().horizontalHeader().defaultSectionSize()

				self._qtWidget().horizontalHeader().resizeSection( index, width )

		finally :

			self.__ignoreColumnResized = False

	def __applyColumnOrderMetadata( self ) :

		if self.__mode == self.Mode.RowNames :
			return

		rowsPlug = self._qtWidget().model().rowsPlug()
		header = self._qtWidget().horizontalHeader()
		for index, plug in enumerate( rowsPlug.defaultRow()["cells"] ) :
			visualIndex = Gaffer.Metadata.value( plug, "spreadsheet:columnIndex" )
			self.__ignoreColumnMoved = True
			header.moveSection( header.visualIndex( index ), visualIndex if visualIndex is not None else index )
			self.__ignoreColumnMoved = False

	def __applyColumnVisibility( self ) :

		if self.__mode == self.Mode.RowNames :
			return

		# Changing column visibility seems to cause the
		# `sectionResized()` signal to be emitted unnecessarily,
		# so we suppress the slot we've attached to it.
		self.__ignoreColumnResized = True
		try :
			rowsPlug = self._qtWidget().model().rowsPlug()
			for i, plug in enumerate( rowsPlug.defaultRow()["cells"].children() ) :
				if self.__visibleSection is not None :
					visible = _SectionChooser.getSection( plug ) == self.__visibleSection
				else :
					visible = True
				if visible :
					self._qtWidget().showColumn( i )
				else :
					self._qtWidget().hideColumn( i )
		finally :
			self.__ignoreColumnResized = False

	def __canReorderRows( self ) :

		rowsPlug = self._qtWidget().model().rowsPlug()
		if isinstance( rowsPlug.node(), Gaffer.Reference ) :
			reference = rowsPlug.node()
			# Default row (`[0]`) is irrelevant because it is always
			# referenced and we won't try to reorder it anyway.
			for row in rowsPlug.children()[1:] :
				if not reference.isChildEdit( row ) :
					return False

		return True

	def __rowMoved( self, logicalIndex, oldVisualIndex, newVisualIndex ) :

		if self.__ignoreRowMoved :
			return

		# Qt implements row moves as a visual transform on top of the model.
		# We want to implement them as edits to the order of the underlying
		# RowPlugs. So we translate the change in visual transform to a call to
		# `reorderChildren()`, and then reset the visual transform.

		assert( oldVisualIndex == logicalIndex ) # Otherwise a previous visual transform reset failed

		# Reorder rows

		rowsPlug = self._qtWidget().model().rowsPlug()
		rows = list( rowsPlug.children() )
		header = self._qtWidget().verticalHeader()
		assert( len( rows ) == header.count() + 1 ) # Header doesn't know about the default row
		rows = [ rows[0] ] + [ rows[header.logicalIndex(i)+1] for i in range( 0, header.count() ) ]

		with Gaffer.UndoScope( rowsPlug.ancestor( Gaffer.ScriptNode ) ) :
			rowsPlug.reorderChildren( rows )

		# Reset visual transform

		self.__ignoreRowMoved = True
		for i in range( min( oldVisualIndex, newVisualIndex ), max( oldVisualIndex, newVisualIndex ) + 1 ) :
			header.moveSection( header.visualIndex( i ), i )
		self.__ignoreRowMoved = False

	def __applyRowNamesWidth( self ) :

		if self.__mode != self.Mode.RowNames :
			return

		width = self.__getRowNameWidth()
		self._qtWidget().horizontalHeader().resizeSection( 0, width )

	@GafferUI.LazyMethod()
	def __applyColumnOrderLazily( self ) :

		self.__applyColumnOrderMetadata()

	def __nodeMetadataChanged( self, nodeTypeId, key, node ) :

		if Gaffer.MetadataAlgo.readOnlyAffectedByChange( self._qtWidget().model().rowsPlug(), nodeTypeId, key, node ) :
			self.__applyReadOnlyMetadata()

	def __plugMetadataChanged( self, plug, key, reason ) :

		rowsPlug = self._qtWidget().model().rowsPlug()

		if Gaffer.MetadataAlgo.readOnlyAffectedByChange( rowsPlug, plug, key ) :
			self.__applyReadOnlyMetadata()

		if self.__mode == self.Mode.RowNames :

			if plug.isSame( rowsPlug.defaultRow() ) and key == "spreadsheet:rowNameWidth" :
				self.__applyRowNamesWidth()
				return

		else :

			if not rowsPlug.isAncestorOf( plug ) :
				return

			if key == "spreadsheet:columnWidth" :

				if plug.parent() == rowsPlug.defaultRow()["cells"] :
					self.__applyColumnWidthMetadata( cellPlug = plug )

			elif key == "spreadsheet:columnIndex" :

				# Typically we get a flurry of edits to columnIndex at once,
				# so we use a lazy method to update the order once everything
				# has been done.
				self.__applyColumnOrderLazily()

			elif key == "spreadsheet:section" :

				self.__applyColumnVisibility()

	def __dragEnter( self, widget, event ) :

		if Gaffer.MetadataAlgo.readOnly( self._qtWidget().model().rowsPlug() ) :
			return False

		if not isinstance( event.data, ( Gaffer.Plug, IECore.Data ) ) :
			return False

		self.__currentDragDestinationPlug = None
		return True

	def __dragMove( self, widget, event ) :

		destinationPlug = self.plugAt( event.line.p0 )

		if self.__currentDragDestinationPlug == destinationPlug :
			return

		self.__currentDragDestinationPlug = destinationPlug

		selectionModel = self._qtWidget().selectionModel()
		selectionModel.clear()

		if destinationPlug is None:
			return

		select = False
		if isinstance( event.data, IECore.Data ) :
			select = _ClipboardAlgo.canPasteCells( event.data, [ [ destinationPlug ] ] )
		else :
			sourcePlug, targetPlug = self.__connectionPlugs( event.data, destinationPlug )
			select = self.__canConnect( sourcePlug, targetPlug )

		if select :
			selectionModel.select(
				self._qtWidget().model().indexForPlug( destinationPlug ),
				QtCore.QItemSelectionModel.SelectCurrent
			)

	def __dragLeave( self, widget, event ) :

		self.__currentDragDestinationPlug = None
		self._qtWidget().selectionModel().clear()

	def __drop( self, widget, event ) :

		self.__currentDragDestinationPlug = None

		destinationPlug = self.plugAt( event.line.p0 )

		if isinstance( event.data, IECore.Data ) :
			if not _ClipboardAlgo.canPasteCells( event.data, [ [ destinationPlug ] ] ) :
				return False
			with Gaffer.UndoScope( destinationPlug.ancestor( Gaffer.ScriptNode ) ) :
				context = self.ancestor( GafferUI.PlugValueWidget ).getContext()
				_ClipboardAlgo.pasteCells( event.data, [ [ destinationPlug ] ], context.getTime() )
		else :
			sourcePlug, targetPlug = self.__connectionPlugs( event.data, destinationPlug )
			if not self.__canConnect( sourcePlug, targetPlug ) :
				return False
			with Gaffer.UndoScope( targetPlug.ancestor( Gaffer.ScriptNode ) ) :
				targetPlug.setInput( sourcePlug )

		index = self._qtWidget().model().indexForPlug( destinationPlug )
		selectionModel = self._qtWidget().selectionModel()
		selectionModel.select( index, QtCore.QItemSelectionModel.ClearAndSelect )
		selectionModel.setCurrentIndex( index, QtCore.QItemSelectionModel.ClearAndSelect )

		# People regularly have spreadsheets in separate windows. Ensure the
		# sheet has focus after drop has concluded. It will have returned to
		# the origin of the drag.
		def focusOnIdle() :
			if not self._qtWidget().isActiveWindow() :
				self._qtWidget().activateWindow()
			self._qtWidget().setFocus()
			return False

		GafferUI.EventLoop.addIdleCallback( focusOnIdle )
		return True

	def __connectionPlugs( self, sourcePlug, targetPlug ) :

		if isinstance( targetPlug, Gaffer.Spreadsheet.CellPlug ) :
			targetPlug = targetPlug[ "value" ]

		if isinstance( targetPlug, Gaffer.NameValuePlug ) :
			if not isinstance( sourcePlug, Gaffer.NameValuePlug ) :
				targetPlug = targetPlug[ "value" ]
		else :
			if isinstance( sourcePlug, Gaffer.NameValuePlug ) :
				sourcePlug = sourcePlug[ "value" ]

		return sourcePlug, targetPlug

	def __canConnect( self, sourcePlug, targetPlug ) :

		if targetPlug is None :
			return False

		if Gaffer.MetadataAlgo.readOnly( targetPlug ) :
			return False

		if any( Gaffer.MetadataAlgo.getReadOnly( p ) for p in Gaffer.Plug.RecursiveRange( targetPlug ) ) :
			return False

		with self.ancestor( GafferUI.PlugValueWidget ).getContext() :
			if not targetPlug.ancestor( Gaffer.Spreadsheet.RowPlug )["enabled"].getValue() :
				return False

		if not targetPlug.acceptsInput( sourcePlug ) :
			return False

		return True

	def __positionInCellGrid( self, position ) :

		# The event coordinate origin includes the header view.
		# Queries to indexAt etc... need the origin to be in the
		# table view itself.

		cellPosition = imath.V3f( position )

		if self._qtWidget().verticalHeader().isVisible() :
			cellPosition.x -= self._qtWidget().verticalHeader().frameRect().width()
		if self._qtWidget().horizontalHeader().isVisible() :
			cellPosition.y -= self._qtWidget().horizontalHeader().frameRect().height()

		return cellPosition

	def __buttonPress( self, widget, event ) :

		if event.buttons != event.Buttons.Right :
			return False

		point = self._qtWidget().viewport().mapFrom(
			self._qtWidget(),
			QtCore.QPoint( event.line.p0.x, event.line.p0.y )
		)
		index = self._qtWidget().indexAt( point )

		# Disabled items won't show up in the selection model
		if not index.flags() & QtCore.Qt.ItemIsEnabled :
			return True

		# Ensure the cell that was clicked is selected. This avoids any ambiguity
		# as to whether the menu is operating on the cell that was right-clicked, or
		# the cells that are selected. As double-click to edit also resets selection
		# (Qt default) then this offers the most consistent experience.
		selectionModel = self._qtWidget().selectionModel()
		if not selectionModel.isSelected( index ) :
			selectionModel.select( index, selectionModel.ClearAndSelect )

		selectedPlugs = self.selectedPlugs()

		if len( selectedPlugs ) == 1 :

			plug = next( iter( selectedPlugs ) )
			if isinstance( plug, Gaffer.Spreadsheet.CellPlug ) :
				plug = plug["value"]

			## \todo We need to make this temporary PlugValueWidget just so we
			# can show a plug menu. We should probably refactor so we can do it
			# without the widget, but this would touch `PlugValueWidget.popupMenuSignal()`
			# and all connected client code.
			self.__menuPlugValueWidget = GafferUI.PlugValueWidget.create( plug )
			definition = self.__menuPlugValueWidget._popupMenuDefinition()

		else :

			definition = IECore.MenuDefinition()

		if self.__mode == self.Mode.RowNames :
			self.__prependRowMenuItems( definition, selectedPlugs )
		else :
			self.__prependCellMenuItems( definition, selectedPlugs )

		self.__plugMenu = GafferUI.Menu( definition )
		self.__plugMenu.popup()

		return True

	def __buttonDoubleClick( self, widget, event ) :

		if event.buttons != event.Buttons.Left :
			return False

		# Consistency is a little tricky here. Ideally we'd have the same
		# interaction for all plug types, without adding unnecessary steps. We
		# standardise 'return/double click opens edit window'. But in the
		# interest of simplifying common steps, there are the following
		# exceptions.
		#
		#  - Bools: Return/double-click toggles the value. Requires right-click
		#    to display the edit window.
		#
		#  - Presets: Return/Double click displays the popup menu, requires right-click
		#    to display the edit window.

		point = self._qtWidget().viewport().mapFrom(
			self._qtWidget(),
			QtCore.QPoint( event.line.p0.x, event.line.p0.y )
		)
		index = self._qtWidget().indexAt( point )

		if not index.flags() & QtCore.Qt.ItemIsEnabled :
			return True

		plug = self._qtWidget().model().plugForIndex( index )
		if plug is None :
			return False

		if self._qtWidget().model().presentsCheckstate( index ) :
			valuePlug = plug["value"] if isinstance( plug, Gaffer.Spreadsheet.CellPlug ) else plug
			self.__toggleBooleans( [ valuePlug ] )
		else :
			self.editPlugs( [ plug ], scrollTo = False, position = GafferUI.Widget.mousePosition() )

		return True

	def __keyPress( self, widget, event ) :

		forRows = self.__mode == self.Mode.RowNames

		if event.key == "Space" :
			self.__spaceBarPressed()
			return True

		if event.modifiers == event.Modifiers.None_ :

			if event.key == "Return" :
				self.__returnKeyPress()
				return True

			if event.key == "D" :
				# We don't have a shortcut for managing the enabled state of rows, because when a
				# row is disabled (via Qt.ItemIsEnabled flag), those indices are no longer reported
				# from the selection model. So you could use the key to turn them off, but its
				# hard to turn them back on again with it.
				if not forRows :
					self.__toggleCellEnabledState()
				return True

		elif event.modifiers == event.Modifiers.Control :

			if event.key in ( "C", "V", "X" ) :

				if event.key == "C" :
					self.__copyRows() if forRows else self.__copyCells()
				elif event.key == "V" :
					self.__pasteRows() if forRows else self.__pasteCells()

				return True

		return False

	def __returnKeyPress( self ) :

		# If the selection is presented as a checkbox, toggle rather than
		# opening the edit window.  This matches the single-click toggle mouse
		# interaction.

		selectionModel = self._qtWidget().selectionModel()
		selectedIndexes = selectionModel.selectedIndexes()

		if not selectedIndexes :
			return

		model = selectionModel.model()
		if all( [ model.presentsCheckstate( i ) for i in selectedIndexes ] ) :
			valuePlugs = [ model.valuePlugForIndex( i ) for i in selectedIndexes ]
			self.__toggleBooleans( valuePlugs )
		else :
			self.__editSelectedPlugs()

	def __spaceBarPressed( self ) :

		# Qt has the odd behaviour that space will toggle the selection of the
		# focused cell, unless it has a checked state, and then it'll toggle
		# that. As we support `return` to do that, then make sure space only
		# ever toggles the selection state of the focused cell.
		currentIndex = self._qtWidget().selectionModel().currentIndex()
		if currentIndex.isValid() :
			self._qtWidget().selectionModel().select( currentIndex, QtCore.QItemSelectionModel.Toggle )

	def __headerButtonPress( self, header, event ) :

		if event.buttons != event.Buttons.Right :
			return False

		column = self._qtWidget().columnAt( event.line.p0.x )
		cellPlug = self._qtWidget().model().plugForIndex( self._qtWidget().model().index( 0, column ) )
		assert( cellPlug.ancestor( Gaffer.Spreadsheet.RowPlug ) == cellPlug.ancestor( Gaffer.Spreadsheet.RowsPlug ).defaultRow() )

		menuDefinition = IECore.MenuDefinition()
		menuDefinition.append(
			"/Set Label...",
			{
				"command" : functools.partial( Gaffer.WeakMethod( self.__setColumnLabel ), cellPlug ),
				"active" : not Gaffer.MetadataAlgo.readOnly( cellPlug ),
			}
		)

		menuDefinition.append(
			"/Set Description...",
			{
				"command" : functools.partial( Gaffer.WeakMethod( self.__setColumnDescription ), cellPlug ),
				"active" : not Gaffer.MetadataAlgo.readOnly( cellPlug ),
			}
		)

		sectionNames = _SectionChooser.sectionNames( self._qtWidget().model().rowsPlug() )
		currentSection = _SectionChooser.getSection( cellPlug )
		for sectionName in sectionNames :
			menuDefinition.append(
				"/Move to Section/{}".format( sectionName ),
				{
					"command" : functools.partial( Gaffer.WeakMethod( self.__moveToSection ), cellPlug, sectionName = sectionName ),
					"active" : not Gaffer.MetadataAlgo.readOnly( cellPlug ) and sectionName != currentSection,
				}
			)

		if sectionNames :
			menuDefinition.append( "/Move to Section/__divider__", { "divider" : True } )

		menuDefinition.append(
			"/Move to Section/New...",
			{
				"command" : functools.partial( Gaffer.WeakMethod( self.__moveToSection ), cellPlug ),
				"active" : not Gaffer.MetadataAlgo.readOnly( cellPlug ),
			}
		)

		menuDefinition.append( "/DeleteDivider", { "divider" : True } )

		menuDefinition.append(
			"/Delete Column",
			{
				"command" : functools.partial( Gaffer.WeakMethod( self.__deleteColumn ), cellPlug ),
				"active" : self.__canDeleteColumn( cellPlug )
			}
		)

		self.__headerMenu = GafferUI.Menu( menuDefinition )
		self.__headerMenu.popup()

		return True

	def __prependRowMenuItems( self, menuDefinition, plugs ) :

		rowPlugs = { p.ancestor( Gaffer.Spreadsheet.RowPlug ) for p in plugs }

		pluralSuffix = "" if len( rowPlugs ) == 1 else "s"

		targetDivider = "/__SpreadsheetRowAndCellDivider__"
		if menuDefinition.item( targetDivider ) is None :
			menuDefinition.prepend( targetDivider, { "divider" : True } )

		items = []

		rowsPlug = next( iter( rowPlugs ) ).ancestor( Gaffer.Spreadsheet.RowsPlug )

		widths = [
			( "Half", GafferUI.PlugWidget.labelWidth() * 0.5 ),
			( "Single", GafferUI.PlugWidget.labelWidth() ),
			( "Double", GafferUI.PlugWidget.labelWidth() * 2 ),
		]

		currentWidth = self.__getRowNameWidth()
		for label, width in widths :
			items.append( (
				"/Width/{}".format( label ),
				{
					"command" : functools.partial( Gaffer.WeakMethod( self.__setRowNameWidth ), width ),
					"active" : not Gaffer.MetadataAlgo.readOnly( rowsPlug ),
					"checkBox" : width == currentWidth,
				}
			) )

		clipboard = self.__getClipboard()
		pasteRowsPluralSuffix = "" if _ClipboardAlgo.isValueMatrix( clipboard ) and len( clipboard ) == 1 else "s"

		canChangeEnabledState, currentEnabledState = self.__canChangeRowEnabledState( rowPlugs )
		enabledPlugs = [ row["enabled"] for row in rowPlugs ]

		items.extend( (
			(
				"/__DisableRowsDivider__", { "divider" : True }
			),
			(
				( "/Disable Row%s" if currentEnabledState else "/Enable Row%s" ) % pluralSuffix,
				{
					"command" : functools.partial( Gaffer.WeakMethod( self.__setRowEnabledState ), enabledPlugs, not currentEnabledState ),
					"active" : canChangeEnabledState
				}
			),
			(
				"/__CopyPasteRowsDivider__", { "divider" : True }
			),
			(
				"Copy Row%s" % pluralSuffix,
				{
					"command" : Gaffer.WeakMethod( self.__copyRows ),
					"shortCut" : "Ctrl+C"
				}
			),
			(
				"Paste Row%s" % pasteRowsPluralSuffix,
				{
					"command" : Gaffer.WeakMethod( self.__pasteRows ),
					"active" : _ClipboardAlgo.canPasteRows( self.__getClipboard(), rowsPlug ),
					"shortCut" : "Ctrl+V"
				}
			),
			(
				"/__DeleteRowDivider__", { "divider" : True }
			),
			(
				"/Delete Row%s" % pluralSuffix,
				{
					"command" : functools.partial( Gaffer.WeakMethod( self.__deleteRows ), rowPlugs ),
					"active" : self.__canDeleteRows( rowPlugs )
				}
			)
		) )

		for path, args in reversed( items ) :
			menuDefinition.prepend( path, args )

	def __prependCellMenuItems( self, menuDefinition, cellPlugs ) :

		targetDivider = "/__SpreadsheetRowAndCellDivider__"
		if menuDefinition.item( targetDivider ) is None :
			menuDefinition.prepend( targetDivider, { "divider" : True } )

		pluralSuffix = "" if len( cellPlugs ) == 1 else "s"

		canChangeEnabledState, currentEnabledState = self.__canChangeCellEnabledState( cellPlugs )
		enabledPlugs = [ cell.enabledPlug() for cell in cellPlugs ]

		plugMatrix = _ClipboardAlgo.createPlugMatrixFromCells( cellPlugs )

		items = [
			(
				( "/Disable Cell%s" if currentEnabledState else "/Enable Cell%s" ) % pluralSuffix,
				{
					"command" : functools.partial( Gaffer.WeakMethod( self.__setPlugValues ), enabledPlugs, not currentEnabledState ),
					"active" : canChangeEnabledState,
					"shortCut" : "D"
				}
			),

			( "/__EditCellsDivider__", { "divider" : True } ),

			(
				"/Edit Cell%s" % pluralSuffix,
				{
					"active" : _CellPlugValueWidget.canEdit( cellPlugs ),
					"command" : functools.partial( Gaffer.WeakMethod( self.__editSelectedPlugs ), False )
				}
			),

			( "/__CopyPasteCellsDivider__", { "divider" : True } ),

			(
				"Copy Cell%s" % pluralSuffix,
				{
					"command" : Gaffer.WeakMethod( self.__copyCells ),
					"active" : _ClipboardAlgo.canCopyPlugs( plugMatrix ),
					"shortCut" : "Ctrl+C"
				}
			),
			(
				"Paste Cell%s" % pluralSuffix,
				{
					"command" : Gaffer.WeakMethod( self.__pasteCells ),
					"active" : _ClipboardAlgo.canPasteCells( self.__getClipboard(), plugMatrix ),
					"shortCut" : "Ctrl+V"
				}
			)
		]

		for path, args in reversed( items ) :
			menuDefinition.prepend( path, args )

	def __getClipboard( self ) :

		appRoot = self._qtWidget().model().rowsPlug().ancestor( Gaffer.ApplicationRoot )
		return appRoot.getClipboardContents()

	def __setClipboard( self, data ) :

		appRoot = self._qtWidget().model().rowsPlug().ancestor( Gaffer.ApplicationRoot )
		return appRoot.setClipboardContents( data )

	def __copyCells( self ) :

		selection = self.selectedPlugs()
		plugMatrix = _ClipboardAlgo.createPlugMatrixFromCells( selection )

		if not plugMatrix or not _ClipboardAlgo.canCopyPlugs( plugMatrix ) :
			return

		with self.ancestor( GafferUI.PlugValueWidget ).getContext() :
			clipboardData = _ClipboardAlgo.valueMatrix( plugMatrix )

		self.__setClipboard( clipboardData )

	def __pasteCells( self ) :

		plugMatrix = _ClipboardAlgo.createPlugMatrixFromCells( self.selectedPlugs() )
		clipboard = self.__getClipboard()

		if not plugMatrix or not _ClipboardAlgo.canPasteCells( clipboard, plugMatrix ) :
			return

		context = self.ancestor( GafferUI.PlugValueWidget ).getContext()
		with Gaffer.UndoScope( plugMatrix[0][0].ancestor( Gaffer.ScriptNode ) ) :
			_ClipboardAlgo.pasteCells( clipboard, plugMatrix, context.getTime() )

	def __copyRows( self ) :

		rowPlugs = _PlugTableView.__orderedRowsPlugs( self.selectedPlugs() )

		with self.ancestor( GafferUI.PlugValueWidget ).getContext() :
			clipboardData = _ClipboardAlgo.copyRows( rowPlugs )

		self.__setClipboard( clipboardData )

	def __pasteRows( self ) :

		rowsPlug = self._qtWidget().model().rowsPlug()
		clipboard = self.__getClipboard()

		if not _ClipboardAlgo.canPasteRows( clipboard, rowsPlug ) :
			return

		with Gaffer.UndoScope( rowsPlug.ancestor( Gaffer.ScriptNode ) ) :
			_ClipboardAlgo.pasteRows( clipboard, rowsPlug )

	def __setRowNameWidth( self, width, *unused ) :

		rowsPlug = self._qtWidget().model().rowsPlug()

		with Gaffer.UndoScope( rowsPlug.ancestor( Gaffer.ScriptNode ) ) :
			Gaffer.Metadata.registerValue( rowsPlug.defaultRow(), "spreadsheet:rowNameWidth", width )

	def __getRowNameWidth( self ) :

		rowsPlug = self._qtWidget().model().rowsPlug()

		width = Gaffer.Metadata.value( rowsPlug.defaultRow(), "spreadsheet:rowNameWidth" )
		return width if width is not None else GafferUI.PlugWidget.labelWidth()

	def __editSelectedPlugs( self, allowDirectEditing = True ) :

		selectedPlugs = self.selectedPlugs()

		if self.__mode == self.Mode.RowNames :
			# Multi-editing row names makes no sense, so pick the first one.
			# It will also be muddled up with the value cells.
			rows = _PlugTableView.__orderedRowsPlugs( selectedPlugs )
			selectedPlugs = { rows[0]["name"] }

		self.editPlugs( selectedPlugs, allowDirectEditing = allowDirectEditing )

	def __showEditor( self, plugs, plugBound, allowDirectEditing ) :

		self.__editorWidget = None

		if allowDirectEditing :
			# Show a presets menu directly to avoid an unnecessary interaction step
			# This sadly leaks the widget, but there isn't a lot we can do at present.
			plugValueWidget = GafferUI.PlugValueWidget.create( plugs )
			if isinstance( plugValueWidget, _CellPlugValueWidget ) :
				valuePlugValueWidget = plugValueWidget.childPlugValueWidget( next( iter( plugs ) )["value"] )
				if isinstance( valuePlugValueWidget, GafferUI.PresetsPlugValueWidget ) :
					if not Gaffer.Metadata.value( next( iter( valuePlugValueWidget.getPlugs() ) ), "presetsPlugValueWidget:isCustom" ) :
						self.__editorWidget = plugValueWidget
						valuePlugValueWidget.menu().popup( position = plugBound.center() )
						return

		self.__editorWidget = GafferUI.PlugPopup( plugs, title = "" )
		self.__editorWidget.popup( plugBound.center() )

	# Clears and selects a non-contiguous list of indexes if they're not already selected.
	def __selectIndexes( self, indexes ) :

		selectionModel = self._qtWidget().selectionModel()

		if set( selectionModel.selectedIndexes() ) != set( indexes ) :
			selection = QtCore.QItemSelection()
			for index in indexes :
				selection.select( index, index )
			selectionModel.select( selection, QtCore.QItemSelectionModel.ClearAndSelect )

		if not selectionModel.isSelected( selectionModel.currentIndex() ) :
			selectionModel.setCurrentIndex( indexes[ -1 ], QtCore.QItemSelectionModel.ClearAndSelect )

	def __setColumnLabel( self, cellPlug ) :

		label = GafferUI.TextInputDialogue(
			title = "Set Label",
			confirmLabel = "Set",
			initialText = Gaffer.Metadata.value( cellPlug, "spreadsheet:columnLabel" ) or cellPlug.getName()
		).waitForText( parentWindow = self.ancestor( GafferUI.Window ) )

		if label is not None :
			with Gaffer.UndoScope( cellPlug.ancestor( Gaffer.ScriptNode ) ) :
				Gaffer.Metadata.registerValue( cellPlug, "spreadsheet:columnLabel", label )

	def __setColumnDescription( self, cellPlug ) :

		description = GafferUI.TextInputDialogue(
			title = "Set Description",
			confirmLabel = "Set",
			initialText = Gaffer.Metadata.value( cellPlug["value"], "description" ) or "",
			multiLine = True,
		).waitForText( parentWindow = self.ancestor( GafferUI.Window ) )

		if description is not None :
			with Gaffer.UndoScope( cellPlug.ancestor( Gaffer.ScriptNode ) ) :
				Gaffer.Metadata.registerValue( cellPlug["value"], "description", description )

	def __canDeleteColumn( self, cellPlug ) :

		if Gaffer.MetadataAlgo.readOnly( cellPlug ) :
			return False
		if isinstance( cellPlug.node(), Gaffer.Reference ) :
			return False

		return True

	def __deleteColumn( self, cellPlug ) :

		rowsPlug = cellPlug.ancestor( Gaffer.Spreadsheet.RowsPlug )
		with Gaffer.UndoScope( rowsPlug.ancestor( Gaffer.ScriptNode ) ) :
			rowsPlug.removeColumn( cellPlug.parent().children().index( cellPlug ) )

	def __canDeleteRows( self, rowPlugs ) :

		if not rowPlugs :
			return False

		rowsPlug = next( iter( rowPlugs ) ).ancestor( Gaffer.Spreadsheet.RowsPlug )
		if rowsPlug.defaultRow() in rowPlugs :
			return False
		if any( [ Gaffer.MetadataAlgo.readOnly( row ) for row in rowPlugs ] ) :
			return False
		if isinstance( rowsPlug.node(), Gaffer.Reference ) :
			# Can't delete rows unless they have been added as edits
			# on top of the reference. Otherwise they will be recreated
			# when the reference is reloaded anyway.
			reference = rowsPlug.node()
			for row in rowPlugs :
				if not reference.isChildEdit( row ) :
					return False

		return True

	def __deleteRows( self, rowPlugs ) :

		with Gaffer.UndoScope( next( iter( rowPlugs ) ).ancestor( Gaffer.ScriptNode ) ) :
			for row in rowPlugs :
				row.parent().removeChild( row )

	def __canChangeRowEnabledState( self, rowPlugs ) :

		enabledPlugs = [ row["enabled"] for row in rowPlugs ]
		return self.__canChangeEnabledState( enabledPlugs )

	def __setRowEnabledState( self, enabledPlugs, enabled ) :

		self.__setPlugValues( enabledPlugs, enabled )

		# Clear the row name column selection if rows have been disabled.
		# They don't show up in selectionModel.selection().
		if not enabled :
			selectionModel = self._qtWidget().selectionModel()
			nameColumnIndex = self._qtWidget().model().index( 0, 0 )
			flags = QtCore.QItemSelectionModel.Columns | QtCore.QItemSelectionModel.Deselect
			selectionModel.select( nameColumnIndex, flags )
			if selectionModel.currentIndex().column() == 0 :
				selectionModel.clearCurrentIndex()

	def __canChangeCellEnabledState( self, cellPlugs ) :

		enabledPlugs = [ cell.enabledPlug() for cell in cellPlugs ]
		allSettable, enabled = self.__canChangeEnabledState( enabledPlugs )
		return ( _Algo.cellsCanBeDisabled( cellPlugs ) and allSettable, enabled )

	def __canChangeEnabledState( self, enabledPlugs ) :

		anyReadOnly = any( [ Gaffer.MetadataAlgo.readOnly( plug ) for plug in enabledPlugs ] )
		allSettable = all( [ plug.settable() for plug in enabledPlugs ] )

		enabled = True
		with self.ancestor( GafferUI.PlugValueWidget ).getContext() :
			with IECore.IgnoredExceptions( Gaffer.ProcessException ) :
				enabled = all( [ plug.getValue() for plug in enabledPlugs ] )

		return ( allSettable and not anyReadOnly, enabled )

	def __toggleBooleans( self, plugs ) :

		if not plugs or any( Gaffer.MetadataAlgo.readOnly( p ) for p in plugs ) :
			return

		with self.ancestor( GafferUI.PlugValueWidget ).getContext() :
			checked = sole( [ plug.getValue() for plug in plugs ] )
		with Gaffer.UndoScope( next( iter( plugs ) ).ancestor( Gaffer.ScriptNode ) ) :
			self.__setPlugValues( plugs, not checked )

	def __toggleCellEnabledState( self ) :

		cellPlugs = [ p for p in self.selectedPlugs() if isinstance( p, Gaffer.Spreadsheet.CellPlug ) ]

		canChange, currentState = self.__canChangeCellEnabledState( cellPlugs )
		if not canChange :
			return

		self.__setPlugValues( [ cell.enabledPlug() for cell in cellPlugs ], not currentState )

	def __setPlugValues( self, plugs, value ) :

		with Gaffer.UndoScope( next( iter( plugs ) ).ancestor( Gaffer.ScriptNode ) ) :
			for plug in plugs :
				plug.setValue( value )

	def __modelReset( self ) :

		self.__applyColumnVisibility()
		self.__applyColumnWidthMetadata()
		self.__applyRowNamesWidth()

	def __moveToSection( self, cellPlug, sectionName = None ) :

		if sectionName is None :
			sectionName = GafferUI.TextInputDialogue(
				initialText = "New Section",
				title = "Move to Section",
				confirmLabel = "Move"
			).waitForText( parentWindow = self.ancestor( GafferUI.Window ) )

		if not sectionName :
			return

		with Gaffer.UndoScope( cellPlug.ancestor( Gaffer.ScriptNode ) ) :
			_SectionChooser.setSection( cellPlug, sectionName )

	@staticmethod
	def __orderedRowsPlugs( plugs ) :

		rowPlugs = { p.ancestor( Gaffer.Spreadsheet.RowPlug ) for p in plugs }
		if rowPlugs :
			allRows = next( iter( rowPlugs ) ).parent().children()
			return sorted( rowPlugs, key = allRows.index )

		return []

# Ensures navigation key presses aren't stolen by any application-level actions.
class _NavigableTable( _TableView ) :

	__protectedKeys = (
		QtCore.Qt.Key_Left,
		QtCore.Qt.Key_Right,
		QtCore.Qt.Key_Up,
		QtCore.Qt.Key_Down
	)

	def event( self, event ) :

		if event.type() == QtCore.QEvent.ShortcutOverride and event.key() in self.__protectedKeys :
			event.accept()
			return True
		else :
			return _TableView.event( self, event )
