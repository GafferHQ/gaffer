import IECore

import Gaffer
import GafferUI


class ArrayPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		sizeEditable = plug.minSize() != plug.maxSize()

		self.__dataWidget = GafferUI.ArrayDataWidget(
			header = True,
			sizeEditable = sizeEditable,
		)

		GafferUI.PlugValueWidget.__init__( self, self.__dataWidget, plug, **kw )

		self.__dataWidget.dataChangedSignal().connect( Gaffer.WeakMethod( self.__dataChanged ) )

	def setHighlighted( self, highlighted ) :

		GafferUI.PlugValueWidget.setHighlighted( self, highlighted )
		self.__dataWidget.setHighlighted( highlighted )
	

	@staticmethod
	def _valuesForUpdate( plugs, auxiliaryPlugs ) :

		assert( len( plugs ) == 1 )
		plug = next( iter( plugs ) )
		children = list( plug )
		return {
			"values" : [ c.getValue() for c in children ],
			"rowEditable" : [ c.getInput() is None for c in children ],
		}

	def _updateFromValues( self, values, exception ) :

		if not values :
			return

		vectorDataType = None
		
		plug = self.getPlug()
		if plug is not None :
			vectorDataType = self.__vectorDataType( plug )
		
		if vectorDataType is not None :
			self.__dataWidget.setRowEditability( values["rowEditable"] )
			self.__dataWidget.setData( vectorDataType( values["values"] ) )
		self.__dataWidget.setErrored( exception is not None )

	def _updateFromEditable( self ) :

		self.__dataWidget.setEditable( self._editable() )

	def __dataChanged( self, widget ) :

		plug = self.getPlug()
		if plug is None :
			return

		with self._blockedUpdateFromValues() :
			with Gaffer.UndoScope( plug.ancestor( Gaffer.ScriptNode ) ) :
				data = self.__dataWidget.getData()[0]
				targetSize = max( plug.minSize(), min( plug.maxSize(), len( data ) ) )
				plug.resize( targetSize )
				for i, child in enumerate( plug ) :
					if i < len( data ) and child.getInput() is None :
						child.setValue( data[i] )

		self._requestUpdateFromValues()

	@staticmethod
	def __vectorDataType( plug ) :

		elementPrototype = plug.elementPrototype()
		if elementPrototype is None :
			return None
		return ArrayPlugValueWidget.__plugTypeToVectorDataType.get( type( elementPrototype ) )

	__plugTypeToVectorDataType = {
		Gaffer.BoolPlug : IECore.BoolVectorData,
		Gaffer.IntPlug : IECore.IntVectorData,
		Gaffer.FloatPlug : IECore.FloatVectorData,
		Gaffer.StringPlug : IECore.StringVectorData,
		Gaffer.V2iPlug : IECore.V2iVectorData,
		Gaffer.V2fPlug : IECore.V2fVectorData,
		Gaffer.V3iPlug : IECore.V3iVectorData,
		Gaffer.V3fPlug : IECore.V3fVectorData,
		Gaffer.Color3fPlug : IECore.Color3fVectorData,
		Gaffer.Color4fPlug : IECore.Color4fVectorData,
	}

GafferUI.PlugValueWidget.registerType( Gaffer.ArrayPlug, ArrayPlugValueWidget )
