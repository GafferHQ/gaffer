##########################################################################
#
#  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

import pathlib
import sys
import time
import shutil
import unittest
import imath
import arnold

import IECore
import IECoreScene
import IECoreImage

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest
import GafferImage
import GafferArnold

class InteractiveArnoldRenderTest( GafferSceneTest.InteractiveRenderTest ) :

	renderer = "Arnold"

	# Arnold outputs licensing warnings that would cause failures
	failureMessageLevel = IECore.MessageHandler.Level.Error

	def testTwoRenders( self ) :

		s = Gaffer.ScriptNode()
		s["s"] = GafferScene.Sphere()

		s["o"] = GafferScene.Outputs()
		s["o"].addOutput(
			"beauty",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ImageDisplayDriver",
					"handle" : "myLovelySphere",
				}
			)
		)
		s["o"]["in"].setInput( s["s"]["out"] )

		s["r"] = self._createInteractiveRender()
		s["r"]["in"].setInput( s["o"]["out"] )

		s["r"]["state"].setValue( s["r"].State.Running )

		time.sleep( 0.5 )

		image = IECoreImage.ImageDisplayDriver.storedImage( "myLovelySphere" )
		self.assertTrue( isinstance( image, IECoreImage.ImagePrimitive ) )

		# Try to start a second render while the first is running.

		s["o2"] = GafferScene.Outputs()
		s["o2"].addOutput(
			"beauty",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ImageDisplayDriver",
					"handle" : "myLovelySphere2",
				}
			)
		)
		s["o2"]["in"].setInput( s["s"]["out"] )

		s["r2"] = self._createInteractiveRender( failOnError = False )
		s["r2"]["in"].setInput( s["o2"]["out"] )

		s["r2"]["state"].setValue( s["r"].State.Running )
		time.sleep( 0.5 )

		image = IECoreImage.ImageDisplayDriver.storedImage( "myLovelySphere2" )
		self.assertTrue( isinstance( image, IECoreImage.ImagePrimitive ) )

	def testEditSubdivisionAttributes( self ) :

		script = Gaffer.ScriptNode()

		script["cube"] = GafferScene.Cube()
		script["cube"]["dimensions"].setValue( imath.V3f( 2 ) )

		script["meshType"] = GafferScene.MeshType()
		script["meshType"]["in"].setInput( script["cube"]["out"] )
		script["meshType"]["meshType"].setValue( "catmullClark" )

		script["attributes"] = GafferArnold.ArnoldAttributes()
		script["attributes"]["in"].setInput( script["meshType"]["out"] )
		script["attributes"]["attributes"]["subdivIterations"]["enabled"].setValue( True )

		script["catalogue"] = GafferImage.Catalogue()

		script["outputs"] = GafferScene.Outputs()
		script["outputs"].addOutput(
			"beauty",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ClientDisplayDriver",
					"displayHost" : "localhost",
					"displayPort" : str( script['catalogue'].displayDriverServer().portNumber() ),
					"remoteDisplayType" : "GafferImage::GafferDisplayDriver",
				}
			)
		)
		script["outputs"]["in"].setInput( script["attributes"]["out"] )

		script["imageStats"] = GafferImage.ImageStats()
		script["imageStats"]["in"].setInput( script["catalogue"]["out"] )
		script["imageStats"]["channels"].setValue( IECore.StringVectorData( [ "R", "G", "B", "A" ] ) )
		script["imageStats"]["area"].setValue( imath.Box2i( imath.V2i( 0 ), imath.V2i( 640, 480 ) ) )

		script["options"] = GafferScene.StandardOptions()
		script["options"]["in"].setInput( script["outputs"]["out"] )
		script["options"]["options"]["filmFit"]["enabled"].setValue( True )
		script["options"]["options"]["filmFit"]["value"].setValue( IECoreScene.Camera.FilmFit.Fit )

		script["render"] = self._createInteractiveRender()
		script["render"]["in"].setInput( script["options"]["out"] )

		# Render the cube with one level of subdivision. Check we get roughly the
		# alpha coverage we expect.

		script["render"]["state"].setValue( script["render"].State.Running )

		self.uiThreadCallHandler.waitFor( 1 )

		self.assertAlmostEqual( script["imageStats"]["average"][3].getValue(), 0.381, delta = 0.001 )

		# Now up the number of subdivision levels. The alpha coverage should
		# increase as the shape tends towards the limit surface.

		script["attributes"]["attributes"]["subdivIterations"]["value"].setValue( 4 )
		self.uiThreadCallHandler.waitFor( 1 )

		self.assertAlmostEqual( script["imageStats"]["average"][3].getValue(), 0.424, delta = 0.001 )

		script["render"]["state"].setValue( script["render"].State.Stopped )

	def testLightLinkingAfterParameterUpdates( self ) :

		s = Gaffer.ScriptNode()
		s["catalogue"] = GafferImage.Catalogue()


		s["s"] = GafferScene.Sphere()

		s["PathFilter"] = GafferScene.PathFilter( "PathFilter" )
		s["PathFilter"]["paths"].setValue( IECore.StringVectorData( [ '/sphere' ] ) )

		s["ShaderAssignment"] = GafferScene.ShaderAssignment( "ShaderAssignment" )
		s["ShaderAssignment"]["in"].setInput( s["s"]["out"] )
		s["ShaderAssignment"]["filter"].setInput( s["PathFilter"]["out"] )

		s["lambert"], _, lambertOut = self._createMatteShader()
		s["ShaderAssignment"]["shader"].setInput( lambertOut )

		s["StandardAttributes"] = GafferScene.StandardAttributes( "StandardAttributes" )
		s["StandardAttributes"]["attributes"]["linkedLights"]["enabled"].setValue( True )
		s["StandardAttributes"]["attributes"]["linkedLights"]["value"].setValue( "defaultLights" )
		s["StandardAttributes"]["filter"].setInput( s["PathFilter"]["out"] )
		s["StandardAttributes"]["in"].setInput( s["ShaderAssignment"]["out"] )

		s["Light"] = GafferArnold.ArnoldLight( "skydome_light" )
		s["Light"].loadShader( "skydome_light" )

		s["c"] = GafferScene.Camera()
		s["c"]["transform"]["translate"]["z"].setValue( 2 )

		s["group"] = GafferScene.Group()
		s["group"]["in"][0].setInput( s["StandardAttributes"]["out"] )
		s["group"]["in"][1].setInput( s["Light"]["out"] )
		s["group"]["in"][2].setInput( s["c"]["out"] )

		s["o"] = GafferScene.Outputs()
		s["o"].addOutput(
			"beauty",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ClientDisplayDriver",
					"displayHost" : "localhost",
					"displayPort" : str( s['catalogue'].displayDriverServer().portNumber() ),
					"remoteDisplayType" : "GafferImage::GafferDisplayDriver",
				}
			)
		)
		s["o"]["in"].setInput( s["group"]["out"] )

		s["so"] = GafferScene.StandardOptions()
		s["so"]["options"]["renderCamera"]["value"].setValue( "/group/camera" )
		s["so"]["options"]["renderCamera"]["enabled"].setValue( True )
		s["so"]["in"].setInput( s["o"]["out"] )

		s["r"] = self._createInteractiveRender()
		s["r"]["in"].setInput( s["so"]["out"] )

		# Start rendering and make sure the light is linked to the sphere

		s["r"]["state"].setValue( s["r"].State.Running )

		self.uiThreadCallHandler.waitFor( 1.0 )

		self.assertAlmostEqual(
			self._color4fAtUV( s["catalogue"], imath.V2f( 0.5 ) ).r,
			1,
			delta = 0.01
		)

		# Change a value on the light. The light should still be linked to the sphere
		# and we should get the same result as before.
		s["Light"]['parameters']['shadow_density'].setValue( 0.0 )

		self.uiThreadCallHandler.waitFor( 1.0 )

		self.assertAlmostEqual(
			self._color4fAtUV( s["catalogue"], imath.V2f( 0.5 ) ).r,
			1,
			delta = 0.01
		)

		s["r"]["state"].setValue( s["r"].State.Stopped )

	def testQuadLightTextureEdits( self ) :

		# Quad light texture edits don't currently update correctly in Arnold.
		# Check that our workaround is working

		s = Gaffer.ScriptNode()
		s["catalogue"] = GafferImage.Catalogue()


		s["s"] = GafferScene.Sphere()

		s["PathFilter"] = GafferScene.PathFilter( "PathFilter" )
		s["PathFilter"]["paths"].setValue( IECore.StringVectorData( [ '/sphere' ] ) )

		s["ShaderAssignment"] = GafferScene.ShaderAssignment( "ShaderAssignment" )
		s["ShaderAssignment"]["in"].setInput( s["s"]["out"] )
		s["ShaderAssignment"]["filter"].setInput( s["PathFilter"]["out"] )

		s["lambert"], _, lambertOut = self._createMatteShader()
		s["ShaderAssignment"]["shader"].setInput( lambertOut )

		s["Tex"] = GafferArnold.ArnoldShader( "image" )
		s["Tex"].loadShader( "image" )
		s["Tex"]["parameters"]["filename"].setValue( pathlib.Path( __file__ ).parent / "images" / "sphereLightBake.exr" )
		s["Tex"]["parameters"]["multiply"].setValue( imath.Color3f( 1, 0, 0 ) )

		s["Light"] = GafferArnold.ArnoldLight( "quad_light" )
		s["Light"].loadShader( "quad_light" )
		s["Light"]["transform"]["translate"]["z"].setValue( 2 )
		s["Light"]["parameters"]["color"].setInput( s["Tex"]["out"] )
		s["Light"]["parameters"]["exposure"].setValue( 6 )
		s["Light"]["parameters"]["samples"].setValue( 6 )

		s["c"] = GafferScene.Camera()
		s["c"]["transform"]["translate"]["z"].setValue( 2 )

		s["group"] = GafferScene.Group()
		s["group"]["in"][0].setInput( s["ShaderAssignment"]["out"] )
		s["group"]["in"][1].setInput( s["Light"]["out"] )
		s["group"]["in"][2].setInput( s["c"]["out"] )

		s["o"] = GafferScene.Outputs()
		s["o"].addOutput(
			"beauty",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ClientDisplayDriver",
					"displayHost" : "localhost",
					"displayPort" : str( s['catalogue'].displayDriverServer().portNumber() ),
					"remoteDisplayType" : "GafferImage::GafferDisplayDriver",
				}
			)
		)
		s["o"]["in"].setInput( s["group"]["out"] )

		s["so"] = GafferScene.StandardOptions()
		s["so"]["options"]["renderCamera"]["value"].setValue( "/group/camera" )
		s["so"]["options"]["renderCamera"]["enabled"].setValue( True )
		s["so"]["in"].setInput( s["o"]["out"] )

		s["r"] = self._createInteractiveRender()
		s["r"]["in"].setInput( s["so"]["out"] )

		# Start rendering and make sure the light is linked to the sphere

		s["r"]["state"].setValue( s["r"].State.Running )

		self.uiThreadCallHandler.waitFor( 1.0 )

		initialColor = self._color4fAtUV( s["catalogue"], imath.V2f( 0.5 ) )
		self.assertAlmostEqual( initialColor.r, 0.58, delta = 0.02 )
		self.assertAlmostEqual( initialColor.g, 0, delta = 0.01 )

		# Edit texture network and make sure the changes take effect

		s["Tex"]["parameters"]["multiply"].setValue( imath.Color3f( 0, 1, 0 ) )

		self.uiThreadCallHandler.waitFor( 1.0 )

		updateColor = self._color4fAtUV( s["catalogue"], imath.V2f( 0.5 ) )
		self.assertAlmostEqual( updateColor.r, 0, delta = 0.01 )
		self.assertAlmostEqual( updateColor.g, 0.3, delta = 0.02 )

		s["r"]["state"].setValue( s["r"].State.Stopped )

	def testFlushCache( self ) :

		# Arnold has a shared texture cache. We want to make sure that on a render stop
		# that the cache gets reloaded from the default universe.

		# Create tmp file for texture image
		redTextureFile  = pathlib.Path( __file__ ).parent / "images" / "red.exr"
		blueTextureFile = pathlib.Path( __file__ ).parent / "images" / "blue.exr"
		tmpTextureFile  = self.temporaryDirectory() / "texture.exr"
		shutil.copyfile( redTextureFile, tmpTextureFile )

		s = Gaffer.ScriptNode()
		s["catalogue"] = GafferImage.Catalogue()

		s["s"] = GafferScene.Sphere()

		s["PathFilter"] = GafferScene.PathFilter( "PathFilter" )
		s["PathFilter"]["paths"].setValue( IECore.StringVectorData( [ '/sphere' ] ) )

		s["ShaderAssignment"] = GafferScene.ShaderAssignment( "ShaderAssignment" )
		s["ShaderAssignment"]["in"].setInput( s["s"]["out"] )
		s["ShaderAssignment"]["filter"].setInput( s["PathFilter"]["out"] )

		# Add a texture
		s["Tex"] = GafferArnold.ArnoldShader( "image" )
		s["Tex"].loadShader( "image" )
		s["Tex"]["parameters"]["filename"].setValue( tmpTextureFile )

		# Create a constant shader
		s["constant"], shaderColor, constantOut = self._createConstantShader()
		shaderColor.setInput( s["Tex"]["out"] )
		s["ShaderAssignment"]["shader"].setInput( constantOut )

		s["c"] = GafferScene.Camera()
		s["c"]["transform"]["translate"]["z"].setValue( 2 )

		s["group"] = GafferScene.Group()
		s["group"]["in"][0].setInput( s["ShaderAssignment"]["out"] )
		s["group"]["in"][1].setInput( s["c"]["out"] )

		s["o"] = GafferScene.Outputs()
		s["o"].addOutput(
			"beauty",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ClientDisplayDriver",
					"displayHost" : "localhost",
					"displayPort" : str( s['catalogue'].displayDriverServer().portNumber() ),
					"remoteDisplayType" : "GafferImage::GafferDisplayDriver",
				}
			)
		)
		s["o"]["in"].setInput( s["group"]["out"] )

		s["so"] = GafferScene.StandardOptions()
		s["so"]["options"]["renderCamera"]["value"].setValue( "/group/camera" )
		s["so"]["options"]["renderCamera"]["enabled"].setValue( True )
		s["so"]["in"].setInput( s["o"]["out"] )

		s["r"] = self._createInteractiveRender()
		s["r"]["in"].setInput( s["so"]["out"] )

		# Start render 1 and save the image output.
		s["r"]["state"].setValue( s["r"].State.Running )
		self.uiThreadCallHandler.waitFor( 1.0 )
		s["r"]["state"].setValue( s["r"].State.Stopped )
		redTexture = self._color4fAtUV( s["catalogue"], imath.V2f( 0.5 ) )

		# Copy new texture
		shutil.copyfile( blueTextureFile, tmpTextureFile )
		# If no renders are currently running, then we must call the Arnold API
		# directly to flush the global cache.
		arnold.AiUniverseCacheFlush( None, arnold.AI_CACHE_ALL )

		# Start and stop new render
		s["r"]["state"].setValue( s["r"].State.Running )
		self.uiThreadCallHandler.waitFor( 1.0 )
		s["r"]["state"].setValue( s["r"].State.Stopped )

		# Get image from new render.
		blueTexture = self._color4fAtUV( s["catalogue"], imath.V2f( 0.5 ) )

		# Make sure that the two renders are different.
		self.assertNotEqual( redTexture, blueTexture )

		# Double check that the textures are the right colours.
		# Texture one should have red and no blue.
		self.assertAlmostEqual( redTexture.r, 1.0, delta = 0.01 )
		self.assertAlmostEqual( redTexture.b, 0.0, delta = 0.01 )

		# Texture one should have blue and no red.
		self.assertAlmostEqual( blueTexture.b, 1.0, delta = 0.01 )
		self.assertAlmostEqual( blueTexture.r, 0.0, delta = 0.01 )

		# Reset texture.
		shutil.copyfile( redTextureFile, tmpTextureFile )
		arnold.AiUniverseCacheFlush( None, arnold.AI_CACHE_ALL )

		# Now test flush cache during a render
		s["r"]["state"].setValue( s["r"].State.Running )
		self.uiThreadCallHandler.waitFor( 1.0 )

		# Get colour after 1 second of render.
		redTexture = self._color4fAtUV( s["catalogue"], imath.V2f( 0.5 ) )

		# Copy new texture, flush cache and then render for 1 second.
		shutil.copyfile( blueTextureFile, tmpTextureFile )
		# If the renderer is running, then we use `command()` to flush the
		# cache, managing the pause/restart for us.
		s["r"].command( "ai:cacheFlush", { "flags" : arnold.AI_CACHE_ALL } )
		self.uiThreadCallHandler.waitFor( 1.0 )

		# Get colour of second texture and stop.
		blueTexture = self._color4fAtUV( s["catalogue"], imath.V2f( 0.5 ) )
		s["r"]["state"].setValue( s["r"].State.Stopped )

		# Make sure that the two renders are different.
		self.assertNotEqual( redTexture, blueTexture )

		# Double check that the textures are the right colours.
		# Texture one should have red and no blue.
		self.assertAlmostEqual( redTexture.r, 1.0, delta = 0.01 )
		self.assertAlmostEqual( redTexture.b, 0.0, delta = 0.01 )

		# Texture one should have blue and no red.
		self.assertAlmostEqual( blueTexture.b, 1.0, delta = 0.01 )
		self.assertAlmostEqual( blueTexture.r, 0.0, delta = 0.01 )

	def testMeshLightFilterChange( self ) :

		s = Gaffer.ScriptNode()

		s["catalogue"] = GafferImage.Catalogue()

		s["sphere"] = GafferScene.Sphere()
		s["cube"] = GafferScene.Cube()

		s["group"] = GafferScene.Group()
		s["group"]["in"][0].setInput( s["sphere"]["out"] )
		s["group"]["in"][1].setInput( s["cube"]["out"] )

		s["filter"] = GafferScene.PathFilter()
		s["filter"]["paths"].setValue( IECore.StringVectorData( [ '/group/sphere' ] ) )

		s["meshLight"] = GafferArnold.ArnoldMeshLight()
		s["meshLight"]["in"].setInput( s["group"]["out"] )
		s["meshLight"]["filter"].setInput( s["filter"]["out"] )

		s["outputs"] = GafferScene.Outputs()
		s["outputs"]["in"].setInput( s["meshLight"]["out"] )
		s["outputs"].addOutput(
			"beauty",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ClientDisplayDriver",
					"displayHost" : "localhost",
					"displayPort" : str( s['catalogue'].displayDriverServer().portNumber() ),
					"remoteDisplayType" : "GafferImage::GafferDisplayDriver",
				}
			)
		)

		s["render"] = self._createInteractiveRender()
		s["render"]["in"].setInput( s["outputs"]["out"] )

		# Start rendering.

		s["render"]["state"].setValue( s["render"].State.Running )
		self.uiThreadCallHandler.waitFor( 1.0 )

		# Switch which object is tagged as a mesh light. This used to trigger a
		# crash.
		s["filter"]["paths"].setValue( IECore.StringVectorData( [ '/group/cube' ] ) )
		self.uiThreadCallHandler.waitFor( 1.0 )

		s["render"]["state"].setValue( s["render"].State.Stopped )

	def testMeshLightTexture( self ) :

		# Build scene with textures mesh light `/group/sphere1`
		# on left, illuminating a sphere `/group/sphere2` on right.

		s = Gaffer.ScriptNode()

		s["catalogue"] = GafferImage.Catalogue()

		s["sphere1"] = GafferScene.Sphere()
		s["sphere1"]["name"].setValue( "sphere1" )
		s["sphere1"]["radius"].setValue( 10 )
		s["sphere1"]["transform"]["translate"].setValue( imath.V3f( -10, 0, -2 ) )

		s["sphere2"] = GafferScene.Sphere()
		s["sphere2"]["name"].setValue( "sphere2" )
		s["sphere2"]["transform"]["translate"].setValue( imath.V3f( 1, 0, -2 ) )

		s["group"] = GafferScene.Group()
		s["group"]["in"][0].setInput( s["sphere1"]["out"] )
		s["group"]["in"][1].setInput( s["sphere2"]["out"] )

		s["sphere1Filter"] = GafferScene.PathFilter()
		s["sphere1Filter"]["paths"].setValue( IECore.StringVectorData( [ '/group/sphere1' ] ) )

		s["checkerboard"] = GafferArnold.ArnoldShader()
		s["checkerboard"].loadShader( "checkerboard" )

		s["meshLight"] = GafferArnold.ArnoldMeshLight()
		s["meshLight"]["in"].setInput( s["group"]["out"] )
		s["meshLight"]["filter"].setInput( s["sphere1Filter"]["out"] )
		s["meshLight"]["parameters"]["color"].setInput( s["checkerboard"]["out"] )
		s["meshLight"]["parameters"]["exposure"].setValue( 11 )

		s["lambert"] = GafferArnold.ArnoldShader()
		s["lambert"].loadShader( "lambert" )

		s["sphere2Filter"] = GafferScene.PathFilter()
		s["sphere2Filter"]["paths"].setValue( IECore.StringVectorData( [ '/group/sphere2' ] ) )

		s["shaderAssignment"] = GafferScene.ShaderAssignment()
		s["shaderAssignment"]["in"].setInput( s["meshLight"]["out"] )
		s["shaderAssignment"]["filter"].setInput( s["sphere2Filter"]["out"] )
		s["shaderAssignment"]["shader"].setInput( s["lambert"]["out"] )

		s["outputs"] = GafferScene.Outputs()
		s["outputs"]["in"].setInput( s["shaderAssignment"]["out"] )
		s["outputs"].addOutput(
			"beauty",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ClientDisplayDriver",
					"displayHost" : "localhost",
					"displayPort" : str( s['catalogue'].displayDriverServer().portNumber() ),
					"remoteDisplayType" : "GafferImage::GafferDisplayDriver",
				}
			)
		)

		s["options"] = GafferArnold.ArnoldOptions()
		s["options"]["in"].setInput( s["outputs"]["out"] )
		s["options"]["options"]["aaSamples"]["enabled"].setValue( True )
		s["options"]["options"]["aaSamples"]["value"].setValue( 5 )

		s["render"] = self._createInteractiveRender()
		s["render"]["in"].setInput( s["options"]["out"] )

		# Render, and check `sphere2`` is receiving illumination.

		s["render"]["state"].setValue( s["render"].State.Running )
		self.uiThreadCallHandler.waitFor( 1.0 )

		litColor = self._color4fAtUV( s["catalogue"], imath.V2f( 0.75, 0.5 ) )
		self.assertGreater( litColor.r, 0.1 )
		self.assertGreater( litColor.g, 0.1 )
		self.assertGreater( litColor.b, 0.1 )

	@unittest.skipIf( sys.platform == "win32", "Automated test fails on Windows whereas manual equivalent test passes." )
	def testEditLightGroups( self ) :

		for withOtherOutput in ( True, False ) :

			with self.subTest( withOtherOutput = withOtherOutput ) :

				script = Gaffer.ScriptNode()
				script["catalogue"] = GafferImage.Catalogue()

				script["sphere"] = GafferScene.Sphere()

				script["light1"] = GafferArnold.ArnoldLight()
				script["light1"].loadShader( "point_light" )
				script["light2"] = GafferArnold.ArnoldLight()
				script["light2"].loadShader( "point_light" )

				script["parent"] = GafferScene.Parent()
				script["parent"]["parent"].setValue( "/" )
				script["parent"]["children"][0].setInput( script["sphere"]["out"] )
				script["parent"]["children"][1].setInput( script["light1"]["out"] )
				script["parent"]["children"][2].setInput( script["light2"]["out"] )

				script["outputs"] = GafferScene.Outputs()
				script["outputs"]["in"].setInput( script["parent"]["out"] )

				if withOtherOutput :
					script["outputs"].addOutput(
						"beauty",
						IECoreScene.Output(
							"test",
							"ieDisplay",
							"rgba",
							{
								"driverType" : "ClientDisplayDriver",
								"displayHost" : "localhost",
								"displayPort" : str( script["catalogue"].displayDriverServer().portNumber() ),
								"remoteDisplayType" : "GafferImage::GafferDisplayDriver",
							}
						)
					)
					otherChannels = { "R", "G", "B", "A" }
				else :
					otherChannels = set()

				script["outputs"].addOutput(
					"beautyPerLight",
					IECoreScene.Output(
						"test",
						"ieDisplay",
						"rgba",
						{
							"driverType" : "ClientDisplayDriver",
							"displayHost" : "localhost",
							"displayPort" : str( script["catalogue"].displayDriverServer().portNumber() ),
							"remoteDisplayType" : "GafferImage::GafferDisplayDriver",
							"layerPerLightGroup" : True,
						}
					)
				)

				script["renderer"] = self._createInteractiveRender()
				script["renderer"]["in"].setInput( script["outputs"]["out"] )

				# Start a render, give it time to finish, and check the output.
				# Because there are no light groups yet, Arnold chooses to
				# render just the `RGBA_default` catch-all.

				script["renderer"]["state"].setValue( script["renderer"].State.Running )
				self.uiThreadCallHandler.waitFor( 1 )

				self.assertEqual( len( script["catalogue"]["images"] ), 1 )
				self.assertEqual(
					set( script["catalogue"]["out"].channelNames() ),
					otherChannels |
					{ "RGBA_default.{}".format( c ) for c in "RGBA" }
				)
				self.assertEqual( script["catalogue"]["out"].metadata()["gaffer:isRendering"], IECore.BoolData( True ) )

				# Add a light group. We should now get `RGBA_groupA` for the
				# light group we made, and `RGBA_default` as a catch-all for
				# anything else.

				script["light1"]["parameters"]["aov"].setValue( "groupA" )
				self.uiThreadCallHandler.waitFor( 1 )

				self.assertEqual( len( script["catalogue"]["images"] ), 1 )
				self.assertEqual( script["catalogue"]["out"].metadata()["gaffer:isRendering"], IECore.BoolData( True ) )
				self.assertEqual(
					set( script["catalogue"]["out"].channelNames() ),
					otherChannels |
					{ "RGBA_default.{}".format( c ) for c in "RGBA" } |
					{ "RGBA_groupA.{}".format( c ) for c in "RGBA" }
				)

				# Add another light group and check it appears. Ideally the
				# `RGBA_default` catch-all would disappear as well, but Arnold doesn't
				# do that yet.

				script["light2"]["parameters"]["aov"].setValue( "groupB" )
				self.uiThreadCallHandler.waitFor( 1 )

				self.assertEqual( len( script["catalogue"]["images"] ), 1 )
				self.assertEqual( script["catalogue"]["out"].metadata()["gaffer:isRendering"], IECore.BoolData( True ) )
				self.assertEqual(
					set( script["catalogue"]["out"].channelNames() ),
					otherChannels |
					{ "RGBA_default.{}".format( c ) for c in "RGBA" } |
					{ "RGBA_groupA.{}".format( c ) for c in "RGBA" } |
					{ "RGBA_groupB.{}".format( c ) for c in "RGBA" }
				)

				# Remove a light group. Ideally we'd assert that the additional image
				# layers have been removed now, but Arnold doesn't seem to reliably
				# reopen the driver with fewer layers. So we satisfy ourselves with
				# checking that at least we haven't made any unnecessary catalogue
				# images.

				script["light1"]["enabled"].setValue( False )
				self.uiThreadCallHandler.waitFor( 1 )

				self.assertEqual( len( script["catalogue"]["images"] ), 1 )
				self.assertEqual( script["catalogue"]["out"].metadata()["gaffer:isRendering"], IECore.BoolData( True ) )

				# Stop the renderer, and check we still have only one image, and
				# that it is no longer rendering.

				script["renderer"]["state"].setValue( script["renderer"].State.Stopped )
				self.uiThreadCallHandler.waitFor( 0.5 ) # Wait for saving to complete

				self.assertEqual( len( script["catalogue"]["images"] ), 1 )
				self.assertNotIn( "gaffer:isRendering", script["catalogue"]["out"].metadata() )

	## \todo Promote to InteractiveRenderTest and check it works for other renderer backends.
	def testEditOutputMetadata( self ) :

		script = Gaffer.ScriptNode()
		script["catalogue"] = GafferImage.Catalogue()

		script["sphere"] = GafferScene.Sphere()

		script["outputs"] = GafferScene.Outputs()
		script["outputs"]["in"].setInput( script["sphere"]["out"] )

		script["outputs"].addOutput(
			"beauty",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ClientDisplayDriver",
					"displayHost" : "localhost",
					"displayPort" : str( script["catalogue"].displayDriverServer().portNumber() ),
					"remoteDisplayType" : "GafferImage::GafferDisplayDriver",
					"header:test1" : "hello",
					"header:test2" : "world",
				}
			)
		)

		script["renderer"] = self._createInteractiveRender()
		script["renderer"]["in"].setInput( script["outputs"]["out"] )

		# Start a render, give it time to finish, and check we have our
		# custom metadata in the outputs.

		script["renderer"]["state"].setValue( script["renderer"].State.Running )
		self.uiThreadCallHandler.waitFor( 1 )

		self.assertEqual( len( script["catalogue"]["images"] ), 1 )
		self.assertEqual( script["catalogue"]["out"].metadata()["test1"], IECore.StringData( "hello" ) )
		self.assertEqual( script["catalogue"]["out"].metadata()["test2"], IECore.StringData( "world" ) )

		# Modify the header parameters and rerender.

		with Gaffer.DirtyPropagationScope() :

			script["outputs"]["outputs"][0]["parameters"]["header_test1"]["name"].setValue( "header:test1B" )
			script["outputs"]["outputs"][0]["parameters"]["header_test2"]["value"].setValue( "edited" )

		self.uiThreadCallHandler.waitFor( 1 )

		self.assertEqual( len( script["catalogue"]["images"] ), 1 )
		self.assertNotIn( "test1", script["catalogue"]["out"].metadata() )
		self.assertEqual( script["catalogue"]["out"].metadata()["test1B"], IECore.StringData( "hello" ) )
		self.assertEqual( script["catalogue"]["out"].metadata()["test2"], IECore.StringData( "edited" ) )

	## \todo Promote to InteractiveRenderTest and check it works for other renderer backends.
	def testEditOutputType( self ) :

		script = Gaffer.ScriptNode()
		script["catalogue"] = GafferImage.Catalogue()

		script["sphere"] = GafferScene.Sphere()

		script["outputs"] = GafferScene.Outputs()
		script["outputs"]["in"].setInput( script["sphere"]["out"] )

		script["outputs"].addOutput(
			"beauty",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ClientDisplayDriver",
					"displayHost" : "localhost",
					"displayPort" : str( script["catalogue"].displayDriverServer().portNumber() ),
					"remoteDisplayType" : "GafferImage::GafferDisplayDriver",
				}
			)
		)

		script["renderer"] = self._createInteractiveRender()
		script["renderer"]["in"].setInput( script["outputs"]["out"] )

		# Start a render, give it time to finish, and check we have an image.

		script["renderer"]["state"].setValue( script["renderer"].State.Running )
		self.uiThreadCallHandler.waitFor( 1 )

		self.assertEqual( len( script["catalogue"]["images"] ), 1 )
		self.assertEqual( script["catalogue"]["out"].metadata()["gaffer:isRendering"], IECore.BoolData( True ) )

		# Modify the output to render to file instead of the catalogue, and check
		# the catalogue image is closed and the file is created.

		with Gaffer.DirtyPropagationScope() :

			script["outputs"]["outputs"][0]["fileName"].setValue( self.temporaryDirectory() / "test.exr" )
			script["outputs"]["outputs"][0]["type"].setValue( "exr" )

		self.uiThreadCallHandler.waitFor( 1 )

		self.assertEqual( len( script["catalogue"]["images"] ), 1 )
		self.assertNotIn( "gaffer:isRendering", script["catalogue"]["out"].metadata() )
		self.assertTrue( ( self.temporaryDirectory() / "test.exr" ).is_file() )

	## \todo Promote to InteractiveRenderTest and check it works for other renderer backends.
	def testEditOutputFilterType( self ) :

		script = Gaffer.ScriptNode()
		script["catalogue"] = GafferImage.Catalogue()

		script["sphere"] = GafferScene.Sphere()

		script["outputs"] = GafferScene.Outputs()
		script["outputs"]["in"].setInput( script["sphere"]["out"] )

		script["outputs"].addOutput(
			"beauty",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ClientDisplayDriver",
					"displayHost" : "localhost",
					"displayPort" : str( script["catalogue"].displayDriverServer().portNumber() ),
					"remoteDisplayType" : "GafferImage::GafferDisplayDriver",
					"filter" : "gaussian"
				}
			)
		)

		script["renderer"] = self._createInteractiveRender()
		script["renderer"]["in"].setInput( script["outputs"]["out"] )

		# Start a render, give it time to finish, and check we have an image.

		script["renderer"]["state"].setValue( script["renderer"].State.Running )
		self.uiThreadCallHandler.waitFor( 1 )

		self.assertEqual( len( script["catalogue"]["images"] ), 1 )
		self.assertEqual( script["catalogue"]["out"].metadata()["gaffer:isRendering"], IECore.BoolData( True ) )

		self.assertAlmostEqual(
			self._color4fAtUV( script["catalogue"], imath.V2f( 0.5 ) ).r,
			1,
			delta = 0.01
		)

		# Modify the output to use a different filter, check we're still
		# rendering to the same image in the catalogue, and that the image
		# has been affected by the filter.

		script["outputs"]["outputs"][0]["parameters"]["filter"]["value"].setValue( "variance" )

		self.uiThreadCallHandler.waitFor( 1 )

		self.assertEqual( len( script["catalogue"]["images"] ), 1 )
		self.assertEqual( script["catalogue"]["out"].metadata()["gaffer:isRendering"], IECore.BoolData( True ) )

		self.assertAlmostEqual(
			self._color4fAtUV( script["catalogue"], imath.V2f( 0.5 ) ).r,
			0,
			delta = 0.01
		)

	def _createConstantShader( self ) :

		shader = GafferArnold.ArnoldShader()
		shader.loadShader( "flat" )
		return shader, shader["parameters"]["color"], shader["out"]

	def _createMatteShader( self ) :

		shader = GafferArnold.ArnoldShader()
		shader.loadShader( "lambert" )
		shader["parameters"]["Kd"].setValue( 1 )
		return shader, shader["parameters"]["Kd_color"], shader["out"]

	def _createTraceSetShader( self ) :
		# It's currently pretty ugly how we need to disable the trace set when it is left empty,
		# to match the behaviour expected by GafferSceneTest.InteractiveRenderTest.
		# Would be somewhat cleaner if we had the primaryInput metadata on trace_set
		# available, so we could just put an expression on it to disable it when no trace set is given,
		# but it doesn't seem very safe to do a metadata load in the middle of the tests
		shaderBox = Gaffer.Box()

		shader = GafferArnold.ArnoldShader("shader")
		shader.loadShader( "standard_surface" )

		shader["parameters"]["base"].setValue( 1 )
		shader["parameters"]["base_color"].setValue( imath.Color3f( 1 ) )
		shader["parameters"]["specular_roughness"].setValue( 0 )
		shader["parameters"]["metalness"].setValue( 1 )
		shader["parameters"]["specular_IOR"].setValue( 100 )

		#return shader, Gaffer.StringPlug( "unused" )

		traceSetShader = GafferArnold.ArnoldShader("traceSetShader")
		traceSetShader.loadShader( "trace_set" )
		traceSetShader["parameters"]["passthrough"].setInput( shader["out"] )

		switchShader = GafferArnold.ArnoldShader("switchShader")
		switchShader.loadShader( "switch_shader" )
		switchShader["parameters"]["input0"].setInput( shader["out"] )
		switchShader["parameters"]["input1"].setInput( traceSetShader["out"] )

		shaderBox.addChild( shader )
		shaderBox.addChild( traceSetShader )
		shaderBox.addChild( switchShader )

		shaderBox["enableExpression"] = Gaffer.Expression()
		shaderBox["enableExpression"].setExpression( 'parent.switchShader.parameters.index = parent.traceSetShader.parameters.trace_set != ""', "OSL" )

		Gaffer.PlugAlgo.promote( switchShader["out"] )

		return shaderBox, traceSetShader["parameters"]["trace_set"], shaderBox["out"]

	def _cameraVisibilityAttribute( self ) :

		return "ai:visibility:camera"

	def _traceDepthOptions( self ) :

		return "ai:GI_specular_depth", "ai:GI_diffuse_depth", "ai:GI_transmission_depth"

	def _createPointLight( self ) :

		light = GafferArnold.ArnoldLight()
		light.loadShader( "point_light" )
		return light, light["parameters"]["color"]

	def _createSpotLight( self ) :

		light = GafferArnold.ArnoldLight()
		light.loadShader( "spot_light" )
		return light, light["parameters"]["color"]

	def _createLightFilter( self ) :

		lightFilter = GafferArnold.ArnoldLightFilter()
		lightFilter.loadShader( "light_blocker" )
		return lightFilter, lightFilter["parameters"]["density"]

	def _createGobo( self ) :

		gobo = GafferArnold.ArnoldShader()
		gobo.loadShader( "gobo" )

		return gobo, gobo["parameters"]["slidemap"]

if __name__ == "__main__":
	unittest.main()
