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

import IECore

import Gaffer
import GafferUI

QtCore = GafferUI._qtImport( "QtCore" )
QtGui = GafferUI._qtImport( "QtGui" )

## The VectorDataWidget provides a table view for the contents of
# one or more IECore VectorData instances.
class VectorDataWidget( GafferUI.Widget ) :

	## data may either be a VectorData instance or a list of VectorData instances
	# of identical length.
	#
	# header may be False for no header, True for a default header, or a list of
	# strings to specify a custom header per column.
	#
	# minimumVisibleRows specifies a number of rows after which a vertical scroll bar
	# may become visible - before this all rows should be directly visible with no need
	# for scrolling.
	#
	# columnToolTips may be specified as a list of strings to provide a tooltip for
	# each column.
	#
	# sizeEditable specifies whether or not items may be added and removed
	# from the data (assuming it is editable).
	def __init__(
		self,
		data=None,
		editable=True,
		header=False,
		showIndices=True,
		minimumVisibleRows=8,
		columnToolTips=None,
		sizeEditable=True,
		**kw
	) :
	
		self.__column = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical )
	
		GafferUI.Widget.__init__( self, self.__column, **kw )
		
		# table view
		
		self.__tableView = _TableView( minimumVisibleRows = minimumVisibleRows )
						
		self.__tableView.horizontalHeader().setVisible( bool( header ) )
		self.__tableView.horizontalHeader().setMinimumSectionSize( 70 )
		
		self.__tableView.verticalHeader().setVisible( showIndices )
		self.__tableView.verticalHeader().setResizeMode( QtGui.QHeaderView.Fixed )
		self.__tableView.verticalHeader().setObjectName( "vectorDataWidgetVerticalHeader" )

		self.__tableView.setHorizontalScrollBarPolicy( QtCore.Qt.ScrollBarAlwaysOff )
		self.__tableView.setVerticalScrollBarPolicy( QtCore.Qt.ScrollBarAsNeeded )
		
		self.__tableView.setSelectionBehavior( QtGui.QAbstractItemView.SelectItems )
		self.__tableView.setCornerButtonEnabled( False )
	
		self.__tableView.setContextMenuPolicy( QtCore.Qt.CustomContextMenu )
		self.__tableView.customContextMenuRequested.connect( Gaffer.WeakMethod( self.__contextMenu ) )

		self.__tableView.verticalHeader().setDefaultSectionSize( 20 )
	
		self.__tableViewHolder = GafferUI.Widget( self.__tableView )
		self.__column.append( self.__tableViewHolder )
		
		# buttons
		
		self.__buttonRow = GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Horizontal )
		
		addButton = GafferUI.Button( image="plus.png", hasFrame=False )
		self.__addButtonConnection = addButton.clickedSignal().connect( Gaffer.WeakMethod( self.__addRows ) )
		self.__buttonRow.append( addButton )
		
		removeButton = GafferUI.Button( image="minus.png", hasFrame=False )
		self.__removeButtonConnection = removeButton.clickedSignal().connect( Gaffer.WeakMethod( self.__removeSelection ) )
		self.__buttonRow.append( removeButton )
		
		self.__buttonRow.append( GafferUI.Spacer( size = IECore.V2i( 0 ), maximumSize = IECore.V2i( 100000, 1 ) ), expand=1 )
		self.__column.append( self.__buttonRow )
		
		# stuff for drag enter/leave and drop
		
		self.__dragEnterConnections = [
			self.dragEnterSignal().connect( Gaffer.WeakMethod( self.__dragEnter ) ),
			addButton.dragEnterSignal().connect( Gaffer.WeakMethod( self.__dragEnter ) ),
			removeButton.dragEnterSignal().connect( Gaffer.WeakMethod( self.__dragEnter ) ),
		]
		
		self.__dragLeaveConnections = [
			self.dragLeaveSignal().connect( Gaffer.WeakMethod( self.__dragLeave ) ),
			addButton.dragLeaveSignal().connect( Gaffer.WeakMethod( self.__dragLeave ) ),
			removeButton.dragLeaveSignal().connect( Gaffer.WeakMethod( self.__dragLeave ) ),
		]
		
		self.__dropConnections = [
			self.dropSignal().connect( Gaffer.WeakMethod( self.__drop ) ),
			addButton.dropSignal().connect( Gaffer.WeakMethod( self.__drop ) ),
			removeButton.dropSignal().connect( Gaffer.WeakMethod( self.__drop ) ),
		]
		
		# stuff for drag begin
		
		self.__borrowedButtonPress = None
		self.__emittingButtonPress = False
		self.__buttonPressConnection = self.__tableViewHolder.buttonPressSignal().connect( Gaffer.WeakMethod( self.__buttonPress ) )
		self.__buttonReleaseConnection = self.__tableViewHolder.buttonReleaseSignal().connect( Gaffer.WeakMethod( self.__buttonRelease ) )
		self.__dragBeginConnection = self.__tableViewHolder.dragBeginSignal().connect( Gaffer.WeakMethod( self.__dragBegin ) )

		# final setup
		
		self.__dataChangedSignal = GafferUI.WidgetSignal()
		
		if isinstance( header, list ) :
			self.__headerOverride = header
		else :
			self.__headerOverride = None
		
		self.__columnToolTips = columnToolTips
		
		self.__propagatingDataChangesToSelection = False
		
		self.__sizeEditable = sizeEditable
		self.setData( data )
		self.setEditable( editable )
	
	def setHighlighted( self, highlighted ) :
		
		if highlighted == self.getHighlighted() :
			return
			
		self.__tableView.setProperty( "gafferHighlighted", GafferUI._Variant.toVariant( highlighted ) )
		
		GafferUI.Widget.setHighlighted( self, highlighted )
				
	def setData( self, data ) :
		
		# it could be argued that we should early out here if data is self.getData(),
		# but we can't right now as we're relying on setData() to update everything
		# when the data has been modified in place by some external process, or
		# by self.__removeSelection.
							
		if data is not None :
			if not isinstance( data, list ) :
				data = [ data ]
			self.__model = _Model( data, self.__tableView, self.getEditable(), self.__headerOverride, self.__columnToolTips )
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

			self.__tableView.horizontalHeader().setResizeMode(
				QtGui.QHeaderView.ResizeToContents if haveResizeableContents else QtGui.QHeaderView.Fixed
			)
			self.__tableView.horizontalHeader().setStretchLastSection( canStretch )
			self.__tableView.setSizePolicy(
				QtGui.QSizePolicy(
					QtGui.QSizePolicy.Expanding if canStretch else QtGui.QSizePolicy.Fixed,
					QtGui.QSizePolicy.Maximum
				)
			)
		
		# Somehow the QTableView can leave its header in a state where updates are disabled.
		# If we didn't turn them back on, the header would disappear.
		self.__tableView.verticalHeader().setUpdatesEnabled( True )
		self.__tableView.updateGeometry()
	
	## Returns the data being displayed. This is always returned as a list of
	# VectorData instances, even if only one instance was passed to setData().	
	def getData( self ) :
	
		return self.__model.vectorData()
			
	def setEditable( self, editable ) :
	
		# set object name so stylesheet can differentiate editable from
		# non editable in terms of the style. hide the add/remove buttons
		# if not editable.
		if editable :
			self.__tableView.setObjectName( "vectorDataWidgetEditable" )
			self.__buttonRow.setVisible( self.__sizeEditable )
		else :
			self.__tableView.setObjectName( "vectorDataWidget" )
			self.__buttonRow.setVisible( False )
		
		# update the model
		if self.__model is not None :
			self.__model.setEditable( editable )
		
	def getEditable( self ) :
	
		return self.__tableView.objectName()=="vectorDataWidgetEditable"
	
	def setSizeEditable( self, sizeEditable ) :
	
		if sizeEditable == self.__sizeEditable :
			return
		
		self.__sizeEditable = sizeEditable
		self.__buttonRow.setVisible( self.getEditable() and self.__sizeEditable )
	
	def getSizeEditable( self ) :
	
		return self.__sizeEditable
	
	## Returns a signal which is emitted whenever the data is edited.
	# The signal is /not/ emitted when setData() is called.
	def dataChangedSignal( self ) :
	
		return self.__dataChangedSignal
	
	## Returns a definition for the popup menu - this is called each time
	# the menu is displayed to allow menus to be built dynamically. May be
	# overridden in derived classes to modify the menu. 
	def _contextMenuDefinition( self, selectedIndices ) :
	
		m = IECore.MenuDefinition()
		
		m.append( "/Select All", { "command" : self.__selectAll } )
		m.append( "/Clear Selection", { "command" : self.__clearSelection } )
		
		if self.getEditable() and self.getSizeEditable() :

			m.append( "/divider", { "divider" : True } )
			m.append( "/Remove Selected Rows", { "command" : IECore.curry( Gaffer.WeakMethod( self.__removeIndices ), selectedIndices ) } )
		
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
	
	def __modelDataChanged( self, topLeft, bottomRight ) :
	
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
		m = self._contextMenuDefinition( self.__selectedIndices() )
		self.__popupMenu = GafferUI.Menu( m )
		self.__popupMenu.popup( self )
			
	def __selectAll( self ) :
	
		self.__tableView.selectAll()
		
	def __clearSelection( self ) :
	
		self.__tableView.clearSelection()
	
	def __selectedIndices( self ) :
	
		selectedIndices = [ x.row() for x in self.__tableView.selectedIndexes() ]
		selectedIndices = list( set( selectedIndices ) ) # remove duplicates
		selectedIndices.sort()
		
		return selectedIndices
	
	def __removeSelection( self, button ) :
	
		self.__removeIndices( self.__selectedIndices() )
	
	def __removeIndices( self, indices ) :
			
		data = self.getData()
			
		# delete the rows from data
		for i in range( len( indices )-1, -1, -1 ) :
			for d in data :
				del d[indices[i]]
		
		# tell the world
		self.setData( data )
		self.__emitDataChangedSignal()
		
	def __addRows( self, button ) :
	
		if self.__model is None :
			return
	
		newData = self._createRows()
		if not newData :
			return
			
		data = self.getData()
		assert( len( data ) == len( newData ) )
		for i in range( 0, len( data ) ) :
			data[i].extend( newData[i] )
					
		self.setData( data )
		
		self.__tableView.scrollToBottom()
		
		self.__emitDataChangedSignal()
				
	def __dragEnter( self, widget, event ) :
	
		if event.sourceWidget is self.__tableViewHolder and widget is not self.__buttonRow[1]:
			# we don't accept drags from ourself unless the target is the remove button
			return False
	
		data = self.getData()
		if len( data ) == 1 and event.data.isInstanceOf( data[0].typeId() ) :
			widget.setHighlighted( True )
			return True 

		return False

	def __dragLeave( self, widget, event ) :
	
		widget.setHighlighted( False )
		return True

	def __drop( self, widget, event ) :
	
		# dragEnter checked that we only had one data array
		data = self.getData()[0]
				
		if widget is self.__buttonRow[1] :
			# remove
			s = set( event.data )
			newData = data.__class__()
			for d in data :
				if d not in s :
					newData.append( d )
			data = newData	
		else :
			# add, but avoid creating duplicates
			s = set( data )
			for d in event.data :
				if d not in s :
					data.append( d )
					s.add( d )
		
		self.setData( [ data ] )
		self.dataChangedSignal()( self )
	
		widget.setHighlighted( False )

		return True

	def __buttonPress( self, widget, event ) :
		
		assert( widget is self.__tableViewHolder )
		
		if len( self.getData() ) != 1 :
			# we only act as a drag source when we have a single vector of data
			return False
						
		if self.__emittingButtonPress :
			return False
		
		self.__borrowedButtonPress = None
		if event.buttons == event.Buttons.Left and event.modifiers == event.Modifiers.None :
			
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
			
			index = self.__tableView.indexAt( QtCore.QPoint( event.line.p0.x, event.line.p0.y ) )
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
		
	def __dragBegin( self, widget, event ) :

		self.__borrowedButtonPress = None
		selectedIndices = self.__selectedIndices()
		if len( selectedIndices ) :		
			data = self.getData()[0]
			result = IECore.Object.create( data.typeId() )
			for i in selectedIndices :
				result.append( data[i] )
			return result
			
		return None
		
	def __emitButtonPress( self, event ) :
	
		qEvent = QtGui.QMouseEvent(
			QtCore.QEvent.MouseButtonPress,
			QtCore.QPoint( event.line.p0.x, event.line.p0.y ),
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
		
# Private implementation - a QTableView with custom size behaviour.
class _TableView( QtGui.QTableView ) :

	def __init__( self, minimumVisibleRows ) :
	
		QtGui.QTableView.__init__( self )
		
		self.__minimumVisibleRows = minimumVisibleRows
		
	def setModel( self, model ) :
	
		prevModel = self.model()
		if prevModel :
			prevModel.rowsInserted.disconnect( self.__sizeShouldChange )
			prevModel.rowsRemoved.disconnect( self.__sizeShouldChange )
			prevModel.dataChanged.connect( self.__sizeShouldChange )
	
		QtGui.QTableView.setModel( self, model )
	
		if model :
			model.rowsInserted.connect( self.__sizeShouldChange )
			model.rowsRemoved.connect( self.__sizeShouldChange )
			model.dataChanged.connect( self.__sizeShouldChange )

	def minimumSizeHint( self ) :
		
		# compute the minimum height to be the size of the header plus
		# a minimum number of rows specified in self.__minimumVisibleRows
		
		margins = self.contentsMargins()
		minimumHeight = margins.top() + margins.bottom()
		
		if not self.horizontalHeader().isHidden() :
			minimumHeight += self.horizontalHeader().sizeHint().height()
		
		numRows = self.verticalHeader().count()
		if numRows :
			minimumHeight += self.verticalHeader().sectionSize( 0 ) * min( numRows, self.__minimumVisibleRows )
		
		# horizontal direction doesn't matter, as we don't allow shrinking
		# in that direction anyway.
		
		return QtCore.QSize( 1, minimumHeight )
		
	def sizeHint( self ) :
						
		# this seems to be necessary to nudge the header into calculating
		# the correct size - otherwise the length() below comes out wrong
		# sometimes. in other words it's a hack.
		for i in range( 0, self.horizontalHeader().count() ) :
			self.horizontalHeader().sectionSize( i )
	
		margins = self.contentsMargins()
		
		w = self.horizontalHeader().length() + margins.left() + margins.right()
		if not self.verticalHeader().isHidden() :
			w += self.verticalHeader().sizeHint().width()
		# always allow room for a scrollbar even though we don't always need one. we
		# make sure the background in the stylesheet is transparent so that when the
		# scrollbar is hidden we don't draw an empty gap where it otherwise would be.
		w += self.verticalScrollBar().sizeHint().width()
				
		h = self.verticalHeader().length() + margins.top() + margins.bottom()
		if not self.horizontalHeader().isHidden() :
			h += self.horizontalHeader().sizeHint().height()
										
		return QtCore.QSize( w, h )

	def __sizeShouldChange( self, *unusedArgs ) :
		
		self.updateGeometry()
		
# Internal implementation detail - a qt model which wraps
# around the VectorData.		
class _Model( QtCore.QAbstractTableModel ) :

	__addValueText = "Add..."

	def __init__( self, data, parent=None, editable=True, header=None, columnToolTips=None ) :
	
		QtCore.QAbstractTableModel.__init__( self, parent )
				
		self.__data = data
		self.__editable = editable
		self.__header = header
		self.__columnToolTips = columnToolTips

		self.__columns = []
		self.__accessors = []
		for d in self.__data :
			accessor = _DataAccessor.create( d )
			assert( accessor is not None ) 
			for i in range( 0, accessor.numColumns() ) :
				self.__columns.append( IECore.Struct( accessor=accessor, relativeColumnIndex=i ) )
			self.__accessors.append( accessor )
							
	## Methods specific to this model first
	
	def vectorData( self ) :
	
		return self.__data
		
	def vectorDataAccessors( self ) :
	
		return self.__accessors
		
	def setEditable( self, editable ) :
	
		if self.__editable == editable :
			return
	
		self.__editable = editable
			
	def getEditable( self ) :
	
		return self.__editable
	
	## Then overrides for methods inherited from QAbstractModel
	
	def rowCount( self, parent ) :
	
		if parent.isValid() :
			return 0
		
		return len( self.__data[0] )
		
	def columnCount( self, parent ) :
	
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
				if self.__header is not None :
					return GafferUI._Variant.toVariant( self.__header[section] )
				else :
					column = self.__columns[section]
					return GafferUI._Variant.toVariant( column.accessor.headerLabel( column.relativeColumnIndex ) )
			else :
				return GafferUI._Variant.toVariant( section )
		elif role == QtCore.Qt.ToolTipRole :
			if orientation == QtCore.Qt.Horizontal and self.__columnToolTips is not None :
				return GafferUI._Variant.toVariant( self.__columnToolTips[section] )
		
		return GafferUI._Variant.toVariant( None )	

	def flags( self, index ) :
	
		result = (
			QtCore.Qt.ItemIsSelectable |
			QtCore.Qt.ItemIsEnabled |
			QtCore.Qt.ItemIsDragEnabled
		)
			
		if self.__editable :
			result |= QtCore.Qt.ItemIsEditable
		
		return result
		
	def data( self, index, role ) :
		
		if (
			role == QtCore.Qt.DisplayRole or 
			role == QtCore.Qt.EditRole
		) :
			column = self.__columns[index.column()]
			return column.accessor.getElement( index.row(), column.relativeColumnIndex )
		elif role == QtCore.Qt.ToolTipRole and self.__columnToolTips is not None :
			return GafferUI._Variant.toVariant( self.__columnToolTips[index.column()] )
			
		return GafferUI._Variant.toVariant( None )

	def setData( self, index, value, role ) :
	
		if role == QtCore.Qt.EditRole :
			column = self.__columns[index.column()]
			column.accessor.setElement( index.row(), column.relativeColumnIndex, value )
			self.dataChanged.emit( index, index )

		return True

# The _DataAccessor classes are responsible for converting from the Cortex data representation to the
# Qt (QVariant) representation.
class _DataAccessor() :

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
	
		if isinstance( self.data(), ( IECore.Color3fVectorData, IECore.Color4fVectorData ) ) :
			return [ "R", "G", "B", "A" ][columnIndex]
		else :
			return [ "X", "Y", "Z", "W" ][columnIndex]
		
	def setElement( self, rowIndex, columnIndex, value ) :
	
		element = self.data()[rowIndex]
		element[columnIndex] = GafferUI._Variant.fromVariant( value )
		self.data()[rowIndex] = element
	
	def getElement( self, rowIndex, columnIndex ) :
	
		return GafferUI._Variant.toVariant( self.data()[rowIndex][columnIndex] )

_DataAccessor.registerType( IECore.Color3fVectorData.staticTypeId(), _CompoundDataAccessor )
_DataAccessor.registerType( IECore.Color4fVectorData.staticTypeId(), _CompoundDataAccessor )
_DataAccessor.registerType( IECore.V3fVectorData.staticTypeId(), _CompoundDataAccessor )

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
class _Delegate( QtGui.QStyledItemDelegate ) :

	def __init__( self ) :
			
		QtGui.QStyledItemDelegate.__init__( self )
			
	def canStretch( self ) :
	
		return False
	
	# Factory methods
	#################################

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
	
_Delegate.registerType( IECore.HalfVectorData.staticTypeId(), _Delegate )
_Delegate.registerType( IECore.FloatVectorData.staticTypeId(), _Delegate )
_Delegate.registerType( IECore.DoubleVectorData.staticTypeId(), _Delegate )
_Delegate.registerType( IECore.IntVectorData.staticTypeId(), _Delegate )
_Delegate.registerType( IECore.UIntVectorData.staticTypeId(), _Delegate )
_Delegate.registerType( IECore.Int64VectorData.staticTypeId(), _Delegate )
_Delegate.registerType( IECore.UInt64VectorData.staticTypeId(), _Delegate )
_Delegate.registerType( IECore.FloatVectorData.staticTypeId(), _Delegate )
_Delegate.registerType( IECore.Color3fVectorData.staticTypeId(), _Delegate )
_Delegate.registerType( IECore.Color4fVectorData.staticTypeId(), _Delegate )
_Delegate.registerType( IECore.V3fVectorData.staticTypeId(), _Delegate )

class _BoolDelegate( _Delegate ) :

	def __init__( self ) :
	
		_Delegate.__init__( self )
				
	def paint( self, painter, option, index ) :
		
		# draw the background
		
		widget = option.widget	
		widget.style().drawControl( QtGui.QStyle.CE_ItemViewItem, option, painter, widget )
			
		# draw the checkbox.
					
		styleOption = QtGui.QStyleOptionButton()
		styleOption.state = option.state
		styleOption.state |= QtGui.QStyle.State_Enabled
		
		if index.model().data( index, QtCore.Qt.DisplayRole ).toBool() :
			styleOption.state |= QtGui.QStyle.State_On
		else :
			styleOption.state |= QtGui.QStyle.State_Off

		styleOption.rect = self.__checkBoxRect( widget, option.rect )
		widget.style().drawControl( QtGui.QStyle.CE_CheckBox, styleOption, painter, widget )

	def createEditor( self, parent, option, index ) :
	
		return None

	def editorEvent( self, event, model, option, index ) :
				
		if event.type()==QtCore.QEvent.MouseButtonDblClick :
			# eat event so an editor doesn't get created
			return True
		elif event.type()==QtCore.QEvent.MouseButtonPress :
			# eat event so row isn't selected
			rect = self.__checkBoxRect( option.widget, option.rect )
			if event.button() == QtCore.Qt.LeftButton and rect.contains( event.pos() ) :
				checked = index.model().data( index, QtCore.Qt.DisplayRole ).toBool()
				model.setData( index, not checked, QtCore.Qt.EditRole )
				return True
		elif event.type()==QtCore.QEvent.KeyPress :
			if event.key() in ( QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter ) :
				checked = index.model().data( index, QtCore.Qt.DisplayRole ).toBool()
				model.setData( index, not checked, QtCore.Qt.EditRole )
				return True

		return False

	def __checkBoxRect( self, widget, viewItemRect ) :
	
		checkBoxStyleOption = QtGui.QStyleOptionButton()
		r = widget.style().subElementRect( QtGui.QStyle.SE_CheckBoxIndicator, checkBoxStyleOption )
		
		return QtCore.QRect(
			viewItemRect.center() - ( QtCore.QPoint( r.width(), r.height() ) / 2 ),
			r.size()
		)

_Delegate.registerType( IECore.BoolVectorData.staticTypeId(), _BoolDelegate )

class _StringDelegate( _Delegate ) :

	def __init__( self ) :
	
		_Delegate.__init__( self )
				
	def canStretch( self ) :
	
		return True

_Delegate.registerType( IECore.StringVectorData.staticTypeId(), _StringDelegate )
_Delegate.registerType( IECore.InternedStringVectorData.staticTypeId(), _StringDelegate )
