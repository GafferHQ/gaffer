##########################################################################
#
#  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

import re
import unittest
import os
import subprocess

import Gaffer
import GafferTest

class StatsApplicationTest( GafferTest.TestCase ) :

	def test( self ) :

		script = Gaffer.ScriptNode()

		script["frameRange"]["start"].setValue( 10 )
		script["frameRange"]["end"].setValue( 50 )
		script["variables"].addChild( Gaffer.NameValuePlug( "test", 20.5, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )

		script["n"] = GafferTest.AddNode()
		script["b"] = Gaffer.Box()
		script["b"]["n"] = GafferTest.AddNode()

		script["fileName"].setValue( self.temporaryDirectory() + "/script.gfr" )
		script.save()

		executable = "gaffer" if os.name != "nt" else "gaffer.cmd"
		o = subprocess.check_output( [ executable, "stats", script["fileName"].getValue() ], universal_newlines = True )

		self.assertTrue( Gaffer.About.versionString() in o )
		self.assertTrue( re.search( r"frameRange\.start\s*10", o ) )
		self.assertTrue( re.search( r"frameRange\.end\s*50", o ) )
		self.assertTrue( re.search( r"framesPerSecond\s*24.0", o ) )
		self.assertTrue( re.search( r"test\s*20.5", o ) )
		self.assertTrue( re.search( r"AddNode\s*2", o ) )
		self.assertTrue( re.search( r"Box\s*1", o ) )
		self.assertTrue( re.search( r"Total\s*3", o ) )

if __name__ == "__main__":
	unittest.main()
