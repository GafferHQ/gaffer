##########################################################################
#
#  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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

import unittest

import IECore

import Gaffer
import GafferTest
import GafferDispatch
import GafferDispatchTest

class FrameMaskTest( GafferTest.TestCase ) :

	def test( self ) :

		s = Gaffer.ScriptNode()

		s["task"] = GafferDispatchTest.LoggingTaskNode()
		s["task"]["frameDependency"] = Gaffer.StringPlug( defaultValue = "#" )

		s["mask"] = GafferDispatch.FrameMask()
		s["mask"]["preTasks"][0].setInput( s["task"]["task"] )
		s["mask"]["mask"].setValue( "1,3,10-15,20-30x2" )

		d = GafferDispatch.LocalDispatcher()
		d["jobsDirectory"].setValue( self.temporaryDirectory() / "jobs" )
		d["framesMode"].setValue( d.FramesMode.CustomRange )
		d["frameRange"].setValue( "1-50" )

		d.dispatch( [ s["mask"] ] )

		self.assertEqual(
			[ l.context.getFrame() for l in s["task"].log ],
			IECore.FrameList.parse( s["mask"]["mask"].getValue() ).asList()
		)

		# Check that empty mask is a pass-through

		del s["task"].log[:]
		s["mask"]["mask"].setValue( "" )

		d.dispatch( [ s["mask"] ] )

		self.assertEqual(
			[ l.context.getFrame() for l in s["task"].log ],
			IECore.FrameList.parse( d["frameRange"].getValue() ).asList()
		)

if __name__ == "__main__":
	unittest.main()
