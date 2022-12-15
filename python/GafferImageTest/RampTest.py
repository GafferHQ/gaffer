##########################################################################
#
#  Copyright (c) 2018, John Haddon. All rights reserved.
#  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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

class RampTest( GafferImageTest.ImageTestCase ) :

	def testFormatHash( self ) :

		# Check that the data hash change when the format does.
		c = GafferImage.Ramp()
		c["format"].setValue( GafferImage.Format( 2048, 1156, 1. ) )
		h1 = c["out"].channelDataHash( "R", imath.V2i( 0 ) )
		c["format"].setValue( GafferImage.Format( 1920, 1080, 1. ) )
		h2 = c["out"].channelDataHash( "R", imath.V2i( 0 ) )
		self.assertEqual( h1, h2 )

	def testEnableBehaviour( self ) :

		c = GafferImage.Ramp()
		self.assertTrue( c.enabledPlug().isSame( c["enabled"] ) )
		self.assertEqual( c.correspondingInput( c["out"] ), None )
		self.assertEqual( c.correspondingInput( c["startPosition"] ), None )
		self.assertEqual( c.correspondingInput( c["endPosition"] ), None )
		self.assertEqual( c.correspondingInput( c["ramp"] ), None )
		self.assertEqual( c.correspondingInput( c["format"] ), None )

	def testChannelNamesHash( self ) :

		c = GafferImage.Ramp()
		h1 = c["out"]["channelNames"].hash()
		c["startPosition"].setValue( imath.V2f( 0, 540 ) )
		h2 = c["out"]["channelNames"].hash()

		self.assertEqual( h1, h2 )

	def testSerialisation( self ) :

		s = Gaffer.ScriptNode()
		s["r"] = GafferImage.Ramp()
		s["r"]["endPosition"].setValue( imath.V2f( 512, 512 ) )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( s2["r"]["endPosition"].getValue(), imath.V2f( 512, 512 ) )

	def testFormatDependencies( self ) :

		c = GafferImage.Ramp()

		self.assertEqual(
			c.affects( c["format"]["pixelAspect"] ),
			[ c["out"]["format"] ],
		)

		self.assertEqual(
			c.affects( c["format"]["displayWindow"]["min"]["x"] ),
			[ c["out"]["format"], c["out"]["dataWindow"]]
		)

		self.assertEqual(
			c.affects( c["startPosition"]["x"] ),
			[ c["out"]["channelData"] ],
		)

		self.assertEqual(
			c.affects( c["endPosition"]["x"] ),
			[ c["out"]["channelData"] ],
		)

		self.assertEqual(
			c.affects( c["ramp"]["p1"]["x"] ),
			[ c["out"]["channelData"] ],
		)

		self.assertEqual(
			c.affects( c["transform"]["rotate"] ),
			[ c["out"]["channelData"] ],
		)

	def testLayerAffectsChannelNames( self ) :

		c = GafferImage.Ramp()
		cs = GafferTest.CapturingSlot( c.plugDirtiedSignal() )
		c["layer"].setValue( "diffuse" )

		self.assertTrue( c["out"]["channelNames"] in set( [ x[0] for x in cs ] ) )

	def testExpectedResult( self ) :

		ramp = GafferImage.Ramp()
		ramp["format"].setValue( GafferImage.Format( 128, 128 ) )
		ramp["transform"]["rotate"].setValue( 45 )
		ramp["transform"]["scale"]["x"].setValue( .5 )

		ramp["startPosition"].setValue( imath.V2f( 0, 64 ) )
		ramp["endPosition"].setValue( imath.V2f( 128, 64 ) )
		ramp["ramp"].addChild( Gaffer.ValuePlug( "p2" ) )
		ramp["ramp"]["p2"].addChild( Gaffer.FloatPlug( "x", defaultValue = 0.5308765172958374 ) )
		ramp["ramp"]["p2"].addChild( Gaffer.Color4fPlug( "y", defaultValue = imath.Color4f( 0.530900002, 0, 0, 0.50999999 ) ) )

		reader = GafferImage.ImageReader()
		reader["fileName"].setValue( self.imagesPath() / "GafferRamp.exr" )

		self.assertImagesEqual( ramp["out"], reader["out"], ignoreMetadata = True, maxDifference = 0.001 )

if __name__ == "__main__":
	unittest.main()
