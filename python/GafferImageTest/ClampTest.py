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

import unittest
import os
import pathlib
import imath

import IECore

import Gaffer
import GafferTest
import GafferImage
import GafferImageTest

class ClampTest( GafferImageTest.ImageTestCase ) :

	def testClamp( self ) :

		i = GafferImage.ImageReader()
		i["fileName"].setValue( self.imagesPath() / "colorbars_half_max.exr" )

		clamp = GafferImage.Clamp()
		clamp["in"].setInput(i["out"])
		clamp["max"].setValue( imath.Color4f( .5, .5, .5, .5 ) )

		self.assertImagesEqual( i["out"], clamp["out"] )

	def testPerChannelHash( self ) :

		i = GafferImage.ImageReader()
		i["fileName"].setValue( self.imagesPath() / "colorbars_half_max.exr" )

		clamp = GafferImage.Clamp()
		clamp["in"].setInput(i["out"])

		clamp["max"].setValue( imath.Color4f( 1., 1., 1., 1. ) )

		redHash = clamp["out"].channelDataHash( "R", imath.V2i( 0 ) )
		greenHash = clamp["out"].channelDataHash( "G", imath.V2i( 0 ) )
		blueHash = clamp["out"].channelDataHash( "B", imath.V2i( 0 ) )

		clamp["max"].setValue( imath.Color4f( .25, 1., 1., 1. ) )

		redHash2 = clamp["out"].channelDataHash( "R", imath.V2i( 0 ) )
		greenHash2 = clamp["out"].channelDataHash( "G", imath.V2i( 0 ) )
		blueHash2 = clamp["out"].channelDataHash( "B", imath.V2i( 0 ) )

		self.assertNotEqual(redHash, redHash2)
		self.assertEqual(greenHash, greenHash2)
		self.assertEqual(blueHash, blueHash2)

	def testDisconnectedDirty( self ) :

		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.imagesPath() / "colorbars_half_max.exr" )
		clamp = GafferImage.Clamp()
		clamp["in"].setInput( r["out"] )

		cs = GafferTest.CapturingSlot( clamp.plugDirtiedSignal() )
		clamp["max"].setValue( imath.Color4f( .25, 1., 1., 1. ) )

		dirtiedPlugs = set( [ x[0].relativeName( x[0].node() ) for x in cs ] )

		expectedPlugs = [
			'out.channelData',
			'out'
		]

		for plug in expectedPlugs :
			self.assertTrue( plug in dirtiedPlugs )

	def testClampWithMaxTo( self ) :

		i = GafferImage.ImageReader()
		i["fileName"].setValue( self.imagesPath() / "colorbars_max_clamp.exr" )

		clamp = GafferImage.Clamp()
		clamp["in"].setInput(i["out"])
		clamp["min"].setValue( imath.Color4f( .0, .0, .0, .0 ) )
		clamp["max"].setValue( imath.Color4f( .0, .25, .25, .25 ) )
		clamp["minClampTo"].setValue( imath.Color4f( .0, .0, .0, .0 ) )
		clamp["maxClampTo"].setValue( imath.Color4f( 1., .5, .25, 1. ) )
		clamp["minEnabled"].setValue( True )
		clamp["maxEnabled"].setValue( True )
		clamp["minClampToEnabled"].setValue( False )
		clamp["maxClampToEnabled"].setValue( True )

		self.assertImagesEqual( i["out"], clamp["out"] )

	def testDefaultState( self ) :

		clamp = GafferImage.Clamp()

		self.assertTrue( clamp['minEnabled'].getValue() )
		self.assertTrue( clamp['maxEnabled'].getValue() )
		self.assertFalse( clamp['minClampToEnabled'].getValue() )
		self.assertFalse( clamp['maxClampToEnabled'].getValue() )

	def testEnabledBypass( self ) :

		i = GafferImage.ImageReader()
		i["fileName"].setValue( self.imagesPath() / "colorbars_half_max.exr" )

		clamp = GafferImage.Clamp()
		clamp["in"].setInput(i["out"])
		clamp["minEnabled"].setValue( False )
		clamp["maxEnabled"].setValue( False )

		self.assertEqual( GafferImage.ImageAlgo.imageHash( i["out"] ), GafferImage.ImageAlgo.imageHash( clamp["out"] ) )
		self.assertEqual( i["out"]["format"].hash(), clamp["out"]["format"].hash() )
		self.assertEqual( i["out"]["dataWindow"].hash(), clamp["out"]["dataWindow"].hash() )
		self.assertEqual( i["out"]["channelNames"].hash(), clamp["out"]["channelNames"].hash() )

	def testEnableBehaviour( self ) :

		clamp = GafferImage.Clamp()

		self.assertTrue( clamp.enabledPlug().isSame( clamp["enabled"] ) )
		self.assertTrue( clamp.correspondingInput( clamp["out"] ).isSame( clamp["in"] ) )
		self.assertEqual( clamp.correspondingInput( clamp["in"] ), None )
		self.assertEqual( clamp.correspondingInput( clamp["enabled"] ), None )
		self.assertEqual( clamp.correspondingInput( clamp["min"] ), None )

	def testPassThrough( self ) :

		i = GafferImage.ImageReader()
		i["fileName"].setValue( self.imagesPath() / "colorbars_half_max.exr" )

		c = GafferImage.Clamp()
		c["in"].setInput( i["out"] )
		c["max"].setValue( imath.Color4f( .5, .5, .5, .5 ) )

		self.assertEqual( i["out"]["format"].hash(), c["out"]["format"].hash() )
		self.assertEqual( i["out"]["dataWindow"].hash(), c["out"]["dataWindow"].hash() )
		self.assertEqual( i["out"]["metadata"].hash(), c["out"]["metadata"].hash() )
		self.assertEqual( i["out"]["channelNames"].hash(), c["out"]["channelNames"].hash() )

		self.assertEqual( i["out"]["format"].getValue(), c["out"]["format"].getValue() )
		self.assertEqual( i["out"]["dataWindow"].getValue(), c["out"]["dataWindow"].getValue() )
		self.assertEqual( i["out"]["metadata"].getValue(), c["out"]["metadata"].getValue() )
		self.assertEqual( i["out"]["channelNames"].getValue(), c["out"]["channelNames"].getValue() )

if __name__ == "__main__":
	unittest.main()
