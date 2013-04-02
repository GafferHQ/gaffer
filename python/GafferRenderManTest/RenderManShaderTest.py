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
import GafferRenderMan
import GafferRenderManTest

class RenderManShaderTest( GafferRenderManTest.RenderManTestCase ) :

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
		
if __name__ == "__main__":
	unittest.main()
