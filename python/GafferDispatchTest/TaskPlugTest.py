##########################################################################
#
#  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

import Gaffer
import GafferTest
import GafferDispatch

class TaskPlugTest( GafferTest.TestCase ) :

	def testAcceptsInput( self ) :

		taskPlug1 = GafferDispatch.TaskNode.TaskPlug()
		taskPlug2 = GafferDispatch.TaskNode.TaskPlug()

		# We want to accept inputs from TaskPlugs.
		self.assertTrue( taskPlug1.acceptsInput( taskPlug2 ) )

		# But not from regular plugs.
		plug = Gaffer.Plug()
		self.assertFalse( taskPlug1.acceptsInput( plug ) )

		# Even if they are on a box.
		box = Gaffer.Box()
		box["p"] = Gaffer.Plug()
		self.assertFalse( taskPlug1.acceptsInput( box["p"] ) )

		# Or a dot.
		dot = Gaffer.Dot()
		dot.setup( Gaffer.Plug() )
		self.assertFalse( taskPlug1.acceptsInput( dot["out"] ) )

if __name__ == "__main__":
	unittest.main()
