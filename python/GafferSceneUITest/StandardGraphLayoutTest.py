##########################################################################
#
#  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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
import GafferUI
import GafferUITest
import GafferScene

class StandardGraphLayoutTest( GafferUITest.TestCase ) :

	def testConnectNodeInStream( self ) :

		s = Gaffer.ScriptNode()

		s["a1"] = GafferScene.ShaderAssignment()
		s["a2"] = GafferScene.ShaderAssignment()
		s["a3"] = GafferScene.ShaderAssignment()

		s["a2"]["in"].setInput( s["a1"]["out"] )

		g = GafferUI.GraphGadget( s )
		g.getLayout().connectNode( g, s["a3"], Gaffer.StandardSet( [ s["a1"] ] ) )

		self.assertTrue( s["a3"]["in"].getInput().isSame( s["a1"]["out"] ) )
		self.assertTrue( s["a2"]["in"].getInput().isSame( s["a3"]["out"] ) )

	def testConnectNodeInStreamWithMultipleOutputs( self ) :

		s = Gaffer.ScriptNode()

		s["a1"] = GafferScene.ShaderAssignment()
		s["a2"] = GafferScene.ShaderAssignment()
		s["a3"] = GafferScene.ShaderAssignment()
		s["a4"] = GafferScene.ShaderAssignment()

		s["a2"]["in"].setInput( s["a1"]["out"] )
		s["a3"]["in"].setInput( s["a1"]["out"] )

		g = GafferUI.GraphGadget( s )
		g.getLayout().connectNode( g, s["a4"], Gaffer.StandardSet( [ s["a1"] ] ) )

		self.assertTrue( s["a2"]["in"].getInput().isSame( s["a4"]["out"] ) )
		self.assertTrue( s["a3"]["in"].getInput().isSame( s["a4"]["out"] ) )

if __name__ == "__main__":
	unittest.main()

