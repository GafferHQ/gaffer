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
import struct
import subprocess
import unittest

import imath

import IECore
import IECoreScene

import Gaffer
import GafferTest
import GafferImage
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
				( self.temporaryDirectory() / "test.exr" ).as_posix(),
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
				( self.temporaryDirectory() / "test.exr" ).as_posix(),
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
				( self.temporaryDirectory() / "test.exr" ).as_posix(),
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
				( self.temporaryDirectory() / "test.exr" ).as_posix(),
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

	def testResolvedRenderer( self ) :

		standardOptions = GafferScene.StandardOptions()

		render = GafferScene.Render()
		render["in"].setInput( standardOptions["out"] )
		self.assertEqual( render["renderer"].getValue(), "" )
		self.assertEqual( render["resolvedRenderer"].getValue(), "" )

		standardOptions["options"]["render:defaultRenderer"]["enabled"].setValue( True )
		standardOptions["options"]["render:defaultRenderer"]["value"].setValue( self.renderer )
		self.assertEqual( render["resolvedRenderer"].getValue(), self.renderer )

		render["renderer"].setValue( "Other" )
		self.assertEqual( render["resolvedRenderer"].getValue(), "Other" )

	def testRenderSignals( self ) :

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

		preCS = GafferTest.CapturingSlot( GafferScene.Render.preRenderSignal() )
		postCS = GafferTest.CapturingSlot( GafferScene.Render.postRenderSignal() )

		render = GafferScene.Render()
		render["task"].execute()
		self.assertEqual( len( preCS ), 0 )
		self.assertEqual( len( postCS ), 0 )

		render["in"].setInput( outputs["out"] )
		render["task"].execute()
		self.assertEqual( len( preCS ), 0 )
		self.assertEqual( len( postCS ), 0 )

		render["renderer"].setValue( self.renderer )
		render["task"].execute()
		self.assertEqual( len( preCS ), 1 )
		self.assertEqual( len( postCS ), 1 )
		self.assertEqual( preCS[0], ( render, ) )
		self.assertEqual( postCS[0], ( render, ) )

		with Gaffer.Context() as context :
			context["scene:render:sceneTranslationOnly"] = IECore.BoolData( True )
			render["task"].execute()

		self.assertEqual( len( preCS ), 2 )
		self.assertEqual( len( postCS ), 2 )
		self.assertEqual( preCS[1], ( render, ) )
		self.assertEqual( postCS[1], ( render, ) )

	def testLightLinking( self ) :

		script = Gaffer.ScriptNode()

		script["camera"] = GafferScene.Camera()
		script["camera"]["transform"]["translate"]["z"].setValue( 5 )

		script["parent"] = GafferScene.Parent()
		script["parent"]["in"].setInput( script["camera"]["out"] )
		script["parent"]["parent"].setValue( "/" )

		script["shader"], unused, shaderOut = self._createDiffuseShader()

		for label, color in {
			"red" : imath.Color3f( 1, 0, 0 ),
			"green" : imath.Color3f( 0, 1, 0 ),
		}.items() :

			light, colorPlug = self._createPointLight()
			light["name"].setValue( f"{label}Light" )
			colorPlug.setValue( color )
			light["transform"]["translate"]["z"].setValue( 1 )
			script[f"{label}Light"] = light

			plane = GafferScene.Plane()
			plane["name"].setValue( f"{label}Plane" )
			plane["transform"]["translate"].setValue( color )
			script[f"{label}Plane"] = plane

			assignment = GafferScene.ShaderAssignment()
			assignment["in"].setInput( plane["out"] )
			assignment["shader"].setInput( shaderOut )
			script[f"{label}Assignment"] = assignment

			attributes = GafferScene.StandardAttributes()
			attributes["attributes"]["linkedLights"]["enabled"].setValue( True )
			attributes["attributes"]["linkedLights"]["value"].setValue( f"/{label}Light" )
			attributes["in"].setInput( assignment["out"] )
			script[f"{label}Attributes"] = attributes

			script["parent"]["children"].next().setInput( light["out"] )
			script["parent"]["children"].next().setInput( attributes["out"] )

		imagePath = ( self.temporaryDirectory() / "test.exr" )
		script["outputs"] = GafferScene.Outputs()
		script["outputs"].addOutput(
			"beauty",
			IECoreScene.Output(
				imagePath.as_posix(),
				"exr",
				"rgba",
			)
		)
		script["outputs"]["in"].setInput( script["parent"]["out"] )

		script["options"] = GafferScene.StandardOptions()
		script["options"]["options"]["render:camera"]["enabled"].setValue( True )
		script["options"]["options"]["render:camera"]["value"].setValue( "/camera" )
		script["options"]["in"].setInput( script["outputs"]["out"] )

		script["render"] = GafferScene.Render()
		script["render"]["in"].setInput( script["options"]["out"] )
		script["render"]["renderer"].setValue( self.renderer )
		script["render"]["task"].execute()

		reader = GafferImage.ImageReader()
		reader["fileName"].setValue( imagePath )

		sampler = GafferImage.ImageSampler()
		sampler["image"].setInput( reader["out"] )

		sampler["pixel"].setValue( imath.V2f( 320, 370 ) )
		self.assertEqual( sampler["color"]["r"].getValue(), 0 )
		self.assertGreater( sampler["color"]["g"].getValue(), 0.02 )

		sampler["pixel"].setValue( imath.V2f( 455, 232 ) )
		self.assertGreater( sampler["color"]["r"].getValue(), 0.02 )
		self.assertEqual( sampler["color"]["g"].getValue(), 0 )

	def testShadowLinking( self ) :

		script = Gaffer.ScriptNode()

		script["camera"] = GafferScene.Camera()
		script["camera"]["transform"]["translate"]["z"].setValue( 5 )

		script["parent"] = GafferScene.Parent()
		script["parent"]["in"].setInput( script["camera"]["out"] )
		script["parent"]["parent"].setValue( "/" )

		script["shader"], unused, shaderOut = self._createDiffuseShader()

		script["plane"] = GafferScene.Plane()
		script["plane"]["dimensions"].setValue( imath.V2f( 10 ) )
		script["assignment"] = GafferScene.ShaderAssignment()
		script["assignment"]["in"].setInput( script["plane"]["out"] )
		script["assignment"]["shader"].setInput( shaderOut )
		script["parent"]["children"].next().setInput( script["assignment"]["out"] )

		for label, color in {
			"red" : imath.Color3f( 1, 0, 0 ),
			"green" : imath.Color3f( 0, 1, 0 ),
		}.items() :

			light, colorPlug = self._createDistantLight()
			light["name"].setValue( f"{label}Light" )
			colorPlug.setValue( color )
			light["transform"]["translate"]["z"].setValue( 10 )
			script[f"{label}Light"] = light
			script["parent"]["children"].next().setInput( light["out"] )

		for index, shadowedLights in enumerate( [ None, "", "/redLight", "/greenLight", "defaultLights" ] ) :

			sphere = GafferScene.Sphere()
			sphere["radius"].setValue( 0.5 )
			sphere["transform"]["translate"]["x"].setValue( index - 2 )
			sphere["transform"]["translate"]["z"].setValue( 5 )
			script.addChild( sphere )

			assignment = GafferScene.ShaderAssignment()
			assignment["in"].setInput( sphere["out"] )
			assignment["shader"].setInput( shaderOut )
			script.addChild( assignment )

			attributes = GafferScene.CustomAttributes()
			attributes["in"].setInput( assignment["out"] )
			attributes["attributes"].addChild(
				Gaffer.NameValuePlug( self._cameraVisibilityAttribute(), False, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
			)

			if shadowedLights is not None :
				attributes["attributes"].addChild(
					Gaffer.NameValuePlug( "shadowedLights", shadowedLights, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
				)

			script["parent"]["children"].next().setInput( attributes["out"] )
			script.addChild( attributes )

		imagePath = self.temporaryDirectory() / "test.exr"
		script["outputs"] = GafferScene.Outputs()
		script["outputs"].addOutput(
			"beauty",
			IECoreScene.Output(
				imagePath.as_posix(),
				"exr",
				"rgba",
			)
		)
		script["outputs"]["in"].setInput( script["parent"]["out"] )

		script["options"] = GafferScene.StandardOptions()
		script["options"]["in"].setInput( script["outputs"]["out"] )
		script["options"]["options"]["render:camera"]["enabled"].setValue( True )
		script["options"]["options"]["render:camera"]["value"].setValue( "/camera" )

		script["rendererOptions"] = self._createOptions()
		script["rendererOptions"]["in"].setInput( script["options"]["out"] )

		script["render"] = GafferScene.Render()
		script["render"]["in"].setInput( script["rendererOptions"]["out"] )
		script["render"]["renderer"].setValue( self.renderer )
		script["render"]["task"].execute()

		reader = GafferImage.ImageReader()
		reader["fileName"].setValue( imagePath )

		sampler = GafferImage.ImageSampler()
		sampler["image"].setInput( reader["out"] )

		for x, expectedColor in {
			47 : imath.Color4f( 0, 0, 0, 1 ),
			186 : imath.Color4f( 1, 1, 0, 1 ),
			320 : imath.Color4f( 0, 1, 0, 1 ),
			454 : imath.Color4f( 1, 0, 0, 1 ),
			592 : imath.Color4f( 0, 0, 0, 1 ),
		}.items() :

			sampler["pixel"].setValue( imath.V2f( x, 240 ) )
			c = sampler["color"].getValue()
			m = max( c.r, c.g )
			if m :
				c.r /= m # Normalize so light intensity/falloff is irrelevant
				c.g /= m
			self.assertEqualWithAbsError( c, expectedColor, 0.001, f"(x == {x})" )

	def testOutputMetadata( self ) :

		script = Gaffer.ScriptNode()

		metadata = {
			"test:int" : IECore.IntData( 1 ),
			"test:float" : IECore.FloatData( 2.5 ),
			"test:string" : IECore.StringData( "foo" ),
		}

		fileName = self.temporaryDirectory() / "test.exr"
		script["outputs"] = GafferScene.Outputs()
		script["outputs"].addOutput(
			"beauty",
			IECoreScene.Output(
				fileName.as_posix(),
				"exr",
				"rgba",
				{
					f"header:{k}" : v
					for k, v in metadata.items()
				}
			)
		)

		script["render"] = GafferScene.Render()
		script["render"]["renderer"].setValue( self.renderer )
		script["render"]["in"].setInput( script["outputs"]["out"] )
		script["render"]["task"].execute()

		imageReader = GafferImage.ImageReader()
		imageReader["fileName"].setValue( fileName )

		for k, v in metadata.items() :
			self.assertIn( k, imageReader["out"].metadata() )
			self.assertEqual( imageReader["out"].metadata()[k], v )

	def testIDOutput( self ) :

		script = Gaffer.ScriptNode()

		script["camera"] = GafferScene.Camera()
		script["camera"]["transform"]["translate"]["z"].setValue( 5 )

		script["parent"] = GafferScene.Parent()
		script["parent"]["in"].setInput( script["camera"]["out"] )
		script["parent"]["parent"].setValue( "/" )

		for i in range( 0, 3 ) :

			sphere = GafferScene.Sphere()
			sphere["name"].setValue( f"sphere{i}" )
			sphere["radius"].setValue( 0.5 )
			sphere["transform"]["translate"]["x"].setValue( i - 1 )
			script.addChild( sphere )

			script["parent"]["children"].next().setInput( sphere["out"] )

		imagePath = self.temporaryDirectory() / "test.exr"
		beautyPath = self.temporaryDirectory() / "beauty.exr"
		script["outputs"] = GafferScene.Outputs()
		script["outputs"].addOutput(
			"beauty",
			IECoreScene.Output(
				beautyPath.as_posix(),
				"exr",
				"rgba"
			)
		)

		script["outputs"]["in"].setInput( script["parent"]["out"] )

		script["options"] = GafferScene.StandardOptions()
		script["options"]["in"].setInput( script["outputs"]["out"] )
		script["options"]["options"]["render:camera"]["enabled"].setValue( True )
		script["options"]["options"]["render:camera"]["value"].setValue( "/camera" )

		manifestPath = self.temporaryDirectory() / "manifest.exr"
		script["options"]["options"]["render:manifestFilePath"]["enabled"].setValue( True )
		script["options"]["options"]["render:manifestFilePath"]["value"].setValue( manifestPath )

		script["rendererOptions"] = self._createOptions()
		script["rendererOptions"]["in"].setInput( script["options"]["out"] )

		script["render"] = GafferScene.Render()
		script["render"]["in"].setInput( script["rendererOptions"]["out"] )
		script["render"]["renderer"].setValue( self.renderer )

		with IECore.CapturingMessageHandler() as mh :
			script["render"]["task"].execute()
			self.assertEqual( len( mh.messages ), 1 )
			self.assertEqual( mh.messages[0].message, 'Found render:manifestFilePath option, but the render manifest is not enabled because there is no ID output' )

		reader = GafferImage.ImageReader()
		reader["fileName"].setValue( beautyPath )
		self.assertNotIn( "gaffer:renderManifestFilePath", reader["out"].metadata() )

		script["outputs"].addOutput(
			"id",
			IECoreScene.Output(
				imagePath.as_posix(),
				"exr",
				"float id",
				{
					"layerName" : "id",
					"filter" : "closest",
				},
			)
		)

		script["render"]["task"].execute()

		reader["fileName"].setValue( imagePath )
		manifest = GafferScene.RenderManifest.loadFromImageMetadata( reader["out"].metadata(), "" )

		sampler = GafferImage.ImageSampler()
		sampler["image"].setInput( reader["out"] )
		sampler["channels"].setValue( IECore.StringVectorData( [ "id" ] * 4 ) )
		sampler["interpolate"].setValue( False )

		for x, expectedObject in {
			183 : "/sphere0",
			320 : "/sphere1",
			470 : "/sphere2",
		}.items() :

			sampler["pixel"].setValue( imath.V2f( x, 220 ) )
			id = sampler["color"]["r"].getValue()

			# Reinterpret float as int.
			id = struct.pack( "f", id )
			id = struct.unpack( "I", id )[0]

			self.assertEqual( manifest.pathForID( id ), expectedObject )

	def testInstanceIDOutput( self ) :

		script = Gaffer.ScriptNode()

		script["camera"] = GafferScene.Camera()
		script["camera"]["transform"]["translate"]["z"].setValue( 5 )

		script["plane"] = GafferScene.Plane()

		script["filter"] = GafferScene.PathFilter()
		script["filter"]["paths"].setValue( IECore.StringVectorData( [ '/plane' ] ) )

		script["instancer"] = GafferScene.Instancer()
		script["instancer"]["in"].setInput( script["plane"]["out"] )
		script["instancer"]["prototypes"].setInput( script["plane"]["out"] )
		script["instancer"]["filter"].setInput( script["filter"]["out"] )
		script["instancer"]["encapsulate"].setValue( True )

		script["parent"] = GafferScene.Parent()
		script["parent"]["in"].setInput( script["camera"]["out"] )
		script["parent"]["parent"].setValue( "/" )

		script["parent"]["children"][0].setInput( script["instancer"]["out"] )

		imagePath = self.temporaryDirectory() / "test.exr"
		beautyPath = self.temporaryDirectory() / "beauty.exr"

		script["outputs"] = GafferScene.Outputs()
		script["outputs"].addOutput(
			"beauty",
			IECoreScene.Output(
				beautyPath.as_posix(),
				"exr",
				"rgba"
			)
		)

		script["outputs"]["in"].setInput( script["parent"]["out"] )

		script["options"] = GafferScene.StandardOptions()
		script["options"]["in"].setInput( script["outputs"]["out"] )
		script["options"]["options"]["render:camera"]["enabled"].setValue( True )
		script["options"]["options"]["render:camera"]["value"].setValue( "/camera" )

		script["rendererOptions"] = self._createOptions()
		script["rendererOptions"]["in"].setInput( script["options"]["out"] )

		script["render"] = GafferScene.Render()
		script["render"]["in"].setInput( script["rendererOptions"]["out"] )
		script["render"]["renderer"].setValue( self.renderer )

		script["outputs"].addOutput(
			"instanceID",
			IECoreScene.Output(
				imagePath.as_posix(),
				"exr",
				"float instanceID",
				{
					"layerName" : "instanceID",
					"filter" : "closest",
				},
			)
		)

		script["render"]["task"].execute()

		reader = GafferImage.ImageReader()
		reader["fileName"].setValue( imagePath )

		sampler = GafferImage.ImageSampler()
		sampler["image"].setInput( reader["out"] )
		sampler["channels"].setValue( IECore.StringVectorData( [ "instanceID" ] * 4 ) )
		sampler["interpolate"].setValue( False )

		for pixel, expectedID in {
			imath.V2f( 260, 360 ) : 2,
			imath.V2f( 400, 360 ) : 3,
			imath.V2f( 260, 160 ) : 0,
			imath.V2f( 400, 160 ) : 1,
		}.items() :

			sampler["pixel"].setValue( pixel )
			id = sampler["color"]["r"].getValue()

			# Reinterpret float as int.
			id = struct.pack( "f", id )
			id = struct.unpack( "I", id )[0]

			self.assertEqual( id, expectedID + 1 )

	## Should be implemented by derived classes to return
	# an appropriate Shader node with a diffuse surface shader loaded, along
	# with the plug for the colour parameter and the output plug to be connected
	# to a ShaderAssignment.
	def _createDiffuseShader( self ) :

		raise NotImplementedError

	# Should be implemented by derived classes to return an appropriate Light
	# node with a distant light loaded, along with the plug for the colour
	# parameter.
	def _createDistantLight( self ) :

		raise NotImplementedError

	## Should be implemented by derived classes to return
	# the name of a bool attribute which controls camera visibility.
	def _cameraVisibilityAttribute( self ) :

		raise NotImplementedError

	## May be implemented by derived classes to return
	# an Options node to control rendering.
	def _createOptions( self ) :

		return GafferScene.CustomOptions()

if __name__ == "__main__":
	unittest.main()
