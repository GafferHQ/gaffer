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
import GafferImage
import GafferImageTest

class TextTest( GafferImageTest.ImageTestCase ) :

	def testDirtyPropagation( self ) :

		# This exposed a crash bug in the Shape
		# base class.

		t = GafferImage.Text()
		t["text"].setValue( "hi" )

	def testPremultiplication( self ) :

		constant = GafferImage.Constant()
		constant["color"].setValue( IECore.Color4f( 0 ) )

		text = GafferImage.Text()
		text["in"].setInput( constant["out"] )

		stats = GafferImage.ImageStats()
		stats["in"].setInput( text["out"] )
		stats["regionOfInterest"].setValue( text["out"]["dataWindow"].getValue() )

		self.assertEqual( stats["max"].getValue(), IECore.Color4f( 1, 1, 1, 1 ) )

		text["color"]["a"].setValue( 0.5 )
		self.assertEqual( stats["max"].getValue(), IECore.Color4f( 0.5, 0.5, 0.5, 1 ) )

		text["color"].setValue( IECore.Color4f( 0.5, 0.25, 1, 0.5 ) )
		self.assertEqual( stats["max"].getValue(), IECore.Color4f( 0.25, 0.125, 0.5, 1 ) )

	def testDataWindow( self ) :

		text = GafferImage.Text()
		text["text"].setValue( "a" )
		w = text["out"]["dataWindow"].getValue()

		text["text"].setValue( "ab" )
		w2 = text["out"]["dataWindow"].getValue()

		self.assertEqual( w.min, w2.min )
		self.assertGreater( w2.max.x, w.max.x )
		self.assertGreater( w2.max.y, w.max.y )

	def testDefaultFormat( self ) :

		text = GafferImage.Text()
		with Gaffer.Context() as c :
			GafferImage.FormatPlug().setDefaultFormat( c, GafferImage.Format( 100, 200, 2 ) )
			self.assertEqual( text["out"]["format"].getValue(), GafferImage.Format( 100, 200, 2 ) )

	def testExpectedResult( self ) :

		constant = GafferImage.Constant()
		constant["color"].setValue( IECore.Color4f( 0.25, 0.5, 0.75, 1 ) )
		constant["format"].setValue( GafferImage.Format( 100, 100 ) )

		text = GafferImage.Text()
		text["in"].setInput( constant["out"] )
		text["color"].setValue( IECore.Color4f( 1, 0.75, 0.5, 1 ) )
		text["size"].setValue( IECore.V2i( 20 ) )
		text["area"].setValue( IECore.Box2i( IECore.V2i( 5 ), IECore.V2i( 95 ) ) )
		text["transform"]["pivot"].setValue( IECore.V2f( 50 ) )
		text["transform"]["rotate"].setValue( 90 )

		reader = GafferImage.ImageReader()
		reader["fileName"].setValue( os.path.dirname( __file__ ) + "/images/text.exr" )
		expectedImage = reader['out'].image()

		self.assertImagesEqual( text["out"], reader["out"], ignoreMetadata = True, maxDifference = 0.001 )

if __name__ == "__main__":
	unittest.main()
