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

import collections
import functools
import re
import sys

import imath

import IECore

import Gaffer
import GafferUI

from Qt import QtCore
from Qt import QtGui
from Qt import QtWidgets
from Qt import QtCompat

from ._TableView import _TableView

# Value Formatting
# ================

## Returns the value of the plug as it will be formatted in a Spreadsheet.
def formatValue( plug, forToolTip = False ) :

	currentPreset = Gaffer.NodeAlgo.currentPreset( plug )
	if currentPreset is not None :
		return currentPreset

	global __valueFormatters
	formatter = __valueFormatters.get( plug.__class__, __defaultValueFormatter )
	return formatter( plug, forToolTip )

## Registers a custom formatter for the specified `plugType`.
# `formatter` must have the same signature as `formatValue()`.
def registerValueFormatter( plugType, formatter ) :

	global __valueFormatters
	__valueFormatters[plugType] = formatter

__valueFormatters = {}

def __defaultValueFormatter( plug, forToolTip ) :

	if not hasattr( plug, "getValue" ) :
		return ""

	value = plug.getValue()
	if isinstance( value, str ) :
		return value
	elif isinstance( value, ( int, float ) ) :
		return GafferUI.NumericWidget.valueToString( value )
	elif isinstance( value, ( imath.V2i, imath.V2f, imath.V3i, imath.V3f ) ) :
		return ", ".join( GafferUI.NumericWidget.valueToString( v ) for v in value )

	try :
		# Unknown type. If iteration is supported then use that.
		separator = "\n" if forToolTip else ", "
		return separator.join( str( x ) for x in value )
	except :
		# Otherwise just cast to string
		return str( value )

def __transformPlugFormatter( plug, forToolTip ) :

	separator = "\n" if forToolTip else "  "
	return separator.join(
		"{label} : {value}".format(
			label = c.getName().title() if forToolTip else c.getName()[0].title(),
			value = formatValue( c, forToolTip )
		)
		for c in plug.children()
	)

registerValueFormatter( Gaffer.TransformPlug, __transformPlugFormatter )

# Decorations
# ===========

## Registers a function to return a decoration to be shown
# alongside the formatted value. Currently the only supported
# return type is `Color3f`.
def registerDecoration( plugType, decorator ) :

	global __valueDecorators
	__valueDecorators[plugType] = decorator

## Returns the decoration for the specified plug.
def decoration( plug ) :

	global __valueDecorators
	decorator = __valueDecorators.get( plug.__class__ )
	return decorator( plug ) if decorator is not None else None

__valueDecorators = {}

def __colorPlugDecorator( plug ) :

	return plug.getValue()

registerDecoration( Gaffer.Color3fPlug, __colorPlugDecorator )

# Editing
# =======
#
# By default, `PlugValueWidget.create( cell["value"] )` is used to create
# a widget for editing cells in the spreadsheet, but custom editors may be
# provided for specific plug types.

# Registers a function to return a PlugValueWidget for editing cell
# value plugs of the specified type.
def registerValueWidget( plugType, plugValueWidgetCreator ) :

	_CellPlugValueWidget.registerValueWidget( plugType, plugValueWidgetCreator )

def _dimensionsEditable( rowsPlug ) :

	# We don't currently allow addition/removal of rows/columns
	# when a RowsPlug is hosted on a Reference node, to avoid
	# merge hell when reloading or updating the reference.
	return not isinstance( rowsPlug.node(), Gaffer.Reference )

# Metadata
# ========

Gaffer.Metadata.registerNode(

	Gaffer.Spreadsheet,

	"description",
	"""
	Provides a spreadsheet designed for easy management of sets of
	associated plug values. Each column of the spreadsheet corresponds
	to an output value that can be connected to drive a plug on another
	node. Each row of the spreadsheet provides candidate values for each
	output, along with a row name and enabled status. Row names are matched
	against a selector to determine which row is passed through to the output.
	Row matching is performed as follows :

	- Matching starts with the second row and considers all subsequent
	  rows one by one until a match is found. The first matching row
	  is the one that is chosen.
	- Matching is performed using Gaffer's standard wildcard matching.
	  Each "name" may contain several individual patterns each separated
	  by spaces.
	- The first row is used as a default, and is chosen only if no other
	  row matches.

	> Note : The matching rules are identical to the ones used by the
	> NameSwitch node.
	""",

	"nodeGadget:type", "GafferUI::AuxiliaryNodeGadget",
	"nodeGadget:shape", "oval",
	"uiEditor:nodeGadgetTypes", IECore.StringVectorData( [ "GafferUI::AuxiliaryNodeGadget", "GafferUI::StandardNodeGadget" ] ),
	"auxiliaryNodeGadget:label", "#",

	plugs = {

		"*" : [

			"nodule:type", "",

		],

		"selector" : [

			"description",
			"""
			The value that the row names will be matched against.
			Typically this will refer to a Context Variable using
			the `${variableName}` syntax.
			""",

			"divider", True,

		],

		"rows" : [

			"description",
			"""
			Holds a child RowPlug for each row in the spreadsheet.
			""",

		],

		"rows.default" : [

			"description",
			"""
			The default row. This provides output values when no other
			row matches the `selector`.
			""",

		],

		"rows.*.name" : [

			"description",
			"""
			The name of the row. This is matched against the `selector`
			to determine which row is chosen to be passed to the output.
			May contain multiple space separated names and any of Gaffer's
			standard wildcards.
			""",

		],

		"rows.*.enabled" : [

			"description",
			"""
			Enables or disables this row. Disabled rows are ignored.
			""",

		],

		"rows.*.cells" : [

			"description",
			"""
			Contains a child CellPlug for each column in the spreadsheet.
			""",

		],

		"out" : [

			"description",
			"""
			The outputs from the spreadsheet. Contains a child plug for each
			column in the spreadsheet.
			""",

			"plugValueWidget:type", "",

		],

		"activeRowNames" : [

			"description",
			"""
			An output plug containing the names of all currently active rows.
			""",

			"plugValueWidget:type", "",

		],

	}

)

# Metadata methods
# ================
#
# We don't want to copy identical metadata onto every cell of the spreadsheet, as
# that's a lot of pointless duplication. Instead we register metadata onto the
# default row only, and then mirror it dynamically onto the other rows. This isn't
# flawless because we can only mirror metadata we know the names for in advance, but
# since we only support a limited subset of widgets in the spreadsheet it seems
# workable.

def __correspondingDefaultPlug( plug ) :

	rowPlug = plug.ancestor( Gaffer.Spreadsheet.RowPlug )
	rowsPlug = rowPlug.parent()
	return rowsPlug.defaultRow().descendant( plug.relativeName( rowPlug ) )

def __defaultCellMetadata( plug, key ) :

	return Gaffer.Metadata.value( __correspondingDefaultPlug( plug ), key )

for key in [
	"spreadsheet:columnLabel",
	"plugValueWidget:type",
	"presetsPlugValueWidget:allowCustom"
] :

	Gaffer.Metadata.registerValue(
		Gaffer.Spreadsheet.RowsPlug, "row*.cells...", key,
		functools.partial( __defaultCellMetadata, key = key ),
	)

# Presets are tricky because we can't know their names in advance. We register
# "presetNames" and "presetValues" arrays that we can use to gather all "preset:*"
# metadata into on the fly.

__plugPresetTypes = {

	Gaffer.IntPlug : IECore.IntVectorData,
	Gaffer.FloatPlug : IECore.FloatVectorData,
	Gaffer.StringPlug : IECore.StringVectorData,
	Gaffer.V3fPlug : IECore.V3fVectorData,
	Gaffer.V2fPlug : IECore.V2fVectorData,
	Gaffer.V3iPlug : IECore.V3iVectorData,
	Gaffer.V2iPlug : IECore.V2iVectorData,
	Gaffer.Color3fPlug : IECore.Color3fVectorData,
	Gaffer.Color4fPlug : IECore.Color4fVectorData,

}

def __presetNamesMetadata( plug ) :

	if plug.__class__ not in __plugPresetTypes :
		return None

	source = __correspondingDefaultPlug( plug )

	result = IECore.StringVectorData()
	for n in Gaffer.Metadata.registeredValues( source ) :
		if n.startswith( "preset:" ) :
			result.append( n[7:] )

	result.extend( Gaffer.Metadata.value( source, "presetNames" ) or [] )
	return result

def __presetValuesMetadata( plug ) :

	dataType = __plugPresetTypes.get( plug.__class__ )
	if dataType is None :
		return None

	source = __correspondingDefaultPlug( plug )

	result = dataType()
	for n in Gaffer.Metadata.registeredValues( source ) :
		if n.startswith( "preset:" ) :
			result.append( Gaffer.Metadata.value( source, n ) )

	result.extend( Gaffer.Metadata.value( source, "presetValues" ) or [] )
	return result

Gaffer.Metadata.registerValue( Gaffer.Spreadsheet.RowsPlug, "row*.cells...", "presetNames", __presetNamesMetadata )
Gaffer.Metadata.registerValue( Gaffer.Spreadsheet.RowsPlug, "row*.cells...", "presetValues", __presetValuesMetadata )

def _affectsRowNameWidth( key ) :

	return key == "spreadsheet:rowNameWidth"

