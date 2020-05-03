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
import os
import unittest
import six

import IECore

import Gaffer
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
		with six.assertRaisesRegex( self, RuntimeError, "is not a child of a ScenePlug" ) :
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
		copyAttributes["in"][0].setInput( tweaks1["out"] )
		copyAttributes["in"][1].setInput( tweaks2["out"] )

		# No filter

		self.assertEqual(
			GafferScene.shaderTweaks( copyAttributes["out"], "/plane", "test:surface" ),
			tweaks1
		)

		# Filter, but nothing being copied

		copyAttributes["filter"].setInput( planeFilter["out"] )
		copyAttributes["attributes"].setValue( "" )
		self.assertEqual(
			GafferScene.shaderTweaks( copyAttributes["out"], "/plane", "test:surface" ),
			tweaks1
		)

		# Attribute actually being copied

		copyAttributes["attributes"].setValue( "test:surface" )
		self.assertEqual(
			GafferScene.shaderTweaks( copyAttributes["out"], "/plane", "test:surface" ),
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

		pathWithoutMeta = os.path.join( self.temporaryDirectory(), "sceneAlgoSourceSceneWithoutMeta.exr" )
		o["fileName"].setValue( pathWithoutMeta )
		o.execute()

		pathWithMeta = os.path.join( self.temporaryDirectory(), "sceneAlgoSourceSceneWithMeta.exr" )
		m["metadata"].addChild( Gaffer.NameValuePlug( "gaffer:sourceScene", IECore.StringData( expectedPath ), True, "sourceScene" ) )
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

		attributeHistory = GafferScene.attributeHistory( history, "test" )

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
			attributeHistory = GafferScene.attributeHistory( history, "test" )

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
			attributeHistory = GafferScene.attributeHistory( history, destination )

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
			attributeHistory = GafferScene.attributeHistory( history, attributeName )

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
		attributeHistory = GafferScene.attributeHistory( history, "a" )

		self.__assertAttributeHistory( attributeHistory, [], outerAttributes["out"], "/outer/inner/plane", "a", IECore.StringData( "planeA" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0 ], outerAttributes["in"], "/outer/inner/plane", "a", IECore.StringData( "planeA" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0 ], innerAttributes["out"], "/outer/inner/plane", "a", IECore.StringData( "planeA" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0 ], innerAttributes["in"], "/outer/inner/plane", "a", IECore.StringData( "planeA" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0, 0 ], outerGroup["out"], "/outer/inner/plane", "a", IECore.StringData( "planeA" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0, 0, 0 ], outerGroup["in"][0], "/inner/plane", "a", IECore.StringData( "planeA" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0, 0, 0, 0 ], innerGroup["out"], "/inner/plane", "a", IECore.StringData( "planeA" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0, 0, 0, 0, 0 ], innerGroup["in"][0], "/plane", "a", IECore.StringData( "planeA" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0, 0, 0, 0, 0, 0 ], planeAttributes["out"], "/plane", "a", IECore.StringData( "planeA" ), 0 )

		self.assertIsNone( GafferScene.attributeHistory( history, "b" ) )
		self.assertIsNone( GafferScene.attributeHistory( history, "c" ) )

		# Add localisation

		localiseFilter = GafferScene.PathFilter()
		localiseFilter["paths"].setValue( IECore.StringVectorData( [ "/outer/inner/plane" ] ) )

		localise = GafferScene.LocaliseAttributes()
		localise["in"].setInput( outerAttributes["out"] )
		localise["filter"].setInput( localiseFilter["out"] )
		localise["attributes"].setValue( "*" )

		# Test attribute "a"

		history = GafferScene.SceneAlgo.history( localise["out"]["attributes"], "/outer/inner/plane" )
		attributeHistory = GafferScene.attributeHistory( history, "a" )

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

		attributeHistory = GafferScene.attributeHistory( history, "b" )

		self.__assertAttributeHistory( attributeHistory, [], localise["out"], "/outer/inner/plane", "b", IECore.StringData( "innerB" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0 ], localise["in"], "/outer/inner", "b", IECore.StringData( "innerB" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0 ], outerAttributes["out"], "/outer/inner", "b", IECore.StringData( "innerB" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0 ], outerAttributes["in"], "/outer/inner", "b", IECore.StringData( "innerB" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0, 0 ], innerAttributes["out"], "/outer/inner", "b", IECore.StringData( "innerB" ), 0 )

		# Test attribute "c"

		attributeHistory = GafferScene.attributeHistory( history, "c" )

		self.__assertAttributeHistory( attributeHistory, [], localise["out"], "/outer/inner/plane", "c", IECore.StringData( "outerC" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0 ], localise["in"], "/outer", "c", IECore.StringData( "outerC" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0 ], outerAttributes["out"], "/outer", "c", IECore.StringData( "outerC" ), 0 )

		# Test location not touched by LocaliseAttributes

		history = GafferScene.SceneAlgo.history( localise["out"]["attributes"], "/outer/inner" )

		attributeHistory = GafferScene.attributeHistory( history, "a" )
		self.__assertAttributeHistory( attributeHistory, [], localise["out"], "/outer/inner", "a", IECore.StringData( "innerA" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0 ], localise["in"], "/outer/inner", "a", IECore.StringData( "innerA" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0 ], outerAttributes["out"], "/outer/inner", "a", IECore.StringData( "innerA" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0 ], outerAttributes["in"], "/outer/inner", "a", IECore.StringData( "innerA" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0, 0 ], innerAttributes["out"], "/outer/inner", "a", IECore.StringData( "innerA" ), 0 )

		attributeHistory = GafferScene.attributeHistory( history, "b" )
		self.__assertAttributeHistory( attributeHistory, [], localise["out"], "/outer/inner", "b", IECore.StringData( "innerB" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0 ], localise["in"], "/outer/inner", "b", IECore.StringData( "innerB" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0 ], outerAttributes["out"], "/outer/inner", "b", IECore.StringData( "innerB" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0 ], outerAttributes["in"], "/outer/inner", "b", IECore.StringData( "innerB" ), 1 )
		self.__assertAttributeHistory( attributeHistory, [ 0, 0, 0, 0 ], innerAttributes["out"], "/outer/inner", "b", IECore.StringData( "innerB" ), 0 )

		self.assertIsNone( GafferScene.attributeHistory( history, "c" ) )

	def testAttributeHistoryWithMissingAttribute( self ) :

		# Attribute doesn't exist, so we return None.

		plane = GafferScene.Plane()
		attributesHistory = GafferScene.SceneAlgo.history( plane["out"]["attributes"], "/plane" )
		self.assertIsNone( GafferScene.SceneAlgo.attributeHistory( attributesHistory, "test" ) )

if __name__ == "__main__":
	unittest.main()
