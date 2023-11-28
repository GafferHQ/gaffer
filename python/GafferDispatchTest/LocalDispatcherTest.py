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

import errno
import os
import stat
import shutil
import unittest
import time
import inspect
import functools
import subprocess
import sys
import tempfile
import threading
import weakref

import imath

import IECore

import Gaffer
import GafferTest
import GafferDispatch
import GafferDispatchTest

class LocalDispatcherTest( GafferTest.TestCase ) :

	def __createLocalDispatcher( self, jobPool = None ) :

		if jobPool is None :
			# By default we run each test with its own JobPool,
			# to avoid polluting the default pool, and having
			# that spill from one test to the next.
			jobPool = GafferDispatch.LocalDispatcher.JobPool()

		result = GafferDispatch.LocalDispatcher( jobPool = jobPool )
		result["jobsDirectory"].setValue( self.temporaryDirectory() )
		return result

	def testDispatcherRegistration( self ) :

		self.assertIn( "Local", GafferDispatch.Dispatcher.registeredDispatchers() )
		self.assertIsInstance( GafferDispatch.Dispatcher.create( "Local" ), GafferDispatch.LocalDispatcher )

	def testDispatch( self ) :

		dispatcher = self.__createLocalDispatcher()
		fileName = self.temporaryDirectory() / "result.txt"

		def createWriter( text ) :
			node = GafferDispatchTest.TextWriter()
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
		s["n1"]["preTasks"][0].setInput( s["n2"]["task"] )
		s["n2"]["preTasks"][0].setInput( s["n2a"]["task"] )
		s["n2"]["preTasks"][1].setInput( s["n2b"]["task"] )

		# No files should exist yet
		self.assertFalse( fileName.is_file() )

		# Executing n1 should trigger execution of all of them
		dispatcher.dispatch( [ s["n1"] ] )
		self.assertTrue( fileName.is_file() )
		with open( fileName, "r", encoding = "utf-8" ) as f :
			text = f.read()
		expectedText = s.context().substitute( "n2a on ${frame};n2b on ${frame};n2 on ${frame};n1 on ${frame};" )
		self.assertEqual( text, expectedText )

		# Executing n1 and anything else, should be the same as just n1, but forcing n2b execution puts it before n2a
		fileName.unlink()
		dispatcher.dispatch( [ s["n2b"], s["n1"] ] )
		self.assertTrue( fileName.is_file() )
		with open( fileName, "r", encoding = "utf-8" ) as f :
			text = f.read()
		expectedText = s.context().substitute( "n2b on ${frame};n2a on ${frame};n2 on ${frame};n1 on ${frame};" )
		self.assertEqual( text, expectedText )

		# Executing all nodes should be the same as just n1
		fileName.unlink()
		dispatcher.dispatch( [ s["n2"], s["n2b"], s["n1"], s["n2a"] ] )
		self.assertTrue( fileName.is_file() )
		with open( fileName, "r", encoding = "utf-8" ) as f :
			text = f.read()
		expectedText = s.context().substitute( "n2a on ${frame};n2b on ${frame};n2 on ${frame};n1 on ${frame};" )
		self.assertEqual( text, expectedText )

		# Executing a sub-branch (n2) should only trigger execution in that branch
		fileName.unlink()
		dispatcher.dispatch( [ s["n2"] ] )
		self.assertTrue( fileName.is_file() )
		with open( fileName, "r", encoding = "utf-8" ) as f :
			text = f.read()
		expectedText = s.context().substitute( "n2a on ${frame};n2b on ${frame};n2 on ${frame};" )
		self.assertEqual( text, expectedText )

		# Executing a leaf node, should not trigger other executions.
		fileName.unlink()
		dispatcher.dispatch( [ s["n2b"] ] )
		self.assertTrue( fileName.is_file() )
		with open( fileName, "r", encoding = "utf-8" ) as f :
			text = f.read()
		expectedText = s.context().substitute( "n2b on ${frame};" )
		self.assertEqual( text, expectedText )

	def testDispatchDifferentFrame( self ) :

		s = Gaffer.ScriptNode()
		s["n1"] = GafferDispatchTest.TextWriter()
		s["n1"]["fileName"].setValue( self.temporaryDirectory() / "n1_####.txt" )
		s["n1"]["text"].setValue( "n1 on ${frame}" )

		context = Gaffer.Context( s.context() )
		context.setFrame( s.context().getFrame() + 10 )

		with context :
			self.__createLocalDispatcher().dispatch( [ s["n1"] ] )

		fileName = context.substitute( s["n1"]["fileName"].getValue() )
		self.assertTrue( os.path.isfile( fileName ) )
		with open( fileName, "r", encoding = "utf-8" ) as f :
			text = f.read()
		self.assertEqual( text, "%s on %d" % ( s["n1"].getName(), context.getFrame() ) )

	def testDispatchFullRange( self ) :

		dispatcher = self.__createLocalDispatcher()
		dispatcher["framesMode"].setValue( GafferDispatch.Dispatcher.FramesMode.FullRange )
		frameList = IECore.FrameList.parse( "5-7" )
		fileName = self.temporaryDirectory() / "result.txt"

		def createWriter( text ) :
			node = GafferDispatchTest.TextWriter()
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
		s["n1"]["preTasks"][0].setInput( s["n2"]["task"] )
		s["n2"]["preTasks"][0].setInput( s["n2a"]["task"] )
		s["n2"]["preTasks"][1].setInput( s["n2b"]["task"] )

		# No files should exist yet
		self.assertFalse( fileName.is_file() )

		# Executing n1 should trigger execution of all of them
		dispatcher.dispatch( [ s["n1"] ] )
		self.assertTrue( fileName.is_file() )
		with open( fileName, "r", encoding = "utf-8" ) as f :
			text = f.read()
		expectedText = ""
		for frame in frameList.asList() :
			context = Gaffer.Context( s.context() )
			context.setFrame( frame )
			expectedText += context.substitute( "n2a on ${frame};n2b on ${frame};n2 on ${frame};n1 on ${frame};" )
		self.assertEqual( text, expectedText )

		# Executing a leaf node, should not trigger other executions.
		fileName.unlink()
		dispatcher.dispatch( [ s["n2b"] ] )
		self.assertTrue( fileName.is_file() )
		with open( fileName, "r", encoding = "utf-8" ) as f :
			text = f.read()
		expectedText = ""
		for frame in frameList.asList() :
			context = Gaffer.Context( s.context() )
			context.setFrame( frame )
			expectedText += context.substitute( "n2b on ${frame};" )
		self.assertEqual( text, expectedText )

	def testDispatchCustomRange( self ) :

		dispatcher = self.__createLocalDispatcher()
		dispatcher["framesMode"].setValue( GafferDispatch.Dispatcher.FramesMode.CustomRange )
		frameList = IECore.FrameList.parse( "2-6x2" )
		dispatcher["frameRange"].setValue( str(frameList) )
		fileName = self.temporaryDirectory() / "result.txt"

		def createWriter( text ) :
			node = GafferDispatchTest.TextWriter()
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
		s["n1"]["preTasks"][0].setInput( s["n2"]["task"] )
		s["n2"]["preTasks"][0].setInput( s["n2a"]["task"] )
		s["n2"]["preTasks"][1].setInput( s["n2b"]["task"] )

		# No files should exist yet
		self.assertFalse( fileName.is_file() )

		# Executing n1 should trigger execution of all of them
		dispatcher.dispatch( [ s["n1"] ] )
		self.assertTrue( fileName.is_file() )
		with open( fileName, "r", encoding = "utf-8" ) as f :
			text = f.read()
		expectedText = ""
		for frame in frameList.asList() :
			context = Gaffer.Context( s.context() )
			context.setFrame( frame )
			expectedText += context.substitute( "n2a on ${frame};n2b on ${frame};n2 on ${frame};n1 on ${frame};" )
		self.assertEqual( text, expectedText )

		# Executing a leaf node, should not trigger other executions.
		fileName.unlink()
		dispatcher.dispatch( [ s["n2b"] ] )
		self.assertTrue( fileName.is_file() )
		with open( fileName, "r", encoding = "utf-8" ) as f :
			text = f.read()
		expectedText = ""
		for frame in frameList.asList() :
			context = Gaffer.Context( s.context() )
			context.setFrame( frame )
			expectedText += context.substitute( "n2b on ${frame};" )
		self.assertEqual( text, expectedText )

	def testDispatchBadCustomRange( self ) :

		dispatcher = self.__createLocalDispatcher()
		dispatcher["framesMode"].setValue( GafferDispatch.Dispatcher.FramesMode.CustomRange )
		dispatcher["frameRange"].setValue( "notAFrameRange" )

		s = Gaffer.ScriptNode()
		s["n1"] = GafferDispatchTest.TextWriter()
		s["n1"]["fileName"].setValue( self.temporaryDirectory() / "n1_####.txt" )
		s["n1"]["text"].setValue( "n1 on ${frame}" )

		self.assertRaises( RuntimeError, dispatcher.dispatch, [ s["n1"] ] )
		self.assertFalse( os.path.isfile( s.context().substitute( s["n1"]["fileName"].getValue() ) ) )

	def testContextVariation( self ) :

		s = Gaffer.ScriptNode()
		context = Gaffer.Context( s.context() )
		context["script:name"] = "notTheRealScriptName"
		context["textWriter:replace"] = IECore.StringVectorData( [ " ", "\n" ] )

		s["n1"] = GafferDispatchTest.TextWriter()
		s["n1"]["fileName"].setValue( self.temporaryDirectory() / "${script:name}_####.txt" )
		s["n1"]["text"].setValue( "${script:name} on ${frame}" )

		fileName = context.substitute( s["n1"]["fileName"].getValue() )
		self.assertFalse( os.path.isfile( fileName ) )

		with context :
			self.__createLocalDispatcher().dispatch( [ s["n1"] ] )

		self.assertTrue( os.path.isfile( fileName ) )
		self.assertTrue( os.path.basename( fileName ).startswith( context["script:name"] ) )
		with open( fileName, "r", encoding = "utf-8" ) as f :
			text = f.read()
		expected = "%s on %d" % ( context["script:name"], context.getFrame() )
		expected = expected.replace( context["textWriter:replace"][0], context["textWriter:replace"][1] )
		self.assertEqual( text, expected )

	def testDispatcherSignals( self ) :

		preCs = GafferTest.CapturingSlot( GafferDispatch.Dispatcher.preDispatchSignal() )
		self.assertEqual( len( preCs ), 0 )
		dispatchCs = GafferTest.CapturingSlot( GafferDispatch.Dispatcher.preDispatchSignal() )
		self.assertEqual( len( dispatchCs ), 0 )
		postCs = GafferTest.CapturingSlot( GafferDispatch.Dispatcher.postDispatchSignal() )
		self.assertEqual( len( postCs ), 0 )

		s = Gaffer.ScriptNode()
		s["n1"] = GafferDispatchTest.TextWriter()
		s["n1"]["fileName"].setValue( self.temporaryDirectory() / "n1_####.txt" )
		s["n1"]["text"].setValue( "n1 on ${frame}" )

		dispatcher = self.__createLocalDispatcher()
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

	def testExecuteInBackground( self ) :

		preCs = GafferTest.CapturingSlot( GafferDispatch.LocalDispatcher.preDispatchSignal() )
		self.assertEqual( len( preCs ), 0 )
		dispatchCs = GafferTest.CapturingSlot( GafferDispatch.LocalDispatcher.dispatchSignal() )
		self.assertEqual( len( dispatchCs ), 0 )
		postCs = GafferTest.CapturingSlot( GafferDispatch.LocalDispatcher.postDispatchSignal() )
		self.assertEqual( len( postCs ), 0 )

		s = Gaffer.ScriptNode()
		s["n1"] = GafferDispatchTest.TextWriter()
		s["n1"]["fileName"].setValue( self.temporaryDirectory() / "n1_####.txt" )
		s["n1"]["text"].setValue( "n1 on ${frame}" )

		dispatcher = self.__createLocalDispatcher()
		dispatcher["executeInBackground"].setValue( True )
		dispatcher.dispatch( [ s["n1"] ] )

		# the dispatching started and finished
		self.assertEqual( len( preCs ), 1 )
		self.assertEqual( len( dispatchCs ), 1 )
		self.assertEqual( len( postCs ), 1 )

		# but the execution hasn't finished yet
		self.assertFalse( os.path.isfile( s.context().substitute( s["n1"]["fileName"].getValue() ) ) )

		# wait long enough to finish execution
		dispatcher.jobPool().waitForAll()
		self.assertEqual( len( dispatcher.jobPool().jobs() ), 1 )
		self.assertEqual( dispatcher.jobPool().jobs()[0].status(), GafferDispatch.LocalDispatcher.Job.Status.Complete )

		self.assertTrue( os.path.isfile( s.context().substitute( s["n1"]["fileName"].getValue() ) ) )

	def testMixedImmediateAndBackground( self ) :

		preCs = GafferTest.CapturingSlot( GafferDispatch.LocalDispatcher.preDispatchSignal() )
		self.assertEqual( len( preCs ), 0 )
		dispatchCs = GafferTest.CapturingSlot( GafferDispatch.LocalDispatcher.dispatchSignal() )
		self.assertEqual( len( dispatchCs ), 0 )
		postCs = GafferTest.CapturingSlot( GafferDispatch.LocalDispatcher.postDispatchSignal() )
		self.assertEqual( len( postCs ), 0 )

		fileName = self.temporaryDirectory() / "result.txt"

		def createWriter( text ) :
			node = GafferDispatchTest.TextWriter()
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
		s["n2"]["dispatcher"]["immediate"].setValue( True )
		s["n2a"] = createWriter( "n2a" )
		s["n2b"] = createWriter( "n2b" )
		s["n3"] = createWriter( "n3" )
		s["n1"]["preTasks"][0].setInput( s["n2"]["task"] )
		s["n1"]["preTasks"][1].setInput( s["n3"]["task"] )
		s["n2"]["preTasks"][0].setInput( s["n2a"]["task"] )
		s["n2"]["preTasks"][1].setInput( s["n2b"]["task"] )

		dispatcher = self.__createLocalDispatcher()
		dispatcher["executeInBackground"].setValue( True )
		dispatcher["framesMode"].setValue( GafferDispatch.Dispatcher.FramesMode.CustomRange )
		frameList = IECore.FrameList.parse( "2-6x2" )
		dispatcher["frameRange"].setValue( str(frameList) )

		dispatcher.dispatch( [ s["n1"] ] )

		# the dispatching started and finished
		self.assertEqual( len( preCs ), 1 )
		self.assertEqual( len( dispatchCs ), 1 )
		self.assertEqual( len( postCs ), 1 )

		# all the foreground execution has finished
		self.assertTrue( fileName.is_file() )
		with open( fileName, "r", encoding = "utf-8" ) as f :
			text = f.read()
		expectedText = ""
		for frame in frameList.asList() :
			context = Gaffer.Context( s.context() )
			context.setFrame( frame )
			expectedText += context.substitute( "n2a on ${frame};n2b on ${frame};n2 on ${frame};" )
		self.assertEqual( text, expectedText )

		# wait long enough for background execution to finish
		dispatcher.jobPool().waitForAll()
		self.assertEqual( len( dispatcher.jobPool().jobs() ), 1 )
		self.assertEqual( dispatcher.jobPool().jobs()[0].status(), GafferDispatch.LocalDispatcher.Job.Status.Complete )

		self.assertTrue( fileName.is_file() )
		with open( fileName, "r", encoding = "utf-8" ) as f :
			text = f.read()
		# don't reset the expectedText since we're still appending
		for frame in frameList.asList() :
			context = Gaffer.Context( s.context() )
			context.setFrame( frame )
			expectedText += context.substitute( "n3 on ${frame};n1 on ${frame};" )
		self.assertEqual( text, expectedText )

	def testMultipleDispatchers( self ) :

		s = Gaffer.ScriptNode()
		s["n1"] = GafferDispatchTest.TextWriter()
		s["n1"]["fileName"].setValue( self.temporaryDirectory() / "n1_####.txt" )
		s["n1"]["text"].setValue( "n1 on ${frame}" )

		jobPool = GafferDispatch.LocalDispatcher.JobPool()

		dispatcher = self.__createLocalDispatcher( jobPool )
		dispatcher["executeInBackground"].setValue( True )
		dispatcher2 = self.__createLocalDispatcher( jobPool )
		dispatcher2["executeInBackground"].setValue( True )
		dispatcher.dispatch( [ s["n1"] ] )
		c = s.context()
		c.setFrame( 2 )
		with c :
			dispatcher2.dispatch( [ s["n1"] ] )

		# wait long enough for background execution to finish
		self.assertEqual( len( jobPool.jobs() ), 2 )
		dispatcher.jobPool().waitForAll()
		self.assertEqual( len( jobPool.jobs() ), 2 )
		self.assertEqual(
			[ j.status() for j in jobPool.jobs() ],
			[ GafferDispatch.LocalDispatcher.Job.Status.Complete ] * 2
		)

		self.assertTrue( os.path.isfile( s.context().substitute( s["n1"]["fileName"].getValue() ) ) )
		self.assertTrue( os.path.isfile( c.substitute( s["n1"]["fileName"].getValue() ) ) )

	def testFailure( self ) :

		s = Gaffer.ScriptNode()
		s["n1"] = GafferDispatchTest.TextWriter()
		s["n1"]["fileName"].setValue( self.temporaryDirectory() / "n1_####.txt" )
		s["n1"]["text"].setValue( "n1 on ${frame}" )
		s["n2"] = GafferDispatchTest.TextWriter()
		s["n2"]["fileName"].setValue( "" )
		s["n2"]["text"].setValue( "n2 on ${frame}" )
		s["n3"] = GafferDispatchTest.TextWriter()
		s["n3"]["fileName"].setValue( self.temporaryDirectory() / "n3_####.txt" )
		s["n3"]["text"].setValue( "n3 on ${frame}" )
		s["n1"]["preTasks"][0].setInput( s["n2"]["task"] )
		s["n2"]["preTasks"][0].setInput( s["n3"]["task"] )

		dispatcher = self.__createLocalDispatcher()

		# fails because n2 doesn't have a valid fileName
		self.assertRaisesRegex( RuntimeError, "No such file or directory", functools.partial( dispatcher.dispatch, [ s["n1"] ] ) )
		self.assertEqual( len( dispatcher.jobPool().jobs() ), 1 )
		self.assertEqual(
			dispatcher.jobPool().jobs()[0].status(),
			GafferDispatch.LocalDispatcher.Job.Status.Failed
		)

		# n3 executed correctly
		self.assertTrue( os.path.isfile( s.context().substitute( s["n3"]["fileName"].getValue() ) ) )
		with open( s.context().substitute( s["n3"]["fileName"].getValue() ), "r", encoding = "utf-8" ) as f :
			text = f.read()
		self.assertEqual( text, "n3 on %d" % s.context().getFrame() )

		# n2 failed, so n1 never executed
		self.assertFalse( os.path.isfile( s.context().substitute( s["n2"]["fileName"].getValue() ) ) )
		self.assertFalse( os.path.isfile( s.context().substitute( s["n1"]["fileName"].getValue() ) ) )

		self.tearDown()

		dispatcher["executeInBackground"].setValue( True )
		dispatcher.dispatch( [ s["n1"] ] )

		# wait long enough for background execution to finish
		dispatcher.jobPool().waitForAll()
		self.assertEqual( len( dispatcher.jobPool().jobs() ), 2 )
		self.assertEqual(
			dispatcher.jobPool().jobs()[1].status(),
			GafferDispatch.LocalDispatcher.Job.Status.Failed
		)

		# n3 executed correctly
		self.assertTrue( os.path.isfile( s.context().substitute( s["n3"]["fileName"].getValue() ) ) )
		with open( s.context().substitute( s["n3"]["fileName"].getValue() ), "r", encoding = "utf-8" ) as f :
			text = f.read()
		self.assertEqual( text, "n3 on %d" % s.context().getFrame() )

		# n2 failed, so n1 never executed
		self.assertFalse( os.path.isfile( s.context().substitute( s["n2"]["fileName"].getValue() ) ) )
		self.assertFalse( os.path.isfile( s.context().substitute( s["n1"]["fileName"].getValue() ) ) )

	def testKill( self ) :

		s = Gaffer.ScriptNode()
		s["n1"] = GafferDispatchTest.TextWriter()
		s["n1"]["fileName"].setValue( self.temporaryDirectory() / "n1_####.txt" )
		s["n1"]["text"].setValue( "n1 on ${frame}" )

		dispatcher = self.__createLocalDispatcher()
		dispatcher["executeInBackground"].setValue( True )

		self.assertEqual( len(dispatcher.jobPool().jobs()), 0 )
		dispatcher.dispatch( [ s["n1"] ] )
		self.assertEqual( len(dispatcher.jobPool().jobs()), 1 )

		# the execution hasn't finished yet
		self.assertFalse( os.path.isfile( s.context().substitute( s["n1"]["fileName"].getValue() ) ) )

		# kill the job
		dispatcher.jobPool().jobs()[0].kill()

		# wait long enough for the process to die
		dispatcher.jobPool().waitForAll()
		self.assertEqual( len( dispatcher.jobPool().jobs() ), 1 )
		self.assertEqual( dispatcher.jobPool().jobs()[0].status(), GafferDispatch.LocalDispatcher.Job.Status.Killed )

		# make sure it never wrote the file
		self.assertFalse( os.path.isfile( s.context().substitute( s["n1"]["fileName"].getValue() ) ) )

	def testSpacesInContext( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = GafferDispatchTest.TextWriter()
		s["n"]["fileName"].setValue( self.temporaryDirectory() / "test.txt" )
		s["n"]["text"].setValue( "${test}" )

		dispatcher = self.__createLocalDispatcher()
		dispatcher["executeInBackground"].setValue( True )

		c = Gaffer.Context()
		c["test"] = "i am a string with spaces"

		with c :
			dispatcher.dispatch( [ s["n"] ] )

		dispatcher.jobPool().waitForAll()

		text = "".join( open( self.temporaryDirectory() / "test.txt", encoding = "utf-8" ).readlines() )
		self.assertEqual( text, "i am a string with spaces" )

	def testUIContextEntriesIgnored( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferDispatchTest.TextWriter()
		s["n"]["fileName"].setValue( self.temporaryDirectory() / "out.txt" )
		s["n"]["text"].setValue( "${foo} ${ui:foo}" )

		dispatcher = self.__createLocalDispatcher()
		dispatcher["executeInBackground"].setValue( True )

		c = Gaffer.Context()
		c["ui:foo"] = "uiFoo"
		c["foo"] = "foo"

		with c :
			dispatcher.dispatch( [ s["n"] ] )

		dispatcher.jobPool().waitForAll()

		text = "".join( open( self.temporaryDirectory() / "out.txt", encoding = "utf-8" ).readlines() )
		self.assertEqual( text, "foo " )

	def testContextLockedDuringBackgroundDispatch( self ) :

		fileName = self.temporaryDirectory() / "out.txt"

		s = Gaffer.ScriptNode()
		s["n1"] = GafferDispatchTest.TextWriter()
		s["n1"]["fileName"].setValue( fileName )
		s["n1"]["text"].setValue( "n1 on ${frame} with ${foo}" )

		dispatcher = self.__createLocalDispatcher()
		dispatcher["executeInBackground"].setValue( True )

		c = Gaffer.Context( s.context() )
		c["foo"] = "foo"

		with c :
			dispatcher.dispatch( [ s["n1"] ] )

		self.assertFalse( fileName.is_file() )

		foo = s["variables"].addChild( Gaffer.NameValuePlug( "foo", IECore.StringData( "foo" ) ) )

		dispatcher.jobPool().waitForAll()

		self.assertTrue( fileName.is_file() )

		text = "".join( open( fileName, encoding = "utf-8" ).readlines() )
		self.assertEqual( text, "n1 on 1 with foo" )

	def testNodeNamesLockedDuringBackgroundDispatch( self ) :

		fileName = self.temporaryDirectory() / "out.txt"

		s = Gaffer.ScriptNode()
		s["n1"] = GafferDispatchTest.TextWriter()
		s["n1"]["fileName"].setValue( fileName )
		s["n1"]["text"].setValue( "n1 on ${frame}" )

		dispatcher = self.__createLocalDispatcher()
		dispatcher["executeInBackground"].setValue( True )
		dispatcher.dispatch( [ s["n1"] ] )

		self.assertFalse( fileName.is_file() )

		s["n1"].setName( "n2" )

		dispatcher.jobPool().waitForAll()

		self.assertTrue( fileName.is_file() )

		text = "".join( open( fileName, encoding = "utf-8" ).readlines() )
		self.assertEqual( text, "n1 on 1" )

	def testIgnoreScriptLoadErrors( self ) :

		fileName = self.temporaryDirectory() / "scriptLoadErrorTest.txt"

		s = Gaffer.ScriptNode()
		s["n"] = GafferDispatchTest.TextWriter()
		s["n"]["fileName"].setValue( fileName )
		s["n"]["text"].setValue( "test" )

		# because this doesn't have the dynamic flag set,
		# it won't serialise/load properly.
		s["n"]["user"]["badPlug"] = Gaffer.IntPlug()
		s["n"]["user"]["badPlug"].setValue( 10 )

		dispatcher = self.__createLocalDispatcher()
		dispatcher["executeInBackground"].setValue( True )

		dispatcher.dispatch( [ s["n"] ] )
		dispatcher.jobPool().waitForAll()

		self.assertFalse( fileName.is_file() )

		dispatcher["ignoreScriptLoadErrors"].setValue( True )
		dispatcher.dispatch( [ s["n"] ] )
		dispatcher.jobPool().waitForAll()

		self.assertTrue( fileName.is_file() )

	def testBackgroundBatchesCanAccessJobDirectory( self ) :

		s = Gaffer.ScriptNode()

		s["w"] = GafferDispatchTest.TextWriter()
		s["w"]["fileName"].setValue( "${dispatcher:jobDirectory}/test.####.txt" )
		s["w"]["text"].setValue( "w on ${frame} from ${dispatcher:jobDirectory}" )

		dispatcher = self.__createLocalDispatcher()
		dispatcher["executeInBackground"].setValue( True )
		dispatcher["framesMode"].setValue( GafferDispatch.Dispatcher.FramesMode.CustomRange )
		frameList = IECore.FrameList.parse( "2-6x2" )
		dispatcher["frameRange"].setValue( str(frameList) )
		dispatcher.dispatch( [ s["w"] ] )
		dispatcher.jobPool().waitForAll()

		# a single dispatch should have the same job directory for all batches
		jobDir = dispatcher["jobsDirectory"].getValue() + "/000000"
		self.assertEqual( next( open( "%s/test.0002.txt" % jobDir, encoding = "utf-8" ) ), "w on 2 from %s" % jobDir )
		self.assertEqual( next( open( "%s/test.0004.txt" % jobDir, encoding = "utf-8" ) ), "w on 4 from %s" % jobDir )
		self.assertEqual( next( open( "%s/test.0006.txt" % jobDir, encoding = "utf-8" ) ), "w on 6 from %s" % jobDir )

	def testEnvironmentCommand( self ) :

		s = Gaffer.ScriptNode()

		testFile = self.temporaryDirectory() / "test"

		s["c"] = GafferDispatch.SystemCommand()
		if os.name != "nt" :
			s["c"]["command"].setValue( rf"echo HELLO \$GAFFERDISPATCHTEST_ENVVAR > {testFile}" )
		else :
			s["c"]["command"].setValue( "echo HELLO %GAFFERDISPATCHTEST_ENVVAR%> " + testFile.as_posix() )

		dispatcher = self.__createLocalDispatcher()
		dispatcher["executeInBackground"].setValue( True )
		dispatcher["framesMode"].setValue( GafferDispatch.Dispatcher.FramesMode.CurrentFrame )
		dispatcher.dispatch( [ s["c"] ] )
		dispatcher.jobPool().waitForAll()

		with open( testFile, encoding = "utf-8" ) as f :
			self.assertEqual( f.readlines(), [ "HELLO\n" if os.name != "nt" else "HELLO %GAFFERDISPATCHTEST_ENVVAR%\n" ] )

		if os.name != "nt" :
			dispatcher["environmentCommand"].setValue( "env GAFFERDISPATCHTEST_ENVVAR=WORLD" )
		else :
			dispatcher["environmentCommand"].setValue( "set GAFFERDISPATCHTEST_ENVVAR=WORLD&" )
		dispatcher.dispatch( [ s["c"] ] )
		dispatcher.jobPool().waitForAll()

		with open( testFile, encoding = "utf-8" ) as f :
			self.assertEqual( f.readlines(), [ "HELLO WORLD\n" ] )

	def testEnvironmentCommandSubstitutions( self ) :

		s = Gaffer.ScriptNode()

		testFile = self.temporaryDirectory() / "test"

		s["c"] = GafferDispatch.SystemCommand()
		if os.name != "nt" :
			s["c"]["command"].setValue( rf"echo HELLO \$GAFFERDISPATCHTEST_ENVVAR > {testFile}" )
		else :
			s["c"]["command"].setValue( "echo HELLO %GAFFERDISPATCHTEST_ENVVAR%> " + testFile.as_posix() )

		dispatcher = self.__createLocalDispatcher()
		dispatcher["executeInBackground"].setValue( True )
		dispatcher["framesMode"].setValue( GafferDispatch.Dispatcher.FramesMode.CurrentFrame )

		if os.name != "nt" :
			dispatcher["environmentCommand"].setValue( "env GAFFERDISPATCHTEST_ENVVAR=$world" )
		else :
			dispatcher["environmentCommand"].setValue( "set GAFFERDISPATCHTEST_ENVVAR=$world&" )

		with Gaffer.Context() as c :
			c["world"] = "WORLD"
			dispatcher.dispatch( [ s["c"] ] )

		dispatcher.jobPool().waitForAll()

		with open( testFile, encoding = "utf-8" ) as f :
			self.assertEqual( f.readlines(), [ "HELLO WORLD\n" ] )

	def testScaling( self ) :

		# See DispatcherTest.testScaling for details.

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

		d = self.__createLocalDispatcher()
		d["framesMode"].setValue( d.FramesMode.CustomRange )
		d["frameRange"].setValue( "1-1000" )

		t = time.process_time()
		d.dispatch( [ lastTask ] )
		timeLimit = 6
		if Gaffer.isDebug():
			timeLimit *= 2
		self.assertLess( time.process_time() - t, timeLimit )

		d["executeInBackground"].setValue( True )

		d.dispatch( [ lastTask ] )

		t = time.process_time()
		d.jobPool().jobs()[-1].kill()
		self.assertLess( time.process_time() - t, 1 )

		d.jobPool().waitForAll()

	def testImathContextVariable( self ) :

		s = Gaffer.ScriptNode()

		s["t"] = GafferDispatchTest.TextWriter()
		s["t"]["fileName"].setValue( self.temporaryDirectory() / "test.txt" )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( inspect.cleandoc(
			"""
			c = context["c"]
			parent["t"]["text"] = "{0} {1} {2}".format( *c )
			"""
		) )

		s["v"] = GafferDispatch.TaskContextVariables()
		s["v"]["variables"].addChild( Gaffer.NameValuePlug( "c", imath.Color3f( 0, 1, 2 ) ) )
		s["v"]["preTasks"][0].setInput( s["t"]["task"] )

		d = self.__createLocalDispatcher()
		d["executeInBackground"].setValue( True )
		d.dispatch( [ s["v"] ] )
		d.jobPool().waitForAll()

		self.assertEqual(
			open( s["t"]["fileName"].getValue(), encoding = "utf-8" ).read(),
			"0.0 1.0 2.0"
		)

	def testNestedDispatchBorrowingOuterJobDirectory( self ) :

		s = Gaffer.ScriptNode()

		s["nestedTask"] = GafferDispatchTest.TextWriter()
		s["nestedTask"]["fileName"].setValue( self.temporaryDirectory() / "nested.txt" )
		s["nestedTask"]["text"].setValue( "${dispatcher:jobDirectory} : ${dispatcher:scriptFileName}" )

		s["dispatchTask"] = GafferDispatch.PythonCommand()
		s["dispatchTask"]["command"].setValue( inspect.cleandoc(
			"""
			import GafferDispatch
			dispatcher = GafferDispatch.LocalDispatcher( jobPool = GafferDispatch.LocalDispatcher.JobPool() )
			dispatcher.dispatch( [ self.parent()["nestedTask"] ] )
			"""
		) )

		s["outerTask"] = GafferDispatchTest.TextWriter()
		s["outerTask"]["preTasks"][0].setInput( s["dispatchTask"]["task"] )
		s["outerTask"]["fileName"].setValue( self.temporaryDirectory() / "outer.txt" )
		s["outerTask"]["text"].setValue( "${dispatcher:jobDirectory} : ${dispatcher:scriptFileName}" )

		d = self.__createLocalDispatcher()
		d["executeInBackground"].setValue( True )
		d.dispatch( [ s["outerTask"] ] )
		d.jobPool().waitForAll()

		self.assertTrue( ( self.temporaryDirectory() / "nested.txt" ).exists() )
		self.assertTrue( ( self.temporaryDirectory() / "outer.txt" ).exists() )

		self.assertEqual(
			open( self.temporaryDirectory() / "nested.txt", encoding = "utf-8" ).readlines(),
			open( self.temporaryDirectory() / "outer.txt", encoding = "utf-8" ).readlines(),
		)

	def testBackgroundJobFailureStatus( self ) :

		script = Gaffer.ScriptNode()

		script["pythonCommand"] = GafferDispatch.PythonCommand()
		script["pythonCommand"]["command"].setValue( "a = nonExistentVariable" )

		dispatcher = self.__createLocalDispatcher()
		dispatcher["executeInBackground"].setValue( True )

		dispatcher.dispatch( [ script["pythonCommand"] ] )
		dispatcher.jobPool().waitForAll()
		self.assertEqual(
			dispatcher.jobPool().jobs()[0].status(),
			GafferDispatch.LocalDispatcher.Job.Status.Failed
		)

	def testJobPoolSignals( self ) :

		dispatcher = self.__createLocalDispatcher()

		jobAddedSlot = GafferTest.CapturingSlot( dispatcher.jobPool().jobAddedSignal() )
		jobRemovedSlot = GafferTest.CapturingSlot( dispatcher.jobPool().jobRemovedSignal() )

		script = Gaffer.ScriptNode()
		script["taskNode"] = GafferDispatchTest.LoggingTaskNode()

		self.assertEqual( len( jobAddedSlot ), 0 )
		self.assertEqual( len( jobRemovedSlot ), 0 )

		dispatcher.dispatch( [ script["taskNode"] ] )

		self.assertEqual( len( jobAddedSlot ), 1 )
		job = jobAddedSlot[0][0]
		self.assertIsInstance( job, GafferDispatch.LocalDispatcher.Job )
		self.assertIs( job, dispatcher.jobPool().jobs()[0] )
		self.assertEqual( len( jobRemovedSlot ), 0 )

		dispatcher.jobPool().removeJob( job )
		self.assertEqual( len( jobAddedSlot ), 1 )
		self.assertEqual( len( jobRemovedSlot ), 1 )
		self.assertIs( jobRemovedSlot[0][0], job )

	def testJobStatusChangedSignal( self ) :

		# Create dispatcher and connect to signals

		dispatcher = self.__createLocalDispatcher()

		statusChanges = []
		def statusChanged( job ) :

			self.assertIs( threading.current_thread(), threading.main_thread() )
			# Job holds a reference to the `statusChanged()` function (via
			# `statusChangedSignal()`), and we hold a reference to the
			# `statusChanges` list. Use `weakref` to avoid creating a circular
			# reference back to the job.
			statusChanges.append( ( weakref.proxy( job ), job.status() ) )

		def jobAdded( job ) :

			job.statusChangedSignal().connect( statusChanged, scoped = False )

		dispatcher.jobPool().jobAddedSignal().connect( jobAdded, scoped = False )

		# Test foreground dispatch

		script = Gaffer.ScriptNode()
		script["taskNode"] = GafferDispatchTest.LoggingTaskNode()

		dispatcher.dispatch( [ script["taskNode"] ] )

		self.assertEqual(
			statusChanges,
			[
				( dispatcher.jobPool().jobs()[0], GafferDispatch.LocalDispatcher.Job.Status.Running ),
				( dispatcher.jobPool().jobs()[0], GafferDispatch.LocalDispatcher.Job.Status.Complete )
			]
		)

		# Test background dispatch

		dispatcher["executeInBackground"].setValue( True )
		del statusChanges[:]

		with GafferTest.ParallelAlgoTest.UIThreadCallHandler() as handler :
			dispatcher.dispatch( [ script["taskNode"] ] )
			handler.assertCalled()
			dispatcher.jobPool().waitForAll()

		self.assertEqual(
			statusChanges,
			[
				( dispatcher.jobPool().jobs()[1], GafferDispatch.LocalDispatcher.Job.Status.Running ),
				( dispatcher.jobPool().jobs()[1], GafferDispatch.LocalDispatcher.Job.Status.Complete )
			]
		)

	def testSubprocessMessages( self ) :

		script = Gaffer.ScriptNode()
		script["command"] = GafferDispatch.PythonCommand()
		script["command"]["command"].setValue( inspect.cleandoc(
			"""
			import sys
			sys.stderr.write( "Hello stderr!\\n" )
			sys.stdout.write( "Hello stdout!\\n" )
			"""
		) )

		dispatcher = self.__createLocalDispatcher()
		dispatcher["executeInBackground"].setValue( True )
		dispatcher.dispatch( [ script["command"] ] )
		dispatcher.jobPool().waitForAll()

		messages = dispatcher.jobPool().jobs()[0].messages()
		messages = { m.message for m in messages }
		self.assertIn( "Hello stderr!", messages )
		self.assertIn( "Hello stdout!", messages )

	def testShutdownDuringBackgroundDispatch( self ) :

		# Launch a subprocess that will launch a very long background task,
		# print out the PID of that task, and then exit before the task
		# has finished.

		output = subprocess.check_output(
			[ str( Gaffer.executablePath() ), "env", "python", "-c", "import GafferDispatchTest; GafferDispatchTest.LocalDispatcherTest._shutdownDuringBackgroundDispatch()" ],
			stderr = subprocess.STDOUT, text = True
		)

		# We want a prompt clean exit, with only the output we expect.

		self.assertRegex( output, "^PID : [0-9]+$" )
		pid = int( output.split( ":" )[-1].strip() )

		# And we want the process for the child task to have
		# been terminated.

		with self.assertRaises( OSError ) as check :
			os.kill( pid, 0 )

		self.assertEqual( check.exception.errno, errno.ESRCH ) # ESRCH means "no such process"

	@staticmethod
	def _shutdownDuringBackgroundDispatch() :

		script = Gaffer.ScriptNode()
		script["command"] = GafferDispatch.PythonCommand()
		script["command"]["command"].setValue( inspect.cleandoc(
			"""
			import time
			time.sleep( 1000000 )
			"""
		) )

		with tempfile.TemporaryDirectory() as jobDirectory :

			dispatcher = GafferDispatch.LocalDispatcher( jobPool = GafferDispatch.LocalDispatcher.JobPool() )
			dispatcher["jobsDirectory"].setValue( jobDirectory )
			dispatcher["executeInBackground"].setValue( True )
			dispatcher.dispatch( [ script["command"] ] )

			# Wait for background task to start, print its PID
			# to `stdout` and then exit.
			while True :
				s = dispatcher.jobPool().jobs()[-1].statistics()
				if "pid" in s :
					sys.stdout.write( "PID : {}\n".format( s["pid"] ) )
					sys.exit( 0 )

if __name__ == "__main__":
	unittest.main()
