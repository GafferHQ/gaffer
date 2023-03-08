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

import math
import os
import pathlib
import shutil
import unittest
import imath

import IECore

import Gaffer
import GafferTest
import GafferImage
import GafferImageTest

class ImageReaderTest( GafferImageTest.ImageTestCase ) :

	fileName = GafferImageTest.ImageTestCase.imagesPath() / "circles.exr"
	colorSpaceFileName = GafferImageTest.ImageTestCase.imagesPath() / "circles_as_cineon.exr"
	offsetDataWindowFileName = GafferImageTest.ImageTestCase.imagesPath() / "rgb.100x100.exr"
	jpgFileName = GafferImageTest.ImageTestCase.imagesPath() / "circles.jpg"
	largeFileName = GafferImageTest.ImageTestCase.imagesPath() / "colorbars_max_clamp.exr"

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

	def testChannelMissing( self ) :
		n = GafferImage.ImageReader()
		n["fileName"].setValue( self.largeFileName )

		with self.assertRaisesRegex( RuntimeError, 'OpenImageIOReader : No channel named "doesNotExist"' ):
			n["out"].channelData( "doesNotExist", imath.V2i( 0 ) )

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

		testFile = self.temporaryDirectory() / "refresh.exr"
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

		self.assertRaisesRegex( RuntimeError, ".*wellIDontExist.exr.*", reader["out"]["format"].getValue )
		self.assertRaisesRegex( RuntimeError, ".*wellIDontExist.exr.*", reader["out"]["dataWindow"].getValue )
		self.assertRaisesRegex( RuntimeError, ".*wellIDontExist.exr.*", reader["out"]["metadata"].getValue )
		self.assertRaisesRegex( RuntimeError, ".*wellIDontExist.exr.*", reader["out"]["channelNames"].getValue )
		self.assertRaisesRegex( RuntimeError, ".*wellIDontExist.exr.*", reader["out"].channelData, "R", imath.V2i( 0 ) )
		self.assertRaisesRegex( RuntimeError, ".*wellIDontExist.exr.*", GafferImage.ImageAlgo.image, reader["out"] )

	def testMissingFrameMode( self ) :

		testSequence = IECore.FileSequence( str( self.temporaryDirectory() / "incompleteSequence.####.exr" ) )
		shutil.copyfile( self.fileName, testSequence.fileNameForFrame( 1 ) )
		shutil.copyfile( self.offsetDataWindowFileName, testSequence.fileNameForFrame( 3 ) )

		reader = GafferImage.ImageReader()
		# todo : Change IECore.FileSequence to return a `pathlib.Path` object and use that directly.
		reader["fileName"].setValue( pathlib.Path( testSequence.fileName ) )

		oiio = GafferImage.OpenImageIOReader()
		oiio["fileName"].setValue( pathlib.Path( testSequence.fileName ) )

		def assertMatch() :

			self.assertEqual( reader["out"]["format"].getValue(), oiio["out"]["format"].getValue() )
			self.assertEqual( reader["out"]["dataWindow"].getValue(), oiio["out"]["dataWindow"].getValue() )
			self.assertEqual( reader["out"]["metadata"].getValue(), oiio["out"]["metadata"].getValue() )
			self.assertEqual( reader["out"]["channelNames"].getValue(), oiio["out"]["channelNames"].getValue() )

			# It is only valid to query the data inside the data window
			if not GafferImage.BufferAlgo.empty( reader["out"]["dataWindow"].getValue() ):
				self.assertEqual( reader["out"].channelData( "R", imath.V2i( 0 ) ), oiio["out"].channelData( "R", imath.V2i( 0 ) ) )
			self.assertImagesEqual( reader["out"], oiio["out"] )

		context = Gaffer.Context( Gaffer.Context.current() )

		# set to a missing frame
		context.setFrame( 2 )

		# everything throws
		reader["missingFrameMode"].setValue( GafferImage.ImageReader.MissingFrameMode.Error )
		with context :
			self.assertRaisesRegex( RuntimeError, ".*incompleteSequence.*.exr.*", reader["out"]["format"].getValue )
			self.assertRaisesRegex( RuntimeError, ".*incompleteSequence.*.exr.*", reader["out"]["dataWindow"].getValue )
			self.assertRaisesRegex( RuntimeError, ".*incompleteSequence.*.exr.*", reader["out"]["metadata"].getValue )
			self.assertRaisesRegex( RuntimeError, ".*incompleteSequence.*.exr.*", reader["out"]["channelNames"].getValue )
			self.assertRaisesRegex( RuntimeError, ".*incompleteSequence.*.exr.*", reader["out"].channelData, "R", imath.V2i( 0 ) )
			self.assertRaisesRegex( RuntimeError, ".*incompleteSequence.*.exr.*", GafferImage.ImageAlgo.image, reader["out"] )

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
			self.assertRaisesRegex( RuntimeError, ".*incompleteSequence.*.exr.*", GafferImage.ImageAlgo.image, reader["out"] )
			self.assertRaisesRegex( RuntimeError, ".*incompleteSequence.*.exr.*", reader["out"]["format"].getValue )
			self.assertRaisesRegex( RuntimeError, ".*incompleteSequence.*.exr.*", reader["out"]["dataWindow"].getValue )
			self.assertRaisesRegex( RuntimeError, ".*incompleteSequence.*.exr.*", reader["out"]["metadata"].getValue )
			self.assertRaisesRegex( RuntimeError, ".*incompleteSequence.*.exr.*", reader["out"]["channelNames"].getValue )
			self.assertRaisesRegex( RuntimeError, ".*incompleteSequence.*.exr.*", reader["out"].channelData, "R", imath.V2i( 0 ) )

		reader["missingFrameMode"].setValue( GafferImage.OpenImageIOReader.MissingFrameMode.Black )
		oiio["missingFrameMode"].setValue( GafferImage.OpenImageIOReader.MissingFrameMode.Black )
		with context :
			self.assertRaisesRegex( RuntimeError, ".*incompleteSequence.*.exr.*", GafferImage.ImageAlgo.image, reader["out"] )
			self.assertRaisesRegex( RuntimeError, ".*incompleteSequence.*.exr.*", reader["out"]["format"].getValue )
			self.assertEqual( reader["out"]["dataWindow"].getValue(), oiio["out"]["dataWindow"].getValue() )
			self.assertEqual( reader["out"]["metadata"].getValue(), oiio["out"]["metadata"].getValue() )
			self.assertEqual( reader["out"]["channelNames"].getValue(), oiio["out"]["channelNames"].getValue() )
			self.assertTrue( GafferImage.BufferAlgo.empty( reader["out"]['dataWindow'].getValue() ) )
			self.assertTrue( GafferImage.BufferAlgo.empty( oiio["out"]['dataWindow'].getValue() ) )

	def testFrameRangeMask( self ) :

		testSequence = IECore.FileSequence( str( self.temporaryDirectory() / "incompleteSequence.####.exr" ) )
		shutil.copyfile( self.fileName, testSequence.fileNameForFrame( 1 ) )
		shutil.copyfile( self.fileName, testSequence.fileNameForFrame( 3 ) )
		shutil.copyfile( self.offsetDataWindowFileName, testSequence.fileNameForFrame( 5 ) )
		shutil.copyfile( self.offsetDataWindowFileName, testSequence.fileNameForFrame( 7 ) )

		reader = GafferImage.ImageReader()
		reader["fileName"].setValue( pathlib.Path( testSequence.fileName ) )
		reader["missingFrameMode"].setValue( GafferImage.ImageReader.MissingFrameMode.Hold )

		oiio = GafferImage.OpenImageIOReader()
		oiio["fileName"].setValue( pathlib.Path( testSequence.fileName ) )
		oiio["missingFrameMode"].setValue( GafferImage.ImageReader.MissingFrameMode.Hold )

		context = Gaffer.Context( Gaffer.Context.current() )

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

			context = Gaffer.Context( Gaffer.Context.current() )
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

			w["fileName"].setValue( self.temporaryDirectory() / "{0}.{1}".format( dataType, ext ) )
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
		def validateChannels( channels, view = "default" ):
			self.assertEqual( reader["out"].viewNames(), IECore.StringVectorData( [ view ] ) )
			self.assertEqual( [ i for i in reader["out"].channelNames( view ) ], [ i[0] for i in channels ] )
			for name, value in channels:
				self.assertAlmostEqual( reader["out"].channelData( name, imath.V2i( 0 ), view )[0], value, places = 3 )

		reader["fileName"].setValue( self.imagesPath() / "imitateProductionLayers1.exr" )

		reader["channelInterpretation"].setValue( GafferImage.ImageReader.ChannelInterpretation.Default )
		validateChannels( [ ( "R", 0.1 ), ( "G", 0.2 ), ( "B", 0.3 ), ( "character.R", 0.4 ), ( "character.G", 0.5 ), ( "character.B", 0.6 ) ] )
		reader["channelInterpretation"].setValue( GafferImage.ImageReader.ChannelInterpretation.Legacy )
		validateChannels( [ ( "rgba.main.R", 0.1 ), ( "rgba.main.G", 0.2 ), ( "rgba.main.B", 0.3 ), ( "character.main.red", 0.4 ), ( "character.main.green", 0.5 ), ( "character.main.blue", 0.6 ) ] )
		reader["channelInterpretation"].setValue( GafferImage.ImageReader.ChannelInterpretation.Specification )
		# This file has a view of "main" - by default, we assume that this is a Nuke file which should be
		# interpreted as the default view ( same as if the view is unspecified in OpenEXR ), but if you ask
		#for the specification interpretation, then you actually get a view named "main"
		validateChannels( [ ( "R", 0.1 ), ( "G", 0.2 ), ( "B", 0.3 ), ( "red", 0.4 ), ( "green", 0.5 ), ( "blue", 0.6 ) ], "main" )

		reader["fileName"].setValue( self.imagesPath() / "imitateProductionLayers2.exr" )
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
		reader["fileName"].setValue( self.imagesPath() / "weirdPartNames.exr" )
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

			reader["fileName"].setValue( self.imagesPath() / ( "channelTest" + n + ".exr" ) )

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
					# We also need to access it as a multi-view file, since according to the spec, there is a
					# view declared
					reader["out"].channelNames( "main" )
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

	def testWithMultiViewChannelTestImage( self ):
		reference = self.channelTestImageMultiView()

		reader = GafferImage.ImageReader()

		# Note that we have no test file to compare to for NukePartPerLayer, because Nuke just crashes when
		# I try to export in that mode to get a reference image
		for n in [ "SinglePart", "PartPerView", "PartPerLayer", "NukeCompat", "NukePartPerView", "NukeSinglePart" ]:
			if n == "NukeSinglePart":
				# We've tried to munge together the EXR spec, and what Nuke actually does, when using the "Default"
				# channel interpretation, but when it comes to Nuke's implementation of single part multi-view, it
				# directly contradicts the spec - the spec says "If a channel contains image data that is not
				# associated with any view, then the channel must have at least one period in its name,
				# otherwise it will be considered to belong to the default view."  But Nuke exports channels
				# in the default view with periods when they are in layers, without including the view name,
				# like the spec says they must.  I guess we just give up on this?
				continue

			reader["fileName"].setValue( self.imagesPath() / ( "channelTestMultiView" + n + ".exr" ) )

			# Our reference comes from channelTestImageMultiView, which tries to exercise a bunch of corner
			# cases, including one view with some channels deleted so the channels aren't the same between views.
			# Nuke can't handle this, so disable the Delete for the test where we compare with Nuke
			reference["DeleteChannels"]["enabled"].setValue( not n.startswith( "Nuke" ) )

			# If the data window couldn't be stored separately, due to using an out of date version of OpenEXR,
			# or Nuke not supporting it, then we can't expect the data windows to match
			windowExpanded = n == "SinglePart" or n.startswith( "Nuke" )

			# The default channel interpretation should work fine with files coming from Nuke, or from a
			# spec compliant writer ( like Gaffer's new default )
			reader["channelInterpretation"].setValue( GafferImage.ImageReader.ChannelInterpretation.Default )
			self.assertImagesEqual( reader["out"], reference["out"], ignoreMetadata = True, ignoreChannelNamesOrder = True, ignoreViewNamesOrder = True, maxDifference = 0.0002, ignoreDataWindow = windowExpanded )

			if n.startswith( "Nuke" ):
				# Reading Nuke files according to the spec produces weird results - we check exactly how
				# they are weird in the single view case above, don't bother repeating that for multi-view
				continue

			reader["channelInterpretation"].setValue( GafferImage.ImageReader.ChannelInterpretation.Specification )
			self.assertImagesEqual( reader["out"], reference["out"], ignoreMetadata = True, maxDifference = 0.0002, ignoreChannelNamesOrder = True, ignoreViewNamesOrder = True, ignoreDataWindow = windowExpanded )

	@unittest.skipIf( not "OPENEXR_IMAGES_DIR" in os.environ, "If you want to run tests using the OpenEXR sample images, then download https://github.com/AcademySoftwareFoundation/openexr-images and set the env var OPENEXR_IMAGES_DIR to the directory" )
	def testWithEXRSampleImages( self ):

		directory = pathlib.Path( os.environ["OPENEXR_IMAGES_DIR"] )

		reader = GafferImage.ImageReader()

		stats = GafferImage.ImageStats()
		stats["in"].setInput( reader["out"] )

		# This is an awfully brute force way to test this, just recording the current results for
		# basic statistics on everything, but I've augmented this through visually skimming through these
		# images, and this ensures that nothing unexpected is happening, and that our loading of these images
		# doesn't change

		for name, expected in [
			[ "Chromaticities/Rec709.exr", [
					[ None, "RGB", ((0,0), (610,406)), (0.365261, 0.277788, 0.115344, 0), (0.00322533, 0, 0, 0), (6.94531, 4.64062, 4.14062, 0) ] ] ],
			[ "Chromaticities/XYZ.exr", [
					[ None, "RGB", ((0,0), (610,406)), (0.27078, 0.284661, 0.14981, 0), (0.00473022, 0.00584412, 0.00109863, 0), (4.82812, 4.91797, 4.19922, 0) ] ] ],
			[ "DisplayWindow/t01.exr", [
					[ None, "RGB", ((0,0), (400,300)), (0.0075, 0.00918333, 0.740058, 0), (0, 0, 0, 0), (2, 2, 2, 0) ] ] ],
			[ "DisplayWindow/t02.exr", [
					[ None, "RGB", ((0,2), (400,302)), (0.0075, 0.00918333, 0.740058, 0), (0, 0, 0, 0), (2, 2, 2, 0) ] ] ],
			[ "DisplayWindow/t03.exr", [
					[ None, "RGB", ((0,20), (400,320)), (0.0075, 0.00918333, 0.740058, 0), (0, 0, 0, 0), (2, 2, 2, 0) ] ] ],
			[ "DisplayWindow/t04.exr", [
					[ None, "RGB", ((0,-20), (400,280)), (0.0075, 0.00918333, 0.740058, 0), (0, 0, 0, 0), (2, 2, 2, 0) ] ] ],
			[ "DisplayWindow/t05.exr", [
					[ None, "RGB", ((0,0), (400,300)), (0.0075, 0.00918333, 0.740058, 0), (0, 0, 0, 0), (2, 2, 2, 0) ] ] ],
			[ "DisplayWindow/t06.exr", [
					[ None, "RGB", ((0,0), (400,300)), (0.0075, 0.00918333, 0.740058, 0), (0, 0, 0, 0), (2, 2, 2, 0) ] ] ],
			[ "DisplayWindow/t07.exr", [
					[ None, "RGB", ((0,-9), (400,291)), (0.0075, 0.00918333, 0.740058, 0), (0, 0, 0, 0), (2, 2, 2, 0) ] ] ],
			[ "DisplayWindow/t08.exr", [
					[ None, "RGB", ((30,61), (430,361)), (0.0075, 0.00918333, 0.740058, 0), (0, 0, 0, 0), (2, 2, 2, 0) ] ] ],
			[ "DisplayWindow/t09.exr", [
					[ None, "RGB", ((0,0), (400,300)), (0.0075, 0.00918333, 0.740058, 0), (0, 0, 0, 0), (2, 2, 2, 0) ] ] ],
			[ "DisplayWindow/t10.exr", [
					[ None, "RGB", ((0,0), (400,300)), (0.0075, 0.00918333, 0.740058, 0), (0, 0, 0, 0), (2, 2, 2, 0) ] ] ],
			[ "DisplayWindow/t11.exr", [
					[ None, "RGB", ((0,500), (400,800)), (0.0075, 0.00918333, 0.740058, 0), (0, 0, 0, 0), (2, 2, 2, 0) ] ] ],
			[ "DisplayWindow/t12.exr", [
					[ None, "RGB", ((0,-400), (400,-100)), (0.0075, 0.00918333, 0.740058, 0), (0, 0, 0, 0), (2, 2, 2, 0) ] ] ],
			[ "DisplayWindow/t13.exr", [
					[ None, "RGB", ((0,399), (400,699)), (0.0075, 0.00918333, 0.740058, 0), (0, 0, 0, 0), (2, 2, 2, 0) ] ] ],
			[ "DisplayWindow/t14.exr", [
					[ None, "RGB", ((0,-399), (400,-99)), (0.0075, 0.00918333, 0.740058, 0), (0, 0, 0, 0), (2, 2, 2, 0) ] ] ],
			[ "DisplayWindow/t15.exr", [
					[ None, "RGB", ((0,-9), (400,291)), (0.0075, 0.00918333, 0.740058, 0), (0, 0, 0, 0), (2, 2, 2, 0) ] ] ],
			[ "DisplayWindow/t16.exr", [
					[ None, "RGB", ((0,-9), (400,291)), (0.0075, 0.00918333, 0.740058, 0), (0, 0, 0, 0), (2, 2, 2, 0) ] ] ],
			[ "MultiResolution/Bonita.exr", [
					[ None, "RGB", ((0,0), (550,832)), (0.522202, 0.559464, 0.638232, 0), (0.00196457, 0.00156307, 0.00118732, 0), (73.6875, 75.125, 178.375, 0) ] ] ],
			[ "MultiResolution/ColorCodedLevels.exr", [
					[ None, "RGBA", ((0,0), (512,512)), (0.494569, 0.494569, 0.494569, 1), (0, 0, 0, 1), (0.999512, 0.999512, 0.999512, 1) ] ] ],
			[ "MultiResolution/Kapaa.exr", [
					[ None, "RGB", ((0,0), (799,546)), (0.90483, 0.888923, 0.862289, 0), (0.00575638, 0.0064888, 0.040863, 0), (5.57812, 5.625, 6.9375, 0) ] ] ],
			[ "MultiResolution/KernerEnvCube.exr", [
					[ None, "RGBA", ((0,-1280), (256,256)), (0.131746, 0.175845, 0.252479, 1), (0.00287819, 0.00508499, 0.00519943, 1), (1657, 1657, 1657, 1) ] ] ],
			[ "MultiResolution/KernerEnvLatLong.exr", [
					[ None, "RGBA", ((0,0), (1024,512)), (0.116983, 0.155036, 0.223585, 1), (0.00248146, 0.00481033, 0.00497818, 1), (1678, 1678, 1678, 1) ] ] ],
			[ "MultiResolution/MirrorPattern.exr", [
					[ None, "RGB", ((0,0), (512,512)), (0.215575, 0.126366, 0.126366, 0), (0, 0, 0, 0), (1, 1, 1, 0) ] ] ],
			[ "MultiResolution/OrientationCube.exr", [
					[ None, "RGBA", ((0,-2560), (512,512)), (0.913853, 0.943919, 0.978465, 1), (0, 0, 0, 1), (0.996582, 0.990723, 0.990723, 1) ] ] ],
			[ "MultiResolution/OrientationLatLong.exr", [
					[ None, "RGBA", ((0,0), (1024,512)), (0.876986, 0.914758, 0.957655, 1), (0, 0, 0, 1), (0.995605, 0.990723, 0.990723, 1) ] ] ],
			[ "MultiResolution/PeriodicPattern.exr", [
					[ None, "RGB", ((0,0), (517,517)), (0.211508, 0.210598, 0.199672, 0), (0.0499878, 0.0100021, 0.0100021, 0), (1, 1, 1, 0) ] ] ],
			[ "MultiResolution/StageEnvCube.exr", [
					[ None, "RGB", ((0,-1280), (256,256)), (2.4875, 3.15043, 4.28611, 0), (0.00164318, 0.000381231, 0, 0), (4096, 4096, 4096, 0) ] ] ],
			[ "MultiResolution/StageEnvLatLong.exr", [
					[ None, "RGB", ((0,0), (1000,500)), (2.18642, 2.76372, 3.75409, 0), (0.00134659, 0.000170827, 0, 0), (4096, 4096, 4096, 0) ] ] ],
			[ "MultiResolution/WavyLinesCube.exr", [
					[ None, "RGB", ((0,-1280), (256,256)), (0.195406, 0.195406, 0.195406, 0), (0.0999756, 0.0999756, 0.0999756, 0), (0.999512, 0.999512, 0.999512, 0) ] ] ],
			[ "MultiResolution/WavyLinesLatLong.exr", [
					[ None, "RGB", ((0,0), (1024,512)), (0.202087, 0.202087, 0.202087, 0), (0.0999756, 0.0999756, 0.0999756, 0), (1, 1, 1, 0) ] ] ],
			[ "MultiResolution/WavyLinesSphere.exr", [
					[ None, "RGBA", ((0,0), (480,480)), (0.107064, 0.107064, 0.107064, 1), (0, 0, 0, 1), (0.981445, 0.981445, 0.981445, 1) ] ] ],
			[ "MultiView/Adjuster.exr", [
					[ "center", "RGB", ((0,0), (775,678)), (0.322665, 0.184189, 0.0388801, 0), (0.000525475, 1.11461e-05, -1.64509e-05, 0), (12, 11.8906, 11.8672, 0) ],
					[ "left", "RGB", ((0,0), (775,678)), (0.310802, 0.177438, 0.0330001, 0), (0.000848293, 4.01139e-05, -1.57952e-05, 0), (12, 11.8906, 11.8438, 0) ],
					[ "right", "RGB", ((0,0), (775,678)), (0.333135, 0.18872, 0.0423806, 0), (0.000470877, 1.48416e-05, -1.46627e-05, 0), (12, 11.9141, 11.9141, 0) ] ] ],
			[ "MultiView/Balls.exr", [
					[ "left", "RGB", ((0,0), (1000,784)), (0.102131, 0.0780757, 0.0596448, 0), (0.00131321, 0.00157166, 0, 0), (16, 16, 16, 0) ],
					[ "right", "RGB", ((0,0), (1000,784)), (0.0977333, 0.0752816, 0.0562899, 0), (1.43051e-05, 0.000945091, 6.31809e-06, 0), (15.9844, 15.9531, 15.9609, 0) ] ] ],
			[ "MultiView/Fog.exr", [
					[ "left", "Y", ((0,0), (1000,672)), (0.0304154, 0.0304154, 0.0304154, 0), (0.000130057, 0.000130057, 0.000130057, 0), (50.6875, 50.6875, 50.6875, 0) ],
					[ "right", "Y", ((0,0), (1000,672)), (0.0281404, 0.0281404, 0.0281404, 0), (0, 0, 0, 0), (20.6719, 20.6719, 20.6719, 0) ] ] ],
			[ "MultiView/Impact.exr", [
					[ "left", "RGB", ((0,0), (554,699)), (0.0697831, 0.0726828, 0.0734706, 0), (0, 0, 0, 0), (11.1797, 10.9766, 11.4766, 0) ],
					[ "right", "RGB", ((0,0), (554,699)), (0.0587976, 0.0627622, 0.0626202, 0), (0, 0, 0, 0), (9.46094, 9.04688, 10.0781, 0) ] ] ],
			[ "MultiView/LosPadres.exr", [
					[ "right", "RGB", ((0,0), (689,1000)), (0.281751, 0.244324, 0.269491, 0), (0.000358343, 8.67248e-05, 6.20484e-05, 0), (0.785645, 0.862793, 0.930176, 0) ],
					[ "left", "RGB", ((0,0), (689,1000)), (0.274605, 0.235265, 0.260486, 0), (5.35846e-05, 4.58956e-06, 1.60933e-06, 0), (0.825195, 0.868164, 0.916992, 0) ] ] ],
			[ "ScanLines/Blobbies.exr", [
					[ None, "RGBAZ", ((-20,-20), (1020,1020)), (0.0711425, 0.107248, 0.0443995, 0.662422), (0, 0, 0, 0), (6.23047, 6.41016, 6.05078, 1.00098) ] ] ],
			[ "ScanLines/CandleGlass.exr", [
					[ None, "RGBA", ((0,0), (1000,810)), (0.14975, 0.055625, 0.0159023, 0.0962285), (-8.86917e-05, -0.000217438, -0.000338554, 0), (413.25, 173.375, 43.875, 1) ] ] ],
			[ "ScanLines/Cannon.exr", [
					[ None, "RGB", ((0,0), (780,566)), (0.347088, 0.359306, 0.34587, 0), (0.0241089, 0.0226288, 0.0201416, 0), (2.60156, 2.55469, 2.64258, 0) ] ] ],
			[ "ScanLines/Desk.exr", [
					[ None, "RGBA", ((0,0), (644,874)), (6.06403, 6.04835, 2.85017, 1), (-0.000806808, -0.0119171, -0.00597382, 1), (193.625, 233.75, 230.125, 1) ] ] ],
			[ "ScanLines/MtTamWest.exr", [
					[ None, "RGBA", ((0,0), (1214,732)), (0.222063, 0.354169, 0.495088, 1), (0.000188112, 0.000243545, 0, 1), (3.88477, 3.89844, 4.87891, 1) ] ] ],
			[ "ScanLines/PrismsLenses.exr", [
					[ None, "RGBA", ((0,0), (1200,865)), (0.0351189, 0.0882229, 0.00894904, 0.111396), (-0.000112534, 1.23978e-05, -5.91278e-05, 0), (227.75, 492.25, 152.25, 1) ] ] ],
			[ "ScanLines/StillLife.exr", [
					[ None, "RGBA", ((0,0), (1240,846)), (0.135308, 0.0781079, 0.0581713, 1), (0, 0, 0, 1), (231.5, 214.5, 491.5, 1) ] ] ],
			[ "ScanLines/Tree.exr", [
					[ None, "RGBA", ((0,0), (928,906)), (0.625079, 0.978651, 1.30421, 1), (0, 0, 0, 1), (9.32031, 12.2578, 16.2969, 1) ] ] ],
			[ "TestImages/AllHalfValues.exr", [
					[ None, "RGB", ((0,0), (256,256)), (math.nan, math.nan, math.nan, 0), (-65504, -65504, -65504, 0), (65504, 65504, 65504, 0) ] ] ],
			[ "TestImages/BrightRings.exr", [
					[ None, "RGB", ((0,0), (800,800)), (27.5853, 27.5853, 27.5853, 0), (0.5, 0.5, 0.5, 0), (1025, 1025, 1025, 0) ] ] ],
			[ "TestImages/BrightRingsNanInf.exr", [
					[ None, "RGB", ((0,0), (800,800)), (math.nan, math.nan, math.nan, 0), (-3.40282e+38, 0.5, -3.40282e+38, 0), (3.40282e+38, 1025, 3.40282e+38, 0) ] ] ],
			[ "TestImages/GammaChart.exr", [
					[ None, "RGB", ((0,0), (800,800)), (0.175781, 0.175781, 0.175781, 0), (0, 0, 0, 0), (1, 1, 1, 0) ] ] ],
			[ "TestImages/GrayRampsDiagonal.exr", [
					[ None, "Y", ((0,0), (800,800)), (0.642926, 0.642926, 0.642926, 0), (0.00179958, 0.00179958, 0.00179958, 0), (18, 18, 18, 0) ] ] ],
			[ "TestImages/GrayRampsHorizontal.exr", [
					[ None, "Y", ((0,0), (800,800)), (0.642926, 0.642926, 0.642926, 0), (0.00179958, 0.00179958, 0.00179958, 0), (18, 18, 18, 0) ] ] ],
			[ "TestImages/RgbRampsDiagonal.exr", [
					[ None, "RGB", ((0,0), (800,800)), (0.239128, 0.237108, 0.237333, 0), (0, 0, 0, 0), (18, 18, 18, 0) ] ] ],
			[ "TestImages/SquaresSwirls.exr", [
					[ None, "RGB", ((0,0), (1000,1000)), (18.495, 18.4687, 18.5593, 0), (-5.96046e-08, -5.96046e-08, 0, 0), (1000, 1000, 1000, 0) ] ] ],
			[ "TestImages/WideColorGamut.exr", [
					[ None, "RGB", ((0,0), (800,800)), (1.09907, 0.962274, 1.08193, 0), (-1.30273, -0.807129, -0.0823364, 0), (7.43359, 1.79297, 21.4375, 0) ] ] ],
			[ "TestImages/WideFloatRange.exr", [
					[ None, "G", ((0,0), (500,500)), (0, -5.00979e+21, 0, 0), (0, -1.70141e+38, 0, 0), (0, 1.70141e+38, 0, 0) ] ] ],
			[ "Tiles/GoldenGate.exr", [
					[ None, "RGB", ((0,0), (1262,860)), (0.0917954, 0.0977245, 0.280126, 0), (0.00133514, 0.000816345, 0, 0), (685.5, 200, 114.75, 0) ] ] ],
			[ "Tiles/Ocean.exr", [
					[ None, "RGB", ((0,0), (1255,876)), (2.95192, 4.37267, 5.00984, 0), (0.0001297, 2.31862e-05, 0, 0), (1423, 1622, 2100, 0) ] ] ],
			[ "Tiles/Spirals.exr", [
					[ None, "RGBAZ", ((-20,-20), (1020,1020)), (0.105671, 0.0587984, 0.0527612, 0.860275), (0, 0, 0, 0), (9.65625, 5.23438, 5.5625, 1.00098) ] ] ],
			[ "v2/LeftView/Balls.exr", [
					[ "left", "RGBAZ", ((247,0), (1678,761)), (0.0425611, 0.00429801, 0.00478153, 0.373963), (0, 0, 0, 0), (0.62207, 0.265625, 0.267822, 1) ] ] ],
			[ "v2/LeftView/Ground.exr", [
					[ "left", "RGBAZ", ((0,0), (1920,741)), (0.122791, 0.0876847, 0.0307255, 0.915993), (0, 0, 0, 0), (0.352295, 0.229492, 0.0673485, 1) ] ] ],
			[ "v2/LeftView/Leaves.exr", [
					[ "left", "RGBAZ", ((0,0), (1920,1080)), (0.0325196, 0.0705669, 0.0221435, 0.429987), (0, 0, 0, 0), (0.40332, 0.593262, 0.344971, 1) ] ] ],
			[ "v2/LeftView/Trunks.exr", [
					[ "left", "RGBAZ", ((0,0), (1920,814)), (0.0072465, 0.00569297, 0.00303837, 0.0964944), (0, 0, 0, 0), (0.397461, 0.307129, 0.177368, 1) ] ] ],
			[ "v2/LowResLeftView/Balls.exr", [
					[ "left", "RGBAZ", ((131,0), (895,406)), (0.0425079, 0.0042918, 0.00477465, 0.373747), (0, 0, 0, 0), (0.621582, 0.265625, 0.267822, 1) ] ] ],
			[ "v2/LowResLeftView/composited.exr", [
					[ None, "RGBA", ((1,1), (1023,575)), (0.0783222, 0.0939879, 0.0316361, 0.771075), (0, 0, 0, 0), (0.600098, 0.593262, 0.344727, 1) ] ] ],
			[ "v2/LowResLeftView/Ground.exr", [
					[ "left", "RGBAZ", ((0,0), (1024,396)), (0.122671, 0.087597, 0.0306891, 0.915247), (0, 0, 0, 0), (0.352295, 0.22937, 0.067193, 1) ] ] ],
			[ "v2/LowResLeftView/Leaves.exr", [
					[ "left", "RGBAZ", ((0,0), (1024,576)), (0.0324851, 0.0705, 0.0221249, 0.430456), (0, 0, 0, 0), (0.40332, 0.593262, 0.344727, 1) ] ] ],
			[ "v2/LowResLeftView/Trunks.exr", [
					[ "left", "RGBAZ", ((0,0), (1024,435)), (0.00720663, 0.00566415, 0.00302519, 0.0964603), (0, 0, 0, 0), (0.394043, 0.302734, 0.177368, 1) ] ] ],
			[ "v2/Stereo/Balls.exr", [
					[ "left", "RGBAZ", ((247,0), (1678,761)), (0.0425611, 0.00429801, 0.00478153, 0.373963), (0, 0, 0, 0), (0.62207, 0.265625, 0.267822, 1) ],
					[ "right", "RGBAZ", ((389,0), (1841,761)), (0.0413221, 0.00423597, 0.00471265, 0.368658), (0, 0, 0, 0), (0.619629, 0.266357, 0.268799, 1) ] ] ],
			[ "v2/Stereo/composited.exr", [
					[ "left", "RGBAZ", ((1,1), (1919,1079)), (0.0782152, 0.0939382, 0.0316098, 0.769054), (0, 0, 0, 0), (0.600586, 0.593262, 0.344971, 1) ],
					[ "right", "RGBAZ", ((1,1), (1919,1079)), (0.0725963, 0.0852973, 0.0297889, 0.78676), (0, 0, 0, 0), (0.600586, 0.591309, 0.345215, 1) ] ] ],
			[ "v2/Stereo/Ground.exr", [
					[ "left", "RGBAZ", ((0,0), (1920,741)), (0.122791, 0.0876847, 0.0307255, 0.915993), (0, 0, 0, 0), (0.352295, 0.229492, 0.0673485, 1) ],
					[ "right", "RGBAZ", ((0,0), (1920,741)), (0.119776, 0.0856502, 0.0300023, 0.913899), (0, 0, 0, 0), (0.352295, 0.229492, 0.0666981, 1) ] ] ],
			[ "v2/Stereo/Leaves.exr", [
					[ "left", "RGBAZ", ((0,0), (1920,1080)), (0.0325196, 0.0705669, 0.0221435, 0.429987), (0, 0, 0, 0), (0.40332, 0.593262, 0.344971, 1) ],
					[ "right", "RGBAZ", ((0,0), (1920,1080)), (0.0297268, 0.064128, 0.0210256, 0.463715), (0, 0, 0, 0), (0.402832, 0.591309, 0.345215, 1) ] ] ],
			[ "v2/Stereo/Trunks.exr", [
					[ "left", "RGBAZ", ((0,0), (1920,814)), (0.0072465, 0.00569297, 0.00303837, 0.0964944), (0, 0, 0, 0), (0.397461, 0.307129, 0.177368, 1) ],
					[ "right", "RGBAZ", ((0,0), (1883,814)), (0.00711977, 0.00569962, 0.00315493, 0.111899), (0, 0, 0, 0), (0.396729, 0.306396, 0.17749, 1) ] ] ]
		]:
			reader["fileName"].setValue( directory / name )

			# The EXR examples should load correctly with either our default interpretation, or a strict
			# interpretation of the spec
			for interpretation in [ GafferImage.ImageReader.ChannelInterpretation.Default, GafferImage.ImageReader.ChannelInterpretation.Specification ]:
				reader["channelInterpretation"].setValue( interpretation )
				self.assertEqual( list( reader["out"].viewNames() ), [ i[0] for i in expected ] if expected[0][0] else [ "default" ]  )
				for e in expected:
					channelNames = reader["out"].channelNames( e[0] )
					self.assertEqual( "".join( channelNames ), e[1] )

					dw = reader["out"].dataWindow( e[0] )
					self.assertEqual( dw, imath.Box2i( imath.V2i( *e[2][0] ), imath.V2i( *e[2][1] ) ) )

					stats["view"].setValue( e[0] or "" )
					if list( channelNames ) == ["Y"]:
						stats['channels'].setValue( IECore.StringVectorData( ["Y", "Y", "Y", "A" ] ) )
					else:
						stats['channels'].setValue( IECore.StringVectorData( ["R", "G", "B", "A" ] ) )

					stats["area"].setValue( dw )
					for i in range( 4 ):
						# TODO - It's even more awful than usual for Python that the standard spec for
						# assertAlmostEqual doesn't use significant digits.  Should really put a proper
						# version of assertAlmostEqual in GafferTest.TestCase ( we could handle imath types
						# as well ), and also handle nans properly
						if not ( stats["average"].getValue()[i] != stats["average"].getValue()[i] and e[3][i] != e[3][i] or abs( e[3][i] ) > 1e20 ):
							self.assertAlmostEqual( stats["average"].getValue()[i], e[3][i], places = 4 )
						if not ( stats["min"].getValue()[i] != stats["min"].getValue()[i] and e[4][i] != e[4][i] or abs( e[4][i] ) > 1e20 ):
							self.assertAlmostEqual( stats["min"].getValue()[i], e[4][i], places = 4 )
						if not ( stats["max"].getValue()[i] != stats["max"].getValue()[i] and e[5][i] != e[5][i] or abs( e[5][i] ) > 1e20 ):
							self.assertAlmostEqual( stats["max"].getValue()[i], e[5][i], places = 4 )


	@unittest.skipIf( not "OPENEXR_IMAGES_DIR" in os.environ, "If you want to run tests using the OpenEXR sample images, then download https://github.com/AcademySoftwareFoundation/openexr-images and set the env var OPENEXR_IMAGES_DIR to the directory" )
	def testEXRSampleImagesComplexMultiView( self ):

		# The Beachball images demonstrate a bunch of edge cases in multi-view images - single part multi-view,
		# channels not in views, channels in layers, etc, so we test them separately
		directory = os.environ["OPENEXR_IMAGES_DIR"] + "/"

		multiPartReader = GafferImage.ImageReader()
		multiPartReader["fileName"].setValue( directory + "Beachball/multipart.0001.exr" )
		singlePartReader = GafferImage.ImageReader()
		singlePartReader["fileName"].setValue( directory + "Beachball/singlepart.0001.exr" )

		for interpretation in [ GafferImage.ImageReader.ChannelInterpretation.Default, GafferImage.ImageReader.ChannelInterpretation.Specification ]:
			multiPartReader["channelInterpretation"].setValue( interpretation )
			singlePartReader["channelInterpretation"].setValue( interpretation )

			self.assertEqual( list( multiPartReader["out"].viewNames() ), [ "right", "left", "default" ] )
			# The order is a little bit weird : EXR sorts alphabetically, and then OIIO sorts RGBA correctly.
			# This matches our expectations:
			self.assertEqual( list( multiPartReader["out"].channelNames( "left" ) ), ['Z', 'forward.u', 'forward.v', 'whitebarmask.mask', 'R', 'G', 'B', 'A'] )
			self.assertEqual( list( multiPartReader["out"].channelNames( "right" ) ), [ 'R', 'G', 'B', 'A', 'Z', 'forward.u', 'forward.v', 'whitebarmask.mask' ] )
			self.assertEqual( list( multiPartReader["out"].channelNames( "default" ) ), [ 'disparityL.x', 'disparityL.y', 'disparityR.x', 'disparityR.y' ] )

			self.assertEqual( list( singlePartReader["out"].viewNames() ), [ "right", "left", "default" ] )
			self.assertEqual( list( singlePartReader["out"].channelNames( "left" ) ), ['forward.u', 'forward.v', 'R', 'G', 'B', 'A', 'Z', 'whitebarmask.mask'] )
			self.assertEqual( list( singlePartReader["out"].channelNames( "right" ) ), [ 'R', 'G', 'B', 'A', 'Z', 'forward.u', 'forward.v', 'whitebarmask.mask' ] )
			self.assertEqual( list( singlePartReader["out"].channelNames( "default" ) ), [ 'disparityL.x', 'disparityL.y', 'disparityR.x', 'disparityR.y' ] )

			self.assertEqual( multiPartReader["out"].dataWindow( "left" ), imath.Box2i( imath.V2i( 688, 435 ), imath.V2i( 1565, 1311 ) ) )
			self.assertEqual( multiPartReader["out"].dataWindow( "right" ), imath.Box2i( imath.V2i( 654, 435 ), imath.V2i( 1531, 1311 ) ) )
			self.assertEqual( multiPartReader["out"].dataWindow( "default" ), imath.Box2i( imath.V2i( 654, 435 ), imath.V2i( 1565, 1311 ) ) )
			self.assertEqual( singlePartReader["out"].dataWindow( "left" ), imath.Box2i( imath.V2i( 654, 435 ), imath.V2i( 1565, 1311 ) ) )
			self.assertEqual( singlePartReader["out"].dataWindow( "right" ), imath.Box2i( imath.V2i( 654, 435 ), imath.V2i( 1565, 1311 ) ) )
			self.assertEqual( singlePartReader["out"].dataWindow( "default" ), imath.Box2i( imath.V2i( 654, 435 ), imath.V2i( 1565, 1311 ) ) )

			# The single part file must have a data window encompassing both views, so we ignore the
			# data window when comparing
			self.assertImagesEqual( multiPartReader["out"], singlePartReader["out"], metadataBlacklist = [ "openexr:chunkCount" ], ignoreChannelNamesOrder = True, ignoreDataWindow = True )

if __name__ == "__main__":
	unittest.main()
