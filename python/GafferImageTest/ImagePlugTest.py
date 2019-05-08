##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
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

class ImagePlugTest( GafferImageTest.ImageTestCase ) :

	def testTileOrigin( self ) :

		ts = GafferImage.ImagePlug.tileSize()

		testCases = [
			( imath.V2i( ts-1, ts-1 ), imath.V2i( 0, 0 ) ),
			( imath.V2i( ts, ts-1 ), imath.V2i( ts, 0 ) ),
			( imath.V2i( ts, ts ), imath.V2i( ts, ts ) ),
			( imath.V2i( ts*3-1, ts+5 ), imath.V2i( ts*2, ts ) ),
			( imath.V2i( ts*3, ts-5 ), imath.V2i( ts*3, 0 ) ),
			( imath.V2i( -ts+ts/2, 0 ), imath.V2i( -ts, 0 ) ),
			( imath.V2i( ts*5+ts/3, -ts*4 ), imath.V2i( ts*5, -ts*4 ) ),
			( imath.V2i( -ts+1, -ts-1 ), imath.V2i( -ts, -ts*2 ) )
		]

		for input, expectedResult in testCases :
			self.assertEqual(
				GafferImage.ImagePlug.tileOrigin( input ),
				expectedResult
			)

	def testTileIndex( self ) :

		ts = GafferImage.ImagePlug.tileSize()

		for position, tileIndex in [
			( imath.V2i( -ts ), imath.V2i( -1 ) ),
			( imath.V2i( -ts -1 ), imath.V2i( -2 ) ),
			( imath.V2i( 0 ), imath.V2i( 0 ) ),
			( imath.V2i( ts ), imath.V2i( 1 ) ),
			( imath.V2i( ts - 1 ), imath.V2i( 0 ) ),
		] :
			self.assertEqual(
				GafferImage.ImagePlug.tileIndex( position ),
				tileIndex
			)

	def testDefaultChannelNamesMethod( self ) :

		channelNames = GafferImage.ImagePlug()['channelNames'].defaultValue()
		self.assertTrue( 'R' in channelNames )
		self.assertTrue( 'G' in channelNames )
		self.assertTrue( 'B' in channelNames )

	def testCreateCounterpart( self ) :

		p = GafferImage.ImagePlug()
		p2 = p.createCounterpart( "a", Gaffer.Plug.Direction.Out )

		self.assertEqual( p2.getName(), "a" )
		self.assertEqual( p2.direction(), Gaffer.Plug.Direction.Out )
		self.assertEqual( p2.getFlags(), p.getFlags() )

	def testDynamicSerialisation( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["p"] = GafferImage.ImagePlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		ss = s.serialise()

		s = Gaffer.ScriptNode()
		s.execute( ss )

		self.assertTrue( isinstance( s["n"]["p"], GafferImage.ImagePlug ) )
		self.assertEqual( s["n"]["p"].getFlags(), Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

	def testBoxPromotion( self ) :

		b = Gaffer.Box()
		b["n"] = GafferImage.Grade()

		self.assertTrue( Gaffer.PlugAlgo.canPromote( b["n"]["in"] ) )
		self.assertTrue( Gaffer.PlugAlgo.canPromote( b["n"]["out"] ) )

		i = Gaffer.PlugAlgo.promote( b["n"]["in"] )
		o = Gaffer.PlugAlgo.promote( b["n"]["out"] )

		self.assertEqual( b["n"]["in"].getInput(), i )
		self.assertEqual( o.getInput(), b["n"]["out"] )

		self.assertTrue( Gaffer.PlugAlgo.isPromoted( b["n"]["in"] ) )
		self.assertTrue( Gaffer.PlugAlgo.isPromoted( b["n"]["out"] ) )

	def testTypeNamePrefixes( self ) :

		self.assertTypeNamesArePrefixed(
			GafferImage,
			namesToIgnore = {
				"Gaffer::Switch", "Gaffer::ContextVariables",
				"Gaffer::DeleteContextVariables",
				"Gaffer::TimeWarp", "Gaffer::Loop",
			}
		)
		self.assertTypeNamesArePrefixed( GafferImageTest )

	def testDefaultNames( self ) :

		self.assertDefaultNamesAreCorrect(
			GafferImage,
			namesToIgnore = {
				"ImageSwitch", "ImageContextVariables", "DeleteImageContextVariables", "ImageTimeWarp",
				"ImageLoop",
			}
		)
		self.assertDefaultNamesAreCorrect( GafferImageTest )

	def testImageHash( self ) :

		r = GafferImage.ImageReader()
		r['fileName'].setValue( os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/checker.exr" ) )

		h = r['out'].imageHash()

		for i in range( 20 ) :
			self.assertEqual( h, r['out'].imageHash() )

		r['refreshCount'].setValue( 2 )

		self.assertNotEqual( h, r['out'].imageHash() )

	def testDefaultFormatForImage( self ) :

		constant = GafferImage.Constant()

		with Gaffer.Context() as c :

			GafferImage.FormatPlug.setDefaultFormat( c, GafferImage.Format( 100, 200 ) )
			self.assertEqual( constant["out"].image().displayWindow, imath.Box2i( imath.V2i( 0 ), imath.V2i( 99, 199 ) ) )

			GafferImage.FormatPlug.setDefaultFormat( c, GafferImage.Format( 200, 300 ) )
			self.assertEqual( constant["out"].image().displayWindow, imath.Box2i( imath.V2i( 0 ), imath.V2i( 199, 299 ) ) )

	def testGlobalConvenienceMethods( self ) :

		checker = GafferImage.Checkerboard()

		metadata = GafferImage.ImageMetadata()
		metadata["in"].setInput( checker["out"] )
		metadata["metadata"].addChild( Gaffer.NameValuePlug( "test", 10 ) )

		self.assertEqual( metadata["out"].format(), metadata["out"]["format"].getValue() )
		self.assertEqual( metadata["out"].formatHash(), metadata["out"]["format"].hash() )

		self.assertEqual( metadata["out"].dataWindow(), metadata["out"]["dataWindow"].getValue() )
		self.assertEqual( metadata["out"].dataWindowHash(), metadata["out"]["dataWindow"].hash() )

		self.assertEqual( metadata["out"].channelNames(), metadata["out"]["channelNames"].getValue() )
		self.assertFalse( metadata["out"].channelNames().isSame( metadata["out"]["channelNames"].getValue( _copy = False ) ) )
		self.assertTrue( metadata["out"].channelNames( _copy = False ).isSame( metadata["out"]["channelNames"].getValue( _copy = False ) ) )
		self.assertEqual( metadata["out"].channelNamesHash(), metadata["out"]["channelNames"].hash() )

		self.assertEqual( metadata["out"].metadata(), metadata["out"]["metadata"].getValue() )
		self.assertFalse( metadata["out"].metadata().isSame( metadata["out"]["metadata"].getValue( _copy = False ) ) )
		self.assertTrue( metadata["out"].metadata( _copy = False ).isSame( metadata["out"]["metadata"].getValue( _copy = False ) ) )
		self.assertEqual( metadata["out"].metadataHash(), metadata["out"]["metadata"].hash() )

if __name__ == "__main__":
	unittest.main()
