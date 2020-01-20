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

import unittest
import imath

import IECore

import Gaffer
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
			history = history.predecessors[0] if history.predecessors else None

		self.assertIsNone( history )

		# Attributes history

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
			history = history.predecessors[0] if history.predecessors else None

		self.assertIsNone( history )

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
		with self.assertRaisesRegexp( RuntimeError, "is not a child of a ScenePlug" ) :
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

if __name__ == "__main__":
	unittest.main()
