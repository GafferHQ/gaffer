##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

import os
import subprocess
import unittest
import imath

import IECore
import IECoreScene
import IECoreImage

import Gaffer
import GafferOSL
import GafferTest
import GafferImage
import GafferScene
import GafferSceneTest
import GafferArnold

# Decorator that executes in a subprocess with our test metadata file on the
# `ARNOLD_PLUGIN_PATH`.
def withMetadata( func ) :

	def wrapper( self ) :

		metadataPath = os.path.join( os.path.dirname( __file__ ), "metadata" )
		if metadataPath not in os.environ["ARNOLD_PLUGIN_PATH"].split( ":" ) :

			env = os.environ.copy()
			env["ARNOLD_PLUGIN_PATH"] = env["ARNOLD_PLUGIN_PATH"] + ":" + metadataPath

			try :
				subprocess.check_output(
					[ "gaffer", "test", "GafferArnoldTest.ArnoldShaderTest." + func.__name__ ],
					env = env, stderr = subprocess.STDOUT
				)
			except subprocess.CalledProcessError as e :
				self.fail( e.output )

		else :

			func( self )

	return wrapper

class ArnoldShaderTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		n = GafferArnold.ArnoldShader()
		n.loadShader( "noise" )

	def testAttributes( self ) :

		n = GafferArnold.ArnoldShader()
		n.loadShader( "utility" )

		network = n.attributes()["ai:surface"]
		self.assertTrue( isinstance( network, IECoreScene.ShaderNetwork ) )
		self.assertEqual( len( network ), 1 )

		self.assertEqual( network.outputShader().name, "utility" )

	def testParameterRepresentation( self ) :

		n = GafferArnold.ArnoldShader()
		n.loadShader( "wireframe" )

		self.assertIsInstance( n["parameters"]["line_width"], Gaffer.FloatPlug )
		self.assertIsInstance( n["parameters"]["fill_color"], Gaffer.Color3fPlug )
		self.assertIsInstance( n["parameters"]["line_color"], Gaffer.Color3fPlug )
		self.assertIsInstance( n["parameters"]["raster_space"], Gaffer.BoolPlug )
		self.assertIsInstance( n["parameters"]["edge_type"], Gaffer.StringPlug )
		self.assertNotIn( "name", n["parameters"] )

	def testParameterUse( self ) :

		n = GafferArnold.ArnoldShader()
		n.loadShader( "wireframe" )

		n["parameters"]["line_width"].setValue( 10 )
		n["parameters"]["fill_color"].setValue( imath.Color3f( .25, .5, 1 ) )
		n["parameters"]["raster_space"].setValue( False )
		n["parameters"]["edge_type"].setValue( "polygons" )

		s = n.attributes()["ai:surface"].outputShader()
		self.assertEqual( s.parameters["line_width"], IECore.FloatData( 10 ) )
		self.assertEqual( s.parameters["fill_color"], IECore.Color3fData( imath.Color3f( .25, .5, 1 ) ) )
		self.assertEqual( s.parameters["line_color"], IECore.Color3fData( imath.Color3f( 0 ) ) )
		self.assertEqual( s.parameters["raster_space"], IECore.BoolData( False ) )
		self.assertEqual( s.parameters["edge_type"], IECore.StringData( "polygons" ) )

	def testSerialisation( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferArnold.ArnoldShader()
		s["n"].loadShader( "wireframe" )

		ss = s.serialise()

		s = Gaffer.ScriptNode()
		s.execute( ss )

		self.assertIsInstance( s["n"]["parameters"]["line_width"], Gaffer.FloatPlug )
		self.assertIsInstance( s["n"]["parameters"]["fill_color"], Gaffer.Color3fPlug )
		self.assertIsInstance( s["n"]["parameters"]["line_color"], Gaffer.Color3fPlug )
		self.assertIsInstance( s["n"]["parameters"]["raster_space"], Gaffer.BoolPlug )
		self.assertIsInstance( s["n"]["parameters"]["edge_type"], Gaffer.StringPlug )

	def testHash( self ) :

		n = GafferArnold.ArnoldShader()
		h = n.attributesHash()

		n.loadShader( "noise" )
		h2 = n.attributesHash()

		self.assertNotEqual( h, h2 )

		n["parameters"]["octaves"].setValue( 10 )
		h3 = n.attributesHash()

		self.assertNotEqual( h2, h3 )

	def testShaderNetwork( self ) :

		s = GafferArnold.ArnoldShader( "surface" )
		s.loadShader( "standard_surface" )

		n = GafferArnold.ArnoldShader( "noise" )
		n.loadShader( "noise" )

		s["parameters"]["base_color"].setInput( n["out"] )
		s["parameters"]["specular_color"].setInput( n["out"] )

		network = s.attributes()["ai:surface"]
		self.assertEqual( len( network ), 2 )

		self.assertEqual( network.getShader( "noise" ).type, "ai:shader" )
		self.assertEqual( network.getShader( "noise" ).name, "noise" )

		self.assertEqual( network.getShader( "surface" ).type, "ai:surface" )
		self.assertEqual( network.getShader( "surface" ).name, "standard_surface" )

		self.assertEqual(
			network.inputConnections( "surface" ),
			[
				network.Connection( ( "noise", "" ), ( "surface", "base_color" ) ),
				network.Connection( ( "noise", "" ), ( "surface", "specular_color" ) ),
			]
		)

	def testShaderNetworkRender( self ) :

		f = GafferArnold.ArnoldShader()
		f.loadShader( "flat" )
		f["parameters"]["color"].setValue( imath.Color3f( 1, 1, 0 ) )

		s = GafferArnold.ArnoldShader()
		s.loadShader( "utility" )
		s["parameters"]["color"].setInput( f["parameters"]["color"] )

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"Arnold",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
		)

		r.output(
			"test",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ImageDisplayDriver",
					"handle" : "test"
				}
			)
		)

		mesh = r.object(
			"mesh",
			IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) ),
			r.attributes( s.attributes() )
		)
		mesh.transform( imath.M44f().translate( imath.V3f( 0, 0, -5 ) ) )

		r.render()

		imagePrimitive = IECoreImage.ImageDisplayDriver.removeStoredImage( "test" )

		pixelPos = 320 + 240 * 640

		self.assertAlmostEqual( imagePrimitive["R"][pixelPos], 1, 5 )
		self.assertAlmostEqual( imagePrimitive["G"][pixelPos], 1, 5 )
		self.assertEqual( imagePrimitive["B"][pixelPos], 0 )

	def testShaderNetworkHash( self ) :

		s = GafferArnold.ArnoldShader()
		s.loadShader( "standard_surface" )

		h1 = s.attributesHash()

		n = GafferArnold.ArnoldShader()
		n.loadShader( "noise" )
		s["parameters"]["base_color"].setInput( n["out"] )

		h2 = s.attributesHash()
		self.assertNotEqual( h1, h2 )

		n["parameters"]["octaves"].setValue( 3 )

		h3 = s.attributesHash()
		self.assertNotEqual( h3, h2 )
		self.assertNotEqual( h3, h1 )

	def testShaderNetworkHashWithNonShaderInputs( self ) :

		s = GafferArnold.ArnoldShader()
		s.loadShader( "standard_surface" )

		n = GafferArnold.ArnoldShader()
		n.loadShader( "noise" )
		s["parameters"]["base_color"].setInput( n["out"] )

		r = Gaffer.Random()
		r["seedVariable"].setValue( "a" )

		n["parameters"]["amplitude"].setInput( r["outFloat"] )

		c = Gaffer.Context()
		with c :
			c["a"] = "/one/two/1"
			h1 = s.attributesHash()
			c["a"] = "/one/two/2"
			h2 = s.attributesHash()
			self.assertNotEqual( h1, h2 )

	def testStandardShaderAcceptsImageInputs( self ) :

		s = GafferArnold.ArnoldShader()
		s.loadShader( "standard_surface" )

		t = GafferArnold.ArnoldShader()
		t.loadShader( "image" )

		s["parameters"]["emission_color"].setInput( t["out"] )

		self.assertTrue( s["parameters"]["emission_color"].getInput().isSame( t["out"] ) )
		self.assertTrue( s["parameters"]["emission_color"][0].getInput().isSame( t["out"][0] ) )
		self.assertTrue( s["parameters"]["emission_color"][1].getInput().isSame( t["out"][1] ) )
		self.assertTrue( s["parameters"]["emission_color"][2].getInput().isSame( t["out"][2] ) )

	def testDirtyPropagationThroughNetwork( self ) :

		s = GafferArnold.ArnoldShader()
		s.loadShader( "standard_surface" )

		n1 = GafferArnold.ArnoldShader()
		n1.loadShader( "noise" )

		n2 = GafferArnold.ArnoldShader()
		n2.loadShader( "noise" )

		s["parameters"]["base_color"].setInput( n1["out"] )
		n1["parameters"]["color1"].setInput( n2["out"] )

		cs = GafferTest.CapturingSlot( s.plugDirtiedSignal() )

		n2["parameters"]["amplitude"].setValue( 20 )

		self.assertTrue( "ArnoldShader.out" in [ x[0].fullName() for x in cs ] )

	def testConnectionsBetweenParameters( self ) :

		s = GafferArnold.ArnoldShader()
		s.loadShader( "add" )

		s["parameters"]["input1"].setValue( imath.Color3f( 0.1, 0.2, 0.3 ) )
		s["parameters"]["input2"].setInput( s["parameters"]["input1"] )

		shader = s.attributes()["ai:surface"].outputShader()

		self.assertEqual( shader.parameters["input1"].value, imath.Color3f( 0.1, 0.2, 0.3 ) )
		self.assertEqual( shader.parameters["input2"].value, imath.Color3f( 0.1, 0.2, 0.3 ) )

	def testDisabling( self ) :

		s = GafferArnold.ArnoldShader()
		s.loadShader( "standard_surface" )

		attributesHash = s.attributesHash()
		attributes = s.attributes()
		self.assertEqual( len( attributes ), 1 )
		self.assertEqual( attributes["ai:surface"].outputShader().name, "standard_surface" )

		self.assertTrue( s["enabled"].isSame( s.enabledPlug() ) )

		s["enabled"].setValue( False )

		attributesHash2 = s.attributesHash()
		self.assertNotEqual( attributesHash2, attributesHash )

		attributes2 = s.attributes()
		self.assertEqual( len( attributes2 ), 0 )

	def testDisablingInNetwork( self ) :

		s = GafferArnold.ArnoldShader( "s" )
		s.loadShader( "standard_surface" )

		f = GafferArnold.ArnoldShader( "f" )
		f.loadShader( "flat" )

		s["parameters"]["specular_color"].setInput( f["out"] )

		attributesHash = s.attributesHash()
		attributes = s.attributes()
		self.assertEqual( len( attributes ), 1 )
		self.assertEqual( attributes["ai:surface"].getShader( "s" ).name, "standard_surface" )
		self.assertEqual( attributes["ai:surface"].getShader( "f" ).name, "flat" )

		self.assertTrue( s["enabled"].isSame( s.enabledPlug() ) )

		f["enabled"].setValue( False )

		attributesHash2 = s.attributesHash()
		self.assertNotEqual( attributesHash2, attributesHash )

		attributes2 = s.attributes()
		self.assertEqual( len( attributes2 ), 1 )

		for key in attributes["ai:surface"].getShader( "s" ).parameters.keys() :
			if key != "specular_color" :
				self.assertEqual(
					attributes["ai:surface"].getShader( "s" ).parameters[key],
					attributes2["ai:surface"].getShader( "s" ).parameters[key]
				)

	def testAssignmentAttributeName( self ) :

		p = GafferScene.Plane()

		s = GafferArnold.ArnoldShader()
		s.loadShader( "standard_surface" )

		a = GafferScene.ShaderAssignment()
		a["in"].setInput( p["out"] )
		a["shader"].setInput( s["out"] )

		self.assertEqual( a["out"].attributes( "/plane" ).keys(), [ "ai:surface"] )

	def testLightFilterAssignmentAttributeName( self ) :

		p = GafferScene.Plane()

		s = GafferArnold.ArnoldShader( "light_blocker" )
		s.loadShader( "light_blocker" )  # metadata sets type to ai:lightFilter

		a = GafferScene.ShaderAssignment()
		a["in"].setInput( p["out"] )
		a["shader"].setInput( s["out"] )

		self.assertEqual( s["attributeSuffix"].getValue(), "light_blocker" )
		self.assertEqual( a["out"].attributes( "/plane" ).keys(), [ "ai:lightFilter:light_blocker"] )

	def testDirtyPropagationThroughShaderAssignment( self ) :

		n = GafferArnold.ArnoldShader()
		n.loadShader( "flat" )

		p = GafferScene.Plane()
		a = GafferScene.ShaderAssignment()
		a["in"].setInput( p["out"] )
		a["shader"].setInput( n["out"] )

		cs = GafferTest.CapturingSlot( a.plugDirtiedSignal() )

		n["parameters"]["color"]["r"].setValue( 0.25 )

		self.assertEqual(
			[ c[0] for c in cs ],
			[
				a["shader"],
				a["out"]["attributes"],
				a["out"],
			],
		)

	def testByteParameters( self ) :

		n = GafferArnold.ArnoldShader()
		n.loadShader( "image" )

		p = n["parameters"]["start_channel"]
		self.assertTrue( isinstance( p, Gaffer.IntPlug ) )
		self.assertEqual( p.minValue(), 0 )
		self.assertEqual( p.maxValue(), 255 )

	def testMeshLight( self ) :

		n = GafferArnold.ArnoldShader()
		n.loadShader( "mesh_light" )

		self.assertEqual( n["name"].getValue(), "mesh_light" )
		self.assertEqual( n["type"].getValue(), "ai:light" )

		self.assertTrue( "exposure" in n["parameters"] )
		self.assertTrue( n["out"].typeId(), Gaffer.Plug.staticTypeId() )

	def testColorParameterMetadata( self ) :

		n = GafferArnold.ArnoldShader()
		n.loadShader( "ray_switch" )

		for p in n["parameters"] :
			self.assertTrue( isinstance( p, Gaffer.Color4fPlug ) )

		self._testColorParameterMetadata()

	@withMetadata
	def _testColorParameterMetadata( self ) :

		n = GafferArnold.ArnoldShader()
		n.loadShader( "ray_switch" )

		for name in [ "camera", "shadow", "diffuse_transmission" ] :
			self.assertTrue( isinstance( n["parameters"][name], Gaffer.Color3fPlug ) )

		for name in [ "diffuse_reflection", "specular_transmission", "specular_reflection", "volume" ] :
			self.assertTrue( isinstance( n["parameters"][name], Gaffer.Color4fPlug ) )

	def testFloatParameterMetadata( self ) :

		n = GafferArnold.ArnoldShader()
		n.loadShader( "gobo" )

		self.assertTrue( isinstance( n["parameters"]["slidemap"], Gaffer.Color3fPlug ) )

		self._testFloatParameterMetadata()

	@withMetadata
	def _testFloatParameterMetadata( self ) :

		n = GafferArnold.ArnoldShader()
		n.loadShader( "gobo" )

		self.assertTrue( isinstance( n["parameters"]["slidemap"], Gaffer.FloatPlug ) )

	def testEmptyPlugTypeMetadata( self ) :

		n = GafferArnold.ArnoldShader()
		n.loadShader( "standard_surface" )
		self.assertTrue( "diffuse_roughness" in n["parameters"] )

		self._testEmptyPlugTypeMetadata()

	@withMetadata
	def _testEmptyPlugTypeMetadata( self ) :

		n = GafferArnold.ArnoldShader()
		n.loadShader( "standard_surface" )
		self.assertTrue( "diffuse_roughness" not in n["parameters"] )

		n = GafferArnold.ArnoldShader()
		n.loadShader( "standard_surface" )
		self.assertTrue( "diffuse_roughness" not in n["parameters"] )

	def testDefaultOverrideMetadata( self ) :

		n = GafferArnold.ArnoldShader()
		n.loadShader( "image" )

		self.assertEqual( n["parameters"]["single_channel"].defaultValue(), False )
		self.assertEqual( n["parameters"]["mipmap_bias"].defaultValue(), 0 )
		self.assertEqual( n["parameters"]["start_channel"].defaultValue(), 0 )
		self.assertEqual( n["parameters"]["sscale"].defaultValue(), 1.0 )
		self.assertEqual( n["parameters"]["multiply"].defaultValue(), imath.Color3f( 1.0 ) )
		self.assertEqual( n["parameters"]["missing_texture_color"].defaultValue(), imath.Color4f( 0.0 ) )
		self.assertEqual( n["parameters"]["uvcoords"].defaultValue(), imath.V2f( 0.0 ) )
		self.assertEqual( n["parameters"]["filename"].defaultValue(), "" )
		self.assertEqual( n["parameters"]["filter"].defaultValue(), "smart_bicubic" )

		self._testDefaultOverrideMetadata()

	@withMetadata
	def _testDefaultOverrideMetadata( self ) :

		n = GafferArnold.ArnoldShader()
		n.loadShader( "image" )
		self.assertEqual( n["parameters"]["single_channel"].defaultValue(), True )
		self.assertEqual( n["parameters"]["mipmap_bias"].defaultValue(), 42 )
		self.assertEqual( n["parameters"]["start_channel"].defaultValue(), 42 )
		self.assertAlmostEqual( n["parameters"]["sscale"].defaultValue(), 42.42, places = 5 )
		self.assertEqual( n["parameters"]["multiply"].defaultValue(), imath.Color3f( 1.2, 3.4, 5.6 ) )
		# RGBA metadata support added in Arnold 5.3.  Need to wait until we standardise on that
		# to add this declaration to the test metadata
		#self.assertEqual( n["parameters"]["missing_texture_color"].defaultValue(), imath.Color4f( 1.2, 3.4, 5.6, 7.8 ) )
		self.assertEqual( n["parameters"]["uvcoords"].defaultValue(), imath.V2f( 1.2, 3.4 ) )
		self.assertEqual( n["parameters"]["filename"].defaultValue(), "overrideDefault" )
		self.assertEqual( n["parameters"]["filter"].defaultValue(), "closest" )

	def testMixAndMatchWithOSLShaders( self ) :

		utility = GafferArnold.ArnoldShader()
		utility.loadShader( "utility" )

		colorToFloat = GafferOSL.OSLShader()
		colorToFloat.loadShader( "Conversion/ColorToFloat" )
		colorToFloat["parameters"]["c"].setInput( utility["out"] )

		colorSpline = GafferOSL.OSLShader()
		colorSpline.loadShader( "Pattern/ColorSpline" )
		colorSpline["parameters"]["x"].setInput( colorToFloat["out"]["r"] )

		flat = GafferArnold.ArnoldShader()
		flat.loadShader( "flat" )
		flat["parameters"]["color"].setInput( colorSpline["out"]["c"] )

	def testReload( self ) :

		image = GafferArnold.ArnoldShader()
		image.loadShader( "image" )

		image["parameters"]["swap_st"].setValue( True )
		image["parameters"]["uvcoords"].setValue( imath.V2f( 0.5, 1 ) )
		image["parameters"]["missing_texture_color"].setValue( imath.Color4f( 0.25, 0.5, 0.75, 1 ) )
		image["parameters"]["start_channel"].setValue( 1 )
		image["parameters"]["swrap"].setValue( "black" )

		lambert = GafferArnold.ArnoldShader()
		lambert.loadShader( "lambert" )

		lambert["parameters"]["Kd"].setValue( 0.25 )
		lambert["parameters"]["Kd_color"].setInput( image["out"] )
		lambert["parameters"]["opacity"].setValue( imath.Color3f( 0.1 ) )

		originalImagePlugs = image.children()
		originalImageParameterPlugs = image["parameters"].children()

		originalLambertPlugs = lambert.children()
		originalLambertParameterPlugs = lambert["parameters"].children()

		lambert.loadShader( "lambert", keepExistingValues = True )

		def assertValuesWereKept() :

			self.assertEqual( image["parameters"]["swap_st"].getValue(), True )
			self.assertEqual( image["parameters"]["uvcoords"].getValue(), imath.V2f( 0.5, 1 ) )
			self.assertEqual( image["parameters"]["missing_texture_color"].getValue(), imath.Color4f( 0.25, 0.5, 0.75, 1 ) )
			self.assertEqual( image["parameters"]["start_channel"].getValue(), 1 )
			self.assertEqual( image["parameters"]["swrap"].getValue(), "black" )

			self.assertEqual( image.children(), originalImagePlugs )
			self.assertEqual( image["parameters"].children(), originalImageParameterPlugs )

			self.assertEqual( lambert["parameters"]["Kd"].getValue(), 0.25 )
			self.assertTrue( lambert["parameters"]["Kd_color"].getInput().isSame( image["out"] ) )
			self.assertEqual( lambert["parameters"]["opacity"].getValue(), imath.Color3f( 0.1 ) )

			self.assertEqual( lambert.children(), originalLambertPlugs )
			self.assertEqual( lambert["parameters"].children(), originalLambertParameterPlugs )

		assertValuesWereKept()

		image.loadShader( "image", keepExistingValues = True )

		assertValuesWereKept()

		image.loadShader( "image", keepExistingValues = False )

		for p in image["parameters"].children() :
			self.assertTrue( p.isSetToDefault() )

		self.assertTrue( lambert["parameters"]["Kd_color"].getInput() is None )

	def testLoadDifferentShader( self ) :

		mix = GafferArnold.ArnoldShader()
		mix.loadShader( "mix" )

		switch = GafferArnold.ArnoldShader()
		switch.loadShader( "switch_rgba" )

		shader = GafferArnold.ArnoldShader()
		shader.loadShader( "switch_rgba" )

		def assertParametersEqual( s1, s2, ignore = [] ) :

			self.assertEqual( set( s1["parameters"].keys() ), set( s2["parameters"].keys() ) )
			for k in s1["parameters"].keys() :
				if k in ignore :
					continue
				self.assertEqual( s1["parameters"][k].getValue(), s2["parameters"][k].getValue() )

		assertParametersEqual( shader, switch )

		shader["parameters"]["input1"].setValue( imath.Color4f( 0.25 ) )

		shader.loadShader( "mix", keepExistingValues = True )
		assertParametersEqual( shader, mix, ignore = [ "input1" ] )
		self.assertEqual( shader["parameters"]["input1"].getValue(), imath.Color4f( 0.25 ) )

		shader.loadShader( "switch_rgba", keepExistingValues = False )
		assertParametersEqual( shader, switch )

	def testLoadTransformMatrixShader( self ):
		shader = GafferArnold.ArnoldShader()
		shader.loadShader( "matrix_transform" )
		self.assertEqual(type(shader["out"]), Gaffer.M44fPlug)

	def testLoadShaderInSerialisation( self ) :

		s = Gaffer.ScriptNode()
		s["s"] = GafferArnold.ArnoldShader()
		s["s"].loadShader( "lambert" )

		self.assertTrue( """loadShader( "lambert" )""" in s.serialise() )

	def testReloadShaderWithPartialColourConnections( self ) :

		n = GafferArnold.ArnoldShader()
		n.loadShader( "flat" )
		n["parameters"]["color"]["b"].setInput( n["parameters"]["color"]["g"] )

		n.loadShader( "flat", keepExistingValues = True )
		self.assertTrue( n["parameters"]["color"]["b"].getInput().isSame( n["parameters"]["color"]["g"] ) )

	def testDefaultValuesForOutput( self ) :

		for i in range( 0, 100 ) :

			n = GafferArnold.ArnoldShader()
			n.loadShader( "flat" )
			self.assertEqual( n["out"].defaultValue(), imath.Color3f( 0 ) )

	def testRecoverFromIncorrectSerialisedDefaultValue( self ) :

		s = Gaffer.ScriptNode()

		s["n1"] = GafferArnold.ArnoldShader()
		s["n1"].loadShader( "flat" )

		s["n2"] = GafferArnold.ArnoldShader()
		s["n2"].loadShader( "flat" )

		# Emulate the incorrect loading of
		# default value for output plugs -
		# bug introduced in 0.28.2.0.
		s["n1"]["out"] = Gaffer.Color3fPlug(
			direction = Gaffer.Plug.Direction.Out,
			defaultValue = imath.Color3f( -1 ),
			flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic
		)
		s["n2"]["out"] = Gaffer.Color3fPlug(
			direction = Gaffer.Plug.Direction.Out,
			defaultValue = imath.Color3f( -1 ),
			flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic
		)

		s["a"] = GafferScene.ShaderAssignment()
		s["a"]["shader"].setInput( s["n2"]["out"] )

		s["n2"]["parameters"]["color"].setInput( s["n1"]["out"] )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( s2["n1"]["out"].defaultValue(), imath.Color3f( 0 ) )
		self.assertTrue( s2["n2"]["parameters"]["color"].getInput().isSame( s2["n1"]["out"] ) )
		self.assertTrue( s2["a"]["shader"].getInput().isSame( s2["n2"]["out"] ) )

	def testDisabledShaderPassesThroughExternalValue( self ) :

		s = GafferArnold.ArnoldShader( "s" )
		s.loadShader( "standard_surface" )

		f = GafferArnold.ArnoldShader( "f" )
		f.loadShader( "flat" )

		f["parameters"]["color"].setValue( imath.Color3f( 1, 2, 3 ) )
		s["parameters"]["specular_color"].setInput( f["out"] )

		attributesHash = s.attributesHash()
		attributes = s.attributes()
		self.assertEqual( len( attributes ), 1 )
		self.assertEqual( attributes["ai:surface"].getShader( "s" ).name, "standard_surface" )
		self.assertEqual( attributes["ai:surface"].getShader( "f" ).name, "flat" )

		self.assertTrue( s["enabled"].isSame( s.enabledPlug() ) )

		f["enabled"].setValue( False )

		attributesHash2 = s.attributesHash()
		self.assertNotEqual( attributesHash2, attributesHash )

		attributes2 = s.attributes()
		self.assertEqual( len( attributes2 ), 1 )

		for key in attributes["ai:surface"].getShader( "s" ).parameters.keys() :
			if key != "specular_color" :
				self.assertEqual(
					attributes["ai:surface"].getShader( "s" ).parameters[key],
					attributes2["ai:surface"].getShader( "s" ).parameters[key]
				)
			else :
				self.assertEqual(
					attributes["ai:surface"].getShader( "f" ).parameters["color"],
					attributes2["ai:surface"].getShader( "s" ).parameters[key]
				)

	def testShaderSwitch( self ) :

		l = GafferArnold.ArnoldShader()
		l.loadShader( "lambert" )

		f1 = GafferArnold.ArnoldShader( "f1" )
		f1.loadShader( "flat" )
		f1["parameters"]["color"].setValue( imath.Color3f( 0 ) )

		f2 = GafferArnold.ArnoldShader( "f2" )
		f2.loadShader( "flat" )
		f2["parameters"]["color"].setValue( imath.Color3f( 1 ) )

		f3 = GafferArnold.ArnoldShader( "f3" )
		f3.loadShader( "flat" )
		f3["parameters"]["color"].setValue( imath.Color3f( 2 ) )

		s = Gaffer.Switch()
		s.setup( f1["out"] )

		s["in"][0].setInput( f1["out"] )
		s["in"][1].setInput( f2["out"] )
		s["in"][2].setInput( f3["out"] )

		l["parameters"]["Kd_color"].setInput( s["out"] )

		def assertIndex( index ) :

			network = l.attributes()["ai:surface"]
			self.assertEqual( len( network ), 2 )
			self.assertEqual(
				network.getShader( "f{0}".format( index + 1 ) ).parameters["color"].value,
				imath.Color3f( index )
			)

		for i in range( 0, 3 ) :
			s["index"].setValue( i )
			assertIndex( i )

	def testMixAndMatchWithOSLShadersThroughSwitch( self ) :

		arnoldIn = GafferArnold.ArnoldShader( "arnoldIn" )
		arnoldIn.loadShader( "flat" )

		oslIn = GafferOSL.OSLShader( "oslIn" )
		oslIn.loadShader( "Pattern/ColorSpline" )

		switch1 = Gaffer.Switch()
		switch2 = Gaffer.Switch()

		switch1.setup( arnoldIn["out"] )
		switch2.setup( oslIn["out"]["c"] )

		switch1["in"][0].setInput( arnoldIn["out"] )
		switch1["in"][1].setInput( oslIn["out"]["c"] )

		switch2["in"][0].setInput( arnoldIn["out"] )
		switch2["in"][1].setInput( oslIn["out"]["c"] )

		arnoldOut = GafferArnold.ArnoldShader( "arnoldOut" )
		arnoldOut.loadShader( "flat" )

		oslOut = GafferOSL.OSLShader( "oslOut" )
		oslOut.loadShader( "Conversion/ColorToFloat" )

		arnoldOut["parameters"]["color"].setInput( switch1["out"] )
		oslOut["parameters"]["c"].setInput( switch2["out"] )

		for i in range( 0, 2 ) :

			switch1["index"].setValue( i )
			switch2["index"].setValue( i )

			network1 = arnoldOut.attributes()["ai:surface"]
			network2 = oslOut.attributes()["osl:shader"]

			self.assertEqual( len( network1 ), 2 )
			self.assertEqual( len( network2 ), 2 )

			self.assertEqual( network1.getShader( "arnoldOut" ).name, "flat" )
			self.assertEqual( network2.getShader( "oslOut" ).name, "Conversion/ColorToFloat" )

			if i == 0 :

				self.assertEqual(
					network1.inputConnections( "arnoldOut" ),
					[ network1.Connection( ( "arnoldIn", "" ), ( "arnoldOut", "color" ) ) ]
				)
				self.assertEqual(
					network2.inputConnections( "oslOut" ),
					[ network1.Connection( ( "arnoldIn", "" ), ( "oslOut", "c" ) ) ]
				)

			else :

				self.assertEqual(
					network1.inputConnections( "arnoldOut" ),
					[ network1.Connection( ( "oslIn", "c" ), ( "arnoldOut", "color" ) ) ]
				)
				self.assertEqual(
					network2.inputConnections( "oslOut" ),
					[ network1.Connection( ( "oslIn", "c" ), ( "oslOut", "c" ) ) ]
				)

	def testComponentToComponentConnections( self ) :

		n1 = GafferArnold.ArnoldShader( "n1" )
		n1.loadShader( "flat" )

		n2 = GafferArnold.ArnoldShader( "n2" )
		n2.loadShader( "flat" )

		n2["parameters"]["color"]["r"].setInput( n1["out"]["g"] )
		n2["parameters"]["color"]["g"].setInput( n1["out"]["b"] )
		n2["parameters"]["color"]["b"].setInput( n1["out"]["r"] )

		network = n2.attributes()["ai:surface"]
		self.assertEqual(
			network.inputConnections( "n2" ),
			[
				( ( "n1", "r" ), ( "n2", "color.b" ) ),
				( ( "n1", "b" ), ( "n2", "color.g" ) ),
				( ( "n1", "g" ), ( "n2", "color.r" ) ),
			]
		)

	def testLoadImager( self ) :

		node = GafferArnold.ArnoldShader()
		node.loadShader( "imager_exposure" )

		self.assertEqual( node["type"].getValue(), "ai:imager" )
		self.assertEqual( node["name"].getValue(), "imager_exposure" )
		self.assertEqual(
			list( node["parameters"].keys() ),
			[ "input", "enable", "layer_selection", "exposure" ]
		)

	def testImagerConnections( self ) :

		imager1 = GafferArnold.ArnoldShader()
		imager1.loadShader( "imager_exposure" )

		imager2 = GafferArnold.ArnoldShader()
		imager2.loadShader( "imager_exposure" )

		userDataFloat = GafferArnold.ArnoldShader()
		userDataFloat.loadShader( "user_data_float" )

		# Arnold imagers don't accept connections from shaders. They only accept
		# inputs to the `input` parameter, and only then from the output of
		# another imager.

		self.assertFalse( imager1["parameters"]["exposure"].acceptsInput( userDataFloat["out"] ) )
		self.assertFalse( imager1["parameters"]["input"].acceptsInput( imager1["out"] ) )
		self.assertFalse( imager1["parameters"]["input"].acceptsInput( userDataFloat["out"] ) )
		self.assertTrue( imager1["parameters"]["input"].acceptsInput( imager2["out"] ) )

		# Connections between _input_ parameters are OK though, because they are
		# handled in Gaffer rather than Arnold.

		self.assertTrue( imager1["parameters"]["exposure"].acceptsInput( userDataFloat["parameters"]["default"] ) )
		self.assertTrue( userDataFloat["parameters"]["default"].acceptsInput( imager1["parameters"]["exposure"] ) )

if __name__ == "__main__":
	unittest.main()
