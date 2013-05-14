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
#      * Neither the name of Image Engine Design nor the names of
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

class SamplerTest( unittest.TestCase ) :
	
	fileName = os.path.expandvars( "$GAFFER_ROOT/python/GafferTest/images/checker.exr" )

	def testOutOfBoundsSample( self ) : 
		
		s = Gaffer.ScriptNode()
		r = GafferImage.ImageReader()
		r["fileName"].setValue( self.fileName )		
		s.addChild( r )
			
		c = Gaffer.Context()
		c["image:channelName"] = 'R'
		c["image:tileOrigin"] = IECore.V2i( 0 )
		
		bounds = r["out"]["dataWindow"].getValue();
	
		testCases = [
			( bounds.min.x-1, bounds.min.y ),
			( bounds.min.x, bounds.min.y-1 ),
			( bounds.max.x, bounds.max.y+1 ),
			( bounds.max.x+1, bounds.max.y ),
			( bounds.min.x-1, bounds.max.y ),
			( bounds.min.x, bounds.max.y+1 ),
			( bounds.max.x+1, bounds.min.y ),
			( bounds.max.x, bounds.min.y-1 )
		]

		with c :
			
			self.assertTrue( "Box" in GafferImage.FilterPlug.filters() )
			self.assertTrue( "R" in r["out"]["channelNames"].getValue() )
			s = GafferImage.Sampler( r["out"], "R", bounds, "Box" )
		
			# Check that the bounding pixels are non zero.
			self.assertNotEqual( s.sample( bounds.min.x, bounds.min.y ), 0. )
			self.assertNotEqual( s.sample( bounds.max.x, bounds.max.y ), 0. )
			self.assertNotEqual( s.sample( bounds.min.x, bounds.max.y ), 0. )
			self.assertNotEqual( s.sample( bounds.max.x, bounds.min.y ), 0. )
	
			# Sample out of bounds and assert that a zero is returned.	
			for x, y in testCases :
				self.assertEqual( s.sample( x+.5, y+.5 ), 0. )

	def testSampleHash( self ) :
		###\todo: See the todo in the GafferImage.Sampler class and then write this test case.
		pass

