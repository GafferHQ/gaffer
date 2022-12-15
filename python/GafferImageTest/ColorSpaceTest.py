##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
#  Copyright (c) 2012-2015, Image Engine Design Inc. All rights reserved.
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
import subprocess
import imath

import IECore

import Gaffer
import GafferTest
import GafferImage
import GafferImageTest

class ColorSpaceTest( GafferImageTest.ImageTestCase ) :

	fileName = GafferImageTest.ImageTestCase.imagesPath() / "checker.exr"

	def test( self ) :

		n = GafferImage.ImageReader()
		n["fileName"].setValue( self.fileName )

		o = GafferImage.ColorSpace()
		o["in"].setInput( n["out"] )

		self.assertImageHashesEqual( n["out"], o["out"] )
		self.assertImagesEqual( n["out"], o["out"] )

		o["inputSpace"].setValue( "linear" )
		o["outputSpace"].setValue( "sRGB" )

		self.assertNotEqual( GafferImage.ImageAlgo.image( n["out"] ), GafferImage.ImageAlgo.image( o["out"] ) )

	def testHashPassThrough( self ) :

		n = GafferImage.ImageReader()
		n["fileName"].setValue( self.fileName )

		o = GafferImage.ColorSpace()
		o["in"].setInput( n["out"] )

		self.assertImageHashesEqual( n["out"], o["out"] )
		self.assertImagesEqual( n["out"], o["out"] )

		o["inputSpace"].setValue( "linear" )
		o["outputSpace"].setValue( "sRGB" )

		self.assertNotEqual( GafferImage.ImageAlgo.image( n["out"] ), GafferImage.ImageAlgo.image( o["out"] ) )

		o["enabled"].setValue( False )

		self.assertImageHashesEqual( n["out"], o["out"] )
		self.assertImagesEqual( n["out"], o["out"] )
		self.assertEqual( n["out"]['format'].hash(), o["out"]['format'].hash() )
		self.assertEqual( n["out"]['dataWindow'].hash(), o["out"]['dataWindow'].hash() )
		self.assertEqual( n["out"]["metadata"].getValue(), o["out"]["metadata"].getValue() )
		self.assertEqual( n["out"]['channelNames'].hash(), o["out"]['channelNames'].hash() )
		self.assertTrue(
			o["out"].channelData( "R", imath.V2i( 0 ), _copy = False ).isSame(
				n["out"].channelData( "R", imath.V2i( 0 ), _copy = False )
			)
		)

		o["enabled"].setValue( True )

		o["inputSpace"].setValue( "linear" )
		o["outputSpace"].setValue( "linear" )
		self.assertImageHashesEqual( n["out"], o["out"] )
		self.assertImagesEqual( n["out"], o["out"] )
		self.assertEqual( n["out"]['format'].hash(), o["out"]['format'].hash() )
		self.assertEqual( n["out"]['dataWindow'].hash(), o["out"]['dataWindow'].hash() )
		self.assertEqual( n["out"]["metadata"].getValue(), o["out"]["metadata"].getValue() )
		self.assertEqual( n["out"]['channelNames'].hash(), o["out"]['channelNames'].hash() )
		self.assertTrue(
			o["out"].channelData( "R", imath.V2i( 0 ), _copy = False ).isSame(
				n["out"].channelData( "R", imath.V2i( 0 ), _copy = False )
			)
		)

	def testImageHashPassThrough( self ) :

		i = GafferImage.ImageReader()
		i["fileName"].setValue( self.fileName )

		o = GafferImage.ColorSpace()
		o["in"].setInput( i["out"] )

		self.assertEqual( GafferImage.ImageAlgo.imageHash( i["out"] ), GafferImage.ImageAlgo.imageHash( o["out"] ) )

		o["inputSpace"].setValue( "linear" )
		o["outputSpace"].setValue( "sRGB" )

		self.assertNotEqual( GafferImage.ImageAlgo.imageHash( i["out"] ), GafferImage.ImageAlgo.imageHash( o["out"] ) )

	def testChannelsAreSeparate( self ) :

		i = GafferImage.ImageReader()
		i["fileName"].setValue( self.imagesPath() / "circles.exr" )

		o = GafferImage.ColorSpace()
		o["in"].setInput( i["out"] )

		o["inputSpace"].setValue( "linear" )
		o["outputSpace"].setValue( "sRGB" )

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
		i["fileName"].setValue( self.fileName )

		o = GafferImage.ColorSpace()
		o["in"].setInput( i["out"] )
		o["inputSpace"].setValue( "linear" )
		o["outputSpace"].setValue( "sRGB" )

		self.assertEqual( i["out"]["format"].hash(), o["out"]["format"].hash() )
		self.assertEqual( i["out"]["dataWindow"].hash(), o["out"]["dataWindow"].hash() )
		self.assertEqual( i["out"]["channelNames"].hash(), o["out"]["channelNames"].hash() )

		self.assertEqual( i["out"]["format"].getValue(), o["out"]["format"].getValue() )
		self.assertEqual( i["out"]["dataWindow"].getValue(), o["out"]["dataWindow"].getValue() )
		self.assertEqual( i["out"]["channelNames"].getValue(), o["out"]["channelNames"].getValue() )

	def testContext( self ) :

		scriptFileName = self.temporaryDirectory() / "script.gfr"
		contextImageFile = self.temporaryDirectory() / "context.#.exr"
		contextOverrideImageFile = self.temporaryDirectory() / "context_override.#.exr"

		s = Gaffer.ScriptNode()

		s["reader"] =  GafferImage.ImageReader()
		s["reader"]["fileName"].setValue( self.fileName )

		s["cs"] = GafferImage.ColorSpace()
		s["cs"]["in"].setInput( s["reader"]["out"] )
		s["cs"]["inputSpace"].setValue( "linear" )
		s["cs"]["outputSpace"].setValue( "context" )


		s["writer"] = GafferImage.ImageWriter()
		s["writer"]["fileName"].setValue( contextImageFile )
		s["writer"]["in"].setInput( s["cs"]["out"] )
		s["writer"]["channels"].setValue( "R G B A" )

		s["fileName"].setValue( scriptFileName )
		s.save()

		env = os.environ.copy()
		env["OCIO"] = self.openColorIOPath() / "context.ocio"
		env["LUT"] = "srgb.spi1d"
		env["CDL"] = "cineon.spi1d"

		subprocess.check_call(
			[ str( Gaffer.executablePath() ), "execute", scriptFileName,"-frames", "1" ],
			stderr = subprocess.PIPE,
			env = env,
		)

		i = GafferImage.ImageReader()
		i["fileName"].setValue( self.imagesPath() / "checker_ocio_context.exr" )

		o = GafferImage.ImageReader()
		o["fileName"].setValue( contextImageFile )

		expected = i["out"]
		context = o["out"]

		# check against expected output
		self.assertImagesEqual( expected, context, ignoreMetadata = True )

		# override context
		s["writer"]["fileName"].setValue( contextOverrideImageFile )
		s["cs"]["context"].addChild( Gaffer.NameValuePlug("LUT", "cineon.spi1d", True, "LUT", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		s["cs"]["context"].addChild( Gaffer.NameValuePlug("CDL", "rec709.spi1d", True, "CDL", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		s.save()

		subprocess.check_call(
			[ str( Gaffer.executablePath() ), "execute", scriptFileName,"-frames", "1" ],
			stderr = subprocess.PIPE,
			env = env
		)

		i = GafferImage.ImageReader()
		i["fileName"].setValue( self.imagesPath() / "checker_ocio_context_override.exr" )

		o = GafferImage.ImageReader()
		o["fileName"].setValue( contextOverrideImageFile )

		expected = i["out"]
		context = o["out"]

		# check override produce expected output
		self.assertImagesEqual( expected, context, ignoreMetadata = True )

	def testSingleChannelImage( self ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.imagesPath() / "blurRange.exr" )
		self.assertEqual( r["out"]["channelNames"].getValue(), IECore.StringVectorData( [ "R" ] ) )

		s = GafferImage.Shuffle()
		s["in"].setInput( r["out"] )
		s["channels"].addChild( s.ChannelPlug( "G", "R" ) )
		s["channels"].addChild( s.ChannelPlug( "B", "R" ) )

		c1 = GafferImage.ColorSpace()
		c1["in"].setInput( r["out"] )
		c1["inputSpace"].setValue( "linear" )
		c1["outputSpace"].setValue( "sRGB" )

		c2 = GafferImage.ColorSpace()
		c2["in"].setInput( s["out"] )
		c2["inputSpace"].setValue( "linear" )
		c2["outputSpace"].setValue( "sRGB" )

		self.assertEqual( c2["out"].channelData( "R", imath.V2i( 0 ) ), c1["out"].channelData( "R", imath.V2i( 0 ) ) )

	def testUnpremultiplied( self ) :

		i = GafferImage.ImageReader()
		i["fileName"].setValue( self.imagesPath() / "circles.exr" )

		shuffleAlpha = GafferImage.Shuffle()
		shuffleAlpha["channels"].addChild( GafferImage.Shuffle.ChannelPlug( "channel" ) )
		shuffleAlpha["in"].setInput( i["out"] )
		shuffleAlpha["channels"]["channel"]["out"].setValue( 'A' )
		shuffleAlpha["channels"]["channel"]["in"].setValue( 'R' )

		gradeAlpha = GafferImage.Grade()
		gradeAlpha["in"].setInput( shuffleAlpha["out"] )
		gradeAlpha["channels"].setValue( '[RGBA]' )
		gradeAlpha["offset"].setValue( imath.Color4f( 0, 0, 0, 0.1 ) )

		unpremultipliedColorSpace = GafferImage.ColorSpace()
		unpremultipliedColorSpace["in"].setInput( gradeAlpha["out"] )
		unpremultipliedColorSpace["processUnpremultiplied"].setValue( True )
		unpremultipliedColorSpace["inputSpace"].setValue( 'linear' )
		unpremultipliedColorSpace["outputSpace"].setValue( 'sRGB' )

		unpremultiply = GafferImage.Unpremultiply()
		unpremultiply["in"].setInput( gradeAlpha["out"] )

		bareColorSpace = GafferImage.ColorSpace()
		bareColorSpace["in"].setInput( unpremultiply["out"] )
		bareColorSpace["inputSpace"].setValue( 'linear' )
		bareColorSpace["outputSpace"].setValue( 'sRGB' )

		premultiply = GafferImage.Premultiply()
		premultiply["in"].setInput( bareColorSpace["out"] )

		# Assert that with a non-zero alpha, processUnpremultiplied is identical to:
		# unpremult, colorSpace, and premult
		self.assertImagesEqual( unpremultipliedColorSpace["out"], premultiply["out"] )

		gradeAlpha["multiply"].setValue( imath.Color4f( 1, 1, 1, 0.0 ) )
		gradeAlpha["offset"].setValue( imath.Color4f( 0, 0, 0, 0.0 ) )

		# Assert that when alpha is zero, processUnpremultiplied doesn't affect the result
		defaultColorSpace = GafferImage.ColorSpace()
		defaultColorSpace["in"].setInput( gradeAlpha["out"] )
		defaultColorSpace["inputSpace"].setValue( 'linear' )
		defaultColorSpace["outputSpace"].setValue( 'sRGB' )

		self.assertImagesEqual( unpremultipliedColorSpace["out"], defaultColorSpace["out"] )

if __name__ == "__main__":
	unittest.main()
