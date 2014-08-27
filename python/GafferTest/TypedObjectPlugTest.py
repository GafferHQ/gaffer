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
import GafferTest

class TypedObjectPlugTest( GafferTest.TestCase ) :

	def testSerialisation( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["t"] = Gaffer.ObjectPlug( "hello", defaultValue = IECore.IntData( 1 ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		se = s.serialise()

		s2 = Gaffer.ScriptNode()
		s2.execute( se )

		self.failUnless( s2["n"]["t"].isInstanceOf( Gaffer.ObjectPlug.staticTypeId() ) )

	def testSerialisationWithConnection( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["t"] = Gaffer.ObjectPlug( "hello", defaultValue = IECore.IntData( 0 ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["n2"] = Gaffer.Node()
		s["n2"]["t2"] = Gaffer.ObjectPlug( "hello", defaultValue = IECore.IntData( 0 ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, direction=Gaffer.Plug.Direction.Out )

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

		p = Gaffer.ObjectPlug( "hello", Gaffer.Plug.Direction.In, IECore.IntData( 10 ) )
		self.failUnless( p.acceptsInput( None ) )

	def testBoolVectorDataPlug( self ) :

		p = Gaffer.BoolVectorDataPlug( "p", defaultValue = IECore.BoolVectorData( [ True, False ] ) )

		self.assertEqual( p.defaultValue(), IECore.BoolVectorData( [ True, False ] ) )
		self.assertEqual( p.getValue(), IECore.BoolVectorData( [ True, False ] ) )

		p.setValue( IECore.BoolVectorData( [ False ] ) )
		self.assertEqual( p.getValue(), IECore.BoolVectorData( [ False ] ) )

		self.assertRaises( Exception, p.setValue, IECore.IntData( 10 ) )

	def testNullDefaultValue( self ) :

		self.assertRaises( ValueError, Gaffer.ObjectPlug, "hello", defaultValue = None )

	def testNullValue( self ) :

		p = Gaffer.ObjectPlug( "hello", Gaffer.Plug.Direction.In, IECore.IntData( 10 ) )
		self.assertRaises( ValueError, p.setValue, None )

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

 	@GafferTest.expectedFailure
	def testSerialisationOfMeshPrimitives( self ) :

		# right now we can only serialise types which define __repr__, but that
		# isn't defined for all cortex types. this test should pass when we get round
		# to defining it for MeshPrimitives - we should do the other primitives at the
		# same time, obviously.

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["t"] = Gaffer.ObjectPlug( "hello", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, defaultValue = IECore.MeshPrimitive.createPlane( IECore.Box2f( IECore.V2f( 0 ), IECore.V2f( 10 ) ) ) )
		s["n"]["t"].setValue( IECore.MeshPrimitive.createPlane( IECore.Box2f( IECore.V2f( 0 ), IECore.V2f( 1 ) ) ) )

 		se = s.serialise()

		s2 = Gaffer.ScriptNode()
 		s2.execute( se )

		self.assertEqual( s["n"]["t"].defaultValue(), s2["n"]["t"].defaultValue() )
		self.assertEqual( s["n"]["t"].getValue(), s2["n"]["t"].getValue() )

	def testConstructCantSpecifyBothInputAndValue( self ) :

		out = Gaffer.ObjectPlug( "out", direction=Gaffer.Plug.Direction.Out, defaultValue=IECore.StringData( "hi" ) )

		self.assertRaises( Exception, Gaffer.ObjectPlug, "in", input=out, value=IECore.IntData( 10 ) )

	class TypedObjectPlugNode( Gaffer.Node ) :

		def __init__( self, name="TypedObjectPlugNode" ) :

			Gaffer.Node.__init__( self, name )

			self.addChild(
				Gaffer.ObjectPlug( "p", defaultValue = IECore.IntData( 1 ) ),
			)

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

	def testValueType( self ) :

		self.failUnless( Gaffer.ObjectPlug.ValueType is IECore.Object )
		self.failUnless( Gaffer.BoolVectorDataPlug.ValueType is IECore.BoolVectorData )
		self.failUnless( Gaffer.IntVectorDataPlug.ValueType is IECore.IntVectorData )
		self.failUnless( Gaffer.FloatVectorDataPlug.ValueType is IECore.FloatVectorData )
		self.failUnless( Gaffer.StringVectorDataPlug.ValueType is IECore.StringVectorData )
		self.failUnless( Gaffer.V3fVectorDataPlug.ValueType is IECore.V3fVectorData )
		self.failUnless( Gaffer.ObjectVectorPlug.ValueType is IECore.ObjectVector )

	def testReadOnlySetValueRaises( self ) :

		p = Gaffer.ObjectPlug( defaultValue = IECore.NullObject(), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.ReadOnly )
		self.assertRaises( RuntimeError, p.setValue, IECore.IntData( 10 ) )

	def testSetValueCopying( self ) :

		p = Gaffer.ObjectPlug( defaultValue = IECore.IntData( 1 ) )

		i = IECore.IntData( 10 )
		p.setValue( i )
		self.failIf( p.getValue( _copy=False ).isSame( i ) )

		i = IECore.IntData( 20 )
		p.setValue( i, _copy=False )
		self.failUnless( p.getValue( _copy=False ).isSame( i ) )

	def testCreateCounterpart( self ) :

		p = Gaffer.ObjectPlug( defaultValue = IECore.IntData( 20 ) )
		p2 = p.createCounterpart( "c", Gaffer.Plug.Direction.Out )

		self.assertEqual( p2.getName(), "c" )
		self.assertEqual( p2.direction(), Gaffer.Plug.Direction.Out )
		self.assertEqual( p2.defaultValue(), p.defaultValue() )
		self.assertEqual( p2.getFlags(), p.getFlags() )

if __name__ == "__main__":
	unittest.main()

