##########################################################################
#
#  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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

class LocalDispatcherTest( GafferTest.TestCase ) :

	def setUp( self ) :

		localDispatcher = Gaffer.Dispatcher.dispatcher( "Local" )
		localDispatcher["jobsDirectory"].setValue( "/tmp/dispatcherTest" )
		localDispatcher["framesMode"].setValue( Gaffer.Dispatcher.FramesMode.CurrentFrame )

	def testDispatcherRegistration( self ) :

		self.failUnless( "Local" in Gaffer.Dispatcher.dispatcherNames() )
		self.failUnless( Gaffer.Dispatcher.dispatcher( "Local" ).isInstanceOf( Gaffer.LocalDispatcher.staticTypeId() ) )

	def testDispatch( self ) :

		dispatcher = Gaffer.Dispatcher.dispatcher( "Local" )
		fileName = "/tmp/dispatcherTest/result.txt"

		def createWriter( text ) :
			node = GafferTest.TextWriter()
			node["mode"].setValue( "a" )
			node["fileName"].setValue( fileName )
			node["text"].setValue( text + " on ${frame};" )
			return node

		# Create a tree of dependencies for execution:
		# n1 requires:
		# - n2 requires:
		#    -n2a
		#    -n2b
		s = Gaffer.ScriptNode()
		s["n1"] = createWriter( "n1" )
		s["n2"] = createWriter( "n2" )
		s["n2a"] = createWriter( "n2a" )
		s["n2b"] = createWriter( "n2b" )
		s["n1"]['requirements'][0].setInput( s["n2"]['requirement'] )
		s["n2"]['requirements'][0].setInput( s["n2a"]['requirement'] )
		s["n2"]['requirements'][1].setInput( s["n2b"]['requirement'] )

		# No files should exist yet
		self.assertEqual( os.path.isfile( fileName ), False )

		# Executing n1 should trigger execution of all of them
		dispatcher.dispatch( [ s["n1"] ] )
		self.assertEqual( os.path.isfile( fileName ), True )
		with file( fileName, "r" ) as f :
			text = f.read()
		expectedText = s.context().substitute( "n2a on ${frame};n2b on ${frame};n2 on ${frame};n1 on ${frame};" )
		self.assertEqual( text, expectedText )

		# Executing n1 and anything else, should be the same as just n1, but forcing n2b execution puts it before n2a
		os.remove( fileName )
		dispatcher.dispatch( [ s["n2b"], s["n1"] ] )
		self.assertEqual( os.path.isfile( fileName ), True )
		with file( fileName, "r" ) as f :
			text = f.read()
		expectedText = s.context().substitute( "n2b on ${frame};n2a on ${frame};n2 on ${frame};n1 on ${frame};" )
		self.assertEqual( text, expectedText )

		# Executing all nodes should be the same as just n1
		os.remove( fileName )
		dispatcher.dispatch( [ s["n2"], s["n2b"], s["n1"], s["n2a"] ] )
		self.assertEqual( os.path.isfile( fileName ), True )
		with file( fileName, "r" ) as f :
			text = f.read()
		expectedText = s.context().substitute( "n2a on ${frame};n2b on ${frame};n2 on ${frame};n1 on ${frame};" )
		self.assertEqual( text, expectedText )

		# Executing a sub-branch (n2) should only trigger execution in that branch
		os.remove( fileName )
		dispatcher.dispatch( [ s["n2"] ] )
		self.assertEqual( os.path.isfile( fileName ), True )
		with file( fileName, "r" ) as f :
			text = f.read()
		expectedText = s.context().substitute( "n2a on ${frame};n2b on ${frame};n2 on ${frame};" )
		self.assertEqual( text, expectedText )

		# Executing a leaf node, should not trigger other executions.
		os.remove( fileName )
		dispatcher.dispatch( [ s["n2b"] ] )
		self.assertEqual( os.path.isfile( fileName ), True )
		with file( fileName, "r" ) as f :
			text = f.read()
		expectedText = s.context().substitute( "n2b on ${frame};" )
		self.assertEqual( text, expectedText )

	def testDispatchDifferentFrame( self ) :

		s = Gaffer.ScriptNode()
		s["n1"] = GafferTest.TextWriter()
		s["n1"]["fileName"].setValue( "/tmp/dispatcherTest/n1_####.txt" )
		s["n1"]["text"].setValue( "n1 on ${frame}" )

		context = Gaffer.Context( s.context() )
		context.setFrame( s.context().getFrame() + 10 )

		with context :
			Gaffer.Dispatcher.dispatcher( "Local" ).dispatch( [ s["n1"] ] )

		fileName = context.substitute( s["n1"]["fileName"].getValue() )
		self.assertTrue( os.path.isfile( fileName ) )
		with file( fileName, "r" ) as f :
			text = f.read()
		self.assertEqual( text, "%s on %d" % ( s["n1"].getName(), context.getFrame() ) )

	def testDispatchFullRange( self ) :

		dispatcher = Gaffer.Dispatcher.dispatcher( "Local" )
		dispatcher["framesMode"].setValue( Gaffer.Dispatcher.FramesMode.FullRange )
		frameList = IECore.FrameList.parse( "5-7" )
		fileName = "/tmp/dispatcherTest/result.txt"

		def createWriter( text ) :
			node = GafferTest.TextWriter()
			node["mode"].setValue( "a" )
			node["fileName"].setValue( fileName )
			node["text"].setValue( text + " on ${frame};" )
			return node

		# Create a tree of dependencies for execution:
		# n1 requires:
		# - n2 requires:
		#    -n2a
		#    -n2b
		s = Gaffer.ScriptNode()
		s["frameRange"]["start"].setValue( 5 )
		s["frameRange"]["end"].setValue( 7 )
		s["n1"] = createWriter( "n1" )
		s["n2"] = createWriter( "n2" )
		s["n2a"] = createWriter( "n2a" )
		s["n2b"] = createWriter( "n2b" )
		s["n1"]['requirements'][0].setInput( s["n2"]['requirement'] )
		s["n2"]['requirements'][0].setInput( s["n2a"]['requirement'] )
		s["n2"]['requirements'][1].setInput( s["n2b"]['requirement'] )

		# No files should exist yet
		self.assertEqual( os.path.isfile( fileName ), False )

		# Executing n1 should trigger execution of all of them
		dispatcher.dispatch( [ s["n1"] ] )
		self.assertEqual( os.path.isfile( fileName ), True )
		with file( fileName, "r" ) as f :
			text = f.read()
		expectedText = ""
		for frame in frameList.asList() :
			context = Gaffer.Context( s.context() )
			context.setFrame( frame )
			expectedText += context.substitute( "n2a on ${frame};n2b on ${frame};n2 on ${frame};n1 on ${frame};" )
		self.assertEqual( text, expectedText )

		# Executing a leaf node, should not trigger other executions.
		os.remove( fileName )
		dispatcher.dispatch( [ s["n2b"] ] )
		self.assertEqual( os.path.isfile( fileName ), True )
		with file( fileName, "r" ) as f :
			text = f.read()
		expectedText = ""
		for frame in frameList.asList() :
			context = Gaffer.Context( s.context() )
			context.setFrame( frame )
			expectedText += context.substitute( "n2b on ${frame};" )
		self.assertEqual( text, expectedText )

	def testDispatchCustomRange( self ) :

		dispatcher = Gaffer.Dispatcher.dispatcher( "Local" )
		dispatcher["framesMode"].setValue( Gaffer.Dispatcher.FramesMode.CustomRange )
		frameList = IECore.FrameList.parse( "2-6x2" )
		dispatcher["frameRange"].setValue( str(frameList) )
		fileName = "/tmp/dispatcherTest/result.txt"

		def createWriter( text ) :
			node = GafferTest.TextWriter()
			node["mode"].setValue( "a" )
			node["fileName"].setValue( fileName )
			node["text"].setValue( text + " on ${frame};" )
			return node

		# Create a tree of dependencies for execution:
		# n1 requires:
		# - n2 requires:
		#    -n2a
		#    -n2b
		s = Gaffer.ScriptNode()
		s["n1"] = createWriter( "n1" )
		s["n2"] = createWriter( "n2" )
		s["n2a"] = createWriter( "n2a" )
		s["n2b"] = createWriter( "n2b" )
		s["n1"]['requirements'][0].setInput( s["n2"]['requirement'] )
		s["n2"]['requirements'][0].setInput( s["n2a"]['requirement'] )
		s["n2"]['requirements'][1].setInput( s["n2b"]['requirement'] )

		# No files should exist yet
		self.assertEqual( os.path.isfile( fileName ), False )

		# Executing n1 should trigger execution of all of them
		dispatcher.dispatch( [ s["n1"] ] )
		self.assertEqual( os.path.isfile( fileName ), True )
		with file( fileName, "r" ) as f :
			text = f.read()
		expectedText = ""
		for frame in frameList.asList() :
			context = Gaffer.Context( s.context() )
			context.setFrame( frame )
			expectedText += context.substitute( "n2a on ${frame};n2b on ${frame};n2 on ${frame};n1 on ${frame};" )
		self.assertEqual( text, expectedText )

		# Executing a leaf node, should not trigger other executions.
		os.remove( fileName )
		dispatcher.dispatch( [ s["n2b"] ] )
		self.assertEqual( os.path.isfile( fileName ), True )
		with file( fileName, "r" ) as f :
			text = f.read()
		expectedText = ""
		for frame in frameList.asList() :
			context = Gaffer.Context( s.context() )
			context.setFrame( frame )
			expectedText += context.substitute( "n2b on ${frame};" )
		self.assertEqual( text, expectedText )

	def testDispatchBadCustomRange( self ) :

		dispatcher = Gaffer.Dispatcher.dispatcher( "Local" )
		dispatcher["framesMode"].setValue( Gaffer.Dispatcher.FramesMode.CustomRange )
		dispatcher["frameRange"].setValue( "notAFrameRange" )

		s = Gaffer.ScriptNode()
		s["n1"] = GafferTest.TextWriter()
		s["n1"]["fileName"].setValue( "/tmp/dispatcherTest/n1_####.txt" )
		s["n1"]["text"].setValue( "n1 on ${frame}" )

		self.assertRaises( RuntimeError, dispatcher.dispatch, [ s["n1"] ] )
		self.assertFalse( os.path.isfile( s.context().substitute( s["n1"]["fileName"].getValue() ) ) )

	def testContextVariation( self ) :

		s = Gaffer.ScriptNode()
		context = Gaffer.Context( s.context() )
		context["script:name"] = "notTheRealScriptName"
		context["textWriter:replace"] = IECore.StringVectorData( [ " ", "\n" ] )

		s["n1"] = GafferTest.TextWriter()
		s["n1"]["fileName"].setValue( "/tmp/dispatcherTest/${script:name}_####.txt" )
		s["n1"]["text"].setValue( "${script:name} on ${frame}" )

		fileName = context.substitute( s["n1"]["fileName"].getValue() )
		self.assertFalse( os.path.isfile( fileName ) )

		with context :
			Gaffer.Dispatcher.dispatcher( "Local" ).dispatch( [ s["n1"] ] )

		self.assertTrue( os.path.isfile( fileName ) )
		self.assertTrue( os.path.basename( fileName ).startswith( context["script:name"] ) )
		with file( fileName, "r" ) as f :
			text = f.read()
		expected = "%s on %d" % ( context["script:name"], context.getFrame() )
		expected = expected.replace( context["textWriter:replace"][0], context["textWriter:replace"][1] )
		self.assertEqual( text, expected )

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

		s = Gaffer.ScriptNode()
		s["n1"] = GafferTest.TextWriter()
		s["n1"]["fileName"].setValue( "/tmp/dispatcherTest/n1_####.txt" )
		s["n1"]["text"].setValue( "n1 on ${frame}" )

		dispatcher = Gaffer.Dispatcher.dispatcher( "Local" )
		dispatcher.dispatch( [ s["n1"] ] )

		self.assertEqual( len( preCs ), 1 )
		self.failUnless( preCs[0][0].isSame( dispatcher ) )
		self.assertEqual( preCs[0][1], [ s["n1"] ] )

		self.assertEqual( len( postCs ), 1 )
		self.failUnless( postCs[0][0].isSame( dispatcher ) )
		self.assertEqual( postCs[0][1], [ s["n1"] ] )

	def testExecuteInBackground( self ) :

		preCs = GafferTest.CapturingSlot( Gaffer.LocalDispatcher.preDispatchSignal() )
		self.assertEqual( len( preCs ), 0 )
		postCs = GafferTest.CapturingSlot( Gaffer.LocalDispatcher.postDispatchSignal() )
		self.assertEqual( len( postCs ), 0 )

		s = Gaffer.ScriptNode()
		s["n1"] = GafferTest.TextWriter()
		s["n1"]["fileName"].setValue( "/tmp/dispatcherTest/n1_####.txt" )
		s["n1"]["text"].setValue( "n1 on ${frame}" )

		dispatcher = Gaffer.Dispatcher.dispatcher( "Local" )
		dispatcher["executeInBackground"].setValue( True )
		dispatcher.dispatch( [ s["n1"] ] )

		# the dispatching started and finished
		self.assertEqual( len( preCs ), 1 )
		self.assertEqual( len( postCs ), 1 )

		# but the execution hasn't finished yet
		self.assertFalse( os.path.isfile( s.context().substitute( s["n1"]["fileName"].getValue() ) ) )

		# wait long enough to finish execution
		import time; time.sleep( 2 )

		self.assertTrue( os.path.isfile( s.context().substitute( s["n1"]["fileName"].getValue() ) ) )

	def testMixedForegroundAndBackground( self ) :

		preCs = GafferTest.CapturingSlot( Gaffer.LocalDispatcher.preDispatchSignal() )
		self.assertEqual( len( preCs ), 0 )
		postCs = GafferTest.CapturingSlot( Gaffer.LocalDispatcher.postDispatchSignal() )
		self.assertEqual( len( postCs ), 0 )

		fileName = "/tmp/dispatcherTest/result.txt"

		def createWriter( text ) :
			node = GafferTest.TextWriter()
			node["mode"].setValue( "a" )
			node["fileName"].setValue( fileName )
			node["text"].setValue( text + " on ${frame};" )
			return node

		s = Gaffer.ScriptNode()
		# Create a tree of dependencies for execution:
		# n1 requires:
		# - n2 requires:
		#    -n2a
		#    -n2b
		# - n3
		s = Gaffer.ScriptNode()
		s["n1"] = createWriter( "n1" )
		s["n2"] = createWriter( "n2" )
		# force the entire n2 tree to execute in the foreground
		s["n2"]["dispatcher"]["local"]["executeInForeground"].setValue( True )
		s["n2a"] = createWriter( "n2a" )
		s["n2b"] = createWriter( "n2b" )
		s["n3"] = createWriter( "n3" )
		s["n1"]['requirements'][0].setInput( s["n2"]['requirement'] )
		s["n1"]['requirements'][1].setInput( s["n3"]['requirement'] )
		s["n2"]['requirements'][0].setInput( s["n2a"]['requirement'] )
		s["n2"]['requirements'][1].setInput( s["n2b"]['requirement'] )

		dispatcher = Gaffer.Dispatcher.dispatcher( "Local" )
		dispatcher["executeInBackground"].setValue( True )
		dispatcher["framesMode"].setValue( Gaffer.Dispatcher.FramesMode.CustomRange )
		frameList = IECore.FrameList.parse( "2-6x2" )
		dispatcher["frameRange"].setValue( str(frameList) )

		dispatcher.dispatch( [ s["n1"] ] )

		# the dispatching started and finished
		self.assertEqual( len( preCs ), 1 )
		self.assertEqual( len( postCs ), 1 )

		# all the foreground execution has finished
		self.assertEqual( os.path.isfile( fileName ), True )
		with file( fileName, "r" ) as f :
			text = f.read()
		expectedText = ""
		for frame in frameList.asList() :
			context = Gaffer.Context( s.context() )
			context.setFrame( frame )
			expectedText += context.substitute( "n2a on ${frame};n2b on ${frame};n2 on ${frame};" )
		self.assertEqual( text, expectedText )

		# wait long enough for background execution to finish
		import time; time.sleep( 12 )

		self.assertEqual( os.path.isfile( fileName ), True )
		with file( fileName, "r" ) as f :
			text = f.read()
		# don't reset the expectedText since we're still appending
		for frame in frameList.asList() :
			context = Gaffer.Context( s.context() )
			context.setFrame( frame )
			expectedText += context.substitute( "n3 on ${frame};n1 on ${frame};" )
		self.assertEqual( text, expectedText )

	def tearDown( self ) :

		shutil.rmtree( "/tmp/dispatcherTest", ignore_errors = True )

if __name__ == "__main__":
	unittest.main()

