##########################################################################
#
#  Copyright (c) 2025, Cinesite VFX Ltd. All rights reserved.
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

import imath

import IECore
import IECoreScene
import IECoreRenderMan

class ShaderNetworkAlgoTest( unittest.TestCase ) :

	def testUSDPreviewSurface( self ) :

		parameters = {
			"diffuseColor" : IECore.Color3fData( imath.Color3f( 0.1, 0.2, 0.3 ) ),
			"emissiveColor" : IECore.Color3fData( imath.Color3f( 0.4, 0.5, 0.6 ) ),
			"useSpecularWorkflow" : 1,
			"specularColor" : IECore.Color3fData( imath.Color3f( 0.7, 0.8, 0.9 ) ),
			"metallic" : 0.5,
			"roughness" : 0.375,
			"clearcoat" : 0.25,
			"clearcoatRoughness" : 0.75,
			"opacity" : 0.625,
			"opacityThreshold" : 0.875,
			"ior" : 1.25,
			"normal" : IECore.V3fData( imath.V3f( 0.1, 0.2, 0.3 ) ),
			"occlusion" : 0.5625,
		}

		network = IECoreScene.ShaderNetwork(
			shaders = {
				"previewSurface" : IECoreScene.Shader(
					"UsdPreviewSurface", "surface", parameters
				)
			},
			output = "previewSurface"
		)

		IECoreRenderMan.ShaderNetworkAlgo.convertUSDShaders( network )

		self.assertEqual( len( network ), 2 )

		convertedShader = network.getShader( "previewSurface" )
		self.assertEqual( convertedShader.name, "__usd/__UsdPreviewSurfaceParameters" )
		self.assertEqual( convertedShader.type, "osl:shader" )

		self.assertEqual( convertedShader.parameters["diffuseColor"].value, imath.Color3f( 0.1, 0.2, 0.3 ) )
		self.assertEqual( convertedShader.parameters["emissiveColor"].value, imath.Color3f( 0.4, 0.5, 0.6 ) )
		self.assertEqual( convertedShader.parameters["useSpecularWorkflow"].value, 1 )
		self.assertEqual( convertedShader.parameters["specularColor"].value, imath.Color3f( 0.7, 0.8, 0.9 ) )
		self.assertEqual( convertedShader.parameters["metallic"].value, 0.5 )
		self.assertEqual( convertedShader.parameters["roughness"].value, 0.375 )
		self.assertEqual( convertedShader.parameters["clearcoat"].value, 0.25 )
		self.assertEqual( convertedShader.parameters["clearcoatRoughness"].value, 0.75 )
		self.assertEqual( convertedShader.parameters["opacity"].value, 0.625 )
		self.assertEqual( convertedShader.parameters["opacityThreshold"].value, 0.875 )
		self.assertEqual( convertedShader.parameters["ior"].value, 1.25 )
		self.assertNotIn( "normal", convertedShader.parameters )
		self.assertEqual( convertedShader.parameters["normalIn"].value, imath.V3f( 0.1, 0.2, 0.3 ) )
		self.assertEqual( convertedShader.parameters["occlusion"].value, 0.5625 )

		convertedSurface = network.getShader( "previewSurfacePxrSurface" )
		self.assertEqual( convertedSurface.name, "PxrSurface" )
		self.assertEqual( convertedSurface.type, "ri:surface" )

		self.assertEqual( convertedSurface.parameters["specularModelType"].value, 1 )
		self.assertEqual( convertedSurface.parameters["diffuseDoubleSided"].value, 1 )
		self.assertEqual( convertedSurface.parameters["specularDoubleSided"].value, 1 )
		self.assertEqual( convertedSurface.parameters["roughSpecularDoubleSided"].value, 1 )
		self.assertEqual( convertedSurface.parameters["clearcoatDoubleSided"].value, 1 )

		for pxrSurfaceIn in [
			"diffuseGain",
			"diffuseColor",
			"specularFaceColor",
			"specularEdgeColor",
			"specularRoughness",
			"specularIor",
			"clearcoatFaceColor",
			"clearcoatEdgeColor",
			"clearcoatRoughness",
			"glowGain",
			"glowColor",
			"bumpNormal",
			"glassIor",
			"glassRoughness",
			"refractionGain",
			"presence",
		] :
			self.assertEqual( network.input( ( "previewSurfacePxrSurface", pxrSurfaceIn ) ), ( "previewSurface", pxrSurfaceIn + "Out" ) )

		self.assertEqual( network.getOutput(), ( "previewSurfacePxrSurface", "" ) )

	def testConvertUSDPrimvarReader( self ) :

		for usdDataType, fallback, riType, riDefaultParameter, riDefault, readerOut, surfaceIn in [
			( "float", 2.0, "float", "defaultFloat", 2.0, "resultF", "metallic" ),
			( "float2", imath.V2f( 1, 2 ), "float2", "defaultFloat3", imath.Color3f( 1, 2, 0 ), "resultRGB", "diffuseColor" ),
			( "float3", imath.V3f( 1, 2, 3 ), "vector", "defaultFloat3", imath.Color3f( 1, 2, 3 ), "resultRGB", "diffuseColor" ),
			( "normal", imath.V3f( 1, 2, 3 ), "normal", "defaultFloat3", imath.Color3f( 1, 2, 3 ), "resultRGB", "diffuseColor" ),
			( "point", imath.V3f( 1, 2, 3 ), "point", "defaultFloat3", imath.Color3f( 1, 2, 3 ), "resultRGB", "diffuseColor" ),
			( "vector", imath.V3f( 1, 2, 3 ), "vector", "defaultFloat3", imath.Color3f( 1, 2, 3 ), "resultRGB", "diffuseColor" ),
			( "int", 10, "int", "defaultInt", 10, "resultI", "metallic" ),
		] :
			with self.subTest( usdDataType = usdDataType, fallback = fallback, riType = riType, riDefaultParameter = riDefaultParameter, riDefault = riDefault, readerOut = readerOut, surfaceIn = surfaceIn ) :
				network = IECoreScene.ShaderNetwork(
					shaders = {
						"previewSurface" : IECoreScene.Shader( "UsdPreviewSurface" ),
						"reader" : IECoreScene.Shader(
							"UsdPrimvarReader_{}".format( usdDataType ), "shader",
							{
								"varname" : "test",
								"fallback" : fallback,
							}
						),
					},
					connections = [
						( ( "reader", readerOut ), ( "previewSurface", surfaceIn ) ),
					],
					output = "previewSurface",
				)

				IECoreRenderMan.ShaderNetworkAlgo.convertUSDShaders( network )

				reader = network.getShader( "reader" )
				self.assertEqual( reader.name, "PxrAttribute" )
				self.assertEqual( len( reader.parameters ), 3 )
				self.assertEqual( reader.parameters["varname"].value, "test" )
				self.assertEqual( reader.parameters["type"].value, riType )
				if riDefaultParameter is not None :
					self.assertEqual( reader.parameters[riDefaultParameter].value, riDefault )

				self.assertEqual( network.input( ( "previewSurface", surfaceIn ) ), ( "reader", readerOut ) )

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
				"enableShadows" : True,
				"shadowColor" : imath.Color3f( 0 ),
			}
			result.update( parameters )
			return result

		for testName, shaders in {

			# Basic SphereLight -> PxrSphereLight conversion

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
						"ri:light:lightgroup" : "test", # todo: get the right name
						"ri:light:samples" : 3, # todo: get the right name
					}
				),

				IECoreScene.Shader(
					"PxrSphereLight", "light",
					expectedLightParameters( {
						"intensity" : 2.5,
						"exposure" : 1.1,
						"color" : imath.Color3f( 1, 2, 3 ),
						"diffuse" : 0.5,
						"specular" : 0.75,
						# TODO: Check xform differences
						"normalize" : True,
						"lightgroup" : "test", # todo: get the right name
						"samples" : 3, # todo: get the right name
					} )
				),

			],

			# Basic SphereLight -> PxrSphereLight conversion, testing default values

			"defaultParameters" : [

				IECoreScene.Shader( "SphereLight", "light", {} ),

				IECoreScene.Shader(
					"PxrSphereLight", "light",
					expectedLightParameters( {
						# TODO: Check xform differences
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
					"PxrSphereLight", "light",
					expectedLightParameters( {
						# TODO: Check xform differences
						"normalize" : True,
					} )
				),

			],

			# SphereLight (with shaping) -> PxrSphereLight conversion

			"sphereLightToSpotLight" : [

				IECoreScene.Shader(
					"SphereLight", "light",
					{
						"shaping:cone:angle" : 20.0,
						"shaping:cone:softness" : 0.5,
					}
				),

				IECoreScene.Shader(
					"PxrSphereLight", "light",
					expectedLightParameters( {
						"coneAngle" : 20.0,
						"coneSoftness" : 0.5,
					} )
				),

			],

			# RectLight -> PxrRectLight, with USD default width and height

			"rectLight" : [

				IECoreScene.Shader( "RectLight", "light", {} ),

				IECoreScene.Shader(
					"PxrRectLight", "light",
					expectedLightParameters( {
						# TODO: Check xform differences
					} )
				),

			],

			# RectLight -> PxrRectLight

			"rectLight" : [

				IECoreScene.Shader(
					"RectLight", "light",
					{
						"width" : 20.0,
						"height" : 60.0,
					}
				),

				IECoreScene.Shader(
					"PxrRectLight", "light",
					expectedLightParameters( {
						# TODO: Check xform differences
					} )
				),

			],

			# DistantLight -> PxrDistantLight

			"distantLight" : [

				IECoreScene.Shader(
					"DistantLight", "light",
					{
						"angle" : 1.0,
					}
				),

				IECoreScene.Shader(
					"PxrDistantLight", "light",
					expectedLightParameters( {
						"angleExtent" : 1.0
					} )
				),

			],

			# CylinderLight -> PxrCylinderLight

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
					"PxrCylinderLight", "light",
					expectedLightParameters( {
						"intensity" : 2.5,
						"exposure" : 1.1,
						"normalize" : True,
					} )
				),

			],

			# CylinderLight with `treatAsLine = true`.

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
					"PxrCylinderLight", "light",
					expectedLightParameters( {
						"normalize" : True,
					} )
				),

			],

			# SphereLight with ShadowAPI parameters.

			"shadowAPI" : [

				IECoreScene.Shader(
					"SphereLight", "light",
					{
						"shadow:enable" : False,
						"shadow:color" : imath.V3f( 1, 0, 0 ),
					}
				),

				IECoreScene.Shader(
					"PxrSphereLight", "light",
					expectedLightParameters( {
						"enableShadows" : False,
						"shadowColor" : imath.Color3f( 1, 0, 0 ),
					} )
				),

			],

		}.items() :

			with self.subTest( testName = testName ) :

				network = IECoreScene.ShaderNetwork(
					shaders = {
						"light" : shaders[0],
					},
					output = "light",
				)

				IECoreRenderMan.ShaderNetworkAlgo.convertUSDShaders( network )

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

		IECoreRenderMan.ShaderNetworkAlgo.convertUSDShaders( network )

		output = network.outputShader()
		self.assertEqual( output.name, "PxrRectLight" )
		self.assertEqual( output.parameters["lightColorMap"].value, "myFile.tx" )

	def testConvertUSDDomeLightTexture( self ) :

		network = IECoreScene.ShaderNetwork(
			shaders = {
				"light" : IECoreScene.Shader(
					"DomeLight", "light",
					{
						"texture:file" : "myFile.tx",
					}
				)
			},
			output = "light"
		)

		IECoreRenderMan.ShaderNetworkAlgo.convertUSDShaders( network )

		output = network.outputShader()
		self.assertEqual( output.name, "PxrDomeLight" )
		self.assertEqual( output.parameters["lightColorMap"].value, "myFile.tx" )

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

		IECoreRenderMan.ShaderNetworkAlgo.convertUSDShaders( network )

		output = network.outputShader()
		self.assertEqual( output.name, "PxrRectLight" )
		self.assertEqual( output.parameters["lightColorMap"].value, "myFile.tx" )
		self.assertEqual( output.parameters["lightColor"].value, imath.Color3f( 1, 2, 3 ) )


if __name__ == "__main__" :
	unittest.main()
