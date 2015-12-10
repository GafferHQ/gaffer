##########################################################################
#
#  Copyright (c) 2013-2015, Image Engine Design Inc. All rights reserved.
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
import GafferTest
import GafferDispatch

## \todo Remove this in preference to LoggingExecutableNode.
class CountingExecutableNode( GafferDispatch.ExecutableNode ) :

	def __init__( self, name = "CountingExecutableNode", withHash = True, requiresSequenceExecution = False ) :

		GafferDispatch.ExecutableNode.__init__( self, name )

		self.__requiresSequenceExecution = requiresSequenceExecution
		self.__withHash = withHash

		self.executionCount = 0

	def execute( self ) :

		self.executionCount += 1

	def executeSequence( self, frames ) :

		if not self.__requiresSequenceExecution :
			GafferDispatch.ExecutableNode.executeSequence( self, frames )
			return

		self.executionCount += 1

	def hash( self, context ) :

		if not self.__withHash :
			return IECore.MurmurHash()

		h = GafferDispatch.ExecutableNode.hash( self, context )
		h.append( context.getFrame() )
		return h

	def requiresSequenceExecution( self ) :

		return self.__requiresSequenceExecution

IECore.registerRunTimeTyped( CountingExecutableNode, typeName = "GafferDispatchTest::CountingExecutableNode" )
