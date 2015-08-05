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

import IECore

import Gaffer
import GafferImage

class PremultiplyTest( unittest.TestCase ) :

	checkerFile = os.path.expandvars( "$GAFFER_ROOT/python/GafferTest/images/rgbOverChecker.100x100.exr" )

	def testChannelDataHashes( self ) :
		# Create a premult node and save the hash of a tile from each channel.
		i = GafferImage.ImageReader()
		i["fileName"].setValue( self.checkerFile )

		premult = GafferImage.Premultiply()
		premult["in"].setInput(i["out"])

		h1 = premult["out"].channelData( "R", IECore.V2i( 0 ) ).hash()
		h2 = premult["out"].channelData( "R", IECore.V2i( GafferImage.ImagePlug().tileSize() ) ).hash()
		self.assertNotEqual( h1, h2 )

		# Test that two tiles within the same image have the same hash when disabled.
		premult["enabled"].setValue(False)
		h1 = premult["out"].channelData( "R", IECore.V2i( 0 ) ).hash()
		h2 = premult["out"].channelData( "R", IECore.V2i( GafferImage.ImagePlug().tileSize() ) ).hash()
		self.assertNotEqual( h1, h2 )

	def testByChannel( self ) :
		# Test that changing the channel to multiply by changes the hash
		i = GafferImage.ImageReader()
		i["fileName"].setValue( self.checkerFile )

		premult = GafferImage.Premultiply()
		premult["in"].setInput(i["out"])

		premult["byChannel"].setValue("R")
		h1 = premult["out"].channelData( "R", IECore.V2i( 0 ) ).hash()

		premult["byChannel"].setValue("B")
		h2 = premult["out"].channelData( "R", IECore.V2i( 0 ) ).hash()
		self.assertNotEqual( h1, h2 )

	def testEnableBehaviour( self ) :

		g = GafferImage.Premultiply()
		self.assertTrue( g.enabledPlug().isSame( g["enabled"] ) )
		self.assertTrue( g.correspondingInput( g["out"] ).isSame( g["in"] ) )
		self.assertEqual( g.correspondingInput( g["in"] ), None )
		self.assertEqual( g.correspondingInput( g["enabled"] ), None )
		self.assertEqual( g.correspondingInput( g["byChannel"] ), None )

	def testPassThrough( self ) :

		i = GafferImage.ImageReader()
		i["fileName"].setValue( self.checkerFile )

		g = GafferImage.Premultiply()
		g["in"].setInput( i["out"] )

		self.assertEqual( i["out"]["format"].hash(), g["out"]["format"].hash() )
		self.assertEqual( i["out"]["dataWindow"].hash(), g["out"]["dataWindow"].hash() )
		self.assertEqual( i["out"]["metadata"].hash(), g["out"]["metadata"].hash() )
		self.assertEqual( i["out"]["channelNames"].hash(), g["out"]["channelNames"].hash() )

		self.assertEqual( i["out"]["format"].getValue(), g["out"]["format"].getValue() )
		self.assertEqual( i["out"]["dataWindow"].getValue(), g["out"]["dataWindow"].getValue() )
		self.assertEqual( i["out"]["metadata"].getValue(), g["out"]["metadata"].getValue() )
		self.assertEqual( i["out"]["channelNames"].getValue(), g["out"]["channelNames"].getValue() )
