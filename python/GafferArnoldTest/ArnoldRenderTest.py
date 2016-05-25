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

	def __assertStructsEqual( self, a, b ) :

		for field in a._fields_ :
			self.assertEqual( getattr( a, field[0] ), getattr( b, field[0] ) )

if __name__ == "__main__":
	unittest.main()
