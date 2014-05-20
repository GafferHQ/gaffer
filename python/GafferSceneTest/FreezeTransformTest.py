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

import unittest

import IECore

import Gaffer
import GafferScene
import GafferSceneTest

class FreezeTransformTest( GafferSceneTest.SceneTestCase ) :
	
	def test( self ) :
	
		p = GafferScene.Plane()
		p["transform"]["translate"].setValue( IECore.V3f( 1, 2, 3 ) )
	
		t = GafferScene.FreezeTransform()
		t["in"].setInput( p["out"] )
		
		self.assertSceneValid( t["out"] )
		
		self.assertEqual( t["out"].transform( "/plane" ), IECore.M44f() )
		self.assertEqual( t["out"].bound( "/plane" ), IECore.Box3f( IECore.V3f( 0.5, 1.5, 3 ), IECore.V3f( 1.5, 2.5, 3 ) ) )
		self.assertEqual( t["out"].object( "/plane" ).bound(), IECore.Box3f( IECore.V3f( 0.5, 1.5, 3 ), IECore.V3f( 1.5, 2.5, 3 ) ) )
	
	def testFilter( self ) :
	
		p1 = GafferScene.Plane()
		p1["transform"]["translate"].setValue( IECore.V3f( 1, 2, 3 ) )

		p2 = GafferScene.Plane()
		p2["transform"]["translate"].setValue( IECore.V3f( 1, 2, 3 ) )
		
		g = GafferScene.Group()
		g["transform"]["translate"].setValue( IECore.V3f( 1, 0, 0 ) )
		g["in"].setInput( p1["out"] )
		g["in1"].setInput( p2["out"] )
		
		f = GafferScene.PathFilter()
		f["paths"].setValue( IECore.StringVectorData( [ "/group/plane" ] ) )
	
		t = GafferScene.FreezeTransform()
		t["in"].setInput( g["out"] )
		t["filter"].setInput( f["match"] )
		
		self.assertSceneValid( t["out"] )
		
		self.assertEqual( t["out"].transform( "/group" ), IECore.M44f.createTranslated( IECore.V3f( 1, 0, 0 ) ) )
		self.assertEqual( t["out"].transform( "/group/plane" ), IECore.M44f() )
		self.assertEqual( t["out"].transform( "/group/plane1" ), IECore.M44f.createTranslated( IECore.V3f( 1, 2, 3 ) ) )
		
		self.assertEqual( t["out"].bound( "/group/plane" ), IECore.Box3f( IECore.V3f( 0.5, 1.5, 3 ), IECore.V3f( 1.5, 2.5, 3 ) ) )
		self.assertEqual( t["out"].bound( "/group/plane1" ), IECore.Box3f( IECore.V3f( -0.5, -0.5, 0 ), IECore.V3f( 0.5, 0.5, 0 ) ) )

		self.assertEqual( t["out"].object( "/group/plane" ).bound(), IECore.Box3f( IECore.V3f( 0.5, 1.5, 3 ), IECore.V3f( 1.5, 2.5, 3 ) ) )
		self.assertEqual( t["out"].object( "/group/plane1" ).bound(), IECore.Box3f( IECore.V3f( -0.5, -0.5, 0 ), IECore.V3f( 0.5, 0.5, 0 ) ) )
	
		f["paths"].setValue( IECore.StringVectorData( [ "/group", "/group/plane" ] ) )

		self.assertSceneValid( t["out"] )

		self.assertEqual( t["out"].transform( "/group" ), IECore.M44f() )
		self.assertEqual( t["out"].transform( "/group/plane" ), IECore.M44f() )
		self.assertEqual( t["out"].transform( "/group/plane1" ), IECore.M44f.createTranslated( IECore.V3f( 1, 2, 3 ) ) )
		
		self.assertEqual( t["out"].bound( "/group/plane" ), IECore.Box3f( IECore.V3f( 1.5, 1.5, 3 ), IECore.V3f( 2.5, 2.5, 3 ) ) )
		self.assertEqual( t["out"].bound( "/group/plane1" ), IECore.Box3f( IECore.V3f( 0.5, -0.5, 0 ), IECore.V3f( 1.5, 0.5, 0 ) ) )
	
if __name__ == "__main__":
	unittest.main()
