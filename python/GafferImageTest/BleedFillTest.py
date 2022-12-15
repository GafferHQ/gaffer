##########################################################################
#
#  Copyright (c) 2013-2015, Image Engine Design Inc. All rights reserved.
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
#  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES LOSS OF USE, DATA, OR
#  PROFITS OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
##########################################################################

import unittest
import random
import os
import imath
import pathlib

import IECore

import Gaffer
import GafferTest
import GafferImage
import GafferImageTest

class BleedFillTest( GafferImageTest.ImageTestCase ) :

	def testBasics( self ) :

		# Load a basic black/white checker, and resize it to 8x8 pixels
		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.imagesPath() / "checker2x2.exr" )

		resize = GafferImage.Resize()
		resize["in"].setInput( r["out"] )
		resize["format"]["displayWindow"]["min"].setValue( imath.V2i( 0, 0 ) )
		resize["format"]["displayWindow"]["max"].setValue( imath.V2i( 8 ) )
		resize["filter"].setValue( 'box' )

		# Create a large empty border around the checker
		c = GafferImage.Crop()
		c["area"].setValue( imath.Box2i( imath.V2i( -11 ), imath.V2i( 19 ) ) )
		c["in"].setInput( resize["out"] )


		bleedFill = GafferImage.BleedFill()
		bleedFill["expandDataWindow"].setValue( True )
		bleedFill["in"].setInput( c["out"] )

		# Test passthrough
		bleedFill["enabled"].setValue( False )

		self.assertEqual( GafferImage.ImageAlgo.imageHash( bleedFill["out"] ), GafferImage.ImageAlgo.imageHash( c["out"] ) )
		self.assertEqual( GafferImage.ImageAlgo.image( bleedFill["out"] ), GafferImage.ImageAlgo.image( c["out"] ) )

		bleedFill["enabled"].setValue( True )

		self.assertNotEqual( GafferImage.ImageAlgo.imageHash( bleedFill["out"] ), GafferImage.ImageAlgo.imageHash( c["out"] ) )
		self.assertNotEqual( GafferImage.ImageAlgo.image( bleedFill["out"] ), GafferImage.ImageAlgo.image( c["out"] ) )

		def sample( position ) :
			sampler = GafferImage.Sampler(
				bleedFill['out'],
				"R",
				imath.Box2i( position, position + imath.V2i( 1 ) )
			)
			return sampler.sample( position.x, position.y )

		# Check that the area covered by the original checkerboard image keeps its exact values
		self.assertEqual( sample( imath.V2i( 15, 15 ) ), 1.0 )
		self.assertEqual( sample( imath.V2i( 14, 14 ) ), 1.0 )
		self.assertEqual( sample( imath.V2i( 14, 15 ) ), 0.0 )
		self.assertEqual( sample( imath.V2i( 15, 14 ) ), 0.0 )
		self.assertEqual( sample( imath.V2i( 18, 18 ) ), 1.0 )
		self.assertEqual( sample( imath.V2i( 11, 11 ) ), 1.0 )
		self.assertEqual( sample( imath.V2i( 11, 18 ) ), 0.0 )
		self.assertEqual( sample( imath.V2i( 18, 11 ) ), 0.0 )

		# The area on the sides of the image at the color boundaries should have been smeared out to
		# grey
		self.assertAlmostEqual( sample( imath.V2i( 0, 15 ) ), 0.5, places = 2 )
		self.assertAlmostEqual( sample( imath.V2i( 29, 15 ) ), 0.5, places = 2 )
		self.assertAlmostEqual( sample( imath.V2i( 15, 0 ) ), 0.5, places = 2 )
		self.assertAlmostEqual( sample( imath.V2i( 15, 29 ) ), 0.5, places = 2 )

		# The corners should be a bit influenced by the sector they are in, but are far enough away to
		# still be averaged fairly close to grey
		self.assertAlmostEqual( sample( imath.V2i( 0, 0 ) ), 0.6, places = 1 )
		self.assertAlmostEqual( sample( imath.V2i( 29, 29 ) ), 0.6, places = 1 )
		self.assertAlmostEqual( sample( imath.V2i( 29, 0 ) ), 0.4, places = 1 )
		self.assertAlmostEqual( sample( imath.V2i( 0, 29 ) ), 0.4, places = 1 )

	def testSerialization( self ):
		s = Gaffer.ScriptNode()
		s["bleedFill"] = GafferImage.BleedFill()

		# By default, the only line serialized should be the constructor
		relevantSerialise = [ i for i in s.serialise().splitlines() if i.startswith( '__children["bleedFill"]' ) ]
		self.assertEqual( [ '__children["bleedFill"] = GafferImage.BleedFill( "bleedFill" )'], relevantSerialise )

		# If we set a plug, that gets serialised
		s["bleedFill"]["expandDataWindow"].setValue( True )
		relevantSerialise = [ i for i in s.serialise().splitlines() if i.startswith( '__children["bleedFill"]' ) ]
		self.assertEqual( [
				'__children["bleedFill"] = GafferImage.BleedFill( "bleedFill" )',
				'__children["bleedFill"]["expandDataWindow"].setValue( True )',
			], relevantSerialise )

if __name__ == "__main__":
	unittest.main()
