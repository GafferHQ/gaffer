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
import threading
import gc

import IECore

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest

class GroupTest( GafferSceneTest.SceneTestCase ) :

	def testTwoLevels( self ) :

		sphere = IECore.SpherePrimitive()
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

		group = GafferScene.Group()
		group["in"].setInput( input["out"] )
		group["name"].setValue( "topLevel" )

		self.assertEqual( group["name"].getValue(), "topLevel" )

		self.assertEqual( group["out"].object( "/" ), IECore.NullObject() )
		self.assertEqual( group["out"].transform( "/" ), IECore.M44f() )
		self.assertEqual( group["out"].bound( "/" ), sphere.bound() )
		self.assertEqual( group["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "topLevel" ] ) )

		self.assertEqual( group["out"].object( "/topLevel" ), IECore.NullObject() )
		self.assertEqual( group["out"].transform( "/topLevel" ), IECore.M44f() )
		self.assertEqual( group["out"].bound( "/topLevel" ), sphere.bound() )
		self.assertEqual( group["out"].childNames( "/topLevel" ), IECore.InternedStringVectorData( [ "group" ] ) )

		self.assertEqual( group["out"].object( "/topLevel/group" ), IECore.NullObject() )
		self.assertEqual( group["out"].transform( "/topLevel/group" ), IECore.M44f() )
		self.assertEqual( group["out"].bound( "/topLevel/group" ), sphere.bound() )
		self.assertEqual( group["out"].childNames( "/topLevel/group" ), IECore.InternedStringVectorData( [ "sphere" ] ) )

		self.assertEqual( group["out"].object( "/topLevel/group/sphere" ), sphere )
		self.assertEqual( group["out"].transform( "/topLevel/group/sphere" ), IECore.M44f() )
		self.assertEqual( group["out"].bound( "/topLevel/group/sphere" ), sphere.bound() )
		self.assertEqual( group["out"].childNames( "/topLevel/group/sphere" ), IECore.InternedStringVectorData() )

	def testTransform( self ) :

		sphere = IECore.SpherePrimitive()
		originalRootBound = sphere.bound()
		originalRootBound.min += IECore.V3f( 1, 0, 0 )
		originalRootBound.max += IECore.V3f( 1, 0, 0 )
		input = GafferSceneTest.CompoundObjectSource()
		input["in"].setValue(
			IECore.CompoundObject( {
				"bound" : IECore.Box3fData( originalRootBound ),
				"children" : {
					"sphere" : {
						"object" : sphere,
						"bound" : IECore.Box3fData( sphere.bound() ),
						"transform" : IECore.M44fData( IECore.M44f.createTranslated( IECore.V3f( 1, 0, 0 ) ) ),
					}
				}
			} )
		)

		group = GafferScene.Group()
		group["in"].setInput( input["out"] )
		group["transform"]["translate"].setValue( IECore.V3f( 0, 1, 0 ) )

		self.assertEqual( group["name"].getValue(), "group" )

		groupedRootBound = IECore.Box3f( originalRootBound.min, originalRootBound.max )
		groupedRootBound.min += IECore.V3f( 0, 1, 0 )
		groupedRootBound.max += IECore.V3f( 0, 1, 0 )

		self.assertEqual( group["out"].object( "/" ), IECore.NullObject() )
		self.assertEqual( group["out"].transform( "/" ), IECore.M44f() )
		self.assertEqual( group["out"].bound( "/" ), groupedRootBound )
		self.assertEqual( group["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "group" ] ) )

		self.assertEqual( group["out"].object( "/group" ), IECore.NullObject() )
		self.assertEqual( group["out"].transform( "/group" ), IECore.M44f.createTranslated( IECore.V3f( 0, 1, 0 ) ) )
		self.assertEqual( group["out"].bound( "/group" ), originalRootBound )
		self.assertEqual( group["out"].childNames( "/group" ), IECore.InternedStringVectorData( [ "sphere" ] ) )

		self.assertEqual( group["out"].object( "/group/sphere" ), sphere )
		self.assertEqual( group["out"].transform( "/group/sphere" ), IECore.M44f.createTranslated( IECore.V3f( 1, 0, 0 ) ) )
		self.assertEqual( group["out"].bound( "/group/sphere" ), sphere.bound() )
		self.assertEqual( group["out"].childNames( "/group/sphere" ), IECore.InternedStringVectorData() )

	def testAddAndRemoveInputs( self ) :

		g = GafferScene.Group()
		p = GafferScene.Plane()

		def scenePlugNames() :
			return [ plug.getName() for plug in g.children() if isinstance( plug, GafferScene.ScenePlug ) and plug.direction() == Gaffer.Plug.Direction.In ]

		self.assertEqual( scenePlugNames(), [ "in"] )

		g["in"].setInput( p["out"] )
		self.assertEqual( scenePlugNames(), [ "in", "in1"] )

 		g["in1"].setInput( p["out"] )
 		self.assertEqual( scenePlugNames(), [ "in", "in1", "in2" ] )

 		g["in1"].setInput( None )
 		self.assertEqual( scenePlugNames(), [ "in", "in1" ] )

 		g["in"].setInput( None )
 		self.assertEqual( scenePlugNames(), [ "in" ] )

 		g["in"].setInput( p["out"] )
 		self.assertEqual( scenePlugNames(), [ "in", "in1"] )

 		g["in1"].setInput( p["out"] )
 		self.assertEqual( scenePlugNames(), [ "in", "in1", "in2" ] )

		g["in"].setInput( None )
		self.assertEqual( scenePlugNames(), [ "in", "in1", "in2" ] )

	def testMerge( self ) :

		sphere = IECore.SpherePrimitive()
		input1 = GafferSceneTest.CompoundObjectSource()
		input1["in"].setValue(
			IECore.CompoundObject( {
				"bound" : IECore.Box3fData( sphere.bound() ),
				"children" : {
					"sphereGroup" : {
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

		plane = IECore.MeshPrimitive.createPlane( IECore.Box2f( IECore.V2f( -1 ), IECore.V2f( 1 ) ) )
		input2 = GafferSceneTest.CompoundObjectSource()
		input2["in"].setValue(
			IECore.CompoundObject( {
				"bound" : IECore.Box3fData( plane.bound() ),
				"children" : {
					"planeGroup" : {
						"bound" : IECore.Box3fData( plane.bound() ),
						"children" : {
							"plane" : {
								"bound" : IECore.Box3fData( plane.bound() ),
								"object" : plane,
							},
						},
					},
				},
			} ),
		)

		combinedBound = sphere.bound()
		combinedBound.extendBy( plane.bound() )

		group = GafferScene.Group()
		group["name"].setValue( "topLevel" )
		group["in"].setInput( input1["out"] )
		group["in1"].setInput( input2["out"] )

		self.assertEqual( group["out"].object( "/" ), IECore.NullObject() )
		self.assertEqual( group["out"].transform( "/" ), IECore.M44f() )
		self.assertEqual( group["out"].bound( "/" ), combinedBound )
		self.assertEqual( group["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "topLevel" ] ) )

		self.assertEqual( group["out"].object( "/topLevel" ), IECore.NullObject() )
		self.assertEqual( group["out"].transform( "/topLevel" ), IECore.M44f() )
		self.assertEqual( group["out"].bound( "/topLevel" ), combinedBound )
		self.assertEqual( group["out"].childNames( "/topLevel" ), IECore.InternedStringVectorData( [ "sphereGroup", "planeGroup" ] ) )

		self.assertEqual( group["out"].object( "/topLevel/sphereGroup" ), IECore.NullObject() )
		self.assertEqual( group["out"].transform( "/topLevel/sphereGroup" ), IECore.M44f() )
		self.assertEqual( group["out"].bound( "/topLevel/sphereGroup" ), sphere.bound() )
		self.assertEqual( group["out"].childNames( "/topLevel/sphereGroup" ), IECore.InternedStringVectorData( [ "sphere" ] ) )

		self.assertEqual( group["out"].object( "/topLevel/sphereGroup/sphere" ), sphere )
		self.assertEqual( group["out"].transform( "/topLevel/sphereGroup/sphere" ), IECore.M44f() )
		self.assertEqual( group["out"].bound( "/topLevel/sphereGroup/sphere" ), sphere.bound() )
		self.assertEqual( group["out"].childNames( "/topLevel/sphereGroup/sphere" ), IECore.InternedStringVectorData() )

		self.assertEqual( group["out"].object( "/topLevel/planeGroup" ), IECore.NullObject() )
		self.assertEqual( group["out"].transform( "/topLevel/planeGroup" ), IECore.M44f() )
		self.assertEqual( group["out"].bound( "/topLevel/planeGroup" ), plane.bound() )
		self.assertEqual( group["out"].childNames( "/topLevel/planeGroup" ), IECore.InternedStringVectorData( [ "plane" ] ) )

		self.assertEqual( group["out"].object( "/topLevel/planeGroup/plane" ), plane )
		self.assertEqual( group["out"].transform( "/topLevel/planeGroup/plane" ), IECore.M44f() )
		self.assertEqual( group["out"].bound( "/topLevel/planeGroup/plane" ), plane.bound() )
		self.assertEqual( group["out"].childNames( "/topLevel/planeGroup/plane" ), IECore.InternedStringVectorData() )

	def testNameClashes( self ) :

		sphere = IECore.SpherePrimitive()
		input1 = GafferSceneTest.CompoundObjectSource()
		input1["in"].setValue(
			IECore.CompoundObject( {
				"bound" : IECore.Box3fData( sphere.bound() ),
				"children" : {
					"myLovelyObject" : {
						"bound" : IECore.Box3fData( sphere.bound() ),
						"object" : sphere,
					},
				},
			} ),
		)

		plane = IECore.MeshPrimitive.createPlane( IECore.Box2f( IECore.V2f( -1 ), IECore.V2f( 1 ) ) )
		input2 = GafferSceneTest.CompoundObjectSource()
		input2["in"].setValue(
			IECore.CompoundObject( {
				"bound" : IECore.Box3fData( plane.bound() ),
				"children" : {
					"myLovelyObject" : {
						"bound" : IECore.Box3fData( plane.bound() ),
						"object" : plane,
					},
				},
			} ),
		)

		combinedBound = sphere.bound()
		combinedBound.extendBy( plane.bound() )

		group = GafferScene.Group()
		group["name"].setValue( "topLevel" )
		group["in"].setInput( input1["out"] )
		group["in1"].setInput( input2["out"] )

		self.assertEqual( group["out"].object( "/" ), IECore.NullObject() )
		self.assertEqual( group["out"].transform( "/" ), IECore.M44f() )
		self.assertEqual( group["out"].bound( "/" ), combinedBound )
		self.assertEqual( group["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "topLevel" ] ) )

		self.assertEqual( group["out"].object( "/topLevel" ), IECore.NullObject() )
		self.assertEqual( group["out"].transform( "/topLevel" ), IECore.M44f() )
		self.assertEqual( group["out"].bound( "/topLevel" ), combinedBound )
		self.assertEqual( group["out"].childNames( "/topLevel" ), IECore.InternedStringVectorData( [ "myLovelyObject", "myLovelyObject1" ] ) )

		self.assertEqual( group["out"].object( "/topLevel/myLovelyObject" ), sphere )
		self.assertEqual( group["out"].transform( "/topLevel/myLovelyObject" ), IECore.M44f() )
		self.assertEqual( group["out"].bound( "/topLevel/myLovelyObject" ), sphere.bound() )
		self.assertEqual( group["out"].childNames( "/topLevel/myLovelyObject" ), IECore.InternedStringVectorData() )

		self.assertEqual( group["out"].object( "/topLevel/myLovelyObject1" ), plane )
		self.assertEqual( group["out"].transform( "/topLevel/myLovelyObject1" ), IECore.M44f() )
		self.assertEqual( group["out"].bound( "/topLevel/myLovelyObject1" ), plane.bound() )
		self.assertEqual( group["out"].childNames( "/topLevel/myLovelyObject1" ), IECore.InternedStringVectorData() )

	def testSerialisationOfDynamicInputs( self ) :

		s = Gaffer.ScriptNode()
		s["c"] = GafferScene.Camera()
		s["g"] = GafferScene.Group()
		s["g"]["in"].setInput( s["c"]["out"] )
		s["g"]["in1"].setInput( s["c"]["out"] )

		self.failUnless( "in2" in s["g"] )
		self.assertEqual( s["g"]["in2"].getInput(), None )

		ss = s.serialise()

		s = Gaffer.ScriptNode()
		s.execute( ss )

		self.failUnless( s["g"]["in"].getInput().isSame( s["c"]["out"] ) )
		self.failUnless( s["g"]["in1"].getInput().isSame( s["c"]["out"] ) )
		self.failUnless( "in2" in s["g"] )
		self.assertEqual( s["g"]["in2"].getInput(), None )

	def testNameClashesWithNumericSuffixes( self ) :

		sphere = IECore.SpherePrimitive()
		input1 = GafferSceneTest.CompoundObjectSource()
		input1["in"].setValue(
			IECore.CompoundObject( {
				"bound" : IECore.Box3fData( sphere.bound() ),
				"children" : {
					"myLovelyObject1" : {
						"bound" : IECore.Box3fData( sphere.bound() ),
						"object" : sphere,
					},
				},
			} ),
		)

		plane = IECore.MeshPrimitive.createPlane( IECore.Box2f( IECore.V2f( -1 ), IECore.V2f( 1 ) ) )
		input2 = GafferSceneTest.CompoundObjectSource()
		input2["in"].setValue(
			IECore.CompoundObject( {
				"bound" : IECore.Box3fData( plane.bound() ),
				"children" : {
					"myLovelyObject1" : {
						"bound" : IECore.Box3fData( plane.bound() ),
						"object" : plane,
					},
				},
			} ),
		)

		combinedBound = sphere.bound()
		combinedBound.extendBy( plane.bound() )

		group = GafferScene.Group()
		group["name"].setValue( "topLevel" )
		group["in"].setInput( input1["out"] )
		group["in1"].setInput( input2["out"] )

		self.assertEqual( group["out"].object( "/" ), IECore.NullObject() )
		self.assertEqual( group["out"].transform( "/" ), IECore.M44f() )
		self.assertEqual( group["out"].bound( "/" ), combinedBound )
		self.assertEqual( group["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "topLevel" ] ) )

		self.assertEqual( group["out"].object( "/topLevel" ), IECore.NullObject() )
		self.assertEqual( group["out"].transform( "/topLevel" ), IECore.M44f() )
		self.assertEqual( group["out"].bound( "/topLevel" ), combinedBound )
		self.assertEqual( group["out"].childNames( "/topLevel" ), IECore.InternedStringVectorData( [ "myLovelyObject1", "myLovelyObject2" ] ) )

		self.assertEqual( group["out"].object( "/topLevel/myLovelyObject1" ), sphere )
		self.assertEqual( group["out"].transform( "/topLevel/myLovelyObject1" ), IECore.M44f() )
		self.assertEqual( group["out"].bound( "/topLevel/myLovelyObject1" ), sphere.bound() )
		self.assertEqual( group["out"].childNames( "/topLevel/myLovelyObject1" ), IECore.InternedStringVectorData() )

		self.assertEqual( group["out"].object( "/topLevel/myLovelyObject2" ), plane )
		self.assertEqual( group["out"].transform( "/topLevel/myLovelyObject2" ), IECore.M44f() )
		self.assertEqual( group["out"].bound( "/topLevel/myLovelyObject2" ), plane.bound() )
		self.assertEqual( group["out"].childNames( "/topLevel/myLovelyObject2" ), IECore.InternedStringVectorData() )

	def testNameClashesWithThreading( self ) :

		sphere = IECore.SpherePrimitive()
		input1 = GafferSceneTest.CompoundObjectSource()
		input1["in"].setValue(
			IECore.CompoundObject( {
				"bound" : IECore.Box3fData( sphere.bound() ),
				"children" : {
					"myLovelyObject1" : {
						"bound" : IECore.Box3fData( sphere.bound() ),
						"object" : sphere,
					},
				},
			} ),
		)

		plane = IECore.MeshPrimitive.createPlane( IECore.Box2f( IECore.V2f( -1 ), IECore.V2f( 1 ) ) )
		input2 = GafferSceneTest.CompoundObjectSource()
		input2["in"].setValue(
			IECore.CompoundObject( {
				"bound" : IECore.Box3fData( plane.bound() ),
				"children" : {
					"myLovelyObject1" : {
						"bound" : IECore.Box3fData( plane.bound() ),
						"object" : plane,
					},
				},
			} ),
		)

		group = GafferScene.Group()
		group["name"].setValue( "topLevel" )
		group["in"].setInput( input1["out"] )
		group["in1"].setInput( input2["out"] )

		sceneProcedural = GafferScene.SceneProcedural( group["out"], Gaffer.Context(), "/" )

		for i in range( 0, 1000 ) :
			mh = IECore.CapturingMessageHandler()
			with mh :
				# we use a CapturingRenderer as it will invoke the procedural
				# on multiple threads for us automatically.
				renderer = IECore.CapturingRenderer()
				with IECore.WorldBlock( renderer ) :
					renderer.procedural( sceneProcedural )
			self.assertEqual( len( mh.messages ), 0 )

	def testHashes( self ) :

		p = GafferScene.Plane()

		g = GafferScene.Group()
		g["in"].setInput( p["out"] )

		self.assertSceneValid( g["out"] )
		self.assertSceneHashesNotEqual( g["out"], p["out"], childPlugNames = ( "globals", ) )

		self.assertPathHashesEqual( g["out"], "/group/plane", p["out"], "/plane" )

	def testTransformHash( self ) :

		p = GafferScene.Plane()

		g1 = GafferScene.Group()
		g1["in"].setInput( p["out"] )

		g2 = GafferScene.Group()
 		g2["in"].setInput( p["out"] )

 		self.assertSceneHashesEqual( g1["out"], g2["out"] )

	 	g2["transform"]["translate"].setValue( IECore.V3f( 1, 0, 0 ) )

 		self.assertSceneHashesEqual( g1["out"], g2["out"], pathsToIgnore = ( "/", "/group", ) )
 		self.assertSceneHashesEqual( g1["out"], g2["out"], childPlugNamesToIgnore = ( "transform", "bound" ) )
		self.assertNotEqual( g1["out"].transformHash( "/group" ), g2["out"].transformHash( "/group" ) )
		self.assertEqual( g1["out"].boundHash( "/group" ), g2["out"].boundHash( "/group" ) )
		self.assertNotEqual( g1["out"].boundHash( "/" ), g2["out"].boundHash( "/" ) )

	def testChildNamesHash( self ) :

		p = GafferScene.Plane()

		g1 = GafferScene.Group()
		g1["in"].setInput( p["out"] )

		g2 = GafferScene.Group()
 		g2["in"].setInput( p["out"] )

 		self.assertSceneHashesEqual( g1["out"], g2["out"] )

		g2["name"].setValue( "stuff" )

		equivalentPaths = [
			( "/", "/" ),
			( "/group", "/stuff" ),
			( "/group/plane", "/stuff/plane" ),
		]
		for path1, path2 in equivalentPaths :
			self.assertEqual( g1["out"].boundHash( path1 ), g2["out"].boundHash( path2 ) )
			self.assertEqual( g1["out"].transformHash( path1 ), g2["out"].transformHash( path2 ) )
			self.assertEqual( g1["out"].objectHash( path1 ), g2["out"].objectHash( path2 ) )
			self.assertEqual( g1["out"].attributesHash( path1 ), g2["out"].attributesHash( path2 ) )
			if path1 is not "/" :
				self.assertEqual( g1["out"].childNamesHash( path1 ), g2["out"].childNamesHash( path2 ) )
			else :
				self.assertNotEqual( g1["out"].childNamesHash( path1 ), g2["out"].childNamesHash( path2 ) )

	def testWithCacheDisabled( self ) :

		Gaffer.ValuePlug.setCacheMemoryLimit( 0 )

		p = GafferScene.Plane()

		g1 = GafferScene.Group()
		g1["in"].setInput( p["out"] )

		self.assertSceneValid( g1["out"] )

	def testAffects( self ) :

		p = GafferScene.Plane()
		g = GafferScene.Group()
		g["in"].setInput( p["out"] )

		for c in g["in"].children() :
			a = g.affects( c )
			self.assertEqual( len( a ), 1 if c.getName() != "childNames" else 2 )
			self.assertEqual( a[0].fullName(), "Group.out." + c.getName() )

	def testGroupInABox( self ) :

		s = Gaffer.ScriptNode()

		s["p"] = GafferScene.Plane()
		s["g1"] = GafferScene.Group()
		s["g2"] = GafferScene.Group()

		s["g1"]["in"].setInput( s["p"]["out"] )
		s["g2"]["in"].setInput( s["g1"]["out"] )

		s.selection().add( s["g1"] )
		b = Gaffer.Box.create( s, s.selection() )

		self.assertEqual( len( b ), 4 ) # one for the user plug, one for the child, one for the input and one for the output

		self.assertTrue( b["g1"]["in"].getInput().isSame( b["in"] ) )
		self.assertTrue( b["in"].getInput().isSame( s["p"]["out"] ) )

		self.assertTrue( s["g2"]["in"].getInput().isSame( b["out"] ) )
		self.assertTrue( b["out"].getInput().isSame( b["g1"]["out"] ) )

		# this test was causing crashes elsewhere when the script
		# was finally garbage collected, so we force the collection
		# here so we can be sure the problem is fixed.
		del s
		del b
		while gc.collect() :
			pass
		IECore.RefCounted.collectGarbage()

	def testSetsWithRenaming( self ) :

		l1 = GafferSceneTest.TestLight()
		l2 = GafferSceneTest.TestLight()

		g = GafferScene.Group()
		g["in"].setInput( l1["out"] )
		g["in1"].setInput( l2["out"] )

		lightSet = g["out"]["globals"].getValue()["gaffer:sets"]["__lights"]
		self.assertEqual(
			set( lightSet.value.paths() ),
			set( [
				"/group/light",
				"/group/light1",
			] )
		)

		self.assertSceneValid( g["out"] )

		g2 = GafferScene.Group()
		g2["in"].setInput( g["out"] )

		lightSet = g2["out"]["globals"].getValue()["gaffer:sets"]["__lights"]
		self.assertEqual(
			set( lightSet.value.paths() ),
			set( [
				"/group/group/light",
				"/group/group/light1",
			] )
		)

	def testDisabled( self ) :

		p1 = GafferScene.Plane()
		p2 = GafferScene.Plane()

		g = GafferScene.Group()
		g["in"].setInput( p1["out"] )
		g["in1"].setInput( p2["out"] )

		self.assertSceneValid( g["out"] )
		self.assertEqual( g["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "group" ] ) )

		g["enabled"].setValue( False )

		self.assertSceneValid( g["out"] )
		self.assertEqual( g["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "plane" ] ) )
		self.assertScenesEqual( g["out"], p1["out"] )

	def testSetsWithDiamondInput( self ) :

		#	l
		#	| \
		#	|  \
		#	lg1 lg2
		#	|  /
		#	| /
		#	g

		l = GafferSceneTest.TestLight()

		lg1 = GafferScene.Group()
		lg1["name"].setValue( "lightGroup1" )
		lg1["in"].setInput( l["out"] )

		lg2 = GafferScene.Group()
		lg2["name"].setValue( "lightGroup2" )
		lg2["in"].setInput( l["out"] )

		self.assertNotEqual( lg1["out"]["globals"].hash(), lg2["out"]["globals"].hash() )

		g = GafferScene.Group()
		g["in"].setInput( lg1["out"] )
		g["in1"].setInput( lg2["out"] )

		lightSet = g["out"]["globals"].getValue()["gaffer:sets"]["__lights"]
		self.assertEqual(
			set( lightSet.value.paths() ),
			set( [
				"/group/lightGroup1/light",
				"/group/lightGroup2/light",
			] )
		)

	def testMakeConnectionAndUndo( self ) :

		s = Gaffer.ScriptNode()

		s["c"] = GafferScene.Plane()
		s["g"] = GafferScene.Group()
		s["g"]["__customPlug"] = Gaffer.V2fPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		with Gaffer.UndoContext( s ) :
			s["g"]["in"].setInput( s["c"]["out"] )

		self.assertTrue( "__customPlug" in s["g"] )
		self.assertTrue( "in" in s["g"] )
		self.assertTrue( "in1" in s["g"] )

		s.undo()

		self.assertTrue( "__customPlug" in s["g"] )
		self.assertTrue( "in" in s["g"] )
		self.assertFalse( "in1" in s["g"] )

	def testDeleteInputsAndSerialise( self ) :

		s = Gaffer.ScriptNode()

		s["s"] = GafferScene.Sphere()
		s["c"] = GafferScene.Camera()
		s["p"] = GafferScene.Plane()
		s["t"] = GafferScene.Transform()
		s["p1"] = GafferScene.Plane()

		s["g"] = GafferScene.Group()
		s["g"]["in"].setInput( s["s"]["out"] )
		s["g"]["in1"].setInput( s["c"]["out"] )
		s["g"]["in2"].setInput( s["p"]["out"] )
		s["g"]["in3"].setInput( s["t"]["out"] )
		s["g"]["in4"].setInput( s["p1"]["out"] )

		s.deleteNodes( filter = Gaffer.StandardSet( [ s["s"], s["p"], s["p1"] ] ) )

		ss = s.serialise()

		s2 = Gaffer.ScriptNode()
		s2.execute( ss )

	def testDifferentSetsInEachInput( self ) :

		p1 = GafferScene.Plane()
		s1 = GafferScene.Set()
		s1["name"].setValue( "s1" )
		s1["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )
		s1["in"].setInput( p1["out"] )

		p2 = GafferScene.Plane()
		s2 = GafferScene.Set()
		s2["name"].setValue( "s2" )
		s2["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )
		s2["in"].setInput( p2["out"] )

		g = GafferScene.Group()
		g["in"].setInput( s1["out"] )
		g["in1"].setInput( s2["out"] )

		sets = g["out"]["globals"].getValue()["gaffer:sets"]

		self.assertEqual(
			sets,
			IECore.CompoundData( {
				"s1" : GafferScene.PathMatcherData(
					GafferScene.PathMatcher( [ "/group/plane" ] )
				),
				"s2" : GafferScene.PathMatcherData(
					GafferScene.PathMatcher( [ "/group/plane1" ] )
				),
			} )
		)

	def setUp( self ) :

		self.__originalCacheMemoryLimit = Gaffer.ValuePlug.getCacheMemoryLimit()

	def tearDown( self ) :

		Gaffer.ValuePlug.setCacheMemoryLimit( self.__originalCacheMemoryLimit )

if __name__ == "__main__":
	unittest.main()
