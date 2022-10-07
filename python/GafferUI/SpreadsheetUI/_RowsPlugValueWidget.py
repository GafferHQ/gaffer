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
import traceback

import imath

import IECore

import Gaffer
import GafferUI

from Qt import QtCore
from Qt import QtWidgets

from . import _Algo
from ._LinkedScrollBar import _LinkedScrollBar
from ._PlugTableModel import _PlugTableModel
from ._PlugTableView import _PlugTableView
from ._SectionChooser import _SectionChooser

# _RowsPlugValueWidget
# ====================
#
# This is the main top-level widget that forms the spreadsheet UI.

class _RowsPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug ) :

		self.__grid = GafferUI.GridContainer( spacing = 4 )

		GafferUI.PlugValueWidget.__init__( self, self.__grid, plug )

		model = _PlugTableModel( plug, self.getContext(), self._qtWidget() )
		selectionModel = QtCore.QItemSelectionModel( model, self._qtWidget() )

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
				selectionModel, _PlugTableView.Mode.Defaults,
				parenting = {
					"index" : ( 1, 1 ),
				}
			)

			with GafferUI.ListContainer(
				parenting = {
					"index" : ( 2, 1 ),
					"alignment" : ( GafferUI.HorizontalAlignment.Left, GafferUI.VerticalAlignment.Top )
				},
			) :

				GafferUI.Spacer( imath.V2i( 1, 4 ), maximumSize = imath.V2i( 1, 4 ) )

				self.__addColumnButton = GafferUI.MenuButton(
					image="plus.png", hasFrame=False, toolTip = "Click to add column, or drop plug to connect",
					menu = GafferUI.Menu( Gaffer.WeakMethod( self.__addColumnMenuDefinition ) )
				)
				self.__addColumnButton.dragEnterSignal().connect( Gaffer.WeakMethod( self.__addColumnButtonDragEnter ), scoped = False )
				self.__addColumnButton.dragLeaveSignal().connect( Gaffer.WeakMethod( self.__addColumnButtonDragLeave ), scoped = False )
				self.__addColumnButton.dropSignal().connect( Gaffer.WeakMethod( self.__addColumnButtonDrop ), scoped = False )

			self.__rowNamesTable = _PlugTableView(
				selectionModel, _PlugTableView.Mode.RowNames,
				parenting = {
					"index" : ( 0, 2 ),
				}
			)

			self.__cellsTable = _PlugTableView(
				selectionModel, _PlugTableView.Mode.Cells,
				parenting = {
					"index" : ( 1, 2 ),
				}
			)

			_LinkedScrollBar(
				GafferUI.ListContainer.Orientation.Vertical, [ self.__cellsTable, self.__rowNamesTable ],
				parenting = {
					"index" : ( 2, 2 ),
					"alignment" : ( GafferUI.HorizontalAlignment.Left, GafferUI.VerticalAlignment.None_ )
				}
			)

			_LinkedScrollBar(
				GafferUI.ListContainer.Orientation.Horizontal, [ self.__cellsTable, self.__defaultTable ],
				parenting = {
					"index" : ( 1, 3 ),
				}
			)

			self.__addRowButton = GafferUI.Button(
				image="plus.png", hasFrame=False, toolTip = "Click to add row, or drop new row names",
				parenting = {
					"index" : ( 0, 4 )
				}
			)
			self.__addRowButton.clickedSignal().connect( Gaffer.WeakMethod( self.__addRowButtonClicked ), scoped = False )
			self.__addRowButton.dragEnterSignal().connect( Gaffer.WeakMethod( self.__addRowButtonDragEnter ), scoped = False )
			self.__addRowButton.dragLeaveSignal().connect( Gaffer.WeakMethod( self.__addRowButtonDragLeave ), scoped = False )
			self.__addRowButton.dropSignal().connect( Gaffer.WeakMethod( self.__addRowButtonDrop ), scoped = False )

			if isinstance( plug.node(), Gaffer.Reference ) :
				# Currently we only allow new rows to be added to references
				# that had no rows when they were exported. We don't want to
				# get into merge hell trying to combine user-added and referenced
				# rows, especially given the row-reordering feature.
				for row in plug.children()[1:] :
					if not plug.node().isChildEdit( row ) :
						self.__addRowButton.setVisible( False )
						break
				# Likewise, we don't support the addition of new columns at all.
				self.__addColumnButton.setVisible( False )

			if Gaffer.Metadata.value( plug, "spreadsheet:columnsNeedSerialisation" ) == False :
				# This metadata is set by custom nodes which create their
				# columns in a constructor. If users were to add their own
				# columns, they wouldn't be serialised correctly, so we hide the
				# button.
				self.__addColumnButton.setVisible( False )

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

		for widget in [ self.__addRowButton, self.__addColumnButton ] :
			widget.enterSignal().connect( Gaffer.WeakMethod( self.__enterToolTippedWidget ), scoped = False )
			widget.leaveSignal().connect( Gaffer.WeakMethod( self.__leaveToolTippedWidget ), scoped = False )

		for widget in [ self.__defaultTable, self.__cellsTable ] :
			widget.mouseMoveSignal().connect( Gaffer.WeakMethod( self.__cellsMouseMove ), scoped = False )
			widget.leaveSignal().connect( Gaffer.WeakMethod( self.__cellsLeave ), scoped = False )

		Gaffer.Metadata.plugValueChangedSignal( plug.node() ).connect( Gaffer.WeakMethod( self.__plugMetadataChanged ), scoped = False )

		self.__updateVisibleSections()
		self.__updateDefaultRowVisibility()

	def hasLabel( self ) :

		return True

	def getToolTip( self ) :

		# The generic auto-generated PlugValueWidget tooltip is distracting
		# rather than useful, so we disable it. Calling `Widget.getToolTip()`
		# means we continue to support tooltips added explicitly with
		# `setToolTip()`.
		return GafferUI.Widget.getToolTip( self )

	__addRowButtonMenuSignal = None
	## This signal is emitted whenever the add row button is clicked.
	# If the resulting menu definition has been populated with items,
	# a popup menu will be presented from the button.
	# If only a single item is present, its command will be called
	# immediately instead of presenting a menu.
	# If no items are present, then the default behaviour is to
	# add a single row to the end of the spreadsheet.
	# The signal is called with the corresponding spreadsheet rows plug
	# value widget.
	@classmethod
	def addRowButtonMenuSignal( cls ) :

		if cls.__addRowButtonMenuSignal is None :
			cls.__addRowButtonMenuSignal = _AddButtonMenuSignal()

		return cls.__addRowButtonMenuSignal

	__addColumnButtonMenuSignal = None
	@classmethod
	def addColumnButtonMenuSignal( cls ) :

		if cls.__addColumnButtonMenuSignal is None :
			cls.__addColumnButtonMenuSignal = _AddButtonMenuSignal()

		return cls.__addColumnButtonMenuSignal

	def _updateFromPlug( self ) :

		editable = self.getPlug().getInput() is None and not Gaffer.MetadataAlgo.readOnly( self.getPlug() )
		self.__addRowButton.setEnabled( editable )
		self.__addColumnButton.setEnabled( editable )

	def __addRowButtonClicked( self, *unused ) :

		menuDefinition = IECore.MenuDefinition()
		self.addRowButtonMenuSignal()( menuDefinition, self )

		if menuDefinition.size() == 0 :
			with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
				row = self.getPlug().addRow()
			# Select new row for editing. Have to do this on idle as otherwise it doesn't scroll
			# right to the bottom.
			GafferUI.EventLoop.addIdleCallback( functools.partial( self.__rowNamesTable.editPlugs, [ row["name"] ] ) )
		elif menuDefinition.size() == 1 :
			_, item = menuDefinition.items()[0]
			item.command()
		else :
			self.__popupMenu = GafferUI.Menu( menuDefinition )
			self.__popupMenu.popup( parent = self )

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

	def __addColumnMenuDefinition( self ) :

		menuDefinition = IECore.MenuDefinition()

		## \todo Centralise a standard mechanism for building plug
		# creation menus. We have similar code in UserPlugs, CompoundDataPlugValueWidget,
		# UIEditor, ShaderTweaksUI etc.
		for label, plugType in [
			( "Bool", Gaffer.BoolPlug ),
			( "Int", Gaffer.IntPlug ),
			( "Float", Gaffer.FloatPlug ),
			( "NumericDivider", None ),
			( "String", Gaffer.StringPlug ),
			( "StringDivider", None ),
			( "V2i", Gaffer.V2iPlug ),
			( "V3i", Gaffer.V3iPlug ),
			( "V2f", Gaffer.V2fPlug ),
			( "V3f", Gaffer.V3fPlug ),
			( "VectorDivider", None ),
			( "Color3f", Gaffer.Color3fPlug ),
			( "Color4f", Gaffer.Color4fPlug ),
		] :

			if plugType is None :
				menuDefinition.append( label, { "divider" : True } )
			else :
				menuDefinition.append(
					label, { "command" : functools.partial( Gaffer.WeakMethod( self.__addColumn ), plugType = plugType ), "active" : True }
				)

		self.addColumnButtonMenuSignal()( menuDefinition, self )

		return menuDefinition

	def __addColumn( self, menu, plugType ) :

		d = GafferUI.TextInputDialogue( initialText = "column", title = "Enter name", confirmLabel = "Add Column" )
		name = d.waitForText( parentWindow = menu.ancestor( GafferUI.Window ) )
		if not name :
			return

		plug = plugType( name )
		with Gaffer.UndoScope( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			columnIndex = self.getPlug().addColumn( plug )
			if self.__sectionChooser.currentSection() :
				self.__sectionChooser.setSection(
					self.getPlug().defaultRow()["cells"][columnIndex],
					self.__sectionChooser.currentSection()
				)

	def __addColumnButtonDragEnter( self, addButton, event ) :

		if not isinstance( event.data, Gaffer.ValuePlug ) or event.data.getInput() is not None :
			return False

		if not isinstance( self.getPlug().node(), Gaffer.Spreadsheet ) :
			# Dropping plugs involves making an output connection from
			# the spreadsheet, which we don't want to do for a promoted
			# plug.
			return False

		addButton.setHighlighted( True )
		return True

	def __addColumnButtonDragLeave( self, addButton, event ) :

		addButton.setHighlighted( False )
		return True

	def __addColumnButtonDrop( self, addButton, event ) :

		addButton.setHighlighted( False )
		_Algo.addToSpreadsheet( event.data, self.getPlug().node(), self.__sectionChooser.currentSection() )
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

			columnPlug = self.getPlug().defaultRow()["cells"][plug.getName()]
			columnName = Gaffer.Metadata.value( columnPlug, "spreadsheet:columnLabel" )
			if not columnName :
				columnName = IECore.CamelCase.toSpaced( columnPlug.getName() )

			status = "Row : {}, Column : {}".format(
				rowName,
				columnName
			)

		self.__statusLabel.setText( status )

	def __cellsLeave( self, widget ) :

		self.__statusLabel.setText( "" )

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

	def __plugMetadataChanged( self, plug, key, reason ) :

		if plug == self.getPlug() and key == "spreadsheet:defaultRowVisible" :
			self.__updateDefaultRowVisibility()

	def __currentSectionChanged( self, tabBar ) :

		self.__updateVisibleSections()

	def __updateVisibleSections( self ) :

		section = self.__sectionChooser.currentSection()
		self.__defaultTable.setVisibleSection( section )
		self.__cellsTable.setVisibleSection( section )

GafferUI.PlugValueWidget.registerType( Gaffer.Spreadsheet.RowsPlug, _RowsPlugValueWidget )

# Signal with custom result combiner to prevent bad
# slots blocking the execution of others.
class _AddButtonMenuSignal( Gaffer.Signals.Signal2 ) :

	def __init__( self ) :

		Gaffer.Signals.Signal2.__init__( self, self.__combiner )

	@staticmethod
	def __combiner( results ) :

		while True :
			try :
				next( results )
			except StopIteration :
				return
			except Exception as e :
				# Print message but continue to execute other slots
				IECore.msg(
					IECore.Msg.Level.Error,
					"Spreadsheet Add Button menu", traceback.format_exc()
				)
				# Remove circular references that would keep the widget in limbo.
				e.__traceback__ = None
