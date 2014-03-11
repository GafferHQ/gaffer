##########################################################################
#  
#  Copyright (c) 2013-2014, Image Engine Design Inc. All rights reserved.
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
import unittest
import IECore
import Gaffer
import GafferImage
import sys

class ImageWriterTest( unittest.TestCase ) :
	
	__rgbFilePath = os.path.expandvars( "$GAFFER_ROOT/python/GafferTest/images/rgb.100x100" )
	__defaultFormatFile = os.path.expandvars( "$GAFFER_ROOT/python/GafferTest/images/defaultNegativeDisplayWindow.exr" )
	__testFilePath = "/tmp/test"
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
			w.execute( [ Gaffer.Context() ] )
				
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

	# Outputting RGBA images with JPG doesn't work but it should... this is a known issue and needs fixing.
	def testJpgWrite( self ) :
		self.__testExtension( "jpg" )

	def testTgaWrite( self ) :
		self.__testExtension( "tga" )

	def testExrWrite( self ) :
		self.__testExtension( "exr" )

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
		w.execute( [ s.context() ] )
		self.failUnless( os.path.exists( testFile ) )
		
		# Check the output.
		expectedFile = self.__defaultFormatFile
		expectedOutput = IECore.Reader.create( expectedFile ).read()
		expectedOutput.blindData().clear()
		
		writerOutput = IECore.Reader.create( testFile ).read()
		writerOutput.blindData().clear()
		
		self.assertEqual( writerOutput, expectedOutput )
		
		
	# Write an RGBA image that has a data window to various supported formats and in both scanline and tile modes.
	def __testExtension( self, ext ) :
		
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
			w.execute( [ Gaffer.Context() ] )
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

	def testOffsetDisplayWinodowWrite( self ) :

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

			# Execute
			w.execute( [ Gaffer.Context() ] )
			self.failUnless( os.path.exists( testFile ) )
			i = IECore.Reader.create( testFile ).read()
			i.blindData().clear()

			self.assertEqual( i.displayWindow, format.getDisplayWindow() )

	def tearDown( self ) :
	
		files = [
			self.__testFilePath + "testBlack.exr",
			self.__testFile( "scanline", "RGBA", "jpg" ),
			self.__testFile( "offsetDisplayWindow", "RGBA", "exr" )
		]

		for f in files :
			if os.path.exists( f ) :
				os.remove( f )
		
		for name, mode in self.__writeModes :
			testFileRB = self.__testFile( name, "RB", "exr" )
			if os.path.exists( testFileRB ) :
				os.remove( testFileRB )
		
			exts = ["exr", "tga", "tif", "jpg"]	
			for ext in exts :
				testFile = self.__testFile( name, "RGBA", ext )
				if os.path.exists( testFile ) :
					os.remove( testFile )
				

	def __testFile( self, mode, channels, ext ) :

		return self.__testFilePath+"."+channels+"."+str( mode )+"."+str( ext )

if __name__ == "__main__":
	unittest.main()

