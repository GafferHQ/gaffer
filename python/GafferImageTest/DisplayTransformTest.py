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
import unittest
import subprocess32 as subprocess
import imath

import IECore

import Gaffer
import GafferTest
import GafferImage
import GafferImageTest

class DisplayTransformTest( GafferImageTest.ImageTestCase ) :

	imageFile = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/checker.exr" )

	def test( self ) :

		n = GafferImage.ImageReader()
		n["fileName"].setValue( self.imageFile )
		orig = n["out"].image()

		o = GafferImage.DisplayTransform()
		o["in"].setInput( n["out"] )

		self.assertEqual( orig, o["out"].image() )

		o["inputColorSpace"].setValue( "linear" )
		o["display"].setValue( "default" )
		o["view"].setValue( "rec709" )

		rec709 = o["out"].image()
		self.assertNotEqual( orig, rec709 )

		o["view"].setValue( "sRGB" )
		sRGB = o["out"].image()
		self.assertNotEqual( orig, sRGB )
		self.assertNotEqual( rec709, sRGB )

		o["inputColorSpace"].setValue( "cineon" )
		cineon = o["out"].image()
		self.assertNotEqual( orig, cineon )
		self.assertNotEqual( rec709, cineon )
		self.assertNotEqual( sRGB, cineon )

	def testHashPassThrough( self ) :

		n = GafferImage.ImageReader()
		n["fileName"].setValue( self.imageFile )

		o = GafferImage.DisplayTransform()
		o["in"].setInput( n["out"] )

		self.assertImageHashesEqual( n["out"], o["out"] )
		self.assertImagesEqual( n["out"], o["out"] )

		o["inputColorSpace"].setValue( "linear" )
		o["display"].setValue( "default" )
		o["view"].setValue( "rec709" )

		self.assertNotEqual( n["out"].image(), o["out"].image() )

		o["enabled"].setValue( False )

		self.assertImageHashesEqual( n["out"], o["out"] )
		self.assertImagesEqual( n["out"], o["out"] )
		self.assertEqual( n["out"]['format'].hash(), o["out"]['format'].hash() )
		self.assertEqual( n["out"]['dataWindow'].hash(), o["out"]['dataWindow'].hash() )
		self.assertEqual( n["out"]["metadata"].getValue(), o["out"]["metadata"].getValue() )
		self.assertEqual( n["out"]['channelNames'].hash(), o["out"]['channelNames'].hash() )

		o["enabled"].setValue( True )

		o["inputColorSpace"].setValue( "" )
		self.assertImageHashesEqual( n["out"], o["out"] )
		self.assertImagesEqual( n["out"], o["out"] )
		self.assertEqual( n["out"]['format'].hash(), o["out"]['format'].hash() )
		self.assertEqual( n["out"]['dataWindow'].hash(), o["out"]['dataWindow'].hash() )
		self.assertEqual( n["out"]["metadata"].getValue(), o["out"]["metadata"].getValue() )
		self.assertEqual( n["out"]['channelNames'].hash(), o["out"]['channelNames'].hash() )

	def testImageHashPassThrough( self ) :

		i = GafferImage.ImageReader()
		i["fileName"].setValue( self.imageFile )

		o = GafferImage.DisplayTransform()
		o["in"].setInput( i["out"] )

		self.assertEqual( i["out"].imageHash(), o["out"].imageHash() )

		o["inputColorSpace"].setValue( "linear" )
		o["display"].setValue( "default" )
		o["view"].setValue( "rec709" )

		self.assertNotEqual( i["out"].imageHash(), o["out"].imageHash() )

	def testChannelsAreSeparate( self ) :

		i = GafferImage.ImageReader()
		i["fileName"].setValue( os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/circles.exr" ) )

		o = GafferImage.DisplayTransform()
		o["in"].setInput( i["out"] )

		o["inputColorSpace"].setValue( "linear" )

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
		o["inputColorSpace"].setValue( "linear" )
		o["display"].setValue( "default" )
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

		scriptFileName = self.temporaryDirectory() + "/script.gfr"
		contextImageFile = self.temporaryDirectory() + "/context.#.exr"
		contextOverrideImageFile = self.temporaryDirectory() + "/context_override.#.exr"

		s = Gaffer.ScriptNode()

		s["reader"] =  GafferImage.ImageReader()
		s["reader"]["fileName"].setValue( self.imageFile )

		s["dt"] = GafferImage.DisplayTransform()
		s["dt"]["in"].setInput( s["reader"]["out"] )
		s["dt"]["inputColorSpace"].setValue( "linear" )
		s["dt"]["display"].setValue( "default" )
		s["dt"]["view"].setValue( "context" )


		s["writer"] = GafferImage.ImageWriter()
		s["writer"]["fileName"].setValue( contextImageFile )
		s["writer"]["in"].setInput( s["dt"]["out"] )
		s["writer"]["channels"].setValue( "R G B A" )

		s["fileName"].setValue( scriptFileName )
		s.save()

		env = os.environ.copy()
		env["OCIO"] = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/openColorIO/context.ocio" )
		env["LUT"] = "srgb.spi1d"
		env["CDL"] = "cineon.spi1d"

		subprocess.check_call(
			" ".join(["gaffer", "execute", scriptFileName,"-frames", "1"]),
			shell = True,
			stderr = subprocess.PIPE,
			env = env,
		)

		i = GafferImage.ImageReader()
		i["fileName"].setValue( os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/checker_ocio_context.exr" ) )

		o = GafferImage.ImageReader()
		o["fileName"].setValue( contextImageFile )

		expected = i["out"]
		context = o["out"]

		# check against expected output
		self.assertImagesEqual( expected, context, ignoreMetadata = True )

		# override context
		s["writer"]["fileName"].setValue( contextOverrideImageFile )
		s["dt"]["context"].addChild( Gaffer.NameValuePlug("LUT", IECore.StringData( "cineon.spi1d" ), True, "LUT", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		s["dt"]["context"].addChild( Gaffer.NameValuePlug("CDL", IECore.StringData( "rec709.spi1d" ), True, "CDL", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		s.save()

		subprocess.check_call(
			" ".join(["gaffer", "execute", scriptFileName,"-frames", "1"]),
			shell = True,
			stderr = subprocess.PIPE,
			env = env
		)

		i = GafferImage.ImageReader()
		i["fileName"].setValue( os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/checker_ocio_context_override.exr" ) )

		o = GafferImage.ImageReader()
		o["fileName"].setValue( contextOverrideImageFile )

		expected = i["out"]
		context = o["out"]

		# check override produce expected output
		self.assertImagesEqual( expected, context, ignoreMetadata = True )

if __name__ == "__main__":
	unittest.main()
