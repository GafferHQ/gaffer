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
import itertools

import IECore

import Gaffer
import GafferTest
import GafferDispatch
import GafferDispatchTest

class TaskNodeTest( GafferTest.TestCase ) :

	def testTypeNamePrefixes( self ) :

		self.assertTypeNamesArePrefixed( GafferDispatch )

	def testDefaultNames( self ) :

		self.assertDefaultNamesAreCorrect( GafferDispatch )

	def testNodesConstructWithDefaultValues( self ) :

		self.assertNodesConstructWithDefaultValues( GafferDispatch )

	def testDerivedClasses( self ) :

		self.assertTrue( issubclass( GafferDispatchTest.LoggingTaskNode, GafferDispatch.TaskNode ) )
		self.assertTrue( isinstance( GafferDispatchTest.LoggingTaskNode(), GafferDispatch.TaskNode ) )

	def testHash( self ) :

		c1 = Gaffer.Context()
		c1.setFrame( 1 )
		c2 = Gaffer.Context()
		c2.setFrame( 2 )
		c3 = Gaffer.Context()
		c3.setFrame( 3.0 )

		# Hashes that don't use the context are equivalent
		n = GafferDispatchTest.LoggingTaskNode()
		with c1 :
			c1h = n["task"].hash()
		with c2 :
			c2h = n["task"].hash()
		with c3 :
			c3h = n["task"].hash()

		self.assertEqual( c1h, c2h )
		self.assertEqual( c1h, c3h )

		# Hashes that do use the context differ
		n2 = GafferDispatchTest.LoggingTaskNode()
		n2["frameSensitivePlug"] = Gaffer.StringPlug( defaultValue = "####" )
		with c1 :
			c1h = n2["task"].hash()
		with c2 :
			c2h = n2["task"].hash()
		with c3 :
			c3h = n2["task"].hash()

		self.assertNotEqual( c1h, c2h )
		self.assertNotEqual( c1h, c3h )

		# Hashes match across the same node type
		n3 = GafferDispatchTest.LoggingTaskNode()
		n3["frameSensitivePlug"] = Gaffer.StringPlug( defaultValue = "####" )
		with c1 :
			c1h2 = n3["task"].hash()
		with c2 :
			c2h2 = n3["task"].hash()
		with c3 :
			c3h2 = n3["task"].hash()

		self.assertEqual( c1h, c1h2 )
		self.assertEqual( c2h, c2h2 )
		self.assertEqual( c3h, c3h2 )

		# Hashes differ across different node types
		class MyNode( GafferDispatchTest.LoggingTaskNode ) :
			def __init__( self ) :
				GafferDispatchTest.LoggingTaskNode.__init__( self )

		IECore.registerRunTimeTyped( MyNode )

		n4 = MyNode()
		n4["frameSensitivePlug"] = Gaffer.StringPlug( defaultValue = "####" )
		with c1 :
			c1h3 = n4["task"].hash()
		with c2 :
			c2h3 = n4["task"].hash()
		with c3 :
			c3h3 = n4["task"].hash()

		self.assertNotEqual( c1h3, c1h2 )
		self.assertNotEqual( c2h3, c2h2 )
		self.assertNotEqual( c3h3, c3h2 )

	def testExecute( self ) :

		n = GafferDispatchTest.LoggingTaskNode()
		self.assertEqual( len( n.log ), 0 )

		n["task"].execute()
		self.assertEqual( len( n.log ), 1 )

		n["task"].execute()
		self.assertEqual( len( n.log ), 2 )

		c = Gaffer.Context()
		c.setFrame( Gaffer.Context.current().getFrame() + 1 )
		with c :
			n["task"].execute()
		self.assertEqual( len( n.log ), 3 )

	def testExecuteSequence( self ) :

		n = GafferDispatchTest.LoggingTaskNode()
		self.assertEqual( len( n.log ), 0 )

		n["task"].executeSequence( [ 1, 2, 3 ] )
		self.assertEqual( len( n.log ), 3 )

		n["task"].executeSequence( [ 1, 5, 10 ] )
		self.assertEqual( len( n.log ), 6 )

		n2 = GafferDispatchTest.LoggingTaskNode()
		n2["requiresSequenceExecution"].setValue( True )
		self.assertEqual( len( n2.log ), 0 )

		n2["task"].executeSequence( [ 1, 2, 3 ] )
		self.assertEqual( len( n2.log ), 1 )

		n2["task"].executeSequence( [ 1, 5, 10 ] )
		self.assertEqual( len( n2.log ), 2 )

	def testRequiresSequenceExecution( self ) :

		n = GafferDispatchTest.LoggingTaskNode()
		self.assertEqual( n.requiresSequenceExecution(), False )

	def testPreTasks( self ) :

		c1 = Gaffer.Context()
		c1.setFrame( 1 )
		c2 = Gaffer.Context()
		c2.setFrame( 2 )

		n = GafferDispatchTest.LoggingTaskNode()

		with c1 :
			self.assertEqual( n["task"].preTasks(), [ GafferDispatch.TaskNode.Task( n["preTasks"][0], c1 ) ] )
		with c2 :
			self.assertEqual( n["task"].preTasks(), [ GafferDispatch.TaskNode.Task( n["preTasks"][0], c2 ) ] )

	def testTaskConstructors( self ) :

		c = Gaffer.Context()

		n = GafferDispatchTest.LoggingTaskNode()
		t = GafferDispatch.TaskNode.Task( n["task"], c )
		t2 = GafferDispatch.TaskNode.Task( t )
		t3 = GafferDispatch.TaskNode.Task( n["task"], c )

		self.assertEqual( t.plug(), n["task"] )
		self.assertEqual( t.context(), c )
		self.assertEqual( t2.plug(), n["task"] )
		self.assertEqual( t2.context(), c )
		self.assertEqual( t3.plug(), n["task"] )
		self.assertEqual( t3.context(), c )

	def testTaskComparison( self ) :

		c = Gaffer.Context()
		n = GafferDispatchTest.LoggingTaskNode()
		t1 = GafferDispatch.TaskNode.Task( n["task"], c )
		t2 = GafferDispatch.TaskNode.Task( n["task"], c )
		c2 = Gaffer.Context()
		c2["a"] = 2
		t3 = GafferDispatch.TaskNode.Task( n["task"], c2 )
		n2 = GafferDispatchTest.LoggingTaskNode()
		t4 = GafferDispatch.TaskNode.Task( n2["task"], c2 )

		self.assertEqual( t1, t1 )
		self.assertEqual( t1, t2 )
		self.assertEqual( t2, t1 )
		self.assertNotEqual( t1, t3 )
		self.assertNotEqual( t3, t1 )
		self.assertNotEqual( t3, t4 )
		self.assertNotEqual( t4, t3 )

	def testInputAcceptanceInsideBoxes( self ) :

		s = Gaffer.ScriptNode()

		s["a"] = GafferDispatchTest.TextWriter()
		s["b"] = GafferDispatchTest.TextWriter()
		s["n"] = Gaffer.Node()
		s["n"]["task"] = Gaffer.Plug( direction = Gaffer.Plug.Direction.Out )

		# the TaskNode shouldn't accept inputs from any old node

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

		# TaskNodes should accept connections speculatively from unconnected box inputs and outputs

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
		p = Gaffer.PlugAlgo.promote( s["b"]["e"]["preTasks"][0] )
		p.setName( "p" )

		s["b"].exportForReference( self.temporaryDirectory() / "test.grf" )

		s["r"] = Gaffer.Reference()
		s["r"].load( self.temporaryDirectory() / "test.grf" )

		s["e"] = GafferDispatchTest.TextWriter()

		s["r"]["p"].setInput( s["e"]["task"] )

	def testReferencePromotedPreTasksArrayPlug( self ) :

		s = Gaffer.ScriptNode()

		s["b"] = Gaffer.Box()
		s["b"]["e"] = GafferDispatchTest.TextWriter()
		p = Gaffer.PlugAlgo.promote( s["b"]["e"]["preTasks"] )
		p.setName( "p" )

		s["b"].exportForReference( self.temporaryDirectory() / "test.grf" )

		s["r"] = Gaffer.Reference()
		s["r"].load( self.temporaryDirectory() / "test.grf" )

		s["e"] = GafferDispatchTest.TextWriter()

		s["r"]["p"][0].setInput( s["e"]["task"] )

		self.assertTrue( s["r"]["e"]["preTasks"][0].source().isSame( s["e"]["task"] ) )

	def testPostTasks( self ) :

		writer = GafferDispatchTest.TextWriter()

		c = Gaffer.Context()
		c["test"] = "test"
		with c :
			self.assertEqual( writer["task"].preTasks(), [ GafferDispatch.TaskNode.Task( writer["preTasks"][0], c ) ] )
			self.assertEqual( writer["task"].postTasks(), [ GafferDispatch.TaskNode.Task( writer["postTasks"][0], c ) ] )

	def testExecuteSequenceWithIterable( self ) :

		n = GafferDispatchTest.LoggingTaskNode()

		n["task"].executeSequence( tuple( [ 1, 2, 3 ] ) )
		self.assertEqual( len( n.log ), 3 )

		n["task"].executeSequence( itertools.chain( [ 1, 2, 3 ], [ 4, 5, 6 ] ) )
		self.assertEqual( len( n.log ), 9 )

	def testErrorSignal( self ) :

		n = GafferDispatchTest.ErroringTaskNode()

		for f, args in [
			( "execute", [] ),
			( "executeSequence", [ ( 1, 2, 3 ) ] ),
			( "hash", [] ),
			( "requiresSequenceExecution", [] ),
			( "preTasks", [] ),
			( "postTasks", [] ),
		] :

			cs = GafferTest.CapturingSlot( n.errorSignal() )

			self.assertRaisesRegex(
				RuntimeError,
				"Error in {}".format( f ),
				getattr( n["task"], f ),
				*args
			)

			self.assertEqual( len( cs ), 1 )
			self.assertEqual( cs[0][0], n["task"] )
			self.assertEqual( cs[0][1], n["task"] )
			self.assertIn(
				"Error in {}".format( f ),
				cs[0][2]
			)

	def testDependencyNode( self ) :

		n = GafferDispatchTest.LoggingTaskNode()
		self.assertTrue( isinstance( n, Gaffer.DependencyNode ) )
		self.assertTrue( n.isInstanceOf( Gaffer.DependencyNode.staticTypeId() ) )

	def testDirtyPropagation( self ) :

		n1 = GafferDispatchTest.TextWriter()
		n2 = GafferDispatchTest.TextWriter()
		n3 = GafferDispatchTest.TextWriter()

		n2["preTasks"][0].setInput( n1["task"] )
		n3["preTasks"][0].setInput( n2["task"] )

		cs1 = GafferTest.CapturingSlot( n1.plugDirtiedSignal() )
		cs2 = GafferTest.CapturingSlot( n2.plugDirtiedSignal() )
		cs3 = GafferTest.CapturingSlot( n3.plugDirtiedSignal() )

		n1["fileName"].setValue( "test.txt" )

		self.assertIn( n1["task"], { x[0] for x in cs1 } )
		self.assertIn( n2["task"], { x[0] for x in cs2 } )
		self.assertIn( n3["task"], { x[0] for x in cs3 } )

	def testOverrideAffectsTask( self ) :

		class MySystemCommand( GafferDispatch.SystemCommand ) :

			def __init__( self, name = "MySystemCommand" ) :

				GafferDispatch.SystemCommand.__init__( self, name )

				self["nothingToDoWithTask"] = Gaffer.StringPlug()

			def affectsTask( self, input ) :

				if input == self["nothingToDoWithTask"] :
					return False
				else :
					return GafferDispatch.SystemCommand.affectsTask( self, input )

		IECore.registerRunTimeTyped( MySystemCommand, typeName = "GafferDispatchTest::MySystemCommand" )

		n = MySystemCommand()
		cs = GafferTest.CapturingSlot( n.plugDirtiedSignal() )

		n["command"].setValue( "ls" )
		self.assertIn( n["command"], { x[0] for x in cs } )
		self.assertIn( n["task"], { x[0] for x in cs } )
		del cs[:]

		n["nothingToDoWithTask"].setValue( "irrelevant" )
		self.assertIn( n["nothingToDoWithTask"], { x[0] for x in cs } )
		self.assertNotIn( n["task"], { x[0] for x in cs } )

	def testSubclassAndBuildInternalNetwork( self ) :

		class TaskSubnet( GafferDispatch.TaskNode ) :

			def __init__( self, name = "TaskSubnet", log = None ) :

				GafferDispatch.TaskNode.__init__( self, name )

				self["internalTask"] = GafferDispatchTest.LoggingTaskNode( log = log )
				self["internalTask"]["preTasks"].setInput( self["preTasks"] )
				self["internalTask"]["postTasks"].setInput( self["postTasks"] )

				self["task"].setInput( self["internalTask"]["task"] )

		log = []

		# n1
		# |
		# n3-n2

		s = Gaffer.ScriptNode()
		s["n1"] = GafferDispatchTest.LoggingTaskNode( log = log )

		s["n2"] = GafferDispatchTest.LoggingTaskNode( log = log )

		s["n3"] = TaskSubnet( log = log )
		s["n3"]["preTasks"][0].setInput( s["n1"]["task"] )
		s["n3"]["postTasks"][0].setInput( s["n2"]["task"] )

		preTasks = s["n3"]["task"].preTasks()
		self.assertEqual( len( preTasks ), 2 )
		self.assertEqual( preTasks[0].plug(), s["n3"]["internalTask"]["preTasks"][0] )
		self.assertEqual( preTasks[1].plug(), s["n3"]["internalTask"]["preTasks"][1] )

		postTasks = s["n3"]["task"].postTasks()
		self.assertEqual( len( postTasks ), 2 )
		self.assertEqual( postTasks[0].plug(), s["n3"]["internalTask"]["postTasks"][0] )
		self.assertEqual( postTasks[1].plug(), s["n3"]["internalTask"]["postTasks"][1] )

		dispatcher = GafferDispatchTest.DispatcherTest.TestDispatcher()
		dispatcher["jobsDirectory"].setValue( self.temporaryDirectory() )
		dispatcher.dispatch( [ s["n3"] ] )

		self.assertEqual( len( log ), 3 )
		self.assertEqual( [ l.node for l in log ], [ s["n1"], s["n3"]["internalTask"], s["n2"] ] )

if __name__ == "__main__":
	unittest.main()
