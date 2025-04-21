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
				"lightColor" : imath.Color3f( 1.0, 1.0, 1.0 ),
				"diffuse" : 1.0,
				"specular" : 1.0,
				"areaNormalize" : False,  # Common to all lights except DomeLight
				"enableTemperature" : False,
				"temperature" : 6500.0,
				"enableShadows" : True,
				"shadowColor" : imath.Color3f( 0.0, 0.0, 0.0 ),
				"shadowDistance" : -1.0,
				"shadowFalloff" : -1.0,
				"shadowFalloffGamma" : 1.0,
			}
			result.update( parameters )
			return result

		for testName, shaders in {

			# Basic SphereLight -> point_light conversion, testing default values

			"defaultParameters" : [

				IECoreScene.Shader( "SphereLight", "light", {} ),

				IECoreScene.Shader(
					"PxrSphereLight", "light",
					expectedLightParameters( {} )
				)

			],

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
						"enableColorTemperature" : True,
						"colorTemperature" : 5500.0,
						"ri:light:thinShadow" : False,
					}
				),

				IECoreScene.Shader(
					"PxrSphereLight", "light",
					expectedLightParameters( {
						"intensity" : 2.5,
						"exposure" : 1.1,
						"lightColor" : imath.Color3f( 1, 2, 3 ),
						"diffuse" : 0.5,
						"specular" : 0.75,
						"areaNormalize" : True,
						"enableTemperature" : True,
						"temperature" : 5500.0,
						"thinShadow" : False,
					} )
				),

			],

			"shadowAPI" : [

				IECoreScene.Shader(
					"SphereLight", "light",
					{
						"shadow:enable" : False,
						"shadow:color" : imath.V3f( 1.0, 0.0, 0.0 ),
						"shadow:distance" : 2.0,
						"shadow:falloff" : 3.0,
						"shadow:falloffGamma" : 0.5,
					}
				),

				IECoreScene.Shader(
					"PxrSphereLight", "light",
					expectedLightParameters( {
						"enableShadows" : False,
						"shadowColor" : imath.Color3f( 1.0, 0.0, 0.0 ),
						"shadowDistance" : 2.0,
						"shadowFalloff" : 3.0,
						"shadowFalloffGamma" : 0.5,
					} )
				),

			],

			"diskLight" : [

				IECoreScene.Shader(
					"DiskLight", "light",
					{
						"radius" : 2.0,
					}
				),

				IECoreScene.Shader( "PxrDiskLight", "light", expectedLightParameters( {} ) )

			],

			"rectLight" : [

				IECoreScene.Shader(
					"RectLight", "light",
					{
						"width" : 20.0,
						"height" : 60.0,
						"texture:file" : "test.tex",
					}
				),

				IECoreScene.Shader(
					"PxrRectLight", "light",
					expectedLightParameters( {
						"lightColorMap" : "test.tex",
					} )
				),

			],

			"rectLightNoTexture" : [

				IECoreScene.Shader(
					"RectLight", "light",
					{
						"width" : 20.0,
						"height" : 60.0,
					}
				),

				IECoreScene.Shader( "PxrRectLight", "light", expectedLightParameters( {} ) ),

			],

			"distantLightDefault" : [

				IECoreScene.Shader( "DistantLight", "light", {} ),

				IECoreScene.Shader(
					"PxrDistantLight", "light",
					expectedLightParameters( {
						"intensity" : 50000.0,
						"angleExtent" : 0.53,
					} )
				),
			],

			"distantLight" : [

				IECoreScene.Shader(
					"DistantLight", "light",
					{
						"intensity" : 11.0,
						"angle" : 2.0,
					}
				),

				IECoreScene.Shader(
					"PxrDistantLight", "light",
					expectedLightParameters( {
						"intensity" : 11.0,
						"angleExtent" : 2.0,
					} )
				)

			],

			"domeLight" : [

				IECoreScene.Shader(
					"DomeLight", "light",
					{
						"texture:file" : "test.tex",
						"texture:format" : "automatic",
					}
				),

				IECoreScene.Shader(
					"PxrDomeLight", "light",
					{
						k : v for k, v in expectedLightParameters( {
							"lightColorMap" : "test.tex"
						} ).items() if k != "areaNormalize"
					}
				),
			],

			"cylinderLight" : [

				IECoreScene.Shader(
					"CylinderLight", "light",
					{
						"length" : 2.0,
						"radius" : 4.0,
					}
				),

				IECoreScene.Shader(
					"PxrCylinderLight", "light",
					expectedLightParameters( {} )
				)
			],

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
						"areaNormalize" : True,
					} )
				),

			],

			"treatAsLine" : [

				IECoreScene.Shader(
					"CylinderLight", "light",
					{
						"treatAsLine" : True,
					}
				),

				IECoreScene.Shader(
					"PxrCylinderLight", "light",
					expectedLightParameters( {
						"areaNormalize" : True,
					} )
				),

			],

			"sphereLightToPhotometricLight" : [

				IECoreScene.Shader(
					"SphereLight", "light",
					{
						"shaping:ies:file" : "photometric.ies",
						"shaping:ies:angleScale" : 2.0,
						"shaping:ies:normalize" : True
					}
				),

				IECoreScene.Shader(
					"PxrSphereLight", "light",
					expectedLightParameters( {
						"iesProfile" : "photometric.ies",
						"iesProfileScale" : 2.0,
						"iesProfileNormalize" : True,
					} )
				),

			],

			"sphereLightToPhotometricLightEmptyProfile" : [

				IECoreScene.Shader(
					"SphereLight", "light",
					{
						"shaping:ies:file" : "",
						"shaping:ies:angleScale" : 2.0,
						"shaping:ies:normalize" : True,
					}
				),

				IECoreScene.Shader( "PxrSphereLight", "light", expectedLightParameters( {} ) ),

			],

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

			"sphereLightToPhotoMetricAndSpot" : [

				IECoreScene.Shader(
					"SphereLight", "light",
					{
						"shaping:ies:file" : "photometric.ies",
						"shaping:ies:angleScale" : 2.0,
						"shaping:ies:normalize" : True,
						"shaping:cone:angle" : 20.0,
						"shaping:cone:softness" : 0.5,
					}
				),

				IECoreScene.Shader(
					"PxrSphereLight", "light",
					expectedLightParameters( {
						"iesProfile" : "photometric.ies",
						"iesProfileScale" : 2.0,
						"iesProfileNormalize" : True,
						"coneAngle" : 20.0,
						"coneSoftness" : 0.5,
					} )
				),

			],

		}.items() :
			with self.subTest( testName = testName ) :

				network = IECoreScene.ShaderNetwork(
					shaders = {
						"light" : shaders[0],
					},
					output = "light"
				)

				IECoreRenderMan.ShaderNetworkAlgo.convertUSDShaders( network )

				self.__assertShadersEqual( network.getShader( "light" ), shaders[1], "Testing {}".format( testName ) )

	def testUSDLightTransform( self ) :

		for shader, transform in {

			IECoreScene.Shader( "SphereLight", "light", { "radius" : 2.0 } ) : imath.M44f().scale( imath.V3f( 4.0 ) ),
			IECoreScene.Shader( "RectLight", "light", { "width" : 20.0, "height" : 60.0 } ) : imath.M44f().scale( imath.V3f( 20.0, 60.0, 1.0 ) ),
			IECoreScene.Shader( "DiskLight", "light", { "radius" : 2.0 } ) : imath.M44f().scale( imath.V3f( 4.0 ) ),
			IECoreScene.Shader( "DistantLight", "light", { "angle" : 2.0 } ) : imath.M44f(),
			IECoreScene.Shader( "DomeLight", "light", {} ) : imath.M44f(),
			IECoreScene.Shader( "CylinderLight", "light", { "length" : 2.0, "radius" : 4.0 } ) : imath.M44f().scale( imath.V3f( 2.0, 8.0, 8.0 ) ),
			IECoreScene.Shader( "SphereLight", "light", { "treatAsPoint" : True } ) : imath.M44f().scale( imath.V3f( 0.002 ) ),
			IECoreScene.Shader( "CylinderLight", "light", { "treatAsLine" : True } ) : imath.M44f().scale( imath.V3f( 1.0, 0.002, 0.002 ) ),

		}.items() :
			with self.subTest() :

				self.assertEqual(
					IECoreRenderMan.ShaderNetworkAlgo.usdLightTransform( shader ),
					transform,
					"Testing {}".format( shader.name )
				)

	def testDomeLightNotAutomatic( self ) :

		shaderNetwork = IECoreScene.ShaderNetwork(
			shaders = {
				"light" : IECoreScene.Shader(
					"DomeLight", "light",
					{
						"texture:format" : "latlong",
					}
				)
			},
			output = "light",
		)

		with IECore.CapturingMessageHandler() as mh :
			IECoreRenderMan.ShaderNetworkAlgo.convertUSDShaders( shaderNetwork )
			self.assertEqual( len( mh.messages ), 1 )
			self.assertEqual( mh.messages[0].level, mh.Level.Warning )
			self.assertEqual(
				mh.messages[0].message,
				"Unsupported value \"latlong\" for DomeLight.format. Only \"automatic\" is supported. Format will be read from texture file."
			)

	def __assertShadersEqual( self, shader1, shader2, message = None ) :

		self.assertEqual( shader1.name, shader2.name, message )
		self.assertEqual( shader1.parameters.keys(), shader2.parameters.keys(), message )
		for k in shader1.parameters.keys() :
			self.assertEqual(
				shader1.parameters[k], shader2.parameters[k],
				"{}(Parameter = {})".format( message or "", k )
			)


if __name__ == "__main__" :
	unittest.main()
