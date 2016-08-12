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

import os
import unittest

import IECore

import Gaffer
import GafferTest
import GafferImage
import GafferImageTest

class UVWarpTest( GafferImageTest.ImageTestCase ) :

	def testConstructor( self ) :

		w = GafferImage.UVWarp()
		self.assertTrue( isinstance( w, GafferImage.UVWarp ) )

	def testFormatAndDataWindow( self ) :

		texture = GafferImage.Constant()
		texture["format"].setValue( GafferImage.Format( 100, 100 ) )

		uv = GafferImage.Constant()
		uv["format"].setValue( GafferImage.Format( 200, 200 ) )

		warp = GafferImage.UVWarp()
		warp["in"].setInput( texture["out"] )
		warp["uv"].setInput( uv["out"] )

		self.assertEqual( warp["out"]["format"].getValue(), uv["out"]["format"].getValue() )
		self.assertEqual( warp["out"]["dataWindow"].getValue(), uv["out"]["dataWindow"].getValue() )

	def testUVWarp( self ) :

		reader = GafferImage.ImageReader()
		reader["fileName"].setValue( os.path.dirname( __file__ ) + "/images/checker2x2.exr" )

		# Constant provides the same UV across the board
		# for the UVWarp uv input.
		constant = GafferImage.Constant()

		uvWarp = GafferImage.UVWarp()
		uvWarp["in"].setInput( reader["out"] )
		uvWarp["uv"].setInput( constant["out"] )

		# We can then sample the input image at the
		# same UV position.
		sampler1 = GafferImage.ImageSampler()
		sampler1["image"].setInput( reader["out"] )

		# And compare it to an arbitrary pixel in the
		# (constant) warped output.
		sampler2 = GafferImage.ImageSampler()
		sampler2["image"].setInput( uvWarp["out"] )
		sampler2["pixel"].setValue( IECore.V2f( 5.5 ) )

		for u in ( 0.0, 0.25, 0.5, 0.75, 1.0 ) :
			for v in ( 0.0, 0.25, 0.5, 0.75, 1.0 ) :
				constant["color"].setValue( IECore.Color4f( u, v, 0, 1 ) )
				sampler1["pixel"].setValue( IECore.V2f( u * 2, v * 2 ) )
				self.assertEqual( sampler1["color"].getValue(), sampler2["color"].getValue() )

	def testNonFlatHashPassThrough( self ) :

		deepIn = self.deepImage( GafferImage.Format( 8, 8 ) )
		deepUv = self.deepImage( GafferImage.Format( 16, 16 ) )

		warp = GafferImage.UVWarp()
		warp["in"].setInput( deepIn['out'] )
		warp["uv"].setInput( deepUv['out'] )

		self.assertEqual( deepIn["out"]["deepState"].getValue(), GafferImage.ImagePlug.DeepState.Tidy )
		self.assertEqual( deepUv["out"]["deepState"].getValue(), GafferImage.ImagePlug.DeepState.Tidy )
		self.assertEqual( deepIn["out"].imageHash(), warp["out"].imageHash(), "Hashes should be equal when both inputs are Deep" )

		deepUv["deepState"].setValue( GafferImage.ImagePlug.DeepState.Flat )
		self.assertEqual( deepIn["out"]["deepState"].getValue(), GafferImage.ImagePlug.DeepState.Tidy )
		self.assertEqual( deepUv["out"]["deepState"].getValue(), GafferImage.ImagePlug.DeepState.Flat )
		self.assertEqual( deepIn["out"].imageHash(), warp["out"].imageHash(), "Hashes should be equal when 'in' is Deep, 'uv' is Flat" )

		deepIn["deepState"].setValue( GafferImage.ImagePlug.DeepState.Flat )
		self.assertEqual( deepIn["out"]["deepState"].getValue(), GafferImage.ImagePlug.DeepState.Flat )
		self.assertEqual( deepUv["out"]["deepState"].getValue(), GafferImage.ImagePlug.DeepState.Flat )
		self.assertNotEqual( deepIn["out"].imageHash(), warp["out"].imageHash(), "Hashes should not be equal when both inputs are Flat" )

		deepUv["deepState"].setValue( GafferImage.ImagePlug.DeepState.Tidy )
		self.assertEqual( deepIn["out"]["deepState"].getValue(), GafferImage.ImagePlug.DeepState.Flat )
		self.assertEqual( deepUv["out"]["deepState"].getValue(), GafferImage.ImagePlug.DeepState.Tidy )
		self.assertEqual( deepIn["out"].imageHash(), warp["out"].imageHash(), "Hashes should be equal when 'in' is Flat, 'uv' is Deep" )

	def testNegativeDataWindowOrigin( self ) :

		reader = GafferImage.ImageReader()
		reader["fileName"].setValue( os.path.dirname( __file__ ) + "/images/checker.exr" )

		constant = GafferImage.Constant()
		constant["color"].setValue( IECore.Color4f( 0.5, 0, 0, 1 ) )

		offset = GafferImage.Offset()
		offset["in"].setInput( constant["out"] )
		offset["offset"].setValue( IECore.V2i( -200, -250 ) )

		uvWarp = GafferImage.UVWarp()
		uvWarp["in"].setInput( reader["out"] )
		uvWarp["uv"].setInput( offset["out"] )

		GafferImageTest.processTiles( uvWarp["out"] )

if __name__ == "__main__":
	unittest.main()
