##########################################################################
#
#  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
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

import IECore
import IECoreScene

import Gaffer
import GafferScene
import GafferSceneTest

import GafferScene.RenderPassTypeAdaptor

class RenderPassTypeAdaptorTest( GafferSceneTest.SceneTestCase ) :

	@staticmethod
	def __typeAProcessor() :

		result = GafferScene.CustomOptions()
		result["options"].addChild( Gaffer.NameValuePlug( "typeA", True ) )
		return result

	@staticmethod
	def __typeBProcessor() :

		result = GafferScene.CustomOptions()
		result["options"].addChild( Gaffer.NameValuePlug( "typeB", True ) )
		return result

	def testTypeProcessorRegistration( self ) :

		self.assertNotIn( "Test", GafferScene.RenderPassTypeAdaptor.registeredTypeNames() )

		GafferScene.RenderPassTypeAdaptor.registerTypeProcessor( "Test", "Main", self.__typeAProcessor )
		self.addCleanup( GafferScene.RenderPassTypeAdaptor.deregisterTypeProcessor, "Test", "Main" )

		self.assertIn( "Test", GafferScene.RenderPassTypeAdaptor.registeredTypeNames() )
		self.assertIn( "Main", GafferScene.RenderPassTypeAdaptor.registeredTypeProcessors( "Test" ) )

		GafferScene.RenderPassTypeAdaptor.deregisterTypeProcessor( "Test", "Main" )

		self.assertNotIn( "Test", GafferScene.RenderPassTypeAdaptor.registeredTypeNames() )

	def testTypeProcessorScope( self ) :

		GafferScene.RenderPassTypeAdaptor.registerTypeProcessor( "TestA", "Test", self.__typeAProcessor )
		GafferScene.RenderPassTypeAdaptor.registerTypeProcessor( "TestB", "Test", self.__typeBProcessor )
		self.addCleanup( GafferScene.RenderPassTypeAdaptor.deregisterTypeProcessor, "TestA", "Test" )
		self.addCleanup( GafferScene.RenderPassTypeAdaptor.deregisterTypeProcessor, "TestB", "Test" )

		renderPassType = GafferScene.CustomOptions()
		renderPassType["options"].addChild( Gaffer.NameValuePlug( "renderPass:type", "" ) )

		typeAdaptor = GafferScene.RenderPassTypeAdaptor()
		typeAdaptor["in"].setInput( renderPassType["out"] )

		self.assertNotIn( "option:typeA", typeAdaptor["out"].globals() )
		self.assertNotIn( "option:typeB", typeAdaptor["out"].globals() )

		renderPassType["options"][0]["value"].setValue( "TestA" )
		self.assertIn( "option:typeA", typeAdaptor["out"].globals() )
		self.assertNotIn( "option:typeB", typeAdaptor["out"].globals() )

		renderPassType["options"][0]["value"].setValue( "TestB" )
		self.assertNotIn( "option:typeA", typeAdaptor["out"].globals() )
		self.assertIn( "option:typeB", typeAdaptor["out"].globals() )

		renderPassType["options"][0]["value"].setValue( "TestC" )
		self.assertNotIn( "option:typeA", typeAdaptor["out"].globals() )
		self.assertNotIn( "option:typeB", typeAdaptor["out"].globals() )

	def testChainedTypeProcessors( self ) :

		GafferScene.RenderPassTypeAdaptor.registerTypeProcessor( "Test", "TypeA", self.__typeAProcessor )
		GafferScene.RenderPassTypeAdaptor.registerTypeProcessor( "Test", "TypeB", self.__typeBProcessor )
		self.addCleanup( GafferScene.RenderPassTypeAdaptor.deregisterTypeProcessor, "Test", "TypeA" )
		self.addCleanup( GafferScene.RenderPassTypeAdaptor.deregisterTypeProcessor, "Test", "TypeB" )

		renderPassType = GafferScene.CustomOptions()
		renderPassType["options"].addChild( Gaffer.NameValuePlug( "renderPass:type", "" ) )

		typeAdaptor = GafferScene.RenderPassTypeAdaptor()
		typeAdaptor["in"].setInput( renderPassType["out"] )

		self.assertNotIn( "option:typeA", typeAdaptor["out"].globals() )
		self.assertNotIn( "option:typeB", typeAdaptor["out"].globals() )

		renderPassType["options"][0]["value"].setValue( "NotAType" )

		self.assertNotIn( "option:typeA", typeAdaptor["out"].globals() )
		self.assertNotIn( "option:typeB", typeAdaptor["out"].globals() )

		renderPassType["options"][0]["value"].setValue( "Test" )

		self.assertIn( "option:typeA", typeAdaptor["out"].globals() )
		self.assertIn( "option:typeB", typeAdaptor["out"].globals() )

		GafferScene.RenderPassTypeAdaptor.deregisterTypeProcessor( "Test", "TypeB" )

		typeAdaptor = GafferScene.RenderPassTypeAdaptor()
		typeAdaptor["in"].setInput( renderPassType["out"] )

		self.assertIn( "option:typeA", typeAdaptor["out"].globals() )
		self.assertNotIn( "option:typeB", typeAdaptor["out"].globals() )

	def testRegisterAutoTypeFunction( self ) :

		def f( name ) :

			return name.upper()

		GafferScene.RenderPassTypeAdaptor.registerAutoTypeFunction( f )
		self.assertEqual( GafferScene.RenderPassTypeAdaptor.autoTypeFunction()( "test_beauty" ), "TEST_BEAUTY" )

	def testAutoTypeFunction( self ) :

		GafferScene.RenderPassTypeAdaptor.registerTypeProcessor( "shadow", "Test", self.__typeAProcessor )
		GafferScene.RenderPassTypeAdaptor.registerTypeProcessor( "reflection", "Test", self.__typeBProcessor )
		self.addCleanup( GafferScene.RenderPassTypeAdaptor.deregisterTypeProcessor, "shadow", "Test" )
		self.addCleanup( GafferScene.RenderPassTypeAdaptor.deregisterTypeProcessor, "shadow", "Test" )

		def f( name ) :

			return name.split("_")[-1] if "_" in name else ""

		GafferScene.RenderPassTypeAdaptor.registerAutoTypeFunction( f )

		self.assertEqual( GafferScene.RenderPassTypeAdaptor.autoTypeFunction()( "test_shadow" ), "shadow" )

		renderPassTypeOption = GafferScene.CustomOptions()
		renderPassTypeOption["options"].addChild( Gaffer.NameValuePlug( "renderPass:type", "" ) )

		typeAdaptor = GafferScene.RenderPassTypeAdaptor()
		typeAdaptor["in"].setInput( renderPassTypeOption["out"] )

		for renderPassName, renderPassType, expected, notExpected in (
			( "test_shadow", "auto", "option:typeA", "option:typeB" ),
			( "test_reflection", "auto", "option:typeB", "option:typeA" )
		) :
			renderPassTypeOption["options"][0]["value"].setValue( renderPassType )
			with Gaffer.Context() as context :
				context["renderPass"] = renderPassName
				self.assertIn( expected, typeAdaptor["out"].globals() )
				self.assertNotIn( notExpected, typeAdaptor["out"].globals() )

	def testDeleteOutputsProcessor( self ) :

		for type in ( "shadow", "reflection", "reflectionAlpha" ) :

			outputs = GafferScene.Outputs()
			outputs.addOutput( "test", IECoreScene.Output( "fileName", "type", "data", {} ) )
			outputs.addOutput( "Batch/Beauty", IECoreScene.Output( "fileName", "type", "data", {} ) )
			outputs.addOutput( "Interactive/Arnold/Beauty", IECoreScene.Output( "fileName", "type", "data", {} ) )

			g = outputs["out"]["globals"].getValue()
			self.assertTrue( "output:test" in g )
			self.assertTrue( "output:Batch/Beauty" in g )
			self.assertTrue( "output:Interactive/Arnold/Beauty" in g )

			processor = GafferScene.RenderPassTypeAdaptor.createTypeProcessor( type, "deleteOutputs" )
			processor["in"].setInput( outputs["out"] )

			g = processor["out"]["globals"].getValue()
			self.assertFalse( "output:test" in g )
			self.assertTrue( "output:Batch/Beauty" in g )
			self.assertTrue( "output:Interactive/Arnold/Beauty" in g )

	def testShadowCatcherProcessor( self ) :

		# /group
		#    /groupA
		#        /cube      (A, CUBE)
		#        /sphere    (A, SPHERE)
		#    /groupB
		#        /cube      (B, CUBE)
		#        /sphere    (B, SPHERE)

		cubeA = GafferScene.Cube()
		cubeA["sets"].setValue( "A CUBE" )

		sphereA = GafferScene.Sphere()
		sphereA["sets"].setValue( "A SPHERE" )

		groupA = GafferScene.Group()
		groupA["name"].setValue( "groupA" )
		groupA["in"][0].setInput( cubeA["out"] )
		groupA["in"][1].setInput( sphereA["out"] )

		cubeB = GafferScene.Cube()
		cubeB["sets"].setValue( "B CUBE" )

		sphereB = GafferScene.Sphere()
		sphereB["sets"].setValue( "B SPHERE" )

		groupB = GafferScene.Group()
		groupB["name"].setValue( "groupB" )
		groupB["in"][0].setInput( cubeB["out"] )
		groupB["in"][1].setInput( sphereB["out"] )

		group = GafferScene.Group()
		group["in"][0].setInput( groupA["out"] )
		group["in"][1].setInput( groupB["out"] )

		originalShader = IECoreScene.ShaderNetwork(
			shaders = {
				"output" : IECoreScene.Shader( "UsdPreviewSurface", "surface", {} ),
			},
			output = "output",
		)

		customAttributes = GafferScene.CustomAttributes()
		customAttributes["in"].setInput( group["out"] )
		customAttributes["extraAttributes"].setValue(
			IECore.CompoundObject(
				{
					"ai:surface" : originalShader,
					"cycles:surface" : originalShader,
					"osl:surface" : originalShader,
				}
			)
		)

		customOptions = GafferScene.CustomOptions()
		customOptions["in"].setInput( customAttributes["out"] )
		customOptions["options"].addChild( Gaffer.NameValuePlug( "render:cameraInclusions", "", False, "cameraInclusions" ) )
		customOptions["options"].addChild( Gaffer.NameValuePlug( "render:cameraExclusions", "", True, "cameraExclusions" ) )

		processor = GafferScene.RenderPassTypeAdaptor.createTypeProcessor( "shadow", "catcher" )
		processor["in"].setInput( customOptions["out"] )

		def assertShadowCatcher( rendererName, shaderAttribute, visibilityAttribute, catcherPaths, casterPaths, catchers = None, casters = None ) :

			processor["renderer"].setValue( rendererName )

			if catchers is not None :
				customOptions["options"]["cameraInclusions"]["value"].setValue( catchers )
			customOptions["options"]["cameraInclusions"]["enabled"].setValue( catchers is not None )

			if casters is not None :
				customOptions["options"]["cameraExclusions"]["value"].setValue( casters )
			customOptions["options"]["cameraExclusions"]["enabled"].setValue( casters is not None )

			allPaths = {
				"/group/groupA/cube",
				"/group/groupA/sphere",
				"/group/groupB/cube",
				"/group/groupB/sphere"
			}

			renderer = GafferScene.Private.IECoreScenePreview.CapturingRenderer(
				GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
			)
			GafferScene.Private.RendererAlgo.outputObjects(
				processor["out"], GafferScene.Private.RendererAlgo.RenderOptions( processor["out"] ), GafferScene.Private.RendererAlgo.RenderSets( processor["out"] ), GafferScene.Private.RendererAlgo.LightLinks(),
				renderer
			)

			if catcherPaths != {} :
				self.assertTrue( catcherPaths.issubset( allPaths ) )

			if casterPaths != {} :
				self.assertTrue( casterPaths.issubset( allPaths ) )

			for path in allPaths :
				capturedObject = renderer.capturedObject( path )
				if path in catcherPaths :
					# Path is a catcher by presence of a "shadowCatcher" shader
					self.assertTrue( shaderAttribute in capturedObject.capturedAttributes().attributes() )
					self.assertIsNotNone( capturedObject.capturedAttributes().attributes()[shaderAttribute].getShader( "shadowCatcher" ) )
					# Cycles uses `cycles:is_shadow_catcher` to define shadow catchers
					if rendererName == "Cycles" :
						self.assertTrue( "cycles:is_shadow_catcher" in capturedObject.capturedAttributes().attributes() )
						self.assertTrue( capturedObject.capturedAttributes().attributes()["cycles:is_shadow_catcher"].value )
					# Catchers should also be invisible to shadow rays to avoid self-shadowing.
					self.assertTrue( visibilityAttribute in capturedObject.capturedAttributes().attributes() )
					self.assertFalse( capturedObject.capturedAttributes().attributes()[visibilityAttribute].value )
				else :
					# Non-catchers should have their original shader assigned
					self.assertTrue( shaderAttribute in capturedObject.capturedAttributes().attributes() )
					self.assertShaderNetworksEqual( originalShader, capturedObject.capturedAttributes().attributes()[shaderAttribute] )
					# `cycles:is_shadow_catcher` should not be true on non-shadow catching locations
					if rendererName == "Cycles" and "cycles:is_shadow_catcher" in capturedObject.capturedAttributes().attributes() :
						self.assertFalse( capturedObject.capturedAttributes().attributes()["cycles:is_shadow_catcher"].value )
					# Only casters should be visible to shadow rays
					if visibilityAttribute in capturedObject.capturedAttributes().attributes() :
						self.assertEqual( path in casterPaths, capturedObject.capturedAttributes().attributes()[visibilityAttribute].value )

		for renderer, shaderAttribute, visibilityAttribute in (
			( "Arnold", "ai:surface", "ai:visibility:shadow" ),
			( "Cycles", "cycles:surface", "cycles:visibility:shadow" ),
			( "3Delight", "osl:surface", "dl:visibility.shadow" ),
			( "3Delight Cloud", "osl:surface", "dl:visibility.shadow" )
		) :

			# Nothing is a shadow catcher or caster by default
			assertShadowCatcher(
				renderer, shaderAttribute, visibilityAttribute,
				{}, {}, catchers = "", casters = ""
			)

			# Test defining catchers and casters with direct paths
			assertShadowCatcher(
				renderer, shaderAttribute, visibilityAttribute,
				{ "/group/groupA/cube" }, {}, catchers = "/group/groupA/cube"
			)

			assertShadowCatcher(
				renderer, shaderAttribute, visibilityAttribute,
				{}, { "/group/groupA/cube" }, casters = "/group/groupA/cube"
			)

			# Assigning a group should result in its descendants being treated as catchers
			assertShadowCatcher(
				renderer, shaderAttribute, visibilityAttribute,
				{ "/group/groupA/cube", "/group/groupA/sphere" }, {}, catchers = "/group/groupA"
			)

			# Non-matching siblings shouldn't be affected
			assertShadowCatcher(
				renderer, shaderAttribute, visibilityAttribute,
				{ "/group/groupA/cube", "/group/groupB/cube" }, {}, catchers = "CUBE"
			)

			# Catchers are overridden by casters
			assertShadowCatcher(
				renderer, shaderAttribute, visibilityAttribute,
				{}, { "/group/groupA/cube", "/group/groupA/sphere" }, catchers = "/group/groupA", casters = "/group/groupA"
			)

			# Descendants of catchers can be overridden as a shadow caster
			assertShadowCatcher(
				renderer, shaderAttribute, visibilityAttribute,
				{ "/group/groupA/cube" }, { "/group/groupA/sphere" }, catchers = "/group/groupA", casters = "/group/groupA/sphere"
			)

			# Descendants of casters can be overridden as a shadow catcher
			assertShadowCatcher(
				renderer, shaderAttribute, visibilityAttribute,
				{
					"/group/groupA/cube",
					"/group/groupA/sphere",
				},
				{
					"/group/groupB/cube",
					"/group/groupB/sphere"
				},
				catchers = "/group/groupA", casters = "/"
			)

			assertShadowCatcher(
				renderer, shaderAttribute, visibilityAttribute,
				{
					"/group/groupA/sphere",
					"/group/groupB/sphere"
				},
				{
					"/group/groupA/cube",
				},
				catchers = "SPHERE", casters = "/group/groupA"
			)

	def testReflectionCatcherProcessor( self ) :

		# /group
		#    /groupA
		#        /cube      (A, CUBE)
		#        /sphere    (A, SPHERE)
		#    /groupB
		#        /cube      (B, CUBE)
		#        /sphere    (B, SPHERE)

		cubeA = GafferScene.Cube()
		cubeA["sets"].setValue( "A CUBE" )

		sphereA = GafferScene.Sphere()
		sphereA["sets"].setValue( "A SPHERE" )

		groupA = GafferScene.Group()
		groupA["name"].setValue( "groupA" )
		groupA["in"][0].setInput( cubeA["out"] )
		groupA["in"][1].setInput( sphereA["out"] )

		cubeB = GafferScene.Cube()
		cubeB["sets"].setValue( "B CUBE" )

		sphereB = GafferScene.Sphere()
		sphereB["sets"].setValue( "B SPHERE" )

		groupB = GafferScene.Group()
		groupB["name"].setValue( "groupB" )
		groupB["in"][0].setInput( cubeB["out"] )
		groupB["in"][1].setInput( sphereB["out"] )

		group = GafferScene.Group()
		group["in"][0].setInput( groupA["out"] )
		group["in"][1].setInput( groupB["out"] )

		originalShader = IECoreScene.ShaderNetwork(
			shaders = {
				"originalShader" : IECoreScene.Shader( "UsdPreviewSurface", "surface", {} ),
			},
			output = "originalShader",
		)

		customAttributes = GafferScene.CustomAttributes()
		customAttributes["in"].setInput( group["out"] )
		customAttributes["extraAttributes"].setValue(
			IECore.CompoundObject(
				{
					"ai:surface" : originalShader,
					"cycles:surface" : originalShader,
					"osl:surface" : originalShader,
					"linkedLights" : IECore.StringData( "/light1" ),
				}
			)
		)

		customOptions = GafferScene.CustomOptions()
		customOptions["in"].setInput( customAttributes["out"] )
		customOptions["options"].addChild( Gaffer.NameValuePlug( "render:cameraInclusions", "", False, "cameraInclusions" ) )
		customOptions["options"].addChild( Gaffer.NameValuePlug( "render:cameraExclusions", "", True, "cameraExclusions" ) )

		processor = GafferScene.RenderPassTypeAdaptor.createTypeProcessor( "reflection", "catcher" )
		processor["in"].setInput( customOptions["out"] )

		def assertReflectionCatcher( renderer, shaderAttribute, visibilityAttribute, catcherPaths, casterPaths, catchers = None, casters = None ) :

			processor["renderer"].setValue( renderer )

			if catchers is not None :
				customOptions["options"]["cameraInclusions"]["value"].setValue( catchers )
			customOptions["options"]["cameraInclusions"]["enabled"].setValue( catchers is not None )

			if casters is not None :
				customOptions["options"]["cameraExclusions"]["value"].setValue( casters )
			customOptions["options"]["cameraExclusions"]["enabled"].setValue( casters is not None )

			allPaths = {
				"/group/groupA/cube",
				"/group/groupA/sphere",
				"/group/groupB/cube",
				"/group/groupB/sphere"
			}

			renderer = GafferScene.Private.IECoreScenePreview.CapturingRenderer(
				GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
			)
			GafferScene.Private.RendererAlgo.outputObjects(
				processor["out"], GafferScene.Private.RendererAlgo.RenderOptions( processor["out"] ), GafferScene.Private.RendererAlgo.RenderSets( processor["out"] ), GafferScene.Private.RendererAlgo.LightLinks(),
				renderer
			)

			if catcherPaths != {} :
				self.assertTrue( catcherPaths.issubset( allPaths ) )

			if casterPaths != {} :
				self.assertTrue( casterPaths.issubset( allPaths ) )

			for path in allPaths :
				capturedObject = renderer.capturedObject( path )
				if path in catcherPaths :
					# Catchers should have an overridden "reflectionCatcher" shader
					self.assertTrue( shaderAttribute in capturedObject.capturedAttributes().attributes() )
					self.assertIsNotNone( capturedObject.capturedAttributes().attributes()[shaderAttribute].getShader( "reflectionCatcher" ) )
					# Should be unlinked from all lights
					self.assertTrue( "linkedLights" in capturedObject.capturedAttributes().attributes() )
					self.assertEqual( "", capturedObject.capturedAttributes().attributes()["linkedLights"].value )
					# And should also be invisible to reflection rays
					self.assertTrue( visibilityAttribute in capturedObject.capturedAttributes().attributes() )
					self.assertFalse( capturedObject.capturedAttributes().attributes()[visibilityAttribute].value )
				else :
					# Non-catchers should have their original shader assigned
					self.assertTrue( shaderAttribute in capturedObject.capturedAttributes().attributes() )
					self.assertShaderNetworksEqual( originalShader, capturedObject.capturedAttributes().attributes()[shaderAttribute] )
					# Not have their linkedLights modified
					self.assertTrue( "linkedLights" in capturedObject.capturedAttributes().attributes() )
					self.assertEqual( "/light1", capturedObject.capturedAttributes().attributes()["linkedLights"].value )
					# And only casters should be visible to reflection rays
					if visibilityAttribute in capturedObject.capturedAttributes().attributes() :
						self.assertEqual( path in casterPaths, capturedObject.capturedAttributes().attributes()[visibilityAttribute].value )

		for renderer, shaderAttribute, visibilityAttribute in (
			( "Arnold", "ai:surface", "ai:visibility:specular_reflect" ),
			( "Cycles", "cycles:surface", "cycles:visibility:glossy" ),
			( "3Delight", "osl:surface", "dl:visibility.reflection" ),
			( "3Delight Cloud", "osl:surface", "dl:visibility.reflection" )
		) :

			# Nothing is a reflection catcher or caster by default
			assertReflectionCatcher(
				renderer, shaderAttribute, visibilityAttribute,
				{}, {}, catchers = "", casters = ""
			)

			# Test defining catchers and casters with direct paths
			assertReflectionCatcher(
				renderer, shaderAttribute, visibilityAttribute,
				{ "/group/groupA/cube" }, {}, catchers = "/group/groupA/cube"
			)

			assertReflectionCatcher(
				renderer, shaderAttribute, visibilityAttribute,
				{}, { "/group/groupA/cube" }, casters = "/group/groupA/cube"
			)

			# Assigning a group should result in its descendants being treated as catchers
			assertReflectionCatcher(
				renderer, shaderAttribute, visibilityAttribute,
				{ "/group/groupA/cube", "/group/groupA/sphere" }, {}, catchers = "/group/groupA"
			)

			# Non-matching siblings shouldn't be affected
			assertReflectionCatcher(
				renderer, shaderAttribute, visibilityAttribute,
				{ "/group/groupA/cube", "/group/groupB/cube" }, {}, catchers = "CUBE"
			)

			# Catchers are overridden by casters
			assertReflectionCatcher(
				renderer, shaderAttribute, visibilityAttribute,
				{}, { "/group/groupA/cube", "/group/groupA/sphere" },
				catchers = "/group/groupA", casters = "/group/groupA"
			)

			# Descendants of catchers can be overridden as a reflection caster
			assertReflectionCatcher(
				renderer, shaderAttribute, visibilityAttribute,
				{ "/group/groupA/cube" }, { "/group/groupA/sphere" },
				catchers = "/group/groupA", casters = "/group/groupA/sphere"
			)

			# Descendants of casters can be overridden as a reflection catcher
			assertReflectionCatcher(
				renderer, shaderAttribute, visibilityAttribute,
				{
					"/group/groupA/cube",
					"/group/groupA/sphere",
				},
				{
					"/group/groupB/cube",
					"/group/groupB/sphere"
				},
				catchers = "/group/groupA", casters = "/"
			)

			assertReflectionCatcher(
				renderer, shaderAttribute, visibilityAttribute,
				{
					"/group/groupA/sphere",
					"/group/groupB/sphere"
				},
				{
					"/group/groupA/cube",
				},
				catchers = "SPHERE", casters = "/group/groupA"
			)

	def testReflectionAlphaCasterProcessorPrunesLights( self ) :

		cubeA = GafferScene.Cube()
		cubeA["sets"].setValue( "A CUBE" )

		lightA = GafferSceneTest.TestLight()
		lightA["sets"].setValue( "A" )

		groupA = GafferScene.Group()
		groupA["name"].setValue( "groupA" )
		groupA["in"][0].setInput( cubeA["out"] )
		groupA["in"][1].setInput( lightA["out"] )

		sphereB = GafferScene.Sphere()
		sphereB["sets"].setValue( "B SPHERE" )

		lightB = GafferSceneTest.TestLight()
		lightB["sets"].setValue( "B" )

		groupB = GafferScene.Group()
		groupB["name"].setValue( "groupB" )
		groupB["in"][0].setInput( sphereB["out"] )
		groupB["in"][1].setInput( lightB["out"] )

		group = GafferScene.Group()
		group["in"][0].setInput( groupA["out"] )
		group["in"][1].setInput( groupB["out"] )

		processor = GafferScene.RenderPassTypeAdaptor.createTypeProcessor( "reflectionAlpha", "caster" )
		processor["in"].setInput( group["out"] )

		# Lights are not necessary, as the reflectionAlpha caster locations are emissive so the
		# processor prunes them from the scene.
		self.assertTrue( GafferScene.SceneAlgo.exists( processor["in"], "/group/groupA/light" ) )
		self.assertTrue( GafferScene.SceneAlgo.exists( processor["in"], "/group/groupB/light" ) )
		self.assertFalse( GafferScene.SceneAlgo.exists( processor["out"], "/group/groupA/light" ) )
		self.assertFalse( GafferScene.SceneAlgo.exists( processor["out"], "/group/groupB/light" ) )

	def testReflectionAlphaCasterProcessor( self ) :

		# /group
		#    /groupA
		#        /cube      (A, CUBE)
		#        /sphere    (A, SPHERE)
		#        /light     (A)
		#    /groupB
		#        /cube      (B, CUBE)
		#        /sphere    (B, SPHERE)
		#        /light     (B)

		cubeA = GafferScene.Cube()
		cubeA["sets"].setValue( "A CUBE" )

		sphereA = GafferScene.Sphere()
		sphereA["sets"].setValue( "A SPHERE" )

		lightA = GafferSceneTest.TestLight()
		lightA["sets"].setValue( "A" )

		groupA = GafferScene.Group()
		groupA["name"].setValue( "groupA" )
		groupA["in"][0].setInput( cubeA["out"] )
		groupA["in"][1].setInput( sphereA["out"] )
		groupA["in"][2].setInput( lightA["out"] )

		cubeB = GafferScene.Cube()
		cubeB["sets"].setValue( "B CUBE" )

		sphereB = GafferScene.Sphere()
		sphereB["sets"].setValue( "B SPHERE" )

		lightB = GafferSceneTest.TestLight()
		lightB["sets"].setValue( "B" )

		groupB = GafferScene.Group()
		groupB["name"].setValue( "groupB" )
		groupB["in"][0].setInput( cubeB["out"] )
		groupB["in"][1].setInput( sphereB["out"] )
		groupB["in"][2].setInput( lightB["out"] )

		group = GafferScene.Group()
		group["in"][0].setInput( groupA["out"] )
		group["in"][1].setInput( groupB["out"] )

		originalShader = IECoreScene.ShaderNetwork(
			shaders = {
				"originalShader" : IECoreScene.Shader( "UsdPreviewSurface", "surface", {} ),
			},
			output = "originalShader",
		)

		customAttributes = GafferScene.CustomAttributes()
		customAttributes["in"].setInput( group["out"] )
		customAttributes["extraAttributes"].setValue(
			IECore.CompoundObject(
				{
					"ai:surface" : originalShader,
					"cycles:surface" : originalShader,
					"osl:surface" : originalShader,
				}
			)
		)

		customOptions = GafferScene.CustomOptions()
		customOptions["in"].setInput( customAttributes["out"] )
		customOptions["options"].addChild( Gaffer.NameValuePlug( "render:cameraExclusions", "", True, "cameraExclusions" ) )

		processor = GafferScene.RenderPassTypeAdaptor.createTypeProcessor( "reflectionAlpha", "caster" )
		processor["in"].setInput( customOptions["out"] )

		def assertReflectionCaster( renderer, shaderAttribute, casterPaths, casters = None ) :

			processor["renderer"].setValue( renderer )

			if casters is not None :
				customOptions["options"]["cameraExclusions"]["value"].setValue( casters )
			customOptions["options"]["cameraExclusions"]["enabled"].setValue( casters is not None )

			allPaths = {
				"/group/groupA/cube",
				"/group/groupA/sphere",
				"/group/groupB/cube",
				"/group/groupB/sphere"
			}

			renderer = GafferScene.Private.IECoreScenePreview.CapturingRenderer(
				GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
			)
			GafferScene.Private.RendererAlgo.outputObjects(
				processor["out"], GafferScene.Private.RendererAlgo.RenderOptions( processor["out"] ), GafferScene.Private.RendererAlgo.RenderSets( processor["out"] ), GafferScene.Private.RendererAlgo.LightLinks(),
				renderer
			)

			if casterPaths != {} :
				self.assertTrue( casterPaths.issubset( allPaths ) )

			for path in allPaths :
				capturedObject = renderer.capturedObject( path )
				if path in casterPaths :
					# Path is a caster by presence of a "reflectionCaster" shader
					self.assertTrue( shaderAttribute in capturedObject.capturedAttributes().attributes() )
					self.assertIsNotNone( capturedObject.capturedAttributes().attributes()[shaderAttribute].getShader( "reflectionCaster" ) )
				else :
					# Non-casters should keep their original shader
					self.assertTrue( shaderAttribute in capturedObject.capturedAttributes().attributes() )
					self.assertShaderNetworksEqual( originalShader, capturedObject.capturedAttributes().attributes()[shaderAttribute] )

		for renderer, shaderAttribute in (
			( "Arnold", "ai:surface" ),
			( "Cycles", "cycles:surface" ),
			( "3Delight", "osl:surface" ),
			( "3Delight Cloud", "osl:surface" ),
		) :

			# Nothing is a reflection caster by default
			assertReflectionCaster( renderer, shaderAttribute, {}, casters = "" )

			# Reflection casters
			assertReflectionCaster( renderer, shaderAttribute, { "/group/groupA/cube" }, casters = "/group/groupA/cube" )
			assertReflectionCaster( renderer, shaderAttribute, { "/group/groupA/cube", "/group/groupA/sphere" }, casters = "/group/groupA" )
			assertReflectionCaster( renderer, shaderAttribute, { "/group/groupA/cube", "/group/groupB/cube" }, casters = "CUBE" )

if __name__ == "__main__":
	unittest.main()