def _getRowNameWidth( rowsPlug ) :

	assert( isinstance( rowsPlug, Gaffer.Spreadsheet.RowsPlug ) )
	width = Gaffer.Metadata.value( rowsPlug.defaultRow(), "spreadsheet:rowNameWidth" )
	return width if width is not None else GafferUI.PlugWidget.labelWidth()

def _setRowNameWidth( rowsPlug, width ) :

	assert( isinstance( rowsPlug, Gaffer.Spreadsheet.RowsPlug ) )
	Gaffer.Metadata.registerValue( rowsPlug.defaultRow(), "spreadsheet:rowNameWidth", width )

# _RowsPlugValueWidget
# ====================
#
# This is the main top-level widget that forms the spreadsheet UI.

class _RowsPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug ) :

		self.__grid = GafferUI.GridContainer( spacing = 4 )

		GafferUI.PlugValueWidget.__init__( self, self.__grid, plug )

		with self.__grid :

			self.__sectionChooser = _SectionChooser(
				plug,
				parenting = {
					"index" : ( 1, 0 ),
				}
			)
			self.__sectionChooser.currentSectionChangedSignal().connect( Gaffer.WeakMethod( self.__currentSectionChanged ), scoped = False )

			with GafferUI.ListContainer(
				parenting = {
					"index" : ( 0, 1 ),
					"alignment" : ( GafferUI.HorizontalAlignment.Left, GafferUI.VerticalAlignment.Bottom ),
				}
			) :

				self.__defaultLabel = GafferUI.Label( "Default" )
				self.__defaultLabel._qtWidget().setIndent( 6 )
				GafferUI.Spacer( imath.V2i( 1, 8 ) )

			self.__defaultTable = _PlugTableView(
				plug, self.getContext(), _PlugTableView.Mode.Defaults,
				parenting = {
					"index" : ( 1, 1 ),
				}
			)

			self.__rowNamesTable = _PlugTableView(
				plug, self.getContext(), _PlugTableView.Mode.RowNames,
				parenting = {
					"index" : ( 0, 2 ),
				}
			)
			self.__updateRowNamesWidth()

			self.__cellsTable = _PlugTableView(
				plug, self.getContext(), _PlugTableView.Mode.Cells,
				parenting = {
					"index" : ( 1, 2 ),
				}
			)

			_LinkedScrollBar(
				GafferUI.ListContainer.Orientation.Vertical, [ self.__cellsTable, self.__rowNamesTable ],
				parenting = {
					"index" : ( 2, 2 ),
				}
			)

			_LinkedScrollBar(
				GafferUI.ListContainer.Orientation.Horizontal, [ self.__cellsTable, self.__defaultTable ],
				parenting = {
					"index" : ( 1, 3 ),
				}
			)

			addRowButton = GafferUI.Button(
				image="plus.png", hasFrame=False, toolTip = "Click to add row, or drop new row names",
				parenting = {
					"index" : ( 0, 4 )
				}
			)
			addRowButton.clickedSignal().connect( Gaffer.WeakMethod( self.__addRowButtonClicked ), scoped = False )
			addRowButton.dragEnterSignal().connect( Gaffer.WeakMethod( self.__addRowButtonDragEnter ), scoped = False )
			addRowButton.dragLeaveSignal().connect( Gaffer.WeakMethod( self.__addRowButtonDragLeave ), scoped = False )
			addRowButton.dropSignal().connect( Gaffer.WeakMethod( self.__addRowButtonDrop ), scoped = False )

			addRowButton.setVisible( _dimensionsEditable( plug ) )

			self.__statusLabel = GafferUI.Label(
				"",
				parenting = {
					"index" : ( slice( 1, 3 ), 4 ),
					"alignment" : ( GafferUI.HorizontalAlignment.Left, GafferUI.VerticalAlignment.Top )
				}
			)
			# The status label occupies the same column as `cellsTable`, and has a dynamic width based on the length
			# of the status text. Ignore the width in X so that the column width is dictated solely by `cellsTable`,
			# otherwise large status labels can force cells off the screen.
			self.__statusLabel._qtWidget().setSizePolicy( QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Fixed )

		for widget in [ addRowButton ] :
			widget.enterSignal().connect( Gaffer.WeakMethod( self.__enterToolTippedWidget ), scoped = False )
			widget.leaveSignal().connect( Gaffer.WeakMethod( self.__leaveToolTippedWidget ), scoped = False )

		for widget in [ self.__defaultTable, self.__cellsTable ] :
			widget.mouseMoveSignal().connect( Gaffer.WeakMethod( self.__cellsMouseMove ), scoped = False )
			widget.leaveSignal().connect( Gaffer.WeakMethod( self.__cellsLeave ), scoped = False )

		Gaffer.Metadata.plugValueChangedSignal().connect( Gaffer.WeakMethod( self.__plugMetadataChanged ), scoped = False )

		self.__updateVisibleSections()
		self.__updateDefaultRowVisibility()

	def hasLabel( self ) :

		return True

	def _updateFromPlug( self ) :

		self.__grid.setEnabled(
			self.getPlug().getInput() is None and not Gaffer.MetadataAlgo.readOnly( self.getPlug() )
		)

	def __addRowButtonClicked( self, *unused ) :

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			row = self.getPlug().addRow()

		# Select new row for editing. Have to do this on idle as otherwise it doesn't scroll
		# right to the bottom.
		GafferUI.EventLoop.addIdleCallback( functools.partial( self.__rowNamesTable.editPlug, row["name"] ) )

	def __addRowButtonDragEnter( self, addButton, event ) :

		if isinstance( event.data, ( IECore.StringData, IECore.StringVectorData ) ) :
			addButton.setHighlighted( True )
			return True

		return False

	def __addRowButtonDragLeave( self, addButton, event ) :

		addButton.setHighlighted( False )
		return True

	def __addRowButtonDrop( self, addButton, event ) :

		addButton.setHighlighted( False )
		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			strings = event.data if isinstance( event.data, IECore.StringVectorData ) else [ event.data.value ]
			for s in strings :
				self.getPlug().addRow()["name"].setValue( s )

		return True

	def __enterToolTippedWidget( self, widget ) :

		self.__statusLabel.setText( widget.getToolTip() )

	def __leaveToolTippedWidget( self, widget ) :

		self.__statusLabel.setText( "" )

	def __cellsMouseMove( self, widget, event ) :

		status = ""

		plug = widget.plugAt( event.line.p0 )
		if plug is not None :

			rowPlug = plug.ancestor( Gaffer.Spreadsheet.RowPlug )
			if rowPlug == rowPlug.parent().defaultRow() :
				rowName = "Default"
			else :
				with self.getContext() :
					rowName = rowPlug["name"].getValue() or "unnamed"

			status = "Row : {}, Column : {}".format(
				rowName,
				IECore.CamelCase.toSpaced( plug.getName() ),
			)

		self.__statusLabel.setText( status )

	def __cellsLeave( self, widget ) :

		self.__statusLabel.setText( "" )

	def __updateRowNamesWidth( self ) :

		self.__rowNamesTable._qtWidget().setFixedWidth( _getRowNameWidth( self.getPlug() ) )

	def __updateDefaultRowVisibility( self ) :

		visible = Gaffer.Metadata.value( self.getPlug(), "spreadsheet:defaultRowVisible" )
		if visible is None :
			visible = True
		self.__defaultLabel.setVisible( visible )
		## \todo We shouldn't really be reaching into the protected
		# `_qtWidget()` implementation here. Soon enough we will want
		# to implement searching/filtering of rows, and when we implement
		# that we should do it via a simple abstraction on `_PlugTableView`
		# and use that here too. Perhaps just `setRowFilter( matchPattern )`
		# would do the trick?
		self.__defaultTable._qtWidget().setRowHidden( 0, not visible )

	def __plugMetadataChanged( self, nodeTypeId, plugPath, key, plug ) :

		if plug is not None and _affectsRowNameWidth( key ) :
			if self.getPlug().isAncestorOf( plug ) :
				self.__updateRowNamesWidth()

		if plug == self.getPlug() and key == "spreadsheet:defaultRowVisible" :
			self.__updateDefaultRowVisibility()

	def __currentSectionChanged( self, tabBar ) :

		self.__updateVisibleSections()

	def __updateVisibleSections( self ) :

		section = self.__sectionChooser.currentSection()
		self.__defaultTable.setVisibleSection( section )
		self.__cellsTable.setVisibleSection( section )

GafferUI.PlugValueWidget.registerType( Gaffer.Spreadsheet.RowsPlug, _RowsPlugValueWidget )

# _CellPlugValueWidget
# ====================

