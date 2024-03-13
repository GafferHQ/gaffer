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
import pathlib
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
class OpenGLRenderTest( GafferSceneTest.RenderTest ) :

	renderer = "OpenGL"

	def testTextureFromImagePlug( self ) :

		self.assertFalse( ( self.temporaryDirectory() / "test.exr" ).exists() )

		s = Gaffer.ScriptNode()

		s["plane"] = GafferScene.Plane()
		s["plane"]["transform"]["translate"].setValue( imath.V3f( 0, 0, -5 ) )

		s["image"] = GafferImage.ImageReader()
		s["image"]["fileName"].setValue( pathlib.Path( os.environ["GAFFER_ROOT"] ) / "python" / "GafferImageTest" / "images" / "checker.exr" )

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
				( self.temporaryDirectory() / "test.exr" ).as_posix(),
				"exr",
				"rgba",
				{}
			)
		)
		s["outputs"]["in"].setInput( s["assignment"]["out"] )

		s["render"] = GafferScene.OpenGLRender()
		s["render"]["in"].setInput( s["outputs"]["out"] )

		s["fileName"].setValue( self.temporaryDirectory() / "test.gfr" )
		s.save()

		s["render"]["task"].execute()

		self.assertTrue( ( self.temporaryDirectory() / "test.exr" ).exists() )

		imageReader = GafferImage.ImageReader()
		imageReader["fileName"].setValue( self.temporaryDirectory() / "test.exr" )

		imageSampler = GafferImage.ImageSampler()
		imageSampler["image"].setInput( imageReader["out"] )
		imageSampler["pixel"].setValue( imath.V2f( 320, 240 ) )

		self.assertAlmostEqual( imageSampler["color"]["r"].getValue(), 0.666666, delta = 0.001 )
		self.assertAlmostEqual( imageSampler["color"]["g"].getValue(), 0.666666, delta = 0.001 )
		self.assertEqual( imageSampler["color"]["b"].getValue(), 0 )

if __name__ == "__main__":
	unittest.main()
