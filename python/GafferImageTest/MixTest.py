##########################################################################
#
#  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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
import six
import imath

import IECore

import Gaffer
import GafferTest
import GafferImage
import GafferImageTest

class MixTest( GafferImageTest.ImageTestCase ) :

	rPath = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/redWithDataWindow.100x100.exr" )
	gPath = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/greenWithDataWindow.100x100.exr" )
	checkerPath = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/checkerboard.100x100.exr" )
	checkerNegativeDataWindowPath = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/checkerWithNegativeDataWindow.200x150.exr" )
	checkerMixPath = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/checkerMix.100x100.exr" )
	representativeDeepImagePath = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/representativeDeepImage.exr" )
	radialPath = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/radial.exr" )

	# Do several tests to check the cache is working correctly:
	def testHashes( self ) :

		r1 = GafferImage.ImageReader()
		r1["fileName"].setValue( self.checkerPath )

		r2 = GafferImage.ImageReader()
		r2["fileName"].setValue( self.gPath )

		##########################################
		# Test to see if the hash changes.
		##########################################

		mix = GafferImage.Mix()

		mix["in"][0].setInput( r1["out"] )
		mix["in"][1].setInput( r2["out"] )
		h1 = GafferImage.ImageAlgo.imageHash( mix["out"] )

		# Switch the inputs.
		mix["in"][1].setInput( r1["out"] )
		mix["in"][0].setInput( r2["out"] )
		h2 = GafferImage.ImageAlgo.imageHash( mix["out"] )

		self.assertNotEqual( h1, h2 )

	def testPassThroughs( self ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.rPath )

		g = GafferImage.ImageReader()
		g["fileName"].setValue( self.gPath )

		mix = GafferImage.Mix()

		input1Hash = GafferImage.ImageAlgo.imageHash( r["out"] )
		mix["in"][0].setInput( r["out"] )
		mix["in"][1].setInput( g["out"] )
		mix["mix"].setValue( 0.5 )

		##########################################
		# With a mix applied, the hashes don't match either input,
		# and the data window is merged
		##########################################

		self.assertNotEqual( GafferImage.ImageAlgo.imageHash( mix["out"] ), input1Hash )
		self.assertEqual( mix["out"]["dataWindow"].getValue(), imath.Box2i( imath.V2i( 20 ), imath.V2i( 75 ) ) )

		##########################################
		# Test that if we disable the node the hash gets passed through.
		##########################################

		mix["enabled"].setValue(False)
		self.assertEqual( GafferImage.ImageAlgo.imageHash( mix["out"] ), input1Hash )
		self.assertEqual( mix["out"]["dataWindow"].getValue(), imath.Box2i( imath.V2i( 20 ), imath.V2i( 70 ) ) )
		self.assertImagesEqual( mix["out"], r["out"] )


		##########################################
		# Or if we enable but set mix to 0
		##########################################

		mix["enabled"].setValue( True )
		mix["mix"].setValue( 0 )
		self.assertEqual( GafferImage.ImageAlgo.imageHash( mix["out"] ), input1Hash )
		self.assertEqual( mix["out"]["dataWindow"].getValue(), imath.Box2i( imath.V2i( 20 ), imath.V2i( 70 ) ) )
		self.assertImagesEqual( mix["out"], r["out"] )

		##########################################
		# Set mix to 1 to get pass through of other input
		# In this case, the overall image hash won't match because it still takes metadata from the first input
		# But we can check the other components
		##########################################

		mix["mix"].setValue( 1 )

		self.assertEqual( mix["out"]["dataWindow"].hash(), g["out"]["dataWindow"].hash() )
		self.assertEqual( mix["out"]["channelNames"].hash(), g["out"]["channelNames"].hash() )

		# Just check the first tile of the data to make sure hashes are passing through
		with Gaffer.Context( Gaffer.Context.current() ) as c :
			c[ "image:channelName" ] = IECore.StringData( "G" )
			c[ "image:tileOrigin" ] = IECore.V2iData( imath.V2i( 0, 0 ) )
			self.assertEqual( mix["out"]["channelData"].hash(), g["out"]["channelData"].hash() )

		self.assertEqual( mix["out"]["dataWindow"].getValue(), imath.Box2i( imath.V2i( 25 ), imath.V2i( 75 ) ) )
		self.assertImagesEqual( mix["out"], g["out"], ignoreMetadata = True )

	# Overlay a red and green tile of different data window sizes with a checkered mask and check the data window is expanded on the result and looks as we expect.
	def testMaskedMix( self ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.rPath )

		g = GafferImage.ImageReader()
		g["fileName"].setValue( self.gPath )

		mask = GafferImage.ImageReader()
		mask["fileName"].setValue( self.checkerPath )

		mix = GafferImage.Mix()
		mix["in"][0].setInput( r["out"] )
		mix["in"][1].setInput( g["out"] )
		mix["maskChannel"].setValue( "R" )
		mix["mask"].setInput( mask["out"] )

		expected = GafferImage.ImageReader()
		expected["fileName"].setValue( self.checkerMixPath )

		self.assertImagesEqual( mix["out"], expected["out"], maxDifference = 0.001, ignoreMetadata = True )

	def testAffects( self ) :

		c1 = GafferImage.Constant()
		c2 = GafferImage.Constant()

		m = GafferImage.Mix()
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

		m = GafferImage.Mix()

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

		m = GafferImage.Mix()
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

		mask = GafferImage.Constant()
		mask["format"].setValue( GafferImage.Format( 500, 500, 1.0 ) )
		mask["color"].setValue( imath.Color4f( 0.75 ) )

		aCrop = GafferImage.Crop()
		aCrop["in"].setInput( a["out"] )
		aCrop["areaSource"].setValue( aCrop.AreaSource.Area )
		aCrop["area"].setValue( imath.Box2i( imath.V2i( 50 ), imath.V2i( 162 ) ) )
		aCrop["affectDisplayWindow"].setValue( False )

		m = GafferImage.Mix()
		m["in"][0].setInput( b["out"] )
		m["in"][1].setInput( aCrop["out"] )
		m["mask"].setInput( mask["out"] )

		redSampler = GafferImage.Sampler( m["out"], "R", m["out"]["format"].getValue().getDisplayWindow() )
		greenSampler = GafferImage.Sampler( m["out"], "G", m["out"]["format"].getValue().getDisplayWindow() )
		blueSampler = GafferImage.Sampler( m["out"], "B", m["out"]["format"].getValue().getDisplayWindow() )

		def sample( x, y ) :

			return imath.Color3f(
				redSampler.sample( x, y ),
				greenSampler.sample( x, y ),
				blueSampler.sample( x, y ),
			)

		# We should only have green in areas which are inside
		# the data window of aCrop. But we still only take 25%
		# of the red everywhere

		self.assertEqual( sample( 49, 49 ), imath.Color3f( 0.25, 0, 0 ) )
		self.assertEqual( sample( 50, 50 ), imath.Color3f( 0.25, 0.75, 0 ) )
		self.assertEqual( sample( 161, 161 ), imath.Color3f( 0.25, 0.75, 0 ) )
		self.assertEqual( sample( 162, 162 ), imath.Color3f( 0.25, 0, 0 ) )

	def testLargeDataWindowAddedToSmall( self ) :

		b = GafferImage.Constant()
		b["format"].setValue( GafferImage.Format( 500, 500, 1.0 ) )
		b["color"].setValue( imath.Color4f( 1, 0, 0, 1 ) )

		a = GafferImage.Constant()
		a["format"].setValue( GafferImage.Format( 500, 500, 1.0 ) )
		a["color"].setValue( imath.Color4f( 0, 1, 0, 1 ) )

		mask = GafferImage.Constant()
		mask["format"].setValue( GafferImage.Format( 500, 500, 1.0 ) )
		mask["color"].setValue( imath.Color4f( 0.5 ) )

		bCrop = GafferImage.Crop()
		bCrop["in"].setInput( b["out"] )
		bCrop["areaSource"].setValue( bCrop.AreaSource.Area )
		bCrop["area"].setValue( imath.Box2i( imath.V2i( 50 ), imath.V2i( 162 ) ) )
		bCrop["affectDisplayWindow"].setValue( False )

		m = GafferImage.Mix()
		m["in"][0].setInput( bCrop["out"] )
		m["in"][1].setInput( a["out"] )
		m["mask"].setInput( mask["out"] )

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

		self.assertEqual( sample( 49, 49 ), imath.Color3f( 0, 0.5, 0 ) )
		self.assertEqual( sample( 50, 50 ), imath.Color3f( 0.5, 0.5, 0 ) )
		self.assertEqual( sample( 161, 161 ), imath.Color3f( 0.5, 0.5, 0 ) )
		self.assertEqual( sample( 162, 162 ), imath.Color3f( 0, 0.5, 0 ) )

	def testChannelRequest( self ) :

		a = GafferImage.Constant()
		a["color"].setValue( imath.Color4f( 0.1, 0.2, 0.3, 0.4 ) )

		ad = GafferImage.DeleteChannels()
		ad["in"].setInput( a["out"] )
		ad["mode"].setValue( GafferImage.DeleteChannels.Mode.Delete )
		ad["channels"].setValue( IECore.StringVectorData( [ "R" ] ) )

		b = GafferImage.Constant()
		b["color"].setValue( imath.Color4f( 1.0, 0.3, 0.1, 0.2 ) )

		bd = GafferImage.DeleteChannels()
		bd["in"].setInput( b["out"] )
		bd["mode"].setValue( GafferImage.DeleteChannels.Mode.Delete )
		bd["channels"].setValue( IECore.StringVectorData( [ "G" ] ) )

		m = GafferImage.Constant()
		m["color"].setValue( imath.Color4f( 0.5 ) )

		mix = GafferImage.Mix()
		mix["in"][0].setInput( ad["out"] )
		mix["in"][1].setInput( bd["out"] )
		mix["mask"].setInput( m["out"] )

		sampler = GafferImage.ImageSampler()
		sampler["image"].setInput( mix["out"] )
		sampler["pixel"].setValue( imath.V2f( 10 ) )

		self.assertAlmostEqual( sampler["color"]["r"].getValue(), ( 0.0 + 1.0 ) * 0.5 )
		self.assertAlmostEqual( sampler["color"]["g"].getValue(), ( 0.2 + 0.0 ) * 0.5 )
		self.assertAlmostEqual( sampler["color"]["b"].getValue(), ( 0.3 + 0.1 ) * 0.5 )
		self.assertAlmostEqual( sampler["color"]["a"].getValue(), ( 0.4 + 0.2 ) * 0.5 )

	def testDefaultFormat( self ) :

		a = GafferImage.Constant()
		a["format"].setValue( GafferImage.Format( 100, 200 ) )

		m = GafferImage.Mix()
		m["in"][1].setInput( a["out"] )

		with Gaffer.Context() as c :
			GafferImage.FormatPlug().setDefaultFormat( c, GafferImage.Format( 1000, 2000 ) )
			self.assertEqual( m["out"]["format"].getValue(), GafferImage.Format( 1000, 2000 ) )

	def testDataWindowWhenBNotConnected( self ) :

		a = GafferImage.Constant()
		a["format"].setValue( GafferImage.Format( 100, 200 ) )

		m = GafferImage.Mix()
		m["in"][1].setInput( a["out"] )

		self.assertEqual( m["out"]["dataWindow"].getValue(), a["out"]["dataWindow"].getValue() )

	def testMixParm( self ) :

		b = GafferImage.Constant()
		b["format"].setValue( GafferImage.Format( 50, 50, 1.0 ) )
		b["color"].setValue( imath.Color4f( 1, 0, 0, 1 ) )

		a = GafferImage.Constant()
		a["format"].setValue( GafferImage.Format( 50, 50, 1.0 ) )
		a["color"].setValue( imath.Color4f( 0, 1, 0, 1 ) )

		mask = GafferImage.Constant()
		mask["format"].setValue( GafferImage.Format( 50, 50, 1.0 ) )
		mask["color"].setValue( imath.Color4f( 0.5 ) )

		m = GafferImage.Mix()
		m["in"][0].setInput( b["out"] )
		m["in"][1].setInput( a["out"] )


		def sample( x, y ) :
			redSampler = GafferImage.Sampler( m["out"], "R", m["out"]["format"].getValue().getDisplayWindow() )
			greenSampler = GafferImage.Sampler( m["out"], "G", m["out"]["format"].getValue().getDisplayWindow() )
			blueSampler = GafferImage.Sampler( m["out"], "B", m["out"]["format"].getValue().getDisplayWindow() )

			return imath.Color3f(
				redSampler.sample( x, y ),
				greenSampler.sample( x, y ),
				blueSampler.sample( x, y ),
			)

		# Using just mix
		m["mix"].setValue( 0.75 )
		self.assertEqual( sample( 49, 49 ), imath.Color3f( 0.25, 0.75, 0 ) )
		m["mix"].setValue( 0.25 )
		self.assertEqual( sample( 49, 49 ), imath.Color3f( 0.75, 0.25, 0 ) )

		# Using mask multiplied with mix
		m["mask"].setInput( mask["out"] )
		self.assertEqual( sample( 49, 49 ), imath.Color3f( 0.875, 0.125, 0 ) )

		# Using invalid channel of mask defaults to just mix
		m["maskChannel"].setValue( "DOES_NOT_EXIST" )
		self.assertEqual( sample( 49, 49 ), imath.Color3f( 0.75, 0.25, 0 ) )

	def testDeepWithFlatMask( self ) :

		# Set up a mask
		maskReader = GafferImage.ImageReader()
		maskReader["fileName"].setValue( self.radialPath )

		maskText = GafferImage.Text()
		maskText["in"].setInput( maskReader["out"] )
		maskText["area"].setValue( imath.Box2i( imath.V2i( 0, 0 ), imath.V2i( 256, 256 ) ) )
		maskText["text"].setValue( 'Test\nTest\nTest\nTest' )

		maskOffset = GafferImage.Offset()
		maskOffset["in"].setInput( maskText["out"] )

		representativeDeepImage = GafferImage.ImageReader()
		representativeDeepImage["fileName"].setValue( self.representativeDeepImagePath )

		deepGradeBlack = GafferImage.Grade()
		deepGradeBlack["in"].setInput( representativeDeepImage["out"] )
		deepGradeBlack["multiply"].setValue( imath.Color4f( 0, 0, 0, 1 ) )

		deepMix = GafferImage.Mix()
		deepMix["in"]["in0"].setInput( representativeDeepImage["out"] )
		deepMix["in"]["in1"].setInput( deepGradeBlack["out"] )
		deepMix["mask"].setInput( maskOffset["out"] )
		deepMix["maskChannel"].setValue( 'R' )

		postFlatten = GafferImage.DeepToFlat()
		postFlatten["in"].setInput( deepMix["out"] )

		preFlatten = GafferImage.DeepToFlat()
		preFlatten["in"].setInput( representativeDeepImage["out"] )

		flatGradeBlack = GafferImage.Grade()
		flatGradeBlack["in"].setInput( preFlatten["out"] )
		flatGradeBlack["multiply"].setValue( imath.Color4f( 0, 0, 0, 1 ) )

		flatMix = GafferImage.Mix()
		flatMix["in"]["in0"].setInput( preFlatten["out"] )
		flatMix["in"]["in1"].setInput( flatGradeBlack["out"] )
		flatMix["mask"].setInput( maskOffset["out"] )
		flatMix["maskChannel"].setValue( 'R' )

		for o in [ imath.V2i( 0, 0 ), imath.V2i( -3, -8 ), imath.V2i( -7, -79 ), imath.V2i( 12, 8 ) ]:
			maskOffset["offset"].setValue( o )

			self.assertImagesEqual( postFlatten["out"], flatMix["out"], maxDifference = 0.000003 )

	def testDeepMix( self ):
		representativeDeepImage = GafferImage.ImageReader()
		representativeDeepImage["fileName"].setValue( self.representativeDeepImagePath )

		# Easier to compare colors if we clamp - this requires unpremulting
		unpremultiply = GafferImage.Unpremultiply()
		unpremultiply["in"].setInput( representativeDeepImage["out"] )

		clamp = GafferImage.Grade()
		clamp["in"].setInput( unpremultiply["out"] )
		clamp["whiteClamp"].setValue( True )

		premultiply = GafferImage.Premultiply()
		premultiply["in"].setInput( clamp["out"] )


		# Create a deep image containing a mixture of samples from two offset copies, where
		# the "offsetted" channel contains a mask showing which of the samples come from
		# the offsetted copy
		offset = GafferImage.Offset()
		offset["in"].setInput( premultiply["out"] )
		offset["offset"].setValue( imath.V2i( 33, -25 ) )

		addOffsetMarker = GafferImage.Shuffle()
		addOffsetMarker["channels"].addChild( GafferImage.Shuffle.ChannelPlug( "offsetted", "__white" ) )
		addOffsetMarker["in"].setInput( offset["out"] )

		deepMerge = GafferImage.DeepMerge()
		deepMerge["in"].addChild( GafferImage.ImagePlug( "in2", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, ) )
		deepMerge["in"]["in0"].setInput( addOffsetMarker["out"] )
		deepMerge["in"]["in1"].setInput( premultiply["out"] )

		gradeBlack = GafferImage.Grade()
		gradeBlack["in"].setInput( deepMerge["out"] )
		gradeBlack["channels"].setValue( '[RGBA]' )
		gradeBlack["multiply"].setValue( imath.Color4f( 0, 0, 0, 0 ) )

		mix = GafferImage.Mix( "mix" )
		mix["in"]["in0"].setInput( deepMerge["out"] )
		mix["in"]["in1"].setInput( gradeBlack["out"] )
		mix["mask"].setInput( deepMerge["out"] )
		mix["maskChannel"].setValue( 'offsetted' )

		mixedFlat = GafferImage.DeepToFlat()
		mixedFlat["in"].setInput( mix["out"] )

		mergeRef = GafferImage.DeepToFlat()
		mergeRef["in"].setInput( deepMerge["out"] )

		startRef = GafferImage.DeepToFlat()
		startRef["in"].setInput( premultiply["out"] )

		startDiff = GafferImage.Merge()
		startDiff["in"]["in0"].setInput( startRef["out"] )
		startDiff["in"]["in1"].setInput( mixedFlat["out"] )
		startDiff["operation"].setValue( GafferImage.Merge.Operation.Difference )

		startDiffStats = GafferImage.ImageStats( "startDiffStats" )
		startDiffStats["in"].setInput( startDiff["out"] )
		startDiffStats["area"].setValue( mix["out"].dataWindow() )

		mergedDiff = GafferImage.Merge()
		mergedDiff["in"]["in0"].setInput( mergeRef["out"] )
		mergedDiff["in"]["in1"].setInput( mixedFlat["out"] )
		mergedDiff["operation"].setValue( GafferImage.Merge.Operation.Difference )

		mergedDiffStats = GafferImage.ImageStats( "mergedDiffStats" )
		mergedDiffStats["in"].setInput( mergedDiff["out"] )
		mergedDiffStats["area"].setValue( mix["out"].dataWindow() )

		# With mix set to 0, the mix outputs the left input with everything
		mix["mix"].setValue( 0.0 )
		self.assertEqual( mergedDiffStats["average"].getValue(), imath.Color4f( 0 ) )
		self.assertEqual( mergedDiffStats["max"].getValue(), imath.Color4f( 0 ) )
		self.assertGreater( startDiffStats["average"].getValue()[3], 0.2 )
		self.assertGreater( startDiffStats["max"].getValue()[3], 0.999  )
		for i in range( 3 ):
			self.assertGreater( startDiffStats["average"].getValue()[i], 0.1 )
			self.assertGreater( startDiffStats["max"].getValue()[i], 0.8 )

		# With mix set to 1, the mix blends the offsetted samples to 0, and outputs just the non-offset
		# samples
		mix["mix"].setValue( 1.0 )
		for i in range( 4 ):
			self.assertAlmostEqual( startDiffStats["average"].getValue()[i], 0 )
			self.assertAlmostEqual( startDiffStats["max"].getValue()[i], 0, places = 5 )
		self.assertGreater( mergedDiffStats["average"].getValue()[3], 0.2 )
		self.assertGreater( mergedDiffStats["max"].getValue()[3], 0.999  )
		for i in range( 3 ):
			self.assertGreater( mergedDiffStats["average"].getValue()[i], 0.1 )
			self.assertGreater( mergedDiffStats["max"].getValue()[i], 0.8 )

		# With the mix in between, the result should be a bit closer to both than the farthest
		# result at either extreme
		mix["mix"].setValue( 0.75 )
		self.assertLess( startDiffStats["average"].getValue()[3], 0.16 )
		self.assertLess( startDiffStats["max"].getValue()[3], 0.8  )
		self.assertLess( mergedDiffStats["average"].getValue()[3], 0.16 )
		self.assertLess( mergedDiffStats["max"].getValue()[3], 0.8  )
		for i in range( 3 ):
			self.assertLess( startDiffStats["average"].getValue()[i], 0.08 )
			self.assertLess( startDiffStats["max"].getValue()[i], 0.7 )
			self.assertLess( mergedDiffStats["average"].getValue()[i], 0.08 )
			self.assertLess( mergedDiffStats["max"].getValue()[i], 0.7 )

	def testMismatchThrows( self ) :

		deep = GafferImage.Empty()
		flat = GafferImage.Constant()

		mix = GafferImage.Mix()
		mix["mix"].setValue( 0.5 )
		mix["in"][0].setInput( flat["out"] )
		mix["in"][1].setInput( flat["out"] )

		self.assertNotEqual( GafferImage.ImageAlgo.imageHash( mix["out"] ), GafferImage.ImageAlgo.imageHash( flat["out"] ) )
		GafferImage.ImageAlgo.tiles( mix["out"] )

		mix["in"][0].setInput( deep["out"] )
		six.assertRaisesRegex( self, RuntimeError, 'Mix.out.deep : Cannot mix between deep and flat image.', GafferImage.ImageAlgo.tiles, mix["out"] )
		mix["in"][0].setInput( flat["out"] )
		mix["in"][1].setInput( deep["out"] )
		six.assertRaisesRegex( self, RuntimeError, 'Mix.out.deep : Cannot mix between deep and flat image.', GafferImage.ImageAlgo.tiles, mix["out"] )

		mix["in"][0].setInput( deep["out"] )
		GafferImage.ImageAlgo.tiles( mix["out"] )

	def testFuzzDataWindows( self ):

		# A bunch of different test images with varying data windows
		file1 = GafferImage.ImageReader()
		file1["fileName"].setValue( self.checkerNegativeDataWindowPath )

		file1Shuffle = GafferImage.Shuffle()
		file1Shuffle["channels"].addChild( GafferImage.Shuffle.ChannelPlug( "A", "R" ) )
		file1Shuffle['in'].setInput( file1['out'] )

		file2 = GafferImage.ImageReader()
		file2["fileName"].setValue( self.checkerPath )

		file2Shuffle = GafferImage.Shuffle()
		file2Shuffle["channels"].addChild( GafferImage.Shuffle.ChannelPlug( "A", "R" ) )
		file2Shuffle['in'].setInput( file2['out'] )

		largeConstant = GafferImage.Constant()
		largeConstant["format"].setValue( GafferImage.Format( imath.Box2i( imath.V2i( 0 ), imath.V2i( 1920, 1080 ) ), 1 ) )
		largeConstant["color"].setValue( imath.Color4f( 0.7, 0.8, 0.9, 0.65 ) )

		smallConstant = GafferImage.Constant()
		smallConstant["format"].setValue( GafferImage.Format( imath.Box2i( imath.V2i( 554, 210 ), imath.V2i( 1265, 869 ) ), 1 ) )
		smallConstant["color"].setValue( imath.Color4f( 0.4, 0.5, 0.6, 0.45 ) )

		leftConstant = GafferImage.Constant()
		leftConstant["format"].setValue( GafferImage.Format( imath.Box2i( imath.V2i( -353, -561 ), imath.V2i( 915, 500 ) ), 1 ) )
		leftConstant["color"].setValue( imath.Color4f( 0.1, 0.2, 0.3, 0.75 ) )

		rightConstant = GafferImage.Constant()
		rightConstant["format"].setValue( GafferImage.Format( imath.Box2i( imath.V2i( 945, 557 ), imath.V2i( 2007, 1117 ) ), 1 ) )
		rightConstant["color"].setValue( imath.Color4f( 0.61, 0.62, 0.63, 0.35 ) )

		Mix = GafferImage.Mix( "Mix" )

		# Create a network using Merge that should match the result of Mix
		MaskPromote = GafferImage.Shuffle( "MaskPromote" )
		MaskPromote["channels"].addChild( GafferImage.Shuffle.ChannelPlug( "R", "A" ) )
		MaskPromote["channels"].addChild( GafferImage.Shuffle.ChannelPlug( "G", "A" ) )
		MaskPromote["channels"].addChild( GafferImage.Shuffle.ChannelPlug( "B", "A" ) )
		MaskPromote["channels"].addChild( GafferImage.Shuffle.ChannelPlug( "A", "A" ) )
		MaskPromote['in'].setInput( Mix['mask'] )

		Input0Mult = GafferImage.Merge( "Input0Mult" )
		Input0Mult["operation"].setValue( GafferImage.Merge.Operation.Multiply )
		Input0Mult['in'][0].setInput( Mix['in'][0] )
		Input0Mult["in"][1].setInput( MaskPromote["out"] )

		Input0Subtract = GafferImage.Merge( "Input0Subtract" )
		Input0Subtract["operation"].setValue( GafferImage.Merge.Operation.Subtract )
		Input0Subtract["in"][0].setInput( Input0Mult["out"] )
		Input0Subtract['in'][1].setInput( Mix['in'][0] )

		Input1Mult = GafferImage.Merge( "Input1Mult" )
		Input1Mult["operation"].setValue( GafferImage.Merge.Operation.Multiply )
		Input1Mult['in'][0].setInput( Mix['in'][1] )
		Input1Mult["in"][1].setInput( MaskPromote["out"] )

		ReferenceMerge = GafferImage.Merge( "ReferenceMerge" )
		ReferenceMerge["operation"].setValue( GafferImage.Merge.Operation.Add )
		ReferenceMerge["in"][0].setInput( Input0Subtract["out"] )
		ReferenceMerge["in"][1].setInput( Input1Mult["out"] )

		# Expand the data window of the reference to match the Mix, so we can compare
		BlackBackground = GafferImage.Shuffle( "BlackBackground" )
		BlackBackground["channels"].addChild( GafferImage.Shuffle.ChannelPlug( "R", "__black" ) )
		BlackBackground["channels"].addChild( GafferImage.Shuffle.ChannelPlug( "G", "__black" ) )
		BlackBackground["channels"].addChild( GafferImage.Shuffle.ChannelPlug( "B", "__black" ) )
		BlackBackground["channels"].addChild( GafferImage.Shuffle.ChannelPlug( "A", "__black" ) )
		BlackBackground["in"].setInput( Mix["out"] )

		ReferenceWithDataWindow = GafferImage.Merge( "ReferenceWithDataWindow" )
		ReferenceWithDataWindow["operation"].setValue( GafferImage.Merge.Operation.Over )
		ReferenceWithDataWindow["in"][0].setInput( BlackBackground["out"] )
		ReferenceWithDataWindow["in"][1].setInput( ReferenceMerge["out"] )

		# For a more thorough test, use the full list of test images - but restricting to just 3 catches
		# most failures, and takes just 2 seconds to test
		#testImages = [ largeConstant, smallConstant, leftConstant, rightConstant, file1Shuffle, file2Shuffle ]
		testImages = [ largeConstant, smallConstant, leftConstant ]
		for input0 in testImages:
			for input1 in testImages:
				for mask in testImages:
					Mix["in"][0].setInput( input0["out"] )
					Mix["in"][1].setInput( input1["out"] )
					Mix["mask"].setInput( mask["out"] )

					self.assertImagesEqual( Mix["out"], ReferenceWithDataWindow["out"], maxDifference = 1e-7 )

if __name__ == "__main__":
	unittest.main()
