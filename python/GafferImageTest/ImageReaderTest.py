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

class ImageReaderTest( GafferTest.TestCase ) :

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

		n = GafferImage.ImageReader()
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

		n = GafferImage.ImageReader()
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

		n = GafferImage.ImageReader()
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

		n = GafferImage.ImageReader()
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

		n = GafferImage.ImageReader()
		n["fileName"].setValue( self.fileName )

		tile = n["out"].channelData( "R", IECore.V2i( 0 ) )
		self.assertEqual( len( tile ), GafferImage.ImagePlug().tileSize() **2 )

	def testNoCaching( self ) :

		n = GafferImage.ImageReader()
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

		n = GafferImage.ImageReader()
		n["out"]["channelNames"].getValue()
		n["out"].channelData( "R", IECore.V2i( 0 ) )

	def testNoOIIOErrorBufferOverflows( self ) :

		n = GafferImage.ImageReader()
		n["fileName"].setValue( "thisReallyReallyReallyReallyReallyReallyReallyReallyReallyLongFilenameDoesNotExist.tif" )

		for i in range( 0, 300000 ) :
			with IECore.IgnoredExceptions( Exception ) :
				n["out"]["dataWindow"].getValue()

	def testChannelDataHashes( self ) :
		# Test that two tiles within the same image have different hashes.
		n = GafferImage.ImageReader()
		n["fileName"].setValue( self.fileName )
		h1 = n["out"].channelData( "R", IECore.V2i( 0 ) ).hash()
		h2 = n["out"].channelData( "R", IECore.V2i( GafferImage.ImagePlug().tileSize() ) ).hash()

		self.assertNotEqual( h1, h2 )

	def testDisabledChannelDataHashes( self ) :
		# Test that two tiles within the same image have the same hash when disabled.
		n = GafferImage.ImageReader()
		n["fileName"].setValue( self.fileName )
		n["enabled"].setValue( False )
		h1 = n["out"].channelData( "R", IECore.V2i( 0 ) ).hash()
		h2 = n["out"].channelData( "R", IECore.V2i( GafferImage.ImagePlug().tileSize() ) ).hash()

		self.assertEqual( h1, h2 )

	def testOffsetDataWindowOrigin( self ) :

		n = GafferImage.ImageReader()
		n["fileName"].setValue( self.offsetDataWindowFileName )

		image = n["out"].image()
		image2 = IECore.Reader.create( self.offsetDataWindowFileName ).read()

		image.blindData().clear()
		image2.blindData().clear()

		self.assertEqual( image, image2 )

	def testJpgRead( self ) :

		exrReader = GafferImage.ImageReader()
		exrReader["fileName"].setValue( self.circlesExrFileName )

		jpgReader = GafferImage.ImageReader()
		jpgReader["fileName"].setValue( self.circlesJpgFileName )
		## \todo This colorspace manipulation needs to be performed
		# automatically in the ImageReader.
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

		e = GafferImage.ImageReader.supportedExtensions()

		self.assertTrue( "exr" in e )
		self.assertTrue( "jpg" in e )
		self.assertTrue( "tif" in e )
		self.assertTrue( "png" in e )
		self.assertTrue( "cin" in e )
		self.assertTrue( "dpx" in e )

	def testFileRefresh( self ) :

		testFile = self.temporaryDirectory() + "/refresh.exr"
		shutil.copyfile( self.fileName, testFile )

		reader = GafferImage.ImageReader()
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

		reader = GafferImage.ImageReader()
		reader["fileName"].setValue( "wellIDontExist.exr" )

		self.assertRaisesRegexp( RuntimeError, ".*wellIDontExist.exr.*", reader["out"].image )
		self.assertRaisesRegexp( RuntimeError, ".*wellIDontExist.exr.*", reader["out"]["format"].getValue )
		self.assertRaisesRegexp( RuntimeError, ".*wellIDontExist.exr.*", reader["out"]["dataWindow"].getValue )
		self.assertRaisesRegexp( RuntimeError, ".*wellIDontExist.exr.*", reader["out"]["metadata"].getValue )
		self.assertRaisesRegexp( RuntimeError, ".*wellIDontExist.exr.*", reader["out"]["channelNames"].getValue )
		self.assertRaisesRegexp( RuntimeError, ".*wellIDontExist.exr.*", reader["out"].channelData, "R", IECore.V2i( 0 ) )

if __name__ == "__main__":
	unittest.main()
