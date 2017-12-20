##########################################################################
#
#  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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
import imath

import IECore

import Gaffer
import GafferTest
import GafferImage
import GafferImageTest

class CopyChannelsTest( GafferImageTest.ImageTestCase ) :

	def __constantLayer( self, layer, color, size = imath.V2i( 512 ) ) :

		result = GafferImage.Constant()
		result["format"].setValue( GafferImage.Format( imath.Box2i( imath.V2i( 0 ), size ), 1 ) )
		result["color"].setValue( color )
		result["layer"].setValue( layer )

		return result

	def test( self ) :

		# Set up a copy where the main layer comes from the first
		# input and the diffuse layer is copied in from a second input.

		main = self.__constantLayer( "", imath.Color4f( 1, 0.5, 0.25, 1 ) )
		diffuse = self.__constantLayer( "diffuse", imath.Color4f( 0, 0.25, 0.5, 1 ) )

		copy = GafferImage.CopyChannels()
		copy["in"][0].setInput( main["out"] )
		copy["in"][1].setInput( diffuse["out"] )
		copy["channels"].setValue( "*" )

		# Check that our new image has all the expected channels.

		self.assertEqual(
			copy["out"]["channelNames"].getValue(),
			IECore.StringVectorData( [ "R", "G", "B", "A", "diffuse.R", "diffuse.G", "diffuse.B", "diffuse.A" ] ),
		)

		# Check that each channel is a perfect pass-through from the
		# relevant input, sharing the same entries in the cache.

		for constant in ( main, diffuse ) :
			for channel in ( "R", "G", "B", "A" ) :

				if constant["layer"].getValue() :
					channel = constant["layer"].getValue() + "." + channel

				self.assertEqual(
					copy["out"].channelDataHash( channel, imath.V2i( 0 ) ),
					constant["out"].channelDataHash( channel, imath.V2i( 0 ) ),
				)

				self.assertTrue(
					copy["out"].channelData( channel, imath.V2i( 0 ), _copy = False ).isSame(
						constant["out"].channelData( channel, imath.V2i( 0 ), _copy = False )
					)
				)

	def testMismatchedDataWindow( self ) :

		# Set up a situation where we're copying channels
		# from an image with a smaller data window than the
		# primary input.
		main = self.__constantLayer( "", imath.Color4f( 1 ), size = imath.V2i( 64 ) )
		diffuse = self.__constantLayer( "diffuse", imath.Color4f( 0.5 ), size = imath.V2i( 60 ) )

		copy = GafferImage.CopyChannels()
		copy["in"][0].setInput( main["out"] )
		copy["in"][1].setInput( diffuse["out"] )
		copy["channels"].setValue( "*" )

		# Format should be taken from the primary input, and data window should be the union
		# of both input data windows.

		self.assertEqual( copy["out"]["format"].getValue(), main["out"]["format"].getValue() )
		self.assertEqual( copy["out"]["dataWindow"].getValue(), main["out"]["dataWindow"].getValue() )

		# And CopyChannels must take care to properly fill in with
		# black any missing areas from the second input.

		for channel in ( "R", "G", "B", "A" ) :

			diffuseDW = diffuse["out"]["dataWindow"].getValue()
			copyDW = copy["out"]["dataWindow"].getValue()
			sampler = GafferImage.Sampler( copy["out"], "diffuse." + channel, copyDW )
			for x in range( copyDW.min().x, copyDW.max().x ) :
				for y in range( copyDW.min().y, copyDW.max().y ) :
					if GafferImage.BufferAlgo.contains( diffuseDW, imath.V2i( x, y ) ) :
						self.assertEqual( sampler.sample( x, y ), 0.5 )
					else :
						self.assertEqual( sampler.sample( x, y ), 0 )

	def testChannelsPlug( self ) :

		main = self.__constantLayer( "", imath.Color4f( 1, 0.5, 0.25, 1 ) )
		diffuse = self.__constantLayer( "diffuse", imath.Color4f( 0, 0.25, 0.5, 1 ) )

		copy = GafferImage.CopyChannels()
		copy["in"][0].setInput( main["out"] )
		copy["in"][1].setInput( diffuse["out"] )

		copy["channels"].setValue( "diffuse.R" )

		self.assertEqual(
			copy["out"]["channelNames"].getValue(),
			IECore.StringVectorData( [ "R", "G", "B", "A", "diffuse.R" ] ),
		)

		copy["channels"].setValue( "diffuse.R diffuse.B" )

		self.assertEqual(
			copy["out"]["channelNames"].getValue(),
			IECore.StringVectorData( [ "R", "G", "B", "A", "diffuse.R", "diffuse.B" ] ),
		)

		copy["channels"].setValue( "diffuse.*" )

		self.assertEqual(
			copy["out"]["channelNames"].getValue(),
			IECore.StringVectorData( [ "R", "G", "B", "A", "diffuse.R", "diffuse.G", "diffuse.B", "diffuse.A" ] ),
		)

	def testAffectsChannelNames( self ) :

		c1 = GafferImage.Constant()
		c2 = GafferImage.Constant()

		copy = GafferImage.CopyChannels()
		copy["in"][0].setInput( c1["out"] )
		copy["in"][1].setInput( c2["out"] )

		cs = GafferTest.CapturingSlot( copy.plugDirtiedSignal() )

		c2["layer"].setValue( "diffuse" )
		self.assertTrue( copy["out"]["channelNames"] in [ x[0] for x in cs ] )

		del cs[:]
		copy["channels"].setValue( "diffuse.R" )
		self.assertTrue( copy["out"]["channelNames"] in [ x[0] for x in cs ] )

if __name__ == "__main__":
	unittest.main()
