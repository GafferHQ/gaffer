##########################################################################
#  
#  Copyright (c) 2011, John Haddon. All rights reserved.
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
import sys
import ctypes
import tempfile
import uuid

__all__ = [ "start", "stop" ]

__currentProfile = None

def start( fileName=None ) :

	global __currentProfile

	if __currentProfile is not None :
		raise RuntimeError( "Profiling already in progress" )

	if fileName is None :
		fileName = os.path.join( tempfile.gettempdir(), "gafferProfile" + str( uuid.uuid4() ) + ".prof" )

	lib = ctypes.CDLL( "libprofiler.so" )
	lib.ProfilerStart( fileName )
	
	__currentProfile = fileName
	
def stop( view=False ) :

	global __currentProfile

	if __currentProfile is None :
		raise RuntimeError( "Profiling not in progress" )
		
	lib = ctypes.CDLL( "libprofiler.so" )
	lib.ProfilerStop()
		
	if view :
		pdf = os.path.splitext( __currentProfile )[0] + ".pdf"
		os.system( "pprof --pdf '%s' '%s' > '%s'" % ( sys.executable, __currentProfile, pdf )  )
		os.system( "see '%s'" % pdf )
				
	__currentProfile = None
