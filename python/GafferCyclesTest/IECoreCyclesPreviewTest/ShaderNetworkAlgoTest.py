##########################################################################
#
#  Copyright (c) 2022, Alex Fuller. All rights reserved.
#  Copyright (c) 2023, Cinesite VFX Ltd. All rights reserved.
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
#      * Neither the name of Alex Fuller nor the names of
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
import IECoreScene

from GafferCycles import IECoreCyclesPreview as IECoreCycles

class ShaderNetworkAlgoTest( unittest.TestCase ) :

	def testConvertUSDLights( self ) :

		def expectedLightParameters( parameters ) :

			# Start with defaults
			result = {
				"intensity" : 1.0,
				"exposure" : 0.0,
				"color" : imath.Color3f( 1, 1, 1 ),
				"normalize" : False,
				"cast_shadow" : True,
				"use_mis" : True,
				"use_diffuse" : True,
				"use_glossy" : True,
			}
			result.update( parameters )
			return result

		for testName, shaders in {

			# Basic SphereLight -> point_light conversion

			"sphereLightToPointLight" : [

				IECoreScene.Shader(
					"SphereLight", "light",
					{
						"intensity" : 2.5,
						"exposure" : 1.1,
						"color" : imath.Color3f( 1, 2, 3 ),
						"normalize" : True,
						"radius" : 1.0,
					}
				),

				IECoreScene.Shader(
					"point_light", "light",
					expectedLightParameters( {
						"intensity" : 2.5,
						"exposure" : 1.1,
						"color" : imath.Color3f( 1, 2, 3 ),
						"normalize" : True,
						"size" : 1.0,
					} )
				),

			],

			# Basic SphereLight -> point_light conversion, testing default values

			"defaultParameters" : [

				IECoreScene.Shader( "SphereLight", "light", {} ),

				IECoreScene.Shader(
					"point_light", "light",
					expectedLightParameters( {
						"size" : 0.5,
					} )
				),

			],

			# SphereLight with `treatAsPoint = true`.

			"treatAsPoint" : [

				IECoreScene.Shader(
					"SphereLight", "light",
					{
						"treatAsPoint" : True,
					}
				),

				IECoreScene.Shader(
					"point_light", "light",
					expectedLightParameters( {
						"size" : 0.0,
						"normalize" : True,
					} )
				),

			],

			# SphereLight (with shaping) -> spot_light conversion

			"sphereLightToSpotLight" : [

				IECoreScene.Shader(
					"SphereLight", "light",
					{
						"shaping:cone:angle" : 20.0,
						"shaping:cone:softness" : 0.5,
					}
				),

				IECoreScene.Shader(
					"spot_light", "light",
					expectedLightParameters( {
						"spot_angle" : 40.0,
						"spot_smooth" : 0.5,
						"size" : 0.5,
					} )
				),

			],

			# SphereLight (with bogus out-of-range Houdini softness)

			"houdiniPenumbra" : [

				IECoreScene.Shader(
					"SphereLight", "light",
					{
						"shaping:cone:angle" : 20.0,
						"shaping:cone:softness" : 60.0,
					}
				),

				IECoreScene.Shader(
					"spot_light", "light",
					expectedLightParameters( {
						"spot_angle" : 40.0,
						"size" : 0.5,
					} )
				),

			],

			# RectLight -> quad_light

			"rectLight" : [

				IECoreScene.Shader(
					"RectLight", "light",
					{
						"width" : 20.0,
						"height" : 60.0,
					}
				),

				IECoreScene.Shader(
					"quad_light", "light",
					expectedLightParameters( {
						"width" : 20.0,
						"height" : 60.0,
					} )
				),

			],

			# DistantLight -> distant_light

			"distantLight" : [

				IECoreScene.Shader(
					"DistantLight", "light",
					{
						"angle" : 1.0,
					}
				),

				IECoreScene.Shader(
					"distant_light", "light",
					expectedLightParameters( {
						"angle" : 1.0
					} )
				),

			],

			# Disabling shadows

			"rectLightWithoutShadows" : [

				IECoreScene.Shader(
					"RectLight", "light",
					{
						"shadow:enable" : False,
					}
				),

				IECoreScene.Shader(
					"quad_light", "light",
					expectedLightParameters( {
						"width" : 1.0,
						"height" : 1.0,
						"cast_shadow" : False,
					} )
				),

			],

			# Disabling diffuse

			"rectLightWithoutDiffuse" : [

				IECoreScene.Shader(
					"RectLight", "light",
					{
						"diffuse" : 0.0,
					}
				),

				IECoreScene.Shader(
					"quad_light", "light",
					expectedLightParameters( {
						"width" : 1.0,
						"height" : 1.0,
						"use_diffuse" : False,
					} )
				),

			],

			# Disabling specular

			"rectLightWithoutSpecular" : [

				IECoreScene.Shader(
					"RectLight", "light",
					{
						"specular" : 0.0,
					}
				),

				IECoreScene.Shader(
					"quad_light", "light",
					expectedLightParameters( {
						"width" : 1.0,
						"height" : 1.0,
						"use_glossy" : False,
					} )
				),

			],

		}.items() :

			with self.subTest( name = testName ) :

				network = IECoreScene.ShaderNetwork(
					shaders = {
						"light" : shaders[0],
					},
					output = "light",
				)

				IECoreCycles.ShaderNetworkAlgo.convertUSDShaders( network )

				self.__assertShadersEqual( network.getShader( "light" ), shaders[1] )

	def testConvertUSDRectLightTexture( self ) :

		network = IECoreScene.ShaderNetwork(
			shaders = {
				"light" : IECoreScene.Shader(
					"RectLight", "light",
					{
						"texture:file" : "myFile.tx"
					}
				)
			},
			output = "light"
		)

		IECoreCycles.ShaderNetworkAlgo.convertUSDShaders( network )

		output = network.outputShader()
		self.assertEqual( output.name, "quad_light" )

		colorInput = network.input( ( "light", "color" ) )
		texture = network.getShader( colorInput.shader )
		self.assertEqual( texture.name, "image_texture" )
		self.assertEqual( texture.parameters["filename"].value, "myFile.tx" )
		textureInput = network.input( ( colorInput.shader, "vector" ) )
		self.assertEqual( textureInput.name, "parametric" )
		geometry = network.getShader( textureInput.shader )
		self.assertEqual( geometry.name, "geometry" )

	def testConvertUSDDomeLightTexture( self ) :

		network = IECoreScene.ShaderNetwork(
			shaders = {
				"light" : IECoreScene.Shader(
					"DomeLight", "light",
					{
						"texture:file" : "myFile.tx",
						"texture:format" : "mirroredBall",
					}
				)
			},
			output = "light"
		)

		IECoreCycles.ShaderNetworkAlgo.convertUSDShaders( network )

		output = network.outputShader()
		self.assertEqual( output.name, "background_light" )

		colorInput = network.input( ( "light", "color" ) )
		texture = network.getShader( colorInput.shader )
		self.assertEqual( texture.name, "environment_texture" )
		self.assertEqual( texture.parameters["filename"].value, "myFile.tx" )
		self.assertEqual( texture.parameters["projection"].value, "mirror_ball" )

	def testConvertUSDRectLightTextureWithColor( self ) :

		network = IECoreScene.ShaderNetwork(
			shaders = {
				"light" : IECoreScene.Shader(
					"RectLight", "light",
					{
						"texture:file" : "myFile.tx",
						"color" : imath.Color3f( 1, 2, 3 ),
					}
				)
			},
			output = "light"
		)

		IECoreCycles.ShaderNetworkAlgo.convertUSDShaders( network )

		output = network.outputShader()
		self.assertEqual( output.name, "quad_light" )

		# When using a colour and a texture, we need to multiply
		# them together using a shader.

		colorInput = network.input( ( "light", "color" ) )
		colorInputShader = network.getShader( colorInput.shader )
		self.assertEqual( colorInputShader.name, "vector_math" )
		self.assertEqual( colorInputShader.parameters["vector2"].value, imath.Color3f( 1, 2, 3 ) )

		colorInput1 = network.input( ( colorInput.shader, "vector1" ) )
		texture = network.getShader( colorInput1.shader )
		self.assertEqual( texture.name, "image_texture" )
		self.assertEqual( texture.parameters["filename"].value, "myFile.tx" )

	def testConvertCylinderLight( self ) :

		# Cycles doesn't have a Cylinder light, so we convert to a point light
		# and issue a warning.

		network = IECoreScene.ShaderNetwork(
			shaders = {
				"light" : IECoreScene.Shader(
					"CylinderLight", "light",
					{
						"radius" : 0.5,
						"length" : 2.0,
					}
				)
			},
			output = "light"
		)

		with IECore.CapturingMessageHandler() as mh :
			IECoreCycles.ShaderNetworkAlgo.convertUSDShaders( network )

		self.assertEqual( len( mh.messages ), 1 )
		self.assertEqual( mh.messages[0].level, IECore.Msg.Level.Warning )
		self.assertEqual( mh.messages[0].message, "Converting USD CylinderLight to Cycles point light" )

		output = network.outputShader()
		self.assertEqual( output.name, "point_light" )
		self.assertEqual( output.parameters["size"].value, 1.0 )

	def __assertShadersEqual( self, shader1, shader2, message = None ) :

		self.assertEqual( shader1.name, shader2.name, message )
		self.assertEqual( shader1.parameters.keys(), shader2.parameters.keys(), message )
		for k in shader1.parameters.keys() :
			self.assertEqual(
				shader1.parameters[k], shader2.parameters[k],
				"{}(Parameter = {})".format( message or "", k )
			)

if __name__ == "__main__":
	unittest.main()
