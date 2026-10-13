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

import ast
import base64
import inspect
import sys
import threading
import traceback
import typing

import IECore

import Gaffer

# Tools provide the functionality that clients of Server will
# use to interact with Gaffer. The base Tool class provides the full
# generality of the MCP specification, but typically you would derive
# from BasicTool for simplicity of implementation.
class Tool :

	def __init__( self, definition ) :

		self.__definition = definition

	# The tool's MCP definition - a dictionary with at least "name",
	# "description" and "inputSchema" keys.
	#
	# See https://modelcontextprotocol.io/specification/2025-11-25/server/tools#tool.
	def definition( self ) :

		return self.__definition

	# Called by the Server to invoke the tool. Receives `arguments`
	# from the client, and is responsible for their validation.
	# Should return a result conforming to the MCP specification.
	# Typically this means one of `textResult()`, `imageResult()`
	# or `errorResult()`.
	#
	# See https://modelcontextprotocol.io/specification/2025-11-25/server/tools#tool-result.
	def call( self, target, arguments ) :

		raise NotImplementedError

	# Utilities
	# =========

	# Returns a tool result containing `text`. Long text is truncated
	# to avoid burning context.
	@classmethod
	def textResult( cls, text ) :

		maxOutputLength = 100000

		if len( text ) > maxOutputLength :
			half = maxOutputLength // 2
			text = "{}\n\n[... {} characters omitted ...]\n\n{}".format(
				text[:half], len( text ) - 2 * half, text[-half:]
			)

		return {
			"content" : [ { "type" : "text", "text" : text } ],
		}

	# Returns an error result.
	@classmethod
	def errorResult( cls, errorMessage ) :

		result = cls.textResult( errorMessage )
		result["isError"] = True
		return result

	# Returns a tool result containing `text` and a PNG image.
	@classmethod
	def imageResult( cls, text, pngData ) :

		result = cls.textResult( text )
		result["content"].append( {
			"type" : "image",
			"data" : base64.b64encode( pngData ).decode( "ascii" ),
			"mimeType" : "image/png",
		} )

		return result

	# Registry
	# ========

	## Registers a tool, which will be available to the clients of all Servers.
	@classmethod
	def registerTool( cls, tool ) :

		cls.__tools[tool.definition()["name"]] = tool

	@classmethod
	def deregisterTool( cls, tool ) :

		# Allow deregistration by name or instance.
		cls.__tools.pop( tool.definition()["name"] if isinstance( tool, Tool ) else tool, None )

	@classmethod
	def registeredTools( cls ) :

		return dict( cls.__tools )

	__tools = {}

# Tool subclass to simplify the process of making tools.
# Automatically builds the JSON `inputSchema` by introspecting
# the parameters of the `_call()` method, and validates incoming
# arguments before passing them to `_call()`.
class BasicTool( Tool ) :

	__jsonSchemaTypes = {
		str : "string",
		int : "integer",
		float : "number",
		bool : "boolean",
		list : "array",
		dict : "object",
	}

	def __init__( self, name, description, parameterDescriptions ) :

		self.__requiredArguments = set()
		self.__argumentTypes = {}

		properties = {}
		for parameter in inspect.signature( self._call ).parameters.values() :

			if parameter.name == "target" :
				continue

			assert( parameter.kind == parameter.POSITIONAL_OR_KEYWORD )

			property = {}

			if parameter.default != inspect.Parameter.empty :
				parameterType = type( parameter.default )
				property["default"] = repr( parameter.default )
			else :
				if parameter.annotation is inspect.Parameter.empty :
					raise TypeError( f"Parameter `{parameter.name}` must have a type annotation" )
				parameterType = typing.get_origin( parameter.annotation ) or parameter.annotation
				self.__requiredArguments.add( parameter.name )

			self.__argumentTypes[parameter.name] = parameterType
			property["type"] = self.__jsonSchemaTypes[parameterType]
			property["description"] = inspect.cleandoc( parameterDescriptions[parameter.name] )

			properties[parameter.name] = property

		Tool.__init__(
			self,
			{
				"name" : name,
				"description" : description,
				"inputSchema" : {
					"type" : "object",
					"properties" : properties,
					"required" : list( self.__requiredArguments ),
				},
			}
		)

	def call( self, target, arguments ) :

		for argument, value in arguments.items() :
			if argument not in self.__argumentTypes :
				return self.errorResult( f"Argument `{argument}` does not exist" )
			elif not isinstance( value, self.__argumentTypes[argument] ) :
				return self.errorResult( f"Argument `{argument}` has wrong type" )

		for argument in self.__requiredArguments :
			if argument not in arguments :
				return self.errorResult( f"Provide `{argument}` argument" )

		return self._call( target, **arguments )

# We find a single `executePython` call to be sufficient versus providing many
# tools that each wrap some aspect of Gaffer's API individually. Claude at least
# seems to know Gaffer's API plenty well enough.
class ExecutePythonTool( BasicTool ) :

	def __init__( self ) :

		BasicTool.__init__(

			self,

			"executePython",

			"""
			Executes Python in a target script. `root` is the ScriptNode, and
			all loaded Gaffer and IECore modules are available, along with
			`imath`. Variables persist between calls. If the last statement is
			an expression, its `repr()` is returned. `stdout`, `stderr` and
			IECore messages are captured. Each call is a single undoable step.
			""",

			parameterDescriptions = {

				"code" : "The Python code to execute."

			}

		)

	def _call( self, target, code: str ) :

		assert( threading.current_thread() == threading.main_thread() )

		output = []
		try :
			statements, expression = self.__compile( code )
		except SyntaxError as e :
			return self.errorResult(
				"".join( traceback.format_exception_only( SyntaxError, e ) )
			)

		with Gaffer.OutputRedirection( stdOut = output.append, stdErr = output.append ) :
			with _CapturingMessageHandler( output ) :
				with Gaffer.UndoScope( target.scriptNode() ) :
					with target.scriptNode().context() :
						try :
							exec( statements, target.namespace(), target.namespace() )
							if expression is not None :
								value = eval( expression, target.namespace(), target.namespace() )
								if value is not None :
									output.append( repr( value ) + "\n" )
						except Exception :
							output.append( self.__exceptionText() )
							return self.errorResult( "".join( output ) )

		return self.textResult( "".join( output ) )

	# Returns `( statements, expression )`, compiled from `code`. If the last
	# statement is an expression, it is split off into `expression` so that it can
	# be evaluated and its result returned. Otherwise `expression` is `None`.
	@staticmethod
	def __compile( code ) :

		parsed = ast.parse( code )
		expression = None
		if parsed.body and isinstance( parsed.body[-1], ast.Expr ) :
			expression = compile( ast.Expression( parsed.body.pop().value ), "<string>", "eval" )

		return compile( parsed, "<string>", "exec" ), expression

	# Formats the exception currently being handled, omitting the first frame,
	# which is in our code rather than the executed code.
	@staticmethod
	def __exceptionText() :

		exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
		return "".join( traceback.format_exception( exceptionType, exceptionValue, exceptionTraceback.tb_next ) )

Tool.registerTool( ExecutePythonTool() )

# Used to capure `IECore.msg()` output during execution, interleaving
# it with the `stdout` and `stderr` redirection from OutputRedirection.
class _CapturingMessageHandler( IECore.MessageHandler ) :

	def __init__( self, output ) :

		IECore.MessageHandler.__init__( self )
		self.__output = output

	def handle( self, level, context, message ) :

		self.__output.append(
			"{} : {} : {}\n".format( IECore.Msg.levelAsString( level ), context, message )
		)
