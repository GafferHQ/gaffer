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

import IECore

import Gaffer
import GafferTest
import GafferImage
import GafferImageTest

class ShuffleTest( GafferImageTest.ImageTestCase ) :

	def test( self ) :

		c = GafferImage.Constant()
		c["format"].setValue( GafferImage.Format( IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 511 ) ), 1 ) )
		c["color"].setValue( IECore.Color4f( 1, 0.75, 0.25, 1 ) )

		s = GafferImage.Shuffle()
		s["in"].setInput( c["out"] )

		self.assertEqual( s["out"].image(), c["out"].image() )

		for outName, inName in [ ( "R", "R" ), ( "G", "G" ), ( "B", "B" ), ( "A", "A" ) ] :
			self.assertEqual(
				s["out"].channelDataHash( outName, IECore.V2i( 0 ) ),
				c["out"].channelDataHash( inName, IECore.V2i( 0 ) ),
			)
			self.assertTrue(
				s["out"].channelData( outName, IECore.V2i( 0 ), _copy = False ).isSame(
					c["out"].channelData( inName, IECore.V2i( 0 ), _copy = False )
				)
			)

		s["channels"].addChild( s.ChannelPlug( "R", "G" ) )
		s["channels"].addChild( s.ChannelPlug( "G", "B" ) )
		s["channels"].addChild( s.ChannelPlug( "B", "A" ) )
		s["channels"].addChild( s.ChannelPlug( "A", "R" ) )

		for outName, inName in [ ( "R", "G" ), ( "G", "B" ), ( "B", "A" ), ( "A", "R" ) ] :
			self.assertEqual(
				s["out"].channelDataHash( outName, IECore.V2i( 0 ) ),
				c["out"].channelDataHash( inName, IECore.V2i( 0 ) ),
			)
			self.assertTrue(
				s["out"].channelData( outName, IECore.V2i( 0 ), _copy = False ).isSame(
					c["out"].channelData( inName, IECore.V2i( 0 ), _copy = False )
				)
			)

	def testAddConstantChannel( self ) :

		s = GafferImage.Shuffle()
		self.assertEqual( s["out"]["channelNames"].getValue(), IECore.StringVectorData( [ "R", "G", "B" ] ) )

		s["channels"].addChild( s.ChannelPlug( "A", "__white" ) )
		self.assertEqual( s["out"]["channelNames"].getValue(), IECore.StringVectorData( [ "R", "G", "B", "A" ] ) )

		self.assertEqual( s["out"].channelData( "A", IECore.V2i( 0 ) )[0], 1 )
		self.assertTrue(
			s["out"].channelData( "A", IECore.V2i( 0 ), _copy = False ).isSame(
				s["out"].channelData( "A", IECore.V2i( s["out"].tileSize() ), _copy = False )
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

	def testCreateCounterpart( self ) :

		p = GafferImage.Shuffle.ChannelPlug()
		p2 = p.createCounterpart( "p2", p.Direction.Out )
		self.assertTrue( isinstance( p2, GafferImage.Shuffle.ChannelPlug ) )
		self.assertTrue( p2.direction(), p.Direction.Out )

	def testAffects( self ) :

		s = GafferImage.Shuffle()

		self.assertEqual( s.affects( s["in"]["channelData"] ), [ s["out"]["channelData" ] ] )
		self.assertEqual( s.affects( s["in"]["channelNames"] ), [ s["out"]["channelNames" ] ] )

		s["channels"].addChild( s.ChannelPlug( "R", "G" ) )
		self.assertEqual( s.affects( s["channels"][0]["out"] ), [ s["out"]["channelNames"], s["out"]["channelData"] ] )

if __name__ == "__main__":
	unittest.main()
