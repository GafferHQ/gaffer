##########################################################################
#
#  Copyright (c) 2025, Cinesite VFX Ltd. All rights reserved.
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

import Gaffer
import GafferTest

class ObjectMatrixTest( GafferTest.TestCase ) :

	def test( self ) :

		m = Gaffer.ObjectMatrix( 3, 4 )
		self.assertEqual( m.width(), 3 )
		self.assertEqual( m.height(), 4 )

		self.assertIsNone( m.value( 0, 0 ) )
		self.assertIsNone( m.value( 0, 1 ) )
		m[0, 1] = IECore.IntData( 123 )

		self.assertIsNone( m.value( 0, 0 ) )
		self.assertIsNone( m[0, 0] )
		self.assertEqual( m.value( 0, 1 ), IECore.IntData( 123 ) )
		self.assertEqual( m[0, 1], IECore.IntData( 123 ) )

		m[2, 3] = IECore.StringData( "test" )
		self.assertEqual( m[2, 3], IECore.StringData( "test" ) )
		self.assertEqual( m[-1, -1], IECore.StringData( "test" ) )

		with self.assertRaises( IndexError ) :
			_ = m[7, 0]
			_ = m[0, 7]
			_ = m[7, 7]
			_ = m[-7, -7]

	def testConstructFromSequence( self ) :

		m = Gaffer.ObjectMatrix( 1, 1, [ IECore.IntData( 123 ) ] )
		self.assertEqual( m.width(), 1 )
		self.assertEqual( m.height(), 1 )
		self.assertEqual( m[0, 0], IECore.IntData( 123 ) )

		m = Gaffer.ObjectMatrix( 4, 3, [ IECore.IntData( x ) for x in range( 12 ) ] )
		self.assertEqual( m.width(), 4 )
		self.assertEqual( m.height(), 3 )

		for x in range( 4 ) :
			for y in range( 3 ) :
				self.assertEqual( m[x, y], IECore.IntData( y * 4 + x ) )

		self.assertRaises( ValueError, Gaffer.ObjectMatrix, 1, 1, [] )
		self.assertRaises( ValueError, Gaffer.ObjectMatrix, 1, 1, [ IECore.IntData( 123 ), IECore.FloatData( 456.0 ) ] )

	def testCompare( self ) :

		m1 = Gaffer.ObjectMatrix( 4, 4, [ IECore.IntData( x ) for x in range( 16 ) ] )
		m2 = Gaffer.ObjectMatrix( 4, 4 )
		for x in range( 4 ) :
			for y in range( 4 ) :
				m2[x, y] = IECore.IntData( y * 4 + x )

		self.assertTrue( m1 == m2 )
		self.assertFalse( m1 != m2 )

		m2[0, 0] = IECore.FloatData( 1.0 )
		self.assertTrue( m1 != m2 )

		m3 = m2.copy()

		self.assertTrue( m2 == m3 )
		self.assertEqual( m3[0, 0], IECore.FloatData( 1.0 ) )

		m3[0, 0] = IECore.CompoundData()
		self.assertTrue( m2 != m3 )
		self.assertEqual( m2[0, 0], IECore.FloatData( 1.0 ) )
		self.assertEqual( m3[0, 0], IECore.CompoundData() )

	def testHash( self ) :

		m = Gaffer.ObjectMatrix( 1, 1 )
		h = m.hash()

		m[0, 0] = IECore.IntData( 10 )
		self.assertNotEqual( m.hash(), h )

		m1 = Gaffer.ObjectMatrix( 2, 1, [ IECore.StringData( "A" ), IECore.FloatData( 2.0 ) ] )
		m2 = Gaffer.ObjectMatrix( 1, 2, [ IECore.StringData( "A" ), IECore.FloatData( 2.0 ) ] )
		self.assertNotEqual( m1.hash(), m2.hash() )

	def testRepr( self ) :

		m = Gaffer.ObjectMatrix( 2, 2, [ IECore.IntData( 42 ), IECore.StringData( "123" ), IECore.FloatData( 0.1 ), IECore.CompoundData() ] )
		self.assertEqual( repr( m ), "Gaffer.ObjectMatrix( 2, 2, [ IECore.IntData( 42 ), IECore.StringData( '123' ), IECore.FloatData( 0.1 ), IECore.CompoundData(), ] )" )

if __name__ == "__main__":
	unittest.main()
