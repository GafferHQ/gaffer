##########################################################################
#
#  Copyright (c) 2018, John Haddon. All rights reserved.
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

import math
import time
import unittest

import imath

import OpenImageIO

import IECore
import IECoreImage
import IECoreScene
import IECoreRenderManTest

import GafferTest
import GafferScene

@unittest.skipIf( GafferTest.inCI(), "RenderMan license not available" )
class RendererTest( GafferTest.TestCase ) :

	def setUp( self ) :

		GafferTest.TestCase.setUp( self )
		# Get "RenderMan" Renderer registered.
		import IECoreRenderMan

	def testFactory( self ) :

		self.assertTrue( "RenderMan" in GafferScene.Private.IECoreScenePreview.Renderer.types() )

		r = GafferScene.Private.IECoreScenePreview.Renderer.create( "RenderMan" )
		self.assertTrue( isinstance( r, GafferScene.Private.IECoreScenePreview.Renderer ) )

	def testTwoRenderers( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create( "RenderMan" )
		# This looks unused, but is needed to trigger the deferred creation of
		# the Riley session.
		attributes = renderer.attributes( IECore.CompoundObject() )

		with self.assertRaisesRegex( RuntimeError, "RenderMan doesn't allow multiple active sessions" ) as handler :
			# RenderMan only allows there to be one renderer at a time.
			GafferScene.Private.IECoreScenePreview.Renderer.create( "RenderMan" )

		handler.exception.__traceback__ = None

	def testSceneDescription( self ) :

		with self.assertRaisesRegex( RuntimeError, "SceneDescription mode not supported" ) :
			GafferScene.Private.IECoreScenePreview.Renderer.create(
				"RenderMan",
				GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
				( self.temporaryDirectory() / "test.rib" ).as_posix()
			)

	def testOutput( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"RenderMan",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
		)

		r.output(
			"testRGB",
			IECoreScene.Output(
				( self.temporaryDirectory() / "rgb.exr" ).as_posix(),
				"exr",
				"rgb",
				{
				}
			)
		)

		r.output(
			"testRGBA",
			IECoreScene.Output(
				( self.temporaryDirectory() / "rgba.exr" ).as_posix(),
				"exr",
				"rgba",
				{
				}
			)
		)

		r.render()
		del r

		self.assertTrue( ( self.temporaryDirectory() / "rgb.exr" ).is_file() )
		imageFile = OpenImageIO.ImageInput.open( str( self.temporaryDirectory() / "rgb.exr" ) )
		imageSpec = imageFile.spec()
		imageFile.close()
		self.assertEqual( imageSpec.nchannels, 3 )
		self.assertEqual( imageSpec.channelnames, ( "R", "G", "B" ) )

		self.assertTrue( ( self.temporaryDirectory() / "rgba.exr" ).is_file() )
		imageFile = OpenImageIO.ImageInput.open( str( self.temporaryDirectory() / "rgba.exr" ) )
		imageSpec = imageFile.spec()
		imageFile.close()
		self.assertEqual( imageSpec.nchannels, 4 )
		self.assertEqual( imageSpec.channelnames, ( "R", "G", "B", "A" ) )

	def testObject( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"RenderMan",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
		)

		renderer.output(
			"test",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ImageDisplayDriver",
					"handle" : "myLovelySphere",
				}
			)
		)

		renderer.object(
			"sphere",
			IECoreScene.SpherePrimitive(),
			renderer.attributes( IECore.CompoundObject() )
		)

		renderer.render()

		image = IECoreImage.ImageDisplayDriver.storedImage( "myLovelySphere" )
		self.assertEqual( max( image["A"] ), 1 )

	def testMissingLightShader( self ) :

		messageHandler = IECore.CapturingMessageHandler()
		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"RenderMan",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Interactive,
			messageHandler = messageHandler
		)

		lightShader = IECoreScene.ShaderNetwork( { "light" : IECoreScene.Shader( "BadShader", "ri:light" ), }, output = ( "light", "out" ) )
		lightAttributes = renderer.attributes(
			IECore.CompoundObject( { "ri:light" : lightShader } )
		)

		# Exercises our workarounds for crashes in Riley when a light
		# doesn't have a valid shader.
		light = renderer.light( "/light", None, lightAttributes )
		light.transform( imath.M44f().translate( imath.V3f( 1, 2, 3 ) ) )

		self.assertEqual( len( messageHandler.messages ), 1 )
		self.assertEqual( messageHandler.messages[0].level, IECore.MessageHandler.Level.Warning )
		self.assertEqual( messageHandler.messages[0].message, "Unable to find shader \"BadShader\"." )

		del lightAttributes
		del light
		del renderer

	def testIntegratorEdit( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"RenderMan",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Interactive
		)

		renderer.output(
			"test",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ImageDisplayDriver",
					"handle" : "myLovelySphere",
				}
			)
		)

		object = renderer.object(
			"sphere",
			IECoreScene.SpherePrimitive(),
			renderer.attributes( IECore.CompoundObject() )
		)

		renderer.render()
		time.sleep( 1 )
		renderer.pause()

		image = IECoreImage.ImageDisplayDriver.storedImage( "myLovelySphere" )
		self.assertEqual( self.__colorAtUV( image, imath.V2i( 0.5 ) ), imath.Color4f( 1 ) )

		renderer.option(
			"ri:integrator",
			IECoreScene.ShaderNetwork(
				shaders = {
					"integrator" : IECoreScene.Shader(
						"PxrVisualizer", "ri:integrator",
						{
							"style" : "objectnormals",
							"wireframe" : False,
						}
					),
				},
				output = "integrator"
			)
		)

		renderer.render()
		time.sleep( 1 )

		image = IECoreImage.ImageDisplayDriver.storedImage( "myLovelySphere" )
		self.assertNotEqual( self.__colorAtUV( image, imath.V2i( 0.5 ) ), imath.Color4f( 0, 0.514117, 0.515205, 1 ) )

		del object
		del renderer

	def testEXRLayerNames( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"RenderMan",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
		)

		outputs = [
			# Data source, layer name, expected EXR channel names.
			( "rgb", None, ( "R", "G", "B" ) ),
			( "rgba", None, ( "R", "G", "B", "A" ) ),
			( "float z", "Z", ( "Z", ) ),
			( "lpe C<RD>[<L.>O]", None, ( "R", "G", "B" ) ),
			# Really we want the "rgb" suffixes to be capitalised to match
			# the EXR specification, but that's not what RenderMan does.
			# Gaffer's ImageReader will correct for it on loading though.
			( "lpe C<RD>[<L.>O]", "directDiffuse", ( "directDiffuse.r", "directDiffuse.g", "directDiffuse.b" ) ),
		]

		for i, output in enumerate( outputs ) :

			parameters = {}
			if output[1] is not None :
				parameters["layerName"] = output[1]

			renderer.output(
				f"test{i}",
				IECoreScene.Output(
					str( self.temporaryDirectory() / f"test{i}.exr" ),
					"exr",
					output[0],
					parameters
				)
			)

		renderer.render()
		del renderer

		for i, output in enumerate( outputs ) :
			with self.subTest( source = output[0], layerName = output[1] ) :
				image = OpenImageIO.ImageBuf( str( self.temporaryDirectory() / f"test{i}.exr" ) )
				self.assertEqual( image.spec().channelnames, output[2] )

	def testMultiLayerEXR( self ) :

		fileName = str( self.temporaryDirectory() / "test.exr" )

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"RenderMan",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
		)

		outputs = [
			# Data source, layer name.
			( "rgba", None ),
			( "float z", "Z" ),
			# Really we want the "rgb" suffixes to be capitalised to match
			# the EXR specification, but that's not what RenderMan does.
			# Gaffer's ImageReader will correct for it on loading though.
			( "lpe C<RD>[<L.>O]", "directDiffuse" ),
		]

		for i, output in enumerate( outputs ) :

			parameters = {}
			if output[1] is not None :
				parameters["layerName"] = output[1]

			renderer.output(
				f"test{i}",
				IECoreScene.Output(
					fileName,
					"exr",
					output[0],
					parameters
				)
			)

		renderer.render()
		del renderer

		image = OpenImageIO.ImageBuf( fileName )
		self.assertEqual( set( image.spec().channelnames ), { "R", "G", "B", "A", "Z", "directDiffuse.r", "directDiffuse.g", "directDiffuse.b" } )

	def testMultiLayerIEDisplay( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"RenderMan",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
		)

		outputs = [
			# Data source, layer name.
			( "rgba", None ),
			( "float z", "Z" ),
			# Really we want the "rgb" suffixes to be capitalised to match
			# the EXR specification, but that's not what RenderMan does.
			# Gaffer's ImageReader will correct for it on loading though.
			( "lpe C<RD>[<L.>O]", "directDiffuse" ),
		]

		for i, output in enumerate( outputs ) :

			parameters = {
				"driverType" : "ImageDisplayDriver",
				"handle" : "multiLayerTest",
			}
			if output[1] is not None :
				parameters["layerName"] = output[1]

			renderer.output(
				f"test{i}",
				IECoreScene.Output(
					"test",
					"ieDisplay",
					output[0],
					parameters
				)
			)

		renderer.render()
		del renderer

		image = IECoreImage.ImageDisplayDriver.storedImage( "multiLayerTest" )
		self.assertEqual( set( image.keys() ), { "R", "G", "B", "A", "Z", "directDiffuse.R", "directDiffuse.G", "directDiffuse.B" } )

	def testOutputAccumulationRule( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"RenderMan",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
		)

		renderer.option( "ri:hider:maxsamples", IECore.IntData( 8 ) )
		renderer.option( "ri:hider:minsamples", IECore.IntData( 8 ) )

		fileName = str( self.temporaryDirectory() / "test.exr" )
		renderer.output(
			"test",
			IECoreScene.Output(
				fileName,
				"exr",
				"float sampleCount",
				{
					"ri:accumulationRule" : "sum",
				},
			)
		)

		renderer.object(
			"sphere",
			IECoreScene.SpherePrimitive(),
			renderer.attributes( IECore.CompoundObject( {
				"ri:surface" : IECoreScene.ShaderNetwork(
					shaders = {
						"output" : IECoreScene.Shader( "PxrDiffuse" )
					},
					output = "output",
				)
			} ) )
		).transform( imath.M44f().translate( imath.V3f( 0, 0, -3 ) ) )

		renderer.render()
		del renderer

		image = OpenImageIO.ImageBuf( fileName )
		self.assertEqual( image.getpixel( 320, 240, 0 ), ( 8.0, ) )

	def testEXRHeaderMetadata( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"RenderMan",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
		)

		fileName = str( self.temporaryDirectory() / "test.exr" )
		renderer.output(
			"test",
			IECoreScene.Output(
				fileName,
				"exr",
				"rgba",
				{
					"header:testInt" : 1,
					"header:testFloat" : 2.0,
					"header:testString" : "foo",
					"header:testBool" : True,
					"header:testV2i" : imath.V2i( 1, 2 ),
				},
			)
		)

		renderer.render()
		del renderer

		image = OpenImageIO.ImageBuf( fileName )
		self.assertEqual( image.spec().get_int_attribute( "testInt" ), 1 )
		self.assertEqual( image.spec().get_float_attribute( "testFloat" ), 2.0 )
		self.assertEqual( image.spec().get_string_attribute( "testString" ), "foo" )
		self.assertEqual( image.spec().get_int_attribute( "testBool" ), 1 )
		self.assertEqual( image.spec().getattribute( "testV2i" ), ( 1, 2 ) )

	def testOneRenderOutputTwoDrivers( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"RenderMan",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
		)

		renderer.output(
			"test1",
			IECoreScene.Output(
				str( self.temporaryDirectory() / "test1.exr" ),
				"exr",
				"rgba",
				{}
			)
		)

		renderer.output(
			"test2",
			IECoreScene.Output(
				str( self.temporaryDirectory() / "test2.exr" ),
				"exr",
				"rgba",
				{}
			)
		)

		renderer.object(
			"sphere",
			IECoreScene.SpherePrimitive(),
			renderer.attributes( IECore.CompoundObject() )
		).transform( imath.M44f().translate( imath.V3f( 0, 0, -3 ) ) )

		renderer.render()
		del renderer

		image1 = OpenImageIO.ImageBuf( str( self.temporaryDirectory() / "test1.exr" ) )
		image2 = OpenImageIO.ImageBuf( str( self.temporaryDirectory() / "test2.exr" ) )

		self.assertFalse( OpenImageIO.ImageBufAlgo.compare( image1, image2, failthresh = 0, warnthresh=0 ).error )

	def testUserAttribute( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"RenderMan",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
		)

		fileName = str( self.temporaryDirectory() / "test.exr" )
		renderer.output(
			"test",
			IECoreScene.Output(
				fileName,
				"exr",
				"rgba",
				{
				},
			)
		)

		renderer.object(
			"sphere",
			IECoreScene.SpherePrimitive(),
			renderer.attributes( IECore.CompoundObject( {
				"ri:surface" : IECoreScene.ShaderNetwork(
					shaders = {
						"attribute" : IECoreScene.Shader(
							"PxrAttribute", "osl:shader", {
								"varname" : "user:myColor",
								"type" : "color",
							}
						),
						"output" : IECoreScene.Shader( "PxrConstant", "ri:surface" ),
					},
					connections = [
						( ( "attribute", "resultRGB" ), ( "output", "emitColor" ) )
					],
					output = "output",
				),
				"user:myColor" : IECore.Color3fData( imath.Color3f( 1, 0.5, 0.25 ) ),
			} ) )
		).transform( imath.M44f().translate( imath.V3f( 0, 0, -3 ) ) )

		renderer.render()
		del renderer

		image = OpenImageIO.ImageBuf( fileName )
		self.assertEqual( image.getpixel( 320, 240, 0 ), ( 1.0, 0.5, 0.25, 1.0 ) )

	def testArrayConnections( self ) :

		with IECoreRenderManTest.RileyCapture() as capture :

			renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
				"RenderMan",
				GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
			)

			renderer.object(
				"sphere",
				IECoreScene.SpherePrimitive(),
				renderer.attributes( IECore.CompoundObject( {
					"ri:surface" : IECoreScene.ShaderNetwork(
						shaders = {
							"mattes" : IECoreScene.Shader( "PxrMatteID", "osl:shader" ),
							"styles" : IECoreScene.Shader( "PxrStylizedControl", "osl:shader" ),
							"output" : IECoreScene.Shader( "PxrSurface", "ri:surface" ),
						},
						connections = [
							( ( "mattes", "resultAOV" ), ( "output", "utilityPattern[0]" ) ),
							( ( "styles", "resultAOV" ), ( "output", "utilityPattern[1]" ) ),
						],
						output = "output",
					),
				} ) )
			)

			del renderer

		material = next(
			x for x in capture.json if x["method"] == "CreateMaterial"
		)
		outputNode = next(
			x for x in material["material"]["nodes"] if x["name"] == "PxrSurface"
		)
		utilityPattern = next(
			x for x in outputNode["params"]["params"] if x["info"]["name"] == "utilityPattern"
		)
		self.assertEqual( utilityPattern["data"], [ "mattes:resultAOV", "styles:resultAOV" ] )
		self.assertEqual( utilityPattern["info"]["array"], True )
		self.assertEqual( utilityPattern["info"]["length"], 2 )
		self.assertEqual( utilityPattern["info"]["detail"], 5 ) #  Reference
		self.assertEqual( utilityPattern["info"]["type"], 0 ) # Integer

	def testPortalLight( self ) :

		# Render with a dome light on its own.

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"RenderMan",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Interactive
		)

		renderer.output(
			"test",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ImageDisplayDriver",
					"handle" : "myLovelySphere",
				}
			)
		)

		sphere = renderer.object(
			"sphere",
			IECoreScene.SpherePrimitive(),
			renderer.attributes( IECore.CompoundObject( {
				"ri:surface" : IECoreScene.ShaderNetwork(
					shaders = {
						"output" : IECoreScene.Shader( "PxrDiffuse" )
					},
					output = "output",
				)
			} ) )
		)
		sphere.transform( imath.M44f().translate( imath.V3f( 0, 0, -2 ) ) )

		dome = renderer.light(
			"dome",
			None,
			renderer.attributes( IECore.CompoundObject( {
				"ri:light" : IECoreScene.ShaderNetwork(
					shaders = {
						"output" : IECoreScene.Shader( "PxrDomeLight", "ri:light", { "exposure" : 4.0 } ),
					},
					output = "output",
				),
				"ri:visibility:camera" : IECore.BoolData( False ),
			} ) )
		)

		renderer.render()
		time.sleep( 1 )
		renderer.pause()

		# We should be illuminating the whole sphere.

		image = IECoreImage.ImageDisplayDriver.storedImage( "myLovelySphere" )
		self.assertGreater( self.__colorAtUV( image, imath.V2f( 0.3, 0.5 ) )[0], 0.5 )
		self.assertGreater( self.__colorAtUV( image, imath.V2f( 0.6, 0.5 ) )[0], 0.5 )

		# Add a portal light.

		portal = renderer.light(
			"portal",
			None,
			renderer.attributes( IECore.CompoundObject( {
				"ri:light" : IECoreScene.ShaderNetwork(
					shaders = {
						"output" : IECoreScene.Shader( "PxrPortalLight", "ri:light", {} ),
					},
					output = "output",
				),
				"ri:visibility:camera" : IECore.BoolData( False ),
			} ) )
		)
		portal.transform( imath.M44f().translate( imath.V3f( 1, 0, -1 ) ).rotate( imath.V3f( 0, math.pi / 2, 0 ) ) )

		renderer.render()
		time.sleep( 1 )
		renderer.pause()

		# We should only be illuminating the side the portal is on.

		image = IECoreImage.ImageDisplayDriver.storedImage( "myLovelySphere" )
		self.assertEqual( self.__colorAtUV( image, imath.V2f( 0.3, 0.5 ) )[0], 0 )
		self.assertGreater( self.__colorAtUV( image, imath.V2f( 0.6, 0.5 ) )[0], 0.5 )

		# Delete the portal light. We should be back to illuminating
		# on both sides.

		del portal
		renderer.render()
		time.sleep( 1 )
		renderer.pause()

		image = IECoreImage.ImageDisplayDriver.storedImage( "myLovelySphere" )
		self.assertGreater( self.__colorAtUV( image, imath.V2f( 0.4, 0.5 ) )[0], 0.5 )
		self.assertGreater( self.__colorAtUV( image, imath.V2f( 0.6, 0.5 ) )[0], 0.5 )

		# Recreate the portal light. We should only be illuminating on
		# one side again.

		portal = renderer.light(
			"portal",
			None,
			renderer.attributes( IECore.CompoundObject( {
				"ri:light" : IECoreScene.ShaderNetwork(
					shaders = {
						"output" : IECoreScene.Shader( "PxrPortalLight", "ri:light", {} ),
					},
					output = "output",
				),
				"ri:visibility:camera" : IECore.BoolData( False ),
			} ) )
		)
		portal.transform( imath.M44f().translate( imath.V3f( 1, 0, -1 ) ).rotate( imath.V3f( 0, math.pi / 2, 0 ) ) )

		renderer.render()
		time.sleep( 1 )
		renderer.pause()

		image = IECoreImage.ImageDisplayDriver.storedImage( "myLovelySphere" )
		self.assertEqual( self.__colorAtUV( image, imath.V2f( 0.3, 0.5 ) )[0], 0 )
		color = self.__colorAtUV( image, imath.V2f( 0.6, 0.5 ) )
		self.assertGreater( color[0], 0.5 )
		self.assertGreater( color[1], 0.5 )
		self.assertGreater( color[2], 0.5 )

		# Increase the intensity of the portal and tint the light colour.

		portal.attributes(
			renderer.attributes( IECore.CompoundObject( {
				"ri:light" : IECoreScene.ShaderNetwork(
					shaders = {
						"output" : IECoreScene.Shader( "PxrPortalLight", "ri:light", { "intensityMult" : 2.0, "tint" : imath.Color3f( 1, 0, 1 ) } ),
					},
					output = "output",
				),
				"ri:visibility:camera" : IECore.BoolData( False ),
			} ) )
		)

		renderer.render()
		time.sleep( 1 )
		renderer.pause()

		image = IECoreImage.ImageDisplayDriver.storedImage( "myLovelySphere" )
		self.assertEqual( self.__colorAtUV( image, imath.V2f( 0.3, 0.5 ) )[0], 0 )
		expectedColor = color * imath.Color4f( 2, 0, 2, 1 )
		color = self.__colorAtUV( image, imath.V2f( 0.6, 0.5 ) )
		for i in range( 0, 4 ) :
			self.assertAlmostEqual( color[i], expectedColor[i], delta = 0.01 )

		# Now delete the dome light. We should get no illumination at all.

		del dome
		renderer.render()
		time.sleep( 1 )
		renderer.pause()

		image = IECoreImage.ImageDisplayDriver.storedImage( "myLovelySphere" )
		self.assertEqual( self.__colorAtUV( image, imath.V2f( 0.3, 0.5 ) )[0], 0 )
		self.assertEqual( self.__colorAtUV( image, imath.V2f( 0.6, 0.5 ) )[0], 0 )

		# Recreate the dome light. We should again be illuminating only on one side.

		dome = renderer.light(
			"dome",
			None,
			renderer.attributes( IECore.CompoundObject( {
				"ri:light" : IECoreScene.ShaderNetwork(
					shaders = {
						"output" : IECoreScene.Shader( "PxrDomeLight", "ri:light", { "exposure" : 4.0 } ),
					},
					output = "output",
				),
				"ri:visibility:camera" : IECore.BoolData( False ),
			} ) )
		)

		renderer.render()
		time.sleep( 1 )
		renderer.pause()

		image = IECoreImage.ImageDisplayDriver.storedImage( "myLovelySphere" )
		self.assertEqual( self.__colorAtUV( image, imath.V2f( 0.3, 0.5 ) )[0], 0 )
		self.assertGreater( self.__colorAtUV( image, imath.V2f( 0.6, 0.5 ) )[0], 0.5 )

		del sphere, portal, dome
		del renderer

	def testMeshLight( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"RenderMan",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Interactive
		)

		renderer.output(
			"test",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ImageDisplayDriver",
					"handle" : "meshLightTest",
				}
			)
		)

		sphere = renderer.object(
			"sphere",
			IECoreScene.SpherePrimitive(),
			renderer.attributes( IECore.CompoundObject( {
				"ri:surface" : IECoreScene.ShaderNetwork(
					shaders = {
						"output" : IECoreScene.Shader(
							"PxrDiffuse",
							parameters = {
								"diffuseColor" : imath.Color3f( 1.0, 1.0, 0.0 )
							}
						)
					},
					output = "output",
				)
			} ) )
		)
		sphere.transform( imath.M44f().translate( imath.V3f( 0, 0, -2 ) ) )

		lightShader = IECoreScene.ShaderNetwork(
			shaders = {
				"output" : IECoreScene.Shader(
					"PxrMeshLight", "ri:light",
					{ "lightColor" : imath.Color3f( 0.0, 1.0, 1.0 ) }
				),
			},
			output = "output",
		)

		light = renderer.light(
			"meshLight",
			IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) ),
			renderer.attributes( IECore.CompoundObject( { "ri:light" : lightShader } ) )
		)
		light.transform( imath.M44f().translate( imath.V3f( 1, 0, -1 ) ).rotate( imath.V3f( 0, math.pi / 2, 0 ) ) )

		renderer.render()
		time.sleep( 1 )
		renderer.pause()

		# Sphere should appear green.

		image = IECoreImage.ImageDisplayDriver.storedImage( "meshLightTest" )
		self.assertEqual( self.__colorAtUV( image, imath.V2f( 0.5, 0.5 ) )[0], 0.0 )
		self.assertGreater( self.__colorAtUV( image, imath.V2f( 0.5, 0.5 ) )[1], 0.1 )
		self.assertEqual( self.__colorAtUV( image, imath.V2f( 0.5, 0.5 ) )[2], 0.0 )
		self.assertEqual( self.__colorAtUV( image, imath.V2f( 0.5, 0.5 ) )[3], 1.0 )

		# Light is camera visible and should be cyan.

		self.assertEqual( self.__colorAtUV( image, imath.V2f( 0.75, 0.5 ) ), imath.Color4f( 0, 1, 1, 1 ) )

		# Can also assign a surface shader to lights, in which case
		# RenderMan will use it for ray hits. RenderMan seems to sum
		# this with the light shader, so adding a red surface shader
		# makes our cyan light white.

		light.attributes(
			renderer.attributes( IECore.CompoundObject( {
				"ri:light" : lightShader,
				"ri:surface" : IECoreScene.ShaderNetwork(
					shaders = {
						"output" : IECoreScene.Shader(
							"PxrConstant", "ri:surface",
							{ "emitColor" : imath.Color3f( 1.0, 0.0, 0.0 ) }
						),
					},
					output = "output",
				),
			} ) )
		)

		renderer.render()
		time.sleep( 1 )
		renderer.pause()

		image = IECoreImage.ImageDisplayDriver.storedImage( "meshLightTest" )
		self.assertEqual( self.__colorAtUV( image, imath.V2f( 0.75, 0.5 ) ), imath.Color4f( 1, 1, 1, 1 ) )

		# Make the light invisible to camera. It should continue to illuminate
		# the sphere, but no longer be visible in the render.

		light.attributes(
			renderer.attributes( IECore.CompoundObject( {
				"ri:light" : lightShader,
				"ri:visibility:camera" : IECore.BoolData( False ),
			} ) )
		)

		renderer.render()
		time.sleep( 1 )
		renderer.pause()

		# Green sphere.
		image = IECoreImage.ImageDisplayDriver.storedImage( "meshLightTest" )
		self.assertEqual( self.__colorAtUV( image, imath.V2f( 0.5, 0.5 ) )[0], 0.0 )
		self.assertGreater( self.__colorAtUV( image, imath.V2f( 0.5, 0.5 ) )[1], 0.1 )
		self.assertEqual( self.__colorAtUV( image, imath.V2f( 0.5, 0.5 ) )[2], 0.0 )
		self.assertEqual( self.__colorAtUV( image, imath.V2f( 0.5, 0.5 ) )[3], 1.0 )

		# No light in beauty.
		self.assertEqual( self.__colorAtUV( image, imath.V2f( 0.75, 0.5 ) ), imath.Color4f( 0 ) )

		del sphere, light
		del renderer

	def testConnectionToMissingShader( self ) :

		# This test doesn't assert anything, but demonstrates that making
		# a connection to a missing shader doesn't throw an exception or
		# crash. Both of which we did at one point.

		messageHandler = IECore.CapturingMessageHandler()
		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"RenderMan",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch,
			messageHandler = messageHandler
		)

		renderer.output(
			"test",
			IECoreScene.Output(
				str( self.temporaryDirectory() / "test.exr" ),
				"exr",
				"rgba",
				{
				},
			)
		)

		renderer.object(
			"sphere",
			IECoreScene.SpherePrimitive(),
			renderer.attributes( IECore.CompoundObject( {
				"ri:surface" : IECoreScene.ShaderNetwork(
					shaders = {
						"attribute" : IECoreScene.Shader( "PxrAttribute", "osl:shader", {} ),
						"output" : IECoreScene.Shader( "MissingShader", "ri:surface" ),
					},
					connections = [
						( ( "attribute", "resultRGB" ), ( "output", "emitColor" ) )
					],
					output = "output",
				),
			} ) )
		).transform( imath.M44f().translate( imath.V3f( 0, 0, -3 ) ) )

		renderer.render()

		self.assertEqual( len( messageHandler.messages ), 1 )
		self.assertEqual( messageHandler.messages[0].level, IECore.MessageHandler.Level.Warning )
		self.assertEqual( messageHandler.messages[0].message, "Unable to find shader \"MissingShader\"." )

		del renderer

	def testConnectionToOSLShader( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"RenderMan",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
		)

		fileName = str( self.temporaryDirectory() / "test.exr" )
		renderer.output(
			"test",
			IECoreScene.Output(
				fileName,
				"exr",
				"rgba",
				{
				},
			)
		)

		renderer.object(
			"sphere",
			IECoreScene.SpherePrimitive(),
			renderer.attributes( IECore.CompoundObject( {
				"ri:surface" : IECoreScene.ShaderNetwork(
					shaders = {
						"mix" : IECoreScene.Shader( "PxrMix", "osl:shader", { "color1" : imath.Color3f( 1, 1, 0 ) } ),
						"correct" : IECoreScene.Shader( "PxrColorCorrect", "osl:shader" ),
						"output" : IECoreScene.Shader( "PxrConstant", "ri:surface" ),
					},
					connections = [
						( ( "mix", "resultRGB" ), ( "correct", "inputRGB" ) ),
						( ( "correct", "resultRGB" ), ( "output", "emitColor" ) ),
					],
					output = "output",
				),
			} ) )
		).transform( imath.M44f().translate( imath.V3f( 0, 0, -3 ) ) )

		renderer.render()
		del renderer

		image = OpenImageIO.ImageBuf( fileName )
		self.assertEqual( image.getpixel( 320, 240, 0 ), ( 1.0, 1.0, 0.0, 1.0 ) )

	def testBXDFConnection( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"RenderMan",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
		)

		fileName = str( self.temporaryDirectory() / "test.exr" )
		renderer.output(
			"test",
			IECoreScene.Output(
				fileName,
				"exr",
				"rgba",
				{
				},
			)
		)

		renderer.object(
			"sphere",
			IECoreScene.SpherePrimitive(),
			renderer.attributes( IECore.CompoundObject( {
				"ri:surface" : IECoreScene.ShaderNetwork(
					shaders = {
						"mix" : IECoreScene.Shader( "LamaMix", "ri:surface" ),
						"emission" : IECoreScene.Shader( "LamaEmission", "ri:surface", { "emissionColor" : imath.Color3f( 1, 2, 3 ) } ),
					},
					connections = [
						( ( "emission", "bxdf_out" ), ( "mix", "material1" ) ),
					],
					output = "mix",
				),
			} ) )
		).transform( imath.M44f().translate( imath.V3f( 0, 0, -3 ) ) )

		renderer.render()
		del renderer

		image = OpenImageIO.ImageBuf( fileName )
		self.assertEqual( image.getpixel( 320, 240, 0 ), ( 1.0, 2.0, 3.0, 1.0 ) )

	def testWarningForPerOutputPixelFilter( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"RenderMan",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
		)

		with IECore.CapturingMessageHandler() as mh :

			renderer.output(
				"test",
				IECoreScene.Output(
					"test.exr",
					"exr",
					"rgba",
					{
						"filter" : "gaussian",
						"filterwidth" : imath.V2f( 4, 4 ),
					},
				)
			)

		self.assertEqual( len( mh.messages ), 2 )
		for m in mh.messages :
			self.assertEqual( m.level, IECore.Msg.Level.Warning )
			self.assertIn( "Ignoring unsupported parameter", m.message )

	def testSubdivInterpolatedBoundary( self ) :

		for interpolateBoundary, expected in [
			( IECoreScene.MeshPrimitive.interpolateBoundaryNone, 0 ),
			( IECoreScene.MeshPrimitive.interpolateBoundaryEdgeAndCorner, 1 ),
			( IECoreScene.MeshPrimitive.interpolateBoundaryEdgeOnly, 2 ),
		] :

			with self.subTest( interpolateBoundary = interpolateBoundary ) :

				with IECoreRenderManTest.RileyCapture() as capture :

					renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
						"RenderMan",
						GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
					)

					mesh = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) )
					mesh.setInterpolation( "catmullClark" )
					mesh.setInterpolateBoundary( interpolateBoundary )

					renderer.object(
						"mesh", mesh, renderer.attributes( IECore.CompoundObject() )
					)

					del mesh, renderer

				proto = next(
					x for x in capture.json if x["method"] == "CreateGeometryPrototype"
				)
				self.__assertInTags(
					proto, "interpolateboundary", intArgs = [ expected ]
				)

	def testSubdivFaceVaryingLinearInterpolation( self ) :

		for faceVaryingLinearInterpolation, expected in [
			( IECoreScene.MeshPrimitive.faceVaryingLinearInterpolationNone, 2 ),
			( IECoreScene.MeshPrimitive.faceVaryingLinearInterpolationCornersOnly, 1 ),
			( IECoreScene.MeshPrimitive.faceVaryingLinearInterpolationCornersPlus1, 1 ),
			( IECoreScene.MeshPrimitive.faceVaryingLinearInterpolationCornersPlus2, 1 ),
			( IECoreScene.MeshPrimitive.faceVaryingLinearInterpolationBoundaries, 3 ),
			( IECoreScene.MeshPrimitive.faceVaryingLinearInterpolationAll, 0 ),
		] :

			with self.subTest( faceVaryingLinearInterpolation = faceVaryingLinearInterpolation ) :

				with IECoreRenderManTest.RileyCapture() as capture :

					renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
						"RenderMan",
						GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
					)

					mesh = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) )
					mesh.setInterpolation( "catmullClark" )
					mesh.setFaceVaryingLinearInterpolation( faceVaryingLinearInterpolation )

					renderer.object(
						"mesh", mesh, renderer.attributes( IECore.CompoundObject() )
					)

					del mesh, renderer

				proto = next(
					x for x in capture.json if x["method"] == "CreateGeometryPrototype"
				)
				self.__assertInTags(
					proto, "facevaryinginterpolateboundary", intArgs = [ expected ]
				)

	def testSubdivTriangleSubdivisionRule( self ) :

		for rule, expected in [
			( IECoreScene.MeshPrimitive.triangleSubdivisionRuleCatmullClark, 0 ),
			( IECoreScene.MeshPrimitive.triangleSubdivisionRuleSmooth, 2 ),
		] :

			with self.subTest( rule = rule ) :

				with IECoreRenderManTest.RileyCapture() as capture :

					renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
						"RenderMan",
						GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
					)

					mesh = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) )
					mesh.setInterpolation( "catmullClark" )
					mesh.setTriangleSubdivisionRule( rule )

					renderer.object(
						"mesh", mesh, renderer.attributes( IECore.CompoundObject() )
					)

					del mesh, renderer

				proto = next(
					x for x in capture.json if x["method"] == "CreateGeometryPrototype"
				)
				self.__assertInTags(
					proto, "smoothtriangles", intArgs = [ expected ]
				)

	def testSubdivisionScheme( self ) :

		for interpolation, scheme in [
			( IECoreScene.MeshPrimitive.interpolationLinear, None ),
			( IECoreScene.MeshPrimitive.interpolationCatmullClark, "catmull-clark" ),
			( IECoreScene.MeshPrimitive.interpolationLoop, "loop" ),
		] :

			with self.subTest( interpolation = interpolation ) :

				with IECoreRenderManTest.RileyCapture() as capture :

					renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
						"RenderMan",
						GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
					)

					mesh = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) )
					mesh.setInterpolation( interpolation )

					renderer.object(
						"mesh", mesh, renderer.attributes( IECore.CompoundObject() )
					)

					del mesh, renderer

				proto = next(
					x for x in capture.json if x["method"] == "CreateGeometryPrototype"
				)

				if scheme is not None :
					self.assertEqual( proto["type"], "Ri:SubdivisionMesh" )
					self.__assertPrimitiveVariableEqual( proto, "Ri:scheme", [ scheme ] )
				else :
					self.__assertNotInPrimitiveVariables( proto, "Ri:scheme" )
					self.assertEqual( proto["type"], "Ri:PolygonMesh" )

	def testAutomaticInstancingAttribute( self ) :

		for instancingEnabled in ( True, False ) :
			with self.subTest( instancingEnabled = instancingEnabled ) :
				with IECoreRenderManTest.RileyCapture() as capture :

					renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
						"RenderMan",
						GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
					)

					mesh = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) )
					attributes = renderer.attributes( IECore.CompoundObject( { "gaffer:automaticInstancing" : IECore.BoolData( instancingEnabled ) } )  )
					for i in range( 0, 10 ) :
						renderer.object( f"mesh{i}", mesh, attributes )

					del renderer

				self.assertEqual(
					sum( 1 for x in capture.json if x["method"] == "CreateGeometryPrototype" ),
					1 if instancingEnabled else 10
				)
				self.assertEqual(
					sum( 1 for x in capture.json if x["method"] == "CreateGeometryInstance" ),
					10
				)

	def testPrototypeAndInstanceAttributes( self ) :

		with IECoreRenderManTest.RileyCapture() as capture :

			renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
				"RenderMan",
				GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
			)

			mesh = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) )
			attributes = renderer.attributes(
				IECore.CompoundObject( {
					"ri:shade:minsamples" : IECore.IntData( 5 ),
					"ri:polygon:concave" : IECore.BoolData( 1 ),
				} )
			)
			renderer.object( "mesh", mesh, attributes )

			del renderer

		prototype = next(
			x for x in capture.json if x["method"] == "CreateGeometryPrototype"
		)

		self.__assertPrimitiveVariableEqual( prototype, "polygon:concave", [ 1 ] )
		self.__assertNotInPrimitiveVariables( prototype, "shade:minsamples" )

		instance = next(
			x for x in capture.json if x["method"] == "CreateGeometryInstance"
		)
		self.__assertParameterEqual( instance["attributes"]["params"], "shade:minsamples", [ 5 ] )
		self.__assertNotInParameters( instance["attributes"]["params"], "polygon:concave" )

	def testAutomaticInstancingRespectsPrototypeAttributes( self ) :

		with IECoreRenderManTest.RileyCapture() as capture :

			renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
				"RenderMan",
				GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
			)

			mesh = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) )
			concaveAttributes = renderer.attributes(
				IECore.CompoundObject( {
					"ri:polygon:concave" : IECore.BoolData( 1 ),
				} )
			)
			convexAttributes = renderer.attributes(
				IECore.CompoundObject( {
					"ri:polygon:concave" : IECore.BoolData( 0 ),
				} )
			)

			renderer.object( "concave1", mesh, concaveAttributes )
			renderer.object( "convex1", mesh, convexAttributes )
			renderer.object( "concave2", mesh, concaveAttributes )
			renderer.object( "convex2", mesh, convexAttributes )

			del renderer

		prototypes = [ x for x in capture.json if x["method"] == "CreateGeometryPrototype" ]
		self.assertEqual( len( prototypes ), 2 )
		self.__assertPrimitiveVariableEqual( prototypes[0], "polygon:concave", [ 1 ] )
		self.__assertPrimitiveVariableEqual( prototypes[1], "polygon:concave", [ 0 ] )

		instances = [ x for x in capture.json if x["method"] == "CreateGeometryInstance" ]
		self.assertEqual( len( instances ), 4 )
		self.assertEqual( instances[0]["geoMasterId"], prototypes[0]["result"] )
		self.assertEqual( instances[1]["geoMasterId"], prototypes[1]["result"] )
		self.assertEqual( instances[2]["geoMasterId"], prototypes[0]["result"] )
		self.assertEqual( instances[3]["geoMasterId"], prototypes[1]["result"] )

	def testChangingPrototypeAttributesCausesEditFailure( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"RenderMan",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Interactive
		)

		mesh = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) )
		concaveAttributes = renderer.attributes(
			IECore.CompoundObject( {
				"ri:polygon:concave" : IECore.BoolData( 1 ),
			} )
		)
		meshObject = renderer.object( "mesh", mesh, concaveAttributes )

		# Can change instance-level attributes OK.
		concaveAttributesPlus = renderer.attributes(
			IECore.CompoundObject( {
				"ri:polygon:concave" : IECore.BoolData( True ),
				"ri:visibility:camera" : IECore.BoolData( False ),
			} )
		)
		self.assertTrue( meshObject.attributes( concaveAttributesPlus ) )

		# But changing prototype-level attribute should cause edit failure.
		convexAttributes = renderer.attributes(
			IECore.CompoundObject( {
				"ri:polygon:concave" : IECore.BoolData( False ),
				"ri:visibility:camera" : IECore.BoolData( False ),
			} )
		)
		self.assertFalse( meshObject.attributes( convexAttributes ) )

		del meshObject, concaveAttributes, concaveAttributesPlus, convexAttributes, renderer

	def testDisplacement( self ) :

		with IECoreRenderManTest.RileyCapture() as capture :

			renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
				"RenderMan",
				GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
			)

			mesh = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) )

			displacementAttributes1 = renderer.attributes(
				IECore.CompoundObject( {
					"osl:displacement" : IECoreScene.ShaderNetwork(
						shaders = {
							"output" : IECoreScene.Shader( "PxrDisplace", "osl:displacement", { "dispAmount" : 1.0 } )
						},
						output = ( "output", "result" )
					),
				} )
			)

			displacementAttributes2 = renderer.attributes(
				IECore.CompoundObject( {
					"osl:displacement" : IECoreScene.ShaderNetwork(
						shaders = {
							"output" : IECoreScene.Shader( "PxrDisplace", "osl:displacement", { "dispAmount" : 2.0 } )
						},
						output = ( "output", "result" )
					),
				} )
			)

			renderer.object( "mesh1A", mesh, displacementAttributes1 )
			renderer.object( "mesh2A", mesh, displacementAttributes2 )
			renderer.object( "mesh1B", mesh, displacementAttributes1 )
			renderer.object( "mesh2B", mesh, displacementAttributes2 )

			del renderer

		displacements = [ x for x in capture.json if x["method"] == "CreateDisplacement" ]
		self.assertEqual( len( displacements ), 2 )

		prototypes = [ x for x in capture.json if x["method"] == "CreateGeometryPrototype" ]
		self.assertEqual( len( prototypes ), 2 )
		self.assertEqual( prototypes[0]["displacementId"], displacements[0]["result"] )
		self.assertEqual( prototypes[1]["displacementId"], displacements[1]["result"] )

		instances = [ x for x in capture.json if x["method"] == "CreateGeometryInstance" ]
		self.assertEqual( len( instances ), 4 )
		self.assertEqual( instances[0]["geoMasterId"], prototypes[0]["result"] )
		self.assertEqual( instances[1]["geoMasterId"], prototypes[1]["result"] )
		self.assertEqual( instances[2]["geoMasterId"], prototypes[0]["result"] )
		self.assertEqual( instances[3]["geoMasterId"], prototypes[1]["result"] )

	def testTransformMotionBlur( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"RenderMan",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
		)

		# RenderMan needs the shutter upfront when the Riley object is created,
		# so until we can come up with something, the renderer client is responsible
		# for passing the shutter separately from the camera.
		renderer.option( "ri:Ri:Shutter", IECore.V2fData( imath.V2f( 0, 1 ) ) )

		renderer.output(
			"test",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ImageDisplayDriver",
					"handle" : "transformMotion",
				}
			)
		)

		object = renderer.object(
			"sphere",
			IECoreScene.SpherePrimitive( 1 ),
			renderer.attributes( IECore.CompoundObject() )
		)
		object.transform(
			[ imath.M44f().translate( imath.V3f( x, 0, -3 ) ) for x in [ -3, 3 ] ],
			[ 0.0, 1.0 ],
		)

		renderer.render()

		image = IECoreImage.ImageDisplayDriver.storedImage( "transformMotion" )

		for i in range( 0, 10 ) :
			u = i / 9.0
			self.assertEqual( self.__colorAtUV( image, imath.V2f( u, 0.1 ) ).a, 0 )
			self.assertGreaterEqual( self.__colorAtUV( image, imath.V2f( u, 0.5 ) ).a, 0.1 )
			self.assertEqual( self.__colorAtUV( image, imath.V2f( u, 0.9 ) ).a, 0 )

	def testUnknownCommands( self ) :

		messageHandler = IECore.CapturingMessageHandler()
		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"RenderMan",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch,
			messageHandler = messageHandler
		)

		renderer.command( "ri:unknown", {} )
		self.assertEqual( len( messageHandler.messages ), 1 )
		self.assertEqual( messageHandler.messages[0].level, IECore.Msg.Level.Warning )
		self.assertEqual( messageHandler.messages[0].message, 'Unknown command "ri:unknown".' )

		renderer.command( "unknown", {} )
		self.assertEqual( len( messageHandler.messages ), 2 )
		self.assertEqual( messageHandler.messages[1].level, IECore.Msg.Level.Warning )
		self.assertEqual( messageHandler.messages[1].message, 'Unknown command "unknown".' )

		renderer.command( "ai:unknown", {} ) # Shouldn't warn, because command is for another renderer.
		self.assertEqual( len( messageHandler.messages ), 2 )

	def testNoOutputs( self ) :

		messageHandler = IECore.CapturingMessageHandler()
		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"RenderMan",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch,
			messageHandler = messageHandler
		)
		renderer.render()

		self.assertEqual( len( messageHandler.messages ), 1 )
		self.assertEqual( messageHandler.messages[0].level, IECore.Msg.Level.Warning )
		self.assertEqual( messageHandler.messages[0].context, "IECoreRenderMan" )
		self.assertEqual( messageHandler.messages[0].message, "No outputs defined." )


	def testLPELobeOptions( self ) :

		with IECoreRenderManTest.RileyCapture() as capture :

			renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
				"RenderMan",
				GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
			)

			renderer.option( "ri:lpe:user1", IECore.StringData( "test" ) )
			renderer.option( "ri:lpe:diffuse3", None )

			renderer.object(
				"sphere", IECoreScene.SpherePrimitive(), renderer.attributes( IECore.CompoundObject() )
			)

			del renderer

		options = next(
			x for x in capture.json if x["method"] == "SetOptions"
		)["sceneOptions"]["params"]

		# Default.
		self.__assertParameterEqual( options, "lpe:diffuse2", [ "Diffuse,HairDiffuse,diffuse,translucent,hair4,irradiance" ] )
		# Set explicitly.
		self.__assertParameterEqual( options, "lpe:user1", [ "test" ] )
		# Set to default explicitly.
		self.__assertParameterEqual( options, "lpe:diffuse3", [ "Subsurface,subsurface" ] )

	def testDisplayFilter( self ):

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"RenderMan",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Interactive
		)

		renderer.output(
			"test",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ImageDisplayDriver",
					"handle" : "testDisplayFilter",
				}
			)
		)

		# First test without any display filters.

		renderer.render()
		time.sleep( 1 )
		renderer.pause()

		image = IECoreImage.ImageDisplayDriver.storedImage( "testDisplayFilter" )
		self.assertEqual( self.__colorAtUV( image, imath.V2i( 0.5 ) ), imath.Color4f( 0 ) )

		# Then apply a single display filter.

		renderer.option(
			"ri:displayfilter",
			IECoreScene.ShaderNetwork(
				shaders = {
					"output" : IECoreScene.Shader(
						"PxrBackgroundDisplayFilter", "ri:displayfilter",
						{
							"backgroundColor" : imath.Color3f( 1, 0, 0 ),
						}
					),
				},
				output = "output"
			)
		)

		renderer.render()
		time.sleep( 1 )
		renderer.pause()

		image = IECoreImage.ImageDisplayDriver.storedImage( "testDisplayFilter" )
		self.assertEqual( self.__colorAtUV( image, imath.V2i( 0.5 ) ), imath.Color4f( 1, 0, 0, 0 ) )

		# And finally a combined one, the grade filter should apply after the background.

		renderer.option(
			"ri:displayfilter",
			IECoreScene.ShaderNetwork(
				shaders = {
					"combiner" : IECoreScene.Shader(
						"PxrDisplayFilterCombiner", "ri:displayfilter",
					),
					"background" : IECoreScene.Shader(
						"PxrBackgroundDisplayFilter", "ri:displayfilter",
						{
							"backgroundColor" : imath.Color3f( 1, 0, 0 ),
						}
					),
					"grade" : IECoreScene.Shader(
						"PxrGradeDisplayFilter", "ri:displayfilter",
						{
							"multiply" : imath.Color3f( 0.5 ),
						}
					),
				},
				connections = [
						( ( "background", "out" ), ( "combiner", "filter[0]" ) ),
						( ( "grade", "out" ), ( "combiner", "filter[1]" ) ),
				],
				output = "combiner"
			)
		)

		renderer.render()
		time.sleep( 1 )
		image = IECoreImage.ImageDisplayDriver.storedImage( "testDisplayFilter" )
		self.assertEqual( self.__colorAtUV( image, imath.V2i( 0.5 ) ), imath.Color4f( 0.5, 0, 0, 0 ) )

		del renderer

	def testSampleFilter( self ):

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"RenderMan",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Interactive
		)

		renderer.output(
			"test",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ImageDisplayDriver",
					"handle" : "testSampleFilter",
				}
			)
		)

		# First test without any sample filters.

		renderer.render()
		time.sleep( 1 )
		renderer.pause()

		image = IECoreImage.ImageDisplayDriver.storedImage( "testSampleFilter" )
		self.assertEqual( self.__colorAtUV( image, imath.V2i( 0.5 ) ), imath.Color4f( 0 ) )

		# Then apply a single sample filter.

		renderer.option(
			"ri:samplefilter",
			IECoreScene.ShaderNetwork(
				shaders = {
					"output" : IECoreScene.Shader(
						"PxrBackgroundSampleFilter", "ri:samplefilter",
						{
							"backgroundColor" : imath.Color3f( 1, 0, 0 ),
						}
					),
				},
				output = "output"
			)
		)

		renderer.render()
		time.sleep( 1 )
		renderer.pause()

		image = IECoreImage.ImageDisplayDriver.storedImage( "testSampleFilter" )
		self.assertEqual( self.__colorAtUV( image, imath.V2i( 0.5 ) ), imath.Color4f( 1, 0, 0, 0 ) )

		# And finally a combined one, the grade filter should apply after the background.

		renderer.option(
			"ri:samplefilter",
			IECoreScene.ShaderNetwork(
				shaders = {
					"combiner" : IECoreScene.Shader(
						"PxrSampleFilterCombiner", "ri:samplefilter"
					),
					"background" : IECoreScene.Shader(
						"PxrBackgroundSampleFilter", "ri:samplefilter",
						{
							"backgroundColor" : imath.Color3f( 1, 0, 0 ),
						}
					),
					"grade" : IECoreScene.Shader(
						"PxrGradeSampleFilter", "ri:samplefilter",
						{
							"multiply" : imath.Color3f( 0.5 ),
						}
					),
				},
				connections = [
						( ( "background", "out" ), ( "combiner", "filter[0]" ) ),
						( ( "grade", "out" ), ( "combiner", "filter[1]" ) ),
				],
				output = "combiner"
			)
		)

		renderer.render()
		time.sleep( 1 )
		image = IECoreImage.ImageDisplayDriver.storedImage( "testSampleFilter" )
		self.assertEqual( self.__colorAtUV( image, imath.V2i( 0.5 ) ), imath.Color4f( 0.5, 0, 0, 0 ) )

		del renderer

	def __assertParameterEqual( self, paramList, name, data ) :

		p = next( x for x in paramList if x["info"]["name"] == name )
		self.assertEqual( p["data"], data )

	def __assertNotInParameters( self, paramList, name ) :

		self.assertNotIn(
			name, { x["info"]["name"] for x in paramList }
		)

	def __assertPrimitiveVariableEqual( self, geometryPrototype, name, data ) :

		self.__assertParameterEqual( geometryPrototype["primvars"]["params"], name, data )

	def __assertNotInPrimitiveVariables( self, geometryPrototype, name ) :

		self.__assertNotInParameters( geometryPrototype["primvars"]["params"], name )

	def __assertInTags( self, geometryPrototype, tag, intArgs = [], floatArgs = [] ) :

		tags = next( x for x in geometryPrototype["primvars"]["params"] if x["info"]["name"] == "Ri:subdivtags" )["data"]
		numArgs = next( x for x in geometryPrototype["primvars"]["params"] if x["info"]["name"] == "Ri:subdivtagnargs" )["data"]
		ints = next( x for x in geometryPrototype["primvars"]["params"] if x["info"]["name"] == "Ri:subdivtagintargs" )["data"]
		floats = next( x for x in geometryPrototype["primvars"]["params"] if x["info"]["name"] == "Ri:subdivtagfloatargs" )["data"]

		foundTag = False
		for t in tags :

			if t == tag :
				self.assertEqual( numArgs[0:3], [ len( intArgs ), len( floatArgs ), 0 ] )
				self.assertEqual( ints[0:len(intArgs)], intArgs )
				self.assertEqual( floats[0:len(floatArgs)], floatArgs )
				foundTag = True

			# Move to next tag
			del ints[0:numArgs[0]]
			del floats[0:numArgs[1]]
			del numArgs[0:3]

		self.assertEqual( len( numArgs ), 0 )
		self.assertEqual( len( ints ), 0 )
		self.assertEqual( len( floats ), 0 )

		self.assertTrue( foundTag )

	def __colorAtUV( self, image, uv ) :

		dimensions = image.dataWindow.size() + imath.V2i( 1 )

		ix = int( uv.x * ( dimensions.x - 1 ) )
		iy = int( uv.y * ( dimensions.y - 1 ) )
		i = iy * dimensions.x + ix

		return imath.Color4f( image["R"][i], image["G"][i], image["B"][i], image["A"][i] if "A" in image.keys() else 0.0 )

if __name__ == "__main__":
	unittest.main()
