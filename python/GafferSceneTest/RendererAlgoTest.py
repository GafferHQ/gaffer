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

import unittest

import imath

import IECore

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest

class RendererAlgoTest( GafferSceneTest.SceneTestCase ) :

	def testObjectSamples( self ) :

		frame = GafferTest.FrameNode()

		sphere = GafferScene.Sphere()
		sphere["type"].setValue( sphere.Type.Primitive )
		sphere["radius"].setInput( frame["output"] )

		with Gaffer.Context() as c :
			c["scene:path"] = IECore.InternedStringVectorData( [ "sphere" ] )
			samples = GafferScene.Private.RendererAlgo.objectSamples( sphere["out"]["object"], [ 0.75, 1.25 ] )

		self.assertEqual( [ s.radius() for s in samples ], [ 0.75, 1.25 ] )

	def testNonInterpolableObjectSamples( self ) :

		frame = GafferTest.FrameNode()

		procedural = GafferScene.ExternalProcedural()
		procedural["parameters"]["frame"] = Gaffer.NameValuePlug( "frame", 0.0 )
		procedural["parameters"]["frame"]["value"].setInput( frame["output"] )

		with Gaffer.Context() as c :
			c["scene:path"] = IECore.InternedStringVectorData( [ "procedural" ] )
			samples = GafferScene.Private.RendererAlgo.objectSamples( procedural["out"]["object"], [ 0.75, 1.25 ] )

		self.assertEqual( len( samples ), 1 )
		self.assertEqual( samples[0].parameters()["frame"].value, 1.0 )

	def testObjectSamplesForCameras( self ) :

		frame = GafferTest.FrameNode()
		camera = GafferScene.Camera()
		camera["perspectiveMode"].setValue( camera.PerspectiveMode.ApertureFocalLength )
		camera["focalLength"].setInput( frame["output"] )

		with Gaffer.Context() as c :
			c["scene:path"] = IECore.InternedStringVectorData( [ "camera" ] )
			samples = GafferScene.Private.RendererAlgo.objectSamples( camera["out"]["object"], [ 0.75, 1.25 ] )

		self.assertEqual( [ s.parameters()["focalLength"].value for s in samples ], [ 0.75, 1.25 ] )

	def testOutputCameras( self ) :

		frame = GafferTest.FrameNode()
		camera = GafferScene.Camera()
		camera["perspectiveMode"].setValue( camera.PerspectiveMode.ApertureFocalLength )
		camera["focalLength"].setInput( frame["output"] )

		options = GafferScene.StandardOptions()
		options["in"].setInput( camera["out"] )

		renderSets = GafferScene.Private.RendererAlgo.RenderSets( options["out"] )

		def expectedCamera( frame ) :

			with Gaffer.Context() as c :
				c.setFrame( frame )
				camera = options["out"].object( "/camera" )

			GafferScene.SceneAlgo.applyCameraGlobals( camera, sceneGlobals, options["out"] )
			return camera

		# Non-animated case

		renderer = GafferScene.Private.IECoreScenePreview.CapturingRenderer(
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
		)
		sceneGlobals = options["out"].globals()
		GafferScene.Private.RendererAlgo.outputCameras( options["out"], sceneGlobals, renderSets, renderer )

		capturedCamera = renderer.capturedObject( "/camera" )

		self.assertEqual( capturedCamera.capturedSamples(), [ expectedCamera( 1 ) ] )
		self.assertEqual( capturedCamera.capturedSampleTimes(), [] )

		# Animated case

		options["options"]["deformationBlur"]["enabled"].setValue( True )
		options["options"]["deformationBlur"]["value"].setValue( True )

		renderer = GafferScene.Private.IECoreScenePreview.CapturingRenderer(
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
		)
		sceneGlobals = options["out"].globals()
		GafferScene.Private.RendererAlgo.outputCameras( options["out"], sceneGlobals, renderSets, renderer )

		capturedCamera = renderer.capturedObject( "/camera" )
		self.assertEqual( capturedCamera.capturedSamples(), [ expectedCamera( 0.75 ), expectedCamera( 1.25 ) ] )
		self.assertEqual( capturedCamera.capturedSampleTimes(), [ 0.75, 1.25 ] )

	def testCoordinateSystemSamples( self ) :

		coordinateSystem = GafferScene.CoordinateSystem()
		with Gaffer.Context() as c :
			c["scene:path"] = IECore.InternedStringVectorData( [ "coordinateSystem" ] )
			samples = GafferScene.Private.RendererAlgo.objectSamples( coordinateSystem["out"]["object"], [ 0.75, 1.25 ] )
			self.assertEqual( len( samples ), 1 )
			self.assertEqual( samples[0], coordinateSystem["out"].object( "/coordinateSystem" ) )

	def testObjectSamplesHash( self ) :

		sphere = GafferScene.Sphere()
		sphere["type"].setValue( sphere.Type.Primitive )

		with Gaffer.Context() as c :

			c["scene:path"] = IECore.InternedStringVectorData( [ "sphere" ] )

			h1 = IECore.MurmurHash()
			samples1 = GafferScene.Private.RendererAlgo.objectSamples( sphere["out"]["object"], [ 1.0 ], h1 )
			self.assertEqual( samples1[0].radius(), 1 )
			self.assertNotEqual( h1, IECore.MurmurHash() )

			sphere["radius"].setValue( 2 )
			h2 = IECore.MurmurHash( h1 )
			samples2 = GafferScene.Private.RendererAlgo.objectSamples( sphere["out"]["object"], [ 1.0 ], h2 )
			self.assertEqual( samples2[0].radius(), 2 )
			self.assertNotEqual( h2, IECore.MurmurHash() )
			self.assertNotEqual( h2, h1 )

			h3 = IECore.MurmurHash( h2 )
			samples3 = GafferScene.Private.RendererAlgo.objectSamples( sphere["out"]["object"], [ 1.0 ], h3 )
			self.assertIsNone( samples3 ) # Hash matched, so no samples generated
			self.assertEqual( h3, h2 )

	def testTransformSamplesHash( self ) :

		sphere = GafferScene.Sphere()

		with Gaffer.Context() as c :

			c["scene:path"] = IECore.InternedStringVectorData( [ "sphere" ] )

			h1 = IECore.MurmurHash()
			samples1 = GafferScene.Private.RendererAlgo.transformSamples( sphere["out"]["transform"], [ 1.0 ], h1 )
			self.assertEqual( samples1[0].translation().x, 0 )
			self.assertNotEqual( h1, IECore.MurmurHash() )

			sphere["transform"]["translate"]["x"].setValue( 2 )
			h2 = IECore.MurmurHash( h1 )
			samples2 = GafferScene.Private.RendererAlgo.transformSamples( sphere["out"]["transform"], [ 1.0 ], h2 )
			self.assertEqual( samples2[0].translation().x, 2 )
			self.assertNotEqual( h2, IECore.MurmurHash() )
			self.assertNotEqual( h2, h1 )

			h3 = IECore.MurmurHash( h2 )
			samples3 = GafferScene.Private.RendererAlgo.transformSamples( sphere["out"]["transform"], [ 1.0 ], h3 )
			self.assertIsNone( samples3 ) # Hash matched, so no samples generated
			self.assertEqual( h3, h2 )

if __name__ == "__main__":
	unittest.main()
