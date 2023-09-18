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

	def testInvisibleCamera( self ) :

		camera = GafferScene.Camera()

		standardAttributes = GafferScene.StandardAttributes()
		standardAttributes["in"].setInput( camera["out"] )
		standardAttributes["attributes"]["visibility"]["enabled"].setValue( True )
		standardAttributes["attributes"]["visibility"]["value"].setValue( False )

		standardOptions = GafferScene.StandardOptions()
		standardOptions["in"].setInput( standardAttributes["out"] )
		standardOptions["options"]["renderCamera"]["enabled"].setValue( True )
		standardOptions["options"]["renderCamera"]["value"].setValue( "/camera" )

		renderer = GafferScene.Private.IECoreScenePreview.CapturingRenderer(
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
		)
		with self.assertRaisesRegex( RuntimeError, "Camera \"/camera\" is hidden" ) :
			GafferScene.Private.RendererAlgo.outputCameras(
				standardOptions["out"], standardOptions["out"].globals(),
				GafferScene.Private.RendererAlgo.RenderSets( standardOptions["out"] ),
				renderer
			)

	def testCoordinateSystemSamples( self ) :

		coordinateSystem = GafferScene.CoordinateSystem()
		with Gaffer.Context() as c :
			c["scene:path"] = IECore.InternedStringVectorData( [ "coordinateSystem" ] )
			samples = GafferScene.Private.RendererAlgo.objectSamples( coordinateSystem["out"]["object"], [ 0.75, 1.25 ] )
			self.assertEqual( len( samples ), 1 )
			self.assertEqual( samples[0], coordinateSystem["out"].object( "/coordinateSystem" ) )

	def testLightSolo( self ) :

		#   Light                       light:mute      soloLights  Mute Result
		#   ---------------------------------------------------------------------------
		# - lightSolo                   undefined       in          False
		# - light                       undefined       out         True
		# - lightSolo2                  False           in          False
		# - lightMute                   True            out         True
		# --- lightMuteChild            undefined       out         True
		# --- lightMuteChildSolo        undefined       in          False
		# - lightMuteSolo               True            in          True
		# --- lightMuteSoloChild        undefined       out         False
		# --- lightMuteSoloChildSolo    undefined       in          False
		# - groupMute                   True            out         --
		# --- lightGroupMuteChildSolo   undefined       in          False

		lightSolo = GafferSceneTest.TestLight()
		lightSolo["name"].setValue( "lightSolo" )
		light = GafferSceneTest.TestLight()
		light["name"].setValue( "light" )
		lightSolo2 = GafferSceneTest.TestLight()
		lightSolo2["name"].setValue( "lightSolo2" )
		lightMute = GafferSceneTest.TestLight()
		lightMute["name"].setValue( "lightMute" )
		lightMuteChild = GafferSceneTest.TestLight()
		lightMuteChild["name"].setValue( "lightMuteChild" )
		lightMuteChildSolo = GafferSceneTest.TestLight()
		lightMuteChildSolo["name"].setValue( "lightMuteChildSolo" )
		lightMuteSolo = GafferSceneTest.TestLight()
		lightMuteSolo["name"].setValue( "lightMuteSolo" )
		lightMuteSoloChild = GafferSceneTest.TestLight()
		lightMuteSoloChild["name"].setValue( "lightMuteSoloChild" )
		lightMuteSoloChildSolo = GafferSceneTest.TestLight()
		lightMuteSoloChildSolo["name"].setValue( "lightMuteSoloChildSolo" )
		lightGroupMuteChildSolo = GafferSceneTest.TestLight()
		lightGroupMuteChildSolo["name"].setValue( "lightGroupMuteChildSolo" )

		parent = GafferScene.Parent()
		parent["parent"].setValue( "/" )
		parent["children"][0].setInput( lightSolo["out"] )
		parent["children"][1].setInput( light["out"] )
		parent["children"][2].setInput( lightSolo2["out"] )

		parent["children"][3].setInput( lightMute["out"] )

		lightMuteParent = GafferScene.Parent()
		lightMuteParent["in"].setInput( parent["out"] )
		lightMuteParent["parent"].setValue( "/lightMute" )
		lightMuteParent["children"][0].setInput( lightMuteChild["out"] )
		lightMuteParent["children"][1].setInput( lightMuteChildSolo["out"] )

		parent["children"][4].setInput( lightMuteSolo["out"] )

		lightMuteSoloParent = GafferScene.Parent()
		lightMuteSoloParent["in"].setInput( lightMuteParent["out"] )
		lightMuteSoloParent["parent"].setValue( "/lightMuteSolo" )
		lightMuteSoloParent["children"][0].setInput( lightMuteSoloChild["out"] )
		lightMuteSoloParent["children"][1].setInput( lightMuteSoloChildSolo["out"] )

		groupMute = GafferScene.Group()
		groupMute["name"].setValue( "groupMute" )
		groupMute["in"][0].setInput( lightGroupMuteChildSolo["out"] )

		parent["children"][5].setInput( groupMute["out"] )

		unMuteFilter = GafferScene.PathFilter()
		unMuteFilter["paths"].setValue(
			IECore.StringVectorData( [ "/lightSolo2" ] )
		)
		unMuteAttributes = GafferScene.CustomAttributes()
		unMuteAttributes["in"].setInput( lightMuteSoloParent["out"] )
		unMuteAttributes["filter"].setInput( unMuteFilter["out"] )
		unMuteAttributes["attributes"].addChild( Gaffer.NameValuePlug( "light:mute", False ) )

		muteFilter = GafferScene.PathFilter()
		muteFilter["paths"].setValue(
			IECore.StringVectorData( [ "/lightMute", "/lightMuteSolo", "/groupMute" ] )
		)
		muteAttributes = GafferScene.CustomAttributes()
		muteAttributes["in"].setInput( unMuteAttributes["out"] )
		muteAttributes["filter"].setInput( muteFilter["out"] )
		muteAttributes["attributes"].addChild( Gaffer.NameValuePlug( "light:mute", True ) )

		soloFilter = GafferScene.PathFilter()
		soloFilter["paths"].setValue(
			IECore.StringVectorData(
				[
					"/lightSolo",
					"/lightSolo2",
					"/lightMute/lightMuteChildSolo",
					"/lightMuteSolo",
					"/lightMuteSolo/lightMuteSoloChildSolo",
					"/groupMute/lightGroupMuteChildSolo",
				]
			)
		)

		soloSet = GafferScene.Set()
		soloSet["in"].setInput( muteAttributes["out"])
		soloSet["name"].setValue( "soloLights" )
		soloSet["filter"].setInput( soloFilter["out"] )

		# Make sure we got the hierarchy, attributes and set right
		self.assertEqual(
			parent["out"].childNames( "/" ),
			IECore.InternedStringVectorData( [ "lightSolo", "light", "lightSolo2", "lightMute", "lightMuteSolo", "groupMute", ] )
		)
		self.assertEqual(
			soloSet["out"].childNames( "/lightMute" ),
			IECore.InternedStringVectorData( [ "lightMuteChild", "lightMuteChildSolo", ] )
		)
		self.assertEqual(
			soloSet["out"].childNames( "/lightMuteSolo" ),
			IECore.InternedStringVectorData( [ "lightMuteSoloChild", "lightMuteSoloChildSolo", ] )
		)
		self.assertEqual(
			soloSet["out"].childNames( "/groupMute" ),
			IECore.InternedStringVectorData( [ "lightGroupMuteChildSolo", ] )
		)
		self.assertNotIn( "light:mute", soloSet["out"].attributes( "/lightSolo" ) )
		self.assertNotIn( "light:mute", soloSet["out"].attributes( "/light" ) )
		self.assertFalse( soloSet["out"].attributes( "/lightSolo2" )["light:mute"].value )
		self.assertTrue( soloSet["out"].attributes( "/lightMute" )["light:mute"].value )
		self.assertNotIn( "light:mute", soloSet["out"].attributes( "/lightMute/lightMuteChild" ) )
		self.assertNotIn( "light:mute", soloSet["out"].attributes( "/lightMute/lightMuteChildSolo" ) )
		self.assertTrue( soloSet["out"].attributes( "/lightMuteSolo" )["light:mute"].value )
		self.assertNotIn( "light:mute", soloSet["out"].attributes( "/lightMuteSolo/lightMuteSoloChild" ) )
		self.assertNotIn( "light:mute", soloSet["out"].attributes( "/lightMuteSolo/lightMuteSoloChildSolo" ) )
		self.assertTrue( soloSet["out"].attributes( "/groupMute" )["light:mute"].value )
		self.assertNotIn( "light:mute", soloSet["out"].attributes( "/groupMute/lightGroupMuteChildSolo" ) )
		self.assertTrue( "light:mute", soloSet["out"].fullAttributes( "/groupMute/lightGroupMuteChildSolo" ) )

		self.assertEqual(
			sorted( soloSet["out"].set( "soloLights" ).value.paths() ),
			sorted(
				[
					"/lightSolo",
					"/lightSolo2",
					"/lightMute/lightMuteChildSolo",
					"/lightMuteSolo",
					"/lightMuteSolo/lightMuteSoloChildSolo",
					"/groupMute/lightGroupMuteChildSolo",
				]
			)
		)

		# Output the lights to the renderer

		renderSets = GafferScene.Private.RendererAlgo.RenderSets( soloSet["out"] )
		lightLinks = GafferScene.Private.RendererAlgo.LightLinks()

		renderer = GafferScene.Private.IECoreScenePreview.CapturingRenderer(
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
		)
		sceneGlobals = soloSet["out"].globals()
		GafferScene.Private.RendererAlgo.outputLights( soloSet["out"], sceneGlobals, renderSets, lightLinks, renderer )

		# Check that the output is correct

		self.assertFalse( renderer.capturedObject( "/lightSolo" ).capturedAttributes().attributes()["light:mute"].value )
		self.assertTrue( renderer.capturedObject( "/light" ).capturedAttributes().attributes()["light:mute"].value )
		self.assertFalse( renderer.capturedObject( "/lightSolo2" ).capturedAttributes().attributes()["light:mute"].value )
		self.assertTrue( renderer.capturedObject( "/lightMute" ).capturedAttributes().attributes()["light:mute"].value )
		self.assertTrue( renderer.capturedObject( "/lightMute/lightMuteChild" ).capturedAttributes().attributes()["light:mute"].value )
		self.assertFalse( renderer.capturedObject( "/lightMute/lightMuteChildSolo" ).capturedAttributes().attributes()["light:mute"].value )
		self.assertTrue( renderer.capturedObject( "/lightMuteSolo" ).capturedAttributes().attributes()["light:mute"].value )
		self.assertFalse( renderer.capturedObject( "/lightMuteSolo/lightMuteSoloChild" ).capturedAttributes().attributes()["light:mute"].value )
		self.assertFalse( renderer.capturedObject( "/lightMuteSolo/lightMuteSoloChildSolo" ).capturedAttributes().attributes()["light:mute"].value )
		self.assertFalse( renderer.capturedObject( "/groupMute/lightGroupMuteChildSolo" ).capturedAttributes().attributes()["light:mute"].value )

	def testLightMute( self ) :

		#   Light                   light:mute      Muted Result
		#   --------------------------------------------------------
		# - lightMute               True            True
		# - light                   undefined       undefined
		# - lightMute2              True            True
		# - lightMute3              True            True
		# --- lightMute3Child       False           False
		# - light2                  undefined       undefined
		# --- light2ChildMute       True            True
		# --- light2Child           False           False
		# - groupMute               True            --
		# --- lightGroupMuteChild   undefined       True (inherited)

		lightMute = GafferSceneTest.TestLight()
		lightMute["name"].setValue( "lightMute" )
		light = GafferSceneTest.TestLight()
		light["name"].setValue( "light" )
		lightMute2 = GafferSceneTest.TestLight()
		lightMute2["name"].setValue( "lightMute2" )
		lightMute3 = GafferSceneTest.TestLight()
		lightMute3["name"].setValue( "lightMute3" )
		lightMute3Child = GafferSceneTest.TestLight()
		lightMute3Child["name"].setValue( "lightMute3Child" )
		light2 = GafferSceneTest.TestLight()
		light2["name"].setValue( "light2" )
		light2ChildMute = GafferSceneTest.TestLight()
		light2ChildMute["name"].setValue( "light2ChildMute" )
		light2Child = GafferSceneTest.TestLight()
		light2Child["name"].setValue( "light2Child" )
		lightGroupMuteChild = GafferSceneTest.TestLight()
		lightGroupMuteChild["name"].setValue( "lightGroupMuteChild" )

		parent = GafferScene.Parent()
		parent["parent"].setValue( "/" )
		parent["children"][0].setInput( lightMute["out"] )
		parent["children"][1].setInput( light["out"] )
		parent["children"][2].setInput( lightMute2["out"] )
		parent["children"][3].setInput( lightMute3["out"] )

		lightMute3Parent = GafferScene.Parent()
		lightMute3Parent["in"].setInput( parent["out"] )
		lightMute3Parent["parent"].setValue( "/lightMute3" )
		lightMute3Parent["children"][0].setInput( lightMute3Child["out"] )

		parent["children"][4].setInput( light2["out"] )

		light2Parent = GafferScene.Parent()
		light2Parent["in"].setInput( lightMute3Parent["out"] )
		light2Parent["parent"].setValue( "/light2" )
		light2Parent["children"][0].setInput( light2ChildMute["out"] )
		light2Parent["children"][1].setInput( light2Child["out"] )

		groupMute = GafferScene.Group()
		groupMute["name"].setValue( "groupMute" )
		groupMute["in"][0].setInput( lightGroupMuteChild["out"] )

		parent["children"][5].setInput( groupMute["out"] )

		unMuteFilter = GafferScene.PathFilter()
		unMuteFilter["paths"].setValue(
			IECore.StringVectorData( [ "/lightMute3/lightMute3Child", "/light2/light2Child" ] )
		)
		unMuteAttributes = GafferScene.CustomAttributes()
		unMuteAttributes["in"].setInput( light2Parent["out"] )
		unMuteAttributes["filter"].setInput( unMuteFilter["out"] )
		unMuteAttributes["attributes"].addChild( Gaffer.NameValuePlug( "light:mute", False ) )

		muteFilter = GafferScene.PathFilter()
		muteFilter["paths"].setValue(
			IECore.StringVectorData( [ "/lightMute", "/lightMute2", "/lightMute3", "/light2/light2ChildMute", "/groupMute" ] )
		)
		muteAttributes = GafferScene.CustomAttributes()
		muteAttributes["in"].setInput( unMuteAttributes["out"] )
		muteAttributes["filter"].setInput( muteFilter["out"] )
		muteAttributes["attributes"].addChild( Gaffer.NameValuePlug( "light:mute", True ) )

		# Make sure we got the hierarchy and attributes right
		self.assertEqual(
			parent["out"].childNames( "/" ),
			IECore.InternedStringVectorData( [ "lightMute", "light", "lightMute2", "lightMute3", "light2", "groupMute", ] )
		)
		self.assertEqual(
			muteAttributes["out"].childNames( "/lightMute3" ),
			IECore.InternedStringVectorData( [ "lightMute3Child", ] )
		)
		self.assertEqual(
			muteAttributes["out"].childNames( "/light2" ),
			IECore.InternedStringVectorData( [ "light2ChildMute", "light2Child", ] )
		)
		self.assertEqual(
			muteAttributes["out"].childNames( "/groupMute" ),
			IECore.InternedStringVectorData( [ "lightGroupMuteChild", ] )
		)
		self.assertTrue( muteAttributes["out"].attributes( "/lightMute" )["light:mute"].value )
		self.assertNotIn( "light:mute", muteAttributes["out"].attributes( "/light" ) )
		self.assertTrue( muteAttributes["out"].attributes( "/lightMute2" )["light:mute"].value )
		self.assertTrue( muteAttributes["out"].attributes( "/lightMute3" )["light:mute"].value )
		self.assertFalse( muteAttributes["out"].attributes( "/lightMute3/lightMute3Child" )["light:mute"].value )
		self.assertNotIn( "light:mute", muteAttributes["out"].attributes( "/light2" ) )
		self.assertTrue( muteAttributes["out"].attributes( "/light2/light2ChildMute" )["light:mute"].value )
		self.assertFalse( muteAttributes["out"].attributes( "/light2/light2Child" )["light:mute"].value )
		self.assertTrue( muteAttributes["out"].attributes( "/groupMute" )["light:mute"].value )
		self.assertNotIn( "light:mute", muteAttributes["out"].attributes( "/groupMute/lightGroupMuteChild" ) )
		self.assertTrue( muteAttributes["out"].fullAttributes( "/groupMute/lightGroupMuteChild" ) )

		# Output the lights to the renderer

		renderSets = GafferScene.Private.RendererAlgo.RenderSets( muteAttributes["out"] )
		lightLinks = GafferScene.Private.RendererAlgo.LightLinks()

		renderer = GafferScene.Private.IECoreScenePreview.CapturingRenderer(
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
		)
		sceneGlobals = muteAttributes["out"].globals()
		GafferScene.Private.RendererAlgo.outputLights( muteAttributes["out"], sceneGlobals, renderSets, lightLinks, renderer )

		# Check that the output is correct

		self.assertTrue( renderer.capturedObject( "/lightMute" ).capturedAttributes().attributes()["light:mute"].value )
		self.assertNotIn( "light:mute", renderer.capturedObject( "/light" ).capturedAttributes().attributes() )
		self.assertTrue( renderer.capturedObject( "/lightMute2" ).capturedAttributes().attributes()["light:mute"] .value)
		self.assertTrue( renderer.capturedObject( "/lightMute3" ).capturedAttributes().attributes()["light:mute"].value )
		self.assertFalse( renderer.capturedObject( "/lightMute3/lightMute3Child" ).capturedAttributes().attributes()["light:mute"].value )
		self.assertNotIn( "light:mute", renderer.capturedObject( "/light2" ).capturedAttributes().attributes() )
		self.assertTrue( renderer.capturedObject( "/light2/light2ChildMute" ).capturedAttributes().attributes()["light:mute"].value )
		self.assertFalse( renderer.capturedObject( "/light2/light2Child" ).capturedAttributes().attributes()["light:mute"].value )
		self.assertTrue( renderer.capturedObject( "/groupMute/lightGroupMuteChild" ).capturedAttributes().attributes()["light:mute"].value )

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

	def testObjectSamplesCancellation( self ) :

		sphere = GafferScene.Sphere()
		sphere["type"].setValue( sphere.Type.Primitive )

		# Cache the hash now, so `objectSamples()` can get the hash without
		# it being cancelled.
		sphere["out"].objectHash( "/sphere" )

		# Call `objectSamples()` with a canceller that will immediately
		# cancel any attempt to get the object.

		canceller = IECore.Canceller()
		canceller.cancel()

		context = Gaffer.Context()
		context["scene:path"] = IECore.InternedStringVectorData( [ "sphere" ] )
		cancelledContext = Gaffer.Context( context, canceller )

		with cancelledContext :

			h = IECore.MurmurHash()
			with self.assertRaises( IECore.Cancelled ) :
				GafferScene.Private.RendererAlgo.objectSamples( sphere["out"]["object"], [ 1.0 ], h )

			# The hash should not have been updated, so that when we use
			# it in a non-cancelled context, we get some samples returned.
			self.assertEqual( h, IECore.MurmurHash() )

		with context :

			samples = GafferScene.Private.RendererAlgo.objectSamples( sphere["out"]["object"], [ 1.0 ], h )
			self.assertEqual( [ s.radius() for s in samples ], [ 1.0 ] )
			self.assertNotEqual( h, IECore.MurmurHash() )

	def testTransformSamplesCancellation( self ) :

		sphere = GafferScene.Sphere()

		# Cache the hash now, so `transformSamples()` can get the hash without
		# it being cancelled.
		sphere["out"].transformHash( "/sphere" )

		# Call `transformSamples()` with a canceller that will immediately
		# cancel any attempt to get the object.

		canceller = IECore.Canceller()
		canceller.cancel()

		context = Gaffer.Context()
		context["scene:path"] = IECore.InternedStringVectorData( [ "sphere" ] )
		cancelledContext = Gaffer.Context( context, canceller )

		with cancelledContext :

			h = IECore.MurmurHash()
			with self.assertRaises( IECore.Cancelled ) :
				GafferScene.Private.RendererAlgo.transformSamples( sphere["out"]["transform"], [ 1.0 ], h )

			# The hash should not have been updated, so that when we use
			# it in a non-cancelled context, we get some samples returned.
			self.assertEqual( h, IECore.MurmurHash() )

		with context :

			samples = GafferScene.Private.RendererAlgo.transformSamples( sphere["out"]["transform"], [ 1.0 ], h )
			self.assertEqual( [ s.translation().x for s in samples ], [ 0.0 ] )
			self.assertNotEqual( h, IECore.MurmurHash() )

	def testPurposes( self ) :

		# /group
		#    /innerGroup1   (default)
		#		 /cube
		#        /sphere    (render)
		#    /innerGroup2
		#        /cube      (proxy)
		#        /sphere

		def purposeAttribute( purpose ) :

			result = GafferScene.CustomAttributes()
			result["attributes"].addChild( Gaffer.NameValuePlug( "usd:purpose", purpose ) )
			return result

		rootFilter = GafferScene.PathFilter()
		rootFilter["paths"].setValue( IECore.StringVectorData( [ "*" ] ) )

		cube = GafferScene.Cube()

		renderSphere = GafferScene.Sphere()
		renderSphereAttributes = purposeAttribute( "render" )
		renderSphereAttributes["in"].setInput( renderSphere["out"] )
		renderSphereAttributes["filter"].setInput( rootFilter["out"] )

		innerGroup1 = GafferScene.Group()
		innerGroup1["name"].setValue( "innerGroup1" )
		innerGroup1["in"][0].setInput( cube["out"] )
		innerGroup1["in"][1].setInput( renderSphereAttributes["out"] )

		innerGroup1Attributes = purposeAttribute( "default" )
		innerGroup1Attributes["in"].setInput( innerGroup1["out"] )
		innerGroup1Attributes["filter"].setInput( rootFilter["out"] )

		proxyCube = GafferScene.Cube()

		proxyCubeAttributes = purposeAttribute( "proxy" )
		proxyCubeAttributes["in"].setInput( proxyCube["out"] )
		proxyCubeAttributes["filter"].setInput( rootFilter["out"] )

		sphere = GafferScene.Sphere()

		innerGroup2 = GafferScene.Group()
		innerGroup2["name"].setValue( "innerGroup2" )
		innerGroup2["in"][0].setInput( proxyCubeAttributes["out"] )
		innerGroup2["in"][1].setInput( sphere["out"] )

		group = GafferScene.Group()
		group["in"][0].setInput( innerGroup1Attributes["out"] )
		group["in"][1].setInput( innerGroup2["out"] )

		def assertIncludedObjects( scene, includedPurposes, paths ) :

			globals = IECore.CompoundObject()
			if includedPurposes :
				globals["option:render:includedPurposes"] = IECore.StringVectorData( includedPurposes )

			renderer = GafferScene.Private.IECoreScenePreview.CapturingRenderer(
				GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
			)
			GafferScene.Private.RendererAlgo.outputObjects(
				group["out"], globals, GafferScene.Private.RendererAlgo.RenderSets( scene ), GafferScene.Private.RendererAlgo.LightLinks(),
				renderer
			)

			allPaths = {
				"/group/innerGroup1/cube",
				"/group/innerGroup1/sphere",
				"/group/innerGroup2/cube",
				"/group/innerGroup2/sphere",
			}

			self.assertTrue( paths.issubset( allPaths ) )
			for path in allPaths :
				if path in paths :
					self.assertIsNotNone( renderer.capturedObject( path ) )
				else :
					self.assertIsNone( renderer.capturedObject( path ) )

		# If we don't specify a purpose, then we should get everything.

		assertIncludedObjects(
			group["out"], None,
			{
				"/group/innerGroup1/cube",
				"/group/innerGroup1/sphere",
				"/group/innerGroup2/cube",
				"/group/innerGroup2/sphere",
			}
		)

		# The default purpose should pick objects without any purpose attribute,
		# and those that explicitly have a value of "default".

		assertIncludedObjects(
			group["out"], [ "default" ],
			{
				"/group/innerGroup1/cube",
				"/group/innerGroup2/sphere",
			}
		)

		# Purpose-based visibility isn't pruning, so we can see a child location
		# with the right purpose even if it is parented below a location with the
		# wrong purpose.

		assertIncludedObjects(
			group["out"], [ "render" ],
			{
				"/group/innerGroup1/sphere",
			}
		)

		assertIncludedObjects(
			group["out"], [ "proxy" ],
			{
				"/group/innerGroup2/cube",
			}
		)

		# Multiple purposes can be rendered at once.

		assertIncludedObjects(
			group["out"], [ "render", "default" ],
			{
				"/group/innerGroup1/cube",
				"/group/innerGroup1/sphere",
				"/group/innerGroup2/sphere",
			}
		)

		assertIncludedObjects(
			group["out"], [ "proxy", "default" ],
			{
				"/group/innerGroup1/cube",
				"/group/innerGroup2/cube",
				"/group/innerGroup2/sphere",
			}
		)

		assertIncludedObjects(
			group["out"], [ "render", "proxy", "default" ],
			{
				"/group/innerGroup1/cube",
				"/group/innerGroup1/sphere",
				"/group/innerGroup2/cube",
				"/group/innerGroup2/sphere",
			}
		)

		assertIncludedObjects(
			group["out"], [ "proxy", "render" ],
			{
				"/group/innerGroup1/sphere",
				"/group/innerGroup2/cube",
			}
		)

if __name__ == "__main__":
	unittest.main()
