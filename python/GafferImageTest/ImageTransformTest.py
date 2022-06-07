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
import inspect
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


	def testNonFlatThrows( self ) :

		transform = GafferImage.ImageTransform()
		transform["transform"]["translate"].setValue( imath.V2f( 20., 20.5 ) )

		self.assertRaisesDeepNotSupported( transform )


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

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testRotationPerformance( self ) :

		checker = GafferImage.Checkerboard()
		checker["format"].setValue( GafferImage.Format( 3000, 3000 ) )

		transform = GafferImage.ImageTransform()
		transform["in"].setInput( checker["out"] )
		transform["transform"]["pivot"].setValue( imath.V2f( 1500 ) )
		transform["transform"]["rotate"].setValue( 2.5 )

		with GafferTest.TestRunner.PerformanceScope() :
			GafferImageTest.processTiles( transform["out"] )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testTranslationPerformance( self ) :

		checker = GafferImage.Checkerboard()
		checker["format"].setValue( GafferImage.Format( 3000, 3000 ) )

		transform = GafferImage.ImageTransform()
		transform["in"].setInput( checker["out"] )
		transform["transform"]["translate"].setValue( imath.V2f( 2.2 ) )

		with GafferTest.TestRunner.PerformanceScope() :
			GafferImageTest.processTiles( transform["out"] )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testDownsizingPerformance( self ) :

		checker = GafferImage.Checkerboard()
		checker["format"].setValue( GafferImage.Format( 3000, 3000 ) )

		transform = GafferImage.ImageTransform()
		transform["in"].setInput( checker["out"] )
		transform["transform"]["scale"].setValue( imath.V2f( 0.1 ) )

		with GafferTest.TestRunner.PerformanceScope() :
			GafferImageTest.processTiles( transform["out"] )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testUpsizingPerformance( self ) :

		checker = GafferImage.Checkerboard()
		checker["format"].setValue( GafferImage.Format( 1000, 1000 ) )

		transform = GafferImage.ImageTransform()
		transform["in"].setInput( checker["out"] )
		transform["transform"]["scale"].setValue( imath.V2f( 3 ) )

		with GafferTest.TestRunner.PerformanceScope() :
			GafferImageTest.processTiles( transform["out"] )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testRotationAndScalingPerformance( self ) :

		checker = GafferImage.Checkerboard()
		checker["format"].setValue( GafferImage.Format( 3000, 3000 ) )

		transform = GafferImage.ImageTransform()
		transform["in"].setInput( checker["out"] )
		transform["transform"]["pivot"].setValue( imath.V2f( 1500 ) )
		transform["transform"]["rotate"].setValue( 2.5 )
		transform["transform"]["scale"].setValue( imath.V2f( 0.75 ) )

		with GafferTest.TestRunner.PerformanceScope() :
			GafferImageTest.processTiles( transform["out"] )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testConcatenationPerformance1( self ) :

		checker = GafferImage.Checkerboard()
		checker["format"].setValue( GafferImage.Format( 3000, 3000 ) )

		transform1 = GafferImage.ImageTransform( "Transform1" )
		transform1["in"].setInput( checker["out"] )
		transform1["transform"]["pivot"].setValue( imath.V2f( 1500 ) )
		transform1["transform"]["rotate"].setValue( 2.5 )

		transform2 = GafferImage.ImageTransform( "Transform2" )
		transform2["in"].setInput( transform1["out"] )
		transform2["transform"]["translate"].setValue( imath.V2f( 10 ) )

		with GafferTest.TestRunner.PerformanceScope() :
			GafferImageTest.processTiles( transform2["out"] )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testConcatenationPerformance2( self ) :

		checker = GafferImage.Checkerboard()
		checker["format"].setValue( GafferImage.Format( 3000, 3000 ) )

		transform1 = GafferImage.ImageTransform( "Transform1" )
		transform1["in"].setInput( checker["out"] )
		transform1["transform"]["pivot"].setValue( imath.V2f( 1500 ) )
		transform1["transform"]["rotate"].setValue( 2.5 )
		transform1["transform"]["scale"].setValue( imath.V2f( 1.1 ) )

		transform2 = GafferImage.ImageTransform( "Transform2" )
		transform2["in"].setInput( transform1["out"] )
		transform2["transform"]["translate"].setValue( imath.V2f( 10 ) )

		with GafferTest.TestRunner.PerformanceScope() :
			GafferImageTest.processTiles( transform2["out"] )

	def testOutTransform( self ) :

		t1 = GafferImage.ImageTransform()
		t2 = GafferImage.ImageTransform()

		t1["transform"]["scale"]["x"].setValue( .5 )
		t2["transform"]["scale"]["x"].setValue( 2 )

		self.assertNotEqual( t2["__outTransform"].getValue(), imath.M33f() )

		t2["in"].setInput( t1["out"] )

		self.assertEqual( t2["__outTransform"].getValue(), imath.M33f() )

	def testNoContextLeakage( self ) :

		c = GafferImage.Constant()

		t1 = GafferImage.ImageTransform()
		t1["in"].setInput( c["out"] )

		t2 = GafferImage.ImageTransform()
		t2["in"].setInput( t1["out"] )

		with Gaffer.ContextMonitor( root = c ) as cm :
			self.assertImagesEqual( t2["out"], t2["out"] )

		self.assertEqual(
			set( cm.combinedStatistics().variableNames() ),
			{ "frame", "framesPerSecond", "image:channelName", "image:tileOrigin" },
		)

	def testMatrixPlugConnection( self ) :

		t1 = GafferImage.ImageTransform()
		t2 = GafferImage.ImageTransform()
		t2["in"].setInput( t1["out"] )
		self.assertTrue( t2["__inTransform"].getInput() == t1["__outTransform"] )

		t2["in"].setInput( None )
		self.assertFalse( t2["__inTransform"].getInput() == t1["__outTransform"] )

	def testMatrixConnectionNotSerialised( self ) :

		s = Gaffer.ScriptNode()
		s["t1"] = GafferImage.ImageTransform()
		s["t2"] = GafferImage.ImageTransform()
		s["t2"]["in"].setInput( s["t1"]["out"] )

		self.assertEqual( s.serialise().count( "setInput" ), 1 )

	def testConcatenation( self ) :

		# Identical transformation chains, but one
		# with concatenation broken by a Blur node.
		#
		#        checker
		#          |
		#    deleteChannels
		#          /\
		#         /  \
		#       tc1  t1
		#        |    |
		#       tc2  blur
		#             |
		#            t2

		checker = GafferImage.Checkerboard()
		checker["format"].setValue( GafferImage.Format( 200, 200 ) )

		deleteChannels = GafferImage.DeleteChannels()
		deleteChannels["in"].setInput( checker["out"] )
		deleteChannels["channels"].setValue( "A" )

		tc1 = GafferImage.ImageTransform()
		tc1["in"].setInput( deleteChannels["out"] )
		tc1["filter"].setValue( "gaussian" )

		tc2 = GafferImage.ImageTransform()
		tc2["in"].setInput( tc1["out"] )
		tc2["filter"].setInput( tc1["filter"] )

		t1 = GafferImage.ImageTransform()
		t1["in"].setInput( deleteChannels["out"] )
		t1["transform"].setInput( tc1["transform"] )
		t1["filter"].setInput( tc1["filter"] )

		blur = GafferImage.Blur()
		blur["in"].setInput( t1["out"] )

		t2 = GafferImage.ImageTransform()
		t2["in"].setInput( blur["out"] )
		t2["transform"].setInput( tc2["transform"] )
		t2["filter"].setInput( tc1["filter"] )

		# The blur doesn't do anything except
		# break concatentation. Check that tc2
		# is practically identical to t2 for
		# a range of transforms.

		for i in range( 0, 10 ) :

			random.seed( i )

			translate1 = imath.V2f( random.uniform( -100, 100 ), random.uniform( -100, 100 ) )
			rotate1 = random.uniform( -360, 360 )
			scale1 = imath.V2f( random.uniform( -2, 2 ), random.uniform( -2, 2 ) )

			tc1["transform"]["translate"].setValue( translate1 )
			tc1["transform"]["rotate"].setValue( rotate1 )
			tc1["transform"]["scale"].setValue( scale1 )

			translate2 = imath.V2f( random.uniform( -100, 100 ), random.uniform( -100, 100 ) )
			rotate2 = random.uniform( -360, 360 )
			scale2 = imath.V2f( random.uniform( -2, 2 ), random.uniform( -2, 2 ) )

			tc2["transform"]["translate"].setValue( translate2 )
			tc2["transform"]["rotate"].setValue( rotate2 )
			tc2["transform"]["scale"].setValue( scale2 )

			# The `maxDifference` here is surprisingly high, but visual checks
			# show that it is legitimate : differences in filtering are that great.
			# The threshold is still significantly lower than the differences between
			# checker tiles, so does guarantee that tiles aren't getting out of alignment.
			self.assertImagesEqual( tc2["out"], t2["out"], maxDifference = 0.17, ignoreDataWindow = True )

	def testDisabledAndNonConcatenating( self ) :

		checker = GafferImage.Checkerboard()
		checker["format"].setValue( GafferImage.Format( 200, 200 ) )

		t1 = GafferImage.ImageTransform()
		t1["in"].setInput( checker["out"] )
		t1["transform"]["translate"]["x"].setValue( 10 )

		t2 = GafferImage.ImageTransform()
		t2["in"].setInput( t1["out"] )
		t2["transform"]["translate"]["x"].setValue( 10 )

		t3 = GafferImage.ImageTransform()
		t3["in"].setInput( t2["out"] )
		t3["transform"]["translate"]["x"].setValue( 10 )

		self.assertEqual( t3["out"]["dataWindow"].getValue().min().x, 30 )

		t2["concatenate"].setValue( False )
		self.assertEqual( t3["out"]["dataWindow"].getValue().min().x, 30 )

		t2["enabled"].setValue( False )
		self.assertEqual( t3["out"]["dataWindow"].getValue().min().x, 20 )

if __name__ == "__main__":
	unittest.main()
