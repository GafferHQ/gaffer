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
import imath

import IECore
import IECoreScene

import Gaffer
import GafferTest
import GafferImage
import GafferScene
import GafferSceneTest

@unittest.skipIf( GafferTest.inCI(), "OpenGL not set up" )
class OpenGLRenderTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		self.assertFalse( os.path.exists( self.temporaryDirectory() + "/test.exr" ) )

		s = Gaffer.ScriptNode()

		s["plane"] = GafferScene.Plane()
		s["plane"]["transform"]["translate"].setValue( imath.V3f( 0, 0, -5 ) )

		s["image"] = GafferImage.ImageReader()
		s["image"]["fileName"].setValue( os.path.expandvars( "$GAFFER_ROOT/python/GafferImageTest/images/checker.exr" ) )

		s["shader"] = GafferScene.OpenGLShader()
		s["shader"].loadShader( "Texture" )
		s["shader"]["parameters"]["texture"].setInput( s["image"]["out"] )
		s["shader"]["parameters"]["mult"].setValue( 1 )
		s["shader"]["parameters"]["tint"].setValue( imath.Color4f( 1 ) )

		s["assignment"] = GafferScene.ShaderAssignment()
		s["assignment"]["in"].setInput( s["plane"]["out"] )
		s["assignment"]["shader"].setInput( s["shader"]["out"] )

		s["outputs"] = GafferScene.Outputs()
		s["outputs"].addOutput(
			"beauty",
			IECoreScene.Output(
				self.temporaryDirectory() + "/test.exr",
				"exr",
				"rgba",
				{}
			)
		)
		s["outputs"]["in"].setInput( s["assignment"]["out"] )

		s["render"] = GafferScene.OpenGLRender()
		s["render"]["in"].setInput( s["outputs"]["out"] )

		s["fileName"].setValue( self.temporaryDirectory() + "/test.gfr" )
		s.save()

		s["render"]["task"].execute()

		self.assertTrue( os.path.exists( self.temporaryDirectory() + "/test.exr" ) )

		imageReader = GafferImage.ImageReader()
		imageReader["fileName"].setValue( self.temporaryDirectory() + "/test.exr" )

		imageSampler = GafferImage.ImageSampler()
		imageSampler["image"].setInput( imageReader["out"] )
		imageSampler["pixel"].setValue( imath.V2f( 320, 240 ) )

		self.assertAlmostEqual( imageSampler["color"]["r"].getValue(), 0.666666, delta = 0.001 )
		self.assertAlmostEqual( imageSampler["color"]["g"].getValue(), 0.666666, delta = 0.001 )
		self.assertEqual( imageSampler["color"]["b"].getValue(), 0 )

	def testOutputDirectoryCreation( self ) :

		s = Gaffer.ScriptNode()
		s["variables"].addChild( Gaffer.NameValuePlug( "renderDirectory", self.temporaryDirectory() + "/openGLRenderTest" ) )

		s["plane"] = GafferScene.Plane()

		s["outputs"] = GafferScene.Outputs()
		s["outputs"]["in"].setInput( s["plane"]["out"] )
		s["outputs"].addOutput(
			"beauty",
			IECoreScene.Output(
				"$renderDirectory/test.####.exr",
				"exr",
				"rgba",
				{}
			)
		)

		s["render"] = GafferScene.OpenGLRender()
		s["render"]["in"].setInput( s["outputs"]["out"] )

		self.assertFalse( os.path.exists( self.temporaryDirectory() + "/openGLRenderTest" ) )
		self.assertFalse( os.path.exists( self.temporaryDirectory() + "/openGLRenderTest/test.0001.exr" ) )

		with s.context() :
			s["render"]["task"].execute()

		self.assertTrue( os.path.exists( self.temporaryDirectory() + "/openGLRenderTest" ) )
		self.assertTrue( os.path.exists( self.temporaryDirectory() + "/openGLRenderTest/test.0001.exr" ) )

	def testHash( self ) :

		c = Gaffer.Context()
		c.setFrame( 1 )
		c2 = Gaffer.Context()
		c2.setFrame( 2 )

		s = Gaffer.ScriptNode()
		s["plane"] = GafferScene.Plane()
		s["outputs"] = GafferScene.Outputs()
		s["outputs"]["in"].setInput( s["plane"]["out"] )
		s["outputs"].addOutput( "beauty", IECoreScene.Output( "$renderDirectory/test.####.exr", "exr", "rgba", {} ) )
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
		c["renderDirectory"] = self.temporaryDirectory() + "/openGLRenderTest"
		self.assertNotEqual( s["render"].hash( c ), current )

		# output varies by changed Context entries
		current = s["render"].hash( c )
		c["renderDirectory"] = self.temporaryDirectory() + "/openGLRenderTest2"
		self.assertNotEqual( s["render"].hash( c ), current )

		# output doesn't vary by ui Context entries
		current = s["render"].hash( c )
		c["ui:something"] = "alterTheUI"
		self.assertEqual( s["render"].hash( c ), current )

		# also varies by input node
		current = s["render"].hash( c )
		s["render"]["in"].setInput( s["plane"]["out"] )
		self.assertNotEqual( s["render"].hash( c ), current )

if __name__ == "__main__":
	unittest.main()
