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
import IECoreScene

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
				network.Connection( network.Parameter( "n2", "out", ), network.Parameter( "n3", "c" ) ),
				network.Connection( network.Parameter( "n1", "out.r", ), network.Parameter( "n3", "i" ) )
			]
		)

		# The values set on the parameters don't come through, but we get the default value from the
		# connected shader's output as the correct type
		self.assertEqual(
			network.getShader( "n3" ).parameters,
			IECore.CompoundData( { "i" : IECore.IntData( 0 ), "c" : IECore.Color3fData( imath.Color3f( 0 ) ), "spline" : IECore.SplinefColor3fData() } )
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
				[ network.Connection( network.Parameter( "n{0}".format( effectiveIndex + 1 ), "out", ), network.Parameter( "n3", "c" ) ) ]
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
			[ network.Connection( network.Parameter( "n1", "out", ), network.Parameter( "n3", "c" ) ) ]
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
					[ network.Connection( network.Parameter( "n{0}".format( effectiveIndex + 1 ), "out", ), network.Parameter( "n3", "c" ) ) ]
				)

	def testSecondSwitchWithContextSensitiveIndex( self ) :

		contextQuery = Gaffer.ContextQuery()
		contextQuery.addQuery( Gaffer.IntPlug(), "index" )

		n1 = GafferSceneTest.TestShader( "n1" )
		n2 = GafferSceneTest.TestShader( "n2" )
		n3 = GafferSceneTest.TestShader( "n3" )
		n3["type"].setValue( "test:surface" )

		switch1 = Gaffer.Switch( "switch1" )
		switch1.setup( n3["parameters"]["c"] )
		switch2 = Gaffer.Switch( "switch2" )
		switch2.setup( n3["parameters"]["c"] )

		switch1["index"].setInput( contextQuery["out"][0]["value"] )
		switch1["in"][0].setInput( n1["out"] )
		switch1["in"][1].setInput( n2["out"] )

		switch2["index"].setInput( contextQuery["out"][0]["value"] )
		switch2["in"][0].setInput( n1["out"] )
		switch2["in"][1].setInput( switch1["out"] )

		n3["parameters"]["c"].setInput( switch2["out"] )

		with Gaffer.Context() as context :

			context["index"] = 1

			network = n3.attributes()["test:surface"]
			self.assertEqual( len( network ), 2 )
			self.assertEqual(
				network.inputConnections( "n3" ),
				[ network.Connection( network.Parameter( "n2", "out", ), network.Parameter( "n3", "c" ) ) ]
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
					[ network.Connection( network.Parameter( "n{0}".format( effectiveIndex + 1 ), "out.r", ), network.Parameter( "n3", "c.r" ) ) ]
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
				( ( "n1", "out.r" ), ( "n2", "c.b" ) ),
				( ( "n1", "out.b" ), ( "n2", "c.g" ) ),
				( ( "n1", "out.g" ), ( "n2", "c.r" ) ),
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
				[ network.Connection( network.Parameter( n, "out", ), network.Parameter( "n3", "c" ) ) ]
			)

	def testConnectionFromSwitchIndex( self ) :

		switch = Gaffer.Switch()
		shader = GafferSceneTest.TestShader()
		shader["type"].setValue( "test:surface" )
		shader["parameters"]["i"].setInput( switch["index"] )

		network = shader.attributes()["test:surface"]
		self.assertEqual( network.outputShader().parameters["i"], IECore.IntData( 0 ) )

	def testContextProcessors( self ) :

		contextQuery = Gaffer.ContextQuery()
		contextQuery.addQuery( Gaffer.Color3fPlug(), "c" )

		texture = GafferSceneTest.TestShader( "texture" )
		texture["parameters"]["c"].setInput( contextQuery["out"][0]["value"] )

		redContext = Gaffer.ContextVariables()
		redContext.setup( texture["out"] )
		redContext["variables"].addChild( Gaffer.NameValuePlug( "c", imath.Color3f( 1, 0, 0 ) ) )
		redContext["in"].setInput( texture["out"] )

		greenContext = Gaffer.ContextVariables()
		greenContext.setup( texture["out"] )
		greenContext["variables"].addChild( Gaffer.NameValuePlug( "c", imath.Color3f( 0, 1, 0 ) ) )
		greenContext["in"].setInput( texture["out"] )

		mix = GafferSceneTest.TestShader( "mix" )
		mix.loadShader( "mix" )
		mix["type"].setValue( "test:surface" )
		mix["parameters"]["a"].setInput( redContext["out"] )
		mix["parameters"]["b"].setInput( greenContext["out"] )

		shaderPlug = GafferScene.ShaderPlug()
		shaderPlug.setInput( mix["out"] )

		network = shaderPlug.attributes()["test:surface"]
		self.assertEqual( len( network.shaders() ), 3 )
		self.assertEqual( network.getOutput(), ( "mix", "out" ) )

		aInput = network.input( ( "mix", "a" ) )
		bInput = network.input( ( "mix", "b" ) )

		self.assertEqual( network.getShader( aInput.shader ).parameters["c"], IECore.Color3fData( imath.Color3f( 1, 0, 0 ) ) )
		self.assertEqual( network.getShader( bInput.shader ).parameters["c"], IECore.Color3fData( imath.Color3f( 0, 1, 0 ) ) )

		self.assertEqual( shaderPlug.parameterSource( ( "texture", "c" ) ), texture["parameters"]["c"] )
		self.assertEqual( shaderPlug.parameterSource( ( "texture1", "c" ) ), texture["parameters"]["c"] )

	def testContextProcessorsWithSpreadsheets( self ) :

		spreadsheet = Gaffer.Spreadsheet()
		spreadsheet["selector"].setValue( "${color}" )
		spreadsheet["rows"].addColumn( Gaffer.Color3fPlug( "c" ) )
		spreadsheet["rows"].addRows( 2 )
		spreadsheet["rows"][1]["name"].setValue( "red" )
		spreadsheet["rows"][1]["cells"]["c"]["value"].setValue( imath.Color3f( 1, 0, 0 ) )
		spreadsheet["rows"][2]["name"].setValue( "green" )
		spreadsheet["rows"][2]["cells"]["c"]["value"].setValue( imath.Color3f( 0, 1, 0 ) )

		texture = GafferSceneTest.TestShader( "texture" )
		texture["parameters"]["c"].setInput( spreadsheet["out"]["c"] )

		redContext = Gaffer.ContextVariables()
		redContext.setup( texture["out"] )
		redContext["variables"].addChild( Gaffer.NameValuePlug( "color", "red" ) )
		redContext["in"].setInput( texture["out"] )

		greenContext = Gaffer.ContextVariables()
		greenContext.setup( texture["out"] )
		greenContext["variables"].addChild( Gaffer.NameValuePlug( "color", "green" ) )
		greenContext["in"].setInput( texture["out"] )

		mix = GafferSceneTest.TestShader( "mix" )
		mix.loadShader( "mix" )
		mix["type"].setValue( "test:surface" )
		mix["parameters"]["a"].setInput( redContext["out"] )
		mix["parameters"]["b"].setInput( greenContext["out"] )

		shaderPlug = GafferScene.ShaderPlug()
		shaderPlug.setInput( mix["out"] )

		network = shaderPlug.attributes()["test:surface"]
		self.assertEqual( len( network.shaders() ), 3 )
		self.assertEqual( network.getOutput(), ( "mix", "out" ) )

		aInput = network.input( ( "mix", "a" ) )
		bInput = network.input( ( "mix", "b" ) )

		self.assertEqual( network.getShader( aInput.shader ).parameters["c"], IECore.Color3fData( imath.Color3f( 1, 0, 0 ) ) )
		self.assertEqual( network.getShader( bInput.shader ).parameters["c"], IECore.Color3fData( imath.Color3f( 0, 1, 0 ) ) )

	def testContextProcessorsWithInlineSpreadsheets( self ) :

		redTexture = GafferSceneTest.TestShader( "redTexture" )
		redTexture["parameters"]["c"].setValue( imath.Color3f( 1, 0, 0 ) )
		greenTexture = GafferSceneTest.TestShader( "greenTexture" )
		greenTexture["parameters"]["c"].setValue( imath.Color3f( 0, 1, 0 ) )

		spreadsheet = Gaffer.Spreadsheet()
		spreadsheet["selector"].setValue( "${color}" )
		spreadsheet["rows"].addColumn( Gaffer.Color3fPlug( "texture" ) )
		spreadsheet["rows"].addRows( 2 )
		spreadsheet["rows"][1]["name"].setValue( "red" )
		spreadsheet["rows"][1]["cells"]["texture"]["value"].setInput( redTexture["out"] )
		spreadsheet["rows"][2]["name"].setValue( "green" )
		spreadsheet["rows"][2]["cells"]["texture"]["value"].setInput( greenTexture["out"] )

		redContext = Gaffer.ContextVariables()
		redContext.setup( spreadsheet["out"]["texture"] )
		redContext["variables"].addChild( Gaffer.NameValuePlug( "color", "red" ) )
		redContext["in"].setInput( spreadsheet["out"]["texture"] )

		greenContext = Gaffer.ContextVariables()
		greenContext.setup( spreadsheet["out"]["texture"] )
		greenContext["variables"].addChild( Gaffer.NameValuePlug( "color", "green" ) )
		greenContext["in"].setInput( spreadsheet["out"]["texture"] )

		mix = GafferSceneTest.TestShader( "mix" )
		mix.loadShader( "mix" )
		mix["type"].setValue( "test:surface" )
		mix["parameters"]["a"].setInput( redContext["out"] )
		mix["parameters"]["b"].setInput( greenContext["out"] )

		shaderPlug = GafferScene.ShaderPlug()
		shaderPlug.setInput( mix["out"] )

		network = shaderPlug.attributes()["test:surface"]
		self.assertEqual( len( network.shaders() ), 3 )
		self.assertEqual( network.getOutput(), ( "mix", "out" ) )

		aInput = network.input( ( "mix", "a" ) )
		bInput = network.input( ( "mix", "b" ) )

		self.assertEqual( network.getShader( aInput.shader ).parameters["c"], IECore.Color3fData( imath.Color3f( 1, 0, 0 ) ) )
		self.assertEqual( network.getShader( bInput.shader ).parameters["c"], IECore.Color3fData( imath.Color3f( 0, 1, 0 ) ) )

	def testLoops( self ) :

		baseTexture = GafferSceneTest.TestShader( "baseTexture" )

		indexQuery = Gaffer.ContextQuery()
		indexQuery.addQuery( Gaffer.IntPlug(), "loop:index" )

		overlayTexture = GafferSceneTest.TestShader( "overlayTexture" )
		overlayTexture["parameters"]["i"].setInput( indexQuery["out"][0]["value"] )

		mix = GafferSceneTest.TestShader( "mix" )
		mix.loadShader( "mix" )
		mix["type"].setValue( "test:surface" )

		loop = Gaffer.Loop()
		loop.setup( mix["out"] )
		loop["in"].setInput( baseTexture["out"] )

		mix["parameters"]["a"].setInput( loop["previous"] )
		mix["parameters"]["b"].setInput( overlayTexture["out"] )

		loop["next"].setInput( mix["out"] )
		loop["iterations"].setValue( 3 )

		output = GafferSceneTest.TestShader( "output" )
		output["type"].setValue( "test:surface" )
		output["parameters"]["c"].setInput( loop["out"] )

		shaderPlug = GafferScene.ShaderPlug()
		shaderPlug.setInput( output["out"] )

		network = shaderPlug.attributes()["test:surface"]
		self.assertEqual( len( network.shaders() ), 8 )
		self.assertEqual( network.getOutput(), ( "output", "out" ) )

		input = network.input( ( "output", "c" ) )
		for i in range( 2, -1, -1 ) :

			self.assertEqual(
				input, IECoreScene.ShaderNetwork.Parameter( "mix{}".format( i if i else "" ), "out" )
			)

			overlay = network.input( ( input.shader, "b" ) )
			self.assertEqual(
				overlay, IECoreScene.ShaderNetwork.Parameter( "overlayTexture{}".format( i if i else "" ), "out" )
			)
			self.assertEqual( network.getShader( overlay.shader ).parameters["i"].value, i )

			input = network.input( ( input.shader, "a" ) )

		self.assertEqual( input, IECoreScene.ShaderNetwork.Parameter( "baseTexture", "out" ) )

	def testContextProcessorsWithoutContextSensitiveShaders( self ) :

		# Same shader seen in two custom contexts, but with the shader
		# not using the context variable.

		texture = GafferSceneTest.TestShader( "texture" )

		contextA = Gaffer.ContextVariables()
		contextA.setup( texture["out"] )
		contextA["variables"].addChild( Gaffer.NameValuePlug( "c", "A" ) )
		contextA["in"].setInput( texture["out"] )

		contextB = Gaffer.ContextVariables()
		contextB.setup( texture["out"] )
		contextB["variables"].addChild( Gaffer.NameValuePlug( "c", "B" ) )
		contextB["in"].setInput( texture["out"] )

		mix = GafferSceneTest.TestShader( "mix" )
		mix.loadShader( "mix" )
		mix["type"].setValue( "test:surface" )
		mix["parameters"]["a"].setInput( contextA["out"] )
		mix["parameters"]["b"].setInput( contextB["out"] )

		# The `texture` shader is the same in both contexts, so there should only
		# be a single instance of it in the result.

		network = mix.attributes()["test:surface"]
		self.assertEqual( len( network.shaders() ), 2 )
		self.assertEqual( network.getOutput(), ( "mix", "out" ) )
		self.assertEqual( network.input( ( "mix", "a" ) ), network.input( ( "mix", "a" ) ) )

		# The same should apply when the shader is seen in the default context
		# and a single custom context.

		contextA["enabled"].setValue( False )

		network = mix.attributes()["test:surface"]
		self.assertEqual( len( network.shaders() ), 2 )
		self.assertEqual( network.getOutput(), ( "mix", "out" ) )
		self.assertEqual( network.input( ( "mix", "a" ) ), network.input( ( "mix", "a" ) ) )

	def testSpline( self ) :

		n1 = GafferSceneTest.TestShader( "n1" )
		n1["type"].setValue( "test:surface" )

		network = n1.attributes()["test:surface"]

		self.assertEqual( network.shaders()["n1"].parameters["spline"], IECore.SplinefColor3fData() )

		n1["parameters"]["spline"].addPoint()
		n1["parameters"]["spline"].addPoint()
		n1["parameters"]["spline"].addPoint()
		n1["parameters"]["spline"]["p1"]["x"].setValue( 1 )
		n1["parameters"]["spline"]["p1"]["y"].setValue( imath.Color3f( 1 ) )
		n1["parameters"]["spline"]["p2"]["x"].setValue( 0.6 )
		n1["parameters"]["spline"]["p2"]["y"].setValue( imath.Color3f( 0.4, 0.5, 0.7 ) )


		network = n1.attributes()["test:surface"]

		refSpline = IECore.SplinefColor3f()
		refSpline[0] = imath.Color3f( 0 )
		refSpline[0] = imath.Color3f( 0 )
		refSpline[0.6] = imath.Color3f( 0.4, 0.5, 0.7 )
		refSpline[1] = imath.Color3f( 1 )
		refSpline[1] = imath.Color3f( 1 )

		self.assertEqual( network.shaders()["n1"].parameters["spline"].value, refSpline )

		inN1 = GafferSceneTest.TestShader( "inN1" )

		n1["parameters"]["spline"]["p0"]["y"].setInput( inN1["out"] )
		n1["parameters"]["spline"]["p1"]["y"]["b"].setInput( inN1["out"]["g"] )

		network = n1.attributes()["test:surface"]

		self.assertEqual( len( network ), 2 )
		self.assertEqual(
			network.inputConnections( "n1" ), [
				network.Connection( network.Parameter( "inN1", "out", ), network.Parameter( "n1", "spline[0].y" ) ),
				network.Connection( network.Parameter( "inN1", "out", ), network.Parameter( "n1", "spline[1].y" ) ),
				network.Connection( network.Parameter( "inN1", "out.g", ), network.Parameter( "n1", "spline[3].y.b" ) ),
				network.Connection( network.Parameter( "inN1", "out.g", ), network.Parameter( "n1", "spline[4].y.b" ) )
			]
		)

		n1["parameters"]["spline"]["p1"]["x"].setInput( inN1["out"]["g"] )

		with self.assertRaisesRegex( RuntimeError, "n1.__outAttributes : Shader connections to n1.parameters.spline.p1.x are not supported." ) :
			network = n1.attributes()["test:surface"]

		n1["parameters"]["spline"]["p1"]["x"].setInput( None )

		n1["parameters"]["spline"]["interpolation"].setValue( Gaffer.SplineDefinitionInterpolation.Linear )

		network = n1.attributes()["test:surface"]
		self.assertEqual(
			network.inputConnections( "n1" ), [
				network.Connection( network.Parameter( "inN1", "out", ), network.Parameter( "n1", "spline[0].y" ) ),
				network.Connection( network.Parameter( "inN1", "out.g", ), network.Parameter( "n1", "spline[2].y.b" ) )
			]
		)

		n1["parameters"]["spline"]["interpolation"].setValue( Gaffer.SplineDefinitionInterpolation.MonotoneCubic )

		with self.assertRaisesRegex( RuntimeError, "n1.__outAttributes : Cannot support monotone cubic interpolation for splines with inputs, for plug n1.parameters.spline" ):
			network = n1.attributes()["test:surface"]

	def testOptionalParameter( self ) :

		node = GafferSceneTest.TestShader( "n1" )
		node["type"].setValue( "test:surface" )

		shader = node.attributes()["test:surface"].outputShader()
		self.assertNotIn( "optionalString", shader.parameters )

		node["parameters"]["optionalString"]["enabled"].setValue( True )
		shader = node.attributes()["test:surface"].outputShader()
		self.assertIn( "optionalString", shader.parameters )
		self.assertEqual( shader.parameters["optionalString"], IECore.StringData() )

		node["parameters"]["optionalString"]["value"].setValue( "test" )
		shader = node.attributes()["test:surface"].outputShader()
		self.assertIn( "optionalString", shader.parameters )
		self.assertEqual( shader.parameters["optionalString"], IECore.StringData( "test" ) )

		node["parameters"]["optionalString"]["enabled"].setValue( False )
		shader = node.attributes()["test:surface"].outputShader()
		self.assertNotIn( "optionalString", shader.parameters )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testNetworkBuilderPerformance( self ) :

		script = Gaffer.ScriptNode()

		def build( output, depth ) :

			if depth > 10 :
				return

			shader = GafferSceneTest.TestShader()
			shader.loadShader( "mix" )
			shader["type"].setValue( "test:surface" )
			script.addChild( shader )

			if output is not None :
				output.setInput( shader["out"] )

			build( shader["parameters"]["a"], depth + 1 )
			build( shader["parameters"]["b"], depth + 1 )

		build( None, 0 )

		with GafferTest.TestRunner.PerformanceScope() :
			script["TestShader"].attributes( _copy = False )

if __name__ == "__main__":
	unittest.main()
