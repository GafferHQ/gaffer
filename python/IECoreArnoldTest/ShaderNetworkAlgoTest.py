##########################################################################
#
#  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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

import ctypes
import unittest
import math

import arnold

import imath

import IECore
import IECoreScene
import IECoreArnold

class ShaderNetworkAlgoTest( unittest.TestCase ) :

	def test( self ) :

		network = IECoreScene.ShaderNetwork(
			shaders = {
				"noiseHandle" : IECoreScene.Shader( "noise" ),
				"flatHandle" : IECoreScene.Shader( "flat" ),
			},
			connections = [
				( ( "noiseHandle", "" ), ( "flatHandle", "color" ) ),
			],
			output = "flatHandle"
		)

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			nodes = IECoreArnold.ShaderNetworkAlgo.convert( network, universe, "test" )

			self.assertEqual( len( nodes ), 2 )
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( nodes[0] ) ), "noise" )
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( nodes[1] ) ), "flat" )

			self.assertEqual( arnold.AiNodeGetName( nodes[0] ), "test:noiseHandle" )
			self.assertEqual( arnold.AiNodeGetName( nodes[1] ), "test" )

			self.assertEqual(
				ctypes.addressof( arnold.AiNodeGetLink( nodes[1], "color" ).contents ),
				ctypes.addressof( nodes[0].contents )
			)

	def testUpdate( self ) :

		network = IECoreScene.ShaderNetwork(
			shaders = {
				"noiseHandle" : IECoreScene.Shader( "noise" ),
				"flatHandle" : IECoreScene.Shader( "flat" ),
			},
			connections = [
				( ( "noiseHandle", "" ), ( "flatHandle", "color" ) ),
			],
			output = "flatHandle"
		)

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			# Convert

			nodes = IECoreArnold.ShaderNetworkAlgo.convert( network, universe, "test" )

			def assertNoiseAndFlatNodes() :

				self.assertEqual( len( nodes ), 2 )
				self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( nodes[0] ) ), "noise" )
				self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( nodes[1] ) ), "flat" )

				self.assertEqual( arnold.AiNodeGetName( nodes[0] ), "test:noiseHandle" )
				self.assertEqual( arnold.AiNodeGetName( nodes[1] ), "test" )

				self.assertEqual(
					ctypes.addressof( arnold.AiNodeGetLink( nodes[1], "color" ).contents ),
					ctypes.addressof( nodes[0].contents )
				)

			assertNoiseAndFlatNodes()

			# Convert again with no changes at all. We want to see the same nodes reused.

			originalNodes = nodes[:]
			self.assertTrue( IECoreArnold.ShaderNetworkAlgo.update( nodes, network ) )
			assertNoiseAndFlatNodes()

			self.assertEqual( ctypes.addressof( nodes[0].contents ), ctypes.addressof( originalNodes[0].contents ) )
			self.assertEqual( ctypes.addressof( nodes[1].contents ), ctypes.addressof( originalNodes[1].contents ) )

			# Convert again with a tweak to a noise parameter. We want to see the same nodes
			# reused, with the new parameter value taking hold.

			noise = network.getShader( "noiseHandle" )
			noise.parameters["octaves"] = IECore.IntData( 3 )
			network.setShader( "noiseHandle", noise )

			originalNodes = nodes[:]
			self.assertTrue( IECoreArnold.ShaderNetworkAlgo.update( nodes, network ) )
			assertNoiseAndFlatNodes()

			self.assertEqual( ctypes.addressof( nodes[0].contents ), ctypes.addressof( originalNodes[0].contents ) )
			self.assertEqual( ctypes.addressof( nodes[1].contents ), ctypes.addressof( originalNodes[1].contents ) )
			self.assertEqual( arnold.AiNodeGetInt( nodes[0], "octaves" ), 3 )

			# Remove the noise shader, and replace it with an image. Make sure the new network is as we expect, and
			# the old noise node has been destroyed.

			network.removeShader( "noiseHandle" )
			network.setShader( "imageHandle", IECoreScene.Shader( "image" ) )
			network.addConnection( ( ( "imageHandle", "" ), ( "flatHandle", "color" ) ) )

			originalNodes = nodes[:]
			self.assertTrue( IECoreArnold.ShaderNetworkAlgo.update( nodes, network ) )

			self.assertEqual( ctypes.addressof( nodes[1].contents ), ctypes.addressof( originalNodes[1].contents ) )

			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( nodes[0] ) ), "image" )
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( nodes[1] ) ), "flat" )

			self.assertEqual( arnold.AiNodeGetName( nodes[0] ), "test:imageHandle" )
			self.assertEqual( arnold.AiNodeGetName( nodes[1] ), "test" )

			self.assertEqual(
				ctypes.addressof( arnold.AiNodeGetLink( nodes[1], "color" ).contents ),
				ctypes.addressof( nodes[0].contents )
			)

			self.assertIsNone( arnold.AiNodeLookUpByName( universe, "test:noiseHandle" ) )

			# Replace the output shader with something else.

			network.removeShader( "flatHandle" )
			network.setShader( "lambertHandle", IECoreScene.Shader( "lambert" ) )
			network.addConnection( ( ( "imageHandle", "" ), ( "lambertHandle", "Kd_color" ) ) )
			network.setOutput( ( "lambertHandle", "" ) )

			originalNodes = nodes[:]
			self.assertFalse( IECoreArnold.ShaderNetworkAlgo.update( nodes, network ) )

			self.assertEqual( ctypes.addressof( nodes[0].contents ), ctypes.addressof( originalNodes[0].contents ) )

			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( nodes[0] ) ), "image" )
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( nodes[1] ) ), "lambert" )

			self.assertEqual( arnold.AiNodeGetName( nodes[0] ), "test:imageHandle" )
			self.assertEqual( arnold.AiNodeGetName( nodes[1] ), "test" )

			self.assertEqual(
				ctypes.addressof( arnold.AiNodeGetLink( nodes[1], "Kd_color" ).contents ),
				ctypes.addressof( nodes[0].contents )
			)

	def testBlindData( self ) :

		flat = IECoreScene.Shader( "flat" )
		flat.blindData().update( {
				"user:testInt" : IECore.IntData( 1 ),
				"user:testFloat" : IECore.FloatData( 2.5 ),
				"user:testV3f" : IECore.V3fData( imath.V3f( 1, 2, 3 ) ),
				"user:testColor3f" : IECore.Color3fData( imath.Color3f( 4, 5, 6 ) ),
				"user:testString" : IECore.StringData( "we're all doomed" ),
		} )

		network = IECoreScene.ShaderNetwork(
			shaders = {
				"noiseHandle" : IECoreScene.Shader( "noise" ),
				"flatHandle" : flat,
			},
			connections = [
				( ( "noiseHandle", "" ), ( "flatHandle", "color" ) ),
			],
			output = "flatHandle"
		)

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			nodes = IECoreArnold.ShaderNetworkAlgo.convert( network, universe, "test" )

			self.assertEqual( len( nodes ), 2 )
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( nodes[0] ) ), "noise" )
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( nodes[1] ) ), "flat" )

			self.assertEqual( arnold.AiNodeGetName( nodes[0] ), "test:noiseHandle" )
			self.assertEqual( arnold.AiNodeGetName( nodes[1] ), "test" )

			self.assertEqual( arnold.AiNodeGetInt( nodes[1], "user:testInt" ), 1 )
			self.assertEqual( arnold.AiNodeGetFlt( nodes[1], "user:testFloat" ), 2.5 )
			self.assertEqual( arnold.AiNodeGetVec( nodes[1], "user:testV3f" ), arnold.AtVector( 1, 2, 3 ) )
			self.assertEqual( arnold.AiNodeGetRGB( nodes[1], "user:testColor3f" ), arnold.AtRGB( 4, 5, 6 ) )
			self.assertEqual( arnold.AiNodeGetStr( nodes[1], "user:testString" ), "we're all doomed" )

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
			IECoreArnold.ShaderNetworkAlgo.convertUSDShaders( convertedNetwork )

			convertedShader = convertedNetwork.getShader( "previewSurface" )
			self.assertEqual( convertedShader.name, "standard_surface" )
			self.assertEqual(
				convertedShader.parameters["emission_color"].value,
				emissiveColor if emissiveColor is not None else imath.Color3f( 0 )
			)

			if emissiveColor is not None and emissiveColor != imath.Color3f( 0 ) :
				self.assertEqual( convertedShader.parameters["emission"], IECore.FloatData( 1 ) )
			else :
				self.assertEqual( convertedShader.parameters["emission"], IECore.FloatData( 0 ) )

			# Repeat, but with an input connection as well as the parameter value

			network.addShader( "texture", IECoreScene.Shader( "UsdUVTexture" ) )
			network.addConnection( ( ( "texture", "rgb" ), ( "previewSurface", "emissiveColor" ) ) )

			convertedNetwork = network.copy()
			IECoreArnold.ShaderNetworkAlgo.convertUSDShaders( convertedNetwork )

			convertedShader = convertedNetwork.getShader( "previewSurface" )
			self.assertEqual( convertedShader.name, "standard_surface" )

			self.assertEqual(
				convertedNetwork.input( ( "previewSurface", "emission_color" ) ),
				( "texture", "" ),
			)
			self.assertEqual( convertedShader.parameters["emission"], IECore.FloatData( 1 ) )

	def testConvertUSDFloat3ToColor3f( self ) :

		# Although UsdPreviewSurface parameters are defined to be `color3f` in the spec,
		# some USD files seem to provide `float3` values instead. For example :
		#
		# https://github.com/usd-wg/assets/blob/64ebce19c9a6c795862548066bc1070bf0f7f955/test_assets/AlphaBlendModeTest/AlphaBlendModeTest.usd#L27
		#
		# Make sure that we convert these to colours for consumption by Arnold.

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

		IECoreArnold.ShaderNetworkAlgo.convertUSDShaders( network )
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
		# > Note : the leftmost texture is incorrect, because USD expects the texture
		# > (which has unpremultiplied alpha) to be loaded unmodified, but OIIO/Arnold
		# > appear to premultiply it during loading.

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
				IECoreArnold.ShaderNetworkAlgo.convertUSDShaders( convertedNetwork )

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
				IECoreArnold.ShaderNetworkAlgo.convertUSDShaders( convertedNetwork )

				if opacityThreshold :

					self.assertEqual( len( convertedNetwork ), 4 )
					opacityInput = convertedNetwork.input( ( "previewSurface", "opacity" ) )
					self.assertEqual( opacityInput, "previewSurfaceOpacityMultiply" )
					self.assertEqual( convertedNetwork.getShader( opacityInput.shader ).name, "multiply" )
					self.assertEqual(
						convertedNetwork.input( ( "previewSurfaceOpacityMultiply", "input1" ) ),
						( "texture", "a" )
					)
					for c in "rgb" :
						multiplyInput = convertedNetwork.input( ( "previewSurfaceOpacityMultiply", "input2.{}".format( c ) ) )
						self.assertEqual( multiplyInput, "previewSurfaceOpacityCompare" )

					self.assertEqual(
						convertedNetwork.input( ( "previewSurfaceOpacityCompare", "input1" ) ),
						( "texture", "a" )
					)

					compareShader = convertedNetwork.getShader( "previewSurfaceOpacityCompare" )
					self.assertEqual( compareShader.parameters["test"].value, ">" )
					self.assertEqual( compareShader.parameters["input2"].value, opacityThreshold )

				else :

					self.assertEqual( len( convertedNetwork ), 2 )
					self.assertEqual(
						convertedNetwork.input( ( "previewSurface", "opacity" ) ),
						( "texture", "a" )
					)

	def testConvertUSDSpecular( self ) :

		for useSpecularWorkflow in ( True, False ) :

			network = IECoreScene.ShaderNetwork(
				shaders = {
					"previewSurface" : IECoreScene.Shader(
						"UsdPreviewSurface", "surface",
						{
							"specularColor" : imath.V3f( 0, 0.25, 0.5 ),
							"metallic" : 0.5,
							"useSpecularWorkflow" : int( useSpecularWorkflow ),
						}
					)
				},
				output = "previewSurface",
			)

			convertedNetwork = network.copy()
			IECoreArnold.ShaderNetworkAlgo.convertUSDShaders( convertedNetwork )
			convertedShader = convertedNetwork.getShader( "previewSurface" )

			if useSpecularWorkflow :
				self.assertEqual( convertedShader.parameters["specular_color"].value, imath.V3f( 0, 0.25, 0.5 ) )
				self.assertNotIn( "metalness", convertedShader.parameters )
			else :
				self.assertEqual( convertedShader.parameters["metalness"].value, 0.5 )
				self.assertNotIn( "specularColor", convertedShader.parameters )

			# Repeat with input connections

			network.addShader( "texture", IECoreScene.Shader( "UsdUVTexture" ) )
			network.addConnection( ( ( "texture", "rgb" ), ( "previewSurface", "specularColor" ) ) )
			network.addConnection( ( ( "texture", "r" ), ( "previewSurface", "metallic" ) ) )

			convertedNetwork = network.copy()
			IECoreArnold.ShaderNetworkAlgo.convertUSDShaders( convertedNetwork )

			if useSpecularWorkflow :
				self.assertEqual(
					convertedNetwork.input( ( "previewSurface", "specular_color" ) ),
					( "texture", "" ),
				)
				self.assertFalse( convertedNetwork.input( ( "previewSurface", "metalness" ) ) )
			else :
				self.assertEqual(
					convertedNetwork.input( ( "previewSurface", "metalness" ) ),
					( "texture", "r" ),
				)
				self.assertFalse( convertedNetwork.input( ( "previewSurface", "specular_color" ) ) )

			self.assertFalse( convertedNetwork.input( ( "previewSurface", "specularColor" ) ) )
			self.assertFalse( convertedNetwork.input( ( "previewSurface", "metallic" ) ) )

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
		IECoreArnold.ShaderNetworkAlgo.convertUSDShaders( convertedNetwork )
		convertedShader = convertedNetwork.getShader( "previewSurface" )

		self.assertEqual( convertedShader.parameters["coat"].value, 0.75 )
		self.assertEqual( convertedShader.parameters["coat_roughness"].value, 0.25 )

		# Repeat with input connections

		network.addShader( "texture", IECoreScene.Shader( "UsdUVTexture" ) )
		network.addConnection( ( ( "texture", "r" ), ( "previewSurface", "clearcoat" ) ) )
		network.addConnection( ( ( "texture", "g" ), ( "previewSurface", "clearcoatRoughness" ) ) )

		convertedNetwork = network.copy()
		IECoreArnold.ShaderNetworkAlgo.convertUSDShaders( convertedNetwork )

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

			IECoreArnold.ShaderNetworkAlgo.convertUSDShaders( network )

			self.assertEqual( network.input( ( "previewSurface", "base_color" ) ), "texture" )

			texture = network.getShader( "texture" )
			self.assertEqual( texture.name, "image" )
			self.assertEqual( texture.parameters["filename"].value, "test.png" )
			self.assertEqual( texture.parameters["color_space"].value, "auto" )
			self.assertEqual( texture.parameters["swrap"].value, "file" )
			self.assertEqual( texture.parameters["twrap"].value, "periodic" )

			# The obvious conversion of the network is to turn `uvReader`
			# into a `user_data_rgb` shader and plug that into `texture.uv_coords`,
			# but we go out of our way to avoid it. Arnold doesn't support derivatives
			# for `uv_coords`, which breaks texture filtering. So instead we need
			# to use the `uvset` parameter instead.

			self.assertEqual( len( network.shaders() ), 2 )
			self.assertIsNone( network.getShader( "uvReader" ) )
			self.assertEqual( texture.parameters["uvset"].value, uvPrimvar if uvPrimvar != "st" else "" )
			self.assertFalse( network.input( ( "texture", "uvcoords" ) ) )

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
						"wrapS" : "useMetadata",
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
		IECoreArnold.ShaderNetworkAlgo.convertUSDShaders( convertedNetwork )

		texture = convertedNetwork.getShader( "texture" )
		self.assertEqual( texture.name, "image" )
		self.assertEqual( texture.parameters["filename"].value, "test.png" )
		self.assertEqual( texture.parameters["color_space"].value, "auto" )
		self.assertEqual( texture.parameters["swrap"].value, "file" )
		self.assertEqual( texture.parameters["twrap"].value, "periodic" )

		uvReader = convertedNetwork.getShader( "uvReader" )
		self.assertEqual( uvReader.name, "utility" )
		self.assertEqual( uvReader.parameters["color_mode"].value, "uv" )
		self.assertEqual( uvReader.parameters["shade_mode"].value, "flat" )

		transform = convertedNetwork.getShader( "transform" )
		self.assertEqual( transform.name, "matrix_multiply_vector" )
		self.assertEqual( transform.parameters["matrix"].value, imath.M44f().rotate( imath.V3f( 0, 0, math.radians( 90 ) ) ) )

		self.assertEqual( convertedNetwork.input( ( "transform", "input" ) ), "uvReader" )
		# Note : connecting to `uvcoords` is terrible, because Arnold gives up on using
		# derivatives to filter the texture. But it's the only way to implement the intent of
		# the USD network using native Arnold shaders.
		## \todo Would we be better off writing some OSL shaders to implement all this?
		self.assertEqual( convertedNetwork.input( ( "texture", "uvcoords" ) ), "transform" )
		self.assertEqual( convertedNetwork.input( ( "previewSurface", "base_color" ) ), "texture" )

	def testConvertUSDPrimvarReader( self ) :

		for usdDataType, arnoldShaderType, usdFallback, arnoldDefault in [
			( "float", "user_data_float", 2.0, 2.0 ),
			( "float2", "user_data_rgb", imath.V2f( 1, 2 ), imath.Color3f( 1, 2, 0 ) ),
			( "float3", "user_data_rgb", imath.V3f( 1, 2, 3 ), imath.Color3f( 1, 2, 3 ) ),
			( "normal", "user_data_rgb", imath.V3f( 1, 2, 3 ), imath.Color3f( 1, 2, 3 ) ),
			( "point", "user_data_rgb", imath.V3f( 1, 2, 3 ), imath.Color3f( 1, 2, 3 ) ),
			( "vector", "user_data_rgb", imath.V3f( 1, 2, 3 ), imath.Color3f( 1, 2, 3 ) ),
			( "float4", "user_data_rgba", imath.Color4f( 1, 2, 3, 4 ), imath.Color4f( 1, 2, 3, 4 ) ),
			( "int", "user_data_int", 10, 10 ),
			( "string", "user_data_string", "hi", "hi" ),
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

			IECoreArnold.ShaderNetworkAlgo.convertUSDShaders( network )

			reader = network.getShader( "reader" )
			self.assertEqual( reader.name, arnoldShaderType )
			self.assertEqual( len( reader.parameters ), 2 )
			self.assertEqual( reader.parameters["attribute"].value, "test" )
			self.assertEqual( reader.parameters["default"].value, arnoldDefault )

	def testConvertUSDSphereLight( self ) :

		network = IECoreScene.ShaderNetwork(
			shaders = {
				"light" : IECoreScene.Shader(
					"SphereLight", "light",
					{
						"exposure" : 1.0,
						"intensity" : 2.0,
						"color" : imath.Color3f( 1, 2, 3 ),
						"diffuse" : 0.25,
						"specular" : 0.5,
						"normalize" : True,
						"radius" : 0.25,
						"unknown" : "unknown",
					}
				),
			},
			output = "light",
		)

		IECoreArnold.ShaderNetworkAlgo.convertUSDShaders( network )

		light = network.getShader( "light" )
		self.assertEqual( light.name, "point_light" )
		self.assertEqual( light.parameters["exposure"].value, 1.0 )
		self.assertEqual( light.parameters["intensity"].value, 2.0 )
		self.assertEqual( light.parameters["color"].value, imath.Color3f( 1, 2, 3 ) )
		self.assertEqual( light.parameters["diffuse"].value, 0.25 )
		self.assertEqual( light.parameters["specular"].value, 0.5 )
		self.assertEqual( light.parameters["normalize"].value, True )
		self.assertEqual( light.parameters["radius"].value, 0.25 )
		self.assertNotIn( "unknown", light.parameters )

	## \todo Register this via `unittest.addTypeEqualityFunc()`, once we've
	# ditched Python 2.
	def __assertShadersEqual( self, shader1, shader2, message = None ) :

		self.assertEqual( shader1.name, shader2.name, message )
		self.assertEqual( shader1.parameters.keys(), shader2.parameters.keys(), message )
		for k in shader1.parameters.keys() :
			self.assertEqual(
				shader1.parameters[k], shader2.parameters[k],
				"{}(Parameter = {})".format( message or "", k )
			)

	def testConvertUSDLights( self ) :

		def expectedLightParameters( parameters ) :

			# Start with defaults
			result = {
				"intensity" : 1.0,
				"exposure" : 0.0,
				"color" : imath.Color3f( 1, 1, 1 ),
				"diffuse" : 1.0,
				"specular" : 1.0,
				"normalize" : False,
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
						"diffuse" : 0.5,
						"specular" : 0.75,
						"radius" : 0.5,
						"normalize" : True,
					}
				),

				IECoreScene.Shader(
					"point_light", "light",
					expectedLightParameters( {
						"intensity" : 2.5,
						"exposure" : 1.1,
						"color" : imath.Color3f( 1, 2, 3 ),
						"diffuse" : 0.5,
						"specular" : 0.75,
						"radius" : 0.5,
						"normalize" : True,
					} )
				),

			],

			# Basic SphereLight -> point_light conversion, testing default values

			"defaultParameters" : [

				IECoreScene.Shader( "SphereLight", "light", {} ),

				IECoreScene.Shader(
					"point_light", "light",
					expectedLightParameters( {
						"radius" : 0.5,
					} )
				),

			],

			# SphereLight with `treatAsPoint = true`. We must normalize these
			# otherwise we lose all the energy in Arnold.

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
						"radius" : 0.0,
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
						"cone_angle" : 40.0,
						"penumbra_angle" : 20.0,
						"cosine_power" : 0.0,
						"radius" : 0.5,
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
						"cone_angle" : 40.0,
						"cosine_power" : 0.0,
						"radius" : 0.5,
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
						"vertices" : IECore.V3fVectorData( [
							imath.V3f( 10, 30, 0 ),
							imath.V3f( 10, -30, 0 ),
							imath.V3f( -10, -30, 0 ),
							imath.V3f( -10, 30, 0 ),
						] )
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

			# CylinderLight -> cylinder_light

			"cylinderLight" : [

				IECoreScene.Shader(
					"CylinderLight", "light",
					{
						"intensity" : 2.5,
						"exposure" : 1.1,
						"radius" : 0.5,
						"length" : 2.0,
						"normalize" : True,
					}
				),

				IECoreScene.Shader(
					"cylinder_light", "light",
					expectedLightParameters( {
						"intensity" : 2.5,
						"exposure" : 1.1,
						"radius" : 0.5,
						"top" : imath.V3f( 1, 0, 0 ),
						"bottom" : imath.V3f( -1, 0, 0 ),
						"normalize" : True,
					} )
				),

			],

			# CylinderLight with `treatAsLine = true`. We must normalize these
			# otherwise we lose all the energy in Arnold.

			"cylinderLight" : [

				IECoreScene.Shader(
					"CylinderLight", "light",
					{
						"radius" : 1.0,
						"length" : 2.0,
						"treatAsLine" : True,
					}
				),

				IECoreScene.Shader(
					"cylinder_light", "light",
					expectedLightParameters( {
						"radius" : 0.001,
						"top" : imath.V3f( 1, 0, 0 ),
						"bottom" : imath.V3f( -1, 0, 0 ),
						"normalize" : True,
					} )
				),

			],


		}.items() :

			network = IECoreScene.ShaderNetwork(
				shaders = {
					"light" : shaders[0],
				},
				output = "light",
			)

			IECoreArnold.ShaderNetworkAlgo.convertUSDShaders( network )

			light = network.getShader( "light" )
			self.__assertShadersEqual( network.getShader( "light" ), shaders[1], "Testing {}".format( testName ) )

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

		IECoreArnold.ShaderNetworkAlgo.convertUSDShaders( network )

		output = network.outputShader()
		self.assertEqual( output.name, "quad_light" )

		colorInput = network.input( ( "light", "color" ) )
		texture = network.getShader( colorInput.shader )
		self.assertEqual( texture.name, "image" )
		self.assertEqual( texture.parameters["filename"].value, "myFile.tx" )

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

		IECoreArnold.ShaderNetworkAlgo.convertUSDShaders( network )

		output = network.outputShader()
		self.assertEqual( output.name, "skydome_light" )
		self.assertEqual( output.parameters["format"].value, "mirrored_ball" )

		colorInput = network.input( ( "light", "color" ) )
		texture = network.getShader( colorInput.shader )
		self.assertEqual( texture.name, "image" )
		self.assertEqual( texture.parameters["filename"].value, "myFile.tx" )

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

		IECoreArnold.ShaderNetworkAlgo.convertUSDShaders( network )

		output = network.outputShader()
		self.assertEqual( output.name, "quad_light" )

		# When using a colour and a texture, we need to multiply
		# them together using a shader in Arnold.

		colorInput = network.input( ( "light", "color" ) )
		colorInputShader = network.getShader( colorInput.shader )
		self.assertEqual( colorInputShader.name, "multiply" )
		self.assertEqual( colorInputShader.parameters["input2"].value, imath.Color3f( 1, 2, 3 ) )

		colorInput1 = network.input( ( colorInput.shader, "input1" ) )
		texture = network.getShader( colorInput1.shader )
		self.assertEqual( texture.name, "image" )
		self.assertEqual( texture.parameters["filename"].value, "myFile.tx" )

if __name__ == "__main__":
	unittest.main()
