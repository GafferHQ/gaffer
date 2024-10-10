##########################################################################
#
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
#      * Neither the name of Image Engine Design Inc nor the names of
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

import Gaffer
import GafferUSD
import GafferScene
import GafferSceneTest

class USDShaderTest( GafferSceneTest.SceneTestCase ) :

	def __assertShaderLoads( self, name, expectedParameters, expectedOutputs ) :

		shader = GafferUSD.USDShader()
		shader.loadShader( name )
		self.assertEqual( shader["name"].getValue(), name )

		for parent, expected in {
			shader["parameters"] : expectedParameters,
			shader["out"] : expectedOutputs
		}.items() :

			allNames = set()
			for name, plugType, defaultValue in expected :
				with self.subTest( name = name ) :
					self.assertIn( name, parent )
					plug = parent[name]
					self.assertIs( type( plug ), plugType )
					self.assertEqual( plug.direction(), parent.direction() )
					self.assertEqual( plug.getFlags(), Gaffer.Plug.Flags.Default )
					if defaultValue is not None :
						self.assertEqual( plug.defaultValue(), defaultValue )
					else :
						self.assertFalse( hasattr( plug, "defaultValue" ) )
					allNames.add( name )

			## \todo Assert that order is also what we expect, if we can get USD
			# to preserve order in the first place.
			# See https://github.com/PixarAnimationStudios/OpenUSD/pull/2497.
			self.assertEqual( set( parent.keys() ), allNames )

	def testLoadUsdPreviewSurface( self ) :

		self.__assertShaderLoads(
			"UsdPreviewSurface",
			[
				( "diffuseColor", Gaffer.Color3fPlug, imath.Color3f( 0.18 ) ),
				( "emissiveColor", Gaffer.Color3fPlug, imath.Color3f( 0 ) ),
				( "useSpecularWorkflow", Gaffer.IntPlug, 0 ),
				( "specularColor", Gaffer.Color3fPlug, imath.Color3f( 0 ) ),
				( "metallic", Gaffer.FloatPlug, 0 ),
				( "roughness", Gaffer.FloatPlug, 0.5 ),
				( "clearcoat", Gaffer.FloatPlug, 0 ),
				( "clearcoatRoughness", Gaffer.FloatPlug, 0.009999999776482582 ),
				( "opacity", Gaffer.FloatPlug, 1 ),
				( "opacityThreshold", Gaffer.FloatPlug, 0 ),
				( "ior", Gaffer.FloatPlug, 1.5 ),
				( "normal", Gaffer.V3fPlug, imath.V3f( 0, 0, 1 ) ),
				( "displacement", Gaffer.FloatPlug, 0 ),
				( "occlusion", Gaffer.FloatPlug, 1 ),
			],
			[
				( "surface", Gaffer.Plug, None ),
				( "displacement", Gaffer.Plug, None ),
			]
		)

	def testLoadUsdPrimvarReader( self ) :

		self.__assertShaderLoads(
			"UsdPrimvarReader_float",
			[
				( "varname", Gaffer.StringPlug, "" ),
				( "fallback", Gaffer.FloatPlug, 0 ),
			],
			[
				( "result", Gaffer.FloatPlug, 0 ),
			]
		)

	def testLoadUsdUVTexture( self ) :

		self.__assertShaderLoads(
			"UsdUVTexture",
			[
				( "file", Gaffer.StringPlug, "" ),
				( "st", Gaffer.V2fPlug, imath.V2f( 0 ) ),
				( "wrapS", Gaffer.StringPlug, "useMetadata" ),
				( "wrapT", Gaffer.StringPlug, "useMetadata" ),
				( "fallback", Gaffer.Color4fPlug, imath.Color4f( 0, 0, 0, 1 ) ),
				( "scale", Gaffer.Color4fPlug, imath.Color4f( 1 ) ),
				( "bias", Gaffer.Color4fPlug, imath.Color4f( 0 ) ),
				( "sourceColorSpace", Gaffer.StringPlug, "auto" ),
			],
			[
				( "r", Gaffer.FloatPlug, 0 ),
				( "g", Gaffer.FloatPlug, 0 ),
				( "b", Gaffer.FloatPlug, 0 ),
				( "a", Gaffer.FloatPlug, 0 ),
				( "rgb", Gaffer.V3fPlug, imath.V3f( 0 ) ),
			]
		)

	def testKeepExistingValues( self ) :

		shader = GafferUSD.USDShader()
		shader.loadShader( "UsdPrimvarReader_float" )

		shader["parameters"]["fallback"].setValue( 1 )
		shader.loadShader( "UsdPrimvarReader_float", keepExistingValues = True )
		self.assertEqual( shader["parameters"]["fallback"].getValue(), 1 )

		shader.loadShader( "UsdPrimvarReader_float", keepExistingValues = False )
		self.assertEqual( shader["parameters"]["fallback"].getValue(), 0 )

	def testLoadDifferentShader( self ) :

		for keepExistingValues in [ True, False ] :
			with self.subTest( keepExistingValues = keepExistingValues ) :

				shader = GafferUSD.USDShader()
				shader.loadShader( "UsdPreviewSurface" )
				self.assertIn( "diffuseColor", shader["parameters"] )

				shader.loadShader( "UsdPrimvarReader_float", keepExistingValues = keepExistingValues )
				self.assertEqual( set( shader["parameters"].keys() ), { "varname", "fallback" } )

	def testMissingShader( self ) :

		shader = GafferUSD.USDShader()
		with self.assertRaisesRegex( RuntimeError, "Shader \"missing\" not found in SdrRegistry" ) :
			shader.loadShader( "missing" )

	def testGeometricInterpretation( self ) :

		for interpretation in [ "Normal", "Point", "Vector" ] :
			with self.subTest( interpretation = interpretation ) :

				shader = GafferUSD.USDShader()
				shader.loadShader( "UsdPrimvarReader_{}".format( interpretation.lower() ) )

				self.assertEqual(
					shader["parameters"]["fallback"].interpretation(),
					getattr( IECore.GeometricData.Interpretation, interpretation )
				)

	def testSerialisation( self ) :

		script = Gaffer.ScriptNode()
		script["shader"] = GafferUSD.USDShader()
		script["shader"].loadShader( "UsdPrimvarReader_float" )
		script["shader"]["parameters"]["fallback"].setValue( 10 )

		script2 = Gaffer.ScriptNode()
		script2.execute( script.serialise() )
		self.assertEqual( script2["shader"]["name"].getValue(), script["shader"]["name"].getValue() )
		self.assertEqual( script2["shader"]["type"].getValue(), script["shader"]["type"].getValue() )
		self.assertEqual( script2["shader"]["parameters"].keys(), script["shader"]["parameters"].keys() )
		self.assertEqual( script2["shader"]["parameters"]["fallback"].getValue(), script["shader"]["parameters"]["fallback"].getValue() )

	def testShaderNetwork( self ) :

		uvReader = GafferUSD.USDShader( "uvReader" )
		uvReader.loadShader( "UsdPrimvarReader_float2" )

		transform2D = GafferUSD.USDShader( "transform2D" )
		transform2D.loadShader( "UsdTransform2d" )
		transform2D["parameters"]["in"].setInput( uvReader["out"]["result"] )
		transform2D["parameters"]["scale"].setValue( imath.V2f( 2, 3 ) )

		texture = GafferUSD.USDShader( "texture" )
		texture.loadShader( "UsdUVTexture" )
		texture["parameters"]["file"].setValue( "test.tx" )
		texture["parameters"]["st"].setInput( transform2D["out"]["result"] )

		surface = GafferUSD.USDShader( "surface" )
		surface.loadShader( "UsdPreviewSurface" )
		surface["parameters"]["diffuseColor"].setInput( texture["out"]["rgb"] )

		shaderPlug = GafferScene.ShaderPlug()
		shaderPlug.setInput( surface["out"]["surface"] )

		network = shaderPlug.attributes()["surface"]
		self.assertIsInstance( network, IECoreScene.ShaderNetwork )

		self.assertEqual( network.getOutput(), ( "surface", "surface" ) )
		self.assertEqual(
			network.inputConnections( "surface" ),
			[ ( ( "texture", "rgb" ), ( "surface", "diffuseColor" ) ) ]
		)
		self.assertEqual(
			network.inputConnections( "texture" ),
			[ ( ( "transform2D", "result" ), ( "texture", "st" ) ) ]
		)
		self.assertEqual(
			network.inputConnections( "transform2D" ),
			[ ( ( "uvReader", "result" ), ( "transform2D", "in" ) ) ]
		)

	def testUsdPreviewSurfaceAssignment( self ) :

		sphere = GafferScene.Sphere()

		shader = GafferUSD.USDShader()
		shader.loadShader( "UsdPreviewSurface" )

		sphereFilter = GafferScene.PathFilter()
		sphereFilter["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )

		shaderAssignment = GafferScene.ShaderAssignment()
		shaderAssignment["in"].setInput( sphere["out"] )
		shaderAssignment["filter"].setInput( sphereFilter["out"] )
		shaderAssignment["shader"].setInput( shader["out"]["surface"] )

		self.assertEqual( shaderAssignment["out"].attributes( "/sphere" ).keys(), [ "surface" ] )
		self.assertIsInstance( shaderAssignment["out"].attributes( "/sphere" )["surface"], IECoreScene.ShaderNetwork )

		shaderAssignment["shader"].setInput( shader["out"]["displacement"] )
		self.assertEqual( shaderAssignment["out"].attributes( "/sphere" ).keys(), [ "displacement" ] )
		self.assertIsInstance( shaderAssignment["out"].attributes( "/sphere" )["displacement"], IECoreScene.ShaderNetwork )

	def testMtlxSurfaceAssignment( self ) :

		sphere = GafferScene.Sphere()

		shader = GafferUSD.USDShader()
		shader.loadShader( "ND_surface" )

		sphereFilter = GafferScene.PathFilter()
		sphereFilter["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )

		shaderAssignment = GafferScene.ShaderAssignment()
		shaderAssignment["in"].setInput( sphere["out"] )
		shaderAssignment["filter"].setInput( sphereFilter["out"] )
		shaderAssignment["shader"].setInput( shader["out"]["out"] )

		self.assertEqual( shaderAssignment["out"].attributes( "/sphere" ).keys(), [ "mtlx:surface" ] )
		self.assertIsInstance( shaderAssignment["out"].attributes( "/sphere" )["mtlx:surface"], IECoreScene.ShaderNetwork )

	def testMtlxDisplacementAssignment( self ) :

		sphere = GafferScene.Sphere()

		shader = GafferUSD.USDShader()
		shader.loadShader( "ND_displacement_float" )

		sphereFilter = GafferScene.PathFilter()
		sphereFilter["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )

		shaderAssignment = GafferScene.ShaderAssignment()
		shaderAssignment["in"].setInput( sphere["out"] )
		shaderAssignment["filter"].setInput( sphereFilter["out"] )
		shaderAssignment["shader"].setInput( shader["out"]["out"] )

		self.assertEqual( shaderAssignment["out"].attributes( "/sphere" ).keys(), [ "mtlx:displacement" ] )
		self.assertIsInstance( shaderAssignment["out"].attributes( "/sphere" )["mtlx:displacement"], IECoreScene.ShaderNetwork )

	def testMtlxVolumeAssignment( self ) :

		sphere = GafferScene.Sphere()

		shader = GafferUSD.USDShader()
		shader.loadShader( "ND_volume" )

		sphereFilter = GafferScene.PathFilter()
		sphereFilter["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )

		shaderAssignment = GafferScene.ShaderAssignment()
		shaderAssignment["in"].setInput( sphere["out"] )
		shaderAssignment["filter"].setInput( sphereFilter["out"] )
		shaderAssignment["shader"].setInput( shader["out"]["out"] )

		self.assertEqual( shaderAssignment["out"].attributes( "/sphere" ).keys(), [ "mtlx:volume" ] )
		self.assertIsInstance( shaderAssignment["out"].attributes( "/sphere" )["mtlx:volume"], IECoreScene.ShaderNetwork )

if __name__ == "__main__":
	unittest.main()
