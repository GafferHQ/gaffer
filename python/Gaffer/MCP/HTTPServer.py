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

import http.server
import json
import os
import sys
import threading
import urllib.parse
import weakref

import Gaffer

from . import Server

## Implements MCP over HTTP.
class HTTPServer( Server ) :

	def __init__( self, port = 0 ) :

		Server.__init__( self )

		# Opening the server on `localhost` so that only processes
		# on this machine can connect to it.
		self.__httpServer = _HTTPServer( ( "localhost", port ), self )

	## Acquires a default shared server for this process, with
	# the port number specified by the GAFFER_MCP_PORT environment
	# variable.
	@classmethod
	def acquireDefaultServer( cls ) :

		if cls.__defaultServer is None :
			cls.__defaultServer = HTTPServer( int( os.environ.get( "GAFFER_MCP_PORT", "8765" ) ) )

		return cls.__defaultServer

	__defaultServer = None

	## Returns the port the server is listening on.
	def port( self ) :

		return self.__httpServer.server_address[1]

	## Returns the URL clients should use to connect.
	def url( self ) :

		return "http://localhost:{}/mcp".format( self.port() )

# Internal implementation for HTTPServer. Handles one request at a time,
# on a single thread. There is no benefit to handling requests concurrently
# via multiple threads, because they all get serviced serially through
# `callOnUIThread()` anyway.
class _HTTPServer( http.server.HTTPServer ) :

	# On Windows, `SO_REUSEADDR` allows a second process to bind a port
	# that is already in use, which we definitely don't want.
	allow_reuse_address = sys.platform != "win32"

	# Starts serving on a background thread, stopping automatically when
	# `mcpServer` dies.
	def __init__( self, address, mcpServer ) :

		http.server.HTTPServer.__init__( self, address, _RequestHandler )

		# Must not reference `mcpServer`, otherwise it would never die.
		# Once it has died, we stop our server thread so we die with it.
		self.mcpServer = weakref.ref( mcpServer, self.__mcpServerDied )
		threading.Thread(
			name = "Gaffer.MCP.HTTPServer", daemon = True,
			target = self.serve_forever,
			kwargs = { "poll_interval" : 0.1 },
		).start()

	def __mcpServerDied( self, ref ) :

		self.shutdown()
		self.server_close()

# Implements the "Streamable HTTP" transport in its simplest form, responding to
# each POST with a single JSON response.
class _RequestHandler( http.server.BaseHTTPRequestHandler ) :

	protocol_version = "HTTP/1.1"
	server_version = "GafferMCP"
	# Socket timeout, so that a client that stalls mid-request can't block
	# the server indefinitely.
	timeout = 10

	def do_POST( self ) :

		if not self.__authorised() :
			return

		mcpServer = self.server.mcpServer()
		if mcpServer is None :
			# Server has died.
			self.__send( http.HTTPStatus.SERVICE_UNAVAILABLE )
			return

		try :
			length = int( self.headers.get( "Content-Length", 0 ) )
			request = json.loads( self.rfile.read( length ) )
		except ValueError :
			self.__sendJSON(
				http.HTTPStatus.BAD_REQUEST,
				mcpServer._errorResponse( None, Gaffer.MCP.Server.Error.ParseError )
			)
			return

		## \todo Make `callOnUIThread()` accept a `waitForResult()`
		# argument so we don't have to retrieve the response ourselves.
		event = threading.Event()
		def handleRequest() :
			event.response = mcpServer._handleRequest( request )
			event.set()

		Gaffer.ParallelAlgo.callOnUIThread( handleRequest )
		event.wait()

		if event.response is None :
			self.__send( http.HTTPStatus.ACCEPTED )
		else :
			self.__sendJSON( http.HTTPStatus.OK, event.response )

	def do_GET( self ) :

		# We don't provide an SSE stream for server-initiated messages.
		if self.__authorised() :
			self.__send( http.HTTPStatus.METHOD_NOT_ALLOWED, { "Allow" : "POST" } )

	def do_DELETE( self ) :

		# We don't use sessions, so there is nothing to delete.
		if self.__authorised() :
			self.__send( http.HTTPStatus.METHOD_NOT_ALLOWED, { "Allow" : "POST" } )

	def log_message( self, format, *args ) :

		# Don't spam the terminal with a line for every request.
		pass

	def __authorised( self ) :

		if urllib.parse.urlsplit( self.path ).path != "/mcp" :
			self.__send( http.HTTPStatus.NOT_FOUND )
			return False

		# Guard against DNS rebinding attacks, whereby a web page in a browser
		# could otherwise make requests to us.
		origin = self.headers.get( "Origin" )
		if origin is not None and urllib.parse.urlsplit( origin ).hostname not in ( "localhost", "127.0.0.1", "::1" ) :
			self.__send( http.HTTPStatus.FORBIDDEN )
			return False

		return True

	def __sendJSON( self, status, data ) :

		self.__send( status, { "Content-Type" : "application/json" }, json.dumps( data ).encode( "utf-8" ) )

	def __send( self, status, headers = {}, body = b"" ) :

		# Close the connection after every response. The server only handles
		# one connection at a time, so a client holding one open would block
		# all others.
		self.close_connection = True

		self.send_response( status )
		for key, value in headers.items() :
			self.send_header( key, value )
		self.send_header( "Content-Length", str( len( body ) ) )
		self.send_header( "Connection", "close" )
		self.end_headers()
		self.wfile.write( body )
