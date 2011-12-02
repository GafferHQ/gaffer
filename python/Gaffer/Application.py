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

import IECore

class Application( IECore.Parameterised ) :

	def __init__( self ) :
	
		IECore.Parameterised.__init__( self, "" )

	def run( self ) :
	
		args = self.parameters().getValidatedValue()
		return self.doRun( args )

	def _executeStartupFiles( self, subdirectories, contextDict = {} ) :
	
		sp = os.environ.get( "GAFFER_STARTUP_PATHS", "" )
		if not sp :
			IECore.msg( IECore.Msg.Level.Warning, "Gaffer.Application._executeStartupFiles", "GAFFER_STARTUP_PATHS environment variable not set" )
			return
	
		sp = IECore.SearchPath( sp, ":" )
		rootPaths = sp.paths
	
		for d in subdirectories :
		
			paths = [ os.path.join( p, d ) for p in rootPaths ]
			spd = IECore.SearchPath( ":".join( paths ), ":" )
			
			IECore.loadConfig( spd, contextDict )
			
