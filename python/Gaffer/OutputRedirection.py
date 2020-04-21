##########################################################################
#
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

import sys
import threading

## A threadsafe means of temporarily diverting sys.stdout and/or sys.stderr
# to alternative functions.
class OutputRedirection( object ) :

	def __init__( self, stdOut = None, stdErr = None ) :

		self.__stdOut = stdOut
		self.__stdErr = stdErr

	def __enter__( self ) :

		with self.__sysLock :
			if not isinstance( sys.stdout, _StdOut ) :
				OutputRedirection._originalStdOut = sys.stdout
				OutputRedirection._originalStdErr = sys.stderr
				sys.stdout = _StdOut()
				sys.stderr = _StdErr()

		stdOutStack = self._streams.__dict__.setdefault( "out", [] )
		if self.__stdOut is not None :
			stdOutStack.append( self.__stdOut )

		stdErrStack = self._streams.__dict__.setdefault( "err", [] )
		if self.__stdErr is not None :
			stdErrStack.append( self.__stdErr )

	def __exit__( self, type, value, traceBack ) :

		if self.__stdOut :
			self._streams.out.pop()
		if self.__stdErr :
			self._streams.err.pop()

	__sysLock = threading.RLock()
	_streams = threading.local()

class _StdOut( object ) :

	def write( self, text ) :

		stdOutStack = OutputRedirection._streams.__dict__.get( "out" )
		if stdOutStack :
			stdOutStack[-1]( text )
		else :
			OutputRedirection._originalStdOut.write( text )

	def flush( self ) :

		pass

class _StdErr( object ) :

	def write( self, text ) :

		stdErrStack = OutputRedirection._streams.__dict__.get( "err" )
		if stdErrStack :
			stdErrStack[-1]( text )
		else :
			OutputRedirection._originalStdErr.write( text )

	def flush( self ) :

		pass