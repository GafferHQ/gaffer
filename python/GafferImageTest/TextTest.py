##########################################################################
#
#  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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
import GafferImage
import GafferImageTest

class TextTest( GafferImageTest.ImageTestCase ) :

	def testDirtyPropagation( self ) :

		# This exposed a crash bug in the Shape
		# base class.

		t = GafferImage.Text()
		t["text"].setValue( "hi" )

	def testPremultiplication( self ) :

		constant = GafferImage.Constant()
		constant["color"].setValue( imath.Color4f( 0 ) )

		text = GafferImage.Text()
		text["in"].setInput( constant["out"] )

		stats = GafferImage.ImageStats()
		stats["in"].setInput( text["out"] )
		stats["area"].setValue( text["out"]["dataWindow"].getValue() )

		self.assertEqual( stats["max"].getValue(), imath.Color4f( 1, 1, 1, 1 ) )

		text["color"]["a"].setValue( 0.5 )
		self.assertEqual( stats["max"].getValue(), imath.Color4f( 0.5, 0.5, 0.5, 0.5 ) )

		text["color"].setValue( imath.Color4f( 0.5, 0.25, 1, 0.5 ) )
		self.assertEqual( stats["max"].getValue(), imath.Color4f( 0.25, 0.125, 0.5, 0.5 ) )

	def testDataWindow( self ) :

		text = GafferImage.Text()
		text["text"].setValue( "a" )
		w = text["out"]["dataWindow"].getValue()

		text["text"].setValue( "ab" )
		w2 = text["out"]["dataWindow"].getValue()

		self.assertEqual( w.min(), w2.min() )
		self.assertGreater( w2.max().x, w.max().x )
		self.assertGreater( w2.max().y, w.max().y )

	def testDefaultFormat( self ) :

		text = GafferImage.Text()
		with Gaffer.Context() as c :
			GafferImage.FormatPlug().setDefaultFormat( c, GafferImage.Format( 100, 200, 2 ) )
			self.assertEqual( text["out"]["format"].getValue(), GafferImage.Format( 100, 200, 2 ) )

	def testExpectedResult( self ) :

		constant = GafferImage.Constant()
		constant["color"].setValue( imath.Color4f( 0.25, 0.5, 0.75, 1 ) )
		constant["format"].setValue( GafferImage.Format( 100, 100 ) )

		text = GafferImage.Text()
		text["in"].setInput( constant["out"] )
		text["color"].setValue( imath.Color4f( 1, 0.75, 0.5, 1 ) )
		text["size"].setValue( imath.V2i( 20 ) )
		text["area"].setValue( imath.Box2i( imath.V2i( 5 ), imath.V2i( 95 ) ) )
		text["transform"]["pivot"].setValue( imath.V2f( 50 ) )
		text["transform"]["rotate"].setValue( 90 )

		reader = GafferImage.ImageReader()
		reader["fileName"].setValue( os.path.dirname( __file__ ) + "/images/text.exr" )

		self.assertImagesEqual( text["out"], reader["out"], ignoreMetadata = True, maxDifference = 0.001 )

	def testArea( self ) :

		text = GafferImage.Text()
		text["text"].setValue( "a a a a a a a a" )
		text["size"].setValue( imath.V2i( 20 ) )
		text["area"].setValue( imath.Box2i( imath.V2i( 0 ), imath.V2i( 100 ) ) )

		self.assertEqual( text["out"].dataWindow(), imath.Box2i( imath.V2i( 1, 58 ), imath.V2i( 83, 92 ) ) )

		text["area"].setValue( imath.Box2i( imath.V2i( 0 ), imath.V2i( 200 ) ) )
		self.assertEqual( text["out"].dataWindow(), imath.Box2i( imath.V2i( 1, 181 ), imath.V2i( 137, 192 ) ) )

		text["area"].setValue( imath.Box2i( imath.V2i( 0 ), imath.V2i( 5, 200 ) ) )
		self.assertEqual( text["out"].dataWindow(), imath.Box2i( imath.V2i( 1, 20 ), imath.V2i( 11, 192 ) ) )

		text["text"].setValue( "longWord\nlongWord\nlongWord" )
		text["area"].setValue( imath.Box2i( imath.V2i( 0 ), imath.V2i( 100 ) ) )

		self.assertEqual( text["out"].dataWindow(), imath.Box2i( imath.V2i( 1, 31 ), imath.V2i( 95, 96 ) ) )

		# If the text box is too short horizontally to fit a single word in, this doesn't affect anything,
		# since we don't wrap individual words ( this test ensures that we don't add vertical space in
		# this case, which wouldn't help fit the text in
		shortText = GafferImage.Text()
		shortText["text"].setValue( "longWord\nlongWord\nlongWord" )
		shortText["size"].setValue( imath.V2i( 20 ) )
		shortText["area"].setValue( imath.Box2i( imath.V2i( 0 ), imath.V2i( 5, 100 ) ) )
		shortText["text"].setValue( "longWord\nlongWord\nlongWord" )
		self.assertImagesEqual( text["out"], shortText["out"], ignoreMetadata = True, maxDifference = 0.001 )

	def testHorizontalAlignment( self ) :

		text = GafferImage.Text()

		text["horizontalAlignment"].setValue( GafferImage.Text.HorizontalAlignment.Left )
		leftDW = text["out"]["dataWindow"].getValue()

		text["horizontalAlignment"].setValue( GafferImage.Text.HorizontalAlignment.Right )
		rightDW = text["out"]["dataWindow"].getValue()

		text["horizontalAlignment"].setValue( GafferImage.Text.HorizontalAlignment.Center )
		centerDW = text["out"]["dataWindow"].getValue()

		self.assertLess( leftDW.min().x, centerDW.min().x )
		self.assertLess( centerDW.min().x, rightDW.min().x )

		# Delta of 1 pixel is ok because layout is done in floating point space,
		# and then must be rounded to pixel space to make the enclosing data window.
		self.assertAlmostEqual( leftDW.size().x, centerDW.size().x, delta = 1 )
		self.assertAlmostEqual( centerDW.size().x, rightDW.size().x, delta = 1 )

	def testVerticalAlignment( self ) :

		text = GafferImage.Text()

		text["verticalAlignment"].setValue( GafferImage.Text.VerticalAlignment.Bottom )
		bottomDW = text["out"]["dataWindow"].getValue()

		text["verticalAlignment"].setValue( GafferImage.Text.VerticalAlignment.Top )
		topDW = text["out"]["dataWindow"].getValue()

		text["verticalAlignment"].setValue( GafferImage.Text.VerticalAlignment.Center )
		centerDW = text["out"]["dataWindow"].getValue()

		self.assertLess( bottomDW.min().y, centerDW.min().y )
		self.assertLess( centerDW.min().y, topDW.min().y )

		# Delta of 1 pixel is ok because layout is done in floating point space,
		# and then must be rounded to pixel space to make the enclosing data window.
		self.assertAlmostEqual( bottomDW.size().y, centerDW.size().y, delta = 1 )
		self.assertAlmostEqual( centerDW.size().y, topDW.size().y, delta = 1 )

	def testNonFlatThrows( self ) :

		text = GafferImage.Text()
		text["size"].setValue( imath.V2i( 20 ) )
		text["area"].setValue( imath.Box2i( imath.V2i( 5 ), imath.V2i( 95 ) ) )

		self.assertRaisesDeepNotSupported( text )

	def testImagePlugs( self ) :

		constant = GafferImage.Constant()
		constant["format"].setValue( GafferImage.Format( imath.Box2i( imath.V2i( 0 ), imath.V2i( 512 ) ), 1 ) )
		constant["color"].setValue( imath.Color4f( 0 ) )

		text = GafferImage.Text()
		text["in"].setInput( constant["out"] )

		text["out"]["format"].getValue()
		text["out"]["dataWindow"].getValue()
		text["out"]["metadata"].getValue()
		text["out"]["channelNames"].getValue()
		self.assertFalse( text["out"]["deep"].getValue() )

		c = Gaffer.Context( Gaffer.Context.current() )
		c["image:channelName"] = "R"
		c["image:tileOrigin"] = imath.V2i( 0 )

		with c :
			text["out"]["channelData"].getValue()

	def testUnparenting( self ) :

		t1 = GafferImage.Text()
		t2 = GafferImage.Text()

		s = Gaffer.ScriptNode()
		s.addChild( t2 )
		s.removeChild( t2 )

		self.assertImageHashesEqual( t1["out"], t2["out"] )
		self.assertImagesEqual( t1["out"], t2["out"] )

	def testDisable( self ) :

		c = GafferImage.Constant()
		c["color"].setValue( imath.Color4f( 1, 0, 0, 0.5, ) )

		t = GafferImage.Text()
		t["in"].setInput( c["out"] )
		t["enabled"].setValue( False )

		self.assertImagesEqual( c["out"], t["out"] )

		t["shadow"].setValue( True )
		self.assertImagesEqual( c["out"], t["out"] )

	def testShadowAssertions( self ) :

		# This used to trigger invalid assertions

		t = GafferImage.Text()
		dataWindow = t["out"]["dataWindow"].getValue()
		tile = t["out"].channelData( "R", GafferImage.ImagePlug.tileOrigin( dataWindow.min() ) )

		t["shadow"].setValue( True )
		t["shadowColor"].setValue( imath.Color4f( 0.5 ) )

		shadowDataWindow = t["out"]["dataWindow"].getValue()

		self.assertEqual( shadowDataWindow.min().x, dataWindow.min().x )
		self.assertEqual( shadowDataWindow.max().y, dataWindow.max().y )
		self.assertGreater( shadowDataWindow.max().x, dataWindow.max().x )
		self.assertLess( shadowDataWindow.min().y, dataWindow.min().y )

		self.assertEqual( t["out"]["channelNames"].getValue(), IECore.StringVectorData( [ "R", "G", "B", "A" ] ) )

		shadowTile = t["out"].channelData( "R", GafferImage.ImagePlug.tileOrigin( dataWindow.min() ) )

		self.assertNotEqual( shadowTile, tile )

	def testNoSerialisationOfInternalConnections( self ) :

		script = Gaffer.ScriptNode()
		script["text"] = GafferImage.Text()
		self.assertNotIn( "setInput", script.serialise() )

if __name__ == "__main__":
	unittest.main()
