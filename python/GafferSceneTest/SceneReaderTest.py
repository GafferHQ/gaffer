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

import pathlib
import unittest
import inspect
import imath

import IECore
import IECoreScene

import Gaffer
import GafferScene
import GafferSceneTest

class SceneReaderTest( GafferSceneTest.SceneTestCase ) :

	def setUp( self ) :

		GafferSceneTest.SceneTestCase.setUp( self )

		self.__testFile = self.temporaryDirectory() / "test.scc"

	def testFileRefreshProblem( self ) :

		sc = IECoreScene.SceneCache( str( self.__testFile ), IECore.IndexedIO.OpenMode.Write )

		t = sc.createChild( "1" )
		t.writeTransform( IECore.M44dData( imath.M44d().translate( imath.V3d( 1, 0, 0 ) ) ), 0.0 )

		s = t.createChild( "2" )
		s.writeObject( IECoreScene.SpherePrimitive( 10 ), 0.0 )

		del sc, t, s

		reader = GafferScene.SceneReader()
		reader["fileName"].setValue( self.__testFile )
		reader["refreshCount"].setValue( self.uniqueInt( self.__testFile ) )

		scene = reader["out"]
		self.assertEqual( scene.childNames( "/" ), IECore.InternedStringVectorData( [ "1" ] ) )

		del scene

		sc = IECoreScene.SceneCache( str( self.__testFile ), IECore.IndexedIO.OpenMode.Write )

		t = sc.createChild( "transform" )
		t.writeTransform( IECore.M44dData( imath.M44d().translate( imath.V3d( 1, 0, 0 ) ) ), 0.0 )

		s = t.createChild( "shape" )
		s.writeObject( IECoreScene.SpherePrimitive( 10 ), 0.0 )

		del sc, t, s

		# we have to remember to set the refresh counts to different values in different tests, otherwise
		# it thinks it's reading an old file...
		reader = GafferScene.SceneReader()
		reader["fileName"].setValue( self.__testFile )
		reader["refreshCount"].setValue( self.uniqueInt( self.__testFile ) )

		scene = reader["out"]
		self.assertEqual( scene.childNames( "/" ), IECore.InternedStringVectorData( [ "transform" ] ) )

	def testRead( self ) :

		sc = IECoreScene.SceneCache( str( self.__testFile ), IECore.IndexedIO.OpenMode.Write )

		t = sc.createChild( "transform" )
		t.writeTransform( IECore.M44dData( imath.M44d().translate( imath.V3d( 1, 0, 0 ) ) ), 0.0 )

		s = t.createChild( "shape" )
		s.writeObject( IECoreScene.SpherePrimitive( 10 ), 0.0 )

		del sc, t, s

		reader = GafferScene.SceneReader()
		reader["fileName"].setValue( self.__testFile )

		# we have to remember to set the refresh counts to different values in different tests, otherwise
		# it thinks it's reading an old file...
		reader["refreshCount"].setValue( self.uniqueInt( self.__testFile ) )

		scene = reader["out"]
		self.assertSceneValid( scene )

		self.assertEqual( scene.transform( "transform" ), imath.M44f().translate( imath.V3f( 1, 0, 0 ) ) )
		self.assertEqual( scene.object( "transform/shape" ), IECoreScene.SpherePrimitive( 10 ) )

	def writeAnimatedSCC( self ) :

		scene = IECoreScene.SceneCache( str( self.__testFile ), IECore.IndexedIO.OpenMode.Write )

		time = 0
		sc1 = scene.createChild( str( 1 ) )
		mesh = IECoreScene.MeshPrimitive.createBox(imath.Box3f(imath.V3f(0),imath.V3f(1)))
		mesh["Cd"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Uniform, IECore.V3fVectorData( [ imath.V3f( 1, 0, 0 ) ] * 6 ) )
		sc1.writeObject( mesh, time )
		sc1.writeTransform( IECore.M44dData(), time )

		sc2 = sc1.createChild( str( 2 ) )
		mesh = IECoreScene.MeshPrimitive.createBox(imath.Box3f(imath.V3f(0),imath.V3f(1)))
		mesh["Cd"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Uniform, IECore.V3fVectorData( [ imath.V3f( 0, 1, 0 ) ] * 6 ) )
		sc2.writeObject( mesh, time )
		sc2.writeTransform( IECore.M44dData(), time )

		sc3 = sc2.createChild( str( 3 ) )
		mesh = IECoreScene.MeshPrimitive.createBox(imath.Box3f(imath.V3f(0),imath.V3f(1)))
		mesh["Cd"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Uniform, IECore.V3fVectorData( [ imath.V3f( 0, 0, 1 ) ] * 6 ) )
		sc3.writeObject( mesh, time )
		sc3.writeTransform( IECore.M44dData(), time )

		for frame in [ 0.5, 1, 1.5, 2, 5, 10 ] :

			matrix = imath.M44d().translate( imath.V3d( 1, frame, 0 ) )
			sc1.writeTransform( IECore.M44dData( matrix ), float( frame ) / 24 )

			mesh["Cd"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Uniform, IECore.V3fVectorData( [ imath.V3f( frame, 1, 0 ) ] * 6 ) )
			sc2.writeObject( mesh, float( frame ) / 24 )
			matrix = imath.M44d().translate( imath.V3d( 2, frame, 0 ) )
			sc2.writeTransform( IECore.M44dData( matrix ), float( frame ) / 24 )

			matrix = imath.M44d().translate( imath.V3d( 3, frame, 0 ) )
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
			self.assertEqual( scene.transform( "/1" ), imath.M44f() )
			self.assertEqual( scene.transform( "/1/2" ), imath.M44f() )
			self.assertEqual( scene.transform( "/1/2/3" ), imath.M44f() )

		for time in [ 0.5, 1, 1.5, 2, 5, 10 ] :

			context.setFrame( time )

			with context:
				self.assertEqual( scene.transform( "/1" ), imath.M44f().translate( imath.V3f( 1, time, 0 ) ) )
				self.assertEqual( scene.transform( "/1/2" ), imath.M44f().translate( imath.V3f( 2, time, 0 ) ) )
				self.assertEqual( scene.transform( "/1/2/3" ), imath.M44f().translate( imath.V3f( 3, time, 0 ) ) )

				mesh = scene.object( "/1/2" )
				self.assertEqual( mesh["Cd"].data, IECore.V3fVectorData( [ imath.V3f( time, 1, 0 ) ] * 6 ) )

	def testEnabled( self ) :

		sc = IECoreScene.SceneCache( str( self.__testFile ), IECore.IndexedIO.OpenMode.Write )

		t = sc.createChild( "transform" )
		t.writeTransform( IECore.M44dData( imath.M44d().translate( imath.V3d( 1, 0, 0 ) ) ), 0.0 )

		s = t.createChild( "shape" )
		s.writeObject( IECoreScene.SpherePrimitive( 10 ), 0.0 )

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
		self.assertEqual( s["out"].bound( "/" ), imath.Box3f() )
		self.assertEqual( s["out"].transform( "/" ), imath.M44f() )
		self.assertEqual( s["out"].attributes( "/" ), IECore.CompoundObject() )
		self.assertEqual( s["out"].object( "/" ), IECore.NullObject() )

	def testChildNamesHash( self ) :

		filePath = self.temporaryDirectory() / "test.scc"
		s = IECoreScene.SceneCache( str( filePath ), IECore.IndexedIO.OpenMode.Write )
		sphereGroup = s.createChild( "sphereGroup" )
		sphereGroup.writeTransform( IECore.M44dData( imath.M44d().translate( imath.V3d( 1, 0, 0 ) ) ), 0.0 )
		sphereGroup.writeTransform( IECore.M44dData( imath.M44d().translate( imath.V3d( 2, 0, 0 ) ) ), 1.0 )
		sphere = sphereGroup.createChild( "sphere" )
		sphere.writeObject( IECoreScene.SpherePrimitive(), 0 )

		del s, sphereGroup, sphere

		s = GafferScene.SceneReader()
		s["fileName"].setValue( filePath )
		s["refreshCount"].setValue( self.uniqueInt( filePath ) ) # account for our changing of file contents between tests

		t = Gaffer.TimeWarp()
		t.setup( GafferScene.ScenePlug() )
		t["in"].setInput( s["out"] )
		t["offset"].setValue( 1 )

		self.assertSceneHashesEqual(
			s["out"], t["out"],
			checks = { "childNames" }
		)

	def testStaticHashes( self ) :

		filePath = self.temporaryDirectory() / "test.scc"
		s = IECoreScene.SceneCache( str( filePath ), IECore.IndexedIO.OpenMode.Write )

		movingGroup = s.createChild( "movingGroup" )
		movingGroup.writeTransform( IECore.M44dData( imath.M44d().translate( imath.V3d( 1, 0, 0 ) ) ), 0.0 )
		movingGroup.writeTransform( IECore.M44dData( imath.M44d().translate( imath.V3d( 2, 0, 0 ) ) ), 1.0 )

		deformingSphere = movingGroup.createChild( "deformingSphere" )
		deformingSphere.writeObject( IECoreScene.SpherePrimitive(), 0 )
		deformingSphere.writeObject( IECoreScene.SpherePrimitive( 2 ), 1 )

		staticGroup = s.createChild( "staticGroup" )
		staticGroup.writeTransform( IECore.M44dData( imath.M44d().translate( imath.V3d( 1, 0, 0 ) ) ), 0.0 )

		staticSphere = staticGroup.createChild( "staticSphere" )
		staticSphere.writeObject( IECoreScene.SpherePrimitive(), 0 )

		del s, movingGroup, deformingSphere, staticGroup, staticSphere

		s = GafferScene.SceneReader()
		s["fileName"].setValue( filePath )
		s["refreshCount"].setValue( self.uniqueInt( filePath ) ) # account for our changing of file contents between tests

		t = Gaffer.TimeWarp()
		t.setup( GafferScene.ScenePlug() )
		t["in"].setInput( s["out"] )
		t["offset"].setValue( 1 )

		self.assertPathHashesNotEqual(
			s["out"], "/movingGroup",
			t["out"], "/movingGroup",
			checks = { "transform", "bound" }
		)

		self.assertPathHashesNotEqual(
			s["out"], "/movingGroup/deformingSphere",
			t["out"], "/movingGroup/deformingSphere",
			checks = { "bound", "object" }
		)

		self.assertPathHashesEqual(
			s["out"], "/movingGroup",
			t["out"], "/movingGroup",
			checks = { "attributes", "object" }
		)

		self.assertPathHashesEqual(
			s["out"], "/movingGroup/deformingSphere",
			t["out"], "/movingGroup/deformingSphere",
			checks = { "attributes" }
		)

		self.assertPathHashesEqual(
			s["out"], "/staticGroup",
			t["out"], "/staticGroup",
			checks = { "object", "transform", "attributes", "bound" }
		)

		self.assertPathHashesEqual(
			s["out"], "/staticGroup/staticSphere",
			t["out"], "/staticGroup/staticSphere",
			checks = { "object", "transform", "attributes", "bound" }
		)

	def testTagFilteringWholeScene( self ) :

		filePath = self.temporaryDirectory() / "test.scc"
		s = IECoreScene.SceneCache( str( filePath ), IECore.IndexedIO.OpenMode.Write )

		sphereGroup = s.createChild( "sphereGroup" )
		sphereGroup.writeTags( [ "chrome" ] )
		sphere = sphereGroup.createChild( "sphere" )
		sphere.writeObject( IECoreScene.SpherePrimitive(), 0 )

		planeGroup = s.createChild( "planeGroup" )
		plane = planeGroup.createChild( "plane" )
		plane.writeTags( [ "wood", "something" ] )
		plane.writeObject( IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) ), 0 )

		del s, sphereGroup, sphere, planeGroup, plane

		# these are all loading everything, although each with
		# different filters.

		refreshCount = self.uniqueInt( filePath )

		s1 = GafferScene.SceneReader()
		s1["fileName"].setValue( filePath )
		s1["refreshCount"].setValue( refreshCount )

		s2 = GafferScene.SceneReader()
		s2["fileName"].setValue( filePath )
		s2["refreshCount"].setValue( refreshCount )
		s2["tags"].setValue( "chrome wood" )

		s3 = GafferScene.SceneReader()
		s3["fileName"].setValue( filePath )
		s3["refreshCount"].setValue( refreshCount )
		s3["tags"].setValue( "chrome something" )

		# so the resulting scenes should be equal

		self.assertScenesEqual( s1["out"], s2["out"] )
		self.assertScenesEqual( s2["out"], s3["out"] )

		# as should be the hashes, except for childNames

		self.assertSceneHashesEqual( s1["out"], s2["out"], checks = self.allPathChecks - { "childNames" } )
		self.assertSceneHashesEqual( s2["out"], s3["out"], checks = self.allPathChecks - { "childNames" } )

	def testTagFilteringPartialScene( self ) :

		filePath = self.temporaryDirectory() / "test.scc"
		s = IECoreScene.SceneCache( str( filePath ), IECore.IndexedIO.OpenMode.Write )

		sphereGroup = s.createChild( "sphereGroup" )
		sphereGroup.writeTags( [ "chrome" ] )
		sphere = sphereGroup.createChild( "sphere" )
		sphere.writeObject( IECoreScene.SpherePrimitive(), 0 )

		planeGroup = s.createChild( "planeGroup" )
		plane = planeGroup.createChild( "plane" )
		plane.writeTags( [ "wood", "something" ] )
		plane.writeObject( IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) ), 0 )

		del s, sphereGroup, sphere, planeGroup, plane

		refreshCount = self.uniqueInt( filePath )

		# this one will load everything

		s1 = GafferScene.SceneReader()
		s1["fileName"].setValue( filePath )
		s1["refreshCount"].setValue( refreshCount )

		# this one should load just the sphere

		s2 = GafferScene.SceneReader()
		s2["fileName"].setValue( filePath )
		s2["refreshCount"].setValue( refreshCount )
		s2["tags"].setValue( "chrome" )

		# this one should load just the plane

		s3 = GafferScene.SceneReader()
		s3["fileName"].setValue( filePath )
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

		self.assertPathsEqual( s1["out"], "/", s2["out"], "/", checks = self.allPathChecks - { "childNames" } )
		self.assertPathsEqual( s1["out"], "/", s3["out"], "/", checks = self.allPathChecks - { "childNames" } )

		self.assertPathsEqual( s1["out"], "/sphereGroup/sphere", s2["out"], "/sphereGroup/sphere", checks = self.allPathChecks - { "childNames" } )
		self.assertPathsEqual( s1["out"], "/sphereGroup/sphere", s2["out"], "/sphereGroup/sphere", checks = self.allPathChecks - { "childNames" } )

		self.assertPathsEqual( s1["out"], "/planeGroup/plane", s3["out"], "/planeGroup/plane", checks = self.allPathChecks - { "childNames" } )
		self.assertPathsEqual( s1["out"], "/planeGroup/plane", s3["out"], "/planeGroup/plane", checks = self.allPathChecks - { "childNames" } )

	def testSupportedExtensions( self ) :

		e = GafferScene.SceneReader.supportedExtensions()
		self.assertTrue( "scc" in e )
		self.assertTrue( "lscc" in e )

	def testTagsAsSets( self ) :

		filePath = self.temporaryDirectory() / "test.scc"
		s = IECoreScene.SceneCache( str( filePath ), IECore.IndexedIO.OpenMode.Write )

		sphereGroup = s.createChild( "sphereGroup" )
		sphereGroup.writeTags( [ "chrome" ] )
		sphere = sphereGroup.createChild( "sphere" )
		sphere.writeObject( IECoreScene.SpherePrimitive(), 0 )

		planeGroup = s.createChild( "planeGroup" )
		plane = planeGroup.createChild( "plane" )
		plane.writeTags( [ "wood", "something" ] )
		plane.writeObject( IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) ), 0 )

		del s, sphereGroup, sphere, planeGroup, plane

		s = GafferScene.SceneReader()
		s["fileName"].setValue( filePath )
		s["refreshCount"].setValue( self.uniqueInt( filePath ) ) # account for our changing of file contents between tests

		self.assertEqual(
			set( [ str( ss ) for ss in s["out"]["setNames"].getValue() ] ),
			set( [ "ObjectType:SpherePrimitive", "wood", "chrome", "ObjectType:MeshPrimitive", "something" ] )
		)

		self.assertEqual( s["out"].set( "chrome" ).value.paths(), [ "/sphereGroup" ] )
		self.assertEqual( s["out"].set( "wood" ).value.paths(), [ "/planeGroup/plane" ] )
		self.assertEqual( s["out"].set( "something" ).value.paths(), [ "/planeGroup/plane" ] )
		self.assertEqual( s["out"].set( "ObjectType:SpherePrimitive" ).value.paths(), [ "/sphereGroup/sphere" ] )
		self.assertEqual( s["out"].set( "ObjectType:MeshPrimitive" ).value.paths(), [ "/planeGroup/plane" ] )

	def testInvalidFiles( self ) :

		reader = GafferScene.SceneReader()
		reader["fileName"].setValue( "iDontExist.scc" )

		for i in range( 0, 10 ) :
			self.assertRaises( RuntimeError, GafferSceneTest.traverseScene, reader["out"] )

	def testInvalidPaths( self ) :

		self.writeAnimatedSCC()

		reader = GafferScene.SceneReader()
		reader["fileName"].setValue( self.__testFile )
		reader["refreshCount"].setValue( self.uniqueInt( self.__testFile ) )

		for i in range( 0, 10 ) :
			self.assertRaises( RuntimeError, reader["out"].object, "/this/object/does/not/exist" )

	def testGlobals( self ) :

		self.writeAnimatedSCC()

		r1 = GafferScene.SceneReader()

		r2 = GafferScene.SceneReader()
		r2["fileName"].setValue( self.__testFile )
		r2["refreshCount"].setValue( self.uniqueInt( self.__testFile ) )

		# Because globals aren't implemented, the globals should be the exact same
		# across all SceneReaders.
		self.assertEqual( r1["out"]["globals"].hash(), r2["out"]["globals"].hash() )
		self.assertEqual( r1["out"]["globals"].getValue(), IECore.CompoundObject() )
		self.assertTrue( r1["out"]["globals"].getValue( _copy = False ).isSame( r2["out"]["globals"].getValue( _copy = False ) ) )

	def testComputeSetInEmptyScene( self ) :

		# this used to cause a crash:
		r1 = GafferScene.SceneReader()
		self.assertEqual( r1["out"].set( "blahblah" ).value.paths(), [] )

	def testAlembic( self ) :

		r = GafferScene.SceneReader()
		r["fileName"].setValue( pathlib.Path( __file__ ).parent / "alembicFiles" / "cube.abc" )
		self.assertSceneValid( r["out"] )

	def testTransform( self ) :

		r = GafferScene.SceneReader()
		r["fileName"].setValue( pathlib.Path( __file__ ).parent / "alembicFiles" / "groupedPlane.abc" )
		self.assertEqual( r["out"].transform( "/group" ), imath.M44f() )

		r["transform"]["translate"].setValue( imath.V3f( 1, 2, 3 ) )
		self.assertEqual( r["out"].transform( "/group" ), r["transform"].matrix() )
		self.assertSceneValid( r["out"] )

	def testAlembicThreading( self ) :

		mesh = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) )
		filePath = self.temporaryDirectory() / "test.abc"

		root = IECoreScene.SceneInterface.create( str( filePath ), IECore.IndexedIO.OpenMode.Write )
		root.writeBound( imath.Box3d( mesh.bound() ), 0 )
		for i in range( 0, 1000 ) :
			child = root.createChild( str( i ) )
			child.writeObject( mesh, 0 )
			child.writeBound( imath.Box3d( mesh.bound() ), 0 )

		del root, child

		sceneReader = GafferScene.SceneReader()
		sceneReader["fileName"].setValue( filePath )

		for i in range( 0, 20 ) :
			sceneReader["refreshCount"].setValue( sceneReader["refreshCount"].getValue() + 1 )
			GafferSceneTest.traverseScene( sceneReader["out"] )

	def testGlobalHashesUseFileNameValue( self ) :

		# This models a situation where a complex asset-managed reader uses a
		# fileName expression which depends on the frame only in specific
		# circumstances. In the cases that it doesn't actually use the frame in
		# computing the filename, we want that to be reflected in the hash for
		# global scene properties, so that we don't do unnecessary recomputation
		# from frame to frame.

		script = Gaffer.ScriptNode()
		script["reader"] = GafferScene.SceneReader()

		script["expression"] = Gaffer.Expression()
		script["expression"].setExpression( inspect.cleandoc(
			"""
			frame = context.getFrame()
			if False :
				parent["reader"]["fileName"] = "test.{}.abc".format( int( frame ) )
			else :
				parent["reader"]["fileName"] = "test.abc"
			"""
		) )

		with Gaffer.Context() as c :

			c.setFrame( 1 )
			globalsHash = script["reader"]["out"].globalsHash()
			setNamesHash = script["reader"]["out"].setNamesHash()
			setHash = script["reader"]["out"].setHash( "test" )

			c.setFrame( 2 )
			self.assertEqual(
				script["reader"]["out"].globalsHash(),
				globalsHash
			)
			self.assertEqual(
				script["reader"]["out"].setNamesHash(),
				setNamesHash
			)
			self.assertEqual(
				script["reader"]["out"].setHash( "test" ),
				setHash
			)

	def testNullAttributes( self ) :

		s = GafferScene.SceneReader()
		s["fileName"].setValue( "${GAFFER_ROOT}/python/GafferSceneTest/usdFiles/unsupportedAttribute.usda" )

		# At the time of writing, `IECoreUSD` advertises custom attributes via
		# `USDScene::attributeNames()` even if it can't load them, and then it
		# returns `nullptr` from `USDScene::readAttribute()`. Make sure we are
		# robust to this.

		with IECore.CapturingMessageHandler() as mh :
			attributes = s["out"].attributes( "/sphere" )

		self.assertEqual( len( attributes ), 0 )
		self.assertEqual( len( mh.messages ), 1 )
		self.assertEqual( mh.messages[0].level, IECore.Msg.Level.Warning )
		self.assertEqual( mh.messages[0].message, 'Failed to load attribute "test:double4" at location "/sphere"' )

	def testImplicitUSDDefaultLights( self ) :

		reader = GafferScene.SceneReader()
		reader["fileName"].setValue( "${GAFFER_ROOT}/python/GafferSceneTest/usdFiles/sphereLight.usda" )

		self.assertIn( "defaultLights", reader["out"].setNames() )
		self.assertEqual( reader["out"].set( "defaultLights" ).value, IECore.PathMatcher( [ "/SpotLight23" ] ) )

	def testExplicitUSDDefaultLights( self ) :

		light1 = GafferSceneTest.TestLight()
		light1["name"].setValue( "light1" )
		light1["defaultLight"].setValue( False )

		light2 = GafferSceneTest.TestLight()
		light2["name"].setValue( "light2" )

		group = GafferScene.Group()
		group["in"][0].setInput( light1["out"] )
		group["in"][1].setInput( light2["out"] )

		writer = GafferScene.SceneWriter()
		writer["in"].setInput( group["out"] )
		writer["fileName"].setValue( self.temporaryDirectory() / "test.usda" )
		writer["task"].execute()

		reader = GafferScene.SceneReader()
		reader["fileName"].setInput( writer["fileName"] )

		self.assertIn( "defaultLights", reader["out"].setNames() )
		self.assertEqual( reader["out"].set( "defaultLights" ).value, IECore.PathMatcher( [ "/group/light2" ] ) )

	def testReadSets( self ) :

		plane = GafferScene.Plane()
		plane["sets"].setValue( "A B C" )

		sphere = GafferScene.Sphere()
		sphere["sets"].setValue( "B C D" )

		group = GafferScene.Group()
		group["in"][0].setInput( plane["out"] )
		group["in"][1].setInput( sphere["out"] )

		writer = GafferScene.SceneWriter()
		writer["in"].setInput( group["out"] )

		reader = GafferScene.SceneReader()
		reader["fileName"].setInput( writer["fileName"] )

		for extension in IECoreScene.SceneInterface.supportedExtensions() :

			if extension in { "abc", "usdz", "vdb" } :
				# - `IECoreAlembic::AlembicScene::writeSet()` hasn't been implemented properly for
				#   the root item yet.
				# - `IECoreUSD::USDScene` can read `usdz`, but not write it.
				# - `IECoreVDB::VDBScene` hasn't implemented sets or tags at all.
				continue

			writer["fileName"].setValue( self.temporaryDirectory() / f"test.{extension}" )
			writer["task"].execute()

			for setName in writer["in"].setNames() :
				self.assertIn( setName, reader["out"].setNames() )
				self.assertEqual( reader["out"].set( setName ), writer["in"].set( setName ) )

if __name__ == "__main__":
	unittest.main()
