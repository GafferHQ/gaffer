##########################################################################
#
#  Copyright (c) 2022, Cinesite VFX Ltd. All rights reserved.
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
import GafferScene

class PlaceholderTest( GafferTest.TestCase ) :

	def testFactory( self ) :

		o = IECore.Object.create( "IECoreScenePreview::Placeholder" )
		self.assertIsInstance( o, GafferScene.Private.IECoreScenePreview.Placeholder )
		self.assertEqual( o.getBound(), imath.Box3f() )

	def testBound( self ) :

		o = GafferScene.Private.IECoreScenePreview.Placeholder(
			imath.Box3f( imath.V3f( 1, 2, 3 ), imath.V3f( 4, 5, 6 ) )
		)
		self.assertEqual(
			o.getBound(),
			imath.Box3f( imath.V3f( 1, 2, 3 ), imath.V3f( 4, 5, 6 ) )
		)

		o.setBound( imath.Box3f( imath.V3f( 2, 3, 4 ), imath.V3f( 5, 6, 7 ) ) )
		self.assertEqual(
			o.getBound(),
			imath.Box3f( imath.V3f( 2, 3, 4 ), imath.V3f( 5, 6, 7 ) )
		)

	def testCopy( self ) :

		o = GafferScene.Private.IECoreScenePreview.Placeholder(
			imath.Box3f( imath.V3f( 1, 2, 3 ), imath.V3f( 4, 5, 6 ) )
		)
		o2 = o.copy()
		self.assertEqual( o.getBound(), o2.getBound() )
		self.assertEqual( o, o2 )

		o2.setBound( imath.Box3f( imath.V3f( 2, 3, 4 ), imath.V3f( 5, 6, 7 ) ) )
		self.assertNotEqual( o.getBound(), o2.getBound() )
		self.assertNotEqual( o, o2 )

	def testSerialisation( self ) :

		o = GafferScene.Private.IECoreScenePreview.Placeholder(
			imath.Box3f( imath.V3f( 1, 2, 3 ), imath.V3f( 4, 5, 6 ) )
		)

		m = IECore.MemoryIndexedIO( IECore.CharVectorData(), [], IECore.IndexedIO.OpenMode.Write )
		o.save( m, "o" )

		m2 = IECore.MemoryIndexedIO( m.buffer(), [], IECore.IndexedIO.OpenMode.Read )
		o2 = IECore.Object.load( m2, "o" )

		self.assertEqual( o.getBound(), o2.getBound() )
		self.assertEqual( o, o2 )

if __name__ == "__main__":
	unittest.main()
