##########################################################################
#  
#  Copyright (c) 2011, John Haddon. All rights reserved.
#  Copyright (c) 2011, Image Engine Design Inc. All rights reserved.
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

class TypedObjectPlugTest( unittest.TestCase ) :

	def testSerialisation( self ) :
	
		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["t"] = Gaffer.ObjectPlug( "hello", flags = Gaffer.Plug.Flags.Dynamic )
		
		se = s.serialise()
		
		s2 = Gaffer.ScriptNode()
		s2.execute( se )
		
		self.failUnless( s2["n"]["t"].isInstanceOf( Gaffer.ObjectPlug.staticTypeId() ) )		

	def testSerialisationWithConnection( self ) :
	
		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["t"] = Gaffer.ObjectPlug( "hello", flags = Gaffer.Plug.Flags.Dynamic )
		
		s["n2"] = Gaffer.Node()
		s["n2"]["t2"] = Gaffer.ObjectPlug( "hello", flags = Gaffer.Plug.Flags.Dynamic, direction=Gaffer.Plug.Direction.Out )
		
		s["n"]["t"].setInput( s["n2"]["t2"] )
		
		se = s.serialise()
				
		s2 = Gaffer.ScriptNode()
		s2.execute( se )
		
		self.failUnless( s2["n"]["t"].getInput().isSame( s2["n2"]["t2"] ) )
		
	def testDefaultValue( self ) :
	
		p = Gaffer.ObjectPlug( "p", defaultValue = IECore.IntVectorData( [ 1, 2, 3 ] ) )
		self.assertEqual( p.defaultValue(), IECore.IntVectorData( [ 1, 2, 3 ] ) )
	
	def testRunTimeTyped( self ) :
	
		self.assertEqual( IECore.RunTimeTyped.baseTypeId( Gaffer.ObjectPlug.staticTypeId() ), Gaffer.ValuePlug.staticTypeId() )
	
	def testAcceptsNoneInput( self ) :
	
		p = Gaffer.ObjectPlug( "hello" )
		self.failUnless( p.acceptsInput( None ) )
				
if __name__ == "__main__":
	unittest.main()
	
