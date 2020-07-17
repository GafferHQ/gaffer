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
import imath

import IECore
import IECoreScene

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest

class SphereTest( GafferSceneTest.SceneTestCase ) :

	def testConstruct( self ) :

		s = GafferScene.Sphere()
		self.assertEqual( s.getName(), "Sphere" )

	def testCompute( self ) :

		s = GafferScene.Sphere()
		s["type"].setValue( GafferScene.Sphere.Type.Primitive )

		self.assertEqual( s["out"].object( "/" ), IECore.NullObject() )
		self.assertEqual( s["out"].transform( "/" ), imath.M44f() )
		self.assertEqual( s["out"].bound( "/" ), imath.Box3f( imath.V3f( -1 ), imath.V3f( 1 ) ) )
		self.assertEqual( s["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "sphere" ] ) )

		self.assertEqual( s["out"].object( "/sphere" ), IECoreScene.SpherePrimitive( 1 ) )
		self.assertEqual( s["out"].transform( "/sphere" ), imath.M44f() )
		self.assertEqual( s["out"].bound( "/sphere" ), imath.Box3f( imath.V3f( -1 ), imath.V3f( 1 ) ) )
		self.assertEqual( s["out"].childNames( "/sphere" ), IECore.InternedStringVectorData() )

	def testMesh( self ) :

		s = GafferScene.Sphere()
		s["type"].setValue( GafferScene.Sphere.Type.Mesh )
		m = IECoreScene.MeshPrimitive.createSphere( 1 )
		self.assertEqual( s["out"].object( "/sphere" ), m )
		c = Gaffer.Context()
		h = s["out"].objectHash( "/sphere" )

		s["radius"].setValue( 3 )
		m = IECoreScene.MeshPrimitive.createSphere( 3 )
		self.assertEqual( s["out"].object( "/sphere" ), m )
		self.assertNotEqual( s["out"].objectHash( "/sphere" ), h )
		h = s["out"].objectHash( "/sphere" )

		s["zMin"].setValue( -0.75 )
		m = IECoreScene.MeshPrimitive.createSphere( 3, -0.75 )
		self.assertEqual( s["out"].object( "/sphere" ), m )
		self.assertNotEqual( s["out"].objectHash( "/sphere" ), h )
		h = s["out"].objectHash( "/sphere" )

		s["zMax"].setValue( 0.75 )
		m = IECoreScene.MeshPrimitive.createSphere( 3, -0.75, 0.75 )
		self.assertEqual( s["out"].object( "/sphere" ), m )
		self.assertNotEqual( s["out"].objectHash( "/sphere" ), h )
		h = s["out"].objectHash( "/sphere" )

		s["thetaMax"].setValue( 300 )
		m = IECoreScene.MeshPrimitive.createSphere( 3, -0.75, 0.75, 300 )
		self.assertEqual( s["out"].object( "/sphere" ), m )
		self.assertNotEqual( s["out"].objectHash( "/sphere" ), h )
		h = s["out"].objectHash( "/sphere" )

		s["divisions"].setValue( imath.V2i( 5, 10 ) )
		m = IECoreScene.MeshPrimitive.createSphere( 3, -0.75, 0.75, 300, imath.V2i( 5, 10 ) )
		self.assertEqual( s["out"].object( "/sphere" ), m )
		self.assertNotEqual( s["out"].objectHash( "/sphere" ), h )

	def testSphere( self ) :

		s = GafferScene.Sphere()
		s["type"].setValue( GafferScene.Sphere.Type.Primitive )
		m = IECoreScene.SpherePrimitive( 1 )
		self.assertEqual( s["out"].object( "/sphere" ), m )
		h = s["out"].objectHash( "/sphere" )

		s["radius"].setValue( 3 )
		m = IECoreScene.SpherePrimitive( 3 )
		self.assertEqual( s["out"].object( "/sphere" ), m )
		self.assertNotEqual( s["out"].objectHash( "/sphere" ), h )
		h = s["out"].objectHash( "/sphere" )

		s["zMin"].setValue( -0.75 )
		m = IECoreScene.SpherePrimitive( 3, -0.75 )
		self.assertEqual( s["out"].object( "/sphere" ), m )
		self.assertNotEqual( s["out"].objectHash( "/sphere" ), h )
		h = s["out"].objectHash( "/sphere" )

		s["zMax"].setValue( 0.75 )
		m = IECoreScene.SpherePrimitive( 3, -0.75, 0.75 )
		self.assertEqual( s["out"].object( "/sphere" ), m )
		self.assertNotEqual( s["out"].objectHash( "/sphere" ), h )
		h = s["out"].objectHash( "/sphere" )

		s["thetaMax"].setValue( 300 )
		m = IECoreScene.SpherePrimitive( 3, -0.75, 0.75, 300 )
		self.assertEqual( s["out"].object( "/sphere" ), m )
		self.assertNotEqual( s["out"].objectHash( "/sphere" ), h )
		h = s["out"].objectHash( "/sphere" )

		s["divisions"].setValue( imath.V2i( 5, 10 ) )
		# divisions don't affect SpherePrimitives
		self.assertEqual( s["out"].object( "/sphere" ), m )
		# divisions do affect the hash, since we don't check the value of type
		self.assertNotEqual( s["out"].objectHash( "/sphere" ), h )

	def testAffects( self ) :

		s = GafferScene.Sphere()

		ss = GafferTest.CapturingSlot( s.plugDirtiedSignal() )

		s["name"].setValue( "ball" )
		self.assertEqual(
			{ x[0] for x in ss if not x[0].getName().startswith( "__" ) },
			{ s["name"], s["out"]["childNames"], s["out"]["exists"], s["out"]["childBounds"], s["out"]["set"], s["out"] }
		)

		del ss[:]

		s["divisions"]["x"].setValue( 10 )
		found = False
		for sss in ss :
			if sss[0].isSame( s["out"] ) :
				found = True
		self.assertTrue( found )

	def testTransform( self ) :

		s = GafferScene.Sphere()
		s["type"].setValue( GafferScene.Sphere.Type.Primitive )
		s["transform"]["translate"].setValue( imath.V3f( 1, 0, 0 ) )

		self.assertEqual( s["out"].transform( "/" ), imath.M44f() )
		self.assertEqual( s["out"].transform( "/sphere" ), imath.M44f().translate( imath.V3f( 1, 0, 0 ) ) )

		self.assertEqual( s["out"].bound( "/" ), imath.Box3f( imath.V3f( 0, -1, -1 ), imath.V3f( 2, 1, 1 ) ) )
		self.assertEqual( s["out"].bound( "/sphere" ), imath.Box3f( imath.V3f( -1 ), imath.V3f( 1 ) ) )

	def testEnabled( self ) :

		s = GafferScene.Sphere()
		s["enabled"].setValue( False )

		self.assertSceneValid( s["out"] )
		self.assertTrue( s["out"].bound( "/" ).isEmpty() )
		self.assertEqual( s["out"].childNames( "/" ), IECore.InternedStringVectorData() )

		s["enabled"].setValue( True )
		self.assertSceneValid( s["out"] )
		self.assertEqual( s["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "sphere" ] ) )

	def testSerialise( self ) :

		s = Gaffer.ScriptNode()
		s["s"] = GafferScene.Sphere()

		ss = s.serialise()

	def testChildNamesHash( self ) :

		s1 = GafferScene.Sphere()
		s1["name"].setValue( "sphere1" )

		s2 = GafferScene.Sphere()
		s2["name"].setValue( "sphere2" )

		self.assertNotEqual( s1["out"].childNamesHash( "/" ), s2["out"].childNamesHash( "/" ) )
		self.assertEqual( s1["out"].childNamesHash( "/sphere1" ), s2["out"].childNamesHash( "/sphere2" ) )

		self.assertNotEqual( s1["out"].childNames( "/" ), s2["out"].childNames( "/" ) )
		self.assertTrue( s1["out"].childNames( "/sphere1", _copy=False ).isSame( s2["out"].childNames( "sphere2", _copy=False ) ) )

	def testTransformAffectsBound( self ) :

		s = GafferScene.Sphere()
		self.assertTrue( s["out"]["bound"] in s.affects( s["transform"]["translate"]["x"] ) )

if __name__ == "__main__":
	unittest.main()
