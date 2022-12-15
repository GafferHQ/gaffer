##########################################################################
#
#  Copyright (c) 2013-2015, Image Engine Design Inc. All rights reserved.
#  Copyright (c) 2015, Nvizible Ltd. All rights reserved.
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
import imath

import IECore

import Gaffer
import GafferImage
import GafferImageTest

class UnpremultiplyTest( GafferImageTest.ImageTestCase ) :

	checkerFile = GafferImageTest.ImageTestCase.imagesPath() / "rgbOverChecker.100x100.exr"

	def testAlphaChannel( self ) :
		# Test that changing the channel to use as the alpha channel changes the hash
		i = GafferImage.ImageReader()
		i["fileName"].setValue( self.checkerFile )

		unpremult = GafferImage.Unpremultiply()
		unpremult["in"].setInput(i["out"])

		unpremult["alphaChannel"].setValue("R")
		h1 = unpremult["out"].channelData( "R", imath.V2i( 0 ) ).hash()

		unpremult["alphaChannel"].setValue("B")
		h2 = unpremult["out"].channelData( "R", imath.V2i( 0 ) ).hash()
		self.assertNotEqual( h1, h2 )

	def testEnableBehaviour( self ) :

		g = GafferImage.Unpremultiply()
		self.assertTrue( g.enabledPlug().isSame( g["enabled"] ) )
		self.assertTrue( g.correspondingInput( g["out"] ).isSame( g["in"] ) )
		self.assertEqual( g.correspondingInput( g["in"] ), None )
		self.assertEqual( g.correspondingInput( g["enabled"] ), None )
		self.assertEqual( g.correspondingInput( g["alphaChannel"] ), None )

	def testPassThrough( self ) :

		i = GafferImage.ImageReader()
		i["fileName"].setValue( self.checkerFile )

		g = GafferImage.Unpremultiply()
		g["in"].setInput( i["out"] )

		self.assertEqual( i["out"]["format"].hash(), g["out"]["format"].hash() )
		self.assertEqual( i["out"]["dataWindow"].hash(), g["out"]["dataWindow"].hash() )
		self.assertEqual( i["out"]["metadata"].hash(), g["out"]["metadata"].hash() )
		self.assertEqual( i["out"]["channelNames"].hash(), g["out"]["channelNames"].hash() )

		self.assertEqual( i["out"]["format"].getValue(), g["out"]["format"].getValue() )
		self.assertEqual( i["out"]["dataWindow"].getValue(), g["out"]["dataWindow"].getValue() )
		self.assertEqual( i["out"]["metadata"].getValue(), g["out"]["metadata"].getValue() )
		self.assertEqual( i["out"]["channelNames"].getValue(), g["out"]["channelNames"].getValue() )

	def testDivideValue( self ) :
		# Test the image results when multiplying by each channel in turn

		color = { "R": 1.0, "G": 2.0, "B": 0.0, "A": 0.5 }
		s = Gaffer.ScriptNode()
		s["c"] = GafferImage.Constant()
		s["c"]["color"].setValue( imath.Color4f( color["R"], color["G"], color["B"], color["A"] ) )
		s["u"] = GafferImage.Unpremultiply()
		s["u"]["in"].setInput( s["c"]["out"] )
		s["u"]["channels"].setValue( "R G B A" )

		for alphaChannelName in color.keys() :
			s["u"]["alphaChannel"].setValue(alphaChannelName)

			for channelName in color.keys():
				c = Gaffer.Context( s.context() )
				c["image:channelName"] = channelName
				c["image:tileOrigin"] = imath.V2i( 0 )
				with c :
					result = s["u"]["out"]["channelData"].getValue()[0]

					if channelName == alphaChannelName or color[alphaChannelName] == 0.0:
						self.assertEqual( result, color[channelName] )
					else:
						self.assertEqual( result, color[channelName] / color[alphaChannelName] )
