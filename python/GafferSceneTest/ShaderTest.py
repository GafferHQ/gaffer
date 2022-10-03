##########################################################################
#
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
import imath

import IECore

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest

class ShaderTest( GafferSceneTest.SceneTestCase ) :

	def testDirtyPropagation( self ) :

		s = GafferSceneTest.TestShader( "s" )

		cs = GafferTest.CapturingSlot( s.plugDirtiedSignal() )

		s["parameters"]["i"].setValue( 10 )

		d = set( [ a[0].fullName() for a in cs ] )

		self.assertTrue( "s.out" in d )
		self.assertTrue( "s.out.r" in d )
		self.assertTrue( "s.out.g" in d )
		self.assertTrue( "s.out.b" in d )

	def testDisabling( self ) :

		s = GafferSceneTest.TestShader()

		self.assertTrue( s["enabled"].isSame( s.enabledPlug() ) )
		self.assertEqual( s.correspondingInput( s["out"] ), None )

		h = s.attributesHash()
		self.assertEqual( len( s.attributes() ), 1 )

		s["enabled"].setValue( False )

		self.assertEqual( len( s.attributes() ), 0 )
		self.assertNotEqual( s.attributesHash(), h )

	def testNodeNameBlindData( self ) :

		s = GafferSceneTest.TestShader( "node1" )
		s["type"].setValue( "test:surface" )

		h1 = s.attributesHash()
		s1 = s.attributes()["test:surface"]
		cs = GafferTest.CapturingSlot( s.plugDirtiedSignal() )

		s.setName( "node2" )

		self.assertTrue( s["out"] in [ x[0] for x in cs ] )

		self.assertNotEqual( s.attributesHash(), h1 )

		s2 = s.attributes()["test:surface"]
		self.assertNotEqual( s2, s1 )

		self.assertEqual( s1.getShader( "node1" ).blindData()["label"], IECore.StringData( "node1" ) )
		self.assertEqual( s2.getShader( "node2" ).blindData()["label"], IECore.StringData( "node2" ) )

	def testNodeColorBlindData( self ) :

		s = GafferSceneTest.TestShader( "test" )
		s["type"].setValue( "test:surface" )

		h1 = s.attributesHash()
		s1 = s.attributes()["test:surface"]

		cs = GafferTest.CapturingSlot( s.plugDirtiedSignal() )

		Gaffer.Metadata.registerValue( s, "nodeGadget:color", imath.Color3f( 1, 0, 0 ) )

		self.assertTrue( s["out"] in [ x[0] for x in cs ] )

		self.assertNotEqual( s.attributesHash(), h1 )

		s2 = s.attributes()["test:surface"]
		self.assertNotEqual( s2, s1 )

		self.assertEqual( s1.getShader( "test" ).blindData()["gaffer:nodeColor"], IECore.Color3fData( imath.Color3f( 0 ) ) )
		self.assertEqual( s2.getShader( "test" ).blindData()["gaffer:nodeColor"], IECore.Color3fData( imath.Color3f( 1, 0, 0 ) ) )

	def testShaderTypesInAttributes( self ) :

		surface = GafferSceneTest.TestShader( "surface" )
		surface["name"].setValue( "testSurface" )
		surface["type"].setValue( "test:surface" )
		surface["parameters"]["t"] = Gaffer.Color3fPlug()

		texture = GafferSceneTest.TestShader( "texture" )
		texture["name"].setValue( "testTexture" )
		texture["type"].setValue( "test:shader" )

		surface["parameters"]["t"].setInput( texture["out"] )

		network = surface.attributes()["test:surface"]
		self.assertEqual( network.getShader( "texture" ).type, "test:shader" )
		self.assertEqual( network.getShader( "surface" ).type, "test:surface" )

		surface["attributeSuffix"].setValue( "TestSurface" )
		self.assertIn( "test:surface:TestSurface", surface.attributes() )

	def testDirtyPropagationThroughShaderAssignment( self ) :

		n = GafferSceneTest.TestShader()

		p = GafferScene.Plane()
		a = GafferScene.ShaderAssignment()
		a["in"].setInput( p["out"] )
		a["shader"].setInput( n["out"] )

		cs = GafferTest.CapturingSlot( a.plugDirtiedSignal() )

		n["parameters"]["i"].setValue( 1 )

		self.assertEqual(
			[ c[0] for c in cs ],
			[
				a["shader"],
				a["out"]["attributes"],
				a["out"],
			],
		)

	def testParameterValuesWhenConnected( self ) :

		n1 = GafferSceneTest.TestShader( "n1" )
		n2 = GafferSceneTest.TestShader( "n2" )
		n3 = GafferSceneTest.TestShader( "n3" )
		n3["type"].setValue( "test:surface" )

		n3["parameters"]["i"].setInput( n1["out"]["r"] )
		n3["parameters"]["c"].setValue( imath.Color3f( 2, 3, 4 ) )
		n3["parameters"]["c"].setInput( n2["out"] )

		network = n3.attributes()["test:surface"]
		self.assertEqual( len( network ), 3 )
		self.assertEqual(
			network.inputConnections( "n3" ), [
				network.Connection( network.Parameter( "n2", "", ), network.Parameter( "n3", "c" ) ),
				network.Connection( network.Parameter( "n1", "r", ), network.Parameter( "n3", "i" ) )
			]
		)

		# The values set on the parameters don't come through, but we get the default value from the
		# connected shader's output as the correct type
		self.assertEqual(
			network.getShader( "n3" ).parameters,
			IECore.CompoundData( { "i" : IECore.IntData( 0 ), "c" : IECore.Color3fData( imath.Color3f( 0 ) ) } )
		)

	def testDetectCyclicConnections( self ) :

		n1 = GafferSceneTest.TestShader()
		n2 = GafferSceneTest.TestShader()
		n3 = GafferSceneTest.TestShader()

		n2["parameters"]["i"].setInput( n1["out"]["r"] )
		n3["parameters"]["i"].setInput( n2["out"]["g"] )

		with IECore.CapturingMessageHandler() as mh :
			n1["parameters"]["i"].setInput( n3["out"]["b"] )

		# We expect a message warning of the cycle when the
		# connection is made.
		self.assertEqual( len( mh.messages ), 1 )
		self.assertTrue( "Plug dirty propagation" in mh.messages[0].context )

		# And a hard error when we attempt to actually generate
		# the shader network.
		for node in ( n1, n2, n3 ) :
			self.assertRaisesRegex( RuntimeError, "cycle", node.attributesHash )
			self.assertRaisesRegex( RuntimeError, "cycle", node.attributes )

	def testSwitch( self ) :

		n1 = GafferSceneTest.TestShader( "n1" )
		n2 = GafferSceneTest.TestShader( "n2" )
		n3 = GafferSceneTest.TestShader( "n3" )
		n3["type"].setValue( "test:surface" )

		switch = Gaffer.Switch()
		switch.setup( n3["parameters"]["c"] )

		switch["in"][0].setInput( n1["out"] )
		switch["in"][1].setInput( n2["out"] )

		n3["parameters"]["c"].setInput( switch["out"] )

		for i in range( 0, 3 ) :

			switch["index"].setValue( i )
			effectiveIndex = i % 2

			network = n3.attributes()["test:surface"]
			self.assertEqual( len( network ), 2 )
			self.assertEqual(
				network.inputConnections( "n3" ),
				[ network.Connection( network.Parameter( "n{0}".format( effectiveIndex + 1 ), "", ), network.Parameter( "n3", "c" ) ) ]
			)

	def testSwitchWithContextSensitiveIndex( self ) :

		s = Gaffer.ScriptNode()

		s["n1"] = GafferSceneTest.TestShader()
		s["n2"] = GafferSceneTest.TestShader()
		s["n3"] = GafferSceneTest.TestShader()
		s["n3"]["type"].setValue( "test:surface" )

		s["switch"] = Gaffer.Switch()
		s["switch"].setup( s["n3"]["parameters"]["c"] )

		s["switch"]["in"][0].setInput( s["n1"]["out"] )
		s["switch"]["in"][1].setInput( s["n2"]["out"] )

		s["n3"]["parameters"]["c"].setInput( s["switch"]["out"] )

		network = s["n3"].attributes()["test:surface"]
		self.assertEqual( len( network ), 2 )
		self.assertEqual(
			network.inputConnections( "n3" ),
			[ network.Connection( network.Parameter( "n1", "", ), network.Parameter( "n3", "c" ) ) ]
		)

		s["expression"] = Gaffer.Expression()
		s["expression"].setExpression( 'parent["switch"]["index"] = context["index"]' )

		with Gaffer.Context() as context :

			for i in range( 0, 3 ) :

				context["index"] = i
				effectiveIndex = i % 2

				network = s["n3"].attributes()["test:surface"]
				self.assertEqual( len( network ), 2 )
				self.assertEqual(
					network.inputConnections( "n3" ),
					[ network.Connection( network.Parameter( "n{0}".format( effectiveIndex + 1 ), "", ), network.Parameter( "n3", "c" ) ) ]
				)

	def testSwitchWithComponentConnections( self ) :

		s = Gaffer.ScriptNode()

		s["n1"] = GafferSceneTest.TestShader( "n1" )
		s["n2"] = GafferSceneTest.TestShader( "n2" )
		s["n3"] = GafferSceneTest.TestShader( "n3" )
		s["n3"]["type"].setValue( "test:surface" )

		s["switch"] = Gaffer.Switch()
		s["switch"].setup( s["n3"]["parameters"]["c"] )

		s["switch"]["in"][0].setInput( s["n1"]["out"] )
		s["switch"]["in"][1].setInput( s["n2"]["out"] )

		s["n3"]["parameters"]["c"]["r"].setInput( s["switch"]["out"]["r"] )

		s["expression"] = Gaffer.Expression()
		s["expression"].setExpression( 'parent["switch"]["index"] = context["index"]' )

		with Gaffer.Context() as context :

			for i in range( 0, 3 ) :

				context["index"] = i
				effectiveIndex = i % 2

				network = s["n3"].attributes()["test:surface"]
				self.assertEqual( len( network ), 2 )
				self.assertEqual(
					network.inputConnections( "n3" ),
					[ network.Connection( network.Parameter( "n{0}".format( effectiveIndex + 1 ), "r", ), network.Parameter( "n3", "c.r" ) ) ]
				)

	def testComponentToComponentConnections( self ) :

		n1 = GafferSceneTest.TestShader( "n1" )
		n2 = GafferSceneTest.TestShader( "n2" )
		n2["type"].setValue( "test:surface" )

		n2["parameters"]["c"]["r"].setInput( n1["out"]["g"] )
		n2["parameters"]["c"]["g"].setInput( n1["out"]["b"] )
		n2["parameters"]["c"]["b"].setInput( n1["out"]["r"] )

		network = n2.attributes()["test:surface"]
		self.assertEqual(
			network.inputConnections( "n2" ),
			[
				( ( "n1", "r" ), ( "n2", "c.b" ) ),
				( ( "n1", "b" ), ( "n2", "c.g" ) ),
				( ( "n1", "g" ), ( "n2", "c.r" ) ),
			]
		)

	def testNameSwitch( self ) :

		n1 = GafferSceneTest.TestShader( "n1" )
		n2 = GafferSceneTest.TestShader( "n2" )
		n3 = GafferSceneTest.TestShader( "n3" )
		n3["type"].setValue( "test:surface" )

		switch = Gaffer.NameSwitch()
		switch.setup( n3["parameters"]["c"] )

		switch["in"].resize( 2 )
		switch["in"][0]["value"].setInput( n1["out"] )
		switch["in"][1]["value"].setInput( n2["out"] )
		switch["in"][1]["name"].setValue( "n2" )

		n3["parameters"]["c"].setInput( switch["out"]["value"] )

		for n in ( "n1", "n2" ) :

			switch["selector"].setValue( n )

			network = n3.attributes()["test:surface"]
			self.assertEqual( len( network ), 2 )
			self.assertEqual(
				network.inputConnections( "n3" ),
				[ network.Connection( network.Parameter( n, "", ), network.Parameter( "n3", "c" ) ) ]
			)

if __name__ == "__main__":
	unittest.main()
