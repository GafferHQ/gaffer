#########################################################################
#
#  Copyright (c) 2022, Cinesite VFX Ltd. All rights reserved.
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
import Gaffer
import GafferScene
import GafferSceneTest


class ShaderQueryTest( GafferSceneTest.SceneTestCase ):

	def testDefault( self ) :

		q = GafferScene.ShaderQuery()

		self.assertEqual( q["location"].getValue(), "" )
		self.assertEqual( q["shader"].getValue(), "" )
		self.assertFalse( q["inherit"].getValue() )
		self.assertEqual( len( q["queries"].children() ), 0 )
		self.assertEqual( len( q["out"].children() ), 0 )

	def testIntermediateObject( self ) :

		s = GafferScene.Sphere()

		srf = GafferSceneTest.TestShader( "surface" )
		srf["name"].setValue( "testSurface" )
		srf["type"].setValue( "test:surface" )

		a = GafferScene.ShaderAssignment()
		a["in"].setInput( s["out"] )
		a["shader"].setInput( srf["out"] )

		q = GafferScene.ShaderQuery()
		q["scene"].setInput( a["out"] )
		q["location"].setValue( "/sphere" )
		q["shader"].setValue( "test:surface" )

		self.assertEqual(
			q["__intermediateObjectPlug"].getValue(),
			a["out"].attributes( "/sphere" )["test:surface"]
		)

	def testOutput( self ) :

		q = GafferScene.ShaderQuery()

		n1 = q.addQuery( Gaffer.IntPlug() )
		n2 = q.addQuery( Gaffer.Color3fPlug() )
		n3 = q.addQuery( Gaffer.Box2iPlug() )
		n4 = q.addQuery( Gaffer.IntPlug() )
		badPlug = Gaffer.NameValuePlug( "missing", Gaffer.Color3fPlug(), "badPlug" )

		self.assertEqual( q.outPlugFromQuery( n1 ), q["out"][0] )
		self.assertEqual( q.outPlugFromQuery( n2 ), q["out"][1] )
		self.assertEqual( q.outPlugFromQuery( n3 ), q["out"][2] )

		self.assertEqual( q.existsPlugFromQuery( n1 ), q["out"][0]["exists"] )
		self.assertEqual( q.existsPlugFromQuery( n2 ), q["out"][1]["exists"] )
		self.assertEqual( q.existsPlugFromQuery( n3 ), q["out"][2]["exists"] )

		self.assertEqual( q.valuePlugFromQuery( n1 ), q["out"][0]["value"] )
		self.assertEqual( q.valuePlugFromQuery( n2 ), q["out"][1]["value"] )
		self.assertEqual( q.valuePlugFromQuery( n3 ), q["out"][2]["value"] )

		self.assertEqual( q.queryPlug( q["out"][0]["value"] ), n1 )
		self.assertEqual( q.queryPlug( q["out"][1]["value"] ), n2 )
		self.assertEqual( q.queryPlug( q["out"][1]["value"]["r"] ), n2 )
		self.assertEqual( q.queryPlug( q["out"][2]["value"] ), n3 )
		self.assertEqual( q.queryPlug( q["out"][2]["value"]["min"] ), n3 )
		self.assertEqual( q.queryPlug( q["out"][2]["value"]["min"]["x"] ), n3 )
		self.assertRaises( IECore.Exception, q.queryPlug, badPlug )

		q["out"][3].removeChild( q["out"][3]["exists"] )
		q["out"][3].removeChild( q["out"][3]["value"] )

		self.assertIsNone( q.existsPlugFromQuery( n4 ) )
		self.assertIsNone( q.valuePlugFromQuery( n4 ) )

		q["out"][3].addChild( Gaffer.FloatPlug( "exists", Gaffer.Plug.Direction.Out ) )
		self.assertIsNone( q.existsPlugFromQuery( n4 ) )

	def testAddRemoveQuery( self ) :

		def checkChildrenCount( plug, count ) :
			self.assertEqual( len( plug["queries"].children() ), count )
			self.assertEqual( len( plug["out"].children() ), count )

		q = GafferScene.ShaderQuery()

		checkChildrenCount( q, 0 )

		a = q.addQuery( Gaffer.IntPlug() )
		checkChildrenCount( q, 1 )
		self.assertEqual( q["queries"]["query1"]["name"].getValue(), "" )
		self.assertEqual( q["queries"]["query1"]["value"].getValue(), 0 )
		self.assertEqual( q["out"][0]["exists"].typeId(), Gaffer.BoolPlug.staticTypeId() )
		self.assertEqual( q["out"][0]["value"].typeId(), Gaffer.IntPlug.staticTypeId() )

		b = q.addQuery( Gaffer.Color3fPlug( "c3f" ), "color" )
		checkChildrenCount( q, 2 )
		self.assertEqual( q["queries"].children(), ( a, b ) )
		self.assertEqual( q["queries"]["query2"]["name"].getValue(), "color" )
		self.assertEqual( q["queries"]["query2"]["value"].getValue(), imath.Color3f() )
		self.assertEqual( q["out"][0]["value"].typeId(), Gaffer.IntPlug.staticTypeId() )
		self.assertEqual( q["out"][1]["value"].typeId(), Gaffer.Color3fPlug.staticTypeId() )
		for i in range( 0, 2) :
			self.assertEqual( q["out"][i]["exists"].typeId(), Gaffer.BoolPlug.staticTypeId() )

		c = q.addQuery( Gaffer.Box2iPlug( "b2i", Gaffer.Plug.Direction.Out, imath.Box2i( imath.V2i( 1 ), imath.V2i( 2 ) ) ), "box" )
		checkChildrenCount( q, 3 )
		self.assertEqual( q["queries"].children(), ( a, b, c ) )
		self.assertEqual( q["queries"]["query3"]["name"].getValue(), "box" )
		self.assertEqual( q["queries"]["query3"]["value"].getValue(), imath.Box2i( imath.V2i( 1 ), imath.V2i( 2 ) ) )
		self.assertEqual( q["out"][0]["value"].typeId(), Gaffer.IntPlug.staticTypeId() )
		self.assertEqual( q["out"][1]["value"].typeId(), Gaffer.Color3fPlug.staticTypeId() )
		self.assertEqual( q["out"][2]["value"].typeId(), Gaffer.Box2iPlug.staticTypeId() )
		for i in range( 0, 3) :
			self.assertEqual( q["out"][i]["exists"].typeId(), Gaffer.BoolPlug.staticTypeId() )

		q.removeQuery( b )
		checkChildrenCount( q, 2 )
		self.assertEqual( q["queries"].children(), ( a, c ) )
		self.assertEqual( q["out"][0]["value"].typeId(), Gaffer.IntPlug.staticTypeId() )
		self.assertEqual( q["out"][1]["value"].typeId(), Gaffer.Box2iPlug.staticTypeId() )
		for i in range( 0, 2) :
			self.assertEqual( q["out"][i]["exists"].typeId(), Gaffer.BoolPlug.staticTypeId() )

		q.removeQuery( c )
		checkChildrenCount( q, 1 )
		q.removeQuery( a )
		checkChildrenCount( q, 0 )

	def testExists( self ) :

		s = GafferScene.Sphere()

		srf = GafferSceneTest.TestShader( "surface" )
		srf["type"].setValue( "test:surface" )
		srf["parameters"]["t"] = Gaffer.Color3fPlug()

		tex = GafferSceneTest.TestShader( "texture" )
		tex["type"].setValue( "test:surface" )

		srf["parameters"]["t"].setInput( tex["out"] )

		a = GafferScene.ShaderAssignment()
		a["in"].setInput( s["out"] )
		a["shader"].setInput( srf["out"] )

		q = GafferScene.ShaderQuery()
		q["scene"].setInput( a["out"] )
		q["location"].setValue( "/sphere" )

		e1 = q.addQuery( Gaffer.IntPlug( "i", Gaffer.Plug.Direction.Out, 1 ), "i" )
		e2 = q.addQuery( Gaffer.IntPlug( "i", Gaffer.Plug.Direction.Out, 1 ), "m" )
		e3 = q.addQuery( Gaffer.Color3fPlug( "c3f", Gaffer.Plug.Direction.Out, imath.Color3f( 1.0, 1.0, 1.0 ) ), "texture.c" )
		e4 = q.addQuery( Gaffer.Color3fPlug( "c3f", Gaffer.Plug.Direction.Out, imath.Color3f( 1.0, 1.0, 1.0 ) ), "texture.m" )
		e5 = q.addQuery( Gaffer.Color3fPlug( "c3f", Gaffer.Plug.Direction.Out, imath.Color3f( 1.0, 1.0, 1.0 ) ), "texture" )
		e6 = q.addQuery( Gaffer.FloatPlug( "f", Gaffer.Plug.Direction.Out, 0.5 ), "missing.m" )

		q["shader"].setValue( "test:missing" )

		self.assertFalse( q["out"][0]["exists"].getValue() )
		self.assertFalse( q["out"][1]["exists"].getValue() )
		self.assertFalse( q["out"][2]["exists"].getValue() )
		self.assertFalse( q["out"][3]["exists"].getValue() )
		self.assertFalse( q["out"][4]["exists"].getValue() )
		self.assertFalse( q["out"][5]["exists"].getValue() )

		q["shader"].setValue( "test:surface" )

		self.assertTrue( q["out"][0]["exists"].getValue() )
		self.assertFalse( q["out"][1]["exists"].getValue() )
		self.assertTrue( q["out"][2]["exists"].getValue() )
		self.assertFalse( q["out"][3]["exists"].getValue() )
		self.assertFalse( q["out"][4]["exists"].getValue() )
		self.assertFalse( q["out"][5]["exists"].getValue() )

		q.removeQuery( e3 )
		self.assertTrue( q["out"][0]["exists"].getValue() )
		self.assertFalse( q["out"][1]["exists"].getValue() )
		self.assertFalse( q["out"][2]["exists"].getValue() )
		self.assertFalse( q["out"][3]["exists"].getValue() )
		self.assertFalse( q["out"][4]["exists"].getValue() )

		e7 = q.addQuery( Gaffer.Color3fPlug( "c3f", Gaffer.Plug.Direction.Out, imath.Color3f( 1.0, 1.0, 1.0 ) ), "c" )

		self.assertTrue( q["out"][5]["exists"].getValue() )

		q["location"].setValue( "/missing" )

		self.assertFalse( q["out"][0]["exists"].getValue() )
		self.assertFalse( q["out"][1]["exists"].getValue() )
		self.assertFalse( q["out"][2]["exists"].getValue() )
		self.assertFalse( q["out"][3]["exists"].getValue() )
		self.assertFalse( q["out"][4]["exists"].getValue() )
		self.assertFalse( q["out"][5]["exists"].getValue() )

	def testValues( self ) :

		s = GafferScene.Sphere()

		srf = GafferSceneTest.TestShader( "surface" )
		srf["type"].setValue( "test:surface" )
		srf["parameters"]["c"].setValue( imath.Color3f( 0.4, 0.5, 0.6 ) )
		srf["parameters"]["i"].setValue( 2 )
		srf["parameters"]["t"] = Gaffer.Color3fPlug()
		srf["parameters"]["b"] = Gaffer.Box2iPlug()
		srf["parameters"]["b"].setValue( imath.Box2i( imath.V2i( 3 ), imath.V2i( 4 ) ) )

		tex = GafferSceneTest.TestShader( "texture" )
		tex["type"].setValue( "test:surface" )
		tex["parameters"]["c"].setValue( imath.Color3f( 0.7, 0.8, 0.9 ) )
		tex["parameters"]["i"].setValue( 3 )

		srf["parameters"]["t"].setInput( tex["out"] )

		a = GafferScene.ShaderAssignment()
		a["in"].setInput( s["out"] )
		a["shader"].setInput( srf["out"] )

		q = GafferScene.ShaderQuery()
		q["scene"].setInput( a["out"] )
		q["location"].setValue( "/sphere" )

		v1 = q.addQuery( Gaffer.IntPlug( "i", Gaffer.Plug.Direction.Out, 1 ), "i" )
		v2 = q.addQuery( Gaffer.IntPlug( "i", Gaffer.Plug.Direction.Out, 1 ), "m" )
		v3 = q.addQuery( Gaffer.Box2iPlug( "b2i", Gaffer.Plug.Direction.Out, imath.Box2i( imath.V2i( 1 ), imath.V2i( 2 ) ) ), "b" )
		v4 = q.addQuery( Gaffer.Color3fPlug( "c3f", Gaffer.Plug.Direction.Out, imath.Color3f( 0.1, 0.2, 0.3 ) ), "texture.c" )
		v5 = q.addQuery( Gaffer.Color3fPlug( "c3f", Gaffer.Plug.Direction.Out, imath.Color3f( 0.1, 0.2, 0.3 ) ), "texture.m" )
		v6 = q.addQuery( Gaffer.Color3fPlug( "c3f", Gaffer.Plug.Direction.Out, imath.Color3f( 0.1, 0.2, 0.3 ) ), "texture" )
		v7 = q.addQuery( Gaffer.FloatPlug( "f", Gaffer.Plug.Direction.Out, 0.5 ), "missing.m" )

		q["shader"].setValue( "test:missing" )

		self.assertEqual( q["out"][0]["value"].getValue(), 1 )
		self.assertEqual( q["out"][1]["value"].getValue(), 1 )
		self.assertEqual( q["out"][2]["value"].getValue(), imath.Box2i( imath.V2i( 1 ), imath.V2i( 2 ) ) )
		self.assertEqual( q["out"][3]["value"].getValue(), imath.Color3f( 0.1, 0.2, 0.3 ) )
		self.assertEqual( q["out"][4]["value"].getValue(), imath.Color3f( 0.1, 0.2, 0.3 ) )
		self.assertEqual( q["out"][5]["value"].getValue(), imath.Color3f( 0.1, 0.2, 0.3 ) )
		self.assertEqual( q["out"][6]["value"].getValue(), 0.5 )

		q["shader"].setValue( "test:surface" )

		self.assertEqual( q["out"][0]["value"].getValue(), 2 )
		self.assertEqual( q["out"][1]["value"].getValue(), 1 )
		self.assertEqual( q["out"][2]["value"].getValue(), imath.Box2i( imath.V2i( 3 ), imath.V2i( 4 ) ) )
		self.assertEqual( q["out"][3]["value"].getValue(), imath.Color3f( 0.7, 0.8, 0.9 ) )
		self.assertEqual( q["out"][4]["value"].getValue(), imath.Color3f( 0.1, 0.2, 0.3 ) )
		self.assertEqual( q["out"][5]["value"].getValue(), imath.Color3f( 0.1, 0.2, 0.3 ) )
		self.assertEqual( q["out"][6]["value"].getValue(), 0.5 )

		q.removeQuery( v4 )
		self.assertEqual( q["out"][0]["value"].getValue(), 2 )
		self.assertEqual( q["out"][1]["value"].getValue(), 1 )
		self.assertEqual( q["out"][2]["value"].getValue(), imath.Box2i( imath.V2i( 3 ), imath.V2i( 4 ) ) )
		self.assertEqual( q["out"][3]["value"].getValue(), imath.Color3f( 0.1, 0.2, 0.3 ) )
		self.assertEqual( q["out"][4]["value"].getValue(), imath.Color3f( 0.1, 0.2, 0.3 ) )
		self.assertEqual( q["out"][5]["value"].getValue(), 0.5 )

		v8 = q.addQuery( Gaffer.Color3fPlug( "c3f", Gaffer.Plug.Direction.Out, imath.Color3f( 0.1, 0.2, 0.3 ) ), "c" )

		self.assertEqual( q["out"][6]["value"].getValue(), imath.Color3f( 0.4, 0.5, 0.6 ) )

	def testChangeShaderValue( self ) :

		s = GafferScene.Sphere()

		srf = GafferSceneTest.TestShader( "surface" )
		srf["type"].setValue( "test:surface" )
		srf["parameters"]["i"].setValue( 2 )
		srf["parameters"]["t"] = Gaffer.Color3fPlug()
		srf["parameters"]["b"] = Gaffer.Box2iPlug()
		srf["parameters"]["b"].setValue( imath.Box2i( imath.V2i( 3 ), imath.V2i( 4 ) ) )

		tex = GafferSceneTest.TestShader( "texture" )
		tex["type"].setValue( "test:surface" )
		tex["parameters"]["c"].setValue( imath.Color3f( 0.7, 0.8, 0.9 ) )
		tex["parameters"]["i"].setValue( 3 )

		srf["parameters"]["t"].setInput( tex["out"] )

		a = GafferScene.ShaderAssignment()
		a["in"].setInput( s["out"] )
		a["shader"].setInput( srf["out"] )

		q = GafferScene.ShaderQuery()
		q["scene"].setInput( a["out"] )
		q["location"].setValue( "/sphere" )
		q["shader"].setValue( "test:surface" )

		v1 = q.addQuery( Gaffer.IntPlug( "i", Gaffer.Plug.Direction.Out, 1 ), "i" )
		v2 = q.addQuery( Gaffer.Box2iPlug( "b2i", Gaffer.Plug.Direction.Out, imath.Box2i( imath.V2i( 1 ), imath.V2i( 2 ) ) ), "b" )
		v3 = q.addQuery( Gaffer.Color3fPlug( "c3f", Gaffer.Plug.Direction.Out, imath.Color3f( 0.1, 0.2, 0.3 ) ), "texture.c" )

		self.assertTrue( q["out"][0]["exists"].getValue() )
		self.assertEqual( q["out"][0]["value"].getValue(), 2)
		self.assertTrue( q["out"][1]["exists"].getValue() )
		self.assertEqual( q["out"][1]["value"].getValue(), imath.Box2i( imath.V2i( 3 ), imath.V2i( 4 ) ) )
		self.assertTrue( q["out"][2]["exists"].getValue() )
		self.assertEqual( q["out"][2]["value"].getValue(), imath.Color3f( 0.7, 0.8, 0.9 ) )

		srf["parameters"]["i"].setValue( 3 )
		srf["parameters"]["b"].setValue( imath.Box2i( imath.V2i( 5 ), imath.V2i( 6 ) ) )
		tex["parameters"]["c"].setValue( imath.Color3f( 1.0, 1.1, 1.2 ) )

		self.assertTrue( q["out"][0]["exists"].getValue() )
		self.assertEqual( q["out"][0]["value"].getValue(), 3)
		self.assertTrue( q["out"][1]["exists"].getValue() )
		self.assertEqual( q["out"][1]["value"].getValue(), imath.Box2i( imath.V2i( 5 ), imath.V2i( 6 ) ) )
		self.assertTrue( q["out"][2]["exists"].getValue() )
		self.assertEqual( q["out"][2]["value"].getValue(), imath.Color3f( 1.0, 1.1, 1.2 ) )

	def testChangeDefault( self ) :

		s = GafferScene.Sphere()

		srf = GafferSceneTest.TestShader( "surface" )
		srf["type"].setValue( "test:surface" )
		srf["parameters"]["i"].setValue( 2 )
		srf["parameters"]["t"] = Gaffer.Color3fPlug()
		srf["parameters"]["b"] = Gaffer.Box2iPlug()
		srf["parameters"]["b"].setValue( imath.Box2i( imath.V2i( 3 ), imath.V2i( 4 ) ) )

		tex = GafferSceneTest.TestShader( "texture" )
		tex["type"].setValue( "test:surface" )
		tex["parameters"]["c"].setValue( imath.Color3f( 0.7, 0.8, 0.9 ) )
		tex["parameters"]["i"].setValue( 3 )

		srf["parameters"]["t"].setInput( tex["out"] )

		a = GafferScene.ShaderAssignment()
		a["in"].setInput( s["out"] )
		a["shader"].setInput( srf["out"] )

		q = GafferScene.ShaderQuery()
		q["scene"].setInput( a["out"] )
		q["location"].setValue( "/sphere" )
		q["shader"].setValue( "test:missing" )

		v1 = q.addQuery( Gaffer.IntPlug( "i", Gaffer.Plug.Direction.Out, 1 ), "i" )
		v2 = q.addQuery( Gaffer.Box2iPlug( "b2i", Gaffer.Plug.Direction.Out, imath.Box2i( imath.V2i( 1 ), imath.V2i( 2 ) ) ), "b" )
		v3 = q.addQuery( Gaffer.Color3fPlug( "c3f", Gaffer.Plug.Direction.Out, imath.Color3f( 0.1, 0.2, 0.3 ) ), "texture.c" )

		self.assertFalse( q["out"][0]["exists"].getValue() )
		self.assertEqual( q["out"][0]["value"].getValue(), 1)
		self.assertFalse( q["out"][1]["exists"].getValue() )
		self.assertEqual( q["out"][1]["value"].getValue(), imath.Box2i( imath.V2i( 1 ), imath.V2i( 2 ) ) )
		self.assertFalse( q["out"][2]["exists"].getValue() )
		self.assertEqual( q["out"][2]["value"].getValue(), imath.Color3f( 0.1, 0.2, 0.3 ) )

		v1["value"].setValue( 3 )
		v2["value"].setValue( imath.Box2i( imath.V2i( 5 ), imath.V2i( 6 ) ) )
		v3["value"].setValue( imath.Color3f( 1.0, 1.1, 1.2 ) )

		self.assertFalse( q["out"][0]["exists"].getValue() )
		self.assertEqual( q["out"][0]["value"].getValue(), 3)
		self.assertFalse( q["out"][1]["exists"].getValue() )
		self.assertEqual( q["out"][1]["value"].getValue(), imath.Box2i( imath.V2i( 5 ), imath.V2i( 6 ) ) )
		self.assertFalse( q["out"][2]["exists"].getValue() )
		self.assertEqual( q["out"][2]["value"].getValue(), imath.Color3f( 1.0, 1.1, 1.2 ) )

	def testSerialisation( self ) :

		s = GafferScene.Sphere()

		srf = GafferSceneTest.TestShader( "surface" )
		srf["type"].setValue( "test:surface" )
		srf["parameters"]["i"].setValue( 2 )
		srf["parameters"]["c"].setValue( imath.Color3f( 0.7, 0.8, 0.9 ) )

		a = GafferScene.ShaderAssignment()
		a["in"].setInput( s["out"] )
		a["shader"].setInput( srf["out"] )

		q = GafferScene.ShaderQuery()
		q["scene"].setInput( a["out"] )
		q["location"].setValue( "/sphere" )
		q["shader"].setValue( "test:surface" )

		v1 = q.addQuery( Gaffer.IntPlug( "i", Gaffer.Plug.Direction.Out, 1 ), "i" )
		v2 = q.addQuery( Gaffer.Color3fPlug( "c3f", Gaffer.Plug.Direction.Out, imath.Color3f( 0.1, 0.2, 0.3 ) ), "c" )

		t = GafferScene.Shader( "target" )
		t["type"].setValue( "test:surface" )
		t["parameters"]["i"] = Gaffer.IntPlug()
		t["parameters"]["c"] = Gaffer.Color3fPlug()
		t["parameters"]["b1"] = Gaffer.BoolPlug()
		t["parameters"]["b2"] = Gaffer.BoolPlug()
		t["parameters"]["i"].setFlags( Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		t["parameters"]["c"].setFlags( Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		t["parameters"]["b1"].setFlags( Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		t["parameters"]["b2"].setFlags( Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		t["parameters"]["i"].setInput( q["out"][0]["value"] )
		t["parameters"]["c"].setInput( q["out"][1]["value"] )
		t["parameters"]["b1"].setInput( q["out"][0]["exists"] )
		t["parameters"]["b2"].setInput( q["out"][1]["exists"] )

		scriptNode = Gaffer.ScriptNode()
		scriptNode.addChild( s )
		scriptNode.addChild( srf )
		scriptNode.addChild( a )
		scriptNode.addChild( q )
		scriptNode.addChild( t )

		self.assertTrue( scriptNode["ShaderQuery"]["out"][0]["exists"].getValue() )
		self.assertEqual( scriptNode["ShaderQuery"]["out"][0]["value"].getValue(), 2)
		self.assertTrue( scriptNode["ShaderQuery"]["out"][1]["exists"].getValue() )
		self.assertEqual( scriptNode["ShaderQuery"]["out"][1]["value"].getValue(), imath.Color3f( 0.7, 0.8, 0.9 ) )
		self.assertEqual( scriptNode["target"]["parameters"]["i"].getInput(), q["out"][0]["value"] )
		self.assertEqual( scriptNode["target"]["parameters"]["c"].getInput(), q["out"][1]["value"] )
		self.assertEqual( scriptNode["target"]["parameters"]["b1"].getInput(), q["out"][0]["exists"] )
		self.assertEqual( scriptNode["target"]["parameters"]["b2"].getInput(), q["out"][1]["exists"] )

		serialised = scriptNode.serialise()

		scriptNode = Gaffer.ScriptNode()
		scriptNode.execute( serialised )

		self.assertTrue( scriptNode["ShaderQuery"]["out"][0]["exists"].getValue() )
		self.assertEqual( scriptNode["ShaderQuery"]["out"][0]["value"].getValue(), 2)
		self.assertTrue( scriptNode["ShaderQuery"]["out"][1]["exists"].getValue() )
		self.assertEqual( scriptNode["ShaderQuery"]["out"][1]["value"].getValue(), imath.Color3f( 0.7, 0.8, 0.9 ) )
		self.assertEqual( str( scriptNode["target"]["parameters"]["i"].getInput() ), str( q["out"][0]["value"] ) )
		self.assertEqual( str( scriptNode["target"]["parameters"]["c"].getInput() ), str( q["out"][1]["value"] ) )
		self.assertEqual( str( scriptNode["target"]["parameters"]["b1"].getInput() ), str( q["out"][0]["exists"] ) )
		self.assertEqual( str( scriptNode["target"]["parameters"]["b2"].getInput() ), str( q["out"][1]["exists"] ) )

		scriptNode["ShaderQuery"].removeQuery( scriptNode["ShaderQuery"]["queries"][0] )

		self.assertTrue( scriptNode["ShaderQuery"]["out"][0]["exists"].getValue() )
		self.assertEqual( scriptNode["ShaderQuery"]["out"][0]["value"].getValue(), imath.Color3f( 0.7, 0.8, 0.9 ) )
		self.assertIsNone( scriptNode["target"]["parameters"]["i"].getInput() )
		self.assertEqual( str( scriptNode["target"]["parameters"]["c"].getInput() ), str( q["out"][1]["value"] ) )
		self.assertIsNone( scriptNode["target"]["parameters"]["b1"].getInput() )
		self.assertEqual( str( scriptNode["target"]["parameters"]["b2"].getInput() ), str( q["out"][1]["exists"] ) )

		serialised = scriptNode.serialise()

		scriptNode = Gaffer.ScriptNode()
		scriptNode.execute( serialised )

		self.assertTrue( scriptNode["ShaderQuery"]["out"][0]["exists"].getValue() )
		self.assertEqual( scriptNode["ShaderQuery"]["out"][0]["value"].getValue(), imath.Color3f( 0.7, 0.8, 0.9 ) )
		self.assertIsNone( scriptNode["target"]["parameters"]["i"].getInput() )
		self.assertEqual( str( scriptNode["target"]["parameters"]["c"].getInput() ), str( q["out"][1]["value"] ) )
		self.assertIsNone( scriptNode["target"]["parameters"]["b1"].getInput() )
		self.assertEqual( str( scriptNode["target"]["parameters"]["b2"].getInput() ), str( q["out"][1]["exists"] ) )


if __name__ == "__main__":
	unittest.main()
