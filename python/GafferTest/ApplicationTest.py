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

import ast
import os
import sys
import time
import subprocess
import unittest

import IECore
import Gaffer
import GafferTest

class ApplicationTest( GafferTest.TestCase ) :

	def testTBBGlobalControlDoesntSuppressExceptions( self ) :

		def f() :

			with IECore.tbb_global_control( IECore.tbb_global_control.parameter.max_allowed_parallelism, IECore.hardwareConcurrency() ) :
				raise Exception( "Woops!")

		self.assertRaises( Exception, f )

	def testWrapperDoesntDuplicatePaths( self ) :

		for v in ["GAFFER_STARTUP_PATHS", "GAFFER_APP_PATHS"] :
			value = subprocess.check_output( [ str( Gaffer.executablePath() ), "env", "python", "-c", "import os; print(os.environ['{}'])".format( v ) ], universal_newlines = True )
			self.assertEqual( value.strip(), os.environ[v] )

	@unittest.skipIf( os.name == "nt", "Process name is not controllable on Windows.")
	def testProcessName( self ) :

		process = subprocess.Popen( [ str( Gaffer.executablePath() ), "env", "sleep", "100" ] )
		try :
			startTime = time.time()
			while True :
				time.sleep( 0.1 )
				command = subprocess.check_output( [ "ps", "-p", str( process.pid ), "-o", "command=" ], universal_newlines = True ).strip()
				name = subprocess.check_output( [ "ps", "-p", str( process.pid ), "-o", "comm=" ], universal_newlines = True ).strip()
				try :
					self.assertEqual( command, "gaffer env sleep 100" )
					self.assertEqual( name, "gaffer" )

				except self.failureException :
					# It can take some time for gaffer to change its own process name, which varies
					# based on the host's performance.
					# For that reason, we check until 3 seconds have passed before giving up.
					if time.time() - startTime > 3.0 :
						raise

				else :
					break

		finally :
			process.kill()

	def testEnvironmentVariableCase( self ) :

		# On Windows, the `os` module will screw this up, and create an all-upper-case
		# environment variable instead. Still, we want to test that variables created
		# this way are passed to child applications.
		os.environ["gafferApplicationTestMIXEDcaseA"] = "testTEST"
		self.addCleanup( os.environ.__delitem__, "gafferApplicationTestMIXEDcaseA" )

		# If we bypass `os.environ`, then we can create a mixed-case variable even
		# on Windows.
		os.putenv( "gafferApplicationTestMIXEDcaseB", "testTEST" )
		self.addCleanup( os.unsetenv, "gafferApplicationTestMIXEDcaseB" )

		childEnvironment = subprocess.check_output( [ Gaffer.executablePath(), "env" ], text = True )
		childEnvironment = {
			line.partition( "=" )[0] : line.partition( "=" )[2]
			for line in childEnvironment.split( "\n" )
		}

		# We preseve mixed-case environment variables on all platforms.
		self.assertEqual( childEnvironment["gafferApplicationTestMIXEDcaseB"], "testTEST" )

		if sys.platform == "win32" :
			# Assert that Python botched this one as expected.
			self.assertEqual( childEnvironment["GAFFERAPPLICATIONTESTMIXEDCASEA"], "testTEST" )
			# Check standard variable that happens to be mixed case.
			self.assertIn( "ProgramData", childEnvironment )
		else :
			# On Linux, everything actually makes sense.
			self.assertEqual( childEnvironment["gafferApplicationTestMIXEDcaseA"], "testTEST" )

	def testEnvironmentCleanup( self ) :

		# The `LD_PRELOAD` additions made in `_gaffer.py` should be
		# removed from the environment so that they are not inherited
		# by subprocesses launched by Gaffer.

		environments = {
			"pythonNative" : os.environ,
			"pythonCasePreserving" : Gaffer.environment(),
			"subprocess" : ast.literal_eval(
				subprocess.check_output( [ "python", "-c", "import os; print( dict( os.environ ) )" ], universal_newlines = True )
			)
		}

		for source, environment in environments.items() :
			with self.subTest( source = source ) :
				self.assertNotIn( "libstdc++", environment.get( "LD_PRELOAD", "" ) )
				self.assertNotIn( "libjemalloc", environment.get( "LD_PRELOAD", "" ) )
				self.assertEqual(
					[ k for k in environment.keys() if k.startswith( "__GAFFER_RESTORE_" ) ],
					[]
				)

		# But any `LD_PRELOAD` from the environment Gaffer is called
		# in should be passed through as normal.

		env = Gaffer.environment()
		env["LD_PRELOAD"] = "libc.so.6"

		self.assertEqual(

			subprocess.check_output(
				[ str( Gaffer.executablePath() ), "env", "python", "-c", "import os; print( os.environ['LD_PRELOAD'], end = '' )" ],
				universal_newlines = True, env = env
			),

			env["LD_PRELOAD"],

		)

		# Even if it's just an empty string.

		env["LD_PRELOAD"] = ""
		self.assertEqual(

			subprocess.check_output(
				[ str( Gaffer.executablePath() ), "env", "python", "-c", "import os; print( os.environ['LD_PRELOAD'], end = '' )" ],
				universal_newlines = True, env = env
			),

			env["LD_PRELOAD"],

		)

		# If `LD_PRELOAD` wasn't set in the launch environment, then it
		# shouldn't be set for subprocesses either.

		del env["LD_PRELOAD"]
		subprocess.check_call(
			[ str( Gaffer.executablePath() ), "env", "python", "-c", "import os; assert( 'LD_PRELOAD' not in os.environ )" ],
			universal_newlines = True, env = env
		)

if __name__ == "__main__":
	unittest.main()
