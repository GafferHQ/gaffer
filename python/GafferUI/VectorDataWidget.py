##########################################################################
#  
#  Copyright (c) 2011, Image Engine Design Inc. All rights reserved.
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
	def __init__( self, data=None, editable=True, header=False, showIndices=True ) :
	
		GafferUI.Widget.__init__( self, _TableView() )
						
		self._qtWidget().horizontalHeader().setVisible( header )
		self._qtWidget().horizontalHeader().setResizeMode( QtGui.QHeaderView.Fixed )
		
		self._qtWidget().verticalHeader().setVisible( showIndices )
		self._qtWidget().verticalHeader().setResizeMode( QtGui.QHeaderView.Fixed )
		self._qtWidget().verticalHeader().setObjectName( "vectorDataWidgetVerticalHeader" )

		self._qtWidget().setHorizontalScrollBarPolicy( QtCore.Qt.ScrollBarAlwaysOff )
		self._qtWidget().setVerticalScrollBarPolicy( QtCore.Qt.ScrollBarAlwaysOff )
		
		self._qtWidget().setSelectionBehavior( QtGui.QAbstractItemView.SelectRows )
		self._qtWidget().setCornerButtonEnabled( False )
		
		self._qtWidget().setContextMenuPolicy( QtCore.Qt.CustomContextMenu )
		self._qtWidget().customContextMenuRequested.connect( Gaffer.WeakMethod( self.__contextMenu ) )

		self.__dataChangedSignal = GafferUI.WidgetSignal()
	
		self.setData( data )
		self.setEditable( editable )
	
	def setData( self, data ) :
		
		# it could be argued that we should early out here if data is self.getData(),
		# but we can't right now as we're relying on setData() to update everything
		# when the data has been modified in place by some external process, or
		# by self.__removeSelection.
					
		if data is not None :
			if not isinstance( data, list ) :
				data = [ data ]
			self.__model = _Model( data, self._qtWidget(), self.getEditable() )
			self.__model.dataChanged.connect( Gaffer.WeakMethod( self.__dataChanged ) )
			self.__model.rowsInserted.connect( Gaffer.WeakMethod( self.__dataChanged ) )
			self.__model.rowsRemoved.connect( Gaffer.WeakMethod( self.__dataChanged ) )
		else :
			self.__model = None
		
		self._qtWidget().setModel( self.__model )
		
		if self.__model :
		
			columnIndex = 0
			columnWidths = []
			for accessor in self.__model.vectorDataAccessors() :
				for i in range( 0, accessor.numColumns() ) :
					delegate = _Delegate.create( accessor.data() )
					delegate.setParent( self.__model )
					self._qtWidget().setItemDelegateForColumn( columnIndex, delegate )
					columnWidths.append( delegate.columnWidth() )
					canStretch = delegate.canStretch()
					columnIndex += 1

			self._qtWidget().horizontalHeader().setStretchLastSection( canStretch )
			self._qtWidget().setSizePolicy( QtGui.QSizePolicy( QtGui.QSizePolicy.Expanding if canStretch else QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed ) )

			# we have to call resizeSection after setStretchLastSection as otherwise it doesn't work
			for i in range( 0, len( columnWidths ) ) :
				self._qtWidget().horizontalHeader().resizeSection( i, columnWidths[i] )
		
		self._qtWidget().updateGeometry()
	
	## Returns the data being displayed. This is always returned as a list of
	# VectorData instances, even if only one instance was passd to setData().	
	def getData( self ) :
	
		return self.__model.vectorData()
			
	def setEditable( self, editable ) :
	
		# set object name so stylesheet can differentiate editable from
		# non editable in terms of the style.
		if editable :
			self._qtWidget().setObjectName( "vectorDataWidgetEditable" )
		else :
			self._qtWidget().setObjectName( "vectorDataWidget" )
		
		# update the model
		if self.__model is not None :
			self.__model.setEditable( editable )
		
	def getEditable( self ) :
	
		return self._qtWidget().objectName()=="vectorDataWidgetEditable"
	
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
		
		if self.getEditable() :

			m.append( "/divider", { "divider" : True } )
			m.append( "/Remove Selection", { "command" : IECore.curry( Gaffer.WeakMethod( self.__removeIndices ), selectedIndices ) } )
		
		return m
		
	def __dataChanged( self, *unusedArgs ) :
	
		self.dataChangedSignal()( self )
		
	def __contextMenu( self, pos ) :
	
		# get the selection
		selectedIndices = [ x.row() for x in self._qtWidget().selectedIndexes() ]
		selectedIndices = list( set( selectedIndices ) ) # remove duplicates
		selectedIndices.sort()
		
		# build the menu and pop it up
		m = self._contextMenuDefinition( selectedIndices )
		m = GafferUI.Menu( m )
		m.popup( self )
			
	def __selectAll( self ) :
	
		self._qtWidget().selectAll()
		
	def __clearSelection( self ) :
	
		self._qtWidget().clearSelection()
	
	def __removeIndices( self, indices ) :
			
		data = self.getData()
		
		# remove the "Add..." row which can't be deleted as it doesn't
		# exist in the data.
		if indices[-1] >= len( data ) :
			del indices[-1]
	
		# delete the rows from data
		for i in range( len( indices )-1, -1, -1 ) :
			for d in data :
				del d[indices[i]]
		
		# tell the world
		self.setData( data )
		self.__dataChanged()
	
