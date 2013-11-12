##########################################################################
#  
#  Copyright (c) 2012, John Haddon. All rights reserved.
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

class ConstantTest( unittest.TestCase ) :
	
	def testDefaultFormatHash( self ) :
		s = Gaffer.ScriptNode()
		n = GafferImage.Constant()
		s.addChild( n )
		
		with s.context():
			h = n["out"].image().hash()
			n["color"][0].setValue( .5 )
			n["color"][1].setValue( .1 )
			n["color"][2].setValue( .8 )
			h2 = n["out"].image().hash()
			self.assertNotEqual( h, h2 )
		
	def testColourHash( self ) :
		# Check that the hash changes when the colour does.
		s = Gaffer.ScriptNode()
		n = GafferImage.Constant()
		s.addChild( n )
		
		with s.context():
			h = n["out"].image().hash()
			n["color"][0].setValue( .5 )
			n["color"][1].setValue( .1 )
			n["color"][2].setValue( .8 )
			h2 = n["out"].image().hash()
			self.assertNotEqual( h, h2 )
		
	def testFormatHash( self ) :
		# Check that the data hash doesn't change when the format does.
		c = GafferImage.Constant()
		c["format"].setValue( GafferImage.Format( 2048, 1156, 1. ) )
		h1 = c["out"].channelData( "R", IECore.V2i( 0 ) ).hash()
		c["format"].setValue( GafferImage.Format( 1920, 1080, 1. ) )
		h2 = c["out"].channelData( "R", IECore.V2i( 0 ) ).hash()
		self.assertEqual( h1, h2 )
		
	def testTileHashes( self ) :
		# Test that two tiles within the image have the same hash.
		c = GafferImage.Constant()
		c["format"].setValue( GafferImage.Format( 2048, 1156, 1. ) )
		c["color"][0].setValue( .5 )
		
		self.assertEqual(
			c["out"].channelDataHash( "R", IECore.V2i( 0 ) ),
			c["out"].channelDataHash( "R", IECore.V2i( GafferImage.ImagePlug().tileSize() ) ),
		)
	
	def testEnableBehaviour( self ) :
		
		c = GafferImage.Constant()
		self.assertTrue( c.enabledPlug().isSame( c["enabled"] ) )
		self.assertEqual( c.correspondingInput( c["out"] ), None )
		self.assertEqual( c.correspondingInput( c["color"] ), None )
		self.assertEqual( c.correspondingInput( c["format"] ), None )
	
	def testChannelNamesHash( self ) :
	
		c = GafferImage.Constant()
		h1 = c["out"]["channelNames"].hash()
		c["color"].setValue( IECore.Color4f( 1, 0.5, 0.25, 1 ) )
		h2 = c["out"]["channelNames"].hash()
	
		self.assertEqual( h1, h2 )
if __name__ == "__main__":
	unittest.main()
