##########################################################################
#
#  Copyright (c) 2026, Cinesite VFX Ltd. All rights reserved.
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

import json
import queue
import subprocess
import threading

import Gaffer
import GafferTest

class MCPApplicationTest( GafferTest.TestCase ) :

	# Runs `gaffer mcp` and talks to it over stdin and stdout, as a client
	# would. Requests are made one at a time, waiting for each response.
	## \todo Perhaps this and `MCPTest.TestClient` could be rationalised
	# a bit under an `MCP.Client` base class?
	class TestClient( object ) :

		def __init__( self, arguments ) :

			self.__process = subprocess.Popen(
				[ str( Gaffer.executablePath() ), "mcp" ] + arguments,
				stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE,
				text = True, encoding = "utf-8",
			)

			# Read stdout and stderr on background threads, so we can time out
			# rather than hanging if the application misbehaves.
			self.__stdout = queue.Queue()
			self.__stderr = []
			threading.Thread( target = self.__read, args = ( self.__process.stdout, self.__stdout.put ), daemon = True ).start()
			self.__stderrThread = threading.Thread( target = self.__read, args = ( self.__process.stderr, self.__stderr.append ), daemon = True )
			self.__stderrThread.start()

		## Sends a request, and returns the decoded response.
		def request( self, method, params = None, id = 1 ) :

			message = { "jsonrpc" : "2.0", "id" : id, "method" : method }
			if params is not None :
				message["params"] = params

			return self.send( json.dumps( message ) )

		## Sends a notification, which has no response.
		def notify( self, method ) :

			self.send( json.dumps( { "jsonrpc" : "2.0", "method" : method } ), expectResponse = False )

		## Sends a raw line, and returns the decoded response.
		def send( self, line, expectResponse = True ) :

			self.__process.stdin.write( line + "\n" )
			self.__process.stdin.flush()
			if not expectResponse :
				return None

			response = self.__stdout.get( timeout = 30 )
			return json.loads( response )

		def executePython( self, code, target = None ) :

			arguments = { "code" : code }
			if target is not None :
				arguments["target"] = target

			return self.request( "tools/call", { "name" : "executePython", "arguments" : arguments } )["result"]

		## Closes stdin, waits for the application to exit, and returns
		# `( returnCode, remainingStdout, stderr )`.
		def close( self ) :

			self.__process.stdin.close()
			returnCode = self.__process.wait( timeout = 30 )

			# The reader threads see end-of-file once the process has exited.
			remaining = []
			while True :
				try :
					line = self.__stdout.get( timeout = 1 )
				except queue.Empty :
					break
				if line is None :
					break
				remaining.append( line )

			self.__stderrThread.join( timeout = 30 )
			return returnCode, remaining, "".join( line for line in self.__stderr if line is not None )

		@staticmethod
		def __read( stream, put ) :

			for line in stream :
				put( line )
			put( None )

	@GafferTest.TestRunner.CategorisedTestMethod( { "mcp" } )
	def testExecute( self ) :

		script = Gaffer.ScriptNode()
		script["node"] = GafferTest.AddNode()
		script["fileName"].setValue( self.temporaryDirectory() / "shot.gfr" )
		script.save()

		client = self.TestClient( [ script["fileName"].getValue() ] )

		response = client.request( "initialize", { "protocolVersion" : "2025-11-25", "capabilities" : {}, "clientInfo" : { "name" : "test", "version" : "1.0" } } )
		self.assertEqual( response["result"]["serverInfo"]["name"], "gaffer" )
		client.notify( "notifications/initialized" )

		response = client.request( "tools/list", id = 2 )
		self.assertEqual( response["id"], 2 )
		self.assertIn( "executePython", [ t["name"] for t in response["result"]["tools"] ] )

		# The script is loaded.
		result = client.executePython( "root['node'].typeName()" )
		self.assertNotIn( "isError", result )
		self.assertEqual( result["content"][0]["text"], "'GafferTest::AddNode'\n" )

		# Output is returned to the client, and doesn't end up in the protocol
		# stream, even when written directly to file descriptor 1.
		result = client.executePython( "print( 'hello' )\nimport os\nos.write( 1, b'not a message\\n' )\nNone" )
		self.assertEqual( result["content"][0]["text"], "hello\n" )

		returnCode, remaining, stderr = client.close()

		self.assertEqual( returnCode, 0 )
		self.assertEqual( remaining, [] )
		self.assertIn( "not a message", stderr )
		self.assertIn( "Serving \"shot\"", stderr )

	@GafferTest.TestRunner.CategorisedTestMethod( { "mcp" } )
	def testNoScripts( self ) :

		client = self.TestClient( [] )

		result = client.executePython( "root['fileName'].getValue()" )
		self.assertNotIn( "isError", result )
		self.assertEqual( result["content"][0]["text"], "''\n" )

		returnCode, remaining, stderr = client.close()
		self.assertEqual( returnCode, 0 )
		self.assertIn( "unsaved", stderr )

	@GafferTest.TestRunner.CategorisedTestMethod( { "mcp" } )
	def testMultipleScripts( self ) :

		fileNames = []
		for name in ( "one", "two" ) :
			script = Gaffer.ScriptNode()
			script["fileName"].setValue( self.temporaryDirectory() / "{}.gfr".format( name ) )
			script.save()
			fileNames.append( script["fileName"].getValue() )

		client = self.TestClient( fileNames )

		# Each script is a target, named after its file.

		result = client.executePython( "1" )
		self.assertTrue( result["isError"] )
		self.assertIn( "- one :", result["content"][0]["text"] )
		self.assertIn( "- two :", result["content"][0]["text"] )

		result = client.executePython( "root['fileName'].getValue()", target = "two" )
		self.assertNotIn( "isError", result )
		self.assertIn( "two.gfr", result["content"][0]["text"] )

		self.assertEqual( client.close()[0], 0 )

	@GafferTest.TestRunner.CategorisedTestMethod( { "mcp" } )
	def testScriptLoadError( self ) :

		client = self.TestClient( [ str( self.temporaryDirectory() / "doesNotExist.gfr" ) ] )
		returnCode, remaining, stderr = client.close()
		self.assertNotEqual( returnCode, 0 )
		self.assertEqual( remaining, [] )
		self.assertIn( "doesNotExist.gfr", stderr )

	@GafferTest.TestRunner.CategorisedTestMethod( { "mcp" } )
	def testInvalidMessages( self ) :

		client = self.TestClient( [] )

		# Parse errors are reported, and the application keeps going.
		response = client.send( "{ this isn't json" )
		self.assertIsNone( response["id"] )
		self.assertEqual( response["error"]["code"], Gaffer.MCP.Server.Error.ParseError )

		response = client.send( json.dumps( [ 1, 2, 3 ] ) )
		self.assertEqual( response["error"]["code"], Gaffer.MCP.Server.Error.InvalidRequest )

		# Blank lines are ignored.
		client.send( "", expectResponse = False )

		response = client.request( "ping", id = "abc" )
		self.assertEqual( response, { "jsonrpc" : "2.0", "id" : "abc", "result" : {} } )

		returnCode, remaining, stderr = client.close()
		self.assertEqual( returnCode, 0 )
		self.assertEqual( remaining, [] )
