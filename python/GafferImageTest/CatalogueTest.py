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

	def setUp( self ) :

		GafferImageTest.ImageTestCase.setUp( self )

		# Emulate the UI by making the same connections it will
		self.__driverCreatedConnection = GafferImage.Display.driverCreatedSignal().connect( GafferImage.Catalogue.driverCreated )
		self.__imageReceivedConnection = GafferImage.Display.imageReceivedSignal().connect( GafferImage.Catalogue.imageReceived )

	def tearDown( self ) :

		self.__driverCreatedConnection = None
		self.__imageReceivedConnection = None

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

	def testDisplayDriver( self ) :

		c = GafferImage.Catalogue()
		self.assertEqual( len( c["images"] ), 0 )

		r = GafferImage.ImageReader()
		r["fileName"].setValue( "${GAFFER_ROOT}/python/GafferImageTest/images/checker.exr" )
		GafferImageTest.DisplayTest.sendImage( r["out"], c.displayDriverServer().portNumber() )

		self.assertEqual( len( c["images"] ), 1 )
		self.assertEqual( c["images"][0]["fileName"].getValue(), "" )
		self.assertEqual( c["imageIndex"].getValue(), 0 )
		self.assertImagesEqual( r["out"], c["out"], ignoreMetadata = True )

		r["fileName"].setValue( "${GAFFER_ROOT}/python/GafferImageTest/images/blurRange.exr" )
		GafferImageTest.DisplayTest.sendImage( r["out"], c.displayDriverServer().portNumber() )

		self.assertEqual( len( c["images"] ), 2 )
		self.assertEqual( c["images"][1]["fileName"].getValue(), "" )
		self.assertEqual( c["imageIndex"].getValue(), 1 )
		self.assertImagesEqual( r["out"], c["out"], ignoreMetadata = True )

	def testDisplayDriverAOVGrouping( self ) :

		c = GafferImage.Catalogue()
		self.assertEqual( len( c["images"] ), 0 )

		aov1 = GafferImage.Constant()
		aov1["format"].setValue( GafferImage.Format( 100, 100 ) )
		aov1["color"].setValue( IECore.Color4f( 1, 0, 0, 1 ) )

		aov2 = GafferImage.Constant()
		aov2["format"].setValue( GafferImage.Format( 100, 100 ) )
		aov2["color"].setValue( IECore.Color4f( 0, 1, 0, 1 ) )
		aov2["layer"].setValue( "diffuse" )

		GafferImageTest.DisplayTest.sendImage( aov1["out"], c.displayDriverServer().portNumber() )
		GafferImageTest.DisplayTest.sendImage( aov2["out"], c.displayDriverServer().portNumber() )

		self.assertEqual( len( c["images"] ), 1 )
		self.assertEqual(
			set( c["out"]["channelNames"].getValue() ),
			set( aov1["out"]["channelNames"].getValue() ) | set( aov2["out"]["channelNames"].getValue() )
		)

	def testDisplayDriverSaveToFile( self ) :

		s = Gaffer.ScriptNode()
		s["c"] = GafferImage.Catalogue()
		s["c"]["directory"].setValue( os.path.join( self.temporaryDirectory(), "catalogue" ) )

		r = GafferImage.ImageReader()
		r["fileName"].setValue( "${GAFFER_ROOT}/python/GafferImageTest/images/blurRange.exr" )
		GafferImageTest.DisplayTest.sendImage( r["out"], GafferImage.Catalogue.displayDriverServer().portNumber() )

		self.assertEqual( len( s["c"]["images"] ), 1 )
		self.assertEqual( os.path.dirname( s["c"]["images"][0]["fileName"].getValue() ), s["c"]["directory"].getValue() )
		self.assertImagesEqual( s["c"]["out"], r["out"], ignoreMetadata = True, maxDifference = 0.0003 )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( len( s2["c"]["images"] ), 1 )
		self.assertEqual( s2["c"]["images"][0]["fileName"].getValue(), s["c"]["images"][0]["fileName"].getValue() )
		self.assertImagesEqual( s2["c"]["out"], r["out"], ignoreMetadata = True, maxDifference = 0.0003 )

	def testCatalogueName( self ) :

		c1 = GafferImage.Catalogue()
		c2 = GafferImage.Catalogue()
		c2["name"].setValue( "catalogue2" )

		self.assertEqual( len( c1["images"] ), 0 )
		self.assertEqual( len( c2["images"] ), 0 )

		constant1 = GafferImage.Constant()
		constant2 = GafferImage.Constant()
		constant1["format"].setValue( GafferImage.Format( 100, 100 ) )
		constant2["format"].setValue( GafferImage.Format( 100, 100 ) )
		constant1["color"].setValue( IECore.Color4f( 1, 0, 0, 1 ) )
		constant2["color"].setValue( IECore.Color4f( 0, 1, 0, 1 ) )

		GafferImageTest.DisplayTest.sendImage(
			constant1["out"],
			GafferImage.Catalogue.displayDriverServer().portNumber(),
		)

		GafferImageTest.DisplayTest.sendImage(
			constant2["out"],
			GafferImage.Catalogue.displayDriverServer().portNumber(),
			extraParameters = {
				"catalogue:name" : "catalogue2",
			}
		)

		self.assertEqual( len( c1["images"] ), 1 )
		self.assertEqual( len( c2["images"] ), 1 )

		self.assertImagesEqual( c1["out"], constant1["out"], ignoreMetadata = True )
		self.assertImagesEqual( c2["out"], constant2["out"], ignoreMetadata = True )

	def testDontSerialiseUnsavedRenders( self ) :

		s = Gaffer.ScriptNode()
		s["c"] = GafferImage.Catalogue()

		constant = GafferImage.Constant()
		constant["format"].setValue( GafferImage.Format( 100, 100 ) )
		GafferImageTest.DisplayTest.sendImage(
			constant["out"],
			GafferImage.Catalogue.displayDriverServer().portNumber(),
		)

		self.assertEqual( len( s["c"]["images"] ), 1 )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( len( s2["c"]["images"] ), 0 )

	def testPromotion( self ) :

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()
		s["b"]["c"] = GafferImage.Catalogue()
		promotedImages = Gaffer.PlugAlgo.promote( s["b"]["c"]["images"] )
		promotedImageIndex = Gaffer.PlugAlgo.promote( s["b"]["c"]["imageIndex"] )
		promotedOut = Gaffer.PlugAlgo.promote( s["b"]["c"]["out"] )

		images = []
		readers = []
		for i, fileName in enumerate( [ "checker.exr", "blurRange.exr", "noisyRamp.exr" ] ) :
			images.append( GafferImage.Catalogue.Image.load( "${GAFFER_ROOT}/python/GafferImageTest/images/" + fileName ) )
			readers.append( GafferImage.ImageReader() )
			readers[-1]["fileName"].setValue( images[-1]["fileName"].getValue() )

		for image in images :
			promotedImages.addChild( image )
			self.assertImagesEqual( readers[0]["out"], promotedOut, ignoreMetadata = True )

		for i, reader in enumerate( readers ) :
			promotedImageIndex.setValue( i )
			self.assertImagesEqual( readers[i]["out"], promotedOut, ignoreMetadata = True )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		for i, reader in enumerate( readers ) :
			s2["b"]["imageIndex"].setValue( i )
			self.assertImagesEqual( readers[i]["out"], s2["b"]["out"], ignoreMetadata = True )

		s3 = Gaffer.ScriptNode()
		s3.execute( s.serialise() )

		for i, reader in enumerate( readers ) :
			s3["b"]["imageIndex"].setValue( i )
			self.assertImagesEqual( readers[i]["out"], s3["b"]["out"], ignoreMetadata = True )

	def testDisplayDriverAndPromotion( self ) :

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()
		s["b"]["c"] = GafferImage.Catalogue()
		s["b"]["c"]["directory"].setValue( os.path.join( self.temporaryDirectory(), "catalogue" ) )
		promotedImages = Gaffer.PlugAlgo.promote( s["b"]["c"]["images"] )
		promotedImageIndex = Gaffer.PlugAlgo.promote( s["b"]["c"]["imageIndex"] )
		promotedOut = Gaffer.PlugAlgo.promote( s["b"]["c"]["out"] )

		r = GafferImage.ImageReader()
		r["fileName"].setValue( "${GAFFER_ROOT}/python/GafferImageTest/images/checker.exr" )
		GafferImageTest.DisplayTest.sendImage( r["out"], GafferImage.Catalogue.displayDriverServer().portNumber() )

		self.assertEqual( len( promotedImages ), 1 )
		self.assertEqual( promotedImageIndex.getValue(), 0 )
		self.assertImagesEqual( r["out"], promotedOut, ignoreMetadata = True, maxDifference = 0.0003 )

		r["fileName"].setValue( "${GAFFER_ROOT}/python/GafferImageTest/images/blurRange.exr" )
		GafferImageTest.DisplayTest.sendImage( r["out"], GafferImage.Catalogue.displayDriverServer().portNumber() )

		self.assertEqual( len( promotedImages ), 2 )
		self.assertEqual( promotedImageIndex.getValue(), 1 )
		self.assertImagesEqual( r["out"], promotedOut, ignoreMetadata = True, maxDifference = 0.0003 )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( len( s2["b"]["images"] ), 2 )
		self.assertEqual( s2["b"]["imageIndex"].getValue(), 1 )
		self.assertImagesEqual( promotedOut, s2["b"]["c"]["out"], ignoreMetadata = True )

		s3 = Gaffer.ScriptNode()
		s3.execute( s2.serialise() )

		self.assertEqual( len( s3["b"]["images"] ), 2 )
		self.assertEqual( s3["b"]["imageIndex"].getValue(), 1 )
		self.assertImagesEqual( promotedOut, s3["b"]["c"]["out"], ignoreMetadata = True )

	def testDontSavePromotedUnsavedRenders( self ) :

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()
		s["b"]["c"] = GafferImage.Catalogue()
		promotedImages = Gaffer.PlugAlgo.promote( s["b"]["c"]["images"] )
		promotedImageIndex = Gaffer.PlugAlgo.promote( s["b"]["c"]["imageIndex"] )
		promotedOut = Gaffer.PlugAlgo.promote( s["b"]["c"]["out"] )

		r = GafferImage.ImageReader()
		r["fileName"].setValue( "${GAFFER_ROOT}/python/GafferImageTest/images/checker.exr" )
		GafferImageTest.DisplayTest.sendImage( r["out"], GafferImage.Catalogue.displayDriverServer().portNumber() )

		self.assertEqual( len( promotedImages ), 1 )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( len( s2["b"]["images"] ), 0 )

	def testUndoRedo( self ) :

		s = Gaffer.ScriptNode()
		s["c"] = GafferImage.Catalogue()
		s["c"]["images"].addChild( s["c"].Image.load( "${GAFFER_ROOT}/python/GafferImageTest/images/checker.exr" ) )

		r = GafferImage.ImageReader()
		r["fileName"].setValue( "${GAFFER_ROOT}/python/GafferImageTest/images/blurRange.exr" )

		def assertPreconditions() :

			self.assertEqual( len( s["c"]["images"] ), 1 )
			self.assertEqual( s["c"]["imageIndex"].getValue(), 0 )

		assertPreconditions()

		with Gaffer.UndoScope( s ) :
			s["c"]["images"].addChild( s["c"].Image.load( r["fileName"].getValue() ) )
			s["c"]["imageIndex"].setValue( 1 )

		def assertPostConditions() :

			self.assertEqual( len( s["c"]["images"] ), 2 )
			self.assertEqual( s["c"]["imageIndex"].getValue(), 1 )
			self.assertImagesEqual( s["c"]["out"], r["out"], ignoreMetadata = True )

		assertPostConditions()

		s.undo()
		assertPreconditions()

		s.redo()
		assertPostConditions()

		s.undo()
		assertPreconditions()

if __name__ == "__main__":
	unittest.main()
