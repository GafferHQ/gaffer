##########################################################################
#
#  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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
import unittest.mock
import inspect
import sys

import imath

import IECore

import Gaffer
import GafferTest
import GafferDispatch
import GafferDispatchTest
import GafferTractor
import GafferTractorTest

@unittest.mock.patch( "GafferTractor.tractorAPI", new = GafferTractorTest.tractorAPI )
class TractorDispatcherTest( GafferTest.TestCase ) :

	def __dispatcher( self ) :

		dispatcher = GafferTractor.TractorDispatcher()
		dispatcher["jobsDirectory"].setValue( self.temporaryDirectory() / "testJobDirectory" )

		return dispatcher

	def __job( self, nodes, dispatcher = None ) :

		jobs = []
		def f( dispatcher, job ) :

			jobs.append( job )

		c = GafferTractor.TractorDispatcher.preSpoolSignal().connect( f, scoped = True )

		if dispatcher is None :
			dispatcher = self.__dispatcher()

		for i, node in enumerate( nodes ) :
			dispatcher["tasks"][i].setInput( node["task"] )

		dispatcher["task"].execute()

		return jobs[0]

	def testPreSpoolSignal( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferDispatchTest.LoggingTaskNode()

		spooled = []
		def f( dispatcher, job ) :

			spooled.append( ( dispatcher, job ) )

		c = GafferTractor.TractorDispatcher.preSpoolSignal().connect( f, scoped = True )

		dispatcher = self.__dispatcher()
		dispatcher["tasks"][0].setInput( s["n"]["task"] )
		dispatcher["task"].execute()

		self.assertEqual( len( spooled ), 1 )
		self.assertTrue( spooled[0][0] is dispatcher )

	def testJobScript( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferDispatchTest.LoggingTaskNode()

		dispatcher = self.__dispatcher()
		dispatcher["tasks"][0].setInput( s["n"]["task"] )
		dispatcher["task"].execute()

		self.assertTrue( ( dispatcher.jobDirectory() / "job.alf" ).is_file() )

	def testJobScriptInNestedDispatch( self ) :

		script = Gaffer.ScriptNode()

		# Fake the creation of a `.alf` file from a downstream
		# TractorDispatcher. We can't use a TractorDispatcher to do this because
		# the Tractor API is mocked during testing.

		script["pythonCommand"] = GafferDispatch.PythonCommand()
		script["pythonCommand"]["command"].setValue( inspect.cleandoc(
			"""
			import pathlib
			p = pathlib.Path( context["dispatcher:jobDirectory"] ) / "job.alf"
			with open( p, "w", encoding = "utf-8" ) as f :
					f.write( "First one wins" )
			"""
		) )

		# That runs as a preTask for an actual TractorDispatcher.

		script["node"] = GafferDispatchTest.LoggingTaskNode()

		script["tractorDispatcher"] = self.__dispatcher()
		script["tractorDispatcher"]["tasks"][0].setInput( script["node"]["task"] )
		script["tractorDispatcher"]["preTasks"][0].setInput( script["pythonCommand"]["task"] )

		# And then we use a LocalDispatcher to launch the whole thing.

		script["localDispatcher"] = GafferDispatch.LocalDispatcher()
		script["localDispatcher"]["tasks"][0].setInput( script["tractorDispatcher"]["task"] )
		script["localDispatcher"]["jobsDirectory"].setValue( script["tractorDispatcher"]["jobsDirectory"].getValue() )
		script["localDispatcher"]["task"].execute()

		# We want our fake job script to have won, because it represents
		# the downstream dispatch, which provides a full record of the job.

		self.assertTrue( ( script["tractorDispatcher"].jobDirectory() / "job.alf" ).is_file() )
		with open( script["tractorDispatcher"].jobDirectory() / "job.alf" ) as f :
			self.assertEqual( f.readline(), "First one wins" )

	def testJobAttributes( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferDispatchTest.LoggingTaskNode()

		dispatcher = self.__dispatcher()
		dispatcher["jobName"].setValue( "Test Job" )
		dispatcher["service"].setValue( "myService" )
		dispatcher["envKey"].setValue( "myEnvKey" )

		job = self.__job( [ s["n" ] ], dispatcher )

		self.assertEqual( job.title, "Test Job" )
		self.assertEqual( job.service, "myService" )
		self.assertEqual( job.envkey, [ "myEnvKey" ] )

		dispatcher["jobName"].setValue( "${jobName}" )
		dispatcher["service"].setValue( "${service}" )
		dispatcher["envKey"].setValue( "${envKey}" )

		with Gaffer.Context() as context :

			context["jobName"] = "a"
			context["service"] = "b"
			context["envKey"] = "c"

			job = self.__job( [ s["n" ] ], dispatcher )

		self.assertEqual( job.title, "a" )
		self.assertEqual( job.service, "b" )
		self.assertEqual( job.envkey, [ "c" ] )

	def testTaskAttributes( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferDispatchTest.LoggingTaskNode()
		s["n"]["frame"] = Gaffer.StringPlug( defaultValue = "${frame}", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["dispatcher"]["batchSize"].setValue( 10 )
		s["n"]["dispatcher"]["tractor"]["tags"].setValue( "myTag1 ${myTagContext2}" )
		s["expression"] = Gaffer.Expression()
		s["expression"].setExpression( """parent["n"]["dispatcher"]["tractor"]["service"] = context.get("service", "")""" )

		# add context variables: myTagContext2 and service
		s["context"] = Gaffer.ContextVariables()
		s["context"].setup( GafferDispatch.TaskNode.TaskPlug() )
		s["context"]["in"].setInput( s["n"]["task"] )
		variable = s["context"]["variables"].addMember( "tag", Gaffer.StringPlug() )
		variable["name"].setValue("myTagContext2")
		variable["value"].setValue("myTag2")
		variable = s["context"]["variables"].addMember( "service", Gaffer.StringPlug() )
		variable["name"].setValue("service")
		variable["value"].setValue("myService")

		s["job"] = GafferDispatch.TaskList()
		s["job"]["preTasks"][0].setInput( s["context"]["out"] )

		dispatcher = self.__dispatcher()
		dispatcher["framesMode"].setValue( dispatcher.FramesMode.CustomRange )
		dispatcher["frameRange"].setValue( "1-10" )

		job = self.__job( [ s["job"] ], dispatcher )

		self.assertEqual( len( job.subtasks ), 10 )

		task = job.subtasks[0].subtasks[0]
		self.assertEqual( task.title, "n 1-10" )

		self.assertEqual( len( task.cmds ), 1 )
		command = task.cmds[0]
		self.assertEqual( command.service, "myService", "context variables were not expanded correctly" )
		self.assertEqual( command.tags, [ "myTag1", "myTag2" ] )

	def testPreTasks( self ) :

		# n1
		#  |
		# n2     n3

		s = Gaffer.ScriptNode()
		s["n1"] = GafferDispatchTest.LoggingTaskNode()
		s["n2"] = GafferDispatchTest.LoggingTaskNode()
		s["n3"] = GafferDispatchTest.LoggingTaskNode()
		s["n2"]["preTasks"][0].setInput( s["n1"]["task" ] )

		job = self.__job( [ s["n2"], s["n3"] ] )

		self.assertEqual( len( job.subtasks ), 2 )
		self.assertEqual( job.subtasks[0].title, "n2 1" )
		self.assertEqual( job.subtasks[1].title, "n3 1" )

		self.assertEqual( len( job.subtasks[0].subtasks ), 1 )
		self.assertEqual( job.subtasks[0].subtasks[0].title, "n1 1" )

		self.assertEqual( len( job.subtasks[1].subtasks ), 0 )

	def testSharedPreTasks( self ) :

		#   n1
		#  / \
		# i1 i2
		#  \ /
		#   n2

		s = Gaffer.ScriptNode()

		log = []
		s["n1"] = GafferDispatchTest.LoggingTaskNode()
		s["i1"] = GafferDispatchTest.LoggingTaskNode()
		s["i1"]["preTasks"][0].setInput( s["n1"]["task"] )
		s["i2"] = GafferDispatchTest.LoggingTaskNode()
		s["i2"]["preTasks"][0].setInput( s["n1"]["task"] )
		s["n2"] = GafferDispatchTest.LoggingTaskNode()
		s["n2"]["preTasks"][0].setInput( s["i1"]["task"] )
		s["n2"]["preTasks"][1].setInput( s["i2"]["task"] )

		job = self.__job( [ s["n2" ] ] )

		self.assertEqual( len( job.subtasks ), 1 )
		self.assertEqual( job.subtasks[0].title, "n2 1" )

		self.assertEqual( len( job.subtasks[0].subtasks ), 2 )
		self.assertEqual( job.subtasks[0].subtasks[0].title, "i1 1" )
		self.assertEqual( job.subtasks[0].subtasks[1].title, "i2 1" )

		self.assertEqual( len( job.subtasks[0].subtasks[0].subtasks ), 1 )
		self.assertEqual( len( job.subtasks[0].subtasks[1].subtasks ), 1 )
		self.assertEqual( job.subtasks[0].subtasks[0].subtasks[0].title, "n1 1" )
		self.assertEqual( job.subtasks[0].subtasks[1].subtasks[0].title, "n1 1" )

		self.assertIsInstance(
			job.subtasks[0].subtasks[1].subtasks[0],
			GafferTractor.tractorAPI().Instance
		)

	def testTaskPlugs( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferDispatchTest.LoggingTaskNode()
		self.assertTrue( "tractor" in [ x.getName() for x in s["n"]["dispatcher"].children() ] )
		self.assertTrue( "tractor1" not in [ x.getName() for x in s["n"]["dispatcher"].children() ] )
		s["n"]["dispatcher"]["tractor"]["service"].setValue( "myService" )
		s["n"]["dispatcher"]["tractor"]["tags"].setValue( "myTag1 myTag2" )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )
		self.assertTrue( "tractor" in [ x.getName() for x in s2["n"]["dispatcher"].children() ] )
		self.assertTrue( "tractor1" not in [ x.getName() for x in s2["n"]["dispatcher"].children() ] )
		self.assertEqual( s2["n"]["dispatcher"]["tractor"]["service"].getValue(), "myService" )
		self.assertEqual( s2["n"]["dispatcher"]["tractor"]["tags"].getValue(), "myTag1 myTag2" )

	def testTypeNamePrefixes( self ) :

		self.assertTypeNamesArePrefixed( GafferTractor )

	def testDefaultNames( self ) :

		self.assertDefaultNamesAreCorrect( GafferTractor )

	def testTasksWithoutCommands( self ) :

		s = Gaffer.ScriptNode()
		s["systemCommand"] = GafferDispatch.SystemCommand()
		s["systemCommand"]["command"].setValue( "ls" )

		s["taskList"] = GafferDispatch.TaskList()
		s["taskList"]["preTasks"][0].setInput( s["systemCommand"]["task"] )

		job = self.__job( [ s["taskList" ] ] )

		taskListTask = job.subtasks[0]
		self.assertEqual( taskListTask.title, "taskList" )
		self.assertEqual( len( taskListTask.cmds ), 0 )

		systemCommandTask = taskListTask.subtasks[0]
		self.assertEqual( systemCommandTask.title, "systemCommand 1" )
		self.assertEqual( len( systemCommandTask.cmds ), 1 )

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

		job = self.__job( [ s["v" ] ] )
		task = job.subtasks[0].subtasks[0]
		self.assertIn(
			"imath.Color3f( 0, 1, 2 )",
			task.cmds[0].argv
		)

	def testMissingTractorAPI( self ) :

		script = Gaffer.ScriptNode()
		script["pythonCommand"] = GafferDispatch.PythonCommand()

		script["dispatcher"] = self.__dispatcher()
		script["dispatcher"]["tasks"][0].setInput( script["pythonCommand"]["task"] )

		with unittest.mock.patch( "GafferTractor.tractorAPI", side_effect = ImportError() ) :
			with self.assertRaisesRegex( RuntimeError, "Tractor API not found" ) :
				script["dispatcher"]["task"].execute()

if __name__ == "__main__":
	unittest.main()
