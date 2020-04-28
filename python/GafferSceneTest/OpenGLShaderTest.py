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
import sys
import unittest
import imath
import inspect

import IECore
import IECoreScene
import IECoreGL

import Gaffer
import GafferTest
import GafferImage
import GafferScene
import GafferSceneTest

@unittest.skipIf( GafferTest.inCI(), "OpenGL not set up" )
class OpenGLShaderTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		s = GafferScene.OpenGLShader()
		s.loadShader( "Texture" )

		self.assertEqual( len( s["parameters"] ), 3 )
		self.assertTrue( isinstance( s["parameters"]["mult"], Gaffer.FloatPlug ) )
		self.assertTrue( isinstance( s["parameters"]["tint"], Gaffer.Color4fPlug ) )
		self.assertTrue( isinstance( s["parameters"]["texture"], GafferImage.ImagePlug ) )

		s["parameters"]["mult"].setValue( 0.5 )
		s["parameters"]["tint"].setValue( imath.Color4f( 1, 0.5, 0.25, 1 ) )

		i = GafferImage.ImageReader()
		i["fileName"].setValue( os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/checker.exr" ) )
		s["parameters"]["texture"].setInput( i["out"] )

		a = s.attributes()
		self.assertEqual( a.keys(), [ "gl:surface"] )
		self.assertIsInstance( a["gl:surface"].outputShader(), IECoreScene.Shader )

		self.assertEqual( a["gl:surface"].outputShader().name, "Texture" )
		self.assertEqual( a["gl:surface"].outputShader().type, "gl:surface" )
		self.assertEqual( a["gl:surface"].outputShader().parameters["mult"], IECore.FloatData( 0.5 ) )
		self.assertEqual( a["gl:surface"].outputShader().parameters["tint"].value, imath.Color4f( 1, 0.5, 0.25, 1 ) )
		self.assertTrue( isinstance( a["gl:surface"].outputShader().parameters["texture"], IECore.CompoundData ) )
		self.assertIn( "displayWindow", a["gl:surface"].outputShader().parameters["texture"] )
		self.assertIn( "dataWindow", a["gl:surface"].outputShader().parameters["texture"] )
		self.assertIn( "channels", a["gl:surface"].outputShader().parameters["texture"] )

	def testDirtyPropagation( self ) :

		s = GafferScene.OpenGLShader()
		s.loadShader( "Texture" )

		i = GafferImage.Constant()
		s["parameters"]["texture"].setInput( i["out"] )

		cs = GafferTest.CapturingSlot( s.plugDirtiedSignal() )

		i["color"]["r"].setValue( 0.1 )

		self.assertTrue( "OpenGLShader.out" in [ x[0].fullName() for x in cs ] )

	def testHash( self ) :

		s = GafferScene.OpenGLShader()
		s.loadShader( "Texture" )

		h1 = s.attributesHash()

		i = GafferImage.Constant()
		i["format"].setValue( GafferImage.Format( 100, 100, 1 ) )
		s["parameters"]["texture"].setInput( i["out"] )

		h2 = s.attributesHash()
		self.assertNotEqual( h2, h1 )

		i["color"].setValue( imath.Color4f( 1, 0, 1, 0 ) )

		h3 = s.attributesHash()
		self.assertNotEqual( h3, h2 )
		self.assertNotEqual( h3, h1 )

	def testLoadShader( self ) :

		s = GafferScene.OpenGLShader()
		s.loadShader( "Texture" )
		self.assertEqual( s["parameters"].keys(), ['mult', 'texture', 'tint'] )
		s["parameters"]["mult"].setValue( 3 )

		s.loadShader( "Texture", keepExistingValues = True )
		self.assertEqual( s["parameters"].keys(), ['mult', 'texture', 'tint'] )
		self.assertEqual( s["parameters"]["mult"].getValue(), 3 )

		s.loadShader( "Texture" )
		self.assertEqual( s["parameters"].keys(), ['mult', 'texture', 'tint'] )

		# By default we don't keep existing values
		self.assertEqual( s["parameters"]["mult"].getValue(), 0 )

	def testSerialisation( self ) :

		s = Gaffer.ScriptNode()
		s["shader"] = GafferScene.OpenGLShader()
		s["shader"].loadShader( "Constant" )

		self.assertEqual(
			s["shader"].attributes()["gl:surface"].outputShader().name,
			"Constant"
		)

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( s2["shader"].attributes(), s["shader"].attributes() )

	def testGLSLSourceParameters( self ) :

		vertSource = inspect.cleandoc(
			'''
			void main()
			{
				gl_Position = vec4( 1 );
			}
			'''
		)

		geomSource = inspect.cleandoc(
			'''
			layout(points) in;
			layout(points, max_vertices = 1) out;

			void main()
			{
				gl_Position = gl_in[0].gl_Position;
				EmitVertex();
				EndPrimitive();
			}
			'''
		)

		fragSource = inspect.cleandoc(
			'''
			void main()
			{
				gl_FragColor = vec4( 1 );
			}
			'''
		)

		s = GafferScene.OpenGLShader()
		s["name"].setValue( "testSource" )
		s["type"].setValue( "gl:surface" )
		s["parameters"].addChild( Gaffer.StringPlug( "glVertexSource", defaultValue = vertSource ) )
		s["parameters"].addChild( Gaffer.StringPlug( "glGeometrySource", defaultValue = geomSource ) )
		s["parameters"].addChild( Gaffer.StringPlug( "glFragmentSource", defaultValue = fragSource ) )
		s["parameters"].addChild( Gaffer.StringPlug( "glNotAThing", defaultValue = "this isnt glsl" ) )

		ss = s.attributes()["gl:surface"].outputShader()
		self.assertEqual( set(ss.parameters.keys()), set(['gl:vertexSource', 'gl:geometrySource', 'gl:fragmentSource', 'glNotAThing']) )
		self.assertEqual( ss.parameters["gl:vertexSource"].value, vertSource )
		self.assertEqual( ss.parameters["gl:geometrySource"].value, geomSource )
		self.assertEqual( ss.parameters["gl:fragmentSource"].value, fragSource )
		self.assertEqual( ss.parameters["glNotAThing"].value, "this isnt glsl" )

if sys.platform == "darwin" :
	# The Texture shader used in the test provides only a .frag file, which
	# means that it gets the default vertex shader. The default vertex shader
	# declares a "Cs" parameter which for some reason the OSX shader compiler
	# fails to optimise out (it is not used in the fragment shader, so it should
	# be). This means we end up with an unexpected shader parameter and the test
	# fails. Since the issue is in the shader compiler itself, it seems there's
	# not much we can do (other than provide a .vert shader with the unnecessary
	# bit omitted), so for now we mark the test as an expected failure.
	OpenGLShaderTest.test = unittest.expectedFailure( OpenGLShaderTest.test )
	OpenGLShaderTest.testLoadShader = unittest.expectedFailure( OpenGLShaderTest.testLoadShader )

if __name__ == "__main__":
	unittest.main()
