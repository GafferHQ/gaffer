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

import os
import pathlib
import shutil
import unittest
import random
import subprocess
import time

import imath

import IECore

import Gaffer
import GafferTest
import GafferImage
import GafferImageTest

class ResampleTest( GafferImageTest.ImageTestCase ) :

	# The closest thing we have in the test images to a "normal" image
	representativeImagePath = GafferImageTest.ImageTestCase.imagesPath() / 'deepMergeReference.exr'

	representativeDeepImagePath = GafferImageTest.ImageTestCase.imagesPath() / "representativeDeepImage.exr"
	deepResampleRGBErrorPath = GafferImageTest.ImageTestCase.imagesPath() / "deepResampleRGBError.exr"
	deepIntPointsPath = GafferImageTest.ImageTestCase.imagesPath() / "deepIntPoints.exr"
	deepIntVolumesPath = GafferImageTest.ImageTestCase.imagesPath() / "deepIntVolumes.exr"
	deepFloatPointsPath = GafferImageTest.ImageTestCase.imagesPath() / "deepFloatPoints.exr"
	deepFloatVolumesPath = GafferImageTest.ImageTestCase.imagesPath() / "deepFloatVolumes.exr"

	floatValuesPath = GafferImageTest.ImageTestCase.imagesPath() / "floatValues.exr"

	def testDataWindow( self ) :

		c = GafferImage.Constant()
		c["format"].setValue( GafferImage.Format( 100, 100 ) )
		c["color"].setValue( imath.Color4f( 1 ) )

		r = GafferImage.Resample()
		r["in"].setInput( c["out"] )
		r["matrix"].setValue(
			imath.M33f().translate( imath.V2f( 10.5, 11.5 ) ).scale( imath.V2f( 0.1 ) )
		)

		self.assertEqual(
			r["out"]["dataWindow"].getValue(),
			imath.Box2i(
				imath.V2i( 10, 11 ),
				imath.V2i( 21, 22 )
			)
		)

	def testExpectedOutput( self ) :

		def __test( fileName, size, filter ) :

			inputFileName = self.imagesPath() / fileName

			reader = GafferImage.ImageReader()
			reader["fileName"].setValue( inputFileName )

			inSize = reader["out"]["format"].getValue().getDisplayWindow().size()
			inSize = imath.V2f( inSize.x, inSize.y )

			resample = GafferImage.Resample()
			resample["in"].setInput( reader["out"] )
			resample["matrix"].setValue(
				imath.M33f().scale( imath.V2f( size.x, size.y ) / inSize )
			)
			resample["filter"].setValue( filter )
			resample["boundingMode"].setValue( GafferImage.Sampler.BoundingMode.Clamp )

			crop = GafferImage.Crop()
			crop["in"].setInput( resample["out"] )
			crop["area"].setValue( imath.Box2i( imath.V2i( 0 ), size ) )

			outputFileName = self.temporaryDirectory() / ( "%s_%dx%d_%s.exr" % ( pathlib.Path( fileName ).with_suffix(""), size.x, size.y, filter ) )
			writer = GafferImage.ImageWriter()
			writer["in"].setInput( crop["out"] )
			writer["channels"].setValue( "[RGB]" )
			writer["fileName"].setValue( outputFileName )
			writer["task"].execute()

			result = GafferImage.ImageReader()
			result["fileName"].setValue( writer["fileName"].getValue() )

			expected = GafferImage.ImageReader()
			expected["fileName"].setValue(
				self.imagesPath() / (
					"%s_%dx%d_%s.exr" % (
						pathlib.Path( fileName ).with_suffix(""),
						size.x,
						size.y,
						filter
					)
				)
			)

			self.assertImagesEqual( result["out"], expected["out"], maxDifference = 0.0005, ignoreMetadata = True )

			# Enable to write out images for visual comparison with OIIO.
			# The images will appear in a "resampleComparison" subdirectory
			# of the current directory.
			if False :

				resampleComparisonDir = pathlib.Path( "resampleComparison" )
				resampleComparisonDir.mkdir( exist_ok=True )

				shutil.copyfile( outputFileName, resampleComparisonDir / ( "gaffer_" + outputFileName.name ) )

				oiioOutputFileName = resampleComparisonDir / ( "oiio_%s_%dx%d_%s.exr" % ( pathlib.Path( fileName ).with_suffix(""), size.x, size.y, filter ) )

				subprocess.check_call(
					"oiiotool --threads 1 %s --ch R,G,B --resize:filter=%s %dx%d  -o %s" %
					(
						inputFileName,
						filter,
						size.x, size.y,
						oiioOutputFileName
					),
					shell = True
				)

		tests = [
			( "resamplePatterns.exr", imath.V2i( 4 ), "lanczos3" ),
			( "resamplePatterns.exr", imath.V2i( 40 ), "box" ),
			( "resamplePatterns.exr", imath.V2i( 101 ), "gaussian" ),
			( "resamplePatterns.exr", imath.V2i( 119 ), "mitchell" ),
		]

		for args in tests :
			with self.subTest( fileName = args[0], size = args[1], ftilter = args[2] ):
				__test( *args )

	def testNearest( self ) :

		reader = GafferImage.ImageReader()
		reader["fileName"].setValue( self.representativeImagePath )

		resampleNearest = GafferImage.Resample()
		resampleNearest["in"].setInput( reader["out"] )
		resampleNearest["filter"].setValue( "nearest" )
		resampleNearest["matrix"].setValue( imath.M33f( 1.377, 0, 0, 0, 1.377, 0, 0, 0, 1 ) )

		resampleRef = GafferImage.Resample()
		resampleRef["in"].setInput( reader["out"] )
		resampleRef["filter"].setValue( "box" )
		resampleRef["matrix"].setValue( imath.M33f( 1.377, 0, 0, 0, 1.377, 0, 0, 0, 1 ) )

		# For upscaling, "nearest" should have the same result as a box filter with a default filter size,
		# except that "nearest" is faster
		self.assertImagesEqual( resampleNearest["out"], resampleRef["out"] )

	def testInseparableFastPath( self ) :

		reader = GafferImage.ImageReader()
		reader["fileName"].setValue( self.imagesPath() / "resamplePatterns.exr" )

		# When applying an inseparable filter with no scaling, we can use a much faster code path.
		# This code path should not have any effect on the result
		resampleFastPath = GafferImage.Resample()
		resampleFastPath["in"].setInput( reader["out"] )
		resampleFastPath['filterScale'].setValue( imath.V2f( 4 ) )
		resampleFastPath["filter"].setValue( "radial-lanczos3" )

		# Force the slow code path using the "debug" parameter
		resampleReference = GafferImage.Resample()
		resampleReference["in"].setInput( reader["out"] )
		resampleReference['filterScale'].setValue( imath.V2f( 4 ) )
		resampleReference["filter"].setValue( "radial-lanczos3" )
		resampleReference["debug"].setValue( GafferImage.Resample.Debug.SinglePass )

		self.assertImagesEqual( resampleFastPath["out"], resampleReference["out"] )

	def testSincUpsize( self ) :

		c = GafferImage.Constant()
		c["format"].setValue( GafferImage.Format( 100, 100 ) )
		c["color"].setValue( imath.Color4f( 1 ) )

		r = GafferImage.Resample()
		r["matrix"].setValue( imath.M33f().scale( imath.V2f( 4 ) ) )
		r["boundingMode"].setValue( GafferImage.Sampler.BoundingMode.Clamp )
		r["filter"].setValue( "sinc" )
		r["in"].setInput( c["out"] )

		i = GafferImage.ImageAlgo.image( r["out"] )
		self.assertEqual( i["R"], IECore.FloatVectorData( [ 1.0 ] * 400 * 400 ) )

	def testExpandDataWindow( self ) :

		d = imath.Box2i( imath.V2i( 5, 6 ), imath.V2i( 101, 304 ) )
		c = GafferImage.Constant()
		c["format"].setValue( GafferImage.Format( d ) )

		r = GafferImage.Resample()
		r["in"].setInput( c["out"] )
		r["filter"].setValue( "box" )
		self.assertEqual( r["out"]["dataWindow"].getValue(), d )

		r["expandDataWindow"].setValue( True )
		self.assertEqual( r["out"]["dataWindow"].getValue(), imath.Box2i( d.min() - imath.V2i( 1 ), d.max() + imath.V2i( 1 ) ) )

		r["filterScale"].setValue( imath.V2f( 10 ) )
		self.assertEqual( r["out"]["dataWindow"].getValue(), imath.Box2i( d.min() - imath.V2i( 5 ), d.max() + imath.V2i( 5 ) ) )

	def testCancellation( self ) :

		script = Gaffer.ScriptNode()

		script["c"] = GafferImage.Constant()

		script["r"] = GafferImage.Resample()
		script["r"]["in"].setInput( script["c"]["out"] )
		script["r"]["filterScale"].setValue( imath.V2f( 2000 ) )

		bt = Gaffer.ParallelAlgo.callOnBackgroundThread( script["r"]["out"], lambda : GafferImageTest.processTiles( script["r"]["out"] ) )
		# Give background tasks time to get into full swing
		time.sleep( 0.1 )

		# Check that we can cancel them in reasonable time
		acceptableCancellationDelay = 4.0 if GafferTest.inCI() else 0.25
		t = time.time()
		bt.cancelAndWait()
		self.assertLess( time.time() - t, acceptableCancellationDelay )

		# Check that we can do the same when using a non-separable filter
		script["r"]["filter"].setValue( "disk" )

		bt = Gaffer.ParallelAlgo.callOnBackgroundThread( script["r"]["out"], lambda : GafferImageTest.processTiles( script["r"]["out"] ) )
		time.sleep( 0.1 )

		t = time.time()
		bt.cancelAndWait()
		self.assertLess( time.time() - t, acceptableCancellationDelay )

	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 5 )
	def testPerfHorizontal( self ) :

		imageReader = GafferImage.ImageReader()
		imageReader["fileName"].setValue( self.representativeImagePath )

		resize = GafferImage.Resize()
		resize["in"].setInput( imageReader["out"] )
		resize["format"].setValue( GafferImage.Format( 1920, 1080, 1.000 ) )

		resample = GafferImage.Resample()
		resample["in"].setInput( resize["out"] )
		resample["filter"].setValue( 'box' )
		resample["filterScale"].setValue( imath.V2f( 300.0 ) )

		GafferImageTest.processTiles( resize["out"] )

		with GafferTest.TestRunner.PerformanceScope() :
			GafferImageTest.processTiles( resample["__horizontalPass"] )

	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 5 )
	def testPerfVertical( self ) :

		imageReader = GafferImage.ImageReader()
		imageReader["fileName"].setValue( self.representativeImagePath )

		resize = GafferImage.Resize()
		resize["in"].setInput( imageReader["out"] )
		resize["format"].setValue( GafferImage.Format( 1920, 1080, 1.000 ) )

		resample = GafferImage.Resample()
		resample["in"].setInput( resize["out"] )
		resample["filter"].setValue( 'box' )
		resample["filterScale"].setValue( imath.V2f( 300.0 ) )

		GafferImageTest.processTiles( resample["__horizontalPass"] )

		with GafferTest.TestRunner.PerformanceScope() :
			GafferImageTest.processTiles( resample["out"] )

	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 5 )
	def testPerfSmallFilter( self ) :

		imageReader = GafferImage.ImageReader()
		imageReader["fileName"].setValue( self.representativeImagePath )

		resize = GafferImage.Resize()
		resize["in"].setInput( imageReader["out"] )
		resize["format"].setValue( GafferImage.Format( 4000, 4000, 1.000 ) )

		resample = GafferImage.Resample()
		resample["in"].setInput( resize["out"] )
		resample["filter"].setValue( 'box' )
		resample["filterScale"].setValue( imath.V2f( 4.0 ) )

		GafferImageTest.processTiles( resize["out"] )

		with GafferTest.TestRunner.PerformanceScope() :
			GafferImageTest.processTiles( resample["out"] )

	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 5 )
	def testPerfVerySmallFilter( self ) :

		imageReader = GafferImage.ImageReader()
		imageReader["fileName"].setValue( self.representativeImagePath )

		resize = GafferImage.Resize()
		resize["in"].setInput( imageReader["out"] )
		resize["format"].setValue( GafferImage.Format( 4000, 4000, 1.000 ) )

		resample = GafferImage.Resample()
		resample["in"].setInput( resize["out"] )
		resample["filter"].setValue( 'box' )
		resample["filterScale"].setValue( imath.V2f( 2.0 ) )

		GafferImageTest.processTiles( resize["out"] )

		with GafferTest.TestRunner.PerformanceScope() :
			GafferImageTest.processTiles( resample["out"] )

	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 1 )
	def testPerfInseparableLanczos( self ) :

		imageReader = GafferImage.ImageReader()
		imageReader["fileName"].setValue( self.representativeImagePath )

		resize = GafferImage.Resize()
		resize["in"].setInput( imageReader["out"] )
		resize["format"].setValue( GafferImage.Format( 64, 64 ) )

		resample = GafferImage.Resample()
		resample["in"].setInput( resize["out"] )
		resample["filter"].setValue( 'radial-lanczos3' )
		resample["filterScale"].setValue( imath.V2f( 20.0 ) )

		GafferImageTest.processTiles( resize["out"] )

		with GafferTest.TestRunner.PerformanceScope() :
			GafferImageTest.processTiles( resample["out"] )

	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 1 )
	def testPerfInseparableDisk( self ) :

		imageReader = GafferImage.ImageReader()
		imageReader["fileName"].setValue( self.representativeImagePath )

		resize = GafferImage.Resize()
		resize["in"].setInput( imageReader["out"] )
		resize["format"].setValue( GafferImage.Format( 1920, 1920 ) )

		resample = GafferImage.Resample()
		resample["in"].setInput( resize["out"] )
		resample["filter"].setValue( 'disk' )
		resample["filterScale"].setValue( imath.V2f( 20.0 ) )

		GafferImageTest.processTiles( resize["out"] )

		with GafferTest.TestRunner.PerformanceScope() :
			GafferImageTest.processTiles( resample["out"] )

	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 1 )
	def testPerfInseparableAwkwardSize( self ) :

		imageReader = GafferImage.ImageReader()
		imageReader["fileName"].setValue( self.representativeImagePath )

		resize = GafferImage.Resize()
		resize["in"].setInput( imageReader["out"] )
		resize["format"].setValue( GafferImage.Format( 6000, 6000 ) )

		resample = GafferImage.Resample()
		resample["in"].setInput( resize["out"] )
		resample["filter"].setValue( 'disk' )
		resample["filterScale"].setValue( imath.V2f( 1.1 ) )

		GafferImageTest.processTiles( resize["out"] )

		with GafferTest.TestRunner.PerformanceScope() :
			GafferImageTest.processTiles( resample["out"] )

	def testBruteForceDeep( self ):

		intPoints = GafferImage.ImageReader()
		intPoints["fileName"].setValue( self.deepIntPointsPath )
		intVolumes = GafferImage.ImageReader()
		intVolumes["fileName"].setValue( self.deepIntVolumesPath )
		floatPoints = GafferImage.ImageReader()
		floatPoints["fileName"].setValue( self.deepFloatPointsPath )
		floatVolumes = GafferImage.ImageReader()
		floatVolumes["fileName"].setValue( self.deepFloatVolumesPath )

		allInts = GafferImage.DeepMerge( "allInts" )
		allInts["in"][0].setInput( intPoints["out"] )
		allInts["in"][1].setInput( intVolumes["out"] )

		allFloats = GafferImage.DeepMerge( "allFloats" )
		allFloats["in"][0].setInput( floatPoints["out"] )
		allFloats["in"][1].setInput( floatVolumes["out"] )

		allCombined = GafferImage.DeepMerge( "allCombined" )
		allCombined["in"][0].setInput( intPoints["out"] )
		allCombined["in"][1].setInput( intVolumes["out"] )
		allCombined["in"][2].setInput( floatPoints["out"] )
		allCombined["in"][3].setInput( floatVolumes["out"] )

		# By upsizing this test image, we produce a test image where there are lots of identical samples
		# in adjacent pixels, which could help exercise special cases when merging samples at identical depths
		allCombinedUpsize = GafferImage.Resize( "allCombinedUpsize" )
		allCombinedUpsize["in"].setInput( allCombined["out"] )
		allCombinedUpsize["format"].setValue( GafferImage.Format( 128, 128, 1.000 ) )
		allCombinedUpsize["filter"].setValue( 'box' )
		allCombinedUpsize["filterDeep"].setValue( True )

		rgbError = GafferImage.ImageReader( "deepResampleRGBError" )
		rgbError["fileName"].setValue( self.deepResampleRGBErrorPath )

		testImageCentered = GafferImage.Offset()

		deepResample = GafferImage.Resample()
		deepResample["in"].setInput( testImageCentered["out"] )
		deepResample["expandDataWindow"].setValue( True )
		deepResample["filterDeep"].setValue( True )

		tidyAfterResample = GafferImage.DeepTidy()
		tidyAfterResample["in"].setInput( deepResample["out"] )

		flattenAfter = GafferImage.DeepToFlat()
		flattenAfter["in"].setInput( deepResample["out"] )
		# The filtered depth output from Flatten is affected enormously by
		# "curve shape discrepancy" ( see comment below ), so we just won't check Z.
		# The tests using DeepSlice are used to check the depth.
		flattenAfter['depthMode'].setValue( GafferImage.DeepToFlat.DepthMode.None_ )

		flattenBefore = GafferImage.DeepToFlat()
		flattenBefore["in"].setInput( testImageCentered["out"] )
		flattenBefore['depthMode'].setValue( GafferImage.DeepToFlat.DepthMode.None_ )

		flatResample = GafferImage.Resample()
		flatResample["in"].setInput( flattenBefore["out"] )
		flatResample["expandDataWindow"].setValue( True )
		flatResample["matrix"].setInput( deepResample["matrix"] )
		flatResample["filter"].setInput( deepResample["filter"] )
		flatResample["filterScale"].setInput( deepResample["filterScale"] )

		flatResampleIsolateNegative = GafferImage.Grade()
		flatResampleIsolateNegative["in"].setInput( flatResample["out"] )
		flatResampleIsolateNegative["channels"].setValue( '[A]' )
		flatResampleIsolateNegative["whitePoint"]["a"].setValue( -1e-10 )
		flatResampleIsolateNegative["whiteClamp"].setValue( True )

		flatResampleRemoveNegative = GafferImage.Mix()
		flatResampleRemoveNegative["in"][0].setInput( flatResample["out"] )
		flatResampleRemoveNegative["mask"].setInput( flatResampleIsolateNegative["out"] )

		flatResampleForceRange = GafferImage.Grade()
		flatResampleForceRange["in"].setInput( flatResampleRemoveNegative["out"] )
		flatResampleForceRange["channels"].setValue( '[A]' )
		flatResampleForceRange["whiteClamp"].setValue( True )

		sliceAfter = GafferImage.DeepSlice()
		sliceAfter["in"].setInput( deepResample["out"] )
		sliceAfter["farClip"]["enabled"].setValue( True )
		sliceAfter["flatten"].setValue( True )

		sliceAfterNoZ = GafferImage.DeleteChannels()
		sliceAfterNoZ["in"].setInput( sliceAfter["out"] )
		sliceAfterNoZ["channels"].setValue( "Z ZBack" )

		sliceAfterAlphaOnly = GafferImage.DeleteChannels()
		sliceAfterAlphaOnly["in"].setInput( sliceAfter["out"] )
		sliceAfterAlphaOnly['mode'].setValue( GafferImage.DeleteChannels.Mode.Keep )
		sliceAfterAlphaOnly["channels"].setValue( "A" )

		referenceSlice = GafferImage.DeepSlice()
		referenceSlice["in"].setInput( testImageCentered["out"] )
		referenceSlice["farClip"]["enabled"].setValue( True )
		referenceSlice["farClip"]["value"].setInput( sliceAfter["farClip"]["value"] )
		referenceSlice["flatten"].setValue( True )

		referenceSliceResample = GafferImage.Resample()
		referenceSliceResample["in"].setInput( referenceSlice["out"] )
		referenceSliceResample["expandDataWindow"].setValue( True )
		referenceSliceResample["matrix"].setInput( deepResample["matrix"] )
		referenceSliceResample["filter"].setInput( deepResample["filter"] )
		referenceSliceResample["filterScale"].setInput( deepResample["filterScale"] )

		referenceSliceResampleNoZ = GafferImage.DeleteChannels()
		referenceSliceResampleNoZ["in"].setInput( referenceSliceResample["out"] )
		referenceSliceResampleNoZ["channels"].setValue( "Z ZBack" )

		referenceSliceResampleAlphaOnly = GafferImage.DeleteChannels()
		referenceSliceResampleAlphaOnly["in"].setInput( referenceSliceResample["out"] )
		referenceSliceResampleAlphaOnly['mode'].setValue( GafferImage.DeleteChannels.Mode.Keep )
		referenceSliceResampleAlphaOnly["channels"].setValue( "A" )

		linearReferenceSliceTidy = GafferImage.DeepTidy()
		linearReferenceSliceTidy["in"].setInput( testImageCentered["out"] )

		convertToLinear = GafferImage.Premultiply()
		convertToLinear["in"].setInput( linearReferenceSliceTidy["out"] )
		convertToLinear["channels"].setValue( '[RGBA]' )
		convertToLinear["useDeepVisibility"].setValue( True )

		linearReferenceDontUseA = GafferImage.Shuffle()
		linearReferenceDontUseA["in"].setInput( convertToLinear["out"] )
		linearReferenceDontUseA["shuffles"].addChild( Gaffer.ShufflePlug( "A", "swapA", True ) )

		linearReferenceSlice = GafferImage.DeepSlice()
		linearReferenceSlice["in"].setInput( linearReferenceDontUseA["out"] )
		linearReferenceSlice["farClip"]["enabled"].setValue( True )
		linearReferenceSlice["farClip"]["value"].setInput( sliceAfter["farClip"]["value"] )
		linearReferenceSlice["flatten"].setValue( True )

		linearReferenceRestoreA = GafferImage.Shuffle()
		linearReferenceRestoreA["in"].setInput( linearReferenceSlice["out"] )
		linearReferenceRestoreA["shuffles"].addChild( Gaffer.ShufflePlug( "swapA", "A", True ) )

		linearReferenceSliceNoZ = GafferImage.DeleteChannels()
		linearReferenceSliceNoZ["in"].setInput( linearReferenceRestoreA["out"] )
		linearReferenceSliceNoZ["channels"].setValue( "Z ZBack" )

		linearReferenceSliceResample = GafferImage.Resample()
		linearReferenceSliceResample["in"].setInput( linearReferenceSliceNoZ["out"] )
		linearReferenceSliceResample["expandDataWindow"].setValue( True )
		linearReferenceSliceResample["matrix"].setInput( deepResample["matrix"] )
		linearReferenceSliceResample["filter"].setInput( deepResample["filter"] )
		linearReferenceSliceResample["filterScale"].setInput( deepResample["filterScale"] )

		random.seed( 42 )

		# Test a variety of source images
		for image, zStart, zEnd, tolerance in [
			( allInts["out"], 0, 4, 2e-6 ),
			( allFloats["out"], 0, 4, 2e-6 ),
			( allCombined["out"], 0, 4, 2e-6 ),
			( allCombinedUpsize["out"], 0, 4, 4e-5 ),
			( rgbError["out"], 2, 4, 2e-6 ),
		]:

			testImageCentered["in"].setInput( image )
			testImageCentered["offset"].setValue( -image.dataWindow().center() )

			# Test a variety of operations
			for scale, offset, filter, filterScale in [
				# Test an upscale using the simple but inaccurate nearest mode
				( 1.6, 0, "nearest", 0.0 ),

				# Results in kernel of [ 0.333333, 1, 0.333333 ]
				# Only samples 9 pixels, moderate weights, reasonable for basic tests
				( 1, 0, "triangle", 1.5 ),

				# Test a moderate upscale
				( 1.5, 0, "triangle", 1.5 ),

				# Test a downscale ( chosen to exercise some weird behaviour at floating point boundaries )
				( 0.48, 32, "triangle", 1.5 ),

				# An aggressive sharpening filter with negative lobes. Intended to test the sort of thing
				# we use for downsampling, though scaled down to reduce runtime.
				# Results in kernel of [ 0.0243171, -0.132871, 1, -0.132871, 0.0243171 ]
				( 1, 0, "lanczos3", 0.8 ),
			]:

				deepResample["matrix"].setValue( imath.M33f( ( scale, 0, 0 ), ( 0, scale, 0 ), ( offset, offset, 1 ) ) )
				deepResample["filter"].setValue( filter )
				deepResample["filterScale"].setValue( imath.V2f( filterScale ) )

				with self.subTest( scale = scale, filter = filter, filterScale = filterScale, name = image.node().getName() ) :
					# Most basic test - flattening the resampled deep should have the same result as
					# flattening and then resampling.
					if filter != "lanczos3":
						self.assertImagesEqual( flattenAfter["out"], flatResample["out"], maxDifference = 6e-6 )
					else:
						# A filter with negative lobes makes this test a bit more complicated. We need to compare
						# to a reference that has its alpha forced into a valid range ( by discarding pixels
						# with alpha < 0, and clamping pixels with alpha > 1 ).
						#
						# The negative lobes also result in alphas over 1, which makes the numerical precision
						# for the RGB channels much trickier - it's possible to reach an alpha of 1 before all
						# contributions are accounted for, which means that all remaining contributions must
						# be crammed into the last segment in order preserve the final result ... if the last
						# segment has low visibility, we end up having to put extremely high RGB values in
						# the last segment, resulting in poor precision. We could be a bit more specific in
						# this test about where this poor precision happens, but currently we just use a large
						# tolerance for everything.
						self.assertImagesEqual(
							flattenAfter["out"],
							flatResampleForceRange["out"],
							maxDifference = 5e-4
						)

					# Our output should always be tidy already
					self.assertImagesEqual( tidyAfterResample["out"], deepResample["out"] )

					# Now we need some sort of check that the shapes of the RGBA vs depth curves that we
					# output are correct. We do this by picking depths to check, and then comparing results
					# from doing a slice at that depth and resampling, vs slicing our resampled image
					# ( though unfortunately these tests aren't quite as simple as asserting the results
					# are identical )
					#
					# Since some of our tests have samples at integer depths, test specifically in the neighbourhood
					# of integer depths, then test at a bunch of random depths as well

					if filter == "lanczos3":
						# When using a filter with negative lobes, we need shift contributions in depth, because
						# we can only output valid deep segments where alpha is between 0 and 1. This requires
						# shifting contributions from negative areas backwards to the next positive part of the
						# curve, and shifting contributions from areas over one forwards to the segment where
						# it first reaches one. This means our depth based tests don't apply here, but we
						# we have validated that the negative lobed filter reaches the correct end value,
						# and in visual inspection, the results at various depths are reasonable, even though
						# it would be impossible to produce perfectly accurate results for negative lobes
						# ( since deep alpha must be non-decreasing ).
						continue

					for depth in (
						[ i + o for i in range( zStart, zEnd + 1) for o in [ -5e-7, 0, 5e-7 ] ] +
						[ random.uniform( zStart, zEnd ) for i in range( 10 ) ]
					):
						with self.subTest( scale = scale, filter = filter, filterScale = filterScale, name = image.node().getName(), depth = depth ) :
							sliceAfter["farClip"]["value"].setValue( depth )

							# By slicing first, and then doing a 2D resize, we can compute a totally accurate
							# reference. We only validate agains this on the top end, however, because
							# "curve shape discrepancy" can result in errors in the output of a deep Resample
							# which we deem acceptable.
							#
							# This is a somewhat complicated thing to describe, but it relates to how the
							# EXR spec that defines deep pixel interprets the way alpha increases throughout
							# a deep pixel as exponential fog. This means that the alpha value for a segment
							# determines both its final alpha value, and it's shape. Consider a pixel with
							# a volume segment with a very high alpha ( like 0.998 ) next to a pixel with
							# zero alpha. If you look at the curve shape of alpha vs depth of the volume segment,
							# you see a strong curve, with a very steep initial slope quickly curving to an
							# almost flat plateau ( since a very dense fog will absorb most light within a
							# small fraction of depth. Compare to a segment with alpha 0.499, which has half
							# the end value, but also a very different curve shape - it's close to a straight
							# line ( since lower density fog absorbs light more gradually ). If we wanted
							# to accurately represent a resampled pixel halfway between a 0.998 segment and zero,
							# it would have an end point of 0.499, but a strong curve with a steep initial
							# slope quickly reaching a plateau. This is not representable as a deep segment
							# according to the EXR spec. We could approximate the shape by splitting into a
							# series of shorter segments, each of which would be close to linear - this could
							# come close to accurately capturing the shape, but would increase complexity and
							# dramatically slowdown an already horribly slow operation.
							#
							# Instead, we classify it as legitimate to simply produce a volume segment with
							# alpha 0.499 as halfway between a 0.998 segment and zero. This has the correct
							# start and end points, and the shape of the curve is somewhere in between the
							# curve shapes of the nearby pixels. Visually, a close to opaque volume sample
							# will just get slightly less blur than it should while resampling, if evaluated
							# in the middle of its depth range.
							#
							# This does make testing a bit trickier, however, since we won't get an exact match
							# to the fully accurate version we get by picking a depth upfront, slicing first,
							# then resampling. To account for this, we compare with an upper bound to the fully
							# accurate slice, and a lower bound to a reference that is sliced first, but using
							# a linear curve shap ( the linear curve shape is achieved by using the depth
							# interpolation for segments with zero alpha, which is linear ). The output of
							# our algorithm should always be less than the accurate reference, and greater
							# than what an accurate reference would be if performed using linear interpolation
							# ( plus a bit of extra tolerance on each end to account for floating point error).

							self.assertImagesEqual(
								referenceSliceResampleAlphaOnly["out"], sliceAfterAlphaOnly["out"],
								maxDifference = ( -1, tolerance )
							)
							self.assertImagesEqual(
								linearReferenceSliceResample["out"], sliceAfterNoZ["out"],
								maxDifference = ( -5e-6, 1 )
							)

							# For the RGB channels, we have to allow error even above reference.
							# This is because the shape of the curve is determined by the alpha,
							# but it's possible for the sample with the most alpha, which drives the curve
							# shape, to not be the sample contributing most to this channel.
							# The curve can't get too wrong though, because you usually can't contribute a
							# lot of color without also contributing alpha - hence this error has a
							# tolerance of just 0.03, unlike the underflow in the first test above which
							# can reach 100% of alpha in extreme cases involving alphas very close to 1.
							# The test image "deepResampleRGBError.exr" illustrates the worst the case
							# I've been able to find for this error.
							self.assertImagesEqual(
								referenceSliceResampleNoZ["out"], sliceAfterNoZ["out"],
								maxDifference = ( -1, 0.03 )
							)

	def testDeepWithExceptionalValues( self ):

		# Similar to the test above, we make a deep image from these 4 layers, but this time, one of the
		# 4 layers will be given an unreasonable value for one of its channels. We don't test this
		# as thoroughly, since many of these situations aren't reasonable, but we want to make sure
		# that we at least don't crash.

		intPoints = GafferImage.ImageReader()
		intPoints["fileName"].setValue( self.deepIntPointsPath )
		intVolumes = GafferImage.ImageReader()
		intVolumes["fileName"].setValue( self.deepIntVolumesPath )
		floatPoints = GafferImage.ImageReader()
		floatPoints["fileName"].setValue( self.deepFloatPointsPath )
		floatVolumes = GafferImage.ImageReader()
		floatVolumes["fileName"].setValue( self.deepFloatVolumesPath )

		floatValues = GafferImage.ImageReader()
		floatValues["fileName"].setValue( self.floatValuesPath )

		floatValuesResize = GafferImage.Resize()
		floatValuesResize["in"].setInput( floatValues["out"] )
		floatValuesResize["format"].setValue( GafferImage.Format( 64, 64, 1.000 ) )
		floatValuesResize["filter"].setValue( 'nearest' )

		pickBadValue = GafferImage.Shuffle()
		pickBadValue["shuffles"].addChild( Gaffer.ShufflePlug( "shuffle0" ) )
		pickBadValue["in"].setInput( floatValuesResize["out"] )

		messUpFloatVolumes = GafferImage.CopyChannels()
		messUpFloatVolumes["in"][0].setInput( floatVolumes["out"] )
		messUpFloatVolumes["in"][1].setInput( pickBadValue["out"] )
		messUpFloatVolumes["channels"].setValue( '[RGBAZ] ZBack' )

		allCombined = GafferImage.DeepMerge( "allCombined" )
		allCombined["in"][0].setInput( intPoints["out"] )
		allCombined["in"][1].setInput( intVolumes["out"] )
		allCombined["in"][2].setInput( floatPoints["out"] )
		allCombined["in"][3].setInput( messUpFloatVolumes["out"] )

		centered = GafferImage.Offset()
		centered["in"].setInput( allCombined["out"] )
		centered["offset"].setValue( -allCombined["out"].dataWindow().center() )

		deepResample = GafferImage.Resample()
		deepResample["in"].setInput( centered["out"] )
		deepResample["filter"].setValue( "triangle" )
		deepResample["filterScale"].setValue( imath.V2f( 1.5 ) )
		deepResample["filterDeep"].setValue( True )

		postTidy = GafferImage.DeepTidy()
		postTidy["in"].setInput( deepResample["out"] )

		tidyAfterResample = GafferImage.DeepTidy()
		tidyAfterResample["in"].setInput( deepResample["out"] )

		flattenAfter = GafferImage.DeepToFlat()
		flattenAfter["in"].setInput( deepResample["out"] )
		# The filtered depth output from Flatten is affected enormously by curve shape discrepancy,
		# so we just won't check Z. The tests using DeepSlice are used to check the depth.
		flattenAfter['depthMode'].setValue( GafferImage.DeepToFlat.DepthMode.None_ )

		flattenBefore = GafferImage.DeepToFlat()
		flattenBefore["in"].setInput( centered["out"] )
		flattenBefore['depthMode'].setValue( GafferImage.DeepToFlat.DepthMode.None_ )

		flatResample = GafferImage.Resample()
		flatResample["in"].setInput( flattenBefore["out"] )
		flatResample["matrix"].setInput( deepResample["matrix"] )
		flatResample["filter"].setInput( deepResample["filter"] )
		flatResample["filterScale"].setInput( deepResample["filterScale"] )

		ignoredChannelsA = GafferImage.DeleteChannels()
		ignoredChannelsA["in"].setInput( flattenAfter["out"] )

		ignoredChannelsB = GafferImage.DeleteChannels()
		ignoredChannelsB["in"].setInput( flatResample["out"] )
		ignoredChannelsB["channels"].setInput( ignoredChannelsA["channels"] )

		for target in [ "G", "A", "Z", "ZBack" ]:
			for source in [ "infinity", "negativeInfinity", "nan", "zero", "negative", "overOne" ]:
				pickBadValue["shuffles"]["shuffle0"]["destination"].setValue( target )
				pickBadValue["shuffles"]["shuffle0"]["source"].setValue( source )

				maxDiff = 6e-6

				if target == "G" and source in ["infinity", "negativeInfinity" ]:
					# If a color channel is infinity, it doesn't really bother me that that channel ends up
					# getting set to NaN
					ignoredChannelsA["channels"].setValue( "G" )
				elif target == "A" and source == "nan":
					# I don't really care at all about what happens with an alpha of NaN, as long as we
					# don't crash, and output a tidy image.
					ignoredChannelsA["channels"].setValue( "*" )
				else:
					ignoredChannelsA["channels"].setValue( "" )

				if target == "Z" and source == "nan":
					# If Z is set to nan, we miss outputting that sample. That seems fine.
					maxDiff = 1.0

				with self.subTest( source = source, target = target ) :
					self.assertImagesEqual( deepResample["out"], postTidy["out"] )
					self.assertImagesEqual( ignoredChannelsA["out"], ignoredChannelsB["out"], maxDifference = maxDiff )

	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 3 )
	def testDeepPerformance( self ) :

		imageReader = GafferImage.ImageReader()
		imageReader["fileName"].setValue( self.representativeDeepImagePath )

		resample = GafferImage.Resample()
		resample["in"].setInput( imageReader["out"] )
		resample["filter"].setValue( 'box' )
		resample["filterScale"].setValue( imath.V2f( 3.0 ) )
		resample["filterDeep"].setValue( True )

		GafferImageTest.processTiles( imageReader["out"] )

		with GafferTest.TestRunner.PerformanceScope() :
			GafferImageTest.processTiles( resample["out"] )

	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 3 )
	def testDeepAlphaPerformance( self ) :

		imageReader = GafferImage.ImageReader()
		imageReader["fileName"].setValue( self.representativeDeepImagePath )

		deleteChannels = GafferImage.DeleteChannels()
		deleteChannels["in"].setInput( imageReader["out"] )
		deleteChannels["channels"].setValue( "R G B" )


		resample = GafferImage.Resample()
		resample["in"].setInput( deleteChannels["out"] )
		resample["filter"].setValue( 'box' )
		resample["filterScale"].setValue( imath.V2f( 3.0 ) )
		resample["filterDeep"].setValue( True )

		GafferImageTest.processTiles( deleteChannels["out"] )

		with GafferTest.TestRunner.PerformanceScope() :
			GafferImageTest.processTiles( resample["out"] )

if __name__ == "__main__":
	unittest.main()