class _CellPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plugs, **kw ) :

		self.__row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 )
		GafferUI.PlugValueWidget.__init__( self, self.__row, plugs )

		enabledPlugs = [ p["enabled"] for p in plugs if "enabled" in p ]
		valuePlugs = [ p["value"] for p in plugs if "value" in p ]

		assert( len(enabledPlugs) == len(valuePlugs) )

		rowPlug = ( next( iter( plugs ) ) ).ancestor( Gaffer.Spreadsheet.RowPlug )
		if enabledPlugs and rowPlug != rowPlug.parent().defaultRow() :
			enabledPlugValueWidget = GafferUI.BoolPlugValueWidget(
				enabledPlugs,
				displayMode=GafferUI.BoolWidget.DisplayMode.Switch
			)
			self.__row.append( enabledPlugValueWidget, verticalAlignment=GafferUI.VerticalAlignment.Top )

		plugValueWidget = self.__createValueWidget( valuePlugs )

		# Apply some fixed widths for some widgets, otherwise they're
		# a bit too eager to grow. \todo Should we change the underlying
		# behaviour of the widgets themselves?
		self.__applyFixedWidths( plugValueWidget )

		self.__row.append( plugValueWidget )

		self._updateFromPlugs()

	def childPlugValueWidget( self, childPlug ) :

		for widget in self.__row :
			if childPlug in widget.getPlugs() :
				return widget

		return None

	@classmethod
	def registerValueWidget( cls, plugType, plugValueWidgetCreator ) :

		cls.__plugValueWidgetCreators[plugType] = plugValueWidgetCreator

	def __createValueWidget( self, plugs ) :

		creator = self.__plugValueWidgetCreators.get(
			next( iter( plugs ) ).__class__,
			GafferUI.PlugValueWidget.create
		)

		w = creator( plugs )
		assert( isinstance( w, GafferUI.PlugValueWidget ) )
		return w

	__plugValueWidgetCreators = {}

	def _updateFromPlugs( self ) :

		# TODO Properly support multiple plugs

		plugs = self.getPlugs()
		if len( plugs ) == 1 :
			plug = next( iter( self.getPlugs() ) )
			if "enabled" in plug :
				enabled = False
				with self.getContext() :
					with IECore.IgnoredExceptions( Exception ) :
						enabled = plug["enabled"].getValue()
				self.__row[-1].setEnabled( enabled )

	__numericFieldWidth = 60

	@classmethod
	def __applyFixedWidths( cls, plugValueWidget ) :

		def walk( widget ) :

			if isinstance( widget, GafferUI.NumericPlugValueWidget ) :
				widget._qtWidget().setFixedWidth( cls.__numericFieldWidth )
				widget._qtWidget().layout().setSizeConstraint( QtWidgets.QLayout.SetNoConstraint )

			for childPlug in Gaffer.Plug.Range( next( iter( widget.getPlugs() ) ) ) :
				childWidget = widget.childPlugValueWidget( childPlug )
				if childWidget is not None :
					walk( childWidget )

		if isinstance( plugValueWidget, GafferUI.VectorDataPlugValueWidget ) :
			plugValueWidget._qtWidget().setFixedWidth( 250 )
		else :
			walk( plugValueWidget )

GafferUI.PlugValueWidget.registerType( Gaffer.Spreadsheet.CellPlug, _CellPlugValueWidget )

# _PlugTableView
# ==============

class _PlugTableView( GafferUI.Widget ) :

	Mode = IECore.Enum.create( "RowNames", "Defaults", "Cells" )

	def __init__( self, plug, context, mode, **kw ) :

		tableView = _TableView()
		GafferUI.Widget.__init__( self, tableView, **kw )

		tableView.setModel(
			_PlugTableModel( plug, context, mode )
		)

		# Headers and column sizing

		QtCompat.setSectionResizeMode( tableView.verticalHeader(), QtWidgets.QHeaderView.Fixed )
		tableView.verticalHeader().setDefaultSectionSize( 25 )
		tableView.verticalHeader().setVisible( mode is self.Mode.RowNames )

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
			tableView.verticalHeader().setSectionsMovable( True )

		if mode != self.Mode.Defaults :
			tableView.horizontalHeader().setVisible( False )

		# Column visibility

		self.__visibleSection = None
		tableView.model().modelReset.connect( Gaffer.WeakMethod( self.__modelReset ) )

		# Selection and editing. We disable all edit triggers so that
		# the QTableView itself won't edit anything, and we then implement
		# our own editing via PlugValueWidgets in _EditWindow.

		tableView.setEditTriggers( tableView.NoEditTriggers )
		tableView.setSelectionMode( QtWidgets.QAbstractItemView.ExtendedSelection )
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

		# Selection changed signalling

		tableView.selectionModel().selectionChanged.connect( Gaffer.WeakMethod( self.__selectionChanged ) )
		self.__selectionChangedSignal = GafferUI.WidgetSignal()

		# Keys

		self.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ), scoped = False )

	def selectionChangedSignal( self ) :

		return self.__selectionChangedSignal

	def plugAt( self, position ) :

		index = self._qtWidget().indexAt( QtCore.QPoint( position.x, position.y ) )
		return self._qtWidget().model().plugForIndex( index )

	def selectedPlugs( self ) :

		selection = self._qtWidget().selectionModel().selectedIndexes()
		return self._qtWidget().model().plugsForIndices( selection )

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

	def __keyPress( self, widget, event ) :

		if event.key == "Return" :
			self.__editSelection()
			return True

		return False

	def __selectionChanged( self, selected, deselected ) :

		self.__selectionChangedSignal( self )

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

		if self._qtWidget().model().mode() == self.Mode.RowNames :
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

		if self._qtWidget().model().mode() == self.Mode.RowNames :
			return

		rowsPlug = self._qtWidget().model().rowsPlug()
		header = self._qtWidget().horizontalHeader()
		for index, plug in enumerate( rowsPlug.defaultRow()["cells"] ) :
			visualIndex = Gaffer.Metadata.value( plug, "spreadsheet:columnIndex" )
			self.__callingMoveSection = True
			header.moveSection( header.visualIndex( index ), visualIndex if visualIndex is not None else index )
			self.__callingMoveSection = False

	def __applyColumnVisibility( self ) :

		if self._qtWidget().model().mode() == self.Mode.RowNames :
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

		index = self._qtWidget().indexAt( QtCore.QPoint( event.line.p0.x, event.line.p0.y ) )
		plug = self._qtWidget().model().plugForIndex( index )
		if plug is None :
			return False

		if event.buttons == event.Buttons.Right :

			if index.flags() & QtCore.Qt.ItemIsEnabled :

				if isinstance( plug, Gaffer.Spreadsheet.CellPlug ) :
					plug = plug["value"]
				## \todo We need to make this temporary PlugValueWidget just so we
				# can show a plug menu. We should probably refactor so we can do it
				# without the widget, but this would touch `PlugValueWidget.popupMenuSignal()`
				# and all connected client code.
				self.__menuPlugValueWidget = GafferUI.PlugValueWidget.create( plug )
				definition = self.__menuPlugValueWidget._popupMenuDefinition()
				self.__appendPlugContextMenu( definition )
				self.__plugMenu = GafferUI.Menu( definition )
				self.__plugMenu.popup()

			return True

		return False

	def __buttonDoubleClick( self, widget, event ) :

		index = self._qtWidget().indexAt( QtCore.QPoint( event.line.p0.x, event.line.p0.y ) )
		plug = self._qtWidget().model().plugForIndex( index )
		if plug is None :
			return False

		if event.buttons == event.Buttons.Left :

			valuePlug = plug["value"] if isinstance( plug, Gaffer.Spreadsheet.CellPlug ) else plug
			if isinstance( valuePlug, Gaffer.BoolPlug ) :
				valuePlug.setValue( not valuePlug.getValue() )
			else :
				self.editPlug( plug, scrollTo = False )

			return True

		return False

	def __appendPlugContextMenu( self, definition ) :

		selectedPlugs = self.selectedPlugs()

		definition.prepend( "/Edit divider", { "divider" : True } )

		definition.prepend( "/Edit Selection", {
			"active" : self.__canMultiEdit( selectedPlugs ),
			"command" : Gaffer.WeakMethod( self.__editSelection )
		} )

	@staticmethod
	def __canMultiEdit( plugs ) :

		return sole( [ type(p["value"]) for p in plugs ] ) is not None

	def __editSelection( self ) :

		selectedPlugs = self.selectedPlugs()

		if not self.__canMultiEdit( selectedPlugs ) :
			raise RuntimeError( "Can't multi-edit selection as it contains mixed plug types" )

		pos = GafferUI.Widget.mousePosition()
		_EditWindow.popupEditor( selectedPlugs, imath.Box2i( pos, pos ) )

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
					_dimensionsEditable( self._qtWidget().model().rowsPlug() )
				)
			}
		)

		self.__headerMenu = GafferUI.Menu( menuDefinition )
		self.__headerMenu.popup()

		return True

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

