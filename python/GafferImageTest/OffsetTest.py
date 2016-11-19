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
import GafferTest
import GafferImage

class OffsetTest( GafferTest.TestCase ) :

	def testPassThrough( self ) :

		c = GafferImage.ImageReader()
		c["fileName"].setValue( os.path.dirname( __file__ ) + "/images/checker2x2.exr" )

		o = GafferImage.Offset()
		o["in"].setInput( c["out"] )

		self.assertEqual( o["offset"].getValue(), IECore.V2i( 0 ) )
		self.assertEqual( o["out"].imageHash(), c["out"].imageHash() )
		self.assertEqual( o["out"].image(), c["out"].image() )

	def testDataWindow( self ) :

		c = GafferImage.ImageReader()
		c["fileName"].setValue( os.path.dirname( __file__ ) + "/images/checker2x2.exr" )

		self.assertEqual(
			c["out"]["dataWindow"].getValue(),
			IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 2 ) )
		)

		o = GafferImage.Offset()
		o["in"].setInput( c["out"] )
		o["offset"].setValue( IECore.V2i( 1 ) )

		self.assertEqual(
			o["out"]["dataWindow"].getValue(),
			IECore.Box2i( IECore.V2i( 1 ), IECore.V2i( 3 ) )
		)

	def testChannelData( self ) :

		c = GafferImage.ImageReader()
		c["fileName"].setValue( os.path.dirname( __file__ ) + "/images/checker2x2.exr" )

		o = GafferImage.Offset()
		o["in"].setInput( c["out"] )
		o["offset"].setValue( IECore.V2i( 1 ) )

		def sample( image, channelName, pos ) :

			sampler = GafferImage.Sampler( image, channelName, image["dataWindow"].getValue() )
			return sampler.sample( pos.x, pos.y )

		for yOffset in range( -10, 10 ) :
			for xOffset in range( -10, 10 ) :

				o["offset"].setValue( IECore.V2i( xOffset, yOffset ) )

				for y in range( 0, 2 ) :
					for x in range( 0, 2 ) :
						for channelName in ( "R", "G", "B", "A" ) :
							self.assertEqual(
								sample( o["out"], channelName, IECore.V2i( x + xOffset, y + yOffset ) ),
								sample( c["out"], channelName, IECore.V2i( x, y ) ),
						)

	def testDeepOffset( self ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( os.path.dirname( __file__ ) + "/images/checker8x8.exr" )

		c = GafferImage.Constant()
		c["format"].setValue( GafferImage.Format( IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 8, 8 ) ), 1 ) )
		c["color"].setValue( IECore.Color4f( 0.0, 0.0, 0.0, 0.0 ) )
		c["z"].setValue( 1.0 )
		c["zBack"].setValue( 1.0 )

		m = GafferImage.DeepMerge()
		m["in"][0].setInput( r["out"] )
		m["in"][1].setInput( c["out"] )

		od = GafferImage.Offset()
		od["in"].setInput( m["out"] )
		od["offset"].setValue( IECore.V2i( 1 ) )

		od["out"].sampleOffsets( IECore.V2i( 0 ) )
		od["out"].channelData( "R", IECore.V2i( 0 ) )

		of = GafferImage.Offset()
		of["in"].setInput( r["out"] )
		of["offset"].setValue( IECore.V2i( 1 ) )

		of["out"].sampleOffsets( IECore.V2i( 0 ) )
		of["out"].channelData( "R", IECore.V2i( 0 ) )

		s = GafferImage.ImageState()
		s["in"].setInput( od["out"] )
		s["deepState"].setValue( GafferImage.ImagePlug.DeepState.Flat )

		def sample( image, channelName, pos ) :

			sampler = GafferImage.Sampler( image, channelName, image["dataWindow"].getValue() )
			return sampler.sample( pos.x, pos.y )

		for yOffset in range( -10, 10 ) :
			for xOffset in range( -10, 10 ) :

				od["offset"].setValue( IECore.V2i( xOffset, yOffset ) )
				of["offset"].setValue( IECore.V2i( xOffset, yOffset ) )

				self.assertEqual( of["out"]["dataWindow"].getValue(), s["out"]["dataWindow"].getValue() )

				for y in range( 0, 8 ) :
					for x in range( 0, 8 ) :
						for channelName in ( "R", "G", "B", "A" ) :
							self.assertEqual(
								sample( of["out"], channelName, IECore.V2i( x + xOffset, y + yOffset ) ),
								sample( s["out"], channelName, IECore.V2i( x + xOffset, y + yOffset ) ),
						)


	def testMultipleOfTileSize( self ) :

		c = GafferImage.ImageReader()
		c["fileName"].setValue( os.path.dirname( __file__ ) + "/images/checker.exr" )

		o = GafferImage.Offset()
		o["in"].setInput( c["out"] )

		for offset in [
			IECore.V2i( 0, 1 ),
			IECore.V2i( 1, 0 ),
			IECore.V2i( 2, 0 ),
			IECore.V2i( 2, 1 ),
			IECore.V2i( 2, -3 ),
			IECore.V2i( -2, 3 ),
			IECore.V2i( -1, -1 ),
		] :

			offset *= GafferImage.ImagePlug.tileSize()
			o["offset"].setValue( offset )

			self.assertEqual(
				o["out"].channelDataHash( "R", offset ),
				c["out"].channelDataHash( "R", IECore.V2i( 0 ) ),
			)
			self.assertEqual(
				o["out"].channelData( "R", offset ),
				c["out"].channelData( "R", IECore.V2i( 0 ) ),
			)

	def testOffsetBack( self ) :

		c = GafferImage.ImageReader()
		c["fileName"].setValue( os.path.dirname( __file__ ) + "/images/checker.exr" )

		o1 = GafferImage.Offset()
		o1["in"].setInput( c["out"] )
		o1["offset"].setValue( IECore.V2i( 101, -45 ) )

		o2 = GafferImage.Offset()
		o2["in"].setInput( o1["out"] )
		o2["offset"].setValue( IECore.V2i( -101, 45 ) )

		self.assertEqual( c["out"].image(), o2["out"].image() )

	def testChannelDataDirtyPropagation( self ) :

		c = GafferImage.Constant()

		o = GafferImage.Offset()
		o["in"].setInput( c["out"] )

		cs = GafferTest.CapturingSlot( o.plugDirtiedSignal() )
		c["color"]["r"].setValue( 0.5 )

		self.assertTrue( o["out"]["channelData"] in { x[0] for x in cs } )

	def testDataWindowDirtyPropagation( self ) :

		c = GafferImage.Constant()

		o = GafferImage.Offset()
		o["in"].setInput( c["out"] )

		cs = GafferTest.CapturingSlot( o.plugDirtiedSignal() )
		c["format"].setValue( GafferImage.Format( 100, 100 ) )

		self.assertTrue( o["out"]["dataWindow"] in { x[0] for x in cs } )

if __name__ == "__main__":
	unittest.main()
