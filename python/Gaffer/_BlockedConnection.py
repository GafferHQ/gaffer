##########################################################################
#
#  Copyright (c) 2011, John Haddon. All rights reserved.
#  Copyright (c) 2012, Image Engine Design Inc. All rights reserved.
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

import Gaffer

# This isn't a direct binding of the C++ class because
# binding C++ scopes as Python context managers isn't
# completely straightforward, and in Python it is useful
# to provide the additional functionality of passing multiple
# connections.
class BlockedConnection( object ) :

	def __init__( self, connectionOrConnections ) :

		if isinstance( connectionOrConnections, Gaffer.Signals.Connection ) :
			self.__connections = [ connectionOrConnections ]
		else :
			self.__connections = connectionOrConnections

		self.__previouslyBlocked = None

	def __enter__( self ) :

		assert( self.__previouslyBlocked is None )

		self.__previouslyBlocked = [ c.getBlocked() for c in self.__connections ]
		for c in self.__connections :
			c.setBlocked( True )

	def __exit__( self, type, value, traceBack ) :

		for c, b in zip( self.__connections, self.__previouslyBlocked ) :
			c.setBlocked( b )

		self.__previouslyBlocked = None

Gaffer.Signals.BlockedConnection = BlockedConnection
