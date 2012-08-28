##########################################################################
#  
#  Copyright (c) 2012, John Haddon. All rights reserved.
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
import GafferArnold

class ArnoldShaderTest( unittest.TestCase ) :

	def test( self ) :
	
		n = GafferArnold.ArnoldShader()
		n.setShader( "noise" )
		
	def testState( self ) :
	
		n = GafferArnold.ArnoldShader()
		n.setShader( "utility" )
		
		s = n.state()
		self.failUnless( isinstance( s, IECore.ObjectVector ) )
		self.assertEqual( len( s ), 1 )
		self.failUnless( isinstance( s[0], IECore.Shader ) )
		
		s = s[0]
		self.assertEqual( s.name, "utility" )
		
	def testParameterRepresentation( self ) :
	
		n = GafferArnold.ArnoldShader()
		n.setShader( "wireframe" )
		
		self.failUnless( isinstance( n["parameters"]["line_width"], Gaffer.FloatPlug ) )
		self.failUnless( isinstance( n["parameters"]["fill_color"], Gaffer.Color3fPlug ) )
		self.failUnless( isinstance( n["parameters"]["line_color"], Gaffer.Color3fPlug ) )
		self.failUnless( isinstance( n["parameters"]["raster_space"], Gaffer.BoolPlug ) )
		self.failUnless( isinstance( n["parameters"]["edge_type"], Gaffer.StringPlug ) )
		self.failIf( "name" in n["parameters"] )
		
	def testParameterUse( self ) :
	
		n = GafferArnold.ArnoldShader()
		n.setShader( "wireframe" )
		
		n["parameters"]["line_width"].setValue( 10 )
		n["parameters"]["fill_color"].setValue( IECore.Color3f( .25, .5, 1 ) )
		n["parameters"]["raster_space"].setValue( False )
		n["parameters"]["edge_type"].setValue( "polygons" )
	
		s = n.state()[0]
		self.assertEqual( s.parameters["line_width"], IECore.FloatData( 10 ) )
		self.assertEqual( s.parameters["fill_color"], IECore.Color3fData( IECore.Color3f( .25, .5, 1 ) ) )
		self.assertEqual( s.parameters["line_color"], IECore.Color3fData( IECore.Color3f( 0 ) ) )
		self.assertEqual( s.parameters["raster_space"], IECore.BoolData( False ) )
		self.assertEqual( s.parameters["edge_type"], IECore.StringData( "polygons" ) )
	
	def testSerialisation( self ) :
	
		s = Gaffer.ScriptNode()
		s["n"] = GafferArnold.ArnoldShader()
		s["n"].setShader( "wireframe" )
		
		ss = s.serialise()
		
		s = Gaffer.ScriptNode()
		s.execute( ss )
		
		self.failUnless( isinstance( s["n"]["parameters"]["line_width"], Gaffer.FloatPlug ) )
		self.failUnless( isinstance( s["n"]["parameters"]["fill_color"], Gaffer.Color3fPlug ) )
		self.failUnless( isinstance( s["n"]["parameters"]["line_color"], Gaffer.Color3fPlug ) )
		self.failUnless( isinstance( s["n"]["parameters"]["raster_space"], Gaffer.BoolPlug ) )
		self.failUnless( isinstance( s["n"]["parameters"]["edge_type"], Gaffer.StringPlug ) )
	
	def testHash( self ) :
	
		n = GafferArnold.ArnoldShader()
		h = n.stateHash()
		
		n.setShader( "noise" )
		h2 = n.stateHash()
		
		self.assertNotEqual( h, h2 )
		
		n["parameters"]["octaves"].setValue( 10 )
		h3 = n.stateHash()
		
		self.assertNotEqual( h2, h3 )
		
if __name__ == "__main__":
	unittest.main()
