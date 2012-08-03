##########################################################################
#  
#  Copyright (c) 2012, John Haddon. All rights reserved.
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
import unittest

import IECore

import Gaffer
import GafferScene
import GafferSceneTest

class AlembicSourceTest( GafferSceneTest.SceneTestCase ) :

	def testCube( self ) :
			
		a = GafferScene.AlembicSource()
		a["fileName"].setValue( os.path.dirname( __file__ ) + "/alembicFiles/cube.abc" )

		self.assertSceneValid( a["out"] )
	
		self.assertEqual( a["out"].object( "/" ), None )
		self.assertEqual( a["out"].transform( "/" ), IECore.M44f() )
		self.assertEqual( a["out"].bound( "/" ), IECore.Box3f( IECore.V3f( -2 ), IECore.V3f( 2 ) ) )
		self.assertEqual( a["out"].attributes( "/" ), None )
		self.assertEqual( a["out"].childNames( "/" ), IECore.StringVectorData( [ "group1"] ) )
		
		self.assertEqual( a["out"].object( "/group1" ), None )
		self.assertEqual( a["out"].transform( "/group1" ), IECore.M44f.createScaled( IECore.V3f( 2 ) ) * IECore.M44f.createTranslated( IECore.V3f( 2, 0, 0 ) ) )
		self.assertEqual( a["out"].bound( "/group1" ), IECore.Box3f( IECore.V3f( -2, -1, -1 ), IECore.V3f( 0, 1, 1 ) ) )
		self.assertEqual( a["out"].attributes( "/group1" ), None )
		self.assertEqual( a["out"].childNames( "/group1" ), IECore.StringVectorData( [ "pCube1"] ) )

		self.assertEqual( a["out"].object( "/group1/pCube1" ), None )
		self.assertEqual( a["out"].transform( "/group1/pCube1" ), IECore.M44f.createTranslated( IECore.V3f( -1, 0, 0 ) ) )
		self.assertEqual( a["out"].bound( "/group1/pCube1" ), IECore.Box3f( IECore.V3f( -1 ), IECore.V3f( 1 ) ) )
		self.assertEqual( a["out"].attributes( "/group1/pCube1" ), None )
		self.assertEqual( a["out"].childNames( "/group1/pCube1" ), IECore.StringVectorData( [ "pCubeShape1"] ) )
		
		self.assertTrue( isinstance( a["out"].object( "/group1/pCube1/pCubeShape1" ), IECore.MeshPrimitive ) )
		self.assertEqual( a["out"].transform( "/group1/pCube1/pCubeShape1" ), IECore.M44f() )
		self.assertEqual( a["out"].bound( "/group1/pCube1/pCubeShape1" ), IECore.Box3f( IECore.V3f( -1 ), IECore.V3f( 1 ) ) )
		self.assertEqual( a["out"].attributes( "/group1/pCube1/pCubeShape1" ), None )
		self.assertEqual( a["out"].childNames( "/group1/pCube1/pCubeShape1" ), IECore.StringVectorData( [] ) )

if __name__ == "__main__":
	unittest.main()
