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

import math
import time
import unittest

import imath

import IECore
import IECoreScene
import IECoreImage

import GafferScene
import GafferCycles

import GafferTest

class RendererTest( GafferTest.TestCase ) :

	def testObjectColor( self ) :

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
						"output" : IECoreScene.Shader( "principled_bsdf", "cycles:surface" ),
						"info" : IECoreScene.Shader( "object_info", "cycles:shader" )
					},
					connections = [
						( ( "info", "color" ), ( "output", "emission" ) )
					],
					output = "output",
				)
			} ) )
		)
		## \todo Default camera is facing down +ve Z but should be facing
		# down -ve Z.
		plane.transform( imath.M44f().translate( imath.V3f( 0, 0, 1 ) ) )

		renderer.render()
		time.sleep( 2 )

		image = IECoreImage.ImageDisplayDriver.storedImage( "testObjectColor" )
		self.assertIsInstance( image, IECoreImage.ImagePrimitive )

		middlePixel = image["R"].size() // 2
		self.assertEqual( image["R"][middlePixel], 1 )
		self.assertEqual( image["G"][middlePixel], 0.5 )
		self.assertEqual( image["B"][middlePixel], 0.25 )

		del plane

	def testQuadLightColorTexture( self ) :

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
		## \todo Default camera is facing down +ve Z but should be facing
		# down -ve Z.
		plane.transform( imath.M44f().translate( imath.V3f( 0, 0, 1 ) ) )

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
		light.transform( imath.M44f().rotate( imath.V3f( 0, math.pi, 0 ) ) )

		renderer.render()
		time.sleep( 2.0 )

		# Check that we have a pure red image.

		image = IECoreImage.ImageDisplayDriver.storedImage( "testQuadLightColorTexture" )
		self.assertTrue( isinstance( image, IECoreImage.ImagePrimitive ) )

		middlePixel = image["R"].size() // 2
		self.assertGreater( image["R"][middlePixel], 0 )
		self.assertEqual( image["G"][middlePixel], 0 )
		self.assertEqual( image["B"][middlePixel], 0 )

		del plane, light

	def testLightWithoutAttribute( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Cycles",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch,
		)

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
		## \todo Default camera is facing down +ve Z but should be facing
		# down -ve Z.
		plane.transform( imath.M44f().translate( imath.V3f( 0, 0, 1 ) ) )

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
		time.sleep( 2.0 )

		# Check that we have a pure red image.

		image = IECoreImage.ImageDisplayDriver.storedImage( "testBackgroundLightWithoutTexture" )
		self.assertTrue( isinstance( image, IECoreImage.ImagePrimitive ) )

		middlePixel = image["R"].size() // 2
		self.assertGreater( image["R"][middlePixel], 0 )
		self.assertEqual( image["G"][middlePixel], 0 )
		self.assertEqual( image["B"][middlePixel], 0 )

		del plane

	def testCrashWhenNoBackgroundLight( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Cycles",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Interactive,
		)

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
		time.sleep( 2.0 )

	def testMultipleOutputs( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Cycles",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Interactive,
		)

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

	def testDisplayDriverCropWindow( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Cycles",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Interactive
		)

		renderer.camera(
			"testCamera",
			IECoreScene.Camera(
				parameters = {
					"resolution" : imath.V2i( 2000, 1000 ),
					"cropWindow" : imath.Box2f( imath.V2f( 0.25 ), imath.V2f( 0.75 ) ),
				}
			),
			renderer.attributes( IECore.CompoundObject() )
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
		## \todo We could just be running this test with a Batch mode render,
		# in which case `render()` would block until the image was complete.
		# But CyclesRenderer is currently hardcoded to only use IEDisplayOutputDriver
		# for interactive renders.
		time.sleep( 2.0 )
		del renderer

		image = IECoreImage.ImageDisplayDriver.storedImage( "testCropWindow" )
		self.assertIsNotNone( image )
		self.assertEqual( image.dataWindow, imath.Box2i( imath.V2i( 500, 250 ), imath.V2i( 1499, 749 ) ) )
		self.assertEqual( image.displayWindow, imath.Box2i( imath.V2i( 0 ), imath.V2i( 1999, 999 ) ) )

if __name__ == "__main__":
	unittest.main()
