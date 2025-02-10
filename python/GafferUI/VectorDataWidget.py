##########################################################################
#
#  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
#  Copyright (c) 2012, John Haddon. All rights reserved.
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
from GafferUI.ColorSwatch import _Checker
from ._TableView import _TableView

from Qt import QtCore
from Qt import QtGui
from Qt import QtWidgets
from Qt import QtCompat
import Qt

## The VectorDataWidget provides a table view for the contents of
# one or more IECore VectorData instances.
class VectorDataWidget( GafferUI.Widget ) :

	## data may either be a VectorData instance or a list of VectorData instances
	# of identical length.
	#
	# header may be False for no header, True for a default header, or a list of
	# strings to specify a custom header per data.
	#
	# minimumVisibleRows specifies a number of rows after which a vertical scroll bar
	# may become visible - before this all rows should be directly visible with no need
	# for scrolling.
	#
	# columnToolTips may be specified as a list of strings to provide a tooltip for
	# each data. Note that the `column` part of the name is misleading.
	#
	# sizeEditable specifies whether or not items may be added and removed
	# from the data (assuming it is editable).
	#
	# columnEditability may be specified as a list of booleans, providing per-column
	# editability.
	def __init__(
		self,
		data=None,
		editable=True,
		header=False,
		showIndices=True,
		minimumVisibleRows=8,
		columnToolTips=None,
		sizeEditable=True,
		columnEditability=None,
		horizontalScrollMode = GafferUI.ScrollMode.Never,
		verticalScrollMode = GafferUI.ScrollMode.Automatic,
		**kw
	) :

		self.__column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical )

		GafferUI.Widget.__init__( self, self.__column, **kw )

		# table view

		self.__tableView = _TableView( minimumVisibleRows = minimumVisibleRows )

		self.__tableView.horizontalHeader().setMinimumSectionSize( 70 )

		self.__tableView.verticalHeader().setVisible( showIndices )
		QtCompat.setSectionResizeMode( self.__tableView.verticalHeader(), QtWidgets.QHeaderView.Fixed )

		self.__tableView.setHorizontalScrollBarPolicy( GafferUI.ScrollMode._toQt( horizontalScrollMode ) )
		self.__tableView.setVerticalScrollBarPolicy( GafferUI.ScrollMode._toQt( verticalScrollMode ) )

		self.__tableView.setSelectionBehavior( QtWidgets.QAbstractItemView.SelectItems )
		self.__tableView.setCornerButtonEnabled( False )

		self.__tableView.setContextMenuPolicy( QtCore.Qt.CustomContextMenu )
		self.__tableView.customContextMenuRequested.connect( Gaffer.WeakMethod( self.__contextMenu ) )

		self.__tableView.verticalHeader().setDefaultSectionSize( 20 )
		self.__tableView.setWordWrap( False )

		self.__tableViewHolder = GafferUI.Widget( self.__tableView )
		self.__column.append( self.__tableViewHolder )

		# buttons

		self.__buttonRow = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal, spacing = 4 )

		addButton = GafferUI.Button( image="plus.png", hasFrame=False )
		addButton.clickedSignal().connect( Gaffer.WeakMethod( self.__addRows ) )
		self.__buttonRow.append( addButton )

		removeButton = GafferUI.Button( image="minus.png", hasFrame=False )
		removeButton.clickedSignal().connect( Gaffer.WeakMethod( self.__removeSelection ) )
		self.__buttonRow.append( removeButton )

		self.__buttonRow.append( GafferUI.Spacer( size = imath.V2i( 0 ), maximumSize = imath.V2i( 100000, 1 ) ), expand=1 )
		self.__column.append( self.__buttonRow )

		# stuff for drag enter/leave and drop

		self.dragEnterSignal().connect( Gaffer.WeakMethod( self.__dragEnter ) )
		addButton.dragEnterSignal().connect( Gaffer.WeakMethod( self.__dragEnter ) )
		removeButton.dragEnterSignal().connect( Gaffer.WeakMethod( self.__dragEnter ) )

		self.dragLeaveSignal().connect( Gaffer.WeakMethod( self.__dragLeave ) )
		addButton.dragLeaveSignal().connect( Gaffer.WeakMethod( self.__dragLeave ) )
		removeButton.dragLeaveSignal().connect( Gaffer.WeakMethod( self.__dragLeave ) )

		self.dropSignal().connect( Gaffer.WeakMethod( self.__drop ) )
		addButton.dropSignal().connect( Gaffer.WeakMethod( self.__drop ) )
		removeButton.dropSignal().connect( Gaffer.WeakMethod( self.__drop ) )
		self.__dragPointer = "values"

		# stuff for drag begin

		self.__borrowedButtonPress = None
		self.__emittingButtonPress = False
		self.__tableViewHolder.buttonPressSignal().connect( Gaffer.WeakMethod( self.__buttonPress ) )
		self.__tableViewHolder.buttonReleaseSignal().connect( Gaffer.WeakMethod( self.__buttonRelease ) )
		self.__tableViewHolder.mouseMoveSignal().connect( Gaffer.WeakMethod( self.__mouseMove ) )
		self.__tableViewHolder.dragBeginSignal().connect( Gaffer.WeakMethod( self.__dragBegin ) )
		self.__tableViewHolder.dragEndSignal().connect( Gaffer.WeakMethod( self.__dragEnd ) )

		# key handling

		self.__tableViewHolder.keyPressSignal().connect( Gaffer.WeakMethod( self.__keyPress ) )

		# popup menu for data

		self.__dataMenuSignal = Gaffer.Signal2()

		# final setup

		self.__dataChangedSignal = GafferUI.WidgetSignal()
		self.__editSignal = Gaffer.Signals.Signal3()

		self.setHeader( header )

		self.__toolTips = columnToolTips
		self.__columnEditability = columnEditability

		self.__propagatingDataChangesToSelection = False

		self.__sizeEditable = sizeEditable
		self.setData( data )
		self.setEditable( editable )

	def setHighlighted( self, highlighted ) :

		if highlighted == self.getHighlighted() :
			return

		self.__tableView.setProperty( "gafferHighlighted", GafferUI._Variant.toVariant( highlighted ) )

		GafferUI.Widget.setHighlighted( self, highlighted )

	def setErrored( self, errored ) :

		if errored == self.getErrored() :
			return

		self.__tableView.setProperty( "gafferError", GafferUI._Variant.toVariant( bool( errored ) ) )
		self._repolish()

	def getErrored( self ) :

		return GafferUI._Variant.fromVariant( self.__tableView.property( "gafferError" ) ) or False

	def addButton( self ) :

		return self.__buttonRow[0]

	def removeButton( self ) :

		return self.__buttonRow[1]

	def setData( self, data ) :

		# it could be argued that we should early out here if data is self.getData(),
		# but we can't right now as we're relying on setData() to update everything
		# when the data has been modified in place by some external process, or
		# by self.__removeSelection.

		if data is not None :
			if not isinstance( data, list ) :
				data = [ data ]
			self.__model = _Model( data, self.__tableView, self.getEditable(), self.__header, self.__toolTips, self.__columnEditability )
			self.__model.dataChanged.connect( Gaffer.WeakMethod( self.__modelDataChanged ) )
			self.__model.rowsInserted.connect( Gaffer.WeakMethod( self.__emitDataChangedSignal ) )
			self.__model.rowsRemoved.connect( Gaffer.WeakMethod( self.__emitDataChangedSignal ) )
		else :
			self.__model = None

		self.__tableView.setModel( self.__model )

		if self.__model :

			columnIndex = 0
			haveResizeableContents = False
			for accessor in self.__model.vectorDataAccessors() :
				for i in range( 0, accessor.numColumns() ) :
					delegate = _Delegate.create( accessor.data() )
					delegate.setParent( self.__model )
					self.__tableView.setItemDelegateForColumn( columnIndex, delegate )
					canStretch = delegate.canStretch()
					haveResizeableContents = haveResizeableContents or canStretch
					columnIndex += 1

			QtCompat.setSectionResizeMode(
				self.__tableView.horizontalHeader(),
				QtWidgets.QHeaderView.ResizeToContents if haveResizeableContents else QtWidgets.QHeaderView.Fixed
			)

			self.__tableView.horizontalHeader().setStretchLastSection( canStretch )
			horizontalSizePolicy = QtWidgets.QSizePolicy.Expanding
			if self.__tableView.horizontalScrollMode() == QtCore.Qt.ScrollBarAlwaysOff and not canStretch :
				horizontalSizePolicy = QtWidgets.QSizePolicy.Fixed

			self.__tableView.setSizePolicy(
				QtWidgets.QSizePolicy(
					horizontalSizePolicy,
					QtWidgets.QSizePolicy.Maximum
				)
			)

			selectionModel = self.__tableView.selectionModel()
			selectionModel.selectionChanged.connect( Gaffer.WeakMethod( self.__selectionChanged ) )

		self.__updateRemoveButtonEnabled()

		# Somehow the QTableView can leave its header in a state where updates are disabled.
		# If we didn't turn them back on, the header would disappear.
		self.__tableView.verticalHeader().setUpdatesEnabled( True )
		self.__tableView.updateGeometry()

	## Returns the data being displayed. This is always returned as a list of
	# VectorData instances, even if only one instance was passed to setData().
	def getData( self ) :
		if not self.__model:
			return []

		return self.__model.vectorData()

	def setHeader( self, header ) :

		if isinstance( header, list ) :
			self.__header = header
		else :
			self.__header = None

		self.__tableView.horizontalHeader().setVisible( bool( header ) )

	def getHeader( self ):

		return self.__header

	def setToolTips( self, toolTips ) :

		self.__toolTips = toolTips

	def getToolTips( self ):

		return self.__toolTips

	def setEditable( self, editable ) :

		if editable == self.getEditable() :
			return

		# Set property for stylesheet and update visibility
		# of buttons.

		if editable :
			self.__tableView.setProperty( "gafferEditable", True )
			self.__buttonRow.setVisible( self.__sizeEditable )
		else :
			self.__tableView.setProperty( "gafferEditable", False )
			self.__buttonRow.setVisible( False )

		self._repolish()

		# update the model
		if self.__model is not None :
			self.__model.setEditable( editable )

	def getEditable( self ) :

		return self.__tableView.property( "gafferEditable" )

	def setSizeEditable( self, sizeEditable ) :

		if sizeEditable == self.__sizeEditable :
			return

		self.__sizeEditable = sizeEditable
		self.__buttonRow.setVisible( self.getEditable() and self.__sizeEditable )

	def getSizeEditable( self ) :

		return self.__sizeEditable

	## Note that the number of columns is not necessarily the
	# same as the length of the list returned by getData() - for
	# instance a V3fVectorData in the list will generate 3 columns
	# in the UI. The columnIndex is specified taking this into account,
	# so there are actually 3 columns indexes relating to a single
	# V3fVectorData, and each can be shown/hidden individually.
	def setColumnVisible( self, columnIndex, visible ) :

		self.__tableView.setColumnHidden( columnIndex, not visible )

	def getColumnVisible( self, columnIndex ) :

		return not self.__tableView.isColumnHidden( columnIndex )

	def setColumnEditable( self, columnIndex, editable ) :

		if columnIndex < 0 or not self.__model or columnIndex >= self.__model.columnCount() :
			raise IndexError

		if self.__columnEditability is None :
			if editable :
				return
			else :
				self.__columnEditability = [ True ] * self.__model.columnCount()

		if self.__columnEditability[columnIndex] == editable :
			return

		self.__columnEditability[columnIndex] = editable
		self.setData( self.getData() ) # update the model

	def getColumnEditable( self, columnIndex ) :

		if columnIndex < 0 or not self.__model or columnIndex >= self.__model.columnCount() :
			raise IndexError

		if self.__columnEditability is None :
			return True

		return self.__columnEditability[columnIndex]

	def setDragPointer( self, dragPointer ) :

		self.__dragPointer = dragPointer

	def getDragPointer( self ) :

		return self.__dragPointer

	## Returns a tuple of ( columnIndex, rowIndex ) for the
	# index at the specified position in local space. Note that because
	# compound types like V3fVectorData are represented as more than one
	# column, this index is not suitable for indexing directly into the
	# data returned by getData().
	def indexAt( self, position ) :

		point = self.__tableView.viewport().mapFrom( self.__tableView, QtCore.QPoint( position[0], position[1] ) )
		index = self.__tableView.indexAt( point )
		return ( index.column(), index.row() )

	## Returns a list of ( columnIndex, rowIndex ) for the currently
	# selected cells.
	def selectedIndices( self ) :

		return [ ( x.column(), x.row() ) for x in self.__tableView.selectedIndexes() ]

	## Maps from the index of a column to a tuple of ( dataIndex, componentIndex )
	# which can be used to index into the data as follows :
	#
	#    getData()[dataIndex][rowIndex][componentIndex]
	#
	# Where the data in a column is not of a compound type, the returned
	# componentIndex will be -1.
	def columnToDataIndex( self, columnIndex ) :

		return self.__model.columnToDataIndex( columnIndex )

	## Performs the reverse of columnToDataIndex.
	def dataToColumnIndex( self, dataIndex, componentIndex ) :

		return self.__model.dataToColumnIndex( dataIndex, componentIndex )


	## Returns a signal which is emitted whenever the data is edited.
	# The signal is /not/ emitted when setData() is called.
	def dataChangedSignal( self ) :

		return self.__dataChangedSignal

	## A signal emitted when the user clicks to edit a cell.
	# Slots should accept ( vectorDataWidget, columnIndex, rowIndex )
	# arguments and return a Widget which will be used to perform the
	# editing. The Widget must have setValue()/getValue() methods which
	# accept the appropriate type for the column being edited - these will
	# be used to transfer values to and from the Widget. By default, the Enter
	# and Escape keys will be intercepted to complete editing, but the Widget
	# may also be hidden to signify that editing has been completed by some
	# other means.
	def editSignal( self ) :

		return self.__editSignal

	## A signal emitted when the user right clicks selected cells.
	# Slots should accept ( VectorDataWidget, IECore.MenuDefinition ) arguments,
	# modify the given menu and return it.
	def dataMenuSignal( self ) :

		return self.__dataMenuSignal

	## \deprecated Use dataMenuSignal() instead.
	# Returns a definition for the popup menu - this is called each time
	# the menu is displayed to allow menus to be built dynamically. May be
	# overridden in derived classes to modify the menu.
	## \todo We should remove this as part of implementing #217, and just
	# let everything hook onto contextMenuSignal() instead.
	def _contextMenuDefinition( self, selectedRows ) :

		m = IECore.MenuDefinition()

		m.append( "/Select All", { "command" : self.__selectAll } )
		m.append( "/Clear Selection", { "command" : self.__clearSelection } )

		if self.getEditable() and self.getSizeEditable() :

			m.append( "/divider", { "divider" : True } )
			m.append(
				"/Delete Selected Rows",
				{
					"command" : functools.partial( Gaffer.WeakMethod( self.__removeRows ), selectedRows ),
					"shortCut" : "Backspace, Delete"
				}
			)

		return m

	## This function is used by the ui to create new data to append. It may be overridden
	# in derived classes to customise data creation. The return value should be a list of
	# VectorData instances  in the same format as that returned by getData(), or None to
	# cancel the operation.
	def _createRows( self ) :

		newData = []
		data = self.getData()
		accessors = self.__model.vectorDataAccessors()
		for d, a in zip( data, accessors ) :
			nd = d.__class__()
			nd.append( a.defaultElement() )
			newData.append( nd )

		return newData

	def _displayTransformChanged( self ) :

		GafferUI.Widget._displayTransformChanged( self )
		self._qtWidget().update()

	def __modelDataChanged( self, topLeft, bottomRight, roles ) :

		if self.__propagatingDataChangesToSelection :
			return

		if topLeft == bottomRight and self.__tableView.selectionModel().isSelected( topLeft ) :
			self.__propagatingDataChangesToSelection = True
			valueToPropagate = self.__model.data( topLeft, QtCore.Qt.EditRole )
			for index in self.__tableView.selectedIndexes() :
				if index == topLeft :
					continue
				# we have to ignore exceptions, as the items we're setting might
				# have a different data type than the value we're passing.
				with IECore.IgnoredExceptions( Exception ) :
					self.__model.setData( index, valueToPropagate, QtCore.Qt.EditRole )
			self.__propagatingDataChangesToSelection = False

		self.__emitDataChangedSignal()

	def __emitDataChangedSignal( self, *unusedArgs ) :

		self.dataChangedSignal()( self )

	def __contextMenu( self, pos ) :

		# build the menu and pop it up
		m = self._contextMenuDefinition( self.__selectedRows() )
		self.dataMenuSignal()( self, m )
		self.__popupMenu = GafferUI.Menu( m )
		self.__popupMenu.popup( self )

	def __selectAll( self ) :

		self.__tableView.selectAll()

	def __clearSelection( self ) :

		self.__tableView.clearSelection()

	def __selectedRows( self ) :

		selectedRows = [ x.row() for x in self.__tableView.selectedIndexes() ]
		selectedRows = list( set( selectedRows ) ) # remove duplicates
		selectedRows.sort()

		return selectedRows

	def __updateRemoveButtonEnabled( self ) :

		self.removeButton().setEnabled( self.__tableView.selectionModel().hasSelection() )

	def __selectionChanged( self, *unused ) :

		self.__updateRemoveButtonEnabled()

	def __removeSelection( self, button ) :

		self.__removeRows( self.__selectedRows() )
		# If __updateRemoveButtonEnabled() disables
		# the button, then it can get stuck in a highlighted
		# state unless we unstick it like so.
		button.setHighlighted( False )

	def __removeRows( self, rows ) :

		data = self.getData()

		# delete the rows from data
		for i in range( len( rows )-1, -1, -1 ) :
			for d in data :
				del d[rows[i]]

		# tell the world
		self.setData( data )
		self.__emitDataChangedSignal()

	def __addRows( self, button ) :

		if self.__model is None :
			return

		# Get the data we want to append.

		newData = self._createRows()
		if not newData :
			return

		# Extend our current data with the new data,
		# and call setData() to update the table view.

		data = self.getData()
		assert( len( data ) == len( newData ) )
		originalLength = len( data[0] )
		for i in range( 0, len( data ) ) :
			data[i].extend( newData[i] )

		self.setData( data )

		# Select the newly created rows, making the last one
		# the current selection (the one used as the endpoint
		# for shift-click region selects).

		lastIndex = self.__model.index( len( data[0] ) - 1, 0 )

		self.__tableView.setCurrentIndex(
			lastIndex
		)

		selection = QtCore.QItemSelection(
			self.__model.index( originalLength, 0 ),
			lastIndex
		)

		self.__tableView.selectionModel().select(
			selection,
			QtCore.QItemSelectionModel.ClearAndSelect | QtCore.QItemSelectionModel.Rows
		)

		# Scroll so the newly added item is visible, and
		# move the focus to the table view, so the new item can
		# be edited with the keyboard immediately.

		self.__tableView.scrollToBottom()
		self.__tableView.setFocus( QtCore.Qt.OtherFocusReason )

		# Let everyone know about this wondrous event.

		self.__emitDataChangedSignal()

	def __dragEnter( self, widget, event ) :

		if not self.getEditable() :
			return False

		if event.sourceWidget is self.__tableViewHolder and widget is not self.__buttonRow[1]:
			# we don't accept drags from ourself unless the target is the remove button
			return False

		data = self.getData()
		if (
			len( data ) == 1 and (
				event.data.isInstanceOf( data[0].typeId() ) or (
					hasattr( event.data, "value" ) and isinstance(
						event.data.value,
						IECore.DataTraits.valueTypeFromSequenceType( type( data[0] ) )
					)
				)
			)
		) :
			# The remove button will be disabled if there's no selection -
			# we reenable it so it can receive the drag. We'll update it again
			# in __dragLeave() and __drop().
			self.removeButton().setEnabled( True )
			widget.setHighlighted( True )
			return True

		return False

	def __dragLeave( self, widget, event ) :

		widget.setHighlighted( False )

		if event.destinationWidget is not self and not self.isAncestorOf( event.destinationWidget ) :
			self.__updateRemoveButtonEnabled()

		return True

	def __drop( self, widget, event ) :

		# dragEnter checked that we only had one data array
		data = self.getData()[0]

		# dragEnter also checked that if the drop value is not a vector, then
		# the type matches what is contained by the widget's vector.

		if widget is self.__buttonRow[1] :
			# remove
			s = set( event.data ) if IECore.DataTraits.isSequenceDataType( event.data ) else [event.data.value]
			newData = data.__class__()
			for d in data :
				if d not in s :
					newData.append( d )
			data = newData
		else :
			# add, but avoid creating duplicates
			s = set( data )
			eventList = event.data if IECore.DataTraits.isSequenceDataType( event.data ) else [event.data.value]
			for d in eventList :
				if d not in s :
					data.append( d )
					s.add( d )

		self.setData( [ data ] )
		self.dataChangedSignal()( self )

		widget.setHighlighted( False )
		self.__updateRemoveButtonEnabled()

		return True

	def __buttonPress( self, widget, event ) :

		assert( widget is self.__tableViewHolder )

		if len( self.getData() ) != 1 :
			# we only act as a drag source when we have a single vector of data
			return False

		if self.__emittingButtonPress :
			return False

		self.__borrowedButtonPress = None
		if event.buttons == event.Buttons.Left and event.modifiers == event.Modifiers.None_ :

			# We want to implement drag and drop of the selected items, which means borrowing
			# mouse press events that the QTableView needs to perform selection.
			# This makes things a little tricky. There are are two cases :
			#
			#  1) There is an existing selection, and it's been clicked on. We borrow the event
			#     so we can get a dragBeginSignal(), and to prevent the QTableView reducing a current
			#     multi-selection down to the single clicked item. If a drag doesn't materialise we'll
			#     re-emit the event straight to the QTableView in __buttonRelease so the QTableView can
			#     do its thing.
			#
			#  2) There is no existing selection. We pass the event to the QTableView
			#     to see if it will select something which we can subsequently drag.
			#
			# This is further complicated by the fact that the button presses we simulate for Qt
			# will end up back in this function, so we have to be careful to ignore those.

			point = self.__tableView.viewport().mapFrom(
				self.__tableView,
				QtCore.QPoint( event.line.p0.x, event.line.p0.y )
			)
			index = self.__tableView.indexAt( point )
			if self.__tableView.selectionModel().isSelected( index ) :
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
			# take the event so that the underlying QTableView doesn't
			# try to do drag-selection, which would ruin our own upcoming drag.
			return True

		return False

	def __dragBegin( self, widget, event ) :

		self.__borrowedButtonPress = None
		selectedRows = self.__selectedRows()
		if len( selectedRows ) :
			data = self.getData()[0]
			result = IECore.Object.create( data.typeId() )
			for i in selectedRows :
				result.append( data[i] )
			GafferUI.Pointer.setCurrent( self.__dragPointer )
			return result

		return None

	def __dragEnd( self, widget, event ) :

		GafferUI.Pointer.setCurrent( None )

	def __emitButtonPress( self, event ) :

		point = self.__tableView.viewport().mapFrom(
			self.__tableView,
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
			self.__tableView.mousePressEvent( qEvent )
		finally :
			self.__emittingButtonPress = False

	def __keyPress( self, widget, event ) :

		if event.key in ( "Backspace", "Delete" ) :
			if self.getEditable() and self.getSizeEditable() :
				self.__removeRows( self.__selectedRows() )
			return True

# Internal implementation detail - a qt model which wraps
# around the VectorData.
class _Model( QtCore.QAbstractTableModel ) :

	__addValueText = "Add..."

	def __init__( self, data, parent=None, editable=True, header=None, toolTips=None, columnEditability=None ) :

		QtCore.QAbstractTableModel.__init__( self, parent )

		self.__data = data
		self.__editable = editable
		self.__header = header
		self.__toolTips = toolTips
		self.__columnEditability = columnEditability

		self.__columns = []
		self.__accessors = []
		for d in self.__data :
			accessor = _DataAccessor.create( d )
			assert( accessor is not None )
			for i in range( 0, accessor.numColumns() ) :
				self.__columns.append( IECore.Struct( accessor=accessor, relativeColumnIndex=i ) )
			self.__accessors.append( accessor )

		if self.__columnEditability is not None :
			assert( len( self.__columns ) == len( self.__columnEditability ) )

	## Methods specific to this model first

	def vectorData( self ) :

		return self.__data

	def columnToDataIndex( self, columnIndex ) :

		c = 0
		for dataIndex, accessor in enumerate( self.vectorDataAccessors() ) :
			nc = accessor.numColumns()
			if c + nc > columnIndex :
				if nc == 1 :
					return ( dataIndex, -1 )
				else :
					return ( dataIndex, columnIndex - c )
			c += nc

		raise IndexError( columnIndex )

	def dataToColumnIndex( self, dataIndex, componentIndex ) :

		accessors = self.vectorDataAccessors()
		if dataIndex < 0 or dataIndex >= len( accessors ) :
			raise IndexError( dataIndex )

		columnIndex = 0
		for d in range( 0, dataIndex ) :
			columnIndex += accessors[d].numColumns()

		return columnIndex + max( 0, componentIndex )

	def vectorDataAccessors( self ) :

		return self.__accessors

	def setEditable( self, editable ) :

		if self.__editable == editable :
			return

		self.__editable = editable

	def getEditable( self ) :

		return self.__editable

	## Then overrides for methods inherited from QAbstractModel

	def rowCount( self, parent = QtCore.QModelIndex() ) :

		if parent.isValid() :
			return 0

		return max( [ len( d ) for d in self.__data ] )

	def columnCount( self, parent = QtCore.QModelIndex() ) :

		if parent.isValid() :
			return 0

		return len( self.__columns )

	def headerData( self, section, orientation, role ) :

		if QtCore is None :
			# it seems that this is sometimes getting called during python shutdown.
			# during shutdown python makes all module globals reference None, so
			# QtCore becomes None, and we can't do anything. just return None and
			# hope for the best.
			return None

		if role == QtCore.Qt.DisplayRole :
			if orientation == QtCore.Qt.Horizontal :
				column = self.__columns[section]
				if self.__header is not None :
					result = self.__header[self.columnToDataIndex(section)[0]]
					if column.accessor.numColumns() > 1 :
						suffix = column.accessor.headerLabel( column.relativeColumnIndex )
						result += ( "." + suffix ) if suffix is not None else ""
				else :
					result = column.accessor.headerLabel( column.relativeColumnIndex )
				return GafferUI._Variant.toVariant( result )
			else :
				return GafferUI._Variant.toVariant( section )
		elif role == QtCore.Qt.ToolTipRole :
			if orientation == QtCore.Qt.Horizontal and self.__toolTips is not None :
				return GafferUI._Variant.toVariant( self.__toolTips[self.columnToDataIndex(section)[0]] )

		return GafferUI._Variant.toVariant( None )

	def flags( self, index ) :

		result = (
			QtCore.Qt.ItemIsSelectable |
			QtCore.Qt.ItemIsEnabled |
			QtCore.Qt.ItemIsDragEnabled
		)

		if self.__editable :
			if self.__columnEditability is None or self.__columnEditability[index.column()] :
				result |= QtCore.Qt.ItemIsEditable

		return result

	def data( self, index, role ) :

		column = self.__columns[index.column()]
		if role == QtCore.Qt.BackgroundColorRole :

			if self.columnToDataIndex( index.column() )[0] % 2 == 0:
				return  GafferUI._Variant.toVariant( GafferUI._StyleSheet.styleColor("background")  )
			else:
				return  GafferUI._Variant.toVariant( GafferUI._StyleSheet.styleColor("backgroundAlt") )

		if (
			role == QtCore.Qt.DisplayRole or
			role == QtCore.Qt.EditRole
		) :
			if index.row() < len( column.accessor.data() ) :
				return column.accessor.getElement( index.row(), column.relativeColumnIndex )

		return GafferUI._Variant.toVariant( None )

	def setData( self, index, value, role ) :

		if role == QtCore.Qt.EditRole :
			column = self.__columns[index.column()]
			column.accessor.setElement( index.row(), column.relativeColumnIndex, value )

			if Qt.__binding__ in ( "PySide2", "PyQt5" ) :
				self.dataChanged.emit( index, index, [ QtCore.Qt.DisplayRole, QtCore.Qt.EditRole ] )
			else:
				self.dataChanged.emit( index, index )

		return True

# The _DataAccessor classes are responsible for converting from the Cortex data representation to the
# Qt (QVariant) representation.
class _DataAccessor( object ) :

	def __init__( self, data ) :

		self.__data = data

	def data( self ) :

		return self.__data

	def numColumns( self ) :

		return 1

	def headerLabel( self, columnIndex ) :

		return [ "X", "Y", "Z" ][columnIndex]

	def defaultElement( self ) :

		elementType = IECore.DataTraits.valueTypeFromSequenceType( type( self.data() ) )
		return elementType( 0 )

	def setElement( self, rowIndex, columnIndex, value ) :

		self.data()[rowIndex] = GafferUI._Variant.fromVariant( value )

	def getElement( self, rowIndex, columnIndex ) :

		return GafferUI._Variant.toVariant( self.data()[rowIndex] )

	# Factory methods
	#################################

	@classmethod
	def create( cls, data ) :

		typeIds = [ data.typeId() ] + IECore.RunTimeTyped.baseTypeIds( data.typeId() )
		for typeId in typeIds :
			creator = cls.__typesToCreators.get( typeId, None )
			if creator is not None :
				return creator( data )

		return None

	@classmethod
	def registerType( cls, typeId, creator ) :

		cls.__typesToCreators[typeId] = creator

	__typesToCreators = {}

_DataAccessor.registerType( IECore.BoolVectorData.staticTypeId(), _DataAccessor )
_DataAccessor.registerType( IECore.HalfVectorData.staticTypeId(), _DataAccessor )
_DataAccessor.registerType( IECore.FloatVectorData.staticTypeId(), _DataAccessor )
_DataAccessor.registerType( IECore.DoubleVectorData.staticTypeId(), _DataAccessor )
_DataAccessor.registerType( IECore.CharVectorData.staticTypeId(), _DataAccessor )
_DataAccessor.registerType( IECore.UCharVectorData.staticTypeId(), _DataAccessor )
_DataAccessor.registerType( IECore.ShortVectorData.staticTypeId(), _DataAccessor )
_DataAccessor.registerType( IECore.UShortVectorData.staticTypeId(), _DataAccessor )
_DataAccessor.registerType( IECore.IntVectorData.staticTypeId(), _DataAccessor )
_DataAccessor.registerType( IECore.UIntVectorData.staticTypeId(), _DataAccessor )
_DataAccessor.registerType( IECore.Int64VectorData.staticTypeId(), _DataAccessor )
_DataAccessor.registerType( IECore.UInt64VectorData.staticTypeId(), _DataAccessor )

class _CompoundDataAccessor( _DataAccessor ) :

	def __init__( self, data ) :

		_DataAccessor.__init__( self, data )

	def numColumns( self ) :

		v = IECore.DataTraits.valueTypeFromSequenceType( type( self.data() ) )
		return v.dimensions()

	def headerLabel( self, columnIndex ) :

		return [ "X", "Y", "Z", "W" ][columnIndex]

	def setElement( self, rowIndex, columnIndex, value ) :

		element = self.data()[rowIndex]
		element[columnIndex] = GafferUI._Variant.fromVariant( value )
		self.data()[rowIndex] = element

	def getElement( self, rowIndex, columnIndex ) :

		return GafferUI._Variant.toVariant( self.data()[rowIndex][columnIndex] )

_DataAccessor.registerType( IECore.V2iVectorData.staticTypeId(), _CompoundDataAccessor )
_DataAccessor.registerType( IECore.V2fVectorData.staticTypeId(), _CompoundDataAccessor )
_DataAccessor.registerType( IECore.V2dVectorData.staticTypeId(), _CompoundDataAccessor )

_DataAccessor.registerType( IECore.V3iVectorData.staticTypeId(), _CompoundDataAccessor )
_DataAccessor.registerType( IECore.V3fVectorData.staticTypeId(), _CompoundDataAccessor )
_DataAccessor.registerType( IECore.V3dVectorData.staticTypeId(), _CompoundDataAccessor )

class _ColorDataAccessor( _CompoundDataAccessor ) :

	def __init__( self, data ) :

		_CompoundDataAccessor.__init__( self, data )

	def setElement( self, rowIndex, columnIndex, value ) :

		if columnIndex < self.numColumns() - 1 :
			_CompoundDataAccessor.setElement( self, rowIndex, columnIndex, value )
		else :
			self.data()[rowIndex] = GafferUI._Variant.fromVariant( value )

	def getElement( self, rowIndex, columnIndex ) :

		if columnIndex < self.numColumns() - 1 :
			return _CompoundDataAccessor.getElement( self, rowIndex, columnIndex )
		else :
			return GafferUI._Variant.toVariant( self.data()[rowIndex] )

class _Color3fDataAccessor( _ColorDataAccessor ) :

	def __init__( self, data ) :

		_ColorDataAccessor.__init__( self, data )

	def numColumns( self ) :

		return 4

	def headerLabel( self, columnIndex ) :

		return [ "R", "G", "B", None ][columnIndex]

class _Color4fDataAccessor( _ColorDataAccessor ) :

	def __init__( self, data ) :

		_ColorDataAccessor.__init__( self, data )

	def numColumns( self ) :

		return 5

	def headerLabel( self, columnIndex ) :

		return [ "R", "G", "B", "A", None ][columnIndex]

_DataAccessor.registerType( IECore.Color3fVectorData.staticTypeId(), _Color3fDataAccessor )
_DataAccessor.registerType( IECore.Color4fVectorData.staticTypeId(), _Color4fDataAccessor )

class _QuatDataAccessor( _CompoundDataAccessor ) :

	def __init__( self, data  ) :

		_CompoundDataAccessor.__init__( self, data )

	def numColumns( self ) :

		return 4

	def getElement( self, rowIndex, columnIndex ) :

		v = self.data()[rowIndex]
		if columnIndex == 0:
			return GafferUI._Variant.toVariant( v.v()[0] )
		if columnIndex == 1:
			return GafferUI._Variant.toVariant( v.v()[1] )
		if columnIndex == 2:
			return GafferUI._Variant.toVariant( v.v()[2] )
		if columnIndex == 3:
			return GafferUI._Variant.toVariant( v.r() )

_DataAccessor.registerType( IECore.QuatfVectorData.staticTypeId(), _QuatDataAccessor )
_DataAccessor.registerType( IECore.QuatdVectorData.staticTypeId(), _QuatDataAccessor )

class _BoxDataAccessor( _CompoundDataAccessor ) :

	def __init__( self, data ) :

		_DataAccessor.__init__( self, data  )

	def numColumns( self ) :

		v = IECore.DataTraits.valueTypeFromSequenceType( type( self.data() ) )
		return v().min().dimensions() * 2

	def headerLabel( self, columnIndex ) :

		if self.numColumns() == 4:
			return [ "minX", "minY", "maxX", "maxY" ][columnIndex]
		else:
			return [ "minX", "minY", "minZ", "maxX", "maxY", "maxZ" ][columnIndex]

	def setElement( self, rowIndex, columnIndex, value ) :

		element = self.data()[rowIndex]
		element[columnIndex] = GafferUI._Variant.fromVariant( value )
		self.data()[rowIndex] = element

	def getElement( self, rowIndex, columnIndex ) :

		dimension = self.numColumns() // 2

		index = columnIndex % dimension
		minMax = (columnIndex - index) / dimension
		item = self.data()[rowIndex]
		if minMax == 0:
			return GafferUI._Variant.toVariant( item.min()[index] )
		else:
			return GafferUI._Variant.toVariant( item.max()[index] )

_DataAccessor.registerType( IECore.Box2iVectorData.staticTypeId(), _BoxDataAccessor )
_DataAccessor.registerType( IECore.Box2fVectorData.staticTypeId(), _BoxDataAccessor )
_DataAccessor.registerType( IECore.Box2dVectorData.staticTypeId(), _BoxDataAccessor )

_DataAccessor.registerType( IECore.Box3iVectorData.staticTypeId(), _BoxDataAccessor )
_DataAccessor.registerType( IECore.Box3fVectorData.staticTypeId(), _BoxDataAccessor )
_DataAccessor.registerType( IECore.Box3dVectorData.staticTypeId(), _BoxDataAccessor )

class _MatrixDataAccessor( _DataAccessor ) :

	def __init__( self, data ) :

		_DataAccessor.__init__( self, data )

	def numColumns( self ) :

		scalarType = IECore.DataTraits.valueTypeFromSequenceType( type ( self.data() ) )()
		if isinstance(scalarType, imath.M33f) or isinstance(scalarType, imath.M33d) :
			return 9
		elif isinstance(scalarType, imath.M44f) or isinstance(scalarType, imath.M44d) :
			return 16


	def headerLabel( self, columnIndex ) :

		return "[{}]".format( columnIndex )

	def setElement( self, rowIndex, columnIndex, value ) :

		element = self.data()[rowIndex]
		element[columnIndex] = GafferUI._Variant.fromVariant( value )
		self.data()[rowIndex] = element

	def getElement( self, rowIndex, columnIndex ) :

		if self.numColumns() == 16:
			dimension = 4
		else:
			dimension = 3

		y = columnIndex % dimension
		x = (columnIndex - y) // dimension
		item = self.data()[rowIndex]

		return GafferUI._Variant.toVariant( item[x][y] )

_DataAccessor.registerType( IECore.M33fVectorData.staticTypeId(), _MatrixDataAccessor )
_DataAccessor.registerType( IECore.M33dVectorData.staticTypeId(), _MatrixDataAccessor )
_DataAccessor.registerType( IECore.M44fVectorData.staticTypeId(), _MatrixDataAccessor )
_DataAccessor.registerType( IECore.M44dVectorData.staticTypeId(), _MatrixDataAccessor )

class _StringDataAccessor( _DataAccessor ) :

	def __init__( self, data ) :

		_DataAccessor.__init__( self, data )

	def defaultElement( self ) :

		return ""

_DataAccessor.registerType( IECore.StringVectorData.staticTypeId(), _StringDataAccessor )

class _InternedStringDataAccessor( _StringDataAccessor ) :

	def __init__( self, data ) :

		_DataAccessor.__init__( self, data )

	def getElement( self, rowIndex, columnIndex ) :

		return GafferUI._Variant.toVariant( self.data()[rowIndex].value() )

_DataAccessor.registerType( IECore.InternedStringVectorData.staticTypeId(), _InternedStringDataAccessor )

# The _Delegate classes are used to decide how the different types of data are
# displayed. They derive from QStyledItemDelegate for drawing and event handling,
# but also have additional methods to specify sizing.
class _Delegate( QtWidgets.QStyledItemDelegate ) :

	def __init__( self ) :

		QtWidgets.QStyledItemDelegate.__init__( self )

		# The closeEditor signal is used to tell the view that editing is complete,
		# at which point it will destroy the QWidget used for editing.
		# It is emitted from QtWidgets.QAbstractItemDelegate.eventFilter() and also from
		# our own eventFilter() to stop editing. We connect to it here so that we can
		# drop our reference to self.__editor (a GafferUI.Widget) when editing finishes -
		# otherwise it would live on but with its Qt half already destroyed, which would
		# likely give rise to errors.
		self.closeEditor.connect( self.__closeEditor )

	# Qt methods we override
	########################

	def createEditor( self, parent, option, index ) :

		# see if editSignal() has been connected up to provide a custom editor.
		vectorDataWidget = GafferUI.Widget._owner( parent ).ancestor( VectorDataWidget )
		self.__editor = vectorDataWidget.editSignal()( vectorDataWidget, index.column(), index.row() )

		# if it hasn't, then see if a derived class can provide a custom editor.
		if self.__editor is None :
			self.__editor = self._createEditorInternal( index )

		# set up the custom editor if we have one, otherwise
		# fall through to the base class which will provide a default
		# editor.
		if self.__editor is not None :
			if not isinstance( self.__editor, GafferUI.Window ) :
				self.__editor._qtWidget().setParent( parent )
			return self.__editor._qtWidget()
		else :
			return QtWidgets.QStyledItemDelegate.createEditor( self, parent, option, index )

	def updateEditorGeometry( self, editor, option, index ) :

		if not isinstance( self.__editor, GafferUI.Window ) :
			QtWidgets.QStyledItemDelegate.updateEditorGeometry( self, editor, option, index )
		else :
			# Windows can't be conformed to the cell geometry
			pass

	def setEditorData( self, editor, index ) :

		if self.__editor is not None :
			self.__editor.setValue( GafferUI._Variant.fromVariant( index.data() ) )
		else :
			QtWidgets.QStyledItemDelegate.setEditorData( self, editor, index )

	def setModelData( self, editor, model, index ) :

		if self.__editor is not None :
			model.setData( index, GafferUI._Variant.toVariant( self.__editor.getValue() ), QtCore.Qt.EditRole )
		else :
			QtWidgets.QStyledItemDelegate.setModelData( self, editor, model, index )

	def eventFilter( self, object, event ) :

		if QtWidgets.QStyledItemDelegate.eventFilter( self, object, event ) :
			return True

		if event.type() == event.Hide and self.__editor is not None :
			# custom editors may hide themselves to indicate that editing
			# is complete. when this happens we are responsible for carrying
			# out this completion.
			self.commitData.emit( self.__editor._qtWidget() )
			self.closeEditor.emit( self.__editor._qtWidget(), self.NoHint )

		return False

	# Methods we define for our own purposes
	########################################

	def canStretch( self ) :

		return False

	# Called by createEditor() if editSignal() doesn't provide a custom widget.
	# Derived classes may override this to return a GafferUI.Widget to be used
	# for editing if they wish to override the default behaviour.
	def _createEditorInternal( self, index ) :

		return None

	@classmethod
	def create( cls, data ) :

		typeIds = [ data.typeId() ] + IECore.RunTimeTyped.baseTypeIds( data.typeId() )
		for typeId in typeIds :
			creator = cls.__typesToCreators.get( typeId, None )
			if creator is not None :
				return creator()

		return None

	@classmethod
	def registerType( cls, typeId, creator ) :

		cls.__typesToCreators[typeId] = creator

	__typesToCreators = {}

	def __closeEditor( self ) :

		# the QWidget for the editor is being destroyed - also destroy
		# the GafferUI.Widget that wrapped it.
		self.__editor = None

# A delegate to ensure that numeric editing is performed by our NumericWidget
# class, complete with cursor increments and virtual sliders, rather than the
# built in qt one.
class _NumericDelegate( _Delegate ) :

	def __init__( self ) :

		_Delegate.__init__( self )

	def _createEditorInternal( self, index ) :

		return GafferUI.NumericWidget( GafferUI._Variant.fromVariant( index.data() ) )

_Delegate.registerType( IECore.HalfVectorData.staticTypeId(), _NumericDelegate )
_Delegate.registerType( IECore.FloatVectorData.staticTypeId(), _NumericDelegate )
_Delegate.registerType( IECore.DoubleVectorData.staticTypeId(), _NumericDelegate )
_Delegate.registerType( IECore.CharVectorData.staticTypeId(), _NumericDelegate )
_Delegate.registerType( IECore.UCharVectorData.staticTypeId(), _NumericDelegate )
_Delegate.registerType( IECore.ShortVectorData.staticTypeId(), _NumericDelegate )
_Delegate.registerType( IECore.UShortVectorData.staticTypeId(), _NumericDelegate )
_Delegate.registerType( IECore.IntVectorData.staticTypeId(), _NumericDelegate )
_Delegate.registerType( IECore.UIntVectorData.staticTypeId(), _NumericDelegate )
_Delegate.registerType( IECore.Int64VectorData.staticTypeId(), _NumericDelegate )
_Delegate.registerType( IECore.UInt64VectorData.staticTypeId(), _NumericDelegate )
_Delegate.registerType( IECore.FloatVectorData.staticTypeId(), _NumericDelegate )

_Delegate.registerType( IECore.V2iVectorData.staticTypeId(), _NumericDelegate )
_Delegate.registerType( IECore.V2fVectorData.staticTypeId(), _NumericDelegate )
_Delegate.registerType( IECore.V2dVectorData.staticTypeId(), _NumericDelegate )

_Delegate.registerType( IECore.V3iVectorData.staticTypeId(), _NumericDelegate )
_Delegate.registerType( IECore.V3fVectorData.staticTypeId(), _NumericDelegate )
_Delegate.registerType( IECore.V3dVectorData.staticTypeId(), _NumericDelegate )

_Delegate.registerType( IECore.M33fVectorData.staticTypeId(), _NumericDelegate )
_Delegate.registerType( IECore.M33dVectorData.staticTypeId(), _NumericDelegate )
_Delegate.registerType( IECore.M44fVectorData.staticTypeId(), _NumericDelegate )
_Delegate.registerType( IECore.M44dVectorData.staticTypeId(), _NumericDelegate )

_Delegate.registerType( IECore.Box2iVectorData.staticTypeId(), _NumericDelegate )
_Delegate.registerType( IECore.Box2fVectorData.staticTypeId(), _NumericDelegate )
_Delegate.registerType( IECore.Box2dVectorData.staticTypeId(), _NumericDelegate )

_Delegate.registerType( IECore.Box3iVectorData.staticTypeId(), _NumericDelegate )
_Delegate.registerType( IECore.Box3fVectorData.staticTypeId(), _NumericDelegate )
_Delegate.registerType( IECore.Box3dVectorData.staticTypeId(), _NumericDelegate )

_Delegate.registerType( IECore.QuatfVectorData.staticTypeId(), _NumericDelegate )
_Delegate.registerType( IECore.QuatdVectorData.staticTypeId(), _NumericDelegate )

# A delegate that creates a `_NumericDelegate` for each of the color components
# and an editable color swatch for the color column.
class _ColorDelegate( _Delegate ) :

	def __init__( self ) :

		_Delegate.__init__( self )

		self.__colorChooser = None
		self.__popup = None

		self.__checkerBoardColor0 = imath.Color3f( 0.1 )
		self.__checkerBoardColor1 = imath.Color3f( 0.2 )

	def paint( self, painter, option, index ) :

		value = self.__colorData( index )

		if isinstance( value, float ) :
			_Delegate.paint( self, painter, option, index )
		else :
			# in PyQt, option is passed to us correctly as a QStyleOptionViewItemV4,
			# but in PySide it is merely a QStyleOptionViewItem and we must "cast" it.
			if hasattr( QtGui, "QStyleOptionViewItemV4" ) :
				option = QtGui.QStyleOptionViewItemV4( option )

			# in PyQt, we can access the widget with option.widget, but in PySide it
			# is always None for some reason, so we jump through some hoops to get the
			# widget via our parent.
			widget = QtCore.QObject.parent( self.parent() )

			# draw the background

			widget.style().drawControl( QtWidgets.QStyle.CE_ItemViewItem, option, painter, widget )
			displayTransform = GafferUI.Widget._owner( widget ).displayTransform()
			transformedColor = displayTransform( value )

			opaqueCheckerColor0 = GafferUI.Widget._qtColor( transformedColor )
			opaqueCheckerColor1 = opaqueCheckerColor0
			transparentCheckerColor0 = opaqueCheckerColor0
			transparentCheckerColor1 = opaqueCheckerColor0

			if isinstance( value, imath.Color4f ) :
				transparentCheckerColor0 = self.__checkerBoardColor0 * ( 1.0 - value.a ) + imath.Color3f( value.r, value.g, value.b ) * value.a
				transparentCheckerColor1 = self.__checkerBoardColor1 * ( 1.0 - value.a ) + imath.Color3f( value.r, value.g, value.b ) * value.a

				transparentCheckerColor0 = GafferUI.Widget._qtColor( displayTransform( transparentCheckerColor0 ) )
				transparentCheckerColor1 = GafferUI.Widget._qtColor( displayTransform( transparentCheckerColor1 ) )

			padding = 2
			size = imath.V2i( min( option.rect.height() - padding * 2, option.rect.width() ), ( option.rect.height() - padding * 2 ) * 0.5 )
			topLeft = imath.V2i( option.rect.x() + option.rect.width() * 0.5 - size.x * 0.5, option.rect.y() + padding )

			topRect = QtCore.QRectF( topLeft.x, topLeft.y, size.x, size.y )
			bottomRect = QtCore.QRectF( topLeft.x, topLeft.y + size.y, size.x, size.y )
			_Checker._paintRectangle(
				painter,
				topRect,
				opaqueCheckerColor0,
				opaqueCheckerColor1
			)
			_Checker._paintRectangle(
				painter,
				bottomRect,
				transparentCheckerColor0,
				transparentCheckerColor1
			)

	def _createEditorInternal( self, index ) :

		value = self.__colorData( index )

		if isinstance( value, float ) :
			return GafferUI.NumericWidget( value )
		else :
			self.__colorChooser = GafferUI.ColorChooser( value )
			self.__popup = GafferUI.PopupWindow( "", child = self.__colorChooser )

			self.__popup.popup( parent = self )

			return self.__popup

	def setEditorData( self, editor, index ) :

		value = self.__colorData( index )
		if isinstance( value, float ) :
			_Delegate.setEditorData( self, editor, index )
		else :
			self.__colorChooser.setColor( value )

	def setModelData( self, editor, model, index ) :

		if self.__colorChooser is None :
			_Delegate.setModelData( self, editor, model, index )
		else :
			model.setData( index, self.__colorChooser.getColor(), QtCore.Qt.EditRole )

	def __colorData( self, index ) :

		return index.model().data( index, QtCore.Qt.DisplayRole )

_Delegate.registerType( IECore.Color3fVectorData.staticTypeId(), _ColorDelegate )
_Delegate.registerType( IECore.Color4fVectorData.staticTypeId(), _ColorDelegate )

class _BoolDelegate( _Delegate ) :

	def __init__( self ) :

		_Delegate.__init__( self )

	def paint( self, painter, option, index ) :

		# in PyQt, option is passed to us correctly as a QStyleOptionViewItemV4,
		# but in PySide it is merely a QStyleOptionViewItem and we must "cast" it.
		if hasattr( QtGui, "QStyleOptionViewItemV4" ) :
			option = QtGui.QStyleOptionViewItemV4( option )

		# in PyQt, we can access the widget with option.widget, but in PySide it
		# is always None for some reason, so we jump through some hoops to get the
		# widget via our parent.
		widget = QtCore.QObject.parent( self.parent() )

		# draw the background

		widget.style().drawControl( QtWidgets.QStyle.CE_ItemViewItem, option, painter, widget )

		# draw the checkbox.

		styleOption = QtWidgets.QStyleOptionButton()
		styleOption.state = option.state
		styleOption.state |= QtWidgets.QStyle.State_Enabled

		if self.__toBool( index ) :
			styleOption.state |= QtWidgets.QStyle.State_On
		else :
			styleOption.state |= QtWidgets.QStyle.State_Off

		styleOption.rect = self.__checkBoxRect( widget, option.rect )
		widget.style().drawControl( QtWidgets.QStyle.CE_CheckBox, styleOption, painter, widget )

	def createEditor( self, parent, option, index ) :

		return None

	def editorEvent( self, event, model, option, index ) :

		if not ( index.flags() & QtCore.Qt.ItemIsEditable ) :
			return False

		if event.type()==QtCore.QEvent.MouseButtonDblClick :
			# eat event so an editor doesn't get created
			return True
		elif event.type()==QtCore.QEvent.MouseButtonPress :
			# eat event so row isn't selected
			widget = QtCore.QObject.parent( self.parent() )
			rect = self.__checkBoxRect( widget, option.rect )
			if event.button() == QtCore.Qt.LeftButton and rect.contains( event.pos() ) :
				checked = self.__toBool( index )
				model.setData( index, not checked, QtCore.Qt.EditRole )
				return True
		elif event.type()==QtCore.QEvent.KeyPress :
			if event.key() in ( QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter ) :
				checked = self.__toBool( index )
				model.setData( index, not checked, QtCore.Qt.EditRole )
				return True

		return False

	def __checkBoxRect( self, widget, viewItemRect ) :

		checkBoxStyleOption = QtWidgets.QStyleOptionButton()
		r = widget.style().subElementRect( QtWidgets.QStyle.SE_CheckBoxIndicator, checkBoxStyleOption )

		return QtCore.QRect(
			viewItemRect.center() - ( QtCore.QPoint( r.width(), r.height() ) / 2 ),
			r.size()
		)

	def __toBool( self, index ) :

		return GafferUI._Variant.fromVariant( index.model().data( index, QtCore.Qt.DisplayRole ) )

_Delegate.registerType( IECore.BoolVectorData.staticTypeId(), _BoolDelegate )

class _StringDelegate( _Delegate ) :

	def __init__( self ) :

		_Delegate.__init__( self )

	def canStretch( self ) :

		return True

_Delegate.registerType( IECore.StringVectorData.staticTypeId(), _StringDelegate )
_Delegate.registerType( IECore.InternedStringVectorData.staticTypeId(), _StringDelegate )
