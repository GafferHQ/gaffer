##########################################################################
#  
#  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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

import unittest

import IECore

import GafferTest
import GafferUI
import GafferUITest

class VectorDataWidgetTest( GafferUITest.TestCase ) :

	def testIndexing( self ) :
	
		data = [
			IECore.FloatVectorData( range( 0, 3 ) ),
			IECore.Color3fVectorData( [ IECore.Color3f( x ) for x in range( 0, 3 ) ] ),
			IECore.StringVectorData( [ str( x ) for x in range( 0, 3 ) ] ),
			IECore.IntVectorData( range( 0, 3 ) ),
			IECore.V3fVectorData( [ IECore.V3f( x ) for x in range( 0, 3 ) ] ),
		]
		
		w = GafferUI.VectorDataWidget( data )
		
		self.assertEqual( w.columnToDataIndex( 0 ), ( 0, -1 ) )
		self.assertEqual( w.columnToDataIndex( 1 ), ( 1, 0 ) )
		self.assertEqual( w.columnToDataIndex( 2 ), ( 1, 1 ) )
		self.assertEqual( w.columnToDataIndex( 3 ), ( 1, 2 ) )
		self.assertEqual( w.columnToDataIndex( 4 ), ( 2, -1 ) )
		self.assertEqual( w.columnToDataIndex( 5 ), ( 3, -1 ) )
		self.assertEqual( w.columnToDataIndex( 6 ), ( 4, 0 ) )
		self.assertEqual( w.columnToDataIndex( 7 ), ( 4, 1 ) )
		self.assertEqual( w.columnToDataIndex( 8 ), ( 4, 2 ) )
		
		self.assertRaises( IndexError, w.columnToDataIndex, 9 )
		
		self.assertEqual( w.dataToColumnIndex( 0, -1 ), 0 )
		self.assertEqual( w.dataToColumnIndex( 1, 0 ), 1 )
		self.assertEqual( w.dataToColumnIndex( 1, 1 ), 2 )
		self.assertEqual( w.dataToColumnIndex( 1, 2 ), 3 )
		self.assertEqual( w.dataToColumnIndex( 2, -1 ), 4 )
		self.assertEqual( w.dataToColumnIndex( 3, -1 ), 5 )
		self.assertEqual( w.dataToColumnIndex( 4, 0 ), 6 )
		self.assertEqual( w.dataToColumnIndex( 4, 1 ), 7 )
		self.assertEqual( w.dataToColumnIndex( 4, 2 ), 8 )

		self.assertRaises( IndexError, w.dataToColumnIndex, 5, 0 )
	
	def testColumnEditability( self ) :
	
		data = [
			IECore.FloatVectorData( range( 0, 3 ) ),
			IECore.Color3fVectorData( [ IECore.Color3f( x ) for x in range( 0, 3 ) ] ),
			IECore.StringVectorData( [ str( x ) for x in range( 0, 3 ) ] ),
		]
		
		w = GafferUI.VectorDataWidget( data )
		
		for i in range( 0, 5 ) :
			self.assertEqual( w.getColumnEditable( i ), True )
			
		self.assertRaises( IndexError, w.getColumnEditable, 5 )
		self.assertRaises( IndexError, w.getColumnEditable, -1 )
		
		w.setColumnEditable( 1, False )
		self.assertEqual( w.getColumnEditable( 1 ), False )
		
		data[0][0] += 1.0
		w.setData( data )
		
		for i in range( 0, 5 ) :
			self.assertEqual( w.getColumnEditable( i ), i != 1 )
		
		cs = GafferTest.CapturingSlot( w.dataChangedSignal() )
		self.assertEqual( len( cs ), 0 )
		
		w.setColumnEditable( 0, False )
		w.setColumnEditable( 1, True )
		
		# changing editability shouldn't emit dataChangedSignal.
		self.assertEqual( len( cs ), 0 )
		
if __name__ == "__main__":
	unittest.main()
	
