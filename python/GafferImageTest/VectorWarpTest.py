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
		def __warpImage( size, distortion, idistortStyle ):
			w = imath.Box2i( imath.V2i( 0 ), size - imath.V2i( 1 ) )
			image = IECoreImage.ImagePrimitive( w, w )

			R = IECore.FloatVectorData( size.x * size.y )
			G = IECore.FloatVectorData( size.x * size.y )

			for iy in range( size.y ):
				for ix in range( size.x ):
					x = (ix + 0.5) / size.x
					y = 1 - (iy + 0.5) / size.y
					if idistortStyle:
						R[ iy * size.x + ix ] = distortion * math.sin( y * 8 ) * size.x
						G[ iy * size.x + ix ] = distortion * math.sin( x * 8 ) * size.y
					else:
						R[ iy * size.x + ix ] = x + distortion * math.sin( y * 8 )
						G[ iy * size.x + ix ] = y + distortion * math.sin( x * 8 )


			image["R"] = R
			image["G"] = G

			return image

		def __dotGrid( size ):
			w = imath.Box2i( imath.V2i( 0 ), size - imath.V2i( 1 ) )
			image = IECoreImage.ImagePrimitive( w, w )

			R = IECore.FloatVectorData( size.x * size.y )
			G = IECore.FloatVectorData( size.x * size.y )
			B = IECore.FloatVectorData( size.x * size.y )

			for iy in range( 0, size.y ):
				for ix in range( 0, size.x ):
					q = max( ix % 16, iy % 16 )

					R[ iy * size.x + ix ] = q < 1
					G[ iy * size.x + ix ] = q < 4
					B[ iy * size.x + ix ] = q < 8

			image["R"] = R
			image["G"] = G
			image["B"] = B

			return image


		objectToImageSource = GafferImage.ObjectToImage()
		objectToImageSource["object"].setValue( __dotGrid( imath.V2i( 300 ) ) )

		# TODO - reorder channels of our source image because ObjectToImage outputs in opposite order to
		# the rest of Gaffer.  This probably should be fixed in ObjectToImage,
		# or we shouldn't depend on channel order to check if images are equal?
		sourceReorderConstant = GafferImage.Constant()
		sourceReorderConstant["format"].setValue( GafferImage.Format( 300, 300, 1.000 ) )
		sourceReorderDelete = GafferImage.DeleteChannels()
		sourceReorderDelete["channels"].setValue( IECore.StringVectorData( [ "A" ] ) )
		sourceReorderDelete["in"].setInput( sourceReorderConstant["out"] )
		sourceReorder = GafferImage.CopyChannels()
		sourceReorder["channels"].setValue( "R G B" )
		sourceReorder["in"]["in0"].setInput( sourceReorderDelete["out"] )
		sourceReorder["in"]["in1"].setInput( objectToImageSource["out"] )

		objectToImageVector = GafferImage.ObjectToImage()

		vectorWarp = GafferImage.VectorWarp()
		vectorWarp["in"].setInput( sourceReorder["out"] )
		vectorWarp["vector"].setInput( objectToImageVector["out"] )

		# Test that a warp with no distortion and a box filter reproduces the input
		objectToImageVector["object"].setValue( __warpImage( imath.V2i( 300 ), 0, False ) )
		vectorWarp["filter"].setValue( "box" )
		self.assertImagesEqual( vectorWarp["out"], sourceReorder["out"], maxDifference = 0.00001 )

		# Test that a warp with distortion produces an expected output
		objectToImageVector["object"].setValue( __warpImage( imath.V2i( 300 ), 0.2, False ) )
		vectorWarp["filter"].setValue( "blackman-harris" )

		# Enable to write out images for visual comparison
		if False:
			testWriter = GafferImage.ImageWriter()
			testWriter["in"].setInput( vectorWarp["out"] )
			testWriter["fileName"].setValue( "/tmp/dotGrid.warped.exr" )
			testWriter["task"].execute()

		expectedReader = GafferImage.ImageReader()
		expectedReader["fileName"].setValue( os.path.dirname( __file__ ) + "/images/dotGrid.warped.exr" )

		# Test that we can get the same result using pixel offsets instead of normalized coordinates
		objectToImageVector["object"].setValue( __warpImage( imath.V2i( 300 ), 0.2, True ) )
		vectorWarp["vectorMode"].setValue( GafferImage.VectorWarp.VectorMode.Relative )
		vectorWarp["vectorUnits"].setValue( GafferImage.VectorWarp.VectorUnits.Pixels )

		self.assertImagesEqual( vectorWarp["out"], expectedReader["out"], maxDifference = 0.0005, ignoreMetadata = True )


if __name__ == "__main__":
	unittest.main()
