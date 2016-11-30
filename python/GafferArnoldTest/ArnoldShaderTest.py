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
import unittest

import IECore
import IECoreArnold

import Gaffer
import GafferOSL
import GafferTest
import GafferScene
import GafferSceneTest
import GafferArnold

class ArnoldShaderTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		n = GafferArnold.ArnoldShader()
		n.loadShader( "noise" )

	def testAttributes( self ) :

		n = GafferArnold.ArnoldShader()
		n.loadShader( "utility" )

		s = n.attributes()["ai:surface"]
		self.failUnless( isinstance( s, IECore.ObjectVector ) )
		self.assertEqual( len( s ), 1 )
		self.failUnless( isinstance( s[0], IECore.Shader ) )

		s = s[0]
		self.assertEqual( s.name, "utility" )

	def testParameterRepresentation( self ) :

		n = GafferArnold.ArnoldShader()
		n.loadShader( "wireframe" )

		self.failUnless( isinstance( n["parameters"]["line_width"], Gaffer.FloatPlug ) )
		self.failUnless( isinstance( n["parameters"]["fill_color"], Gaffer.Color3fPlug ) )
		self.failUnless( isinstance( n["parameters"]["line_color"], Gaffer.Color3fPlug ) )
		self.failUnless( isinstance( n["parameters"]["raster_space"], Gaffer.BoolPlug ) )
		self.failUnless( isinstance( n["parameters"]["edge_type"], Gaffer.StringPlug ) )
		self.failIf( "name" in n["parameters"] )

	def testParameterUse( self ) :

		n = GafferArnold.ArnoldShader()
		n.loadShader( "wireframe" )

		n["parameters"]["line_width"].setValue( 10 )
		n["parameters"]["fill_color"].setValue( IECore.Color3f( .25, .5, 1 ) )
		n["parameters"]["raster_space"].setValue( False )
		n["parameters"]["edge_type"].setValue( "polygons" )

		s = n.attributes()["ai:surface"][0]
		self.assertEqual( s.parameters["line_width"], IECore.FloatData( 10 ) )
		self.assertEqual( s.parameters["fill_color"], IECore.Color3fData( IECore.Color3f( .25, .5, 1 ) ) )
		self.assertEqual( s.parameters["line_color"], IECore.Color3fData( IECore.Color3f( 0 ) ) )
		self.assertEqual( s.parameters["raster_space"], IECore.BoolData( False ) )
		self.assertEqual( s.parameters["edge_type"], IECore.StringData( "polygons" ) )

	def testSerialisation( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferArnold.ArnoldShader()
		s["n"].loadShader( "wireframe" )

		ss = s.serialise()

		s = Gaffer.ScriptNode()
		s.execute( ss )

		self.failUnless( isinstance( s["n"]["parameters"]["line_width"], Gaffer.FloatPlug ) )
		self.failUnless( isinstance( s["n"]["parameters"]["fill_color"], Gaffer.Color3fPlug ) )
		self.failUnless( isinstance( s["n"]["parameters"]["line_color"], Gaffer.Color3fPlug ) )
		self.failUnless( isinstance( s["n"]["parameters"]["raster_space"], Gaffer.BoolPlug ) )
		self.failUnless( isinstance( s["n"]["parameters"]["edge_type"], Gaffer.StringPlug ) )

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

		s = GafferArnold.ArnoldShader()
		s.loadShader( "standard" )

		n = GafferArnold.ArnoldShader()
		n.loadShader( "noise" )

		s["parameters"]["Kd"].setInput( n["out"] )
		s["parameters"]["Ks"].setInput( n["out"] )

		st = s.attributes()["ai:surface"]
		self.assertEqual( len( st ), 2 )

		self.assertEqual( st[0].type, "ai:shader" )
		self.assertEqual( st[0].name, "noise" )
		self.failUnless( "__handle" in st[0].parameters )

		self.assertEqual( st[1].type, "ai:surface" )
		self.assertEqual( st[1].name, "standard" )
		self.failIf( "__handle" in st[1].parameters )

		self.assertEqual(
			st[1].parameters["Kd"].value,
			"link:" + st[0].parameters["__handle"].value
		)

		self.assertEqual(
			st[1].parameters["Ks"].value,
			"link:" + st[0].parameters["__handle"].value
		)

	def testShaderNetworkRender( self ) :

		f = GafferArnold.ArnoldShader()
		f.loadShader( "flat" )
		f["parameters"]["color"].setValue( IECore.Color3f( 1, 1, 0 ) )

		s = GafferArnold.ArnoldShader()
		s.loadShader( "utility" )
		s["parameters"]["color"].setInput( f["parameters"]["color"] )

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"IECoreArnold::Renderer",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
		)

		r.output(
			"test",
			IECore.Display(
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
			IECore.MeshPrimitive.createPlane( IECore.Box2f( IECore.V2f( -1 ), IECore.V2f( 1 ) ) ),
			r.attributes( s.attributes() )
		)
		mesh.transform( IECore.M44f().translate( IECore.V3f( 0, 0, -5 ) ) )

		r.render()

		image = IECore.ImageDisplayDriver.removeStoredImage( "test" )
		e = IECore.PrimitiveEvaluator.create( image )
 		result = e.createResult()

		e.pointAtUV( IECore.V2f( 0.5 ), result )
		self.assertAlmostEqual( result.floatPrimVar( e.R() ), 1, 5 )
		self.assertAlmostEqual( result.floatPrimVar( e.G() ), 1, 5 )
		self.assertEqual( result.floatPrimVar( e.B() ), 0 )

	def testShaderNetworkHash( self ) :

		s = GafferArnold.ArnoldShader()
		s.loadShader( "standard" )

		h1 = s.attributesHash()

		n = GafferArnold.ArnoldShader()
		n.loadShader( "noise" )
		s["parameters"]["Kd"].setInput( n["out"] )

		h2 = s.attributesHash()
		self.assertNotEqual( h1, h2 )

		n["parameters"]["octaves"].setValue( 3 )

		h3 = s.attributesHash()
		self.assertNotEqual( h3, h2 )
		self.assertNotEqual( h3, h1 )

	def testShaderNetworkHashWithNonShaderInputs( self ) :

		s = GafferArnold.ArnoldShader()
		s.loadShader( "standard" )

		n = GafferArnold.ArnoldShader()
		n.loadShader( "noise" )
		s["parameters"]["Kd"].setInput( n["out"] )

		r = Gaffer.Random()
		r["contextEntry"].setValue( "a" )

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
		s.loadShader( "standard" )

		t = GafferArnold.ArnoldShader()
		t.loadShader( "image" )

		s["parameters"]["emission_color"].setInput( t["out"] )

		self.failUnless( s["parameters"]["emission_color"].getInput().isSame( t["out"] ) )
		self.failUnless( s["parameters"]["emission_color"][0].getInput().isSame( t["out"][0] ) )
		self.failUnless( s["parameters"]["emission_color"][1].getInput().isSame( t["out"][1] ) )
		self.failUnless( s["parameters"]["emission_color"][2].getInput().isSame( t["out"][2] ) )

	def testDirtyPropagationThroughNetwork( self ) :

		s = GafferArnold.ArnoldShader()
		s.loadShader( "standard" )

		n1 = GafferArnold.ArnoldShader()
		n1.loadShader( "noise" )

		n2 = GafferArnold.ArnoldShader()
		n2.loadShader( "noise" )

		s["parameters"]["Kd"].setInput( n1["out"] )
		n1["parameters"]["distortion"].setInput( n2["out"] )

		cs = GafferTest.CapturingSlot( s.plugDirtiedSignal() )

		n2["parameters"]["amplitude"].setValue( 20 )

		self.assertTrue( "ArnoldShader.out" in [ x[0].fullName() for x in cs ] )

	def testConnectionsBetweenParameters( self ) :

		s = GafferArnold.ArnoldShader()
		s.loadShader( "flat" )

		s["parameters"]["color"].setValue( IECore.Color3f( 0.1, 0.2, 0.3 ) )
		s["parameters"]["opacity"].setInput( s["parameters"]["color"] )

		shader = s.attributes()["ai:surface"][0]

		self.assertEqual( shader.parameters["color"].value, IECore.Color3f( 0.1, 0.2, 0.3 ) )
		self.assertEqual( shader.parameters["opacity"].value, IECore.Color3f( 0.1, 0.2, 0.3 ) )

	def testDisabling( self ) :

		s = GafferArnold.ArnoldShader()
		s.loadShader( "standard" )

		attributesHash = s.attributesHash()
		attributes = s.attributes()
		self.assertEqual( len( attributes ), 1 )
		self.assertEqual( attributes["ai:surface"][0].name, "standard" )

		self.assertTrue( s["enabled"].isSame( s.enabledPlug() ) )

		s["enabled"].setValue( False )

		attributesHash2 = s.attributesHash()
		self.assertNotEqual( attributesHash2, attributesHash )

		attributes2 = s.attributes()
		self.assertEqual( len( attributes2 ), 0 )

	def testDisablingInNetwork( self ) :

		s = GafferArnold.ArnoldShader()
		s.loadShader( "standard" )

		f = GafferArnold.ArnoldShader()
		f.loadShader( "flat" )

		s["parameters"]["Ks_color"].setInput( f["out"] )

		attributesHash = s.attributesHash()
		attributes = s.attributes()
		self.assertEqual( len( attributes ), 1 )
		self.assertEqual( attributes["ai:surface"][1].name, "standard" )
		self.assertEqual( attributes["ai:surface"][0].name, "flat" )

		self.assertTrue( s["enabled"].isSame( s.enabledPlug() ) )

		f["enabled"].setValue( False )

		attributesHash2 = s.attributesHash()
		self.assertNotEqual( attributesHash2, attributesHash )

		attributes2 = s.attributes()
		self.assertEqual( len( attributes2 ), 1 )

		for key in attributes["ai:surface"][1].parameters.keys() :
			if key != "Ks_color" :
				self.assertEqual(
					attributes["ai:surface"][1].parameters[key],
					attributes2["ai:surface"][0].parameters[key]
				)

	def testAssignmentAttributeName( self ) :

		p = GafferScene.Plane()

		s = GafferArnold.ArnoldShader()
		s.loadShader( "standard" )

		a = GafferScene.ShaderAssignment()
		a["in"].setInput( p["out"] )
		a["shader"].setInput( s["out"] )

		self.assertEqual( a["out"].attributes( "/plane" ).keys(), [ "ai:surface"] )

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

		self.__forceArnoldRestart()

		n = GafferArnold.ArnoldShader()
		n.loadShader( "ray_switch" )

		for p in n["parameters"] :
			self.assertTrue( isinstance( p, Gaffer.Color4fPlug ) )

		self.addCleanup( os.environ.__setitem__, "ARNOLD_PLUGIN_PATH", os.environ["ARNOLD_PLUGIN_PATH"] )
		os.environ["ARNOLD_PLUGIN_PATH"] = os.environ["ARNOLD_PLUGIN_PATH"] + ":" + os.path.join( os.path.dirname( __file__ ), "metadata" )

		self.__forceArnoldRestart()

		n = GafferArnold.ArnoldShader()
		n.loadShader( "ray_switch" )

		for name in [ "camera", "shadow", "reflection" ] :
			self.assertTrue( isinstance( n["parameters"][name], Gaffer.Color3fPlug ) )

		for name in [ "refraction", "diffuse", "glossy" ] :
			self.assertTrue( isinstance( n["parameters"][name], Gaffer.Color4fPlug ) )

	def testEmptyPlugTypeMetadata( self ) :

		self.__forceArnoldRestart()

		n = GafferArnold.ArnoldShader()
		n.loadShader( "standard" )
		self.assertTrue( "aov_direct_diffuse" in n["parameters"] )

		self.addCleanup( os.environ.__setitem__, "ARNOLD_PLUGIN_PATH", os.environ["ARNOLD_PLUGIN_PATH"] )
		os.environ["ARNOLD_PLUGIN_PATH"] = os.environ["ARNOLD_PLUGIN_PATH"] + ":" + os.path.join( os.path.dirname( __file__ ), "metadata" )

		self.__forceArnoldRestart()

		n.loadShader( "standard" )
		self.assertTrue( "aov_direct_diffuse" not in n["parameters"] )

		n = GafferArnold.ArnoldShader()
		n.loadShader( "standard" )
		self.assertTrue( "aov_direct_diffuse" not in n["parameters"] )

	def testMixAndMatchWithOSLShaders( self ) :

		utility = GafferArnold.ArnoldShader()
		utility.loadShader( "utility" )

		splitColor = GafferOSL.OSLShader()
		splitColor.loadShader( "Utility/SplitColor" )
		splitColor["parameters"]["c"].setInput( utility["out"] )

		colorSpline = GafferOSL.OSLShader()
		colorSpline.loadShader( "Pattern/ColorSpline" )
		colorSpline["parameters"]["x"].setInput( splitColor["out"]["r"] )

		flat = GafferArnold.ArnoldShader()
		flat.loadShader( "flat" )
		flat["parameters"]["color"].setInput( colorSpline["out"]["c"] )

	def testReload( self ) :

		image = GafferArnold.ArnoldShader()
		image.loadShader( "image" )

		image["parameters"]["swap_st"].setValue( True )
		image["parameters"]["uvcoords"].setValue( IECore.V2f( 0.5, 1 ) )
		image["parameters"]["missing_tile_color"].setValue( IECore.Color4f( 0.25, 0.5, 0.75, 1 ) )
		image["parameters"]["start_channel"].setValue( 1 )
		image["parameters"]["swrap"].setValue( "black" )

		lambert = GafferArnold.ArnoldShader()
		lambert.loadShader( "lambert" )

		lambert["parameters"]["Kd"].setValue( 0.25 )
		lambert["parameters"]["Kd_color"].setInput( image["out"] )
		lambert["parameters"]["opacity"].setValue( IECore.Color3f( 0.1 ) )
		lambert["parameters"]["aov_direct_diffuse"].setValue( "test" )

		originalImagePlugs = image.children()
		originalImageParameterPlugs = image["parameters"].children()

		originalLambertPlugs = lambert.children()
		originalLambertParameterPlugs = lambert["parameters"].children()

		lambert.loadShader( "lambert", keepExistingValues = True )

		def assertValuesWereKept() :

			self.assertEqual( image["parameters"]["swap_st"].getValue(), True )
			self.assertEqual( image["parameters"]["uvcoords"].getValue(), IECore.V2f( 0.5, 1 ) )
			self.assertEqual( image["parameters"]["missing_tile_color"].getValue(), IECore.Color4f( 0.25, 0.5, 0.75, 1 ) )
			self.assertEqual( image["parameters"]["start_channel"].getValue(), 1 )
			self.assertEqual( image["parameters"]["swrap"].getValue(), "black" )

			self.assertEqual( image.children(), originalImagePlugs )
			self.assertEqual( image["parameters"].children(), originalImageParameterPlugs )

			self.assertEqual( lambert["parameters"]["Kd"].getValue(), 0.25 )
			self.assertTrue( lambert["parameters"]["Kd_color"].getInput().isSame( image["out"] ) )
			self.assertEqual( lambert["parameters"]["opacity"].getValue(), IECore.Color3f( 0.1 ) )
			self.assertEqual( lambert["parameters"]["aov_direct_diffuse"].getValue(), "test" )

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

		standard = GafferArnold.ArnoldShader()
		standard.loadShader( "standard" )

		lambert = GafferArnold.ArnoldShader()
		lambert.loadShader( "lambert" )

		shader = GafferArnold.ArnoldShader()
		shader.loadShader( "lambert" )

		def assertParametersEqual( s1, s2, ignore = [] ) :

			self.assertEqual( set( s1["parameters"].keys() ), set( s2["parameters"].keys() ) )
			for k in s1["parameters"].keys() :
				if k in ignore :
					continue
				self.assertEqual( s1["parameters"][k].getValue(), s2["parameters"][k].getValue() )

		assertParametersEqual( shader, lambert )

		shader["parameters"]["Kd"].setValue( 0.25 )

		shader.loadShader( "standard", keepExistingValues = True )
		assertParametersEqual( shader, standard, ignore = [ "Kd" ] )
		self.assertEqual( shader["parameters"]["Kd"].getValue(), 0.25 )

		shader.loadShader( "lambert", keepExistingValues = False )
		assertParametersEqual( shader, lambert )

	def testLoadShaderInSerialisation( self ) :

		s = Gaffer.ScriptNode()
		s["s"] = GafferArnold.ArnoldShader()
		s["s"].loadShader( "lambert" )

		self.assertTrue( """loadShader( "lambert", keepExistingValues=True )""" in s.serialise() )

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
			self.assertEqual( n["out"].defaultValue(), IECore.Color3f( 0 ) )

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
			defaultValue = IECore.Color3f( -1 ),
			flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic
		)
		s["n2"]["out"] = Gaffer.Color3fPlug(
			direction = Gaffer.Plug.Direction.Out,
			defaultValue = IECore.Color3f( -1 ),
			flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic
		)

		s["a"] = GafferScene.ShaderAssignment()
		s["a"]["shader"].setInput( s["n2"]["out"] )

		s["n2"]["parameters"]["color"].setInput( s["n1"]["out"] )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( s2["n1"]["out"].defaultValue(), IECore.Color3f( 0 ) )
		self.assertTrue( s2["n2"]["parameters"]["color"].getInput().isSame( s2["n1"]["out"] ) )
		self.assertTrue( s2["a"]["shader"].getInput().isSame( s2["n2"]["out"] ) )

	def testDisabledShaderPassesThroughExternalValue( self ) :

		s = GafferArnold.ArnoldShader()
		s.loadShader( "standard" )

		f = GafferArnold.ArnoldShader()
		f.loadShader( "flat" )

		f["parameters"]["color"].setValue( IECore.Color3f( 1, 2, 3 ) )
		s["parameters"]["Ks_color"].setInput( f["out"] )

		attributesHash = s.attributesHash()
		attributes = s.attributes()
		self.assertEqual( len( attributes ), 1 )
		self.assertEqual( attributes["ai:surface"][1].name, "standard" )
		self.assertEqual( attributes["ai:surface"][0].name, "flat" )

		self.assertTrue( s["enabled"].isSame( s.enabledPlug() ) )

		f["enabled"].setValue( False )

		attributesHash2 = s.attributesHash()
		self.assertNotEqual( attributesHash2, attributesHash )

		attributes2 = s.attributes()
		self.assertEqual( len( attributes2 ), 1 )

		for key in attributes["ai:surface"][1].parameters.keys() :
			if key != "Ks_color" :
				self.assertEqual(
					attributes["ai:surface"][1].parameters[key],
					attributes2["ai:surface"][0].parameters[key]
				)
			else :
				self.assertEqual(
					attributes["ai:surface"][0].parameters["color"],
					attributes2["ai:surface"][0].parameters[key]
				)

	def testShaderSwitch( self ) :

		l = GafferArnold.ArnoldShader()
		l.loadShader( "lambert" )

		f1 = GafferArnold.ArnoldShader( "f1" )
		f1.loadShader( "flat" )
		f1["parameters"]["color"].setValue( IECore.Color3f( 0 ) )

		f2 = GafferArnold.ArnoldShader( "f2" )
		f2.loadShader( "flat" )
		f2["parameters"]["color"].setValue( IECore.Color3f( 1 ) )

		f3 = GafferArnold.ArnoldShader( "f3" )
		f3.loadShader( "flat" )
		f3["parameters"]["color"].setValue( IECore.Color3f( 2 ) )

		for switchType in ( Gaffer.SwitchComputeNode, GafferScene.ShaderSwitch ) :

			s = switchType()
			s.setup( f1["out"] )

			s["in"][0].setInput( f1["out"] )
			s["in"][1].setInput( f2["out"] )
			s["in"][2].setInput( f3["out"] )

			l["parameters"]["Kd_color"].setInput( s["out"] )

			def assertIndex( index ) :

				network = l.attributes()["ai:surface"]
				self.assertEqual( len( network ), 2 )
				self.assertEqual( network[0].parameters["color"].value, IECore.Color3f( index ) )

			for i in range( 0, 3 ) :
				s["index"].setValue( i )
				assertIndex( i )

	def testMixAndMatchWithOSLShadersThroughSwitch( self ) :

		arnoldIn = GafferArnold.ArnoldShader()
		arnoldIn.loadShader( "flat" )

		oslIn = GafferOSL.OSLShader()
		oslIn.loadShader( "Pattern/ColorSpline" )

		switch1 = GafferScene.ShaderSwitch()
		switch2 = GafferScene.ShaderSwitch()

		switch1.setup( arnoldIn["out"] )
		switch2.setup( oslIn["out"]["c"] )

		switch1["in"][0].setInput( arnoldIn["out"] )
		switch1["in"][1].setInput( oslIn["out"]["c"] )

		switch2["in"][0].setInput( arnoldIn["out"] )
		switch2["in"][1].setInput( oslIn["out"]["c"] )

		arnoldOut = GafferArnold.ArnoldShader()
		arnoldOut.loadShader( "flat" )

		oslOut = GafferOSL.OSLShader()
		oslOut.loadShader( "Utility/SplitColor" )

		arnoldOut["parameters"]["color"].setInput( switch1["out"] )
		oslOut["parameters"]["c"].setInput( switch2["out"] )

		for i in range( 0, 2 ) :

			switch1["index"].setValue( i )
			switch2["index"].setValue( i )

			network1 = arnoldOut.attributes()["ai:surface"]
			network2 = oslOut.attributes()["osl:shader"]

			self.assertEqual( len( network1 ), 2 )
			self.assertEqual( len( network2 ), 2 )

			self.assertEqual( network1[1].name, "flat" )
			self.assertEqual( network2[1].name, "Utility/SplitColor" )

			if i == 0 :

				self.assertEqual( network1[1].parameters["color"].value, "link:" + network1[0].parameters["__handle"].value )
				self.assertEqual( network2[1].parameters["c"].value, "link:" + network1[0].parameters["__handle"].value )

			else :

				self.assertEqual( network1[1].parameters["color"].value, "link:" + network1[0].parameters["__handle"].value + ".c" )
				self.assertEqual( network2[1].parameters["c"].value, "link:" + network1[0].parameters["__handle"].value + ".c" )

	def __forceArnoldRestart( self ) :

		with IECoreArnold.UniverseBlock( writable = True ) :
			pass

if __name__ == "__main__":
	unittest.main()
