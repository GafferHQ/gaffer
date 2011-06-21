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
						
		self._qtWidget().horizontalHeader().setStretchLastSection( True )
		self._qtWidget().horizontalHeader().setVisible( header )
		
		self._qtWidget().verticalHeader().setVisible( showIndices )
		self._qtWidget().verticalHeader().setResizeMode( QtGui.QHeaderView.Fixed )
		self._qtWidget().verticalHeader().setObjectName( "vectorDataWidgetVerticalHeader" )

		self._qtWidget().setHorizontalScrollBarPolicy( QtCore.Qt.ScrollBarAlwaysOff )
		self._qtWidget().setVerticalScrollBarPolicy( QtCore.Qt.ScrollBarAlwaysOff )
		self._qtWidget().setSizePolicy( QtGui.QSizePolicy( QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed ) )

		self.__dataChangedSignal = GafferUI.WidgetSignal()
	
		self.setData( data )
		self.setEditable( editable )
	
	def setData( self, data ) :
		
		if data is not None :
			self.__model = _Model( data, self._qtWidget(), self.getEditable() )
			self.__model.dataChanged.connect( Gaffer.WeakMethod( self.__dataChanged ) )
			self.__model.rowsInserted.connect( Gaffer.WeakMethod( self.__dataChanged ) )
			self.__model.rowsRemoved.connect( Gaffer.WeakMethod( self.__dataChanged ) )
		else :
			self.__model = None
		
		self._qtWidget().setModel( self.__model )
		
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
		
	def __dataChanged( self, *unusedArgs ) :
	
		self.dataChangedSignal()( self )
		
## Private implementation - a QTableView which is much more forceful about
# requesting enough height if the vertical scrollbar is always off.
class _TableView( QtGui.QTableView ) :

	def __init__( self ) :
	
		QtGui.QTableView.__init__( self )
	
	def setModel( self, model ) :
	
		prevModel = self.model()
		if prevModel :
			prevModel.rowsInserted.disconnect( self.__rowsChanged )
			prevModel.rowsRemoved.disconnect( self.__rowsChanged )
	
		QtGui.QTableView.setModel( self, model )
	
		if model :
			model.rowsInserted.connect( self.__rowsChanged )
			model.rowsRemoved.connect( self.__rowsChanged )
	
		self.updateGeometry()

	def minimumSizeHint( self ) :
	
		return QtCore.QSize()
		
	def sizeHint( self ) :
		
		result = QtGui.QTableView.sizeHint( self )
				
		if self.verticalScrollBarPolicy()==QtCore.Qt.ScrollBarAlwaysOff :
			margins = self.contentsMargins()		
			result.setHeight( self.verticalHeader().length()  + margins.top() + margins.bottom() )
				
		return result

	def __rowsChanged( self, *unusedArgs ) :
		
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
		self.__numColumns = 1
		if isinstance( data, IECore.StringVectorData ) :
			self.__fromVariant = self.__fromVariantStr
		elif isinstance( data, IECore.IntVectorData ) :
			self.__fromVariant = self.__fromVariantInt
		elif isinstance( data, IECore.FloatVectorData ) :
			self.__fromVariant = self.__fromVariantFloat
		elif isinstance( data, IECore.V3fVectorData ) :
			self.__fromVariant = self.__fromVariantCompoundFloat
			self.__toVariant = self.__toVariantCompound
			self.__numColumns = 3
						
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
					
		if role == QtCore.Qt.DisplayRole :
			if orientation == QtCore.Qt.Horizontal :
				## \todo
				return QtCore.QVariant( "X" )
			else :
				return QtCore.QVariant( section )
		
		return QtCore.QVariant()	

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
				return QtCore.QVariant( self.__addValueText )
			
		return QtCore.QVariant()

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
	
		return QtCore.QVariant( data[index.row()] )

	@staticmethod
	def __fromVariantStr( variant, data, index ) :
	
		return str( variant.toString() )
		
	@staticmethod
	def __fromVariantInt( variant, data, index ) :
	
		return variant.toInt()[0]
		
	@staticmethod
	def __fromVariantFloat( variant, data, index ) :
	
		return variant.toFloat()[0]

	@staticmethod
	def __toVariantCompound( data, index ) :
		
		return QtCore.QVariant( data[index.row()][index.column()] )

	@staticmethod
	def __fromVariantCompoundFloat( variant, data, index ) :
	
		if index.row() < len( data ) :
			result = data[index.row()]
		else :
			result = IECore.DataTraits.valueTypeFromSequenceType( type( data ) )( 0 )
		
		result[index.column()] = variant.toFloat()[0]
		return result
