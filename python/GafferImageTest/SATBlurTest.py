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

class SATBlurTest( GafferImageTest.ImageTestCase ) :

	def testAgainstResample( self ) :

		imageReader = GafferImage.ImageReader()
		imageReader["fileName"].setValue( '${GAFFER_ROOT}/python/GafferImageTest/images/deepMergeReference.exr' )

		resample = GafferImage.Resample()
		resample["in"].setInput( imageReader["out"] )
		resample["filter"].setValue( 'box' )
		resample["filterScale"].setValue( imath.V2f( 7.0 ) )

		# The 'disk' mode of Resample is not anti-aliased, and treats a filterscale of 1 as a no-op ( to start
		# adding blur you have to set filterScale >1. We can match this by cranking up the approximationThreshold
		# to disable anti-aliasing, and setting the radius corresponding to a diameter to one less than the filterScale.
		satBlur = GafferImage.SATBlur()
		satBlur["in"].setInput( imageReader["out"] )
		satBlur["radius"].setValue( imath.V2f( 3.0 ) )

		self.assertImagesEqual( satBlur["out"], resample["out"], maxDifference = 1e-4 )

		resample["filterScale"].setValue( imath.V2f( 21.0 ) )
		satBlur["radius"].setValue( imath.V2f( 10.0 ) )

		self.assertImagesEqual( satBlur["out"], resample["out"], maxDifference = 1e-4 )

	def testMaxRadius( self ) :

		imageReader = GafferImage.ImageReader()
		imageReader["fileName"].setValue( '${GAFFER_ROOT}/python/GafferImageTest/images/deepMergeReference.exr' )

		satBlur = GafferImage.SATBlur()
		satBlur["in"].setInput( imageReader["out"] )
		satBlur["radius"].setValue( imath.V2f( 100 ) )
		satBlur["maxRadius"].setValue( 20 )

		satBlurRef = GafferImage.SATBlur()
		satBlurRef["in"].setInput( imageReader["out"] )
		satBlurRef["radius"].setValue( imath.V2f( 20 ) )

		# Setting the maxRadius to something lower than the radius has the same effect as setting the radius
		# lower ( the difference just being the performance benefit to lowering maxRadius )
		self.assertImagesEqual( satBlur["out"], satBlurRef["out"], maxDifference = 0 )

	def testDiskApproximation( self ) :

		imageReader = GafferImage.ImageReader()
		imageReader["fileName"].setValue( '${GAFFER_ROOT}/python/GafferImageTest/images/deepMergeReference.exr' )

		satBlur = GafferImage.SATBlur()
		satBlur["in"].setInput( imageReader["out"] )
		satBlur["radius"].setValue( imath.V2f( 20 ) )

		rotate = GafferImage.ImageTransform()
		rotate["in"].setInput( imageReader["out"] )
		rotate["transform"]["rotate"].setValue( 45.0 )

		satBlurRotated = GafferImage.SATBlur()
		satBlurRotated["in"].setInput( rotate["out"] )
		satBlurRotated["radius"].setValue( imath.V2f( 20.0 ) )

		rotateBack = GafferImage.ImageTransform()
		rotateBack["in"].setInput( satBlurRotated["out"] )
		rotateBack["transform"]["rotate"].setValue( -45.0 )


		difference = GafferImage.Merge()
		difference["operation"].setValue( GafferImage.Merge.Operation.Difference )
		difference["in"][0].setInput( satBlur["out"] )
		difference["in"][1].setInput( rotateBack["out"] )

		stats = GafferImage.ImageStats()
		stats["in"].setInput( difference["out"] )
		# Use the original dataWindow as the region to compare
		stats["area"].setValue( imath.Box2i( imath.V2i( -58, -46 ), imath.V2i( 150, 111 ) ) )

		# Using a box filter results in substantial difference in filter shape after a 45 degree rotation
		self.assertAlmostEqual( stats["max"]["r"].getValue(), 0.08, delta = 0.02 )
		self.assertAlmostEqual( stats["max"]["g"].getValue(), 0.08, delta = 0.02 )
		self.assertAlmostEqual( stats["max"]["b"].getValue(), 0.08, delta = 0.02 )
		self.assertAlmostEqual( stats["max"]["a"].getValue(), 0.08, delta = 0.02 )

		# Using an approximate disk filter gives similar results for either orientation
		satBlur["filter"].setValue( "disk" )
		satBlur["diskRectangles"].setValue( 5 )
		satBlurRotated["filter"].setValue( "disk" )
		satBlurRotated["diskRectangles"].setValue( 5 )

		self.assertAlmostEqual( stats["max"]["r"].getValue(), 0.025, delta = 0.013 )
		self.assertAlmostEqual( stats["max"]["g"].getValue(), 0.025, delta = 0.013 )
		self.assertAlmostEqual( stats["max"]["b"].getValue(), 0.025, delta = 0.013 )
		self.assertAlmostEqual( stats["max"]["a"].getValue(), 0.025, delta = 0.013 )

		# Using a better approximation improves the match
		satBlur["diskRectangles"].setValue( 25 )
		satBlurRotated["diskRectangles"].setValue( 25 )

		self.assertAlmostEqual( stats["max"]["r"].getValue(), 0.006, delta = 0.003 )
		self.assertAlmostEqual( stats["max"]["g"].getValue(), 0.006, delta = 0.003 )
		self.assertAlmostEqual( stats["max"]["b"].getValue(), 0.006, delta = 0.003 )
		self.assertAlmostEqual( stats["max"]["a"].getValue(), 0.006, delta = 0.003 )

	def testVariableRadius( self ) :

		# As a gathering blur, using a different radius for different pixels is the same as blending
		# between different images that were blurred with each radius. We can check this by using a
		# Mix to prepare an image with different radii, versus using a Mix on two different SatBlurs

		imageReader = GafferImage.ImageReader()
		imageReader["fileName"].setValue( '${GAFFER_ROOT}/python/GafferImageTest/images/deepMergeReference.exr' )

		maskReader = GafferImage.ImageReader()
		maskReader["fileName"].setValue( '${GAFFER_ROOT}/python/GafferImageTest/images/noisyBlobs.exr' )

		maskOffset = GafferImage.Offset()
		maskOffset["in"].setInput( maskReader["out"] )
		maskOffset["offset"].setValue( imath.V2i( -60, -60 ) )

		maskAlpha = GafferImage.Shuffle()
		maskAlpha["shuffles"].addChild( Gaffer.ShufflePlug( "shuffle0", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
		maskAlpha["in"].setInput( maskOffset["out"] )
		maskAlpha["shuffles"]["shuffle0"]["source"].setValue( 'Y' )
		maskAlpha["shuffles"]["shuffle0"]["destination"].setValue( 'A' )

		# Partial blends of results is not the same as using a blended radius - we grade the mask so
		# it is pure black and white
		makeMaskBinary = GafferImage.Grade()
		makeMaskBinary["in"].setInput( maskAlpha["out"] )
		makeMaskBinary["channels"].setValue( '[A]' )
		makeMaskBinary["blackPoint"].setValue( imath.Color4f( 0, 0, 0, 0.5 ) )
		makeMaskBinary["whitePoint"].setValue( imath.Color4f( 1, 1, 1, 0.500100017 ) )

		satBlurA = GafferImage.SATBlur()
		satBlurA["in"].setInput( imageReader["out"] )
		satBlurA["radius"].setValue( imath.V2f( 3.0 ) )

		satBlurB = GafferImage.SATBlur()
		satBlurB["in"].setInput( imageReader["out"] )
		satBlurB["radius"].setValue( imath.V2f( 20.0 ) )

		mixResult = GafferImage.Mix()
		mixResult["in"][0].setInput( satBlurA["out"] )
		mixResult["in"][1].setInput( satBlurB["out"] )
		mixResult["mask"].setInput( makeMaskBinary["out"] )

		createRadius = GafferImage.Shuffle()
		createRadius["shuffles"].addChild( Gaffer.ShufflePlug( "shuffle0", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
		createRadius["in"].setInput( imageReader["out"] )
		createRadius["shuffles"]["shuffle0"]["source"].setValue( '__white' )
		createRadius["shuffles"]["shuffle0"]["destination"].setValue( 'radius' )

		gradeRadiusA = GafferImage.Grade()
		gradeRadiusA["in"].setInput( createRadius["out"] )
		gradeRadiusA["channels"].setValue( 'radius' )
		gradeRadiusA["multiply"].setValue( imath.Color4f( 3, 1, 1, 1 ) )

		gradeRadiusB = GafferImage.Grade()
		gradeRadiusB["in"].setInput( createRadius["out"] )
		gradeRadiusB["channels"].setValue( 'radius' )
		gradeRadiusB["multiply"].setValue( imath.Color4f( 20, 1, 1, 1 ) )

		mixRadius = GafferImage.Mix()
		mixRadius["in"][0].setInput( gradeRadiusA["out"] )
		mixRadius["in"][1].setInput( gradeRadiusB["out"] )
		mixRadius["mask"].setInput( makeMaskBinary["out"] )

		satBlurVariableRadius = GafferImage.SATBlur()
		satBlurVariableRadius["in"].setInput( mixRadius["out"] )
		satBlurVariableRadius["radiusChannel"].setValue( 'radius' )
		satBlurVariableRadius["radius"].setValue( imath.V2f( 1.0 ) )

		deleteRadius = GafferImage.DeleteChannels()
		deleteRadius["in"].setInput( satBlurVariableRadius["out"] )
		deleteRadius["channels"].setValue( "radius" )

		self.assertImagesEqual( mixResult["out"], deleteRadius["out"], maxDifference = 0 )

		# Test with a disk kernel as well.
		satBlurA["filter"].setValue( "disk" )
		satBlurA["diskRectangles"].setValue( 9 )
		satBlurB["filter"].setValue( "disk" )
		satBlurB["diskRectangles"].setValue( 9 )
		satBlurVariableRadius["filter"].setValue( "disk" )
		satBlurVariableRadius["diskRectangles"].setValue( 9 )

		self.assertImagesEqual( mixResult["out"], deleteRadius["out"], maxDifference = 0 )

		# There's a special case when radius is 0 that should pass through, so test setting
		# half the radii to 0, and disabling the corresponding component blur
		satBlurA["enabled"].setValue( False )
		gradeRadiusA["multiply"].setValue( imath.Color4f( 0, 1, 1, 1 ) )

		# The tolerance required is rather high, but this is consistent with using 32 bit floats to store
		# a summed area table for tens of thousands of pixels per tile. The current precision seems fine
		# for FocalBlur infilling, but if we want to use this more widely, we should like add support for
		# double precision.
		self.assertImagesEqual( mixResult["out"], deleteRadius["out"], maxDifference = 0.002 )

	def testDataWindow( self ) :
		# Many of our image sources set the pixels outside the data window to black anyway, so there would
		# be no error introduced by reading pixels outside the data window, but this is incorrect.
		# We can test this using a Constant as a source, which sets the pixels for all tiles to a constant,
		# indepedent of the data window.


		constant = GafferImage.Constant()
		constant["color"].setValue( imath.Color4f( 1, 0, 1, 1 ) )

		satBlur = GafferImage.SATBlur()
		satBlur["in"].setInput( constant["out"] )
		satBlur["radius"].setValue( imath.V2f( 10.0 ) )

		resample = GafferImage.Resample()
		resample["in"].setInput( constant["out"] )
		resample["filter"].setValue( 'box' )
		resample["filterScale"].setValue( imath.V2f( 21.0 ) )

		for bound in [
			( imath.V2i( 0, 0 ), imath.V2i( 50, 50 ) ),
			( imath.V2i( 0, 0 ), imath.V2i( 100, 100 ) ),
			( imath.V2i( 33, 51 ), imath.V2i( 70, 113 ) ),
			( imath.V2i( 133, 151 ), imath.V2i( 170, 213 ) )
		]:
			with self.subTest( bound = bound ):
				constant["format"].setValue( GafferImage.Format( imath.Box2i( bound[0], bound[1] ), 1.000 ) )

				resample["boundingMode"].setValue( GafferImage.Sampler.BoundingMode.Black )
				satBlur["boundingMode"].setValue( GafferImage.SATBlur.BoundingMode.Black )

				self.assertImagesEqual( satBlur["out"], resample["out"], maxDifference = 5e-7 )

				# Clamp and normalize are not identical, but they both have the same effect on a constant
				# image, exactly removing any falloff on the edges
				resample["boundingMode"].setValue( GafferImage.Sampler.BoundingMode.Clamp )
				satBlur["boundingMode"].setValue( GafferImage.SATBlur.BoundingMode.Normalize )

				self.assertImagesEqual( satBlur["out"], resample["out"], maxDifference = 2e-7 )

	def testMultilayer( self ) :

		imageReader = GafferImage.ImageReader()
		imageReader["fileName"].setValue( '${GAFFER_ROOT}/python/GafferImageTest/images/deepMergeReference.exr' )

		crop = GafferImage.Crop()
		crop["in"].setInput( imageReader["out"] )
		crop["area"].setValue( imath.Box2i( imath.V2i( 0, 0 ), imath.V2i( 100, 100 ) ) )

		depthRamp = GafferImage.Ramp()
		depthRamp["format"].setValue( GafferImage.Format( 100, 100, 1.000 ) )
		depthRamp["endPosition"].setValue( imath.V2f( 100, 0 ) )
		depthRamp["ramp"]["p0"]["y"].setValue( imath.Color4f( -0.5, 0, 0, 0 ) )
		depthRamp["ramp"]["p1"]["y"].setValue( imath.Color4f( 1.5, 1, 1, 1 ) )
		depthRamp["layer"].setValue( 'depth' )

		copyDepth = GafferImage.CopyChannels( "copyDepth" )
		copyDepth["in"][0].setInput( crop["out"] )
		copyDepth["in"][1].setInput( depthRamp["out"] )
		copyDepth["channels"].setValue( 'depth.[R]' )

		createDepthLookup = GafferImage.Shuffle( "createDepthLookup" )
		createDepthLookup["in"].setInput( copyDepth["out"] )
		createDepthLookup["shuffles"].addChild( Gaffer.ShufflePlug( "shuffle0", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
		createDepthLookup["shuffles"]["shuffle0"]["source"].setValue( '__white' )
		createDepthLookup["shuffles"]["shuffle0"]["destination"].setValue( 'depthLookup' )

		gradeDepthLookup = GafferImage.Grade( "gradeDepthLookup" )
		gradeDepthLookup["in"].setInput( createDepthLookup["out"] )
		gradeDepthLookup["channels"].setValue( 'depthLookup' )

		satBlur = GafferImage.SATBlur( "satBlur" )
		satBlur["in"].setInput( gradeDepthLookup["out"] )
		satBlur["depthChannel"].setValue( 'depth.R' )
		satBlur["depthLookupChannel"].setValue( 'depthLookup' )
		satBlur["layerBoundaries"].setValue( IECore.FloatVectorData( [ i * 0.1 for i in range( 11 ) ] ) )

		deleteChannels = GafferImage.DeleteChannels()
		deleteChannels["in"].setInput( satBlur["out"] )
		deleteChannels["channels"].setValue( "depth.R depthLookup" )


		referenceMask = GafferImage.Ramp( "referenceMask" )
		referenceMask["format"].setValue( GafferImage.Format( 100, 100, 1.000 ) )
		referenceMask["endPosition"].setValue( imath.V2f( 100, 0 ) )
		referenceMask["ramp"]["interpolation"].setValue( 4 )
		referenceMask["ramp"].addChild( Gaffer.ValuePlug( "p2" ) )
		referenceMask["ramp"]["p2"].addChild( Gaffer.FloatPlug( "x" ) )
		referenceMask["ramp"]["p2"].addChild( Gaffer.Color4fPlug( "y" ) )

		referenceMultiply = GafferImage.Merge( "reference" )
		referenceMultiply["in"].resize( 3 )
		referenceMultiply["in"][0].setInput( crop["out"] )
		referenceMultiply["in"][1].setInput( referenceMask["out"] )
		referenceMultiply["operation"].setValue( GafferImage.Merge.Operation.Multiply )

		referenceBlur = GafferImage.Resample( "referenceBlur" )
		referenceBlur["in"].setInput( referenceMultiply["out"] )
		referenceBlur["filter"].setValue( 'box' )
		referenceBlur["filterScale"].setValue( imath.V2f( 5.0 ) )


		testWriter = GafferImage.ImageWriter()
		testWriter["fileName"].setValue( "/tmp/test.exr" )
		testWriter["in"].setInput( deleteChannels["out"] )

		testWriter.execute()

		for radius in [ 0, 1, 3 ]:
			with self.subTest( radius = radius ):
				satBlur["radius"].setValue( imath.V2f( radius ) )
				referenceBlur["filterScale"].setValue( imath.V2f( 1.0 + 2 * radius ) )

				tolerance = 2e-3 if radius == 0 else 2e-4

				# For depths less than the first plane, everything is visible
				gradeDepthLookup["multiply"].setValue( imath.Color4f( -0.5, 1, 1, 1 ) )
				referenceMultiply["enabled"].setValue( False )

				self.assertImagesEqual( deleteChannels["out"], referenceBlur["out"], maxDifference = tolerance * 1.5 )

				# The last depth where we still include everything
				gradeDepthLookup["multiply"].setValue( imath.Color4f( 0.001, 1, 1, 1 ) )
				referenceMultiply["enabled"].setValue( False )

				self.assertImagesEqual( deleteChannels["out"], referenceBlur["out"], maxDifference = tolerance * 1.5 )

				gradeDepthLookup["multiply"].setValue( imath.Color4f( 0.05, 1, 1, 1 ) )
				referenceMultiply["enabled"].setValue( True )
				referenceMask["ramp"]["p2"]["x"].setValue( 0.0 )
				referenceMask["ramp"]["p1"]["x"].setValue( 0.3 )
				referenceMask["ramp"]["p2"]["y"].setValue( imath.Color4f( 0.51 ) )

				self.assertImagesEqual( deleteChannels["out"], referenceBlur["out"], maxDifference = tolerance )

				# The way things align with depths isn't quite precise, because I've currently got a 1% depth
				# bias - we don't want the contribution of something to drop all the way to 0 at it's own depth,
				# we only want to exclude things behind that depth. So the contribution of the first segment is
				# still 1% when we set the depth lookup to 0.1, and it only drops to 0 at a depth lookup of
				# 0.101
				gradeDepthLookup["multiply"].setValue( imath.Color4f( 0.1, 1, 1, 1 ) )

				referenceMask["ramp"]["p2"]["x"].setValue( 0.0 )
				referenceMask["ramp"]["p1"]["x"].setValue( 0.3 )
				referenceMask["ramp"]["p2"]["y"].setValue( imath.Color4f( 0.01 ) )

				self.assertImagesEqual( deleteChannels["out"], referenceBlur["out"], maxDifference = tolerance )

				gradeDepthLookup["multiply"].setValue( imath.Color4f( 0.101, 1, 1, 1 ) )

				referenceMask["ramp"]["p2"]["x"].setValue( 0.0 )
				referenceMask["ramp"]["p1"]["x"].setValue( 0.3 )
				referenceMask["ramp"]["p2"]["y"].setValue( imath.Color4f( 0.0 ) )

				self.assertImagesEqual( deleteChannels["out"], referenceBlur["out"], maxDifference = tolerance )

				# Now increase depth so the first band is completely omitted, and the second band is half omitted
				gradeDepthLookup["multiply"].setValue( imath.Color4f( 0.15, 1, 1, 1 ) )

				referenceMask["ramp"]["p2"]["x"].setValue( 0.3 )
				referenceMask["ramp"]["p1"]["x"].setValue( 0.35 )
				referenceMask["ramp"]["p2"]["y"].setValue( imath.Color4f( 0.51 ) )

				self.assertImagesEqual( deleteChannels["out"], referenceBlur["out"], maxDifference = tolerance )

				# Now the second band is completely omitted
				gradeDepthLookup["multiply"].setValue( imath.Color4f( 0.201, 1, 1, 1 ) )

				referenceMask["ramp"]["p2"]["x"].setValue( 0.0 )
				referenceMask["ramp"]["p1"]["x"].setValue( 0.35 )
				referenceMask["ramp"]["p2"]["y"].setValue( imath.Color4f( 0.0 ) )

				self.assertImagesEqual( deleteChannels["out"], referenceBlur["out"], maxDifference = tolerance )

				# Random depth in the middle

				gradeDepthLookup["multiply"].setValue( imath.Color4f( 0.57, 1, 1, 1 ) )

				referenceMultiply["enabled"].setValue( True )
				referenceMask["ramp"]["p2"]["x"].setValue( 0.5 )
				referenceMask["ramp"]["p1"]["x"].setValue( 0.55 )
				referenceMask["ramp"]["p2"]["y"].setValue( imath.Color4f( 0.31 ) )

				self.assertImagesEqual( deleteChannels["out"], referenceBlur["out"], maxDifference = tolerance )

				# Starting to fade out the 0.9 layer

				gradeDepthLookup["multiply"].setValue( imath.Color4f( 0.95, 1, 1, 1 ) )

				referenceMultiply["enabled"].setValue( True )
				referenceMask["ramp"]["p2"]["x"].setValue( 0.7 )
				referenceMask["ramp"]["p1"]["x"].setValue( 0.75 )
				referenceMask["ramp"]["p2"]["y"].setValue( imath.Color4f( 0.51 ) )

				self.assertImagesEqual( deleteChannels["out"], referenceBlur["out"], maxDifference = tolerance )

				# The 0.9 layer is almost all faded out, aside from the depth bias

				gradeDepthLookup["multiply"].setValue( imath.Color4f( 1, 1, 1, 1 ) )

				referenceMultiply["enabled"].setValue( True )
				referenceMask["ramp"]["p2"]["x"].setValue( 0.7 )
				referenceMask["ramp"]["p1"]["x"].setValue( 0.75 )
				referenceMask["ramp"]["p2"]["y"].setValue( imath.Color4f( 0.01 ) )

				self.assertImagesEqual( deleteChannels["out"], referenceBlur["out"], maxDifference = tolerance )

				# Now past everything, except the final layer, which never fades

				gradeDepthLookup["multiply"].setValue( imath.Color4f( 1.01, 1, 1, 1 ) )

				referenceMultiply["enabled"].setValue( True )
				referenceMask["ramp"]["p2"]["x"].setValue( 0.0 )
				referenceMask["ramp"]["p1"]["x"].setValue( 0.75 )
				referenceMask["ramp"]["p2"]["y"].setValue( imath.Color4f( 0 ) )

				self.assertImagesEqual( deleteChannels["out"], referenceBlur["out"], maxDifference = tolerance )

				gradeDepthLookup["multiply"].setValue( imath.Color4f( 10, 1, 1, 1 ) )

				self.assertImagesEqual( deleteChannels["out"], referenceBlur["out"], maxDifference = tolerance )

	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 1 )
	def testPerfHuge( self ) :

		imageReader = GafferImage.ImageReader()
		imageReader["fileName"].setValue( "${GAFFER_ROOT}/resources/images/macaw.exr" )

		satBlur = GafferImage.SATBlur()
		satBlur["in"].setInput( imageReader["out"] )
		satBlur["radius"].setValue( imath.V2f( 250 ) )

		GafferImageTest.processTiles( satBlur["in"] )

		with GafferTest.TestRunner.PerformanceScope() :
			GafferImageTest.processTiles( satBlur["out"] )

	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 1 )
	def testPerfMedium( self ) :

		imageReader = GafferImage.ImageReader()
		imageReader["fileName"].setValue( "${GAFFER_ROOT}/resources/images/macaw.exr" )

		satBlur = GafferImage.SATBlur()
		satBlur["in"].setInput( imageReader["out"] )
		satBlur["radius"].setValue( imath.V2f( 25 ) )

		GafferImageTest.processTiles( satBlur["in"] )

		with GafferTest.TestRunner.PerformanceScope() :
			GafferImageTest.processTiles( satBlur["out"] )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testPerfSmall( self ) :

		imageReader = GafferImage.ImageReader()
		imageReader["fileName"].setValue( "${GAFFER_ROOT}/resources/images/macaw.exr" )

		satBlur = GafferImage.SATBlur()
		satBlur["in"].setInput( imageReader["out"] )
		satBlur["radius"].setValue( imath.V2f( 2 ) )

		GafferImageTest.processTiles( satBlur["in"] )

		with GafferTest.TestRunner.PerformanceScope() :
			GafferImageTest.processTiles( satBlur["out"] )

	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 1 )
	def testPerfSmallTightBound( self ) :

		imageReader = GafferImage.ImageReader()
		imageReader["fileName"].setValue( "${GAFFER_ROOT}/resources/images/macaw.exr" )

		satBlur = GafferImage.SATBlur()
		satBlur["in"].setInput( imageReader["out"] )
		satBlur["radius"].setValue( imath.V2f( 2 ) )

		# With a small radius, turning down the maxRadius improves performance measurably
		# ( Though the actual blur is still more expensive than setting up tiles )
		satBlur["maxRadius"].setValue( 32 )

		GafferImageTest.processTiles( satBlur["in"] )

		with GafferTest.TestRunner.PerformanceScope() :
			GafferImageTest.processTiles( satBlur["out"] )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testPerfTiny( self ) :

		imageReader = GafferImage.ImageReader()
		imageReader["fileName"].setValue( "${GAFFER_ROOT}/resources/images/macaw.exr" )

		satBlur = GafferImage.SATBlur()
		satBlur["in"].setInput( imageReader["out"] )
		satBlur["radius"].setValue( imath.V2f( 0.5 ) )

		GafferImageTest.processTiles( satBlur["in"] )

		with GafferTest.TestRunner.PerformanceScope() :
			GafferImageTest.processTiles( satBlur["out"] )

	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 1 )
	def testPerfMediumDisk( self ) :

		imageReader = GafferImage.ImageReader()
		imageReader["fileName"].setValue( "${GAFFER_ROOT}/resources/images/macaw.exr" )

		satBlur = GafferImage.SATBlur()
		satBlur["in"].setInput( imageReader["out"] )
		satBlur["radius"].setValue( imath.V2f( 25 ) )
		satBlur["filter"].setValue( "disk" )
		satBlur["diskRectangles"].setValue( 9 )

		GafferImageTest.processTiles( satBlur["in"] )

		with GafferTest.TestRunner.PerformanceScope() :
			GafferImageTest.processTiles( satBlur["out"] )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testPerfTinyDisk( self ) :

		imageReader = GafferImage.ImageReader()
		imageReader["fileName"].setValue( "${GAFFER_ROOT}/resources/images/macaw.exr" )

		satBlur = GafferImage.SATBlur()
		satBlur["in"].setInput( imageReader["out"] )
		satBlur["radius"].setValue( imath.V2f( 0.5 ) )
		satBlur["filter"].setValue( "disk" )
		satBlur["diskRectangles"].setValue( 9 )

		GafferImageTest.processTiles( satBlur["in"] )

		with GafferTest.TestRunner.PerformanceScope() :
			GafferImageTest.processTiles( satBlur["out"] )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testPerfZero( self ) :

		imageReader = GafferImage.ImageReader()
		imageReader["fileName"].setValue( "${GAFFER_ROOT}/resources/images/macaw.exr" )

		# Using a 0 radius uses a special case that shouldn't apply any blur, but for
		# consistency, it still reconstructs pixels from the SAT

		satBlur = GafferImage.SATBlur()
		satBlur["in"].setInput( imageReader["out"] )
		satBlur["radius"].setValue( imath.V2f( 0 ) )
		# Using an accurate disk approximation won't affect performance when the radius is 0
		satBlur["filter"].setValue( "disk" )
		satBlur["diskRectangles"].setValue( 9 )

		GafferImageTest.processTiles( satBlur["in"] )

		with GafferTest.TestRunner.PerformanceScope() :
			GafferImageTest.processTiles( satBlur["out"] )

if __name__ == "__main__":
	unittest.main()
