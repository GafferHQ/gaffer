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

from __future__ import with_statement

import unittest
import weakref

import IECore

import Gaffer
import GafferUI
import GafferTest
import GafferUITest

class NestedPlugTestNode( Gaffer.Node ) :
		
	def __init__( self ) :
			
		Gaffer.Node.__init__( self )
	
IECore.registerRunTimeTyped( NestedPlugTestNode )
GafferUI.Nodule.registerNodule( NestedPlugTestNode.staticTypeId(), "c", GafferUI.CompoundNodule )

class NodeGraphTest( GafferUITest.TestCase ) :

	def testCreateWithExistingGraph( self ) :
	
		s = Gaffer.ScriptNode()
		
		s["add1"] = GafferTest.AddNode()
		s["add2"] = GafferTest.AddNode()
		
		s["add1"]["op1"].setInput( s["add2"]["sum"] )
		
		g = GafferUI.NodeGraph( s )
		
		self.failUnless( g.graphGadget().nodeGadget( s["add1"] ).node() is s["add1"] )
		self.failUnless( g.graphGadget().nodeGadget( s["add2"] ).node() is s["add2"] )
	
		self.failUnless( g.graphGadget().connectionGadget( s["add1"]["op1"] ).dstNodule().plug().isSame( s["add1"]["op1"] ) )
				
	def testGraphGadgetAccess( self ) :
	
		s = Gaffer.ScriptNode()
		ge = GafferUI.NodeGraph( s )
		
		g = ge.graphGadget()
		
		self.failUnless( isinstance( g, GafferUI.GraphGadget ) )
	
	def testRemovedNodesDontHaveGadgets( self ) :
	
		s = Gaffer.ScriptNode()
		g = GafferUI.GraphGadget( s )
		
		n = GafferTest.AddNode()
		s["add1"] = n
		
		self.failUnless( g.nodeGadget( n ) is not None )
		
		s.deleteNodes( filter = Gaffer.StandardSet( [ n ] ) )

		self.failUnless( g.nodeGadget( n ) is None )
	
	def testRemovedNodesDontHaveConnections( self ) :
	
		s = Gaffer.ScriptNode()
		
		n = GafferTest.AddNode()
		s["add1"] = n
		s["add2"] = GafferTest.AddNode()
		
		s["add1"]["op1"].setInput( s["add2"]["sum"] )
		
		g = GafferUI.NodeGraph( s )

		s.deleteNodes( filter = Gaffer.StandardSet( [ s["add1"] ] ) )
		
		self.failIf( g.graphGadget().connectionGadget( n["op1"] ) )

	def testCreateWithFilter( self ) :
	
		script = Gaffer.ScriptNode()
		
		script["add1"] = GafferTest.AddNode()
		script["add2"] = GafferTest.AddNode()
		
		nodeFilter = Gaffer.StandardSet( [ script["add2"] ] )
		
		g = GafferUI.GraphGadget( script, nodeFilter )
		
		self.failIf( g.nodeGadget( script["add1"] ) )
		self.failUnless( g.nodeGadget( script["add2"] ) )
	
	def testEditFilter( self ) :
		
		script = Gaffer.ScriptNode()
		
		script["add1"] = GafferTest.AddNode()
		script["add2"] = GafferTest.AddNode()

		nodeFilter = Gaffer.StandardSet( script.children() )
		
		g = GafferUI.GraphGadget( script, nodeFilter )
		
		self.failUnless( g.nodeGadget( script["add1"] ) )
		self.failUnless( g.nodeGadget( script["add2"] ) )
			
		nodeFilter.remove( script["add1"] )
			
		self.failIf( g.nodeGadget( script["add1"] ) )
		self.failUnless( g.nodeGadget( script["add2"] ) )
		
		nodeFilter.remove( script["add2"] )
		
		self.failIf( g.nodeGadget( script["add1"] ) )
		self.failIf( g.nodeGadget( script["add2"] ) )
		
		nodeFilter.add( script["add1"] )
		
		self.failUnless( g.nodeGadget( script["add1"] ) )
		self.failIf( g.nodeGadget( script["add2"] ) )

		nodeFilter.add( script["add2"] )
		
		self.failUnless( g.nodeGadget( script["add1"] ) )
		self.failUnless( g.nodeGadget( script["add2"] ) )
	
	def testUnhidingConnectedDstNodes( self ) :
	
		script = Gaffer.ScriptNode()
		
		script["add1"] = GafferTest.AddNode()
		script["add2"] = GafferTest.AddNode()
		
		script["add2"]["op1"].setInput( script["add1"]["sum"] )
		
		nodeFilter = Gaffer.StandardSet( [ script["add1"] ] )
		g = GafferUI.GraphGadget( script, nodeFilter )

		self.failUnless( g.nodeGadget( script["add1"] ) )
		self.failIf( g.nodeGadget( script["add2"] ) )
		self.failIf( g.connectionGadget( script["add2"]["op1"] ) )
		
		nodeFilter.add( script["add2"] )
		
		self.failUnless( g.nodeGadget( script["add1"] ) )
		self.failUnless( g.nodeGadget( script["add2"] ) )
		self.failUnless( g.connectionGadget( script["add2"]["op1"] ) )
	
	def testCreatingWithHiddenSrcNodes( self ) :
	
		script = Gaffer.ScriptNode()
		
		script["add1"] = GafferTest.AddNode()
		script["add2"] = GafferTest.AddNode()
		
		script["add2"]["op1"].setInput( script["add1"]["sum"] )
		
		nodeFilter = Gaffer.StandardSet( [ script["add2"] ] )
		
		g = GafferUI.GraphGadget( script, nodeFilter )

		self.failIf( g.nodeGadget( script["add1"] ) )
		self.failUnless( g.nodeGadget( script["add2"] ) )
				
		c = g.connectionGadget( script["add2"]["op1"] )
		self.failUnless( c )
		
		self.failUnless( c.dstNodule().plug().isSame( script["add2"]["op1"] ) )
		self.assertEqual( c.srcNodule(), None )
		
	def testHidingConnectedDstNodes( self ) :
	
		script = Gaffer.ScriptNode()
		
		script["add1"] = GafferTest.AddNode()
		script["add2"] = GafferTest.AddNode()
		
		script["add2"]["op1"].setInput( script["add1"]["sum"] )
		
		nodeFilter = Gaffer.StandardSet( script.children() )
		g = GafferUI.GraphGadget( script, nodeFilter )

		self.failUnless( g.nodeGadget( script["add1"] ) )
		self.failUnless( g.nodeGadget( script["add2"] ) )
		self.failUnless( g.connectionGadget( script["add2"]["op1"] ) )
		
		nodeFilter.remove( script["add2"] )
		
		self.failUnless( g.nodeGadget( script["add1"] ) )
		self.failIf( g.nodeGadget( script["add2"] ) )
		self.failIf( g.connectionGadget( script["add2"]["op1"] ) )
		
	def testHidingConnectedSrcNodes( self ) :
	
		script = Gaffer.ScriptNode()
		
		script["add1"] = GafferTest.AddNode()
		script["add2"] = GafferTest.AddNode()
		
		script["add2"]["op1"].setInput( script["add1"]["sum"] )
		
		nodeFilter = Gaffer.StandardSet( [ script["add1"], script["add2"] ] )
		
		g = GafferUI.GraphGadget( script, nodeFilter )

		self.failUnless( g.nodeGadget( script["add1"] ) )
		self.failUnless( g.nodeGadget( script["add2"] ) )
				
		c = g.connectionGadget( script["add2"]["op1"] )
		self.failUnless( c )
		
		self.failUnless( c.srcNodule().plug().isSame( script["add1"]["sum"] ) )
		self.failUnless( c.dstNodule().plug().isSame( script["add2"]["op1"] ) )
		
		nodeFilter.remove( script["add1"] )

		self.failIf( g.nodeGadget( script["add1"] ) )
	
		c = g.connectionGadget( script["add2"]["op1"] )
		self.failUnless( c )
		self.failUnless( c.srcNodule() is None )
		self.failUnless( c.dstNodule().plug().isSame( script["add2"]["op1"] ) )
	
	def testConnectingInvisibleDstNodes( self ) :
	
		script = Gaffer.ScriptNode()
		
		script["add1"] = GafferTest.AddNode()
		script["add2"] = GafferTest.AddNode()
		
		nodeFilter = Gaffer.StandardSet( [ script["add1"] ] )
		g = GafferUI.GraphGadget( script, nodeFilter )

		self.failUnless( g.nodeGadget( script["add1"] ) )
		self.failIf( g.nodeGadget( script["add2"] ) )		
				
		script["add2"]["op1"].setInput( script["add1"]["sum"] )
		
		self.failUnless( g.nodeGadget( script["add1"] ) )
		self.failIf( g.nodeGadget( script["add2"] ) )
		self.failIf( g.connectionGadget( script["add2"]["op1"] ) )
		
	def testConnectingHiddenDstNodes( self ) :
	
		script = Gaffer.ScriptNode()
		
		script["add1"] = GafferTest.AddNode()
		script["add2"] = GafferTest.AddNode()
		
		nodeFilter = Gaffer.StandardSet( script.children() )
		g = GafferUI.GraphGadget( script, nodeFilter )

		self.failUnless( g.nodeGadget( script["add1"] ) )
		self.failUnless( g.nodeGadget( script["add2"] ) )		
		
		nodeFilter.remove( script["add2"] )
		
		self.failUnless( g.nodeGadget( script["add1"] ) )
		self.failIf( g.nodeGadget( script["add2"] ) )		
				
		script["add2"]["op1"].setInput( script["add1"]["sum"] )
		
		self.failUnless( g.nodeGadget( script["add1"] ) )
		self.failIf( g.nodeGadget( script["add2"] ) )
		self.failIf( g.connectionGadget( script["add2"]["op1"] ) )	
		
	def testConnectingHiddenSrcNodes( self ) :
	
		script = Gaffer.ScriptNode()
		
		script["add1"] = GafferTest.AddNode()
		script["add2"] = GafferTest.AddNode()
		
		nodeFilter = Gaffer.StandardSet( [ script["add2"] ] )
		g = GafferUI.GraphGadget( script, nodeFilter )
	
		self.failIf( g.nodeGadget( script["add1"] ) )
		self.failUnless( g.nodeGadget( script["add2"] ) )
		
		script["add2"]["op1"].setInput( script["add1"]["sum"] )
		
		self.failIf( g.nodeGadget( script["add1"] ) )
		self.failUnless( g.nodeGadget( script["add2"] ) )
		
		c = g.connectionGadget( script["add2"]["op1"] )
		self.failUnless( c )
		self.failUnless( c.srcNodule() is None )
		
	def testConnectingHiddenSrcNodesAndReshowing( self ) :
	
		script = Gaffer.ScriptNode()
		
		script["add1"] = GafferTest.AddNode()
		script["add2"] = GafferTest.AddNode()
		
		nodeFilter = Gaffer.StandardSet( [ script["add2"] ] )
		g = GafferUI.GraphGadget( script, nodeFilter )
	
		self.failIf( g.nodeGadget( script["add1"] ) )
		self.failUnless( g.nodeGadget( script["add2"] ) )
		
		script["add2"]["op1"].setInput( script["add1"]["sum"] )
		
		self.failIf( g.nodeGadget( script["add1"] ) )
		self.failUnless( g.nodeGadget( script["add2"] ) )
		
		c = g.connectionGadget( script["add2"]["op1"] )
		self.failUnless( c )
		self.failUnless( c.srcNodule() is None )
	
		nodeFilter.add( script["add1"] )
		
		self.failUnless( g.nodeGadget( script["add1"] ) )
		self.failUnless( g.nodeGadget( script["add2"] ) )
	
		c = g.connectionGadget( script["add2"]["op1"] )
		self.failUnless( c )
		self.failUnless( c.srcNodule().plug().isSame( script["add1"]["sum"] ) )
		
	def testChangingFilter( self ) :
	
		script = Gaffer.ScriptNode()
		
		script["add1"] = GafferTest.AddNode()
		script["add2"] = GafferTest.AddNode()
		
		nodeFilter = Gaffer.StandardSet( [ script["add1"] ] )
		g = GafferUI.GraphGadget( script, nodeFilter )

		self.failUnless( g.nodeGadget( script["add1"] ) )
		self.failIf( g.nodeGadget( script["add2"] ) )
		
		nodeFilter2 = Gaffer.StandardSet( [ script["add2"] ] )
		g.setFilter( nodeFilter2 )
		
		self.failIf( g.nodeGadget( script["add1"] ) )
		self.failUnless( g.nodeGadget( script["add2"] ) )
		
	def testChangingFilterAndEditingOriginal( self ) :
	
		script = Gaffer.ScriptNode()
		
		script["add1"] = GafferTest.AddNode()
		script["add2"] = GafferTest.AddNode()
		
		nodeFilter = Gaffer.StandardSet()
		g = GafferUI.GraphGadget( script, nodeFilter )

		self.failIf( g.nodeGadget( script["add1"] ) )
		self.failIf( g.nodeGadget( script["add2"] ) )
		
		nodeFilter2 = Gaffer.StandardSet( [ script["add2"] ] )
		g.setFilter( nodeFilter2 )
		
		self.failIf( g.nodeGadget( script["add1"] ) )
		self.failUnless( g.nodeGadget( script["add2"] ) )	
		
		nodeFilter.add( script["add1"] )
		
		self.failIf( g.nodeGadget( script["add1"] ) )
		self.failUnless( g.nodeGadget( script["add2"] ) )
	
	def testConnectionsForNestedPlugs( self ) :
	
		script = Gaffer.ScriptNode()
		
		script["n"] = NestedPlugTestNode()
		script["n"]["c"] = Gaffer.CompoundPlug()
		script["n"]["c"]["i"] = Gaffer.IntPlug()
		
		script["n2"] = NestedPlugTestNode()
		script["n2"]["c"] = Gaffer.CompoundPlug(  direction = Gaffer.Plug.Direction.Out )
		script["n2"]["c"]["o"] = Gaffer.IntPlug( direction = Gaffer.Plug.Direction.Out )
		
		script["n"]["c"]["i"].setInput( script["n2"]["c"]["o"] )
		
		s = Gaffer.StandardSet( script.children() )
		g = GafferUI.GraphGadget( script, s )
				
		c = g.connectionGadget( script["n"]["c"]["i"] )
		self.failUnless( c )
		self.failUnless( c.srcNodule().plug().isSame( script["n2"]["c"]["o"] ) )
		self.failUnless( c.dstNodule().plug().isSame( script["n"]["c"]["i"] ) )
		
		s.remove( script["n2"] )
		
		self.failUnless( g.nodeGadget( script["n2"] ) is None )
		
		c = g.connectionGadget( script["n"]["c"]["i"] )
		self.failUnless( c )
		self.failUnless( c.srcNodule() is None )
		self.failUnless( c.dstNodule().plug().isSame( script["n"]["c"]["i"] ) )
		
		s.add( script["n2"] )
		
		self.failUnless( g.nodeGadget( script["n2"] ) )
		
		c = g.connectionGadget( script["n"]["c"]["i"] )
		self.failUnless( c )
		self.failUnless( c.srcNodule().plug().isSame( script["n2"]["c"]["o"] ) )
		self.failUnless( c.dstNodule().plug().isSame( script["n"]["c"]["i"] ) )
		
		s.remove( script["n"] )
		
		self.failUnless( g.nodeGadget( script["n"] ) is None )
		
		self.failUnless( g.connectionGadget( script["n"]["c"]["i"] ) is None )

		s.add( script["n"] )

		self.failUnless( g.nodeGadget( script["n"] ) )
		
		c = g.connectionGadget( script["n"]["c"]["i"] )
		self.failUnless( c )
		self.failUnless( c.srcNodule().plug().isSame( script["n2"]["c"]["o"] ) )
		self.failUnless( c.dstNodule().plug().isSame( script["n"]["c"]["i"] ) )

	def testRemovePlugWithInputConnection( self ) :
	
		script = Gaffer.ScriptNode()
		
		script["n1"] = Gaffer.Node()
		script["n2"] = Gaffer.Node()
		
		script["n1"]["o"] = Gaffer.IntPlug( direction = Gaffer.Plug.Direction.Out )
		script["n2"]["i"] = Gaffer.IntPlug()
		
		script["n2"]["i"].setInput( script["n1"]["o"] )
		
		g = GafferUI.GraphGadget( script )
		
		self.failUnless( g.connectionGadget( script["n2"]["i"] ) is not None )
		
		with Gaffer.UndoContext( script ) :
			
			removedPlug = script["n2"]["i"]
			del script["n2"]["i"]
			
		self.failUnless( g.connectionGadget( removedPlug ) is None )

		script.undo()
		
		self.failUnless( g.connectionGadget( script["n2"]["i"] ) is not None )		
	
	def testRemovePlugWithOutputConnection( self ) :
	
		script = Gaffer.ScriptNode()
		
		script["n1"] = Gaffer.Node()
		script["n2"] = Gaffer.Node()
		
		script["n1"]["o"] = Gaffer.IntPlug( direction = Gaffer.Plug.Direction.Out )
		script["n2"]["i"] = Gaffer.IntPlug()
		
		script["n2"]["i"].setInput( script["n1"]["o"] )
		
		g = GafferUI.GraphGadget( script )
		
		self.failUnless( g.connectionGadget( script["n2"]["i"] ) is not None )
		
		with Gaffer.UndoContext( script ) :
		
			del script["n1"]["o"]
			
		self.failUnless( g.connectionGadget( script["n2"]["i"] ) is None )

		script.undo()
		
		self.failUnless( g.connectionGadget( script["n2"]["i"] ) is not None )		
	
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
	
			gb = IECore.Box3f()
			gb.extendBy( g.nodeGadget( script["n1"] ).bound() )
			gb.extendBy( g.nodeGadget( script["n2"] ).bound() )
			gb.min -= IECore.V3f( 10 )
			gb.max += IECore.V3f( 10 )
	
			b = c.bound()
			self.failIf( b.isEmpty() )
			
			self.failUnless( gb.contains( b ) )
	
	def testNoFilter( self ) :
	
		s = Gaffer.ScriptNode()
		s["n1"] = Gaffer.Node()
		
		g = GafferUI.GraphGadget( s )
		
		self.assertTrue( g.getRoot() is s )
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
		def f( gg ) :
		
			self.failUnless( gg.isSame( g ) )
			roots.append( gg.getRoot() )
		
		g = GafferUI.GraphGadget( s )
		c = g.rootChangedSignal().connect( f )
		
		self.assertEqual( len( roots ), 0 )
		
		g.setRoot( s["b"] )
		self.assertEqual( len( roots ), 1 )
		self.assertTrue( roots[0].isSame( s["b"] ) )
		
		g.setRoot( s["b"] )
		self.assertEqual( len( roots ), 1 )
		self.assertTrue( roots[0].isSame( s["b"] ) )
		
		g.setRoot( s )
		self.assertEqual( len( roots ), 2 )
		self.assertTrue( roots[1].isSame( s ) )
	
	def testLifetime( self ) :
	
		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()
		
		e = GafferUI.NodeGraph( s )
		
		we = weakref.ref( e )
		del e
		
		self.assertEqual( we(), None )
			
	def testSetNodePosition( self ) :
	
		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		
		g = GafferUI.GraphGadget( s )
		
		g.setNodePosition( s["n"], IECore.V2f( -100, 2000 ) )
		self.assertEqual( g.getNodePosition( s["n"] ), IECore.V2f( -100, 2000 ) )

	def testTitle( self ) :
	
		s = Gaffer.ScriptNode()
		
		g = GafferUI.NodeGraph( s )
		
		self.assertEqual( g.getTitle(), "Node Graph" )
		
		g.setTitle( "This is a test!" )
		
		self.assertEqual( g.getTitle(), "This is a test!" )
		
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
		
if __name__ == "__main__":
	unittest.main()
