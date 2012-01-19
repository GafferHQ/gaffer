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

class ContextTest( unittest.TestCase ) :

	def testFrameAccess( self ) :
	
		c = Gaffer.Context()
		
		self.assertEqual( c.getFrame(), 1.0 )
		self.assertEqual( c["frame"], 1.0 )
		
		c.setFrame( 10.5 )
		self.assertEqual( c.getFrame(), 10.5 )
		self.assertEqual( c["frame"], 10.5 )
		
	def testChangedSignal( self ) :
	
		c = Gaffer.Context()
		
		changes = []
		def f( context, name ) :
		
			self.failUnless( context.isSame( c ) )
			changes.append( ( name, context[name] ) )
		
		cn = c.changedSignal().connect( f )
		
		c["a"] = 2
		self.assertEqual( changes, [ ( "a", 2 ) ] )
		
		c["a"] = 3
		self.assertEqual( changes, [ ( "a", 2 ), ( "a", 3 ) ] )
		
		c["b"] = 1
		self.assertEqual( changes, [ ( "a", 2 ), ( "a", 3 ), ( "b", 1 ) ] )

		# when an assignment makes no actual change, the signal should not
		# be triggered again.
		c["b"] = 1
		self.assertEqual( changes, [ ( "a", 2 ), ( "a", 3 ), ( "b", 1 ) ] )

	def testTypes( self ) :
	
		c = Gaffer.Context()
		
		c["int"] = 1
		self.assertEqual( c["int"], 1 )
		self.assertEqual( c.get( "int" ), 1 )
		c.set( "int", 2 )
		self.assertEqual( c["int"], 2 )
		self.failUnless( isinstance( c["int"], int ) )

		c["float"] = 1.0
		self.assertEqual( c["float"], 1.0 )
		self.assertEqual( c.get( "float" ), 1.0 )
		c.set( "float", 2.0 )
		self.assertEqual( c["float"], 2.0 )
		self.failUnless( isinstance( c["float"], float ) )

		c["string"] = "hi"
		self.assertEqual( c["string"], "hi" )
		self.assertEqual( c.get( "string" ), "hi" )
		c.set( "string", "bye" )
		self.assertEqual( c["string"], "bye" )
		self.failUnless( isinstance( c["string"], basestring ) )

	def testCopying( self ) :
	
		c = Gaffer.Context()
		c["i"] = 10
		
		c2 = Gaffer.Context( c )
		self.assertEqual( c2["i"], 10 )
		
		c["i"] = 1
		self.assertEqual( c["i"], 1 )
		self.assertEqual( c2["i"], 10 )
		
if __name__ == "__main__":
	unittest.main()
	
