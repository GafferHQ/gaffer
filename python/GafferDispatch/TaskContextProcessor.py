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

import IECore

import Gaffer
import GafferDispatch

## \todo Since we can now use regular Gaffer.ContextProcessors
# with TaskNodes, the only legitimate subclass of TaskContextProcessor
# is the Wedge node. So we could probably just remove the
# TaskContextProcessor class entirely.
class TaskContextProcessor( GafferDispatch.TaskNode ) :

	def __init__( self, name = "TaskContextProcessor" ) :

		GafferDispatch.TaskNode.__init__( self, name )

	def preTasks( self, context ) :

		contexts = self._processedContexts( context )

		result = []
		for plug in self["preTasks"] :
			result.extend( [ self.Task( plug, c ) for c in contexts ] )

		return result

	def hash( self, context ) :

		# Our hash is empty to signify that we don't do
		# anything in execute().
		return IECore.MurmurHash()

	def execute( self ) :

		# We don't need to do anything here because our
		# sole purpose is to manipulate the context
		# in which our preTasks are executed.
		pass

	## Must be implemented by derived classes to return
	# a list of contexts to be used by upstream tasks.
	def _processedContexts( self, context ) :

		raise NotImplementedError

IECore.registerRunTimeTyped( TaskContextProcessor, typeName = "GafferDispatch::TaskContextProcessor" )
