##########################################################################
#
#  Copyright (c) 2022, Cinesite VFX Ltd. All rights reserved.
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
import math
import time
import unittest

import imath

import IECore
import IECoreScene
import IECoreImage
import IECoreVDB

import GafferScene
import GafferCycles

import GafferTest

class RendererTest( GafferTest.TestCase ) :

	def testObjectColor( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create( "Cycles" )

		renderer.output(
			"testOutput",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ImageDisplayDriver",
					"handle" : "testObjectColor",
				}
			)
		)

		plane = renderer.object(
			"/plane",
			IECoreScene.MeshPrimitive.createPlane(
				imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ),
			),
			renderer.attributes( IECore.CompoundObject ( {
				"render:displayColor" : IECore.Color3fData( imath.Color3f( 1, 0.5, 0.25 ) ),
				"cycles:surface" : IECoreScene.ShaderNetwork(
					shaders = {
						"output" : IECoreScene.Shader( "principled_bsdf", "cycles:surface", { "emission_strength" : 1 } ),
						"info" : IECoreScene.Shader( "object_info", "cycles:shader" )
					},
					connections = [
						( ( "info", "color" ), ( "output", "emission_color" ) )
					],
					output = "output",
				)
			} ) )
		)
		plane.transform( imath.M44f().translate( imath.V3f( 0, 0, -1 ) ) )

		renderer.render()

		image = IECoreImage.ImageDisplayDriver.storedImage( "testObjectColor" )
		self.assertIsInstance( image, IECoreImage.ImagePrimitive )

		# Slightly off-centre, to avoid triangle edge artifact in centre of image.
		testPixel = self.__colorAtUV( image, imath.V2f( 0.55 ) )
		self.assertEqual( testPixel.r, 1 )
		self.assertEqual( testPixel.g, 0.5 )
		self.assertEqual( testPixel.b, 0.25 )

		del plane

	def testQuadLightColorTexture( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create( "Cycles" )

		renderer.output(
			"testOutput",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ImageDisplayDriver",
					"handle" : "testQuadLightColorTexture",
				}
			)
		)

		plane = renderer.object(
			"/plane",
			IECoreScene.MeshPrimitive.createPlane(
				imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ),
			),
			renderer.attributes( IECore.CompoundObject ( {
				"cycles:surface" : IECoreScene.ShaderNetwork(
					shaders = {
						"output" : IECoreScene.Shader( "principled_bsdf", "cycles:surface" )
					},
					output = "output",
				)
			} ) )
		)
		plane.transform( imath.M44f().translate( imath.V3f( 0, 0, -1 ) ) )

		# Pure red light, with the colour being provided by an input shader, _not_
		# a direct parameter value. This requires some translation in the renderer backend.

		light = renderer.light(
			"/light",
			None,
			renderer.attributes( IECore.CompoundObject ( {
				"cycles:light" : IECoreScene.ShaderNetwork(
					shaders = {
						"output" : IECoreScene.Shader( "quad_light", "cycles:light", { "exposure" : 5.0 } ),
						"color" : IECoreScene.Shader( "color", "cycles:shader", { "value" : imath.Color3f( 1, 0, 0 ) } ),
					},
					connections = [
						( "color", ( "output", "color" ) )
					],
					output = "output",
				),
			} ) )
		)

		renderer.render()

		# Check that we have a pure red image.

		image = IECoreImage.ImageDisplayDriver.storedImage( "testQuadLightColorTexture" )
		self.assertTrue( isinstance( image, IECoreImage.ImagePrimitive ) )

		# Slightly off-centre, to avoid triangle edge artifact in centre of image.
		testPixel = self.__colorAtUV( image, imath.V2f( 0.55 ) )
		self.assertGreater( testPixel.r, 0 )
		self.assertEqual( testPixel.g, 0 )
		self.assertEqual( testPixel.b, 0 )

		del plane, light

	def testRecycleLightGroups( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Cycles",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Interactive,
		)

		renderer.output(
			"testOutput",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ImageDisplayDriver",
					"handle" : "testRecycleLightGroups",
				}
			)
		)

		plane = renderer.object(
			"/plane",
			IECoreScene.MeshPrimitive.createPlane(
				imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ),
			),
			renderer.attributes( IECore.CompoundObject ( {
				"cycles:surface" : IECoreScene.ShaderNetwork(
					shaders = {
						"output" : IECoreScene.Shader( "principled_bsdf", "cycles:surface" )
					},
					output = "output",
				)
			} ) )
		)
		plane.transform( imath.M44f().translate( imath.V3f( 0, 0, -1 ) ) )

		# Cycles only has 64 distinct light groups, so if more than 64 unique
		# sets of light links are used, we can't translate the scene accurately.
		# So for interactive use, we need to be careful to recycle old light
		# groups to make way for new ones. Here we make 200 unique light sets,
		# but with only a single one in use at the end, to check that the
		# recycling works.

		for i in range( 0, 200 ) :

			redLight = renderer.light(
				"/redLight",
				None,
				renderer.attributes( IECore.CompoundObject ( {
					"cycles:light" : IECoreScene.ShaderNetwork(
						shaders = {
							"output" : IECoreScene.Shader( "distant_light", "cycles:light", { "color" : imath.Color3f( 1, 0, 0 ) } ),
						},
						output = "output",
					),
				} ) )
			)

			greenLight = renderer.light(
				"/redLight",
				None,
				renderer.attributes( IECore.CompoundObject ( {
					"cycles:light" : IECoreScene.ShaderNetwork(
						shaders = {
							"output" : IECoreScene.Shader( "distant_light", "cycles:light", { "color" : imath.Color3f( 0, 1, 0 ) } ),
						},
						output = "output",
					),
				} ) )
			)

			plane.link( "lights", { redLight } )

		# Render, and check that we have a pure red image. If green has crept in,
		# then we know the light linking was broken.

		renderer.render()
		time.sleep( 1 )

		image = IECoreImage.ImageDisplayDriver.storedImage( "testRecycleLightGroups" )
		self.assertTrue( isinstance( image, IECoreImage.ImagePrimitive ) )

		# Slightly off-centre, to avoid triangle edge artifact in centre of image.
		testPixel = self.__colorAtUV( image, imath.V2f( 0.55 ) )
		self.assertGreater( testPixel.r, 0 )
		self.assertEqual( testPixel.g, 0 )
		self.assertEqual( testPixel.b, 0 )

		del plane, redLight, greenLight

	def testLightWithoutAttribute( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create( "Cycles" )

		# Light destined for another renderer - we want to ignore this, and not crash.

		light = renderer.light(
			"/light",
			None,
			renderer.attributes( IECore.CompoundObject ( {
				"ai:light" : IECoreScene.ShaderNetwork(
					shaders = {
						"output" : IECoreScene.Shader( "quad_light", "ai:light" ),
					},
					output = "output",
				),
			} ) )
		)
		light.transform( imath.M44f().rotate( imath.V3f( 0, math.pi, 0 ) ) )

	def testBackgroundLightWithoutTexture( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create( "Cycles" )

		renderer.output(
			"testOutput",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ImageDisplayDriver",
					"handle" : "testBackgroundLightWithoutTexture",
				}
			)
		)

		plane = renderer.object(
			"/plane",
			IECoreScene.MeshPrimitive.createPlane(
				imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ),
			),
			renderer.attributes( IECore.CompoundObject ( {
				"cycles:surface" : IECoreScene.ShaderNetwork(
					shaders = {
						"output" : IECoreScene.Shader( "principled_bsdf", "cycles:surface" )
					},
					output = "output",
				)
			} ) )
		)
		plane.transform( imath.M44f().translate( imath.V3f( 0, 0, -1 ) ) )

		# Pure red light, with the colour being provided by a parameter value,
		# not an input connection. This requires workarounds for the fact that
		# Cycles will ignore the light's strength unless a texture is connected.

		light = renderer.light(
			"/light",
			None,
			renderer.attributes( IECore.CompoundObject ( {
				"cycles:light" : IECoreScene.ShaderNetwork(
					shaders = {
						"output" : IECoreScene.Shader( "background_light", "cycles:light", { "color" : imath.Color3f( 1, 0, 0 ) } ),
					},
					output = "output",
				),
			} ) )
		)
		light.transform( imath.M44f().rotate( imath.V3f( 0, math.pi, 0 ) ) )

		renderer.render()

		# Check that we have a pure red image.

		image = IECoreImage.ImageDisplayDriver.storedImage( "testBackgroundLightWithoutTexture" )
		self.assertTrue( isinstance( image, IECoreImage.ImagePrimitive ) )

		middlePixel = self.__colorAtUV( image, imath.V2f( 0.5 ) )
		self.assertGreater( middlePixel.r, 0 )
		self.assertEqual( middlePixel.g, 0 )
		self.assertEqual( middlePixel.b, 0 )

		del plane

	def testCrashWhenNoBackgroundLight( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create( "Cycles" )

		renderer.option( "cycles:shadingsystem", IECore.StringData( "SVM" ) )

		renderer.output(
			"testOutput",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ImageDisplayDriver",
					"handle" : "testCrashWhenNoBackgroundLight",
				}
			)
		)

		# This used to crash. If it doesn't crash now, then we are happy.
		renderer.render()

	def testBackgroundLightBatchRender( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create( "Cycles" )

		fileName = self.temporaryDirectory() / "test.exr"
		renderer.output(
			"testOutput",
			IECoreScene.Output(
				str( fileName ),
				"exr",
				"rgba",
				{}
			)
		)

		# Set an option that requires a re-created cycles session before rendering starts
		renderer.option( "cycles:session:use_auto_tile", IECore.BoolData( False ) )

		plane = renderer.object(
			"/plane",
			IECoreScene.MeshPrimitive.createPlane(
				imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ),
			),
			renderer.attributes( IECore.CompoundObject ( {
				"cycles:surface" : IECoreScene.ShaderNetwork(
					shaders = {
						"output" : IECoreScene.Shader( "principled_bsdf", "cycles:surface", { "base_color" : imath.Color3f( 1, 1, 1 ) } ),
					},
					output = "output",
				)
			} ) )
		)
		plane.transform( imath.M44f().translate( imath.V3f( 0, 0, -1 ) ) )

		light = renderer.light(
			"/light",
			None,
			renderer.attributes( IECore.CompoundObject ( {
				"cycles:light" : IECoreScene.ShaderNetwork(
					shaders = {
						"output" : IECoreScene.Shader( "background_light", "cycles:light", { "color" : imath.Color3f( 1, 0, 0 ) } ),
					},
					output = "output",
				),
			} ) )
		)
		light.transform( imath.M44f().rotate( imath.V3f( 0, math.pi, 0 ) ) )

		renderer.render()

		# Check that we have a pure red image.

		image = IECore.Reader.create( str( fileName ) ).read()

		middlePixel = self.__colorAtUV( image, imath.V2f( 0.5 ) )
		self.assertGreater( middlePixel.r, 0 )
		self.assertEqual( middlePixel.g, 0 )
		self.assertEqual( middlePixel.b, 0 )

		del plane

	def testBackgroundLightEdits( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Cycles",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Interactive,
		)

		renderer.output(
			"testOutput",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ImageDisplayDriver",
					"handle" : "testBackgroundLightEdits",
				}
			)
		)

		plane = renderer.object(
			"/plane",
			IECoreScene.MeshPrimitive.createPlane(
				imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ),
			),
			renderer.attributes( IECore.CompoundObject ( {
				"cycles:surface" : IECoreScene.ShaderNetwork(
					shaders = {
						"output" : IECoreScene.Shader( "principled_bsdf", "cycles:surface" )
					},
					output = "output",
				)
			} ) )
		)
		plane.transform( imath.M44f().translate( imath.V3f( 0, 0, -1 ) ) )

		def lightAttributes( color ) :

			return renderer.attributes( IECore.CompoundObject ( {
				"cycles:light" : IECoreScene.ShaderNetwork(
					shaders = {
						"output" : IECoreScene.Shader( "background_light", "cycles:light", { "color" : color } ),
					},
					output = "output",
				),
			} ) )

		# Render with a red light.

		light = renderer.light( "/light", None, lightAttributes( imath.Color3f( 1, 0, 0 ) ) )
		renderer.render()
		time.sleep( 1 )

		# Check that we have a pure red image.

		image = IECoreImage.ImageDisplayDriver.storedImage( "testBackgroundLightEdits" )
		self.assertTrue( isinstance( image, IECoreImage.ImagePrimitive ) )

		middlePixel = self.__colorAtUV( image, imath.V2f( 0.5 ) )
		self.assertGreater( middlePixel.r, 0 )
		self.assertEqual( middlePixel.g, 0 )
		self.assertEqual( middlePixel.b, 0 )

		# Rerender with a green light.

		renderer.pause()
		light.attributes( lightAttributes( imath.Color3f( 0, 1, 0 ) ) )
		renderer.render()
		time.sleep( 1 )

		# Check that we have a pure green image.

		image = IECoreImage.ImageDisplayDriver.storedImage( "testBackgroundLightEdits" )
		middlePixel = self.__colorAtUV( image, imath.V2f( 0.5 ) )
		self.assertEqual( middlePixel.r, 0 )
		self.assertGreater( middlePixel.g, 0 )
		self.assertEqual( middlePixel.b, 0 )

		# Rerender with a blue light.

		renderer.pause()
		light.attributes( lightAttributes( imath.Color3f( 0, 0, 1 ) ) )
		renderer.render()
		time.sleep( 1 )

		# Check that we have a pure blue image.

		image = IECoreImage.ImageDisplayDriver.storedImage( "testBackgroundLightEdits" )
		middlePixel = self.__colorAtUV( image, imath.V2f( 0.5 ) )
		self.assertEqual( middlePixel.r, 0 )
		self.assertEqual( middlePixel.g, 0 )
		self.assertGreater( middlePixel.b, 0 )

		# Rerender without the light.

		renderer.pause()
		del light
		renderer.render()
		time.sleep( 1 )

		# Check that we have a pure black image.

		image = IECoreImage.ImageDisplayDriver.storedImage( "testBackgroundLightEdits" )
		self.assertEqual( self.__colorAtUV( image, imath.V2f( 0.55 ) ), imath.Color4f( 0, 0, 0, 1 ) )

		renderer.pause()
		del plane

	def testBackgroundShader( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Cycles",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Interactive,
		)

		renderer.output(
			"testOutput",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ImageDisplayDriver",
					"handle" : "testBackgroundShader",
				}
			)
		)

		plane = renderer.object(
			"/plane",
			IECoreScene.MeshPrimitive.createPlane(
				imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ),
			),
			renderer.attributes( IECore.CompoundObject ( {
				"cycles:surface" : IECoreScene.ShaderNetwork(
					shaders = {
						"output" : IECoreScene.Shader( "principled_bsdf", "cycles:surface" )
					},
					output = "output",
				)
			} ) )
		)
		plane.transform( imath.M44f().translate( imath.V3f( 0, 0, -1 ) ) )

		def backgroundShader( color ) :

			return IECoreScene.ShaderNetwork(
				shaders = {
					"output" : IECoreScene.Shader( "checker_texture", "cycles:shader", { "color1" : color, "color2" : color } ),
				},
				output = "output",
			)

		# Render with no background, and check we have a black image.

		renderer.render()
		time.sleep( 1 )

		image = IECoreImage.ImageDisplayDriver.storedImage( "testBackgroundShader" )
		self.assertTrue( isinstance( image, IECoreImage.ImagePrimitive ) )
		self.assertEqual( self.__colorAtUV( image, imath.V2f( 0.55 ) ), imath.Color4f( 0, 0, 0, 1 ) )

		# Render with a red background.

		renderer.pause()
		renderer.option( "cycles:background:shader", backgroundShader( imath.Color3f( 1, 0, 0 ) ) )
		renderer.render()
		time.sleep( 1 )

		# Check that we have a pure red image.

		image = IECoreImage.ImageDisplayDriver.storedImage( "testBackgroundShader" )
		self.assertTrue( isinstance( image, IECoreImage.ImagePrimitive ) )

		middlePixel = self.__colorAtUV( image, imath.V2f( 0.5 ) )
		self.assertGreater( middlePixel.r, 0 )
		self.assertEqual( middlePixel.g, 0 )
		self.assertEqual( middlePixel.b, 0 )

		# Render with a green background.

		renderer.pause()
		renderer.option( "cycles:background:shader", backgroundShader( imath.Color3f( 0, 1, 0 ) ) )
		renderer.render()
		time.sleep( 1 )

		# Check that we have a pure green image.

		image = IECoreImage.ImageDisplayDriver.storedImage( "testBackgroundShader" )
		self.assertTrue( isinstance( image, IECoreImage.ImagePrimitive ) )

		middlePixel = self.__colorAtUV( image, imath.V2f( 0.5 ) )
		self.assertEqual( middlePixel.r, 0 )
		self.assertGreater( middlePixel.g, 0 )
		self.assertEqual( middlePixel.b, 0 )

		# Render with a red background again.

		renderer.pause()
		renderer.option( "cycles:background:shader", backgroundShader( imath.Color3f( 1, 0, 0 ) ) )
		renderer.render()
		time.sleep( 1 )

		# Check that we have gone back to a pure red image.

		image = IECoreImage.ImageDisplayDriver.storedImage( "testBackgroundShader" )
		self.assertTrue( isinstance( image, IECoreImage.ImagePrimitive ) )

		middlePixel = self.__colorAtUV( image, imath.V2f( 0.5 ) )
		self.assertGreater( middlePixel.r, 0 )
		self.assertEqual( middlePixel.g, 0 )
		self.assertEqual( middlePixel.b, 0 )

		# Remove background, and check we have a black image.

		renderer.pause()
		renderer.option( "cycles:background:shader", None )
		renderer.render()
		time.sleep( 1 )

		image = IECoreImage.ImageDisplayDriver.storedImage( "testBackgroundShader" )
		self.assertTrue( isinstance( image, IECoreImage.ImagePrimitive ) )
		self.assertEqual( self.__colorAtUV( image, imath.V2f( 0.55 ) ), imath.Color4f( 0, 0, 0, 1 ) )

		del plane

	def testMultipleOutputs( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create( "Cycles" )

		renderer.output(
			"testOutput:beauty",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ImageDisplayDriver",
					"handle" : "testMultipleOutputs:beauty",
				}
			)
		)

		renderer.output(
			"testOutput:normal",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"normal",
				{
					"driverType" : "ImageDisplayDriver",
					"handle" : "testMultipleOutputs:normal",
				}
			)
		)

		renderer.render()

		beauty = IECoreImage.ImageDisplayDriver.storedImage( "testMultipleOutputs:beauty" )
		self.assertTrue( isinstance( beauty, IECoreImage.ImagePrimitive ) )

		normal = IECoreImage.ImageDisplayDriver.storedImage( "testMultipleOutputs:normal" )
		self.assertTrue( isinstance( normal, IECoreImage.ImagePrimitive ) )

	def testCommand( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Cycles",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Interactive,
		)

		# Unknown commands that claim to be for Cycles should emit a warning.

		with IECore.CapturingMessageHandler() as mh :
			self.assertIsNone( renderer.command( "cycles:thisCommandDoesNotExist", {} ) )

		self.assertEqual( len( mh.messages ), 1 )
		self.assertEqual( mh.messages[0].level, IECore.MessageHandler.Level.Warning )
		self.assertEqual( mh.messages[0].context, "CyclesRenderer::command" )
		self.assertEqual( mh.messages[0].message, 'Unknown command "cycles:thisCommandDoesNotExist"' )

		# Unknown commands without a renderer prefix should also emit a warning.

		with IECore.CapturingMessageHandler() as mh :
			self.assertIsNone( renderer.command( "thisCommandDoesNotExist", {} ) )

		self.assertEqual( len( mh.messages ), 1 )
		self.assertEqual( mh.messages[0].level, IECore.MessageHandler.Level.Warning )
		self.assertEqual( mh.messages[0].context, "CyclesRenderer::command" )
		self.assertEqual( mh.messages[0].message, 'Unknown command "thisCommandDoesNotExist"' )

		# Unknown commands for some other renderer should be silently ignored.

		with IECore.CapturingMessageHandler() as mh :
			self.assertIsNone( renderer.command( "gl:renderToCurrentContext", {} ) )

		self.assertEqual( len( mh.messages ), 0 )

	def testUnconvertibleObject( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Cycles",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Interactive,
		)

		# We don't expect renderers other than OpenGL to have any support
		# for the Placeholder object. Here we're just checking that the Cycles
		# renderer doesn't crash if given a placeholder.

		o = renderer.object(
			"/test",
			GafferScene.Private.IECoreScenePreview.Placeholder(),
			renderer.attributes( IECore.CompoundObject ( {} ) )
		)

		del o

		# Likewise for CoordinateSystems and NullObjects.

		o = renderer.object(
			"/coordinateSystem",
			IECoreScene.CoordinateSystem(),
			renderer.attributes( IECore.CompoundObject ( {} ) )
		)
		del o

		o = renderer.object(
			"/nullObject",
			IECore.NullObject.defaultNullObject(),
			renderer.attributes( IECore.CompoundObject ( {} ) )
		)
		del o

	def testCameraAttributeEdits( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Cycles",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Interactive
		)

		camera = renderer.camera( "test", IECoreScene.Camera() )

		# Edit should succeed.
		self.assertTrue( camera.attributes(
			renderer.attributes( IECore.CompoundObject( { "user:test" : IECore.IntData( 10 ) } ) )
		) )

		del camera

	def testDisplayDriverCropWindow( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create( "Cycles" )

		renderer.camera(
			"testCamera",
			IECoreScene.Camera(
				parameters = {
					"resolution" : imath.V2i( 2000, 1000 ),
					"cropWindow" : imath.Box2f( imath.V2f( 0.25 ), imath.V2f( 0.75 ) ),
				}
			)
		)

		renderer.output(
			"testOutput",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					# This driver type will throw if it receives tiles
					# outside the data window.
					"driverType" : "ImageDisplayDriver",
					"handle" : "testCropWindow",
				}
			)
		)

		renderer.option( "camera", IECore.StringData( "testCamera" ) )
		renderer.render()
		del renderer

		image = IECoreImage.ImageDisplayDriver.storedImage( "testCropWindow" )
		self.assertIsNotNone( image )
		self.assertEqual( image.dataWindow, imath.Box2i( imath.V2i( 500, 250 ), imath.V2i( 1499, 749 ) ) )
		self.assertEqual( image.displayWindow, imath.Box2i( imath.V2i( 0 ), imath.V2i( 1999, 999 ) ) )

	def testOutputFileCropWindow( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create( "Cycles" )

		renderer.camera(
			"testCamera",
			IECoreScene.Camera(
				parameters = {
					"resolution" : imath.V2i( 2000, 1000 ),
					"cropWindow" : imath.Box2f( imath.V2f( 0.25 ), imath.V2f( 0.75 ) ),
				}
			)
		)

		fileName = self.temporaryDirectory() / "test.exr"
		renderer.output(
			"testOutput",
			IECoreScene.Output(
				str( fileName ),
				"exr",
				"rgba",
				{}
			)
		)

		renderer.option( "camera", IECore.StringData( "testCamera" ) )
		renderer.render()

		image = IECoreImage.ImageReader( str( fileName ) ).read()
		self.assertEqual( image.dataWindow, imath.Box2i( imath.V2i( 500, 250 ), imath.V2i( 1499, 749 ) ) )
		self.assertEqual( image.displayWindow, imath.Box2i( imath.V2i( 0 ), imath.V2i( 1999, 999 ) ) )

	def testPointsWithNormals( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create( "Cycles" )

		renderer.output(
			"pointsWithNormals",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ImageDisplayDriver",
					"handle" : "pointsWithNormals",
				}
			)
		)

		# Render a point with a custom normal.

		points = IECoreScene.PointsPrimitive(
			IECore.V3fVectorData( [ imath.V3f( 0 ) ] )
		)
		points["N"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.V3fVectorData(
				[ imath.V3f( 1, 0.5, 0.25 ) ],
				IECore.GeometricData.Interpretation.Normal
			)
		)

		pointsObject = renderer.object(
			"/pointsWithNormals",
			points,
			renderer.attributes( IECore.CompoundObject ( {
				"cycles:surface" : IECoreScene.ShaderNetwork(
					shaders = {
						"output" : IECoreScene.Shader( "principled_bsdf", "cycles:surface", { "emission_strength" : 1 } ),
						"attribute" : IECoreScene.Shader( "attribute", "cycles:shader", { "attribute" : "N" } ),
					},
					connections = [
						( ( "attribute", "color" ), ( "output", "emission_color" ) ),
					],
					output = "output",
				)
			} ) )
		)
		pointsObject.transform( imath.M44f().translate( imath.V3f( 0, 0, -2 ) ) )

		renderer.render()

		del pointsObject
		del renderer

		# Check that the shader was able to read the normal.

		image = IECoreImage.ImageDisplayDriver.storedImage( "pointsWithNormals" )
		self.assertTrue( isinstance( image, IECoreImage.ImagePrimitive ) )

		color = self.__colorAtUV( image, imath.V2f( 0.5 ) )
		self.assertEqual( color.r, points["N"].data[0].x )
		self.assertEqual( color.g, points["N"].data[0].y )
		self.assertEqual( color.b, points["N"].data[0].z )

	def __testMeshSmoothing( self, cube, smoothingExpected ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create( "Cycles" )

		renderer.output(
			"meshSmoothing",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ImageDisplayDriver",
					"handle" : "meshSmoothing",
				}
			)
		)

		# Render the cube, rotated so an edge faces the camera, shaded with the
		# standard facing-ratio shader.

		cubeObject = renderer.object( "/cube", cube, renderer.attributes( IECore.CompoundObject() ) )
		cubeObject.transform( imath.M44f().translate( imath.V3f( 0, 0, -2 ) ).rotate( imath.V3f( 0, math.pi / 4.0, 0 ) ) )

		renderer.render()

		del cubeObject
		del renderer

		# Check the shading on the center edge, and close to the back left and right edges.
		# If normals have been smoothed, then the back edges should be close to zero.

		image = IECoreImage.ImageDisplayDriver.storedImage( "meshSmoothing" )
		self.assertTrue( isinstance( image, IECoreImage.ImagePrimitive ) )

		center = self.__colorAtUV( image, imath.V2f( 0.5, 0.5 ) )
		left = self.__colorAtUV( image, imath.V2f( 0.15, 0.5 ) )
		right = self.__colorAtUV( image, imath.V2f( 0.85, 0.5 ) )

		# Everything should have solid alpha.

		self.assertEqual( center[3], 1 )
		self.assertEqual( left[3], 1 )
		self.assertEqual( right[3], 1 )

		# Shading is down to whether the normals are smoothed or not.

		if smoothingExpected :
			# Center normal faces straight at us
			self.assertGreater( center[0], 0.95 )
			# Outer normals are close to perpendicular.
			self.assertLess( left[0], 0.015 )
			self.assertLess( right[0], 0.015 )
		else :
			# Everything faces towards and to the side of us.
			self.assertGreater( center[0], 0.4 )
			self.assertGreater( left[0], 0.4 )
			self.assertGreater( right[0], 0.4 )

	def testNoMeshNormals( self ) :

		cube = IECoreScene.MeshPrimitive.createBox( imath.Box3f( imath.V3f( -0.5 ), imath.V3f( 0.5 ) ) )
		del cube["N"]
		self.__testMeshSmoothing( cube, smoothingExpected = False )

	def testFaceVaryingMeshNormals( self ) :

		# These are treated like non-existent normals, since Cycles doesn't support them.
		cube = IECoreScene.MeshPrimitive.createBox( imath.Box3f( imath.V3f( -0.5 ), imath.V3f( 0.5 ) ) )
		self.__testMeshSmoothing( cube, smoothingExpected = False )

	def testVertexMeshNormals( self ) :

		cube = IECoreScene.MeshPrimitive.createBox( imath.Box3f( imath.V3f( -0.5 ), imath.V3f( 0.5 ) ) )
		cube["N"] = IECoreScene.MeshAlgo.calculateVertexNormals( cube, IECoreScene.MeshAlgo.NormalWeighting.Equal )
		self.__testMeshSmoothing( cube, smoothingExpected = True )

	def testUnsupportedPrimitiveVariables( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create( "Cycles" )
		attributes = renderer.attributes( IECore.CompoundObject() )

		primitive = IECoreScene.PointsPrimitive( IECore.V3fVectorData( [ imath.V3f( 0 ) ] ) )

		for data in [
			IECore.StringData(),
			IECore.StringVectorData(),
			IECore.Box3fData(),
			IECore.Box3fVectorData()
		] :

			primitive = primitive.copy()
			primitive["test"] = IECoreScene.PrimitiveVariable(
				IECoreScene.PrimitiveVariable.Interpolation.Constant, data
			)

			with IECore.CapturingMessageHandler() as mh :

				renderer.object( data.typeName(), primitive, attributes )

				self.assertEqual( len( mh.messages ), 1 )
				self.assertRegex(
					mh.messages[0].message,
					"Primitive variable \"test\" has unsupported type \"{}\"".format( data.typeName() )
				)

	def __testPrimitiveVariableInterpolation( self, primitive, primitiveVariable, expectedPixels, maxDifference = 0.0, attributeName = None ) :

		attributeName = primitiveVariable if attributeName is None else attributeName

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create( "Cycles" )

		# Frame the primitive so it fills the entire image.

		renderer.camera(
			"testCamera",
			IECoreScene.Camera(
				parameters = {
					"resolution" : imath.V2i( 100, 100 ),
					"projection" : "orthographic",
					"screenWindow" : imath.Box2f( imath.V2f( -0.5 ), imath.V2f( 0.5 ) )
				}
			)
		)
		renderer.option( "camera", IECore.StringData( "testCamera" ) )

		fileName = self.temporaryDirectory() / "test.exr"
		renderer.output(
			"testOutput",
			IECoreScene.Output(
				str( fileName ),
				"exr",
				"rgba",
				{}
			)
		)

		# Render with a constant shader showing the primitive variable

		shader = IECoreScene.ShaderNetwork(
			shaders = {
				"output" : IECoreScene.Shader( "principled_bsdf", "cycles:surface", { "base_color" : imath.Color3f( 0 ), "emission_strength" : 1 } ),
				"attribute" : IECoreScene.Shader( "attribute", "cycles:shader", { "attribute" : attributeName } ),
			},
			connections = [
				( ( "attribute", "color" ), ( "output", "emission_color" ) ),
			],
			output = "output",
		)

		primitiveHandle = renderer.object( "primitive", primitive, renderer.attributes( IECore.CompoundObject( { "cycles:surface" : shader } ) ) )
		primitiveHandle.transform( imath.M44f().translate( imath.V3f( 0, 0, -1 ) ) )

		renderer.render()

		# Check we got what we expected

		image = IECore.Reader.create( str( fileName ) ).read()

		for uv, expectedColor in expectedPixels.items() :

			if isinstance( expectedColor, imath.V3f ) :
				expectedColor = imath.Color4f( expectedColor[0], expectedColor[1], expectedColor[2], 1 )
			elif isinstance( expectedColor, ( imath.V2f, imath.V2i ) ) :
				expectedColor = imath.Color4f( expectedColor[0], expectedColor[1], 0, 1 )
			elif isinstance( expectedColor, ( int, float ) ) :
				expectedColor = imath.Color4f( expectedColor, expectedColor, expectedColor, 1 )

			color = self.__colorAtUV( image, uv )
			self.assertEqualWithAbsError( color, expectedColor, maxDifference )

	def testMeshPrimitiveVariableInterpolation( self ) :

		# Plane with 3x3 faces and primitive variables with various interpolations.

		plane = IECoreScene.MeshPrimitive.createPlane(
			imath.Box2f( imath.V2f( -0.5 ), imath.V2f( 0.5 ) ),
			imath.V2i( 3 )
		)

		plane["constantColor"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Constant,
			IECore.Color3fData( imath.Color3f( 0, 0.5, 1 ) ),
		)

		plane["constantInt"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Constant,
			IECore.IntData( 1 ),
		)

		plane["uniformColor"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Uniform,
			IECore.Color3fVectorData( [
				imath.Color3f( i, i, i )
				for i in range( 0, plane.variableSize( IECoreScene.PrimitiveVariable.Interpolation.Uniform ) )
			] )
		)

		plane["uniformIndexedColor"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Uniform,
			IECore.Color3fVectorData( [ imath.Color3f( 1, 0, 0 ), imath.Color3f( 0, 1, 0 ) ] ),
			IECore.IntVectorData( [
				i % 2
				for i in range( 0, plane.variableSize( IECoreScene.PrimitiveVariable.Interpolation.Uniform ) )
			] )
		)

		plane["vertexColor"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.Color3fVectorData( [
				imath.Color3f( uv.x, uv.y, 0 ) for uv in plane["uv"].data
			] )
		)

		plane["varyingColor"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Varying,
			plane["vertexColor"].data
		)

		# Image UV coordinates of the center of particular faces.

		topLeft = imath.V2f( 1/6.0, 1/6.0 )
		topCenter = imath.V2f( 0.5, 1/6.0 )
		center = imath.V2f( 0.5, 0.5 )
		bottomRight = imath.V2f( 5/6.0 )

		# Tests for each of the primitive variables.

		for interpolation in [ "linear", "catmullClark" ] :

			for triangulate in [ False, True ] :

				if triangulate :
					testPlane = IECoreScene.MeshAlgo.triangulate( plane )
				else :
					testPlane = plane.copy()

				testPlane.setInterpolation( interpolation )

				self.__testPrimitiveVariableInterpolation(
					testPlane, "constantColor",
					{
						topLeft : plane["constantColor"].data.value,
						topCenter : plane["constantColor"].data.value,
						center : plane["constantColor"].data.value,
						bottomRight : plane["constantColor"].data.value,
					}
				)

				self.__testPrimitiveVariableInterpolation(
					testPlane, "constantInt",
					{
						topLeft : plane["constantInt"].data.value,
						topCenter : plane["constantInt"].data.value,
						center : plane["constantInt"].data.value,
						bottomRight : plane["constantInt"].data.value,
					}
				)

				self.__testPrimitiveVariableInterpolation(
					testPlane, "uniformColor",
					{
						topLeft : imath.Color4f( 6, 6, 6, 1 ),
						topCenter : imath.Color4f( 7, 7, 7, 1 ),
						center : imath.Color4f( 4, 4, 4, 1 ),
						bottomRight : imath.Color4f( 2, 2, 2, 1 ),
					}
				)

				self.__testPrimitiveVariableInterpolation(
					testPlane, "uniformIndexedColor",
					{
						topLeft : imath.Color4f( 1, 0, 0, 1 ),
						topCenter : imath.Color4f( 0, 1, 0, 1 ),
						center : imath.Color4f( 1, 0, 0, 1 ),
						bottomRight : imath.Color4f( 1, 0, 0, 1 ),
					}
				)

				self.__testPrimitiveVariableInterpolation(
					testPlane, "vertexColor",
					{
						topLeft : imath.Color4f( topLeft.x, 1.0 - topLeft.y, 0, 1 ),
						topCenter : imath.Color4f( topCenter.x, 1.0 - topCenter.y, 0, 1 ),
						center : imath.Color4f( center.x, 1.0 - center.y, 0, 1 ),
						bottomRight : imath.Color4f( bottomRight.x, 1.0 - bottomRight.y, 0, 1 ),
					},
					maxDifference = 0.01
				)

				self.__testPrimitiveVariableInterpolation(
					testPlane, "varyingColor",
					{
						topLeft : imath.Color4f( topLeft.x, 1.0 - topLeft.y, 0, 1 ),
						topCenter : imath.Color4f( topCenter.x, 1.0 - topCenter.y, 0, 1 ),
						center : imath.Color4f( center.x, 1.0 - center.y, 0, 1 ),
						bottomRight : imath.Color4f( bottomRight.x, 1.0 - bottomRight.y, 0, 1 ),
					},
					maxDifference = 0.01
				)

	def testUniformMeshNormal( self ) :

		plane = IECoreScene.MeshPrimitive.createPlane(
			imath.Box2f( imath.V2f( -0.5 ), imath.V2f( 0.5 ) ),
			imath.V2i( 1 )
		)
		plane["N"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Uniform,
			# Note : not the true geometric normal - actually a tangent.
			# This way we can be sure our data is making it through and
			# not being clobbered by a default normal.
			IECore.V3fVectorData( [ imath.V3f( 1, 0, 0 ) ], IECore.GeometricData.Interpretation.Normal ),
		)

		self.__testPrimitiveVariableInterpolation(
			plane, "N", { imath.V2f( 0.6 ) : plane["N"].data[0] }, attributeName = "Ng"
		)

	def testPointsPrimitiveVariableInterpolation( self ) :

		# 3 points diagonally

		points = IECoreScene.PointsPrimitive(
			IECore.V3fVectorData( [ imath.V3f( -0.5, 0.5, 0 ), imath.V3f( 0 ), imath.V3f( 0.5, -0.5, 0 ) ] )
		)
		points["width"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Constant,
			IECore.FloatData( 0.1 )
		)

		points["uniformColor"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Uniform,
			IECore.Color3fVectorData( [ imath.Color3f( 1, 0.5, 0.25 ) ] )
		)

		points["vertexColor"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.Color3fVectorData( [
				imath.Color3f( p.x + 0.5, p.y + 0.5, 0 ) for p in points["P"].data
			] )
		)

		points["varyingColor"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Varying,
			points["vertexColor"].data
		)

		# Image UV coordinates of each point

		topLeft = imath.V2f( 0, 0 )
		center = imath.V2f( 0.5 )
		bottomRight = imath.V2f( 1, 1 )

		# Tests for each of the primitive variables.

		## \todo Fix and enable. As far as I can tell, we're passing the data
		# to Cycles correctly, but it just doesn't make it through to the shader.
		if False :
			self.__testPrimitiveVariableInterpolation(
				points, "uniformColor",
				{
					topLeft : points["uniformColor"].data[0],
					center : points["uniformColor"].data[0],
					bottomRight : points["uniformColor"].data[0],
				}
			)

		self.__testPrimitiveVariableInterpolation(
			points, "vertexColor",
			{
				topLeft : imath.Color4f( 0, 1, 0, 1 ),
				center : imath.Color4f( 0.5, 0.5, 0, 1 ),
				bottomRight : imath.Color4f( 1, 0, 0, 1 ),
			}
		)

		self.__testPrimitiveVariableInterpolation(
			points, "varyingColor",
			{
				topLeft : imath.Color4f( 0, 1, 0, 1 ),
				center : imath.Color4f( 0.5, 0.5, 0, 1 ),
				bottomRight : imath.Color4f( 1, 0, 0, 1 ),
			}
		)

	def testCurvesPrimitiveVariableInterpolation( self ) :

		# 3 vertical curves

		curves = IECoreScene.CurvesPrimitive(
			verticesPerCurve = IECore.IntVectorData( [ 2, 2, 2 ] ),
			p = IECore.V3fVectorData( [
				imath.V3f( -0.5, 0.5, 0 ), imath.V3f( -0.5, -0.5, 0 ),
				imath.V3f( 0, 0.5, 0 ), imath.V3f( 0, -0.5, 0 ),
				imath.V3f( 0.5, 0.5, 0 ), imath.V3f( 0.5, -0.5, 0 ),
			] )
		)
		curves["width"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Constant,
			IECore.FloatData( 0.1 )
		)

		curves["uniformColor"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Uniform,
			IECore.Color3fVectorData( [ imath.Color3f( i + 1 ) for i in range( 0, 3 ) ] )
		)

		curves["uniformInt"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Uniform,
			IECore.IntVectorData( range( 0, 3 ) )
		)

		curves["uniformV2f"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Uniform,
			IECore.V2fVectorData( [ imath.V2f( i ) for i in range( 0, 3 ) ] )
		)

		curves["uniformV2i"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Uniform,
			IECore.V2iVectorData( [ imath.V2i( i ) for i in range( 0, 3 ) ] )
		)

		curves["vertexColor"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.Color3fVectorData( [
				imath.Color3f( p.x + 0.5, p.y + 0.5, 0 ) for p in curves["P"].data
			] )
		)

		# Image UV coordinates of top and bottom of each curve

		leftTop = imath.V2f( 0, 0 )
		leftBottom = imath.V2f( 0, 1 )
		centerTop = imath.V2f( 0.5, 0 )
		centerBottom = imath.V2f( 0.5, 1 )
		rightTop = imath.V2f(1, 0 )
		rightBottom = imath.V2f( 1, 1 )

		# Tests for each of the primitive variables.

		self.__testPrimitiveVariableInterpolation(
			curves, "uniformColor",
			{
				leftTop : curves["uniformColor"].data[0],
				leftBottom : curves["uniformColor"].data[0],
				centerTop : curves["uniformColor"].data[1],
				centerBottom : curves["uniformColor"].data[1],
				rightTop : curves["uniformColor"].data[2],
				rightBottom : curves["uniformColor"].data[2],
			}
		)

		self.__testPrimitiveVariableInterpolation(
			curves, "uniformInt",
			{
				leftTop : imath.Color3f( 0 ),
				leftBottom : imath.Color3f( 0 ),
				centerTop : imath.Color3f( 1 ),
				centerBottom : imath.Color3f( 1 ),
				rightTop : imath.Color3f( 2 ),
				rightBottom : imath.Color3f( 2 ),
			}
		)

		self.__testPrimitiveVariableInterpolation(
			curves, "uniformV2f",
			{
				leftTop : curves["uniformV2f"].data[0],
				leftBottom : curves["uniformV2f"].data[0],
				centerTop : curves["uniformV2f"].data[1],
				centerBottom : curves["uniformV2f"].data[1],
				rightTop : curves["uniformV2f"].data[2],
				rightBottom : curves["uniformV2f"].data[2],
			}
		)

		self.__testPrimitiveVariableInterpolation(
			curves, "uniformV2i",
			{
				leftTop : curves["uniformV2i"].data[0],
				leftBottom : curves["uniformV2i"].data[0],
				centerTop : curves["uniformV2i"].data[1],
				centerBottom : curves["uniformV2i"].data[1],
				rightTop : curves["uniformV2i"].data[2],
				rightBottom : curves["uniformV2i"].data[2],
			}
		)

		self.__testPrimitiveVariableInterpolation(
			curves, "vertexColor",
			{
				leftTop : imath.Color4f( 0, 1, 0, 1 ),
				leftBottom : imath.Color4f( 0, 0, 0, 1 ),
				centerTop : imath.Color4f( 0.5, 1, 0, 1 ),
				centerBottom : imath.Color4f( 0.5, 0, 0, 1 ),
				rightTop : imath.Color4f( 1, 1, 0, 1 ),
				rightBottom : imath.Color4f( 1, 0, 0, 1 ),
			},
			maxDifference = 0.01
		)

	def testMeshUVs( self ) :

		plane = IECoreScene.MeshPrimitive.createPlane(
			imath.Box2f( imath.V2f( -0.5 ), imath.V2f( 0.5 ) ),
			imath.V2i( 3 )
		)

		# Image UV coordinates of the center of particular faces.

		topLeft = imath.V2f( 1/6.0, 1/6.0 )
		topCenter = imath.V2f( 0.5, 1/6.0 )
		center = imath.V2f( 0.5, 0.5 )
		bottomRight = imath.V2f( 5/6.0 )

		# Test FaceVarying

		self.assertEqual(
			plane["uv"].interpolation, IECoreScene.PrimitiveVariable.Interpolation.FaceVarying
		)

		for interpolation in [ "linear", "catmullClark" ] :

			plane.setInterpolation( interpolation )
			self.__testPrimitiveVariableInterpolation(
				plane, "uv",
				{
					topLeft : imath.Color4f( topLeft.x, 1.0 - topLeft.y, 0, 1 ),
					topCenter : imath.Color4f( topCenter.x, 1.0 - topCenter.y, 0, 1 ),
					center : imath.Color4f( center.x, 1.0 - center.y, 0, 1 ),
					bottomRight : imath.Color4f( bottomRight.x, 1.0 - bottomRight.y, 0, 1 ),
				},
				maxDifference = 0.01
			)

		# Test Vertex

		uv = plane["uv"]
		IECoreScene.MeshAlgo.resamplePrimitiveVariable(
			plane, uv, IECoreScene.PrimitiveVariable.Interpolation.Vertex
		)
		plane["uv"] = uv

		self.assertEqual(
			plane["uv"].interpolation, IECoreScene.PrimitiveVariable.Interpolation.Vertex
		)

		for interpolation in [ "linear", "catmullClark" ] :

			plane.setInterpolation( interpolation )
			self.__testPrimitiveVariableInterpolation(
				plane, "uv",
				{
					topLeft : imath.Color4f( topLeft.x, 1.0 - topLeft.y, 0, 1 ),
					topCenter : imath.Color4f( topCenter.x, 1.0 - topCenter.y, 0, 1 ),
					center : imath.Color4f( center.x, 1.0 - center.y, 0, 1 ),
					bottomRight : imath.Color4f( bottomRight.x, 1.0 - bottomRight.y, 0, 1 ),
				},
				maxDifference = 0.01
			)

	def testShaderSubstitutions( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create( "Cycles" )

		fileName = self.temporaryDirectory() / "test.exr"
		renderer.output(
			"testOutput",
			IECoreScene.Output(
				str( fileName ),
				"exr",
				"rgba",
				{}
			)
		)

		# Render two planes, with the same shader on them both. Each
		# plane has a different value for the `textureFileName` attribute,
		# which should be successfully substituted in to make a unique shader
		# per plane.

		shader = IECoreScene.ShaderNetwork(
			shaders = {
				"output" : IECoreScene.Shader( "principled_bsdf", "cycles:surface", { "emission_strength" : 1 } ),
				"texture" : IECoreScene.Shader( "image_texture", "cycles:shader", { "filename" : "<attr:textureFileName>" } )
			},
			connections = [
				( ( "texture", "color" ), ( "output", "emission_color" ) )
			],
			output = "output",
		)

		for translateX, name, color in [
			( -0.1, "red", imath.Color3f( 1, 0, 0 ) ),
			( 0.1, "green", imath.Color3f( 0, 1, 0 ) ),
		] :

			displayWindow = imath.Box2i( imath.V2i( 0 ), imath.V2i( 16 ) )
			textureImage = IECoreImage.ImagePrimitive.createRGBFloat( color, displayWindow, displayWindow )
			textureFileName = self.temporaryDirectory() / f"{name}.png"
			IECoreImage.ImageWriter( textureImage, str( textureFileName ) ).write()

			plane = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -0.1 ), imath.V2f( 0.1 ) ) )
			# Workaround for #4890
			plane["uniquefier"] = IECoreScene.PrimitiveVariable(
				IECoreScene.PrimitiveVariable.Interpolation.Constant,
				IECore.FloatData( translateX ),
			)

			cyclesPlane = renderer.object(
				"{}Plane".format( name ), plane,
				renderer.attributes( IECore.CompoundObject( {
					"cycles:surface" : shader,
					"textureFileName" : IECore.StringData( textureFileName.as_posix() ),
				} ) )
			)
			cyclesPlane.transform( imath.M44f().translate( imath.V3f( translateX, 0, -1 ) ) )

		renderer.render()
		image = IECore.Reader.create( str( fileName ) ).read()

		self.assertEqual( self.__colorAtUV( image, imath.V2f( 0.48, 0.5 ) ), imath.Color4f( 1, 0, 0, 1 ) )
		self.assertEqual( self.__colorAtUV( image, imath.V2f( 0.52, 0.5 ) ), imath.Color4f( 0, 1, 0, 1 ) )

	def __colorAtUV( self, image, uv, channelName = "" ) :

		dimensions = image.dataWindow.size() + imath.V2i( 1 )

		ix = int( uv.x * ( dimensions.x - 1 ) )
		iy = int( uv.y * ( dimensions.y - 1 ) )
		i = iy * dimensions.x + ix

		c = channelName
		if c != "":
			c = "%s." % channelName

		return imath.Color4f( image[c+"R"][i], image[c+"G"][i], image[c+"B"][i], image[c+"A"][i] if c+"A" in image.keys() else 0.0 )

	def __testCustomAttributeType( self, primitive, prefix, customAttribute, outputPlug, data, expectedResult, maxDifference = 0.0 ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create( "Cycles" )

		# Frame the primitive so it fills the entire image.

		renderer.camera(
			"testCamera",
			IECoreScene.Camera(
				parameters = {
					"resolution" : imath.V2i( 100, 100 ),
					"projection" : "orthographic",
					"screenWindow" : imath.Box2f( imath.V2f( -0.5 ), imath.V2f( 0.5 ) )
				}
			)
		)
		renderer.option( "camera", IECore.StringData( "testCamera" ) )

		fileName = self.temporaryDirectory() / "test.exr"
		renderer.output(
			"testOutput",
			IECoreScene.Output(
				str( fileName ),
				"exr",
				"rgba",
				{}
			)
		)

		# Render with a constant shader showing the custom attribute

		attribute = customAttribute
		if prefix != "render:" :
			attribute = prefix + attribute

		shader = IECoreScene.ShaderNetwork(
			shaders = {
				"output" : IECoreScene.Shader( "principled_bsdf", "cycles:surface", { "base_color" : imath.Color3f( 0 ), "emission_strength" : 1 } ),
				"attribute" : IECoreScene.Shader( "attribute", "cycles:shader", { "attribute" : attribute } ),
			},
			connections = [
				( ( "attribute", outputPlug ), ( "output", "emission_color" ) ),
				( ( "attribute", "alpha" ), ( "output", "alpha" ) )
			],
			output = "output",
		)

		primitiveHandle = renderer.object( "/primitive", primitive, renderer.attributes( IECore.CompoundObject( { prefix + customAttribute : data, "cycles:surface" : shader } ) ) )
		primitiveHandle.transform( imath.M44f().translate( imath.V3f( 0, 0, -1 ) ) )

		renderer.render()
		image = IECore.Reader.create( str( fileName ) ).read()

		self.assertEqualWithAbsError( self.__colorAtUV( image, imath.V2f( 0.55 ) ), expectedResult, maxDifference )

	def testCustomAttributes( self ) :

		testData = [
			{ "name" : "testBool", "outputPlug" : "fac", "data" : IECore.BoolData( True ), "expectedResult" : imath.Color4f( 1, 1, 1, 1 ), "maxDifference" : 0.0 },
			{ "name" : "testInt", "outputPlug" : "fac", "data" : IECore.IntData( 7 ), "expectedResult" : imath.Color4f( 7, 7, 7, 1 ), "maxDifference" : 0.0 },
			{ "name" : "testFloat", "outputPlug" : "fac", "data" : IECore.FloatData( 2.5 ), "expectedResult" : imath.Color4f( 2.5, 2.5, 2.5, 1 ), "maxDifference" : 0.0 },
			{ "name" : "testV2f", "outputPlug" : "vector", "data" : IECore.V2fData( imath.V2f( 1, 2 ) ), "expectedResult" : imath.Color4f( 1, 2, 0, 1 ), "maxDifference" : 0.0 },
			{ "name" : "testV3f", "outputPlug" : "vector", "data" : IECore.V3fData( imath.V3f( 1, 2, 3 ) ), "expectedResult" : imath.Color4f( 1, 2, 3, 1 ), "maxDifference" : 0.0 },
			{ "name" : "testColor3f", "outputPlug" : "color", "data" : IECore.Color3fData( imath.Color3f( 4, 5, 6 ) ), "expectedResult" : imath.Color4f( 4, 5, 6, 1 ), "maxDifference" : 0.0 },
			{ "name" : "testColor4f", "outputPlug" : "color", "data" : IECore.Color4fData( imath.Color4f( 7, 8, 9, 0.5 ) ), "expectedResult" : imath.Color4f( 3.5, 4, 4.5, 0.5 ), "maxDifference" : 0.01 },
		]

		plane = IECoreScene.MeshPrimitive.createPlane(
			imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ),
			imath.V2i( 1 )
		)

		for attribute in testData:
			for prefix in [ "user:", "render:" ] :
				self.__testCustomAttributeType(
					plane, prefix, attribute["name"], attribute['outputPlug'], attribute["data"], attribute["expectedResult"], attribute["maxDifference"]
				)

	def testCustomAttributePrecedence( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create( "Cycles" )

		renderer.output(
			"testOutput",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ImageDisplayDriver",
					"handle" : "testCustomAttributePrecedence",
				}
			)
		)

		plane = renderer.object(
			"/plane",
			IECoreScene.MeshPrimitive.createPlane(
				imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ),
			),
			renderer.attributes( IECore.CompoundObject ( {
				"user:testColor" : IECore.Color3fData( imath.Color3f( 1, 0, 0 ) ),
				"render:user:testColor" : IECore.Color3fData( imath.Color3f( 0, 1, 0 ) ),
				"cycles:surface" : IECoreScene.ShaderNetwork(
					shaders = {
						"output" : IECoreScene.Shader( "principled_bsdf", "cycles:surface", { "base_color" : imath.Color3f( 0 ), "emission_strength" : 1 } ),
						"attribute" : IECoreScene.Shader( "attribute", "cycles:shader", { "attribute" : "user:testColor" } ),
					},
					connections = [
						( ( "attribute", "color" ), ( "output", "emission_color" ) )
					],
					output = "output",
				)
			} ) )
		)

		plane.transform( imath.M44f().translate( imath.V3f( 0, 0, -1 ) ) )

		renderer.render()

		image = IECoreImage.ImageDisplayDriver.storedImage( "testCustomAttributePrecedence" )
		self.assertIsInstance( image, IECoreImage.ImagePrimitive )

		self.assertEqual( self.__colorAtUV( image, imath.V2f( 0.55 ) ), imath.Color4f( 0, 1, 0, 1 ) )

		del plane

	def testMissingOSLShader( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Cycles",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Interactive,
		)

		with IECore.CapturingMessageHandler() as mh :

			renderer.attributes( IECore.CompoundObject ( {
				"cycles:surface" : IECoreScene.ShaderNetwork(
					shaders = {
						"output" : IECoreScene.Shader( "NonExistentShader", "osl:surface" ),
					},
					output = "output",
				)
			} ) )

		self.assertEqual( len( mh.messages ), 1 )
		self.assertEqual( mh.messages[0].message, "Couldn't load shader \"NonExistentShader\"" )

	def testMissingCyclesShader( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Cycles",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Interactive,
		)

		with IECore.CapturingMessageHandler() as mh :

			renderer.attributes( IECore.CompoundObject ( {
				"cycles:surface" : IECoreScene.ShaderNetwork(
					shaders = {
						"output" : IECoreScene.Shader( "NonExistentShader", "cycles:surface" ),
					},
					output = "output",
				)
			} ) )

		self.assertEqual( len( mh.messages ), 1 )
		self.assertEqual( mh.messages[0].message, "Couldn't load shader \"NonExistentShader\"" )

	def testMissingShaderParameter( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create( "Cycles" )

		with IECore.CapturingMessageHandler() as mh :
			dodgyNetwork = IECoreScene.ShaderNetwork(
				shaders = {
					"output" : IECoreScene.Shader( "principled_bsdf", "cycles:surface", { "bad_parameter" : 10 } )
				},
				output = "output"
			)
			renderer.attributes( IECore.CompoundObject( { "cycles:surface" : dodgyNetwork } ) )

		self.assertEqual( len( mh.messages ), 1 )
		self.assertEqual( mh.messages[0].context, "Cycles::SocketAlgo" )
		self.assertEqual( mh.messages[0].level, IECore.Msg.Level.Warning )
		self.assertRegex(
			mh.messages[0].message,
			"Socket `bad_parameter` on node .* does not exist"
		)

	def testOSLComponentConnections( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create( "Cycles" )

		renderer.output(
			"testOutput",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ImageDisplayDriver",
					"handle" : "testOSLComponentConnections",
				}
			)
		)

		plane = renderer.object(
			"/plane",
			IECoreScene.MeshPrimitive.createPlane(
				imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ),
			),
			renderer.attributes( IECore.CompoundObject ( {
				"cycles:surface" : IECoreScene.ShaderNetwork(
					shaders = {
						"output" : IECoreScene.Shader( "principled_bsdf", "cycles:surface", { "base_color" : imath.Color3f( 0 ), "emission_strength" : 1 } ),
						"multiplyColor" : IECoreScene.Shader( "Maths/MultiplyColor", "osl:shader", { "b" : imath.Color3f( 0, 0, 0 ) } ),
						"multiplyFloat" : IECoreScene.Shader( "Maths/MultiplyFloat", "osl:shader" ),
					},
					connections = [
						( ( "multiplyFloat", "out" ), ( "multiplyColor", "b.b" ) ),
						( ( "multiplyColor", "out" ), ( "output", "emission_color" ) ),
					],
					output = "output",
				)
			} ) )
		)

		plane.transform( imath.M44f().translate( imath.V3f( 0, 0, -1 ) ) )

		renderer.render()

		image = IECoreImage.ImageDisplayDriver.storedImage( "testOSLComponentConnections" )
		self.assertIsInstance( image, IECoreImage.ImagePrimitive )
		self.assertEqual( self.__colorAtUV( image, imath.V2f( 0.55 ) ), imath.Color4f( 0, 0, 1, 1 ) )

		del plane

	def testSurfaceAttributeWithGenericShaderType( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create( "Cycles" )

		renderer.output(
			"testOutput",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ImageDisplayDriver",
					"handle" : "testSurfaceAttributeWithGenericShaderType",
				}
			)
		)

		plane = renderer.object(
			"/plane",
			IECoreScene.MeshPrimitive.createPlane(
				imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ),
			),
			renderer.attributes( IECore.CompoundObject ( {
				"cycles:surface" : IECoreScene.ShaderNetwork(
					shaders = {
						"output" : IECoreScene.Shader(
							"principled_bsdf", "cycles:shader",
							{ "emission_color" : imath.Color3f( 1, 0, 1 ), "emission_strength" : 1 }
						),
					},
					output = "output",
				)
			} ) )
		)
		plane.transform( imath.M44f().translate( imath.V3f( 0, 0, -1 ) ) )

		renderer.render()

		image = IECoreImage.ImageDisplayDriver.storedImage( "testSurfaceAttributeWithGenericShaderType" )
		self.assertIsInstance( image, IECoreImage.ImagePrimitive )

		# Slightly off-centre, to avoid triangle edge artifact in centre of image.
		testPixel = self.__colorAtUV( image, imath.V2f( 0.55 ) )
		self.assertEqual( testPixel.r, 1 )
		self.assertEqual( testPixel.g, 0 )
		self.assertEqual( testPixel.b, 1 )

		del plane

	def __valueAtUV( self, image, uv, channelName ) :

		dimensions = image.dataWindow.size() + imath.V2i( 1 )

		ix = int( uv.x * ( dimensions.x - 1 ) )
		iy = int( uv.y * ( dimensions.y - 1 ) )
		i = iy * dimensions.x + ix

		return image[channelName][i]

	def testCustomAOV( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create( "Cycles" )

		# Custom AOVs are currently not supported in OSL mode.
		# See https://developer.blender.org/T73266 for further updates
		# for when OSL will eventually support custom AOVs.
		renderer.option( "cycles:shadingsystem", IECore.StringData( "SVM" ) )

		renderer.output(
			"testValueOutput",
			IECoreScene.Output(
				"testValue",
				"ieDisplay",
				"float myValueAOV",
				{
					"driverType" : "ImageDisplayDriver",
					"handle" : "testCustomValueAOV",
				}
			)
		)

		renderer.output(
			"testColorOutput",
			IECoreScene.Output(
				"testColor",
				"ieDisplay",
				"color myColorAOV",
				{
					"driverType" : "ImageDisplayDriver",
					"handle" : "testCustomColorAOV",
				}
			)
		)

		plane = renderer.object(
			"/plane",
			IECoreScene.MeshPrimitive.createPlane(
				imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ),
			),
			renderer.attributes( IECore.CompoundObject ( {
				"cycles:surface" : IECoreScene.ShaderNetwork(
					shaders = {
						"output" : IECoreScene.Shader(
							"principled_bsdf", "cycles:shader",
						),
					},
					output = "output",
				),
				"cycles:aov:myValueAOV" : IECoreScene.ShaderNetwork(
					shaders = {
						"aov_value" : IECoreScene.Shader(
							"aov_output", "cycles:shader",
							{ "name" : "myValueAOV", "value" : 0.5 }
						),
					},
					output = "aov_value",
				),
				"cycles:aov:myColorAOV" : IECoreScene.ShaderNetwork(
					shaders = {
						"aov_color" : IECoreScene.Shader(
							"aov_output", "cycles:shader",
							{ "name" : "myColorAOV", "color" : imath.Color3f( 1, 0, 1 ) }
						),
					},
					output = "aov_color",
				)
			} ) )
		)
		plane.transform( imath.M44f().translate( imath.V3f( 0, 0, -1 ) ) )

		renderer.render()

		image = IECoreImage.ImageDisplayDriver.storedImage( "testCustomValueAOV" )
		self.assertIsInstance( image, IECoreImage.ImagePrimitive )

		# Slightly off-centre, to avoid triangle edge artifact in centre of image.
		testPixel = self.__valueAtUV( image, imath.V2f( 0.55 ), "myValueAOV" )
		self.assertEqual( testPixel, 0.5 )

		image = IECoreImage.ImageDisplayDriver.storedImage( "testCustomColorAOV" )
		self.assertIsInstance( image, IECoreImage.ImagePrimitive )

		# Slightly off-centre, to avoid triangle edge artifact in centre of image.
		testPixel = self.__colorAtUV( image, imath.V2f( 0.55 ), "myColorAOV" )
		self.assertEqual( testPixel.r, 1 )
		self.assertEqual( testPixel.g, 0 )
		self.assertEqual( testPixel.b, 1 )

		del plane

	def __testShaderResults( self, shader, expectedResults, maxDifference = 0.0 ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create( "Cycles" )

		# Frame so our plane fills the entire image.

		renderer.camera(
			"testCamera",
			IECoreScene.Camera(
				parameters = {
					"resolution" : imath.V2i( 100, 100 ),
					"projection" : "orthographic",
					"screenWindow" : imath.Box2f( imath.V2f( -0.5 ), imath.V2f( 0.5 ) )
				}
			)
		)
		renderer.option( "camera", IECore.StringData( "testCamera" ) )

		fileName = self.temporaryDirectory() / "test.exr"
		renderer.output(
			"testOutput",
			IECoreScene.Output(
				str( fileName ),
				"exr",
				"rgba",
				{}
			)
		)

		# Render the plane with the shader provided.

		primitiveHandle = renderer.object(
			"/primitive",
			IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -0.5 ), imath.V2f( 0.5 ) ) ),
			renderer.attributes( IECore.CompoundObject( { "cycles:surface" : shader } ) )
		)
		primitiveHandle.transform( imath.M44f().translate( imath.V3f( 0, 0, -1 ) ) )

		renderer.render()
		image = IECore.Reader.create( str( fileName ) ).read()

		# Check we got what we expected.

		for uv, expectedResult in expectedResults :
			self.assertEqualWithAbsError( self.__colorAtUV( image, uv ), expectedResult, maxDifference )

	def testNumericParameters( self ) :

		for value in [
			IECore.IntData( 1 ),
			IECore.UIntData( 1 ),
			IECore.FloatData( 1 ),
			IECore.DoubleData( 1 ),
			IECore.FloatData( 1 ),
		] :

			shader = IECoreScene.ShaderNetwork(
				shaders = {
					"output" : IECoreScene.Shader( "principled_bsdf", "cycles:surface", { "base_color" : imath.Color3f( 0 ), "emission_strength" : 1 } ),
					"value" : IECoreScene.Shader( "value", "cycles:shader", { "value" : value } ),
					"converter" : IECoreScene.Shader( "convert_float_to_color", "cycles:shader" ),
				},
				connections = [
					( ( "value", "value" ), ( "converter", "value_float" ) ),
					( ( "converter", "value_color" ), ( "output", "emission_color" ) ),
				],
				output = "output",
			)

			self.__testShaderResults( shader, [ ( imath.V2f( 0.55 ), imath.Color4f( value.value, value.value, value.value, 1 ) ) ] )

	def testColorParameters( self ) :

		for value in [
			IECore.Color3fData( imath.Color3f( 1, 2, 3 ) ),
			IECore.Color4fData( imath.Color4f( 1, 2, 3, 4 ) ),
			IECore.V3fData( imath.V3f( 1, 2, 3 ) ),
			IECore.V3iData( imath.V3i( 1, 2, 3 ) ),
		] :

			shader = IECoreScene.ShaderNetwork(
				shaders = {
					"output" : IECoreScene.Shader(
						"principled_bsdf", "cycles:surface",
						{ "base_color" : imath.Color3f( 0 ), "emission_color" : value, "emission_strength" : 1 }
					),
				},
				output = "output",
			)

			self.__testShaderResults( shader, [ ( imath.V2f( 0.55 ), imath.Color4f( 1, 2, 3, 1 ) ) ] )

	def testVectorParameters( self ) :

		for value in [
			IECore.Color3fData( imath.Color3f( 1, 2, 3 ) ),
			IECore.Color4fData( imath.Color4f( 1, 2, 3, 4 ) ),
			IECore.V3fData( imath.V3f( 1, 2, 3 ) ),
			IECore.V3iData( imath.V3i( 1, 2, 3 ) ),
		] :

			shader = IECoreScene.ShaderNetwork(
				shaders = {
					"converter" : IECoreScene.Shader(
						"convert_vector_to_color", "cycles:shader", { "value_vector" : value }
					),
					"output" : IECoreScene.Shader(
						"principled_bsdf", "cycles:surface", { "base_color" : imath.Color3f( 0 ), "emission_strength" : 1 }
					),
				},
				connections = [
					( ( "converter", "value_color" ), ( "output", "emission_color" ) )
				],
				output = "output",
			)

			self.__testShaderResults( shader, [ ( imath.V2f( 0.55 ), imath.Color4f( 1, 2, 3, 1 ) ) ] )

	def testColorArrayParameters( self ) :

		shader = IECoreScene.ShaderNetwork(
			shaders = {
				"coordinates" : IECoreScene.Shader( "texture_coordinate", "cycles:shader" ),
				"ramp" : IECoreScene.Shader(
					"rgb_ramp", "cycles:shader", {
						"interpolate" : False,
						"ramp" : IECore.Color3fVectorData( [
							imath.Color3f( 0.0, 1.0, 0.25 ),
							imath.Color3f( 0.25, 0.75, 0.25 ),
							imath.Color3f( 0.5, 0.5, 0.25 ),
							imath.Color3f( 0.75, 0.25, 0.25 ),
						] ),
						"ramp_alpha" : IECore.FloatVectorData( [ 1, 1, 1, 1 ] ),
					}
				),
				"output" : IECoreScene.Shader(
					"principled_bsdf", "cycles:surface", { "base_color" : imath.Color3f( 0 ), "emission_strength" : 1 }
				),
			},
			connections = [
				( ( "coordinates", "UV.x" ), ( "ramp", "fac" ) ),
				( ( "ramp", "color" ), ( "output", "emission_color" ) ),
			],
			output = "output",
		)

		self.__testShaderResults(
			shader,
			[
				( imath.V2f( 0.25, 0.5 ), imath.Color4f( 0, 1.0, 0.25, 1 ) ),
				( imath.V2f( 0.5, 0.5 ), imath.Color4f( 0.25, 0.75, 0.25, 1 ) ),
				( imath.V2f( 0.75, 0.5 ), imath.Color4f( 0.5, 0.5, 0.25, 1 ) ),
			]
		)

	def testComponentConnections( self ) :

		shader = IECoreScene.ShaderNetwork(
			shaders = {
				"input" : IECoreScene.Shader(
					"convert_point_to_color", "cycles:shader",
					{
						"value_point" : imath.V3f( 1, 0.5, 0.25 ),
					}
				),
				"output" : IECoreScene.Shader(
					"emission", "cycles:surface",
					{
						"color" : imath.Color3f( 0 ),
						"strength" : 1.0,
					}
				),
			},
			connections = [
				( ( "input", "value_color.r" ), ( "output", "color.g" ) ),
				( ( "input", "value_color.g" ), ( "output", "color.b" ) ),
				( ( "input", "value_color.b" ), ( "output", "color.r" ) ),
			],
			output = "output",
		)

		self.__testShaderResults(
			shader,
			[
				( imath.V2f( 0.5, 0.5 ), imath.Color4f( 0.25, 1, 0.5, 1 ) ),
			]
		)

	def testInvalidShaderParameterValues( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create( "Cycles" )

		for name, value in {
			"sheen_weight" : IECore.StringData( "iShouldBeAFloat" ),
			"base_color" : IECore.StringData( "iShouldBeAColor" ),
			"normal" : IECore.StringData( "iShouldBeAV3f" ),
			"subsurface_method" : IECore.Color3fData( imath.Color3f( 10 ) ),
		}.items() :

			with IECore.CapturingMessageHandler() as mh :

				attributes = renderer.attributes(
					IECore.CompoundObject( {
						"cycles:surface" : IECoreScene.ShaderNetwork(
							shaders = {
								"output" : IECoreScene.Shader( "principled_bsdf", "cycles:surface", { name : value } )
							},
							output = "output"
						)
					} )
				)

				self.assertEqual( len( mh.messages ), 1 )
				self.assertEqual( mh.messages[0].context, "Cycles::SocketAlgo" )
				self.assertEqual( mh.messages[0].level, IECore.Msg.Level.Warning )
				self.assertRegex(
					mh.messages[0].message,
					"Unsupported type `{}` for socket `{}` on node .*".format(
						value.typeName(), name
					)
				)

	def testInvalidShaderEnumValue( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create( "Cycles" )

		with IECore.CapturingMessageHandler() as mh :

			attributes = renderer.attributes(
				IECore.CompoundObject( {
					"cycles:surface" : IECoreScene.ShaderNetwork(
						shaders = {
							"output" : IECoreScene.Shader( "principled_bsdf", "cycles:surface", { "subsurface_method" : "missing" } )
						},
						output = "output"
					)
				} )
			)

			self.assertEqual( len( mh.messages ), 1 )
			self.assertEqual( mh.messages[0].context, "Cycles::SocketAlgo" )
			self.assertEqual( mh.messages[0].level, IECore.Msg.Level.Warning )
			self.assertRegex(
				mh.messages[0].message,
				"Invalid enum value \"missing\" for socket `subsurface_method` on node .*"
			)

	def testUnsupportedShaderParameters( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create( "Cycles" )

		with IECore.CapturingMessageHandler() as mh :

			attributes = renderer.attributes(
				IECore.CompoundObject( {
					"cycles:surface" : IECoreScene.ShaderNetwork(
						shaders = {
							"output" : IECoreScene.Shader( "principled_bsdf", "cycles:surface" ),
							"coordinates" : IECoreScene.Shader( "texture_coordinate", "cycles:shader", { "ob_tfm" : imath.M44f() } ),
						},
						connections = [
							( ( "coordinates", "normal" ), ( "output", "normal" ) )
						],
						output = "output"
					)
				} )
			)

		self.assertEqual( len( mh.messages ), 1 )
		self.assertEqual( mh.messages[0].context, "Cycles::SocketAlgo" )
		self.assertEqual( mh.messages[0].level, IECore.Msg.Level.Warning )
		self.assertRegex(
			mh.messages[0].message,
			"Unsupported socket type `transform` for socket `ob_tfm` on node .*"
		)

	def testUSDLightColorTemperature( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create( "Cycles" )

		renderer.output(
			"testOutput",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ImageDisplayDriver",
					"handle" : "testUsdLightColorTemperature",
				}
			)
		)

		plane = renderer.object(
			"/plane",
			IECoreScene.MeshPrimitive.createPlane(
				imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ),
			),
			renderer.attributes( IECore.CompoundObject ( {
				"cycles:surface" : IECoreScene.ShaderNetwork(
					shaders = {
						"output" : IECoreScene.Shader( "principled_bsdf", "cycles:surface" )
					},
					output = "output",
				)
			} ) )
		)
		plane.transform( imath.M44f().translate( imath.V3f( 0, 0, -1 ) ) )

		# Pure red light, with the colour being provided by an input shader, _not_
		# a direct parameter value. This requires some translation in the renderer backend.

		light = renderer.light(
			"/light",
			None,
			renderer.attributes( IECore.CompoundObject ( {
				"light" : IECoreScene.ShaderNetwork(
					shaders = {
						"output" : IECoreScene.Shader( "SphereLight", "light", { "enableColorTemperature" : True, "colorTemperature" : 3000.0, "exposure" : 6.0 } ),
					},
					output = "output",
				),
			} ) )
		)
		light.transform( imath.M44f().rotate( imath.V3f( 0, math.pi, 0 ) ) )

		renderer.render()

		# Check that the color temperature has tinted the image red.

		image = IECoreImage.ImageDisplayDriver.storedImage( "testUsdLightColorTemperature" )
		self.assertTrue( isinstance( image, IECoreImage.ImagePrimitive ) )

		testPixel = self.__colorAtUV( image, imath.V2f( 0.55 ) )
		testPixel /= testPixel.r # Normalise, to negate impact of noise
		self.assertAlmostEqual( testPixel.r, 1.0, delta = 0.01 )
		self.assertAlmostEqual( testPixel.g, 0.476725, delta = 0.01 )
		self.assertAlmostEqual( testPixel.b, 0.153601, delta = 0.01 )

		del plane, light

	def testOSLInSVMShadingSystem( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create( "Cycles" )

		renderer.option( "cycles:shadingsystem", IECore.StringData( "SVM" ) )

		renderer.output(
			"testOutput",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ImageDisplayDriver",
					"handle" : "testOSLInSVMShadingSystem",
				}
			)
		)

		with IECore.CapturingMessageHandler() as mh :
			attributes = renderer.attributes( IECore.CompoundObject ( {
					"cycles:surface" : IECoreScene.ShaderNetwork(
						shaders = {
							"output" : IECoreScene.Shader(
								"Surface/Constant", "osl:shader",
								{ "Cs" : imath.Color3f( 0, 1, 0 ) }
							),
						},
						output = "output",
					)
				} ) )

		self.assertEqual( len( mh.messages ), 1 )
		self.assertEqual( mh.messages[0].message, """Couldn't load OSL shader "Surface/Constant" as the shading system is not set to OSL.""" )

		plane = renderer.object(
			"/plane",
			IECoreScene.MeshPrimitive.createPlane(
				imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ),
			),
			attributes
		)
		plane.transform( imath.M44f().translate( imath.V3f( 0, 0, -1 ) ) )

		renderer.render()

		image = IECoreImage.ImageDisplayDriver.storedImage( "testOSLInSVMShadingSystem" )
		self.assertIsInstance( image, IECoreImage.ImagePrimitive )

		# Slightly off-centre, to avoid triangle edge artifact in centre of image.
		testPixel = self.__colorAtUV( image, imath.V2f( 0.55 ) )
		# Shader should be black and not crash.
		self.assertEqual( testPixel.r, 0 )
		self.assertEqual( testPixel.g, 0 )
		self.assertEqual( testPixel.b, 0 )

		del plane

	def testFilmOptions( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create( "Cycles" )

		# Get default values

		defaults = renderer.command( "cycles:queryFilm", {} )

		# Set some values of our own and check they have taken hold.

		options = IECore.CompoundData( {
			"cycles:film:exposure" : 10.0,
			"cycles:film:show_active_pixels" : True,
			"cycles:film:filter_type" : "gaussian",
			"cycles:film:filter_width" : 2.5,
		} )
		for name, value in options.items() :
			renderer.option( name, value )

		film = renderer.command( "cycles:queryFilm", {} )
		for name, value in options.items() :
			with self.subTest( name = name ) :
				name = name.replace( "cycles:film:", "" )
				self.assertIn( name, film )
				self.assertEqual( film[name], value )

		# Remove all our options and check that we get back to the
		# original defaults.

		for name in options.keys() :
			renderer.option( name, None )

		film = renderer.command( "cycles:queryFilm", {} )
		for name in options.keys() :
			with self.subTest( name = name ) :
				name = name.replace( "cycles:film:", "" )
				self.assertEqual( film[name], defaults[name] )

	def testIntegratorOptions( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create( "Cycles" )

		# Get default values

		defaults = renderer.command( "cycles:queryIntegrator", {} )

		# Set some values of our own and check they have taken hold.

		options = IECore.CompoundData( {
			"cycles:integrator:min_bounce" : 1,
			"cycles:integrator:max_bounce" : 4,
			"cycles:integrator:use_light_tree" : False,
			"cycles:integrator:use_adaptive_sampling" : False,
		} )
		for name, value in options.items() :
			renderer.option( name, value )

		film = renderer.command( "cycles:queryIntegrator", {} )
		for name, value in options.items() :
			with self.subTest( name = name ) :
				name = name.replace( "cycles:integrator:", "" )
				self.assertIn( name, film )
				self.assertEqual( film[name], value )

		# Remove all our options and check that we get back to the
		# original defaults.

		for name in options.keys() :
			renderer.option( name, None )

		film = renderer.command( "cycles:queryIntegrator", {} )
		for name in options.keys() :
			with self.subTest( name = name ) :
				name = name.replace( "cycles:integrator:", "" )
				self.assertEqual( film[name], defaults[name] )

	def testUnknownOptions( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create( "Cycles" )

		renderer.output(
			"testOutput",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ImageDisplayDriver",
					"handle" : "testUnknownOptions",
				}
			)
		)

		with IECore.CapturingMessageHandler() as mh :
			renderer.option( "cycles:invalid", IECore.IntData( 10 ) )
			renderer.option( "someOtherRenderer:unknown", IECore.IntData( 10 ) )
			renderer.render()

		self.assertEqual( len( mh.messages ), 1 )
		self.assertEqual( mh.messages[0].level, IECore.Msg.Level.Warning )
		self.assertEqual( mh.messages[0].message, 'Unknown option "cycles:invalid".' )

	def testThreads( self ) :

		for threads, expectedThreads in [
			( 1, 1 ),
			( 2, 2 ),
			( -1, max( IECore.hardwareConcurrency() -1, 1 ) ),
			( -10, max( IECore.hardwareConcurrency() -10, 1 ) ),
			( -10000, 1 ),
		] :

			with self.subTest( threads = threads ) :

				renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
					"Cycles",
					GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Interactive,
				)

				renderer.option( "cycles:session:threads", IECore.IntData( threads ) )
				self.assertEqual( renderer.command( "cycles:querySession", {} )["threads"].value, expectedThreads )

	def testDevices( self ) :

		typeIndices = {}
		for device in GafferCycles.devices.values() :

			deviceType = device["type"]
			typeIndex = typeIndices.setdefault( deviceType, 0 )
			typeIndices[device["type"]] += 1

			with self.subTest( device = device["id"] ) :

				renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
					"Cycles",
					GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Interactive,
				)

				# Ideally we want clients to emit all options before doing anything else,
				# to simplify our internal session management. But certain important clients
				# (SceneGadget, RenderController, I'm looking at you) like to create a camera
				# first, and we need to accommodate them while preserving the ability to specify
				# `cycles:device` afterwards.
				renderer.camera( "camera", IECoreScene.Camera() )

				renderer.option( "cycles:shadingsystem", IECore.StringData( "SVM" ) )
				renderer.option( "cycles:device", IECore.StringData( f"{deviceType}:{typeIndex:02d}" ) )
				self.assertEqual( renderer.command( "cycles:querySession", {} )["device"], device["id"] )

	def testExposureEdit( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Cycles",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Interactive,
		)

		renderer.output(
			"testOutput",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ImageDisplayDriver",
					"handle" : "testExposureEdit",
				}
			)
		)

		plane = renderer.object(
			"/plane",
			IECoreScene.MeshPrimitive.createPlane(
				imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ),
			),
			renderer.attributes( IECore.CompoundObject ( {
				"cycles:surface" : IECoreScene.ShaderNetwork(
					shaders = {
						"output" : IECoreScene.Shader( "principled_bsdf", "cycles:surface", { "emission_strength" : 1 } ),
					},
					output = "output",
				)
			} ) )
		)
		plane.transform( imath.M44f().translate( imath.V3f( 0, 0, -1 ) ) )

		renderer.render()
		time.sleep( 1 )

		image = IECoreImage.ImageDisplayDriver.storedImage( "testExposureEdit" )
		self.assertIsInstance( image, IECoreImage.ImagePrimitive )

		# Slightly off-centre, to avoid triangle edge artifact in centre of image.
		testPixel = self.__colorAtUV( image, imath.V2f( 0.55 ) )
		self.assertEqualWithAbsError( testPixel, imath.Color4f( 1 ), 1e-6 )

		# Edit exposure and re-render. We should get an image twice as bright.

		renderer.pause()
		renderer.option( "cycles:film:exposure", IECore.FloatData( 2 ) )

		renderer.render()
		time.sleep( 1 )

		image = IECoreImage.ImageDisplayDriver.storedImage( "testExposureEdit" )
		self.assertIsInstance( image, IECoreImage.ImagePrimitive )

		testPixel = self.__colorAtUV( image, imath.V2f( 0.55 ) )
		self.assertEqualWithAbsError( testPixel, imath.Color4f( 2, 2, 2, 1 ), 1e-6 )

		del plane

	def testUnsupportedSessionEdit( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Cycles",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Interactive,
		)

		renderer.option( "cycles:session:threads", IECore.IntData( 1 ) )

		renderer.output(
			"testOutput",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ImageDisplayDriver",
					"handle" : "testUnsupportedSessionEdit",
				}
			)
		)

		renderer.render()
		self.assertEqual( renderer.command( "cycles:querySession", {} )["threads"].value, 1 )

		with IECore.CapturingMessageHandler() as mh :
			renderer.pause()
			renderer.option( "cycles:session:threads", IECore.IntData( 2 ) )
			renderer.render()

		self.assertEqual( renderer.command( "cycles:querySession", {} )["threads"].value, 1 )

		self.assertEqual( len( mh.messages ), 1 )
		self.assertEqual( mh.messages[0].context, "CyclesRenderer::option" )
		self.assertEqual( mh.messages[0].message, "Option edit requires a manual render restart" )

	def testUnsupportedSessionEdit( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Cycles",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Interactive,
		)

		renderer.option( "cycles:session:threads", IECore.IntData( 1 ) )

		renderer.output(
			"testOutput",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ImageDisplayDriver",
					"handle" : "testUnsupportedSessionEdit",
				}
			)
		)

		renderer.render()
		self.assertEqual( renderer.command( "cycles:querySession", {} )["threads"].value, 1 )

		with IECore.CapturingMessageHandler() as mh :
			renderer.pause()
			renderer.option( "cycles:session:threads", IECore.IntData( 2 ) )
			renderer.render()

		self.assertEqual( len( mh.messages ), 1 )
		self.assertEqual( mh.messages[0].context, "CyclesRenderer::option" )
		self.assertEqual( mh.messages[0].message, "Option edit requires a manual render restart" )

	def testUnsupportedSceneEdit( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Cycles",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Interactive,
		)

		renderer.output(
			"testOutput",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ImageDisplayDriver",
					"handle" : "testUnsupportedSessionEdit",
				}
			)
		)

		renderer.render()

		with IECore.CapturingMessageHandler() as mh :
			renderer.pause()
			renderer.option( "cycles:scene:use_bvh_spatial_split", IECore.BoolData( True ) )
			renderer.render()

		self.assertEqual( len( mh.messages ), 1 )
		self.assertEqual( mh.messages[0].context, "CyclesRenderer::option" )
		self.assertEqual( mh.messages[0].message, "Option edit requires a manual render restart" )

	def testBackgroundLightgroup( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Cycles",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Interactive,
		)

		renderer.output(
			"testOutput",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ImageDisplayDriver",
					"handle" : "testOutput",
				}
			)
		)

		renderer.output(
			"testEnvOutput",
			IECoreScene.Output(
				"env",
				"ieDisplay",
				"lg env",
				{
					"driverType" : "ImageDisplayDriver",
					"handle" : "testEnvOutput",
				}
			)
		)

		renderer.output(
			"testOtherOutput",
			IECoreScene.Output(
				"env",
				"ieDisplay",
				"lg other",
				{
					"driverType" : "ImageDisplayDriver",
					"handle" : "testOtherOutput",
				}
			)
		)

		plane = renderer.object(
			"/plane",
			IECoreScene.MeshPrimitive.createPlane(
				imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ),
			),
			renderer.attributes( IECore.CompoundObject ( {
				"cycles:surface" : IECoreScene.ShaderNetwork(
					shaders = {
						"output" : IECoreScene.Shader(
							"principled_bsdf", "cycles:shader",
							{ "base_color" : imath.Color3f( 1, 1, 1 ) }
						),
					},
					output = "output",
				)
			} ) )
		)
		plane.transform( imath.M44f().translate( imath.V3f( 0, 0, -1 ) ) )

		def lightAttributes( lightgroup ) :

			return renderer.attributes( IECore.CompoundObject ( {
				"cycles:light" : IECoreScene.ShaderNetwork(
					shaders = {
						"output" : IECoreScene.Shader( "background_light", "cycles:light", { "color" : imath.Color3f( 0, 1, 0 ), "lightgroup" : lightgroup } ),
					},
					output = "output",
				),
			} ) )

		# Render with a background light in the "env" lightgroup.
		light = renderer.light( "/light", None, lightAttributes( "env" ) )

		renderer.render()
		time.sleep( 1 )

		image = IECoreImage.ImageDisplayDriver.storedImage( "testOutput" )
		self.assertIsInstance( image, IECoreImage.ImagePrimitive )

		# Slightly off-centre, to avoid triangle edge artifact in centre of image.
		testPixel = self.__colorAtUV( image, imath.V2f( 0.55 ) )
		self.assertEqual( testPixel.r, 0 )
		self.assertGreater( testPixel.g, 0.99 )
		self.assertEqual( testPixel.b, 0 )

		image = IECoreImage.ImageDisplayDriver.storedImage( "testEnvOutput" )
		self.assertIsInstance( image, IECoreImage.ImagePrimitive )

		testPixel = self.__colorAtUV( image, imath.V2f( 0.55 ), "env" )
		self.assertEqual( testPixel.r, 0 )
		self.assertGreater( testPixel.g, 0.99 )
		self.assertEqual( testPixel.b, 0 )

		image = IECoreImage.ImageDisplayDriver.storedImage( "testOtherOutput" )
		self.assertIsInstance( image, IECoreImage.ImagePrimitive )

		testPixel = self.__colorAtUV( image, imath.V2f( 0.55 ), "other" )
		self.assertEqual( testPixel.r, 0 )
		self.assertEqual( testPixel.g, 0 )
		self.assertEqual( testPixel.b, 0 )

		# Edit the lightgroup and re-render, we should see the light's contribution
		# change to the other lightgroup output.
		renderer.pause()
		light.attributes( lightAttributes( "other" ) )
		renderer.render()
		time.sleep( 1 )

		image = IECoreImage.ImageDisplayDriver.storedImage( "testOutput" )
		self.assertIsInstance( image, IECoreImage.ImagePrimitive )

		testPixel = self.__colorAtUV( image, imath.V2f( 0.55 ) )
		self.assertEqual( testPixel.r, 0 )
		self.assertGreater( testPixel.g, 0.99 )
		self.assertEqual( testPixel.b, 0 )

		image = IECoreImage.ImageDisplayDriver.storedImage( "testEnvOutput" )
		self.assertIsInstance( image, IECoreImage.ImagePrimitive )

		testPixel = self.__colorAtUV( image, imath.V2f( 0.55 ), "env" )
		self.assertEqual( testPixel.r, 0 )
		self.assertEqual( testPixel.g, 0 )
		self.assertEqual( testPixel.b, 0 )

		image = IECoreImage.ImageDisplayDriver.storedImage( "testOtherOutput" )
		self.assertIsInstance( image, IECoreImage.ImagePrimitive )

		testPixel = self.__colorAtUV( image, imath.V2f( 0.55 ), "other" )
		self.assertEqual( testPixel.r, 0 )
		self.assertGreater( testPixel.g, 0.99 )
		self.assertEqual( testPixel.b, 0 )

		# Clear the lightgroup and re-render, we shouldn't see the light's contribution
		# in either lightgroup output.
		renderer.pause()
		light.attributes( lightAttributes( "" ) )
		renderer.render()
		time.sleep( 1 )

		image = IECoreImage.ImageDisplayDriver.storedImage( "testOutput" )
		self.assertIsInstance( image, IECoreImage.ImagePrimitive )

		testPixel = self.__colorAtUV( image, imath.V2f( 0.55 ) )
		self.assertEqual( testPixel.r, 0 )
		self.assertGreater( testPixel.g, 0.99 )
		self.assertEqual( testPixel.b, 0 )

		image = IECoreImage.ImageDisplayDriver.storedImage( "testEnvOutput" )
		self.assertIsInstance( image, IECoreImage.ImagePrimitive )

		testPixel = self.__colorAtUV( image, imath.V2f( 0.55 ), "env" )
		self.assertEqual( testPixel.r, 0 )
		self.assertEqual( testPixel.g, 0 )
		self.assertEqual( testPixel.b, 0 )

		image = IECoreImage.ImageDisplayDriver.storedImage( "testOtherOutput" )
		self.assertIsInstance( image, IECoreImage.ImagePrimitive )

		testPixel = self.__colorAtUV( image, imath.V2f( 0.55 ), "other" )
		self.assertEqual( testPixel.r, 0 )
		self.assertEqual( testPixel.g, 0 )
		self.assertEqual( testPixel.b, 0 )

		del light, plane

	def testVDB( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Cycles",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Interactive,
		)

		camera = renderer.camera(
			"testCamera",
			IECoreScene.Camera(
				parameters = {
					"resolution" : imath.V2i( 64, 64 ),
					"projection" : "orthographic",
					"aperture" : imath.V2f( 100, 100 )
				}
			)
		)
		camera.transform( imath.M44f().translate( imath.V3f( 0, 40, 150 ) ) )
		renderer.option( "camera", IECore.StringData( "testCamera" ) )

		renderer.output(
			"testOutput",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ImageDisplayDriver",
					"handle" : "testVDB",
				}
			)
		)

		vdb = IECoreVDB.VDBObject( str( pathlib.Path( __file__ ).parents[2] / "GafferVDBTest" / "data" / "smoke.vdb" ) )
		volume = renderer.object(
			"/vdb",
			vdb,
			renderer.attributes( IECore.CompoundObject ( {
				"cycles:volume" : IECoreScene.ShaderNetwork(
					shaders = {
						"output" : IECoreScene.Shader( "principled_volume", "cycles:volume", { "emission_strength" : 1.0 } )
					},
					output = "output",
				)
			} ) )
		)

		renderer.render()
		time.sleep( 1 )

		image = IECoreImage.ImageDisplayDriver.storedImage( "testVDB" )
		self.assertIsInstance( image, IECoreImage.ImagePrimitive )

		testPixel = self.__colorAtUV( image, imath.V2f( 0.5 ) )
		self.assertGreater( testPixel.r, 0 )
		self.assertGreater( testPixel.g, 0 )
		self.assertGreater( testPixel.b, 0 )

		# Change the shader and ensure that the volume hasn't disappeared as a result.
		renderer.pause()
		volume.attributes(
			renderer.attributes( IECore.CompoundObject ( {
				"cycles:volume" : IECoreScene.ShaderNetwork(
					shaders = {
						"output" : IECoreScene.Shader( "principled_volume", "cycles:volume", { "emission_strength" : 0.5 }  )
					},
					output = "output",
				),
			} ) )
		)

		renderer.render()
		time.sleep( 1 )

		image = IECoreImage.ImageDisplayDriver.storedImage( "testVDB" )
		self.assertIsInstance( image, IECoreImage.ImagePrimitive )

		testPixel = self.__colorAtUV( image, imath.V2f( 0.5 ) )
		self.assertGreater( testPixel.r, 0 )
		self.assertGreater( testPixel.g, 0 )
		self.assertGreater( testPixel.b, 0 )

		del camera
		del volume
		del vdb

	def testDuplicateVDB( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Cycles",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Interactive,
		)

		camera = renderer.camera(
			"testCamera",
			IECoreScene.Camera(
				parameters = {
					"resolution" : imath.V2i( 64, 64 ),
					"projection" : "orthographic",
					"aperture" : imath.V2f( 100, 100 )
				}
			)
		)
		camera.transform( imath.M44f().translate( imath.V3f( 15, 40, 150 ) ) )
		renderer.option( "camera", IECore.StringData( "testCamera" ) )

		renderer.output(
			"testOutput",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ImageDisplayDriver",
					"handle" : "testVDB",
				}
			)
		)

		vdb = IECoreVDB.VDBObject( str( pathlib.Path( __file__ ).parents[2] / "GafferVDBTest" / "data" / "smoke.vdb" ) )
		volume = renderer.object(
			"/vdb",
			vdb,
			renderer.attributes( IECore.CompoundObject ( {
				"cycles:volume" : IECoreScene.ShaderNetwork(
					shaders = {
						"output" : IECoreScene.Shader( "principled_volume", "cycles:volume", { "emission_strength" : 1.0 } )
					},
					output = "output",
				)
			} ) )
		)

		volume2 = renderer.object(
			"/vdb2",
			vdb,
			renderer.attributes( IECore.CompoundObject ( {
				"cycles:volume" : IECoreScene.ShaderNetwork(
					shaders = {
						"output" : IECoreScene.Shader( "principled_volume", "cycles:volume", { "emission_strength" : 0.9 } )
					},
					output = "output",
				)
			} ) )
		)
		volume2.transform( imath.M44f().translate( imath.V3f( 50, 0, 0 ) ) )

		renderer.render()
		time.sleep( 1 )

		image = IECoreImage.ImageDisplayDriver.storedImage( "testVDB" )
		self.assertIsInstance( image, IECoreImage.ImagePrimitive )

		# Ensure both volumes are visible.
		for x in [ imath.V2f( 0.25, 0.5 ), imath.V2f( 0.75, 0.5 ) ] :
			testPixel = self.__colorAtUV( image, x )
			self.assertGreater( testPixel.r, 0 )
			self.assertGreater( testPixel.g, 0 )
			self.assertGreater( testPixel.b, 0 )

		# Change the shader on one volume and ensure that neither volume has disappeared as a result.
		renderer.pause()
		volume.attributes(
			renderer.attributes( IECore.CompoundObject ( {
				"cycles:volume" : IECoreScene.ShaderNetwork(
					shaders = {
						"output" : IECoreScene.Shader( "principled_volume", "cycles:volume", { "emission_strength" : 0.5 }  )
					},
					output = "output",
				),
			} ) )
		)

		renderer.render()
		time.sleep( 1 )

		image = IECoreImage.ImageDisplayDriver.storedImage( "testVDB" )
		self.assertIsInstance( image, IECoreImage.ImagePrimitive )

		for x in [ imath.V2f( 0.25, 0.5 ), imath.V2f( 0.75, 0.5 ) ] :
			testPixel = self.__colorAtUV( image, x )
			self.assertGreater( testPixel.r, 0 )
			self.assertGreater( testPixel.g, 0 )
			self.assertGreater( testPixel.b, 0 )

		del camera
		del volume
		del volume2
		del vdb

if __name__ == "__main__":
	unittest.main()
