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

from Qt import QtCore
from Qt import QtWidgets
from Qt import QtCompat

from . import _Algo
from . import _Clipboard
from . import _ProxyModels
from ._EditWindow import _EditWindow
from ._PlugTableDelegate import _PlugTableDelegate
from ._PlugTableModel import _PlugTableModel
from ._ProxySelectionModel import _ProxySelectionModel
from ._SectionChooser import _SectionChooser

from .._TableView import _TableView

class _PlugTableView( GafferUI.Widget ) :

	Mode = IECore.Enum.create( "RowNames", "Defaults", "Cells" )

	def __init__( self, sharedSelectionModel, mode, **kw ) :

		tableView = _TableView()
		GafferUI.Widget.__init__( self, tableView, **kw )

		self.__mode = mode;

		self.__setupModels( mode, sharedSelectionModel )

		# Headers and column sizing

		QtCompat.setSectionResizeMode( tableView.verticalHeader(), QtWidgets.QHeaderView.Fixed )
		tableView.verticalHeader().setDefaultSectionSize( 25 )
		tableView.verticalHeader().setVisible( False )

		self.__horizontalHeader = GafferUI.Widget( QtWidgets.QHeaderView( QtCore.Qt.Horizontal, tableView ) )
		self.__horizontalHeader._qtWidget().setDefaultAlignment( QtCore.Qt.AlignLeft )
		tableView.setHorizontalHeader( self.__horizontalHeader._qtWidget() )
		self.__horizontalHeader.buttonPressSignal().connect( Gaffer.WeakMethod( self.__headerButtonPress ), scoped = False )

		if mode in ( self.Mode.Cells, self.Mode.Defaults ) :

			self.__applyColumnWidthMetadata()
			self.__applySectionOrderMetadata()

			tableView.horizontalHeader().setSectionsMovable( True )
			tableView.horizontalHeader().sectionResized.connect( Gaffer.WeakMethod( self.__sectionResized ) )
			tableView.horizontalHeader().sectionMoved.connect( Gaffer.WeakMethod( self.__sectionMoved ) )

			self.__ignoreSectionResized = False
			self.__callingMoveSection = False

			self.__plugMetadataChangedConnection = Gaffer.Metadata.plugValueChangedSignal().connect(
				Gaffer.WeakMethod( self.__plugMetadataChanged ), scoped = False
			)

		else : # RowNames mode

			tableView.horizontalHeader().resizeSection( 1, 22 )
			tableView.horizontalHeader().setSectionResizeMode( 0, QtWidgets.QHeaderView.Stretch )
			# Style the row enablers as toggles rather than checkboxes.
			## \todo Do the same for cells containing NameValuePlugs with enablers. This is tricky
			# because we need to do it on a per-cell basis, so will need to use `_CellPlugItemDelegate.paint()`
			# instead.
			tableView.setProperty( "gafferToggleIndicator", True )

		if mode != self.Mode.Defaults :
			tableView.horizontalHeader().setVisible( False )

		# Column visibility

		self.__visibleSection = None
		tableView.model().modelReset.connect( Gaffer.WeakMethod( self.__modelReset ) )

		# Selection and editing. We disable all edit triggers so that
		# the QTableView itself won't edit anything, and we then implement
		# our own editing via PlugValueWidgets in _EditWindow.

		tableView.setEditTriggers( tableView.NoEditTriggers )
		tableView.setSelectionMode( tableView.ExtendedSelection )
		tableView.setSelectionBehavior( tableView.SelectRows if mode == self.Mode.RowNames else tableView.SelectItems )
		self.buttonPressSignal().connect( Gaffer.WeakMethod( self.__buttonPress ), scoped = False )
		self.buttonDoubleClickSignal().connect( Gaffer.WeakMethod( self.__buttonDoubleClick ), scoped = False )

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

		index = self._qtWidget().indexAt( QtCore.QPoint( position.x, position.y ) )
		return self._qtWidget().model().plugForIndex( index )

	def selectedPlugs( self ) :

		selection = self._qtWidget().selectionModel().selectedIndexes()
		model = self._qtWidget().model()
		return { model.plugForIndex( i ) for i in selection }

	def editPlug( self, plug, scrollTo = True ) :

		index = self._qtWidget().model().indexForPlug( plug )
		assert( index.isValid() )

		if not index.flags() & QtCore.Qt.ItemIsEnabled or not index.flags() & QtCore.Qt.ItemIsEditable :
			return

		if scrollTo :
			self._qtWidget().scrollTo( index )

		rect = self._qtWidget().visualRect( index )
		rect.setTopLeft( self._qtWidget().viewport().mapToGlobal( rect.topLeft() ) )
		rect.setBottomRight( self._qtWidget().viewport().mapToGlobal( rect.bottomRight() ) )

		_EditWindow.popupEditor(
			plug,
			imath.Box2i(
				imath.V2i( rect.left(), rect.bottom() ),
				imath.V2i( rect.right(), rect.top() )
			)
		)

	def setVisibleSection( self, sectionName ) :

		if self.__visibleSection == sectionName :
			return

		self.__visibleSection = sectionName
		self.__applyColumnVisibility()

	def getVisibleSection( self ) :

		return self.__visibleSection

	def __setupModels( self, mode, sharedSelectionModel ) :

		if mode == self.Mode.RowNames :
			proxy = _ProxyModels.RowNamesProxyModel
		elif mode == self.Mode.Cells :
			proxy = _ProxyModels.CellsProxyModel
		else :
			proxy = _ProxyModels.DefaultsProxyModel

		tableView = self._qtWidget()

		viewProxy = proxy( tableView )
		viewProxy.setSourceModel( sharedSelectionModel.model() )

		selectionProxy = _ProxySelectionModel( viewProxy, sharedSelectionModel, tableView )

		tableView.setModel( viewProxy )
		tableView.setSelectionModel( selectionProxy )

	def __sectionMoved( self, logicalIndex, oldVisualIndex, newVisualIndex ) :

		if self.__callingMoveSection :
			return

		model = self._qtWidget().model()
		header = self._qtWidget().horizontalHeader()

		with Gaffer.UndoScope( model.rowsPlug().ancestor( Gaffer.ScriptNode ) ) :
			with Gaffer.BlockedConnection( self.__plugMetadataChangedConnection ) :
				for logicalIndex in range( 0, header.count() ) :
					plug = model.plugForIndex( model.index( 0, logicalIndex ) )
					Gaffer.Metadata.registerValue( plug, "spreadsheet:columnIndex", header.visualIndex( logicalIndex ) )

	def __sectionResized( self, logicalIndex, oldSize, newSize ) :

		if self.__ignoreSectionResized :
			return

		model = self._qtWidget().model()
		plug = model.plugForIndex( model.index( 0, logicalIndex ) )

		with Gaffer.UndoScope( plug.ancestor( Gaffer.ScriptNode ), mergeGroup = "_PlugTableView{}{}".format( id( self ), logicalIndex ) ) :
			with Gaffer.BlockedConnection( self.__plugMetadataChangedConnection ) :
				Gaffer.Metadata.registerValue( plug, "spreadsheet:columnWidth", newSize )

	def __applyColumnWidthMetadata( self, cellPlug = None ) :

		if self.__mode == self.Mode.RowNames :
			return

		defaultCells = self._qtWidget().model().rowsPlug().defaultRow()["cells"]

		if cellPlug is not None :
			indicesAndPlugs = [ ( defaultCells.children().index( cellPlug ), cellPlug ) ]
		else :
			indicesAndPlugs = enumerate( defaultCells )

		try :

			self.__ignoreSectionResized = True

			for index, plug in indicesAndPlugs :

				width = Gaffer.Metadata.value( plug, "spreadsheet:columnWidth" )
				if width is None :
					width = self._qtWidget().horizontalHeader().defaultSectionSize()

				self._qtWidget().horizontalHeader().resizeSection( index, width )

		finally :

			self.__ignoreSectionResized = False

	def __applySectionOrderMetadata( self ) :

		if self.__mode == self.Mode.RowNames :
			return

		rowsPlug = self._qtWidget().model().rowsPlug()
		header = self._qtWidget().horizontalHeader()
		for index, plug in enumerate( rowsPlug.defaultRow()["cells"] ) :
			visualIndex = Gaffer.Metadata.value( plug, "spreadsheet:columnIndex" )
			self.__callingMoveSection = True
			header.moveSection( header.visualIndex( index ), visualIndex if visualIndex is not None else index )
			self.__callingMoveSection = False

	def __applyColumnVisibility( self ) :

		if self.__mode == self.Mode.RowNames :
			return

		# Changing column visibility seems to cause the
		# `sectionResized()` signal to be emitted unnecessarily,
		# so we suppress the slot we've attached to it.
		self.__ignoreSectionResized = True
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
			self.__ignoreSectionResized = False

	@GafferUI.LazyMethod()
	def __applySectionOrderLazily( self ) :

		self.__applySectionOrderMetadata()

	def __plugMetadataChanged( self, nodeTypeId, plugPath, key, plug ) :

		if plug is None :
			return

		rowsPlug = self._qtWidget().model().rowsPlug()
		if not rowsPlug.isAncestorOf( plug ) :
			return

		if key == "spreadsheet:columnWidth" :

			if plug.parent() == rowsPlug.defaultRow()["cells"] :
				self.__applyColumnWidthMetadata( cellPlug = plug )

		elif key == "spreadsheet:columnIndex" :

			# Typically we get a flurry of edits to columnIndex at once,
			# so we use a lazy method to update the order once everything
			# has been done.
			self.__applySectionOrderLazily()

		elif key == "spreadsheet:section" :

			self.__applyColumnVisibility()

	def __buttonPress( self, widget, event ) :

		if event.buttons != event.Buttons.Right :
			return False

		index = self._qtWidget().indexAt( QtCore.QPoint( event.line.p0.x, event.line.p0.y ) )

		if not index.flags() & QtCore.Qt.ItemIsEnabled :
			return True

		selectionModel = self._qtWidget().selectionModel()

		if not selectionModel.isSelected( index ) :
			selectionModel.select( index, selectionModel.ClearAndSelect )

		if len( selectionModel.selection().indexes() ) == 1 :

			plug = self._qtWidget().model().plugForIndex( index )
			if plug is None :
				return False

			if isinstance( plug, Gaffer.Spreadsheet.CellPlug ) :
				plug = plug["value"]

			cellPlug = plug.ancestor( Gaffer.Spreadsheet.CellPlug )

			## \todo We need to make this temporary PlugValueWidget just so we
			# can show a plug menu. We should probably refactor so we can do it
			# without the widget, but this would touch `PlugValueWidget.popupMenuSignal()`
			# and all connected client code.
			self.__menuPlugValueWidget = GafferUI.PlugValueWidget.create( plug )
			definition = self.__menuPlugValueWidget._popupMenuDefinition()

			if self.__mode == self.Mode.RowNames :
				self.__prependRowMenuItems( definition, plug.ancestor( Gaffer.Spreadsheet.RowPlug ) )
			elif cellPlug is not None :
				self.__prependCellMenuItems( definition, [ cellPlug ] )

		else :

			definition = IECore.MenuDefinition()
			if self.__mode != self.Mode.RowNames :
				self.__prependCellMenuItems( definition, self.selectedPlugs() )

		self.__plugMenu = GafferUI.Menu( definition )
		self.__plugMenu.popup()

		return True

	def __buttonDoubleClick( self, widget, event ) :

		if event.buttons != event.Buttons.Left :
			return False

		index = self._qtWidget().indexAt( QtCore.QPoint( event.line.p0.x, event.line.p0.y ) )
		plug = self._qtWidget().model().plugForIndex( index )
		if plug is None :
			return False

		valuePlug = plug["value"] if isinstance( plug, Gaffer.Spreadsheet.CellPlug ) else plug
		if not isinstance( valuePlug, Gaffer.BoolPlug ) :
			self.editPlug( plug, scrollTo = False )

		return True

	def __headerButtonPress( self, header, event ) :

		if event.buttons != event.Buttons.Right :
			return False

		cellPlug = self.plugAt( event.line.p0 )
		assert( cellPlug.ancestor( Gaffer.Spreadsheet.RowPlug ) == cellPlug.ancestor( Gaffer.Spreadsheet.RowsPlug ).defaultRow() )

		menuDefinition = IECore.MenuDefinition()
		menuDefinition.append(
			"/Set Label...",
			{
				"command" : functools.partial( Gaffer.WeakMethod( self.__setColumnLabel ), cellPlug ),
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
				"command" : functools.partial( Gaffer.WeakMethod( self.__deleteColumn), cellPlug ),
				"active" : (
					not Gaffer.MetadataAlgo.readOnly( cellPlug ) and
					_Algo.dimensionsEditable( self._qtWidget().model().rowsPlug() )
				)
			}
		)

		self.__headerMenu = GafferUI.Menu( menuDefinition )
		self.__headerMenu.popup()

		return True

	def __prependRowMenuItems( self, menuDefinition, rowPlug ) :

		if rowPlug == rowPlug.parent().defaultRow() :
			return

		targetDivider = "/__SpreadsheetRowAndCellDivider__"
		if menuDefinition.item( targetDivider ) is None :
			menuDefinition.prepend( targetDivider, { "divider" : True } )

		items = []

		widths = [
			( "Half", GafferUI.PlugWidget.labelWidth() * 0.5 ),
			( "Single", GafferUI.PlugWidget.labelWidth() ),
			( "Double", GafferUI.PlugWidget.labelWidth() * 2 ),
		]

		currentWidth = _PlugTableView._getRowNameWidth( rowPlug.parent() )
		for label, width in widths :
			items.append( (
				"/Width/{}".format( label ),
				{
					"command" : functools.partial( self.__setRowNameWidth, rowPlug, width ),
					"active" : not Gaffer.MetadataAlgo.readOnly( rowPlug ),
					"checkBox" : width == currentWidth,
				}
			) )

		items.extend( (
			(
				"/__DeleteRowDivider__", { "divider" : True }
			),
			(
				"/Delete Row",
				{
					"command" : functools.partial( _Algo.deleteRow, rowPlug ),
					"active" : (
						not Gaffer.MetadataAlgo.readOnly( rowPlug ) and
						_Algo.dimensionsEditable( rowPlug.parent() )
					)
				}
			)
		) )

		for path, args in reversed( items ) :
			menuDefinition.prepend( path, args )

	def __prependCellMenuItems( self, menuDefinition, cellPlugs ) :

		if len( cellPlugs ) == 0 :
			return

		targetDivider = "/__SpreadsheetRowAndCellDivider__"
		if menuDefinition.item( targetDivider ) is None :
			menuDefinition.prepend( targetDivider, { "divider" : True } )

		pluralSuffix = "" if len( cellPlugs ) == 1 else "s"

		defaultRow = next( iter( cellPlugs ) ).ancestor( Gaffer.Spreadsheet.RowsPlug ).defaultRow()
		defaultRowPlugs = [ c for c in cellPlugs if c.ancestor( Gaffer.Spreadsheet.RowPlug ) == defaultRow ]

		# Disallow disable if the selection contains the default row, and any default row cells aren't adopting
		# an enabled plug, but do allow a mix of 'should be disable-able but locked/connected' and ok plugs.
		disabledAllowed = not defaultRowPlugs or any( [ "enabled" not in cell for cell in defaultRowPlugs ] )
		enabledPlugs = [ cell.enabledPlug() for cell in cellPlugs ]
		readOnly = all( [ Gaffer.MetadataAlgo.readOnly( plug ) for plug in enabledPlugs ] )
		settable = all( [ plug.settable() for plug in enabledPlugs ] )

		with self.__getContext() :
			with IECore.IgnoredExceptions( Gaffer.ProcessException ) :
				enabled = all( [ plug.getValue() for plug in enabledPlugs ] )

		items = [
			(
				( "/Disable Cell%s" if enabled else "/Enable Cell%s" ) % pluralSuffix,
				{
					"command" : functools.partial( _Algo.setPlugValues, enabledPlugs, not enabled ),
					"active" : not readOnly and settable
				}
			)
		]

		plugMatrix = _Clipboard.createPlugMatrix( cellPlugs )
		clipboard = self.__getClipboard()

		items.extend( (
			(
				"/__CopyPasteCellsDivider__", { "divider" : True }
			),
			(
				"Copy Cell%s" % pluralSuffix,
				{
					"command" : Gaffer.WeakMethod( self.__copyCells ),
					"active" : _Clipboard.canCopyCells( plugMatrix )
				}
			),
			(
				"Paste Cell%s" % pluralSuffix,
				{
					"command" : Gaffer.WeakMethod( self.__pasteCells ),
					"active" : _Clipboard.isCellData( clipboard ) and _Clipboard.canPasteCells( clipboard, plugMatrix )
				}
			)
		) )

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

		with self.__getContext() :
			clipboardData = _Clipboard.cellData( _Clipboard.createPlugMatrix( selection ) )

		self.__setClipboard( clipboardData )

	def __pasteCells( self ) :

		scriptNode = self._qtWidget().model().rowsPlug().ancestor( Gaffer.ScriptNode )

		targetPlugs = _Clipboard.createPlugMatrix( self.selectedPlugs() )

		# Required for current time if keyframing
		with self.__getContext() :
			with Gaffer.UndoScope( scriptNode ) :
				_Clipboard.pasteCells( self.__getClipboard(), targetPlugs )

	def __getContext( self ) :

		editor = self.ancestor( GafferUI.Editor )
		if editor is not None:
			return editor.getContext()

		scriptNode = self._qtWidget().model().rowsPlug().ancestor( Gaffer.ScriptNode )
		if scriptNode is not None :
			return scriptNode.context()

		return Gaffer.Context.current()

	def __setColumnLabel( self, cellPlug ) :

		label = GafferUI.TextInputDialogue(
			title = "Set Label",
			confirmLabel = "Set",
			initialText = Gaffer.Metadata.value( cellPlug, "spreadsheet:columnLabel" ) or cellPlug.getName()
		).waitForText( parentWindow = self.ancestor( GafferUI.Window ) )

		if label is not None :
			with Gaffer.UndoScope( cellPlug.ancestor( Gaffer.ScriptNode ) ) :
				Gaffer.Metadata.registerValue( cellPlug, "spreadsheet:columnLabel", label )

	def __deleteColumn( self, cellPlug ) :

		rowsPlug = cellPlug.ancestor( Gaffer.Spreadsheet.RowsPlug )
		with Gaffer.UndoScope( rowsPlug.ancestor( Gaffer.ScriptNode ) ) :
			rowsPlug.removeColumn( cellPlug.parent().children().index( cellPlug ) )

	@staticmethod
	def __setRowNameWidth( rowPlug, width, *unused ) :

		with Gaffer.UndoScope( rowPlug.ancestor( Gaffer.ScriptNode ) ) :
			_PlugTableView._setRowNameWidth( rowPlug.parent(), width )

	def __modelReset( self ) :

		self.__applyColumnVisibility()
		self.__applyColumnWidthMetadata()

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
	def _affectsRowNameWidth( key ) :

		return key == "spreadsheet:rowNameWidth"

	@staticmethod
	def _getRowNameWidth( rowsPlug ) :

		assert( isinstance( rowsPlug, Gaffer.Spreadsheet.RowsPlug ) )
		width = Gaffer.Metadata.value( rowsPlug.defaultRow(), "spreadsheet:rowNameWidth" )
		return width if width is not None else GafferUI.PlugWidget.labelWidth()

	@staticmethod
	def _setRowNameWidth( rowsPlug, width ) :

		assert( isinstance( rowsPlug, Gaffer.Spreadsheet.RowsPlug ) )
		Gaffer.Metadata.registerValue( rowsPlug.defaultRow(), "spreadsheet:rowNameWidth", width )
