##########################################################################
#
#  Copyright (c) 2019, John Haddon. All rights reserved.
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
import subprocess

import Gaffer
import GafferTest

class ModuleTest( GafferTest.TestCase ) :

	def testDoesNotImportUI( self ) :

		self.assertModuleDoesNotImportUI( "GafferRenderMan" )
		self.assertModuleDoesNotImportUI( "GafferRenderManTest" )

	def testCanLoadGUIConfigsWithoutRenderMan( self ) :

		# Start a subprocess without RMANTREE set, and without the side-effects
		# of it having been set when our wrapper ran earlier. And in that subprocess,
		# check that we can still load the GUI configs cleanly.

		env = os.environ.copy()
		for var in ( "RMANTREE", "PYTHONPATH", "LD_LIBRARY_PATH", "DYLD_LIBRARY_PATH", "GAFFER_STARTUP_PATHS" ) :
			env.pop( var, None )

		try :
			subprocess.check_output(
				[ str( Gaffer.executablePath() ), "test", "GafferUITest.TestCase.assertCanLoadGUIConfigs" ],
				env = env, stderr = subprocess.STDOUT
			)
		except subprocess.CalledProcessError as e :
			self.fail( e.output )

if __name__ == "__main__":
	unittest.main()
