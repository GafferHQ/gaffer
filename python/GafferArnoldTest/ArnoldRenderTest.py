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

import pathlib
import inspect
import unittest
import subprocess
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

		self.__scriptFileName = self.temporaryDirectory() / "test.gfr"

	def tearDown( self ) :

		GafferSceneTest.SceneTestCase.tearDown( self )

		GafferScene.SceneAlgo.deregisterRenderAdaptor( "Test" )

	def testExecute( self ) :

		s = Gaffer.ScriptNode()

		s["plane"] = GafferScene.Plane()
		s["render"] = GafferArnold.ArnoldRender()
		s["render"]["mode"].setValue( s["render"].Mode.SceneDescriptionMode )
		s["render"]["in"].setInput( s["plane"]["out"] )

		s["expression"] = Gaffer.Expression()
		s["expression"].setExpression( f"""parent['render']['fileName'] = '{( self.temporaryDirectory() / "test.%d.ass" ).as_posix()}' % int( context['frame'] )""" )

		s["fileName"].setValue( self.__scriptFileName )
		s.save()

		p = subprocess.Popen(
			f"gaffer execute {self.__scriptFileName} -frames 1-3",
			shell=True,
			stderr = subprocess.PIPE,
		)
		p.wait()
		self.assertFalse( p.returncode )

		for i in range( 1, 4 ) :
			self.assertTrue( ( self.temporaryDirectory() / f"test.{i}.ass" ).exists() )

	def testWaitForImage( self ) :

		s = Gaffer.ScriptNode()

		s["plane"] = GafferScene.Plane()

		s["outputs"] = GafferScene.Outputs()
		s["outputs"].addOutput(
			"beauty",
			IECoreScene.Output(
				str( self.temporaryDirectory() / "test.tif" ),
				"tiff",
				"rgba",
				{}
			)
		)
		s["outputs"]["in"].setInput( s["plane"]["out"] )

		s["render"] = GafferArnold.ArnoldRender()
		s["render"]["in"].setInput( s["outputs"]["out"] )
		s["render"]["task"].execute()

		self.assertTrue( ( self.temporaryDirectory() / "test.tif" ).exists() )

	def testExecuteWithStringSubstitutions( self ) :

		s = Gaffer.ScriptNode()

		s["plane"] = GafferScene.Plane()
		s["render"] = GafferArnold.ArnoldRender()
		s["render"]["mode"].setValue( s["render"].Mode.SceneDescriptionMode )
		s["render"]["in"].setInput( s["plane"]["out"] )
		s["render"]["fileName"].setValue( self.temporaryDirectory() / "test.####.ass" )

		s["fileName"].setValue( self.__scriptFileName )
		s.save()

		p = subprocess.Popen(
			f"gaffer execute {self.__scriptFileName} -frames 1-3",
			shell=True,
			stderr = subprocess.PIPE,
		)
		p.wait()
		self.assertFalse( p.returncode )

		for i in range( 1, 4 ) :
			self.assertTrue( ( self.temporaryDirectory() / f"test.{i:04d}.ass" ).exists() )

	def testImageOutput( self ) :

		s = Gaffer.ScriptNode()

		s["plane"] = GafferScene.Plane()

		s["outputs"] = GafferScene.Outputs()
		s["outputs"].addOutput(
			"beauty",
			IECoreScene.Output(
				str( self.temporaryDirectory() / "test.####.tif" ),
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
			self.assertTrue( ( self.temporaryDirectory() / f"test.{i:04d}.tif" ).exists() )

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
		s["variables"].addChild( Gaffer.NameValuePlug( "renderDirectory", ( self.temporaryDirectory() / "renderTests" ).as_posix() ) )
		s["variables"].addChild( Gaffer.NameValuePlug( "assDirectory", ( self.temporaryDirectory() / "assTests" ).as_posix() ) )

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

		self.assertFalse( ( self.temporaryDirectory() / "renderTests" ).exists() )
		self.assertFalse( ( self.temporaryDirectory() / "assTests" ).exists() )
		self.assertFalse( ( self.temporaryDirectory() / "assTests" / "test.0001.ass" ).exists() )

		s["fileName"].setValue( self.temporaryDirectory() / "test.gfr" )

		with s.context() :
			s["render"]["task"].execute()

		self.assertTrue( ( self.temporaryDirectory() / "renderTests" ).exists() )
		self.assertTrue( ( self.temporaryDirectory() / "assTests" ).exists())
		self.assertTrue( ( self.temporaryDirectory() / "assTests"/ "test.0001.ass" ).exists() )

		# check it can cope with everything already existing

		with s.context() :
			s["render"]["task"].execute()

		self.assertTrue( ( self.temporaryDirectory() / "renderTests" ).exists() )
		self.assertTrue( ( self.temporaryDirectory() / "assTests" ).exists() )
		self.assertTrue( ( self.temporaryDirectory() / "assTests" / "test.0001.ass" ).exists() )

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
				( self.temporaryDirectory() / "${wedge:value}.exr" ).as_posix(),
				"exr",
				"rgba",
				{
				}
			)
		)
		s["outputs"]["in"].setInput( s["attributes"]["out"] )

		s["render"] = GafferArnold.ArnoldRender()
		s["render"]["fileName"].setValue( self.temporaryDirectory() / "test.####.ass" )
		s["render"]["in"].setInput( s["outputs"]["out"] )

		s["wedge"] = GafferDispatch.Wedge()
		s["wedge"]["mode"].setValue( int( s["wedge"].Mode.StringList ) )
		s["wedge"]["strings"].setValue( IECore.StringVectorData( [ "visible", "hidden" ] ) )
		s["wedge"]["preTasks"][0].setInput( s["render"]["task"] )

		s["fileName"].setValue( self.temporaryDirectory() / "test.gfr" )
		s.save()

		dispatcher = GafferDispatch.LocalDispatcher( jobPool = GafferDispatch.LocalDispatcher.JobPool() )
		dispatcher["jobsDirectory"].setValue( self.temporaryDirectory() / "testJobDirectory" )
		dispatcher["framesMode"].setValue( GafferDispatch.Dispatcher.FramesMode.CurrentFrame )
		dispatcher["executeInBackground"].setValue( False )

		dispatcher.dispatch( [ s["wedge"] ] )

		hidden = GafferImage.ImageReader()
		hidden["fileName"].setValue( self.temporaryDirectory() / "hidden.exr" )

		visible = GafferImage.ImageReader()
		visible["fileName"].setValue( self.temporaryDirectory() / "visible.exr" )

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
		s["render"]["fileName"].setValue( self.temporaryDirectory() / "test.ass" )

		# No motion blur

		s["options"]["options"]["transformBlur"]["value"].setValue( False )
		s["render"]["task"].execute()

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, str( self.temporaryDirectory() / "test.ass" ), None )

			camera = arnold.AiNodeLookUpByName( universe, "gaffer:defaultCamera" )
			sphere = arnold.AiNodeLookUpByName( universe, "/group/sphere" )
			sphereMotionStart = arnold.AiNodeGetFlt( sphere, "motion_start" )
			sphereMotionEnd = arnold.AiNodeGetFlt( sphere, "motion_end" )
			sphereMatrix = arnold.AiNodeGetMatrix( sphere, "matrix" )

			plane = arnold.AiNodeLookUpByName( universe, "/group/plane" )
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

			self.assertEqual( arnold.AiNodeGetBool( arnold.AiUniverseGetOptions( universe ), "ignore_motion_blur" ), False )

		# Motion blur

		s["options"]["options"]["transformBlur"]["value"].setValue( True )
		s["render"]["task"].execute()

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, str( self.temporaryDirectory() / "test.ass" ), None )

			camera = arnold.AiNodeLookUpByName( universe, "gaffer:defaultCamera" )
			sphere = arnold.AiNodeLookUpByName( universe, "/group/sphere" )
			sphereMotionStart = arnold.AiNodeGetFlt( sphere, "motion_start" )
			sphereMotionEnd = arnold.AiNodeGetFlt( sphere, "motion_end" )
			sphereMatrices = arnold.AiNodeGetArray( sphere, "matrix" )

			plane = arnold.AiNodeLookUpByName( universe, "/group/plane" )
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

			self.assertEqual( arnold.AiNodeGetBool( arnold.AiUniverseGetOptions( universe ), "ignore_motion_blur" ), False )

		# Motion blur on, but sampleMotion off

		s["options"]["options"]["sampleMotion"]["enabled"].setValue( True )
		s["options"]["options"]["sampleMotion"]["value"].setValue( False )
		s["render"]["task"].execute()

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, str( self.temporaryDirectory() / "test.ass" ), None )

			camera = arnold.AiNodeLookUpByName( universe, "gaffer:defaultCamera" )
			sphere = arnold.AiNodeLookUpByName( universe, "/group/sphere" )
			sphereMotionStart = arnold.AiNodeGetFlt( sphere, "motion_start" )
			sphereMotionEnd = arnold.AiNodeGetFlt( sphere, "motion_end" )
			sphereMatrices = arnold.AiNodeGetArray( sphere, "matrix" )

			plane = arnold.AiNodeLookUpByName( universe, "/group/plane" )
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

			self.assertEqual( arnold.AiNodeGetBool( arnold.AiUniverseGetOptions( universe ), "ignore_motion_blur" ), True )

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
		s["render"]["fileName"].setValue( self.temporaryDirectory() / "test.ass" )

		# Default camera should have the right resolution.

		s["render"]["task"].execute()

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, str( self.temporaryDirectory() / "test.ass" ), None )
			options = arnold.AiUniverseGetOptions( universe )
			self.assertEqual( arnold.AiNodeGetInt( options, "xres" ), 400 )
			self.assertEqual( arnold.AiNodeGetInt( options, "yres" ), 200 )

		# As should a camera picked from the scene.

		s["options"]["options"]["renderCamera"]["enabled"].setValue( True )
		s["options"]["options"]["renderCamera"]["value"].setValue( "/camera" )
		s["render"]["task"].execute()

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, str( self.temporaryDirectory() / "test.ass" ), None )
			options = arnold.AiUniverseGetOptions( universe )
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
		s["render"]["fileName"].setValue( self.temporaryDirectory() / "test.ass" )

		# Default region
		s["render"]["task"].execute()

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, str( self.temporaryDirectory() / "test.ass" ), None )
			options = arnold.AiUniverseGetOptions( universe )
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

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, str( self.temporaryDirectory() / "test.ass" ), None )
			options = arnold.AiUniverseGetOptions( universe )
			self.assertEqual( arnold.AiNodeGetInt( options, "xres" ), 640 )
			self.assertEqual( arnold.AiNodeGetInt( options, "yres" ), 480 )
			self.assertEqual( arnold.AiNodeGetInt( options, "region_min_x" ), 160 )
			self.assertEqual( arnold.AiNodeGetInt( options, "region_max_x" ), 479 )
			self.assertEqual( arnold.AiNodeGetInt( options, "region_min_y" ), 240 )
			self.assertEqual( arnold.AiNodeGetInt( options, "region_max_y" ), 479 )

		# Test Empty Crop Window
		s["options"]["options"]["renderCropWindow"]["value"].setValue( imath.Box2f() )

		s["render"]["task"].execute()

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, str( self.temporaryDirectory() / "test.ass" ), None )
			options = arnold.AiUniverseGetOptions( universe )
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

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, str( self.temporaryDirectory() / "test.ass" ), None )
			options = arnold.AiUniverseGetOptions( universe )
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
		s["render"]["fileName"].setValue( self.temporaryDirectory() / "test.ass" )

		# The requested camera doesn't exist - this should raise an exception.

		self.assertRaisesRegex( RuntimeError, "/i/dont/exist", s["render"]["task"].execute )

		# And even the existence of a different camera shouldn't change that.

		s["camera"] = GafferScene.Camera()
		s["options"]["in"].setInput( s["camera"]["out"] )

		self.assertRaisesRegex( RuntimeError, "/i/dont/exist", s["render"]["task"].execute )

	def testManyCameras( self ) :

		camera = GafferScene.Camera()

		duplicate = GafferScene.Duplicate()
		duplicate["in"].setInput( camera["out"] )
		duplicate["target"].setValue( "/camera" )
		duplicate["copies"].setValue( 1000 )

		render = GafferArnold.ArnoldRender()
		render["in"].setInput( duplicate["out"] )
		render["mode"].setValue( render.Mode.SceneDescriptionMode )
		render["fileName"].setValue( self.temporaryDirectory() / "test.ass" )

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
		render["fileName"].setValue( self.temporaryDirectory() / "test.####.ass" )

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

		with Gaffer.Context() as c :
			for i in range( 0, 2 ) :
				c.setFrame( i )
				self.assertTrue( pathlib.Path( c.substitute( render["fileName"].getValue() ) ).exists() )

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
		render["fileName"].setValue( self.temporaryDirectory() / "test.ass" )

		render["task"].execute()

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, str( self.temporaryDirectory() / "test.ass" ), None )

			firstSphere = arnold.AiNodeLookUpByName( universe, "/group/sphere" )
			secondSphere = arnold.AiNodeLookUpByName( universe, "/group/sphere1" )

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
		script["render"]["fileName"].setValue( self.temporaryDirectory() / "test.ass" )

		for i in range( 0, 100 ) :

			with Gaffer.Context() as context :
				context["lightName"] = "light%d" % i
				script["render"]["task"].execute()

	def testFrameAndAASeed( self ) :

		options = GafferArnold.ArnoldOptions()

		render = GafferArnold.ArnoldRender()
		render["in"].setInput( options["out"] )
		render["mode"].setValue( render.Mode.SceneDescriptionMode )
		render["fileName"].setValue( self.temporaryDirectory() / "test.ass" )

		for frame in ( 1, 2, 2.8, 3.2 ) :
			for seed in ( None, 3, 4 ) :
				with Gaffer.Context() as c :

					c.setFrame( frame )

					options["options"]["aaSeed"]["enabled"].setValue( seed is not None )
					options["options"]["aaSeed"]["value"].setValue( seed or 1 )

					render["task"].execute()

					with IECoreArnold.UniverseBlock( writable = True ) as universe :

						arnold.AiSceneLoad( universe, str( self.temporaryDirectory() / "test.ass" ), None )

						self.assertEqual(
							arnold.AiNodeGetInt( arnold.AiUniverseGetOptions( universe ), "AA_seed" ),
							seed or round( frame )
						)

	def testRendererContextVariable( self ) :

		sphere = GafferScene.Sphere()
		sphere["name"].setValue( "sphere${scene:renderer}" )

		render = GafferArnold.ArnoldRender()
		render["in"].setInput( sphere["out"] )
		render["mode"].setValue( render.Mode.SceneDescriptionMode )
		render["fileName"].setValue( self.temporaryDirectory() / "test.ass" )

		render["task"].execute()

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, str( self.temporaryDirectory() / "test.ass" ), None )
			self.assertTrue( arnold.AiNodeLookUpByName( universe, "/sphereArnold" ) is not None )

	def testAdaptors( self ) :

		sphere = GafferScene.Sphere()

		def a() :

			result = GafferArnold.ArnoldAttributes()
			result["attributes"]["matte"]["enabled"].setValue( True )
			result["attributes"]["matte"]["value"].setValue( True )

			return result

		GafferScene.SceneAlgo.registerRenderAdaptor( "Test", a )

		sphere = GafferScene.Sphere()

		render = GafferArnold.ArnoldRender()
		render["in"].setInput( sphere["out"] )
		render["mode"].setValue( render.Mode.SceneDescriptionMode )
		render["fileName"].setValue( self.temporaryDirectory() / "test.ass" )

		render["task"].execute()

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, str( self.temporaryDirectory() / "test.ass" ), None )
			node = arnold.AiNodeLookUpByName( universe, "/sphere" )

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

		render = GafferArnold.ArnoldRender()

		attributes["in"].setInput( sphere1["out"] )
		arnoldAttributes["in"].setInput( attributes["out"] )
		group["in"][0].setInput( arnoldAttributes["out"] )
		group["in"][1].setInput( light1["out"] )
		group["in"][2].setInput( light2["out"] )
		group["in"][3].setInput( sphere2["out"] )

		render["in"].setInput( group["out"] )

		# Illumination
		attributes["attributes"]["linkedLights"]["enabled"].setValue( True )
		attributes["attributes"]["linkedLights"]["value"].setValue( "/group/light" )

		# Shadows
		arnoldAttributes["attributes"]["shadowGroup"]["enabled"].setValue( True )
		arnoldAttributes["attributes"]["shadowGroup"]["value"].setValue( "/group/light1" )

		render["mode"].setValue( render.Mode.SceneDescriptionMode )
		render["fileName"].setValue( self.temporaryDirectory() / "test.ass" )
		render["task"].execute()

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, str( self.temporaryDirectory() / "test.ass" ), None )

			# the first sphere had linked lights
			sphere = arnold.AiNodeLookUpByName( universe, "/group/sphere" )

			# check illumination
			self.assertTrue( arnold.AiNodeGetBool( sphere, "use_light_group" ) )
			lights = arnold.AiNodeGetArray( sphere, "light_group" )
			self.assertEqual( arnold.AiArrayGetNumElements( lights ), 1 )
			self.assertEqual(
				arnold.AiNodeGetName( arnold.AiArrayGetPtr( lights, 0 ) ),
				"light:/group/light"
			)

			# check shadows
			self.assertTrue( arnold.AiNodeGetBool( sphere, "use_shadow_group" ) )
			shadows = arnold.AiNodeGetArray( sphere, "shadow_group" )
			self.assertEqual( arnold.AiArrayGetNumElements( shadows ), 1 )
			self.assertEqual(
				arnold.AiNodeGetName( arnold.AiArrayGetPtr( shadows, 0 ) ),
				"light:/group/light1"
			)

			# the second sphere does not have any light linking enabled
			sphere1 = arnold.AiNodeLookUpByName( universe, "/group/sphere1" )

			# check illumination
			self.assertFalse( arnold.AiNodeGetBool( sphere1, "use_light_group" ) )
			lights = arnold.AiNodeGetArray( sphere1, "light_group" )
			self.assertEqual( arnold.AiArrayGetNumElements( lights ), 0 )

			# check shadows
			self.assertFalse( arnold.AiNodeGetBool( sphere1, "use_shadow_group" ) )
			shadows = arnold.AiNodeGetArray( sphere1, "shadow_group" )
			self.assertEqual( arnold.AiArrayGetNumElements( shadows ), 0 )

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
		render["fileName"].setValue( self.temporaryDirectory() / "test.ass" )
		render["task"].execute()

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, str( self.temporaryDirectory() / "test.ass" ), None )

			sphere = arnold.AiNodeLookUpByName( universe, "/group/sphere" )
			self.assertIsNotNone( sphere )

			self.assertEqual( arnold.AiArrayGetNumElements( arnold.AiNodeGetArray( sphere, "light_group" ) ), 0 )
			self.assertFalse( arnold.AiNodeGetBool( sphere, "use_light_group" ) )

	def testLightFilters( self ) :

		s = Gaffer.ScriptNode()

		s["lightFilter"] = GafferArnold.ArnoldLightFilter()
		s["lightFilter"].loadShader( "light_blocker" )

		s["attributes"] = GafferScene.StandardAttributes()
		s["attributes"]["in"].setInput( s["lightFilter"]["out"] )
		s["attributes"]["attributes"]["filteredLights"]["enabled"].setValue( True )
		s["attributes"]["attributes"]["filteredLights"]["value"].setValue( "defaultLights" )

		s["light"] = GafferArnold.ArnoldLight()
		s["light"].loadShader( "point_light" )

		s["gobo"] = GafferArnold.ArnoldShader()
		s["gobo"].loadShader( "gobo" )

		s["assignment"] = GafferScene.ShaderAssignment()
		s["assignment"]["in"].setInput( s["light"]["out"] )
		s["assignment"]["shader"].setInput( s["gobo"]["out"] )

		s["group"] = GafferScene.Group()

		s["group"]["in"][0].setInput( s["attributes"]["out"] )
		s["group"]["in"][1].setInput( s["assignment"]["out"] )

		s["render"] = GafferArnold.ArnoldRender()
		s["render"]["in"].setInput( s["group"]["out"] )
		s["render"]["mode"].setValue( s["render"].Mode.SceneDescriptionMode )
		s["render"]["fileName"].setValue( self.temporaryDirectory() / "test.ass" )

		s["render"]["task"].execute()

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, str( self.temporaryDirectory() / "test.ass" ), None )

			light = arnold.AiNodeLookUpByName( universe, "light:/group/light" )
			linkedFilters = arnold.AiNodeGetArray( light, "filters" )
			numFilters = arnold.AiArrayGetNumElements( linkedFilters.contents )

			self.assertEqual( numFilters, 2 )

			linkedFilter = arnold.cast(arnold.AiArrayGetPtr(linkedFilters, 0), arnold.POINTER(arnold.AtNode))
			linkedGobo = arnold.cast(arnold.AiArrayGetPtr(linkedFilters, 1), arnold.POINTER(arnold.AtNode))

			self.assertEqual( arnold.AiNodeGetName( linkedFilter ), "lightFilter:/group/lightFilter" )
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( linkedFilter ) ), "light_blocker" )
			self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( linkedGobo ) ), "gobo" )

	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 1 )
	def testLightFiltersMany( self ) :

		numLights = 10000
		numLightFilters = 10000

		s = Gaffer.ScriptNode()

		s["lightFilter"] = GafferArnold.ArnoldLightFilter()
		s["lightFilter"].loadShader( "light_blocker" )
		s["lightFilter"]["filteredLights"].setValue( "defaultLights" )

		s["planeFilters"] = GafferScene.Plane( "Plane" )
		s["planeFilters"]["divisions"].setValue( imath.V2i( 1, numLightFilters / 2 - 1 ) )

		s["instancerFilters"] = GafferScene.Instancer( "Instancer" )
		s["instancerFilters"]["in"].setInput( s["planeFilters"]["out"] )
		s["instancerFilters"]["instances"].setInput( s["lightFilter"]["out"] )
		s["instancerFilters"]["parent"].setValue( "/plane" )

		s["light"] = GafferArnold.ArnoldLight()
		s["light"].loadShader( "point_light" )

		s["planeLights"] = GafferScene.Plane( "Plane" )
		s["planeLights"]["divisions"].setValue( imath.V2i( 1, numLights / 2 - 1 ) )

		s["instancerLights"] = GafferScene.Instancer( "Instancer" )
		s["instancerLights"]["in"].setInput( s["planeLights"]["out"] )
		s["instancerLights"]["instances"].setInput( s["light"]["out"] )
		s["instancerLights"]["parent"].setValue( "/plane" )

		s["group"] = GafferScene.Group( "Group" )
		s["group"]["in"][0].setInput( s["instancerFilters"]["out"] )
		s["group"]["in"][1].setInput( s["instancerLights"]["out"] )

		s["render"] = GafferArnold.ArnoldRender()
		s["render"]["in"].setInput( s["group"]["out"] )

		with Gaffer.Context() as c :
			c["scene:render:sceneTranslationOnly"] = IECore.BoolData( True )
			s["render"]["task"].execute()

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
				str( self.temporaryDirectory() / "test.tif" ),
				"tiff",
				"rgba",
				{}
			)
		)
		s["outputs"]["in"].setInput( s["shaderAssignment"]["out"] )

		s["render"] = GafferArnold.ArnoldRender()
		s["render"]["in"].setInput( s["outputs"]["out"] )

		self.assertRaisesRegex( RuntimeError, "Render aborted", s["render"]["task"].execute )

	def testOSLShaders( self ) :

		purple = GafferOSL.OSLShader()
		purple.loadShader( "Maths/MixColor" )
		purple["parameters"]["a"].setValue( imath.Color3f( 0.5, 0, 1 ) )

		green = GafferOSL.OSLShader()
		green.loadShader( "Maths/MixColor" )
		green["parameters"]["a"].setValue( imath.Color3f( 0, 1, 0 ) )

		mix = GafferOSL.OSLShader()
		mix.loadShader( "Maths/MixColor" )
		# test component connections
		mix["parameters"]["a"][2].setInput( purple["out"]["out"][2] )
		# test color connections
		mix["parameters"]["b"].setInput( green["out"]["out"] )
		mix["parameters"]["m"].setValue( 0.5 )

		ball = GafferArnold.ArnoldShaderBall()
		ball["shader"].setInput( mix["out"] )

		catalogue = GafferImage.Catalogue()

		outputs = GafferScene.Outputs()
		outputs.addOutput(
			"beauty",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ClientDisplayDriver",
					"displayHost" : "localhost",
					"displayPort" : str( catalogue.displayDriverServer().portNumber() ),
					"remoteDisplayType" : "GafferImage::GafferDisplayDriver",
				}
			)
		)
		outputs["in"].setInput( ball["out"] )

		render = GafferArnold.ArnoldRender()
		render["in"].setInput( outputs["out"] )

		with GafferTest.ParallelAlgoTest.UIThreadCallHandler() as handler :
			render["task"].execute()

			handler.waitFor( 0.1 ) #Just need to let the catalogue update

			self.assertEqual( self.__color4fAtUV( catalogue, imath.V2f( 0.5 ) ), imath.Color4f( 0, 0.5, 0.5, 1 ) )

	def testDefaultLightsMistakesDontForceLinking( self ) :

		light = GafferArnold.ArnoldLight()
		light.loadShader( "point_light" )

		sphere = GafferScene.Sphere()

		# It doesn't make sense to add a non-light to the "defaultLights"
		# set like this, but in the event of user error, we don't want to
		# emit light links unnecessarily.
		sphereSet = GafferScene.Set()
		sphereSet["in"].setInput( sphere["out"] )
		sphereSet["name"].setValue( "defaultLights" )
		sphereSet["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )

		group = GafferScene.Group()

		group["in"][0].setInput( light["out"] )
		group["in"][1].setInput( sphereSet["out"] )

		render = GafferArnold.ArnoldRender()
		render["in"].setInput( group["out"] )

		render["mode"].setValue( render.Mode.SceneDescriptionMode )
		render["fileName"].setValue( self.temporaryDirectory() / "test.ass" )
		render["task"].execute()

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, str( self.temporaryDirectory() / "test.ass" ), None )

			sphere = arnold.AiNodeLookUpByName( universe, "/group/sphere" )
			self.assertIsNotNone( sphere )

			self.assertEqual( arnold.AiArrayGetNumElements( arnold.AiNodeGetArray( sphere, "light_group" ) ), 0 )
			self.assertFalse( arnold.AiNodeGetBool( sphere, "use_light_group" ) )

	def testLightLinkingWarnings( self ) :

		# Emulate a meshlight that has been set up sloppily - it is filtered to 4 locations, some actually
		# have meshes, some don't
		lightSphere = GafferScene.Sphere()
		lightInvalid = GafferScene.Group()

		lightGroup = GafferScene.Group()
		lightGroup["name"].setValue( "lightGroup" )
		lightGroup["in"][0].setInput( lightSphere["out"] ) # Has a mesh
		lightGroup["in"][1].setInput( lightSphere["out"] ) # Has a mesh
		lightGroup["in"][2].setInput( lightInvalid["out"] ) # Doesn't have a mesh
		lightGroup["in"][3].setInput( lightInvalid["out"] ) # Doesn't have a mesh

		meshLightFilter = GafferScene.PathFilter()
		meshLightFilter["paths"].setValue( IECore.StringVectorData( [ "/lightGroup/*" ] ) )

		meshLight = GafferArnold.ArnoldMeshLight()
		meshLight["in"].setInput( lightGroup["out"] )
		meshLight["filter"].setInput( meshLightFilter["out"] )

		geoSphere = GafferScene.Sphere()
		geoGroup = GafferScene.Group()
		geoGroup["name"].setValue( "geoGroup" )
		for i in range( 20 ):
			geoGroup["in"][i].setInput( geoSphere["out"] )

		group = GafferScene.Group()
		group["in"][0].setInput( geoGroup["out"] )
		group["in"][1].setInput( meshLight["out"] )

		attributeFilter = GafferScene.PathFilter()
		attributeFilter["paths"].setValue( IECore.StringVectorData( [ "/group/geoGroup/*" ] ) )

		attributes = GafferScene.StandardAttributes()
		attributes["in"].setInput( group["out"] )
		attributes["filter"].setInput( attributeFilter["out"] )
		attributes["attributes"]["linkedLights"]["enabled"].setValue( True )
		# Link some ( but not all ) lights, so we have to do actual light linking
		attributes["attributes"]["linkedLights"]["value"].setValue(
			"/group/lightGroup/sphere1 /group/lightGroup/group /group/lightGroup/group1"
		)

		render = GafferArnold.ArnoldRender()
		render["in"].setInput( attributes["out"] )
		render["mode"].setValue( render.Mode.SceneDescriptionMode )
		render["fileName"].setValue( self.temporaryDirectory() / "test.ass" )

		# Don't really understand why a regular `with CapturingMessageHandler` doesn't work here
		try :
			defaultHandler = IECore.MessageHandler.getDefaultHandler()
			mh = IECore.CapturingMessageHandler()
			IECore.MessageHandler.setDefaultHandler( mh )
			render["task"].execute()
		finally :
			IECore.MessageHandler.setDefaultHandler( defaultHandler )

		# We want to see one message per invalid light - not repeated for each location it's referenced at
		self.assertEqual( len( mh.messages ), 2 )
		mm = [ m.message for m in mh.messages ]
		self.assertTrue( "Mesh light without object at location: /group/lightGroup/group" in mm )
		self.assertTrue( "Mesh light without object at location: /group/lightGroup/group1" in mm )

	def __color4fAtUV( self, image, uv ) :

		sampler = GafferImage.ImageSampler()
		sampler["image"].setInput( image["out"] )
		dw = image['out']["format"].getValue().getDisplayWindow().size()
		sampler["pixel"].setValue( uv * imath.V2f( dw.x, dw.y ) )
		return sampler["color"].getValue()

	def __arrayToSet( self, a ) :

		result = set()
		for i in range( 0, arnold.AiArrayGetNumElements( a.contents ) ) :
			if arnold.AiArrayGetType( a.contents ) == arnold.AI_TYPE_STRING :
				result.add( arnold.AiArrayGetStr( a, i ) )
			else :
				raise TypeError

		return result

	def testPerformanceMonitorDoesntCrash( self ) :

		options = GafferScene.StandardOptions()

		options["options"]["performanceMonitor"]["value"].setValue( True )
		options["options"]["performanceMonitor"]["enabled"].setValue( True )

		render = GafferArnold.ArnoldRender()
		render["in"].setInput( options["out"] )
		render["mode"].setValue( render.Mode.SceneDescriptionMode )
		render["fileName"].setValue( self.temporaryDirectory() / "test.ass" )

		render["task"].execute()

	def testShaderSubstitutions( self ) :

		s = Gaffer.ScriptNode()

		s["plane"] = GafferScene.Plane()

		s["planeAttrs"] = GafferScene.CustomAttributes()
		s["planeAttrs"]["in"].setInput( s["plane"]["out"] )
		s["planeAttrs"]["attributes"].addChild( Gaffer.NameValuePlug( "A", Gaffer.StringPlug( "value", defaultValue = 'bar' ) ) )
		s["planeAttrs"]["attributes"].addChild( Gaffer.NameValuePlug( "B", Gaffer.StringPlug( "value", defaultValue = 'foo' ) ) )

		s["cube"] = GafferScene.Cube()

		s["cubeAttrs"] = GafferScene.CustomAttributes()
		s["cubeAttrs"]["in"].setInput( s["cube"]["out"] )
		s["cubeAttrs"]["attributes"].addChild( Gaffer.NameValuePlug( "B", Gaffer.StringPlug( "value", defaultValue = 'override' ) ) )

		s["parent"] = GafferScene.Parent()
		s["parent"]["in"].setInput( s["planeAttrs"]["out"] )
		s["parent"]["children"][0].setInput( s["cubeAttrs"]["out"] )
		s["parent"]["parent"].setValue( "/plane" )

		s["shader"] = GafferArnold.ArnoldShader()
		s["shader"].loadShader( "image" )
		s["shader"]["parameters"]["filename"].setValue( "<attr:A>/path/<attr:B>.tx" )

		s["filter"] = GafferScene.PathFilter()
		s["filter"]["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		s["shaderAssignment"] = GafferScene.ShaderAssignment()
		s["shaderAssignment"]["in"].setInput( s["parent"]["out"] )
		s["shaderAssignment"]["filter"].setInput( s["filter"]["out"] )
		s["shaderAssignment"]["shader"].setInput( s["shader"]["out"] )

		s["light"] = GafferArnold.ArnoldLight()
		s["light"].loadShader( "photometric_light" )
		s["light"]["parameters"]["filename"].setValue( "/path/<attr:A>.ies" )

		s["goboTexture"] = GafferArnold.ArnoldShader()
		s["goboTexture"].loadShader( "image" )
		s["goboTexture"]["parameters"]["filename"].setValue( "<attr:B>/gobo.tx" )

		s["gobo"] = GafferArnold.ArnoldShader()
		s["gobo"].loadShader( "gobo" )
		s["gobo"]["parameters"]["slidemap"].setInput( s["goboTexture"]["out"] )

		s["goboAssign"] = GafferScene.ShaderAssignment()
		s["goboAssign"]["in"].setInput( s["light"]["out"] )
		s["goboAssign"]["shader"].setInput( s["gobo"]["out"] )

		s["lightBlocker"] = GafferArnold.ArnoldLightFilter()
		s["lightBlocker"].loadShader( "light_blocker" )
		s["lightBlocker"]["parameters"]["geometry_type"].setValue( "<attr:geometryType>" )

		s["lightGroup"] = GafferScene.Group()
		s["lightGroup"]["name"].setValue( "lightGroup" )
		s["lightGroup"]["in"][0].setInput( s["goboAssign"]["out"] )
		s["lightGroup"]["in"][1].setInput( s["lightBlocker"]["out"] )

		s["parent2"] = GafferScene.Parent()
		s["parent2"]["in"].setInput( s["shaderAssignment"]["out"] )
		s["parent2"]["children"][0].setInput( s["lightGroup"]["out"] )
		s["parent2"]["parent"].setValue( "/" )

		s["globalAttrs"] = GafferScene.CustomAttributes()
		s["globalAttrs"]["in"].setInput( s["parent2"]["out"] )
		s["globalAttrs"]["global"].setValue( True )
		s["globalAttrs"]["attributes"].addChild( Gaffer.NameValuePlug( "A", Gaffer.StringPlug( "value", defaultValue = 'default1' ) ) )
		s["globalAttrs"]["attributes"].addChild( Gaffer.NameValuePlug( "B", Gaffer.StringPlug( "value", defaultValue = 'default2' ) ) )
		s["globalAttrs"]["attributes"].addChild( Gaffer.NameValuePlug( "geometryType", Gaffer.StringPlug( "value", defaultValue = 'cylinder' ) ) )

		s["render"] = GafferArnold.ArnoldRender()
		s["render"]["in"].setInput( s["globalAttrs"]["out"] )
		s["render"]["mode"].setValue( s["render"].Mode.SceneDescriptionMode )
		s["render"]["fileName"].setValue( self.temporaryDirectory() / "test.ass" )

		s["render"]["task"].execute()

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, str( self.temporaryDirectory() / "test.ass" ), None )
			plane = arnold.AiNodeLookUpByName( universe, "/plane" )
			shader = arnold.AiNodeGetPtr( plane, "shader" )
			self.assertEqual( arnold.AiNodeGetStr( shader, "filename" ), "bar/path/foo.tx" )

			cube = arnold.AiNodeLookUpByName( universe, "/plane/cube" )
			shader2 = arnold.AiNodeGetPtr( cube, "shader" )
			self.assertEqual( arnold.AiNodeGetStr( shader2, "filename" ), "bar/path/override.tx" )

			light = arnold.AiNodeLookUpByName( universe, "light:/lightGroup/light" )
			self.assertEqual( arnold.AiNodeGetStr( light, "filename" ), "/path/default1.ies" )

			gobo = arnold.AiNodeGetPtr( light, "filters" )
			goboTex = arnold.AiNodeGetLink( gobo, "slidemap" )
			self.assertEqual( arnold.AiNodeGetStr( goboTex, "filename" ), "default2/gobo.tx" )

			lightFilter = arnold.AiNodeLookUpByName( universe, "lightFilter:/lightGroup/lightFilter" )
			self.assertEqual( arnold.AiNodeGetStr( lightFilter, "geometry_type" ), "cylinder" )

	def testEncapsulateDeformationBlur( self ) :

		s = Gaffer.ScriptNode()

		# Make a sphere where the red channel has the value of the current frame.

		s["sphere"] = GafferScene.Sphere()

		s["sphereFilter"] = GafferScene.PathFilter()
		s["sphereFilter"]["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )

		s["frame"] = GafferTest.FrameNode()

		s["flat"] = GafferArnold.ArnoldShader()
		s["flat"].loadShader( "flat" )
		s["flat"]["parameters"]["color"].setValue( imath.Color3f( 0 ) )
		s["flat"]["parameters"]["color"]["r"].setInput( s["frame"]["output"] )

		s["assignment"] = GafferScene.ShaderAssignment()
		s["assignment"]["in"].setInput( s["sphere"]["out"] )
		s["assignment"]["shader"].setInput( s["flat"]["out"] )
		s["assignment"]["filter"].setInput( s["sphereFilter"]["out"] )

		# Put the sphere in a capsule.

		s["group"] = GafferScene.Group()
		s["group"]["in"][0].setInput( s["assignment"]["out"] )

		s["groupFilter"] = GafferScene.PathFilter()
		s["groupFilter"]["paths"].setValue( IECore.StringVectorData( [ "/group" ] ) )

		s["encapsulate"] = GafferScene.Encapsulate()
		s["encapsulate"]["in"].setInput( s["group"]["out"] )
		s["encapsulate"]["filter"].setInput( s["groupFilter"]["out"] )

		# Do a render at frame 1, with deformation blur off.

		s["outputs"] = GafferScene.Outputs()
		s["outputs"].addOutput(
			"beauty",
			IECoreScene.Output(
				str( self.temporaryDirectory() / "deformationBlurOff.exr" ),
				"exr",
				"rgba",
				{
				}
			)
		)
		s["outputs"]["in"].setInput( s["encapsulate"]["out"] )

		s["options"] = GafferScene.StandardOptions()
		s["options"]["in"].setInput( s["outputs"]["out"] )

		s["arnoldOptions"] = GafferArnold.ArnoldOptions()
		s["arnoldOptions"]["in"].setInput( s["options"]["out"] )
		s["arnoldOptions"]["options"]["aaSamples"]["enabled"].setValue( True )
		s["arnoldOptions"]["options"]["aaSamples"]["value"].setValue( 6 )

		s["render"] = GafferArnold.ArnoldRender()
		s["render"]["in"].setInput( s["arnoldOptions"]["out"] )
		s["render"]["task"].execute()

		# Do another render at frame 1, but with deformation blur on.

		s["options"]["options"]["deformationBlur"]["enabled"].setValue( True )
		s["options"]["options"]["deformationBlur"]["value"].setValue( True )
		s["options"]["options"]["shutter"]["enabled"].setValue( True )
		s["options"]["options"]["shutter"]["value"].setValue( imath.V2f( -0.5, 0.5 ) )
		s["outputs"]["outputs"][0]["fileName"].setValue( self.temporaryDirectory() / "deformationBlurOn.exr" )
		s["render"]["task"].execute()

		# Check that the renders are the same.

		s["deformationOff"] = GafferImage.ImageReader()
		s["deformationOff"]["fileName"].setValue( self.temporaryDirectory() / "deformationBlurOff.exr" )

		s["deformationOn"] = GafferImage.ImageReader()
		s["deformationOn"]["fileName"].setValue( self.temporaryDirectory() / "deformationBlurOn.exr" )

		# The `maxDifference` is huge to account for noise and watermarks, but is still low enough to check what
		# we want, since if the Encapsulate was sampled at shutter open and not the frame, the difference would be
		# 0.5.
		self.assertImagesEqual( s["deformationOff"]["out"], s["deformationOn"]["out"], maxDifference = 0.27, ignoreMetadata = True )

	def testCoordinateSystem( self ) :

		coordinateSystem = GafferScene.CoordinateSystem()
		render = GafferArnold.ArnoldRender()
		render["in"].setInput( coordinateSystem["out"] )
		render["mode"].setValue( render.Mode.SceneDescriptionMode )
		render["fileName"].setValue( self.temporaryDirectory() / "test.ass" )
		render["task"].execute()

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			arnold.AiSceneLoad( universe, render["fileName"].getValue(), None )

			# Arnold doesn't support coordinate systems, so we don't expect a
			# node to have been created for ours.
			self.assertIsNone( arnold.AiNodeLookUpByName( universe, "/coordinateSystem" ) )

	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 1 )
	def testInstancerPerf( self ) :

		s = Gaffer.ScriptNode()

		s["plane"] = GafferScene.Plane()
		s["plane"]["divisions"].setValue( imath.V2i( 500 ) )

		s["sphere"] = GafferScene.Sphere()

		s["pathFilter"] = GafferScene.PathFilter()
		s["pathFilter"]["paths"].setValue( IECore.StringVectorData( [ '/plane' ] ) )

		s["instancer"] = GafferScene.Instancer()
		s["instancer"]["in"].setInput( s["plane"]["out"] )
		s["instancer"]["filter"].setInput( s["pathFilter"]["out"] )
		s["instancer"]["prototypes"].setInput( s["sphere"]["out"] )

		s["render"] = GafferArnold.ArnoldRender()
		s["render"]["in"].setInput( s["instancer"]["out"] )

		with Gaffer.Context() as c :
			c["scene:render:sceneTranslationOnly"] = IECore.BoolData( True )
			with GafferTest.TestRunner.PerformanceScope() :
				s["render"]["task"].execute()

	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 5 )
	def testInstancerEncapsulatePerf( self ) :

		s = Gaffer.ScriptNode()

		s["plane"] = GafferScene.Plane()
		s["plane"]["divisions"].setValue( imath.V2i( 500 ) )

		s["sphere"] = GafferScene.Sphere()

		s["pathFilter"] = GafferScene.PathFilter()
		s["pathFilter"]["paths"].setValue( IECore.StringVectorData( [ '/plane' ] ) )

		s["instancer"] = GafferScene.Instancer()
		s["instancer"]["in"].setInput( s["plane"]["out"] )
		s["instancer"]["filter"].setInput( s["pathFilter"]["out"] )
		s["instancer"]["prototypes"].setInput( s["sphere"]["out"] )

		s["instancer"]["encapsulateInstanceGroups"].setValue( True )

		s["render"] = GafferArnold.ArnoldRender()
		s["render"]["in"].setInput( s["instancer"]["out"] )

		with Gaffer.Context() as c :
			c["scene:render:sceneTranslationOnly"] = IECore.BoolData( True )
			with GafferTest.TestRunner.PerformanceScope() :
				s["render"]["task"].execute()

	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 1 )
	def testInstancerManyPrototypesPerf( self ) :
		# Having a context variable set without anything in the prototype being affected by that
		# context variable is mostly just going to add stress to the hash cache. This test exists
		# mostly for comparison with the encapsulated case below.

		s = Gaffer.ScriptNode()

		s["plane"] = GafferScene.Plane()
		s["plane"]["divisions"].setValue( imath.V2i( 500 ) )

		s["sphere"] = GafferScene.Sphere()

		s["pathFilter"] = GafferScene.PathFilter()
		s["pathFilter"]["paths"].setValue( IECore.StringVectorData( [ '/plane' ] ) )

		s["instancer"] = GafferScene.Instancer()
		s["instancer"]["in"].setInput( s["plane"]["out"] )
		s["instancer"]["filter"].setInput( s["pathFilter"]["out"] )
		s["instancer"]["prototypes"].setInput( s["sphere"]["out"] )

		s["instancer"]["contextVariables"].addChild( GafferScene.Instancer.ContextVariablePlug( "context" ) )
		s["instancer"]["contextVariables"][0]["name"].setValue( "P" )
		s["instancer"]["contextVariables"][0]["quantize"].setValue( 0 )

		s["render"] = GafferArnold.ArnoldRender()
		s["render"]["in"].setInput( s["instancer"]["out"] )

		with Gaffer.Context() as c :
			c["scene:render:sceneTranslationOnly"] = IECore.BoolData( True )
			with GafferTest.TestRunner.PerformanceScope() :
				s["render"]["task"].execute()

	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 1 )
	def testInstancerManyPrototypesEncapsulatePerf( self ) :
		# Having a context variable set ( even without anything in the prototype reading it ), will force
		# the encapsulate code path to allocate a bunch of separate prototypes, even if they all end up the same.

		s = Gaffer.ScriptNode()

		s["plane"] = GafferScene.Plane()
		s["plane"]["divisions"].setValue( imath.V2i( 500 ) )

		s["sphere"] = GafferScene.Sphere()

		s["pathFilter"] = GafferScene.PathFilter()
		s["pathFilter"]["paths"].setValue( IECore.StringVectorData( [ '/plane' ] ) )

		s["instancer"] = GafferScene.Instancer()
		s["instancer"]["in"].setInput( s["plane"]["out"] )
		s["instancer"]["filter"].setInput( s["pathFilter"]["out"] )
		s["instancer"]["prototypes"].setInput( s["sphere"]["out"] )

		s["instancer"]["contextVariables"].addChild( GafferScene.Instancer.ContextVariablePlug( "context" ) )
		s["instancer"]["contextVariables"][0]["name"].setValue( "P" )
		s["instancer"]["contextVariables"][0]["quantize"].setValue( 0 )

		s["instancer"]["encapsulateInstanceGroups"].setValue( True )

		s["render"] = GafferArnold.ArnoldRender()
		s["render"]["in"].setInput( s["instancer"]["out"] )

		with Gaffer.Context() as c :
			c["scene:render:sceneTranslationOnly"] = IECore.BoolData( True )
			with GafferTest.TestRunner.PerformanceScope() :
				s["render"]["task"].execute()

	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 1 )
	def testInstancerFewPrototypesPerf( self ) :

		# A slightly weird test, but it tests one extreme: there is a context variable, but quantize is
		# set so high that all the contexts end up the same, and only one prototype is needed.
		# This case is particularly bad for the unencapsulated code path, but quite good for the
		# encapsulated path.

		s = Gaffer.ScriptNode()

		s["plane"] = GafferScene.Plane()
		s["plane"]["divisions"].setValue( imath.V2i( 500 ) )

		s["sphere"] = GafferScene.Sphere()

		s["pathFilter"] = GafferScene.PathFilter()
		s["pathFilter"]["paths"].setValue( IECore.StringVectorData( [ '/plane' ] ) )

		s["instancer"] = GafferScene.Instancer()
		s["instancer"]["in"].setInput( s["plane"]["out"] )
		s["instancer"]["filter"].setInput( s["pathFilter"]["out"] )
		s["instancer"]["prototypes"].setInput( s["sphere"]["out"] )

		s["instancer"]["contextVariables"].addChild( GafferScene.Instancer.ContextVariablePlug( "context" ) )
		s["instancer"]["contextVariables"][0]["name"].setValue( "P" )
		s["instancer"]["contextVariables"][0]["quantize"].setValue( 100000 )

		s["render"] = GafferArnold.ArnoldRender()
		s["render"]["in"].setInput( s["instancer"]["out"] )

		with Gaffer.Context() as c :
			c["scene:render:sceneTranslationOnly"] = IECore.BoolData( True )
			with GafferTest.TestRunner.PerformanceScope() :
				s["render"]["task"].execute()

	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 1 )
	def testInstancerFewPrototypesEncapsulatePerf( self ) :

		s = Gaffer.ScriptNode()

		s["plane"] = GafferScene.Plane()
		s["plane"]["divisions"].setValue( imath.V2i( 500 ) )

		s["sphere"] = GafferScene.Sphere()

		s["pathFilter"] = GafferScene.PathFilter()
		s["pathFilter"]["paths"].setValue( IECore.StringVectorData( [ '/plane' ] ) )

		s["instancer"] = GafferScene.Instancer()
		s["instancer"]["in"].setInput( s["plane"]["out"] )
		s["instancer"]["filter"].setInput( s["pathFilter"]["out"] )
		s["instancer"]["prototypes"].setInput( s["sphere"]["out"] )

		s["instancer"]["contextVariables"].addChild( GafferScene.Instancer.ContextVariablePlug( "context" ) )
		s["instancer"]["contextVariables"][0]["name"].setValue( "P" )
		s["instancer"]["contextVariables"][0]["quantize"].setValue( 1000000 )

		s["instancer"]["encapsulateInstanceGroups"].setValue( True )

		s["render"] = GafferArnold.ArnoldRender()
		s["render"]["in"].setInput( s["instancer"]["out"] )

		with Gaffer.Context() as c :
			c["scene:render:sceneTranslationOnly"] = IECore.BoolData( True )
			with GafferTest.TestRunner.PerformanceScope() :
				s["render"]["task"].execute()

	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 1 )
	def testInstancerWithAttributesPerf( self ) :

		s = Gaffer.ScriptNode()

		s["plane"] = GafferScene.Plane()
		s["plane"]["divisions"].setValue( imath.V2i( 500 ) )

		s["pathFilter"] = GafferScene.PathFilter()
		s["pathFilter"]["paths"].setValue( IECore.StringVectorData( [ '/plane' ] ) )

		s["shuffle"] = GafferScene.ShufflePrimitiveVariables()
		s["shuffle"]["in"].setInput( s["plane"]["out"] )
		s["shuffle"]["filter"].setInput( s["pathFilter"]["out"] )
		for v in [ "A", "B", "C", "D", "E", "F", "G", "H" ]:
			s["shuffle"]["shuffles"].addChild( Gaffer.ShufflePlug( "P", v ) )

		s["sphere"] = GafferScene.Sphere()

		s["sphereAttrs"] = GafferScene.CustomAttributes()
		s["sphereAttrs"]["in"].setInput( s["sphere"]["out"] )
		for v in [ "I", "J", "K", "L", "M", "N", "O", "P" ]:
			s["sphereAttrs"]["attributes"].addChild( Gaffer.NameValuePlug( v, Gaffer.IntPlug( "value", defaultValue = 7 ) ) )

		s["instancer"] = GafferScene.Instancer()
		s["instancer"]["in"].setInput( s["shuffle"]["out"] )
		s["instancer"]["filter"].setInput( s["pathFilter"]["out"] )
		s["instancer"]["prototypes"].setInput( s["sphereAttrs"]["out"] )
		s["instancer"]["attributes"].setValue( "P N uv A B C D E F G H" )

		s["render"] = GafferArnold.ArnoldRender()
		s["render"]["in"].setInput( s["instancer"]["out"] )

		with Gaffer.Context() as c :
			c["scene:render:sceneTranslationOnly"] = IECore.BoolData( True )
			with GafferTest.TestRunner.PerformanceScope() :
				s["render"]["task"].execute()

	@GafferTest.TestRunner.PerformanceTestMethod( repeat = 5 )
	def testInstancerWithAttributesEncapsulatePerf( self ) :

		s = Gaffer.ScriptNode()

		s["plane"] = GafferScene.Plane()
		s["plane"]["divisions"].setValue( imath.V2i( 500 ) )

		s["pathFilter"] = GafferScene.PathFilter()
		s["pathFilter"]["paths"].setValue( IECore.StringVectorData( [ '/plane' ] ) )

		s["shuffle"] = GafferScene.ShufflePrimitiveVariables()
		s["shuffle"]["in"].setInput( s["plane"]["out"] )
		s["shuffle"]["filter"].setInput( s["pathFilter"]["out"] )
		for v in [ "A", "B", "C", "D", "E", "F", "G", "H" ]:
			s["shuffle"]["shuffles"].addChild( Gaffer.ShufflePlug( "P", v ) )

		s["sphere"] = GafferScene.Sphere()

		s["sphereAttrs"] = GafferScene.CustomAttributes()
		s["sphereAttrs"]["in"].setInput( s["sphere"]["out"] )
		for v in [ "I", "J", "K", "L", "M", "N", "O", "P" ]:
			s["sphereAttrs"]["attributes"].addChild( Gaffer.NameValuePlug( v, Gaffer.IntPlug( "value", defaultValue = 7 ) ) )

		s["instancer"] = GafferScene.Instancer()
		s["instancer"]["in"].setInput( s["shuffle"]["out"] )
		s["instancer"]["filter"].setInput( s["pathFilter"]["out"] )
		s["instancer"]["prototypes"].setInput( s["sphereAttrs"]["out"] )
		s["instancer"]["attributes"].setValue( "P N uv A B C D E F G H" )

		s["instancer"]["encapsulateInstanceGroups"].setValue( True )

		s["render"] = GafferArnold.ArnoldRender()
		s["render"]["in"].setInput( s["instancer"]["out"] )

		with Gaffer.Context() as c :
			c["scene:render:sceneTranslationOnly"] = IECore.BoolData( True )
			with GafferTest.TestRunner.PerformanceScope() :
				s["render"]["task"].execute()

if __name__ == "__main__":
	unittest.main()
