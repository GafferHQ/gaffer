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
#      * Neither the name of Image Engine Design nor the names of
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

import IECore

import Gaffer
import GafferImage
import GafferImageTest

class SamplerTest( GafferImageTest.ImageTestCase ) :

	fileName = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/checker.exr" )

	def testOutOfBoundsSampleModeBlack( self ) :

		c = GafferImage.Constant()
		c["color"].setValue( IECore.Color4f( 1 ) )

		dw = c["out"]["dataWindow"].getValue();
		s = GafferImage.Sampler( c["out"], "R", dw, GafferImage.Sampler.BoundingMode.Black )

		# Check integer sampling.
		#########################

		# Pixels on corners of dataWindow should be white.

		self.assertEqual( s.sample( dw.min.x, dw.min.y ), 1 )
		self.assertEqual( s.sample( dw.max.x - 1, dw.min.y ), 1 )
		self.assertEqual( s.sample( dw.max.x - 1, dw.max.y - 1 ), 1 )
		self.assertEqual( s.sample( dw.min.x, dw.max.y - 1 ), 1 )

		# Pixels just outside dataWindow should be white.

		self.assertEqual( s.sample( dw.min.x - 1, dw.min.y - 1 ), 0 )
		self.assertEqual( s.sample( dw.max.x, dw.min.y - 1 ), 0 )
		self.assertEqual( s.sample( dw.max.x, dw.max.y ), 0 )
		self.assertEqual( s.sample( dw.min.x - 1, dw.max.y ), 0 )

		# Check interpolated sampling.
		##############################

		# Pixels on corners of dataWindow should be interpolating
		# to black. Note that here we're sampling at the corners
		# of pixels, not centers.

		self.assertEqual( s.sample( float( dw.min.x ), float( dw.min.y ) ), 0.25 )
		self.assertEqual( s.sample( float( dw.max.x ), float( dw.min.y ) ), 0.25 )
		self.assertEqual( s.sample( float( dw.max.x ), float( dw.max.y ) ), 0.25 )
		self.assertEqual( s.sample( float( dw.min.x ), float( dw.max.y ) ), 0.25 )

		# Pixel centers at the corners of dataWindow should be white.

		self.assertEqual( s.sample( float( dw.min.x + 0.5 ), float( dw.min.y + 0.5 ) ), 1 )
		self.assertEqual( s.sample( float( dw.max.x - 0.5 ), float( dw.min.y + 0.5 ) ), 1 )
		self.assertEqual( s.sample( float( dw.max.x - 0.5 ), float( dw.max.y - 0.5 ) ), 1 )
		self.assertEqual( s.sample( float( dw.min.x + 0.5 ), float( dw.max.y - 0.5 ) ), 1 )

	def testOutOfBoundsSampleModeClamp( self ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.fileName )

		dw = r["out"]["dataWindow"].getValue();
		s = GafferImage.Sampler( r["out"], "R", dw, GafferImage.Sampler.BoundingMode.Clamp )

		# Get the exact values of the corner pixels.
		bl = s.sample( dw.min.x, dw.min.y )
		br = s.sample( dw.max.x - 1, dw.min.y  )
		tr = s.sample( dw.max.x - 1, dw.max.y - 1 )
		tl = s.sample( dw.min.x, dw.max.y - 1 )

		# Sample out of bounds and assert that the same value as the nearest pixel is returned.
		self.assertEqual( s.sample( dw.min.x-1, dw.min.y ), bl )
		self.assertEqual( s.sample( dw.min.x, dw.min.y-1 ), bl )
		self.assertEqual( s.sample( dw.max.x-1, dw.max.y ), tr )
		self.assertEqual( s.sample( dw.max.x, dw.max.y-1 ), tr )
		self.assertEqual( s.sample( dw.min.x-1, dw.max.y-1 ), tl )
		self.assertEqual( s.sample( dw.min.x, dw.max.y ), tl )
		self.assertEqual( s.sample( dw.max.x, dw.min.y ), br )
		self.assertEqual( s.sample( dw.max.x-1, dw.min.y-1 ), br )

	def test2x2Checker( self ) :

		reader = GafferImage.ImageReader()
		reader["fileName"].setValue( os.path.dirname( __file__ ) + "/images/checker2x2.exr" )

		# As long as the sample region includes the valid range of our image, and all
		# the pixels we're going to request, it should have no effect on our sampling.
		# So test with a few such ranges.
		sampleRegions = [
			IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( GafferImage.ImagePlug.tileSize() ) ),
			IECore.Box2i( -IECore.V2i( GafferImage.ImagePlug.tileSize() ), IECore.V2i( GafferImage.ImagePlug.tileSize() ) ),
			IECore.Box2i( IECore.V2i( -1 ), IECore.V2i( 4 ) ),
		]

		# List of positions inside and outside of the image, along
		# with expected values if outside points are clamped inside.
		samples = [
			( IECore.V2i( 0, 0 ), 1 ),
			( IECore.V2i( 1, 0 ), 0 ),
			( IECore.V2i( 1, 1 ), 1 ),
			( IECore.V2i( 0, 1 ), 0 ),
			( IECore.V2i( -1, 0 ), 1 ),
			( IECore.V2i( 2, 0 ), 0 ),
			( IECore.V2i( 0, 3 ), 0 ),
			( IECore.V2i( 0, -1 ), 1 ),
			( IECore.V2i( 3, 3 ), 1 ),
			( IECore.V2i( -1, -1 ), 1 ),
			( IECore.V2i( -1, 2 ), 0 ),
			( IECore.V2i( 2, 2 ), 1 ),
			( IECore.V2f( 1, 1 ), 0.5 ),
		]

		# Assert all is as expected for all combos of region and sample.
		for region in sampleRegions :
			sampler = GafferImage.Sampler( reader["out"], "R", region, boundingMode = GafferImage.Sampler.BoundingMode.Clamp )
			for position, value in samples :
				self.assertEqual( sampler.sample( position.x, position.y ), value )

	def testSampleOutsideDataWindow( self ) :

		constant = GafferImage.Constant()
		constant["format"].setValue( GafferImage.Format( 1000, 1000 ) )
		constant["color"].setValue( IECore.Color4f( 1 ) )

		crop = GafferImage.Crop()
		crop["in"].setInput( constant["out"] )
		crop["areaSource"].setValue( crop.AreaSource.Area )
		crop["area"].setValue( IECore.Box2i( IECore.V2i( 135 ), IECore.V2i( 214 ) ) )
		crop["affectDisplayWindow"].setValue( False )

		sampler = GafferImage.Sampler( crop["out"], "R", IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 50 ) ), boundingMode = GafferImage.Sampler.BoundingMode.Clamp )
		self.assertEqual( sampler.sample( 0, 0 ), 1 )

		sampler = GafferImage.Sampler( crop["out"], "R", IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 50 ) ), boundingMode = GafferImage.Sampler.BoundingMode.Black )
		self.assertEqual( sampler.sample( 0, 0 ), 0 )

	def testHashIncludesBlackPixels( self ) :

		constant = GafferImage.Constant()
		constant["format"].setValue( GafferImage.Format( 1000, 1000 ) )
		constant["color"].setValue( IECore.Color4f( 1 ) )

		crop = GafferImage.Crop()
		crop["in"].setInput( constant["out"] )
		crop["areaSource"].setValue( crop.AreaSource.Area )
		crop["area"].setValue( IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 200 ) ) )
		crop["affectDisplayWindow"].setValue( False )
		crop["affectDataWindow"].setValue( False )

		# Samples the whole data window
		sampler1 = GafferImage.Sampler( crop["out"], "R", IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 200 ) ), boundingMode = GafferImage.Sampler.BoundingMode.Black )
		# Samples the whole data window and then some.
		sampler2 = GafferImage.Sampler( crop["out"], "R", IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 210 ) ), boundingMode = GafferImage.Sampler.BoundingMode.Black )
		# Samples the whole data window and then some and then some more.
		sampler3 = GafferImage.Sampler( crop["out"], "R", IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 220 ) ), boundingMode = GafferImage.Sampler.BoundingMode.Black )

		# The hashes must take account of the additional pixels being sampled.
		self.assertNotEqual( sampler1.hash(), sampler2.hash() )
		self.assertNotEqual( sampler2.hash(), sampler3.hash() )
		self.assertNotEqual( sampler3.hash(), sampler1.hash() )

	def testClampModeWithEmptyDataWindow( self ) :

		empty = self.emptyImage()
		sampler = GafferImage.Sampler( empty["out"], "R", empty["out"]["format"].getValue().getDisplayWindow(), boundingMode = GafferImage.Sampler.BoundingMode.Clamp )
		self.assertEqual( sampler.sample( 0, 0 ), 0.0 )

	def testExceptionOnDeepData( self ) :

		constant1 = GafferImage.Constant()
		constant1["format"].setValue( GafferImage.Format( 1000, 1000 ) )
		constant1["color"].setValue( IECore.Color4f( 1 ) )

		constant2 = GafferImage.Constant()
		constant2["format"].setValue( GafferImage.Format( 1000, 1000 ) )
		constant2["color"].setValue( IECore.Color4f( 1 ) )

		merge = GafferImage.DeepMerge()
		merge["in"][0].setInput( constant1["out"] )
		merge["in"][1].setInput( constant2["out"] )

		with self.assertRaises( RuntimeError ) :
			sampler = GafferImage.Sampler( merge["out"], "R", IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 200 ) ), boundingMode = GafferImage.Sampler.BoundingMode.Black )

if __name__ == "__main__":
	unittest.main()