class _PlugTableModel( QtCore.QAbstractTableModel ) :

	CellPlugEnabledRole = QtCore.Qt.UserRole

	def __init__( self, rowsPlug, context, mode, parent = None ) :

		QtCore.QAbstractTableModel.__init__( self, parent )

		self.__rowsPlug = rowsPlug
		self.__context = context
		self.__mode = mode

		self.__plugDirtiedConnection = rowsPlug.node().plugDirtiedSignal().connect( Gaffer.WeakMethod( self.__plugDirtied ) )
		self.__rowAddedConnection = rowsPlug.childAddedSignal().connect( Gaffer.WeakMethod( self.__rowAdded ) )
		self.__rowRemovedConnection = rowsPlug.childRemovedSignal().connect( Gaffer.WeakMethod( self.__rowRemoved ) )
		self.__columnAddedConnection = rowsPlug.defaultRow()["cells"].childAddedSignal().connect( Gaffer.WeakMethod( self.__columnAdded ) )
		self.__columnRemovedConnection = rowsPlug.defaultRow()["cells"].childRemovedSignal().connect( Gaffer.WeakMethod( self.__columnRemoved ) )
		self.__plugMetadataChangedConnection = Gaffer.Metadata.plugValueChangedSignal().connect( Gaffer.WeakMethod( self.__plugMetadataChanged ) )
		self.__contextChangedConnection = self.__context.changedSignal().connect( Gaffer.WeakMethod( self.__contextChanged ) )

	# Methods of our own
	# ------------------

	def mode( self ) :

		return self.__mode

	def rowsPlug( self ) :

		return self.__rowsPlug

	def plugForIndex( self, index ) :

		if not index.isValid() :
			return None

		if self.__mode in ( _PlugTableView.Mode.Cells, _PlugTableView.Mode.RowNames ) :
			row = self.__rowsPlug[index.row()+1]
		else :
			row = self.__rowsPlug[0]

		if self.__mode == _PlugTableView.Mode.RowNames :
			return row[index.column()]
		else :
			return row["cells"][index.column()]

	def plugsForIndices( self, modelIndexList ) :

		return [ self.plugForIndex( i ) for i in modelIndexList ]

	def valuePlugForIndex( self, index ) :

		plug = self.plugForIndex( index )
		if isinstance( plug, Gaffer.Spreadsheet.CellPlug ) :
			plug = plug["value"]

		return plug

	def indexForPlug( self, plug ) :

		rowPlug = plug.ancestor( Gaffer.Spreadsheet.RowPlug )
		if rowPlug is None :
			return QtCore.QModelIndex()

		if self.__mode in ( _PlugTableView.Mode.Cells, _PlugTableView.Mode.RowNames ) :
			rowIndex = rowPlug.parent().children().index( rowPlug )
			if rowIndex == 0 :
				return QtCore.QModelIndex()
			else :
				rowIndex -= 1
		else :
			rowIndex = 0

		if self.__mode == _PlugTableView.Mode.RowNames :
			if plug == rowPlug["name"] :
				columnIndex = 0
			elif plug == rowPlug["enabled"] :
				columnIndex = 1
			else :
				return QtCore.QModelIndex()
		else :
			cellPlug = plug if isinstance( plug, Gaffer.Spreadsheet.CellPlug ) else plug.ancestor( Gaffer.Spreadsheet.CellPlug )
			if cellPlug is not None :
				columnIndex = rowPlug["cells"].children().index( cellPlug )
			else :
				return QtCore.QModelIndex()

		return self.index( rowIndex, columnIndex )


	# Overrides for methods inherited from QAbstractTableModel
	# --------------------------------------------------------

	def rowCount( self, parent = QtCore.QModelIndex() ) :

		if parent.isValid() :
			return 0

		if self.__mode == _PlugTableView.Mode.Defaults :
			return 1
		else :
			return len( self.__rowsPlug ) - 1

	def columnCount( self, parent = QtCore.QModelIndex() ) :

		if parent.isValid() :
			return 0

		if self.__mode == _PlugTableView.Mode.RowNames :
			return 2
		else :
			return len( self.__rowsPlug[0]["cells"] )

	def headerData( self, section, orientation, role ) :

		if role == QtCore.Qt.DisplayRole :
			if orientation == QtCore.Qt.Horizontal and self.__mode != _PlugTableView.Mode.RowNames :
				cellPlug = self.__rowsPlug.defaultRow()["cells"][section]
				label = Gaffer.Metadata.value( cellPlug, "spreadsheet:columnLabel" )
				if not label :
					label = IECore.CamelCase.toSpaced( cellPlug.getName() )
				return label
			elif orientation == QtCore.Qt.Vertical and self.__mode == _PlugTableView.Mode.RowNames :
				return ""
			return section

	def flags( self, index ) :

		result = QtCore.Qt.ItemIsSelectable

		# We use the ItemIsEnabled flag to reflect the state of
		# `RowPlug::enabledPlug()` for the row `index` is in.
		enabled = True
		plug = self.valuePlugForIndex( index )
		rowPlug = plug.ancestor( Gaffer.Spreadsheet.RowPlug )
		if plug != rowPlug["enabled"] :
			with self.__context :
				try :
					enabled = rowPlug["enabled"].getValue()
				except :
					pass

		if enabled :
			result |= QtCore.Qt.ItemIsEnabled

		# We use the ItemIsEditable flag to reflect the state of
		# readOnly metadata.

		if not Gaffer.MetadataAlgo.readOnly( plug ) :
			result |= QtCore.Qt.ItemIsEditable
			#if isinstance( plug, Gaffer.BoolPlug ) :
			#	result |= QtCore.Qt.ItemIsUserCheckable

		return result

	def data( self, index, role ) :

		if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole :

			return self.__formatValue( index )

		elif role == QtCore.Qt.BackgroundColorRole :

			if index.row() % 2 == 0 :
				return GafferUI._Variant.toVariant( GafferUI._StyleSheet.styleColor( "background" ) )
			else:
				return GafferUI._Variant.toVariant( GafferUI._StyleSheet.styleColor( "backgroundAlt" ) )

		elif role == QtCore.Qt.DecorationRole :

			plug = self.valuePlugForIndex( index )
			with self.__context :
				try :
					value = decoration( plug )
				except :
					return None

			if value is None :
				return None
			elif isinstance( value, imath.Color3f ) :
				displayTransform = GafferUI.DisplayTransform.get()
				return GafferUI.Widget._qtColor( displayTransform( value ) )
			else :
				IECore.msg( IECore.Msg.Level.Error, "Spreadsheet Decoration", "Unsupported type {}".format( type( value ) ) )
				return None

		elif role == QtCore.Qt.CheckStateRole :

			plug = self.__checkStatePlug( index )
			if plug is not None :
				with self.__context :
					try :
						value = plug.getValue()
					except :
						return None
				return QtCore.Qt.Checked if value else QtCore.Qt.Unchecked

		elif role == QtCore.Qt.ToolTipRole :

			return self.__formatValue( index, forToolTip = True )

		elif role == self.CellPlugEnabledRole :

			plug = self.plugForIndex( index )
			enabled = True
			if isinstance( plug, Gaffer.Spreadsheet.CellPlug ) :
				with self.__context :
					try :
						enabled = plug.enabledPlug().getValue()
					except :
						return None
			return enabled

		return None

	def setData( self, index, value, role ) :

		# We use Qt's built-in direct editing of check states
		# as it is convenient, but all other editing is done
		# separately via `_EditWindow`.

		assert( role == QtCore.Qt.CheckStateRole )
		plug = self.__checkStatePlug( index )
		assert( isinstance( plug, Gaffer.BoolPlug ) )

		with Gaffer.UndoScope( plug.ancestor( Gaffer.ScriptNode ) ) :
			plug.setValue( value )

		return True

	# Methods of our own
	# ------------------

	def __checkStatePlug( self, index ) :

		valuePlug = self.valuePlugForIndex( index )
		if isinstance( valuePlug, Gaffer.BoolPlug ) :
			return valuePlug

		return None

	def __rowAdded( self, rowsPlug, row ) :

		## \todo Is there any benefit in finer-grained signalling?
		self.__emitModelReset()
		self.headerDataChanged.emit( QtCore.Qt.Vertical, 0, self.rowCount() )

	def __rowRemoved( self, rowsPlug, row ) :

		## \todo Is there any benefit in finer-grained signalling?
		self.__emitModelReset()

	def __columnAdded( self, cellsPlug, cellPlug ) :

		## \todo Is there any benefit in finer-grained signalling?
		self.__emitModelReset()
		self.headerDataChanged.emit( QtCore.Qt.Horizontal, 0, self.columnCount() )

	def __columnRemoved( self, cellsPlug, cellPlug ) :

		## \todo Is there any benefit in finer-grained signalling?
		self.__emitModelReset()

	def __plugDirtied( self, plug ) :

		if not self.__rowsPlug.isAncestorOf( plug ) :
			return

		parentPlug = plug.parent()
		if isinstance( parentPlug, Gaffer.Spreadsheet.RowPlug ) and plug.getName() == "enabled" :
			# Special case. The enabled plug affects the flags for the entire row.
			# Qt doesn't have a mechanism for signalling flag changes, so we emit `dataChanged`
			# instead, giving our delegate the kick it needs to redraw.
			rowIndex = parentPlug.parent().children().index( parentPlug )
			self.dataChanged.emit( self.index( rowIndex, 0 ), self.index( rowIndex, self.columnCount() - 1 ) )
			return

		# Regular case. Emit `dataChanged` for just this one plug.
		index = self.indexForPlug( plug )
		if index.isValid() :
			self.dataChanged.emit( index, index )

	def __plugMetadataChanged( self, nodeTypeId, plugPath, key, plug ) :

		if plug is None :
			return

		index = self.indexForPlug( plug )
		if not index.isValid() :
			return

		if key == "spreadsheet:columnLabel" :
			self.headerDataChanged.emit( QtCore.Qt.Horizontal, index.column(), index.column() )
		elif Gaffer.MetadataAlgo.readOnlyAffectedByChange( key ) :
			# Read-only metadata is actually reflected in `flags()`, but there's no signal to emit
			# when they change. Emitting `dataChanged` is enough to kick a redraw off.
			self.dataChanged.emit( index, index )

	def __contextChanged( self, context, key ) :

		if key.startswith( "ui:" ) :
			return

		self.__emitModelReset()

	def __emitModelReset( self ) :

		self.beginResetModel()
		self.endResetModel()

	def __formatValue( self, index, forToolTip = False ) :

		plug = self.valuePlugForIndex( index )

		if isinstance( plug, Gaffer.BoolPlug ) :
			# Dealt with via CheckStateRole
			return None

		try :
			with self.__context :
				return formatValue( plug, forToolTip )
		except :
			return None

