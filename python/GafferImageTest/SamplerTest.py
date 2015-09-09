##########################################################################
#
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

import unittest

import IECore
import Gaffer
import GafferImage
import os

class SamplerTest( unittest.TestCase ) :

	fileName = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/checker.exr" )

	def testConstructors( self ) :

		s = Gaffer.ScriptNode()
		r = GafferImage.ImageReader()
		s.addChild( r )

		r["fileName"].setValue( self.fileName )

		bounds = r["out"]["dataWindow"].getValue();

		# Check that the default sampler is the same as a sampler with the default filter.
		defaultSampler = GafferImage.Sampler( r["out"], "R", bounds, GafferImage.Sampler.BoundingMode.Black )

		defaultFilter = GafferImage.Filter.create( GafferImage.Filter.defaultFilter() )
		sampler = GafferImage.Sampler( r["out"], "R", bounds, defaultFilter, GafferImage.Sampler.BoundingMode.Black )

		c = Gaffer.Context()
		c["image:channelName"] = 'R'
		c["image:tileOrigin"] = IECore.V2i( 0 )
		with c:
			self.assertEqual( sampler.sample( bounds.min.x+.5, bounds.min.y+.5 ), defaultSampler.sample( bounds.min.x+.5, bounds.min.y+.5 ) )


	def testOutOfBoundsSampleModeBlack( self ) :

		s = Gaffer.ScriptNode()
		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.fileName )
		s.addChild( r )

		c = Gaffer.Context()
		c["image:channelName"] = 'R'
		c["image:tileOrigin"] = IECore.V2i( 0 )

		bounds = r["out"]["dataWindow"].getValue();

		testCases = [
			( bounds.min.x-1, bounds.min.y ),
			( bounds.min.x, bounds.min.y-1 ),
			( bounds.max.x-1, bounds.max.y ),
			( bounds.max.x, bounds.max.y-1 ),
			( bounds.min.x-1, bounds.max.y-1 ),
			( bounds.min.x, bounds.max.y ),
			( bounds.max.x, bounds.min.y ),
			( bounds.max.x-1, bounds.min.y-1 )
		]

		self.assertTrue( "Box" in GafferImage.Filter.filters() )
		f = GafferImage.Filter.create("Box")

		with c :

			self.assertTrue( "R" in r["out"]["channelNames"].getValue() )
			s = GafferImage.Sampler( r["out"], "R", bounds, f, GafferImage.Sampler.BoundingMode.Black )

			# Check that the bounding pixels are non zero.
			self.assertNotEqual( s.sample( bounds.min.x+.5, bounds.min.y+.5 ), 0. )
			self.assertNotEqual( s.sample( bounds.max.x-.5, bounds.max.y-.5 ), 0. )
			self.assertNotEqual( s.sample( bounds.min.x+.5, bounds.max.y-.5 ), 0. )
			self.assertNotEqual( s.sample( bounds.max.x-.5, bounds.min.y+.5 ), 0. )

			# Sample out of bounds and assert that a zero is returned.
			for x, y in testCases :
				self.assertEqual( s.sample( x+.5, y+.5 ), 0. )

	def testOutOfBoundsSampleModeClamp( self ) :

		s = Gaffer.ScriptNode()
		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.fileName )
		s.addChild( r )

		c = Gaffer.Context()
		c["image:channelName"] = 'R'
		c["image:tileOrigin"] = IECore.V2i( 0 )

		bounds = r["out"]["dataWindow"].getValue();
		f = GafferImage.Filter.create( "Box" )

		with c :

			self.assertTrue( "R" in r["out"]["channelNames"].getValue() )
			s = GafferImage.Sampler( r["out"], "R", bounds, f, GafferImage.Sampler.BoundingMode.Clamp )

			# Get the values of the corner pixels.
			bl = s.sample( bounds.min.x+.5, bounds.min.y+.5 )
			br = s.sample( bounds.max.x-.5, bounds.min.y+.5 )
			tr = s.sample( bounds.max.x-.5, bounds.max.y-.5 )
			tl = s.sample( bounds.min.x+.5, bounds.max.y-.5 )

			# Sample out of bounds and assert that the same value as the nearest pixel is returned.
			self.assertEqual( s.sample( bounds.min.x-1, bounds.min.y ), bl )
			self.assertEqual( s.sample( bounds.min.x, bounds.min.y-1 ), bl )
			self.assertEqual( s.sample( bounds.max.x-1, bounds.max.y ), tr )
			self.assertEqual( s.sample( bounds.max.x, bounds.max.y-1 ), tr )
			self.assertEqual( s.sample( bounds.min.x-1, bounds.max.y-1 ), tl )
			self.assertEqual( s.sample( bounds.min.x, bounds.max.y ), tl )
			self.assertEqual( s.sample( bounds.max.x, bounds.min.y ), br )
			self.assertEqual( s.sample( bounds.max.x-1, bounds.min.y-1 ), br )

	# Test that the hash() method accumulates all of the hashes of the tiles within the sample area
	# for a large number of different sample areas.
	def testSampleHash( self ) :

		s = Gaffer.ScriptNode()
		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.fileName )
		s.addChild( r )

		tileSize = GafferImage.ImagePlug.tileSize()
		# Test one tile first.

		for w in range(2, 6) :
			for x in range(-3, 3) :
				for y in range(-3, 3) :
					sampleBox = IECore.Box2i( IECore.V2i( x*tileSize, y*tileSize ), IECore.V2i( x*tileSize+w*tileSize/2, y*tileSize+w*tileSize/2 ) )
					self.__testHashOfBounds( sampleBox, "R", r["out"] )


	# A private method that acumulates the hashes of the tiles within
	# a box and compares them to the hash returned by the sampler.
	def __testHashOfBounds( self, box, channel, plug ) :

		tileOrigin = GafferImage.ImagePlug.tileOrigin( IECore.V2i( box.min ) )
		self.assertTrue( channel in plug["channelNames"].getValue() )

		c = Gaffer.Context()
		c["image:channelName"] = channel
		c["image:tileOrigin"] = tileOrigin

		h = IECore.MurmurHash()
		h2 = h

		# Get the hash from the sampler.
		with c :
			f = GafferImage.Filter.create( "Box" )
			s = GafferImage.Sampler( plug, channel, box, f, GafferImage.Sampler.BoundingMode.Clamp )
			s.hash( h )

		# Get the hash from the tiles within our desired sample area.
		with c :
			y = box.min.y
			while y < box.max.y :
				x = box.min.x
				while x < box.max.x :
					tileOrigin = GafferImage.ImagePlug.tileOrigin( IECore.V2i( x, y ) )
					h2.append( plug.channelDataHash( channel, tileOrigin ) )
					x += GafferImage.ImagePlug.tileSize()
				y += GafferImage.ImagePlug.tileSize()

		self.assertEqual( h, h2 )

	def test2x2Checker( self ) :

		reader = GafferImage.ImageReader()
		reader["fileName"].setValue( os.path.dirname( __file__ ) + "/images/checker2x2.exr" )

		# As long as the sample region includes the valid range of our image,
		# it should have not effect on our sampling. So test with a few such ranges.
		sampleRegions = [
			IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( GafferImage.ImagePlug.tileSize() ) ),
			IECore.Box2i( -IECore.V2i( GafferImage.ImagePlug.tileSize() ), IECore.V2i( GafferImage.ImagePlug.tileSize() ) ),
			IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 2 ) ),
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
		crop["areaSource"].setValue( crop.AreaSource.Custom )
		crop["area"].setValue( IECore.Box2i( IECore.V2i( 135 ), IECore.V2i( 214 ) ) )

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
		crop["areaSource"].setValue( crop.AreaSource.Custom )
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

if __name__ == "__main__":
	unittest.main()
