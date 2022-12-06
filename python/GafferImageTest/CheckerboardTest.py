##########################################################################
#
#  Copyright (c) 2017, John Haddon. All rights reserved.
#  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

import os
import pathlib
import unittest

import imath

import IECore

import Gaffer
import GafferTest
import GafferImage
import GafferImageTest

class CheckerboardTest( GafferImageTest.ImageTestCase ) :

	def testChannelData( self ) :

		checkerboard = GafferImage.Checkerboard()
		checkerboard["format"].setValue( GafferImage.Format( imath.Box2i( imath.V2i( 0 ), imath.V2i( 511 ) ), 1 ) )
		checkerboard["colorA"].setValue( imath.Color4f( 0.1, 0.25, 0.5, 1 ) )

		for i, channel in enumerate( [ "R", "G", "B", "A" ] ) :
			channelData = checkerboard["out"].channelData( channel, imath.V2i( 0 ) )
			self.assertEqual( len( channelData ), checkerboard["out"].tileSize() * checkerboard["out"].tileSize() )

			expectedValue = checkerboard["colorA"][i].getValue()
			s = GafferImage.Sampler( checkerboard["out"], channel, checkerboard["out"]["dataWindow"].getValue() )
			self.assertEqual( s.sample( 12, 12 ), expectedValue )
			self.assertEqual( s.sample( 72, 72 ), expectedValue )

	def testFormatHash( self ) :

		# Check that the data hash change when the format does.
		c = GafferImage.Checkerboard()
		c["format"].setValue( GafferImage.Format( 2048, 1156, 1. ) )
		h1 = c["out"].channelData( "R", imath.V2i( 0 ) ).hash()
		c["format"].setValue( GafferImage.Format( 1920, 1080, 1. ) )
		h2 = c["out"].channelData( "R", imath.V2i( 0 ) ).hash()
		self.assertEqual( h1, h2 )

	def testEnableBehaviour( self ) :

		c = GafferImage.Checkerboard()
		self.assertTrue( c.enabledPlug().isSame( c["enabled"] ) )
		self.assertEqual( c.correspondingInput( c["out"] ), None )
		self.assertEqual( c.correspondingInput( c["colorA"] ), None )
		self.assertEqual( c.correspondingInput( c["colorB"] ), None )
		self.assertEqual( c.correspondingInput( c["size"] ), None )
		self.assertEqual( c.correspondingInput( c["format"] ), None )

	def testChannelNamesHash( self ) :

		c = GafferImage.Checkerboard()
		h1 = c["out"]["channelNames"].hash()
		c["colorA"].setValue( imath.Color4f( 1, 0.5, 0.25, 1 ) )
		h2 = c["out"]["channelNames"].hash()

		self.assertEqual( h1, h2 )

	def testSerialisationWithZeroAlpha( self ) :

		s = Gaffer.ScriptNode()
		s["c"] = GafferImage.Checkerboard()
		s["c"]["colorA"].setValue( imath.Color4f( 0, 1, 0, 0 ) )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( s2["c"]["colorA"].getValue(), imath.Color4f( 0, 1, 0, 0 ) )

	def testFormatDependencies( self ) :

		c = GafferImage.Checkerboard()

		self.assertEqual(
			c.affects( c["format"]["pixelAspect"] ),
			[ c["out"]["format"] ],
		)

		self.assertEqual(
			c.affects( c["format"]["displayWindow"]["min"]["x"] ),
			[ c["out"]["format"], c["out"]["dataWindow"]]
		)

		self.assertEqual(
			c.affects( c["colorA"]["r"] ),
			[ c["out"]["channelData"] ],
		)

		self.assertEqual(
			c.affects( c["colorB"]["r"] ),
			[ c["out"]["channelData"] ],
		)

		self.assertEqual(
			c.affects( c["size"]["x"] ),
			[ c["out"]["channelData"] ],
		)

	def testLayerAffectsChannelNames( self ) :

		c = GafferImage.Checkerboard()
		cs = GafferTest.CapturingSlot( c.plugDirtiedSignal() )
		c["layer"].setValue( "diffuse" )

		self.assertTrue( c["out"]["channelNames"] in set( [ x[0] for x in cs ] ) )

	def testExpectedResult( self ) :

		checkerboard = GafferImage.Checkerboard()
		checkerboard["format"].setValue( GafferImage.Format( 128, 128 ) )
		checkerboard["size"]["x"].setValue( 1 )
		checkerboard["size"]["y"].setValue( 1 )
		checkerboard["transform"]["rotate"].setValue( 45 )
		checkerboard["transform"]["scale"]["x"].setValue( 200 )
		checkerboard["transform"]["scale"]["y"].setValue( 10 )

		reader = GafferImage.ImageReader()
		reader["fileName"].setValue( pathlib.Path( __file__ ).parent / "images" / "GafferChecker.exr" )

		# The image
		self.assertImagesEqual( checkerboard["out"], reader["out"], ignoreMetadata = True, maxDifference = 0.0002 )

	def testFilterWidth( self ) :

		checkerboard = GafferImage.Checkerboard()
		checkerboard["format"].setValue( GafferImage.Format( 128, 128 ) )
		checkerboard["size"]["x"].setValue( 1 )
		checkerboard["size"]["y"].setValue( 1 )
		checkerboard["transform"]["scale"]["x"].setValue( 200 )
		checkerboard["transform"]["scale"]["y"].setValue( 200 )

		sampler = GafferImage.ImageSampler()
		sampler["image"].setInput( checkerboard["out"] )

		# Pixels on the border could be classified as within the filter width due to floating point precision,
		# and could have floating point error
		sampler["pixel"].setValue( imath.V2f( 101, 54 ) )
		self.assertAlmostEqual( checkerboard["colorB"].getValue().r, sampler["color"].getValue().r, delta = 0.0000001 )

		# Pixels on the interior of a checker must be exact
		sampler["pixel"].setValue( imath.V2f( 102, 54 ) )
		self.assertEqual( checkerboard["colorB"].getValue().r, sampler["color"].getValue().r )

	def testValuesIdentical( self ):

		checkerboard = GafferImage.Checkerboard()
		checkerboard["format"].setValue( GafferImage.Format( 1024, 1024, 1 ) )
		checkerboard["size"].setValue( imath.V2f( 14 ) )

		offset = GafferImage.Offset()
		offset["in"].setInput( checkerboard["out"] )
		offset["offset"].setValue( imath.V2i( 7 ) )

		merge = GafferImage.Merge()
		merge["in"][0].setInput( checkerboard["out"] )
		merge["in"][1].setInput( offset["out"] )
		merge["operation"].setValue( GafferImage.Merge.Operation.Difference )

		imageStats = GafferImage.ImageStats()
		imageStats["in"].setInput( merge["out"] )
		imageStats["area"].setValue( imath.Box2i( imath.V2i( 7 ), imath.V2i( 1024 ) ) )

		self.assertLess( imageStats["max"][0].getValue(), 2e-5 )
		self.assertLess( imageStats["average"][0].getValue(), 5e-7 )

	def testSeparableCodePath( self ):

		# Make sure that there is no inordinate difference between the special optimized code
		# when rotation is 0 and the general code
		checker1 = GafferImage.Checkerboard()
		checker1["size"].setValue( imath.V2f( 35, 121 ) )
		checker1["transform"]["translate"].setValue( imath.V2f( 214.849503, -199.025101 ) )
		checker1["transform"]["scale"].setValue( imath.V2f( 7.1413002, 0.640600026 ) )

		checker2 = GafferImage.Checkerboard()
		checker2["size"].setValue( imath.V2f( 35, 121 ) )
		checker2["transform"]["translate"].setValue( imath.V2f( 214.849503, -199.025101 ) )
		checker2["transform"]["scale"].setValue( imath.V2f( 7.1413002, 0.640600026 ) )
		checker2["transform"]["rotate"].setValue( 1e-6 )

		diff = GafferImage.Merge()
		diff["in"][0].setInput( checker2["out"] )
		diff["in"][1].setInput( checker1["out"] )
		diff["operation"].setValue( GafferImage.Merge.Operation.Difference )

		stats = GafferImage.ImageStats()
		stats["in"].setInput( diff["out"] )
		stats["area"].setValue( imath.Box2i( imath.V2i( 0, 0 ), imath.V2i( 1920, 1080 ) ) )

		self.assertGreater( stats["max"].getValue()[0], 0 ) # Should produce some change
		self.assertLess( stats["max"].getValue()[0], 1e-4 ) # But nothing visible
		self.assertLess( stats["average"].getValue()[0], 1e-6 )

if __name__ == "__main__":
	unittest.main()
