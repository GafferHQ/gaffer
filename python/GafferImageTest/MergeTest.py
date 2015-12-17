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

import IECore

import Gaffer
import GafferTest
import GafferImage
import GafferImageTest

class MergeTest( GafferImageTest.ImageTestCase ) :

	rPath = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/redWithDataWindow.100x100.exr" )
	gPath = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/greenWithDataWindow.100x100.exr" )
	bPath = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/blueWithDataWindow.100x100.exr" )
	checkerPath = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/checkerboard.100x100.exr" )
	checkerRGBPath = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/rgbOverChecker.100x100.exr" )
	rgbPath = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/rgb.100x100.exr" )

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
		h1 = merge["out"].image().hash()

		# Switch the inputs.
		merge["in"][1].setInput( r1["out"] )
		merge["in"][0].setInput( r2["out"] )
		h2 = merge["out"].image().hash()

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
		h1 = merge["out"].image().hash()

		self.assertEqual( h1, expectedHash )

	def testHashPassThrough( self ) :

		r1 = GafferImage.ImageReader()
		r1["fileName"].setValue( self.checkerPath )

		##########################################
		# Test to see if the input has is always passed
		# through if only the first input is connected.
		##########################################

		merge = GafferImage.Merge()
		merge["operation"].setValue( GafferImage.Merge.Operation.Over )

		expectedHash = r1["out"].image().hash()
		merge["in"][0].setInput( r1["out"] )
		h1 = merge["out"].image().hash()

		self.assertEqual( h1, expectedHash )

		##########################################
		# Test that if we disable the node the hash gets passed through.
		##########################################

		merge["enabled"].setValue(False)
		h1 = merge["out"].image().hash()

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
		f["format"].setValue( GafferImage.Format( IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 10 ) ), 1 ) )
		d = GafferImage.ImageMetadata()
		d["metadata"].addMember( "comment", IECore.StringData( "reformated and metadata updated" ) )
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

	def testFileCompatibilityWithVersion0_15( self ) :

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( os.path.dirname( __file__ ) + "/scripts/mergeVersion-0.15.0.0.gfr" )
		s.load()

		self.assertTrue( s["m"]["in"][0].getInput().isSame( s["c1"]["out"] ) )
		self.assertTrue( s["m"]["in"][1].getInput().isSame( s["c2"]["out"] ) )

		self.assertTrue( "in1" not in s["m"] )
		self.assertTrue( "in2" not in s["m"] )

		with s.context() :
			self.assertEqual( s["m"]["out"].channelData( "R", IECore.V2i( 0 ) )[0], 0.75 )

	def testSmallDataWindowOverLarge( self ) :

		b = GafferImage.Constant()
		b["format"].setValue( GafferImage.Format( 500, 500, 1.0 ) )
		b["color"].setValue( IECore.Color4f( 1, 0, 0, 1 ) )

		a = GafferImage.Constant()
		a["format"].setValue( GafferImage.Format( 500, 500, 1.0 ) )
		a["color"].setValue( IECore.Color4f( 0, 1, 0, 1 ) )

		aCrop = GafferImage.Crop()
		aCrop["in"].setInput( a["out"] )
		aCrop["areaSource"].setValue( aCrop.AreaSource.Area )
		aCrop["area"].setValue( IECore.Box2i( IECore.V2i( 50 ), IECore.V2i( 162 ) ) )
		aCrop["affectDisplayWindow"].setValue( False )

		m = GafferImage.Merge()
		m["operation"].setValue( m.Operation.Over )
		m["in"][0].setInput( b["out"] )
		m["in"][1].setInput( aCrop["out"] )

		redSampler = GafferImage.Sampler( m["out"], "R", m["out"]["format"].getValue().getDisplayWindow() )
		greenSampler = GafferImage.Sampler( m["out"], "G", m["out"]["format"].getValue().getDisplayWindow() )
		blueSampler = GafferImage.Sampler( m["out"], "B", m["out"]["format"].getValue().getDisplayWindow() )

		def sample( x, y ) :

			return IECore.Color3f(
				redSampler.sample( x, y ),
				greenSampler.sample( x, y ),
				blueSampler.sample( x, y ),
			)

		# We should only have overed green in areas which are inside
		# the data window of aCrop. Everywhere else we should have
		# red still.

		self.assertEqual( sample( 49, 49 ), IECore.Color3f( 1, 0, 0 ) )
		self.assertEqual( sample( 50, 50 ), IECore.Color3f( 0, 1, 0 ) )
		self.assertEqual( sample( 161, 161 ), IECore.Color3f( 0, 1, 0 ) )
		self.assertEqual( sample( 162, 162 ), IECore.Color3f( 1, 0, 0 ) )

	def testLargeDataWindowAddedToSmall( self ) :

		b = GafferImage.Constant()
		b["format"].setValue( GafferImage.Format( 500, 500, 1.0 ) )
		b["color"].setValue( IECore.Color4f( 1, 0, 0, 1 ) )

		a = GafferImage.Constant()
		a["format"].setValue( GafferImage.Format( 500, 500, 1.0 ) )
		a["color"].setValue( IECore.Color4f( 0, 1, 0, 1 ) )

		bCrop = GafferImage.Crop()
		bCrop["in"].setInput( b["out"] )
		bCrop["areaSource"].setValue( bCrop.AreaSource.Area )
		bCrop["area"].setValue( IECore.Box2i( IECore.V2i( 50 ), IECore.V2i( 162 ) ) )
		bCrop["affectDisplayWindow"].setValue( False )

		m = GafferImage.Merge()
		m["operation"].setValue( m.Operation.Add )
		m["in"][0].setInput( bCrop["out"] )
		m["in"][1].setInput( a["out"] )

		redSampler = GafferImage.Sampler( m["out"], "R", m["out"]["format"].getValue().getDisplayWindow() )
		greenSampler = GafferImage.Sampler( m["out"], "G", m["out"]["format"].getValue().getDisplayWindow() )
		blueSampler = GafferImage.Sampler( m["out"], "B", m["out"]["format"].getValue().getDisplayWindow() )

		def sample( x, y ) :

			return IECore.Color3f(
				redSampler.sample( x, y ),
				greenSampler.sample( x, y ),
				blueSampler.sample( x, y ),
			)

		# We should only have yellow in areas where the background exists,
		# and should have just green everywhere else.

		self.assertEqual( sample( 49, 49 ), IECore.Color3f( 0, 1, 0 ) )
		self.assertEqual( sample( 50, 50 ), IECore.Color3f( 1, 1, 0 ) )
		self.assertEqual( sample( 161, 161 ), IECore.Color3f( 1, 1, 0 ) )
		self.assertEqual( sample( 162, 162 ), IECore.Color3f( 0, 1, 0 ) )

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

		merge["out"].image()

	def testDifference( self ) :

		a = GafferImage.Constant()
		a["color"].setValue( IECore.Color4f( 0.1, 0.2, 0.3, 0.4 ) )

		b = GafferImage.Constant()
		b["color"].setValue( IECore.Color4f( 1, 0.3, 0.1, 0.2 ) )

		merge = GafferImage.Merge()
		merge["in"][0].setInput( a["out"] )
		merge["in"][1].setInput( b["out"] )
		merge["operation"].setValue( GafferImage.Merge.Operation.Difference )

		sampler = GafferImage.ImageSampler()
		sampler["image"].setInput( merge["out"] )
		sampler["pixel"].setValue( IECore.V2f( 10 ) )

		self.assertAlmostEqual( sampler["color"]["r"].getValue(), 0.9 )
		self.assertAlmostEqual( sampler["color"]["g"].getValue(), 0.1 )
		self.assertAlmostEqual( sampler["color"]["b"].getValue(), 0.2 )
		self.assertAlmostEqual( sampler["color"]["a"].getValue(), 0.2 )

	def testChannelRequest( self ) :

		a = GafferImage.Constant()
		a["color"].setValue( IECore.Color4f( 0.1, 0.2, 0.3, 0.4 ) )

		ad = GafferImage.DeleteChannels()
		ad["in"].setInput( a["out"] )
		ad["mode"].setValue( GafferImage.DeleteChannels.Mode.Delete )
		ad["channels"].setValue( IECore.StringVectorData( [ "R" ] ) )

		b = GafferImage.Constant()
		b["color"].setValue( IECore.Color4f( 1.0, 0.3, 0.1, 0.2 ) )

		bd = GafferImage.DeleteChannels()
		bd["in"].setInput( b["out"] )
		bd["mode"].setValue( GafferImage.DeleteChannels.Mode.Delete )
		bd["channels"].setValue( IECore.StringVectorData( [ "G" ] ) )

		merge = GafferImage.Merge()
		merge["in"][0].setInput( ad["out"] )
		merge["in"][1].setInput( bd["out"] )
		merge["operation"].setValue( GafferImage.Merge.Operation.Add )

		sampler = GafferImage.ImageSampler()
		sampler["image"].setInput( merge["out"] )
		sampler["pixel"].setValue( IECore.V2f( 10 ) )

		self.assertAlmostEqual( sampler["color"]["r"].getValue(), 0.0 + 1.0 )
		self.assertAlmostEqual( sampler["color"]["g"].getValue(), 0.2 + 0.0 )
		self.assertAlmostEqual( sampler["color"]["b"].getValue(), 0.3 + 0.1 )
		self.assertAlmostEqual( sampler["color"]["a"].getValue(), 0.4 + 0.2 )

	def testNonFlatHashPassThrough( self ) :

		constant1 = GafferImage.Constant()
		constant1["color"].setValue( IECore.Color4f( 1 ) )

		crop1 = GafferImage.Crop()
		crop1["in"].setInput( constant1["out"] )
		crop1["area"].setValue( IECore.Box2i( IECore.V2i( 10 ), IECore.V2i( 20 ) ) )
		crop1["affectDisplayWindow"].setValue( False )

		constant2 = GafferImage.Constant()
		constant2["color"].setValue( IECore.Color4f( 1 ) )

		crop2 = GafferImage.Crop()
		crop2["in"].setInput( constant2["out"] )
		crop2["area"].setValue( IECore.Box2i( IECore.V2i( 10 ), IECore.V2i( 20 ) ) )
		crop2["affectDisplayWindow"].setValue( False )

		deepMerge = GafferImage.DeepMerge()
		deepMerge["in"][0].setInput( crop1["out"] )
		deepMerge["in"][1].setInput( crop2["out"] )

		merge = GafferImage.Merge()
		merge["in"][0].setInput( deepMerge["out"] )
		merge["in"][1].setInput( crop2["out"] )

		self.assertEqual( deepMerge["out"].imageHash(), merge["out"].imageHash() )

		deepMerge["enabled"].setValue( False )

		self.assertNotEqual( deepMerge["out"].imageHash(), merge["out"].imageHash() )

	def testSecondaryNonFlatIgnored( self ) :

		img = GafferImage.ImageReader()
		img["fileName"].setValue( self.rgbPath )

		constant1 = GafferImage.Constant()
		constant1["color"].setValue( IECore.Color4f( 0.1, 0.2, 0.3, 0.4 ) )
		constant1["z"].setValue( 1.0 )
		constant1["zBack"].setValue( 1.0 )

		constant2 = GafferImage.Constant()
		constant2["color"].setValue( IECore.Color4f( 0.9, 0.8, 0.7, 0.6 ) )
		constant2["z"].setValue( 3.0 )
		constant2["zBack"].setValue( 4.0 )

		deepMerge = GafferImage.DeepMerge()
		deepMerge["in"][0].setInput( constant1["out"] )
		deepMerge["in"][1].setInput( constant2["out"] )

		mergeFlat = GafferImage.Merge()
		mergeFlat["in"][0].setInput( img["out"] )
		mergeFlat["in"][1].setInput( constant1["out"] )

		mergeMixed = GafferImage.Merge()
		mergeMixed["in"][0].setInput( img["out"] )
		mergeMixed["in"][1].setInput( deepMerge["out"] )
		mergeMixed["in"][2].setInput( constant1["out"] )

		self.assertEqual( mergeFlat["out"].imageHash(), mergeMixed["out"].imageHash() )
		self.assertEqual( mergeFlat["out"].image(), mergeMixed["out"].image() )

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

if __name__ == "__main__":
	unittest.main()
