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
import shutil
import unittest
import six
import imath

import IECore

import Gaffer
import GafferTest
import GafferImage
import GafferImageTest

class ImageReaderTest( GafferImageTest.ImageTestCase ) :

	fileName = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/circles.exr" )
	colorSpaceFileName = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/circles_as_cineon.exr" )
	offsetDataWindowFileName = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/rgb.100x100.exr" )
	jpgFileName = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/circles.jpg" )

	def setUp( self ) :

		GafferImageTest.ImageTestCase.setUp( self )
		self.__defaultColorSpaceFunction = GafferImage.ImageReader.getDefaultColorSpaceFunction()

	def tearDown( self ) :

		GafferImageTest.ImageTestCase.tearDown( self )
		GafferImage.ImageReader.setDefaultColorSpaceFunction( self.__defaultColorSpaceFunction )

	def test( self ) :

		n = GafferImage.ImageReader()
		n["fileName"].setValue( self.fileName )

		oiio = GafferImage.OpenImageIOReader()
		oiio["fileName"].setValue( self.fileName )

		self.assertEqual( n["out"]["format"].getValue(), oiio["out"]["format"].getValue() )
		self.assertEqual( n["out"]["dataWindow"].getValue(), oiio["out"]["dataWindow"].getValue() )
		self.assertEqual( n["out"]["metadata"].getValue(), oiio["out"]["metadata"].getValue() )
		self.assertEqual( n["out"]["deep"].getValue(), oiio["out"]["deep"].getValue() )
		self.assertEqual( n["out"]["channelNames"].getValue(), oiio["out"]["channelNames"].getValue() )
		self.assertEqual( n["out"].sampleOffsets( imath.V2i( 0 ) ), oiio["out"].sampleOffsets( imath.V2i( 0 ) ) )
		self.assertEqual( n["out"].channelData( "R", imath.V2i( 0 ) ), oiio["out"].channelData( "R", imath.V2i( 0 ) ) )
		self.assertImagesEqual( n["out"], oiio["out"] )

	def testUnspecifiedFilename( self ) :

		n = GafferImage.ImageReader()
		n["out"]["channelNames"].getValue()
		self.assertTrue( GafferImage.BufferAlgo.empty( n["out"]['dataWindow'].getValue() ) )


	def testChannelDataHashes( self ) :
		# Test that two tiles within the same image have different hashes.
		n = GafferImage.ImageReader()
		n["fileName"].setValue( self.fileName )
		h1 = n["out"].channelData( "R", imath.V2i( 0 ) ).hash()
		h2 = n["out"].channelData( "R", imath.V2i( GafferImage.ImagePlug().tileSize() ) ).hash()

		self.assertNotEqual( h1, h2 )

	def testColorSpaceOverride( self ) :

		exrReader = GafferImage.ImageReader()
		exrReader["fileName"].setValue( self.fileName )
		exrReader["colorSpace"].setValue( "Cineon" )

		colorSpaceOverrideReader = GafferImage.ImageReader()
		colorSpaceOverrideReader["fileName"].setValue( self.colorSpaceFileName )

		exrImage = exrReader["out"]
		colorSpaceOverrideImage = colorSpaceOverrideReader["out"]

		self.assertImagesEqual( colorSpaceOverrideImage, exrImage, ignoreMetadata = True, maxDifference = 0.005 )

	def testJpgRead( self ) :

		exrReader = GafferImage.ImageReader()
		exrReader["fileName"].setValue( self.fileName )

		jpgReader = GafferImage.ImageReader()
		jpgReader["fileName"].setValue( self.jpgFileName )

		self.assertImagesEqual( exrReader["out"], jpgReader["out"], ignoreMetadata = True, maxDifference = 0.001 )

	def testSupportedExtensions( self ) :

		self.assertEqual( GafferImage.ImageReader.supportedExtensions(), GafferImage.OpenImageIOReader.supportedExtensions() )

	def testFileRefresh( self ) :

		testFile = self.temporaryDirectory() + "/refresh.exr"
		shutil.copyfile( self.fileName, testFile )

		reader = GafferImage.ImageReader()
		reader["fileName"].setValue( testFile )
		image1 = GafferImage.ImageAlgo.image( reader["out"] )

		# even though we've change the image on disk, gaffer will
		# still have the old one in its cache.
		shutil.copyfile( self.jpgFileName, testFile )
		self.assertEqual( GafferImage.ImageAlgo.image( reader["out"] ), image1 )

		# until we force a refresh
		reader["refreshCount"].setValue( reader["refreshCount"].getValue() + 1 )
		self.assertNotEqual( GafferImage.ImageAlgo.image( reader["out"] ), image1 )

	def testNonexistentFiles( self ) :

		reader = GafferImage.ImageReader()
		reader["fileName"].setValue( "wellIDontExist.exr" )

		six.assertRaisesRegex( self, RuntimeError, ".*wellIDontExist.exr.*", reader["out"]["format"].getValue )
		six.assertRaisesRegex( self, RuntimeError, ".*wellIDontExist.exr.*", reader["out"]["dataWindow"].getValue )
		six.assertRaisesRegex( self, RuntimeError, ".*wellIDontExist.exr.*", reader["out"]["metadata"].getValue )
		six.assertRaisesRegex( self, RuntimeError, ".*wellIDontExist.exr.*", reader["out"]["channelNames"].getValue )
		six.assertRaisesRegex( self, RuntimeError, ".*wellIDontExist.exr.*", reader["out"].channelData, "R", imath.V2i( 0 ) )
		six.assertRaisesRegex( self, RuntimeError, ".*wellIDontExist.exr.*", GafferImage.ImageAlgo.image, reader["out"] )

	def testMissingFrameMode( self ) :

		testSequence = IECore.FileSequence( self.temporaryDirectory() + "/incompleteSequence.####.exr" )
		shutil.copyfile( self.fileName, testSequence.fileNameForFrame( 1 ) )
		shutil.copyfile( self.offsetDataWindowFileName, testSequence.fileNameForFrame( 3 ) )

		reader = GafferImage.ImageReader()
		reader["fileName"].setValue( testSequence.fileName )

		oiio = GafferImage.OpenImageIOReader()
		oiio["fileName"].setValue( testSequence.fileName )

		def assertMatch() :

			self.assertEqual( reader["out"]["format"].getValue(), oiio["out"]["format"].getValue() )
			self.assertEqual( reader["out"]["dataWindow"].getValue(), oiio["out"]["dataWindow"].getValue() )
			self.assertEqual( reader["out"]["metadata"].getValue(), oiio["out"]["metadata"].getValue() )
			self.assertEqual( reader["out"]["channelNames"].getValue(), oiio["out"]["channelNames"].getValue() )

			# It is only valid to query the data inside the data window
			if not GafferImage.BufferAlgo.empty( reader["out"]["dataWindow"].getValue() ):
				self.assertEqual( reader["out"].channelData( "R", imath.V2i( 0 ) ), oiio["out"].channelData( "R", imath.V2i( 0 ) ) )
			self.assertImagesEqual( reader["out"], oiio["out"] )

		context = Gaffer.Context()

		# set to a missing frame
		context.setFrame( 2 )

		# everything throws
		reader["missingFrameMode"].setValue( GafferImage.ImageReader.MissingFrameMode.Error )
		with context :
			six.assertRaisesRegex( self, RuntimeError, ".*incompleteSequence.*.exr.*", reader["out"]["format"].getValue )
			six.assertRaisesRegex( self, RuntimeError, ".*incompleteSequence.*.exr.*", reader["out"]["dataWindow"].getValue )
			six.assertRaisesRegex( self, RuntimeError, ".*incompleteSequence.*.exr.*", reader["out"]["metadata"].getValue )
			six.assertRaisesRegex( self, RuntimeError, ".*incompleteSequence.*.exr.*", reader["out"]["channelNames"].getValue )
			six.assertRaisesRegex( self, RuntimeError, ".*incompleteSequence.*.exr.*", reader["out"].channelData, "R", imath.V2i( 0 ) )
			six.assertRaisesRegex( self, RuntimeError, ".*incompleteSequence.*.exr.*", GafferImage.ImageAlgo.image, reader["out"] )

		# Hold mode matches OpenImageIOReader
		reader["missingFrameMode"].setValue( GafferImage.ImageReader.MissingFrameMode.Hold )
		oiio["missingFrameMode"].setValue( GafferImage.OpenImageIOReader.MissingFrameMode.Hold )
		with context :
			assertMatch()

		# Black mode matches OpenImageIOReader
		reader["missingFrameMode"].setValue( GafferImage.ImageReader.MissingFrameMode.Black )
		oiio["missingFrameMode"].setValue( GafferImage.OpenImageIOReader.MissingFrameMode.Black )
		with context :
			assertMatch()

		# set to a different missing frame
		context.setFrame( 4 )

		# Hold mode matches OpenImageIOReader
		reader["missingFrameMode"].setValue( GafferImage.ImageReader.MissingFrameMode.Hold )
		oiio["missingFrameMode"].setValue( GafferImage.OpenImageIOReader.MissingFrameMode.Hold )
		with context :
			assertMatch()

		# Black mode matches OpenImageIOReader
		reader["missingFrameMode"].setValue( GafferImage.ImageReader.MissingFrameMode.Black )
		oiio["missingFrameMode"].setValue( GafferImage.OpenImageIOReader.MissingFrameMode.Black )
		with context :
			assertMatch()

		# set to a missing frame before the start of the sequence
		context.setFrame( 0 )

		# Hold mode matches OpenImageIOReader
		reader["missingFrameMode"].setValue( GafferImage.ImageReader.MissingFrameMode.Hold )
		oiio["missingFrameMode"].setValue( GafferImage.OpenImageIOReader.MissingFrameMode.Hold )
		with context :
			assertMatch()

		# Black mode matches OpenImageIOReader
		reader["missingFrameMode"].setValue( GafferImage.ImageReader.MissingFrameMode.Black )
		oiio["missingFrameMode"].setValue( GafferImage.OpenImageIOReader.MissingFrameMode.Black )
		with context :
			assertMatch()

		# explicit fileNames do not support MissingFrameMode
		reader["fileName"].setValue( testSequence.fileNameForFrame( 0 ) )
		reader["missingFrameMode"].setValue( GafferImage.OpenImageIOReader.MissingFrameMode.Hold )
		with context :
			six.assertRaisesRegex( self, RuntimeError, ".*incompleteSequence.*.exr.*", GafferImage.ImageAlgo.image, reader["out"] )
			six.assertRaisesRegex( self, RuntimeError, ".*incompleteSequence.*.exr.*", reader["out"]["format"].getValue )
			six.assertRaisesRegex( self, RuntimeError, ".*incompleteSequence.*.exr.*", reader["out"]["dataWindow"].getValue )
			six.assertRaisesRegex( self, RuntimeError, ".*incompleteSequence.*.exr.*", reader["out"]["metadata"].getValue )
			six.assertRaisesRegex( self, RuntimeError, ".*incompleteSequence.*.exr.*", reader["out"]["channelNames"].getValue )
			six.assertRaisesRegex( self, RuntimeError, ".*incompleteSequence.*.exr.*", reader["out"].channelData, "R", imath.V2i( 0 ) )

		reader["missingFrameMode"].setValue( GafferImage.OpenImageIOReader.MissingFrameMode.Black )
		oiio["missingFrameMode"].setValue( GafferImage.OpenImageIOReader.MissingFrameMode.Black )
		with context :
			six.assertRaisesRegex( self, RuntimeError, ".*incompleteSequence.*.exr.*", GafferImage.ImageAlgo.image, reader["out"] )
			six.assertRaisesRegex( self, RuntimeError, ".*incompleteSequence.*.exr.*", reader["out"]["format"].getValue )
			self.assertEqual( reader["out"]["dataWindow"].getValue(), oiio["out"]["dataWindow"].getValue() )
			self.assertEqual( reader["out"]["metadata"].getValue(), oiio["out"]["metadata"].getValue() )
			self.assertEqual( reader["out"]["channelNames"].getValue(), oiio["out"]["channelNames"].getValue() )
			self.assertTrue( GafferImage.BufferAlgo.empty( reader["out"]['dataWindow'].getValue() ) )
			self.assertTrue( GafferImage.BufferAlgo.empty( oiio["out"]['dataWindow'].getValue() ) )

	def testFrameRangeMask( self ) :

		testSequence = IECore.FileSequence( self.temporaryDirectory() + "/incompleteSequence.####.exr" )
		shutil.copyfile( self.fileName, testSequence.fileNameForFrame( 1 ) )
		shutil.copyfile( self.fileName, testSequence.fileNameForFrame( 3 ) )
		shutil.copyfile( self.offsetDataWindowFileName, testSequence.fileNameForFrame( 5 ) )
		shutil.copyfile( self.offsetDataWindowFileName, testSequence.fileNameForFrame( 7 ) )

		reader = GafferImage.ImageReader()
		reader["fileName"].setValue( testSequence.fileName )
		reader["missingFrameMode"].setValue( GafferImage.ImageReader.MissingFrameMode.Hold )

		oiio = GafferImage.OpenImageIOReader()
		oiio["fileName"].setValue( testSequence.fileName )
		oiio["missingFrameMode"].setValue( GafferImage.ImageReader.MissingFrameMode.Hold )

		context = Gaffer.Context()

		# make sure the tile we're comparing isn't black
		# so we can tell if BlackOutside is working.
		blackTile = IECore.FloatVectorData( [ 0 ] * GafferImage.ImagePlug.tileSize() * GafferImage.ImagePlug.tileSize() )
		with context :
			for i in range( 1, 11 ) :
				context.setFrame( i )
				self.assertNotEqual( reader["out"].channelData( "R", imath.V2i( 0 ) ), blackTile )

		def assertBlack() :

			# format and data window still match
			self.assertEqual( reader["out"]["format"].getValue(), oiio["out"]["format"].getValue() )
			self.assertEqual( reader["out"]["dataWindow"].getValue(), oiio["out"]["dataWindow"].getValue() )
			self.assertNotEqual( GafferImage.ImageAlgo.image( reader["out"] ), GafferImage.ImageAlgo.image( oiio["out"] ) )
			# the metadata and channel names are at the defaults
			self.assertEqual( reader["out"]["metadata"].getValue(), reader["out"]["metadata"].defaultValue() )
			self.assertEqual( reader["out"]["channelNames"].getValue(), reader["out"]["channelNames"].defaultValue() )
			# channel data is black
			self.assertEqual( reader["out"].channelData( "R", imath.V2i( 0 ) ), blackTile )

		def assertMatch() :

			self.assertEqual( reader["out"]["format"].getValue(), oiio["out"]["format"].getValue() )
			self.assertEqual( reader["out"]["dataWindow"].getValue(), oiio["out"]["dataWindow"].getValue() )
			self.assertEqual( reader["out"]["metadata"].getValue(), oiio["out"]["metadata"].getValue() )
			self.assertEqual( reader["out"]["channelNames"].getValue(), oiio["out"]["channelNames"].getValue() )
			self.assertEqual( reader["out"].channelData( "R", imath.V2i( 0 ) ), oiio["out"].channelData( "R", imath.V2i( 0 ) ) )
			self.assertImagesEqual( reader["out"], oiio["out"] )

		def assertHold( holdFrame ) :

			context = Gaffer.Context()
			context.setFrame( holdFrame )
			with context :
				holdImage = GafferImage.ImageAlgo.image( reader["out"] )
				holdFormat = reader["out"]["format"].getValue()
				holdDataWindow = reader["out"]["dataWindow"].getValue()
				holdMetadata = reader["out"]["metadata"].getValue()
				holdChannelNames = reader["out"]["channelNames"].getValue()
				holdTile = reader["out"].channelData( "R", imath.V2i( 0 ) )

			self.assertEqual( reader["out"]["format"].getValue(), holdFormat )
			self.assertEqual( reader["out"]["dataWindow"].getValue(), holdDataWindow )
			self.assertEqual( reader["out"]["metadata"].getValue(), holdMetadata )
			self.assertEqual( reader["out"]["channelNames"].getValue(), holdChannelNames )
			self.assertEqual( reader["out"].channelData( "R", imath.V2i( 0 ) ), holdTile )
			self.assertEqual( GafferImage.ImageAlgo.image( reader["out"] ), holdImage )

		reader["start"]["frame"].setValue( 4 )
		reader["end"]["frame"].setValue( 7 )

		# frame 0 errors, match from 1-10
		reader["start"]["mode"].setValue( GafferImage.ImageReader.FrameMaskMode.None )
		reader["end"]["mode"].setValue( GafferImage.ImageReader.FrameMaskMode.None )
		with context :

			for i in range( 0, 11 ) :
				context.setFrame( i )
				assertMatch()

		# black from 0-3, match from 4-10
		reader["start"]["mode"].setValue( GafferImage.ImageReader.FrameMaskMode.BlackOutside )
		with context :

			for i in range( 0, 4 ) :
				context.setFrame( i )
				assertBlack()

			for i in range( 4, 11 ) :
				context.setFrame( i )
				assertMatch()

		# black from 0-3, match from 4-7, black from 8-10
		reader["end"]["mode"].setValue( GafferImage.ImageReader.FrameMaskMode.BlackOutside )
		with context :

			for i in range( 0, 4 ) :
				context.setFrame( i )
				assertBlack()

			for i in range( 4, 8 ) :
				context.setFrame( i )
				assertMatch()

			for i in range( 8, 11 ) :
				context.setFrame( i )
				assertBlack()

		# hold frame 4 from 0-3, match from 4-7, black from 8-10
		reader["start"]["mode"].setValue( GafferImage.ImageReader.FrameMaskMode.ClampToFrame )
		with context :

			for i in range( 0, 4 ) :
				context.setFrame( i )
				assertHold( 4 )

			for i in range( 4, 8 ) :
				context.setFrame( i )
				assertMatch()

			for i in range( 8, 11 ) :
				context.setFrame( i )
				assertBlack()

		# hold frame 4 from 0-3, match from 4-7, hold frame 7 from 8-10
		reader["end"]["mode"].setValue( GafferImage.ImageReader.FrameMaskMode.ClampToFrame )
		with context :

			for i in range( 0, 4 ) :
				context.setFrame( i )
				assertHold( 4 )

			for i in range( 4, 8 ) :
				context.setFrame( i )
				assertMatch()

			for i in range( 8, 11 ) :
				context.setFrame( i )
				assertHold( 7 )

	def testDefaultColorSpaceFunctionArguments( self ) :

		# Make a network to write and read an image
		# in various formats.

		c = GafferImage.Constant()
		c["format"].setValue( GafferImage.Format( 64, 64 ) )

		w = GafferImage.ImageWriter()
		w["in"].setInput( c["out"] )

		r = GafferImage.ImageReader()
		r["fileName"].setInput( w["fileName"] )

		# Register a custom colorspace function that
		# just captures its arguments.

		capturedArguments = {}
		def f( fileName, fileFormat, dataType, metadata ) :

			capturedArguments.update(
				{
					"fileName" : fileName,
					"fileFormat" : fileFormat,
					"dataType" : dataType,
					"metadata" : metadata,
				}
			)
			return "linear"

		GafferImage.ImageReader.setDefaultColorSpaceFunction( f )

		# Verify that the correct arguments are passed for
		# a variety of fileNames and dataTypes.

		for ext, fileFormat, dataType in [
			( "exr", "openexr", "half" ),
			( "dpx", "dpx", "uint12" ),
			( "TIFF", "tiff", "float" ),
			( "tif", "tiff", "uint32" ),
		] :

			w["fileName"].setValue( "{0}/{1}.{2}".format( self.temporaryDirectory(), dataType, ext ) )
			w[fileFormat]["dataType"].setValue( dataType )
			w.execute()

			capturedArguments.clear()
			r["out"].channelData( "R", imath.V2i( 0 ) ) # Triggers call to color space function

			self.assertEqual( len( capturedArguments ), 4 )
			self.assertEqual( capturedArguments["fileName"], w["fileName"].getValue() )
			self.assertEqual( capturedArguments["fileFormat"], fileFormat )
			self.assertEqual( capturedArguments["dataType"], dataType )
			self.assertEqual( capturedArguments["metadata"], r["out"]["metadata"].getValue() )

	def testDisabling( self ) :

		reader = GafferImage.ImageReader()
		reader["fileName"].setValue( self.fileName )
		reader["enabled"].setValue( False )

		constant = GafferImage.Constant()
		constant["enabled"].setValue( False )

		self.assertImagesEqual( reader["out"], constant["out"] )

if __name__ == "__main__":
	unittest.main()
