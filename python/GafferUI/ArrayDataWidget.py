import Gaffer
import GafferUI
from GafferUI.VectorDataWidget import _Model as _VectorDataWidgetModel
from GafferUI.VectorDataWidget import _Delegate as _VectorDataWidgetDelegate

from Qt import QtCore
from Qt import QtWidgets
from Qt import QtCompat


class ArrayDataWidget( GafferUI.VectorDataWidget ) :
	def __init__( self, data=None, **kwargs ) :
		self.__rowEditability = None
		super( ArrayDataWidget, self ).__init__( data, **kwargs )
		

	def setData( self, data ) :
		
		if data is not None :
			if not isinstance( data, list ) :
				data = [ data ]
			self._VectorDataWidget__model = _Model( data, self._VectorDataWidget__tableView, self.getEditable(), self._VectorDataWidget__header, self._VectorDataWidget__toolTips, self._VectorDataWidget__columnEditability, self.__rowEditability )
			self._VectorDataWidget__model.dataChanged.connect( Gaffer.WeakMethod( self._VectorDataWidget__modelDataChanged ) )
			self._VectorDataWidget__model.rowsInserted.connect( Gaffer.WeakMethod( self._VectorDataWidget__emitDataChangedSignal ) )
			self._VectorDataWidget__model.rowsRemoved.connect( Gaffer.WeakMethod( self._VectorDataWidget__emitDataChangedSignal ) )
		else :
			self._VectorDataWidget__model = None

		self._VectorDataWidget__tableView.setModel( self._VectorDataWidget__model )

		if self._VectorDataWidget__model :

			columnIndex = 0
			haveResizeableContents = False
			for accessor in self._VectorDataWidget__model.vectorDataAccessors() :
				for i in range( 0, accessor.numColumns() ) :
					delegate = _VectorDataWidgetDelegate.create( accessor.data() )
					delegate.setParent( self._VectorDataWidget__model )
					self._VectorDataWidget__tableView.setItemDelegateForColumn( columnIndex, delegate )
					canStretch = delegate.canStretch()
					haveResizeableContents = haveResizeableContents or canStretch
					columnIndex += 1

			QtCompat.setSectionResizeMode(
				self._VectorDataWidget__tableView.horizontalHeader(),
				QtWidgets.QHeaderView.ResizeToContents if haveResizeableContents else QtWidgets.QHeaderView.Fixed
			)

			self._VectorDataWidget__tableView.horizontalHeader().setStretchLastSection( canStretch )
			horizontalSizePolicy = QtWidgets.QSizePolicy.Expanding
			if self._VectorDataWidget__tableView.horizontalScrollMode() == QtCore.Qt.ScrollBarAlwaysOff and not canStretch :
				horizontalSizePolicy = QtWidgets.QSizePolicy.Fixed

			self._VectorDataWidget__tableView.setSizePolicy(
				QtWidgets.QSizePolicy(
					horizontalSizePolicy,
					QtWidgets.QSizePolicy.Maximum
				)
			)

			selectionModel = self._VectorDataWidget__tableView.selectionModel()
			selectionModel.selectionChanged.connect( Gaffer.WeakMethod( self._VectorDataWidget__selectionChanged ) )

		self._VectorDataWidget__updateRemoveButtonEnabled()

		self._VectorDataWidget__tableView.verticalHeader().setUpdatesEnabled( True )
		self._VectorDataWidget__tableView.updateGeometry()

	def setRowEditability( self, rowEditability ) :

		self.__rowEditability = rowEditability

	def getRowEditability( self ) :

		return self.__rowEditability


class _Model( _VectorDataWidgetModel ) :

	def __init__( self, data, parent=None, editable=True, header=None, toolTips=None, columnEditability=None, rowEditability=None  ) :
		_VectorDataWidgetModel.__init__( self, data, parent=parent, editable=editable, header=header, toolTips=toolTips, columnEditability=columnEditability )

		self.__rowEditability = rowEditability

	def flags( self, index ) :
		result = (
			QtCore.Qt.ItemIsSelectable |
			QtCore.Qt.ItemIsDragEnabled
		)

		if self.__editable :
			rowEditable = (
				self.__rowEditability is None or
				index.row() >= len( self.__rowEditability ) or
				self.__rowEditability[index.row()]
			)
			if rowEditable :
				result |= QtCore.Qt.ItemIsEnabled
				if self.__columnEditability is None or self.__columnEditability[index.column()] :
					result |= QtCore.Qt.ItemIsEditable
		else :
			result |= QtCore.Qt.ItemIsEnabled

		return result