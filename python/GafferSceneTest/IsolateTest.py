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

import IECore
import IECoreScene

import Gaffer
import GafferScene
import GafferSceneTest

class IsolateTest( GafferSceneTest.SceneTestCase ) :

	def testPassThrough( self ) :

		sphere = IECoreScene.SpherePrimitive()
		input = GafferSceneTest.CompoundObjectSource()
		input["in"].setValue(
			IECore.CompoundObject( {
				"bound" : IECore.Box3fData( sphere.bound() ),
				"children" : {
					"groupA" : {
						"bound" : IECore.Box3fData( sphere.bound() ),
						"children" : {
							"sphereAA" : {
								"bound" : IECore.Box3fData( sphere.bound() ),
								"object" : sphere,
							},
							"sphereAB" : {
								"bound" : IECore.Box3fData( sphere.bound() ),
								"object" : sphere,
							},
						},
					},
					"groupB" : {
						"bound" : IECore.Box3fData( sphere.bound() ),
						"children" : {
							"sphereBA" : {
								"bound" : IECore.Box3fData( sphere.bound() ),
								"object" : sphere,
							},
							"sphereBB" : {
								"bound" : IECore.Box3fData( sphere.bound() ),
								"object" : sphere,
							},
						},
					},
				},
			} ),
		)

		isolate = GafferScene.Isolate()
		isolate["in"].setInput( input["out"] )

		self.assertSceneValid( input["out"] )
		self.assertSceneValid( isolate["out"] )

		# with no filter applied, nothing should be isolated so we should have a perfect pass through

		self.assertScenesEqual( input["out"], isolate["out"] )
		self.assertSceneHashesEqual( input["out"], isolate["out"] )
		self.assertTrue( input["out"].object( "/groupA/sphereAA", _copy = False ).isSame( isolate["out"].object( "/groupA/sphereAA", _copy = False ) ) )

		# and even with a filter applied, we should have a perfect pass through if the node is disabled.

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/*" ] ) )
		isolate["filter"].setInput( filter["out"] )

		isolate["enabled"].setValue( False )

		self.assertScenesEqual( input["out"], isolate["out"] )
		self.assertSceneHashesEqual( input["out"], isolate["out"] )
		self.assertTrue( input["out"].object( "/groupA/sphereAA", _copy = False ).isSame( isolate["out"].object( "/groupA/sphereAA", _copy = False ) ) )

	def testIsolation( self ) :

		sphere = IECoreScene.SpherePrimitive()
		input = GafferSceneTest.CompoundObjectSource()
		input["in"].setValue(
			IECore.CompoundObject( {
				"bound" : IECore.Box3fData( sphere.bound() ),
				"children" : {
					"groupA" : {
						"bound" : IECore.Box3fData( sphere.bound() ),
						"children" : {
							"sphereAA" : {
								"bound" : IECore.Box3fData( sphere.bound() ),
								"object" : sphere,
							},
							"sphereAB" : {
								"bound" : IECore.Box3fData( sphere.bound() ),
								"object" : sphere,
							},
						},
					},
					"groupB" : {
						"bound" : IECore.Box3fData( sphere.bound() ),
						"children" : {
							"sphereBA" : {
								"bound" : IECore.Box3fData( sphere.bound() ),
								"object" : sphere,
							},
							"sphereBB" : {
								"bound" : IECore.Box3fData( sphere.bound() ),
								"object" : sphere,
							},
						},
					},
				},
			} ),
		)

		isolate = GafferScene.Isolate()
		isolate["in"].setInput( input["out"] )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/groupA/sphereAB" ] ) )
		isolate["filter"].setInput( filter["out"] )

		self.assertNotEqual( isolate["out"].childNamesHash( "/groupA" ), input["out"].childNamesHash( "/groupA" ) )
		self.assertEqual( isolate["out"].childNames( "/groupA" ), IECore.InternedStringVectorData( [ "sphereAB" ] ) )
		self.assertEqual( isolate["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "groupA" ] ) )

		filter["paths"].setValue( IECore.StringVectorData( [ "/groupA/sphereAA" ] ) )
		self.assertEqual( isolate["out"].childNames( "/groupA" ), IECore.InternedStringVectorData( [ "sphereAA" ] ) )
		self.assertEqual( isolate["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "groupA" ] ) )


	def testAdjustBounds( self ) :

		sphere1 = IECoreScene.SpherePrimitive()
		sphere2 = IECoreScene.SpherePrimitive( 2 )
		input = GafferSceneTest.CompoundObjectSource()
		input["in"].setValue(
			IECore.CompoundObject( {
				"bound" : IECore.Box3fData( sphere2.bound() ),
				"children" : {
					"group" : {
						"bound" : IECore.Box3fData( sphere2.bound() ),
						"children" : {
							"sphere1" : {
								"bound" : IECore.Box3fData( sphere1.bound() ),
								"object" : sphere1,
							},
							"sphere2" : {
								"bound" : IECore.Box3fData( sphere2.bound() ),
								"object" : sphere2,
							},
						},
					},
				},
			} ),
		)

		isolate = GafferScene.Isolate()
		isolate["in"].setInput( input["out"] )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/group/sphere1" ] ) )
		isolate["filter"].setInput( filter["out"] )

		self.assertEqual( isolate["out"].bound( "/" ), sphere2.bound() )
		self.assertEqual( isolate["out"].bound( "/group" ), sphere2.bound() )
		self.assertEqual( isolate["out"].bound( "/group/sphere1" ), sphere1.bound() )

		isolate["adjustBounds"].setValue( True )

		self.assertEqual( isolate["out"].bound( "/" ), sphere1.bound() )
		self.assertEqual( isolate["out"].bound( "/group" ), sphere1.bound() )
		self.assertEqual( isolate["out"].bound( "/group/sphere1" ), sphere1.bound() )

	def testSets( self ) :

		light1 = GafferSceneTest.TestLight()
		light2 = GafferSceneTest.TestLight()

		group = GafferScene.Group()
		group["in"][0].setInput( light1["out"] )
		group["in"][1].setInput( light2["out"] )

		lightSet = group["out"].set( "__lights" )
		self.assertEqual( set( lightSet.value.paths() ), set( [ "/group/light", "/group/light1" ] ) )

		isolate = GafferScene.Isolate()
		isolate["in"].setInput( group["out"] )

		lightSet = isolate["out"].set( "__lights" )
		self.assertEqual( set( lightSet.value.paths() ), set( [ "/group/light", "/group/light1" ] ) )

		filter = GafferScene.PathFilter()
		isolate["filter"].setInput( filter["out"] )

		lightSet = isolate["out"].set( "__lights" )
		self.assertEqual( set( lightSet.value.paths() ), set( [] ) )

		filter["paths"].setValue( IECore.StringVectorData( [ "/group/light" ] ) )
		lightSet = isolate["out"].set( "__lights" )
		self.assertEqual( set( lightSet.value.paths() ), set( [ "/group/light" ] ) )

		filter["paths"].setValue( IECore.StringVectorData( [ "/group/light*" ] ) )
		lightSet = isolate["out"].set( "__lights" )
		self.assertEqual( set( lightSet.value.paths() ), set( [ "/group/light", "/group/light1" ] ) )

	def testFrom( self ) :

		# - group1
		#	- group2
		#		- light1
		#		- light2
		#	- light3
		# - plane

		light1 = GafferSceneTest.TestLight()
		light1["name"].setValue( "light1" )
		light2 = GafferSceneTest.TestLight()
		light2["name"].setValue( "light2" )
		light3 = GafferSceneTest.TestLight()
		light3["name"].setValue( "light3" )

		group1 = GafferScene.Group()
		group1["name"].setValue( "group1" )
		group2 = GafferScene.Group()
		group2["name"].setValue( "group2" )

		group1["in"][0].setInput( group2["out"] )
		group1["in"][1].setInput( light3["out"] )
		group2["in"][0].setInput( light1["out"] )
		group2["in"][1].setInput( light2["out"] )

		plane = GafferScene.Plane()

		parent = GafferScene.Parent()
		parent["parent"].setValue( "/" )
		parent["in"].setInput( group1["out"] )
		parent["children"][0].setInput( plane["out"] )

		isolate = GafferScene.Isolate()
		isolate["in"].setInput( parent["out"] )

		self.assertSceneValid( isolate["out"] )
		self.assertEqual( isolate["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "group1", "plane" ] ) )
		self.assertEqual( isolate["out"].childNames( "/group1" ), IECore.InternedStringVectorData( [ "group2", "light3" ] ) )
		self.assertEqual( isolate["out"].childNames( "/group1/group2" ), IECore.InternedStringVectorData( [ "light1", "light2" ] ) )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/group1/group2/light1" ] ) )

		isolate["filter"].setInput( filter["out"] )

		self.assertSceneValid( isolate["out"] )
		self.assertEqual( isolate["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "group1" ] ) )
		self.assertEqual( isolate["out"].childNames( "/group1" ), IECore.InternedStringVectorData( [ "group2" ] ) )
		self.assertEqual( isolate["out"].childNames( "/group1/group2" ), IECore.InternedStringVectorData( [ "light1" ] ) )

		isolate["from"].setValue( "/group1" )

		self.assertSceneValid( isolate["out"] )
		self.assertEqual( isolate["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "group1", "plane" ] ) )
		self.assertEqual( isolate["out"].childNames( "/group1" ), IECore.InternedStringVectorData( [ "group2" ] ) )
		self.assertEqual( isolate["out"].childNames( "/group1/group2" ), IECore.InternedStringVectorData( [ "light1" ] ) )

		isolate["from"].setValue( "/group1/group2" )

		self.assertSceneValid( isolate["out"] )
		self.assertEqual( isolate["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "group1", "plane" ] ) )
		self.assertEqual( isolate["out"].childNames( "/group1" ), IECore.InternedStringVectorData( [ "group2", "light3" ] ) )
		self.assertEqual( isolate["out"].childNames( "/group1/group2" ), IECore.InternedStringVectorData( [ "light1" ] ) )

	def testIsolateNothing( self ) :

		sphere = GafferScene.Sphere()
		sphere["sets"].setValue("sphereSet")

		i = GafferScene.Isolate()
		i["in"].setInput( sphere["out"] )
		pathFilter = GafferScene.PathFilter()
		i["filter"].setInput( pathFilter["out"] )
		pathFilter["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )

		self.assertEqual( i["out"].childNames("/"), IECore.InternedStringVectorData( [ "sphere" ] ) )
		self.assertEqual( i["out"].set( "sphereSet" ).value.paths(), ["/sphere"] )

		pathFilter["paths"].setValue( IECore.StringVectorData() )

		self.assertEqual( i["out"].set( "sphereSet" ).value.paths(), [] )
		self.assertEqual( i["out"].childNames("/"), IECore.InternedStringVectorData() )

	def testKeepLightsAndCameras( self ) :

		# - group
		#    - light
		#    - camera
		#    - lightFilter
		#    - model1
		#       - sphere
		#       - light
		#       - lightFilter
		#    - model2
		#       - sphere
		#       - light
		#       - lightFilter

		light = GafferSceneTest.TestLight()
		light["sets"].setValue( "lightsAndSpheres" )

		lightFilter = GafferSceneTest.TestLightFilter()
		lightFilter["sets"].setValue( "lightsAndSpheres" )

		sphere = GafferScene.Sphere()
		sphere["sets"].setValue( "lightsAndSpheres" )

		camera = GafferScene.Camera()

		model1 = GafferScene.Group()
		model1["in"][0].setInput( sphere["out"] )
		model1["in"][1].setInput( light["out"] )
		model1["in"][2].setInput( lightFilter["out"] )
		model1["name"].setValue( "model1" )

		model2 = GafferScene.Group()
		model2["in"][0].setInput( sphere["out"] )
		model2["in"][1].setInput( light["out"] )
		model2["in"][2].setInput( lightFilter["out"] )
		model2["name"].setValue( "model2" )

		group = GafferScene.Group()
		group["in"][0].setInput( light["out"] )
		group["in"][1].setInput( lightFilter["out"] )
		group["in"][2].setInput( camera["out"] )
		group["in"][3].setInput( model1["out"] )
		group["in"][4].setInput( model2["out"] )

		self.assertSceneValid( group["out"] )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/group/model1" ] ) )

		isolate = GafferScene.Isolate()
		isolate["in"].setInput( group["out"] )
		isolate["filter"].setInput( filter["out"] )

		# Keep neither

		self.assertSceneValid( isolate["out"] )

		self.assertTrue( isolate["out"].exists( "/group/model1/sphere" ) )
		self.assertTrue( isolate["out"].exists( "/group/model1/light" ) )
		self.assertTrue( isolate["out"].exists( "/group/model1/lightFilter" ) )
		self.assertTrue( isolate["out"].exists( "/group/model1" ) )

		self.assertFalse( isolate["out"].exists( "/group/model2/sphere" ) )
		self.assertFalse( isolate["out"].exists( "/group/model2/light" ) )
		self.assertFalse( isolate["out"].exists( "/group/model2/lightFilter" ) )
		self.assertFalse( isolate["out"].exists( "/group/model2" ) )

		self.assertFalse( isolate["out"].exists( "/group/light" ) )
		self.assertFalse( isolate["out"].exists( "/group/lightFilter" ) )
		self.assertFalse( isolate["out"].exists( "/group/camera" ) )

		self.assertEqual( isolate["out"].set( "__lights" ).value.paths(), [ "/group/model1/light" ] )
		self.assertEqual( isolate["out"].set( "__lightFilters" ).value.paths(), [ "/group/model1/lightFilter" ] )
		self.assertEqual( isolate["out"].set( "__cameras" ).value.paths(), [] )
		self.assertEqual( isolate["out"].set( "lightsAndSpheres" ).value, IECore.PathMatcher( [ "/group/model1/sphere", "/group/model1/light", "/group/model1/lightFilter" ] ) )

		self.assertNotEqual( isolate["out"].setHash( "__lights" ), group["out"].setHash( "__lights" ) )
		self.assertNotEqual( isolate["out"].setHash( "__lightFilters" ), group["out"].setHash( "__lightFilters" ) )
		self.assertNotEqual( isolate["out"].setHash( "__cameras" ), group["out"].setHash( "__cameras" ) )

		# Keep lights

		isolate["keepLights"].setValue( True )

		self.assertSceneValid( isolate["out"] )

		self.assertFalse( isolate["out"].exists( "/group/camera" ) )

		self.assertEqual( isolate["out"].set( "__lights" ), group["out"].set( "__lights" ) )
		self.assertEqual( isolate["out"].set( "__lightFilters" ), group["out"].set( "__lightFilters" ) )
		self.assertEqual( isolate["out"].set( "__cameras" ).value.paths(), [] )
		self.assertEqual(
			isolate["out"].set("lightsAndSpheres" ).value,
			IECore.PathMatcher(
				[ "/group/model1/sphere" ] +
				group["out"].set( "__lights" ).value.paths() +
				group["out"].set( "__lightFilters" ).value.paths()
			)
		)

		self.assertEqual( isolate["out"].setHash( "__lights" ), group["out"].setHash( "__lights" ) )
		self.assertEqual( isolate["out"].setHash( "__lightFilters" ), group["out"].setHash( "__lightFilters" ) )
		self.assertNotEqual( isolate["out"].setHash( "__cameras" ), group["out"].setHash( "__cameras" ) )

		# Keep cameras too

		isolate["keepCameras"].setValue( True )

		self.assertSceneValid( isolate["out"] )

		self.assertTrue( isolate["out"].exists( "/group/camera" ) )

		self.assertEqual( isolate["out"].set( "__lights" ), group["out"].set( "__lights" ) )
		self.assertEqual( isolate["out"].set( "__cameras" ), group["out"].set( "__cameras" ) )
		self.assertEqual(
			isolate["out"].set("lightsAndSpheres" ).value,
			IECore.PathMatcher(
				[ "/group/model1/sphere" ] +
				group["out"].set( "__lights" ).value.paths() +
				group["out"].set( "__lightFilters" ).value.paths()
			)
		)

		self.assertEqual( isolate["out"].setHash( "__lights" ), group["out"].setHash( "__lights" ) )
		self.assertEqual( isolate["out"].setHash( "__lightFilters" ), group["out"].setHash( "__lightFilters" ) )
		self.assertEqual( isolate["out"].setHash( "__cameras" ), group["out"].setHash( "__cameras" ) )

	def testKeepLightsAndCamerasHashing( self ):

		# - group
		#    - cameraGroup
		#       - camera

		camera = GafferScene.Camera()

		cameraGroup = GafferScene.Group()
		cameraGroup["name"].setValue( "cameraGroup" )
		cameraGroup["in"][0].setInput( camera["out"] )

		group = GafferScene.Group()
		group["in"][0].setInput( cameraGroup["out"] )

		filter = GafferScene.PathFilter()

		isolate = GafferScene.Isolate()
		isolate["in"].setInput( group["out"] )
		isolate["filter"].setInput( filter["out"] )

		isolate["keepCameras"].setValue( True )

		self.assertTrue( isolate["out"].exists( "/group/cameraGroup/camera" ) )

	def testSetFilter( self ) :

		sphere = GafferScene.Sphere()
		sphere["sets"].setValue( "A" )

		filter = GafferScene.SetFilter()
		filter["setExpression"].setValue( "A" )

		isolate = GafferScene.Isolate()
		isolate["in"].setInput( sphere["out"] )
		isolate["filter"].setInput( filter["out"] )

		self.assertSceneValid( isolate["out"] )
		self.assertTrue( isolate["out"].exists( "/sphere" ) )

if __name__ == "__main__":
	unittest.main()
