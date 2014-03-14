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
import GafferTest
import GafferUI
import GafferUITest

class BoxUITest( GafferUITest.TestCase ) :

	def testNodulePositions( self ) :
	
		class NodulePositionNode( GafferTest.AddNode ) :
		
			def __init__( self, name = "NodulePositionNode" ) :
			
				GafferTest.AddNode.__init__( self, name )
	
		IECore.registerRunTimeTyped( NodulePositionNode )
		
		Gaffer.Metadata.registerPlugValue( NodulePositionNode, "op1", "nodeGadget:nodulePosition", "left" )
		Gaffer.Metadata.registerPlugValue( NodulePositionNode, "sum", "nodeGadget:nodulePosition", "right" )

		s = Gaffer.ScriptNode()
		g = GafferUI.GraphGadget( s )
		
		s["a"] = GafferTest.AddNode()
		s["n"] = NodulePositionNode()
		s["r"] = GafferTest.AddNode()
		
		s["n"]["op1"].setInput( s["a"]["sum"] )
		s["r"]["op1"].setInput( s["n"]["sum"] )
		
		box = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["n"] ] ) )
				
		boxGadget = g.nodeGadget( box )
		
		self.assertEqual( boxGadget.noduleTangent( boxGadget.nodule( box["in"] ) ), IECore.V3f( -1, 0, 0 ) ) 
		self.assertEqual( boxGadget.noduleTangent( boxGadget.nodule( box["out"] ) ), IECore.V3f( 1, 0, 0 ) )
	
	def testRenamingPlugs( self ) :
	
		box = Gaffer.Box()
		box["user"]["a"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		
		ui = GafferUI.NodeUI.create( box )
		
		w = ui.plugValueWidget( box["user"]["a"], lazy=False )
		self.assertTrue( w is not None )
		
		box["user"]["a"].setName( "b" )
		
		w2 = ui.plugValueWidget( box["user"]["b"], lazy=False )
		self.assertTrue( w2 is not None )
		self.assertTrue( w2 is w )
		
if __name__ == "__main__":
	unittest.main()
