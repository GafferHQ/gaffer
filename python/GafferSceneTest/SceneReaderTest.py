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

import os
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
	
		if os.path.exists( "/tmp/test.scc" ) :
			os.remove( "/tmp/test.scc" )
		
if __name__ == "__main__":
	unittest.main()
