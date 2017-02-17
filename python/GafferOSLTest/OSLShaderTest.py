##########################################################################
#
#  Copyright (c) 2013, John Haddon. All rights reserved.
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

import Gaffer
import GafferTest
import GafferScene
import GafferOSL
import GafferOSLTest

class OSLShaderTest( GafferOSLTest.OSLTestCase ) :

	def test( self ) :

		s = self.compileShader( os.path.dirname( __file__ ) + "/shaders/types.osl" )

		n = GafferOSL.OSLShader()
		n.loadShader( s )

		self.assertEqual( n["name"].getValue(), s )
		self.assertEqual( n["type"].getValue(), "osl:surface" )

		self.assertEqual( n["parameters"].keys(), [ "i", "f", "c", "s", "m" ] )

		self.assertTrue( isinstance( n["parameters"]["i"], Gaffer.IntPlug ) )
		self.assertTrue( isinstance( n["parameters"]["f"], Gaffer.FloatPlug ) )
		self.assertTrue( isinstance( n["parameters"]["c"], Gaffer.Color3fPlug ) )
		self.assertTrue( isinstance( n["parameters"]["s"], Gaffer.StringPlug ) )
		self.assertTrue( isinstance( n["parameters"]["m"], Gaffer.M44fPlug ) )

		self.assertEqual( n["parameters"]["i"].defaultValue(), 10 )
		self.assertEqual( n["parameters"]["f"].defaultValue(), 1 )
		self.assertEqual( n["parameters"]["c"].defaultValue(), IECore.Color3f( 1, 2, 3 ) )
		self.assertEqual( n["parameters"]["s"].defaultValue(), "s" )
		self.assertEqual( n["parameters"]["m"].defaultValue(), IECore.M44f() )

		self.assertEqual( n["out"].typeId(), Gaffer.Plug.staticTypeId() )

		network = n.attributes()["osl:surface"]
		self.assertEqual( len( network ), 1 )
		self.assertEqual( network[0].name, s )
		self.assertEqual( network[0].type, "osl:surface" )
		self.assertEqual( network[0].parameters["i"], IECore.IntData( 10 ) )
		self.assertEqual( network[0].parameters["f"], IECore.FloatData( 1 ) )
		self.assertEqual( network[0].parameters["c"], IECore.Color3fData( IECore.Color3f( 1, 2, 3 ) ) )
		self.assertEqual( network[0].parameters["s"], IECore.StringData( "s" ) )
		self.assertEqual( network[0].parameters["m"], IECore.M44fData( IECore.M44f() ) )

	def testOutputTypes( self ) :

		s = self.compileShader( os.path.dirname( __file__ ) + "/shaders/outputTypes.osl" )

		n = GafferOSL.OSLShader()
		n.loadShader( s )

		self.assertEqual( n["name"].getValue(), s )
		self.assertEqual( n["type"].getValue(), "osl:shader" )

		self.assertEqual( len( n["parameters"] ), 1 )
		self.assertEqual( n["parameters"].keys(), [ "input" ] )

		self.assertEqual( n["out"].typeId(), Gaffer.Plug.staticTypeId() )
		self.assertEqual( n["out"].keys(), [ "i", "f", "c", "s", "m" ] )

		self.assertTrue( isinstance( n["out"]["i"], Gaffer.IntPlug ) )
		self.assertTrue( isinstance( n["out"]["f"], Gaffer.FloatPlug ) )
		self.assertTrue( isinstance( n["out"]["c"], Gaffer.Color3fPlug ) )
		self.assertTrue( isinstance( n["out"]["s"], Gaffer.StringPlug ) )
		self.assertTrue( isinstance( n["out"]["m"], Gaffer.M44fPlug ) )

	def testNetwork( self ) :

		typesShader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/types.osl" )
		outputTypesShader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/outputTypes.osl" )

		typesNode = GafferOSL.OSLShader()
		outputTypesNode = GafferOSL.OSLShader()

		typesNode.loadShader( typesShader )
		outputTypesNode.loadShader( outputTypesShader )

		typesNode["parameters"]["i"].setInput( outputTypesNode["out"]["i"] )

		self.assertEqual( typesNode["parameters"]["i"].getValue(), 10 )

		network = typesNode.attributes()["osl:surface"]

		self.assertEqual( len( network ), 2 )

		self.assertEqual( network[1].name, typesShader )
		self.assertEqual( network[1].type, "osl:surface" )
		self.assertEqual( network[1].parameters["i"], IECore.StringData( "link:" + network[0].parameters["__handle"].value + ".i" ) )
		self.assertEqual( network[1].parameters["f"], IECore.FloatData( 1 ) )
		self.assertEqual( network[1].parameters["c"], IECore.Color3fData( IECore.Color3f( 1, 2, 3 ) ) )
		self.assertEqual( network[1].parameters["s"], IECore.StringData( "s" ) )
		self.assertEqual( network[0].name, outputTypesShader )
		self.assertEqual( network[0].type, "osl:shader" )
		self.assertEqual( network[0].parameters["input"], IECore.FloatData( 1 ) )

	def testSerialiation( self ) :

		s = self.compileShader( os.path.dirname( __file__ ) + "/shaders/outputTypes.osl" )

		script = Gaffer.ScriptNode()
		script["n"] = GafferOSL.OSLShader()
		script["n"].loadShader( s )

		script2 = Gaffer.ScriptNode()
		script2.execute( script.serialise() )

		self.assertEqual( script["n"]["name"].getValue(), script2["n"]["name"].getValue() )
		self.assertEqual( script["n"]["type"].getValue(), script2["n"]["type"].getValue() )

		self.assertEqual( script["n"]["parameters"].keys(), script2["n"]["parameters"].keys() )
		self.assertEqual( script["n"]["out"].keys(), script2["n"]["out"].keys() )

	def testLoadNonexistentShader( self ) :

		n = GafferOSL.OSLShader()
		self.assertRaises( RuntimeError, n.loadShader,  "nonexistent" )

	def testSearchPaths( self ) :

		s = self.compileShader( os.path.dirname( __file__ ) + "/shaders/types.osl" )

		os.environ["OSL_SHADER_PATHS"] = os.path.dirname( s )
		n = GafferOSL.OSLShader()
		n.loadShader( os.path.basename( s ) )

		self.assertEqual( n["parameters"].keys(), [ "i", "f", "c", "s", "m" ] )

	def testNoConnectionToParametersPlug( self ) :

		splitPoint = GafferOSL.OSLShader()
		splitPoint.loadShader( "Utility/SplitPoint" )

		globals = GafferOSL.OSLShader()
		globals.loadShader( "Utility/Globals" )

		splitPoint["parameters"]["p"].setInput( globals["out"]["globalP"] )

		self.assertTrue( splitPoint["parameters"]["p"].getInput().isSame( globals["out"]["globalP"] ) )
		self.assertTrue( splitPoint["parameters"]["p"][0].getInput().isSame( globals["out"]["globalP"][0] ) )
		self.assertTrue( splitPoint["parameters"]["p"][1].getInput().isSame( globals["out"]["globalP"][1] ) )
		self.assertTrue( splitPoint["parameters"]["p"][2].getInput().isSame( globals["out"]["globalP"][2] ) )
		self.assertTrue( splitPoint["parameters"].getInput() is None )

	def testStructs( self ) :

		s = self.compileShader( os.path.dirname( __file__ ) + "/shaders/structs.osl" )
		n = GafferOSL.OSLShader()
		n.loadShader( s )

		self.assertEqual( n["parameters"].keys(), [ "i", "f", "s", "ss" ] )
		self.assertEqual( n["parameters"]["i"].defaultValue(), 2 )
		self.assertEqual( n["parameters"]["f"].defaultValue(), 3 )
		self.assertEqual( n["parameters"]["ss"].defaultValue(), "ss" )

		self.assertEqual( n["parameters"]["s"].keys(), [ "i", "f", "c", "s" ] )
		self.assertEqual( n["parameters"]["s"]["i"].defaultValue(), 1 )
		self.assertEqual( n["parameters"]["s"]["f"].defaultValue(), 2 )
		self.assertEqual( n["parameters"]["s"]["c"].defaultValue(), IECore.Color3f( 1, 2, 3 ) )
		self.assertEqual( n["parameters"]["s"]["s"].defaultValue(), "s" )

		n["parameters"]["s"]["i"].setValue( 10 )
		n["parameters"]["s"]["f"].setValue( 21 )
		n["parameters"]["s"]["c"].setValue( IECore.Color3f( 3, 4, 5 ) )
		n["parameters"]["s"]["s"].setValue( "ttt" )

		network = n.attributes()["osl:shader"]
		self.assertEqual( len( network[0].parameters ), 7 )
		self.assertTrue( network[0].parameters["i"], IECore.IntData( 2 ) )
		self.assertTrue( network[0].parameters["f"], IECore.FloatData( 3 ) )
		self.assertTrue( network[0].parameters["s.i"], IECore.IntData( 10 ) )
		self.assertTrue( network[0].parameters["s.f"], IECore.FloatData( 21 ) )
		self.assertTrue( network[0].parameters["s.c"], IECore.Color3fData( IECore.Color3f( 3, 4, 5 ) ) )
		self.assertTrue( network[0].parameters["s.s"], IECore.StringData( "ttt" ) )
		self.assertTrue( network[0].parameters["ss"], IECore.StringData( "ss" ) )

		h1 = n.attributesHash()

		n["parameters"]["s"]["i"].setValue( 100 )
		h2 = n.attributesHash()
		self.assertNotEqual( h1, h2 )

		s2 = self.compileShader( os.path.dirname( __file__ ) + "/shaders/outputTypes.osl" )
		g = GafferOSL.OSLShader()
		g.loadShader( s2 )

		n["parameters"]["s"]["i"].setInput( g["out"]["i"] )
		h3 = n.attributesHash()
		self.assertNotEqual( h1, h3 )
		self.assertNotEqual( h2, h3 )

	def testOutputPlugAffectsHash( self ) :

		globals = GafferOSL.OSLShader()
		globals.loadShader( "Utility/Globals" )

		buildColor = GafferOSL.OSLShader()
		buildColor.loadShader( "Utility/BuildColor" )

		buildColor["parameters"]["r"].setInput( globals["out"]["globalU"] )
		h1 = buildColor.attributesHash()

		buildColor["parameters"]["r"].setInput( globals["out"]["globalV"] )
		h2 = buildColor.attributesHash()

		self.assertNotEqual( h1, h2 )

	def testCantConnectVectorToColor( self ) :

		globals = GafferOSL.OSLShader()
		globals.loadShader( "Utility/Globals" )

		constant = GafferOSL.OSLShader()
		constant.loadShader( "Surface/Constant" )

		self.assertFalse( constant["parameters"]["Cs"].acceptsInput( globals["out"]["globalP"] ) )

	def testClosureParameters( self ) :

		outputClosureShader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/outputClosure.osl" )
		outputClosure = GafferOSL.OSLShader()
		outputClosure.loadShader( outputClosureShader )

		inputClosureShader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/inputClosure.osl" )
		inputClosure = GafferOSL.OSLShader()
		inputClosure.loadShader( inputClosureShader )

		self.assertEqual( outputClosure["out"]["c"].typeId(), Gaffer.Plug.staticTypeId() )
		self.assertEqual( inputClosure["parameters"]["i"].typeId(), Gaffer.Plug.staticTypeId() )

		inputClosure["parameters"]["i"].setInput( outputClosure["out"]["c"] )

		s = inputClosure.attributes()["osl:surface"]
		self.assertEqual( len( s ), 2 )
		self.assertEqual( s[1].parameters["i"].value, "link:" + s[0].parameters["__handle"].value + ".c" )

	def testClosureParametersInputAcceptance( self ) :

		outputClosureShader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/outputClosure.osl" )
		outputClosure = GafferOSL.OSLShader()
		outputClosure.loadShader( outputClosureShader )

		inputClosureShader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/inputClosure.osl" )
		inputClosure = GafferOSL.OSLShader()
		inputClosure.loadShader( inputClosureShader )

		outputColor = GafferOSL.OSLShader()
		outputColor.loadShader( "Utility/VectorToColor" )

		self.assertTrue( inputClosure["parameters"]["i"].acceptsInput( outputClosure["out"]["c"] ) )
		self.assertFalse( inputClosure["parameters"]["i"].acceptsInput( outputColor["out"]["c"] ) )

	def testOutputClosureDirtying( self ) :

		outputClosureShader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/outputClosure.osl" )
		outputClosure = GafferOSL.OSLShader()
		outputClosure.loadShader( outputClosureShader )

		cs = GafferTest.CapturingSlot( outputClosure.plugDirtiedSignal() )

		outputClosure["parameters"]["e"]["r"].setValue( 10 )

		self.assertEqual(
			set( [ x[0].relativeName( x[0].node() ) for x in cs ] ),
			set( [
				"parameters.e.r",
				"parameters.e",
				"parameters",
				"out.c",
				"out",
			] )
		)

	def testRepeatability( self ) :

		s1 = self.compileShader( os.path.dirname( __file__ ) + "/shaders/outputTypes.osl" )
		s2 = self.compileShader( os.path.dirname( __file__ ) + "/shaders/types.osl" )

		sn1 = GafferOSL.OSLShader()
		sn1.loadShader( s1 )

		sn2 = GafferOSL.OSLShader()
		sn2.loadShader( s2 )

		sn2["parameters"]["i"].setInput( sn1["out"]["i"] )

		self.assertEqual( sn2.attributesHash(), sn2.attributesHash() )
		self.assertEqual( sn2.attributes(), sn2.attributes() )

	def testHandlesAreHumanReadable( self ) :

		s1 = self.compileShader( os.path.dirname( __file__ ) + "/shaders/outputTypes.osl" )
		s2 = self.compileShader( os.path.dirname( __file__ ) + "/shaders/types.osl" )

		sn1 = GafferOSL.OSLShader( "Shader1" )
		sn1.loadShader( s1 )

		sn2 = GafferOSL.OSLShader( "Shader2" )
		sn2.loadShader( s2 )

		sn2["parameters"]["i"].setInput( sn1["out"]["i"] )

		network = sn2.attributes()["osl:surface"]
		self.assertTrue( "Shader1" in network[0].parameters["__handle"].value )

	def testHandlesAreUniqueEvenIfNodeNamesArent( self ) :

		s1 = self.compileShader( os.path.dirname( __file__ ) + "/shaders/outputTypes.osl" )
		s2 = self.compileShader( os.path.dirname( __file__ ) + "/shaders/types.osl" )

		script = Gaffer.ScriptNode()

		script["in1"] = GafferOSL.OSLShader()
		script["in1"].loadShader( s1 )

		script["in2"] = GafferOSL.OSLShader()
		script["in2"].loadShader( s1 )

		script["shader"] = GafferOSL.OSLShader()
		script["shader"].loadShader( s2 )

		script["shader"]["parameters"]["i"].setInput( script["in1"]["out"]["i"] )
		script["shader"]["parameters"]["f"].setInput( script["in2"]["out"]["f"] )

		box = Gaffer.Box.create( script, Gaffer.StandardSet( [ script["in1"] ] ) )

		# because the nodes have different parents, we can give them the same name.
		box["in1"].setName( "notUnique" )
		script["in2"].setName( "notUnique" )

		network = script["shader"].attributes()["osl:surface"]
		self.assertNotEqual( network[0].parameters["__handle"], network[1].parameters["__handle"] )

	def testShaderMetadata( self ) :

		s = self.compileShader( os.path.dirname( __file__ ) + "/shaders/metadata.osl" )
		n = GafferOSL.OSLShader()
		n.loadShader( s )

		self.assertEqual( n.shaderMetadata( "stringValue" ), "s" )
		self.assertEqual( n.shaderMetadata( "intValue" ), 1 )
		self.assertEqual( n.shaderMetadata( "floatValue" ), 0.5 )

	def testParameterMetadata( self ) :

		s = self.compileShader( os.path.dirname( __file__ ) + "/shaders/metadata.osl" )
		n = GafferOSL.OSLShader()
		n.loadShader( s )

		self.assertEqual( n.parameterMetadata( n["parameters"]["a"], "aStringValue" ), "s" )
		self.assertEqual( n.parameterMetadata( n["parameters"]["a"], "aIntValue" ), 1 )
		self.assertEqual( n.parameterMetadata( n["parameters"]["a"], "aFloatValue" ), 0.5 )

		self.assertEqual( n.parameterMetadata( n["parameters"]["b"], "bStringValue" ), "st" )
		self.assertEqual( n.parameterMetadata( n["parameters"]["b"], "bIntValue" ), 2 )
		self.assertEqual( n.parameterMetadata( n["parameters"]["b"], "bFloatValue" ), 0.75 )

	def testParameterArrayMetadata( self ) :

		s = self.compileShader( os.path.dirname( __file__ ) + "/shaders/arrayMetadata.osl" )
		n = GafferOSL.OSLShader()
		n.loadShader( s )

		self.assertEqual( n.parameterMetadata( n["parameters"]["a"], "aStringValues" ), IECore.StringVectorData( [ "one","two" ] ) )
		self.assertEqual( n.parameterMetadata( n["parameters"]["a"], "aIntValues" ), IECore.IntVectorData( [ 1, 2 ] ) )
		self.assertEqual( n.parameterMetadata( n["parameters"]["a"], "aFloatValues" ), IECore.FloatVectorData( [ 0.25, 0.5 ] ) )

	def testParameterMinMaxMetadata( self ) :

		s = self.compileShader( os.path.dirname( __file__ ) + "/shaders/metadataMinMax.osl" )
		n = GafferOSL.OSLShader()
		n.loadShader( s )

		self.assertAlmostEqual( n["parameters"]["b"].minValue(), 2.3, delta = 0.00001 )
		self.assertAlmostEqual( n["parameters"]["b"].maxValue(), 4.7, delta = 0.00001 )
		self.assertEqual( n["parameters"]["c"].minValue(), 23 )
		self.assertEqual( n["parameters"]["c"].maxValue(), 47 )
		self.assertEqual( n["parameters"]["d"].minValue(), IECore.Color3f( 1, 2, 3 ) )
		self.assertEqual( n["parameters"]["d"].maxValue(), IECore.Color3f( 4, 5, 6 ) )
		self.assertEqual( n["parameters"]["e"].minValue(), IECore.V3f( 1, 2, 3 ) )
		self.assertEqual( n["parameters"]["e"].maxValue(), IECore.V3f( 4, 5, 6 ) )
		self.assertEqual( n["parameters"]["f"].minValue(), IECore.V3f( 1, 2, 3 ) )
		self.assertEqual( n["parameters"]["f"].maxValue(), IECore.V3f( 4, 5, 6 ) )
		self.assertEqual( n["parameters"]["g"].minValue(), IECore.V3f( 1, 2, 3 ) )
		self.assertEqual( n["parameters"]["g"].maxValue(), IECore.V3f( 4, 5, 6 ) )

		# Check default min/max if not specified
		self.assertFalse( n["parameters"]["h"].hasMinValue() )
		self.assertFalse( n["parameters"]["h"].hasMaxValue() )

	def testParameterSplineMetadata( self ) :

		s = self.compileShader( os.path.dirname( __file__ ) + "/shaders/splineMetadata.osl" )
		n = GafferOSL.OSLShader()
		n.loadShader( s )

		# If the components of the spline all match, the metadata is registered to the spline plug
		self.assertEqual( n.parameterMetadata( n["parameters"]["correctSpline"], "a" ), 1 )
		self.assertEqual( n.parameterMetadata( n["parameters"]["correctSpline"], "b" ), 2 )
		self.assertEqual( n.parameterMetadata( n["parameters"]["correctSpline"], "c" ), 3 )

		# If the components don't match, the metadata is registered to the individual plugs
		# Note that array plugs are not supported, so we can't test Values and Positions
		self.assertEqual( n.parameterMetadata( n["parameters"]["incompleteSplineBasis"], "c" ), 3 )


	def testMetadataReuse( self ) :

		s = self.compileShader( os.path.dirname( __file__ ) + "/shaders/arrayMetadata.osl" )

		n1 = GafferOSL.OSLShader()
		n1.loadShader( s )

		n2 = GafferOSL.OSLShader()
		n2.loadShader( s )

		# we don't want every shader to have its own copy of metadata when it could be shared
		self.assertTrue(
			n1.parameterMetadata( n1["parameters"]["a"], "aStringValues", _copy = False ).isSame(
				n2.parameterMetadata( n2["parameters"]["a"], "aStringValues", _copy = False )
			)
		)

		# but because there is no const in python, we want to make sure that the casual
		# caller doesn't have the opportunity to really break things, so unless requested
		# copies are returned from the query.
		n1.parameterMetadata( n1["parameters"]["a"], "aStringValues" ).value = "editingSharedConstDataIsABadIdea"
		self.assertEqual( n1.parameterMetadata( n1["parameters"]["a"], "aStringValues" ), IECore.StringVectorData( [ "one", "two" ] ) )

	def testAcceptsNoneInput( self ) :

		s = self.compileShader( os.path.dirname( __file__ ) + "/shaders/types.osl" )
		n = GafferOSL.OSLShader()
		n.loadShader( s )

		self.assertTrue( n["parameters"]["i"].acceptsInput( None ) )

	def testOverzealousCycleDetection( self ) :

		globals = GafferOSL.OSLShader( "Globals" )
		globals.loadShader( "Utility/Globals" )

		point = GafferOSL.OSLShader( "Point" )
		point.loadShader( "Utility/BuildPoint" )

		noise = GafferOSL.OSLShader( "Noise" )
		noise.loadShader( "Pattern/Noise" )

		color = GafferOSL.OSLShader( "Color" )
		color.loadShader( "Utility/BuildColor" )

		point["parameters"]["x"].setInput( globals["out"]["globalU"] )
		point["parameters"]["y"].setInput( globals["out"]["globalV"] )

		noise["parameters"]["p"].setInput( point["out"]["p"] )

		color["parameters"]["r"].setInput( globals["out"]["globalU"] )
		color["parameters"]["g"].setInput( noise["out"]["n"] )

		# Should not throw - there are no cycles above.
		color.attributesHash()
		color.attributes()

	def testLoadNetworkFromVersion0_23( self ) :

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( os.path.dirname( __file__ ) + "/scripts/networkVersion-0.23.2.1.gfr" )
		s.load()

		for plug, expectedValue, expectedInput in [
			( "InFloat.parameters.name", "s", None ),
			( "InFloat.parameters.defaultValue", 1, None ),
			( "InFloat1.parameters.name", "t", None ),
			( "InFloat1.parameters.defaultValue", 0.5, None ),
			( "InFloat2.parameters.name", "u", None ),
			( "InFloat2.parameters.defaultValue", 0.25, None ),
			( "OutPoint.parameters.name", "stu", None ),
			( "BuildPoint.parameters.x", None, "InFloat.out.value" ),
			( "BuildPoint.parameters.y", None, "InFloat1.out.value" ),
			( "BuildPoint.parameters.z", None, "InFloat2.out.value" ),
			( "OutPoint.parameters.value", None, "BuildPoint.out.p" ),
			( "OutObject.parameters.in0", None, "OutPoint.out.primitiveVariable" ),
		] :

			if expectedInput is not None :
				self.assertTrue( s.descendant( plug ).getInput().isSame( s.descendant( expectedInput ) ) )
			else :
				self.assertTrue( s.descendant( plug ).getInput() is None )

			if expectedValue is not None :
				self.assertEqual( s.descendant( plug ).getValue(), expectedValue )

	def testReload( self ) :

		s1 = self.compileShader( os.path.dirname( __file__ ) + "/shaders/version1.osl" )
		s2 = self.compileShader( os.path.dirname( __file__ ) + "/shaders/version2.osl" )

		n = GafferOSL.OSLShader()
		n.loadShader( s1 )

		self.assertEqual(
			n["parameters"].keys(),
			[
				"commonI",
				"commonF",
				"commonColor",
				"commonString",
				"commonStruct",
				"commonArray",
				"removedI",
				"removedF",
				"removedColor",
				"removedString",
				"removedStruct",
				"typeChanged1",
				"typeChanged2",
				"typeChanged3",
				"typeChanged4",
				"typeChanged5",
				"defaultChangedArray",
			]
		)

		self.assertEqual(
			n["parameters"]["commonStruct"].keys(),
			[
				"commonI",
				"commonF",
				"commonColor",
				"commonString",
				"removedI",
				"removedF",
				"removedColor",
				"removedString",
				"typeChanged1",
				"typeChanged2",
				"typeChanged3",
				"typeChanged4",
			]
		)

		values = {
			"commonI" : 10,
			"commonF" : 25,
			"commonColor" : IECore.Color3f( 1 ),
			"commonString" : "test",
			"commonStruct.commonI" : 11,
			"commonStruct.commonF" : 2.5,
			"commonStruct.commonColor" : IECore.Color3f( 0.5 ),
			"commonStruct.commonString" : "test2",
			"commonArray" : IECore.FloatVectorData( [ 0, 1, 2 ] )
		}

		for key, value in values.items() :
			n["parameters"].descendant( key ).setValue( value )

		arrayToNotGetReloaded = n["parameters"]["commonArray"]
		arrayToGetReloaded = n["parameters"]["defaultChangedArray"]

		self.assertTrue( isinstance( n["parameters"]["typeChanged1"], Gaffer.IntPlug ) )
		self.assertTrue( isinstance( n["parameters"]["typeChanged2"], Gaffer.FloatPlug ) )
		self.assertTrue( isinstance( n["parameters"]["typeChanged3"], Gaffer.Color3fPlug ) )
		self.assertTrue( isinstance( n["parameters"]["typeChanged4"], Gaffer.StringPlug ) )
		self.assertTrue( isinstance( n["parameters"]["typeChanged5"], Gaffer.V3fPlug ) )
		self.assertTrue( n["parameters"]["typeChanged5"].interpretation(), IECore.GeometricData.Interpretation.Vector)

		n.loadShader( s2, keepExistingValues = True )

		self.assertEqual(
			n["parameters"].keys(),
			[
				"commonI",
				"commonF",
				"commonColor",
				"commonString",
				"commonStruct",
				"commonArray",
				"typeChanged1",
				"typeChanged2",
				"typeChanged3",
				"typeChanged4",
				"typeChanged5",
				"addedI",
				"addedF",
				"addedColor",
				"addedString",
				"addedStruct",
				"defaultChangedArray",
			]
		)

		self.assertEqual(
			n["parameters"]["commonStruct"].keys(),
			[
				"commonI",
				"commonF",
				"commonColor",
				"commonString",
				"typeChanged1",
				"typeChanged2",
				"typeChanged3",
				"typeChanged4",
				"addedI",
				"addedF",
				"addedColor",
				"addedString",
			]
		)

		self.assertEqual( arrayToNotGetReloaded, n["parameters"]["commonArray"] )
		self.assertNotEqual( arrayToGetReloaded, n["parameters"]["defaultChangedArray"] )

		for key, value in values.items() :
			self.assertEqual( n["parameters"].descendant( key ).getValue(), value )

		self.assertTrue( isinstance( n["parameters"]["typeChanged1"], Gaffer.StringPlug ) )
		self.assertTrue( isinstance( n["parameters"]["typeChanged2"], Gaffer.Color3fPlug ) )
		self.assertTrue( isinstance( n["parameters"]["typeChanged3"], Gaffer.FloatPlug ) )
		self.assertTrue( isinstance( n["parameters"]["typeChanged4"], Gaffer.IntPlug ) )
		self.assertTrue( isinstance( n["parameters"]["typeChanged5"], Gaffer.V3fPlug ) )
		self.assertEqual( n["parameters"]["typeChanged5"].interpretation(), IECore.GeometricData.Interpretation.Normal)

		n.loadShader( s2, keepExistingValues = False )
		for plug in n["parameters"] :
			if isinstance( plug, Gaffer.ValuePlug ) :
				self.assertTrue( plug.isSetToDefault() )

	def testSplineParameters( self ) :

		s = self.compileShader( os.path.dirname( __file__ ) + "/shaders/splineParameters.osl" )
		n = GafferOSL.OSLShader()
		n.loadShader( s )

		self.assertEqual( n["parameters"].keys(), [ "floatSpline", "colorSpline" ] )

		self.assertTrue( isinstance( n["parameters"]["floatSpline"], Gaffer.SplineffPlug ) )
		self.assertEqual(
			n["parameters"]["floatSpline"].getValue(),
			IECore.Splineff(
				IECore.CubicBasisf.catmullRom(),
				[
					( 0, 0 ),
					( 0, 0 ),
					( 1, 1 ),
					( 1, 1 ),
				]
			)
		)

		self.assertTrue( isinstance( n["parameters"]["colorSpline"], Gaffer.SplinefColor3fPlug ) )
		self.assertEqual(
			n["parameters"]["colorSpline"].getValue(),
			IECore.SplinefColor3f(
				IECore.CubicBasisf.bSpline(),
				[
					( 0, IECore.Color3f( 0 ) ),
					( 0, IECore.Color3f( 0 ) ),
					( 1, IECore.Color3f( 1 ) ),
					( 1, IECore.Color3f( 1 ) ),
				]
			)
		)

		shader = n.attributes()["osl:surface"][0]

		self.assertEqual(
			shader.parameters["floatSpline"].value,
			IECore.Splineff(
				IECore.CubicBasisf.catmullRom(),
				[
					( 0, 0 ),
					( 0, 0 ),
					( 1, 1 ),
					( 1, 1 ),
				]
			)
		)

		self.assertEqual(
			shader.parameters["colorSpline"].value,
			IECore.SplinefColor3f(
				IECore.CubicBasisf.bSpline(),
				[
					( 0, IECore.Color3f( 0 ) ),
					( 0, IECore.Color3f( 0 ) ),
					( 1, IECore.Color3f( 1 ) ),
					( 1, IECore.Color3f( 1 ) ),
				]
			)
		)

	def testArrays( self ) :

		s = self.compileShader( os.path.dirname( __file__ ) + "/shaders/arrays.osl" )

		n = GafferOSL.OSLShader()
		n.loadShader( s )

		self.assertEqual( n["parameters"].keys(), [ "i", "f", "c", "p", "q", "s", "m" ] )

		self.assertTrue( isinstance( n["parameters"]["i"], Gaffer.IntVectorDataPlug ) )
		self.assertTrue( isinstance( n["parameters"]["f"], Gaffer.FloatVectorDataPlug ) )
		self.assertTrue( isinstance( n["parameters"]["c"], Gaffer.Color3fVectorDataPlug ) )
		self.assertTrue( isinstance( n["parameters"]["p"], Gaffer.V3fVectorDataPlug ) )
		self.assertTrue( isinstance( n["parameters"]["q"], Gaffer.V3fVectorDataPlug ) )
		self.assertTrue( isinstance( n["parameters"]["s"], Gaffer.StringVectorDataPlug ) )
		self.assertTrue( isinstance( n["parameters"]["m"], Gaffer.M44fVectorDataPlug ) )

		self.assertEqual( n["parameters"]["i"].defaultValue(), IECore.IntVectorData( [ 10, 11, 12 ] ) )
		self.assertEqual( n["parameters"]["f"].defaultValue(), IECore.FloatVectorData( [ 1, 2 ] ) )
		self.assertEqual( n["parameters"]["c"].defaultValue(), IECore.Color3fVectorData(
			[ IECore.Color3f( 1, 2, 3 ), IECore.Color3f( 4, 5, 6 ) ] ) )
		self.assertEqual( n["parameters"]["p"].defaultValue(), IECore.V3fVectorData(
			[ IECore.V3f( 1, 2, 3 ), IECore.V3f( 4, 5, 6 ) ] ) )
		self.assertEqual( n["parameters"]["q"].defaultValue(), IECore.V3fVectorData(
			[ IECore.V3f( 1, 2, 3 ), IECore.V3f( 4, 5, 6 ) ] ) )
		self.assertEqual( n["parameters"]["s"].defaultValue(), IECore.StringVectorData( [ "s", "t", "u", "v", "word" ] ) )
		self.assertEqual( n["parameters"]["m"].defaultValue(), IECore.M44fVectorData(
			[ IECore.M44f() * 1, IECore.M44f() * 0, IECore.M44f() * 1 ] ) )

		self.assertEqual( n["out"].typeId(), Gaffer.Plug.staticTypeId() )

		network = n.attributes()["osl:surface"]
		self.assertEqual( len( network ), 1 )
		self.assertEqual( network[0].name, s )
		self.assertEqual( network[0].type, "osl:surface" )
		self.assertEqual( network[0].parameters["i"], IECore.IntVectorData( [ 10, 11, 12 ] ) )
		self.assertEqual( network[0].parameters["f"], IECore.FloatVectorData( [ 1, 2 ] ) )
		self.assertEqual( network[0].parameters["c"], IECore.Color3fVectorData(
			[ IECore.Color3f( 1, 2, 3 ), IECore.Color3f( 4, 5, 6 ) ] ) )
		self.assertEqual( network[0].parameters["p"], IECore.V3fVectorData(
			[ IECore.V3f( 1, 2, 3 ), IECore.V3f( 4, 5, 6 ) ] ) )
		self.assertEqual( network[0].parameters["q"], IECore.V3fVectorData(
			[ IECore.V3f( 1, 2, 3 ), IECore.V3f( 4, 5, 6 ) ] ) )
		self.assertEqual( network[0].parameters["s"], IECore.StringVectorData( [ "s", "t", "u", "v", "word" ] ) )
		self.assertEqual( network[0].parameters["m"], IECore.M44fVectorData(
			[ IECore.M44f() * 1, IECore.M44f() * 0, IECore.M44f() * 1 ] ) )

	def testUnload( self ) :

		n = GafferOSL.OSLShader()
		n.loadShader( self.compileShader( os.path.dirname( __file__ ) + "/shaders/types.osl" ) )
		self.assertTrue( "osl:surface" in n.attributes() )

		n.loadShader( "" )
		self.assertEqual( len( n["parameters"] ), 0 )
		self.assertEqual( n["type"].getValue(), "" )
		self.assertEqual( n["name"].getValue(), "" )
		self.assertFalse( "osl:surface" in n.attributes() )

	def testLoadSurfaceAfterShader( self ) :

		n = GafferOSL.OSLShader()
		n.loadShader( self.compileShader( os.path.dirname( __file__ ) + "/shaders/outputTypes.osl" ) )
		self.assertEqual( len( n["out"] ), 5 )

		n.loadShader( self.compileShader( os.path.dirname( __file__ ) + "/shaders/constant.osl" ) )
		self.assertEqual( len( n["out"] ), 0 )

	def testReconnectionOfChildPlugShader( self ) :

		s = Gaffer.ScriptNode()

		s["n1"] = GafferOSL.OSLShader()
		s["n1"].loadShader( "Maths/VectorAdd" )

		s["n2"] = GafferOSL.OSLShader()
		s["n2"].loadShader( "Maths/VectorAdd" )

		s["n3"] = GafferOSL.OSLShader()
		s["n3"].loadShader( "Maths/VectorAdd" )

		s["n2"]["parameters"]["a"].setInput( s["n1"]["out"]["out"] )
		s["n3"]["parameters"]["a"].setInput( s["n2"]["out"]["out"] )

		s.deleteNodes( filter = Gaffer.StandardSet( [ s["n2"] ] ) )
		self.assertTrue( s["n3"]["parameters"]["a"].getInput().isSame( s["n1"]["out"]["out"] ) )

	def testDisablingShader( self ) :

		n1 = GafferOSL.OSLShader()
		n1.loadShader( "Maths/VectorAdd" )
		n1["parameters"]["a"].setValue( IECore.V3f( 5, 7, 6 ) )

		n2 = GafferOSL.OSLShader()
		n2.loadShader( "Maths/VectorAdd" )

		n3 = GafferOSL.OSLShader()
		n3.loadShader( "Maths/VectorAdd" )

		n2["parameters"]["a"].setInput( n1["out"]["out"] )
		n3["parameters"]["a"].setInput( n2["out"]["out"] )

		n2["enabled"].setValue( False )
		network = n3.attributes()["osl:shader"]
		self.assertEqual( len( network ), 2 )
		self.assertEqual( network[1].parameters["a"].value, "link:" + network[0].parameters["__handle"].value + ".out" )
		self.assertEqual( network[0].parameters["a"].value, IECore.V3f( 5, 7, 6 ) )

	def testDisabledShaderPassesThroughExternalValue( self ) :

		n1 = Gaffer.Node()
		n1["user"]["v"] = Gaffer.V3fPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		n1["user"]["v"].setValue( IECore.V3f( 12, 11, 10 ) )

		n2 = GafferOSL.OSLShader()
		n2.loadShader( "Maths/VectorAdd" )
		n2["parameters"]["a"].setInput( n1["user"]["v"] )

		n3 = GafferOSL.OSLShader()
		n3.loadShader( "Maths/VectorAdd" )
		n3["parameters"]["a"].setInput( n2["parameters"]["a"] )

		n2["enabled"].setValue( False )

		network = n3.attributes()["osl:shader"]
		self.assertEqual( len( network ), 1 )
		self.assertEqual( network[0].parameters["a"].value, IECore.V3f( 12, 11, 10 ) )

if __name__ == "__main__":
	unittest.main()
