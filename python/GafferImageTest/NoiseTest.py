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

class NoiseTest( GafferImageTest.ImageTestCase ) :
	def testFormatHash( self ) :

		# Check that the data hash change when the format does.
		c = GafferImage.Noise()
		c["format"].setValue( GafferImage.Format( 2048, 1156, 1. ) )
		h1 = c["out"].channelData( "R", imath.V2i( 0 ) ).hash()
		c["format"].setValue( GafferImage.Format( 1920, 1080, 1. ) )
		h2 = c["out"].channelData( "R", imath.V2i( 0 ) ).hash()
		self.assertEqual( h1, h2 )

	def testEnableBehaviour( self ) :

		c = GafferImage.Noise()
		self.assertTrue( c.enabledPlug().isSame( c["enabled"] ) )
		self.assertEqual( c.correspondingInput( c["out"] ), None )
		self.assertEqual( c.correspondingInput( c["gain"] ), None )
		self.assertEqual( c.correspondingInput( c["lacunarity"] ), None )
		self.assertEqual( c.correspondingInput( c["size"] ), None )
		self.assertEqual( c.correspondingInput( c["format"] ), None )

	def testChannelNamesHash( self ) :

		c = GafferImage.Noise()
		h1 = c["out"]["channelNames"].hash()
		c["size"].setValue( imath.V2f( 120, 120 ) )
		h2 = c["out"]["channelNames"].hash()

		self.assertEqual( h1, h2 )

	def testSerialisationWithZeroAlpha( self ) :

		s = Gaffer.ScriptNode()
		s["c"] = GafferImage.Noise()
		s["c"]["lacunarity"].setValue( 1.0 )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( s2["c"]["lacunarity"].getValue(), 1.0 )

	def testFormatDependencies( self ) :

		c = GafferImage.Noise()

		self.assertEqual(
			c.affects( c["format"]["pixelAspect"] ),
			[ c["out"]["format"] ],
		)

		self.assertEqual(
			c.affects( c["format"]["displayWindow"]["min"]["x"] ),
			[ c["out"]["format"], c["out"]["dataWindow"] ]
		)

		self.assertEqual(
			c.affects( c["size"]["y"] ),
			[ c["out"]["channelData"] ],
		)

		self.assertEqual(
			c.affects( c["size"]["x"] ),
			[ c["out"]["channelData"] ],
		)

		self.assertEqual(
			c.affects( c["octaves"] ),
			[ c["out"]["channelData"] ],
		)

		self.assertEqual(
			c.affects( c["lacunarity"] ),
			[ c["out"]["channelData"] ],
		)

		self.assertEqual(
			c.affects( c["gain"] ),
			[ c["out"]["channelData"] ],
		)

		self.assertEqual(
			c.affects( c["minOutput"] ),
			[ c["out"]["channelData"] ],
		)

		self.assertEqual(
			c.affects( c["maxOutput"] ),
			[ c["out"]["channelData"] ],
		)

	def testLayerAffectsChannelNames( self ) :

		c = GafferImage.Noise()
		cs = GafferTest.CapturingSlot( c.plugDirtiedSignal() )
		c["layer"].setValue( "diffuse" )

		self.assertTrue( c["out"]["channelNames"] in set( [ x[0] for x in cs ] ) )

	def testExpectedResult( self ) :

		noise = GafferImage.Noise()
		noise["format"].setValue( GafferImage.Format( 128, 128 ) )
		noise["size"]["x"].setValue( 35 )
		noise["size"]["y"].setValue( 35 )
		noise["transform"]["rotate"].setValue( 45 )
		noise["transform"]["scale"]["x"].setValue( 10 )
		noise["transform"]["scale"]["y"].setValue( .5 )

		reader = GafferImage.ImageReader()
		reader["fileName"].setValue( os.path.dirname( __file__ ) + "/images/Noise.exr" )

		self.assertImagesEqual( noise["out"], reader["out"], ignoreMetadata = True, maxDifference = 0.001 )

if __name__ == "__main__":
	unittest.main()
