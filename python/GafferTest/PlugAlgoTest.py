##########################################################################
#
#  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

class PlugAlgoTest( GafferTest.TestCase ) :

	def tearDown( self ) :

		GafferTest.TestCase.tearDown( self )

		Gaffer.Metadata.deregisterValue( GafferTest.AddNode, "op1", "plugAlgoTest:a" )

	def testPromote( self ) :

		s = Gaffer.ScriptNode()

		s["b"] = Gaffer.Box()
		s["b"]["n1"] = GafferTest.AddNode()
		s["b"]["n1"]["op1"].setValue( -10 )
		s["n2"] = GafferTest.AddNode()

		self.assertTrue( Gaffer.PlugAlgo.canPromote( s["b"]["n1"]["op1"] ) )
		self.assertFalse( Gaffer.PlugAlgo.canPromote( s["n2"]["op1"], parent = s["b"]["user"] ) )

		self.assertFalse( Gaffer.PlugAlgo.isPromoted( s["b"]["n1"]["op1"] ) )
		self.assertFalse( Gaffer.PlugAlgo.isPromoted( s["b"]["n1"]["op2"] ) )
		self.assertFalse( Gaffer.PlugAlgo.isPromoted( s["n2"]["op1"] ) )

		p = Gaffer.PlugAlgo.promote( s["b"]["n1"]["op1"] )
		self.assertEqual( p.getName(), "op1" )
		self.assertTrue( p.parent().isSame( s["b"] ) )
		self.assertTrue( s["b"]["n1"]["op1"].getInput().isSame( p ) )
		self.assertTrue( Gaffer.PlugAlgo.isPromoted( s["b"]["n1"]["op1"] ) )
		self.assertFalse( Gaffer.PlugAlgo.canPromote( s["b"]["n1"]["op1"] ) )
		self.assertEqual( p.getValue(), -10 )

	def testPromoteColor( self ) :

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()
		s["b"]["n"] = Gaffer.Node()
		s["b"]["n"]["c"] = Gaffer.Color3fPlug()
		s["b"]["n"]["c"].setValue( imath.Color3f( 1, 0, 1 ) )

		self.assertTrue( Gaffer.PlugAlgo.canPromote( s["b"]["n"]["c"] ) )
		self.assertFalse( Gaffer.PlugAlgo.isPromoted( s["b"]["n"]["c"] ) )

		p = Gaffer.PlugAlgo.promote( s["b"]["n"]["c"] )

		self.assertTrue( isinstance( p, Gaffer.Color3fPlug ) )
		self.assertTrue( s["b"]["n"]["c"].getInput().isSame( p ) )
		self.assertTrue( s["b"]["n"]["c"]["r"].getInput().isSame( p["r"] ) )
		self.assertTrue( s["b"]["n"]["c"]["g"].getInput().isSame( p["g"] ) )
		self.assertTrue( s["b"]["n"]["c"]["b"].getInput().isSame( p["b"] ) )
		self.assertEqual( p.getValue(), imath.Color3f( 1, 0, 1 ) )

	def testPromoteCompoundPlugAndSerialise( self ) :

		s = Gaffer.ScriptNode()

		s["b"] = Gaffer.Box()
		s["b"]["n"] = GafferTest.CompoundPlugNode()
		s["b"]["n"]["p"]["s"].setValue( "hello" )

		Gaffer.PlugAlgo.promote( s["b"]["n"]["p"] )

		ss = s.serialise()

		s = Gaffer.ScriptNode()
		s.execute( ss )

		self.assertEqual( s["b"]["n"]["p"]["s"].getValue(), "hello" )

	def testPromoteDynamicColorPlugAndSerialise( self ) :

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()
		s["b"]["n"] = Gaffer.Node()
		s["b"]["n"]["c"] = Gaffer.Color3fPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		Gaffer.PlugAlgo.promote( s["b"]["n"]["c"] )

		ss = s.serialise()

		s = Gaffer.ScriptNode()
		s.execute( ss )

		self.assertTrue( isinstance( s["b"]["c"], Gaffer.Color3fPlug ) )
		self.assertTrue( s["b"]["n"]["c"].getInput().isSame( s["b"]["c"] ) )

	def testPromoteNonDynamicColorPlugAndSerialise( self ) :

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()
		s["b"]["n"] = Gaffer.Random()

		p = Gaffer.PlugAlgo.promote( s["b"]["n"]["baseColor"] )
		p.setValue( imath.Color3f( 1, 2, 3 ) )
		p.setName( "c" )

		self.assertTrue( isinstance( s["b"]["c"], Gaffer.Color3fPlug ) )
		self.assertTrue( s["b"]["n"]["baseColor"].getInput().isSame( s["b"]["c"] ) )
		self.assertTrue( s["b"]["n"]["baseColor"]["r"].getInput().isSame( s["b"]["c"]["r"] ) )
		self.assertTrue( s["b"]["n"]["baseColor"]["g"].getInput().isSame( s["b"]["c"]["g"] ) )
		self.assertTrue( s["b"]["n"]["baseColor"]["b"].getInput().isSame( s["b"]["c"]["b"] ) )
		self.assertEqual( s["b"]["c"].getValue(), imath.Color3f( 1, 2, 3 ) )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertTrue( isinstance( s2["b"]["c"], Gaffer.Color3fPlug ) )
		self.assertTrue( s2["b"]["n"]["baseColor"].getInput().isSame( s2["b"]["c"] ) )
		self.assertTrue( s2["b"]["n"]["baseColor"]["r"].getInput().isSame( s2["b"]["c"]["r"] ) )
		self.assertTrue( s2["b"]["n"]["baseColor"]["g"].getInput().isSame( s2["b"]["c"]["g"] ) )
		self.assertTrue( s2["b"]["n"]["baseColor"]["b"].getInput().isSame( s2["b"]["c"]["b"] ) )
		self.assertEqual( s2["b"]["c"].getValue(), imath.Color3f( 1, 2, 3 ) )

	def testCantPromoteNonSerialisablePlugs( self ) :

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()
		s["b"]["n"] = Gaffer.Node()
		s["b"]["n"]["p"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default & ~Gaffer.Plug.Flags.Serialisable )

		self.assertEqual( Gaffer.PlugAlgo.canPromote( s["b"]["n"]["p"] ), False )
		self.assertRaises( RuntimeError, Gaffer.PlugAlgo.promote, s["b"]["n"]["p"] )

	def testUnpromoting( self ) :

		s = Gaffer.ScriptNode()

		s["b"] = Gaffer.Box()
		s["b"]["n1"] = GafferTest.AddNode()

		p = Gaffer.PlugAlgo.promote( s["b"]["n1"]["op1"] )
		self.assertTrue( Gaffer.PlugAlgo.isPromoted( s["b"]["n1"]["op1"] ) )
		self.assertTrue( p.node().isSame( s["b"] ) )

		Gaffer.PlugAlgo.unpromote( s["b"]["n1"]["op1"] )
		self.assertFalse( Gaffer.PlugAlgo.isPromoted( s["b"]["n1"]["op1"] ) )
		self.assertTrue( p.node() is None )

	def testColorUnpromoting( self ) :

		s = Gaffer.ScriptNode()

		s["b"] = Gaffer.Box()
		s["b"]["n"] = Gaffer.Node()
		s["b"]["n"]["c"] = Gaffer.Color3fPlug()

		p = Gaffer.PlugAlgo.promote( s["b"]["n"]["c"] )
		self.assertTrue( Gaffer.PlugAlgo.isPromoted( s["b"]["n"]["c"] ) )
		self.assertTrue( Gaffer.PlugAlgo.isPromoted( s["b"]["n"]["c"]["r"] ) )
		self.assertTrue( Gaffer.PlugAlgo.isPromoted( s["b"]["n"]["c"]["g"] ) )
		self.assertTrue( Gaffer.PlugAlgo.isPromoted( s["b"]["n"]["c"]["b"] ) )
		self.assertTrue( p.node().isSame( s["b"] ) )

		Gaffer.PlugAlgo.unpromote( s["b"]["n"]["c"] )
		self.assertFalse( Gaffer.PlugAlgo.isPromoted( s["b"]["n"]["c"] ) )
		self.assertFalse( Gaffer.PlugAlgo.isPromoted( s["b"]["n"]["c"]["r"] ) )
		self.assertFalse( Gaffer.PlugAlgo.isPromoted( s["b"]["n"]["c"]["g"] ) )
		self.assertFalse( Gaffer.PlugAlgo.isPromoted( s["b"]["n"]["c"]["b"] ) )
		self.assertTrue( p.node() is None )

	def testIncrementalUnpromoting( self ) :

		s = Gaffer.ScriptNode()

		s["b"] = Gaffer.Box()

		s["b"]["n"] = Gaffer.Node()
		s["b"]["n"]["c"] = Gaffer.Color3fPlug()

		p = Gaffer.PlugAlgo.promote( s["b"]["n"]["c"] )
		self.assertTrue( Gaffer.PlugAlgo.isPromoted( s["b"]["n"]["c"] ) )
		self.assertTrue( Gaffer.PlugAlgo.isPromoted( s["b"]["n"]["c"]["r"] ) )
		self.assertTrue( Gaffer.PlugAlgo.isPromoted( s["b"]["n"]["c"]["g"] ) )
		self.assertTrue( Gaffer.PlugAlgo.isPromoted( s["b"]["n"]["c"]["b"] ) )
		self.assertTrue( p.node().isSame( s["b"] ) )

		Gaffer.PlugAlgo.unpromote( s["b"]["n"]["c"]["r"] )
		self.assertFalse( Gaffer.PlugAlgo.isPromoted( s["b"]["n"]["c"] ) )
		self.assertFalse( Gaffer.PlugAlgo.isPromoted( s["b"]["n"]["c"]["r"] ) )
		self.assertTrue( Gaffer.PlugAlgo.isPromoted( s["b"]["n"]["c"]["g"] ) )
		self.assertTrue( Gaffer.PlugAlgo.isPromoted( s["b"]["n"]["c"]["b"] ) )
		self.assertTrue( p.node().isSame( s["b"] ) )

		Gaffer.PlugAlgo.unpromote( s["b"]["n"]["c"]["g"] )
		self.assertFalse( Gaffer.PlugAlgo.isPromoted( s["b"]["n"]["c"] ) )
		self.assertFalse( Gaffer.PlugAlgo.isPromoted( s["b"]["n"]["c"]["r"] ) )
		self.assertFalse( Gaffer.PlugAlgo.isPromoted( s["b"]["n"]["c"]["g"] ) )
		self.assertTrue( Gaffer.PlugAlgo.isPromoted( s["b"]["n"]["c"]["b"] ) )
		self.assertTrue( p.node().isSame( s["b"] ) )

		Gaffer.PlugAlgo.unpromote( s["b"]["n"]["c"]["b"] )
		self.assertFalse( Gaffer.PlugAlgo.isPromoted( s["b"]["n"]["c"] ) )
		self.assertFalse( Gaffer.PlugAlgo.isPromoted( s["b"]["n"]["c"]["r"] ) )
		self.assertFalse( Gaffer.PlugAlgo.isPromoted( s["b"]["n"]["c"]["g"] ) )
		self.assertFalse( Gaffer.PlugAlgo.isPromoted( s["b"]["n"]["c"]["b"] ) )
		self.assertTrue( p.node() is None )

	def testPromoteOutputPlug( self ) :

		b = Gaffer.Box()
		b["n"] = GafferTest.AddNode()

		self.assertTrue( Gaffer.PlugAlgo.canPromote( b["n"]["sum"] ) )

		sum = Gaffer.PlugAlgo.promote( b["n"]["sum"] )
		self.assertTrue( b.isAncestorOf( sum ) )
		self.assertTrue( sum.direction() == Gaffer.Plug.Direction.Out )
		self.assertEqual( sum.getInput(), b["n"]["sum"] )
		self.assertTrue( Gaffer.PlugAlgo.isPromoted( b["n"]["sum"] ) )
		self.assertFalse( Gaffer.PlugAlgo.canPromote( b["n"]["sum"] ) )
		self.assertRaises( RuntimeError, Gaffer.PlugAlgo.promote, b["n"]["sum"] )

		b["n"]["op1"].setValue( 10 )
		b["n"]["op2"].setValue( 12 )

		self.assertEqual( sum.getValue(), 22 )

		Gaffer.PlugAlgo.unpromote( b["n"]["sum"] )
		self.assertFalse( Gaffer.PlugAlgo.isPromoted( b["n"]["sum"] ) )
		self.assertTrue( sum.parent() is None )
		self.assertTrue( Gaffer.PlugAlgo.canPromote( b["n"]["sum"] ) )

	def testPromoteDynamicBoxPlugAndSerialise( self ) :

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()
		s["b"]["n"] = Gaffer.Node()
		s["b"]["n"]["p"] = Gaffer.Box2iPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		p = Gaffer.PlugAlgo.promote( s["b"]["n"]["p"] )
		p.setValue( imath.Box2i( imath.V2i( 1, 2 ), imath.V2i( 3, 4 ) ) )
		p.setName( "c" )

		self.assertTrue( isinstance( s["b"]["c"], Gaffer.Box2iPlug ) )
		self.assertTrue( s["b"]["n"]["p"].getInput().isSame( s["b"]["c"] ) )
		self.assertTrue( s["b"]["n"]["p"]["min"].getInput().isSame( s["b"]["c"]["min"] ) )
		self.assertTrue( s["b"]["n"]["p"]["max"].getInput().isSame( s["b"]["c"]["max"] ) )
		self.assertEqual( s["b"]["c"].getValue(), imath.Box2i( imath.V2i( 1, 2 ), imath.V2i( 3, 4 ) ) )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertTrue( isinstance( s2["b"]["c"], Gaffer.Box2iPlug ) )
		self.assertTrue( s2["b"]["n"]["p"].getInput().isSame( s2["b"]["c"] ) )
		self.assertTrue( s2["b"]["n"]["p"]["min"].getInput().isSame( s2["b"]["c"]["min"] ) )
		self.assertTrue( s2["b"]["n"]["p"]["max"].getInput().isSame( s2["b"]["c"]["max"] ) )
		self.assertEqual( s2["b"]["c"].getValue(), imath.Box2i( imath.V2i( 1, 2 ), imath.V2i( 3, 4 ) ) )

	def testPromoteStaticPlugsWithChildren( self ) :

		s = Gaffer.ScriptNode()

		s["b"] = Gaffer.Box()
		s["b"]["n"] = GafferTest.CompoundPlugNode()
		s["b"]["n"]["valuePlug"]["i"].setValue( 10 )

		p = Gaffer.PlugAlgo.promote( s["b"]["n"]["valuePlug"] )
		p.setName( "p" )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( s2["b"]["n"]["valuePlug"]["i"].getValue(), 10 )
		self.assertTrue( s2["b"]["n"]["valuePlug"]["i"].getInput().isSame( s2["b"]["p"]["i"] ) )

	def testPromoteDynamicPlugsWithChildren( self ) :

		s = Gaffer.ScriptNode()

		s["b"] = Gaffer.Box()
		s["b"]["n"] = Gaffer.Node()

		s["b"]["n"]["user"]["p"] = Gaffer.Plug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["b"]["n"]["user"]["p"]["p"] = Gaffer.Plug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["b"]["n"]["user"]["p"]["p"]["i"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["b"]["n"]["user"]["v"] = Gaffer.ValuePlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["b"]["n"]["user"]["v"]["v"] = Gaffer.ValuePlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["b"]["n"]["user"]["v"]["v"]["i"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		p = Gaffer.PlugAlgo.promote( s["b"]["n"]["user"]["p"] )
		p.setName( "p" )
		p["p"]["i"].setValue( 10 )

		v = Gaffer.PlugAlgo.promote( s["b"]["n"]["user"]["v"] )
		v.setName( "v" )
		v["v"]["i"].setValue( 20 )

		def assertValid( script ) :

			self.assertEqual( script["b"]["n"]["user"]["p"]["p"]["i"].getValue(), 10 )
			self.assertTrue( script["b"]["n"]["user"]["p"]["p"]["i"].getInput().isSame( script["b"]["p"]["p"]["i"] ) )
			self.assertTrue( script["b"]["n"]["user"]["p"]["p"].getInput().isSame( script["b"]["p"]["p"] ) )
			self.assertTrue( script["b"]["n"]["user"]["p"].getInput().isSame( script["b"]["p"] ) )

			self.assertEqual( script["b"]["n"]["user"]["v"]["v"]["i"].getValue(), 20 )
			self.assertTrue( script["b"]["n"]["user"]["v"]["v"]["i"].getInput().isSame( script["b"]["v"]["v"]["i"] ) )
			self.assertTrue( script["b"]["n"]["user"]["v"]["v"].getInput().isSame( script["b"]["v"]["v"] ) )
			self.assertTrue( script["b"]["n"]["user"]["v"].getInput().isSame( script["b"]["v"] ) )

		assertValid( s )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		assertValid( s2 )

	def testPromoteArrayPlug( self ) :

		s = Gaffer.ScriptNode()

		s["a"] = GafferTest.AddNode()

		s["b"] = Gaffer.Box()
		s["b"]["n"] = GafferTest.ArrayPlugNode()

		p = Gaffer.PlugAlgo.promote( ( s["b"]["n"]["in"] ) )
		p.setName( "p" )

		s["b"]["p"][0].setInput( s["a"]["sum"] )
		s["b"]["p"][1].setInput( s["a"]["sum"] )

		self.assertEqual( len( s["b"]["n"]["in"] ), 3 )
		self.assertTrue( s["b"]["n"]["in"].getInput().isSame( s["b"]["p"] ) )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( len( s2["b"]["n"]["in"] ), 3 )
		self.assertTrue( s2["b"]["n"]["in"].getInput().isSame( s2["b"]["p"] ) )

	def testPromotionIncludesArbitraryMetadata( self ) :

		s = Gaffer.ScriptNode()

		s["b"] = Gaffer.Box()
		s["b"]["n"] = Gaffer.Node()
		s["b"]["n"]["user"]["p"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		Gaffer.Metadata.registerValue( s["b"]["n"]["user"]["p"], "testInt", 10 )
		Gaffer.Metadata.registerValue( s["b"]["n"]["user"]["p"], "testString", "test" )

		p = Gaffer.PlugAlgo.promote( s["b"]["n"]["user"]["p"] )
		p.setName( "p" )

		self.assertEqual( Gaffer.Metadata.value( p, "testInt" ), 10 )
		self.assertEqual( Gaffer.Metadata.value( p, "testString" ), "test" )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( Gaffer.Metadata.value( s2["b"]["p"], "testInt" ), 10 )
		self.assertEqual( Gaffer.Metadata.value( s2["b"]["p"], "testString" ), "test" )

	def testPromotionIncludesArbitraryChildMetadata( self ) :

		s = Gaffer.ScriptNode()

		s["b"] = Gaffer.Box()
		s["b"]["n"] = Gaffer.Node()
		s["b"]["n"]["user"]["p"] = Gaffer.Plug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["b"]["n"]["user"]["p"]["i"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		Gaffer.Metadata.registerValue( s["b"]["n"]["user"]["p"], "testInt", 10 )
		Gaffer.Metadata.registerValue( s["b"]["n"]["user"]["p"]["i"], "testString", "test" )

		p = Gaffer.PlugAlgo.promote( s["b"]["n"]["user"]["p"] )
		p.setName( "p" )

		self.assertEqual( Gaffer.Metadata.value( p, "testInt" ), 10 )
		self.assertEqual( Gaffer.Metadata.value( p["i"], "testString" ), "test" )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( Gaffer.Metadata.value( s2["b"]["p"], "testInt" ), 10 )
		self.assertEqual( Gaffer.Metadata.value( s2["b"]["p"]["i"], "testString" ), "test" )

	def testPromoteToNonBoxParent( self ) :

		n = Gaffer.Node()
		n["n"] = GafferTest.AddNode()

		self.assertTrue( Gaffer.PlugAlgo.canPromote( n["n"]["op1"] ) )

		p = Gaffer.PlugAlgo.promote( n["n"]["op1"] )
		self.assertTrue( p.isSame( n["op1"] ) )
		self.assertTrue( n["n"]["op1"].getInput().isSame( n["op1"] ) )
		self.assertTrue( Gaffer.PlugAlgo.isPromoted( n["n"]["op1"] ) )
		self.assertFalse( n["op1"].getFlags( Gaffer.Plug.Flags.Dynamic ) )

		Gaffer.PlugAlgo.unpromote( n["n"]["op1"] )
		self.assertTrue( "op1" not in "n" )
		self.assertTrue( n["n"]["op1"].getInput() is None )

	def testPromotionParent( self ) :

		n1 = Gaffer.Node()
		n1["n"] = GafferTest.AddNode()
		n2 = Gaffer.Node()

		self.assertTrue( Gaffer.PlugAlgo.canPromote( n1["n"]["op1"], parent = n1["user"] ) )
		self.assertFalse( Gaffer.PlugAlgo.canPromote( n1["n"]["op1"], parent = n2["user"] ) )

		self.assertRaises( RuntimeError,  Gaffer.PlugAlgo.promote, n1["n"]["op1"], parent = n2["user"] )

		p = Gaffer.PlugAlgo.promote( n1["n"]["op1"], parent = n1["user"] )
		self.assertTrue( p.parent().isSame( n1["user"] ) )
		self.assertTrue( Gaffer.PlugAlgo.isPromoted( n1["n"]["op1"] ) )

	def testPromotionExcludingMetadata( self ) :

		n = Gaffer.Node()
		n["a"] = GafferTest.AddNode()
		Gaffer.Metadata.registerValue( n["a"]["op1"], "test", "testValue" )
		Gaffer.Metadata.registerValue( n["a"]["op2"], "test", "testValue" )

		p1 = Gaffer.PlugAlgo.promote( n["a"]["op1"] )
		self.assertEqual( Gaffer.Metadata.value( p1, "test" ), "testValue" )

		p2 = Gaffer.PlugAlgo.promote( n["a"]["op2"], excludeMetadata = "*" )
		self.assertEqual( Gaffer.Metadata.value( p2, "test" ), None )

	def testPromotedNonBoxMetadataIsNonPersistent( self ) :

		n = Gaffer.Node()
		n["a"] = GafferTest.AddNode()
		Gaffer.Metadata.registerValue( n["a"]["op1"], "testPersistence", 10 )

		p = Gaffer.PlugAlgo.promote( n["a"]["op1"] )
		self.assertEqual( Gaffer.Metadata.value( p, "testPersistence" ), 10 )
		self.assertTrue( "testPersistence" in Gaffer.Metadata.registeredValues( p ) )
		self.assertTrue( "testPersistence" not in Gaffer.Metadata.registeredValues( p, persistentOnly = True ) )

	def testPromoteWithName( self ) :

		s = Gaffer.ScriptNode()

		s["b"] = Gaffer.Box()
		s["b"]["n1"] = GafferTest.AddNode()

		p = Gaffer.PlugAlgo.promoteWithName( s["b"]["n1"]["op1"], 'newName' )

		self.assertEqual( p.getName(), 'newName' )

	def testPromotePlugWithDescendantValues( self ) :

		n = Gaffer.Node()
		n["a"] = Gaffer.Node()
		n["a"]["p"] = Gaffer.Plug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		n["a"]["p"]["c"] = Gaffer.Plug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		n["a"]["p"]["c"]["i"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		n["a"]["p"]["c"]["v"] = Gaffer.V3fPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		n["a"]["p"]["c"]["i"].setValue( 10 )
		n["a"]["p"]["c"]["v"].setValue( imath.V3f( 1, 2, 3 ) )

		p = Gaffer.PlugAlgo.promote( n["a"]["p"] )

		self.assertEqual( n["a"]["p"]["c"]["i"].getValue(), 10 )
		self.assertEqual( n["a"]["p"]["c"]["v"].getValue(), imath.V3f( 1, 2, 3 ) )

	def testPromoteNonSerialisableOutput( self ) :

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()
		s["b"]["a"] = GafferTest.AddNode()
		s["b"]["a"]["sum"].setFlags( Gaffer.Plug.Flags.Serialisable, False )

		Gaffer.PlugAlgo.promote( s["b"]["a"]["sum"] )
		self.assertTrue( s["b"]["sum"].getInput().isSame( s["b"]["a"]["sum"] ) )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertTrue( s2["b"]["sum"].getInput().isSame( s2["b"]["a"]["sum"] ) )

	def testNonBoxDoublePromote( self ) :

		s = Gaffer.ScriptNode()
		s['a'] = Gaffer.SubGraph()
		s['a']['b'] = Gaffer.SubGraph()
		s['a']['b']['c'] = GafferTest.AddNode()
		Gaffer.Metadata.registerValue( s['a']['b']['c']["op1"], "test", 10 )

		Gaffer.PlugAlgo.promote( s['a']['b']['c']['op1'] )
		Gaffer.PlugAlgo.promote( s['a']['b']['op1'] )

		self.assertEqual( Gaffer.Metadata.value( s['a']['b']['c']['op1'], "test" ), 10 )
		self.assertEqual( Gaffer.Metadata.value( s['a']['b']['op1'], "test" ), 10 )
		self.assertEqual( Gaffer.Metadata.value( s['a']['op1'], "test" ), 10 )

	def testPromoteCompoundPlugWithColorPlug( self ) :

		s = Gaffer.ScriptNode()

		s["b"] = Gaffer.Box()
		s["b"]["n"] = Gaffer.Node()
		s["b"]["n"]["user"]["p"] = Gaffer.Plug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["b"]["n"]["user"]["p"]["c"] = Gaffer.Color3fPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		Gaffer.PlugAlgo.promote( s["b"]["n"]["user"]["p"] )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( len( s2["b"]["n"]["user"]["p"]["c"] ), 3 )

	class AddTen( Gaffer.Node ) :

		def __init__( self, name = "AddTen" ) :

			Gaffer.Node.__init__( self, name )

			self["__add"] = GafferTest.AddNode()
			self["__add"]["op2"].setValue( 10 )

			Gaffer.PlugAlgo.promoteWithName( self["__add"]["op1"], "in" )
			Gaffer.PlugAlgo.promoteWithName( self["__add"]["sum"], "out" )

	IECore.registerRunTimeTyped( AddTen )

	def testPromoteInNodeConstructor( self ) :

		Gaffer.Metadata.registerValue( GafferTest.AddNode, "op1", "plugAlgoTest:a", "a" )

		script = Gaffer.ScriptNode()
		script["box"] = Gaffer.Box()
		script["box"]["n"] = self.AddTen()

		# We want the metadata from the AddNode to have been promoted, but registered
		# as non-persistent so that it won't be serialised unnecessarily.

		self.assertEqual( Gaffer.Metadata.value( script["box"]["n"]["in"], "plugAlgoTest:a" ), "a" )
		self.assertIn( "plugAlgoTest:a", Gaffer.Metadata.registeredValues( script["box"]["n"]["in"] ) )
		self.assertNotIn( "plugAlgoTest:a", Gaffer.Metadata.registeredValues( script["box"]["n"]["in"], persistentOnly = True ) )

		# And if we promote up one more level, we want that to work, and we want the
		# new metadata to be persistent so that it will be serialised and restored.

		Gaffer.PlugAlgo.promote( script["box"]["n"]["in"] )
		self.assertIn( "plugAlgoTest:a", Gaffer.Metadata.registeredValues( script["box"]["in"] ) )
		self.assertIn( "plugAlgoTest:a", Gaffer.Metadata.registeredValues( script["box"]["in"], persistentOnly = True ) )

		# After serialisation and loading, everything should look the same.

		script2 = Gaffer.ScriptNode()
		script2.execute( script.serialise() )

		self.assertEqual( Gaffer.Metadata.value( script2["box"]["n"]["in"], "plugAlgoTest:a" ), "a" )
		self.assertIn( "plugAlgoTest:a", Gaffer.Metadata.registeredValues( script2["box"]["n"]["in"] ) )
		self.assertNotIn( "plugAlgoTest:a", Gaffer.Metadata.registeredValues( script2["box"]["n"]["in"], persistentOnly = True ) )
		self.assertIn( "plugAlgoTest:a", Gaffer.Metadata.registeredValues( script2["box"]["in"] ) )
		self.assertIn( "plugAlgoTest:a", Gaffer.Metadata.registeredValues( script2["box"]["in"], persistentOnly = True ) )

	def testPromotableMetadata( self ) :

		box = Gaffer.Box()
		box["n"] = Gaffer.Node()
		box["n"]["user"]["p"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		Gaffer.Metadata.registerValue( box["n"]["user"]["p"], "a", 10 )
		Gaffer.Metadata.registerValue( box["n"]["user"]["p"], "b", 20 )
		Gaffer.Metadata.registerValue( box["n"]["user"]["p"], "b:promotable", False )
		Gaffer.Metadata.registerValue( box["n"]["user"]["p"], "c", 30 )
		Gaffer.Metadata.registerValue( box["n"]["user"]["p"], "c:promotable", True )

		p = Gaffer.PlugAlgo.promote( box["n"]["user"]["p"] )
		self.assertEqual( Gaffer.Metadata.value( p, "a" ), 10 )
		self.assertIsNone( Gaffer.Metadata.value( p, "b" ) )
		self.assertIsNone( Gaffer.Metadata.value( p, "b:promotable" ) )
		self.assertNotIn( "b", Gaffer.Metadata.registeredValues( p ) )
		self.assertNotIn( "b:promotable", Gaffer.Metadata.registeredValues( p ) )
		self.assertEqual( Gaffer.Metadata.value( p, "c" ), 30 )
		self.assertIsNone( Gaffer.Metadata.value( p, "b:promotable" ) )
		self.assertNotIn( "c:promotable", Gaffer.Metadata.registeredValues( p ) )

	def testGetValueFromNameValuePlug( self ) :

		withEnabled = Gaffer.NameValuePlug( "test", 10, defaultEnabled = True )
		withoutEnabled = Gaffer.NameValuePlug( "test", 20 )

		self.assertEqual(
			Gaffer.PlugAlgo.getValueAsData( withEnabled ),
			IECore.CompoundData( { "name" : "test", "value" : 10, "enabled" : True } )
		)

		self.assertEqual(
			Gaffer.PlugAlgo.getValueAsData( withoutEnabled ),
			IECore.CompoundData( { "name" : "test", "value" : 20 } )
		)

	def testGetValueAsData( self ) :

		n = Gaffer.Node()
		n.addChild( Gaffer.FloatPlug( "floatPlug", defaultValue = 2.0 ) )
		n.addChild(
			Gaffer.V3fPlug(
				"v3fPlug",
				defaultValue = imath.V3f( 1.0, 2.0, 3.0 ),
				interpretation = IECore.GeometricData.Interpretation.Point
			)
		)
		n.addChild( Gaffer.FloatVectorDataPlug( "floatVectorPlug", defaultValue = IECore.FloatVectorData( [ 1.0, 2.0, 3.0 ] ) ) )
		n.addChild( Gaffer.Box2iPlug( "box2iPlug", defaultValue = imath.Box2i( imath.V2i( 1.0 ), imath.V2i( 2.0 ) ) ) )
		s = Gaffer.SplineDefinitionff(
			(
				( 0, 0 ),
				( 0.2, 0.3 ),
				( 0.4, 0.9 ),
				( 1, 1 ),
			),
			Gaffer.SplineDefinitionInterpolation.CatmullRom
		)
		n.addChild( Gaffer.SplineffPlug( "splinePlug", defaultValue = s ) )

		self.assertEqual( Gaffer.PlugAlgo.getValueAsData( n["floatPlug"] ), IECore.FloatData( 2.0 ) )
		self.assertEqual(
			Gaffer.PlugAlgo.getValueAsData( n["v3fPlug"] ),
			IECore.V3fData( imath.V3f( 1, 2, 3 ), IECore.GeometricData.Interpretation.Point )
		)
		self.assertEqual( Gaffer.PlugAlgo.getValueAsData( n["floatVectorPlug"] ), IECore.FloatVectorData( [ 1.0, 2.0, 3.0 ] ) )
		self.assertEqual( Gaffer.PlugAlgo.getValueAsData( n["box2iPlug"] ), IECore.Box2iData( imath.Box2i( imath.V2i( 1.0 ), imath.V2i( 2.0 ) ) ) )
		self.assertEqual( Gaffer.PlugAlgo.getValueAsData( n["splinePlug"] ), IECore.SplineffData( s.spline() ) )


	def testSetValueFromData( self ) :

		n = Gaffer.Node()
		n.addChild( Gaffer.FloatPlug( "floatPlug" ) )
		n.addChild( Gaffer.Color3fPlug( "color3fPlug" ) )
		n.addChild( Gaffer.Color4fPlug( "color4fPlug" ) )
		n.addChild( Gaffer.V3fPlug( "v3fPlug" ) )
		n.addChild( Gaffer.Box2iPlug( "box2iPlug" ) )
		n.addChild( Gaffer.Box3fPlug( "box3fPlug" ) )

		r = Gaffer.PlugAlgo.setValueFromData( n["floatPlug"], IECore.FloatData( 5.0 ) )
		self.assertTrue( r )
		self.assertEqual( n["floatPlug"].getValue(), 5.0 )

		r = Gaffer.PlugAlgo.setValueFromData(
			n["color3fPlug"],
			IECore.Color3fData( imath.Color3f( 1.0, 2.0, 3.0 ) )
		)
		self.assertTrue( r )
		self.assertEqual( n["color3fPlug"].getValue(), imath.Color3f( 1.0, 2.0, 3.0 ) )


		r = Gaffer.PlugAlgo.setValueFromData(
			n["color4fPlug"],
			IECore.Color4fData( imath.Color4f( 1.0, 2.0, 3.0, 4.0) ),
		)
		self.assertTrue( r )
		self.assertEqual( n["color4fPlug"].getValue(), imath.Color4f( 1.0, 2.0, 3.0, 4.0 ) )

		r = Gaffer.PlugAlgo.setValueFromData(
			n["color4fPlug"],
			IECore.Color3fData( imath.Color3f( 5.0, 6.0, 7.0) )
		)
		self.assertTrue( r )
		self.assertEqual( n["color4fPlug"].getValue(), imath.Color4f( 5.0, 6.0, 7.0, 1.0 ) )

		r = Gaffer.PlugAlgo.setValueFromData(
			n["color4fPlug"],
			IECore.FloatData( 8.0 )
		)
		self.assertTrue( r )
		self.assertEqual( n["color4fPlug"].getValue(), imath.Color4f( 8.0, 8.0, 8.0, 1.0 ) )

		r = Gaffer.PlugAlgo.setValueFromData(
			n["v3fPlug"],
			IECore.V2fData( imath.V2f( 1.0, 2.0 ) ),
		)
		self.assertTrue( r )
		self.assertEqual( n["v3fPlug"].getValue(), imath.V3f( 1.0, 2.0, 0.0 ) )

		r = Gaffer.PlugAlgo.setValueFromData(
			n["box2iPlug"],
			IECore.Box2iData( imath.Box2i( imath.V2i (1.0 ), imath.V2i( 2.0 ) ) )
		)
		self.assertTrue( r )
		self.assertEqual( n["box2iPlug"].getValue(), imath.Box2i( imath.V2i( 1.0 ), imath.V2i( 2.0 ) ) )

		r = Gaffer.PlugAlgo.setValueFromData(
			n["box3fPlug"],
			IECore.Box3fData( imath.Box3f( imath.V3f( 3.0 ), imath.V3f( 7.0 ) ) )
		)
		self.assertTrue( r )
		self.assertEqual( n["box3fPlug"].getValue(), imath.Box3f( imath.V3f( 3.0 ), imath.V3f( 7.0 ) ) )

		r = Gaffer.PlugAlgo.setValueFromData(
			n["floatPlug"],
			IECore.V3fData( imath.V3f( 1.0, 2.0, 3.0 ) )
		)
		self.assertFalse( r )

	def testSetLeafValueFromData( self ) :

		n = Gaffer.Node()
		n.addChild( Gaffer.FloatPlug( "floatPlug" ) )
		n.addChild( Gaffer.Color3fPlug( "color3fPlug" ) )
		n.addChild( Gaffer.Color4fPlug( "color4fPlug" ) )
		n.addChild( Gaffer.Box2iPlug( "box2iPlug" ) )

		r = Gaffer.PlugAlgo.setValueFromData(
			n["color3fPlug"],
			n["color3fPlug"]["g"],
			IECore.Color3fData( imath.Color3f( 1.0, 2.0, 3.0 ) ),
		)
		self.assertTrue( r )
		self.assertEqual( n["color3fPlug"].getValue(), imath.Color3f( 0.0, 2.0, 0.0 ) )

		r = Gaffer.PlugAlgo.setValueFromData(
			n["color4fPlug"],
			n["color4fPlug"]["a"],
			IECore.Color3fData( imath.Color3f( 4.0, 5.0, 6.0 ) )
		)
		self.assertTrue( r )
		self.assertEqual( n["color4fPlug"].getValue(), imath.Color4f( 0.0, 0.0, 0.0, 1.0 ) )

		r = Gaffer.PlugAlgo.setValueFromData(
			n["box2iPlug"],
			n["box2iPlug"]["min"]["x"],
			IECore.Box2iData( imath.Box2i( imath.V2i( 1.0 ), imath.V2i( 2.0 ) ) )
		)
		self.assertTrue( r )
		defaultBox2i = imath.Box2i()
		self.assertEqual(
			n["box2iPlug"].getValue(),
			imath.Box2i(
				imath.V2i( 1.0, defaultBox2i.min().y ),
				imath.V2i( defaultBox2i.max().x, defaultBox2i.max().y )
			)
		)

		r = Gaffer.PlugAlgo.setValueFromData( n["floatPlug"], n["floatPlug"], IECore.FloatData( 1.0 ) )
		self.assertTrue( r )
		self.assertEqual( n["floatPlug"].getValue(), 1.0 )

		self.assertRaises(
			RuntimeError,
			Gaffer.PlugAlgo.setValueFromData,
			n["box2iPlug"],
			n["box2iPlug"]["min"],
			IECore.V2iData( imath.V2i( 1.0 ) )
		)

	def testCanSetPlugFromValue( self ) :
		compatiblePlugs = [
			Gaffer.BoolPlug(),
			Gaffer.FloatPlug(),
			Gaffer.IntPlug(),
			Gaffer.BoolVectorDataPlug( "bv", Gaffer.Plug.Direction.In, IECore.BoolVectorData( [] ) ),
			Gaffer.FloatVectorDataPlug( "fv", Gaffer.Plug.Direction.In, IECore.FloatVectorData( [] ) ),
			Gaffer.IntVectorDataPlug( "iv", Gaffer.Plug.Direction.In, IECore.IntVectorData( [] ) ),
			Gaffer.StringPlug(),
			Gaffer.StringVectorDataPlug( "sv", Gaffer.Plug.Direction.In, IECore.StringVectorData( [] ) ),
			Gaffer.InternedStringVectorDataPlug( "isv", Gaffer.Plug.Direction.In, IECore.InternedStringVectorData( [] ) ),
			Gaffer.Color3fPlug(),
			Gaffer.Color4fPlug(),
			Gaffer.V3fPlug(),
			Gaffer.V3iPlug(),
			Gaffer.V2fPlug(),
			Gaffer.V2iPlug(),
			Gaffer.Box3fPlug(),
			Gaffer.Box3iPlug(),
			Gaffer.Box2fPlug(),
			Gaffer.Box2iPlug(),
		]

		for p in compatiblePlugs :
			self.assertTrue( Gaffer.PlugAlgo.canSetValueFromData( p ) )

		self.assertFalse( Gaffer.PlugAlgo.canSetValueFromData( Gaffer.NameValuePlug() ) )


if __name__ == "__main__":
	unittest.main()
