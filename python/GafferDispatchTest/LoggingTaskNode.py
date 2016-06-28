##########################################################################
#
#  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

import collections

import IECore

import Gaffer
import GafferDispatch

class LoggingTaskNode( GafferDispatch.TaskNode ) :

	LogEntry = collections.namedtuple( "LogEntry", [ "node", "context", "frames" ] )

	def __init__( self, name = "LoggingTaskNode", log = None ) :

		GafferDispatch.TaskNode.__init__( self, name )

		self["noOp"] = Gaffer.BoolPlug()
		self["requiresSequenceExecution"] = Gaffer.BoolPlug()

		self.log = log if log is not None else []

	def execute( self ) :

		self.log.append(
			self.LogEntry(
				node = self,
				context = Gaffer.Context( Gaffer.Context.current() ),
				frames = None
			)
		)

	def executeSequence( self, frames ) :

		if not self["requiresSequenceExecution"].getValue() :
			GafferDispatch.TaskNode.executeSequence( self, frames )
			return

		self.log.append(
			self.LogEntry(
				node = self,
				context = Gaffer.Context( Gaffer.Context.current() ),
				frames = frames
			)
		)

	def hash( self, context ) :

		if self["noOp"].getValue() :
			return IECore.MurmurHash()

		h = GafferDispatch.TaskNode.hash( self, context )

		# Hash in any additional plugs that have been added after construction.
		# This allows the test cases to customise the hashing by adding plugs
		# and connecting them as required.
		for plug in self.children( Gaffer.ValuePlug ) :
			if plug.getName() in ( "noOp", "requiresSequenceExecution" ) :
				continue
			plug.hash( h )

		return h

	def requiresSequenceExecution( self ) :

		return self["requiresSequenceExecution"].getValue()

IECore.registerRunTimeTyped( LoggingTaskNode, typeName = "GafferDispatchTest::LoggingTaskNode" )
