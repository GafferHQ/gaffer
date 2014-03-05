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

from __future__ import with_statement

import unittest
import weakref

import IECore

import Gaffer
import GafferUI
import GafferTest
import GafferUITest

class LayoutNode( Gaffer.Node ) :

	def __init__( self, name = "LayoutNode" ) :
	
		Gaffer.Node.__init__( self, name )
		
		self["top0"] = Gaffer.IntPlug()
		self["top1"] = Gaffer.IntPlug()
		self["top2"] = Gaffer.IntPlug()
		
		self["left0"] = Gaffer.IntPlug()
		self["left1"] = Gaffer.IntPlug()
		self["left2"] = Gaffer.IntPlug()
		
		self["bottom0"] = Gaffer.IntPlug( direction = Gaffer.Plug.Direction.Out )
		self["bottom1"] = Gaffer.IntPlug( direction = Gaffer.Plug.Direction.Out )
		self["bottom2"] = Gaffer.IntPlug( direction = Gaffer.Plug.Direction.Out )

		self["right0"] = Gaffer.IntPlug( direction = Gaffer.Plug.Direction.Out )
		self["right1"] = Gaffer.IntPlug( direction = Gaffer.Plug.Direction.Out )
		self["right2"] = Gaffer.IntPlug( direction = Gaffer.Plug.Direction.Out )
		
IECore.registerRunTimeTyped( LayoutNode )

Gaffer.Metadata.registerPlugValue( LayoutNode, "left*", "nodeGadget:nodulePosition", "left" )
Gaffer.Metadata.registerPlugValue( LayoutNode, "right*", "nodeGadget:nodulePosition", "right" )
Gaffer.Metadata.registerPlugValue( LayoutNode, "top*", "nodeGadget:nodulePosition", "top" )
Gaffer.Metadata.registerPlugValue( LayoutNode, "bottom*", "nodeGadget:nodulePosition", "bottom" )

