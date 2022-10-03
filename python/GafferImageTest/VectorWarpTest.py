##########################################################################
#
#  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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
import math
import imath

import IECore
import IECoreImage

import Gaffer
import GafferTest
import GafferImage
import GafferImageTest

class VectorWarpTest( GafferImageTest.ImageTestCase ) :
	def testConstructor( self ) :

		w = GafferImage.VectorWarp()
		self.assertTrue( isinstance( w, GafferImage.VectorWarp ) )

	def testFormatAndDataWindow( self ) :

		texture = GafferImage.Constant()
		texture["format"].setValue( GafferImage.Format( 100, 100 ) )

		vector = GafferImage.Constant()
		vector["format"].setValue( GafferImage.Format( 200, 200 ) )

		warp = GafferImage.VectorWarp()
		warp["in"].setInput( texture["out"] )
		warp["vector"].setInput( vector["out"] )

		self.assertEqual( warp["out"]["format"].getValue(), vector["out"]["format"].getValue() )
		self.assertEqual( warp["out"]["dataWindow"].getValue(), vector["out"]["dataWindow"].getValue() )

	def testVectorWarp( self ) :

		reader = GafferImage.ImageReader()
		reader["fileName"].setValue( os.path.dirname( __file__ ) + "/images/checker2x2.exr" )

		# Constant provides the same Vector across the board
		# for the VectorWarp vector input.
		constant = GafferImage.Constant()

		vectorWarp = GafferImage.VectorWarp()
		vectorWarp["in"].setInput( reader["out"] )
		vectorWarp["vector"].setInput( constant["out"] )
		vectorWarp["filter"].setValue( "box" )

		# We can then sample the input image at the
		# same Vector position.
		sampler1 = GafferImage.ImageSampler()
		sampler1["image"].setInput( reader["out"] )

		# And compare it to an arbitrary pixel in the
		# (constant) warped output.
		sampler2 = GafferImage.ImageSampler()
		sampler2["image"].setInput( vectorWarp["out"] )
		sampler2["pixel"].setValue( imath.V2f( 5.5 ) )

		for u in ( 0.0, 0.25, 0.5, 0.75, 1.0 ) :
			for v in ( 0.0, 0.25, 0.5, 0.75, 1.0 ) :
				constant["color"].setValue( imath.Color4f( u, v, 0, 1 ) )
				sampler1["pixel"].setValue( imath.V2f( u * 2, v * 2 ) )
				self.assertEqual( sampler1["color"].getValue(), sampler2["color"].getValue() )

	def testNegativeDataWindowOrigin( self ) :

		reader = GafferImage.ImageReader()
		reader["fileName"].setValue( os.path.dirname( __file__ ) + "/images/checker.exr" )

		constant = GafferImage.Constant()
		constant["color"].setValue( imath.Color4f( 0.5, 0, 0, 1 ) )

		offset = GafferImage.Offset()
		offset["in"].setInput( constant["out"] )
		offset["offset"].setValue( imath.V2i( -200, -250 ) )

		vectorWarp = GafferImage.VectorWarp()
		vectorWarp["in"].setInput( reader["out"] )
		vectorWarp["vector"].setInput( offset["out"] )

		GafferImageTest.processTiles( vectorWarp["out"] )

	def testWarpImage( self ):
		dotGridReader = GafferImage.ImageReader()
		dotGridReader["fileName"].setValue( os.path.dirname( __file__ ) + "/images/dotGrid.300.exr" )

		vectorWarp = GafferImage.VectorWarp()
		vectorWarp["in"].setInput( dotGridReader["out"] )

		# Test that a warp with no distortion and a box filter reproduces the input

		xRamp = GafferImage.Ramp()
		xRamp["format"].setValue( GafferImage.Format( 300, 300 ) )
		xRamp["endPosition"].setValue( imath.V2f( 300, 0 ) )
		xRamp["ramp"]["p1"]["y"].setValue( imath.Color4f( 1, 0, 0, 1 ) )
		yRamp = GafferImage.Ramp()
		yRamp["format"].setValue( GafferImage.Format( 300, 300 ) )
		yRamp["endPosition"].setValue( imath.V2f( 0, 300 ) )
		yRamp["ramp"]["p1"]["y"].setValue( imath.Color4f( 0, 1, 0, 1 ) )

		toAbsoluteMerge = GafferImage.Merge()
		toAbsoluteMerge["operation"].setValue( GafferImage.Merge.Operation.Add )
		toAbsoluteMerge["in"]["in0"].setInput( xRamp["out"] )
		toAbsoluteMerge["in"]["in1"].setInput( yRamp["out"] )
		vectorWarp["vector"].setInput( toAbsoluteMerge["out"] )

		vectorWarp["filter"].setValue( "box" )
		self.assertImagesEqual( vectorWarp["out"], dotGridReader["out"], maxDifference = 0.00001 )

		# Test that a warp with distortion produces an expected output
		warpPatternReader = GafferImage.ImageReader()
		warpPatternReader["fileName"].setValue( os.path.dirname( __file__ ) + "/images/warpPattern.exr" )

		toAbsoluteMerge["in"]["in2"].setInput( warpPatternReader["out"] )

		vectorWarp["filter"].setValue( "blackman-harris" )
		vectorWarp["vector"].setInput( toAbsoluteMerge["out"] )

		expectedReader = GafferImage.ImageReader()
		expectedReader["fileName"].setValue( os.path.dirname( __file__ ) + "/images/dotGrid.warped.exr" )
		self.assertImagesEqual( vectorWarp["out"], expectedReader["out"], maxDifference = 0.0005, ignoreMetadata = True )

		# Test that we can get the same result using pixel offsets instead of normalized coordinates

		toPixelsGrade = GafferImage.Grade()
		toPixelsGrade["in"].setInput( warpPatternReader["out"] )
		toPixelsGrade["blackClamp"].setValue( False )
		toPixelsGrade["multiply"].setValue( imath.Color4f( 300 ) )

		vectorWarp["vector"].setInput( toPixelsGrade["out"] )
		vectorWarp["vectorMode"].setValue( GafferImage.VectorWarp.VectorMode.Relative )
		vectorWarp["vectorUnits"].setValue( GafferImage.VectorWarp.VectorUnits.Pixels )

		self.assertImagesEqual( vectorWarp["out"], expectedReader["out"], maxDifference = 0.0005, ignoreMetadata = True )


if __name__ == "__main__":
	unittest.main()
