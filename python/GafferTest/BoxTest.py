##########################################################################
#
#  Copyright (c) 2013-2015, Image Engine Design Inc. All rights reserved.
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
import pathlib

import IECore

import Gaffer
import GafferTest

class BoxTest( GafferTest.TestCase ) :

	def testSerialisation( self ) :

		s = Gaffer.ScriptNode()

		s["b"] = Gaffer.Box()
		s["b"]["n1"] = GafferTest.AddNode()
		s["b"]["n2"] = GafferTest.AddNode()
		s["b"]["n2"]["op1"].setInput( s["b"]["n1"]["sum"] )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertTrue( s2["b"]["n2"]["op1"].getInput().isSame( s2["b"]["n1"]["sum"] ) )

	def testCreate( self ) :

		s = Gaffer.ScriptNode()

		s["n1"] = GafferTest.AddNode()
		s["n2"] = GafferTest.AddNode()
		s["n3"] = GafferTest.AddNode()
		s["n4"] = GafferTest.AddNode()

		s["n2"]["op1"].setInput( s["n1"]["sum"] )
		s["n2"]["op2"].setInput( s["n1"]["sum"] )

		s["n3"]["op1"].setInput( s["n2"]["sum"] )

		s["n4"]["op1"].setInput( s["n3"]["sum"] )
		s["n4"]["op2"].setInput( s["n3"]["sum"] )

		def assertPreConditions() :

			self.assertTrue( "Box" not in s )

			self.assertTrue( s["n2"]["op1"].getInput().isSame( s["n1"]["sum"] ) )
			self.assertTrue( s["n2"]["op2"].getInput().isSame( s["n1"]["sum"] ) )

			self.assertTrue( s["n3"]["op1"].getInput().isSame( s["n2"]["sum"] ) )

			self.assertTrue( s["n4"]["op1"].getInput().isSame( s["n3"]["sum"] ) )
			self.assertTrue( s["n4"]["op2"].getInput().isSame( s["n3"]["sum"] ) )

		assertPreConditions()

		with Gaffer.UndoScope( s ) :
			b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["n2"], s["n3"] ] ) )

		def assertPostConditions() :

			self.assertTrue( isinstance( b, Gaffer.Box ) )
			self.assertTrue( b.parent().isSame( s ) )

			self.assertTrue( "n2" not in s )
			self.assertTrue( "n3" not in s )

			self.assertTrue( "n2" in b )
			self.assertTrue( "n3" in b )

			self.assertTrue( b["n3"]["op1"].getInput().isSame( b["n2"]["sum"] ) )

			self.assertTrue( b["n2"]["op1"].getInput().node().isSame( b ) )
			self.assertTrue( b["n2"]["op2"].getInput().node().isSame( b ) )

			self.assertTrue( b["n2"]["op1"].getInput().getInput().isSame( s["n1"]["sum"] ) )
			self.assertTrue( b["n2"]["op2"].getInput().getInput().isSame( s["n1"]["sum"] ) )
			self.assertTrue( b["n2"]["op1"].getInput().isSame( b["n2"]["op2"].getInput() ) )

			self.assertTrue( s["n4"]["op1"].getInput().node().isSame( b ) )
			self.assertTrue( s["n4"]["op2"].getInput().node().isSame( b ) )

			self.assertTrue( s["n4"]["op1"].getInput().isSame( s["n4"]["op2"].getInput() ) )

		assertPostConditions()

		s.undo()
		assertPreConditions()

		s.redo()
		assertPostConditions()

	def testCreateWithScriptSelection( self ) :

		s = Gaffer.ScriptNode()

		s["n1"] = GafferTest.AddNode()
		s["n2"] = GafferTest.AddNode()
		s["n3"] = GafferTest.AddNode()
		s["n4"] = GafferTest.AddNode()

		s["n2"]["op1"].setInput( s["n1"]["sum"] )
		s["n2"]["op2"].setInput( s["n1"]["sum"] )

		s["n3"]["op1"].setInput( s["n2"]["sum"] )

		s["n4"]["op1"].setInput( s["n3"]["sum"] )
		s["n4"]["op2"].setInput( s["n3"]["sum"] )

		s.selection().add( [ s["n2"], s["n3"] ] )

		b = Gaffer.Box.create( s, s.selection() )

	def testCreateWithScriptSelectionReversed( self ) :

		s = Gaffer.ScriptNode()

		s["n1"] = GafferTest.AddNode()
		s["n2"] = GafferTest.AddNode()
		s["n3"] = GafferTest.AddNode()
		s["n4"] = GafferTest.AddNode()

		s["n2"]["op1"].setInput( s["n1"]["sum"] )
		s["n2"]["op2"].setInput( s["n1"]["sum"] )

		s["n3"]["op1"].setInput( s["n2"]["sum"] )

		s["n4"]["op1"].setInput( s["n3"]["sum"] )
		s["n4"]["op2"].setInput( s["n3"]["sum"] )

		s.selection().add( [ s["n3"], s["n2"] ] )

		b = Gaffer.Box.create( s, s.selection() )

	def testCompute( self ) :

		s = Gaffer.ScriptNode()

		s["n1"] = GafferTest.AddNode()
		s["n2"] = GafferTest.AddNode()
		s["n3"] = GafferTest.AddNode()
		s["n4"] = GafferTest.AddNode()

		s["n2"]["op1"].setInput( s["n1"]["sum"] )
		s["n2"]["op2"].setInput( s["n1"]["sum"] )

		s["n3"]["op1"].setInput( s["n2"]["sum"] )

		s["n4"]["op1"].setInput( s["n3"]["sum"] )
		s["n4"]["op2"].setInput( s["n3"]["sum"] )

		s["n1"]["op1"].setValue( 2 )
		s["n3"]["op2"].setValue( 3 )

		self.assertEqual( s["n1"]["sum"].getValue(), 2 )
		self.assertEqual( s["n2"]["sum"].getValue(), 4 )
		self.assertEqual( s["n3"]["sum"].getValue(), 7 )
		self.assertEqual( s["n4"]["sum"].getValue(), 14 )

		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["n2"], s["n3"] ] ) )

		self.assertEqual( s["n1"]["sum"].getValue(), 2 )
		self.assertEqual( s["Box"]["n2"]["sum"].getValue(), 4 )
		self.assertEqual( s["Box"]["n3"]["sum"].getValue(), 7 )
		self.assertEqual( s["n4"]["sum"].getValue(), 14 )

	def testCreateWithNodesWithInternalConnections( self ) :

		s = Gaffer.ScriptNode()

		s["n1"] = GafferTest.AddNode()
		s["n2"] = Gaffer.Node()
		s["n3"] = GafferTest.AddNode()

		s["n2"]["in"] = Gaffer.IntPlug()
		s["n2"]["out"] = Gaffer.IntPlug( direction = Gaffer.Plug.Direction.Out )
		s["n2"]["__in"] = Gaffer.IntPlug()
		s["n2"]["__out"] = Gaffer.IntPlug( direction = Gaffer.Plug.Direction.Out )


		s["n2"]["in"].setInput( s["n1"]["sum"] )
		s["n2"]["out"].setInput( s["n2"]["in"] ) # internal shortcut connection
		s["n2"]["__in"].setInput( s["n2"]["__out"] ) # internal input connection
		s["n3"]["op1"].setInput( s["n2"]["out"] )

		s.selection().add( s["n2"] )
		b = Gaffer.Box.create( s, s.selection() )

		self.assertEqual( len( b ), 4 ) # the user plug, one child node, an in plug and an out plug

		self.assertTrue( b["n2"]["in"].getInput().isSame( b["in"] ) )
		self.assertTrue( b["in"].getInput().isSame( s["n1"]["sum"] ) )

		self.assertTrue( b["n2"]["out"].getInput().isSame( b["n2"]["in"] ) )
		self.assertTrue( s["n3"]["op1"].getInput().isSame( b["out"] ) )

	def testSerialisationOfCreatedResult( self ) :

		s = Gaffer.ScriptNode()

		s["n1"] = GafferTest.AddNode()
		s["n2"] = GafferTest.AddNode()
		s["n3"] = GafferTest.AddNode()
		s["n4"] = GafferTest.AddNode()

		s["n2"]["op1"].setInput( s["n1"]["sum"] )
		s["n2"]["op2"].setInput( s["n1"]["sum"] )

		s["n3"]["op1"].setInput( s["n2"]["sum"] )

		s["n4"]["op1"].setInput( s["n3"]["sum"] )
		s["n4"]["op2"].setInput( s["n3"]["sum"] )

		Gaffer.Box.create( s, Gaffer.StandardSet( [ s["n2"], s["n3"] ] ) )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertTrue( isinstance( s2["Box"], Gaffer.Box ) )

		self.assertTrue( "n2" not in s2 )
		self.assertTrue( "n3" not in s2 )

		self.assertTrue( "n2" in s2["Box"] )
		self.assertTrue( "n3" in s2["Box"] )

		self.assertTrue( s2["Box"]["n3"]["op1"].getInput().isSame( s2["Box"]["n2"]["sum"] ) )

		self.assertTrue( s2["Box"]["n2"]["op1"].getInput().node().isSame( s2["Box"] ) )
		self.assertTrue( s2["Box"]["n2"]["op2"].getInput().node().isSame( s2["Box"] ) )

		self.assertTrue( s2["Box"]["n2"]["op1"].getInput().getInput().isSame( s2["n1"]["sum"] ) )
		self.assertTrue( s2["Box"]["n2"]["op2"].getInput().getInput().isSame( s2["n1"]["sum"] ) )
		self.assertTrue( s2["Box"]["n2"]["op1"].getInput().isSame( s2["Box"]["n2"]["op2"].getInput() ) )

		self.assertTrue( s2["n4"]["op1"].getInput().node().isSame( s2["Box"] ) )
		self.assertTrue( s2["n4"]["op2"].getInput().node().isSame( s2["Box"] ) )

		self.assertTrue( s2["n4"]["op1"].getInput().isSame( s2["n4"]["op2"].getInput() ) )

	def testSelection( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["b"] = Gaffer.Box()
		s["b"]["n"] = Gaffer.Node()

		s.selection().add( s["n"] )
		s.selection().add( s["b"]["n"] )

		self.assertTrue( s["n"] in s.selection() )
		self.assertTrue( s["b"]["n"] in s.selection() )

	def testPromote( self ) :

		s = Gaffer.ScriptNode()

		s["n1"] = GafferTest.AddNode()
		s["n1"]["op1"].setValue( -10 )
		s["n2"] = GafferTest.AddNode()

		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["n1"] ] ) )

		self.assertTrue( b.canPromotePlug( b["n1"]["op1"] ) )
		self.assertFalse( b.canPromotePlug( s["n2"]["op1"] ) )

		self.assertFalse( b.plugIsPromoted( b["n1"]["op1"] ) )
		self.assertFalse( b.plugIsPromoted( b["n1"]["op2"] ) )
		self.assertFalse( b.plugIsPromoted( s["n2"]["op1"] ) )

		p = b.promotePlug( b["n1"]["op1"] )
		self.assertEqual( p.getName(), "op1" )
		self.assertTrue( p.parent().isSame( b ) )
		self.assertTrue( b["n1"]["op1"].getInput().isSame( p ) )
		self.assertTrue( b.plugIsPromoted( b["n1"]["op1"] ) )
		self.assertFalse( b.canPromotePlug( b["n1"]["op1"] ) )
		self.assertEqual( p.getValue(), -10 )

	def testPromoteColor( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["c"] = Gaffer.Color3fPlug()
		s["n"]["c"].setValue( imath.Color3f( 1, 0, 1 ) )

		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["n"] ] ) )

		self.assertTrue( b.canPromotePlug( b["n"]["c"] ) )
		self.assertFalse( b.plugIsPromoted( b["n"]["c"] ) )

		p = b.promotePlug( b["n"]["c"] )

		self.assertTrue( isinstance( p, Gaffer.Color3fPlug ) )
		self.assertTrue( b["n"]["c"].getInput().isSame( p ) )
		self.assertTrue( b["n"]["c"]["r"].getInput().isSame( p["r"] ) )
		self.assertTrue( b["n"]["c"]["g"].getInput().isSame( p["g"] ) )
		self.assertTrue( b["n"]["c"]["b"].getInput().isSame( p["b"] ) )
		self.assertEqual( p.getValue(), imath.Color3f( 1, 0, 1 ) )

	def testPromoteCompoundPlugAndSerialise( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = GafferTest.CompoundPlugNode()
		s["n"]["p"]["s"].setValue( "hello" )

		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["n"] ] ) )
		b.promotePlug( b["n"]["p"] )

		ss = s.serialise()

		s = Gaffer.ScriptNode()
		s.execute( ss )

		self.assertEqual( s["Box"]["n"]["p"]["s"].getValue(), "hello" )

	def testPromoteDynamicColorPlugAndSerialise( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["c"] = Gaffer.Color3fPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["n"] ] ) )
		b.promotePlug( b["n"]["c"] )

		ss = s.serialise()

		s = Gaffer.ScriptNode()
		s.execute( ss )

		self.assertTrue( isinstance( s["Box"]["c"], Gaffer.Color3fPlug ) )
		self.assertTrue( s["Box"]["n"]["c"].getInput().isSame( s["Box"]["c"] ) )

	def testPromoteNonDynamicColorPlugAndSerialise( self ) :

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()
		s["b"]["n"] = Gaffer.Random()

		p = s["b"].promotePlug( s["b"]["n"]["baseColor"] )
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
		s["n"] = Gaffer.Node()
		s["n"]["p"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default & ~Gaffer.Plug.Flags.Serialisable )

		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["n"] ] ) )
		self.assertEqual( b.canPromotePlug( b["n"]["p"] ), False )
		self.assertRaises( RuntimeError, b.promotePlug, b["n"]["p"] )

	def testUnpromoting( self ) :

		s = Gaffer.ScriptNode()

		s["n1"] = GafferTest.AddNode()

		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["n1"] ] ) )
		p = b.promotePlug( b["n1"]["op1"] )
		self.assertTrue( b.plugIsPromoted( b["n1"]["op1"] ) )
		self.assertTrue( p.node().isSame( b ) )

		b.unpromotePlug( b["n1"]["op1"] )
		self.assertFalse( b.plugIsPromoted( b["n1"]["op1"] ) )
		self.assertTrue( p.node() is None )

	def testColorUnpromoting( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["c"] = Gaffer.Color3fPlug()

		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["n"] ] ) )
		p = b.promotePlug( b["n"]["c"] )
		self.assertTrue( b.plugIsPromoted( b["n"]["c"] ) )
		self.assertTrue( b.plugIsPromoted( b["n"]["c"]["r"] ) )
		self.assertTrue( b.plugIsPromoted( b["n"]["c"]["g"] ) )
		self.assertTrue( b.plugIsPromoted( b["n"]["c"]["b"] ) )
		self.assertTrue( p.node().isSame( b ) )

		b.unpromotePlug( b["n"]["c"] )
		self.assertFalse( b.plugIsPromoted( b["n"]["c"] ) )
		self.assertFalse( b.plugIsPromoted( b["n"]["c"]["r"] ) )
		self.assertFalse( b.plugIsPromoted( b["n"]["c"]["g"] ) )
		self.assertFalse( b.plugIsPromoted( b["n"]["c"]["b"] ) )
		self.assertTrue( p.node() is None )

	def testIncrementalUnpromoting( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["c"] = Gaffer.Color3fPlug()

		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["n"] ] ) )
		p = b.promotePlug( b["n"]["c"] )
		self.assertTrue( b.plugIsPromoted( b["n"]["c"] ) )
		self.assertTrue( b.plugIsPromoted( b["n"]["c"]["r"] ) )
		self.assertTrue( b.plugIsPromoted( b["n"]["c"]["g"] ) )
		self.assertTrue( b.plugIsPromoted( b["n"]["c"]["b"] ) )
		self.assertTrue( p.node().isSame( b ) )

		b.unpromotePlug( b["n"]["c"]["r"] )
		self.assertFalse( b.plugIsPromoted( b["n"]["c"] ) )
		self.assertFalse( b.plugIsPromoted( b["n"]["c"]["r"] ) )
		self.assertTrue( b.plugIsPromoted( b["n"]["c"]["g"] ) )
		self.assertTrue( b.plugIsPromoted( b["n"]["c"]["b"] ) )
		self.assertTrue( p.node().isSame( b ) )

		b.unpromotePlug( b["n"]["c"]["g"] )
		self.assertFalse( b.plugIsPromoted( b["n"]["c"] ) )
		self.assertFalse( b.plugIsPromoted( b["n"]["c"]["r"] ) )
		self.assertFalse( b.plugIsPromoted( b["n"]["c"]["g"] ) )
		self.assertTrue( b.plugIsPromoted( b["n"]["c"]["b"] ) )
		self.assertTrue( p.node().isSame( b ) )

		b.unpromotePlug( b["n"]["c"]["b"] )
		self.assertFalse( b.plugIsPromoted( b["n"]["c"] ) )
		self.assertFalse( b.plugIsPromoted( b["n"]["c"]["r"] ) )
		self.assertFalse( b.plugIsPromoted( b["n"]["c"]["g"] ) )
		self.assertFalse( b.plugIsPromoted( b["n"]["c"]["b"] ) )
		self.assertTrue( p.node() is None )

	def testDeletedNodesAreUnselected( self ) :

		s = Gaffer.ScriptNode()

		s["n1"] = Gaffer.Node()
		s["n2"] = Gaffer.Node()

		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["n1"], s["n2"] ] ) )

		s.selection().add( b["n1"] )
		s.selection().add( b["n2"] )

		self.assertEqual( len( s.selection() ), 2 )

		n1 = b["n1"]
		del b["n1"]

		self.assertTrue( b["n2"] in s.selection() )
		self.assertFalse( n1 in s.selection() )
		self.assertEqual( len( s.selection() ), 1 )

	def testDerivingInPython( self ) :

		class DerivedBox( Gaffer.Box ) :

			def __init__( self, name = "DerivedBox" ) :

				Gaffer.Box.__init__( self, name )

		IECore.registerRunTimeTyped( DerivedBox )

		# check that the typeid can be seen from the C++ side.

		b = DerivedBox()
		b["c"] = Gaffer.Node()

		a = b["c"].ancestor( DerivedBox )
		self.assertTrue( a.isSame( b ) )

		# check that adding the node to a script and getting
		# it back gives the same object, with the correct
		# typeids etc.

		s = Gaffer.ScriptNode()
		s["b"] = b

		self.assertTrue( s["b"] is b )
		self.assertEqual( s["b"].typeId(), DerivedBox.staticTypeId() )
		self.assertEqual( s["b"].typeName(), DerivedBox.staticTypeName() )

	def testNesting( self ) :

		s = Gaffer.ScriptNode()

		s["a1"] = GafferTest.AddNode()
		s["a2"] = GafferTest.AddNode()
		s["a2"]["op1"].setInput( s["a1"]["sum"] )

		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["a1"], s["a2"] ] ) )
		# we're not expecting any extra plugs on the box, because the enclosed network
		# had no external connections.
		self.assertEqual( b.keys(), Gaffer.Box().keys() + [ "a1", "a2" ] )

		b2 = Gaffer.Box.create( s, Gaffer.StandardSet( [ b ] ) )
		self.assertTrue( b.parent().isSame( b2 ) )
		# likewise here, the enclosed network had no external connections so the
		# box should have no additional children other than the nested box.
		self.assertEqual( b2.keys(), Gaffer.Box().keys() + [ b.getName() ] )

	def testMetadata( self ) :

		s = Gaffer.ScriptNode()

		s["a1"] = GafferTest.AddNode()
		s["a2"] = GafferTest.AddNode()
		s["a2"]["op1"].setInput( s["a1"]["sum"] )

		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["a2"] ] ) )

		self.assertEqual( Gaffer.Metadata.value( b["op1"], "description" ), None )

		Gaffer.Metadata.registerValue( b["op1"], "description", "hello" )
		self.assertEqual( Gaffer.Metadata.value( b["op1"], "description" ), "hello" )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( Gaffer.Metadata.value( s2["Box"]["op1"], "description" ), "hello" )

	def testMetadataSignalling( self ) :

		s = Gaffer.ScriptNode()
		s["r"] = Gaffer.Random()

		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["r"] ] ) )
		p = b.promotePlug( b["r"]["floatRange"] )

		cs = GafferTest.CapturingSlot( Gaffer.Metadata.plugValueChangedSignal( b ) )

		Gaffer.Metadata.registerValue( p, "description", "hello" )

		self.assertEqual( len( cs ), 1 )
		self.assertEqual( cs[0], ( p, "description", Gaffer.Metadata.ValueChangedReason.InstanceRegistration ) )

	def testNodeMetadata( self ) :

		s = Gaffer.ScriptNode()

		s["b"] = Gaffer.Box()

		cs = GafferTest.CapturingSlot( Gaffer.Metadata.nodeValueChangedSignal() )

		Gaffer.Metadata.registerValue( s["b"], "description", "aaa" )
		self.assertEqual( Gaffer.Metadata.value( s["b"], "description" ), "aaa" )

		self.assertEqual( len( cs ), 1 )
		self.assertEqual( cs[0], ( Gaffer.Box.staticTypeId(), "description", s["b"] ) )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( Gaffer.Metadata.value( s["b"], "description" ), "aaa" )

	def testMetadataSignallingIgnoresIdenticalValues( self ) :

		s = Gaffer.ScriptNode()
		s["r"] = Gaffer.Random()

		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["r"] ] ) )
		p = b.promotePlug( b["r"]["floatRange"] )

		ncs = GafferTest.CapturingSlot( Gaffer.Metadata.nodeValueChangedSignal( b ) )
		pcs = GafferTest.CapturingSlot( Gaffer.Metadata.plugValueChangedSignal( b ) )

		Gaffer.Metadata.registerValue( b, "description", "t" )
		Gaffer.Metadata.registerValue( p, "description", "tt" )

		self.assertEqual( len( ncs ), 1 )
		self.assertEqual( len( pcs ), 1 )
		self.assertEqual( ncs[0], ( b, "description", Gaffer.Metadata.ValueChangedReason.InstanceRegistration ) )
		self.assertEqual( pcs[0], ( p, "description", Gaffer.Metadata.ValueChangedReason.InstanceRegistration ) )

		Gaffer.Metadata.registerValue( b, "description", "t" )
		Gaffer.Metadata.registerValue( p, "description", "tt" )

		self.assertEqual( len( ncs ), 1 )
		self.assertEqual( len( pcs ), 1 )

		Gaffer.Metadata.registerValue( b, "description", "d" )
		Gaffer.Metadata.registerValue( p, "description", "dd" )

		self.assertEqual( len( ncs ), 2 )
		self.assertEqual( len( pcs ), 2 )
		self.assertEqual( ncs[1], ( b, "description", Gaffer.Metadata.ValueChangedReason.InstanceRegistration ) )
		self.assertEqual( pcs[1], ( p, "description", Gaffer.Metadata.ValueChangedReason.InstanceRegistration ) )

	def testMetadataUndo( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()

		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["n"] ] ) )
		p = b.promotePlug( b["n"]["op1"] )

		originalBoxDescription = Gaffer.Metadata.value( b, "description" )
		originalPlugDescription = Gaffer.Metadata.value( p, "description" )

		with Gaffer.UndoScope( s ) :
			Gaffer.Metadata.registerValue( b, "description", "d" )
			Gaffer.Metadata.registerValue( p, "description", "dd" )

		self.assertEqual( Gaffer.Metadata.value( b, "description" ), "d" )
		self.assertEqual( Gaffer.Metadata.value( p, "description" ), "dd" )

		with Gaffer.UndoScope( s ) :
			Gaffer.Metadata.registerValue( b, "description", "t" )
			Gaffer.Metadata.registerValue( p, "description", "tt" )

		self.assertEqual( Gaffer.Metadata.value( b, "description" ), "t" )
		self.assertEqual( Gaffer.Metadata.value( p, "description" ), "tt" )

		s.undo()

		self.assertEqual( Gaffer.Metadata.value( b, "description" ), "d" )
		self.assertEqual( Gaffer.Metadata.value( p, "description" ), "dd" )

		s.undo()

		self.assertEqual( Gaffer.Metadata.value( b, "description" ), originalBoxDescription )
		self.assertEqual( Gaffer.Metadata.value( p, "description" ), originalPlugDescription )

		s.redo()

		self.assertEqual( Gaffer.Metadata.value( b, "description" ), "d" )
		self.assertEqual( Gaffer.Metadata.value( p, "description" ), "dd" )

		s.redo()

		self.assertEqual( Gaffer.Metadata.value( b, "description" ), "t" )
		self.assertEqual( Gaffer.Metadata.value( p, "description" ), "tt" )

	def testPromoteOutputPlug( self ) :

		b = Gaffer.Box()
		b["n"] = GafferTest.AddNode()

		self.assertTrue( b.canPromotePlug( b["n"]["sum"] ) )

		sum = b.promotePlug( b["n"]["sum"] )
		self.assertTrue( b.isAncestorOf( sum ) )
		self.assertTrue( sum.direction() == Gaffer.Plug.Direction.Out )
		self.assertEqual( sum.getInput(), b["n"]["sum"] )
		self.assertTrue( b.plugIsPromoted( b["n"]["sum"] ) )
		self.assertFalse( b.canPromotePlug( b["n"]["sum"] ) )
		self.assertRaises( RuntimeError, b.promotePlug, b["n"]["sum"] )

		b["n"]["op1"].setValue( 10 )
		b["n"]["op2"].setValue( 12 )

		self.assertEqual( sum.getValue(), 22 )

		b.unpromotePlug( b["n"]["sum"] )
		self.assertFalse( b.plugIsPromoted( b["n"]["sum"] ) )
		self.assertTrue( sum.parent() is None )
		self.assertTrue( b.canPromotePlug( b["n"]["sum"] ) )

	def testDependencyNode( self ) :

		s = Gaffer.ScriptNode()

		# Make a box, and check it's a DependencyNode

		s["b"] = Gaffer.Box()
		self.assertTrue( isinstance( s["b"], Gaffer.DependencyNode ) )
		self.assertTrue( s["b"].isInstanceOf( Gaffer.DependencyNode.staticTypeId() ) )

		s["b"]["n"] = GafferTest.AddNode()
		outPromoted = s["b"].promotePlug( s["b"]["n"]["sum"] )

		# Wire it up to support enabledPlug() and correspondingInput()

		self.assertEqual( s["b"].correspondingInput( outPromoted ), None )
		self.assertEqual( s["b"].enabledPlug(), None )

		inPromoted = s["b"].promotePlug( s["b"]["n"]["op1"] )
		s["b"]["n"]["op2"].setValue( 10 )

		self.assertEqual( s["b"].correspondingInput( outPromoted ), None )
		self.assertEqual( s["b"].enabledPlug(), None )

		s["b"]["enabled"] = Gaffer.BoolPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		self.assertEqual( s["b"].correspondingInput( outPromoted ), None )
		self.assertTrue( s["b"].enabledPlug().isSame( s["b"]["enabled"] ) )

		s["b"]["n"]["enabled"].setInput( s["b"]["enabled"] )

		self.assertTrue( s["b"].enabledPlug().isSame( s["b"]["enabled"] ) )
		self.assertTrue( s["b"].correspondingInput( outPromoted ).isSame( inPromoted ) )

		# Connect it into a network, delete it, and check that we get nice auto-reconnect behaviour

		s["a"] = GafferTest.AddNode()
		inPromoted.setInput( s["a"]["sum"] )

		s["c"] = GafferTest.AddNode()
		s["c"]["op1"].setInput( outPromoted )

		s.deleteNodes( filter = Gaffer.StandardSet( [ s["b"] ] ) )

		self.assertTrue( s["c"]["op1"].getInput().isSame( s["a"]["sum"] ) )

	def testSerialiseChildrenOmitsParentMetadata( self ) :

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()
		s["b"]["n"] = Gaffer.Node()

		defaultDescription = Gaffer.Metadata.value( s["b"], "description" )
		defaultNodeColor = Gaffer.Metadata.value( s["b"], "nodeGadget:color" )

		Gaffer.Metadata.registerValue( s["b"], "description", "Test description" )
		Gaffer.Metadata.registerValue( s["b"], "nodeGadget:color", imath.Color3f( 1, 0, 0 ) )

		ss = s.serialise( parent = s["b"] )

		s["b2"] = Gaffer.Box()
		s.execute( ss, parent = s["b2"] )

		self.assertTrue( "n" in s["b2"] )
		self.assertEqual( Gaffer.Metadata.value( s["b2"], "description" ), defaultDescription )
		self.assertEqual( Gaffer.Metadata.value( s["b2"], "nodeGadget:color" ), defaultNodeColor )

	def testPromoteDynamicBoxPlugAndSerialise( self ) :

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()
		s["b"]["n"] = Gaffer.Node()
		s["b"]["n"]["p"] = Gaffer.Box2iPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		p = s["b"].promotePlug( s["b"]["n"]["p"] )
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

		p = s["b"].promotePlug( s["b"]["n"]["valuePlug"] )
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

		p = s["b"].promotePlug( s["b"]["n"]["user"]["p"] )
		p.setName( "p" )
		p["p"]["i"].setValue( 10 )

		v = s["b"].promotePlug( s["b"]["n"]["user"]["v"] )
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

		p = s["b"].promotePlug( s["b"]["n"]["in"] )
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

		p = s["b"].promotePlug( s["b"]["n"]["user"]["p"] )
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

		p = s["b"].promotePlug( s["b"]["n"]["user"]["p"] )
		p.setName( "p" )

		self.assertEqual( Gaffer.Metadata.value( p, "testInt" ), 10 )
		self.assertEqual( Gaffer.Metadata.value( p["i"], "testString" ), "test" )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( Gaffer.Metadata.value( s2["b"]["p"], "testInt" ), 10 )
		self.assertEqual( Gaffer.Metadata.value( s2["b"]["p"]["i"], "testString" ), "test" )

	def testCreateWithBoxIOInSelection( self ) :

		s = Gaffer.ScriptNode()

		# Make a Box containing BoxIn -> n -> BoxOut

		s["b"] = Gaffer.Box()
		s["b"]["i"] = Gaffer.BoxIn()
		s["b"]["n"] = GafferTest.AddNode()
		s["b"]["o"] = Gaffer.BoxOut()

		s["b"]["i"]["name"].setValue( "op1" )
		s["b"]["i"].setup( s["b"]["n"]["op1"] )
		s["b"]["n"]["op1"].setInput( s["b"]["i"]["out"] )

		s["b"]["o"]["name"].setValue( "sum" )
		s["b"]["o"].setup( s["b"]["n"]["sum"] )
		s["b"]["o"]["in"].setInput( s["b"]["n"]["sum"] )

		# Ask to move all that (including the BoxIOs) into a
		# nested Box. This doesn't really make sense, because
		# the BoxIOs exist purely to build a bridge to the
		# outer parent. So we expect them to remain where they
		# were.

		innerBox = Gaffer.Box.create( s["b"], Gaffer.StandardSet( s["b"].children( Gaffer.Node ) ) )

		self.assertEqual( len( innerBox.children( Gaffer.Node ) ), 1 )
		self.assertTrue( "n" in innerBox )
		self.assertFalse( "n" in s["b"] )
		self.assertTrue( "i" in s["b"] )
		self.assertTrue( "o" in s["b"] )
		self.assertTrue( s["b"]["sum"].source().isSame( innerBox["n"]["sum"] ) )
		self.assertTrue( innerBox["n"]["op1"].source().isSame( s["b"]["op1"] ) )

	def testCreateWithBoxIOPassThroughInSelection( self ) :

		s = Gaffer.ScriptNode()

		# Make a Box containing BoxIn -> n -> BoxOut
		# and BoxIn -> dot -> BoxOut.passThrough

		s["b"] = Gaffer.Box()
		s["b"]["i"] = Gaffer.BoxIn()
		s["b"]["n"] = GafferTest.AddNode()
		s["b"]["o"] = Gaffer.BoxOut()

		s["b"]["i"]["name"].setValue( "op1" )
		s["b"]["i"].setup( s["b"]["n"]["op1"] )
		s["b"]["n"]["op1"].setInput( s["b"]["i"]["out"] )

		s["b"]["dot"] = Gaffer.Dot()
		s["b"]["dot"].setup( s["b"]["n"]["sum"] )
		s["b"]["dot"]["in"].setInput( s["b"]["i"]["out"] )

		s["b"]["o"]["name"].setValue( "sum" )
		s["b"]["o"].setup( s["b"]["n"]["sum"] )
		s["b"]["o"]["in"].setInput( s["b"]["n"]["sum"] )
		s["b"]["o"]["passThrough"].setInput( s["b"]["dot"]["out"] )

		# Ask to move all that (including the BoxIOs) into a
		# nested Box. This doesn't really make sense, because
		# the BoxIOs exist purely to build a bridge to the
		# outer parent. So we expect them to remain where they
		# were.

		innerBox = Gaffer.Box.create( s["b"], Gaffer.StandardSet( s["b"].children( Gaffer.Node ) ) )

		self.assertEqual( len( innerBox.children( Gaffer.Node ) ), 1 )
		self.assertTrue( "n" in innerBox )
		self.assertFalse( "n" in s["b"] )
		self.assertFalse( "dot" in innerBox )
		self.assertTrue( "dot" in s["b"] )
		self.assertTrue( "i" in s["b"] )
		self.assertTrue( "o" in s["b"] )
		self.assertTrue( s["b"]["sum"].source().isSame( innerBox["n"]["sum"] ) )
		self.assertTrue( innerBox["n"]["op1"].source().isSame( s["b"]["op1"] ) )
		self.assertTrue( s["b"]["o"]["passThrough"].source().isSame( s["b"]["i"].promotedPlug() ) )

	def testCanBoxNodesWithInternalNodeNetworkAndHiddenPlug( self ) :

		# if we try to box a node which has an internal node network using a hidden non-serialised
		# input plug then a spurious exception is raised as the Box::create function
		# attempts to promote the __i plug.

		scriptNode = Gaffer.ScriptNode()

		externalNode = Gaffer.Node( "external" )
		scriptNode.addChild( externalNode )

		outPlug = Gaffer.IntPlug( "output", Gaffer.IntPlug.Direction.Out )
		externalNode.addChild( outPlug )

		nodeToBox = Gaffer.Node( "toBox" )
		scriptNode.addChild( nodeToBox )

		nodeIn = Gaffer.IntPlug( "i", Gaffer.IntPlug.Direction.In )
		nodeToBox.addChild( nodeIn )

		nodeIn.setInput( outPlug )

		hiddenIn = Gaffer.IntPlug( "__i", Gaffer.IntPlug.Direction.In, flags = Gaffer.IntPlug.Flags.Default & ~Gaffer.IntPlug.Flags.Serialisable )
		nodeToBox.addChild( hiddenIn )

		childNode = Gaffer.Node()
		nodeToBox.addChild( childNode )

		childIn = Gaffer.IntPlug( "i", Gaffer.IntPlug.Direction.In )
		childNode.addChild( childIn )

		childOut = Gaffer.IntPlug( "o", Gaffer.IntPlug.Direction.Out )
		childNode.addChild( childOut )

		childIn.setInput( nodeIn )
		hiddenIn.setInput( childOut )

		setOfNodesToBox = Gaffer.StandardSet()
		setOfNodesToBox.add( nodeToBox )

		try :
			box = Gaffer.Box.create( scriptNode, setOfNodesToBox )
		except RuntimeError as e :
			self.assertTrue( False, msg = "boxing should not raise an exception here" )

	def testPassThroughCreatedInVersion0_52( self ) :

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( ( pathlib.Path( __file__ ).parent / "scripts" / "boxPassThroughVersion-0.52.0.0.gfr" ).as_posix() )
		s.load()

		def assertPassThrough( script ) :

			self.assertEqual( script["AddTen"]["op1"].getValue(), 0 )
			self.assertEqual( script["AddTen"]["sum"].getValue(), 10 )
			self.assertEqual( script["AddTen"].correspondingInput( script["AddTen"]["sum"] ), script["AddTen"]["op1"] )

			script["AddTen"]["enabled"].setValue( False )
			self.assertEqual( script["AddTen"]["sum"].getValue(), 0 )

			script["AddTen"]["op1"].setValue( 1 )
			self.assertEqual( script["AddTen"]["sum"].getValue(), 1 )

			script["AddTen"]["enabled"].setValue( True )
			script["AddTen"]["op1"].setValue( 0 )

		assertPassThrough( s )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		assertPassThrough( s2 )

	def testAddPassThroughToBoxFromVersion0_52( self ) :

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( ( pathlib.Path( __file__ ).parent / "scripts" / "boxVersion-0.52.0.0.gfr" ).as_posix() )
		s.load()

		# The original Box had no pass-through behaviour defined,
		# and no "enabled" plug. We don't want that to change without
		# user interaction.

		self.assertNotIn( "enabled", s["AddTen"] )
		self.assertEqual( s["AddTen"]["sum"].getValue(), 10 )

		# When the user defines a pass-through for the first time,
		# only then do we want to create the enabled plug and hook
		# everything up.

		s["AddTen"]["BoxOut"]["passThrough"].setInput( s["AddTen"]["BoxIn"]["out"] )

		def assertPassThrough( script ) :

			self.assertIn( "enabled", script["AddTen"] )
			self.assertEqual( script["AddTen"]["enabled"].getValue(), True )
			self.assertEqual( script["AddTen"]["sum"].getValue(), 10 )
			script["AddTen"]["enabled"].setValue( False )
			self.assertEqual( script["AddTen"]["sum"].getValue(), 0 )

			script["AddTen"]["op1"].setValue( 1 )
			self.assertEqual( script["AddTen"]["sum"].getValue(), 1 )

			script["AddTen"]["enabled"].setValue( True )
			script["AddTen"]["op1"].setValue( 0 )

		assertPassThrough( s )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		assertPassThrough( s2 )

if __name__ == "__main__":
	unittest.main()
