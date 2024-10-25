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

import IECore
import GafferTest
import GafferML

class TensorTest( GafferTest.TestCase ) :

	def testAsData( self ) :

		for data in [
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

	def testShape( self ) :

		tensor = GafferML.Tensor( IECore.IntVectorData( [ 1, 2, 3, 4, 5, 6 ] ), [ 1, 1, 2, 3 ] )
		self.assertEqual( tensor.shape(), [ 1, 1, 2, 3 ] )

		tensor = GafferML.Tensor()
		with self.assertRaisesRegex( RuntimeError, "Null tensor" ) :
			tensor.shape()

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

if __name__ == "__main__":
	unittest.main()
