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

import http
import json
import threading
import urllib.request
import weakref

import IECore

import Gaffer
import GafferTest

class MCPTest( GafferTest.TestCase ) :

	class TestClient( object ) :

		def __init__( self, port ) :

			self.__port = port

		## Makes a request, returning a dictionary containing the HTTP "status"
		# and the decoded JSON "body", or `None` if the body is empty.
		def request( self, message, headers = {}, method = "POST", path = "/mcp" ) :

			if message is None :
				data = None
			elif isinstance( message, bytes ) :
				data = message
			else :
				data = json.dumps( message ).encode( "utf-8" )

			request = urllib.request.Request(
				"http://localhost:{}{}".format( self.__port, path ),
				data = data, method = method,
				headers = { "Content-Type" : "application/json", "Accept" : "application/json, text/event-stream", **headers }
			)

			# Bypass any proxy configured in the environment.
			opener = urllib.request.build_opener( urllib.request.ProxyHandler( {} ) )

			result = {}
			def makeRequest() :
				try :
					with opener.open( request, timeout = 10 ) as response :
						result["status"] = response.status
						body = response.read()
				except urllib.error.HTTPError as e :
					result["status"] = e.code
					body = e.read()
				result["body"] = json.loads( body ) if body else None

			# The server uses `ParallelAlgo.callOnUIThread()`, and the tests are
			# running on the main thread. So we need to make the request from a
			# background thread while servicing UI calls on this thread.
			with GafferTest.ParallelAlgoTest.UIThreadCallHandler() as handler :
				backgroundTask = Gaffer.ParallelAlgo.callOnBackgroundThread( None, makeRequest )
				while backgroundTask.status() != backgroundTask.Status.Completed :
					handler.waitFor( 0.01 )

			return result

		def callTool( self, name, arguments ) :

			response = self.request( {
				"jsonrpc" : "2.0", "id" : 1, "method" : "tools/call",
				"params" : { "name" : name, "arguments" : arguments }
			} )
			if response["status"] != http.HTTPStatus.OK :
				raise RuntimeError( "Unexpected status {}".format( response["status"] ) )

			if "error" in response["body"] :
				raise RuntimeError( response["body"]["error"]["message"] )

			return response["body"]["result"]

		def executePython( self, code, target = None ) :

			arguments = { "code" : code }
			if target is not None :
				arguments["target"] = target

			return self.callTool( "executePython", arguments )

	@GafferTest.TestRunner.CategorisedTestMethod( { "mcp" } )
	def testAcquire( self ) :

		self.assertIs( Gaffer.MCP.HTTPServer.acquireDefaultServer(), Gaffer.MCP.HTTPServer.acquireDefaultServer() )

	@GafferTest.TestRunner.CategorisedTestMethod( { "mcp" } )
	def testServerLifetime( self ) :

		numThreads = threading.active_count()
		server = Gaffer.MCP.HTTPServer()
		self.assertEqual( threading.active_count(), numThreads + 1 )

		server.addTarget( Gaffer.MCP.HTTPServer.Target( Gaffer.ScriptNode() ) )

		weakServer = weakref.ref( server )
		del server
		self.assertIsNone( weakServer() )
		self.assertEqual( threading.active_count(), numThreads )

	@GafferTest.TestRunner.CategorisedTestMethod( { "mcp" } )
	def testInitialize( self ) :

		server = Gaffer.MCP.HTTPServer()
		client = self.TestClient( server.port() )

		for requested, expected in [
			( "2025-06-18", "2025-06-18" ),
			( "2025-03-26", "2025-03-26" ),
			( "1999-01-01", "2025-11-25" ),
		] :
			response = client.request( {
				"jsonrpc" : "2.0", "id" : 1, "method" : "initialize",
				"params" : { "protocolVersion" : requested, "capabilities" : {}, "clientInfo" : { "name" : "test", "version" : "1.0" } }
			} )
			self.assertEqual( response["status"], http.HTTPStatus.OK )
			result = response["body"]["result"]
			self.assertEqual( result["protocolVersion"], expected )
			self.assertEqual( result["capabilities"], { "tools" : {} } )
			self.assertEqual( result["serverInfo"]["name"], "gaffer" )
			self.assertEqual( result["serverInfo"]["version"], Gaffer.About.versionString() )
			self.assertIn( "instructions", result )

	@GafferTest.TestRunner.CategorisedTestMethod( { "mcp" } )
	def testPing( self ) :

		server = Gaffer.MCP.HTTPServer()
		client = self.TestClient( server.port() )

		response = client.request( { "jsonrpc" : "2.0", "id" : "abc", "method" : "ping" } )
		self.assertEqual( response["status"], http.HTTPStatus.OK )
		self.assertEqual( response["body"], { "jsonrpc" : "2.0", "id" : "abc", "result" : {} } )

	@GafferTest.TestRunner.CategorisedTestMethod( { "mcp" } )
	def testNotification( self ) :

		server = Gaffer.MCP.HTTPServer()
		server.addTarget( Gaffer.MCP.HTTPServer.Target( Gaffer.ScriptNode() ) )
		client = self.TestClient( server.port() )

		response = client.request( { "jsonrpc" : "2.0", "method" : "notifications/initialized" } )
		self.assertEqual( response["status"], http.HTTPStatus.ACCEPTED )
		self.assertIsNone( response["body"] )

	@GafferTest.TestRunner.CategorisedTestMethod( { "mcp" } )
	def testListTools( self ) :

		server = Gaffer.MCP.HTTPServer()
		client = self.TestClient( server.port() )

		response = client.request( { "jsonrpc" : "2.0", "id" : 1, "method" : "tools/list" } )
		tools = { t["name"] : t for t in response["body"]["result"]["tools"] }
		self.assertIn( "executePython", tools )
		self.assertIn( "Executes Python in a target", tools["executePython"]["description"] )
		self.assertEqual( tools["executePython"]["inputSchema"]["required"], [ "code" ] )
		self.assertEqual( tools["executePython"]["inputSchema"]["properties"]["code"]["type"], "string" )
		self.assertIn( "The Python code to execute", tools["executePython"]["inputSchema"]["properties"]["code"]["description"] )

		# All tools accept a `target` argument.
		for tool in tools.values() :
			self.assertIn( "target", tool["inputSchema"]["properties"] )

	@GafferTest.TestRunner.CategorisedTestMethod( { "mcp" } )
	def testErrors( self ) :

		server = Gaffer.MCP.HTTPServer()
		client = self.TestClient( server.port() )

		response = client.request( { "jsonrpc" : "2.0", "id" : 1, "method" : "resources/list" } )
		self.assertEqual( response["body"]["error"]["code"], Gaffer.MCP.Server.Error.MethodNotFound )

		response = client.request( { "jsonrpc" : "2.0", "id" : 1, "method" : "tools/call", "params" : { "name" : "notATool" } } )
		self.assertEqual( response["body"]["error"]["code"], Gaffer.MCP.Server.Error.InvalidParams )

		response = client.request( { "id" : 1, "method" : "ping" } )
		self.assertEqual( response["body"]["error"]["code"], Gaffer.MCP.Server.Error.InvalidRequest )

		response = client.request( b"{ this isn't json" )
		self.assertEqual( response["status"], http.HTTPStatus.BAD_REQUEST )

		self.assertTrue( client.executePython( 10 )["isError"] )

	@GafferTest.TestRunner.CategorisedTestMethod( { "mcp" } )
	def testUnsupportedVerbs( self ) :

		server = Gaffer.MCP.HTTPServer()
		client = self.TestClient( server.port() )

		for method in ( "GET", "DELETE" ) :
			self.assertEqual( client.request( None, method = method )["status"], http.HTTPStatus.METHOD_NOT_ALLOWED )

		self.assertEqual( client.request( { "jsonrpc" : "2.0", "id" : 1, "method" : "ping" }, path = "/notMCP" )["status"], http.HTTPStatus.NOT_FOUND )

	@GafferTest.TestRunner.CategorisedTestMethod( { "mcp" } )
	def testOrigin( self ) :

		server = Gaffer.MCP.HTTPServer()
		client = self.TestClient( server.port() )

		ping = { "jsonrpc" : "2.0", "id" : 1, "method" : "ping" }

		self.assertEqual( client.request( ping, { "Origin" : "http://localhost:3000" } )["status"], http.HTTPStatus.OK )
		self.assertEqual( client.request( ping, { "Origin" : "http://localhost" } )["status"], http.HTTPStatus.OK )
		self.assertEqual( client.request( ping, { "Origin" : "https://evil.example.com" } )["status"], http.HTTPStatus.FORBIDDEN )

	@GafferTest.TestRunner.CategorisedTestMethod( { "mcp" } )
	def testExecutePython( self ) :

		server = Gaffer.MCP.HTTPServer()
		script = Gaffer.ScriptNode()
		target = Gaffer.MCP.HTTPServer.Target( script )
		server.addTarget( target )
		client = self.TestClient( server.port() )

		result = client.executePython( "print( 'hello' )\na = 1\na + 1" )
		self.assertNotIn( "isError", result )
		self.assertEqual( result["content"][0]["type"], "text" )
		self.assertEqual( result["content"][0]["text"], "hello\n2\n" )

		# Namespace persists.
		self.assertEqual( client.executePython( "a" )["content"][0]["text"], "1\n" )
		self.assertEqual( target.namespace()["a"], 1 )

		# Results use `repr()`.
		self.assertEqual( client.executePython( "'x'" )["content"][0]["text"], "'x'\n" )

		# Access to the script and modules.
		client.executePython( "root['node'] = Gaffer.Node()" )
		self.assertIn( "node", script )
		self.assertEqual(
			client.executePython( "IECore.IntData( 2 ).value + imath.V2i( 1 ).x" )["content"][0]["text"],
			"3\n"
		)

	@GafferTest.TestRunner.CategorisedTestMethod( { "mcp" } )
	def testToolArgumentValidation( self ) :

		server = Gaffer.MCP.HTTPServer()
		server.addTarget( Gaffer.MCP.HTTPServer.Target( Gaffer.ScriptNode() ) )
		client = self.TestClient( server.port() )

		result = client.callTool( "executePython", { "code" : 10 } )
		self.assertTrue( result["isError"] )
		self.assertEqual( result["content"][0]["text"], "Argument `code` has wrong type" )

		result = client.callTool( "executePython", { "stuff" : 10 } )
		self.assertTrue( result["isError"] )
		self.assertEqual( result["content"][0]["text"], "Argument `stuff` does not exist" )

		result = client.callTool( "executePython", {} )
		self.assertTrue( result["isError"] )
		self.assertEqual( result["content"][0]["text"], "Provide `code` argument" )

	@GafferTest.TestRunner.CategorisedTestMethod( { "mcp" } )
	def testExecutionContext( self ) :

		server = Gaffer.MCP.HTTPServer()
		script = Gaffer.ScriptNode()
		server.addTarget( Gaffer.MCP.HTTPServer.Target( script ) )
		client = self.TestClient( server.port() )

		for frame in range( 1, 10 ) :

			script["frame"].setValue( frame )
			self.assertEqual(
				client.executePython(
					"Gaffer.Context.current().getFrame()"
				)["content"][0]["text"],
				f"{float(frame)}\n"
			)

	@GafferTest.TestRunner.CategorisedTestMethod( { "mcp" } )
	def testUndo( self ) :

		server = Gaffer.MCP.HTTPServer()

		script = Gaffer.ScriptNode()
		server.addTarget( Gaffer.MCP.HTTPServer.Target( script ) )

		client = self.TestClient( server.port() )
		client.executePython( "root['a'] = Gaffer.Node()\nroot['b'] = Gaffer.Node()" )
		self.assertIn( "a", script )
		self.assertIn( "b", script )

		script.undo()
		self.assertNotIn( "a", script )
		self.assertNotIn( "b", script )

	@GafferTest.TestRunner.CategorisedTestMethod( { "mcp" } )
	def testException( self ) :

		server = Gaffer.MCP.HTTPServer()
		server.addTarget( Gaffer.MCP.HTTPServer.Target( Gaffer.ScriptNode() ) )

		client = self.TestClient( server.port() )
		result = client.executePython( "a = 1\nohDearThisVariableDoesntExist" )

		self.assertTrue( result["isError"] )
		text = result["content"][0]["text"]
		self.assertIn( "NameError", text )
		self.assertIn( "ohDearThisVariableDoesntExist", text )
		self.assertIn( "line 2", text )
		# We don't want our own code to appear in the traceback.
		self.assertNotIn( "HTTPServer.py", text )

	@GafferTest.TestRunner.CategorisedTestMethod( { "mcp" } )
	def testSyntaxError( self ) :

		server = Gaffer.MCP.HTTPServer()
		server.addTarget( Gaffer.MCP.HTTPServer.Target( Gaffer.ScriptNode() ) )

		client = self.TestClient( server.port() )

		for code in [ "a = ", "return 10" ] :
			result = client.executePython( code )
			self.assertTrue( result["isError"] )
			self.assertIn( "SyntaxError", result["content"][0]["text"] )

	@GafferTest.TestRunner.CategorisedTestMethod( { "mcp" } )
	def testMessages( self ) :

		server = Gaffer.MCP.HTTPServer()
		server.addTarget( Gaffer.MCP.HTTPServer.Target( Gaffer.ScriptNode() ) )
		client = self.TestClient( server.port() )

		result = client.executePython( "IECore.msg( IECore.Msg.Level.Warning, 'MCPServerTest', 'Alert!' )" )
		self.assertIn( "WARNING : MCPServerTest : Alert!", result["content"][0]["text"] )

	@GafferTest.TestRunner.CategorisedTestMethod( { "mcp" } )
	def testOutputTruncation( self ) :

		server = Gaffer.MCP.HTTPServer()
		server.addTarget( Gaffer.MCP.HTTPServer.Target( Gaffer.ScriptNode() ) )
		client = self.TestClient( server.port() )

		text = client.executePython( "print( 'a' * 1000000 )" )["content"][0]["text"]
		self.assertLess( len( text ), 101000 )
		self.assertIn( "characters omitted", text )

	@GafferTest.TestRunner.CategorisedTestMethod( { "mcp" } )
	def testMultipleTargets( self ) :

		server = Gaffer.MCP.HTTPServer()

		script1 = Gaffer.ScriptNode()
		script1["fileName"].setValue( "/path/to/one.gfr" )
		target1 = Gaffer.MCP.HTTPServer.Target( script1 )
		server.addTarget( target1 )

		script2 = Gaffer.ScriptNode()
		script2["fileName"].setValue( "/path/to/two.gfr" )
		target2 = Gaffer.MCP.HTTPServer.Target( script2 )
		server.addTarget( target2 )

		client = self.TestClient( server.port() )

		# Ambiguous without a target. Error lists the available targets.

		result = client.executePython( "root['n'] = Gaffer.Node()" )
		self.assertTrue( result["isError"] )
		text = result["content"][0]["text"]
		self.assertIn( "one : /path/to/one.gfr", text )
		self.assertIn( "two : /path/to/two.gfr", text )
		self.assertNotIn( "n", script1 )
		self.assertNotIn( "n", script2 )

		# Unknown targets also list the available targets.

		result = client.executePython( "1", target = "three" )
		self.assertTrue( result["isError"] )
		self.assertIn( "Target \"three\" does not exist", result["content"][0]["text"] )
		self.assertIn( "one : /path/to/one.gfr", result["content"][0]["text"] )

		# Explicit targets.

		result = client.executePython( "root['n'] = Gaffer.Node()", target = "two" )
		self.assertNotIn( "n", script1 )
		self.assertIn( "n", script2 )

		# Removed targets are no longer available.

		server.removeTarget( target2 )
		result = client.executePython( "1", target = "two" )
		self.assertTrue( result["isError"] )
		self.assertIn( "one : /path/to/one.gfr", result["content"][0]["text"] )
		self.assertNotIn( "two :", result["content"][0]["text"] )

		# And we don't need to specify a target when there is only one.

		result = client.executePython( "1" )
		self.assertNotIn( "isError", result )
		self.assertEqual( result["content"][0]["text"], "1\n" )

	@GafferTest.TestRunner.CategorisedTestMethod( { "mcp" } )
	def testAmbiguousTarget( self ) :

		server = Gaffer.MCP.HTTPServer()

		for i in range( 2 ) :
			script = Gaffer.ScriptNode()
			script["fileName"].setValue( f"/dir{i}/duplicated.gfr" )
			server.addTarget( Gaffer.MCP.HTTPServer.Target( script ) )

		client = self.TestClient( server.port() )
		result = client.executePython( "1", target = "duplicated" )
		self.assertTrue( result["isError"] )
		self.assertEqual(
			result["content"][0]["text"],
			"Multiple targets named \"duplicated\". Please save each target with a unique name."
		)

	@GafferTest.TestRunner.CategorisedTestMethod( { "mcp" } )
	def testNoTargets( self ) :

		server = Gaffer.MCP.HTTPServer()
		client = self.TestClient( server.port() )

		result = client.executePython( "1" )
		self.assertTrue( result["isError"] )
		self.assertIn( "No targets are available.", result["content"][0]["text"] )

	@GafferTest.TestRunner.CategorisedTestMethod( { "mcp" } )
	def testCustomTool( self ) :

		class HelloWorldTool( Gaffer.MCP.BasicTool ) :

			def __init__( self ) :

				Gaffer.MCP.BasicTool.__init__(
					self,
					"helloWorld",
					"Says hello",
					{
						"name" : "The person to greet"
					}
				)

				self.callsMade = []

			def _call( self, target, name = "World" ) :

				self.callsMade.append( ( target, name ) )
				return self.textResult( f"Hello {name}" )

		tool = HelloWorldTool()
		Gaffer.MCP.Tool.registerTool( tool )
		self.addCleanup( Gaffer.MCP.Tool.deregisterTool, tool )

		server = Gaffer.MCP.HTTPServer()
		script = Gaffer.ScriptNode()
		target = Gaffer.MCP.HTTPServer.Target( script )
		server.addTarget( target )

		client = self.TestClient( server.port() )

		# Check tool is listed by the server.

		tools = { t["name"] : t for t in client.request( { "jsonrpc" : "2.0", "id" : 1, "method" : "tools/list" } )["body"]["result"]["tools"] }
		self.assertIn( "helloWorld", tools )
		self.assertEqual( set( tools["helloWorld"]["inputSchema"]["properties"].keys() ), { "name", "target" } )

		# Call it without arguments, and check we get the
		# default argument.

		result = client.callTool( "helloWorld", {} )
		self.assertNotIn( "isError", result )
		self.assertEqual( result["content"][0]["text"], "Hello World" )
		self.assertEqual( len( tool.callsMade ), 1 )
		self.assertEqual( tool.callsMade[-1], ( target, "World" ) )

		result = client.callTool( "helloWorld", { "name" : "Gaffer" } )
		self.assertNotIn( "isError", result )
		self.assertEqual( result["content"][0]["text"], "Hello Gaffer" )
		self.assertEqual( len( tool.callsMade ), 2 )
		self.assertEqual( tool.callsMade[-1], ( target, "Gaffer" ) )

		Gaffer.MCP.Tool.deregisterTool( tool )
		response = client.request( {
			"jsonrpc" : "2.0", "id" : 1, "method" : "tools/call", "params" : { "name" : "testHello", "arguments" : {} }
		} )
		self.assertEqual( response["body"]["error"]["code"], Gaffer.MCP.Server.Error.InvalidParams )

	@GafferTest.TestRunner.CategorisedTestMethod( { "mcp" } )
	def testImageResult( self ) :

		result = Gaffer.MCP.Tool.imageResult( "An image", b"\x89PNGdata" )
		self.assertEqual( result["content"][0], { "type" : "text", "text" : "An image" } )
		self.assertEqual( result["content"][1]["type"], "image" )
		self.assertEqual( result["content"][1]["mimeType"], "image/png" )
		self.assertEqual( result["content"][1]["data"], "iVBOR2RhdGE=" )
		self.assertNotIn( "isError", result )

	@GafferTest.TestRunner.CategorisedTestMethod( { "mcp" } )
	def testToolCalledSignal( self ) :

		server = Gaffer.MCP.HTTPServer()
		script = Gaffer.ScriptNode()
		target = Gaffer.MCP.HTTPServer.Target( script )
		server.addTarget( target )

		cs = GafferTest.CapturingSlot( target.toolCalledSignal() )
		client = self.TestClient( server.port() )
		result = client.executePython( "print( 10 )" )

		self.assertEqual( len( cs ), 1 )
		self.assertEqual( cs[0][0], "executePython" )
		self.assertEqual( cs[0][1], { "code" : "print( 10 )" } )
		self.assertEqual( cs[0][2], result )
