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

class NodeTest( GafferTest.TestCase ) :

	def testParenting( self ) :

		c = Gaffer.GraphComponent()
		n = Gaffer.Node()
		self.assertEqual( n.acceptsParent( c ), False )
		self.assertRaises( RuntimeError, c.addChild, n )

		n2 = Gaffer.Node()
		self.assertEqual( n.acceptsParent( n2 ), True )
		n2.addChild( n )

		p = Gaffer.Plug()
		self.assertTrue( n.acceptsChild( p ) )
		self.assertFalse( n.acceptsParent( p ) )
		n.addChild( p )
		self.assertTrue( p.parent().isSame( n ) )

	def testNaming( self ) :

		n = Gaffer.Node()
		self.assertEqual( n.getName(), "Node" )

	def testScriptNode( self ) :

		n = Gaffer.Node()
		n2 = Gaffer.Node()
		self.assertEqual( n.scriptNode(), None )
		self.assertEqual( n2.scriptNode(), None )

		sn = Gaffer.ScriptNode()

		sn.addChild( n )
		n.addChild( n2 )

		self.assertTrue( sn.scriptNode().isSame( sn ) )
		self.assertTrue( n.scriptNode().isSame( sn ) )
		self.assertTrue( n2.scriptNode().isSame( sn ) )

	def testExtendedConstructor( self ) :

		n = Gaffer.Node()
		self.assertEqual( n.getName(), "Node" )

		n = Gaffer.Node( "a" )
		self.assertEqual( n.getName(), "a" )

		self.assertRaises( Exception, Gaffer.Node, "too", "many" )

	def testDynamicPlugSerialisationOrder( self ) :

		n = Gaffer.Node()

		n["p1"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		n["p2"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		n["p3"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		self.assertEqual( n.children()[0].getName(), "user" )
		self.assertEqual( n.children()[1].getName(), "p1" )
		self.assertEqual( n.children()[2].getName(), "p2" )
		self.assertEqual( n.children()[3].getName(), "p3" )

		s = Gaffer.ScriptNode()
		s["n"] = n

		ss = s.serialise()

		s = Gaffer.ScriptNode()
		s.execute( ss )

		self.assertEqual( s["n"].children()[0].getName(), "user" )
		self.assertEqual( s["n"].children()[1].getName(), "p1" )
		self.assertEqual( s["n"].children()[2].getName(), "p2" )
		self.assertEqual( s["n"].children()[3].getName(), "p3" )

	def testSerialiseDynamicStringPlugs( self ) :

		n = Gaffer.Node()

		n["p1"] = Gaffer.StringPlug( defaultValue = "default", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		n["p1"].setValue( "value" )
		self.assertEqual( n["p1"].getValue(), "value" )

		s = Gaffer.ScriptNode()
		s["n"] = n

		ss = s.serialise()

		s = Gaffer.ScriptNode()
		s.execute( ss )

		self.assertEqual( s["n"]["p1"].defaultValue(), "default" )
		self.assertEqual( s["n"]["p1"].getValue(), "value" )

	def testSerialiseDynamicBoolPlugs( self ) :

		n = Gaffer.Node()

		n["p1"] = Gaffer.BoolPlug( defaultValue = True, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		n["p1"].setValue( False )

		s = Gaffer.ScriptNode()
		s["n"] = n

		ss = s.serialise()

		s = Gaffer.ScriptNode()
		s.execute( ss )

		self.assertEqual( s["n"]["p1"].defaultValue(), True )
		self.assertEqual( s["n"]["p1"].getValue(), False )

	def testUnparentingRemovesConnections( self ) :

		s = Gaffer.ScriptNode()

		n1 = GafferTest.AddNode( "n1" )
		n2 = GafferTest.AddNode( "n2" )

		s.addChild( n1 )
		s.addChild( n2 )

		n2["op1"].setInput( n1["sum"] )
		self.assertTrue( n2["op1"].getInput().isSame( n1["sum"] ) )

		del s["n2"]

		self.assertEqual( n2["op1"].getInput(), None )

		s.addChild( n2 )

		n2["op1"].setInput( n1["sum"] )
		self.assertTrue( n2["op1"].getInput().isSame( n1["sum"] ) )

		del s["n1"]

		self.assertEqual( n2["op1"].getInput(), None )

	def testUnparentingRemovesUserConnections( self ) :

		s = Gaffer.ScriptNode()

		n1 = GafferTest.AddNode()
		n2 = GafferTest.AddNode()

		s["n1"] = n1
		s["n2"] = n2

		s["n1"]["user"]["i1"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n1"]["user"]["i2"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n1"]["user"]["v"] = Gaffer.V2iPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["n1"]["user"]["i1"].setInput( n2["sum"] )
		s["n2"]["op1"].setInput( s["n1"]["user"]["i2"] )
		s["n1"]["user"]["v"][0].setInput( s["n2"]["sum"] )
		s["n2"]["op2"].setInput( s["n1"]["user"]["v"][1] )

		del s["n1"]
		self.assertTrue( n1.parent() is None )

		self.assertTrue( n1["user"]["i1"].getInput() is None )
		self.assertTrue( n2["op1"].getInput() is None )
		self.assertTrue( n1["user"]["v"][0].getInput() is None )
		self.assertTrue( n2["op2"].getInput() is None )

	def testOverrideAcceptsInput( self ) :

		class AcceptsInputTestNode( Gaffer.Node ) :

			def __init__( self, name = "AcceptsInputTestNode" ) :

				Gaffer.Node.__init__( self, name )

				self.addChild( Gaffer.IntPlug( "in" ) )
				self.addChild( Gaffer.IntPlug( "out", Gaffer.Plug.Direction.Out ) )

			def acceptsInput( self, plug, inputPlug ) :

				if plug.isSame( self["in"] ) :
					return isinstance( inputPlug.source().node(), AcceptsInputTestNode )

				return True

		n1 = AcceptsInputTestNode()
		n2 = AcceptsInputTestNode()
		n3 = GafferTest.AddNode()

		self.assertEqual( n1["in"].acceptsInput( n2["out"] ), True )
		self.assertEqual( n1["in"].acceptsInput( n3["sum"] ), False )

		n1["in"].setInput( n2["out"] )
		self.assertRaises( RuntimeError, n1["in"].setInput, n3["sum"] )

		# check that we can't use a pass-through connection as
		# a loophole.

		n1["in"].setInput( None )

		# this particular connection makes no sense but breaks
		# no rules - we're just using it to test the loophole.
		n2["out"].setInput( n3["sum"] )

		self.assertEqual( n1["in"].acceptsInput( n2["out"] ), False )

		self.assertRaises( RuntimeError, n1["in"].setInput, n2["out"] )

	def testPlugFlagsChangedSignal( self ) :

		n = Gaffer.Node()
		n["p"] = Gaffer.Plug()

		cs = GafferTest.CapturingSlot( n.plugFlagsChangedSignal() )
		self.assertEqual( len( cs ), 0 )

		n["p"].setFlags( Gaffer.Plug.Flags.Dynamic, True )
		self.assertEqual( len( cs ), 1 )
		self.assertTrue( cs[0][0].isSame( n["p"] ) )

		# second time should have no effect because they're the same
		n["p"].setFlags( Gaffer.Plug.Flags.Dynamic, True )
		self.assertEqual( len( cs ), 1 )

		n["p"].setFlags( Gaffer.Plug.Flags.Dynamic, False )
		self.assertEqual( len( cs ), 2 )
		self.assertTrue( cs[1][0].isSame( n["p"] ) )

	def testUserPlugs( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["user"]["test"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["test"].setValue( 10 )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( s2["n"]["user"]["test"].getValue(), 10 )

	def testNodesConstructWithDefaultValues( self ) :

		self.assertNodesConstructWithDefaultValues( Gaffer )
		self.assertNodesConstructWithDefaultValues( GafferTest )

	def testUserPlugDoesntTrackChildConnections( self ) :

		s = Gaffer.ScriptNode()

		s["n1"] = Gaffer.Node()
		s["n1"]["user"]["p"] = Gaffer.IntPlug()

		s["n2"] = Gaffer.Node()
		s["n2"]["user"]["p"] = Gaffer.IntPlug()

		s["n2"]["user"]["p"].setInput( s["n1"]["user"]["p"] )
		self.assertTrue( s["n2"]["user"]["p"].getInput().isSame( s["n1"]["user"]["p"] ) )
		self.assertTrue( s["n2"]["user"].getInput() is None )

		s["n1"]["user"]["p2"] = Gaffer.IntPlug()
		self.assertEqual( len( s["n2"]["user"] ), 1 )

	def testInternalConnectionsSurviveUnparenting( self ) :

		class InternalConnectionsNode( Gaffer.Node ) :

			def __init__( self, name = "InternalConnectionsNode" ) :

				Gaffer.Node.__init__( self, name )

				self["in1"] = Gaffer.IntPlug()
				self["in2"] = Gaffer.IntPlug()
				self["__in"] = Gaffer.IntPlug()

				self["out1"] = Gaffer.IntPlug( direction = Gaffer.Plug.Direction.Out )
				self["out2"] = Gaffer.IntPlug( direction = Gaffer.Plug.Direction.Out )
				self["__out"] = Gaffer.IntPlug( direction = Gaffer.Plug.Direction.Out )

				self["out1"].setInput( self["in1"] )

				self["__add"] = GafferTest.AddNode()
				self["__add"]["op1"].setInput( self["in2"] )
				self["__add"]["op2"].setInput( self["__out"] )
				self["__in"].setInput( self["__add"]["sum"] )

				self["out2"].setInput( self["__add"]["sum"] )

		IECore.registerRunTimeTyped( InternalConnectionsNode )

		s = Gaffer.ScriptNode()
		n = InternalConnectionsNode()
		s["n"] = n

		def assertConnections() :

			self.assertTrue( n["out1"].getInput().isSame( n["in1"] ) )
			self.assertTrue( n["__add"]["op1"].getInput().isSame( n["in2"] ) )
			self.assertTrue( n["__add"]["op2"].getInput().isSame( n["__out"] ) )
			self.assertTrue( n["out2"].getInput().isSame( n["__add"]["sum"] ) )
			self.assertTrue( n["__in"].getInput().isSame( n["__add"]["sum"] ) )

		assertConnections()

		s.removeChild( n )
		assertConnections()

		s.addChild( n )
		assertConnections()

	def testRanges( self ) :

		n = Gaffer.Node()
		n["c1"] = Gaffer.Node()
		n["c2"] = GafferTest.AddNode()
		n["c2"]["gc1"] = Gaffer.Node()
		n["c3"] = Gaffer.Node()
		n["c3"]["gc2"] = GafferTest.AddNode()
		n["c3"]["gc3"] = GafferTest.AddNode()

		self.assertEqual(
			list( Gaffer.Node.Range( n ) ),
			[ n["c1"], n["c2"], n["c3"] ],
		)

		self.assertEqual(
			list( Gaffer.Node.RecursiveRange( n ) ),
			[ n["c1"], n["c2"], n["c2"]["gc1"], n["c3"], n["c3"]["gc2"], n["c3"]["gc3"] ],
		)

		self.assertEqual(
			list( GafferTest.AddNode.Range( n ) ),
			[ n["c2"] ],
		)

		self.assertEqual(
			list( GafferTest.AddNode.RecursiveRange( n ) ),
			[ n["c2"], n["c3"]["gc2"], n["c3"]["gc3"] ],
		)

	def testRangesForPythonTypes( self ) :

		n = Gaffer.Node()
		n["a"] = GafferTest.AddNode()
		n["b"] = Gaffer.Node()
		n["c"] = GafferTest.AddNode()
		n["d"] = Gaffer.Node()
		n["d"]["e"] = GafferTest.AddNode()

		self.assertEqual(
			list( Gaffer.Node.Range( n ) ),
			[ n["a"], n["b"], n["c"], n["d"] ],
		)

		self.assertEqual(
			list( GafferTest.AddNode.Range( n ) ),
			[ n["a"], n["c"] ],
		)

		self.assertEqual(
			list( Gaffer.Node.RecursiveRange( n ) ),
			[ n["a"], n["b"], n["c"], n["d"], n["d"]["e"] ],
		)

		self.assertEqual(
			list( GafferTest.AddNode.RecursiveRange( n ) ),
			[ n["a"], n["c"], n["d"]["e"] ],
		)

if __name__ == "__main__" :
	unittest.main()
