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

import IECore

import GafferScene
import GafferSceneTest

class ParentTest( GafferSceneTest.SceneTestCase ) :
	
	def test( self ) :
	
		s = GafferScene.Sphere()
		c = GafferScene.Cube()
		
		g = GafferScene.Group()
		g["in"].setInput( s["out"] )
		g["in1"].setInput( c["out"] )
		
		p = GafferScene.Parent()
		p["in"].setInput( g["out"] )
		p["parent"].setValue( "/group" )
		p["child"].setInput( c["out"] )
		
		self.assertEqual( p["out"].childNames( "/group" ), IECore.InternedStringVectorData( [ "sphere", "cube", "cube1" ] ) )
		self.assertPathsEqual( p["out"], "/group/cube", p["out"], "/group/cube1" )
		
		self.assertSceneValid( p["out"] )
	
	def testParentAtRoot( self ) :
	
		s = GafferScene.Sphere()
		c = GafferScene.Cube()
		
		g = GafferScene.Group()
		g["in"].setInput( s["out"] )
		g["in1"].setInput( c["out"] )
		
		p = GafferScene.Parent()
		p["in"].setInput( g["out"] )
		p["parent"].setValue( "/" )
		p["child"].setInput( c["out"] )
		
		self.assertEqual( p["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "group", "cube" ] ) )
		self.assertPathsEqual( p["out"], "/group/cube", p["out"], "/cube" )
		
		self.assertSceneValid( p["out"] )
		
	def testUnconnected( self ) :
		
		p = GafferScene.Parent()
		
		self.assertEqual( p["out"].childNames( "/" ), IECore.InternedStringVectorData( [] ) )
		self.assertSceneValid( p["out"] )

	def testPassThroughWhenNoChild( self ) :
	
		c = GafferScene.Cube()

		p = GafferScene.Parent()
		p["parent"].setValue( "/" )
		p["in"].setInput( c["out"] )
		
		self.assertScenesEqual( p["out"], c["out"] )
		self.assertSceneHashesEqual( p["out"], c["out"] )
	
	def testNameUniqueification( self ) :
	
		c = GafferScene.Cube()
		
		g = GafferScene.Group()
		g["in"].setInput( c["out"] )
		g["in1"].setInput( c["out"] )
		
		p = GafferScene.Parent()
		p["in"].setInput( g["out"] )
		p["parent"].setValue( "/group" )
		p["child"].setInput( c["out"] )
		
		self.assertEqual( p["out"].childNames( "/group" ), IECore.InternedStringVectorData( [ "cube", "cube1", "cube2" ] ) )
		self.assertSceneValid( p["out"] )

	def testChildSmallerThanExistingChildren( self ) :
	
		c = GafferScene.Cube()
		
		cSmall = GafferScene.Cube()
		cSmall["dimensions"].setValue( IECore.V3f( 0.1 ) )
				
		g = GafferScene.Group()
		g["in"].setInput( c["out"] )
		
		p = GafferScene.Parent()
		p["in"].setInput( g["out"] )
		p["parent"].setValue( "/group" )
		p["child"].setInput( cSmall["out"] )

		self.assertSceneValid( p["out"] )

	def testChildLargerThanExistingChildren( self ) :
	
		c = GafferScene.Cube()
		
		cLarge = GafferScene.Cube()
		cLarge["dimensions"].setValue( IECore.V3f( 10 ) )
				
		g = GafferScene.Group()
		g["in"].setInput( c["out"] )
		
		p = GafferScene.Parent()
		p["in"].setInput( g["out"] )
		p["parent"].setValue( "/group" )
		p["child"].setInput( cLarge["out"] )

		self.assertSceneValid( p["out"] )
	
	def testEmptyParent( self ) :
	
		c = GafferScene.Cube()
		
		g = GafferScene.Group()
		g["in"].setInput( c["out"] )
		
		p = GafferScene.Parent()
		p["in"].setInput( g["out"] )
		p["parent"].setValue( "" )
		p["child"].setInput( c["out"] )
		
		self.assertScenesEqual( p["out"], g["out"] )
		self.assertSceneHashesEqual( p["out"], g["out"] )
	
	def testParentInsideParent( self ) :
	
		c = GafferScene.Cube()
		
		p1 = GafferScene.Parent()
		p1["in"].setInput( c["out"] )
		p1["parent"].setValue( "/cube" )
		p1["child"].setInput( c["out"] )
		
		self.assertEqual( p1["out"].childNames( "/cube" ), IECore.InternedStringVectorData( [ "cube" ] ) )

		p2 = GafferScene.Parent()
		p2["in"].setInput( p1["out"] )
		p2["parent"].setValue( "/cube/cube" )
		p2["child"].setInput( c["out"] )

		self.assertEqual( p2["out"].childNames( "/cube" ), IECore.InternedStringVectorData( [ "cube" ] ) )
		self.assertEqual( p2["out"].childNames( "/cube/cube" ), IECore.InternedStringVectorData( [ "cube" ] ) )
		
if __name__ == "__main__":
	unittest.main()
