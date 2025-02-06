##########################################################################
#
#  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

import functools

import IECore

import Gaffer
import GafferUI
import GafferUITest
import GafferImage
import GafferScene
import GafferSceneTest
import GafferSceneUI

class ShaderViewTest( GafferUITest.TestCase ) :

	def testFactory( self ) :

		script = Gaffer.ScriptNode()
		script["shader"] = GafferSceneTest.TestShader()
		script["shader"]["type"].setValue( "test:surface" )
		script["shader"]["name"].setValue( "test" )

		view = GafferUI.View.create( script["shader"]["out"] )
		self.assertTrue( isinstance( view, GafferSceneUI.ShaderView ) )

	def testRegisterScene( self ) :

		class TestShaderBall( GafferScene.ShaderBall ) :

			def __init__( self, name = "TestShaderBall" ) :

				GafferScene.ShaderBall.__init__( self, name )

		IECore.registerRunTimeTyped( TestShaderBall )

		GafferSceneUI.ShaderView.registerScene( "test", "Default", TestShaderBall )

		script = Gaffer.ScriptNode()
		script["shader"] = GafferSceneTest.TestShader()
		script["shader"]["type"].setValue( "test:surface" )
		script["shader"]["name"].setValue( "test" )

		view = GafferUI.View.create( script["shader"]["out"] )
		self.assertTrue( isinstance( view.scene(), TestShaderBall ) )

	def testRegisterReferenceScene( self ) :

		s = Gaffer.ScriptNode()

		s["b"] = Gaffer.Box()
		s["b"]["shader"] = GafferScene.ShaderPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["b"]["out"] = GafferScene.ScenePlug( direction = Gaffer.Plug.Direction.Out, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["b"]["cube"] = GafferScene.Cube()
		s["b"]["assignment"] = GafferScene.ShaderAssignment()
		s["b"]["assignment"]["in"].setInput( s["b"]["cube"]["out"] )
		s["b"]["assignment"]["shader"].setInput( s["b"]["shader"] )
		s["b"]["out"].setInput( s["b"]["assignment"]["out"] )

		s["b"].exportForReference( self.temporaryDirectory() / "test.grf" )

		GafferSceneUI.ShaderView.registerScene( "test", "Default", self.temporaryDirectory() / "test.grf" )

		script = Gaffer.ScriptNode()
		script["shader"] = GafferSceneTest.TestShader()
		script["shader"]["type"].setValue( "test:surface" )
		script["shader"]["name"].setValue( "test" )

		view = GafferUI.View.create( script["shader"]["out"] )
		self.assertTrue( isinstance( view.scene(), Gaffer.Reference ) )
		self.assertEqual( view.scene().fileName(), self.temporaryDirectory() / "test.grf" )
		self.assertEqual( view.scene()["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "cube" ] ) )

	def testScenesAreReused( self ) :

		class TestAShaderBall( GafferScene.ShaderBall ) :

			def __init__( self, name = "TestAShaderBall" ) :

				GafferScene.ShaderBall.__init__( self, name )

		IECore.registerRunTimeTyped( TestAShaderBall )

		class TestBShaderBall( GafferScene.ShaderBall ) :

			def __init__( self, name = "TestBShaderBall" ) :

				GafferScene.ShaderBall.__init__( self, name )

		IECore.registerRunTimeTyped( TestBShaderBall )

		GafferSceneUI.ShaderView.registerScene( "testA", "Default", TestAShaderBall )
		GafferSceneUI.ShaderView.registerScene( "testB", "Default", TestBShaderBall )

		script = Gaffer.ScriptNode()
		script["shaderA"] = GafferSceneTest.TestShader()
		script["shaderA"]["type"].setValue( "testA:surface" )
		script["shaderA"]["name"].setValue( "test" )

		script["shaderB"] = GafferSceneTest.TestShader()
		script["shaderB"]["type"].setValue( "testB:surface" )
		script["shaderB"]["name"].setValue( "test" )

		view = GafferUI.View.create( script["shaderA"]["out"] )
		sceneA = view.scene()
		self.assertTrue( isinstance( sceneA, TestAShaderBall ) )

		view["in"].setInput( script["shaderB"]["out"] )
		sceneB = view.scene()
		self.assertTrue( isinstance( sceneB, TestBShaderBall ) )

		view["in"].setInput( script["shaderA"]["out"] )
		self.assertTrue( view.scene().isSame( sceneA ) )

		view["in"].setInput( script["shaderB"]["out"] )
		self.assertTrue( view.scene().isSame( sceneB ) )

	def testChangeScene( self ) :

		GafferSceneUI.ShaderView.registerScene( "sceneTest", "A", GafferScene.ShaderBall )
		GafferSceneUI.ShaderView.registerScene( "sceneTest", "B", GafferScene.ShaderBall )

		script = Gaffer.ScriptNode()
		script["shader"] = GafferSceneTest.TestShader()
		script["shader"]["type"].setValue( "sceneTest:surface" )
		script["shader"]["name"].setValue( "test" )

		view = GafferUI.View.create( script["shader"]["out"] )
		view["scene"].setValue( "A" )

		sceneA = view.scene()
		self.assertTrue( isinstance( sceneA, GafferScene.ShaderBall ) )

		view["scene"].setValue( "B" )
		sceneB = view.scene()
		self.assertTrue( isinstance( sceneB, GafferScene.ShaderBall ) )
		self.assertFalse( sceneA.isSame( sceneB ) )

	def testReregisterScene( self ) :

		def shaderBallCreator( resolution ) :

			result = GafferScene.ShaderBall()
			result["resolution"].setValue( resolution )

			return result

		GafferSceneUI.ShaderView.registerScene( "test", "Default", functools.partial( shaderBallCreator, 16 ) )

		script = Gaffer.ScriptNode()
		script["shader"] = GafferSceneTest.TestShader()
		script["shader"]["type"].setValue( "test:surface" )
		script["shader"]["name"].setValue( "test" )

		view = GafferUI.View.create( script["shader"]["out"] )
		scene1 = view.scene()
		self.assertEqual( view.scene()["resolution"].getValue(), 16 )

		GafferSceneUI.ShaderView.registerScene( "test", "Default", functools.partial( shaderBallCreator, 32 ) )
		self.assertFalse( view.scene().isSame( scene1 ) )
		self.assertEqual( view.scene()["resolution"].getValue(), 32 )

		GafferSceneUI.ShaderView.registerScene( "test", "HiRes", functools.partial( shaderBallCreator, 2048 ) )
		view["scene"].setValue( "HiRes" )
		self.assertEqual( view.scene()["resolution"].getValue(), 2048 )

		GafferSceneUI.ShaderView.registerScene( "test", "HiRes", functools.partial( shaderBallCreator, 4096 ) )
		self.assertEqual( view.scene()["resolution"].getValue(), 4096 )

	def testCannotViewCatalogue( self ) :

		script = Gaffer.ScriptNode()
		script["catalogue"] = GafferImage.Catalogue()

		view = GafferSceneUI.ShaderView( script )
		self.assertFalse( view["in"].acceptsInput( script["catalogue"]["out"] ) )

	def testCannotViewSceneSwitch( self ) :

		script = Gaffer.ScriptNode()
		script["sphere"] = GafferScene.Sphere()
		script["switch"] = Gaffer.Switch()
		script["switch"].setup( script["sphere"]["out"] )

		view = GafferSceneUI.ShaderView( script )

		self.assertFalse( view["in"].acceptsInput( script["sphere"]["out"] ) )
		self.assertFalse( view["in"].acceptsInput( script["switch"]["out"] ) )

	def testSceneCreatorReturningNone( self ) :

		script = Gaffer.ScriptNode()
		script["shader"] = GafferSceneTest.TestShader()
		script["shader"]["type"].setValue( "test:surface" )
		script["shader"]["name"].setValue( "test" )

		GafferSceneUI.ShaderView.registerScene( "test", "Bad", lambda : None )
		view = GafferUI.View.create( script["shader"]["out"] )
		with IECore.CapturingMessageHandler() as mh :
			view["scene"].setValue( "Bad" )

		self.assertEqual( len( mh.messages ), 1 )
		self.assertEqual( mh.messages[0].message, 'SceneCreator "Bad" returned null' )
		self.assertIsNone( view.scene() )

	def testSceneWithoutShaderPlug( self ) :

		script = Gaffer.ScriptNode()
		script["shader"] = GafferSceneTest.TestShader()
		script["shader"]["type"].setValue( "test:surface" )
		script["shader"]["name"].setValue( "test" )

		GafferSceneUI.ShaderView.registerScene( "test", "NoShaderPlug", lambda : GafferScene.Plane() )
		view = GafferUI.View.create( script["shader"]["out"] )
		with IECore.CapturingMessageHandler() as mh :
			view["scene"].setValue( "NoShaderPlug" )

		self.assertEqual( len( mh.messages ), 1 )
		self.assertEqual( mh.messages[0].message, 'Scene "NoShaderPlug" does not have a "shader" input plug' )

	def testSceneWithoutOutPlug( self ) :

		script = Gaffer.ScriptNode()
		script["shader"] = GafferSceneTest.TestShader()
		script["shader"]["type"].setValue( "test:surface" )
		script["shader"]["name"].setValue( "test" )

		def noOutPlug() :

			node = Gaffer.Node()
			node["shader"] = GafferScene.ShaderPlug()
			return node

		GafferSceneUI.ShaderView.registerScene( "test", "NoOutPlug", noOutPlug )
		view = GafferUI.View.create( script["shader"]["out"] )
		with IECore.CapturingMessageHandler() as mh :
			view["scene"].setValue( "NoOutPlug" )

		self.assertEqual( len( mh.messages ), 1 )
		self.assertEqual( mh.messages[0].message, 'Scene "NoOutPlug" does not have an "out" output scene plug' )

	def testIdleConnectionDoesntExtendLifetime( self ) :

		script = Gaffer.ScriptNode()
		script["shader"] = GafferSceneTest.TestShader()
		script["shader"]["type"].setValue( "test:surface" )
		script["shader"]["name"].setValue( "test" )

		numSlots = GafferUI.Gadget.idleSignal().numSlots()
		view = GafferUI.View.create( script["shader"]["out"] )
		self.assertEqual( GafferUI.Gadget.idleSignal().numSlots(), numSlots + 1 )
		del view
		self.assertEqual( GafferUI.Gadget.idleSignal().numSlots(), numSlots )

if __name__ == "__main__":
	unittest.main()
