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

import PyOpenColorIO

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

		o["inputSpace"].setValue( "scene_linear" )
		o["outputSpace"].setValue( "color_picking" )

		self.assertNotEqual( GafferImage.ImageAlgo.image( n["out"] ), GafferImage.ImageAlgo.image( o["out"] ) )

	def testHashPassThrough( self ) :

		n = GafferImage.ImageReader()
		n["fileName"].setValue( self.fileName )

		o = GafferImage.ColorSpace()
		o["in"].setInput( n["out"] )

		self.assertImageHashesEqual( n["out"], o["out"] )
		self.assertImagesEqual( n["out"], o["out"] )

		o["inputSpace"].setValue( "scene_linear" )
		o["outputSpace"].setValue( "color_picking" )

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

		o["inputSpace"].setValue( "scene_linear" )
		o["outputSpace"].setValue( "scene_linear" )
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

		o["inputSpace"].setValue( "scene_linear" )
		o["outputSpace"].setValue( "color_picking" )

		self.assertNotEqual( GafferImage.ImageAlgo.imageHash( i["out"] ), GafferImage.ImageAlgo.imageHash( o["out"] ) )

	def testChannelsAreSeparate( self ) :

		i = GafferImage.ImageReader()
		i["fileName"].setValue( self.imagesPath() / "circles.exr" )

		o = GafferImage.ColorSpace()
		o["in"].setInput( i["out"] )

		o["inputSpace"].setValue( "scene_linear" )
		o["outputSpace"].setValue( "color_picking" )

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
		o["inputSpace"].setValue( "scene_linear" )
		o["outputSpace"].setValue( "color_picking" )

		self.assertEqual( i["out"]["format"].hash(), o["out"]["format"].hash() )
		self.assertEqual( i["out"]["dataWindow"].hash(), o["out"]["dataWindow"].hash() )
		self.assertEqual( i["out"]["channelNames"].hash(), o["out"]["channelNames"].hash() )

		self.assertEqual( i["out"]["format"].getValue(), o["out"]["format"].getValue() )
		self.assertEqual( i["out"]["dataWindow"].getValue(), o["out"]["dataWindow"].getValue() )
		self.assertEqual( i["out"]["channelNames"].getValue(), o["out"]["channelNames"].getValue() )

	def testContextPlugs( self ) :

		scriptFileName = self.temporaryDirectory() / "script.gfr"
		contextImageFile = self.temporaryDirectory() / "context.exr"
		contextOverrideImageFile = self.temporaryDirectory() / "context_override.exr"

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
		s["cs"]["context"].addChild( Gaffer.NameValuePlug( "LUT", "cineon.spi1d", True, "LUT", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		s["cs"]["context"].addChild( Gaffer.NameValuePlug( "CDL", "rec709.spi1d", True, "CDL", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
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

	def testConfigFromGafferContext( self ) :

		reader = GafferImage.ImageReader()
		reader["fileName"].setValue( self.fileName )

		colorSpace = GafferImage.ColorSpace()
		colorSpace["in"].setInput( reader["out"] )
		colorSpace["inputSpace"].setValue( "linear" )
		colorSpace["outputSpace"].setValue( "context" )

		expected = GafferImage.ImageReader()
		expected["fileName"].setValue( self.imagesPath() / "checker_ocio_context.exr" )

		with Gaffer.Context() as c :

			GafferImage.OpenColorIOAlgo.setConfig( c, ( self.openColorIOPath() / "context.ocio" ).as_posix() )
			GafferImage.OpenColorIOAlgo.addVariable( c, "LUT", "srgb.spi1d" )
			GafferImage.OpenColorIOAlgo.addVariable( c, "CDL", "cineon.spi1d" )

			self.assertImagesEqual( expected["out"], colorSpace["out"], maxDifference = 0.0002, ignoreMetadata = True )

	def testSingleChannelImage( self ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.imagesPath() / "blurRange.exr" )
		self.assertEqual( r["out"]["channelNames"].getValue(), IECore.StringVectorData( [ "R" ] ) )

		s = GafferImage.Shuffle()
		s["in"].setInput( r["out"] )
		s["shuffles"].addChild( Gaffer.ShufflePlug( "R", "G" ) )
		s["shuffles"].addChild( Gaffer.ShufflePlug( "R", "B" ) )

		# This test is primarily to check that the ColorSpace node doesn't pull
		# on non-existent input channels, and can still transform a single-channel
		# image. In order for the transform to be comparable to an RGB image, we
		# must test with a transform that contains no channel cross-talk, hence the
		# use of simple gamma encodings with identical primaries for our input and
		# output spaces.

		c1 = GafferImage.ColorSpace()
		c1["in"].setInput( r["out"] )
		c1["inputSpace"].setValue( "Gamma 2.2 Rec.709 - Texture" )
		c1["outputSpace"].setValue( "Gamma 2.4 Rec.709 - Texture" )

		c2 = GafferImage.ColorSpace()
		c2["in"].setInput( s["out"] )
		c2["inputSpace"].setValue( "Gamma 2.2 Rec.709 - Texture" )
		c2["outputSpace"].setValue( "Gamma 2.4 Rec.709 - Texture" )

		self.assertEqual( c2["out"].channelData( "R", imath.V2i( 0 ) ), c1["out"].channelData( "R", imath.V2i( 0 ) ) )

	def testUnpremultiplied( self ) :

		i = GafferImage.ImageReader()
		i["fileName"].setValue( self.imagesPath() / "circles.exr" )

		shuffleAlpha = GafferImage.Shuffle()
		shuffleAlpha["shuffles"].addChild( Gaffer.ShufflePlug( "R", "A" ) )
		shuffleAlpha["in"].setInput( i["out"] )

		gradeAlpha = GafferImage.Grade()
		gradeAlpha["in"].setInput( shuffleAlpha["out"] )
		gradeAlpha["channels"].setValue( '[RGBA]' )
		gradeAlpha["offset"].setValue( imath.Color4f( 0, 0, 0, 0.1 ) )

		unpremultipliedColorSpace = GafferImage.ColorSpace()
		unpremultipliedColorSpace["in"].setInput( gradeAlpha["out"] )
		unpremultipliedColorSpace["processUnpremultiplied"].setValue( True )
		unpremultipliedColorSpace["inputSpace"].setValue( "scene_linear" )
		unpremultipliedColorSpace["outputSpace"].setValue( "color_picking" )

		unpremultiply = GafferImage.Unpremultiply()
		unpremultiply["in"].setInput( gradeAlpha["out"] )

		bareColorSpace = GafferImage.ColorSpace()
		bareColorSpace["in"].setInput( unpremultiply["out"] )
		bareColorSpace["inputSpace"].setValue( "scene_linear" )
		bareColorSpace["outputSpace"].setValue( "color_picking" )

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
		defaultColorSpace["inputSpace"].setValue( "scene_linear" )
		defaultColorSpace["outputSpace"].setValue( "color_picking" )

		self.assertImagesEqual( unpremultipliedColorSpace["out"], defaultColorSpace["out"] )

	def testDeepTileWithNoSamples( self ) :

		reader = GafferImage.ImageReader()
		reader["fileName"].setValue( GafferImageTest.ImageTestCase.imagesPath() / "representativeDeepImage.exr" )

		crop = GafferImage.Crop()
		crop["in"].setInput( reader["out"] )
		crop["area"].setValue( imath.Box2i( imath.V2i( 0, 47 ), imath.V2i( 13, 59 ) ) )
		self.assertEqual( sum( crop["out"].sampleOffsets( imath.V2i( 0 ) ) ), 0 )
		self.assertEqual( crop["out"].channelData( "R", imath.V2i( 0 ) ), IECore.FloatVectorData() )

		colorSpace = GafferImage.ColorSpace()
		colorSpace["in"].setInput( crop["out"] )
		colorSpace["inputSpace"].setValue( "scene_linear" )
		colorSpace["outputSpace"].setValue( "color_picking" )

		self.assertImagesEqual( colorSpace["out"], colorSpace["in"] )

	def testRolePassThrough( self ) :

		# There's nothing particularly special about this image, except that it contains
		# pixels that don't round-trip through unpremultiplication and re-premultiplication.

		reader = GafferImage.ImageReader()
		reader["fileName"].setValue( GafferImageTest.ImageTestCase.imagesPath() / "mergeBoundariesRef.exr" )

		# This color transform should be a no-op, but if we don't realise that
		# then we'll end up modifying the pixels slightly by an unnecessary
		# unpremult and repremult.

		colorSpace = GafferImage.ColorSpace()
		colorSpace["in"].setInput( reader["out"] )
		colorSpace["processUnpremultiplied"].setValue( True )
		colorSpace["inputSpace"].setValue( PyOpenColorIO.ROLE_SCENE_LINEAR )
		colorSpace["outputSpace"].setValue(
			PyOpenColorIO.GetCurrentConfig().getCanonicalName(
				PyOpenColorIO.ROLE_SCENE_LINEAR
			)
		)

		self.assertImagesEqual( colorSpace["out"], reader["out"] )
		self.assertImageHashesEqual( colorSpace["out"], reader["out"] )

	def testEmptyColorSpaceIsSameAsWorkingSpace( self ) :

		checker = GafferImage.Checkerboard()

		colorSpace1 = GafferImage.ColorSpace()
		colorSpace1["in"].setInput( checker["out"] )
		colorSpace1["inputSpace"].setValue( "scene_linear" )
		colorSpace1["outputSpace"].setValue( "color_picking" )

		self.assertNotEqual(
			colorSpace1["out"].channelData( "R", imath.V2i( 0 ) ),
			colorSpace1["in"].channelData( "R", imath.V2i( 0 ) )
		)

		colorSpace2 = GafferImage.ColorSpace()
		colorSpace2["in"].setInput( checker["out"] )
		self.assertEqual( colorSpace2["inputSpace"].getValue(), "" )
		colorSpace2["outputSpace"].setValue( "color_picking" )

		self.assertImagesEqual( colorSpace2["out"], colorSpace1["out"] )

	def testChangingWorkingSpace( self ) :

		checker = GafferImage.Checkerboard()

		colorSpace = GafferImage.ColorSpace()
		colorSpace["in"].setInput( checker["out"] )
		colorSpace["outputSpace"].setValue( "color_picking" )

		with Gaffer.Context() as context :

			GafferImage.OpenColorIOAlgo.setWorkingSpace( context, "scene_linear" )
			tile = colorSpace["out"].channelData( "R", imath.V2i( 0 ) )

			GafferImage.OpenColorIOAlgo.setWorkingSpace( context, "color_picking" )
			self.assertNotEqual( colorSpace["out"].channelData( "R", imath.V2i( 0 ) ), tile )

if __name__ == "__main__":
	unittest.main()
