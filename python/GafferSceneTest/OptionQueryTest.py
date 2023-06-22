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
import IECoreScene

import Gaffer
import GafferScene
import GafferSceneTest

class OptionQueryTest( GafferSceneTest.SceneTestCase ):

	def testDefault( self ) :

		q = GafferScene.OptionQuery()

		self.assertEqual( len( q["queries"].children() ), 0 )
		self.assertEqual( len( q["out"].children() ), 0 )

	def testOutput( self ) :

		query = GafferScene.OptionQuery()

		n1 = query.addQuery( Gaffer.IntPlug() )
		n2 = query.addQuery( Gaffer.Color3fPlug() )
		n3 = query.addQuery( Gaffer.Box2iPlug() )
		badPlug = Gaffer.NameValuePlug( "missing", Gaffer.Color3fPlug(), "badPlug" )

		self.assertEqual( query.outPlugFromQuery( n1 ), query["out"][0] )
		self.assertEqual( query.outPlugFromQuery( n2 ), query["out"][1] )
		self.assertEqual( query.outPlugFromQuery( n3 ), query["out"][2] )

		self.assertEqual( query.existsPlugFromQuery( n1 ), query["out"][0]["exists"] )
		self.assertEqual( query.existsPlugFromQuery( n2 ), query["out"][1]["exists"] )
		self.assertEqual( query.existsPlugFromQuery( n3 ), query["out"][2]["exists"] )

		self.assertEqual( query.valuePlugFromQuery( n1 ), query["out"][0]["value"] )
		self.assertEqual( query.valuePlugFromQuery( n2 ), query["out"][1]["value"] )
		self.assertEqual( query.valuePlugFromQuery( n3 ), query["out"][2]["value"] )

		self.assertEqual( query.queryPlug( query["out"][0]["value"] ), n1 )
		self.assertEqual( query.queryPlug( query["out"][1]["value"] ), n2 )
		self.assertEqual( query.queryPlug( query["out"][1]["value"]["r"] ), n2 )
		self.assertEqual( query.queryPlug( query["out"][2]["value"] ), n3 )
		self.assertEqual( query.queryPlug( query["out"][2]["value"]["min"] ), n3 )
		self.assertEqual( query.queryPlug( query["out"][2]["value"]["min"]["x"] ), n3 )
		self.assertRaises( IECore.Exception, query.queryPlug, badPlug )

	def testAddRemoveQuery( self ) :

		def checkChildrenCount( plug, count ) :
			self.assertEqual( len( plug["queries"].children() ), count )
			self.assertEqual( len( plug["out"].children() ), count )

		query = GafferScene.OptionQuery()

		checkChildrenCount( query, 0 )

		a = query.addQuery( Gaffer.IntPlug() )
		checkChildrenCount( query, 1 )
		self.assertEqual( query["queries"][0]["name"].getValue(), "" )
		self.assertEqual( query["queries"][0]["value"].getValue(), 0 )
		self.assertEqual( query["out"][0]["exists"].typeId(), Gaffer.BoolPlug.staticTypeId() )
		self.assertEqual( query["out"][0]["value"].typeId(), Gaffer.IntPlug.staticTypeId() )

		b = query.addQuery( Gaffer.Color3fPlug( "c3f" ), "c" )
		checkChildrenCount( query, 2 )
		self.assertEqual( query["queries"].children(), ( a, b ) )
		self.assertEqual( query["queries"][1]["name"].getValue(), "c" )
		self.assertEqual( query["queries"][1]["value"].getValue(), imath.Color3f() )
		self.assertEqual( query["out"][0]["value"].typeId(), Gaffer.IntPlug.staticTypeId() )
		self.assertEqual( query["out"][1]["value"].typeId(), Gaffer.Color3fPlug.staticTypeId() )
		for i in range( 0, 2) :
			self.assertEqual( query["out"][i]["exists"].typeId(), Gaffer.BoolPlug.staticTypeId() )

		c = query.addQuery( Gaffer.Box2iPlug( "b2i", Gaffer.Plug.Direction.Out, imath.Box2i( imath.V2i( 1 ), imath.V2i( 2 ) ) ), "b" )
		checkChildrenCount( query, 3 )
		self.assertEqual( query["queries"].children(), ( a, b, c ) )
		self.assertEqual( query["queries"][2]["name"].getValue(), "b" )
		self.assertEqual( query["queries"][2]["value"].getValue(), imath.Box2i( imath.V2i( 1 ), imath.V2i( 2 ) ) )
		self.assertEqual( query["out"][0]["value"].typeId(), Gaffer.IntPlug.staticTypeId() )
		self.assertEqual( query["out"][1]["value"].typeId(), Gaffer.Color3fPlug.staticTypeId() )
		self.assertEqual( query["out"][2]["value"].typeId(), Gaffer.Box2iPlug.staticTypeId() )
		for i in range( 0, 3) :
			self.assertEqual( query["out"][i]["exists"].typeId(), Gaffer.BoolPlug.staticTypeId() )

		query.removeQuery( b )
		checkChildrenCount( query, 2 )
		self.assertEqual( query["queries"].children(), ( a, c ) )
		self.assertEqual( query["out"][0]["value"].typeId(), Gaffer.IntPlug.staticTypeId() )
		self.assertEqual( query["out"][1]["value"].typeId(), Gaffer.Box2iPlug.staticTypeId() )
		for i in range( 0, 2) :
			self.assertEqual( query["out"][i]["exists"].typeId(), Gaffer.BoolPlug.staticTypeId() )

		query.removeQuery( c )
		checkChildrenCount( query, 1 )
		query.removeQuery( a )
		checkChildrenCount( query, 0 )

	def testExists( self ) :

		options = GafferScene.CustomOptions()

		query = GafferScene.OptionQuery()
		query["scene"].setInput( options["out"] )

		q1 = query.addQuery( Gaffer.IntPlug( "i", Gaffer.Plug.Direction.Out, 1 ), "i" )
		q2 = query.addQuery( Gaffer.Color3fPlug( "c3f", Gaffer.Plug.Direction.Out, imath.Color3f( 1.0, 1.0, 1.0 ) ), "c1" )
		q3 = query.addQuery( Gaffer.FloatPlug( "f", Gaffer.Plug.Direction.Out, 0.5 ), "missing" )

		self.assertFalse( query["out"][0]["exists"].getValue() )
		self.assertFalse( query["out"][1]["exists"].getValue() )
		self.assertFalse( query["out"][2]["exists"].getValue() )

		options["options"].addChild( Gaffer.NameValuePlug( "i", IECore.IntData( 10 ) ) )
		options["options"].addChild( Gaffer.NameValuePlug( "c1", IECore.Color3fData( imath.Color3f( 0.5 ) ) ) )
		options["options"].addChild( Gaffer.NameValuePlug( "c2", IECore.Color3fData( imath.Color3f( 0.5 ) ) ) )

		self.assertTrue( query["out"][0]["exists"].getValue() )
		self.assertTrue( query["out"][1]["exists"].getValue() )
		self.assertFalse( query["out"][2]["exists"].getValue() )

		query.removeQuery( q2 )
		self.assertTrue( query["out"][0]["exists"].getValue() )
		self.assertFalse( query["out"][1]["exists"].getValue() )

		e4 = query.addQuery( Gaffer.Color3fPlug( "c3f", Gaffer.Plug.Direction.Out, imath.Color3f( 1.0, 1.0, 1.0 ) ), "c2" )

		self.assertTrue( query["out"][2]["exists"].getValue() )

	def testValues( self ) :

		options = GafferScene.CustomOptions()

		query = GafferScene.OptionQuery()
		query["scene"].setInput( options["out"] )

		q1 = query.addQuery( Gaffer.IntPlug( "i", Gaffer.Plug.Direction.Out, 1 ), "i" )
		q2 = query.addQuery( Gaffer.IntPlug( "i", Gaffer.Plug.Direction.Out, 1 ), "m" )
		q3 = query.addQuery( Gaffer.Box2iPlug( "b2i", Gaffer.Plug.Direction.Out, imath.Box2i( imath.V2i( 1 ), imath.V2i( 2 ) ) ), "b" )
		q4 = query.addQuery( Gaffer.Color3fPlug( "c3f", Gaffer.Plug.Direction.Out, imath.Color3f( 0.1, 0.2, 0.3 ) ), "c1" )

		self.assertEqual( query["out"][0]["value"].getValue(), 1 )
		self.assertEqual( query["out"][1]["value"].getValue(), 1 )
		self.assertEqual( query["out"][2]["value"].getValue(), imath.Box2i( imath.V2i( 1 ), imath.V2i( 2 ) ) )
		self.assertEqual( query["out"][3]["value"].getValue(), imath.Color3f( 0.1, 0.2, 0.3 ) )

		options["options"].addChild( Gaffer.NameValuePlug( "i", IECore.IntData( 2 ) ) )
		options["options"].addChild( Gaffer.NameValuePlug( "b", IECore.Box2iData( imath.Box2i( imath.V2i( 3 ), imath.V2i( 4 ) ) ) ) )
		options["options"].addChild( Gaffer.NameValuePlug( "c1", IECore.Color3fData( imath.Color3f( 0.4, 0.5, 0.6 ) ) ) )
		options["options"].addChild( Gaffer.NameValuePlug( "c2", IECore.Color3fData( imath.Color3f( 0.7, 0.8, 0.9 ) ) ) )

		self.assertEqual( query["out"][0]["value"].getValue(), 2 )
		self.assertEqual( query["out"][1]["value"].getValue(), 1 )
		self.assertEqual( query["out"][2]["value"].getValue(), imath.Box2i( imath.V2i( 3 ), imath.V2i( 4 ) ) )
		self.assertEqual( query["out"][3]["value"].getValue(), imath.Color3f( 0.4, 0.5, 0.6 ) )

		query.removeQuery( q3 )
		self.assertEqual( query["out"][0]["value"].getValue(), 2 )
		self.assertEqual( query["out"][1]["value"].getValue(), 1 )
		self.assertEqual( query["out"][2]["value"].getValue(), imath.Color3f( 0.4, 0.5, 0.6 ) )

		v5 = query.addQuery( Gaffer.Color3fPlug( "c3f", Gaffer.Plug.Direction.Out, imath.Color3f( 0.5 ) ), "c2" )

		self.assertEqual( query["out"][3]["value"].getValue(), imath.Color3f( 0.7, 0.8, 0.9 ) )

	def testChangeOptionValue( self ) :

		options = GafferScene.CustomOptions()
		options["options"].addChild( Gaffer.NameValuePlug( "i", IECore.IntData( 2 ), "i" ) )
		options["options"].addChild( Gaffer.NameValuePlug( "b", IECore.Box2iData( imath.Box2i( imath.V2i( 3 ), imath.V2i( 4 ) ) ), "b" ) )
		options["options"].addChild( Gaffer.NameValuePlug( "c", IECore.Color3fData( imath.Color3f( 0.4, 0.5, 0.6 ) ), "c" ) )

		q = GafferScene.OptionQuery()
		q["scene"].setInput( options["out"] )

		q1 = q.addQuery( Gaffer.IntPlug( "i", Gaffer.Plug.Direction.Out, 1 ), "i" )
		q2 = q.addQuery( Gaffer.Box2iPlug( "b2i", Gaffer.Plug.Direction.Out, imath.Box2i( imath.V2i( 1 ), imath.V2i( 2 ) ) ), "b" )
		q3 = q.addQuery( Gaffer.Color3fPlug( "c3f", Gaffer.Plug.Direction.Out, imath.Color3f( 0.1, 0.2, 0.3 ) ), "c" )

		self.assertTrue( q["out"][0]["exists"].getValue() )
		self.assertEqual( q["out"][0]["value"].getValue(), 2)
		self.assertTrue( q["out"][1]["exists"].getValue() )
		self.assertEqual( q["out"][1]["value"].getValue(), imath.Box2i( imath.V2i( 3 ), imath.V2i( 4 ) ) )
		self.assertTrue( q["out"][2]["exists"].getValue() )
		self.assertEqual( q["out"][2]["value"].getValue(), imath.Color3f( 0.4, 0.5, 0.6 ) )

		options["options"]["i"]["value"].setValue( 3 )
		options["options"]["b"]["value"].setValue( imath.Box2i( imath.V2i( 5 ), imath.V2i( 6 ) ) )
		options["options"]["c"]["value"].setValue( imath.Color3f( 1.0, 1.1, 1.2 ) )

		self.assertTrue( q["out"][0]["exists"].getValue() )
		self.assertEqual( q["out"][0]["value"].getValue(), 3)
		self.assertTrue( q["out"][1]["exists"].getValue() )
		self.assertEqual( q["out"][1]["value"].getValue(), imath.Box2i( imath.V2i( 5 ), imath.V2i( 6 ) ) )
		self.assertTrue( q["out"][2]["exists"].getValue() )
		self.assertEqual( q["out"][2]["value"].getValue(), imath.Color3f( 1.0, 1.1, 1.2 ) )

	def testChangeDefault( self ) :

		options = GafferScene.CustomOptions()

		query = GafferScene.OptionQuery()
		query["scene"].setInput( options["out"] )

		q1 = query.addQuery( Gaffer.IntPlug( "i", Gaffer.Plug.Direction.Out, 1 ), "i" )
		q2 = query.addQuery( Gaffer.Box2iPlug( "b2i", Gaffer.Plug.Direction.Out, imath.Box2i( imath.V2i( 1 ), imath.V2i( 2 ) ) ), "b" )
		q3 = query.addQuery( Gaffer.Color3fPlug( "c3f", Gaffer.Plug.Direction.Out, imath.Color3f( 0.1, 0.2, 0.3 ) ), "c" )

		self.assertFalse( query["out"][0]["exists"].getValue() )
		self.assertEqual( query["out"][0]["value"].getValue(), 1)
		self.assertFalse( query["out"][1]["exists"].getValue() )
		self.assertEqual( query["out"][1]["value"].getValue(), imath.Box2i( imath.V2i( 1 ), imath.V2i( 2 ) ) )
		self.assertFalse( query["out"][2]["exists"].getValue() )
		self.assertEqual( query["out"][2]["value"].getValue(), imath.Color3f( 0.1, 0.2, 0.3 ) )

		q1["value"].setValue( 3 )
		q2["value"].setValue( imath.Box2i( imath.V2i( 5 ), imath.V2i( 6 ) ) )
		q3["value"].setValue( imath.Color3f( 1.0, 1.1, 1.2 ) )

		self.assertFalse( query["out"][0]["exists"].getValue() )
		self.assertEqual( query["out"][0]["value"].getValue(), 3)
		self.assertFalse( query["out"][1]["exists"].getValue() )
		self.assertEqual( query["out"][1]["value"].getValue(), imath.Box2i( imath.V2i( 5 ), imath.V2i( 6 ) ) )
		self.assertFalse( query["out"][2]["exists"].getValue() )
		self.assertEqual( query["out"][2]["value"].getValue(), imath.Color3f( 1.0, 1.1, 1.2 ) )

	def testSerialisation( self ) :

		options = GafferScene.CustomOptions()
		options["options"].addChild( Gaffer.NameValuePlug( "i", IECore.IntData( 2 ), "i", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		options["options"].addChild( Gaffer.NameValuePlug( "b", IECore.Box2iData( imath.Box2i( imath.V2i( 3 ), imath.V2i( 4 ) ) ), "b", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		options["options"].addChild( Gaffer.NameValuePlug( "c", IECore.Color3fData( imath.Color3f( 0.4, 0.5, 0.6 ) ), "c", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )

		query = GafferScene.OptionQuery()
		query["scene"].setInput( options["out"] )

		q1 = query.addQuery( Gaffer.IntPlug( "i", Gaffer.Plug.Direction.Out, 1 ), "i" )
		q2 = query.addQuery( Gaffer.Box2iPlug( "b2i", Gaffer.Plug.Direction.Out, imath.Box2i( imath.V2i( 1 ), imath.V2i( 2 ) ) ), "b" )
		q3 = query.addQuery( Gaffer.Color3fPlug( "c3f", Gaffer.Plug.Direction.Out, imath.Color3f( 0.1, 0.2, 0.3 ) ), "c" )

		self.assertTrue( query["out"][0]["exists"].getValue() )
		self.assertEqual( query["out"][0]["value"].getValue(), 2)
		self.assertTrue( query["out"][1]["exists"].getValue() )
		self.assertEqual( query["out"][1]["value"].getValue(), imath.Box2i( imath.V2i( 3 ), imath.V2i( 4 ) ) )
		self.assertTrue( query["out"][2]["exists"].getValue() )
		self.assertEqual( query["out"][2]["value"].getValue(), imath.Color3f( 0.4, 0.5, 0.6 ) )

		target = GafferScene.CustomOptions( "target" )
		target["options"].addChild( Gaffer.NameValuePlug( "i", IECore.IntData( 3 ), "i", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		target["options"].addChild( Gaffer.NameValuePlug( "b", IECore.Box2iData( imath.Box2i( imath.V2i( 5 ), imath.V2i( 6 ) ) ), "b", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		target["options"].addChild( Gaffer.NameValuePlug( "c", IECore.Color3fData( imath.Color3f( 0.7, 0.8, 0.9 ) ), "c", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		target["options"].addChild( Gaffer.NameValuePlug( "bool", IECore.BoolData( False ), "bool", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		target["options"]["i"]["value"].setInput( query["out"][0]["value"] )
		target["options"]["b"]["value"].setInput( query["out"][1]["value"] )
		target["options"]["c"]["value"].setInput( query["out"][2]["value"] )
		target["options"]["bool"]["value"].setInput( query["out"][0]["exists"] )

		scriptNode = Gaffer.ScriptNode()
		scriptNode.addChild( options )
		scriptNode.addChild( query )
		scriptNode.addChild( target )

		self.assertTrue( scriptNode["OptionQuery"]["out"][0]["exists"].getValue() )
		self.assertEqual( scriptNode["OptionQuery"]["out"][0]["value"].getValue(), 2)
		self.assertTrue( scriptNode["OptionQuery"]["out"][1]["exists"].getValue() )
		self.assertEqual( scriptNode["OptionQuery"]["out"][1]["value"].getValue(), imath.Box2i( imath.V2i( 3 ), imath.V2i( 4 ) ) )
		self.assertTrue( scriptNode["OptionQuery"]["out"][2]["exists"].getValue() )
		self.assertEqual( scriptNode["OptionQuery"]["out"][2]["value"].getValue(), imath.Color3f( 0.4, 0.5, 0.6 ) )
		self.assertEqual( scriptNode["target"]["options"]["i"]["value"].getInput(), query["out"][0]["value"] )
		self.assertEqual( scriptNode["target"]["options"]["b"]["value"].getInput(), query["out"][1]["value"] )
		self.assertEqual( scriptNode["target"]["options"]["c"]["value"].getInput(), query["out"][2]["value"] )
		self.assertEqual( scriptNode["target"]["options"]["bool"]["value"].getInput(), query["out"][0]["exists"] )

		serialised = scriptNode.serialise()

		scriptNode = Gaffer.ScriptNode()
		scriptNode.execute( serialised )

		self.assertTrue( scriptNode["OptionQuery"]["out"][0]["exists"].getValue() )
		self.assertEqual( scriptNode["OptionQuery"]["out"][0]["value"].getValue(), 2)
		self.assertTrue( scriptNode["OptionQuery"]["out"][1]["exists"].getValue() )
		self.assertEqual( scriptNode["OptionQuery"]["out"][1]["value"].getValue(), imath.Box2i( imath.V2i( 3 ), imath.V2i( 4 ) ) )
		self.assertTrue( scriptNode["OptionQuery"]["out"][2]["exists"].getValue() )
		self.assertEqual( scriptNode["OptionQuery"]["out"][2]["value"].getValue(), imath.Color3f( 0.4, 0.5, 0.6 ) )
		self.assertEqual( str( scriptNode["target"]["options"]["i"]["value"].getInput() ), str( query["out"][0]["value"] ) )
		self.assertEqual( str( scriptNode["target"]["options"]["b"]["value"].getInput() ), str( query["out"][1]["value"] ) )
		self.assertEqual( str( scriptNode["target"]["options"]["c"]["value"].getInput() ), str( query["out"][2]["value"] ) )
		self.assertEqual( str( scriptNode["target"]["options"]["bool"]["value"].getInput() ), str( query["out"][0]["exists"] ) )

		scriptNode["OptionQuery"].removeQuery( scriptNode["OptionQuery"]["queries"][0] )

		self.assertTrue( scriptNode["OptionQuery"]["out"][0]["exists"].getValue() )
		self.assertEqual( scriptNode["OptionQuery"]["out"][0]["value"].getValue(), imath.Box2i( imath.V2i( 3 ), imath.V2i( 4 ) ) )
		self.assertTrue( scriptNode["OptionQuery"]["out"][1]["exists"].getValue() )
		self.assertEqual( scriptNode["OptionQuery"]["out"][1]["value"].getValue(), imath.Color3f( 0.4, 0.5, 0.6 ) )
		self.assertIsNone( scriptNode["target"]["options"]["i"]["value"].getInput() )
		self.assertIsNone( scriptNode["target"]["options"]["bool"]["value"].getInput() )
		self.assertEqual( str( scriptNode["target"]["options"]["b"]["value"].getInput() ), str( query["out"][1]["value"] ) )
		self.assertEqual( str( scriptNode["target"]["options"]["c"]["value"].getInput() ), str( query["out"][2]["value"] ) )

		serialised = scriptNode.serialise()

		scriptNode = Gaffer.ScriptNode()
		scriptNode.execute( serialised )

		self.assertTrue( scriptNode["OptionQuery"]["out"][0]["exists"].getValue() )
		self.assertEqual( scriptNode["OptionQuery"]["out"][0]["value"].getValue(), imath.Box2i( imath.V2i( 3 ), imath.V2i( 4 ) ) )
		self.assertTrue( scriptNode["OptionQuery"]["out"][1]["exists"].getValue() )
		self.assertEqual( scriptNode["OptionQuery"]["out"][1]["value"].getValue(), imath.Color3f( 0.4, 0.5, 0.6 ) )
		self.assertIsNone( scriptNode["target"]["options"]["i"]["value"].getInput() )
		self.assertIsNone( scriptNode["target"]["options"]["bool"]["value"].getInput() )
		self.assertEqual( str( scriptNode["target"]["options"]["b"]["value"].getInput() ), str( query["out"][1]["value"] ) )
		self.assertEqual( str( scriptNode["target"]["options"]["c"]["value"].getInput() ), str( query["out"][2]["value"] ) )

	def testObjectPlugQuery( self ) :

		value1 = IECoreScene.ShaderNetwork(
			shaders = {
				"output" : IECoreScene.Shader( "test1" ),
			},
			output = "output"
		)

		value2 = IECoreScene.ShaderNetwork(
			shaders = {
				"output" : IECoreScene.Shader( "test2" ),
			},
			output = "output"
		)

		customOptions = GafferScene.CustomOptions()
		customOptions["extraOptions"].setValue( {
			"testObject" : value1,
		} )

		query = GafferScene.OptionQuery()
		query["scene"].setInput( customOptions["out"] )
		query.addQuery( Gaffer.ObjectPlug( defaultValue = IECore.NullObject.defaultNullObject() ), "testObject" )

		self.assertTrue( query["out"][0]["exists"].getValue() )
		self.assertEqual( query["out"][0]["value"].getValue(), value1 )

		customOptions["extraOptions"].setValue( {
			"testObject" : value2,
		} )

		self.assertTrue( query["out"][0]["exists"].getValue() )
		self.assertEqual( query["out"][0]["value"].getValue(), value2 )

		query["queries"][0]["name"].setValue( "blah" )
		self.assertFalse( query["out"][0]["exists"].getValue() )
		self.assertEqual( query["out"][0]["value"].getValue(), IECore.NullObject.defaultNullObject() )

	def testMismatchedTypes( self ) :

		customOptions = GafferScene.CustomOptions()
		customOptions["extraOptions"].setValue( {
			"test" : IECore.StringData( "i am a string" ),
		} )

		query = GafferScene.OptionQuery()
		query["scene"].setInput( customOptions["out"] )
		query.addQuery( Gaffer.FloatPlug( defaultValue = 2.0 ), "test" )

		self.assertTrue( query["out"][0]["exists"].getValue() )
		self.assertEqual( query["out"][0]["value"].getValue(), 2.0 )

if __name__ == "__main__":
	unittest.main()
