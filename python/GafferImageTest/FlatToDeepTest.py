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

import random
import unittest
import six
import imath

import IECore

import GafferTest
import GafferImage
import GafferImageTest
import Gaffer

class FlatToDeepTest( GafferImageTest.ImageTestCase ) :

	def testOverall( self ) :

		constant = GafferImage.Constant()
		constant["color"].setValue( imath.Color4f( 0.1, 0.2, 0.3, 0.5 ) )

		shuffle = GafferImage.Shuffle()
		shuffle["in"].setInput( constant["out"] )
		shuffle["channels"].addChild( shuffle.ChannelPlug( "Z", "R" ) )
		shuffle["channels"].addChild( shuffle.ChannelPlug( "ZBack", "G" ) )
		shuffle["enabled"].setValue( False )

		addDepth = GafferImage.FlatToDeep()
		addDepth["in"].setInput( shuffle["out"] )
		addDepth["enabled"].setValue( False )

		self.assertEqual( addDepth["out"]["channelNames"].getValue(), IECore.StringVectorData( [ "R", "G", "B", "A" ] ) )

		addDepth["enabled"].setValue( True )
		self.assertEqual( addDepth["out"]["channelNames"].getValue(), IECore.StringVectorData( [ "R", "G", "B", "A", "Z" ] ) )
		addDepth["zBackMode"].setValue( GafferImage.FlatToDeep.ZBackMode.Thickness )
		self.assertEqual( addDepth["out"]["channelNames"].getValue(), IECore.StringVectorData( [ "R", "G", "B", "A", "Z", "ZBack" ] ) )

		with Gaffer.Context() as c:
			c["image:tileOrigin"] = imath.V2i( 0 )

			c["image:channelName"] = "R"
			rHash = constant["out"]["channelData"].hash()

			c["image:channelName"] = "G"
			gHash = constant["out"]["channelData"].hash()

			# TEST Z CHANNEL
			c["image:channelName"] = "Z"

			tilePixels = GafferImage.ImagePlug.tileSize() ** 2

			initialZHash = addDepth["out"]["channelData"].hash()
			self.assertEqual( addDepth["out"]["channelData"].getValue(), IECore.FloatVectorData( [0] * tilePixels ) )

			addDepth["depth"].setValue( 42.0 )

			newZHash = addDepth["out"]["channelData"].hash()
			self.assertEqual( addDepth["out"]["channelData"].getValue(), IECore.FloatVectorData( [42.0] * tilePixels ) )
			self.assertNotEqual( initialZHash, newZHash )

			addDepth["zMode"].setValue( GafferImage.FlatToDeep.ZMode.Channel )
			addDepth["zChannel"].setValue( "R" )
			self.assertEqual( addDepth["out"]["channelData"].hash(), rHash )
			self.assertEqual( addDepth["out"]["channelData"].getValue(), IECore.FloatVectorData( [0.1] * tilePixels ) )

			addDepth["zChannel"].setValue( "G" )
			self.assertEqual( addDepth["out"]["channelData"].hash(), gHash )
			self.assertEqual( addDepth["out"]["channelData"].getValue(), IECore.FloatVectorData( [0.2] * tilePixels ) )

			addDepth["zChannel"].setValue( "Q" )
			six.assertRaisesRegex( self, RuntimeError, 'FlatToDeep : Cannot find requested Z channel - no channel "Q" found.', addDepth["out"]["channelData"].hash )
			six.assertRaisesRegex( self, RuntimeError, 'FlatToDeep : Cannot find requested Z channel - no channel "Q" found.', addDepth["out"]["channelData"].getValue )

			addDepth["zChannel"].setValue( "Z" )
			shuffle["enabled"].setValue( True )
			self.assertEqual( shuffle["out"]["channelData"].hash(), addDepth["out"]["channelData"].hash() )
			self.assertEqual( addDepth["out"]["channelData"].getValue(), IECore.FloatVectorData( [0.1] * tilePixels ) )

			addDepth["zMode"].setValue( GafferImage.FlatToDeep.ZMode.Constant )
			addDepth["depth"].setValue( 0.0 )
			shuffle["enabled"].setValue( False )

			# TEST ZBack CHANNEL
			c["image:channelName"] = "ZBack"

			initialZBackHash = addDepth["out"]["channelData"].hash()
			self.assertEqual( addDepth["out"]["channelData"].getValue(), IECore.FloatVectorData( [0] * tilePixels ) )

			addDepth["depth"].setValue( 42.0 )

			newZBackHash = addDepth["out"]["channelData"].hash()
			self.assertEqual( addDepth["out"]["channelData"].getValue(), IECore.FloatVectorData( [42.0] * tilePixels ) )
			self.assertNotEqual( initialZBackHash, newZBackHash )

			addDepth["thickness"].setValue( 0.09 )

			newerZBackHash = addDepth["out"]["channelData"].hash()
			self.assertEqual( addDepth["out"]["channelData"].getValue(), IECore.FloatVectorData( [42.09] * tilePixels ) )
			self.assertNotEqual( newZBackHash, newerZBackHash )

			addDepth["zBackMode"].setValue( GafferImage.FlatToDeep.ZBackMode.Channel )
			addDepth["zBackChannel"].setValue( "R" )
			self.assertEqual( addDepth["out"]["channelData"].hash(), rHash )
			self.assertEqual( addDepth["out"]["channelData"].getValue(), IECore.FloatVectorData( [0.1] * tilePixels ) )

			addDepth["zBackChannel"].setValue( "G" )
			self.assertEqual( addDepth["out"]["channelData"].hash(), gHash )
			self.assertEqual( addDepth["out"]["channelData"].getValue(), IECore.FloatVectorData( [0.2] * tilePixels ) )

			addDepth["zBackChannel"].setValue( "Q" )
			six.assertRaisesRegex( self, RuntimeError, 'FlatToDeep : Cannot find requested ZBack channel - no channel "Q" found.', addDepth["out"]["channelData"].hash )
			six.assertRaisesRegex( self, RuntimeError, 'FlatToDeep : Cannot find requested ZBack channel - no channel "Q" found.', addDepth["out"]["channelData"].getValue )

			addDepth["zBackChannel"].setValue( "ZBack" )
			shuffle["enabled"].setValue( True )
			self.assertEqual( shuffle["out"]["channelData"].hash(), addDepth["out"]["channelData"].hash() )
			self.assertEqual( addDepth["out"]["channelData"].getValue(), IECore.FloatVectorData( [0.2] * tilePixels ) )

			addDepth["zBackMode"].setValue( GafferImage.FlatToDeep.ZBackMode.Thickness )

			self.assertEqual( newerZBackHash, addDepth["out"]["channelData"].hash() )
			self.assertEqual( addDepth["out"]["channelData"].getValue(), IECore.FloatVectorData( [42.09] * tilePixels ) )

			addDepth["zMode"].setValue( GafferImage.FlatToDeep.ZMode.Channel )
			addDepth["zChannel"].setValue( "Z" )
			self.assertNotEqual( newerZBackHash, addDepth["out"]["channelData"].hash() )
			self.assertEqual( addDepth["out"]["channelData"].getValue(), IECore.FloatVectorData( [0.19] * tilePixels ) )

if __name__ == "__main__":
	unittest.main()
