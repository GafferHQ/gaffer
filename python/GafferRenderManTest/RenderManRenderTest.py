##########################################################################
#
#  Copyright (c) 2013-2014, Image Engine Design Inc. All rights reserved.
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
import unittest
import subprocess32 as subprocess

import IECore

import Gaffer
import GafferImage
import GafferScene
import GafferSceneTest
import GafferRenderMan
import GafferRenderManTest

class RenderManRenderTest( GafferRenderManTest.RenderManTestCase ) :

	def testBoundsAndImageOutput( self ) :

		s = Gaffer.ScriptNode()

		s["plane"] = GafferScene.Plane()
		s["plane"]["transform"]["translate"].setValue( IECore.V3f( 0, 0, -5 ) )

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

		s["render"] = GafferRenderMan.RenderManRender()
		s["render"]["in"].setInput( s["outputs"]["out"] )
		s["render"]["mode"].setValue( "generate" )

		s["render"]["ribFileName"].setValue( self.temporaryDirectory() + "/test.rib" )

		s["fileName"].setValue( self.temporaryDirectory() + "/test.gfr" )
		s.save()

		s["render"].execute()

		self.assertTrue( os.path.exists( self.temporaryDirectory() + "/test.rib" ) )

		p = subprocess.Popen(
			"renderdl " + self.temporaryDirectory() + "/test.rib",
			shell = True,
			stderr = subprocess.PIPE
		)
		p.wait()

		self.failIf( "exceeded its bounds" in "".join( p.stderr.readlines() ) )

		self.assertTrue( os.path.exists( self.temporaryDirectory() + "/test.tif" ) )

	def testCameraMotionBlur( self ) :

		s = Gaffer.ScriptNode()

		s["camera"] = GafferScene.Camera()

		s["attributes"] = GafferScene.StandardAttributes()
		s["attributes"]["in"].setInput( s["camera"]["out"] )

		s["options"] = GafferScene.StandardOptions()
		s["options"]["in"].setInput( s["attributes"]["out"] )
		s["options"]["options"]["renderCamera"]["enabled"].setValue( True )
		s["options"]["options"]["renderCamera"]["value"].setValue( "/camera" )

		s["render"] = GafferRenderMan.RenderManRender()
		s["render"]["in"].setInput( s["options"]["out"] )
		s["render"]["mode"].setValue( "generate" )

		s["render"]["ribFileName"].setValue( self.temporaryDirectory() + "/test.rib" )

		s["fileName"].setValue( self.temporaryDirectory() + "/test.gfr" )
		s.save()

		s["render"].execute()

		self.assertTrue( os.path.exists( self.temporaryDirectory() + "/test.rib" ) )

		# camera motion off, we should have no motion statements

		r = "".join( file( self.temporaryDirectory() + "/test.rib" ).readlines() )
		self.failIf( "MotionBegin" in r )

		# camera motion on, we should have no motion statements

		s["options"]["options"]["cameraBlur"]["enabled"].setValue( True )
		s["options"]["options"]["cameraBlur"]["value"].setValue( True )

		s["render"].execute()

		r = "".join( file( self.temporaryDirectory() + "/test.rib" ).readlines() )
		self.failUnless( "MotionBegin" in r )

		# motion disabled on camera object, we should have no motion statements
		# even though motion blur is enabled in the globals.

		s["attributes"]["attributes"]["transformBlur"]["enabled"].setValue( True )
		s["attributes"]["attributes"]["transformBlur"]["value"].setValue( False )

		s["render"].execute()

		r = "".join( file( self.temporaryDirectory() + "/test.rib" ).readlines() )
		self.failIf( "MotionBegin" in r )

		# motion enabled on camera object, with extra samples specified. we should
		# have a motion statement with multiple segments

		s["attributes"]["attributes"]["transformBlur"]["value"].setValue( True )
		s["attributes"]["attributes"]["transformBlurSegments"]["enabled"].setValue( True )
		s["attributes"]["attributes"]["transformBlurSegments"]["value"].setValue( 5 )

		s["render"].execute()

		def motionTimes( ribFileName ) :

			for line in file( ribFileName ).readlines() :
				if "MotionBegin" in line :
					times = line.partition( "[" )[2].partition( "]" )[0]
					times = times.strip().split()
					return [ float( t ) for t in times ]

			return []

		self.assertEqual( len( motionTimes( self.temporaryDirectory() + "/test.rib" ) ), 6 )

		# different shutter times

		s["attributes"]["attributes"]["transformBlurSegments"]["enabled"].setValue( False )
		s["options"]["options"]["shutter"]["enabled"].setValue( True )

		s["render"].execute()

		self.assertEqual( motionTimes( self.temporaryDirectory() + "/test.rib" ), [ 0.75, 1.25 ] )

		s["options"]["options"]["shutter"]["value"].setValue( IECore.V2f( -0.1, 0.3 ) )

		s["render"].execute()

		self.assertEqual( motionTimes( self.temporaryDirectory() + "/test.rib" ), [ 0.9, 1.3 ] )

	def testDynamicLoadProcedural( self ) :

		s = Gaffer.ScriptNode()

		s["plane"] = GafferScene.Plane()

		s["render"] = GafferRenderMan.RenderManRender()
		s["render"]["in"].setInput( s["plane"]["out"] )
		s["render"]["mode"].setValue( "generate" )

		s["render"]["ribFileName"].setValue( self.temporaryDirectory() + "/test.rib" )

		s["fileName"].setValue( self.temporaryDirectory() + "/test.gfr" )
		s.save()

		s["render"].execute()

		self.assertTrue( os.path.exists( self.temporaryDirectory() + "/test.rib" ) )

		rib = "\n".join( file( self.temporaryDirectory() + "/test.rib" ).readlines() )
		self.assertTrue( "DynamicLoad" in rib )
		self.assertFalse( "Polygon" in rib )

	def testDirectoryCreation( self ) :

		s = Gaffer.ScriptNode()
		s["variables"].addMember( "renderDirectory", self.temporaryDirectory() + "/renderTests" )
		s["variables"].addMember( "ribDirectory", self.temporaryDirectory() + "/ribTests" )

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

		s["render"] = GafferRenderMan.RenderManRender()
		s["render"]["in"].setInput( s["outputs"]["out"] )
		s["render"]["ribFileName"].setValue( "$ribDirectory/test.####.rib" )
		s["render"]["mode"].setValue( "generate" )

		self.assertFalse( os.path.exists( self.temporaryDirectory() + "/renderTests" ) )
		self.assertFalse( os.path.exists( self.temporaryDirectory() + "/ribTests" ) )
		self.assertFalse( os.path.exists( self.temporaryDirectory() + "/ribTests/test.0001.rib" ) )

		s["fileName"].setValue( self.temporaryDirectory() + "/test.gfr" )

		with s.context() :
			s["render"].execute()

		self.assertTrue( os.path.exists( self.temporaryDirectory() + "/renderTests" ) )
		self.assertTrue( os.path.exists( self.temporaryDirectory() + "/ribTests" ) )
		self.assertTrue( os.path.exists( self.temporaryDirectory() + "/ribTests/test.0001.rib" ) )

		# check that having the directories already exist is ok too

		with s.context() :
			s["render"].execute()

		self.assertTrue( os.path.exists( self.temporaryDirectory() + "/renderTests" ) )
		self.assertTrue( os.path.exists( self.temporaryDirectory() + "/ribTests" ) )
		self.assertTrue( os.path.exists( self.temporaryDirectory() + "/ribTests/test.0001.rib" ) )

	def testTypeNamePrefixes( self ) :

		self.assertTypeNamesArePrefixed( GafferRenderMan )
		self.assertTypeNamesArePrefixed( GafferRenderManTest )

	def testDefaultNames( self ) :

		self.assertDefaultNamesAreCorrect( GafferRenderMan )
		self.assertDefaultNamesAreCorrect( GafferRenderManTest )

	def testNodesConstructWithDefaultValues( self ) :

		self.assertNodesConstructWithDefaultValues( GafferRenderMan )
		self.assertNodesConstructWithDefaultValues( GafferRenderManTest )

	def testCropWindow( self ) :

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( self.temporaryDirectory() + "/test.gfr" )

		s["p"] = GafferScene.Plane()

		s["o"] = GafferScene.StandardOptions()
		s["o"]["options"]["renderCropWindow"]["enabled"].setValue( True )
		s["o"]["options"]["renderCropWindow"]["value"].setValue( IECore.Box2f( IECore.V2f( 0, 0.5 ), IECore.V2f( 1, 1 ) ) )
		s["o"]["in"].setInput( s["p"]["out"] )

		s["r"] = GafferRenderMan.RenderManRender()
		s["r"]["mode"].setValue( "generate" )
		s["r"]["ribFileName"].setValue( self.temporaryDirectory() + "/test.rib" )
		s["r"]["in"].setInput( s["o"]["out"] )

		s["r"].execute()

		rib = "\n".join( file( self.temporaryDirectory() + "/test.rib" ).readlines() )
		self.assertTrue( "CropWindow 0 1 0.5 1" in rib )

	def testHash( self ) :

		c = Gaffer.Context()
		c.setFrame( 1 )
		c2 = Gaffer.Context()
		c2.setFrame( 2 )

		s = Gaffer.ScriptNode()
		s["plane"] = GafferScene.Plane()
		s["outputs"] = GafferScene.Outputs()
		s["outputs"]["in"].setInput( s["plane"]["out"] )
		s["outputs"].addOutput( "beauty", IECore.Display( "$renderDirectory/test.####.exr", "exr", "rgba", {} ) )
		s["render"] = GafferRenderMan.RenderManRender()

		# no input scene produces no effect
		self.assertEqual( s["render"].hash( c ), IECore.MurmurHash() )

		# now theres an scene to render, we get some output
		s["render"]["in"].setInput( s["outputs"]["out"] )
		self.assertNotEqual( s["render"].hash( c ), IECore.MurmurHash() )

		# output varies by time
		self.assertNotEqual( s["render"].hash( c ), s["render"].hash( c2 ) )

		# output varies by new Context entries
		current = s["render"].hash( c )
		c["renderDirectory"] = self.temporaryDirectory() + "/renderTests"
		self.assertNotEqual( s["render"].hash( c ), current )

		# output varies by changed Context entries
		current = s["render"].hash( c )
		c["renderDirectory"] = self.temporaryDirectory() + "/renderTests2"
		self.assertNotEqual( s["render"].hash( c ), current )

		# output doesn't vary by ui Context entries
		current = s["render"].hash( c )
		c["ui:something"] = "alterTheUI"
		self.assertEqual( s["render"].hash( c ), current )

		# also varies by input node
		current = s["render"].hash( c )
		s["render"]["in"].setInput( s["plane"]["out"] )
		self.assertNotEqual( s["render"].hash( c ), current )

	def testCoordinateSystem( self ) :

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( self.temporaryDirectory() + "/test.gfr" )

		s["c"] = GafferScene.CoordinateSystem()
		s["c"]["name"].setValue( "myCoordSys" )

		s["r"] = GafferRenderMan.RenderManRender()
		s["r"]["mode"].setValue( "generate" )
		s["r"]["ribFileName"].setValue( self.temporaryDirectory() + "/test.rib" )
		s["r"]["in"].setInput( s["c"]["out"] )

		s["r"].execute()

		rib = "\n".join( file( self.temporaryDirectory() + "/test.rib" ).readlines() )
		self.assertTrue( "CoordinateSystem \"/myCoordSys\"" in rib )

	def testRenderToDisplayViaForegroundDispatch( self ) :

		s = Gaffer.ScriptNode()

		s["sphere"] = GafferScene.Sphere()

		s["outputs"] = GafferScene.Outputs()
		s["outputs"].addOutput(
			"beauty",
			IECore.Display(
				"test",
				"ieDisplay",
				"rgba",
				{
					"quantize" : IECore.FloatVectorData( [ 0, 0, 0, 0 ] ),
					"driverType" : "ClientDisplayDriver",
					"displayHost" : "localhost",
					"displayPort" : "1559",
					"remoteDisplayType" : "GafferImage::GafferDisplayDriver",
					"handle" : "myLovelyPlane",
				}
			)
		)
		s["outputs"]["in"].setInput( s["sphere"]["out"] )

		s["display"] = GafferImage.Display()
		def __displayCallback( plug ) :
			pass

		# connect a python function to the Display node image and data
		# received signals. this emulates what the UI does.
		c = (
			s["display"].imageReceivedSignal().connect( __displayCallback ),
			s["display"].dataReceivedSignal().connect( __displayCallback ),
		)

		s["render"] = GafferRenderMan.RenderManRender()
		s["render"]["ribFileName"].setValue( self.temporaryDirectory() + "/test.rib" )
		s["render"]["in"].setInput( s["outputs"]["out"] )

		s["fileName"].setValue( self.temporaryDirectory() + "/test.gfr" )
		s.save()

		# dispatch the render on the foreground thread. if we don't manage
		# the GIL appropriately, we'll get a deadlock when the Display signals
		# above try to enter python on the background thread.
		dispatcher = Gaffer.LocalDispatcher()
		dispatcher["jobsDirectory"].setValue( self.temporaryDirectory() + "/testJobDirectory" )
		dispatcher["framesMode"].setValue( Gaffer.Dispatcher.FramesMode.CurrentFrame )
		dispatcher["executeInBackground"].setValue( False )

		dispatcher.dispatch( [ s["render"] ] )

	def testCommand( self ) :

		s = Gaffer.ScriptNode()

		s["sphere"] = GafferScene.Sphere()

		s["outputs"] = GafferScene.Outputs()
		s["outputs"].addOutput(
			"beauty",
			IECore.Display(
				"test",
				"ieDisplay",
				"rgba",
				{
					"quantize" : IECore.FloatVectorData( [ 0, 0, 0, 0 ] ),
					"driverType" : "ClientDisplayDriver",
					"displayHost" : "localhost",
					"displayPort" : "1559",
					"remoteDisplayType" : "GafferImage::GafferDisplayDriver",
					"handle" : "myLovelyPlane",
				}
			)
		)
		s["outputs"]["in"].setInput( s["sphere"]["out"] )

		s["display"] = GafferImage.Display()

		s["render"] = GafferRenderMan.RenderManRender()
		s["render"]["ribFileName"].setValue( self.temporaryDirectory() + "/test.rib" )
		s["render"]["in"].setInput( s["outputs"]["out"] )

		s["fileName"].setValue( self.temporaryDirectory() + "/test.gfr" )
		s.save()

		# render a full frame and get the data window
		s["render"].execute()
		dataWindow1 = s["display"]["out"].image().dataWindow

		# specify a crop on the command line and get the new data window
		s["render"]["command"].setValue( "renderdl -crop 0 0.5 0 0.5" )
		s["render"].execute()

		# check that the crop worked
		dataWindow2 = s["display"]["out"].image().dataWindow
		self.assertEqual( dataWindow2.size(), dataWindow1.size() / 2 )

		# now check that we can specify values via the context too
		s["render"]["command"].setValue( "renderdl -crop 0 ${size} 0 ${size}" )
		s.context()["size"] = 0.25
		with s.context() :
			s["render"].execute()

		dataWindow3 = s["display"]["out"].image().dataWindow
		self.assertEqual( dataWindow3.size(), dataWindow1.size() / 4 )

	def testOptions( self ) :

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( self.temporaryDirectory() + "/test.gfr" )

		s["p"] = GafferScene.Plane()

		s["o"] = GafferRenderMan.RenderManOptions()
		s["o"]["options"]["pixelSamples"]["enabled"].setValue( True )
		s["o"]["options"]["pixelSamples"]["value"].setValue( IECore.V2i( 2, 3 ) )
		s["o"]["in"].setInput( s["p"]["out"] )

		s["r"] = GafferRenderMan.RenderManRender()
		s["r"]["mode"].setValue( "generate" )
		s["r"]["ribFileName"].setValue( self.temporaryDirectory() + "/test.rib" )
		s["r"]["in"].setInput( s["o"]["out"] )

		s["r"].execute()

		rib = "\n".join( file( self.temporaryDirectory() + "/test.rib" ).readlines() )
		self.assertTrue( "PixelSamples 2 3" in rib )

	def testFrameBlock( self ) :

		s = Gaffer.ScriptNode()

		s["p"] = GafferScene.Plane()

		s["r"] = GafferRenderMan.RenderManRender()
		s["r"]["mode"].setValue( "generate" )
		s["r"]["ribFileName"].setValue( self.temporaryDirectory() + "/test.rib" )
		s["r"]["in"].setInput( s["p"]["out"] )

		with Gaffer.Context( s.context() ) as context :
			for i in range( 0, 10 ) :
				context.setFrame( i )
				s["r"].execute()
				rib = "\n".join( file( self.temporaryDirectory() + "/test.rib" ).readlines() )
				self.assertTrue( "FrameBegin %d" % i in rib )

	def testMultipleCameras( self ) :

		s = Gaffer.ScriptNode()

		s["camera1"] = GafferScene.Camera()
		s["camera1"]["name"].setValue( "camera1" )

		s["camera2"] = GafferScene.Camera()
		s["camera2"]["name"].setValue( "camera2" )

		s["camera3"] = GafferScene.Camera()
		s["camera3"]["name"].setValue( "camera3" )

		s["group"] = GafferScene.Group()
		s["group"]["in"][0].setInput( s["camera1"]["out"] )
		s["group"]["in"][1].setInput( s["camera2"]["out"] )
		s["group"]["in"][2].setInput( s["camera3"]["out"] )

		s["options"] = GafferScene.StandardOptions()
		s["options"]["in"].setInput( s["group"]["out"] )
		s["options"]["options"]["renderCamera"]["enabled"].setValue( True )
		s["options"]["options"]["renderCamera"]["value"].setValue( "/group/camera2" )

		s["render"] = GafferRenderMan.RenderManRender()
		s["render"]["in"].setInput( s["options"]["out"] )
		s["render"]["mode"].setValue( "generate" )

		s["render"]["ribFileName"].setValue( self.temporaryDirectory() + "/test.rib" )

		s["fileName"].setValue( self.temporaryDirectory() + "/test.gfr" )
		s.save()

		s["render"].execute()

		rib = "\n".join( file( self.temporaryDirectory() + "/test.rib" ).readlines() )

		self.assertTrue( "Camera \"/group/camera1\"" in rib )
		self.assertTrue( "Camera \"/group/camera2\"" in rib )
		self.assertTrue( "Camera \"/group/camera3\"" in rib )
		# camera3 must come last, because it is the primary render camera
		self.assertTrue( rib.index( "Camera \"/group/camera2\"" ) > rib.index( "Camera \"/group/camera1\"" ) )
		self.assertTrue( rib.index( "Camera \"/group/camera2\"" ) > rib.index( "Camera \"/group/camera3\"" ) )

	def testHiddenCoordinateSystem( self ) :

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( self.temporaryDirectory() + "/test.gfr" )

		s["c"] = GafferScene.CoordinateSystem()
		s["c"]["name"].setValue( "myCoordSys" )

		s["g"] = GafferScene.Group()
		s["g"]["in"][0].setInput( s["c"]["out"] )

		s["f1"] = GafferScene.PathFilter()
		s["f2"] = GafferScene.PathFilter()

		s["a1"] = GafferScene.StandardAttributes()
		s["a1"]["attributes"]["visibility"]["enabled"].setValue( True )
		s["a1"]["attributes"]["visibility"]["value"].setValue( False )
		s["a1"]["in"].setInput( s["g"]["out"] )
		s["a1"]["filter"].setInput( s["f1"]["out"] )

		s["a2"] = GafferScene.StandardAttributes()
		s["a2"]["attributes"]["visibility"]["enabled"].setValue( True )
		s["a2"]["attributes"]["visibility"]["value"].setValue( True )
		s["a2"]["in"].setInput( s["a1"]["out"] )
		s["a2"]["filter"].setInput( s["f2"]["out"] )

		s["r"] = GafferRenderMan.RenderManRender()
		s["r"]["mode"].setValue( "generate" )
		s["r"]["ribFileName"].setValue( self.temporaryDirectory() + "/test.rib" )
		s["r"]["in"].setInput( s["a2"]["out"] )

		s["r"].execute()
		rib = "\n".join( file( self.temporaryDirectory() + "/test.rib" ).readlines() )
		self.assertTrue( "CoordinateSystem \"/group/myCoordSys\"" in rib )

		s["f1"]["paths"].setValue( IECore.StringVectorData( [ "/group" ] ) ) # hide group

		s["r"].execute()
		rib = "\n".join( file( self.temporaryDirectory() + "/test.rib" ).readlines() )
		self.assertTrue( "CoordinateSystem" not in rib )

		s["f2"]["paths"].setValue( IECore.StringVectorData( [ "/group/myCoordSys" ] ) ) # show coordsys (but parent still hidden)

		s["r"].execute()
		rib = "\n".join( file( self.temporaryDirectory() + "/test.rib" ).readlines() )
		self.assertTrue( "CoordinateSystem" not in rib )

	def testHiddenLight( self ) :

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( self.temporaryDirectory() + "/test.gfr" )

		s["l"] = GafferRenderMan.RenderManLight()
		s["l"]["name"].setValue( "myLight" )
		s["l"].loadShader( "pointlight" )

		s["g"] = GafferScene.Group()
		s["g"]["in"][0].setInput( s["l"]["out"] )

		s["f1"] = GafferScene.PathFilter()
		s["f2"] = GafferScene.PathFilter()

		s["a1"] = GafferScene.StandardAttributes()
		s["a1"]["attributes"]["visibility"]["enabled"].setValue( True )
		s["a1"]["attributes"]["visibility"]["value"].setValue( False )
		s["a1"]["in"].setInput( s["g"]["out"] )
		s["a1"]["filter"].setInput( s["f1"]["out"] )

		s["a2"] = GafferScene.StandardAttributes()
		s["a2"]["attributes"]["visibility"]["enabled"].setValue( True )
		s["a2"]["attributes"]["visibility"]["value"].setValue( True )
		s["a2"]["in"].setInput( s["a1"]["out"] )
		s["a2"]["filter"].setInput( s["f2"]["out"] )

		s["r"] = GafferRenderMan.RenderManRender()
		s["r"]["mode"].setValue( "generate" )
		s["r"]["ribFileName"].setValue( self.temporaryDirectory() + "/test.rib" )
		s["r"]["in"].setInput( s["a2"]["out"] )

		s["r"].execute()
		rib = "\n".join( file( self.temporaryDirectory() + "/test.rib" ).readlines() )
		self.assertTrue( "LightSource \"pointlight\"" in rib )

		s["f1"]["paths"].setValue( IECore.StringVectorData( [ "/group" ] ) ) # hide group

		s["r"].execute()
		rib = "\n".join( file( self.temporaryDirectory() + "/test.rib" ).readlines() )
		self.assertTrue( "LightSource \"pointlight\"" not in rib )

		s["f2"]["paths"].setValue( IECore.StringVectorData( [ "/group/myLight" ] ) ) # show coordsys (but parent still hidden)

		s["r"].execute()
		rib = "\n".join( file( self.temporaryDirectory() + "/test.rib" ).readlines() )
		self.assertTrue( "LightSource \"pointlight\"" not in rib )

	def testClippingPlane( self ) :

		s = Gaffer.ScriptNode()

		s["c"] = GafferScene.ClippingPlane()

		s["r"] = GafferRenderMan.RenderManRender()
		s["r"]["mode"].setValue( "generate" )
		s["r"]["ribFileName"].setValue( self.temporaryDirectory() + "/test.rib" )
		s["r"]["in"].setInput( s["c"]["out"] )

		s["r"].execute()

		rib = "\n".join( file( self.temporaryDirectory() + "/test.rib" ).readlines() )
		self.assertTrue( "ClippingPlane" in rib )

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

		s["render"] = GafferRenderMan.RenderManRender()
		s["render"]["ribFileName"].setValue( self.temporaryDirectory() + "/test.rib" )
		s["render"]["in"].setInput( s["outputs"]["out"] )

		s["wedge"] = Gaffer.Wedge()
		s["wedge"]["mode"].setValue( int( s["wedge"].Mode.StringList ) )
		s["wedge"]["strings"].setValue( IECore.StringVectorData( [ "visible", "hidden" ] ) )
		s["wedge"]["requirements"][0].setInput( s["render"]["requirement"] )

		s["fileName"].setValue( self.temporaryDirectory() + "/test.gfr" )
		s.save()

		dispatcher = Gaffer.LocalDispatcher()
		dispatcher["jobsDirectory"].setValue( self.temporaryDirectory() + "/testJobDirectory" )
		dispatcher["framesMode"].setValue( Gaffer.Dispatcher.FramesMode.CurrentFrame )
		dispatcher["executeInBackground"].setValue( False )

		dispatcher.dispatch( [ s["wedge"] ] )

		hidden = GafferImage.ImageReader()
		hidden["fileName"].setValue( self.temporaryDirectory() + "/hidden.tif" )

		visible = GafferImage.ImageReader()
		visible["fileName"].setValue( self.temporaryDirectory() + "/visible.tif" )

		hiddenStats = GafferImage.ImageStats()
		hiddenStats["in"].setInput( hidden["out"] )
		hiddenStats['regionOfInterest'].setValue( IECore.Box2i( IECore.V2i( 0, 0 ), IECore.V2i( 640, 480 ) ) )

		visibleStats = GafferImage.ImageStats()
		visibleStats["in"].setInput( visible["out"] )
		visibleStats['regionOfInterest'].setValue( IECore.Box2i( IECore.V2i( 0, 0 ), IECore.V2i( 640, 480 ) ) )

		self.assertLess( hiddenStats["average"].getValue()[0], 0.05 )
		self.assertGreater( visibleStats["average"].getValue()[0], .35 )

	def testPreWorldRenderables( self ):

		s = Gaffer.ScriptNode()

		s["g"] = GafferSceneTest.CompoundObjectSource()
		s["g"]["in"].setValue(
			IECore.CompoundObject( {
				"bound" : IECore.Box3fData( IECore.Box3f() ),
				"globals" : {
					"option:user:blah" : IECore.ClippingPlane(),
				},
			} )
		)

		s["r"] = GafferRenderMan.RenderManRender()
		s["r"]["mode"].setValue( "generate" )
		s["r"]["ribFileName"].setValue( self.temporaryDirectory() + "/test.rib" )
		s["r"]["in"].setInput( s["g"]["out"] )

		s["r"].execute()

		# node should have inserted a ClippingPlane into the rib by putting it
		# in the options:
		rib = "\n".join( file( self.temporaryDirectory() + "/test.rib" ).readlines() )
		self.assertTrue( "ClippingPlane" in rib )

if __name__ == "__main__":
	unittest.main()
