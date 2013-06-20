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

import IECore
import IECoreGL

import Gaffer
import GafferTest
import GafferImage
import GafferScene
import GafferSceneTest

class OpenGLShaderTest( GafferSceneTest.SceneTestCase ) :
	
	def test( self ) :
				
		s = GafferScene.OpenGLShader()
		s.loadShader( "texture" )
		
		self.assertEqual( len( s["parameters"] ), 3 )
		self.assertTrue( isinstance( s["parameters"]["mult"], Gaffer.FloatPlug ) )
		self.assertTrue( isinstance( s["parameters"]["tint"], Gaffer.Color4fPlug ) )
		self.assertTrue( isinstance( s["parameters"]["texture"], GafferImage.ImagePlug ) )
		
		s["parameters"]["mult"].setValue( 0.5 )
		s["parameters"]["tint"].setValue( IECore.Color4f( 1, 0.5, 0.25, 1 ) )
		
		i = GafferImage.ImageReader()
		i["fileName"].setValue( os.path.expandvars( "$GAFFER_ROOT/python/GafferTest/images/checker.exr" ) )
		s["parameters"]["texture"].setInput( i["out"] )
		
		ss = s.state()
		self.assertEqual( len( ss ), 1 )
		self.failUnless( isinstance( ss[0], IECore.Shader ) )
		
		self.assertEqual( ss[0].name, "texture" )
		self.assertEqual( ss[0].type, "gl:surface" )
		self.assertEqual( ss[0].parameters["mult"], IECore.FloatData( 0.5 ) )
		self.assertEqual( ss[0].parameters["tint"].value, IECore.Color4f( 1, 0.5, 0.25, 1 ) )
		self.assertTrue( isinstance( ss[0].parameters["texture"], IECore.CompoundData ) )
		self.failUnless( "displayWindow" in ss[0].parameters["texture"] )
		self.failUnless( "dataWindow" in ss[0].parameters["texture"] )
		self.failUnless( "channels" in ss[0].parameters["texture"] )
	
	def testDirtyPropagation( self ) :
	
		s = GafferScene.OpenGLShader()
		s.loadShader( "texture" )
		
		i = GafferImage.Constant()
		s["parameters"]["texture"].setInput( i["out"] )
		
		cs = GafferTest.CapturingSlot( s.plugDirtiedSignal() )
		
		i["color"]["r"].setValue( 0.1 )
		
		self.assertTrue( "OpenGLShader.out" in [ x[0].fullName() for x in cs ] )
	
	def testHash( self ) :
	
		s = GafferScene.OpenGLShader()
		s.loadShader( "texture" )
		
		h1 = s.stateHash()
		
		i = GafferImage.Constant()
		s["parameters"]["texture"].setInput( i["out"] )
		
		h2 = s.stateHash()
		self.assertNotEqual( h2, h1 )
		
		i["color"].setValue( IECore.Color4f( 1, 0, 1, 0 ) )

		h3 = s.stateHash()
		self.assertNotEqual( h3, h2 )
		self.assertNotEqual( h3, h1 )
		
if __name__ == "__main__":
	unittest.main()
