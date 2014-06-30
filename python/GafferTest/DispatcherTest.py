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

import unittest

import IECore

import Gaffer
import GafferTest

class TestOp (IECore.Op) :

	def __init__( self, name, executionOrder ) :

		IECore.Op.__init__( self, "Test op", IECore.IntParameter( "result", "", 0 ) )
		self.parameters().addParameter( IECore.StringParameter( "currentFrame", "testing context substitution", "${frame}" ) )
		self.counter = 0
		self.frames = []
		self.name = name
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

		def _doDispatch( self, taskDescriptions ) :

			del self.log[:]
			for (task,requirements) in taskDescriptions :
				task.node().execute( [ task.context() ] )

		def _doSetupPlugs( self, parentPlug ) :

			parentPlug["testDispatcherPlug"] = Gaffer.IntPlug(
				direction = Gaffer.Plug.Direction.In,
				flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic
			)

	def setUp( self ) :

		if not "testDispatcher" in Gaffer.Dispatcher.dispatcherNames():
			IECore.registerRunTimeTyped( DispatcherTest.MyDispatcher )
			dispatcher = DispatcherTest.MyDispatcher()
			Gaffer.Dispatcher.registerDispatcher( "testDispatcher", dispatcher )

	def testDerivedClass( self ) :

		dispatcher = DispatcherTest.MyDispatcher()
		
		s = Gaffer.ScriptNode()
		op1 = TestOp("1", dispatcher.log)
		s["n1"] = Gaffer.ExecutableOpHolder()
		s["n1"].setParameterised( op1 )

		dispatcher.dispatch( [ s["n1"] ] )

		self.assertEqual( op1.counter, 1 )

	def testNoScript( self ) :
		
		dispatcher = DispatcherTest.MyDispatcher()
		
		op1 = TestOp("1", dispatcher.log)
		n1 = Gaffer.ExecutableOpHolder()
		n1.setParameterised( op1 )
		
		self.assertRaises( RuntimeError, dispatcher.dispatch, [ n1 ] )
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
		self.assertEqual( op1.counter, 0 )
		self.assertEqual( op2.counter, 0 )

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
		
		self.assertEqual( len( preCs ), 1 )
		self.failUnless( preCs[0][0].isSame( dispatcher ) )
		self.assertEqual( preCs[0][1], [ s["n1"] ] )

		self.assertEqual( len( postCs ), 1 )
		self.failUnless( postCs[0][0].isSame( dispatcher ) )
		self.assertEqual( postCs[0][1], [ s["n1"] ] )

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

		r1 = Gaffer.Plug( name = "r1" )
		s["n1"]['requirements'].addChild( r1 )
		r1.setInput( s["n2"]['requirement'] )

		r1 = Gaffer.Plug( name = "r1" )
		s["n2"]['requirements'].addChild( r1 )
		r1.setInput( s["n2a"]['requirement'] )
		
		r2 = Gaffer.Plug( name = "r2" )
		s["n2"]['requirements'].addChild( r2 )
		r2.setInput( s["n2b"]['requirement'] )

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
		
		self.assertEqual( op1.counter, 1 )
		self.assertEqual( op1.frames, [ context.getFrame() ] )
	
	def testDispatchScriptRange( self ) :
		
		dispatcher = DispatcherTest.MyDispatcher()
		dispatcher["framesMode"].setValue( Gaffer.Dispatcher.FramesMode.ScriptRange )
		
		s = Gaffer.ScriptNode()
		op1 = TestOp("1", dispatcher.log)
		s["n1"] = Gaffer.ExecutableOpHolder()
		s["n1"].setParameterised( op1 )
		
		dispatcher.dispatch( [ s["n1"] ] )
		
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

if __name__ == "__main__":
	unittest.main()
	