class _PlugTableDelegate( QtWidgets.QStyledItemDelegate ) :

	def __init__( self, parent = None ) :

		QtWidgets.QStyledItemDelegate.__init__( self, parent )

	def paint( self, painter, option, index ) :

		QtWidgets.QStyledItemDelegate.paint( self, painter, option, index )

		flags = index.flags()
		enabled = flags & QtCore.Qt.ItemIsEnabled and flags & QtCore.Qt.ItemIsEditable
		cellPlugEnabled = index.data( _PlugTableModel.CellPlugEnabledRole )

		if enabled and cellPlugEnabled :
			return

		painter.save()

		painter.setRenderHint( QtGui.QPainter.Antialiasing )
		overlayColor = QtGui.QColor( 40, 40, 40, 200 )

		if not cellPlugEnabled :

			painter.fillRect( option.rect, overlayColor )

			pen = QtGui.QPen( QtGui.QColor( 20, 20, 20, 150 ) )
			pen.setWidth( 2 )
			painter.setPen( pen )
			painter.drawLine( option.rect.bottomLeft(), option.rect.topRight() )

		if not enabled :

			painter.fillRect( option.rect, overlayColor )

		painter.restore()

class _EditWindow( GafferUI.Window ) :

	# Considered private - use `_EditWindow.popupEditor()` instead.
	def __init__( self, plugValueWidget, **kw ) :

		GafferUI.Window.__init__( self, "", child = plugValueWidget, borderWidth = 8, sizeMode=GafferUI.Window.SizeMode.Automatic, **kw )

		self._qtWidget().setWindowFlags( QtCore.Qt.Popup )

		self._qtWidget().setAttribute( QtCore.Qt.WA_TranslucentBackground )
		self._qtWidget().paintEvent = Gaffer.WeakMethod( self.__paintEvent )

		self.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ), scoped = False )

	@classmethod
	def popupEditor( cls, plugOrPlugs, plugBound ) :

		if not isinstance( plugOrPlugs, ( tuple, list ) ) :
			plugOrPlugs = [ plugOrPlugs ]

		plugValueWidget = GafferUI.PlugValueWidget.create( plugOrPlugs )
		cls.__currentWindow = _EditWindow( plugValueWidget )

		if isinstance( plugValueWidget, _CellPlugValueWidget ) :
			valuePlugValueWidget = plugValueWidget.childPlugValueWidget( plugOrPlugs[0]["value"] )
			if isinstance( valuePlugValueWidget, GafferUI.PresetsPlugValueWidget ) :
				if not Gaffer.Metadata.value( next( iter( valuePlugValueWidget.getPlugs() ) ), "presetsPlugValueWidget:isCustom" ) :
					valuePlugValueWidget.menu().popup()
					return

		cls.__currentWindow.resizeToFitChild()
		windowSize = cls.__currentWindow.bound().size()
		cls.__currentWindow.setPosition( plugBound.center() - windowSize / 2 )
		cls.__currentWindow.setVisible( True )

		textWidget = cls.__textWidget( plugValueWidget )
		if textWidget is not None :
			if isinstance( textWidget, GafferUI.TextWidget ) :
				textWidget.grabFocus()
				textWidget.setSelection( 0, len( textWidget.getText() ) )
			else :
				textWidget.setFocussed( True )
			textWidget._qtWidget().activateWindow()

	def __paintEvent( self, event ) :

		painter = QtGui.QPainter( self._qtWidget() )
		painter.setRenderHint( QtGui.QPainter.Antialiasing )

		painter.setBrush( QtGui.QColor( 35, 35, 35 ) )
		painter.setPen( QtGui.QColor( 0, 0, 0, 0 ) )

		radius = self._qtWidget().layout().contentsMargins().left()
		size = self.size()
		painter.drawRoundedRect( QtCore.QRectF( 0, 0, size.x, size.y ), radius, radius )

	def __keyPress( self, widget, event ) :

		if event.key == "Return" :
			self.close()

	@classmethod
	def __textWidget( cls, plugValueWidget ) :

		def widgetUsable( w ) :
			return w.visible() and w.enabled() and w.getEditable()

		widget = None

		if isinstance( plugValueWidget, GafferUI.StringPlugValueWidget ) :
			widget = plugValueWidget.textWidget()
		elif isinstance( plugValueWidget, GafferUI.NumericPlugValueWidget ) :
			widget = plugValueWidget.numericWidget()
		elif isinstance( plugValueWidget, GafferUI.PathPlugValueWidget ) :
			widget = plugValueWidget.pathWidget()
		elif isinstance( plugValueWidget, GafferUI.MultiLineStringPlugValueWidget ) :
			widget = plugValueWidget.textWidget()

		if widget is not None and widgetUsable( widget ) :
			return widget

		for childPlug in Gaffer.Plug.Range( next( iter( plugValueWidget.getPlugs() ) ) ) :
			childWidget = plugValueWidget.childPlugValueWidget( childPlug )
			if childWidget is not None :
				childTextWidget = cls.__textWidget( childWidget )
				if childTextWidget is not None :
					return childTextWidget

		return None

# _SectionChooser
# ===============

