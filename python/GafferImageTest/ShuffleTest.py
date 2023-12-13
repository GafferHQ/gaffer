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

import unittest
import os
import imath

import IECore

import Gaffer
import GafferTest
import GafferImage
import GafferImageTest

class ShuffleTest( GafferImageTest.ImageTestCase ) :

	representativeDeepImagePath = GafferImageTest.ImageTestCase.imagesPath() / "representativeDeepImage.exr"

	def test( self ) :

		c = GafferImage.Constant()
		c["format"].setValue( GafferImage.Format( imath.Box2i( imath.V2i( 0 ), imath.V2i( 511 ) ), 1 ) )
		c["color"].setValue( imath.Color4f( 1, 0.75, 0.25, 1 ) )

		s = GafferImage.Shuffle()
		s["in"].setInput( c["out"] )

		self.assertImagesEqual( s["out"], c["out"] )

		for outName, inName in [ ( "R", "R" ), ( "G", "G" ), ( "B", "B" ), ( "A", "A" ) ] :
			self.assertEqual(
				s["out"].channelDataHash( outName, imath.V2i( 0 ) ),
				c["out"].channelDataHash( inName, imath.V2i( 0 ) ),
			)
			self.assertTrue(
				s["out"].channelData( outName, imath.V2i( 0 ), _copy = False ).isSame(
					c["out"].channelData( inName, imath.V2i( 0 ), _copy = False )
				)
			)

		s["channels"].addChild( s.ChannelPlug( "R", "G" ) )
		s["channels"].addChild( s.ChannelPlug( "G", "B" ) )
		s["channels"].addChild( s.ChannelPlug( "B", "A" ) )
		s["channels"].addChild( s.ChannelPlug( "A", "R" ) )

		for outName, inName in [ ( "R", "G" ), ( "G", "B" ), ( "B", "A" ), ( "A", "R" ) ] :
			self.assertEqual(
				s["out"].channelDataHash( outName, imath.V2i( 0 ) ),
				c["out"].channelDataHash( inName, imath.V2i( 0 ) ),
			)
			self.assertTrue(
				s["out"].channelData( outName, imath.V2i( 0 ), _copy = False ).isSame(
					c["out"].channelData( inName, imath.V2i( 0 ), _copy = False )
				)
			)

	def testAddConstantChannel( self ) :

		s = GafferImage.Shuffle()
		self.assertEqual( s["out"]["channelNames"].getValue(), IECore.StringVectorData() )

		s["channels"].addChild( s.ChannelPlug( "A", "__white" ) )
		self.assertEqual( s["out"]["channelNames"].getValue(), IECore.StringVectorData( [ "A" ] ) )

		self.assertEqual( s["out"].channelData( "A", imath.V2i( 0 ) )[0], 1 )
		self.assertTrue(
			s["out"].channelData( "A", imath.V2i( 0 ), _copy = False ).isSame(
				s["out"].channelData( "A", imath.V2i( s["out"].tileSize() ), _copy = False )
			)
		)

	def testSerialisation( self ) :

		s = Gaffer.ScriptNode()

		s["shuffle"] = GafferImage.Shuffle()
		s["shuffle"]["channels"].addChild( GafferImage.Shuffle.ChannelPlug( "R", "G" ) )
		s["shuffle"]["channels"].addChild( GafferImage.Shuffle.ChannelPlug( "G", "B" ) )
		s["shuffle"]["channels"].addChild( GafferImage.Shuffle.ChannelPlug( "B", "R" ) )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertTrue( len( s2["shuffle"]["channels"] ), 3 )
		self.assertEqual( s2["shuffle"]["channels"][0]["out"].getValue(), "R" )
		self.assertEqual( s2["shuffle"]["channels"][0]["in"].getValue(), "G" )
		self.assertEqual( s2["shuffle"]["channels"][1]["out"].getValue(), "G" )
		self.assertEqual( s2["shuffle"]["channels"][1]["in"].getValue(), "B" )
		self.assertEqual( s2["shuffle"]["channels"][2]["out"].getValue(), "B" )
		self.assertEqual( s2["shuffle"]["channels"][2]["in"].getValue(), "R" )

		s3 = Gaffer.ScriptNode()
		s3.execute( s2.serialise() )

		self.assertTrue( len( s3["shuffle"]["channels"] ), 3 )
		self.assertEqual( s3["shuffle"]["channels"][0]["out"].getValue(), "R" )
		self.assertEqual( s3["shuffle"]["channels"][0]["in"].getValue(), "G" )
		self.assertEqual( s3["shuffle"]["channels"][1]["out"].getValue(), "G" )
		self.assertEqual( s3["shuffle"]["channels"][1]["in"].getValue(), "B" )
		self.assertEqual( s3["shuffle"]["channels"][2]["out"].getValue(), "B" )
		self.assertEqual( s3["shuffle"]["channels"][2]["in"].getValue(), "R" )

	def testAffects( self ) :

		s = GafferImage.Shuffle()

		self.assertEqual( s.affects( s["in"]["channelData"] ), [ s["out"]["channelData" ] ] )
		self.assertEqual( s.affects( s["in"]["channelNames"] ), [ s["__mapping" ] ] )

		s["channels"].addChild( s.ChannelPlug( "R", "G" ) )
		self.assertEqual( s.affects( s["channels"][0]["out"] ), [ s["__mapping"] ] )

		self.assertEqual( s.affects( s["__mapping"] ), [ s["out"]["channelNames"], s["out"]["channelData" ] ] )

	def testMissingInputChannel( self ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.imagesPath() / "blurRange.exr" )
		self.assertEqual( r["out"]["channelNames"].getValue(), IECore.StringVectorData( [ "R" ] ) )

		s = GafferImage.Shuffle()
		s["in"].setInput( r["out"] )
		s["channels"].addChild( s.ChannelPlug( "R", "A" ) )
		s["channels"].addChild( s.ChannelPlug( "G", "B" ) )
		s["channels"].addChild( s.ChannelPlug( "B", "G" ) )
		s["channels"].addChild( s.ChannelPlug( "A", "R" ) )

		black = IECore.FloatVectorData( [ 0 ] * GafferImage.ImagePlug.tileSize() * GafferImage.ImagePlug.tileSize() )

		self.assertEqual( s["out"].channelData( "R", imath.V2i( 0 ) ), black )
		self.assertEqual( s["out"].channelData( "G", imath.V2i( 0 ) ), black )
		self.assertEqual( s["out"].channelData( "B", imath.V2i( 0 ) ), black )
		self.assertEqual( s["out"].channelData( "A", imath.V2i( 0 ) ), r["out"].channelData( "R", imath.V2i( 0 ) ) )

	def testDeep( self ) :
		representativeDeep = GafferImage.ImageReader()
		representativeDeep["fileName"].setValue( self.representativeDeepImagePath )

		deepShuffle = GafferImage.Shuffle()
		deepShuffle["in"].setInput( representativeDeep["out"] )

		postFlatten = GafferImage.DeepToFlat()
		postFlatten["in"].setInput( deepShuffle["out"] )

		preFlatten = GafferImage.DeepToFlat()
		preFlatten["in"].setInput( representativeDeep["out"] )

		flatShuffle = GafferImage.Shuffle()
		flatShuffle["in"].setInput( preFlatten["out"] )
		flatShuffle["channels"].setInput( deepShuffle["channels"] )

		deepShuffle["channels"].addChild( deepShuffle.ChannelPlug( "R", "B" ) )
		deepShuffle["channels"].addChild( deepShuffle.ChannelPlug( "G", "R" ) )
		deepShuffle["channels"].addChild( deepShuffle.ChannelPlug( "B", "G" ) )

		deepOrig = GafferImage.ImageAlgo.tiles( representativeDeep["out"] )
		flatOrig = GafferImage.ImageAlgo.tiles( preFlatten["out"] )


		flatShuffled = GafferImage.ImageAlgo.tiles( flatShuffle["out"] )
		deepShuffled = GafferImage.ImageAlgo.tiles( deepShuffle["out"] )

		self.assertEqual( flatShuffled["R"], flatOrig["B"] )
		self.assertEqual( flatShuffled["G"], flatOrig["R"] )
		self.assertEqual( flatShuffled["B"], flatOrig["G"] )
		self.assertEqual( flatShuffled["A"], flatOrig["A"] )

		self.assertEqual( deepShuffled["R"], deepOrig["B"] )
		self.assertEqual( deepShuffled["G"], deepOrig["R"] )
		self.assertEqual( deepShuffled["B"], deepOrig["G"] )
		self.assertEqual( deepShuffled["A"], deepOrig["A"] )

		self.assertImagesEqual( postFlatten["out"], flatShuffle["out"] )

		deepShuffle["channels"].clearChildren()
		deepShuffle["channels"].addChild( deepShuffle.ChannelPlug( "R", "__black" ) )
		deepShuffle["channels"].addChild( deepShuffle.ChannelPlug( "G", "__white" ) )
		deepShuffle["channels"].addChild( deepShuffle.ChannelPlug( "B", "__black" ) )

		flatGreen = GafferImage.ImageAlgo.tiles( flatShuffle["out"] )
		deepGreen = GafferImage.ImageAlgo.tiles( deepShuffle["out"] )

		for i in range( len( flatGreen["R"] ) ):
			self.assertEqual( flatGreen["R"][i], GafferImage.ImagePlug.blackTile() )
			self.assertEqual( flatGreen["G"][i], GafferImage.ImagePlug.whiteTile() )
			self.assertEqual( flatGreen["B"][i], GafferImage.ImagePlug.blackTile() )

			numSamples = deepGreen["sampleOffsets"][i][-1]

			self.assertEqual( deepGreen["R"][i], IECore.FloatVectorData( [ 0.0 ] * numSamples ) )
			self.assertEqual( deepGreen["G"][i], IECore.FloatVectorData( [ 1.0 ] * numSamples ) )
			self.assertEqual( deepGreen["B"][i], IECore.FloatVectorData( [ 0.0 ] * numSamples ) )

		deepPremult = GafferImage.Premultiply()
		deepPremult["in"].setInput( deepShuffle["out"] )
		postFlatten["in"].setInput( deepPremult["out"] )

		flatPremult = GafferImage.Premultiply()
		flatPremult["in"].setInput( flatShuffle["out"] )

		self.assertImagesEqual( postFlatten["out"], flatPremult["out"], maxDifference = 0.000001 )

	def testWildCards( self ) :

		constant = GafferImage.Constant()
		constant["color"].setValue( imath.Color4f( 0, 1, 2, 3 ) )

		shuffle = GafferImage.Shuffle()
		shuffle["in"].setInput( constant["out"] )

		self.assertImagesEqual( shuffle["out"], constant["out"] )

		shuffle["shuffles"].addChild(
			Gaffer.ShufflePlug( "[RGB]", "newLayer.${source}" )
		)

		self.assertEqual(
			shuffle["out"].channelNames(),
			IECore.StringVectorData( [ "R", "G", "B", "A", "newLayer.R", "newLayer.G", "newLayer.B" ] )
		)

		for channel in "RGB" :
			self.assertEqual(
				shuffle["out"].channelData( f"newLayer.{channel}", imath.V2i( 0 ) ),
				constant["out"].channelData( channel, imath.V2i( 0 ) ),
			)

	def testWildCardsDontMatchSpecialChannels( self ) :

		constant = GafferImage.Constant()
		constant["color"].setValue( imath.Color4f( 0, 1, 2, 3 ) )

		shuffle = GafferImage.Shuffle()
		shuffle["in"].setInput( constant["out"] )

		self.assertImagesEqual( shuffle["out"], constant["out"] )

		shuffle["shuffles"].addChild(
			Gaffer.ShufflePlug( "*", "newLayer.${source}" )
		)

		self.assertEqual(
			shuffle["out"].channelNames(),
			IECore.StringVectorData( [ "R", "G", "B", "A", "newLayer.R", "newLayer.G", "newLayer.B", "newLayer.A" ] )
		)

		for channel in "RGBA" :
			self.assertEqual(
				shuffle["out"].channelData( f"newLayer.{channel}", imath.V2i( 0 ) ),
				constant["out"].channelData( channel, imath.V2i( 0 ) ),
			)

	def testDeleteSource( self ) :

		constant = GafferImage.Constant()
		constant["color"].setValue( imath.Color4f( 0, 1, 2, 3 ) )

		shuffle = GafferImage.Shuffle()
		shuffle["in"].setInput( constant["out"] )

		self.assertImagesEqual( shuffle["out"], constant["out"] )

		shuffle["shuffles"].addChild(
			Gaffer.ShufflePlug( "R", "newLayer.R" )
		)

		# With `deleteSource` off.

		self.assertFalse( shuffle["shuffles"][0]["deleteSource"].getValue() )

		self.assertEqual(
			shuffle["out"].channelNames(),
			IECore.StringVectorData( [ "R", "G", "B", "A", "newLayer.R" ] )
		)

		self.assertEqual(
			shuffle["out"].channelData( "newLayer.R", imath.V2i( 0 ) ),
			constant["out"].channelData( "R", imath.V2i( 0 ) ),
		)

		# With `deleteSource` on.

		shuffle["shuffles"][0]["deleteSource"].setValue( True )

		self.assertEqual(
			shuffle["out"].channelNames(),
			IECore.StringVectorData( [ "G", "B", "A", "newLayer.R" ] )
		)

		self.assertEqual(
			shuffle["out"].channelData( "newLayer.R", imath.V2i( 0 ) ),
			constant["out"].channelData( "R", imath.V2i( 0 ) ),
		)

		with self.assertRaisesRegex( Gaffer.ProcessException, "Invalid output channel" ) :
			shuffle["out"].channelData( "R", imath.V2i( 0 ) )

	def testReplaceDestination( self ) :

		constant = GafferImage.Constant()
		constant["color"].setValue( imath.Color4f( 0, 1, 2, 3 ) )

		shuffle = GafferImage.Shuffle()
		shuffle["in"].setInput( constant["out"] )

		self.assertImagesEqual( shuffle["out"], constant["out"] )

		shuffle["shuffles"].addChild(
			Gaffer.ShufflePlug( "R", "G" )
		)

		# With `replaceDestination` on.

		self.assertTrue( shuffle["shuffles"][0]["replaceDestination"].getValue() )

		self.assertEqual(
			shuffle["out"].channelNames(),
			IECore.StringVectorData( [ "R", "G", "B", "A" ] )
		)

		self.assertEqual(
			shuffle["out"].channelData( "G", imath.V2i( 0 ) ),
			constant["out"].channelData( "R", imath.V2i( 0 ) ),
		)

		# With `replaceDestination` on.

		shuffle["shuffles"][0]["replaceDestination"].setValue( False )

		self.assertEqual(
			shuffle["out"].channelNames(),
			IECore.StringVectorData( [ "R", "G", "B", "A" ] )
		)

		self.assertEqual(
			shuffle["out"].channelData( "G", imath.V2i( 0 ) ),
			constant["out"].channelData( "G", imath.V2i( 0 ) ),
		)

if __name__ == "__main__":
	unittest.main()
