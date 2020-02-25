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
import gc
import os
import imath

import IECore
import IECoreScene

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest

class GroupTest( GafferSceneTest.SceneTestCase ) :

	def testTwoLevels( self ) :

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

		group = GafferScene.Group()
		group["in"][0].setInput( input["out"] )
		group["name"].setValue( "topLevel" )

		self.assertEqual( group["name"].getValue(), "topLevel" )

		self.assertEqual( group["out"].object( "/" ), IECore.NullObject() )
		self.assertEqual( group["out"].transform( "/" ), imath.M44f() )
		self.assertEqual( group["out"].bound( "/" ), sphere.bound() )
		self.assertEqual( group["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "topLevel" ] ) )

		self.assertEqual( group["out"].object( "/topLevel" ), IECore.NullObject() )
		self.assertEqual( group["out"].transform( "/topLevel" ), imath.M44f() )
		self.assertEqual( group["out"].bound( "/topLevel" ), sphere.bound() )
		self.assertEqual( group["out"].childNames( "/topLevel" ), IECore.InternedStringVectorData( [ "group" ] ) )

		self.assertEqual( group["out"].object( "/topLevel/group" ), IECore.NullObject() )
		self.assertEqual( group["out"].transform( "/topLevel/group" ), imath.M44f() )
		self.assertEqual( group["out"].bound( "/topLevel/group" ), sphere.bound() )
		self.assertEqual( group["out"].childNames( "/topLevel/group" ), IECore.InternedStringVectorData( [ "sphere" ] ) )

		self.assertEqual( group["out"].object( "/topLevel/group/sphere" ), sphere )
		self.assertEqual( group["out"].transform( "/topLevel/group/sphere" ), imath.M44f() )
		self.assertEqual( group["out"].bound( "/topLevel/group/sphere" ), sphere.bound() )
		self.assertEqual( group["out"].childNames( "/topLevel/group/sphere" ), IECore.InternedStringVectorData() )

	def testTransform( self ) :

		sphere = IECoreScene.SpherePrimitive()
		originalRootBound = sphere.bound()
		originalRootBound.setMin( originalRootBound.min() + imath.V3f( 1, 0, 0 ) )
		originalRootBound.setMax( originalRootBound.max() + imath.V3f( 1, 0, 0 ) )
		input = GafferSceneTest.CompoundObjectSource()
		input["in"].setValue(
			IECore.CompoundObject( {
				"bound" : IECore.Box3fData( originalRootBound ),
				"children" : {
					"sphere" : {
						"object" : sphere,
						"bound" : IECore.Box3fData( sphere.bound() ),
						"transform" : IECore.M44fData( imath.M44f().translate( imath.V3f( 1, 0, 0 ) ) ),
					}
				}
			} )
		)

		group = GafferScene.Group()
		group["in"][0].setInput( input["out"] )
		group["transform"]["translate"].setValue( imath.V3f( 0, 1, 0 ) )

		self.assertEqual( group["name"].getValue(), "group" )

		groupedRootBound = imath.Box3f( originalRootBound.min(), originalRootBound.max() )
		groupedRootBound.setMin( groupedRootBound.min() + imath.V3f( 0, 1, 0 ) )
		groupedRootBound.setMax( groupedRootBound.max() + imath.V3f( 0, 1, 0 ) )

		self.assertEqual( group["out"].object( "/" ), IECore.NullObject() )
		self.assertEqual( group["out"].transform( "/" ), imath.M44f() )
		self.assertEqual( group["out"].bound( "/" ), groupedRootBound )
		self.assertEqual( group["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "group" ] ) )

		self.assertEqual( group["out"].object( "/group" ), IECore.NullObject() )
		self.assertEqual( group["out"].transform( "/group" ), imath.M44f().translate( imath.V3f( 0, 1, 0 ) ) )
		self.assertEqual( group["out"].bound( "/group" ), originalRootBound )
		self.assertEqual( group["out"].childNames( "/group" ), IECore.InternedStringVectorData( [ "sphere" ] ) )

		self.assertEqual( group["out"].object( "/group/sphere" ), sphere )
		self.assertEqual( group["out"].transform( "/group/sphere" ), imath.M44f().translate( imath.V3f( 1, 0, 0 ) ) )
		self.assertEqual( group["out"].bound( "/group/sphere" ), sphere.bound() )
		self.assertEqual( group["out"].childNames( "/group/sphere" ), IECore.InternedStringVectorData() )

	def testAddAndRemoveInputs( self ) :

		g = GafferScene.Group()
		p = GafferScene.Plane()

		self.assertEqual( len( g["in"] ), 1 )

		g["in"][0].setInput( p["out"] )
		self.assertEqual( len( g["in"] ), 2 )

 		g["in"][1].setInput( p["out"] )
		self.assertEqual( len( g["in"] ), 3 )

 		g["in"][1].setInput( None )
		self.assertEqual( len( g["in"] ), 2 )

		g["in"][0].setInput( None )
		self.assertEqual( len( g["in"] ), 1 )

		g["in"][0].setInput( p["out"] )
		self.assertEqual( len( g["in"] ), 2 )

 		g["in"][1].setInput( p["out"] )
		self.assertEqual( len( g["in"] ), 3 )

		g["in"].setInput( None )
		self.assertEqual( len( g["in"] ), 3 )

	def testMerge( self ) :

		sphere = IECoreScene.SpherePrimitive()
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

		plane = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) )
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
		group["in"][0].setInput( input1["out"] )
		group["in"][1].setInput( input2["out"] )

		self.assertEqual( group["out"].object( "/" ), IECore.NullObject() )
		self.assertEqual( group["out"].transform( "/" ), imath.M44f() )
		self.assertEqual( group["out"].bound( "/" ), combinedBound )
		self.assertEqual( group["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "topLevel" ] ) )

		self.assertEqual( group["out"].object( "/topLevel" ), IECore.NullObject() )
		self.assertEqual( group["out"].transform( "/topLevel" ), imath.M44f() )
		self.assertEqual( group["out"].bound( "/topLevel" ), combinedBound )
		self.assertEqual( group["out"].childNames( "/topLevel" ), IECore.InternedStringVectorData( [ "sphereGroup", "planeGroup" ] ) )

		self.assertEqual( group["out"].object( "/topLevel/sphereGroup" ), IECore.NullObject() )
		self.assertEqual( group["out"].transform( "/topLevel/sphereGroup" ), imath.M44f() )
		self.assertEqual( group["out"].bound( "/topLevel/sphereGroup" ), sphere.bound() )
		self.assertEqual( group["out"].childNames( "/topLevel/sphereGroup" ), IECore.InternedStringVectorData( [ "sphere" ] ) )

		self.assertEqual( group["out"].object( "/topLevel/sphereGroup/sphere" ), sphere )
		self.assertEqual( group["out"].transform( "/topLevel/sphereGroup/sphere" ), imath.M44f() )
		self.assertEqual( group["out"].bound( "/topLevel/sphereGroup/sphere" ), sphere.bound() )
		self.assertEqual( group["out"].childNames( "/topLevel/sphereGroup/sphere" ), IECore.InternedStringVectorData() )

		self.assertEqual( group["out"].object( "/topLevel/planeGroup" ), IECore.NullObject() )
		self.assertEqual( group["out"].transform( "/topLevel/planeGroup" ), imath.M44f() )
		self.assertEqual( group["out"].bound( "/topLevel/planeGroup" ), plane.bound() )
		self.assertEqual( group["out"].childNames( "/topLevel/planeGroup" ), IECore.InternedStringVectorData( [ "plane" ] ) )

		self.assertEqual( group["out"].object( "/topLevel/planeGroup/plane" ), plane )
		self.assertEqual( group["out"].transform( "/topLevel/planeGroup/plane" ), imath.M44f() )
		self.assertEqual( group["out"].bound( "/topLevel/planeGroup/plane" ), plane.bound() )
		self.assertEqual( group["out"].childNames( "/topLevel/planeGroup/plane" ), IECore.InternedStringVectorData() )

	def testNameClashes( self ) :

		sphere = IECoreScene.SpherePrimitive()
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

		plane = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) )
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
		group["in"][0].setInput( input1["out"] )
		group["in"][1].setInput( input2["out"] )

		self.assertEqual( group["out"].object( "/" ), IECore.NullObject() )
		self.assertEqual( group["out"].transform( "/" ), imath.M44f() )
		self.assertEqual( group["out"].bound( "/" ), combinedBound )
		self.assertEqual( group["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "topLevel" ] ) )

		self.assertEqual( group["out"].object( "/topLevel" ), IECore.NullObject() )
		self.assertEqual( group["out"].transform( "/topLevel" ), imath.M44f() )
		self.assertEqual( group["out"].bound( "/topLevel" ), combinedBound )
		self.assertEqual( group["out"].childNames( "/topLevel" ), IECore.InternedStringVectorData( [ "myLovelyObject", "myLovelyObject1" ] ) )

		self.assertEqual( group["out"].object( "/topLevel/myLovelyObject" ), sphere )
		self.assertEqual( group["out"].transform( "/topLevel/myLovelyObject" ), imath.M44f() )
		self.assertEqual( group["out"].bound( "/topLevel/myLovelyObject" ), sphere.bound() )
		self.assertEqual( group["out"].childNames( "/topLevel/myLovelyObject" ), IECore.InternedStringVectorData() )

		self.assertEqual( group["out"].object( "/topLevel/myLovelyObject1" ), plane )
		self.assertEqual( group["out"].transform( "/topLevel/myLovelyObject1" ), imath.M44f() )
		self.assertEqual( group["out"].bound( "/topLevel/myLovelyObject1" ), plane.bound() )
		self.assertEqual( group["out"].childNames( "/topLevel/myLovelyObject1" ), IECore.InternedStringVectorData() )

	def testSerialisationOfDynamicInputs( self ) :

		s = Gaffer.ScriptNode()
		s["c"] = GafferScene.Camera()
		s["g"] = GafferScene.Group()
		s["g"]["in"][0].setInput( s["c"]["out"] )
		s["g"]["in"][1].setInput( s["c"]["out"] )

		self.assertEqual( len( s["g"]["in"] ), 3 )
		self.assertEqual( s["g"]["in"][2].getInput(), None )

		ss = s.serialise()

		s = Gaffer.ScriptNode()
		s.execute( ss )

		self.failUnless( s["g"]["in"][0].getInput().isSame( s["c"]["out"] ) )
		self.failUnless( s["g"]["in"][1].getInput().isSame( s["c"]["out"] ) )
		self.assertEqual( len( s["g"]["in"] ), 3 )
		self.assertEqual( s["g"]["in"][2].getInput(), None )

	def testNameClashesWithNumericSuffixes( self ) :

		sphere = IECoreScene.SpherePrimitive()
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

		plane = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) )
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
		group["in"][0].setInput( input1["out"] )
		group["in"][1].setInput( input2["out"] )

		self.assertEqual( group["out"].object( "/" ), IECore.NullObject() )
		self.assertEqual( group["out"].transform( "/" ), imath.M44f() )
		self.assertEqual( group["out"].bound( "/" ), combinedBound )
		self.assertEqual( group["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "topLevel" ] ) )

		self.assertEqual( group["out"].object( "/topLevel" ), IECore.NullObject() )
		self.assertEqual( group["out"].transform( "/topLevel" ), imath.M44f() )
		self.assertEqual( group["out"].bound( "/topLevel" ), combinedBound )
		self.assertEqual( group["out"].childNames( "/topLevel" ), IECore.InternedStringVectorData( [ "myLovelyObject1", "myLovelyObject2" ] ) )

		self.assertEqual( group["out"].object( "/topLevel/myLovelyObject1" ), sphere )
		self.assertEqual( group["out"].transform( "/topLevel/myLovelyObject1" ), imath.M44f() )
		self.assertEqual( group["out"].bound( "/topLevel/myLovelyObject1" ), sphere.bound() )
		self.assertEqual( group["out"].childNames( "/topLevel/myLovelyObject1" ), IECore.InternedStringVectorData() )

		self.assertEqual( group["out"].object( "/topLevel/myLovelyObject2" ), plane )
		self.assertEqual( group["out"].transform( "/topLevel/myLovelyObject2" ), imath.M44f() )
		self.assertEqual( group["out"].bound( "/topLevel/myLovelyObject2" ), plane.bound() )
		self.assertEqual( group["out"].childNames( "/topLevel/myLovelyObject2" ), IECore.InternedStringVectorData() )

	def testNameClashesWithThreading( self ) :

		sphere = IECoreScene.SpherePrimitive()
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

		plane = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) )
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
		group["in"][0].setInput( input1["out"] )
		group["in"][1].setInput( input2["out"] )

		GafferSceneTest.traverseScene( group["out"] )

	def testHashes( self ) :

		p = GafferScene.Plane()

		g = GafferScene.Group()
		g["in"][0].setInput( p["out"] )

		self.assertSceneValid( g["out"] )

		self.assertPathHashesEqual( g["out"], "/group/plane", p["out"], "/plane" )

	def testGlobalsPassThrough( self ) :

		p = GafferScene.Plane()

		g = GafferScene.Group()
		g["in"][0].setInput( p["out"] )

		self.assertEqual( g["out"]["globals"].hash(), p["out"]["globals"].hash() )
		self.assertTrue( g["out"]["globals"].getValue( _copy = False ).isSame( p["out"]["globals"].getValue( _copy = False ) ) )

	def testTransformHash( self ) :

		p = GafferScene.Plane()

		g1 = GafferScene.Group()
		g1["in"][0].setInput( p["out"] )

		g2 = GafferScene.Group()
 		g2["in"][0].setInput( p["out"] )

 		self.assertSceneHashesEqual( g1["out"], g2["out"] )

	 	g2["transform"]["translate"].setValue( imath.V3f( 1, 0, 0 ) )

 		self.assertSceneHashesEqual( g1["out"], g2["out"], pathsToIgnore = ( "/", "/group", ) )
		self.assertSceneHashesEqual( g1["out"], g2["out"], checks = self.allSceneChecks - { "transform", "bound" } )
		self.assertNotEqual( g1["out"].transformHash( "/group" ), g2["out"].transformHash( "/group" ) )
		self.assertEqual( g1["out"].boundHash( "/group" ), g2["out"].boundHash( "/group" ) )
		self.assertNotEqual( g1["out"].boundHash( "/" ), g2["out"].boundHash( "/" ) )

	def testChildNamesHash( self ) :

		p = GafferScene.Plane()

		g1 = GafferScene.Group()
		g1["in"][0].setInput( p["out"] )

		g2 = GafferScene.Group()
 		g2["in"][0].setInput( p["out"] )

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
		g1["in"][0].setInput( p["out"] )

		self.assertSceneValid( g1["out"] )

	def testAffects( self ) :

		p = GafferScene.Plane()
		g = GafferScene.Group()
		g["in"][0].setInput( p["out"] )

		for c in g["in"][0].children() :
			a = g.affects( c )
			self.assertEqual( len( a ), 1 if c.getName() != "childNames" else 2 )
			self.assertEqual( a[0].fullName(), "Group.out." + c.getName() )

	def testGroupInABox( self ) :

		s = Gaffer.ScriptNode()

		s["p"] = GafferScene.Plane()
		s["g1"] = GafferScene.Group()
		s["g2"] = GafferScene.Group()

		s["g1"]["in"][0].setInput( s["p"]["out"] )
		s["g2"]["in"][0].setInput( s["g1"]["out"] )

		s.selection().add( s["g1"] )
		b = Gaffer.Box.create( s, s.selection() )

		self.assertEqual( len( b ), 4 ) # one for the user plug, one for the child, one for the input and one for the output

		self.assertTrue( b["g1"]["in"][0].getInput().isSame( b["in_in0"] ) )
		self.assertTrue( b["in_in0"].getInput().isSame( s["p"]["out"] ) )

		self.assertTrue( s["g2"]["in"][0].getInput().isSame( b["out"] ) )
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
		g["in"][0].setInput( l1["out"] )
		g["in"][1].setInput( l2["out"] )

		lightSet = g["out"].set( "__lights" )
		self.assertEqual(
			set( lightSet.value.paths() ),
			set( [
				"/group/light",
				"/group/light1",
			] )
		)

		self.assertSceneValid( g["out"] )

		g2 = GafferScene.Group()
		g2["in"][0].setInput( g["out"] )

		lightSet = g2["out"].set( "__lights" )
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
		g["in"][0].setInput( p1["out"] )
		g["in"][1].setInput( p2["out"] )

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
		lg1["in"][0].setInput( l["out"] )

		lg2 = GafferScene.Group()
		lg2["name"].setValue( "lightGroup2" )
		lg2["in"][0].setInput( l["out"] )

		self.assertEqual( lg1["out"]["globals"].hash(), lg2["out"]["globals"].hash() )

		g = GafferScene.Group()
		g["in"][0].setInput( lg1["out"] )
		g["in"][1].setInput( lg2["out"] )

		lightSet = g["out"].set( "__lights" )
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

		with Gaffer.UndoScope( s ) :
			s["g"]["in"][0].setInput( s["c"]["out"] )

		self.assertTrue( "__customPlug" in s["g"] )
		self.assertEqual( len( s["g"]["in"] ), 2 )

		s.undo()

		self.assertTrue( "__customPlug" in s["g"] )
		self.assertEqual( len( s["g"]["in"] ), 1 )

	def testDeleteInputsAndSerialise( self ) :

		s = Gaffer.ScriptNode()

		s["s"] = GafferScene.Sphere()
		s["c"] = GafferScene.Camera()
		s["p"] = GafferScene.Plane()
		s["t"] = GafferScene.Transform()
		s["p1"] = GafferScene.Plane()

		s["g"] = GafferScene.Group()
		s["g"]["in"][0].setInput( s["s"]["out"] )
		s["g"]["in"][1].setInput( s["c"]["out"] )
		s["g"]["in"][2].setInput( s["p"]["out"] )
		s["g"]["in"][3].setInput( s["t"]["out"] )
		s["g"]["in"][4].setInput( s["p1"]["out"] )

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
		g["in"][0].setInput( s1["out"] )
		g["in"][1].setInput( s2["out"] )

		self.assertEqual( g["out"]["setNames"].getValue(), IECore.InternedStringVectorData( [ "s1", "s2" ] ) )

		self.assertEqual(
			g["out"].set( "s1" ).value,
			IECore.PathMatcher( [ "/group/plane" ] )
		)

		self.assertEqual(
			g["out"].set( "s2" ).value,
			IECore.PathMatcher( [ "/group/plane1" ] )
		)

	def testNextInPlug( self ) :

		g = GafferScene.Group()
		self.assertTrue( g.nextInPlug().isSame( g["in"][0] ) )

		p = GafferScene.Plane()
		g["in"][0].setInput( p["out"] )
		self.assertTrue( g.nextInPlug().isSame( g["in"][1] ) )

		g["in"][0].setInput( None )
		self.assertTrue( g.nextInPlug().isSame( g["in"][0] ) )

		g["in"][0].setInput( p["out"] )
		g["in"][1].setInput( p["out"] )
		self.assertTrue( g.nextInPlug().isSame( g["in"][2] ) )

		g["in"][0].setInput( None )
		self.assertTrue( g.nextInPlug().isSame( g["in"][2] ) )

	def testUpdateWhenInputSetChanges( self ) :

		p = GafferScene.Plane()
		c = GafferScene.Cube()

		g1 = GafferScene.Group()
		g1["in"][0].setInput( p["out"] )
		g1["in"][1].setInput( c["out"] )

		s = GafferScene.Set()
		s["in"].setInput( g1["out"] )
		s["paths"].setValue( IECore.StringVectorData( [ "/group/plane" ] ) )

		g2 = GafferScene.Group()
		g2["in"][0].setInput( s["out"] )

		h = g2["out"].setHash( "set" )
		self.assertEqual( g2["out"].set( "set" ).value.paths(), [ "/group/group/plane" ] )

		s["paths"].setValue( IECore.StringVectorData( [ "/group/cube" ] ) )

		self.assertNotEqual( g2["out"].setHash( "set" ), h )
		self.assertEqual( g2["out"].set( "set" ).value.paths(), [ "/group/group/cube" ] )

	def testConnectingGroupDoesNotCopyColorMetadata( self ) :

		p = GafferScene.Plane()
		g = GafferScene.Group()

		g["in"][0].setInput( p["out"] )

		noduleColor = Gaffer.Metadata.value( p, "nodule:color", instanceOnly = True )
		connectionColor = Gaffer.Metadata.value( p, "connectionGadget:color", instanceOnly = True )

		self.assertEqual( noduleColor, None )
		self.assertEqual( noduleColor, connectionColor )

	def testProcessInvalidSet( self ) :

		sphere = GafferScene.Sphere()

		bogusSet = GafferScene.Set()
		bogusSet["in"].setInput( sphere["out"] )
		bogusSet["paths"].setValue( IECore.StringVectorData( [ "/sphere", "/notASphere" ] ) )

		group = GafferScene.Group()
		group["in"][0].setInput( bogusSet["out"] )

		self.assertEqual(
			group["out"].set( "set" ).value,
			IECore.PathMatcher( [ "/group/sphere" ] )
		)

		self.assertSceneValid( group["out"] )

	def testExistsAndSortedChildNames( self ) :

		sphere = GafferScene.Sphere()
		cube = GafferScene.Cube()
		group = GafferScene.Group()
		group["in"][0].setInput( sphere["out"] )
		group["in"][1].setInput( cube["out"] )

		self.assertTrue( group["out"].exists( "/" ) )
		self.assertTrue( group["out"].exists( "/group" ) )
		self.assertTrue( group["out"].exists( "/group/sphere" ) )
		self.assertTrue( group["out"].exists( "/group/cube" ) )
		self.assertFalse( group["out"].exists( "/group2" ) )
		self.assertFalse( group["out"].exists( "/group/plane" ) )
		self.assertFalse( group["out"].exists( "/road/to/nowhere" ) )

	def setUp( self ) :

		GafferSceneTest.SceneTestCase.setUp( self )

		self.__originalCacheMemoryLimit = Gaffer.ValuePlug.getCacheMemoryLimit()

	def tearDown( self ) :

		GafferSceneTest.SceneTestCase.tearDown( self )

		Gaffer.ValuePlug.setCacheMemoryLimit( self.__originalCacheMemoryLimit )

if __name__ == "__main__":
	unittest.main()
