##########################################################################
#  
#  Copyright (c) 2012, John Haddon. All rights reserved.
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

class ExpressionNodeTest( unittest.TestCase ) :

	def test( self ) :
	
		s = Gaffer.ScriptNode()
		
		s["m1"] = GafferTest.MultiplyNode()
		s["m1"]["op1"].setValue( 10 )
		s["m1"]["op2"].setValue( 20 )
		
		s["m2"] = GafferTest.MultiplyNode()
		s["m2"]["op2"].setValue( 1 )
		
		s["e"] = Gaffer.ExpressionNode()
		s["e"]["engine"].setValue( "python" )
		
		s["e"]["expression"].setValue( "parent[\"m2\"][\"op1\"] = parent[\"m1\"][\"product\"] * 2" )
	
		self.assertEqual( s["m2"]["product"].getValue(), 400 )
	
	def testContextAccess( self ) :
	
		s = Gaffer.ScriptNode()

		s["m"] = GafferTest.MultiplyNode()
		s["m"]["op1"].setValue( 1 )

		s["e"] = Gaffer.ExpressionNode()
		s["e"]["engine"].setValue( "python" )
		s["e"]["expression"].setValue( "parent[\"m\"][\"op2\"] = int( context[\"frame\"] * 2 )" )

		context = Gaffer.Context()
		context.setFrame( 10 )
		with context :
			self.assertEqual( s["m"]["product"].getValue(), 20 )
	
	def testSetExpressionWithNoEngine( self ) :
	
		s = Gaffer.ScriptNode()

		s["m"] = GafferTest.MultiplyNode()

		s["e"] = Gaffer.ExpressionNode()
		s["e"]["engine"].setValue( "" )		
		s["e"]["expression"].setValue( "parent[\"m\"][\"op2\"] = int( context[\"frame\"] * 2 )" )
	
	def testSerialisation( self ) :
	
		s = Gaffer.ScriptNode()
		
		s["m1"] = GafferTest.MultiplyNode()
		s["m1"]["op1"].setValue( 10 )
		s["m1"]["op2"].setValue( 20 )
		
		s["m2"] = GafferTest.MultiplyNode()
		s["m2"]["op2"].setValue( 1 )
		
		s["e"] = Gaffer.ExpressionNode()
		s["e"]["engine"].setValue( "python" )
		
		s["e"]["expression"].setValue( "parent[\"m2\"][\"op1\"] = parent[\"m1\"][\"product\"] * 2" )
	
		self.assertEqual( s["m2"]["product"].getValue(), 400 )
		
		ss = s.serialise()
		
		s2 = Gaffer.ScriptNode()
		s2.execute( ss )
		
		self.assertEqual( s2["m2"]["product"].getValue(), 400 )
	
	def testStringOutput( self ) :
	
		s = Gaffer.ScriptNode()
		
		s["n"] = Gaffer.Node()
		s["n"]["p"] = Gaffer.StringPlug()
		
		s["e"] = Gaffer.ExpressionNode()
		s["e"]["engine"].setValue( "python" )
		s["e"]["expression"].setValue( "parent['n']['p'] = '#%d' % int( context['frame'] )" )
	
		context = Gaffer.Context()
		for i in range( 0, 10 ) :
			context.setFrame( i )
			with context :
				self.assertEqual( s["n"]["p"].getValue(), "#%d" % i )
			
if __name__ == "__main__":
	unittest.main()
