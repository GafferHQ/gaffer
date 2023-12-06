##########################################################################
#
#  Copyright (c) 2023 Image Engine Design Inc. All rights reserved.
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
import random

import IECore

import Gaffer
import GafferImage
import GafferImageTest

class DeepSliceTest( GafferImageTest.ImageTestCase ) :

	def testBasics( self ) :

		# Set up 3 segments in primary colors with depth ranges 1-2, 3-4, 5-6

		constantRed = GafferImage.Constant()
		constantRed["format"].setValue( GafferImage.Format( 32, 32, 1.000 ) )
		constantRed["color"].setValue( imath.Color4f( 0.5, 0, 0, 0.5 ) )

		constantGreen = GafferImage.Constant()
		constantGreen["format"].setValue( GafferImage.Format( 32, 32, 1.000 ) )
		constantGreen["color"].setValue( imath.Color4f( 0, 0.5, 0, 0.5 ) )

		constantBlue = GafferImage.Constant()
		constantBlue["format"].setValue( GafferImage.Format( 32, 32, 1.000 ) )
		constantBlue["color"].setValue( imath.Color4f( 0, 0, 0.5, 0.5 ) )

		flatToDeep1 = GafferImage.FlatToDeep()
		flatToDeep1["in"].setInput( constantRed["out"] )
		flatToDeep1["depth"].setValue( 1.0 )
		flatToDeep1["zBackMode"].setValue( 1 )
		flatToDeep1["thickness"].setValue( 1.0 )

		flatToDeep2 = GafferImage.FlatToDeep()
		flatToDeep2["in"].setInput( constantGreen["out"] )
		flatToDeep2["depth"].setValue( 3.0 )
		flatToDeep2["zBackMode"].setValue( 1 )
		flatToDeep2["thickness"].setValue( 1.0 )

		flatToDeep3 = GafferImage.FlatToDeep()
		flatToDeep3["in"].setInput( constantBlue["out"] )
		flatToDeep3["depth"].setValue( 5.0 )
		flatToDeep3["zBackMode"].setValue( 1 )
		flatToDeep3["thickness"].setValue( 1.0 )

		deepMerge = GafferImage.DeepMerge()
		deepMerge["in"][0].setInput( flatToDeep1["out"] )
		deepMerge["in"][1].setInput( flatToDeep2["out"] )
		deepMerge["in"][2].setInput( flatToDeep3["out"] )

		deepSlice = GafferImage.DeepSlice()
		deepSlice["in"].setInput( constantRed["out"] )
		deepSlice["flatten"].setValue( False )

		deepSliceFlatten = GafferImage.DeepSlice()
		deepSliceFlatten["in"].setInput( constantRed["out"] )
		deepSliceFlatten["flatten"].setValue( True )

		flatten = GafferImage.DeepToFlat()
		flatten["in"].setInput( deepSlice["out"] )
		flatten["depthMode"].setValue( GafferImage.DeepToFlat.DepthMode.Range )

		sampler = GafferImage.DeepSampler()
		sampler["image"].setInput( deepSlice["out"] )

		# Run a test with specified near and far clips, based on what we expect for the 3 segments we've
		# set up.
		# The expected Z values are computed based on
		# the given values, but the expected alpha and color values are computed based on the given
		# expectedWeights, specifying the fraction of each sample that is taken.
		# We could compute expectedWeights based some simple computations, but I think it makes it more
		# obivous what we're testing to hardcode the expectedWeights for each test.
		def sliceTest( nearClip, nearClipDepth, farClip, farClipDepth, expectedWeights ):
			deepSlice["nearClip"]["enabled"].setValue( nearClip )
			deepSlice["nearClip"]["value"].setValue( nearClipDepth )
			deepSlice["farClip"]["enabled"].setValue( farClip )
			deepSlice["farClip"]["value"].setValue( farClipDepth )
			deepSliceFlatten["nearClip"]["enabled"].setValue( nearClip )
			deepSliceFlatten["nearClip"]["value"].setValue( nearClipDepth )
			deepSliceFlatten["farClip"]["enabled"].setValue( farClip )
			deepSliceFlatten["farClip"]["value"].setValue( farClipDepth )

			self.assertImagesEqual( deepSliceFlatten["out"], flatten["out"], maxDifference = 1e-7 )

			pd = sampler["pixelData"].getValue()

			if expectedWeights == [ None, None, None ]:
				self.assertEqual( pd, IECore.CompoundData() )
				return

			self.assertEqual( pd["R"], IECore.FloatVectorData( [ 0.5 * w * c for w, c in zip( expectedWeights, [ 1, 0, 0 ] ) if not w is None ] ) )
			self.assertEqual( pd["G"], IECore.FloatVectorData( [ 0.5 * w * c for w, c in zip( expectedWeights, [ 0, 1, 0 ] ) if not w is None ] ) )
			self.assertEqual( pd["B"], IECore.FloatVectorData( [ 0.5 * w * c for w, c in zip( expectedWeights, [ 0, 0, 1 ] ) if not w is None ] ) )
			self.assertEqual( pd["A"], IECore.FloatVectorData( [ 0.5 * w for w in expectedWeights if not w is None] ) )
			self.assertEqual( pd["Z"], IECore.FloatVectorData( [
				max( nearClipDepth, z ) if nearClip else z
				for w, z in zip( expectedWeights, [ 1, 3, 5 ] ) if not w is None
			] ) )
			self.assertEqual( pd["ZBack"], IECore.FloatVectorData( [
				min( farClipDepth, z ) if farClip else z
				for w, z in zip( expectedWeights, [ 2, 4, 6 ] ) if not w is None
			] ) )

		with self.assertRaisesRegex( RuntimeError, "DeepSlice requires a Z channel" ) :
			sliceTest( False, 0, False, 0, [ 1, None, None ] )

		# Compute the multiplier we need of a segment with 50% alpha in order to split it in half,
		# so that the two halves composite back to the original. It's more than 50% because of
		# how alpha compositing works - if we used 50%, we would get a total of:
		# 0.25 + ( 1 - 0.25 ) * 0.25 == 0.4375. So instead we use this math, which results in a value
		# of about 58%, which then accumulates to exactly 0.5
		halfSeg = ( 1 - 0.5 ** 0.5 ) / 0.5


		# Test with only one segment hooked up

		deepSlice["in"].setInput( flatToDeep1["out"] )
		deepSliceFlatten["in"].setInput( flatToDeep1["out"] )

		sliceTest( False, 0, False, 0, [ 1, None, None ] )
		sliceTest( False, 1.5, False, 1.5, [ 1, None, None ] )
		sliceTest( True, 1.5, False, 1.5, [ halfSeg, None, None ] )
		sliceTest( False, 1.5, True, 1.5, [ halfSeg, None, None ] )
		sliceTest( True, 1.5, True, 1.5, [ 0, None, None ] )


		# Create a flat image with the first segment in it, but with valid Z and ZBack,
		# so we can check we do something reasonable with a flat input
		oneSegmentFlat = GafferImage.DeepToFlat()
		oneSegmentFlat["in"].setInput( flatToDeep1["out"] )
		oneSegmentFlat["depthMode"].setValue( GafferImage.DeepToFlat.DepthMode.Range )

		deepSlice["in"].setInput( oneSegmentFlat["out"] )
		deepSliceFlatten["in"].setInput( oneSegmentFlat["out"] )

		# Results should be identical to the "deep" image produced by flatToDeep
		sliceTest( False, 0, False, 0, [ 1, None, None ] )
		sliceTest( False, 1.5, False, 1.5, [ 1, None, None ] )
		sliceTest( True, 1.5, False, 1.5, [ halfSeg, None, None ] )
		sliceTest( False, 1.5, True, 1.5, [ halfSeg, None, None ] )
		sliceTest( True, 1.5, True, 1.5, [ 0, None, None ] )


		# Now hook up all 3 segments through the DeepMerge
		deepSlice["in"].setInput( deepMerge["out"] )
		deepSliceFlatten["in"].setInput( deepMerge["out"] )

		# Toggle near/far on and off
		sliceTest( False, 1.5, False, 1.5, [ 1, 1, 1 ] )
		sliceTest( True, 1.5, False, 1.5, [ halfSeg, 1, 1 ] )
		sliceTest( False, 1.5, True, 1.5, [ halfSeg, None, None ] )
		sliceTest( True, 1.5, True, 1.5, [ 0, None, None ] )

		# Test many near clip values
		sliceTest( True, 0, False, 1.5, [ 1, 1, 1 ] )
		sliceTest( True, 1, False, 1.5, [ 1, 1, 1 ] )
		sliceTest( True, 1.5, False, 1.5, [ halfSeg, 1, 1 ] )
		sliceTest( True, 2, False, 1.5, [ None, 1, 1 ] )
		sliceTest( True, 3, False, 1.5, [ None, 1, 1 ] )
		sliceTest( True, 3.5, False, 1.5, [ None, halfSeg, 1 ] )
		sliceTest( True, 4, False, 1.5, [ None, None, 1 ] )
		sliceTest( True, 5, False, 1.5, [ None, None, 1 ] )
		sliceTest( True, 5.5, False, 1.5, [ None, None, halfSeg ] )
		sliceTest( True, 6, False, 1.5, [ None, None, None ] )
		sliceTest( True, 7, False, 1.5, [ None, None, None ] )

		# Test many far clip values
		sliceTest( False, 1.5, True, 0, [ None, None, None ] )
		sliceTest( False, 1.5, True, 1, [ None, None, None ] )
		sliceTest( False, 1.5, True, 1.0000001, [ 1.6525917e-7, None, None ] )
		sliceTest( False, 1.5, True, 1.5, [ halfSeg, None, None ] )
		sliceTest( False, 1.5, True, 2, [ 1, None, None ] )
		sliceTest( False, 1.5, True, 3, [ 1, None, None ] )
		sliceTest( False, 1.5, True, 3.0000002, [ 1, 3.305183e-7, None ] )
		sliceTest( False, 1.5, True, 3.5, [ 1, halfSeg, None ] )
		sliceTest( False, 1.5, True, 4, [ 1, 1, None ] )
		sliceTest( False, 1.5, True, 5, [ 1, 1, None ] )
		sliceTest( False, 1.5, True, 5.0000004, [ 1, 1, 6.6103655e-07 ] )
		sliceTest( False, 1.5, True, 5.5, [ 1, 1, halfSeg ] )
		sliceTest( False, 1.5, True, 6, [ 1, 1, 1 ] )

		# Handle zero length segments in node, or in tests ( Handle in tests using None )
		# Test both clips here
		# Test point samples at 1.25 and 1.75
		sliceTest( True, 3.5, True, 3.5, [ None, 0, None ] )
		sliceTest( True, 1.5, True, 3.5, [ halfSeg, halfSeg, None ] )
		sliceTest( True, 3.5, True, 5.5, [ None, halfSeg, halfSeg ] )
		sliceTest( True, 2, True, 5, [ None, 1, None ] )
		sliceTest( True, 2, True, 5.0000004, [ None, 1, 6.6103655e-07 ] )
		sliceTest( True, 1.5, True, 5.5, [ halfSeg, 1, halfSeg ] )
		sliceTest( True, 1, True, 6, [ 1, 1, 1 ] )

	# Compare a lot of possible slices to a reference implementation using a slower "generate a holdout image
	# then DeepHoldout" approach.
	def testBruteForce( self ) :

		representativeImagePath = GafferImageTest.ImageTestCase.imagesPath() / "representativeDeepImage.exr"
		deepIntPointsPath = GafferImageTest.ImageTestCase.imagesPath() / "deepIntPoints.exr"
		deepIntVolumesPath = GafferImageTest.ImageTestCase.imagesPath() / "deepIntVolumes.exr"
		deepFloatPointsPath = GafferImageTest.ImageTestCase.imagesPath() / "deepFloatPoints.exr"
		deepFloatVolumesPath = GafferImageTest.ImageTestCase.imagesPath() / "deepFloatVolumes.exr"

		representativeImage = GafferImage.ImageReader( "representativeDeep" )
		representativeImage["fileName"].setValue( representativeImagePath )
		intPoints = GafferImage.ImageReader()
		intPoints["fileName"].setValue( deepIntPointsPath )
		intVolumes = GafferImage.ImageReader()
		intVolumes["fileName"].setValue( deepIntVolumesPath )
		floatPoints = GafferImage.ImageReader()
		floatPoints["fileName"].setValue( deepFloatPointsPath )
		floatVolumes = GafferImage.ImageReader()
		floatVolumes["fileName"].setValue( deepFloatVolumesPath )

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

		testImage = GafferImage.ImagePlug()

		formatQuery = GafferImage.FormatQuery()
		formatQuery["image"].setInput( testImage )

		sliceNear = GafferImage.DeepSlice()
		sliceNear["in"].setInput( testImage )
		sliceNear["nearClip"]["enabled"].setValue( False )
		sliceNear["farClip"]["enabled"].setValue( True )
		sliceNear["flatten"].setValue( False )

		flattenedNear = GafferImage.DeepToFlat()
		flattenedNear["in"].setInput( sliceNear["out"] )
		flattenedNear["depthMode"].setValue( GafferImage.DeepToFlat.DepthMode.Range )

		flatSliceNear = GafferImage.DeepSlice()
		flatSliceNear["in"].setInput( testImage )
		flatSliceNear["nearClip"]["enabled"].setValue( False )
		flatSliceNear["farClip"]["enabled"].setValue( True )
		flatSliceNear["farClip"]["value"].setInput( sliceNear["farClip"]["value"] )
		flatSliceNear["flatten"].setValue( True )

		sliceFar = GafferImage.DeepSlice()
		sliceFar["in"].setInput( testImage )
		sliceFar["nearClip"]["enabled"].setValue( True )
		sliceFar["farClip"]["enabled"].setValue( False )
		sliceFar["flatten"].setValue( False )

		flattenedFar = GafferImage.DeepToFlat()
		flattenedFar["in"].setInput( sliceFar["out"] )
		flattenedFar["depthMode"].setValue( GafferImage.DeepToFlat.DepthMode.Range )

		flatSliceFar = GafferImage.DeepSlice()
		flatSliceFar["in"].setInput( testImage )
		flatSliceFar["nearClip"]["enabled"].setValue( True )
		flatSliceFar["nearClip"]["value"].setInput( sliceFar["nearClip"]["value"] )
		flatSliceFar["farClip"]["enabled"].setValue( False )
		flatSliceFar["flatten"].setValue( True )

		sliceMiddle = GafferImage.DeepSlice()
		sliceMiddle["in"].setInput( testImage )
		sliceMiddle["nearClip"]["enabled"].setValue( True )
		sliceMiddle["farClip"]["enabled"].setValue( True )
		sliceMiddle["flatten"].setValue( False )

		flattenedMiddle = GafferImage.DeepToFlat()
		flattenedMiddle["in"].setInput( sliceMiddle["out"] )
		flattenedMiddle["depthMode"].setValue( GafferImage.DeepToFlat.DepthMode.Range )

		flatSliceMiddle = GafferImage.DeepSlice()
		flatSliceMiddle["in"].setInput( testImage )
		flatSliceMiddle["nearClip"]["enabled"].setValue( True )
		flatSliceMiddle["nearClip"]["value"].setInput( sliceMiddle["nearClip"]["value"] )
		flatSliceMiddle["farClip"]["enabled"].setValue( True )
		flatSliceMiddle["farClip"]["value"].setInput( sliceMiddle["farClip"]["value"] )
		flatSliceMiddle["flatten"].setValue( True )

		flattenedInput = GafferImage.DeepToFlat()
		flattenedInput["in"].setInput( testImage )
		flattenedInput["depthMode"].setValue( GafferImage.DeepToFlat.DepthMode.None_ )

		flatSliceNearWithoutDepth = GafferImage.DeleteChannels()
		flatSliceNearWithoutDepth["in"].setInput( flatSliceNear["out"] )
		flatSliceNearWithoutDepth["channels"].setValue( "Z ZBack" )

		flatSliceFarWithoutDepth = GafferImage.DeleteChannels()
		flatSliceFarWithoutDepth["in"].setInput( flatSliceFar["out"] )
		flatSliceFarWithoutDepth["channels"].setValue( "Z ZBack" )

		flatSliceMiddleWithoutDepth = GafferImage.DeleteChannels()
		flatSliceMiddleWithoutDepth["in"].setInput( flatSliceMiddle["out"] )
		flatSliceMiddleWithoutDepth["channels"].setValue( "Z ZBack" )

		nearOverFar = GafferImage.Merge()
		nearOverFar["operation"].setValue( GafferImage.Merge.Operation.Over )
		nearOverFar["in"][0].setInput( flatSliceFarWithoutDepth["out"] )
		nearOverFar["in"][1].setInput( flatSliceNearWithoutDepth["out"] )

		nearOverMiddleOverFar = GafferImage.Merge()
		nearOverMiddleOverFar["operation"].setValue( GafferImage.Merge.Operation.Over )
		nearOverMiddleOverFar["in"][0].setInput( flatSliceFarWithoutDepth["out"] )
		nearOverMiddleOverFar["in"][1].setInput( flatSliceMiddleWithoutDepth["out"] )
		nearOverMiddleOverFar["in"][2].setInput( flatSliceNearWithoutDepth["out"] )

		tidyInput = GafferImage.DeepTidy()
		tidyInput["in"].setInput( testImage )

		sampleCountsInput = GafferImage.DeepSampleCounts()
		sampleCountsInput["in"].setInput( tidyInput["out"] )

		sampleCountsNear = GafferImage.DeepSampleCounts()
		sampleCountsNear["in"].setInput( sliceNear["out"] )

		sampleCountsFar = GafferImage.DeepSampleCounts()
		sampleCountsFar["in"].setInput( sliceFar["out"] )

		sampleCountsMiddle = GafferImage.DeepSampleCounts()
		sampleCountsMiddle["in"].setInput( sliceMiddle["out"] )

		sampleCountsNearFar = GafferImage.Merge()
		sampleCountsNearFar["operation"].setValue( GafferImage.Merge.Operation.Add )
		sampleCountsNearFar["in"][0].setInput( sampleCountsNear["out"] )
		sampleCountsNearFar["in"][1].setInput( sampleCountsFar["out"] )

		sampleCountsNearMiddleFar = GafferImage.Merge()
		sampleCountsNearMiddleFar["operation"].setValue( GafferImage.Merge.Operation.Add )
		sampleCountsNearMiddleFar["in"][0].setInput( sampleCountsNear["out"] )
		sampleCountsNearMiddleFar["in"][1].setInput( sampleCountsMiddle["out"] )
		sampleCountsNearMiddleFar["in"][2].setInput( sampleCountsFar["out"] )

		tidyNear = GafferImage.DeepTidy()
		tidyNear["in"].setInput( sliceNear["out"] )

		tidyFar = GafferImage.DeepTidy()
		tidyFar["in"].setInput( sliceFar["out"] )

		tidyMiddle = GafferImage.DeepTidy()
		tidyMiddle["in"].setInput( sliceMiddle["out"] )

		holdoutConstant = GafferImage.Constant()
		holdoutConstant["format"].setInput( formatQuery["format"] )

		holdoutDepth = GafferImage.FlatToDeep()
		holdoutDepth["in"].setInput( holdoutConstant["out"] )

		holdout = GafferImage.DeepHoldout()
		holdout["in"].setInput( testImage )
		holdout["holdout"].setInput( holdoutDepth["out"] )

		holdoutWithoutDepth = GafferImage.DeleteChannels()
		holdoutWithoutDepth["in"].setInput( holdout["out"] )
		holdoutWithoutDepth["channels"].setValue( "Z ZBack" )

		random.seed( 42 )

		for image, zStart, zEnd in [
			( allInts["out"], 0, 4 ),
			( allFloats["out"], 0, 4 ),
			( allCombined["out"], 0, 4 ),
			( representativeImage["out"], 4, 11 ),
		]:
			testImage.setInput( image )

			# Since some of our tests have samples at integer depths, test specifically in the neighbourhood
			# of integer depths, then test at a bunch of random depths as well
			for depth in (
				[ i + o for i in range( zStart, zEnd + 1) for o in [ -5e-7, 0, 5e-7 ] ] +
				[ random.uniform( zStart, zEnd ) for i in range( 20 ) ]
			):
				with self.subTest( mode = "Near/Far", name = image.node().getName(), depth = depth ) :
					sliceNear["farClip"]["value"].setValue( depth )
					sliceFar["nearClip"]["value"].setValue( depth )

					# The output from DeepSlice should always be tidy, which we can validate by making
					# sure tidying has no effect
					self.assertImagesEqual( tidyNear["out"], sliceNear["out"] )
					self.assertImagesEqual( tidyFar["out"], sliceFar["out"] )

					# Check that the flat output from DeepSlice matches with what we get by flattening
					# the deep output
					self.assertImagesEqual( flattenedNear["out"], flatSliceNear["out"], maxDifference = 1e-6 )
					self.assertImagesEqual( flattenedFar["out"], flatSliceFar["out"], maxDifference = 1e-6 )


					# Check that we match with passing an image containing a constant depth into DeepHoldout
					holdoutDepth["depth"].setValue( depth )
					try:
						self.assertImagesEqual( flatSliceNearWithoutDepth["out"], holdoutWithoutDepth["out"], maxDifference = 3e-5 )
					except:
						# We handle point samples exactly at the threshold a little bit differently than
						# this DeepHoldout approach - the holdout is doing a DeepMerge with a black image with
						# a point sample at a fixed depth at each pixel, so the fraction of a point sample
						# exactly at the cutoff depth that comes through depends on the EXR logic for merging
						# samples ( since the cutoff image is opaque, you get 50% of an opaque sample, or 0% of
						# a non-opaque sample ).
						#
						# Our logic is different: we exclude all samples at the cutoff for farClipDepth,
						# and we include samples at the cutoff for nearClipDepth. This ensures that using
						# two DeepSlices to split an image at a particular depth, and then re-compositing it,
						# gives you something that matches the original.
						#
						# Because of this difference, in order to get the tests passing, we just shift the
						# holdout depth slightly nearer in order to get a matching result from the holdout.
						holdoutDepth["depth"].setValue( depth - 5e-7 )
						self.assertImagesEqual( flatSliceNearWithoutDepth["out"], holdoutWithoutDepth["out"], maxDifference = 3e-5 )

					# Check that using DeepSlice to take everything before a depth, and using DeepSlice to
					# take everything after a depth, results in 2 images that composite together to match
					# the original
					self.assertImagesEqual( nearOverFar["out"], flattenedInput["out"], maxDifference = 4e-6 )

					# Check that sample counts of the two slices are reasonable. The sum should be no less than
					# the original sample counts, and no more than 1 greater ( since if a sample is split by
					# the depth, it will appear in both )
					self.assertImagesEqual(
						sampleCountsInput["out"], sampleCountsNearFar["out"], maxDifference = (0,1)
					)

			# Run a few more tests when we're taking a middle slice by clipping both near and far
			for a, b in ( ( random.uniform( zStart, zEnd ), random.uniform( zStart, zEnd ) ) for i in range( 20 ) ):
				with self.subTest( mode = "Middle", name = image.node().getName(), depth = depth ) :
					nearDepth = min( a, b )
					farDepth = max( a, b )
					sliceNear["farClip"]["value"].setValue( nearDepth )
					sliceMiddle["nearClip"]["value"].setValue( nearDepth )
					sliceMiddle["farClip"]["value"].setValue( farDepth )
					sliceFar["nearClip"]["value"].setValue( farDepth )

					# Check that the flat output from DeepSlice matches with what we get by flattening
					# the deep output
					self.assertImagesEqual( flattenedMiddle["out"], flatSliceMiddle["out"], maxDifference = 1e-6 )

					# The output from DeepSlice should always be tidy, which we can validate by making
					# sure tidying has no effect
					self.assertImagesEqual( tidyMiddle["out"], sliceMiddle["out"] )

					# Check that compositing the middle slice with the part before and after it gives
					# us the original
					self.assertImagesEqual( nearOverMiddleOverFar["out"], flattenedInput["out"], maxDifference = 4e-6 )

					# Check that sample counts of the three slices are reasonable. The sum should be no less than
					# the original sample counts, and no more than 2 greater ( since both clipping depths
					# could split a sample )
					self.assertImagesEqual(
						sampleCountsInput["out"], sampleCountsNearMiddleFar["out"], maxDifference = (0,2)
					)

if __name__ == "__main__":
	unittest.main()
