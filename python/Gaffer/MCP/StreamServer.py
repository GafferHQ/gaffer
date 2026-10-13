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

import functools
import io
import json
import threading

import Gaffer

from . import Server

## Implements MCP over standard streams.
class StreamServer( Server ) :

	def __init__( self, inStream, outStream ) :

		Server.__init__( self )

		self.__in = io.TextIOWrapper( inStream.buffer, encoding = "utf-8" )
		self.__out = io.TextIOWrapper( outStream,  encoding = "utf-8", newline = "\n" )

		threading.Thread(
			target = self.__readInput,
			name = "Gaffer.MCP.StreamServer",
			daemon = True
		).start()

		self.__closed = False

	def closed( self ) :

		return self.__closed

	def __readInput( self ) :

		for line in self.__in :

			line = line.strip()
			if not line :
				continue

			try :
				request = json.loads( line )
			except ValueError :
				Gaffer.ParallelAlgo.callOnUIThread(
					functools.partial(
						self.__write,
						json.dumps( self._errorResponse( None, Gaffer.MCP.Server.Error.ParseError ) ) + "\n"
					)
				)
				continue

			Gaffer.ParallelAlgo.callOnUIThread(
				functools.partial( self.__handleRequestAndWriteResponse, request )
			)

		Gaffer.ParallelAlgo.callOnUIThread( self.__close )

	def __handleRequestAndWriteResponse( self, request ) :

		response = self._handleRequest( request )
		if response is not None :
			self.__write( json.dumps( response ) + "\n" )

	def __write( self, text ) :

		self.__out.write( text )
		self.__out.flush()

	def __close( self ) :

		self.__closed = True
