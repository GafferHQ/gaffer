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

import unittest

import Gaffer
import GafferScene
import GafferSceneTest

class RenderAdaptorTest( GafferSceneTest.SceneTestCase ) :

	def testRenderSetAdaptor( self ) :

		# /group
		#    /groupA
		#        /cube      (A, CUBE)
		#        /sphere    (A, SPHERE)
		#    /groupB
		#        /cube      (B, CUBE)
		#        /sphere    (B, SPHERE)
		#    /groupC
		#        /cube      (C, CUBE)
		#        /light     (C)
		#        /lightFilter    (C)

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

		cubeC = GafferScene.Cube()
		cubeC["sets"].setValue( "C CUBE" )

		lightC = GafferSceneTest.TestLight()
		lightC["sets"].setValue( "C" )

		lightFilterC = GafferSceneTest.TestLightFilter()
		lightFilterC["sets"].setValue( "C" )

		groupC = GafferScene.Group()
		groupC["name"].setValue( "groupC" )
		groupC["in"][0].setInput( cubeC["out"] )
		groupC["in"][1].setInput( lightC["out"] )
		groupC["in"][2].setInput( lightFilterC["out"] )

		group = GafferScene.Group()
		group["in"][0].setInput( groupA["out"] )
		group["in"][1].setInput( groupB["out"] )
		group["in"][2].setInput( groupC["out"] )

		standardOptions = GafferScene.StandardOptions()
		standardOptions["in"].setInput( group["out"] )

		testAdaptors = GafferScene.SceneAlgo.createRenderAdaptors()
		testAdaptors["in"].setInput( standardOptions["out"] )

		def assertIncludedObjects( scene, paths, inclusions = None, exclusions = None, additionalLights = None ) :

			if inclusions is not None :
				standardOptions["options"]["inclusions"]["value"].setValue( inclusions )
			standardOptions["options"]["inclusions"]["enabled"].setValue( inclusions is not None )

			if exclusions is not None :
				standardOptions["options"]["exclusions"]["value"].setValue( exclusions )
			standardOptions["options"]["exclusions"]["enabled"].setValue( exclusions is not None )

			if additionalLights is not None :
				standardOptions["options"]["additionalLights"]["value"].setValue( additionalLights )
			standardOptions["options"]["additionalLights"]["enabled"].setValue( additionalLights is not None )

			allPaths = {
				"/group/groupA/cube",
				"/group/groupA/sphere",
				"/group/groupB/cube",
				"/group/groupB/sphere",
				"/group/groupC/cube",
				"/group/groupC/light",
				"/group/groupC/lightFilter",
			}

			if paths != {} :
				self.assertTrue( paths.issubset( allPaths ) )

			for path in allPaths :
				if path in paths :
					self.assertTrue( GafferScene.SceneAlgo.exists( scene, path ) )
				else :
					self.assertFalse( GafferScene.SceneAlgo.exists( scene, path ) )

		# If inclusions aren't specified, then we should get everything.

		assertIncludedObjects(
			testAdaptors["out"],
			{
				"/group/groupA/cube",
				"/group/groupA/sphere",
				"/group/groupB/cube",
				"/group/groupB/sphere",
				"/group/groupC/cube",
				"/group/groupC/light",
				"/group/groupC/lightFilter",
			},
			inclusions = None
		)

		# If we specify the root of the scene, then we should also get everything.

		assertIncludedObjects(
			testAdaptors["out"],
			{
				"/group/groupA/cube",
				"/group/groupA/sphere",
				"/group/groupB/cube",
				"/group/groupB/sphere",
				"/group/groupC/cube",
				"/group/groupC/light",
				"/group/groupC/lightFilter",
			},
			inclusions = "/"
		)

		# If we include "", then we should get nothing.

		assertIncludedObjects(
			testAdaptors["out"],
			{},
			inclusions = ""
		)

		# Test a variety of inclusions set expressions.

		assertIncludedObjects(
			testAdaptors["out"],
			{
				"/group/groupA/sphere",
				"/group/groupB/sphere",
			},
			inclusions = "SPHERE"
		)

		assertIncludedObjects(
			testAdaptors["out"],
			{
				"/group/groupA/cube",
				"/group/groupB/cube",
				"/group/groupC/cube",
			},
			inclusions = "CUBE"
		)

		assertIncludedObjects(
			testAdaptors["out"],
			{
				"/group/groupA/cube",
				"/group/groupA/sphere",
			},
			inclusions = "A"
		)

		assertIncludedObjects(
			testAdaptors["out"],
			{
				"/group/groupA/cube",
				"/group/groupA/sphere",
				"/group/groupB/sphere",
			},
			inclusions = "A | SPHERE"
		)

		assertIncludedObjects(
			testAdaptors["out"],
			{
				"/group/groupA/sphere",
			},
			inclusions = "A & SPHERE"
		)

		assertIncludedObjects(
			testAdaptors["out"],
			{
				"/group/groupA/sphere",
				"/group/groupB/sphere",
				"/group/groupB/cube",
			},
			inclusions = "SPHERE | /group/groupB"
		)

		assertIncludedObjects(
			testAdaptors["out"],
			{
				"/group/groupB/cube",
				"/group/groupB/sphere",
			},
			inclusions = "B"
		)

		assertIncludedObjects(
			testAdaptors["out"],
			{
				"/group/groupB/cube",
			},
			inclusions = "B - SPHERE"
		)

		# Lights matched by the set expression are included as usual.

		assertIncludedObjects(
			testAdaptors["out"],
			{
				"/group/groupC/cube",
				"/group/groupC/light",
				"/group/groupC/lightFilter",
			},
			inclusions = "C"
		)

		# Exclusions will override inclusions.

		assertIncludedObjects(
			testAdaptors["out"],
			{
				"/group/groupA/cube",
				"/group/groupB/cube",
				"/group/groupC/cube",
				"/group/groupC/light",
				"/group/groupC/lightFilter",
			},
			inclusions = "/",
			exclusions = "SPHERE"
		)

		assertIncludedObjects(
			testAdaptors["out"],
			{
				"/group/groupA/sphere",
				"/group/groupB/sphere",
				"/group/groupC/light",
				"/group/groupC/lightFilter",
			},
			inclusions = "/",
			exclusions = "CUBE"
		)

		assertIncludedObjects(
			testAdaptors["out"],
			{
				"/group/groupC/light",
				"/group/groupC/lightFilter",
			},
			inclusions = "/",
			exclusions = "SPHERE | CUBE"
		)

		# Excluding the root of the scene gives us nothing.

		assertIncludedObjects(
			testAdaptors["out"],
			{},
			inclusions = "/",
			exclusions = "/"
		)

		# Excluding "" still gives us the full set of inclusions.

		assertIncludedObjects(
			testAdaptors["out"],
			{
				"/group/groupA/cube",
				"/group/groupA/sphere",
				"/group/groupB/cube",
				"/group/groupB/sphere",
				"/group/groupC/cube",
				"/group/groupC/light",
				"/group/groupC/lightFilter",
			},
			inclusions = "/",
			exclusions = ""
		)

		# AdditionalLights combine with inclusions but only
		# include lights matched by the set expression.

		assertIncludedObjects(
			testAdaptors["out"],
			{
				"/group/groupA/sphere",
				"/group/groupB/sphere",
				"/group/groupC/light",
				"/group/groupC/lightFilter",
			},
			inclusions = "SPHERE",
			additionalLights = "C"
		)

		assertIncludedObjects(
			testAdaptors["out"],
			{
				"/group/groupA/sphere",
				"/group/groupB/sphere",
				"/group/groupC/light",
				"/group/groupC/lightFilter",
			},
			inclusions = "SPHERE",
			additionalLights = "/"
		)

		assertIncludedObjects(
			testAdaptors["out"],
			{
				"/group/groupC/light",
				"/group/groupC/lightFilter",
			},
			inclusions = "",
			additionalLights = "C"
		)

		assertIncludedObjects(
			testAdaptors["out"],
			{
				"/group/groupA/sphere",
				"/group/groupB/sphere",
			},
			inclusions = "SPHERE",
			additionalLights = ""
		)

		# Exclusions override additionalLights.

		assertIncludedObjects(
			testAdaptors["out"],
			{
				"/group/groupA/sphere",
				"/group/groupB/sphere",
			},
			inclusions = "SPHERE",
			additionalLights = "C",
			exclusions = "C"
		)

		# And win over both inclusions and additionalLights.

		assertIncludedObjects(
			testAdaptors["out"],
			{
				"/group/groupB/sphere",
				"/group/groupC/lightFilter",
			},
			inclusions = "SPHERE",
			additionalLights = "C",
			exclusions = "__lights | /group/groupA"
		)

		# Though we can still save a light from the grasp of exclusion...

		assertIncludedObjects(
			testAdaptors["out"],
			{
				"/group/groupB/sphere",
				"/group/groupC/light",
				"/group/groupC/lightFilter",
			},
			inclusions = "SPHERE",
			additionalLights = "C",
			exclusions = "( __lights - C ) | /group/groupA"
		)

	def testCameraVisibilityAdaptor( self ) :

		#  /groupA
		#    /cube      (A, CUBE)
		#    /sphere    (A, SPHERE)

		cubeA = GafferScene.Cube()
		cubeA["sets"].setValue( "A CUBE" )

		sphereA = GafferScene.Sphere()
		sphereA["sets"].setValue( "A SPHERE" )

		groupA = GafferScene.Group()
		groupA["name"].setValue( "groupA" )
		groupA["in"][0].setInput( cubeA["out"] )
		groupA["in"][1].setInput( sphereA["out"] )

		customOptions = GafferScene.CustomOptions()
		customOptions["in"].setInput( groupA["out"] )
		customOptions["options"].addChild( Gaffer.NameValuePlug( "render:cameraInclusions", "", False, "cameraInclusions" ) )
		customOptions["options"].addChild( Gaffer.NameValuePlug( "render:cameraExclusions", "", True, "cameraExclusions" ) )

		inclusionAttributesFilter = GafferScene.SetFilter()
		inclusionAttributes = GafferScene.CustomAttributes()
		inclusionAttributes["in"].setInput( customOptions["out"] )
		inclusionAttributes["filter"].setInput( inclusionAttributesFilter["out"] )
		inclusionAttributes["attributes"].addChild( Gaffer.NameValuePlug( "ai:visibility:camera", True, True ) )
		inclusionAttributes["attributes"].addChild( Gaffer.NameValuePlug( "cycles:visibility:camera", True, True ) )
		inclusionAttributes["attributes"].addChild( Gaffer.NameValuePlug( "dl:visibility.camera", True, True ) )
		inclusionAttributes["attributes"].addChild( Gaffer.NameValuePlug( "ri:visibility:camera", True, True ) )

		exclusionAttributesFilter = GafferScene.SetFilter()
		exclusionAttributes = GafferScene.CustomAttributes()
		exclusionAttributes["in"].setInput( inclusionAttributes["out"] )
		exclusionAttributes["filter"].setInput( exclusionAttributesFilter["out"] )
		exclusionAttributes["attributes"].addChild( Gaffer.NameValuePlug( "ai:visibility:camera", False, True ) )
		exclusionAttributes["attributes"].addChild( Gaffer.NameValuePlug( "cycles:visibility:camera", False, True ) )
		exclusionAttributes["attributes"].addChild( Gaffer.NameValuePlug( "dl:visibility.camera", False, True ) )
		exclusionAttributes["attributes"].addChild( Gaffer.NameValuePlug( "ri:visibility:camera", False, True ) )

		# Create adaptors for the CapturingRenderer
		testAdaptors = GafferScene.SceneAlgo.createRenderAdaptors()
		testAdaptors["in"].setInput( exclusionAttributes["out"] )

		def assertCameraVisibleObjects( paths, cameraInclusions = None, cameraExclusions = None, inclusionOverrides = "", exclusionOverrides = "" ) :

			if cameraInclusions is not None :
				customOptions["options"]["cameraInclusions"]["value"].setValue( cameraInclusions )
			customOptions["options"]["cameraInclusions"]["enabled"].setValue( cameraInclusions is not None )

			if cameraExclusions is not None :
				customOptions["options"]["cameraExclusions"]["value"].setValue( cameraExclusions )
			customOptions["options"]["cameraExclusions"]["enabled"].setValue( cameraExclusions is not None )

			inclusionAttributesFilter["setExpression"].setValue( inclusionOverrides )
			exclusionAttributesFilter["setExpression"].setValue( exclusionOverrides )

			allPaths = {
				"/groupA/cube",
				"/groupA/sphere",
			}

			renderer = GafferScene.Private.IECoreScenePreview.CapturingRenderer(
				GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
			)
			GafferScene.Private.RendererAlgo.outputObjects(
				testAdaptors["out"], GafferScene.Private.RendererAlgo.RenderOptions( testAdaptors["out"] ), GafferScene.Private.RendererAlgo.RenderSets( testAdaptors["out"] ), GafferScene.Private.RendererAlgo.LightLinks(),
				renderer
			)

			if paths != {} :
				self.assertTrue( paths.issubset( allPaths ) )

			for path in allPaths :
				capturedObject = renderer.capturedObject( path )
				for attribute in [ "ai:visibility:camera", "cycles:visibility:camera", "dl:visibility.camera", "ri:visibility:camera" ] :
					if path in paths :
						# path is visible by the absence of the attribute, or its presence with a value of True
						if attribute in capturedObject.capturedAttributes().attributes() :
							self.assertTrue( capturedObject.capturedAttributes().attributes()[attribute].value )
					else :
						# path is invisible only by the presence of the attribute with a value of False
						self.assertTrue( attribute in capturedObject.capturedAttributes().attributes() )
						self.assertFalse( capturedObject.capturedAttributes().attributes()[attribute].value )

		# By default everything should be camera visible
		assertCameraVisibleObjects( { "/groupA/cube", "/groupA/sphere" } )

		# All should be visible with the root included
		assertCameraVisibleObjects( { "/groupA/cube", "/groupA/sphere" }, cameraInclusions = "/" )

		# All should be visible with the group included
		assertCameraVisibleObjects( { "/groupA/cube", "/groupA/sphere" }, cameraInclusions = "/groupA" )

		# Only the included location should be visible
		assertCameraVisibleObjects( { "/groupA/sphere" }, cameraInclusions = "/groupA/sphere" )

		# Nothing should be visible if nothing is included
		assertCameraVisibleObjects( {}, cameraInclusions = "" )

		# Test a variety of cameraInclusions set expressions
		assertCameraVisibleObjects( { "/groupA/cube", "/groupA/sphere" }, cameraInclusions = "A" )
		assertCameraVisibleObjects( { "/groupA/sphere" }, cameraInclusions = "SPHERE" )
		assertCameraVisibleObjects( { "/groupA/cube" }, cameraInclusions = "CUBE" )
		assertCameraVisibleObjects( { "/groupA/cube" }, cameraInclusions = "A - SPHERE" )

		# Test a variety of cameraExclusions set expressions
		assertCameraVisibleObjects( {}, cameraExclusions = "A" )
		assertCameraVisibleObjects( { "/groupA/cube" }, cameraExclusions = "SPHERE" )
		assertCameraVisibleObjects( { "/groupA/sphere" }, cameraExclusions = "CUBE" )
		assertCameraVisibleObjects( { "/groupA/sphere" }, cameraExclusions = "A - SPHERE" )

		# Camera exclusions overrides camera inclusions at the same location
		assertCameraVisibleObjects( {}, cameraInclusions = "A", cameraExclusions = "A" )

		# Camera exclusions overrides camera inclusions at a parent location
		assertCameraVisibleObjects( {}, cameraInclusions = "/", cameraExclusions = "A" )

		# Test a variety of camera inclusions and exclusions combinations
		assertCameraVisibleObjects( { "/groupA/sphere" }, cameraInclusions = "A", cameraExclusions = "CUBE" )
		assertCameraVisibleObjects( { "/groupA/sphere" }, cameraInclusions = "/groupA", cameraExclusions = "CUBE" )
		assertCameraVisibleObjects( { "/groupA/cube" }, cameraInclusions = "A", cameraExclusions = "SPHERE" )
		assertCameraVisibleObjects( { "/groupA/cube" }, cameraInclusions = "/groupA", cameraExclusions = "SPHERE" )

		# Camera inclusions overrides camera exclusions at lower locations
		assertCameraVisibleObjects( { "/groupA/sphere" }, cameraInclusions = "/groupA/sphere", cameraExclusions = "/groupA" )
		assertCameraVisibleObjects( { "/groupA/sphere" }, cameraInclusions = "SPHERE", cameraExclusions = "/groupA" )

		# Excluding nothing should leave everything visible
		assertCameraVisibleObjects( { "/groupA/cube", "/groupA/sphere" }, cameraExclusions = "" )

		# Test interaction with scene attributes
		assertCameraVisibleObjects( { "/groupA/sphere" }, cameraInclusions = "A", exclusionOverrides = "/groupA/cube" )
		assertCameraVisibleObjects( { "/groupA/cube", "/groupA/sphere" }, cameraInclusions = "A", exclusionOverrides = "/groupA" )
		assertCameraVisibleObjects( { "/groupA/cube", "/groupA/sphere" }, cameraInclusions = "CUBE", inclusionOverrides = "/groupA/sphere" )
		assertCameraVisibleObjects( { "/groupA/cube", "/groupA/sphere" }, cameraInclusions = "", inclusionOverrides = "A" )
		assertCameraVisibleObjects( {}, cameraInclusions = "/", exclusionOverrides = "A" )

	def testMatteAdaptor( self ) :

		#  /groupA
		#    /cube      (A, CUBE)
		#    /sphere    (A, SPHERE)

		cubeA = GafferScene.Cube()
		cubeA["sets"].setValue( "A CUBE" )

		sphereA = GafferScene.Sphere()
		sphereA["sets"].setValue( "A SPHERE" )

		groupA = GafferScene.Group()
		groupA["name"].setValue( "groupA" )
		groupA["in"][0].setInput( cubeA["out"] )
		groupA["in"][1].setInput( sphereA["out"] )

		customOptions = GafferScene.CustomOptions()
		customOptions["in"].setInput( groupA["out"] )
		customOptions["options"].addChild( Gaffer.NameValuePlug( "render:matteInclusions", "", True, "matteInclusions" ) )
		customOptions["options"].addChild( Gaffer.NameValuePlug( "render:matteExclusions", "", True, "matteExclusions" ) )

		inclusionAttributesFilter = GafferScene.SetFilter()
		inclusionAttributes = GafferScene.CustomAttributes()
		inclusionAttributes["in"].setInput( customOptions["out"] )
		inclusionAttributes["filter"].setInput( inclusionAttributesFilter["out"] )
		inclusionAttributes["attributes"].addChild( Gaffer.NameValuePlug( "ai:matte", True, True, "aiMatte" ) )
		inclusionAttributes["attributes"].addChild( Gaffer.NameValuePlug( "cycles:use_holdout", True, True, "cyclesUseHoldout" ) )
		inclusionAttributes["attributes"].addChild( Gaffer.NameValuePlug( "dl:matte", True, True, "dlMatte" ) )

		exclusionAttributesFilter = GafferScene.SetFilter()
		exclusionAttributes = GafferScene.CustomAttributes()
		exclusionAttributes["in"].setInput( inclusionAttributes["out"] )
		exclusionAttributes["filter"].setInput( exclusionAttributesFilter["out"] )
		exclusionAttributes["attributes"].addChild( Gaffer.NameValuePlug( "ai:matte", False, True, "aiMatte" ) )
		exclusionAttributes["attributes"].addChild( Gaffer.NameValuePlug( "cycles:use_holdout", False, True, "cyclesUseHoldout" ) )
		exclusionAttributes["attributes"].addChild( Gaffer.NameValuePlug( "dl:matte", False, True, "dlMatte" ) )

		# Create adaptors for the CapturingRenderer
		testAdaptors = GafferScene.SceneAlgo.createRenderAdaptors()
		testAdaptors["in"].setInput( exclusionAttributes["out"] )

		def assertMatte( paths, matteInclusions = None, matteExclusions = None, inclusionOverrides = "", exclusionOverrides = "" ) :

			if matteInclusions is not None :
				customOptions["options"]["matteInclusions"]["value"].setValue( matteInclusions )
			customOptions["options"]["matteInclusions"]["enabled"].setValue( matteInclusions is not None )

			if matteExclusions is not None :
				customOptions["options"]["matteExclusions"]["value"].setValue( matteExclusions )
			customOptions["options"]["matteExclusions"]["enabled"].setValue( matteExclusions is not None )

			inclusionAttributesFilter["setExpression"].setValue( inclusionOverrides )
			exclusionAttributesFilter["setExpression"].setValue( exclusionOverrides )

			allPaths = {
				"/groupA/cube",
				"/groupA/sphere",
			}

			renderer = GafferScene.Private.IECoreScenePreview.CapturingRenderer(
				GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
			)
			GafferScene.Private.RendererAlgo.outputObjects(
				testAdaptors["out"], GafferScene.Private.RendererAlgo.RenderOptions( testAdaptors["out"] ), GafferScene.Private.RendererAlgo.RenderSets( testAdaptors["out"] ), GafferScene.Private.RendererAlgo.LightLinks(),
				renderer
			)

			for path in allPaths :
				capturedObject = renderer.capturedObject( path )
				for attribute in [ "ai:matte", "cycles:use_holdout", "dl:matte" ] :
					if path in paths :
						# path is matte only by the presence of the attribute with a value of True
						self.assertTrue( attribute in capturedObject.capturedAttributes().attributes() )
						self.assertTrue( capturedObject.capturedAttributes().attributes()[attribute].value )
					else :
						# path isn't matte by the absence of the attribute, or its presence with a value of False
						if attribute in capturedObject.capturedAttributes().attributes() :
							self.assertFalse( capturedObject.capturedAttributes().attributes()[attribute].value )

		# Nothing should be matte when matte inclusions and exclusions are empty or undefined
		assertMatte( {} )
		assertMatte( {}, matteInclusions = "" )
		assertMatte( {}, matteExclusions = "" )
		assertMatte( {}, matteInclusions = "", matteExclusions = "" )

		# Including the root of the scene should make everything matte
		assertMatte( { "/groupA/cube", "/groupA/sphere" }, matteInclusions = "/" )

		# Including the group should make its descendants matte
		assertMatte( { "/groupA/cube", "/groupA/sphere" }, matteInclusions = "/groupA" )
		# Unless a descendant has been excluded
		assertMatte( { "/groupA/cube" }, matteInclusions = "/groupA", matteExclusions = "/groupA/sphere" )

		# Including a specific location should not affect its siblings
		assertMatte( { "/groupA/cube" }, matteInclusions = "/groupA/cube" )

		# Test a variety of set expressions
		assertMatte( { "/groupA/cube", "/groupA/sphere" }, matteInclusions = "A" )
		assertMatte( { "/groupA/sphere" }, matteInclusions = "SPHERE" )
		assertMatte( { "/groupA/cube" }, matteInclusions = "CUBE" )
		assertMatte( { "/groupA/sphere" }, matteInclusions = "A - CUBE" )

		# Exclusions should override inclusions
		assertMatte( {}, matteInclusions = "A", matteExclusions = "A" )
		assertMatte( {}, matteInclusions = "/groupA/sphere", matteExclusions = "/groupA/sphere" )
		assertMatte( { "/groupA/sphere" }, matteInclusions = "A", matteExclusions = "CUBE" )
		assertMatte( { "/groupA/cube" }, matteInclusions = "/groupA", matteExclusions = "SPHERE" )
		assertMatte( { "/groupA/sphere" }, matteInclusions = "A", matteExclusions = "/groupA/cube" )

		# Matte inclusions override matte exclusions at lower locations
		assertMatte( { "/groupA/sphere" }, matteInclusions = "/groupA/sphere", matteExclusions = "/groupA" )

		# Test interaction with scene attributes
		assertMatte( { "/groupA/sphere" }, inclusionOverrides = "/groupA/sphere" )
		assertMatte( { "/groupA/cube", "/groupA/sphere" }, matteInclusions = "/groupA/cube", inclusionOverrides = "/groupA/sphere" )
		assertMatte( { "/groupA/sphere" }, matteExclusions = "/groupA/sphere", inclusionOverrides = "/groupA/sphere" )
		assertMatte( { "/groupA/sphere" }, matteExclusions = "/groupA", inclusionOverrides = "/groupA/sphere" )
		assertMatte( { "/groupA/cube", "/groupA/sphere" }, matteInclusions = "/groupA", matteExclusions = "/groupA/sphere", inclusionOverrides = "/groupA/sphere" )

		assertMatte( {}, matteInclusions = "/groupA/sphere", exclusionOverrides = "/groupA/sphere" )
		assertMatte( { "/groupA/sphere" }, matteInclusions = "/groupA/sphere", exclusionOverrides = "/groupA" )
		assertMatte( { "/groupA/sphere" }, matteInclusions = "/groupA", exclusionOverrides = "/groupA/cube" )
