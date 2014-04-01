##########################################################################
#  
#  Copyright (c) 2014, John Haddon. All rights reserved.
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
import GafferScene
import GafferSceneTest

class PrimitiveVariablesTest( GafferSceneTest.SceneTestCase ) :
		
	def test( self ) :
	
		s = GafferScene.Sphere()
		p = GafferScene.PrimitiveVariables()
		p["in"].setInput( s["out"] )
		
		self.assertScenesEqual( s["out"], p["out"] )
		self.assertSceneHashesEqual( s["out"], p["out"] )
		
		p["primitiveVariables"].addMember( "a", IECore.IntData( 10 ) )
		
		self.assertScenesEqual( s["out"], p["out"], childPlugNamesToIgnore=( "object", ) )
		self.assertSceneHashesEqual( s["out"], p["out"], childPlugNamesToIgnore=( "object", ) )
		
		self.assertNotEqual( s["out"].objectHash( "/sphere" ), p["out"].objectHash( "/sphere" ) )
		self.assertNotEqual( s["out"].object( "/sphere" ), p["out"].object( "/sphere" ) )
		
		o1 = s["out"].object( "/sphere" )
		o2 = p["out"].object( "/sphere" )
		
		self.assertEqual( set( o1.keys() + [ "a" ] ), set( o2.keys() ) )
		self.assertEqual( o2["a"], IECore.PrimitiveVariable( IECore.PrimitiveVariable.Interpolation.Constant, IECore.IntData( 10 ) ) )
		
		del o2["a"]
		self.assertEqual( o1, o2 )
		
if __name__ == "__main__":
	unittest.main()