class _SectionChooser( GafferUI.Widget ) :

	def __init__( self, rowsPlug, **kw ) :

		tabBar = QtWidgets.QTabBar()
		GafferUI.Widget.__init__( self, tabBar, **kw )

		self.__rowsPlug = rowsPlug
		self.__currentSectionChangedSignal = Gaffer.Signal1()

		tabBar.setDrawBase( False )
		tabBar.setMovable( True )
		tabBar.setExpanding( False )
		tabBar.setUsesScrollButtons( False )

		tabBar.setContextMenuPolicy( QtCore.Qt.CustomContextMenu )
		tabBar.customContextMenuRequested.connect( Gaffer.WeakMethod( self.__contextMenuRequested ) )

		tabBar.currentChanged.connect( Gaffer.WeakMethod( self.__currentChanged ) )
		self.__ignoreCurrentChanged = False
		tabBar.tabMoved.connect( Gaffer.WeakMethod( self.__tabMoved ) )
		self.__plugMetadataChangedConnection = Gaffer.Metadata.plugValueChangedSignal().connect( Gaffer.WeakMethod( self.__plugMetadataChanged ) )
		self.__rowsPlug.defaultRow()["cells"].childAddedSignal().connect( Gaffer.WeakMethod( self.__columnAdded ), scoped = False )
		self.__rowsPlug.defaultRow()["cells"].childRemovedSignal().connect( Gaffer.WeakMethod( self.__columnRemoved ), scoped = False )

		self.__updateTabs()

	def currentSection( self ) :

		if not self._qtWidget().count() :
			return None

		return self._qtWidget().tabText( self._qtWidget().currentIndex() )

	def currentSectionChangedSignal( self ) :

		return self.__currentSectionChangedSignal

	@classmethod
	def sectionNames( cls, rowsPlug ) :

		names = set()
		for cellPlug in rowsPlug.defaultRow()["cells"] :
			names.add( cls.getSection( cellPlug ) )

		if names == { "Other" } :
			# "Other" is a special section that we put columns into
			# automatically if they don't have any section metadata.
			# This helps us be robust to columns that are added directly
			# through the API by code unaware of sectioning. When _everything_
			# is in "Other", we automatically disable sectioning.
			return []

		namesAndIndices = []
		for name in sorted( list( names ) ) :
			index = len( namesAndIndices ) if name != "Other" else sys.maxsize
			metadataIndex = Gaffer.Metadata.value( rowsPlug, "spreadsheet:section:{}:index".format( name ) )
			index = metadataIndex if metadataIndex is not None else index
			namesAndIndices.append( ( name, index ) )

		namesAndIndices.sort( key = lambda x : x[1] )
		return [ x[0] for x in namesAndIndices ]

	@classmethod
	def setSection( cls, cellPlug, sectionName ) :

		rowsPlug = cellPlug.ancestor( Gaffer.Spreadsheet.RowsPlug )
		oldSectionNames = cls.sectionNames( rowsPlug )

		cls.__registerSectionMetadata( cellPlug, sectionName )

		# We may have made a new section and/or destroyed
		# an old one (by removing its last item). Reassign order
		# to put new sections where we want them, and to remove
		# gaps and old metadata.
		newSectionNames = cls.sectionNames( rowsPlug )
		if sectionName not in oldSectionNames :
			# New section created. Make sure it goes at the end, unless "Other"
			# is at the end, in which case put it in front of that.
			newSectionNames.remove( sectionName )
			if len( newSectionNames ) and newSectionNames[-1] == "Other" :
				newSectionNames.insert( -1, sectionName )
			else :
				newSectionNames.append( sectionName )

		cls.__assignSectionOrder( rowsPlug, newSectionNames )

	@classmethod
	def getSection( cls, cellPlug ) :

		return Gaffer.Metadata.value( cellPlug, "spreadsheet:section" ) or "Other"

	@classmethod
	def __registerSectionMetadata( cls, cellPlug, sectionName ) :

		if sectionName == "Other" :
			Gaffer.Metadata.deregisterValue( cellPlug, "spreadsheet:section" )
		else :
			Gaffer.Metadata.registerValue( cellPlug, "spreadsheet:section", sectionName )

	@classmethod
	def __assignSectionOrder( cls, rowsPlug, sectionNames ) :

		# Remove metadata for sections that no longer exist

		registeredValues = Gaffer.Metadata.registeredValues( rowsPlug, instanceOnly = True )
		for key in registeredValues :
			m = re.match( "spreadsheet:section:(.+):index", key )
			if m and m.group( 1 ) not in sectionNames :
				Gaffer.Metadata.deregisterValue( rowsPlug, key )

		# Register indices for existing sections

		for i, sectionName in enumerate( sectionNames ) :
			Gaffer.Metadata.registerValue(
				rowsPlug,
				"spreadsheet:section:{}:index".format( sectionName ),
				i
			)

	def __plugMetadataChanged( self, nodeTypeId, plugPath, key, plug ) :

		if plug is None :
			return

		if key == "spreadsheet:section" and self.__rowsPlug.isAncestorOf( plug ) :
			self.__updateTabs()
		elif re.match( "spreadsheet:section:.+:index", key ) and plug == self.__rowsPlug :
			self.__updateTabs()

	def __updateTabs( self ) :

		oldSectionNames = [ self._qtWidget().tabText( i ) for i in range( 0, self._qtWidget().count() ) ]
		newSectionNames = self.sectionNames( self.__rowsPlug )

		if oldSectionNames == newSectionNames :
			return

		currentSectionName = self._qtWidget().tabText( self._qtWidget().currentIndex() )

		self.__ignoreCurrentChanged = True
		try :
			while self._qtWidget().count() :
				self._qtWidget().removeTab( 0 )
			for sectionName in newSectionNames :
				self._qtWidget().addTab( sectionName )
			if currentSectionName in newSectionNames :
				self._qtWidget().setCurrentIndex( newSectionNames.index( currentSectionName ) )
			else :
				self.currentSectionChangedSignal()( self )
		finally :
			self.__ignoreCurrentChanged = False

	def __currentChanged( self, index ) :

		if not self.__ignoreCurrentChanged :
			self.currentSectionChangedSignal()( self )

	def __tabMoved( self, fromIndex, toIndex ) :

		with Gaffer.BlockedConnection( self.__plugMetadataChangedConnection ) :
			with Gaffer.UndoScope( self.__rowsPlug.ancestor( Gaffer.ScriptNode ) ) :
				for i in range( 0, self._qtWidget().count() ) :
					sectionName = self._qtWidget().tabText( i )
					Gaffer.Metadata.registerValue( self.__rowsPlug, "spreadsheet:section:{}:index".format( sectionName ), i )

	def __columnAdded( self, cellsPlug, cellPlug ) :

		self.__updateTabs()

	def __columnRemoved( self, cellsPlug, cellPlug ) :

		self.__updateTabs()

	def __renameSection( self, sectionName ) :

		sectionNames = self.sectionNames( self.__rowsPlug )
		assert( sectionName in sectionNames )
		sectionIsCurrent = self._qtWidget().tabText( self._qtWidget().currentIndex() ) == sectionName

		newSectionName = GafferUI.TextInputDialogue(
			title = "Rename section",
			initialText = sectionName,
			confirmLabel = "Rename",
		).waitForText( parentWindow = self.ancestor( GafferUI.Window ) )

		if not newSectionName or newSectionName == sectionName :
			return

		if newSectionName in sectionNames :
			for suffix in range( 1, len( sectionNames ) + 2 ) :
				suffixedSectionName = newSectionName + str( suffix )
				if suffixedSectionName not in sectionNames :
					newSectionName = suffixedSectionName
					break

		with Gaffer.UndoScope( self.__rowsPlug.ancestor( Gaffer.ScriptNode ) ) :

			# Move appropriate columns to renamed section
			for cellPlug in self.__rowsPlug.defaultRow()["cells"] :
				if self.getSection( cellPlug ) == sectionName :
					# Using `__registerSectionMetadata()` rather than `setSection()`
					# because we call `__assignSectionOrder()` ourselves.
					self.__registerSectionMetadata( cellPlug, newSectionName )

			# Reapply section order for renamed section.
			self.__assignSectionOrder(
				self.__rowsPlug,
				[ newSectionName if n == sectionName else n for n in sectionNames ]
			)

			# And choose the renamed tab if necessary.
			if sectionIsCurrent :
				self._qtWidget().setCurrentIndex( sectionNames.index( sectionName ) )

	def __deleteSection( self, sectionName ) :

		sectionNames = self.sectionNames( self.__rowsPlug )

		with Gaffer.UndoScope( self.__rowsPlug.ancestor( Gaffer.ScriptNode ) ) :
			# Iterate in reverse to avoid invalidating column indices we're
			# about to visit.
			for columnIndex, cellPlug in reversed( list( enumerate( self.__rowsPlug.defaultRow()["cells"] ) ) ) :
				if self.getSection( cellPlug ) == sectionName :
					self.__rowsPlug.removeColumn( columnIndex )
			# Reassign section indices to remove gap.
			self.__assignSectionOrder(
				self.__rowsPlug,
				[ n for n in sectionNames if n != sectionName ]
			)

	def __moveSection( self, fromSectionName, toSectionName ) :

		sectionNames = self.sectionNames( self.__rowsPlug )
		sectionIsCurrent = self._qtWidget().tabText( self._qtWidget().currentIndex() ) == fromSectionName

		with Gaffer.UndoScope( self.__rowsPlug.ancestor( Gaffer.ScriptNode ) ) :

			# Move columns
			for cellPlug in self.__rowsPlug.defaultRow()["cells"] :
				if self.getSection( cellPlug ) == fromSectionName :
					# Using `__registerSectionMetadata()` rather than `setSection()`
					# because we call `__assignSectionOrder()` ourselves.
					self.__registerSectionMetadata( cellPlug, toSectionName )

			# Reapply section order to remove gaps.
			newSectionNames = [ n for n in sectionNames if n != fromSectionName ]
			self.__assignSectionOrder( self.__rowsPlug, newSectionNames )

			if sectionIsCurrent :
				self._qtWidget().setCurrentIndex( newSectionNames.index( toSectionName ) )

	def __removeSectioning( self ) :

		with Gaffer.UndoScope( self.__rowsPlug.ancestor( Gaffer.ScriptNode ) ) :

			for cellPlug in self.__rowsPlug.defaultRow()["cells"] :
				# Using `__registerSectionMetadata()` rather than `setSection()`
				# because we call `__assignSectionOrder()` ourselves.
				self.__registerSectionMetadata( cellPlug, "Other" )

			self.__assignSectionOrder( self.__rowsPlug, [] )

	def __contextMenuRequested( self, pos ) :

		m = IECore.MenuDefinition()
		sectionName = self._qtWidget().tabText( self._qtWidget().tabAt( pos ) )

		m.append(
			"/Rename",
			{
				"command" : functools.partial( Gaffer.WeakMethod( self.__renameSection ), sectionName )
			}
		)

		sectionNames = self.sectionNames( self.__rowsPlug )
		for toSectionName in sectionNames :
			m.append(
				"/Move Columns To/{}".format( toSectionName ),
				{
					"command" : functools.partial( Gaffer.WeakMethod( self.__moveSection ), sectionName, toSectionName ),
					"active" : toSectionName != sectionName,
				}
			)

		m.append( "/__DeleteDivider__", { "divider" : True } )

		m.append(
			"/Delete",
			{
				"command" : functools.partial( Gaffer.WeakMethod( self.__deleteSection ), sectionName )
			}
		)

		m.append( "/__RemoveDivider__", { "divider" : True } )

		m.append(
			"/Remove Sectioning",
			{
				"command" : functools.partial( Gaffer.WeakMethod( self.__removeSectioning ) )
			}
		)

		self.__contextMenu = GafferUI.Menu( m )
		self.__contextMenu.popup( parent = self )

# ScrolledContainer linking
# =========================
#
# To keep the row and column names and default cells visible at all times, we
# need to house them in separate table views from the main one. But we
# want to link the scrolling of them all, so they still act as a unit. We achieve
# this using the _LinkedScrollBar widget, which provides two-way coupling between
# the scrollbars of each container.

