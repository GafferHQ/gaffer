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

import IECore
import IECoreArnold

import Gaffer
import GafferTest
import GafferDispatch
import GafferImage
import GafferScene
import GafferArnold
import GafferArnoldTest

class ArnoldRenderTest( GafferTest.TestCase ) :

	def setUp( self ) :

		GafferTest.TestCase.setUp( self )

		self.__scriptFileName = self.temporaryDirectory() + "/test.gfr"

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
			IECore.Display(
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
			IECore.Display(
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
		s["variables"].addMember( "renderDirectory", self.temporaryDirectory() + "/renderTests" )
		s["variables"].addMember( "assDirectory", self.temporaryDirectory() + "/assTests" )

		s["plane"] = GafferScene.Plane()

		s["outputs"] = GafferScene.Outputs()
		s["outputs"]["in"].setInput( s["plane"]["out"] )
		s["outputs"].addOutput(
			"beauty",
			IECore.Display(
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
		s["filter"]["set"].setValue( "hidden" )

		s["attributes"] = GafferScene.StandardAttributes()
		s["attributes"]["attributes"]["visibility"]["enabled"].setValue( True )
		s["attributes"]["attributes"]["visibility"]["value"].setValue( False )
		s["attributes"]["filter"].setInput( s["filter"]["out"] )
		s["attributes"]["in"].setInput( s["sphere"]["out"] )

		s["outputs"] = GafferScene.Outputs()
		s["outputs"].addOutput(
			"beauty",
			IECore.Display(
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
		hiddenStats["regionOfInterest"].setValue( hiddenStats["in"]["dataWindow"].getValue() )

		visibleStats = GafferImage.ImageStats()
		visibleStats["in"].setInput( visible["out"] )
		visibleStats["regionOfInterest"].setValue( visibleStats["in"]["dataWindow"].getValue() )

		self.assertLess( hiddenStats["average"].getValue()[0], 0.05 )
		self.assertGreater( visibleStats["average"].getValue()[0], .35 )

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
		s["options"]["options"]["transformBlur"]["enabled"].setValue( True )

		s["render"] = GafferArnold.ArnoldRender()
		s["render"]["in"].setInput( s["options"]["out"] )
		s["render"]["mode"].setValue( s["render"].Mode.SceneDescriptionMode )
		s["render"]["fileName"].setValue( self.temporaryDirectory() + "/test.ass" )

		# No motion blur

		s["options"]["options"]["transformBlur"]["value"].setValue( False )
		s["render"]["task"].execute()

		with IECoreArnold.UniverseBlock() :

			arnold.AiASSLoad( self.temporaryDirectory() + "/test.ass" )

			sphere = arnold.AiNodeLookUpByName( "/group/sphere" )
			sphereTimes = arnold.AiNodeGetArray( sphere, "transform_time_samples" )
			sphereMatrix = arnold.AtMatrix()
			arnold.AiNodeGetMatrix( sphere, "matrix", sphereMatrix )

			plane = arnold.AiNodeLookUpByName( "/group/plane" )
			planeTimes = arnold.AiNodeGetArray( plane, "transform_time_samples" )
			planeMatrix = arnold.AtMatrix()
			arnold.AiNodeGetMatrix( plane, "matrix", planeMatrix )

			expectedSphereMatrix = arnold.AtMatrix()
			arnold.AiM4Translation( expectedSphereMatrix, arnold.AtVector( 0, 2, 0 ) )

			expectedPlaneMatrix = arnold.AtMatrix()
			arnold.AiM4Translation( expectedPlaneMatrix, arnold.AtVector( 1, 0, 0 ) )

			self.__assertStructsEqual( sphereMatrix, expectedSphereMatrix )
			self.__assertStructsEqual( planeMatrix, expectedPlaneMatrix )

		# Motion blur

		s["options"]["options"]["transformBlur"]["value"].setValue( True )
		s["render"]["task"].execute()

		with IECoreArnold.UniverseBlock() :

			arnold.AiASSLoad( self.temporaryDirectory() + "/test.ass" )

			sphere = arnold.AiNodeLookUpByName( "/group/sphere" )
			sphereTimes = arnold.AiNodeGetArray( sphere, "transform_time_samples" )
			sphereMatrices = arnold.AiNodeGetArray( sphere, "matrix" )

			plane = arnold.AiNodeLookUpByName( "/group/plane" )
			planeTimes = arnold.AiNodeGetArray( plane, "transform_time_samples" )
			planeMatrices = arnold.AiNodeGetArray( plane, "matrix" )

			self.assertEqual( sphereTimes.contents.nelements, 2 )
			self.assertEqual( sphereTimes.contents.nkeys, 1 )
			self.assertEqual( sphereMatrices.contents.nelements, 1 )
			self.assertEqual( sphereMatrices.contents.nkeys, 2 )

			self.assertEqual( planeTimes.contents.nelements, 2 )
			self.assertEqual( planeTimes.contents.nkeys, 1 )
			self.assertEqual( planeMatrices.contents.nelements, 1 )
			self.assertEqual( planeMatrices.contents.nkeys, 2 )

			for i in range( 0, 2 ) :

				frame = 0.75 + 0.5 * i
				self.assertEqual( arnold.AiArrayGetFlt( sphereTimes, i ), frame )
				self.assertEqual( arnold.AiArrayGetFlt( planeTimes, i ), frame )

				sphereMatrix = arnold.AtMatrix()
				arnold.AiArrayGetMtx( sphereMatrices, i, sphereMatrix )

				expectedSphereMatrix = arnold.AtMatrix()
				arnold.AiM4Translation( expectedSphereMatrix, arnold.AtVector( 0, frame * 2, frame - 1 ) )

				planeMatrix = arnold.AtMatrix()
				arnold.AiArrayGetMtx( planeMatrices, i, planeMatrix )

				expectedPlaneMatrix = arnold.AtMatrix()
				arnold.AiM4Translation( expectedPlaneMatrix, arnold.AtVector( 1, 0, frame - 1 ) )

				self.__assertStructsEqual( sphereMatrix, expectedSphereMatrix )
				self.__assertStructsEqual( planeMatrix, expectedPlaneMatrix )

	def testResolution( self ) :

		s = Gaffer.ScriptNode()

		s["camera"] = GafferScene.Camera()

		s["options"] = GafferScene.StandardOptions()
		s["options"]["in"].setInput( s["camera"]["out"] )
		s["options"]["options"]["renderResolution"]["enabled"].setValue( True )
		s["options"]["options"]["renderResolution"]["value"].setValue( IECore.V2i( 200, 100 ) )
		s["options"]["options"]["resolutionMultiplier"]["enabled"].setValue( True )
		s["options"]["options"]["resolutionMultiplier"]["value"].setValue( 2 )

		s["render"] = GafferArnold.ArnoldRender()
		s["render"]["in"].setInput( s["options"]["out"] )
		s["render"]["mode"].setValue( s["render"].Mode.SceneDescriptionMode )
		s["render"]["fileName"].setValue( self.temporaryDirectory() + "/test.ass" )

		# Default camera should have the right resolution.

		s["render"]["task"].execute()

		with IECoreArnold.UniverseBlock() :

			arnold.AiASSLoad( self.temporaryDirectory() + "/test.ass" )
			options = arnold.AiUniverseGetOptions()
			self.assertEqual( arnold.AiNodeGetInt( options, "xres" ), 400 )
			self.assertEqual( arnold.AiNodeGetInt( options, "yres" ), 200 )

		# As should a camera picked from the scene.

		s["options"]["options"]["renderCamera"]["enabled"].setValue( True )
		s["options"]["options"]["renderCamera"]["value"].setValue( "/camera" )
		s["render"]["task"].execute()

		with IECoreArnold.UniverseBlock() :

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

		with IECoreArnold.UniverseBlock() :

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
		s["options"]["options"]["renderCropWindow"]["value"].setValue( IECore.Box2f( IECore.V2f( 0.25, 0.5 ), IECore.V2f( 0.75, 1.0 ) ) )

		s["render"]["task"].execute()

		with IECoreArnold.UniverseBlock() :

			arnold.AiASSLoad( self.temporaryDirectory() + "/test.ass" )
			options = arnold.AiUniverseGetOptions()
			self.assertEqual( arnold.AiNodeGetInt( options, "xres" ), 640 )
			self.assertEqual( arnold.AiNodeGetInt( options, "yres" ), 480 )
			self.assertEqual( arnold.AiNodeGetInt( options, "region_min_x" ), 160 )
			self.assertEqual( arnold.AiNodeGetInt( options, "region_max_x" ), 479 )
			self.assertEqual( arnold.AiNodeGetInt( options, "region_min_y" ), 240 )
			self.assertEqual( arnold.AiNodeGetInt( options, "region_max_y" ), 479 )

		# Test Empty Crop Window
		s["options"]["options"]["renderCropWindow"]["value"].setValue( IECore.Box2f() )

		s["render"]["task"].execute()

		with IECoreArnold.UniverseBlock() :

			arnold.AiASSLoad( self.temporaryDirectory() + "/test.ass" )
			options = arnold.AiUniverseGetOptions()
			self.assertEqual( arnold.AiNodeGetInt( options, "xres" ), 640 )
			self.assertEqual( arnold.AiNodeGetInt( options, "yres" ), 480 )

			# Since Arnold doesn't support empty regions, we default to one pixel in the corner
			self.assertEqual( arnold.AiNodeGetInt( options, "region_min_x" ), 0 )
			self.assertEqual( arnold.AiNodeGetInt( options, "region_max_x" ), 0 )
			self.assertEqual( arnold.AiNodeGetInt( options, "region_min_y" ), 0 )
			self.assertEqual( arnold.AiNodeGetInt( options, "region_max_y" ), 0 )

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

		with IECoreArnold.UniverseBlock() :

			arnold.AiASSLoad( self.temporaryDirectory() + "/test.ass" )
			options = arnold.AiUniverseGetOptions()
			self.assertEqual( arnold.AiNodeGetInt( options, "xres" ), 640 )
			self.assertEqual( arnold.AiNodeGetInt( options, "yres" ), 480 )
			self.assertEqual( arnold.AiNodeGetInt( options, "region_min_x" ), -192 )
			self.assertEqual( arnold.AiNodeGetInt( options, "region_max_x" ), 640 + 255 )
			self.assertEqual( arnold.AiNodeGetInt( options, "region_min_y" ), -96 )
			self.assertEqual( arnold.AiNodeGetInt( options, "region_max_y" ), 480 + 47 )

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

		with IECoreArnold.UniverseBlock() :

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

	def __arrayToSet( self, a ) :

		result = set()
		for i in range( 0, a.contents.nelements ) :
			if a.contents.type == arnold.AI_TYPE_STRING :
				result.add( arnold.AiArrayGetStr( a, i ) )
			else :
				raise TypeError

		return result

	def __assertStructsEqual( self, a, b ) :

		for field in a._fields_ :
			self.assertEqual( getattr( a, field[0] ), getattr( b, field[0] ) )

if __name__ == "__main__":
	unittest.main()
