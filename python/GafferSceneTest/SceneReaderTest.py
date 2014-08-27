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

import os
import unittest

import IECore

import Gaffer
import GafferScene
import GafferSceneTest

class SceneReaderTest( GafferSceneTest.SceneTestCase ) :

	__testFile = "/tmp/test.scc"

	def testFileRefreshProblem( self ) :

		sc = IECore.SceneCache( self.__testFile, IECore.IndexedIO.OpenMode.Write )

		t = sc.createChild( "1" )
		t.writeTransform( IECore.M44dData( IECore.M44d.createTranslated( IECore.V3d( 1, 0, 0 ) ) ), 0.0 )

		s = t.createChild( "2" )
		s.writeObject( IECore.SpherePrimitive( 10 ), 0.0 )

		del sc, t, s

		reader = GafferScene.SceneReader()
		reader["fileName"].setValue( self.__testFile )
		reader["refreshCount"].setValue( self.uniqueInt( self.__testFile ) )

		scene = reader["out"]
		self.assertEqual( scene.childNames( "/" ), IECore.InternedStringVectorData( [ "1" ] ) )

		del scene

		sc = IECore.SceneCache( self.__testFile, IECore.IndexedIO.OpenMode.Write )

		t = sc.createChild( "transform" )
		t.writeTransform( IECore.M44dData( IECore.M44d.createTranslated( IECore.V3d( 1, 0, 0 ) ) ), 0.0 )

		s = t.createChild( "shape" )
		s.writeObject( IECore.SpherePrimitive( 10 ), 0.0 )

		del sc, t, s

		# we have to remember to set the refresh counts to different values in different tests, otherwise
		# it thinks it's reading an old file...
		reader = GafferScene.SceneReader()
		reader["fileName"].setValue( self.__testFile )
		reader["refreshCount"].setValue( self.uniqueInt( self.__testFile ) )

		scene = reader["out"]
		self.assertEqual( scene.childNames( "/" ), IECore.InternedStringVectorData( [ "transform" ] ) )

	def testRead( self ) :

		sc = IECore.SceneCache( self.__testFile, IECore.IndexedIO.OpenMode.Write )

		t = sc.createChild( "transform" )
		t.writeTransform( IECore.M44dData( IECore.M44d.createTranslated( IECore.V3d( 1, 0, 0 ) ) ), 0.0 )

		s = t.createChild( "shape" )
		s.writeObject( IECore.SpherePrimitive( 10 ), 0.0 )

		del sc, t, s

		reader = GafferScene.SceneReader()
		reader["fileName"].setValue( self.__testFile )

		# we have to remember to set the refresh counts to different values in different tests, otherwise
		# it thinks it's reading an old file...
		reader["refreshCount"].setValue( self.uniqueInt( self.__testFile ) )

		scene = reader["out"]
		self.assertSceneValid( scene )

		self.assertEqual( scene.transform( "transform" ), IECore.M44f.createTranslated( IECore.V3f( 1, 0, 0 ) ) )
		self.assertEqual( scene.object( "transform/shape" ), IECore.SpherePrimitive( 10 ) )

	def writeAnimatedSCC( self ) :

		scene = IECore.SceneCache( self.__testFile, IECore.IndexedIO.OpenMode.Write )

		time = 0
		sc1 = scene.createChild( str( 1 ) )
		mesh = IECore.MeshPrimitive.createBox(IECore.Box3f(IECore.V3f(0),IECore.V3f(1)))
		mesh["Cd"] = IECore.PrimitiveVariable( IECore.PrimitiveVariable.Interpolation.Uniform, IECore.V3fVectorData( [ IECore.V3f( 1, 0, 0 ) ] * 6 ) )
		sc1.writeObject( mesh, time )
		sc1.writeTransform( IECore.M44dData(), time )

		sc2 = sc1.createChild( str( 2 ) )
		mesh = IECore.MeshPrimitive.createBox(IECore.Box3f(IECore.V3f(0),IECore.V3f(1)))
		mesh["Cd"] = IECore.PrimitiveVariable( IECore.PrimitiveVariable.Interpolation.Uniform, IECore.V3fVectorData( [ IECore.V3f( 0, 1, 0 ) ] * 6 ) )
		sc2.writeObject( mesh, time )
		sc2.writeTransform( IECore.M44dData(), time )

		sc3 = sc2.createChild( str( 3 ) )
		mesh = IECore.MeshPrimitive.createBox(IECore.Box3f(IECore.V3f(0),IECore.V3f(1)))
		mesh["Cd"] = IECore.PrimitiveVariable( IECore.PrimitiveVariable.Interpolation.Uniform, IECore.V3fVectorData( [ IECore.V3f( 0, 0, 1 ) ] * 6 ) )
		sc3.writeObject( mesh, time )
		sc3.writeTransform( IECore.M44dData(), time )

		for frame in [ 0.5, 1, 1.5, 2, 5, 10 ] :

			matrix = IECore.M44d.createTranslated( IECore.V3d( 1, frame, 0 ) )
			sc1.writeTransform( IECore.M44dData( matrix ), float( frame ) / 24 )

			mesh["Cd"] = IECore.PrimitiveVariable( IECore.PrimitiveVariable.Interpolation.Uniform, IECore.V3fVectorData( [ IECore.V3f( frame, 1, 0 ) ] * 6 ) )
			sc2.writeObject( mesh, float( frame ) / 24 )
			matrix = IECore.M44d.createTranslated( IECore.V3d( 2, frame, 0 ) )
			sc2.writeTransform( IECore.M44dData( matrix ), float( frame ) / 24 )

			matrix = IECore.M44d.createTranslated( IECore.V3d( 3, frame, 0 ) )
			sc3.writeTransform( IECore.M44dData( matrix ), float( frame ) / 24 )

	def testAnimatedScene( self ) :

		self.writeAnimatedSCC()

		reader = GafferScene.SceneReader()
		reader["fileName"].setValue( self.__testFile )
		reader["refreshCount"].setValue( self.uniqueInt( self.__testFile ) )

		scene = reader["out"]

		context = Gaffer.Context()
		context.setFrame( 0 )

		with context:
			self.assertEqual( scene.transform( "/1" ), IECore.M44f() )
			self.assertEqual( scene.transform( "/1/2" ), IECore.M44f() )
			self.assertEqual( scene.transform( "/1/2/3" ), IECore.M44f() )

		for time in [ 0.5, 1, 1.5, 2, 5, 10 ] :

			context.setFrame( time )

			with context:
				self.assertEqual( scene.transform( "/1" ), IECore.M44f.createTranslated( IECore.V3f( 1, time, 0 ) ) )
				self.assertEqual( scene.transform( "/1/2" ), IECore.M44f.createTranslated( IECore.V3f( 2, time, 0 ) ) )
				self.assertEqual( scene.transform( "/1/2/3" ), IECore.M44f.createTranslated( IECore.V3f( 3, time, 0 ) ) )

				mesh = scene.object( "/1/2" )
				self.assertEqual( mesh["Cd"].data, IECore.V3fVectorData( [ IECore.V3f( time, 1, 0 ) ] * 6 ) )

	def testEnabled( self ) :

		sc = IECore.SceneCache( self.__testFile, IECore.IndexedIO.OpenMode.Write )

		t = sc.createChild( "transform" )
		t.writeTransform( IECore.M44dData( IECore.M44d.createTranslated( IECore.V3d( 1, 0, 0 ) ) ), 0.0 )

		s = t.createChild( "shape" )
		s.writeObject( IECore.SpherePrimitive( 10 ), 0.0 )

		del sc, t, s

		reader = GafferScene.SceneReader()
		reader["fileName"].setValue( self.__testFile )

		# we have to remember to set the refresh counts to different values in different tests, otherwise
		# it thinks it's reading an old file...
		reader["refreshCount"].setValue( self.uniqueInt( self.__testFile ) )

		self.assertSceneValid( reader["out"] )
		self.assertEqual( reader["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "transform" ] ) )

		reader["enabled"].setValue( False )
		self.assertSceneValid( reader["out"] )
		self.assertTrue( reader["out"].bound( "/" ).isEmpty() )
		self.assertEqual( reader["out"].childNames( "/" ), IECore.InternedStringVectorData() )

	def testEmptyFileName( self ) :

		s = GafferScene.SceneReader()

		self.assertSceneValid( s["out"] )
		self.assertEqual( s["out"].childNames( "/" ), IECore.InternedStringVectorData() )
		self.assertEqual( s["out"].bound( "/" ), IECore.Box3f() )
		self.assertEqual( s["out"].transform( "/" ), IECore.M44f() )
		self.assertEqual( s["out"].attributes( "/" ), IECore.CompoundObject() )
		self.assertEqual( s["out"].object( "/" ), IECore.NullObject() )

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
		s["refreshCount"].setValue( self.uniqueInt( "/tmp/test.scc" ) ) # account for our changing of file contents between tests

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

	def testChildNamesHash( self ) :

		s = IECore.SceneCache( "/tmp/test.scc", IECore.IndexedIO.OpenMode.Write )
		sphereGroup = s.createChild( "sphereGroup" )
		sphereGroup.writeTransform( IECore.M44dData( IECore.M44d.createTranslated( IECore.V3d( 1, 0, 0 ) ) ), 0.0 )
		sphereGroup.writeTransform( IECore.M44dData( IECore.M44d.createTranslated( IECore.V3d( 2, 0, 0 ) ) ), 1.0 )
		sphere = sphereGroup.createChild( "sphere" )
		sphere.writeObject( IECore.SpherePrimitive(), 0 )

		del s, sphereGroup, sphere

		s = GafferScene.SceneReader()
		s["fileName"].setValue( "/tmp/test.scc" )
		s["refreshCount"].setValue( self.uniqueInt( "/tmp/test.scc" ) ) # account for our changing of file contents between tests

		t = GafferScene.SceneTimeWarp()
		t["in"].setInput( s["out"] )
		t["offset"].setValue( 1 )

		self.assertSceneHashesEqual(
			s["out"], t["out"],
			childPlugNames = [ "childNames" ]
		)

	def testStaticHashes( self ) :

		s = IECore.SceneCache( "/tmp/test.scc", IECore.IndexedIO.OpenMode.Write )

		movingGroup = s.createChild( "movingGroup" )
		movingGroup.writeTransform( IECore.M44dData( IECore.M44d.createTranslated( IECore.V3d( 1, 0, 0 ) ) ), 0.0 )
		movingGroup.writeTransform( IECore.M44dData( IECore.M44d.createTranslated( IECore.V3d( 2, 0, 0 ) ) ), 1.0 )

		deformingSphere = movingGroup.createChild( "deformingSphere" )
		deformingSphere.writeObject( IECore.SpherePrimitive(), 0 )
		deformingSphere.writeObject( IECore.SpherePrimitive( 2 ), 1 )

		staticGroup = s.createChild( "staticGroup" )
		staticGroup.writeTransform( IECore.M44dData( IECore.M44d.createTranslated( IECore.V3d( 1, 0, 0 ) ) ), 0.0 )

		staticSphere = staticGroup.createChild( "staticSphere" )
		staticSphere.writeObject( IECore.SpherePrimitive(), 0 )

		del s, movingGroup, deformingSphere, staticGroup, staticSphere

		s = GafferScene.SceneReader()
		s["fileName"].setValue( "/tmp/test.scc" )
		s["refreshCount"].setValue( self.uniqueInt( "/tmp/test.scc" ) ) # account for our changing of file contents between tests

		t = GafferScene.SceneTimeWarp()
		t["in"].setInput( s["out"] )
		t["offset"].setValue( 1 )

		self.assertPathHashesNotEqual(
			s["out"], "/movingGroup",
			t["out"], "/movingGroup",
			childPlugNames = [ "transform", "bound" ]
		)

		self.assertPathHashesNotEqual(
			s["out"], "/movingGroup/deformingSphere",
			t["out"], "/movingGroup/deformingSphere",
			childPlugNames = [ "bound", "object" ]
		)

		self.assertPathHashesEqual(
			s["out"], "/movingGroup",
			t["out"], "/movingGroup",
			childPlugNames = [ "attributes", "object" ]
		)

		self.assertPathHashesEqual(
			s["out"], "/movingGroup/deformingSphere",
			t["out"], "/movingGroup/deformingSphere",
			childPlugNames = [ "attributes" ]
		)

		self.assertPathHashesEqual(
			s["out"], "/staticGroup",
			t["out"], "/staticGroup",
			childPlugNames = [ "object", "transform", "attributes", "bound" ]
		)

		self.assertPathHashesEqual(
			s["out"], "/staticGroup/staticSphere",
			t["out"], "/staticGroup/staticSphere",
			childPlugNames = [ "object", "transform", "attributes", "bound" ]
		)

	def testTagFilteringWholeScene( self ) :

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

		# these are all loading everything, although each with
		# different filters.

		refreshCount = self.uniqueInt( "/tmp/test.scc" )

		s1 = GafferScene.SceneReader()
		s1["fileName"].setValue( "/tmp/test.scc" )
		s1["refreshCount"].setValue( refreshCount )

		s2 = GafferScene.SceneReader()
		s2["fileName"].setValue( "/tmp/test.scc" )
		s2["refreshCount"].setValue( refreshCount )
		s2["tags"].setValue( "chrome wood" )

		s3 = GafferScene.SceneReader()
		s3["fileName"].setValue( "/tmp/test.scc" )
		s3["refreshCount"].setValue( refreshCount )
		s3["tags"].setValue( "chrome something" )

		# so the resulting scenes should be equal

		self.assertScenesEqual( s1["out"], s2["out"] )
		self.assertScenesEqual( s2["out"], s3["out"] )

		# as should be the hashes, except for childNames

		self.assertSceneHashesEqual( s1["out"], s2["out"], childPlugNamesToIgnore = ( "childNames", ) )
		self.assertSceneHashesEqual( s2["out"], s3["out"], childPlugNamesToIgnore = ( "childNames", ) )

	def testTagFilteringPartialScene( self ) :

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

		refreshCount = self.uniqueInt( "/tmp/test.scc" )

		# this one will load everything

		s1 = GafferScene.SceneReader()
		s1["fileName"].setValue( "/tmp/test.scc" )
		s1["refreshCount"].setValue( refreshCount )

		# this one should load just the sphere

		s2 = GafferScene.SceneReader()
		s2["fileName"].setValue( "/tmp/test.scc" )
		s2["refreshCount"].setValue( refreshCount )
		s2["tags"].setValue( "chrome" )

		# this one should load just the plane

		s3 = GafferScene.SceneReader()
		s3["fileName"].setValue( "/tmp/test.scc" )
		s3["refreshCount"].setValue( refreshCount )
		s3["tags"].setValue( "wood" )

		# check childnames

		self.assertEqual( set( [ str( x ) for x in s1["out"].childNames( "/" ) ] ), set( [ "sphereGroup", "planeGroup" ] ) )
		self.assertEqual( set( [ str( x ) for x in s2["out"].childNames( "/" ) ] ), set( [ "sphereGroup" ] ) )
		self.assertEqual( set( [ str( x ) for x in s3["out"].childNames( "/" ) ] ), set( [ "planeGroup" ] ) )

		self.assertEqual( set( [ str( x ) for x in s1["out"].childNames( "/sphereGroup" ) ] ), set( [ "sphere" ] ) )
		self.assertEqual( set( [ str( x ) for x in s2["out"].childNames( "/sphereGroup" ) ] ), set( [ "sphere" ] ) )

		self.assertEqual( set( [ str( x ) for x in s1["out"].childNames( "/planeGroup" ) ] ), set( [ "plane" ] ) )
		self.assertEqual( set( [ str( x ) for x in s3["out"].childNames( "/planeGroup" ) ] ), set( [ "plane" ] ) )

		# check equality of the locations which are preserved

		self.assertPathsEqual( s1["out"], "/", s2["out"], "/", childPlugNamesToIgnore = ( "childNames", ) )
		self.assertPathsEqual( s1["out"], "/", s3["out"], "/", childPlugNamesToIgnore = ( "childNames", ) )

		self.assertPathsEqual( s1["out"], "/sphereGroup/sphere", s2["out"], "/sphereGroup/sphere", childPlugNamesToIgnore = ( "childNames", ) )
		self.assertPathsEqual( s1["out"], "/sphereGroup/sphere", s2["out"], "/sphereGroup/sphere", childPlugNamesToIgnore = ( "childNames", ) )

		self.assertPathsEqual( s1["out"], "/planeGroup/plane", s3["out"], "/planeGroup/plane", childPlugNamesToIgnore = ( "childNames", ) )
		self.assertPathsEqual( s1["out"], "/planeGroup/plane", s3["out"], "/planeGroup/plane", childPlugNamesToIgnore = ( "childNames", ) )

	def testSupportedExtensions( self ) :

		e = GafferScene.SceneReader.supportedExtensions()
		self.assertTrue( "scc" in e )
		self.assertTrue( "lscc" in e )

	def testTagsAsSets( self ) :

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
		s["refreshCount"].setValue( self.uniqueInt( "/tmp/test.scc" ) ) # account for our changing of file contents between tests

		sets = s["out"]["globals"].getValue()["gaffer:sets"]
		self.assertEqual( sets.keys(), [] )

		s["sets"].setValue( "chrome" )
		sets = s["out"]["globals"].getValue()["gaffer:sets"]
		self.assertEqual( len( sets ), 1 )
		self.assertEqual( sets.keys(), [ "chrome" ] )
		self.assertEqual( sets["chrome"].value.paths(), [ "/sphereGroup" ] )

		s["sets"].setValue( "wood" )
		sets = s["out"]["globals"].getValue()["gaffer:sets"]
		self.assertEqual( len( sets ), 1 )
		self.assertEqual( sets.keys(), [ "wood" ] )
		self.assertEqual( sets["wood"].value.paths(), [ "/planeGroup/plane" ] )

		s["sets"].setValue( "*e*" )
		sets = s["out"]["globals"].getValue()["gaffer:sets"]
		# we can't simply assert that we have only "something" and "chrome" because the pesky
		# SceneCache inserts tags of its own behind our backs, and our wildcards might match them.
		self.assertTrue( set( sets.keys() ).issuperset( set( [ "something", "chrome" ] ) ) )
		self.assertTrue( "wood" not in sets )
		self.assertEqual( sets["chrome"].value.paths(), [ "/sphereGroup" ] )
		self.assertEqual( sets["something"].value.paths(), [ "/planeGroup/plane" ] )

		s["sets"].setValue( "wood *e*" )
		sets = s["out"]["globals"].getValue()["gaffer:sets"]
		self.assertTrue( set( sets.keys() ).issuperset( set( [ "wood", "something", "chrome" ] ) ) )
		self.assertEqual( sets["chrome"].value.paths(), [ "/sphereGroup" ] )
		self.assertEqual( sets["wood"].value.paths(), [ "/planeGroup/plane" ] )
		self.assertEqual( sets["something"].value.paths(), [ "/planeGroup/plane" ] )

	def tearDown( self ) :

		if os.path.exists( self.__testFile ) :
			os.remove( self.__testFile )

if __name__ == "__main__":
	unittest.main()
