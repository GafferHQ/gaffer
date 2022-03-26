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
	largeFileName = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/colorbars_max_clamp.exr" )

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
		n["fileName"].setValue( self.largeFileName )
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
		reader["start"]["mode"].setValue( GafferImage.ImageReader.FrameMaskMode.None_ )
		reader["end"]["mode"].setValue( GafferImage.ImageReader.FrameMaskMode.None_ )
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
			w["task"].execute()

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

	def testLayerNames( self ):

		reader = GafferImage.ImageReader()
		def validateChannels( channels ):
			self.assertEqual( [ i for i in reader["out"].channelNames() ], [ i[0] for i in channels ] )
			for name, value in channels:
				self.assertAlmostEqual( reader["out"].channelData( name, imath.V2i( 0 ) )[0], value, places = 3 )

		reader["fileName"].setValue( "${GAFFER_ROOT}/python/GafferImageTest/images/imitateProductionLayers1.exr" )

		reader["channelInterpretation"].setValue( GafferImage.ImageReader.ChannelInterpretation.Default )
		validateChannels( [ ( "R", 0.1 ), ( "G", 0.2 ), ( "B", 0.3 ), ( "character.R", 0.4 ), ( "character.G", 0.5 ), ( "character.B", 0.6 ) ] )
		reader["channelInterpretation"].setValue( GafferImage.ImageReader.ChannelInterpretation.Legacy )
		validateChannels( [ ( "rgba.main.R", 0.1 ), ( "rgba.main.G", 0.2 ), ( "rgba.main.B", 0.3 ), ( "character.main.red", 0.4 ), ( "character.main.green", 0.5 ), ( "character.main.blue", 0.6 ) ] )
		reader["channelInterpretation"].setValue( GafferImage.ImageReader.ChannelInterpretation.Specification )
		validateChannels( [ ( "R", 0.1 ), ( "G", 0.2 ), ( "B", 0.3 ), ( "red", 0.4 ), ( "green", 0.5 ), ( "blue", 0.6 ) ] )

		reader["fileName"].setValue( "${GAFFER_ROOT}/python/GafferImageTest/images/imitateProductionLayers2.exr" )
		reader["channelInterpretation"].setValue( GafferImage.ImageReader.ChannelInterpretation.Default )
		validateChannels( [ ( "R", 0.1 ), ( "G", 0.2 ), ( "B", 0.3 ), ( "Z", 0.4 ) ] )
		reader["channelInterpretation"].setValue( GafferImage.ImageReader.ChannelInterpretation.Legacy )
		validateChannels( [ ( "rgba_main.R", 0.1 ), ( "rgba_main.G", 0.2 ), ( "rgba_main.B", 0.3 ), ( "depth_main.depth.Z", 0.4 ) ] )
		reader["channelInterpretation"].setValue( GafferImage.ImageReader.ChannelInterpretation.Specification )
		validateChannels( [ ( "R", 0.1 ), ( "G", 0.2 ), ( "B", 0.3 ), ( "depth.Z", 0.4 ) ] )

		# The EXR spec allows enormous flexibility in the naming of parts, since the part name is not used
		# at all.  We can't handle all of this with our heuristics - if one of the default channels is stored
		# in an unrecognized part name, then we assume that this part is a Nuke layer name, and incorrectly
		# prefix it.  We haven't seen this in practice though - usually the main part name will be named
		# something like "RGB" or "rgba" or "main", which we recognize.  If you have an EXR with weird part
		# names though, you can load it correctly by switching channelInterpretation from Default to
		# Specification
		reader["fileName"].setValue( "${GAFFER_ROOT}/python/GafferImageTest/images/weirdPartNames.exr" )
		reader["channelInterpretation"].setValue( GafferImage.ImageReader.ChannelInterpretation.Default )
		validateChannels( [
			( "part0.R", 0.1 ), ( "part1.G", 0.2 ), ( "part2.B", 0.3 ), ( "layer.R", 0.4 ),
			( "part3.A", 0.4 ), ( "layer.G", 0.5 ), ( "layer.B", 0.6 ), ( "layer.A", 1.0 )
		] )
		reader["channelInterpretation"].setValue( GafferImage.ImageReader.ChannelInterpretation.Legacy )
		validateChannels( [
			( "part0.R", 0.1 ), ( "part1.G", 0.2 ), ( "part2.B", 0.3 ), ( "part2.layer.R", 0.4 ),
			( "part3.A", 0.4 ), ( "part3.layer.G", 0.5 ), ( "part4.layer.B", 0.6 ), ( "part5.layer.A", 1.0 )
		] )
		reader["channelInterpretation"].setValue( GafferImage.ImageReader.ChannelInterpretation.Specification )
		validateChannels( [
			( "R", 0.1 ), ( "G", 0.2 ), ( "B", 0.3 ), ( "layer.R", 0.4 ),
			( "A", 0.4 ), ( "layer.G", 0.5 ), ( "layer.B", 0.6 ), ( "layer.A", 1.0 )
		] )

	def testWithChannelTestImage( self ):
		reference = self.channelTestImage()

		reader = GafferImage.ImageReader()

		for n in [ "SinglePart", "PartPerLayer", "NukeSinglePart", "NukePartPerLayer" ]:

			reader["fileName"].setValue( "${GAFFER_ROOT}/python/GafferImageTest/images/channelTest" + n + ".exr" )

			# The default channel interpretation should work fine with files coming from Nuke, or from a
			# spec compliant writer ( like Gaffer's new default )
			reader["channelInterpretation"].setValue( GafferImage.ImageReader.ChannelInterpretation.Default )
			self.assertImagesEqual( reader["out"], reference["out"], ignoreMetadata = True, ignoreChannelNamesOrder = n.startswith( "Nuke" ), maxDifference = 0.0002 )


			reader["channelInterpretation"].setValue( GafferImage.ImageReader.ChannelInterpretation.Specification )
			if n == "NukeSinglePart":
				# Reading a single part Nuke file based on the spec gives weird channel names
				self.assertEqual( list( reader["out"].channelNames() ), [ "R", "G", "B", "A", "character.red", "character.green", "character.blue", "character.alpha", "character.Z", "character.ZBack", "character.custom", "character.mask", "depth.Z", "other.ZBack", "other.custom", "other.mask" ] )
			elif n == "NukePartPerLayer":
				# Trying to open a Nuke multipart file according to the spec goes very badly, since the
				# channel names aren't unique ( since Nuke incorrectly expects them to be prefixed ).  Check
				# we get warnings about duplicate channels
				with IECore.CapturingMessageHandler() as mh :
					reader["out"].channelNames()
				self.assertTrue( len( mh.messages ) )
				self.assertTrue( mh.messages[0].message.startswith( "Ignoring channel" ) )

			else:
				self.assertImagesEqual( reader["out"], reference["out"], ignoreMetadata = True, maxDifference = 0.0002 )

			reader["channelInterpretation"].setValue( GafferImage.ImageReader.ChannelInterpretation.Legacy )
			if n == "PartPerLayer":
				# Using the Legacy mode on a spec compliant EXR adds incorrect prefixes
				self.assertEqual( list( reader["out"].channelNames() ), [ "character." + i if i.startswith( "character." ) else i for i in reference["out"].channelNames() ] )
			elif n == "NukeSinglePart":
				# Single part nuke files were dealt with almost OK, except for the weird "other" and "depth" prefixes
				self.assertEqual( list( reader["out"].channelNames() ), [ "R", "G", "B", "A", "character.red", "character.green", "character.blue", "character.alpha", "character.Z", "character.ZBack", "character.custom", "character.mask", "depth.Z", "other.ZBack", "other.custom", "other.mask" ] )
			elif n == "NukePartPerLayer":
				# Multi part Nuke files were dealt with very badly ... I'm a bit surprised by how messy this is.
				# We had special cases for parts named "rgba" or "depth", but they don't trigger here because
				# Nuke adds view prefixes.  I'm confused by why the legacy code has these branches that don't do
				# anything in practice ... maybe they were written for an older version of Nuke that didn't suffix
				# with the view name
				self.assertEqual( list( reader["out"].channelNames() ), [ "rgba.main.R", "rgba.main.G", "rgba.main.B", "rgba.main.A", "character.main.red", "character.main.green", "character.main.blue", "character.main.alpha", "character.main.Z", "character.main.ZBack", "character.main.custom", "character.main.mask", "depth.main.Z", "other.main.ZBack", "other.main.custom", "other.main.mask" ] )
			else:
				# The only complex files it actually dealt with properly were single part, standards compliant files
				self.assertImagesEqual( reader["out"], reference["out"], ignoreMetadata = True, maxDifference = 0.0002 )

if __name__ == "__main__":
	unittest.main()
