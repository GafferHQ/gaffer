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
import shutil
import sys
import unittest

import IECore

import Gaffer
import GafferImage

class ImageWriterTest( unittest.TestCase ) :

	__rgbFilePath = os.path.expandvars( "$GAFFER_ROOT/python/GafferTest/images/rgb.100x100" )
	__negativeDataWindowFilePath = os.path.expandvars( "$GAFFER_ROOT/python/GafferTest/images/checkerWithNegativeDataWindow.200x150" )
	__defaultFormatFile = os.path.expandvars( "$GAFFER_ROOT/python/GafferTest/images/defaultNegativeDisplayWindow.exr" )
	__testDir = "/tmp/testImageWriter/"
	__testFilePath = __testDir + "test"
	__writeModes = [ ("scanline", 0), ("tile", 1) ]

	# Test that we can select which channels to write.
	def testChannelMask( self ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.__rgbFilePath+".exr" )

		for name, mode in self.__writeModes :

			testFile = self.__testFile( name, "RB", "exr" )
			self.failIf( os.path.exists( testFile ) )

			w = GafferImage.ImageWriter()
			w["in"].setInput( r["out"] )
			w["fileName"].setValue( testFile )
			w["channels"].setValue( IECore.StringVectorData( ["R","B"] ) )
			with Gaffer.Context() :
				w.execute()

			writerOutput = GafferImage.ImageReader()
			writerOutput["fileName"].setValue( testFile )

			channelNames = writerOutput["out"]["channelNames"].getValue()
			self.failUnless( "R" in channelNames )
			self.failUnless( not "G" in channelNames )
			self.failUnless( "B" in channelNames )
			self.failUnless( not "A" in channelNames )

	def testAcceptsInput( self ) :

		w = GafferImage.ImageWriter()
		p = GafferImage.ImagePlug( direction = Gaffer.Plug.Direction.Out )

		self.failIf( w['requirements']['requirement0'].acceptsInput( p ) )
		self.failUnless( w["in"].acceptsInput( p ) )

	def testTiffWrite( self ) :
		self.__testExtension( "tif" )

	@unittest.expectedFailure
	def testJpgWrite( self ) :
		self.__testExtension( "jpg", metadataToIgnore = [ "DocumentName", "HostComputer" ] )

	@unittest.expectedFailure
	def testTgaWrite( self ) :
		self.__testExtension( "tga", metadataToIgnore = [ "compression", "HostComputer", "Software" ] )

	def testExrWrite( self ) :
		self.__testExtension( "exr" )

	def testPngWrite( self ) :
		self.__testExtension( "png" )

	# Not sure why IFF fails on scanline - it writes fine as tiles
	@unittest.expectedFailure
	def testIffWrite( self ) :
		self.__testExtension( "iff" )

	def testDefaultFormatWrite( self ) :

		s = Gaffer.ScriptNode()
		w = GafferImage.ImageWriter()
		g = GafferImage.Grade()

		s.addChild( g )
		s.addChild( w )

		testFile = self.__testFilePath + "testBlack.exr"
		self.failIf( os.path.exists( testFile ) )

		GafferImage.Format.setDefaultFormat( s, GafferImage.Format( IECore.Box2i( IECore.V2i( -7, -2 ), IECore.V2i( 22, 24 ) ), 1. ) )
		w["in"].setInput( g["out"] )
		w["fileName"].setValue( testFile )
		w["channels"].setValue( IECore.StringVectorData( g["out"]["channelNames"].getValue() ) )

		# Try to execute. In older versions of the ImageWriter this would throw an exception.
		with s.context() :
			w.execute()
		self.failUnless( os.path.exists( testFile ) )

		# Check the output.
		expectedFile = self.__defaultFormatFile
		expectedOutput = IECore.Reader.create( expectedFile ).read()
		expectedOutput.blindData().clear()

		writerOutput = IECore.Reader.create( testFile ).read()
		writerOutput.blindData().clear()

		self.assertEqual( writerOutput, expectedOutput )


	# Write an RGBA image that has a data window to various supported formats and in both scanline and tile modes.
	def __testExtension( self, ext, metadataToIgnore = [] ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.__rgbFilePath+".exr" )
		w = GafferImage.ImageWriter()

		for name, mode in self.__writeModes :

			# Skip this test if the extension cannot write in tile mode.
			if ( w["writeMode"].getFlags() & Gaffer.Plug.Flags.ReadOnly ) == True and name == "tile":
				continue

			testFile = self.__testFile( name, "RGBA", ext )
			expectedFile = self.__rgbFilePath+"."+ext

			self.failIf( os.path.exists( testFile ) )

			# Setup the writer.
			w["in"].setInput( r["out"] )
			w["fileName"].setValue( testFile )
			w["channels"].setValue( IECore.StringVectorData( r["out"]["channelNames"].getValue() ) )
			if ( w["writeMode"].getFlags() & Gaffer.Plug.Flags.ReadOnly ) == False :
				w["writeMode"].setValue( mode )

			# Execute
			with Gaffer.Context() :
				w.execute()
			self.failUnless( os.path.exists( testFile ) )

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
			expectedMetadata["Artist"] = IECore.StringData( os.getlogin() )
			expectedMetadata["DocumentName"] = IECore.StringData( "untitled" )
			
			# some formats support IPTC standards, and some of the standard metadata
			# is translated automatically by OpenImageIO.
			for key in writerMetadata.keys() :
				if key.startswith( "IPTC:" ) :
					expectedMetadata["IPTC:OriginatingProgram"] = expectedMetadata["Software"]
					expectedMetadata["IPTC:Creator"] = expectedMetadata["Artist"]
					break
			
			# some input files don't contain all the metadata that the ImageWriter
			# will create, and some output files don't support all the metadata
			# that the ImageWriter attempt to create.
			for name in metadataToIgnore :
				if name in writerMetadata :
					del writerMetadata[name]
				if name in expectedMetadata :
					del expectedMetadata[name]
			
			self.assertEqual( expectedMetadata, writerMetadata )
			
			op = IECore.ImageDiffOp()
			res = op(
				imageA = expectedOutput["out"].image(),
				imageB = writerOutput["out"].image()
			)
			self.assertFalse( res.value )

	def testPadDataWindowToDisplayWindowScanline ( self ) :
		self.__testAdjustDataWindowToDisplayWindow( "png", ("scanline", 0) , self.__rgbFilePath )

	def testCropDataWindowToDisplayWindowScanline ( self ) :
		self.__testAdjustDataWindowToDisplayWindow( "png", ("scanline", 0) , self.__negativeDataWindowFilePath )

	# @unittest.expectedFailure
	def testPadDataWindowToDisplayWindowTile ( self ) :
		self.__testAdjustDataWindowToDisplayWindow( "iff", ("tile", 1) , self.__rgbFilePath )

	# @unittest.expectedFailure
	def testCropDataWindowToDisplayWindowTile ( self ) :
		self.__testAdjustDataWindowToDisplayWindow( "iff", ("tile", 1) , self.__negativeDataWindowFilePath )

	def __testAdjustDataWindowToDisplayWindow( self, ext, writeMode, filePath ) :
		r = GafferImage.ImageReader()
		r["fileName"].setValue( filePath+".exr" )
		w = GafferImage.ImageWriter()

		name, mode = writeMode

		testFile = self.__testFile( os.path.basename(filePath), "RGBA", ext )
		expectedFile = filePath+"."+ext

		if os.path.exists( testFile ):
			os.remove( testFile )
		# self.failIf( os.path.exists( testFile ) )

		# Setup the writer.
		w["in"].setInput( r["out"] )
		w["fileName"].setValue( testFile )
		w["channels"].setValue( IECore.StringVectorData( r["out"]["channelNames"].getValue() ) )
		if ( w["writeMode"].getFlags() & Gaffer.Plug.Flags.ReadOnly ) == False :
			w["writeMode"].setValue( mode )

		# Execute
		with Gaffer.Context() :
			w.execute()
		self.failUnless( os.path.exists( testFile ) )

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
		self.assertFalse( res.value )


	def testOffsetDisplayWindowWrite( self ) :

		s = Gaffer.ScriptNode()
		c = GafferImage.Constant()
		s.addChild( c )

		with s.context() :

			format = GafferImage.Format( IECore.Box2i( IECore.V2i( -20, -15 ), IECore.V2i( 29, 14 ) ), 1. )
			GafferImage.Format.setDefaultFormat( s, format )

			self.assertEqual( c["out"]["format"].getValue(), format )

			testFile = self.__testFile( "offsetDisplayWindow", "RGBA", "exr" )
			w = GafferImage.ImageWriter()
			w["in"].setInput( c["out"] )
			w["fileName"].setValue( testFile )

			w.execute()
			
			self.failUnless( os.path.exists( testFile ) )
			i = IECore.Reader.create( testFile ).read()
			i.blindData().clear()

			self.assertEqual( i.displayWindow, format.getDisplayWindow() )

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
		writer["fileName"].setValue( "/tmp/test.exr" )
		self.assertEqual( writer.hash( c ), IECore.MurmurHash() )

		# now theres a file and an image, we get some output
		constant = GafferImage.Constant()
		writer["in"].setInput( constant["out"] )
		self.assertNotEqual( writer.hash( c ), IECore.MurmurHash() )

		# output doesn't vary by time yet
		self.assertEqual( writer.hash( c ), writer.hash( c2 ) )

		# now it does vary
		writer["fileName"].setValue( "/tmp/test.#.exr" )
		self.assertNotEqual( writer.hash( c ), writer.hash( c2 ) )

		# other plugs matter too
		current = writer.hash( c )
		writer["writeMode"].setValue( 1 ) # tile mode
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
			w.execute()
		self.failUnless( os.path.exists( testFile ) )
		
		result = GafferImage.ImageReader()
		result["fileName"].setValue( testFile )
		
		self.assertEqual( result["out"]["metadata"].getValue()["DocumentName"].value, "untitled" )
		
		# add the writer to a script
		
		s = Gaffer.ScriptNode()
		s.addChild( w )
		
		with Gaffer.Context() :
			w.execute()
		
		result["refreshCount"].setValue( result["refreshCount"].getValue() + 1 )
		self.assertEqual( result["out"]["metadata"].getValue()["DocumentName"].value, "untitled" )
		
		# actually set the script's file name
		s["fileName"].setValue( "/my/gaffer/script.gfr" )
		
		with Gaffer.Context() :
			w.execute()
		
		result["refreshCount"].setValue( result["refreshCount"].getValue() + 1 )
		self.assertEqual( result["out"]["metadata"].getValue()["DocumentName"].value, "/my/gaffer/script.gfr" )
	
	def __testMetadataDoesNotAffectPixels( self, ext ) :
		
		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.__rgbFilePath+"."+ext )
		m = GafferImage.ImageMetadata()
		m["in"].setInput( r["out"] )
		# lets tell a few lies
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
		w2["in"].setInput( r["out"] )
		w2["fileName"].setValue( testFile2 )
		w2["channels"].setValue( IECore.StringVectorData( r["out"]["channelNames"].getValue() ) )
		
		inMetadata = w["in"]["metadata"].getValue()
		self.assertEqual( inMetadata["PixelAspectRatio"], IECore.FloatData( 2 ) )
		self.assertEqual( inMetadata["oiio:ColorSpace"], IECore.StringData( "Rec709" ) )
		self.assertEqual( inMetadata["oiio:BitsPerSample"], IECore.IntData( 8 ) )
		self.assertEqual( inMetadata["oiio:UnassociatedAlpha"], IECore.IntData( 1 ) )
		self.assertEqual( inMetadata["oiio:Gamma"], IECore.FloatData( 0.25 ) )
		
		with Gaffer.Context() :
			w.execute()
			w2.execute()
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
		expectedMetadata["Artist"] = IECore.StringData( os.getlogin() )
		expectedMetadata["DocumentName"] = IECore.StringData( "untitled" )
		# some formats support IPTC standards, and some of the standard metadata
		# is translated automatically by OpenImageIO.
		for key in afterMetadata.keys() :
			if key.startswith( "IPTC:" ) :
				expectedMetadata["IPTC:OriginatingProgram"] = expectedMetadata["Software"]
				expectedMetadata["IPTC:Creator"] = expectedMetadata["Artist"]
				break
		
		self.assertEqual( afterMetadata, expectedMetadata )
		self.assertEqual( afterMetadata, beforeMetadata )
	
	def testExrMetadata( self ) :
		
		self.__testMetadataDoesNotAffectPixels( "exr" )
	
	def testTiffMetadata( self ) :
		
		self.__testMetadataDoesNotAffectPixels( "tif" )
	
	def testPixelAspectRatio( self ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.__rgbFilePath+".exr" )
		self.assertEqual( r["out"]["format"].getValue().getPixelAspect(), 1 )
		self.assertEqual( r["out"]["metadata"].getValue()["PixelAspectRatio"], IECore.FloatData( 1 ) )
		
		# change the Format pixel aspect
		f = GafferImage.Reformat()
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
			w.execute()
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

		s["b"]["e"]["expression"].setValue( 'parent["w"]["user"]["s"] = parent["p1"]; parent["w"]["fileName"] = parent["p2"]' )

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
		s["w"]["fileName"].setValue( self.__testDir + "/test.${ext}" )

		context = Gaffer.Context( s.context() )
		context["ext"] = "tif"
		with context :
			s["w"].execute()

		self.assertTrue( os.path.isfile( self.__testDir + "/test.tif" ) )

	def testErrorMessages( self ) :

		s = Gaffer.ScriptNode()

		s["c"] = GafferImage.Constant()
		s["w"] = GafferImage.ImageWriter()
		s["w"]["in"].setInput( s["c"]["out"] )
		s["w"]["fileName"].setValue( self.__testDir + "/test.unsupportedExtension" )

		with s.context() :

			self.assertRaisesRegexp( RuntimeError, "could not find a format writer for", s["w"].execute )

			s["w"]["fileName"].setValue( self.__testDir + "/test.tif" )
			s["w"].execute()

			os.chmod( self.__testDir + "/test.tif", 0o444 )
			self.assertRaisesRegexp( RuntimeError, "Could not open", s["w"].execute )

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
		s["w1"]["fileName"].setValue( self.__testDir + "/test1.exr" )

		s["r"] = GafferImage.ImageReader()
		s["r"]["fileName"].setValue( self.__testDir + "/test1.exr" )

		s["w2"] = GafferImage.ImageWriter()
		s["w2"]["in"].setInput( s["r"]["out"] )
		s["w2"]["fileName"].setValue( self.__testDir + "/test2.exr" )
		s["w2"]["requirements"][0].setInput( s["w1"]["requirement"] )

		d = Gaffer.LocalDispatcher()
		d["jobsDirectory"].setValue( self.__testDir + "/jobs" )

		with s.context() :
			d.dispatch( [ s["w2"] ] )

		self.assertTrue( os.path.isfile( s["w1"]["fileName"].getValue() ) )
		self.assertTrue( os.path.isfile( s["w2"]["fileName"].getValue() ) )

	def tearDown( self ) :

		if os.path.isdir( self.__testDir ) :
			shutil.rmtree( self.__testDir )

	def __testFile( self, mode, channels, ext ) :

		return self.__testFilePath+"."+channels+"."+str( mode )+"."+str( ext )

if __name__ == "__main__":
	unittest.main()

