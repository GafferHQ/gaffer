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

import os
import time
import subprocess
import unittest

import IECore
import Gaffer
import GafferTest

class ApplicationTest( GafferTest.TestCase ) :

	def testTaskSchedulerInitDoesntSuppressExceptions( self ) :

		def f() :

			with IECore.tbb_task_scheduler_init( IECore.tbb_task_scheduler_init.automatic ) :
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


if __name__ == "__main__":
	unittest.main()
