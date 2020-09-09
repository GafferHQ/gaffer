##########################################################################
#
#  Copyright (c) 2014-2015, Image Engine Design Inc. All rights reserved.
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

import six

import IECore

import Gaffer
import GafferTest

class NodeAlgoTest( GafferTest.TestCase ) :

	def testUserDefaults( self ) :

		node = GafferTest.AddNode()

		self.assertEqual( node["op1"].getValue(), 0 )
		self.assertFalse( Gaffer.NodeAlgo.hasUserDefault( node["op1"] ) )
		Gaffer.Metadata.registerValue( GafferTest.AddNode, "op1", "userDefault", IECore.IntData( 7 ) )
		self.assertTrue( Gaffer.NodeAlgo.hasUserDefault( node["op1"] ) )
		self.assertFalse( Gaffer.NodeAlgo.isSetToUserDefault( node["op1"] ) )
		Gaffer.NodeAlgo.applyUserDefaults( node )
		self.assertEqual( node["op1"].getValue(), 7 )
		self.assertTrue( Gaffer.NodeAlgo.isSetToUserDefault( node["op1"] ) )

		# even if it's registered, it doesn't get applied outside of the NodeMenu UI
		node2 = GafferTest.AddNode()
		self.assertEqual( node2["op1"].getValue(), 0 )
		Gaffer.NodeAlgo.applyUserDefaults( node2 )
		self.assertEqual( node2["op1"].getValue(), 7 )

		# they can also be applied to the plug directly
		node2["op1"].setValue( 1 )
		Gaffer.NodeAlgo.applyUserDefault( node2["op1"] )
		self.assertEqual( node2["op1"].getValue(), 7 )

		# the userDefault can be unregistered by overriding with None
		node3 = GafferTest.AddNode()
		Gaffer.Metadata.registerValue( GafferTest.AddNode, "op1", "userDefault", None )
		self.assertFalse( Gaffer.NodeAlgo.hasUserDefault( node3["op1"] ) )
		Gaffer.NodeAlgo.applyUserDefaults( node3 )
		self.assertEqual( node3["op1"].getValue(), 0 )
		self.assertFalse( Gaffer.NodeAlgo.isSetToUserDefault( node["op1"] ) )

	def testUserDefaultConnectedToCompute( self ) :

		srcNode = GafferTest.AddNode()
		node = GafferTest.AddNode()

		Gaffer.Metadata.registerValue( GafferTest.AddNode, "op1", "userDefault", IECore.IntData( 7 ) )
		node["op1"].setValue( 7 )
		self.assertTrue( Gaffer.NodeAlgo.isSetToUserDefault( node["op1"] ) )

		node["op1"].setInput( srcNode["sum"] )
		self.assertFalse( Gaffer.NodeAlgo.isSetToUserDefault( node["op1"] ) )

		# Even if it happens to have the same value

		srcNode["op1"].setValue( 7 )
		srcNode["op2"].setValue( 0 )
		self.assertEqual( srcNode["sum"].getValue(), 7 )
		self.assertFalse( Gaffer.NodeAlgo.isSetToUserDefault( node["op1"] ) )

	def testCompoundPlugUserDefaults( self ) :

		node = GafferTest.CompoundPlugNode()

		self.assertEqual( node["p"]["s"].getValue(), "" )
		Gaffer.Metadata.registerValue( GafferTest.CompoundPlugNode, "p.s", "userDefault", IECore.StringData( "from the metadata" ) )
		self.assertFalse( Gaffer.NodeAlgo.isSetToUserDefault( node["p"]["s"] ) )
		Gaffer.NodeAlgo.applyUserDefaults( node )
		self.assertEqual( node["p"]["s"].getValue(), "from the metadata" )
		self.assertTrue( Gaffer.NodeAlgo.isSetToUserDefault( node["p"]["s"] ) )

		# override the metadata for this particular instance
		Gaffer.Metadata.registerValue( node["p"]["s"], "userDefault", IECore.StringData( "i am special" ) )
		self.assertFalse( Gaffer.NodeAlgo.isSetToUserDefault( node["p"]["s"] ) )
		Gaffer.NodeAlgo.applyUserDefaults( node )
		self.assertEqual( node["p"]["s"].getValue(), "i am special" )
		self.assertTrue( Gaffer.NodeAlgo.isSetToUserDefault( node["p"]["s"] ) )

		# this node still gets the original userDefault
		node2 = GafferTest.CompoundPlugNode()
		self.assertFalse( Gaffer.NodeAlgo.isSetToUserDefault( node2["p"]["s"] ) )
		Gaffer.NodeAlgo.applyUserDefaults( node2 )
		self.assertEqual( node2["p"]["s"].getValue(), "from the metadata" )
		self.assertTrue( Gaffer.NodeAlgo.isSetToUserDefault( node2["p"]["s"] ) )

	def testSeveralUserDefaults( self ) :

		node = GafferTest.AddNode()
		node2 = GafferTest.AddNode()

		self.assertEqual( node["op1"].getValue(), 0 )
		self.assertEqual( node2["op1"].getValue(), 0 )

		Gaffer.Metadata.registerValue( GafferTest.AddNode, "op1", "userDefault", IECore.IntData( 1 ) )
		Gaffer.Metadata.registerValue( node2["op1"], "userDefault", IECore.IntData( 2 ) )
		Gaffer.NodeAlgo.applyUserDefaults( [ node, node2 ] )

		self.assertEqual( node["op1"].getValue(), 1 )
		self.assertEqual( node2["op1"].getValue(), 2 )

	def testUnsettableUserDefaults( self ) :

		node = GafferTest.AddNode()
		node["op2"].setInput( node["op1"] )

		self.assertEqual( node["op1"].getValue(), 0 )
		self.assertEqual( node["op2"].getValue(), 0 )

		Gaffer.Metadata.registerValue( GafferTest.AddNode, "op1", "userDefault", IECore.IntData( 1 ) )
		Gaffer.Metadata.registerValue( GafferTest.AddNode, "op2", "userDefault", IECore.IntData( 2 ) )
		Gaffer.NodeAlgo.applyUserDefaults( node )

		self.assertEqual( node["op1"].getValue(), 1 )
		self.assertEqual( node["op2"].getValue(), 1 )

	def testPresets( self ) :

		node = GafferTest.AddNode()

		self.assertEqual( Gaffer.NodeAlgo.presets( node["op1"] ), [] )
		self.assertEqual( Gaffer.NodeAlgo.currentPreset( node["op1"] ), None )

		Gaffer.Metadata.registerValue( node["op1"], "preset:one", 1 )
		Gaffer.Metadata.registerValue( node["op1"], "preset:two", 2 )

		self.assertEqual( Gaffer.NodeAlgo.presets( node["op1"] ), [ "one", "two" ] )
		self.assertEqual( Gaffer.NodeAlgo.currentPreset( node["op1"] ), None )

		Gaffer.NodeAlgo.applyPreset( node["op1"], "one" )
		self.assertEqual( node["op1"].getValue(), 1 )
		self.assertEqual( Gaffer.NodeAlgo.currentPreset( node["op1"] ), "one" )

		Gaffer.NodeAlgo.applyPreset( node["op1"], "two" )
		self.assertEqual( node["op1"].getValue(), 2 )
		self.assertEqual( Gaffer.NodeAlgo.currentPreset( node["op1"] ), "two" )

	def testPresetsArray( self ) :

		node = GafferTest.AddNode()
		self.assertEqual( Gaffer.NodeAlgo.presets( node["op1"] ), [] )

		Gaffer.Metadata.registerValue(
			node["op1"], "presetNames",
			IECore.StringVectorData( [ "a", "b", "c" ] )
		)

		Gaffer.Metadata.registerValue(
			node["op1"], "presetValues",
			IECore.IntVectorData( [ 1, 2, 3 ] )
		)

		self.assertEqual( Gaffer.NodeAlgo.presets( node["op1"] ), [ "a", "b", "c" ] )

		Gaffer.NodeAlgo.applyPreset( node["op1"], "a" )
		self.assertEqual( node["op1"].getValue(), 1 )
		self.assertEqual( Gaffer.NodeAlgo.currentPreset( node["op1"] ), "a" )

		Gaffer.NodeAlgo.applyPreset( node["op1"], "b" )
		self.assertEqual( node["op1"].getValue(), 2 )
		self.assertEqual( Gaffer.NodeAlgo.currentPreset( node["op1"] ), "b" )

		Gaffer.NodeAlgo.applyPreset( node["op1"], "c" )
		self.assertEqual( node["op1"].getValue(), 3 )
		self.assertEqual( Gaffer.NodeAlgo.currentPreset( node["op1"] ), "c" )

		# a preset registered individually should take precedence

		Gaffer.Metadata.registerValue( node["op1"], "preset:c", 10 )
		self.assertEqual( Gaffer.NodeAlgo.currentPreset( node["op1"] ), None )

		Gaffer.NodeAlgo.applyPreset( node["op1"], "c" )
		self.assertEqual( node["op1"].getValue(), 10 )
		self.assertEqual( Gaffer.NodeAlgo.currentPreset( node["op1"] ), "c" )

	def __visitationGraph( self ) :

		# L1_1     L1_2
		#   |       |\
		#   |       | \
		#   |       |  \
		# L2_1   L2_2   L2_3
		#   |\      |   /
		#   | \     |  /
		#   |  \    | /
		#   |   \   |/
		# L3_1   L3_2

		s = Gaffer.ScriptNode()

		s["L1_1"] = GafferTest.MultiplyNode()
		s["L1_2"] = GafferTest.AddNode()

		s["L2_1"] = GafferTest.AddNode()
		s["L2_2"] = GafferTest.MultiplyNode()
		s["L2_3"] = GafferTest.AddNode()

		s["L3_1"] = GafferTest.AddNode()
		s["L3_2"] = GafferTest.MultiplyNode()
		s["L3_2"]["op3"] = Gaffer.IntPlug()

		s["L2_1"]["op1"].setInput( s["L1_1"]["product"] )
		s["L2_2"]["op1"].setInput( s["L1_2"]["sum"] )
		s["L2_3"]["op1"].setInput( s["L1_2"]["sum"] )

		s["L3_1"]["op1"].setInput( s["L2_1"]["sum"] )
		s["L3_2"]["op1"].setInput( s["L2_1"]["sum"] )
		s["L3_2"]["op2"].setInput( s["L2_2"]["product"] )
		s["L3_2"]["op3"].setInput( s["L2_3"]["sum"] )

		return s

	class __CapturingVisitor( object ) :

		def __init__( self ) :

			self.visited = []

		def __call__( self, node ) :

			self.visited.append( node )
			return True

	def testVisitUpstream( self ) :

		g = self.__visitationGraph()

		v = self.__CapturingVisitor()
		Gaffer.NodeAlgo.visitUpstream( g["L3_1"], v )
		self.assertEqual( v.visited, [ g["L2_1"], g["L1_1"] ] )

		del v.visited[:]
		Gaffer.NodeAlgo.visitUpstream( g["L3_2"], v )
		self.assertEqual( v.visited, [ g["L2_1"], g["L2_2"], g["L2_3"], g["L1_1"], g["L1_2"] ] )

		del v.visited[:]
		Gaffer.NodeAlgo.visitUpstream( g["L3_2"], v, order = Gaffer.NodeAlgo.VisitOrder.DepthFirst )
		self.assertEqual( v.visited, [ g["L2_1"], g["L1_1"], g["L2_2"], g["L1_2"], g["L2_3"] ] )

	def testVisitDownstream( self ) :

		g = self.__visitationGraph()

		v = self.__CapturingVisitor()
		Gaffer.NodeAlgo.visitDownstream( g["L1_1"], v )
		self.assertEqual( v.visited, [ g["L2_1"], g["L3_1"], g["L3_2"] ] )

		del v.visited[:]
		Gaffer.NodeAlgo.visitDownstream( g["L1_2"], v )
		self.assertEqual( v.visited, [ g["L2_2"], g["L2_3"], g["L3_2"] ] )

		del v.visited[:]
		Gaffer.NodeAlgo.visitDownstream( g["L1_2"], v, order = Gaffer.NodeAlgo.VisitOrder.DepthFirst )
		self.assertEqual( v.visited, [ g["L2_2"], g["L3_2"], g["L2_3"] ] )

	def testVisitConnected( self ) :

		g = self.__visitationGraph()

		v = self.__CapturingVisitor()
		Gaffer.NodeAlgo.visitConnected( g["L2_1"], v )
		self.assertEqual( v.visited, [ g["L1_1"], g["L3_1"], g["L3_2"], g["L2_2"], g["L2_3"], g["L1_2"] ] )

		v = self.__CapturingVisitor()
		Gaffer.NodeAlgo.visitConnected( g["L2_1"], v, order = Gaffer.NodeAlgo.VisitOrder.DepthFirst )
		self.assertEqual( v.visited, [ g["L1_1"], g["L3_1"], g["L3_2"], g["L2_2"], g["L1_2"], g["L2_3"] ] )

	def testFindUpstream( self ) :

		g = self.__visitationGraph()
		isLevelOne = lambda node : node.getName().startswith( "L1" )

		self.assertEqual( Gaffer.NodeAlgo.findUpstream( g["L3_1"], isLevelOne ), g["L1_1"] )
		self.assertEqual( Gaffer.NodeAlgo.findUpstream( g["L3_2"], isLevelOne ), g["L1_1"] )
		self.assertEqual( Gaffer.NodeAlgo.findUpstream( g["L1_1"], isLevelOne ), None )

	def testFindDownstream( self ) :

		g = self.__visitationGraph()
		isLevelThree = lambda node : node.getName().startswith( "L3" )

		self.assertEqual( Gaffer.NodeAlgo.findDownstream( g["L1_1"], isLevelThree ), g["L3_1"] )
		self.assertEqual( Gaffer.NodeAlgo.findDownstream( g["L1_2"], isLevelThree ), g["L3_2"] )
		self.assertEqual( Gaffer.NodeAlgo.findDownstream( g["L3_2"], isLevelThree ), None )

	def testFindConnected( self ) :

		g = self.__visitationGraph()
		isLevelTwo = lambda node : node.getName().startswith( "L2" )

		self.assertEqual( Gaffer.NodeAlgo.findConnected( g["L1_1"], isLevelTwo ), g["L2_1"] )
		self.assertEqual( Gaffer.NodeAlgo.findConnected( g["L1_2"], isLevelTwo ), g["L2_2"] )
		self.assertEqual( Gaffer.NodeAlgo.findConnected( g["L2_1"], isLevelTwo ), g["L2_2"] )

	def testFindAllUpstream( self ) :

		g = self.__visitationGraph()
		isLevelOne = lambda node : node.getName().startswith( "L1" )

		self.assertEqual( Gaffer.NodeAlgo.findAllUpstream( g["L3_1"], isLevelOne ), [ g["L1_1"] ] )
		self.assertEqual( Gaffer.NodeAlgo.findAllUpstream( g["L3_2"], isLevelOne ), [ g["L1_1"], g["L1_2"] ] )
		self.assertEqual( Gaffer.NodeAlgo.findAllUpstream( g["L1_1"], isLevelOne ), [] )

	def testFindAllDownstream( self ) :

		g = self.__visitationGraph()
		isLevelThree = lambda node : node.getName().startswith( "L3" )

		self.assertEqual( Gaffer.NodeAlgo.findAllDownstream( g["L1_1"], isLevelThree ), [ g["L3_1"], g["L3_2"] ] )
		self.assertEqual( Gaffer.NodeAlgo.findAllDownstream( g["L1_2"], isLevelThree ), [ g["L3_2"] ] )
		self.assertEqual( Gaffer.NodeAlgo.findAllDownstream( g["L3_2"], isLevelThree ), [] )

	def testFindAllConnected( self ) :

		g = self.__visitationGraph()
		isLevelTwo = lambda node : node.getName().startswith( "L2" )

		self.assertEqual( Gaffer.NodeAlgo.findAllConnected( g["L1_1"], isLevelTwo ), [ g["L2_1"], g["L2_2"], g["L2_3"] ] )
		self.assertEqual( Gaffer.NodeAlgo.findAllConnected( g["L1_2"], isLevelTwo ), [ g["L2_2"], g["L2_3"], g["L2_1"] ] )
		self.assertEqual( Gaffer.NodeAlgo.findAllConnected( g["L2_1"], isLevelTwo ), [ g["L2_2"], g["L2_3"] ] )

	def testUpstreamNodes( self ) :

		g = self.__visitationGraph()

		self.assertEqual( Gaffer.NodeAlgo.upstreamNodes( g["L3_1"] ), [ g["L2_1" ], g["L1_1"] ] )
		self.assertEqual( Gaffer.NodeAlgo.upstreamNodes( g["L3_1"], GafferTest.MultiplyNode ), [ g["L1_1"] ] )

	def testDownstreamNodes( self ) :

		g = self.__visitationGraph()

		self.assertEqual( Gaffer.NodeAlgo.downstreamNodes( g["L1_1"] ), [ g["L2_1" ], g["L3_1"], g["L3_2"] ] )
		self.assertEqual( Gaffer.NodeAlgo.downstreamNodes( g["L1_1"], GafferTest.MultiplyNode ), [ g["L3_2"] ] )

	def testConnectedNodes( self ) :

		g = self.__visitationGraph()

		self.assertEqual( Gaffer.NodeAlgo.connectedNodes( g["L1_1"] ), [ g["L2_1" ], g["L3_1"], g["L3_2"], g["L2_2"], g["L2_3"], g["L1_2"] ] )
		self.assertEqual( Gaffer.NodeAlgo.connectedNodes( g["L1_1"], GafferTest.MultiplyNode ), [ g["L3_2"], g["L2_2"] ] )

	def testBadVisitorReturnValue( self ) :

		g = self.__visitationGraph()

		with six.assertRaisesRegex( self, RuntimeError, r"Visitor must return a bool \(True to continue, False to prune\)" ) :
			Gaffer.NodeAlgo.visitUpstream( g["L3_1"], lambda node : None )

	def __boxedVisitationGraph( self ) :

		s = self.__visitationGraph()
		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["L1_1"] ] ) )
		b.setName( "Box_L1_1" )
		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["L2_3"] ] ) )
		b.setName( "Box_L2_3" )
		return s

	def testVisitBoxedNodesDepthFirst( self ) :

		s = self.__boxedVisitationGraph()

		self.assertEqual(
			Gaffer.NodeAlgo.downstreamNodes( s["Box_L1_1"], order = Gaffer.NodeAlgo.VisitOrder.DepthFirst ),
			[ s[ "L2_1"], s["L3_1"], s["L3_2"] ]
		)

		self.assertEqual(
			Gaffer.NodeAlgo.downstreamNodes( s["Box_L1_1"]["L1_1"], order = Gaffer.NodeAlgo.VisitOrder.DepthFirst ),
			[ s["Box_L1_1"], s[ "L2_1"], s["L3_1"], s["L3_2"] ]
		)

		self.assertEqual(
			Gaffer.NodeAlgo.downstreamNodes( s["L1_2"], order = Gaffer.NodeAlgo.VisitOrder.DepthFirst ),
			[ s["L2_2"], s["L3_2"], s["Box_L2_3"], s["Box_L2_3"]["L2_3"] ]
		)

		self.assertEqual(
			Gaffer.NodeAlgo.upstreamNodes( s["Box_L2_3"], order = Gaffer.NodeAlgo.VisitOrder.DepthFirst ),
			[ s[ "L1_2"] ]
		)

		self.assertEqual(
			Gaffer.NodeAlgo.upstreamNodes( s["Box_L2_3"]["L2_3"], order = Gaffer.NodeAlgo.VisitOrder.DepthFirst ),
			[ s["Box_L2_3"], s[ "L1_2"] ]
		)

		self.assertEqual(
			Gaffer.NodeAlgo.upstreamNodes( s["L3_1"], order = Gaffer.NodeAlgo.VisitOrder.DepthFirst ),
			[ s[ "L2_1"], s["Box_L1_1"], s["Box_L1_1"]["L1_1"] ]
		)

	def testVisitBoxedNodesBreadthFirst( self ) :

		s = self.__boxedVisitationGraph()

		self.assertEqual(
			Gaffer.NodeAlgo.downstreamNodes( s["Box_L1_1"], order = Gaffer.NodeAlgo.VisitOrder.BreadthFirst ),
			[ s[ "L2_1"], s["L3_1"], s["L3_2"] ]
		)

		self.assertEqual(
			Gaffer.NodeAlgo.downstreamNodes( s["Box_L1_1"]["L1_1"], order = Gaffer.NodeAlgo.VisitOrder.BreadthFirst ),
			[ s["Box_L1_1"], s[ "L2_1"], s["L3_1"], s["L3_2"] ]
		)

		self.assertEqual(
			Gaffer.NodeAlgo.downstreamNodes( s["L1_2"], order = Gaffer.NodeAlgo.VisitOrder.BreadthFirst ),
			[ s["L2_2"], s["Box_L2_3"], s["Box_L2_3"]["L2_3"], s["L3_2"] ]
		)

		self.assertEqual(
			Gaffer.NodeAlgo.upstreamNodes( s["Box_L2_3"], order = Gaffer.NodeAlgo.VisitOrder.BreadthFirst ),
			[ s[ "L1_2"] ]
		)

		self.assertEqual(
			Gaffer.NodeAlgo.upstreamNodes( s["Box_L2_3"]["L2_3"], order = Gaffer.NodeAlgo.VisitOrder.BreadthFirst ),
			[ s["Box_L2_3"], s[ "L1_2"] ]
		)

		self.assertEqual(
			Gaffer.NodeAlgo.upstreamNodes( s["L3_1"], order = Gaffer.NodeAlgo.VisitOrder.BreadthFirst ),
			[ s[ "L2_1"], s["Box_L1_1"], s["Box_L1_1"]["L1_1"] ]
		)

		self.assertEqual(
			Gaffer.NodeAlgo.upstreamNodes( s["L3_2"], order = Gaffer.NodeAlgo.VisitOrder.BreadthFirst ),
			[ s["L2_1"], s[ "L2_2"], s["Box_L2_3"], s["Box_L2_3"]["L2_3"], s["Box_L1_1"], s["Box_L1_1"]["L1_1"], s["L1_2"] ]
		)

	def testVisitBoxedBranches( self ) :

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()

		s["b"]["L1"] = GafferTest.AddNode()
		s["b"]["L2_1"] = GafferTest.AddNode()
		s["b"]["L2_2"] = GafferTest.AddNode()
		s["b"]["L3_1"] = GafferTest.AddNode()

		s["b"]["L1"]["op1"].setInput( s["b"]["L2_1"]["sum"] )
		s["b"]["L1"]["op2"].setInput( s["b"]["L2_2"]["sum"] )

		s["b"]["L2_1"]["op1"].setInput( s["b"]["L3_1"]["sum"] )

		s["n"] = GafferTest.AddNode()
		s["n"]["op1"].setInput( Gaffer.PlugAlgo.promote( s["b"]["L1"]["sum"] ) )

		self.assertEqual(
			Gaffer.NodeAlgo.upstreamNodes( s["n"], order = Gaffer.NodeAlgo.VisitOrder.DepthFirst ),
			[ s["b"], s["b"]["L1"], s["b"]["L2_1"], s["b"]["L3_1"], s["b"]["L2_2"] ]
		)

		self.assertEqual(
			Gaffer.NodeAlgo.upstreamNodes( s["n"], order = Gaffer.NodeAlgo.VisitOrder.BreadthFirst ),
			[ s["b"], s["b"]["L1"], s["b"]["L2_1"], s["b"]["L2_2"], s["b"]["L3_1"] ]
		)

	def tearDown( self ) :

		Gaffer.Metadata.deregisterValue( GafferTest.AddNode, "op1", "userDefault" )
		Gaffer.Metadata.deregisterValue( GafferTest.AddNode, "op2", "userDefault" )
		Gaffer.Metadata.deregisterValue( GafferTest.CompoundPlugNode, "p.s", "userDefault" )

if __name__ == "__main__":
	unittest.main()
