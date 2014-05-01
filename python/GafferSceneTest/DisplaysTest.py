##########################################################################
#  
#  Copyright (c) 2012, John Haddon. All rights reserved.
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

class DisplaysTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :
	
		p = GafferScene.Plane()
		displays = GafferScene.Displays()
		displays["in"].setInput( p["out"] )
	
		# check that the scene hierarchy is passed through
	
		self.assertEqual( displays["out"].object( "/" ), IECore.NullObject() )
		self.assertEqual( displays["out"].transform( "/" ), IECore.M44f() )
		self.assertEqual( displays["out"].bound( "/" ), IECore.Box3f( IECore.V3f( -0.5, -0.5, 0 ), IECore.V3f( 0.5, 0.5, 0 ) ) )
		self.assertEqual( displays["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "plane" ] ) )
		
		self.assertEqual( displays["out"].object( "/plane" ), IECore.MeshPrimitive.createPlane( IECore.Box2f( IECore.V2f( -0.5 ), IECore.V2f( 0.5 ) ) ) )
		self.assertEqual( displays["out"].transform( "/plane" ), IECore.M44f() )
		self.assertEqual( displays["out"].bound( "/plane" ), IECore.Box3f( IECore.V3f( -0.5, -0.5, 0 ), IECore.V3f( 0.5, 0.5, 0 ) ) )
		self.assertEqual( displays["out"].childNames( "/plane" ), IECore.InternedStringVectorData() )
		
		# check that we have some displays
		
		display = displays.addDisplay( "beauty", IECore.Display( "beauty.exr", "exr", "rgba" ) )
		display["parameters"].addMember( "test", IECore.FloatData( 10 ) )

		displays.addDisplay( "diffuse", IECore.Display( "diffuse.exr", "exr", "color aov_diffuse" ) )
		
		g = displays["out"]["globals"].getValue()
		self.assertEqual( len( g ), 2 )
		self.assertEqual( g["display:beauty.exr"], IECore.Display( "beauty.exr", "exr", "rgba", { "test" : 10.0 } ) )
		self.assertEqual( g["display:diffuse.exr"], IECore.Display( "diffuse.exr", "exr", "color aov_diffuse" ) )
		
		# check that we can turn 'em off as well
		display["active"].setValue( False )
		
		g = displays["out"]["globals"].getValue()
		self.assertEqual( len( g ), 1 )
		self.assertEqual( g["display:diffuse.exr"], IECore.Display( "diffuse.exr", "exr", "color aov_diffuse" ) )
			
	def testSerialisation( self ) :
	
		s = Gaffer.ScriptNode()
		s["displaysNode"] = GafferScene.Displays()
		display = s["displaysNode"].addDisplay( "beauty", IECore.Display( "beauty.exr", "exr", "rgba" ) )
		display["parameters"].addMember( "test", IECore.FloatData( 10 ) )
		
		ss = s.serialise()
		
		s2 = Gaffer.ScriptNode()		
		s2.execute( ss )
		
		g = s2["displaysNode"]["out"]["globals"].getValue()
		self.assertEqual( len( g ), 1 )
		self.assertEqual( g["display:beauty.exr"], IECore.Display( "beauty.exr", "exr", "rgba", { "test" : 10.0 } ) )
		self.assertEqual( len( s2["displaysNode"]["displays"] ), 1 )
		self.assertTrue( "displays1" not in s2["displaysNode"] )
		
	def testRegistry( self ) :
	
		GafferScene.Displays.registerDisplay( "test", IECore.Display( "test.exr", "exr", "rgba" ) )
		GafferScene.Displays.registerDisplay( "test2", IECore.Display( "test.exr", "exr", "rgba" ) )
		
		self.assertEqual( GafferScene.Displays.registeredDisplays(), ( "test", "test2" ) )
	
	def testHashPassThrough( self ) :
	
		# the hash of the per-object part of a displays output should be
		# identical to the input, so that they share cache entries.
	
		p = GafferScene.Plane()
		displays = GafferScene.Displays()
		displays["in"].setInput( p["out"] )
		
		self.assertSceneHashesEqual( p["out"], displays["out"], childPlugNames = ( "transform", "bound", "attributes", "object", "childNames" ) )
	
	def testParametersHaveUsefulNames( self ) :
	
		displays = GafferScene.Displays()
		displays.addDisplay( "test", IECore.Display( "name", "type", "data", { "paramA" : 1, "paramB" : 2 } ) )
		
		self.assertEqual( set( displays["displays"][0]["parameters"].keys() ), set( [ "paramA", "paramB" ] ) )
		
if __name__ == "__main__":
	unittest.main()
