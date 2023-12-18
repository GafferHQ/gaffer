##########################################################################
#
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
import time
import unittest
import imath
import OpenImageIO

import IECore

import Gaffer
import GafferTest
import GafferImage
import GafferImageTest

class MedianTest( GafferImageTest.ImageTestCase ) :

	def testPassThrough( self ) :

		c = GafferImage.Constant()

		m = GafferImage.Median()
		m["in"].setInput( c["out"] )
		m["radius"].setValue( imath.V2i( 0 ) )

		self.assertEqual( GafferImage.ImageAlgo.imageHash( c["out"] ), GafferImage.ImageAlgo.imageHash( m["out"] ) )
		self.assertImagesEqual( c["out"], m["out"] )

	def testExpandDataWindow( self ) :

		c = GafferImage.Constant()

		m = GafferImage.Median()
		m["in"].setInput( c["out"] )
		m["radius"].setValue( imath.V2i( 1 ) )

		self.assertEqual( m["out"]["dataWindow"].getValue(), c["out"]["dataWindow"].getValue() )

		m["expandDataWindow"].setValue( True )

		self.assertEqual( m["out"]["dataWindow"].getValue().min(), c["out"]["dataWindow"].getValue().min() - imath.V2i( 1 ) )
		self.assertEqual( m["out"]["dataWindow"].getValue().max(), c["out"]["dataWindow"].getValue().max() + imath.V2i( 1 ) )

	def testFilter( self ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.imagesPath() / "noisyRamp.exr" )

		m = GafferImage.Median()
		m["in"].setInput( r["out"] )
		self.assertImagesEqual( m["out"], r["out"] )

		m["radius"].setValue( imath.V2i( 1 ) )
		m["boundingMode"].setValue( GafferImage.Sampler.BoundingMode.Clamp )

		dataWindow = m["out"]["dataWindow"].getValue()
		s = GafferImage.Sampler( m["out"], "R", dataWindow )

		uStep = 1.0 / dataWindow.size().x
		uMin = 0.5 * uStep
		for y in range( dataWindow.min().y, dataWindow.max().y ) :
			for x in range( dataWindow.min().x, dataWindow.max().x ) :
				self.assertAlmostEqual( s.sample( x, y ), uMin + x * uStep, delta = 0.011 )

	def testDriverChannel( self ) :

		rRaw = GafferImage.ImageReader()
		rRaw["fileName"].setValue( self.imagesPath() / "circles.exr" )

		r = GafferImage.Grade()
		r["in"].setInput( rRaw["out"] )
		# Trim off the noise in the blacks so that areas with no visible color are actually flat
		r["blackPoint"].setValue( imath.Color4f( 0.03 ) )


		masterMedian = GafferImage.Median()
		masterMedian["in"].setInput( r["out"] )
		masterMedian["radius"].setValue( imath.V2i( 2 ) )

		masterMedian["masterChannel"].setValue( "G" )

		expected = GafferImage.ImageReader()
		expected["fileName"].setValue( self.imagesPath() / "circlesGreenMedian.exr" )

		# Note that in this expected image, the green channel is nicely medianed, and red and blue are completely
		# unchanged in areas where there is no green.  In areas where red and blue overlap with a noisy green,
		# they get a bit scrambled.  This is why in practice, you would use something like luminance, rather
		# than just the green channel
		self.assertImagesEqual( masterMedian["out"], expected["out"], ignoreMetadata = True, maxDifference=0.0005 )


		defaultMedian = GafferImage.Median()
		defaultMedian["in"].setInput( r["out"] )
		defaultMedian["radius"].setValue( imath.V2i( 2 ) )

		masterMedianSingleChannel = GafferImage.DeleteChannels()
		masterMedianSingleChannel["in"].setInput( masterMedian["out"] )
		masterMedianSingleChannel["mode"].setValue( GafferImage.DeleteChannels.Mode.Keep )

		defaultMedianSingleChannel = GafferImage.DeleteChannels()
		defaultMedianSingleChannel["in"].setInput( defaultMedian["out"] )
		defaultMedianSingleChannel["mode"].setValue( GafferImage.DeleteChannels.Mode.Keep )

		for c in [ "R", "G", "B" ]:
			masterMedian["masterChannel"].setValue( c )
			masterMedianSingleChannel["channels"].setValue( c )
			defaultMedianSingleChannel["channels"].setValue( c )

			# When we look at just the channel being used as the master, it matches a default median not using
			# a master
			self.assertImagesEqual( masterMedianSingleChannel["out"], defaultMedianSingleChannel["out"] )

	def testCancellation( self ) :

		script = Gaffer.ScriptNode()
		script["c"] = GafferImage.Constant()

		script["m"] = GafferImage.Median()
		script["m"]["in"].setInput( script["c"]["out"] )
		script["m"]["radius"].setValue( imath.V2i( 2000 ) )

		bt = Gaffer.ParallelAlgo.callOnBackgroundThread( script["m"]["out"], lambda : GafferImageTest.processTiles( script["m"]["out"] ) )
		# Give background tasks time to get into full swing
		time.sleep( 0.1 )

		# Check that we can cancel them in reasonable time
		acceptableCancellationDelay = 4.0 if GafferTest.inCI() else 0.25
		t = time.time()
		bt.cancelAndWait()
		self.assertLess( time.time() - t, acceptableCancellationDelay )

		# Check that we can do the same when using a master
		# channel.
		script["m"]["masterChannel"].setValue( "R" )

		bt = Gaffer.ParallelAlgo.callOnBackgroundThread( script["m"]["out"], lambda : GafferImageTest.processTiles( script["m"]["out"] ) )
		time.sleep( 0.1 )

		t = time.time()
		bt.cancelAndWait()
		self.assertLess( time.time() - t, acceptableCancellationDelay )

	def writeRefMedianFiltered( self, imageBuf, rad, fileName ):
		# OIIO has a different edge behaviour to us - they reduce the size of the filter region
		# as they get closer to the edge. In order to get matching behaviour, pad out the image
		# with black before taking the median
		roi = imageBuf.roi
		padded = OpenImageIO.ImageBufAlgo.crop( imageBuf,
			OpenImageIO.ROI(-rad.x, roi.xend + rad.x, -rad.y, roi.yend + rad.y, 0, 1, 0, roi.chend)
		)
		filtered = OpenImageIO.ImageBufAlgo.median_filter( padded, 1 + 2 * rad.x, 1 + 2 * rad.y )
		cropped = OpenImageIO.ImageBufAlgo.crop( filtered, roi )
		cropped.write( str( self.temporaryDirectory() / fileName ) )

	def testAgainstOIIO( self ):
		pureNoise = OpenImageIO.ImageBufAlgo.noise( "gaussian", 0, 1, roi = OpenImageIO.ROI(0, 320, 0, 240, 0, 1, 0, 3) )
		pureNoise.write( str( self.temporaryDirectory() / "pureNoise.exr" ) )
		self.writeRefMedianFiltered( pureNoise, imath.V2i( 1 ), "pureNoiseMed1.exr" )
		self.writeRefMedianFiltered( pureNoise, imath.V2i( 4 ), "pureNoiseMed4.exr" )
		self.writeRefMedianFiltered( pureNoise, imath.V2i( 3, 7 ), "pureNoiseMed3x7.exr" )

		diagonalGradient = {
			"topleft" : (1,1,1), "bottomright" : (0,0,0),
			"bottomleft" : (0.5,0.5,0.5), "topright" : (0.5, 0.5, 0.5)
		}

		gradWithNoise = OpenImageIO.ImageBufAlgo.fill(
			roi = OpenImageIO.ROI(0, 320, 0, 240, 0, 1, 0, 3), **diagonalGradient
		)
		OpenImageIO.ImageBufAlgo.noise( gradWithNoise, "gaussian", 0, 1 )
		gradWithNoise.write( str( self.temporaryDirectory() / "gradWithNoise.exr" ) )
		self.writeRefMedianFiltered( gradWithNoise, imath.V2i( 1 ), "gradWithNoiseMed1.exr" )
		self.writeRefMedianFiltered( gradWithNoise, imath.V2i( 3 ), "gradWithNoiseMed3.exr" )
		self.writeRefMedianFiltered( gradWithNoise, imath.V2i( 1, 7 ), "gradWithNoiseMed1x7.exr" )
		self.writeRefMedianFiltered( gradWithNoise, imath.V2i( 7, 1 ), "gradWithNoiseMed7x1.exr" )

		# Exercise special cases with the fast median filter where you get a scanline that is all high
		scanlines = OpenImageIO.ImageBufAlgo.noise("gaussian", 0.5, 2, roi = OpenImageIO.ROI(0, 1, 0, 256, 0, 1, 0, 3))
		scanlines = OpenImageIO.ImageBufAlgo.resize( scanlines, roi = OpenImageIO.ROI(0, 8, 0, 256, 0, 1, 0, 3))
		scanlines.write( str( self.temporaryDirectory() / "scanlines.exr" ) )
		self.writeRefMedianFiltered( scanlines, imath.V2i( 3 ), "scanlinesMed3.exr" )

		scanlinesWithNoise = OpenImageIO.ImageBuf()
		scanlinesWithNoise.copy( scanlines )
		OpenImageIO.ImageBufAlgo.noise( scanlinesWithNoise, "gaussian", 0.5, 1 )
		scanlinesWithNoise = OpenImageIO.ImageBufAlgo.clamp( scanlinesWithNoise, [ 0, 0, 0 ], [ 1, 1, 1 ] )
		scanlinesWithNoise.write( str( self.temporaryDirectory() / "scanlinesWithNoise.exr" ) )
		self.writeRefMedianFiltered( scanlinesWithNoise, imath.V2i( 3 ), "scanlinesWithNoiseMed3.exr" )

		oneExceptional = OpenImageIO.ImageBufAlgo.fill(
			roi = OpenImageIO.ROI(0, 8, 0, 8, 0, 1, 0, 3), **diagonalGradient
		)

		oneExceptional.setpixel( 2, 2, 0, ( -float( "inf" ), float( "nan" ), float( "inf") ) )
		oneExceptional.write( str( self.temporaryDirectory() / "oneExceptional.exr" ) )

		# OIIO can't deal with NaNs - just use the channel with negative infinity as a replacement.
		# Gaffer will treat NaN like a regative infinity
		oneExceptionalNoNan = OpenImageIO.ImageBufAlgo.channels( oneExceptional, ( 0, 0, 2 ), newchannelnames = ("R", "G", "B" ) )
		self.writeRefMedianFiltered( oneExceptionalNoNan, imath.V2i( 2 ), "oneExceptionalMed2.exr" )

		halfExceptional = OpenImageIO.ImageBufAlgo.fill(
			roi = OpenImageIO.ROI(0, 8, 0, 8, 0, 1, 0, 3), **diagonalGradient
		)
		for y in range( 8 ):
			for x in range( 8 ):
				if (x % 2) == (y % 2):
					halfExceptional.setpixel( x, y, 0, [ -float( "inf" ), float( "nan" ), float( "inf") ] )
		halfExceptional.write( str( self.temporaryDirectory() / "halfExceptional.exr" ) )
		halfExceptionalNoNan = OpenImageIO.ImageBufAlgo.channels( halfExceptional, ( 0, 0, 2 ), newchannelnames = ("R", "G", "B" ) )
		self.writeRefMedianFiltered( halfExceptionalNoNan, imath.V2i( 2 ), "halfExceptionalMed2.exr" )

		mostExceptional = OpenImageIO.ImageBufAlgo.fill(
			[ -float( "inf" ), float( "nan" ), float( "inf") ],
			roi = OpenImageIO.ROI(0, 8, 0, 8, 0, 1, 0, 3)
		)
		mostExceptional.setpixel( 2, 2, 0, [ 0.1, 0.2, 0.3 ] )
		mostExceptional.write( str( self.temporaryDirectory() / "mostExceptional.exr" ) )
		mostExceptionalNoNan = OpenImageIO.ImageBufAlgo.channels( mostExceptional, ( 0, 0, 2 ), newchannelnames = ("R", "G", "B" ) )
		self.writeRefMedianFiltered( mostExceptionalNoNan, imath.V2i( 2 ), "mostExceptionalMed2.exr" )

		# We can use OIIO to produce some good test images, but it appears that OIIO produces slightly different
		# results on Windows, so we instead use an image stored in the test images folder
		#noisyBlobs = OpenImageIO.ImageBufAlgo.noise("gaussian", 0.5, 1, roi = OpenImageIO.ROI(0, 8, 0, 8, 0, 1, 0, 1))
		#noisyBlobs = OpenImageIO.ImageBufAlgo.resize( noisyBlobs, roi = OpenImageIO.ROI(0, 256, 0, 256, 0, 1, 0, 1))
		#OpenImageIO.ImageBufAlgo.noise(noisyBlobs, "gaussian", 0, 0.5)
		#noisyBlobs.write( str( self.temporaryDirectory() / "noisyBlobs.exr" ) )
		noisyBlobs = OpenImageIO.ImageBuf( str( self.imagesPath() / "noisyBlobs.exr" ) )

		self.writeRefMedianFiltered( noisyBlobs, imath.V2i( 1 ), "noisyBlobsMed1.exr" )
		self.writeRefMedianFiltered( noisyBlobs, imath.V2i( 4 ), "noisyBlobsMed4.exr" )
		# We want at least one test for a large radius, but this takes over 20 seconds for OIIO to generate
		# using its naive algorithm, so instead we store this reference image in the repo
		# self.writeRefMedianFiltered( noisyBlobs, imath.V2i( 72, 67 ), "noisyBlobsMed72x67.exr" )

		imageReader = GafferImage.ImageReader()
		median = GafferImage.Median()
		median["in"].setInput( imageReader["out"] )
		refReader = GafferImage.ImageReader()

		driverShuffle = GafferImage.Shuffle()
		driverShuffle["in"].setInput( imageReader["out"] )
		driverShuffle["shuffles"].addChild( Gaffer.ShufflePlug( "R", "driver" ) )
		driverShuffle["shuffles"].addChild( Gaffer.ShufflePlug( "R", "driven" ) )

		driverDelete = GafferImage.DeleteChannels()
		driverDelete["in"].setInput( driverShuffle["out"] )
		driverDelete["mode"].setValue( GafferImage.DeleteChannels.Mode.Keep )
		driverDelete["channels"].setValue( 'driven driver' )

		driverMedian = GafferImage.Median()
		driverMedian["in"].setInput( driverDelete["out"] )

		refDriverShuffle = GafferImage.Shuffle()
		refDriverShuffle["in"].setInput( refReader["out"] )
		refDriverShuffle["shuffles"].addChild( Gaffer.ShufflePlug( "R", "driver" ) )
		refDriverShuffle["shuffles"].addChild( Gaffer.ShufflePlug( "R", "driven" ) )

		refDriverDelete = GafferImage.DeleteChannels()
		refDriverDelete["in"].setInput( refDriverShuffle["out"] )
		refDriverDelete["mode"].setValue( GafferImage.DeleteChannels.Mode.Keep )
		refDriverDelete["channels"].setValue( 'driven driver' )

		for source, rad, ref in [
			( "pureNoise.exr", imath.V2i( 1 ), "pureNoiseMed1.exr" ),
			( "pureNoise.exr", imath.V2i( 4 ), "pureNoiseMed4.exr" ),
			( "pureNoise.exr", imath.V2i( 3, 7 ), "pureNoiseMed3x7.exr" ),
			( "gradWithNoise.exr", imath.V2i( 1 ), "gradWithNoiseMed1.exr" ),
			( "gradWithNoise.exr", imath.V2i( 3 ), "gradWithNoiseMed3.exr" ),
			( "gradWithNoise.exr", imath.V2i( 1, 7 ), "gradWithNoiseMed1x7.exr" ),
			( "gradWithNoise.exr", imath.V2i( 7, 1 ), "gradWithNoiseMed7x1.exr" ),
			( "scanlines.exr", imath.V2i( 3 ), "scanlinesMed3.exr" ),
			( "scanlinesWithNoise.exr", imath.V2i( 3 ), "scanlinesWithNoiseMed3.exr" ),
			( "oneExceptional.exr", imath.V2i( 2 ), "oneExceptionalMed2.exr" ),
			( "halfExceptional.exr", imath.V2i( 2 ), "halfExceptionalMed2.exr" ),
			( "mostExceptional.exr", imath.V2i( 2 ), "mostExceptionalMed2.exr" ),
			( "noisyBlobs.exr", imath.V2i( 1 ), "noisyBlobsMed1.exr" ),
			( "noisyBlobs.exr", imath.V2i( 4 ), "noisyBlobsMed4.exr" )
		] :
			if source == "noisyBlobs.exr":
				imageReader["fileName"].setValue( self.imagesPath() / source )
			else:
				imageReader["fileName"].setValue( self.temporaryDirectory() / source )
			refReader["fileName"].setValue( self.temporaryDirectory() / ref )
			with self.subTest( refFile = ref ):
				median["radius"].setValue( rad )
				self.assertImagesEqual( median["out"], refReader["out"], ignoreMetadata = True )


			driverMedian["radius"].setValue( rad )
			for channelName in imageReader["out"].channelNames():
				if ( ref == "halfExceptionalMed2.exr" or ref == "mostExceptionalMed2.exr" ) and channelName == "G":
					# We usually don't pass through NaNs, but when we're using a driver channel, we just
					# take the channel value from the corresponding position in the input. This doesn't
					# really correspond to anything OIIO does, and it's a rare corner case. I think
					# the current behaviour is correct, but we just skip the test
					continue

				with self.subTest( refFile = ref, driverChannel = channelName ):
					for channelPlug in [ i["source"] for i in driverShuffle["shuffles"].children() + refDriverShuffle["shuffles"].children() ] + [ driverMedian["masterChannel"] ]:
						channelPlug.setValue( channelName )
					self.assertImagesEqual( driverMedian["out"], refDriverDelete["out"], ignoreMetadata = True )

		median["radius"].setValue( imath.V2i( 72, 67 ) )
		refReader["fileName"].setValue( self.imagesPath() / "noisyBlobsMed72x67.exr" )
		self.assertImagesEqual( median["out"], refReader["out"], ignoreMetadata = True )

		# Shift the data window around to get more coverage of different tile locations,
		# including negative tile origins

		offset = GafferImage.Offset()
		offset["in"].setInput( imageReader["out"] )

		median["in"].setInput( offset["out"] )

		reverseOffset = GafferImage.Offset()
		reverseOffset["in"].setInput( median["out"] )

		offset["offset"].setValue( imath.V2i( 107, 136 ) )
		reverseOffset["offset"].setValue( imath.V2i( -107, -136 ) )
		self.assertImagesEqual( reverseOffset["out"], refReader["out"], ignoreMetadata = True )

		offset["offset"].setValue( imath.V2i( -107, -136 ) )
		reverseOffset["offset"].setValue( imath.V2i( 107, 136 ) )
		self.assertImagesEqual( reverseOffset["out"], refReader["out"], ignoreMetadata = True )

		offset["offset"].setValue( imath.V2i( -1070, 1360 ) )
		reverseOffset["offset"].setValue( imath.V2i( 1070, -1360 ) )
		self.assertImagesEqual( reverseOffset["out"], refReader["out"], ignoreMetadata = True )

	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 1 )
	def testPerf( self ) :

		imageReader = GafferImage.ImageReader()
		imageReader["fileName"].setValue( self.imagesPath() / 'deepMergeReference.exr' )

		GafferImageTest.processTiles( imageReader["out"] )

		median = GafferImage.Median()
		median["in"].setInput( imageReader["out"] )
		median["radius"].setValue( imath.V2i( 128 ) )

		with GafferTest.TestRunner.PerformanceScope() :
			GafferImageTest.processTiles( median["out"] )

if __name__ == "__main__":
	unittest.main()