class _LinkedScrollBar( GafferUI.Widget ) :

	def __init__( self, orientation, scrolledContainers, **kw ) :

		GafferUI.Widget.__init__(
			self,
			_StepsChangedScrollBar(
				QtCore.Qt.Orientation.Horizontal if orientation == GafferUI.ListContainer.Orientation.Horizontal else QtCore.Qt.Orientation.Vertical
			),
			**kw
		)

		self.__scrollBars = [ self._qtWidget() ]
		for container in scrolledContainers :
			if orientation == GafferUI.ListContainer.Orientation.Horizontal :
				if not isinstance( container._qtWidget().horizontalScrollBar(), _StepsChangedScrollBar ) :
					container._qtWidget().setHorizontalScrollBar( _StepsChangedScrollBar( QtCore.Qt.Orientation.Horizontal ) )
				self.__scrollBars.append( container._qtWidget().horizontalScrollBar() )
			else :
				if not isinstance( container._qtWidget().verticalScrollBar(), _StepsChangedScrollBar ) :
					container._qtWidget().setVerticalScrollBar( _StepsChangedScrollBar( QtCore.Qt.Orientation.Vertical ) )
				self.__scrollBars.append( container._qtWidget().verticalScrollBar() )

		# Set size policy to `Ignored` in the direction of scrolling, so sizing is determined entirely
		# by the `scrolledContainers`. Otherwise, showing the scrollbar in `__rangeChanged` can lead to
		# another change of range, making an infinite loop where the scrollbar flickers on and off.
		if orientation == GafferUI.ListContainer.Orientation.Vertical :
			self._qtWidget().setSizePolicy( QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Ignored )
		else :
			self._qtWidget().setSizePolicy( QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Fixed )

		self._qtWidget().setValue( self.__scrollBars[1].value() )
		self._qtWidget().setRange( self.__scrollBars[1].minimum(), self.__scrollBars[1].maximum() )
		self._qtWidget().setPageStep( self.__scrollBars[1].pageStep() )
		self._qtWidget().setSingleStep( self.__scrollBars[1].singleStep() )
		self.setVisible( self._qtWidget().minimum() != self._qtWidget().maximum() )

		for scrollBar in self.__scrollBars :
			scrollBar.valueChanged.connect( Gaffer.WeakMethod( self.__valueChanged ) )
			scrollBar.rangeChanged.connect( Gaffer.WeakMethod( self.__rangeChanged ) )
			scrollBar.stepsChanged.connect( Gaffer.WeakMethod( self.__stepsChanged ) )

	def __valueChanged( self, value ) :

		for scrollBar in self.__scrollBars :
			scrollBar.setValue( value )

	def __rangeChanged( self, min, max ) :

		for scrollBar in self.__scrollBars :
			scrollBar.setRange( min, max )

		self.setVisible( min != max )

	def __stepsChanged( self, page, single ) :

		for scrollBar in self.__scrollBars :
			scrollBar.setPageStep( page )
			scrollBar.setSingleStep( single )

# QScrollBar provides signals for when the value and range are changed,
# but not for when the page step is changed. This subclass adds the missing
# signal.
class _StepsChangedScrollBar( QtWidgets.QScrollBar ) :

	stepsChanged = QtCore.Signal( int, int )

	def __init__( self, orientation, parent = None ) :

		QtWidgets.QScrollBar.__init__( self, orientation, parent )

	def sliderChange( self, change ) :

		QtWidgets.QScrollBar.sliderChange( self, change )

		if change == self.SliderStepsChange :
			self.stepsChanged.emit( self.pageStep(), self.singleStep() )

# Plug context menu
# =================

def __setPlugValue( plug, value ) :

	with Gaffer.UndoScope( plug.ancestor( Gaffer.ScriptNode ) ) :
		plug.setValue( value )

def __deleteRow( rowPlug ) :

	with Gaffer.UndoScope( rowPlug.ancestor( Gaffer.ScriptNode ) ) :
		rowPlug.parent().removeChild( rowPlug )

def __setRowNameWidth( rowPlug, width, *unused ) :

	with Gaffer.UndoScope( rowPlug.ancestor( Gaffer.ScriptNode ) ) :
		_setRowNameWidth( rowPlug.parent(), width )

def __prependRowAndCellMenuItems( menuDefinition, plugValueWidget ) :

	plug = plugValueWidget.getPlug()
	rowPlug = plug.ancestor( Gaffer.Spreadsheet.RowPlug )
	if rowPlug is None :
		return

	isDefaultRow = rowPlug == rowPlug.parent().defaultRow()

	def ensureDivider() :
		if menuDefinition.item( "/__SpreadsheetRowAndCellDivider__" ) is None :
			menuDefinition.prepend( "/__SpreadsheetRowAndCellDivider__", { "divider" : True } )

	# Row menu items

	if plug.parent() == rowPlug and not isDefaultRow :

		ensureDivider()

		menuDefinition.prepend(
			"/Delete Row",
			{
				"command" : functools.partial( __deleteRow, rowPlug ),
				"active" : (
					not plugValueWidget.getReadOnly() and
					not Gaffer.MetadataAlgo.readOnly( rowPlug ) and
					_dimensionsEditable( rowPlug.parent() )
				)
			}
		)

		widths = [
			( "Half", GafferUI.PlugWidget.labelWidth() * 0.5 ),
			( "Single", GafferUI.PlugWidget.labelWidth() ),
			( "Double", GafferUI.PlugWidget.labelWidth() * 2 ),
		]

		currentWidth = _getRowNameWidth( rowPlug.parent() )
		for label, width in reversed( widths ) :
			menuDefinition.prepend(
				"/Width/{}".format( label ),
				{
					"command" : functools.partial( __setRowNameWidth, rowPlug, width ),
					"active" : not plugValueWidget.getReadOnly() and not Gaffer.MetadataAlgo.readOnly( rowPlug ),
					"checkBox" : width == currentWidth,
				}
			)

	# Cell menu items

	cellPlug = plug if isinstance( plug, Gaffer.Spreadsheet.CellPlug ) else plug.ancestor( Gaffer.Spreadsheet.CellPlug )
	if cellPlug is not None :

		if not isDefaultRow or "enabled" not in cellPlug :

			ensureDivider()

			enabled = None
			enabledPlug = cellPlug.enabledPlug()
			with plugValueWidget.getContext() :
				with IECore.IgnoredExceptions( Gaffer.ProcessException ) :
					enabled = enabledPlug.getValue()

			menuDefinition.prepend(
				"/Disable Cell" if enabled else "/Enable Cell",
				{
					"command" : functools.partial( __setPlugValue, enabledPlug, not enabled ),
					"active" : not plugValueWidget.getReadOnly() and not Gaffer.MetadataAlgo.readOnly( enabledPlug ) and enabledPlug.settable()
				}
			)

def __addColumn( spreadsheet, plug ) :

	# We allow the name of a column to be overridden by metadata, so that NameValuePlug and
	# TweakPlug can provide more meaningful names than "name" or "enabled" when their child
	# plugs are added to spreadsheets.
	columnName = Gaffer.Metadata.value( plug, "spreadsheet:columnName" ) or plug.getName()

	# If the plug already has a child `enabled` plug, then we always adopt
	# it to enable the cell. This makes for a much simpler user experience
	# for NameValuePlugs and TweakPlugs. In an ideal world we would have
	# made this the standard behaviour from the start.
	adoptEnabledPlug = isinstance( plug.getChild( "enabled" ), Gaffer.BoolPlug )

	# Rows plug may have been promoted, in which case we need to edit
	# the source, which will automatically propagate the new column to
	# the spreadsheet.
	rowsPlug = spreadsheet["rows"].source()
	columnIndex = rowsPlug.addColumn( plug, columnName, adoptEnabledPlug )
	valuePlug = rowsPlug.defaultRow()["cells"][columnIndex]["value"]
	Gaffer.MetadataAlgo.copy( plug, valuePlug, exclude = "spreadsheet:columnName layout:* deletable" )

	return columnIndex

def __createSpreadsheet( plug ) :

	spreadsheet = Gaffer.Spreadsheet()
	__addColumn( spreadsheet, plug )
	spreadsheet["rows"].addRow()

	if isinstance( plug.node(), Gaffer.ScriptNode ) :
		spreadsheetParent = plug.node()
		Gaffer.Metadata.registerValue( spreadsheet, "nodeGadget:type", "GafferUI::StandardNodeGadget" )
	else :
		spreadsheetParent = plug.node().parent()

	with Gaffer.UndoScope( plug.ancestor( Gaffer.ScriptNode ) ) :
		spreadsheetParent.addChild( spreadsheet )
		plug.setInput( spreadsheet["out"][0] )

	GafferUI.NodeEditor.acquire( spreadsheet )

def __addToSpreadsheet( plug, spreadsheet, sectionName = None ) :

	with Gaffer.UndoScope( spreadsheet.ancestor( Gaffer.ScriptNode ) ) :
		columnIndex = __addColumn( spreadsheet, plug )
		if sectionName is not None :
			_SectionChooser.setSection(
				spreadsheet["rows"].defaultRow()["cells"][columnIndex].source(),
				sectionName
			)
		plug.setInput( spreadsheet["out"][columnIndex] )

