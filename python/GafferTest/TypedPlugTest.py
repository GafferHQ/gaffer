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

import imath

import IECore

import Gaffer
import GafferTest

class TypedPlugTest( GafferTest.TestCase ) :

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
		self.assertTrue( p2.getInput().isSame( p1 ) )
		p2.setInput( None )
		self.assertIsNone( p2.getInput(), None )

	def testAcceptsNoneInput( self ) :

		p = Gaffer.StringPlug( "hello" )
		self.assertTrue( p.acceptsInput( None ) )

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
			flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic
		)

		p2 = eval( repr( p1 ) )

		self.assertEqual( p2.getName(), p1.getName() )
		self.assertEqual( p2.direction(), p1.direction() )
		self.assertEqual( p2.defaultValue(), p1.defaultValue() )
		self.assertEqual( p2.getFlags(), p1.getFlags() )

	def testBoolPlugNumericConnections( self ) :

		b = Gaffer.BoolPlug()

		for p in ( Gaffer.FloatPlug(), Gaffer.IntPlug() ) :

			b.setInput( p )
			self.assertEqual( b.getValue(), False )

			p.setValue( 1 )
			self.assertEqual( b.getValue(), True )

			p.setValue( 0 )
			self.assertEqual( b.getValue(), False )

			p.setValue( 1000 )
			self.assertEqual( b.getValue(), True )

	def testNoChildrenAccepted( self ) :

		p1 = Gaffer.BoolPlug()
		p2 = Gaffer.BoolPlug()

		self.assertFalse( p1.acceptsChild( p2 ) )
		self.assertRaises( RuntimeError, p1.addChild, p2 )

	def testPrecomputedHash( self ) :

		class MatrixMultiplyNode( Gaffer.ComputeNode ) :

			def __init__( self, name = "MatrixMultiply" ) :

				Gaffer.ComputeNode.__init__( self, name )

				self["in1"] = Gaffer.M44fPlug()
				self["in2"] = Gaffer.M44fPlug()
				self["out"] = Gaffer.M44fPlug( direction = Gaffer.Plug.Direction.Out )

				self.numComputeCalls = 0
				self.numHashCalls = 0

			def affects( self, input ) :

				outputs = Gaffer.ComputeNode.affects( self, input )
				if input.isSame( self["in1"] ) or input.isSame( self["in2"] ) :
					outputs.append( self.getChild( "out" ) )

				return outputs

			def hash( self, output, context, h ) :

				assert( output.isSame( self.getChild( "out" ) ) )

				self["in1"].hash( h )
				self["in2"].hash( h )

				self.numHashCalls += 1

			def compute( self, output, context ) :

				assert( output.isSame( self.getChild( "out" ) ) )
				output.setValue( self["in1"].getValue() * self["in2"].getValue() )

				self.numComputeCalls += 1

		IECore.registerRunTimeTyped( MatrixMultiplyNode )

		n = MatrixMultiplyNode()

		self.assertEqual( n["out"].getValue(), imath.M44f() )
		self.assertEqual( n.numHashCalls, 1 )
		self.assertEqual( n.numComputeCalls, 1 )

		h = n["out"].hash()
		self.assertEqual( n.numHashCalls, 1 )
		self.assertEqual( n.numComputeCalls, 1 )

		# Calling `getValue()` with a precomputed hash shouldn't recompute the
		# hash again, even if it has been cleared from the cache.
		Gaffer.ValuePlug.clearHashCache()
		self.assertEqual( n["out"].getValue( _precomputedHash = h ), imath.M44f() )
		self.assertEqual( n.numHashCalls, 1 )
		self.assertEqual( n.numComputeCalls, 1 )

	def testBoolPlugStringConnections( self ) :

		n = GafferTest.AddNode()
		n["op1"].setValue( 0 )
		n["op2"].setValue( 2 )
		self.assertEqual( n["sum"].getValue(), 2 )

		s = Gaffer.StringPlug()
		n["enabled"].setInput( s )
		self.assertEqual( n["sum"].getValue(), 0 )

		s.setValue( "notEmpty" )
		self.assertEqual( n["sum"].getValue(), 2 )

		s.setValue( "${test}" )
		self.assertEqual( n["sum"].getValue(), 0 )

		with Gaffer.Context() as c :

			c["test"] = "notEmpty"
			self.assertEqual( n["sum"].getValue(), 2 )

			c["test"] = ""
			self.assertEqual( n["sum"].getValue(), 0 )

	def testValueType( self ) :

		self.assertIs( Gaffer.BoolPlug.ValueType, bool )
		self.assertIs( Gaffer.M33fPlug.ValueType, imath.M33f )
		self.assertIs( Gaffer.M44fPlug.ValueType, imath.M44f )
		self.assertIs( Gaffer.AtomicBox2fPlug.ValueType, imath.Box2f )
		self.assertIs( Gaffer.AtomicBox2iPlug.ValueType, imath.Box2i )
		self.assertIs( Gaffer.AtomicBox3fPlug.ValueType, imath.Box3f )

if __name__ == "__main__":
	unittest.main()
