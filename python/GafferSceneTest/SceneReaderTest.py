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

import unittest

import IECore

import Gaffer
import GafferScene
import GafferSceneTest

class SceneReaderTest( GafferSceneTest.SceneTestCase ) :
		
	def testTagsAsAttributes( self ) :
	
		s = IECore.SceneCache( "/tmp/test.scc", IECore.IndexedIO.OpenMode.Write )
		
		sphereGroup = s.createChild( "sphereGroup" )
		sphereGroup.writeTags( [ "chrome" ] )
		sphere = sphereGroup.createChild( "sphere" )
		sphere.writeObject( IECore.SpherePrimitive(), 0 )
		
		planeGroup = s.createChild( "planeGroup" )
		plane = planeGroup.createChild( "plane" )
		plane.writeTags( [ "wood", "something" ] )
		plane.writeObject( IECore.MeshPrimitive.createPlane( IECore.Box2f( IECore.V2f( -1 ), IECore.V2f( 1 ) ) ), 0 )
		
		del s, sphereGroup, sphere, planeGroup, plane
		
		s = GafferScene.SceneReader()
		s["fileName"].setValue( "/tmp/test.scc" )
		
		self.assertEqual( len( s["out"].attributes( "/" ) ), 0 )
		
		a = s["out"].attributes( "/sphereGroup" )
		self.assertEqual( len( a ), 1 )
		self.assertEqual( a["user:tag:chrome"], IECore.BoolData( True ) )
		
		self.assertEqual( len( s["out"].attributes( "/sphereGroup/sphere" ) ), 0 )
		self.assertEqual( len( s["out"].attributes( "/planeGroup" ) ), 0 )
		
		a = s["out"].attributes( "/planeGroup/plane" )
		self.assertEqual( len( a ), 2 )
		self.assertEqual( a["user:tag:wood"], IECore.BoolData( True ) )
		self.assertEqual( a["user:tag:something"], IECore.BoolData( True ) )
		
if __name__ == "__main__":
	unittest.main()
