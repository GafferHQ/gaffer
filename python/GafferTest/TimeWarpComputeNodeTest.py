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

import unittest

import Gaffer
import GafferTest

class TimeWarpComputeNodeTest( unittest.TestCase ) :

	def test( self ) :
	
		s = Gaffer.ScriptNode()
		
		s["m"] = GafferTest.MultiplyNode()
		s["m"]["op2"].setValue( 1 )
		
		s["e"] = Gaffer.Expression()
		s["e"]["engine"].setValue( "python" )
		s["e"]["expression"].setValue( "parent[\"m\"][\"op1\"] = int( context[\"frame\"] )" ) 
		
		s["w"] = Gaffer.TimeWarpComputeNode()
		s["w"]["in"] = Gaffer.IntPlug()
		s["w"]["in"].setInput( s["m"]["product"] )
		s["w"]["out"] = Gaffer.IntPlug( direction = Gaffer.Plug.Direction.Out )
		s["w"]["offset"].setValue( 2 )
		s["w"]["speed"].setValue( 2 )
		
		for i in range( 0, 10 ) :
			c = Gaffer.Context()
			c.setFrame( i )
			with c :
				self.assertEqual( s["m"]["product"].getValue(), i )
				self.assertEqual( s["w"]["out"].getValue(), i * 2 + 2 )
	
	def testHash( self ) :
	
		# we want the output of the time warp to have the same hash
		# as the input at the appropriate point in time. that way we get
		# to share cache entries between the nodes and use less memory
		# and do less computation.
		
		s = Gaffer.ScriptNode()
		
		s["m"] = GafferTest.MultiplyNode()
		s["m"]["op2"].setValue( 1 )
		
		s["e"] = Gaffer.Expression()
		s["e"]["engine"].setValue( "python" )
		s["e"]["expression"].setValue( "parent[\"m\"][\"op1\"] = int( context[\"frame\"] )" ) 
					
		s["w"] = Gaffer.TimeWarpComputeNode()
		s["w"]["in"] = Gaffer.IntPlug()
		s["w"]["in"].setInput( s["m"]["product"] )
		s["w"]["out"] = Gaffer.IntPlug( direction = Gaffer.Plug.Direction.Out )
		s["w"]["offset"].setValue( 2 )
		
		for i in range( 0, 10 ) :
			c = Gaffer.Context()
			c.setFrame( i )
			with c :
				self.assertEqual( s["m"]["product"].getValue(), i )
				self.assertEqual( s["w"]["out"].getValue(), i + 2 )
				wh = s["w"]["out"].hash()	
			c.setFrame( i + 2 )
			with c :
				mh = s["m"]["product"].hash()
			self.assertEqual( wh, mh )
				
if __name__ == "__main__":
	unittest.main()
