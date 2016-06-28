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

import os
import unittest

import tractor.api.author as author

import Gaffer
import GafferTest
import GafferDispatch
import GafferDispatchTest
import GafferTractor

class TractorDispatcherTest( GafferTest.TestCase ) :

	def __dispatcher( self ) :

		dispatcher = GafferTractor.TractorDispatcher()
		dispatcher["jobsDirectory"].setValue( self.temporaryDirectory() + "/testJobDirectory" )

		return dispatcher

	def __job( self, nodes, dispatcher = None ) :

		jobs = []
		def f( dispatcher, job ) :

			jobs.append( job )

		c = GafferTractor.TractorDispatcher.preSpoolSignal().connect( f )

		if dispatcher is None :
			dispatcher = self.__dispatcher()

		dispatcher.dispatch( nodes )

		return jobs[0]

	def testPreSpoolSignal( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferDispatchTest.LoggingTaskNode()

		spooled = []
		def f( dispatcher, job ) :

			spooled.append( ( dispatcher, job ) )

		c = GafferTractor.TractorDispatcher.preSpoolSignal().connect( f )

		dispatcher = self.__dispatcher()
		dispatcher.dispatch( [ s["n"] ] )

		self.assertEqual( len( spooled ), 1 )
		self.assertTrue( spooled[0][0] is dispatcher )

	def testJobScript( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferDispatchTest.LoggingTaskNode()

		dispatcher = self.__dispatcher()
		dispatcher.dispatch( [ s["n"] ] )

		self.assertTrue( os.path.isfile( dispatcher.jobDirectory() + "/job.alf" ) )

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

	def testTaskAttributes( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferDispatchTest.LoggingTaskNode()
		s["n"]["frame"] = Gaffer.StringPlug( defaultValue = "${frame}", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["dispatcher"]["batchSize"].setValue( 10 )
		s["n"]["dispatcher"]["tractor"]["service"].setValue( "myService" )
		s["n"]["dispatcher"]["tractor"]["tags"].setValue( "myTag1 myTag2" )

		dispatcher = self.__dispatcher()
		dispatcher["framesMode"].setValue( dispatcher.FramesMode.CustomRange )
		dispatcher["frameRange"].setValue( "1-10" )

		job = self.__job( [ s["n"] ], dispatcher )
		self.assertEqual( len( job.subtasks ), 1 )

		task = job.subtasks[0]
		self.assertEqual( task.title, "n 1-10" )

		self.assertEqual( len( task.cmds ), 1 )
		command = task.cmds[0]
		self.assertEqual( command.service, "myService" )
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

		self.assertTrue( isinstance( job.subtasks[0].subtasks[1].subtasks[0], author.Instance ) )

	def testTypeNamePrefixes( self ) :

		self.assertTypeNamesArePrefixed( GafferTractor )

	def testDefaultNames( self ) :

		self.assertDefaultNamesAreCorrect( GafferTractor )

if __name__ == "__main__":
	unittest.main()
