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
import subprocess32 as subprocess

import IECore

import Gaffer
import GafferTest
import GafferImage
import GafferImageTest

class ColorSpaceTest( GafferImageTest.ImageTestCase ) :

	fileName = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/checker.exr" )

	def test( self ) :

		n = GafferImage.ImageReader()
		n["fileName"].setValue( self.fileName )

		o = GafferImage.ColorSpace()
		o["in"].setInput( n["out"] )

		self.assertEqual( n["out"].image(), o["out"].image() )

		o["inputSpace"].setValue( "linear" )
		o["outputSpace"].setValue( "sRGB" )

		self.assertNotEqual( n["out"].image(), o["out"].image() )

	def testHashPassThrough( self ) :

		n = GafferImage.ImageReader()
		n["fileName"].setValue( self.fileName )

		o = GafferImage.ColorSpace()
		o["in"].setInput( n["out"] )

		self.assertEqual( n["out"].image(), o["out"].image() )

		o["inputSpace"].setValue( "linear" )
		o["outputSpace"].setValue( "sRGB" )

		self.assertNotEqual( n["out"].image(), o["out"].image() )

		o["enabled"].setValue( False )

		self.assertEqual( n["out"].image(), o["out"].image() )
		self.assertEqual( n["out"]['format'].hash(), o["out"]['format'].hash() )
		self.assertEqual( n["out"]['dataWindow'].hash(), o["out"]['dataWindow'].hash() )
		self.assertEqual( n["out"]["metadata"].getValue(), o["out"]["metadata"].getValue() )
		self.assertEqual( n["out"]['channelNames'].hash(), o["out"]['channelNames'].hash() )

		o["enabled"].setValue( True )

		o["inputSpace"].setValue( "linear" )
		o["outputSpace"].setValue( "linear" )
		self.assertEqual( n["out"].image(), o["out"].image() )
		self.assertEqual( n["out"]['format'].hash(), o["out"]['format'].hash() )
		self.assertEqual( n["out"]['dataWindow'].hash(), o["out"]['dataWindow'].hash() )
		self.assertEqual( n["out"]["metadata"].getValue(), o["out"]["metadata"].getValue() )
		self.assertEqual( n["out"]['channelNames'].hash(), o["out"]['channelNames'].hash() )

	def testImageHashPassThrough( self ) :

		i = GafferImage.ImageReader()
		i["fileName"].setValue( self.fileName )

		o = GafferImage.ColorSpace()
		o["in"].setInput( i["out"] )

		self.assertEqual( i["out"].imageHash(), o["out"].imageHash() )

		o["inputSpace"].setValue( "linear" )
		o["outputSpace"].setValue( "sRGB" )

		self.assertNotEqual( i["out"].imageHash(), o["out"].imageHash() )

	def testChannelsAreSeparate( self ) :

		i = GafferImage.ImageReader()
		i["fileName"].setValue( os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/circles.exr" ) )

		o = GafferImage.ColorSpace()
		o["in"].setInput( i["out"] )

		o["inputSpace"].setValue( "linear" )
		o["outputSpace"].setValue( "sRGB" )

		self.assertNotEqual(
			o["out"].channelDataHash( "R", IECore.V2i( 0 ) ),
			o["out"].channelDataHash( "G", IECore.V2i( 0 ) )
		)

		self.assertNotEqual(
			o["out"].channelData( "R", IECore.V2i( 0 ) ),
			o["out"].channelData( "G", IECore.V2i( 0 ) )
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
		
		scriptFileName = self.temporaryDirectory() + "/script.gfr"
		contextImageFile = self.temporaryDirectory() + "/context.#.exr"
		contextOverrideImageFile = self.temporaryDirectory() + "/context_override.#.exr"

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
		s["writer"]['channels'].setValue(IECore.StringVectorData(["R", "G", "B", "A"]))
	
		s["fileName"].setValue( scriptFileName )
		s.save()

		ocioEnv = os.environ.get("OCIO")
		os.environ["OCIO"] = os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/openColorIO/context.ocio" )
		os.environ["LUT"] = "srgb.spi1d"
		os.environ["CDL"] = "cineon.spi1d"

		p = subprocess.Popen(
			" ".join(["gaffer", "execute", scriptFileName,"-frames", "1-1"]),
			shell = True,
			stderr = subprocess.PIPE,
		)

		p.wait()

		i = GafferImage.ImageReader()
		i["fileName"].setValue( os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/checker_ocio_context.exr" ) )

		o = GafferImage.ImageReader()
		o["fileName"].setValue( contextImageFile )

		expected = i["out"].image()
		context = o["out"].image()

		# check against expected output
		op = IECore.ImageDiffOp()
		res = op(
			imageA = expected,
			imageB = context
		)

		self.assertFalse( res.value )
		
		# override context
		s["writer"]["fileName"].setValue( contextOverrideImageFile )
		s["cs"]["context"].addOptionalMember("LUT", "cineon.spi1d", "LUT", enabled=True)
		s["cs"]["context"].addOptionalMember("CDL", "rec709.spi1d", "CDL", enabled=True)
		s.save()

		p = subprocess.Popen(
			" ".join(["gaffer", "execute", scriptFileName,"-frames", "1-1"]),
			shell = True,
			stderr = subprocess.PIPE,
		)

		p.wait()

		i = GafferImage.ImageReader()
		i["fileName"].setValue( os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/checker_ocio_context_override.exr" ) )

		o = GafferImage.ImageReader()
		o["fileName"].setValue( contextOverrideImageFile )

		expected = i["out"].image()
		context = o["out"].image()

		# check override produce expected output
		op = IECore.ImageDiffOp()
		res = op(
			imageA = expected,
			imageB = context
		)

		self.assertFalse( res.value )

		os.environ["OCIO"] = ocioEnv
		del os.environ["LUT"]
		del os.environ["CDL"]


if __name__ == "__main__":
	unittest.main()
