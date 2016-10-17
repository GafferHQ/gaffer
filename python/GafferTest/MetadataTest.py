##########################################################################
#
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

import IECore

import Gaffer
import GafferTest

class MetadataTest( GafferTest.TestCase ) :

	class DerivedAddNode( GafferTest.AddNode ) :

		def __init__( self, name="DerivedAddNode" ) :

			GafferTest.AddNode.__init__( self, name )

	IECore.registerRunTimeTyped( DerivedAddNode )

	def testNodeDescription( self ) :

		add = GafferTest.AddNode()

		self.assertEqual( Gaffer.Metadata.nodeDescription( add ), "" )

		Gaffer.Metadata.registerNodeDescription( GafferTest.AddNode, "description" )
		self.assertEqual( Gaffer.Metadata.nodeDescription( add ), "description" )

		Gaffer.Metadata.registerNodeDescription( GafferTest.AddNode, lambda node : node.getName() )
		self.assertEqual( Gaffer.Metadata.nodeDescription( add ), "AddNode" )

		derivedAdd = self.DerivedAddNode()
		self.assertEqual( Gaffer.Metadata.nodeDescription( derivedAdd ), "DerivedAddNode" )
		self.assertEqual( Gaffer.Metadata.nodeDescription( derivedAdd, inherit=False ), "" )

		Gaffer.Metadata.registerNodeDescription( self.DerivedAddNode.staticTypeId(), "a not very helpful description" )
		self.assertEqual( Gaffer.Metadata.nodeDescription( derivedAdd ), "a not very helpful description" )
		self.assertEqual( Gaffer.Metadata.nodeDescription( add ), "AddNode" )

	def testExtendedNodeDescription( self ) :

		multiply = GafferTest.MultiplyNode()

		self.assertEqual( Gaffer.Metadata.nodeDescription( multiply ), "" )

		Gaffer.Metadata.registerNodeDescription(

			GafferTest.MultiplyNode,
			"description",

			"op1",
			"op1 description",

			"op2",
			{
				"description" : "op2 description",
				"otherValue" : 100,
			}

		)

		self.assertEqual( Gaffer.Metadata.nodeDescription( multiply ), "description" )
		self.assertEqual( Gaffer.Metadata.plugDescription( multiply["op1"] ), "op1 description" )
		self.assertEqual( Gaffer.Metadata.plugDescription( multiply["op2"] ), "op2 description" )
		self.assertEqual( Gaffer.Metadata.value( multiply["op2"], "otherValue" ), 100 )

	def testPlugDescription( self ) :

		add = GafferTest.AddNode()

		self.assertEqual( Gaffer.Metadata.plugDescription( add["op1"] ), "" )

		Gaffer.Metadata.registerPlugDescription( GafferTest.AddNode.staticTypeId(), "op1", "The first operand" )
		self.assertEqual( Gaffer.Metadata.plugDescription( add["op1"] ), "The first operand" )

		Gaffer.Metadata.registerPlugDescription( GafferTest.AddNode.staticTypeId(), "op1", lambda plug : plug.getName() + " description" )
		self.assertEqual( Gaffer.Metadata.plugDescription( add["op1"] ), "op1 description" )

		derivedAdd = self.DerivedAddNode()
		self.assertEqual( Gaffer.Metadata.plugDescription( derivedAdd["op1"] ), "op1 description" )
		self.assertEqual( Gaffer.Metadata.plugDescription( derivedAdd["op1"], inherit=False ), "" )

		Gaffer.Metadata.registerPlugDescription( self.DerivedAddNode, "op*", "derived class description" )
		self.assertEqual( Gaffer.Metadata.plugDescription( derivedAdd["op1"] ), "derived class description" )
		self.assertEqual( Gaffer.Metadata.plugDescription( derivedAdd["op2"] ), "derived class description" )

		self.assertEqual( Gaffer.Metadata.plugDescription( add["op1"] ), "op1 description" )
		self.assertEqual( Gaffer.Metadata.plugDescription( add["op2"] ), "" )

	def testArbitraryValues( self ) :

		add = GafferTest.AddNode()

		self.assertEqual( Gaffer.Metadata.value( add, "aKey" ), None )
		self.assertEqual( Gaffer.Metadata.value( add["op1"], "aKey" ), None )

		Gaffer.Metadata.registerValue( GafferTest.AddNode, "aKey", "something" )
		Gaffer.Metadata.registerValue( GafferTest.AddNode, "op*", "aKey", "somethingElse" )

		self.assertEqual( Gaffer.Metadata.value( add, "aKey" ), "something" )
		self.assertEqual( Gaffer.Metadata.value( add["op1"], "aKey" ), "somethingElse" )

	def testInheritance( self ) :

		Gaffer.Metadata.registerValue( GafferTest.AddNode, "iKey", "Base class value" )

		derivedAdd = self.DerivedAddNode()
		self.assertEqual( Gaffer.Metadata.value( derivedAdd, "iKey" ), "Base class value" )

		Gaffer.Metadata.registerValue( self.DerivedAddNode, "iKey", "Derived class value" )

		Gaffer.Metadata.registerValue( GafferTest.AddNode, "op1", "iKey", "Base class plug value" )
		self.assertEqual( Gaffer.Metadata.value( derivedAdd["op1"], "iKey" ), "Base class plug value" )

		Gaffer.Metadata.registerValue( self.DerivedAddNode, "op1", "iKey", "Derived class plug value" )

	def testNodeSignals( self ) :

		ns = GafferTest.CapturingSlot( Gaffer.Metadata.nodeValueChangedSignal() )
		ps = GafferTest.CapturingSlot( Gaffer.Metadata.plugValueChangedSignal() )

		Gaffer.Metadata.registerValue( GafferTest.AddNode, "k", "something" )

		self.assertEqual( len( ps ), 0 )
		self.assertEqual( len( ns ), 1 )
		self.assertEqual( ns[0], ( GafferTest.AddNode.staticTypeId(), "k", None ) )

		Gaffer.Metadata.registerValue( GafferTest.AddNode, "k", "somethingElse" )

		self.assertEqual( len( ps ), 0 )
		self.assertEqual( len( ns ), 2 )
		self.assertEqual( ns[1], ( GafferTest.AddNode.staticTypeId(), "k", None ) )

	def testPlugSignals( self ) :

		ns = GafferTest.CapturingSlot( Gaffer.Metadata.nodeValueChangedSignal() )
		ps = GafferTest.CapturingSlot( Gaffer.Metadata.plugValueChangedSignal() )

		Gaffer.Metadata.registerValue( GafferTest.AddNode, "op1", "k", "something" )

		self.assertEqual( len( ps ), 1 )
		self.assertEqual( len( ns ), 0 )
		self.assertEqual( ps[0], ( GafferTest.AddNode.staticTypeId(), "op1", "k", None ) )

		Gaffer.Metadata.registerValue( GafferTest.AddNode, "op1", "k", "somethingElse" )

		self.assertEqual( len( ps ), 2 )
		self.assertEqual( len( ns ), 0 )
		self.assertEqual( ps[1], ( GafferTest.AddNode.staticTypeId(), "op1", "k", None ) )

	def testSignalsDontExposeInternedStrings( self ) :

		cs = GafferTest.CapturingSlot( Gaffer.Metadata.nodeValueChangedSignal() )
		Gaffer.Metadata.registerValue( GafferTest.AddNode, "k", "aaa" )
		self.assertTrue( type( cs[0][1] ) is str )

		cs = GafferTest.CapturingSlot( Gaffer.Metadata.plugValueChangedSignal() )
		Gaffer.Metadata.registerValue( GafferTest.AddNode, "op1", "k", "bbb" )
		self.assertTrue( type( cs[0][1] ) is str )
		self.assertTrue( type( cs[0][2] ) is str )

	def testInstanceMetadata( self ) :

		Gaffer.Metadata.registerValue( GafferTest.AddNode.staticTypeId(), "imt", "globalNodeValue" )
		Gaffer.Metadata.registerValue( GafferTest.AddNode.staticTypeId(), "op1", "imt", "globalPlugValue" )

		n = GafferTest.AddNode()

		self.assertEqual( Gaffer.Metadata.value( n, "imt" ), "globalNodeValue" )
		self.assertEqual( Gaffer.Metadata.value( n["op1"], "imt" ), "globalPlugValue" )

		Gaffer.Metadata.registerValue( n, "imt", "instanceNodeValue" )
		Gaffer.Metadata.registerValue( n["op1"], "imt", "instancePlugValue" )

		self.assertEqual( Gaffer.Metadata.value( n, "imt" ), "instanceNodeValue" )
		self.assertEqual( Gaffer.Metadata.value( n["op1"], "imt" ), "instancePlugValue" )

		Gaffer.Metadata.registerValue( n, "imt", None )
		Gaffer.Metadata.registerValue( n["op1"], "imt", None )

		self.assertEqual( Gaffer.Metadata.value( n, "imt" ), None )
		self.assertEqual( Gaffer.Metadata.value( n["op1"], "imt" ), None )

	def testInstanceMetadataUndo( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()

		self.assertEqual( Gaffer.Metadata.value( s["n"], "undoTest" ), None )
		self.assertEqual( Gaffer.Metadata.value( s["n"]["op1"], "undoTest" ), None )

		with Gaffer.UndoContext( s ) :
			Gaffer.Metadata.registerValue( s["n"], "undoTest", "instanceNodeValue" )
			Gaffer.Metadata.registerValue( s["n"]["op1"], "undoTest", "instancePlugValue" )

		self.assertEqual( Gaffer.Metadata.value( s["n"], "undoTest" ), "instanceNodeValue" )
		self.assertEqual( Gaffer.Metadata.value( s["n"]["op1"], "undoTest" ), "instancePlugValue" )

		with Gaffer.UndoContext( s ) :
			Gaffer.Metadata.registerValue( s["n"], "undoTest", "instanceNodeValue2" )
			Gaffer.Metadata.registerValue( s["n"]["op1"], "undoTest", "instancePlugValue2" )

		self.assertEqual( Gaffer.Metadata.value( s["n"], "undoTest" ), "instanceNodeValue2" )
		self.assertEqual( Gaffer.Metadata.value( s["n"]["op1"], "undoTest" ), "instancePlugValue2" )

		s.undo()

		self.assertEqual( Gaffer.Metadata.value( s["n"], "undoTest" ), "instanceNodeValue" )
		self.assertEqual( Gaffer.Metadata.value( s["n"]["op1"], "undoTest" ), "instancePlugValue" )

		s.undo()

		self.assertEqual( Gaffer.Metadata.value( s["n"], "undoTest" ), None )
		self.assertEqual( Gaffer.Metadata.value( s["n"]["op1"], "undoTest" ), None )

		s.redo()

		self.assertEqual( Gaffer.Metadata.value( s["n"], "undoTest" ), "instanceNodeValue" )
		self.assertEqual( Gaffer.Metadata.value( s["n"]["op1"], "undoTest" ), "instancePlugValue" )

		s.redo()

		self.assertEqual( Gaffer.Metadata.value( s["n"], "undoTest" ), "instanceNodeValue2" )
		self.assertEqual( Gaffer.Metadata.value( s["n"]["op1"], "undoTest" ), "instancePlugValue2" )

	def testInstanceMetadataSignals( self ) :

		n = GafferTest.AddNode()

		ncs = GafferTest.CapturingSlot( Gaffer.Metadata.nodeValueChangedSignal() )
		pcs = GafferTest.CapturingSlot( Gaffer.Metadata.plugValueChangedSignal() )

		Gaffer.Metadata.registerValue( n, "signalTest", 1 )
		Gaffer.Metadata.registerValue( n["op1"], "signalTest", 1 )

		self.assertEqual( len( ncs ), 1 )
		self.assertEqual( len( pcs ), 1 )
		self.assertEqual( ncs[0], ( GafferTest.AddNode.staticTypeId(), "signalTest", n ) )
		self.assertEqual( pcs[0], ( GafferTest.AddNode.staticTypeId(), "op1", "signalTest", n["op1"] ) )

		Gaffer.Metadata.registerValue( n, "signalTest", 1 )
		Gaffer.Metadata.registerValue( n["op1"], "signalTest", 1 )

		self.assertEqual( len( ncs ), 1 )
		self.assertEqual( len( pcs ), 1 )

		Gaffer.Metadata.registerValue( n, "signalTest", 2 )
		Gaffer.Metadata.registerValue( n["op1"], "signalTest", 2 )

		self.assertEqual( len( ncs ), 2 )
		self.assertEqual( len( pcs ), 2 )
		self.assertEqual( ncs[1], ( GafferTest.AddNode.staticTypeId(), "signalTest", n ) )
		self.assertEqual( pcs[1], ( GafferTest.AddNode.staticTypeId(), "op1", "signalTest", n["op1"] ) )

	def testSerialisation( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = GafferTest.AddNode()

		Gaffer.Metadata.registerValue( s["n"], "serialisationTest", 1 )
		Gaffer.Metadata.registerValue( s["n"]["op1"], "serialisationTest", 2 )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( Gaffer.Metadata.value( s2["n"], "serialisationTest" ), 1 )
		self.assertEqual( Gaffer.Metadata.value( s2["n"]["op1"], "serialisationTest" ), 2 )

	def testStringSerialisationWithNewlinesAndQuotes( self ) :

		trickyStrings = [
			"Paragraph 1\n\nParagraph 2",
			"'Quote'",
			"Apostrophe's",
			'"Double quote"',
		]

		script = Gaffer.ScriptNode()

		script["n"] = Gaffer.Node()
		for s in trickyStrings :
			p = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
			script["n"]["user"].addChild( p )
			Gaffer.Metadata.registerValue( p, "description", s )

		script2 = Gaffer.ScriptNode()
		script2.execute( script.serialise() )

		for p, s in zip( script2["n"]["user"].children(), trickyStrings ) :
			self.assertEqual( Gaffer.Metadata.plugDescription( p ), s )

	def testRegisteredValues( self ) :

		n = GafferTest.AddNode()

		self.assertTrue( "r" not in Gaffer.Metadata.registeredValues( n ) )
		self.assertTrue( "rp" not in Gaffer.Metadata.registeredValues( n["op1"] ) )
		self.assertTrue( "ri" not in Gaffer.Metadata.registeredValues( n ) )
		self.assertTrue( "rpi" not in Gaffer.Metadata.registeredValues( n["op1"] ) )

		Gaffer.Metadata.registerValue( n.staticTypeId(), "r", 10 )
		Gaffer.Metadata.registerValue( n.staticTypeId(), "op1", "rp", 20 )

		self.assertTrue( "r" in Gaffer.Metadata.registeredValues( n ) )
		self.assertTrue( "rp" in Gaffer.Metadata.registeredValues( n["op1"] ) )
		self.assertTrue( "ri" not in Gaffer.Metadata.registeredValues( n ) )
		self.assertTrue( "rpi" not in Gaffer.Metadata.registeredValues( n["op1"] ) )

		Gaffer.Metadata.registerValue( n, "ri", 10 )
		Gaffer.Metadata.registerValue( n["op1"], "rpi", 20 )

		self.assertTrue( "r" in Gaffer.Metadata.registeredValues( n ) )
		self.assertTrue( "rp" in Gaffer.Metadata.registeredValues( n["op1"] ) )
		self.assertTrue( "ri" in Gaffer.Metadata.registeredValues( n ) )
		self.assertTrue( "rpi" in Gaffer.Metadata.registeredValues( n["op1"] ) )

		self.assertTrue( "r" not in Gaffer.Metadata.registeredValues( n, instanceOnly=True ) )
		self.assertTrue( "rp" not in Gaffer.Metadata.registeredValues( n["op1"], instanceOnly=True ) )
		self.assertTrue( "ri" in Gaffer.Metadata.registeredValues( n ) )
		self.assertTrue( "rpi" in Gaffer.Metadata.registeredValues( n["op1"] ) )

	def testInstanceDestruction( self ) :

		for i in range( 0, 1000 ) :
			p = Gaffer.Plug()
			n = Gaffer.Node()
			self.assertEqual( Gaffer.Metadata.value( p, "destructionTest" ), None )
			self.assertEqual( Gaffer.Metadata.value( n, "destructionTest" ), None )
			Gaffer.Metadata.registerValue( p, "destructionTest", 10 )
			Gaffer.Metadata.registerValue( n, "destructionTest", 20 )
			self.assertEqual( Gaffer.Metadata.value( p, "destructionTest" ), 10 )
			self.assertEqual( Gaffer.Metadata.value( n, "destructionTest" ), 20 )
			del p
			del n

	def testOrder( self ) :

		class MetadataTestNodeA( Gaffer.Node ) :

			def __init__( self, name = "MetadataTestNodeOne" ) :

				Gaffer.Node.__init__( self, name )

				self["a"] = Gaffer.IntPlug()

		IECore.registerRunTimeTyped( MetadataTestNodeA )

		class MetadataTestNodeB( MetadataTestNodeA ) :

			def __init__( self, name = "MetadataTestNodeOne" ) :

				MetadataTestNodeA.__init__( self, name )

		IECore.registerRunTimeTyped( MetadataTestNodeB )

		# test node registrations

		node = MetadataTestNodeB()

		Gaffer.Metadata.registerValue( node, "nodeSeven", 7 )
		Gaffer.Metadata.registerValue( node, "nodeEight", 8 )
		Gaffer.Metadata.registerValue( node, "nodeNine", 9 )

		Gaffer.Metadata.registerValue( MetadataTestNodeB, "nodeFour", 4 )
		Gaffer.Metadata.registerValue( MetadataTestNodeB, "nodeFive", 5 )
		Gaffer.Metadata.registerValue( MetadataTestNodeB, "nodeSix", 6 )

		Gaffer.Metadata.registerValue( MetadataTestNodeA, "nodeOne", 1 )
		Gaffer.Metadata.registerValue( MetadataTestNodeA, "nodeTwo", 2 )
		Gaffer.Metadata.registerValue( MetadataTestNodeA, "nodeThree", 3 )

		self.assertEqual(
			Gaffer.Metadata.registeredValues( node ),
			[
				# base class values first, in order of their registration
				"nodeOne",
				"nodeTwo",
				"nodeThree",
				# derived class values next, in order of their registration
				"nodeFour",
				"nodeFive",
				"nodeSix",
				# instance values last, in order of their registration
				"nodeSeven",
				"nodeEight",
				"nodeNine",
			]
		)

		# test plug registrations

		Gaffer.Metadata.registerValue( node["a"], "plugSeven", 7 )
		Gaffer.Metadata.registerValue( node["a"], "plugEight", 8 )
		Gaffer.Metadata.registerValue( node["a"], "plugNine", 9 )

		Gaffer.Metadata.registerValue( MetadataTestNodeB, "a", "plugFour", 4 )
		Gaffer.Metadata.registerValue( MetadataTestNodeB, "a", "plugFive", 5 )
		Gaffer.Metadata.registerValue( MetadataTestNodeB, "a", "plugSix", 6 )

		Gaffer.Metadata.registerValue( MetadataTestNodeA, "a", "plugOne", 1 )
		Gaffer.Metadata.registerValue( MetadataTestNodeA, "a", "plugTwo", 2 )
		Gaffer.Metadata.registerValue( MetadataTestNodeA, "a", "plugThree", 3 )

		self.assertEqual(
			Gaffer.Metadata.registeredValues( node["a"] ),
			[
				# base class values first, in order of their registration
				"plugOne",
				"plugTwo",
				"plugThree",
				# derived class values next, in order of their registration
				"plugFour",
				"plugFive",
				"plugSix",
				# instance values last, in order of their registration
				"plugSeven",
				"plugEight",
				"plugNine",
			]
		)

	def testThreading( self ) :

		GafferTest.testMetadataThreading()

	def testVectorTypes( self ) :

		n = Gaffer.Node()

		Gaffer.Metadata.registerValue( n, "stringVector", IECore.StringVectorData( [ "a", "b", "c" ] ) )
		self.assertEqual( Gaffer.Metadata.value( n, "stringVector" ), IECore.StringVectorData( [ "a", "b", "c" ] ) )

		Gaffer.Metadata.registerValue( n, "intVector", IECore.IntVectorData( [ 1, 2, 3 ] ) )
		self.assertEqual( Gaffer.Metadata.value( n, "intVector" ), IECore.IntVectorData( [ 1, 2, 3 ] ) )

	def testCopy( self ) :

		n = Gaffer.Node()

		s = IECore.StringVectorData( [ "a", "b", "c" ] )
		Gaffer.Metadata.registerValue( n, "stringVector", s )

		s2 = Gaffer.Metadata.value( n, "stringVector" )
		self.assertEqual( s, s2 )
		self.assertFalse( s.isSame( s2 ) )

		s3 = Gaffer.Metadata.value( n, "stringVector", _copy = False )
		self.assertEqual( s, s3 )
		self.assertTrue( s.isSame( s3 ) )

	def testBadSlotsDontAffectGoodSlots( self ) :

		def badSlot( nodeTypeId, key, node ) :

			raise Exception( "Oops" )

		self.__goodSlotExecuted = False
		def goodSlot( nodeTypeId, key, node ) :

			self.__goodSlotExecuted = True

		badConnection = Gaffer.Metadata.nodeValueChangedSignal().connect( badSlot )
		goodConnection = Gaffer.Metadata.nodeValueChangedSignal().connect( goodSlot )

		n = Gaffer.Node()
		with IECore.CapturingMessageHandler() as mh :
			Gaffer.Metadata.registerValue( n, "test", 10 )

		self.assertTrue( self.__goodSlotExecuted )

		self.assertEqual( len( mh.messages ), 1 )
		self.assertTrue( "Oops" in mh.messages[0].message )

	def testRegisterNode( self ) :

		class MetadataTestNodeC( Gaffer.Node ) :

			def __init__( self, name = "MetadataTestNodeC" ) :

				Gaffer.Node.__init__( self, name )

				self["a"] = Gaffer.IntPlug()
				self["b"] = Gaffer.IntPlug()

		IECore.registerRunTimeTyped( MetadataTestNodeC )

		Gaffer.Metadata.registerNode(

			MetadataTestNodeC,

			"description",
			"""
			I am a multi
			line description
			""",

			"nodeGadget:color", IECore.Color3f( 1, 0, 0 ),

			plugs = {
				"a" : [
					"description",
					"""Another multi
					line description""",

					"preset:One", 1,
					"preset:Two", 2,
					"preset:Three", 3,
				],
				"b" : (
					"description",
					"""
					I am the first paragraph.

					I am the second paragraph.
					""",
					"otherValue", 100,
				)
			}

		)

		n = MetadataTestNodeC()

		self.assertEqual( Gaffer.Metadata.value( n, "description" ), "I am a multi\nline description" )
		self.assertEqual( Gaffer.Metadata.value( n, "nodeGadget:color" ), IECore.Color3f( 1, 0, 0 ) )

		self.assertEqual( Gaffer.Metadata.value( n["a"], "description" ), "Another multi\nline description" )
		self.assertEqual( Gaffer.Metadata.value( n["a"], "preset:One" ), 1 )
		self.assertEqual( Gaffer.Metadata.value( n["a"], "preset:Two" ), 2 )
		self.assertEqual( Gaffer.Metadata.value( n["a"], "preset:Three" ), 3 )
		self.assertEqual( Gaffer.Metadata.registeredValues( n["a"] ), [ "description", "preset:One", "preset:Two", "preset:Three" ] )

		self.assertEqual( Gaffer.Metadata.value( n["b"], "description" ), "I am the first paragraph.\n\nI am the second paragraph." )
		self.assertEqual( Gaffer.Metadata.value( n["b"], "otherValue" ), 100 )

	def testPersistenceOfInstanceValues( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()

		Gaffer.Metadata.registerValue( s["n"], "persistent1", 1 )
		Gaffer.Metadata.registerValue( s["n"], "persistent2", 2, persistent = True )
		Gaffer.Metadata.registerValue( s["n"], "nonpersistent", 3, persistent = False )

		Gaffer.Metadata.registerValue( s["n"]["op1"], "persistent1", "one" )
		Gaffer.Metadata.registerValue( s["n"]["op1"], "persistent2", "two", persistent = True )
		Gaffer.Metadata.registerValue( s["n"]["op1"], "nonpersistent", "three", persistent = False )

		self.assertEqual( Gaffer.Metadata.value( s["n"], "persistent1" ), 1 )
		self.assertEqual( Gaffer.Metadata.value( s["n"], "persistent2" ), 2 )
		self.assertEqual( Gaffer.Metadata.value( s["n"], "nonpersistent" ), 3 )

		self.assertEqual( Gaffer.Metadata.value( s["n"]["op1"], "persistent1" ), "one" )
		self.assertEqual( Gaffer.Metadata.value( s["n"]["op1"], "persistent2" ), "two" )
		self.assertEqual( Gaffer.Metadata.value( s["n"]["op1"], "nonpersistent" ), "three" )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( Gaffer.Metadata.value( s2["n"], "persistent1" ), 1 )
		self.assertEqual( Gaffer.Metadata.value( s2["n"], "persistent2" ), 2 )
		self.assertEqual( Gaffer.Metadata.value( s2["n"], "nonpersistent" ), None )

		self.assertEqual( Gaffer.Metadata.value( s2["n"]["op1"], "persistent1" ), "one" )
		self.assertEqual( Gaffer.Metadata.value( s2["n"]["op1"], "persistent2" ), "two" )
		self.assertEqual( Gaffer.Metadata.value( s2["n"]["op1"], "nonpersistent" ), None )

	def testUndoOfPersistentInstanceValues( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()

		def assertNonExistent() :

			self.assertEqual( Gaffer.Metadata.value( s["n"], "a" ), None )
			self.assertEqual( Gaffer.Metadata.value( s["n"]["op1"], "b" ), None )

		def assertPersistent() :

			self.assertEqual( Gaffer.Metadata.registeredValues( s["n"], instanceOnly = True ), [ "a" ] )
			self.assertEqual( Gaffer.Metadata.registeredValues( s["n"]["op1"], instanceOnly = True ), [ "b" ] )
			self.assertEqual( Gaffer.Metadata.registeredValues( s["n"], instanceOnly = True, persistentOnly = True ), [ "a" ] )
			self.assertEqual( Gaffer.Metadata.registeredValues( s["n"]["op1"], instanceOnly = True, persistentOnly = True ), [ "b" ] )
			self.assertEqual( Gaffer.Metadata.value( s["n"], "a" ), 1 )
			self.assertEqual( Gaffer.Metadata.value( s["n"]["op1"], "b" ), 2 )

		def assertNonPersistent() :

			self.assertEqual( Gaffer.Metadata.registeredValues( s["n"], instanceOnly = True ), [ "a" ] )
			self.assertEqual( Gaffer.Metadata.registeredValues( s["n"]["op1"], instanceOnly = True ), [ "b" ] )
			self.assertEqual( Gaffer.Metadata.registeredValues( s["n"], instanceOnly = True, persistentOnly = True ), [] )
			self.assertEqual( Gaffer.Metadata.registeredValues( s["n"]["op1"], instanceOnly = True, persistentOnly = True ), [] )
			self.assertEqual( Gaffer.Metadata.value( s["n"], "a" ), 1 )
			self.assertEqual( Gaffer.Metadata.value( s["n"]["op1"], "b" ), 2 )

		assertNonExistent()

		with Gaffer.UndoContext( s ) :

			Gaffer.Metadata.registerValue( s["n"], "a", 1, persistent = True )
			Gaffer.Metadata.registerValue( s["n"]["op1"], "b", 2, persistent = True )

		assertPersistent()

		with Gaffer.UndoContext( s ) :

			Gaffer.Metadata.registerValue( s["n"], "a", 1, persistent = False )
			Gaffer.Metadata.registerValue( s["n"]["op1"], "b", 2, persistent = False )

		assertNonPersistent()

		s.undo()
		assertPersistent()

		s.undo()
		assertNonExistent()

		s.redo()
		assertPersistent()

		s.redo()
		assertNonPersistent()

	def testChangeOfPersistenceSignals( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()

		ncs = GafferTest.CapturingSlot( Gaffer.Metadata.nodeValueChangedSignal() )
		pcs = GafferTest.CapturingSlot( Gaffer.Metadata.plugValueChangedSignal() )

		self.assertEqual( len( ncs ), 0 )
		self.assertEqual( len( pcs ), 0 )

		Gaffer.Metadata.registerValue( s["n"], "a", 1, persistent = False )
		Gaffer.Metadata.registerValue( s["n"]["op1"], "b", 2, persistent = False )

		self.assertEqual( len( ncs ), 1 )
		self.assertEqual( len( pcs ), 1 )

		Gaffer.Metadata.registerValue( s["n"], "a", 1, persistent = True )
		Gaffer.Metadata.registerValue( s["n"]["op1"], "b", 2, persistent = True )

		self.assertEqual( len( ncs ), 2 )
		self.assertEqual( len( pcs ), 2 )

		Gaffer.Metadata.registerValue( s["n"], "a", 1, persistent = False )
		Gaffer.Metadata.registerValue( s["n"]["op1"], "b", 2, persistent = False )

		self.assertEqual( len( ncs ), 3 )
		self.assertEqual( len( pcs ), 3 )

	def testExactPreferredToWildcards( self ) :

		class MetadataTestNodeD( Gaffer.Node ) :

			def __init__( self, name = "MetadataTestNodeD" ) :

				Gaffer.Node.__init__( self, name )

				self["a"] = Gaffer.IntPlug()
				self["b"] = Gaffer.IntPlug()

		IECore.registerRunTimeTyped( MetadataTestNodeD )

		Gaffer.Metadata.registerNode(

			MetadataTestNodeD,

			plugs = {
				"*" : [
					"test", "wildcard",
				],
				"a" :[
					"test", "exact",
				],
			}

		)

		n = MetadataTestNodeD()

		self.assertEqual( Gaffer.Metadata.value( n["a"], "test" ), "exact" )
		self.assertEqual( Gaffer.Metadata.value( n["b"], "test" ), "wildcard" )

	def testNoSerialiseAfterUndo( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()

		self.assertFalse( "Metadata" in s.serialise() )

		with Gaffer.UndoContext( s ) :
			Gaffer.Metadata.registerValue( s["n"], "test", 1 )

		self.assertTrue( "Metadata" in s.serialise() )

		s.undo()
		self.assertFalse( "Metadata" in s.serialise() )

	def testNoneMasksOthers( self ) :

		n = GafferTest.AddNode()
		self.assertEqual( Gaffer.Metadata.value( n, "maskTest" ), None )

		Gaffer.Metadata.registerValue( Gaffer.DependencyNode, "maskTest", 10 )
		self.assertEqual( Gaffer.Metadata.value( n, "maskTest" ), 10 )

		Gaffer.Metadata.registerValue( Gaffer.ComputeNode, "maskTest", None )
		self.assertEqual( Gaffer.Metadata.value( n, "maskTest" ), None )

		Gaffer.Metadata.registerValue( GafferTest.AddNode, "maskTest", 20 )
		self.assertEqual( Gaffer.Metadata.value( n, "maskTest" ), 20 )

		Gaffer.Metadata.registerValue( n, "maskTest", 30 )
		self.assertEqual( Gaffer.Metadata.value( n, "maskTest" ), 30 )

		Gaffer.Metadata.registerValue( n, "maskTest", None )
		self.assertEqual( Gaffer.Metadata.value( n, "maskTest" ), None )

	def testDeregisterNodeValue( self ) :

		n = GafferTest.AddNode()
		self.assertEqual( Gaffer.Metadata.value( n, "deleteMe" ), None )

		Gaffer.Metadata.registerValue( Gaffer.Node, "deleteMe", 10 )
		self.assertEqual( Gaffer.Metadata.value( n, "deleteMe" ), 10 )

		Gaffer.Metadata.registerValue( Gaffer.ComputeNode, "deleteMe", 20 )
		self.assertEqual( Gaffer.Metadata.value( n, "deleteMe" ), 20 )

		Gaffer.Metadata.deregisterValue( Gaffer.ComputeNode, "deleteMe" )
		self.assertEqual( Gaffer.Metadata.value( n, "deleteMe" ), 10 )

		Gaffer.Metadata.deregisterValue( Gaffer.Node, "deleteMe" )
		self.assertEqual( Gaffer.Metadata.value( n, "deleteMe" ), None )

	def testDeregisterNodeInstanceValue( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()

		self.assertEqual( Gaffer.Metadata.value( s["n"], "deleteMe" ), None )

		Gaffer.Metadata.registerValue( GafferTest.AddNode, "deleteMe", 10 )
		self.assertEqual( Gaffer.Metadata.value( s["n"], "deleteMe" ), 10 )

		Gaffer.Metadata.registerValue( s["n"], "deleteMe", 20 )
		self.assertEqual( Gaffer.Metadata.value( s["n"], "deleteMe" ), 20 )
		self.assertTrue( "Metadata" in s.serialise() )

		with Gaffer.UndoContext( s ) :
			Gaffer.Metadata.deregisterValue( s["n"], "deleteMe" )
			self.assertTrue( "Metadata" not in s.serialise() )
			self.assertEqual( Gaffer.Metadata.value( s["n"], "deleteMe" ), 10 )

		s.undo()
		self.assertEqual( Gaffer.Metadata.value( s["n"], "deleteMe" ), 20 )
		self.assertTrue( "Metadata" in s.serialise() )

		s.redo()
		self.assertEqual( Gaffer.Metadata.value( s["n"], "deleteMe" ), 10 )
		self.assertTrue( "Metadata" not in s.serialise() )

		Gaffer.Metadata.deregisterValue( GafferTest.AddNode, "deleteMe" )
		self.assertEqual( Gaffer.Metadata.value( s["n"], "deleteMe" ), None )

		self.assertTrue( "Metadata" not in s.serialise() )

	def testDeregisterPlugValue( self ) :

		n = GafferTest.AddNode()
		self.assertEqual( Gaffer.Metadata.value( n["op1"], "deleteMe" ), None )

		Gaffer.Metadata.registerValue( Gaffer.Node, "op1", "deleteMe", 10 )
		self.assertEqual( Gaffer.Metadata.value( n["op1"], "deleteMe" ), 10 )

		Gaffer.Metadata.deregisterValue( Gaffer.Node, "op1", "deleteMe" )
		self.assertEqual( Gaffer.Metadata.value( n["op1"], "deleteMe" ), None )

	def testDeregisterPlugInstanceValue( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()

		self.assertEqual( Gaffer.Metadata.value( s["n"]["op1"], "deleteMe" ), None )

		Gaffer.Metadata.registerValue( GafferTest.AddNode, "op1", "deleteMe", 10 )
		self.assertEqual( Gaffer.Metadata.value( s["n"]["op1"], "deleteMe" ), 10 )
		self.assertTrue( "Metadata" not in s.serialise() )

		Gaffer.Metadata.registerValue( s["n"]["op1"], "deleteMe", 20 )
		self.assertEqual( Gaffer.Metadata.value( s["n"]["op1"], "deleteMe" ), 20 )
		self.assertTrue( "Metadata" in s.serialise() )

		with Gaffer.UndoContext( s ) :
			Gaffer.Metadata.deregisterValue( s["n"]["op1"], "deleteMe" )
			self.assertTrue( "Metadata" not in s.serialise() )
			self.assertEqual( Gaffer.Metadata.value( s["n"]["op1"], "deleteMe" ), 10 )

		s.undo()
		self.assertEqual( Gaffer.Metadata.value( s["n"]["op1"], "deleteMe" ), 20 )
		self.assertTrue( "Metadata" in s.serialise() )

		s.redo()
		self.assertEqual( Gaffer.Metadata.value( s["n"]["op1"], "deleteMe" ), 10 )
		self.assertTrue( "Metadata" not in s.serialise() )

		Gaffer.Metadata.deregisterValue( GafferTest.AddNode, "op1", "deleteMe" )
		self.assertEqual( Gaffer.Metadata.value( s["n"]["op1"], "deleteMe" ), None )

		self.assertTrue( "Metadata" not in s.serialise() )

	def testComponentsWithMetaData( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()
		s["n2"] = GafferTest.AddNode()
		s["n3"] = GafferTest.AddNode()
		s["m"] = GafferTest.MultiplyNode()

		self.assertEqual( Gaffer.Metadata.nodesWithMetadata( s, "nodeData1"), [] )

		# register instance node values on n and n2:
		Gaffer.Metadata.registerValue( s["n"], "nodeData1", "something" )
		Gaffer.Metadata.registerValue( s["n2"], "nodeData2", "something" )
		Gaffer.Metadata.registerValue( s["m"], "nodeData3", "something" )
		Gaffer.Metadata.registerValue( s["n"], "nodeData3", "something" )

		# register class value on GafferTest.AddNode:
		Gaffer.Metadata.registerValue( GafferTest.AddNode, "nodeData3", "something" )

		# register some instance plug values:
		Gaffer.Metadata.registerValue( s["n"]["op1"], "plugData1", "something" )
		Gaffer.Metadata.registerValue( s["n2"]["op2"], "plugData2", "something" )
		Gaffer.Metadata.registerValue( s["m"]["op2"], "plugData3", "something" )
		Gaffer.Metadata.registerValue( s["m"]["op1"], "plugData3", "something" )

		# register class value on GafferTest.AddNode:
		Gaffer.Metadata.registerValue( GafferTest.AddNode, "op1", "plugData3", "somethingElse" )

		# test it lists nodes with matching data:
		self.assertEqual( Gaffer.Metadata.nodesWithMetadata( s, "nodeData1" ), [ s["n"] ] )
		self.assertEqual( Gaffer.Metadata.nodesWithMetadata( s, "nodeData2" ), [ s["n2"] ] )
		self.assertEqual( Gaffer.Metadata.nodesWithMetadata( s, "nodeData3" ), [ s["n"], s["n2"], s["n3"], s["m"] ] )
		self.assertEqual( set(Gaffer.Metadata.nodesWithMetadata( s, "nodeData3", instanceOnly=True )), set([ s["n"], s["m"] ]) )

		# telling it to list plugs should make it return an empty list:
		self.assertEqual( Gaffer.Metadata.plugsWithMetadata( s, "nodeData1" ), [] )
		self.assertEqual( Gaffer.Metadata.plugsWithMetadata( s, "nodeData3" ), [] )

		# test it lists plugs with matching data:
		self.assertEqual( Gaffer.Metadata.plugsWithMetadata( s, "plugData1" ), [ s["n"]["op1"] ] )
		self.assertEqual( Gaffer.Metadata.plugsWithMetadata( s, "plugData2" ), [ s["n2"]["op2"] ] )
		self.assertEqual( Gaffer.Metadata.plugsWithMetadata( s, "plugData3" ), [ s["n"]["op1"], s["n2"]["op1"], s["n3"]["op1"], s["m"]["op1"], s["m"]["op2"] ] )
		self.assertEqual( set( Gaffer.Metadata.plugsWithMetadata( s, "plugData3", instanceOnly=True ) ), set( [ s["m"]["op1"], s["m"]["op2"] ] ) )

		# telling it to list nodes should make it return an empty list:
		self.assertEqual( Gaffer.Metadata.nodesWithMetadata( s, "plugData1" ), [] )
		self.assertEqual( Gaffer.Metadata.nodesWithMetadata( s, "plugData3" ), [] )

		# test child removal:
		m = s["m"]
		s.removeChild( m )
		self.assertEqual( Gaffer.Metadata.plugsWithMetadata( s, "plugData3", instanceOnly=True ), [] )
		self.assertEqual( Gaffer.Metadata.nodesWithMetadata( s, "nodeData3", instanceOnly=True ), [ s["n"] ] )

	def testNonNodeMetadata( self ) :

		cs = GafferTest.CapturingSlot( Gaffer.Metadata.valueChangedSignal() )
		self.assertEqual( len( cs ), 0 )

		Gaffer.Metadata.registerValue( "testTarget", "testInt", 1 )
		self.assertEqual( Gaffer.Metadata.value( "testTarget", "testInt" ), 1 )

		self.assertEqual( len( cs ), 1 )
		self.assertEqual( cs[0], ( "testTarget", "testInt" ) )

		intVectorData = IECore.IntVectorData( [ 1, 2 ] )
		Gaffer.Metadata.registerValue( "testTarget", "testIntVectorData", intVectorData )
		self.assertEqual( Gaffer.Metadata.value( "testTarget", "testIntVectorData" ), intVectorData )
		self.assertFalse( Gaffer.Metadata.value( "testTarget", "testIntVectorData" ).isSame( intVectorData ) )

		self.assertEqual( len( cs ), 2 )
		self.assertEqual( cs[1], ( "testTarget", "testIntVectorData" ) )

		Gaffer.Metadata.registerValue( "testTarget", "testDynamicValue", lambda : 20 )
		self.assertEqual( Gaffer.Metadata.value( "testTarget", "testDynamicValue" ), 20 )

		self.assertEqual( len( cs ), 3 )
		self.assertEqual( cs[2], ( "testTarget", "testDynamicValue" ) )

		names = Gaffer.Metadata.registeredValues( "testTarget" )
		self.assertTrue( "testInt" in names )
		self.assertTrue( "testIntVectorData" in names )
		self.assertTrue( "testDynamicValue" in names )
		self.assertTrue( names.index( "testInt" ) < names.index( "testIntVectorData" ) )
		self.assertTrue( names.index( "testIntVectorData" ) < names.index( "testDynamicValue" ) )

	def testSerialisationQuoting( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["p"] = Gaffer.Plug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		needsQuoting = """'"\n\\'!"""

		Gaffer.Metadata.registerValue( s["n"], "test", needsQuoting )
		Gaffer.Metadata.registerValue( s["n"], needsQuoting, "test" )
		Gaffer.Metadata.registerValue( s["n"]["p"], "test", needsQuoting )
		Gaffer.Metadata.registerValue( s["n"]["p"], needsQuoting, "test" )

		self.assertEqual( Gaffer.Metadata.value( s["n"], "test" ), needsQuoting )
		self.assertEqual( Gaffer.Metadata.value( s["n"], needsQuoting ), "test" )
		self.assertEqual( Gaffer.Metadata.value( s["n"]["p"], "test" ), needsQuoting )
		self.assertEqual( Gaffer.Metadata.value( s["n"]["p"], needsQuoting ), "test" )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( Gaffer.Metadata.value( s2["n"], "test" ), needsQuoting )
		self.assertEqual( Gaffer.Metadata.value( s2["n"], needsQuoting ), "test" )
		self.assertEqual( Gaffer.Metadata.value( s2["n"]["p"], "test" ), needsQuoting )
		self.assertEqual( Gaffer.Metadata.value( s2["n"]["p"], needsQuoting ), "test" )

	def testSerialisationOnlyUsesDataWhenNecessary( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["p"] = Gaffer.Plug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		for value in [
			"s",
			1,
			2.0,
			True,
			IECore.Color3f( 0 ),
			IECore.V2f( 0 ),
			IECore.V2i( 0 ),
			IECore.V3i( 0 ),
			IECore.StringVectorData( [ "one", "two" ] ),
			IECore.IntVectorData( [ 1, 2, 3 ] ),
		] :

			Gaffer.Metadata.registerValue( s["n"], "test", value )
			Gaffer.Metadata.registerValue( s["n"]["p"], "test", value )

			self.assertEqual( Gaffer.Metadata.value( s["n"], "test" ), value )
			self.assertEqual( Gaffer.Metadata.value( s["n"]["p"], "test" ), value )

			ss = s.serialise()
			if not isinstance( value, IECore.Data ) :
				self.assertTrue( "Data" not in ss )

			s2 = Gaffer.ScriptNode()
			s2.execute( ss )

			self.assertEqual( Gaffer.Metadata.value( s2["n"], "test" ), value )
			self.assertEqual( Gaffer.Metadata.value( s2["n"]["p"], "test" ), value )

	def testOverloadedMethods( self ) :

		n = GafferTest.AddNode()

		Gaffer.Metadata.registerValue( n, "one", 1 )
		Gaffer.Metadata.registerValue( n["op1"], "two", 2 )

		self.assertEqual( Gaffer.Metadata.registeredValues( n, instanceOnly = True ), [ "one" ] )
		self.assertEqual( Gaffer.Metadata.registeredValues( n["op1"], instanceOnly = True ), [ "two" ] )

		self.assertEqual( Gaffer.Metadata.value( n, "one" ), 1 )
		self.assertEqual( Gaffer.Metadata.value( n["op1"], "two" ), 2 )

		Gaffer.Metadata.deregisterValue( n, "one" )
		Gaffer.Metadata.deregisterValue( n["op1"], "two" )

		self.assertEqual( Gaffer.Metadata.registeredValues( n, instanceOnly = True ), [] )
		self.assertEqual( Gaffer.Metadata.registeredValues( n["op1"], instanceOnly = True ), [] )

if __name__ == "__main__":
	unittest.main()
