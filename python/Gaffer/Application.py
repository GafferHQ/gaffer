##########################################################################
#  
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2012-2013, Image Engine Design Inc. All rights reserved.
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
import cProfile

import IECore

import Gaffer

class Application( IECore.Parameterised ) :

	def __init__( self, description="" ) :
	
		IECore.Parameterised.__init__( self, description )

		self.parameters().addParameters(
			
			[
				IECore.FileNameParameter(
					name = "profileFileName",
					description = "If this is specified, then the application "
						"is run using the cProfile profiling module, and the "
						"results saved to the file for later examination.",
					defaultValue = "",
					allowEmptyString = True
				),
			]
		
		)
		
		self.__root = Gaffer.ApplicationRoot( self.__class__.__name__ )

	## All Applications have an ApplicationRoot which forms the root of the
	# hierarchy for all scripts, preferences, nodes etc.
	def root( self ) :
	
		return self.__root

	## Called to run the application and return a status value.
	def run( self ) :
	
		args = self.parameters().getValidatedValue()
		
		if args["profileFileName"].value :
			contextDict = {
				"self" : self,
				"args" : args,
			}
			cProfile.runctx( "result = self._Application__run( args )", contextDict, contextDict, args["profileFileName"].value )
			return contextDict["result"]
		else :
			return self.__run( args )

	## Must be implemented by subclasses to do the actual work of
	# running the application and returning a status value. The args
	# argument contains the already validated parameter values.
	def _run( self, args ) :
	
		raise NotImplementedError

	## Executes the startup files for the specified application. This
	# is called automatically for this application before _run is called,
	# but applications may call it in order to "borrow" the startup files
	# for other applications. See the screengrab app for a good use case.
	def _executeStartupFiles( self, applicationName ) :
	
		sp = os.environ.get( "GAFFER_STARTUP_PATHS", "" )
		if not sp :
			IECore.msg( IECore.Msg.Level.Warning, "Gaffer.Application.__executeStartupFiles", "GAFFER_STARTUP_PATHS environment variable not set" )
			return
	
		sp = IECore.SearchPath( sp, ":" )
		paths = [ os.path.join( p, applicationName ) for p in sp.paths ]
		sp = IECore.SearchPath( ":".join( paths ), ":" )
		
		contextDict = {	"application" : self }	
		IECore.loadConfig( sp, contextDict )
		
	def __run( self, args ) :
	
		self._executeStartupFiles( self.root().getName() )
		return self._run( args )

IECore.registerRunTimeTyped( Application, typeName = "Gaffer::Application" )		
