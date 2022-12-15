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

class MirrorTest( GafferImageTest.ImageTestCase ) :

	def testPassThrough( self ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.imagesPath() / "checker2x2.exr" )

		m = GafferImage.Mirror()
		m["in"].setInput( r["out"] )

		self.assertImageHashesEqual( r["out"], m["out"] )
		self.assertImagesEqual( r["out"], m["out"] )

	def testEmptyInputDataWindow( self ) :

		m = GafferImage.Mirror()
		self.assertTrue( GafferImage.BufferAlgo.empty( m["in"]["dataWindow"].getValue() ) )
		self.assertTrue( GafferImage.BufferAlgo.empty( m["out"]["dataWindow"].getValue() ) )

	def testFormatAndDataWindow( self ) :

		c = GafferImage.Constant()

		m = GafferImage.Mirror()
		m["in"].setInput( c["out"] )

		for width in range( 1, 100 ) :
			for height in range( 1, 100 ) :
				c["format"].setValue( GafferImage.Format( width, height ) )
				for horizontal, vertical in (
					( True, True ),
					( False, True ),
					( True, False ),
				) :
					m["horizontal"].setValue( horizontal )
					m["vertical"].setValue( vertical )

					self.assertEqual( m["out"]["dataWindow"].getValue(), c["out"]["dataWindow"].getValue() )
					self.assertEqual( m["out"]["format"].getValue(), c["out"]["format"].getValue() )

	def testHorizontal( self ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.imagesPath() / "checker2x2.exr" )

		m = GafferImage.Mirror()
		m["in"].setInput( r["out"] )
		m["horizontal"].setValue( True )

		self.assertEqual( m["out"]["dataWindow"].getValue(), r["out"]["dataWindow"].getValue() )
		self.assertEqual( m["out"]["format"].getValue(), r["out"]["format"].getValue() )

		t = GafferImage.ImageTransform()
		t["in"].setInput( r["out"] )
		t["transform"]["scale"]["x"].setValue( -1 )
		t["transform"]["pivot"]["x"].setValue( r["out"]["format"].getValue().getDisplayWindow().center().x )

		self.assertImagesEqual( m["out"], t["out"] )

	def testVertical( self ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.imagesPath() / "checker2x2.exr" )

		m = GafferImage.Mirror()
		m["in"].setInput( r["out"] )
		m["vertical"].setValue( True )

		self.assertEqual( m["out"]["dataWindow"].getValue(), r["out"]["dataWindow"].getValue() )
		self.assertEqual( m["out"]["format"].getValue(), r["out"]["format"].getValue() )

		t = GafferImage.ImageTransform()
		t["in"].setInput( r["out"] )
		t["transform"]["scale"]["y"].setValue( -1 )
		t["transform"]["pivot"]["y"].setValue( r["out"]["format"].getValue().getDisplayWindow().center().y )

		self.assertImagesEqual( m["out"], t["out"] )

	def testNonFlatThrows( self ) :

		mirror = GafferImage.Mirror()
		mirror["vertical"].setValue( True )

		self.assertRaisesDeepNotSupported( mirror )

if __name__ == "__main__":
	unittest.main()
