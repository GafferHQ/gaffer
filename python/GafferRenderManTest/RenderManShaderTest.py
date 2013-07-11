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

import os
import unittest

import IECore

import Gaffer
import GafferTest
import GafferScene
import GafferRenderMan
import GafferRenderManTest

class RenderManShaderTest( GafferRenderManTest.RenderManTestCase ) :

	def setUp( self ) :

		GafferRenderManTest.RenderManTestCase.setUp( self )
		
		GafferRenderMan.RenderManShader.shaderLoader().clear()
	
	def test( self ) :
	
		n = GafferRenderMan.RenderManShader()
		n.loadShader( "plastic" )
	
		self.failUnless( isinstance( n["parameters"]["Ks"], Gaffer.FloatPlug ) )
		self.failUnless( isinstance( n["parameters"]["Kd"], Gaffer.FloatPlug ) )
		self.failUnless( isinstance( n["parameters"]["Ka"], Gaffer.FloatPlug ) )
		self.failUnless( isinstance( n["parameters"]["roughness"], Gaffer.FloatPlug ) )
		self.failUnless( isinstance( n["parameters"]["specularcolor"], Gaffer.Color3fPlug ) )
	
		self.assertEqual( n["parameters"]["Ks"].getValue(), 0.5 )
		self.assertEqual( n["parameters"]["Kd"].getValue(), 0.5 )
		self.assertEqual( n["parameters"]["Ka"].getValue(), 1 )
		self.assertAlmostEqual( n["parameters"]["roughness"].getValue(), 0.1 )
		self.assertEqual( n["parameters"]["specularcolor"].getValue(), IECore.Color3f( 1 ) )
	
	def testSerialisation( self ) :
	
		s = Gaffer.ScriptNode()
		s["n"] = GafferRenderMan.RenderManShader()
		s["n"].loadShader( "plastic" )
		
		ss = s.serialise()
		
		s = Gaffer.ScriptNode()
		s.execute( ss )
		
		st = s["n"].state()
		self.assertEqual( len( st ), 1 )
		
		self.assertEqual( st[0].type, "ri:surface" )
		self.assertEqual( st[0].name, "plastic" )
		
		self.failUnless( isinstance( s["n"]["parameters"]["Ks"], Gaffer.FloatPlug ) )
		self.failUnless( isinstance( s["n"]["parameters"]["Kd"], Gaffer.FloatPlug ) )
		self.failUnless( isinstance( s["n"]["parameters"]["Ka"], Gaffer.FloatPlug ) )
		self.failUnless( isinstance( s["n"]["parameters"]["roughness"], Gaffer.FloatPlug ) )
		self.failUnless( isinstance( s["n"]["parameters"]["specularcolor"], Gaffer.Color3fPlug ) )
	
		self.assertTrue( "parameters1" not in s["n"] )
	
	def testShader( self ) :
	
		n = GafferRenderMan.RenderManShader()
		n.loadShader( "plastic" )
		
		s = n.state()
		self.assertEqual( len( s ), 1 )
		
		self.assertEqual( s[0].type, "ri:surface" )
		self.assertEqual( s[0].name, "plastic" )
		
		self.assertEqual( s[0].parameters["Ks"], IECore.FloatData( .5 ) )
		self.assertEqual( s[0].parameters["Kd"], IECore.FloatData( .5 ) )
		self.assertEqual( s[0].parameters["Ka"], IECore.FloatData( 1 ) )
		self.assertEqual( s[0].parameters["roughness"], IECore.FloatData( .1 ) )
		self.assertEqual( s[0].parameters["specularcolor"], IECore.Color3fData( IECore.Color3f( 1 ) ) )
	
	def testShaderHash( self ) :
	
		n = GafferRenderMan.RenderManShader()
		n.loadShader( "checker" )
		h1 = n.stateHash()
		
		n["parameters"]["Kd"].setValue( 0.25 )
		self.assertNotEqual( n.stateHash(), h1 )
		
	def testCoshaderHash( self ) :
	
		shader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/coshaderParameter.sl" )
	
		shaderNode = GafferRenderMan.RenderManShader()
		shaderNode.loadShader( shader )
		
		self.assertTrue( "coshaderParameter" in shaderNode["parameters"] )
		self.assertEqual( shaderNode["parameters"]["coshaderParameter"].typeId(), Gaffer.Plug.staticTypeId() )
		
		coshader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/coshader.sl" )
		
		coshaderNode = GafferRenderMan.RenderManShader()
		coshaderNode.loadShader( coshader )
		
		shaderNode["parameters"]["coshaderParameter"].setInput( coshaderNode["out"] )
		
		h1 = shaderNode.stateHash()
		
		coshaderNode["parameters"]["floatParameter"].setValue( 0.25 )
		
		self.assertNotEqual( shaderNode.stateHash(), h1 )
	
	def testParameterOrdering( self ) :
	
		n = GafferRenderMan.RenderManShader()
		n.loadShader( "plastic" )
		
		self.assertEqual( n["parameters"][0].getName(), "Ks" )
		self.assertEqual( n["parameters"][1].getName(), "Kd" )
		self.assertEqual( n["parameters"][2].getName(), "Ka" )
		self.assertEqual( n["parameters"][3].getName(), "roughness" )
		self.assertEqual( n["parameters"][4].getName(), "specularcolor" )
		
		n = GafferRenderMan.RenderManShader()
		n.loadShader( "matte" )
		
		self.assertEqual( n["parameters"][0].getName(), "Ka" )
		self.assertEqual( n["parameters"][1].getName(), "Kd" )
	
	def testCoshader( self ) :
	
		shader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/coshaderParameter.sl" )
	
		shaderNode = GafferRenderMan.RenderManShader()
		shaderNode.loadShader( shader )
		
		self.assertTrue( "coshaderParameter" in shaderNode["parameters"] )
		self.assertEqual( shaderNode["parameters"]["coshaderParameter"].typeId(), Gaffer.Plug.staticTypeId() )
		
		coshader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/coshader.sl" )
		
		coshaderNode = GafferRenderMan.RenderManShader()
		coshaderNode.loadShader( coshader )
		
		shaderNode["parameters"]["coshaderParameter"].setInput( coshaderNode["out"] )
		
		s = shaderNode.state()
		self.assertEqual( len( s ), 2 )
		
		self.assertEqual( s[0].name, coshader )
		self.assertEqual( s[1].name, shader )
		self.assertEqual( s[0].parameters["__handle"], s[1].parameters["coshaderParameter"] )
	
	def testInputAcceptance( self ) :
	
		shader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/coshaderParameter.sl" )
		shaderNode = GafferRenderMan.RenderManShader()
		shaderNode.loadShader( shader )
		
		coshader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/coshader.sl" )
		coshaderNode = GafferRenderMan.RenderManShader()
		coshaderNode.loadShader( coshader )
		
		random = Gaffer.Random()
		
		self.assertTrue( shaderNode["parameters"]["coshaderParameter"].acceptsInput( coshaderNode["out"] ) )
		self.assertFalse( shaderNode["parameters"]["coshaderParameter"].acceptsInput( random["outFloat"] ) )
		
		self.assertTrue( shaderNode["parameters"]["floatParameter"].acceptsInput( random["outFloat"] ) )
		self.assertFalse( shaderNode["parameters"]["floatParameter"].acceptsInput( coshaderNode["out"] ) )
		
		self.assertTrue( coshaderNode["parameters"]["colorParameter"].acceptsInput( random["outColor"] ) )
		self.assertFalse( coshaderNode["parameters"]["colorParameter"].acceptsInput( coshaderNode["out"] ) )
	
	def testParameterDefaultValue( self ) :
	
		shader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/coshaderParameter.sl" )
		shaderNode = GafferRenderMan.RenderManShader()
		shaderNode.loadShader( shader )
		
		self.assertEqual( shaderNode["parameters"]["floatParameter"].defaultValue(), 1 )
	
	def testParameterMinMax( self ) :
	
		shader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/coshaderParameter.sl" )
		shaderNode = GafferRenderMan.RenderManShader()
		shaderNode.loadShader( shader )
		
		self.assertEqual( shaderNode["parameters"]["floatParameter"].minValue(), -1 )
		self.assertEqual( shaderNode["parameters"]["floatParameter"].maxValue(), 10 )
	
	def testReload( self ) :
	
		shader1 = self.compileShader( os.path.dirname( __file__ ) + "/shaders/version1.sl" )
		
		shaderNode = GafferRenderMan.RenderManShader()
		shaderNode.loadShader( shader1 )
		shaderNode["parameters"]["float1"].setValue( 0.1 )
		shaderNode["parameters"]["string1"].setValue( "test" )
		shaderNode["parameters"]["color1"].setValue( IECore.Color3f( 1, 2, 3 ) )
		self.assertAlmostEqual( shaderNode["parameters"]["float1"].getValue(), 0.1 )
		self.assertEqual( shaderNode["parameters"]["string1"].getValue(), "test" )
		self.assertEqual( shaderNode["parameters"]["color1"].getValue(), IECore.Color3f( 1, 2, 3 ) )
		
		shader2 = self.compileShader( os.path.dirname( __file__ ) + "/shaders/version2.sl" )
		shaderNode.loadShader( shader2, keepExistingValues=True )
		
		self.assertEqual( shaderNode["parameters"].keys(), [ "float1", "string1", "color1", "float2", "string2", "color2" ] )
		self.assertAlmostEqual( shaderNode["parameters"]["float1"].getValue(), 0.1 )
		self.assertEqual( shaderNode["parameters"]["string1"].getValue(), "test" )
		self.assertEqual( shaderNode["parameters"]["color1"].getValue(), IECore.Color3f( 1, 2, 3 ) )
		
		shaderNode.loadShader( shader1, keepExistingValues=True )
		
		self.assertEqual( shaderNode["parameters"].keys(), [ "float1", "string1", "color1" ] )
		self.assertAlmostEqual( shaderNode["parameters"]["float1"].getValue(), 0.1 )
		self.assertEqual( shaderNode["parameters"]["string1"].getValue(), "test" )
		self.assertEqual( shaderNode["parameters"]["color1"].getValue(), IECore.Color3f( 1, 2, 3 ) )

		shaderNode.loadShader( shader1, keepExistingValues=False )
		
		self.assertEqual( shaderNode["parameters"].keys(), [ "float1", "string1", "color1" ] )
		self.assertEqual( shaderNode["parameters"]["float1"].getValue(), 1 )
		self.assertEqual( shaderNode["parameters"]["string1"].getValue(), "" )
		self.assertEqual( shaderNode["parameters"]["color1"].getValue(), IECore.Color3f( 1, 1, 1 ) )
	
	def testReloadRemovesOldParameters( self ) :
		
		shader2 = self.compileShader( os.path.dirname( __file__ ) + "/shaders/version2.sl" )
		
		shaderNode = GafferRenderMan.RenderManShader()
		shaderNode.loadShader( shader2 )
		
		self.assertEqual( shaderNode["parameters"].keys(), [ "float1", "string1", "color1", "float2", "string2", "color2" ] )

		shader3 = self.compileShader( os.path.dirname( __file__ ) + "/shaders/version3.sl" )
		shaderNode.loadShader( shader3 )
		
		self.assertEqual( shaderNode["parameters"].keys(), [ "float1", "string1", "color1", "float2" ] )		
			
	def testAutomaticReloadOnScriptLoad( self ) :
	
		shader1 = self.compileShader( os.path.dirname( __file__ ) + "/shaders/version1.sl", shaderName = "unversioned" )

		s = Gaffer.ScriptNode()
		s["shader"] = GafferRenderMan.RenderManShader()
		s["shader"].loadShader( shader1 )
		s["shader"]["parameters"]["float1"].setValue( 0.1 )
		s["shader"]["parameters"]["string1"].setValue( "test" )
		s["shader"]["parameters"]["color1"].setValue( IECore.Color3f( 1, 2, 3 ) )
		
		ss = s.serialise()
		
		self.compileShader( os.path.dirname( __file__ ) + "/shaders/version2.sl", shaderName = "unversioned" )
		
		GafferRenderMan.RenderManShader.shaderLoader().clear()
		
		s = Gaffer.ScriptNode()
		s.execute( ss )
		
		self.assertEqual( s["shader"]["parameters"].keys(), [ "float1", "string1", "color1", "float2", "string2", "color2" ] )
		self.assertAlmostEqual( s["shader"]["parameters"]["float1"].getValue(), 0.1 )
		self.assertEqual( s["shader"]["parameters"]["string1"].getValue(), "test" )
		self.assertEqual( s["shader"]["parameters"]["color1"].getValue(), IECore.Color3f( 1, 2, 3 ) )
	
	def testReloadPreservesConnections( self ) :
	
		n = GafferRenderMan.RenderManShader()
		n.loadShader( "plastic" )
	
		random = Gaffer.Random()
		
		n["parameters"]["Ks"].setInput( random["outFloat"] )
		n["parameters"]["specularcolor"].setInput( random["outColor"] )
	
		n.loadShader( "plastic", keepExistingValues = True )
		
		self.assertTrue( n["parameters"]["Ks"].getInput().isSame( random["outFloat"] ) )
		self.assertTrue( n["parameters"]["specularcolor"].getInput().isSame( random["outColor"] ) )
	
	def testReloadPreservesConnectionsWhenMinMaxOrDefaultChanges( self ) :
	
		shader1 = self.compileShader( os.path.dirname( __file__ ) + "/shaders/version1.sl", shaderName = "unversioned" )
		n = GafferRenderMan.RenderManShader()
		n.loadShader( shader1 )
		
		self.assertFalse( n["parameters"]["float1"].hasMinValue() )
		self.assertFalse( n["parameters"]["float1"].hasMaxValue() )
		self.assertEqual( n["parameters"]["string1"].defaultValue(), "" )
		
		nn = Gaffer.Node()
		nn["outFloat"] = Gaffer.FloatPlug( direction = Gaffer.Plug.Direction.Out )
		nn["outString"] = Gaffer.StringPlug( direction = Gaffer.Plug.Direction.Out )
		
		n["parameters"]["float1"].setInput( nn["outFloat"] )
		n["parameters"]["string1"].setInput( nn["outString"] )
		
		shader2 = self.compileShader( os.path.dirname( __file__ ) + "/shaders/version2.sl", shaderName = "unversioned" )
				
		GafferRenderMan.RenderManShader.shaderLoader().clear()
		n.loadShader( shader1, keepExistingValues=True )
		
		self.assertTrue( n["parameters"]["float1"].hasMinValue() )
		self.assertTrue( n["parameters"]["float1"].hasMaxValue() )
		self.assertEqual( n["parameters"]["float1"].minValue(), -1 )
		self.assertEqual( n["parameters"]["float1"].maxValue(), 2 )
		self.assertEqual( n["parameters"]["string1"].defaultValue(), "newDefaultValue" )
		
		self.assertTrue( n["parameters"]["float1"].getInput().isSame( nn["outFloat"] ) )
		self.assertTrue( n["parameters"]["string1"].getInput().isSame( nn["outString"] ) )

	def testReloadPreservesPartialConnectionsWhenMinMaxOrDefaultChanges( self ) :
	
		shader1 = self.compileShader( os.path.dirname( __file__ ) + "/shaders/version1.sl", shaderName = "unversioned" )
		n = GafferRenderMan.RenderManShader()
		n.loadShader( shader1 )
		
		nn = Gaffer.Node()
		nn["outFloat"] = Gaffer.FloatPlug( direction = Gaffer.Plug.Direction.Out )
		
		n["parameters"]["color1"][0].setInput( nn["outFloat"] )
		n["parameters"]["color1"][1].setInput( nn["outFloat"] )
		n["parameters"]["color1"][2].setValue( 0.75 )
		
		shader2 = self.compileShader( os.path.dirname( __file__ ) + "/shaders/version2.sl", shaderName = "unversioned" )
						
		GafferRenderMan.RenderManShader.shaderLoader().clear()
		n.loadShader( shader1, keepExistingValues=True )
	
		self.assertTrue( n["parameters"]["color1"][0].getInput().isSame( nn["outFloat"] ) )
		self.assertTrue( n["parameters"]["color1"][1].getInput().isSame( nn["outFloat"] ) )
		self.assertEqual( n["parameters"]["color1"][2].getValue(), 0.75 )
	
	def testReloadPreservesValuesWhenMinMaxOrDefaultChanges( self ) :
	
		shader1 = self.compileShader( os.path.dirname( __file__ ) + "/shaders/version1.sl", shaderName = "unversioned" )
		n = GafferRenderMan.RenderManShader()
		n.loadShader( shader1 )
		
		n["parameters"]["float1"].setValue( 0.25 )
		n["parameters"]["string1"].setValue( "dog" )
		n["parameters"]["color1"].setValue( IECore.Color3f( 0.1, 0.25, 0.5 ) )
		
		shader2 = self.compileShader( os.path.dirname( __file__ ) + "/shaders/version2.sl", shaderName = "unversioned" )
				
		GafferRenderMan.RenderManShader.shaderLoader().clear()
		n.loadShader( shader1, keepExistingValues=True )
		
		self.assertEqual( n["parameters"]["float1"].getValue(), 0.25 )
		self.assertEqual( n["parameters"]["string1"].getValue(), "dog" )
		self.assertEqual( n["parameters"]["color1"].getValue(), IECore.Color3f( 0.1, 0.25, 0.5 ) )
	
	def testOutputParameters( self ) :

		shader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/version3.sl" )
		n = GafferRenderMan.RenderManShader()
		n.loadShader( shader )
		
		self.failIf( "outputFloat" in n["parameters"].keys() )
	
	def testAssignmentDirtyPropagation( self ) :
	
		shader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/coshaderParameter.sl" )
		shaderNode = GafferRenderMan.RenderManShader()
		shaderNode.loadShader( shader )
				
		coshader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/coshader.sl" )
		coshaderNode = GafferRenderMan.RenderManShader()
		coshaderNode.loadShader( coshader )
		
		shaderNode["parameters"]["coshaderParameter"].setInput( coshaderNode["out"] )
		
		plane = GafferScene.Plane()
		assignment = GafferScene.ShaderAssignment()
		assignment["in"].setInput( plane["out"] )
		assignment["shader"].setInput( shaderNode["out"] )
		
		cs = GafferTest.CapturingSlot( assignment.plugDirtiedSignal() )
		
		coshaderNode["parameters"]["floatParameter"].setValue( 12 )
		
		dirtiedNames = [ x[0].fullName() for x in cs ]
		self.assertEqual( len( dirtiedNames ), 3 )
		self.assertEqual( dirtiedNames[0], "ShaderAssignment.shader" )
		self.assertEqual( dirtiedNames[1], "ShaderAssignment.out.attributes" )
		self.assertEqual( dirtiedNames[2], "ShaderAssignment.out" )
	
	def testArrayParameters( self ) :
	
		shader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/arrayParameters.sl" )
		n = GafferRenderMan.RenderManShader()
		n.loadShader( shader )
		
		expected = {
			"dynamicFloatArray" : IECore.FloatVectorData( [] ),
			"fixedFloatArray" : IECore.FloatVectorData( [ 1, 2, 3, 4 ] ),
			"dynamicStringArray" : IECore.StringVectorData( [ "dynamic", "arrays", "can", "still", "have", "defaults" ] ),
			"fixedStringArray" : IECore.StringVectorData( [ "hello", "goodbye" ] ),
			"dynamicColorArray" : IECore.Color3fVectorData( [ IECore.Color3f( 1 ), IECore.Color3f( 2 ) ] ),
			"fixedColorArray" : IECore.Color3fVectorData( [ IECore.Color3f( 1 ), IECore.Color3f( 2 ) ] ),
			"dynamicVectorArray" : IECore.V3fVectorData( [] ),
			"fixedVectorArray" : IECore.V3fVectorData( [ IECore.V3f( x ) for x in range( 1, 6 ) ] ),
			"dynamicPointArray" : IECore.V3fVectorData( [] ),
			"fixedPointArray" : IECore.V3fVectorData( [ IECore.V3f( x ) for x in range( 1, 6 ) ] ),
			"dynamicNormalArray" : IECore.V3fVectorData( [] ),
			"fixedNormalArray" : IECore.V3fVectorData( [ IECore.V3f( x ) for x in range( 1, 6 ) ] ),
		}
		
		self.assertEqual( set( n["parameters"].keys() ), set( expected.keys() ) )
		
		for name, value in expected.items() :
		
			self.assertEqual( n["parameters"][name].defaultValue(), value )
			self.assertEqual( n["parameters"][name].getValue(), value )
		
		s = n.state()[0]
		
		for name, value in expected.items() :
		
			self.assertEqual( s.parameters[name], value )
			
	def testFixedCoshaderArrayParameters( self ) :
	
		shader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/coshaderArrayParameters.sl" )
		n = GafferRenderMan.RenderManShader()
		n.loadShader( shader )
		
		self.assertEqual( n["parameters"].keys(), [ "dynamicShaderArray", "fixedShaderArray" ] )
		
		self.assertTrue( isinstance( n["parameters"]["fixedShaderArray"], Gaffer.CompoundPlug ) )
		
		self.assertEqual( len( n["parameters"]["fixedShaderArray"] ), 4 )
		self.assertTrue( isinstance( n["parameters"]["fixedShaderArray"]["in1"], Gaffer.Plug ) )
		self.assertTrue( isinstance( n["parameters"]["fixedShaderArray"]["in2"], Gaffer.Plug ) )
		self.assertTrue( isinstance( n["parameters"]["fixedShaderArray"]["in3"], Gaffer.Plug ) )
		self.assertTrue( isinstance( n["parameters"]["fixedShaderArray"]["in4"], Gaffer.Plug ) )
		
		state = n.state()
		
		self.assertEqual( state[0].parameters["fixedShaderArray"], IECore.StringVectorData( [ "" ] * 4 ) )

		coshader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/coshader.sl" )
		
		coshaderNode = GafferRenderMan.RenderManShader()
		coshaderNode.loadShader( coshader )
		
		n["parameters"]["fixedShaderArray"]["in1"].setInput( coshaderNode["out"] )
	
		state = n.state()
			
		self.assertEqual( state[1].parameters["fixedShaderArray"], IECore.StringVectorData( [ state[0].parameters["__handle"].value, "", "", "" ] ) )
	
	def testCoshaderType( self ) :
	
		coshader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/coshader.sl" )
		coshaderNode = GafferRenderMan.RenderManShader()
		coshaderNode.loadShader( coshader )
		
		self.assertEqual( coshaderNode.state()[0].type, "ri:shader" )
	
	def testCantConnectSurfaceShaderIntoCoshaderInput( self ) :
	
		shader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/coshaderParameter.sl" )
		n1 = GafferRenderMan.RenderManShader()
		n1.loadShader( shader )
		
		n2 = GafferRenderMan.RenderManShader()
		n2.loadShader( "plastic" )
		
		self.assertFalse( n1["parameters"]["coshaderParameter"].acceptsInput( n2["out"] ) )

		coshader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/coshader.sl" )
		n3 = GafferRenderMan.RenderManShader()
		n3.loadShader( coshader )

		self.assertTrue( n1["parameters"]["coshaderParameter"].acceptsInput( n3["out"] ) )
		
		arrayShader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/coshaderArrayParameters.sl" )
		n4 = GafferRenderMan.RenderManShader()
		n4.loadShader( arrayShader )
		
		self.assertFalse( n4["parameters"]["fixedShaderArray"]["in1"].acceptsInput( n2["out"] ) )
		self.assertTrue( n4["parameters"]["fixedShaderArray"]["in1"].acceptsInput( n3["out"] ) )
	
	def testConnectionsBetweenParameters( self ) :
	
		s = GafferRenderMan.RenderManShader()
		s.loadShader( "plastic" )
		
		s["parameters"]["Kd"].setValue( 0.25 )
		s["parameters"]["Ks"].setInput( s["parameters"]["Kd"] )
		
		shader = s.state()[0]
		
		self.assertEqual( shader.parameters["Kd"].value, 0.25 )
		self.assertEqual( shader.parameters["Ks"].value, 0.25 )

	def testFixedCoshaderArrayParameterHash( self ) :
	
		shader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/coshaderArrayParameters.sl" )
		n = GafferRenderMan.RenderManShader()
		n.loadShader( shader )
		
		h1 = n.stateHash()
		
		coshader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/coshader.sl" )
		coshaderNode = GafferRenderMan.RenderManShader()
		coshaderNode.loadShader( coshader )
		
		n["parameters"]["fixedShaderArray"]["in1"].setInput( coshaderNode["out"] )
	
		h2 = n.stateHash()
		self.assertNotEqual( h2, h1 )
		
		n["parameters"]["fixedShaderArray"]["in2"].setInput( coshaderNode["out"] )
		
		h3 = n.stateHash()
		self.assertNotEqual( h3, h2 )
		self.assertNotEqual( h3, h1 )

		n["parameters"]["fixedShaderArray"]["in2"].setInput( None )
		n["parameters"]["fixedShaderArray"]["in3"].setInput( coshaderNode["out"] )

		h4 = n.stateHash()
		self.assertNotEqual( h4, h3 )
		self.assertNotEqual( h4, h2 )
		self.assertNotEqual( h4, h1 )

	def testDisabling( self ) :
	
		s = GafferRenderMan.RenderManShader()
		s.loadShader( "plastic" )
				
		stateHash = s.stateHash()
		state = s.state()
		self.assertEqual( len( state ), 1 )
		self.assertEqual( state[0].name, "plastic" )
		
		self.assertTrue( s["enabled"].isSame( s.enabledPlug() ) )
						
		s["enabled"].setValue( False )
		
		stateHash2 = s.stateHash()
		self.assertNotEqual( stateHash2, stateHash )
		
		state2 = s.state()
		self.assertEqual( len( state2 ), 0 )

	def testDisablingCoshaders( self ) :
		
		shader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/coshaderParameter.sl" )
	
		shaderNode = GafferRenderMan.RenderManShader()
		shaderNode.loadShader( shader )
				
		coshader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/coshader.sl" )
		
		coshaderNode = GafferRenderMan.RenderManShader()
		coshaderNode.loadShader( coshader )
		
		shaderNode["parameters"]["coshaderParameter"].setInput( coshaderNode["out"] )
		
		s = shaderNode.state()
		self.assertEqual( len( s ), 2 )
		
		self.assertEqual( s[0].name, coshader )
		self.assertEqual( s[1].name, shader )
		
		h = shaderNode.stateHash()
		
		coshaderNode["enabled"].setValue( False )
		
		s2 = shaderNode.state()
		self.assertEqual( len( s2 ), 1 )
		
		self.assertEqual( s2[0].name, shader )
		self.assertTrue( "coshaderParameter" not in s2[0].parameters )
		
		self.assertNotEqual( shaderNode.stateHash(), h )	
	
	def testDisablingCoshaderArrayInputs( self ) :
	
		shader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/coshaderArrayParameters.sl" )
		n = GafferRenderMan.RenderManShader()
		n.loadShader( shader )
		
		coshader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/coshader.sl" )
		
		coshaderNode1 = GafferRenderMan.RenderManShader()
		coshaderNode1.loadShader( coshader )
		
		coshaderNode2 = GafferRenderMan.RenderManShader()
		coshaderNode2.loadShader( coshader )
			
		n["parameters"]["fixedShaderArray"]["in1"].setInput( coshaderNode1["out"] )
		n["parameters"]["fixedShaderArray"]["in3"].setInput( coshaderNode2["out"] )
	
		state = n.state()
		h1 = n.stateHash()
			
		self.assertEqual(
			state[2].parameters["fixedShaderArray"],
			IECore.StringVectorData( [
				state[0].parameters["__handle"].value,
				"",
				state[1].parameters["__handle"].value,
				""
			] )
		)
	
		coshaderNode1["enabled"].setValue( False )
		
		state = n.state()
			
		self.assertEqual(
			state[1].parameters["fixedShaderArray"],
			IECore.StringVectorData( [
				"",
				"",
				state[0].parameters["__handle"].value,
				""
			] )
		)
	
		h2 = n.stateHash()
		self.assertNotEqual( h2, h1 )

		coshaderNode2["enabled"].setValue( False )
		
		state = n.state()
			
		self.assertEqual(
			state[0].parameters["fixedShaderArray"],
			IECore.StringVectorData( [
				"",
				"",
				"",
				""
			] )
		)
	
		self.assertNotEqual( n.stateHash(), h1 )
		self.assertNotEqual( n.stateHash(), h2 )
	
	def testCorrespondingInput( self ) :
	
		coshader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/coshader.sl" )
		coshaderNode = GafferRenderMan.RenderManShader()
		coshaderNode.loadShader( coshader )
		self.assertEqual( coshaderNode.correspondingInput( coshaderNode["out"] ), None )
		
		coshader2 = self.compileShader( os.path.dirname( __file__ ) + "/shaders/coshaderWithPassThrough.sl" )
		coshaderNode2 = GafferRenderMan.RenderManShader()
		coshaderNode2.loadShader( coshader2 )
		self.assertTrue( coshaderNode2.correspondingInput( coshaderNode2["out"] ).isSame( coshaderNode2["parameters"]["aColorIWillTint"] ) )
	
	def testCoshaderPassThrough( self ) :
	
		shader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/coshaderParameter.sl" )
		shaderNode = GafferRenderMan.RenderManShader()
		shaderNode.loadShader( shader )
				
		passThroughCoshader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/coshaderWithPassThrough.sl" )
		passThroughCoshaderNode = GafferRenderMan.RenderManShader()
		passThroughCoshaderNode.loadShader( passThroughCoshader )
		
		coshader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/coshader.sl" )
		coshaderNode = GafferRenderMan.RenderManShader()
		coshaderNode.loadShader( coshader )

		shaderNode["parameters"]["coshaderParameter"].setInput( passThroughCoshaderNode["out"] )
		passThroughCoshaderNode["parameters"]["aColorIWillTint"].setInput( coshaderNode["out"] )
		
		h = shaderNode.stateHash()
		s = shaderNode.state()
		
		self.assertEqual( len( s ), 3 )
		self.assertEqual( s[2].parameters["coshaderParameter"], s[1].parameters["__handle"] )
		self.assertEqual( s[1].name, passThroughCoshader )
		self.assertEqual( s[1].parameters["aColorIWillTint"], s[0].parameters["__handle"] )
		self.assertEqual( s[0].name, coshader )
		
		passThroughCoshaderNode["enabled"].setValue( False )

		s = shaderNode.state()
		
		self.assertEqual( len( s ), 2 )
		self.assertEqual( s[1].parameters["coshaderParameter"], s[0].parameters["__handle"] )
		self.assertEqual( s[0].name, coshader )
	
	def testSplineParameters( self ) :
	
		shader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/splineParameters.sl" )
		n = GafferRenderMan.RenderManShader()
		n.loadShader( shader )
		
		self.assertEqual( n["parameters"].keys(), [ "floatSpline", "colorSpline", "colorSpline2" ] )
		
		self.assertTrue( isinstance( n["parameters"]["floatSpline"], Gaffer.SplineffPlug ) )
		self.assertTrue( isinstance( n["parameters"]["colorSpline"], Gaffer.SplinefColor3fPlug ) )
		
		self.assertEqual(
		
			n["parameters"]["floatSpline"].defaultValue(),
		
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
		
			n["parameters"]["colorSpline"].defaultValue(),
		
			IECore.SplinefColor3f(
				IECore.CubicBasisf.catmullRom(),
				[
					( 0, IECore.Color3f( 0 ) ),
					( 0, IECore.Color3f( 0 ) ),
					( 1, IECore.Color3f( 1 ) ),
					( 1, IECore.Color3f( 1 ) ),		
				]
			)
			
		)
		
		floatValue = IECore.Splineff(
			IECore.CubicBasisf.catmullRom(),
			[
				( 0, 0 ),
				( 0, 0 ),
				( 1, 2 ),
				( 1, 2 ),		
			]
		)
		
		colorValue = IECore.SplinefColor3f(
			IECore.CubicBasisf.catmullRom(),
			[
				( 0, IECore.Color3f( 0 ) ),
				( 0, IECore.Color3f( 0 ) ),
				( 1, IECore.Color3f( .5 ) ),
				( 1, IECore.Color3f( .5 ) ),			
			]
		)
		
		n["parameters"]["floatSpline"].setValue( floatValue )
		n["parameters"]["colorSpline"].setValue( colorValue )
		
		s = n.state()[0]
		
		self.assertEqual( s.parameters["floatSpline"].value, floatValue )
		self.assertEqual( s.parameters["colorSpline"].value, colorValue )
		
	def testSplineParameterSerialisationKeepsExistingValues( self ) :
	
		shader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/splineParameters.sl" )
		
		s = Gaffer.ScriptNode()
		s["n"] = GafferRenderMan.RenderManShader()
		s["n"].loadShader( shader )
		
		s["n"]["parameters"]["floatSpline"].setValue(
			IECore.Splineff(
				IECore.CubicBasisf.catmullRom(),
				[
					( 0, 0 ),
					( 0, 0 ),
					( 1, 2 ),
					( 1, 2 ),		
				]
			)
		)
		
		self.assertEqual(
			s["n"]["parameters"]["floatSpline"].getValue(),
			IECore.Splineff(
				IECore.CubicBasisf.catmullRom(),
				[
					( 0, 0 ),
					( 0, 0 ),
					( 1, 2 ),
					( 1, 2 ),		
				]
			),
		)
		
		ss = s.serialise()
		
		s2 = Gaffer.ScriptNode()
		s2.execute( ss )
		
		self.assertEqual(
			s2["n"]["parameters"]["floatSpline"].getValue(),
			IECore.Splineff(
				IECore.CubicBasisf.catmullRom(),
				[
					( 0, 0 ),
					( 0, 0 ),
					( 1, 2 ),
					( 1, 2 ),		
				]
			),
		)

	def testSplineParameterDefaultValueAnnotation( self ) :
		
		# because variable length parameters must be initialised
		# with a zero length array, we have to pass the defaults we actually
		# want via an annotation.
		
		shader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/splineParameters.sl" )
		
		n = GafferRenderMan.RenderManShader()
		n.loadShader( shader )
	
		self.assertEqual(
			n["parameters"]["colorSpline2"].getValue(),
			IECore.SplinefColor3f(
				IECore.CubicBasisf.catmullRom(),
				[
					( 0, IECore.Color3f( 1 ) ),
					( 0, IECore.Color3f( 1 ) ),
					( 0.5, IECore.Color3f( 1, 0.5, 0.25 ) ),
					( 1, IECore.Color3f( 0 ) ),
					( 1, IECore.Color3f( 0 ) ),		
				]
			),
		)
			
if __name__ == "__main__":
	unittest.main()
