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
import imath

import IECore

import Gaffer
import GafferTest
import GafferImage
import GafferImageTest

class CDLTest( GafferImageTest.ImageTestCase ) :

	imageFile = pathlib.Path( os.environ["GAFFER_ROOT"] ) / "python" / "GafferImageTest" / "images" / "checker.exr"

	def test( self ) :

		n = GafferImage.ImageReader()
		n["fileName"].setValue( self.imageFile )
		orig = GafferImage.ImageAlgo.image( n["out"] )

		o = GafferImage.CDL()
		o["in"].setInput( n["out"] )

		self.assertEqual( GafferImage.ImageAlgo.image( n["out"] ), GafferImage.ImageAlgo.image( o["out"] ) )

		o['slope'].setValue( imath.Color3f( 1, 2, 3 ) )

		slope = GafferImage.ImageAlgo.image( o["out"] )
		self.assertNotEqual( orig, slope )

		o["offset"].setValue( imath.Color3f( 1, 2, 3 ) )
		offset = GafferImage.ImageAlgo.image( o["out"] )
		self.assertNotEqual( orig, offset )
		self.assertNotEqual( slope, offset )

		o["power"].setValue( imath.Color3f( 1, 2, 3 ) )
		power = GafferImage.ImageAlgo.image( o["out"] )
		self.assertNotEqual( orig, power )
		self.assertNotEqual( slope, power )
		self.assertNotEqual( offset, power )

		o["saturation"].setValue( 0.5 )
		saturation = GafferImage.ImageAlgo.image( o["out"] )
		self.assertNotEqual( orig, saturation )
		self.assertNotEqual( slope, saturation )
		self.assertNotEqual( offset, saturation )
		self.assertNotEqual( power, saturation )

		o["direction"].setValue( GafferImage.OpenColorIOTransform.Direction.Inverse ) # inverse
		inverse = GafferImage.ImageAlgo.image( o["out"] )
		self.assertNotEqual( orig, inverse )
		self.assertNotEqual( slope, inverse )
		self.assertNotEqual( offset, inverse )
		self.assertNotEqual( power, inverse )
		self.assertNotEqual( saturation, inverse )

	def testHashPassThrough( self ) :

		n = GafferImage.ImageReader()
		n["fileName"].setValue( self.imageFile )

		o = GafferImage.CDL()
		o["in"].setInput( n["out"] )

		self.assertEqual( GafferImage.ImageAlgo.image( n["out"] ), GafferImage.ImageAlgo.image( o["out"] ) )

		o['slope'].setValue( imath.Color3f( 1, 2, 3 ) )

		self.assertNotEqual( GafferImage.ImageAlgo.image( n["out"] ), GafferImage.ImageAlgo.image( o["out"] ) )

		o["enabled"].setValue( False )

		self.assertEqual( GafferImage.ImageAlgo.image( n["out"] ), GafferImage.ImageAlgo.image( o["out"] ) )
		self.assertEqual( n["out"]['format'].hash(), o["out"]['format'].hash() )
		self.assertEqual( n["out"]['dataWindow'].hash(), o["out"]['dataWindow'].hash() )
		self.assertEqual( n["out"]["metadata"].getValue(), o["out"]["metadata"].getValue() )
		self.assertEqual( n["out"]['channelNames'].hash(), o["out"]['channelNames'].hash() )

		o["enabled"].setValue( True )
		o['slope'].setValue( o['slope'].defaultValue() )
		self.assertEqual( GafferImage.ImageAlgo.image( n["out"] ), GafferImage.ImageAlgo.image( o["out"] ) )
		self.assertEqual( n["out"]['format'].hash(), o["out"]['format'].hash() )
		self.assertEqual( n["out"]['dataWindow'].hash(), o["out"]['dataWindow'].hash() )
		self.assertEqual( n["out"]["metadata"].getValue(), o["out"]["metadata"].getValue() )
		self.assertEqual( n["out"]['channelNames'].hash(), o["out"]['channelNames'].hash() )

	def testImageHashPassThrough( self ) :

		i = GafferImage.ImageReader()
		i["fileName"].setValue( self.imageFile )

		o = GafferImage.CDL()
		o["in"].setInput( i["out"] )

		self.assertEqual( GafferImage.ImageAlgo.imageHash( i["out"] ), GafferImage.ImageAlgo.imageHash( o["out"] ) )

		o['slope'].setValue( imath.Color3f( 1, 2, 3 ) )

		self.assertNotEqual( GafferImage.ImageAlgo.imageHash( i["out"] ), GafferImage.ImageAlgo.imageHash( o["out"] ) )

	def testChannelsAreSeparate( self ) :

		i = GafferImage.ImageReader()
		i["fileName"].setValue( pathlib.Path( os.environ["GAFFER_ROOT"] ) / "python" / "GafferImageTest" / "images" / "circles.exr" )

		o = GafferImage.CDL()
		o["in"].setInput( i["out"] )
		o['slope'].setValue( imath.Color3f( 1, 2, 3 ) )

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

		o = GafferImage.CDL()
		o["in"].setInput( i["out"] )
		o['slope'].setValue( imath.Color3f( 1, 2, 3 ) )

		self.assertEqual( i["out"]["format"].hash(), o["out"]["format"].hash() )
		self.assertEqual( i["out"]["dataWindow"].hash(), o["out"]["dataWindow"].hash() )
		self.assertEqual( i["out"]["metadata"].getValue(), o["out"]["metadata"].getValue() )
		self.assertEqual( i["out"]["channelNames"].hash(), o["out"]["channelNames"].hash() )

		self.assertEqual( i["out"]["format"].getValue(), o["out"]["format"].getValue() )
		self.assertEqual( i["out"]["dataWindow"].getValue(), o["out"]["dataWindow"].getValue() )
		self.assertEqual( i["out"]["metadata"].getValue(), o["out"]["metadata"].getValue() )
		self.assertEqual( i["out"]["channelNames"].getValue(), o["out"]["channelNames"].getValue() )

	def testMultipleLayers( self ) :

		main = GafferImage.Constant()
		main["color"].setValue( imath.Color4f( 1, 0.5, 0.25, 1 ) )

		diffuse = GafferImage.Constant()
		diffuse["color"].setValue( imath.Color4f( 0.25, 0.5, 0.75, 1 ) )
		diffuse["layer"].setValue( "diffuse" )

		m = GafferImage.CopyChannels()
		m["in"][0].setInput( main["out"] )
		m["in"][1].setInput( diffuse["out"] )
		m["channels"].setValue( "*" )

		cdl = GafferImage.CDL()
		cdl["in"].setInput( m["out"] )

		self.assertImagesEqual( cdl["out"], m["out"] )

		mainCDLSampler = GafferImage.ImageSampler()
		mainCDLSampler["image"].setInput( cdl["out"] )
		mainCDLSampler["pixel"].setValue( imath.V2f( 0.5 ) )
		mainCDLSampler["channels"].setValue( IECore.StringVectorData( [ "R", "G", "B", "A" ] ) )

		diffuseCDLSampler = GafferImage.ImageSampler()
		diffuseCDLSampler["image"].setInput( cdl["out"] )
		diffuseCDLSampler["pixel"].setValue( imath.V2f( 0.5 ) )
		diffuseCDLSampler["channels"].setValue( IECore.StringVectorData( [ "diffuse." + x for x in "RGBA" ] ) )

		self.assertEqual( mainCDLSampler["color"].getValue(), main["color"].getValue() )
		self.assertEqual( diffuseCDLSampler["color"].getValue(), diffuse["color"].getValue() )

		cdl["saturation"].setValue( 0.5 )

		self.assertNotEqual( mainCDLSampler["color"].getValue(), main["color"].getValue() )
		self.assertEqual( diffuseCDLSampler["color"].getValue(), diffuse["color"].getValue() )

		cdl["channels"].setValue( "*[RGB]" )

		self.assertNotEqual( mainCDLSampler["color"].getValue(), main["color"].getValue() )
		self.assertNotEqual( diffuseCDLSampler["color"].getValue(), diffuse["color"].getValue() )
		self.assertNotEqual( mainCDLSampler["color"].hash(), diffuseCDLSampler["color"].hash() )
		self.assertNotEqual( mainCDLSampler["color"].getValue(), diffuseCDLSampler["color"].getValue() )

		cdl["channels"].setValue( "diffuse.[RGB]" )

		self.assertEqual( mainCDLSampler["color"].getValue(), main["color"].getValue() )
		self.assertNotEqual( diffuseCDLSampler["color"].getValue(), diffuse["color"].getValue() )

if __name__ == "__main__":
	unittest.main()
