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

import json
import unittest
import subprocess32 as subprocess

import Gaffer
import GafferTest


class StatsApplicationTest( GafferTest.TestCase ) :

	def test( self ) :

		script = Gaffer.ScriptNode()

		script["frameRange"]["start"].setValue( 10 )
		script["frameRange"]["end"].setValue( 50 )
		script["variables"].addMember( "test", 20.5 )

		script["n"] = GafferTest.AddNode()
		script["b"] = Gaffer.Box()
		script["b"]["n"] = GafferTest.AddNode()

		script["fileName"].setValue( self.temporaryDirectory() + "/script.gfr" )
		script.save()

		o = subprocess.check_output( [ "gaffer", "stats", script["fileName"].getValue(), "-json", "1" ] )

		statsData = json.loads( o )

		self.assertEqual( statsData["Version"]["Current"], Gaffer.About.versionString() )
		self.assertEqual( statsData["Settings"]["frameRange.start"], 10 )
		self.assertEqual( statsData["Settings"]["frameRange.end"], 50 )
		self.assertEqual( statsData["Settings"]["framesPerSecond"], 24.0 )
		self.assertEqual( statsData["Variables"]["test"], "20.5" )
		self.assertEqual( statsData["Nodes"]["AddNode"], 2 )
		self.assertEqual( statsData["Nodes"]["Box"], 1 )
		self.assertEqual( statsData["Nodes"]["Total"], 3 )

if __name__ == "__main__":
	unittest.main()
