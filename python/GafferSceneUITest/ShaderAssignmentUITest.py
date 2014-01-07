##########################################################################
#  
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

import IECore

import Gaffer
import GafferUI
import GafferUITest
import GafferScene
import GafferSceneTest
import GafferSceneUI

class ShaderAssignmentUITest( GafferUITest.TestCase ) :

	def testBoxNodulePositions( self ) :
	
		s = Gaffer.ScriptNode()
		g = GafferUI.GraphGadget( s )
		
		s["p"] = GafferScene.Plane()
		s["s"] = GafferSceneTest.TestShader()
		s["a"] = GafferScene.ShaderAssignment()
	
		s["a"]["in"].setInput( s["p"]["out"] )
		s["a"]["shader"].setInput( s["s"]["out"] )
	
		box = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["a"] ] ) )
			
		boxGadget = g.nodeGadget( box )
		
		self.assertEqual( boxGadget.noduleTangent( boxGadget.nodule( box["in"] ) ), IECore.V3f( 0, 1, 0 ) ) 
		self.assertEqual( boxGadget.noduleTangent( boxGadget.nodule( box["in1"] ) ), IECore.V3f( -1, 0, 0 ) ) 
		
if __name__ == "__main__":
	unittest.main()
	
