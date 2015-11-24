##########################################################################
#
#  Copyright (c) 2012-2015, Image Engine Design Inc. All rights reserved.
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
import random

import IECore

import Gaffer
import GafferTest

import GafferImage
import GafferImageTest

class FormatTest( GafferImageTest.ImageTestCase ) :

	def testOffsetDisplayWindow( self ) :

		box = IECore.Box2i( IECore.V2i( 6, -4 ), IECore.V2i( 50, 150 ) )
		f = GafferImage.Format( box, 1.1 )
		self.assertEqual( f.getDisplayWindow(), box )
		self.assertEqual( f.width(), 44 )
		self.assertEqual( f.height(), 154 )
		self.assertEqual( f.getPixelAspect(), 1.1 )

	def testBoxAspectConstructor( self ) :

		f = GafferImage.Format( IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 50, 150 ) ), 1.3 )
		self.assertEqual( f.width(), 50 )
		self.assertEqual( f.height(), 150 )
		self.assertEqual( f.getPixelAspect(), 1.3 )

	def testDefaultPixelAspect( self ) :

		f = GafferImage.Format( 100, 100 )
		self.assertEqual( f.getPixelAspect(), 1. )

		f = GafferImage.Format( IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 100, 100 ) ) )
		self.assertEqual( f.getPixelAspect(), 1. )

	def testWH( self ) :

		f = GafferImage.Format( 101, 102, 1. )
		self.assertEqual( f.width(), 101 )
		self.assertEqual( f.height(), 102 )

		f = GafferImage.Format( 0, 0, 1. )
		self.assertEqual( f.width(), 0 )
		self.assertEqual( f.height(), 0 )

	def testEXRSpaceFormat( self ) :

		f = GafferImage.Format( IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 99 ) ), 1.0, True )
		self.assertEqual( f.width(), 100 )
		self.assertEqual( f.height(), 100 )
		self.assertEqual(
			f.toEXRSpace( f.getDisplayWindow() ),
			IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 99 ) ),
		)

		f = GafferImage.Format( IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 99 ) ), 1.0, fromEXRSpace = True )
		self.assertEqual( f.width(), 100 )
		self.assertEqual( f.height(), 100 )
		self.assertEqual(
			f.toEXRSpace( f.getDisplayWindow() ),
			IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 99 ) ),
		)

		f = GafferImage.Format( IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 100 ) ), 1.0, fromEXRSpace = False )
		self.assertEqual( f.width(), 100 )
		self.assertEqual( f.height(), 100 )
		self.assertEqual(
			f.getDisplayWindow(),
			IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 100 ) ),
		)

	def testCoordinateSystemTransforms( self ) :

		f = GafferImage.Format( IECore.Box2i( IECore.V2i( -100, -200 ), IECore.V2i( 501, 301 ) ), 1 )

		self.assertEqual( f.fromEXRSpace( IECore.V2i( -100, -200 ) ), IECore.V2i( -100, 300 ) )
		self.assertEqual( f.fromEXRSpace( IECore.V2i( -100, 300 ) ), IECore.V2i( -100, -200 ) )

		self.assertEqual( f.toEXRSpace( IECore.V2i( -100, -200 ) ), IECore.V2i( -100, 300 ) )
		self.assertEqual( f.toEXRSpace( IECore.V2i( -100, 300 ) ), IECore.V2i( -100, -200 ) )

		self.assertEqual(
			f.toEXRSpace(
				IECore.Box2i( IECore.V2i( -100, -200 ), IECore.V2i( 501, 301 ) )
			),
			IECore.Box2i( IECore.V2i( -100, -200 ), IECore.V2i( 500, 300 ) )
		)

		self.assertEqual(
			f.toEXRSpace(
				IECore.Box2i( IECore.V2i( -100, -100 ), IECore.V2i( 501, 301 ) )
			),
			IECore.Box2i( IECore.V2i( -100, -200 ), IECore.V2i( 500, 200 ) )
		)

		self.assertEqual(
			f.toEXRSpace(
				IECore.Box2i( IECore.V2i( -100, -200 ), IECore.V2i( 501, -100 ) )
			),
			IECore.Box2i( IECore.V2i( -100, 201 ), IECore.V2i( 500, 300 ) )
		)

		for i in range( 0, 1000 ) :

			p = IECore.V2i( int( random.uniform( -500, 500 ) ), int( random.uniform( -500, 500 ) ) )
			pDown = f.toEXRSpace( p )
			self.assertEqual( f.fromEXRSpace( pDown ), p )

			b = IECore.Box2i()
			b.extendBy( IECore.V2i( int( random.uniform( -500, 500 ) ), int( random.uniform( -500, 500 ) ) ) )
			b.extendBy( IECore.V2i( int( random.uniform( -500, 500 ) ), int( random.uniform( -500, 500 ) ) ) )

			bDown = f.toEXRSpace( b )
			if not GafferImage.empty( b ) :
				self.assertEqual( f.fromEXRSpace( bDown ), b )
			else :
				self.assertEqual( f.fromEXRSpace( bDown ), IECore.Box2i() )

	def testDisplayWindowCoordinateSystemTransforms( self ) :

		f = GafferImage.Format( 10, 10, 1.0 )

		self.assertEqual( f.toEXRSpace( 0 ), 9 )
		self.assertEqual( f.toEXRSpace( 9 ), 0 )

		self.assertEqual( f.fromEXRSpace( 9 ), 0 )
		self.assertEqual( f.fromEXRSpace( 0 ), 9 )

		self.assertEqual(
			f.toEXRSpace( f.getDisplayWindow() ),
			IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 9 ) )
		)

		self.assertEqual(
			f.fromEXRSpace( IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 9 ) ) ),
			f.getDisplayWindow()
		)

	def testRegistry( self ) :

		f = GafferImage.Format( 100, 200, 2 )

		# Our test format should not be registered yet.
		self.assertTrue( "testFormat" not in GafferImage.Format.registeredFormats() )
		self.assertEqual( GafferImage.Format.name( f ), "" )

		# If we register it, it should be queryable afterwards.
		GafferImage.Format.registerFormat( "testFormat", f )
		self.assertTrue( "testFormat" in GafferImage.Format.registeredFormats() )
		self.assertEqual( GafferImage.Format.name( f ), "testFormat" )
		self.assertEqual( GafferImage.Format.format( "testFormat"), f )

		# And if we reregister it with a new value, that should
		# override the previous registration.
		f = GafferImage.Format( 200, 200, 2 )
		GafferImage.Format.registerFormat( "testFormat", f )
		self.assertTrue( "testFormat" in GafferImage.Format.registeredFormats() )
		self.assertEqual( GafferImage.Format.name( f ), "testFormat" )
		self.assertEqual( GafferImage.Format.format( "testFormat"), f )

		# If we deregister it, it should be gone gone gone.
		GafferImage.Format.deregisterFormat( "testFormat" )
		self.assertTrue( "testFormat" not in GafferImage.Format.registeredFormats() )
		self.assertEqual( GafferImage.Format.name( f ), "" )

	def testStr( self ) :

		f = GafferImage.Format( 10, 20 )
		self.assertEqual( str( f ), "10x20" )

		f = GafferImage.Format( 10, 20, 2 )
		self.assertEqual( str( f ), "10x20, 2" )

		f = GafferImage.Format( IECore.Box2i( IECore.V2i( 10 ), IECore.V2i( 20 ) ) )
		self.assertEqual( str( f ), "(10 10) - (20 20)" )

	def testEmptyBoxCoordinateSystemTransforms( self ) :

		f = GafferImage.Format( 100, 200 )
		self.assertEqual( f.toEXRSpace( IECore.Box2i() ), IECore.Box2i() )
		self.assertEqual( f.toEXRSpace( IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 0 ) ) ), IECore.Box2i() )
		self.assertEqual( f.fromEXRSpace( IECore.Box2i() ), IECore.Box2i() )

	def tearDown( self ) :

		GafferTest.TestCase.tearDown( self )

		GafferImage.Format.deregisterFormat( "testFormat" )

if __name__ == "__main__":
	unittest.main()
