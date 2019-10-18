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

import os
import unittest
import imath

import IECore

import Gaffer
import GafferTest
import GafferImage
import GafferImageTest

class ErodeTest( GafferImageTest.ImageTestCase ) :

	def testPassThrough( self ) :

		c = GafferImage.Constant()

		m = GafferImage.Erode()
		m["in"].setInput( c["out"] )
		m["radius"].setValue( imath.V2i( 0 ) )

		self.assertEqual( GafferImage.ImageAlgo.imageHash( c["out"] ), GafferImage.ImageAlgo.imageHash( m["out"] ) )
		self.assertImagesEqual( c["out"], m["out"] )

	def testExpandDataWindow( self ) :

		c = GafferImage.Constant()

		m = GafferImage.Erode()
		m["in"].setInput( c["out"] )
		m["radius"].setValue( imath.V2i( 1 ) )

		self.assertEqual( m["out"]["dataWindow"].getValue(), c["out"]["dataWindow"].getValue() )

		m["expandDataWindow"].setValue( True )

		self.assertEqual( m["out"]["dataWindow"].getValue().min(), c["out"]["dataWindow"].getValue().min() - imath.V2i( 1 ) )
		self.assertEqual( m["out"]["dataWindow"].getValue().max(), c["out"]["dataWindow"].getValue().max() + imath.V2i( 1 ) )

	def testFilter( self ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( os.path.dirname( __file__ ) + "/images/radial.exr" )

		m = GafferImage.Erode()
		m["in"].setInput( r["out"] )
		self.assertImagesEqual( m["out"], r["out"] )

		m["radius"].setValue( imath.V2i( 8 ) )
		m["boundingMode"].setValue( GafferImage.Sampler.BoundingMode.Clamp )

		dataWindow = m["out"]["dataWindow"].getValue()
		s = GafferImage.ImageStats()
		s["in"].setInput( m["out"] )
		s["area"].setValue( dataWindow )

		self.assertEqual( s["max"].getValue(), imath.Color4f( 0, 0, 0, 1 ) )

	def testDriverChannel( self ) :

		rRaw = GafferImage.ImageReader()
		rRaw["fileName"].setValue( os.path.dirname( __file__ ) + "/images/circles.exr" )

		r = GafferImage.Grade()
		r["in"].setInput( rRaw["out"] )
		# Trim off the noise in the blacks so that areas with no visible color are actually flat
		r["blackPoint"].setValue( imath.Color4f( 0.03 ) )


		masterErode = GafferImage.Erode()
		masterErode["in"].setInput( r["out"] )
		masterErode["radius"].setValue( imath.V2i( 2 ) )

		masterErode["masterChannel"].setValue( "G" )

		expected = GafferImage.ImageReader()
		expected["fileName"].setValue( os.path.dirname( __file__ ) + "/images/circlesGreenErode.exr" )

		# Note that in this expected image, the green channel is nicely medianed, and red and blue are completely
		# unchanged in areas where there is no green.  In areas where red and blue overlap with a noisy green,
		# they get a bit scrambled.  This is why in practice, you would use something like luminance, rather
		# than just the green channel
		self.assertImagesEqual( masterErode["out"], expected["out"], ignoreMetadata = True, maxDifference=0.0005 )


		defaultErode = GafferImage.Erode()
		defaultErode["in"].setInput( r["out"] )
		defaultErode["radius"].setValue( imath.V2i( 2 ) )

		masterErodeSingleChannel = GafferImage.DeleteChannels()
		masterErodeSingleChannel["in"].setInput( masterErode["out"] )
		masterErodeSingleChannel["mode"].setValue( GafferImage.DeleteChannels.Mode.Keep )

		defaultErodeSingleChannel = GafferImage.DeleteChannels()
		defaultErodeSingleChannel["in"].setInput( defaultErode["out"] )
		defaultErodeSingleChannel["mode"].setValue( GafferImage.DeleteChannels.Mode.Keep )

		for c in [ "R", "G", "B" ]:
			masterErode["masterChannel"].setValue( c )
			masterErodeSingleChannel["channels"].setValue( c )
			defaultErodeSingleChannel["channels"].setValue( c )

			# When we look at just the channel being used as the master, it matches a default median not using
			# a master
			self.assertImagesEqual( masterErodeSingleChannel["out"], defaultErodeSingleChannel["out"] )

if __name__ == "__main__":
	unittest.main()
