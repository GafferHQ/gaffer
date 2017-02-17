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

import IECore

import Gaffer
import GafferTest
import GafferImage
import GafferImageTest

class UVWarpTest( GafferImageTest.ImageTestCase ) :
	def testConstructor( self ) :

		w = GafferImage.UVWarp()
		self.assertTrue( isinstance( w, GafferImage.UVWarp ) )

	def testFormatAndDataWindow( self ) :

		texture = GafferImage.Constant()
		texture["format"].setValue( GafferImage.Format( 100, 100 ) )

		uv = GafferImage.Constant()
		uv["format"].setValue( GafferImage.Format( 200, 200 ) )

		warp = GafferImage.UVWarp()
		warp["in"].setInput( texture["out"] )
		warp["uv"].setInput( uv["out"] )

		self.assertEqual( warp["out"]["format"].getValue(), uv["out"]["format"].getValue() )
		self.assertEqual( warp["out"]["dataWindow"].getValue(), uv["out"]["dataWindow"].getValue() )

	def testUVWarp( self ) :

		reader = GafferImage.ImageReader()
		reader["fileName"].setValue( os.path.dirname( __file__ ) + "/images/checker2x2.exr" )

		# Constant provides the same UV across the board
		# for the UVWarp uv input.
		constant = GafferImage.Constant()

		uvWarp = GafferImage.UVWarp()
		uvWarp["in"].setInput( reader["out"] )
		uvWarp["uv"].setInput( constant["out"] )
		uvWarp["filter"].setValue( "box" )

		# We can then sample the input image at the
		# same UV position.
		sampler1 = GafferImage.ImageSampler()
		sampler1["image"].setInput( reader["out"] )

		# And compare it to an arbitrary pixel in the
		# (constant) warped output.
		sampler2 = GafferImage.ImageSampler()
		sampler2["image"].setInput( uvWarp["out"] )
		sampler2["pixel"].setValue( IECore.V2f( 5.5 ) )

		for u in ( 0.0, 0.25, 0.5, 0.75, 1.0 ) :
			for v in ( 0.0, 0.25, 0.5, 0.75, 1.0 ) :
				constant["color"].setValue( IECore.Color4f( u, v, 0, 1 ) )
				sampler1["pixel"].setValue( IECore.V2f( u * 2, v * 2 ) )
				self.assertEqual( sampler1["color"].getValue(), sampler2["color"].getValue() )

	def testNegativeDataWindowOrigin( self ) :

		reader = GafferImage.ImageReader()
		reader["fileName"].setValue( os.path.dirname( __file__ ) + "/images/checker.exr" )

		constant = GafferImage.Constant()
		constant["color"].setValue( IECore.Color4f( 0.5, 0, 0, 1 ) )

		offset = GafferImage.Offset()
		offset["in"].setInput( constant["out"] )
		offset["offset"].setValue( IECore.V2i( -200, -250 ) )

		uvWarp = GafferImage.UVWarp()
		uvWarp["in"].setInput( reader["out"] )
		uvWarp["uv"].setInput( offset["out"] )

		GafferImageTest.processTiles( uvWarp["out"] )

	def testWarpImage( self ):
		def __warpImage( size, distortion ):
			w = IECore.Box2i( IECore.V2i( 0 ), size - IECore.V2i( 1 ) )
			image = IECore.ImagePrimitive( w, w )

			R = IECore.FloatVectorData( size.x * size.y )
			G = IECore.FloatVectorData( size.x * size.y )

			for iy in range( size.y ):
				for ix in range( size.x ):
					x = (ix + 0.5) / size.x 
					y = 1 - (iy + 0.5) / size.y
					R[ iy * size.x + ix ] = x + distortion * math.sin( y * 8 )
					G[ iy * size.x + ix ] = y + distortion * math.sin( x * 8 )

			image["R"] = IECore.PrimitiveVariable( IECore.PrimitiveVariable.Interpolation.Vertex, R )
			image["G"] = IECore.PrimitiveVariable( IECore.PrimitiveVariable.Interpolation.Vertex, G )

			return image

		def __dotGrid( size ):
			w = IECore.Box2i( IECore.V2i( 0 ), size - IECore.V2i( 1 ) )
			image = IECore.ImagePrimitive( w, w )

			R = IECore.FloatVectorData( size.x * size.y )
			G = IECore.FloatVectorData( size.x * size.y )
			B = IECore.FloatVectorData( size.x * size.y )

			for iy in range( 0, size.y ):
				for ix in range( 0, size.x ):
					q = max( ix % 16, iy % 16 )
					
					R[ iy * size.x + ix ] = q < 1
					G[ iy * size.x + ix ] = q < 4
					B[ iy * size.x + ix ] = q < 8

			image["R"] = IECore.PrimitiveVariable( IECore.PrimitiveVariable.Interpolation.Vertex, R )
			image["G"] = IECore.PrimitiveVariable( IECore.PrimitiveVariable.Interpolation.Vertex, G )
			image["B"] = IECore.PrimitiveVariable( IECore.PrimitiveVariable.Interpolation.Vertex, B )

			return image


		objectToImageSource = GafferImage.ObjectToImage()
		objectToImageSource["object"].setValue( __dotGrid( IECore.V2i( 300 ) ) )

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

		uvWarp = GafferImage.UVWarp()
		uvWarp["in"].setInput( sourceReorder["out"] )
		uvWarp["uv"].setInput( objectToImageVector["out"] )

		# Test that a warp with no distortion and a box filter reproduces the input
		objectToImageVector["object"].setValue( __warpImage( IECore.V2i( 300 ), 0 ) )
		uvWarp["filter"].setValue( "box" )
		self.assertImagesEqual( uvWarp["out"], sourceReorder["out"], maxDifference = 0.00001 )

		# Test that a warp with distortion produces an expected output
		objectToImageVector["object"].setValue( __warpImage( IECore.V2i( 300 ), 0.2 ) )
		uvWarp["filter"].setValue( "blackman-harris" )

		# Enable to write out images for visual comparison
		if False:
			testWriter = GafferImage.ImageWriter()
			testWriter["in"].setInput( uvWarp["out"] )
			testWriter["fileName"].setValue( "/tmp/dotGrid.warped.exr" )
			testWriter["task"].execute()

		expectedReader = GafferImage.ImageReader()
		expectedReader["fileName"].setValue( os.path.dirname( __file__ ) + "/images/dotGrid.warped.exr" )

		self.assertImagesEqual( uvWarp["out"], expectedReader["out"], maxDifference = 0.0005, ignoreMetadata = True )
		

if __name__ == "__main__":
	unittest.main()
