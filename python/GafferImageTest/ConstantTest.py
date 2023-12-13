##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
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
import GafferTest
import GafferImage
import GafferImageTest

class ConstantTest( GafferImageTest.ImageTestCase ) :

	def testChannelData( self ) :

		constant = GafferImage.Constant()
		constant["format"].setValue( GafferImage.Format( imath.Box2i( imath.V2i( 0 ), imath.V2i( 511 ) ), 1 ) )
		constant["color"].setValue( imath.Color4f( 0, 0.25, 0.5, 1 ) )

		for i, channel in enumerate( [ "R", "G", "B", "A" ] ) :
			channelData = constant["out"].channelData( channel, imath.V2i( 0 ) )
			self.assertEqual( len( channelData ), constant["out"].tileSize() * constant["out"].tileSize() )
			expectedValue = constant["color"][i].getValue()
			for value in channelData :
				self.assertEqual( value, expectedValue )

	def testChannelDataHash( self ) :

		# The hash for each individual channel should only
		# be affected by that particular channel of the colour plug.

		constant = GafferImage.Constant()
		constant["format"].setValue( GafferImage.Format( imath.Box2i( imath.V2i( 0 ), imath.V2i( 511 ) ), 1 ) )
		constant["color"].setValue( imath.Color4f( 0 ) )

		channels = [ "R", "G", "B", "A" ]
		for i, channel in enumerate( channels ) :

			h1 = [ constant["out"].channelDataHash( c, imath.V2i( 0 ) ) for c in channels ]
			constant["color"][i].setValue( constant["color"][i].getValue() + .1 )
			h2 = [ constant["out"].channelDataHash( c, imath.V2i( 0 ) ) for c in channels ]

			for j in range( 0, len( channels ) ) :
				if j == i :
					self.assertNotEqual( h1[j], h2[j] )
				else :
					self.assertEqual( h1[j], h2[j] )

	def testFormatHash( self ) :

		# Check that the data hash doesn't change when the format does.
		c = GafferImage.Constant()
		c["format"].setValue( GafferImage.Format( 2048, 1156, 1. ) )
		h1 = c["out"].channelData( "R", imath.V2i( 0 ) ).hash()
		c["format"].setValue( GafferImage.Format( 1920, 1080, 1. ) )
		h2 = c["out"].channelData( "R", imath.V2i( 0 ) ).hash()
		self.assertEqual( h1, h2 )

	def testTileHashes( self ) :

		# Test that two tiles within the image have the same hash.
		c = GafferImage.Constant()
		c["format"].setValue( GafferImage.Format( 2048, 1156, 1. ) )
		c["color"][0].setValue( .5 )

		self.assertEqual(
			c["out"].channelDataHash( "R", imath.V2i( 0 ) ),
			c["out"].channelDataHash( "R", imath.V2i( GafferImage.ImagePlug().tileSize() ) ),
		)

	def testTileIdentity( self ) :

		c = GafferImage.Constant()
		c["format"].setValue( GafferImage.Format( 2048, 1156, 1. ) )

		# The channelData() binding returns a copy by default, so we wouldn't
		# expect two tiles to be referencing the same object.
		self.assertFalse(
			c["out"].channelData( "R", imath.V2i( 0 ) ).isSame(
				c["out"].channelData( "R", imath.V2i( GafferImage.ImagePlug.tileSize() ) )
			)
		)

		# But behind the scenes we do want them to be the same, so
		# check that that is the case.
		self.assertTrue(
			c["out"].channelData( "R", imath.V2i( 0 ), _copy = False ).isSame(
				c["out"].channelData( "R", imath.V2i( GafferImage.ImagePlug.tileSize() ), _copy = False )
			)
		)

	def testEnableBehaviour( self ) :

		c = GafferImage.Constant()
		self.assertTrue( c.enabledPlug().isSame( c["enabled"] ) )
		self.assertEqual( c.correspondingInput( c["out"] ), None )
		self.assertEqual( c.correspondingInput( c["color"] ), None )
		self.assertEqual( c.correspondingInput( c["format"] ), None )

	def testChannelNamesHash( self ) :

		c = GafferImage.Constant()
		h1 = c["out"]["channelNames"].hash()
		c["color"].setValue( imath.Color4f( 1, 0.5, 0.25, 1 ) )
		h2 = c["out"]["channelNames"].hash()

		self.assertEqual( h1, h2 )

	def testSerialisationWithZeroAlpha( self ) :

		s = Gaffer.ScriptNode()
		s["c"] = GafferImage.Constant()
		s["c"]["color"].setValue( imath.Color4f( 0, 1, 0, 0 ) )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( s2["c"]["color"].getValue(), imath.Color4f( 0, 1, 0, 0 ) )

	def testFormatDependencies( self ) :

		c = GafferImage.Constant()

		self.assertEqual(
			c.affects( c["format"]["displayWindow"]["min"]["x"] ),
			[ c["out"]["format"], c["out"]["dataWindow"] ],
		)

		# For the sake of simplicity when dealing with falling back to a default format from the context,
		# we make all child plugs of the format affect everything that depends at all on the format
		self.assertEqual(
			c.affects( c["format"]["pixelAspect"] ),
			[ c["out"]["format"], c["out"]["dataWindow"] ],
		)

	def testLayer( self ) :

		c1 = GafferImage.Constant()
		c2 = GafferImage.Constant()

		c1["color"].setValue( imath.Color4f( 1, 0.5, 0.25, 1 ) )
		c2["color"].setValue( imath.Color4f( 1, 0.5, 0.25, 1 ) )
		c2["layer"].setValue( "diffuse" )

		self.assertEqual(
			c1["out"]["channelNames"].getValue(),
			IECore.StringVectorData( [ "R", "G", "B", "A" ] )
		)

		self.assertEqual(
			c2["out"]["channelNames"].getValue(),
			IECore.StringVectorData( [ "diffuse.R", "diffuse.G", "diffuse.B", "diffuse.A" ] )
		)

		for channelName in ( "R", "G", "B", "A" ) :

			self.assertEqual(
				c1["out"].channelDataHash( channelName, imath.V2i( 0 ) ),
				c2["out"].channelDataHash( "diffuse." + channelName, imath.V2i( 0 ) )
			)

			self.assertEqual(
				c1["out"].channelData( channelName, imath.V2i( 0 ) ),
				c2["out"].channelData( "diffuse." + channelName, imath.V2i( 0 ) )
			)

	def testLayerAffectsChannelNames( self ) :

		c = GafferImage.Constant()
		cs = GafferTest.CapturingSlot( c.plugDirtiedSignal() )
		c["layer"].setValue( "diffuse" )

		self.assertTrue( c["out"]["channelNames"] in set( [ x[0] for x in cs ] ) )

	def testAssertImagesEqual( self ) :

		a = GafferImage.Constant()
		a["color"].setValue( imath.Color4f( 0.5 ) )

		b = GafferImage.Constant()
		b["color"].setValue( imath.Color4f( 0.5 ) )

		self.assertImagesEqual( a["out"], b["out"] )

		a["color"].setValue( imath.Color4f( 0.75 ) )

		with self.assertRaisesRegex( AssertionError, "0.25 not less than or equal to 0.0 : Channel R" ) :
			self.assertImagesEqual( a["out"], b["out"] )

		self.assertImagesEqual( a["out"], b["out"], maxDifference = 0.25 )

		self.assertImagesEqual( a["out"], b["out"], maxDifference = ( -0.25, 0.0 ) )
		with self.assertRaisesRegex( AssertionError, "-0.25 not greater than or equal to 0.0 : Channel R" ) :
			self.assertImagesEqual( a["out"], b["out"], maxDifference = ( 0.0, 0.25 ) )

		b["color"].setValue( imath.Color4f( 1.0 ) )

		self.assertImagesEqual( a["out"], b["out"], maxDifference = ( 0.0, 0.25 ) )
		with self.assertRaisesRegex( AssertionError, "0.25 not less than or equal to 0.0 : Channel R" ) :
			self.assertImagesEqual( a["out"], b["out"], maxDifference = ( -0.25, 0.0 ) )


if __name__ == "__main__":
	unittest.main()
