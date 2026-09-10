import unittest
import imath

import IECore

import GafferTest
import GafferUI
import GafferUITest
from Qt import QtCore

class ArrayDataWidgetTest( GafferUITest.TestCase ) :

	def testIndexing( self ) :

		data = [
			IECore.FloatVectorData( range( 0, 3 ) ),
			IECore.Color3fVectorData( [ imath.Color3f( x ) for x in range( 0, 3 ) ] ),
			IECore.StringVectorData( [ str( x ) for x in range( 0, 3 ) ] ),
			IECore.IntVectorData( range( 0, 3 ) ),
			IECore.V3fVectorData( [ imath.V3f( x ) for x in range( 0, 3 ) ] ),
		]

		w = GafferUI.ArrayDataWidget( data )

		self.assertEqual( w.columnToDataIndex( 0 ), ( 0, -1 ) )
		self.assertEqual( w.columnToDataIndex( 1 ), ( 1, 0 ) )
		self.assertEqual( w.columnToDataIndex( 2 ), ( 1, 1 ) )
		self.assertEqual( w.columnToDataIndex( 3 ), ( 1, 2 ) )
		self.assertEqual( w.columnToDataIndex( 4 ), ( 1, 3 ) )
		self.assertEqual( w.columnToDataIndex( 5 ), ( 2, -1 ) )
		self.assertEqual( w.columnToDataIndex( 6 ), ( 3, -1 ) )
		self.assertEqual( w.columnToDataIndex( 7 ), ( 4, 0 ) )
		self.assertEqual( w.columnToDataIndex( 8 ), ( 4, 1 ) )
		self.assertEqual( w.columnToDataIndex( 9 ), ( 4, 2 ) )

		self.assertRaises( IndexError, w.columnToDataIndex, 10 )

		self.assertEqual( w.dataToColumnIndex( 0, -1 ), 0 )
		self.assertEqual( w.dataToColumnIndex( 1, 0 ), 1 )
		self.assertEqual( w.dataToColumnIndex( 1, 1 ), 2 )
		self.assertEqual( w.dataToColumnIndex( 1, 2 ), 3 )
		self.assertEqual( w.dataToColumnIndex( 1, 3 ), 4 )
		self.assertEqual( w.dataToColumnIndex( 2, -1 ), 5 )
		self.assertEqual( w.dataToColumnIndex( 3, -1 ), 6 )
		self.assertEqual( w.dataToColumnIndex( 4, 0 ), 7 )
		self.assertEqual( w.dataToColumnIndex( 4, 1 ), 8 )
		self.assertEqual( w.dataToColumnIndex( 4, 2 ), 9 )

		self.assertRaises( IndexError, w.dataToColumnIndex, 6, 0 )

	def testColumnEditability( self ) :

		data = [
			IECore.FloatVectorData( range( 0, 3 ) ),
			IECore.Color3fVectorData( [ imath.Color3f( x ) for x in range( 0, 3 ) ] ),
			IECore.StringVectorData( [ str( x ) for x in range( 0, 3 ) ] ),
		]

		w = GafferUI.ArrayDataWidget( data )

		for i in range( 0, 6 ) :
			self.assertEqual( w.getColumnEditable( i ), True )

		self.assertRaises( IndexError, w.getColumnEditable, 7 )
		self.assertRaises( IndexError, w.getColumnEditable, -1 )

		w.setColumnEditable( 1, False )
		self.assertEqual( w.getColumnEditable( 1 ), False )

		data[0][0] += 1.0
		w.setData( data )

		for i in range( 0, 6 ) :
			self.assertEqual( w.getColumnEditable( i ), i != 1 )

		cs = GafferTest.CapturingSlot( w.dataChangedSignal() )
		self.assertEqual( len( cs ), 0 )

		w.setColumnEditable( 0, False )
		w.setColumnEditable( 1, True )

		# changing editability shouldn't emit dataChangedSignal.
		self.assertEqual( len( cs ), 0 )

	def testRowEditability( self ) :

		data = [ IECore.IntVectorData( range( 0, 3 ) ) ]

		w = GafferUI.ArrayDataWidget()
		w.setRowEditability( [ False, True, False ] )
		w.setData( data )

		model = w._VectorDataWidget__model

		index0 = model.index( 0, 0 )
		index1 = model.index( 1, 0 )
		index2 = model.index( 2, 0 )

		self.assertFalse( bool( model.flags( index0 ) & QtCore.Qt.ItemIsEditable ) )
		self.assertTrue( bool( model.flags( index1 ) & QtCore.Qt.ItemIsEditable ) )
		self.assertFalse( bool( model.flags( index2 ) & QtCore.Qt.ItemIsEditable ) )

if __name__ == "__main__":
	unittest.main()
