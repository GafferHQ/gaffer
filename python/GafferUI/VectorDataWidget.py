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

## The VectorDataWidget provides a list view for the contents of
# the IECore VectorData classes.
class VectorDataWidget( GafferUI.Widget ) :

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
			self.__model = _Model( data, self._qtWidget(), self.getEditable() )
			self.__model.dataChanged.connect( Gaffer.WeakMethod( self.__dataChanged ) )
			self.__model.rowsInserted.connect( Gaffer.WeakMethod( self.__dataChanged ) )
			self.__model.rowsRemoved.connect( Gaffer.WeakMethod( self.__dataChanged ) )
		else :
			self.__model = None
		
		self._qtWidget().setModel( self.__model )
		
		isStringData = isinstance( data, IECore.StringVectorData )
		self._qtWidget().horizontalHeader().setStretchLastSection( isStringData )
		self._qtWidget().setSizePolicy( QtGui.QSizePolicy( QtGui.QSizePolicy.Expanding if isStringData else QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed ) )
		for i in range( 0, self._qtWidget().horizontalHeader().count() ) :
			self._qtWidget().horizontalHeader().resizeSection( i, 70 )
			
		self._qtWidget().updateGeometry()
		
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
			del data[indices[i]]
		
		# tell the world
		self.setData( data )
		self.__dataChanged()
	
## Private implementation - a QTableView which is much more forceful about
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
		
## Internal implementation detail - a qt model which wraps
# around the VectorData.		
class _Model( QtCore.QAbstractTableModel ) :

	__addValueText = "Add..."

	def __init__( self, data, parent=None, editable=True ) :
	
		QtCore.QAbstractTableModel.__init__( self, parent )
				
		self.__data = data
		self.__editable = editable
		
		self.__toVariant = self.__toVariantSimple
		self.__fromVariant = self.__fromVariantSimple
		self.__numColumns = 1
		self.__headerLabels = [ "X", "Y", "Z" ]
		if isinstance( data, IECore.V3fVectorData ) :
			self.__fromVariant = self.__fromVariantCompound
			self.__toVariant = self.__toVariantCompound
			self.__numColumns = 3
		elif isinstance( data, IECore.IntVectorData ) :
			self.__fromVariant = self.__fromVariantInt
		elif isinstance( data, ( IECore.FloatVectorData, IECore.DoubleVectorData ) ) :
			self.__fromVariant = self.__fromVariantFloat
		elif isinstance( data, ( IECore.Color3fVectorData ) ) :
			self.__fromVariant = self.__fromVariantCompound
			self.__toVariant = self.__toVariantCompound
			self.__numColumns = 3
			self.__headerLabels = [ "R", "G", "B" ]
		elif isinstance( data, ( IECore.Color4fVectorData ) ) :
			self.__fromVariant = self.__fromVariantCompound
			self.__toVariant = self.__toVariantCompound
			self.__numColumns = 4
			self.__headerLabels = [ "R", "G", "B", "A" ]	
								
	## Methods specific to this model first
	
	def vectorData( self ) :
	
		return self.__data
		
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
		
		if self.__editable :
			return len( self.__data ) + 1
		else :
			return len( self.__data )
		
	def columnCount( self, parent ) :
	
		if parent.isValid() :
			return 0
			
		return self.__numColumns
		
	def headerData( self, section, orientation, role ) :
		
		if QtCore is None :
			# it seems that this is sometimes getting called during python shutdown.
			# during shutdown python makes all module globals reference None, so
			# QtCore becomes None, and we can't do anything. just return None and
			# hope for the best.
			return None
					
		if role == QtCore.Qt.DisplayRole :
			if orientation == QtCore.Qt.Horizontal :
				return GafferUI._Variant.toVariant( self.__headerLabels[section] )
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
			if index.row() < len( self.__data ) :
				return self.__toVariant( self.__data, index )
			else :
				return GafferUI._Variant.toVariant( self.__addValueText )
			
		return GafferUI._Variant.toVariant( None )

	def setData( self, index, value, role ) :
	
		if role == QtCore.Qt.EditRole :
			if index.row() < len( self.__data ) :
				self.__data[index.row()] = self.__fromVariant( value, self.__data, index )
				self.dataChanged.emit( index, index )
			else :
				if value!=self.__addValueText :
					self.beginInsertRows( index.parent(), len( self.__data ) + 1, len( self.__data ) + 1 )
					self.__data.append( self.__fromVariant( value, self.__data, index ) )
					self.endInsertRows()

		return True

	@staticmethod
	def __toVariantSimple( data, index ) :
	
		return GafferUI._Variant.toVariant( data[index.row()] )

	@staticmethod
	def __fromVariantSimple( variant, data, index ) :
	
		return GafferUI._Variant.fromVariant( variant )
		
	@staticmethod
	def __fromVariantInt( variant, data, index ) :
	
		value = GafferUI._Variant.fromVariant( variant )
		if isinstance( value, basestring ) :
			# we get strings back from the Add... line
			try :
				value = int( float( value ) )
			except ValueError :
				value = 0
						
		return value
		
	@staticmethod
	def __fromVariantFloat( variant, data, index ) :
	
		value = GafferUI._Variant.fromVariant( variant )
		if isinstance( value, basestring ) :
			# we get strings back from the Add... line
			try :
				value = float( value )
			except ValueError :
				value = 0
						
		return value	

	@staticmethod
	def __toVariantCompound( data, index ) :
		
		return GafferUI._Variant.toVariant( data[index.row()][index.column()] )

	@staticmethod
	def __fromVariantCompound( variant, data, index ) :
	
		if index.row() < len( data ) :
			result = data[index.row()]
		else :
			result = IECore.DataTraits.valueTypeFromSequenceType( type( data ) )( 0 )
		
		value = GafferUI._Variant.fromVariant( variant )
		if isinstance( value, basestring ) :
			# we get strings back from the Add... line
			try :
				value = float( value )
			except ValueError :
				value = 0
				
		result[index.column()] = value
		return result
