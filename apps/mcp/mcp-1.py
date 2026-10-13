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

import os
import pathlib
import sys

import IECore

import Gaffer

class mcp( Gaffer.Application ) :

	def __init__( self ) :

		Gaffer.Application.__init__(
			self,
			"""
			Makes scripts available to MCP clients such as coding agents.
			Clients should launch the application themselves, and communicate
			with it directly using the MCP stdio transport.

			Each script is made available as a target. If no scripts are
			specified, a new empty script is made available. The application
			exits when the client closes its input.

			> Tip : To configure Claude Code to use a `gaffer mcp` server for
			> the duration of each session, run this command :
			>
			> `claude mcp add gaffer-headless -- gaffer mcp`

			> Caution : This gives clients full control over Gaffer, and >
			anything else that can be done with Python.
			"""
		)

		self.parameters().addParameters(

			[
				IECore.StringVectorParameter(
					name = "scripts",
					description = "The scripts to make available to clients.",
					defaultValue = IECore.StringVectorData( [] ),
				),

				IECore.BoolParameter(
					name = "ignoreScriptLoadErrors",
					description = "Causes errors which occur while loading the scripts "
						"to be ignored. Not recommended.",
					defaultValue = False,
				),
			]

		)

		self.parameters().userData()["parser"] = IECore.CompoundObject(
			{
				"flagless" : IECore.StringVectorData( [ "scripts" ] )
			}
		)

	def _run( self, args ) :

		# Stdout is reserved for MCP messages, and any other output on it
		# will corrupt the stream. Keep the real stdout for ourselves, and
		# redirect file descriptor 1 to stderr so that nothing written by
		# other code can cause any harm.

		sys.stdout.flush()
		output = os.fdopen( os.dup( 1 ), "wb" )
		os.dup2( 2, 1 )

		scripts = self.__loadScripts( args )
		if scripts is None :
			return 1

		# The server runs on a background thread, but uses `ParallelAlgo.callOnUIThread()`
		# for running tools. So we use a UIThreadCallHandler to service those calls.
		# It's a little ugly that we're using GafferTest functionality here, but it does
		# exactly what we need.
		import GafferTest
		with GafferTest.ParallelAlgoTest.UIThreadCallHandler() as callHandler :

			server = Gaffer.MCP.StreamServer( sys.stdin, output )

			for script in scripts :
				target = Gaffer.MCP.Server.Target( script )
				server.addTarget( target )
				sys.stderr.write( "gaffer mcp : Serving \"{}\" ({})\n".format(
					target.name(), target.scriptNode()["fileName"].getValue() or "unsaved"
				) )

			while not server.closed() :
				callHandler.waitFor( 0.01 )

		return 0

	def __loadScripts( self, args ) :

		scripts = []
		for fileName in args["scripts"] :
			script = Gaffer.ScriptNode()
			script["fileName"].setValue( pathlib.Path( fileName ).absolute() )
			try :
				script.load( continueOnError = args["ignoreScriptLoadErrors"].value )
			except Exception as exception :
				IECore.msg( IECore.Msg.Level.Error, "gaffer mcp : loading \"{}\"".format( fileName ), str( exception ) )
				return None
			scripts.append( script )

		if not scripts :
			scripts.append( Gaffer.ScriptNode() )

		for script in scripts :
			self.root()["scripts"].addChild( script )

		return scripts

IECore.registerRunTimeTyped( mcp )
