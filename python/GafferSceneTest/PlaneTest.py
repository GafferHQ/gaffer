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
import imath

import IECore
import IECoreScene

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
		self.assertEqual( p["out"].transform( "/" ), imath.M44f() )
		self.assertEqual( p["out"].bound( "/" ), imath.Box3f( imath.V3f( -0.5, -0.5, 0 ), imath.V3f( 0.5, 0.5, 0 ) ) )
		self.assertEqual( p["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "plane" ] ) )

		self.assertEqual( p["out"].object( "/plane" ), IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -0.5 ), imath.V2f( 0.5 ) ) ) )
		self.assertEqual( p["out"].transform( "/plane" ), imath.M44f() )
		self.assertEqual( p["out"].bound( "/plane" ), imath.Box3f( imath.V3f( -0.5, -0.5, 0 ), imath.V3f( 0.5, 0.5, 0 ) ) )
		self.assertEqual( p["out"].childNames( "/plane" ), IECore.InternedStringVectorData() )

	def testPlugs( self ) :

		p = GafferScene.Plane()
		m = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -0.5 ), imath.V2f( 0.5 ) ) )
		self.assertEqual( p["out"].object( "/plane" ), m )
		h = p["out"].objectHash( "/plane" )

		p["dimensions"].setValue( imath.V2f( 2.5, 5 ) )
		m = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1.25, -2.5 ), imath.V2f( 1.25, 2.5 ) ) )
		self.assertEqual( p["out"].object( "/plane" ), m )
		self.assertNotEqual( p["out"].objectHash( "/plane" ), h )
		h = p["out"].objectHash( "/plane" )

		p["divisions"].setValue( imath.V2i( 5, 10 ) )
		m = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1.25, -2.5 ), imath.V2f( 1.25, 2.5 ) ), imath.V2i( 5, 10 ) )
		self.assertEqual( p["out"].object( "/plane" ), m )
		self.assertNotEqual( p["out"].objectHash( "/plane" ), h )

	def testAffects( self ) :

		p = GafferScene.Plane()

		s = GafferTest.CapturingSlot( p.plugDirtiedSignal() )

		p["name"].setValue( "ground" )
		self.assertEqual(
			{ x[0] for x in s if not x[0].getName().startswith( "__" ) },
			{ p["name"], p["out"]["childNames"], p["out"]["exists"], p["out"]["childBounds"], p["out"]["set"], p["out"] }
		)

		del s[:]

		p["dimensions"]["x"].setValue( 10 )
		found = False
		for ss in s :
			if ss[0].isSame( p["out"] ) :
				found = True
		self.assertTrue( found )

	def testTransform( self ) :

		p = GafferScene.Plane()
		p["transform"]["translate"].setValue( imath.V3f( 1, 0, 0 ) )

		self.assertEqual( p["out"].transform( "/" ), imath.M44f() )
		self.assertEqual( p["out"].transform( "/plane" ), imath.M44f().translate( imath.V3f( 1, 0, 0 ) ) )

		self.assertEqual( p["out"].bound( "/" ), imath.Box3f( imath.V3f( 0.5, -0.5, 0 ), imath.V3f( 1.5, 0.5, 0 ) ) )
		self.assertEqual( p["out"].bound( "/plane" ), imath.Box3f( imath.V3f( -0.5, -0.5, 0 ), imath.V3f( 0.5, 0.5, 0 ) ) )

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

	def testUndoAndRedoAndCompute( self ) :

		s = Gaffer.ScriptNode()

		with Gaffer.UndoScope( s ) :
			s["p"] = GafferScene.Plane()

		self.assertTrue( isinstance( s["p"]["out"].object( "/plane" ), IECoreScene.MeshPrimitive ) )

		s.undo()
		s.redo()

		self.assertTrue( isinstance( s["p"]["out"].object( "/plane" ), IECoreScene.MeshPrimitive ) )

	def testNonExistentSets( self ) :

		p = GafferScene.Plane()
		p["sets"].setValue( "A B")
		self.assertEqual( p["out"]["setNames"].getValue(), IECore.InternedStringVectorData( [ "A", "B" ] ) )

		self.assertEqual( p["out"].set( "" ), IECore.PathMatcherData() )
		self.assertEqual( p["out"].set( "nonexistent1" ), IECore.PathMatcherData() )
		self.assertEqual( p["out"].setHash( "nonexistent1" ), p["out"].setHash( "nonexistent2" ) )
		self.assertTrue( p["out"].set( "nonexistent1", _copy = False ).isSame( p["out"].set( "nonexistent2", _copy = False ) ) )

	def testSetNameAffectsSet( self ) :

		p = GafferScene.Plane()
		a = p.affects( p["sets"] )
		self.assertTrue( p["out"]["set"] in a )

	def testEnabledAffectsSet( self ) :

		p = GafferScene.Plane()
		a = p.affects( p["enabled"] )
		self.assertTrue( p["out"]["set"] in a )

if __name__ == "__main__":
	unittest.main()
