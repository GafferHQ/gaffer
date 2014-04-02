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
		
		self.assertEqual( n["parameters"].keys(), [ "i", "f", "c", "s" ] )
		
		self.assertTrue( isinstance( n["parameters"]["i"], Gaffer.IntPlug ) )
		self.assertTrue( isinstance( n["parameters"]["f"], Gaffer.FloatPlug ) )
		self.assertTrue( isinstance( n["parameters"]["c"], Gaffer.Color3fPlug ) )
		self.assertTrue( isinstance( n["parameters"]["s"], Gaffer.StringPlug ) )
		
		self.assertEqual( n["parameters"]["i"].defaultValue(), 10 )
		self.assertEqual( n["parameters"]["f"].defaultValue(), 1 )
		self.assertEqual( n["parameters"]["c"].defaultValue(), IECore.Color3f( 1, 2, 3 ) )
		self.assertEqual( n["parameters"]["s"].defaultValue(), "s" )
	
		self.assertEqual( n["out"].typeId(), Gaffer.Plug.staticTypeId() )
	
		state = n.state()
		self.assertEqual( len( state ), 1 )
		self.assertEqual( state[0].name, s )
		self.assertEqual( state[0].type, "osl:surface" )
		self.assertEqual( state[0].parameters["i"], IECore.IntData( 10 ) )
		self.assertEqual( state[0].parameters["f"], IECore.FloatData( 1 ) )
		self.assertEqual( state[0].parameters["c"], IECore.Color3fData( IECore.Color3f( 1, 2, 3 ) ) )
		self.assertEqual( state[0].parameters["s"], IECore.StringData( "s" ) )
	
	def testOutputTypes( self ) :
	
		s = self.compileShader( os.path.dirname( __file__ ) + "/shaders/outputTypes.osl" )
	
		n = GafferOSL.OSLShader()
		n.loadShader( s )
		
		self.assertEqual( n["name"].getValue(), s )
		self.assertEqual( n["type"].getValue(), "osl:shader" )
	
		self.assertEqual( len( n["parameters"] ), 1 )
		self.assertEqual( n["parameters"].keys(), [ "input" ] )
		
		self.assertEqual( n["out"].typeId(), Gaffer.CompoundPlug.staticTypeId() )
		self.assertEqual( n["out"].keys(), [ "i", "f", "c", "s" ] )

	def testNetwork( self ) :
	
		typesShader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/types.osl" )
		outputTypesShader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/outputTypes.osl" )
		
		typesNode = GafferOSL.OSLShader()
		outputTypesNode = GafferOSL.OSLShader()
		
		typesNode.loadShader( typesShader )
		outputTypesNode.loadShader( outputTypesShader )
		
		typesNode["parameters"]["i"].setInput( outputTypesNode["out"]["i"] )
		
		self.assertEqual( typesNode["parameters"]["i"].getValue(), 10 )
		
		state = typesNode.state()
		
		self.assertEqual( len( state ), 2 )
		
		self.assertEqual( state[1].name, typesShader )	
		self.assertEqual( state[1].type, "osl:surface" )
		self.assertEqual( state[1].parameters["i"], IECore.StringData( "link:" + state[0].parameters["__handle"].value + ".i" ) )
		self.assertEqual( state[1].parameters["f"], IECore.FloatData( 1 ) )
		self.assertEqual( state[1].parameters["c"], IECore.Color3fData( IECore.Color3f( 1, 2, 3 ) ) )
		self.assertEqual( state[1].parameters["s"], IECore.StringData( "s" ) )
		self.assertEqual( state[0].name, outputTypesShader )	
		self.assertEqual( state[0].type, "shader" )
		self.assertEqual( state[0].parameters["input"], IECore.FloatData( 1 ) )

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
		
		self.assertEqual( n["parameters"].keys(), [ "i", "f", "c", "s" ] )
	
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
		
		state = n.state()
		self.assertEqual( len( state[0].parameters ), 7 )
		self.assertTrue( state[0].parameters["i"], IECore.IntData( 2 ) )
		self.assertTrue( state[0].parameters["f"], IECore.FloatData( 3 ) )
		self.assertTrue( state[0].parameters["s.i"], IECore.IntData( 10 ) )
		self.assertTrue( state[0].parameters["s.f"], IECore.FloatData( 21 ) )
		self.assertTrue( state[0].parameters["s.c"], IECore.Color3fData( IECore.Color3f( 3, 4, 5 ) ) )
		self.assertTrue( state[0].parameters["s.s"], IECore.StringData( "ttt" ) )
		self.assertTrue( state[0].parameters["ss"], IECore.StringData( "ss" ) )
		
		h1 = n.stateHash()

		n["parameters"]["s"]["i"].setValue( 100 )
		h2 = n.stateHash()
		self.assertNotEqual( h1, h2 )
		
		s2 = self.compileShader( os.path.dirname( __file__ ) + "/shaders/outputTypes.osl" )
		g = GafferOSL.OSLShader()
		g.loadShader( s2 )
					
		n["parameters"]["s"]["i"].setInput( g["out"]["i"] )
		h3 = n.stateHash()
		self.assertNotEqual( h1, h3 )
		self.assertNotEqual( h2, h3 )
	
	def testOutputPlugAffectsHash( self ) :
	
		globals = GafferOSL.OSLShader()
		globals.loadShader( "Utility/Globals" )
		
		buildColor = GafferOSL.OSLShader()
		buildColor.loadShader( "Utility/BuildColor" )
		
		buildColor["parameters"]["r"].setInput( globals["out"]["globalU"] )
		h1 = buildColor.stateHash()
		
		buildColor["parameters"]["r"].setInput( globals["out"]["globalV"] )
		h2 = buildColor.stateHash()
		
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
		
		s = inputClosure.state()
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
		
		self.assertEqual( sn2.stateHash(), sn2.stateHash() )
		self.assertEqual( sn2.state(), sn2.state() )
	
	def testHandlesAreHumanReadable( self ) :
	
		s1 = self.compileShader( os.path.dirname( __file__ ) + "/shaders/outputTypes.osl" )
		s2 = self.compileShader( os.path.dirname( __file__ ) + "/shaders/types.osl" )

		sn1 = GafferOSL.OSLShader( "Shader1" )
		sn1.loadShader( s1 )
		
		sn2 = GafferOSL.OSLShader( "Shader2" )
		sn2.loadShader( s2 )
		
		sn2["parameters"]["i"].setInput( sn1["out"]["i"] )
		
		state = sn2.state()
		self.assertTrue( "Shader1" in state[0].parameters["__handle"].value )
	
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
		
		state = script["shader"].state()
		self.assertNotEqual( state[0].parameters["__handle"], state[1].parameters["__handle"] )
	
	# As best as I can tell, OSL doesn't actually implement the shader level metadata
	# that it describes in the language spec.
	@unittest.expectedFailure
	def testShaderMetadata( self ) :
	
		s = self.compileShader( os.path.dirname( __file__ ) + "/shaders/metadata.osl" )
		n = GafferOSL.OSLShader()
		n.loadShader( s )
				
		self.assertEqual( n.shaderMetadata( "stringValue" ), IECore.StringData( "s" ) )
		self.assertEqual( n.shaderMetadata( "intValue" ), IECore.IntData( 1 ) )
		self.assertEqual( n.shaderMetadata( "floatValue" ), IECore.FloatData( 0.5 ) )

	def testParameterMetadata( self ) :
	
		s = self.compileShader( os.path.dirname( __file__ ) + "/shaders/metadata.osl" )
		n = GafferOSL.OSLShader()
		n.loadShader( s )
				
		self.assertEqual( n.parameterMetadata( n["parameters"]["a"], "aStringValue" ), IECore.StringData( "s" ) )
		self.assertEqual( n.parameterMetadata( n["parameters"]["a"], "aIntValue" ), IECore.IntData( 1 ) )
		self.assertEqual( n.parameterMetadata( n["parameters"]["a"], "aFloatValue" ), IECore.FloatData( 0.5 ) )
		
		self.assertEqual( n.parameterMetadata( n["parameters"]["b"], "bStringValue" ), IECore.StringData( "st" ) )
		self.assertEqual( n.parameterMetadata( n["parameters"]["b"], "bIntValue" ), IECore.IntData( 2 ) )
		self.assertEqual( n.parameterMetadata( n["parameters"]["b"], "bFloatValue" ), IECore.FloatData( 0.75 ) )
	
	def testMetadaReuse( self ) :
	
		s = self.compileShader( os.path.dirname( __file__ ) + "/shaders/metadata.osl" )
		
		n1 = GafferOSL.OSLShader()
		n1.loadShader( s )
		
		n2 = GafferOSL.OSLShader()
		n2.loadShader( s )
		
		# we don't want every shader to have its own copy of metadata when it could be shared
		self.assertTrue(
			n1.parameterMetadata( n1["parameters"]["a"], "aStringValue", _copy = False ).isSame(
				n2.parameterMetadata( n2["parameters"]["a"], "aStringValue", _copy = False )
			)
		)
	
		# but because there is no const in python, we want to make sure that the casual
		# caller doesn't have the opportunity to really break things, so unless requested
		# copies are returned from the query.
		n1.parameterMetadata( n1["parameters"]["a"], "aStringValue" ).value = "editingSharedConstDataIsABadIdea"
		self.assertEqual( n1.parameterMetadata( n1["parameters"]["a"], "aStringValue" ), IECore.StringData( "s" ) )

	def testAcceptsNoneInput( self ) :
	
		s = self.compileShader( os.path.dirname( __file__ ) + "/shaders/types.osl" )
		n = GafferOSL.OSLShader()
		n.loadShader( s )
		
		self.assertTrue( n["parameters"]["i"].acceptsInput( None ) )
		
if __name__ == "__main__":
	unittest.main()
