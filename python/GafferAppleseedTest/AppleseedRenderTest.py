##########################################################################
#
#  Copyright (c) 2014, Esteban Tovagliari. All rights reserved.
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
import re
import subprocess
import time
import unittest

import IECore
import IECoreScene

import Gaffer
import GafferTest
import GafferScene
import GafferAppleseed
import GafferAppleseedTest
import GafferOSL

class AppleseedRenderTest( GafferTest.TestCase ) :

	def setUp( self ) :

		GafferTest.TestCase.setUp( self )

		self.__scriptFileName = self.temporaryDirectory() / "test.gfr"

	def testExecute( self ) :

		s = Gaffer.ScriptNode()

		s["plane"] = GafferScene.Plane()
		s["render"] = GafferAppleseed.AppleseedRender()
		s["render"]["mode"].setValue( s["render"].Mode.SceneDescriptionMode )
		s["render"]["in"].setInput( s["plane"]["out"] )

		s["expression"] = Gaffer.Expression()
		s["expression"].setExpression( f"""parent['render']['fileName'] = '{( self.temporaryDirectory() / "test.%d.appleseed" ).as_posix()}' % int( context['frame'] )""" )

		s["fileName"].setValue( self.__scriptFileName )
		s.save()

		subprocess.check_call(
			[ str( Gaffer.executablePath() ), "execute", self.__scriptFileName, "-frames", "1-3" ]
		)

		for i in range( 1, 4 ) :
			self.assertTrue( ( self.temporaryDirectory() / f"test.{i}.appleseed" ).exists() )

	def testWaitForImage( self ) :

		s = Gaffer.ScriptNode()

		s["plane"] = GafferScene.Plane()

		s["options"] = GafferAppleseed.AppleseedOptions()
		s["options"]["in"].setInput( s["plane"]["out"] )
		s["options"]["options"]["maxAASamples"]["value"].setValue( 1 )
		s["options"]["options"]["maxAASamples"]["enabled"].setValue( True )

		s["outputs"] = GafferScene.Outputs()
		s["outputs"].addOutput(
			"beauty",
			IECoreScene.Output(
				str( self.temporaryDirectory() / "test.exr" ),
				"exr",
				"rgba",
				{}
			)
		)
		s["outputs"]["in"].setInput( s["options"]["out"] )

		s["render"] = GafferAppleseed.AppleseedRender()
		s["render"]["in"].setInput( s["outputs"]["out"] )

		s["render"]["fileName"].setValue( self.temporaryDirectory() / "test.appleseed" )

		s["fileName"].setValue( self.__scriptFileName )
		s.save()

		s["render"]["task"].execute()

		self.assertTrue( ( self.temporaryDirectory() / "test.exr" ).exists() )

	def testExecuteWithStringSubstitutions( self ) :

		s = Gaffer.ScriptNode()

		s["plane"] = GafferScene.Plane()
		s["render"] = GafferAppleseed.AppleseedRender()
		s["render"]["mode"].setValue( s["render"].Mode.SceneDescriptionMode )
		s["render"]["in"].setInput( s["plane"]["out"] )
		s["render"]["fileName"].setValue( self.temporaryDirectory() / "test.####.appleseed" )

		s["fileName"].setValue( self.__scriptFileName )
		s.save()

		subprocess.check_call(
			[ str( Gaffer.executablePath() ), "execute", self.__scriptFileName, "-frames", "1-3" ]
		)

		for i in range( 1, 4 ) :
			self.assertTrue( ( self.temporaryDirectory() / f"test.{i:04d}.appleseed" ).exists() )

	def testImageOutput( self ) :

		s = Gaffer.ScriptNode()

		s["plane"] = GafferScene.Plane()

		s["options"] = GafferAppleseed.AppleseedOptions()
		s["options"]["in"].setInput( s["plane"]["out"] )
		s["options"]["options"]["maxAASamples"]["value"].setValue( 1 )
		s["options"]["options"]["maxAASamples"]["enabled"].setValue( True )

		s["outputs"] = GafferScene.Outputs()
		s["outputs"].addOutput(
			"beauty",
			IECoreScene.Output(
				str( self.temporaryDirectory() / "test.####.exr" ),
				"exr",
				"rgba",
				{}
			)
		)
		s["outputs"]["in"].setInput( s["options"]["out"] )

		s["render"] = GafferAppleseed.AppleseedRender()
		s["render"]["in"].setInput( s["outputs"]["out"] )

		s["render"]["fileName"].setValue( self.temporaryDirectory() / "test.####.appleseed" )

		s["fileName"].setValue( self.__scriptFileName )
		s.save()

		c = Gaffer.Context()
		for i in range( 1, 4 ) :
			c.setFrame( i )
			with c :
				s["render"]["task"].execute()

		for i in range( 1, 4 ) :
			self.assertTrue( ( self.temporaryDirectory() / f"test.{i:04d}.exr" ).exists() )

	def testTypeNamePrefixes( self ) :

		self.assertTypeNamesArePrefixed( GafferAppleseed )
		self.assertTypeNamesArePrefixed( GafferAppleseedTest )

	def testDefaultNames( self ) :

		self.assertDefaultNamesAreCorrect( GafferAppleseed )
		self.assertDefaultNamesAreCorrect( GafferAppleseedTest )

	def testNodesConstructWithDefaultValues( self ) :

		self.assertNodesConstructWithDefaultValues( GafferAppleseed )
		self.assertNodesConstructWithDefaultValues( GafferAppleseedTest )

	def testDirectoryCreation( self ) :

		s = Gaffer.ScriptNode()
		s["variables"].addChild( Gaffer.NameValuePlug( "renderDirectory", ( self.temporaryDirectory() / "renderTests" ).as_posix(),  Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		s["variables"].addChild( Gaffer.NameValuePlug( "appleseedDirectory", ( self.temporaryDirectory() / "appleseedTests" ).as_posix(), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )

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

		s["render"] = GafferAppleseed.AppleseedRender()
		s["render"]["in"].setInput( s["outputs"]["out"] )
		s["render"]["fileName"].setValue( "$appleseedDirectory/test.####.appleseed" )
		s["render"]["mode"].setValue( s["render"].Mode.SceneDescriptionMode )

		self.assertFalse( ( self.temporaryDirectory() / "renderTests" ).exists() )
		self.assertFalse( ( self.temporaryDirectory() / "appleseedTests" ).exists() )
		self.assertFalse( ( self.temporaryDirectory() / "appleseedTests" / "test.0001.appleseed" ).exists() )
		self.assertFalse( self.__scriptFileName.exists() )

		s["fileName"].setValue( self.__scriptFileName )
		s.save()

		with s.context() :
			s["render"]["task"].execute()

		self.assertTrue( ( self.temporaryDirectory() / "renderTests" ).exists() )
		self.assertTrue( ( self.temporaryDirectory() / "appleseedTests" ).exists() )
		self.assertTrue( ( self.temporaryDirectory() / "appleseedTests" / "test.0001.appleseed" ).exists() )
		self.assertTrue( ( self.__scriptFileName ) )

		# check it can cope with everything already existing

		with s.context() :
			s["render"]["task"].execute()

		self.assertTrue( ( self.temporaryDirectory() / "renderTests" ).exists() )
		self.assertTrue( ( self.temporaryDirectory() / "appleseedTests" ).exists() )
		self.assertTrue( ( self.temporaryDirectory() / "appleseedTests" / "test.0001.appleseed" ).exists() )

	def testInternalConnectionsNotSerialised( self ) :

		s = Gaffer.ScriptNode()
		s["render"] = GafferAppleseed.AppleseedRender()
		self.assertFalse( "__adaptedIn" in s.serialise() )

	def testNoInput( self ) :

		render = GafferAppleseed.AppleseedRender()
		render["mode"].setValue( render.Mode.SceneDescriptionMode )
		render["fileName"].setValue( self.temporaryDirectory() / "test.appleseed" )

		self.assertEqual( render["task"].hash(), IECore.MurmurHash() )
		render["task"].execute()
		self.assertFalse( pathlib.Path( render["fileName"].getValue() ).exists() )

	def testInputFromContextVariables( self ) :

		plane = GafferScene.Plane()

		variables = Gaffer.ContextVariables()
		variables.setup( GafferScene.ScenePlug() )
		variables["in"].setInput( plane["out"] )

		render = GafferAppleseed.AppleseedRender()
		render["in"].setInput( variables["out"] )
		render["mode"].setValue( render.Mode.SceneDescriptionMode )
		render["fileName"].setValue( self.temporaryDirectory() / "test.appleseed" )

		self.assertNotEqual( render["task"].hash(), IECore.MurmurHash() )
		render["task"].execute()
		self.assertTrue( pathlib.Path( render["fileName"].getValue() ).exists() )

	def testShaderSubstitutions( self ) :

		plane = GafferScene.Plane()

		planeAttrs = GafferScene.CustomAttributes()
		planeAttrs["in"].setInput( plane["out"] )
		planeAttrs["attributes"].addChild( Gaffer.NameValuePlug( "A", Gaffer.StringPlug( "value", defaultValue = 'bar' ) ) )
		planeAttrs["attributes"].addChild( Gaffer.NameValuePlug( "B", Gaffer.StringPlug( "value", defaultValue = 'foo' ) ) )

		cube = GafferScene.Cube()

		cubeAttrs = GafferScene.CustomAttributes()
		cubeAttrs["in"].setInput( cube["out"] )
		cubeAttrs["attributes"].addChild( Gaffer.NameValuePlug( "B", Gaffer.StringPlug( "value", defaultValue = 'override' ) ) )

		parent = GafferScene.Parent()
		parent["in"].setInput( planeAttrs["out"] )
		parent["children"][0].setInput( cubeAttrs["out"] )
		parent["parent"].setValue( "/plane" )

		shader = GafferOSL.OSLShader()
		shader.loadShader( "as_texture" )
		shader["parameters"]["in_filename"].setValue( "<attr:A>/path/<attr:B>.tx" )

		f = GafferScene.PathFilter()
		f["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		shaderAssignment = GafferScene.ShaderAssignment()
		shaderAssignment["in"].setInput( parent["out"] )
		shaderAssignment["filter"].setInput( f["out"] )
		shaderAssignment["shader"].setInput( shader["out"] )

		render = GafferAppleseed.AppleseedRender()
		render["in"].setInput( shaderAssignment["out"] )
		render["mode"].setValue( render.Mode.SceneDescriptionMode )
		render["fileName"].setValue( self.temporaryDirectory() / "test.appleseed" )

		self.assertNotEqual( render["task"].hash(), IECore.MurmurHash() )
		render["task"].execute()
		self.assertTrue( pathlib.Path( render["fileName"].getValue() ).exists() )
		f = open( render["fileName"].getValue(), "r", encoding = "utf-8" )
		texturePaths = set( re.findall( '<parameter name="in_filename" value="string (.*)"', f.read()) )
		self.assertEqual( texturePaths, set( ['bar/path/foo.tx', 'bar/path/override.tx' ] ) )

	def testMessageHandler( self ) :

		RenderType = GafferScene.Private.IECoreScenePreview.Renderer.RenderType

		for renderType, fileName, output, expected in (
			( RenderType.Batch, "", IECoreScene.Output( str( self.temporaryDirectory() / "beauty.exr" ), "exr", "rgba" ), 2 ),
			( RenderType.Interactive, "", IECoreScene.Output( str( self.temporaryDirectory() / "beauty.exr" ), "exr", "rgba" ), 2 ),
			( RenderType.SceneDescription, str( self.temporaryDirectory() / "test.appleseed" ) , None, 1 )
		) :

			with IECore.CapturingMessageHandler() as fallbackHandler :

				handler = IECore.CapturingMessageHandler()

				r = GafferScene.Private.IECoreScenePreview.Renderer.create(
					"Appleseed",
					renderType,
					fileName = fileName,
					messageHandler = handler
				)

				r.option( "as:log:level", IECore.StringData( "debug" ) )
				r.option( "as:invalid", IECore.BoolData( True ) )

				if output :
					r.output( "testOutput", output )

				r.object( "/sphere", IECoreScene.SpherePrimitive(), r.attributes( IECore.CompoundObject() ) )

				r.render()

				if renderType == RenderType.Interactive :
					time.sleep( 1 )

				# We should have at least 1 message from our invalid option plus
				# _something_ from the renderers own output stream for a render.
				self.assertGreaterEqual( len(handler.messages), expected, msg=str(renderType) )

				self.assertEqual( [ m.message for m in fallbackHandler.messages ], [], msg=str(renderType) )

if __name__ == "__main__":
	unittest.main()
