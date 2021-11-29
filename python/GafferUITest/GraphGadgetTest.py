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
import threading
import imath
import inspect
import time

import IECore

import Gaffer
import GafferUI
import GafferTest
import GafferUITest

class NestedPlugTestNode( Gaffer.Node ) :

	def __init__( self ) :

		Gaffer.Node.__init__( self )

IECore.registerRunTimeTyped( NestedPlugTestNode )
Gaffer.Metadata.registerValue( NestedPlugTestNode, "c", "nodule:type", "GafferUI::CompoundNodule" )

class GraphGadgetTest( GafferUITest.TestCase ) :

	def testRemovedNodesDontHaveGadgets( self ) :

		s = Gaffer.ScriptNode()
		g = GafferUI.GraphGadget( s )

		n = GafferTest.AddNode()
		s["add1"] = n

		self.assertIsNotNone( g.nodeGadget( n ) )

		s.deleteNodes( filter = Gaffer.StandardSet( [ n ] ) )

		self.assertIsNone( g.nodeGadget( n ) )

	def testRemovedNodesDontHaveConnections( self ) :

		s = Gaffer.ScriptNode()

		n = GafferTest.AddNode()
		s["add1"] = n
		s["add2"] = GafferTest.AddNode()

		s["add1"]["op1"].setInput( s["add2"]["sum"] )

		g = GafferUI.GraphGadget( s )

		s.deleteNodes( filter = Gaffer.StandardSet( [ s["add1"] ] ) )

		self.assertIsNone( g.connectionGadget( n["op1"] ) )

	def testCreateWithFilter( self ) :

		script = Gaffer.ScriptNode()

		script["add1"] = GafferTest.AddNode()
		script["add2"] = GafferTest.AddNode()

		nodeFilter = Gaffer.StandardSet( [ script["add2"] ] )

		g = GafferUI.GraphGadget( script, nodeFilter )

		self.assertIsNone( g.nodeGadget( script["add1"] ) )
		self.assertIsNotNone( g.nodeGadget( script["add2"] ) )

	def testEditFilter( self ) :

		script = Gaffer.ScriptNode()

		script["add1"] = GafferTest.AddNode()
		script["add2"] = GafferTest.AddNode()

		nodeFilter = Gaffer.StandardSet( script.children() )

		g = GafferUI.GraphGadget( script, nodeFilter )

		self.assertIsNotNone( g.nodeGadget( script["add1"] ) )
		self.assertIsNotNone( g.nodeGadget( script["add2"] ) )

		nodeFilter.remove( script["add1"] )

		self.assertIsNone( g.nodeGadget( script["add1"] ) )
		self.assertIsNotNone( g.nodeGadget( script["add2"] ) )

		nodeFilter.remove( script["add2"] )

		self.assertIsNone( g.nodeGadget( script["add1"] ) )
		self.assertIsNone( g.nodeGadget( script["add2"] ) )

		nodeFilter.add( script["add1"] )

		self.assertIsNotNone( g.nodeGadget( script["add1"] ) )
		self.assertIsNone( g.nodeGadget( script["add2"] ) )

		nodeFilter.add( script["add2"] )

		self.assertIsNotNone( g.nodeGadget( script["add1"] ) )
		self.assertIsNotNone( g.nodeGadget( script["add2"] ) )

	def testUnhidingConnectedDstNodes( self ) :

		script = Gaffer.ScriptNode()

		script["add1"] = GafferTest.AddNode()
		script["add2"] = GafferTest.AddNode()

		script["add2"]["op1"].setInput( script["add1"]["sum"] )

		nodeFilter = Gaffer.StandardSet( [ script["add1"] ] )
		g = GafferUI.GraphGadget( script, nodeFilter )

		self.assertIsNotNone( g.nodeGadget( script["add1"] ) )
		self.assertIsNone( g.nodeGadget( script["add2"] ) )
		self.assertIsNone( g.connectionGadget( script["add2"]["op1"] ) )

		nodeFilter.add( script["add2"] )

		self.assertIsNotNone( g.nodeGadget( script["add1"] ) )
		self.assertIsNotNone( g.nodeGadget( script["add2"] ) )
		self.assertIsNotNone( g.connectionGadget( script["add2"]["op1"] ) )

	def testCreatingWithHiddenSrcNodes( self ) :

		script = Gaffer.ScriptNode()

		script["add1"] = GafferTest.AddNode()
		script["add2"] = GafferTest.AddNode()

		script["add2"]["op1"].setInput( script["add1"]["sum"] )

		nodeFilter = Gaffer.StandardSet( [ script["add2"] ] )

		g = GafferUI.GraphGadget( script, nodeFilter )

		self.assertIsNone( g.nodeGadget( script["add1"] ) )
		self.assertIsNotNone( g.nodeGadget( script["add2"] ) )

		c = g.connectionGadget( script["add2"]["op1"] )
		self.assertIsNotNone( c )

		self.assertTrue( c.dstNodule().plug().isSame( script["add2"]["op1"] ) )
		self.assertEqual( c.srcNodule(), None )

	def testHidingConnectedDstNodes( self ) :

		script = Gaffer.ScriptNode()

		script["add1"] = GafferTest.AddNode()
		script["add2"] = GafferTest.AddNode()

		script["add2"]["op1"].setInput( script["add1"]["sum"] )

		nodeFilter = Gaffer.StandardSet( script.children() )
		g = GafferUI.GraphGadget( script, nodeFilter )

		self.assertIsNotNone( g.nodeGadget( script["add1"] ) )
		self.assertIsNotNone( g.nodeGadget( script["add2"] ) )
		self.assertIsNotNone( g.connectionGadget( script["add2"]["op1"] ) )

		nodeFilter.remove( script["add2"] )

		self.assertIsNotNone( g.nodeGadget( script["add1"] ) )
		self.assertIsNone( g.nodeGadget( script["add2"] ) )
		self.assertIsNone( g.connectionGadget( script["add2"]["op1"] ) )

	def testHidingConnectedSrcNodes( self ) :

		script = Gaffer.ScriptNode()

		script["add1"] = GafferTest.AddNode()
		script["add2"] = GafferTest.AddNode()

		script["add2"]["op1"].setInput( script["add1"]["sum"] )

		nodeFilter = Gaffer.StandardSet( [ script["add1"], script["add2"] ] )

		g = GafferUI.GraphGadget( script, nodeFilter )

		self.assertIsNotNone( g.nodeGadget( script["add1"] ) )
		self.assertIsNotNone( g.nodeGadget( script["add2"] ) )

		c = g.connectionGadget( script["add2"]["op1"] )
		self.assertIsNotNone( c )

		self.assertTrue( c.srcNodule().plug().isSame( script["add1"]["sum"] ) )
		self.assertTrue( c.dstNodule().plug().isSame( script["add2"]["op1"] ) )

		nodeFilter.remove( script["add1"] )

		self.assertIsNone( g.nodeGadget( script["add1"] ) )

		c = g.connectionGadget( script["add2"]["op1"] )
		self.assertIsNotNone( c )
		self.assertIsNone( c.srcNodule() )
		self.assertTrue( c.dstNodule().plug().isSame( script["add2"]["op1"] ) )

	def testConnectingInvisibleDstNodes( self ) :

		script = Gaffer.ScriptNode()

		script["add1"] = GafferTest.AddNode()
		script["add2"] = GafferTest.AddNode()

		nodeFilter = Gaffer.StandardSet( [ script["add1"] ] )
		g = GafferUI.GraphGadget( script, nodeFilter )

		self.assertIsNotNone( g.nodeGadget( script["add1"] ) )
		self.assertIsNone( g.nodeGadget( script["add2"] ) )

		script["add2"]["op1"].setInput( script["add1"]["sum"] )

		self.assertIsNotNone( g.nodeGadget( script["add1"] ) )
		self.assertIsNone( g.nodeGadget( script["add2"] ) )
		self.assertIsNone( g.connectionGadget( script["add2"]["op1"] ) )

	def testConnectingHiddenDstNodes( self ) :

		script = Gaffer.ScriptNode()

		script["add1"] = GafferTest.AddNode()
		script["add2"] = GafferTest.AddNode()

		nodeFilter = Gaffer.StandardSet( script.children() )
		g = GafferUI.GraphGadget( script, nodeFilter )

		self.assertIsNotNone( g.nodeGadget( script["add1"] ) )
		self.assertIsNotNone( g.nodeGadget( script["add2"] ) )

		nodeFilter.remove( script["add2"] )

		self.assertIsNotNone( g.nodeGadget( script["add1"] ) )
		self.assertIsNone( g.nodeGadget( script["add2"] ) )

		script["add2"]["op1"].setInput( script["add1"]["sum"] )

		self.assertIsNotNone( g.nodeGadget( script["add1"] ) )
		self.assertIsNone( g.nodeGadget( script["add2"] ) )
		self.assertIsNone( g.connectionGadget( script["add2"]["op1"] ) )

	def testConnectingHiddenSrcNodes( self ) :

		script = Gaffer.ScriptNode()

		script["add1"] = GafferTest.AddNode()
		script["add2"] = GafferTest.AddNode()

		nodeFilter = Gaffer.StandardSet( [ script["add2"] ] )
		g = GafferUI.GraphGadget( script, nodeFilter )

		self.assertIsNone( g.nodeGadget( script["add1"] ) )
		self.assertIsNotNone( g.nodeGadget( script["add2"] ) )

		script["add2"]["op1"].setInput( script["add1"]["sum"] )

		self.assertIsNone( g.nodeGadget( script["add1"] ) )
		self.assertIsNotNone( g.nodeGadget( script["add2"] ) )

		c = g.connectionGadget( script["add2"]["op1"] )
		self.assertIsNotNone( c )
		self.assertIsNone( c.srcNodule() )

	def testConnectingHiddenSrcNodesAndReshowing( self ) :

		script = Gaffer.ScriptNode()

		script["add1"] = GafferTest.AddNode()
		script["add2"] = GafferTest.AddNode()

		nodeFilter = Gaffer.StandardSet( [ script["add2"] ] )
		g = GafferUI.GraphGadget( script, nodeFilter )

		self.assertIsNone( g.nodeGadget( script["add1"] ) )
		self.assertIsNotNone( g.nodeGadget( script["add2"] ) )

		script["add2"]["op1"].setInput( script["add1"]["sum"] )

		self.assertIsNone( g.nodeGadget( script["add1"] ) )
		self.assertIsNotNone( g.nodeGadget( script["add2"] ) )

		c = g.connectionGadget( script["add2"]["op1"] )
		self.assertIsNotNone( c )
		self.assertIsNone( c.srcNodule() )

		nodeFilter.add( script["add1"] )

		self.assertIsNotNone( g.nodeGadget( script["add1"] ) )
		self.assertIsNotNone( g.nodeGadget( script["add2"] ) )

		c = g.connectionGadget( script["add2"]["op1"] )
		self.assertIsNotNone( c )
		self.assertTrue( c.srcNodule().plug().isSame( script["add1"]["sum"] ) )

	def testChangingFilter( self ) :

		script = Gaffer.ScriptNode()

		script["add1"] = GafferTest.AddNode()
		script["add2"] = GafferTest.AddNode()

		nodeFilter = Gaffer.StandardSet( [ script["add1"] ] )
		g = GafferUI.GraphGadget( script, nodeFilter )

		self.assertIsNotNone( g.nodeGadget( script["add1"] ) )
		self.assertIsNone( g.nodeGadget( script["add2"] ) )

		nodeFilter2 = Gaffer.StandardSet( [ script["add2"] ] )
		g.setFilter( nodeFilter2 )

		self.assertIsNone( g.nodeGadget( script["add1"] ) )
		self.assertIsNotNone( g.nodeGadget( script["add2"] ) )

	def testChangingFilterAndEditingOriginal( self ) :

		script = Gaffer.ScriptNode()

		script["add1"] = GafferTest.AddNode()
		script["add2"] = GafferTest.AddNode()

		nodeFilter = Gaffer.StandardSet()
		g = GafferUI.GraphGadget( script, nodeFilter )

		self.assertIsNone( g.nodeGadget( script["add1"] ) )
		self.assertIsNone( g.nodeGadget( script["add2"] ) )

		nodeFilter2 = Gaffer.StandardSet( [ script["add2"] ] )
		g.setFilter( nodeFilter2 )

		self.assertIsNone( g.nodeGadget( script["add1"] ) )
		self.assertIsNotNone( g.nodeGadget( script["add2"] ) )

		nodeFilter.add( script["add1"] )

		self.assertIsNone( g.nodeGadget( script["add1"] ) )
		self.assertIsNotNone( g.nodeGadget( script["add2"] ) )

	def testConnectionsForNestedPlugs( self ) :

		script = Gaffer.ScriptNode()

		script["n"] = NestedPlugTestNode()
		script["n"]["c"] = Gaffer.Plug()
		script["n"]["c"]["i"] = Gaffer.IntPlug()

		script["n2"] = NestedPlugTestNode()
		script["n2"]["c"] = Gaffer.Plug(  direction = Gaffer.Plug.Direction.Out )
		script["n2"]["c"]["o"] = Gaffer.IntPlug( direction = Gaffer.Plug.Direction.Out )

		script["n"]["c"]["i"].setInput( script["n2"]["c"]["o"] )

		s = Gaffer.StandardSet( script.children() )
		g = GafferUI.GraphGadget( script, s )

		c = g.connectionGadget( script["n"]["c"]["i"] )
		self.assertIsNotNone( c )
		self.assertTrue( c.srcNodule().plug().isSame( script["n2"]["c"]["o"] ) )
		self.assertTrue( c.dstNodule().plug().isSame( script["n"]["c"]["i"] ) )

		s.remove( script["n2"] )

		self.assertIsNone( g.nodeGadget( script["n2"] ) )

		c = g.connectionGadget( script["n"]["c"]["i"] )
		self.assertIsNotNone( c )
		self.assertIsNone( c.srcNodule() )
		self.assertTrue( c.dstNodule().plug().isSame( script["n"]["c"]["i"] ) )

		s.add( script["n2"] )

		self.assertIsNotNone( g.nodeGadget( script["n2"] ) )

		c = g.connectionGadget( script["n"]["c"]["i"] )
		self.assertIsNotNone( c )
		self.assertTrue( c.srcNodule().plug().isSame( script["n2"]["c"]["o"] ) )
		self.assertTrue( c.dstNodule().plug().isSame( script["n"]["c"]["i"] ) )

		s.remove( script["n"] )

		self.assertIsNone( g.nodeGadget( script["n"] ) )

		self.assertIsNone( g.connectionGadget( script["n"]["c"]["i"] ) )

		s.add( script["n"] )

		self.assertIsNotNone( g.nodeGadget( script["n"] ) )

		c = g.connectionGadget( script["n"]["c"]["i"] )
		self.assertIsNotNone( c )
		self.assertTrue( c.srcNodule().plug().isSame( script["n2"]["c"]["o"] ) )
		self.assertTrue( c.dstNodule().plug().isSame( script["n"]["c"]["i"] ) )

	def testRemovePlugWithInputConnection( self ) :

		script = Gaffer.ScriptNode()

		script["n1"] = Gaffer.Node()
		script["n2"] = Gaffer.Node()

		script["n1"]["o"] = Gaffer.IntPlug( direction = Gaffer.Plug.Direction.Out )
		script["n2"]["i"] = Gaffer.IntPlug()

		script["n2"]["i"].setInput( script["n1"]["o"] )

		g = GafferUI.GraphGadget( script )

		self.assertIsNotNone( g.connectionGadget( script["n2"]["i"] ) )

		with Gaffer.UndoScope( script ) :

			removedPlug = script["n2"]["i"]
			del script["n2"]["i"]

		self.assertIsNone( g.connectionGadget( removedPlug ) )

		script.undo()

		self.assertIsNotNone( g.connectionGadget( script["n2"]["i"] ) )

	def testRemovePlugWithOutputConnection( self ) :

		script = Gaffer.ScriptNode()

		script["n1"] = Gaffer.Node()
		script["n2"] = Gaffer.Node()

		script["n1"]["o"] = Gaffer.IntPlug( direction = Gaffer.Plug.Direction.Out )
		script["n2"]["i"] = Gaffer.IntPlug()

		script["n2"]["i"].setInput( script["n1"]["o"] )

		g = GafferUI.GraphGadget( script )

		self.assertIsNotNone( g.connectionGadget( script["n2"]["i"] ) )

		with Gaffer.UndoScope( script ) :

			del script["n1"]["o"]

		self.assertIsNone( g.connectionGadget( script["n2"]["i"] ) )

		script.undo()

		self.assertIsNotNone( g.connectionGadget( script["n2"]["i"] ) )

	def testConnectionBound( self ) :

		for i in range( 0, 100 ) :

			script = Gaffer.ScriptNode()

			script["n1"] = Gaffer.Node()
			script["n2"] = Gaffer.Node()

			script["n1"]["o"] = Gaffer.IntPlug( direction = Gaffer.Plug.Direction.Out )
			script["n2"]["i"] = Gaffer.IntPlug()

			script["n2"]["i"].setInput( script["n1"]["o"] )

			g = GafferUI.GraphGadget( script )
			c = g.connectionGadget( script["n2"]["i"] )

			gb = imath.Box3f()
			gb.extendBy( g.nodeGadget( script["n1"] ).bound() )
			gb.extendBy( g.nodeGadget( script["n2"] ).bound() )
			gb.setMin( gb.min() - imath.V3f( 10 ) )
			gb.setMax( gb.max() + imath.V3f( 10 ) )

			b = c.bound()
			self.assertFalse( b.isEmpty() )

			self.assertTrue( IECore.BoxAlgo.contains( gb, b ) )

	def testNoFilter( self ) :

		s = Gaffer.ScriptNode()
		s["n1"] = Gaffer.Node()

		g = GafferUI.GraphGadget( s )

		self.assertTrue( g.getRoot().isSame( s ) )
		self.assertTrue( g.getFilter() is None )
		self.assertTrue( g.nodeGadget( s["n1"] ) )

		s["n2"] = Gaffer.Node()
		self.assertTrue( g.nodeGadget( s["n1"] ) )

	def testFilterIsChildSet( self ) :

		s = Gaffer.ScriptNode()
		s["n1"] = Gaffer.Node()

		g = GafferUI.GraphGadget( s, Gaffer.ChildSet( s ) )
		self.assertTrue( g.nodeGadget( s["n1"] ) )

		l = len( g )

		s["n2"] = Gaffer.Node()
		self.assertTrue( g.nodeGadget( s["n2"] ) )

		self.assertEqual( len( g ), l + 1 )

	def testSetRoot( self ) :

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()
		s["b"]["n"] = Gaffer.Node()

		f = Gaffer.StandardSet( [ s["b"] ] )
		g = GafferUI.GraphGadget( s, f )

		self.assertTrue( g.nodeGadget( s["b"] ) )
		self.assertFalse( g.nodeGadget( s["b"]["n"] ) )

		g.setRoot( s["b"] )
		self.assertTrue( g.getRoot().isSame( s["b"] ) )
		self.assertEqual( g.getFilter(), None )

		self.assertTrue( g.nodeGadget( s["b"]["n"] ) )
		self.assertFalse( g.nodeGadget( s["b"] ) )

	def testRootChangedSignal( self ) :

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()

		roots = []
		previousRoots = []
		def f( gg, previousRoot ) :

			self.assertTrue( gg.isSame( g ) )
			roots.append( gg.getRoot() )
			previousRoots.append( previousRoot )

		g = GafferUI.GraphGadget( s )
		c = g.rootChangedSignal().connect( f )

		self.assertEqual( len( roots ), 0 )
		self.assertEqual( len( previousRoots ), 0 )

		g.setRoot( s["b"] )
		self.assertEqual( len( roots ), 1 )
		self.assertTrue( roots[0].isSame( s["b"] ) )
		self.assertEqual( len( previousRoots ), 1 )
		self.assertTrue( previousRoots[0].isSame( s ) )

		g.setRoot( s["b"] )
		self.assertEqual( len( roots ), 1 )
		self.assertTrue( roots[0].isSame( s["b"] ) )
		self.assertEqual( len( previousRoots ), 1 )
		self.assertTrue( previousRoots[0].isSame( s ) )

		g.setRoot( s )
		self.assertEqual( len( roots ), 2 )
		self.assertTrue( roots[1].isSame( s ) )
		self.assertEqual( len( previousRoots ), 2 )
		self.assertTrue( previousRoots[1].isSame( s["b"] ) )

	def testSetNodePosition( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()

		g = GafferUI.GraphGadget( s )

		self.assertFalse( g.hasNodePosition( s["n"] ) )
		g.setNodePosition( s["n"], imath.V2f( -100, 2000 ) )
		self.assertEqual( g.getNodePosition( s["n"] ), imath.V2f( -100, 2000 ) )
		self.assertTrue( g.hasNodePosition( s["n"] ) )

	def testPlugConnectionGadgets( self ) :

		script = Gaffer.ScriptNode()

		script["add1"] = GafferTest.AddNode()
		script["add2"] = GafferTest.AddNode()
		script["add3"] = GafferTest.AddNode()
		script["add4"] = GafferTest.AddNode()

		script["add2"]["op1"].setInput( script["add1"]["sum"] )
		script["add3"]["op1"].setInput( script["add2"]["sum"] )
		script["add4"]["op2"].setInput( script["add2"]["sum"] )

		g = GafferUI.GraphGadget( script )

		c = g.connectionGadgets( script["add1"]["sum"] )
		self.assertEqual( len( c ), 1 )
		self.assertTrue( c[0].srcNodule().plug().isSame( script["add1"]["sum"] ) )
		self.assertTrue( c[0].dstNodule().plug().isSame( script["add2"]["op1"] ) )

		c = g.connectionGadgets( script["add1"]["sum"], excludedNodes = Gaffer.StandardSet( [ script["add2"] ] ) )
		self.assertEqual( len( c ), 0 )

		c = g.connectionGadgets( script["add2"]["sum"] )
		self.assertEqual( len( c ), 2 )
		self.assertTrue( c[0].srcNodule().plug().isSame( script["add2"]["sum"] ) )
		self.assertTrue( c[0].dstNodule().plug().isSame( script["add3"]["op1"] ) )
		self.assertTrue( c[1].srcNodule().plug().isSame( script["add2"]["sum"] ) )
		self.assertTrue( c[1].dstNodule().plug().isSame( script["add4"]["op2"] ) )

		c = g.connectionGadgets( script["add2"]["sum"], excludedNodes = Gaffer.StandardSet( [ script["add3"] ] ) )
		self.assertEqual( len( c ), 1 )
		self.assertTrue( c[0].srcNodule().plug().isSame( script["add2"]["sum"] ) )
		self.assertTrue( c[0].dstNodule().plug().isSame( script["add4"]["op2"] ) )

	def testNodeConnectionGadgets( self ) :

		script = Gaffer.ScriptNode()

		script["add1"] = GafferTest.AddNode()
		script["add2"] = GafferTest.AddNode()
		script["add3"] = GafferTest.AddNode()
		script["add4"] = GafferTest.AddNode()

		script["add2"]["op1"].setInput( script["add1"]["sum"] )
		script["add3"]["op1"].setInput( script["add2"]["sum"] )
		script["add4"]["op2"].setInput( script["add2"]["sum"] )

		g = GafferUI.GraphGadget( script )

		c = g.connectionGadgets( script["add1"] )
		self.assertEqual( len( c ), 1 )
		self.assertTrue( c[0].srcNodule().plug().isSame( script["add1"]["sum"] ) )
		self.assertTrue( c[0].dstNodule().plug().isSame( script["add2"]["op1"] ) )

		c = g.connectionGadgets( script["add1"], excludedNodes = Gaffer.StandardSet( [ script["add2"] ] ) )
		self.assertEqual( len( c ), 0 )

		c = g.connectionGadgets( script["add2"] )
		self.assertEqual( len( c ), 3 )
		self.assertTrue( c[0].srcNodule().plug().isSame( script["add1"]["sum"] ) )
		self.assertTrue( c[0].dstNodule().plug().isSame( script["add2"]["op1"] ) )
		self.assertTrue( c[1].srcNodule().plug().isSame( script["add2"]["sum"] ) )
		self.assertTrue( c[1].dstNodule().plug().isSame( script["add3"]["op1"] ) )
		self.assertTrue( c[2].srcNodule().plug().isSame( script["add2"]["sum"] ) )
		self.assertTrue( c[2].dstNodule().plug().isSame( script["add4"]["op2"] ) )

		c = g.connectionGadgets( script["add2"], excludedNodes = Gaffer.StandardSet( [ script["add3"] ] ) )
		self.assertEqual( len( c ), 2 )
		self.assertTrue( c[0].srcNodule().plug().isSame( script["add1"]["sum"] ) )
		self.assertTrue( c[0].dstNodule().plug().isSame( script["add2"]["op1"] ) )
		self.assertTrue( c[1].srcNodule().plug().isSame( script["add2"]["sum"] ) )
		self.assertTrue( c[1].dstNodule().plug().isSame( script["add4"]["op2"] ) )

	def testInternalConnectionsNotShown( self ) :

		# make sure they're not shown when they exist before graph visualisation

		script = Gaffer.ScriptNode()

		script["add1"] = GafferTest.AddNode()
		script["add1"]["sum"].setInput( script["add1"]["op1"] )
		script["add1"]["op1"].setInput( script["add1"]["op2"] )

		g = GafferUI.GraphGadget( script )

		self.assertEqual( len( g.connectionGadgets( script["add1"] ) ), 0 )
		self.assertEqual( g.connectionGadget( script["add1"]["sum"] ), None )
		self.assertEqual( g.connectionGadget( script["add1"]["op1"] ), None )
		self.assertEqual( g.connectionGadget( script["add1"]["op2"] ), None )

		# make sure they're not shown when they're made after graph visualisation

		script = Gaffer.ScriptNode()
		g = GafferUI.GraphGadget( script )

		script["add1"] = GafferTest.AddNode()
		script["add1"]["sum"].setInput( script["add1"]["op1"] )
		script["add1"]["op1"].setInput( script["add1"]["op2"] )

		self.assertEqual( len( g.connectionGadgets( script["add1"] ) ), 0 )
		self.assertEqual( g.connectionGadget( script["add1"]["sum"] ), None )
		self.assertEqual( g.connectionGadget( script["add1"]["op1"] ), None )
		self.assertEqual( g.connectionGadget( script["add1"]["op2"] ), None )

	def testConnectionMinimisedAccessors( self ) :

		script = Gaffer.ScriptNode()

		script["add1"] = GafferTest.AddNode()
		script["add2"] = GafferTest.AddNode()
		script["add3"] = GafferTest.AddNode()

		script["add2"]["op1"].setInput( script["add1"]["sum"] )
		script["add3"]["op1"].setInput( script["add2"]["sum"] )

		g = GafferUI.GraphGadget( script )

		self.assertFalse( g.getNodeInputConnectionsMinimised( script["add1"] ) )
		self.assertFalse( g.getNodeInputConnectionsMinimised( script["add2"] ) )
		self.assertFalse( g.getNodeInputConnectionsMinimised( script["add3"] ) )

		self.assertFalse( g.getNodeOutputConnectionsMinimised( script["add1"] ) )
		self.assertFalse( g.getNodeOutputConnectionsMinimised( script["add2"] ) )
		self.assertFalse( g.getNodeOutputConnectionsMinimised( script["add3"] ) )

		g.setNodeInputConnectionsMinimised( script["add3"], True )

		self.assertFalse( g.getNodeInputConnectionsMinimised( script["add1"] ) )
		self.assertFalse( g.getNodeInputConnectionsMinimised( script["add2"] ) )
		self.assertTrue( g.getNodeInputConnectionsMinimised( script["add3"] ) )

		self.assertFalse( g.getNodeOutputConnectionsMinimised( script["add1"] ) )
		self.assertFalse( g.getNodeOutputConnectionsMinimised( script["add2"] ) )
		self.assertFalse( g.getNodeOutputConnectionsMinimised( script["add3"] ) )

		g.setNodeOutputConnectionsMinimised( script["add2"], True )

		self.assertFalse( g.getNodeInputConnectionsMinimised( script["add1"] ) )
		self.assertFalse( g.getNodeInputConnectionsMinimised( script["add2"] ) )
		self.assertTrue( g.getNodeInputConnectionsMinimised( script["add3"] ) )

		self.assertFalse( g.getNodeOutputConnectionsMinimised( script["add1"] ) )
		self.assertTrue( g.getNodeOutputConnectionsMinimised( script["add2"] ) )
		self.assertFalse( g.getNodeOutputConnectionsMinimised( script["add3"] ) )

		g.setNodeOutputConnectionsMinimised( script["add2"], False )

		self.assertFalse( g.getNodeInputConnectionsMinimised( script["add1"] ) )
		self.assertFalse( g.getNodeInputConnectionsMinimised( script["add2"] ) )
		self.assertTrue( g.getNodeInputConnectionsMinimised( script["add3"] ) )

		self.assertFalse( g.getNodeOutputConnectionsMinimised( script["add1"] ) )
		self.assertFalse( g.getNodeOutputConnectionsMinimised( script["add2"] ) )
		self.assertFalse( g.getNodeOutputConnectionsMinimised( script["add3"] ) )

		g.setNodeInputConnectionsMinimised( script["add3"], False )

		self.assertFalse( g.getNodeInputConnectionsMinimised( script["add1"] ) )
		self.assertFalse( g.getNodeInputConnectionsMinimised( script["add2"] ) )
		self.assertFalse( g.getNodeInputConnectionsMinimised( script["add3"] ) )

		self.assertFalse( g.getNodeOutputConnectionsMinimised( script["add1"] ) )
		self.assertFalse( g.getNodeOutputConnectionsMinimised( script["add2"] ) )
		self.assertFalse( g.getNodeOutputConnectionsMinimised( script["add3"] ) )

	def testConnectionMinimisation( self ) :

		script = Gaffer.ScriptNode()

		script["add1"] = GafferTest.AddNode()
		script["add2"] = GafferTest.AddNode()
		script["add3"] = GafferTest.AddNode()

		g = GafferUI.GraphGadget( script )

		g.setNodeOutputConnectionsMinimised( script["add1"], True )

		script["add2"]["op1"].setInput( script["add1"]["sum"] )

		c1 = g.connectionGadget( script["add2"]["op1"] )
		self.assertTrue( c1.getMinimised() )

		script["add3"]["op1"].setInput( script["add2"]["sum"] )

		c2 = g.connectionGadget( script["add3"]["op1"] )
		self.assertFalse( c2.getMinimised() )

		g.setNodeInputConnectionsMinimised( script["add2"], True )

		self.assertTrue( c1.getMinimised() )
		self.assertFalse( c2.getMinimised() )

		g.setNodeOutputConnectionsMinimised( script["add1"], False )

		self.assertTrue( c1.getMinimised() )
		self.assertFalse( c2.getMinimised() )

		g.setNodeInputConnectionsMinimised( script["add2"], False )

		self.assertFalse( c1.getMinimised() )
		self.assertFalse( c2.getMinimised() )

	def testNodeGadgetCreatorReturningNull( self ) :

		class InvisibleNode( GafferTest.AddNode ) :

			def __init__( self, name = "InvisibleNode" ) :

				GafferTest.AddNode.__init__( self, name )

		IECore.registerRunTimeTyped( InvisibleNode )

		GafferUI.NodeGadget.registerNodeGadget( InvisibleNode, lambda node : None )

		script = Gaffer.ScriptNode()
		g = GafferUI.GraphGadget( script )

		script["n1"] = InvisibleNode()
		script["n2"] = InvisibleNode()

		self.assertEqual( g.nodeGadget( script["n1"] ), None )
		self.assertEqual( g.nodeGadget( script["n2"] ), None )

		script["n2"]["op1"].setInput( script["n1"]["sum"] )

		self.assertEqual( g.connectionGadget( script["n2"]["op1"] ), None )

		# in case it wasn't clear, hiding the nodes has zero
		# effect on their computations.

		script["n1"]["op1"].setValue( 12 )
		script["n1"]["op2"].setValue( 13 )
		script["n2"]["op2"].setValue( 100 )

		self.assertEqual( script["n2"]["sum"].getValue(), 125 )

	def testUpstreamNodeGadgets( self ) :

		script = Gaffer.ScriptNode()

		# a -> b -> c -> e -> f
		#           ^
		#           |
		#			d

		script["a"] = GafferTest.AddNode()
		script["b"] = GafferTest.AddNode()
		script["c"] = GafferTest.AddNode()
		script["d"] = GafferTest.AddNode()
		script["e"] = GafferTest.AddNode()
		script["f"] = GafferTest.AddNode()

		script["b"]["op1"].setInput( script["a"]["sum"] )
		script["c"]["op1"].setInput( script["b"]["sum"] )
		script["c"]["op2"].setInput( script["d"]["sum"] )

		script["e"]["op1"].setInput( script["c"]["sum"] )
		script["f"]["op1"].setInput( script["e"]["sum"] )

		g = GafferUI.GraphGadget( script )

		u = [ x.node().relativeName( script ) for x in g.upstreamNodeGadgets( script["c"] ) ]

		self.assertEqual( len( u ), 3 )
		self.assertEqual( set( u ), set( [ "a", "b", "d" ] ) )

		u = [ x.node().relativeName( script ) for x in g.upstreamNodeGadgets( script["f"] ) ]
		self.assertEqual( len( u ), 5 )
		self.assertEqual( set( u ), set( [ "a", "b", "d", "c", "e" ] ) )

		# the degreesOfSeparation argument should limit the depth
		# of the search.

		u = [ x.node().relativeName( script ) for x in g.upstreamNodeGadgets( script["c"], degreesOfSeparation = 1 ) ]
		self.assertEqual( len( u ), 2 )
		self.assertEqual( set( u ), set( [ "b", "d" ] ) )

		# filtered nodes should be ignored

		g.setFilter( Gaffer.StandardSet( [ script["f"], script["e"], script["a"] ] ) )

		u = [ x.node().relativeName( script ) for x in g.upstreamNodeGadgets( script["f"] ) ]
		self.assertEqual( u, [ "e" ] )

	def testDownstreamNodeGadgets( self ) :

		script = Gaffer.ScriptNode()

		# a -> b -> c -> e -> f
		#           |
		#           v
		#			d

		script["a"] = GafferTest.AddNode()
		script["b"] = GafferTest.AddNode()
		script["c"] = GafferTest.AddNode()
		script["d"] = GafferTest.AddNode()
		script["e"] = GafferTest.AddNode()
		script["f"] = GafferTest.AddNode()

		script["b"]["op1"].setInput( script["a"]["sum"] )
		script["c"]["op1"].setInput( script["b"]["sum"] )
		script["d"]["op1"].setInput( script["c"]["sum"] )
		script["e"]["op1"].setInput( script["c"]["sum"] )
		script["f"]["op1"].setInput( script["e"]["sum"] )

		g = GafferUI.GraphGadget( script )

		u = [ x.node().relativeName( script ) for x in g.downstreamNodeGadgets( script["b"] ) ]
		self.assertEqual( len( u ), 4 )
		self.assertEqual( set( u ), set( [ "c", "d", "e", "f" ] ) )

		u = [ x.node().relativeName( script ) for x in g.downstreamNodeGadgets( script["e"] ) ]
		self.assertEqual( len( u ), 1 )
		self.assertEqual( set( u ), set( [ "f" ] ) )

		u = [ x.node().relativeName( script ) for x in g.downstreamNodeGadgets( script["c"], degreesOfSeparation = 1 ) ]
		self.assertEqual( len( u ), 2 )
		self.assertEqual( set( u ), set( [ "d", "e" ] ) )

	def testConnectedNodeGadgets( self ) :

		script = Gaffer.ScriptNode()

		# a -> b -> c -> e -> f
		#           |
		#           v
		#			d

		script["a"] = GafferTest.AddNode()
		script["b"] = GafferTest.AddNode()
		script["c"] = GafferTest.AddNode()
		script["d"] = GafferTest.AddNode()
		script["e"] = GafferTest.AddNode()
		script["f"] = GafferTest.AddNode()

		script["b"]["op1"].setInput( script["a"]["sum"] )
		script["c"]["op1"].setInput( script["b"]["sum"] )
		script["d"]["op1"].setInput( script["c"]["sum"] )
		script["e"]["op1"].setInput( script["c"]["sum"] )
		script["f"]["op1"].setInput( script["e"]["sum"] )

		g = GafferUI.GraphGadget( script )

		# test traversing in both directions

		u = [ x.node().relativeName( script ) for x in g.connectedNodeGadgets( script["b"] ) ]
		self.assertEqual( set( u ), set( [ "a", "c", "d", "e", "f" ] ) )

		u = [ x.node().relativeName( script ) for x in g.connectedNodeGadgets( script["e"] ) ]
		self.assertEqual( set( u ), set( [ "a", "b", "c", "d", "f" ] ) )

		u = [ x.node().relativeName( script ) for x in g.connectedNodeGadgets( script["c"], degreesOfSeparation = 1 ) ]
		self.assertEqual( set( u ), set( [ "b", "d", "e" ] ) )

		# test traversing upstream

		u = [ x.node().relativeName( script ) for x in g.connectedNodeGadgets( script["c"], direction = Gaffer.Plug.Direction.In ) ]
		self.assertEqual( set( u ), set( [ "a", "b" ] ) )

		u = [ x.node().relativeName( script ) for x in g.connectedNodeGadgets( script["c"], direction = Gaffer.Plug.Direction.In, degreesOfSeparation = 1 ) ]
		self.assertEqual( set( u ), set( [ "b" ] ) )

		# test traversing downstream

		u = [ x.node().relativeName( script ) for x in g.connectedNodeGadgets( script["c"], direction = Gaffer.Plug.Direction.Out ) ]
		self.assertEqual( set( u ), set( [ "d", "e", "f" ] ) )

		u = [ x.node().relativeName( script ) for x in g.connectedNodeGadgets( script["c"], direction = Gaffer.Plug.Direction.Out, degreesOfSeparation = 1 ) ]
		self.assertEqual( set( u ), set( [ "d", "e" ] ) )

		# test that invisible nodes are ignored

		g.setFilter( Gaffer.StandardSet( [ script["f"], script["e"], script["c"] ] ) )

		u = [ x.node().relativeName( script ) for x in g.connectedNodeGadgets( script["e"] ) ]
		self.assertEqual( set( u ), set( [ "f", "c" ] ) )

		u = [ x.node().relativeName( script ) for x in g.connectedNodeGadgets( script["e"], direction = Gaffer.Plug.Direction.In ) ]
		self.assertEqual( set( u ), set( [ "c" ] ) )

		u = [ x.node().relativeName( script ) for x in g.connectedNodeGadgets( script["e"], direction = Gaffer.Plug.Direction.Out ) ]
		self.assertEqual( set( u ), set( [ "f" ] ) )

	def testSelectionHighlighting( self ) :

		script = Gaffer.ScriptNode()

		script["a"] = GafferTest.AddNode()
		script["b"] = GafferTest.AddNode()

		script.selection().add( script["a"] )

		g = GafferUI.GraphGadget( script )

		self.assertTrue( g.nodeGadget( script["a"] ).getHighlighted() )
		self.assertFalse( g.nodeGadget( script["b"] ).getHighlighted() )

		script.selection().add( script["b"] )

		self.assertTrue( g.nodeGadget( script["a"] ).getHighlighted() )
		self.assertTrue( g.nodeGadget( script["b"] ).getHighlighted() )

		script.selection().remove( script["a"] )

		self.assertFalse( g.nodeGadget( script["a"] ).getHighlighted() )
		self.assertTrue( g.nodeGadget( script["b"] ).getHighlighted() )

		script.selection().clear()

		self.assertFalse( g.nodeGadget( script["a"] ).getHighlighted() )
		self.assertFalse( g.nodeGadget( script["b"] ).getHighlighted() )

	def testNoDuplicatePositionPlugsAfterPasting( self ) :

		script = Gaffer.ScriptNode()
		script["n"] = Gaffer.Node()

		g = GafferUI.GraphGadget( script )
		g.setNodePosition( script["n"], imath.V2f( 1, 2 ) )
		self.assertTrue( g.hasNodePosition( script["n"] ) )

		script.execute( script.serialise( script, Gaffer.StandardSet( [ script["n"] ] ) ) )

		self.assertTrue( "__uiPosition" in script["n1"] )
		self.assertFalse( "__uiPosition1" in script["n1"] )

	def testErrorAndDelete( self ) :

		# Create a script with a dodgy node,
		# and a GraphGadget for displaying it.

		script = Gaffer.ScriptNode()
		script["n"] = GafferTest.BadNode()

		graphGadget = GafferUI.GraphGadget( script )

		# Arrange for the node to error on
		# a background thread.

		def f() :
			with IECore.IgnoredExceptions( Exception ) :
				script["n"]["out1"].getValue()

		r = threading.Thread( target = f )
		r.start()
		r.join()

		# Delete the node on the
		# foreground thread - this will
		# remove the NodeGadget inside
		# the GraphGadget.

		del script["n"]

		# Run idle events. Woe betide any NodeGadget
		# implementation assuming it will still be
		# alive at arbitrary points in the future!

		self.waitForIdle( 1000 )

	def testMovePlugWithInputConnection( self ) :

		script = Gaffer.ScriptNode()

		script["n1"] = Gaffer.Node()
		script["n1"]["p"] = Gaffer.Plug()

		script["n2"] = Gaffer.Node()
		script["n2"]["p"] = Gaffer.Plug()
		script["n2"]["p"].setInput( script["n1"]["p"] )

		g = GafferUI.GraphGadget( script )

		script["n3"] = Gaffer.Node()
		script["n3"]["p"] = script["n2"]["p"]

		connection = g.connectionGadget( script["n3"]["p"] )
		dstNodule = connection.dstNodule()
		srcNodule = connection.srcNodule()

		self.assertTrue( dstNodule.plug().isSame( script["n3"]["p"] ) )
		self.assertTrue( srcNodule.plug().isSame( script["n1"]["p"] ) )

		self.assertTrue( g.nodeGadget( script["n1"] ).isAncestorOf( srcNodule ) )
		self.assertTrue( g.nodeGadget( script["n3"] ).isAncestorOf( dstNodule ) )

	def testMovePlugWithInputConnectionOutsideGraph( self ) :

		script = Gaffer.ScriptNode()

		script["n1"] = Gaffer.Node()
		script["n1"]["p"] = Gaffer.Plug()

		script["n2"] = Gaffer.Node()
		script["n2"]["p"] = Gaffer.Plug()
		script["n2"]["p"].setInput( script["n1"]["p"] )

		g = GafferUI.GraphGadget( script )

		n3 = Gaffer.Node()
		n3["p"] = script["n2"]["p"]

		self.assertEqual( g.connectionGadget( n3["p"] ), None )

	def testRemoveNoduleWithInputConnection( self ) :

		script = Gaffer.ScriptNode()

		script["n1"] = Gaffer.Node()
		script["n1"]["p"] = Gaffer.Plug()

		script["n2"] = Gaffer.Node()
		script["n2"]["p"] = Gaffer.Plug()
		script["n2"]["p"].setInput( script["n1"]["p"] )

		g = GafferUI.GraphGadget( script )

		self.assertTrue( g.nodeGadget( script["n2"] ).nodule( script["n2"]["p"] ) is not None )
		self.assertTrue( g.connectionGadget( script["n2"]["p"] ) is not None )

		Gaffer.Metadata.registerValue( script["n2"]["p"], "nodule:type", "" )
		self.assertTrue( g.nodeGadget( script["n2"] ).nodule( script["n2"]["p"] ) is None )
		self.assertTrue( g.connectionGadget( script["n2"]["p"] ) is None )

	def testRemoveNoduleWithOutputConnections( self ) :

		script = Gaffer.ScriptNode()

		script["n1"] = Gaffer.Node()
		script["n1"]["out"] = Gaffer.Plug( direction = Gaffer.Plug.Direction.Out )

		script["n2"] = Gaffer.Node()
		script["n2"]["in"] = Gaffer.Plug()
		script["n2"]["in"].setInput( script["n1"]["out"] )

		g = GafferUI.GraphGadget( script )

		c = g.connectionGadget( script["n2"]["in"] )
		self.assertTrue( c is not None )
		self.assertTrue( c.srcNodule().plug().isSame( script["n1"]["out"] ) )
		self.assertTrue( c.dstNodule().plug().isSame( script["n2"]["in"] ) )

		Gaffer.Metadata.registerValue( script["n1"]["out"], "nodule:type", "" )

		c = g.connectionGadget( script["n2"]["in"] )
		self.assertTrue( c is not None )
		self.assertTrue( c.srcNodule() is None )
		self.assertTrue( c.dstNodule().plug().isSame( script["n2"]["in"] ) )

		Gaffer.Metadata.registerValue( script["n1"]["out"], "nodule:type", "GafferUI::StandardNodule" )

		c = g.connectionGadget( script["n2"]["in"] )
		self.assertTrue( c is not None )
		self.assertTrue( c.srcNodule().plug().isSame( script["n1"]["out"] ) )
		self.assertTrue( c.dstNodule().plug().isSame( script["n2"]["in"] ) )

	def testAddNoduleWithInputConnection( self ) :

		script = Gaffer.ScriptNode()

		script["n"] = Gaffer.Node()
		script["n"]["in"] = Gaffer.Plug()
		script["n"]["out"] = Gaffer.Plug( direction = Gaffer.Plug.Direction.Out )
		script["n"]["out"].setInput( script["n"]["in"] )

		Gaffer.Metadata.registerValue( script["n"]["out"], "nodule:type", "" )

		g = GafferUI.GraphGadget( script )
		self.assertTrue( g.nodeGadget( script["n"] ).nodule( script["n"]["out"] ) is None )
		self.assertTrue( g.connectionGadget( script["n"]["out"] ) is None )

		Gaffer.Metadata.registerValue( script["n"]["out"], "nodule:type", "GafferUI::StandardNodule" )

		self.assertTrue( g.nodeGadget( script["n"] ).nodule( script["n"]["out"] ) is not None )
		self.assertTrue( g.connectionGadget( script["n"]["out"] ) is None )

	def testAddNoduleWithOutputConnection( self ) :

		script = Gaffer.ScriptNode()

		script["n1"] = Gaffer.Node()
		script["n1"]["out"] = Gaffer.Plug( direction = Gaffer.Plug.Direction.Out )

		script["n2"] = Gaffer.Node()
		script["n2"]["in"] = Gaffer.Plug()
		script["n2"]["in"].setInput( script["n1"]["out"] )

		Gaffer.Metadata.registerValue( script["n1"]["out"], "nodule:type", "" )

		g = GafferUI.GraphGadget( script )
		self.assertTrue( g.nodeGadget( script["n1"] ).nodule( script["n1"]["out"] ) is None )
		self.assertTrue( g.connectionGadget( script["n2"]["in"] ) is not None )
		self.assertTrue( g.connectionGadget( script["n2"]["in"] ).srcNodule() is None )

		Gaffer.Metadata.registerValue( script["n1"]["out"], "nodule:type", "GafferUI::StandardNodule" )

		self.assertTrue( g.nodeGadget( script["n1"] ).nodule( script["n1"]["out"] ) is not None )
		self.assertTrue( g.connectionGadget( script["n2"]["in"] ) is not None )
		self.assertTrue( g.connectionGadget( script["n2"]["in"] ).srcNodule() is not None )

	def testRemoveNonNodulePlug( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["p"] = Gaffer.Plug()
		Gaffer.Metadata.registerValue( s["n"]["p"], "nodule:type", "" )

		g = GafferUI.GraphGadget( s )
		self.assertTrue( g.nodeGadget( s["n"] ).nodule( s["n"]["p"] ) is None )

		# Once upon a time, this would crash.
		del s["n"]["p"]

	def testEnabledException( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = GafferTest.AddNode()

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( "parent['n']['enabled'] = undefinedVariable" )

		g = GafferUI.GraphGadget( s )
		self.assertTrue( g.nodeGadget( s["n"] ) is not None )

	def testLayoutAccessors( self ) :

		s = Gaffer.ScriptNode()
		g = GafferUI.GraphGadget( s )
		l = g.getLayout()
		self.assertTrue( isinstance( l, GafferUI.StandardGraphLayout ) )

		l2 = GafferUI.StandardGraphLayout()
		g.setLayout( l2 )
		self.assertTrue( g.getLayout().isSame( l2 ) )

		g.setLayout( l )
		self.assertTrue( g.getLayout().isSame( l ) )

	def testUnpositionedNodeGadgets( self ) :

		s = Gaffer.ScriptNode()
		g = GafferUI.GraphGadget( s )

		s["n"] = Gaffer.Node()
		self.assertEqual( g.unpositionedNodeGadgets(), [ g.nodeGadget( s["n"] ) ] )

		g.setNodePosition( s["n"], imath.V2f( 0 ) )
		self.assertEqual( g.unpositionedNodeGadgets(), [] )

	def testInputConnectionMaintainedOnNoduleMove( self ) :

		s = Gaffer.ScriptNode()
		g = GafferUI.GraphGadget( s )

		s["n1"] = GafferTest.AddNode()
		s["n2"] = GafferTest.AddNode()

		s["n2"]["op1"].setInput( s["n1"]["sum"] )

		self.assertTrue( g.connectionGadget( s["n2"]["op1"] ) is not None )

		for section in ( "top", "bottom", "top", "left", "right", "left", "bottom", "right" ) :
			Gaffer.Metadata.registerValue( s["n2"]["op1"], "noduleLayout:section", section )
			connection = g.connectionGadget( s["n2"]["op1"] )
			self.assertTrue( connection is not None )
			self.assertTrue( connection.srcNodule() is not None )
			self.assertTrue( connection.srcNodule().isSame( g.nodeGadget( s["n1"] ).nodule( s["n1"]["sum"] ) ) )
			self.assertTrue( connection.dstNodule().isSame( g.nodeGadget( s["n2"] ).nodule( s["n2"]["op1"] ) ) )

	def testOutputConnectionMaintainedOnNoduleMove( self ) :

		s = Gaffer.ScriptNode()
		g = GafferUI.GraphGadget( s )

		s["n1"] = GafferTest.AddNode()
		s["n2"] = GafferTest.AddNode()

		s["n2"]["op1"].setInput( s["n1"]["sum"] )

		self.assertTrue( g.connectionGadget( s["n2"]["op1"] ) is not None )

		for section in ( "top", "bottom", "top", "left", "right", "left", "bottom", "right" ) :
			Gaffer.Metadata.registerValue( s["n1"]["sum"], "noduleLayout:section", section )
			connection = g.connectionGadget( s["n2"]["op1"] )
			self.assertTrue( connection is not None )
			self.assertTrue( connection.srcNodule() is not None )
			self.assertTrue( connection.srcNodule().isSame( g.nodeGadget( s["n1"] ).nodule( s["n1"]["sum"] ) ) )
			self.assertTrue( connection.dstNodule().isSame( g.nodeGadget( s["n2"] ).nodule( s["n2"]["op1"] ) ) )

	def testInputConnectionMaintainedOnNestedNoduleMove( self ) :

		s = Gaffer.ScriptNode()
		g = GafferUI.GraphGadget( s )

		s["n1"] = GafferTest.AddNode()
		s["n2"] = GafferTest.ArrayPlugNode()

		Gaffer.Metadata.registerValue( s["n2"]["in"], "nodule:type", "GafferUI::CompoundNodule" )

		s["n2"]["in"][0].setInput( s["n1"]["sum"] )

		self.assertTrue( g.connectionGadget( s["n2"]["in"][0] ) is not None )

		for section in ( "top", "bottom", "top", "left", "right", "left", "bottom", "right" ) :
			Gaffer.Metadata.registerValue( s["n2"]["in"], "noduleLayout:section", section )
			connection = g.connectionGadget( s["n2"]["in"][0] )
			self.assertTrue( connection is not None )
			self.assertTrue( connection.srcNodule() is not None )
			self.assertTrue( connection.srcNodule().isSame( g.nodeGadget( s["n1"] ).nodule( s["n1"]["sum"] ) ) )
			self.assertTrue( connection.dstNodule().isSame( g.nodeGadget( s["n2"] ).nodule( s["n2"]["in"][0] ) ) )

	def testNodeGadgetMetadataChanges( self ) :

		s = Gaffer.ScriptNode()
		g = GafferUI.GraphGadget( s )

		s["n1"] = GafferTest.AddNode()
		s["n2"] = GafferTest.AddNode()
		s["n2"]["op1"].setInput( s["n1"]["sum"] )

		def assertBothVisible() :

			ng1 = g.nodeGadget( s["n1"] )
			ng2 = g.nodeGadget( s["n2"] )
			c = g.connectionGadget( s["n2"]["op1"] )
			self.assertTrue( isinstance( ng1, GafferUI.StandardNodeGadget ) )
			self.assertTrue( isinstance( ng2, GafferUI.StandardNodeGadget ) )
			self.assertTrue( isinstance( c, GafferUI.StandardConnectionGadget ) )
			self.assertTrue( c.srcNodule().isSame( ng1.nodule( s["n1"]["sum"] ) ) )
			self.assertTrue( c.dstNodule().isSame( ng2.nodule( s["n2"]["op1"] ) ) )

		assertBothVisible()

		Gaffer.Metadata.registerValue( s["n1"], "nodeGadget:type", "" )

		def assertN1Hidden() :

			ng1 = g.nodeGadget( s["n1"] )
			ng2 = g.nodeGadget( s["n2"] )
			c = g.connectionGadget( s["n2"]["op1"] )
			self.assertTrue( ng1 is None )
			self.assertTrue( isinstance( ng2, GafferUI.StandardNodeGadget ) )
			self.assertTrue( isinstance( c, GafferUI.StandardConnectionGadget ) )
			self.assertTrue( c.srcNodule() is None )
			self.assertTrue( c.dstNodule().isSame( ng2.nodule( s["n2"]["op1"] ) ) )

		assertN1Hidden()

		Gaffer.Metadata.registerValue( s["n2"], "nodeGadget:type", "" )

		def assertBothHidden() :

			self.assertTrue( g.nodeGadget( s["n1"] ) is None )
			self.assertTrue( g.nodeGadget( s["n2"] ) is None )
			self.assertTrue( g.connectionGadget( s["n2"]["op1"] ) is None )

		assertBothHidden()

		Gaffer.Metadata.registerValue( s["n2"], "nodeGadget:type", "GafferUI::StandardNodeGadget" )

		assertN1Hidden()

		Gaffer.Metadata.registerValue( s["n1"], "nodeGadget:type", "GafferUI::StandardNodeGadget" )

		assertBothVisible()

	def testConnectionGadgetsIncludesDanglingConnections( self ) :

		s = Gaffer.ScriptNode()

		s["n1"] = Gaffer.Node()
		s["n1"]["c"] = Gaffer.Color3fPlug( direction = Gaffer.Plug.Direction.Out, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["n2"] = Gaffer.Node()
		s["n2"]["c"] = Gaffer.Color3fPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n2"]["c"]["r"].setInput( s["n1"]["c"]["r"] )

		Gaffer.Metadata.registerValue( s["n2"]["c"], "compoundNumericNodule:childrenVisible", True )

		g = GafferUI.GraphGadget( s )
		c = g.connectionGadgets( s["n2"]["c"]["r"] )
		self.assertEqual( len( c ), 1 )
		self.assertEqual( c[0].dstNodule(), g.nodeGadget( s["n2"] ).nodule( s["n2"]["c"]["r"] ) )
		self.assertIsNone( c[0].srcNodule() )

	def testChangeNodeGadgetForUnviewedNode( self ) :

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()
		s["b"]["n"] = Gaffer.Node()

		g = GafferUI.GraphGadget( s )
		self.assertIsNotNone( g.nodeGadget( s["b"] ) )
		self.assertIsNone( g.nodeGadget( s["b"]["n"] ) )

		Gaffer.Metadata.registerValue( s["b"]["n"], "nodeGadget:type", "GafferUI::AuxiliaryNodeGadget" )
		self.assertIsNone( g.nodeGadget( s["b"]["n"] ) )

	def testActivePlugsAndNodes( self ) :

		s = Gaffer.ScriptNode()

		# Basic network with single and multiple inputs

		s["add1"] = GafferTest.AddNode()
		s["add2"] = GafferTest.AddNode()
		s["add3"] = GafferTest.AddNode()
		s["add4"] = GafferTest.AddNode()

		s["add1"]["op1"].setInput( s["add2"]["sum"] )
		s["add1"]["op2"].setInput( s["add3"]["sum"] )

		s["add2"]["op1"].setInput( s["add4"]["sum"] )

		c = Gaffer.Context()

		plugs, nodes = GafferUI.GraphGadget._activePlugsAndNodes( s["add1"]["sum"], c )
		self.assertEqual( set( plugs ), set( [ s["add1"]["op1"], s["add1"]["op2"], s["add2"]["op1"] ] ) )
		self.assertEqual( set( nodes ), set( [ s["add1"], s["add2"], s["add3"], s["add4"] ] ) )


		# Test disabling
		s["add2"]["op1"].setInput( None )
		s["add1"]["enabled"].setValue( False )
		plugs, nodes = GafferUI.GraphGadget._activePlugsAndNodes( s["add1"]["sum"], c )
		self.assertEqual( set( plugs ), set( [ s["add1"]["op1"] ] ) )
		self.assertEqual( set( nodes ), set( [ s["add1"], s["add2"] ] ) )

		s["add1"]["expr"] = Gaffer.Expression()
		s["add1"]["expr"].setExpression( 'parent["enabled"] = True', "python" )
		plugs, nodes = GafferUI.GraphGadget._activePlugsAndNodes( s["add1"]["sum"], c )
		self.assertEqual( set( plugs ), set( [ s["add1"]["op1"], s["add1"]["op2"], s["add1"]["enabled"] ] ) )
		self.assertEqual( set( nodes ), set( [ s["add1"], s["add2"], s["add3"], s["add1"]["expr"] ] ) )

		s["add1"]["expr"].setExpression( 'parent["enabled"] = False', "python" )
		plugs, nodes = GafferUI.GraphGadget._activePlugsAndNodes( s["add1"]["sum"], c )
		self.assertEqual( set( plugs ), set( [ s["add1"]["op1"], s["add1"]["enabled"] ] ) )
		self.assertEqual( set( nodes ), set( [ s["add1"], s["add2"], s["add1"]["expr"] ] ) )

		del s["add1"]["expr"]
		s["add1"]["enabled"].setValue( True )


		# Setup switch instead
		s["add1"]["op1"].setInput( None )
		s["add1"]["op2"].setInput( None )

		s["switch"] = Gaffer.Switch()
		s["switch"].setup( Gaffer.FloatPlug() )

		s["switch"]["in"][0].setInput( s["add3"]["sum"] )
		s["switch"]["in"][1].setInput( s["add4"]["sum"] )


		# Test with index set to a hardcoded value, which will just follow the connections created inside
		# the Switch when the index isn't computed.

		plugs, nodes = GafferUI.GraphGadget._activePlugsAndNodes( s["switch"]["out"], c )
		self.assertEqual( set( plugs ), set( [ s["switch"]["in"][0], s["switch"]["out"] ] ) )
		self.assertEqual( set( nodes ), set( [ s["switch"], s["add3"] ] ) )

		s["switch"]["index"].setValue( 1 )

		plugs, nodes = GafferUI.GraphGadget._activePlugsAndNodes( s["switch"]["out"], c )
		self.assertEqual( set( plugs ), set( [ s["switch"]["in"][1], s["switch"]["out"] ] ) )
		self.assertEqual( set( nodes ), set( [ s["switch"], s["add4"] ] ) )

		s["switch"]["enabled"].setValue( False )

		plugs, nodes = GafferUI.GraphGadget._activePlugsAndNodes( s["switch"]["out"], c )
		self.assertEqual( set( plugs ), set( [ s["switch"]["in"][0], s["switch"]["out"] ] ) )
		self.assertEqual( set( nodes ), set( [ s["switch"], s["add3"] ] ) )

		s["switch"]["enabled"].setValue( True )

		# Now set with an expression, so that there is actually a compute happening on the Switch to track

		s["switch"]["expr"] = Gaffer.Expression()
		s["switch"]["expr"].setExpression( 'parent["index"] = context["foo"]', "python" )

		# Error during evaluation falls back to taking all inputs
		with IECore.CapturingMessageHandler() as mh :
			plugs, nodes = GafferUI.GraphGadget._activePlugsAndNodes( s["switch"]["out"], c )

		self.assertEqual( len( mh.messages ), 1 )
		self.assertEqual( mh.messages[0].level, IECore.Msg.Level.Warning )
		self.assertEqual( mh.messages[0].context, "Gaffer" )
		self.assertEqual( mh.messages[0].message, 'Error during graph active state visualisation: switch.expr.__execute : Context has no variable named "foo"' )
		self.assertEqual( set( plugs ), set( [ s["switch"]["in"][0], s["switch"]["in"][1], s["switch"]["index"] ] ) )
		self.assertEqual( set( nodes ), set( [ s["switch"], s["add3"], s["add4"], s["switch"]["expr"] ] ) )

		# Test setting switch index from context
		c["foo"] = 0
		plugs, nodes = GafferUI.GraphGadget._activePlugsAndNodes( s["switch"]["out"], c )
		self.assertEqual( set( plugs ), set( [ s["switch"]["in"][0], s["switch"]["index"] ] ) )
		self.assertEqual( set( nodes ), set( [ s["switch"], s["add3"], s["switch"]["expr"] ] ) )

		c["foo"] = 1
		plugs, nodes = GafferUI.GraphGadget._activePlugsAndNodes( s["switch"]["out"], c )
		self.assertEqual( set( plugs ), set( [ s["switch"]["in"][1], s["switch"]["index"] ] ) )
		self.assertEqual( set( nodes ), set( [ s["switch"], s["add4"], s["switch"]["expr"] ] ) )

		# Also test disabling
		s["switch"]["expr2"] = Gaffer.Expression()
		s["switch"]["expr2"].setExpression( 'parent["enabled"] = False', "python" )

		plugs, nodes = GafferUI.GraphGadget._activePlugsAndNodes( s["switch"]["out"], c )
		self.assertEqual( set( plugs ), set( [ s["switch"]["in"][0], s["switch"]["enabled"] ] ) )
		self.assertEqual( set( nodes ), set( [ s["switch"], s["add3"], s["switch"]["expr2"] ] ) )

		s["switch"]["expr2"].setExpression( 'parent["enabled"] = True', "python" )

		plugs, nodes = GafferUI.GraphGadget._activePlugsAndNodes( s["switch"]["out"], c )
		self.assertEqual( set( plugs ), set( [ s["switch"]["in"][1], s["switch"]["enabled"], s["switch"]["index"] ] ) )
		self.assertEqual( set( nodes ), set( [ s["switch"], s["add4"], s["switch"]["expr2"], s["switch"]["expr"] ] ) )

		# And NameSwitch
		s["nameSwitch"] = Gaffer.NameSwitch()
		s["nameSwitch"].setup( Gaffer.FloatPlug() )

		s["nameSwitch"]["in"].resize( 3 )
		s["nameSwitch"]["in"][0]["value"].setInput( s["add3"]["sum"] ) # Default
		s["nameSwitch"]["in"][1]["name"].setValue( "AAA" )
		s["nameSwitch"]["in"][1]["value"].setInput( s["add1"]["sum"] )
		s["nameSwitch"]["in"][2]["value"].setInput( s["add2"]["sum"] )

		s["nameSwitch"]["expr"] = Gaffer.Expression()
		s["nameSwitch"]["expr"].setExpression( 'parent["selector"] = context["foo"]', "python" )

		# Set one name with an expression - the output will always depend on this name
		s["nameSwitch"]["expr2"] = Gaffer.Expression()
		s["nameSwitch"]["expr2"].setExpression( 'parent["in"]["in2"]["name"] = "BBB"', "python" )

		# Test default output
		c["foo"] = "XXX"
		plugs, nodes = GafferUI.GraphGadget._activePlugsAndNodes( s["nameSwitch"]["out"], c )
		self.assertEqual( set( plugs ), set( [ s["nameSwitch"]["in"]["in0"]["value"], s["nameSwitch"]["selector"], s["nameSwitch"]["in"]["in2"]["name"], s["nameSwitch"]["__index"] ] ) )
		self.assertEqual( set( nodes ), set( [ s["nameSwitch"], s["add3"], s["nameSwitch"]["expr"], s["nameSwitch"]["expr2"] ] ) )

		# Test first input
		c["foo"] = "AAA"
		plugs, nodes = GafferUI.GraphGadget._activePlugsAndNodes( s["nameSwitch"]["out"], c )
		self.assertEqual( set( plugs ), set( [ s["nameSwitch"]["in"]["in1"]["value"], s["nameSwitch"]["selector"], s["nameSwitch"]["in"]["in2"]["name"], s["nameSwitch"]["__index"] ] ) )
		self.assertEqual( set( nodes ), set( [ s["nameSwitch"], s["add1"], s["nameSwitch"]["expr"], s["nameSwitch"]["expr2"] ] ) )

		# Test second input
		c["foo"] = "BBB"
		plugs, nodes = GafferUI.GraphGadget._activePlugsAndNodes( s["nameSwitch"]["out"], c )
		self.assertEqual( set( plugs ), set( [ s["nameSwitch"]["in"]["in2"]["value"], s["nameSwitch"]["selector"], s["nameSwitch"]["in"]["in2"]["name"], s["nameSwitch"]["__index"] ] ) )
		self.assertEqual( set( nodes ), set( [ s["nameSwitch"], s["add2"], s["nameSwitch"]["expr"], s["nameSwitch"]["expr2"] ] ) )

		# Test same result if just querying value of output
		plugs, nodes = GafferUI.GraphGadget._activePlugsAndNodes( s["nameSwitch"]["out"]["value"], c )
		self.assertEqual( set( plugs ), set( [ s["nameSwitch"]["in"]["in2"]["value"], s["nameSwitch"]["selector"], s["nameSwitch"]["in"]["in2"]["name"], s["nameSwitch"]["__index"] ] ) )
		self.assertEqual( set( nodes ), set( [ s["nameSwitch"], s["add2"], s["nameSwitch"]["expr"], s["nameSwitch"]["expr2"] ] ) )

		# Name of the output only depends names of inputs
		plugs, nodes = GafferUI.GraphGadget._activePlugsAndNodes( s["nameSwitch"]["out"]["name"], c )
		self.assertEqual( set( plugs ), set( [ s["nameSwitch"]["selector"], s["nameSwitch"]["in"]["in2"]["name"], s["nameSwitch"]["__index"] ] ) )
		self.assertEqual( set( nodes ), set( [ s["nameSwitch"], s["nameSwitch"]["expr"], s["nameSwitch"]["expr2"] ] ) )

		# Test ContextProcessor
		s["contextVariables"] = Gaffer.ContextVariables()
		s["contextVariables"].setup( Gaffer.FloatPlug() )
		s["contextVariables"]["variables"]["setVar"] = Gaffer.NameValuePlug( "foo", Gaffer.StringPlug( "value", defaultValue = 'AAA' ), True )

		s["contextVariables"]["in"].setInput( s["nameSwitch"]["out"]["value"] )
		plugs, nodes = GafferUI.GraphGadget._activePlugsAndNodes( s["contextVariables"]["out"], c )
		self.assertEqual( set( plugs ), set( [ s["contextVariables"]["in"], s["nameSwitch"]["in"]["in1"]["value"], s["nameSwitch"]["selector"], s["nameSwitch"]["in"]["in2"]["name"], s["nameSwitch"]["__index"] ] ) )
		self.assertEqual( set( nodes ), set( [ s["contextVariables"], s["nameSwitch"], s["add1"], s["nameSwitch"]["expr"], s["nameSwitch"]["expr2"] ] ) )

		s["contextVariables"]["enabled"].setValue( False )
		plugs, nodes = GafferUI.GraphGadget._activePlugsAndNodes( s["contextVariables"]["out"], c )
		self.assertEqual( set( plugs ), set( [ s["contextVariables"]["in"], s["nameSwitch"]["in"]["in2"]["value"], s["nameSwitch"]["selector"], s["nameSwitch"]["in"]["in2"]["name"], s["nameSwitch"]["__index"] ] ) )
		self.assertEqual( set( nodes ), set( [ s["contextVariables"], s["nameSwitch"], s["add2"], s["nameSwitch"]["expr"], s["nameSwitch"]["expr2"] ] ) )


		# The behaviour of a Box is just a consequence of the previous behaviour, but it's somewhat complex
		# and confusing, so I've got some specific tests for it
		s["add5"] = GafferTest.AddNode()
		s["add6"] = GafferTest.AddNode()

		s["add3"]["op1"].setInput( s["add5"]["sum"] )
		s["add4"]["op1"].setInput( s["add6"]["sum"] )

		s["add1"]["op1"].setInput( s["add3"]["sum"] )
		s["add2"]["op1"].setInput( s["add4"]["sum"] )

		box = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["add3"], s["add4"] ] ) )


		# The box itself counts as active, plus the input which is used by the internal network
		plugs, nodes = GafferUI.GraphGadget._activePlugsAndNodes( s["add1"]["sum"], c )
		self.assertEqual( set( plugs ), set( [ s["add1"]["op1"], box["add3"]["op1"], box["op1"], box["sum"] ] ) )
		self.assertEqual( set( nodes ), set( [ box, s["add1"], box["add3"], s["add5"] ] ) )


		# Add BoxIO nodes
		Gaffer.BoxIO.insert( box )

		# And add a passThrough connection
		box["BoxOut1"]["passThrough"].setInput( box["BoxIn"]["out"] )

		# Now we've got a bunch of intermediate BoxIO and Switch nodes
		plugs, nodes = GafferUI.GraphGadget._activePlugsAndNodes( s["add2"]["sum"], c )
		self.assertEqual( set( plugs ), set( [ s["add2"]["op1"], box["add4"]["op1"], box["op2"], box["sum1"], box["BoxIn1"]["__in"], box["BoxOut1"]["in"], box["BoxOut1"]["__out"], box["BoxOut1"]["__switch"]["in"]["in1"], box["BoxOut1"]["__switch"]["out"], box["BoxIn1"]["out"] ] ) )
		self.assertEqual( set( nodes ), set( [ box, s["add2"], box["add4"], s["add6"], box["BoxOut1"]["__switch"], box["BoxOut1"], box["BoxIn1"] ] ) )

		# Disabling uses the passThrough instead
		box["enabled"].setValue( False )
		plugs, nodes = GafferUI.GraphGadget._activePlugsAndNodes( s["add2"]["sum"], c )
		self.assertEqual( set( plugs ), set( [ s["add2"]["op1"], box["op1"], box["sum1"], box["BoxIn"]["__in"], box["BoxOut1"]["passThrough"], box["BoxOut1"]["__out"], box["BoxOut1"]["__switch"]["in"]["in0"], box["BoxOut1"]["__switch"]["out"], box["BoxIn"]["out"] ] ) )
		self.assertEqual( set( nodes ), set( [ box, s["add2"], s["add5"], box["BoxOut1"]["__switch"], box["BoxOut1"], box["BoxIn"] ] ) )

		# If we disconnect the passThrough, nothing gets through
		box["BoxOut1"]["passThrough"].setInput( None )
		plugs, nodes = GafferUI.GraphGadget._activePlugsAndNodes( s["add2"]["sum"], c )
		self.assertEqual( set( plugs ), set( [ s["add2"]["op1"], box["sum1"], box["BoxOut1"]["__out"], box["BoxOut1"]["__switch"]["in"]["in0"], box["BoxOut1"]["__switch"]["out"] ] ) )
		self.assertEqual( set( nodes ), set( [ box, s["add2"], box["BoxOut1"]["__switch"], box["BoxOut1"] ] ) )


		# Test a box with promoted array plug
		s["add7"] = GafferTest.AddNode()
		s["add1"]["op1"].setInput( s["add7"]["sum"] )
		box2 = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["add7"] ] ) )
		box2["add7"]["arrayInput"] = Gaffer.ArrayPlug( "arrayInput", Gaffer.Plug.Direction.In, Gaffer.FloatPlug() )
		box2.promotePlug( box2["add7"]["arrayInput"] )
		box2["arrayInput"][0].setInput( s["add5"]["sum"] )
		box2["arrayInput"][1].setInput( s["add6"]["sum"] )
		plugs, nodes = GafferUI.GraphGadget._activePlugsAndNodes( s["add1"]["sum"], c )
		self.assertEqual( set( plugs ), set( [ s["add1"]["op1"], box2["sum"], box2["add7"]["arrayInput"], box2["arrayInput"][0], box2["arrayInput"][1] ] ) )
		self.assertEqual( set( nodes ), set( [ s["add1"], box2, box2["add7"], s["add5"], s["add6"] ] ) )

		# Test Loop

		s["loopSwitch"] = Gaffer.Switch()
		s["loopSwitch"].setup( Gaffer.FloatPlug() )
		for i in range( 5 ):
			s["loopSwitchIn%i" % i ] = GafferTest.AddNode()
			s["loopSwitchIn%i" % i ]["op1"].setValue( (i+1) * 10 ** i )
			s["loopSwitch"]["in"][-1].setInput( s["loopSwitchIn%i" % i ]["sum"] )

		s["loopSwitch"]["expr"] = Gaffer.Expression()
		s["loopSwitch"]["expr"].setExpression( 'parent["index"] = context.get("loop:index", 4)', "python" )

		s["start"] = GafferTest.AddNode()
		s["start"]["op1"].setValue( 900000 )

		s["loop"] = Gaffer.Loop()
		s["loop"].setup( Gaffer.FloatPlug() )
		s["loop"]["in"].setInput( s["start"]["sum"] )

		s["merge"] = GafferTest.AddNode()
		s["merge"]["op1"].setInput( s["loop"]["previous"] )
		s["loop"]["next"].setInput( s["merge"]["sum"] )
		s["merge"]["op2"].setInput( s["loopSwitch"]["out"] )

		s["loop"]["iterations"].setValue( 4 )

		self.assertEqual( s["loop"]["out"].getValue(), 904321.0 )

		# We don't track through the loop for every separate loop context, we just fall back to a naive
		# traversal that takes every input
		plugs, nodes = GafferUI.GraphGadget._activePlugsAndNodes( s["loop"]["out"], c )
		self.assertEqual( set( nodes ), set( [ s["loop"], s["start"], s["merge"], s["loopSwitch"], s["loopSwitch"]["expr"] ] + [ s["loopSwitchIn%i"%i] for i in range(5) ] ) )

		# Same deal if we start from a node in the middle of the loop iteration
		plugs, nodes = GafferUI.GraphGadget._activePlugsAndNodes( s["merge"]["sum"], c )
		self.assertEqual( set( nodes ), set( [ s["loop"], s["start"], s["merge"], s["loopSwitch"], s["loopSwitch"]["expr"] ] + [ s["loopSwitchIn%i"%i] for i in range(5) ] ) )


	def testActiveCompoundPlugs( self ):

		s = Gaffer.ScriptNode()
		c = Gaffer.Context()

		p = Gaffer.Plug()
		p.addChild( Gaffer.StringPlug() )
		p.addChild( Gaffer.FloatPlug() )

		s["contextVariables"] = Gaffer.ContextVariables()
		s["contextVariables"].setup( p )

		s["dummyNode"] = Gaffer.ComputeNode()
		s["dummyNode"]["in"] = p.createCounterpart( "in", Gaffer.Plug.Direction.In )
		s["dummyNode"]["out"] = p.createCounterpart( "out", Gaffer.Plug.Direction.Out )
		s["dummyNode"]["in"].setInput( s["contextVariables"]["out"] )

		# Check that we don't explicitly include child connections when the parents are connected
		plugs, nodes = GafferUI.GraphGadget._activePlugsAndNodes( s["dummyNode"]["out"], c )
		self.assertEqual( set( plugs ), set( [ s["dummyNode"]["in"] ] ) )
		self.assertEqual( set( nodes ), set( [ s["contextVariables"], s["dummyNode"] ] ) )

		s["switch"] = Gaffer.Switch()
		s["switch"].setup( p )

		s["switch"]["in"][0].setInput( s["dummyNode"]["out"] )
		s["switch"]["in"][1].setInput( s["contextVariables"]["out"] )
		s["switch"]["expr"] = Gaffer.Expression()
		s["switch"]["expr"].setExpression( 'parent["index"] = 1' )

		# Check that we take only the children of active inputs
		plugs, nodes = GafferUI.GraphGadget._activePlugsAndNodes( s["switch"]["out"], c )
		self.assertEqual( set( plugs ), set( [ s["switch"]["in"]["in1"], s["switch"]["index"] ] ) )
		self.assertEqual( set( nodes ), set( [ s["contextVariables"], s["switch"], s["switch"]["expr"] ] ) )

		# Test that if a compound plug gets split, we take the children, even from one of the special case nodes
		s["dummyNode"]["in"]["FloatPlug"].setInput( None )
		plugs, nodes = GafferUI.GraphGadget._activePlugsAndNodes( s["dummyNode"]["out"], c )
		self.assertEqual( set( plugs ), set( [ s["dummyNode"]["in"]["StringPlug"] ] ) )
		self.assertEqual( set( nodes ), set( [ s["contextVariables"], s["dummyNode"] ] ) )

		s["switch"]["in"][1]["StringPlug"].setInput( None )
		plugs, nodes = GafferUI.GraphGadget._activePlugsAndNodes( s["switch"]["out"], c )
		self.assertEqual( set( plugs ), set( [ s["switch"]["in"]["in1"]["FloatPlug"], s["switch"]["index"] ] ) )
		self.assertEqual( set( nodes ), set( [ s["contextVariables"], s["switch"], s["switch"]["expr"] ] ) )

		s["dummyNode"]["in"].setInput( None )
		s["contextVariables"]["in"]["StringPlug"].setInput( s["dummyNode"]["out"]["StringPlug"] )
		plugs, nodes = GafferUI.GraphGadget._activePlugsAndNodes( s["contextVariables"]["out"], c )
		self.assertEqual( set( plugs ), set( [ s["contextVariables"]["in"]["StringPlug"] ] ) )
		self.assertEqual( set( nodes ), set( [ s["contextVariables"], s["dummyNode"] ] ) )

	testActivePlugsAndNodesCancellationCondition = threading.Condition()
	def testActivePlugsAndNodesCancellation( self ) :

		def testThreadFunc( plug, canceller, testInstance ):
			with testInstance.assertRaises( IECore.Cancelled ):
				GafferUI.GraphGadget._activePlugsAndNodes( plug, Gaffer.Context( Gaffer.Context(), canceller ) )

		s = Gaffer.ScriptNode()

		# Test a computation that supports cancellation

		s["add"] = GafferTest.AddNode()

		s["addExpr"] = Gaffer.Expression()
		s["addExpr"].setExpression( inspect.cleandoc(
			"""
			import time
			import Gaffer
			import GafferUITest.GraphGadgetTest

			with GafferUITest.GraphGadgetTest.testActivePlugsAndNodesCancellationCondition:
				GafferUITest.GraphGadgetTest.testActivePlugsAndNodesCancellationCondition.notify()
			while True:
				IECore.Canceller.check( context.canceller() )

			parent["add"]["enabled"] = True
			"""
		) )

		canceller = IECore.Canceller()

		with GraphGadgetTest.testActivePlugsAndNodesCancellationCondition:
			t = Gaffer.ParallelAlgo.callOnBackgroundThread(
				s["add"]["sum"], lambda : testThreadFunc( s["add"]["sum"], canceller, self )
			)
			GraphGadgetTest.testActivePlugsAndNodesCancellationCondition.wait()

		canceller.cancel()
		t.wait()

if __name__ == "__main__":
	unittest.main()
