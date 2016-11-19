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

import IECore

import Gaffer
import GafferTest
import GafferImage
import GafferImageTest

class ImageReaderTest( GafferImageTest.ImageTestCase ) :

	fileName = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/circles.exr" )
	offsetDataWindowFileName = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/rgb.100x100.exr" )
	jpgFileName = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/circles.jpg" )

	def test( self ) :

		n = GafferImage.ImageReader()
		n["fileName"].setValue( self.fileName )

		oiio = GafferImage.OpenImageIOReader()
		oiio["fileName"].setValue( self.fileName )

		self.assertEqual( n["out"]["format"].getValue(), oiio["out"]["format"].getValue() )
		self.assertEqual( n["out"]["dataWindow"].getValue(), oiio["out"]["dataWindow"].getValue() )
		self.assertEqual( n["out"]["metadata"].getValue(), oiio["out"]["metadata"].getValue() )
		self.assertEqual( n["out"]["deepState"].getValue(), oiio["out"]["deepState"].getValue() )
		self.assertEqual( n["out"]["channelNames"].getValue(), oiio["out"]["channelNames"].getValue() )
		self.assertEqual( n["out"].sampleOffsets( IECore.V2i( 0 ) ), oiio["out"].sampleOffsets( IECore.V2i( 0 ) ) )
		self.assertEqual( n["out"].channelData( "R", IECore.V2i( 0 ) ),oiio["out"].channelData( "R", IECore.V2i( 0 ) ) )
		self.assertEqual( n["out"].image(), oiio["out"].image() )

	def testUnspecifiedFilename( self ) :

		n = GafferImage.ImageReader()
		n["out"]["channelNames"].getValue()
		n["out"].channelData( "R", IECore.V2i( 0 ) )

	def testChannelDataHashes( self ) :
		# Test that two tiles within the same image have different hashes.
		n = GafferImage.ImageReader()
		n["fileName"].setValue( self.fileName )
		h1 = n["out"].channelData( "R", IECore.V2i( 0 ) ).hash()
		h2 = n["out"].channelData( "R", IECore.V2i( GafferImage.ImagePlug().tileSize() ) ).hash()

		self.assertNotEqual( h1, h2 )

	def testJpgRead( self ) :

		exrReader = GafferImage.ImageReader()
		exrReader["fileName"].setValue( self.fileName )

		jpgReader = GafferImage.ImageReader()
		jpgReader["fileName"].setValue( self.jpgFileName )

		exrImage = exrReader["out"].image()
		jpgImage = jpgReader["out"].image()

		exrImage.blindData().clear()
		jpgImage.blindData().clear()

		imageDiffOp = IECore.ImageDiffOp()
		res = imageDiffOp(
			imageA = exrImage,
			imageB = jpgImage,
		)
		self.assertFalse( res.value )

	def testSupportedExtensions( self ) :

		self.assertEqual( GafferImage.ImageReader.supportedExtensions(), GafferImage.OpenImageIOReader.supportedExtensions() )

	def testFileRefresh( self ) :

		testFile = self.temporaryDirectory() + "/refresh.exr"
		shutil.copyfile( self.fileName, testFile )

		reader = GafferImage.ImageReader()
		reader["fileName"].setValue( testFile )
		image1 = reader["out"].image()

		# even though we've change the image on disk, gaffer will
		# still have the old one in its cache.
		shutil.copyfile( self.jpgFileName, testFile )
		self.assertEqual( reader["out"].image(), image1 )

		# until we force a refresh
		reader["refreshCount"].setValue( reader["refreshCount"].getValue() + 1 )
		self.assertNotEqual( reader["out"].image(), image1 )

	def testNonexistentFiles( self ) :

		reader = GafferImage.ImageReader()
		reader["fileName"].setValue( "wellIDontExist.exr" )

		self.assertRaisesRegexp( RuntimeError, ".*wellIDontExist.exr.*", reader["out"].image )
		self.assertRaisesRegexp( RuntimeError, ".*wellIDontExist.exr.*", reader["out"]["format"].getValue )
		self.assertRaisesRegexp( RuntimeError, ".*wellIDontExist.exr.*", reader["out"]["dataWindow"].getValue )
		self.assertRaisesRegexp( RuntimeError, ".*wellIDontExist.exr.*", reader["out"]["metadata"].getValue )
		self.assertRaisesRegexp( RuntimeError, ".*wellIDontExist.exr.*", reader["out"]["channelNames"].getValue )
		self.assertRaisesRegexp( RuntimeError, ".*wellIDontExist.exr.*", reader["out"].channelData, "R", IECore.V2i( 0 ) )

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
			self.assertEqual( reader["out"].channelData( "R", IECore.V2i( 0 ) ), oiio["out"].channelData( "R", IECore.V2i( 0 ) ) )
			self.assertEqual( reader["out"].image(), oiio["out"].image() )

		context = Gaffer.Context()

		# set to a missing frame
		context.setFrame( 2 )

		# everything throws
		reader["missingFrameMode"].setValue( GafferImage.ImageReader.MissingFrameMode.Error )
		with context :
			self.assertRaisesRegexp( RuntimeError, ".*incompleteSequence.*.exr.*", reader["out"].image )
			self.assertRaisesRegexp( RuntimeError, ".*incompleteSequence.*.exr.*", reader["out"]["format"].getValue )
			self.assertRaisesRegexp( RuntimeError, ".*incompleteSequence.*.exr.*", reader["out"]["dataWindow"].getValue )
			self.assertRaisesRegexp( RuntimeError, ".*incompleteSequence.*.exr.*", reader["out"]["metadata"].getValue )
			self.assertRaisesRegexp( RuntimeError, ".*incompleteSequence.*.exr.*", reader["out"]["channelNames"].getValue )
			self.assertRaisesRegexp( RuntimeError, ".*incompleteSequence.*.exr.*", reader["out"].channelData, "R", IECore.V2i( 0 ) )

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
			self.assertRaisesRegexp( RuntimeError, ".*incompleteSequence.*.exr.*", reader["out"].image )
			self.assertRaisesRegexp( RuntimeError, ".*incompleteSequence.*.exr.*", reader["out"]["format"].getValue )
			self.assertRaisesRegexp( RuntimeError, ".*incompleteSequence.*.exr.*", reader["out"]["dataWindow"].getValue )
			self.assertRaisesRegexp( RuntimeError, ".*incompleteSequence.*.exr.*", reader["out"]["metadata"].getValue )
			self.assertRaisesRegexp( RuntimeError, ".*incompleteSequence.*.exr.*", reader["out"]["channelNames"].getValue )
			self.assertRaisesRegexp( RuntimeError, ".*incompleteSequence.*.exr.*", reader["out"].channelData, "R", IECore.V2i( 0 ) )

		reader["missingFrameMode"].setValue( GafferImage.OpenImageIOReader.MissingFrameMode.Black )
		oiio["missingFrameMode"].setValue( GafferImage.OpenImageIOReader.MissingFrameMode.Black )
		with context :
			self.assertRaisesRegexp( RuntimeError, ".*incompleteSequence.*.exr.*", reader["out"].image )
			self.assertRaisesRegexp( RuntimeError, ".*incompleteSequence.*.exr.*", reader["out"]["format"].getValue )
			self.assertEqual( reader["out"]["dataWindow"].getValue(), oiio["out"]["dataWindow"].getValue() )
			self.assertEqual( reader["out"]["metadata"].getValue(), oiio["out"]["metadata"].getValue() )
			self.assertEqual( reader["out"]["channelNames"].getValue(), oiio["out"]["channelNames"].getValue() )
			self.assertEqual( reader["out"].channelData( "R", IECore.V2i( 0 ) ), oiio["out"].channelData( "R", IECore.V2i( 0 ) ) )

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
				self.assertNotEqual( reader["out"].channelData( "R", IECore.V2i( 0 ) ), blackTile )

		def assertBlack() :

			# format and data window still match
			self.assertEqual( reader["out"]["format"].getValue(), oiio["out"]["format"].getValue() )
			self.assertEqual( reader["out"]["dataWindow"].getValue(), oiio["out"]["dataWindow"].getValue() )
			self.assertNotEqual( reader["out"].image(), oiio["out"].image() )
			# the metadata and channel names are at the defaults
			self.assertEqual( reader["out"]["metadata"].getValue(), reader["out"]["metadata"].defaultValue() )
			self.assertEqual( reader["out"]["channelNames"].getValue(), reader["out"]["channelNames"].defaultValue() )
			# channel data is black
			self.assertEqual( reader["out"].channelData( "R", IECore.V2i( 0 ) ), blackTile )

		def assertMatch() :

			self.assertEqual( reader["out"]["format"].getValue(), oiio["out"]["format"].getValue() )
			self.assertEqual( reader["out"]["dataWindow"].getValue(), oiio["out"]["dataWindow"].getValue() )
			self.assertEqual( reader["out"]["metadata"].getValue(), oiio["out"]["metadata"].getValue() )
			self.assertEqual( reader["out"]["channelNames"].getValue(), oiio["out"]["channelNames"].getValue() )
			self.assertEqual( reader["out"].channelData( "R", IECore.V2i( 0 ) ), oiio["out"].channelData( "R", IECore.V2i( 0 ) ) )
			self.assertEqual( reader["out"].image(), oiio["out"].image() )

		def assertHold( holdFrame ) :

			context = Gaffer.Context()
			context.setFrame( holdFrame )
			with context :
				holdImage = reader["out"].image()
				holdFormat = reader["out"]["format"].getValue()
				holdDataWindow = reader["out"]["dataWindow"].getValue()
				holdMetadata = reader["out"]["metadata"].getValue()
				holdChannelNames = reader["out"]["channelNames"].getValue()
				holdTile = reader["out"].channelData( "R", IECore.V2i( 0 ) )

			self.assertEqual( reader["out"]["format"].getValue(), holdFormat )
			self.assertEqual( reader["out"]["dataWindow"].getValue(), holdDataWindow )
			self.assertEqual( reader["out"]["metadata"].getValue(), holdMetadata )
			self.assertEqual( reader["out"]["channelNames"].getValue(), holdChannelNames )
			self.assertEqual( reader["out"].channelData( "R", IECore.V2i( 0 ) ), holdTile )
			self.assertEqual( reader["out"].image(), holdImage )

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

if __name__ == "__main__":
	unittest.main()
