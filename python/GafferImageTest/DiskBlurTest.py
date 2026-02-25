##########################################################################
#
#  Copyright (c) 2025, Image Engine Design Inc. All rights reserved.
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
import random

import imath

import IECore

import Gaffer
import GafferTest
import GafferImage
import GafferImageTest
import OpenImageIO

class DiskBlurTest( GafferImageTest.ImageTestCase ) :

	def testAgainstReferenceImplementation( self ) :

		imageReader = GafferImage.ImageReader()
		imageReader["fileName"].setValue( '${GAFFER_ROOT}/python/GafferImageTest/images/deepMergeReference.exr' )

		cropToDisplay = GafferImage.Crop()
		cropToDisplay["in"].setInput( imageReader["out"] )
		cropToDisplay["areaSource"].setValue( 2 )

		ramp = GafferImage.Ramp()
		ramp["format"].setValue( GafferImage.Format( 150, 100, 1.000 ) )
		ramp["startPosition"].setValue( imath.V2f( 0, 0 ) )
		ramp["endPosition"].setValue( imath.V2f( 150, 0 ) )

		shuffleRadius = GafferImage.Shuffle()
		shuffleRadius["shuffles"].addChild( Gaffer.ShufflePlug( "R", "radius" ) )
		shuffleRadius["in"].setInput( ramp["out"] )

		copyChannels = GafferImage.CopyChannels()
		copyChannels["in"][0].setInput( cropToDisplay["out"] )
		copyChannels["in"][1].setInput( shuffleRadius["out"] )
		copyChannels["channels"].setValue( 'radius' )

		diskBlur = GafferImage.DiskBlur()
		diskBlur["in"].setInput( copyChannels["out"] )
		diskBlur["radius"].setValue( 25.0 )
		diskBlur["radiusChannel"].setValue( 'radius' )
		diskBlur["approximationThreshold"].setValue( 1.0 )

		diskBlurRef = GafferImage.DiskBlur()
		diskBlurRef["in"].setInput( copyChannels["out"] )
		diskBlurRef["radius"].setValue( 25.0 )
		diskBlurRef["radiusChannel"].setValue( 'radius' )
		diskBlurRef["approximationThreshold"].setValue( 1.0 )
		diskBlurRef["__useReferenceImplementation"].setValue( 1 )

		with self.subTest( approximation = 1.0 ):
			self.assertImagesEqual( diskBlur["out"], diskBlurRef["out"], maxDifference = 1e-6 )

		diskBlur["approximationThreshold"].setValue( 0.0 )
		diskBlurRef["approximationThreshold"].setValue( 0.0 )

		with self.subTest( approximation = 0.0 ):
			self.assertImagesEqual( diskBlur["out"], diskBlurRef["out"], maxDifference = 1e-6 )

		diskBlur["layerBoundaries"].setValue( IECore.FloatVectorData( [ i * 0.5 for i in range( -15, 15 ) ] ) )
		diskBlurRef["layerBoundaries"].setValue( IECore.FloatVectorData( [ i * 0.5 for i in range( -15, 15 ) ] ) )

		with self.subTest( layerBoundaries = True ):
			self.assertImagesEqual( diskBlur["out"], diskBlurRef["out"], maxDifference = 1e-6 )

	def testAgainstReferenceImages( self ) :

		imageReader = GafferImage.ImageReader()
		imageReader["fileName"].setValue( '${GAFFER_ROOT}/python/GafferImageTest/images/diskBlurSource.exr' )

		diskBlur = GafferImage.DiskBlur()
		diskBlur["in"].setInput( imageReader["out"] )
		diskBlur["radius"].setValue( 1.0 )
		diskBlur["radiusChannel"].setValue( 'radius' )
		diskBlur["approximationThreshold"].setValue( 0.001 )

		refImageReader = GafferImage.ImageReader()
		refImageReader["fileName"].setValue( '${GAFFER_ROOT}/python/GafferImageTest/images/diskBlurred.exr' )

		# We have some tolerance here because the reference images were saved out before standardizing the
		# chunkSize - changing the chunkSize doesn't change correctness, but changing the order of summation
		# does affect the numerical imprecision. ( The actual error is more like 5e-7 in everything except the
		# radius channel, which is 8X bigger, so the errors are bigger ).
		self.assertImagesEqual( diskBlur["out"], refImageReader["out"], maxDifference = 3e-6, ignoreMetadata = True )

		diskBlur["layerBoundaries"].setValue( IECore.FloatVectorData( [ i * 0.5 for i in range( -15, 15 ) ] ) )

		refImageReader["fileName"].setValue( '${GAFFER_ROOT}/python/GafferImageTest/images/diskBlurredWithPlanes.exr' )

		self.assertImagesEqual( diskBlur["out"], refImageReader["out"], maxDifference = 3e-6, ignoreMetadata = True )

	def testAgainstResample( self ) :

		imageReader = GafferImage.ImageReader()
		imageReader["fileName"].setValue( '${GAFFER_ROOT}/python/GafferImageTest/images/deepMergeReference.exr' )

		resample = GafferImage.Resample()
		resample["in"].setInput( imageReader["out"] )
		resample["filter"].setValue( 'disk' )
		resample["filterScale"].setValue( imath.V2f( 7.0 ) )

		# The 'disk' mode of Resample is not anti-aliased, and treats a filterscale of 1 as a no-op ( to start
		# adding blur you have to set filterScale >1. We can match this by cranking up the approximationThreshold
		# to disable anti-aliasing, and setting the radius corresponding to a diameter to one less than the filterScale.
		diskBlur = GafferImage.DiskBlur()
		diskBlur["in"].setInput( imageReader["out"] )
		diskBlur["radius"].setValue( 3.0 )
		diskBlur["approximationThreshold"].setValue( 1.0 )

		self.assertImagesEqual( diskBlur["out"], resample["out"], maxDifference = 1e-6 )

	def testTransforms( self ) :

		imageReader = GafferImage.ImageReader()
		imageReader["fileName"].setValue( '${GAFFER_ROOT}/python/GafferImageTest/images/diskBlurSource.exr' )

		preOffset = GafferImage.Offset()
		preOffset["in"].setInput( imageReader["out"] )

		diskBlurAfter = GafferImage.DiskBlur()
		diskBlurAfter["in"].setInput( preOffset["out"] )
		diskBlurAfter["radius"].setValue( 1.0 )
		diskBlurAfter["radiusChannel"].setValue( 'radius' )
		diskBlurAfter["approximationThreshold"].setValue( 0.001 )
		diskBlurAfter["layerBoundaries"].setValue( IECore.FloatVectorData( [ i * 0.5 for i in range( -15, 15 ) ] ) )

		clearRadiusA = GafferImage.DeleteChannels()
		clearRadiusA["in"].setInput( diskBlurAfter["out"] )
		clearRadiusA["channels"].setValue( "radius" )

		diskBlurBefore = GafferImage.DiskBlur()
		diskBlurBefore["in"].setInput( imageReader["out"] )
		diskBlurBefore["radius"].setValue( 1.0 )
		diskBlurBefore["radiusChannel"].setValue( 'radius' )
		diskBlurBefore["approximationThreshold"].setValue( 0.001 )
		diskBlurBefore["layerBoundaries"].setValue( IECore.FloatVectorData( [ i * 0.5 for i in range( -15, 15 ) ] ) )

		postOffset = GafferImage.Offset()
		postOffset["in"].setInput( diskBlurBefore["out"] )
		postOffset["offset"].setInput( preOffset["offset"] )

		clearRadiusB = GafferImage.DeleteChannels()
		clearRadiusB["in"].setInput( postOffset["out"] )
		clearRadiusB["channels"].setValue( "radius" )

		offsets = [ (0,0), ( 1, 1 ), ( -1, -1 ), ( 127, -127 ), ( 61, 65), ( 3242, 7485 ) ]

		for o in offsets:
			with self.subTest( offset = o ):
				preOffset["offset"].setValue( imath.V2i( *o ) )
				self.assertImagesEqual( clearRadiusA["out"], clearRadiusB["out"], maxDifference = 4e-7 )

		preOffset["offset"].setValue( imath.V2i( 0 ) )

		resize = GafferImage.Resize()
		resize["in"].setInput( imageReader["out"] )
		resize["format"].setValue( GafferImage.Format( 1024, 256, 1.000 ) )
		resize["filter"].setValue( 'nearest' )

		preOffset["in"].setInput( resize["out"] )

		# After scaling up, we need to scale up the radius as well
		diskBlurAfter["radius"].setValue( 8.0 )
		diskBlurAfter["layerBoundaries"].setValue( IECore.FloatVectorData( [ i * 4 for i in range( -15, 15 ) ] ) )

		with self.subTest( testScaling = True ):
			# Test that scaling up all inputs gives a similar result to scaling up the output
			# ( The edges aren't exact due to pixel filtering, so we just check the average error )

			postResize = GafferImage.Resize()
			postResize["in"].setInput( clearRadiusB["out"] )
			postResize["format"].setValue( GafferImage.Format( 1024, 256, 1 ) )
			postResize["filter"].setValue( 'nearest' )

			compareMerge = GafferImage.Merge()
			compareMerge['operation'].setValue( GafferImage.Merge.Operation.Difference )
			compareMerge["in"][0].setInput( clearRadiusA["out"] )
			compareMerge["in"][1].setInput( postResize["out"] )

			compareStats = GafferImage.ImageStats()
			compareStats["in"].setInput( compareMerge["out"] )
			compareStats["areaSource"].setValue( GafferImage.ImageStats.AreaSource.DisplayWindow )

			self.assertLess( compareStats["average"].getValue()[0], 0.02 )
			self.assertLess( compareStats["average"].getValue()[1], 0.02 )
			self.assertLess( compareStats["average"].getValue()[2], 0.02 )
			self.assertLess( compareStats["average"].getValue()[3], 0.02 )

		diskBlurBefore["in"].setInput( resize["out"] )
		diskBlurBefore["radius"].setValue( 8.0 )
		diskBlurBefore["layerBoundaries"].setValue( IECore.FloatVectorData( [ i * 4 for i in range( -15, 15 ) ] ) )

		for o in offsets:
			with self.subTest( offset = o, large = True ):
				preOffset["offset"].setValue( imath.V2i( *o ) )
				self.assertImagesEqual( clearRadiusA["out"], clearRadiusB["out"], maxDifference = 1.5e-6 )

	def testDataWindow( self ) :
		# Many of our image sources set the pixels outside the data window to black anyway, so there would
		# be no error introduced by reading pixels outside the data window, but this is incorrect.
		# We can test this using a Constant as a source, which sets the pixels for all tiles to a constant,
		# indepedent of the data window.


		constant = GafferImage.Constant()
		constant["color"].setValue( imath.Color4f( 1, 0, 1, 1 ) )

		diskBlur = GafferImage.DiskBlur()
		diskBlur["in"].setInput( constant["out"] )
		diskBlur["radius"].setValue( 10.0 )
		diskBlur["approximationThreshold"].setValue( 0.0 )

		refConstant = GafferImage.Constant()
		refConstant["color"].setValue( imath.Color4f( 1, 0, 1, 1 ) )

		refDiskBlur = GafferImage.DiskBlur()
		refDiskBlur["in"].setInput( refConstant["out"] )
		refDiskBlur["radius"].setValue( 10.0 )
		refDiskBlur["approximationThreshold"].setValue( 0.0 )
		refDiskBlur["__useReferenceImplementation"].setValue( 1 )

		refOffset = GafferImage.Offset()
		refOffset["in"].setInput( refDiskBlur["out"] )

		refCrop = GafferImage.Crop()
		refCrop["in"].setInput( refOffset["out"] )
		refCrop["affectDataWindow"].setValue( False )
		refCrop["resetOrigin"].setValue( False )


		for bound in [
			( imath.V2i( 0, 0 ), imath.V2i( 50, 50 ) ),
			( imath.V2i( 0, 0 ), imath.V2i( 100, 100 ) ),
			( imath.V2i( 33, 51 ), imath.V2i( 70, 113 ) ),
			( imath.V2i( 133, 151 ), imath.V2i( 170, 213 ) )
		]:
			with self.subTest( bound = bound ):
				constant["format"].setValue( GafferImage.Format( imath.Box2i( bound[0], bound[1] ), 1.000 ) )
				refConstant["format"].setValue( GafferImage.Format( imath.Box2i( imath.V2i( 0 ), bound[1] - bound[0] ), 1.000 ) )
				refOffset["offset"].setValue( bound[0] )
				refCrop["area"].setValue( imath.Box2i( bound[0], bound[1] ) )

				self.assertImagesEqual( diskBlur["out"], refCrop["out"], maxDifference = 5e-7 )

	def testBoundingMode( self ) :

		imageReader = GafferImage.ImageReader()
		imageReader["fileName"].setValue( '${GAFFER_ROOT}/resources/images/macaw.exr' )

		crop = GafferImage.Crop()
		crop["in"].setInput( imageReader["out"] )
		crop["area"].setValue( imath.Box2i( imath.V2i( 1090, 1100 ), imath.V2i( 1190, 1200 ) ) )

		resample = GafferImage.Resample()
		resample["in"].setInput( crop["out"] )
		resample["filter"].setValue( 'disk' )
		resample["filterScale"].setValue( imath.V2f( 10, 10 ) )

		diskBlur = GafferImage.DiskBlur()
		diskBlur["in"].setInput( crop["out"] )
		diskBlur["radius"].setValue( 4.0 )
		diskBlur["approximationThreshold"].setValue( 1000.0 )

		self.assertImagesEqual( diskBlur["out"], resample["out"], maxDifference = 1e-6 )


		diskBlur["boundingMode"].setValue( GafferImage.DiskBlur.BoundingMode.Mirror )

		# We don't currently support a "Mirror" bounding mode on Resample, so this
		# reference image was created with a prototype version of Resample that does
		# support Mirror. Using this image validates that the behaviour of the Mirror
		# bounding mode for a scattering blur has an identical result to a Mirror
		# bounding mode for a gathering blur. If we eventually support Mirror mode
		# on Resample, we can just compare to that live, and get rid of this image
		# from the repo ( and also lower the high tolerance, which is currently
		# due to saving the ref image as half float ).
		refImageReader = GafferImage.ImageReader()
		refImageReader["fileName"].setValue( '${GAFFER_ROOT}/python/GafferImageTest/images/diskBlurMirrorRef.exr' )

		self.assertImagesEqual( diskBlur["out"], refImageReader["out"], ignoreMetadata = True, maxDifference = 0.0003 )

	def testNormalization( self ):

		constant = GafferImage.Constant()
		constant["format"].setValue( GafferImage.Format( 513, 513, 1.000 ) )
		constant["color"].setValue( imath.Color4f( 1, 1, 1, 1 ) )

		diskBlur = GafferImage.DiskBlur()
		diskBlur["in"].setInput( constant["out"] )
		diskBlur["maxRadius"].setValue( 256 )

		imageSampler = GafferImage.ImageSampler()
		imageSampler["image"].setInput( diskBlur["out"] )
		imageSampler["pixel"].setValue( imath.V2f( 256, 256 ) )
		imageSampler["interpolate"].setValue( False )

		random.seed( 42 )

		for approximate in [ True, False ]:
			for radius in [ 0, 0.01, 0.3, 0.7, 0.999, 1.0, 1.001, 1.1, 1.3, 1.9, 1.999, 37.2,
					233, 233.1, 233.33, 255.999, 256, 256.001, 256.7, 999999
					] + [ random.uniform( 0, 256 ) for i in range( 20 )
				]:

				diskBlur["approximationThreshold"].setValue( 1.0 if approximate else 0.0 )
				diskBlur["radius"].setValue( radius )

				with self.subTest( approximate = approximate, radius = radius ):
					self.assertAlmostEqual( imageSampler['color']['r'].getValue(), 1.0, delta = 5e-6 )

	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 5 )
	def testPerfLarge( self ) :

		imageReader = GafferImage.ImageReader()
		imageReader["fileName"].setValue( "${GAFFER_ROOT}/resources/images/macaw.exr" )


		resize = GafferImage.Resize()
		resize["in"].setInput( imageReader["out"] )
		resize["format"].setValue( GafferImage.Format( 960, 720, 1.000 ) )

		diskBlur = GafferImage.DiskBlur()
		diskBlur["in"].setInput( resize["out"] )
		diskBlur["radius"].setValue( 100 )
		diskBlur["approximationThreshold"].setValue( 0.0 )

		GafferImageTest.processTiles( diskBlur["in"] )

		with GafferTest.TestRunner.PerformanceScope() :
			GafferImageTest.processTiles( diskBlur["out"] )

	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 1 )
	def testPerfMedium( self ) :

		imageReader = GafferImage.ImageReader()
		imageReader["fileName"].setValue( "${GAFFER_ROOT}/resources/images/macaw.exr" )

		diskBlur = GafferImage.DiskBlur()
		diskBlur["in"].setInput( imageReader["out"] )
		diskBlur["radius"].setValue( 25 )
		diskBlur["approximationThreshold"].setValue( 0.0 )

		GafferImageTest.processTiles( diskBlur["in"] )

		with GafferTest.TestRunner.PerformanceScope() :
			GafferImageTest.processTiles( diskBlur["out"] )

	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 1 )
	def testPerfLargeApprox( self ) :

		imageReader = GafferImage.ImageReader()
		imageReader["fileName"].setValue( "${GAFFER_ROOT}/resources/images/macaw.exr" )

		GafferImageTest.processTiles( imageReader["out"] )

		diskBlur = GafferImage.DiskBlur()
		diskBlur["in"].setInput( imageReader["out"] )
		diskBlur["radius"].setValue( 100 )
		diskBlur["approximationThreshold"].setValue( 1 )

		GafferImageTest.processTiles( diskBlur["in"] )

		with GafferTest.TestRunner.PerformanceScope() :
			GafferImageTest.processTiles( diskBlur["out"] )

	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 1 )
	def testPerfHugeApprox( self ) :

		imageReader = GafferImage.ImageReader()
		imageReader["fileName"].setValue( "${GAFFER_ROOT}/resources/images/macaw.exr" )

		GafferImageTest.processTiles( imageReader["out"] )

		diskBlur = GafferImage.DiskBlur()
		diskBlur["in"].setInput( imageReader["out"] )
		diskBlur["radius"].setValue( 250 )
		diskBlur["approximationThreshold"].setValue( 1 )

		GafferImageTest.processTiles( diskBlur["in"] )

		with GafferTest.TestRunner.PerformanceScope() :
			GafferImageTest.processTiles( diskBlur["out"] )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testPerfSmallApprox( self ) :

		imageReader = GafferImage.ImageReader()
		imageReader["fileName"].setValue( "${GAFFER_ROOT}/resources/images/macaw.exr" )

		GafferImageTest.processTiles( imageReader["out"] )

		diskBlur = GafferImage.DiskBlur()
		diskBlur["in"].setInput( imageReader["out"] )
		diskBlur["radius"].setValue( 2 )
		diskBlur["approximationThreshold"].setValue( 1 )

		GafferImageTest.processTiles( diskBlur["in"] )

		with GafferTest.TestRunner.PerformanceScope() :
			GafferImageTest.processTiles( diskBlur["out"] )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testPerfSmall( self ) :

		imageReader = GafferImage.ImageReader()
		imageReader["fileName"].setValue( "${GAFFER_ROOT}/resources/images/macaw.exr" )

		GafferImageTest.processTiles( imageReader["out"] )

		diskBlur = GafferImage.DiskBlur()
		diskBlur["in"].setInput( imageReader["out"] )
		diskBlur["radius"].setValue( 2 )
		diskBlur["approximationThreshold"].setValue( 0.0 )

		GafferImageTest.processTiles( diskBlur["in"] )

		with GafferTest.TestRunner.PerformanceScope() :
			GafferImageTest.processTiles( diskBlur["out"] )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testPerfTiny( self ) :

		imageReader = GafferImage.ImageReader()
		imageReader["fileName"].setValue( "${GAFFER_ROOT}/resources/images/macaw.exr" )

		GafferImageTest.processTiles( imageReader["out"] )

		diskBlur = GafferImage.DiskBlur()
		diskBlur["in"].setInput( imageReader["out"] )
		diskBlur["radius"].setValue( 0.5 )
		diskBlur["approximationThreshold"].setValue( 0.0 )

		GafferImageTest.processTiles( diskBlur["in"] )

		with GafferTest.TestRunner.PerformanceScope() :
			GafferImageTest.processTiles( diskBlur["out"] )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testPerfPrecalc( self ) :

		diskBlur = GafferImage.DiskBlur()

		c = Gaffer.Context()
		c["__quantizedMaxRadius"] = IECore.IntData( 2048 )
		with c:
			with GafferTest.TestRunner.PerformanceScope() :
				diskBlur["__scanlinesLUT"].getValue()

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testPerfParallelPrecalc( self ) :

		constant = GafferImage.Constant()
		constant["format"].setValue( GafferImage.Format( 1920, 1080, 1.000 ) )

		diskBlur = GafferImage.DiskBlur()
		diskBlur["in"].setInput( constant["out"] )
		diskBlur["maxRadius"].setValue( 2048 )

		# Set up a blur that is incredibly cheap to compute, so that most of the expense
		# will be in the precomputation of the scanlinesLUT plug
		diskBlur["radius"].setValue( 1 )
		diskBlur["approximationThreshold"].setValue( 1.0 )

		with GafferTest.TestRunner.PerformanceScope() :
			GafferImageTest.processTiles( diskBlur["out"] )

	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 1 )
	def testPerfVaryMaxRadius( self ) :

		imageReader = GafferImage.ImageReader()
		imageReader["fileName"].setValue( "${GAFFER_ROOT}/resources/images/macaw.exr" )

		diskBlur = GafferImage.DiskBlur()
		diskBlur["in"].setInput( imageReader["out"] )
		diskBlur["radius"].setValue( 5 )
		diskBlur["approximationThreshold"].setValue( 1.0 )

		GafferImageTest.processTiles( diskBlur["in"] )

		with GafferTest.TestRunner.PerformanceScope() :
			for maxRadius in [ 1000, 1001, 1002, 1003, 1004 ]:
				diskBlur["maxRadius"].setValue( maxRadius )
				GafferImageTest.processTiles( diskBlur["out"] )

if __name__ == "__main__":
	unittest.main()
