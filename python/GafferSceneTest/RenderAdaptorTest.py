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
