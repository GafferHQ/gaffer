##########################################################################
#
#  Copyright (c) 2026, Cinesite VFX Ltd. All rights reserved.
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

import shutil
import subprocess
import unittest

import Gaffer
import GafferTest

class GafferPythonTest( GafferTest.TestCase ) :

	def test( self ) :

		gafferPythonPath = Gaffer.rootPath() / "bin" / "__private" / "gafferPython"
		pythonPath = Gaffer.rootPath() / "bin" / "python"

		gafferPythonResult = subprocess.run( [ shutil.which( "ldd" ), gafferPythonPath ], text = True, stdout = subprocess.PIPE, check = True )
		gafferPythonLibs = [ x.strip().split()[0] for x in gafferPythonResult.stdout.split( "\n" ) if x != "" ]

		pythonResult = subprocess.run( [ shutil.which( "ldd" ), pythonPath ], text = True, stdout = subprocess.PIPE, check = True )
		pythonLibs = [ x.strip().split()[0] for x in pythonResult.stdout.split( "\n" ) if x != "" ]

		print( gafferPythonLibs, pythonLibs )

		self.assertTrue( len( gafferPythonLibs ) > 0 )
		self.assertEqual( sorted( gafferPythonLibs ), sorted( pythonLibs ) )

		# \ todo Currently the test above passes when it shouldn't. Running `gafferPython` as a subprocess
		# of the test process causes it to list the same libraries as `python`. If running `ldd` directly
		# from the terminal it returns fewer libraries for `gafferPython`.
		self.assertTrue( False )


if __name__ == "__main__" :
	unittest.main()