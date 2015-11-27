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

import IECore

import Gaffer
import GafferTest
import GafferDispatch
import GafferDispatchTest

class TestOp (IECore.Op) :

	def __init__( self, name, executionOrder ) :

		IECore.Op.__init__( self, "Test op", IECore.IntParameter( "result", "", 0 ) )
		self.parameters().addParameter( IECore.StringParameter( "name", "unique name to force different executions", name ) )
		self.parameters().addParameter( IECore.StringParameter( "currentFrame", "testing context substitution", "${frame}" ) )
		self.counter = 0
		self.frames = []
		self.executionOrder = executionOrder

	def doOperation( self, args ) :

		self.counter += 1
		self.frames.append( int(args["currentFrame"].value) )
		self.executionOrder.append( self )
		return IECore.IntData( self.counter )

class DispatcherTest( GafferTest.TestCase ) :

	class TestDispatcher( GafferDispatch.Dispatcher ) :

		def __init__( self ) :

			GafferDispatch.Dispatcher.__init__( self )
			self.log = list()

		def _doDispatch( self, batch ) :

			del self.log[:]
			self.__dispatch( batch )

		def __dispatch( self, batch ) :

			for currentBatch in batch.preTasks() :
				self.__dispatch( currentBatch )

			if not batch.node() or batch.blindData().get( "dispatched" ) :
				return

			batch.execute()

			batch.blindData()["dispatched"] = IECore.BoolData( True )

		@staticmethod
		def _doSetupPlugs( parentPlug ) :

			parentPlug["testDispatcherPlug"] = Gaffer.IntPlug(
				direction = Gaffer.Plug.Direction.In,
				flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic
			)

	IECore.registerRunTimeTyped( TestDispatcher )

	def setUp( self ) :

		GafferTest.TestCase.setUp( self )

		def create( jobsDirectory ) :

			dispatcher = DispatcherTest.TestDispatcher()
			dispatcher["jobsDirectory"].setValue( jobsDirectory )
			return dispatcher

		GafferDispatch.Dispatcher.registerDispatcher( "testDispatcher", functools.partial( create, self.temporaryDirectory() ) )

	def testBadJobDirectory( self ) :

		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )
		self.assertEqual( dispatcher["jobName"].getValue(), "" )
		self.assertEqual( dispatcher["jobsDirectory"].getValue(), self.temporaryDirectory() )

		s = Gaffer.ScriptNode()
		op1 = TestOp("1", dispatcher.log)
		s["n1"] = Gaffer.ExecutableOpHolder()
		s["n1"].setParameterised( op1 )
		dispatcher.dispatch( [ s["n1"] ] )
		jobDir = dispatcher.jobDirectory()
		self.assertEqual( jobDir, self.temporaryDirectory() + "/000000" )
		self.assertTrue( os.path.exists( jobDir ) )

	def testDerivedClass( self ) :

		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )

		s = Gaffer.ScriptNode()
		op1 = TestOp("1", dispatcher.log)
		s["n1"] = Gaffer.ExecutableOpHolder()
		s["n1"].setParameterised( op1 )

		dispatcher.dispatch( [ s["n1"] ] )

		self.assertEqual( op1.counter, 1 )

	def testNoScript( self ) :

		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )

		op1 = TestOp("1", dispatcher.log)
		n1 = Gaffer.ExecutableOpHolder()
		n1.setParameterised( op1 )

		self.assertRaises( RuntimeError, dispatcher.dispatch, [ n1 ] )
		self.assertEqual( dispatcher.jobDirectory(), "" )
		self.assertEqual( op1.counter, 0 )

	def testDifferentScripts( self ) :

		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )

		op1 = TestOp("1", dispatcher.log)
		s = Gaffer.ScriptNode()
		s["n1"] = Gaffer.ExecutableOpHolder()
		s["n1"].setParameterised( op1 )

		op2 = TestOp("2", dispatcher.log)
		s2 = Gaffer.ScriptNode()
		s2["n2"] = Gaffer.ExecutableOpHolder()
		s2["n2"].setParameterised( op2 )

		self.assertRaises( RuntimeError, dispatcher.dispatch, [ s["n1"], s2["n2"] ] )
		self.assertEqual( dispatcher.jobDirectory(), "" )
		self.assertEqual( op1.counter, 0 )
		self.assertEqual( op2.counter, 0 )

	def testNonExecutables( self ) :

		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )

		s = Gaffer.ScriptNode()
		s["n1"] = Gaffer.Node()

		self.assertRaises( RuntimeError, dispatcher.dispatch, [ s["n1"] ] )
		self.assertEqual( dispatcher.jobDirectory(), "" )

	def testDispatcherRegistration( self ) :

		self.failUnless( "testDispatcher" in GafferDispatch.Dispatcher.registeredDispatchers() )
		self.failUnless( GafferDispatch.Dispatcher.create( 'testDispatcher' ).isInstanceOf( DispatcherTest.TestDispatcher.staticTypeId() ) )

	def testDispatcherSignals( self ) :

		class CapturingSlot2( list ) :

			def __init__( self, *signals ) :

				self.__connections = []
				for s in signals :
					self.__connections.append( s.connect( Gaffer.WeakMethod( self.__slot ) ) )

			def __slot( self, d, nodes ) :
				self.append( (d,nodes) )

		preCs = CapturingSlot2( GafferDispatch.Dispatcher.preDispatchSignal() )
		self.assertEqual( len( preCs ), 0 )
		postCs = GafferTest.CapturingSlot( GafferDispatch.Dispatcher.postDispatchSignal() )
		self.assertEqual( len( postCs ), 0 )

		log = list()
		op1 = TestOp("1", log)
		s = Gaffer.ScriptNode()
		s["n1"] = Gaffer.ExecutableOpHolder()
		s["n1"].setParameterised( op1 )
		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )
		dispatcher.dispatch( [ s["n1"] ] )

		self.assertEqual( len( preCs ), 1 )
		self.failUnless( preCs[0][0].isSame( dispatcher ) )
		self.assertEqual( preCs[0][1], [ s["n1"] ] )

		self.assertEqual( len( postCs ), 1 )
		self.failUnless( postCs[0][0].isSame( dispatcher ) )
		self.assertEqual( postCs[0][1], [ s["n1"] ] )

	def testCancelDispatch( self ) :

		def onlyRunOnce( dispatcher, nodes ) :

			if len(dispatcher.log) :
				return True

			return False

		connection = GafferDispatch.Dispatcher.preDispatchSignal().connect( onlyRunOnce )

		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )
		op1 = TestOp( "1", dispatcher.log )
		s = Gaffer.ScriptNode()
		s["n1"] = Gaffer.ExecutableOpHolder()
		s["n1"].setParameterised( op1 )

		# never run
		self.assertEqual( len(dispatcher.log), 0 )
		self.assertEqual( op1.counter, 0 )

		# runs the first time
		dispatcher.dispatch( [ s["n1"] ] )
		self.assertEqual( len(dispatcher.log), 1 )
		self.assertEqual( op1.counter, 1 )

		# never runs again
		dispatcher.dispatch( [ s["n1"] ] )
		self.assertEqual( len(dispatcher.log), 1 )
		self.assertEqual( op1.counter, 1 )

	def testPlugs( self ) :

		n = Gaffer.ExecutableOpHolder()
		self.assertEqual( n['dispatcher'].getChild( 'testDispatcherPlug' ), None )

		GafferDispatch.Dispatcher.registerDispatcher( "testDispatcherWithCustomPlugs", DispatcherTest.TestDispatcher, setupPlugsFn = DispatcherTest.TestDispatcher._doSetupPlugs )

		n2 = Gaffer.ExecutableOpHolder()
		self.assertTrue( isinstance( n2['dispatcher'].getChild( 'testDispatcherPlug' ), Gaffer.IntPlug ) )
		self.assertEqual( n2['dispatcher']['testDispatcherPlug'].direction(), Gaffer.Plug.Direction.In )

	def testDispatch( self ) :

		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )

		# Create a tree of dependencies for execution:
		# n1 requires:
		# - n2 requires:
		#    -n2a
		#    -n2b
		op1 = TestOp("1", dispatcher.log)
		s = Gaffer.ScriptNode()
		s["n1"] = Gaffer.ExecutableOpHolder()
		s["n1"].setParameterised( op1 )
		s["n2"] = Gaffer.ExecutableOpHolder()
		op2 = TestOp("2", dispatcher.log)
		s["n2"].setParameterised( op2 )
		s["n2a"] = Gaffer.ExecutableOpHolder()
		op2a = TestOp("2a", dispatcher.log)
		s["n2a"].setParameterised( op2a )
		s["n2b"] = Gaffer.ExecutableOpHolder()
		op2b = TestOp("2b", dispatcher.log)
		s["n2b"].setParameterised( op2b )
		s["n1"]["preTasks"][0].setInput( s["n2"]["task"] )
		s["n2"]["preTasks"][0].setInput( s["n2a"]["task"] )
		s["n2"]["preTasks"][1].setInput( s["n2b"]["task"] )

		# Executing n1 should trigger execution of all of them
		dispatcher.dispatch( [ s["n1"] ] )
		self.assertEqual( op1.counter, 1 )
		self.assertEqual( op2.counter, 1 )
		self.assertEqual( op2a.counter, 1 )
		self.assertEqual( op2b.counter, 1 )
		self.assertTrue( dispatcher.log == [ op2a, op2b, op2, op1 ] or dispatcher.log == [ op2b, op2a, op2, op1 ] )

		# Executing n1 and anything else, should be the same as just n1
		dispatcher.dispatch( [ s["n2b"], s["n1"] ] )
		self.assertEqual( op1.counter, 2 )
		self.assertEqual( op2.counter, 2 )
		self.assertEqual( op2a.counter, 2 )
		self.assertEqual( op2b.counter, 2 )
		self.assertTrue( dispatcher.log == [ op2a, op2b, op2, op1 ] or dispatcher.log == [ op2b, op2a, op2, op1 ] )

		# Executing all nodes should be the same as just n1
		dispatcher.dispatch( [ s["n2"], s["n2b"], s["n1"], s["n2a"] ] )
		self.assertEqual( op1.counter, 3 )
		self.assertEqual( op2.counter, 3 )
		self.assertEqual( op2a.counter, 3 )
		self.assertEqual( op2b.counter, 3 )
		self.assertTrue( dispatcher.log == [ op2a, op2b, op2, op1 ] or dispatcher.log == [ op2b, op2a, op2, op1 ] )

		# Executing a sub-branch (n2) should only trigger execution in that branch
		dispatcher.dispatch( [ s["n2"] ] )
		self.assertEqual( op1.counter, 3 )
		self.assertEqual( op2.counter, 4 )
		self.assertEqual( op2a.counter, 4 )
		self.assertEqual( op2b.counter, 4 )
		self.assertTrue( dispatcher.log == [ op2a, op2b, op2 ] or dispatcher.log == [ op2b, op2a, op2 ] )

		# Executing a leaf node, should not trigger other executions.
		dispatcher.dispatch( [ s["n2b"] ] )
		self.assertEqual( op1.counter, 3 )
		self.assertEqual( op2.counter, 4 )
		self.assertEqual( op2a.counter, 4 )
		self.assertEqual( op2b.counter, 5 )
		self.assertTrue( dispatcher.log == [ op2b ] )

	def testDispatchIdenticalTasks( self ) :

		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )

		# Create a tree of dependencies for execution:
		# n1 requires:
		# - n2 requires:
		#    -n2a
		#    -n2b
		op1 = TestOp("1", dispatcher.log)
		s = Gaffer.ScriptNode()
		s["n1"] = Gaffer.ExecutableOpHolder()
		s["n1"].setParameterised( op1 )
		s["n2"] = Gaffer.ExecutableOpHolder()
		s["n2"].setParameterised( op1 )
		s["n2a"] = Gaffer.ExecutableOpHolder()
		s["n2a"].setParameterised( op1 )
		s["n2b"] = Gaffer.ExecutableOpHolder()
		s["n2b"].setParameterised( op1 )
		s["n1"]["preTasks"][0].setInput( s["n2"]["task"] )
		s["n2"]["preTasks"][0].setInput( s["n2a"]["task"] )
		s["n2"]["preTasks"][1].setInput( s["n2b"]["task"] )

		# even though all tasks are identical, we still execute them all
		dispatcher.dispatch( [ s["n1"] ] )
		self.assertEqual( op1.counter, 4 )
		self.assertEqual( dispatcher.log, [ op1, op1, op1, op1 ] )

		# Executing them all should do the same, with no duplicates
		dispatcher.dispatch( [ s["n2"], s["n2b"], s["n1"], s["n2a"] ] )
		self.assertEqual( op1.counter, 8 )
		self.assertEqual( dispatcher.log, [ op1, op1, op1, op1 ] )

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
		s["n1"]["preTasks"][0].setInput( s["n4"]["task"] )

		self.assertNotEqual( s["n1"].hash( s.context() ), s["n2"].hash( s.context() ) )
		self.assertNotEqual( s["n2"].hash( s.context() ), s["n3"].hash( s.context() ) )
		self.assertNotEqual( s["n3"].hash( s.context() ), s["n4"].hash( s.context() ) )
		self.assertNotEqual( s["n1"].hash( s.context() ), s["n4"].hash( s.context() ) )

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

		self.assertNotEqual( s["n1"].hash( s.context() ), s["n2"].hash( s.context() ) )
		self.assertNotEqual( s["n2"].hash( s.context() ), s["n3"].hash( s.context() ) )

		self.assertEqual( os.path.isfile( fileName ), False )
		dispatcher.dispatch( [ s["n3"] ] )
		self.assertEqual( os.path.isfile( fileName ), True )

		with file( fileName, "r" ) as f :
			text = f.read()

		self.assertEqual( text, "a1;b1;c1;" )

	def testNoTask( self ) :

		s = Gaffer.ScriptNode()
		s["n1"] = Gaffer.ExecutableOpHolder()
		self.assertEqual( s["n1"].hash( s.context() ), IECore.MurmurHash() )

		# It doesn't execute, because the executionHash is null
		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )
		dispatcher.dispatch( [ s["n1"] ] )
		self.assertEqual( dispatcher.log, [] )

	def testDispatchDifferentFrame( self ) :

		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )
		dispatcher["framesMode"].setValue( GafferDispatch.Dispatcher.FramesMode.CurrentFrame )

		s = Gaffer.ScriptNode()
		op1 = TestOp("1", dispatcher.log)
		s["n1"] = Gaffer.ExecutableOpHolder()
		s["n1"].setParameterised( op1 )

		context = Gaffer.Context( s.context() )
		context.setFrame( s.context().getFrame() + 10 )
		self.assertEqual( dispatcher.frameRange( s, context ), IECore.frameListFromList( [ int(context.getFrame()) ] ) )

		with context :
			dispatcher.dispatch( [ s["n1"] ] )

		self.assertEqual( op1.counter, 1 )
		self.assertEqual( op1.frames, [ context.getFrame() ] )

	def testDispatchFullRange( self ) :

		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )
		dispatcher["framesMode"].setValue( GafferDispatch.Dispatcher.FramesMode.FullRange )

		s = Gaffer.ScriptNode()
		op1 = TestOp("1", dispatcher.log)
		s["n1"] = Gaffer.ExecutableOpHolder()
		s["n1"].setParameterised( op1 )

		dispatcher.dispatch( [ s["n1"] ] )

		frameRange = IECore.FrameRange( s["frameRange"]["start"].getValue(), s["frameRange"]["end"].getValue() )
		self.assertEqual( dispatcher.frameRange( s, s.context() ), frameRange )
		self.assertEqual( op1.counter, len(frameRange.asList()) )
		self.assertEqual( op1.frames, frameRange.asList() )

	def testDispatchCustomRange( self ) :

		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )
		dispatcher["framesMode"].setValue( GafferDispatch.Dispatcher.FramesMode.CustomRange )
		frameList = IECore.FrameList.parse( "2-6x2" )
		dispatcher["frameRange"].setValue( str(frameList) )

		s = Gaffer.ScriptNode()
		op1 = TestOp("1", dispatcher.log)
		s["n1"] = Gaffer.ExecutableOpHolder()
		s["n1"].setParameterised( op1 )

		dispatcher.dispatch( [ s["n1"] ] )

		frames = frameList.asList()
		self.assertEqual( dispatcher.frameRange( s, s.context() ), frameList )
		self.assertEqual( op1.counter, len(frames) )
		self.assertEqual( op1.frames, frames )

	def testDispatchBadCustomRange( self ) :

		dispatcher = GafferDispatch.Dispatcher.create( "testDispatcher" )
		dispatcher["framesMode"].setValue( GafferDispatch.Dispatcher.FramesMode.CustomRange )
		dispatcher["frameRange"].setValue( "notAFrameRange" )

		s = Gaffer.ScriptNode()
		op1 = TestOp("1", dispatcher.log)
		s["n1"] = Gaffer.ExecutableOpHolder()
		s["n1"].setParameterised( op1 )

		self.assertRaises( RuntimeError, dispatcher.dispatch, [ s["n1"] ] )
		self.assertRaises( RuntimeError, dispatcher.frameRange, s, s.context() )
		self.assertEqual( op1.counter, 0 )
		self.assertEqual( op1.frames, [] )

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

		with file( fileName, "r" ) as f :
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
		with file( fileName, "r" ) as f :
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
		with file( fileName, "r" ) as f :
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
		with file( fileName, "r" ) as f :
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
		with file( fileName, "r" ) as f :
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
		promotedPreTaskPlug = s["b"].promotePlug( s["b"]["n3"]["preTasks"][0] )
		promotedPreTaskPlug.setInput( s["n1"]["task"] )
		s["b"]["n3"]["preTasks"][1].setInput( s["b"]["n2"]["task"] )
		promotedTaskPlug = s["b"].promotePlug( s["b"]["n3"]["task"] )
		s["n4"]["preTasks"][0].setInput( promotedTaskPlug )
		# export a reference too
		s["b"].exportForReference( self.temporaryDirectory() + "/test.grf" )
		s["r"] = Gaffer.Reference()
		s["r"].load( self.temporaryDirectory() + "/test.grf" )
		s["r"][promotedPreTaskPlug.getName()].setInput( s["n1"]["task"] )

		# dispatch an Executable that requires a Box

		self.assertEqual( os.path.isfile( fileName ), False )
		dispatcher.dispatch( [ s["n4"] ] )
		self.assertEqual( os.path.isfile( fileName ), True )
		with file( fileName, "r" ) as f :
			text = f.read()

		# all frames of n1 and n2 interleaved, followed by the n3 sequence, followed by n4 on all frames
		expectedText = "n1 on 2;n2 on 2;n1 on 4;n2 on 4;n1 on 6;n2 on 6;n3 on 2;n3 on 4;n3 on 6;n4 on 2;n4 on 4;n4 on 6;"
		self.assertEqual( text, expectedText )

		# dispatch the box directly

		os.remove( fileName )
		self.assertEqual( os.path.isfile( fileName ), False )
		dispatcher.dispatch( [ s["b"] ] )
		self.assertEqual( os.path.isfile( fileName ), True )
		with file( fileName, "r" ) as f :
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
		with file( fileName, "r" ) as f :
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
		with file( fileName, "r" ) as f :
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
		with file( fileName, "r" ) as f :
			text = f.read()

		# all frames of n1, followed by the n3 sequence, followed by all frames of n2
		expectedText = "n1 on 2;n1 on 4;n1 on 6;n3 on 2;n3 on 4;n3 on 6;n2 on 2;n2 on 4;n2 on 6;"
		self.assertEqual( text, expectedText )

		# dispatch an Executable that requires a Reference

		os.remove( fileName )
		s["n4"]["preTasks"][0].setInput( s["r"][promotedTaskPlug.getName()] )
		self.assertEqual( os.path.isfile( fileName ), False )
		dispatcher.dispatch( [ s["n4"] ] )
		self.assertEqual( os.path.isfile( fileName ), True )
		with file( fileName, "r" ) as f :
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
		with file( fileName, "r" ) as f :
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
		op1 = TestOp("1", dispatcher.log)
		s["n1"] = Gaffer.ExecutableOpHolder()
		s["n1"].setParameterised( op1 )

		dispatcher["framesMode"].setValue( GafferDispatch.Dispatcher.FramesMode.CurrentFrame )
		self.assertEqual( dispatcher.frameRange( s, s.context() ), IECore.frameListFromList( [ int(s.context().getFrame()) ] ) )

		dispatcher["framesMode"].setValue( GafferDispatch.Dispatcher.FramesMode.FullRange )
		self.assertEqual( dispatcher.frameRange( s, s.context() ), IECore.FrameList.parse( "1-100b" ) )

		dispatcher["framesMode"].setValue( GafferDispatch.Dispatcher.FramesMode.CustomRange )
		binaryFrames = IECore.FrameList.parse( "1-10b" )
		self.assertEqual( dispatcher.frameRange( s, s.context() ), binaryFrames )

		dispatcher.dispatch( [ s["n1"] ] )

		self.assertEqual( op1.counter, len(frameList.asList()) )
		self.assertNotEqual( op1.frames, frameList.asList() )
		self.assertEqual( op1.frames, binaryFrames.asList() )

	def testPreTasksOverride( self ) :

		class SelfRequiringNode( GafferDispatch.ExecutableNode ) :

			def __init__( self ) :

				GafferDispatch.ExecutableNode.__init__( self )

				self.addChild( Gaffer.IntPlug( "multiplier", defaultValue = 1 ) )

				self.preExecutionCount = 0
				self.mainExecutionCount = 0

			def preTasks( self, context ) :

				if context.get( "selfExecutingNode:preExecute", None ) is None :

					customContext = Gaffer.Context( context )
					customContext["selfExecutingNode:preExecute"] = True
					preTasks = [ GafferDispatch.ExecutableNode.Task( self, customContext ) ]

				else :

					# We need to evaluate our external requirements as well,
					# and they need to be requirements of our preExecute task
					# only, since that is the topmost branch of our internal
					# requirement graph. We also need to use a Context which
					# does not contain our internal preExecute entry, incase
					# that has meaning for any of our external requirements.
					customContext = Gaffer.Context( context )
					del customContext["selfExecutingNode:preExecute"]
					preTasks = GafferDispatch.ExecutableNode.preTasks( self, customContext )

				return preTasks

			def hash( self, context ) :

				h = GafferDispatch.ExecutableNode.hash( self, context )
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
		self.assertEqual( s["e2"].preTasks( c1 ), [ GafferDispatch.ExecutableNode.Task( s["e2"], c2 ) ] )
		# e2 in the other context requires e1 with the original context
		self.assertEqual( s["e2"].preTasks( c2 ), [ GafferDispatch.ExecutableNode.Task( s["e1"], c1 ) ] )
		# e1 requires itself with a different context
		self.assertEqual( s["e1"].preTasks( c1 ), [ GafferDispatch.ExecutableNode.Task( s["e1"], c2 ) ] )
		# e1 in the other context has no requirements
		self.assertEqual( s["e1"].preTasks( c2 ), [] )

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

		class ContextChangingExecutable( GafferDispatch.ExecutableNode ) :

			def __init__( self, name = "ContextChangingExecutable" ) :

				GafferDispatch.ExecutableNode.__init__( self, name )

			def preTasks( self, context ) :

				assert( context.isSame( Gaffer.Context.current() ) )

				upstreamContext = Gaffer.Context( context )
				upstreamContext["myText"] = "testing 123"
				upstreamContext.setFrame( 10 )

				result = []
				for plug in self["preTasks"] :
					node = plug.source().node()
					if node.isSame( self ) or not isinstance( node, GafferDispatch.ExecutableNode ):
						continue

					result.append( self.Task( node, upstreamContext ) )

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

		s["c"] = ContextChangingExecutable()
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

if __name__ == "__main__":
	unittest.main()
