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

class FormatTest( GafferTest.TestCase ) :

	def testAddRemoveFormat( self ) :

		# Get any existing format names
		existingFormatNames = GafferImage.Format.formatNames()

		# Assert that our test format is in not in the list of formats
		self.assertFalse( self.__testFormatName() in existingFormatNames )

		# Add a test format
		GafferImage.Format.registerFormat( self.__testFormatValue(), self.__testFormatName() )

		# Get the new list of format names and test that it contains our new format
		self.assertTrue( self.__testFormatName() in GafferImage.Format.formatNames() )

		# Attempt to get the format we added by name and check to see if the results are what we expect
		testFormat = GafferImage.Format.getFormat( self.__testFormatName() )
		self.__assertTestFormat( testFormat )

		# Now remove it by name.
		GafferImage.Format.removeFormat( self.__testFormatName() )

		# Get the new list of format names and check that it is the same as the old list
		self.assertEqual( set( existingFormatNames ), set( GafferImage.Format.formatNames() ) )

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

	def testAddRemoveFormatByValue( self ) :

		# Get any existing format names
		existingFormatNames = GafferImage.Format.formatNames()

		# Assert that our test format is in not in the list of formats
		self.assertFalse( self.__testFormatName() in existingFormatNames )

		# Add a test format by value only
		GafferImage.Format.registerFormat( self.__testFormatValue() )

		# Get the new list of format names and test that it contains our new format name
		self.assertTrue( self.__testFormatName() in GafferImage.Format.formatNames() )

		# Attempt to get the format we added by name and check to see if the results are what we expect
		testFormat = GafferImage.Format.getFormat( self.__testFormatName() )
		self.__assertTestFormat( testFormat )

		# Now remove it by value.
		GafferImage.Format.removeFormat( self.__testFormatValue() )

		# Get the new list of format names and check that it is the same as the old list
		self.assertEqual( set( existingFormatNames ), set( GafferImage.Format.formatNames() ) )

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
			self.assertEqual( f.fromEXRSpace( bDown ), b )

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

	def tearDown( self ) :

		GafferTest.TestCase.tearDown( self )

		GafferImage.Format.removeFormat( self.__testFormatName() )

	def __assertTestFormat( self, testFormat ) :

		self.assertEqual( testFormat.getPixelAspect(), 1.4 )
		self.assertEqual( testFormat.width(), 1234 )
		self.assertEqual( testFormat.height(), 5678 )
		self.assertEqual( testFormat.getDisplayWindow(), IECore.Box2i( IECore.V2i( 0, 0 ), IECore.V2i( 1234, 5678 ) ) )

	def __testFormatValue( self ) :

		return GafferImage.Format( 1234, 5678, 1.4 )

	def __testFormatName( self ) :

		return '1234x5678 1.400'

if __name__ == "__main__":
	unittest.main()
