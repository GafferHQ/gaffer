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
import GafferTest
import GafferScene
import GafferSceneTest

class PlaneTest( GafferSceneTest.SceneTestCase ) :

	def testConstruct( self ) :
	
		p = GafferScene.Plane()
		self.assertEqual( p.getName(), "Plane" )
	
	def testCompute( self ) :
	
		p = GafferScene.Plane()
	
		self.assertEqual( p["out"].object( "/" ), IECore.NullObject() )
		self.assertEqual( p["out"].transform( "/" ), IECore.M44f() )
		self.assertEqual( p["out"].bound( "/" ), IECore.Box3f( IECore.V3f( -0.5, -0.5, 0 ), IECore.V3f( 0.5, 0.5, 0 ) ) )
		self.assertEqual( p["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "plane" ] ) )
		
		self.assertEqual( p["out"].object( "/plane" ), IECore.MeshPrimitive.createPlane( IECore.Box2f( IECore.V2f( -0.5 ), IECore.V2f( 0.5 ) ) ) )
		self.assertEqual( p["out"].transform( "/plane" ), IECore.M44f() )
		self.assertEqual( p["out"].bound( "/plane" ), IECore.Box3f( IECore.V3f( -0.5, -0.5, 0 ), IECore.V3f( 0.5, 0.5, 0 ) ) )
		self.assertEqual( p["out"].childNames( "/plane" ), IECore.InternedStringVectorData() )
		
	def testPlugs( self ) : 
		
		p = GafferScene.Plane()
		m = IECore.MeshPrimitive.createPlane( IECore.Box2f( IECore.V2f( -0.5 ), IECore.V2f( 0.5 ) ) )
		self.assertEqual( p["out"].object( "/plane" ), m )
		h = p["out"].objectHash( "/plane" )
		
		p["dimensions"].setValue( IECore.V2f( 2.5, 5 ) )
		m = IECore.MeshPrimitive.createPlane( IECore.Box2f( IECore.V2f( -1.25, -2.5 ), IECore.V2f( 1.25, 2.5 ) ) )
		self.assertEqual( p["out"].object( "/plane" ), m )
		self.assertNotEqual( p["out"].objectHash( "/plane" ), h )
		h = p["out"].objectHash( "/plane" )
		
		p["divisions"].setValue( IECore.V2i( 5, 10 ) )
		m = IECore.MeshPrimitive.createPlane( IECore.Box2f( IECore.V2f( -1.25, -2.5 ), IECore.V2f( 1.25, 2.5 ) ), IECore.V2i( 5, 10 ) )
		self.assertEqual( p["out"].object( "/plane" ), m )
		self.assertNotEqual( p["out"].objectHash( "/plane" ), h )
	
	def testAffects( self ) :
	
		p = GafferScene.Plane()

		s = GafferTest.CapturingSlot( p.plugDirtiedSignal() )
		
		p["name"].setValue( "ground" )
		self.assertEqual( len( s ), 2 )
		self.failUnless( s[0][0].isSame( p["out"]["childNames"] ) )
		self.failUnless( s[1][0].isSame( p["out"] ) )
		
		del s[:]
		
		p["dimensions"]["x"].setValue( 10 )
		found = False
		for ss in s :
			if ss[0].isSame( p["out"] ) :
				found = True
		self.failUnless( found )
	
	def testTransform( self ) :
	
		p = GafferScene.Plane()
		p["transform"]["translate"].setValue( IECore.V3f( 1, 0, 0 ) )
		
		self.assertEqual( p["out"].transform( "/" ), IECore.M44f() )
		self.assertEqual( p["out"].transform( "/plane" ), IECore.M44f.createTranslated( IECore.V3f( 1, 0, 0 ) ) )
		
		self.assertEqual( p["out"].bound( "/" ), IECore.Box3f( IECore.V3f( 0.5, -0.5, 0 ), IECore.V3f( 1.5, 0.5, 0 ) ) )
		self.assertEqual( p["out"].bound( "/plane" ), IECore.Box3f( IECore.V3f( -0.5, -0.5, 0 ), IECore.V3f( 0.5, 0.5, 0 ) ) )

	def testEnabled( self ) :
	
		p = GafferScene.Plane()
		p["enabled"].setValue( False )
		
		self.assertSceneValid( p["out"] )
		self.assertTrue( p["out"].bound( "/" ).isEmpty() )
		self.assertEqual( p["out"].childNames( "/" ), IECore.InternedStringVectorData() )

		p["enabled"].setValue( True )
		self.assertSceneValid( p["out"] )
		self.assertEqual( p["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "plane" ] ) )	

	def testSerialise( self ) :
	
		s = Gaffer.ScriptNode()
		s["p"] = GafferScene.Plane()
		
		ss = s.serialise()
	
if __name__ == "__main__":
	unittest.main()
