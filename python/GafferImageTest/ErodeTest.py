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
import unittest
import imath

import IECore

import Gaffer
import GafferTest
import GafferImage
import GafferImageTest
import OpenImageIO

class ErodeTest( GafferImageTest.ImageTestCase ) :

	def testPassThrough( self ) :

		c = GafferImage.Constant()

		m = GafferImage.Erode()
		m["in"].setInput( c["out"] )
		m["radius"].setValue( imath.V2i( 0 ) )

		self.assertEqual( GafferImage.ImageAlgo.imageHash( c["out"] ), GafferImage.ImageAlgo.imageHash( m["out"] ) )
		self.assertImagesEqual( c["out"], m["out"] )

	def testExpandDataWindow( self ) :

		c = GafferImage.Constant()

		m = GafferImage.Erode()
		m["in"].setInput( c["out"] )
		m["radius"].setValue( imath.V2i( 1 ) )

		self.assertEqual( m["out"]["dataWindow"].getValue(), c["out"]["dataWindow"].getValue() )

		m["expandDataWindow"].setValue( True )

		self.assertEqual( m["out"]["dataWindow"].getValue().min(), c["out"]["dataWindow"].getValue().min() - imath.V2i( 1 ) )
		self.assertEqual( m["out"]["dataWindow"].getValue().max(), c["out"]["dataWindow"].getValue().max() + imath.V2i( 1 ) )

	def testFilter( self ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.imagesPath() / "radial.exr" )

		m = GafferImage.Erode()
		m["in"].setInput( r["out"] )
		self.assertImagesEqual( m["out"], r["out"] )

		m["radius"].setValue( imath.V2i( 8 ) )
		m["boundingMode"].setValue( GafferImage.Sampler.BoundingMode.Clamp )

		dataWindow = m["out"]["dataWindow"].getValue()
		s = GafferImage.ImageStats()
		s["in"].setInput( m["out"] )
		s["area"].setValue( dataWindow )

		self.assertEqual( s["max"].getValue(), imath.Color4f( 0, 0, 0, 0 ) )

	def testDriverChannel( self ) :

		rRaw = GafferImage.ImageReader()
		rRaw["fileName"].setValue( self.imagesPath() / "circles.exr" )

		r = GafferImage.Grade()
		r["in"].setInput( rRaw["out"] )
		# Trim off the noise in the blacks so that areas with no visible color are actually flat
		r["blackPoint"].setValue( imath.Color4f( 0.03 ) )


		masterErode = GafferImage.Erode()
		masterErode["in"].setInput( r["out"] )
		masterErode["radius"].setValue( imath.V2i( 2 ) )

		masterErode["masterChannel"].setValue( "G" )

		expected = GafferImage.ImageReader()
		expected["fileName"].setValue( self.imagesPath() / "circlesGreenErode.exr" )

		# Note that in this expected image, the green channel is nicely medianed, and red and blue are completely
		# unchanged in areas where there is no green.  In areas where red and blue overlap with a noisy green,
		# they get a bit scrambled.  This is why in practice, you would use something like luminance, rather
		# than just the green channel
		self.assertImagesEqual( masterErode["out"], expected["out"], ignoreMetadata = True, maxDifference=0.0005 )


		defaultErode = GafferImage.Erode()
		defaultErode["in"].setInput( r["out"] )
		defaultErode["radius"].setValue( imath.V2i( 2 ) )

		masterErodeSingleChannel = GafferImage.DeleteChannels()
		masterErodeSingleChannel["in"].setInput( masterErode["out"] )
		masterErodeSingleChannel["mode"].setValue( GafferImage.DeleteChannels.Mode.Keep )

		defaultErodeSingleChannel = GafferImage.DeleteChannels()
		defaultErodeSingleChannel["in"].setInput( defaultErode["out"] )
		defaultErodeSingleChannel["mode"].setValue( GafferImage.DeleteChannels.Mode.Keep )

		for c in [ "R", "G", "B" ]:
			masterErode["masterChannel"].setValue( c )
			masterErodeSingleChannel["channels"].setValue( c )
			defaultErodeSingleChannel["channels"].setValue( c )

			# When we look at just the channel being used as the master, it matches a default median not using
			# a master
			self.assertImagesEqual( masterErodeSingleChannel["out"], defaultErodeSingleChannel["out"] )

	def writeRefErodeFiltered( self, imageBuf, rad, fileName ):
		filtered = OpenImageIO.ImageBufAlgo.erode( imageBuf, 1 + 2 * rad.x, 1 + 2 * rad.y )
		filtered.write( str( self.temporaryDirectory() / fileName ) )

	def testAgainstOIIO( self ):
		pureNoise = OpenImageIO.ImageBufAlgo.noise( "gaussian", 0, 1, roi = OpenImageIO.ROI(0, 320, 0, 240, 0, 1, 0, 3) )
		pureNoise.write( str( self.temporaryDirectory() / "pureNoise.exr" ) )
		self.writeRefErodeFiltered( pureNoise, imath.V2i( 1 ), "pureNoiseErode1.exr" )
		self.writeRefErodeFiltered( pureNoise, imath.V2i( 4 ), "pureNoiseErode4.exr" )
		self.writeRefErodeFiltered( pureNoise, imath.V2i( 3, 7 ), "pureNoiseErode3x7.exr" )

		diagonalGradient = {
			"topleft" : (1,1,1), "bottomright" : (0,0,0),
			"bottomleft" : (0.5,0.5,0.5), "topright" : (0.5, 0.5, 0.5)
		}

		gradWithNoise = OpenImageIO.ImageBufAlgo.fill(
			roi = OpenImageIO.ROI(0, 320, 0, 240, 0, 1, 0, 3), **diagonalGradient
		)
		OpenImageIO.ImageBufAlgo.noise( gradWithNoise, "gaussian", 0, 1 )
		gradWithNoise.write( str( self.temporaryDirectory() / "gradWithNoise.exr" ) )
		self.writeRefErodeFiltered( gradWithNoise, imath.V2i( 1 ), "gradWithNoiseErode1.exr" )
		self.writeRefErodeFiltered( gradWithNoise, imath.V2i( 3 ), "gradWithNoiseErode3.exr" )
		self.writeRefErodeFiltered( gradWithNoise, imath.V2i( 1, 7 ), "gradWithNoiseErode1x7.exr" )
		self.writeRefErodeFiltered( gradWithNoise, imath.V2i( 7, 1 ), "gradWithNoiseErode7x1.exr" )

		scanlines = OpenImageIO.ImageBufAlgo.noise("gaussian", 0.5, 2, roi = OpenImageIO.ROI(0, 1, 0, 256, 0, 1, 0, 3))
		scanlines = OpenImageIO.ImageBufAlgo.resize( scanlines, roi = OpenImageIO.ROI(0, 8, 0, 256, 0, 1, 0, 3))
		scanlines.write( str( self.temporaryDirectory() / "scanlines.exr" ) )
		self.writeRefErodeFiltered( scanlines, imath.V2i( 3 ), "scanlinesErode3.exr" )

		scanlinesWithNoise = OpenImageIO.ImageBuf()
		scanlinesWithNoise.copy( scanlines )
		OpenImageIO.ImageBufAlgo.noise( scanlinesWithNoise, "gaussian", 0.5, 1 )
		scanlinesWithNoise = OpenImageIO.ImageBufAlgo.clamp( scanlinesWithNoise, [ 0, 0, 0 ], [ 1, 1, 1 ] )
		scanlinesWithNoise.write( str( self.temporaryDirectory() / "scanlinesWithNoise.exr" ) )
		self.writeRefErodeFiltered( scanlinesWithNoise, imath.V2i( 3 ), "scanlinesWithNoiseErode3.exr" )

		oneExceptional = OpenImageIO.ImageBufAlgo.fill(
			roi = OpenImageIO.ROI(0, 8, 0, 8, 0, 1, 0, 3), **diagonalGradient
		)
		oneExceptional.setpixel( 2, 2, 0, ( -float( "inf" ), float( "nan" ), float( "inf") ) )
		oneExceptional.write( str( self.temporaryDirectory() / "oneExceptional.exr" ) )

		# OIIO can't deal with NaNs - just use the channel with negative infinity as a replacement.
		# Gaffer will treat NaN like a regative infinity
		self.writeRefErodeFiltered( oneExceptional, imath.V2i( 2 ), "oneExceptionalErode2.exr" )

		halfExceptional = OpenImageIO.ImageBufAlgo.fill(
			roi = OpenImageIO.ROI(0, 8, 0, 8, 0, 1, 0, 3), **diagonalGradient
		)
		for y in range( 8 ):
			for x in range( 8 ):
				if (x % 2) == (y % 2):
					halfExceptional.setpixel( x, y, 0, [ -float( "inf" ), float( "nan" ), float( "inf") ] )
		halfExceptional.write( str( self.temporaryDirectory() / "halfExceptional.exr" ) )
		self.writeRefErodeFiltered( halfExceptional, imath.V2i( 2 ), "halfExceptionalErode2.exr" )

		mostExceptional = OpenImageIO.ImageBufAlgo.fill(
			[ -float( "inf" ), float( "nan" ), float( "inf") ],
			roi = OpenImageIO.ROI(0, 8, 0, 8, 0, 1, 0, 3)
		)
		mostExceptional.setpixel( 2, 2, 0, [ 0.1, 0.2, 0.3 ] )
		mostExceptional.write( str( self.temporaryDirectory() / "mostExceptional.exr" ) )
		self.writeRefErodeFiltered( mostExceptional, imath.V2i( 2 ), "mostExceptionalErode2.exr" )

		mostExceptionalDriverChannelRef = OpenImageIO.ImageBufAlgo.fill(
			[ 0.1, 0.2, 0.3 ], roi = OpenImageIO.ROI(0, 8, 0, 8, 0, 1, 0, 3)
		)
		for y in range( 8 ):
			for x in range( 8 ):
				if x > 4 or y > 4 :
					mostExceptionalDriverChannelRef.setpixel( x, y, 0, [ -float( "inf" ), float( "nan" ), float( "inf") ] )
		mostExceptionalDriverChannelRef.write( str( self.temporaryDirectory() / "mostExceptionalDriverChannelRef.exr" ) )

		noisyBlobs = OpenImageIO.ImageBufAlgo.noise("gaussian", 0.5, 1, roi = OpenImageIO.ROI(0, 8, 0, 8, 0, 1, 0, 1))
		noisyBlobs = OpenImageIO.ImageBufAlgo.resize( noisyBlobs, roi = OpenImageIO.ROI(0, 256, 0, 256, 0, 1, 0, 1))
		OpenImageIO.ImageBufAlgo.noise(noisyBlobs, "gaussian", 0, 0.5)
		noisyBlobs.write( str( self.temporaryDirectory() / "noisyBlobs.exr" ) )
		self.writeRefErodeFiltered( noisyBlobs, imath.V2i( 1 ), "noisyBlobsErode1.exr" )
		self.writeRefErodeFiltered( noisyBlobs, imath.V2i( 4 ), "noisyBlobsErode4.exr" )
		self.writeRefErodeFiltered( noisyBlobs, imath.V2i( 72, 67 ), "noisyBlobsErode72x67.exr" )

		imageReader = GafferImage.ImageReader()
		erode = GafferImage.Erode()
		erode["in"].setInput( imageReader["out"] )
		erode['boundingMode'].setValue( GafferImage.Sampler.BoundingMode.Clamp )
		refReader = GafferImage.ImageReader()

		# For one exceptional case, we need to clamp our result to match OIIO
		erodeClampSource = GafferImage.Constant()
		erodeClampSource['format'].setValue( GafferImage.Format( 8, 8 ) )
		erodeClampSource['color'].setValue( imath.Color4f( 3.403e38 ) )

		erodeClampChannels = GafferImage.DeleteChannels()
		erodeClampChannels["in"].setInput( erodeClampSource["out"] )
		erodeClampChannels["channels"].setValue( "A" )

		erodeClamp = GafferImage.Merge()
		erodeClamp["operation"].setValue( GafferImage.Merge.Operation.Min )
		erodeClamp["in"][0].setInput( erode["out"] )
		erodeClamp["in"][1].setInput( erodeClampChannels["out"] )


		driverShuffle = GafferImage.Shuffle()
		driverShuffle["in"].setInput( imageReader["out"] )
		driverShuffle["channels"].addChild( GafferImage.Shuffle.ChannelPlug( "driver", "R" ) )
		driverShuffle["channels"].addChild( GafferImage.Shuffle.ChannelPlug( "driven", "R" ) )

		driverDelete = GafferImage.DeleteChannels()
		driverDelete["in"].setInput( driverShuffle["out"] )
		driverDelete["mode"].setValue( GafferImage.DeleteChannels.Mode.Keep )
		driverDelete["channels"].setValue( 'driven driver' )

		driverErode = GafferImage.Erode()
		driverErode["in"].setInput( driverDelete["out"] )
		driverErode['boundingMode'].setValue( GafferImage.Sampler.BoundingMode.Clamp )


		refDriverShuffle = GafferImage.Shuffle()
		refDriverShuffle["in"].setInput( refReader["out"] )
		refDriverShuffle["channels"].addChild( GafferImage.Shuffle.ChannelPlug( "driver", "R" ) )
		refDriverShuffle["channels"].addChild( GafferImage.Shuffle.ChannelPlug( "driven", "R" ) )

		refDriverDelete = GafferImage.DeleteChannels()
		refDriverDelete["in"].setInput( refDriverShuffle["out"] )
		refDriverDelete["mode"].setValue( GafferImage.DeleteChannels.Mode.Keep )
		refDriverDelete["channels"].setValue( 'driven driver' )

		for source, rad, ref in [
			( "pureNoise.exr", imath.V2i( 1 ), "pureNoiseErode1.exr" ),
			( "pureNoise.exr", imath.V2i( 4 ), "pureNoiseErode4.exr" ),
			( "pureNoise.exr", imath.V2i( 3, 7 ), "pureNoiseErode3x7.exr" ),
			( "gradWithNoise.exr", imath.V2i( 1 ), "gradWithNoiseErode1.exr" ),
			( "gradWithNoise.exr", imath.V2i( 3 ), "gradWithNoiseErode3.exr" ),
			( "gradWithNoise.exr", imath.V2i( 1, 7 ), "gradWithNoiseErode1x7.exr" ),
			( "gradWithNoise.exr", imath.V2i( 7, 1 ), "gradWithNoiseErode7x1.exr" ),
			( "scanlines.exr", imath.V2i( 3 ), "scanlinesErode3.exr" ),
			( "scanlinesWithNoise.exr", imath.V2i( 3 ), "scanlinesWithNoiseErode3.exr" ),
			( "oneExceptional.exr", imath.V2i( 2 ), "oneExceptionalErode2.exr" ),
			( "halfExceptional.exr", imath.V2i( 2 ), "halfExceptionalErode2.exr" ),
			( "mostExceptional.exr", imath.V2i( 2 ), "mostExceptionalErode2.exr" ),
			( "noisyBlobs.exr", imath.V2i( 1 ), "noisyBlobsErode1.exr" ),
			( "noisyBlobs.exr", imath.V2i( 4 ), "noisyBlobsErode4.exr" ),
			( "noisyBlobs.exr", imath.V2i( 72, 67 ), "noisyBlobsErode72x67.exr" )
		] :
			imageReader["fileName"].setValue( self.temporaryDirectory() / source )
			refReader["fileName"].setValue( self.temporaryDirectory() / ref )
			with self.subTest( refFile = ref ):
				erode["radius"].setValue( rad )

				if source == "mostExceptional.exr":
					# OIIO has an arbitrary clamp on the maximum value output by erode, we can use a clamp
					# just to get the same values as OIIO for comparison purposes
					self.assertImagesEqual( erodeClamp["out"], refReader["out"], ignoreMetadata = True )
				else:
					self.assertImagesEqual( erode["out"], refReader["out"], ignoreMetadata = True )


			driverErode["radius"].setValue( rad )
			for channelName in imageReader["out"].channelNames():
				if ref == "mostExceptionalErode2.exr" and channelName in [ "G", "B" ]:
					# OIIO doesn't handle nans or infinities well, so we replace this with a manual reference file
					refReader["fileName"].setValue( self.temporaryDirectory() / "mostExceptionalDriverChannelRef.exr" )
				else:
					refReader["fileName"].setValue( self.temporaryDirectory() / ref )

				with self.subTest( refFile = ref, driverChannel = channelName ):
					for channelPlug in [ i["in"] for i in driverShuffle["channels"].children() + refDriverShuffle["channels"].children() ] + [ driverErode["masterChannel"] ]:
						channelPlug.setValue( channelName )

					self.assertImagesEqual( driverErode["out"], refDriverDelete["out"], ignoreMetadata = True )

		# For the last, large radius test, shift the data window around to get more coverage
		# of different tile locations, including negative tile origins

		offset = GafferImage.Offset()
		offset["in"].setInput( imageReader["out"] )

		erode["in"].setInput( offset["out"] )

		reverseOffset = GafferImage.Offset()
		reverseOffset["in"].setInput( erode["out"] )

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

		erode = GafferImage.Erode()
		erode["in"].setInput( imageReader["out"] )
		erode["radius"].setValue( imath.V2i( 128 ) )

		with GafferTest.TestRunner.PerformanceScope() :
			GafferImageTest.processTiles( erode["out"] )

if __name__ == "__main__":
	unittest.main()
