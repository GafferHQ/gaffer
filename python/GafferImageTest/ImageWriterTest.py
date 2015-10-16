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
import platform
import unittest
import shutil
import functools
import datetime
import imath

import IECore

import Gaffer
import GafferTest
import GafferDispatch
import GafferImage
import GafferImageTest

class ImageWriterTest( GafferImageTest.ImageTestCase ) :

	__largeFilePath = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/large.exr" )
	__rgbFilePath = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/rgb.100x100" )
	__negativeDataWindowFilePath = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/checkerWithNegativeDataWindow.200x150" )
	__defaultFormatFile = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/defaultNegativeDisplayWindow.exr" )
	__representativeDeepPath = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/representativeDeepImage.exr" )

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
		r["fileName"].setValue( self.__rgbFilePath+".exr" )

		testFile = self.__testFile( "default", "RB", "exr" )
		self.failIf( os.path.exists( testFile ) )

		w = GafferImage.ImageWriter()
		w["in"].setInput( r["out"] )
		w["fileName"].setValue( testFile )
		w["channels"].setValue( "R B" )
		with Gaffer.Context() :
			w["task"].execute()

		writerOutput = GafferImage.ImageReader()
		writerOutput["fileName"].setValue( testFile )

		channelNames = writerOutput["out"]["channelNames"].getValue()
		self.failUnless( "R" in channelNames )
		self.failUnless( not "G" in channelNames )
		self.failUnless( "B" in channelNames )
		self.failUnless( not "A" in channelNames )

	def testWriteModePlugCompatibility( self ) :
		w = GafferImage.ImageWriter()

		w['writeMode'].setValue( GafferImage.ImageWriter.Mode.Scanline )

		self.assertEqual( w['openexr']['mode'].getValue(), GafferImage.ImageWriter.Mode.Scanline )
		self.assertEqual( w['tiff']['mode'].getValue(), GafferImage.ImageWriter.Mode.Scanline )
		self.assertEqual( w['field3d']['mode'].getValue(), GafferImage.ImageWriter.Mode.Scanline )
		self.assertEqual( w['iff']['mode'].getValue(), GafferImage.ImageWriter.Mode.Scanline )

		w['writeMode'].setValue( GafferImage.ImageWriter.Mode.Tile )

		self.assertEqual( w['openexr']['mode'].getValue(), GafferImage.ImageWriter.Mode.Tile )
		self.assertEqual( w['tiff']['mode'].getValue(), GafferImage.ImageWriter.Mode.Tile )
		self.assertEqual( w['field3d']['mode'].getValue(), GafferImage.ImageWriter.Mode.Tile )
		self.assertEqual( w['iff']['mode'].getValue(), GafferImage.ImageWriter.Mode.Tile )

	def testAcceptsInput( self ) :

		w = GafferImage.ImageWriter()
		p = GafferImage.ImagePlug( direction = Gaffer.Plug.Direction.Out )

		self.failIf( w["preTasks"][0].acceptsInput( p ) )
		self.failUnless( w["in"].acceptsInput( p ) )

	def testTiffWrite( self ) :

		options = {}
		options['maxError'] = 0.003
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
		w1 = GafferImage.ImageWriter()
		w2 = GafferImage.ImageWriter()
		g = GafferImage.Grade()

		s.addChild( g )
		s.addChild( w2 )

		testScanlineFile = self.temporaryDirectory() + "/test.defaultFormat.scanline.exr"
		testTileFile = self.temporaryDirectory() + "/test.defaultFormat.tile.exr"
		self.failIf( os.path.exists( testScanlineFile ) )
		self.failIf( os.path.exists( testTileFile ) )

		GafferImage.FormatPlug.acquireDefaultFormatPlug( s ).setValue(
			GafferImage.Format( imath.Box2i( imath.V2i( -7, -2 ), imath.V2i( 23, 25 ) ), 1. )
		)

		w1["in"].setInput( g["out"] )
		w1["fileName"].setValue( testScanlineFile )
		w1["channels"].setValue( "*" )
		w1["openexr"]["mode"].setValue( GafferImage.ImageWriter.Mode.Scanline )

		w2["in"].setInput( g["out"] )
		w2["fileName"].setValue( testTileFile )
		w2["channels"].setValue( "*" )
		w2["openexr"]["mode"].setValue( GafferImage.ImageWriter.Mode.Tile )

		# Try to execute. In older versions of the ImageWriter this would throw an exception.
		with s.context() :
			w1["task"].execute()
			w2["task"].execute()
		self.failUnless( os.path.exists( testScanlineFile ) )
		self.failUnless( os.path.exists( testTileFile ) )

		# Check the output.
		expectedFile = self.__defaultFormatFile
		expectedOutput = IECore.Reader.create( expectedFile ).read()
		expectedOutput.blindData().clear()

		writerScanlineOutput = IECore.Reader.create( testScanlineFile ).read()
		writerScanlineOutput.blindData().clear()

		writerTileOutput = IECore.Reader.create( testTileFile ).read()
		writerTileOutput.blindData().clear()

		self.assertEqual( writerScanlineOutput, expectedOutput )
		self.assertEqual( writerTileOutput, expectedOutput )

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

					with Gaffer.Context() :
						w["task"].execute()

					reRead["refreshCount"].setValue( reRead["refreshCount"].getValue() + 1 )
					if area.size() != imath.V2i( 0 ):
						self.assertImagesEqual( reRead["out"], trimToDataWindowStage2["out"], ignoreMetadata = True )
					else:
						# We have to write one pixel to file, since OpenEXR doesn't permit empty dataWindow
						onePixelDataWindow = imath.Box2i( imath.V2i( 0, 99 ), imath.V2i( 1, 100 ) )
						self.assertEqual( reRead["out"].dataWindow(), onePixelDataWindow )

						emptyPixelData = IECore.CompoundData( dict( [
							( key,  IECore.CompoundData( {
								"0, 64" : IECore.FloatVectorData() if key != "sampleOffsets"
									else GafferImage.ImagePlug.emptyTileSampleOffsets()
							} ) ) for key in [ "sampleOffsets", "R", "G","B", "A", "Z", "ZBack" ]
						] ) )
						self.assertEqual( GafferImage.ImageAlgo.tiles( reRead["out"] ), emptyPixelData )

	# Write an RGBA image that has a data window to various supported formats and in both scanline and tile modes.
	def __testExtension( self, ext, formatName, options = {}, metadataToIgnore = [] ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.__rgbFilePath+".exr" )
		expectedFile = "{base}.{ext}".format( base=self.__rgbFilePath, ext=ext )

		tests = [ {
			'name': "default",
			'plugs': {},
			'metadata': options.get( "metadata", {} ),
			'maxError': options.get( "maxError", 0.0 ) } ]

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

			self.failIf( os.path.exists( testFile ), "Temporary file already exists : {}".format( testFile ) )

			# Setup the writer.
			w = GafferImage.ImageWriter()
			w["in"].setInput( r["out"] )
			w["fileName"].setValue( testFile )
			w["channels"].setValue( "*" )

			for opt in test['plugs']:
				w[formatName][opt].setValue( test['plugs'][opt] )

			# Execute
			with Gaffer.Context() :
				w["task"].execute()
			self.failUnless( os.path.exists( testFile ), "Failed to create file : {} ({}) : {}".format( ext, name, testFile ) )

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
			expectedMetadata["Artist"] = IECore.StringData( os.environ["USER"] )
			expectedMetadata["DocumentName"] = IECore.StringData( "untitled" )

			for key in overrideMetadata :
				expectedMetadata[key] = overrideMetadata[key]

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

			self.assertImagesEqual( expectedOutput["out"], writerOutput["out"], maxDifference = maxError, ignoreMetadata = True )

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
		r["fileName"].setValue( filePath+".exr" )
		w = GafferImage.ImageWriter()

		testFile = self.__testFile( os.path.basename(filePath), "RGBA", ext )
		expectedFile = filePath+"."+ext

		self.failIf( os.path.exists( testFile ), "Temporary file already exists : {}".format( testFile ) )

		# Setup the writer.
		w["in"].setInput( r["out"] )
		w["fileName"].setValue( testFile )
		w["channels"].setValue( "*" )

		# Execute
		with Gaffer.Context() :
			w["task"].execute()
		self.failUnless( os.path.exists( testFile ), "Failed to create file : {} : {}".format( ext, testFile ) )

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

		self.failUnless( os.path.exists( testFile ) )
		i = IECore.Reader.create( testFile ).read()

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
		writer["fileName"].setValue( self.temporaryDirectory() + "/test.exr" )
		self.assertEqual( writer.hash( c ), IECore.MurmurHash() )

		# now theres a file and an image, we get some output
		constant = GafferImage.Constant()
		writer["in"].setInput( constant["out"] )
		self.assertNotEqual( writer.hash( c ), IECore.MurmurHash() )

		# output doesn't vary by time yet
		self.assertEqual( writer.hash( c ), writer.hash( c2 ) )

		# now it does vary
		writer["fileName"].setValue( self.temporaryDirectory() + "/test.#.exr" )
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

		with s.context() :
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
		r["fileName"].setValue( self.__rgbFilePath+".exr" )
		w = GafferImage.ImageWriter()

		testFile = self.__testFile( "metadataTest", "RGBA", "exr" )
		self.failIf( os.path.exists( testFile ) )

		w["in"].setInput( r["out"] )
		w["fileName"].setValue( testFile )

		with Gaffer.Context() :
			w["task"].execute()
		self.failUnless( os.path.exists( testFile ) )

		result = GafferImage.ImageReader()
		result["fileName"].setValue( testFile )

		self.assertEqual( result["out"]["metadata"].getValue()["DocumentName"].value, "untitled" )

		# add the writer to a script

		s = Gaffer.ScriptNode()
		s.addChild( w )

		with Gaffer.Context() :
			w["task"].execute()

		result["refreshCount"].setValue( result["refreshCount"].getValue() + 1 )
		self.assertEqual( result["out"]["metadata"].getValue()["DocumentName"].value, "untitled" )

		# actually set the script's file name
		s["fileName"].setValue( "/my/gaffer/script.gfr" )

		with Gaffer.Context() :
			w["task"].execute()

		result["refreshCount"].setValue( result["refreshCount"].getValue() + 1 )
		self.assertEqual( result["out"]["metadata"].getValue()["DocumentName"].value, "/my/gaffer/script.gfr" )

	def __testMetadataDoesNotAffectPixels( self, ext, overrideMetadata = {}, metadataToIgnore = [] ) :

		reader = GafferImage.ImageReader()
		reader["fileName"].setValue( self.__rgbFilePath+"."+ext )

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
		self.failIf( os.path.exists( regularWriter["fileName"].getValue() ) )

		misledWriter = GafferImage.ImageWriter()
		misledWriter["in"].setInput( misleadingMetadata["out"] )
		misledWriter["fileName"].setValue( self.__testFile( "misleadingMetadata", "RGBA", ext ) )
		self.failIf( os.path.exists( misledWriter["fileName"].getValue() ) )

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

		self.failUnless( os.path.exists( regularWriter["fileName"].getValue() ) )
		self.failUnless( os.path.exists( misledWriter["fileName"].getValue() ) )

		# Make readers to read back what we wrote out

		misledReader = GafferImage.ImageReader()
		misledReader["fileName"].setInput( misledWriter["fileName"] )

		regularReader = GafferImage.ImageReader()
		regularReader["fileName"].setInput( regularWriter["fileName"] )

		# Check that the pixel data, format and data window has not
		# been changed at all, regardless of which metadata
		# was provided to the writers.

		self.assertImagesEqual( misledWriter["in"], misledReader["out"], ignoreMetadata = True )
		self.assertImagesEqual( misledReader["out"], regularReader["out"], ignoreMetadata = True )

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
		expectedMetadata["Artist"] = IECore.StringData( os.environ["USER"] )
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
		self.failIf( os.path.exists( testFile ) )

		w = GafferImage.ImageWriter()
		w["in"].setInput( c["out"] )
		w["fileName"].setValue( testFile )

		with Gaffer.Context():
			w["task"].execute()
		self.failUnless( os.path.exists( testFile ) )

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
		self.failIf( os.path.exists( testFile ) )

		w = GafferImage.ImageWriter()
		w["in"].setInput( c["out"] )
		w["fileName"].setValue( testFile )

		with Gaffer.Context():
			w["task"].execute()
		self.failUnless( os.path.exists( testFile ) )

		after = GafferImage.ImageReader()
		after["fileName"].setValue( testFile )
		# Check that the data window is the expected single pixel
		self.assertEqual( after["out"]["dataWindow"].getValue(), imath.Box2i( imath.V2i( 0, 99 ), imath.V2i( 1, 100 ) ) )

	def testPixelAspectRatio( self ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.__rgbFilePath+".exr" )
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
		self.failIf( os.path.exists( testFile ) )

		w = GafferImage.ImageWriter()
		w["in"].setInput( f["out"] )
		w["fileName"].setValue( testFile )
		w["channels"].setValue( "*" )

		with Gaffer.Context() :
			w["task"].execute()
		self.failUnless( os.path.exists( testFile ) )

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
		s["w"]["fileName"].setValue( self.temporaryDirectory() + "/test.${ext}" )

		context = Gaffer.Context( s.context() )
		context["ext"] = "tif"
		with context :
			s["w"]["task"].execute()

		self.assertTrue( os.path.isfile( self.temporaryDirectory() + "/test.tif" ) )

	def testErrorMessages( self ) :

		s = Gaffer.ScriptNode()

		s["c"] = GafferImage.Constant()
		s["w"] = GafferImage.ImageWriter()
		s["w"]["in"].setInput( s["c"]["out"] )
		s["w"]["fileName"].setValue( self.temporaryDirectory() + "/test.unsupportedExtension" )

		with s.context() :

			self.assertRaisesRegexp( RuntimeError, "could not find a format writer for", s["w"].execute )

			s["w"]["fileName"].setValue( self.temporaryDirectory() + "/test.tif" )
			s["w"]["task"].execute()

			os.chmod( self.temporaryDirectory() + "/test.tif", 0o444 )
			self.assertRaisesRegexp( RuntimeError, "Could not open", s["w"]["task"].execute )

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
		s["w1"]["fileName"].setValue( self.temporaryDirectory() + "/test1.exr" )

		s["r"] = GafferImage.ImageReader()
		s["r"]["fileName"].setValue( self.temporaryDirectory() + "/test1.exr" )

		s["w2"] = GafferImage.ImageWriter()
		s["w2"]["in"].setInput( s["r"]["out"] )
		s["w2"]["fileName"].setValue( self.temporaryDirectory() + "/test2.exr" )
		s["w2"]["preTasks"][0].setInput( s["w1"]["task"] )

		d = GafferDispatch.LocalDispatcher()
		d["jobsDirectory"].setValue( self.temporaryDirectory() + "/jobs" )

		with s.context() :
			d.dispatch( [ s["w2"] ] )

		self.assertTrue( os.path.isfile( s["w1"]["fileName"].getValue() ) )
		self.assertTrue( os.path.isfile( s["w2"]["fileName"].getValue() ) )

	def testBackgroundDispatch( self ) :

		s = Gaffer.ScriptNode()

		s["c"] = GafferImage.Constant()

		s["w"] = GafferImage.ImageWriter()
		s["w"]["in"].setInput( s["c"]["out"] )
		s["w"]["fileName"].setValue( self.temporaryDirectory() + "/test.exr" )

		d = GafferDispatch.LocalDispatcher()
		d["jobsDirectory"].setValue( self.temporaryDirectory() + "/jobs" )
		d["executeInBackground"].setValue( True )

		with s.context() :
			d.dispatch( [ s["w"] ] )

		d.jobPool().waitForAll()

		self.assertTrue( os.path.isfile( s["w"]["fileName"].getValue() ) )

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
		w["fileName"].setValue( os.path.join( self.temporaryDirectory(), "test.exr" ) )
		w["copyFileName"].setValue( os.path.join( self.temporaryDirectory(), "test2.exr" ) )

		w["task"].execute()

		self.assertTrue( os.path.isfile( w["fileName"].getValue() ) )
		self.assertTrue( os.path.isfile( w["copyFileName"].getValue() ) )

	def testStringMetadata( self ) :

		c = GafferImage.Constant()

		m = GafferImage.ImageMetadata()
		m["in"].setInput( c["out"] )
		m["metadata"].addChild( Gaffer.NameValuePlug( "test", IECore.StringData( "popplewell" ) ) )

		w = GafferImage.ImageWriter()
		w["in"].setInput( m["out"] )
		w["fileName"].setValue( os.path.join( self.temporaryDirectory(), "test.exr" ) )
		w["task"].execute()

		r = GafferImage.ImageReader()
		r["fileName"].setValue( w["fileName"].getValue() )

		self.assertEqual( r["out"]["metadata"].getValue()["test"], m["out"]["metadata"].getValue()["test"] )

	def __testFile( self, mode, channels, ext ) :

		return self.temporaryDirectory() + "/test." + channels + "." + str( mode ) + "." + str( ext )

	def testJpgChroma( self ):

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.__rgbFilePath+".exr" )

		w = GafferImage.ImageWriter()
		w["in"].setInput( r["out"] )

		result = GafferImage.ImageReader()

		chromaSubSamplings = ( "4:4:4", "4:2:2", "4:2:0", "4:1:1", "" )
		for chromaSubSampling in chromaSubSamplings:

			testFile = os.path.join( self.temporaryDirectory(), "chromaSubSampling.{0}.jpg".format( chromaSubSampling ) )

			w["fileName"].setValue( testFile )
			w["jpeg"]["chromaSubSampling"].setValue( chromaSubSampling )

			with Gaffer.Context() :
				w["task"].execute()

			self.failUnless( os.path.exists( testFile ), "Failed to create file : {} : {}".format( chromaSubSampling, testFile ) )

			result["fileName"].setValue( testFile )

			self.assertEqual( result["out"]["metadata"].getValue()["jpeg:subsampling"].value, chromaSubSampling if chromaSubSampling != "" else "4:2:0" )

	def testDPXDataType( self ) :

		image = GafferImage.Constant()

		writer = GafferImage.ImageWriter()
		writer["in"].setInput( image["out"] )

		reader = GafferImage.ImageReader()
		reader["fileName"].setInput( writer["fileName"] )

		for dataType in [ 8, 10, 12, 16 ] :

			writer["fileName"].setValue( "{}/uint{}.dpx".format( self.temporaryDirectory(), dataType ) )
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

			w["fileName"].setValue( "{0}/{1}.{2}".format( self.temporaryDirectory(), dataType, ext ) )
			w[fileFormat]["dataType"].setValue( dataType )

			capturedArguments.clear()
			w.execute()

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

			writer["fileName"].setValue( "{0}/{1}.exr".format( self.temporaryDirectory(), colorSpace ) )
			writer["task"].execute()

			reader["colorSpace"].setValue( colorSpace )
			self.assertImagesEqual( reader["out"], image["out"], ignoreMetadata = True, maxDifference = 0.000001 )

	def testNonDefaultColorSpace( self ) :

		reader = GafferImage.ImageReader()
		reader["fileName"].setValue( self.__rgbFilePath + ".exr" )

		writer = GafferImage.ImageWriter()
		writer["in"].setInput( reader["out"] )

		resultReader = GafferImage.ImageReader()
		resultReader["fileName"].setInput( writer["fileName"] )

		for colorSpace in [ "Cineon", "rec709", "AlexaV3LogC" ] :

			writer["fileName"].setValue( "{0}/{1}.exr".format( self.temporaryDirectory(), colorSpace ) )
			writer["colorSpace"].setValue( colorSpace )

			writer["task"].execute()

			self.failUnless( os.path.exists( writer["fileName"].getValue() ), "Failed to create file : {}".format( writer["fileName"].getValue() ) )

			resultReader["colorSpace"].setValue( colorSpace )
			self.assertImagesEqual( resultReader["out"], reader["out"], ignoreMetadata=True, maxDifference=0.0007 )

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
		writer["fileName"].setValue( "{0}/blankScanlines.jpg".format( self.temporaryDirectory() ) )
		writer["task"].execute()

		# ensure we wrote the file successfully
		reader = GafferImage.ImageReader()
		reader["fileName"].setInput( writer["fileName"] )
		cleanOutput = GafferImage.DeleteChannels()
		cleanOutput["in"].setInput( writer["in"] )
		cleanOutput["channels"].setValue( "A" )
		self.assertImagesEqual( reader["out"], cleanOutput["out"], ignoreMetadata=True, ignoreDataWindow=True, maxDifference=0.05 )

if __name__ == "__main__":
	unittest.main()