def __spreadsheetSubMenu( plug, command, showSections = True ) :

	menuDefinition = IECore.MenuDefinition()

	if isinstance( plug.node(), Gaffer.ScriptNode ) :
		spreadsheetParent = plug.node()
	else :
		spreadsheetParent = plug.node().parent()

	alreadyConnected = []
	other = []
	for spreadsheet in Gaffer.Spreadsheet.Range( spreadsheetParent ) :

		if spreadsheet == plug.ancestor( Gaffer.Spreadsheet ) :
			continue

		connected = False
		for output in spreadsheet["out"] :
			for destination in output.outputs() :
				if destination.node() == plug.node() :
					connected = True
					break
			if connected :
				break

		if connected :
			alreadyConnected.append( spreadsheet )
		else :
			other.append( spreadsheet )

	if not alreadyConnected and not other :
		menuDefinition.append(
			"/No Spreadsheets Available",
			{
				"active" : False,
			}
		)
		return menuDefinition

	alreadyConnected.sort( key = Gaffer.GraphComponent.getName )
	other.sort( key = Gaffer.GraphComponent.getName )

	def addItems( spreadsheet ) :

		sectionNames = _SectionChooser.sectionNames( spreadsheet["rows"].source() ) if showSections else None
		if sectionNames :

			for sectionName in sectionNames :

				menuDefinition.append(
					"/{}/{}".format( spreadsheet.getName(), sectionName ),
					{
						"command" : functools.partial( command, spreadsheet, sectionName )
					}
				)

		else :

			menuDefinition.append(
				"/" + spreadsheet.getName(),
				{
					"command" : functools.partial( command, spreadsheet )
				}
			)

	if alreadyConnected and other :
		menuDefinition.append( "/__ConnectedDivider__", { "divider" : True, "label" : "Connected" } )

	for spreadsheet in alreadyConnected :
		addItems( spreadsheet )

	if alreadyConnected and other :
		menuDefinition.append( "/__OtherDivider__", { "divider" : True, "label" : "Other" } )

	for spreadsheet in other :
		addItems( spreadsheet )

	return menuDefinition

def __prependSpreadsheetCreationMenuItems( menuDefinition, plugValueWidget ) :

	plug = plugValueWidget.getPlug()
	if not isinstance( plug, Gaffer.ValuePlug ) :
		return

	node = plug.node()
	if node is None or node.parent() is None :
		return

	if plug.getInput() is not None or not plugValueWidget._editable() or Gaffer.MetadataAlgo.readOnly( plug ) :
		return

	plugsAndSuffixes = [ ( plug, "" ) ]

	ancestorPlug = plug.parent()
	while isinstance( ancestorPlug, Gaffer.Plug ) :

		if any( p.getInput() is not None for p in Gaffer.Plug.RecursiveRange( ancestorPlug ) ) :
			break

		if Gaffer.Metadata.value( ancestorPlug, "spreadsheet:plugMenu:includeAsAncestor" ) :
			label = Gaffer.Metadata.value( ancestorPlug, "spreadsheet:plugMenu:ancestorLabel" )
			label = label or ancestorPlug.typeName().rpartition( ":" )[2]
			plugsAndSuffixes.append( ( ancestorPlug, " ({})".format( label ) ) )

		ancestorPlug = ancestorPlug.parent()

	for plug, suffix in reversed( plugsAndSuffixes ) :

		menuDefinition.prepend( "/__SpreadsheetCreationDivider__" + suffix, { "divider" : True } )

		menuDefinition.prepend(
			"/Add to Spreadsheet{}".format( suffix ),
			{
				"subMenu" :  functools.partial( __spreadsheetSubMenu, plug, functools.partial( __addToSpreadsheet, plug ) )
			}
		)
		menuDefinition.prepend(
			"/Create Spreadsheet{}...".format( suffix ),
			{
				"command" : functools.partial( __createSpreadsheet, plug )
			}
		)

def __plugPopupMenu( menuDefinition, plugValueWidget ) :

	## \todo We're prepending rather than appending so that we get the ordering we
	# want with respect to the Expression menu items. Really we need external control
	# over this ordering.
	__prependRowAndCellMenuItems( menuDefinition, plugValueWidget )
	__prependSpreadsheetCreationMenuItems( menuDefinition, plugValueWidget )

GafferUI.PlugValueWidget.popupMenuSignal().connect( __plugPopupMenu, scoped = False )

for plugType in ( Gaffer.TransformPlug, Gaffer.Transform2DPlug ) :
	Gaffer.Metadata.registerValue( plugType, "spreadsheet:plugMenu:includeAsAncestor", True )
	Gaffer.Metadata.registerValue( plugType, "spreadsheet:plugMenu:ancestorLabel", "Transform" )

# NodeEditor tool menu
# ====================

def __createSpreadsheetForNode( node, activeRowNamesConnection, selectorContextVariablePlug, selectorValue, menu ) :

	with Gaffer.UndoScope( node.scriptNode() ) :

		spreadsheet = Gaffer.Spreadsheet( node.getName() + "Spreadsheet" )
		__connectPlugToRowNames( activeRowNamesConnection, selectorContextVariablePlug, selectorValue, spreadsheet, menu )
		node.parent().addChild( spreadsheet )

	GafferUI.NodeEditor.acquire( spreadsheet )

def __connectPlugToRowNames( activeRowNamesConnection, selectorContextVariablePlug, selectorValue, spreadsheet, menu ) :

	node = activeRowNamesConnection.node()

	# We defer locking the plug until we know we're going ahead
	lockSelectorVarPlug = False
	if selectorValue is None :
		selectorValue = "${" + selectorContextVariablePlug.getValue() + "}"
		lockSelectorVarPlug = True

	# Check that the sheet's selector meets requirements before making any changes

	existingSelector = spreadsheet["selector"].getValue()
	if existingSelector and selectorValue and existingSelector != selectorValue :

		message = "{sheetName}'s selector is set to: '{sheetSelector}'.\n\n" + \
			"The '{plugName}' plug requires a different selector to work\n" + \
			"properly. Continuing will reset the selector to '{selector}'."

		confirm = GafferUI.ConfirmationDialogue(
			"Invalid Selector",
			message.format(
				sheetName = spreadsheet.getName(), sheetSelector = existingSelector,
				plugName = activeRowNamesConnection.getName(), selector = selectorValue
			),
			confirmLabel = "Continue"
		)

		if not confirm.waitForConfirmation( parentWindow = menu.ancestor( GafferUI.Window ) ) :
			return

	with Gaffer.UndoScope( node.scriptNode() ) :

		if lockSelectorVarPlug :
			Gaffer.MetadataAlgo.setReadOnly( selectorContextVariablePlug, True )

		if selectorValue :
			spreadsheet["selector"].setValue( selectorValue )
			Gaffer.MetadataAlgo.setReadOnly( spreadsheet["selector"], True )

		with node.scriptNode().context() :
			rowNames = activeRowNamesConnection.getValue()
		activeRowNamesConnection.setInput( spreadsheet["activeRowNames"] )

		if rowNames :
			for rowName in rowNames :
				spreadsheet["rows"].addRow()["name"].setValue( rowName )
		else :
			# Only a new row to an empty spreadsheet
			if len( spreadsheet["rows"].children() ) == 1 :
				spreadsheet["rows"].addRow()

		node.parent().addChild( spreadsheet )

def __nodeEditorToolMenu( nodeEditor, node, menuDefinition ) :

	if node.parent() is None :
		return

	activeRowNamesConnection = Gaffer.Metadata.value( node, "ui:spreadsheet:activeRowNamesConnection" )
	if not activeRowNamesConnection :
		return
	else :
		activeRowNamesConnection = node.descendant( activeRowNamesConnection )
		assert( activeRowNamesConnection is not None )

	selectorContextVariablePlug = Gaffer.Metadata.value( node, "ui:spreadsheet:selectorContextVariablePlug" )
	if selectorContextVariablePlug :
		selectorContextVariablePlug = node.descendant( selectorContextVariablePlug )
		assert( selectorContextVariablePlug is not None )

	selectorValue = Gaffer.Metadata.value( node, "ui:spreadsheet:selectorValue" )
	assert( not ( selectorValue and selectorContextVariablePlug ) )

	menuDefinition.append( "/SpreadsheetDivider", { "divider" : True } )

	itemsActive = (
		not nodeEditor.getReadOnly()
		and not Gaffer.MetadataAlgo.readOnly( node )
		and not Gaffer.MetadataAlgo.readOnly( activeRowNamesConnection )
		and activeRowNamesConnection.getInput() is None
	)

	menuDefinition.append(
		"/Create Spreadsheet...",
		{
			"command" : functools.partial( __createSpreadsheetForNode, node, activeRowNamesConnection, selectorContextVariablePlug, selectorValue ),
			"active" : itemsActive
		}
	)

	connectCommand = functools.partial( __connectPlugToRowNames, activeRowNamesConnection, selectorContextVariablePlug, selectorValue )
	menuDefinition.append(
		"/Connect to Spreadsheet",
		{
			"subMenu" :  functools.partial( __spreadsheetSubMenu, activeRowNamesConnection, connectCommand, showSections = False ),
			"active" : itemsActive
		}
	)

GafferUI.NodeEditor.toolMenuSignal().connect( __nodeEditorToolMenu, scoped = False )

# Utility in the spirit of `all()` and `any()`. If all values in `sequence`
# are equal, returns that value, otherwise returns `None`.
## \todo Copied from Gaffer.PlugValueWidget. Is there somewhere more sensible we can put this? Cortex perhaps?
def sole( sequence ) :

	result = None
	for i, v in enumerate( sequence ) :
		if i == 0 :
			result = v
		elif v != result :
			return None

	return result
