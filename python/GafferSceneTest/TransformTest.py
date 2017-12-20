##########################################################################
#
#  Copyright (c) 2013-2014, Image Engine Design Inc. All rights reserved.
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
import math
import imath

import IECore
import IECoreScene

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest

class TransformTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		sphere = IECoreScene.SpherePrimitive()
		input = GafferSceneTest.CompoundObjectSource()
		input["in"].setValue(
			IECore.CompoundObject( {
				"bound" : IECore.Box3fData( sphere.bound() ),
				"children" : {
					"group" : {
						"bound" : IECore.Box3fData( sphere.bound() ),
						"children" : {
							"sphere" : {
								"bound" : IECore.Box3fData( sphere.bound() ),
								"object" : sphere,
							},
						},
					},
				},
			} ),
		)

		self.assertSceneValid( input["out"] )

		transform = GafferScene.Transform()
		transform["in"].setInput( input["out"] )

		# by default transform should do nothing

		self.assertSceneValid( transform["out"] )
		self.assertScenesEqual( transform["out"], input["out"] )

		# even when setting a transform it should do nothing, as
		# it requires a filter before operating (applying the same transform
		# at every location is really not very useful).

		transform["transform"]["translate"].setValue( imath.V3f( 1, 2, 3 ) )

		self.assertSceneValid( transform["out"] )
		self.assertScenesEqual( transform["out"], input["out"] )

		# applying a filter should cause things to happen

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/group/sphere" ] ) )
		transform["filter"].setInput( filter["out"] )

		self.assertSceneValid( transform["out"] )

		self.assertEqual( transform["out"].transform( "/group/sphere" ), imath.M44f().translate( imath.V3f( 1, 2, 3 ) ) )
		self.assertEqual( transform["out"].transform( "/group" ), imath.M44f() )

		self.assertEqual( transform["out"].bound( "/group/sphere" ), imath.Box3f( imath.V3f( -1 ), imath.V3f( 1 ) ) )
		self.assertEqual( transform["out"].bound( "/group" ), imath.Box3f( imath.V3f( 0, 1, 2 ), imath.V3f( 2, 3, 4 ) ) )
		self.assertEqual( transform["out"].bound( "/" ), imath.Box3f( imath.V3f( 0, 1, 2 ), imath.V3f( 2, 3, 4 ) ) )

	def testEnableBehaviour( self ) :

		t = GafferScene.Transform()
		self.assertTrue( t.enabledPlug().isSame( t["enabled"] ) )
		self.assertTrue( t.correspondingInput( t["out"] ).isSame( t["in"] ) )
		self.assertEqual( t.correspondingInput( t["in"] ), None )
		self.assertEqual( t.correspondingInput( t["enabled"] ), None )

	def testSpace( self ) :

		sphere = GafferScene.Sphere()
		sphere["transform"]["translate"].setValue( imath.V3f( 1, 0, 0 ) )

		transform = GafferScene.Transform()
		transform["in"].setInput( sphere["out"] )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )
		transform["filter"].setInput( filter["out"] )

		self.assertEqual( transform["space"].getValue(), GafferScene.Transform.Space.Local )
		transform["transform"]["rotate"]["y"].setValue( 90 )

		self.assertSceneValid( transform["out"] )

		self.assertTrue(
			imath.V3f( 1, 0, 0 ).equalWithAbsError(
				imath.V3f( 0 ) * transform["out"].fullTransform( "/sphere" ),
				0.000001
			)
		)

		transform["space"].setValue( GafferScene.Transform.Space.Parent )
		self.assertTrue(
			imath.V3f( 0, 0, -1 ).equalWithAbsError(
				imath.V3f( 0 ) * transform["out"].fullTransform( "/sphere" ),
				0.000001
			)
		)

		transform["space"].setValue( GafferScene.Transform.Space.World )
		self.assertTrue(
			imath.V3f( 0, 0, -1 ).equalWithAbsError(
				imath.V3f( 0 ) * transform["out"].fullTransform( "/sphere" ),
				0.000001
			)
		)

	def testSpaceWithNestedHierarchy( self ) :

		sphere = GafferScene.Sphere()

		group = GafferScene.Group()
		group["in"][0].setInput( sphere["out"] )
		group["transform"]["translate"].setValue( imath.V3f( 1, 0, 0 ) )

		transform = GafferScene.Transform()
		transform["in"].setInput( group["out"] )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/group/sphere" ] ) )
		transform["filter"].setInput( filter["out"] )

		self.assertEqual( transform["space"].getValue(), GafferScene.Transform.Space.Local )
		self.assertSceneValid( transform["out"] )
		self.assertTrue(
			imath.V3f( 1, 0, 0 ).equalWithAbsError(
				imath.V3f( 0 ) * transform["out"].fullTransform( "/group/sphere" ),
				0.000001
			)
		)

		transform["space"].setValue( GafferScene.Transform.Space.Parent )
		self.assertSceneValid( transform["out"] )
		self.assertTrue(
			imath.V3f( 1, 0, 0 ).equalWithAbsError(
				imath.V3f( 0 ) * transform["out"].fullTransform( "/group/sphere" ),
				0.000001
			)
		)

		transform["space"].setValue( GafferScene.Transform.Space.World )
		transform["transform"]["rotate"]["y"].setValue( 90 )
		self.assertTrue(
			imath.V3f( 0, 0, -1 ).equalWithAbsError(
				imath.V3f( 0 ) * transform["out"].fullTransform( "/group/sphere" ),
				0.000001
			)
		)

	def testResetLocal( self ) :

		sphere = GafferScene.Sphere()
		sphere["transform"]["translate"].setValue( imath.V3f( 1, 0, 0 ) )

		group = GafferScene.Group()
		group["in"][0].setInput( sphere["out"] )
		group["transform"]["translate"].setValue( imath.V3f( 1, 0, 0 ) )

		transform = GafferScene.Transform()
		transform["in"].setInput( group["out"] )
		transform["transform"]["rotate"]["y"].setValue( 90 )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/group/sphere" ] ) )
		transform["filter"].setInput( filter["out"] )

		transform["space"].setValue( GafferScene.Transform.Space.ResetLocal )
		self.assertSceneValid( transform["out"] )
		self.assertTrue(
			imath.V3f( 1, 0, 0 ).equalWithAbsError(
				imath.V3f( 0 ) * transform["out"].fullTransform( "/group/sphere" ),
				0.000001
			)
		)
		self.assertTrue(
			imath.V3f( 2, 0, 0 ).equalWithAbsError(
				imath.V3f( 0, 0, 1 ) * transform["out"].fullTransform( "/group/sphere" ),
				0.000001
			)
		)
		self.assertEqual(
			transform["out"].transform( "/group/sphere" ),
			imath.M44f().rotate( imath.V3f( 0, math.radians( 90 ), 0 ) )
		)

	def testResetWorld( self ) :

		sphere = GafferScene.Sphere()
		sphere["transform"]["translate"].setValue( imath.V3f( 1, 0, 0 ) )

		group = GafferScene.Group()
		group["in"][0].setInput( sphere["out"] )
		group["transform"]["translate"].setValue( imath.V3f( 1, 0, 0 ) )

		transform = GafferScene.Transform()
		transform["in"].setInput( group["out"] )
		transform["transform"]["rotate"]["y"].setValue( 90 )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/group/sphere" ] ) )
		transform["filter"].setInput( filter["out"] )

		transform["space"].setValue( GafferScene.Transform.Space.ResetWorld )
		self.assertSceneValid( transform["out"] )
		self.assertTrue(
			imath.V3f( 0, 0, 0 ).equalWithAbsError(
				imath.V3f( 0 ) * transform["out"].fullTransform( "/group/sphere" ),
				0.000001
			)
		)
		self.assertTrue(
			imath.V3f( 1, 0, 0 ).equalWithAbsError(
				imath.V3f( 0, 0, 1 ) * transform["out"].fullTransform( "/group/sphere" ),
				0.000001
			)
		)
		self.assertEqual(
			transform["out"].fullTransform( "/group/sphere" ),
			imath.M44f().rotate( imath.V3f( 0, math.radians( 90 ), 0 ) )
		)

	def testWorldWithMatchingAncestors( self ) :

		b = GafferScene.Sphere()
		b["name"].setValue( "b" )

		a = GafferScene.Group()
		a["in"][0].setInput( b["out"] )
		a["name"].setValue( "a" )

		t = GafferScene.Transform()
		t["in"].setInput( b["out"] )
		t["transform"]["translate"].setValue( imath.V3f( 1, 2, 3 ) )
		t["space"].setValue( t.Space.World )

		f = GafferScene.PathFilter()
		f["paths"].setValue( IECore.StringVectorData( [ "/a", "/a/b" ] ) )
		t["filter"].setInput( f["out"] )

		self.assertSceneValid( t["out"] )
		self.assertEqual(
			t["out"].fullTransform( "/a" ),
			imath.M44f().translate( imath.V3f( 1, 2, 3 ) )
		)

		# We want it to be as if /a/b has been transformed
		# independently in world space, and not inherit the
		# additional transform also applied to /a.

		self.assertEqual(
			t["out"].fullTransform( "/a/b" ),
			imath.M44f().translate( imath.V3f( 1, 2, 3 ) )
		)

		b["transform"]["translate"].setValue( imath.V3f( 4, 5, 6 ) )
		self.assertSceneValid( t["out"] )
		self.assertEqual(
			t["out"].fullTransform( "/a/b" ),
			imath.M44f().translate( imath.V3f( 5, 7, 9 ) )
		)

	def testResetWorldWithMatchingAncestors( self ) :

		c = GafferScene.Sphere()
		c["name"].setValue( "c" )

		b = GafferScene.Group()
		b["in"][0].setInput( c["out"] )
		b["name"].setValue( "b" )

		a = GafferScene.Group()
		a["in"][0].setInput( b["out"] )
		a["name"].setValue( "a" )

		t = GafferScene.Transform()
		t["in"].setInput( a["out"] )
		t["transform"]["translate"].setValue( imath.V3f( 1, 2, 3 ) )
		t["space"].setValue( t.Space.ResetWorld )

		# Apply to /a and /a/b/c so that we must take into
		# account the changing parent transform of /a/b/c
		# to get it's absolute position in world space
		# right.

		f = GafferScene.PathFilter()
		f["paths"].setValue( IECore.StringVectorData( [ "/a", "/a/b/c" ] ) )
		t["filter"].setInput( f["out"] )

		# Check that we're good.

		self.assertSceneValid( t["out"] )

		self.assertEqual(
			t["out"].fullTransform( "/a" ),
			imath.M44f().translate( imath.V3f( 1, 2, 3 ) )
		)

		self.assertEqual(
			t["out"].fullTransform( "/a/b" ),
			imath.M44f().translate( imath.V3f( 1, 2, 3 ) )
		)

		self.assertEqual(
			t["out"].fullTransform( "/a/b/c" ),
			imath.M44f().translate( imath.V3f( 1, 2, 3 ) )
		)

		# Change the transform on /a/b, and check that it is
		# retained, but that /a/b/c adjusts for it and maintains
		# the required absolute transform.

		b["transform"]["translate"].setValue( imath.V3f( 9, 7, 5 ) )

		self.assertSceneValid( t["out"] )

		self.assertEqual(
			t["out"].fullTransform( "/a" ),
			imath.M44f().translate( imath.V3f( 1, 2, 3 ) )
		)

		self.assertEqual(
			t["out"].fullTransform( "/a/b" ),
			imath.M44f().translate( imath.V3f( 10, 9, 8 ) )
		)

		self.assertEqual(
			t["out"].fullTransform( "/a/b/c" ),
			imath.M44f().translate( imath.V3f( 1, 2, 3 ) )
		)

	def testObjectBoundIncludedWhenDescendantsMatch( self ) :

		s = GafferScene.Cube()

		f = GafferScene.PathFilter()
		f["paths"].setValue( IECore.StringVectorData( [ "/..." ] ) ) # the dread ellipsis!

		t = GafferScene.Transform()
		t["in"].setInput( s["out"] )
		t["filter"].setInput( f["out"] )
		t["transform"]["translate"].setValue( imath.V3f( 1 ) )

		self.assertSceneValid( t["out"] )
		self.assertEqual( t["out"].bound( "/" ), imath.Box3f( imath.V3f( 0.5 ), imath.V3f( 1.5 ) ) )

if __name__ == "__main__":
	unittest.main()
