##########################################################################
#
#  Copyright (c) 2018, John Haddon. All rights reserved.
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

import Gaffer
import GafferScene
import GafferSceneTest
import GafferOSL
import GafferRenderMan

class RenderManShaderTest( GafferSceneTest.SceneTestCase ) :

	def testBasicLoading( self ) :

		shader = GafferRenderMan.RenderManShader()
		shader.loadShader( "PxrConstant" )

		self.assertEqual( shader["name"].getValue(), "PxrConstant" )
		self.assertEqual( shader["type"].getValue(), "ri:surface" )

		self.assertEqual( shader["parameters"].keys(), [ "emitColor", "presence" ] )

		self.assertIsInstance( shader["parameters"]["emitColor"], Gaffer.Color3fPlug )
		self.assertIsInstance( shader["parameters"]["presence"], Gaffer.FloatPlug )

		self.assertEqual( shader["parameters"]["emitColor"].defaultValue(), imath.Color3f( 1 ) )
		self.assertEqual( shader["parameters"]["presence"].defaultValue(), 1.0 )
		self.assertEqual( shader["parameters"]["presence"].minValue(), 0.0 )
		self.assertEqual( shader["parameters"]["presence"].maxValue(), 1.0 )

	def testLoadParametersInsidePages( self ) :

		shader = GafferRenderMan.RenderManShader()
		shader.loadShader( "PxrVolume" )

		self.assertIn( "extinctionDistance", shader["parameters"] )
		self.assertIn( "densityColor", shader["parameters"] )

	def testLoadRemovesUnnecessaryParameters( self ) :

		for keepExisting in ( True, False ) :

			shader = GafferRenderMan.RenderManShader()
			shader.loadShader( "PxrDiffuse" )
			self.assertIn( "diffuseColor", shader["parameters"] )

			shader.loadShader( "PxrConstant", keepExistingValues = keepExisting )
			self.assertNotIn( "color1", shader["parameters"] )
			self.assertIn( "emitColor", shader["parameters"] )

	def testLoadOutputs( self ) :

		shader = GafferRenderMan.RenderManShader()
		shader.loadShader( "PxrSeExpr" )

		self.assertIn( "resultRGB", shader["out"] )
		self.assertIsInstance( shader["out"]["resultRGB"], Gaffer.Color3fPlug )

		self.assertIn( "resultR", shader["out"] )
		self.assertIsInstance( shader["out"]["resultR"], Gaffer.FloatPlug )

		self.assertIn( "resultG", shader["out"] )
		self.assertIsInstance( shader["out"]["resultG"], Gaffer.FloatPlug )

		self.assertIn( "resultB", shader["out"] )
		self.assertIsInstance( shader["out"]["resultB"], Gaffer.FloatPlug )

	## IECoreUSD isn't round-tripping the shader type correctly yet.
	@unittest.expectedFailure
	def testUSDRoundTrip( self ) :

		texture = GafferOSL.OSLShader( "PxrTexture" )
		texture.loadShader( "PxrTexture" )
		texture["parameters"]["filename"].setValue( "test.tx" )

		surface = GafferRenderMan.RenderManShader( "PxrSurface" )
		surface.loadShader( "PxrSurface" )
		surface["parameters"]["diffuseColor"].setInput( texture["out"]["resultRGB"] )
		surface["parameters"]["diffuseGain"].setValue( 0.5 )

		plane = GafferScene.Plane()

		shaderAssignment = GafferScene.ShaderAssignment()
		shaderAssignment["in"].setInput( plane["out"] )
		shaderAssignment["shader"].setInput( surface["out"] )

		sceneWriter = GafferScene.SceneWriter()
		sceneWriter["in"].setInput( shaderAssignment["out"] )
		sceneWriter["fileName"].setValue( self.temporaryDirectory() / "test.usda" )
		sceneWriter["task"].execute()

		sceneReader = GafferScene.SceneReader()
		sceneReader["fileName"].setInput( sceneWriter["fileName"] )

		self.assertShaderNetworksEqual(
			sceneReader["out"].attributes( "/plane" )["ri:surface"],
			sceneWriter["in"].attributes( "/plane" )["ri:surface"]
		)

	def testKeepExistingValues( self ) :

		shader = GafferRenderMan.RenderManShader()
		shader.loadShader( "PxrSurface" )
		defaultValues = { p.getName() : p.getValue() for p in shader["parameters"] if hasattr( p, "getValue" ) }

		shader["parameters"]["diffuseGain"].setValue( 0.25 )
		shader["parameters"]["diffuseColor"].setValue( imath.Color3f( 1, 2, 3 ) )
		shader["parameters"]["specularDoubleSided"].setValue( True )
		shader["parameters"]["volumeAggregateName"].setValue( "test" )
		modifiedValues = { p.getName() : p.getValue() for p in shader["parameters"] if hasattr( p, "getValue" ) }

		shader.loadShader( "PxrSurface", keepExistingValues = True )
		self.assertEqual(
			{ p.getName() : p.getValue() for p in shader["parameters"] if hasattr( p, "getValue" ) },
			modifiedValues
		)

		shader.loadShader( "PxrSurface", keepExistingValues = False )
		self.assertEqual(
			{ p.getName() : p.getValue() for p in shader["parameters"] if hasattr( p, "getValue" ) },
			defaultValues
		)

	def testDisplacementShaderType( self ) :

		shader = GafferRenderMan.RenderManShader()
		shader.loadShader( "PxrDisplace" )
		self.assertEqual( shader["type"].getValue(), "ri:displacement" )

		shader = GafferOSL.OSLShader()
		shader.loadShader( "PxrDisplace" )
		self.assertEqual( shader["type"].getValue(), "osl:displacement" )

	def testUtilityPatternArray( self ) :

		shader = GafferRenderMan.RenderManShader()
		shader.loadShader( "PxrSurface" )

		self.assertIn( "utilityPattern", shader["parameters"] )
		self.assertIsInstance( shader["parameters"]["utilityPattern"], Gaffer.ArrayPlug )
		self.assertIsInstance( shader["parameters"]["utilityPattern"].elementPrototype(), Gaffer.IntPlug )

if __name__ == "__main__":
	unittest.main()
