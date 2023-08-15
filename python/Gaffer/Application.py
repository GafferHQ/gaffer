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
import sys
import inspect
import cProfile

import IECore

import Gaffer

class Application( IECore.Parameterised ) :

	def __init__( self, description="" ) :

		IECore.Parameterised.__init__( self, inspect.cleandoc( description ) )

		self.parameters().addParameters(

			[

				IECore.BoolParameter(
					name = "help",
					description = "Prints names and descriptions of each parameter "
						"rather than running the application.",
					defaultValue = False,
				),

				IECore.IntParameter(
					name = "threads",
					description = "The maximum number of threads used for computation. "
						"The default value of zero matches the number of threads to "
						"the available hardware cores. Negative values specify a thread count "
						"relative to the available cores, leaving some in reserve for other "
						"applications. Positive values specify the thread count explicitly, "
						"but are clamped so it does not exceed the available cores.",
					defaultValue = 0,
				),

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

		self.__root = _NonSlicingApplicationRoot( self.__class__.__name__ )

	## All Applications have an ApplicationRoot which forms the root of the
	# hierarchy for all scripts, preferences, nodes etc.
	def root( self ) :

		return self.__root

	## Called to run the application and return a status value.
	def run( self ) :

		if self.parameters()["help"].getTypedValue() :
			self.__formatHelp()
			return 0

		profileFileName = self.parameters()["profileFileName"].getTypedValue()

		if profileFileName :
			contextDict = {
				"self" : self,
			}
			cProfile.runctx( "result = self._Application__run()", contextDict, contextDict, profileFileName )
			return contextDict["result"]
		else :
			return self.__run()

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

		if "GAFFER_STARTUP_PATHS" not in os.environ :
			IECore.msg( IECore.Msg.Level.Warning, "Gaffer.Application._executeStartupFiles", "GAFFER_STARTUP_PATHS environment variable not set" )
			return

		contextDict = {	"application" : self }
		IECore.loadConfig( "GAFFER_STARTUP_PATHS", contextDict, subdirectory = applicationName )

	def __run( self ) :

		maxThreads = IECore.hardwareConcurrency()
		threads = self.parameters()["threads"].getTypedValue()
		if threads <= 0 :
			threads = max( maxThreads + threads, 1 )
		elif threads > maxThreads :
			IECore.msg( IECore.Msg.Level.Warning, "Application", f"Clamping to `-threads {maxThreads}` to avoid oversubscription" )
			threads = maxThreads

		with IECore.tbb_global_control(
			IECore.tbb_global_control.parameter.max_allowed_parallelism,
			threads
		) :

			self._executeStartupFiles( self.root().getName() )

			# Append DEBUG message with process information to all messages
			defaultMessageHandler = IECore.MessageHandler.getDefaultHandler()
			if not isinstance( defaultMessageHandler, Gaffer.ProcessMessageHandler ) :
				IECore.MessageHandler.setDefaultHandler(
					Gaffer.ProcessMessageHandler( defaultMessageHandler )
				)

			return self._run( self.parameters().getValidatedValue() )

	def __formatHelp( self ) :

		formatter = IECore.WrappedTextFormatter( sys.stdout )
		formatter.paragraph( "Name : " + self.typeName() )
		if self.description :
			formatter.paragraph( self.description + "\n" )
		if len( self.parameters().values() ):
			formatter.heading( "Parameters" )
			formatter.indent()
			for p in self.parameters().values() :
				IECore.formatParameterHelp( p, formatter )
			formatter.unindent()

IECore.registerRunTimeTyped( Application, typeName = "Gaffer::Application" )

# Various parts of the UI try to store their state as attributes on
# the root object, and therefore require it's identity in python to
# be stable, even when acquiring it from separate calls to C++ methods
# like `ancestor( ApplicationRoot )`. The IECorePython::RunTimeTypedWrapper
# only guarantees this stability if we've derived from it in Python,
# which is what we do here.
## \todo Either :
#
# - Fix the object identity problem in Cortex
# - Or at least add a way of requesting that identity be
#   preserved without needing to derive.
# - Or stop the UI relying on storing it's own members on
#   the root.
class _NonSlicingApplicationRoot( Gaffer.ApplicationRoot ) :

	def __init__( self, name ) :

		Gaffer.ApplicationRoot.__init__( self, name )
