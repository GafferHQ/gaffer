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
		self.assertEqual( Gaffer.Metadata.plugValue( multiply["op2"], "otherValue" ), 100 )

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

		self.assertEqual( Gaffer.Metadata.nodeValue( add, "aKey" ), None )
		self.assertEqual( Gaffer.Metadata.plugValue( add["op1"], "aKey" ), None )

		Gaffer.Metadata.registerNodeValue( GafferTest.AddNode, "aKey", "something" )
		Gaffer.Metadata.registerPlugValue( GafferTest.AddNode, "op*", "aKey", "somethingElse" )

		self.assertEqual( Gaffer.Metadata.nodeValue( add, "aKey" ), "something" )
		self.assertEqual( Gaffer.Metadata.plugValue( add["op1"], "aKey" ), "somethingElse" )

	def testInheritance( self ) :

		Gaffer.Metadata.registerNodeValue( GafferTest.AddNode, "iKey", "Base class value" )

		derivedAdd = self.DerivedAddNode()
		self.assertEqual( Gaffer.Metadata.nodeValue( derivedAdd, "iKey" ), "Base class value" )
		self.assertEqual( Gaffer.Metadata.nodeValue( derivedAdd, "iKey", inherit=False ), None )

		Gaffer.Metadata.registerNodeValue( self.DerivedAddNode, "iKey", "Derived class value" )
		self.assertEqual( Gaffer.Metadata.nodeValue( derivedAdd, "iKey", inherit=False ), "Derived class value" )

		Gaffer.Metadata.registerPlugValue( GafferTest.AddNode, "op1", "iKey", "Base class plug value" )
		self.assertEqual( Gaffer.Metadata.plugValue( derivedAdd["op1"], "iKey" ), "Base class plug value" )
		self.assertEqual( Gaffer.Metadata.plugValue( derivedAdd["op1"], "iKey", inherit=False ), None )

		Gaffer.Metadata.registerPlugValue( self.DerivedAddNode, "op1", "iKey", "Derived class plug value" )
		self.assertEqual( Gaffer.Metadata.plugValue( derivedAdd["op1"], "iKey", inherit=False ), "Derived class plug value" )

	def testNodeSignals( self ) :

		ns = GafferTest.CapturingSlot( Gaffer.Metadata.nodeValueChangedSignal() )
		ps = GafferTest.CapturingSlot( Gaffer.Metadata.plugValueChangedSignal() )

		Gaffer.Metadata.registerNodeValue( GafferTest.AddNode, "k", "something" )

		self.assertEqual( len( ps ), 0 )
		self.assertEqual( len( ns ), 1 )
		self.assertEqual( ns[0], ( GafferTest.AddNode.staticTypeId(), "k" ) )

		Gaffer.Metadata.registerNodeValue( GafferTest.AddNode, "k", "somethingElse" )

		self.assertEqual( len( ps ), 0 )
		self.assertEqual( len( ns ), 2 )
		self.assertEqual( ns[1], ( GafferTest.AddNode.staticTypeId(), "k" ) )

	def testPlugSignals( self ) :

		ns = GafferTest.CapturingSlot( Gaffer.Metadata.nodeValueChangedSignal() )
		ps = GafferTest.CapturingSlot( Gaffer.Metadata.plugValueChangedSignal() )

		Gaffer.Metadata.registerPlugValue( GafferTest.AddNode, "op1", "k", "something" )

		self.assertEqual( len( ps ), 1 )
		self.assertEqual( len( ns ), 0 )
		self.assertEqual( ps[0], ( GafferTest.AddNode.staticTypeId(), "op1", "k" ) )

		Gaffer.Metadata.registerPlugValue( GafferTest.AddNode, "op1", "k", "somethingElse" )

		self.assertEqual( len( ps ), 2 )
		self.assertEqual( len( ns ), 0 )
		self.assertEqual( ps[1], ( GafferTest.AddNode.staticTypeId(), "op1", "k" ) )

	def testSignalsDontExposeInternedStrings( self ) :

		cs = GafferTest.CapturingSlot( Gaffer.Metadata.nodeValueChangedSignal() )
		Gaffer.Metadata.registerNodeValue( GafferTest.AddNode, "k", "aaa" )
		self.assertTrue( type( cs[0][1] ) is str )

		cs = GafferTest.CapturingSlot( Gaffer.Metadata.plugValueChangedSignal() )
		Gaffer.Metadata.registerPlugValue( GafferTest.AddNode, "op1", "k", "bbb" )
		self.assertTrue( type( cs[0][1] ) is str )
		self.assertTrue( type( cs[0][2] ) is str )

	def testInstanceMetadata( self ) :

		Gaffer.Metadata.registerNodeValue( GafferTest.AddNode.staticTypeId(), "imt", "globalNodeValue" )
		Gaffer.Metadata.registerPlugValue( GafferTest.AddNode.staticTypeId(), "op1", "imt", "globalPlugValue" )

		n = GafferTest.AddNode()

		self.assertEqual( Gaffer.Metadata.nodeValue( n, "imt" ), "globalNodeValue" )
		self.assertEqual( Gaffer.Metadata.plugValue( n["op1"], "imt" ), "globalPlugValue" )

		Gaffer.Metadata.registerNodeValue( n, "imt", "instanceNodeValue" )
		Gaffer.Metadata.registerPlugValue( n["op1"], "imt", "instancePlugValue" )

		self.assertEqual( Gaffer.Metadata.nodeValue( n, "imt" ), "instanceNodeValue" )
		self.assertEqual( Gaffer.Metadata.plugValue( n["op1"], "imt" ), "instancePlugValue" )

		Gaffer.Metadata.registerNodeValue( n, "imt", None )
		Gaffer.Metadata.registerPlugValue( n["op1"], "imt", None )

		self.assertEqual( Gaffer.Metadata.nodeValue( n, "imt" ), "globalNodeValue" )
		self.assertEqual( Gaffer.Metadata.plugValue( n["op1"], "imt" ), "globalPlugValue" )

	def testInstanceMetadataUndo( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()

		self.assertEqual( Gaffer.Metadata.nodeValue( s["n"], "undoTest" ), None )
		self.assertEqual( Gaffer.Metadata.plugValue( s["n"]["op1"], "undoTest" ), None )

		with Gaffer.UndoContext( s ) :
			Gaffer.Metadata.registerNodeValue( s["n"], "undoTest", "instanceNodeValue" )
			Gaffer.Metadata.registerPlugValue( s["n"]["op1"], "undoTest", "instancePlugValue" )

		self.assertEqual( Gaffer.Metadata.nodeValue( s["n"], "undoTest" ), "instanceNodeValue" )
		self.assertEqual( Gaffer.Metadata.plugValue( s["n"]["op1"], "undoTest" ), "instancePlugValue" )

		with Gaffer.UndoContext( s ) :
			Gaffer.Metadata.registerNodeValue( s["n"], "undoTest", "instanceNodeValue2" )
			Gaffer.Metadata.registerPlugValue( s["n"]["op1"], "undoTest", "instancePlugValue2" )

		self.assertEqual( Gaffer.Metadata.nodeValue( s["n"], "undoTest" ), "instanceNodeValue2" )
		self.assertEqual( Gaffer.Metadata.plugValue( s["n"]["op1"], "undoTest" ), "instancePlugValue2" )

		s.undo()

		self.assertEqual( Gaffer.Metadata.nodeValue( s["n"], "undoTest" ), "instanceNodeValue" )
		self.assertEqual( Gaffer.Metadata.plugValue( s["n"]["op1"], "undoTest" ), "instancePlugValue" )

		s.undo()

		self.assertEqual( Gaffer.Metadata.nodeValue( s["n"], "undoTest" ), None )
		self.assertEqual( Gaffer.Metadata.plugValue( s["n"]["op1"], "undoTest" ), None )

		s.redo()

		self.assertEqual( Gaffer.Metadata.nodeValue( s["n"], "undoTest" ), "instanceNodeValue" )
		self.assertEqual( Gaffer.Metadata.plugValue( s["n"]["op1"], "undoTest" ), "instancePlugValue" )

		s.redo()

		self.assertEqual( Gaffer.Metadata.nodeValue( s["n"], "undoTest" ), "instanceNodeValue2" )
		self.assertEqual( Gaffer.Metadata.plugValue( s["n"]["op1"], "undoTest" ), "instancePlugValue2" )

	def testInstanceMetadataSignals( self ) :

		n = GafferTest.AddNode()

		ncs = GafferTest.CapturingSlot( Gaffer.Metadata.nodeValueChangedSignal() )
		pcs = GafferTest.CapturingSlot( Gaffer.Metadata.plugValueChangedSignal() )

		Gaffer.Metadata.registerNodeValue( n, "signalTest", 1 )
		Gaffer.Metadata.registerPlugValue( n["op1"], "signalTest", 1 )

		self.assertEqual( len( ncs ), 1 )
		self.assertEqual( len( pcs ), 1 )
		self.assertEqual( ncs[0], ( GafferTest.AddNode.staticTypeId(), "signalTest" ) )
		self.assertEqual( pcs[0], ( GafferTest.AddNode.staticTypeId(), "op1", "signalTest" ) )

		Gaffer.Metadata.registerNodeValue( n, "signalTest", 1 )
		Gaffer.Metadata.registerPlugValue( n["op1"], "signalTest", 1 )

		self.assertEqual( len( ncs ), 1 )
		self.assertEqual( len( pcs ), 1 )

		Gaffer.Metadata.registerNodeValue( n, "signalTest", 2 )
		Gaffer.Metadata.registerPlugValue( n["op1"], "signalTest", 2 )

		self.assertEqual( len( ncs ), 2 )
		self.assertEqual( len( pcs ), 2 )
		self.assertEqual( ncs[1], ( GafferTest.AddNode.staticTypeId(), "signalTest" ) )
		self.assertEqual( pcs[1], ( GafferTest.AddNode.staticTypeId(), "op1", "signalTest" ) )

	def testSerialisation( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = GafferTest.AddNode()

		Gaffer.Metadata.registerNodeValue( s["n"], "serialisationTest", 1 )
		Gaffer.Metadata.registerPlugValue( s["n"]["op1"], "serialisationTest", 2 )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( Gaffer.Metadata.nodeValue( s2["n"], "serialisationTest" ), 1 )
		self.assertEqual( Gaffer.Metadata.plugValue( s2["n"]["op1"], "serialisationTest" ), 2 )

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
			Gaffer.Metadata.registerPlugValue( p, "description", s )

		script2 = Gaffer.ScriptNode()
		script2.execute( script.serialise() )

		for p, s in zip( script2["n"]["user"].children(), trickyStrings ) :
			self.assertEqual( Gaffer.Metadata.plugDescription( p ), s )

	def testRegisteredValues( self ) :

		n = GafferTest.AddNode()

		self.assertTrue( "r" not in Gaffer.Metadata.registeredNodeValues( n ) )
		self.assertTrue( "rp" not in Gaffer.Metadata.registeredPlugValues( n["op1"] ) )
		self.assertTrue( "ri" not in Gaffer.Metadata.registeredNodeValues( n ) )
		self.assertTrue( "rpi" not in Gaffer.Metadata.registeredPlugValues( n["op1"] ) )

		Gaffer.Metadata.registerNodeValue( n.staticTypeId(), "r", 10 )
		Gaffer.Metadata.registerPlugValue( n.staticTypeId(), "op1", "rp", 20 )

		self.assertTrue( "r" in Gaffer.Metadata.registeredNodeValues( n ) )
		self.assertTrue( "rp" in Gaffer.Metadata.registeredPlugValues( n["op1"] ) )
		self.assertTrue( "ri" not in Gaffer.Metadata.registeredNodeValues( n ) )
		self.assertTrue( "rpi" not in Gaffer.Metadata.registeredPlugValues( n["op1"] ) )

		Gaffer.Metadata.registerNodeValue( n, "ri", 10 )
		Gaffer.Metadata.registerPlugValue( n["op1"], "rpi", 20 )

		self.assertTrue( "r" in Gaffer.Metadata.registeredNodeValues( n ) )
		self.assertTrue( "rp" in Gaffer.Metadata.registeredPlugValues( n["op1"] ) )
		self.assertTrue( "ri" in Gaffer.Metadata.registeredNodeValues( n ) )
		self.assertTrue( "rpi" in Gaffer.Metadata.registeredPlugValues( n["op1"] ) )

		self.assertTrue( "r" not in Gaffer.Metadata.registeredNodeValues( n, instanceOnly=True ) )
		self.assertTrue( "rp" not in Gaffer.Metadata.registeredPlugValues( n["op1"], instanceOnly=True ) )
		self.assertTrue( "ri" in Gaffer.Metadata.registeredNodeValues( n ) )
		self.assertTrue( "rpi" in Gaffer.Metadata.registeredPlugValues( n["op1"] ) )

	def testInstanceDestruction( self ) :

		for i in range( 0, 1000 ) :
			p = Gaffer.Plug()
			n = Gaffer.Node()
			self.assertEqual( Gaffer.Metadata.plugValue( p, "destructionTest" ), None )
			self.assertEqual( Gaffer.Metadata.nodeValue( n, "destructionTest" ), None )
			Gaffer.Metadata.registerPlugValue( p, "destructionTest", 10 )
			Gaffer.Metadata.registerNodeValue( n, "destructionTest", 20 )
			self.assertEqual( Gaffer.Metadata.plugValue( p, "destructionTest" ), 10 )
			self.assertEqual( Gaffer.Metadata.nodeValue( n, "destructionTest" ), 20 )
			del p
			del n

	def testThreading( self ) :

		GafferTest.testMetadataThreading()

if __name__ == "__main__":
	unittest.main()

