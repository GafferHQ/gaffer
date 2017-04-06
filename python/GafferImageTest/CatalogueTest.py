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

import IECore

import Gaffer
import GafferTest
import GafferImage
import GafferImageTest

class CatalogueTest( GafferImageTest.ImageTestCase ) :

	def testImages( self ) :

		images = []
		readers = []
		for i, fileName in enumerate( [ "checker.exr", "blurRange.exr", "noisyRamp.exr", "resamplePatterns.exr" ] ) :
			images.append( GafferImage.Catalogue.Image.load( "${GAFFER_ROOT}/python/GafferImageTest/images/" + fileName ) )
			readers.append( GafferImage.ImageReader() )
			readers[-1]["fileName"].setValue( images[-1]["fileName"].getValue() )

		c = GafferImage.Catalogue()

		for image in images :
			c["images"].addChild( image )
			self.assertImagesEqual( readers[0]["out"], c["out"], ignoreMetadata = True )

		def assertExpectedImages() :

			for i, reader in enumerate( readers ) :
				c["imageIndex"].setValue( i )
				self.assertImagesEqual( readers[i]["out"], c["out"], ignoreMetadata = True )

		assertExpectedImages()

		for i in [ 1, 0, 1, 0 ] :
			c["images"].removeChild( c["images"][i] )
			del readers[i]
			assertExpectedImages()

	def testDescription( self ) :

		c = GafferImage.Catalogue()
		c["images"].addChild( c.Image.load( "${GAFFER_ROOT}/python/GafferImageTest/images/blurRange.exr" ) )
		self.assertEqual( c["out"]["metadata"].getValue()["ImageDescription"].value, "" )

		c["images"][-1]["description"].setValue( "ddd" )
		self.assertEqual( c["out"]["metadata"].getValue()["ImageDescription"].value, "ddd" )

	def testDescriptionLoading( self ) :

		c = GafferImage.Constant()

		m = GafferImage.ImageMetadata()
		m["in"].setInput( c["out"] )
		m["metadata"].addMember( "ImageDescription", "i am a description" )

		w = GafferImage.ImageWriter()
		w["in"].setInput( m["out"] )
		w["fileName"].setValue( os.path.join( self.temporaryDirectory(), "description.exr" ) )
		w["task"].execute()

		r = GafferImage.ImageReader()
		r["fileName"].setValue( w["fileName"].getValue() )

		i = GafferImage.Catalogue.Image.load( w["fileName"].getValue() )
		self.assertEqual( i["description"].getValue(), "i am a description" )

	def testSerialisation( self ) :

		s = Gaffer.ScriptNode()
		s["c"] = GafferImage.Catalogue()

		for i, fileName in enumerate( [ "checker.exr", "blurRange.exr" ] ) :
			s["c"]["images"].addChild(
				GafferImage.Catalogue.Image.load(
					"${GAFFER_ROOT}/python/GafferImageTest/images/" + fileName,
				)
			)

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( len( s["c"]["images"] ), len( s2["c"]["images"] ) )

		for i in range( 0, len( s["c"]["images"] ) ) :
			self.assertEqual(
				s["c"]["images"][i]["fileName"].getValue(),
				s2["c"]["images"][i]["fileName"].getValue()
			)
			s["c"]["imageIndex"].setValue( i )
			s2["c"]["imageIndex"].setValue( i )
			self.assertImagesEqual( s["c"]["out"], s2["c"]["out"] )

		s3 = Gaffer.ScriptNode()
		s3.execute( s2.serialise() )
		self.assertEqual( s3.serialise(), s2.serialise() )

		self.assertFalse( "setInput" in s3.serialise( filter = Gaffer.StandardSet( [ s3["c"] ] ) ) )

	def testDisabling( self ) :

		c1 = GafferImage.Catalogue()
		c1["images"].addChild(
			GafferImage.Catalogue.Image.load( "${GAFFER_ROOT}/python/GafferImageTest/images/checker.exr" )
		)

		c2 = GafferImage.Catalogue()
		c2["images"].addChild(
			GafferImage.Catalogue.Image.load( "${GAFFER_ROOT}/python/GafferImageTest/images/checker.exr" )
		)

		self.assertImagesEqual( c1["out"], c2["out"] )

		c2["enabled"].setValue( False )
		self.assertNotEqual( c2["out"]["format"].getValue(), c1["out"]["format"].getValue() )
		self.assertNotEqual( c2["out"]["dataWindow"].getValue(), c1["out"]["dataWindow"].getValue() )
		self.assertEqual( c2["out"]["dataWindow"].getValue(), IECore.Box2i() )

		disabledConstant = GafferImage.Constant()
		disabledConstant["enabled"].setValue( False )
		self.assertImagesEqual( c2["out"], disabledConstant["out"] )

if __name__ == "__main__":
	unittest.main()
