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

			"noduleLayout:visible", False,

		],

		"selector" : [

			"description",
			"""
			The value that the row names will be matched against.
			Typically this will refer to a context variable using
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

def __defaultRowMetadata( rowPlug, key ) :

	rowsPlug = rowPlug.parent()
	return Gaffer.Metadata.value( rowsPlug["default"], key )

for key in [ "spreadsheet:rowNameWidthScale" ] :

	Gaffer.Metadata.registerValue(
		Gaffer.Spreadsheet.RowsPlug, "row*", key,
		functools.partial( __defaultRowMetadata, key = key )
	)

def __correspondingDefaultPlug( plug ) :

	rowPlug = plug.ancestor( Gaffer.Spreadsheet.RowPlug )
	rowsPlug = rowPlug.parent()
	return rowsPlug["default"].descendant( plug.relativeName( rowPlug ) )

def __defaultCellMetadata( plug, key ) :

	return Gaffer.Metadata.value( __correspondingDefaultPlug( plug ), key )

for key in [ "spreadsheet:columnLabel", "spreadsheet:columnWidthScale", "plugValueWidget:type" ] :

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

# Size constraints and spacing
# ============================
#
# Because the headings, row names, default cells and regular cells of our spreadsheet
# are all housed in different containers, we need to be careful that their sizes line
# up so that rows and columns align correctly between the containers. We achieve this
# by forcing fixed sizes onto the various UI elements. Some widget types just aren't
# suited for viewing in a spreadsheet, so we fall back to displaying a proxy widget
# for anything we haven't whitelisted.

_rowHeight = 25
_rowNameWidth = 150

def _cellWidthAndProxy( cellPlug ) :

	additionalWidth = 0
	valuePlug = cellPlug["value"]
	if isinstance( cellPlug["value"], Gaffer.NameValuePlug ) :
		valuePlug = cellPlug["value"]["value"] # determine width from value plug
		additionalWidth = 25 # add space for the switch

	plugValueWidgetType = Gaffer.Metadata.value( valuePlug, "plugValueWidget:type" )
	widthScale = Gaffer.Metadata.value( cellPlug, "spreadsheet:columnWidthScale" ) or 1

	width = {

		Gaffer.BoolPlug : 60,
		Gaffer.IntPlug : 60,
		Gaffer.FloatPlug : 60,

		"GafferUI.PresetsPlugValueWidget" : 100,
		"GafferUI.StringPlugValueWidget" : 120,
		"GafferUI.FileSystemPathPlugValueWidget" : 120,
		# It's a bit naughty to refer to GafferSceneUI here.
		# If we have other use cases, perhaps we should have
		# a public method to allow the registration of supported
		# widgets and their default widths.
		"GafferSceneUI.ScenePathPlugValueWidget" : 120,
		Gaffer.StringPlug : 120,

		Gaffer.V2iPlug : 120,
		Gaffer.V2fPlug : 120,

		Gaffer.V3iPlug : 180,
		Gaffer.V3fPlug : 180,

		"GafferUI.ColorSwatchPlugValueWidget" : 60,
		Gaffer.Color3fPlug : 200,
		Gaffer.Color4fPlug : 260,

	}.get( plugValueWidgetType or valuePlug.__class__  )

	return ( width * widthScale + additionalWidth, False ) if width is not None else ( 60 * widthScale, True )

def _applyFixedSize( widget, width, height ) :

	layout = widget._qtWidget().layout()
	if layout is not None :
		layout.setSizeConstraint( QtWidgets.QLayout.SetNoConstraint )
	widget._qtWidget().setFixedSize( width, height )

_widthScales = [
	( "Half", 0.5 ),
	( "Single", 1 ),
	( "Double", 2 ),
]

# Widgets
# =======

class _RowsPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug ) :

		grid = GafferUI.GridContainer()

		GafferUI.PlugValueWidget.__init__( self, grid, plug )

		with grid :

			with GafferUI.ScrolledContainer(
				horizontalMode = GafferUI.ScrollMode.Never,
				verticalMode = GafferUI.ScrollMode.Never,
				parenting = {
					"index" : ( 1, 0 ),
				}
			) as columnHeadingsScrolledContainer :

				_LinearLayoutPlugValueWidget( plug["default"]["cells"], childWidgetType = _HeaderPlugValueWidget, orientation = GafferUI.ListContainer.Orientation.Horizontal )

			columnHeadingsScrolledContainer._qtWidget().setFixedHeight( _rowHeight )

			GafferUI.Label(
				"Default  ",
				parenting = {
					"index" : ( 0, 1 ),
					"alignment" : ( GafferUI.HorizontalAlignment.Left, GafferUI.VerticalAlignment.None ),
				}
			)

			with GafferUI.ScrolledContainer(
				horizontalMode = GafferUI.ScrollMode.Never,
				verticalMode = GafferUI.ScrollMode.Never,
				parenting = {
					"index" : ( 1, 1 ),
				}
			) as defaultRowScrolledContainer :

				_LinearLayoutPlugValueWidget( plug["default"]["cells"], childWidgetType = _CellPlugValueWidget, orientation = GafferUI.ListContainer.Orientation.Horizontal )

			defaultRowScrolledContainer._qtWidget().setFixedHeight( _rowHeight )

			GafferUI.Divider( GafferUI.Divider.Orientation.Horizontal, parenting = { "index" : ( slice( 0, 3 ), 2 ) } )

			with GafferUI.ScrolledContainer(
				horizontalMode = GafferUI.ScrollMode.Never,
				verticalMode = GafferUI.ScrollMode.Never,
				parenting = {
					"index" : ( 0, 3 ),
				}
			) as self.__rowNamesScrolledContainer :

				self.__rowNamesPlugValueWidget = _LinearLayoutPlugValueWidget( plug, childWidgetType = _RowNamePlugValueWidget )

			self.__updateRowNamesWidth()

			with GafferUI.ScrolledContainer(
				horizontalMode = GafferUI.ScrollMode.Never,
				verticalMode = GafferUI.ScrollMode.Never,
				parenting = {
					"index" : ( 1, 3 ),
				}
			) as cellsScrolledContainer :

				_LinearLayoutPlugValueWidget( plug, childWidgetType = _RowCellsPlugValueWidget )

			_LinkedScrollBar(
				GafferUI.ListContainer.Orientation.Vertical, [ cellsScrolledContainer, self.__rowNamesScrolledContainer ],
				parenting = {
					"index" : ( 2, 3 ),
				}
			)

			_LinkedScrollBar(
				GafferUI.ListContainer.Orientation.Horizontal, [ cellsScrolledContainer, columnHeadingsScrolledContainer, defaultRowScrolledContainer ],
				parenting = {
					"index" : ( 1, 4 ),
				}
			)

			with GafferUI.ListContainer(
				orientation = GafferUI.ListContainer.Orientation.Horizontal,
				parenting = {
					"index" : ( 0, 4 ),
					"alignment" : ( GafferUI.HorizontalAlignment.Left, GafferUI.VerticalAlignment.Top ),
				},
			) :

				addRowButton = GafferUI.Button( image="plus.png", hasFrame=False, toolTip = "Click to add row, or drop new row names" )
				addRowButton.clickedSignal().connect( Gaffer.WeakMethod( self.__addRowButtonClicked ), scoped = False )
				addRowButton.dragEnterSignal().connect( Gaffer.WeakMethod( self.__addRowButtonDragEnter ), scoped = False )
				addRowButton.dragLeaveSignal().connect( Gaffer.WeakMethod( self.__addRowButtonDragLeave ), scoped = False )
				addRowButton.dropSignal().connect( Gaffer.WeakMethod( self.__addRowButtonDrop ), scoped = False )

			self.__statusLabel = GafferUI.Label( "", parenting = { "index" : ( slice( 1, 5 ), 5 ) } )

			# Allow a final invisible column and row to stretch. There must be better ways, but this is the only
			# way I could find to stop the actual content columns from stretching.
			GafferUI.Spacer( imath.V2i( 0 ), parenting = { "index" : ( 3, 6 ) } )
			grid._qtWidget().layout().setColumnStretch( 4, 1 )
			grid._qtWidget().layout().setRowStretch( 6, 1 )

		_CellPlugValueWidget.currentCellChangedSignal().connect( Gaffer.WeakMethod( self.__currentCellChanged ), scoped = False )
		for widget in [ addRowButton ] :
			widget.enterSignal().connect( Gaffer.WeakMethod( self.__enterToolTippedWidget ), scoped = False )
			widget.leaveSignal().connect( Gaffer.WeakMethod( self.__leaveToolTippedWidget ), scoped = False )

		Gaffer.Metadata.plugValueChangedSignal().connect( Gaffer.WeakMethod( self.__plugMetadataChanged ), scoped = False )

	def hasLabel( self ) :

		return True

	def _updateFromPlug( self ) :

		pass

	def __addRowButtonClicked( self, *unused ) :

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			row = self.getPlug().addRow()

		# Select new row for editing. Have to do this on idle as otherwise the scrollbars
		# flicker on and off.
		GafferUI.EventLoop.addIdleCallback( functools.partial( self.__editNewRow, row ) )

	def __editNewRow( self, row ) :

		rowWidget = self.__rowNamesPlugValueWidget.childPlugValueWidget( row, lazy = False )
		rowNameWidget = rowWidget.childPlugValueWidget( row["name"] )
		rowNameWidget.textWidget().grabFocus()

		# Scroll to show row. Have to do this on idle so it comes after lazy creation of
		# the new cells row, otherwise the offset is wrong.
		GafferUI.EventLoop.addIdleCallback( rowNameWidget.reveal )

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

	def __currentCellChanged( self, cell ) :

		status = ""
		if cell is not None and self.isAncestorOf( cell ) :
			rowPlug = cell.getPlug().ancestor( Gaffer.Spreadsheet.RowPlug )
			if rowPlug.getName() == "default" :
				rowName = "Default"
			else :
				with self.getContext() :
					rowName = rowPlug["name"].getValue() or "unnamed"

			status = "Row : {}, Column : {}".format(
				rowName,
				IECore.CamelCase.toSpaced( cell.getPlug().getName() ),
			)

		self.__statusLabel.setText( status )

	def __enterToolTippedWidget( self, widget ) :

		self.__statusLabel.setText( widget.getToolTip() )

	def __leaveToolTippedWidget( self, widget ) :

		self.__statusLabel.setText( "" )

	def __updateRowNamesWidth( self ) :

		scale = Gaffer.Metadata.value( self.getPlug()["default"], "spreadsheet:rowNameWidthScale" ) or 1
		self.__rowNamesScrolledContainer._qtWidget().setFixedWidth( _rowNameWidth * scale )

	def __plugMetadataChanged( self, nodeTypeId, plugPath, key, plug ) :

		if plug is not None and key == "spreadsheet:rowNameWidthScale" :
			if self.getPlug().isAncestorOf( plug ) :
				self.__updateRowNamesWidth()

GafferUI.PlugValueWidget.registerType( Gaffer.Spreadsheet.RowsPlug, _RowsPlugValueWidget )

class _LinearLayoutPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, childWidgetType, orientation = GafferUI.ListContainer.Orientation.Vertical, spacing = 0, **kw ) :

		self.__container = GafferUI.ListContainer( orientation = orientation, spacing = spacing )
		GafferUI.PlugValueWidget.__init__( self, self.__container, plug, **kw )

		self.__childWidgetType = childWidgetType
		self.__widgets = {}

		plug.childAddedSignal().connect( Gaffer.WeakMethod( self.__childAddedOrRemoved ), scoped = False )
		plug.childRemovedSignal().connect( Gaffer.WeakMethod( self.__childAddedOrRemoved ), scoped = False )

		self.__updateLayout()

	def hasLabel( self ) :

		return True

	## \todo The `lazy = True` default comes from the PlugValueWidget base class, but
	# I don't think the argument is useful at all. Confirm, and remove argument from
	# all implementations.
	def childPlugValueWidget( self, childPlug, lazy=True ) :

		if not lazy :
			self.__updateLayout.flush( self )

		return self.__widgets.get( childPlug )

	def _updateFromPlug( self ) :

		pass

	@GafferUI.LazyMethod()
	def __updateLayout( self ) :

		# Build layout

		layout = []
		for index, child in enumerate( Gaffer.Plug.Range( self.getPlug() ) ) :

			if isinstance( child, Gaffer.Spreadsheet.RowPlug ) and index == 0 :
				# Ignore the default row, since this is shown separately.
				continue

			widget = self.__widgets.get( child )
			if widget is None :
				widget = self.__childWidgetType( child )
				self.__widgets[child] = widget

			if hasattr( widget, "setAlternate" ) :
				widget.setAlternate( len( layout ) % 2 )

			layout.append( widget )

		# Ditch old widgets we don't need and update our container

		layoutSet = set( layout )
		self.__widgets = { k : v for k, v in self.__widgets.items() if v in layoutSet }
		self.__container[:] = layout

	def __childAddedOrRemoved( self, *unused ) :

		self.__updateLayout()

class _RowNamePlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug ) :

		row = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 )
		row._qtWidget().setFixedHeight( _rowHeight )
		row._qtWidget().layout().setSizeConstraint( QtWidgets.QLayout.SetNoConstraint )

		GafferUI.PlugValueWidget.__init__( self, row, plug )
		with row :

				self.__namePlugValueWidget = GafferUI.StringPlugValueWidget( plug["name"] )
				self.__enabledPlugValueWidget = GafferUI.BoolPlugValueWidget( plug["enabled"], displayMode = GafferUI.BoolWidget.DisplayMode.Switch )

		self._updateFromPlug()

	def hasLabel( self ) :

		return True

	def childPlugValueWidget( self, childPlug, lazy=True ) :

		if childPlug == self.getPlug()["name"] :
			return self.__namePlugValueWidget
		elif childPlug == self.getPlug()["enabled"] :
			return self.__enabledPlugValueWidget

		return None

	def setReadOnly( self, readOnly ) :

		if readOnly == self.getReadOnly() :
			return

		GafferUI.PlugValueWidget.setReadOnly( self, readOnly )

		self.__namePlugValueWidget.setReadOnly( self, readOnly )
		self.__enabledPlugValueWidget.setReadOnly( self, readOnly )

	def _updateFromPlug( self ) :

		enabled = False
		with self.getContext() :
			with IECore.IgnoredExceptions( Gaffer.ProcessException ) :
				enabled = self.getPlug()["enabled"].getValue()

		self.__namePlugValueWidget.setEnabled( enabled )

class _RowCellsPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug ) :

		self.__row = _LinearLayoutPlugValueWidget( plug["cells"], childWidgetType = _CellPlugValueWidget, orientation = GafferUI.ListContainer.Orientation.Horizontal )
		GafferUI.PlugValueWidget.__init__( self, self.__row, plug )

	def _updateFromPlug( self ) :

		enabled = False
		with self.getContext() :
			with IECore.IgnoredExceptions( Gaffer.ProcessException ) :
				enabled = self.getPlug()["enabled"].getValue()

		self.__row.setEnabled( enabled )

class _HeaderPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		self.__label = GafferUI.Label()
		GafferUI.PlugValueWidget.__init__( self, self.__label, plug, **kw )

		self.contextMenuSignal().connect( Gaffer.WeakMethod( self.__contextMenu ), scoped = False )

		self._updateFromPlug()

	def _updateFromPlug( self ) :

		self.__label.setText( "<b>" + self.__plugLabel() + "</b>" )
		_applyFixedSize( self.__label, _cellWidthAndProxy( self.getPlug() )[0], _rowHeight )

	def __plugLabel( self ) :

		label = Gaffer.Metadata.value( self.getPlug(), "spreadsheet:columnLabel" )
		if not label :
			label = IECore.CamelCase.toSpaced( self.getPlug().getName() )

		return label

	def __contextMenu( self, widget ) :

		readOnly = self.getReadOnly() or Gaffer.MetadataAlgo.readOnly( self.getPlug() )

		menuDefinition = IECore.MenuDefinition()
		menuDefinition.append(
			"/Set Label...",
			{
				"command" : Gaffer.WeakMethod( self.__setLabel ),
				"active" : not readOnly,
			}
		)

		currentWidthScale = Gaffer.Metadata.value( self.getPlug(), "spreadsheet:columnWidthScale" ) or 1
		for label, widthScale in _widthScales :
			menuDefinition.append(
				"/Width/{}".format( label ),
				{
					"command" : functools.partial( Gaffer.WeakMethod( self.__setWidth ), widthScale ),
					"active" : not readOnly,
					"checkBox" : widthScale == currentWidthScale,
				}
			)

		menuDefinition.append( "/DeleteDivider", { "divider" : True } )

		menuDefinition.append(
			"/Delete Column",
			{
				"command" : Gaffer.WeakMethod( self.__deleteColumn ),
				"active" : not readOnly,
			}
		)

		self.__menu = GafferUI.Menu( menuDefinition )
		self.__menu.popup()

	def __setLabel( self ) :

		label = GafferUI.TextInputDialogue(
			title = "Set Label",
			confirmLabel = "Set",
			initialText = self.__plugLabel()
		).waitForText()

		if label is not None :
			with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
				Gaffer.Metadata.registerValue( self.getPlug(), "spreadsheet:columnLabel", label )

	def __setWidth( self, width, *unused ) :

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
				Gaffer.Metadata.registerValue( self.getPlug(), "spreadsheet:columnWidthScale", width )

	def __deleteColumn( self ) :

		rowsPlug = self.getPlug().ancestor( Gaffer.Spreadsheet.RowsPlug )
		with Gaffer.UndoScope( rowsPlug.ancestor( Gaffer.ScriptNode ) ) :
			rowsPlug.removeColumn( self.getPlug().parent().children().index( self.getPlug() ) )

class _CellPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		self.__frame = GafferUI.Frame( borderStyle = GafferUI.Frame.BorderStyle.None, borderWidth = 0 )
		GafferUI.PlugValueWidget.__init__( self, self.__frame, plug, **kw )

		width, proxy = _cellWidthAndProxy( plug )

		if proxy :
			plugValueWidget = _ProxyPlugValueWidget( self.getPlug()["value"] )
		else :
			plugValueWidget = GafferUI.PlugValueWidget.create( self.getPlug()["value"] )
			if isinstance( plugValueWidget, GafferUI.NameValuePlugValueWidget ) :
				plugValueWidget.setNameVisible( False )

		self.__frame.setChild( plugValueWidget )

		_applyFixedSize( self.__frame, width, _rowHeight )
		self.__frame._qtWidget().setProperty( "gafferAdjoinedTop", True )
		self.__frame._qtWidget().setProperty( "gafferAdjoinedBottom", True )
		self.__frame._qtWidget().setProperty( "gafferAdjoinedLeft", True )
		self.__frame._qtWidget().setProperty( "gafferAdjoinedRight", True )

		self.__alternate = None
		self.setAlternate( False )

		self._addPopupMenu( self.__frame )

		self.__frame.buttonDoubleClickSignal().connect( Gaffer.WeakMethod( self.__doubleClick ), scoped = False )

		self.enterSignal().connect( Gaffer.WeakMethod( self.__enter ), scoped = False )
		self.leaveSignal().connect( Gaffer.WeakMethod( self.__leave ), scoped = False )

		Gaffer.Metadata.plugValueChangedSignal().connect( Gaffer.WeakMethod( self.__plugMetadataChanged ), scoped = False )

		self._updateFromPlug()

	def setAlternate( self, alternate ) :

		alternate = bool( alternate )
		if self.__alternate == alternate :
			return

		self.__alternate = alternate
		self.__frame._qtWidget().setProperty( "gafferAlternate", alternate )
		self.__frame._repolish()

	def getAlternate( self ) :

		return self.__alternate

	@classmethod
	def currentCellChangedSignal( cls ) :

		return cls.__currentCellChangedSignal

	__currentCellChangedSignal = GafferUI.WidgetSignal()

	def _updateFromPlug( self ) :

		with self.getContext() :
			enabled = self.getPlug()["enabled"].getValue()

		if enabled :
			self.__frame.getChild().setVisible( True )
		else :
			self.__frame.getChild().setVisible( False )

	def __enter( self, widget ) :

		self.currentCellChangedSignal()( self )

	def __leave( self, widget ) :

		self.currentCellChangedSignal()( None )

	def __plugMetadataChanged( self, nodeTypeId, plugPath, key, plug ) :

		if plug is not None and key == "spreadsheet:columnWidthScale" :
			if plug.commonAncestor( self.getPlug(), Gaffer.Spreadsheet.RowsPlug ) :
				# We inherit "spreadsheet:columnWidthScale" from the cells of the default
				# row, so need to update when that changes.
				_applyFixedSize( self.__frame, _cellWidthAndProxy( self.getPlug() )[0], _rowHeight )

	def __doubleClick( self, widget, event ) :

		if event.buttons != event.Buttons.Left :
			return False

		if self.__frame.getChild().getVisible() :
			return False

		if self.getReadOnly() or Gaffer.MetadataAlgo.readOnly( self.getPlug()["enabled"] ) :
			return False

		if not self.getPlug()["enabled"].settable() :
			return False

		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			self.getPlug()["enabled"].setValue( True )

		return True

class _ProxyPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		button = GafferUI.Button( "Edit..." )
		GafferUI.PlugValueWidget.__init__( self, button, plug, **kw )

		button.clickedSignal().connect( self.__clicked, scoped = False )

	def getToolTip( self ) :

		result = GafferUI.PlugValueWidget.getToolTip( self )
		if not hasattr( self.getPlug(), "getValue" ) :
			return result

		with self.getContext() :
			value = self.getPlug().getValue()
			result += "\n\n### Current value\n\n" + str( value )

		return result

	def _updateFromPlug( self ) :

		pass

	def __clicked( self, button ) :

		_PlugValueDialogue.acquire( self.getPlug() )

## \todo See comments for `ColorSwatchPlugValueWidget._ColorPlugValueDialogue`.
# and `SplinePlugValueWidget._SplinePlugValueDialogue`.
class _PlugValueDialogue( GafferUI.Dialogue ) :

	def __init__( self, plug ) :

		GafferUI.Dialogue.__init__(
			self,
			plug.relativeName( plug.ancestor( Gaffer.ScriptNode ) )
		)

		self.__plug = plug
		self.setChild( GafferUI.PlugValueWidget.create( plug ) )

		plug.parentChangedSignal().connect( Gaffer.WeakMethod( self.__destroy ), scoped = False )
		plug.node().parentChangedSignal().connect( Gaffer.WeakMethod( self.__destroy ), scoped = False )

	@classmethod
	def acquire( cls, plug ) :

		script = plug.node().scriptNode()
		scriptWindow = GafferUI.ScriptWindow.acquire( script )

		for window in scriptWindow.childWindows() :
			if isinstance( window, cls ) and window.__plug == plug :
				window.setVisible( True )
				return window

		window = cls( plug )
		scriptWindow.addChildWindow( window, removeOnClose = True )
		window.setVisible( True )

		return window

	def __destroy( self, *unused ) :

		self.parent().removeChild( self )

# ScrolledContainer linking
# =========================
#
# To keep the row and column names and default cells visible at all times, we
# need to house them in separate ScrolledContainers from the main one. But we
# want to link the scrolling of them all, so they still act as a unit. We achieve
# this using the _LinkedScrollBar widget, which provides two-way coupling between
# the scrollbars of each container.
## \todo : Consider making this public as part of ScrolledContainer. If you do that,
# you will want to move the Orientation enum from ListContainer into `GafferUI.Enums`.

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

def __setRowNameWidth( rowPlug, widthScale, *unused ) :

	defaultRowPlug = rowPlug.parent()["default"]
	with Gaffer.UndoScope( defaultRowPlug.ancestor( Gaffer.ScriptNode ) ) :
		Gaffer.Metadata.registerValue( defaultRowPlug, "spreadsheet:rowNameWidthScale", widthScale )

def __prependRowAndCellMenuItems( menuDefinition, plugValueWidget ) :

	rowPlug = plugValueWidget.getPlug().ancestor( Gaffer.Spreadsheet.RowPlug )
	if rowPlug is None :
		return

	# Row menu items

	if isinstance( plugValueWidget, _RowNamePlugValueWidget ) :
		rowNamePlugValueWidget = plugValueWidget
	else :
		rowNamePlugValueWidget = plugValueWidget.ancestor( _RowNamePlugValueWidget )

	if rowNamePlugValueWidget and rowPlug.getName() != "default" :

		menuDefinition.prepend(
			"/Delete Row",
			{
				"command" : functools.partial( __deleteRow, rowPlug ),
				"active" : not plugValueWidget.getReadOnly() and not Gaffer.MetadataAlgo.readOnly( rowPlug )

			}
		)

		currentWidthScale = Gaffer.Metadata.value( rowPlug, "spreadsheet:rowNameWidthScale" ) or 1
		for label, widthScale in reversed( _widthScales ) :
			menuDefinition.prepend(
				"/Width/{}".format( label ),
				{
					"command" : functools.partial( __setRowNameWidth, rowPlug, widthScale ),
					"active" : not plugValueWidget.getReadOnly() and not Gaffer.MetadataAlgo.readOnly( rowPlug ),
					"checkBox" : widthScale == currentWidthScale,
				}
			)

	# Cell menu items

	cellPlugValueWidget = None
	if isinstance( plugValueWidget, _CellPlugValueWidget ) :
		cellPlugValueWidget = plugValueWidget
	else :
		cellPlugValueWidget = plugValueWidget.ancestor( _CellPlugValueWidget )

	if cellPlugValueWidget is not None :

		if rowPlug.getName() != "default" :

			enabled = None
			enabledPlug = cellPlugValueWidget.getPlug()["enabled"]
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

	columnIndex = spreadsheet["rows"].addColumn( plug, columnName )
	valuePlug = spreadsheet["rows"]["default"]["cells"][columnIndex]["value"]
	Gaffer.MetadataAlgo.copy( plug, valuePlug )
	if isinstance( plug, ( Gaffer.Color3fPlug, Gaffer.Color4fPlug ) ) :
		# Space is at a premium in spreadsheets, so prefer a single colour
		# swatch over numeric fields.
		Gaffer.Metadata.registerValue( valuePlug, "plugValueWidget:type", "GafferUI.ColorSwatchPlugValueWidget" )

	return columnIndex

def __createSpreadsheet( plug ) :

	spreadsheet = Gaffer.Spreadsheet()
	__addColumn( spreadsheet, plug )
	spreadsheet["rows"].addRow()

	with Gaffer.UndoContext( plug.ancestor( Gaffer.ScriptNode ) ) :
		plug.node().parent().addChild( spreadsheet )
		plug.setInput( spreadsheet["out"][0] )

	GafferUI.NodeEditor.acquire( spreadsheet )

def __addToSpreadsheet( plug, spreadsheet ) :

	with Gaffer.UndoContext( spreadsheet.ancestor( Gaffer.ScriptNode ) ) :
		columnIndex = __addColumn( spreadsheet, plug )
		plug.setInput( spreadsheet["out"][columnIndex] )

def __addToSpreadsheetSubMenu( plug ) :

	menuDefinition = IECore.MenuDefinition()

	alreadyConnected = []
	other = []
	for spreadsheet in Gaffer.Spreadsheet.Range( plug.node().parent() ) :

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

	def addItem( spreadsheet ) :

		menuDefinition.append(
			"/" + spreadsheet.getName(),
			{
				"command" : functools.partial( __addToSpreadsheet, plug, spreadsheet )
			}
		)

	if alreadyConnected and other :
		menuDefinition.append( "/__ConnectedDivider__", { "divider" : True, "label" : "Connected" } )

	for spreadsheet in alreadyConnected :
		addItem( spreadsheet )

	if alreadyConnected and other :
		menuDefinition.append( "/__OtherDivider__", { "divider" : True, "label" : "Other" } )

	for spreadsheet in other :
		addItem( spreadsheet )

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

	ancestorPlug, ancestorLabel = None, ""
	for ancestorType, ancestorLabel in [
		( Gaffer.TransformPlug, "Transform" ),
		( Gaffer.Transform2DPlug, "Transform" ),
		( Gaffer.NameValuePlug, "Value and Switch" ),
	] :
		ancestorPlug = plug.ancestor( ancestorType )
		if ancestorPlug :
			if all( p.getInput() is None for p in Gaffer.Plug.RecursiveRange( ancestorPlug ) ) :
				break
			else :
				ancestorPlug = None

	if ancestorPlug :
		menuDefinition.prepend(
			"/Add to Spreadsheet ({})".format( ancestorLabel ),
			{
				"subMenu" :  functools.partial( __addToSpreadsheetSubMenu, ancestorPlug )
			}
		)
		menuDefinition.prepend(
			"/Create Spreadsheet ({})...".format( ancestorLabel ),
			{
				"command" : functools.partial( __createSpreadsheet, ancestorPlug )
			}
		)

		menuDefinition.prepend(
			"/__AncestorDivider__", { "divider" : True }
		)

	menuDefinition.prepend(
		"/Add to Spreadsheet",
		{
			"subMenu" :  functools.partial( __addToSpreadsheetSubMenu, plug )
		}
	)

	menuDefinition.prepend(
		"/Create Spreadsheet...",
		{
			"command" : functools.partial( __createSpreadsheet, plug )
		}
	)

def __plugPopupMenu( menuDefinition, plugValueWidget ) :

	menuDefinition.prepend( "/SpreadsheetDivider", { "divider" : True } )

	## \todo We're prepending rather than appending so that we get the ordering we
	# want with respect to the Expression menu items. Really we need external control
	# over this ordering.
	__prependRowAndCellMenuItems( menuDefinition, plugValueWidget )
	__prependSpreadsheetCreationMenuItems( menuDefinition, plugValueWidget )

GafferUI.PlugValueWidget.popupMenuSignal().connect( __plugPopupMenu, scoped = False )

# NodeEditor tool menu
# ====================

def __createSpreadsheetForNode( node, activeRowNamesConnection, selectorContextVariablePlug, selectorValue ) :

	with Gaffer.UndoScope( node.ancestor( Gaffer.ScriptNode ) ) :

		spreadsheet = Gaffer.Spreadsheet( node.getName() + "Spreadsheet" )

		with node.scriptNode().context() :
			rowNames = activeRowNamesConnection.getValue()
		activeRowNamesConnection.setInput( spreadsheet["activeRowNames"] )

		if rowNames :
			for rowName in rowNames :
				spreadsheet["rows"].addRow()["name"].setValue( rowName )
		else :
			spreadsheet["rows"].addRow()

		if selectorValue is None :
			selectorValue = "${" + selectorContextVariablePlug.getValue() + "}"
			Gaffer.MetadataAlgo.setReadOnly( selectorContextVariablePlug, True )

		if selectorValue :
			spreadsheet["selector"].setValue( selectorValue )
			Gaffer.MetadataAlgo.setReadOnly( spreadsheet["selector"], True )

		node.parent().addChild( spreadsheet )

	GafferUI.NodeEditor.acquire( spreadsheet )

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
	menuDefinition.append(
		"/Create Spreadsheet...",
		{
			"command" : functools.partial( __createSpreadsheetForNode, node, activeRowNamesConnection, selectorContextVariablePlug, selectorValue ),
			"active" : (
				not nodeEditor.getReadOnly()
				and not Gaffer.MetadataAlgo.readOnly( node )
				and not Gaffer.MetadataAlgo.readOnly( activeRowNamesConnection )
			)
		}
	)

GafferUI.NodeEditor.toolMenuSignal().connect( __nodeEditorToolMenu, scoped = False )
