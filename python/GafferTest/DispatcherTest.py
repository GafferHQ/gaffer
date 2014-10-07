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
import stat
import shutil
import unittest

import IECore

import Gaffer
import GafferTest

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

	class MyDispatcher( Gaffer.Dispatcher ) :

		def __init__( self ) :

			Gaffer.Dispatcher.__init__( self )
			self.log = list()

		def _doDispatch( self, batch ) :

			del self.log[:]
			self.__dispatch( batch )

		def __dispatch( self, batch ) :

			for currentBatch in batch.requirements() :
				self.__dispatch( currentBatch )

			if not batch.node() or batch.blindData().get( "dispatched" ) :
				return

			batch.execute()

			batch.blindData()["dispatched"] = IECore.BoolData( True )

		def _doSetupPlugs( self, parentPlug ) :

			parentPlug["testDispatcherPlug"] = Gaffer.IntPlug(
				direction = Gaffer.Plug.Direction.In,
				flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic
			)

	def setUp( self ) :

		os.makedirs( "/tmp/dispatcherTest" )

		if not "testDispatcher" in Gaffer.Dispatcher.dispatcherNames():
			IECore.registerRunTimeTyped( DispatcherTest.MyDispatcher )
			dispatcher = DispatcherTest.MyDispatcher()
			Gaffer.Dispatcher.registerDispatcher( "testDispatcher", dispatcher )

	def testBadJobDirectory( self ) :

		dispatcher = DispatcherTest.MyDispatcher()
		self.assertEqual( dispatcher["jobName"].getValue(), "" )
		self.assertEqual( dispatcher["jobsDirectory"].getValue(), "" )
		s = Gaffer.ScriptNode()
		op1 = TestOp("1", dispatcher.log)
		s["n1"] = Gaffer.ExecutableOpHolder()
		s["n1"].setParameterised( op1 )
		dispatcher.dispatch( [ s["n1"] ] )
		jobDir = dispatcher.jobDirectory()
		self.assertNotEqual( jobDir, "" )
		self.assertTrue( os.path.exists( jobDir ) )
		shutil.rmtree( jobDir )

	def testDerivedClass( self ) :

		dispatcher = DispatcherTest.MyDispatcher()

		s = Gaffer.ScriptNode()
		op1 = TestOp("1", dispatcher.log)
		s["n1"] = Gaffer.ExecutableOpHolder()
		s["n1"].setParameterised( op1 )

		dispatcher.dispatch( [ s["n1"] ] )
		shutil.rmtree( dispatcher.jobDirectory() )

		self.assertEqual( op1.counter, 1 )

	def testNoScript( self ) :

		dispatcher = DispatcherTest.MyDispatcher()

		op1 = TestOp("1", dispatcher.log)
		n1 = Gaffer.ExecutableOpHolder()
		n1.setParameterised( op1 )

		self.assertRaises( RuntimeError, dispatcher.dispatch, [ n1 ] )
		self.assertEqual( dispatcher.jobDirectory(), "" )
		self.assertEqual( op1.counter, 0 )

	def testDifferentScripts( self ) :

		dispatcher = DispatcherTest.MyDispatcher()

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

		dispatcher = DispatcherTest.MyDispatcher()

		s = Gaffer.ScriptNode()
		s["n1"] = Gaffer.Node()

		self.assertRaises( RuntimeError, dispatcher.dispatch, [ s["n1"] ] )
		self.assertEqual( dispatcher.jobDirectory(), "" )

	def testDispatcherRegistration( self ) :

		self.failUnless( "testDispatcher" in Gaffer.Dispatcher.dispatcherNames() )
		self.failUnless( Gaffer.Dispatcher.dispatcher( 'testDispatcher' ).isInstanceOf( DispatcherTest.MyDispatcher.staticTypeId() ) )

	def testDispatcherSignals( self ) :

		class CapturingSlot2( list ) :

			def __init__( self, *signals ) :

				self.__connections = []
				for s in signals :
					self.__connections.append( s.connect( Gaffer.WeakMethod( self.__slot ) ) )

			def __slot( self, d, nodes ) :
				self.append( (d,nodes) )

		preCs = CapturingSlot2( Gaffer.Dispatcher.preDispatchSignal() )
		self.assertEqual( len( preCs ), 0 )
		postCs = GafferTest.CapturingSlot( Gaffer.Dispatcher.postDispatchSignal() )
		self.assertEqual( len( postCs ), 0 )

		log = list()
		op1 = TestOp("1", log)
		s = Gaffer.ScriptNode()
		s["n1"] = Gaffer.ExecutableOpHolder()
		s["n1"].setParameterised( op1 )
		dispatcher = DispatcherTest.MyDispatcher()
		dispatcher.dispatch( [ s["n1"] ] )
		shutil.rmtree( dispatcher.jobDirectory() )

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

		connection = Gaffer.Dispatcher.preDispatchSignal().connect( onlyRunOnce )

		dispatcher = DispatcherTest.MyDispatcher()
		op1 = TestOp( "1", dispatcher.log )
		s = Gaffer.ScriptNode()
		s["n1"] = Gaffer.ExecutableOpHolder()
		s["n1"].setParameterised( op1 )

		# never run
		self.assertEqual( len(dispatcher.log), 0 )
		self.assertEqual( op1.counter, 0 )

		# runs the first time
		dispatcher.dispatch( [ s["n1"] ] )
		shutil.rmtree( dispatcher.jobDirectory() )
		self.assertEqual( len(dispatcher.log), 1 )
		self.assertEqual( op1.counter, 1 )

		# never runs again
		dispatcher.dispatch( [ s["n1"] ] )
		shutil.rmtree( dispatcher.jobDirectory() )
		self.assertEqual( len(dispatcher.log), 1 )
		self.assertEqual( op1.counter, 1 )

	def testPlugs( self ) :

		n = Gaffer.ExecutableOpHolder()
		n['dispatcher'].direction()
		n['dispatcher']['testDispatcherPlug'].direction()
		self.assertEqual( n['dispatcher']['testDispatcherPlug'].direction(), Gaffer.Plug.Direction.In )

	def testDispatch( self ) :

		dispatcher = Gaffer.Dispatcher.dispatcher( "testDispatcher" )

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
		s["n1"]['requirements'][0].setInput( s["n2"]['requirement'] )
		s["n2"]['requirements'][0].setInput( s["n2a"]['requirement'] )
		s["n2"]['requirements'][1].setInput( s["n2b"]['requirement'] )

		# Executing n1 should trigger execution of all of them
		dispatcher.dispatch( [ s["n1"] ] )
		shutil.rmtree( dispatcher.jobDirectory() )
		self.assertEqual( op1.counter, 1 )
		self.assertEqual( op2.counter, 1 )
		self.assertEqual( op2a.counter, 1 )
		self.assertEqual( op2b.counter, 1 )
		self.assertTrue( dispatcher.log == [ op2a, op2b, op2, op1 ] or dispatcher.log == [ op2b, op2a, op2, op1 ] )

		# Executing n1 and anything else, should be the same as just n1
		dispatcher.dispatch( [ s["n2b"], s["n1"] ] )
		shutil.rmtree( dispatcher.jobDirectory() )
		self.assertEqual( op1.counter, 2 )
		self.assertEqual( op2.counter, 2 )
		self.assertEqual( op2a.counter, 2 )
		self.assertEqual( op2b.counter, 2 )
		self.assertTrue( dispatcher.log == [ op2a, op2b, op2, op1 ] or dispatcher.log == [ op2b, op2a, op2, op1 ] )

		# Executing all nodes should be the same as just n1
		dispatcher.dispatch( [ s["n2"], s["n2b"], s["n1"], s["n2a"] ] )
		shutil.rmtree( dispatcher.jobDirectory() )
		self.assertEqual( op1.counter, 3 )
		self.assertEqual( op2.counter, 3 )
		self.assertEqual( op2a.counter, 3 )
		self.assertEqual( op2b.counter, 3 )
		self.assertTrue( dispatcher.log == [ op2a, op2b, op2, op1 ] or dispatcher.log == [ op2b, op2a, op2, op1 ] )

		# Executing a sub-branch (n2) should only trigger execution in that branch
		dispatcher.dispatch( [ s["n2"] ] )
		shutil.rmtree( dispatcher.jobDirectory() )
		self.assertEqual( op1.counter, 3 )
		self.assertEqual( op2.counter, 4 )
		self.assertEqual( op2a.counter, 4 )
		self.assertEqual( op2b.counter, 4 )
		self.assertTrue( dispatcher.log == [ op2a, op2b, op2 ] or dispatcher.log == [ op2b, op2a, op2 ] )

		# Executing a leaf node, should not trigger other executions.
		dispatcher.dispatch( [ s["n2b"] ] )
		shutil.rmtree( dispatcher.jobDirectory() )
		self.assertEqual( op1.counter, 3 )
		self.assertEqual( op2.counter, 4 )
		self.assertEqual( op2a.counter, 4 )
		self.assertEqual( op2b.counter, 5 )
		self.assertTrue( dispatcher.log == [ op2b ] )

	def testDispatchIdenticalTasks( self ) :

		dispatcher = Gaffer.Dispatcher.dispatcher( "testDispatcher" )

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
		s["n1"]['requirements'][0].setInput( s["n2"]['requirement'] )
		s["n2"]['requirements'][0].setInput( s["n2a"]['requirement'] )
		s["n2"]['requirements'][1].setInput( s["n2b"]['requirement'] )

		# Executing n1 should only execute once, because all tasks are identical
		dispatcher.dispatch( [ s["n1"] ] )
		shutil.rmtree( dispatcher.jobDirectory() )
		self.assertEqual( op1.counter, 1 )
		self.assertEqual( dispatcher.log, [ op1 ] )

		# Executing them all should still only execute one, because all tasks are identical
		dispatcher.dispatch( [ s["n2"], s["n2b"], s["n1"], s["n2a"] ] )
		shutil.rmtree( dispatcher.jobDirectory() )
		self.assertEqual( op1.counter, 2 )
		self.assertEqual( dispatcher.log, [ op1 ] )

	def testNoTask( self ) :

		s = Gaffer.ScriptNode()
		s["n1"] = Gaffer.ExecutableOpHolder()
		self.assertEqual( s["n1"].hash( s.context() ), IECore.MurmurHash() )

		# It doesn't execute, because the executionHash is null
		dispatcher = Gaffer.Dispatcher.dispatcher( "testDispatcher" )
		dispatcher.dispatch( [ s["n1"] ] )
		shutil.rmtree( dispatcher.jobDirectory() )
		self.assertEqual( dispatcher.log, [] )

	def testDispatchDifferentFrame( self ) :

		dispatcher = DispatcherTest.MyDispatcher()
		dispatcher["framesMode"].setValue( Gaffer.Dispatcher.FramesMode.CurrentFrame )

		s = Gaffer.ScriptNode()
		op1 = TestOp("1", dispatcher.log)
		s["n1"] = Gaffer.ExecutableOpHolder()
		s["n1"].setParameterised( op1 )

		context = Gaffer.Context( s.context() )
		context.setFrame( s.context().getFrame() + 10 )

		with context :
			dispatcher.dispatch( [ s["n1"] ] )
			shutil.rmtree( dispatcher.jobDirectory() )

		self.assertEqual( op1.counter, 1 )
		self.assertEqual( op1.frames, [ context.getFrame() ] )

	def testDispatchFullRange( self ) :

		dispatcher = DispatcherTest.MyDispatcher()
		dispatcher["framesMode"].setValue( Gaffer.Dispatcher.FramesMode.FullRange )

		s = Gaffer.ScriptNode()
		op1 = TestOp("1", dispatcher.log)
		s["n1"] = Gaffer.ExecutableOpHolder()
		s["n1"].setParameterised( op1 )

		dispatcher.dispatch( [ s["n1"] ] )
		shutil.rmtree( dispatcher.jobDirectory() )

		frames = IECore.FrameRange( s["frameRange"]["start"].getValue(), s["frameRange"]["end"].getValue() ).asList()
		self.assertEqual( op1.counter, len(frames) )
		self.assertEqual( op1.frames, frames )

	def testDispatchCustomRange( self ) :

		dispatcher = DispatcherTest.MyDispatcher()
		dispatcher["framesMode"].setValue( Gaffer.Dispatcher.FramesMode.CustomRange )
		frameList = IECore.FrameList.parse( "2-6x2" )
		dispatcher["frameRange"].setValue( str(frameList) )

		s = Gaffer.ScriptNode()
		op1 = TestOp("1", dispatcher.log)
		s["n1"] = Gaffer.ExecutableOpHolder()
		s["n1"].setParameterised( op1 )

		dispatcher.dispatch( [ s["n1"] ] )
		shutil.rmtree( dispatcher.jobDirectory() )

		frames = frameList.asList()
		self.assertEqual( op1.counter, len(frames) )
		self.assertEqual( op1.frames, frames )

	def testDispatchBadCustomRange( self ) :

		dispatcher = DispatcherTest.MyDispatcher()
		dispatcher["framesMode"].setValue( Gaffer.Dispatcher.FramesMode.CustomRange )
		dispatcher["frameRange"].setValue( "notAFrameRange" )

		s = Gaffer.ScriptNode()
		op1 = TestOp("1", dispatcher.log)
		s["n1"] = Gaffer.ExecutableOpHolder()
		s["n1"].setParameterised( op1 )

		self.assertRaises( RuntimeError, dispatcher.dispatch, [ s["n1"] ] )
		self.assertEqual( op1.counter, 0 )
		self.assertEqual( op1.frames, [] )

	def testDoesNotRequireSequenceExecution( self ) :

		dispatcher = DispatcherTest.MyDispatcher()
		dispatcher["framesMode"].setValue( Gaffer.Dispatcher.FramesMode.CustomRange )
		frameList = IECore.FrameList.parse( "2-6x2" )
		dispatcher["frameRange"].setValue( str(frameList) )
		fileName = "/tmp/dispatcherTest/result.txt"

		s = Gaffer.ScriptNode()
		s["n1"] = GafferTest.TextWriter()
		s["n1"]["mode"].setValue( "a" )
		s["n1"]["fileName"].setValue( fileName )
		s["n1"]["text"].setValue( "n1 on ${frame};" )
		s["n2"] = GafferTest.TextWriter()
		s["n2"]["mode"].setValue( "a" )
		s["n2"]["fileName"].setValue( fileName )
		s["n2"]["text"].setValue( "n2 on ${frame};" )
		s["n3"] = GafferTest.TextWriter()
		s["n3"]["mode"].setValue( "a" )
		s["n3"]["fileName"].setValue( fileName )
		s["n3"]["text"].setValue( "n3 on ${frame};" )
		s["n2"]['requirements'][0].setInput( s["n1"]['requirement'] )
		s["n3"]['requirements'][0].setInput( s["n2"]['requirement'] )

		self.assertEqual( os.path.isfile( fileName ), False )

		dispatcher.dispatch( [ s["n3"] ] )
		shutil.rmtree( dispatcher.jobDirectory() )

		self.assertEqual( os.path.isfile( fileName ), True )

		with file( fileName, "r" ) as f :
			text = f.read()

		# all nodes on frame 1, followed by all nodes on frame 2, followed by all nodes on frame 3
		expectedText = "n1 on 2;n2 on 2;n3 on 2;n1 on 4;n2 on 4;n3 on 4;n1 on 6;n2 on 6;n3 on 6;"
		self.assertEqual( text, expectedText )

	def testRequiresSequenceExecution( self ) :

		dispatcher = DispatcherTest.MyDispatcher()
		dispatcher["framesMode"].setValue( Gaffer.Dispatcher.FramesMode.CustomRange )
		frameList = IECore.FrameList.parse( "2-6x2" )
		dispatcher["frameRange"].setValue( str(frameList) )
		fileName = "/tmp/dispatcherTest/result.txt"

		s = Gaffer.ScriptNode()
		s["n1"] = GafferTest.TextWriter()
		s["n1"]["mode"].setValue( "a" )
		s["n1"]["fileName"].setValue( fileName )
		s["n1"]["text"].setValue( "n1 on ${frame};" )
		s["n2"] = GafferTest.TextWriter( requiresSequenceExecution = True )
		s["n2"]["mode"].setValue( "a" )
		s["n2"]["fileName"].setValue( fileName )
		s["n2"]["text"].setValue( "n2 on ${frame};" )
		s["n3"] = GafferTest.TextWriter()
		s["n3"]["mode"].setValue( "a" )
		s["n3"]["fileName"].setValue( fileName )
		s["n3"]["text"].setValue( "n3 on ${frame};" )
		s["n2"]['requirements'][0].setInput( s["n1"]['requirement'] )
		s["n3"]['requirements'][0].setInput( s["n2"]['requirement'] )

		self.assertEqual( os.path.isfile( fileName ), False )
		dispatcher.dispatch( [ s["n3"] ] )
		shutil.rmtree( dispatcher.jobDirectory() )
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
		shutil.rmtree( dispatcher.jobDirectory() )
		self.assertEqual( os.path.isfile( fileName ), True )
		with file( fileName, "r" ) as f :
			text = f.read()

		# n1 in requested order, followed by the n2 sequence in sorted order, followed by n3 in the requested order
		expectedText = "n1 on 2;n1 on 6;n1 on 4;n2 on 2;n2 on 4;n2 on 6;n3 on 2;n3 on 6;n3 on 4;"
		self.assertEqual( text, expectedText )

	def testBatchSize( self ) :

		dispatcher = DispatcherTest.MyDispatcher()
		dispatcher["framesMode"].setValue( Gaffer.Dispatcher.FramesMode.CustomRange )
		frameList = IECore.FrameList.parse( "2-6x2" )
		dispatcher["frameRange"].setValue( str(frameList) )
		fileName = "/tmp/dispatcherTest/result.txt"

		s = Gaffer.ScriptNode()
		s["n1"] = GafferTest.TextWriter()
		s["n1"]["mode"].setValue( "a" )
		s["n1"]["fileName"].setValue( fileName )
		s["n1"]["text"].setValue( "n1 on ${frame};" )
		s["n2"] = GafferTest.TextWriter()
		s["n2"]["mode"].setValue( "a" )
		s["n2"]["fileName"].setValue( fileName )
		s["n2"]["text"].setValue( "n2 on ${frame};" )
		s["n3"] = GafferTest.TextWriter( requiresSequenceExecution = True )
		s["n3"]["mode"].setValue( "a" )
		s["n3"]["fileName"].setValue( fileName )
		s["n3"]["text"].setValue( "n3 on ${frame};" )
		s["n4"] = GafferTest.TextWriter()
		s["n4"]["mode"].setValue( "a" )
		s["n4"]["fileName"].setValue( fileName )
		s["n4"]["text"].setValue( "n4 on ${frame};" )
		s["n3"]['requirements'][0].setInput( s["n1"]['requirement'] )
		s["n3"]['requirements'][1].setInput( s["n2"]['requirement'] )
		s["n4"]['requirements'][0].setInput( s["n3"]['requirement'] )

		self.assertEqual( os.path.isfile( fileName ), False )
		dispatcher.dispatch( [ s["n4"] ] )
		shutil.rmtree( dispatcher.jobDirectory() )
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
		shutil.rmtree( dispatcher.jobDirectory() )
		self.assertEqual( os.path.isfile( fileName ), True )
		with file( fileName, "r" ) as f :
			text = f.read()

		# first 2 frames of n1, followed by all frames of n2, followed by last frame of n1, followed by the n3 sequence, followed by n4 on all frames
		expectedText = "n1 on 2;n1 on 4;n2 on 2;n2 on 4;n2 on 6;n1 on 6;n3 on 2;n3 on 4;n3 on 6;n4 on 2;n4 on 4;n4 on 6;"
		self.assertEqual( text, expectedText )

	def testDispatchThroughABox( self ) :

		dispatcher = DispatcherTest.MyDispatcher()
		dispatcher["framesMode"].setValue( Gaffer.Dispatcher.FramesMode.CustomRange )
		frameList = IECore.FrameList.parse( "2-6x2" )
		dispatcher["frameRange"].setValue( str(frameList) )
		fileName = "/tmp/dispatcherTest/result.txt"

		s = Gaffer.ScriptNode()
		s["n1"] = GafferTest.TextWriter()
		s["n1"]["mode"].setValue( "a" )
		s["n1"]["fileName"].setValue( fileName )
		s["n1"]["text"].setValue( "n1 on ${frame};" )
		s["b"] = Gaffer.Box()
		s["b"]["n2"] = GafferTest.TextWriter()
		s["b"]["n2"]["mode"].setValue( "a" )
		s["b"]["n2"]["fileName"].setValue( fileName )
		s["b"]["n2"]["text"].setValue( "n2 on ${frame};" )
		s["b"]["n3"] = GafferTest.TextWriter( requiresSequenceExecution = True )
		s["b"]["n3"]["mode"].setValue( "a" )
		s["b"]["n3"]["fileName"].setValue( fileName )
		s["b"]["n3"]["text"].setValue( "n3 on ${frame};" )
		s["n4"] = GafferTest.TextWriter()
		s["n4"]["mode"].setValue( "a" )
		s["n4"]["fileName"].setValue( fileName )
		s["n4"]["text"].setValue( "n4 on ${frame};" )
		s["b"]["in"] = s["b"]["n3"]["requirements"][0].createCounterpart( "in", Gaffer.Plug.Direction.In )
		s["b"]["n3"]["requirements"][0].setInput( s["b"]["in"] )
		s["b"]["in"].setInput( s["n1"]['requirement'] )
		s["b"]["n3"]["requirements"][1].setInput( s["b"]["n2"]['requirement'] )
		s["b"]["out"] = s["b"]["n3"]['requirement'].createCounterpart( "out", Gaffer.Plug.Direction.Out )
		s["b"]["out"].setInput( s["b"]["n3"]["requirement"] )
		s["n4"]['requirements'][0].setInput( s["b"]['out'] )

		# dispatch an Executable that requires a Box

		self.assertEqual( os.path.isfile( fileName ), False )
		dispatcher.dispatch( [ s["n4"] ] )
		shutil.rmtree( dispatcher.jobDirectory() )
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
		shutil.rmtree( dispatcher.jobDirectory() )
		self.assertEqual( os.path.isfile( fileName ), True )
		with file( fileName, "r" ) as f :
			text = f.read()

		# all frames of n1 and n2 interleaved, followed by the n3 sequence
		expectedText = "n1 on 2;n2 on 2;n1 on 4;n2 on 4;n1 on 6;n2 on 6;n3 on 2;n3 on 4;n3 on 6;"
		self.assertEqual( text, expectedText )

		# only the promoted requirement dispatches

		s["b"]["n3"]["requirements"][1].setInput( None )

		os.remove( fileName )
		self.assertEqual( os.path.isfile( fileName ), False )
		dispatcher.dispatch( [ s["b"] ] )
		shutil.rmtree( dispatcher.jobDirectory() )
		self.assertEqual( os.path.isfile( fileName ), True )
		with file( fileName, "r" ) as f :
			text = f.read()

		# all frames of n1, followed by the n3 sequence
		expectedText = "n1 on 2;n1 on 4;n1 on 6;n3 on 2;n3 on 4;n3 on 6;"
		self.assertEqual( text, expectedText )

		# promoting a requirement doesn't dispatch unless it's connected

		s["b"]["out2"] = s["b"]["n2"]['requirement'].createCounterpart( "out2", Gaffer.Plug.Direction.Out )

		os.remove( fileName )
		self.assertEqual( os.path.isfile( fileName ), False )
		dispatcher.dispatch( [ s["b"] ] )
		shutil.rmtree( dispatcher.jobDirectory() )
		self.assertEqual( os.path.isfile( fileName ), True )
		with file( fileName, "r" ) as f :
			text = f.read()

		# all frames of n1, followed by the n3 sequence
		expectedText = "n1 on 2;n1 on 4;n1 on 6;n3 on 2;n3 on 4;n3 on 6;"
		self.assertEqual( text, expectedText )

		# connecting it to a non-executable doesn't do anything either

		s["b"]["n5"] = Gaffer.Node()
		s["b"]["n5"]["requirement"] = Gaffer.Plug( direction = Gaffer.Plug.Direction.Out )
		s["b"]["out2"].setInput( s["b"]["n5"]["requirement"] )

		os.remove( fileName )
		self.assertEqual( os.path.isfile( fileName ), False )
		dispatcher.dispatch( [ s["b"] ] )
		shutil.rmtree( dispatcher.jobDirectory() )
		self.assertEqual( os.path.isfile( fileName ), True )
		with file( fileName, "r" ) as f :
			text = f.read()

		# all frames of n1, followed by the n3 sequence
		expectedText = "n1 on 2;n1 on 4;n1 on 6;n3 on 2;n3 on 4;n3 on 6;"
		self.assertEqual( text, expectedText )

		# multiple promoted requirements will dispatch

		s["b"]["out3"] = s["b"]["n2"]['requirement'].createCounterpart( "out3", Gaffer.Plug.Direction.Out )
		s["b"]["out3"].setInput( s["b"]["n2"]["requirement"] )

		os.remove( fileName )
		self.assertEqual( os.path.isfile( fileName ), False )
		dispatcher.dispatch( [ s["b"] ] )
		shutil.rmtree( dispatcher.jobDirectory() )
		self.assertEqual( os.path.isfile( fileName ), True )
		with file( fileName, "r" ) as f :
			text = f.read()

		# all frames of n1, followed by the n3 sequence, followed by all frames of n2
		expectedText = "n1 on 2;n1 on 4;n1 on 6;n3 on 2;n3 on 4;n3 on 6;n2 on 2;n2 on 4;n2 on 6;"
		self.assertEqual( text, expectedText )

	def tearDown( self ) :

		shutil.rmtree( "/tmp/dispatcherTest", ignore_errors = True )

if __name__ == "__main__":
	unittest.main()

