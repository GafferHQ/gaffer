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
			( "int", 10, "int", "defaultInt", 10, "resultF", "metallic" ),
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
				self.assertEqual( reader.name, "PxrPrimvar" )
				self.assertEqual( len( reader.parameters ), 3 )
				self.assertEqual( reader.parameters["varname"].value, "test" )
				self.assertEqual( reader.parameters["type"].value, riType )
				if riDefaultParameter is not None :
					self.assertEqual( reader.parameters[riDefaultParameter].value, riDefault )

				self.assertEqual( network.input( ( "previewSurface", surfaceIn ) ), ( "reader", readerOut ) )


if __name__ == "__main__" :
	unittest.main()
