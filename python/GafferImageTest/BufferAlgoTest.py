##########################################################################
#
#  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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
import GafferImage
import GafferImageTest

class BufferAlgoTest( GafferImageTest.ImageTestCase ) :

	def testEmpty( self ) :

		self.assertTrue( GafferImage.BufferAlgo.empty( IECore.Box2i() ) )
		self.assertTrue( GafferImage.BufferAlgo.empty( IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 0 ) ) ) )
		self.assertFalse( GafferImage.BufferAlgo.empty( IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 1 ) ) ) )
		self.assertTrue( GafferImage.BufferAlgo.empty( IECore.Box2i( IECore.V2i( 2147483646 ), IECore.V2i( -2147483646 ) ) ) )
		self.assertTrue( GafferImage.BufferAlgo.empty( IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( -2147483647 ) ) ) )
		self.assertTrue( GafferImage.BufferAlgo.empty( IECore.Box2i( IECore.V2i( 2147483647 ), IECore.V2i( 0 ) ) ) )
		self.assertTrue( GafferImage.BufferAlgo.empty( IECore.Box2i( IECore.V2i( -1 ), IECore.V2i( -2147483647 ) ) ) )
		self.assertTrue( GafferImage.BufferAlgo.empty( IECore.Box2i( IECore.V2i( 2147483647 ), IECore.V2i( 1 ) ) ) )
		self.assertTrue( GafferImage.BufferAlgo.empty( IECore.Box2i( IECore.V2i( 1 ), IECore.V2i( -2147483647 ) ) ) )
		self.assertTrue( GafferImage.BufferAlgo.empty( IECore.Box2i( IECore.V2i( 2147483647 ), IECore.V2i( -1 ) ) ) )

	def testIntersects( self ) :

		self.assertFalse(
			GafferImage.BufferAlgo.intersects(
				IECore.Box2i(), IECore.Box2i()
			)
		)

		self.assertFalse(
			GafferImage.BufferAlgo.intersects(
				IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 10 ) ),
				IECore.Box2i( IECore.V2i( 10 ), IECore.V2i( 20 ) ),
			)
		)

		self.assertTrue(
			GafferImage.BufferAlgo.intersects(
				IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 10 ) ),
				IECore.Box2i( IECore.V2i( 9 ), IECore.V2i( 20 ) ),
			)
		)

	def testIntersection( self ) :

		self.assertEqual(
			GafferImage.BufferAlgo.intersection(
				IECore.Box2i( IECore.V2i( 1, 2 ), IECore.V2i( 9, 10 ) ),
				IECore.Box2i( IECore.V2i( 2, 0 ), IECore.V2i( 8, 29 ) ),
			),
			IECore.Box2i(
				IECore.V2i( 2, 2 ),
				IECore.V2i( 8, 10 )
			)
		)

	def testContains( self ) :

		self.assertFalse(
			GafferImage.BufferAlgo.contains(
				IECore.Box2i(),
				IECore.V2i( 0 )
			)
		)

		self.assertFalse(
			GafferImage.BufferAlgo.contains(
				IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 0 ) ),
				IECore.V2i( 0 )
			)
		)

		self.assertFalse(
			GafferImage.BufferAlgo.contains(
				IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 1 ) ),
				IECore.V2i( 1 )
			)
		)

		self.assertTrue(
			GafferImage.BufferAlgo.contains(
				IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 1 ) ),
				IECore.V2i( 0 )
			)
		)

	def testClamp( self ) :

		self.assertEqual(
			GafferImage.BufferAlgo.clamp(
				IECore.V2i( 5, 6 ),
				IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 10 ) )
			),
			IECore.V2i( 5, 6 )
		)

		self.assertEqual(
			GafferImage.BufferAlgo.clamp(
				IECore.V2i( 10, 6 ),
				IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 10 ) )
			),
			IECore.V2i( 9, 6 )
		)

		self.assertEqual(
			GafferImage.BufferAlgo.clamp(
				IECore.V2i( 0, 6 ),
				IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 10 ) )
			),
			IECore.V2i( 0, 6 )
		)

		self.assertEqual(
			GafferImage.BufferAlgo.clamp(
				IECore.V2i( 5, -1 ),
				IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 10 ) )
			),
			IECore.V2i( 5, 0 )
		)

		self.assertEqual(
			GafferImage.BufferAlgo.clamp(
				IECore.V2i( 5, 10 ),
				IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 10 ) )
			),
			IECore.V2i( 5, 9 )
		)

if __name__ == "__main__":
	unittest.main()
