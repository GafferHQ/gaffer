##########################################################################
#  
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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

class TypedPlugTest( unittest.TestCase ) :

	def testConstructor( self ) :
	
		s = Gaffer.StringPlug()
		self.assertEqual( s.defaultValue(), "" )
		self.assertEqual( s.getName(), "StringPlug" )
		
		s = Gaffer.StringPlug( direction=Gaffer.Plug.Direction.Out, defaultValue = "a" )
			
		self.assertEqual( s.direction(), Gaffer.Plug.Direction.Out )
		self.assertEqual( s.defaultValue(), "a" )
		
		s = Gaffer.StringPlug( defaultValue="b", name="a" )
		self.assertEqual( s.defaultValue(), "b" )
		self.assertEqual( s.getName(), "a" )
		
	def testDisconnection( self ) :
	
		p1 = Gaffer.StringPlug( direction=Gaffer.Plug.Direction.Out )
		p2 = Gaffer.StringPlug( direction=Gaffer.Plug.Direction.In )
		
		p2.setInput( p1 )
		self.assert_( p2.getInput().isSame( p1 ) )
		p2.setInput( None )
		self.assert_( p2.getInput() is None )

	def testAcceptsNoneInput( self ) :
	
		p = Gaffer.StringPlug( "hello" )
		self.failUnless( p.acceptsInput( None ) )
		
	def testRunTimeTyped( self ) :
	
		p = Gaffer.BoolPlug( "b" )
		
		self.assertEqual( p.typeName(), "Gaffer::BoolPlug" )
		self.assertEqual( IECore.RunTimeTyped.typeNameFromTypeId( p.typeId() ), "Gaffer::BoolPlug" )
		self.assertEqual( IECore.RunTimeTyped.baseTypeId( p.typeId() ), Gaffer.ValuePlug.staticTypeId() )

	def testSetToDefault( self ) :
	
		s = Gaffer.StringPlug( "s", defaultValue = "apple" )
		self.assertEqual( s.getValue(), "apple" )
		
		s.setValue( "pear" )
		self.assertEqual( s.getValue(), "pear" )
		
		s.setToDefault()
		self.assertEqual( s.getValue(), "apple" )
	
	def testStringDefaultValueHash( self ) :
	
		p1 = Gaffer.StringPlug(
			"p",
			Gaffer.Plug.Direction.In,
			"a"
		)

		p2 = Gaffer.StringPlug(
			"p",
			Gaffer.Plug.Direction.In,
			"b"
		)
		
		p3 = Gaffer.StringPlug(
			"p",
			Gaffer.Plug.Direction.In,
			"b"
		)
		
		self.assertNotEqual( p1.hash(), p2.hash() )		
		self.assertEqual( p2.hash(), p3.hash() )
		
	def testBoolDefaultValueHash( self ) :
	
		p1 = Gaffer.BoolPlug(
			"p",
			Gaffer.Plug.Direction.In,
			True
		)

		p2 = Gaffer.BoolPlug(
			"p",
			Gaffer.Plug.Direction.In,
			False
		)
		
		p3 = Gaffer.BoolPlug(
			"p",
			Gaffer.Plug.Direction.In,
			False
		)
		
		self.assertNotEqual( p1.hash(), p2.hash() )		
		self.assertEqual( p2.hash(), p3.hash() )	
					
	def testReadOnlySetValueRaises( self ) :
	
		p = Gaffer.BoolPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.ReadOnly )
		self.assertRaises( RuntimeError, p.setValue, True )
	
	def testCreateCounterpart( self ) :
	
		p1 = Gaffer.BoolPlug(
			"p",
			Gaffer.Plug.Direction.In,
			True
		)
		
		p2 = p1.createCounterpart( "a", Gaffer.Plug.Direction.Out )
		
		self.assertEqual( p2.getName(), "a" )
		self.assertEqual( p2.direction(), Gaffer.Plug.Direction.Out )
		self.assertEqual( p2.defaultValue(), p1.defaultValue() )
		self.assertEqual( p2.getFlags(), p1.getFlags() )
	
	def testRepr( self ) :
	
		p1 = Gaffer.StringPlug(
			"p",
			Gaffer.Plug.Direction.In,
			"defaultValue",
			flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.ReadOnly
		)
		
		p2 = eval( repr( p1 ) )
		
		self.assertEqual( p2.getName(), p1.getName() )
		self.assertEqual( p2.direction(), p1.direction() )
		self.assertEqual( p2.defaultValue(), p1.defaultValue() )
		self.assertEqual( p2.getFlags(), p1.getFlags() )
	
	def testReadOnlySerialisation( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["p"] = Gaffer.StringPlug( defaultValue = "defaultValue", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["p"].setValue( "apple" )
		s["n"]["p"].setFlags( Gaffer.Plug.Flags.ReadOnly, True )
		ss = s.serialise()
				
		s2 = Gaffer.ScriptNode()
		s2.execute( ss )
				
		self.assertEqual( s2["n"]["p"].defaultValue(), "defaultValue" )
		self.assertEqual( s2["n"]["p"].getValue(), "apple" )
		self.assertEqual( s2["n"]["p"].getFlags( Gaffer.Plug.Flags.ReadOnly ), True )
		
if __name__ == "__main__":
	unittest.main()
	
