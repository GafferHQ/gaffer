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
if os.name == 'posix' and sys.version_info[0] < 3:
	import subprocess32 as subprocess
else:
	import subprocess
import unittest

import GafferTest

class PythonApplicationTest( GafferTest.TestCase ) :

	executable = "gaffer" if os.name != "nt" else "gaffer.cmd"

	def testVariableScope( self ) :

		subprocess.check_call( [ self.executable, "python", os.path.join( os.path.dirname( __file__ ), "pythonScripts", "variableScope.py" ) ] )

	def testErrorReturnStatus( self ) :

		p = subprocess.Popen(
			[ self.executable, "python", os.path.join( os.path.dirname( __file__ ), "pythonScripts", "exception.py" ) ],
			stderr = subprocess.PIPE,
			universal_newlines = True,
		)
		p.wait()

		self.assertIn( "RuntimeError", "".join( p.stderr.readlines() ) )
		self.assertTrue( p.returncode )

	def testFlagArguments( self ) :

		subprocess.check_call( [ self.executable, "python", os.path.join( os.path.dirname( __file__ ), "pythonScripts", "flagArguments.py" ), "-arguments", "-flag1", "-flag2" ] )

	def testName( self ) :

		subprocess.check_call( [ self.executable, "python", os.path.join( os.path.dirname( __file__ ), "pythonScripts", "name.py" ) ] )

if __name__ == "__main__":
	unittest.main()
