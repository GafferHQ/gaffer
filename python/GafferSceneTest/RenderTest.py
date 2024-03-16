##########################################################################
#
#  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
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
import subprocess
import unittest

import IECore
import IECoreScene

import Gaffer
import GafferScene
import GafferSceneTest

## \todo Transfer more tests from subclasses to this base class, so that we
# run them for all renderers.
class RenderTest( GafferSceneTest.SceneTestCase ) :

	# Derived classes should set `renderer` to the name of the renderer
	# to be tested.
	renderer = None
	# And set this to the file extension used for scene description, if
	# scene description is supported.
	sceneDescriptionSuffix = None

	@classmethod
	def setUpClass( cls ) :

		GafferSceneTest.SceneTestCase.setUpClass()

		if cls.renderer is None :
			# We expect derived classes to set the renderer, and will
			# run the tests there.
			raise unittest.SkipTest( "No renderer available" )

	def testOutputDirectoryCreation( self ) :

		s = Gaffer.ScriptNode()
		s["variables"].addChild( Gaffer.NameValuePlug( "renderDirectory", ( self.temporaryDirectory() / "renderTest" ).as_posix() ) )

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

		s["render"] = GafferScene.Render()
		s["render"]["renderer"].setValue( self.renderer )
		s["render"]["in"].setInput( s["outputs"]["out"] )

		self.assertFalse( ( self.temporaryDirectory() / "renderTest" ).exists() )
		self.assertFalse( ( self.temporaryDirectory() / "renderTest" / "test.0001.exr" ).exists() )

		for i in range( 0, 2 ) : # Test twice, to check we can cope with the directory already existing.

			with s.context() :
				s["render"]["task"].execute()

			self.assertTrue( ( self.temporaryDirectory() / "renderTest" ).exists() )
			self.assertTrue( ( self.temporaryDirectory() / "renderTest" / "test.0001.exr" ).exists() )

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
		s["render"] = GafferScene.Render()
		s["render"]["renderer"].setValue( self.renderer )

		# no input scene produces no effect
		self.assertEqual( s["render"].hash( c ), IECore.MurmurHash() )

		# now theres an scene to render, we get some output
		s["render"]["in"].setInput( s["outputs"]["out"] )
		self.assertNotEqual( s["render"].hash( c ), IECore.MurmurHash() )

		# output varies by time
		self.assertNotEqual( s["render"].hash( c ), s["render"].hash( c2 ) )

		# output varies by new Context entries
		current = s["render"].hash( c )
		c["renderDirectory"] = ( self.temporaryDirectory() / "renderTest" ).as_posix()
		self.assertNotEqual( s["render"].hash( c ), current )

		# output varies by changed Context entries
		current = s["render"].hash( c )
		c["renderDirectory"] = ( self.temporaryDirectory() / "renderTest2" ).as_posix()
		self.assertNotEqual( s["render"].hash( c ), current )

		# output doesn't vary by ui Context entries
		current = s["render"].hash( c )
		c["ui:something"] = "alterTheUI"
		self.assertEqual( s["render"].hash( c ), current )

		# also varies by input node
		current = s["render"].hash( c )
		s["render"]["in"].setInput( s["plane"]["out"] )
		self.assertNotEqual( s["render"].hash( c ), current )

	def testSceneTranslationOnly( self ) :

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

		render = GafferScene.Render()
		render["in"].setInput( outputs["out"] )
		render["mode"].setValue( render.Mode.RenderMode )
		render["renderer"].setValue( self.renderer )

		with Gaffer.Context() as context :
			context["scene:render:sceneTranslationOnly"] = IECore.BoolData( True )
			render["task"].execute()

		self.assertFalse( ( self.temporaryDirectory() / "test.exr" ).exists() )

	def testRenderMode( self ) :

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

		render = GafferScene.Render()
		render["in"].setInput( outputs["out"] )
		render["mode"].setValue( render.Mode.RenderMode )
		render["renderer"].setValue( self.renderer )

		render["task"].execute()
		self.assertTrue( ( self.temporaryDirectory() / "test.exr" ).exists() )

	def testSceneDescriptionMode( self ) :

		if self.sceneDescriptionSuffix is None :
			raise unittest.SkipTest( "Scene description not supported" )

		plane = GafferScene.Plane()

		render = GafferScene.Render()
		render["in"].setInput( plane["out"] )
		render["mode"].setValue( render.Mode.SceneDescriptionMode )
		render["fileName"].setValue( ( self.temporaryDirectory() / "subdirectory" / f"test{self.sceneDescriptionSuffix}" ) )
		render["renderer"].setValue( self.renderer )

		for i in range( 0, 2 ) : # Test twice, to check we can cope with the directory already existing.

			render["task"].execute()
			self.assertTrue( pathlib.Path( render["fileName"].getValue() ).exists() )

	def testExecute( self ) :

		if self.sceneDescriptionSuffix is None :
			raise unittest.SkipTest( "Scene description not supported" )

		s = Gaffer.ScriptNode()

		s["plane"] = GafferScene.Plane()
		s["render"] = GafferScene.Render()
		s["render"]["mode"].setValue( s["render"].Mode.SceneDescriptionMode )
		s["render"]["renderer"].setValue( self.renderer )
		s["render"]["fileName"].setValue( ( self.temporaryDirectory() / f"test.#{self.sceneDescriptionSuffix}" ) )
		s["render"]["in"].setInput( s["plane"]["out"] )

		scriptFileName = self.temporaryDirectory() / "test.gfr"
		s["fileName"].setValue( scriptFileName )
		s.save()

		subprocess.check_call(
			f"gaffer execute {scriptFileName} -frames 1-3",
			shell=True,
		)

		for i in range( 1, 4 ) :
			self.assertTrue( ( self.temporaryDirectory() / f"test.{i}{self.sceneDescriptionSuffix}" ).exists() )

	def testRendererOption( self ) :

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

		customOptions = GafferScene.CustomOptions()
		customOptions["in"].setInput( outputs["out"] )
		customOptions["options"].addChild( Gaffer.NameValuePlug( "render:defaultRenderer", self.renderer ) )

		render = GafferScene.Render()
		render["in"].setInput( customOptions["out"] )
		render["mode"].setValue( render.Mode.RenderMode )
		self.assertEqual( render["renderer"].getValue(), "" )

		render["task"].execute()
		self.assertTrue( ( self.temporaryDirectory() / "test.exr" ).exists() )

	def testNoRenderer( self ) :

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

		render = GafferScene.Render()
		render["in"].setInput( outputs["out"] )
		render["mode"].setValue( render.Mode.RenderMode )
		self.assertEqual( render["renderer"].getValue(), "" )

		self.assertEqual( render["task"].hash(), IECore.MurmurHash() )

		render["task"].execute()
		self.assertFalse( ( self.temporaryDirectory() / "test.exr" ).exists() )

if __name__ == "__main__":
	unittest.main()
