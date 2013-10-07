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

import IECore

import Gaffer
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
		
if __name__ == "__main__":
	unittest.main()
