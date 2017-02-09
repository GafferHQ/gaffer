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

import IECore

import Gaffer
import GafferDispatch
import GafferImage
import GafferImageTest

class ImageWriterTest( GafferImageTest.ImageTestCase ) :

	__largeFilePath = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/large.exr" )
	__rgbFilePath = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/rgb.100x100" )
	__negativeDataWindowFilePath = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/checkerWithNegativeDataWindow.200x150" )
	__defaultFormatFile = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/defaultNegativeDisplayWindow.exr" )

	longMessage = True

	# Test that we can select which channels to write.
	def testChannelMask( self ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.__rgbFilePath+".exr" )

		testFile = self.__testFile( "default", "RB", "exr" )
		self.failIf( os.path.exists( testFile ) )

		w = GafferImage.ImageWriter()
		w["in"].setInput( r["out"] )
		w["fileName"].setValue( testFile )
		w["channels"].setValue( IECore.StringVectorData( ["R","B"] ) )
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
		options['maxError'] = 0.1
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

		self.__testExtension( "tif", "tiff", options = options, metadataToIgnore = [ "tiff:RowsPerStrip" ] )

	def testJpgWrite( self ) :
		options = {}
		options['maxError'] = 0.1
		options['plugs'] = {}
		options['plugs']['compressionQuality'] = [
				{ 'value': 10 },
				{ 'value': 20 },
				{ 'value': 30 },
				{ 'value': 40 },
				{ 'value': 50 },
				{ 'value': 60 },
				{ 'value': 70 },
				{ 'value': 80 },
				{ 'value': 90 },
				{ 'value': 100 },
			]

		self.__testExtension( "jpg", "jpeg", options = options, metadataToIgnore = [ "DocumentName", "HostComputer" ] )

	def testTgaWrite( self ) :
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
		options['metadata'] = { 'compression' : IECore.StringData( "zip" ) }
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

	def testDpxWrite( self ) :
		options = {}
		options['maxError'] = 0.1
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
		options['maxError'] = 0.1
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
			GafferImage.Format( IECore.Box2i( IECore.V2i( -7, -2 ), IECore.V2i( 23, 25 ) ), 1. )
		)

		w1["in"].setInput( g["out"] )
		w1["fileName"].setValue( testScanlineFile )
		w1["channels"].setValue( IECore.StringVectorData( g["out"]["channelNames"].getValue() ) )
		w1["openexr"]["mode"].setValue( GafferImage.ImageWriter.Mode.Scanline )

		w2["in"].setInput( g["out"] )
		w2["fileName"].setValue( testTileFile )
		w2["channels"].setValue( IECore.StringVectorData( g["out"]["channelNames"].getValue() ) )
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
		self.assertEqual( w["openexr"]["compression"].getValue(), "zip" )
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

	# Write an RGBA image that has a data window to various supported formats and in both scanline and tile modes.
	def __testExtension( self, ext, formatName, options = {}, metadataToIgnore = [] ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.__rgbFilePath+".exr" )

		expectedFile = self.__rgbFilePath+"."+ext

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
			w["channels"].setValue( IECore.StringVectorData( r["out"]["channelNames"].getValue() ) )

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

			# some input files don't contain all the metadata that the ImageWriter
			# will create, and some output files don't support all the metadata
			# that the ImageWriter attempt to create.
			for metaName in metadataToIgnore :
				if metaName in writerMetadata :
					del writerMetadata[metaName]
				if metaName in expectedMetadata :
					del expectedMetadata[metaName]

			for metaName in expectedMetadata.keys() :
				self.assertTrue( metaName in writerMetadata.keys(), "Writer Metadata missing expected key \"{}\" set to \"{}\" : {} ({})".format(metaName, str(expectedMetadata[metaName]), ext, name) )
				self.assertEqual( expectedMetadata[metaName], writerMetadata[metaName], "Metadata does not match for key \"{}\" : {} ({})".format(metaName, ext, name) )

			op = IECore.ImageDiffOp()
			op["maxError"].setValue( maxError )
			res = op(
				imageA = expectedOutput["out"].image(),
				imageB = writerOutput["out"].image()
			)

			if res.value :
				matchingError = 0.0
				for i in range( 10 ) :
					maxError += 0.1
					op["maxError"].setValue( maxError )
					res = op(
						imageA = expectedOutput["out"].image(),
						imageB = writerOutput["out"].image()
					)

					if not res.value :
						matchingError = maxError
						break

				if matchingError > 0.0 :
					self.assertFalse( True, "Image data does not match : {} ({}). Matches with max error of {}".format( ext, name, matchingError ) )
				else:
					self.assertFalse( True, "Image data does not match : {} ({}).".format( ext, name ) )

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

	# @unittest.expectedFailure
	def testPadDataWindowToDisplayWindowTile ( self ) :
		self.__testAdjustDataWindowToDisplayWindow( "iff", self.__rgbFilePath )

	# @unittest.expectedFailure
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
		w["channels"].setValue( IECore.StringVectorData( r["out"]["channelNames"].getValue() ) )

		# Execute
		with Gaffer.Context() :
			w["task"].execute()
		self.failUnless( os.path.exists( testFile ), "Failed to create file : {} : {}".format( ext, testFile ) )

		# Check the output.
		expectedOutput = GafferImage.ImageReader()
		expectedOutput["fileName"].setValue( expectedFile )

		writerOutput = GafferImage.ImageReader()
		writerOutput["fileName"].setValue( testFile )

		op = IECore.ImageDiffOp()
		res = op(
			imageA = expectedOutput["out"].image(),
			imageB = writerOutput["out"].image()
		)
		self.assertFalse( res.value, "Image data does not match : {}".format(ext) )


	def testOffsetDisplayWindowWrite( self ) :

		c = GafferImage.Constant()
		format = GafferImage.Format( IECore.Box2i( IECore.V2i( -20, -15 ), IECore.V2i( 29, 14 ) ), 1. )
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
		writer["channels"].setValue( IECore.StringVectorData( [ "R" ] ) )
		self.assertNotEqual( writer.hash( c ), current )

	def testPassThrough( self ) :

		s = Gaffer.ScriptNode()

		s["c"] = GafferImage.Constant()
		s["w"] = GafferImage.ImageWriter()
		s["w"]["in"].setInput( s["c"]["out"] )

		with s.context() :
			ci = s["c"]["out"].image()
			wi = s["w"]["out"].image()

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

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.__rgbFilePath+"."+ext )
		d = GafferImage.DeleteImageMetadata()
		d["in"].setInput( r["out"] )
		m = GafferImage.ImageMetadata()
		m["in"].setInput( d["out"] )
		# lets tell a few lies
		# IPTC:Creator will have the current username appended to the end of
		# the existing one, creating a list of creators. Blank it out for
		# this test
		d["names"].setValue( "IPTC:Creator" )
		m["metadata"].addMember( "PixelAspectRatio", IECore.FloatData( 2 ) )
		m["metadata"].addMember( "oiio:ColorSpace", IECore.StringData( "Rec709" ) )
		m["metadata"].addMember( "oiio:BitsPerSample", IECore.IntData( 8 ) )
		m["metadata"].addMember( "oiio:UnassociatedAlpha", IECore.IntData( 1 ) )
		m["metadata"].addMember( "oiio:Gamma", IECore.FloatData( 0.25 ) )

		testFile = self.__testFile( "metadataHasNoAffect", "RGBA", ext )
		self.failIf( os.path.exists( testFile ) )

		w = GafferImage.ImageWriter()
		w["in"].setInput( m["out"] )
		w["fileName"].setValue( testFile )
		w["channels"].setValue( IECore.StringVectorData( m["out"]["channelNames"].getValue() ) )

		testFile2 = self.__testFile( "noNewMetadata", "RGBA", ext )
		self.failIf( os.path.exists( testFile2 ) )

		w2 = GafferImage.ImageWriter()
		w2["in"].setInput( d["out"] )
		w2["fileName"].setValue( testFile2 )
		w2["channels"].setValue( IECore.StringVectorData( r["out"]["channelNames"].getValue() ) )

		inMetadata = w["in"]["metadata"].getValue()
		self.assertEqual( inMetadata["PixelAspectRatio"], IECore.FloatData( 2 ) )
		self.assertEqual( inMetadata["oiio:ColorSpace"], IECore.StringData( "Rec709" ) )
		self.assertEqual( inMetadata["oiio:BitsPerSample"], IECore.IntData( 8 ) )
		self.assertEqual( inMetadata["oiio:UnassociatedAlpha"], IECore.IntData( 1 ) )
		self.assertEqual( inMetadata["oiio:Gamma"], IECore.FloatData( 0.25 ) )

		with Gaffer.Context() :
			w["task"].execute()
			w2["task"].execute()
		self.failUnless( os.path.exists( testFile ) )
		self.failUnless( os.path.exists( testFile2 ) )

		after = GafferImage.ImageReader()
		after["fileName"].setValue( testFile )

		before = GafferImage.ImageReader()
		before["fileName"].setValue( testFile2 )

		inImage = w["in"].image()
		afterImage = after["out"].image()
		beforeImage = before["out"].image()

		inImage.blindData().clear()
		afterImage.blindData().clear()
		beforeImage.blindData().clear()

		self.assertEqual( afterImage, inImage )
		self.assertEqual( afterImage, beforeImage )

		self.assertEqual( after["out"]["format"].getValue(), r["out"]["format"].getValue() )
		self.assertEqual( after["out"]["format"].getValue(), before["out"]["format"].getValue() )

		self.assertEqual( after["out"]["dataWindow"].getValue(), r["out"]["dataWindow"].getValue() )
		self.assertEqual( after["out"]["dataWindow"].getValue(), before["out"]["dataWindow"].getValue() )

		afterMetadata = after["out"]["metadata"].getValue()
		beforeMetadata = before["out"]["metadata"].getValue()
		expectedMetadata = r["out"]["metadata"].getValue()
		# they were written at different times so we can't expect those values to match
		beforeMetadata["DateTime"] = afterMetadata["DateTime"]
		expectedMetadata["DateTime"] = afterMetadata["DateTime"]
		# the writer adds several standard attributes that aren't in the original file
		expectedMetadata["Software"] = IECore.StringData( "Gaffer " + Gaffer.About.versionString() )
		expectedMetadata["HostComputer"] = IECore.StringData( platform.node() )
		expectedMetadata["Artist"] = IECore.StringData( os.environ["USER"] )
		expectedMetadata["DocumentName"] = IECore.StringData( "untitled" )

		self.__addExpectedIPTCMetadata( afterMetadata, expectedMetadata )

		for key in overrideMetadata :
			expectedMetadata[key] = overrideMetadata[key]
			beforeMetadata[key] = overrideMetadata[key]

		for key in metadataToIgnore :
			if key in expectedMetadata :
				del expectedMetadata[key]
			if key in beforeMetadata :
				del beforeMetadata[key]
			if key in afterMetadata :
				del afterMetadata[key]

		for metaName in expectedMetadata.keys() :
			self.assertTrue( metaName in afterMetadata.keys(), "Writer Metadata missing expected key \"{}\" set to \"{}\" : {}".format(metaName, str(expectedMetadata[metaName]), ext) )
			self.assertEqual( expectedMetadata[metaName], afterMetadata[metaName], "Metadata does not match for key \"{}\" : {}".format(metaName, ext) )

		for metaName in beforeMetadata.keys() :
			self.assertTrue( metaName in afterMetadata.keys(), "Writer Metadata missing expected key \"{}\" set to \"{}\" : {}".format(metaName, str(beforeMetadata[metaName]), ext) )
			self.assertEqual( beforeMetadata[metaName], afterMetadata[metaName], "Metadata does not match for key \"{}\" : {}".format(metaName, ext) )

	def testExrMetadata( self ) :

		self.__testMetadataDoesNotAffectPixels(
			"exr",
			overrideMetadata = {
				"compression" : IECore.StringData( "zip" )
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

	def testWriteEmptyImage( self ) :

		i = GafferImage.Constant()
		i["format"].setValue( GafferImage.Format( IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 100 ) ), 1 ) )

		c = GafferImage.Crop()
		c["areaSource"].setValue( GafferImage.Crop.AreaSource.Area )
		c["area"].setValue( IECore.Box2i( IECore.V2i( 40 ), IECore.V2i( 40 ) ) )
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
		# Check that the data window and the display window are the same
		self.assertEqual( after["out"]["format"].getValue().getDisplayWindow(), after["out"]["dataWindow"].getValue() )


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
		w["channels"].setValue( IECore.StringVectorData( f["out"]["channelNames"].getValue() ) )

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

		with Gaffer.UndoContext( s ) :
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
		m["metadata"].addMember( "test", IECore.StringData( "popplewell" ) )

		w = GafferImage.ImageWriter()
		w["in"].setInput( m["out"] )
		w["fileName"].setValue( os.path.join( self.temporaryDirectory(), "test.exr" ) )
		w["task"].execute()

		r = GafferImage.ImageReader()
		r["fileName"].setValue( w["fileName"].getValue() )

		self.assertEqual( r["out"]["metadata"].getValue()["test"], m["out"]["metadata"].getValue()["test"] )

	def __testFile( self, mode, channels, ext ) :

		return self.temporaryDirectory() + "/test." + channels + "." + str( mode ) + "." + str( ext )

if __name__ == "__main__":
	unittest.main()
