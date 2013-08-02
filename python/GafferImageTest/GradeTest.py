##########################################################################
#  
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

import unittest

import IECore
import Gaffer
import GafferImage
import os

class GradeTest( unittest.TestCase ) :

	checkerFile = os.path.expandvars( "$GAFFER_ROOT/python/GafferTest/images/checker.exr" )
	
	# Test that when gamma == 0 that the coresponding channel isn't modified.
	def testChannelEnable( self ) :
		i = GafferImage.ImageReader()
		i["fileName"].setValue( self.checkerFile )
		
		# Create a grade node and save the hash of a tile from each channel.
		grade = GafferImage.Grade()
		grade["in"].setInput(i["out"])
		grade["gain"].setValue( IECore.Color3f( 2., 2., 2. ) )	
		hashRed = grade["out"].channelData( "R", IECore.V2i( 0 ) ).hash()
		hashGreen = grade["out"].channelData( "G", IECore.V2i( 0 ) ).hash()
		hashBlue = grade["out"].channelData( "B", IECore.V2i( 0 ) ).hash()
		
		# Now we set the gamma on the green channel to 0 which should disable it's output.
		# The red and blue channels should still be graded as before.
		grade["gamma"].setValue( IECore.Color3f( 1., 0., 1. ) )
		hashRed2 = grade["out"].channelData( "R", IECore.V2i( 0 ) ).hash()
		hashGreen2 = grade["out"].channelData( "G", IECore.V2i( 0 ) ).hash()
		hashBlue2 = grade["out"].channelData( "B", IECore.V2i( 0 ) ).hash()
		
		self.assertEqual( hashRed, hashRed2 )
		self.assertNotEqual( hashGreen, hashGreen2 )
		self.assertEqual( hashBlue, hashBlue2 )

	def testChannelDataHashes( self ) :
		# Create a grade node and save the hash of a tile from each channel.
		i = GafferImage.ImageReader()
		i["fileName"].setValue( self.checkerFile )
		
		grade = GafferImage.Grade()
		grade["in"].setInput(i["out"])
		grade["gain"].setValue( IECore.Color3f( 2., 2., 2. ) )
		
		h1 = grade["out"].channelData( "R", IECore.V2i( 0 ) ).hash()
		h2 = grade["out"].channelData( "R", IECore.V2i( GafferImage.ImagePlug().tileSize() ) ).hash()
		self.assertNotEqual( h1, h2 )
		
		# Test that two tiles within the same image have the same hash when disabled.
		grade["enabled"].setValue(False)
		h1 = grade["out"].channelData( "R", IECore.V2i( 0 ) ).hash()
		h2 = grade["out"].channelData( "R", IECore.V2i( GafferImage.ImagePlug().tileSize() ) ).hash()
		self.assertNotEqual( h1, h2 )
		
	def testEnableBehaviour( self ) :
		
		g = GafferImage.Grade()
		self.assertTrue( g.enabledPlug().isSame( g["enabled"] ) )
		self.assertTrue( g.correspondingInput( g["out"] ).isSame( g["in"] ) )
		self.assertEqual( g.correspondingInput( g["in"] ), None )
		self.assertEqual( g.correspondingInput( g["enabled"] ), None )
		self.assertEqual( g.correspondingInput( g["gain"] ), None )



