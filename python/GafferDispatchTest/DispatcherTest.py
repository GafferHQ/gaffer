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

import os
import stat
import unittest
import functools
import itertools
import time

import IECore

import Gaffer
import GafferTest
import GafferDispatch
import GafferDispatchTest

class DispatcherTest( GafferTest.TestCase ) :

	class TestDispatcher( GafferDispatch.Dispatcher ) :

		def __init__( self ) :

			GafferDispatch.Dispatcher.__init__( self )

		def _doDispatch( self, batch ) :

			if batch.blindData().get( "testDispatcher:dispatched" ) :
				return

			for upstreamBatch in batch.preTasks() :
				self._doDispatch( upstreamBatch )

			batch.execute()
			batch.blindData()["testDispatcher:dispatched"] = IECore.BoolData( True )

		@staticmethod
		def _doSetupPlugs( parentPlug ) :

			parentPlug["testDispatcherPlug"] = Gaffer.IntPlug(
				direction = Gaffer.Plug.Direction.In,
				flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic
			)

	IECore.registerRunTimeTyped( TestDispatcher )

	class NullDispatcher( GafferDispatch.Dispatcher ) :

		def __init__( self ) :

			GafferDispatch.Dispatcher.__init__( self )

			self.lastDispatch = None

		def _doDispatch( self, batch ) :

			self.lastDispatch = batch

	IECore.registerRunTimeTyped( NullDispatcher )

	def setUp( self ) :

		GafferTest.TestCase.setUp( self )

		def create( jobsDirectory ) :

			dispatcher = DispatcherTest.TestDispatcher()
			dispatcher["jobsDirectory"].setValue( jobsDirectory )
			return dispatcher

		GafferDispatch.Dispatcher.registerDispatcher( "testDispatcher", functools.partial( create, self.temporaryDirectory() ) )

	def tearDown( self ) :

		GafferTest.TestCase.tearDown( self )

		GafferDispatch.Dispatcher.deregisterDispatcher( "testDispatcher" )
		GafferDispatch.Dispatcher.deregisterDispatcher( "testDispatcherWithCustomPlugs" )

	def testBadJobDirectory( self ) :

		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )
		self.assertEqual( dispatcher["jobName"].getValue(), "" )
		self.assertEqual( dispatcher["jobsDirectory"].getValue(), self.temporaryDirectory() )

		s = Gaffer.ScriptNode()
		s["n1"] = GafferDispatchTest.LoggingTaskNode()
		dispatcher.dispatch( [ s["n1"] ] )

		jobDir = dispatcher.jobDirectory()
		self.assertEqual( jobDir, self.temporaryDirectory() + "/000000" )
		self.assertTrue( os.path.exists( jobDir ) )

	def testDerivedClass( self ) :

		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )

		s = Gaffer.ScriptNode()
		s["n1"] = GafferDispatchTest.LoggingTaskNode()

		dispatcher.dispatch( [ s["n1"] ] )

		self.assertEqual( len( s["n1"].log ), 1 )

	def testNoScript( self ) :

		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )

		n = GafferDispatchTest.LoggingTaskNode()

		self.assertRaises( RuntimeError, dispatcher.dispatch, [ n ] )
		self.assertEqual( dispatcher.jobDirectory(), "" )
		self.assertEqual( n.log, [] )

	def testDifferentScripts( self ) :

		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )

		s = Gaffer.ScriptNode()
		s["n1"] = GafferDispatchTest.LoggingTaskNode()

		s2 = Gaffer.ScriptNode()
		s2["n2"] = GafferDispatchTest.LoggingTaskNode()

		self.assertRaises( RuntimeError, dispatcher.dispatch, [ s["n1"], s2["n2"] ] )
		self.assertEqual( dispatcher.jobDirectory(), "" )
		self.assertEqual( s["n1"].log, [] )
		self.assertEqual( s2["n2"].log, [] )

	def testNonTaskNodes( self ) :

		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )

		s = Gaffer.ScriptNode()
		s["n1"] = Gaffer.Node()

		self.assertRaises( RuntimeError, dispatcher.dispatch, [ s["n1"] ] )
		self.assertEqual( dispatcher.jobDirectory(), "" )

	def testDispatcherRegistration( self ) :

		self.assertIn( "testDispatcher", GafferDispatch.Dispatcher.registeredDispatchers() )
		self.assertIsInstance( GafferDispatch.Dispatcher.create( 'testDispatcher' ), DispatcherTest.TestDispatcher )

		GafferDispatch.Dispatcher.deregisterDispatcher( "testDispatcher" )
		self.assertNotIn( "testDispatcher", GafferDispatch.Dispatcher.registeredDispatchers() )

		# testing that deregistering a non-existent dispatcher is safe
		GafferDispatch.Dispatcher.deregisterDispatcher( "fake" )

	def testDispatcherSignals( self ) :

		preCs = GafferTest.CapturingSlot( GafferDispatch.Dispatcher.preDispatchSignal() )
		self.assertEqual( len( preCs ), 0 )
		dispatchCs = GafferTest.CapturingSlot( GafferDispatch.Dispatcher.dispatchSignal() )
		self.assertEqual( len( dispatchCs ), 0 )
		postCs = GafferTest.CapturingSlot( GafferDispatch.Dispatcher.postDispatchSignal() )
		self.assertEqual( len( postCs ), 0 )

		s = Gaffer.ScriptNode()
		s["n1"] = GafferDispatchTest.LoggingTaskNode()

		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )
		dispatcher.dispatch( [ s["n1"] ] )

		self.assertEqual( len( preCs ), 1 )
		self.assertTrue( preCs[0][0].isSame( dispatcher ) )
		self.assertEqual( preCs[0][1], [ s["n1"] ] )

		self.assertEqual( len( dispatchCs ), 1 )
		self.assertTrue( dispatchCs[0][0].isSame( dispatcher ) )
		self.assertEqual( dispatchCs[0][1], [ s["n1"] ] )

		self.assertEqual( len( postCs ), 1 )
		self.assertTrue( postCs[0][0].isSame( dispatcher ) )
		self.assertEqual( postCs[0][1], [ s["n1"] ] )

	def testCancelDispatch( self ) :

		def onlyRunOnce( dispatcher, nodes ) :

			if len( s["n1"].log ) :
				return True

			return False

		preConnection = GafferDispatch.Dispatcher.preDispatchSignal().connect( onlyRunOnce, scoped = True )
		connection = GafferTest.CapturingSlot( GafferDispatch.Dispatcher.dispatchSignal() )

		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )

		s = Gaffer.ScriptNode()
		s["n1"] = GafferDispatchTest.LoggingTaskNode()

		# never run
		self.assertEqual( len( s["n1"].log ), 0 )
		self.assertEqual( len( connection ), 0 )

		# runs the first time
		dispatcher.dispatch( [ s["n1"] ] )
		self.assertEqual( len( s["n1"].log ), 1 )
		self.assertEqual( len( connection ), 1 )

		# never runs again
		dispatcher.dispatch( [ s["n1"] ] )
		self.assertEqual( len( s["n1"].log ), 1 )
		self.assertEqual( len( connection ), 1 )

	def testCatchThrowingSlots( self ) :

		class BadSlot( list ) :

			def __init__( self, signal ) :

				self.__connection = signal.connect( Gaffer.WeakMethod( self.__slot ), scoped = True )

			def __slot( self, *args ) :

				self.append( args )
				raise RuntimeError( "bad slot!" )

		badConnection = BadSlot( GafferDispatch.Dispatcher.dispatchSignal() )
		cs = GafferTest.CapturingSlot( GafferDispatch.Dispatcher.dispatchSignal() )
		postCs = GafferTest.CapturingSlot( GafferDispatch.Dispatcher.postDispatchSignal() )

		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )

		s = Gaffer.ScriptNode()
		s["n1"] = GafferDispatchTest.LoggingTaskNode()

		# never run
		self.assertEqual( len( s["n1"].log ), 0 )
		self.assertEqual( len( badConnection ), 0 )
		self.assertEqual( len( cs ), 0 )
		self.assertEqual( len( postCs ), 0 )

		# runs even though the bad slot throws
		with IECore.CapturingMessageHandler() as mh :
			dispatcher.dispatch( [ s["n1"] ] )
		self.assertEqual( len( mh.messages ), 1 )
		self.assertRegex( mh.messages[0].message, "bad slot!" )
		self.assertEqual( len( badConnection ), 1 )
		self.assertEqual( len( s["n1"].log ), 1 )
		self.assertEqual( len( cs ), 1 )
		self.assertEqual( len( postCs ), 1 )

		# replace the bad slot with a connection to postDispatch
		badConnection = BadSlot( GafferDispatch.Dispatcher.postDispatchSignal() )

		# runs even though bad slot throws
		with IECore.CapturingMessageHandler() as mh :
			dispatcher.dispatch( [ s["n1"] ] )
		self.assertEqual( len( mh.messages ), 1 )
		self.assertRegex( mh.messages[0].message, "bad slot!" )
		self.assertEqual( len( badConnection ), 1 )
		self.assertEqual( len( s["n1"].log ), 2 )
		self.assertEqual( len( cs ), 2 )
		self.assertEqual( len( postCs ), 2 )

	def testPlugs( self ) :

		n = GafferDispatchTest.TextWriter()
		self.assertEqual( n['dispatcher'].getChild( 'testDispatcherPlug' ), None )

		GafferDispatch.Dispatcher.registerDispatcher( "testDispatcherWithCustomPlugs", DispatcherTest.TestDispatcher, setupPlugsFn = DispatcherTest.TestDispatcher._doSetupPlugs )

		n2 = GafferDispatchTest.TextWriter()
		self.assertTrue( isinstance( n2['dispatcher'].getChild( 'testDispatcherPlug' ), Gaffer.IntPlug ) )
		self.assertEqual( n2['dispatcher']['testDispatcherPlug'].direction(), Gaffer.Plug.Direction.In )

	def testDispatch( self ) :

		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )

		# Create a tree of dependencies for execution:
		# n1 requires:
		# - n2 requires:
		#    -n2a
		#    -n2b
		log = []
		s = Gaffer.ScriptNode()
		s["n1"] = GafferDispatchTest.LoggingTaskNode( log = log )
		s["n2"] = GafferDispatchTest.LoggingTaskNode( log = log )
		s["n2a"] = GafferDispatchTest.LoggingTaskNode( log = log )
		s["n2b"] = GafferDispatchTest.LoggingTaskNode( log = log )
		s["n1"]["preTasks"][0].setInput( s["n2"]["task"] )
		s["n2"]["preTasks"][0].setInput( s["n2a"]["task"] )
		s["n2"]["preTasks"][1].setInput( s["n2b"]["task"] )

		# Executing n1 should trigger execution of all of them
		dispatcher.dispatch( [ s["n1"] ] )
		self.assertTrue(
			[ l.node for l in log ] == [ s["n2a"], s["n2b"], s["n2"], s["n1"] ] or
			[ l.node for l in log ] == [ s["n2b"], s["n2a"], s["n2"], s["n1"] ]
		)

		# Executing n1 and anything else, should be the same as just n1
		del log[:]
		dispatcher.dispatch( [ s["n2b"], s["n1"] ] )
		self.assertTrue(
			[ l.node for l in log ] == [ s["n2a"], s["n2b"], s["n2"], s["n1"] ] or
			[ l.node for l in log ] == [ s["n2b"], s["n2a"], s["n2"], s["n1"] ]
		)

		# Executing all nodes should be the same as just n1
		del log[:]
		dispatcher.dispatch( [ s["n2"], s["n2b"], s["n1"], s["n2a"] ] )
		self.assertTrue(
			[ l.node for l in log ] == [ s["n2a"], s["n2b"], s["n2"], s["n1"] ] or
			[ l.node for l in log ] == [ s["n2b"], s["n2a"], s["n2"], s["n1"] ]
		)

		# Executing a sub-branch (n2) should only trigger execution in that branch
		del log[:]
		dispatcher.dispatch( [ s["n2"] ] )
		self.assertTrue(
			[ l.node for l in log ] == [ s["n2a"], s["n2b"], s["n2"] ] or
			[ l.node for l in log ] == [ s["n2b"], s["n2a"], s["n2"] ]
		)

		# Executing a leaf node, should not trigger other executions.
		del log[:]
		dispatcher.dispatch( [ s["n2b"] ] )
		self.assertEqual( [ l.node for l in log ], [ s["n2b"] ] )

	def testDispatchIdenticalTasks( self ) :

		# Create a tree of dependencies for execution:
		# n1 requires:
		# - n2 requires:
		#    -n2a
		#    -n2b

		log = []
		s = Gaffer.ScriptNode()
		s["n1"] = GafferDispatchTest.LoggingTaskNode( log = log )
		s["n2"] = GafferDispatchTest.LoggingTaskNode( log = log )
		s["n2a"] = GafferDispatchTest.LoggingTaskNode( log = log )
		s["n2b"] = GafferDispatchTest.LoggingTaskNode( log = log )
		s["n1"]["preTasks"][0].setInput( s["n2"]["task"] )
		s["n2"]["preTasks"][0].setInput( s["n2a"]["task"] )
		s["n2"]["preTasks"][1].setInput( s["n2b"]["task"] )

		# even though all tasks are identical, we still execute them all
		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )
		dispatcher.dispatch( [ s["n1"] ] )
		self.assertEqual( len( log ), 4 )
		self.assertEqual( [ l.node for l in log ], [ s["n2a"], s["n2b"], s["n2"], s["n1"] ] )

		# Executing them all should do the same, with no duplicates
		del log[:]
		dispatcher.dispatch( [ s["n2"], s["n2b"], s["n1"], s["n2a"] ] )
		self.assertEqual( len( log ), 4 )
		self.assertEqual( [ l.node for l in log ], [ s["n2a"], s["n2b"], s["n2"], s["n1"] ] )

	def testCyclesThrow( self ) :

		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )
		fileName = self.temporaryDirectory() + "/result.txt"

		s = Gaffer.ScriptNode()
		s["n1"] = GafferDispatchTest.TextWriter()
		s["n1"]["mode"].setValue( "a" )
		s["n1"]["fileName"].setValue( fileName )
		s["n1"]["text"].setValue( "a${frame};" )
		s["n2"] = GafferDispatchTest.TextWriter()
		s["n2"]["mode"].setValue( "a" )
		s["n2"]["fileName"].setValue( fileName )
		s["n2"]["text"].setValue( "b${frame};" )
		s["n3"] = GafferDispatchTest.TextWriter()
		s["n3"]["mode"].setValue( "a" )
		s["n3"]["fileName"].setValue( fileName )
		s["n3"]["text"].setValue( "c${frame};" )
		s["n4"] = GafferDispatchTest.TextWriter()
		s["n4"]["mode"].setValue( "a" )
		s["n4"]["fileName"].setValue( fileName )
		s["n4"]["text"].setValue( "d${frame};" )

		s["n4"]["preTasks"][0].setInput( s["n3"]["task"] )
		s["n3"]["preTasks"][0].setInput( s["n2"]["task"] )
		s["n2"]["preTasks"][0].setInput( s["n1"]["task"] )

		with IECore.CapturingMessageHandler() as mh :
			s["n1"]["preTasks"][0].setInput( s["n4"]["task"] )
		self.assertEqual( len( mh.messages ), 1 )
		self.assertRegex( mh.messages[0].message, "Cycle detected between ScriptNode.n1.preTasks.preTask0 and ScriptNode.n1.task" )

		self.assertNotEqual( s["n1"]["task"].hash(), s["n2"]["task"].hash() )
		self.assertNotEqual( s["n2"]["task"].hash(), s["n3"]["task"].hash() )
		self.assertNotEqual( s["n3"]["task"].hash(), s["n4"]["task"].hash() )
		self.assertNotEqual( s["n1"]["task"].hash(), s["n4"]["task"].hash() )

		self.assertEqual( os.path.isfile( fileName ), False )
		self.assertRaises( RuntimeError, dispatcher.dispatch, [ s["n4"] ] )
		self.assertEqual( os.path.isfile( fileName ), False )

	def testNotACycle( self ) :

		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )
		fileName = self.temporaryDirectory() + "/result.txt"

		s = Gaffer.ScriptNode()
		s["n1"] = GafferDispatchTest.TextWriter()
		s["n1"]["mode"].setValue( "a" )
		s["n1"]["fileName"].setValue( fileName )
		s["n1"]["text"].setValue( "a${frame};" )
		s["n2"] = GafferDispatchTest.TextWriter()
		s["n2"]["mode"].setValue( "a" )
		s["n2"]["fileName"].setValue( fileName )
		s["n2"]["text"].setValue( "b${frame};" )
		s["n3"] = GafferDispatchTest.TextWriter()
		s["n3"]["mode"].setValue( "a" )
		s["n3"]["fileName"].setValue( fileName )
		s["n3"]["text"].setValue( "c${frame};" )

		s["n3"]["preTasks"][0].setInput( s["n2"]["task"] )
		s["n3"]["preTasks"][1].setInput( s["n1"]["task"] )
		s["n2"]["preTasks"][0].setInput( s["n1"]["task"] )

		self.assertNotEqual( s["n1"]["task"].hash(), s["n2"]["task"].hash() )
		self.assertNotEqual( s["n2"]["task"].hash(), s["n3"]["task"].hash() )

		self.assertEqual( os.path.isfile( fileName ), False )
		dispatcher.dispatch( [ s["n3"] ] )
		self.assertEqual( os.path.isfile( fileName ), True )

		with open( fileName, "r" ) as f :
			text = f.read()

		self.assertEqual( text, "a1;b1;c1;" )

	def testNoTask( self ) :

		s = Gaffer.ScriptNode()
		s["n1"] = GafferDispatchTest.LoggingTaskNode()
		s["n1"]["noOp"].setValue( True )
		self.assertEqual( s["n1"]["task"].hash(), IECore.MurmurHash() )

		# It doesn't execute, because the executionHash is null
		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )
		dispatcher.dispatch( [ s["n1"] ] )
		self.assertEqual( s["n1"].log, [] )

	def testDispatchDifferentFrame( self ) :

		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )
		dispatcher["framesMode"].setValue( GafferDispatch.Dispatcher.FramesMode.CurrentFrame )

		s = Gaffer.ScriptNode()
		s["n1"] = GafferDispatchTest.LoggingTaskNode()

		context = Gaffer.Context( s.context() )
		context.setFrame( s.context().getFrame() + 10 )
		self.assertEqual( dispatcher.frameRange( s, context ), IECore.frameListFromList( [ int(context.getFrame()) ] ) )

		with context :
			dispatcher.dispatch( [ s["n1"] ] )

		self.assertEqual( len( s["n1"].log ), 1 )
		self.assertEqual( s["n1"].log[0].context.getFrame(), context.getFrame() )

	def testDispatchFullRange( self ) :

		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )
		dispatcher["framesMode"].setValue( GafferDispatch.Dispatcher.FramesMode.FullRange )

		s = Gaffer.ScriptNode()
		s["n1"] = GafferDispatchTest.LoggingTaskNode()
		s["n1"]["frame"] = Gaffer.StringPlug( defaultValue = "${frame}", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		dispatcher.dispatch( [ s["n1"] ] )

		frameRange = IECore.FrameRange( s["frameRange"]["start"].getValue(), s["frameRange"]["end"].getValue() )
		self.assertEqual( dispatcher.frameRange( s, s.context() ), frameRange )
		self.assertEqual( len( s["n1"].log ), len( frameRange.asList() ) )
		self.assertEqual( [ l.context.getFrame() for l in s["n1"].log ], frameRange.asList() )

	def testDispatchCustomRange( self ) :

		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )
		dispatcher["framesMode"].setValue( GafferDispatch.Dispatcher.FramesMode.CustomRange )
		frameList = IECore.FrameList.parse( "2-6x2" )
		dispatcher["frameRange"].setValue( str(frameList) )

		s = Gaffer.ScriptNode()
		s["n1"] = GafferDispatchTest.LoggingTaskNode()
		s["n1"]["frame"] = Gaffer.StringPlug( defaultValue = "${frame}", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		dispatcher.dispatch( [ s["n1"] ] )

		frames = frameList.asList()
		self.assertEqual( dispatcher.frameRange( s, s.context() ), frameList )
		self.assertEqual( len( s["n1"].log ), len( frames ) )
		self.assertEqual( [ l.context.getFrame() for l in s["n1"].log ], frames )

	def testDispatchBadCustomRange( self ) :

		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )
		dispatcher["framesMode"].setValue( GafferDispatch.Dispatcher.FramesMode.CustomRange )
		dispatcher["frameRange"].setValue( "notAFrameRange" )

		s = Gaffer.ScriptNode()
		s["n1"] = GafferDispatchTest.LoggingTaskNode()

		self.assertRaises( RuntimeError, dispatcher.dispatch, [ s["n1"] ] )
		self.assertRaises( RuntimeError, dispatcher.frameRange, s, s.context() )
		self.assertEqual( len( s["n1"].log ), 0 )

	def testDoesNotRequireSequenceExecution( self ) :

		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )
		dispatcher["framesMode"].setValue( GafferDispatch.Dispatcher.FramesMode.CustomRange )
		frameList = IECore.FrameList.parse( "2-6x2" )
		dispatcher["frameRange"].setValue( str(frameList) )
		fileName = self.temporaryDirectory() + "/result.txt"

		s = Gaffer.ScriptNode()
		s["n1"] = GafferDispatchTest.TextWriter()
		s["n1"]["mode"].setValue( "a" )
		s["n1"]["fileName"].setValue( fileName )
		s["n1"]["text"].setValue( "n1 on ${frame};" )
		s["n2"] = GafferDispatchTest.TextWriter()
		s["n2"]["mode"].setValue( "a" )
		s["n2"]["fileName"].setValue( fileName )
		s["n2"]["text"].setValue( "n2 on ${frame};" )
		s["n3"] = GafferDispatchTest.TextWriter()
		s["n3"]["mode"].setValue( "a" )
		s["n3"]["fileName"].setValue( fileName )
		s["n3"]["text"].setValue( "n3 on ${frame};" )
		s["n2"]["preTasks"][0].setInput( s["n1"]["task"] )
		s["n3"]["preTasks"][0].setInput( s["n2"]["task"] )

		self.assertEqual( os.path.isfile( fileName ), False )

		dispatcher.dispatch( [ s["n3"] ] )

		self.assertEqual( os.path.isfile( fileName ), True )

		with open( fileName, "r" ) as f :
			text = f.read()

		# all nodes on frame 1, followed by all nodes on frame 2, followed by all nodes on frame 3
		expectedText = "n1 on 2;n2 on 2;n3 on 2;n1 on 4;n2 on 4;n3 on 4;n1 on 6;n2 on 6;n3 on 6;"
		self.assertEqual( text, expectedText )

	def testRequiresSequenceExecution( self ) :

		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )
		dispatcher["framesMode"].setValue( GafferDispatch.Dispatcher.FramesMode.CustomRange )
		dispatcher["frameRange"].setValue( "2-6x2" )
		fileName = self.temporaryDirectory() + "/result.txt"

		s = Gaffer.ScriptNode()
		s["n1"] = GafferDispatchTest.TextWriter()
		s["n1"]["mode"].setValue( "a" )
		s["n1"]["fileName"].setValue( fileName )
		s["n1"]["text"].setValue( "n1 on ${frame};" )
		s["n2"] = GafferDispatchTest.TextWriter( requiresSequenceExecution = True )
		s["n2"]["mode"].setValue( "a" )
		s["n2"]["fileName"].setValue( fileName )
		s["n2"]["text"].setValue( "n2 on ${frame};" )
		s["n3"] = GafferDispatchTest.TextWriter()
		s["n3"]["mode"].setValue( "a" )
		s["n3"]["fileName"].setValue( fileName )
		s["n3"]["text"].setValue( "n3 on ${frame};" )
		s["n2"]["preTasks"][0].setInput( s["n1"]["task"] )
		s["n3"]["preTasks"][0].setInput( s["n2"]["task"] )

		self.assertEqual( os.path.isfile( fileName ), False )
		dispatcher.dispatch( [ s["n3"] ] )
		self.assertEqual( os.path.isfile( fileName ), True )
		with open( fileName, "r" ) as f :
			text = f.read()

		# n1 on all frames, followed by the n2 sequence, followed by n3 on all frames
		expectedText = "n1 on 2;n1 on 4;n1 on 6;n2 on 2;n2 on 4;n2 on 6;n3 on 2;n3 on 4;n3 on 6;"
		self.assertEqual( text, expectedText )

		# make sure n2 gets frames in sorted order
		dispatcher["frameRange"].setValue( "2,6,4" )
		os.remove( fileName )
		self.assertEqual( os.path.isfile( fileName ), False )
		dispatcher.dispatch( [ s["n3"] ] )
		self.assertEqual( os.path.isfile( fileName ), True )
		with open( fileName, "r" ) as f :
			text = f.read()

		# n1 in requested order, followed by the n2 sequence in sorted order, followed by n3 in the requested order
		expectedText = "n1 on 2;n1 on 6;n1 on 4;n2 on 2;n2 on 4;n2 on 6;n3 on 2;n3 on 6;n3 on 4;"
		self.assertEqual( text, expectedText )

	def testBatchSize( self ) :

		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )
		dispatcher["framesMode"].setValue( GafferDispatch.Dispatcher.FramesMode.CustomRange )
		dispatcher["frameRange"].setValue( "2-6x2" )
		fileName = self.temporaryDirectory() + "/result.txt"

		s = Gaffer.ScriptNode()
		s["n1"] = GafferDispatchTest.TextWriter()
		s["n1"]["mode"].setValue( "a" )
		s["n1"]["fileName"].setValue( fileName )
		s["n1"]["text"].setValue( "n1 on ${frame};" )
		s["n2"] = GafferDispatchTest.TextWriter()
		s["n2"]["mode"].setValue( "a" )
		s["n2"]["fileName"].setValue( fileName )
		s["n2"]["text"].setValue( "n2 on ${frame};" )
		s["n3"] = GafferDispatchTest.TextWriter( requiresSequenceExecution = True )
		s["n3"]["mode"].setValue( "a" )
		s["n3"]["fileName"].setValue( fileName )
		s["n3"]["text"].setValue( "n3 on ${frame};" )
		s["n4"] = GafferDispatchTest.TextWriter()
		s["n4"]["mode"].setValue( "a" )
		s["n4"]["fileName"].setValue( fileName )
		s["n4"]["text"].setValue( "n4 on ${frame};" )
		s["n3"]["preTasks"][0].setInput( s["n1"]["task"] )
		s["n3"]["preTasks"][1].setInput( s["n2"]["task"] )
		s["n4"]["preTasks"][0].setInput( s["n3"]["task"] )

		self.assertEqual( os.path.isfile( fileName ), False )
		dispatcher.dispatch( [ s["n4"] ] )
		self.assertEqual( os.path.isfile( fileName ), True )
		with open( fileName, "r" ) as f :
			text = f.read()

		# all frames of n1 and n2 interleaved, followed by the n3 sequence, followed by n4 on all frames
		expectedText = "n1 on 2;n2 on 2;n1 on 4;n2 on 4;n1 on 6;n2 on 6;n3 on 2;n3 on 4;n3 on 6;n4 on 2;n4 on 4;n4 on 6;"
		self.assertEqual( text, expectedText )

		# dispatch again with differnt batch sizes
		s["n1"]["dispatcher"]["batchSize"].setValue( 2 )
		s["n2"]["dispatcher"]["batchSize"].setValue( 5 )
		os.remove( fileName )
		self.assertEqual( os.path.isfile( fileName ), False )
		dispatcher.dispatch( [ s["n4"] ] )
		self.assertEqual( os.path.isfile( fileName ), True )
		with open( fileName, "r" ) as f :
			text = f.read()

		# first 2 frames of n1, followed by all frames of n2, followed by last frame of n1, followed by the n3 sequence, followed by n4 on all frames
		expectedText = "n1 on 2;n1 on 4;n2 on 2;n2 on 4;n2 on 6;n1 on 6;n3 on 2;n3 on 4;n3 on 6;n4 on 2;n4 on 4;n4 on 6;"
		self.assertEqual( text, expectedText )

	def testDispatchThroughSubgraphs( self ) :

		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )
		dispatcher["framesMode"].setValue( GafferDispatch.Dispatcher.FramesMode.CustomRange )
		dispatcher["frameRange"].setValue( "2-6x2" )
		fileName = self.temporaryDirectory() + "/result.txt"

		s = Gaffer.ScriptNode()
		s["n1"] = GafferDispatchTest.TextWriter()
		s["n1"]["mode"].setValue( "a" )
		s["n1"]["fileName"].setValue( fileName )
		s["n1"]["text"].setValue( "n1 on ${frame};" )
		s["b"] = Gaffer.Box()
		s["b"]["n2"] = GafferDispatchTest.TextWriter()
		s["b"]["n2"]["mode"].setValue( "a" )
		s["b"]["n2"]["fileName"].setValue( fileName )
		s["b"]["n2"]["text"].setValue( "n2 on ${frame};" )
		s["b"]["n3"] = GafferDispatchTest.TextWriter( requiresSequenceExecution = True )
		s["b"]["n3"]["mode"].setValue( "a" )
		s["b"]["n3"]["fileName"].setValue( fileName )
		s["b"]["n3"]["text"].setValue( "n3 on ${frame};" )
		s["n4"] = GafferDispatchTest.TextWriter()
		s["n4"]["mode"].setValue( "a" )
		s["n4"]["fileName"].setValue( fileName )
		s["n4"]["text"].setValue( "n4 on ${frame};" )
		promotedPreTaskPlug = Gaffer.PlugAlgo.promote( s["b"]["n3"]["preTasks"][0] )
		promotedPreTaskPlug.setInput( s["n1"]["task"] )
		s["b"]["n3"]["preTasks"][1].setInput( s["b"]["n2"]["task"] )
		promotedTaskPlug = Gaffer.PlugAlgo.promote( s["b"]["n3"]["task"] )
		s["n4"]["preTasks"][0].setInput( promotedTaskPlug )
		# export a reference too
		s["b"].exportForReference( self.temporaryDirectory() + "/test.grf" )
		s["r"] = Gaffer.Reference()
		s["r"].load( self.temporaryDirectory() + "/test.grf" )
		s["r"][promotedPreTaskPlug.getName()].setInput( s["n1"]["task"] )

		# dispatch a task that requires a Box

		self.assertEqual( os.path.isfile( fileName ), False )
		dispatcher.dispatch( [ s["n4"] ] )
		self.assertEqual( os.path.isfile( fileName ), True )
		with open( fileName, "r" ) as f :
			text = f.read()

		# all frames of n1 and n2 interleaved, followed by the n3 sequence, followed by n4 on all frames
		expectedText = "n1 on 2;n2 on 2;n1 on 4;n2 on 4;n1 on 6;n2 on 6;n3 on 2;n3 on 4;n3 on 6;n4 on 2;n4 on 4;n4 on 6;"
		self.assertEqual( text, expectedText )

		# dispatch the box directly

		os.remove( fileName )
		self.assertEqual( os.path.isfile( fileName ), False )
		dispatcher.dispatch( [ s["b"] ] )
		self.assertEqual( os.path.isfile( fileName ), True )
		with open( fileName, "r" ) as f :
			text = f.read()

		# all frames of n1 and n2 interleaved, followed by the n3 sequence
		expectedText = "n1 on 2;n2 on 2;n1 on 4;n2 on 4;n1 on 6;n2 on 6;n3 on 2;n3 on 4;n3 on 6;"
		self.assertEqual( text, expectedText )

		# only the promoted task dispatches

		s["b"]["n3"]["preTasks"][1].setInput( None )

		os.remove( fileName )
		self.assertEqual( os.path.isfile( fileName ), False )
		dispatcher.dispatch( [ s["b"] ] )
		self.assertEqual( os.path.isfile( fileName ), True )
		with open( fileName, "r" ) as f :
			text = f.read()

		# all frames of n1, followed by the n3 sequence
		expectedText = "n1 on 2;n1 on 4;n1 on 6;n3 on 2;n3 on 4;n3 on 6;"
		self.assertEqual( text, expectedText )

		# promoting a preTask doesn't dispatch unless it's connected

		s["b"]["out2"] = s["b"]["n2"]["task"].createCounterpart( "out2", Gaffer.Plug.Direction.Out )

		os.remove( fileName )
		self.assertEqual( os.path.isfile( fileName ), False )
		dispatcher.dispatch( [ s["b"] ] )
		self.assertEqual( os.path.isfile( fileName ), True )
		with open( fileName, "r" ) as f :
			text = f.read()

		# all frames of n1, followed by the n3 sequence
		expectedText = "n1 on 2;n1 on 4;n1 on 6;n3 on 2;n3 on 4;n3 on 6;"
		self.assertEqual( text, expectedText )

		# multiple promoted preTasks will dispatch

		s["b"]["out3"] = s["b"]["n2"]["task"].createCounterpart( "out3", Gaffer.Plug.Direction.Out )
		s["b"]["out3"].setInput( s["b"]["n2"]["task"] )

		os.remove( fileName )
		self.assertEqual( os.path.isfile( fileName ), False )
		dispatcher.dispatch( [ s["b"] ] )
		self.assertEqual( os.path.isfile( fileName ), True )
		with open( fileName, "r" ) as f :
			text = f.read()

		# all frames of n1, followed by the n3 sequence, followed by all frames of n2
		expectedText = "n1 on 2;n1 on 4;n1 on 6;n3 on 2;n3 on 4;n3 on 6;n2 on 2;n2 on 4;n2 on 6;"
		self.assertEqual( text, expectedText )

		# dispatch an task that requires a Reference

		os.remove( fileName )
		s["n4"]["preTasks"][0].setInput( s["r"][promotedTaskPlug.getName()] )
		self.assertEqual( os.path.isfile( fileName ), False )
		dispatcher.dispatch( [ s["n4"] ] )
		self.assertEqual( os.path.isfile( fileName ), True )
		with open( fileName, "r" ) as f :
			text = f.read()

		# all frames of n1, n2, n3, and n4 interleaved
		# note that n3 is now interleaved because TextWriter isn't serializing
		# the requiresSequenceExecution value, so s['r']['n3'] is now parallel.
		expectedText = "n1 on 2;n2 on 2;n3 on 2;n4 on 2;n1 on 4;n2 on 4;n3 on 4;n4 on 4;n1 on 6;n2 on 6;n3 on 6;n4 on 6;"
		self.assertEqual( text, expectedText )

		# dispatch the Reference directly

		os.remove( fileName )
		self.assertEqual( os.path.isfile( fileName ), False )
		dispatcher.dispatch( [ s["r"] ] )
		self.assertEqual( os.path.isfile( fileName ), True )
		with open( fileName, "r" ) as f :
			text = f.read()

		# all frames of n1, n2, and n3 interleaved
		# note that n3 is now interleaved because TextWriter isn't serializing
		# the requiresSequenceExecution value, so s['r']['n3'] is now parallel.
		expectedText = "n1 on 2;n2 on 2;n3 on 2;n1 on 4;n2 on 4;n3 on 4;n1 on 6;n2 on 6;n3 on 6;"
		self.assertEqual( text, expectedText )

	def testDefaultDispatcher( self ) :

		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )
		self.assertEqual( GafferDispatch.Dispatcher.getDefaultDispatcherType(), "" )
		GafferDispatch.Dispatcher.setDefaultDispatcherType( "testDispatcher" )
		self.assertEqual( GafferDispatch.Dispatcher.getDefaultDispatcherType(), "testDispatcher" )
		dispatcher2 = GafferDispatch.Dispatcher.create( GafferDispatch.Dispatcher.getDefaultDispatcherType() )
		self.assertTrue( isinstance( dispatcher2, DispatcherTest.TestDispatcher ) )
		self.assertFalse( dispatcher2.isSame( dispatcher ) )
		GafferDispatch.Dispatcher.setDefaultDispatcherType( "fakeDispatcher" )
		self.assertEqual( GafferDispatch.Dispatcher.getDefaultDispatcherType(), "fakeDispatcher" )
		self.assertEqual( GafferDispatch.Dispatcher.create( GafferDispatch.Dispatcher.getDefaultDispatcherType() ), None )

	def testFrameRangeOverride( self ) :

		class BinaryDispatcher( DispatcherTest.TestDispatcher ) :

			def frameRange( self, script, context ) :

				frameRange = GafferDispatch.Dispatcher.frameRange( self, script, context )

				if self["framesMode"].getValue() == GafferDispatch.Dispatcher.FramesMode.CurrentFrame :
					return frameRange

				return IECore.BinaryFrameList( frameRange )

		IECore.registerRunTimeTyped( BinaryDispatcher )

		dispatcher = BinaryDispatcher()
		dispatcher["jobsDirectory"].setValue( self.temporaryDirectory() )
		frameList = IECore.FrameList.parse( "1-10" )
		dispatcher["frameRange"].setValue( str(frameList) )

		s = Gaffer.ScriptNode()
		s["n1"] = GafferDispatchTest.LoggingTaskNode()
		s["n1"]["frame"] = Gaffer.StringPlug( defaultValue = "${frame}", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		dispatcher["framesMode"].setValue( GafferDispatch.Dispatcher.FramesMode.CurrentFrame )
		self.assertEqual( dispatcher.frameRange( s, s.context() ), IECore.frameListFromList( [ int(s.context().getFrame()) ] ) )

		dispatcher["framesMode"].setValue( GafferDispatch.Dispatcher.FramesMode.FullRange )
		self.assertEqual( dispatcher.frameRange( s, s.context() ), IECore.FrameList.parse( "1-100b" ) )

		dispatcher["framesMode"].setValue( GafferDispatch.Dispatcher.FramesMode.CustomRange )
		binaryFrames = IECore.FrameList.parse( "1-10b" )
		self.assertEqual( dispatcher.frameRange( s, s.context() ), binaryFrames )

		dispatcher.dispatch( [ s["n1"] ] )

		self.assertEqual( len( s["n1"].log ), len( frameList.asList() ) )
		self.assertEqual( [ l.context.getFrame() for l in s["n1"].log ], binaryFrames.asList() )

	def testPreTasksOverride( self ) :

		class SelfRequiringNode( GafferDispatch.TaskNode ) :

			def __init__( self ) :

				GafferDispatch.TaskNode.__init__( self )

				self.addChild( Gaffer.IntPlug( "multiplier", defaultValue = 1 ) )

				self.preExecutionCount = 0
				self.mainExecutionCount = 0

			def preTasks( self, context ) :

				if context.get( "selfExecutingNode:preExecute", None ) is None :

					customContext = Gaffer.Context( context )
					customContext["selfExecutingNode:preExecute"] = True
					preTasks = [ GafferDispatch.TaskNode.Task( self, customContext ) ]

				else :

					# We need to evaluate our external preTasks as well,
					# and they need to be preTasks of our preExecute task
					# only, since that is the topmost branch of our internal
					# task graph. We also need to use a Context which
					# does not contain our internal preExecute entry, incase
					# that has meaning for any of our external preTasks.
					customContext = Gaffer.Context( context )
					del customContext["selfExecutingNode:preExecute"]
					preTasks = GafferDispatch.TaskNode.preTasks( self, customContext )

				return preTasks

			def hash( self, context ) :

				h = GafferDispatch.TaskNode.hash( self, context )
				h.append( context.get( "selfExecutingNode:preExecute", False ) )
				h.append( self["multiplier"].hash() )
				return h

			def execute( self ) :

				if Gaffer.Context.current().get( "selfExecutingNode:preExecute", False ) :
					self.preExecutionCount += self["multiplier"].getValue()
				else :
					self.mainExecutionCount += self["multiplier"].getValue()

		IECore.registerRunTimeTyped( SelfRequiringNode )

		s = Gaffer.ScriptNode()
		s["e1"] = SelfRequiringNode()
		s["e2"] = SelfRequiringNode()
		s["e2"]["preTasks"][0].setInput( s["e1"]["task"] )

		c1 = s.context()
		c2 = Gaffer.Context( s.context() )
		c2["selfExecutingNode:preExecute"] = True

		# e2 requires itself with a different context
		with c1 :
			self.assertEqual( s["e2"]["task"].preTasks(), [ GafferDispatch.TaskNode.Task( s["e2"]["task"], c2 ) ] )
		# e2 in the other context requires its standard preTasks with the original context
		with c2 :
			self.assertEqual( s["e2"]["task"].preTasks(), [ GafferDispatch.TaskNode.Task( s["e2"]["preTasks"][0], c1 ), GafferDispatch.TaskNode.Task( s["e2"]["preTasks"][1], c1 ) ] )
		# e1 requires itself with a different context
		with c1 :
			self.assertEqual( s["e1"]["task"].preTasks(), [ GafferDispatch.TaskNode.Task( s["e1"]["task"], c2 ) ] )
		# e1 in the other context has the standard preTasks
		with c2 :
			self.assertEqual( s["e1"]["task"].preTasks(), [ GafferDispatch.TaskNode.Task( s["e1"]["preTasks"][0], c1 ) ] )

		self.assertEqual( s["e1"].preExecutionCount, 0 )
		self.assertEqual( s["e1"].mainExecutionCount, 0 )
		self.assertEqual( s["e2"].preExecutionCount, 0 )
		self.assertEqual( s["e2"].mainExecutionCount, 0 )

		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )

		dispatcher.dispatch( [ s["e1"] ] )
		self.assertEqual( s["e1"].preExecutionCount, 1 )
		self.assertEqual( s["e1"].mainExecutionCount, 1 )
		self.assertEqual( s["e2"].preExecutionCount, 0 )
		self.assertEqual( s["e2"].mainExecutionCount, 0 )

		dispatcher.dispatch( [ s["e2"] ] )
		self.assertEqual( s["e1"].preExecutionCount, 2 )
		self.assertEqual( s["e1"].mainExecutionCount, 2 )
		self.assertEqual( s["e2"].preExecutionCount, 1 )
		self.assertEqual( s["e2"].mainExecutionCount, 1 )

	def testContextChange( self ) :

		class ContextChangingTaskNode( GafferDispatch.TaskNode ) :

			def __init__( self, name = "ContextChangingTaskNode" ) :

				GafferDispatch.TaskNode.__init__( self, name )

			def preTasks( self, context ) :

				assert( context.isSame( Gaffer.Context.current() ) )

				upstreamContext = Gaffer.Context( context )
				upstreamContext["myText"] = "testing 123"
				upstreamContext.setFrame( 10 )

				result = []
				for plug in self["preTasks"] :
					result.append( self.Task( plug, upstreamContext ) )

				return result

			def hash( self, context ) :

				return IECore.MurmurHash()

			def execute( self ) :

				pass

		s = Gaffer.ScriptNode()

		s["w"] = GafferDispatchTest.TextWriter()
		s["w"]["fileName"].setValue( self.temporaryDirectory() + "/test.####.txt" )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( 'parent["w"]["text"] = context["myText"]' )

		s["c"] = ContextChangingTaskNode()
		s["c"]["preTasks"][0].setInput( s["w"]["task"] )

		GafferDispatch.Dispatcher.create( "testDispatcher" ).dispatch( [ s["c"] ] )

		self.assertEqual( next( open( self.temporaryDirectory() + "/test.0010.txt" ) ), "testing 123" )

	def testBatchesCanAccessJobDirectory( self ) :

		s = Gaffer.ScriptNode()

		s["w"] = GafferDispatchTest.TextWriter()
		s["w"]["fileName"].setValue( "${dispatcher:jobDirectory}/test.####.txt" )
		s["w"]["text"].setValue( "w on ${frame} from ${dispatcher:jobDirectory}" )

		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )
		dispatcher["framesMode"].setValue( GafferDispatch.Dispatcher.FramesMode.CustomRange )
		frameList = IECore.FrameList.parse( "2-6x2" )
		dispatcher["frameRange"].setValue( str(frameList) )
		dispatcher.dispatch( [ s["w"] ] )

		# a single dispatch should have the same job directory for all batches
		jobDir = dispatcher.jobDirectory()
		self.assertEqual( next( open( "%s/test.0002.txt" % jobDir ) ), "w on 2 from %s" % jobDir )
		self.assertEqual( next( open( "%s/test.0004.txt" % jobDir ) ), "w on 4 from %s" % jobDir )
		self.assertEqual( next( open( "%s/test.0006.txt" % jobDir ) ), "w on 6 from %s" % jobDir )

	def testNoOpDoesntBreakFrameParallelism( self ) :

		# perFrame1
		# |
		# contextVariables
		# |
		# perFrame2

		s = Gaffer.ScriptNode()

		log = []
		s["perFrame1"] = GafferDispatchTest.LoggingTaskNode( log = log )
		s["perFrame1"]["f"] = Gaffer.StringPlug( defaultValue = "perFrame1.####" )

		s["contextVariables"] = GafferDispatch.TaskContextVariables()
		s["contextVariables"]["preTasks"][0].setInput( s["perFrame1"]["task"] )

		s["perFrame2"] = GafferDispatchTest.LoggingTaskNode( log = log )
		s["perFrame2"]["f"] = Gaffer.StringPlug( defaultValue = "perFrame2.####" )
		s["perFrame2"]["preTasks"][0].setInput( s["contextVariables"]["task"] )

		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )
		dispatcher["framesMode"].setValue( dispatcher.FramesMode.CustomRange )
		dispatcher["frameRange"].setValue( "1-5" )
		dispatcher.dispatch( [ s["perFrame2"] ] )

		self.assertEqual( [ l.context.getFrame() for l in log ], [ 1, 1, 2, 2, 3, 3, 4, 4, 5, 5 ] )
		self.assertEqual( [ l.node for l in log ], [ s["perFrame1"], s["perFrame2"] ] * 5 )

	def testManyFrames( self ) :

		s = Gaffer.ScriptNode()

		s["t1"] = GafferDispatchTest.LoggingTaskNode()
		s["t1"]["f"] = Gaffer.StringPlug( defaultValue = "T1.####" )

		s["t2"] = GafferDispatchTest.LoggingTaskNode()
		s["t2"]["f"] = Gaffer.StringPlug( defaultValue = "T1.####" )

		s["t3"] = GafferDispatchTest.LoggingTaskNode()
		s["t3"]["f"] = Gaffer.StringPlug( defaultValue = "T1.####" )

		s["t2"]["preTasks"][0].setInput( s["t1"]["task"] )
		s["t3"]["preTasks"][0].setInput( s["t2"]["task"] )

		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )
		dispatcher["framesMode"].setValue( dispatcher.FramesMode.CustomRange )
		dispatcher["frameRange"].setValue( "1-10000" )
		dispatcher.dispatch( [ s["t3"] ] )

		self.assertEqual( len( s["t1"].log ), 10000 )
		self.assertEqual( len( s["t2"].log ), 10000 )
		self.assertEqual( len( s["t3"].log ), 10000 )

	def testDirectCyles( self ) :

		s = Gaffer.ScriptNode()
		s["t"] = GafferDispatchTest.LoggingTaskNode()

		with IECore.CapturingMessageHandler() as mh :
			s["t"]["preTasks"][0].setInput( s["t"]["task"] )
		self.assertEqual( len( mh.messages ), 1 )
		self.assertRegex( mh.messages[0].message, "Cycle detected between ScriptNode.t.preTasks.preTask0 and ScriptNode.t.task" )

		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )
		self.assertRaisesRegex( RuntimeError, "cannot have cyclic dependencies", dispatcher.dispatch, [ s["t"] ] )

	def testPostTasks( self ) :

		# t - p
		# |
		# e

		s = Gaffer.ScriptNode()

		log = []
		s["p"] = GafferDispatchTest.LoggingTaskNode( log = log )

		s["t"] = GafferDispatchTest.LoggingTaskNode( log = log )
		s["t"]["postTasks"][0].setInput( s["p"]["task"] )

		s["e"] = GafferDispatchTest.LoggingTaskNode( log = log )
		s["e"]["preTasks"][0].setInput( s["t"]["task"] )

		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )
		dispatcher.dispatch( [ s["e"] ] )

		self.assertEqual( [ l.node for l in log ], [ s["t"], s["p"], s["e"] ] )

	def testSerialPostTasks( self ) :

		# t1 - p1
		# |
		# t2 - p2

		s = Gaffer.ScriptNode()

		log = []
		s["p1"] = GafferDispatchTest.LoggingTaskNode( log = log )
		s["p2"] = GafferDispatchTest.LoggingTaskNode( log = log )
		s["t1"] = GafferDispatchTest.LoggingTaskNode( log = log )
		s["t2"] = GafferDispatchTest.LoggingTaskNode( log = log )

		s["t1"]["postTasks"][0].setInput( s["p1"]["task"] )
		s["t2"]["postTasks"][0].setInput( s["p2"]["task"] )
		s["t2"]["preTasks"][0].setInput( s["t1"]["task"] )

		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )
		dispatcher.dispatch( [ s["t2"] ] )

		self.assertEqual( [ l.node for l in log ], [ s["t1"], s["p1"], s["t2"], s["p2"] ] )

	def testStaticPostTask( self ) :

		s = Gaffer.ScriptNode()

		s["p"] = GafferDispatchTest.LoggingTaskNode()

		s["t"] = GafferDispatchTest.LoggingTaskNode()
		s["t"]["f"] = Gaffer.StringPlug( defaultValue = "####" )
		s["t"]["postTasks"][0].setInput( s["p"]["task"] )

		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )
		dispatcher["framesMode"].setValue( dispatcher.FramesMode.CustomRange )
		dispatcher["frameRange"].setValue( "1-10" )

		dispatcher.dispatch( [ s["t"] ] )
		self.assertEqual( len( s["t"].log ), 10 )
		self.assertEqual( len( s["p"].log ), 1  )

	def testPostTaskWithPreTasks( self ) :

		#     u
		#     |
		# e - p

		s = Gaffer.ScriptNode()

		log = []
		s["u"] = GafferDispatchTest.LoggingTaskNode( log = log )
		s["p"] = GafferDispatchTest.LoggingTaskNode( log = log )
		s["p"]["preTasks"][0].setInput( s["u"]["task"] )
		s["e"] = GafferDispatchTest.LoggingTaskNode( log = log )
		s["e"]["postTasks"][0].setInput( s["p"]["task"] )

		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )
		dispatcher.dispatch( [ s["e"] ] )

		self.assertEqual( [ l.node for l in log ], [ s["e"], s["u"], s["p"] ] )

	def testPostTaskWithDownstreamTasks( self ) :

		# e - p
		#     |
		#     d

		s = Gaffer.ScriptNode()

		log = []
		s["p"] = GafferDispatchTest.LoggingTaskNode( log = log )
		s["e"] = GafferDispatchTest.LoggingTaskNode( log = log )
		s["e"]["postTasks"][0].setInput( s["p"]["task"] )
		s["d"] = GafferDispatchTest.LoggingTaskNode( log = log )
		s["d"]["preTasks"][0].setInput( s["p"]["task"] )

		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )

		# Dispatching e should cause p to execute as a post task, but
		# tasks downstream of p should be ignored.
		dispatcher.dispatch( [ s["e"] ] )
		self.assertEqual( [ l.node for l in log ], [ s["e"], s["p"] ] )

		# Dispatching d should cause p to be executed as a pre task,
		# but that should not cause e to execute.
		del log[:]
		dispatcher.dispatch( [ s["d"] ] )
		self.assertEqual( [ l.node for l in log ], [ s["p"], s["d"] ] )

	def testPostTaskCycles( self ) :

		s = Gaffer.ScriptNode()

		s["t1"] = GafferDispatchTest.LoggingTaskNode()
		s["t2"] = GafferDispatchTest.LoggingTaskNode()

		s["t2"]["preTasks"][0].setInput( s["t1"]["task"] )
		s["t2"]["postTasks"][0].setInput( s["t1"]["task"] )

		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )
		self.assertRaisesRegex( RuntimeError, "cannot have cyclic dependencies", dispatcher.dispatch, [ s["t2"] ] )

	def testImmediateDispatch( self ) :

		# nonImmediate1
		# |
		# immediate
		# |
		# nonImmediate2

		s = Gaffer.ScriptNode()

		log = []
		s["nonImmediate1"] = GafferDispatchTest.LoggingTaskNode( log = log )
		s["immediate"] = GafferDispatchTest.LoggingTaskNode( log = log )
		s["immediate"]["preTasks"][0].setInput( s["nonImmediate1"]["task"] )
		s["immediate"]["dispatcher"]["immediate"].setValue( True )
		s["nonImmediate2"] = GafferDispatchTest.LoggingTaskNode( log = log )
		s["nonImmediate2"]["preTasks"][0].setInput( s["immediate"]["task"] )

		dispatcher = self.NullDispatcher()
		dispatcher["jobsDirectory"].setValue( self.temporaryDirectory() )
		dispatcher.dispatch( [ s["nonImmediate2"] ] )

		self.assertEqual( [ l.node for l in log ], [ s["nonImmediate1"], s["immediate" ] ] )

	def testImmediateDispatchWithSharedBatches( self ) :

		#   n1
		#  / \
		# i1 12
		#  \ /
		#   n2

		s = Gaffer.ScriptNode()

		log = []
		s["n1"] = GafferDispatchTest.LoggingTaskNode( log = log )
		s["i1"] = GafferDispatchTest.LoggingTaskNode( log = log )
		s["i1"]["preTasks"][0].setInput( s["n1"]["task"] )
		s["i1"]["dispatcher"]["immediate"].setValue( True )
		s["i2"] = GafferDispatchTest.LoggingTaskNode( log = log )
		s["i2"]["preTasks"][0].setInput( s["n1"]["task"] )
		s["i2"]["dispatcher"]["immediate"].setValue( True )
		s["n2"] = GafferDispatchTest.LoggingTaskNode( log = log )
		s["n2"]["preTasks"][0].setInput( s["i1"]["task"] )
		s["n2"]["preTasks"][1].setInput( s["i2"]["task"] )

		# NullDispatcher dispatch should only execute the immediate nodes.
		dispatcher = self.NullDispatcher()
		dispatcher["jobsDirectory"].setValue( self.temporaryDirectory() )
		dispatcher.dispatch( [ s["n2"] ] )
		self.assertEqual( [ l.node for l in log ], [ s["n1"], s["i1" ], s["i2"] ] )

		# And a more usual dispatch shouldn't double up dispatch on anything.
		del log[:]
		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )
		dispatcher.dispatch( [ s["n2"] ] )
		self.assertEqual( [ l.node for l in log ], [ s["n1"], s["i1"], s["i2"], s["n2"] ] )

	def testImmediateDispatchWithSplitSharedBatches( self ) :

		#   n1
		#  / \
		# i1 n2
		#  \ /
		#   n3

		s = Gaffer.ScriptNode()

		log = []
		s["n1"] = GafferDispatchTest.LoggingTaskNode( log = log )
		s["i1"] = GafferDispatchTest.LoggingTaskNode( log = log )
		s["i1"]["preTasks"][0].setInput( s["n1"]["task"] )
		s["i1"]["dispatcher"]["immediate"].setValue( True )
		s["n2"] = GafferDispatchTest.LoggingTaskNode( log = log )
		s["n2"]["preTasks"][0].setInput( s["n1"]["task"] )
		s["n3"] = GafferDispatchTest.LoggingTaskNode( log = log )
		s["n3"]["preTasks"][0].setInput( s["i1"]["task"] )
		s["n3"]["preTasks"][1].setInput( s["n2"]["task"] )

		# NullDispatcher dispatch should only execute the immediate nodes.
		dispatcher = self.NullDispatcher()
		dispatcher["jobsDirectory"].setValue( self.temporaryDirectory() )
		dispatcher.dispatch( [ s["n3"] ] )
		self.assertEqual( [ l.node for l in log ], [ s["n1"], s["i1" ] ] )

		# And a more usual dispatch shouldn't double up dispatch on anything.
		del log[:]
		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )
		dispatcher.dispatch( [ s["n3"] ] )
		self.assertEqual( [ l.node for l in log ], [ s["n1"], s["i1"], s["n2"], s["n3"] ] )

	def testDispatchIterable( self ) :

		s = Gaffer.ScriptNode()

		log = []
		s["n1"] = GafferDispatchTest.LoggingTaskNode( log = log )
		s["n2"] = GafferDispatchTest.LoggingTaskNode( log = log )

		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )
		dispatcher.dispatch( itertools.chain( [ s["n1"], s["n2"] ] ) )
		self.assertEqual( [ l.node for l in log ], [ s["n1"], s["n2"] ] )

	def testFrameOrderWithPostTask( self ) :

		# t - p

		s = Gaffer.ScriptNode()

		log = []
		s["p"] = GafferDispatchTest.LoggingTaskNode( log = log )
		s["p"]["f"] = Gaffer.StringPlug( defaultValue = "####" )

		s["t"] = GafferDispatchTest.LoggingTaskNode( log = log )
		s["t"]["postTasks"][0].setInput( s["p"]["task"] )
		s["t"]["f"] = Gaffer.StringPlug( defaultValue = "####" )

		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )
		dispatcher["framesMode"].setValue( GafferDispatch.Dispatcher.FramesMode.CustomRange )
		dispatcher["frameRange"].setValue( "1-4" )

		dispatcher.dispatch( [ s["t"] ] )

		self.assertEqual( [ l.node for l in log ], [ s["t"], s["p"], ] * 4 )
		self.assertEqual( [ l.context.getFrame() for l in log ], [ 1, 1, 2, 2, 3, 3, 4, 4 ] )

	def testFrameOrderWithStaticPostTask( self ) :

		# t - p

		s = Gaffer.ScriptNode()

		log = []
		s["p"] = GafferDispatchTest.LoggingTaskNode( log = log )

		s["t"] = GafferDispatchTest.LoggingTaskNode( log = log )
		s["t"]["postTasks"][0].setInput( s["p"]["task"] )
		s["t"]["f"] = Gaffer.StringPlug( defaultValue = "####" )

		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )
		dispatcher["framesMode"].setValue( GafferDispatch.Dispatcher.FramesMode.CustomRange )
		dispatcher["frameRange"].setValue( "1-4" )

		dispatcher.dispatch( [ s["t"] ] )

		self.assertEqual( [ l.node for l in log ], [ s["t"], s["t"], s["t"], s["t"], s["p"] ] )
		self.assertEqual( [ l.context.getFrame() for l in log ], [ 1, 2, 3, 4, 1 ] )

	def testFrameOrderWithSequencePostTask( self ) :

		# t - p

		s = Gaffer.ScriptNode()

		log = []
		s["p"] = GafferDispatchTest.LoggingTaskNode( log = log )
		s["p"]["f"] = Gaffer.StringPlug( defaultValue = "####" )
		s["p"]["requiresSequenceExecution"].setValue( True )

		s["t"] = GafferDispatchTest.LoggingTaskNode( log = log )
		s["t"]["postTasks"][0].setInput( s["p"]["task"] )
		s["t"]["f"] = Gaffer.StringPlug( defaultValue = "####" )

		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )
		dispatcher["framesMode"].setValue( GafferDispatch.Dispatcher.FramesMode.CustomRange )
		dispatcher["frameRange"].setValue( "1-4" )

		dispatcher.dispatch( [ s["t"] ] )

		self.assertEqual( [ l.node for l in log ], [ s["t"], s["t"], s["t"], s["t"], s["p"], ] )
		self.assertEqual( [ l.context.get( "frame", None ) for l in log ], [ 1, 2, 3, 4, None ] )
		self.assertEqual( [ l.frames for l in log ], [ None, None, None, None, [ 1, 2, 3, 4 ] ] )

	def testScaling( self ) :

		# A series of interleaved per-frame and per-sequence
		# tasks like this :
		#
		#    perFrameA
		#      |
		#    perSequenceA
		#      |
		#    perFrameB
		#      |
		#    perSequenceB
		#      |
		#    ...
		#
		# Leads to a batch graph like this :
		#
		#    pfA1 pfA2 pfA3
		#      \   |   /
		#       \  |  /
		#        \ | /
		#      sequenceA
		#        / | \
		#       /  |  \
		#      /   |   \
		#    pfB1 pfB2 pfB3
		#      \   |   /
		#       \  |  /
		#        \ | /
		#      sequenceB
		#        / | \
		#    ...
		#
		# This fan-out/gather pattern generates a DAG with
		# a huge number of unique paths, exposing any errors
		# in the Dispatcher's pruning of previsited batches
		# by utterly destroying performance.

		s = Gaffer.ScriptNode()

		lastTask = None
		for i in range( 0, 5 ) :

			perFrame = GafferDispatch.PythonCommand()
			perFrame["command"].setValue( "context.getFrame()" )
			s["perFrame%d" % i] = perFrame

			if lastTask is not None :
				perFrame["preTasks"][0].setInput( lastTask["task"] )

			perSequence = GafferDispatch.PythonCommand()
			perSequence["command"].setValue( "pass" )
			perSequence["sequence"].setValue( True )
			perSequence["preTasks"][0].setInput( perFrame["task"] )
			s["perSequence%d" % i] = perSequence

			lastTask = perSequence

		d = self.TestDispatcher()
		d["jobsDirectory"].setValue( self.temporaryDirectory() )
		d["framesMode"].setValue( d.FramesMode.CustomRange )
		d["frameRange"].setValue( "1-1000" )

		t = time.process_time()
		d.dispatch( [ lastTask ] )

		timeLimit = 4
		if Gaffer.isDebug():
			timeLimit *= 2

		self.assertLess( time.process_time() - t, timeLimit )

	def testTaskListWaitForSequence( self ) :

		s = Gaffer.ScriptNode()

		log = []
		s["a"] = GafferDispatchTest.LoggingTaskNode( log = log )
		s["a"]["f"] = Gaffer.StringPlug( defaultValue = "####" )

		s["t"] = GafferDispatch.TaskList()
		s["t"]["preTasks"][0].setInput( s["a"]["task"] )

		s["b"] = GafferDispatchTest.LoggingTaskNode( log = log )
		s["b"]["preTasks"][0].setInput( s["t"]["task"] )
		s["b"]["f"] = Gaffer.StringPlug( defaultValue = "####" )

		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )
		dispatcher["framesMode"].setValue( GafferDispatch.Dispatcher.FramesMode.CustomRange )
		dispatcher["frameRange"].setValue( "1-4" )

		dispatcher.dispatch( [ s["b"] ] )

		self.assertEqual( [ l.node.getName() for l in log ], [ "a", "b" ] * 4 )
		self.assertEqual( [ l.context.getFrame() for l in log ], [ 1, 1, 2, 2, 3, 3, 4, 4 ] )

		del log[:]
		s["t"]["sequence"].setValue( True )
		dispatcher.dispatch( [ s["b"] ] )

		self.assertEqual( [ l.node.getName() for l in log ], [ "a" ] * 4 + [ "b" ] * 4 )
		self.assertEqual( [ l.context.getFrame() for l in log ], [ 1, 2, 3, 4 ] * 2 )

	def testTaskListBatchSize( self ) :

		# a  per-frame task
		# |
		# t  no-op (we'll modify the batch size on this)
		# |
		# b  per-frame task

		s = Gaffer.ScriptNode()

		log = []
		s["a"] = GafferDispatchTest.LoggingTaskNode( log = log )
		s["a"]["f"] = Gaffer.StringPlug( defaultValue = "####" )

		s["t"] = GafferDispatch.TaskList()
		s["t"]["preTasks"][0].setInput( s["a"]["task"] )

		s["b"] = GafferDispatchTest.LoggingTaskNode( log = log )
		s["b"]["preTasks"][0].setInput( s["t"]["task"] )
		s["b"]["f"] = Gaffer.StringPlug( defaultValue = "####" )

		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )
		dispatcher["framesMode"].setValue( GafferDispatch.Dispatcher.FramesMode.CustomRange )
		dispatcher["frameRange"].setValue( "1-4" )

		dispatcher.dispatch( [ s["b"] ] )

		self.assertEqual( [ l.node.getName() for l in log ], [ "a", "b" ] * 4 )
		self.assertEqual( [ l.context.getFrame() for l in log ], [ 1, 1, 2, 2, 3, 3, 4, 4 ] )

		del log[:]
		s["t"]["dispatcher"]["batchSize"].setValue( 2 )
		dispatcher.dispatch( [ s["b"] ] )

		self.assertEqual( [ l.node.getName() for l in log ], [ "a", "a", "b", "b" ] * 2 )
		self.assertEqual( [ l.context.getFrame() for l in log ], [ 1, 2, 1, 2, 3, 4, 3, 4 ] )

	def testTaskListWedging( self ) :

		s = Gaffer.ScriptNode()

		# a  per-wedge-per-frame task
		# |
		# t  no-op
		# |
		# b  per-wedge task (not dependent on frame)
		# |
		# w  wedge over ( "X", "Y" )

		log = []
		s["a"] = GafferDispatchTest.LoggingTaskNode( log = log )
		s["a"]["f"] = Gaffer.StringPlug( defaultValue = "${wedge:value}.####" )

		s["t"] = GafferDispatch.TaskList()
		s["t"]["preTasks"][0].setInput( s["a"]["task"] )

		s["b"] = GafferDispatchTest.LoggingTaskNode( log = log )
		s["b"]["preTasks"][0].setInput( s["t"]["task"] )
		s["b"]["w"] = Gaffer.StringPlug( defaultValue = "${wedge:value}" )

		s["w"] = GafferDispatch.Wedge()
		s["w"]["preTasks"][0].setInput( s["b"]["task"] )
		s["w"]["mode"].setValue( int( GafferDispatch.Wedge.Mode.StringList ) )
		s["w"]["strings"].setValue( IECore.StringVectorData( [ "X", "Y" ] ) )

		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )
		dispatcher["framesMode"].setValue( GafferDispatch.Dispatcher.FramesMode.CustomRange )
		dispatcher["frameRange"].setValue( "1-3" )

		dispatcher.dispatch( [ s["w"] ] )
		self.assertEqual( [ l.node.getName() for l in log ], [ "a", "a", "a", "b" ] * 2 )
		self.assertEqual( [ l.context.getFrame() for l in log ], [ 1, 2, 3, 1 ] * 2 )
		self.assertEqual( [ l.context["wedge:value"] for l in log ], [ "X", "X", "X", "X", "Y", "Y", "Y", "Y" ] )

	def testCreateMatching( self ) :

		self.assertEqual( GafferDispatch.Dispatcher.registeredDispatchers(), tuple([ "Debug", "Local", "testDispatcher" ]) )

		# match all
		dispatchers = GafferDispatch.Dispatcher.createMatching( "*" )
		self.assertEqual( len(dispatchers), 3 )
		self.assertTrue( isinstance( dispatchers[0], GafferDispatchTest.DebugDispatcher ) )
		self.assertTrue( isinstance( dispatchers[1], GafferDispatch.LocalDispatcher ) )
		self.assertTrue( isinstance( dispatchers[2], DispatcherTest.TestDispatcher ) )

		# match specific
		dispatchers = GafferDispatch.Dispatcher.createMatching( "Local" )
		self.assertEqual( len(dispatchers), 1 )
		self.assertTrue( isinstance( dispatchers[0], GafferDispatch.LocalDispatcher ) )

		# match specific with wildcards
		dispatchers = GafferDispatch.Dispatcher.createMatching( "test*" )
		self.assertEqual( len(dispatchers), 1 )
		self.assertTrue( isinstance( dispatchers[0], DispatcherTest.TestDispatcher ) )

		# match several by wildcard
		dispatchers = GafferDispatch.Dispatcher.createMatching( "*e*" )
		self.assertEqual( len(dispatchers), 2 )
		self.assertTrue( isinstance( dispatchers[0], GafferDispatchTest.DebugDispatcher ) )
		self.assertTrue( isinstance( dispatchers[1], DispatcherTest.TestDispatcher ) )

		# match seveal exactly
		dispatchers = GafferDispatch.Dispatcher.createMatching( "Debug Local" )
		self.assertEqual( len(dispatchers), 2 )
		self.assertTrue( isinstance( dispatchers[0], GafferDispatchTest.DebugDispatcher ) )
		self.assertTrue( isinstance( dispatchers[1], GafferDispatch.LocalDispatcher ) )

	def testBatchContextsAreIdentical( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferDispatch.SystemCommand()
		s["n"]["command"].setValue( "echo #" )

		dispatcher = self.NullDispatcher()
		dispatcher["jobsDirectory"].setValue( self.temporaryDirectory() )
		dispatcher["framesMode"].setValue( dispatcher.FramesMode.CustomRange )
		dispatcher["frameRange"].setValue( "1-10" )
		dispatcher.dispatch( [ s["n"] ] )

		batches = dispatcher.lastDispatch.preTasks()
		self.assertEqual( len( batches ), 10 )

		for i, batch in enumerate( batches ) :
			self.assertEqual( batch.plug(), s["n"]["task"] )
			self.assertEqual( batch.frames(), [ i + 1 ] )
			self.assertNotIn( "frame", batch.context() )
			self.assertEqual( batch.context(), batches[0].context() )

	def testNullScriptInFrameRangeCall( self ) :

		d = self.NullDispatcher()
		d["framesMode"].setValue( d.FramesMode.FullRange )
		with self.assertRaisesRegex( Exception, "Python argument types in" ) :
			d.frameRange( None, Gaffer.Context() )

	def testNullContextInFrameRangeCall( self ) :

		d = self.NullDispatcher()
		d["framesMode"].setValue( d.FramesMode.CurrentFrame )
		with self.assertRaisesRegex( Exception, "Python argument types in" ) :
			d.frameRange( Gaffer.ScriptNode(), None )

	def testSwitch( self ) :

		s = Gaffer.ScriptNode()

		s["n1"] = GafferDispatchTest.LoggingTaskNode()
		s["n2"] = GafferDispatchTest.LoggingTaskNode()

		s["switch"] = Gaffer.Switch()
		s["switch"].setup( s["n1"]["task"] )
		s["switch"]["in"][0].setInput( s["n1"]["task"] )
		s["switch"]["in"][1].setInput( s["n2"]["task"] )

		s["n3"] = GafferDispatchTest.LoggingTaskNode()
		s["n3"]["preTasks"][0].setInput( s["switch"]["out"] )

		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )

		s["switch"]["index"].setValue( 1 )
		dispatcher.dispatch( [ s["n3"] ] )

		self.assertEqual( len( s["n1"].log ), 0 )
		self.assertEqual( len( s["n2"].log ), 1 )
		self.assertEqual( len( s["n3"].log ), 1 )

		s["switch"]["index"].setValue( 0 )
		dispatcher.dispatch( [ s["n3"] ] )

		self.assertEqual( len( s["n1"].log ), 1 )
		self.assertEqual( len( s["n2"].log ), 1 )
		self.assertEqual( len( s["n3"].log ), 2 )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( "parent['switch']['index'] = context.getFrame()" )

		with Gaffer.Context() as c :

			c.setFrame( 0 )
			dispatcher.dispatch( [ s["n3"] ] )

			self.assertEqual( len( s["n1"].log ), 2 )
			self.assertEqual( len( s["n2"].log ), 1 )
			self.assertEqual( len( s["n3"].log ), 3 )

			c.setFrame( 1 )
			dispatcher.dispatch( [ s["n3"] ] )

			self.assertEqual( len( s["n1"].log ), 2 )
			self.assertEqual( len( s["n2"].log ), 2 )
			self.assertEqual( len( s["n3"].log ), 4 )

			c.setFrame( 0 )
			s["switch"]["in"][0].setInput( None )
			dispatcher.dispatch( [ s["n3"] ] )

			self.assertEqual( len( s["n1"].log ), 2 )
			self.assertEqual( len( s["n2"].log ), 2 )
			self.assertEqual( len( s["n3"].log ), 5 )

	def testNameSwitch( self ) :

		s = Gaffer.ScriptNode()

		s["n1"] = GafferDispatchTest.LoggingTaskNode()
		s["n2"] = GafferDispatchTest.LoggingTaskNode()

		s["switch"] = Gaffer.NameSwitch()
		s["switch"].setup( s["n1"]["task"] )
		s["switch"]["in"][0]["value"].setInput( s["n1"]["task"] )
		s["switch"]["in"][1]["value"].setInput( s["n2"]["task"] )
		s["switch"]["in"][1]["name"].setValue( "n2" )

		s["n3"] = GafferDispatchTest.LoggingTaskNode()
		s["n3"]["preTasks"][0].setInput( s["switch"]["out"]["value"] )

		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )

		s["switch"]["selector"].setValue( "n2" )
		dispatcher.dispatch( [ s["n3"] ] )

		self.assertEqual( len( s["n1"].log ), 0 )
		self.assertEqual( len( s["n2"].log ), 1 )
		self.assertEqual( len( s["n3"].log ), 1 )

		s["switch"]["selector"].setValue( "n1" )
		dispatcher.dispatch( [ s["n3"] ] )

		self.assertEqual( len( s["n1"].log ), 1 )
		self.assertEqual( len( s["n2"].log ), 1 )
		self.assertEqual( len( s["n3"].log ), 2 )

	def testTwoNameSwitches( self ) :

		s = Gaffer.ScriptNode()

		s["n1"] = GafferDispatchTest.LoggingTaskNode()
		s["n2"] = GafferDispatchTest.LoggingTaskNode()
		s["n3"] = GafferDispatchTest.LoggingTaskNode()

		s["switch1"] = Gaffer.NameSwitch()
		s["switch1"].setup( s["n1"]["task"] )
		s["switch1"]["in"][0]["value"].setInput( s["n1"]["task"] )
		s["switch1"]["in"][1]["value"].setInput( s["n2"]["task"] )
		s["switch1"]["in"][1]["name"].setValue( "n2" )

		s["switch2"] = Gaffer.NameSwitch()
		s["switch2"].setup( s["n1"]["task"] )
		s["switch2"]["in"][0]["value"].setInput( s["switch1"]["out"]["value"] )
		s["switch2"]["in"][1]["value"].setInput( s["n3"]["task"] )
		s["switch2"]["in"][1]["name"].setValue( "n3" )

		s["n4"] = GafferDispatchTest.LoggingTaskNode()
		s["n4"]["preTasks"][0].setInput( s["switch2"]["out"]["value"] )

		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )

		s["switch1"]["selector"].setValue( "n2" )

		dispatcher.dispatch( [ s["n4"] ] )

		self.assertEqual( len( s["n1"].log ), 0 )
		self.assertEqual( len( s["n2"].log ), 1 )
		self.assertEqual( len( s["n3"].log ), 0 )
		self.assertEqual( len( s["n4"].log ), 1 )

	def testContextProcessor( self ) :

		s = Gaffer.ScriptNode()

		s["n1"] = GafferDispatchTest.LoggingTaskNode()

		s["cv"] = Gaffer.ContextVariables()
		s["cv"].setup( s["n1"]["task"] )
		s["cv"]["in"].setInput( s["n1"]["task"] )
		s["cv"]["variables"].addChild( Gaffer.NameValuePlug( "test", 10 ) )

		s["n2"] = GafferDispatchTest.LoggingTaskNode()
		s["n2"]["preTasks"][0].setInput( s["cv"]["out"] )

		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )
		dispatcher.dispatch( [ s["n2"] ] )

		self.assertEqual( len( s["n1"].log ), 1 )
		self.assertEqual( len( s["n2"].log ), 1 )

		self.assertNotIn( "test", s["n2"].log[0].context )
		self.assertIn( "test", s["n1"].log[0].context )
		self.assertEqual( s["n1"].log[0].context["test"], 10 )

	def testTwoContextProcessors( self ) :

		s = Gaffer.ScriptNode()

		s["n1"] = GafferDispatchTest.LoggingTaskNode()

		s["cv1"] = Gaffer.ContextVariables()
		s["cv1"].setup( s["n1"]["task"] )
		s["cv1"]["in"].setInput( s["n1"]["task"] )
		s["cv1"]["variables"].addChild( Gaffer.NameValuePlug( "test1", 10 ) )

		s["cv2"] = Gaffer.ContextVariables()
		s["cv2"].setup( s["n1"]["task"] )
		s["cv2"]["in"].setInput( s["cv1"]["out"] )
		s["cv2"]["variables"].addChild( Gaffer.NameValuePlug( "test2", 20 ) )

		s["n2"] = GafferDispatchTest.LoggingTaskNode()
		s["n2"]["preTasks"][0].setInput( s["cv2"]["out"] )

		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )
		dispatcher.dispatch( [ s["n2"] ] )

		self.assertEqual( len( s["n1"].log ), 1 )
		self.assertEqual( len( s["n2"].log ), 1 )

		self.assertNotIn( "test1", s["n2"].log[0].context )
		self.assertNotIn( "test2", s["n2"].log[0].context )
		self.assertIn( "test1", s["n1"].log[0].context )
		self.assertIn( "test2", s["n1"].log[0].context )
		self.assertEqual( s["n1"].log[0].context["test1"], 10 )
		self.assertEqual( s["n1"].log[0].context["test2"], 20 )

	def testTaskPlugsWithoutTaskNodes( self ) :

		s = Gaffer.ScriptNode()

		s["badNode"] = Gaffer.Node()
		s["badNode"]["task"] = GafferDispatch.TaskNode.TaskPlug(
			direction = Gaffer.Plug.Direction.Out,
			flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic
		)

		s["taskList"] = GafferDispatch.TaskList()
		s["taskList"]["preTasks"][0].setInput( s["badNode"]["task"] )

		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )
		with self.assertRaisesRegex( RuntimeError, "TaskPlug \"ScriptNode.badNode.task\" has no TaskNode" ) :
			dispatcher.dispatch( [ s["taskList"] ] )

	def testContextDrivingDispatcherPlugs( self ) :

		# a  per-frame task with driven dispatcher plugs
		# |
		# v  creates context variables that drive dispatcher plugs on `a`
		# |
		# b  per-frame task with normal dispatcher plugs

		s = Gaffer.ScriptNode()

		log = []
		s["a"] = GafferDispatchTest.LoggingTaskNode( log = log )
		s["a"]["f"] = Gaffer.StringPlug( defaultValue = "####" )

		s["cv"] = Gaffer.ContextVariables()
		s["cv"].setup( s["a"]["task"] )
		s["cv"]["in"].setInput( s["a"]["task"] )
		s["cv"]["variables"].addChild( Gaffer.NameValuePlug( "test", 2 ) )

		s["b"] = GafferDispatchTest.LoggingTaskNode( log = log )
		s["b"]["preTasks"][0].setInput( s["cv"]["out"] )
		s["b"]["f"] = Gaffer.StringPlug( defaultValue = "####" )

		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )
		dispatcher["framesMode"].setValue( GafferDispatch.Dispatcher.FramesMode.CustomRange )
		dispatcher["frameRange"].setValue( "1-4" )

		# batchSize
		s["e"] = Gaffer.Expression()
		s["e"].setExpression( "parent['a']['dispatcher']['batchSize'] = context.get( 'test', 1 )", "python" )
		dispatcher.dispatch( [ s["b"] ] )
		self.assertEqual( [ l.node.getName() for l in log ], [ "a", "a", "b", "b", "a", "a", "b", "b" ] )
		self.assertEqual( [ l.context.getFrame() for l in log ], [ 1, 2, 1, 2, 3, 4, 3, 4 ] )

		# immediate
		del log[:]
		s["cv"]["variables"].addChild( Gaffer.NameValuePlug( "testBool", True ) )
		s["e"].setExpression( "parent['a']['dispatcher']['immediate'] = context.get( 'testBool', False )", "python" )
		dispatcher.dispatch( [ s["b"] ] )
		self.assertEqual( [ l.node.getName() for l in log ], [ "a", "a", "a", "a", "b", "b", "b", "b" ] )
		self.assertEqual( [ l.context.getFrame() for l in log ], [ 1, 2, 3, 4, 1, 2, 3, 4 ] )

		# requiresSequenceExecution
		del log[:]
		s["cv"]["variables"].addChild( Gaffer.NameValuePlug( "testBool", True ) )
		s["e"].setExpression( "parent['a']['requiresSequenceExecution'] = context.get( 'testBool', False )", "python" )
		dispatcher.dispatch( [ s["b"] ] )
		self.assertEqual( [ l.node.getName() for l in log ], [ "a", "b", "b", "b", "b" ] )
		self.assertEqual( log[0].frames, [ 1, 2, 3, 4 ] )
		self.assertEqual( [ l.context.getFrame() for l in log[1:] ], [ 1, 2, 3, 4 ] )

if __name__ == "__main__":
	unittest.main()
