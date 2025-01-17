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
import shutil
import imath
import pathlib
import unittest
import subprocess

import IECore

import Gaffer
import GafferTest
import GafferImage
import GafferImageTest

class CatalogueTest( GafferImageTest.ImageTestCase ) :

	@staticmethod
	def sendImage( image, catalogue, extraParameters = {}, waitForSave = True, close = True ) :

		with GafferTest.ParallelAlgoTest.UIThreadCallHandler() as h :
			result = GafferImageTest.DisplayTest.Driver.sendImage( image, GafferImage.Catalogue.displayDriverServer().portNumber(), extraParameters, close = close )
			if catalogue["directory"].getValue() and waitForSave :
				# When the image has been received, the Catalogue will
				# save it to disk on a background thread, and we need
				# to wait for that to complete.
				h.assertCalled()
				h.assertDone()

		return result

	__catalogueIsRenderingMetadataKey = "gaffer:isRendering"

	def testImages( self ) :

		images = []
		readers = []
		for i, fileName in enumerate( [ "checker.exr", "blurRange.exr", "noisyRamp.exr", "resamplePatterns.exr" ] ) :
			images.append( GafferImage.Catalogue.Image.load( self.imagesPath() / fileName ) )
			readers.append( GafferImage.ImageReader() )
			readers[-1]["fileName"].setValue( images[-1]["fileName"].getValue() )

		c = GafferImage.Catalogue()

		for image in images :
			c["images"].addChild( image )
			self.assertImagesEqual( readers[0]["out"], c["out"] )

		def assertExpectedImages() :

			for i, reader in enumerate( readers ) :
				c["imageIndex"].setValue( i )
				self.assertImagesEqual( readers[i]["out"], c["out"] )

		assertExpectedImages()

		for i in [ 1, 0, 1, 0 ] :
			c["images"].removeChild( c["images"][i] )
			del readers[i]
			assertExpectedImages()

	def testDescription( self ) :

		c = GafferImage.Catalogue()
		c["images"].addChild( c.Image.load( self.imagesPath() / "blurRange.exr" ) )
		self.assertNotIn( "ImageDescription", c["out"]["metadata"].getValue() )

		c["images"][-1]["description"].setValue( "ddd" )
		self.assertEqual( c["out"]["metadata"].getValue()["ImageDescription"].value, "ddd" )

	def testDescriptionLoading( self ) :

		c = GafferImage.Constant()

		m = GafferImage.ImageMetadata()
		m["in"].setInput( c["out"] )
		m["metadata"].addChild( Gaffer.NameValuePlug( "ImageDescription", "i am a description" ) )

		w = GafferImage.ImageWriter()
		w["in"].setInput( m["out"] )
		w["fileName"].setValue( self.temporaryDirectory() / "description.exr" )
		w["task"].execute()

		r = GafferImage.ImageReader()
		r["fileName"].setValue( w["fileName"].getValue() )

		c = GafferImage.Catalogue()
		c["images"].addChild( GafferImage.Catalogue.Image.load( w["fileName"].getValue() ) )
		self.assertEqual( c["images"][0]["description"].getValue(), "" )
		self.assertEqual( c["out"]["metadata"].getValue()["ImageDescription"].value, "i am a description" )

	def testSerialisation( self ) :

		s = Gaffer.ScriptNode()
		s["c"] = GafferImage.Catalogue()

		for i, fileName in enumerate( [ "checker.exr", "blurRange.exr" ] ) :
			s["c"]["images"].addChild(
				GafferImage.Catalogue.Image.load(
					self.imagesPath() / fileName,
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
			GafferImage.Catalogue.Image.load( self.imagesPath() / "checker.exr" )
		)

		c2 = GafferImage.Catalogue()
		c2["images"].addChild(
			GafferImage.Catalogue.Image.load( self.imagesPath() / "checker.exr" )
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
		r["fileName"].setValue( self.imagesPath() / "checker.exr" )

		driver = self.sendImage( r["out"], c, close = False )
		self.assertEqual( c["out"]["metadata"].getValue()[ self.__catalogueIsRenderingMetadataKey ].value, True )
		driver.close()
		self.assertNotIn( self.__catalogueIsRenderingMetadataKey, c["out"]["metadata"].getValue() )

		self.assertEqual( len( c["images"] ), 1 )
		self.assertEqual( c["images"][0]["fileName"].getValue(), "" )
		self.assertEqual( c["imageIndex"].getValue(), 0 )

		self.assertImagesEqual( r["out"], c["out"] )

		r["fileName"].setValue( self.imagesPath() / "blurRange.exr" )
		self.sendImage( r["out"], c )

		self.assertEqual( len( c["images"] ), 2 )
		self.assertEqual( c["images"][1]["fileName"].getValue(), "" )
		self.assertEqual( c["imageIndex"].getValue(), 1 )
		self.assertImagesEqual( r["out"], c["out"] )

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

		driver = self.sendImage( aov1["out"], c, close = False )
		self.sendImage( aov2["out"], c )
		driver.close()

		self.assertEqual( len( c["images"] ), 1 )
		self.assertEqual(
			set( c["out"]["channelNames"].getValue() ),
			set( aov1["out"]["channelNames"].getValue() ) | set( aov2["out"]["channelNames"].getValue() )
		)

	def testDisplayDriverSaveToFile( self ) :

		s = Gaffer.ScriptNode()
		s["c"] = GafferImage.Catalogue()
		s["c"]["directory"].setValue( self.temporaryDirectory() / "catalogue" )

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.imagesPath() / "blurRange.exr" )
		self.sendImage( r["out"], s["c"] )
		self.assertEqual( len( s["c"]["images"] ), 1 )
		self.assertEqual( pathlib.Path( s["c"]["images"][0]["fileName"].getValue() ).parent.as_posix(), s["c"]["directory"].getValue() )
		self.assertImagesEqual( s["c"]["out"], r["out"], ignoreMetadata = True, maxDifference = 0.0003 )

		r["fileName"].setValue( s["c"]["images"][0]["fileName"].getValue() )
		self.assertNotIn( self.__catalogueIsRenderingMetadataKey, r["out"]["metadata"].getValue() )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( len( s2["c"]["images"] ), 1 )
		self.assertEqual( s2["c"]["images"][0]["fileName"].getValue(), s["c"]["images"][0]["fileName"].getValue() )
		self.assertImagesEqual( s2["c"]["out"], r["out"], ignoreMetadata = True, maxDifference = 0.0003 )

		r["fileName"].setValue( s2["c"]["images"][0]["fileName"].getValue() )
		self.assertNotIn( self.__catalogueIsRenderingMetadataKey, r["out"]["metadata"].getValue() )

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

		self.assertImagesEqual( c1["out"], constant1["out"] )
		self.assertImagesEqual( c2["out"], constant2["out"] )

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
			images.append( GafferImage.Catalogue.Image.load( self.imagesPath() / fileName ) )
			readers.append( GafferImage.ImageReader() )
			readers[-1]["fileName"].setValue( images[-1]["fileName"].getValue() )

		for image in images :
			promotedImages.addChild( image )
			self.assertImagesEqual( readers[0]["out"], promotedOut )

		for i, reader in enumerate( readers ) :
			promotedImageIndex.setValue( i )
			self.assertImagesEqual( readers[i]["out"], promotedOut )

		promotedImages[2]["outputIndex"].setValue( 1 )
		promotedImages[0]["outputIndex"].setValue( 2 )

		with Gaffer.Context( s.context() ) as c :
			c["catalogue:imageName"] = "output:1"
			self.assertImagesEqual( readers[2]["out"], promotedOut )
			c["catalogue:imageName"] = "output:2"
			self.assertImagesEqual( readers[0]["out"], promotedOut )

			promotedImages[1]["outputIndex"].setValue( 1 )
			c["catalogue:imageName"] = "output:1"
			self.assertImagesEqual( readers[1]["out"], promotedOut )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		for i, reader in enumerate( readers ) :
			s2["b"]["imageIndex"].setValue( i )
			self.assertImagesEqual( readers[i]["out"], s2["b"]["out"] )

		s3 = Gaffer.ScriptNode()
		s3.execute( s.serialise() )

		for i, reader in enumerate( readers ) :
			s3["b"]["imageIndex"].setValue( i )
			self.assertImagesEqual( readers[i]["out"], s3["b"]["out"] )

	def testDisplayDriverAndPromotion( self ) :

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()
		s["b"]["c"] = GafferImage.Catalogue()
		s["b"]["c"]["directory"].setValue( self.temporaryDirectory() / "catalogue" )
		promotedImages = Gaffer.PlugAlgo.promote( s["b"]["c"]["images"] )
		promotedImageIndex = Gaffer.PlugAlgo.promote( s["b"]["c"]["imageIndex"] )
		promotedOut = Gaffer.PlugAlgo.promote( s["b"]["c"]["out"] )

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.imagesPath() / "checker.exr" )
		self.sendImage( r["out"], s["b"]["c"] )

		self.assertEqual( len( promotedImages ), 1 )
		self.assertEqual( promotedImageIndex.getValue(), 0 )
		self.assertImagesEqual( r["out"], promotedOut, ignoreMetadata = True )

		r["fileName"].setValue( self.imagesPath() / "blurRange.exr" )
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
		r["fileName"].setValue( self.imagesPath() / "checker.exr" )
		self.sendImage( r["out"], s["b"]["c"] )

		self.assertEqual( len( promotedImages ), 1 )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( len( s2["b"]["images"] ), 0 )

	def testUndoRedo( self ) :

		s = Gaffer.ScriptNode()
		s["c"] = GafferImage.Catalogue()
		s["c"]["images"].addChild( s["c"].Image.load( self.imagesPath() / "checker.exr" ) )

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.imagesPath() / "blurRange.exr" )

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
			self.assertImagesEqual( s["c"]["out"], r["out"] )

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

		processTilesConnection = Gaffer.Signals.ScopedConnection( GafferImageTest.connectProcessTilesToPlugDirtiedSignal( s["merge"]["out"] ) )

		# Send an image to the catalogue to demonstrate that
		# we do not deadlock on the GIL.

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.imagesPath() / "checker.exr" )

		self.sendImage( r["out"], s["catalogue"] )

	def testCacheReuse( self ) :

		# Send an image to the catalogue, and also
		# capture the display driver that we used to
		# send it.

		s = Gaffer.ScriptNode()

		s["c"] = GafferImage.Catalogue()
		s["c"]["directory"].setValue( self.temporaryDirectory() / "catalogue" )

		drivers = GafferTest.CapturingSlot( GafferImage.Display.driverCreatedSignal() )

		s["r"] = GafferImage.ImageReader()
		s["r"]["fileName"].setValue( self.imagesPath() / "checker.exr" )
		self.sendImage( s["r"]["out"], s["c"] )

		self.assertEqual( len( drivers ), 1 )

		# The image will have been saved to disk so it can persist between sessions,
		# and the Catalogue should have dropped any reference it has to the driver,
		# in order to save memory.

		self.assertEqual( len( s["c"]["images"] ), 1 )
		self.assertEqual( pathlib.Path( s["c"]["images"][0]["fileName"].getValue() ).parent.as_posix(), s["c"]["directory"].getValue() )

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
			s["c"]["out"].channelDataHash( "R", imath.V2i( 0 ) )
		)
		self.assertTrue(
			display["out"].channelData( "R", imath.V2i( 0 ), _copy = False ).isSame(
				s["c"]["out"].channelData( "R", imath.V2i( 0 ), _copy = False )
			)
		)

		# This applies to copies too

		s["c"]["images"].addChild( GafferImage.Catalogue.Image( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		self.assertEqual( len( s["c"]["images"] ), 2 )
		s["c"]["images"][1].copyFrom( s["c"]["images"][0] )

		s["c"]["imageIndex"].setValue( 1 )
		self.assertEqual(
			display["out"].channelDataHash( "R", imath.V2i( 0 ) ),
			s["c"]["out"].channelDataHash( "R", imath.V2i( 0 ) )
		)
		self.assertTrue(
			display["out"].channelData( "R", imath.V2i( 0 ), _copy = False ).isSame(
				s["c"]["out"].channelData( "R", imath.V2i( 0 ), _copy = False )
			)
		)

	def testCopyFrom( self ) :

		c = GafferImage.Catalogue()
		c["images"].addChild( c.Image.load( self.imagesPath() / "checker.exr" ) )
		c["images"][0]["description"].setValue( "test" )

		c["images"].addChild( c.Image( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		c["images"][1].copyFrom( c["images"][0] )

		self.assertEqual( c["images"][1]["description"].getValue(), c["images"][0]["description"].getValue() )
		self.assertEqual( c["images"][1]["fileName"].getValue(), c["images"][0]["fileName"].getValue() )

		c["imageIndex"].setValue( 1 )
		self.assertNotIn( self.__catalogueIsRenderingMetadataKey, c["out"]["metadata"].getValue() )

	def testDeleteBeforeSaveCompletes( self ) :

		c = GafferImage.Catalogue()
		c["directory"].setValue( self.temporaryDirectory() / "catalogue" )

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.imagesPath() / "checker.exr" )

		with GafferTest.ParallelAlgoTest.UIThreadCallHandler() as h :
			self.sendImage( r["out"], c, waitForSave = False )
			del c

	def testDeleteBeforeSaveCompletesWithScriptVariables( self ) :

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( "testDeleteBeforeSaveCompletesWithScriptVariables" )
		self.assertEqual( s.context().substitute( "${script:name}" ), "testDeleteBeforeSaveCompletesWithScriptVariables" )

		baseDirectory = self.temporaryDirectory() / "catalogue"
		# we don't expect to need to write here, but to ensure
		# we didn't even try to do so we make it read only.
		os.mkdir( baseDirectory )
		os.chmod( baseDirectory, stat.S_IREAD | stat.S_IEXEC )
		directory = baseDirectory / "${script:name}" / "images"

		s["c"] = GafferImage.Catalogue()
		s["c"]["directory"].setValue( directory )

		fullDirectory = pathlib.Path( s.context().substitute( s["c"]["directory"].getValue() ) )
		self.assertNotEqual( directory, fullDirectory )
		self.assertEqual( len( list( baseDirectory.glob( "*" ) ) ), 0 )

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.imagesPath() / "checker.exr" )

		driver = self.sendImage( r["out"], s["c"], waitForSave = False, close = False )
		# Simulate deletion by removing it from the script but keeping it alive.
		# This would typically be fine, but we've setup the directory to require
		# a script and then removed the script prior to closing the driver. Note
		# we can't actually delete the catalogue yet or `driver.close()` would
		# hang indefinitely waiting for an imageReceivedSignal.
		c = s["c"]
		s.removeChild( s["c"] )
		driver.close()

		self.assertEqual( len( list( baseDirectory.glob( "*" ) ) ), 0 )

	def testNonWritableDirectory( self ) :

		s = Gaffer.ScriptNode()
		s["c"] = GafferImage.Catalogue()
		s["c"]["directory"].setValue( self.temporaryDirectory() / "catalogue" )
		if os.name != "nt" :
			os.chmod( self.temporaryDirectory(), stat.S_IREAD )
		else :
			subprocess.check_call( [ "icacls", self.temporaryDirectory(), "/deny", "Users:(OI)(CI)(W)" ] )

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.imagesPath() / "blurRange.exr" )

		originalMessageHandler = IECore.MessageHandler.getDefaultHandler()
		mh = IECore.CapturingMessageHandler()
		IECore.MessageHandler.setDefaultHandler( mh )

		try :
			self.sendImage( r["out"], s["c"] )
		finally :
			IECore.MessageHandler.setDefaultHandler( originalMessageHandler )

		self.assertEqual( len( mh.messages ), 1 )
		self.assertEqual( mh.messages[0].level, IECore.Msg.Level.Error )
		self.assertIn(
			"Permission denied" if os.name != "nt" else "Access is denied",
			mh.messages[0].message
		)

		with self.assertRaisesRegex(
			RuntimeError,
			r".* : Could not open \".*\" " + (
				"\(Permission denied\)" if os.name != "nt" else "\(No such file or directory\)"
			)
		) :
			GafferImage.ImageAlgo.image( s["c"]["out"] )

	def testDeleteKeepsOrder( self ) :

		# Send 4 images to a Catalogue : red, green, blue, yellow

		script = Gaffer.ScriptNode()
		script["catalogue"] = GafferImage.Catalogue()
		script["catalogue"]["directory"].setValue( self.temporaryDirectory() / "catalogue" )

		script["red"] = GafferImage.Constant()
		script["red"]["format"].setValue( GafferImage.Format( 64, 64 ) )
		script["red"]["color"]["r"].setValue( 1 )
		self.sendImage( script["red"]["out"], script["catalogue"] )
		script["catalogue"]["images"][-1].setName( "Red" )

		script["green"] = GafferImage.Constant()
		script["green"]["format"].setValue( GafferImage.Format( 64, 64 ) )
		script["green"]["color"]["g"].setValue( 1 )
		self.sendImage( script["green"]["out"], script["catalogue"] )
		script["catalogue"]["images"][-1].setName( "Green" )

		script["blue"] = GafferImage.Constant()
		script["blue"]["format"].setValue( GafferImage.Format( 64, 64 ) )
		script["blue"]["color"]["b"].setValue( 1 )
		self.sendImage( script["blue"]["out"], script["catalogue"] )
		script["catalogue"]["images"][-1].setName( "Blue" )

		script["yellow"] = GafferImage.Constant()
		script["yellow"]["format"].setValue( GafferImage.Format( 64, 64 ) )
		script["yellow"]["color"].setValue( imath.Color4f( 1, 1, 0, 1 ) )
		self.sendImage( script["yellow"]["out"], script["catalogue"] )
		script["catalogue"]["images"][-1].setName( "Yellow" )

		# Check it worked

		def assertPreconditions() :

			self.assertEqual( len( script["catalogue"]["images"] ), 4 )
			self.assertEqual( script["catalogue"]["images"][0].getName(), "Red" )
			self.assertEqual( script["catalogue"]["images"][1].getName(), "Green" )
			self.assertEqual( script["catalogue"]["images"][2].getName(), "Blue" )
			self.assertEqual( script["catalogue"]["images"][3].getName(), "Yellow" )

			script["catalogue"]["imageIndex"].setValue( 0 )
			self.assertImagesEqual( script["catalogue"]["out"], script["red"]["out"], ignoreMetadata = True )
			script["catalogue"]["imageIndex"].setValue( 1 )
			self.assertImagesEqual( script["catalogue"]["out"], script["green"]["out"], ignoreMetadata = True )
			script["catalogue"]["imageIndex"].setValue( 2 )
			self.assertImagesEqual( script["catalogue"]["out"], script["blue"]["out"], ignoreMetadata = True )
			script["catalogue"]["imageIndex"].setValue( 3 )
			self.assertImagesEqual( script["catalogue"]["out"], script["yellow"]["out"], ignoreMetadata = True )

			with Gaffer.Context( script.context() ) as c :
				c["catalogue:imageName"] = "Red"
				self.assertImagesEqual( script["catalogue"]["out"], script["red"]["out"], ignoreMetadata = True )
				c["catalogue:imageName"] = "Green"
				self.assertImagesEqual( script["catalogue"]["out"], script["green"]["out"], ignoreMetadata = True )
				c["catalogue:imageName"] = "Blue"
				self.assertImagesEqual( script["catalogue"]["out"], script["blue"]["out"], ignoreMetadata = True )
				c["catalogue:imageName"] = "Yellow"
				self.assertImagesEqual( script["catalogue"]["out"], script["yellow"]["out"], ignoreMetadata = True )

		assertPreconditions()

		# Delete green, then blue, then yellow

		script["catalogue"]["imageIndex"].setValue( 0 )

		with Gaffer.UndoScope( script ) :
			del script["catalogue"]["images"][1]
			del script["catalogue"]["images"][1]
			del script["catalogue"]["images"][1]

		# Check it worked

		def assertPostConditions() :

			self.assertEqual( len( script["catalogue"]["images"] ), 1 )
			self.assertEqual( script["catalogue"]["images"][0].getName(), "Red" )

			script["catalogue"]["imageIndex"].setValue( 0 )
			self.assertImagesEqual( script["catalogue"]["out"], script["red"]["out"], ignoreMetadata = True )

			with Gaffer.Context( script.context() ) as c :
				c["catalogue:imageName"] = "Red"
				self.assertImagesEqual( script["catalogue"]["out"], script["red"]["out"], ignoreMetadata = True )


		assertPostConditions()

		# Check that undo and redo work

		script.undo()
		assertPreconditions()

		script.redo()
		assertPostConditions()

		script.undo()
		assertPreconditions()

	def testLoadWithInvalidNames( self ) :

		sourceFile = pathlib.Path( __file__ ).parent /  "images" / "blurRange.exr"

		for name, expectedName in [
			( "0", "_0" ),
			( "[]", "__" ),
			( "(", "_" ),
			( "%", "_" ),
		] :

			fileName = self.temporaryDirectory() / ( name + ".exr" )
			shutil.copyfile( sourceFile, fileName )
			GafferImage.Catalogue.Image.load( fileName )

	def testRenamePromotedImages( self ) :

		# Create boxed Catalogue with promoted `images` plug.

		s = Gaffer.ScriptNode()

		s["box"] = Gaffer.Box()

		s["box"]["catalogue"] = GafferImage.Catalogue()
		s["box"]["catalogue"]["directory"].setValue( self.temporaryDirectory() / "catalogue" )

		images = Gaffer.PlugAlgo.promote( s["box"]["catalogue"]["images"] )

		# Send 2 images and name them using the promoted plugs.

		red = GafferImage.Constant()
		red["format"].setValue( GafferImage.Format( 64, 64 ) )
		red["color"]["r"].setValue( 1 )
		self.sendImage( red["out"], s["box"]["catalogue"] )
		images[-1].setName( "Red" )
		images[-1]["outputIndex"].setValue( 1 )

		green = GafferImage.Constant()
		green["format"].setValue( GafferImage.Format( 64, 64 ) )
		green["color"]["g"].setValue( 1 )
		self.sendImage( green["out"], s["box"]["catalogue"] )
		images[-1].setName( "Green" )
		images[-1]["outputIndex"].setValue( 2 )

		# Assert that images are accessible under those names ( and output indices ).

		with Gaffer.Context() as c :
			c["catalogue:imageName"] = "Red"
			self.assertImagesEqual( s["box"]["catalogue"]["out"], red["out"], ignoreMetadata = True )
			c["catalogue:imageName"] = "Green"
			self.assertImagesEqual( s["box"]["catalogue"]["out"], green["out"], ignoreMetadata = True )
			c["catalogue:imageName"] = "output:1"
			self.assertImagesEqual( s["box"]["catalogue"]["out"], red["out"], ignoreMetadata = True )
			c["catalogue:imageName"] = "output:2"
			self.assertImagesEqual( s["box"]["catalogue"]["out"], green["out"], ignoreMetadata = True )

		# And that invalid names generate errors.

		notFoundText = GafferImage.Text()
		notFoundText["text"].setValue( 'Catalogue : Unknown Image "Blue"' )
		notFoundText["size"].setValue( imath.V2i( 100 ) )
		notFoundText["area"].setValue( imath.Box2i( imath.V2i( 0, 0 ), imath.V2i( 1920, 1080 ) ) )
		notFoundText["horizontalAlignment"].setValue( GafferImage.Text.HorizontalAlignment.HorizontalCenter )
		notFoundText["verticalAlignment"].setValue( GafferImage.Text.VerticalAlignment.VerticalCenter )

		with Gaffer.Context() as c :
			c["catalogue:imageName"] = "Blue"
			self.assertImagesEqual( s["box"]["catalogue"]["out"], notFoundText["out"], ignoreMetadata = True )

		# Assert that we can rename the images and get them under the new name.

		images[0].setName( "Crimson" )
		images[1].setName( "Emerald" )

		with Gaffer.Context() as c :
			c["catalogue:imageName"] = "Crimson"
			self.assertImagesEqual( s["box"]["catalogue"]["out"], red["out"], ignoreMetadata = True )
			c["catalogue:imageName"] = "Emerald"
			self.assertImagesEqual( s["box"]["catalogue"]["out"], green["out"], ignoreMetadata = True )
			c["catalogue:imageName"] = "output:1"
			self.assertImagesEqual( s["box"]["catalogue"]["out"], red["out"], ignoreMetadata = True )
			c["catalogue:imageName"] = "output:2"
			self.assertImagesEqual( s["box"]["catalogue"]["out"], green["out"], ignoreMetadata = True )

		# And that the old names are now invalid.

		with Gaffer.Context() as c :
			c["catalogue:imageName"] = "Red"
			notFoundText["text"].setValue( 'Catalogue : Unknown Image "Red"' )
			self.assertImagesEqual( s["box"]["catalogue"]["out"], notFoundText["out"], ignoreMetadata = True )

	def testInternalImagePythonType( self ) :

		c = GafferImage.Catalogue()
		c["images"].addChild( c.Image.load( self.imagesPath() / "blurRange.exr" ) )

		for g in Gaffer.GraphComponent.RecursiveRange( c ) :
			self.assertTrue(
				isinstance( g, Gaffer.Plug ) or
				isinstance( g, Gaffer.Node )
			)

	def testImageName( self ) :

		catalogue = GafferImage.Catalogue()
		self.assertEqual( len( catalogue["images"] ), 0 )

		constant = GafferImage.Constant()
		constant["format"].setValue( GafferImage.Format( 64, 64 ) )
		self.sendImage(
			constant["out"],
			catalogue,
			{
				"catalogue:imageName" : "testName",
			}
		)

		self.assertEqual( len( catalogue["images"] ), 1 )
		self.assertEqual( catalogue["images"][0].getName(), "testName" )

		self.sendImage(
			constant["out"],
			catalogue,
			{
				"catalogue:imageName" : "!invalid&^ Name[]",
			}
		)

		self.assertEqual( len( catalogue["images"] ), 2 )
		self.assertEqual( catalogue["images"][0].getName(), "testName" )
		self.assertEqual( catalogue["images"][1].getName(), "_invalid_Name_" )

		self.sendImage(
			constant["out"],
			catalogue,
			{
				"catalogue:imageName" : "5IsntAValidStartingCharacter",
			}
		)

		self.assertEqual( len( catalogue["images"] ), 3 )
		self.assertEqual( catalogue["images"][0].getName(), "testName" )
		self.assertEqual( catalogue["images"][1].getName(), "_invalid_Name_" )
		self.assertEqual( catalogue["images"][2].getName(), "_IsntAValidStartingCharacter" )

	def testGenerateFileName( self ):

		s = Gaffer.ScriptNode()
		s["variables"].addChild( Gaffer.NameValuePlug( "CV", Gaffer.StringPlug( "value", defaultValue = "foo" ) ) )
		catalogue = GafferImage.Catalogue()
		catalogue["directory"].setValue( "${CV}/dir/" )
		s.addChild( catalogue )
		constant1 = GafferImage.Constant()
		constant1["format"].setValue( GafferImage.Format( imath.Box2i( imath.V2i(0), imath.V2i( 100 ) ) ) )

		# Check that two images match only if identical
		f1 = catalogue.generateFileName( constant1["out"] )

		self.assertEqual( f1.parts[:2], ( "foo", "dir" ) )
		self.assertEqual( f1.suffix, ".exr" )

		constant2 = GafferImage.Constant()
		constant2["format"].setValue( GafferImage.Format( imath.Box2i( imath.V2i(0), imath.V2i( 100 ) ) ) )

		f2 = catalogue.generateFileName( constant2["out"] )

		self.assertEqual( f1, f2 )

		constant2["format"]["displayWindow"]["max"]["x"].setValue( 101 )
		f2 = catalogue.generateFileName( constant2["out"] )

		self.assertNotEqual( f1, f2 )

		# Check that two multi-view images match only if all views are identical
		createViews = GafferImage.CreateViews()
		createViews["views"].resize( 2 )
		createViews["views"][0]["value"].setInput( constant1["out"] )
		createViews["views"][0]["name"].setValue( "left" )
		createViews["views"][1]["value"].setInput( constant2["out"] )
		createViews["views"][1]["name"].setValue( "right" )

		f3 = catalogue.generateFileName( createViews["out"] )
		self.assertNotIn( f3, [f1, f2] )

		constant2["format"]["displayWindow"]["max"]["x"].setValue( 102 )
		f4 = catalogue.generateFileName( createViews["out"] )
		self.assertNotIn( f4, [f1, f2, f3] )

		constant1["format"]["displayWindow"]["max"]["x"].setValue( 101 )
		f5 = catalogue.generateFileName( createViews["out"] )
		self.assertNotIn( f5, [f1, f2, f3, f4] )

		constant1["format"]["displayWindow"]["max"]["x"].setValue( 100 )
		constant2["format"]["displayWindow"]["max"]["x"].setValue( 101 )
		f6 = catalogue.generateFileName( createViews["out"] )
		self.assertEqual( f6, f3 )

	def testOutputIndex( self ) :

		images = []
		readers = []
		for i, fileName in enumerate( [ "checker.exr", "blurRange.exr", "noisyRamp.exr", "resamplePatterns.exr" ] ) :
			images.append( GafferImage.Catalogue.Image.load( self.imagesPath() / fileName ) )
			readers.append( GafferImage.ImageReader() )
			readers[-1]["fileName"].setValue( images[-1]["fileName"].getValue() )

		catalogue = GafferImage.Catalogue()

		for image in images :
			catalogue["images"].addChild( image )

		catalogue["images"][0]["outputIndex"].setValue( 4 )
		catalogue["images"][1]["outputIndex"].setValue( 3 )
		catalogue["images"][2]["outputIndex"].setValue( 2 )
		catalogue["images"][3]["outputIndex"].setValue( 1 )

		with Gaffer.Context() as c :
			c["catalogue:imageName"] = "output:1"
			self.assertImagesEqual( readers[3]["out"], catalogue["out"] )
			c["catalogue:imageName"] = "output:2"
			self.assertImagesEqual( readers[2]["out"], catalogue["out"] )
			c["catalogue:imageName"] = "output:3"
			self.assertImagesEqual( readers[1]["out"], catalogue["out"] )
			c["catalogue:imageName"] = "output:4"
			self.assertImagesEqual( readers[0]["out"], catalogue["out"] )

		# Test exclusivity
		catalogue["images"][0]["outputIndex"].setValue( 1 )
		self.assertEqual( catalogue["images"][3]["outputIndex"].getValue(), 0 )

		with Gaffer.Context() as c :
			c["catalogue:imageName"] = "output:1"
			self.assertImagesEqual( readers[0]["out"], catalogue["out"] )

		catalogue["images"][0]["outputIndex"].setValue( 2 )
		self.assertEqual( catalogue["images"][2]["outputIndex"].getValue(), 0 )

		with Gaffer.Context() as c :
			c["catalogue:imageName"] = "output:2"
			self.assertImagesEqual( readers[0]["out"], catalogue["out"] )

		catalogue["images"][1]["outputIndex"].setValue( 2 )
		self.assertEqual( catalogue["images"][0]["outputIndex"].getValue(), 0 )

		notFoundText = GafferImage.Text()
		notFoundText["text"].setValue( 'Catalogue : Unassigned Output 1' )
		notFoundText["size"].setValue( imath.V2i( 100 ) )
		notFoundText["area"].setValue( imath.Box2i( imath.V2i( 0, 0 ), imath.V2i( 1920, 1080 ) ) )
		notFoundText["horizontalAlignment"].setValue( GafferImage.Text.HorizontalAlignment.HorizontalCenter )
		notFoundText["verticalAlignment"].setValue( GafferImage.Text.VerticalAlignment.VerticalCenter )

		with Gaffer.Context() as c :
			c["catalogue:imageName"] = "output:2"
			self.assertImagesEqual( readers[1]["out"], catalogue["out"] )

			c["catalogue:imageName"] = "output:1"
			self.assertImagesEqual( notFoundText["out"], catalogue["out"] )

			notFoundText["text"].setValue( 'Catalogue : Unassigned Output 3' )
			c["catalogue:imageName"] = "output:3"
			self.assertImagesEqual( notFoundText["out"], catalogue["out"] )

	def testYouOnlySaveOnce( self ) :

		# Send a bunch of AOVs to a Catalogue image, but don't
		# close the drivers yet.

		script = Gaffer.ScriptNode()

		script["catalogue"] = GafferImage.Catalogue()
		script["catalogue"]["directory"].setValue( self.temporaryDirectory() / "catalogue" )

		script["constant"] = GafferImage.Constant()
		script["constant"]["format"].setValue( GafferImage.Format( 100, 100 ) )
		script["constant"]["color"].setValue( imath.Color4f( 1, 0, 0, 1 ) )

		drivers = []
		for layer in [ "" ] + [ f"aov{n}" for n in range( 0, 10 ) ] :

			script["constant"]["layer"].setValue( layer )
			drivers.append( self.sendImage( script["constant"]["out"], script["catalogue"], waitForSave = False, close = False ) )

		self.assertEqual( len( script["catalogue"]["images"] ), 1 )

		# Now close the drivers from a background thread, as they will be by a
		# real renderer, and check that the image is saved to file appropriately.

		with GafferTest.ParallelAlgoTest.UIThreadCallHandler() as handler :
			closingThread = threading.Thread( target = lambda : [ d.close( withCallHandler = False ) for d in drivers ] )
			closingThread.start()
			# In practice, renderers close drivers fast enough that all drivers
			# are closed before the first `Display::imageReceivedSignal()` is
			# emitted on the UI thread. Emulate this by waiting for the thread to
			# finish before calling `assertCalled()`
			closingThread.join()
			# We now have a bunch of pending UI thread calls, one for each driver,
			# so handle those. We expect the first call to start the saving process,
			# but that process happens in the background and won't be visible yet.
			for driver in drivers :
				handler.assertCalled()
				self.assertEqual( script["catalogue"]["images"][0]["fileName"].getValue(), "" )
			# The saving process will make one more UI thread call, to make the
			# result of the save visible. Handle that and check we now have an image
			# file.
			handler.assertCalled()
			self.assertNotEqual( script["catalogue"]["images"][0]["fileName"].getValue(), "" )
			self.assertTrue( pathlib.Path( script["catalogue"]["images"][0]["fileName"].getValue() ).is_file() )
			# That should be it. There should definitely not be a whole load more
			# attempts to save the image, so assert that no more UI thread calls are
			# made.
			handler.assertDone()

	def testReorder( self ) :

		for newOrder in [
			[ "blue", "green", "red" ],
			[ "blue", "red", "green" ],
			[ "green", "red", "blue" ],
			[ "green", "blue", "red" ],
			[ "red", "blue", "green" ],
		] :
			with self.subTest( newOrder = newOrder ) :

				# Send 3 images to a Catalogue : red, green, blue

				script = Gaffer.ScriptNode()
				script["catalogue"] = GafferImage.Catalogue()
				script["catalogue"]["directory"].setValue( self.temporaryDirectory() / "catalogue" )

				script["red"] = GafferImage.Constant()
				script["red"]["format"].setValue( GafferImage.Format( 64, 64 ) )
				script["red"]["color"]["r"].setValue( 1 )
				self.sendImage( script["red"]["out"], script["catalogue"] )
				script["catalogue"]["images"][-1].setName( "red" )

				script["green"] = GafferImage.Constant()
				script["green"]["format"].setValue( GafferImage.Format( 64, 64 ) )
				script["green"]["color"]["g"].setValue( 1 )
				self.sendImage( script["green"]["out"], script["catalogue"] )
				script["catalogue"]["images"][-1].setName( "green" )

				script["blue"] = GafferImage.Constant()
				script["blue"]["format"].setValue( GafferImage.Format( 64, 64 ) )
				script["blue"]["color"]["b"].setValue( 1 )
				self.sendImage( script["blue"]["out"], script["catalogue"] )
				script["catalogue"]["images"][-1].setName( "blue" )

				# Check it worked

				def assertPreconditions() :

					self.assertEqual( len( script["catalogue"]["images"] ), 3 )
					self.assertEqual( script["catalogue"]["images"][0].getName(), "red" )
					self.assertEqual( script["catalogue"]["images"][1].getName(), "green" )
					self.assertEqual( script["catalogue"]["images"][2].getName(), "blue" )

					script["catalogue"]["imageIndex"].setValue( 0 )
					self.assertImagesEqual( script["catalogue"]["out"], script["red"]["out"], ignoreMetadata = True )
					script["catalogue"]["imageIndex"].setValue( 1 )
					self.assertImagesEqual( script["catalogue"]["out"], script["green"]["out"], ignoreMetadata = True )
					script["catalogue"]["imageIndex"].setValue( 2 )
					self.assertImagesEqual( script["catalogue"]["out"], script["blue"]["out"], ignoreMetadata = True )

					with Gaffer.Context( script.context() ) as c :
						for name in script["catalogue"]["images"].keys() :
							c["catalogue:imageName"] = name
							self.assertImagesEqual( script["catalogue"]["out"], script[name]["out"], ignoreMetadata = True )

				assertPreconditions()

				# Reorder the images

				with Gaffer.UndoScope( script ) :
					script["catalogue"]["images"].reorderChildren( [
						script["catalogue"]["images"][x] for x in newOrder
					] )

				# Check it worked

				def assertPostConditions() :

					self.assertEqual( len( script["catalogue"]["images"] ), 3 )
					self.assertEqual( script["catalogue"]["images"].keys(), newOrder )

					for index, name in enumerate( script["catalogue"]["images"].keys() ) :
						script["catalogue"]["imageIndex"].setValue( index )
						self.assertImagesEqual( script["catalogue"]["out"], script[name]["out"], ignoreMetadata = True )

					with Gaffer.Context( script.context() ) as c :
						for name in script["catalogue"]["images"].keys() :
							c["catalogue:imageName"] = name
							self.assertImagesEqual( script["catalogue"]["out"], script[name]["out"], ignoreMetadata = True )

				assertPostConditions()

				# Check that undo and redo work

				script.undo()
				assertPreconditions()

				script.redo()
				assertPostConditions()

				script.undo()
				assertPreconditions()

	def testImageNames( self ) :

		def assertImageNames( catalogue ) :

			self.assertEqual(
				catalogue["imageNames"].getValue(),
				IECore.StringVectorData( catalogue["images"].keys() )
			)

		catalogue = GafferImage.Catalogue()
		plugDirtiedSlot = GafferTest.CapturingSlot( catalogue.plugDirtiedSignal() )
		assertImageNames( catalogue )

		catalogue["images"].addChild( catalogue.Image.load( self.imagesPath() / "blurRange.exr" ) )
		self.assertIn( catalogue["imageNames"], { x[0] for x in plugDirtiedSlot } )
		assertImageNames( catalogue )

		del plugDirtiedSlot[:]
		catalogue["images"].addChild( catalogue.Image.load( self.imagesPath() / "blurRange.exr" ) )
		self.assertIn( catalogue["imageNames"], { x[0] for x in plugDirtiedSlot } )
		assertImageNames( catalogue )

		del plugDirtiedSlot[:]
		catalogue["images"][0].setName( "newName" )
		self.assertIn( catalogue["imageNames"], { x[0] for x in plugDirtiedSlot } )
		assertImageNames( catalogue )

		del plugDirtiedSlot[:]
		catalogue["images"].reorderChildren( reversed( catalogue["images"].children() ) )
		self.assertIn( catalogue["imageNames"], { x[0] for x in plugDirtiedSlot } )
		assertImageNames( catalogue )

if __name__ == "__main__":
	unittest.main()
