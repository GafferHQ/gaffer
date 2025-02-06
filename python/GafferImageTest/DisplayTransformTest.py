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
import pathlib
import unittest
import subprocess
import imath

import PyOpenColorIO

import IECore

import Gaffer
import GafferTest
import GafferImage
import GafferImageTest

class DisplayTransformTest( GafferImageTest.ImageTestCase ) :

	imageFile = GafferImageTest.ImageTestCase.imagesPath() / "checker.exr"

	def test( self ) :

		n = GafferImage.ImageReader()
		n["fileName"].setValue( self.imageFile )
		orig = GafferImage.ImageAlgo.image( n["out"] )

		o = GafferImage.DisplayTransform()
		o["in"].setInput( n["out"] )

		o["inputColorSpace"].setValue( "scene_linear" )
		o["display"].setValue( "sRGB - Display" )
		o["view"].setValue( "ACES 1.0 - SDR Video" )

		transform1 = GafferImage.ImageAlgo.image( o["out"] )
		self.assertNotEqual( orig, transform1 )

		o["view"].setValue( "Un-tone-mapped" )
		transform2 = GafferImage.ImageAlgo.image( o["out"] )
		self.assertNotEqual( orig, transform2 )
		self.assertNotEqual( transform1, transform2 )

		o["inputColorSpace"].setValue( "V-Log V-Gamut" )
		transform3 = GafferImage.ImageAlgo.image( o["out"] )
		self.assertNotEqual( orig, transform3 )
		self.assertNotEqual( transform1, transform3 )
		self.assertNotEqual( transform2, transform3 )

	def testHashPassThrough( self ) :

		n = GafferImage.ImageReader()
		n["fileName"].setValue( self.imageFile )

		o = GafferImage.DisplayTransform()
		o["in"].setInput( n["out"] )

		o["display"].setValue( "sRGB - Display" )
		o["view"].setValue( "Raw" ) # No-op view

		self.assertImageHashesEqual( n["out"], o["out"] )
		self.assertImagesEqual( n["out"], o["out"] )

		o["display"].setValue( "sRGB - Display" )
		o["view"].setValue( "ACES 1.0 - SDR Video" )

		self.assertNotEqual( GafferImage.ImageAlgo.image( n["out"] ), GafferImage.ImageAlgo.image( o["out"] ) )

		o["enabled"].setValue( False )

		self.assertImageHashesEqual( n["out"], o["out"] )
		self.assertImagesEqual( n["out"], o["out"] )
		self.assertEqual( n["out"]['format'].hash(), o["out"]['format'].hash() )
		self.assertEqual( n["out"]['dataWindow'].hash(), o["out"]['dataWindow'].hash() )
		self.assertEqual( n["out"]["metadata"].getValue(), o["out"]["metadata"].getValue() )
		self.assertEqual( n["out"]['channelNames'].hash(), o["out"]['channelNames'].hash() )

	def testChannelsAreSeparate( self ) :

		i = GafferImage.ImageReader()
		i["fileName"].setValue( self.imagesPath() / "circles.exr" )

		o = GafferImage.DisplayTransform()
		o["in"].setInput( i["out"] )

		o["inputColorSpace"].setValue( "scene_linear" )

		self.assertNotEqual(
			o["out"].channelDataHash( "R", imath.V2i( 0 ) ),
			o["out"].channelDataHash( "G", imath.V2i( 0 ) )
		)

		self.assertNotEqual(
			o["out"].channelData( "R", imath.V2i( 0 ) ),
			o["out"].channelData( "G", imath.V2i( 0 ) )
		)

	def testPassThrough( self ) :

		i = GafferImage.ImageReader()
		i["fileName"].setValue( self.imageFile )

		o = GafferImage.DisplayTransform()
		o["in"].setInput( i["out"] )
		o["inputColorSpace"].setValue( "scene_linear" )
		o["display"].setValue( "sRGB - Display" )
		o["view"].setValue( "rec709" )

		self.assertEqual( i["out"]["format"].hash(), o["out"]["format"].hash() )
		self.assertEqual( i["out"]["dataWindow"].hash(), o["out"]["dataWindow"].hash() )
		self.assertEqual( i["out"]["metadata"].getValue(), o["out"]["metadata"].getValue() )
		self.assertEqual( i["out"]["channelNames"].hash(), o["out"]["channelNames"].hash() )

		self.assertEqual( i["out"]["format"].getValue(), o["out"]["format"].getValue() )
		self.assertEqual( i["out"]["dataWindow"].getValue(), o["out"]["dataWindow"].getValue() )
		self.assertEqual( i["out"]["metadata"].getValue(), o["out"]["metadata"].getValue() )
		self.assertEqual( i["out"]["channelNames"].getValue(), o["out"]["channelNames"].getValue() )

	def testContext( self ) :

		scriptFileName = self.temporaryDirectory() / "script.gfr"
		contextImageFile = self.temporaryDirectory() / "context.exr"
		contextOverrideImageFile = self.temporaryDirectory() / "context_override.exr"

		s = Gaffer.ScriptNode()

		s["reader"] =  GafferImage.ImageReader()
		s["reader"]["fileName"].setValue( self.imageFile )

		s["dt"] = GafferImage.DisplayTransform()
		s["dt"]["in"].setInput( s["reader"]["out"] )
		s["dt"]["inputColorSpace"].setValue( "scene_linear" )
		s["dt"]["display"].setValue( "default" )
		s["dt"]["view"].setValue( "context" )

		s["writer"] = GafferImage.ImageWriter()
		s["writer"]["fileName"].setValue( contextImageFile )
		s["writer"]["in"].setInput( s["dt"]["out"] )
		s["writer"]["channels"].setValue( "R G B A" )
		s["writer"]["openexr"]["dataType"].setValue( "float" )

		s["fileName"].setValue( scriptFileName )
		s.save()

		env = os.environ.copy()
		env["OCIO"] = str( self.openColorIOPath() / "context.ocio" )
		env["LUT"] = "srgb.spi1d"
		env["CDL"] = "cineon.spi1d"

		subprocess.check_call(
			[ str( Gaffer.executablePath() ), "execute", str( scriptFileName ), "-frames", "1" ],
			stderr = subprocess.PIPE,
			env = env,
		)

		expected = GafferImage.ImageReader()
		expected["fileName"].setValue( self.imagesPath() / "checker_ocio_context.exr" )

		actual = GafferImage.ImageReader()
		actual["fileName"].setValue( contextImageFile )

		# check against expected output
		self.assertImagesEqual( actual["out"], expected["out"], ignoreMetadata = True )

		# override context
		s["writer"]["fileName"].setValue( contextOverrideImageFile )
		s["dt"]["context"].addChild( Gaffer.NameValuePlug( "LUT", IECore.StringData( "cineon.spi1d" ), True, "LUT", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		s["dt"]["context"].addChild( Gaffer.NameValuePlug( "CDL", IECore.StringData( "rec709.spi1d" ), True, "CDL", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		s.save()

		subprocess.check_call(
			[ str( Gaffer.executablePath() ), "execute", str( scriptFileName ), "-frames", "1" ],
			stderr = subprocess.PIPE,
			env = env
		)

		expected["fileName"].setValue( self.imagesPath() / "checker_ocio_context_override.exr" )
		actual["fileName"].setValue( contextOverrideImageFile )

		# check override produce expected output
		self.assertImagesEqual( actual["out"], expected["out"], ignoreMetadata = True )

	def testChangingWorkingSpace( self ) :

		checker = GafferImage.Checkerboard()

		displayTransform = GafferImage.DisplayTransform()
		displayTransform["in"].setInput( checker["out"] )
		displayTransform["display"].setValue( "sRGB - Display" )
		displayTransform["view"].setValue( "ACES 1.0 - SDR Video" )

		with Gaffer.Context() as context :

			GafferImage.OpenColorIOAlgo.setWorkingSpace( context, "scene_linear" )
			tile = displayTransform["out"].channelData( "R", imath.V2i( 0 ) )

			GafferImage.OpenColorIOAlgo.setWorkingSpace( context, "color_picking" )
			self.assertNotEqual( displayTransform["out"].channelData( "R", imath.V2i( 0 ) ), tile )

	def testDisplayAndViewDefaultToConfig( self ) :

		checker = GafferImage.Checkerboard()

		# Test default config

		defaultDisplayTransform = GafferImage.DisplayTransform()
		defaultDisplayTransform["in"].setInput( checker["out"] )

		config = GafferImage.OpenColorIOAlgo.currentConfig()
		explicitDisplayTransform = GafferImage.DisplayTransform()
		explicitDisplayTransform["in"].setInput( checker["out"] )
		explicitDisplayTransform["display"].setValue( config.getDefaultDisplay() )
		explicitDisplayTransform["view"].setValue( config.getDefaultView( config.getDefaultDisplay() ) )

		self.assertImagesEqual( defaultDisplayTransform["out"], explicitDisplayTransform["out"] )

		# Test alternative config

		configPath = self.openColorIOPath() / "context.ocio"
		config = PyOpenColorIO.Config.CreateFromFile( str( configPath ) )

		explicitDisplayTransform["display"].setValue( config.getDefaultDisplay() )
		explicitDisplayTransform["view"].setValue( config.getDefaultView( config.getDefaultDisplay() ) )

		with Gaffer.Context() as context :
			GafferImage.OpenColorIOAlgo.setConfig( context, configPath.as_posix() )
			GafferImage.OpenColorIOAlgo.addVariable( context, "CDL", "rec709.spi1d" )
			GafferImage.OpenColorIOAlgo.addVariable( context, "LUT", "cineon.spi1d" )
			self.assertImagesEqual( defaultDisplayTransform["out"], explicitDisplayTransform["out"] )

if __name__ == "__main__":
	unittest.main()
