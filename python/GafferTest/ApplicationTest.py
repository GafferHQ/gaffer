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
import re
import sys
if os.name == 'posix' and sys.version_info[0] < 3:
	import subprocess32 as subprocess
else:
	import subprocess

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

		executable = "gaffer" if os.name != "nt" else "gaffer.cmd"
		output = subprocess.check_output( [ executable, "env", "env" if os.name != "nt" else "set" ], universal_newlines = True )

		externalEnv = {}
		for line in output.split( '\n' ) :
			partition = line.partition( "=" )
			externalEnv[partition[0]] = partition[2]

		self.assertEqual( externalEnv["GAFFER_STARTUP_PATHS"], os.environ["GAFFER_STARTUP_PATHS"] )
		self.assertEqual( externalEnv["GAFFER_APP_PATHS"], os.environ["GAFFER_APP_PATHS"] )

	def testProcessName( self ) :

		if os.name == "nt" :
			process = subprocess.Popen( [ "gaffer.cmd", "env", "timeout", "100" ] )

			time.sleep( 1 )

			command = subprocess.check_output(
				[
					"powershell",
					"-command",
					"Get-WmiObject -Query \"SELECT CommandLine FROM Win32_Process WHERE ProcessID={}\" | Format-List -Property CommandLine".format( process.pid )
				],
				universal_newlines = True
			)
			command = " ".join( [ i.strip() for i in command.strip().split( "\n" ) ] )
			command = command.replace( "CommandLine : ", "" )

			name = subprocess.check_output(
				[
					"powershell",
					"-command",
					"Get-WmiObject -Query \"SELECT Name FROM Win32_Process WHERE ProcessID={}\" | Format-List -Property Name".format( process.pid )
				],
				universal_newlines = True
			)
			name = name.strip().replace( "Name : ", "" )

			subprocess.Popen( "TASKKILL /F /PID {} /T".format( process.pid ), stdout = sys.stderr )

			self.assertEqual( command, "C:\\Windows\\system32\\cmd.exe /c gaffer.cmd env timeout 100" )
			self.assertEqual( name, "cmd.exe" )

		else :
			process = subprocess.Popen( [ "gaffer", "env", "sleep", "100" ] )
			time.sleep( 1 )

			command = subprocess.check_output( [ "ps", "-p", str( process.pid ), "-o", "command=" ], universal_newlines = True ).strip()
			name = subprocess.check_output( [ "ps", "-p", str( process.pid ), "-o", "comm=" ], universal_newlines = True ).strip()

			process.kill()

			self.assertEqual( command, "gaffer env sleep 100" )
			self.assertEqual( name, "gaffer" )

if __name__ == "__main__":
	unittest.main()
