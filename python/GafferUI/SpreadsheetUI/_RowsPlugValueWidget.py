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

			addRowButton.setVisible( _Algo.dimensionsEditable( plug ) )

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
		GafferUI.EventLoop.addIdleCallback( functools.partial( self.__rowNamesTable.editPlugs, [ row["name"] ] ) )

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

		if plug == self.getPlug() and key == "spreadsheet:defaultRowVisible" :
			self.__updateDefaultRowVisibility()

	def __currentSectionChanged( self, tabBar ) :

		self.__updateVisibleSections()

	def __updateVisibleSections( self ) :

		section = self.__sectionChooser.currentSection()
		self.__defaultTable.setVisibleSection( section )
		self.__cellsTable.setVisibleSection( section )

GafferUI.PlugValueWidget.registerType( Gaffer.Spreadsheet.RowsPlug, _RowsPlugValueWidget )
