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

import datetime
import errno
import gc
import os
import stat
import shutil
import unittest
import time
import inspect
import functools
import pathlib
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

	def tearDown( self ) :

		GafferTest.TestCase.tearDown( self )

		# Check for Jobs existing past their expected lifetime (most likely through circular references).
		self.assertEqual(
			[ o for o in gc.get_objects() if isinstance( o, GafferDispatch.LocalDispatcher.Job ) ],
			[]
		)

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
		s["dispatcher"] = self.__createLocalDispatcher()
		s["dispatcher"]["tasks"][0].setInput( s["n1"]["task"] )
		s["dispatcher"]["task"].execute()
		self.assertTrue( fileName.is_file() )
		with open( fileName, "r", encoding = "utf-8" ) as f :
			text = f.read()
		expectedText = s.context().substitute( "n2a on ${frame};n2b on ${frame};n2 on ${frame};n1 on ${frame};" )
		self.assertEqual( text, expectedText )

		# Executing n1 and anything else, should be the same as just n1, but forcing n2b execution puts it before n2a
		fileName.unlink()
		s["dispatcher"]["tasks"][0].setInput( s["n2b"]["task"] )
		s["dispatcher"]["tasks"][1].setInput( s["n1"]["task"] )
		s["dispatcher"]["task"].execute()
		self.assertTrue( fileName.is_file() )
		with open( fileName, "r", encoding = "utf-8" ) as f :
			text = f.read()
		expectedText = s.context().substitute( "n2b on ${frame};n2a on ${frame};n2 on ${frame};n1 on ${frame};" )
		self.assertEqual( text, expectedText )

		# Executing all nodes should be the same as just n1
		fileName.unlink()
		s["dispatcher"]["tasks"][0].setInput( s["n2"]["task"] )
		s["dispatcher"]["tasks"][1].setInput( s["n2b"]["task"] )
		s["dispatcher"]["tasks"][2].setInput( s["n1"]["task"] )
		s["dispatcher"]["tasks"][3].setInput( s["n2a"]["task"] )
		s["dispatcher"]["task"].execute()
		self.assertTrue( fileName.is_file() )
		with open( fileName, "r", encoding = "utf-8" ) as f :
			text = f.read()
		expectedText = s.context().substitute( "n2a on ${frame};n2b on ${frame};n2 on ${frame};n1 on ${frame};" )
		self.assertEqual( text, expectedText )

		# Executing a sub-branch (n2) should only trigger execution in that branch
		fileName.unlink()
		s["dispatcher"]["tasks"].resize( 1 )
		s["dispatcher"]["tasks"][0].setInput( s["n2"]["task"] )
		s["dispatcher"]["task"].execute()
		self.assertTrue( fileName.is_file() )
		with open( fileName, "r", encoding = "utf-8" ) as f :
			text = f.read()
		expectedText = s.context().substitute( "n2a on ${frame};n2b on ${frame};n2 on ${frame};" )
		self.assertEqual( text, expectedText )

		# Executing a leaf node, should not trigger other executions.
		fileName.unlink()
		s["dispatcher"]["tasks"][0].setInput( s["n2b"]["task"] )
		s["dispatcher"]["task"].execute()
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

		s["dispatcher"] = self.__createLocalDispatcher()
		s["dispatcher"]["tasks"][0].setInput( s["n1"]["task"] )

		context = Gaffer.Context( s.context() )
		context.setFrame( s.context().getFrame() + 10 )

		with context :
			s["dispatcher"]["task"].execute()

		fileName = context.substitute( s["n1"]["fileName"].getValue() )
		self.assertTrue( os.path.isfile( fileName ) )
		with open( fileName, "r", encoding = "utf-8" ) as f :
			text = f.read()
		self.assertEqual( text, "%s on %d" % ( s["n1"].getName(), context.getFrame() ) )

	def testDispatchFullRange( self ) :

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

		s["dispatcher"] = self.__createLocalDispatcher()
		s["dispatcher"]["framesMode"].setValue( GafferDispatch.Dispatcher.FramesMode.FullRange )
		s["dispatcher"]["tasks"][0].setInput( s["n1"]["task"] )
		s["dispatcher"]["task"].execute()
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
		s["dispatcher"]["tasks"][0].setInput( s["n2b"]["task"] )
		s["dispatcher"]["task"].execute()
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

		frameList = IECore.FrameList.parse( "2-6x2" )
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
		s["dispatcher"] = self.__createLocalDispatcher()
		s["dispatcher"]["framesMode"].setValue( GafferDispatch.Dispatcher.FramesMode.CustomRange )
		s["dispatcher"]["frameRange"].setValue( str(frameList) )

		s["dispatcher"]["tasks"][0].setInput( s["n1"]["task"] )
		s["dispatcher"]["task"].execute()
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
		s["dispatcher"]["tasks"][0].setInput( s["n2b"]["task"] )
		s["dispatcher"]["task"].execute()
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

		s = Gaffer.ScriptNode()
		s["n1"] = GafferDispatchTest.TextWriter()
		s["n1"]["fileName"].setValue( self.temporaryDirectory() / "n1_####.txt" )
		s["n1"]["text"].setValue( "n1 on ${frame}" )

		s["dispatcher"] = self.__createLocalDispatcher()
		s["dispatcher"]["framesMode"].setValue( GafferDispatch.Dispatcher.FramesMode.CustomRange )
		s["dispatcher"]["frameRange"].setValue( "notAFrameRange" )
		s["dispatcher"]["tasks"][0].setInput( s["n1"]["task"] )

		self.assertRaises( RuntimeError, s["dispatcher"]["task"].execute )
		self.assertFalse( os.path.isfile( s.context().substitute( s["n1"]["fileName"].getValue() ) ) )

	def testContextVariation( self ) :

		s = Gaffer.ScriptNode()
		context = Gaffer.Context( s.context() )
		context["script:name"] = "notTheRealScriptName"
		context["textWriter:replace"] = IECore.StringVectorData( [ " ", "\n" ] )

		s["n1"] = GafferDispatchTest.TextWriter()
		s["n1"]["fileName"].setValue( self.temporaryDirectory() / "${script:name}_####.txt" )
		s["n1"]["text"].setValue( "${script:name} on ${frame}" )

		s["dispatcher"] = self.__createLocalDispatcher()
		s["dispatcher"]["tasks"][0].setInput( s["n1"]["task"] )

		fileName = context.substitute( s["n1"]["fileName"].getValue() )
		self.assertFalse( os.path.isfile( fileName ) )

		with context :
			s["dispatcher"]["task"].execute()

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

		s["dispatcher"] = self.__createLocalDispatcher()
		s["dispatcher"]["tasks"][0].setInput( s["n1"]["task"] )
		s["dispatcher"]["task"].execute()

		self.assertEqual( len( preCs ), 1 )
		self.assertTrue( preCs[0][0].isSame( s["dispatcher"] ) )
		self.assertEqual( preCs[0][1], [ s["n1"] ] )

		self.assertEqual( len( dispatchCs ), 1 )
		self.assertTrue( dispatchCs[0][0].isSame( s["dispatcher"] ) )
		self.assertEqual( dispatchCs[0][1], [ s["n1"] ] )

		self.assertEqual( len( postCs ), 1 )
		self.assertTrue( postCs[0][0].isSame( s["dispatcher"] ) )
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

		s["dispatcher"] = self.__createLocalDispatcher()
		s["dispatcher"]["executeInBackground"].setValue( True )
		s["dispatcher"]["tasks"][0].setInput( s["n1"]["task"] )
		s["dispatcher"]["task"].execute()

		# the dispatching started and finished
		self.assertEqual( len( preCs ), 1 )
		self.assertEqual( len( dispatchCs ), 1 )
		self.assertEqual( len( postCs ), 1 )

		# but the execution hasn't finished yet
		self.assertFalse( os.path.isfile( s.context().substitute( s["n1"]["fileName"].getValue() ) ) )

		# wait long enough to finish execution
		s["dispatcher"].jobPool().waitForAll()
		self.assertEqual( len( s["dispatcher"].jobPool().jobs() ), 1 )
		self.assertEqual( s["dispatcher"].jobPool().jobs()[0].status(), GafferDispatch.LocalDispatcher.Job.Status.Complete )

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

		s["dispatcher"] = self.__createLocalDispatcher()
		s["dispatcher"]["executeInBackground"].setValue( True )
		s["dispatcher"]["framesMode"].setValue( GafferDispatch.Dispatcher.FramesMode.CustomRange )
		frameList = IECore.FrameList.parse( "2-6x2" )
		s["dispatcher"]["frameRange"].setValue( str(frameList) )

		s["dispatcher"]["tasks"][0].setInput( s["n1"]["task"] )
		s["dispatcher"]["task"].execute()

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
		s["dispatcher"].jobPool().waitForAll()
		self.assertEqual( len( s["dispatcher"].jobPool().jobs() ), 1 )
		self.assertEqual( s["dispatcher"].jobPool().jobs()[0].status(), GafferDispatch.LocalDispatcher.Job.Status.Complete )

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

		s["dispatcher"] = self.__createLocalDispatcher( jobPool )
		s["dispatcher"]["executeInBackground"].setValue( True )
		s["dispatcher"]["tasks"][0].setInput( s["n1"]["task"] )
		s["dispatcher2"] = self.__createLocalDispatcher( jobPool )
		s["dispatcher2"]["executeInBackground"].setValue( True )
		s["dispatcher2"]["tasks"][0].setInput( s["n1"]["task"] )

		s["dispatcher"]["task"].execute()

		c = s.context()
		c.setFrame( 2 )
		with c :
			s["dispatcher2"]["task"].execute()

		# wait long enough for background execution to finish
		self.assertEqual( len( jobPool.jobs() ), 2 )
		s["dispatcher"].jobPool().waitForAll()
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

		s["dispatcher"] = self.__createLocalDispatcher()
		s["dispatcher"]["tasks"][0].setInput( s["n1"]["task"] )

		# fails because n2 doesn't have a valid fileName
		self.assertRaisesRegex( RuntimeError, "No such file or directory", s["dispatcher"]["task"].execute )
		self.assertEqual( len( s["dispatcher"].jobPool().jobs() ), 1 )
		self.assertEqual(
			s["dispatcher"].jobPool().jobs()[0].status(),
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

		os.unlink( s.context().substitute( s["n3"]["fileName"].getValue() ) )

		s["dispatcher"]["executeInBackground"].setValue( True )
		s["dispatcher"]["task"].execute()

		# wait long enough for background execution to finish
		s["dispatcher"].jobPool().waitForAll()
		self.assertEqual( len( s["dispatcher"].jobPool().jobs() ), 2 )
		self.assertEqual(
			s["dispatcher"].jobPool().jobs()[1].status(),
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

		s["dispatcher"] = self.__createLocalDispatcher()
		s["dispatcher"]["executeInBackground"].setValue( True )
		s["dispatcher"]["tasks"][0].setInput( s["n1"]["task"] )

		self.assertEqual( len(s["dispatcher"].jobPool().jobs()), 0 )
		s["dispatcher"]["task"].execute()
		self.assertEqual( len(s["dispatcher"].jobPool().jobs()), 1 )

		# the execution hasn't finished yet
		self.assertFalse( os.path.isfile( s.context().substitute( s["n1"]["fileName"].getValue() ) ) )

		# kill the job
		s["dispatcher"].jobPool().jobs()[0].kill()

		# wait long enough for the process to die
		s["dispatcher"].jobPool().waitForAll()
		self.assertEqual( len( s["dispatcher"].jobPool().jobs() ), 1 )
		self.assertEqual( s["dispatcher"].jobPool().jobs()[0].status(), GafferDispatch.LocalDispatcher.Job.Status.Killed )

		# make sure it never wrote the file
		self.assertFalse( os.path.isfile( s.context().substitute( s["n1"]["fileName"].getValue() ) ) )

	def testSpacesInContext( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = GafferDispatchTest.TextWriter()
		s["n"]["fileName"].setValue( self.temporaryDirectory() / "test.txt" )
		s["n"]["text"].setValue( "${test}" )

		s["dispatcher"] = self.__createLocalDispatcher()
		s["dispatcher"]["executeInBackground"].setValue( True )
		s["dispatcher"]["tasks"][0].setInput( s["n"]["task"] )

		c = Gaffer.Context()
		c["test"] = "i am a string with spaces"

		with c :
			s["dispatcher"]["task"].execute()

		s["dispatcher"].jobPool().waitForAll()

		text = "".join( open( self.temporaryDirectory() / "test.txt", encoding = "utf-8" ).readlines() )
		self.assertEqual( text, "i am a string with spaces" )

	def testUIContextEntriesIgnored( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferDispatchTest.TextWriter()
		s["n"]["fileName"].setValue( self.temporaryDirectory() / "out.txt" )
		s["n"]["text"].setValue( "${foo} ${ui:foo}" )

		s["dispatcher"] = self.__createLocalDispatcher()
		s["dispatcher"]["executeInBackground"].setValue( True )
		s["dispatcher"]["tasks"][0].setInput( s["n"]["task"] )

		c = Gaffer.Context()
		c["ui:foo"] = "uiFoo"
		c["foo"] = "foo"

		with c :
			s["dispatcher"]["task"].execute()

		s["dispatcher"].jobPool().waitForAll()

		text = "".join( open( self.temporaryDirectory() / "out.txt", encoding = "utf-8" ).readlines() )
		self.assertEqual( text, "foo " )

	def testContextLockedDuringBackgroundDispatch( self ) :

		fileName = self.temporaryDirectory() / "out.txt"

		s = Gaffer.ScriptNode()
		s["n1"] = GafferDispatchTest.TextWriter()
		s["n1"]["fileName"].setValue( fileName )
		s["n1"]["text"].setValue( "n1 on ${frame} with ${foo}" )

		s["dispatcher"] = self.__createLocalDispatcher()
		s["dispatcher"]["executeInBackground"].setValue( True )
		s["dispatcher"]["tasks"][0].setInput( s["n1"]["task"] )

		c = Gaffer.Context( s.context() )
		c["foo"] = "foo"

		with c :
			s["dispatcher"]["task"].execute()

		self.assertFalse( fileName.is_file() )

		foo = s["variables"].addChild( Gaffer.NameValuePlug( "foo", IECore.StringData( "foo" ) ) )

		s["dispatcher"].jobPool().waitForAll()

		self.assertTrue( fileName.is_file() )

		text = "".join( open( fileName, encoding = "utf-8" ).readlines() )
		self.assertEqual( text, "n1 on 1 with foo" )

	def testNodeNamesLockedDuringBackgroundDispatch( self ) :

		fileName = self.temporaryDirectory() / "out.txt"

		s = Gaffer.ScriptNode()
		s["n1"] = GafferDispatchTest.TextWriter()
		s["n1"]["fileName"].setValue( fileName )
		s["n1"]["text"].setValue( "n1 on ${frame}" )

		s["dispatcher"] = self.__createLocalDispatcher()
		s["dispatcher"]["executeInBackground"].setValue( True )
		s["dispatcher"]["tasks"][0].setInput( s["n1"]["task"] )
		s["dispatcher"]["task"].execute()

		self.assertFalse( fileName.is_file() )

		s["n1"].setName( "n2" )

		s["dispatcher"].jobPool().waitForAll()

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

		s["dispatcher"] = self.__createLocalDispatcher()
		s["dispatcher"]["executeInBackground"].setValue( True )
		s["dispatcher"]["tasks"][0].setInput( s["n"]["task"] )

		s["dispatcher"]["task"].execute()
		s["dispatcher"].jobPool().waitForAll()

		self.assertFalse( fileName.is_file() )

		s["dispatcher"]["ignoreScriptLoadErrors"].setValue( True )
		s["dispatcher"]["task"].execute()
		s["dispatcher"].jobPool().waitForAll()

		self.assertTrue( fileName.is_file() )

	def testBackgroundBatchesCanAccessJobDirectory( self ) :

		s = Gaffer.ScriptNode()

		s["w"] = GafferDispatchTest.TextWriter()
		s["w"]["fileName"].setValue( "${dispatcher:jobDirectory}/test.####.txt" )
		s["w"]["text"].setValue( "w on ${frame} from ${dispatcher:jobDirectory}" )

		s["dispatcher"] = self.__createLocalDispatcher()
		s["dispatcher"]["executeInBackground"].setValue( True )
		s["dispatcher"]["framesMode"].setValue( GafferDispatch.Dispatcher.FramesMode.CustomRange )
		frameList = IECore.FrameList.parse( "2-6x2" )
		s["dispatcher"]["frameRange"].setValue( str(frameList) )
		s["dispatcher"]["tasks"][0].setInput( s["w"]["task"] )
		s["dispatcher"]["task"].execute()
		s["dispatcher"].jobPool().waitForAll()

		# a single dispatch should have the same job directory for all batches
		jobDir = s["dispatcher"]["jobsDirectory"].getValue() + "/000000"
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

		s["dispatcher"] = self.__createLocalDispatcher()
		s["dispatcher"]["executeInBackground"].setValue( True )
		s["dispatcher"]["framesMode"].setValue( GafferDispatch.Dispatcher.FramesMode.CurrentFrame )
		s["dispatcher"]["tasks"][0].setInput( s["c"]["task"] )
		s["dispatcher"]["task"].execute()
		s["dispatcher"].jobPool().waitForAll()

		with open( testFile, encoding = "utf-8" ) as f :
			self.assertEqual( f.readlines(), [ "HELLO\n" if os.name != "nt" else "HELLO %GAFFERDISPATCHTEST_ENVVAR%\n" ] )

		if os.name != "nt" :
			s["dispatcher"]["environmentCommand"].setValue( "env GAFFERDISPATCHTEST_ENVVAR=WORLD" )
		else :
			s["dispatcher"]["environmentCommand"].setValue( "set GAFFERDISPATCHTEST_ENVVAR=WORLD&" )
		s["dispatcher"]["task"].execute()
		s["dispatcher"].jobPool().waitForAll()

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

		s["dispatcher"] = self.__createLocalDispatcher()
		s["dispatcher"]["executeInBackground"].setValue( True )
		s["dispatcher"]["framesMode"].setValue( GafferDispatch.Dispatcher.FramesMode.CurrentFrame )
		s["dispatcher"]["tasks"][0].setInput( s["c"]["task"] )

		if os.name != "nt" :
			s["dispatcher"]["environmentCommand"].setValue( "env GAFFERDISPATCHTEST_ENVVAR=$world" )
		else :
			s["dispatcher"]["environmentCommand"].setValue( "set GAFFERDISPATCHTEST_ENVVAR=$world&" )

		with Gaffer.Context() as c :
			c["world"] = "WORLD"
			s["dispatcher"]["task"].execute()

		s["dispatcher"].jobPool().waitForAll()

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

		s["d"] = self.__createLocalDispatcher()
		s["d"]["framesMode"].setValue( s["d"].FramesMode.CustomRange )
		s["d"]["frameRange"].setValue( "1-1000" )
		s["d"]["tasks"][0].setInput( lastTask["task"] )

		t = time.process_time()
		s["d"]["task"].execute()
		timeLimit = 6
		if Gaffer.isDebug():
			timeLimit *= 2
		self.assertLess( time.process_time() - t, timeLimit )

		s["d"]["executeInBackground"].setValue( True )

		s["d"]["task"].execute()

		t = time.process_time()
		s["d"].jobPool().jobs()[-1].kill()
		self.assertLess( time.process_time() - t, 1 )

		s["d"].jobPool().waitForAll()

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

		s["d"] = self.__createLocalDispatcher()
		s["d"]["executeInBackground"].setValue( True )
		s["d"]["tasks"][0].setInput( s["v"]["task"] )
		s["d"]["task"].execute()
		s["d"].jobPool().waitForAll()

		self.assertEqual(
			open( s["t"]["fileName"].getValue(), encoding = "utf-8" ).read(),
			"0.0 1.0 2.0"
		)

	def testNestedDispatchBorrowingOuterJobDirectory( self ) :

		# This tested very early initial support for limited nested dispatch,
		# where the job directory was borrowed if the nested dispatcher didn't
		# specify a directory at all.

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

		s["d"] = self.__createLocalDispatcher()
		s["d"]["executeInBackground"].setValue( True )
		s["d"]["tasks"][0].setInput( s["outerTask"]["task"] )
		s["d"]["task"].execute()
		s["d"].jobPool().waitForAll()

		self.assertTrue( ( self.temporaryDirectory() / "nested.txt" ).exists() )
		self.assertTrue( ( self.temporaryDirectory() / "outer.txt" ).exists() )

		self.assertEqual(
			open( self.temporaryDirectory() / "nested.txt", encoding = "utf-8" ).readlines(),
			open( self.temporaryDirectory() / "outer.txt", encoding = "utf-8" ).readlines(),
		)

	def testUpstreamDispatchJobDirectory( self ) :

		script = Gaffer.ScriptNode()

		# Nested dispatcher sharing the job directory from the outer dispatch,
		# because it's `jobDirectory` plug has the same value.

		script["nestedTask"] = GafferDispatchTest.LoggingTaskNode()

		script["nestedDispatcher"] = self.__createLocalDispatcher()
		script["nestedDispatcher"]["tasks"][0].setInput( script["nestedTask"]["task"] )

		script["outerTask"] = GafferDispatchTest.LoggingTaskNode()
		script["outerTask"]["preTasks"][0].setInput( script["nestedDispatcher"]["task"] )

		script["outerDispatcher"] = self.__createLocalDispatcher()
		script["outerDispatcher"]["tasks"][0].setInput( script["outerTask"]["task"] )
		script["outerDispatcher"]["task"].execute()

		self.assertEqual(
			script["outerTask"].log[0].context["dispatcher:jobDirectory"],
			script["nestedTask"].log[0].context["dispatcher:jobDirectory"],
		)
		self.assertEqual(
			script["outerTask"].log[0].context["dispatcher:scriptFileName"],
			script["nestedTask"].log[0].context["dispatcher:scriptFileName"],
		)
		self.assertTrue( pathlib.Path( script["outerTask"].log[0].context["dispatcher:scriptFileName"] ).is_file() )

		# Nested dispatcher with its own job directory.

		del script["outerTask"].log[:]
		del script["nestedTask"].log[:]

		script["nestedDispatcher"]["jobsDirectory"].setValue( self.temporaryDirectory() / "nestedJobDir" )
		script["outerDispatcher"]["task"].execute()

		self.assertNotEqual(
			script["outerTask"].log[0].context["dispatcher:jobDirectory"],
			script["nestedTask"].log[0].context["dispatcher:jobDirectory"],
		)
		self.assertEqual(
			pathlib.Path( script["nestedTask"].log[0].context["dispatcher:jobDirectory"] ),
			self.temporaryDirectory() / "nestedJobDir" / "000000"
		)
		self.assertTrue( pathlib.Path( script["outerTask"].log[0].context["dispatcher:scriptFileName"] ).is_file() )
		self.assertTrue( pathlib.Path( script["nestedTask"].log[0].context["dispatcher:scriptFileName"] ).is_file() )

	def testBackgroundJobFailureStatus( self ) :

		script = Gaffer.ScriptNode()

		script["pythonCommand"] = GafferDispatch.PythonCommand()
		script["pythonCommand"]["command"].setValue( "a = nonExistentVariable" )

		script["dispatcher"] = self.__createLocalDispatcher()
		script["dispatcher"]["executeInBackground"].setValue( True )
		script["dispatcher"]["tasks"][0].setInput( script["pythonCommand"]["task"] )

		script["dispatcher"]["task"].execute()
		script["dispatcher"].jobPool().waitForAll()
		self.assertEqual(
			script["dispatcher"].jobPool().jobs()[0].status(),
			GafferDispatch.LocalDispatcher.Job.Status.Failed
		)

	def testJobPoolSignals( self ) :

		script = Gaffer.ScriptNode()
		script["taskNode"] = GafferDispatchTest.LoggingTaskNode()

		script["dispatcher"] = self.__createLocalDispatcher()
		script["dispatcher"]["tasks"][0].setInput( script["taskNode"]["task"] )

		jobAddedSlot = GafferTest.CapturingSlot( script["dispatcher"].jobPool().jobAddedSignal() )
		jobRemovedSlot = GafferTest.CapturingSlot( script["dispatcher"].jobPool().jobRemovedSignal() )

		self.assertEqual( len( jobAddedSlot ), 0 )
		self.assertEqual( len( jobRemovedSlot ), 0 )

		script["dispatcher"]["task"].execute()

		self.assertEqual( len( jobAddedSlot ), 1 )
		job = jobAddedSlot[0][0]
		self.assertIsInstance( job, GafferDispatch.LocalDispatcher.Job )
		self.assertIs( job, script["dispatcher"].jobPool().jobs()[0] )
		self.assertEqual( len( jobRemovedSlot ), 0 )

		script["dispatcher"].jobPool().removeJob( job )
		self.assertEqual( len( jobAddedSlot ), 1 )
		self.assertEqual( len( jobRemovedSlot ), 1 )
		self.assertIs( jobRemovedSlot[0][0], job )

	def testJobStatusChangedSignal( self ) :

		# Create dispatcher and connect to signals

		script = Gaffer.ScriptNode()
		script["taskNode"] = GafferDispatchTest.LoggingTaskNode()

		script["dispatcher"] = self.__createLocalDispatcher()
		script["dispatcher"]["tasks"][0].setInput( script["taskNode"]["task"] )

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

		script["dispatcher"].jobPool().jobAddedSignal().connect( jobAdded, scoped = False )

		# Test foreground dispatch

		script["dispatcher"]["task"].execute()

		self.assertEqual(
			statusChanges,
			[
				( script["dispatcher"].jobPool().jobs()[0], GafferDispatch.LocalDispatcher.Job.Status.Running ),
				( script["dispatcher"].jobPool().jobs()[0], GafferDispatch.LocalDispatcher.Job.Status.Complete )
			]
		)

		# Test background dispatch

		script["dispatcher"]["executeInBackground"].setValue( True )
		del statusChanges[:]

		with GafferTest.ParallelAlgoTest.UIThreadCallHandler() as handler :
			script["dispatcher"]["task"].execute()
			handler.assertCalled()
			script["dispatcher"].jobPool().waitForAll()

		self.assertEqual(
			statusChanges,
			[
				( script["dispatcher"].jobPool().jobs()[1], GafferDispatch.LocalDispatcher.Job.Status.Running ),
				( script["dispatcher"].jobPool().jobs()[1], GafferDispatch.LocalDispatcher.Job.Status.Complete )
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

		script["dispatcher"] = self.__createLocalDispatcher()
		script["dispatcher"]["executeInBackground"].setValue( True )
		script["dispatcher"]["tasks"][0].setInput( script["command"]["task"] )
		script["dispatcher"]["task"].execute()
		script["dispatcher"].jobPool().waitForAll()

		messages = script["dispatcher"].jobPool().jobs()[0].messages()
		messages = { m.message for m in messages }
		self.assertIn( "Hello stderr!", messages )
		self.assertIn( "Hello stdout!", messages )

	def testMessageLevels( self ) :

		script = Gaffer.ScriptNode()

		script["command"] = GafferDispatch.PythonCommand()
		script["command"]["command"].setValue( inspect.cleandoc(
			r"""
			import sys
			import IECore

			# Cortex messages

			for level in IECore.Msg.Level.values.values() :
				IECore.msg(
					level, "testMessageLevels",
					# Obfuscate the level in the message text, so it can't be used
					# by any level-detection heuristics in the LocalDispatcher.
					"message level {}".format(
						"-".join( str( level.name ) )
					)
				)

			# Arnold-like messages, with and without time and memory prefixes

			for message in [
				"00:00:00   315MB WARNING | rendering with watermarks because ARNOLD_LICENSE_ORDER = none",
				"315MB WARNING | rendering with watermarks because ARNOLD_LICENSE_ORDER = none",
				"WARNING | rendering with watermarks because ARNOLD_LICENSE_ORDER = none",
				"00:00:00   368MB ERROR   |  [texturesys] shader:55b3960bd4e0c6a75adc63c08ac0cb6b: Invalid image file "": ImageInput::create() called with no filename",

			] :
				sys.stdout.write( f"{message}\n" )
			"""
		) )

		dispatcher = self.__createLocalDispatcher()
		dispatcher["tasks"][0].setInput( script["command"]["task"] )
		dispatcher["executeInBackground"].setValue( True )
		dispatcher["task"].execute()
		dispatcher.jobPool().waitForAll()

		messages = dispatcher.jobPool().jobs()[0].messages()
		messageLevels = {
			m.message : m.level
			for m in messages
		}

		for level in IECore.Msg.Level.values.values() :
			if level == IECore.Msg.Level.Invalid :
				continue
			self.assertEqual(
				messageLevels["testMessageLevels : message level {}".format( "-".join( str( level ) ) ) ],
				level
			)

		for message, level in [
			( "00:00:00   315MB WARNING | rendering with watermarks because ARNOLD_LICENSE_ORDER = none", IECore.Msg.Level.Warning ),
			( "315MB WARNING | rendering with watermarks because ARNOLD_LICENSE_ORDER = none", IECore.Msg.Level.Warning ),
			( "rendering with watermarks because ARNOLD_LICENSE_ORDER = none", IECore.Msg.Level.Warning ),
			( "00:00:00   368MB ERROR   |  [texturesys] shader:55b3960bd4e0c6a75adc63c08ac0cb6b: Invalid image file "": ImageInput::create() called with no filename", IECore.Msg.Level.Error ),
		] :
			self.assertEqual( messageLevels[message], level )

			# self.assertEqual( messages[i].level, level )
			# self.assertEqual( messages[i].context, "testMessageLevels" )
			# self.assertEqual( messages[i].message, "this is a message" )

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
		# \todo Figure out how to check this on Windows.

		if os.name != "nt" :
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

			# `LocalDispatcher.defaultJobPool()` automatically kills
			# running jobs at exit.
			script["dispatcher"] = GafferDispatch.LocalDispatcher( jobPool = GafferDispatch.LocalDispatcher.defaultJobPool() )
			script["dispatcher"]["jobsDirectory"].setValue( jobDirectory )
			script["dispatcher"]["executeInBackground"].setValue( True )
			script["dispatcher"]["tasks"][0].setInput( script["command"]["task"] )
			script["dispatcher"]["task"].execute()

			# Wait for background task to start, print its PID
			# to `stdout` and then exit.
			while True :
				pid = script["dispatcher"].jobPool().jobs()[-1].processID()
				if pid is not None :
					sys.stdout.write( f"PID : {pid}\n" )
					sys.exit( 0 )

	def testRunningTime( self ) :

		script = Gaffer.ScriptNode()
		script["command"] = GafferDispatch.PythonCommand()
		script["command"]["command"].setValue( inspect.cleandoc(
			"""
			import time
			time.sleep( 0.5 )
			"""
		) )

		dispatcher = self.__createLocalDispatcher()
		dispatcher["tasks"][0].setInput( script["command"]["task"] )
		dispatcher["executeInBackground"].setValue( True )
		dispatcher["task"].execute()
		dispatcher.jobPool().waitForAll()

		runningTime = dispatcher.jobPool().jobs()[0].runningTime()
		self.assertGreaterEqual( runningTime, datetime.timedelta( seconds = 0.5 ) )
		self.assertEqual( dispatcher.jobPool().jobs()[0].runningTime(), runningTime )

if __name__ == "__main__":
	unittest.main()
