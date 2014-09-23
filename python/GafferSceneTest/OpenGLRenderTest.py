##########################################################################
#
#  Copyright (c) 2013-2014, Image Engine Design Inc. All rights reserved.
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
import GafferImage
import GafferScene

@unittest.skipIf( "TRAVIS" in os.environ, "OpenGL not set up on Travis" )
class OpenGLRenderTest( unittest.TestCase ) :

	def test( self ) :

		self.assertFalse( os.path.exists( "/tmp/test.exr" ) )

		s = Gaffer.ScriptNode()

		s["plane"] = GafferScene.Plane()
		s["plane"]["transform"]["translate"].setValue( IECore.V3f( 0, 0, -5 ) )

		s["image"] = GafferImage.ImageReader()
		s["image"]["fileName"].setValue( os.path.expandvars( "$GAFFER_ROOT/python/GafferTest/images/checker.exr" ) )

		s["shader"] = GafferScene.OpenGLShader()
		s["shader"].loadShader( "Texture" )
		s["shader"]["parameters"]["texture"].setInput( s["image"]["out"] )
		s["shader"]["parameters"]["mult"].setValue( 1 )
		s["shader"]["parameters"]["tint"].setValue( IECore.Color4f( 1 ) )

		s["assignment"] = GafferScene.ShaderAssignment()
		s["assignment"]["in"].setInput( s["plane"]["out"] )
		s["assignment"]["shader"].setInput( s["shader"]["out"] )

		s["outputs"] = GafferScene.Outputs()
		s["outputs"].addOutput(
			"beauty",
			IECore.Display(
				"/tmp/test.exr",
				"exr",
				"rgba",
				{}
			)
		)
		s["outputs"]["in"].setInput( s["assignment"]["out"] )

		s["render"] = GafferScene.OpenGLRender()
		s["render"]["in"].setInput( s["outputs"]["out"] )

		s["fileName"].setValue( "/tmp/test.gfr" )
		s.save()

		s["render"].execute()

		self.assertTrue( os.path.exists( "/tmp/test.exr" ) )

		i = IECore.EXRImageReader( "/tmp/test.exr" ).read()
		e = IECore.ImagePrimitiveEvaluator( i )
		r = e.createResult()
		e.pointAtUV( IECore.V2f( 0.5 ), r )
		self.assertAlmostEqual( r.floatPrimVar( e.R() ), 0.666666, 5 )
		self.assertAlmostEqual( r.floatPrimVar( e.G() ), 0.666666, 5 )
		self.assertEqual( r.floatPrimVar( e.B() ), 0 )

	def testOutputDirectoryCreation( self ) :

		s = Gaffer.ScriptNode()
		s["variables"].addMember( "renderDirectory", "/tmp/openGLRenderTest" )

		s["plane"] = GafferScene.Plane()

		s["outputs"] = GafferScene.Outputs()
		s["outputs"]["in"].setInput( s["plane"]["out"] )
		s["outputs"].addOutput(
			"beauty",
			IECore.Display(
				"$renderDirectory/test.####.exr",
				"exr",
				"rgba",
				{}
			)
		)

		s["render"] = GafferScene.OpenGLRender()
		s["render"]["in"].setInput( s["outputs"]["out"] )

		self.assertFalse( os.path.exists( "/tmp/openGLRenderTest" ) )
		self.assertFalse( os.path.exists( "/tmp/openGLRenderTest/test.0001.exr" ) )

		s["fileName"].setValue( "/tmp/test.gfr" )

		with s.context() :
			s["render"].execute()

		self.assertTrue( os.path.exists( "/tmp/openGLRenderTest" ) )
		self.assertTrue( os.path.exists( "/tmp/openGLRenderTest/test.0001.exr" ) )

	def testHash( self ) :

		c = Gaffer.Context()
		c.setFrame( 1 )
		c2 = Gaffer.Context()
		c2.setFrame( 2 )

		s = Gaffer.ScriptNode()
		s["plane"] = GafferScene.Plane()
		s["outputs"] = GafferScene.Outputs()
		s["outputs"]["in"].setInput( s["plane"]["out"] )
		s["outputs"].addOutput( "beauty", IECore.Display( "$renderDirectory/test.####.exr", "exr", "rgba", {} ) )
		s["render"] = GafferScene.OpenGLRender()

		# no input scene produces no effect
		self.assertEqual( s["render"].hash( c ), IECore.MurmurHash() )

		# now theres an scene to render, we get some output
		s["render"]["in"].setInput( s["outputs"]["out"] )
		self.assertNotEqual( s["render"].hash( c ), IECore.MurmurHash() )

		# output varies by time
		self.assertNotEqual( s["render"].hash( c ), s["render"].hash( c2 ) )

		# output varies by new Context entries
		current = s["render"].hash( c )
		c["renderDirectory"] = "/tmp/openGLRenderTest"
		self.assertNotEqual( s["render"].hash( c ), current )

		# output varies by changed Context entries
		current = s["render"].hash( c )
		c["renderDirectory"] = "/tmp/openGLRenderTest2"
		self.assertNotEqual( s["render"].hash( c ), current )

		# output doesn't vary by ui Context entries
		current = s["render"].hash( c )
		c["ui:something"] = "alterTheUI"
		self.assertEqual( s["render"].hash( c ), current )

		# also varies by input node
		current = s["render"].hash( c )
		s["render"]["in"].setInput( s["plane"]["out"] )
		self.assertNotEqual( s["render"].hash( c ), current )

	def setUp( self ) :

		for f in (
			"/tmp/test.exr",
			"/tmp/test.gfr",
			"/tmp/openGLRenderTest/test.0001.exr",
			"/tmp/openGLRenderTest",
		) :
			if os.path.isfile( f ) :
				os.remove( f )
			elif os.path.isdir( f ) :
				os.rmdir( f )

	def tearDown( self ) :

		self.setUp()

if __name__ == "__main__":
	unittest.main()
