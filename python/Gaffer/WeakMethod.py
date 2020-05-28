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

import weakref

## Implements an object similar to weakref.proxy, except that
# it can work with bound methods.
class WeakMethod( object ) :

	def __init__( self, boundMethod, **kw ) :

		self.__method = boundMethod.__func__
		self.__self = weakref.ref( boundMethod.__self__ )
		self.__kw = kw

	## Calls the method if the instance it refers to is still alive,
	# and returns the result.
	#
	# If the instance is not alive, then returns "fallbackResult" if
	# it was passed to the constructor as a keyword argument, and throws
	# ReferenceError otherwise.
	def __call__( self, *args, **kwArgs ) :

		s = self.instance()
		if s is None :
			if "fallbackResult" in self.__kw :
				return self.__kw["fallbackResult"]
			else :
				raise ReferenceError( "Instance referenced by WeakMethod %s.%s() no longer exists" % ( self.__method.__module__, self.__method.__name__ ) )

		return self.__method( s, *args, **kwArgs )

	## Returns the function that implements the method.
	def method( self ) :

		return self.__method

	## Returns the instance the method is bound to, or None if
	# it has expired.
	def instance( self ) :

		return self.__self()
