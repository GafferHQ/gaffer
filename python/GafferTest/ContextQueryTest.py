#########################################################################
#
#  Copyright (c) 2022, Image Engine Design Inc. All rights reserved.
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
import GafferTest


class ContextQueryTest( GafferTest.TestCase ):

	def testDefault( self ) :

		q = Gaffer.ContextQuery()

		self.assertEqual( len( q["queries"].children() ), 0 )
		self.assertEqual( len( q["out"].children() ), 0 )

	def testOutput( self ) :

		q = Gaffer.ContextQuery()

		n1 = q.addQuery( Gaffer.IntPlug() )
		n2 = q.addQuery( Gaffer.Color3fPlug() )
		n3 = q.addQuery( Gaffer.Box2iPlug() )

		self.assertEqual( q.outPlugFromQueryPlug( n1 ), q["out"][0] )
		self.assertEqual( q.outPlugFromQueryPlug( n2 ), q["out"][1] )
		self.assertEqual( q.outPlugFromQueryPlug( n3 ), q["out"][2] )

		self.assertEqual( q.existsPlugFromQueryPlug( n1 ), q["out"][0]["exists"] )
		self.assertEqual( q.existsPlugFromQueryPlug( n2 ), q["out"][1]["exists"] )
		self.assertEqual( q.existsPlugFromQueryPlug( n3 ), q["out"][2]["exists"] )

		self.assertEqual( q.queryPlugFromOutPlug( q["out"][0]["value"] ), n1 )
		self.assertEqual( q.queryPlugFromOutPlug( q["out"][1]["value"] ), n2 )
		self.assertEqual( q.queryPlugFromOutPlug( q["out"][1]["value"]["r"] ), n2 )
		self.assertEqual( q.queryPlugFromOutPlug( q["out"][2]["value"] ), n3 )
		self.assertEqual( q.queryPlugFromOutPlug( q["out"][2]["value"]["min"] ), n3 )
		self.assertEqual( q.queryPlugFromOutPlug( q["out"][2]["value"]["min"]["x"] ), n3 )

		badPlug = Gaffer.NameValuePlug( "missing", Gaffer.Color3fPlug(), "badPlug" )
		self.assertRaises( IECore.Exception, q.queryPlugFromOutPlug, badPlug )

	def testAddRemoveQuery( self ) :

		def checkChildrenCount( plug, count ) :
			self.assertEqual( len( plug["queries"].children() ), count )
			self.assertEqual( len( plug["out"].children() ), count )

		q = Gaffer.ContextQuery()

		checkChildrenCount( q, 0 )

		a = q.addQuery( Gaffer.IntPlug() )
		checkChildrenCount( q, 1 )
		self.assertEqual( q["queries"]["query0"]["name"].getValue(), "" )
		self.assertEqual( q["queries"]["query0"]["value"].getValue(), 0 )
		self.assertEqual( q["out"][0]["exists"].typeId(), Gaffer.BoolPlug.staticTypeId() )
		self.assertEqual( q["out"][0]["value"].typeId(), Gaffer.IntPlug.staticTypeId() )

		b = q.addQuery( Gaffer.Color3fPlug( "c3f" ), "color" )
		checkChildrenCount( q, 2 )
		self.assertEqual( q["queries"].children(), ( a, b ) )
		self.assertEqual( q["queries"]["query1"]["name"].getValue(), "color" )
		self.assertEqual( q["queries"]["query1"]["value"].getValue(), imath.Color3f() )
		self.assertEqual( q["out"][0]["value"].typeId(), Gaffer.IntPlug.staticTypeId() )
		self.assertEqual( q["out"][1]["value"].typeId(), Gaffer.Color3fPlug.staticTypeId() )
		for i in range( 0, 2) :
			self.assertEqual( q["out"][i]["exists"].typeId(), Gaffer.BoolPlug.staticTypeId() )

		c = q.addQuery( Gaffer.Box2iPlug( "b2i", Gaffer.Plug.Direction.Out, imath.Box2i( imath.V2i( 1 ), imath.V2i( 2 ) ) ), "box" )
		checkChildrenCount( q, 3 )
		self.assertEqual( q["queries"].children(), ( a, b, c ) )
		self.assertEqual( q["queries"]["query2"]["name"].getValue(), "box" )
		self.assertEqual( q["queries"]["query2"]["value"].getValue(), imath.Box2i( imath.V2i( 1 ), imath.V2i( 2 ) ) )
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

	def testValuesAndExists( self ) :

		q = Gaffer.ContextQuery()

		v1 = q.addQuery( Gaffer.IntPlug( "i", Gaffer.Plug.Direction.Out, 1 ), "i" )
		v2 = q.addQuery( Gaffer.IntPlug( "i", Gaffer.Plug.Direction.Out, 1 ), "m" )
		v3 = q.addQuery( Gaffer.Box2iPlug( "b2i", Gaffer.Plug.Direction.Out, imath.Box2i( imath.V2i( 1 ), imath.V2i( 2 ) ) ), "b" )
		v4 = q.addQuery( Gaffer.Color3fPlug( "c3f", Gaffer.Plug.Direction.Out, imath.Color3f( 0.1, 0.2, 0.3 ) ), "c" )
		v5 = q.addQuery( Gaffer.Color3fPlug( "c3f", Gaffer.Plug.Direction.Out, imath.Color3f( 0.1, 0.2, 0.3 ) ), "m" )
		v6 = q.addQuery( Gaffer.Color3fPlug( "c3f", Gaffer.Plug.Direction.Out, imath.Color3f( 0.1, 0.2, 0.3 ) ), "m2" )
		v7 = q.addQuery( Gaffer.FloatPlug( "f", Gaffer.Plug.Direction.Out, 0.5 ), "missing.m" )

		self.assertFalse( q["out"][0]["exists"].getValue() )
		self.assertEqual( q["out"][0]["value"].getValue(), 1 )
		self.assertFalse( q["out"][1]["exists"].getValue() )
		self.assertEqual( q["out"][1]["value"].getValue(), 1 )
		self.assertFalse( q["out"][2]["exists"].getValue() )
		self.assertEqual( q["out"][2]["value"].getValue(), imath.Box2i( imath.V2i( 1 ), imath.V2i( 2 ) ) )
		self.assertFalse( q["out"][3]["exists"].getValue() )
		self.assertEqual( q["out"][3]["value"].getValue(), imath.Color3f( 0.1, 0.2, 0.3 ) )
		self.assertFalse( q["out"][4]["exists"].getValue() )
		self.assertEqual( q["out"][4]["value"].getValue(), imath.Color3f( 0.1, 0.2, 0.3 ) )
		self.assertFalse( q["out"][5]["exists"].getValue() )
		self.assertEqual( q["out"][5]["value"].getValue(), imath.Color3f( 0.1, 0.2, 0.3 ) )
		self.assertFalse( q["out"][6]["exists"].getValue() )
		self.assertEqual( q["out"][6]["value"].getValue(), 0.5 )

		testC = Gaffer.Context()
		testC["i"] = 2
		testC["b"] = imath.Box2i( imath.V2i( 3 ), imath.V2i( 4 ) )
		testC["c"] = imath.Color3f( 0.7, 0.8, 0.9 )
		with testC:
			self.assertTrue( q["out"][0]["exists"].getValue() )
			self.assertEqual( q["out"][0]["value"].getValue(), 2 )
			self.assertFalse( q["out"][1]["exists"].getValue() )
			self.assertEqual( q["out"][1]["value"].getValue(), 1 )
			self.assertTrue( q["out"][2]["exists"].getValue() )
			self.assertEqual( q["out"][2]["value"].getValue(), imath.Box2i( imath.V2i( 3 ), imath.V2i( 4 ) ) )
			self.assertTrue( q["out"][3]["exists"].getValue() )
			self.assertEqual( q["out"][3]["value"].getValue(), imath.Color3f( 0.7, 0.8, 0.9 ) )
			self.assertFalse( q["out"][4]["exists"].getValue() )
			self.assertEqual( q["out"][4]["value"].getValue(), imath.Color3f( 0.1, 0.2, 0.3 ) )
			self.assertFalse( q["out"][5]["exists"].getValue() )
			self.assertEqual( q["out"][5]["value"].getValue(), imath.Color3f( 0.1, 0.2, 0.3 ) )
			self.assertFalse( q["out"][6]["exists"].getValue() )
			self.assertEqual( q["out"][6]["value"].getValue(), 0.5 )

		q.removeQuery( v4 )
		with testC:
			self.assertTrue( q["out"][0]["exists"].getValue() )
			self.assertEqual( q["out"][0]["value"].getValue(), 2 )
			self.assertFalse( q["out"][1]["exists"].getValue() )
			self.assertEqual( q["out"][1]["value"].getValue(), 1 )
			self.assertTrue( q["out"][2]["exists"].getValue() )
			self.assertEqual( q["out"][2]["value"].getValue(), imath.Box2i( imath.V2i( 3 ), imath.V2i( 4 ) ) )
			self.assertFalse( q["out"][3]["exists"].getValue() )
			self.assertEqual( q["out"][3]["value"].getValue(), imath.Color3f( 0.1, 0.2, 0.3 ) )
			self.assertFalse( q["out"][4]["exists"].getValue() )
			self.assertEqual( q["out"][4]["value"].getValue(), imath.Color3f( 0.1, 0.2, 0.3 ) )
			self.assertFalse( q["out"][5]["exists"].getValue() )
			self.assertEqual( q["out"][5]["value"].getValue(), 0.5 )

		v8 = q.addQuery( Gaffer.Color3fPlug( "c3f", Gaffer.Plug.Direction.Out, imath.Color3f( 0.1, 0.2, 0.3 ) ), "c" )

		with testC:
			self.assertTrue( q["out"][6]["exists"].getValue() )
			self.assertEqual( q["out"][6]["value"].getValue(), imath.Color3f( 0.7, 0.8, 0.9 ) )

	def testChangeDefault( self ) :

		q = Gaffer.ContextQuery()

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

		q = Gaffer.ContextQuery()

		q.addQuery( Gaffer.IntPlug( "i", Gaffer.Plug.Direction.Out, 1 ), "i" )
		q.addQuery( Gaffer.Color3fPlug( "c3f", Gaffer.Plug.Direction.Out, imath.Color3f( 0.1, 0.2, 0.3 ) ), "c3f" )

		t = Gaffer.Node( "target" )
		t.addChild( Gaffer.IntPlug( "i", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		t.addChild( Gaffer.Color3fPlug( "c", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		t.addChild( Gaffer.BoolPlug( "b1", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		t.addChild( Gaffer.BoolPlug( "b2", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		t["i"].setInput( q["out"][0]["value"] )
		t["c"].setInput( q["out"][1]["value"] )
		t["b1"].setInput( q["out"][0]["exists"] )
		t["b2"].setInput( q["out"][1]["exists"] )

		scriptNode = Gaffer.ScriptNode()
		scriptNode.addChild( q )
		scriptNode.addChild( t )

		testC = Gaffer.Context()
		testC["i"] = 2
		testC["c3f"] = imath.Color3f( 0.7, 0.8, 0.9 )
		with testC:
			self.assertTrue( scriptNode["ContextQuery"]["out"][0]["exists"].getValue() )
			self.assertEqual( scriptNode["ContextQuery"]["out"][0]["value"].getValue(), 2)
			self.assertTrue( scriptNode["ContextQuery"]["out"][1]["exists"].getValue() )
			self.assertEqual( scriptNode["ContextQuery"]["out"][1]["value"].getValue(), imath.Color3f( 0.7, 0.8, 0.9 ) )
			self.assertEqual( scriptNode["target"]["i"].getInput(), q["out"][0]["value"] )
			self.assertEqual( scriptNode["target"]["c"].getInput(), q["out"][1]["value"] )
			self.assertEqual( scriptNode["target"]["b1"].getInput(), q["out"][0]["exists"] )
			self.assertEqual( scriptNode["target"]["b2"].getInput(), q["out"][1]["exists"] )


		serialised = scriptNode.serialise()

		scriptNode = Gaffer.ScriptNode()
		scriptNode.execute( serialised )

		with testC:
			self.assertTrue( scriptNode["ContextQuery"]["out"][0]["exists"].getValue() )
			self.assertEqual( scriptNode["ContextQuery"]["out"][0]["value"].getValue(), 2)
			self.assertTrue( scriptNode["ContextQuery"]["out"][1]["exists"].getValue() )
			self.assertEqual( scriptNode["ContextQuery"]["out"][1]["value"].getValue(), imath.Color3f( 0.7, 0.8, 0.9 ) )
		self.assertEqual( str( scriptNode["target"]["i"].getInput() ), str( q["out"][0]["value"] ) )
		self.assertEqual( str( scriptNode["target"]["c"].getInput() ), str( q["out"][1]["value"] ) )
		self.assertEqual( str( scriptNode["target"]["b1"].getInput() ), str( q["out"][0]["exists"] ) )
		self.assertEqual( str( scriptNode["target"]["b2"].getInput() ), str( q["out"][1]["exists"] ) )

		scriptNode["ContextQuery"].removeQuery( scriptNode["ContextQuery"]["queries"][0] )

		with testC:
			self.assertTrue( scriptNode["ContextQuery"]["out"][0]["exists"].getValue() )
			self.assertEqual( scriptNode["ContextQuery"]["out"][0]["value"].getValue(), imath.Color3f( 0.7, 0.8, 0.9 ) )
		self.assertIsNone( scriptNode["target"]["i"].getInput() )
		self.assertEqual( str( scriptNode["target"]["c"].getInput() ), str( q["out"][1]["value"] ) )
		self.assertIsNone( scriptNode["target"]["b1"].getInput() )
		self.assertEqual( str( scriptNode["target"]["b2"].getInput() ), str( q["out"][1]["exists"] ) )

		serialised = scriptNode.serialise()

		scriptNode = Gaffer.ScriptNode()
		scriptNode.execute( serialised )

		with testC:
			self.assertTrue( scriptNode["ContextQuery"]["out"][0]["exists"].getValue() )
			self.assertEqual( scriptNode["ContextQuery"]["out"][0]["value"].getValue(), imath.Color3f( 0.7, 0.8, 0.9 ) )
		self.assertIsNone( scriptNode["target"]["i"].getInput() )
		self.assertEqual( str( scriptNode["target"]["c"].getInput() ), str( q["out"][1]["value"] ) )
		self.assertIsNone( scriptNode["target"]["b1"].getInput() )
		self.assertEqual( str( scriptNode["target"]["b2"].getInput() ), str( q["out"][1]["exists"] ) )

if __name__ == "__main__":
	unittest.main()
