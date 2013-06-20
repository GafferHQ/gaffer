##########################################################################
#  
#  Copyright (c) 2012, John Haddon. All rights reserved.
#  Copyright (c) 2012-2013, Image Engine Design Inc. All rights reserved.
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

import IECore

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest

class ShaderAssignmentTest( unittest.TestCase ) :

	def testFilter( self ) :
	
		sphere = IECore.SpherePrimitive()
		input = GafferSceneTest.CompoundObjectSource()
		input["in"].setValue(
			IECore.CompoundObject( {
				"bound" : IECore.Box3fData( sphere.bound() ),
				"children" : {
					"ball1" : {
						"object" : sphere,
						"bound" : IECore.Box3fData( sphere.bound() ),
					},
					"ball2" : {
						"object" : sphere,
						"bound" : IECore.Box3fData( sphere.bound() ),
					},
				},
			} )
		)
	
		a = GafferScene.ShaderAssignment()
		a["in"].setInput( input["out"] )
		
		s = GafferSceneTest.TestShader()
		a["shader"].setInput( s["out"] )
		
		f = GafferScene.PathFilter()
		f["paths"].setValue( IECore.StringVectorData( [ "/ball1" ] ) )
		a["filter"].setInput( f["match"] )
		
		self.assertEqual( a["out"].attributes( "/" ), IECore.CompoundObject() )
		self.assertNotEqual( a["out"].attributes( "/ball1" ), IECore.CompoundObject() )
		self.assertEqual( a["out"].attributes( "/ball2" ), IECore.CompoundObject() )		
	
	def testFilterInputAcceptance( self ) :
	
		a = GafferScene.ShaderAssignment()
		
		f = GafferScene.PathFilter()
		self.assertTrue( a["filter"].acceptsInput( f["match"] ) )
		
		n = GafferTest.AddNode()
		self.assertFalse( a["filter"].acceptsInput( n["sum"] ) )
		
		p = Gaffer.IntPlug()
		p.setInput( f["match"] )
		
		self.assertTrue( a["filter"].acceptsInput( p ) )
	
	def testAssignShaderFromOutsideBox( self ) :
	
		s = Gaffer.ScriptNode()
		
		s["p"] = GafferScene.Plane()
		s["s"] = GafferSceneTest.TestShader()
		s["a"] = GafferScene.ShaderAssignment()
		s["a"]["in"].setInput( s["p"]["out"] )
		s["a"]["shader"].setInput( s["s"]["out"] )
		
		s["o"] = GafferScene.Options()
		s["o"]["in"].setInput( s["a"]["out"] )
		
		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["p"], s["a"] ] ) )
		
		self.assertTrue( "shader" in s["o"]["out"].attributes( "/plane" ) )
		
		ss = s.serialise()
				
		s = Gaffer.ScriptNode()
		s.execute( ss )
		
		self.assertTrue( s["Box"]["a"]["shader"].getInput().isSame( s["Box"]["in"] ) )
	
	def testDisabled( self ) :
	
		s = Gaffer.ScriptNode()

		s["p"] = GafferScene.Plane()
		s["s"] = GafferSceneTest.TestShader()
		s["a"] = GafferScene.ShaderAssignment()
		s["a"]["in"].setInput( s["p"]["out"] )
		s["a"]["shader"].setInput( s["s"]["out"] )
		
		self.assertTrue( "shader" in s["a"]["out"].attributes( "/plane" ) )		
		
		s["a"]["enabled"].setValue( False )
		
		self.assertTrue( "shader" not in s["a"]["out"].attributes( "/plane" ) )		
	
	def testAssignDisabledShader( self ) :
	
		s = Gaffer.ScriptNode()

		s["p"] = GafferScene.Plane()
		
		s["s"] = GafferSceneTest.TestShader()
		s["s"]["name"].setValue( "test" )
		
		s["a"] = GafferScene.ShaderAssignment()
		s["a"]["in"].setInput( s["p"]["out"] )
		s["a"]["shader"].setInput( s["s"]["out"] )
		
		self.assertTrue( "shader" in s["a"]["out"].attributes( "/plane" ) )
		self.assertEqual( s["a"]["out"].attributes( "/plane" )["shader"][-1].name, "test" )
			
		s["s2"] = GafferSceneTest.TestShader()
		s["s2"]["name"].setValue( "test2" )
	
		s["a2"] = GafferScene.ShaderAssignment()
		s["a2"]["in"].setInput( s["a"]["out"] )
		s["a2"]["shader"].setInput( s["s2"]["out"] )
		
		self.assertTrue( "shader" in s["a"]["out"].attributes( "/plane" ) )
		self.assertEqual( s["a2"]["out"].attributes( "/plane" )["shader"][-1].name, "test2" )
		
		s["s2"]["enabled"].setValue( False )
		
		self.assertTrue( "shader" in s["a"]["out"].attributes( "/plane" ) )
		self.assertEqual( s["a2"]["out"].attributes( "/plane" )["shader"][-1].name, "test" )
		
if __name__ == "__main__":
	unittest.main()
