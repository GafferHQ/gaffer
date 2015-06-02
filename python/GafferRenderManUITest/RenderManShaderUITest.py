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

import IECore

import Gaffer
import GafferUI
import GafferRenderMan
import GafferRenderManTest
import GafferRenderManUI

class RenderManShaderUITest( GafferRenderManTest.RenderManTestCase ) :

	def testPromotedArrayElementNodules( self ) :

		shader = self.compileShader( os.path.expandvars( "$GAFFER_ROOT/python/GafferRenderManTest/shaders/coshaderArrayParameters.sl" ) )

		script = Gaffer.ScriptNode()
		graphGadget = GafferUI.GraphGadget( script )

		script["b"] = Gaffer.Box()

		script["b"]["s"] = GafferRenderMan.RenderManShader()
		script["b"]["s"].loadShader( shader )

		promotedCoshader = script["b"].promotePlug( script["b"]["s"]["parameters"]["fixedShaderArray"][0] )

		nodeGadget = graphGadget.nodeGadget( script["b"] )
		self.assertEqual( nodeGadget.noduleTangent( nodeGadget.nodule( promotedCoshader ) ), IECore.V3f( -1, 0, 0 ) )

if __name__ == "__main__":
	unittest.main()
