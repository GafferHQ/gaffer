##########################################################################
#
#  Copyright (c) 2025, Cinesite VFX Ltd. All rights reserved.
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

import http.server
import inspect
import json
import threading
import unittest

import Gaffer
import GafferTest
import GafferDispatch
import GafferFlamenco

class FlamencoDispatcherTest( GafferTest.TestCase ) :

	class __MockRequestHandler( http.server.BaseHTTPRequestHandler ) :

		def do_GET( self ) :

			if self.path == "/api/v3/jobs/type/gaffer" :
				self.send_response( 200 )
			elif self.path == "/api/v3/worker-mgt/tags" :
				self.send_response( 200 )
				responseBody = inspect.cleandoc(
					"""
					{
						"tags": [
							{
								"id": "d90bf772-2f60-44f7-960e-49f8ca9b3901",
								"name": "workerTagA"
							}
						]
					}
					"""
				).encode( "utf-8" )
				self.send_header( "content-type", "application/json; charset=UTF-8" )
				self.send_header( "content-length", len( responseBody ) )
				self.end_headers()
				self.wfile.write( responseBody )
			else :
				self.send_response( 404 )

			self.end_headers()

		def do_POST( self ) :

			bytes = self.rfile.read( int( self.headers["Content-Length"] ) )
			self.server.jobs.append(
				json.loads( bytes )
			)

			self.send_response( 200 )
			self.end_headers()

	def setUp( self ) :

		GafferTest.TestCase.setUp( self )

		self.__mockServer = http.server.ThreadingHTTPServer( ( "", 8000 ), self.__MockRequestHandler )
		self.__mockServer.jobs = []

		self.__mockServerThread = threading.Thread( target = self.__mockServer.serve_forever )
		self.__mockServerThread.start()

	def tearDown( self ) :

		GafferTest.TestCase.tearDown( self )

		self.__mockServer.shutdown()
		self.__mockServerThread.join()

	def __dispatcher( self ) :

		dispatcher = GafferFlamenco.FlamencoDispatcher()
		dispatcher["jobsDirectory"].setValue( self.temporaryDirectory() / "testJobDirectory" )
		dispatcher["managerURL"].setValue( "http://localhost:8000" )

		return dispatcher

	def testSubmission( self ) :

		script = Gaffer.ScriptNode()
		script["task"] = GafferDispatch.PythonCommand()
		script["task"]["command"].setValue( "print( 'hello world' )" )

		script["dispatcher"] = self.__dispatcher()
		script["dispatcher"]["tasks"][0].setInput( script["task"]["task"] )
		script["dispatcher"]["jobName"].setValue( "myJob" )
		script["dispatcher"]["priority"].setValue( 10 )
		script["dispatcher"]["task"].execute()

		self.assertEqual( len( self.__mockServer.jobs ), 1 )
		job = self.__mockServer.jobs[0]
		self.assertEqual( job["name"], "myJob" )
		self.assertEqual( job["priority"], 10 )
		self.assertEqual( job["initial_status"], "active" )
		self.assertEqual( len( job["settings"]["tasks" ] ), 1 )

		script["dispatcher"]["startPaused"].setValue( True )
		script["dispatcher"]["task"].execute()
		self.assertEqual( len( self.__mockServer.jobs ), 2 )
		job = self.__mockServer.jobs[1]
		self.assertEqual( job["initial_status"], "paused" )

	def testBadManagerURL( self ) :

		script = Gaffer.ScriptNode()
		script["task"] = GafferDispatch.PythonCommand()
		script["task"]["command"].setValue( "print( 'hello world' )" )

		script["dispatcher"] = self.__dispatcher()
		script["dispatcher"]["tasks"][0].setInput( script["task"]["task"] )
		script["dispatcher"]["jobName"].setValue( "myJob" )
		script["dispatcher"]["managerURL"].setValue( "http://localhost:8001" )

		with self.assertRaisesRegex( Gaffer.ProcessException, r"Failed to connect to manager." ) :
			script["dispatcher"]["task"].execute()

	def testWorkerTag( self ) :

		script = Gaffer.ScriptNode()
		script["task"] = GafferDispatch.PythonCommand()
		script["task"]["command"].setValue( "print( 'hello world' )" )

		script["dispatcher"] = self.__dispatcher()
		script["dispatcher"]["tasks"][0].setInput( script["task"]["task"] )
		script["dispatcher"]["workerTag"].setValue( "workerTagA" )
		script["dispatcher"]["task"].execute()

		self.assertEqual( len( self.__mockServer.jobs ), 1 )
		job = self.__mockServer.jobs[0]
		self.assertEqual( job["worker_tag"], "d90bf772-2f60-44f7-960e-49f8ca9b3901" )

	def testBadWorkerTag( self ) :

		script = Gaffer.ScriptNode()
		script["task"] = GafferDispatch.PythonCommand()
		script["task"]["command"].setValue( "print( 'hello world' )" )

		script["dispatcher"] = self.__dispatcher()
		script["dispatcher"]["tasks"][0].setInput( script["task"]["task"] )
		script["dispatcher"]["workerTag"].setValue( "nonExistentWorkerTag" )

		with self.assertRaisesRegex( Gaffer.ProcessException, r'Worker tag "nonExistentWorkerTag" does not exist.' ) :
			script["dispatcher"]["task"].execute()

if __name__ == "__main__":
	unittest.main()
