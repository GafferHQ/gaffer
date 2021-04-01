##########################################################################
#
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

import Gaffer
import GafferImage
import GafferImageTest

class FormatDataTest( GafferImageTest.ImageTestCase ) :

	def test( self ) :

		f1 = GafferImage.Format( imath.Box2i( imath.V2i( 0 ), imath.V2i( 200, 100 ) ), 0.5 )
		f2 = GafferImage.Format( imath.Box2i( imath.V2i( 0 ), imath.V2i( 200, 100 ) ), 1 )

		fd1a = GafferImage.FormatData( f1 )
		fd1b = GafferImage.FormatData( f1 )
		fd2 = GafferImage.FormatData( f2 )

		self.assertEqual( fd1a.value, f1 )
		self.assertEqual( fd1b.value, f1 )
		self.assertEqual( fd2.value, f2 )

		self.assertEqual( fd1a, fd1b )
		self.assertNotEqual( fd1a, fd2 )

		self.assertEqual( fd1a.hash(), fd1b.hash() )
		self.assertNotEqual( fd1a.hash(), fd2.hash() )

		fd2c = fd2.copy()
		self.assertEqual( fd2c, fd2 )
		self.assertEqual( fd2c.hash(), fd2.hash() )

	def testSerialisation( self ) :

		f = GafferImage.Format( imath.Box2i( imath.V2i( 10, 20 ), imath.V2i( 200, 100 ) ), 0.5 )
		fd = GafferImage.FormatData( f )

		m = IECore.MemoryIndexedIO( IECore.CharVectorData(), [], IECore.IndexedIO.OpenMode.Write )

		fd.save( m, "f" )

		m2 = IECore.MemoryIndexedIO( m.buffer(), [], IECore.IndexedIO.OpenMode.Read )
		fd2 = IECore.Object.load( m2, "f" )

		self.assertEqual( fd2, fd )
		self.assertEqual( fd2.value, f )

	def testAutoConstructFromFormat( self ) :

		f = GafferImage.Format( imath.Box2i( imath.V2i( 0 ), imath.V2i( 200, 100 ) ), 0.5 )

		d = IECore.CompoundData()
		d["f"] = f
		self.assertEqual( d["f"], GafferImage.FormatData( f ) )

	def testStoreInContext( self ) :

		f = GafferImage.Format( imath.Box2i( imath.V2i( 0 ), imath.V2i( 200, 100 ) ), 0.5 )
		d = GafferImage.FormatData( f )
		c = Gaffer.Context()
		c["f"] = d
		self.assertEqual( c["f"], d )

	def testEditableScopeForFormat( self ) :
		GafferImageTest.testEditableScopeForFormat()

if __name__ == "__main__":
	unittest.main()
