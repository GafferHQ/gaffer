##########################################################################
#
#  Copyright (c) 2013-2015, Image Engine Design Inc. All rights reserved.
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
#  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES LOSS OF USE, DATA, OR
#  PROFITS OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
##########################################################################

import unittest
import random
import os
import imath

import IECore

import Gaffer
import GafferTest
import GafferImage
import GafferImageTest

class ImageTransformTest( GafferImageTest.ImageTestCase ) :

	fileName = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/checker.exr" )
	path = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/" )

	def testNoPassThrough( self ) :

		# We don't want a perfect unfiltered pass-through when the
		# transform is the identity. This is because it can cause
		# conspicuous jumps when an animated transform happens to
		# pass through the identity matrix on a particular frame.

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.fileName )

		t = GafferImage.ImageTransform()
		t["in"].setInput( r["out"] )
		t["filter"].setValue( "blackman-harris" )

		self.assertNotEqual( GafferImage.ImageAlgo.imageHash( t["out"] ), GafferImage.ImageAlgo.imageHash( t["in"] ) )
		self.assertNotEqual( GafferImage.ImageAlgo.image( t["out"] ), GafferImage.ImageAlgo.image( t["in"] ) )

	def testTilesWithSameInputTiles( self ) :

		# This particular transform (along with many others) has output tiles
		# which share the exact same set of input tiles affecting their result.
		# This revealed a bug in ImageTransform::hashChannelData() whereby the
		# tile origin wasn't being hashed in to break the hashes for these output
		# tiles apart.

		r = GafferImage.ImageReader()
		r["fileName"].setValue( os.path.join( self.path, "rgb.100x100.exr" ) )

		t = GafferImage.ImageTransform()
		t["in"].setInput( r["out"] )
		t["transform"]["rotate"].setValue( -1. )
		t["transform"]["scale"].setValue( imath.V2f( 1.5, 1. ) )

		r2 = GafferImage.ImageReader()
		r2["fileName"].setValue( os.path.join( self.path, "knownTransformBug.exr" ) )

		self.assertImagesEqual( t["out"], r2["out"], ignoreMetadata = True, maxDifference = 0.05 )

	def testImageHash( self ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.fileName )

		t = GafferImage.ImageTransform()

		previousHash = GafferImage.ImageAlgo.imageHash( t["out"] )
		for plug in t["transform"].children() :

			if isinstance( plug, Gaffer.FloatPlug ) :
				plug.setValue( 1 )
			else :
				plug.setValue( imath.V2f( 2 ) )

			hash = GafferImage.ImageAlgo.imageHash( t["out"] )
			self.assertNotEqual( hash, previousHash )

			t["invert"].setValue( True )
			invertHash = GafferImage.ImageAlgo.imageHash( t["out"] )
			t["invert"].setValue( False )

			self.assertNotEqual( invertHash, hash )

			previousHash = hash

	def testDirtyPropagation( self ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.fileName )

		t = GafferImage.ImageTransform()
		t["in"].setInput( r["out"] )

		for plug in t["transform"].children() :

			cs = GafferTest.CapturingSlot( t.plugDirtiedSignal() )
			if isinstance( plug, Gaffer.FloatPlug ) :
				plug.setValue( 1 )
			else :
				plug.setValue( imath.V2f( 2 ) )

			dirtiedPlugs = { x[0] for x in cs }

			self.assertTrue( t["out"]["dataWindow"] in dirtiedPlugs )
			self.assertTrue( t["out"]["channelData"] in dirtiedPlugs )
			self.assertTrue( t["out"] in dirtiedPlugs )

			self.assertFalse( t["out"]["format"] in dirtiedPlugs )
			self.assertFalse( t["out"]["metadata"] in dirtiedPlugs )
			self.assertFalse( t["out"]["channelNames"] in dirtiedPlugs )

	def testOutputFormat( self ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.fileName )

		t = GafferImage.ImageTransform()
		t["in"].setInput( r["out"] )
		t["transform"]["translate"].setValue( imath.V2f( 2., 2. ) )

		self.assertEqual( t["out"]["format"].hash(), r["out"]["format"].hash() )

	def testDisabled( self ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.fileName )

		t = GafferImage.ImageTransform()
		t["in"].setInput( r["out"] )

		t["transform"]["translate"].setValue( imath.V2f( 2., 2. ) )
		t["transform"]["rotate"].setValue( 90 )
		t["enabled"].setValue( True )
		self.assertNotEqual( GafferImage.ImageAlgo.imageHash( r["out"] ), GafferImage.ImageAlgo.imageHash( t["out"] ) )

		t["enabled"].setValue( False )
		self.assertEqual( GafferImage.ImageAlgo.imageHash( r["out"] ), GafferImage.ImageAlgo.imageHash( t["out"] ) )

	def testPassThrough( self ) :

		c = GafferImage.Constant()
		t = GafferImage.ImageTransform()
		t["in"].setInput( c["out"] )
		t["transform"]["translate"].setValue( imath.V2f( 1, 0 ) )

		self.assertEqual( t["out"]["metadata"].hash(), c["out"]["metadata"].hash() )
		self.assertEqual( t["out"]["format"].hash(), c["out"]["format"].hash() )
		self.assertEqual( t["out"]["channelNames"].hash(), c["out"]["channelNames"].hash() )

		self.assertEqual( t["out"]["metadata"].getValue(), c["out"]["metadata"].getValue() )
		self.assertEqual( t["out"]["format"].getValue(), c["out"]["format"].getValue() )
		self.assertEqual( t["out"]["channelNames"].getValue(), c["out"]["channelNames"].getValue() )

	def testCopyPaste( self ) :

		script = Gaffer.ScriptNode()
		script["t"] = GafferImage.ImageTransform()

		script.execute( script.serialise( filter = Gaffer.StandardSet( [ script["t"] ] ) ) )

	def testAffects( self ) :

		c = GafferImage.Constant()
		t = GafferImage.ImageTransform()
		t["in"].setInput( c["out"] )

		cs = GafferTest.CapturingSlot( t.plugDirtiedSignal() )
		c["color"]["r"].setValue( .25 )

		self.assertTrue( t["out"]["channelData"] in set( s[0] for s in cs ) )

	def testInternalPlugsNotSerialised( self ) :

		s = Gaffer.ScriptNode()
		s["t"] = GafferImage.ImageTransform()

		ss = s.serialise()
		for name in s["t"].keys() :
			self.assertFalse( '\"{}\"'.format( name ) in ss )

	def testRotate360( self ) :

		# Check that a 360 degree rotation gives us the
		# same image back, regardless of pivot.

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.fileName )

		t = GafferImage.ImageTransform()
		t["in"].setInput( r["out"] )
		t["transform"]["rotate"].setValue( 360 )

		for i in range( 0, 100 ) :

			# Check that the ImageTransform isn't being smart and treating
			# this as a no-op. If the ImageTransform gets smart we'll need
			# to adjust our test to force it to do an actual resampling of
			# the image, since that's what we want to test.
			self.assertNotEqual(
				r["out"].channelDataHash( "R", imath.V2i( 0 ) ),
				t["out"].channelDataHash( "R", imath.V2i( 0 ) )
			)

			# Check that the rotated image is basically the same as the input.
			t["transform"]["pivot"].setValue(
				imath.V2f( random.uniform( -100, 100 ), random.uniform( -100, 100 ) ),
			)
			self.assertImagesEqual( r["out"], t["out"], maxDifference = 0.0001, ignoreDataWindow = True )

	def testSubpixelTranslate( self ) :

		# This checks we can do subpixel translations properly - at one
		# time a bug in Resample prevented this.

		# Use a Constant and a Crop to make a vertical line.
		constant = GafferImage.Constant()
		constant["format"].setValue( GafferImage.Format( 100, 100 ) )
		constant["color"].setValue( imath.Color4f( 1 ) )

		crop = GafferImage.Crop()
		crop["in"].setInput( constant["out"] )
		crop["affectDataWindow"].setValue( True )
		crop["affectDisplayWindow"].setValue( False )
		crop["area"].setValue( imath.Box2i( imath.V2i( 10, 0 ), imath.V2i( 11, 100 ) ) )

		# Check it's where we expect

		transform = GafferImage.ImageTransform()
		transform["in"].setInput( crop["out"] )
		transform["filter"].setValue( "rifman" )

		def sample( position ) :

			sampler = GafferImage.Sampler(
				transform["out"],
				"R",
				imath.Box2i( position, position + imath.V2i( 1 ) )
			)
			return sampler.sample( position.x, position.y )

		self.assertEqual( sample( imath.V2i( 9, 10 ) ), 0 )
		self.assertEqual( sample( imath.V2i( 10, 10 ) ), 1 )
		self.assertEqual( sample( imath.V2i( 11, 10 ) ), 0 )

		# Move it a tiiny bit, and check it has moved
		# a tiiny bit.

		transform["transform"]["translate"]["x"].setValue( 0.1 )

		self.assertEqual( sample( imath.V2i( 9, 10 ) ), 0 )
		self.assertGreater( sample( imath.V2i( 10, 10 ) ), 0.9 )
		self.assertGreater( sample( imath.V2i( 11, 10 ) ), 0.09 )

	def testNegativeScale( self ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/checker2x2.exr" ) )

		t = GafferImage.ImageTransform()
		t["in"].setInput( r["out"] )
		t["transform"]["pivot"].setValue( imath.V2f( 1 ) )
		t["transform"]["scale"]["x"].setValue( -1 )

		sampler = GafferImage.Sampler(
			t["out"],
			"R",
			t["out"]["dataWindow"].getValue()
		)

		self.assertEqual( sampler.sample( 0, 0 ), 0 )
		self.assertEqual( sampler.sample( 1, 0 ), 1 )
		self.assertEqual( sampler.sample( 0, 1 ), 1 )
		self.assertEqual( sampler.sample( 1, 1 ), 0 )

	def testRotateEmptyDataWindow( self ) :

		r = GafferImage.ImageReader()
		self.assertEqual( r["out"]["dataWindow"].getValue(), imath.Box2i() )

		t = GafferImage.ImageTransform()
		t["in"].setInput( r["out"] )
		t["transform"]["rotate"].setValue( 1 )

		self.assertEqual( t["out"]["dataWindow"].getValue(), imath.Box2i() )

	def testInvertTransform( self ):

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.fileName )

		t = GafferImage.ImageTransform()
		t["in"].setInput( r["out"] )
		t["transform"]["rotate"].setValue( 45 )

		tInv = GafferImage.ImageTransform()
		tInv["in"].setInput( t["out"] )
		tInv["transform"]["rotate"].setValue( 45 )
		tInv["invert"].setValue( True )

		self.assertNotEqual(
			r["out"].channelDataHash( "R", imath.V2i( 0 ) ),
			t["out"].channelDataHash( "R", imath.V2i( 0 ) )
		)

		self.assertImagesEqual( r["out"], tInv["out"], maxDifference = 0.5, ignoreDataWindow=True )

if __name__ == "__main__":
	unittest.main()
