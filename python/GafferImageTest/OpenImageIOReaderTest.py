##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
#  Copyright (c) 2013-2015, Image Engine Design Inc. All rights reserved.
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
import imath
import random
import six

import IECore
import IECoreImage

import Gaffer
import GafferTest
import GafferImage
import GafferImageTest

class OpenImageIOReaderTest( GafferImageTest.ImageTestCase ) :

	fileName = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/checker.exr" )
	offsetDataWindowFileName = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/rgb.100x100.exr" )
	negativeDataWindowFileName = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/checkerWithNegativeDataWindow.200x150.exr" )
	negativeDisplayWindowFileName = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/negativeDisplayWindow.exr" )
	circlesExrFileName = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/circles.exr" )
	circlesJpgFileName = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/circles.jpg" )
	alignmentTestSourceFileName = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/colorbars_half_max.exr" )
	multipartFileName = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/multipart.exr" )
	unsupportedMultipartFileName = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/unsupportedMultipart.exr" )
	multipartDefaultChannelsFileName = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/multipartDefaultChannels.exr" )
	multipartDefaultChannelsOverlapFileName = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/multipartDefaultChannelsOverlap.exr" )

	def testInternalImageSpaceConversion( self ) :

		r = IECore.Reader.create( self.negativeDataWindowFileName )
		image = r.read()
		exrDisplayWindow = image.displayWindow
		exrDataWindow = image.dataWindow

		n = GafferImage.OpenImageIOReader()
		n["fileName"].setValue( self.negativeDataWindowFileName )
		gafferFormat = n["out"]["format"].getValue()

		self.assertEqual(
			gafferFormat.toEXRSpace( gafferFormat.getDisplayWindow() ),
			exrDisplayWindow,
		)

		self.assertEqual(
			gafferFormat.toEXRSpace( n["out"]["dataWindow"].getValue() ),
			exrDataWindow,
		)

	def test( self ) :

		n = GafferImage.OpenImageIOReader()
		n["fileName"].setValue( self.fileName )

		self.assertEqual( n["out"]["dataWindow"].getValue(), imath.Box2i( imath.V2i( 0 ), imath.V2i( 200, 150 ) ) )
		self.assertEqual( n["out"]["format"].getValue().getDisplayWindow(), imath.Box2i( imath.V2i( 0 ), imath.V2i( 200, 150 ) ) )

		expectedMetadata = IECore.CompoundData( {
			"oiio:ColorSpace" : IECore.StringData( 'Linear' ),
			"compression" : IECore.StringData( 'zips' ),
			"PixelAspectRatio" : IECore.FloatData( 1 ),
			"screenWindowCenter" : IECore.V2fData( imath.V2f( 0, 0 ) ),
			"screenWindowWidth" : IECore.FloatData( 1 ),
			"fileFormat" : IECore.StringData( "openexr" ),
			"dataType" : IECore.StringData( "float" ),
		} )

		self.assertEqual( n["out"]["metadata"].getValue(), expectedMetadata )

		channelNames = n["out"]["channelNames"].getValue()
		self.assertIsInstance( channelNames, IECore.StringVectorData )
		self.assertIn( "R", channelNames )
		self.assertIn( "G", channelNames )
		self.assertIn( "B", channelNames )
		self.assertIn( "A", channelNames )

		image = GafferImage.ImageAlgo.image( n["out"] )
		self.assertEqual( image.blindData(), IECore.CompoundData( dict(expectedMetadata) ) )

		image2 = IECore.Reader.create( self.fileName ).read()
		image.blindData().clear()
		image2.blindData().clear()
		self.assertEqual( image, image2 )

	def testNegativeDisplayWindowRead( self ) :

		n = GafferImage.OpenImageIOReader()
		n["fileName"].setValue( self.negativeDisplayWindowFileName )
		f = n["out"]["format"].getValue()
		d = n["out"]["dataWindow"].getValue()
		self.assertEqual( f.getDisplayWindow(), imath.Box2i( imath.V2i( -5, -5 ), imath.V2i( 21, 21 ) ) )
		self.assertEqual( d, imath.Box2i( imath.V2i( 2, -14 ), imath.V2i( 36, 20 ) ) )

		expectedImage = IECore.Reader.create( self.negativeDisplayWindowFileName ).read()
		outImage = GafferImage.ImageAlgo.image( n["out"] )
		expectedImage.blindData().clear()
		outImage.blindData().clear()
		self.assertEqual( expectedImage, outImage )

	def testNegativeDataWindow( self ) :

		n = GafferImage.OpenImageIOReader()
		n["fileName"].setValue( self.negativeDataWindowFileName )
		self.assertEqual( n["out"]["dataWindow"].getValue(), imath.Box2i( imath.V2i( -25, -30 ), imath.V2i( 175, 120 ) ) )
		self.assertEqual( n["out"]["format"].getValue().getDisplayWindow(), imath.Box2i( imath.V2i( 0 ), imath.V2i( 200, 150 ) ) )

		channelNames = n["out"]["channelNames"].getValue()
		self.assertIsInstance( channelNames, IECore.StringVectorData )
		self.assertIn( "R", channelNames )
		self.assertIn( "G", channelNames )
		self.assertIn( "B", channelNames )

		image = GafferImage.ImageAlgo.image( n["out"] )
		image2 = IECore.Reader.create( self.negativeDataWindowFileName ).read()

		op = IECoreImage.ImageDiffOp()
		res = op(
			imageA = image,
			imageB = image2
		)
		self.assertFalse( res.value )

	def testTileSize( self ) :

		n = GafferImage.OpenImageIOReader()
		n["fileName"].setValue( self.fileName )

		tile = n["out"].channelData( "R", imath.V2i( 0 ) )
		self.assertEqual( len( tile ), GafferImage.ImagePlug().tileSize() **2 )

	def testUnspecifiedFilename( self ) :

		n = GafferImage.OpenImageIOReader()
		n["out"]["channelNames"].getValue()
		n["out"].channelData( "R", imath.V2i( 0 ) )

	def testChannelDataHashes( self ) :
		# Test that two tiles within the same image have different hashes.
		n = GafferImage.OpenImageIOReader()
		n["fileName"].setValue( self.fileName )
		h1 = n["out"].channelData( "R", imath.V2i( 0 ) ).hash()
		h2 = n["out"].channelData( "R", imath.V2i( GafferImage.ImagePlug().tileSize() ) ).hash()

		self.assertNotEqual( h1, h2 )

	def testDisabledChannelDataHashes( self ) :
		# Test that two tiles within the same image have the same hash when disabled.
		n = GafferImage.OpenImageIOReader()
		n["fileName"].setValue( self.fileName )
		n["enabled"].setValue( False )
		h1 = n["out"].channelData( "R", imath.V2i( 0 ) ).hash()
		h2 = n["out"].channelData( "R", imath.V2i( GafferImage.ImagePlug().tileSize() ) ).hash()

		self.assertEqual( h1, h2 )

	def testOffsetDataWindowOrigin( self ) :

		n = GafferImage.OpenImageIOReader()
		n["fileName"].setValue( self.offsetDataWindowFileName )

		image = GafferImage.ImageAlgo.image( n["out"] )
		image2 = IECore.Reader.create( self.offsetDataWindowFileName ).read()

		image.blindData().clear()
		image2.blindData().clear()

		self.assertEqual( image, image2 )

	def testJpgRead( self ) :

		exrReader = GafferImage.OpenImageIOReader()
		exrReader["fileName"].setValue( self.circlesExrFileName )

		jpgReader = GafferImage.OpenImageIOReader()
		jpgReader["fileName"].setValue( self.circlesJpgFileName )
		jpgOCIO = GafferImage.ColorSpace()
		jpgOCIO["in"].setInput( jpgReader["out"] )
		jpgOCIO["inputSpace"].setValue( "sRGB" )
		jpgOCIO["outputSpace"].setValue( "linear" )

		self.assertImagesEqual( exrReader["out"], jpgOCIO["out"], ignoreMetadata = True, maxDifference = 0.001 )

	def testSupportedExtensions( self ) :

		e = GafferImage.OpenImageIOReader.supportedExtensions()

		self.assertTrue( "exr" in e )
		self.assertTrue( "jpg" in e )
		self.assertTrue( "tif" in e )
		self.assertTrue( "png" in e )
		self.assertTrue( "cin" in e )
		self.assertTrue( "dpx" in e )

	def testFileRefresh( self ) :

		testFile = self.temporaryDirectory() + "/refresh.exr"
		shutil.copyfile( self.fileName, testFile )

		reader = GafferImage.OpenImageIOReader()
		reader["fileName"].setValue( testFile )
		image1 = GafferImage.ImageAlgo.image( reader["out"] )

		# even though we've change the image on disk, gaffer will
		# still have the old one in its cache.
		shutil.copyfile( self.offsetDataWindowFileName, testFile )
		self.assertEqual( GafferImage.ImageAlgo.image( reader["out"] ), image1 )

		# until we force a refresh
		reader["refreshCount"].setValue( reader["refreshCount"].getValue() + 1 )
		self.assertNotEqual( GafferImage.ImageAlgo.image( reader["out"] ), image1 )

	def testNonexistentFiles( self ) :

		reader = GafferImage.OpenImageIOReader()
		reader["fileName"].setValue( "wellIDontExist.exr" )

		six.assertRaisesRegex( self, RuntimeError, ".*wellIDontExist.exr.*", reader["out"]["format"].getValue )
		six.assertRaisesRegex( self, RuntimeError, ".*wellIDontExist.exr.*", reader["out"]["dataWindow"].getValue )
		six.assertRaisesRegex( self, RuntimeError, ".*wellIDontExist.exr.*", reader["out"]["metadata"].getValue )
		six.assertRaisesRegex( self, RuntimeError, ".*wellIDontExist.exr.*", reader["out"]["channelNames"].getValue )
		six.assertRaisesRegex( self, RuntimeError, ".*wellIDontExist.exr.*", reader["out"].channelData, "R", imath.V2i( 0 ) )
		six.assertRaisesRegex( self, RuntimeError, ".*wellIDontExist.exr.*", GafferImage.ImageAlgo.image, reader["out"] )

	def testAvailableFrames( self ) :

		testSequence = IECore.FileSequence( self.temporaryDirectory() + "/incompleteSequence.####.exr" )
		shutil.copyfile( self.fileName, testSequence.fileNameForFrame( 1 ) )
		shutil.copyfile( self.offsetDataWindowFileName, testSequence.fileNameForFrame( 3 ) )

		reader = GafferImage.OpenImageIOReader()
		reader["fileName"].setValue( testSequence.fileName )

		self.assertEqual( reader["availableFrames"].getValue(), IECore.IntVectorData( [ 1, 3 ] ) )

		# it doesn't update until we refresh
		shutil.copyfile( self.offsetDataWindowFileName, testSequence.fileNameForFrame( 5 ) )
		self.assertEqual( reader["availableFrames"].getValue(), IECore.IntVectorData( [ 1, 3 ] ) )
		reader["refreshCount"].setValue( reader["refreshCount"].getValue() + 1 )
		self.assertEqual( reader["availableFrames"].getValue(), IECore.IntVectorData( [ 1, 3, 5 ] ) )

		# explicit file paths aren't considered a sequence
		reader["fileName"].setValue( self.fileName )
		self.assertEqual( reader["availableFrames"].getValue(), IECore.IntVectorData( [] ) )
		reader["fileName"].setValue( testSequence.fileNameForFrame( 1 )  )
		self.assertEqual( reader["availableFrames"].getValue(), IECore.IntVectorData( [] ) )

	def testMissingFrameMode( self ) :

		testSequence = IECore.FileSequence( self.temporaryDirectory() + "/incompleteSequence.####.exr" )
		shutil.copyfile( self.fileName, testSequence.fileNameForFrame( 1 ) )
		shutil.copyfile( self.offsetDataWindowFileName, testSequence.fileNameForFrame( 3 ) )

		reader = GafferImage.OpenImageIOReader()
		reader["fileName"].setValue( testSequence.fileName )

		context = Gaffer.Context()

		# get frame 1 data for comparison
		context.setFrame( 1 )
		with context :
			f1Image = GafferImage.ImageAlgo.image( reader["out"] )
			f1Format = reader["out"]["format"].getValue()
			f1DataWindow = reader["out"]["dataWindow"].getValue()
			f1Metadata = reader["out"]["metadata"].getValue()
			f1ChannelNames = reader["out"]["channelNames"].getValue()
			f1Tile = reader["out"].channelData( "R", imath.V2i( 0 ) )

		# make sure the tile we're comparing isn't black
		# so we can tell if MissingFrameMode::Black is working.
		blackTile = IECore.FloatVectorData( [ 0 ] * GafferImage.ImagePlug.tileSize() * GafferImage.ImagePlug.tileSize() )
		self.assertNotEqual( f1Tile, blackTile )

		# set to a missing frame
		context.setFrame( 2 )

		# everything throws
		reader["missingFrameMode"].setValue( GafferImage.OpenImageIOReader.MissingFrameMode.Error )
		with context :
			six.assertRaisesRegex( self, RuntimeError, ".*incompleteSequence.*.exr.*", GafferImage.ImageAlgo.image, reader["out"] )
			six.assertRaisesRegex( self, RuntimeError, ".*incompleteSequence.*.exr.*", reader["out"]["format"].getValue )
			six.assertRaisesRegex( self, RuntimeError, ".*incompleteSequence.*.exr.*", reader["out"]["dataWindow"].getValue )
			six.assertRaisesRegex( self, RuntimeError, ".*incompleteSequence.*.exr.*", reader["out"]["metadata"].getValue )
			six.assertRaisesRegex( self, RuntimeError, ".*incompleteSequence.*.exr.*", reader["out"]["channelNames"].getValue )
			six.assertRaisesRegex( self, RuntimeError, ".*incompleteSequence.*.exr.*", reader["out"].channelData, "R", imath.V2i( 0 ) )

		# everything matches frame 1
		reader["missingFrameMode"].setValue( GafferImage.OpenImageIOReader.MissingFrameMode.Hold )
		with context :
			self.assertEqual( GafferImage.ImageAlgo.image( reader["out"] ), f1Image )
			self.assertEqual( reader["out"]["format"].getValue(), f1Format )
			self.assertEqual( reader["out"]["dataWindow"].getValue(), f1DataWindow )
			self.assertEqual( reader["out"]["metadata"].getValue(), f1Metadata )
			self.assertEqual( reader["out"]["channelNames"].getValue(), f1ChannelNames )
			self.assertEqual( reader["out"].channelData( "R", imath.V2i( 0 ) ), f1Tile )

		# the windows match frame 1, but everything else is default
		reader["missingFrameMode"].setValue( GafferImage.OpenImageIOReader.MissingFrameMode.Black )
		with context :
			self.assertNotEqual( GafferImage.ImageAlgo.image( reader["out"] ), f1Image )
			self.assertEqual( reader["out"]["format"].getValue(), f1Format )
			self.assertEqual( reader["out"]["dataWindow"].getValue(), reader["out"]["dataWindow"].defaultValue() )
			self.assertEqual( reader["out"]["metadata"].getValue(), reader["out"]["metadata"].defaultValue() )
			self.assertEqual( reader["out"]["channelNames"].getValue(), reader["out"]["channelNames"].defaultValue() )
			self.assertEqual( reader["out"].channelData( "R", imath.V2i( 0 ) ), blackTile )

		# get frame 3 data for comparison
		context.setFrame( 3 )
		with context :
			f3Image = GafferImage.ImageAlgo.image( reader["out"] )
			f3Format = reader["out"]["format"].getValue()
			f3DataWindow = reader["out"]["dataWindow"].getValue()
			f3Metadata = reader["out"]["metadata"].getValue()
			f3ChannelNames = reader["out"]["channelNames"].getValue()
			f3Tile = reader["out"].channelData( "R", imath.V2i( 0 ) )

		# set to a different missing frame
		context.setFrame( 4 )

		# everything matches frame 3
		reader["missingFrameMode"].setValue( GafferImage.OpenImageIOReader.MissingFrameMode.Hold )
		with context :
			self.assertNotEqual( GafferImage.ImageAlgo.image( reader["out"] ), f1Image )
			self.assertNotEqual( reader["out"]["format"].getValue(), f1Format )
			self.assertNotEqual( reader["out"]["dataWindow"].getValue(), f1DataWindow )
			self.assertNotEqual( reader["out"]["metadata"].getValue(), f1Metadata )
			# same channel names is fine
			self.assertEqual( reader["out"]["channelNames"].getValue(), f1ChannelNames )
			self.assertNotEqual( reader["out"].channelData( "R", imath.V2i( 0 ) ), f1Tile )
			self.assertEqual( GafferImage.ImageAlgo.image( reader["out"] ), f3Image )
			self.assertEqual( reader["out"]["format"].getValue(), f3Format )
			self.assertEqual( reader["out"]["dataWindow"].getValue(), f3DataWindow )
			self.assertEqual( reader["out"]["metadata"].getValue(), f3Metadata )
			self.assertEqual( reader["out"]["channelNames"].getValue(), f3ChannelNames )
			self.assertEqual( reader["out"].channelData( "R", imath.V2i( 0 ) ), f3Tile )

		# the windows match frame 3, but everything else is default
		reader["missingFrameMode"].setValue( GafferImage.OpenImageIOReader.MissingFrameMode.Black )
		with context :
			self.assertNotEqual( reader["out"]["format"].getValue(), f1Format )
			self.assertEqual( reader["out"]["format"].getValue(), f3Format )
			self.assertEqual( reader["out"]["dataWindow"].getValue(), reader["out"]["dataWindow"].defaultValue() )
			self.assertEqual( reader["out"]["metadata"].getValue(), reader["out"]["metadata"].defaultValue() )
			self.assertEqual( reader["out"]["channelNames"].getValue(), reader["out"]["channelNames"].defaultValue() )
			self.assertEqual( reader["out"].channelData( "R", imath.V2i( 0 ) ), blackTile )

		# set to a missing frame before the start of the sequence
		context.setFrame( 0 )

		# everything matches frame 1
		reader["missingFrameMode"].setValue( GafferImage.OpenImageIOReader.MissingFrameMode.Hold )
		with context :
			self.assertEqual( GafferImage.ImageAlgo.image( reader["out"] ), f1Image )
			self.assertEqual( reader["out"]["format"].getValue(), f1Format )
			self.assertEqual( reader["out"]["dataWindow"].getValue(), f1DataWindow )
			self.assertEqual( reader["out"]["metadata"].getValue(), f1Metadata )
			self.assertEqual( reader["out"].channelData( "R", imath.V2i( 0 ) ), f1Tile )

		# the windows match frame 1, but everything else is default
		reader["missingFrameMode"].setValue( GafferImage.OpenImageIOReader.MissingFrameMode.Black )
		with context :
			self.assertEqual( reader["out"]["format"].getValue(), f1Format )
			self.assertEqual( reader["out"]["dataWindow"].getValue(), reader["out"]["dataWindow"].defaultValue() )
			self.assertEqual( reader["out"]["metadata"].getValue(), reader["out"]["metadata"].defaultValue() )
			self.assertEqual( reader["out"]["channelNames"].getValue(), reader["out"]["channelNames"].defaultValue() )
			self.assertEqual( reader["out"].channelData( "R", imath.V2i( 0 ) ), blackTile )

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
		with context :
			six.assertRaisesRegex( self, RuntimeError, ".*incompleteSequence.*.exr.*", GafferImage.ImageAlgo.image, reader["out"] )
			six.assertRaisesRegex( self, RuntimeError, ".*incompleteSequence.*.exr.*", reader["out"]["format"].getValue )
			self.assertEqual( reader["out"]["dataWindow"].getValue(), reader["out"]["dataWindow"].defaultValue() )
			self.assertEqual( reader["out"]["metadata"].getValue(), reader["out"]["metadata"].defaultValue() )
			self.assertEqual( reader["out"]["channelNames"].getValue(), reader["out"]["channelNames"].defaultValue() )
			self.assertEqual( reader["out"].channelData( "R", imath.V2i( 0 ) ), blackTile )

	def testHashesFrame( self ) :

		# the fileName excludes FrameSubstitutions, but
		# the internal implementation can still rely on
		# frame, so we need to check that the output
		# still responds to frame changes.

		testSequence = IECore.FileSequence( self.temporaryDirectory() + "/incompleteSequence.####.exr" )
		shutil.copyfile( self.fileName, testSequence.fileNameForFrame( 0 ) )
		shutil.copyfile( self.offsetDataWindowFileName, testSequence.fileNameForFrame( 1 ) )

		reader = GafferImage.OpenImageIOReader()
		reader["fileName"].setValue( testSequence.fileName )

		context = Gaffer.Context()

		# get frame 0 data for comparison
		context.setFrame( 0 )
		with context :
			sequenceMetadataHash = reader["out"]["metadata"].hash()
			sequenceMetadataValue = reader["out"]["metadata"].getValue()

		context.setFrame( 1 )
		with context :
			self.assertNotEqual( reader["out"]["metadata"].hash(), sequenceMetadataHash )
			self.assertNotEqual( reader["out"]["metadata"].getValue(), sequenceMetadataValue )

		# but when we set an explicit fileName,
		# we no longer re-compute per frame.
		reader["fileName"].setValue( testSequence.fileNameForFrame( 0 ) )

		# get frame 0 data for comparison
		context.setFrame( 0 )
		with context :
			explicitMetadataHash = reader["out"]["metadata"].hash()
			self.assertNotEqual( explicitMetadataHash, sequenceMetadataHash )
			self.assertEqual( reader["out"]["metadata"].getValue(), sequenceMetadataValue )

		context.setFrame( 1 )
		with context :
			self.assertNotEqual( reader["out"]["metadata"].hash(), sequenceMetadataHash )
			self.assertEqual( reader["out"]["metadata"].hash(), explicitMetadataHash )
			self.assertEqual( reader["out"]["metadata"].getValue(), sequenceMetadataValue )

	def testFileFormatMetadata( self ) :

		r = GafferImage.OpenImageIOReader()

		r["fileName"].setValue( self.circlesJpgFileName )
		self.assertEqual( r["out"]["metadata"].getValue()["dataType"].value, "uint8" )
		self.assertEqual( r["out"]["metadata"].getValue()["fileFormat"].value, "jpeg" )

		r["fileName"].setValue( "${GAFFER_ROOT}/python/GafferImageTest/images/rgb.100x100.dpx" )
		self.assertEqual( r["out"]["metadata"].getValue()["dataType"].value, "uint10" )
		self.assertEqual( r["out"]["metadata"].getValue()["fileFormat"].value, "dpx" )

	def testOffsetAlignment( self ) :
		# Test a bunch of different data window alignments on disk.  This exercises code for reading
		# weirdly aligned scanlines and partial tiles

		tempFile = self.temporaryDirectory() + "/tempOffsetImage.exr"

		r = GafferImage.OpenImageIOReader()
		r["fileName"].setValue( self.alignmentTestSourceFileName )

		offsetOut = GafferImage.Offset()
		offsetOut["in"].setInput( r["out"] )

		w = GafferImage.ImageWriter()
		w["in"].setInput( offsetOut["out"] )
		w["fileName"].setValue( tempFile )

		rBack = GafferImage.OpenImageIOReader()
		rBack["fileName"].setValue( tempFile )

		offsetIn = GafferImage.Offset()
		offsetIn["in"].setInput( rBack["out"] )

		random.seed( 42 )
		offsets = [ imath.V2i(x,y) for x in [-1,0,1] for y in [-1, 0, 1] ] + [
			imath.V2i( random.randint( -32, 32 ), random.randint( -32, 32 ) ) for i in range( 10 ) ]

		for mode in [ GafferImage.ImageWriter.Mode.Scanline, GafferImage.ImageWriter.Mode.Tile ]:
			w['openexr']['mode'].setValue( mode )
			for offset in offsets:
				offsetOut['offset'].setValue( offset )
				offsetIn['offset'].setValue( -offset )

				w["task"].execute()
				rBack['refreshCount'].setValue( rBack['refreshCount'].getValue() + 1 )

				self.assertImagesEqual( r["out"], offsetIn["out"], ignoreMetadata = True )

	def testFileNameContext( self ) :

		s = Gaffer.ScriptNode()
		s["reader"] = GafferImage.OpenImageIOReader()

		s["expression"] = Gaffer.Expression()
		s["expression"].setExpression( 'parent["reader"]["fileName"] = "%s"' % self.fileName )

		with Gaffer.ContextMonitor( root = s["expression"] ) as cm :
			GafferImage.ImageAlgo.tiles( s["reader"]["out"] )

		self.assertEqual( set( cm.combinedStatistics().variableNames() ), set( ['frame', 'framesPerSecond'] ) )

	def testMultipartRead( self ) :

		rgbReader = GafferImage.OpenImageIOReader()
		rgbReader["fileName"].setValue( self.offsetDataWindowFileName )

		compareDelete = GafferImage.DeleteChannels()
		compareDelete["in"].setInput( rgbReader["out"] )

		# This test multipart file contains a "customRgb" subimage, a "customRgba" subimage,
		# and a "customDepth" subimage, with one channel named "Z" ( copied from the green
		# channel of our reference image. )
		# We don't use the subimage names "rgb", "rgba" or "depth", because we want to look
		# at channels which don't get automatically mapped to the default channel names.
		# ( see testDefaultChannelsMultipartRead for that )
		# The test file was created using this command:
		# > oiiotool rgb.100x100.exr --attrib "oiio:subimagename" customRgb -ch "R,G,B" rgb.100x100.exr --attrib "oiio:subimagename" customRgba rgb.100x100.exr --attrib "oiio:subimagename" customDepth --ch "G" --chnames "Z" --siappendall -o multipart.exr
		multipartReader = GafferImage.OpenImageIOReader()
		multipartReader["fileName"].setValue( self.multipartFileName )

		multipartShuffle = GafferImage.Shuffle()
		multipartShuffle["in"].setInput( multipartReader["out"] )

		multipartDelete = GafferImage.DeleteChannels()
		multipartDelete["in"].setInput( multipartShuffle["out"] )
		multipartDelete['channels'].setValue( "*.*" )

		self.assertEqual( set( multipartReader["out"]["channelNames"].getValue() ),
			set([ "customRgba.R", "customRgba.G", "customRgba.B", "customRgba.A", "customRgb.R", "customRgb.G", "customRgb.B", "customDepth.Z" ])
		)

		multipartShuffle["channels"].clearChildren()
		multipartShuffle["channels"].addChild( GafferImage.Shuffle.ChannelPlug( "R", "customRgba.R" ) )
		multipartShuffle["channels"].addChild( GafferImage.Shuffle.ChannelPlug( "G", "customRgba.G" ) )
		multipartShuffle["channels"].addChild( GafferImage.Shuffle.ChannelPlug( "B", "customRgba.B" ) )
		multipartShuffle["channels"].addChild( GafferImage.Shuffle.ChannelPlug( "A", "customRgba.A" ) )
		self.assertImagesEqual( compareDelete["out"], multipartDelete["out"], ignoreMetadata = True )

		multipartShuffle["channels"].clearChildren()
		multipartShuffle["channels"].addChild( GafferImage.Shuffle.ChannelPlug( "R", "customRgb.R" ) )
		multipartShuffle["channels"].addChild( GafferImage.Shuffle.ChannelPlug( "G", "customRgb.G" ) )
		multipartShuffle["channels"].addChild( GafferImage.Shuffle.ChannelPlug( "B", "customRgb.B" ) )
		compareDelete['channels'].setValue( "A" )
		self.assertImagesEqual( compareDelete["out"], multipartDelete["out"], ignoreMetadata = True )

		multipartShuffle["channels"].clearChildren()
		multipartShuffle["channels"].addChild( GafferImage.Shuffle.ChannelPlug( "G", "customDepth.Z" ) )
		compareDelete['channels'].setValue( "R B A" )
		self.assertImagesEqual( compareDelete["out"], multipartDelete["out"], ignoreMetadata = True )

	def testUnsupportedMultipartRead( self ) :

		rgbReader = GafferImage.OpenImageIOReader()
		rgbReader["fileName"].setValue( self.offsetDataWindowFileName )

		# This test multipart file contains a "rgba" subimage, and a second subimage with a
		# differing data window.  The second part can currently not be loaded, because Gaffer images
		# have a single data window for the whole image.
		#
		# In the future, should we union the data windows?  Are subimages with differing data windows common?
		# This would probably happen with stereo images, but we should probably put work into handling stereo
		# images differently - with a context variable to control which eye we get, rather than loading everything
		# as channels.
		#
		# It was created using this command:
		# > oiiotool rgb.100x100.exr --attrib "oiio:subimagename" rgba checkerboard.100x100.exr --attrib "oiio:subimagename" fullDataWindow --siappendall -o unsupportedMultipart.exr
		multipartReader = GafferImage.OpenImageIOReader()
		multipartReader["fileName"].setValue( self.unsupportedMultipartFileName )

		# When we compare to the single part comparison file, the image will come out the same, because
		# the second part is ignored - and we should get a message about it being ignored
		with IECore.CapturingMessageHandler() as mh :
			self.assertImagesEqual( rgbReader["out"], multipartReader["out"], ignoreMetadata = True )

		self.assertEqual( len( mh.messages ), 1 )
		self.assertTrue( mh.messages[0].message.startswith( "Ignoring subimage 1 of " ) )

	def testDefaultChannelMultipartRead( self ) :

		# This test multipart file contains a "rgb" subimage with R, G, B channels, an "RGBA" subimage
		# with an A channel, and a "depth" subimage with a Z channel.
		# The standard would expect this to be loaded with channel names like "RGBA.A" and "depth.Z",
		# but in practice, applications expect these default layers to be loaded as the standard layer
		# names, so we conform to this pratical expection, and just name the channels R, G, B, A, and Z
		# The test file was created with this command
		# > oiiotool --create 4x4 3 --addc 0.1,0.2,0.3 --attrib "oiio:subimagename" rgb -create 4x4 1 --chnames A --addc 0.4 --attrib "oiio:subimagename" RGBA -create 4x4 1 --chnames Z --addc 4.2 --attrib "oiio:subimagename" depth --siappendall -o multipartDefaultChannels.exr

		multipartReader = GafferImage.OpenImageIOReader()
		multipartReader["fileName"].setValue( self.multipartDefaultChannelsFileName )

		self.assertEqual( set( multipartReader["out"]["channelNames"].getValue() ),
			set([ "R", "G", "B", "A", "Z" ])
		)

		sampler = GafferImage.ImageSampler()
		sampler["image"].setInput( multipartReader["out"] )
		sampler["pixel"].setValue( imath.V2f( 2 ) )

		self.assertEqual( sampler["color"].getValue(), imath.Color4f( 0.1, 0.2, 0.3, 0.4 ) )

		sampler['channels'].setValue( IECore.StringVectorData( ["Z", "Z", "Z", "Z"] ) )

		self.assertEqual( sampler["color"].getValue(), imath.Color4f( 4.2 ) )

		# Similar sort of image, but this time is ambiguous because subimages "rgb" and "RGBA" both
		# define channels RGB.  This should trigger a warning, and take RGB from the first subimage,
		# but A from the second subimage, because it is only found there.
		# The test file was created with this command:
		# > oiiotool --create 4x4 3 --addc 0.1,0.2,0.3 --attrib "oiio:subimagename" rgb -create 4x4 4 --addc 0.4,0.5,0.6,0.7 --attrib "oiio:subimagename" RGBA --siappendall -o multipartDefaultChannelsOverlap.exr

		multipartReader["fileName"].setValue( self.multipartDefaultChannelsOverlapFileName )
		with IECore.CapturingMessageHandler() as mh :
			self.assertEqual( set( multipartReader["out"]["channelNames"].getValue() ),
				set([ "R", "G", "B", "A" ])
			)

		self.assertEqual( len( mh.messages ), 3 )
		self.assertTrue( mh.messages[0].message.startswith( 'Ignoring channel "R" in subimage "1"' ) )
		self.assertTrue( mh.messages[1].message.startswith( 'Ignoring channel "G" in subimage "1"' ) )
		self.assertTrue( mh.messages[2].message.startswith( 'Ignoring channel "B" in subimage "1"' ) )
		for i in range( 3 ):
			self.assertTrue( mh.messages[i].message.endswith( 'already in subimage "0".' ) )

		sampler['channels'].setToDefault()
		self.assertEqual( sampler["color"].getValue(), imath.Color4f( 0.1, 0.2, 0.3, 0.7 ) )

	def testDefaultFormatHash( self ) :

		r = GafferImage.OpenImageIOReader()

		with Gaffer.Context() as c :

			GafferImage.FormatPlug.setDefaultFormat( c, GafferImage.Format( 100, 200 ) )
			h1 = r["out"].formatHash()
			GafferImage.FormatPlug.setDefaultFormat( c, GafferImage.Format( 200, 300 ) )
			h2 = r["out"].formatHash()
			GafferImage.FormatPlug.setDefaultFormat( c, GafferImage.Format( 100, 300, 2.0 ) )
			h3 = r["out"].formatHash()
			GafferImage.FormatPlug.setDefaultFormat( c, GafferImage.Format( 100, 200 ) )
			h4 = r["out"].formatHash()

		self.assertNotEqual( h1, h2 )
		self.assertNotEqual( h1, h3 )
		self.assertNotEqual( h2, h3 )
		self.assertEqual( h1, h4 )

	def testOpenFilesLimit( self ) :

		l = GafferImage.OpenImageIOReader.getOpenFilesLimit()
		try :
			GafferImage.OpenImageIOReader.setOpenFilesLimit( l + 1 )
			self.assertEqual( GafferImage.OpenImageIOReader.getOpenFilesLimit(), l + 1 )
		finally :
			GafferImage.OpenImageIOReader.setOpenFilesLimit( l )

	def testSubimageMetadataNotLoaded( self ) :

		reader = GafferImage.ImageReader()
		reader["fileName"].setValue( "${GAFFER_ROOT}/python/GafferImageTest/images/multipart.exr" )
		metadata = reader["out"].metadata()

		self.assertNotIn( "name", metadata )
		self.assertNotIn( "oiio:subimagename", metadata )
		self.assertNotIn( "oiio:subimages", metadata )

if __name__ == "__main__":
	unittest.main()
