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

	def test( self ) :

		sphere = GafferScene.Sphere()

		defaultAdaptors = GafferScene.RendererAlgo.createAdaptors()
		defaultAdaptors["in"].setInput( sphere["out"] )

		def a() :

			r = GafferScene.StandardAttributes()
			r["attributes"]["doubleSided"]["enabled"].setValue( True )
			r["attributes"]["doubleSided"]["value"].setValue( False )

			return r

		GafferScene.RendererAlgo.registerAdaptor( "Test", a )

		testAdaptors = GafferScene.RendererAlgo.createAdaptors()
		testAdaptors["in"].setInput( sphere["out"] )

		self.assertFalse( "doubleSided" in sphere["out"].attributes( "/sphere" ) )
		self.assertTrue( "doubleSided" in testAdaptors["out"].attributes( "/sphere" ) )
		self.assertEqual( testAdaptors["out"].attributes( "/sphere" )["doubleSided"].value, False )

		GafferScene.RendererAlgo.deregisterAdaptor( "Test" )

		defaultAdaptors2 = GafferScene.RendererAlgo.createAdaptors()
		defaultAdaptors2["in"].setInput( sphere["out"] )

		self.assertScenesEqual( defaultAdaptors["out"], defaultAdaptors2["out"] )
		self.assertSceneHashesEqual( defaultAdaptors["out"], defaultAdaptors2["out"] )

	def testNullAdaptor( self ) :

		def a() :

			return None

		GafferScene.RendererAlgo.registerAdaptor( "Test", a )

		with IECore.CapturingMessageHandler() as mh :
			GafferScene.RendererAlgo.createAdaptors()

		self.assertEqual( len( mh.messages ), 1 )
		self.assertEqual( mh.messages[0].level, IECore.Msg.Level.Warning )
		self.assertEqual( mh.messages[0].context, "RendererAlgo::createAdaptors" )
		self.assertEqual( mh.messages[0].message, "Adaptor \"Test\" returned null" )

	def testObjectSamples( self ) :

		frame = GafferTest.FrameNode()

		sphere = GafferScene.Sphere()
		sphere["type"].setValue( sphere.Type.Primitive )
		sphere["radius"].setInput( frame["output"] )

		with Gaffer.Context() as c :
			c["scene:path"] = IECore.InternedStringVectorData( [ "sphere" ] )
			samples = GafferScene.RendererAlgo.objectSamples( sphere["out"]["object"], [ 0.75, 1.25 ] )

		self.assertEqual( [ s.radius() for s in samples ], [ 0.75, 1.25 ] )

	def testNonInterpolableObjectSamples( self ) :

		frame = GafferTest.FrameNode()

		procedural = GafferScene.ExternalProcedural()
		procedural["parameters"]["frame"] = Gaffer.NameValuePlug( "frame", 0.0 )
		procedural["parameters"]["frame"]["value"].setInput( frame["output"] )

		with Gaffer.Context() as c :
			c["scene:path"] = IECore.InternedStringVectorData( [ "procedural" ] )
			samples = GafferScene.RendererAlgo.objectSamples( procedural["out"]["object"], [ 0.75, 1.25 ] )

		self.assertEqual( len( samples ), 1 )
		self.assertEqual( samples[0].parameters()["frame"].value, 1.0 )

	def testObjectSamplesForCameras( self ) :

		frame = GafferTest.FrameNode()
		camera = GafferScene.Camera()
		camera["perspectiveMode"].setValue( camera.PerspectiveMode.ApertureFocalLength )
		camera["focalLength"].setInput( frame["output"] )

		with Gaffer.Context() as c :
			c["scene:path"] = IECore.InternedStringVectorData( [ "camera" ] )
			samples = GafferScene.RendererAlgo.objectSamples( camera["out"]["object"], [ 0.75, 1.25 ] )

		self.assertEqual( [ s.parameters()["focalLength"].value for s in samples ], [ 0.75, 1.25 ] )

	def testOutputCameras( self ) :

		frame = GafferTest.FrameNode()
		camera = GafferScene.Camera()
		camera["perspectiveMode"].setValue( camera.PerspectiveMode.ApertureFocalLength )
		camera["focalLength"].setInput( frame["output"] )

		options = GafferScene.StandardOptions()
		options["in"].setInput( camera["out"] )

		renderSets = GafferScene.RendererAlgo.RenderSets( options["out"] )

		def expectedCamera( frame ) :

			with Gaffer.Context() as c :
				c.setFrame( frame )
				camera = options["out"].object( "/camera" )

			GafferScene.RendererAlgo.applyCameraGlobals( camera, sceneGlobals, options["out"] )
			return camera

		# Non-animated case

		renderer = GafferScene.Private.IECoreScenePreview.CapturingRenderer(
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
		)
		sceneGlobals = options["out"].globals()
		GafferScene.RendererAlgo.outputCameras( options["out"], sceneGlobals, renderSets, renderer )

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
		GafferScene.RendererAlgo.outputCameras( options["out"], sceneGlobals, renderSets, renderer )

		capturedCamera = renderer.capturedObject( "/camera" )
		self.assertEqual( capturedCamera.capturedSamples(), [ expectedCamera( 0.75 ), expectedCamera( 1.25 ) ] )
		self.assertEqual( capturedCamera.capturedSampleTimes(), [ 0.75, 1.25 ] )

	def tearDown( self ) :

		GafferSceneTest.SceneTestCase.tearDown( self )
		GafferScene.RendererAlgo.deregisterAdaptor( "Test" )

if __name__ == "__main__":
	unittest.main()
