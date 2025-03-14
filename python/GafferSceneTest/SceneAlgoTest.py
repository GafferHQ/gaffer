##########################################################################
#
#  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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
import unittest

import IECore

import Gaffer
import GafferTest
import GafferImage
import GafferScene
import GafferSceneTest

class SceneAlgoTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		sphere = GafferScene.Sphere()
		plane = GafferScene.Plane()
		group = GafferScene.Group()
		group["in"][0].setInput( sphere["out"] )
		group["in"][1].setInput( plane["out"] )

		plane2 = GafferScene.Plane()
		plane2["divisions"].setValue( imath.V2i( 99, 99 ) ) # 10000 instances

		instancer = GafferScene.Instancer()
		instancer["in"].setInput( plane2["out"] )
		instancer["parent"].setValue( "/plane" )
		instancer["prototypes"].setInput( group["out"] )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/plane/instances/group/*1/plane" ] ) )

		matchingPaths = IECore.PathMatcher()
		GafferScene.SceneAlgo.matchingPaths( filter, instancer["out"], matchingPaths )

		self.assertEqual( len( matchingPaths.paths() ), 1000 )
		self.assertEqual( matchingPaths.match( "/plane/instances/group/1/plane" ), IECore.PathMatcher.Result.ExactMatch )
		self.assertEqual( matchingPaths.match( "/plane/instances/group/1121/plane" ), IECore.PathMatcher.Result.ExactMatch )
		self.assertEqual( matchingPaths.match( "/plane/instances/group/1121/sphere" ), IECore.PathMatcher.Result.NoMatch )

		# Test root argument
		matchingPaths = IECore.PathMatcher()
		GafferScene.SceneAlgo.matchingPaths( filter["out"], instancer["out"], "/plane/instances/group/1121", matchingPaths )
		self.assertEqual( matchingPaths.paths(), [ "/plane/instances/group/1121/plane" ] )

	def testExists( self ) :

		sphere = GafferScene.Sphere()
		plane = GafferScene.Plane()
		group = GafferScene.Group()
		group["in"][0].setInput( sphere["out"] )
		group["in"][1].setInput( plane["out"] )

		self.assertTrue( GafferScene.SceneAlgo.exists( group["out"], "/" ) )
		self.assertTrue( GafferScene.SceneAlgo.exists( group["out"], "/group" ) )
		self.assertTrue( GafferScene.SceneAlgo.exists( group["out"], "/group/sphere" ) )
		self.assertTrue( GafferScene.SceneAlgo.exists( group["out"], "/group/plane" ) )

		self.assertFalse( GafferScene.SceneAlgo.exists( group["out"], "/a" ) )
		self.assertFalse( GafferScene.SceneAlgo.exists( group["out"], "/group2" ) )
		self.assertFalse( GafferScene.SceneAlgo.exists( group["out"], "/group/sphere2" ) )
		self.assertFalse( GafferScene.SceneAlgo.exists( group["out"], "/group/plane/child" ) )

	def testVisible( self ) :

		sphere = GafferScene.Sphere()
		group = GafferScene.Group()
		group["in"][0].setInput( sphere["out"] )
		group2 = GafferScene.Group()
		group2["in"][0].setInput( group["out"] )

		visibleFilter = GafferScene.PathFilter()

		attributes1 = GafferScene.StandardAttributes()
		attributes1["attributes"]["visibility"]["enabled"].setValue( True )
		attributes1["attributes"]["visibility"]["value"].setValue( True )
		attributes1["in"].setInput( group2["out"] )
		attributes1["filter"].setInput( visibleFilter["out"] )

		invisibleFilter = GafferScene.PathFilter()

		attributes2 = GafferScene.StandardAttributes()
		attributes2["attributes"]["visibility"]["enabled"].setValue( True )
		attributes2["attributes"]["visibility"]["value"].setValue( False )
		attributes2["in"].setInput( attributes1["out"] )
		attributes2["filter"].setInput( invisibleFilter["out"] )

		self.assertTrue( GafferScene.SceneAlgo.visible( attributes2["out"], "/group/group/sphere" ) )
		self.assertTrue( GafferScene.SceneAlgo.visible( attributes2["out"], "/group/group" ) )
		self.assertTrue( GafferScene.SceneAlgo.visible( attributes2["out"], "/group" ) )
		self.assertTrue( GafferScene.SceneAlgo.visible( attributes2["out"], "/" ) )

		visibleFilter["paths"].setValue( IECore.StringVectorData( [ "/group" ] ) )

		self.assertTrue( GafferScene.SceneAlgo.visible( attributes2["out"], "/group/group/sphere" ) )
		self.assertTrue( GafferScene.SceneAlgo.visible( attributes2["out"], "/group/group" ) )
		self.assertTrue( GafferScene.SceneAlgo.visible( attributes2["out"], "/group" ) )
		self.assertTrue( GafferScene.SceneAlgo.visible( attributes2["out"], "/" ) )

		invisibleFilter["paths"].setValue( IECore.StringVectorData( [ "/group/group" ] ) )

		self.assertFalse( GafferScene.SceneAlgo.visible( attributes2["out"], "/group/group/sphere" ) )
		self.assertFalse( GafferScene.SceneAlgo.visible( attributes2["out"], "/group/group" ) )
		self.assertTrue( GafferScene.SceneAlgo.visible( attributes2["out"], "/group" ) )
		self.assertTrue( GafferScene.SceneAlgo.visible( attributes2["out"], "/" ) )

		visibleFilter["paths"].setValue( IECore.StringVectorData( [ "/group/group/sphere" ] ) )

		self.assertFalse( GafferScene.SceneAlgo.visible( attributes2["out"], "/group/group/sphere" ) )
		self.assertFalse( GafferScene.SceneAlgo.visible( attributes2["out"], "/group/group" ) )
		self.assertTrue( GafferScene.SceneAlgo.visible( attributes2["out"], "/group" ) )
		self.assertTrue( GafferScene.SceneAlgo.visible( attributes2["out"], "/" ) )

	def testSetExists( self ) :

		plane = GafferScene.Plane()
		plane["sets"].setValue( "A B" )

		self.assertTrue( GafferScene.SceneAlgo.setExists( plane["out"], "A" ) )
		self.assertTrue( GafferScene.SceneAlgo.setExists( plane["out"], "B" ) )
		self.assertFalse( GafferScene.SceneAlgo.setExists( plane["out"], " " ) )
		self.assertFalse( GafferScene.SceneAlgo.setExists( plane["out"], "" ) )
		self.assertFalse( GafferScene.SceneAlgo.setExists( plane["out"], "C" ) )

	def testSets( self ) :

		light = GafferSceneTest.TestLight()
		light["sets"].setValue( "A B C" )

		sets = GafferScene.SceneAlgo.sets( light["out"] )
		self.assertEqual( set( sets.keys() ), { "__lights", "defaultLights", "A", "B", "C" } )
		for n in sets.keys() :
			self.assertEqual( sets[n], light["out"].set( n ) )
			self.assertFalse( sets[n].isSame( light["out"].set( n, _copy = False ) ) )

		sets = GafferScene.SceneAlgo.sets( light["out"], _copy = False )
		self.assertEqual( set( sets.keys() ), { "__lights", "defaultLights", "A", "B", "C" } )
		for n in sets.keys() :
			self.assertTrue( sets[n].isSame( light["out"].set( n, _copy = False ) ) )

		someSets = GafferScene.SceneAlgo.sets( light["out"], ( "A", "B" ), _copy = False )
		self.assertEqual( set( someSets.keys() ), { "A", "B" } )
		for n in someSets.keys() :
			self.assertTrue( someSets[n].isSame( light["out"].set( n, _copy = False ) ) )

	def testMatchingPathsWithPathMatcher( self ) :

		s = GafferScene.Sphere()
		g = GafferScene.Group()
		g["in"][0].setInput( s["out"] )
		g["in"][1].setInput( s["out"] )
		g["in"][2].setInput( s["out"] )

		f = IECore.PathMatcher( [ "/group/s*" ] )
		m = IECore.PathMatcher()
		GafferScene.SceneAlgo.matchingPaths( f, g["out"], m )

		self.assertEqual( set( m.paths() ), { "/group/sphere", "/group/sphere1", "/group/sphere2" } )

	def testSetsNeedContextEntry( self ) :

		script = Gaffer.ScriptNode()
		script["light"] = GafferSceneTest.TestLight()
		script["light"]["sets"].setValue( "A B C" )

		script["expression"] = Gaffer.Expression()
		script["expression"].setExpression(
			"""parent["light"]["name"] = context["lightName"]"""
		)

		for i in range( 0, 100 ) :
			with Gaffer.Context() as context :
				context["lightName"] = "light%d" % i
				GafferScene.SceneAlgo.sets( script["light"]["out"] )

	def testHistoryClass( self ) :

		h = GafferScene.SceneAlgo.History()
		self.assertEqual( h.scene, None )
		self.assertEqual( h.context, None )
		self.assertEqual( len( h.predecessors ), 0 )

		s = GafferScene.ScenePlug()
		c = Gaffer.Context()

		h.scene = s
		h.context = c

		self.assertEqual( h.scene, s )
		self.assertEqual( h.context, c )

		h.predecessors.append( GafferScene.SceneAlgo.History() )
		self.assertEqual( len( h.predecessors ), 1 )

	def testHistory( self ) :

		plane = GafferScene.Plane()

		attributesFilter = GafferScene.PathFilter()
		attributesFilter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		attributes = GafferScene.StandardAttributes()
		attributes["in"].setInput( plane["out"] )
		attributes["filter"].setInput( attributesFilter["out"] )
		attributes["attributes"].addChild( Gaffer.NameValuePlug( "test", 10 ) )

		group = GafferScene.Group()
		group["in"][0].setInput( attributes["out"] )

		transformFilter = GafferScene.PathFilter()
		transformFilter["paths"].setValue( IECore.StringVectorData( [ "/group/plane" ] ) )

		transform = GafferScene.Transform()
		transform["in"].setInput( group["out"] )
		transform["filter"].setInput( transformFilter["out"] )

		# Transform history

		with Gaffer.Context() as c :
			c.setFrame( 10 )
			history = GafferScene.SceneAlgo.history( transform["out"]["transform"], "/group/plane" )

		for plug, scenePath in [
			( transform["out"], "/group/plane" ),
			( transform["in"], "/group/plane" ),
			( group["out"], "/group/plane" ),
			( group["in"][0], "/plane" ),
			( attributes["out"], "/plane" ),
			( attributes["in"], "/plane" ),
			( plane["out"], "/plane" ),
		] :
			self.assertEqual( history.scene, plug )
			self.assertEqual( history.context.getFrame(), 10 )
			self.assertEqual( GafferScene.ScenePlug.pathToString( history.context["scene:path"] ), scenePath )
			self.assertFalse( any( n.startswith( "__" ) for n in history.context.names() ) )
			history = history.predecessors[0] if history.predecessors else None

		self.assertIsNone( history )

		# Attributes history

		def runTest():

			with Gaffer.Context() as c :
				c.setFrame( 20 )
				history = GafferScene.SceneAlgo.history( transform["out"]["attributes"], "/group/plane" )

			for plug, scenePath in [
				( transform["out"], "/group/plane" ),
				( transform["in"], "/group/plane" ),
				( group["out"], "/group/plane" ),
				( group["in"][0], "/plane" ),
				( attributes["out"], "/plane" ),
				( attributes["in"], "/plane" ),
				( plane["out"], "/plane" ),
			] :
				self.assertEqual( history.scene, plug )
				self.assertEqual( history.context.getFrame(), 20 )
				self.assertEqual( GafferScene.ScenePlug.pathToString( history.context["scene:path"] ), scenePath )
				self.assertFalse( any( n.startswith( "__" ) for n in history.context.names() ) )
				self.assertLessEqual( len( history.predecessors ), 1 )
				history = history.predecessors[0] if history.predecessors else None

			self.assertIsNone( history )

		runTest()

		# Before running the same test again, set up a bound query that pulls an unrelated piece of a
		# scene plug, before running this test again.  This isn't part of attribute history,  so it
		# shouldn't affect the result
		attributes["attributes"].addChild( Gaffer.NameValuePlug( "test", imath.V3f( 0 ) ) )

		sourceScene = GafferScene.Sphere()
		boundQuery = GafferScene.BoundQuery()
		boundQuery["scene"].setInput( sourceScene["out"] )
		boundQuery["location"].setValue( "/sphere" )

		attributes["attributes"]["NameValuePlug1"]["value"].setInput( boundQuery["center"] )


		runTest()

		# Test running the test while everything is already cached still works, and doesn't add any
		# new entries to the cache
		Gaffer.ValuePlug.clearHashCache()
		runTest()
		before = Gaffer.ValuePlug.hashCacheTotalUsage()
		runTest()
		self.assertEqual( Gaffer.ValuePlug.hashCacheTotalUsage(), before )

		# Test that even the processes that aren't reading the cache still write to the cache, by
		# making sure that a subsequent attributeHash doesn't need to do anything
		Gaffer.ValuePlug.clearHashCache()
		runTest()
		with Gaffer.PerformanceMonitor() as pm :
			with Gaffer.Context() as c :
				c.setFrame( 20 )
				transform["out"].attributesHash( "/group/plane" )
		self.assertEqual( pm.combinedStatistics().hashCount, 0 )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testHistoryPerformance( self ) :

		plane = GafferScene.Plane( "Plane" )
		plane["divisions"].setValue( imath.V2i( 600 ) )

		planeFilter = GafferScene.PathFilter( "PathFilter" )
		planeFilter["paths"].setValue( IECore.StringVectorData( [ '/plane' ] ) )

		instancer = GafferScene.Instancer( "Instancer" )
		instancer["in"].setInput( plane["out"] )
		instancer["prototypes"].setInput( plane["out"] )
		instancer["filter"].setInput( planeFilter["out"] )

		allFilter = GafferScene.PathFilter( "PathFilter1" )
		allFilter["paths"].setValue( IECore.StringVectorData( [ '/...' ] ) )

		setNode = GafferScene.Set( "Set" )
		setNode["in"].setInput( instancer["out"] )
		setNode["filter"].setInput( allFilter["out"] )

		attributesFilter = GafferScene.SetFilter()
		attributesFilter["setExpression"].setValue( "set" )

		attributes = GafferScene.StandardAttributes()
		attributes["in"].setInput( setNode["out"] )
		attributes["filter"].setInput( attributesFilter["out"] )
		attributes["attributes"].addChild( Gaffer.NameValuePlug( "test", 10 ) )

		with GafferTest.TestRunner.PerformanceScope() :
			history = GafferScene.SceneAlgo.history( attributes["out"]["attributes"], "/plane" )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testHistoryPerformanceAlreadyCached( self ) :

		plane = GafferScene.Plane( "Plane" )
		plane["divisions"].setValue( imath.V2i( 300 ) )

		planeFilter = GafferScene.PathFilter( "PathFilter" )
		planeFilter["paths"].setValue( IECore.StringVectorData( [ '/plane' ] ) )

		instancer = GafferScene.Instancer( "Instancer" )
		instancer["in"].setInput( plane["out"] )
		instancer["prototypes"].setInput( plane["out"] )
		instancer["filter"].setInput( planeFilter["out"] )
		instancer["seedEnabled"].setValue( True )

		allFilter = GafferScene.PathFilter()
		allFilter["paths"].setValue( IECore.StringVectorData( [ '/...' ] ) )

		parent = GafferScene.Parent()
		parent["in"].setInput( instancer["out"] )
		parent["child"][0].setInput( plane["out"] )
		parent["filter"].setInput( allFilter["out"] )

		parent["out"].attributesHash( "/plane/instances/plane/1000" )

		# This history call should perform only the hashes necessary for attribute history, while pulling
		# results for anything but the attributes plug from the hash cache.  ( In particular, this has
		# been set up so that the hash of parent.branches is quite expensive, and this will fail if we
		# don't use the cache for that )
		with GafferTest.TestRunner.PerformanceScope() :
			h = GafferScene.SceneAlgo.history( parent["out"]["attributes"], "/plane/instances/plane/1000" )

		# Make sure that despite not evaluating all the inputs for performance reasons, we do get the
		# source in the correct context
		while h.predecessors:
			h = h.predecessors[-1]
		self.assertEqual( h.context["seed"], 5 )

	def testObjectProcessorHistory( self ) :

		plane = GafferScene.Plane()

		meshType = GafferScene.MeshType()
		meshType["in"].setInput( plane["out"] )

		def runTest() :

			history = GafferScene.SceneAlgo.history( meshType["out"]["object"], "/plane" )

			for plug, scenePath in [
				( meshType["out"], "/plane" ),
				( meshType["in"], "/plane" ),
				( plane["out"], "/plane" ),
			] :
				self.assertEqual( history.scene, plug )
				self.assertEqual( GafferScene.ScenePlug.pathToString( history.context["scene:path"] ), scenePath )
				history = history.predecessors[0] if history.predecessors else None

			self.assertIsNone( history )

		runTest()

		# Test running the test while everything is already cached still works, and doesn't add any
		# new entries to the cache
		Gaffer.ValuePlug.clearHashCache()
		runTest()
		before = Gaffer.ValuePlug.hashCacheTotalUsage()
		runTest()
		self.assertEqual( Gaffer.ValuePlug.hashCacheTotalUsage(), before )

	def testHistoryWithNoComputes( self ) :

		switch = Gaffer.Switch()
		switch.setup( GafferScene.ScenePlug() )

		with Gaffer.Context() as c :
			c["test"] = 10
			history = GafferScene.SceneAlgo.history( switch["out"]["globals"], "" )

		self.assertEqual( history.scene, switch["out"] )
		self.assertEqual( history.context, c )

	def testHistoryWithInvalidPlug( self ) :

		plane = GafferScene.Plane()
		with self.assertRaisesRegex( RuntimeError, "is not a child of a ScenePlug" ) :
			GafferScene.SceneAlgo.history( plane["name"], "/plane" )

	def testHistoryIncludesConnections( self ) :

		plane = GafferScene.Plane()

		dot1 = Gaffer.Dot()
		dot1.setup( plane["out"] )
		dot1["in"].setInput( plane["out"] )

		standardOptions = GafferScene.StandardOptions()
		standardOptions["in"].setInput( dot1["out"] )

		dot2 = Gaffer.Dot()
		dot2.setup( standardOptions["out"] )
		dot2["in"].setInput( standardOptions["out"] )

		shaderAssignment = GafferScene.ShaderAssignment()
		shaderAssignment["in"].setInput( dot2["out"] )

		history = GafferScene.SceneAlgo.history( shaderAssignment["out"]["transform"], "/plane" )

		for plug in [
			shaderAssignment["out"],
			shaderAssignment["in"],
			dot2["out"],
			dot2["in"],
			standardOptions["out"],
			standardOptions["in"],
			dot1["out"],
			dot1["in"],
			plane["out"],
		] :
			self.assertEqual( history.scene, plug )
			history = history.predecessors[0] if history.predecessors else None

		self.assertIsNone( history )

	def testSource( self ) :

		# - group1
		#	- group2
		#		- plane
		# 		- sphere
		#   - plane
		# - cube

		plane = GafferScene.Plane()
		sphere = GafferScene.Sphere()
		cube = GafferScene.Cube()

		group2 = GafferScene.Group()
		group2["in"][0].setInput( plane["out"] )
		group2["in"][1].setInput( sphere["out"] )
		group2["name"].setValue( "group2" )

		group1 = GafferScene.Group()
		group1["in"][0].setInput( group2["out"] )
		group1["in"][1].setInput( plane["out"] )
		group1["name"].setValue( "group1" )

		parent = GafferScene.Parent()
		parent["in"].setInput( group1["out"] )
		parent["children"][0].setInput( cube["out"] )
		parent["parent"].setValue( "/" )

		self.assertEqual( GafferScene.SceneAlgo.source( parent["out"], "/group1" ), group1["out"] )
		self.assertEqual( GafferScene.SceneAlgo.source( parent["out"], "/group1/group2" ), group2["out"] )
		self.assertEqual( GafferScene.SceneAlgo.source( parent["out"], "/group1/group2/plane" ), plane["out"] )
		self.assertEqual( GafferScene.SceneAlgo.source( parent["out"], "/group1/group2/sphere" ), sphere["out"] )
		self.assertEqual( GafferScene.SceneAlgo.source( parent["out"], "/group1/plane" ), plane["out"] )
		self.assertEqual( GafferScene.SceneAlgo.source( parent["out"], "/cube" ), cube["out"] )

	def testShaderTweaks( self ) :

		shader = GafferSceneTest.TestShader()
		shader["type"].setValue( "test:surface" )

		plane = GafferScene.Plane()
		planeShaderAssignment = GafferScene.ShaderAssignment()
		planeShaderAssignment["in"].setInput( plane["out"] )
		planeShaderAssignment["shader"].setInput( shader["out"] )

		sphere = GafferScene.Sphere()
		sphereShaderAssignment = GafferScene.ShaderAssignment()
		sphereShaderAssignment["in"].setInput( sphere["out"] )
		sphereShaderAssignment["shader"].setInput( shader["out"] )

		light = GafferSceneTest.TestLight()

		lightFilter = GafferScene.PathFilter()
		lightFilter["paths"].setValue( IECore.StringVectorData( [ "/light" ] ) )

		lightTweaks = GafferScene.ShaderTweaks()
		lightTweaks["in"].setInput( light["out"] )
		lightTweaks["filter"].setInput( lightFilter["out"] )
		lightTweaks["shader"].setValue( "light" )

		group = GafferScene.Group()
		group["in"][0].setInput( planeShaderAssignment["out"] )
		group["in"][1].setInput( sphereShaderAssignment["out"] )
		group["in"][2].setInput( lightTweaks["out"] )

		planeFilter = GafferScene.PathFilter()
		planeFilter["paths"].setValue( IECore.StringVectorData( [ "/group/plane" ] ) )

		planeTweaks = GafferScene.ShaderTweaks()
		planeTweaks["in"].setInput( group["out"] )
		planeTweaks["filter"].setInput( planeFilter["out"] )
		planeTweaks["shader"].setValue( "test:surface" )

		sphereFilter = GafferScene.PathFilter()
		sphereFilter["paths"].setValue( IECore.StringVectorData( [ "/group/sphere" ] ) )

		sphereTweaks = GafferScene.ShaderTweaks()
		sphereTweaks["in"].setInput( planeTweaks["out"] )
		sphereTweaks["filter"].setInput( sphereFilter["out"] )
		sphereTweaks["shader"].setValue( "test:surface" )

		self.assertEqual( GafferScene.SceneAlgo.shaderTweaks( sphereTweaks["out"], "/group/light", "light" ), lightTweaks )
		self.assertEqual( GafferScene.SceneAlgo.shaderTweaks( sphereTweaks["out"], "/group", "light" ), None )
		self.assertEqual( GafferScene.SceneAlgo.shaderTweaks( sphereTweaks["out"], "/group/light", "surface" ), None )

		self.assertEqual( GafferScene.SceneAlgo.shaderTweaks( sphereTweaks["out"], "/group/sphere", "test:surface" ), sphereTweaks )
		self.assertEqual( GafferScene.SceneAlgo.shaderTweaks( sphereTweaks["out"], "/group/sphere", "displacement" ), None )
		self.assertEqual( GafferScene.SceneAlgo.shaderTweaks( sphereTweaks["out"], "/group", "test:surface" ), None )
		self.assertEqual( GafferScene.SceneAlgo.shaderTweaks( sphereTweaks["out"], "/", "surface" ), None )

		self.assertEqual( GafferScene.SceneAlgo.shaderTweaks( sphereTweaks["out"], "/group/plane", "test:surface" ), planeTweaks )
		self.assertEqual( GafferScene.SceneAlgo.shaderTweaks( sphereTweaks["out"], "/group/plane", "displacement" ), None )
		self.assertEqual( GafferScene.SceneAlgo.shaderTweaks( sphereTweaks["out"], "/group", "test:surface" ), None )
		self.assertEqual( GafferScene.SceneAlgo.shaderTweaks( sphereTweaks["out"], "/", "surface" ), None )

	def testShaderTweaksInheritance( self ) :

		plane = GafferScene.Plane()

		group = GafferScene.Group()
		group["in"][0].setInput( plane["out"] )

		shader = GafferSceneTest.TestShader()
		shader["type"].setValue( "test:surface" )

		groupFilter = GafferScene.PathFilter()
		groupFilter["paths"].setValue( IECore.StringVectorData( [ "/group" ] ) )

		shaderAssignment = GafferScene.ShaderAssignment()
		shaderAssignment["in"].setInput( group["out"] )
		shaderAssignment["shader"].setInput( shader["out"] )
		shaderAssignment["filter"].setInput( groupFilter["out"] )

		tweaks = GafferScene.ShaderTweaks()
		tweaks["in"].setInput( shaderAssignment["out"] )
		tweaks["filter"].setInput( groupFilter["out"] )
		tweaks["shader"].setValue( "test:surface" )

		sphere = GafferScene.Sphere()

		parent = GafferScene.Parent()
		parent["in"].setInput( tweaks["out"] )
		parent["children"][0].setInput( sphere["out"] )
		parent["parent"].setValue( "/" )

		self.assertEqual( GafferScene.SceneAlgo.shaderTweaks( parent["out"], "/group/plane", "test:surface" ), tweaks )
		self.assertEqual( GafferScene.SceneAlgo.shaderTweaks( parent["out"], "/group", "test:surface" ), tweaks )
		self.assertEqual( GafferScene.SceneAlgo.shaderTweaks( parent["out"], "/", "surface" ), None )
		self.assertEqual( GafferScene.SceneAlgo.shaderTweaks( parent["out"], "/sphere", "surface" ), None )

	def testShaderTweaksWithCopyAttributes( self ) :

		#     plane
		#       |
		#  shaderAssignment
		#       /\
		#      /  \
		# tweaks1 tweaks2
		#      \  /
		#  copyAttributes

		plane = GafferScene.Plane()

		planeFilter = GafferScene.PathFilter()
		planeFilter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		shader = GafferSceneTest.TestShader()
		shader["type"].setValue( "test:surface" )

		shaderAssignment = GafferScene.ShaderAssignment()
		shaderAssignment["in"].setInput( plane["out"] )
		shaderAssignment["shader"].setInput( shader["out"] )
		shaderAssignment["filter"].setInput( planeFilter["out"] )

		tweaks1 = GafferScene.ShaderTweaks()
		tweaks1["in"].setInput( shaderAssignment["out"] )
		tweaks1["filter"].setInput( planeFilter["out"] )
		tweaks1["shader"].setValue( "test:surface" )

		tweaks2 = GafferScene.ShaderTweaks()
		tweaks2["in"].setInput( shaderAssignment["out"] )
		tweaks2["filter"].setInput( planeFilter["out"] )
		tweaks2["shader"].setValue( "test:surface" )

		copyAttributes = GafferScene.CopyAttributes()
		copyAttributes["in"].setInput( tweaks1["out"] )
		copyAttributes["source"].setInput( tweaks2["out"] )

		# No filter

		self.assertEqual(
			GafferScene.SceneAlgo.shaderTweaks( copyAttributes["out"], "/plane", "test:surface" ),
			tweaks1
		)

		# Filter, but nothing being copied

		copyAttributes["filter"].setInput( planeFilter["out"] )
		copyAttributes["attributes"].setValue( "" )
		self.assertEqual(
			GafferScene.SceneAlgo.shaderTweaks( copyAttributes["out"], "/plane", "test:surface" ),
			tweaks1
		)

		# Attribute actually being copied

		copyAttributes["attributes"].setValue( "test:surface" )
		self.assertEqual(
			GafferScene.SceneAlgo.shaderTweaks( copyAttributes["out"], "/plane", "test:surface" ),
			tweaks2
		)

	def testObjectTweaks( self ) :

		camera1 = GafferScene.Camera( "Camera1" )
		camera1["name"].setValue( "camera1" )

		camera1Filter = GafferScene.PathFilter()
		camera1Filter["paths"].setValue( IECore.StringVectorData( [ "/camera1" ] ) )

		camera1Tweaks = GafferScene.CameraTweaks( "Camera1Tweaks" )
		camera1Tweaks["in"].setInput( camera1["out"] )
		camera1Tweaks["filter"].setInput( camera1Filter["out"] )

		unfilteredTweaks = GafferScene.CameraTweaks( "UnfilteredTweaks" )
		unfilteredTweaks["in"].setInput( camera1Tweaks["out"] )

		camera2 = GafferScene.Camera( "Camera2" )
		camera2["name"].setValue( "camera2" )

		group = GafferScene.Group()
		group["in"][0].setInput( unfilteredTweaks["out"] )
		group["in"][1].setInput( camera2["out"] )

		camera2Filter = GafferScene.PathFilter()
		camera2Filter["paths"].setValue( IECore.StringVectorData( [ "/group/camera2" ] ) )

		camera2Tweaks = GafferScene.CameraTweaks( "Camera2Tweaks" )
		camera2Tweaks["in"].setInput( group["out"] )
		camera2Tweaks["filter"].setInput( camera2Filter["out"] )

		self.assertEqual( GafferScene.SceneAlgo.objectTweaks( camera2Tweaks["out"], "/" ), None )
		self.assertEqual( GafferScene.SceneAlgo.objectTweaks( camera2Tweaks["out"], "/group" ), None )
		self.assertEqual( GafferScene.SceneAlgo.objectTweaks( camera2Tweaks["out"], "/group/camera1" ), camera1Tweaks )
		self.assertEqual( GafferScene.SceneAlgo.objectTweaks( camera2Tweaks["out"], "/group/camera2" ), camera2Tweaks )

	def testMonitorMatchingPaths( self ) :

		plane = GafferScene.Plane()
		plane["divisions"].setValue( imath.V2i( 1000, 100 ) )

		sphere = GafferScene.Sphere()

		instancer = GafferScene.Instancer()
		instancer["in"].setInput( plane["out"] )
		instancer["prototypes"].setInput( sphere["out"] )
		instancer["parent"].setValue( "/plane" )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/plane/instances/sphere/*" ] ) )

		paths = IECore.PathMatcher()
		with Gaffer.PerformanceMonitor() as m :
			GafferScene.SceneAlgo.matchingPaths( filter["out"], instancer["out"], paths )

		self.assertEqual(
			m.plugStatistics( filter["out"] ).computeCount,
			len( instancer["out"].childNames( "/plane/instances/sphere" ) ) + 4,
		)

	def testObjectTweaksWithSetFilter( self ) :

		camera = GafferScene.Camera()
		camera["sets"].setValue( "A" )

		setFilter = GafferScene.SetFilter()
		setFilter["set"].setValue( "A" )

		cameraTweaks = GafferScene.CameraTweaks()
		cameraTweaks["in"].setInput( camera["out"] )
		cameraTweaks["filter"].setInput( setFilter["out"] )

		self.assertEqual( GafferScene.SceneAlgo.objectTweaks( cameraTweaks["out"], "/camera" ), cameraTweaks )

	def testShaderTweaksWithSetFilter( self ) :

		shader = GafferSceneTest.TestShader()
		shader["type"].setValue( "test:surface" )

		plane = GafferScene.Plane()
		plane["sets"].setValue( "A" )

		planeShaderAssignment = GafferScene.ShaderAssignment()
		planeShaderAssignment["in"].setInput( plane["out"] )
		planeShaderAssignment["shader"].setInput( shader["out"] )

		setFilter = GafferScene.SetFilter()
		setFilter["set"].setValue( "A" )

		planeTweaks = GafferScene.ShaderTweaks()
		planeTweaks["in"].setInput( planeShaderAssignment["out"] )
		planeTweaks["filter"].setInput( setFilter["out"] )
		planeTweaks["shader"].setValue( "test:surface" )

		self.assertEqual( GafferScene.SceneAlgo.shaderTweaks( planeTweaks["out"], "/plane", "test:surface" ), planeTweaks )

	def testSourceScene( self ) :

		b = Gaffer.Box()
		b2 = Gaffer.Box()
		p = GafferScene.Plane()
		b["Box2"] = b2
		b2["Plane"] = p

		expectedPath = "Box.Box2.Plane.out"
		self.assertEqual( p["out"].fullName(), expectedPath )

		# Make a test image, we don't have a renderer to use to invoke the real output
		# mechanism so we'll mock the result here.

		c = GafferImage.Constant()
		m = GafferImage.ImageMetadata()
		o = GafferImage.ImageWriter()
		m["in"].setInput( c["out"] )
		o["in"].setInput( m["out"] )

		pathWithoutMeta = self.temporaryDirectory() / "sceneAlgoSourceSceneWithoutMeta.exr"
		o["fileName"].setValue( pathWithoutMeta )
		o.execute()

		pathWithMeta = self.temporaryDirectory() / "sceneAlgoSourceSceneWithMeta.exr"
		m["metadata"].addChild(
			Gaffer.NameValuePlug(
				"gaffer:sourceScene", IECore.StringData( expectedPath ), True, "sourceScene",
				flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic
			)
		)
		o["fileName"].setValue( pathWithMeta )
		o.execute()

		inm = GafferImage.ImageReader()
		im = GafferImage.ImageReader()
		inm["fileName"].setValue( pathWithoutMeta )
		im["fileName"].setValue( pathWithMeta )
		self.assertTrue( "gaffer:sourceScene" not in inm["out"].metadata().keys() )
		self.assertTrue( "gaffer:sourceScene" in im["out"].metadata().keys() )

		# Test path retrieval
		self.assertEqual( GafferScene.SceneAlgo.sourceSceneName( inm["out"] ), "" )
		self.assertEqual( GafferScene.SceneAlgo.sourceSceneName( im["out"] ), expectedPath )

		# Check plug retrieval without a script node
		self.assertIsNone( GafferScene.SceneAlgo.sourceScene( inm["out"] ) )
		self.assertIsNone( GafferScene.SceneAlgo.sourceScene( im["out"] ) )

		# Add to a script

		s = Gaffer.ScriptNode()
		s["Box"] = b
		s["ImageNoMeta"] = inm
		s["ImageMeta"] = im

		self.assertIsNone( GafferScene.SceneAlgo.sourceScene( inm["out"] ) )
		self.assertTrue( p["out"].isSame( GafferScene.SceneAlgo.sourceScene( im["out"] ) ) )

		# Remove target plug

		del s["Box"]["Box2"]

		self.assertIsNone( GafferScene.SceneAlgo.sourceScene( inm["out"] ) )
		self.assertIsNone( GafferScene.SceneAlgo.sourceScene( im["out"] ) )

	def testFilteredNodes( self ) :

		pathFilter = GafferScene.PathFilter()

		unionFilter = GafferScene.UnionFilter()
		unionFilter["in"][0].setInput( pathFilter["out"] )
		unionFilter["in"][1].setInput( pathFilter["out"] )

		dot1 = Gaffer.Dot()
		dot1.setup( pathFilter["out"] )
		dot1["in"].setInput( pathFilter["out"] )

		dot2 = Gaffer.Dot()
		dot2.setup( unionFilter["out"] )
		dot2["in"].setInput( unionFilter["out"] )

		node1 = GafferScene.ShaderAssignment()
		node1["filter"].setInput( pathFilter["out"] )

		node2 = GafferScene.ShaderAssignment()
		node2["filter"].setInput( dot1["out"] )

		node3 = GafferScene.ShaderAssignment()
		node3["filter"].setInput( unionFilter["out"] )

		node4 = GafferScene.ShaderAssignment()
		node4["filter"].setInput( dot2["out"] )

		node5 = GafferScene.ShaderAssignment()
		node5["in"].setInput( node4["out"] )

		self.assertEqual(
			GafferScene.SceneAlgo.filteredNodes( pathFilter ),
			{ node1, node2, node3, node4 },
		)

		self.assertEqual(
			GafferScene.SceneAlgo.filteredNodes( unionFilter ),
			{ node3, node4 },
		)

		unconnectedFilter = GafferScene.PathFilter()
		self.assertEqual(
			GafferScene.SceneAlgo.filteredNodes( unconnectedFilter ),
			set(),
		)

	def testFilteredNodesForPathFilterRoots( self ) :

		rootsFilter = GafferScene.SetFilter()
		pathFilter = GafferScene.PathFilter()
		pathFilter["roots"].setInput( rootsFilter["out"] )

		shaderAssignment = GafferScene.ShaderAssignment()
		shaderAssignment["filter"].setInput( pathFilter["out"] )

		self.assertEqual(
			GafferScene.SceneAlgo.filteredNodes( rootsFilter ),
			{ shaderAssignment }
		)

	def __predecessor( self, history, predecessorIndices ) :

		for i in predecessorIndices :
			history = history.predecessors[i]

		return history

	def __assertAttributeHistory( self, attributeHistory, predecessorIndices, scene, path, attributeName, attributeValue, numPredecessors ) :

		ah = self.__predecessor( attributeHistory, predecessorIndices )

		self.assertIsInstance( ah, GafferScene.SceneAlgo.AttributeHistory )
		self.assertEqual( ah.scene, scene )
		self.assertEqual( GafferScene.ScenePlug.pathToString( ah.context["scene:path"] ), path )
		self.assertEqual( ah.attributeName, attributeName )
		self.assertEqual( ah.attributeValue, attributeValue )
		self.assertEqual( len( ah.predecessors ), numPredecessors )

	def __assertParameterHistory( self, attributeHistory, predecessorIndices, scene, path, attributeName, shaderName, parameterName, parameterValue, numPredecessors ) :

		ah = self.__predecessor( attributeHistory, predecessorIndices )

		self.assertIsInstance( ah, GafferScene.SceneAlgo.AttributeHistory )
		self.assertEqual( ah.scene, scene )
		self.assertEqual( GafferScene.ScenePlug.pathToString( ah.context["scene:path"] ), path )
		self.assertEqual( ah.attributeName, attributeName )
		self.assertEqual( ah.attributeValue.shaders()[shaderName].parameters[parameterName].value, parameterValue )
		self.assertEqual( len( ah.predecessors ), numPredecessors )

	def __assertOptionHistory( self, optionHistory, predecessorIndices, scene, optionName, optionValue, numPredecessors ) :

		oh = self.__predecessor( optionHistory, predecessorIndices )

		self.assertIsInstance( oh, GafferScene.SceneAlgo.OptionHistory )
		self.assertEqual( oh.scene, scene )
		self.assertNotIn( "scene:path", oh.context )
		self.assertEqual( oh.optionName, optionName )
		self.assertEqual( oh.optionValue.value, optionValue )
		self.assertEqual( len( oh.predecessors ), numPredecessors )

	def testAttributeHistory( self ) :

		# Build network
		# -------------
		#
		#    plane       sphere
		#      |           |
		# attributes1  attributes2
		#       \         /
		#        \       /
		#         \     /
		#      copyAttributes
		#            |
		#          group
		#            |
		#        attributes3

		plane = GafferScene.Plane()
		planeFilter = GafferScene.PathFilter()
		planeFilter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		sphere = GafferScene.Sphere()
		sphereFilter = GafferScene.PathFilter()
		sphereFilter["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )

		attributes1 = GafferScene.CustomAttributes()
		attributes1["in"].setInput( plane["out"] )
		attributes1["filter"].setInput( planeFilter["out"] )
		attributes1["attributes"].addChild( Gaffer.NameValuePlug( "test", 1 ) )

		attributes2 = GafferScene.CustomAttributes()
		attributes2["in"].setInput( sphere["out"] )
		attributes2["filter"].setInput( sphereFilter["out"] )
		attributes2["attributes"].addChild( Gaffer.NameValuePlug( "test", 2 ) )

		copyAttributes = GafferScene.CopyAttributes()
		copyAttributes["in"].setInput( attributes1["out"] )
		copyAttributes["source"].setInput( attributes2["out"] )
		copyAttributes["filter"].setInput( planeFilter["out"] )
		copyAttributes["sourceLocation"].setValue( "/sphere" )
		copyAttributes["attributes"].setValue( "te*" )

		group = GafferScene.Group()
		group["in"][0].setInput( copyAttributes["out"] )

		groupPlaneFilter = GafferScene.PathFilter()
		groupPlaneFilter["paths"].setValue( IECore.StringVectorData( [ "/group/plane" ] ) )

		attributes3 = GafferScene.CustomAttributes()
		attributes3["in"].setInput( group["out"] )
		attributes3["filter"].setInput( groupPlaneFilter["out"] )
		attributes3["attributes"].addChild( Gaffer.NameValuePlug( "test", 3 ) )

		# Sanity check `history()`

		def predecessorScenes( h ) :

			return [ p.scene for p in h.predecessors ]

		history = GafferScene.SceneAlgo.history( attributes3["out"]["attributes"], "/group/plane" )
		self.assertEqual( predecessorScenes( history ), [ attributes3["in"] ] )
		self.assertEqual( predecessorScenes( self.__predecessor( history, [ 0 ] ) ), [ group["out"] ] )
		self.assertEqual( predecessorScenes( self.__predecessor( history, [ 0, 0 ] ) ), [ group["in"][0] ] )
		self.assertEqual( predecessorScenes( self.__predecessor( history, [ 0, 0, 0 ] ) ), [ copyAttributes["out"] ] )
		self.assertEqual( predecessorScenes( self.__predecessor( history, [ 0, 0, 0, 0 ] ) ), [ copyAttributes["in"], copyAttributes["source"] ] )
		self.assertEqual( predecessorScenes( self.__predecessor( history, [ 0, 0, 0, 0, 0 ] ) ), [ attributes1["out"] ] )
		self.assertEqual( predecessorScenes( self.__predecessor( history, [ 0, 0, 0, 0, 1 ] ) ), [ attributes2["out"] ] )
		self.assertEqual( predecessorScenes( self.__predecessor( history, [ 0, 0, 0, 0, 0, 0 ] ) ), [ attributes1["in"] ] )
		self.assertEqual( predecessorScenes( self.__predecessor( history, [ 0, 0, 0, 0, 1, 0 ] ) ), [ attributes2["in"] ] )
		self.assertEqual( predecessorScenes( self.__predecessor( history, [ 0, 0, 0, 0, 0, 0, 0 ] ) ), [ plane["out"] ] )
		self.assertEqual( predecessorScenes( self.__predecessor( history, [ 0, 0, 0, 0, 1, 0, 0 ] ) ), [ sphere["out"] ] )

		# Test `attributeHistory()`

		attributeHistory = GafferScene.SceneAlgo.attributeHistory( history, "test" )

		self.__assertAttributeHistory( attributeHistory, [], attributes3["out"], "/group/plane", "test", IECore.IntData( 3 ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0 ], attributes3["in"], "/group/plane", "test", IECore.IntData( 2 ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0 ], group["out"], "/group/plane", "test", IECore.IntData( 2 ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0 ], group["in"][0], "/plane", "test", IECore.IntData( 2 ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0, 0 ], copyAttributes["out"], "/plane", "test", IECore.IntData( 2 ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0, 0, 0 ], copyAttributes["source"], "/sphere", "test", IECore.IntData( 2 ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0, 0, 0, 0 ], attributes2["out"], "/sphere", "test", IECore.IntData( 2 ), 0 )

		# Test `attributeHistory()` with missing source location in `copyAttributes`

		def assertFromAttributes1() :

			history = GafferScene.SceneAlgo.history( attributes3["out"]["attributes"], "/group/plane" )
			attributeHistory = GafferScene.SceneAlgo.attributeHistory( history, "test" )

			self.__assertAttributeHistory( attributeHistory, [], attributes3["out"], "/group/plane", "test", IECore.IntData( 3 ), 1 )
			self.__assertAttributeHistory( attributeHistory, [ 0 ], attributes3["in"], "/group/plane", "test", IECore.IntData( 1 ), 1 )
			self.__assertAttributeHistory( attributeHistory, [ 0, 0 ], group["out"], "/group/plane", "test", IECore.IntData( 1 ), 1 )
			self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0 ], group["in"][0], "/plane", "test", IECore.IntData( 1 ), 1 )
			self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0, 0 ], copyAttributes["out"], "/plane", "test", IECore.IntData( 1 ), 1 )
			self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0, 0, 0 ], copyAttributes["in"], "/plane", "test", IECore.IntData( 1 ), 1 )
			self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0, 0, 0, 0 ], attributes1["out"], "/plane", "test", IECore.IntData( 1 ), 0 )

		copyAttributes["sourceLocation"].setValue( "" )
		assertFromAttributes1()

		copyAttributes["sourceLocation"].setValue( "/road/to/nowhere" )
		assertFromAttributes1()

		# Test `attributeHistory()` with missing source attribute in `copyAttributes`

		copyAttributes["sourceLocation"].setValue( "/sphere" )
		attributes2["enabled"].setValue( False )
		assertFromAttributes1()

		# Test `attributeHistory()` with `copyAttributes` disabled

		attributes2["enabled"].setValue( True )
		copyAttributes["enabled"].setValue( False )
		assertFromAttributes1()

		# Test `attributeHistory()` with `copyAttributes` unfiltered

		copyAttributes["enabled"].setValue( True )
		copyAttributes["filter"].setInput( None )
		assertFromAttributes1()

	def testAttributeHistoryWithShuffleAttributes( self ) :

		plane = GafferScene.Plane()

		planeFilter = GafferScene.PathFilter()
		planeFilter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		attributes = GafferScene.CustomAttributes()
		attributes["in"].setInput( plane["out"] )
		attributes["filter"].setInput( planeFilter["out"] )
		attributes["attributes"].addChild( Gaffer.NameValuePlug( "a", "a_value" ) )
		attributes["attributes"].addChild( Gaffer.NameValuePlug( "b", "b_value" ) )
		attributes["attributes"].addChild( Gaffer.NameValuePlug( "c", "c_value" ) )

		shuffleAttributes = GafferScene.ShuffleAttributes()
		shuffleAttributes["in"].setInput( attributes["out"] )
		shuffleAttributes["filter"].setInput( planeFilter["out"] )

		def assertShuffledHistory( source, destination ) :

			history = GafferScene.SceneAlgo.history( shuffleAttributes["out"]["attributes"], "/plane" )
			attributeHistory = GafferScene.SceneAlgo.attributeHistory( history, destination )

			if source is None :
				self.assertIsNone( attributeHistory )
				return

			self.__assertAttributeHistory( attributeHistory, [], shuffleAttributes["out"], "/plane", destination, IECore.StringData( source + "_value" ), 1 )
			self.__assertAttributeHistory( attributeHistory, [ 0 ], shuffleAttributes["in"], "/plane", source, IECore.StringData( source + "_value" ), 1 )
			self.__assertAttributeHistory( attributeHistory, [ 0, 0 ], attributes["out"], "/plane", source, IECore.StringData( source + "_value" ), 0 )

		# No shuffles

		assertShuffledHistory( "a", "a" )
		assertShuffledHistory( "b", "b" )
		assertShuffledHistory( "c", "c" )

		# Shuffles

		shuffleAttributes["shuffles"].addChild( Gaffer.ShufflePlug( source = "a", destination = "d" ) )
		shuffleAttributes["shuffles"].addChild( Gaffer.ShufflePlug( source = "b", destination = "c" ) )

		assertShuffledHistory( "a", "a" )
		assertShuffledHistory( "b", "b" )
		assertShuffledHistory( "b", "c" )
		assertShuffledHistory( "a", "d" )

		# Node disabled

		shuffleAttributes["enabled"].setValue( False )

		assertShuffledHistory( "a", "a" )
		assertShuffledHistory( "b", "b" )
		assertShuffledHistory( "c", "c" )
		assertShuffledHistory( None, "d" )

		# Filter disabled

		shuffleAttributes["enabled"].setValue( True )
		shuffleAttributes["filter"].setInput( None )

		assertShuffledHistory( "a", "a" )
		assertShuffledHistory( "b", "b" )
		assertShuffledHistory( "c", "c" )
		assertShuffledHistory( None, "d" )

	def testAttributeHistoryWithMergeScenes( self ) :

		#               plane                    sphere
		#                 /\                        |
		#                /  \                       |
		#               /    \                      |
		# planeAttributes1 planeAttributes2  sphereAttributes
		#               |     |                     |
		#                \    |  --------------------
		#                 |   |  |
		#               mergeScenes
		#

		plane = GafferScene.Plane()
		sphere = GafferScene.Sphere()

		planeFilter = GafferScene.PathFilter()
		planeFilter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		planeAttributes1 = GafferScene.CustomAttributes()
		planeAttributes1["in"].setInput( plane["out"] )
		planeAttributes1["filter"].setInput( planeFilter["out"] )
		planeAttributes1["attributes"].addChild( Gaffer.NameValuePlug( "a", "a1" ) )
		planeAttributes1["attributes"].addChild( Gaffer.NameValuePlug( "c", "c1" ) )

		planeAttributes2 = GafferScene.CustomAttributes()
		planeAttributes2["in"].setInput( plane["out"] )
		planeAttributes2["filter"].setInput( planeFilter["out"] )
		planeAttributes2["attributes"].addChild( Gaffer.NameValuePlug( "a", "a2" ) )
		planeAttributes2["attributes"].addChild( Gaffer.NameValuePlug( "b", "b2" ) )

		sphereFilter = GafferScene.PathFilter()
		sphereFilter["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )

		sphereAttributes = GafferScene.CustomAttributes()
		sphereAttributes["in"].setInput( sphere["out"] )
		sphereAttributes["filter"].setInput( sphereFilter["out"] )
		sphereAttributes["attributes"].addChild( Gaffer.NameValuePlug( "c", "c" ) )

		mergeScenes = GafferScene.MergeScenes()
		mergeScenes["in"][0].setInput( planeAttributes1["out"] )
		mergeScenes["in"][1].setInput( planeAttributes2["out"] )
		mergeScenes["in"][2].setInput( sphereAttributes["out"] )

		# Test Keep mode

		mergeScenes["attributesMode"].setValue( mergeScenes.Mode.Keep )

		def assertAttributeHistory( path, attributeName, mergeScenesInput, value ) :

			history = GafferScene.SceneAlgo.history( mergeScenes["out"]["attributes"], path )
			attributeHistory = GafferScene.SceneAlgo.attributeHistory( history, attributeName )

			if value is None :
				self.assertIsNone( attributeHistory )
				return

			self.__assertAttributeHistory( attributeHistory, [], mergeScenes["out"], path, attributeName, IECore.StringData( value ), 1 )
			self.__assertAttributeHistory( attributeHistory, [ 0 ], mergeScenesInput, path, attributeName, IECore.StringData( value ), 1 )
			self.__assertAttributeHistory( attributeHistory, [ 0, 0 ], mergeScenesInput.getInput(), path, attributeName, IECore.StringData( value ), 0 )

		assertAttributeHistory( "/plane", "a", mergeScenes["in"][0], "a1" )
		assertAttributeHistory( "/plane", "b", None, None )
		assertAttributeHistory( "/plane", "c", mergeScenes["in"][0], "c1" )

		assertAttributeHistory( "/sphere", "a", None, None )
		assertAttributeHistory( "/sphere", "b", None, None )
		assertAttributeHistory( "/sphere", "c", mergeScenes["in"][2], "c" )

		# Test Merge mode

		mergeScenes["attributesMode"].setValue( mergeScenes.Mode.Merge )

		assertAttributeHistory( "/plane", "a", mergeScenes["in"][1], "a2" )
		assertAttributeHistory( "/plane", "b", mergeScenes["in"][1], "b2" )
		assertAttributeHistory( "/plane", "c", mergeScenes["in"][0], "c1" )

		assertAttributeHistory( "/sphere", "a", None, None )
		assertAttributeHistory( "/sphere", "b", None, None )
		assertAttributeHistory( "/sphere", "c", mergeScenes["in"][2], "c" )

		# Test Keep mode

		mergeScenes["attributesMode"].setValue( mergeScenes.Mode.Replace )

		assertAttributeHistory( "/plane", "a", mergeScenes["in"][1], "a2" )
		assertAttributeHistory( "/plane", "b", mergeScenes["in"][1], "b2" )
		assertAttributeHistory( "/plane", "c", None, None )

		assertAttributeHistory( "/sphere", "a", None, None )
		assertAttributeHistory( "/sphere", "b", None, None )
		assertAttributeHistory( "/sphere", "c", mergeScenes["in"][2], "c" )

	def testAttributeHistoryWithLocaliseAttributes( self ) :

		# Graph
		# -----
		#
		#        plane
		#          |
		#    planeAttributes
		#          |
		#      innerGroup
		#          |
		#      outerGroup
		#          |
		#    innerAttributes
		#          |
		#    outerAttributes
		#
		# Hierarchy and attributes
		# ------------------------
		#
		#  /outer         a b c
		#    /inner       a b
		#       /plane    a
		#

		plane = GafferScene.Plane()

		planeFilter = GafferScene.PathFilter()
		planeFilter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		planeAttributes = GafferScene.CustomAttributes()
		planeAttributes["in"].setInput( plane["out"] )
		planeAttributes["filter"].setInput( planeFilter["out"] )
		planeAttributes["attributes"].addChild( Gaffer.NameValuePlug( "a", "planeA" ) )

		innerGroup = GafferScene.Group()
		innerGroup["in"][0].setInput( planeAttributes["out"] )
		innerGroup["name"].setValue( "inner" )

		outerGroup = GafferScene.Group()
		outerGroup["in"][0].setInput( innerGroup["out"] )
		outerGroup["name"].setValue( "outer" )

		innerFilter = GafferScene.PathFilter()
		innerFilter["paths"].setValue( IECore.StringVectorData( [ "/outer/inner" ] ) )

		innerAttributes = GafferScene.CustomAttributes()
		innerAttributes["in"].setInput( outerGroup["out"] )
		innerAttributes["filter"].setInput( innerFilter["out"] )
		innerAttributes["attributes"].addChild( Gaffer.NameValuePlug( "a", "innerA" ) )
		innerAttributes["attributes"].addChild( Gaffer.NameValuePlug( "b", "innerB" ) )

		outerFilter = GafferScene.PathFilter()
		outerFilter["paths"].setValue( IECore.StringVectorData( [ "/outer" ] ) )

		outerAttributes = GafferScene.CustomAttributes()
		outerAttributes["in"].setInput( innerAttributes["out"] )
		outerAttributes["filter"].setInput( outerFilter["out"] )
		outerAttributes["attributes"].addChild( Gaffer.NameValuePlug( "a", "outerA" ) )
		outerAttributes["attributes"].addChild( Gaffer.NameValuePlug( "b", "outerB" ) )
		outerAttributes["attributes"].addChild( Gaffer.NameValuePlug( "c", "outerC" ) )

		# Test history before localisation

		history = GafferScene.SceneAlgo.history( outerAttributes["out"]["attributes"], "/outer/inner/plane" )
		attributeHistory = GafferScene.SceneAlgo.attributeHistory( history, "a" )

		self.__assertAttributeHistory( attributeHistory, [], outerAttributes["out"], "/outer/inner/plane", "a", IECore.StringData( "planeA" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0 ], outerAttributes["in"], "/outer/inner/plane", "a", IECore.StringData( "planeA" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0 ], innerAttributes["out"], "/outer/inner/plane", "a", IECore.StringData( "planeA" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0 ], innerAttributes["in"], "/outer/inner/plane", "a", IECore.StringData( "planeA" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0, 0 ], outerGroup["out"], "/outer/inner/plane", "a", IECore.StringData( "planeA" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0, 0, 0 ], outerGroup["in"][0], "/inner/plane", "a", IECore.StringData( "planeA" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0, 0, 0, 0 ], innerGroup["out"], "/inner/plane", "a", IECore.StringData( "planeA" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0, 0, 0, 0, 0 ], innerGroup["in"][0], "/plane", "a", IECore.StringData( "planeA" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0, 0, 0, 0, 0, 0 ], planeAttributes["out"], "/plane", "a", IECore.StringData( "planeA" ), 0 )

		self.assertIsNone( GafferScene.SceneAlgo.attributeHistory( history, "b" ) )
		self.assertIsNone( GafferScene.SceneAlgo.attributeHistory( history, "c" ) )

		# Add localisation

		localiseFilter = GafferScene.PathFilter()
		localiseFilter["paths"].setValue( IECore.StringVectorData( [ "/outer/inner/plane" ] ) )

		localise = GafferScene.LocaliseAttributes()
		localise["in"].setInput( outerAttributes["out"] )
		localise["filter"].setInput( localiseFilter["out"] )
		localise["attributes"].setValue( "*" )

		# Test attribute "a"

		history = GafferScene.SceneAlgo.history( localise["out"]["attributes"], "/outer/inner/plane" )
		attributeHistory = GafferScene.SceneAlgo.attributeHistory( history, "a" )

		self.__assertAttributeHistory( attributeHistory, [], localise["out"], "/outer/inner/plane", "a", IECore.StringData( "planeA" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0 ], localise["in"], "/outer/inner/plane", "a", IECore.StringData( "planeA" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0 ], outerAttributes["out"], "/outer/inner/plane", "a", IECore.StringData( "planeA" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0 ], outerAttributes["in"], "/outer/inner/plane", "a", IECore.StringData( "planeA" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0, 0 ], innerAttributes["out"], "/outer/inner/plane", "a", IECore.StringData( "planeA" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0, 0, 0 ], innerAttributes["in"], "/outer/inner/plane", "a", IECore.StringData( "planeA" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0, 0, 0, 0 ], outerGroup["out"], "/outer/inner/plane", "a", IECore.StringData( "planeA" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0, 0, 0, 0, 0 ], outerGroup["in"][0], "/inner/plane", "a", IECore.StringData( "planeA" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0, 0, 0, 0, 0, 0 ], innerGroup["out"], "/inner/plane", "a", IECore.StringData( "planeA" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0, 0, 0, 0, 0, 0, 0 ], innerGroup["in"][0], "/plane", "a", IECore.StringData( "planeA" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ], planeAttributes["out"], "/plane", "a", IECore.StringData( "planeA" ), 0 )

		# Test attribute "b"

		attributeHistory = GafferScene.SceneAlgo.attributeHistory( history, "b" )

		self.__assertAttributeHistory( attributeHistory, [], localise["out"], "/outer/inner/plane", "b", IECore.StringData( "innerB" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0 ], localise["in"], "/outer/inner", "b", IECore.StringData( "innerB" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0 ], outerAttributes["out"], "/outer/inner", "b", IECore.StringData( "innerB" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0 ], outerAttributes["in"], "/outer/inner", "b", IECore.StringData( "innerB" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0, 0 ], innerAttributes["out"], "/outer/inner", "b", IECore.StringData( "innerB" ), 0 )

		# Test attribute "c"

		attributeHistory = GafferScene.SceneAlgo.attributeHistory( history, "c" )

		self.__assertAttributeHistory( attributeHistory, [], localise["out"], "/outer/inner/plane", "c", IECore.StringData( "outerC" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0 ], localise["in"], "/outer", "c", IECore.StringData( "outerC" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0 ], outerAttributes["out"], "/outer", "c", IECore.StringData( "outerC" ), 0 )

		# Test location not touched by LocaliseAttributes

		history = GafferScene.SceneAlgo.history( localise["out"]["attributes"], "/outer/inner" )

		attributeHistory = GafferScene.SceneAlgo.attributeHistory( history, "a" )
		self.__assertAttributeHistory( attributeHistory, [], localise["out"], "/outer/inner", "a", IECore.StringData( "innerA" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0 ], localise["in"], "/outer/inner", "a", IECore.StringData( "innerA" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0 ], outerAttributes["out"], "/outer/inner", "a", IECore.StringData( "innerA" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0 ], outerAttributes["in"], "/outer/inner", "a", IECore.StringData( "innerA" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0, 0 ], innerAttributes["out"], "/outer/inner", "a", IECore.StringData( "innerA" ), 0 )

		attributeHistory = GafferScene.SceneAlgo.attributeHistory( history, "b" )
		self.__assertAttributeHistory( attributeHistory, [], localise["out"], "/outer/inner", "b", IECore.StringData( "innerB" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0 ], localise["in"], "/outer/inner", "b", IECore.StringData( "innerB" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0 ], outerAttributes["out"], "/outer/inner", "b", IECore.StringData( "innerB" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0 ], outerAttributes["in"], "/outer/inner", "b", IECore.StringData( "innerB" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0, 0 ], innerAttributes["out"], "/outer/inner", "b", IECore.StringData( "innerB" ), 0 )

		self.assertIsNone( GafferScene.SceneAlgo.attributeHistory( history, "c" ) )

	def testAttributeHistoryWithAttributeTweaks( self ) :

		# Graph
		# -----
		#
		#        plane
		#          |
		#    planeAttributes
		#          |
		#      innerGroup
		#          |
		#      outerGroup
		#          |
		#    innerAttributes
		#          |
		#    outerAttributes
		#
		# Hierarchy and attributes
		# ------------------------
		#
		#  /outer         a b c
		#    /inner       a b
		#       /plane    a
		#

		plane = GafferScene.Plane()

		planeFilter = GafferScene.PathFilter()
		planeFilter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		planeAttributes = GafferScene.CustomAttributes()
		planeAttributes["in"].setInput( plane["out"] )
		planeAttributes["filter"].setInput( planeFilter["out"] )
		planeAttributes["attributes"].addChild( Gaffer.NameValuePlug( "a", "planeA" ) )

		innerGroup = GafferScene.Group()
		innerGroup["in"][0].setInput( planeAttributes["out"] )
		innerGroup["name"].setValue( "inner" )

		outerGroup = GafferScene.Group()
		outerGroup["in"][0].setInput( innerGroup["out"] )
		outerGroup["name"].setValue( "outer" )

		innerFilter = GafferScene.PathFilter()
		innerFilter["paths"].setValue( IECore.StringVectorData( [ "/outer/inner" ] ) )

		innerAttributes = GafferScene.CustomAttributes()
		innerAttributes["in"].setInput( outerGroup["out"] )
		innerAttributes["filter"].setInput( innerFilter["out"] )
		innerAttributes["attributes"].addChild( Gaffer.NameValuePlug( "a", "innerA" ) )
		innerAttributes["attributes"].addChild( Gaffer.NameValuePlug( "b", "innerB" ) )

		outerFilter = GafferScene.PathFilter()
		outerFilter["paths"].setValue( IECore.StringVectorData( [ "/outer" ] ) )

		outerAttributes = GafferScene.CustomAttributes()
		outerAttributes["in"].setInput( innerAttributes["out"] )
		outerAttributes["filter"].setInput( outerFilter["out"] )
		outerAttributes["attributes"].addChild( Gaffer.NameValuePlug( "a", "outerA" ) )
		outerAttributes["attributes"].addChild( Gaffer.NameValuePlug( "b", "outerB" ) )
		outerAttributes["attributes"].addChild( Gaffer.NameValuePlug( "c", "outerC" ) )

		tweaksFilter = GafferScene.PathFilter()
		tweaksFilter["paths"].setValue( IECore.StringVectorData( [ "/outer/inner/plane" ] ) )

		tweaks = GafferScene.AttributeTweaks()
		tweaks["in"].setInput( outerAttributes["out"] )
		tweaks["filter"].setInput( tweaksFilter["out"] )

		# No tweaks yet

		history = GafferScene.SceneAlgo.history( tweaks["out"]["attributes"], "/outer/inner/plane" )
		attributeHistory = GafferScene.SceneAlgo.attributeHistory( history, "a" )

		self.__assertAttributeHistory( attributeHistory, [], tweaks["out"], "/outer/inner/plane", "a", IECore.StringData( "planeA" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0 ], tweaks["in"], "/outer/inner/plane", "a", IECore.StringData( "planeA" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0 ], outerAttributes["out"], "/outer/inner/plane", "a", IECore.StringData( "planeA" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0 ], outerAttributes["in"], "/outer/inner/plane", "a", IECore.StringData( "planeA" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0, 0 ], innerAttributes["out"], "/outer/inner/plane", "a", IECore.StringData( "planeA" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0, 0, 0 ], innerAttributes["in"], "/outer/inner/plane", "a", IECore.StringData( "planeA" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0, 0, 0, 0 ], outerGroup["out"], "/outer/inner/plane", "a", IECore.StringData( "planeA" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0, 0, 0, 0, 0 ], outerGroup["in"][0], "/inner/plane", "a", IECore.StringData( "planeA" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0, 0, 0, 0, 0, 0 ], innerGroup["out"], "/inner/plane", "a", IECore.StringData( "planeA" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0, 0, 0, 0, 0, 0, 0 ], innerGroup["in"][0], "/plane", "a", IECore.StringData( "planeA" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ], planeAttributes["out"], "/plane", "a", IECore.StringData( "planeA" ), 0 )

		# Without localisation, "b" and "c" have no history

		self.assertIsNone( GafferScene.SceneAlgo.attributeHistory( history, "b" ) )
		self.assertIsNone( GafferScene.SceneAlgo.attributeHistory( history, "c" ) )

		# Add tweak on plane attribute

		tweakA = Gaffer.TweakPlug( "a", "tweakA" )
		tweaks["tweaks"].addChild( tweakA )

		history = GafferScene.SceneAlgo.history( tweaks["out"]["attributes"], "/outer/inner/plane" )
		attributeHistory = GafferScene.SceneAlgo.attributeHistory( history, "a" )

		self.__assertAttributeHistory( attributeHistory, [], tweaks["out"], "/outer/inner/plane", "a", IECore.StringData( "tweakA" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0 ], tweaks["in"], "/outer/inner/plane", "a", IECore.StringData( "planeA" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0 ], outerAttributes["out"], "/outer/inner/plane", "a", IECore.StringData( "planeA" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0 ], outerAttributes["in"], "/outer/inner/plane", "a", IECore.StringData( "planeA" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0, 0 ], innerAttributes["out"], "/outer/inner/plane", "a", IECore.StringData( "planeA" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0, 0, 0 ], innerAttributes["in"], "/outer/inner/plane", "a", IECore.StringData( "planeA" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0, 0, 0, 0 ], outerGroup["out"], "/outer/inner/plane", "a", IECore.StringData( "planeA" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0, 0, 0, 0, 0 ], outerGroup["in"][0], "/inner/plane", "a", IECore.StringData( "planeA" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0, 0, 0, 0, 0, 0 ], innerGroup["out"], "/inner/plane", "a", IECore.StringData( "planeA" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0, 0, 0, 0, 0, 0, 0 ], innerGroup["in"][0], "/plane", "a", IECore.StringData( "planeA" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ], planeAttributes["out"], "/plane", "a", IECore.StringData( "planeA" ), 0 )

		self.assertIsNone( GafferScene.SceneAlgo.attributeHistory( history, "b" ) )
		self.assertIsNone( GafferScene.SceneAlgo.attributeHistory( history, "c" ) )

		# Add tweaks to inherited attributes

		tweakB = Gaffer.TweakPlug( "b", "tweakB" )
		tweakC = Gaffer.TweakPlug( "c", "tweakC" )

		tweaks["tweaks"].addChild( tweakB )
		tweaks["tweaks"].addChild( tweakC )

		# Fail while `localise` and `ignoreMissing` are off

		with self.assertRaisesRegex( RuntimeError, "Cannot apply tweak with mode Replace to \"b\" : This parameter does not exist" ) :
			history = GafferScene.SceneAlgo.history( tweaks["out"]["attributes"], "/outer/inner/plane" )
			GafferScene.SceneAlgo.attributeHistory( history, "b" )

		# Localise will get the attributes from parent locations

		tweaks["localise"].setValue( True )

		# Test attribute "b"

		history = GafferScene.SceneAlgo.history( tweaks["out"]["attributes"], "/outer/inner/plane" )
		attributeHistory = GafferScene.SceneAlgo.attributeHistory( history, "b" )

		self.__assertAttributeHistory( attributeHistory, [], tweaks["out"], "/outer/inner/plane", "b", IECore.StringData( "tweakB" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0 ], tweaks["in"], "/outer/inner", "b", IECore.StringData( "innerB" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0 ], outerAttributes["out"], "/outer/inner", "b", IECore.StringData( "innerB" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0 ], outerAttributes["in"], "/outer/inner", "b", IECore.StringData( "innerB" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0, 0 ], innerAttributes["out"], "/outer/inner", "b", IECore.StringData( "innerB" ), 0 )

		# Test attribute "c"

		attributeHistory = GafferScene.SceneAlgo.attributeHistory( history, "c" )

		self.__assertAttributeHistory( attributeHistory, [], tweaks["out"], "/outer/inner/plane", "c", IECore.StringData( "tweakC" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0 ], tweaks["in"], "/outer", "c", IECore.StringData( "outerC" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0 ], outerAttributes["out"], "/outer", "c", IECore.StringData( "outerC" ), 0 )

		# Localise is on, remove parent attribute tweak "b"

		tweaks["tweaks"].removeChild( tweakB )

		history = GafferScene.SceneAlgo.history( tweaks["out"]["attributes"], "/outer/inner/plane" )
		attributeHistory = GafferScene.SceneAlgo.attributeHistory( history, "b" )

		self.assertIsNone( GafferScene.SceneAlgo.attributeHistory( history, "b" ) )

	def testParameterHistoryWithShaderTweaks( self ) :

		# Graph
		# -----
		#
		#       light
		#         |
		#       group
		#         |
		#    shaderTweaks
		#

		testLight = GafferSceneTest.TestLight()
		testLight["visualiserAttributes"]["scale"]["enabled"].setValue( True )

		group = GafferScene.Group()
		group["in"][0].setInput( testLight["out"] )

		lightFilter = GafferScene.PathFilter()
		lightFilter["paths"].setValue( IECore.StringVectorData( [ "/group/light" ] ) )

		tweaks = GafferScene.ShaderTweaks()
		tweaks["in"].setInput( group["out"] )
		tweaks["filter"].setInput( lightFilter["out"] )
		tweaks["shader"].setValue( "light" )
		tweaks["localise"].setValue( True )

		tweak = Gaffer.TweakPlug( "exposure", 2.0 )
		tweaks["tweaks"].addChild( tweak )

		history = GafferScene.SceneAlgo.history( tweaks["out"]["attributes"], "/group/light" )
		attributeHistory = GafferScene.SceneAlgo.attributeHistory( history, "light" )

		self.__assertParameterHistory( attributeHistory, [], tweaks["out"], "/group/light", "light", "__shader", "exposure", 2.0, 1 )
		self.__assertParameterHistory( attributeHistory, [ 0 ], tweaks["in"], "/group/light", "light", "__shader", "exposure", 0.0, 1 )
		self.__assertParameterHistory( attributeHistory, [ 0, 0 ], group["out"], "/group/light", "light", "__shader", "exposure", 0.0, 1 )
		self.__assertParameterHistory( attributeHistory, [ 0, 0, 0 ], group["in"][0], "/light", "light", "__shader", "exposure", 0.0, 1 )
		self.__assertParameterHistory( attributeHistory, [ 0, 0, 0, 0 ], testLight["out"], "/light", "light", "__shader", "exposure", 0.0, 0 )

	def testAttributeHistoryWithMissingAttribute( self ) :

		# Attribute doesn't exist, so we return None.

		plane = GafferScene.Plane()
		attributesHistory = GafferScene.SceneAlgo.history( plane["out"]["attributes"], "/plane" )
		self.assertIsNone( GafferScene.SceneAlgo.attributeHistory( attributesHistory, "test" ) )

	def testOptionHistory( self ) :

		# Build network
		# -------------
		#
		# standardOptions
		#      |
		# optionTweaks  customOptions
		#       \         /
		#        \       /
		#         \     /
		#      copyOptions

		options = GafferScene.StandardOptions()
		options["options"]["renderCamera"]["enabled"].setValue( True )
		options["options"]["renderCamera"]["value"].setValue( "/renderCamera" )
		options["options"]["resolutionMultiplier"]["enabled"].setValue( True )
		options["options"]["resolutionMultiplier"]["value"].setValue( 2.0 )

		tweaks = GafferScene.OptionTweaks()
		tweaks["in"].setInput( options["out"] )

		tweak = Gaffer.TweakPlug( "render:camera", "/tweakCamera" )
		tweaks["tweaks"].addChild( tweak )

		customOptions = GafferScene.CustomOptions()
		customOptions["options"].addChild( Gaffer.NameValuePlug( "render:camera", "/customCamera" ) )
		customOptions["options"].addChild( Gaffer.NameValuePlug( "render:resolutionMultiplier", 4.0 ) )

		copyOptions = GafferScene.CopyOptions()
		copyOptions["in"].setInput( tweaks["out"] )
		copyOptions["source"].setInput( customOptions["out"] )

		def assertResolutionMultiplierFromStandardOptions() :

			history = GafferScene.SceneAlgo.history( copyOptions["out"]["globals"] )
			optionHistory = GafferScene.SceneAlgo.optionHistory( history, "render:resolutionMultiplier" )

			self.__assertOptionHistory( optionHistory, [], copyOptions["out"], "render:resolutionMultiplier", 2.0, 1 )
			self.__assertOptionHistory( optionHistory, [ 0 ], copyOptions["in"], "render:resolutionMultiplier", 2.0, 1 )
			self.__assertOptionHistory( optionHistory, [ 0, 0 ], tweaks["out"], "render:resolutionMultiplier", 2.0, 1 )
			self.__assertOptionHistory( optionHistory, [ 0, 0, 0 ], tweaks["in"], "render:resolutionMultiplier", 2.0, 1 )
			self.__assertOptionHistory( optionHistory, [ 0, 0, 0, 0 ], options["out"], "render:resolutionMultiplier", 2.0, 0 )

		def assertResolutionMultiplierFromCustomOptions() :

			history = GafferScene.SceneAlgo.history( copyOptions["out"]["globals"] )
			optionHistory = GafferScene.SceneAlgo.optionHistory( history, "render:resolutionMultiplier" )

			self.__assertOptionHistory( optionHistory, [], copyOptions["out"], "render:resolutionMultiplier", 4.0, 1 )
			self.__assertOptionHistory( optionHistory, [ 0 ], copyOptions["source"], "render:resolutionMultiplier", 4.0, 1 )
			self.__assertOptionHistory( optionHistory, [ 0, 0 ], customOptions["out"], "render:resolutionMultiplier", 4.0, 0 )

		def assertRenderCameraFromStandardOptions() :

			history = GafferScene.SceneAlgo.history( copyOptions["out"]["globals"] )
			optionHistory = GafferScene.SceneAlgo.optionHistory( history, "render:camera" )

			self.__assertOptionHistory( optionHistory, [], copyOptions["out"], "render:camera", "/tweakCamera", 1 )
			self.__assertOptionHistory( optionHistory, [ 0 ], copyOptions["in"], "render:camera", "/tweakCamera", 1 )
			self.__assertOptionHistory( optionHistory, [ 0, 0 ], tweaks["out"], "render:camera", "/tweakCamera", 1 )
			self.__assertOptionHistory( optionHistory, [ 0, 0, 0 ], tweaks["in"], "render:camera", "/renderCamera", 1 )
			self.__assertOptionHistory( optionHistory, [ 0, 0, 0, 0 ], options["out"], "render:camera", "/renderCamera", 0 )


		def assertRenderCameraFromCustomOptions() :

			history = GafferScene.SceneAlgo.history( copyOptions["out"]["globals"] )
			optionHistory = GafferScene.SceneAlgo.optionHistory( history, "render:camera" )

			self.__assertOptionHistory( optionHistory, [], copyOptions["out"], "render:camera", "/customCamera", 1 )
			self.__assertOptionHistory( optionHistory, [ 0 ], copyOptions["source"], "render:camera", "/customCamera", 1 )
			self.__assertOptionHistory( optionHistory, [ 0, 0 ], customOptions["out"], "render:camera", "/customCamera", 0 )

		# Test `optionHistory()` with "render:camera" copied

		copyOptions["options"].setValue( "render:ca*" )
		assertRenderCameraFromCustomOptions()
		assertResolutionMultiplierFromStandardOptions()

		# Test `optionHistory()` with all "render:" options copied

		copyOptions["options"].setValue( "render:*" )
		assertRenderCameraFromCustomOptions()
		assertResolutionMultiplierFromCustomOptions()

		# Test `optionHistory()` with no options copied

		copyOptions["options"].setValue( "" )
		assertRenderCameraFromStandardOptions()
		assertResolutionMultiplierFromStandardOptions()

		# Test `optionHistory()` with an invalid option copied

		copyOptions["options"].setValue( "not:an:option" )
		assertRenderCameraFromStandardOptions()
		assertResolutionMultiplierFromStandardOptions()

		# Test `optionHistory()` with `copyOptions` disabled

		copyOptions["enabled"].setValue( False )
		assertRenderCameraFromStandardOptions()
		assertResolutionMultiplierFromStandardOptions()

	def testOptionHistoryWithMergeScenes( self ) :

		# Build network
		# -------------
		#
		# standardOptions  customOptions
		#         \         /
		#          \       /
		#           \     /
		#         mergeScenes

		options = GafferScene.StandardOptions()
		options["options"]["renderCamera"]["enabled"].setValue( True )
		options["options"]["renderCamera"]["value"].setValue( "/renderCamera" )
		options["options"]["resolutionMultiplier"]["enabled"].setValue( True )
		options["options"]["resolutionMultiplier"]["value"].setValue( 2.0 )

		customOptions = GafferScene.CustomOptions()
		customOptions["options"].addChild( Gaffer.NameValuePlug( "render:camera", "/altCamera" ) )
		customOptions["options"].addChild( Gaffer.NameValuePlug( "custom:camera", "/customCamera" ) )

		mergeScenes = GafferScene.MergeScenes()
		mergeScenes["in"][0].setInput( options["out"] )
		mergeScenes["in"][1].setInput( customOptions["out"] )

		def assertOptionHistory( optionName, mergeScenesInput, value ) :

			history = GafferScene.SceneAlgo.history( mergeScenes["out"]["globals"] )
			optionHistory = GafferScene.SceneAlgo.optionHistory( history, optionName )

			if value is None :
				self.assertIsNone( optionHistory )
				return

			self.__assertOptionHistory( optionHistory, [], mergeScenes["out"], optionName, value, 1 )
			self.__assertOptionHistory( optionHistory, [ 0 ], mergeScenesInput, optionName, value, 1 )
			self.__assertOptionHistory( optionHistory, [ 0, 0 ], mergeScenesInput.getInput(), optionName, value, 0 )

		# Test Keep mode

		mergeScenes["globalsMode"].setValue( mergeScenes.Mode.Keep )

		assertOptionHistory( "render:camera", mergeScenes["in"][0], "/renderCamera" )
		assertOptionHistory( "custom:camera", None, None )
		assertOptionHistory( "render:resolutionMultiplier", mergeScenes["in"][0], 2.0 )

		# Test Merge mode

		mergeScenes["globalsMode"].setValue( mergeScenes.Mode.Merge )

		assertOptionHistory( "render:camera", mergeScenes["in"][1], "/altCamera" )
		assertOptionHistory( "custom:camera", mergeScenes["in"][1], "/customCamera" )
		assertOptionHistory( "render:resolutionMultiplier", mergeScenes["in"][0], 2.0 )

		# Test Replace mode

		mergeScenes["globalsMode"].setValue( mergeScenes.Mode.Replace )

		assertOptionHistory( "render:camera", mergeScenes["in"][1], "/altCamera" )
		assertOptionHistory( "custom:camera", mergeScenes["in"][1], "/customCamera" )
		assertOptionHistory( "render:resolutionMultiplier", None, None )

	def testOptionHistoryWithMissingOption( self ) :

		# Option doesn't exist, so we return None.

		plane = GafferScene.Plane()
		globalsHistory = GafferScene.SceneAlgo.history( plane["out"]["globals"] )
		self.assertIsNone( GafferScene.SceneAlgo.optionHistory( globalsHistory, "test" ) )

	def testOptionHistoryWithContext( self ) :

		# Build network
		# -------------
		#
		# standardOptions  standardOptions
		#            \         /
		#             \       /
		#              \     /
		#            nameSwitch

		options = GafferScene.StandardOptions()
		options["options"]["renderCamera"]["enabled"].setValue( True )
		options["options"]["renderCamera"]["value"].setValue( "/010" )

		options2 = GafferScene.StandardOptions()
		options2["options"]["renderCamera"]["enabled"].setValue( True )
		options2["options"]["renderCamera"]["value"].setValue( "/020" )

		nameSwitch = Gaffer.NameSwitch()
		nameSwitch.setup( GafferScene.ScenePlug() )
		nameSwitch["selector"].setValue( "${shot}" )
		nameSwitch["in"][0]["name"].setValue( "010" )
		nameSwitch["in"][0]["value"].setInput( options["out"] )
		nameSwitch["in"][1]["name"].setValue( "020" )
		nameSwitch["in"][1]["value"].setInput( options2["out"] )

		def assertOptionHistory( optionName, nameSwitchInput, value ) :

			history = GafferScene.SceneAlgo.history( nameSwitch["out"]["value"]["globals"] )
			optionHistory = GafferScene.SceneAlgo.optionHistory( history, optionName )

			if value is None :
				self.assertIsNone( optionHistory )
				return

			self.__assertOptionHistory( optionHistory, [], nameSwitch["out"]["value"], optionName, value, 1 )
			self.__assertOptionHistory( optionHistory, [ 0 ], nameSwitchInput, optionName, value, 1 )
			self.__assertOptionHistory( optionHistory, [ 0, 0 ], nameSwitchInput.getInput(), optionName, value, 0 )

		with Gaffer.Context() as context :
			context["shot"] = "010"
			assertOptionHistory( "render:camera", nameSwitch["in"][0]["value"], "/010" )

			context["shot"] = "020"
			assertOptionHistory( "render:camera", nameSwitch["in"][1]["value"], "/020" )

			# Use SceneTestCase's ContextSanitiser to indirectly test that `scene:path`
			# isn't leaked into the context used to evaluate the globals.
			context["scene:path"] = IECore.InternedStringVectorData( [ "plane" ] )
			assertOptionHistory( "render:camera", nameSwitch["in"][1]["value"], "/020" )

	def testOptionHistoryWithExpression( self ) :

		script = Gaffer.ScriptNode()

		script["options"] = GafferScene.StandardOptions()
		script["options"]["options"]["renderCamera"]["enabled"].setValue( True )
		script["options"]["options"]["renderCamera"]["value"].setValue( "test" )

		script["dot"] = Gaffer.Dot()
		script["dot"].setup( script["options"]["out"] )
		script["dot"]["in"].setInput( script["options"]["out"] )

		script["expression"] = Gaffer.Expression()
		script["expression"].setExpression( inspect.cleandoc(
		"""
		globals = parent["dot"]["in"]["globals"]
		globals["option:render:camera"] = IECore.StringData( "expression" )
		parent["dot"]["out"]["globals"] = globals
		"""
		) )

		history = GafferScene.SceneAlgo.history( script["dot"]["out"]["globals"] )
		optionHistory = GafferScene.SceneAlgo.optionHistory( history, "render:camera" )

		self.__assertOptionHistory( optionHistory, [], script["dot"]["out"], "render:camera", "expression", 1 )
		self.__assertOptionHistory( optionHistory, [ 0 ], script["dot"]["in"], "render:camera", "test", 1 )
		self.__assertOptionHistory( optionHistory, [ 0, 0 ], script["options"]["out"], "render:camera", "test", 0 )

	def testHistoryWithExpression( self ) :

		script = Gaffer.ScriptNode()

		script["options"] = GafferScene.StandardOptions()
		script["options"]["options"]["renderCamera"]["enabled"].setValue( True )
		script["options"]["options"]["renderCamera"]["value"].setValue( "test" )

		script["dot"] = Gaffer.Dot()
		script["dot"].setup( script["options"]["out"] )
		script["dot"]["in"].setInput( script["options"]["out"] )

		script["expression"] = Gaffer.Expression()
		script["expression"].setExpression( inspect.cleandoc(
		"""
		globals = parent["dot"]["in"]["globals"]
		globals["option:render:camera"] = IECore.StringData( "expression" )
		parent["dot"]["out"]["globals"] = globals
		"""
		) )

		def runTest() :

			history = GafferScene.SceneAlgo.history( script["dot"]["out"]["globals"] )

			for plug in [
				script["dot"]["out"],
				script["dot"]["in"],
				script["options"]["out"],
			] :
				self.assertEqual( history.scene, plug )
				self.assertLessEqual( len( history.predecessors ), 1 )
				history = history.predecessors[0] if history.predecessors else None

			self.assertIsNone( history )

		# Test running the test while everything is already cached still works, and doesn't add any
		# new entries to the cache
		Gaffer.ValuePlug.clearHashCache()
		runTest()
		before = Gaffer.ValuePlug.hashCacheTotalUsage()
		runTest()
		self.assertEqual( Gaffer.ValuePlug.hashCacheTotalUsage(), before )

		# Test that even the processes that aren't reading the cache still write to the cache, by
		# making sure that a subsequent globalsHash doesn't need to do anything
		Gaffer.ValuePlug.clearHashCache()
		runTest()
		with Gaffer.PerformanceMonitor() as pm :
			script["dot"]["out"].globalsHash()
		self.assertEqual( pm.combinedStatistics().hashCount, 0 )

		# Test branching history with an expression using two input globals
		# to produce our output
		script["options2"] = GafferScene.StandardOptions()
		script["options2"]["options"]["renderCamera"]["enabled"].setValue( True )
		script["options2"]["options"]["renderCamera"]["value"].setValue( "other" )

		script["expression"].setExpression( inspect.cleandoc(
		"""
		globals = parent["dot"]["in"]["globals"]
		globals["option:render:camera"] = parent["options2"]["out"]["globals"].get( "option:render:camera" )
		parent["dot"]["out"]["globals"] = globals
		"""
		) )

		history = GafferScene.SceneAlgo.history( script["dot"]["out"]["globals"] )
		self.assertEqual( len( history.predecessors ), 2 )
		self.assertEqual( history.predecessors[0].scene, script["dot"]["in"] )
		self.assertEqual( history.predecessors[1].scene, script["options2"]["out"] )

		# Test that an expression using the value of a non-globals plug to modify the globals
		# does not affect the history
		script["cube"] = GafferScene.Cube()
		script["cube"]["sets"].setValue( "foo" )

		script["expression"].setExpression( inspect.cleandoc(
		"""
		globals = parent["dot"]["in"]["globals"]
		globals["option:render:camera"] = IECore.StringData( "expression" )
		globals["option:setNames"] = parent["cube"]["out"]["setNames"]
		parent["dot"]["out"]["globals"] = globals
		"""
		) )

		history = GafferScene.SceneAlgo.history( script["dot"]["out"]["globals"] )
		self.assertEqual( len( history.predecessors ), 1 )
		self.assertEqual( history.predecessors[0].scene, script["dot"]["in"] )

	def testHistoryWithCanceller( self ) :

		plane = GafferScene.Plane()
		group = GafferScene.Group()
		group["in"][0].setInput( plane["out"] )

		context = Gaffer.Context()
		canceller = IECore.Canceller()
		with Gaffer.Context( context, canceller ) :
			history = GafferScene.SceneAlgo.history( group["out"]["object"], "/group/plane" )

		def assertNoCanceller( history ) :

			self.assertIsNone( history.context.canceller() )
			for p in history.predecessors :
				assertNoCanceller( p )

		assertNoCanceller( history )

		shaderAssignment = GafferScene.ShaderAssignment()
		with Gaffer.Context( context, canceller ) :
			history = GafferScene.SceneAlgo.history( shaderAssignment["in"]["attributes"], "/" )

		assertNoCanceller( history )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testHistoryDiamondPerformance( self ) :

		# A series of diamonds where every iteration reads the output of the
		# previous iteration twice and then feeds into the next iteration.
		#
		#      o
		#     / \
		#    o   o
		#     \ /
		#      o
		#     / \
		#    o   o
		#     \ /
		#      o
		#     / \
		#     ...
		#     \ /
		#      o
		#
		# Without caching, this leads to an explosion of paths through the
		# graph, and can lead to poor performance in `history()`.

		plane = GafferScene.Plane()

		loop = Gaffer.Loop()
		loop.setup( plane["out"] )
		loop["in"].setInput( plane["out"] )

		copyOptions = GafferScene.CopyOptions()
		copyOptions["in"].setInput( loop["previous"] )
		copyOptions["source"].setInput( loop["previous"] )
		copyOptions["options"].setValue( "*" )

		loop["next"].setInput( copyOptions["out"] )
		loop["iterations"].setValue( 20 )

		with GafferTest.TestRunner.PerformanceScope() :
			GafferScene.SceneAlgo.history( loop["out"]["globals"] )

	def testLinkingQueries( self ) :

		# Everything linked to `defaultLights` via the default value for the attribute.

		defaultLight = GafferSceneTest.TestLight()
		defaultLight["name"].setValue( "defaultLight" )

		nonDefaultLight = GafferSceneTest.TestLight()
		nonDefaultLight["name"].setValue( "nonDefaultLight" )
		nonDefaultLight["defaultLight"].setValue( False )
		nonDefaultLight["sets"].setValue( "specialLights" )

		sphere = GafferScene.Sphere()
		cube = GafferScene.Cube()

		group = GafferScene.Group()
		group["in"][0].setInput( sphere["out"] )
		group["in"][1].setInput( cube["out"] )
		group["in"][2].setInput( defaultLight["out"] )
		group["in"][3].setInput( nonDefaultLight["out"] )

		self.assertEqual(
			GafferScene.SceneAlgo.linkedObjects( group["out"], "/group/defaultLight" ),
			IECore.PathMatcher( [ "/group", "/group/sphere", "/group/cube" ] )
		)
		self.assertEqual(
			GafferScene.SceneAlgo.linkedObjects( group["out"], "/group/nonDefaultLight" ),
			IECore.PathMatcher()
		)
		self.assertEqual(
			GafferScene.SceneAlgo.linkedObjects( group["out"], IECore.PathMatcher( [ "/group/defaultLight", "/group/nonDefaultLight" ] ) ),
			IECore.PathMatcher( [ "/group", "/group/sphere", "/group/cube" ] )
		)
		self.assertEqual(
			GafferScene.SceneAlgo.linkedLights( group["out"], "/group/cube" ),
			IECore.PathMatcher( [ "/group/defaultLight" ] )
		)
		self.assertEqual(
			GafferScene.SceneAlgo.linkedLights( group["out"], "/group/sphere" ),
			IECore.PathMatcher( [ "/group/defaultLight" ] )
		)
		self.assertEqual(
			GafferScene.SceneAlgo.linkedLights( group["out"], IECore.PathMatcher( [ "/group/sphere", "/group/cube" ] ) ),
			IECore.PathMatcher( [ "/group/defaultLight" ] )
		)

		# Cube relinked only to `specialLights`.

		cubeFilter = GafferScene.PathFilter()
		cubeFilter["paths"].setValue( IECore.StringVectorData( [ "/group/cube" ] ) )

		standardAttributes = GafferScene.StandardAttributes()
		standardAttributes["in"].setInput( group["out"] )
		standardAttributes["filter"].setInput( cubeFilter["out"] )
		standardAttributes["attributes"]["linkedLights"]["enabled"].setValue( True )
		standardAttributes["attributes"]["linkedLights"]["value"].setValue( "specialLights" )

		self.assertEqual(
			GafferScene.SceneAlgo.linkedObjects( standardAttributes["out"], "/group/defaultLight" ),
			IECore.PathMatcher( [ "/group", "/group/sphere" ] )
		)
		self.assertEqual(
			GafferScene.SceneAlgo.linkedObjects( standardAttributes["out"], "/group/nonDefaultLight" ),
			IECore.PathMatcher( [ "/group/cube" ] )
		)
		self.assertEqual(
			GafferScene.SceneAlgo.linkedObjects( standardAttributes["out"], IECore.PathMatcher( [ "/group/defaultLight", "/group/nonDefaultLight" ] ) ),
			IECore.PathMatcher( [ "/group", "/group/sphere", "/group/cube" ] )
		)
		self.assertEqual(
			GafferScene.SceneAlgo.linkedObjects( standardAttributes["out"], IECore.PathMatcher( [ "/group/defaultLight", "/group/nonDefaultLight" ] ) ),
			IECore.PathMatcher( [ "/group", "/group/sphere", "/group/cube" ] )
		)
		self.assertEqual(
			GafferScene.SceneAlgo.linkedLights( standardAttributes["out"], "/group/cube" ),
			IECore.PathMatcher( [ "/group/nonDefaultLight" ] )
		)
		self.assertEqual(
			GafferScene.SceneAlgo.linkedLights( standardAttributes["out"], "/group/sphere" ),
			IECore.PathMatcher( [ "/group/defaultLight" ] )
		)
		self.assertEqual(
			GafferScene.SceneAlgo.linkedLights( standardAttributes["out"], IECore.PathMatcher( [ "/group/sphere", "/group/cube" ] ) ),
			IECore.PathMatcher( [ "/group/defaultLight", "/group/nonDefaultLight" ] )
		)

		# Light removed from `specialLights` set.

		nonDefaultLight["sets"].setValue( "" )

		self.assertEqual(
			GafferScene.SceneAlgo.linkedObjects( standardAttributes["out"], "/group/defaultLight" ),
			IECore.PathMatcher( [ "/group", "/group/sphere" ] )
		)
		self.assertEqual(
			GafferScene.SceneAlgo.linkedObjects( standardAttributes["out"], "/group/nonDefaultLight" ),
			IECore.PathMatcher()
		)
		self.assertEqual(
			GafferScene.SceneAlgo.linkedLights( standardAttributes["out"], "/group/cube" ),
			IECore.PathMatcher()
		)
		self.assertEqual(
			GafferScene.SceneAlgo.linkedLights( standardAttributes["out"], "/group/sphere" ),
			IECore.PathMatcher( [ "/group/defaultLight" ] )
		)
		self.assertEqual(
			GafferScene.SceneAlgo.linkedLights( standardAttributes["out"], IECore.PathMatcher( [ "/group/sphere", "/group/cube" ] ) ),
			IECore.PathMatcher( [ "/group/defaultLight" ] )
		)

		# `/group/nonDefaultLight` treated as default again.

		nonDefaultLight["defaultLight"].setValue( True )

		self.assertEqual(
			GafferScene.SceneAlgo.linkedObjects( standardAttributes["out"], "/group/defaultLight" ),
			IECore.PathMatcher( [ "/group", "/group/sphere" ] )
		)
		self.assertEqual(
			GafferScene.SceneAlgo.linkedObjects( standardAttributes["out"], "/group/nonDefaultLight" ),
			IECore.PathMatcher( [ "/group", "/group/sphere" ] )
		)
		self.assertEqual(
			GafferScene.SceneAlgo.linkedLights( standardAttributes["out"], "/group/cube" ),
			IECore.PathMatcher()
		)
		self.assertEqual(
			GafferScene.SceneAlgo.linkedLights( standardAttributes["out"], "/group/sphere" ),
			IECore.PathMatcher( [ "/group/defaultLight", "/group/nonDefaultLight" ] )
		)
		self.assertEqual(
			GafferScene.SceneAlgo.linkedLights( standardAttributes["out"], IECore.PathMatcher( [ "/group/sphere", "/group/cube" ] ) ),
			IECore.PathMatcher( [  "/group/defaultLight", "/group/nonDefaultLight" ] )
		)

	def testMatchingPathsHash( self ) :

		# /group
		#    /sphere
		#    /cube

		sphere = GafferScene.Sphere()
		cube = GafferScene.Cube()

		group = GafferScene.Group()
		group["in"][0].setInput( sphere["out"] )
		group["in"][1].setInput( cube["out"] )

		filter1 = GafferScene.PathFilter()
		filter1["paths"].setValue( IECore.StringVectorData( [ "/*" ] ) )

		filter2 = GafferScene.PathFilter()
		filter2["paths"].setValue( IECore.StringVectorData( [ "/*/*" ] ) )

		filter3 = GafferScene.PathFilter()
		filter3["paths"].setValue( IECore.StringVectorData( [ "/gro??" ] ) )

		self.assertEqual(
			GafferScene.SceneAlgo.matchingPathsHash( filter1["out"], group["out"] ),
			GafferScene.SceneAlgo.matchingPathsHash( filter3["out"], group["out"] )
		)

		self.assertNotEqual(
			GafferScene.SceneAlgo.matchingPathsHash( filter1["out"], group["out"] ),
			GafferScene.SceneAlgo.matchingPathsHash( filter2["out"], group["out"] )
		)

		self.assertNotEqual(
			GafferScene.SceneAlgo.matchingPathsHash( filter2["out"], group["out"] ),
			GafferScene.SceneAlgo.matchingPathsHash( filter3["out"], group["out"] )
		)

		rootFilter = GafferScene.PathFilter()
		rootFilter["paths"].setValue( IECore.StringVectorData( [ "/" ] ) )
		emptyFilter = GafferScene.PathFilter()

		self.assertNotEqual(
			GafferScene.SceneAlgo.matchingPathsHash( rootFilter["out"], group["out"] ),
			GafferScene.SceneAlgo.matchingPathsHash( emptyFilter["out"], group["out"] )
		)

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testMatchingPathsHashPerformance( self ) :

		# Trick to make an infinitely recursive scene. This high-depth but
		# low-branching-factor scene is in deliberate contrast to the
		# lots-of-children-at-one-location scene used in
		# `FilterResultsTest.testHashPerformance()`. We need good parallel
		# performance for both topologies.
		scene = GafferScene.ScenePlug()
		scene["childNames"].setValue( IECore.InternedStringVectorData( [ "one", "two" ] ) )
		# We use a PathMatcher to limit the search recursion, matching
		# every item 22 deep, but no other.
		pathMatcher = IECore.PathMatcher( [ "/*" * 22 ] )

		with GafferTest.TestRunner.PerformanceScope() :
			GafferScene.SceneAlgo.matchingPathsHash( pathMatcher, scene )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testMatchingPathsPerformance( self ) :

		# See comments in `testMatchingPathsHashPerformance()`.
		scene = GafferScene.ScenePlug()
		scene["childNames"].setValue( IECore.InternedStringVectorData( [ "one", "two" ] ) )
		pathMatcher = IECore.PathMatcher( [ "/*" * 21 ] )

		with GafferTest.TestRunner.PerformanceScope() :
			result = IECore.PathMatcher()
			GafferScene.SceneAlgo.matchingPaths( pathMatcher, scene, result )

	def testHierarchyHash( self ) :

		# We need to check that changing basically anything about a scene will result in a unique hash

		baseGroup = GafferScene.Group()

		# Temporarily disable testing of bounds ( we're trying to test features independently here, and
		# a lot of the other things we're testing have cross-talk with the bounds )
		testScene = GafferScene.ScenePlug()
		testScene.setInput( baseGroup["out"] )
		testScene["bound"].setInput( None )

		hashes = set()
		def assertHashUnique():
			h = GafferScene.SceneAlgo.hierarchyHash( testScene, "/group" )
			self.assertNotIn( h, hashes )
			hashes.add( h )

		def assertHashNotUnique():
			h = GafferScene.SceneAlgo.hierarchyHash( testScene, "/group" )
			self.assertIn( h, hashes )

		assertHashUnique()

		cube = GafferScene.Cube()
		baseGroup["in"][0].setInput( cube["out"] )

		assertHashUnique()

		sphere = GafferScene.Sphere()
		baseGroup["in"][1].setInput( sphere["out"] )

		self.assertEqual( baseGroup["out"].childNames( "/group" ), IECore.InternedStringVectorData( [ "cube", "sphere" ] ) )
		assertHashUnique()

		# Documenting current edge case behaviour: changing the order of children, but nothing else.
		# We've decided we do want this to affect the hash.
		baseGroup["in"][1].setInput( cube["out"] )
		baseGroup["in"][0].setInput( sphere["out"] )
		self.assertEqual( baseGroup["out"].childNames( "/group" ), IECore.InternedStringVectorData( [ "sphere", "cube" ] ) )

		assertHashUnique()

		sphere["divisions"].setValue( imath.V2i( 3, 6 ) )

		assertHashUnique()

		sphere["transform"]["translate"]["x"].setValue( 2 )

		assertHashUnique()

		cube["transform"]["rotate"]["y"].setValue( 30 )

		assertHashUnique()

		sphereFilter = GafferScene.PathFilter()
		sphereFilter["paths"].setValue( IECore.StringVectorData( [ '/sphere' ] ) )
		customAttributes = GafferScene.CustomAttributes()
		customAttributes["in"].setInput( sphere["out"] )
		customAttributes["filter"].setInput( sphereFilter["out"] )
		baseGroup["in"][0].setInput( customAttributes["out"] )

		# No attributes added yet
		assertHashNotUnique()

		customAttributes["attributes"].addChild( Gaffer.NameValuePlug( "foo", Gaffer.StringPlug( "value", defaultValue = 'foo' ), True, "member1" ) )

		# But now it should change
		assertHashUnique()

		# We can add additional levels of hierarchy inside the scene we're traversing
		subGroup = GafferScene.Group()
		subGroup["in"][0].setInput( customAttributes["out"] )

		baseGroup["in"][0].setInput( subGroup["out"] )

		assertHashUnique()

		# And changes within the deeper hierarchy still affect the hash

		customAttributes["attributes"][0]["value"].setValue( "blah" )

		assertHashUnique()

		sphere["transform"]["translate"]["x"].setValue( 3 )

		assertHashUnique()

		# We've now tested basically everything with the exception of the bound - it's hard to specifically
		# test the bound - if we use existing Gaffer nodes, basically anything we do to affect the bound
		# would also affect one of the other properties we've already tested ... so we would see the hash
		# change, but it's hard to be certain of why. So instead, here's an extremely synthetic test just to
		# confirm that we do check the bound

		loosePlug = GafferScene.ScenePlug()
		hashA = GafferScene.SceneAlgo.hierarchyHash( loosePlug, "/" )
		loosePlug["bound"].setValue( imath.Box3f( imath.V3f( 0 ), imath.V3f( 1 ) ) )
		self.assertNotEqual( GafferScene.SceneAlgo.hierarchyHash( loosePlug, "/" ), hashA )

		# Hashing a hierarchy that is parented somewhere should have exactly the same effect

		group = GafferScene.Group()
		group["in"][0].setInput( baseGroup["out"] )

		self.assertEqual(
			GafferScene.SceneAlgo.hierarchyHash( baseGroup["out"], "/group" ),
			GafferScene.SceneAlgo.hierarchyHash( group["out"], "/group/group" )
		)

	def testHierarchyHashAssociativity( self ) :

		# A specific check that properties of children are bound to their names - switching which child
		# has which properties should result in a different hash. This test has been built with specific
		# attention to the internals of hierarchyHash - it is designed so that it would fail if the
		# mergeChildrenFunctor acted like the reduceFunctor and did encode a binding between child
		# properties and their location in the tree.

		sphere = GafferScene.Sphere()

		sphereFilter = GafferScene.PathFilter()
		sphereFilter["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )

		attributesA = GafferScene.CustomAttributes()
		attributesA["in"].setInput( sphere["out"] )
		attributesA["filter"].setInput( sphereFilter["out"] )
		attributesA["attributes"].addChild( Gaffer.NameValuePlug( "foo", Gaffer.StringPlug( "value", defaultValue = '' ), True, "member1" ) )

		attributesB = GafferScene.CustomAttributes()
		attributesB["in"].setInput( sphere["out"] )
		attributesB["filter"].setInput( sphereFilter["out"] )
		attributesB["attributes"].addChild( Gaffer.NameValuePlug( "foo", Gaffer.StringPlug( "value", defaultValue = '' ), True, "member1" ) )

		attributesA["attributes"][0]["value"].setValue( "AAA" )
		attributesB["attributes"][0]["value"].setValue( "BBB" )

		groupA = GafferScene.Group()
		groupA["in"][0].setInput( attributesA["out"] )

		groupB = GafferScene.Group()
		groupB["in"][0].setInput( attributesB["out"] )

		group = GafferScene.Group()
		group["in"][0].setInput( groupA["out"] )
		group["in"][1].setInput( groupB["out"] )

		h1 = GafferScene.SceneAlgo.hierarchyHash( group["out"], "/group" )

		attributesA["attributes"][0]["value"].setValue( "BBB" )
		attributesB["attributes"][0]["value"].setValue( "AAA" )

		h2 = GafferScene.SceneAlgo.hierarchyHash( group["out"], "/group" )

		self.assertNotEqual( h1, h2 )

	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 1 )
	def testHierarchyHashPerf( self ):

		sphere = GafferScene.Sphere()

		pathFilter = GafferScene.PathFilter()
		pathFilter["paths"].setValue( IECore.StringVectorData( [ '/sphere' ] ) )

		duplicate = GafferScene.Duplicate()
		duplicate["in"].setInput( sphere["out"] )
		duplicate["filter"].setInput( pathFilter["out"] )
		duplicate["copies"].setValue( 300000 )


		# Get everything warm - we want to measure the overhead of hierarchyHash, not the cost of
		# actually computing everything it requires
		GafferScene.SceneAlgo.hierarchyHash( duplicate["out"], "/" )

		# Even with this attempt to cache things, it's still not a very interesting test. What we
		# really want to know is whether we're imposing any extra overhead in how we combine hashes,
		# or with the machinery of parallelReduceLocations itself. But repeatedly hashing plugs is
		# so much more expensive than any of the other stuff that all we're doing, we're really just
		# seeing the time to do the hashes. This seems to be true even if I make the hash cache massive:
		# even pulling hashes from the cache has a cost.
		#
		# It's good that we're not imposing measurable overhead here, but it means this
		# doesn't tell us much about how well parallelReduceLocations can theoretically work.

		with GafferTest.TestRunner.PerformanceScope() :
			GafferScene.SceneAlgo.hierarchyHash( duplicate["out"], "/" )

	def testRenderAdaptors( self ) :

		sphere = GafferScene.Sphere()

		defaultAdaptors = GafferScene.SceneAlgo.createRenderAdaptors()
		defaultAdaptors["in"].setInput( sphere["out"] )

		def a() :

			r = GafferScene.StandardAttributes()
			r["attributes"]["doubleSided"]["enabled"].setValue( True )
			r["attributes"]["doubleSided"]["value"].setValue( False )

			return r

		GafferScene.SceneAlgo.registerRenderAdaptor( "Test", a )

		testAdaptors = GafferScene.SceneAlgo.createRenderAdaptors()
		testAdaptors["in"].setInput( sphere["out"] )

		self.assertFalse( "doubleSided" in sphere["out"].attributes( "/sphere" ) )
		self.assertTrue( "doubleSided" in testAdaptors["out"].attributes( "/sphere" ) )
		self.assertEqual( testAdaptors["out"].attributes( "/sphere" )["doubleSided"].value, False )

		GafferScene.SceneAlgo.deregisterRenderAdaptor( "Test" )

		defaultAdaptors2 = GafferScene.SceneAlgo.createRenderAdaptors()
		defaultAdaptors2["in"].setInput( sphere["out"] )

		self.assertScenesEqual( defaultAdaptors["out"], defaultAdaptors2["out"] )
		self.assertSceneHashesEqual( defaultAdaptors["out"], defaultAdaptors2["out"] )

	def testRenderAdaptorScope( self ) :

		def adaptor() :

			result = GafferScene.CustomOptions()
			result["options"].addChild( Gaffer.NameValuePlug( "adapted", True ) )
			return result

		for clientPattern, rendererPattern, client, renderer, expectAdapted in (
			( "*", "*", None, None, True ),
			( "*", "*", "Render", "Arnold", True ),
			( "*", "Arnold", "Render", "Arnold", True ),
			( "*", "Arnold", "Render", "Cycles", False ),
			( "Render", "*", "Render", "Arnold", True ),
			( "Render", "*", "InteractiveRender", "Arnold", False ),
			( "Render InteractiveRender", "*", "Render", "Arnold", True ),
			( "Render InteractiveRender", "*", "InteractiveRender", "Arnold", True ),
			( "Render InteractiveRender", "*", "SceneView", "Arnold", False ),
			( "Render", "Arnold", "SceneView", "Arnold", False ),
			( "Render", "Arnold", "Render", "Arnold", True ),
		) :
			with self.subTest( clientPattern = clientPattern, rendererPattern = rendererPattern, client = client, renderer = renderer ) :

				GafferScene.SceneAlgo.registerRenderAdaptor( "Test", adaptor, clientPattern, rendererPattern )
				self.addCleanup( GafferScene.SceneAlgo.deregisterRenderAdaptor, "Test" )

				adaptors = GafferScene.SceneAlgo.createRenderAdaptors()
				if client is not None :
					adaptors["client"].setValue( client )
				if renderer is not None :
					adaptors["renderer"].setValue( renderer )

				if expectAdapted :
					self.assertIn( "option:adapted", adaptors["out"].globals() )
				else :
					self.assertNotIn( "option:adapted", adaptors["out"].globals() )

	def testRenderAdaptorScopePlugs( self ) :

		def adaptor() :

			result = GafferScene.CustomOptions()
			result["client"] = Gaffer.StringPlug()
			result["renderer"] = Gaffer.StringPlug()

			result["options"].addChild( Gaffer.NameValuePlug( "theClient", "" ) )
			result["options"].addChild( Gaffer.NameValuePlug( "theRenderer", "" ) )

			result["options"][0]["value"].setInput( result["client"] )
			result["options"][1]["value"].setInput( result["renderer"] )

			return result

		for client, renderer in [
			( "*", "*" ),
			( "SceneView", "Arnold" ),
		] :

			with self.subTest( client = client, renderer = renderer ) :

				GafferScene.SceneAlgo.registerRenderAdaptor( "Test", adaptor, client, renderer )
				self.addCleanup( GafferScene.SceneAlgo.deregisterRenderAdaptor, "Test" )

				adaptors = GafferScene.SceneAlgo.createRenderAdaptors()
				adaptors["client"].setValue( "SceneView" )
				adaptors["renderer"].setValue( "Arnold" )

				self.assertEqual( adaptors["out"].globals()["option:theClient"].value, "SceneView" )
				self.assertEqual( adaptors["out"].globals()["option:theRenderer"].value, "Arnold" )

	def testNullAdaptor( self ) :

		def a() :

			return None

		GafferScene.SceneAlgo.registerRenderAdaptor( "Test", a )

		with IECore.CapturingMessageHandler() as mh :
			GafferScene.SceneAlgo.createRenderAdaptors()

		self.assertEqual( len( mh.messages ), 1 )
		self.assertEqual( mh.messages[0].level, IECore.Msg.Level.Warning )
		self.assertEqual( mh.messages[0].context, "SceneAlgo::createRenderAdaptors" )
		self.assertEqual( mh.messages[0].message, "Adaptor \"Test\" returned null" )

	def testAdaptorCreationException( self ) :

		def a() :

			raise RuntimeError( "Oops" )

		GafferScene.SceneAlgo.registerRenderAdaptor( "Test", a )

		with self.assertRaisesRegex( RuntimeError, "Oops" ) :
			GafferScene.SceneAlgo.createRenderAdaptors()

	def testAdaptorRegistrationFromAdaptorCreator( self ) :

		self.addCleanup( GafferScene.SceneAlgo.deregisterRenderAdaptor, "RegistrationCreator" )
		for i in range( 0, 100 ) :
			self.addCleanup( GafferScene.SceneAlgo.deregisterRenderAdaptor, f"RegisteredFromCreator{i}" )

		def creator() :

			for i in range( 0, 100 ) :
				GafferScene.SceneAlgo.registerRenderAdaptor( f"RegisteredFromCreator{i}", GafferScene.CustomAttributes )
			return GafferScene.CustomAttributes()

		GafferScene.SceneAlgo.registerRenderAdaptor( "RegistrationCreator", creator )
		adaptors = GafferScene.SceneAlgo.createRenderAdaptors()

		self.assertIn( "RegistrationCreator", adaptors )
		for i in range( 0, 100 ) :
			# We can't expect the registrations made from `creator()` to
			# have been accounted for.
			self.assertNotIn( f"RegisteredFromCreator{i}", adaptors )

	def testValidateName( self ) :

		for goodName in [ "obi", "lewis", "ludo" ] :
			with self.subTest( name = goodName ) :
				GafferScene.SceneAlgo.validateName( goodName )

		for badName in [ "..", "...", "", "a/b", "/", "a/", "/b", "*", "a*", "b*", "[", "b[a-z]", "\\", "\\a", "b\\", "a?", "?a" ] :
			with self.subTest( name = badName ) :
				with self.assertRaises( RuntimeError ) :
					GafferScene.SceneAlgo.validateName( badName )

	def testFindAll( self ) :

		plane = GafferScene.Plane()

		planeFilter = GafferScene.PathFilter()
		planeFilter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		sphere = GafferScene.Sphere()

		instancer = GafferScene.Instancer()
		instancer["in"].setInput( plane["out"] )
		instancer["prototypes"].setInput( sphere["out"] )
		instancer["filter"].setInput( planeFilter["out"] )

		self.assertEqual(
			GafferScene.SceneAlgo.findAll(
				instancer["out"],
				lambda scene, path : scene["transform"].getValue().translation().x > 0
			),
			IECore.PathMatcher( [
				"/plane/instances/sphere/1",
				"/plane/instances/sphere/3",
			] )
		)

		self.assertEqual(
			GafferScene.SceneAlgo.findAll(
				instancer["out"],
				lambda scene, path : scene["transform"].getValue().translation().x > 0,
				root = "/not/a/location"
			),
			IECore.PathMatcher()
		)

	def testFindAllWithAttribute( self ) :

		# /group
		#	/light1
		# /light2

		light1 = GafferSceneTest.TestLight()
		light1["name"].setValue( "light1" )

		group = GafferScene.Group()
		group["in"][0].setInput( light1["out"] )

		light2 = GafferSceneTest.TestLight()
		light2["name"].setValue( "light2" )

		parent = GafferScene.Parent()
		parent["in"].setInput( group["out"] )
		parent["children"][0].setInput( light2["out"] )
		parent["parent"].setValue( "/" )

		self.assertEqual(
			GafferScene.SceneAlgo.findAllWithAttribute( parent["out"], "light:mute" ),
			IECore.PathMatcher()
		)

		light1["mute"]["enabled"].setValue( True )
		light1["mute"]["value"].setValue( True )

		light2["mute"]["enabled"].setValue( True )
		light2["mute"]["value"].setValue( False )

		self.assertEqual(
			GafferScene.SceneAlgo.findAllWithAttribute( parent["out"], "light:mute" ),
			IECore.PathMatcher( [ "/group/light1", "/light2" ] )
		)

		self.assertEqual(
			GafferScene.SceneAlgo.findAllWithAttribute( parent["out"], "light:mute", value = IECore.BoolData( True ) ),
			IECore.PathMatcher( [ "/group/light1" ] )
		)

		self.assertEqual(
			GafferScene.SceneAlgo.findAllWithAttribute( parent["out"], "light:mute", value = IECore.BoolData( False ) ),
			IECore.PathMatcher( [ "/light2" ] )
		)

		self.assertEqual(
			GafferScene.SceneAlgo.findAllWithAttribute( parent["out"], "light:mute", root = "/group" ),
			IECore.PathMatcher( [ "/group/light1" ] )
		)

	def testParallelGatherLocations( self ) :

		plane = GafferScene.Plane()
		group = GafferScene.Group()
		group["in"][0].setInput( plane["out"] )

		groupFilter = GafferScene.PathFilter()
		groupFilter["paths"].setValue( IECore.StringVectorData( [ "/group" ] ) )

		duplicate = GafferScene.Duplicate()
		duplicate["in"].setInput( group["out"] )
		duplicate["filter"].setInput( groupFilter["out"] )
		duplicate["copies"].setValue( 100 )

		gathered = []
		GafferScene.SceneAlgo.parallelGatherLocations(

			duplicate["out"],

			lambda scene, path : path,
			lambda path : gathered.append( path )

		)

		# We expect to have visited all locations.

		expected = set(
			[ "/", "/group", "/group/plane" ] +
			[ f"/group{x}" for x in range( 1, 101 ) ] +
			[ f"/group{x}/plane" for x in range( 1, 101 ) ]
		)
		self.assertEqual( set( gathered ), expected )

		# And we expect to have visited parent locations
		# before child locations.

		indices = {
			value : index
			for index, value in enumerate( gathered )
		}

		self.assertEqual( gathered[0], "/" )
		self.assertGreater( indices["/group/plane"], indices["/group"] )

		for i in range( 1, 101 ) :
			self.assertGreater( indices[f"/group{i}/plane"], indices[f"/group{i}"] )

	def testParallelGatherExceptionHandling( self ) :

		plane = GafferScene.Plane()

		with self.assertRaisesRegex( ZeroDivisionError, "division by zero" ) :

			GafferScene.SceneAlgo.parallelGatherLocations(

				plane["out"],
				lambda scene, path : path,
				lambda x : 1/0

			)

	def testParallelGatherLocationExceptionHandling( self ) :

		plane = GafferScene.Plane()

		gathered = []
		with self.assertRaisesRegex( Exception, "ZeroDivisionError" ) :

			GafferScene.SceneAlgo.parallelGatherLocations(

				plane["out"],
				lambda scene, path : 1/0,
				lambda x : gathered.append( x )

			)

		self.assertEqual( gathered, [] )

	def tearDown( self ) :

		GafferSceneTest.SceneTestCase.tearDown( self )
		GafferScene.SceneAlgo.deregisterRenderAdaptor( "Test" )

if __name__ == "__main__":
	unittest.main()
