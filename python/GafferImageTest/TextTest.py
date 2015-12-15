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
		constant["color"].setValue( IECore.Color4f( 0 ) )

		text = GafferImage.Text()
		text["in"].setInput( constant["out"] )

		stats = GafferImage.ImageStats()
		stats["in"].setInput( text["out"] )
		stats["regionOfInterest"].setValue( text["out"]["dataWindow"].getValue() )

		self.assertEqual( stats["max"].getValue(), IECore.Color4f( 1, 1, 1, 1 ) )

		text["color"]["a"].setValue( 0.5 )
		self.assertEqual( stats["max"].getValue(), IECore.Color4f( 0.5, 0.5, 0.5, 1 ) )

		text["color"].setValue( IECore.Color4f( 0.5, 0.25, 1, 0.5 ) )
		self.assertEqual( stats["max"].getValue(), IECore.Color4f( 0.25, 0.125, 0.5, 1 ) )

	def testDataWindow( self ) :

		text = GafferImage.Text()
		text["text"].setValue( "a" )
		w = text["out"]["dataWindow"].getValue()

		text["text"].setValue( "ab" )
		w2 = text["out"]["dataWindow"].getValue()

		self.assertEqual( w.min, w2.min )
		self.assertGreater( w2.max.x, w.max.x )
		self.assertGreater( w2.max.y, w.max.y )

	def testDefaultFormat( self ) :

		text = GafferImage.Text()
		with Gaffer.Context() as c :
			GafferImage.FormatPlug().setDefaultFormat( c, GafferImage.Format( 100, 200, 2 ) )
			self.assertEqual( text["out"]["format"].getValue(), GafferImage.Format( 100, 200, 2 ) )

	def testExpectedResult( self ) :

		constant = GafferImage.Constant()
		constant["color"].setValue( IECore.Color4f( 0.25, 0.5, 0.75, 1 ) )
		constant["format"].setValue( GafferImage.Format( 100, 100 ) )

		text = GafferImage.Text()
		text["in"].setInput( constant["out"] )
		text["color"].setValue( IECore.Color4f( 1, 0.75, 0.5, 1 ) )
		text["size"].setValue( IECore.V2i( 20 ) )
		text["area"].setValue( IECore.Box2i( IECore.V2i( 5 ), IECore.V2i( 95 ) ) )
		text["transform"]["pivot"].setValue( IECore.V2f( 50 ) )
		text["transform"]["rotate"].setValue( 90 )

		deleteChans = GafferImage.DeleteChannels()
		deleteChans["in"].setInput( text["out"] )
		deleteChans["mode"].setValue( GafferImage.DeleteChannels.Mode.Keep )
		deleteChans["channels"].setValue( IECore.StringVectorData( [ "R", "G", "B", "A" ] ) )

		reader = GafferImage.ImageReader()
		reader["fileName"].setValue( os.path.dirname( __file__ ) + "/images/text.exr" )
		expectedImage = reader['out'].image()

		self.assertImagesEqual( deleteChans["out"], reader["out"], ignoreMetadata = True, maxDifference = 0.001 )

	def testHorizontalAlignment( self ) :

		text = GafferImage.Text()

		text["horizontalAlignment"].setValue( GafferImage.Text.HorizontalAlignment.Left )
		leftDW = text["out"]["dataWindow"].getValue()

		text["horizontalAlignment"].setValue( GafferImage.Text.HorizontalAlignment.Right )
		rightDW = text["out"]["dataWindow"].getValue()

		text["horizontalAlignment"].setValue( GafferImage.Text.HorizontalAlignment.Center )
		centerDW = text["out"]["dataWindow"].getValue()

		self.assertLess( leftDW.min.x, centerDW.min.x )
		self.assertLess( centerDW.min.x, rightDW.min.x )

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

		self.assertLess( bottomDW.min.y, centerDW.min.y )
		self.assertLess( centerDW.min.y, topDW.min.y )

		# Delta of 1 pixel is ok because layout is done in floating point space,
		# and then must be rounded to pixel space to make the enclosing data window.
		self.assertAlmostEqual( bottomDW.size().y, centerDW.size().y, delta = 1 )
		self.assertAlmostEqual( centerDW.size().y, topDW.size().y, delta = 1 )

	# Tests that hashes pass through when the input data is not Flat
	def testNonFlatHashPassThrough( self ) :

		text = GafferImage.Text()
		text["size"].setValue( IECore.V2i( 20 ) )
		text["area"].setValue( IECore.Box2i( IECore.V2i( 5 ), IECore.V2i( 95 ) ) )

		self._testNonFlatHashPassThrough( text )

	def testImagePlugs( self ) :

		constant = GafferImage.Constant()
		constant["format"].setValue( GafferImage.Format( IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 512 ) ), 1 ) )
		constant["color"].setValue( IECore.Color4f( 0 ) )

		text = GafferImage.Text()
		text["in"].setInput( constant["out"] )

		c = Gaffer.Context()
		c["image:channelName"] = "R"
		c["image:tileOrigin"] = IECore.V2i( 0 )

		with c :
			text["out"]["format"].getValue()
			text["out"]["dataWindow"].getValue()
			text["out"]["metadata"].getValue()
			text["out"]["channelNames"].getValue()
			text["out"]["deepState"].getValue()
			text["out"]["sampleOffsets"].getValue()
			text["out"]["channelData"].getValue()

	def testUnparenting( self ) :

		t1 = GafferImage.Text()
		t2 = GafferImage.Text()

		s = Gaffer.ScriptNode()
		s.addChild( t2 )
		s.removeChild( t2 )

		self.assertImageHashesEqual( t1["out"], t2["out"] )
		self.assertImagesEqual( t1["out"], t2["out"] )

if __name__ == "__main__":
	unittest.main()
