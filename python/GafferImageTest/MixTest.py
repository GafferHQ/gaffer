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
	checkerMixPath = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/checkerMix.100x100.exr" )

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
		with Gaffer.Context() as c :
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

if __name__ == "__main__":
	unittest.main()
