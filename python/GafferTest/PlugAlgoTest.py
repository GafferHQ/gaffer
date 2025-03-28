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
		Gaffer.Metadata.deregisterValue( Gaffer.IntPlug, "plugAlgoTest:b" )

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
		self.assertTrue( "testPersistence" not in Gaffer.Metadata.registeredValues( p, Gaffer.Metadata.RegistrationTypes.InstancePersistent ) )

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
		self.assertNotIn( "plugAlgoTest:a", Gaffer.Metadata.registeredValues( script["box"]["n"]["in"], Gaffer.Metadata.RegistrationTypes.InstancePersistent ) )

		# And if we promote up one more level, we want that to work, and we want the
		# new metadata to be persistent so that it will be serialised and restored.

		Gaffer.PlugAlgo.promote( script["box"]["n"]["in"] )
		self.assertIn( "plugAlgoTest:a", Gaffer.Metadata.registeredValues( script["box"]["in"] ) )
		self.assertIn( "plugAlgoTest:a", Gaffer.Metadata.registeredValues( script["box"]["in"], Gaffer.Metadata.RegistrationTypes.InstancePersistent ) )

		# After serialisation and loading, everything should look the same.

		script2 = Gaffer.ScriptNode()
		script2.execute( script.serialise() )

		self.assertEqual( Gaffer.Metadata.value( script2["box"]["n"]["in"], "plugAlgoTest:a" ), "a" )
		self.assertIn( "plugAlgoTest:a", Gaffer.Metadata.registeredValues( script2["box"]["n"]["in"] ) )
		self.assertNotIn( "plugAlgoTest:a", Gaffer.Metadata.registeredValues( script2["box"]["n"]["in"], Gaffer.Metadata.RegistrationTypes.InstancePersistent ) )
		self.assertIn( "plugAlgoTest:a", Gaffer.Metadata.registeredValues( script2["box"]["in"] ) )
		self.assertIn( "plugAlgoTest:a", Gaffer.Metadata.registeredValues( script2["box"]["in"], Gaffer.Metadata.RegistrationTypes.InstancePersistent ) )

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

	def testPromoteDoesntMakeRedundantMetadata( self ) :

		# Make plug with metadata registered statically against its type.

		Gaffer.Metadata.registerValue( Gaffer.IntPlug, "plugAlgoTest:b", "testValueB" )
		self.addCleanup( Gaffer.Metadata.deregisterValue, Gaffer.IntPlug, "plugAlgoTest:b" )

		box = Gaffer.Box()
		box["node"] = Gaffer.Node()
		box["node"]["plug"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		self.assertEqual( Gaffer.Metadata.value( box["node"]["plug"], "plugAlgoTest:b" ), "testValueB" )

		# When promoting, we shouldn't need to make a per-instance copy of the
		# static metadata, because the static registration also applies to the
		# promoted plug.

		promoted = Gaffer.PlugAlgo.promote( box["node"]["plug"] )
		self.assertTrue( promoted.node().isSame( box ) )
		self.assertEqual( Gaffer.Metadata.value( promoted, "plugAlgoTest:b" ), "testValueB" )
		self.assertIsNone( Gaffer.Metadata.value( promoted, "plugAlgoTest:b", Gaffer.Metadata.RegistrationTypes.Instance ) )

		box.removeChild( promoted )
		Gaffer.Metadata.registerValue( box["node"]["plug"], "plugAlgoTest:b", "testValueC" )
		self.assertEqual( Gaffer.Metadata.value( box["node"]["plug"], "plugAlgoTest:b" ), "testValueC" )

		# But if the plug to be promoted has a unique per-instance value, then
		# we'll need to promote that explicitly.

		promoted = Gaffer.PlugAlgo.promote( box["node"]["plug"] )
		self.assertTrue( promoted.node().isSame( box ) )
		self.assertEqual( Gaffer.Metadata.value( promoted, "plugAlgoTest:b" ), "testValueC" )
		self.assertEqual( Gaffer.Metadata.value( promoted, "plugAlgoTest:b", Gaffer.Metadata.RegistrationTypes.Instance ), "testValueC" )

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

	def testGetValueFromOptionalValuePlug( self ) :

		enabled = Gaffer.OptionalValuePlug(
			"test",
			Gaffer.IntPlug( "test", Gaffer.Plug.Direction.In, 10 ),
			enabledPlugDefaultValue = True
		)
		disabled = Gaffer.OptionalValuePlug(
			"test",
			Gaffer.IntPlug( "test", Gaffer.Plug.Direction.In, 20 ),
			enabledPlugDefaultValue = False
		)

		self.assertEqual(
			Gaffer.PlugAlgo.getValueAsData( enabled ),
			IECore.CompoundData( { "value" : 10, "enabled" : True } )
		)

		self.assertEqual(
			Gaffer.PlugAlgo.getValueAsData( disabled ),
			IECore.CompoundData( { "value" : 20, "enabled" : False } )
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
		n.addChild( Gaffer.PathMatcherDataPlug( "pathMatcherPlug", defaultValue = IECore.PathMatcherData( IECore.PathMatcher( [ "/test/path", "/test/path2" ] ) ) ) )

		self.assertEqual( Gaffer.PlugAlgo.getValueAsData( n["floatPlug"] ), IECore.FloatData( 2.0 ) )
		self.assertEqual(
			Gaffer.PlugAlgo.getValueAsData( n["v3fPlug"] ),
			IECore.V3fData( imath.V3f( 1, 2, 3 ), IECore.GeometricData.Interpretation.Point )
		)
		self.assertEqual( Gaffer.PlugAlgo.getValueAsData( n["floatVectorPlug"] ), IECore.FloatVectorData( [ 1.0, 2.0, 3.0 ] ) )
		self.assertEqual( Gaffer.PlugAlgo.getValueAsData( n["box2iPlug"] ), IECore.Box2iData( imath.Box2i( imath.V2i( 1.0 ), imath.V2i( 2.0 ) ) ) )
		self.assertEqual( Gaffer.PlugAlgo.getValueAsData( n["splinePlug"] ), IECore.SplineffData( s.spline() ) )
		self.assertEqual( Gaffer.PlugAlgo.getValueAsData( n["pathMatcherPlug"] ), IECore.PathMatcherData( IECore.PathMatcher( [ "/test/path", "/test/path2" ] ) ) )


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

	def testSetValueOrAddKeyFromData( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()

		for data in [
			IECore.HalfData( 2.5 ),
			IECore.FloatData( 0.25 ),
			IECore.DoubleData( 25.5 ),
			IECore.CharData( "a" ),
			IECore.UCharData( 11 ),
			IECore.ShortData( -101 ),
			IECore.UShortData( 102 ),
			IECore.UIntData( 405 ),
			IECore.Int64Data( -1001 ),
			IECore.UInt64Data( 1002 ),
			IECore.BoolData( True )
		] :

			for plugType in [
				Gaffer.IntPlug,
				Gaffer.FloatPlug,
				Gaffer.BoolPlug,
			] :

				with self.subTest( data = data, plugType = plugType ) :

					plug = plugType()
					s["n"].addChild( plug )

					self.assertTrue( Gaffer.PlugAlgo.canSetValueFromData( plug, data ) )

					self.assertTrue( Gaffer.PlugAlgo.setValueOrAddKeyFromData( plug, 1002, data ) )
					self.assertFalse( Gaffer.Animation.isAnimated( plug ) )

					value = ord( data.value ) if isinstance( data, IECore.CharData ) else data.value
					self.assertEqual( plug.getValue(), plugType.ValueType( value ) )

					curve = Gaffer.Animation.acquire( plug )
					curve.addKey( Gaffer.Animation.Key( 0, 1001 ) )
					self.assertFalse( curve.hasKey( 1002 ) )

					self.assertTrue( Gaffer.PlugAlgo.setValueOrAddKeyFromData( plug, 1002, data ) )
					self.assertTrue( curve.hasKey( 1002 ) )
					self.assertEqual( curve.getKey( 1002 ).getValue(), Gaffer.FloatPlug.ValueType( value ) )

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

	def testCanSetPlugFromValueWithType( self ) :

		n = Gaffer.Node()
		n.addChild( Gaffer.BoolPlug( "boolPlug" ) )
		n.addChild( Gaffer.IntPlug( "intPlug" ) )
		n.addChild( Gaffer.FloatPlug( "floatPlug" ) )
		n.addChild( Gaffer.Color3fPlug( "color3fPlug" ) )
		n.addChild( Gaffer.Color4fPlug( "color4fPlug" ) )
		n.addChild( Gaffer.V3fPlug( "v3fPlug" ) )
		n.addChild( Gaffer.V2iPlug( "v2iPlug" ) )
		n.addChild( Gaffer.Box2iPlug( "box2iPlug" ) )
		n.addChild( Gaffer.Box2fPlug( "box2fPlug" ) )
		n.addChild( Gaffer.StringPlug( "stringPlug" ) )
		n.addChild( Gaffer.BoolVectorDataPlug( "boolVectorPlug", defaultValue = IECore.BoolVectorData() ) )
		n.addChild( Gaffer.IntVectorDataPlug( "intVectorPlug", defaultValue = IECore.IntVectorData() ) )
		n.addChild( Gaffer.StringVectorDataPlug( "stringVectorPlug", defaultValue = IECore.StringVectorData() ) )

		testData = [
			IECore.BoolData( True ),
			IECore.IntData( 42 ),
			IECore.FloatData( 5.0 ),
			IECore.Color3fData( imath.Color3f( 1.0, 2.0, 3.0 ) ),
			IECore.Color4fData( imath.Color4f( 1.0, 2.0, 3.0, 4.0) ),
			IECore.V2fData( imath.V2f( 1.0, 2.0 ) ),
			IECore.V3iData( imath.V3i( 3, 4, 5 ) ),
			IECore.Box2iData( imath.Box2i( imath.V2i (1.0 ), imath.V2i( 2.0 ) ) ),
			IECore.StringData( "foo" ),
			IECore.InternedStringData( "bar" ),
			IECore.BoolVectorData( [ True, False, False ] ),
			IECore.IntVectorData( [ 7, 8, 9 ] ),
			IECore.FloatVectorData( [ 7.0, 8.0, 9.0, 10.0 ] ),
			]

		# Make sure canSet doesn't accidentally actually change something
		for data in testData:
			for plug in n.children():
				if plug == n["user"]:
					continue
				Gaffer.PlugAlgo.canSetValueFromData( plug, data )
				self.assertEqual( plug.getValue(), plug.defaultValue() )

		# Make sure canSet matches set setValue
		for data in testData:
			for plug in n.children():
				if plug == n["user"]:
					continue
				self.assertEqual(
					Gaffer.PlugAlgo.canSetValueFromData( plug, data ),
					Gaffer.PlugAlgo.setValueFromData( plug, data )
				)

	def testDataConversionsForAllTypes( self ) :

		for plugType in Gaffer.ValuePlug.__subclasses__() :

			valueType = getattr( plugType, "ValueType", None )
			if valueType is None :
				continue

			if issubclass( valueType, IECore.Data ) :
				dataType = valueType
			elif valueType is float :
				dataType = IECore.FloatData
			else :
				try :
					dataType = IECore.DataTraits.dataTypeFromElementType( valueType )
				except TypeError :
					continue

			with self.subTest( plugType = plugType ) :

				plug = plugType()
				data = dataType()
				self.assertTrue( Gaffer.PlugAlgo.canSetValueFromData( plug, None ) )
				self.assertTrue( Gaffer.PlugAlgo.canSetValueFromData( plug, data ) )
				self.assertTrue( Gaffer.PlugAlgo.setValueFromData( plug, data ) )
				if issubclass( valueType, IECore.Data ) :
					self.assertEqual( plug.getValue(), data )
				else :
					self.assertEqual( plug.getValue(), data.value )
				self.assertEqual( Gaffer.PlugAlgo.getValueAsData( plug ), data )

	def testSetNumericValueFromVectorData( self ) :

		for plugType in Gaffer.FloatPlug, Gaffer.IntPlug, Gaffer.BoolPlug :
			plug = plugType()
			for dataType in [
				IECore.HalfVectorData,
				IECore.FloatVectorData,
				IECore.DoubleVectorData,
				IECore.UCharVectorData,
				IECore.ShortVectorData,
				IECore.UShortVectorData,
				IECore.IntVectorData,
				IECore.UIntVectorData,
				IECore.Int64VectorData,
				IECore.UInt64VectorData,
				IECore.BoolVectorData,
			] :
				with self.subTest( plugType = plugType, dataType = dataType ) :
					for value in ( 0, 1 ) :
						data = dataType()
						# Array length 0, can't set.
						self.assertFalse( Gaffer.PlugAlgo.canSetValueFromData( plug, data ) )
						plug.setToDefault()
						self.assertFalse( Gaffer.PlugAlgo.setValueFromData( plug, data ) )
						self.assertTrue( plug.isSetToDefault() )
						# Array length 1, can set.
						data.append( value )
						self.assertTrue( Gaffer.PlugAlgo.canSetValueFromData( plug, data ) )
						self.assertTrue( Gaffer.PlugAlgo.setValueFromData( plug, data ) )
						self.assertEqual( plug.getValue(), value )
						# Array length > 1, can't set.
						data.append( value )
						self.assertFalse( Gaffer.PlugAlgo.canSetValueFromData( plug, data ) )
						plug.setToDefault()
						self.assertFalse( Gaffer.PlugAlgo.setValueFromData( plug, data ) )
						self.assertTrue( plug.isSetToDefault() )

	def testSetCompoundNumericValueFromVectorData( self ) :

		for plugType in [
			Gaffer.Color3fPlug, Gaffer.Color4fPlug,
			Gaffer.V3fPlug, Gaffer.V3iPlug,
			Gaffer.V2fPlug, Gaffer.V2iPlug
		] :

			plug = plugType()
			for dataType in [
				IECore.Color3fVectorData,
				IECore.Color4fVectorData,
				IECore.V3fVectorData,
				IECore.V3iVectorData,
				IECore.V2fVectorData,
				IECore.V2iVectorData,
				IECore.FloatVectorData,
				IECore.IntVectorData,
				IECore.BoolVectorData,
			] :
				with self.subTest( plugType = plugType, dataType = dataType ) :

					data = dataType()

					# Array length 0, can't set.

					self.assertFalse( Gaffer.PlugAlgo.canSetValueFromData( plug, data ) )
					plug.setToDefault()
					self.assertFalse( Gaffer.PlugAlgo.setValueFromData( plug, data ) )
					self.assertTrue( plug.isSetToDefault() )
					for childPlug in Gaffer.Plug.Range( plug ) :
						self.assertFalse( Gaffer.PlugAlgo.setValueFromData( plug, childPlug, data ) )
					self.assertTrue( plug.isSetToDefault() )

					# Array length 1, can set.

					data.resize( 1 )
					value = data[0]
					if hasattr( value, "dimensions" ) :
						# e.g. `V3f( 1, 2, 3 )`
						for i in range( 0, value.dimensions() ) :
							value[i] = i + 1
					else :
						# e.g `2`, `2.0`, or `True`
						value = type( value )( 2 )
					data[0] = value

					self.assertTrue( Gaffer.PlugAlgo.canSetValueFromData( plug, data ) )
					self.assertTrue( Gaffer.PlugAlgo.setValueFromData( plug, data ) )
					for i, childPlug in enumerate( plug ) :
						if hasattr( value, "dimensions" ) :
							if i < value.dimensions() :
								self.assertEqual( childPlug.getValue(), value[i] )
							else :
								self.assertEqual( childPlug.getValue(), 1 if i == 3 else 0 )
						else :
							self.assertEqual( childPlug.getValue(), 1 if i == 3 else value )

					# And can also set a component at a time.

					plug.setToDefault()
					for i, childPlug in enumerate( plug ) :
						Gaffer.PlugAlgo.setValueFromData( plug, childPlug, data )
						if hasattr( value, "dimensions" ) :
							if i < value.dimensions() :
								self.assertEqual( childPlug.getValue(), value[i] )
							else :
								self.assertEqual( childPlug.getValue(), 1 if i == 3 else 0 )
						else :
							self.assertEqual( childPlug.getValue(), 1 if i == 3 else value )

					# Array length > 1, can't set.

					data.append( data[0] )

					self.assertFalse( Gaffer.PlugAlgo.canSetValueFromData( plug, data ) )
					plug.setToDefault()
					self.assertFalse( Gaffer.PlugAlgo.setValueFromData( plug, data ) )
					self.assertTrue( plug.isSetToDefault() )
					for childPlug in plug :
						self.assertFalse( Gaffer.PlugAlgo.setValueFromData( plug, childPlug, data ) )
						self.assertTrue( childPlug.isSetToDefault() )
					self.assertTrue( plug.isSetToDefault() )

	def testSetTypedValueFromVectorData( self ) :

		for plugType, value in [
			( Gaffer.StringPlug, "test" ),
			( Gaffer.StringPlug, IECore.InternedString( "test" ) ),
			( Gaffer.M33fPlug, imath.M33f( 1 ) ),
			( Gaffer.M44fPlug, imath.M44f( 1 ) ),
			( Gaffer.AtomicBox2fPlug, imath.Box2f( imath.V2f( 0 ), imath.V2f( 1 ) ) ),
			( Gaffer.AtomicBox3fPlug, imath.Box3f( imath.V3f( 0 ), imath.V3f( 1 ) ) ),
			( Gaffer.AtomicBox2iPlug, imath.Box2i( imath.V2i( 0 ), imath.V2i( 1 ) ) ),
		] :

			with self.subTest( plugType = plugType, value = value ) :

				plug = plugType()
				data = IECore.DataTraits.dataFromElement( [ value ] )
				self.assertEqual( len( data ), 1 )

				# Array length 1, can set

				self.assertTrue( Gaffer.PlugAlgo.canSetValueFromData( plug, data ) )
				self.assertTrue( Gaffer.PlugAlgo.setValueFromData( plug, data ) )
				self.assertEqual( plug.getValue(), value )
				self.assertFalse( plug.isSetToDefault() )

				# Array length 2, can't set unless setting StringVectorData on StringPlug

				canSetArray = isinstance( data, IECore.StringVectorData ) and plugType == Gaffer.StringPlug
				data.append( data[0] )
				plug.setToDefault()
				self.assertEqual( Gaffer.PlugAlgo.canSetValueFromData( plug, data ), canSetArray )
				self.assertEqual( Gaffer.PlugAlgo.setValueFromData( plug, data ), canSetArray )
				self.assertNotEqual( plug.isSetToDefault(), canSetArray )

				# Array length 0, can't set unless setting StringVectorData on a StringPlug

				data.resize( 0 )
				plug.setToDefault()
				self.assertEqual( Gaffer.PlugAlgo.canSetValueFromData( plug, data ), canSetArray )
				self.assertEqual( Gaffer.PlugAlgo.setValueFromData( plug, data ), canSetArray )
				self.assertTrue( plug.isSetToDefault() )

	def testSetBoxValueFromVectorData( self ) :

		for plugType in [
			Gaffer.Box2fPlug, Gaffer.Box3fPlug,
			Gaffer.Box2iPlug, Gaffer.Box3iPlug,
		] :

			with self.subTest( plugType = plugType ) :

				plug = plugType()

				minValue = plugType.PointType()
				maxValue = plugType.PointType()
				for i in range( 0, minValue.dimensions() ) :
					minValue[i] = i
					maxValue[i] = i + 1
				value = plugType.ValueType( minValue, maxValue )
				data = IECore.DataTraits.dataFromElement( [ value ] )

				# Array length 1, can set

				self.assertTrue( Gaffer.PlugAlgo.canSetValueFromData( plug, data ) )
				self.assertTrue( plug.isSetToDefault() )
				self.assertTrue( Gaffer.PlugAlgo.setValueFromData( plug, data ) )
				self.assertEqual( plug.getValue(), value )
				self.assertFalse( plug.isSetToDefault() )

				# And can set individual children

				plug.setToDefault()
				for childPlug in plug :
					for componentPlug in childPlug :
						self.assertTrue( Gaffer.PlugAlgo.setValueFromData( plug, data ) )
				self.assertEqual( plug.getValue(), value )
				self.assertFalse( plug.isSetToDefault() )

				# Array length 2, can't set

				data.append( data[0] )
				plug.setToDefault()
				self.assertFalse( Gaffer.PlugAlgo.canSetValueFromData( plug, data ) )
				self.assertFalse( Gaffer.PlugAlgo.setValueFromData( plug, data ) )
				for childPlug in plug :
					for componentPlug in childPlug :
						self.assertFalse( Gaffer.PlugAlgo.setValueFromData( plug, data ) )
				self.assertTrue( plug.isSetToDefault() )

				# Array length 0, can't set

				data.resize( 0 )
				self.assertFalse( Gaffer.PlugAlgo.canSetValueFromData( plug, data ) )
				self.assertFalse( Gaffer.PlugAlgo.setValueFromData( plug, data ) )
				for childPlug in plug :
					for componentPlug in childPlug :
						self.assertFalse( Gaffer.PlugAlgo.setValueFromData( plug, data ) )
				self.assertTrue( plug.isSetToDefault() )

	def testSetStringValueFromStringVectorData( self ) :

		plug = Gaffer.StringPlug()

		for data in [
			IECore.StringVectorData( [ "a", "b", "c" ] ),
			IECore.StringVectorData( [ "a" ] ),
			IECore.StringVectorData()
		] :

			self.assertTrue( Gaffer.PlugAlgo.canSetValueFromData( plug, data ) )
			self.assertTrue( Gaffer.PlugAlgo.setValueFromData( plug, data ) )
			self.assertEqual( plug.getValue(), " ".join( data ) )
			self.assertEqual( plug.isSetToDefault(), len( data ) == 0 )

	def testSetStringVectorValueFromStringData( self ) :

		plug = Gaffer.StringVectorDataPlug()

		for data in [
			IECore.StringData( "a b c" ),
			IECore.StringData( "a" ),
			IECore.StringData()
		] :

			self.assertTrue( Gaffer.PlugAlgo.canSetValueFromData( plug, data ) )
			self.assertTrue( Gaffer.PlugAlgo.setValueFromData( plug, data ) )
			self.assertEqual( plug.getValue(), IECore.StringVectorData( data.value.split( " " ) ) if data.value != "" else IECore.StringVectorData() )
			self.assertEqual( plug.isSetToDefault(), data.value == "" )

	def testDependsOnCompute( self ) :

		add = GafferTest.AddNode()
		self.assertFalse( Gaffer.PlugAlgo.dependsOnCompute( add["op1"] ) )
		self.assertFalse( Gaffer.PlugAlgo.dependsOnCompute( add["op2"] ) )
		self.assertTrue( Gaffer.PlugAlgo.dependsOnCompute( add["sum"] ) )

		node = Gaffer.Node()
		node["user"]["p"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		self.assertFalse( Gaffer.PlugAlgo.dependsOnCompute( node["user"]["p"] ) )
		node["user"]["p"].setInput( add["op1"] )
		self.assertFalse( Gaffer.PlugAlgo.dependsOnCompute( node["user"]["p"] ) )
		node["user"]["p"].setInput( add["sum"] )
		self.assertTrue( Gaffer.PlugAlgo.dependsOnCompute( node["user"]["p"] ) )

		stringNode = GafferTest.StringInOutNode()
		self.assertFalse( Gaffer.PlugAlgo.dependsOnCompute( stringNode["in"] ) )
		self.assertTrue( Gaffer.PlugAlgo.dependsOnCompute( stringNode["out"] ) )

		# Although string substitutions may result in a value that varies with
		# context, they are not implemented via a compute.
		stringNode["in"].setValue( "${frame}" )
		self.assertFalse( Gaffer.PlugAlgo.dependsOnCompute( stringNode["in"] ) )

		# If a child of a compound plug depends on a compute, then so does
		# the parent as far as we're concerned.
		node["user"]["v"] = Gaffer.V3fPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		self.assertFalse( Gaffer.PlugAlgo.dependsOnCompute( node["user"]["v"] ) )
		node["user"]["v"]["x"].setInput( add["op1"] )
		self.assertFalse( Gaffer.PlugAlgo.dependsOnCompute( node["user"]["v"] ) )
		node["user"]["v"]["y"].setInput( add["sum"] )
		self.assertTrue( Gaffer.PlugAlgo.dependsOnCompute( node["user"]["v"] ) )

	def testFindDestination( self ) :

		# Promote a plug through two levels of nesting.

		outerBox = Gaffer.Box()
		outerBox["innerBox"] = Gaffer.Box()
		outerBox["innerBox"]["node"] = GafferTest.AddNode()
		innerPlug = Gaffer.PlugAlgo.promote( outerBox["innerBox"]["node"]["op1"] )
		outerPlug = Gaffer.PlugAlgo.promote( innerPlug )

		# Find the destination plug.

		self.assertEqual(
			Gaffer.PlugAlgo.findDestination( outerPlug, lambda plug : plug if isinstance( plug.node(), GafferTest.AddNode ) else None ),
			outerBox["innerBox"]["node"]["op1"]
		)

		# Find the destination node.

		self.assertEqual(
			Gaffer.PlugAlgo.findDestination( outerPlug, lambda plug : plug.node() if isinstance( plug.node(), GafferTest.AddNode ) else None ),
			outerBox["innerBox"]["node"]
		)

		# Try to find a destination which doesn't exist.

		self.assertIsNone(
			Gaffer.PlugAlgo.findDestination( outerPlug, lambda plug : plug if isinstance( plug, Gaffer.StringPlug ) else None ),
		)

		# Plugs should be visited before their outputs.

		self.assertEqual(
			Gaffer.PlugAlgo.findDestination( outerPlug, lambda plug : plug ),
			outerPlug
		)

		self.assertEqual(
			Gaffer.PlugAlgo.findDestination( outerPlug, lambda plug : plug if plug.getInput() else None ),
			innerPlug
		)

		# Spreadsheets should be taken into account.

		spreadsheet = Gaffer.Spreadsheet()
		spreadsheet["rows"].addColumn( Gaffer.IntPlug( "test" ) )
		outerPlug.setInput( spreadsheet["out"]["test"] )

		self.assertEqual(
			Gaffer.PlugAlgo.findDestination(
				spreadsheet["rows"][0]["cells"]["test"]["value"],
				lambda plug : plug if isinstance( plug.node(), GafferTest.AddNode ) else None,
			),
			outerBox["innerBox"]["node"]["op1"]
		)

	def testFindDestinationSupportsSpreadsheetsWithCompoundPlugs( self ) :

		spreadsheet = Gaffer.Spreadsheet()
		spreadsheet["rows"].addColumn( Gaffer.V2iPlug( "test" ) )

		self.assertEqual(
			Gaffer.PlugAlgo.findDestination(
				spreadsheet["rows"][0]["cells"]["test"]["value"]["x"],
				lambda plug : plug if plug.direction() == Gaffer.Plug.Direction.Out else None,
			),
			spreadsheet["out"]["test"]["x"]
		)

	def testFindDestinationIgnoresSpreadsheetCellEnabled( self ) :

		spreadsheet = Gaffer.Spreadsheet()
		spreadsheet["rows"].addColumn( Gaffer.FloatPlug( "test" ) )

		self.assertIsNone(
			Gaffer.PlugAlgo.findDestination(
				spreadsheet["rows"][0]["cells"]["test"]["enabled"],
				lambda plug : plug if plug.direction() == Gaffer.Plug.Direction.Out else None,
			)
		)

	def testFindDestinationFromNone( self ) :

		self.assertIsNone(
			Gaffer.PlugAlgo.findDestination( None, lambda plug : plug )
		)

	def testFindSource( self ) :

		self.assertIsNone( Gaffer.PlugAlgo.findSource( None, lambda plug : plug ) )
		self.assertIsNone( Gaffer.PlugAlgo.findSource( Gaffer.IntPlug(), lambda plug : None ) )

		node = GafferTest.AddNode()
		self.assertTrue(
			Gaffer.PlugAlgo.findSource( node["op1"], lambda plug : plug ).isSame( node["op1"] )
		)

		node2 = GafferTest.MultiplyNode()
		node["op1"].setInput( node2["product"] )

		self.assertTrue(
			Gaffer.PlugAlgo.findSource( node["op1"], lambda plug : plug ).isSame( node["op1"] )
		)

		self.assertTrue(
			Gaffer.PlugAlgo.findSource(
				node["op1"], lambda plug : plug if isinstance( plug.node(), GafferTest.MultiplyNode ) else None
			).isSame( node2["product"] )
		)

	def testNumericDataConversions( self ) :

		for data in [
			IECore.HalfData( 2.5 ),
			IECore.DoubleData( 2.5 ),
			IECore.CharData( "a" ),
			IECore.UCharData( 11 ),
			IECore.ShortData( -101 ),
			IECore.UShortData( 102 ),
			IECore.UIntData( 405 ),
			IECore.Int64Data( -1001 ),
			IECore.UInt64Data( 1002 ),
		] :

			for plugType in [
				Gaffer.IntPlug,
				Gaffer.FloatPlug,
				Gaffer.BoolPlug,
			] :

				with self.subTest( data = data, plugType = plugType ) :

					plug = plugType()
					self.assertTrue( Gaffer.PlugAlgo.canSetValueFromData( plug, data ) )

					Gaffer.PlugAlgo.setValueFromData( plug, data )
					value = ord( data.value ) if isinstance( data, IECore.CharData ) else data.value
					self.assertEqual( plug.getValue(), plugType.ValueType( value ) )

	class CompoundDataNode( Gaffer.Node ) :

		def __init__( self, name = "CompoundDataNode" ) :

			Gaffer.Node.__init__( self, name )

			self["plug"] = Gaffer.CompoundDataPlug()
			self["plug"]["child1"] = Gaffer.NameValuePlug( "value1", 10 )
			self["plug"]["child2"] = Gaffer.NameValuePlug( "value2", 20 )

	IECore.registerRunTimeTyped( CompoundDataNode )

	def testPromoteCompoundDataPlug( self ) :

		script = Gaffer.ScriptNode()
		script["box"] = Gaffer.Box()
		script["box"]["node"] = self.CompoundDataNode()

		Gaffer.PlugAlgo.promote( script["box"]["node"]["plug"] )
		script["box"]["plug"]["child1"]["value"].setValue( 100 )
		script["box"]["plug"]["child2"]["value"].setInput( script["box"]["plug"]["child1"]["value"] )

		script2 = Gaffer.ScriptNode()
		script2.execute( script.serialise() )

		self.assertEqual( script2["box"]["plug"].keys(), script["box"]["plug"].keys() )
		self.assertTrue( Gaffer.PlugAlgo.isPromoted( script2["box"]["node"]["plug"] ) )
		self.assertEqual( script2["box"]["node"]["plug"]["child1"]["value"].getValue(), 100 )
		self.assertEqual(
			script2["box"]["node"]["plug"]["child2"]["value"].source(),
			script2["box"]["plug"]["child1"]["value"].source()
		)

	def testContextSensitiveSourceWithSwitch( self ) :

		node1 = GafferTest.AddNode()
		node2 = GafferTest.AddNode()

		indexQuery = Gaffer.ContextQuery()
		indexQuery.addQuery( Gaffer.IntPlug(), "index" )

		switch = Gaffer.Switch()
		switch.setup( node1["sum"] )
		switch["in"][0].setInput( node1["sum"] )
		switch["in"][1].setInput( node2["sum"] )
		switch["index"].setInput( indexQuery["out"][0]["value"] )

		plug = Gaffer.IntPlug()
		plug.setInput( switch["out"] )

		with Gaffer.Context() as context :

			self.assertEqual(
				Gaffer.PlugAlgo.contextSensitiveSource( plug ),
				( node1["sum"], context )
			)

			context["index"] = 0
			self.assertEqual(
				Gaffer.PlugAlgo.contextSensitiveSource( plug ),
				( node1["sum"], context )
			)

			context["index"] = 1
			self.assertEqual(
				Gaffer.PlugAlgo.contextSensitiveSource( plug ),
				( node2["sum"], context )
			)

	def testContextSensitiveSourceWithTimeWarp( self ) :

		node = GafferTest.AddNode()
		timeWarp = Gaffer.TimeWarp()
		timeWarp.setup( node["sum"] )
		timeWarp["in"].setInput( node["sum"] )
		timeWarp["offset"].setValue( 10 )

		source, sourceContext = Gaffer.PlugAlgo.contextSensitiveSource( timeWarp["out"] )
		self.assertEqual( source, node["sum"] )
		self.assertEqual( sourceContext.getFrame(), 11 )

	def testContextSensitiveSourceWithSpreadsheet( self ) :

		node = GafferTest.AddNode()

		spreadsheet = Gaffer.Spreadsheet()
		spreadsheet["selector"].setValue( "${row}" )
		spreadsheet["rows"].addColumn( node["op1"] )
		node["op1"].setInput( spreadsheet["out"]["op1"] )

		spreadsheet["rows"].addRows( 2 )
		spreadsheet["rows"][1]["name"].setValue( "one" )
		spreadsheet["rows"][1]["cells"]["op1"]["value"].setValue( 1 )
		spreadsheet["rows"][2]["name"].setValue( "two" )
		spreadsheet["rows"][2]["cells"]["op1"]["value"].setValue( 2 )

		with Gaffer.Context() as context :

			self.assertEqual(
				Gaffer.PlugAlgo.contextSensitiveSource( node["op1"] ),
				( spreadsheet["rows"][0]["cells"]["op1"]["value"], context )
			)

			context["row"] = "one"
			self.assertEqual(
				Gaffer.PlugAlgo.contextSensitiveSource( node["op1"] ),
				( spreadsheet["rows"][1]["cells"]["op1"]["value"], context )
			)

			context["row"] = "two"
			self.assertEqual(
				Gaffer.PlugAlgo.contextSensitiveSource( node["op1"] ),
				( spreadsheet["rows"][2]["cells"]["op1"]["value"], context )
			)

	def testContextSensitiveSourceWithLoop( self ) :

		node = GafferTest.AddNode()

		loop = Gaffer.Loop()
		loop.setup( node["op1"] )
		loop["iterations"].setValue( 5 )
		loop["next"].setInput( node["sum"] )
		node["op1"].setInput( loop["previous"] )

		source, context = Gaffer.PlugAlgo.contextSensitiveSource( loop["out"] )
		self.assertEqual( source, node["sum"] )
		self.assertEqual( context["loop:index"], 4 )

		for i in range( 3, -1, -1 ) :
			with context :
				source, context = Gaffer.PlugAlgo.contextSensitiveSource( node["op1"] )
				self.assertEqual( source, node["sum"] )
				self.assertEqual( context["loop:index"], i )

		source, context = Gaffer.PlugAlgo.contextSensitiveSource( node["op1"] )
		self.assertEqual( source, loop["in"] )
		self.assertNotIn( "loop:index", context )

	def testContextSensitiveSourceWithCanceller( self ) :

		node = GafferTest.AddNode()
		timeWarp = Gaffer.TimeWarp()
		timeWarp.setup( node["sum"] )
		timeWarp["in"].setInput( node["sum"] )
		timeWarp["offset"].setValue( 10 )

		canceller = IECore.Canceller()
		context = Gaffer.Context( Gaffer.Context(), canceller )
		with context :
			source, sourceContext = Gaffer.PlugAlgo.contextSensitiveSource( timeWarp["out"] )

		self.assertEqual( sourceContext.getFrame(), 11 )
		self.assertIsNotNone( sourceContext.canceller() )

if __name__ == "__main__":
	unittest.main()