# Private implementation - a QTableView which is much more forceful about
# requesting enough size if the scrollbars are off in a given direction.
class _TableView( QtGui.QTableView ) :

	def __init__( self ) :
	
		QtGui.QTableView.__init__( self )
				
	def setModel( self, model ) :
	
		prevModel = self.model()
		if prevModel :
			prevModel.rowsInserted.disconnect( self.__sizeShouldChange )
			prevModel.rowsRemoved.disconnect( self.__sizeShouldChange )
	
		QtGui.QTableView.setModel( self, model )
	
		if model :
			model.rowsInserted.connect( self.__sizeShouldChange )
			model.rowsRemoved.connect( self.__sizeShouldChange )
	
		self.updateGeometry()

	def minimumSizeHint( self ) :
	
		return QtCore.QSize()
		
	def sizeHint( self ) :
		
		result = QtGui.QTableView.sizeHint( self )
				
		margins = self.contentsMargins()
			
		if self.horizontalScrollBarPolicy()==QtCore.Qt.ScrollBarAlwaysOff :
			w = self.horizontalHeader().length() + margins.left() + margins.right()
			if not self.verticalHeader().isHidden() :
				w += self.verticalHeader().sizeHint().width()
				
			result.setWidth( w )

		if self.verticalScrollBarPolicy()==QtCore.Qt.ScrollBarAlwaysOff :
			h = self.verticalHeader().length() + margins.top() + margins.bottom()
			if not self.horizontalHeader().isHidden() :
				h += self.horizontalHeader().sizeHint().height()
			result.setHeight( h )		
										
		return result

	def __sizeShouldChange( self, *unusedArgs ) :
		
		self.updateGeometry()
		
# Internal implementation detail - a qt model which wraps
# around the VectorData.		
class _Model( QtCore.QAbstractTableModel ) :

	__addValueText = "Add..."

	def __init__( self, data, parent=None, editable=True ) :
	
		QtCore.QAbstractTableModel.__init__( self, parent )
				
		self.__data = data
		self.__editable = editable

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
				column = self.__columns[section]
				return GafferUI._Variant.toVariant( column.accessor.headerLabel( column.relativeColumnIndex ) )
			else :
				return GafferUI._Variant.toVariant( section )
		
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

_DataAccessor.registerType( IECore.StringVectorData.staticTypeId(), _DataAccessor )
_DataAccessor.registerType( IECore.FloatVectorData.staticTypeId(), _DataAccessor )
_DataAccessor.registerType( IECore.IntVectorData.staticTypeId(), _DataAccessor )
_DataAccessor.registerType( IECore.FloatVectorData.staticTypeId(), _DataAccessor )
_DataAccessor.registerType( IECore.BoolVectorData.staticTypeId(), _DataAccessor )

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

# The _Delegate classes are used to decide how the different types of data are
# displayed. They derive from QStyledItemDelegate for drawing and event handling,
# but also have additional methods to specify sizing.
class _Delegate( QtGui.QStyledItemDelegate ) :

	def __init__( self ) :
			
		QtGui.QStyledItemDelegate.__init__( self )
	
	def columnWidth( self ) :
	
		return 70
		
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
	
_Delegate.registerType( IECore.StringVectorData.staticTypeId(), _Delegate )
_Delegate.registerType( IECore.FloatVectorData.staticTypeId(), _Delegate )
_Delegate.registerType( IECore.IntVectorData.staticTypeId(), _Delegate )
_Delegate.registerType( IECore.FloatVectorData.staticTypeId(), _Delegate )
_Delegate.registerType( IECore.Color3fVectorData.staticTypeId(), _Delegate )
_Delegate.registerType( IECore.Color4fVectorData.staticTypeId(), _Delegate )
_Delegate.registerType( IECore.V3fVectorData.staticTypeId(), _Delegate )

class _BoolDelegate( _Delegate ) :

	def __init__( self ) :
	
		_Delegate.__init__( self )
		
	def columnWidth( self ) :
	
		return 30
		
	def canStretch( self ) :
	
		return False

	def paint( self, painter, option, index ) :
			
		styleOption = QtGui.QStyleOptionButton()
		
		styleOption.state |= QtGui.QStyle.State_Enabled
		if index.model().data( index, QtCore.Qt.DisplayRole ).toBool() :
			styleOption.state |= QtGui.QStyle.State_On
		else :
			styleOption.state |= QtGui.QStyle.State_Off
		
		styleOption.rect = option.rect
		
		widget = option.widget	
		widget.style().drawControl( QtGui.QStyle.CE_CheckBox, styleOption, painter, widget )

	def editorEvent( self, event, model, option, index ) :
		
		if event.type()==QtCore.QEvent.MouseButtonDblClick :
			# eat event so an editor doesn't get created
			return True
		if event.type()==QtCore.QEvent.MouseButtonRelease :
			# toggle the data value
			checked = index.model().data( index, QtCore.Qt.DisplayRole ).toBool()
			model.setData( index, not checked, QtCore.Qt.EditRole )
			return True

		return False

_Delegate.registerType( IECore.BoolVectorData.staticTypeId(), _BoolDelegate )

class _StringDelegate( _Delegate ) :

	def __init__( self ) :
	
		_Delegate.__init__( self )
				
	def canStretch( self ) :
	
		return True

_Delegate.registerType( IECore.StringVectorData.staticTypeId(), _StringDelegate )