class StandardGraphLayoutTest( GafferUITest.TestCase ) :

	def setUp( self ) :
	
		GafferUITest.TestCase.setUp( self )
		
		GafferUI.Nodule.registerNodule( GafferTest.AddNode.staticTypeId(), "enabled", lambda plug : None )

	def testConnectNode( self ) :
	
		s = Gaffer.ScriptNode()
		
		s["add1"] = GafferTest.AddNode()
		s["add2"] = GafferTest.AddNode()
		
		ng = GafferUI.NodeGraph( s )
		g = ng.graphGadget()
		
		# check we can connect to a top level plug
		g.getLayout().connectNode( g, s["add2"], Gaffer.StandardSet( [ s["add1"] ] ) )
		self.assertTrue( s["add2"]["op1"].getInput().isSame( s["add1"]["sum"] ) )
	
		# check we can connect to a nested plug, but only provided it is represented
		# in the node graph by a nodule for that exact plug.
	
		s["compound"] = GafferTest.CompoundPlugNode()
		g.getLayout().connectNode( g, s["compound"], Gaffer.StandardSet( [ s["add2"] ] ) )
		self.assertEqual( s["compound"]["p"]["f"].getInput(), None )
		
		GafferUI.Nodule.registerNodule( GafferTest.CompoundPlugNode.staticTypeId(), "p", GafferUI.CompoundNodule )
		
		s["compound2"] = GafferTest.CompoundPlugNode()
		g.getLayout().connectNode( g, s["compound2"], Gaffer.StandardSet( [ s["add2"] ] ) )
		self.assertTrue( s["compound2"]["p"]["f"].getInput().isSame( s["add2"]["sum"] ) )
		
		# check we can connect from a nested plug, but only provided it is represented
		# in the node graph by a nodule for that exact plug.
		
		s["add3"] = GafferTest.AddNode()
		
		g.getLayout().connectNode( g, s["add3"], Gaffer.StandardSet( [ s["compound2"] ] ) )
		self.assertEqual( s["add3"]["op1"].getInput(), None )
		
		GafferUI.Nodule.registerNodule( GafferTest.CompoundPlugNode.staticTypeId(), "o", GafferUI.CompoundNodule )
		
		s["compound3"] = GafferTest.CompoundPlugNode()
		
		g.getLayout().connectNode( g, s["add3"], Gaffer.StandardSet( [ s["compound3"] ] ) )
		self.assertTrue( s["add3"]["op1"].getInput().isSame( s["compound3"]["o"]["f"] ) )
	
	def testConnectNodes( self ) :
	
		s = Gaffer.ScriptNode()

		s["add1"] = GafferTest.AddNode()
		s["add2"] = GafferTest.AddNode()
		s["add3"] = GafferTest.AddNode()
		
		s["add3"]["op1"].setInput( s["add2"]["sum"] )
		
		g = GafferUI.GraphGadget( s )
		g.getLayout().connectNodes( g, Gaffer.StandardSet( [ s["add3"], s["add2"] ] ), Gaffer.StandardSet( [ s["add1"] ] ) )
		
		self.assertTrue( s["add2"]["op1"].getInput().isSame( s["add1"]["sum"] ) )
	
	def testConnectNodeInStream( self ) :
	
		s = Gaffer.ScriptNode()
		
		s["add1"] = GafferTest.AddNode()
		s["add2"] = GafferTest.AddNode()
		s["add3"] = GafferTest.AddNode()
		
		s["add2"]["op1"].setInput( s["add1"]["sum"] )
		
		g = GafferUI.GraphGadget( s )
		g.getLayout().connectNode( g, s["add3"], Gaffer.StandardSet( [ s["add1"] ] ) )
		
		self.assertTrue( s["add3"]["op1"].getInput().isSame( s["add1"]["sum"] ) )
		self.assertTrue( s["add2"]["op1"].getInput().isSame( s["add3"]["sum"] ) )
	
	def testConnectNodeInStreamWithMultipleOutputs( self ) :
	
		s = Gaffer.ScriptNode()
		
		s["add1"] = GafferTest.AddNode()
		s["add2"] = GafferTest.AddNode()
		s["add3"] = GafferTest.AddNode()
		s["add4"] = GafferTest.AddNode()
		
		s["add2"]["op1"].setInput( s["add1"]["sum"] )
		s["add3"]["op1"].setInput( s["add1"]["sum"] )
		
		g = GafferUI.GraphGadget( s )
		g.getLayout().connectNode( g, s["add4"], Gaffer.StandardSet( [ s["add1"] ] ) )
		
		self.assertTrue( s["add2"]["op1"].getInput().isSame( s["add4"]["sum"] ) )
		self.assertTrue( s["add3"]["op1"].getInput().isSame( s["add4"]["sum"] ) )
	
	def testConnectNodeInStreamWithInvisibleOutputs( self ) :
	
		s = Gaffer.ScriptNode()
		
		s["add1"] = GafferTest.AddNode()
		s["add2"] = GafferTest.AddNode()
		s["add4"] = GafferTest.AddNode()
		
		s["add2"]["op1"].setInput( s["add1"]["sum"] )
		
		add3 = GafferTest.AddNode()
		add3["op1"].setInput( s["add1"]["sum"] )
		
		g = GafferUI.GraphGadget( s )
		g.getLayout().connectNode( g, s["add4"], Gaffer.StandardSet( [ s["add1"] ] ) )
		
		self.assertTrue( s["add2"]["op1"].getInput().isSame( s["add4"]["sum"] ) )
		self.assertTrue( add3["op1"].getInput().isSame( s["add1"]["sum"] ) )
		
	def testConnectNodeToMultipleInputsDoesntInsertInStream( self ) :
	
		s = Gaffer.ScriptNode()
		
		s["add1"] = GafferTest.AddNode()
		s["add2"] = GafferTest.AddNode()
		s["add3"] = GafferTest.AddNode()
		s["add4"] = GafferTest.AddNode()
		
		s["add3"]["op1"].setInput( s["add1"]["sum"] )
		s["add3"]["op2"].setInput( s["add2"]["sum"] )
		
		g = GafferUI.GraphGadget( s )
		g.getLayout().connectNode( g, s["add4"], Gaffer.StandardSet( [ s["add1"], s["add2"] ] ) )
		
		self.assertTrue( s["add4"]["op1"].getInput().isSame( s["add1"]["sum"] ) )
		self.assertTrue( s["add4"]["op2"].getInput().isSame( s["add2"]["sum"] ) )

		self.assertEqual( len( s["add4"]["sum"].outputs() ), 0 )

	def testLayoutDirection( self ) :
	
		s = Gaffer.ScriptNode()
		s["top"] = LayoutNode()
		s["bottom"] = LayoutNode()
		s["bottom"]["top0"].setInput( s["top"]["bottom0"] )
		
		g = GafferUI.GraphGadget( s )
		g.getLayout().layoutNodes( g )
		
		self.assertTrue( g.getNodePosition( s["top"] ).y > g.getNodePosition( s["bottom"] ).y )
	
		s["left"] = LayoutNode()
		s["right"] = LayoutNode()
		s["right"]["left0"].setInput( s["left"]["right0"] )

		g.getLayout().layoutNodes( g )

		self.assertTrue( g.getNodePosition( s["right"] ).x > g.getNodePosition( s["left"] ).x )

	def testInputConnectionsDontCross( self ) :
	
		s = Gaffer.ScriptNode()
		
		s["top0"] = LayoutNode()
		s["top1"] = LayoutNode()
		s["top2"] = LayoutNode()
		s["bottom"] = LayoutNode()
		s["bottom"]["top0"].setInput( s["top0"]["bottom0"] )
		s["bottom"]["top1"].setInput( s["top1"]["bottom0"] )
		s["bottom"]["top2"].setInput( s["top2"]["bottom0"] )

		g = GafferUI.GraphGadget( s )
		g.getLayout().layoutNodes( g )
		
		self.assertTrue( g.getNodePosition( s["top0"] ).x < g.getNodePosition( s["top1"] ).x )
		self.assertTrue( g.getNodePosition( s["top1"] ).x < g.getNodePosition( s["top2"] ).x )

		self.assertNoOverlaps( g )
		
	def testHorizontalInputConnectionsDontCross( self ) :

		s = Gaffer.ScriptNode()

		s["left0"] = LayoutNode()
		s["left1"] = LayoutNode()
		s["left2"] = LayoutNode()
		s["right"] = LayoutNode()
		s["right"]["left0"].setInput( s["left0"]["right0"] )
		s["right"]["left1"].setInput( s["left1"]["right0"] )
		s["right"]["left2"].setInput( s["left2"]["right0"] )

		g = GafferUI.GraphGadget( s )
		g.getLayout().layoutNodes( g )

		self.assertTrue( g.getNodePosition( s["left0"] ).y > g.getNodePosition( s["left1"] ).y )
		self.assertTrue( g.getNodePosition( s["left1"] ).y > g.getNodePosition( s["left2"] ).y )
	
		self.assertNoOverlaps( g )
	
	def testPinning( self ) :
	
		s = Gaffer.ScriptNode()
		
		s["bottom"] = LayoutNode()
		s["top"] = LayoutNode()
		s["bottom"]["top0"].setInput( s["top"]["bottom0"] )
		
		g = GafferUI.GraphGadget( s )
		g.setNodePosition( s["bottom"], IECore.V2f( 50, 60 ) )
		
		g.getLayout().layoutNodes( g, Gaffer.StandardSet( [ s["top"] ] ) )

		self.assertEqual( g.getNodePosition( s["bottom"] ), IECore.V2f( 50, 60 ) )
		self.assertAlmostEqual( g.getNodePosition( s["top"] ).x, g.getNodePosition( s["bottom"] ).x, delta = 0.001 )
		self.assertTrue( g.getNodePosition( s["top"] ).y > g.getNodePosition( s["bottom"] ).y )

	def testPinningInNegativeY( self ) :
	
		s = Gaffer.ScriptNode()
		
		s["bottom"] = LayoutNode()
		s["top"] = LayoutNode()
		s["bottom"]["top0"].setInput( s["top"]["bottom0"] )
		
		g = GafferUI.GraphGadget( s )
		g.setNodePosition( s["bottom"], IECore.V2f( 50, -60 ) )
		
		g.getLayout().layoutNodes( g, Gaffer.StandardSet( [ s["top"] ] ) )

		self.assertEqual( g.getNodePosition( s["bottom"] ), IECore.V2f( 50, -60 ) )
		self.assertAlmostEqual( g.getNodePosition( s["top"] ).x, g.getNodePosition( s["bottom"] ).x, delta=0.001 )
		self.assertTrue( g.getNodePosition( s["top"] ).y > g.getNodePosition( s["bottom"] ).y )

		self.assertNoOverlaps( g )

	def testPinningOfSourceNode( self ) :
	
		s = Gaffer.ScriptNode()
		
		s["bottom"] = LayoutNode()
		s["top"] = LayoutNode()
		s["bottom"]["top0"].setInput( s["top"]["bottom0"] )
		
		g = GafferUI.GraphGadget( s )
		g.setNodePosition( s["top"], IECore.V2f( 50, 60 ) )
		
		g.getLayout().layoutNodes( g, Gaffer.StandardSet( [ s["bottom"] ] ) )

		self.assertEqual( g.getNodePosition( s["top"] ), IECore.V2f( 50, 60 ) )
		self.assertAlmostEqual( g.getNodePosition( s["top"] ).x, g.getNodePosition( s["bottom"] ).x, delta = 0.001 )
		self.assertTrue( g.getNodePosition( s["top"] ).y > g.getNodePosition( s["bottom"] ).y )

		self.assertNoOverlaps( g )
	
	def testUnconnectedNodes( self ) :
	
		s = Gaffer.ScriptNode()
		
		s["one"] = LayoutNode()
		s["two"] = LayoutNode()
		
		g = GafferUI.GraphGadget( s )
		g.getLayout().layoutNodes( g )
		
		self.assertNoOverlaps( g )
	
	def testSeparateNetworks( self ) :
	
		s = Gaffer.ScriptNode()
		
		s["top1"] = LayoutNode()
		s["bottom1"] = LayoutNode()
		s["bottom1"]["top0"].setInput( s["top1"]["bottom0"] )
		
		s["top2"] = LayoutNode()
		s["bottom2"] = LayoutNode()
		s["bottom2"]["top0"].setInput( s["top2"]["bottom0"] )
		
		g = GafferUI.GraphGadget( s )
		g.getLayout().layoutNodes( g )

		self.assertNoOverlaps( g )
	
	def testSideTangentAlignment( self ) :
		
		s = Gaffer.ScriptNode()
		
		s["top"] = LayoutNode()
		s["middle"] = LayoutNode()
		s["bottom"] = LayoutNode()
		s["left"] = LayoutNode()
		
		s["middle"]["top0"].setInput( s["top"]["bottom0"] )
		s["bottom"]["top0"].setInput( s["middle"]["bottom0"] )
		s["middle"]["left1"].setInput( s["left"]["right1"] )
		
		g = GafferUI.GraphGadget( s )
		g.getLayout().layoutNodes( g )

		self.assertNoOverlaps( g )

		self.assertTrue( g.getNodePosition( s["left"] ).x < g.getNodePosition( s["middle"] ).x )
		self.assertAlmostEqual( g.getNodePosition( s["left"] ).y, g.getNodePosition( s["middle"] ).y, 3 )
	
	def testPositionNode( self ) :
	
		s = Gaffer.ScriptNode()
		
		s["topLeft"] = LayoutNode()
		s["topRight"] = LayoutNode()
		
		g = GafferUI.GraphGadget( s )
		g.setNodePosition( s["topLeft"], IECore.V2f( 10, 0 ) )
		g.setNodePosition( s["topRight"], IECore.V2f( 40, 0 ) )
		
		s["new"] = LayoutNode()
		s["new"]["top0"].setInput( s["topLeft"]["bottom1"] )
		s["new"]["top2"].setInput( s["topRight"]["bottom1"] )
		
		g.getLayout().positionNode( g, s["new"] )
		
		self.assertEqual( g.getNodePosition( s["topLeft"] ), IECore.V2f( 10, 0 ) )
		self.assertEqual( g.getNodePosition( s["topRight"] ), IECore.V2f( 40, 0 ) )
		
		self.assertTrue( g.getNodePosition( s["new"] ).x > g.getNodePosition( s["topLeft"] ).x )
		self.assertTrue( g.getNodePosition( s["new"] ).x < g.getNodePosition( s["topRight"] ).x )
		
		self.assertTrue( g.getNodePosition( s["new"] ).y < g.getNodePosition( s["topLeft"] ).x )
	
	def testPositionNodeFallback( self ) :
	
		s = Gaffer.ScriptNode()
		
		s["node1"] = LayoutNode()
		s["node2"] = LayoutNode()
		
		g = GafferUI.GraphGadget( s )
		g.setNodePosition( s["node1"], IECore.V2f( 10, 0 ) )
		
		g.getLayout().positionNode( g, s["node2"], IECore.V2f( -10, -20 ) )
		
		self.assertEqual( g.getNodePosition( s["node1"] ), IECore.V2f( 10, 0 ) )
		self.assertEqual( g.getNodePosition( s["node2"] ), IECore.V2f( -10, -20 ) )
	
	def testPositionNodes( self ) :
	
		s = Gaffer.ScriptNode()
		
		#  1 -> 2
		#       |
		#       v
		#       3
		
		s["node1"] = LayoutNode()
		s["node2"] = LayoutNode()
		s["node3"] = LayoutNode()
		
		s["node2"]["left1"].setInput( s["node1"]["right1"] )
		s["node3"]["top1"].setInput( s["node2"]["bottom1"] )
		
		g = GafferUI.GraphGadget( s )
		
		g.setNodePosition( s["node1"], IECore.V2f( 100, 1000 ) )
		g.setNodePosition( s["node2"], IECore.V2f( -10, 500 ) )
		g.setNodePosition( s["node3"], IECore.V2f( -5, 490 ) )
		
		o1 = g.getNodePosition( s["node3"] ) - g.getNodePosition( s["node2"] )
		
		g.getLayout().positionNodes( g, Gaffer.StandardSet( [ s["node2"], s["node3"] ] ) )
		
		o2 = g.getNodePosition( s["node3"] ) - g.getNodePosition( s["node2"] )
		self.assertEqual( o1, o2 )
		
		self.assertEqual( g.getNodePosition( s["node1"] ), IECore.V2f( 100, 1000 ) )
		self.assertTrue( g.getNodePosition( s["node2"] ).x > g.getNodePosition( s["node1"] ).x )
		self.assertAlmostEqual( g.getNodePosition( s["node1"] ).y, g.getNodePosition( s["node2"] ).y, 2 )

	def testPositionNodesFallback( self ) :
	
		s = Gaffer.ScriptNode()
		
		s["node1"] = LayoutNode()
		s["node2"] = LayoutNode()
		
		s["node2"]["left0"].setInput( s["node1"]["right0"] )
		
		g = GafferUI.GraphGadget( s )
		
		g.setNodePosition( s["node1"], IECore.V2f( 10, 12 ) )
		g.setNodePosition( s["node2"], IECore.V2f( 50, 14 ) )
		
		o1 = g.getNodePosition( s["node2"] ) - g.getNodePosition( s["node1"] )
		
		g.getLayout().positionNodes( g, Gaffer.StandardSet( [ s["node1"], s["node2"] ] ), IECore.V2f( -100, -20 ) )
		
		o2 = g.getNodePosition( s["node2"] ) - g.getNodePosition( s["node1"] )
		self.assertEqual( o1, o2 )
		
		self.assertEqual(
			( g.getNodePosition( s["node1"] ) + g.getNodePosition( s["node2"] ) ) / 2.0,
			IECore.V2f( -100, -20 )
		)
	
	def testImpossibleSiblingOrdering( self ) :
	
		s = Gaffer.ScriptNode()
		
		s["s1"] = LayoutNode()
		s["s2"] = LayoutNode()
		s["s3"] = LayoutNode()
		
		s["o1"] = LayoutNode()
		s["o2"] = LayoutNode()
		
		s["o1"]["top0"].setInput( s["s1"]["bottom1"] )
		s["o1"]["top1"].setInput( s["s2"]["bottom1"] )
		s["o1"]["top2"].setInput( s["s3"]["bottom1"] )
		
		s["o2"]["top0"].setInput( s["s3"]["bottom1"] )
		s["o2"]["top1"].setInput( s["s2"]["bottom1"] )
		s["o2"]["top2"].setInput( s["s1"]["bottom1"] )
		
		g = GafferUI.GraphGadget( s )
		g.getLayout().layoutNodes( g )
		
		self.assertNoOverlaps( g )
		
		self.assertAlmostEqual( g.getNodePosition( s["s1"] ).y, g.getNodePosition( s["s2"] ).y, delta = 0.001 )
		self.assertAlmostEqual( g.getNodePosition( s["s2"] ).y, g.getNodePosition( s["s3"] ).y, delta = 0.001 )

		self.assertAlmostEqual( g.getNodePosition( s["o1"] ).y, g.getNodePosition( s["o2"] ).y, delta = 0.001 )
		self.assertTrue( g.getNodePosition( s["o1"] ).y < g.getNodePosition( s["s1"] ).y )

	def testImpossibleVerticalSiblingOrdering( self ) :
	
		s = Gaffer.ScriptNode()
		
		s["s1"] = LayoutNode()
		s["s2"] = LayoutNode()
		s["s3"] = LayoutNode()
		
		s["o1"] = LayoutNode()
		s["o2"] = LayoutNode()
		
		s["o1"]["left0"].setInput( s["s1"]["right1"] )
		s["o1"]["left1"].setInput( s["s2"]["right1"] )
		s["o1"]["left2"].setInput( s["s3"]["right1"] )
		
		s["o2"]["left0"].setInput( s["s3"]["right1"] )
		s["o2"]["left1"].setInput( s["s2"]["right1"] )
		s["o2"]["left2"].setInput( s["s1"]["right1"] )
		
		g = GafferUI.GraphGadget( s )
		g.getLayout().layoutNodes( g )
		
		self.assertNoOverlaps( g )
		
		self.assertAlmostEqual( g.getNodePosition( s["s1"] ).x, g.getNodePosition( s["s2"] ).x, delta = 0.001 )
		self.assertAlmostEqual( g.getNodePosition( s["s2"] ).x, g.getNodePosition( s["s3"] ).x, delta = 0.001 )

		self.assertAlmostEqual( g.getNodePosition( s["o1"] ).x, g.getNodePosition( s["o2"] ).x, delta = 0.001 )
		self.assertTrue( g.getNodePosition( s["o1"] ).x > g.getNodePosition( s["s1"] ).x )
	
	def testExactCollisions( self ) :
	
		s = Gaffer.ScriptNode()
		
		s["t"] = LayoutNode()
		s["b"] = LayoutNode()
		s["bb"] = LayoutNode()
		s["bbb"] = LayoutNode()
		
		s["b"]["top1"].setInput( s["t"]["bottom1"] )
		s["bb"]["top1"].setInput( s["t"]["bottom1"] )
		s["bbb"]["top1"].setInput( s["t"]["bottom1"] )
		
		g = GafferUI.GraphGadget( s )
		g.getLayout().layoutNodes( g )
		
		self.assertNoOverlaps( g )
	
	def testDiagonalConnectionAlignment( self ) :
	
		#    s
		#    |
		#    |\_t1
		#    |\_t2
		#     \_t3
		#
		# t1, t2 and t3 should be aligned perfectly in x
		
		s = Gaffer.ScriptNode()

		s["s"] = LayoutNode()
		s["t1"] = LayoutNode()
		s["t2"] = LayoutNode()
		s["t3"] = LayoutNode()

		s["t1"]["left1"].setInput( s["s"]["bottom1"] )
		s["t2"]["left1"].setInput( s["s"]["bottom1"] )
		s["t3"]["left1"].setInput( s["s"]["bottom1"] )
		
		g = GafferUI.GraphGadget( s )
		g.getLayout().layoutNodes( g )
		
		self.assertNoOverlaps( g )
		
		self.assertAlmostEqual( g.getNodePosition( s["t1"] ).x, g.getNodePosition( s["t2"] ).x, delta = 0.01 )
		self.assertAlmostEqual( g.getNodePosition( s["t1"] ).x, g.getNodePosition( s["t3"] ).x, delta = 0.01 )
	
	def testConnectionScale( self ) :
	
		s = Gaffer.ScriptNode()
		
		s["i"] = LayoutNode()
		s["o"] = LayoutNode()
		
		s["o"]["top1"].setInput( s["i"]["bottom1"] )
		
		g = GafferUI.GraphGadget( s )
		l = g.getLayout()
		
		self.assertEqual( l.getConnectionScale(), 1 )
		
		l.layoutNodes( g )
		length = ( g.getNodePosition( s["i"] ) - g.getNodePosition( s["o"] ) ).length()
		
		l.setConnectionScale( 2 )
		self.assertEqual( l.getConnectionScale(), 2 )
		
		l.layoutNodes( g )
		newLength = ( g.getNodePosition( s["i"] ) - g.getNodePosition( s["o"] ) ).length()
		
		self.assertTrue( newLength > length )

	def testSeparationScale( self ) :
	
		s = Gaffer.ScriptNode()
		
		s["t1"] = LayoutNode()
		s["t2"] = LayoutNode()
		s["b"] = LayoutNode()
		
		s["b"]["top0"].setInput( s["t1"]["bottom1"] )
		s["b"]["top1"].setInput( s["t2"]["bottom1"] )
		
		g = GafferUI.GraphGadget( s )
		l = g.getLayout()
		
		self.assertEqual( l.getNodeSeparationScale(), 1 )
		
		l.layoutNodes( g )
		length = ( g.getNodePosition( s["t1"] ) - g.getNodePosition( s["t2"] ) ).length()
		
		l.setNodeSeparationScale( 2 )
		self.assertEqual( l.getNodeSeparationScale(), 2 )
		
		l.layoutNodes( g )
		newLength = ( g.getNodePosition( s["t1"] ) - g.getNodePosition( s["t2"] ) ).length()
		
		self.assertTrue( newLength > length )
	
	def testInputAndOutputSeparationEquivalence( self ) :
	
		s = Gaffer.ScriptNode()
		
		s["t1"] = LayoutNode()
		s["t2"] = LayoutNode()
		s["m"] = LayoutNode()
		s["b1"] = LayoutNode()
		s["b2"] = LayoutNode()
		
		s["m"]["top0"].setInput( s["t1"]["bottom1"] )
		s["m"]["top1"].setInput( s["t2"]["bottom1"] )
		
		s["b1"]["top1"].setInput( s["m"]["bottom1"] )
		s["b2"]["top1"].setInput( s["m"]["bottom1"] )
		
		g = GafferUI.GraphGadget( s )
		g.getLayout().layoutNodes( g )
		
		self.assertAlmostEqual(
			( g.getNodePosition( s["t1"]  ) - g.getNodePosition( s["t2"] ) ).length(),
			( g.getNodePosition( s["b1"]  ) - g.getNodePosition( s["b2"] ) ).length(),
			delta = 0.001
		)
		
	def assertNoOverlaps( self, graphGadget ) :
	
		nodes = []
		bounds = IECore.Box2fVectorData()
		for node in graphGadget.getRoot().children( Gaffer.Node.staticTypeId() ) :
		
			nodeGadget = graphGadget.nodeGadget( node )
			if nodeGadget is None :
				continue
			
			nodes.append( node )
			
			bound = nodeGadget.transformedBound( graphGadget )
			bounds.append(
				IECore.Box2f(
					IECore.V2f( bound.min.x, bound.min.y ),
					IECore.V2f( bound.max.x, bound.max.y ),
				)
			)

		tree = IECore.Box2fTree( bounds )
		for index, bound in enumerate( bounds ) :
			for intersectIndex in tree.intersectingBounds( bound ) :
				if intersectIndex == index :
					continue
				
				# oh dear, we have an intersection - report it in a helpful way
				self.assertFalse( nodes[index].getName() + " intersects " + nodes[intersectIndex].getName() )
	
	def testCanPositionNodeWithinBackdrop( self ) :
	
		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Backdrop()
		s["n"] = Gaffer.Node()
		
		g = GafferUI.GraphGadget( s )
		backdropBound = g.nodeGadget( s["b"] ).transformedBound( g )
		fallbackPosition = IECore.V2f( backdropBound.center().x, backdropBound.center().y )
		
		g.getLayout().positionNode( g, s["n"], fallbackPosition )
		self.assertEqual( g.getNodePosition( s["n"] ), fallbackPosition )
		
if __name__ == "__main__":
	unittest.main()
	
