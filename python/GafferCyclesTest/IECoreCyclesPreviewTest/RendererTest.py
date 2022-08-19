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
				"ccl:surface" : IECoreScene.ShaderNetwork(
					shaders = {
						"output" : IECoreScene.Shader( "principled_bsdf", "ccl:surface" ),
						"info" : IECoreScene.Shader( "object_info", "ccl:shader" )
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
				"ccl:surface" : IECoreScene.ShaderNetwork(
					shaders = {
						"output" : IECoreScene.Shader( "principled_bsdf", "ccl:surface" )
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
				"ccl:light" : IECoreScene.ShaderNetwork(
					shaders = {
						"output" : IECoreScene.Shader( "quad_light", "ccl:light", { "exposure" : 5.0 } ),
						"color" : IECoreScene.Shader( "color", "ccl:shader", { "value" : imath.Color3f( 1, 0, 0 ) } ),
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
				"ccl:surface" : IECoreScene.ShaderNetwork(
					shaders = {
						"output" : IECoreScene.Shader( "principled_bsdf", "ccl:surface" )
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
				"ccl:light" : IECoreScene.ShaderNetwork(
					shaders = {
						"output" : IECoreScene.Shader( "background_light", "ccl:light", { "color" : imath.Color3f( 1, 0, 0 ) } ),
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

if __name__ == "__main__":
	unittest.main()
