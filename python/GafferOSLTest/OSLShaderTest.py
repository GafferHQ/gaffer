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
import imath
import random
import shutil

import IECore
import IECoreScene

import Gaffer
import GafferTest
import GafferScene
import GafferOSL
import GafferOSLTest
import GafferImage

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
		self.assertEqual( n["parameters"]["c"].defaultValue(), imath.Color3f( 1, 2, 3 ) )
		self.assertEqual( n["parameters"]["s"].defaultValue(), "s" )
		self.assertEqual( n["parameters"]["m"].defaultValue(), imath.M44f() )

		self.assertEqual( n["out"].typeId(), Gaffer.Plug.staticTypeId() )

		network = n.attributes()["osl:surface"]
		self.assertEqual( len( network ), 1 )
		self.assertEqual( network.outputShader().name, s )
		self.assertEqual( network.outputShader().type, "osl:surface" )
		self.assertEqual( network.outputShader().parameters["i"], IECore.IntData( 10 ) )
		self.assertEqual( network.outputShader().parameters["f"], IECore.FloatData( 1 ) )
		self.assertEqual( network.outputShader().parameters["c"], IECore.Color3fData( imath.Color3f( 1, 2, 3 ) ) )
		self.assertEqual( network.outputShader().parameters["s"], IECore.StringData( "s" ) )
		self.assertEqual( network.outputShader().parameters["m"], IECore.M44fData( imath.M44f() ) )

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

		typesNode = GafferOSL.OSLShader( "types" )
		outputTypesNode = GafferOSL.OSLShader( "outputTypes" )

		typesNode.loadShader( typesShader )
		outputTypesNode.loadShader( outputTypesShader )

		typesNode["parameters"]["i"].setInput( outputTypesNode["out"]["i"] )

		self.assertEqual( typesNode["parameters"]["i"].getValue(), 10 )

		network = typesNode.attributes()["osl:surface"]
		self.assertEqual( len( network ), 2 )
		self.assertEqual( network.getOutput(), ( "types", "" ) )

		types = network.getShader( "types" )
		outputTypes = network.getShader( "outputTypes" )

		self.assertEqual( types.name, typesShader )
		self.assertEqual( types.type, "osl:surface" )
		self.assertEqual( types.parameters["f"], IECore.FloatData( 1 ) )
		self.assertEqual( types.parameters["c"], IECore.Color3fData( imath.Color3f( 1, 2, 3 ) ) )
		self.assertEqual( types.parameters["s"], IECore.StringData( "s" ) )
		self.assertEqual( outputTypes.name, outputTypesShader )
		self.assertEqual( outputTypes.type, "osl:shader" )
		self.assertEqual( outputTypes.parameters["input"], IECore.FloatData( 1 ) )

		self.assertEqual(
			network.inputConnections( "types" ),
			[ ( ( "outputTypes", "i" ), ( "types", "i" ) ) ]
		)

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

		standardShaderPaths = os.environ["OSL_SHADER_PATHS"]
		try:
			s = self.compileShader( os.path.dirname( __file__ ) + "/shaders/types.osl" )

			os.environ["OSL_SHADER_PATHS"] = os.path.dirname( s )
			n = GafferOSL.OSLShader()
			n.loadShader( os.path.basename( s ) )

			self.assertEqual( n["parameters"].keys(), [ "i", "f", "c", "s", "m" ] )
		finally:
			os.environ["OSL_SHADER_PATHS"] = standardShaderPaths

	def testNoConnectionToParametersPlug( self ) :

		vectorToFloat = GafferOSL.OSLShader()
		vectorToFloat.loadShader( "Conversion/VectorToFloat" )

		globals = GafferOSL.OSLShader()
		globals.loadShader( "Utility/Globals" )

		vectorToFloat["parameters"]["p"].setInput( globals["out"]["globalP"] )

		self.assertTrue( vectorToFloat["parameters"]["p"].getInput().isSame( globals["out"]["globalP"] ) )
		self.assertTrue( vectorToFloat["parameters"]["p"][0].getInput().isSame( globals["out"]["globalP"][0] ) )
		self.assertTrue( vectorToFloat["parameters"]["p"][1].getInput().isSame( globals["out"]["globalP"][1] ) )
		self.assertTrue( vectorToFloat["parameters"]["p"][2].getInput().isSame( globals["out"]["globalP"][2] ) )
		self.assertTrue( vectorToFloat["parameters"].getInput() is None )

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
		self.assertEqual( n["parameters"]["s"]["c"].defaultValue(), imath.Color3f( 1, 2, 3 ) )
		self.assertEqual( n["parameters"]["s"]["s"].defaultValue(), "s" )

		n["parameters"]["s"]["i"].setValue( 10 )
		n["parameters"]["s"]["f"].setValue( 21 )
		n["parameters"]["s"]["c"].setValue( imath.Color3f( 3, 4, 5 ) )
		n["parameters"]["s"]["s"].setValue( "ttt" )

		network = n.attributes()["osl:shader"]
		shader = network.outputShader()
		self.assertEqual( len( shader.parameters ), 7 )
		self.assertTrue( shader.parameters["i"], IECore.IntData( 2 ) )
		self.assertTrue( shader.parameters["f"], IECore.FloatData( 3 ) )
		self.assertTrue( shader.parameters["s.i"], IECore.IntData( 10 ) )
		self.assertTrue( shader.parameters["s.f"], IECore.FloatData( 21 ) )
		self.assertTrue( shader.parameters["s.c"], IECore.Color3fData( imath.Color3f( 3, 4, 5 ) ) )
		self.assertTrue( shader.parameters["s.s"], IECore.StringData( "ttt" ) )
		self.assertTrue( shader.parameters["ss"], IECore.StringData( "ss" ) )

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

		floatToColor = GafferOSL.OSLShader()
		floatToColor.loadShader( "Conversion/FloatToColor" )

		floatToColor["parameters"]["r"].setInput( globals["out"]["globalU"] )
		h1 = floatToColor.attributesHash()

		floatToColor["parameters"]["r"].setInput( globals["out"]["globalV"] )
		h2 = floatToColor.attributesHash()

		self.assertNotEqual( h1, h2 )

	def testCanConnectVectorToColor( self ) :

		globals = GafferOSL.OSLShader()
		globals.loadShader( "Utility/Globals" )

		constant = GafferOSL.OSLShader()
		constant.loadShader( "Surface/Constant" )

		self.assertTrue( constant["parameters"]["Cs"].acceptsInput( globals["out"]["globalP"] ) )
		constant["parameters"]["Cs"].setInput( globals["out"]["globalP"] )
		self.assertTrue( constant["parameters"]["Cs"].getInput().isSame( globals["out"]["globalP"] ) )

	def testClosureParameters( self ) :

		outputClosureShader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/outputClosure.osl" )
		outputClosure = GafferOSL.OSLShader( "outputClosure" )
		outputClosure.loadShader( outputClosureShader )

		inputClosureShader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/inputClosure.osl" )
		inputClosure = GafferOSL.OSLShader( "inputClosure" )
		inputClosure.loadShader( inputClosureShader )

		self.assertEqual( outputClosure["out"]["c"].typeId(), GafferOSL.ClosurePlug.staticTypeId() )
		self.assertEqual( inputClosure["parameters"]["i"].typeId(), GafferOSL.ClosurePlug.staticTypeId() )

		inputClosure["parameters"]["i"].setInput( outputClosure["out"]["c"] )

		network = inputClosure.attributes()["osl:surface"]
		self.assertEqual( len( network ), 2 )
		self.assertNotIn( "i", network.outputShader().parameters )
		self.assertEqual(
			network.inputConnections( "inputClosure" ),
			[ network.Connection( ( "outputClosure", "c" ), ( "inputClosure", "i" ) ) ]
		)

	def testClosureParametersInputAcceptance( self ) :

		outputClosureShader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/outputClosure.osl" )
		outputClosure = GafferOSL.OSLShader()
		outputClosure.loadShader( outputClosureShader )

		inputClosureShader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/inputClosure.osl" )
		inputClosure = GafferOSL.OSLShader()
		inputClosure.loadShader( inputClosureShader )

		outputColor = GafferOSL.OSLShader()
		outputColor.loadShader( "Conversion/VectorToColor" )

		self.assertTrue( inputClosure["parameters"]["i"].acceptsInput( outputClosure["out"]["c"] ) )
		self.assertFalse( inputClosure["parameters"]["i"].acceptsInput( outputColor["out"]["c"] ) )

	def testOutputClosureDirtying( self ) :

		outputClosureShader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/outputClosure.osl" )
		outputClosure = GafferOSL.OSLShader()
		outputClosure.loadShader( outputClosureShader )

		cs = GafferTest.CapturingSlot( outputClosure.plugDirtiedSignal() )

		outputClosure["parameters"]["e"]["r"].setValue( 10 )

		self.assertTrue( outputClosure["out"] in [ x[0] for x in cs ] )
		self.assertTrue( outputClosure["out"]["c"] in [ x[0] for x in cs ] )

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
		self.assertEqual( set( network.shaders().keys() ), { "Shader1", "Shader2" } )

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
		self.assertEqual( len( network.shaders() ), 3 )

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
		self.assertEqual( n["parameters"]["d"].minValue(), imath.Color3f( 1, 2, 3 ) )
		self.assertEqual( n["parameters"]["d"].maxValue(), imath.Color3f( 4, 5, 6 ) )
		self.assertEqual( n["parameters"]["e"].minValue(), imath.V3f( 1, 2, 3 ) )
		self.assertEqual( n["parameters"]["e"].maxValue(), imath.V3f( 4, 5, 6 ) )
		self.assertEqual( n["parameters"]["f"].minValue(), imath.V3f( 1, 2, 3 ) )
		self.assertEqual( n["parameters"]["f"].maxValue(), imath.V3f( 4, 5, 6 ) )
		self.assertEqual( n["parameters"]["g"].minValue(), imath.V3f( 1, 2, 3 ) )
		self.assertEqual( n["parameters"]["g"].maxValue(), imath.V3f( 4, 5, 6 ) )

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
		point.loadShader( "Conversion/FloatToVector" )

		noise = GafferOSL.OSLShader( "Noise" )
		noise.loadShader( "Pattern/Noise" )

		color = GafferOSL.OSLShader( "Color" )
		color.loadShader( "Conversion/FloatToColor" )

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

		s1Parameters = n["parameters"].keys()
		self.assertEqual(
			s1Parameters,
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
			"commonColor" : imath.Color3f( 1 ),
			"commonString" : "test",
			"commonStruct.commonI" : 11,
			"commonStruct.commonF" : 2.5,
			"commonStruct.commonColor" : imath.Color3f( 0.5 ),
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

		shutil.copyfile( s1 + ".oso", s2 + ".oso" )
		n.reloadShader()
		self.assertEqual(
			n["parameters"].keys(),
			s1Parameters
		)

	def testSplineParameters( self ) :

		s = self.compileShader( os.path.dirname( __file__ ) + "/shaders/splineParameters.osl" )
		n = GafferOSL.OSLShader()
		n.loadShader( s )

		self.assertEqual( n["parameters"].keys(), [ "floatSpline", "colorSpline", "checkLinearSpline" ] )

		self.assertTrue( isinstance( n["parameters"]["floatSpline"], Gaffer.SplineffPlug ) )
		self.assertEqual(
			n["parameters"]["floatSpline"].getValue().spline(),
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
			n["parameters"]["colorSpline"].getValue().spline(),
			IECore.SplinefColor3f(
				IECore.CubicBasisf.bSpline(),
				[
					( 0, imath.Color3f( 0 ) ),
					( 0, imath.Color3f( 0 ) ),
					( 0, imath.Color3f( 0 ) ),
					( 1, imath.Color3f( 1 ) ),
					( 1, imath.Color3f( 1 ) ),
					( 1, imath.Color3f( 1 ) ),
				]
			)
		)

		# Just adding documentation that this is currently broken, but I'm not supposed to be worrying about
		# the parameter import path at the moment ( it's not using
		# IECoreScene::ShaderNetworkAlgo::collapseSplineParameters yet )
		"""self.assertTrue( isinstance( n["parameters"]["checkLinearSpline"], Gaffer.SplineffPlug ) )
		self.assertEqual(
			n["parameters"]["checkLinearSpline"].getValue().spline(),
			IECore.Splineff(
				IECore.CubicBasisf.linear(),
				[
					( 2, 3 ),
					( 4, 5 ),
				]
			)
		)"""

		shader = n.attributes()["osl:shader"].outputShader()

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
					( 0, imath.Color3f( 0 ) ),
					( 0, imath.Color3f( 0 ) ),
					( 0, imath.Color3f( 0 ) ),
					( 1, imath.Color3f( 1 ) ),
					( 1, imath.Color3f( 1 ) ),
					( 1, imath.Color3f( 1 ) ),
				]
			)
		)

	def testSplineParameterEvaluation( self ) :

		numSamples = 100

		s = self.compileShader( os.path.dirname( __file__ ) + "/shaders/splineParameters.osl" )
		n = GafferOSL.OSLShader()
		n.loadShader( s )

		points = [
			( 0, imath.Color3f( 0.5 ) ),
			( 0.3, imath.Color3f( 0.2 ) ),
			( 0.6, imath.Color3f( 1 ) ),
			( 0.65, imath.Color3f( 0.5 ) ),
			( 0.9, imath.Color3f( 0.7 ) ),
			( 1, imath.Color3f( 1 ) )
		]

		constant = GafferImage.Constant( "Constant" )
		constant["format"].setValue( GafferImage.Format( 1, numSamples, 1.000 ) )

		image = GafferOSL.OSLImage()
		image["in"].setInput( constant["out"] )

		image["shader"].setInput( n["out"]["out"] )

		for interpolation in [
			Gaffer.SplineDefinitionInterpolation.Linear,
			Gaffer.SplineDefinitionInterpolation.CatmullRom,
			Gaffer.SplineDefinitionInterpolation.BSpline,
			Gaffer.SplineDefinitionInterpolation.MonotoneCubic
			]:

			n["parameters"]["colorSpline"].setValue( Gaffer.SplineDefinitionfColor3f( points, interpolation ) )

			oslSamples = list( reversed( GafferImage.ImageAlgo.image( image['out'] )["R"] ) )

			s = n['parameters']['colorSpline'].getValue().spline()
			cortexSamples = [ s( ( i + 0.5 ) / numSamples )[0] for i in range( numSamples ) ]

			for a, b in zip( oslSamples, cortexSamples ):
				self.assertAlmostEqual( a, b, places = 4 )

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
			[ imath.Color3f( 1, 2, 3 ), imath.Color3f( 4, 5, 6 ) ] ) )
		self.assertEqual( n["parameters"]["p"].defaultValue(), IECore.V3fVectorData(
			[ imath.V3f( 1, 2, 3 ), imath.V3f( 4, 5, 6 ) ] ) )
		self.assertEqual( n["parameters"]["q"].defaultValue(), IECore.V3fVectorData(
			[ imath.V3f( 1, 2, 3 ), imath.V3f( 4, 5, 6 ) ] ) )
		self.assertEqual( n["parameters"]["s"].defaultValue(), IECore.StringVectorData( [ "s", "t", "u", "v", "word" ] ) )
		self.assertEqual( n["parameters"]["m"].defaultValue(), IECore.M44fVectorData(
			[ imath.M44f() * 1, imath.M44f() * 0, imath.M44f() * 1 ] ) )

		self.assertEqual( n["out"].typeId(), Gaffer.Plug.staticTypeId() )

		network = n.attributes()["osl:surface"]
		self.assertEqual( len( network ), 1 )
		self.assertEqual( network.outputShader().name, s )
		self.assertEqual( network.outputShader().type, "osl:surface" )
		self.assertEqual( network.outputShader().parameters["i"], IECore.IntVectorData( [ 10, 11, 12 ] ) )
		self.assertEqual( network.outputShader().parameters["f"], IECore.FloatVectorData( [ 1, 2 ] ) )
		self.assertEqual( network.outputShader().parameters["c"], IECore.Color3fVectorData(
			[ imath.Color3f( 1, 2, 3 ), imath.Color3f( 4, 5, 6 ) ] ) )
		self.assertEqual( network.outputShader().parameters["p"], IECore.V3fVectorData(
			[ imath.V3f( 1, 2, 3 ), imath.V3f( 4, 5, 6 ) ] ) )
		self.assertEqual( network.outputShader().parameters["q"], IECore.V3fVectorData(
			[ imath.V3f( 1, 2, 3 ), imath.V3f( 4, 5, 6 ) ] ) )
		self.assertEqual( network.outputShader().parameters["s"], IECore.StringVectorData( [ "s", "t", "u", "v", "word" ] ) )
		self.assertEqual( network.outputShader().parameters["m"], IECore.M44fVectorData(
			[ imath.M44f() * 1, imath.M44f() * 0, imath.M44f() * 1 ] ) )

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
		s["n1"].loadShader( "Maths/AddVector" )

		s["n2"] = GafferOSL.OSLShader()
		s["n2"].loadShader( "Maths/AddVector" )

		s["n3"] = GafferOSL.OSLShader()
		s["n3"].loadShader( "Maths/AddVector" )

		s["n2"]["parameters"]["a"].setInput( s["n1"]["out"]["out"] )
		s["n3"]["parameters"]["a"].setInput( s["n2"]["out"]["out"] )

		s.deleteNodes( filter = Gaffer.StandardSet( [ s["n2"] ] ) )
		self.assertTrue( s["n3"]["parameters"]["a"].getInput().isSame( s["n1"]["out"]["out"] ) )

	def testDisablingShader( self ) :

		n1 = GafferOSL.OSLShader( "n1" )
		n1.loadShader( "Maths/AddVector" )
		n1["parameters"]["a"].setValue( imath.V3f( 5, 7, 6 ) )

		n2 = GafferOSL.OSLShader( "n2" )
		n2.loadShader( "Maths/AddVector" )

		n3 = GafferOSL.OSLShader( "n3" )
		n3.loadShader( "Maths/AddVector" )

		n2["parameters"]["a"].setInput( n1["out"]["out"] )
		n3["parameters"]["a"].setInput( n2["out"]["out"] )

		n2["enabled"].setValue( False )
		network = n3.attributes()["osl:shader"]
		self.assertEqual( len( network ), 2 )
		self.assertEqual( network.inputConnections( "n3" ), [ network.Connection( ( "n1", "out" ), ( "n3", "a" ) ) ] )
		self.assertEqual( network.getShader( "n1" ).parameters["a"].value, imath.V3f( 5, 7, 6 ) )

	def testDisabledShaderPassesThroughExternalValue( self ) :

		n1 = Gaffer.Node()
		n1["user"]["v"] = Gaffer.V3fPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		n1["user"]["v"].setValue( imath.V3f( 12, 11, 10 ) )

		n2 = GafferOSL.OSLShader( "n2" )
		n2.loadShader( "Maths/AddVector" )
		n2["parameters"]["a"].setInput( n1["user"]["v"] )

		n3 = GafferOSL.OSLShader( "n3" )
		n3.loadShader( "Maths/AddVector" )
		n3["parameters"]["a"].setInput( n2["parameters"]["a"] )

		n2["enabled"].setValue( False )

		network = n3.attributes()["osl:shader"]
		self.assertEqual( len( network ), 1 )
		self.assertEqual( network.getShader( "n3" ).parameters["a"].value, imath.V3f( 12, 11, 10 ) )

	def testDisabledShaderEvaluatesStateCorrectly( self ) :

		redShader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/red.osl" )
		greenShader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/green.osl" )

		n2 = GafferOSL.OSLShader( "red1" )
		n2.loadShader( redShader )

		n3 = GafferOSL.OSLShader( "green1" )
		n3.loadShader( greenShader )

		n1 = GafferOSL.OSLShader( "add" )
		n1.loadShader( self.compileShader( os.path.dirname( __file__ ) + "/shaders/add.osl" ) )

		n1['parameters']['a'].setInput(n2["out"]["out"])
		n1['parameters']['b'].setInput(n3["out"]["out"])

		sphere = GafferScene.Sphere()

		shaderAssignment  = GafferScene.ShaderAssignment()
		shaderAssignment["in"].setInput(sphere["out"])

		pathFilter = GafferScene.PathFilter()
		pathFilter["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )

		shaderAssignment["filter"].setInput(pathFilter["out"])
		shaderAssignment["shader"].setInput(n1["out"]["out"])

		network = shaderAssignment["out"].attributes( "/sphere" )["osl:surface"]
		self.assertEqual( len( network ), 3 )

		self.assertEqual( network.getShader( "red1" ).name.split( "/" )[-1], "red" )
		self.assertEqual( network.getShader( "green1" ).name.split( "/" )[-1], "green")
		self.assertEqual( network.getShader( "add" ).name.split( "/" )[-1], "add")

		# when we disable the add shader we should get the pass through parameter's ("a") shader (n2)
		n1["enabled"].setValue( False )

		network = shaderAssignment["out"].attributes( "/sphere" )["osl:surface"]
		self.assertEqual( len ( network ), 1 )
		self.assertEqual( network.getShader( "red1" ).name.split( "/" )[-1], "red" )

	def testShaderSerialisation( self ) :

		s = Gaffer.ScriptNode()
		s['n2'] = GafferOSL.OSLShader()
		s['n2'].loadShader( "Pattern/Noise" )
		s['n'] = GafferOSL.OSLShader()
		s['n'].loadShader( "Pattern/Noise" )
		s['n2']['parameters']['scale'].setInput( s['n']['out']['n'] )
		self.assertEqual( s['n2']['parameters']['scale'].getInput(), s['n']['out']['n'] )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( s2['n2']['parameters']['scale'].getInput(), s2['n']['out']['n'] )

	def testSplineParameterSerialisation( self ) :

		s = Gaffer.ScriptNode()

		shad = self.compileShader( os.path.dirname( __file__ ) + "/shaders/splineParameters.osl" )
		s['n'] = GafferOSL.OSLShader()
		s['n'].loadShader( shad )

		splineValue = Gaffer.SplineDefinitionfColor3f( [ ( random.random(), imath.Color3f( random.random(), random.random(), random.random() ) ) for i in range( 10 ) ], Gaffer.SplineDefinitionInterpolation.Linear )

		s['n']["parameters"]["colorSpline"].setValue( splineValue )

		serialised = s.serialise()

		colorSplineLines = [ i for i in serialised.split( "\n" ) if "colorSpline" in i ]

		# Expect a clearPoint line to get serialised
		self.assertEqual( 1, sum( "clearPoints" in i for i in colorSplineLines ) )

		# Expect 3 addChilds per point ( The parent plug, and x and y )
		self.assertEqual( 30, sum( "addChild" in i for i in colorSplineLines ) )

		s2 = Gaffer.ScriptNode()
		s2.execute( serialised )
		self.assertEqual( s2['n']["parameters"]["colorSpline"].getValue(), splineValue )

	def testComponentToComponentConnections( self ) :

		n1 = GafferOSL.OSLShader( "n1" )
		n1.loadShader( "Maths/MixColor" )

		n2 = GafferOSL.OSLShader( "n2" )
		n2.loadShader( "Maths/MixColor" )

		n2["parameters"]["a"]["r"].setInput( n1["out"]["out"]["g"] )
		n2["parameters"]["a"]["g"].setInput( n1["out"]["out"]["b"] )
		n2["parameters"]["a"]["b"].setInput( n1["out"]["out"]["r"] )

		network = n2.attributes()["osl:shader"]
		self.assertEqual(
			network.inputConnections( "n2" ),
			[
				( ( "n1", "out.r" ), ( "n2", "a.b" ) ),
				( ( "n1", "out.b" ), ( "n2", "a.g" ) ),
				( ( "n1", "out.g" ), ( "n2", "a.r" ) ),
			]
		)

	def testGetConnectedParameterValueInsideSceneNode( self ) :

		n = GafferScene.SceneNode()

		n["n1"] = GafferOSL.OSLShader()
		n["n1"].loadShader( "Maths/AddColor" )

		n["n2"] = GafferOSL.OSLShader()
		n["n2"].loadShader( "Maths/AddColor" )

		n["n2"]["parameters"]["a"].setInput( n["n1"]["out"]["out"] )
		self.assertEqual( n["n2"]["parameters"]["a"].getValue(), imath.Color3f( 0 ) )

	def testOutputNameIncludedInNetwork( self ) :

		shader = GafferOSL.OSLShader( "globals" )
		shader.loadShader( "Utility/Globals" )

		shaderPlug = GafferScene.ShaderPlug()
		shaderPlug.setInput( shader["out"] )
		network1 = shaderPlug.attributes()["osl:shader"]
		hash1 = shaderPlug.attributesHash()

		shaderPlug.setInput( shader["out"]["globalP"] )
		network2 = shaderPlug.attributes()["osl:shader"]
		hash2 = shaderPlug.attributesHash()

		shaderPlug.setInput( shader["out"]["globalN"] )
		network3 = shaderPlug.attributes()["osl:shader"]
		hash3 = shaderPlug.attributesHash()

		self.assertEqual( network1.getOutput(), IECoreScene.ShaderNetwork.Parameter( "globals" ) )
		self.assertEqual( network2.getOutput(), IECoreScene.ShaderNetwork.Parameter( "globals", "globalP" ) )
		self.assertEqual( network3.getOutput(), IECoreScene.ShaderNetwork.Parameter( "globals", "globalN" ) )

		self.assertEqual( network1.getShader( "global" ), network2.getShader( "global" ) )
		self.assertEqual( network1.getShader( "global" ), network3.getShader( "global" ) )

		self.assertNotEqual( hash1, hash2 )
		self.assertNotEqual( hash2, hash3 )

	def testShaderTypeAssignsAsSurfaceType( self ) :

		plane = GafferScene.Plane()

		planeFilter = GafferScene.PathFilter()
		planeFilter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		shader = GafferOSL.OSLShader( "globals" )
		shader.loadShader( "Maths/AddColor" )

		shaderAssignment = GafferScene.ShaderAssignment()
		shaderAssignment["in"].setInput( plane["out"] )
		shaderAssignment["shader"].setInput( shader["out"]["out"] )
		shaderAssignment["filter"].setInput( planeFilter["out"] )

		self.assertEqual( shaderAssignment["out"].attributes( "/plane" ).keys(), [ "osl:surface" ] )

	def testConstantOutPlug( self ) :

		# For compatibility with Arnold, we hack an output closure
		# parameter onto our Constant shader, but we don't want that
		# to affect the way we represent the output plug in Gaffer.
		shader = GafferOSL.OSLShader()
		shader.loadShader( "Surface/Constant" )
		self.assertEqual( len( shader["out"].children() ), 0 )

	def testLoadMxInvertFloat( self ) :

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( os.path.join( os.path.dirname( __file__ ), "scripts", "mxInvert-0.59.8.0.gfr" ) )
		s.load()

		self.assertEqual( s["mx_invert_float"]["parameters"]["in"].getValue(), 1 )
		self.assertEqual( s["mx_invert_float"]["parameters"]["amount"].getValue(), 2 )

if __name__ == "__main__":
	unittest.main()
