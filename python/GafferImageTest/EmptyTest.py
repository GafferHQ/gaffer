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

import unittest
import imath

import IECore

import GafferImage
import GafferImageTest

class EmptyTest( GafferImageTest.ImageTestCase ) :

	def testDeep( self ) :

		empty = GafferImage.Empty()
		empty["format"].setValue( GafferImage.Format( imath.Box2i( imath.V2i( 0 ), imath.V2i( 511 ) ), 1 ) )

		self.assertEqual( empty["out"]["deep"].getValue(), True )

	def testFormatHash( self ) :

		# Check that the data and sampleOffsets hashes don't change when the format does.
		e = GafferImage.Empty()
		e["format"].setValue( GafferImage.Format( 2048, 1156, 1. ) )
		channelDataHash1 = e["out"].channelDataHash( "R", imath.V2i( 0 ) )
		sampleOffsetsHash1 = e["out"].sampleOffsetsHash( imath.V2i( 0 ) )
		e["format"].setValue( GafferImage.Format( 1920, 1080, 1. ) )
		channelDataHash2 = e["out"].channelDataHash( "R", imath.V2i( 0 ) )
		sampleOffsetsHash2 = e["out"].sampleOffsetsHash( imath.V2i( 0 ) )
		self.assertEqual( channelDataHash1, channelDataHash2 )
		self.assertEqual( sampleOffsetsHash1, sampleOffsetsHash2 )

	def testTileHashes( self ) :

		# Test that two tiles within the image have the same hash.
		e = GafferImage.Empty()
		e["format"].setValue( GafferImage.Format( 2048, 1156, 1. ) )

		self.assertEqual(
			e["out"].channelDataHash( "R", imath.V2i( 0 ) ),
			e["out"].channelDataHash( "R", imath.V2i( GafferImage.ImagePlug().tileSize() ) ),
		)

		self.assertEqual(
			e["out"].sampleOffsetsHash( imath.V2i( 0 ) ),
			e["out"].sampleOffsetsHash( imath.V2i( GafferImage.ImagePlug().tileSize() ) ),
		)

	def testTileIdentity( self ) :

		e = GafferImage.Empty()
		e["format"].setValue( GafferImage.Format( 2048, 1156, 1. ) )

		# The channelData() binding returns a copy by default, so we wouldn't
		# expect two tiles to be referencing the same object.
		self.assertFalse(
			e["out"].channelData( "R", imath.V2i( 0 ) ).isSame(
				e["out"].channelData( "R", imath.V2i( GafferImage.ImagePlug.tileSize() ) )
			)
		)

		# But behind the scenes we do want them to be the same, so
		# check that that is the case.
		self.assertTrue(
			e["out"].channelData( "R", imath.V2i( 0 ), _copy = False ).isSame(
				e["out"].channelData( "R", imath.V2i( GafferImage.ImagePlug.tileSize() ), _copy = False )
			)
		)

	def testEnableBehaviour( self ) :

		e = GafferImage.Empty()
		self.assertTrue( e.enabledPlug().isSame( e["enabled"] ) )
		self.assertEqual( e.correspondingInput( e["out"] ), None )
		self.assertEqual( e.correspondingInput( e["format"] ), None )

	def testChannelNames( self ) :

		e = GafferImage.Empty()
		self.assertEqual( e["out"]["channelNames"].getValue(), IECore.StringVectorData( [] ) )

	def testSampleOffsets( self ) :

		ts = GafferImage.ImagePlug.tileSize()

		e = GafferImage.Empty()
		e["format"].setValue( GafferImage.Format( 2048, 1156, 1. ) )

		self.assertEqual( e["out"].sampleOffsets( imath.V2i( 0 ) ), IECore.IntVectorData( [ 0 ] * ts * ts ) )

	def testChannelData( self ) :

		e = GafferImage.Empty()
		e["format"].setValue( GafferImage.Format( 2048, 1156, 1. ) )

		for chan in [ "R", "G", "B", "A", "Z", "ZBack" ] :
			self.assertEqual( e["out"].channelData( chan, imath.V2i( 0 ) ), IECore.FloatVectorData( [] ) )

	def testFormatDependencies( self ) :

		e = GafferImage.Empty()

		self.assertEqual(
			e.affects( e["format"]["displayWindow"]["min"]["x"] ),
			[ e["out"]["format"], e["out"]["dataWindow"] ],
		)
		self.assertEqual(
			e.affects( e["format"]["pixelAspect"] ),
			[ e["out"]["format"] ],
		)

if __name__ == "__main__":
	unittest.main()
