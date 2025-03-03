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


if __name__ == "__main__" :
	unittest.main()
