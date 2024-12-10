##########################################################################
#
#  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
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

import imath

import IECore
import GafferTest
import GafferML

class TensorTest( GafferTest.TestCase ) :

	def testAsData( self ) :

		for data in [
			IECore.BoolVectorData( [ True, False, True ] ),
			IECore.FloatVectorData( [ 1, 2, 3 ] ),
			IECore.DoubleVectorData( [ 1, 2, 3 ] ),
			IECore.IntVectorData( [ 1, 2, 3 ] ),
			IECore.UInt64VectorData( [ 1, 2, 3 ] ),
		] :

			tensor = GafferML.Tensor( data, [ 1, 3 ] )
			self.assertEqual( tensor.asData(), data )

		self.assertIsNone( GafferML.Tensor().asData() )

	def testInvalidShapeThrows( self ) :

		with self.assertRaisesRegex( RuntimeError, "not enough space: expected 16, got 12" ) :
			GafferML.Tensor( IECore.FloatVectorData( [ 1, 2, 3 ] ), [ 4 ] )

	def testExplicitShape( self ) :

		tensor = GafferML.Tensor( IECore.IntVectorData( [ 1, 2, 3, 4, 5, 6 ] ), [ 1, 1, 2, 3 ] )
		self.assertEqual( tensor.shape(), [ 1, 1, 2, 3 ] )

		tensor = GafferML.Tensor()
		with self.assertRaisesRegex( RuntimeError, "Null tensor" ) :
			tensor.shape()

	def testAutomaticShape( self ) :

		tensor = GafferML.Tensor( IECore.IntVectorData( [ 1, 2, 3, 4, 5 ] ) )
		self.assertEqual( tensor.shape(), [ 5 ] )

		tensor = GafferML.Tensor( IECore.V2iVectorData( [ imath.V2i( 1, 2 ), imath.V2i( 3, 4 ), imath.V2i( 5, 6 ) ] ) )
		self.assertEqual( tensor.shape(), [ 3, 2 ] )

		tensor = GafferML.Tensor( IECore.V3fVectorData( [ imath.V3f( 1 ), imath.V3f( 2 ) ] ) )
		self.assertEqual( tensor.shape(), [ 2, 3 ] )

		tensor = GafferML.Tensor( IECore.V3fData( imath.V3f( 1 ) ) )
		self.assertEqual( tensor.shape(), [ 3 ] )

		tensor = GafferML.Tensor( IECore.Box3fData( imath.Box3f( imath.V3f( 1 ), imath.V3f( 2 ) ) ) )
		self.assertEqual( tensor.shape(), [ 2, 3 ] )

		tensor = GafferML.Tensor( IECore.Color4fData( imath.Color4f( 0 ) ) )
		self.assertEqual( tensor.shape(), [ 4 ] )

	def testMemoryUsage( self ) :

		tensor = GafferML.Tensor( IECore.IntVectorData( 100 ), [ 100 ] )
		self.assertEqual( tensor.memoryUsage(), 440 )

	def testHash( self ) :

		tensors = [
			GafferML.Tensor( IECore.IntVectorData( [ 1, 2, 3 ] ), [ 1, 3 ] ),
			GafferML.Tensor( IECore.IntVectorData( [ 1, 2, 3 ] ), [ 3, 1 ] ),
			GafferML.Tensor( IECore.IntVectorData( [ 1, 2, 3, 4 ] ), [ 4 ] )
		]

		self.assertEqual( len( { t.hash() for t in tensors } ), len( tensors ) )

	def testCopy( self ) :

		data = IECore.IntVectorData( [ 1, 2, 3 ] )
		tensor1 = GafferML.Tensor( data, [ 3 ] )
		tensor2 = tensor1.copy()
		self.assertEqual( tensor2, tensor1 )
		self.assertEqual( tensor2.asData(), data )
		self.assertEqual( tensor2.shape(), tensor1.shape() )

	def testIsEqual( self ) :

		data = IECore.IntVectorData( [ 1, 2, 3 ] )
		tensor1 = GafferML.Tensor( data, [ 3 ] )

		tensor2 = GafferML.Tensor( data, [ 3 ] )
		self.assertEqual( tensor1, tensor2 )

		tensor2 = GafferML.Tensor( data.copy(), [ 3 ] )
		self.assertEqual( tensor1, tensor2 )

		tensor2 = GafferML.Tensor( IECore.IntVectorData( [ 1, 2, 3 ] ), [ 3 ] )
		self.assertEqual( tensor1, tensor2 )

		tensor2 = GafferML.Tensor( data, [ 1, 3 ] )
		self.assertNotEqual( tensor1, tensor2 ) # Different shape

		tensor2 = GafferML.Tensor( IECore.IntVectorData( [ 3, 2, 1 ] ), [ 3 ] )
		self.assertNotEqual( tensor1, tensor2 ) # Different data

	def testDefaultRepr( self ) :

		self.assertEqual( repr( GafferML.Tensor() ), "GafferML.Tensor()" )

	def testConstructFromUnsupportedDataType( self ) :

		with self.assertRaisesRegex( RuntimeError, "Unsupported data type `PathMatcherData`" ) :
			GafferML.Tensor( IECore.PathMatcherData() )

	def testGetItem1D( self ) :

		tensor = GafferML.Tensor( IECore.IntVectorData( range( 0, 100 ) ) )
		for i in range( 0, 100 ) :
			self.assertEqual( tensor[i], i )

	def testGetItem2D( self ) :

		data = IECore.V3fVectorData( [ imath.V3f( 1, 2, 3 ), imath.V3f( 4, 5, 6 ) ] )
		tensor = GafferML.Tensor( data )

		for i in range( 0, 2 ) :
			for j in range( 0, 3 ) :
				v = tensor[i, j]
				self.assertIsInstance( v, float )
				self.assertEqual( v, data[i][j] )

	def testGetItemOutOfRange( self ) :

		tensor = GafferML.Tensor( IECore.IntVectorData( [ 1, 2 ] ) )
		with self.assertRaisesRegex( RuntimeError, "invalid location range" ) :
			tensor[-1]
		with self.assertRaisesRegex( RuntimeError, "invalid location range" ) :
			tensor[2]

	def testGetItemWrongDimensions( self ) :

		tensor = GafferML.Tensor( IECore.IntVectorData( [ 1, 2 ] ) )
		with self.assertRaisesRegex( RuntimeError, "location dimensions do not match shape size" ) :
			tensor[0, 1]

if __name__ == "__main__" :
	unittest.main()
