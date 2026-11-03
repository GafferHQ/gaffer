##########################################################################
#
#  Copyright (c) 2020, Cinesite VFX Ltd. All rights reserved.
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

import imath
import inspect

import IECore

import Gaffer
import GafferScene
import GafferSceneTest
import GafferTest

class MergeScenesTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		sphereFilter = GafferScene.PathFilter()
		sphereFilter["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )

		sphere = GafferScene.Sphere()
		sphere["sets"].setValue( "sphere both" )

		sphereAttributes = GafferScene.CustomAttributes()
		sphereAttributes["in"].setInput( sphere["out"] )
		sphereAttributes["filter"].setInput( sphereFilter["out"] )
		sphereAttributes["attributes"].addChild( Gaffer.NameValuePlug( "testAttr1", 1 ) )
		sphereAttributes["attributes"].addChild( Gaffer.NameValuePlug( "testAttr2", 2 ) )

		bigSphere = GafferScene.Sphere()
		bigSphere["radius"].setValue( 2 )
		bigSphere["transform"]["translate"]["x"].setValue( 1 )
		bigSphere["sets"].setValue( "bigSphere" )

		bigSphereAttributes = GafferScene.CustomAttributes()
		bigSphereAttributes["in"].setInput( bigSphere["out"] )
		bigSphereAttributes["filter"].setInput( sphereFilter["out"] )
		bigSphereAttributes["attributes"].addChild( Gaffer.NameValuePlug( "testAttr2", 4 ) )
		bigSphereAttributes["attributes"].addChild( Gaffer.NameValuePlug( "testAttr3", 3 ) )

		cube = GafferScene.Cube()
		cube["sets"].setValue( "cube both" )

		merge = GafferScene.MergeScenes()
		merge["in"][0].setInput( sphereAttributes["out"] )
		merge["in"][1].setInput( cube["out"] )
		merge["in"][2].setInput( bigSphereAttributes["out"] )

		self.assertSceneValid( merge["out"] )

		# Hierarchy
		# =========

		self.assertEqual(
			merge["out"].childNames( "/" ),
			IECore.InternedStringVectorData( [ "sphere", "cube" ] ),
		)

		self.assertEqual(
			merge["out"].childNames( "/sphere" ),
			IECore.InternedStringVectorData(),
		)

		self.assertEqual(
			merge["out"].childNames( "/cube" ),
			IECore.InternedStringVectorData(),
		)

		# Transform
		# =========

		# `Keep`
		self.assertEqual( merge["transformMode"].getValue(), merge.Mode.Keep )
		self.assertEqual( merge["out"].transform( "/" ), imath.M44f() )
		self.assertEqual( merge["out"].transform( "/sphere" ), imath.M44f() )
		self.assertEqual( merge["out"].transform( "/sphere" ), sphere["out"].transform( "/sphere" ) )
		self.assertEqual( merge["out"].transformHash( "/sphere" ), sphere["out"].transformHash( "/sphere" ) )
		self.assertEqual( merge["out"].transform( "/cube" ), cube["out"].transform( "/cube" ) )
		self.assertEqual( merge["out"].transformHash( "/cube" ), cube["out"].transformHash( "/cube" ) )
		self.assertSceneValid( merge["out"] )

		# `Replace`
		merge["transformMode"].setValue( merge.Mode.Replace )
		self.assertEqual( merge["out"].transform( "/" ), imath.M44f() )
		self.assertEqual( merge["out"].transform( "/sphere" ), bigSphere["out"].transform( "/sphere" ) )
		self.assertEqual( merge["out"].transformHash( "/sphere" ), bigSphere["out"].transformHash( "/sphere" ) )
		self.assertEqual( merge["out"].transform( "/cube" ), cube["out"].transform( "/cube" ) )
		self.assertEqual( merge["out"].transformHash( "/cube" ), cube["out"].transformHash( "/cube" ) )
		self.assertSceneValid( merge["out"] )

		# Objects
		# =======

		# `Keep`
		self.assertEqual( merge["objectMode"].getValue(), merge.Mode.Keep )
		self.assertEqual( merge["out"].object( "/sphere" ), sphere["out"].object( "/sphere" ) )
		self.assertEqual( merge["out"].objectHash( "/sphere" ), sphere["out"].objectHash( "/sphere" ) )
		self.assertEqual( merge["out"].object( "/cube" ), cube["out"].object( "/cube" ) )
		self.assertEqual( merge["out"].objectHash( "/cube" ), cube["out"].objectHash( "/cube" ) )

		# `Replace`
		merge["objectMode"].setValue( merge.Mode.Replace )
		self.assertEqual( merge["out"].object( "/" ), IECore.NullObject() )
		self.assertEqual( merge["out"].object( "/sphere" ), bigSphere["out"].object( "/sphere") )
		self.assertEqual( merge["out"].object( "/cube" ), cube["out"].object( "/cube") )
		self.assertSceneValid( merge["out"] )

		# Combination of 2 input locations, hash can't be passed through.
		self.assertNotEqual( merge["out"].objectHash( "/sphere" ), sphere["out"].objectHash( "/sphere") )
		self.assertNotEqual( merge["out"].objectHash( "/sphere" ), bigSphere["out"].objectHash( "/sphere") )
		# Single input location, hash should be passed through, and cache
		# entries shared.
		self.assertEqual( merge["out"].objectHash( "/cube" ), cube["out"].objectHash( "/cube") )
		self.assertTrue(
			merge["out"].object( "/cube", _copy = False ).isSame(
				cube["out"].object( "/cube", _copy = False )
			)
		)

		# Attributes
		# ==========

		# `Keep`
		self.assertEqual( merge["attributesMode"].getValue(), merge.Mode.Keep )
		self.assertEqual( merge["out"].attributes( "/sphere" ), sphereAttributes["out"].attributes( "/sphere" ) )
		self.assertEqual( merge["out"].attributesHash( "/sphere" ), sphereAttributes["out"].attributesHash( "/sphere" ) )

		# `Merge`
		merge["attributesMode"].setValue( merge.Mode.Merge )
		self.assertEqual( merge["out"].attributes( "/" ), IECore.CompoundObject() )
		self.assertEqual(
			merge["out"].attributes( "/sphere" ),
			IECore.CompoundObject( {
				"testAttr1" : IECore.IntData( 1 ),
				"testAttr2" : IECore.IntData( 4 ),
				"testAttr3" : IECore.IntData( 3 )
			} )
		)
		self.assertEqual( merge["out"].attributes( "/cube" ), IECore.CompoundObject() )

		# Combination of 2 input locations, hash can't be passed through.
		self.assertNotEqual( merge["out"].attributesHash( "/sphere" ), sphere["out"].attributesHash( "/sphere") )
		self.assertNotEqual( merge["out"].attributesHash( "/sphere" ), bigSphere["out"].attributesHash( "/sphere") )
		# Single input location, hash should be passed through, and cache
		# entries shared.
		self.assertEqual( merge["out"].attributesHash( "/cube" ), cube["out"].attributesHash( "/cube") )
		self.assertTrue(
			merge["out"].attributes( "/cube", _copy = False ).isSame(
				cube["out"].attributes( "/cube", _copy = False )
			)
		)

		# `Replace`
		merge["attributesMode"].setValue( merge.Mode.Replace )
		self.assertEqual( merge["out"].attributes( "/sphere" ), bigSphereAttributes["out"].attributes( "/sphere" ) )
		self.assertEqual( merge["out"].attributesHash( "/sphere" ), bigSphereAttributes["out"].attributesHash( "/sphere" ) )

		# Sets
		# ====

		# Sets are always merged

		self.assertEqual( merge["out"].setNames(), IECore.InternedStringVectorData( [ "sphere", "both", "cube", "bigSphere" ] ) )
		self.assertEqual( merge["out"].set( "sphere" ).value, IECore.PathMatcher( [ "/sphere" ] ) )
		self.assertEqual( merge["out"].set( "cube" ).value, IECore.PathMatcher( [ "/cube" ] ) )
		self.assertEqual( merge["out"].set( "both" ).value, IECore.PathMatcher( [ "/sphere", "/cube" ] ) )
		self.assertEqual( merge["out"].set( "bigSphere" ).value, IECore.PathMatcher( [ "/sphere" ] ) )

	def testGlobals( self ) :

		a = GafferScene.CustomOptions()
		a["options"].addChild( Gaffer.NameValuePlug( "test1", 1 ) )
		a["options"].addChild( Gaffer.NameValuePlug( "test2", 2 ) )

		b = GafferScene.CustomOptions()
		b["options"].addChild( Gaffer.NameValuePlug( "test2", 4 ) )
		b["options"].addChild( Gaffer.NameValuePlug( "test3", 3 ) )

		merge = GafferScene.MergeScenes()
		merge["in"][0].setInput( a["out"] )
		merge["in"][1].setInput( b["out"] )

		# `Keep`

		self.assertEqual( merge["globalsMode"].getValue(), merge.Mode.Keep )
		self.assertEqual( merge["out"].globals(), a["out"].globals() )
		self.assertEqual( merge["out"].globalsHash(), a["out"].globalsHash() )

		# `Replace`

		merge["globalsMode"].setValue( merge.Mode.Replace )
		self.assertEqual( merge["out"].globals(), b["out"].globals() )
		self.assertEqual( merge["out"].globalsHash(), b["out"].globalsHash() )

		# `Merge`

		merge["globalsMode"].setValue( merge.Mode.Merge )
		mergedGlobals = a["out"].globals()
		mergedGlobals.update( b["out"].globals() )
		self.assertEqual( merge["out"].globals(), mergedGlobals )

	def testSingleInputPassThrough( self ) :

		sphere = GafferSceneTest.TestLight()
		sphere.loadShader( "simpleLight" )
		sphere["transform"]["translate"].setValue( imath.V3f( 1, 2, 3 ) )
		sphere["sets"].setValue( "A" )
		cube = GafferScene.Cube()

		group = GafferScene.Group()
		group["in"][0].setInput( sphere["out"] )
		group["in"][1].setInput( sphere["out"] )

		merge = GafferScene.MergeScenes()
		merge["in"][0].setInput( group["out"] )

		self.assertScenesEqual( merge["out"], group["out"] )
		self.assertSceneHashesEqual( merge["out"], group["out"] )

		merge["in"][1].setInput( group["out"] )
		merge["in"][0].setInput( None )

		self.assertScenesEqual( merge["out"], group["out"] )
		self.assertSceneHashesEqual( merge["out"], group["out"] )

	def testFirstInputEmptyPassThrough( self ) :

		merge = GafferScene.MergeScenes()

		emptyScene = GafferScene.ScenePlug()
		merge["in"][0].setInput( emptyScene )

		light = GafferSceneTest.TestLight()
		light.loadShader( "simpleLight" )
		merge["in"][1].setInput( light["out"] )

		self.assertScenesEqual( merge["out"], light["out"] )
		self.assertSceneHashesEqual( merge["out"], light["out"], checks = self.allSceneChecks - { "sets" } )

	def testNoInputsPassThrough( self ) :

		merge = GafferScene.MergeScenes()
		self.assertScenesEqual( merge["in"][0], merge["out"] )
		self.assertSceneHashesEqual(
			merge["in"][0], merge["out"],
			# Can't expect transform hash to be identical, because
			# `SceneNode::hashTransform()` isn't called for the root.
			checks = self.allSceneChecks - { "transform" }
		)

	def testNullObject( self ) :

		sphere = GafferScene.Sphere()

		group = GafferScene.Group()
		group["name"].setValue( "sphere" )

		merge = GafferScene.MergeScenes()
		merge["in"][0].setInput( sphere["out"] )
		merge["in"][1].setInput( group["out"] )
		merge["objectMode"].setValue( merge.Mode.Replace )

		self.assertEqual( merge["out"].object( "/sphere" ), sphere["out"].object( "/sphere" ) )

	def testNoRedundantEvaluations( self ) :

		sphere1 = GafferScene.Sphere()

		sphere2 = GafferScene.Sphere()
		sphere2["radius"].setValue( 2 )
		sphere2["transform"]["translate"]["x"].setValue( 2 )

		merge = GafferScene.MergeScenes()
		merge["in"][0].setInput( sphere1["out"] )
		merge["in"][1].setInput( sphere2["out"] )
		merge["objectMode"].setValue( merge.Mode.Replace )
		merge["transformMode"].setValue( merge.Mode.Replace )

		# Object
		# ======

		with Gaffer.PerformanceMonitor() as pm :
			merge["out"].object( "/sphere" )

		self.assertEqual( pm.plugStatistics( sphere2["out"]["object"] ).hashCount, 1 )
		self.assertEqual( pm.plugStatistics( sphere2["out"]["object"] ).computeCount, 1 )

		self.assertEqual( pm.plugStatistics( sphere1["out"]["object"] ).hashCount, 1 )
		# No need to compute `sphere1.out.object` because `sphere2.out.object` wins.
		self.assertEqual( pm.plugStatistics( sphere1["out"]["object"] ).computeCount, 0 )

		# Transform
		# =========

		with Gaffer.PerformanceMonitor() as pm :
			merge["out"].transform( "/sphere" )

		self.assertEqual( pm.plugStatistics( sphere2["out"]["transform"] ).hashCount, 1 )
		self.assertEqual( pm.plugStatistics( sphere2["out"]["transform"] ).computeCount, 1 )

		# No need to hash or compute `sphere1.out.transform` because `sphere2.out.transform` wins.
		self.assertEqual( pm.plugStatistics( sphere1["out"]["transform"] ).hashCount, 0 )
		self.assertEqual( pm.plugStatistics( sphere1["out"]["transform"] ).computeCount, 0 )

	def testBounds( self ) :

		sphere = GafferScene.Sphere()
		sphere["transform"]["translate"]["x"].setValue( 5 )

		bigSphere = GafferScene.Sphere()
		bigSphere["radius"].setValue( 2 )

		merge = GafferScene.MergeScenes()
		merge["in"][0].setInput( sphere["out"] )
		merge["in"][1].setInput( bigSphere["out"] )

		# Transform and object both coming from `bigSphere`.

		merge["transformMode"].setValue( merge.Mode.Replace )
		merge["objectMode"].setValue( merge.Mode.Replace )
		self.assertSceneValid( merge["out"] )
		self.assertEqual( merge["out"].bound( "/" ), bigSphere["out"].bound( "/" ) )
		self.assertEqual( merge["out"].bound( "/sphere" ), bigSphere["out"].bound( "/sphere" ) )

		# Just object coming from `bigSphere`.

		merge["transformMode"].setValue( merge.Mode.Keep )
		self.assertSceneValid( merge["out"] )
		self.assertEqual( merge["out"].bound( "/" ), imath.Box3f( imath.V3f( 3, -2, -2 ), imath.V3f( 7, 2, 2 ) ) )
		self.assertEqual( merge["out"].bound( "/sphere" ), bigSphere["out"].bound( "/sphere" ) )

		# Just transform coming from `bigSphere`.

		merge["transformMode"].setValue( merge.Mode.Replace )
		merge["objectMode"].setValue( merge.Mode.Keep )
		self.assertSceneValid( merge["out"] )
		self.assertEqual( merge["out"].bound( "/" ), imath.Box3f( imath.V3f( -1 ), imath.V3f( 1 ) ) )
		self.assertEqual( merge["out"].bound( "/sphere" ), sphere["out"].bound( "/sphere" ) )

		# Neither transforms or objects being merged.

		merge["transformMode"].setValue( merge.Mode.Keep )
		self.assertSceneValid( merge["out"] )
		self.assertEqual( merge["out"].bound( "/" ), sphere["out"].bound( "/" ) )
		self.assertEqual( merge["out"].bound( "/sphere" ), sphere["out"].bound( "/sphere" ) )

	def testBoundsFailureCase( self ):

		# Test simplified from a more complex and general case to highlight a specific situation
		# where we previously failed to take into account one of the two cubes.
		cube = GafferScene.Cube()

		groupA = GafferScene.Group()
		groupA["in"][0].setInput( cube["out"] )
		groupA["name"].setValue( 'a' )
		groupA["transform"]["translate"].setValue( imath.V3f( 1, 0, 0 ) )

		group1 = GafferScene.Group()
		group1["in"][0].setInput( groupA["out"] )

		groupB = GafferScene.Group()
		groupB["in"][0].setInput( cube["out"] )
		groupB["name"].setValue( 'b' )
		groupB["transform"]["translate"].setValue( imath.V3f( -1, 0, 0 ) )

		group2 = GafferScene.Group()
		group2["in"][0].setInput( groupB["out"] )

		mergeScenes = GafferScene.MergeScenes()
		mergeScenes["in"][0].setInput( group1["out"] )
		mergeScenes["in"][1].setInput( group2["out"] )
		# Connect one input twice - previously, we would leave an object out of mergedDescendantsBound
		# if it was present in multiple inputs.
		mergeScenes["in"][2].setInput( group2["out"] )

		self.assertEqual(
			mergeScenes["out"].bound( "/group" ),
			imath.Box3f( imath.V3f(-1.5, -0.5, -0.5),  imath.V3f(1.5, 0.5, 0.5) )
		)

	def testBoundDoesntDependOnObjectsUnnecessarily( self ) :

		# Input 0      Input 1
		# =======      =======
		#
		# /group       /group
		#   /sphere       /sphere
		#   /plane        /innerGroup
		#                     /cube

		input0Sphere = GafferScene.Sphere( "input0Sphere" )
		input0Plane = GafferScene.Plane( "input0Plane" )
		input0Group = GafferScene.Group( "input0Group" )
		input0Group["in"][0].setInput( input0Sphere["out"] )
		input0Group["in"][1].setInput( input0Plane["out"] )

		input1Sphere = GafferScene.Sphere( "input1Sphere" )
		input1Cube = GafferScene.Cube( "input1Cube" )
		input1Cube["transform"]["translate"]["x"].setValue( 10 )
		input1InnerGroup = GafferScene.Group( "input1InnerGroup" )
		input1InnerGroup["name"].setValue( "innerGroup" )
		input1InnerGroup["in"][0].setInput( input1Cube["out"] )
		input1Group = GafferScene.Group( "input1Group" )
		input1Group["in"][0].setInput( input1Sphere["out"] )
		input1Group["in"][1].setInput( input1InnerGroup["out"] )

		merge = GafferScene.MergeScenes()
		merge["in"][0].setInput( input0Group["out"] )
		merge["in"][1].setInput( input1Group["out"] )

		# If we're only taking transforms and objects from
		# the first active input, then we should be able
		# to compute the bounds purely from input bounds
		# and transforms, without ever needing to compute
		# any objects.

		merge["transformMode"].setValue( merge.Mode.Keep )
		merge["objectMode"].setValue( merge.Mode.Keep )

		with Gaffer.PerformanceMonitor() as pm :

			for path in [
				"/",
				"/group",
				"/group/sphere",
				"/group/plane",
				"/group/innerGroup",
				"/group/innerGroup/cube"
			] :
				self.assertTrue( GafferScene.SceneAlgo.exists( merge["out"], path ) )
				merge["out"].bound( path )

		computedPlugs = [ plug.fullName() for plug in pm.allStatistics() ]
		computedObjectPlugs = [ plug for plug in computedPlugs if plug.endswith( ".object" ) ]
		self.assertEqual( computedObjectPlugs, [] )

		# And the bounds should be valid

		self.assertSceneValid( merge["out"] )

		# And should update if the transforms change

		input1Cube["transform"]["translate"]["x"].setValue( 20 )
		self.assertSceneValid( merge["out"] )
		input1InnerGroup["transform"]["translate"]["x"].setValue( 20 )
		self.assertSceneValid( merge["out"] )

	def testDisabledSceneReader( self ) :

		sceneReader1 = GafferScene.SceneReader()
		sceneReader1["fileName"].setValue( "${GAFFER_ROOT}/python/GafferSceneTest/alembicFiles/cube.abc" )

		sceneReader2 = GafferScene.SceneReader()
		sceneReader2["fileName"].setValue( "${GAFFER_ROOT}/python/GafferSceneTest/alembicFiles/groupedPlane.abc" )

		merge = GafferScene.MergeScenes()
		merge["in"][0].setInput( sceneReader1["out"] )
		merge["in"][1].setInput( sceneReader2["out"] )
		self.assertSceneValid( merge["out"] )
		self.assertEqual( merge["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "group1", "group" ] ) )

		sceneReader2["enabled"].setValue( False )
		self.assertSceneValid( merge["out"] )
		self.assertEqual( merge["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "group1" ] ) )

	def testFirstInputUnconnected( self ) :

		sphere = GafferScene.Sphere()
		sphere["sets"].setValue( "A" )

		merge = GafferScene.MergeScenes()
		merge["in"][1].setInput( sphere["out"] )

		self.assertSceneValid( merge["out"] )
		self.assertScenesEqual( sphere["out"], merge["out"] )
		self.assertSceneHashesEqual( sphere["out"], merge["out"] )

	def testCollectEmptyScenes( self ) :

		sphere = GafferScene.Sphere()
		sphere["sets"].setValue( "A" )

		switch = Gaffer.Switch()
		switch.setup( sphere["out"] )
		switch["in"].resize( 2 )
		switch["in"][1].setInput( sphere["out"] )

		switch["expression"] = Gaffer.Expression()
		switch["expression"].setExpression( 'parent["index"] = context.get( "merge:index" )', "python" )

		merge = GafferScene.MergeScenes()
		merge["in"][1].setInput( switch["out"] )
		merge["mode"].setValue( GafferScene.MergeScenes.MergeMode.Collect )
		merge["contextValues"].setValue( IECore.StringVectorData( [ "0", "1", "2" ] ) )

		self.assertSceneValid( merge["out"] )

		# The only valid input scene is the sphere, the rest are empty, and don't affect
		# the result
		self.assertScenesEqual( sphere["out"], merge["out"] )

		# We can't check self.assertSceneHashesEqual( sphere["out"], merge["out"] )
		# here, however, because the empty scene we get from the switch for unused
		# contexts is still "connected", so it still affects the hash.

	def testNoContexts( self ) :

		sphere = GafferScene.Sphere()
		sphere["sets"].setValue( "A" )

		merge = GafferScene.MergeScenes()
		merge["in"][0].setInput( sphere["out"] )
		merge["mode"].setValue( GafferScene.MergeScenes.MergeMode.Collect )

		unconnectedScene = GafferScene.ScenePlug()

		self.assertSceneValid( merge["out"] )
		self.assertScenesEqual( merge["out"], unconnectedScene )
		self.assertSceneHashesEqual( merge["out"], unconnectedScene )

	def testMaxInputs( self ) :

		merge = GafferScene.MergeScenes()
		spheres = []
		groups = []

		# The max size of 32 used to be a requirement of the data structures we were using.
		# Now that we support Collect mode, we support arbitrarily many inputs, and we could
		# remove the restriction on the size of the in plug. I haven't yet just for consistency,
		# but maybe it's worth updating.
		for i in range( 0, merge["in"].maxSize() ) :
			sphere = GafferScene.Sphere()
			sphere["name"].setValue( "sphere{}".format( i ) )
			sphere["sets"].setValue( "set{}".format( i ) )
			group = GafferScene.Group()
			group["in"][0].setInput( sphere["out"] )
			merge["in"][i].setInput( group["out"] )
			spheres.append( sphere )
			groups.append( group )

		self.assertSceneValid( merge["out"] )
		self.assertEqual(
			list( merge["out"].childNames( "/group" ) ),
			[ "sphere{}".format( i ) for i in range( 0, merge["in"].maxSize() ) ]
		)
		self.assertEqual(
			list( merge["out"].setNames() ),
			[ "set{}".format( i ) for i in range( 0, merge["in"].maxSize() ) ]
		)

	def testCollectMode( self ) :
		# Run all the tests from test() again, but checking that using Collect mode to read the
		# inputs from a switch has identical results to connecting to the inputs of the SceneMerge
		# in Standard mode

		sphereFilter = GafferScene.PathFilter()
		sphereFilter["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )

		sphere = GafferScene.Sphere()
		sphere["sets"].setValue( "sphere both" )

		sphereAttributes = GafferScene.CustomAttributes()
		sphereAttributes["in"].setInput( sphere["out"] )
		sphereAttributes["filter"].setInput( sphereFilter["out"] )
		sphereAttributes["attributes"].addChild( Gaffer.NameValuePlug( "testAttr1", 1 ) )
		sphereAttributes["attributes"].addChild( Gaffer.NameValuePlug( "testAttr2", 2 ) )

		bigSphere = GafferScene.Sphere()
		bigSphere["radius"].setValue( 2 )
		bigSphere["transform"]["translate"]["x"].setValue( 1 )
		bigSphere["sets"].setValue( "bigSphere" )

		bigSphereAttributes = GafferScene.CustomAttributes()
		bigSphereAttributes["in"].setInput( bigSphere["out"] )
		bigSphereAttributes["filter"].setInput( sphereFilter["out"] )
		bigSphereAttributes["attributes"].addChild( Gaffer.NameValuePlug( "testAttr2", 4 ) )
		bigSphereAttributes["attributes"].addChild( Gaffer.NameValuePlug( "testAttr3", 3 ) )

		cube = GafferScene.Cube()
		cube["sets"].setValue( "cube both" )

		refMerge = GafferScene.MergeScenes()
		refMerge["in"][0].setInput( sphereAttributes["out"] )
		refMerge["in"][1].setInput( cube["out"] )
		refMerge["in"][2].setInput( bigSphereAttributes["out"] )

		switch = Gaffer.Switch()
		switch.setup( sphere["out"] )
		switch["in"].resize( 2 )
		switch["in"][0].setInput( sphereAttributes["out"] )
		switch["in"][1].setInput( cube["out"] )
		switch["in"][2].setInput( bigSphereAttributes["out"] )

		switch["expression"] = Gaffer.Expression()
		switch["expression"].setExpression( 'parent["index"] = "abc".find( context.get( "merge:value" ) )', "python" )

		merge = GafferScene.MergeScenes()
		merge["in"][0].setInput( switch["out"] )
		merge["mode"].setValue( GafferScene.MergeScenes.MergeMode.Collect )
		merge["contextValues"].setValue( IECore.StringVectorData( [ "a", "b", "c" ] ) )

		self.assertSceneValid( merge["out"] )
		self.assertScenesEqual( merge["out"], refMerge["out"] )
		self.assertSceneHashesEqual( merge["out"], refMerge["out"] )

		switch["expression"].setExpression( 'parent["index"] = context.get( "merge:index" )', "python" )

		self.assertSceneValid( merge["out"] )
		self.assertScenesEqual( merge["out"], refMerge["out"] )
		self.assertSceneHashesEqual( merge["out"], refMerge["out"] )

		merge["transformMode"].setValue( merge.Mode.Replace )
		refMerge["transformMode"].setValue( merge.Mode.Replace )

		self.assertSceneValid( merge["out"] )
		self.assertScenesEqual( merge["out"], refMerge["out"] )
		self.assertSceneHashesEqual( merge["out"], refMerge["out"] )

		merge["objectMode"].setValue( merge.Mode.Replace )
		refMerge["objectMode"].setValue( merge.Mode.Replace )

		self.assertSceneValid( merge["out"] )
		self.assertScenesEqual( merge["out"], refMerge["out"] )
		self.assertSceneHashesEqual( merge["out"], refMerge["out"] )

		merge["attributesMode"].setValue( merge.Mode.Merge )
		refMerge["attributesMode"].setValue( merge.Mode.Merge )

		self.assertSceneValid( merge["out"] )
		self.assertScenesEqual( merge["out"], refMerge["out"] )
		self.assertSceneHashesEqual( merge["out"], refMerge["out"] )

		merge["attributesMode"].setValue( merge.Mode.Replace )
		refMerge["attributesMode"].setValue( merge.Mode.Replace )

		self.assertSceneValid( merge["out"] )
		self.assertScenesEqual( merge["out"], refMerge["out"] )
		self.assertSceneHashesEqual( merge["out"], refMerge["out"] )

		# Try disconnecting each of the 3 inputs
		for i in range( 3 ):
			refMerge["in"][0].setInput( sphereAttributes["out"] )
			refMerge["in"][1].setInput( cube["out"] )
			refMerge["in"][2].setInput( bigSphereAttributes["out"] )

			switch["in"][0].setInput( sphereAttributes["out"] )
			switch["in"][1].setInput( cube["out"] )
			switch["in"][2].setInput( bigSphereAttributes["out"] )

			refMerge["in"][i].setInput( None )
			switch["in"][i].setInput( None )

			# The hashes don't match with a missing input ( since on the reference merge
			# it skips a disconnected input, but the switch is still connected for every
			# context, even if there's no input on the switch ), but all the computed values
			# should still match
			self.assertSceneValid( merge["out"] )
			self.assertScenesEqual( merge["out"], refMerge["out"] )

	def testCollectWithMultipleInputs( self ) :

		sphereFilter = GafferScene.PathFilter()
		sphereFilter["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )

		sphere = GafferScene.Sphere()

		sphere["expression"] = Gaffer.Expression()
		sphere["expression"].setExpression( inspect.cleandoc( """
			parent["transform"]["translate"] = imath.V3f(
				context.get( "merge:index" ),
				1 if context.get( "isSecondInput", "" ) else 0,
				0
			)
		""" ), "python" )

		sphereAttributes = GafferScene.CustomAttributes()
		sphereAttributes["in"].setInput( sphere["out"] )
		sphereAttributes["filter"].setInput( sphereFilter["out"] )
		sphereAttributes["attributes"].addChild( Gaffer.NameValuePlug( "test${merge:value}:${isSecondInput}", 1 ) )

		contextVariables = Gaffer.ContextVariables()
		contextVariables["variables"].addChild( Gaffer.NameValuePlug( "isSecondInput", "second" ) )

		contextVariables.setup( sphereAttributes["out"] )
		contextVariables["in"].setInput( sphereAttributes["out"] )

		merge = GafferScene.MergeScenes()
		merge["in"][0].setInput( sphereAttributes["out"] )
		merge["in"][1].setInput( contextVariables["out"] )
		merge["mode"].setValue( GafferScene.MergeScenes.MergeMode.Collect )
		merge["contextValues"].setValue( IECore.StringVectorData( [ "A", "B", "C" ] ) )

		self.assertEqual( merge["out"].attributes( "/sphere" ), IECore.CompoundObject({'testA:':IECore.IntData( 1 )}) )

		merge["attributesMode"].setValue( merge.Mode.Replace )

		self.assertEqual( merge["out"].attributes( "/sphere" ), IECore.CompoundObject({'testC:second':IECore.IntData( 1 )}) )

		merge["attributesMode"].setValue( merge.Mode.Merge )

		self.assertEqual( merge["out"].attributes( "/sphere" ), IECore.CompoundObject(
			{ "test" + i + ":" + j : IECore.IntData( 1 ) for i in "ABC" for j in [ "", "second" ] }
		) )

		self.assertEqual( merge["out"].transform( "/sphere" ), imath.M44f() )

		merge["transformMode"].setValue( merge.Mode.Replace )

		refM = imath.M44f()
		refM.translate( imath.V3f( 2, 1, 0 ) )
		self.assertEqual( merge["out"].transform( "/sphere" ), refM )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testBasicPerf( self ):

		cube = GafferScene.Cube()
		group1 = GafferScene.Group()
		group1["in"][0].setInput( cube["out"] )
		group2 = GafferScene.Group()
		group2["in"][0].setInput( group1["out"] )
		group3 = GafferScene.Group()
		group3["in"][0].setInput( group2["out"] )
		group4 = GafferScene.Group()
		group4["in"][0].setInput( group3["out"] )
		group5 = GafferScene.Group()
		group5["in"][0].setInput( group4["out"] )


		pathFilter = GafferScene.PathFilter()
		pathFilter["paths"].setValue( IECore.StringVectorData( [ '/group' ] ) )

		duplicate = GafferScene.Duplicate()
		duplicate["in"].setInput( group5["out"] )
		duplicate["filter"].setInput( pathFilter["out"] )
		duplicate["copies"].setValue( 1000 )

		mergeScenes = GafferScene.MergeScenes()
		for i in range( 32 ):
			mergeScenes["in"][i].setInput( duplicate["out"] )

		GafferSceneTest.traverseScene( duplicate["out"] )
		with GafferTest.TestRunner.PerformanceScope() :
			GafferSceneTest.traverseScene( mergeScenes["out"] )
