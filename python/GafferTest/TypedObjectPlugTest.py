##########################################################################
#  
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2011-2012, Image Engine Design Inc. All rights reserved.
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
		s["n"]["t"] = Gaffer.ObjectPlug( "hello", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		
		se = s.serialise()
		
		s2 = Gaffer.ScriptNode()
		s2.execute( se )
		
		self.failUnless( s2["n"]["t"].isInstanceOf( Gaffer.ObjectPlug.staticTypeId() ) )		

	def testSerialisationWithConnection( self ) :
	
		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["t"] = Gaffer.ObjectPlug( "hello", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		
		s["n2"] = Gaffer.Node()
		s["n2"]["t2"] = Gaffer.ObjectPlug( "hello", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, direction=Gaffer.Plug.Direction.Out )
		
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
		
	def testBoolVectorDataPlug( self ) :
	
		p = Gaffer.BoolVectorDataPlug( "p", defaultValue = IECore.BoolVectorData( [ True, False ] ) )
		
		self.assertEqual( p.defaultValue(), IECore.BoolVectorData( [ True, False ] ) )
		self.assertEqual( p.getValue(), IECore.BoolVectorData( [ True, False ] ) )
		
		p.setValue( IECore.BoolVectorData( [ False ] ) )
		self.assertEqual( p.getValue(), IECore.BoolVectorData( [ False ] ) )
				
		self.assertRaises( Exception, p.setValue, IECore.IntData( 10 ) )

	def testNullDefaultValue( self ) :
	
		p = Gaffer.ObjectPlug( "hello", defaultValue = None )
		self.failUnless( p.defaultValue() is None )
		
	def testSerialisationWithValueAndDefaultValue( self ) :
	
		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["t"] = Gaffer.ObjectPlug( "hello", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, defaultValue = IECore.IntData( 10 ) )
		s["n"]["t"].setValue( IECore.CompoundObject( { "a" : IECore.IntData( 20 ) } ) )
		
 		se = s.serialise()
		
 		s2 = Gaffer.ScriptNode()
 		s2.execute( se )
 		 		
 		self.failUnless( s2["n"]["t"].isInstanceOf( Gaffer.ObjectPlug.staticTypeId() ) )		
 		self.failUnless( s2["n"]["t"].defaultValue() == IECore.IntData( 10 ) )
		self.failUnless( s2["n"]["t"].getValue() == IECore.CompoundObject( { "a" : IECore.IntData( 20 ) } ) )
 	
	def testSerialisationWithUnserialisableValue( self ) :
	
		# right now we can only serialise types which define __repr__.
		# this test just asserts that if one does happen to be used then it
		# at least doesn't totally break the parsing. ideally we need to make
		# sure that all types can be serialised (although storing large types
		# in the file itself is frankly a terrible idea).
	
		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["t"] = Gaffer.ObjectPlug( "hello", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, defaultValue = IECore.MeshPrimitive.createPlane( IECore.Box2f( IECore.V2f( 0 ), IECore.V2f( 10 ) ) ) )
		s["n"]["t"].setValue( IECore.MeshPrimitive.createPlane( IECore.Box2f( IECore.V2f( 0 ), IECore.V2f( 1 ) ) ) )
		
		mh = IECore.CapturingMessageHandler()
		with mh :
 			se = s.serialise()
		
		self.assertEqual( len( mh.messages ), 2 )
		
		s2 = Gaffer.ScriptNode()
 		s2.execute( se )
	
	def testConstructCantSpecifyBothInputAndValue( self ) :
	
		out = Gaffer.ObjectPlug( "out", direction=Gaffer.Plug.Direction.Out )
		
		self.assertRaises( Exception, Gaffer.ObjectPlug, "in", input=out, value=IECore.IntData( 10 ) )
	
	class TypedObjectPlugNode( Gaffer.Node ) :
		
		def __init__( self, name="TypedObjectPlugNode", inputs={}, dynamicPlugs=() ) :
		
			Gaffer.Node.__init__( self, name )
			
			self.addChild(
				Gaffer.ObjectPlug( "p" ),
			)
			
			self._init( inputs, dynamicPlugs )
	
	IECore.registerRunTimeTyped( TypedObjectPlugNode )
	
	def testSerialisationOfStaticPlugs( self ) :
	
		s = Gaffer.ScriptNode()
		s["n"] = self.TypedObjectPlugNode()
		s["n"]["p"].setValue( IECore.IntData( 10 ) )

 		se = s.serialise()
				
		s2 = Gaffer.ScriptNode()
 		s2.execute( se )
 		
 		self.assertEqual( s2["n"]["p"].getValue(), IECore.IntData( 10 ) )
	
	def testSetToDefault( self ) :
	
		plane = IECore.MeshPrimitive.createPlane( IECore.Box2f( IECore.V2f( 0 ), IECore.V2f( 10 ) ) )
		plug = Gaffer.ObjectPlug( defaultValue = plane )
		self.assertEqual( plug.getValue(), plane )
		
		plug.setValue( IECore.SpherePrimitive() )
		self.assertEqual( plug.getValue(), IECore.SpherePrimitive() )
		
		plug.setToDefault()
		self.assertEqual( plug.getValue(), plane )
		
if __name__ == "__main__":
	unittest.main()
	
