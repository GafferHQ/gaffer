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

import copy
import enum
import inspect
import pathlib
import sys

import imath

import IECore

import Gaffer

## Base class for minimal [Model Context Protocol](https://modelcontextprotocol.io)
# servers, allowing MCP clients such as coding agents to run tools in Gaffer.
class Server( object ) :

	## JSON-RPC error codes.
	class Error( enum.IntEnum ) :

		ParseError = -32700
		InvalidRequest = -32600
		MethodNotFound = -32601
		InvalidParams = -32602
		InternalError = -32603

	# Targets
	# =======
	#
	# Targets are ScriptNodes which have been explicitly made
	# available for use via MCP.
	#
	# > Note : Nothing stops a client from running Python code
	# > that will affect other scripts in Gaffer. Targets are
	# > just a convenience to allow a user to direct a client to
	# > operate on a particular script.

	class Target( object ) :

		def __init__( self, scriptNode, namespace = None ) :

			self.__scriptNode = scriptNode

			if namespace is not None :
				self.__namespace = namespace
			else :
				self.__namespace = {
					name : module for name, module in sys.modules.items()
					if "." not in name and ( name.startswith( "Gaffer" ) or name.startswith( "IECore" ) )
				}
				self.__namespace["imath"] = imath
				self.__namespace["root"] = self.__scriptNode

			self.__toolCalledSignal = Gaffer.Signal3()

		## Targets are identified by a name derived from the script's
		# filename, since this is already available and is familiar to
		# the user.
		def name( self ) :

			fileName = self.scriptNode()["fileName"].getValue()
			if fileName :
				return pathlib.Path( fileName ).with_suffix( "" ).name
			else :
				return "untitled"

		def scriptNode( self ) :

			return self.__scriptNode

		## A Python dictionary that provides a shared namespace for code
		# execution. This allows tools to share state, and for state to persist
		# between tool calls. It is useful in particular to the built-in
		# `executePython` tool.
		def namespace( self ) :

			return self.__namespace

		## Signal emitted when tools are called. Arguments are
		# `toolName`, `arguments` and `result`.
		def toolCalledSignal( self ) :

			return self.__toolCalledSignal

	def __init__( self ) :

		self.__targets = set()

	def addTarget( self, target ) :

		self.__targets.add( target )

	def removeTarget( self, target ) :

		self.__targets.remove( target )

	def targets( self ) :

		return list( self.__targets )

	# Methods for use by subclasses
	# =============================

	## Returns the response to a JSON-RPC `request`, or `None` if no response
	# is needed. Expected to be called on the main thread by Server subclasses.
	def _handleRequest( self, request ) :

		if not isinstance( request, dict ) or request.get( "jsonrpc" ) != "2.0" :
			return self._errorResponse( None, self.Error.InvalidRequest )

		if "method" not in request :
			# A response to a request. We never make requests, so there is
			# nothing to do.
			return None

		if "id" not in request :
			# A notification. We have no use for any of them.
			return None

		id = request["id"]
		method = {
			"initialize" : self.__initialize,
			"ping" : self.__ping,
			"tools/list" : self.__listTools,
			"tools/call" : self.__callTool,
		}.get( request["method"] )

		if method is None :
			return self._errorResponse( id, self.Error.MethodNotFound, request["method"] )

		params = request.get( "params" ) or {}
		if not isinstance( params, dict ) :
			return self._errorResponse( id, self.Error.InvalidParams )

		try :
			result = method( params )
		except _InvalidParams as e :
			return self._errorResponse( id, self.Error.InvalidParams, str( e ) )
		except Exception as e :
			return self._errorResponse( id, self.Error.InternalError, str( e ) )

		return { "jsonrpc" : "2.0", "id" : id, "result" : result }

	@staticmethod
	def _errorResponse( id, code, detail = None ) :

		# Convert `MethodNotFound` to `Method not found` etc.
		message = IECore.CamelCase.toSpaced( code.name ).capitalize()
		if detail :
			message = f"{message} : {detail}"

		return { "jsonrpc" : "2.0", "id" : id, "error" : { "code" : code, "message" : message } }

	# Internal implementation
	# =======================

	__protocolVersions = [ "2025-03-26", "2025-06-18", "2025-11-25" ]

	__instructions = inspect.cleandoc(
		"""
		Provides access to "targets" - Gaffer scripts that the user has made available to MCP.
		If several targets are enabled, pass `target` to each tool; calling a tool without it
		lists the available targets. In the GUI, tools run on the UI thread and block it until
		they complete, so avoid long-running operations.
		"""
	)

	def __initialize( self, params ) :

		protocolVersion = params.get( "protocolVersion" )
		if protocolVersion not in self.__protocolVersions :
			protocolVersion = self.__protocolVersions[-1]

		return {
			"protocolVersion" : protocolVersion,
			"capabilities" : { "tools" : {} },
			"serverInfo" : {
				"name" : "gaffer",
				"title" : "Gaffer",
				"version" : Gaffer.About.versionString(),
			},
			"instructions" : self.__instructions,
		}

	def __ping( self, params ) :

		return {}

	def __listTools( self, params ) :

		# On top of the tool's own `inputSchema`, we add on a `target` property to determine
		# which target to dispatch the tool to.
		serverProperties = {
			"target" : {
				"type" : "string",
				"description" : "The name of the target. Optional if only one target is enabled.",
			}
		}

		tools = []
		for tool in Gaffer.MCP.Tool.registeredTools().values() :
			definition = copy.deepcopy( tool.definition() )
			definition["inputSchema"]["properties"].update( serverProperties )
			tools.append( definition )

		return { "tools" : tools }

	def __callTool( self, params ) :

		tool = Gaffer.MCP.Tool.registeredTools().get( params.get( "name" ) )
		if tool is None :
			raise _InvalidParams( "Unknown tool \"{}\"".format( params.get( "name" ) ) )

		arguments = params.get( "arguments" ) or {}
		if not isinstance( arguments, dict ) :
			return Gaffer.MCP.Tool.errorResult( "The arguments must be an object." )

		targetName = arguments.get( "target" )
		if targetName is not None :
			if not isinstance( targetName, str ) :
				return Gaffer.MCP.Tool.errorResult( "The `target` argument must be a string." )
			# This one's for us, not the tool.
			del arguments["target"]

		namedTargets = self.__namedTargets()
		if targetName is None :
			if len( namedTargets ) == 1 :
				targetName = next( iter( namedTargets.keys() ) )
			elif len( namedTargets ) == 0 :
				return Gaffer.MCP.Tool.errorResult( "No targets are available." )
			else :
				return Gaffer.MCP.Tool.errorResult(
					"Multiple targets are available. Specify one with the `target` argument.\n\n{}".format( self.__targetListing() )
				)

		targetsWithName = namedTargets.get( targetName, [] )
		if len( targetsWithName ) == 1 :
			target = targetsWithName[0]
			result = tool.call( target, arguments )
			target.toolCalledSignal()( params.get( "name" ), arguments, result )
			return result
		elif len( targetsWithName ) == 0 :
			return Gaffer.MCP.Tool.errorResult(
				"Target \"{}\" does not exist.\n\n{}".format( targetName, self.__targetListing() )
			)
		else :
			return Gaffer.MCP.Tool.errorResult( f"Multiple targets named \"{targetName}\". Please save each target with a unique name." )

	# Returns a dict mapping names to lists of targets with that name (because
	# names are derived from the filename, they are not necessarily unique).
	def __namedTargets( self ) :

		result = {}
		for target in self.__targets :
			result.setdefault( target.name(), [] ).append( target )

		return result

	def __targetListing( self ) :

		if not self.__targets :
			return "No targets available."

		lines = [ "Available targets :" ]
		for name, targets in sorted( self.__namedTargets().items() ) :
			if len( targets ) == 1 :
				lines.append( "- {} : {}".format( name, targets[0].scriptNode()["fileName"].getValue() or "untitled" ) )
			else :
				lines.append( "- {} : Ambiguous. Please save each target with a unique name.".format( name ) )

		return "\n".join( lines )

class _InvalidParams( Exception ) :

	pass
