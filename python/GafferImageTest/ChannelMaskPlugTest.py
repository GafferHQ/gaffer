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

import os
import unittest
import IECore
import Gaffer
import GafferImage
import sys

class ChannelMaskPlugTest( unittest.TestCase ) :
	
	def testChannelMask( self ) :
		n = Gaffer.Node()

		maskChannels = IECore.StringVectorData( [ "R", "B" ] )
		p = GafferImage.ChannelMaskPlug("p", defaultValue = maskChannels, direction = Gaffer.Plug.Direction.In, flags = Gaffer.Plug.Flags.Default )
		n.addChild( p )
		s = Gaffer.ScriptNode()
		s.addChild( n )
		
		testChannels = [ "R", "G", "B", "A" ]
		maskedChannels = p.maskChannels( testChannels )

		# Test that the channels that were masked remain and that those which weren't are removed.
		# Also assert that the order of the new list is correct.
		self.assertTrue( "R" in maskedChannels ) 
		self.assertFalse( "G" in maskedChannels ) 
		self.assertTrue( "B" in maskedChannels ) 
		self.assertFalse( "A" in maskedChannels ) 
		self.assertTrue( maskedChannels[1] == "B" )
		self.assertTrue( maskedChannels[0] == "R" )

if __name__ == "__main__":
	unittest.main()
