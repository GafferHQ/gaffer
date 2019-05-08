##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

import os
import inspect
import unittest
import subprocess32 as subprocess
import threading

import arnold
import imath

import IECore
import IECoreImage
import IECoreScene
import IECoreArnold

import Gaffer
import GafferTest
import GafferDispatch
import GafferImage
import GafferScene
import GafferSceneTest
import GafferOSL
import GafferArnold
import GafferArnoldTest

class ArnoldRenderTest( GafferSceneTest.SceneTestCase ) :

	def setUp( self ) :

		GafferSceneTest.SceneTestCase.setUp( self )

		self.__scriptFileName = self.temporaryDirectory() + "/test.gfr"

	def tearDown( self ) :

		GafferSceneTest.SceneTestCase.tearDown( self )

		GafferScene.deregisterAdaptor( "Test" )

	def testExecute( self ) :

		s = Gaffer.ScriptNode()

		s["plane"] = GafferScene.Plane()
		s["render"] = GafferArnold.ArnoldRender()
		s["render"]["mode"].setValue( s["render"].Mode.SceneDescriptionMode )
		s["render"]["in"].setInput( s["plane"]["out"] )

		s["expression"] = Gaffer.Expression()
		s["expression"].setExpression( "parent['render']['fileName'] = '" + self.temporaryDirectory() + "/test.%d.ass' % int( context['frame'] )" )

		s["fileName"].setValue( self.__scriptFileName )
		s.save()

		p = subprocess.Popen(
			"gaffer execute " + self.__scriptFileName + " -frames 1-3",
			shell=True,
			stderr = subprocess.PIPE,
		)
		p.wait()
		self.failIf( p.returncode )

		for i in range( 1, 4 ) :
			self.failUnless( os.path.exists( self.temporaryDirectory() + "/test.%d.ass" % i ) )

	def testWaitForImage( self ) :

		s = Gaffer.ScriptNode()

		s["plane"] = GafferScene.Plane()

		s["outputs"] = GafferScene.Outputs()
		s["outputs"].addOutput(
			"beauty",
			IECoreScene.Output(
				self.temporaryDirectory() + "/test.tif",
				"tiff",
				"rgba",
				{}
			)
		)
		s["outputs"]["in"].setInput( s["plane"]["out"] )

		s["render"] = GafferArnold.ArnoldRender()
		s["render"]["in"].setInput( s["outputs"]["out"] )
		s["render"]["task"].execute()

		self.failUnless( os.path.exists( self.temporaryDirectory() + "/test.tif" ) )

	def testExecuteWithStringSubstitutions( self ) :

		s = Gaffer.ScriptNode()

		s["plane"] = GafferScene.Plane()
		s["render"] = GafferArnold.ArnoldRender()
		s["render"]["mode"].setValue( s["render"].Mode.SceneDescriptionMode )
		s["render"]["in"].setInput( s["plane"]["out"] )
		s["render"]["fileName"].setValue( self.temporaryDirectory() + "/test.####.ass" )

		s["fileName"].setValue( self.__scriptFileName )
		s.save()

		p = subprocess.Popen(
			"gaffer execute " + self.__scriptFileName + " -frames 1-3",
			shell=True,
			stderr = subprocess.PIPE,
		)
		p.wait()
		self.failIf( p.returncode )

		for i in range( 1, 4 ) :
			self.failUnless( os.path.exists( self.temporaryDirectory() + "/test.%04d.ass" % i ) )

	def testImageOutput( self ) :

		s = Gaffer.ScriptNode()

		s["plane"] = GafferScene.Plane()

		s["outputs"] = GafferScene.Outputs()
		s["outputs"].addOutput(
			"beauty",
			IECoreScene.Output(
				self.temporaryDirectory() + "/test.####.tif",
				"tiff",
				"rgba",
				{}
			)
		)
		s["outputs"]["in"].setInput( s["plane"]["out"] )

		s["render"] = GafferArnold.ArnoldRender()
		s["render"]["in"].setInput( s["outputs"]["out"] )

		c = Gaffer.Context()
		for i in range( 1, 4 ) :
			c.setFrame( i )
			with c :
				s["render"]["task"].execute()

		for i in range( 1, 4 ) :
			self.failUnless( os.path.exists( self.temporaryDirectory() + "/test.%04d.tif" % i ) )

	def testTypeNamePrefixes( self ) :

		self.assertTypeNamesArePrefixed( GafferArnold )
		self.assertTypeNamesArePrefixed( GafferArnoldTest )

	def testDefaultNames( self ) :

		self.assertDefaultNamesAreCorrect( GafferArnold )
		self.assertDefaultNamesAreCorrect( GafferArnoldTest )

	def testNodesConstructWithDefaultValues( self ) :

		self.assertNodesConstructWithDefaultValues( GafferArnold )
		self.assertNodesConstructWithDefaultValues( GafferArnoldTest )

	def testDirectoryCreation( self ) :

		s = Gaffer.ScriptNode()
		s["variables"].addChild( Gaffer.NameValuePlug( "renderDirectory", self.temporaryDirectory() + "/renderTests" ) )
		s["variables"].addChild( Gaffer.NameValuePlug( "assDirectory", self.temporaryDirectory() + "/assTests" ) )

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

		s["render"] = GafferArnold.ArnoldRender()
		s["render"]["in"].setInput( s["outputs"]["out"] )
		s["render"]["fileName"].setValue( "$assDirectory/test.####.ass" )
		s["render"]["mode"].setValue( s["render"].Mode.SceneDescriptionMode )

		self.assertFalse( os.path.exists( self.temporaryDirectory() + "/renderTests" ) )
		self.assertFalse( os.path.exists( self.temporaryDirectory() + "/assTests" ) )
		self.assertFalse( os.path.exists( self.temporaryDirectory() + "/assTests/test.0001.ass" ) )

		s["fileName"].setValue( self.temporaryDirectory() + "/test.gfr" )

		with s.context() :
			s["render"]["task"].execute()

		self.assertTrue( os.path.exists( self.temporaryDirectory() + "/renderTests" ) )
		self.assertTrue( os.path.exists( self.temporaryDirectory() + "/assTests" ) )
		self.assertTrue( os.path.exists( self.temporaryDirectory() + "/assTests/test.0001.ass" ) )

		# check it can cope with everything already existing

		with s.context() :
			s["render"]["task"].execute()

		self.assertTrue( os.path.exists( self.temporaryDirectory() + "/renderTests" ) )
		self.assertTrue( os.path.exists( self.temporaryDirectory() + "/assTests" ) )
		self.assertTrue( os.path.exists( self.temporaryDirectory() + "/assTests/test.0001.ass" ) )

	def testWedge( self ) :

		s = Gaffer.ScriptNode()

		s["sphere"] = GafferScene.Sphere()
		s["sphere"]["sets"].setValue( "${wedge:value}" )

		s["filter"] = GafferScene.SetFilter()
		s["filter"]["setExpression"].setValue( "hidden" )

		s["attributes"] = GafferScene.StandardAttributes()
		s["attributes"]["attributes"]["visibility"]["enabled"].setValue( True )
		s["attributes"]["attributes"]["visibility"]["value"].setValue( False )
		s["attributes"]["filter"].setInput( s["filter"]["out"] )
		s["attributes"]["in"].setInput( s["sphere"]["out"] )

		s["outputs"] = GafferScene.Outputs()
		s["outputs"].addOutput(
			"beauty",
			IECoreScene.Output(
				self.temporaryDirectory() + "/${wedge:value}.tif",
				"tiff",
				"rgba",
				{
				}
			)
		)
		s["outputs"]["in"].setInput( s["attributes"]["out"] )

		s["render"] = GafferArnold.ArnoldRender()
		s["render"]["fileName"].setValue( self.temporaryDirectory() + "/test.####.ass" )
		s["render"]["in"].setInput( s["outputs"]["out"] )

		s["wedge"] = Gaffer.Wedge()
		s["wedge"]["mode"].setValue( int( s["wedge"].Mode.StringList ) )
		s["wedge"]["strings"].setValue( IECore.StringVectorData( [ "visible", "hidden" ] ) )
		s["wedge"]["preTasks"][0].setInput( s["render"]["task"] )

		s["fileName"].setValue( self.temporaryDirectory() + "/test.gfr" )
		s.save()

		dispatcher = GafferDispatch.LocalDispatcher()
		dispatcher["jobsDirectory"].setValue( self.temporaryDirectory() + "/testJobDirectory" )
		dispatcher["framesMode"].setValue( GafferDispatch.Dispatcher.FramesMode.CurrentFrame )
		dispatcher["executeInBackground"].setValue( False )

		dispatcher.dispatch( [ s["wedge"] ] )

		hidden = GafferImage.ImageReader()
		hidden["fileName"].setValue( self.temporaryDirectory() + "/hidden.tif" )

		visible = GafferImage.ImageReader()
		visible["fileName"].setValue( self.temporaryDirectory() + "/visible.tif" )

		hiddenStats = GafferImage.ImageStats()
		hiddenStats["in"].setInput( hidden["out"] )
		hiddenStats["area"].setValue( hiddenStats["in"]["dataWindow"].getValue() )

		visibleStats = GafferImage.ImageStats()
		visibleStats["in"].setInput( visible["out"] )
		visibleStats["area"].setValue( visibleStats["in"]["dataWindow"].getValue() )

		self.assertLess( hiddenStats["average"].getValue()[0], 0.05 )
		self.assertGreater( visibleStats["average"].getValue()[0], .27 )

	@staticmethod
	def __m44f( m ) :

		return imath.M44f( *[ i for row in m.data for i in row ] )

	def testTransformMotion( self ) :

		s = Gaffer.ScriptNode()

		s["plane"] = GafferScene.Plane()
		s["sphere"] = GafferScene.Sphere()
		s["group"] = GafferScene.Group()
		s["group"]["in"][0].setInput( s["plane"]["out"] )
		s["group"]["in"][1].setInput( s["sphere"]["out"] )

		s["expression"] = Gaffer.Expression()
		s["expression"].setExpression(
			inspect.cleandoc(
				"""
				parent["plane"]["transform"]["translate"]["x"] = context.getFrame()
				parent["sphere"]["transform"]["translate"]["y"] = context.getFrame() * 2
				parent["group"]["transform"]["translate"]["z"] = context.getFrame() - 1
				"""
			)
		)

		s["planeFilter"] = GafferScene.PathFilter()
		s["planeFilter"]["paths"].setValue( IECore.StringVectorData( [ "/group/plane" ] ) )

		s["attributes"] = GafferScene.StandardAttributes()
		s["attributes"]["in"].setInput( s["group"]["out"] )
		s["attributes"]["filter"].setInput( s["planeFilter"]["out"] )
		s["attributes"]["attributes"]["transformBlur"]["enabled"].setValue( True )
		s["attributes"]["attributes"]["transformBlur"]["value"].setValue( False )

		s["options"] = GafferScene.StandardOptions()
		s["options"]["in"].setInput( s["attributes"]["out"] )
		s["options"]["options"]["shutter"]["enabled"].setValue( True )
		s["options"]["options"]["transformBlur"]["enabled"].setValue( True )

		s["render"] = GafferArnold.ArnoldRender()
		s["render"]["in"].setInput( s["options"]["out"] )
		s["render"]["mode"].setValue( s["render"].Mode.SceneDescriptionMode )
		s["render"]["fileName"].setValue( self.temporaryDirectory() + "/test.ass" )

		# No motion blur

		s["options"]["options"]["transformBlur"]["value"].setValue( False )
		s["render"]["task"].execute()

		with IECoreArnold.UniverseBlock( writable = True ) :

			arnold.AiASSLoad( self.temporaryDirectory() + "/test.ass" )

			camera = arnold.AiNodeLookUpByName( "gaffer:defaultCamera" )
			sphere = arnold.AiNodeLookUpByName( "/group/sphere" )
			sphereMotionStart = arnold.AiNodeGetFlt( sphere, "motion_start" )
			sphereMotionEnd = arnold.AiNodeGetFlt( sphere, "motion_end" )
			sphereMatrix = arnold.AiNodeGetMatrix( sphere, "matrix" )

			plane = arnold.AiNodeLookUpByName( "/group/plane" )
			planeMotionStart = arnold.AiNodeGetFlt( plane, "motion_start" )
			planeMotionEnd = arnold.AiNodeGetFlt( plane, "motion_end" )
			planeMatrix = arnold.AiNodeGetMatrix( plane, "matrix" )

			# Motion parameters should be left at default
			self.assertEqual( sphereMotionStart, 0 )
			self.assertEqual( sphereMotionEnd, 1 )
			self.assertEqual( planeMotionStart, 0 )
			self.assertEqual( planeMotionEnd, 1 )

			expectedSphereMatrix = arnold.AiM4Translation( arnold.AtVector( 0, 2, 0 ) )

			expectedPlaneMatrix = arnold.AiM4Translation( arnold.AtVector( 1, 0, 0 ) )

			self.assertEqual( self.__m44f( sphereMatrix ), self.__m44f( expectedSphereMatrix ) )
			self.assertEqual( self.__m44f( planeMatrix ), self.__m44f( expectedPlaneMatrix ) )

			self.assertEqual( arnold.AiNodeGetFlt( camera, "shutter_start" ), 1 )
			self.assertEqual( arnold.AiNodeGetFlt( camera, "shutter_end" ), 1 )

		# Motion blur

		s["options"]["options"]["transformBlur"]["value"].setValue( True )
		s["render"]["task"].execute()

		with IECoreArnold.UniverseBlock( writable = True ) :

			arnold.AiASSLoad( self.temporaryDirectory() + "/test.ass" )

			camera = arnold.AiNodeLookUpByName( "gaffer:defaultCamera" )
			sphere = arnold.AiNodeLookUpByName( "/group/sphere" )
			sphereMotionStart = arnold.AiNodeGetFlt( sphere, "motion_start" )
			sphereMotionEnd = arnold.AiNodeGetFlt( sphere, "motion_end" )
			sphereMatrices = arnold.AiNodeGetArray( sphere, "matrix" )

			plane = arnold.AiNodeLookUpByName( "/group/plane" )
			planeMotionStart = arnold.AiNodeGetFlt( plane, "motion_start" )
			planeMotionEnd = arnold.AiNodeGetFlt( plane, "motion_end" )
			planeMatrices = arnold.AiNodeGetArray( plane, "matrix" )

			self.assertEqual( sphereMotionStart, 0.75 )
			self.assertEqual( sphereMotionEnd, 1.25 )
			self.assertEqual( arnold.AiArrayGetNumElements( sphereMatrices.contents ), 1 )
			self.assertEqual( arnold.AiArrayGetNumKeys( sphereMatrices.contents ), 2 )

			self.assertEqual( planeMotionStart, 0.75 )
			self.assertEqual( planeMotionEnd, 1.25 )
			self.assertEqual( arnold.AiArrayGetNumElements( planeMatrices.contents ), 1 )
			self.assertEqual( arnold.AiArrayGetNumKeys( planeMatrices.contents ), 2 )

			for i in range( 0, 2 ) :

				frame = 0.75 + 0.5 * i
				sphereMatrix = arnold.AiArrayGetMtx( sphereMatrices, i )

				expectedSphereMatrix = arnold.AiM4Translation( arnold.AtVector( 0, frame * 2, frame - 1 ) )

				planeMatrix = arnold.AiArrayGetMtx( planeMatrices, i )

				expectedPlaneMatrix = arnold.AiM4Translation( arnold.AtVector( 1, 0, frame - 1 ) )

				self.assertEqual( self.__m44f( sphereMatrix ), self.__m44f( expectedSphereMatrix ) )
				self.assertEqual( self.__m44f( planeMatrix ), self.__m44f( expectedPlaneMatrix ) )

			self.assertEqual( arnold.AiNodeGetFlt( camera, "shutter_start" ), 0.75 )
			self.assertEqual( arnold.AiNodeGetFlt( camera, "shutter_end" ), 1.25 )

		# Motion blur on, but sampleMotion off

		s["options"]["options"]["sampleMotion"]["enabled"].setValue( True )
		s["options"]["options"]["sampleMotion"]["value"].setValue( False )
		s["render"]["task"].execute()

		with IECoreArnold.UniverseBlock( writable = True ) :

			arnold.AiASSLoad( self.temporaryDirectory() + "/test.ass" )

			camera = arnold.AiNodeLookUpByName( "gaffer:defaultCamera" )
			sphere = arnold.AiNodeLookUpByName( "/group/sphere" )
			sphereMotionStart = arnold.AiNodeGetFlt( sphere, "motion_start" )
			sphereMotionEnd = arnold.AiNodeGetFlt( sphere, "motion_end" )
			sphereMatrices = arnold.AiNodeGetArray( sphere, "matrix" )

			plane = arnold.AiNodeLookUpByName( "/group/plane" )
			planeMotionStart = arnold.AiNodeGetFlt( plane, "motion_start" )
			planeMotionEnd = arnold.AiNodeGetFlt( plane, "motion_end" )
			planeMatrices = arnold.AiNodeGetArray( plane, "matrix" )

			self.assertEqual( sphereMotionStart, 0.75 )
			self.assertEqual( sphereMotionEnd, 1.25 )
			self.assertEqual( arnold.AiArrayGetNumElements( sphereMatrices.contents ), 1 )
			self.assertEqual( arnold.AiArrayGetNumKeys( sphereMatrices.contents ), 2 )

			self.assertEqual( planeMotionStart, 0.75 )
			self.assertEqual( planeMotionEnd, 1.25 )
			self.assertEqual( arnold.AiArrayGetNumElements( planeMatrices.contents ), 1 )
			self.assertEqual( arnold.AiArrayGetNumKeys( planeMatrices.contents ), 2 )

			for i in range( 0, 2 ) :

				frame = 0.75 + 0.5 * i

				sphereMatrix = arnold.AiArrayGetMtx( sphereMatrices, i )

				expectedSphereMatrix = arnold.AiM4Translation( arnold.AtVector( 0, frame * 2, frame - 1 ) )

				planeMatrix = arnold.AiArrayGetMtx( planeMatrices, i )

				expectedPlaneMatrix = arnold.AiM4Translation( arnold.AtVector( 1, 0, frame - 1 ) )

				self.assertEqual( self.__m44f( sphereMatrix ), self.__m44f( expectedSphereMatrix ) )
				self.assertEqual( self.__m44f( planeMatrix ), self.__m44f( expectedPlaneMatrix ) )

			self.assertEqual( arnold.AiNodeGetFlt( camera, "shutter_start" ), 0.75 )
			self.assertEqual( arnold.AiNodeGetFlt( camera, "shutter_end" ), 0.75 )

	def testResolution( self ) :

		s = Gaffer.ScriptNode()

		s["camera"] = GafferScene.Camera()

		s["options"] = GafferScene.StandardOptions()
		s["options"]["in"].setInput( s["camera"]["out"] )
		s["options"]["options"]["renderResolution"]["enabled"].setValue( True )
		s["options"]["options"]["renderResolution"]["value"].setValue( imath.V2i( 200, 100 ) )
		s["options"]["options"]["resolutionMultiplier"]["enabled"].setValue( True )
		s["options"]["options"]["resolutionMultiplier"]["value"].setValue( 2 )

		s["render"] = GafferArnold.ArnoldRender()
		s["render"]["in"].setInput( s["options"]["out"] )
		s["render"]["mode"].setValue( s["render"].Mode.SceneDescriptionMode )
		s["render"]["fileName"].setValue( self.temporaryDirectory() + "/test.ass" )

		# Default camera should have the right resolution.

		s["render"]["task"].execute()

		with IECoreArnold.UniverseBlock( writable = True ) :

			arnold.AiASSLoad( self.temporaryDirectory() + "/test.ass" )
			options = arnold.AiUniverseGetOptions()
			self.assertEqual( arnold.AiNodeGetInt( options, "xres" ), 400 )
			self.assertEqual( arnold.AiNodeGetInt( options, "yres" ), 200 )

		# As should a camera picked from the scene.

		s["options"]["options"]["renderCamera"]["enabled"].setValue( True )
		s["options"]["options"]["renderCamera"]["value"].setValue( "/camera" )
		s["render"]["task"].execute()

		with IECoreArnold.UniverseBlock( writable = True ) :

			arnold.AiASSLoad( self.temporaryDirectory() + "/test.ass" )
			options = arnold.AiUniverseGetOptions()
			self.assertEqual( arnold.AiNodeGetInt( options, "xres" ), 400 )
			self.assertEqual( arnold.AiNodeGetInt( options, "yres" ), 200 )

	def testRenderRegion( self ) :

		s = Gaffer.ScriptNode()

		s["camera"] = GafferScene.Camera()

		s["options"] = GafferScene.StandardOptions()
		s["options"]["in"].setInput( s["camera"]["out"] )
		s["options"]["options"]["renderCamera"]["enabled"].setValue( True )
		s["options"]["options"]["renderCamera"]["value"].setValue( "/camera" )

		s["render"] = GafferArnold.ArnoldRender()
		s["render"]["in"].setInput( s["options"]["out"] )
		s["render"]["mode"].setValue( s["render"].Mode.SceneDescriptionMode )
		s["render"]["fileName"].setValue( self.temporaryDirectory() + "/test.ass" )

		# Default region
		s["render"]["task"].execute()

		with IECoreArnold.UniverseBlock( writable = True ) :

			arnold.AiASSLoad( self.temporaryDirectory() + "/test.ass" )
			options = arnold.AiUniverseGetOptions()
			self.assertEqual( arnold.AiNodeGetInt( options, "xres" ), 640 )
			self.assertEqual( arnold.AiNodeGetInt( options, "yres" ), 480 )
			self.assertEqual( arnold.AiNodeGetInt( options, "region_min_x" ), 0 )
			self.assertEqual( arnold.AiNodeGetInt( options, "region_max_x" ), 639 )
			self.assertEqual( arnold.AiNodeGetInt( options, "region_min_y" ), 0 )
			self.assertEqual( arnold.AiNodeGetInt( options, "region_max_y" ), 479 )

		# Apply Crop Window
		s["options"]["options"]["renderCropWindow"]["enabled"].setValue( True )
		s["options"]["options"]["renderCropWindow"]["value"].setValue( imath.Box2f( imath.V2f( 0.25, 0.5 ), imath.V2f( 0.75, 1.0 ) ) )

		s["render"]["task"].execute()

		with IECoreArnold.UniverseBlock( writable = True ) :

			arnold.AiASSLoad( self.temporaryDirectory() + "/test.ass" )
			options = arnold.AiUniverseGetOptions()
			self.assertEqual( arnold.AiNodeGetInt( options, "xres" ), 640 )
			self.assertEqual( arnold.AiNodeGetInt( options, "yres" ), 480 )
			self.assertEqual( arnold.AiNodeGetInt( options, "region_min_x" ), 160 )
			self.assertEqual( arnold.AiNodeGetInt( options, "region_max_x" ), 479 )
			self.assertEqual( arnold.AiNodeGetInt( options, "region_min_y" ), 240 )
			self.assertEqual( arnold.AiNodeGetInt( options, "region_max_y" ), 479 )

		# Test Empty Crop Window
		s["options"]["options"]["renderCropWindow"]["value"].setValue( imath.Box2f() )

		s["render"]["task"].execute()

		with IECoreArnold.UniverseBlock( writable = True ) :

			arnold.AiASSLoad( self.temporaryDirectory() + "/test.ass" )
			options = arnold.AiUniverseGetOptions()
			self.assertEqual( arnold.AiNodeGetInt( options, "xres" ), 640 )
			self.assertEqual( arnold.AiNodeGetInt( options, "yres" ), 480 )

			# Since Arnold doesn't support empty regions, we default to one pixel in the corner
			self.assertEqual( arnold.AiNodeGetInt( options, "region_min_x" ), 0 )
			self.assertEqual( arnold.AiNodeGetInt( options, "region_max_x" ), 0 )
			self.assertEqual( arnold.AiNodeGetInt( options, "region_min_y" ), 479 )
			self.assertEqual( arnold.AiNodeGetInt( options, "region_max_y" ), 479 )

		# Apply Overscan
		s["options"]["options"]["renderCropWindow"]["enabled"].setValue( False )
		s["options"]["options"]["overscan"]["enabled"].setValue( True )
		s["options"]["options"]["overscan"]["value"].setValue( True )
		s["options"]["options"]["overscanTop"]["enabled"].setValue( True )
		s["options"]["options"]["overscanTop"]["value"].setValue( 0.1 )
		s["options"]["options"]["overscanBottom"]["enabled"].setValue( True )
		s["options"]["options"]["overscanBottom"]["value"].setValue( 0.2 )
		s["options"]["options"]["overscanLeft"]["enabled"].setValue( True )
		s["options"]["options"]["overscanLeft"]["value"].setValue( 0.3 )
		s["options"]["options"]["overscanRight"]["enabled"].setValue( True )
		s["options"]["options"]["overscanRight"]["value"].setValue( 0.4 )

		s["render"]["task"].execute()

		with IECoreArnold.UniverseBlock( writable = True ) :

			arnold.AiASSLoad( self.temporaryDirectory() + "/test.ass" )
			options = arnold.AiUniverseGetOptions()
			self.assertEqual( arnold.AiNodeGetInt( options, "xres" ), 640 )
			self.assertEqual( arnold.AiNodeGetInt( options, "yres" ), 480 )
			self.assertEqual( arnold.AiNodeGetInt( options, "region_min_x" ), -192 )
			self.assertEqual( arnold.AiNodeGetInt( options, "region_max_x" ), 640 + 255 )
			self.assertEqual( arnold.AiNodeGetInt( options, "region_min_y" ), -48 )
			self.assertEqual( arnold.AiNodeGetInt( options, "region_max_y" ), 480 + 95 )

	def testMissingCameraRaises( self ) :

		s = Gaffer.ScriptNode()

		s["options"] = GafferScene.StandardOptions()
		s["options"]["options"]["renderCamera"]["enabled"].setValue( True )
		s["options"]["options"]["renderCamera"]["value"].setValue( "/i/dont/exist" )

		s["render"] = GafferArnold.ArnoldRender()
		s["render"]["in"].setInput( s["options"]["out"] )
		s["render"]["mode"].setValue( s["render"].Mode.SceneDescriptionMode )
		s["render"]["fileName"].setValue( self.temporaryDirectory() + "/test.ass" )

		# The requested camera doesn't exist - this should raise an exception.

		self.assertRaisesRegexp( RuntimeError, "/i/dont/exist", s["render"]["task"].execute )

		# And even the existence of a different camera shouldn't change that.

		s["camera"] = GafferScene.Camera()
		s["options"]["in"].setInput( s["camera"]["out"] )

		self.assertRaisesRegexp( RuntimeError, "/i/dont/exist", s["render"]["task"].execute )

	def testManyCameras( self ) :

		camera = GafferScene.Camera()

		duplicate = GafferScene.Duplicate()
		duplicate["in"].setInput( camera["out"] )
		duplicate["target"].setValue( "/camera" )
		duplicate["copies"].setValue( 1000 )

		render = GafferArnold.ArnoldRender()
		render["in"].setInput( duplicate["out"] )
		render["mode"].setValue( render.Mode.SceneDescriptionMode )
		render["fileName"].setValue( self.temporaryDirectory() + "/test.ass" )

		render["task"].execute()

	def testTwoRenders( self ) :

		sphere = GafferScene.Sphere()

		duplicate = GafferScene.Duplicate()
		duplicate["in"].setInput( sphere["out"] )
		duplicate["target"].setValue( "/sphere" )
		duplicate["copies"].setValue( 10000 )

		render = GafferArnold.ArnoldRender()
		render["in"].setInput( duplicate["out"] )
		render["mode"].setValue( render.Mode.SceneDescriptionMode )
		render["fileName"].setValue( self.temporaryDirectory() + "/test.####.ass" )

		errors = []
		def executeFrame( frame ) :

			with Gaffer.Context() as c :
				c.setFrame( frame )
				try :
					render["task"].execute()
				except Exception as e :
					errors.append( str( e ) )

		threads = []
		for i in range( 0, 2 ) :
			t = threading.Thread( target = executeFrame, args = ( i, ) )
			t.start()
			threads.append( t )

		for t in threads :
			t.join()

		self.assertEqual( len( errors ), 1 )
		self.assertTrue( "Arnold is already in use" in errors[0] )

	def testTraceSets( self ) :

		sphere = GafferScene.Sphere()
		group = GafferScene.Group()
		group["in"][0].setInput( sphere["out"] )
		group["in"][1].setInput( sphere["out"] )

		set1 = GafferScene.Set()
		set1["name"].setValue( "render:firstSphere" )
		set1["paths"].setValue( IECore.StringVectorData( [ "/group/sphere" ] ) )
		set1["in"].setInput( group["out"] )

		set2 = GafferScene.Set()
		set2["name"].setValue( "render:secondSphere" )
		set2["paths"].setValue( IECore.StringVectorData( [ "/group/sphere1" ] ) )
		set2["in"].setInput( set1["out"] )

		set3 = GafferScene.Set()
		set3["name"].setValue( "render:group" )
		set3["paths"].setValue( IECore.StringVectorData( [ "/group" ] ) )
		set3["in"].setInput( set2["out"] )

		set4 = GafferScene.Set()
		set4["name"].setValue( "render:bothSpheres" )
		set4["paths"].setValue( IECore.StringVectorData( [ "/group/sphere", "/group/sphere1" ] ) )
		set4["in"].setInput( set3["out"] )

		render = GafferArnold.ArnoldRender()
		render["in"].setInput( set4["out"] )
		render["mode"].setValue( render.Mode.SceneDescriptionMode )
		render["fileName"].setValue( self.temporaryDirectory() + "/test.ass" )

		render["task"].execute()

		with IECoreArnold.UniverseBlock( writable = True ) :

			arnold.AiASSLoad( self.temporaryDirectory() + "/test.ass" )

			firstSphere = arnold.AiNodeLookUpByName( "/group/sphere" )
			secondSphere = arnold.AiNodeLookUpByName( "/group/sphere1" )

			self.assertEqual( self.__arrayToSet( arnold.AiNodeGetArray( firstSphere, "trace_sets" ) ), { "firstSphere", "group", "bothSpheres" } )
			self.assertEqual( self.__arrayToSet( arnold.AiNodeGetArray( secondSphere, "trace_sets" ) ), { "secondSphere", "group", "bothSpheres" } )

	def testSetsNeedContextEntry( self ) :

		script = Gaffer.ScriptNode()

		script["light"] = GafferArnold.ArnoldLight()
		script["light"].loadShader( "point_light" )

		script["expression"] = Gaffer.Expression()
		script["expression"].setExpression(
			"""parent["light"]["name"] = context["lightName"]"""
		)

		script["render"] = GafferArnold.ArnoldRender()
		script["render"]["in"].setInput( script["light"]["out"] )
		script["render"]["mode"].setValue( script["render"].Mode.SceneDescriptionMode )
		script["render"]["fileName"].setValue( self.temporaryDirectory() + "/test.ass" )

		for i in range( 0, 100 ) :

			with Gaffer.Context() as context :
				context["lightName"] = "light%d" % i
				script["render"]["task"].execute()

	def testFrameAndAASeed( self ) :

		options = GafferArnold.ArnoldOptions()

		render = GafferArnold.ArnoldRender()
		render["in"].setInput( options["out"] )
		render["mode"].setValue( render.Mode.SceneDescriptionMode )
		render["fileName"].setValue( self.temporaryDirectory() + "/test.ass" )

		for frame in ( 1, 2, 2.8, 3.2 ) :
			for seed in ( None, 3, 4 ) :
				with Gaffer.Context() as c :

					c.setFrame( frame )

					options["options"]["aaSeed"]["enabled"].setValue( seed is not None )
					options["options"]["aaSeed"]["value"].setValue( seed or 1 )

					render["task"].execute()

					with IECoreArnold.UniverseBlock( writable = True ) :

						arnold.AiASSLoad( self.temporaryDirectory() + "/test.ass" )

						self.assertEqual(
							arnold.AiNodeGetInt( arnold.AiUniverseGetOptions(), "AA_seed" ),
							seed or round( frame )
						)

	def testRendererContextVariable( self ) :

		sphere = GafferScene.Sphere()
		sphere["name"].setValue( "sphere${scene:renderer}" )

		render = GafferArnold.ArnoldRender()
		render["in"].setInput( sphere["out"] )
		render["mode"].setValue( render.Mode.SceneDescriptionMode )
		render["fileName"].setValue( self.temporaryDirectory() + "/test.ass" )

		render["task"].execute()

		with IECoreArnold.UniverseBlock( writable = True ) :

			arnold.AiASSLoad( self.temporaryDirectory() + "/test.ass" )
			self.assertTrue( arnold.AiNodeLookUpByName( "/sphereArnold" ) is not None )

	def testAdaptors( self ) :

		sphere = GafferScene.Sphere()

		def a() :

			result = GafferArnold.ArnoldAttributes()
			result["attributes"]["matte"]["enabled"].setValue( True )
			result["attributes"]["matte"]["value"].setValue( True )

			return result

		GafferScene.registerAdaptor( "Test", a )

		sphere = GafferScene.Sphere()

		render = GafferArnold.ArnoldRender()
		render["in"].setInput( sphere["out"] )
		render["mode"].setValue( render.Mode.SceneDescriptionMode )
		render["fileName"].setValue( self.temporaryDirectory() + "/test.ass" )

		render["task"].execute()

		with IECoreArnold.UniverseBlock( writable = True ) :

			arnold.AiASSLoad( self.temporaryDirectory() + "/test.ass" )
			node = arnold.AiNodeLookUpByName( "/sphere" )

			self.assertEqual( arnold.AiNodeGetBool( node, "matte" ), True )

	def testLightAndShadowLinking( self ) :

		sphere1 = GafferScene.Sphere()
		sphere2 = GafferScene.Sphere()

		attributes = GafferScene.StandardAttributes()
		arnoldAttributes = GafferArnold.ArnoldAttributes()

		light1 = GafferArnold.ArnoldLight()
		light1.loadShader( "point_light" )

		light2 = GafferArnold.ArnoldLight()
		light2.loadShader( "point_light" )

		group = GafferScene.Group()
		group["in"].addChild( GafferScene.ScenePlug( "in1" ) )
		group["in"].addChild( GafferScene.ScenePlug( "in2" ) )
		group["in"].addChild( GafferScene.ScenePlug( "in3" ) )
		group["in"].addChild( GafferScene.ScenePlug( "in4" ) )

		evaluate = GafferScene.EvaluateLightLinks()

		render = GafferArnold.ArnoldRender()

		attributes["in"].setInput( sphere1["out"] )
		arnoldAttributes["in"].setInput( attributes["out"] )
		group["in"]["in1"].setInput( arnoldAttributes["out"] )
		group["in"]["in2"].setInput( light1["out"] )
		group["in"]["in3"].setInput( light2["out"] )
		group["in"]["in4"].setInput( sphere2["out"] )
		evaluate["in"].setInput( group["out"] )
		render["in"].setInput( evaluate["out"] )

		# Illumination
		attributes["attributes"]["linkedLights"]["enabled"].setValue( True )
		attributes["attributes"]["linkedLights"]["value"].setValue( "/group/light /group/light1" )

		# Shadows
		arnoldAttributes["attributes"]["shadowGroup"]["enabled"].setValue( True )
		arnoldAttributes["attributes"]["shadowGroup"]["value"].setValue( "/group/light /group/light1" )

		# make sure we pass correct data into the renderer
		self.assertEqual(
			set( render["in"].attributes( "/group/sphere" )["linkedLights"] ),
			set( IECore.StringVectorData( ["/group/light", "/group/light1"] ) )
		)

		self.assertEqual(
			set( render["in"].attributes( "/group/sphere" )["ai:visibility:shadow_group"] ),
			set( IECore.StringVectorData( ["/group/light", "/group/light1"] ) )
		)

		render["mode"].setValue( render.Mode.SceneDescriptionMode )
		render["fileName"].setValue( self.temporaryDirectory() + "/test.ass" )
		render["task"].execute()

		with IECoreArnold.UniverseBlock( writable = True ) :

			arnold.AiASSLoad( self.temporaryDirectory() + "/test.ass" )

			# the first sphere had linked lights
			sphere = arnold.AiNodeLookUpByName( "/group/sphere" )

			# check illumination
			lights = arnold.AiNodeGetArray( sphere, "light_group" )
			lightNames = []
			for i in range( arnold.AiArrayGetNumElements( lights.contents ) ):
				light = arnold.cast(arnold.AiArrayGetPtr(lights, i), arnold.POINTER(arnold.AtNode))
				lightNames.append( arnold.AiNodeGetName(light.contents)  )

			doLinking = arnold.AiNodeGetBool( sphere, "use_light_group" )

			self.assertEqual( set( lightNames ), { "light:/group/light", "light:/group/light1" } )
			self.assertEqual( doLinking, True )

			# check shadows
			shadows = arnold.AiNodeGetArray( sphere, "shadow_group" )
			lightNames = []
			for i in range( arnold.AiArrayGetNumElements( shadows.contents ) ):
				light = arnold.cast(arnold.AiArrayGetPtr(shadows, i), arnold.POINTER(arnold.AtNode))
				lightNames.append( arnold.AiNodeGetName(light.contents)  )

			doLinking = arnold.AiNodeGetBool( sphere, "use_shadow_group" )

			self.assertEqual( set( lightNames ), { "light:/group/light", "light:/group/light1" } )
			self.assertEqual( doLinking, True )

			# the second sphere does not have any light linking enabled
			sphere1 = arnold.AiNodeLookUpByName( "/group/sphere1" )

			# check illumination
			lights = arnold.AiNodeGetArray( sphere1, "light_group" )
			lightNames = []
			for i in range( arnold.AiArrayGetNumElements( lights.contents ) ):
				light = arnold.cast(arnold.AiArrayGetPtr(lights, i), arnold.POINTER(arnold.AtNode))
				lightNames.append( arnold.AiNodeGetName(light.contents)  )

			doLinking = arnold.AiNodeGetBool( sphere1, "use_light_group" )

			self.assertEqual( lightNames, [] )
			self.assertEqual( doLinking, False )

			# check shadows
			shadows = arnold.AiNodeGetArray( sphere1, "shadow_group" )
			lightNames = []
			for i in range( arnold.AiArrayGetNumElements( shadows.contents ) ):
				light = arnold.cast(arnold.AiArrayGetPtr(shadows, i), arnold.POINTER(arnold.AtNode))
				lightNames.append( arnold.AiNodeGetName(light.contents)  )

			doLinking = arnold.AiNodeGetBool( sphere1, "use_shadow_group" )

			self.assertEqual( lightNames, [] )
			self.assertEqual( doLinking, False )

	def testNoLinkedLightsOnLights( self ) :

		sphere = GafferScene.Sphere()

		meshLightShader = GafferArnold.ArnoldShader()
		meshLightShader.loadShader( "flat" )

		meshLightFilter = GafferScene.PathFilter()
		meshLightFilter["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )

		meshLight = GafferArnold.ArnoldMeshLight()
		meshLight["in"].setInput( sphere["out"] )
		meshLight["filter"].setInput( meshLightFilter["out"] )
		meshLight["parameters"]["color"].setInput( meshLightShader["out"] )

		light1 = GafferArnold.ArnoldLight()
		light1.loadShader( "point_light" )

		light2 = GafferArnold.ArnoldLight()
		light2.loadShader( "point_light" )

		# Trigger light linking by unlinking a light
		light2["defaultLight"].setValue( False )

		group = GafferScene.Group()

		group["in"][0].setInput( meshLight["out"] )
		group["in"][1].setInput( light1["out"] )
		group["in"][2].setInput( light2["out"] )

		render = GafferArnold.ArnoldRender()
		render["in"].setInput( group["out"] )

		render["mode"].setValue( render.Mode.SceneDescriptionMode )
		render["fileName"].setValue( self.temporaryDirectory() + "/test.ass" )
		render["task"].execute()

		with IECoreArnold.UniverseBlock( writable = True ) :

			arnold.AiASSLoad( self.temporaryDirectory() + "/test.ass" )

			sphere = arnold.AiNodeLookUpByName( "/group/sphere" )
			self.assertIsNotNone( sphere )

			self.assertEqual( arnold.AiArrayGetNumElements( arnold.AiNodeGetArray( sphere, "light_group" ) ), 0 )
			self.assertFalse( arnold.AiNodeGetBool( sphere, "use_light_group" ) )

	def testAbortRaises( self ) :

		s = Gaffer.ScriptNode()

		s["plane"] = GafferScene.Plane()
		s["plane"]["transform"]["translate"]["z"].setValue( -10 )

		s["shader"] = GafferArnold.ArnoldShader()
		s["shader"].loadShader( "image" )
		# Missing texture should cause render to abort
		s["shader"]["parameters"]["filename"].setValue( "iDontExist" )

		s["filter"] = GafferScene.PathFilter()
		s["filter"]["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		s["shaderAssignment"] = GafferScene.ShaderAssignment()
		s["shaderAssignment"]["in"].setInput( s["plane"]["out"] )
		s["shaderAssignment"]["filter"].setInput( s["filter"]["out"] )
		s["shaderAssignment"]["shader"].setInput( s["shader"]["out"] )

		s["outputs"] = GafferScene.Outputs()
		s["outputs"].addOutput(
			"beauty",
			IECoreScene.Output(
				self.temporaryDirectory() + "/test.tif",
				"tiff",
				"rgba",
				{}
			)
		)
		s["outputs"]["in"].setInput( s["shaderAssignment"]["out"] )

		s["render"] = GafferArnold.ArnoldRender()
		s["render"]["in"].setInput( s["outputs"]["out"] )

		self.assertRaisesRegexp( RuntimeError, "Render aborted", s["render"]["task"].execute )

	def testOSLShaders( self ) :

		swizzle = GafferOSL.OSLShader()
		swizzle.loadShader( "MaterialX/mx_swizzle_color_float" )
		swizzle["parameters"]["in"].setValue( imath.Color3f( 0, 0, 1 ) )
		swizzle["parameters"]["channels"].setValue( "b" )

		pack = GafferOSL.OSLShader()
		pack.loadShader( "MaterialX/mx_pack_color" )
		pack["parameters"]["in1"].setInput( swizzle["out"]["out"] )

		ball = GafferArnold.ArnoldShaderBall()
		ball["shader"].setInput( pack["out"] )

		outputs = GafferScene.Outputs()
		outputs.addOutput(
			"beauty",
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
		outputs["in"].setInput( ball["out"] )

		render = GafferArnold.ArnoldRender()
		render["in"].setInput( outputs["out"] )
		render["task"].execute()

		image = IECoreImage.ImageDisplayDriver.storedImage( "myLovelySphere" )
		self.assertTrue( isinstance( image, IECoreImage.ImagePrimitive ) )
		self.assertEqual( self.__color4fAtUV( image, imath.V2f( 0.5 ) ), imath.Color4f( 1, 0, 0, 1 ) )

	def __color4fAtUV( self, image, uv ) :

		objectToImage = GafferImage.ObjectToImage()
		objectToImage["object"].setValue( image )

		sampler = GafferImage.ImageSampler()
		sampler["image"].setInput( objectToImage["out"] )
		sampler["pixel"].setValue(
			uv * imath.V2f(
				image.displayWindow.size().x,
				image.displayWindow.size().y
			)
		)

		return sampler["color"].getValue()

	def __arrayToSet( self, a ) :

		result = set()
		for i in range( 0,  arnold.AiArrayGetNumElements( a.contents ) ) :
			if arnold.AiArrayGetType( a.contents ) == arnold.AI_TYPE_STRING :
				result.add( arnold.AiArrayGetStr( a, i ) )
			else :
				raise TypeError

		return result

if __name__ == "__main__":
	unittest.main()
