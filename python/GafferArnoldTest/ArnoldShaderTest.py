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

import unittest

import IECore
import IECoreArnold

import Gaffer
import GafferTest
import GafferScene
import GafferArnold

class ArnoldShaderTest( unittest.TestCase ) :

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

if __name__ == "__main__":
	unittest.main()
