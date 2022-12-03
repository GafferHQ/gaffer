##########################################################################
#
#  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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

import pathlib
import unittest

import IECore
import IECoreScene

import Gaffer
import GafferScene
import GafferSceneTest
import GafferDelight

class DelightRenderTest( GafferSceneTest.SceneTestCase ) :

	def testSceneDescriptionMode( self ) :

		plane = GafferScene.Plane()
		render = GafferDelight.DelightRender()
		render["in"].setInput( plane["out"] )
		render["mode"].setValue( render.Mode.SceneDescriptionMode )
		render["fileName"].setValue( self.temporaryDirectory() / "test.nsi" )

		render["task"].execute()
		self.assertTrue( pathlib.Path( render["fileName"].getValue() ).exists() )

	def testRenderMode( self ) :

		plane = GafferScene.Plane()

		outputs = GafferScene.Outputs()
		outputs.addOutput(
			"beauty",
			IECoreScene.Output(
				str( self.temporaryDirectory() / "test.exr" ),
				"exr",
				"rgba",
				{}
			)
		)

		render = GafferDelight.DelightRender()
		render["in"].setInput( outputs["out"] )
		render["mode"].setValue( render.Mode.RenderMode )

		render["task"].execute()
		self.assertTrue( ( self.temporaryDirectory() / "test.exr" ).exists() )

	def testSceneTranslationOnly( self ) :

		plane = GafferScene.Plane()

		outputs = GafferScene.Outputs()
		outputs.addOutput(
			"beauty",
			IECoreScene.Output(
				str( self.temporaryDirectory() / "test.exr" ),
				"exr",
				"rgba",
				{}
			)
		)

		render = GafferDelight.DelightRender()
		render["in"].setInput( outputs["out"] )
		render["mode"].setValue( render.Mode.RenderMode )

		with Gaffer.Context() as context :
			context["scene:render:sceneTranslationOnly"] = IECore.BoolData( True )
			render["task"].execute()

		self.assertFalse( ( self.temporaryDirectory() / "test.exr" ).exists() )

if __name__ == "__main__":
	unittest.main()
