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

class MergeTest( GafferImageTest.ImageTestCase ) :

	rPath = GafferImageTest.ImageTestCase.imagesPath() / "redWithDataWindow.100x100.exr"
	gPath = GafferImageTest.ImageTestCase.imagesPath() / "greenWithDataWindow.100x100.exr"
	bPath = GafferImageTest.ImageTestCase.imagesPath() / "blueWithDataWindow.100x100.exr"
	checkerPath = GafferImageTest.ImageTestCase.imagesPath() / "checkerboard.100x100.exr"
	checkerRGBPath = GafferImageTest.ImageTestCase.imagesPath() / "rgbOverChecker.100x100.exr"
	rgbPath = GafferImageTest.ImageTestCase.imagesPath() / "rgb.100x100.exr"
	mergeBoundariesRefPath = GafferImageTest.ImageTestCase.imagesPath() / "mergeBoundariesRef.exr"

	# Do several tests to check the cache is working correctly:
	def testHashes( self ) :

		r1 = GafferImage.ImageReader()
		r1["fileName"].setValue( self.checkerPath )

		r2 = GafferImage.ImageReader()
		r2["fileName"].setValue( self.gPath )

		##########################################
		# Test to see if the hash changes.
		##########################################

		merge = GafferImage.Merge()
		merge["operation"].setValue( GafferImage.Merge.Operation.Over )

		merge["in"][0].setInput( r1["out"] )
		merge["in"][1].setInput( r2["out"] )
		h1 = GafferImage.ImageAlgo.imageHash( merge["out"] )

		# Switch the inputs.
		merge["in"][1].setInput( r1["out"] )
		merge["in"][0].setInput( r2["out"] )
		h2 = GafferImage.ImageAlgo.imageHash( merge["out"] )

		self.assertNotEqual( h1, h2 )

		##########################################
		# Test to see if the hash remains the same
		# when the output should be the same but the
		# input plugs used are not.
		##########################################

		merge = GafferImage.Merge()
		merge["operation"].setValue( GafferImage.Merge.Operation.Over )

		expectedHash = h1

		# Connect up a load of inputs ...
		merge["in"][0].setInput( r1["out"] )
		merge["in"][1].setInput( r1["out"] )
		merge["in"][2].setInput( r1["out"] )
		merge["in"][3].setInput( r2["out"] )

		# but then disconnect two so that the result should still be the same...
		merge["in"][1].setInput( None )
		merge["in"][2].setInput( None )
		h1 = GafferImage.ImageAlgo.imageHash( merge["out"] )

		self.assertEqual( h1, expectedHash )

	# The pass through for disabled is working, but I don't see any sign that a pass through
	# for a single input was ever implemented.  ( For a long time this test was broken )
	@unittest.expectedFailure
	def testHashPassThrough( self ) :

		r1 = GafferImage.ImageReader()
		r1["fileName"].setValue( self.checkerPath )

		##########################################
		# Test to see if the input hash is always passed
		# through if only the first input is connected.
		##########################################

		merge = GafferImage.Merge()
		merge["operation"].setValue( GafferImage.Merge.Operation.Over )

		expectedHash = GafferImage.ImageAlgo.imageHash( r1["out"] )
		merge["in"][0].setInput( r1["out"] )
		h1 = GafferImage.ImageAlgo.imageHash( merge["out"] )

		self.assertEqual( h1, expectedHash )

		##########################################
		# Test that if we disable the node the hash gets passed through.
		##########################################

		merge["enabled"].setValue(False)
		h1 = GafferImage.ImageAlgo.imageHash( merge["out"] )

		self.assertEqual( h1, expectedHash )

	# Overlay a red, green and blue tile of different data window sizes and check the data window is expanded on the result and looks as we expect.
	def testOverRGBA( self ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.rPath )

		g = GafferImage.ImageReader()
		g["fileName"].setValue( self.gPath )

		b = GafferImage.ImageReader()
		b["fileName"].setValue( self.bPath )

		merge = GafferImage.Merge()
		merge["operation"].setValue( GafferImage.Merge.Operation.Over )
		merge["in"][0].setInput( r["out"] )
		merge["in"][1].setInput( g["out"] )
		merge["in"][2].setInput( b["out"] )

		expected = GafferImage.ImageReader()
		expected["fileName"].setValue( self.rgbPath )

		self.assertImagesEqual( merge["out"], expected["out"], maxDifference = 0.001, ignoreMetadata = True )

	# Overlay a red, green and blue tile of different data window sizes and check the data window is expanded on the result and looks as we expect.
	def testOverRGBAonRGB( self ) :

		c = GafferImage.ImageReader()
		c["fileName"].setValue( self.checkerPath )

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.rPath )

		g = GafferImage.ImageReader()
		g["fileName"].setValue( self.gPath )

		b = GafferImage.ImageReader()
		b["fileName"].setValue( self.bPath )

		merge = GafferImage.Merge()
		merge["operation"].setValue( GafferImage.Merge.Operation.Over )
		merge["in"][0].setInput( c["out"] )
		merge["in"][1].setInput( r["out"] )
		merge["in"][2].setInput( g["out"] )
		merge["in"][3].setInput( b["out"] )

		expected = GafferImage.ImageReader()
		expected["fileName"].setValue( self.checkerRGBPath )

		self.assertImagesEqual( merge["out"], expected["out"], maxDifference = 0.001, ignoreMetadata = True )

	def testAffects( self ) :

		c1 = GafferImage.Constant()
		c2 = GafferImage.Constant()

		m = GafferImage.Merge()
		m["in"][0].setInput( c1["out"] )
		m["in"][1].setInput( c2["out"] )

		cs = GafferTest.CapturingSlot( m.plugDirtiedSignal() )

		c1["color"]["r"].setValue( 0.1 )

		self.assertEqual( len( cs ), 5 )
		self.assertTrue( cs[0][0].isSame( m["in"][0]["channelData"] ) )
		self.assertTrue( cs[1][0].isSame( m["in"][0] ) )
		self.assertTrue( cs[2][0].isSame( m["in"] ) )
		self.assertTrue( cs[3][0].isSame( m["out"]["channelData"] ) )
		self.assertTrue( cs[4][0].isSame( m["out"] ) )

		del cs[:]

		c2["color"]["g"].setValue( 0.2 )

		self.assertEqual( len( cs ), 5 )
		self.assertTrue( cs[0][0].isSame( m["in"][1]["channelData"] ) )
		self.assertTrue( cs[1][0].isSame( m["in"][1] ) )
		self.assertTrue( cs[2][0].isSame( m["in"] ) )
		self.assertTrue( cs[3][0].isSame( m["out"]["channelData"] ) )
		self.assertTrue( cs[4][0].isSame( m["out"] ) )

	def testEnabledAffects( self ) :

		m = GafferImage.Merge()

		affected = m.affects( m["enabled"] )
		self.assertTrue( m["out"]["channelData"] in affected )

	def testPassThrough( self ) :

		c = GafferImage.Constant()
		f = GafferImage.Resize()
		f["in"].setInput( c["out"] )
		f["format"].setValue( GafferImage.Format( imath.Box2i( imath.V2i( 0 ), imath.V2i( 10 ) ), 1 ) )
		d = GafferImage.ImageMetadata()
		d["metadata"].addChild( Gaffer.NameValuePlug( "comment", IECore.StringData( "reformated and metadata updated" ) ) )
		d["in"].setInput( f["out"] )

		m = GafferImage.Merge()
		m["in"][0].setInput( c["out"] )
		m["in"][1].setInput( d["out"] )

		self.assertEqual( m["out"]["format"].hash(), c["out"]["format"].hash() )
		self.assertEqual( m["out"]["metadata"].hash(), c["out"]["metadata"].hash() )

		self.assertEqual( m["out"]["format"].getValue(), c["out"]["format"].getValue() )
		self.assertEqual( m["out"]["metadata"].getValue(), c["out"]["metadata"].getValue() )

		m["in"][0].setInput( d["out"] )
		m["in"][1].setInput( c["out"] )

		self.assertEqual( m["out"]["format"].hash(), d["out"]["format"].hash() )
		self.assertEqual( m["out"]["metadata"].hash(), d["out"]["metadata"].hash() )

		self.assertEqual( m["out"]["format"].getValue(), d["out"]["format"].getValue() )
		self.assertEqual( m["out"]["metadata"].getValue(), d["out"]["metadata"].getValue() )

	def testSmallDataWindowOverLarge( self ) :

		b = GafferImage.Constant()
		b["format"].setValue( GafferImage.Format( 500, 500, 1.0 ) )
		b["color"].setValue( imath.Color4f( 1, 0, 0, 1 ) )

		a = GafferImage.Constant()
		a["format"].setValue( GafferImage.Format( 500, 500, 1.0 ) )
		a["color"].setValue( imath.Color4f( 0, 1, 0, 1 ) )

		aCrop = GafferImage.Crop()
		aCrop["in"].setInput( a["out"] )
		aCrop["areaSource"].setValue( aCrop.AreaSource.Area )
		aCrop["area"].setValue( imath.Box2i( imath.V2i( 50 ), imath.V2i( 162 ) ) )
		aCrop["affectDisplayWindow"].setValue( False )

		m = GafferImage.Merge()
		m["operation"].setValue( m.Operation.Over )
		m["in"][0].setInput( b["out"] )
		m["in"][1].setInput( aCrop["out"] )

		redSampler = GafferImage.Sampler( m["out"], "R", m["out"]["format"].getValue().getDisplayWindow() )
		greenSampler = GafferImage.Sampler( m["out"], "G", m["out"]["format"].getValue().getDisplayWindow() )
		blueSampler = GafferImage.Sampler( m["out"], "B", m["out"]["format"].getValue().getDisplayWindow() )

		def sample( x, y ) :

			return imath.Color3f(
				redSampler.sample( x, y ),
				greenSampler.sample( x, y ),
				blueSampler.sample( x, y ),
			)

		# We should only have overed green in areas which are inside
		# the data window of aCrop. Everywhere else we should have
		# red still.

		self.assertEqual( sample( 49, 49 ), imath.Color3f( 1, 0, 0 ) )
		self.assertEqual( sample( 50, 50 ), imath.Color3f( 0, 1, 0 ) )
		self.assertEqual( sample( 161, 161 ), imath.Color3f( 0, 1, 0 ) )
		self.assertEqual( sample( 162, 162 ), imath.Color3f( 1, 0, 0 ) )

	def testLargeDataWindowAddedToSmall( self ) :

		b = GafferImage.Constant()
		b["format"].setValue( GafferImage.Format( 500, 500, 1.0 ) )
		b["color"].setValue( imath.Color4f( 1, 0, 0, 1 ) )

		a = GafferImage.Constant()
		a["format"].setValue( GafferImage.Format( 500, 500, 1.0 ) )
		a["color"].setValue( imath.Color4f( 0, 1, 0, 1 ) )

		bCrop = GafferImage.Crop()
		bCrop["in"].setInput( b["out"] )
		bCrop["areaSource"].setValue( bCrop.AreaSource.Area )
		bCrop["area"].setValue( imath.Box2i( imath.V2i( 50 ), imath.V2i( 162 ) ) )
		bCrop["affectDisplayWindow"].setValue( False )

		m = GafferImage.Merge()
		m["operation"].setValue( m.Operation.Add )
		m["in"][0].setInput( bCrop["out"] )
		m["in"][1].setInput( a["out"] )

		redSampler = GafferImage.Sampler( m["out"], "R", m["out"]["format"].getValue().getDisplayWindow() )
		greenSampler = GafferImage.Sampler( m["out"], "G", m["out"]["format"].getValue().getDisplayWindow() )
		blueSampler = GafferImage.Sampler( m["out"], "B", m["out"]["format"].getValue().getDisplayWindow() )

		def sample( x, y ) :

			return imath.Color3f(
				redSampler.sample( x, y ),
				greenSampler.sample( x, y ),
				blueSampler.sample( x, y ),
			)

		# We should only have yellow in areas where the background exists,
		# and should have just green everywhere else.

		self.assertEqual( sample( 49, 49 ), imath.Color3f( 0, 1, 0 ) )
		self.assertEqual( sample( 50, 50 ), imath.Color3f( 1, 1, 0 ) )
		self.assertEqual( sample( 161, 161 ), imath.Color3f( 1, 1, 0 ) )
		self.assertEqual( sample( 162, 162 ), imath.Color3f( 0, 1, 0 ) )

	def testCrashWithResizedInput( self ) :

		b = GafferImage.Constant()
		b["format"].setValue( GafferImage.Format( 2048, 1556 ) )

		bResized = GafferImage.Resize()
		bResized["in"].setInput( b["out"] )
		bResized["format"].setValue( GafferImage.Format( 1920, 1080 ) )
		bResized["fitMode"].setValue( bResized.FitMode.Fit )

		a = GafferImage.Constant()
		a["format"].setValue( GafferImage.Format( 1920, 1080 ) )

		merge = GafferImage.Merge()
		merge["operation"].setValue( merge.Operation.Over )
		merge["in"][0].setInput( bResized["out"] )
		merge["in"][1].setInput( a["out"] )

		GafferImageTest.processTiles( merge["out"] )

	def testModes( self ) :

		b = GafferImage.Constant()
		b["color"].setValue( imath.Color4f( 0.1, 0.2, 0.3, 0.4 ) )

		a = GafferImage.Constant()
		a["color"].setValue( imath.Color4f( 1, 0.3, 0.1, 0.2 ) )

		merge = GafferImage.Merge()
		merge["in"][0].setInput( b["out"] )
		merge["in"][1].setInput( a["out"] )

		sampler = GafferImage.ImageSampler()
		sampler["image"].setInput( merge["out"] )
		sampler["pixel"].setValue( imath.V2f( 10 ) )

		self.longMessage = True
		for operation, expected in [
			( GafferImage.Merge.Operation.Add, ( 1.1, 0.5, 0.4, 0.6 ) ),
			( GafferImage.Merge.Operation.Atop, ( 0.48, 0.28, 0.28, 0.4 ) ),
			( GafferImage.Merge.Operation.Divide, ( 10, 1.5, 1/3.0, 0.5 ) ),
			( GafferImage.Merge.Operation.In, ( 0.4, 0.12, 0.04, 0.08 ) ),
			( GafferImage.Merge.Operation.Out, ( 0.6, 0.18, 0.06, 0.12 ) ),
			( GafferImage.Merge.Operation.Mask, ( 0.02, 0.04, 0.06, 0.08 ) ),
			( GafferImage.Merge.Operation.Matte, ( 0.28, 0.22, 0.26, 0.36 ) ),
			( GafferImage.Merge.Operation.Multiply, ( 0.1, 0.06, 0.03, 0.08 ) ),
			( GafferImage.Merge.Operation.Over, ( 1.08, 0.46, 0.34, 0.52 ) ),
			( GafferImage.Merge.Operation.Subtract, ( 0.9, 0.1, -0.2, -0.2 ) ),
			( GafferImage.Merge.Operation.Difference, ( 0.9, 0.1, 0.2, 0.2 ) ),
			( GafferImage.Merge.Operation.Under, ( 0.7, 0.38, 0.36, 0.52 ) ),
			( GafferImage.Merge.Operation.Min, ( 0.1, 0.2, 0.1, 0.2 ) ),
			( GafferImage.Merge.Operation.Max, ( 1, 0.3, 0.3, 0.4 ) )
		] :

			merge["operation"].setValue( operation )
			self.assertAlmostEqual( sampler["color"]["r"].getValue(), expected[0], msg=operation )
			self.assertAlmostEqual( sampler["color"]["g"].getValue(), expected[1], msg=operation )
			self.assertAlmostEqual( sampler["color"]["b"].getValue(), expected[2], msg=operation )
			self.assertAlmostEqual( sampler["color"]["a"].getValue(), expected[3], msg=operation )

	def testDifferenceExceptionalValues( self ) :

		black = GafferImage.Constant()
		black["color"].setValue( imath.Color4f( 0 ) )

		nan = GafferImage.Constant()
		nan["color"].setValue( imath.Color4f( float( "nan" ) ) )

		# Float plugs by default are capped at 3.4e38 - to get infinity, we multiply that by itself.
		infSource = GafferImage.Constant()
		infSource["color"].setValue( imath.Color4f( float( "inf" ) ) )

		inf = GafferImage.Grade()
		inf["in"].setInput( infSource["out"] )
		inf["multiply"].setValue( imath.Color4f( float( "inf" ) ) )

		minusInf = GafferImage.Grade()
		minusInf["in"].setInput( infSource["out"] )
		minusInf["multiply"].setValue( imath.Color4f( -float( "inf" ) ) )

		b = GafferImage.Constant()
		a = GafferImage.Constant()

		merge = GafferImage.Merge()
		merge["operation"].setValue( GafferImage.Merge.Operation.Difference )

		sampler = GafferImage.ImageSampler()
		sampler["image"].setInput( merge["out"] )
		sampler["pixel"].setValue( imath.V2f( 10 ) )

		merge["in"][0].setInput( inf["out"] )
		merge["in"][1].setInput( inf["out"] )
		self.assertEqual( sampler["color"]["r"].getValue(), 0.0 )

		merge["in"][0].setInput( minusInf["out"] )
		merge["in"][1].setInput( minusInf["out"] )
		self.assertEqual( sampler["color"]["r"].getValue(), 0.0 )

		merge["in"][0].setInput( nan["out"] )
		merge["in"][1].setInput( nan["out"] )
		self.assertEqual( sampler["color"]["r"].getValue(), 0.0 )

		merge["in"][0].setInput( black["out"] )
		merge["in"][1].setInput( nan["out"] )
		self.assertEqual( sampler["color"]["r"].getValue(), float( "inf" ) )

		merge["in"][0].setInput( inf["out"] )
		merge["in"][1].setInput( black["out"] )
		self.assertEqual( sampler["color"]["r"].getValue(), float( "inf" ) )

		merge["in"][0].setInput( inf["out"] )
		merge["in"][1].setInput( minusInf["out"] )
		self.assertEqual( sampler["color"]["r"].getValue(), float( "inf" ) )

		merge["in"][0].setInput( nan["out"] )
		merge["in"][1].setInput( inf["out"] )
		self.assertEqual( sampler["color"]["r"].getValue(), float( "inf" ) )

	def testChannelRequest( self ) :

		a = GafferImage.Constant()
		a["color"].setValue( imath.Color4f( 0.1, 0.2, 0.3, 0.4 ) )

		ad = GafferImage.DeleteChannels()
		ad["in"].setInput( a["out"] )
		ad["mode"].setValue( GafferImage.DeleteChannels.Mode.Delete )
		ad["channels"].setValue( "R" )

		b = GafferImage.Constant()
		b["color"].setValue( imath.Color4f( 1.0, 0.3, 0.1, 0.2 ) )

		bd = GafferImage.DeleteChannels()
		bd["in"].setInput( b["out"] )
		bd["mode"].setValue( GafferImage.DeleteChannels.Mode.Delete )
		bd["channels"].setValue( "G" )

		merge = GafferImage.Merge()
		merge["in"][0].setInput( ad["out"] )
		merge["in"][1].setInput( bd["out"] )
		merge["operation"].setValue( GafferImage.Merge.Operation.Add )

		sampler = GafferImage.ImageSampler()
		sampler["image"].setInput( merge["out"] )
		sampler["pixel"].setValue( imath.V2f( 10 ) )

		self.assertAlmostEqual( sampler["color"]["r"].getValue(), 0.0 + 1.0 )
		self.assertAlmostEqual( sampler["color"]["g"].getValue(), 0.2 + 0.0 )
		self.assertAlmostEqual( sampler["color"]["b"].getValue(), 0.3 + 0.1 )
		self.assertAlmostEqual( sampler["color"]["a"].getValue(), 0.4 + 0.2 )

	def testNonFlatThrows( self ) :

		deep = GafferImage.Empty()
		flat = GafferImage.Constant()

		merge = GafferImage.Merge()
		merge["in"][0].setInput( flat["out"] )
		merge["in"][1].setInput( flat["out"] )

		self.assertNotEqual( GafferImage.ImageAlgo.imageHash( merge["out"] ), GafferImage.ImageAlgo.imageHash( flat["out"] ) )

		merge["in"][0].setInput( deep["out"] )
		self.assertRaisesRegex( RuntimeError, 'Deep data not supported in input "in.in0"', GafferImage.ImageAlgo.image, merge["out"] )
		merge["in"][0].setInput( flat["out"] )
		merge["in"][1].setInput( deep["out"] )
		self.assertRaisesRegex( RuntimeError, 'Deep data not supported in input "in.in1"', GafferImage.ImageAlgo.image, merge["out"] )

	def testDefaultFormat( self ) :

		a = GafferImage.Constant()
		a["format"].setValue( GafferImage.Format( 100, 200 ) )

		m = GafferImage.Merge()
		m["in"][1].setInput( a["out"] )

		with Gaffer.Context() as c :
			GafferImage.FormatPlug().setDefaultFormat( c, GafferImage.Format( 1000, 2000 ) )
			self.assertEqual( m["out"]["format"].getValue(), GafferImage.Format( 1000, 2000 ) )

	def testDataWindowWhenBNotConnected( self ) :

		a = GafferImage.Constant()
		a["format"].setValue( GafferImage.Format( 100, 200 ) )

		m = GafferImage.Merge()
		m["in"][1].setInput( a["out"] )

		self.assertEqual( m["out"]["dataWindow"].getValue(), a["out"]["dataWindow"].getValue() )

	# Make sure we don't fail by pulling tiles outside the data window when merging images with
	# misaligned data
	def testTilesOutsideDataWindow( self ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.checkerPath )

		o = GafferImage.Offset()
		o["in"].setInput( r["out"] )
		o["offset"].setValue( imath.V2i( -10 ) )

		merge = GafferImage.Merge()

		merge["in"][0].setInput( r["out"] )
		merge["in"][1].setInput( o["out"] )
		GafferImage.ImageAlgo.image( merge["out"] )

	def testPassthroughs( self ) :

		ts = GafferImage.ImagePlug.tileSize()

		checkerboardB = GafferImage.Checkerboard()
		checkerboardB["format"]["displayWindow"].setValue( imath.Box2i( imath.V2i( 0 ), imath.V2i( 4096 ) ) )

		checkerboardA = GafferImage.Checkerboard()
		checkerboardA["format"]["displayWindow"].setValue( imath.Box2i( imath.V2i( 0 ), imath.V2i( 4096 ) ) )
		checkerboardA["size"].setValue( imath.V2f( 5 ) )

		cropB = GafferImage.Crop()
		cropB["in"].setInput( checkerboardB["out"] )
		cropB["area"].setValue( imath.Box2i( imath.V2i( ts * 0.5 ), imath.V2i( ts * 4.5 ) ) )
		cropB["affectDisplayWindow"].setValue( False )

		cropA = GafferImage.Crop()
		cropA["in"].setInput( checkerboardA["out"] )
		cropA["area"].setValue( imath.Box2i( imath.V2i( ts * 2.5 ), imath.V2i( ts * 6.5 ) ) )
		cropA["affectDisplayWindow"].setValue( False )

		merge = GafferImage.Merge()
		merge["in"][0].setInput( cropB["out"] )
		merge["in"][1].setInput( cropA["out"] )
		merge["operation"].setValue( 8 )

		sampleTileOrigins = {
			"insideBoth" : imath.V2i( ts * 3, ts * 3 ),
			"outsideBoth" : imath.V2i( ts * 5, ts ),
			"outsideEdgeB" : imath.V2i( ts, 0 ),
			"insideB" : imath.V2i( ts, ts ),
			"internalEdgeB" : imath.V2i( ts * 4, ts ),
			"internalEdgeA" : imath.V2i( ts * 5, ts * 2 ),
			"insideA" : imath.V2i( ts * 5, ts * 5 ),
			"outsideEdgeA" : imath.V2i( ts * 6, ts * 5 )
		}

		for opName, onlyA, onlyB in [
				( "Atop", "black", "passB" ),
				( "Divide", "operate", "black" ),
				( "Out", "passA", "black" ),
				( "Multiply", "black", "black" ),
				( "Over", "passA", "passB" ),
				( "Subtract", "passA", "operate" ),
				( "Difference", "operate", "operate" )
			]:
			op = getattr( GafferImage.Merge.Operation, opName )
			merge["operation"].setValue( op )

			results = {}
			for name, tileOrigin in sampleTileOrigins.items():
				# We want to check the value pass through code independently
				# of the hash passthrough code, which we can do by dropping
				# the value cached and evaluating values first
				Gaffer.ValuePlug.clearCache()

				with Gaffer.Context( Gaffer.Context.current() ) as c :
					c["image:tileOrigin"] = tileOrigin
					c["image:channelName"] = "R"

					data = merge["out"]["channelData"].getValue( _copy = False )
					if data.isSame( GafferImage.ImagePlug.blackTile( _copy = False ) ):
						computeMode = "black"
					elif data.isSame( cropB["out"]["channelData"].getValue( _copy = False ) ):
						computeMode = "passB"
					elif data.isSame( cropA["out"]["channelData"].getValue( _copy = False ) ):
						computeMode = "passA"
					else:
						computeMode = "operate"

					h = merge["out"]["channelData"].hash()
					if h == GafferImage.ImagePlug.blackTile().hash():
						hashMode = "black"
					elif h == cropB["out"]["channelData"].hash():
						hashMode = "passB"
					elif h == cropA["out"]["channelData"].hash():
						hashMode = "passA"
					else:
						hashMode = "operate"

					self.assertEqual( hashMode, computeMode )

					results[name] = hashMode

			self.assertEqual( results["insideBoth"], "operate" )
			self.assertEqual( results["outsideBoth"], "black" )
			self.assertEqual( results["outsideEdgeB"], onlyB )
			self.assertEqual( results["insideB"], onlyB )
			self.assertEqual( results["outsideEdgeA"], onlyA )
			self.assertEqual( results["insideA"], onlyA )

			if onlyA == "black" or onlyB == "black":
				self.assertEqual( results["internalEdgeB"], onlyB )
				self.assertEqual( results["internalEdgeA"], onlyA )
			else:
				self.assertEqual( results["internalEdgeB"], "operate" )
				self.assertEqual( results["internalEdgeA"], "operate" )



	# This somewhat sloppy test cobbled together from a Gaffer scene tests a bunch of the weird cases
	# for how data windows can overlap each other and the tile.  It was added because I'm experimenting
	# with an approach for treating the tile in regions, which does add a little bit of arithmetic that
	# I could get wrong
	def runBoundaryCorrectness( self, scale ):

		testMerge = GafferImage.Merge()
		subImageNodes = []
		for checkSize, col, bound in [
			( 2, ( 0.672299981, 0.672299981,  0           ), ((11, 7), (61, 57)) ),
			( 4, ( 0.972599983, 0.493499994,  1           ), ((9, 5), (59, 55)) ),
			( 6, ( 0.310799986, 0.843800008,  1           ), ((0, 21), (1024, 41)) ),
			( 8, ( 0.958999991, 0.672299981,  0.0296      ), ((22, 0), (42, 1024)) ),
			( 10,   ( 0.950900018, 0.0899000019, 0.235499993 ), ((7, 10), (47, 50)) ),
		]:
			checkerboard = GafferImage.Checkerboard()
			checkerboard["format"].setValue( GafferImage.Format( 1024 * scale, 1024 * scale, 1.000 ) )
			checkerboard["size"].setValue( imath.V2f( checkSize * scale ) )
			checkerboard["colorA"].setValue( imath.Color4f( 0.1 * col[0], 0.1 * col[1], 0.1 * col[2], 0.3 ) )
			checkerboard["colorB"].setValue( imath.Color4f( 0.5 * col[0], 0.5 * col[1], 0.5 * col[2], 0.7 ) )

			crop = GafferImage.Crop( "Crop" )
			crop["in"].setInput( checkerboard["out"] )
			crop["area"].setValue(
				imath.Box2i(
					imath.V2i( scale * bound[0][0], scale * bound[0][1] ),
					imath.V2i( scale * bound[1][0], scale * bound[1][1] )
				)
			)
			crop["affectDisplayWindow"].setValue( False )

			subImageNodes.append( checkerboard )
			subImageNodes.append( crop )

			testMerge["in"][-1].setInput( crop["out"] )

		testMerge["expression"] = Gaffer.Expression()
		testMerge["expression"].setExpression( 'parent["operation"] = context[ "loop:index" ]' )

		inverseScale = GafferImage.ImageTransform()
		inverseScale["in"].setInput( testMerge["out"] )
		inverseScale["filter"].setValue( "box" )
		inverseScale["transform"]["scale"].setValue( imath.V2f( 1.0/scale ) )

		crop1 = GafferImage.Crop()
		crop1["in"].setInput( inverseScale["out"] )
		crop1["area"].setValue( imath.Box2i( imath.V2i( 0, 0 ), imath.V2i( 64, 64 ) ) )

		loopInit = GafferImage.Constant()
		loopInit["format"].setValue( GafferImage.Format( 896, 64, 1.000 ) )
		loopInit["color"].setValue( imath.Color4f( 0 ) )

		loopOffset = GafferImage.Offset()
		loopOffset["in"].setInput( crop1["out"] )
		loopOffset["expression"] = Gaffer.Expression()
		loopOffset["expression"].setExpression( 'parent["offset"]["x"] = 64 * context[ "loop:index" ]' )

		loopMerge = GafferImage.Merge()
		loopMerge["in"][1].setInput( loopOffset["out"] )

		loop = Gaffer.Loop()
		loop.setup( GafferImage.ImagePlug( "in", ) )
		loop["iterations"].setValue( 14 )
		loop["in"].setInput( loopInit["out"] )
		loop["next"].setInput( loopMerge["out"] )
		loopMerge["in"][0].setInput( loop["previous"] )

		# Uncomment for debug
		#imageWriter = GafferImage.ImageWriter( "ImageWriter" )
		#imageWriter["in"].setInput( loop["out"] )
		#imageWriter['openexr']['dataType'].setValue( "float" )
		#imageWriter["fileName"].setValue( "/tmp/mergeBoundaries.exr" )
		#imageWriter["task"].execute()

		reader = GafferImage.ImageReader()
		reader["fileName"].setValue( self.mergeBoundariesRefPath )

		self.assertImagesEqual( loop["out"], reader["out"], ignoreMetadata = True, maxDifference = 1e-5 if scale > 1 else 0 )

	def testBoundaryCorrectness( self ):
		self.runBoundaryCorrectness( 1 )
		self.runBoundaryCorrectness( 2 )
		self.runBoundaryCorrectness( 4 )
		self.runBoundaryCorrectness( 8 )
		self.runBoundaryCorrectness( 16 )
		self.runBoundaryCorrectness( 32 )

	def testEmptyDataWindowMerge( self ):
		constant = GafferImage.Constant()
		constant["format"].setValue( GafferImage.Format( 512, 512, 1.000 ) )
		constant["color"].setValue( imath.Color4f( 1 ) )

		offset = GafferImage.Offset()
		offset["in"].setInput( constant["out"] )
		offset["offset"].setValue( imath.V2i( -1024 ) )

		emptyCrop = GafferImage.Crop()
		emptyCrop["in"].setInput( constant["out"] )
		emptyCrop["area"].setValue( imath.Box2i( imath.V2i( -10 ), imath.V2i( -100 ) ) )

		merge = GafferImage.Merge()
		merge["in"][0].setInput( offset["out"] )
		merge["in"][1].setInput( emptyCrop["out"] )

		self.assertEqual( merge["out"].dataWindow(), imath.Box2i( imath.V2i( -1024 ), imath.V2i( -512 ) ) )

	def testChangeDataWindow( self ):
		constant1 = GafferImage.Constant()
		constant1["format"].setValue( GafferImage.Format( 512, 512, 1.000 ) )
		constant1["color"].setValue( imath.Color4f( 1, 0, 0, 1 ) )

		constant2 = GafferImage.Constant()
		constant2["format"].setValue( GafferImage.Format( 512, 512, 1.000 ) )
		constant2["color"].setValue( imath.Color4f( 0, 1, 0, 1 ) )

		merge = GafferImage.Merge()
		merge["in"][0].setInput( constant1["out"] )
		merge["in"][1].setInput( constant2["out"] )
		merge["operation"].setValue( GafferImage.Merge.Operation.Over )

		stats = GafferImage.ImageStats()
		stats["in"].setInput( merge["out"] )
		stats["area"].setValue( imath.Box2i( imath.V2i( 0 ), imath.V2i( 512 ) ) )

		for i in range( 0, 512, 16 ):
			constant2["format"].setValue( GafferImage.Format( 512, i, 1.000 ) )
			frac = i / 512.0
			self.assertEqual( stats["average"].getValue(), imath.Color4f( 1 - frac, frac, 0, 1 ) )

	def testNoChannelsAffectsBug( self ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.checkerPath )

		resized = GafferImage.Resize()
		resized["in"].setInput( r["out"] )
		resized["format"].setValue( GafferImage.Format( 512, 512, 1.0 ) )

		c = GafferImage.Constant()
		c["format"].setValue( GafferImage.Format( 512, 512, 1.000 ) )

		d = GafferImage.DeleteChannels()
		d["enabled"].setValue( False )
		d["channels"].setValue( "*" )
		d["in"].setInput( c["out"] )

		merge = GafferImage.Merge()
		merge["operation"].setValue( GafferImage.Merge.Operation.Over )

		merge["in"][0].setInput( resized["out"] )
		merge["in"][1].setInput( d["out"] )

		# Merging with a black image should produce black
		self.assertImagesEqual( merge["out"], c["out"], ignoreMetadata = True )

		d["enabled"].setValue( True )

		# Merging with an image with no channels should have no effect
		self.assertImagesEqual( merge["out"], resized["out"] )

	def testOnlyAlphaVsOnlyRGBBug( self ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.checkerRGBPath )

		shuf = GafferImage.Shuffle()
		shuf["in"].setInput( r["out"] )
		shuf["channels"].addChild( GafferImage.Shuffle.ChannelPlug( "A", "R" ) )

		delete = GafferImage.DeleteChannels()
		delete["in"].setInput( shuf["out"] )
		delete["channels"].setValue( "R" )

		c = GafferImage.Constant()
		c["format"].setValue( GafferImage.Format( 100, 100, 1.000 ) )
		c["color"].setValue( imath.Color4f( 0.0 ) )

		merge = GafferImage.Merge()
		merge["in"][0].setInput( c["out"] )
		merge["in"][1].setInput( delete["out"] )

		referenceShuf = GafferImage.Shuffle()
		referenceShuf["in"].setInput( delete["out"] )
		referenceShuf["channels"].addChild( GafferImage.Shuffle.ChannelPlug( "", "__black" ) )
		referenceShuf["channels"][0]["out"].setInput( delete["channels"] )

		# We're comparing two ways of filling in the deleted channels with black - either by
		# merging with a black image, or by shuffling in black.  These should be equivalent.
		#
		# This test is only here because of a weird special case bug in Merge where an input
		# with an R channel and no alpha , and an input with the same channel data but as
		# alpha with no R, would hash the same

		self.assertImagesEqual( referenceShuf["out"], merge["out"], ignoreMetadata = True, ignoreChannelNamesOrder = True )

		delete["channels"].setValue( "A" )

		self.assertImagesEqual( referenceShuf["out"], merge["out"], ignoreMetadata = True, ignoreChannelNamesOrder = True )

	def testMultiView( self ) :

		c1 = GafferImage.Constant()
		c1["color"].setValue( imath.Color4f( 1, 0, 0, 0 ) )
		c1["format"]["displayWindow"].setValue( imath.Box2i( imath.V2i( 0 ), imath.V2i( 128 ) ) )
		c2 = GafferImage.Constant()
		c2["color"].setValue( imath.Color4f( 0, 1, 0, 0 ) )
		c2["format"]["displayWindow"].setValue( imath.Box2i( imath.V2i( 0 ), imath.V2i( 128 ) ) )
		c3 = GafferImage.Constant()
		c3["color"].setValue( imath.Color4f( 0, 0, 1, 0 ) )
		c3["format"]["displayWindow"].setValue( imath.Box2i( imath.V2i( 0 ), imath.V2i( 64 ) ) )
		c4 = GafferImage.Constant()
		c4["color"].setValue( imath.Color4f( 1, 0, 1, 0 ) )
		c4["format"]["displayWindow"].setValue( imath.Box2i( imath.V2i( 0 ), imath.V2i( 64 ) ) )

		createViews1 = GafferImage.CreateViews()
		createViews1["views"].addChild( Gaffer.NameValuePlug( "left", GafferImage.ImagePlug(), True, "view0", Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		createViews1["views"].addChild( Gaffer.NameValuePlug( "right", GafferImage.ImagePlug(), True, "view1", Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		createViews1["views"][0]["value"].setInput( c1["out"] )
		createViews1["views"][1]["value"].setInput( c2["out"] )

		createViews2 = GafferImage.CreateViews()
		createViews2["views"].addChild( Gaffer.NameValuePlug( "left", GafferImage.ImagePlug(), True, "view0", Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		createViews2["views"].addChild( Gaffer.NameValuePlug( "right", GafferImage.ImagePlug(), True, "view1", Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		createViews2["views"][0]["value"].setInput( c3["out"] )
		createViews2["views"][1]["value"].setInput( c4["out"] )

		merge = GafferImage.Merge()
		merge["operation"].setValue( GafferImage.Merge.Operation.Over )

		referenceMerge = GafferImage.Merge()
		referenceMerge["operation"].setValue( GafferImage.Merge.Operation.Over )

		# Test a default view over multiple views
		merge["in"][0].setInput( createViews1["out"] )
		merge["in"][1].setInput( c3["out"] )

		referenceMerge["in"][0].setInput( c1["out"] )
		referenceMerge["in"][1].setInput( c3["out"] )

		self.assertEqual( merge["out"].viewNames(), IECore.StringVectorData( [ "left", "right" ] ) )

		self.assertEqual( GafferImage.ImageAlgo.tiles( merge["out"], True, "left" ), GafferImage.ImageAlgo.tiles( referenceMerge["out"] ) )

		referenceMerge["in"][0].setInput( c2["out"] )

		self.assertEqual( GafferImage.ImageAlgo.tiles( merge["out"], True, "right" ), GafferImage.ImageAlgo.tiles( referenceMerge["out"] ) )

		# No default view in first input
		with self.assertRaisesRegex( RuntimeError, '.*No view "default"' ):
			GafferImage.ImageAlgo.tiles( merge["out"], True, "default" )

		# Merge stereo
		merge["in"][1].setInput( createViews2["out"] )
		self.assertEqual( merge["out"].viewNames(), IECore.StringVectorData( [ "left", "right" ] ) )
		referenceMerge["in"][0].setInput( c1["out"] )
		referenceMerge["in"][1].setInput( c3["out"] )
		self.assertEqual( GafferImage.ImageAlgo.tiles( merge["out"], True, "left" ), GafferImage.ImageAlgo.tiles( referenceMerge["out"] ) )

		referenceMerge["in"][0].setInput( c2["out"] )
		referenceMerge["in"][1].setInput( c4["out"] )
		self.assertEqual( GafferImage.ImageAlgo.tiles( merge["out"], True, "right" ), GafferImage.ImageAlgo.tiles( referenceMerge["out"] ) )

		# Test functionality of default
		createViews1["views"][0]["name"].setValue( "default" )
		self.assertEqual( merge["out"].viewNames(), IECore.StringVectorData( [ "default", "right" ] ) )
		self.assertEqual( GafferImage.ImageAlgo.tiles( merge["out"], True, "default" ), GafferImage.ImageAlgo.tiles( c1["out"] ) )
		self.assertEqual( GafferImage.ImageAlgo.tiles( merge["out"], True, "undeclared" ), GafferImage.ImageAlgo.tiles( c1["out"] ) )

		createViews2["views"][1]["name"].setValue( "default" )
		referenceMerge["in"][0].setInput( c1["out"] )
		referenceMerge["in"][1].setInput( c4["out"] )
		self.assertEqual( GafferImage.ImageAlgo.tiles( merge["out"], True, "default" ), GafferImage.ImageAlgo.tiles( referenceMerge["out"] ) )
		self.assertEqual( GafferImage.ImageAlgo.tiles( merge["out"], True, "undeclared" ), GafferImage.ImageAlgo.tiles( referenceMerge["out"] ) )

		# Test merging in views that aren't in the first image, which does nothing
		createViews2["views"][1]["name"].setValue( "right" )
		merge["in"][0].setInput( c1["out"] )
		self.assertImagesEqual( merge["out"], c1["out"] )

	def mergePerf( self, operation, mismatch ):
		r = GafferImage.Checkerboard( "Checkerboard" )
		r["format"].setValue( GafferImage.Format( 4096, 3112, 1.000 ) )
		# Make the size of the checkerboard not a perfect multiple of tile size
		# in case we ever fix Checkerboard to notice when tiles are repeated
		# and return an identical hash ( which would invalidate this performance
		# test )
		r["size"].setValue( imath.V2f( 64.01 ) )

		alphaShuffle = GafferImage.Shuffle()
		alphaShuffle["in"].setInput( r["out"] )
		alphaShuffle["channels"].addChild( GafferImage.Shuffle.ChannelPlug( "A", "R" ) )

		transform = GafferImage.Offset()
		transform["in"].setInput( alphaShuffle["out"] )
		if mismatch:
			transform["offset"].setValue( imath.V2i( 4000, 3000 ) )
		else:
			transform["offset"].setValue( imath.V2i( 26, 42 ) )

		merge = GafferImage.Merge()
		merge["operation"].setValue( operation )
		merge["in"][0].setInput( alphaShuffle["out"] )
		merge["in"][1].setInput( transform["out"] )

		# Precache upstream network, we're only interested in the performance of Merge
		GafferImageTest.processTiles( alphaShuffle["out"] )
		GafferImageTest.processTiles( transform["out"] )

		with GafferTest.TestRunner.PerformanceScope() :
			GafferImageTest.processTiles( merge["out"] )

	@unittest.skipIf( GafferTest.inCI(), "Performance not relevant on CI platform" )
	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 5)
	def testAddPerf( self ):
		self.mergePerf( GafferImage.Merge.Operation.Add, False )

	@unittest.skipIf( GafferTest.inCI(), "Performance not relevant on CI platform" )
	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 5)
	def testAddMismatchPerf( self ):
		self.mergePerf( GafferImage.Merge.Operation.Add, True )

	@unittest.skipIf( GafferTest.inCI(), "Performance not relevant on CI platform" )
	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 5)
	def testAtopPerf( self ):
		self.mergePerf( GafferImage.Merge.Operation.Atop, False )

	@unittest.skipIf( GafferTest.inCI(), "Performance not relevant on CI platform" )
	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 5)
	def testAtopMismatchPerf( self ):
		self.mergePerf( GafferImage.Merge.Operation.Atop, True )

	@unittest.skipIf( GafferTest.inCI(), "Performance not relevant on CI platform" )
	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 5)
	def testDividePerf( self ):
		self.mergePerf( GafferImage.Merge.Operation.Divide, False )

	@unittest.skipIf( GafferTest.inCI(), "Performance not relevant on CI platform" )
	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 5)
	def testDivideMismatchPerf( self ):
		self.mergePerf( GafferImage.Merge.Operation.Divide, True )

	@unittest.skipIf( GafferTest.inCI(), "Performance not relevant on CI platform" )
	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 5)
	def testInPerf( self ):
		self.mergePerf( GafferImage.Merge.Operation.In, False )

	@unittest.skipIf( GafferTest.inCI(), "Performance not relevant on CI platform" )
	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 5)
	def testInMismatchPerf( self ):
		self.mergePerf( GafferImage.Merge.Operation.In, True )

	@unittest.skipIf( GafferTest.inCI(), "Performance not relevant on CI platform" )
	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 5)
	def testOutPerf( self ):
		self.mergePerf( GafferImage.Merge.Operation.Out, False )

	@unittest.skipIf( GafferTest.inCI(), "Performance not relevant on CI platform" )
	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 5)
	def testOutMismatchPerf( self ):
		self.mergePerf( GafferImage.Merge.Operation.Out, True )

	@unittest.skipIf( GafferTest.inCI(), "Performance not relevant on CI platform" )
	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 5)
	def testMaskPerf( self ):
		self.mergePerf( GafferImage.Merge.Operation.Mask, False )

	@unittest.skipIf( GafferTest.inCI(), "Performance not relevant on CI platform" )
	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 5)
	def testMaskMismatchPerf( self ):
		self.mergePerf( GafferImage.Merge.Operation.Mask, True )

	@unittest.skipIf( GafferTest.inCI(), "Performance not relevant on CI platform" )
	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 5)
	def testOutPerf( self ):
		self.mergePerf( GafferImage.Merge.Operation.Out, False )

	@unittest.skipIf( GafferTest.inCI(), "Performance not relevant on CI platform" )
	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 5)
	def testOutMismatchPerf( self ):
		self.mergePerf( GafferImage.Merge.Operation.Out, True )

	@unittest.skipIf( GafferTest.inCI(), "Performance not relevant on CI platform" )
	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 5)
	def testMaskPerf( self ):
		self.mergePerf( GafferImage.Merge.Operation.Mask, False )

	@unittest.skipIf( GafferTest.inCI(), "Performance not relevant on CI platform" )
	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 5)
	def testMaskMismatchPerf( self ):
		self.mergePerf( GafferImage.Merge.Operation.Mask, True )

	@unittest.skipIf( GafferTest.inCI(), "Performance not relevant on CI platform" )
	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 5)
	def testMattePerf( self ):
		self.mergePerf( GafferImage.Merge.Operation.Matte, False )

	@unittest.skipIf( GafferTest.inCI(), "Performance not relevant on CI platform" )
	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 5)
	def testMatteMismatchPerf( self ):
		self.mergePerf( GafferImage.Merge.Operation.Matte, True )

	@unittest.skipIf( GafferTest.inCI(), "Performance not relevant on CI platform" )
	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 5)
	def testMultiplyPerf( self ):
		self.mergePerf( GafferImage.Merge.Operation.Multiply, False )

	@unittest.skipIf( GafferTest.inCI(), "Performance not relevant on CI platform" )
	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 5)
	def testMultiplyMismatchPerf( self ):
		self.mergePerf( GafferImage.Merge.Operation.Multiply, True )

	@unittest.skipIf( GafferTest.inCI(), "Performance not relevant on CI platform" )
	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 5)
	def testOverPerf( self ):
		self.mergePerf( GafferImage.Merge.Operation.Over, False )

	@unittest.skipIf( GafferTest.inCI(), "Performance not relevant on CI platform" )
	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 5)
	def testOverMismatchPerf( self ):
		self.mergePerf( GafferImage.Merge.Operation.Over, True )

	@unittest.skipIf( GafferTest.inCI(), "Performance not relevant on CI platform" )
	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 5)
	def testSubtractPerf( self ):
		self.mergePerf( GafferImage.Merge.Operation.Subtract, False )

	@unittest.skipIf( GafferTest.inCI(), "Performance not relevant on CI platform" )
	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 5)
	def testSubtractMismatchPerf( self ):
		self.mergePerf( GafferImage.Merge.Operation.Subtract, True )

	@unittest.skipIf( GafferTest.inCI(), "Performance not relevant on CI platform" )
	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 5)
	def testDifferencePerf( self ):
		self.mergePerf( GafferImage.Merge.Operation.Difference, False )

	@unittest.skipIf( GafferTest.inCI(), "Performance not relevant on CI platform" )
	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 5)
	def testDifferenceMismatchPerf( self ):
		self.mergePerf( GafferImage.Merge.Operation.Difference, True )

	@unittest.skipIf( GafferTest.inCI(), "Performance not relevant on CI platform" )
	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 5)
	def testUnderPerf( self ):
		self.mergePerf( GafferImage.Merge.Operation.Under, False )

	@unittest.skipIf( GafferTest.inCI(), "Performance not relevant on CI platform" )
	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 5)
	def testUnderMismatchPerf( self ):
		self.mergePerf( GafferImage.Merge.Operation.Under, True )

	@unittest.skipIf( GafferTest.inCI(), "Performance not relevant on CI platform" )
	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 5)
	def testMinPerf( self ):
		self.mergePerf( GafferImage.Merge.Operation.Min, False )

	@unittest.skipIf( GafferTest.inCI(), "Performance not relevant on CI platform" )
	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 5)
	def testMinMismatchPerf( self ):
		self.mergePerf( GafferImage.Merge.Operation.Min, True )

	@unittest.skipIf( GafferTest.inCI(), "Performance not relevant on CI platform" )
	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 5)
	def testMaxPerf( self ):
		self.mergePerf( GafferImage.Merge.Operation.Max, False )

	@unittest.skipIf( GafferTest.inCI(), "Performance not relevant on CI platform" )
	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 5)
	def testMaxMismatchPerf( self ):
		self.mergePerf( GafferImage.Merge.Operation.Max, True )

if __name__ == "__main__":
	unittest.main()
