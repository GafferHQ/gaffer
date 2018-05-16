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
import threading
import stat
import imath

import IECore

import Gaffer
import GafferTest
import GafferImage
import GafferImageTest

class CatalogueTest( GafferImageTest.ImageTestCase ) :

	@staticmethod
	def sendImage( image, catalogue, extraParameters = {}, waitForSave = True ) :

		if catalogue["directory"].getValue() and waitForSave :

			# When the image has been received, the Catalogue will
			# save it to disk on a background thread, and we need
			# to wait for that to complete.
			with GafferTest.ParallelAlgoTest.ExpectedUIThreadCall() :
				GafferImageTest.DisplayTest.Driver.sendImage( image, GafferImage.Catalogue.displayDriverServer().portNumber(), extraParameters )

		else :

			GafferImageTest.DisplayTest.Driver.sendImage( image, GafferImage.Catalogue.displayDriverServer().portNumber(), extraParameters )

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
		self.assertEqual( c2["out"]["dataWindow"].getValue(), imath.Box2i() )

		disabledConstant = GafferImage.Constant()
		disabledConstant["enabled"].setValue( False )
		self.assertImagesEqual( c2["out"], disabledConstant["out"] )

	def testDisplayDriver( self ) :

		c = GafferImage.Catalogue()
		self.assertEqual( len( c["images"] ), 0 )

		r = GafferImage.ImageReader()
		r["fileName"].setValue( "${GAFFER_ROOT}/python/GafferImageTest/images/checker.exr" )
		self.sendImage( r["out"], c )

		self.assertEqual( len( c["images"] ), 1 )
		self.assertEqual( c["images"][0]["fileName"].getValue(), "" )
		self.assertEqual( c["imageIndex"].getValue(), 0 )

		self.assertImagesEqual( r["out"], c["out"], ignoreMetadata = True )

		r["fileName"].setValue( "${GAFFER_ROOT}/python/GafferImageTest/images/blurRange.exr" )
		self.sendImage( r["out"], c )

		self.assertEqual( len( c["images"] ), 2 )
		self.assertEqual( c["images"][1]["fileName"].getValue(), "" )
		self.assertEqual( c["imageIndex"].getValue(), 1 )
		self.assertImagesEqual( r["out"], c["out"], ignoreMetadata = True )

	def testDisplayDriverAOVGrouping( self ) :

		c = GafferImage.Catalogue()
		self.assertEqual( len( c["images"] ), 0 )

		aov1 = GafferImage.Constant()
		aov1["format"].setValue( GafferImage.Format( 100, 100 ) )
		aov1["color"].setValue( imath.Color4f( 1, 0, 0, 1 ) )

		aov2 = GafferImage.Constant()
		aov2["format"].setValue( GafferImage.Format( 100, 100 ) )
		aov2["color"].setValue( imath.Color4f( 0, 1, 0, 1 ) )
		aov2["layer"].setValue( "diffuse" )

		self.sendImage( aov1["out"], c )
		self.sendImage( aov2["out"], c )

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
		self.sendImage( r["out"], s["c"] )

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
		constant1["color"].setValue( imath.Color4f( 1, 0, 0, 1 ) )
		constant2["color"].setValue( imath.Color4f( 0, 1, 0, 1 ) )

		self.sendImage(
			constant1["out"],
			c1,
		)

		self.sendImage(
			constant2["out"],
			c2,
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
		self.sendImage(
			constant["out"],
			s["c"],
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
		self.sendImage( r["out"], s["b"]["c"] )

		self.assertEqual( len( promotedImages ), 1 )
		self.assertEqual( promotedImageIndex.getValue(), 0 )
		self.assertImagesEqual( r["out"], promotedOut, ignoreMetadata = True )

		r["fileName"].setValue( "${GAFFER_ROOT}/python/GafferImageTest/images/blurRange.exr" )
		self.sendImage( r["out"], s["b"]["c"] )

		self.assertEqual( len( promotedImages ), 2 )
		self.assertEqual( promotedImageIndex.getValue(), 1 )
		self.assertImagesEqual( r["out"], promotedOut, ignoreMetadata = True )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( len( s2["b"]["images"] ), 2 )
		self.assertEqual( s2["b"]["imageIndex"].getValue(), 1 )
		self.assertImagesEqual( promotedOut, s2["b"]["c"]["out"], ignoreMetadata = True, maxDifference = 0.0003 )

		s3 = Gaffer.ScriptNode()
		s3.execute( s2.serialise() )

		self.assertEqual( len( s3["b"]["images"] ), 2 )
		self.assertEqual( s3["b"]["imageIndex"].getValue(), 1 )
		self.assertImagesEqual( promotedOut, s3["b"]["c"]["out"], ignoreMetadata = True, maxDifference = 0.0003 )

	def testDontSavePromotedUnsavedRenders( self ) :

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()
		s["b"]["c"] = GafferImage.Catalogue()
		promotedImages = Gaffer.PlugAlgo.promote( s["b"]["c"]["images"] )
		promotedImageIndex = Gaffer.PlugAlgo.promote( s["b"]["c"]["imageIndex"] )
		promotedOut = Gaffer.PlugAlgo.promote( s["b"]["c"]["out"] )

		r = GafferImage.ImageReader()
		r["fileName"].setValue( "${GAFFER_ROOT}/python/GafferImageTest/images/checker.exr" )
		self.sendImage( r["out"], s["b"]["c"] )

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

	def testGILManagement( self ) :

		# Make a network where a Catalogue
		# is merged with an image that depends
		# on a python expression.

		s = Gaffer.ScriptNode()
		s["catalogue"] = GafferImage.Catalogue()

		s["constant"] = GafferImage.Constant()

		s["expression"] = Gaffer.Expression()
		s["expression"].setExpression( 'parent["constant"]["color"]["r"] = context["image:tileOrigin"].x' )

		s["merge"] = GafferImage.Merge()
		s["merge"]["in"][0].setInput( s["catalogue"]["out"] )
		s["merge"]["in"][1].setInput( s["constant"]["out"] )

		# Arrange to generate the resulting image from C++
		# threads whenever it is dirtied.

		processTilesConnection = Gaffer.ScopedConnection( GafferImageTest.connectProcessTilesToPlugDirtiedSignal( s["merge"]["out"] ) )

		# Send an image to the catalogue to demonstrate that
		# we do not deadlock on the GIL.

		r = GafferImage.ImageReader()
		r["fileName"].setValue( "${GAFFER_ROOT}/python/GafferImageTest/images/checker.exr" )

		self.sendImage( r["out"], s["catalogue"] )

	def testCacheReuse( self ) :

		# Send an image to the catalogue, and also
		# capture the display driver that we used to
		# send it.

		c = GafferImage.Catalogue()
		c["directory"].setValue( os.path.join( self.temporaryDirectory(), "catalogue" ) )

		drivers = GafferTest.CapturingSlot( GafferImage.Display.driverCreatedSignal() )

		r = GafferImage.ImageReader()
		r["fileName"].setValue( "${GAFFER_ROOT}/python/GafferImageTest/images/checker.exr" )
		self.sendImage( r["out"], c )

		self.assertEqual( len( drivers ), 1 )

		# The image will have been saved to disk so it can persist between sessions,
		# and the Catalogue should have dropped any reference it has to the driver,
		# in order to save memory.

		self.assertEqual( len( c["images"] ), 1 )
		self.assertEqual( os.path.dirname( c["images"][0]["fileName"].getValue() ), c["directory"].getValue() )

		self.assertEqual( drivers[0][0].refCount(), 1 )

		# But we don't want the Catalogue to immediately reload the image from
		# disk, because for large images with many AOVs this is a huge overhead.
		# We want to temporarily reuse the cache entries that were created from
		# the data in the display driver. These should be identical to a regular
		# Display node containing the same driver.

		display = GafferImage.Display()
		display.setDriver( drivers[0][0] )

		self.assertEqual(
			display["out"].channelDataHash( "R", imath.V2i( 0 ) ),
			c["out"].channelDataHash( "R", imath.V2i( 0 ) )
		)
		self.assertTrue(
			display["out"].channelData( "R", imath.V2i( 0 ), _copy = False ).isSame(
				c["out"].channelData( "R", imath.V2i( 0 ), _copy = False )
			)
		)

		# This applies to copies too

		c["images"].addChild( GafferImage.Catalogue.Image( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		self.assertEqual( len( c["images"] ), 2 )
		c["images"][1].copyFrom( c["images"][0] )

		c["imageIndex"].setValue( 1 )
		self.assertEqual(
			display["out"].channelDataHash( "R", imath.V2i( 0 ) ),
			c["out"].channelDataHash( "R", imath.V2i( 0 ) )
		)
		self.assertTrue(
			display["out"].channelData( "R", imath.V2i( 0 ), _copy = False ).isSame(
				c["out"].channelData( "R", imath.V2i( 0 ), _copy = False )
			)
		)

	def testCopyFrom( self ) :

		c = GafferImage.Catalogue()
		c["images"].addChild( c.Image.load( "${GAFFER_ROOT}/python/GafferImageTest/images/checker.exr" ) )
		c["images"][0]["description"].setValue( "test" )

		c["images"].addChild( c.Image( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		c["images"][1].copyFrom( c["images"][0] )

		self.assertEqual( c["images"][1]["description"].getValue(), c["images"][0]["description"].getValue() )
		self.assertEqual( c["images"][1]["fileName"].getValue(), c["images"][0]["fileName"].getValue() )

	def testDeleteBeforeSaveCompletes( self ) :

		c = GafferImage.Catalogue()
		c["directory"].setValue( os.path.join( self.temporaryDirectory(), "catalogue" ) )

		r = GafferImage.ImageReader()
		r["fileName"].setValue( "${GAFFER_ROOT}/python/GafferImageTest/images/checker.exr" )

		with GafferTest.ParallelAlgoTest.ExpectedUIThreadCall() :
			self.sendImage( r["out"], c, waitForSave = False )
			del c

	def testNonWritableDirectory( self ) :

		s = Gaffer.ScriptNode()
		s["c"] = GafferImage.Catalogue()
		s["c"]["directory"].setValue( os.path.join( self.temporaryDirectory(), "catalogue" ) )
		os.chmod( self.temporaryDirectory(), stat.S_IREAD )

		r = GafferImage.ImageReader()
		r["fileName"].setValue( "${GAFFER_ROOT}/python/GafferImageTest/images/blurRange.exr" )

		originalMessageHandler = IECore.MessageHandler.getDefaultHandler()
		mh = IECore.CapturingMessageHandler()
		IECore.MessageHandler.setDefaultHandler( mh )

		try :
			self.sendImage( r["out"], s["c"] )
		finally :
			IECore.MessageHandler.setDefaultHandler( originalMessageHandler )

		self.assertEqual( len( mh.messages ), 1 )
		self.assertEqual( mh.messages[0].level, IECore.Msg.Level.Error )
		self.assertIn( "Permission denied", mh.messages[0].message )

		with self.assertRaisesRegexp( RuntimeError, "Could not open file" ) :
			s["c"]["out"].image()

if __name__ == "__main__":
	unittest.main()
