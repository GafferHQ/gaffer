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

import math
import unittest

import imath

import IECore
import IECoreScene

import IECoreDelight

class ShaderNetworkAlgoTest( unittest.TestCase ) :

	def testConvertUSDPreviewSurfaceEmission( self ) :

		for emissiveColor in ( imath.Color3f( 1 ), imath.Color3f( 0 ), None ) :

			parameters = {}
			if emissiveColor is not None :
				parameters["emissiveColor"] = IECore.Color3fData( emissiveColor )

			network = IECoreScene.ShaderNetwork(
				shaders = {
					"previewSurface" : IECoreScene.Shader(
						"UsdPreviewSurface", "surface", parameters
					)
				},
				output = "previewSurface",
			)

			convertedNetwork = network.copy()
			IECoreDelight.ShaderNetworkAlgo.convertUSDShaders( convertedNetwork )

			convertedShader = convertedNetwork.getShader( "previewSurface" )
			self.assertEqual( convertedShader.name, "dlStandard" )
			self.assertEqual(
				convertedShader.parameters["emission_color"].value,
				emissiveColor if emissiveColor is not None else imath.Color3f( 0 )
			)

			if emissiveColor is not None and emissiveColor != imath.Color3f( 0 ) :
				self.assertEqual( convertedShader.parameters["emission_w"], IECore.FloatData( 1 ) )
			else :
				self.assertEqual( convertedShader.parameters["emission_w"], IECore.FloatData( 0 ) )

			# Repeat, but with an input connection as well as the parameter value

			network.addShader( "texture", IECoreScene.Shader( "UsdUVTexture" ) )
			network.addConnection( ( ( "texture", "rgb" ), ( "previewSurface", "emissiveColor" ) ) )

			convertedNetwork = network.copy()
			IECoreDelight.ShaderNetworkAlgo.convertUSDShaders( convertedNetwork )

			convertedShader = convertedNetwork.getShader( "previewSurface" )
			self.assertEqual( convertedShader.name, "dlStandard" )

			self.assertEqual(
				convertedNetwork.input( ( "previewSurface", "emission_color" ) ),
				( "texture", "rgb" ),
			)
			self.assertEqual( convertedShader.parameters["emission_w"], IECore.FloatData( 1 ) )

	def testConvertUSDFloat3ToColor3f( self ) :

		# Although UsdPreviewSurface parameters are defined to be `color3f` in the spec,
		# some USD files seem to provide `float3` values instead. For example :
		#
		# https://github.com/usd-wg/assets/blob/64ebce19c9a6c795862548066bc1070bf0f7f955/test_assets/AlphaBlendModeTest/AlphaBlendModeTest.usd#L27
		#
		# Make sure that we convert these to colours for consumption by 3Delight.

		network = IECoreScene.ShaderNetwork(
			shaders = {
				"previewSurface" : IECoreScene.Shader(
					"UsdPreviewSurface", "surface",
					{
						"diffuseColor" : imath.V3f( 0, 0.25, 0.5 ),
					}
				)
			},
			output = "previewSurface",
		)

		IECoreDelight.ShaderNetworkAlgo.convertUSDShaders( network )
		self.assertEqual(
			network.getShader( "previewSurface" ).parameters["base_color"],
			IECore.Color3fData( imath.Color3f( 0, 0.25, 0.5 ) )
		)

	def testConvertUSDOpacity( self ) :

		# The results of this type of conversion may also be verified visually using
		# the AlphaBlendModeTest asset found here :
		#
		# https://github.com/usd-wg/assets/tree/main/test_assets/AlphaBlendModeTest
		#
		# > Note : the "cutoff" positions are incorrect, because 3Delight's colorspace
		# > transformation of the sRGB PNG textures also affects their alpha channel.
		# > Loading these textures with `sourceColorSpace`=`raw` results in the correct
		# > cutoff positions.

		for opacity in ( 0.25, 1.0, None ) :
			for opacityThreshold in ( 0.0, 0.5, None ) :

				parameters = {}
				if opacity is not None :
					parameters["opacity"] = IECore.FloatData( opacity )
				if opacityThreshold is not None :
					parameters["opacityThreshold"] = IECore.FloatData( opacityThreshold )

				network = IECoreScene.ShaderNetwork(
					shaders = {
						"previewSurface" : IECoreScene.Shader(
							"UsdPreviewSurface", "surface", parameters
						)
					},
					output = "previewSurface",
				)

				convertedNetwork = network.copy()
				IECoreDelight.ShaderNetworkAlgo.convertUSDShaders( convertedNetwork )

				convertedShader = convertedNetwork.getShader( "previewSurface" )
				expectedOpacity = opacity if opacity is not None else 1.0
				if opacityThreshold is not None :
					expectedOpacity = expectedOpacity if expectedOpacity > opacityThreshold else 0

				self.assertEqual(
					convertedShader.parameters["opacity"].value,
					imath.Color3f( expectedOpacity )
				)

				# Repeat, but with an input connection as well as the parameter value

				network.addShader( "texture", IECoreScene.Shader( "UsdUVTexture" ) )
				network.addConnection( ( ( "texture", "a" ), ( "previewSurface", "opacity" ) ) )

				convertedNetwork = network.copy()
				IECoreDelight.ShaderNetworkAlgo.convertUSDShaders( convertedNetwork )

				if opacityThreshold :

					self.assertEqual( len( convertedNetwork ), 4 )
					opacityInput = convertedNetwork.input( ( "previewSurface", "opacity" ) )
					self.assertEqual( opacityInput, ( "previewSurfaceOpacityMultiply", "o_output" ) )
					self.assertEqual( convertedNetwork.getShader( opacityInput.shader ).name, "multiplyDivide" )
					self.assertEqual(
						convertedNetwork.input( ( "previewSurfaceOpacityMultiply", "input1" ) ),
						( "texture", "a" )
					)
					for c in "XYZ" :
						multiplyInput = convertedNetwork.input( ( "previewSurfaceOpacityMultiply", "input2{}".format( c ) ) )
						self.assertEqual( multiplyInput, ( "previewSurfaceOpacityCompare", "success" ) )

					self.assertEqual(
						convertedNetwork.input( ( "previewSurfaceOpacityCompare", "a" ) ),
						( "texture", "a" )
					)

					compareShader = convertedNetwork.getShader( "previewSurfaceOpacityCompare" )
					self.assertEqual( compareShader.parameters["condition"].value, 2 )
					self.assertEqual( compareShader.parameters["b"].value, opacityThreshold )

				else :

					self.assertEqual( len( convertedNetwork ), 2 )
					self.assertEqual(
						convertedNetwork.input( ( "previewSurface", "opacity" ) ),
						( "texture", "a" )
					)

	def testConvertUSDSpecular( self ) :

		for useSpecularWorkflow in ( True, False ) :
			for specularColor in ( imath.Color3f( 0, 0.25, 0.5 ), None ) :
				with self.subTest( useSpecularWorkflow = useSpecularWorkflow, specularColor = specularColor ) :

					parameters = {
						"metallic" : 0.5,
						"useSpecularWorkflow" : int( useSpecularWorkflow ),
					}
					if specularColor is not None :
						parameters["specularColor"] = specularColor

					network = IECoreScene.ShaderNetwork(
						shaders = {
							"previewSurface" : IECoreScene.Shader(
								"UsdPreviewSurface", "surface", parameters
							)
						},
						output = "previewSurface",
					)

					convertedNetwork = network.copy()
					IECoreDelight.ShaderNetworkAlgo.convertUSDShaders( convertedNetwork )
					convertedShader = convertedNetwork.getShader( "previewSurface" )

					if useSpecularWorkflow :
						self.assertEqual(
							convertedShader.parameters["specular_color"].value,
							specularColor if specularColor is not None else imath.Color3f( 0 )
						)
						self.assertNotIn( "metallic", convertedShader.parameters )
					else :
						self.assertEqual( convertedShader.parameters["metalness"].value, 0.5 )
						self.assertNotIn( "specular_color", convertedShader.parameters )

					# Repeat with input connections

					network.addShader( "texture", IECoreScene.Shader( "UsdUVTexture" ) )
					network.addConnection( ( ( "texture", "rgb" ), ( "previewSurface", "specularColor" ) ) )
					network.addConnection( ( ( "texture", "r" ), ( "previewSurface", "metallic" ) ) )

					convertedNetwork = network.copy()
					IECoreDelight.ShaderNetworkAlgo.convertUSDShaders( convertedNetwork )

					if useSpecularWorkflow :
						self.assertEqual(
							convertedNetwork.input( ( "previewSurface", "specular_color" ) ),
							( "texture", "rgb" ),
						)
						self.assertFalse( convertedNetwork.input( ( "previewSurface", "metalness" ) ) )
					else :
						self.assertEqual(
							convertedNetwork.input( ( "previewSurface", "metalness" ) ),
							( "texture", "r" ),
						)
						self.assertFalse( convertedNetwork.input( ( "previewSurface", "specular_color" ) ) )

					self.assertFalse( convertedNetwork.input( ( "previewSurface", "specularColor" ) ) )

	def testConvertUSDClearcoat( self ) :

		network = IECoreScene.ShaderNetwork(
			shaders = {
				"previewSurface" : IECoreScene.Shader(
					"UsdPreviewSurface", "surface",
					{
						"clearcoat" : 0.75,
						"clearcoatRoughness" : 0.25,
					}
				)
			},
			output = "previewSurface",
		)

		convertedNetwork = network.copy()
		IECoreDelight.ShaderNetworkAlgo.convertUSDShaders( convertedNetwork )
		convertedShader = convertedNetwork.getShader( "previewSurface" )

		self.assertEqual( convertedShader.parameters["coat"].value, 0.75 )
		self.assertEqual( convertedShader.parameters["coat_roughness"].value, 0.25 )

		# Repeat with input connections

		network.addShader( "texture", IECoreScene.Shader( "UsdUVTexture" ) )
		network.addConnection( ( ( "texture", "r" ), ( "previewSurface", "clearcoat" ) ) )
		network.addConnection( ( ( "texture", "g" ), ( "previewSurface", "clearcoatRoughness" ) ) )

		convertedNetwork = network.copy()
		IECoreDelight.ShaderNetworkAlgo.convertUSDShaders( convertedNetwork )

		self.assertEqual(
			convertedNetwork.input( ( "previewSurface", "coat" ) ),
			( "texture", "r" ),
		)
		self.assertEqual(
			convertedNetwork.input( ( "previewSurface", "coat_roughness" ) ),
			( "texture", "g" ),
		)

	def testConvertSimpleUSDUVTexture( self ) :

		for uvPrimvar in ( "st", "customUV" ) :

			network = IECoreScene.ShaderNetwork(
				shaders = {
					"previewSurface" : IECoreScene.Shader( "UsdPreviewSurface" ),
					"texture" : IECoreScene.Shader(
						"UsdUVTexture", "shader",
						{
							"file" : "test.png",
							"wrapS" : "useMetadata",
							"wrapT" : "repeat",
							"sourceColorSpace" : "auto",
						}
					),
					"uvReader" : IECoreScene.Shader(
						"UsdPrimvarReader_float2", "shader",
						{
							"varname" : uvPrimvar,
						}
					),
				},
				connections = [
					( ( "uvReader", "result" ), ( "texture", "st" ) ),
					( ( "texture", "rgb" ), ( "previewSurface", "diffuseColor" ) ),
				],
				output = "previewSurface",
			)

			IECoreDelight.ShaderNetworkAlgo.convertUSDShaders( network )

			self.assertEqual( network.input( ( "previewSurface", "base_color" ) ), ( "texture", "rgb" ) )

			texture = network.getShader( "texture" )
			self.assertEqual( texture.name, "__usd/__usdUVTexture" )
			self.assertEqual( texture.parameters["file"].value, "test.png" )
			self.assertEqual( texture.parameters["wrapS"].value, "useMetadata" )
			self.assertEqual( texture.parameters["wrapT"].value, "repeat" )
			self.assertEqual( texture.parameters["file_meta_colorspace"].value, "auto" )

	def testConvertSimpleUSDNormalTexture( self ) :

		for uvPrimvar in ( "st", "customUV" ) :

			network = IECoreScene.ShaderNetwork(
				shaders = {
					"previewSurface" : IECoreScene.Shader( "UsdPreviewSurface" ),
					"normalTexture" : IECoreScene.Shader(
						"UsdUVTexture", "shader",
						{
							"file" : "test.png",
							"wrapS" : "useMetadata",
							"wrapT" : "repeat",
							"sourceColorSpace" : "raw",
						}
					),
					"uvReader" : IECoreScene.Shader(
						"UsdPrimvarReader_float2", "shader",
						{
							"varname" : uvPrimvar,
						}
					),
				},
				connections = [
					( ( "uvReader", "result" ), ( "normalTexture", "st" ) ),
					( ( "normalTexture", "rgb" ), ( "previewSurface", "normal" ) ),
				],
				output = "previewSurface",
			)

			IECoreDelight.ShaderNetworkAlgo.convertUSDShaders( network )

			bump2d = network.getShader( "previewSurfaceNormal" )
			self.assertEqual( bump2d.name, "bump2d" )
			self.assertEqual( bump2d.parameters["bumpInterp"].value, 1 )

			self.assertEqual( network.input( ( "previewSurface", "input_normal" ) ), ( "previewSurfaceNormal", "outNormal" ) )
			# We insert a shader to convert UsdPreviewSurface's expectation of signed normals back into color for the bump2d shader.
			self.assertEqual( network.input( ( "previewSurfaceNormal", "bumpNormal" ) ), ( "previewSurfaceSignedToColor", "out" ) )
			# The bump2d shader requires the same uv coordinates as the normal texture.
			self.assertEqual( network.input( ( "previewSurfaceNormal", "uvCoord" ) ), network.input( ( "normalTexture", "uvCoord" ) ) )

			texture = network.getShader( "normalTexture" )
			self.assertEqual( texture.name, "__usd/__usdUVTexture" )
			self.assertEqual( texture.parameters["file"].value, "test.png" )
			self.assertEqual( texture.parameters["wrapS"].value, "useMetadata" )
			self.assertEqual( texture.parameters["wrapT"].value, "repeat" )
			self.assertEqual( texture.parameters["file_meta_colorspace"].value, "raw" )

	def testConvertTransformedUSDUVTexture( self ) :

		# The results of this type of conversion may also be verified visually using
		# the TextureTransformTest asset found here :
		#
		# https://github.com/usd-wg/assets/tree/main/test_assets/TextureTransformTest

		network = IECoreScene.ShaderNetwork(
			shaders = {
				"previewSurface" : IECoreScene.Shader( "UsdPreviewSurface" ),
				"texture" : IECoreScene.Shader(
					"UsdUVTexture", "shader",
					{
						"file" : "test.png",
						"wrapS" : "repeat",
						"wrapT" : "repeat",
						"sourceColorSpace" : "auto",
					}
				),
				"transform" : IECoreScene.Shader(
					"UsdTransform2d", "shader",
					{
						"rotation" : 90.0,
					}
				),
				"uvReader" : IECoreScene.Shader(
					"UsdPrimvarReader_float2", "shader",
					{
						"varname" : "st",
					}
				),
			},
			connections = [
				( ( "uvReader", "result" ), ( "transform", "in" ) ),
				( ( "transform", "result" ), ( "texture", "st" ) ),
				( ( "texture", "rgb" ), ( "previewSurface", "diffuseColor" ) ),
			],
			output = "previewSurface",
		)

		convertedNetwork = network.copy()
		IECoreDelight.ShaderNetworkAlgo.convertUSDShaders( convertedNetwork )

		texture = convertedNetwork.getShader( "texture" )
		self.assertEqual( texture.name, "__usd/__usdUVTexture" )
		self.assertEqual( texture.parameters["file"].value, "test.png" )
		self.assertEqual( texture.parameters["wrapS"].value, "repeat" )
		self.assertEqual( texture.parameters["wrapT"].value, "repeat" )
		self.assertEqual( texture.parameters["file_meta_colorspace"].value, "auto" )

		uvReader = convertedNetwork.getShader( "uvReader" )
		self.assertEqual( uvReader.name, "dlPrimitiveAttribute" )

		transform = convertedNetwork.getShader( "transform" )
		self.assertEqual( transform.name, "__usd/__matrixTransformUV" )
		self.assertEqual( transform.parameters["m"].value, imath.M44f().rotate( imath.V3f( 0, 0, math.radians( 90 ) ) ) )

		self.assertEqual( convertedNetwork.input( ( "transform", "uvCoord" ) ), ( "uvReader", "o_uv" ) )

	def testConvertUSDUVTextureColor4Parameters( self ) :

		network = IECoreScene.ShaderNetwork(
			shaders = {
				"previewSurface" : IECoreScene.Shader( "UsdPreviewSurface" ),
				"texture" : IECoreScene.Shader(
					"UsdUVTexture", "shader",
					{
						"fallback" : imath.Color4f( 1, 2, 3, 4 ),
						"scale" : imath.Color4f( 0.1, 0.2, 0.3, 0.4 ),
						"bias" : imath.Color4f( 0.2, 0.4, 0.6, 0.8 ),
					}
				),
			},
			connections = [
				( ( "texture", "rgb" ), ( "previewSurface", "diffuseColor" ) ),
				( ( "texture", "a" ), ( "previewSurface", "roughness" ) ),
				( ( "texture", "r" ), ( "previewSurface", "metallic" ) ),
			],
			output = "previewSurface",
		)

		convertedNetwork = network.copy()
		IECoreDelight.ShaderNetworkAlgo.convertUSDShaders( convertedNetwork )

		texture = convertedNetwork.getShader( "texture" )
		self.assertEqual( texture.name, "__usd/__usdUVTexture" )
		self.assertEqual( texture.parameters["fallback"].value, imath.Color4f( 1, 2, 3, 4 ) )
		self.assertEqual( texture.parameters["scale"].value, imath.Color4f( 0.1, 0.2, 0.3, 0.4 ) )
		self.assertEqual( texture.parameters["bias"].value, imath.Color4f( 0.2, 0.4, 0.6, 0.8 ) )

	def testConvertUSDPrimvarReader( self ) :

		for usdDataType, convertedShaderType, usdFallback, convertedDefault in [
			( "float", "ObjectProcessing/InFloat", 2.0, 2.0 ),
			( "float2", "dlPrimitiveAttribute", imath.V2f( 1, 2 ), imath.Color3f( 1, 2, 0 ) ),
			( "float3", "ObjectProcessing/InColor", imath.V3f( 1, 2, 3 ), imath.Color3f( 1, 2, 3 ) ),
			( "normal", "ObjectProcessing/InColor", imath.V3f( 1, 2, 3 ), imath.Color3f( 1, 2, 3 ) ),
			( "point", "ObjectProcessing/InColor", imath.V3f( 1, 2, 3 ), imath.Color3f( 1, 2, 3 ) ),
			( "vector", "ObjectProcessing/InColor", imath.V3f( 1, 2, 3 ), imath.Color3f( 1, 2, 3 ) ),
			( "int", "ObjectProcessing/InInt", 10, 10 ),
			( "string", "ObjectProcessing/InString", "hi", "hi" ),
		] :

			network = IECoreScene.ShaderNetwork(
				shaders = {
					"reader" : IECoreScene.Shader(
						"UsdPrimvarReader_{}".format( usdDataType ), "shader",
						{
							"varname" : "test",
							"fallback" : usdFallback,
						}
					),
				},
				output = "reader",
			)

			IECoreDelight.ShaderNetworkAlgo.convertUSDShaders( network )

			reader = network.getShader( "reader" )
			self.assertEqual( reader.name, convertedShaderType )
			self.assertEqual( len( reader.parameters ), 3 if convertedShaderType == "dlPrimitiveAttribute" else 2 )
			self.assertEqual( reader.parameters["attribute_name" if convertedShaderType == "dlPrimitiveAttribute" else "name"].value, "test" )
			self.assertEqual( reader.parameters["fallback_value" if convertedShaderType == "dlPrimitiveAttribute" else "defaultValue"].value, convertedDefault )

if __name__ == "__main__":
	unittest.main()
