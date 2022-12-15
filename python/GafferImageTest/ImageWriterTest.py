##########################################################################
#
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
import pathlib
import platform
import unittest
import shutil
import functools
import datetime
import re
import subprocess
import imath
import inspect

import IECore
import IECoreImage

import Gaffer
import GafferTest
import GafferDispatch
import GafferImage
import GafferImageTest

class ImageWriterTest( GafferImageTest.ImageTestCase ) :

	__largeFilePath = GafferImageTest.ImageTestCase.imagesPath() / "large.exr"
	__rgbFilePath = GafferImageTest.ImageTestCase.imagesPath() / "rgb.100x100.exr"
	__negativeDataWindowFilePath = GafferImageTest.ImageTestCase.imagesPath() / "checkerWithNegativeDataWindow.200x150.exr"
	__representativeDeepPath = GafferImageTest.ImageTestCase.imagesPath() / "representativeDeepImage.exr"

	longMessage = True

	def setUp( self ) :

		GafferImageTest.ImageTestCase.setUp( self )
		self.__defaultColorSpaceFunction = GafferImage.ImageWriter.getDefaultColorSpaceFunction()

	def tearDown( self ) :

		GafferImageTest.ImageTestCase.tearDown( self )
		GafferImage.ImageWriter.setDefaultColorSpaceFunction( self.__defaultColorSpaceFunction )

	# Test that we can select which channels to write.
	def testChannelMask( self ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.__rgbFilePath )

		testFile = self.__testFile( "default", "RB", "exr" )
		self.assertFalse( testFile.exists() )

		w = GafferImage.ImageWriter()
		w["in"].setInput( r["out"] )
		w["fileName"].setValue( testFile )
		w["channels"].setValue( "R B" )
		w["task"].execute()

		writerOutput = GafferImage.ImageReader()
		writerOutput["fileName"].setValue( testFile )

		channelNames = writerOutput["out"]["channelNames"].getValue()
		self.assertIn( "R", channelNames )
		self.assertNotIn( "G", channelNames )
		self.assertIn( "B", channelNames )
		self.assertNotIn( "A", channelNames )

	def testAcceptsInput( self ) :

		w = GafferImage.ImageWriter()
		p = GafferImage.ImagePlug( direction = Gaffer.Plug.Direction.Out )

		self.assertFalse( w["preTasks"][0].acceptsInput( p ) )
		self.assertTrue( w["in"].acceptsInput( p ) )

	def testTiffWrite( self ) :

		options = {}
		options['maxError'] = 0.0032
		options['metadata'] = { 'compression' : IECore.StringData( "zip" ), 'tiff:Compression' : IECore.IntData( 8 ) }
		options['plugs'] = {}
		options['plugs']['mode'] = [
				{ 'value': GafferImage.ImageWriter.Mode.Scanline },
				{ 'value': GafferImage.ImageWriter.Mode.Tile },
			]
		options['plugs']['compression'] = [
				{ 'value': "none", 'metadata' : { 'compression' : IECore.StringData( "none" ), 'tiff:Compression' : IECore.IntData( 1 ) } },
				{ 'value': "lzw", 'metadata' : { 'compression' : IECore.StringData( "lzw" ), 'tiff:Compression' : IECore.IntData( 5 ) } },
				{ 'value': "zip", 'metadata' : { 'compression' : IECore.StringData( "zip" ), 'tiff:Compression' : IECore.IntData( 8 ) } },
				{ 'value': "packbits", 'metadata' : { 'compression' : IECore.StringData( "packbits" ), 'tiff:Compression' : IECore.IntData( 32773 ) } },
			]
		options['plugs']['dataType'] = [
				{ 'value': "uint8", 'metadata': { 'oiio:BitsPerSample': IECore.IntData( 8 ) }, 'maxError': 0.0 },
				{ 'value': "uint16", 'metadata': { 'oiio:BitsPerSample': IECore.IntData( 16 ) } },
				{ 'value': "float", 'metadata': { 'oiio:BitsPerSample': IECore.IntData( 32 ) } },
			]

		self.__testExtension( "tif", "tiff", options = options, metadataToIgnore = [ "tiff:RowsPerStrip", "IPTC:Creator" ] )

	def testJpgWrite( self ) :

		# We can assert that we get a perfect match when using the default
		# compression (95), because that's what we generated the expected image
		# with.

		options = {}
		options['maxError'] = 0.0
		options['plugs'] = {}

		# But then we have to relax the maxError check when varying
		# the compression quality, because that puts the results all over
		# the map.

		options['plugs']['compressionQuality'] = [
			{ 'value': 10, "maxError" : 0.76 },
			{ 'value': 20, "maxError" : 0.74 },
			{ 'value': 30, "maxError" : 0.65 },
			{ 'value': 40, "maxError" : 0.60 },
			{ 'value': 50, "maxError" : 0.57 },
			{ 'value': 60, "maxError" : 0.56 },
			{ 'value': 70, "maxError" : 0.51 },
			{ 'value': 80, "maxError" : 0.29 },
			{ 'value': 90, "maxError" : 0.25 },
			{ 'value': 100, "maxError" : 0.05 },
		]

		self.__testExtension( "jpg", "jpeg", options = options, metadataToIgnore = [ "DocumentName", "HostComputer" ] )

	def testTgaWrite( self ) :

		## \todo We can currently round-trip targa images correctly
		# through ImageWriter/ImageReader in terms of colorspace management,
		# but not in terms of alpha premultiplication. The "expected" image
		# used by this test is therefore not technically correct - we need
		# to fix the alpha management and then update the test image. The
		# OIIO targa output plugin contains some comments that may be relevant
		# when addressing this - it seems they always premultiply on output
		# even if asked not to.

		options = {}
		options['maxError'] = 0.0
		options['plugs'] = {}
		options['plugs']['compression'] = [
				{ 'value': "none" },
				{ 'value': "rle" },
			]

		self.__testExtension( "tga", "targa", options = options, metadataToIgnore = [ "compression", "HostComputer", "Software" ] )

	def testExrWrite( self ) :
		options = {}
		options['maxError'] = 0.0
		options['metadata'] = { 'compression' : IECore.StringData( "zips" ) }
		options['plugs'] = {}
		options['plugs']['mode'] = [
				{ 'value': GafferImage.ImageWriter.Mode.Scanline },
				{ 'value': GafferImage.ImageWriter.Mode.Tile },
			]
		options['plugs']['compression'] = [
				{ 'value': "none", 'metadata' : { 'compression' : IECore.StringData( "none" ) } },
				{ 'value': "zip", 'metadata' : { 'compression' : IECore.StringData( "zip" ) } },
				{ 'value': "zips", 'metadata' : { 'compression' : IECore.StringData( "zips" ) } },
				{ 'value': "rle", 'metadata' : { 'compression' : IECore.StringData( "rle" ) } },
				{ 'value': "piz", 'metadata' : { 'compression' : IECore.StringData( "piz" ) } },
				{ 'value': "pxr24", 'metadata' : { 'compression' : IECore.StringData( "pxr24" ) } },
				{ 'value': "b44", 'metadata' : { 'compression' : IECore.StringData( "b44" ) } },
				{ 'value': "b44a", 'metadata' : { 'compression' : IECore.StringData( "b44a" ) } },
			]
		options['plugs']['dataType'] = [
				{ 'value': "float" },
				{ 'value': "half" },
			]

		self.__testExtension( "exr", "openexr", options = options )

	def testPngWrite( self ) :

		## \todo PNG read/write correctly roundtrips in terms
		# of colour management, but not in terms of alpha premultiplication.
		# The "expected" image is adjusted to account for this - fix it
		# and change the image. See similar comment in testTgaWrite.

		options = {}
		options['maxError'] = 0.0
		options['plugs'] = {}
		options['plugs']['compression'] = [
				{ 'value': "default" },
				{ 'value': "filtered" },
				{ 'value': "huffman" },
				{ 'value': "rle" },
				{ 'value': "fixed" },
			]
		options['plugs']['compressionLevel'] = [
				{ 'value': 0 },
				{ 'value': 1 },
				{ 'value': 2 },
				{ 'value': 3 },
				{ 'value': 4 },
				{ 'value': 5 },
				{ 'value': 6 },
				{ 'value': 7 },
				{ 'value': 8 },
				{ 'value': 9 },
			]

		self.__testExtension( "png", "png", options = options )

	# See issue #2125
	@unittest.expectedFailure
	def testDpxWrite( self ) :

		options = {}
		options['maxError'] = 0.007
		options['plugs'] = {}
		options['plugs']['dataType'] = [
				{ 'value': "uint8", 'metadata': { 'oiio:BitsPerSample': IECore.IntData( 8 ) } },
				{ 'value': "uint10" },
				{ 'value': "uint12", 'metadata': { 'oiio:BitsPerSample': IECore.IntData( 12 ), 'dpx:Packing': IECore.StringData( "Packed" ) } },
				{ 'value': "uint16", 'metadata': { 'oiio:BitsPerSample': IECore.IntData( 16 ) } },
			]

		self.__testExtension( "dpx", "dpx", options = options, metadataToIgnore = [ "Artist", "DocumentName", "HostComputer", "Software" ] )

	def testIffWrite( self ) :

		options = {}
		options['maxError'] = 0.0
		options['plugs'] = {}
		options['mode'] = [
				{ 'value': GafferImage.ImageWriter.Mode.Tile },
			]

		self.__testExtension( "iff", "iff", options = options, metadataToIgnore = [ "Artist", "DocumentName", "HostComputer", "Software" ] )

	def testDefaultFormatWrite( self ) :

		s = Gaffer.ScriptNode()
		s["c"] = GafferImage.Constant()
		s["w"] = GafferImage.ImageWriter()
		s["r"] = GafferImage.ImageReader()

		GafferImage.FormatPlug.acquireDefaultFormatPlug( s ).setValue(
			GafferImage.Format( imath.Box2i( imath.V2i( -7, -2 ), imath.V2i( 23, 25 ) ), 1. )
		)

		s["w"]["in"].setInput( s["c"]["out"] )
		s["w"]["fileName"].setValue( self.temporaryDirectory() / "test.exr" )
		s["r"]["fileName"].setInput( s["w"]["fileName"] )

		for mode in ( GafferImage.ImageWriter.Mode.Scanline, GafferImage.ImageWriter.Mode.Tile ) :

			s["r"]["refreshCount"].setValue( s["r"]["refreshCount"].getValue() + 1 )

			s["w"]["openexr"]["mode"].setValue( mode )
			with s.context() :
				s["w"]["task"].execute()
				self.assertImagesEqual( s["c"]["out"], s["r"]["out"], ignoreMetadata = True )

	def testDefaultFormatOptionPlugValues( self ) :
		w = GafferImage.ImageWriter()

		self.assertEqual( w["dpx"]["dataType"].getValue(), "uint10" )

		self.assertEqual( w["field3d"]["mode"].getValue(), GafferImage.ImageWriter.Mode.Scanline )
		self.assertEqual( w["field3d"]["dataType"].getValue(), "float" )

		self.assertEqual( w["fits"]["dataType"].getValue(), "float" )

		self.assertEqual( w["iff"]["mode"].getValue(), GafferImage.ImageWriter.Mode.Tile )

		self.assertEqual( w["jpeg"]["compressionQuality"].getValue(), 98 )

		self.assertEqual( w["jpeg2000"]["dataType"].getValue(), "uint8" )

		self.assertEqual( w["openexr"]["mode"].getValue(), GafferImage.ImageWriter.Mode.Scanline )
		self.assertEqual( w["openexr"]["compression"].getValue(), "zips" )
		self.assertEqual( w["openexr"]["dataType"].getValue(), "half" )

		self.assertEqual( w["png"]["compression"].getValue(), "filtered" )
		self.assertEqual( w["png"]["compressionLevel"].getValue(), 6 )

		self.assertEqual( w["rla"]["dataType"].getValue(), "uint8" )

		self.assertEqual( w["sgi"]["dataType"].getValue(), "uint8" )

		self.assertEqual( w["targa"]["compression"].getValue(), "rle" )

		self.assertEqual( w["tiff"]["mode"].getValue(), GafferImage.ImageWriter.Mode.Scanline )
		self.assertEqual( w["tiff"]["compression"].getValue(), "zip" )
		self.assertEqual( w["tiff"]["dataType"].getValue(), "uint8" )

		self.assertEqual( w["webp"]["compressionQuality"].getValue(), 100 )

	def testDeepWrite( self ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.__representativeDeepPath )

		c = GafferImage.Crop()
		c["in"].setInput( r["out"] )
		c["area"].setValue( imath.Box2i( imath.V2i( 0 ), imath.V2i( 64 ) ) )

		o = GafferImage.Offset()
		o["in"].setInput( c["out"] )

		testFile = self.__testFile( "deep", "RGBA", "exr" )

		w = GafferImage.ImageWriter()
		w['fileName'].setValue( testFile )
		w['in'].setInput( o['out'] )

		reRead = GafferImage.ImageReader()
		reRead["fileName"].setValue( testFile )

		# We don't currently have an explicit way of trimming to the dataWindow - any nodes that process the
		# data should do it, but crop may be passing through.  In order to be able to do an exact compare with
		# the round tripped data, we can do a little hack by offsetting back and forth by a pixel, to force
		# processing, which will trim to the dataWindow
		trimToDataWindowStage1 = GafferImage.Offset()
		trimToDataWindowStage1["in"].setInput( o["out"] )
		trimToDataWindowStage1["offset"].setValue( imath.V2i( 1, 0 ) )

		trimToDataWindowStage2 = GafferImage.Offset()
		trimToDataWindowStage2["in"].setInput( trimToDataWindowStage1["out"] )
		trimToDataWindowStage2["offset"].setValue( imath.V2i( -1, 0 ) )

		for mode in [ GafferImage.ImageWriter.Mode.Scanline, GafferImage.ImageWriter.Mode.Tile]:

			w["openexr"]["mode"].setValue( mode )

			for area, affectDisplayWindow in [
					( imath.Box2i( imath.V2i( 0 ), imath.V2i( 64 ) ), True ),
					( imath.Box2i( imath.V2i( 0 ), imath.V2i( 63 ) ), True ),
					( imath.Box2i( imath.V2i( 0 ), imath.V2i( 65 ) ), True ),
					( imath.Box2i( imath.V2i( 0 ), imath.V2i( 150, 100 ) ), True ),
					( imath.Box2i( imath.V2i( 37, 21 ), imath.V2i( 96, 43 ) ), False ),
					( imath.Box2i( imath.V2i( 0 ), imath.V2i( 0 ) ), False )
				]:
				c["area"].setValue( area )
				c["affectDisplayWindow"].setValue( affectDisplayWindow )

				for offset in [
						imath.V2i( 0, 0 ),
						imath.V2i( 13, 17 ),
						imath.V2i( -13, -17 ),
						imath.V2i( -233, 431 ),
						imath.V2i( -GafferImage.ImagePlug.tileSize(), 2 * GafferImage.ImagePlug.tileSize() ),
						imath.V2i( 106, 28 )
					]:

					o["offset"].setValue( offset )

					w["task"].execute()

					reRead["refreshCount"].setValue( reRead["refreshCount"].getValue() + 1 )
					if area.size() != imath.V2i( 0 ):
						self.assertImagesEqual( reRead["out"], trimToDataWindowStage2["out"], ignoreMetadata = True )
					else:
						# We have to write one pixel to file, since OpenEXR doesn't permit empty dataWindow
						onePixelDataWindow = imath.Box2i( imath.V2i( 0, 99 ), imath.V2i( 1, 100 ) )
						self.assertEqual( reRead["out"].dataWindow(), onePixelDataWindow )

						emptyPixelData = IECore.CompoundObject()
						emptyPixelData["tileOrigins"] = IECore.V2iVectorData( [ GafferImage.ImagePlug.tileOrigin( imath.V2i( 0, 99 ) ) ] )
						emptyPixelData["sampleOffsets"] = IECore.ObjectVector( [ GafferImage.ImagePlug.emptyTileSampleOffsets() ] )
						for channel in [ "R", "G","B", "A", "Z", "ZBack" ]:
							emptyPixelData[channel] = IECore.ObjectVector( [ IECore.FloatVectorData() ] )
						self.assertEqual( GafferImage.ImageAlgo.tiles( reRead["out"] ), emptyPixelData )

	# Write an RGBA image that has a data window to various supported formats and in both scanline and tile modes.
	def __testExtension( self, ext, formatName, options = {}, metadataToIgnore = [] ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.__rgbFilePath )
		expectedFile = self.__rgbFilePath.with_suffix( "." + ext )

		tests = [
			{
				'name': "default",
				'plugs': {},
				'metadata': options.get( "metadata", {} ),
				'maxError': options.get( "maxError", 0.0 )
			},
			{
				'name': "defaultNoAlpha",
				'removeAlpha': True,
				'plugs': {},
				'metadata': options.get( "metadata", {} ),
				# The expected images were written out with an alpha.  Removing two unpremults/premults from the
				# color space processing chain produces slightly different results ( in low precision file formats,
				# like PNG, this error accumulates to be a bit large )
				'maxError': 0.011
			}
		]

		for optPlugName in options['plugs'] :
			for optPlugVal in options['plugs'][optPlugName] :
				name = "{}_{}".format(optPlugName, optPlugVal['value'])
				optMetadata = dict(options.get( "metadata", {} ))
				optMetadata.update( optPlugVal.get( "metadata", {} ) )
				tests.append( {
					'name': name,
					'plugs': { optPlugName: optPlugVal['value'] },
					'metadata': optMetadata,
					'maxError': optPlugVal.get( "maxError", options['maxError'] ) } )

		for test in tests:

			name = test['name']
			maxError = test['maxError']
			overrideMetadata = test['metadata']
			testFile = self.__testFile( name, "RGBA", ext )
			removeAlpha = "removeAlpha" in test

			self.assertFalse( testFile.exists(), "Temporary file already exists : {}".format( testFile ) )

			# Setup the writer.
			w = GafferImage.ImageWriter()
			w["in"].setInput( r["out"] )
			w["fileName"].setValue( testFile )
			w["channels"].setValue( "[RGB]" if removeAlpha else "*" )

			for opt in test['plugs']:
				w[formatName][opt].setValue( test['plugs'][opt] )

			# Execute
			with Gaffer.Context() :
				w["task"].execute()
			self.assertTrue( testFile.exists(), "Failed to create file : {} ({}) : {}".format( ext, name, testFile ) )

			# Check the output.
			expectedOutput = GafferImage.ImageReader()
			expectedOutput["fileName"].setValue( expectedFile )

			writerOutput = GafferImage.ImageReader()
			writerOutput["fileName"].setValue( testFile )

			expectedMetadata = expectedOutput["out"]["metadata"].getValue()
			writerMetadata = writerOutput["out"]["metadata"].getValue()
			# they were written at different times so
			# we can't expect those values to match
			if "DateTime" in writerMetadata :
				expectedMetadata["DateTime"] = writerMetadata["DateTime"]

			# the writer adds several standard attributes that aren't in the original file
			expectedMetadata["Software"] = IECore.StringData( "Gaffer " + Gaffer.About.versionString() )
			expectedMetadata["HostComputer"] = IECore.StringData( platform.node() )
			expectedMetadata["Artist"] = IECore.StringData( os.environ.get("USER") or os.environ["USERNAME"] ) #Linux or windows
			expectedMetadata["DocumentName"] = IECore.StringData( "untitled" )

			for key in overrideMetadata :
				expectedMetadata[key] = overrideMetadata[key]

			if removeAlpha:
				# If we're not writing alpha, we can't expect to see OIIO's automatically added alpha type
				# metadata get read in.  This should be compatible with both current OIIO, and also in the
				# future once we upgrade to OIIO 2.3.12, and it gets renamed from tga: to targa:
				try:
					del expectedMetadata[ "tga:alpha_type" ]
				except:
					pass
				try:
					del expectedMetadata["targa:alpha_type" ]
				except:
					pass

			self.__addExpectedIPTCMetadata( writerMetadata, expectedMetadata )

			for metaName in expectedMetadata.keys() :
				if metaName in metadataToIgnore :
					continue
				if metaName in ( "fileFormat", "dataType" ) :
					# These are added on automatically by the ImageReader, and
					# we can't expect them to be the same when converting between
					# image formats.
					continue
				self.assertTrue( metaName in writerMetadata.keys(), "Writer Metadata missing expected key \"{}\" set to \"{}\" : {} ({})".format(metaName, str(expectedMetadata[metaName]), ext, name) )
				self.assertEqual( expectedMetadata[metaName], writerMetadata[metaName], "Metadata does not match for key \"{}\" : {} ({})".format(metaName, ext, name) )

			# OIIO 2.2 no longer considers tiffs to have a dataWindow, but some of our
			# reference images were written with an older OIIO that mistakenly read/writes
			# this metadata. Note non-OIIO apps like RV do not read this metadata.
			# See https://github.com/OpenImageIO/oiio/pull/2521 for an explanation
			ignoreDataWindow = ext in ( "tif", "tiff" ) and hasattr( IECoreImage, "OpenImageIOAlgo" ) and IECoreImage.OpenImageIOAlgo.version() >= 20206

			if not removeAlpha:
				self.assertImagesEqual( expectedOutput["out"], writerOutput["out"], maxDifference = maxError, ignoreMetadata = True, ignoreDataWindow = ignoreDataWindow )
			else:
				deleteChannels = GafferImage.DeleteChannels()
				deleteChannels["channels"].setValue( "A" )
				deleteChannels["in"].setInput( expectedOutput["out"] )

				self.assertImagesEqual( deleteChannels["out"], writerOutput["out"], maxDifference = maxError, ignoreMetadata = True, ignoreDataWindow = ignoreDataWindow )

	def __addExpectedIPTCMetadata( self, metadata, expectedMetadata ) :

		# Some formats support IPTC metadata, and some of the standard OIIO metadata
		# names are translated to it automatically by OpenImageIO. We need to update the
		# expectedMetadata to account for this.

		iptcPresent = bool( [ k for k in metadata.keys() if k.startswith( "IPTC:" ) ] )
		if not iptcPresent :
			return

		expectedMetadata["IPTC:Creator"] = expectedMetadata["Artist"]
		if "IPTC:OriginatingProgram" in metadata :
			# Really this shouldn't be inside a conditional, but we're working around
			# https://github.com/OpenImageIO/oiio/commit/aeecd8181c0667a98b3ae4db2c0ea5673e2ab534
			# whereby OIIO::TIFFInput started willfully discarding metadata.
			expectedMetadata["IPTC:OriginatingProgram"] = expectedMetadata["Software"]

	def testPadDataWindowToDisplayWindowScanline ( self ) :
		self.__testAdjustDataWindowToDisplayWindow( "png", self.__rgbFilePath )

	def testCropDataWindowToDisplayWindowScanline ( self ) :
		self.__testAdjustDataWindowToDisplayWindow( "png", self.__negativeDataWindowFilePath )

	def testPadDataWindowToDisplayWindowTile ( self ) :

		self.__testAdjustDataWindowToDisplayWindow( "iff", self.__rgbFilePath )

	def testCropDataWindowToDisplayWindowTile ( self ) :

		self.__testAdjustDataWindowToDisplayWindow( "iff", self.__negativeDataWindowFilePath )

	def __testAdjustDataWindowToDisplayWindow( self, ext, filePath ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( filePath )
		w = GafferImage.ImageWriter()

		testFile = self.__testFile( filePath.with_suffix("").name, "RGBA", ext )
		expectedFile = filePath.with_suffix( "."+ext )

		self.assertFalse( testFile.exists(), "Temporary file already exists : {}".format( testFile ) )

		# Setup the writer.
		w["in"].setInput( r["out"] )
		w["fileName"].setValue( testFile )
		w["channels"].setValue( "*" )

		# Execute
		w["task"].execute()
		self.assertTrue( testFile.exists(), "Failed to create file : {} : {}".format( ext, testFile ) )

		# Check the output.
		expectedOutput = GafferImage.ImageReader()
		expectedOutput["fileName"].setValue( expectedFile )

		writerOutput = GafferImage.ImageReader()
		writerOutput["fileName"].setValue( testFile )

		self.assertImagesEqual( expectedOutput["out"], writerOutput["out"], ignoreMetadata = True )

	def testOffsetDisplayWindowWrite( self ) :

		c = GafferImage.Constant()
		format = GafferImage.Format( imath.Box2i( imath.V2i( -20, -15 ), imath.V2i( 29, 14 ) ), 1. )
		c["format"].setValue( format )

		testFile = self.__testFile( "offsetDisplayWindow", "RGBA", "exr" )
		w = GafferImage.ImageWriter()
		w["in"].setInput( c["out"] )
		w["fileName"].setValue( testFile )

		w["task"].execute()

		self.assertTrue( testFile.exists() )
		i = IECore.Reader.create( str( testFile ) ).read()

		# Cortex uses the EXR convention, which differs
		# from Gaffer's, so we use the conversion methods to
		# check that the image windows are as expected.

		self.assertEqual(
			format.toEXRSpace( format.getDisplayWindow() ),
			i.displayWindow
		)

	def testHash( self ) :

		c = Gaffer.Context()
		c.setFrame( 1 )
		c2 = Gaffer.Context()
		c2.setFrame( 2 )

		writer = GafferImage.ImageWriter()

		# empty file produces no effect
		self.assertEqual( writer["fileName"].getValue(), "" )
		self.assertEqual( writer.hash( c ), IECore.MurmurHash() )

		# no input image produces no effect
		writer["fileName"].setValue( self.temporaryDirectory() / "test.exr" )
		self.assertEqual( writer.hash( c ), IECore.MurmurHash() )

		# now theres a file and an image, we get some output
		constant = GafferImage.Constant()
		writer["in"].setInput( constant["out"] )
		self.assertNotEqual( writer.hash( c ), IECore.MurmurHash() )

		# output doesn't vary by time yet
		self.assertEqual( writer.hash( c ), writer.hash( c2 ) )

		# now it does vary
		writer["fileName"].setValue( self.temporaryDirectory() / "test.#.exr" )
		self.assertNotEqual( writer.hash( c ), writer.hash( c2 ) )

		# other plugs matter too
		current = writer.hash( c )
		writer["openexr"]["mode"].setValue( GafferImage.ImageWriter.Mode.Tile )
		self.assertNotEqual( writer.hash( c ), current )
		current = writer.hash( c )
		writer["channels"].setValue( "R" )
		self.assertNotEqual( writer.hash( c ), current )

	def testPassThrough( self ) :

		s = Gaffer.ScriptNode()

		s["c"] = GafferImage.Constant()
		s["w"] = GafferImage.ImageWriter()
		s["w"]["in"].setInput( s["c"]["out"] )

		ci = GafferImage.ImageAlgo.image( s["c"]["out"] )
		wi = GafferImage.ImageAlgo.image( s["w"]["out"] )

		self.assertEqual( ci, wi )

	def testPassThroughSerialisation( self ) :

		s = Gaffer.ScriptNode()
		s["w"] = GafferImage.ImageWriter()

		ss = s.serialise()
		self.assertFalse( "out" in ss )

	def testMetadataDocumentName( self ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.__rgbFilePath )
		w = GafferImage.ImageWriter()

		testFile = self.__testFile( "metadataTest", "RGBA", "exr" )
		self.assertFalse( testFile.exists() )

		w["in"].setInput( r["out"] )
		w["fileName"].setValue( testFile )

		w["task"].execute()
		self.assertTrue( testFile.exists() )

		result = GafferImage.ImageReader()
		result["fileName"].setValue( testFile )

		self.assertEqual( result["out"]["metadata"].getValue()["DocumentName"].value, "untitled" )

		# add the writer to a script

		s = Gaffer.ScriptNode()
		s.addChild( w )

		w["task"].execute()

		result["refreshCount"].setValue( result["refreshCount"].getValue() + 1 )
		self.assertEqual( result["out"]["metadata"].getValue()["DocumentName"].value, "untitled" )

		# actually set the script's file name
		s["fileName"].setValue( "/my/gaffer/script.gfr" )

		w["task"].execute()

		result["refreshCount"].setValue( result["refreshCount"].getValue() + 1 )
		self.assertEqual( result["out"]["metadata"].getValue()["DocumentName"].value, "/my/gaffer/script.gfr" )

	def __testMetadataDoesNotAffectPixels( self, ext, overrideMetadata = {}, metadataToIgnore = [] ) :

		reader = GafferImage.ImageReader()
		reader["fileName"].setValue( self.__rgbFilePath.with_suffix( "."+ext ) )

		# IPTC:Creator will have the current username appended to the end of
		# the existing one, creating a list of creators. Blank out the initial
		# value for this test.
		regularMetadata = GafferImage.DeleteImageMetadata()
		regularMetadata["in"].setInput( reader["out"] )
		regularMetadata["names"].setValue( "IPTC:Creator" )

		# Add misleading metadata that if taken at face value could cause
		# us to write the wrong information to the file. Our governing rule
		# is that metadata is just "along for the ride", and should never
		# have any effect on the content of images themselves.
		misleadingMetadata = GafferImage.ImageMetadata()
		misleadingMetadata["in"].setInput( regularMetadata["out"] )
		misleadingMetadata["metadata"].addChild( Gaffer.NameValuePlug( "PixelAspectRatio", IECore.FloatData( 2 ) ) )
		misleadingMetadata["metadata"].addChild( Gaffer.NameValuePlug( "oiio:ColorSpace", IECore.StringData( "Rec709" ) ) )
		misleadingMetadata["metadata"].addChild( Gaffer.NameValuePlug( "oiio:BitsPerSample", IECore.IntData( 8 ) ) )
		misleadingMetadata["metadata"].addChild( Gaffer.NameValuePlug( "oiio:UnassociatedAlpha", IECore.IntData( 1 ) ) )
		misleadingMetadata["metadata"].addChild( Gaffer.NameValuePlug( "oiio:Gamma", IECore.FloatData( 0.25 ) ) )

		# Create ImageWriters to write out the images with regular
		# and misleading metadata.

		regularWriter = GafferImage.ImageWriter()
		regularWriter["in"].setInput( regularMetadata["out"] )
		regularWriter["fileName"].setValue( self.__testFile( "regularMetadata", "RGBA", ext ) )
		self.assertFalse( pathlib.Path( regularWriter["fileName"].getValue() ).exists() )

		misledWriter = GafferImage.ImageWriter()
		misledWriter["in"].setInput( misleadingMetadata["out"] )
		misledWriter["fileName"].setValue( self.__testFile( "misleadingMetadata", "RGBA", ext ) )
		self.assertFalse( pathlib.Path( misledWriter["fileName"].getValue() ).exists() )

		# Check that the writer is indeed being given misleading metadata.

		m = misledWriter["in"]["metadata"].getValue()
		self.assertEqual( m["PixelAspectRatio"], IECore.FloatData( 2 ) )
		self.assertEqual( m["oiio:ColorSpace"], IECore.StringData( "Rec709" ) )
		self.assertEqual( m["oiio:BitsPerSample"], IECore.IntData( 8 ) )
		self.assertEqual( m["oiio:UnassociatedAlpha"], IECore.IntData( 1 ) )
		self.assertEqual( m["oiio:Gamma"], IECore.FloatData( 0.25 ) )

		# Execute the writers

		regularWriter["task"].execute()
		misledWriter["task"].execute()

		self.assertTrue( pathlib.Path( regularWriter["fileName"].getValue() ).exists() )
		self.assertTrue( pathlib.Path( misledWriter["fileName"].getValue() ).exists() )

		# Make readers to read back what we wrote out

		misledReader = GafferImage.ImageReader()
		misledReader["fileName"].setInput( misledWriter["fileName"] )

		regularReader = GafferImage.ImageReader()
		regularReader["fileName"].setInput( regularWriter["fileName"] )

		# Check that the pixel data, format and data window has not
		# been changed at all, regardless of which metadata
		# was provided to the writers.

		# OIIO 2.2 no longer considers tiffs to have a dataWindow, but some of our
		# reference images were written with an older OIIO that mistakenly read/writes
		# this metadata. Note non-OIIO apps like RV do not read this metadata.
		# See https://github.com/OpenImageIO/oiio/pull/2521 for an explanation
		ignoreDataWindow = ext in ( "tif", "tiff" ) and hasattr( IECoreImage, "OpenImageIOAlgo" ) and IECoreImage.OpenImageIOAlgo.version() >= 20206

		self.assertImagesEqual( misledWriter["in"], misledReader["out"], ignoreMetadata = True, ignoreDataWindow = ignoreDataWindow )
		self.assertImagesEqual( misledReader["out"], regularReader["out"], ignoreMetadata = True, ignoreDataWindow = ignoreDataWindow )

		# Load the metadata from the files, and figure out what
		# metadata we expect to have based on what we expect the
		# writer to add, and what the reader adds automatically
		# during loading.

		misledReaderMetadata = misledReader["out"]["metadata"].getValue()
		regularReaderMetadata = regularReader["out"]["metadata"].getValue()

		expectedMetadata = regularMetadata["out"]["metadata"].getValue()
		expectedMetadata["DateTime"] = regularReaderMetadata["DateTime"]
		expectedMetadata["Software"] = IECore.StringData( "Gaffer " + Gaffer.About.versionString() )
		expectedMetadata["HostComputer"] = IECore.StringData( platform.node() )
		expectedMetadata["Artist"] = IECore.StringData( os.environ.get("USER") or os.environ["USERNAME"] ) #Linux or windows
		expectedMetadata["DocumentName"] = IECore.StringData( "untitled" )
		expectedMetadata["fileFormat"] = regularReaderMetadata["fileFormat"]
		expectedMetadata["dataType"] = regularReaderMetadata["dataType"]

		self.__addExpectedIPTCMetadata( regularReaderMetadata, expectedMetadata )

		for key, value in overrideMetadata.items() :
			expectedMetadata[key] = value
			regularReaderMetadata[key] = value

		# Now check that we have what we expect.
		for metaName in expectedMetadata.keys() :
			if metaName in metadataToIgnore :
				continue
			self.assertTrue( metaName in misledReaderMetadata.keys(), "Writer Metadata missing expected key \"{}\" set to \"{}\" : {}".format(metaName, str(expectedMetadata[metaName]), ext) )

			if metaName == "DateTime" :
				dateTimeDiff = datetime.datetime.strptime( str( expectedMetadata[metaName] ), "%Y:%m:%d %H:%M:%S" ) - datetime.datetime.strptime( str( misledReaderMetadata[metaName] ), "%Y:%m:%d %H:%M:%S" )
				self.assertLessEqual( abs( dateTimeDiff ), datetime.timedelta( seconds=1 ) )
			else :
				self.assertEqual( expectedMetadata[metaName], misledReaderMetadata[metaName], "Metadata does not match for key \"{}\" : {}".format(metaName, ext) )

		for metaName in regularReaderMetadata.keys() :
			if metaName in metadataToIgnore :
				continue
			self.assertTrue( metaName in misledReaderMetadata.keys(), "Writer Metadata missing expected key \"{}\" set to \"{}\" : {}".format(metaName, str(expectedMetadata[metaName]), ext) )

			if metaName == "DateTime" :
				dateTimeDiff = datetime.datetime.strptime( str( regularReaderMetadata[metaName] ), "%Y:%m:%d %H:%M:%S" ) - datetime.datetime.strptime( str( misledReaderMetadata[metaName] ), "%Y:%m:%d %H:%M:%S" )
				self.assertLessEqual( abs( dateTimeDiff ), datetime.timedelta( seconds=1 ) )
			else :
				self.assertEqual( regularReaderMetadata[metaName], misledReaderMetadata[metaName], "Metadata does not match for key \"{}\" : {}".format(metaName, ext) )

	def testExrMetadata( self ) :

		self.__testMetadataDoesNotAffectPixels(
			"exr",
			overrideMetadata = {
				"compression" : IECore.StringData( "zips" )
			},
		)

	def testTiffMetadata( self ) :

		self.__testMetadataDoesNotAffectPixels(
			"tif",
			overrideMetadata = {
				"compression" : IECore.StringData( "zip" ),
				"tiff:Compression" : IECore.IntData( 8 )
			},
		)

	def testSinglePixelThatUsedToCrash( self ) :
		i = GafferImage.Constant()
		i["format"].setValue( GafferImage.Format( 4096, 2304, 1.000 ) )

		overscanCrop = GafferImage.Crop()
		overscanCrop["area"].setValue( imath.Box2i( imath.V2i( 300, 300 ), imath.V2i( 2220, 1908 ) ) )
		overscanCrop["affectDataWindow"].setValue( False )
		overscanCrop["in"].setInput( i["out"] )

		c = GafferImage.Crop()
		c["area"].setValue( imath.Box2i( imath.V2i( -144, 1744 ), imath.V2i( -143, 1745 ) ) )
		c["affectDisplayWindow"].setValue( False )
		c["in"].setInput( overscanCrop["out"] )

		testFile = self.__testFile( "emptyImage", "RGBA", "exr" )
		self.assertFalse( testFile.exists() )

		w = GafferImage.ImageWriter()
		w["in"].setInput( c["out"] )
		w["fileName"].setValue( testFile )

		w["task"].execute()
		self.assertTrue( testFile.exists() )

		after = GafferImage.ImageReader()
		after["fileName"].setValue( testFile )
		# Check that the data window is the expected single pixel
		self.assertEqual( after["out"]["dataWindow"].getValue(), imath.Box2i( imath.V2i( -144, 1744 ), imath.V2i( -143, 1745 ) ) )

	def testWriteEmptyImage( self ) :

		i = GafferImage.Constant()
		i["format"].setValue( GafferImage.Format( imath.Box2i( imath.V2i( 0 ), imath.V2i( 100 ) ), 1 ) )

		c = GafferImage.Crop()
		c["areaSource"].setValue( GafferImage.Crop.AreaSource.Area )
		c["area"].setValue( imath.Box2i( imath.V2i( 40 ), imath.V2i( 40 ) ) )
		c["affectDisplayWindow"].setValue( False )
		c["affectDataWindow"].setValue( True )
		c["in"].setInput( i["out"] )

		testFile = self.__testFile( "emptyImage", "RGBA", "exr" )
		self.assertFalse( testFile.exists() )

		w = GafferImage.ImageWriter()
		w["in"].setInput( c["out"] )
		w["fileName"].setValue( testFile )

		w["task"].execute()
		self.assertTrue( testFile.exists() )

		after = GafferImage.ImageReader()
		after["fileName"].setValue( testFile )
		# Check that the data window is the expected single pixel
		self.assertEqual( after["out"]["dataWindow"].getValue(), imath.Box2i( imath.V2i( 0, 99 ), imath.V2i( 1, 100 ) ) )

	def testPixelAspectRatio( self ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.__rgbFilePath )
		self.assertEqual( r["out"]["format"].getValue().getPixelAspect(), 1 )
		self.assertEqual( r["out"]["metadata"].getValue()["PixelAspectRatio"], IECore.FloatData( 1 ) )

		# change the Format pixel aspect
		f = GafferImage.Resize()
		f["in"].setInput( r["out"] )
		f["format"].setValue( GafferImage.Format( r["out"]["format"].getValue().getDisplayWindow(), 2. ) )
		self.assertEqual( f["out"]["format"].getValue().getPixelAspect(), 2 )
		# processing does not change metadata
		self.assertEqual( r["out"]["metadata"].getValue()["PixelAspectRatio"], IECore.FloatData( 1 ) )

		testFile = self.__testFile( "pixelAspectFromFormat", "RGBA", "exr" )
		self.assertFalse( testFile.exists() )

		w = GafferImage.ImageWriter()
		w["in"].setInput( f["out"] )
		w["fileName"].setValue( testFile )
		w["channels"].setValue( "*" )

		w["task"].execute()
		self.assertTrue( testFile.exists() )

		after = GafferImage.ImageReader()
		after["fileName"].setValue( testFile )
		# the image is loaded with the correct pixel aspect
		self.assertEqual( after["out"]["format"].getValue().getPixelAspect(), 2 )
		# the metadata reflects this as well
		self.assertEqual( after["out"]["metadata"].getValue()["PixelAspectRatio"], IECore.FloatData( 2 ) )

	def testFileNameExpression( self ) :

		# this test was distilled down from a production example, where
		# serialising and reloading a script similar to this would throw
		# an exception.

		s = Gaffer.ScriptNode()

		s["b"] = Gaffer.Box()

		s["b"]["w"] = GafferImage.ImageWriter()
		s["b"]["w"]["user"]["s"] = Gaffer.StringPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic)

		s["b"]["p1"] = Gaffer.StringPlug( defaultValue = "test.tif", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["b"]["p2"] = Gaffer.StringPlug( defaultValue = "test.tif", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["b"]["e"] = Gaffer.Expression( "Expression" )

		s["b"]["e"].setExpression( 'parent["w"]["user"]["s"] = parent["p1"]; parent["w"]["fileName"] = parent["p2"]' )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

	def testUndoSetFileName( self ) :

		s = Gaffer.ScriptNode()
		s["w"] = GafferImage.ImageWriter()

		with Gaffer.UndoScope( s ) :
			s["w"]["fileName"].setValue( "test.tif" )

		self.assertEqual( s["w"]["fileName"].getValue(), "test.tif" )

		s.undo()
		self.assertEqual( s["w"]["fileName"].getValue(), "" )

		s.redo()
		self.assertEqual( s["w"]["fileName"].getValue(), "test.tif" )

	def testFileNamesWithSubstitutions( self ) :

		s = Gaffer.ScriptNode()

		s["c"] = GafferImage.Constant()
		s["w"] = GafferImage.ImageWriter()
		s["w"]["in"].setInput( s["c"]["out"] )
		s["w"]["fileName"].setValue( self.temporaryDirectory() / "test.${ext}" )

		context = Gaffer.Context( s.context() )
		context["ext"] = "tif"
		with context :
			s["w"]["task"].execute()

		self.assertTrue( ( self.temporaryDirectory() / "test.tif" ).is_file() )

	def testErrorMessages( self ) :

		s = Gaffer.ScriptNode()

		s["c"] = GafferImage.Constant()
		s["w"] = GafferImage.ImageWriter()
		s["w"]["in"].setInput( s["c"]["out"] )
		s["w"]["fileName"].setValue( self.temporaryDirectory() / "test.unsupportedExtension" )

		with s.context() :

			self.assertRaisesRegex( RuntimeError, "could not find a format writer for", s["w"].execute )

			s["w"]["fileName"].setValue( self.temporaryDirectory() / "test.tif" )
			s["w"]["task"].execute()

			os.chmod( self.temporaryDirectory() / "test.tif", 0o444 )
			self.assertRaisesRegex( RuntimeError, "Could not open", s["w"]["task"].execute )

	def testWriteIntermediateFile( self ) :

		# This tests a fairly common usage pattern whereby
		# an ImageReader loads an image generated higher
		# up the task tree, some processing is done, and
		# then an ImageWriter is used to write out the modified
		# image. A good example of this is a render node being
		# used to generate an image which is then pushed through
		# a slapcomp process. Because the rendered image to be
		# read/written doesn't exist at the point of dispatch
		# we have to make sure this doesn't cause problems.

		s = Gaffer.ScriptNode()

		s["c"] = GafferImage.Constant()

		s["w1"] = GafferImage.ImageWriter()
		s["w1"]["in"].setInput( s["c"]["out"] )
		s["w1"]["fileName"].setValue( self.temporaryDirectory() / "test1.exr" )

		s["r"] = GafferImage.ImageReader()
		s["r"]["fileName"].setValue( self.temporaryDirectory() / "test1.exr" )

		s["w2"] = GafferImage.ImageWriter()
		s["w2"]["in"].setInput( s["r"]["out"] )
		s["w2"]["fileName"].setValue( self.temporaryDirectory() / "test2.exr" )
		s["w2"]["preTasks"][0].setInput( s["w1"]["task"] )

		d = GafferDispatch.LocalDispatcher()
		d["jobsDirectory"].setValue( self.temporaryDirectory() / "jobs" )

		with s.context() :
			d.dispatch( [ s["w2"] ] )

		self.assertTrue( pathlib.Path( s["w1"]["fileName"].getValue() ).is_file() )
		self.assertTrue( pathlib.Path( s["w2"]["fileName"].getValue() ).is_file() )

	def testBackgroundDispatch( self ) :

		s = Gaffer.ScriptNode()

		s["c"] = GafferImage.Constant()

		s["w"] = GafferImage.ImageWriter()
		s["w"]["in"].setInput( s["c"]["out"] )
		s["w"]["fileName"].setValue( self.temporaryDirectory() / "test.exr" )

		d = GafferDispatch.LocalDispatcher()
		d["jobsDirectory"].setValue( self.temporaryDirectory() / "jobs" )
		d["executeInBackground"].setValue( True )

		with s.context() :
			d.dispatch( [ s["w"] ] )

		d.jobPool().waitForAll()

		self.assertTrue( pathlib.Path( s["w"]["fileName"].getValue() ).is_file() )

	def testDerivingInPython( self ) :

		class DerivedImageWriter( GafferImage.ImageWriter ) :

			def __init__( self, name = "DerivedImageWriter" ) :

				GafferImage.ImageWriter.__init__( self, name )

				self["copyFileName"] = Gaffer.StringPlug()

			def execute( self ) :

				GafferImage.ImageWriter.execute( self )

				shutil.copyfile( self["fileName"].getValue(), self["copyFileName"].getValue() )

		IECore.registerRunTimeTyped( DerivedImageWriter )

		c = GafferImage.Constant()

		w = DerivedImageWriter()
		w["in"].setInput( c["out"] )
		w["fileName"].setValue( self.temporaryDirectory() / "test.exr" )
		w["copyFileName"].setValue( self.temporaryDirectory() / "test2.exr" )

		w["task"].execute()

		self.assertTrue( pathlib.Path( w["fileName"].getValue() ).is_file() )
		self.assertTrue( pathlib.Path( w["copyFileName"].getValue() ).is_file() )

	def testStringMetadata( self ) :

		c = GafferImage.Constant()

		m = GafferImage.ImageMetadata()
		m["in"].setInput( c["out"] )
		m["metadata"].addChild( Gaffer.NameValuePlug( "test", IECore.StringData( "popplewell" ) ) )

		w = GafferImage.ImageWriter()
		w["in"].setInput( m["out"] )
		w["fileName"].setValue( self.temporaryDirectory() / "test.exr" )
		w["task"].execute()

		r = GafferImage.ImageReader()
		r["fileName"].setValue( w["fileName"].getValue() )

		self.assertEqual( r["out"]["metadata"].getValue()["test"], m["out"]["metadata"].getValue()["test"] )

	def __testFile( self, mode, channels, ext ) :

		return self.temporaryDirectory() / ( "test." + channels + "." + str( mode ) + "." + str( ext ) )

	def testJpgChroma( self ):

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.__rgbFilePath )

		w = GafferImage.ImageWriter()
		w["in"].setInput( r["out"] )

		result = GafferImage.ImageReader()

		chromaSubSamplings = ( "4:4:4", "4:2:2", "4:2:0", "4:1:1", "" )
		for chromaSubSampling in chromaSubSamplings:

			testFile = self.temporaryDirectory() / "chromaSubSampling.{0}.jpg".format( chromaSubSampling )

			w["fileName"].setValue( testFile )
			w["jpeg"]["chromaSubSampling"].setValue( chromaSubSampling )

			w["task"].execute()

			self.assertTrue( testFile.exists(), "Failed to create file : {} : {}".format( chromaSubSampling, testFile ) )

			result["fileName"].setValue( testFile )

			self.assertEqual( result["out"]["metadata"].getValue()["jpeg:subsampling"].value, chromaSubSampling if chromaSubSampling != "" else "4:2:0" )

	def testDPXDataType( self ) :

		image = GafferImage.Constant()

		writer = GafferImage.ImageWriter()
		writer["in"].setInput( image["out"] )

		reader = GafferImage.ImageReader()
		reader["fileName"].setInput( writer["fileName"] )

		for dataType in [ 8, 10, 12, 16 ] :

			writer["fileName"].setValue( self.temporaryDirectory() / "uint{}.dpx".format( dataType ) )
			writer["dpx"]["dataType"].setValue( "uint{0}".format( dataType ) )
			writer["task"].execute()

			self.assertEqual( reader["out"]["metadata"].getValue()["oiio:BitsPerSample"].value , dataType  )

	def testDefaultColorSpaceFunctionArguments( self ) :

		# Make a network to write an image
		# in various formats.

		c = GafferImage.Constant()
		c["format"].setValue( GafferImage.Format( 64, 64 ) )

		m = GafferImage.ImageMetadata()
		m["in"].setInput( c["out"] )
		m["metadata"].addChild( Gaffer.NameValuePlug( "test", IECore.StringData( "test" ) ) )

		w = GafferImage.ImageWriter()
		w["in"].setInput( m["out"] )

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

		GafferImage.ImageWriter.setDefaultColorSpaceFunction( f )

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

			capturedArguments.clear()
			w["task"].execute()

			self.assertEqual( len( capturedArguments ), 4 )
			self.assertEqual( capturedArguments["fileName"], w["fileName"].getValue() )
			self.assertEqual( capturedArguments["fileFormat"], fileFormat )
			self.assertEqual( capturedArguments["dataType"], dataType )
			self.assertEqual( capturedArguments["metadata"], w["in"]["metadata"].getValue() )

	def testDefaultColorSpace( self ) :

		image = GafferImage.Constant()
		image["color"].setValue( imath.Color4f( 0.25, 0.5, 0.75, 1 ) )

		writer = GafferImage.ImageWriter()
		writer["in"].setInput( image["out"] )
		writer["openexr"]["dataType"].setValue( "float" )

		reader = GafferImage.ImageReader()
		reader["fileName"].setInput( writer["fileName"] )

		def hardcodedColorSpaceConfig( colorSpace, *args ) :

			return colorSpace

		for colorSpace in [ "Cineon", "rec709", "AlexaV3LogC", "linear" ] :

			GafferImage.ImageWriter.setDefaultColorSpaceFunction(
				functools.partial( hardcodedColorSpaceConfig, colorSpace )
			)

			writer["fileName"].setValue( self.temporaryDirectory() / "{}.exr".format( colorSpace ) )
			writer["task"].execute()

			reader["colorSpace"].setValue( colorSpace )
			self.assertImagesEqual( reader["out"], image["out"], ignoreMetadata = True, maxDifference = 0.000001 )

	def testNonDefaultColorSpace( self ) :

		reader = GafferImage.ImageReader()
		reader["fileName"].setValue( self.__rgbFilePath )

		extraChannel = GafferImage.Shuffle()
		extraChannel["in"].setInput( reader["out"] )
		extraChannel["channels"].addChild( GafferImage.Shuffle.ChannelPlug( "Q", "R" ) )

		writer = GafferImage.ImageWriter()

		resultReader = GafferImage.ImageReader()
		resultReader["fileName"].setInput( writer["fileName"] )

		resultWithoutExtra = GafferImage.DeleteChannels()
		resultWithoutExtra["in"].setInput( resultReader["out"] )
		resultWithoutExtra["channels"].setValue( "Q" )

		for colorSpace in [ "Cineon", "rec709", "AlexaV3LogC" ] :

			writer["in"].setInput( reader["out"] )
			writer["fileName"].setValue( self.temporaryDirectory() / "{}.exr".format( colorSpace ) )
			writer["colorSpace"].setValue( colorSpace )

			writer["task"].execute()

			self.assertTrue( pathlib.Path( writer["fileName"].getValue() ).exists(), "Failed to create file : {}".format( writer["fileName"].getValue() ) )

			resultReader["colorSpace"].setValue( colorSpace )
			self.assertImagesEqual( resultReader["out"], reader["out"], ignoreMetadata=True, maxDifference=0.0008 )

			# This is a kinda weird test for a very specific bug:  an earlier version of ImageWriter would
			# only unpremultiply during color processing if the alpha channel came last.  To verify we've
			#fixed this, we add a channel named Q, write to file, then read back and delete it, and make
			# sure we unpremulted properly
			writer["in"].setInput( extraChannel["out"] )
			writer["task"].execute()

			resultReader["refreshCount"].setValue( resultReader["refreshCount"].getValue() + 1 )

			self.assertEqual( list( resultReader["out"].channelNames() ), [ "R", "G", "B", "A", "Q" ] )

			self.assertImagesEqual( resultWithoutExtra["out"], reader["out"], ignoreMetadata=True, maxDifference=0.0008 )

	def testDependencyNode( self ) :

		writer = GafferImage.ImageWriter()
		self.assertTrue( isinstance( writer, Gaffer.DependencyNode ) )
		self.assertTrue( writer.isInstanceOf( Gaffer.DependencyNode.staticTypeId() ) )

		cs = GafferTest.CapturingSlot( writer.plugDirtiedSignal() )
		writer["fileName"].setValue( "test.png" )
		self.assertIn( writer["task"], { x[0] for x in cs } )

	def testBlankScanlines( self ) :

		# create a wide image
		constant = GafferImage.Constant()
		constant["color"].setValue( imath.Color4f( 0.5, 0.5, 0.5, 1 ) )
		constant["format"].setValue( GafferImage.Format( imath.Box2i( imath.V2i( 0 ), imath.V2i( 3000, 1080 ) ), 1. ) )

		# fit it such that we have several tiles of blank lines on top (and bottom)
		resize = GafferImage.Resize()
		resize["in"].setInput( constant["out"] )
		resize["fitMode"].setValue( GafferImage.Resize.FitMode.Horizontal )

		# write to a file format that requires consecutive scanlines
		writer = GafferImage.ImageWriter()
		writer["in"].setInput( resize["out"] )
		writer["fileName"].setValue( self.temporaryDirectory() / "blankScanlines.jpg" )
		writer["task"].execute()

		# ensure we wrote the file successfully
		reader = GafferImage.ImageReader()
		reader["fileName"].setInput( writer["fileName"] )
		cleanOutput = GafferImage.DeleteChannels()
		cleanOutput["in"].setInput( writer["in"] )
		cleanOutput["channels"].setValue( "A" )
		self.assertImagesEqual( reader["out"], cleanOutput["out"], ignoreMetadata=True, ignoreDataWindow=True, maxDifference=0.05 )

	def testThrowsForEmptyChannels( self ) :

		constant = GafferImage.Constant()

		writer = GafferImage.ImageWriter()
		writer["in"].setInput( constant["out"] )
		writer["fileName"].setValue( self.temporaryDirectory() / "test.exr" )
		writer["channels"].setValue( "diffuse.[RGB]" )

		with self.assertRaisesRegex( Gaffer.ProcessException, "No channels to write" ) :
			writer["task"].execute()

		self.assertFalse( pathlib.Path( writer["fileName"].getValue() ).exists() )

	def testDWACompressionLevel( self ) :

		constant = GafferImage.Constant()
		writer = GafferImage.ImageWriter()
		writer["in"].setInput( constant["out"] )
		writer["fileName"].setValue( self.temporaryDirectory() / "test.exr" )
		writer["openexr"]["dwaCompressionLevel"].setValue( 100 )

		reader = GafferImage.ImageReader()
		reader["fileName"].setInput( writer["fileName"] )

		# Not in DWA mode, so no level specified.
		writer["task"].execute()
		self.assertNotIn( "openexr:dwaCompressionLevel", reader["out"].metadata() )

		# DWAA mode should specify level.
		writer["openexr"]["compression"].setValue( "dwaa" )
		writer["task"].execute()
		reader["refreshCount"].setValue( reader["refreshCount"].getValue() + 1 )
		self.assertEqual( reader["out"].metadata()["openexr:dwaCompressionLevel"].value, 100.0 )

		# As should DWAB.
		writer["openexr"]["compression"].setValue( "dwab" )
		writer["openexr"]["dwaCompressionLevel"].setValue( 110 )
		writer["task"].execute()
		reader["refreshCount"].setValue( reader["refreshCount"].getValue() + 1 )
		self.assertEqual( reader["out"].metadata()["openexr:dwaCompressionLevel"].value, 110.0 )

	def testNameMetadata( self ) :

		# Load an image with various layers.

		reader = GafferImage.ImageReader()
		reader["fileName"].setValue( self.imagesPath() / "multipart.exr" )
		self.assertEqual(
			set( reader["out"].channelNames() ),
			{
				"customRgb.R", "customRgb.G", "customRgb.B",
				"customRgba.R", "customRgba.G", "customRgba.B", "customRgba.A",
				"customDepth.Z",
			}
		)

		# Shuffle one of them into the primary RGBA layer.

		shuffle = GafferImage.Shuffle()
		shuffle["in"].setInput( reader["out"] )
		shuffle["channels"].addChild( GafferImage.Shuffle.ChannelPlug( "R", "customRgba.R" ) )
		shuffle["channels"].addChild( GafferImage.Shuffle.ChannelPlug( "G", "customRgba.G" ) )
		shuffle["channels"].addChild( GafferImage.Shuffle.ChannelPlug( "B", "customRgba.B" ) )
		shuffle["channels"].addChild( GafferImage.Shuffle.ChannelPlug( "A", "customRgba.A" ) )

		# Write the image out and assert that it reads in again the same.

		writer = GafferImage.ImageWriter()
		writer["in"].setInput( shuffle["out"] )
		writer["fileName"].setValue( self.temporaryDirectory() / "test.exr" )
		writer["task"].execute()

		rereader = GafferImage.ImageReader()
		rereader["fileName"].setInput( writer["fileName"] )

		self.assertImagesEqual( writer["in"], rereader["out"], ignoreMetadata = True, ignoreChannelNamesOrder = True )

		# Deliberately introduce some metadata that would confuse OIIO,
		# and check that it is ignored.

		metadata = GafferImage.ImageMetadata()
		metadata["in"].setInput( shuffle["out"] )
		metadata["metadata"].addChild( Gaffer.NameValuePlug( "name", "test" ) )
		metadata["metadata"].addChild( Gaffer.NameValuePlug( "oiio:subimagename", "test" ) )
		metadata["metadata"].addChild( Gaffer.NameValuePlug( "oiio:subimages", 1 ) )

		writer["in"].setInput( metadata["out"] )
		writer["fileName"].setValue( self.temporaryDirectory() / "test2.exr" )

		with IECore.CapturingMessageHandler() as mh :
			writer["task"].execute()

		self.assertImagesEqual( rereader["out"], shuffle["out"], ignoreMetadata = True, ignoreChannelNamesOrder = True )

		warnings = { m.message for m in mh.messages if m.level == IECore.Msg.Level.Warning }
		self.assertEqual( len( warnings ), 3 )
		self.assertIn( "Ignoring metadata \"name\" because it conflicts with OpenImageIO.", warnings )
		self.assertIn( "Ignoring metadata \"oiio:subimagename\" because it conflicts with OpenImageIO.", warnings )
		self.assertIn( "Ignoring metadata \"oiio:subimages\" because it conflicts with OpenImageIO.", warnings )

	def testReproduceProductionSamples( self ):

		constant = GafferImage.Constant()
		constant["format"].setValue( GafferImage.Format( 16, 16, 1.000 ) )
		constant["expression"] = Gaffer.Expression()
		constant["expression"].setExpression(
			'import imath; parent["color"] = imath.Color4f( 0.4, 0.5, 0.6, 1 ) if context.get( "collect:layerName", "" ) != "" else imath.Color4f( 0.1, 0.2, 0.3, 0.4 )'
		)

		deleteChannels = GafferImage.DeleteChannels()
		deleteChannels["in"].setInput( constant["out"] )
		deleteChannels["channels"].setValue( '[A]' )

		collect = GafferImage.CollectImages()
		collect["in"].setInput( deleteChannels["out"] )
		collect["rootLayers"].setValue( IECore.StringVectorData( [ 'character', '' ] ) )

		writer = GafferImage.ImageWriter()
		writer["in"].setInput( collect["out"] )
		writer["fileName"].setValue( self.temporaryDirectory() / "test.exr" )
		writer["layout"]["partName"].setValue( '${imageWriter:standardPartName}.main' )
		writer["layout"]["channelName"].setValue( '${imageWriter:nukeBaseName}' )
		writer["task"].execute()

		refReader = GafferImage.ImageReader()
		refReader["fileName"].setValue( self.imagesPath() / "imitateProductionLayers1.exr" )

		rereader = GafferImage.ImageReader()
		rereader["channelInterpretation"].setInput( refReader["channelInterpretation"] )
		rereader["fileName"].setInput( writer["fileName"] )

		refReader["channelInterpretation"].setValue( GafferImage.ImageReader.ChannelInterpretation.Default )
		self.assertImagesEqual( rereader["out"], refReader["out"], ignoreMetadata = True )
		refReader["channelInterpretation"].setValue( GafferImage.ImageReader.ChannelInterpretation.Legacy )
		self.assertImagesEqual( rereader["out"], refReader["out"], ignoreMetadata = True )

		shuffleDepth = GafferImage.Shuffle()
		shuffleDepth["in"].setInput( constant["out"] )
		shuffleDepth["channels"].addChild( GafferImage.Shuffle.ChannelPlug( "channel" ) )
		shuffleDepth["channels"]["channel"]["out"].setValue( 'depth.Z' )
		shuffleDepth["channels"]["channel"]["in"].setValue( 'A' )

		deleteChannels["in"].setInput( shuffleDepth["out"] )
		writer["in"].setInput( deleteChannels["out"] )
		writer["openexr"]["dataType"].setValue( 'float' )

		writer["layout"]["partName"].setValue( '${imageWriter:standardPartName}_main' )
		writer["expression"] = Gaffer.Expression()
		writer["expression"].setExpression(
			'c = context["imageWriter:baseName"]; parent["layout"]["channelName"] = "depth.Z" if c == "Z" else c'
		)
		writer["task"].execute()

		refReader["fileName"].setValue( self.imagesPath() / "imitateProductionLayers2.exr" )
		refReader["refreshCount"].setValue( 2 )
		rereader["refreshCount"].setValue( 2 )

		refReader["channelInterpretation"].setValue( GafferImage.ImageReader.ChannelInterpretation.Default )
		self.assertImagesEqual( rereader["out"], refReader["out"], ignoreMetadata = True )
		refReader["channelInterpretation"].setValue( GafferImage.ImageReader.ChannelInterpretation.Legacy )
		self.assertImagesEqual( rereader["out"], refReader["out"], ignoreMetadata = True )

	def testReproduceWeirdPartNames( self ):

		constant = GafferImage.Constant()
		constant["format"].setValue( GafferImage.Format( 16, 16, 1.000 ) )
		constant["expression"] = Gaffer.Expression()
		constant["expression"].setExpression(
			'import imath; parent["color"] = imath.Color4f( 0.4, 0.5, 0.6, 1 ) if context.get( "collect:layerName", "" ) != "" else imath.Color4f( 0.1, 0.2, 0.3, 0.4 )'
		)

		collect = GafferImage.CollectImages()
		collect["in"].setInput( constant["out"] )
		collect["rootLayers"].setValue( IECore.StringVectorData( [ 'layer', '' ] ) )

		writer = GafferImage.ImageWriter()
		writer["in"].setInput( collect["out"] )
		writer["fileName"].setValue( self.temporaryDirectory() / "test.exr" )
		writer["layout"]["partName"].setValue( '${imageWriter:standardPartName}.main' )
		writer["layout"]["channelName"].setValue( '${imageWriter:layerName}.${imageWriter:baseName}' )
		writer["expression"] = Gaffer.Expression()
		writer["expression"].setExpression(
			'c = context["imageWriter:baseName"]; l = context["imageWriter:layerName"]; parent["layout"]["partName"] = "part%i" % ( "RGBA".find(c) + 2 * ( l == "layer" ) )'
		)
		writer["task"].execute()

		refReader = GafferImage.ImageReader()
		refReader["fileName"].setValue( self.imagesPath() / "weirdPartNames.exr" )

		rereader = GafferImage.ImageReader()
		rereader["channelInterpretation"].setInput( refReader["channelInterpretation"] )
		rereader["fileName"].setInput( writer["fileName"] )

		refReader["channelInterpretation"].setValue( GafferImage.ImageReader.ChannelInterpretation.Default )
		self.assertImagesEqual( rereader["out"], refReader["out"], ignoreMetadata = True )
		refReader["channelInterpretation"].setValue( GafferImage.ImageReader.ChannelInterpretation.Legacy )
		self.assertImagesEqual( rereader["out"], refReader["out"], ignoreMetadata = True )

	# Helper function that extracts the part of the header we care about from exrheader
	def usefulHeader( self, path ):
		r = subprocess.check_output( ["exrheader", path ], universal_newlines=True ).splitlines()[2:]

		# Skip header lines that change every run, or between software, and compression ( since we're
		# not testing for that ), and chunkCount ( since it depends on compression ).  "version" is
		# something Nuke sets that we're not worrying about.  "ResolutionUnit" is sometimes set by OIIO
		# automatically if it sees other metadata ... it always sets it to "in" for inches
		r = [ i for i in r if not (
			( i + " " ).split( " " )[0] in [ "Artist", "DocumentName", "HostComputer", "Software", "capDate", "compression", "chunkCount", "version", "ResolutionUnit", "textureformat", "preview", "openexr:chunkCount" ] or i.startswith( "nuke" )
		) ]

		# We don't care about the difference between 16 and 32 bit floats
		r = [ i.replace( "32-bit floating-point", "16-bit floating-point" ) for i in r ]

		# Now a very hacky part - we need the main part to be first, but otherwise, the order
		# of parts doesn't matter, so sort the later parts by name
		parts = [ [] ]
		partNames = [ "X" ]

		for i in r:
			if i.startswith( " part " ):
				if i[6] != "0":
					parts.append( [] )
					partNames.append( "X" )
					continue
			parts[-1].append( i )
			if i.startswith( "name " ):
				partNames[-1] = i
		parts[-1].append( "" ) # An extra empty line at the end keeps things consistent for the last part

		r = parts[0]
		partNum = 1
		for n, p in sorted( zip( partNames[1:], parts[1:] ) ):
			r.append( " part %i:" % partNum )
			r += p
			partNum += 1

		return r

	def testWithChannelTestImage( self ):

		reference = self.channelTestImage()

		writePath = self.temporaryDirectory() / "test.exr"
		writer = GafferImage.ImageWriter()
		writer["in"].setInput( reference["out"] )
		writer["fileName"].setValue( writePath )

		rereader = GafferImage.ImageReader()
		rereader["fileName"].setValue( writePath )
		rereader["channelInterpretation"].setValue( GafferImage.ImageReader.ChannelInterpretation.Default )

		# Test that the presets produce the expected files, including that they match files produced by Nuke
		# if appropriate
		for layout, referenceFile in [
				( "Single Part", "SinglePart" ), ( "Part per Layer", "PartPerLayer" ),
				( "Nuke/Interleave Channels, Layers and Views", "NukeSinglePart" ), ( "Nuke/Interleave Channels", "NukePartPerLayer" )
			]:

			Gaffer.NodeAlgo.applyPreset( writer["layout"], layout )

			writer["task"].execute()
			rereader["refreshCount"].setValue( rereader["refreshCount"].getValue() + 1 )
			self.assertImagesEqual( rereader["out"], reference["out"], ignoreMetadata = True, maxDifference = 0.0002, ignoreChannelNamesOrder = layout.startswith( "Nuke" ) )
			header = self.usefulHeader( writePath )
			refHeader = self.usefulHeader( self.imagesPath() / ( "channelTest" + referenceFile + ".exr" ) )

			if layout == "Nuke/Interleave Channels":
				# We don't match the view metadata which Nuke sticks on files without specific views
				refHeader = list( filter( lambda i : i != 'view (type string): "main"', refHeader ) )
			self.assertEqual( header, refHeader )

	def testWithMultiViewChannelTestImage( self ):

		reference = self.channelTestImageMultiView()

		writePath = self.temporaryDirectory() / "multiViewTest.exr"
		writer = GafferImage.ImageWriter()
		writer["in"].setInput( reference["out"] )
		writer["fileName"].setValue( writePath )

		rereader = GafferImage.ImageReader()
		rereader["fileName"].setValue( writePath )
		rereader["channelInterpretation"].setValue( GafferImage.ImageReader.ChannelInterpretation.Default )

		# Test that the presets produce the expected files
		for layout, referenceFile in [
				( "Single Part", "SinglePart" ), ( "Part per View", "PartPerView" ), ( "Part per Layer", "PartPerLayer" ),
			]:

			Gaffer.NodeAlgo.applyPreset( writer["layout"], layout )

			writer["task"].execute()
			rereader["refreshCount"].setValue( rereader["refreshCount"].getValue() + 1 )

			# In "Single Part", we must expand the dataWindow to encompass all views, so we can't get
			# exactly matching data windows
			self.assertImagesEqual( rereader["out"], reference["out"], ignoreMetadata = True, maxDifference = 0.0002, ignoreChannelNamesOrder = layout == "Single Part", ignoreDataWindow = layout == "Single Part" )

			header = self.usefulHeader( writePath )
			refHeader = self.usefulHeader( self.imagesPath() / ( "channelTestMultiView" + referenceFile + ".exr" ) )

			self.assertEqual( header, refHeader )

		# Test for Nuke, which requires expanding data window to match for all views, so we use referenceExpanded

		# Nuke isn't very flexible in handling multiView images.  Don't use different channels in different views
		reference["DeleteChannels"]["enabled"].setValue( False )

		# Nuke also doesn't support different data windows for different views
		writer["matchDataWindows"].setValue( True )

		# Note that there is no test for Nuke/Interleave Channels, because Nuke just crashes when
		# I try to export in that mode to get a reference image
		for layout, referenceFile in [
				( "Part per Layer", "NukeCompat" ), ( "Nuke/Interleave Channels, Layers and Views", "NukeSinglePart" ), ( "Nuke/Interleave Channels and Layers", "NukePartPerView" ), ( "Nuke/Interleave Channels", None )
			]:

			Gaffer.NodeAlgo.applyPreset( writer["layout"], layout )

			writer["task"].execute()
			rereader["refreshCount"].setValue( rereader["refreshCount"].getValue() + 1 )
			self.assertImagesEqual( rereader["out"], reference["out"], ignoreMetadata = True, maxDifference = 0.0002, ignoreChannelNamesOrder = layout.startswith( "Nuke" ), ignoreDataWindow = True )

			if layout == "Nuke/Interleave Channels, Layers and Views":
				# Nuke's implementation of single part multi-view has channel names that don't match the
				# spec at all, don't bother trying to match them
				continue
			if layout == "Nuke/Interleave Channels":
				# I can't get Nuke to export in this mode without segfaulting, so we don't have "ground truth"
				# to compare our channel naming too
				continue

			header = self.usefulHeader( writePath )
			refHeader = self.usefulHeader( self.imagesPath() / ( "channelTestMultiView" + referenceFile + ".exr" ) )

			if layout == "Nuke/Interleave Channels and Layers":
				# Swap the order of left and right to match Nuke having arbitrarily reordered
				# ( We should probably have an actual way of reordering views in Gaffer
				refHeader = [ i.replace( "left", "right" ) if "left" in i else i.replace( "right", "left" ) for i in refHeader ]
			self.assertEqual( header, refHeader )

	@unittest.skipIf( not "OPENEXR_IMAGES_DIR" in os.environ, "If you want to run tests using the OpenEXR sample images, then download https://github.com/AcademySoftwareFoundation/openexr-images and set the env var OPENEXR_IMAGES_DIR to the directory" )
	def testWithEXRSampleImages( self ):
		self.maxDiff = None

		directory = os.environ["OPENEXR_IMAGES_DIR"] + "/"

		reader = GafferImage.ImageReader()

		writer = GafferImage.ImageWriter()
		writer["in"].setInput( reader["out"] )
		writer["openexr"]["dataType"].setValue( 'float' )

		writer["partNameForSeparateZ"] = Gaffer.StringPlug()
		writer["partNameExpression"] = Gaffer.Expression()
		writer["partNameExpression"].setExpression( inspect.cleandoc(
			"""
			v = context.get( "imageWriter:viewName" )
			parent["partNameForSeparateZ"] = ( "depth" if context.get( "imageWriter:channelName" ) == "Z" else context.get( "imageWriter:standardPartName" ) ) + ( ( "_" + v ) if v else "" )
			"""
		) )

		rereader = GafferImage.ImageReader()

		tempFileIndex = 0


		for name in [
			"Beachball/multipart.0001.exr", "Beachball/singlepart.0001.exr", "Chromaticities/Rec709.exr", "Chromaticities/XYZ.exr", "DisplayWindow/t01.exr", "DisplayWindow/t02.exr", "DisplayWindow/t03.exr", "DisplayWindow/t04.exr", "DisplayWindow/t05.exr", "DisplayWindow/t06.exr", "DisplayWindow/t07.exr", "DisplayWindow/t08.exr", "DisplayWindow/t09.exr", "DisplayWindow/t10.exr", "DisplayWindow/t11.exr", "DisplayWindow/t12.exr", "DisplayWindow/t13.exr", "DisplayWindow/t14.exr", "DisplayWindow/t15.exr", "DisplayWindow/t16.exr", "MultiResolution/Bonita.exr", "MultiResolution/ColorCodedLevels.exr", "MultiResolution/Kapaa.exr", "MultiResolution/KernerEnvCube.exr", "MultiResolution/KernerEnvLatLong.exr", "MultiResolution/MirrorPattern.exr", "MultiResolution/OrientationCube.exr", "MultiResolution/OrientationLatLong.exr", "MultiResolution/PeriodicPattern.exr", "MultiResolution/StageEnvCube.exr", "MultiResolution/StageEnvLatLong.exr", "MultiResolution/WavyLinesCube.exr", "MultiResolution/WavyLinesLatLong.exr", "MultiResolution/WavyLinesSphere.exr", "MultiView/Adjuster.exr", "MultiView/Balls.exr", "MultiView/Fog.exr", "MultiView/Impact.exr", "MultiView/LosPadres.exr", "ScanLines/Blobbies.exr", "ScanLines/CandleGlass.exr", "ScanLines/Cannon.exr", "ScanLines/Desk.exr", "ScanLines/MtTamWest.exr", "ScanLines/PrismsLenses.exr", "ScanLines/StillLife.exr", "ScanLines/Tree.exr", "TestImages/AllHalfValues.exr", "TestImages/BrightRings.exr", "TestImages/BrightRingsNanInf.exr", "TestImages/GammaChart.exr", "TestImages/GrayRampsDiagonal.exr", "TestImages/GrayRampsHorizontal.exr", "TestImages/RgbRampsDiagonal.exr", "TestImages/SquaresSwirls.exr", "TestImages/WideColorGamut.exr", "TestImages/WideFloatRange.exr", "Tiles/GoldenGate.exr", "Tiles/Ocean.exr", "Tiles/Spirals.exr", "v2/LeftView/Balls.exr", "v2/LeftView/Ground.exr", "v2/LeftView/Leaves.exr", "v2/LeftView/Trunks.exr", "v2/LowResLeftView/Balls.exr", "v2/LowResLeftView/composited.exr", "v2/LowResLeftView/Ground.exr", "v2/LowResLeftView/Leaves.exr", "v2/LowResLeftView/Trunks.exr", "v2/Stereo/Balls.exr", "v2/Stereo/composited.exr", "v2/Stereo/Ground.exr", "v2/Stereo/Leaves.exr", "v2/Stereo/Trunks.exr"
		]:
			reader["fileName"].setValue( directory + name )

			isDeep = reader["out"].deep( reader["out"].viewNames()[0] )

			matchingLayout = "Part per View" if isDeep else "Single Part"
			if name == "Beachball/singlepart.0001.exr":
				matchingLayout = "Single Part"
			if name == "Beachball/multipart.0001.exr":
				matchingLayout = "Part per Layer"
			elif name.startswith( "MultiResolution" ):
				# We can read multi-resolution files, but we don't write them as multi-res, so the headers
				# won't match
				matchingLayout = None
			elif name == "v2/Stereo/composited.exr" :
				# We don't have a convenient way to write Z in the base layer, but a separate part, so the
				# headers won't match.  ( We could actually write a matching format using a custom expression
				# on writer["layout"]["partName"], but I won't worry about that currently )
				matchingLayout = None

			for layout in [
					"Single Part", "Part per View", "Part per Layer", "Nuke/Interleave Channels, Layers and Views", "Nuke/Interleave Channels and Layers", "Nuke/Interleave Channels"
			]:
				isSinglePart = layout in [ "Single Part", "Nuke/Interleave Channels, Layers and Views" ]

				writer["layout"]["partName"].setInput( None )

				Gaffer.NodeAlgo.applyPreset( writer["layout"], layout )

				if name.startswith( "v2" ) and not name == "v2/LowResLeftView/composited.exr":
					# Match part naming in sample files
					writer["layout"]["partName"].setValue( "rgba." + writer["layout"]["partName"].getValue() )

				if name == "Beachball/multipart.0001.exr" and layout == "Part per Layer":
					writer["layout"]["partName"].setInput( writer["partNameForSeparateZ"] )

				tempFileIndex += 1
				tempFile = self.temporaryDirectory() / ( "sampleImageTestFile%i.exr" % tempFileIndex )
				writer["fileName"].setValue( tempFile )
				rereader["fileName"].setValue( tempFile )

				tiled = name in [ "MultiView/Impact.exr" ] or name.startswith( "Tiles/" )
				writer['openexr']['mode'].setValue( tiled )

				if isDeep and len( reader["out"].viewNames() ) > 1 and isSinglePart:
					self.assertRaisesRegex( Gaffer.ProcessException, '^ImageWriter.task : Cannot write views "left" and "right" both to same image part when dealing with deep images$', writer["task"].execute )
					continue
				else:
					writer["task"].execute()

				# If one of our layout presets matches how the file is laid out, the header should match
				if layout == matchingLayout:
					header = self.usefulHeader( tempFile )
					# Some aspects of EXR files we don't currently control, so we hack those aspects to make
					# sure everything else matches.  It might be nice to be able to actually set tile size
					# on the writer
					if name == "MultiView/Impact.exr":
						header = [ i.replace( "tile size 128 by 128 pixels", "tile size 64 by 64 pixels" ) for i in header ]
					if name == "Tiles/Spirals.exr":
						header = [ i.replace( "tile size 128 by 128 pixels", "tile size 287 by 126 pixels" ) for i in header ]
					if name == "ScanLines/Blobbies.exr":
						header = [ i.replace( "increasing y", "decreasing y" ) for i in header ]

					refHeader = self.usefulHeader( directory + name )

					# In this example, there is an unnecessary name, plus disparity channels outside of views
					# that we currently can't load
					if name == "Beachball/singlepart.0001.exr":
						refHeader = [ i for i in refHeader if not i.startswith( "name" ) ]

					if name == "Beachball/multipart.0001.exr":
						# Account for data window being expanded to match for different parts that share a view
						refHeader = list( map( lambda l :
							l.replace( "(1070 245) - (1455 1013)", "(654 245) - (1530 1120)" ).replace(
								"(1106 245) - (1490 1013)", "(688 245) - (1564 1120)" ),
							refHeader
						) )

					self.assertEqual( header, refHeader )

				# If we're writing from a multi-part to a single-part, we won't be able to preserve the data
				# window
				expandDataWindow = name == "Beachball/multipart.0001.exr" and isSinglePart

				ignoreOrder = name == "Beachball/multipart.0001.exr" or ( name == "Beachball/singlepart.0001.exr" and layout != "Single Part" )
				rereader["channelInterpretation"].setValue( GafferImage.ImageReader.ChannelInterpretation.Default )
				self.assertImagesEqual( rereader["out"], reader["out"], ignoreMetadata = True, ignoreChannelNamesOrder = ignoreOrder, ignoreDataWindow = expandDataWindow )

				if not layout.startswith( "Nuke" ):
					rereader["channelInterpretation"].setValue( GafferImage.ImageReader.ChannelInterpretation.Specification )
					self.assertImagesEqual( rereader["out"], reader["out"], ignoreMetadata = True, ignoreChannelNamesOrder = ignoreOrder, ignoreDataWindow = expandDataWindow )

	def channelTypesFromHeader( self, path ):
		r = subprocess.check_output( ["exrheader", path ], universal_newlines=True )

		channelText = re.findall( re.compile( r'channels \(type chlist\):\n((    .*\n)+)', re.MULTILINE ), r )

		return [ i.split()[:2] for part in channelText for i in part[0].splitlines()  ]

	def testPerChannelDataType( self ):

		reference = self.channelTestImage()

		writer = GafferImage.ImageWriter()
		writer["in"].setInput( reference["out"] )
		writer["fileName"].setValue( self.temporaryDirectory() / "test.tif" )

		# Start with some formats that don't support per channel data types, and check that they fail as
		# expected
		writer["dataTypeExpression"] = Gaffer.Expression()
		writer["dataTypeExpression"].setExpression( 'parent["tiff"]["dataType"] = "uint8" if context.get( "imageWriter:channelName" ) == "R" else "uint16"' )

		with self.assertRaisesRegex( Gaffer.ProcessException, "File format tiff does not support per-channel data types" ) :
			writer["task"].execute()

		writer["fileName"].setValue( self.temporaryDirectory() / "test.dpx" )
		writer["dataTypeExpression"].setExpression( 'parent["dpx"]["dataType"] = "uint8" if context.get( "imageWriter:channelName" ) == "R" else "uint16"' )

		with self.assertRaisesRegex( Gaffer.ProcessException, "File format dpx does not support per-channel data types" ) :
			writer["task"].execute()

		writePath = self.temporaryDirectory() / "test.exr"
		writer["fileName"].setValue( writePath )

		writer["task"].execute()

		# Default channel types - depthDataType forces Z and ZBack to 32-bit, but not character.Z
		self.assertEqual( self.channelTypesFromHeader( writePath ), [
			['A,', '16-bit'], ['B,', '16-bit'], ['G,', '16-bit'], ['R,', '16-bit'],
			['Z,', '32-bit'], ['ZBack,', '32-bit'], ['custom,', '16-bit'], ['mask,', '16-bit'],
			['character.A,', '16-bit'], ['character.B,', '16-bit'], ['character.G,', '16-bit'], ['character.R,', '16-bit'],
			['character.Z,', '16-bit'], ['character.ZBack,', '16-bit'], ['character.custom,', '16-bit'], ['character.mask,', '16-bit']
		] )

		writer["openexr"]["depthDataType"].setValue( "" )
		writer["task"].execute()

		self.assertEqual( self.channelTypesFromHeader( writePath ), [
			['A,', '16-bit'], ['B,', '16-bit'], ['G,', '16-bit'], ['R,', '16-bit'],
			['Z,', '16-bit'], ['ZBack,', '16-bit'], ['custom,', '16-bit'], ['mask,', '16-bit'],
			['character.A,', '16-bit'], ['character.B,', '16-bit'], ['character.G,', '16-bit'], ['character.R,', '16-bit'],
			['character.Z,', '16-bit'], ['character.ZBack,', '16-bit'], ['character.custom,', '16-bit'], ['character.mask,', '16-bit']
		] )

		writer["openexr"]["dataType"].setValue( "float" )
		writer["task"].execute()

		self.assertEqual( self.channelTypesFromHeader( writePath ), [
			['A,', '32-bit'], ['B,', '32-bit'], ['G,', '32-bit'], ['R,', '32-bit'],
			['Z,', '32-bit'], ['ZBack,', '32-bit'], ['custom,', '32-bit'], ['mask,', '32-bit'],
			['character.A,', '32-bit'], ['character.B,', '32-bit'], ['character.G,', '32-bit'], ['character.R,', '32-bit'],
			['character.Z,', '32-bit'], ['character.ZBack,', '32-bit'], ['character.custom,', '32-bit'], ['character.mask,', '32-bit']
		] )

		# Now, lets actually use some per-channel data types
		writer["dataTypeExpression"].setExpression( 'parent["openexr"]["dataType"] = "half" if context.get( "imageWriter:channelName" ) == "R" else "float"' )
		writer["task"].execute()

		self.assertEqual( self.channelTypesFromHeader( writePath ), [
			['A,', '32-bit'], ['B,', '32-bit'], ['G,', '32-bit'], ['R,', '16-bit'],
			['Z,', '32-bit'], ['ZBack,', '32-bit'], ['custom,', '32-bit'], ['mask,', '32-bit'],
			['character.A,', '32-bit'], ['character.B,', '32-bit'], ['character.G,', '32-bit'], ['character.R,', '32-bit'],
			['character.Z,', '32-bit'], ['character.ZBack,', '32-bit'], ['character.custom,', '32-bit'], ['character.mask,', '32-bit']
		] )

		# A weird expression that is basically random
		# ( Note that I have to read the context outside the call to ord(), somehow our expression parser
		# fails to find it if it's inside )
		writer["dataTypeExpression"].setExpression( 'c = context.get( "imageWriter:channelName" ); parent["openexr"]["dataType"] = "float" if ord( c[-1] ) % 2 else "half"' )
		writer["task"].execute()

		self.assertEqual( self.channelTypesFromHeader( writePath ), [
			['A,', '32-bit'], ['B,', '16-bit'], ['G,', '32-bit'], ['R,', '16-bit'],
			['Z,', '16-bit'], ['ZBack,', '32-bit'], ['custom,', '32-bit'], ['mask,', '32-bit'],
			['character.A,', '32-bit'], ['character.B,', '16-bit'], ['character.G,', '32-bit'], ['character.R,', '16-bit'],
			['character.Z,', '16-bit'], ['character.ZBack,', '32-bit'], ['character.custom,', '32-bit'], ['character.mask,', '32-bit']
		] )

		# A more useful expression might affect one layer
		writer["dataTypeExpression"].setExpression( 'parent["openexr"]["dataType"] = "float" if context.get( "imageWriter:layerName" ) == "character" else "half"' )
		writer["task"].execute()

		self.assertEqual( self.channelTypesFromHeader( writePath ), [
			['A,', '16-bit'], ['B,', '16-bit'], ['G,', '16-bit'], ['R,', '16-bit'],
			['Z,', '16-bit'], ['ZBack,', '16-bit'], ['custom,', '16-bit'], ['mask,', '16-bit'],
			['character.A,', '32-bit'], ['character.B,', '32-bit'], ['character.G,', '32-bit'], ['character.R,', '32-bit'],
			['character.Z,', '32-bit'], ['character.ZBack,', '32-bit'], ['character.custom,', '32-bit'], ['character.mask,', '32-bit']
		] )

		# depthDataType still overrides the expression on dataType
		writer["openexr"]["depthDataType"].setValue( "float" )
		writer["task"].execute()

		self.assertEqual( self.channelTypesFromHeader( writePath ), [
			['A,', '16-bit'], ['B,', '16-bit'], ['G,', '16-bit'], ['R,', '16-bit'],
			['Z,', '32-bit'], ['ZBack,', '32-bit'], ['custom,', '16-bit'], ['mask,', '16-bit'],
			['character.A,', '32-bit'], ['character.B,', '32-bit'], ['character.G,', '32-bit'], ['character.R,', '32-bit'],
			['character.Z,', '32-bit'], ['character.ZBack,', '32-bit'], ['character.custom,', '32-bit'], ['character.mask,', '32-bit']
		] )

if __name__ == "__main__":
	unittest.main()
