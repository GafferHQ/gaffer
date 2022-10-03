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
import imath

import IECore

import Gaffer
import GafferTest

class CompoundDataPlugTest( GafferTest.TestCase ) :

	def test( self ) :

		p = Gaffer.CompoundDataPlug()

		m1 = Gaffer.NameValuePlug( "a", IECore.IntData( 10 ), "member1" )
		p.addChild( m1 )
		self.assertIsInstance( m1, Gaffer.ValuePlug )
		self.assertEqual( m1.getName(), "member1" )
		self.assertEqual( m1["name"].getValue(), "a" )
		self.assertEqual( m1["value"].getValue(), 10 )
		self.assertFalse( "enabled" in m1 )

		d, n = p.memberDataAndName( m1 )
		self.assertEqual( d, IECore.IntData( 10 ) )
		self.assertEqual( n, "a" )

		m1["name"].setValue( "b" )
		d, n = p.memberDataAndName( m1 )
		self.assertEqual( d, IECore.IntData( 10 ) )
		self.assertEqual( n, "b" )

		m2 = Gaffer.NameValuePlug( "c", IECore.FloatData( .5 ), "member1" )
		p.addChild( m2 )
		self.assertIsInstance( m2, Gaffer.ValuePlug )
		self.assertEqual( m2.getName(), "member2" )
		self.assertEqual( m2["name"].getValue(), "c" )
		self.assertEqual( m2["value"].getValue(), .5 )
		self.assertNotIn( "enabled", m2 )

		d, n = p.memberDataAndName( m2 )
		self.assertEqual( d, IECore.FloatData( .5 ) )
		self.assertEqual( n, "c" )

		m3 = Gaffer.NameValuePlug( "o", IECore.StringData( "--" ), True, name = "m" )
		p.addChild( m3 )
		self.assertIsInstance( m3, Gaffer.ValuePlug )
		self.assertEqual( m3.getName(), "m" )
		self.assertEqual( m3["name"].getValue(), "o" )
		self.assertEqual( m3["value"].getValue(), "--" )
		self.assertIn( "enabled", m3 )
		self.assertEqual( m3["enabled"].getValue(), True )

		d, n = p.memberDataAndName( m3 )
		self.assertEqual( d, IECore.StringData( "--" ) )
		self.assertEqual( n, "o" )

		m3["enabled"].setValue( False )
		d, n = p.memberDataAndName( m3 )
		self.assertEqual( d, None )
		self.assertEqual( n, "" )

		# test if creating a plug from data that has a geometric
		# interpretation specified transfers that interpretation to the plug
		m4 = Gaffer.NameValuePlug( "vector", IECore.V3fData( imath.V3f( 0 ), IECore.GeometricData.Interpretation.Vector ), True, name = "vector" )
		p.addChild( m4 )
		self.assertEqual( m4["value"].interpretation(), IECore.GeometricData.Interpretation.Vector )

	def testVectorData( self ) :

		p = Gaffer.CompoundDataPlug()

		m1 = Gaffer.NameValuePlug( "a", IECore.FloatVectorData( [ 1, 2, 3 ] ) )
		p.addChild( m1 )
		self.assertIsInstance( m1, Gaffer.ValuePlug )

		d, n = p.memberDataAndName( m1 )
		self.assertEqual( d, IECore.FloatVectorData( [ 1, 2, 3 ] ) )
		self.assertEqual( n, "a" )

		m2 = Gaffer.NameValuePlug( "b", IECore.IntVectorData( [ 1, 2, 3 ] ) )
		p.addChild( m2 )
		self.assertIsInstance( m2, Gaffer.ValuePlug )

		d, n = p.memberDataAndName( m2 )
		self.assertEqual( d, IECore.IntVectorData( [ 1, 2, 3 ] ) )
		self.assertEqual( n, "b" )

		m3 = Gaffer.NameValuePlug( "c", IECore.StringVectorData( [ "1", "2", "3" ] ) )
		p.addChild( m3 )
		self.assertIsInstance( m3, Gaffer.ValuePlug )

		d, n = p.memberDataAndName( m3 )
		self.assertEqual( d, IECore.StringVectorData( [ "1", "2", "3" ] ) )
		self.assertEqual( n, "c" )

		m4 = Gaffer.NameValuePlug( "d", IECore.V3fVectorData( [ imath.V3f( x ) for x in range( 1, 5 ) ] ) )
		p.addChild( m4 )
		self.assertIsInstance( m4, Gaffer.ValuePlug )

		d, n = p.memberDataAndName( m4 )
		self.assertEqual( d, IECore.V3fVectorData( [ imath.V3f( x ) for x in range( 1, 5 ) ] ) )
		self.assertEqual( n, "d" )

		m5 = Gaffer.NameValuePlug( "e", IECore.Color3fVectorData( [ imath.Color3f( x ) for x in range( 1, 5 ) ] ) )
		p.addChild( m5 )
		self.assertIsInstance( m5, Gaffer.ValuePlug )

		d, n = p.memberDataAndName( m5 )
		self.assertEqual( d, IECore.Color3fVectorData( [ imath.Color3f( x ) for x in range( 1, 5 ) ] ) )
		self.assertEqual( n, "e" )

		m6 = Gaffer.NameValuePlug( "f", IECore.M44fVectorData( [ imath.M44f() * x for x in range( 1, 5 ) ] ) )
		p.addChild( m6 )
		self.assertIsInstance( m6, Gaffer.ValuePlug )

		d, n = p.memberDataAndName( m6 )
		self.assertEqual( d, IECore.M44fVectorData( [ imath.M44f() * x for x in range( 1, 5 ) ] ) )
		self.assertEqual( n, "f" )

		m7 = Gaffer.NameValuePlug( "g", IECore.V2iVectorData( [ imath.V2i( x ) for x in range( 1, 5 ) ] ) )
		p.addChild( m7 )
		self.assertIsInstance( m7, Gaffer.ValuePlug )

		d, n = p.memberDataAndName( m7 )
		self.assertEqual( d, IECore.V2iVectorData( [ imath.V2i( x ) for x in range( 1, 5 ) ] ) )
		self.assertEqual( n, "g" )

		m8 = Gaffer.NameValuePlug( "h", IECore.M33fVectorData( [ imath.M33f() * x for x in range( 1, 5 ) ] ) )
		p.addChild( m8 )
		self.assertIsInstance( m8, Gaffer.ValuePlug )

		d, n = p.memberDataAndName( m8 )
		self.assertEqual( d, IECore.M33fVectorData( [ imath.M33f() * x for x in range( 1, 5 ) ] ) )
		self.assertEqual( n, "h" )

	def testImathVectorData( self ) :

		p = Gaffer.CompoundDataPlug()

		m1 = Gaffer.NameValuePlug( "a", IECore.V3fData( imath.V3f( 1, 2, 3 ) ) )
		p.addChild( m1 )
		self.assertIsInstance( m1, Gaffer.ValuePlug )

		d, n = p.memberDataAndName( m1 )
		self.assertEqual( d, IECore.V3fData( imath.V3f( 1, 2, 3 ) ) )
		self.assertEqual( n, "a" )

		m2 = Gaffer.NameValuePlug( "b", IECore.V2fData( imath.V2f( 1, 2 ) ) )
		p.addChild( m2 )
		self.assertIsInstance( m2, Gaffer.ValuePlug )

		d, n = p.memberDataAndName( m2 )
		self.assertEqual( d, IECore.V2fData( imath.V2f( 1, 2 ) ) )
		self.assertEqual( n, "b" )

	def testImathMatrixData( self ) :

		p = Gaffer.CompoundDataPlug()

		m1 = Gaffer.NameValuePlug( "a", IECore.M44fData( imath.M44f( *range(16) ) ) )
		p.addChild( m1 )
		self.assertIsInstance( m1, Gaffer.ValuePlug )

		d, n = p.memberDataAndName( m1 )
		self.assertEqual( d, IECore.M44fData( imath.M44f( *range(16) ) ) )
		self.assertEqual( n, "a" )

	def testTransformPlugData( self ) :

		p = Gaffer.CompoundDataPlug()

		m1 = Gaffer.NameValuePlug( "a", Gaffer.TransformPlug() )
		p.addChild( m1 )
		m1["value"]["translate"].setValue( imath.V3f( 1,2,3 ) )
		self.assertIsInstance( m1, Gaffer.ValuePlug )

		d, n = p.memberDataAndName( m1 )
		self.assertEqual( d, IECore.M44fData( imath.M44f(
			1, 0, 0, 0,
			0, 1, 0, 0,
			0, 0, 1, 0,
			1, 2, 3, 1,
		) ) )
		self.assertEqual( n, "a" )

	def testPlugFlags( self ) :

		p = Gaffer.CompoundDataPlug()
		m1 = Gaffer.NameValuePlug( "a", IECore.V3fData( imath.V3f( 1, 2, 3 ) ) )
		p.addChild( m1 )
		self.assertEqual( m1.getFlags(), Gaffer.Plug.Flags.Default )
		self.assertEqual( m1["name"].getFlags(), Gaffer.Plug.Flags.Default)
		self.assertEqual( m1["value"].getFlags(), Gaffer.Plug.Flags.Default )

		m2 = Gaffer.NameValuePlug( "a", IECore.V3fData( imath.V3f( 1, 2, 3 ) ), True )
		p.addChild( m2 )
		self.assertEqual( m2.getFlags(), Gaffer.Plug.Flags.Default )
		self.assertEqual( m2["name"].getFlags(), Gaffer.Plug.Flags.Default )
		self.assertEqual( m2["value"].getFlags(), Gaffer.Plug.Flags.Default )
		self.assertEqual( m2["enabled"].getFlags(), Gaffer.Plug.Flags.Default )

	def testCreateCounterpart( self ) :

		p1 = Gaffer.CompoundDataPlug()
		m1 = Gaffer.NameValuePlug( "a", IECore.V3fData( imath.V3f( 1, 2, 3 ) ), "member1" )
		p1.addChild( m1 )

		p2 = p1.createCounterpart( "c", Gaffer.Plug.Direction.Out )
		self.assertEqual( p2.typeName(), p1.typeName() )
		self.assertEqual( p2.getName(), "c" )
		self.assertEqual( p2.direction(), Gaffer.Plug.Direction.Out )
		self.assertEqual( len( p2 ), len( p1 ) )
		self.assertEqual( p2.getFlags(), p1.getFlags() )

		m2 = p2["member1"]
		self.assertEqual( m2.typeName(), m1.typeName() )
		self.assertEqual( m2.getFlags(), m1.getFlags() )
		self.assertEqual( m2.direction(), Gaffer.Plug.Direction.Out )
		self.assertEqual( m2.keys(), m1.keys() )

	def testCreateWithValuePlug( self ) :

		p = Gaffer.CompoundDataPlug()

		v = Gaffer.IntPlug( minValue = -10, maxValue = 10 )
		m1 = Gaffer.NameValuePlug( "a", v, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		p.addChild( m1 )
		self.assertTrue( v.parent().isSame( m1 ) )
		self.assertEqual( m1["value"].getName(), "value" )
		self.assertEqual( m1.getFlags(), Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		self.assertEqual( p.memberDataAndName( m1 ), ( IECore.IntData( 0 ), "a" ) )

		v2 = Gaffer.IntPlug( defaultValue = 5, minValue = -10, maxValue = 10 )
		m2 = Gaffer.NameValuePlug( "b", v2, True, name = "blah" )
		p.addChild( m2 )
		self.assertTrue( v2.parent().isSame( m2 ) )
		self.assertEqual( m2["value"].getName(), "value" )
		self.assertEqual( m2.getFlags(), Gaffer.Plug.Flags.Default )

		self.assertEqual( p.memberDataAndName( m2 ), ( IECore.IntData( 5 ), "b" ) )

	def testAdditionalChildrenRejected( self ) :

		p = Gaffer.CompoundDataPlug()

		self.assertRaises( RuntimeError, p.addChild, Gaffer.IntPlug() )
		self.assertRaises( RuntimeError, p.addChild, Gaffer.Plug() )

		m = Gaffer.NameValuePlug( "a", IECore.IntData( 10 ) )
		self.assertRaises( RuntimeError, m.addChild, Gaffer.IntPlug() )
		self.assertRaises( RuntimeError, m.addChild, Gaffer.StringPlug( "name" ) )
		self.assertRaises( RuntimeError, m.addChild, Gaffer.IntPlug( "name" ) )
		self.assertRaises( RuntimeError, m.addChild, Gaffer.IntPlug( "value" ) )

	def testSerialisation( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["p"] = Gaffer.CompoundDataPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["p"].addChild( Gaffer.NameValuePlug( "a", IECore.IntData( 10 ), "a", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual(
			s["n"]["p"].memberDataAndName( s["n"]["p"]["a"] ),
			s2["n"]["p"].memberDataAndName( s2["n"]["p"]["a"] ),
		)

	def testAddMembers( self ) :

		p = Gaffer.CompoundDataPlug()

		p.addMembers( IECore.CompoundData( { "one" : 1, "two" : 2 } ) )
		self.assertEqual( len( p ), 2 )
		self.assertEqual( p[0].getName(), "member1" )
		self.assertEqual( p[1].getName(), "member2" )

		c = IECore.CompoundData()
		p.fillCompoundData( c )
		self.assertEqual( c, IECore.CompoundData( { "one" : 1, "two" : 2 } ) )

	def testAddMembersWithSpecificNames( self ) :

		p = Gaffer.CompoundDataPlug()
		p.addMembers( IECore.CompoundData( { "one" : 1 } ), useNameAsPlugName=True )

		self.assertEqual( len( p ), 1 )
		self.assertEqual( p[0].getName(), "one" )

		o = IECore.CompoundObject()
		p.fillCompoundObject( o )
		self.assertEqual( o, IECore.CompoundObject( { "one" : IECore.IntData( 1 ) } ) )

	def testAddMembersSerialisation( self ) :

		d1 = IECore.CompoundData( { "one" : 1, "two" : 2 } )

		s1 = Gaffer.ScriptNode()
		s1["n"] = Gaffer.Node()
		s1["n"]["user"]["p"] = Gaffer.CompoundDataPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s1["n"]["user"]["p"].addMembers( d1 )

		s2 = Gaffer.ScriptNode()
		s2.execute( s1.serialise() )
		d2 = IECore.CompoundData()
		s2["n"]["user"]["p"].fillCompoundData( d2 )

		self.assertEqual( d1, d2 )

	def testBoxTypes( self ) :

		p = Gaffer.CompoundDataPlug()

		for name, value in [
			( "b2f", IECore.Box2fData( imath.Box2f( imath.V2f( 0, 1 ), imath.V2f( 1, 2 ) ) ) ),
			( "b2i", IECore.Box2iData( imath.Box2i( imath.V2i( -1, 10 ), imath.V2i( 11, 20 ) ) ) ),
			( "b3f", IECore.Box3fData( imath.Box3f( imath.V3f( 0, 1, 2 ), imath.V3f( 3, 4, 5 ) ) ) ),
			( "b3i", IECore.Box3iData( imath.Box3i( imath.V3i( 0, 1, 2 ), imath.V3i( 3, 4, 5 ) ) ) ),
		] :
			p.addChild( Gaffer.NameValuePlug( name, value ) )
			self.assertEqual( p.memberDataAndName( p[-1] ), ( value, name ) )

	def testBoxPromotion( self ) :

		s = Gaffer.ScriptNode()

		s["b"] = Gaffer.Box()
		s["b"]["n"] = Gaffer.Node()
		s["b"]["n"]["p"] = Gaffer.CompoundDataPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		p = Gaffer.PlugAlgo.promote( s["b"]["n"]["p"] )
		p.setName( "p" )

		def assertPreconditions( script ) :

			self.assertEqual( script["b"]["n"]["p"].keys(), [] )
			self.assertEqual( script["b"]["p"].keys(), [] )
			self.assertTrue( script["b"]["n"]["p"].getInput().isSame( script["b"]["p"] ) )

		def assertPostconditions( script ) :

			self.assertEqual( script["b"]["p"].keys(), [ "test" ] )
			self.assertEqual( script["b"]["n"]["p"].keys(), [ "test" ] )

			self.assertEqual( script["b"]["p"]["test"].keys(), [ "name", "value" ]  )
			self.assertEqual( script["b"]["n"]["p"]["test"].keys(), [ "name", "value" ]  )

			self.assertTrue( script["b"]["n"]["p"].getInput().isSame( script["b"]["p"] ) )
			self.assertTrue( script["b"]["n"]["p"]["test"].getInput().isSame( script["b"]["p"]["test"] ) )
			self.assertTrue( script["b"]["n"]["p"]["test"]["name"].getInput().isSame( script["b"]["p"]["test"]["name"] ) )
			self.assertTrue( script["b"]["n"]["p"]["test"]["value"].getInput().isSame( script["b"]["p"]["test"]["value"] ) )

		assertPreconditions( s )

		with Gaffer.UndoScope( s ) :

			p.addChild(
				Gaffer.NameValuePlug( "test", 10, "test",
					Gaffer.Plug.Direction.In, Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic
				)
			)

		assertPostconditions( s )

		s.undo()
		assertPreconditions( s )

		s.redo()
		assertPostconditions( s )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		assertPostconditions( s2 )

	def testHashOmitsDisabledMembers( self ) :

		p = Gaffer.CompoundDataPlug()
		h1 = p.hash()

		m1 = Gaffer.NameValuePlug( "test1", 10, False )
		p.addChild( m1 )
		m2 = Gaffer.NameValuePlug( "test2", 10, False )
		p.addChild( m2 )

		# even though we've added members, they're both
		# disabled, so as far as the hash is concerned, they're
		# not there.
		h2 = p.hash()
		self.assertEqual( h1, h2 )

		# when we enable one, the hash should change.
		m1["enabled"].setValue( True )
		h3 = p.hash()
		self.assertNotEqual( h2, h3 )

		# and it should continue to change as we change the
		# name and value for the enabled member.

		m1["value"].setValue( 20 )
		h4 = p.hash()
		self.assertNotEqual( h3, h4 )

		m1["name"].setValue( "test3" )
		h5 = p.hash()
		self.assertNotEqual( h4, h5 )

		# but changing the name and value for the disabled
		# member should have no effect at all.

		m2["value"].setValue( 40 )
		self.assertEqual( h5, p.hash() )

		m2["name"].setValue( "test4" )
		self.assertEqual( h5, p.hash() )

	def testInternedStringVectorData( self ) :

		d = IECore.InternedStringVectorData( [ "a", "b" ] )
		p = Gaffer.CompoundDataPlug()
		m = Gaffer.NameValuePlug( "test", d )
		p.addChild( m )
		self.assertTrue( isinstance( m["value"], Gaffer.InternedStringVectorDataPlug ) )
		self.assertEqual( m["value"].defaultValue(), d )
		self.assertEqual( m["value"].getValue(), d )

		v, n = p.memberDataAndName( m )
		self.assertEqual( v, d )
		self.assertEqual( n, "test" )

	def testNonAlphanumericNames( self ) :

		p = Gaffer.CompoundDataPlug()
		p.addMembers(
			IECore.CompoundData( {
				"test:A" : 10,
				"@j" : 20
			} ),
			useNameAsPlugName = True,
		)

		self.assertEqual( set( p.keys() ), { "test_A", "_j" } )
		self.assertEqual( p["test_A"]["value"].getValue(), 10 )
		self.assertEqual( p["_j"]["value"].getValue(), 20 )

	def testNonValuePlugs( self ) :

		p = Gaffer.CompoundDataPlug()
		p["test"] = Gaffer.NameValuePlug( "name", Gaffer.Plug() )

		with self.assertRaisesRegex( RuntimeError, "Not a ValuePlug" ) :
			p.hash()

		d = IECore.CompoundData()
		with self.assertRaisesRegex( RuntimeError, "Not a ValuePlug" ) :
			p.fillCompoundData( d )

if __name__ == "__main__":
	unittest.main()
