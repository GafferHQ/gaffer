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
import os
import time
import unittest
import random
import itertools
import subprocess

import imath

import OpenImageIO

import IECore
import IECoreImage
import IECoreScene
import IECoreRenderMan
import IECoreRenderManTest
import IECoreVDB

import GafferTest
import GafferScene

@unittest.skipIf( GafferTest.inCI() and os.name == "nt", "RenderMan cannot get license on Windows.")
class RendererTest( GafferTest.TestCase ) :

	renderer = "RenderMan"

	def testFactory( self ) :

		self.assertTrue( self.renderer in GafferScene.Private.IECoreScenePreview.Renderer.types() )

		r = GafferScene.Private.IECoreScenePreview.Renderer.create( self.renderer )
		self.assertTrue( isinstance( r, GafferScene.Private.IECoreScenePreview.Renderer ) )

	def testTwoRenderers( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create( self.renderer )
		# This looks unused, but is needed to trigger the deferred creation of
		# the Riley session.
		attributes = renderer.attributes( IECore.CompoundObject() )

		with self.assertRaisesRegex( RuntimeError, "RenderMan doesn't allow multiple active sessions" ) as handler :
			# RenderMan only allows there to be one renderer at a time.
			GafferScene.Private.IECoreScenePreview.Renderer.create( self.renderer )

		handler.exception.__traceback__ = None

		del attributes
		del renderer

	def testSceneDescription( self ) :

		with self.assertRaisesRegex( RuntimeError, "SceneDescription mode not supported" ) :
			GafferScene.Private.IECoreScenePreview.Renderer.create(
				self.renderer,
				GafferScene.Private.IECoreScenePreview.Renderer.RenderType.SceneDescription,
				( self.temporaryDirectory() / "test.rib" ).as_posix()
			)

	def testOutput( self ) :

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			self.renderer,
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
			self.renderer,
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

	def testProgress( self ) :

		messageHandler = IECore.CapturingMessageHandler()
		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			self.renderer,
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch,
			messageHandler = messageHandler
		)

		renderer.output(
			"beauty",
			IECoreScene.Output(
				( self.temporaryDirectory() / "beauty.exr" ).as_posix(),
				"exr",
				"rgba",
				{
				}
			)
		)

		renderer.option( "ri:progressMode", IECore.IntData( 2 ) )
		renderer.render()

		self.assertRegex( "".join( [ m.message for m in messageHandler.messages ] ), "R90000.*%" )

	def testMissingLightShader( self ) :

		messageHandler = IECore.CapturingMessageHandler()
		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			self.renderer,
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

		self.assertGreater( len( messageHandler.messages ), 0 )
		self.assertTrue(
			{ m.message for m in messageHandler.messages }.issubset( {
				# Message we output ourselves.
				"Unable to find shader \"BadShader\".",
				# Message that XPU emits but RIS doesn't.
				"W00045 A light shader could not be created because there were no light nodes.",
			} )
		)

		del lightAttributes
		del light
		del renderer

	def testIntegratorEdit( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			self.renderer,
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

		self.assertEventually(
			lambda : self.assertEqualWithAbsError( self.__colorAtUV( "myLovelySphere", imath.V2i( 0.5 ) ), imath.Color4f( 1 ), error = 0.01 )
		)

		renderer.pause()

		renderer.option(
			"ri:integrator",
			IECoreScene.ShaderNetwork(
				shaders = {
					"integrator" : IECoreScene.Shader(
						"PxrVisualizer", "ri:integrator",
						{
							"style" : "normals",
							"wireframe" : False,
						}
					),
				},
				output = "integrator"
			)
		)

		renderer.render()

		self.assertEventually(
			lambda : self.assertEqualWithAbsError( self.__colorAtUV( "myLovelySphere", imath.V2i( 0.5 ) ), imath.Color4f( 0, 0.514107, 0, 1 ), error = 0.01 )
		)

		renderer.pause()

		del object
		del renderer

	def testEXRLayerNames( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			self.renderer,
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
			self.renderer,
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
			self.renderer,
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
			self.renderer,
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
			self.renderer,
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
			self.renderer,
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

	def testUserAttributeValues( self ) :

		with IECoreRenderManTest.RileyCapture() as capture :

			renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
				self.renderer,
				GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
			)

			renderer.object(
				"sphere",
				IECoreScene.SpherePrimitive(),
				renderer.attributes( IECore.CompoundObject( {
					"user:testBool" : IECore.BoolData( False ),
					"user:testInt" : IECore.IntData( 1 ),
					"user:testFloat" : IECore.FloatData( 2.5 ),
					"user:testString" : IECore.StringData( "test" ),
					"user:testInternedString" : IECore.StringData( "test" ),
					"user:testColor" : IECore.Color3fData( imath.Color3f( 1, 2, 3 ) ),
					"user:testV2i" : IECore.V2iData( imath.V2i( 1, 2 ) ),
					"user:testV2f" : IECore.V2fData( imath.V2f( 1.5, 2.5 ) ),
					"user:testM44f" : IECore.M44fData( imath.M44f().translate( imath.V3f( 1, 2, 3 ) ) ),
					"user:testM44d" : IECore.M44dData( imath.M44d().scale( imath.V3d( 1, 2, 3 ) ) ),
					"user:testIntArray" : IECore.IntVectorData( [ 3, 2, 1 ] ),
					"user:testFloatArray" : IECore.FloatVectorData( [ 3.5, 2.5, 1.5 ] ),
					"user:testStringArray" : IECore.StringVectorData( [ "a", "b", "c" ] ),
					"user:testInternedStringArray" : IECore.InternedStringVectorData( [ "a", "b", "c" ] ),
					"user:testColorArray" : IECore.Color3fVectorData( [ imath.Color3f( x, x, x ) for x in range( 0, 3 ) ] ),
					"user:testVectorArray" : IECore.V3fVectorData( [ imath.V3f( x, x, x ) for x in range( 0, 3 ) ] ),
				} ) )
			)

			del renderer

		attributes = next( x for x in capture.json if x["method"] == "CreateGeometryInstance" )["attributes"]["params"]
		self.__assertParameterEqual( attributes, "user:testBool", [ 0 ] )
		self.__assertParameterEqual( attributes, "user:testInt", [ 1 ] )
		self.__assertParameterEqual( attributes, "user:testFloat", [ 2.5 ] )
		self.__assertParameterEqual( attributes, "user:testString", [ "test" ] )
		self.__assertParameterEqual( attributes, "user:testInternedString", [ "test" ] )
		self.__assertParameterEqual( attributes, "user:testColor", [ 1.0, 2.0, 3.0 ] )
		self.__assertParameterEqual( attributes, "user:testV2i", [ 1, 2 ] )
		self.__assertParameterEqual( attributes, "user:testV2f", [ 1.5, 2.5 ] )
		self.__assertParameterEqual( attributes, "user:testM44f", [ 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 2, 3, 1 ] )
		self.__assertParameterEqual( attributes, "user:testM44d", [ 1, 0, 0, 0, 0, 2, 0, 0, 0, 0, 3, 0, 0, 0, 0, 1 ] )
		self.__assertParameterEqual( attributes, "user:testIntArray", [ 3, 2, 1 ] )
		self.__assertParameterEqual( attributes, "user:testFloatArray", [ 3.5, 2.5, 1.5 ] )
		self.__assertParameterEqual( attributes, "user:testStringArray", [ "a", "b", "c" ] )
		self.__assertParameterEqual( attributes, "user:testInternedStringArray", [ "a", "b", "c" ] )
		self.__assertParameterEqual( attributes, "user:testColorArray", [ 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 2.0, 2.0, 2.0 ] )
		self.__assertParameterEqual( attributes, "user:testVectorArray", [ 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 2.0, 2.0, 2.0 ] )

	def testUserAttributeRendering( self ) :

		for attributeName, lookupName, array in [
			( "render:displayColor", "displayColor", False ),
			( "render:displayColor", "displayColor", True ),
			( "user:myColor", "user:myColor", False ),
		] :

			with self.subTest( attributeName = attributeName, lookupName = lookupName, array = array ) :

				renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
					self.renderer,
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
										"varname" : lookupName,
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
						attributeName : IECore.Color3fVectorData( [ imath.Color3f( 1, 0.5, 0.25 ) ] ) if array else IECore.Color3fData( imath.Color3f( 1, 0.5, 0.25 ) ),
					} ) )
				).transform( imath.M44f().translate( imath.V3f( 0, 0, -3 ) ) )

				renderer.render()
				del renderer

				image = OpenImageIO.ImageBuf( fileName )
				self.assertEqual( image.getpixel( 320, 240, 0 ), ( 1.0, 0.5, 0.25, 1.0 ) )

	def testArrayConnections( self ) :

		with IECoreRenderManTest.RileyCapture() as capture :

			renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
				self.renderer,
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
			self.renderer,
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

		# We should be illuminating the whole sphere.

		self.assertEventually(
			lambda : self.assertGreater( self.__colorAtUV( "myLovelySphere", imath.V2f( 0.3, 0.5 ) )[0], 0.5 )
		)
		self.assertEventually(
			lambda : self.assertGreater( self.__colorAtUV( "myLovelySphere", imath.V2f( 0.6, 0.5 ) )[0], 0.5 )
		)

		renderer.pause()

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
		# We should only be illuminating the side the portal is on.

		self.assertEventually(
			lambda : self.assertEqual( self.__colorAtUV( "myLovelySphere", imath.V2f( 0.3, 0.5 ) )[0], 0 )
		)
		self.assertEventually(
			lambda : self.assertGreater( self.__colorAtUV( "myLovelySphere", imath.V2f( 0.6, 0.5 ) )[0], 0.5 )
		)

		renderer.pause()

		# Delete the portal light. We should be back to illuminating
		# on both sides.

		del portal
		renderer.render()

		self.assertEventually(
			lambda : self.assertGreater( self.__colorAtUV( "myLovelySphere", imath.V2f( 0.4, 0.5 ) )[0], 0.5 )
		)
		self.assertEventually(
			lambda : self.assertGreater( self.__colorAtUV( "myLovelySphere", imath.V2f( 0.6, 0.5 ) )[0], 0.5 )
		)

		renderer.pause()

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

		self.assertEventually(
			lambda : self.assertEqual( self.__colorAtUV( "myLovelySphere", imath.V2f( 0.3, 0.5 ) )[0], 0 )
		)
		self.assertEventually(
			lambda : self.assertEqualWithAbsError( self.__colorAtUV( "myLovelySphere", imath.V2f( 0.6, 0.5 ) ), imath.Color4f( 1 ), 0.02 )
		)

		renderer.pause()

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

		self.assertEventually(
			lambda : self.assertEqualWithAbsError( self.__colorAtUV( "myLovelySphere", imath.V2f( 0.6, 0.5 ) ), imath.Color4f( 2, 0, 2, 1 ), 0.04 )
		)
		self.assertEventually(
			lambda : self.assertEqual( self.__colorAtUV( "myLovelySphere", imath.V2f( 0.3, 0.5 ) )[0], 0 )
		)

		renderer.pause()

		# Now delete the dome light. We should get no illumination at all.

		del dome
		renderer.render()

		self.assertEventually(
			lambda : self.assertEqual( self.__colorAtUV( "myLovelySphere", imath.V2f( 0.6, 0.5 ) )[0], 0 )
		)
		self.assertEventually(
			lambda : self.assertEqual( self.__colorAtUV( "myLovelySphere", imath.V2f( 0.3, 0.5 ) )[0], 0 )
		)

		renderer.pause()

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

		self.assertEventually(
			lambda : self.assertGreater( self.__colorAtUV( "myLovelySphere", imath.V2f( 0.6, 0.5 ) )[0], 0.5 )
		)
		self.assertEventually(
			lambda : self.assertEqual( self.__colorAtUV( "myLovelySphere", imath.V2f( 0.3, 0.5 ) )[0], 0 )
		)

		renderer.pause()

		del sphere, portal, dome
		del renderer

	def testMeshLight( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			self.renderer,
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

		# Sphere should appear green.

		def assertGreenSphere() :

			image = IECoreImage.ImageDisplayDriver.storedImage( "meshLightTest" )
			self.assertEqual( self.__colorAtUV( image, imath.V2f( 0.5, 0.5 ) )[0], 0.0 )
			self.assertGreater( self.__colorAtUV( image, imath.V2f( 0.5, 0.5 ) )[1], 0.1 )
			self.assertEqual( self.__colorAtUV( image, imath.V2f( 0.5, 0.5 ) )[2], 0.0 )
			self.assertEqualWithAbsError( self.__colorAtUV( image, imath.V2f( 0.5, 0.5 ) )[3], 1.0, 0.00001 )

		self.assertEventually(
			lambda : assertGreenSphere()
		)

		# Light is camera visible and should be cyan.

		self.assertEventually(
			lambda : self.assertEqual( self.__colorAtUV( "meshLightTest", imath.V2f( 0.75, 0.5 ) ), imath.Color4f( 0, 1, 1, 1 ) )
		)

		renderer.pause()

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

		self.assertEventually(
			lambda : self.assertEqual( self.__colorAtUV( "meshLightTest", imath.V2f( 0.75, 0.5 ) ), imath.Color4f( 1, 1, 1, 1 ) )
		)

		renderer.pause()

		# Make the light invisible to camera. It should continue to illuminate
		# the sphere, but no longer be visible in the render.

		light.attributes(
			renderer.attributes( IECore.CompoundObject( {
				"ri:light" : lightShader,
				"ri:visibility:camera" : IECore.BoolData( False ),
			} ) )
		)

		renderer.render()

		# No light in beauty.
		self.assertEventually(
			lambda : self.assertEqual( self.__colorAtUV( "meshLightTest", imath.V2f( 0.75, 0.5 ) ), imath.Color4f( 0 ) )
		)

		# Green sphere.
		self.assertEventually(
			lambda : assertGreenSphere()
		)

		renderer.pause()

		del sphere, light
		del renderer

	def testConnectionToMissingShader( self ) :

		# This test doesn't assert anything, but demonstrates that making
		# a connection to a missing shader doesn't throw an exception or
		# crash. Both of which we did at one point.

		messageHandler = IECore.CapturingMessageHandler()
		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			self.renderer,
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

		self.assertGreater( len( messageHandler.messages ), 0 )
		self.assertTrue(
			{ m.message for m in messageHandler.messages }.issubset( {
				# Message we output ourselves.
				"Unable to find shader \"MissingShader\".",
				# Message that XPU emits but RIS doesn't.
				"W00053 A material : <unknown> cannot be created because there were no bxdf nodes.",
			} )
		)

		del renderer

	def testComponentConnections( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			self.renderer,
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
						"attribute" : IECoreScene.Shader( "PxrAttribute", "osl:shader", { "defaultFloat" : 0.5 } ),
						"output" : IECoreScene.Shader( "PxrConstant", "ri:surface", { "emitColor" : imath.Color3f( 0.25, 1, 0.75 ) } ),
					},
					connections = [
						( ( "attribute", "resultRGB.r" ), ( "output", "emitColor.g" ) ),
					],
					output = "output",
				),
			} ) )
		).transform( imath.M44f().translate( imath.V3f( 0, 0, -3 ) ) )

		renderer.render()
		del renderer

		image = OpenImageIO.ImageBuf( fileName )
		self.assertEqual( image.getpixel( 320, 240, 0 ), ( 0.25, 0.5, 0.75, 1.0 ) )

	def testConnectionToOSLShader( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			self.renderer,
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
			self.renderer,
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
			self.renderer,
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

	def testGeometricInterpretation( self ) :

		legacy = os.environ.get( "IECORERENDERMAN_LEGACY_TEXTURECOORDINATE_BEHAVIOUR", "0" ) == "1"

		with IECoreRenderManTest.RileyCapture() as capture :

			renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
				self.renderer,
				GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
			)

			mesh = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) )
			mesh["constantPoint"] = IECoreScene.PrimitiveVariable(
				IECoreScene.PrimitiveVariable.Interpolation.Constant,
				IECore.V3fData( imath.V3f( 0 ), IECore.GeometricData.Interpretation.Point )
			)
			mesh["vertexPoint"] = IECoreScene.PrimitiveVariable(
				IECoreScene.PrimitiveVariable.Interpolation.Vertex,
				IECore.V3fVectorData( [ imath.V3f( 0 ) ] * 4, IECore.GeometricData.Interpretation.Point )
			)
			mesh["constantVector"] = IECoreScene.PrimitiveVariable(
				IECoreScene.PrimitiveVariable.Interpolation.Constant,
				IECore.V3fData( imath.V3f( 0 ), IECore.GeometricData.Interpretation.Vector )
			)
			mesh["vertexVector"] = IECoreScene.PrimitiveVariable(
				IECoreScene.PrimitiveVariable.Interpolation.Vertex,
				IECore.V3fVectorData( [ imath.V3f( 0 ) ] * 4, IECore.GeometricData.Interpretation.Vector )
			)
			mesh["constantNormal"] = IECoreScene.PrimitiveVariable(
				IECoreScene.PrimitiveVariable.Interpolation.Constant,
				IECore.V3fData( imath.V3f( 0 ), IECore.GeometricData.Interpretation.Normal )
			)
			mesh["vertexNormal"] = IECoreScene.PrimitiveVariable(
				IECoreScene.PrimitiveVariable.Interpolation.Vertex,
				IECore.V3fVectorData( [ imath.V3f( 0 ) ] * 4, IECore.GeometricData.Interpretation.Normal )
			)
			mesh["constantFloat3"] = IECoreScene.PrimitiveVariable(
				IECoreScene.PrimitiveVariable.Interpolation.Constant,
				IECore.V3fData( imath.V3f( 0 ), IECore.GeometricData.Interpretation.Numeric )
			)
			mesh["vertexFloat3"] = IECoreScene.PrimitiveVariable(
				IECoreScene.PrimitiveVariable.Interpolation.Vertex,
				IECore.V3fVectorData( [ imath.V3f( 0 ) ] * 4, IECore.GeometricData.Interpretation.Numeric )
			)
			mesh["constantTextureCoordinate"] = IECoreScene.PrimitiveVariable(
				IECoreScene.PrimitiveVariable.Interpolation.Constant,
				IECore.V3fData( imath.V3f( 0 ), IECore.GeometricData.Interpretation.UV )
			)
			mesh["vertexTextureCoordinate"] = IECoreScene.PrimitiveVariable(
				IECoreScene.PrimitiveVariable.Interpolation.Vertex,
				IECore.V3fVectorData( [ imath.V3f( 0 ) ] * 4, IECore.GeometricData.Interpretation.UV )
			)

			attributes = IECore.CompoundObject( {
				"user:point" : IECore.V3fData( imath.V3f( 0 ), IECore.GeometricData.Interpretation.Point ),
				"user:pointArray" : IECore.V3fVectorData( [ imath.V3f( 0 ) ] * 10, IECore.GeometricData.Interpretation.Point ),
				"user:vector" : IECore.V3fData( imath.V3f( 0 ), IECore.GeometricData.Interpretation.Vector ),
				"user:vectorArray" : IECore.V3fVectorData( [ imath.V3f( 0 ) ] * 12, IECore.GeometricData.Interpretation.Vector ),
				"user:normal" : IECore.V3fData( imath.V3f( 0 ), IECore.GeometricData.Interpretation.Normal ),
				"user:normalArray" : IECore.V3fVectorData( [ imath.V3f( 0 ) ] * 3, IECore.GeometricData.Interpretation.Normal ),
				"user:float3" : IECore.V3fData( imath.V3f( 0 ), IECore.GeometricData.Interpretation.Numeric ),
				"user:float3Array" : IECore.V3fVectorData( [ imath.V3f( 0 ) ] * 5, IECore.GeometricData.Interpretation.Numeric ),
				"user:textureCoordinate" : IECore.V3fData( imath.V3f( 0 ), IECore.GeometricData.Interpretation.UV ),
				"user:textureCoordinateArray" : IECore.V3fVectorData( [ imath.V3f( 0 ) ] * 5, IECore.GeometricData.Interpretation.UV ),
			} )

			renderer.object(
				"mesh", mesh, renderer.attributes( attributes )
			)

			del mesh, renderer

		proto = next(
			x for x in capture.json if x["method"] == "CreateGeometryPrototype"
		)

		def assertExpectedParamInfo( paramInfo, dataType, length, isArray ) :

			self.assertEqual( paramInfo["type"], dataType )
			self.assertEqual( paramInfo["length"], length )
			self.assertEqual( paramInfo["array"], isArray )

		def assertExpectedPrimVar( name, dataType, length, isArray ) :

			primVar = next( x for x in proto["primvars"]["params"] if x["info"]["name"] == name )
			assertExpectedParamInfo( primVar["info"], dataType, length, isArray )

		# Matching RtDataType
		dataTypes = {
			"integer" : 0,
			"float" : 1,
			"color" : 2,
			"point" : 3,
			"vector" : 4,
			"normal" : 5
		}

		assertExpectedPrimVar( "constantPoint", dataTypes["point"], 1, False )
		assertExpectedPrimVar( "vertexPoint", dataTypes["point"], 1, False )
		assertExpectedPrimVar( "constantVector", dataTypes["vector"], 1, False )
		assertExpectedPrimVar( "vertexVector", dataTypes["vector"], 1, False )
		assertExpectedPrimVar( "constantNormal", dataTypes["normal"], 1, False )
		assertExpectedPrimVar( "vertexNormal", dataTypes["normal"], 1, False )
		assertExpectedPrimVar( "constantFloat3", dataTypes["float"], 3, True )
		assertExpectedPrimVar( "vertexFloat3", dataTypes["float"], 3, True )
		if legacy :
			assertExpectedPrimVar( "constantTextureCoordinate", dataTypes["point"], 1, False )
			assertExpectedPrimVar( "vertexTextureCoordinate", dataTypes["point"], 1, False )
		else :
			assertExpectedPrimVar( "constantTextureCoordinate", dataTypes["float"], 3, True )
			assertExpectedPrimVar( "vertexTextureCoordinate", dataTypes["float"], 3, True )

		instance = next(
			x for x in capture.json if x["method"] == "CreateGeometryInstance"
		)

		def assertExpectedAttribute( name, dataType, length, isArray ) :

			attribute = next( x for x in instance["attributes"]["params"] if x["info"]["name"] == name )
			assertExpectedParamInfo( attribute["info"], dataType, length, isArray )

		assertExpectedAttribute( "user:point", dataTypes["point"], 1, False )
		assertExpectedAttribute( "user:pointArray", dataTypes["point"], 10, True )
		assertExpectedAttribute( "user:vector", dataTypes["vector"], 1, False )
		assertExpectedAttribute( "user:vectorArray", dataTypes["vector"], 12, True )
		assertExpectedAttribute( "user:normal", dataTypes["normal"], 1, False )
		assertExpectedAttribute( "user:normalArray", dataTypes["normal"], 3, True )
		assertExpectedAttribute( "user:float3", dataTypes["float"], 3, True )
		assertExpectedAttribute( "user:float3Array", dataTypes["float"], 15, True )
		if legacy :
			assertExpectedAttribute( "user:textureCoordinate", dataTypes["point"], 1, False )
			assertExpectedAttribute( "user:textureCoordinateArray", dataTypes["point"], 5, True )
		else :
			assertExpectedAttribute( "user:textureCoordinate", dataTypes["float"], 3, True )
			assertExpectedAttribute( "user:textureCoordinateArray", dataTypes["float"], 15, True )

	def testLegacyGeometricInterpretation( self ) :

		# Launch test above in environment to trigger legacy behaviour
		# (unless we're in a legacy environment, in which case test clean
		# behaviour).

		legacy = os.environ.get( "IECORERENDERMAN_LEGACY_TEXTURECOORDINATE_BEHAVIOUR", "0" ) == "1"
		env = os.environ.copy()
		env["IECORERENDERMAN_LEGACY_TEXTURECOORDINATE_BEHAVIOUR"] = "0" if legacy else "1"

		try :
			subprocess.check_output(
				[ "gaffer" if os.name != "nt" else "gaffer.cmd", "test", "IECoreRenderManTest.RendererTest.testGeometricInterpretation" ],
				env = env, stderr = subprocess.STDOUT
			)
		except subprocess.CalledProcessError as e :
			self.fail( e.output )

	def testSubdivInterpolatedBoundary( self ) :

		for interpolateBoundary, expected in [
			( IECoreScene.MeshPrimitive.interpolateBoundaryNone, 0 ),
			( IECoreScene.MeshPrimitive.interpolateBoundaryEdgeAndCorner, 1 ),
			( IECoreScene.MeshPrimitive.interpolateBoundaryEdgeOnly, 2 ),
		] :

			with self.subTest( interpolateBoundary = interpolateBoundary ) :

				with IECoreRenderManTest.RileyCapture() as capture :

					renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
						self.renderer,
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
						self.renderer,
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
						self.renderer,
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
						self.renderer,
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

	def testCurvesWrap( self ) :

		Wrap = IECoreScene.CurvesPrimitive.Wrap
		for basis, wrap in [
			( IECore.CubicBasisf.catmullRom(), Wrap.Pinned ),
			( IECore.CubicBasisf.bSpline(), Wrap.Pinned ),
			( IECore.CubicBasisf.linear(), Wrap.Pinned ),
			( IECore.CubicBasisf.bSpline(), Wrap.Periodic ),
			( IECore.CubicBasisf.bSpline(), Wrap.NonPeriodic ),
		] :

			with self.subTest( basis = basis, wrap = wrap ) :

				with IECoreRenderManTest.RileyCapture() as capture :

					renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
						"RenderMan",
						GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch,
					)

					curves = IECoreScene.CurvesPrimitive(
						IECore.IntVectorData( [ 4 ] ), basis, wrap, IECore.V3fVectorData( [ imath.V3f( x ) for x in range( 0, 4 ) ] )
					)
					renderer.object(
						"curves", curves, renderer.attributes( IECore.CompoundObject() )
					)

					del renderer

				prototype = next(
					x for x in capture.json if x["method"] == "CreateGeometryPrototype"
				)

				if IECoreScene.CurvesAlgo.isPinned( curves ) :

					self.__assertPrimitiveVariableEqual(
						prototype, "P",
						list( itertools.chain( *[ iter( [ x, x, x ] ) for x in range( -1, 5 ) ] ) )
					)
					self.__assertPrimitiveVariableEqual( prototype, "Ri:wrap", [ "nonperiodic" ] )

				else :

					self.__assertPrimitiveVariableEqual(
						prototype, "P",
						list( itertools.chain( *[ iter( [ x, x, x ] ) for x in range( 0, 4 ) ] ) )
					)
					self.__assertPrimitiveVariableEqual( prototype, "Ri:wrap", [ "periodic" if wrap == Wrap.Periodic else "nonperiodic" ] )

	def testMatrixPrimitiveVariables( self ) :

		with IECoreRenderManTest.RileyCapture() as capture :

			renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
				self.renderer,
				GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
			)

			mesh = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) )
			mesh["constantMatrix"] = IECoreScene.PrimitiveVariable(
				IECoreScene.PrimitiveVariable.Interpolation.Constant,
				imath.M44f().translate( imath.V3f( 1, 2, 3 ) )
			)
			mesh["vertexMatrix"] = IECoreScene.PrimitiveVariable(
				IECoreScene.PrimitiveVariable.Interpolation.Vertex,
				IECore.M44fVectorData( [ imath.M44f().translate( imath.V3f( 1, 2, 3 ) ) ] * 4 )
			)

			renderer.object(
				"mesh", mesh, renderer.attributes( IECore.CompoundObject() )
			)

			del mesh, renderer

		prototype = next(
			x for x in capture.json if x["method"] == "CreateGeometryPrototype"
		)

		self.__assertPrimitiveVariableEqual( prototype, "constantMatrix", [ 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 2, 3, 1 ] )
		self.__assertPrimitiveVariableEqual( prototype, "vertexMatrix", [ 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 2, 3, 1 ] * 4 )

	def testAutomaticInstancingAttribute( self ) :

		for instancingEnabled in ( True, False ) :
			with self.subTest( instancingEnabled = instancingEnabled ) :
				with IECoreRenderManTest.RileyCapture() as capture :

					renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
						self.renderer,
						GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
					)

					mesh = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) )
					attributes = renderer.attributes( IECore.CompoundObject( { "gaffer:automaticInstancing" : IECore.BoolData( instancingEnabled ) } )  )
					for i in range( 0, 10 ) :
						renderer.object( f"mesh{i}", mesh, attributes )

					del attributes
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
				self.renderer,
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

			del attributes
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
				self.renderer,
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

			del concaveAttributes, convexAttributes
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
			self.renderer,
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
				self.renderer,
				GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
			)

			mesh = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) )

			displacementAttributes1 = renderer.attributes(
				IECore.CompoundObject( {
					"osl:displacement" : IECoreScene.ShaderNetwork(
						shaders = {
							"output" : IECoreScene.Shader( "PxrDisplace", "ri:displacement", { "dispAmount" : 1.0 } )
						},
						output = ( "output", "result" )
					),
				} )
			)

			displacementAttributes2 = renderer.attributes(
				IECore.CompoundObject( {
					"osl:displacement" : IECoreScene.ShaderNetwork(
						shaders = {
							"output" : IECoreScene.Shader( "PxrDisplace", "ri:displacement", { "dispAmount" : 2.0 } )
						},
						output = ( "output", "result" )
					),
				} )
			)

			renderer.object( "mesh1A", mesh, displacementAttributes1 )
			renderer.object( "mesh2A", mesh, displacementAttributes2 )
			renderer.object( "mesh1B", mesh, displacementAttributes1 )
			renderer.object( "mesh2B", mesh, displacementAttributes2 )

			del displacementAttributes1, displacementAttributes2
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
			self.renderer,
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

		del object
		del renderer

	def testDeformationMotionBlur( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			self.renderer,
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
					"handle" : "deformationMotion",
				}
			)
		)

		staticMesh = IECoreScene.MeshPrimitive.createSphere( 1 )
		meshes = []
		for x in [ -3, 3 ] :
			mesh = staticMesh.copy()
			for i in range( len( mesh["P"].data ) ) :
				mesh["P"].data[i] += imath.V3f( x, 0, -3 )
			meshes.append( mesh )

		object = renderer.object(
			"sphere", meshes, [ 0, 1 ],
			renderer.attributes( IECore.CompoundObject() )
		)

		renderer.render()

		image = IECoreImage.ImageDisplayDriver.storedImage( "deformationMotion" )

		for i in range( 0, 10 ) :
			u = i / 9.0
			self.assertEqual( self.__colorAtUV( image, imath.V2f( u, 0.1 ) ).a, 0 )
			self.assertGreaterEqual( self.__colorAtUV( image, imath.V2f( u, 0.5 ) ).a, 0.1 )
			self.assertEqual( self.__colorAtUV( image, imath.V2f( u, 0.9 ) ).a, 0 )

		del object
		del renderer

	def testDeformationOnlyIncludesPosition( self ) :

		with IECoreRenderManTest.RileyCapture() as capture :

			renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
				self.renderer,
				GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
			)

			renderer.option( "ri:Ri:Shutter", IECore.V2fData( imath.V2f( 0, 1 ) ) )

			staticMesh = IECoreScene.MeshPrimitive.createSphere( 1 )
			meshes = []
			for x in [ 0, 1 ] :
				mesh = staticMesh.copy()
				for i in range( len( mesh["P"].data ) ) :
					mesh["P"].data[i] += imath.V3f( x, 0, 0 )
				mesh["staticPoint"] = staticMesh["P"]
				mesh["animatedPoint"] = mesh["P"]
				mesh["staticFloat"] = IECoreScene.PrimitiveVariable(
					IECoreScene.PrimitiveVariable.Interpolation.Constant,
					IECore.FloatData( 1 )
				)
				mesh["animatedFloat"] = IECoreScene.PrimitiveVariable(
					IECoreScene.PrimitiveVariable.Interpolation.Constant,
					IECore.FloatData( x )
				)
				meshes.append( mesh )

			object = renderer.object(
				"sphere", meshes, [ 0, 1 ],
				renderer.attributes( IECore.CompoundObject() )
			)

			del object
			del renderer

		prototype = next(
			x for x in capture.json if x["method"] == "CreateGeometryPrototype"
		)
		primVars = prototype["primvars"]
		self.assertEqual( primVars["times"], [ 0, 1 ] )

		for name, expectedMotion in {
			"P" : True,
			"staticPoint" : False,
			"animatedPoint" : False,
			"staticFloat" : False,
			"animatedFloat" : False,
		}.items() :

			with self.subTest( name = name ) :

				param = next( x for x in primVars["params"] if x["info"]["name"] == name )
				self.assertEqual( param["info"]["motion"], expectedMotion )

	def testUnknownCommands( self ) :

		messageHandler = IECore.CapturingMessageHandler()
		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			self.renderer,
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
			self.renderer,
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch,
			messageHandler = messageHandler
		)
		renderer.render()

		self.assertEqual( len( messageHandler.messages ), 1 )
		self.assertEqual( messageHandler.messages[0].level, IECore.Msg.Level.Warning )
		self.assertEqual( messageHandler.messages[0].context, "IECoreRenderMan" )
		self.assertEqual( messageHandler.messages[0].message, "No outputs defined." )

	def testLightFilter( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			self.renderer,
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
					"handle" : "lightFilterTest",
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
								"diffuseColor" : imath.Color3f( 1.0 )
							}
						)
					},
					output = "output",
				)
			} ) )
		)
		sphere.transform( imath.M44f().translate( imath.V3f( 0, 0, -2 ) ) )

		def lightAttributes( exposure = 0.0 ) :

			return renderer.attributes(
				IECore.CompoundObject( {
					"ri:light" : IECoreScene.ShaderNetwork(
						shaders = {
							"output" : IECoreScene.Shader(
								"PxrDomeLight", "ri:light",
								parameters = { "exposure" : exposure }
							),
						},
						output = "output",
					),
					"ri:visibility:camera" : IECore.BoolData( False ),
				} )
			)

		light = renderer.light( "light", None, lightAttributes() )

		renderer.render()

		# No light filter yet. Sphere should appear white.

		self.assertEventually(
			lambda : self.assertEqualWithAbsError( self.__color3AtUV( "lightFilterTest", imath.V2f( 0.5, 0.5 ) ), imath.Color3f( 1 ), 0.1 )
		)

		renderer.pause()

		# Add a green light filter. Sphere should appear green.

		def lightFilterAttributes( tint ) :

			return renderer.attributes(
				IECore.CompoundObject( {
					"ri:lightFilter" : IECoreScene.ShaderNetwork(
						shaders = {
							"output" : IECoreScene.Shader(
								"PxrIntMultLightFilter", "ri:lightFilter",
								parameters = { "tint" : tint }
							),
						},
						output = "output",
					)
				} )
			)

		lightFilter = renderer.lightFilter( "filter", None, lightFilterAttributes( imath.Color3f( 0, 1, 0 ) ) )
		light.link( "lightFilters", { lightFilter } )

		renderer.render()

		self.assertEventually(
			lambda : self.assertEqualWithAbsError( self.__color3AtUV( "lightFilterTest", imath.V2f( 0.5, 0.5 ) ), imath.Color3f( 0, 1, 0 ), 0.1 )
		)

		renderer.pause()

		# Edit light filter tint. Sphere should update.

		lightFilter.attributes( lightFilterAttributes( imath.Color3f( 0, 0, 1 ) ) )

		renderer.render()

		self.assertEventually(
			lambda : self.assertEqualWithAbsError( self.__color3AtUV( "lightFilterTest", imath.V2f( 0.5, 0.5 ) ), imath.Color3f( 0, 0, 1 ), 0.1 )
		)

		renderer.pause()

		# Edit light, and make sure filter is still applied.

		light.attributes( lightAttributes( 1.0 ) )
		renderer.render()

		self.assertEventually(
			lambda : self.assertEqualWithAbsError( self.__color3AtUV( "lightFilterTest", imath.V2f( 0.5, 0.5 ) ), imath.Color3f( 0, 0, 2 ), 0.2 )
		)

		renderer.pause()

		# Remove light filter and check render is unfiltered.

		light.link( "lightFilters", None )

		renderer.render()

		self.assertEventually(
			lambda : self.assertEqualWithAbsError( self.__color3AtUV( "lightFilterTest", imath.V2f( 0.5, 0.5 ) ), imath.Color3f( 2 ), 0.2 )
		)

		renderer.pause()

		# Remove light and check render is black.

		del light

		renderer.render()

		self.assertEventually(
			lambda : self.assertEqualWithAbsError( self.__color3AtUV( "lightFilterTest", imath.V2f( 0.5, 0.5 ) ), imath.Color3f( 0 ), 0.1 )
		)

		renderer.pause()

		# Clean up.

		del sphere, lightFilter
		del renderer

	def testLightFilterTransforms( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			self.renderer,
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
					"handle" : "lightFilterTest",
				}
			)
		)

		plane = renderer.object(
			"plane",
			IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) ),
			renderer.attributes( IECore.CompoundObject( {
				"ri:surface" : IECoreScene.ShaderNetwork(
					shaders = {
						"output" : IECoreScene.Shader(
							"PxrDiffuse",
							parameters = {
								"diffuseColor" : imath.Color3f( 1.0 )
							}
						)
					},
					output = "output",
				)
			} ) )
		)
		plane.transform( imath.M44f().translate( imath.V3f( 0, 0, -2 ) ) )

		light = renderer.light(
			"light", None,
			renderer.attributes(
				IECore.CompoundObject( {
					"ri:light" : IECoreScene.ShaderNetwork(
						shaders = { "output" : IECoreScene.Shader( "PxrDomeLight", "ri:light" ) },
						output = "output",
					),
					"ri:visibility:camera" : IECore.BoolData( False ),
				} )
			)
		)

		lightFilter = renderer.lightFilter(
			"filter", None,
			renderer.attributes(
				IECore.CompoundObject( {
					"ri:lightFilter" : IECoreScene.ShaderNetwork(
						shaders = {
							"output" : IECoreScene.Shader(
								"PxrRodLightFilter"
							),
						},
						output = "output",
					)
				} )
			)
		)
		lightFilter.transform( imath.M44f().translate( imath.V3f( 0, 0, -2 ) ).scale( imath.V3f( 0.1 ) ) )
		light.link( "lightFilters", { lightFilter } )

		# Render with rod in center of plane and check expected result.

		renderer.render()

		self.assertEventually(
			lambda : self.assertEqualWithAbsError( self.__color3AtUV( "lightFilterTest", imath.V2f( 0.5, 0.5 ) ), imath.Color3f( 0 ), 0.1 )
		)
		self.assertEventually(
			lambda : self.assertEqualWithAbsError( self.__color3AtUV( "lightFilterTest", imath.V2f( 0.68, 0.5 ) ), imath.Color3f( 1 ), 0.1 )
		)

		renderer.pause()

		# Move rod to right hand side of plane, and check expected result.

		lightFilter.transform( imath.M44f().translate( imath.V3f( 1, 0, -2 ) ).scale( imath.V3f( 0.1 ) ) )
		renderer.render()

		self.assertEventually(
			lambda : self.assertEqualWithAbsError( self.__color3AtUV( "lightFilterTest", imath.V2f( 0.5, 0.5 ) ), imath.Color3f( 1 ), 0.1 )
		)
		self.assertEventually(
			lambda : self.assertEqualWithAbsError( self.__color3AtUV( "lightFilterTest", imath.V2f( 0.68, 0.5 ) ), imath.Color3f( 0 ), 0.1 )
		)

		renderer.pause()

		# Clean up.

		del plane, light, lightFilter
		del renderer

	def testLightFilterCombineModes( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			self.renderer,
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
					"handle" : "lightFilterTest",
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
								"diffuseColor" : imath.Color3f( 1.0 )
							}
						)
					},
					output = "output",
				)
			} ) )
		)
		sphere.transform( imath.M44f().translate( imath.V3f( 0, 0, -2 ) ) )

		light = renderer.light(
			"light", None,
			renderer.attributes(
				IECore.CompoundObject( {
					"ri:light" : IECoreScene.ShaderNetwork(
						shaders = { "output" : IECoreScene.Shader( "PxrDomeLight" ) },
						output = "output",
					),
					"ri:visibility:camera" : IECore.BoolData( False ),
				} )
			)
		)

		def lightFilterAttributes( tint, combineMode ) :

			return renderer.attributes(
				IECore.CompoundObject( {
					"ri:lightFilter" : IECoreScene.ShaderNetwork(
						shaders = {
							"output" : IECoreScene.Shader(
								"PxrIntMultLightFilter", "ri:lightFilter",
								parameters = { "tint" : imath.Color3f( tint ), "combineMode" : combineMode }
							),
						},
						output = "output",
					)
				} )
			)

		lightFilter1 = renderer.lightFilter(
			"lightFilter1", None, lightFilterAttributes( 0.5, "mult" )
		)

		lightFilter2 = renderer.lightFilter(
			"lightFilter2", None, lightFilterAttributes( 0.5, "mult" )
		)

		light.link( "lightFilters", { lightFilter1, lightFilter2 } )

		renderer.render()

		# `0.5 * 0.5 == 0.25`

		self.assertEventually(
			lambda : self.assertEqualWithAbsError( self.__color3AtUV( "lightFilterTest", imath.V2f( 0.5, 0.5 ) ), imath.Color3f( 0.25 ), 0.05 )
		)

		renderer.pause()

		# `min( 0.75, 0.5 ) == 0.5`

		lightFilter1.attributes( lightFilterAttributes( 0.75, "min" ) )
		lightFilter2.attributes( lightFilterAttributes( 0.5, "min" ) )

		renderer.render()

		self.assertEventually(
			lambda : self.assertEqualWithAbsError( self.__color3AtUV( "lightFilterTest", imath.V2f( 0.5, 0.5 ) ), imath.Color3f( 0.5 ), 0.05 )
		)

		renderer.pause()

		# The results from different groups are multiplied together
		# so this is also `0.5 * 0.5 == 0.25`.

		lightFilter1.attributes( lightFilterAttributes( 0.5, "max" ) )
		lightFilter2.attributes( lightFilterAttributes( 0.5, "min" ) )

		renderer.render()

		self.assertEventually(
			lambda : self.assertEqualWithAbsError( self.__color3AtUV( "lightFilterTest", imath.V2f( 0.5, 0.5 ) ), imath.Color3f( 0.25 ), 0.05 )
		)

		renderer.pause()

		# Clean up.

		del sphere, light, lightFilter1, lightFilter2
		del renderer

	def testLPELobeOptions( self ) :

		with IECoreRenderManTest.RileyCapture() as capture :

			renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
				self.renderer,
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
			self.renderer,
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

		self.assertEventually(
			lambda : self.assertEqual( self.__colorAtUV( "testDisplayFilter", imath.V2i( 0.5 ) ), imath.Color4f( 0 ) )
		)

		renderer.pause()

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

		self.assertEventually(
			lambda : self.assertEqual( self.__colorAtUV( "testDisplayFilter", imath.V2i( 0.5 ) ), imath.Color4f( 1, 0, 0, 0 ) )
		)

		renderer.pause()

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

		self.assertEventually(
			lambda : self.assertEqual( self.__colorAtUV( "testDisplayFilter", imath.V2i( 0.5 ) ), imath.Color4f( 0.5, 0, 0, 0 ) )
		)

		renderer.pause()

		del renderer

	def testSampleFilter( self ):

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			self.renderer,
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

		self.assertEventually(
			lambda : self.assertEqual( self.__colorAtUV( "testSampleFilter", imath.V2i( 0.5 ) ), imath.Color4f( 0 ) )
		)

		renderer.pause()

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

		self.assertEventually(
			lambda : self.assertEqual( self.__colorAtUV( "testSampleFilter", imath.V2i( 0.5 ) ), imath.Color4f( 1, 0, 0, 0 ) )
		)

		renderer.pause()

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

		self.assertEventually(
			lambda : self.assertEqual( self.__colorAtUV( "testSampleFilter", imath.V2i( 0.5 ) ), imath.Color4f( 0.5, 0, 0, 0 ) )
		)

		renderer.pause()

		del renderer

	def testCheckpointing( self ):

		def render( recover, messageHandler = None ) :

			renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
				self.renderer,
				GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch,
				messageHandler = messageHandler
			)

			renderer.output(
				"test",
				IECoreScene.Output(
					( self.temporaryDirectory() / "test.exr" ).as_posix(),
					"exr",
					"rgba",
					{
						"driverType" : "ImageDisplayDriver",
						"handle" : "testSampleFilter",
					}
				)
			)

			renderer.option( "ri:hider:incremental", IECore.IntData( 1 ) )

			if recover :
				renderer.option( "ri:checkpoint:recover", IECore.IntData( 1 ) )
			else :
				renderer.option( "ri:checkpoint:interval", IECore.StringData( "1i" ) )
				renderer.option( "ri:checkpoint:exitat", IECore.StringData( "2i" ) )

			renderer.render()
			del renderer

		render( False )

		messageHandler = IECore.CapturingMessageHandler()
		render( True , messageHandler )
		self.assertEqual( len( messageHandler.messages ), 1 )
		self.assertEqual( messageHandler.messages[0].message, "R56049 Incremental rendering recovery succeeded; resuming render at checkpoint 2." )

	def testAssignID( self ) :

		with IECoreRenderManTest.RileyCapture() as capture :

			renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
				self.renderer,
				GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
			)

			object = renderer.object( "/sphere", IECoreScene.SpherePrimitive( 1 ), renderer.attributes( IECore.CompoundObject() ) )
			object.assignID( 1 )

			del renderer

		self.__assertParameterEqual(
			next( x for x in capture.json if x["method"] == "ModifyGeometryInstance" )["attributes"]["params"],
			"identifier:id", [ 1 ]
		)

	def testGroupingMembership( self ) :

		with IECoreRenderManTest.RileyCapture() as capture :

			renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
				self.renderer,
				GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
			)

			renderer.object(
				"/sphere", IECoreScene.SpherePrimitive( 1 ),
				renderer.attributes( IECore.CompoundObject( {
					"ri:grouping:membership" : IECore.StringData( "groupA groupB" )
				} ) )
			)

			del renderer

		# Memberships specified by the user should have been combined with those
		# generated automatically for light linking.
		self.__assertParameterEqual(
			next( x for x in capture.json if x["method"] == "CreateGeometryInstance" )["attributes"]["params"],
			"grouping:membership", [ "defaultShadowGroup groupA groupB" ]
		)

	def testGroupingMembershipMergedWithShadowLinking( self ) :

		with IECoreRenderManTest.RileyCapture() as capture :

			renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
				self.renderer,
				GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
			)

			lightAttributes = renderer.attributes(
				IECore.CompoundObject( {
					"ri:light" : IECoreScene.ShaderNetwork(
						shaders = { "output" : IECoreScene.Shader( "PxrDomeLight", "ri:light" ) },
						output = "output",
					),
				} )
			)

			light = renderer.light( "light", None, lightAttributes )

			object = renderer.object(
				"/sphere", IECoreScene.SpherePrimitive( 1 ),
				renderer.attributes( IECore.CompoundObject( {
					"ri:grouping:membership" : IECore.StringData( "groupA groupB" )
				} ) )
			)

			object.link( "shadowedLights", { light } )

			del renderer

		# Memberships specified by the user should have been combined with those
		# generated automatically for shadow linking.
		self.__assertParameterEqual(
			next( x for x in capture.json if x["method"] == "ModifyGeometryInstance" )["attributes"]["params"],
			"grouping:membership", [ "shadowGroup0 groupA groupB" ]
		)

	def testRemoveLightAttributes( self ) :

		with IECoreRenderManTest.RileyCapture() as capture :

			renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
				self.renderer,
				GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Interactive
			)

			lightShader = IECoreScene.ShaderNetwork(
				shaders = { "output" : IECoreScene.Shader( "PxrRectLight", "ri:light" ) },
				output = "output",
			)

			light = renderer.light(
				"light", None,
				renderer.attributes( IECore.CompoundObject( {
					"ri:light" : lightShader,
					"user:test" : IECore.IntData( 10 ),
					"ri:visibility:camera" : IECore.BoolData( False ),
				} ) )
			)

			# Remove the "user:test" attribute and add "light:mute"
			self.assertTrue(
				light.attributes(
					renderer.attributes( IECore.CompoundObject( {
						"ri:light" : lightShader,
						"ri:visibility:camera" : IECore.BoolData( False ),
						"light:mute" : IECore.BoolData( True ),
					} ) )
				)
			)

			# Remove "light:mute" and update "ri:visibility:camera"
			self.assertTrue(
				light.attributes(
					renderer.attributes( IECore.CompoundObject( {
						"ri:light" : lightShader,
						"ri:visibility:camera" : IECore.BoolData( True ),
					} ) )
				)
			)

			# Remove "ri:visibility:camera"
			self.assertTrue(
				light.attributes(
					renderer.attributes( IECore.CompoundObject( {
						"ri:light" : lightShader,
					} ) )
				)
			)

			del light
			del renderer

		self.__assertParameterEqual(
			next( x for x in capture.json if x["method"] == "CreateLightInstance" )["attributes"]["params"],
			"user:test", [ 10 ]
		)

		modifications = [
			x for x in capture.json
			if x["method"] == "ModifyLightInstance" and x["attributes"] is not None
		]

		self.assertEqual( len( modifications ), 3 )
		self.__assertNotInParameters( modifications[0]["attributes"]["params"], "user:test" )
		self.__assertParameterEqual( modifications[0]["attributes"]["params"], "visibility:camera", [ 0 ] )
		self.__assertParameterEqual( modifications[0]["attributes"]["params"], "lighting:mute", [ 1 ] )

		self.__assertNotInParameters( modifications[1]["attributes"]["params"], "user:test" )
		self.__assertParameterEqual( modifications[1]["attributes"]["params"], "visibility:camera", [ 1 ] )
		self.__assertNotInParameters( modifications[1]["attributes"]["params"], "lighting:mute" )

		self.__assertNotInParameters( modifications[2]["attributes"]["params"], "user:test" )
		self.__assertNotInParameters( modifications[2]["attributes"]["params"], "visibility:camera" )
		self.__assertNotInParameters( modifications[2]["attributes"]["params"], "lighting:mute" )

	def testShaderSubstitutions( self ) :

		with IECoreRenderManTest.RileyCapture() as capture :

			renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
				self.renderer,
				GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
			)

			shader = IECoreScene.ShaderNetwork(
				shaders = {
					"surface" : IECoreScene.Shader( "PxrSurface" ),
					"texture" : IECoreScene.Shader(
						"PxrTexture", parameters = { "filename" : "<attr:user:textureDir>/diffuse.exr" }
					),
				},
				connections = [ ( ( "texture", "resultRGB" ), ( "surface", "diffuseColor" ) ) ],
				output = "surface"
			)

			displacementShader = IECoreScene.ShaderNetwork(
				shaders = {
					"displacement" : IECoreScene.Shader( "PxrDisplace" ),
					"texture" : IECoreScene.Shader(
						"PxrTexture", parameters = { "filename" : "<attr:user:dispDir>/displacement.exr" }
					),
				},
				connections = [ ( ( "texture", "resultR" ), ( "displacement", "dispScalar" ) ) ],
				output = "displacement"
			)

			mesh = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) )

			attributesA = renderer.attributes(
				IECore.CompoundObject( {
					"ri:surface" : shader,
					"ri:displacement" : displacementShader,
					"user:textureDir" : IECore.StringData( "textureDirA" ),
					"user:dispDir" : IECore.StringData( "dispDirA" ),
				} )
			)

			attributesB = renderer.attributes(
				IECore.CompoundObject( {
					"ri:surface" : shader,
					"ri:displacement" : displacementShader,
					"user:textureDir" : IECore.StringData( "textureDirB" ),
					"user:dispDir" : IECore.StringData( "dispDirB" ),
				} )
			)

			renderer.object( "meshA1", mesh, attributesA )
			renderer.object( "meshA2", mesh, attributesA )
			renderer.object( "meshB1", mesh, attributesB )
			renderer.object( "meshB2", mesh, attributesB )

			del attributesA, attributesB
			del renderer

		materials = [ x for x in capture.json if x["method"] == "CreateMaterial" ]
		self.assertEqual( len( materials ), 2 )

		self.__assertShadingNetworkParameterEqual( materials[0]["material"], "texture.filename", [ "textureDirA/diffuse.exr" ] )
		self.__assertShadingNetworkParameterEqual( materials[1]["material"], "texture.filename", [ "textureDirB/diffuse.exr" ] )

		displacements = [ x for x in capture.json if x["method"] == "CreateDisplacement" ]
		self.assertEqual( len( displacements ), 2 )

		self.__assertShadingNetworkParameterEqual( displacements[0]["displacement"], "texture.filename", [ "dispDirA/displacement.exr" ] )
		self.__assertShadingNetworkParameterEqual( displacements[1]["displacement"], "texture.filename", [ "dispDirB/displacement.exr" ] )

	def testMaterialAssignment( self ) :

		surfaceShader1 = IECoreScene.ShaderNetwork(
			shaders = { "output" : IECoreScene.Shader( "PxrSurface", parameters = { "diffuseColor" : imath.Color3f( 1 ) } ) },
			output = "output"
		)

		surfaceShader2 = IECoreScene.ShaderNetwork(
			shaders = { "output" : IECoreScene.Shader( "PxrSurface", parameters = { "diffuseColor" : imath.Color3f( 2 ) } ) },
			output = "output"
		)

		volumeShader1 = IECoreScene.ShaderNetwork(
			shaders = { "output" : IECoreScene.Shader( "PxrVolume", parameters = { "diffuseColor" : imath.Color3f( 3 ) } ) },
			output = "output"
		)

		volumeShader2 = IECoreScene.ShaderNetwork(
			shaders = { "output" : IECoreScene.Shader( "PxrVolume", parameters = { "diffuseColor" : imath.Color3f( 4 ) } ) },
			output = "output"
		)

		for riVolume, volume, riSurface, surface, expectedColor in [
			( None, None, None, None, None ),
			( volumeShader1, None, None, None, [ 3, 3, 3 ] ),
			( volumeShader1, volumeShader2, None, None, [ 3, 3, 3 ] ),
			( None, volumeShader2, None, None, [ 4, 4, 4 ] ),
			( volumeShader1, None, surfaceShader1, None, [ 3, 3, 3 ] ),
			( None, None, surfaceShader1, None, [ 1, 1, 1 ] ),
			( None, None, surfaceShader1, surfaceShader2, [ 1, 1, 1 ] ),
			( None, None, None, surfaceShader2, [ 2, 2, 2 ] ),
		] :

			with self.subTest( riVolume = bool( riVolume ), volume = bool( volume ), riSurface = bool( riSurface ), surface = bool( surface ) ) :

				with IECoreRenderManTest.RileyCapture() as capture :

					renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
						self.renderer,
						GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
					)

					mesh = IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -1 ), imath.V2f( 1 ) ) )

					attributes = {}
					if riVolume is not None :
						attributes["ri:volume"] = riVolume

					if volume is not None :
						attributes["volume"] = volume

					if riSurface is not None :
						attributes["ri:surface"] = riSurface

					if surface is not None :
						attributes["surface"] = surface

					attributes = renderer.attributes( IECore.CompoundObject( attributes ) )

					renderer.object( "mesh", mesh, attributes )

					del attributes
					del renderer

				materials = [ x for x in capture.json if x["method"] == "CreateMaterial" ]
				self.assertEqual( len( materials ), 1 )

				if expectedColor is None :
					node = materials[0]["material"]["nodes"][-1]
					self.__assertNotInParameters( node["params"]["params"], "diffuseColor" )
				else :
					self.__assertShadingNetworkParameterEqual( materials[0]["material"], "output.diffuseColor", expectedColor )

	def testCamera( self ) :

		for ( proj, nearClip, farClip, focalLength, aperture, translate, dof, fStop, flWorldScale, focusDist ) in [
			( "orthographic", 0.7, 1000, 1, imath.V2f( 0.5, 0.125 ), imath.V3f( 1, 2, 3 ), False, 0.5, 1, 10 ),
			( "orthographic", 0.8, 2000, 2, imath.V2f( 3, 0.125 ), imath.V3f( 4, 5, 6 ), True, 0.5, 1, 10 ),
			( "perspective", 0.9, 3000, 3, imath.V2f( 4 ), imath.V3f( 7, 8, 9 ), True, 0.5, 1, 10 ),
			( "perspective", 0.1, 4000, 4, imath.V2f( 5 ), imath.V3f( 0, 1, 2 ), False, 0.5, 1, 11 ),
			( "perspective", 0.2, 5000, 5, imath.V2f( 6 ), imath.V3f( 3, 4, 5 ), True, 0.5, 0.1, 12 ),
		]:
			with self.subTest(
				proj = proj, nearClip = nearClip, farClip = farClip, focalLength = focalLength,
				aperture = aperture, translate = translate, dof = dof, fStop = fStop, flWorldScale = flWorldScale,
				focusDist = focusDist
			):
				m = imath.M44f()
				m.translate( translate )

				camera = IECoreScene.Camera()
				camera.setProjection( proj )
				camera.setClippingPlanes( imath.V2f( nearClip, farClip ) )
				camera.setFocalLength( focalLength )
				camera.setAperture( aperture )
				camera.setFStop( fStop )
				camera.setFocalLengthWorldScale( flWorldScale )
				camera.setFocusDistance( focusDist )
				## \todo Replace with camera.setDepthOfField( True ) once Cortex supports it
				camera.parameters()["depthOfField"] = dof

				with IECoreRenderManTest.RileyCapture() as capture :

					renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
						"RenderMan",
						GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
					)

					renderCam = renderer.camera(
						"camera", camera, renderer.attributes( IECore.CompoundObject() )
					)

					renderCam.transform( m )
					del renderCam, renderer

				cam = next(
					x for x in capture.json if x["method"] == "CreateCamera"
				)
				camModify = next(
					x for x in capture.json if x["method"] == "ModifyCamera"
				)

				self.__assertParameterEqual( cam['properties']['params'], 'nearClip', [nearClip], tolerance = 1e-7 )
				self.__assertParameterEqual( cam['properties']['params'], 'farClip', [farClip] )

				# We apply a Z-flip in order to match the camera direction to what we expect
				m.scale( imath.V3f( 1, 1, -1 ) )
				self.assertEqual( camModify['xform']['matrix'][0], [ m[i][j] for i in range(4) for j in range(4) ] )

				f = camera.frustum()
				self.__assertParameterEqual( cam['properties']['params'], 'Ri:ScreenWindow', [ f.min().x, f.max().x, f.min().y, f.max().y ] )
				if proj != "perspective":
					self.assertEqual( cam['projection']['name'], "PxrOrthographic" )
					self.assertIsNone( cam['projection']['params'] )
				else:
					self.assertEqual( cam['projection']['name'], "PxrCamera" )
					if not dof:
						self.assertIsNone( cam['projection']['params'] )
					else:
						self.__assertParameterEqual( cam['projection']['params']['params'], "focalDistance", [focusDist] )
						self.__assertParameterEqual( cam['projection']['params']['params'], "fStop", [fStop] )
						self.__assertParameterEqual(
							cam['projection']['params']['params'], "focalLength", [focalLength  * flWorldScale],
							tolerance = 1e-7
						)

	def testCustomCameraParameters( self ) :

		camera = IECoreScene.Camera()
		camera.setProjection( "perspective" )
		camera.parameters()["ri:radial1"] = 1.0
		camera.parameters()["ri:apertureAngle"] = 45.0
		camera.parameters()["ri:apertureDensity"] = 5.0
		camera.parameters()["ri:apertureNSides"] = 3
		camera.parameters()["ri:apertureRoundness"] = 0.0
		camera.parameters()["ri:dofaspect"] = 1.0
		camera.parameters()["ai:ignoreMe"] = 1.0

		with IECoreRenderManTest.RileyCapture() as capture :

			renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
				"RenderMan",
				GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
			)

			renderer.camera(
				"camera", camera, renderer.attributes( IECore.CompoundObject() )
			)

			del renderer

		camera = next( x for x in capture.json if x["method"] == "CreateCamera" )
		self.__assertParameterEqual( camera["projection"]["params"]["params"], "radial1", [ 1.0 ] )
		self.__assertParameterEqual( camera["properties"]["params"], "apertureAngle", [ 45.0 ] )
		self.__assertParameterEqual( camera["properties"]["params"], "apertureDensity", [ 5.0 ] )
		self.__assertParameterEqual( camera["properties"]["params"], "apertureNSides", [ 3 ] )
		self.__assertParameterEqual( camera["properties"]["params"], "apertureRoundness", [ 0.0 ] )
		self.__assertParameterEqual( camera["properties"]["params"], "dofaspect", [ 1.0 ] )
		for parameterList in ( camera["properties"]["params"], camera["projection"]["params"]["params"] ) :
			self.__assertNotInParameters( parameterList, "ai:ignoreMe" )
			self.__assertNotInParameters( parameterList, "ignoreMe" )

	def runOverscanTest( self, res, pixelsTop, pixelsBottom, pixelsLeft, pixelsRight ) :

		with self.subTest(
				res = res,
				pixelsTop = pixelsTop, pixelsBottom = pixelsBottom,
				pixelsLeft = pixelsLeft, pixelsRight = pixelsRight
		) :

			renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
				self.renderer,
				GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
			)

			camera = IECoreScene.Camera()
			camera.setResolution( res )
			camera.setOverscan( True )

			# We've got our own rounding in how renderRegion() is computed - to ensure we
			# get the exact pixel amounts of overscan we're requesting, we offset by
			# a quarter pixel.
			camera.setOverscanTop( ( pixelsTop + 0.25 ) / res[1] )
			camera.setOverscanBottom( ( pixelsBottom + 0.25 ) / res[1] )
			camera.setOverscanLeft( ( pixelsLeft + 0.25 ) / res[0] )
			camera.setOverscanRight( ( pixelsRight + 0.25 ) / res[0] )

			self.assertEqual(
				camera.renderRegion(),
				imath.Box2i(
					imath.V2i( -pixelsLeft,	-pixelsBottom ),
					res + imath.V2i( pixelsRight, pixelsTop )
				)
			)

			renderCam = renderer.camera(
				"camera", camera, renderer.attributes( IECore.CompoundObject() )
			)

			renderer.option( "camera", IECore.StringData( "camera" ) )

			renderer.output(
				f"test",
				IECoreScene.Output(
					str( self.temporaryDirectory() / f"test.exr" ),
					"exr",
					"rgb",
					{}
				)
			)

			renderer.render()
			del renderer

			image = OpenImageIO.ImageBuf( str( self.temporaryDirectory() / f"test.exr" ) )

			self.assertEqual( image.spec().width, res[0] + pixelsLeft + pixelsRight )
			self.assertEqual( image.spec().height, res[1] + pixelsTop + pixelsBottom )
			self.assertEqual( image.spec().x, -pixelsLeft )
			self.assertEqual( image.spec().y, -pixelsTop )

			self.assertEqual( image.spec().full_width, res[0] )
			self.assertEqual( image.spec().full_height, res[1] )
			self.assertEqual( image.spec().full_x, 0 )
			self.assertEqual( image.spec().full_y, 0 )

	@unittest.skipIf( True, "Fuzzing the overscan values is too expensive to run regularly" )
	def testFuzzOverscan( self ):
		random.seed( 42 )
		for i in range( 40 ):
			self.runOverscanTest(
				imath.V2i( random.randint( 100, 1000 ), random.randint( 100, 1000 ) ),
				random.randint( 0, 500 ), random.randint( 0, 500 ),
				random.randint( 0, 500 ), random.randint( 0, 500 )
			)

		# We can more efficiently check the rounding behaviours for much larger images by
		# using test images that are one pixel tall or one pixel wide
		for i in range( 1000 ):
			self.runOverscanTest(
				imath.V2i( random.randint( 100, 16000 ), 1 ),
				0, 0,
				random.randint( 0, 1000 ), random.randint( 0, 1000 )
			)

		for i in range( 1000 ):
			self.runOverscanTest(
				imath.V2i( 1, random.randint( 100, 16000 ) ),
				random.randint( 0, 1000 ), random.randint( 0, 1000 ),
				0, 0
			)

	def testOverscan( self ):
		# Test some simple overscan values, and some that were specifically chosen to
		# fail if a naive division without rounding compensation is used.
		self.runOverscanTest( imath.V2i( 100, 100 ), 1, 2, 3, 4 )
		self.runOverscanTest( imath.V2i( 200, 200 ), 14, 13, 12, 11 )
		self.runOverscanTest( imath.V2i( 750, 750 ), 249, 249, 249, 249 )
		self.runOverscanTest( imath.V2i( 162, 512 ), 745, 347, 819, 882 )

	def testVolumeTransformEdit( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			self.renderer,
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
			IECoreVDB.VDBObject( "./python/GafferArnoldTest/volumes/sphere.vdb" ),
			renderer.attributes( IECore.CompoundObject( {
				"ri:surface" : IECoreScene.ShaderNetwork(
					shaders = {
						"output" : IECoreScene.Shader( "PxrVolume", parameters = { "densityFloatPrimVar" : "density" } )
					},
					output = "output",
				)
			} ) )
		)
		sphere.transform( imath.M44f().translate( imath.V3f( 0, -2, -2 ) ) )
		renderer.render()

		# Volume should be visible in the middle of the image, and not at the top.
		self.assertEventually(
			lambda : self.assertGreater( self.__colorAtUV( "myLovelySphere", imath.V2f( 0.5, 0.5 ) ).a, 0.25 )
		)
		self.assertEventually(
			lambda : self.assertEqual( self.__colorAtUV( "myLovelySphere", imath.V2f( 0.5, 0.0 ) ).a, 0 )
		)

		renderer.pause()
		sphere.transform( imath.M44f().translate( imath.V3f( 0, 0, -2 ) ) )
		renderer.render()

		# Volume should have moved to the top of the image.
		self.assertEventually(
			lambda : self.assertEqual( self.__colorAtUV( "myLovelySphere", imath.V2f( 0.5, 0.5 ) ).a, 0 )
		)
		self.assertEventually(
			lambda : self.assertGreater( self.__colorAtUV( "myLovelySphere", imath.V2f( 0.5, 0.0 ) ).a, 0.25 )
		)

		renderer.pause()
		del sphere
		del renderer

	def testMaterialID( self ) :

		surfaceNetwork = IECoreScene.ShaderNetwork(
			shaders = { "surfaceOutputHandle" : IECoreScene.Shader( "PxrConstant" ) },
			output = ( "surfaceOutputHandle", "bxdf_out" ),
		)

		volumeNetwork = IECoreScene.ShaderNetwork(
			shaders = { "volumeOutputHandle" : IECoreScene.Shader( "PxrVolume" ) },
			output = ( "volumeOutputHandle", "out" ),
		)

		for surface, volume, materialID, expectedID in [
			( surfaceNetwork, None, None, "surfaceOutputHandle" ),
			( None, volumeNetwork, None, "volumeOutputHandle" ),
			( surfaceNetwork, volumeNetwork, None, "volumeOutputHandle" ),
			( None, None, None, "defaultFacingRatio" ),
			( surfaceNetwork, volumeNetwork, "customID", "customID" ),
		] :

			with self.subTest( surface = surface is not None, volume = volume is not None, materialID = materialID ) :

				with IECoreRenderManTest.RileyCapture() as capture :

					renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
						self.renderer,
						GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
					)

					attributes = IECore.CompoundObject()
					if surface :
						attributes["ri:surface"] = surfaceNetwork
					if volume :
						attributes["ri:volume"] = volumeNetwork
					if materialID :
						attributes["user:__materialid"] = IECore.StringData( materialID )

					renderer.object(
						"/sphere", IECoreScene.SpherePrimitive( 1 ),
						renderer.attributes( attributes )
					)

					del renderer

				self.__assertParameterEqual(
					next( x for x in capture.json if x["method"] == "CreateGeometryInstance" )["attributes"]["params"],
					"user:__materialid", [ expectedID ]
				)

	def testLayerPerLightGroupOutputs( self ) :

		messageHandler = IECore.CapturingMessageHandler()
		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			self.renderer,
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch,
			messageHandler = messageHandler
		)

		beautyFileName = self.temporaryDirectory() / "beauty.exr"
		renderer.output(
			"RGBA",
			IECoreScene.Output( str( beautyFileName ), "exr", "rgba" )
		)

		beautyLayersFileName = self.temporaryDirectory() / "beautyLayers.exr"
		renderer.output(
			"perLightGroupRGBA",
			IECoreScene.Output(
				str( beautyLayersFileName ), "exr", "rgba",
				{
					"layerPerLightGroup" : True
				}
			)
		)

		diffuseFileName = self.temporaryDirectory() / "diffuse.exr"
		renderer.output(
			"perLightGroupLPE",
			IECoreScene.Output(
				str( diffuseFileName ), "exr", "lpe C<RD>[<L.>O]",
				{
					"layerName" : "directDiffuse",
					"layerPerLightGroup" : True,
				}
			)
		)

		bracketFileName = self.temporaryDirectory() / "bracket.exr"
		renderer.output(
			"bracketLPE",
			IECoreScene.Output(
				str( bracketFileName ), "exr", "lpe C.{0,2}[LO]",
				{
					"layerName" : "bracket",
					"layerPerLightGroup" : True,
				}
			)
		)

		shortNameDiffuseFileName = self.temporaryDirectory() / "shortNameDiffuse.exr"
		renderer.output(
			"perLightGroupShortNameLPE",
			IECoreScene.Output(
				str( shortNameDiffuseFileName ), "exr", "lpe diffuse",
				{
					"layerName" : "diffuse",
					"layerPerLightGroup" : True,
				}
			)
		)

		prefixedDiffuseFileName = self.temporaryDirectory() / "prefixedDiffuse.exr"
		renderer.output(
			"perLightGroupLPEPrefixed",
			IECoreScene.Output(
				str( prefixedDiffuseFileName ), "exr", "lpe unoccluded;noclamp;nothruput;C<RD>[<L.>O]",
				{
					"layerName" : "directDiffuse",
					"layerPerLightGroup" : True,
				}
			)
		)

		shortNamePrefixedDiffuseFileName = self.temporaryDirectory() / "shortNamePrefixedDiffuse.exr"
		renderer.output(
			"perLightGroupShortNameLPEPrefixed",
			IECoreScene.Output(
				str( shortNamePrefixedDiffuseFileName ), "exr", "lpe unoccluded;noclamp;nothruput;diffuse",
				{
					"layerName" : "diffuse",
					"layerPerLightGroup" : True,
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

		lightGroups = {
			"red" : imath.Color3f( 1, 0, 0 ),
			"green" : imath.Color3f( 0, 1, 0 ),
			"blue" : imath.Color3f( 0, 0, 1 ),
		}

		lights = [
			renderer.light(
				f"/light/{group}", None,
				renderer.attributes( IECore.CompoundObject( {
					"ri:light" : IECoreScene.ShaderNetwork(
						shaders = {
							"output" : IECoreScene.Shader(
								"PxrDomeLight", "ri:light",
								{ "lightGroup" : group, "lightColor" : color }
							),
						},
						output = "output",
					),
					"ri:visibility:camera" : IECore.BoolData( True ),
				} ) )
			)
			for group, color in lightGroups.items()
		]

		renderer.render()
		del sphere, lights
		del renderer

		self.assertEqual( len( messageHandler.messages ), 0 )

		beautyImage = OpenImageIO.ImageBuf( str( beautyFileName ) )
		self.assertEqual(
			set( beautyImage.spec().channelnames ),
			set( "RGBA" )
		)

		# The original layers should be replaced by a layer for each light group and a default layer.

		lightLayers = { k : ( v, imath.Color3f( 0.0 ) ) for k, v in lightGroups.items() }
		lightLayers["default"] = ( imath.Color3f( 0.0 ), imath.Color3f( 1.0 ) )

		beautyLayersImage = OpenImageIO.ImageBuf( str( beautyLayersFileName ) )
		self.assertEqual(
			set( beautyLayersImage.spec().channelnames ),
			{ f"RGBA_{g}.{c}" for g in lightLayers for c in "rgb" }
		)

		diffuseImage = OpenImageIO.ImageBuf( str( diffuseFileName ) )
		self.assertEqual(
			set( diffuseImage.spec().channelnames ),
			{ f"directDiffuse_{g}.{c}" for g in lightLayers for c in "rgb" }
		)

		diffuseShortNameImage = OpenImageIO.ImageBuf( str( shortNameDiffuseFileName ) )
		self.assertEqual(
			set( diffuseShortNameImage.spec().channelnames ),
			{ f"diffuse_{g}.{c}" for g in lightLayers for c in "rgb" }
		)

		prefixedDiffuseImage = OpenImageIO.ImageBuf( str( prefixedDiffuseFileName ) )
		self.assertEqual(
			set( prefixedDiffuseImage.spec().channelnames ),
			{ f"directDiffuse_{g}.{c}" for g in lightLayers for c in "rgb" }
		)

		prefixedDiffuseShortNameImage = OpenImageIO.ImageBuf( str( shortNamePrefixedDiffuseFileName ) )
		self.assertEqual(
			set( prefixedDiffuseShortNameImage.spec().channelnames ),
			{ f"diffuse_{g}.{c}" for g in lightLayers for c in "rgb" }
		)

		# Each light group layer should only contain illumination from its own
		# group, and the group layers should sum to the beauty.

		layerChannelIndices = { c : i for i, c in enumerate( beautyLayersImage.spec().channelnames ) }
		layersMidPixel = beautyLayersImage.getpixel( 320, 240 )
		layersTopLeftPixel = beautyLayersImage.getpixel( 0, 0 )

		for group, color in lightGroups.items() :
			for channel, value in zip( "rgb", color ) :
				groupValue = layersMidPixel[layerChannelIndices[f"RGBA_{group}.{channel}"]]
				if value == 0 :
					self.assertAlmostEqual( groupValue, 0, delta = 0.001 )
				else :
					self.assertGreater( groupValue, 0.2 )

				# Where the dome lights are directly visible, no color on layers
				self.assertEqual( layersTopLeftPixel[layerChannelIndices[f"RGBA_{group}.{channel}"]], 0 )

		for channel in "rgb" :
			# default layer has no color on sphere
			self.assertEqual( layersMidPixel[layerChannelIndices[f"RGBA_default.{channel}"]], 0 )
			# default layer all white where dome lights combine
			self.assertEqual( layersTopLeftPixel[layerChannelIndices[f"RGBA_default.{channel}"]], 1 )

		channelIndices = { c : i for i, c in enumerate( beautyImage.spec().channelnames ) }
		midPixel = beautyImage.getpixel( 320, 240 )
		topLeftPixel = beautyImage.getpixel( 0, 0 )

		for channel in "rgb" :
			self.assertAlmostEqual(
				midPixel[channelIndices[channel.upper()]],
				sum( layersMidPixel[layerChannelIndices[f"RGBA_{g}.{channel}"]] for g in lightLayers ),
				delta = 0.01
			)
			self.assertAlmostEqual(
				topLeftPixel[channelIndices[channel.upper()]],
				sum( layersTopLeftPixel[layerChannelIndices[f"RGBA_{g}.{channel}"]] for g in lightLayers ),
				delta = 0.01
			)

	def testLayerPerLightGroupLightWithoutGroup( self ) :

		messageHandler = IECore.CapturingMessageHandler()
		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			self.renderer,
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch,
			messageHandler = messageHandler
		)

		beautyLayersFileName = self.temporaryDirectory() / "beautyLayers.exr"
		renderer.output(
			"perLightGroupRGBA",
			IECoreScene.Output(
				str( beautyLayersFileName ), "exr", "rgba",
				{
					"layerPerLightGroup" : True
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

		lightGroups = [
			( "red", "red", imath.Color3f( 1, 0, 0 ) ),
			( "green", "", imath.Color3f( 0, 1, 0 ) ),
			( "blue", "", imath.Color3f( 0, 0, 1 ) ),
		]

		lights = [
			renderer.light(
				f"/light/{lightName}", None,
				renderer.attributes( IECore.CompoundObject( {
					"ri:light" : IECoreScene.ShaderNetwork(
						shaders = {
							"output" : IECoreScene.Shader(
								"PxrDomeLight", "ri:light",
								{ "lightGroup" : group, "lightColor" : color }
							),
						},
						output = "output",
					),
					"ri:visibility:camera" : IECore.BoolData( False ),
				} ) )
			)
			for lightName, group, color in lightGroups
		]

		renderer.render()
		del sphere, lights
		del renderer

		self.assertEqual( len( messageHandler.messages ), 0 )

		beautyLayersImage = OpenImageIO.ImageBuf( str( beautyLayersFileName ) )
		self.assertEqual(
			set( beautyLayersImage.spec().channelnames ),
			{ f"RGBA_{g}.{c}" for g in [ "red", "default" ] for c in "rgb" }
		)

		expectedColorPerLayer = {}
		for lightName, group, color in lightGroups :
			expectedColorPerLayer[group] = expectedColorPerLayer.get( group, imath.Color3f( 0 ) ) + color

		layerChannelIndices = { c : i for i, c in enumerate( beautyLayersImage.spec().channelnames ) }
		layersMidPixel = beautyLayersImage.getpixel( 320, 240 )

		for group, color in expectedColorPerLayer.items() :
			group = group or "default"
			for channel, value in zip( "rgb", color ) :
				groupValue = layersMidPixel[layerChannelIndices[f"RGBA_{group}.{channel}"]]
				if value == 0 :
					self.assertAlmostEqual( groupValue, 0, delta = 0.001 )
				else :
					self.assertGreater( groupValue, 0.2 )

	def testLayerPerLightGroupIgnoresLPEWithExplicitGroup( self ) :

		messageHandler = IECore.CapturingMessageHandler()
		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			self.renderer,
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch,
			messageHandler = messageHandler
		)

		fileName = self.temporaryDirectory() / "keyDiffuse.exr"
		renderer.output(
			"explicitGroup",
			IECoreScene.Output(
				str( fileName ), "exr", "lpe C<RD>[<L.'key'>O]",
				{
					"layerName" : "keyDiffuse",
					"layerPerLightGroup" : True,
				}
			)
		)

		shortNameFileName = self.temporaryDirectory() / "shortNameDiffuse.exr"
		renderer.output(
			"explicitShortNameGroup",
			IECoreScene.Output(
				str( shortNameFileName ), "exr", "lpe diffuse_key",
				{
					"layerName" : "diffuse",
					"layerPerLightGroup" : True
				}
			)
		)

		# This is valid because the `L'` is part of the LPE identifier
		lpeIdentifierFileName = self.temporaryDirectory() / "lpeIdentifier.exr"
		renderer.output(
			"explicitLPEIdentifierGroup",
			IECoreScene.Output(
				str( lpeIdentifierFileName ), "exr", "lpe C<.D\'LLLLL\'>*[LO]",
				{
					"layerName" : "lpeIdentifier",
					"layerPerLightGroup" : True,
				}
			)
		)

		light = renderer.light(
			"/light", None,
			renderer.attributes( IECore.CompoundObject( {
				"ri:light" : IECoreScene.ShaderNetwork(
					shaders = {
						"output" : IECoreScene.Shader(
							"PxrDomeLight", "ri:light",
							{ "lightGroup" : "rim" }
						),
					},
					output = "output",
				),
			} ) )
		)

		renderer.render()
		del light
		del renderer

		# If the LPE already specifies a light group, then
		# `layerPerLightGroup` should be ignored with a warning.

		self.assertEqual( len( messageHandler.messages ), 2 )
		self.assertEqual(
			set( i.message for i in messageHandler.messages ),
			{
				"Ignoring \"layerPerLightGroup\" parameter on output \"explicitGroup\", because its LPE already specifies a light group.",
				"Ignoring \"layerPerLightGroup\" parameter on output \"explicitShortNameGroup\", because its LPE already specifies a light group.",
			}
		)

		image = OpenImageIO.ImageBuf( str( fileName ) )
		self.assertEqual( set( image.spec().channelnames ), { "keyDiffuse.r", "keyDiffuse.g", "keyDiffuse.b" } )

		image = OpenImageIO.ImageBuf( str( shortNameFileName ) )
		self.assertEqual( set( image.spec().channelnames ), { "diffuse.r", "diffuse.g", "diffuse.b" } )

		image = OpenImageIO.ImageBuf( str( lpeIdentifierFileName ) )
		self.assertEqual(
			set( image.spec().channelnames ),
			{ "lpeIdentifier_rim.r", "lpeIdentifier_rim.g", "lpeIdentifier_rim.b", "lpeIdentifier_default.r", "lpeIdentifier_default.g", "lpeIdentifier_default.b" }
		)

	def testLayerPerLightGroupIgnoresIncompatibleLPE( self ) :

		messageHandler = IECore.CapturingMessageHandler()
		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			self.renderer,
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch,
			messageHandler = messageHandler
		)

		fileName = self.temporaryDirectory() / "emission.exr"
		renderer.output(
			"emission",
			IECoreScene.Output(
				str( fileName ), "exr", "lpe CO",
				{
					"layerName" : "emission",
					"layerPerLightGroup" : True,
				}
			)
		)

		light = renderer.light(
			"/light", None,
			renderer.attributes( IECore.CompoundObject( {
				"ri:light" : IECoreScene.ShaderNetwork(
					shaders = {
						"output" : IECoreScene.Shader(
							"PxrDomeLight", "ri:light",
							{ "lightGroup" : "rim" }
						),
					},
					output = "output",
				),
			} ) )
		)

		renderer.render()
		del light
		del renderer

		# The emission LPE doesn't contain `L` or `<L.>`, so `layerPerLightGroup`
		# should be ignored with a warning and there is no default group.

		self.assertEqual( len( messageHandler.messages ), 1 )
		self.assertEqual( messageHandler.messages[0].message, "Ignoring \"layerPerLightGroup\" parameter on output \"emission\", because its LPE doesn't contain \"L\" or \"<L.>\"." )

		image = OpenImageIO.ImageBuf( str( fileName ) )
		self.assertEqual( set( image.spec().channelnames ), { "emission.r", "emission.g", "emission.b" } )

	def testLayerPerLightGroupOutputsIgnoreInvalidLights( self ) :

		messageHandler = IECore.CapturingMessageHandler()
		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			self.renderer,
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch,
			messageHandler = messageHandler
		)

		renderer.output(
			"test",
			IECoreScene.Output(
				"test", "ieDisplay", "rgba",
				{
					"driverType" : "ImageDisplayDriver",
					"handle" : "invalidLightGroupTest",
					"layerPerLightGroup" : True,
				}
			)
		)

		invalidLight = renderer.light(
			"/invalidLight", None,
			renderer.attributes( IECore.CompoundObject( {
				"ri:light" : IECoreScene.ShaderNetwork(
					shaders = {
						"output" : IECoreScene.Shader(
							"NotALight", "ri:light",
							{ "lightGroup" : "bad" }
						),
					},
					output = "output",
				),
			} ) )
		)

		validLight = renderer.light(
			"/validLight", None,
			renderer.attributes( IECore.CompoundObject( {
				"ri:light" : IECoreScene.ShaderNetwork(
					shaders = {
						"output" : IECoreScene.Shader(
							"PxrDomeLight", "ri:light",
							{ "lightGroup" : "good" }
						),
					},
					output = "output",
				),
			} ) )
		)

		renderer.render()

		self.assertEqual( len( messageHandler.messages ), 1 )
		self.assertEqual( messageHandler.messages[0].message, "Unable to find shader \"NotALight\"." )

		image = IECoreImage.ImageDisplayDriver.storedImage( "invalidLightGroupTest" )
		self.assertEqual(
			set( image.keys() ),
			{ f"RGBA_good.{c}" for c in "RGB" } | { f"RGBA_default.{c}" for c in "RGB" }
		)

		del invalidLight, validLight
		del renderer

	def testInteractiveLightGroupEdits( self ) :

		messageHandler = IECore.CapturingMessageHandler()

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			self.renderer,
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Interactive,
			messageHandler = messageHandler
		)

		renderer.output(
			"test",
			IECoreScene.Output(
				"test", "ieDisplay", "rgba",
				{
					"driverType" : "ImageDisplayDriver",
					"handle" : "lightGroupTest",
					"layerPerLightGroup" : True,
				}
			)
		)

		def channelNames() :

			image = IECoreImage.ImageDisplayDriver.storedImage( "lightGroupTest" )
			return set( image.keys() ) if image is not None else set()

		def lightAttributes( lightGroup ) :

			return renderer.attributes( IECore.CompoundObject( {
				"ri:light" : IECoreScene.ShaderNetwork(
					shaders = {
						"output" : IECoreScene.Shader(
							"PxrDistantLight", "ri:light",
							{ "lightGroup" : lightGroup }
						),
					},
					output = "output",
				),
			} ) )

		keyLight = renderer.light( "/light/key", None, lightAttributes( "first" ) )

		renderer.render()

		self.assertEventually(
			lambda : self.assertEqual(
				channelNames(),
				{ f"RGBA_{g}.{c}" for g in ( "first", "default" ) for c in "RGB" }
			)
		)

		renderer.pause()
		keyLight.attributes( lightAttributes( "key" ) )
		renderer.render()

		self.assertEventually(
			lambda : self.assertEqual(
				channelNames(),
				{ f"RGBA_{g}.{c}" for g in ( "key", "default" ) for c in "RGB" }
			)
		)

		# Adding a light without a light group keeps the default layer.

		renderer.pause()
		fillLight = renderer.light( "/light/fill", None, lightAttributes( "" ) )
		renderer.render()

		self.assertEventually(
			lambda : self.assertEqual(
				channelNames(),
				{ f"RGBA_{g}.{c}" for g in ( "key", "default" ) for c in "RGB" }
			)
		)

		# Editing the new light's light group should only affect its layer.

		renderer.pause()
		fillLight.attributes( lightAttributes( "second" ) )
		renderer.render()

		self.assertEventually(
			lambda : self.assertEqual(
				channelNames(),
				{ f"RGBA_{g}.{c}" for g in ( "key", "second", "default" ) for c in "RGB" }
			)
		)

		renderer.pause()
		fillLight.attributes( lightAttributes( "fill" ) )
		renderer.render()

		self.assertEventually(
			lambda : self.assertEqual(
				channelNames(),
				{ f"RGBA_{g}.{c}" for g in ( "key", "fill", "default" ) for c in "RGB" }
			)
		)

		# Add a third light with another light group.

		renderer.pause()
		fillLight2 = renderer.light( "/light/fill2", None, lightAttributes( "third" ) )
		renderer.render()

		self.assertEventually(
			lambda : self.assertEqual(
				channelNames(),
				{ f"RGBA_{g}.{c}" for g in ( "key", "fill", "third", "default" ) for c in "RGB" }
			)
		)

		# Edit the third light's lightgroup to combine it with the existing fill group.

		renderer.pause()
		fillLight2.attributes( lightAttributes( "fill" ) )
		renderer.render()

		self.assertEventually(
			lambda : self.assertEqual(
				channelNames(),
				{ f"RGBA_{g}.{c}" for g in ( "key", "fill", "default" ) for c in "RGB" }
			)
		)

		# Deleting a light in the fill group should keep the fill layer, as there
		# is still another light in that group.

		renderer.pause()
		del fillLight
		renderer.render()

		self.assertEventually(
			lambda : self.assertEqual(
				channelNames(),
				{ f"RGBA_{g}.{c}" for g in ( "key", "fill", "default" ) for c in "RGB" }
			)
		)

		# Deleting the remaining light in the fill group should remove the layer.

		renderer.pause()
		del fillLight2
		renderer.render()

		self.assertEventually(
			lambda : self.assertEqual(
				channelNames(),
				{ f"RGBA_{g}.{c}" for g in ( "key", "default" ) for c in "RGB" }
			)
		)

		# Editing the only light in the key group to remove its light group should remove
		# the key layer leave only the default layer.

		renderer.pause()
		keyLight.attributes( lightAttributes( "" ) )
		renderer.render()

		self.assertEventually(
			lambda : self.assertEqual(
				channelNames(),
				{ f"RGBA_default.{c}" for c in "RGB" }
			)
		)

		self.assertEqual( len( messageHandler.messages ), 0 )

		renderer.pause()
		del keyLight
		renderer.render()

		# Deleting the light with a now empty light group still leaves the default layer.

		self.assertEventually(
			lambda : self.assertEqual(
				channelNames(),
				{ f"RGBA_default.{c}" for c in "RGB" }
			)
		)

		renderer.pause()

		del renderer

		self.assertEqual( len( messageHandler.messages ), 0 )

	def testLayerPerLightGroupGlowSurfaceShader( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			self.renderer,
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
		)

		beautyLayersFileName = self.temporaryDirectory() / "beautyLayers.exr"
		renderer.output(
			"perLightGroupRGBA",
			IECoreScene.Output(
				str( beautyLayersFileName ), "exr", "rgba",
				{
					"layerPerLightGroup" : True
				}
			)
		)

		diffuseLayersFileName = self.temporaryDirectory() / "diffuseLayers.exr"
		renderer.output(
			"perLightGroupDiffuse",
			IECoreScene.Output(
				str( diffuseLayersFileName ), "exr", "lpe CD[DS]*[LO]",
				{
					"layerName" : "diffuseLayers",
					"layerPerLightGroup" : True,
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

		backPlane = renderer.object(
			"backPlane",
			IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -3 ), imath.V2f( 3 ) ) ),
			renderer.attributes( IECore.CompoundObject( {
				"ri:surface" : IECoreScene.ShaderNetwork(
					shaders = {
						"output" : IECoreScene.Shader(
							"PxrConstant",
							parameters = {
								"emitColor" : imath.Color3f( 1.0, 0.0, 0.0 )
							}
						)
					},
					output = "output",
				)
			} ) )
		)
		backPlane.transform( imath.M44f().translate( imath.V3f( 0, 0, -3 ) ) )

		frontPlane = renderer.object(
			"frontPlane",
			IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -3 ), imath.V2f( 3 ) ) ),
			renderer.attributes( IECore.CompoundObject( {
				"ri:surface" : IECoreScene.ShaderNetwork(
					shaders = {
						"output" : IECoreScene.Shader(
							"PxrConstant",
							parameters = {
								# Glow materials do not have the same strength as lights, so we boost
								# the intensity a little.
								"emitColor" : imath.Color3f( 0.0, 5.0, 0.0 )
							}
						)
					},
					output = "output",
				)
			} ) )
		)
		frontPlane.transform( imath.M44f().translate( imath.V3f( 0, 0, 3 ) ).rotate( imath.V3f( 0, math.pi, 0 ) ) )

		light = renderer.light(
			"/blue", None,
			renderer.attributes( IECore.CompoundObject( {
				"ri:light" : IECoreScene.ShaderNetwork(
					shaders = {
						"output" : IECoreScene.Shader(
							"PxrDomeLight", "ri:light",
							{ "lightGroup" : "blue", "lightColor" : imath.Color3f( 0, 0, 1 ) }
						),
					},
					output = "output",
				),
				"ri:visibility:camera" : IECore.BoolData( False ),
			} ) )
		)

		renderer.render()
		del sphere, frontPlane, backPlane, light
		del renderer

		def testLayerImage( layerFileName, layerName ) :
			layersImage = OpenImageIO.ImageBuf( str( layerFileName ) )
			self.assertEqual(
				set( layersImage.spec().channelnames ),
				{ f"{layerName}_{g}.{c}" for g in [ "blue", "default" ] for c in "rgb" }
			)

			layerChannelIndices = { c : i for i, c in enumerate( layersImage.spec().channelnames ) }
			layersMidPixel = layersImage.getpixel( 320, 240 )
			layersTopPixel = layersImage.getpixel( 320, 0 )
			# The `blue` layer is blue on the sphere.
			self.assertAlmostEqual( layersMidPixel[layerChannelIndices[f"{layerName}_blue.r"]], 0.0, delta = 0.001 )
			self.assertAlmostEqual( layersMidPixel[layerChannelIndices[f"{layerName}_blue.g"]], 0.0, delta = 0.001 )
			self.assertGreater( layersMidPixel[layerChannelIndices[f"{layerName}_blue.b"]], 0.2 )
			# And black in the background.
			self.assertAlmostEqual( layersTopPixel[layerChannelIndices[f"{layerName}_blue.r"]], 0, delta = 0.001 )
			self.assertAlmostEqual( layersTopPixel[layerChannelIndices[f"{layerName}_blue.g"]], 0, delta = 0.001 )
			self.assertAlmostEqual( layersTopPixel[layerChannelIndices[f"{layerName}_blue.b"]], 0, delta = 0.001 )

			# The default layer gets the green illumination from the illuminating plane (behind the camera).
			self.assertAlmostEqual( layersMidPixel[layerChannelIndices[f"{layerName}_default.r"]], 0.0, delta = 0.001 )
			self.assertGreater( layersMidPixel[layerChannelIndices[f"{layerName}_default.g"]], 0.2 )
			self.assertAlmostEqual( layersMidPixel[layerChannelIndices[f"{layerName}_default.b"]], 0.0, delta = 0.001 )

			if layerName == "RGBA" :
				# Red emission from the background plane for the beauty layer.
				self.assertGreater( layersTopPixel[layerChannelIndices[f"{layerName}_default.r"]], 0.2 )
			else :
				# No emission on non-beauty layers.
				self.assertAlmostEqual( layersTopPixel[layerChannelIndices[f"{layerName}_default.r"]], 0, delta = 0.001 )
			self.assertAlmostEqual( layersTopPixel[layerChannelIndices[f"{layerName}_default.g"]], 0, delta = 0.001 )
			self.assertAlmostEqual( layersTopPixel[layerChannelIndices[f"{layerName}_default.b"]], 0, delta = 0.001 )

		testLayerImage( beautyLayersFileName, "RGBA" )
		testLayerImage( diffuseLayersFileName, "diffuseLayers" )

	def testLayerPerLightGroupIdentifierLPEGroups( self ) :

		# LPE groups (per-object groups, not light groups) should not be
		# affected by our removal of emission or substitution of light groups.

		for lpeGroup in [ "OOOOO", "LLLLL" ] :

			with self.subTest( lpeGroup = lpeGroup ) :

				renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
					self.renderer,
					GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
				)

				diffuseFileName = self.temporaryDirectory() / f"{lpeGroup}_diffuse.exr"
				renderer.output(
					"perLightGroupRGBA",
					IECoreScene.Output(
						str( diffuseFileName ), "exr", f"lpe C<.D'{lpeGroup}'>*[LO]",
						{
							"layerPerLightGroup" : True
						}
					)
				)

				sphere = renderer.object(
					"sphere",
					IECoreScene.SpherePrimitive(),
					renderer.attributes( IECore.CompoundObject( {
						"ri:identifier:lpegroup" : IECore.StringData( lpeGroup ),
						"ri:surface" : IECoreScene.ShaderNetwork(
							shaders = {
								"output" : IECoreScene.Shader( "PxrDiffuse" )
							},
							output = "output",
						)
					} ) )
				)
				sphere.transform( imath.M44f().translate( imath.V3f( 0, 0, -2 ) ) )

				light = renderer.light(
					"/light/red", None,
					renderer.attributes( IECore.CompoundObject( {
						"ri:light" : IECoreScene.ShaderNetwork(
							shaders = {
								"output" : IECoreScene.Shader(
									"PxrDomeLight", "ri:light",
									{ "lightGroup" : "red", "lightColor" : imath.Color3f( 1.0, 0.0, 0.0 ) }
								),
							},
							output = "output",
						),
						"ri:visibility:camera" : IECore.BoolData( False ),
					} ) )
				)

				renderer.render()
				del sphere, light
				del renderer

				diffuseImage = OpenImageIO.ImageBuf( str( diffuseFileName ) )
				self.assertEqual(
					set( diffuseImage.spec().channelnames ),
					{ f"RGBA_{g}.{c}" for g in [ "red", "default" ] for c in "rgb" }
				)

				layerChannelIndices = { c : i for i, c in enumerate( diffuseImage.spec().channelnames ) }
				layersMidPixel = diffuseImage.getpixel( 320, 240 )

				for channel, value in zip( "rgb", imath.Color3f( 1.0, 0.0, 0.0 ) ) :
					channelValue = layersMidPixel[layerChannelIndices[f"RGBA_red.{channel}"]]
					if value == 0 :
						self.assertAlmostEqual( channelValue, 0, delta = 0.001 )
					else :
						self.assertGreater( channelValue, 0.2 )

	def testLayerPerLightGroupPortal( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			self.renderer,
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
		)

		beautyLayersFileName = self.temporaryDirectory() / "beautyLayers.exr"
		renderer.output(
			"perLightGroupRGBA",
			IECoreScene.Output(
				str( beautyLayersFileName ), "exr", "rgba",
				{
					"layerPerLightGroup" : True
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

		lightDome = renderer.light(
			"/light/dome", None,
			renderer.attributes( IECore.CompoundObject( {
				"ri:light" : IECoreScene.ShaderNetwork(
					shaders = {
						"output" : IECoreScene.Shader(
							"PxrDomeLight", "ri:light",
							{ "lightGroup" : "dome", "lightColor" : imath.Color3f( 1, 0, 0 ), "intensity" : 100.0 }
						)
					},
					output = "output"
				),
				"ri:visibility:camera" : IECore.BoolData( False ),
			} ) )
		)

		frontPortal = renderer.light(
			"/light/frontPortal", None,
			renderer.attributes( IECore.CompoundObject( {
				"ri:light" : IECoreScene.ShaderNetwork(
					shaders = { "output" : IECoreScene.Shader(
						"PxrPortalLight", "ri:light",
						{ "lightGroup" : "bogusPortal" }
					) },
					output = "output"
				),
				"ri:visibility:camera" : IECore.BoolData( True ),
			} ) )
		)
		frontPortal.transform( imath.M44f().translate( imath.V3f( 0, 0, -3 ) ).rotate( imath.V3f( 0, math.pi, 0 ) ).scale( imath.V3f( 10.0 )) )

		backPortal = renderer.light(
			"/light/backPortal", None,
			renderer.attributes( IECore.CompoundObject( {
				"ri:light" : IECoreScene.ShaderNetwork(
					shaders = { "output" : IECoreScene.Shader(
						"PxrPortalLight", "ri:light",
						{ "lightGroup" : "bogusPortal2" }
					) },
					output = "output"
				),
				"ri:visibility:camera" : IECore.BoolData( True ),
			} ) )
		)
		backPortal.transform( imath.M44f().translate( imath.V3f( 0, 0, 3 ) ) )

		renderer.render()
		del sphere, lightDome, frontPortal, backPortal
		del renderer

		beautyLayersImage = OpenImageIO.ImageBuf( str( beautyLayersFileName ) )
		self.assertEqual(
			set( beautyLayersImage.spec().channelnames ),
			{ f"RGBA_{g}.{c}" for g in ( "dome", "default" ) for c in "rgb" }
		)

		layerChannelIndices = { c : i for i, c in enumerate( beautyLayersImage.spec().channelnames ) }
		layersMidPixel = beautyLayersImage.getpixel( 320, 240 )
		layersTopLeftPixel = beautyLayersImage.getpixel( 0, 0 )

		# Illuminated from the back portal
		self.assertGreater( layersMidPixel[layerChannelIndices["RGBA_dome.r"]], 0.2 )
		self.assertAlmostEqual( layersMidPixel[layerChannelIndices["RGBA_dome.g"]], 0.0, delta = 0.001 )
		self.assertAlmostEqual( layersMidPixel[layerChannelIndices["RGBA_dome.b"]], 0.0, delta = 0.001 )
		# And black in the background.
		self.assertAlmostEqual( layersTopLeftPixel[layerChannelIndices["RGBA_dome.r"]], 0, delta = 0.001 )
		self.assertAlmostEqual( layersTopLeftPixel[layerChannelIndices["RGBA_dome.g"]], 0, delta = 0.001 )
		self.assertAlmostEqual( layersTopLeftPixel[layerChannelIndices["RGBA_dome.b"]], 0, delta = 0.001 )

		# Default layer gets nothing on the sphere.
		self.assertAlmostEqual( layersMidPixel[layerChannelIndices["RGBA_default.r"]], 0.0, delta = 0.001 )
		self.assertAlmostEqual( layersMidPixel[layerChannelIndices["RGBA_default.g"]], 0.0, delta = 0.001 )
		self.assertAlmostEqual( layersMidPixel[layerChannelIndices["RGBA_default.b"]], 0.0, delta = 0.001 )
		# And emission from the front portal.
		self.assertGreater( layersTopLeftPixel[layerChannelIndices["RGBA_default.r"]], 0.2 )
		self.assertAlmostEqual( layersTopLeftPixel[layerChannelIndices["RGBA_default.g"]], 0, delta = 0.001 )
		self.assertAlmostEqual( layersTopLeftPixel[layerChannelIndices["RGBA_default.b"]], 0, delta = 0.001 )

	def __assertParameterEqual( self, paramList, name, data, tolerance = None ) :

		p = next( x for x in paramList if x["info"]["name"] == name )
		if tolerance:
			self.assertEqual( len( p["data"] ), len( data ) )
			for c in zip( p["data"], data ):
				self.assertAlmostEqual( c[0], c[1], delta = tolerance )
		else:
			self.assertEqual( p["data"], data )

	def __assertShadingNetworkParameterEqual( self, shadingNetwork, parameter, data ) :

		node = next( node for node in shadingNetwork["nodes"] if node["handle"] == parameter.partition( "." )[0] )
		self.__assertParameterEqual( node["params"]["params"], parameter.partition( "." )[2], data )

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

		if isinstance( image, str ) :
			image = IECoreImage.ImageDisplayDriver.storedImage( image )

		self.assertIsInstance( image, IECoreImage.ImagePrimitive )

		dimensions = image.dataWindow.size() + imath.V2i( 1 )
		ix = int( uv.x * ( dimensions.x - 1 ) )
		iy = int( uv.y * ( dimensions.y - 1 ) )
		i = iy * dimensions.x + ix

		return imath.Color4f( image["R"][i], image["G"][i], image["B"][i], image["A"][i] if "A" in image.keys() else 0.0 )

	def __color3AtUV( self, image, uv ) :

		c = self.__colorAtUV( image, uv )
		return imath.Color3f( c.r, c.g, c.b )

@unittest.skipIf( IECoreRenderMan.renderManMajorVersion() < 27, "XPU only supported for RenderMan 27+" )
class XPURendererTest( RendererTest ) :

	renderer = "RenderManXPU"

	## \todo Figure out why this test fails with XPU. It does seem
	# that XPU will write a checkpoint sometimes, but possibly only if we make
	# the render take longer. It's hard to tell if its actually recovering from
	# checkpoints, but I've been unable to convince myself it is - it certainly
	# doesn't emit the R56049 message we hope for.
	@unittest.skip( "XPU checkpointing status unclear" )
	def testCheckpointing( self ):

		pass

	@unittest.skipIf( GafferTest.inCI(), "XPU segfault on CI" )
	def testMeshLight( self ):

		RendererTest.testMeshLight( self )

	@unittest.skipIf( GafferTest.inCI(), "intermittent XPU segfault on CI" )
	def testPortalLight( self ) :

		RendererTest.testPortalLight( self )

	def testNoDeviceSelection( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			self.renderer,
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
		)

		renderer.output(
			"test",
			IECoreScene.Output(
				( self.temporaryDirectory() / "beauty.exr" ).as_posix(),
				"exr",
				"rgba",
				{
				}
			)
		)

		renderer.option( "ri:xpuCpuConfig", IECore.BoolData( False ) )
		renderer.option( "ri:xpuGpuConfig", IECore.IntVectorData() )

		with IECore.CapturingMessageHandler() as mh :
			renderer.render()
		del renderer

		self.assertEqual( len( mh.messages ), 1 )
		self.assertEqual( mh.messages[0].message, "No XPU device selected. Defaulting to CPU." )
