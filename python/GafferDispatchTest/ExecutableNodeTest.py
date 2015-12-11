##########################################################################
#
#  Copyright (c) 2013-2014, Image Engine Design Inc. All rights reserved.
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

import os
import unittest

import IECore

import Gaffer
import GafferTest
import GafferDispatch
import GafferDispatchTest

class ExecutableNodeTest( GafferTest.TestCase ) :

	def testTypeNamePrefixes( self ) :

		self.assertTypeNamesArePrefixed( GafferDispatch )

	def testDefaultNames( self ) :

		self.assertDefaultNamesAreCorrect( GafferDispatch )

	def testNodesConstructWithDefaultValues( self ) :

		self.assertNodesConstructWithDefaultValues( GafferDispatch )

	def testIsExecutable( self ) :

		self.assertTrue( issubclass( GafferDispatchTest.CountingExecutableNode, GafferDispatch.ExecutableNode ) )
		self.assertTrue( isinstance( GafferDispatchTest.CountingExecutableNode(), GafferDispatch.ExecutableNode ) )

	def testHash( self ) :

		c1 = Gaffer.Context()
		c1.setFrame( 1 )
		c2 = Gaffer.Context()
		c2.setFrame( 2 )
		c3 = Gaffer.Context()
		c3.setFrame( 3.0 )

		# hashes that don't use the context are equivalent
		n = GafferDispatchTest.CountingExecutableNode( withHash = False )
		self.assertEqual( n.hash( c1 ), n.hash( c1 ) )
		self.assertEqual( n.hash( c1 ), n.hash( c2 ) )
		self.assertEqual( n.hash( c1 ), n.hash( c3 ) )

		# hashes that do use the context differ
		n2 = GafferDispatchTest.CountingExecutableNode( withHash = True )
		self.assertEqual( n2.hash( c1 ), n2.hash( c1 ) )
		self.assertNotEqual( n2.hash( c1 ), n2.hash( c2 ) )
		self.assertNotEqual( n2.hash( c1 ), n2.hash( c3 ) )

		# hashes match across the same node type
		n3 = GafferDispatchTest.CountingExecutableNode( withHash = True )
		self.assertEqual( n2.hash( c1 ), n3.hash( c1 ) )
		self.assertEqual( n2.hash( c2 ), n3.hash( c2 ) )
		self.assertEqual( n2.hash( c3 ), n3.hash( c3 ) )

		# hashes differ across different node types
		class MyNode( GafferDispatchTest.CountingExecutableNode ) :
			def __init__( self ) :
				GafferDispatchTest.CountingExecutableNode.__init__( self )

		IECore.registerRunTimeTyped( MyNode )

		n4 = MyNode()

		self.assertNotEqual( n4.hash( c1 ), n3.hash( c1 ) )
		self.assertNotEqual( n4.hash( c2 ), n3.hash( c2 ) )
		self.assertNotEqual( n4.hash( c3 ), n3.hash( c3 ) )

	def testExecute( self ) :

		n = GafferDispatchTest.CountingExecutableNode()
		self.assertEqual( n.executionCount, 0 )

		n.execute()
		self.assertEqual( n.executionCount, 1 )

		n.execute()
		self.assertEqual( n.executionCount, 2 )

		c = Gaffer.Context()
		c.setFrame( Gaffer.Context.current().getFrame() + 1 )
		with c :
			n.execute()
		self.assertEqual( n.executionCount, 3 )

	def testExecuteSequence( self ) :

		n = GafferDispatchTest.CountingExecutableNode()
		self.assertEqual( n.executionCount, 0 )

		n.executeSequence( [ 1, 2, 3 ] )
		self.assertEqual( n.executionCount, 3 )

		n.executeSequence( [ 1, 5, 10 ] )
		self.assertEqual( n.executionCount, 6 )

		# requiring execution doesn't tally the count per frame
		n2 = GafferDispatchTest.CountingExecutableNode( requiresSequenceExecution = True )
		self.assertEqual( n2.executionCount, 0 )

		n2.executeSequence( [ 1, 2, 3 ] )
		self.assertEqual( n2.executionCount, 1 )

		n2.executeSequence( [ 1, 5, 10 ] )
		self.assertEqual( n2.executionCount, 2 )

	def testRequiresSequenceExecution( self ) :

		n = GafferDispatchTest.CountingExecutableNode()
		self.assertEqual( n.requiresSequenceExecution(), False )

	def testPreTasks( self ) :

		c1 = Gaffer.Context()
		c1.setFrame( 1 )
		c2 = Gaffer.Context()
		c2.setFrame( 2 )

		n = GafferDispatchTest.CountingExecutableNode()
		n2 = GafferDispatchTest.CountingExecutableNode()

		# make n2 require n
		n2["preTasks"][0].setInput( n["task"] )

		self.assertEqual( n.preTasks(c1), [] )
		self.assertEqual( n2.preTasks(c1), [ GafferDispatch.ExecutableNode.Task( n, c1 ) ] )
		self.assertEqual( n2.preTasks(c2), [ GafferDispatch.ExecutableNode.Task( n, c2 ) ] )

	def testTaskConstructors( self ) :

		c = Gaffer.Context()

		n = Gaffer.ExecutableOpHolder()
		t = GafferDispatch.ExecutableNode.Task( n, c )
		t2 = GafferDispatch.ExecutableNode.Task( n, c )
		t3 = GafferDispatch.ExecutableNode.Task( t2 )

		self.assertEqual( t.node(), n )
		self.assertEqual( t.context(), c )
		self.assertEqual( t2.node(), n )
		self.assertEqual( t2.context(), c )
		self.assertEqual( t3.node(), n )
		self.assertEqual( t3.context(), c )

	def testTaskComparison( self ) :

		c = Gaffer.Context()
		n = Gaffer.ExecutableOpHolder()
		t1 = GafferDispatch.ExecutableNode.Task( n, c )
		t2 = GafferDispatch.ExecutableNode.Task( n, c )
		c2 = Gaffer.Context()
		c2["a"] = 2
		t3 = GafferDispatch.ExecutableNode.Task( n, c2 )
		n2 = Gaffer.ExecutableOpHolder()
		t4 = GafferDispatch.ExecutableNode.Task( n2, c2 )

		self.assertEqual( t1, t1 )
		self.assertEqual( t1, t2 )
		self.assertEqual( t2, t1 )
		self.assertNotEqual( t1, t3 )
		self.assertNotEqual( t3, t1 )
		self.assertNotEqual( t3, t4 )
		self.assertNotEqual( t4, t3 )

	def testTaskSet( self ) :

		# an empty ExecutableOpHolder doesn't actually compute anything, so all tasks are the same
		c = Gaffer.Context()
		n = Gaffer.ExecutableOpHolder()
		t1 = GafferDispatch.ExecutableNode.Task( n, c )
		t2 = GafferDispatch.ExecutableNode.Task( n, c )
		self.assertEqual( t1, t2 )
		c2 = Gaffer.Context()
		c2["a"] = 2
		t3 = GafferDispatch.ExecutableNode.Task( n, c2 )
		self.assertEqual( t1, t3 )
		n2 = Gaffer.ExecutableOpHolder()
		t4 = GafferDispatch.ExecutableNode.Task( n2, c2 )
		self.assertEqual( t1, t4 )
		t5 = GafferDispatch.ExecutableNode.Task( n2, c )
		self.assertEqual( t1, t5 )

		s = set( [ t1, t2, t3, t4, t4, t4, t1, t2, t4, t3, t2 ] )
		# there should only be 1 task because they all have identical results
		self.assertEqual( len(s), 1 )
		self.assertEqual( s, set( [ t1 ] ) )
		self.assertTrue( t1 in s )
		self.assertTrue( t2 in s )
		self.assertTrue( t3 in s )
		self.assertTrue( t4 in s )
		# even t5 is in there, because it's really the same task
		self.assertTrue( t5 in s )

		# MyNode.hash() depends on the context time, so tasks will vary
		my = GafferDispatchTest.CountingExecutableNode()
		c.setFrame( 1 )
		t1 = GafferDispatch.ExecutableNode.Task( my, c )
		t2 = GafferDispatch.ExecutableNode.Task( my, c )
		self.assertEqual( t1, t2 )
		c2 = Gaffer.Context()
		c2.setFrame( 2 )
		t3 = GafferDispatch.ExecutableNode.Task( my, c2 )
		self.assertNotEqual( t1, t3 )
		my2 = GafferDispatchTest.CountingExecutableNode()
		t4 = GafferDispatch.ExecutableNode.Task( my2, c2 )
		self.assertNotEqual( t1, t4 )
		self.assertEqual( t3, t4 )
		t5 = GafferDispatch.ExecutableNode.Task( my2, c )
		self.assertEqual( t1, t5 )
		self.assertNotEqual( t3, t5 )

		s = set( [ t1, t2, t3, t4, t4, t4, t1, t2, t4, t3, t2 ] )
		# t1 and t3 are the only distinct tasks
		self.assertEqual( len(s), 2 )
		self.assertEqual( s, set( [ t1, t3 ] ) )
		# but they still all have equivalent tasks in the set
		self.assertTrue( t1 in s )
		self.assertTrue( t2 in s )
		self.assertTrue( t3 in s )
		self.assertTrue( t4 in s )
		self.assertTrue( t5 in s )

	def testInputAcceptanceInsideBoxes( self ) :

		s = Gaffer.ScriptNode()

		s["a"] = GafferDispatchTest.TextWriter()
		s["b"] = GafferDispatchTest.TextWriter()
		s["n"] = Gaffer.Node()
		s["n"]["task"] = Gaffer.Plug( direction = Gaffer.Plug.Direction.Out )

		# the ExecutableNode shouldn't accept inputs from any old node

		self.assertTrue( s["b"]["preTasks"][0].acceptsInput( s["a"]["task"] ) )
		self.assertFalse( s["b"]["preTasks"][0].acceptsInput( s["n"]["task"] ) )

		# and that shouldn't change just because we happen to be inside a box

		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["a"], s["b"], s["n"] ] ) )

		self.assertTrue( b["b"]["preTasks"][0].acceptsInput( b["a"]["task"] ) )
		self.assertFalse( b["b"]["preTasks"][0].acceptsInput( b["n"]["task"] ) )

	def testInputAcceptanceFromBoxes( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["task"] = Gaffer.Plug( direction = Gaffer.Plug.Direction.Out )
		s["a"] = GafferDispatchTest.TextWriter()

		s["b"] = Gaffer.Box()
		s["b"]["a"] = GafferDispatchTest.TextWriter()
		s["b"]["b"] = GafferDispatchTest.TextWriter()
		s["b"]["n"] = Gaffer.Node()
		s["b"]["n"]["task"] = Gaffer.Plug( direction = Gaffer.Plug.Direction.Out )
		s["b"]["in"] = s["b"]["a"]["preTasks"][0].createCounterpart( "in", Gaffer.Plug.Direction.In )
		s["b"]["out"] = s["b"]["a"]["task"].createCounterpart( "out", Gaffer.Plug.Direction.Out )

		# ExecutableNodes should accept connections speculatively from unconnected box inputs and outputs

		self.assertTrue( s["b"]["a"]["preTasks"][0].acceptsInput( s["b"]["in"] ) )
		self.assertTrue( s["a"]["preTasks"][0].acceptsInput( s["b"]["out"] ) )

		# But the promoted plugs shouldn't accept any old inputs.

		self.assertFalse( s["b"]["in"].acceptsInput( s["n"]["task"] ) )
		self.assertFalse( s["b"]["out"].acceptsInput( s["b"]["n"]["task"] ) )

		# We should be able to connect them up only to other appropriate requirement plugs.

		self.assertTrue( s["a"]["preTasks"][0].acceptsInput( s["b"]["out"] ) )

		s["c"] = GafferDispatchTest.TextWriter()
		s["b"]["in"].setInput( s["c"]["task"] )
		self.assertTrue( s["b"]["a"]["preTasks"][0].acceptsInput( s["b"]["in"] ) )

		s["b"]["out"].setInput( s["b"]["b"]["task"] )
		self.assertTrue( s["a"]["preTasks"][0].acceptsInput( s["b"]["out"] ) )

	def testInputAcceptanceFromDots( self ) :

		e1 = GafferDispatchTest.TextWriter()
		e2 = GafferDispatchTest.TextWriter()

		d1 = Gaffer.Dot()
		d1.setup( e1["task"] )

		self.assertTrue( e2["preTasks"][0].acceptsInput( d1["out"] ) )

		d1["in"].setInput( e1["task"] )

		self.assertTrue( e2["preTasks"][0].acceptsInput( d1["out"] ) )

	def testReferencePromotedPreTasksPlug( self ) :

		s = Gaffer.ScriptNode()

		s["b"] = Gaffer.Box()
		s["b"]["e"] = GafferDispatchTest.TextWriter()
		p = s["b"].promotePlug( s["b"]["e"]["preTasks"][0] )
		p.setName( "p" )

		s["b"].exportForReference( self.temporaryDirectory() + "/test.grf" )

		s["r"] = Gaffer.Reference()
		s["r"].load( self.temporaryDirectory() + "/test.grf" )

		s["e"] = GafferDispatchTest.TextWriter()

		s["r"]["p"].setInput( s["e"]["task"] )

	def testReferencePromotedPreTasksPlug( self ) :

		s = Gaffer.ScriptNode()

		s["b"] = Gaffer.Box()
		s["b"]["e"] = GafferDispatchTest.TextWriter()
		p = s["b"].promotePlug( s["b"]["e"]["preTasks"] )
		p.setName( "p" )

		s["b"].exportForReference( self.temporaryDirectory() + "/test.grf" )

		s["r"] = Gaffer.Reference()
		s["r"].load( self.temporaryDirectory() + "/test.grf" )

		s["e"] = GafferDispatchTest.TextWriter()

		s["r"]["p"][0].setInput( s["e"]["task"] )

		self.assertTrue( s["r"]["e"]["preTasks"][0].source().isSame( s["e"]["task"] ) )

	def testLoadPromotedRequirementsFromVersion0_15( self ) :

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( os.path.dirname( __file__ ) + "/scripts/promotedRequirementsVersion-0.15.0.0.gfr" )
		s.load()

	def testLoadPromotedRequirementsNetworkFromVersion0_15( self ) :

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( os.path.dirname( __file__ ) + "/scripts/promotedRequirementsNetworkVersion-0.15.0.0.gfr" )
		s.load()

	def testPostTasks( self ) :

		preWriter = GafferDispatchTest.TextWriter()
		postWriter = GafferDispatchTest.TextWriter()

		writer = GafferDispatchTest.TextWriter()
		writer["preTasks"][0].setInput( preWriter["task"] )
		writer["postTasks"][0].setInput( postWriter["task"] )

		c = Gaffer.Context()
		c["test"] = "test"
		with c :
			self.assertEqual( writer.preTasks( c ), [ GafferDispatch.ExecutableNode.Task( preWriter, c ) ] )
			self.assertEqual( writer.postTasks( c ), [ GafferDispatch.ExecutableNode.Task( postWriter, c ) ] )

	def testLoadNetworkFromVersion0_19( self ) :

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( os.path.dirname( __file__ ) + "/scripts/version-0.19.0.0.gfr" )
		s.load()

		self.assertEqual( len( s["TaskList"]["preTasks"] ), 2 )
		self.assertEqual( s["TaskList"]["preTasks"][0].getName(), "preTask0" )
		self.assertEqual( s["TaskList"]["preTasks"][1].getName(), "preTask1" )

		self.assertTrue( s["TaskList"]["preTasks"][0].getInput().isSame( s["SystemCommand"]["task"] ) )
		self.assertTrue( s["TaskList"]["preTasks"][1].getInput() is None )

if __name__ == "__main__":
	unittest.main()
