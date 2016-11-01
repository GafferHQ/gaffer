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

import IECore

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

	def testInternalImageSpaceConversion( self ) :

		r = IECore.EXRImageReader( self.negativeDataWindowFileName )
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

		self.assertEqual( n["out"]["dataWindow"].getValue(), IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 200, 150 ) ) )
		self.assertEqual( n["out"]["format"].getValue().getDisplayWindow(), IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 200, 150 ) ) )

		expectedMetadata = IECore.CompoundObject( {
			"oiio:ColorSpace" : IECore.StringData( 'Linear' ),
			"compression" : IECore.StringData( 'zips' ),
			"PixelAspectRatio" : IECore.FloatData( 1 ),
			"screenWindowCenter" : IECore.V2fData( IECore.V2f( 0, 0 ) ),
			"screenWindowWidth" : IECore.FloatData( 1 ),
		} )
		self.assertEqual( n["out"]["metadata"].getValue(), expectedMetadata )

		channelNames = n["out"]["channelNames"].getValue()
		self.failUnless( isinstance( channelNames, IECore.StringVectorData ) )
		self.failUnless( "R" in channelNames )
		self.failUnless( "G" in channelNames )
		self.failUnless( "B" in channelNames )
		self.failUnless( "A" in channelNames )

		image = n["out"].image()
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
		self.assertEqual( f.getDisplayWindow(), IECore.Box2i( IECore.V2i( -5, -5 ), IECore.V2i( 21, 21 ) ) )
		self.assertEqual( d, IECore.Box2i( IECore.V2i( 2, -14 ), IECore.V2i( 36, 20 ) ) )

		expectedImage = IECore.Reader.create( self.negativeDisplayWindowFileName ).read()
		outImage = n["out"].image()
		expectedImage.blindData().clear()
		outImage.blindData().clear()
		self.assertEqual( expectedImage, outImage )

	def testNegativeDataWindow( self ) :

		n = GafferImage.OpenImageIOReader()
		n["fileName"].setValue( self.negativeDataWindowFileName )
		self.assertEqual( n["out"]["dataWindow"].getValue(), IECore.Box2i( IECore.V2i( -25, -30 ), IECore.V2i( 175, 120 ) ) )
		self.assertEqual( n["out"]["format"].getValue().getDisplayWindow(), IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 200, 150 ) ) )

		channelNames = n["out"]["channelNames"].getValue()
		self.failUnless( isinstance( channelNames, IECore.StringVectorData ) )
		self.failUnless( "R" in channelNames )
		self.failUnless( "G" in channelNames )
		self.failUnless( "B" in channelNames )

		image = n["out"].image()
		image2 = IECore.Reader.create( self.negativeDataWindowFileName ).read()

		op = IECore.ImageDiffOp()
		res = op(
			imageA = image,
			imageB = image2
		)
		self.assertFalse( res.value )

	def testTileSize( self ) :

		n = GafferImage.OpenImageIOReader()
		n["fileName"].setValue( self.fileName )

		tile = n["out"].channelData( "R", IECore.V2i( 0 ) )
		self.assertEqual( len( tile ), GafferImage.ImagePlug().tileSize() **2 )

	def testNoCaching( self ) :

		n = GafferImage.OpenImageIOReader()
		n["fileName"].setValue( self.fileName )

		c = Gaffer.Context()
		c["image:channelName"] = "R"
		c["image:tileOrigin"] = IECore.V2i( 0 )
		with c :
			# using _copy=False is not recommended anywhere outside
			# of these tests.
			t1 = n["out"]["channelData"].getValue( _copy=False )
			t2 = n["out"]["channelData"].getValue( _copy=False )

		# we don't want the separate computations to result in the
		# same value, because the ImageReader has its own cache in
		# OIIO, so doing any caching on top of that would be wasteful.
		self.failIf( t1.isSame( t2 ) )

	def testUnspecifiedFilename( self ) :

		n = GafferImage.OpenImageIOReader()
		n["out"]["channelNames"].getValue()
		n["out"].channelData( "R", IECore.V2i( 0 ) )

	def testNoOIIOErrorBufferOverflows( self ) :

		n = GafferImage.OpenImageIOReader()
		n["fileName"].setValue( "thisReallyReallyReallyReallyReallyReallyReallyReallyReallyLongFilenameDoesNotExist.tif" )

		for i in range( 0, 300000 ) :
			with IECore.IgnoredExceptions( Exception ) :
				n["out"]["dataWindow"].getValue()

	def testChannelDataHashes( self ) :
		# Test that two tiles within the same image have different hashes.
		n = GafferImage.OpenImageIOReader()
		n["fileName"].setValue( self.fileName )
		h1 = n["out"].channelData( "R", IECore.V2i( 0 ) ).hash()
		h2 = n["out"].channelData( "R", IECore.V2i( GafferImage.ImagePlug().tileSize() ) ).hash()

		self.assertNotEqual( h1, h2 )

	def testDisabledChannelDataHashes( self ) :
		# Test that two tiles within the same image have the same hash when disabled.
		n = GafferImage.OpenImageIOReader()
		n["fileName"].setValue( self.fileName )
		n["enabled"].setValue( False )
		h1 = n["out"].channelData( "R", IECore.V2i( 0 ) ).hash()
		h2 = n["out"].channelData( "R", IECore.V2i( GafferImage.ImagePlug().tileSize() ) ).hash()

		self.assertEqual( h1, h2 )

	def testOffsetDataWindowOrigin( self ) :

		n = GafferImage.OpenImageIOReader()
		n["fileName"].setValue( self.offsetDataWindowFileName )

		image = n["out"].image()
		image2 = IECore.Reader.create( self.offsetDataWindowFileName ).read()

		image.blindData().clear()
		image2.blindData().clear()

		self.assertEqual( image, image2 )

	def testJpgRead( self ) :

		exrReader = GafferImage.OpenImageIOReader()
		exrReader["fileName"].setValue( self.circlesExrFileName )

		jpgReader = GafferImage.OpenImageIOReader()
		jpgReader["fileName"].setValue( self.circlesJpgFileName )
		jpgOCIO = GafferImage.OpenColorIO()
		jpgOCIO["in"].setInput( jpgReader["out"] )
		jpgOCIO["inputSpace"].setValue( "sRGB" )
		jpgOCIO["outputSpace"].setValue( "linear" )

		exrImage = exrReader["out"].image()
		jpgImage = jpgOCIO["out"].image()

		exrImage.blindData().clear()
		jpgImage.blindData().clear()

		imageDiffOp = IECore.ImageDiffOp()
		res = imageDiffOp(
			imageA = exrImage,
			imageB = jpgImage,
		)
		self.assertFalse( res.value )

	def testOIIOJpgRead( self ) :

		# call through to c++ test.
		GafferImageTest.testOIIOJpgRead()

	def testOIIOExrRead( self ) :

		# call through to c++ test.
		GafferImageTest.testOIIOExrRead()

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
		image1 = reader["out"].image()

		# even though we've change the image on disk, gaffer will
		# still have the old one in its cache.
		shutil.copyfile( self.offsetDataWindowFileName, testFile )
		self.assertEqual( reader["out"].image(), image1 )

		# until we force a refresh
		reader["refreshCount"].setValue( reader["refreshCount"].getValue() + 1 )
		self.assertNotEqual( reader["out"].image(), image1 )

	def testNonexistentFiles( self ) :

		reader = GafferImage.OpenImageIOReader()
		reader["fileName"].setValue( "wellIDontExist.exr" )

		self.assertRaisesRegexp( RuntimeError, ".*wellIDontExist.exr.*", reader["out"].image )
		self.assertRaisesRegexp( RuntimeError, ".*wellIDontExist.exr.*", reader["out"]["format"].getValue )
		self.assertRaisesRegexp( RuntimeError, ".*wellIDontExist.exr.*", reader["out"]["dataWindow"].getValue )
		self.assertRaisesRegexp( RuntimeError, ".*wellIDontExist.exr.*", reader["out"]["metadata"].getValue )
		self.assertRaisesRegexp( RuntimeError, ".*wellIDontExist.exr.*", reader["out"]["channelNames"].getValue )
		self.assertRaisesRegexp( RuntimeError, ".*wellIDontExist.exr.*", reader["out"].channelData, "R", IECore.V2i( 0 ) )

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
			f1Image = reader["out"].image()
			f1Format = reader["out"]["format"].getValue()
			f1DataWindow = reader["out"]["dataWindow"].getValue()
			f1Metadata = reader["out"]["metadata"].getValue()
			f1ChannelNames = reader["out"]["channelNames"].getValue()
			f1Tile = reader["out"].channelData( "R", IECore.V2i( 0 ) )

		# make sure the tile we're comparing isn't black
		# so we can tell if MissingFrameMode::Black is working.
		blackTile = IECore.FloatVectorData( [ 0 ] * GafferImage.ImagePlug.tileSize() * GafferImage.ImagePlug.tileSize() )
		self.assertNotEqual( f1Tile, blackTile )

		# set to a missing frame
		context.setFrame( 2 )

		# everything throws
		reader["missingFrameMode"].setValue( GafferImage.OpenImageIOReader.MissingFrameMode.Error )
		with context :
			self.assertRaisesRegexp( RuntimeError, ".*incompleteSequence.*.exr.*", reader["out"].image )
			self.assertRaisesRegexp( RuntimeError, ".*incompleteSequence.*.exr.*", reader["out"]["format"].getValue )
			self.assertRaisesRegexp( RuntimeError, ".*incompleteSequence.*.exr.*", reader["out"]["dataWindow"].getValue )
			self.assertRaisesRegexp( RuntimeError, ".*incompleteSequence.*.exr.*", reader["out"]["metadata"].getValue )
			self.assertRaisesRegexp( RuntimeError, ".*incompleteSequence.*.exr.*", reader["out"]["channelNames"].getValue )
			self.assertRaisesRegexp( RuntimeError, ".*incompleteSequence.*.exr.*", reader["out"].channelData, "R", IECore.V2i( 0 ) )

		# everything matches frame 1
		reader["missingFrameMode"].setValue( GafferImage.OpenImageIOReader.MissingFrameMode.Hold )
		with context :
			self.assertEqual( reader["out"].image(), f1Image )
			self.assertEqual( reader["out"]["format"].getValue(), f1Format )
			self.assertEqual( reader["out"]["dataWindow"].getValue(), f1DataWindow )
			self.assertEqual( reader["out"]["metadata"].getValue(), f1Metadata )
			self.assertEqual( reader["out"]["channelNames"].getValue(), f1ChannelNames )
			self.assertEqual( reader["out"].channelData( "R", IECore.V2i( 0 ) ), f1Tile )

		# the windows match frame 1, but everything else is default
		reader["missingFrameMode"].setValue( GafferImage.OpenImageIOReader.MissingFrameMode.Black )
		with context :
			self.assertNotEqual( reader["out"].image(), f1Image )
			self.assertEqual( reader["out"]["format"].getValue(), f1Format )
			self.assertEqual( reader["out"]["dataWindow"].getValue(), reader["out"]["dataWindow"].defaultValue() )
			self.assertEqual( reader["out"]["metadata"].getValue(), reader["out"]["metadata"].defaultValue() )
			self.assertEqual( reader["out"]["channelNames"].getValue(), reader["out"]["channelNames"].defaultValue() )
			self.assertEqual( reader["out"].channelData( "R", IECore.V2i( 0 ) ), blackTile )

		# get frame 3 data for comparison
		context.setFrame( 3 )
		with context :
			f3Image = reader["out"].image()
			f3Format = reader["out"]["format"].getValue()
			f3DataWindow = reader["out"]["dataWindow"].getValue()
			f3Metadata = reader["out"]["metadata"].getValue()
			f3ChannelNames = reader["out"]["channelNames"].getValue()
			f3Tile = reader["out"].channelData( "R", IECore.V2i( 0 ) )

		# set to a different missing frame
		context.setFrame( 4 )

		# everything matches frame 3
		reader["missingFrameMode"].setValue( GafferImage.OpenImageIOReader.MissingFrameMode.Hold )
		with context :
			self.assertNotEqual( reader["out"].image(), f1Image )
			self.assertNotEqual( reader["out"]["format"].getValue(), f1Format )
			self.assertNotEqual( reader["out"]["dataWindow"].getValue(), f1DataWindow )
			self.assertNotEqual( reader["out"]["metadata"].getValue(), f1Metadata )
			# same channel names is fine
			self.assertEqual( reader["out"]["channelNames"].getValue(), f1ChannelNames )
			self.assertNotEqual( reader["out"].channelData( "R", IECore.V2i( 0 ) ), f1Tile )
			self.assertEqual( reader["out"].image(), f3Image )
			self.assertEqual( reader["out"]["format"].getValue(), f3Format )
			self.assertEqual( reader["out"]["dataWindow"].getValue(), f3DataWindow )
			self.assertEqual( reader["out"]["metadata"].getValue(), f3Metadata )
			self.assertEqual( reader["out"]["channelNames"].getValue(), f3ChannelNames )
			self.assertEqual( reader["out"].channelData( "R", IECore.V2i( 0 ) ), f3Tile )

		# the windows match frame 3, but everything else is default
		reader["missingFrameMode"].setValue( GafferImage.OpenImageIOReader.MissingFrameMode.Black )
		with context :
			self.assertNotEqual( reader["out"]["format"].getValue(), f1Format )
			self.assertEqual( reader["out"]["format"].getValue(), f3Format )
			self.assertEqual( reader["out"]["dataWindow"].getValue(), reader["out"]["dataWindow"].defaultValue() )
			self.assertEqual( reader["out"]["metadata"].getValue(), reader["out"]["metadata"].defaultValue() )
			self.assertEqual( reader["out"]["channelNames"].getValue(), reader["out"]["channelNames"].defaultValue() )
			self.assertEqual( reader["out"].channelData( "R", IECore.V2i( 0 ) ), blackTile )

		# set to a missing frame before the start of the sequence
		context.setFrame( 0 )

		# everything matches frame 1
		reader["missingFrameMode"].setValue( GafferImage.OpenImageIOReader.MissingFrameMode.Hold )
		with context :
			self.assertEqual( reader["out"].image(), f1Image )
			self.assertEqual( reader["out"]["format"].getValue(), f1Format )
			self.assertEqual( reader["out"]["dataWindow"].getValue(), f1DataWindow )
			self.assertEqual( reader["out"]["metadata"].getValue(), f1Metadata )
			self.assertEqual( reader["out"].channelData( "R", IECore.V2i( 0 ) ), f1Tile )

		# the windows match frame 1, but everything else is default
		reader["missingFrameMode"].setValue( GafferImage.OpenImageIOReader.MissingFrameMode.Black )
		with context :
			self.assertEqual( reader["out"]["format"].getValue(), f1Format )
			self.assertEqual( reader["out"]["dataWindow"].getValue(), reader["out"]["dataWindow"].defaultValue() )
			self.assertEqual( reader["out"]["metadata"].getValue(), reader["out"]["metadata"].defaultValue() )
			self.assertEqual( reader["out"]["channelNames"].getValue(), reader["out"]["channelNames"].defaultValue() )
			self.assertEqual( reader["out"].channelData( "R", IECore.V2i( 0 ) ), blackTile )

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
		with context :
			self.assertRaisesRegexp( RuntimeError, ".*incompleteSequence.*.exr.*", reader["out"].image )
			self.assertRaisesRegexp( RuntimeError, ".*incompleteSequence.*.exr.*", reader["out"]["format"].getValue )
			self.assertEqual( reader["out"]["dataWindow"].getValue(), reader["out"]["dataWindow"].defaultValue() )
			self.assertEqual( reader["out"]["metadata"].getValue(), reader["out"]["metadata"].defaultValue() )
			self.assertEqual( reader["out"]["channelNames"].getValue(), reader["out"]["channelNames"].defaultValue() )
			self.assertEqual( reader["out"].channelData( "R", IECore.V2i( 0 ) ), blackTile )

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

	def testCacheLimits( self ) :

		l = GafferImage.OpenImageIOReader.getCacheMemoryLimit()
		self.addCleanup( GafferImage.OpenImageIOReader.setCacheMemoryLimit, l )

		GafferImage.OpenImageIOReader.setCacheMemoryLimit( 100 * 1024 * 1024 ) # 100 megs
		self.assertEqual( GafferImage.OpenImageIOReader.getCacheMemoryLimit(), 100 * 1024 * 1024 )

if __name__ == "__main__":
	unittest.main()
