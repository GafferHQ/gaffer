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

import time
import inspect
import unittest
import imath

import IECore
import IECoreScene
import IECoreImage

import Gaffer
import GafferTest
import GafferImage
import GafferScene
import GafferSceneTest

# Note that this is for testing subclasses of GafferScene.Preview.InteractiveRender
# rather than GafferScene.InteractiveRender, which we hope to phase out.
class InteractiveRenderTest( GafferSceneTest.SceneTestCase ) :

	# Derived classes should set cls.interactiveRenderNodeClass to
	# the class of their interactive render node
	interactiveRenderNodeClass = None

	@classmethod
	def setUpClass( cls ) :

		GafferSceneTest.SceneTestCase.setUpClass()

		if cls is InteractiveRenderTest :
			# The InteractiveRenderTest class is a base class to
			# derive from when wanting to test specific InteractiveRender
			# subclasses - on its own it has no renderer so can't
			# test anything.
			raise unittest.SkipTest( "No renderer available" )

	def run( self, result = None ) :

		# InteractiveRender uses `callOnUIThread()` to handle messages, and the Display/Catalogue
		# nodes use it for handling image updates, so we must install a handler.
		# Note : The handler defers processing of calls until exit, unless `assertCalled()`
		# or `waitFor()` is explicitly called.
		with GafferTest.ParallelAlgoTest.UIThreadCallHandler() as self.uiThreadCallHandler :

			GafferSceneTest.SceneTestCase.run( self, result )

		self.uiThreadCallHandler = None

		# See https://docs.python.org/3/library/unittest.html#unittest.TestCase.run
		return result

	def testOutputs( self ):

		s = Gaffer.ScriptNode()
		s["s"] = GafferScene.Sphere()

		s["o"] = GafferScene.Outputs()
		s["o"].addOutput(
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
		s["o"]["in"].setInput( s["s"]["out"] )

		s["r"] = self._createInteractiveRender()
		s["r"]["in"].setInput( s["o"]["out"] )

		s["r"]["state"].setValue( s["r"].State.Running )

		time.sleep( 1.0 )

		image = IECoreImage.ImageDisplayDriver.storedImage( "myLovelySphere" )
		self.assertTrue( isinstance( image, IECoreImage.ImagePrimitive ) )

	def testMetadata( self ) :

		s = Gaffer.ScriptNode()
		s["variables"].addChild( Gaffer.NameValuePlug( "a", "A", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )

		s["s"] = GafferScene.Sphere()

		s["o"] = GafferScene.Outputs()
		s["o"].addOutput(
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
		s["o"]["in"].setInput( s["s"]["out"] )

		s["r"] = self._createInteractiveRender()
		s["r"]["in"].setInput( s["o"]["out"] )

		s["r"]["state"].setValue( s["r"].State.Running )

		time.sleep( 1.0 )

		image = IECoreImage.ImageDisplayDriver.storedImage( "myLovelySphere" )
		headers = image.blindData()
		self.assertEqual( headers["gaffer:version"], IECore.StringData( Gaffer.About.versionString() ) )
		self.assertEqual( headers["gaffer:sourceScene"], IECore.StringData( "r.__adaptedIn" ) )
		self.assertEqual( headers["gaffer:context:a"], IECore.StringData( "A" ) )

	def testAddAndRemoveOutput( self ):

		s = Gaffer.ScriptNode()
		s["s"] = GafferScene.Sphere()

		s["o"] = GafferScene.Outputs()

		s["o"].addOutput(
			"beauty1",
			IECoreScene.Output(
				"test1",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ImageDisplayDriver",
					"handle" : "myLovelySphere1",
				}
			)
		)
		s["o"]["in"].setInput( s["s"]["out"] )

		s["r"] = self._createInteractiveRender()
		s["r"]["in"].setInput( s["o"]["out"] )

		s["r"]["state"].setValue( s["r"].State.Running )

		time.sleep( 1.0 )

		# Check we have our first image, but not a second one.

		self.assertTrue( isinstance( IECoreImage.ImageDisplayDriver.storedImage( "myLovelySphere1" ), IECoreImage.ImagePrimitive ) )
		self.assertTrue( IECoreImage.ImageDisplayDriver.storedImage( "myLovelySphere2" ) is None )

		# Add a second image and check we can have that too.

		s["o"].addOutput(
			"beauty2",
			IECoreScene.Output(
				"test1",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ImageDisplayDriver",
					"handle" : "myLovelySphere2",
				}
			)
		)

		time.sleep( 1.0 )

		self.assertTrue( isinstance( IECoreImage.ImageDisplayDriver.storedImage( "myLovelySphere1" ), IECoreImage.ImagePrimitive ) )
		self.assertTrue( isinstance( IECoreImage.ImageDisplayDriver.storedImage( "myLovelySphere2" ), IECoreImage.ImagePrimitive ) )

		# Remove the second image and check that it stops updating.

		IECoreImage.ImageDisplayDriver.removeStoredImage( "myLovelySphere2" )
		s["o"]["outputs"][1]["active"].setValue( False )

		time.sleep( 1.0 )

		self.assertTrue( IECoreImage.ImageDisplayDriver.storedImage( "myLovelySphere2" ) is None )

		# Add a third image and check we can have that too.

		s["o"].addOutput(
			"beauty3",
			IECoreScene.Output(
				"test1",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ImageDisplayDriver",
					"handle" : "myLovelySphere3",
				}
			)
		)

		time.sleep( 1.0 )

		self.assertTrue( isinstance( IECoreImage.ImageDisplayDriver.storedImage( "myLovelySphere1" ), IECoreImage.ImagePrimitive ) )
		self.assertTrue( IECoreImage.ImageDisplayDriver.storedImage( "myLovelySphere2" ) is None )
		self.assertTrue( isinstance( IECoreImage.ImageDisplayDriver.storedImage( "myLovelySphere3" ), IECoreImage.ImagePrimitive ) )

	def testAddAndRemoveLocation( self ) :

		s = Gaffer.ScriptNode()
		s["catalogue"] = GafferImage.Catalogue()

		s["s"] = GafferScene.Sphere()

		s["o"] = GafferScene.Outputs()
		s["o"].addOutput(
			"beauty",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ClientDisplayDriver",
					"displayHost" : "localhost",
					"displayPort" : str( s['catalogue'].displayDriverServer().portNumber() ),
					"remoteDisplayType" : "GafferImage::GafferDisplayDriver",
				}
			)
		)
		s["o"]["in"].setInput( s["s"]["out"] )

		s["r"] = self._createInteractiveRender()
		s["r"]["in"].setInput( s["o"]["out"] )

		s["r"]["state"].setValue( s["r"].State.Running )

		self.uiThreadCallHandler.waitFor( 1.0 )

		self.assertAlmostEqual( self._color4fAtUV( s["catalogue"], imath.V2f( 0.5 ) ).r, 1, delta = 0.01 )

		s["s"]["enabled"].setValue( False )
		self.uiThreadCallHandler.waitFor( 1.0 )

		self.assertAlmostEqual( self._color4fAtUV( s["catalogue"], imath.V2f( 0.5 ) ).r, 0, delta = 0.01 )

		s["s"]["enabled"].setValue( True )
		self.uiThreadCallHandler.waitFor( 1.0 )

		self.assertAlmostEqual( self._color4fAtUV( s["catalogue"], imath.V2f( 0.5 ) ).r, 1, delta = 0.01 )

		s["r"]["state"].setValue( s["r"].State.Stopped )

	def testAddAndRemoveObject( self ) :

		s = Gaffer.ScriptNode()
		s["catalogue"] = GafferImage.Catalogue()

		# Switch between a sphere and a group, so
		# we can keep the hierarchy the same ( "/thing" )
		# but add and remove the sphere from the location.

		s["s"] = GafferScene.Sphere()
		s["s"]["name"].setValue( "thing" )

		s["g"] = GafferScene.Group()
		s["g"]["name"].setValue( "thing" )

		s["switch"] = Gaffer.Switch()
		s["switch"].setup( GafferScene.ScenePlug() )
		s["switch"]["in"][0].setInput( s["s"]["out"] )
		s["switch"]["in"][1].setInput( s["g"]["out"] )

		s["o"] = GafferScene.Outputs()
		s["o"].addOutput(
			"beauty",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ClientDisplayDriver",
					"displayHost" : "localhost",
					"displayPort" : str( s['catalogue'].displayDriverServer().portNumber() ),
					"remoteDisplayType" : "GafferImage::GafferDisplayDriver",
				}
			)
		)
		s["o"]["in"].setInput( s["switch"]["out"] )

		s["r"] = self._createInteractiveRender()
		s["r"]["in"].setInput( s["o"]["out"] )

		# Render the sphere.

		s["r"]["state"].setValue( s["r"].State.Running )
		self.uiThreadCallHandler.waitFor( 1.0 )

		self.assertAlmostEqual( self._color4fAtUV( s["catalogue"], imath.V2f( 0.5 ) ).r, 1, delta = 0.01 )

		# Switch to the empty group.

		s["switch"]["index"].setValue( 1 )
		self.uiThreadCallHandler.waitFor( 1.0 )

		self.assertAlmostEqual( self._color4fAtUV( s["catalogue"], imath.V2f( 0.5 ) ).r, 0, delta = 0.01 )

		# Switch back to the sphere.

		s["switch"]["index"].setValue( 0 )
		self.uiThreadCallHandler.waitFor( 1.0 )

		self.assertAlmostEqual( self._color4fAtUV( s["catalogue"], imath.V2f( 0.5 ) ).r, 1, delta = 0.01 )

		s["r"]["state"].setValue( s["r"].State.Stopped )

	def testEditObjectVisibility( self ) :

		s = Gaffer.ScriptNode()
		s["catalogue"] = GafferImage.Catalogue()
		s["s"] = GafferScene.Sphere()

		s["g"] = GafferScene.Group()
		s["g"]["in"][0].setInput( s["s"]["out"] )

		s["f"] = GafferScene.PathFilter()

		s["a"] = GafferScene.StandardAttributes()
		s["a"]["in"].setInput( s["g"]["out"] )
		s["a"]["filter"].setInput( s["f"]["out"] )
		s["a"]["attributes"]["visibility"]["enabled"].setValue( True )

		s["o"] = GafferScene.Outputs()
		s["o"].addOutput(
			"beauty",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ClientDisplayDriver",
					"displayHost" : "localhost",
					"displayPort" : str( s['catalogue'].displayDriverServer().portNumber() ),
					"remoteDisplayType" : "GafferImage::GafferDisplayDriver",
				}
			)
		)
		s["o"]["in"].setInput( s["a"]["out"] )

		s["r"] = self._createInteractiveRender()
		s["r"]["in"].setInput( s["o"]["out"] )

		s["r"]["state"].setValue( s["r"].State.Running )

		self.uiThreadCallHandler.waitFor( 1.0 )

		# Visible to start with

		self.assertAlmostEqual( self._color4fAtUV( s["catalogue"], imath.V2f( 0.5 ) ).r, 1, delta = 0.01 )

		# Hide /group/sphere

		s["f"]["paths"].setValue( IECore.StringVectorData( [ "/group/sphere" ] ) )
		s["a"]["attributes"]["visibility"]["value"].setValue( False )
		self.uiThreadCallHandler.waitFor( 1.0 )

		self.assertAlmostEqual( self._color4fAtUV( s["catalogue"], imath.V2f( 0.5 ) ).r, 0, delta = 0.01 )

		# Tweak the sphere geometry - it should remain hidden

		s["s"]["radius"].setValue( 1.01 )
		self.uiThreadCallHandler.waitFor( 1.0 )

		self.assertAlmostEqual( self._color4fAtUV( s["catalogue"], imath.V2f( 0.5 ) ).r, 0, delta = 0.01 )

		# Show it again

		s["a"]["attributes"]["visibility"]["value"].setValue( True )
		self.uiThreadCallHandler.waitFor( 1.0 )

		self.assertAlmostEqual( self._color4fAtUV( s["catalogue"], imath.V2f( 0.5 ) ).r, 1, delta = 0.01 )

		# Hide /group

		s["f"]["paths"].setValue( IECore.StringVectorData( [ "/group" ] ) )
		s["a"]["attributes"]["visibility"]["value"].setValue( False )
		self.uiThreadCallHandler.waitFor( 1.0 )

		self.assertAlmostEqual( self._color4fAtUV( s["catalogue"], imath.V2f( 0.5 ) ).r, 0, delta = 0.01 )

		# Show it again

		s["a"]["attributes"]["visibility"]["value"].setValue( True )
		self.uiThreadCallHandler.waitFor( 1.0 )

		self.assertAlmostEqual( self._color4fAtUV( s["catalogue"], imath.V2f( 0.5 ) ).r, 1, delta = 0.01 )

		s["r"]["state"].setValue( s["r"].State.Stopped )

	def testEditCameraVisibility( self ) :

		s = Gaffer.ScriptNode()
		s["catalogue"] = GafferImage.Catalogue()
		s["s"] = GafferScene.Sphere()

		s["g"] = GafferScene.Group()
		s["g"]["in"][0].setInput( s["s"]["out"] )

		s["f"] = GafferScene.PathFilter()

		s["a"] = GafferScene.CustomAttributes()
		s["a"]["in"].setInput( s["g"]["out"] )
		s["a"]["filter"].setInput( s["f"]["out"] )
		visibilityPlug = Gaffer.NameValuePlug( self._cameraVisibilityAttribute(), False )
		s["a"]["attributes"].addChild( visibilityPlug )

		s["o"] = GafferScene.Outputs()
		s["o"].addOutput(
			"beauty",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ClientDisplayDriver",
					"displayHost" : "localhost",
					"displayPort" : str( s['catalogue'].displayDriverServer().portNumber() ),
					"remoteDisplayType" : "GafferImage::GafferDisplayDriver",
				}
			)
		)
		s["o"]["in"].setInput( s["a"]["out"] )

		s["r"] = self._createInteractiveRender()
		s["r"]["in"].setInput( s["o"]["out"] )

		s["r"]["state"].setValue( s["r"].State.Running )

		self.uiThreadCallHandler.waitFor( 1.0 )

		# Visible to start with

		self.assertAlmostEqual( self._color4fAtUV( s["catalogue"], imath.V2f( 0.5 ) ).r, 1, delta = 0.01 )

		# Hide /group/sphere

		s["f"]["paths"].setValue( IECore.StringVectorData( [ "/group/sphere" ] ) )
		visibilityPlug["value"].setValue( False )
		self.uiThreadCallHandler.waitFor( 1.0 )

		self.assertAlmostEqual( self._color4fAtUV( s["catalogue"], imath.V2f( 0.5 ) ).r, 0, delta = 0.01 )

		# Show it again

		visibilityPlug["value"].setValue( True )
		self.uiThreadCallHandler.waitFor( 1.0 )

		self.assertAlmostEqual( self._color4fAtUV( s["catalogue"], imath.V2f( 0.5 ) ).r, 1, delta = 0.01 )

		# Hide /group

		s["f"]["paths"].setValue( IECore.StringVectorData( [ "/group" ] ) )
		visibilityPlug["value"].setValue( False )
		self.uiThreadCallHandler.waitFor( 1.0 )

		self.assertAlmostEqual( self._color4fAtUV( s["catalogue"], imath.V2f( 0.5 ) ).r, 0, delta = 0.01 )

		# Show it again

		visibilityPlug["value"].setValue( True )
		self.uiThreadCallHandler.waitFor( 1.0 )

		self.assertAlmostEqual( self._color4fAtUV( s["catalogue"], imath.V2f( 0.5 ) ).r, 1, delta = 0.01 )

		s["r"]["state"].setValue( s["r"].State.Stopped )

	def testEditObjectTransform( self ) :

		s = Gaffer.ScriptNode()
		s["catalogue"] = GafferImage.Catalogue()
		s["s"] = GafferScene.Sphere()

		s["o"] = GafferScene.Outputs()
		s["o"].addOutput(
			"beauty",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ClientDisplayDriver",
					"displayHost" : "localhost",
					"displayPort" : str( s['catalogue'].displayDriverServer().portNumber() ),
					"remoteDisplayType" : "GafferImage::GafferDisplayDriver",
				}
			)
		)
		s["o"]["in"].setInput( s["s"]["out"] )

		s["r"] = self._createInteractiveRender()
		s["r"]["in"].setInput( s["o"]["out"] )

		s["r"]["state"].setValue( s["r"].State.Running )

		self.uiThreadCallHandler.waitFor( 1.0 )

		# Visible to start with

		self.assertAlmostEqual( self._color4fAtUV( s["catalogue"], imath.V2f( 0.5 ) ).r, 1, delta = 0.01 )

		# Move to one side

		s["s"]["transform"]["translate"]["x"].setValue( 2 )
		self.uiThreadCallHandler.waitFor( 1.0 )

		self.assertAlmostEqual( self._color4fAtUV( s["catalogue"], imath.V2f( 0.5 ) ).r, 0, delta = 0.01 )

		# Move back

		s["s"]["transform"]["translate"]["x"].setValue( 0 )
		self.uiThreadCallHandler.waitFor( 1.0 )

		self.assertAlmostEqual( self._color4fAtUV( s["catalogue"], imath.V2f( 0.5 ) ).r, 1, delta = 0.01 )

		s["r"]["state"].setValue( s["r"].State.Stopped )

	def testShaderEdits( self ) :

		s = Gaffer.ScriptNode()
		s["catalogue"] = GafferImage.Catalogue()
		s["s"] = GafferScene.Sphere()

		s["shader"], colorPlug = self._createConstantShader()
		colorPlug.setValue( imath.Color3f( 1, 0, 0 ) )

		s["a"] = GafferScene.ShaderAssignment()
		s["a"]["in"].setInput( s["s"]["out"] )
		s["a"]["shader"].setInput( s["shader"]["out"] )

		s["o"] = GafferScene.Outputs()
		s["o"].addOutput(
			"beauty",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ClientDisplayDriver",
					"displayHost" : "localhost",
					"displayPort" : str( s['catalogue'].displayDriverServer().portNumber() ),
					"remoteDisplayType" : "GafferImage::GafferDisplayDriver",
				}
			)
		)
		s["o"]["in"].setInput( s["a"]["out"] )

		s["r"] = self._createInteractiveRender()
		s["r"]["in"].setInput( s["o"]["out"] )

		s["r"]["state"].setValue( s["r"].State.Running )

		self.uiThreadCallHandler.waitFor( 2.0 )

		# Render red sphere

		self.__assertColorsAlmostEqual( self._color4fAtUV( s["catalogue"], imath.V2f( 0.5 ) ), imath.Color4f( 1, 0, 0, 1 ), delta = 0.01 )

		# Make it green

		colorPlug.setValue( imath.Color3f( 0, 1, 0 ) )
		self.uiThreadCallHandler.waitFor( 2.0 )

		self.__assertColorsAlmostEqual( self._color4fAtUV( s["catalogue"], imath.V2f( 0.5 ) ), imath.Color4f( 0, 1, 0, 1 ), delta = 0.01 )

		# Make it blue

		colorPlug.setValue( imath.Color3f( 0, 0, 1 ) )
		self.uiThreadCallHandler.waitFor( 2.0 )

		self.__assertColorsAlmostEqual( self._color4fAtUV( s["catalogue"], imath.V2f( 0.5 ) ), imath.Color4f( 0, 0, 1, 1 ), delta = 0.01 )

		s["r"]["state"].setValue( s["r"].State.Stopped )

	def testEditCameraTransform( self ) :

		s = Gaffer.ScriptNode()
		s["catalogue"] = GafferImage.Catalogue()

		s["s"] = GafferScene.Sphere()
		s["c"] = GafferScene.Camera()

		s["g"] = GafferScene.Group()
		s["g"]["in"][0].setInput( s["s"]["out"] )
		s["g"]["in"][1].setInput( s["c"]["out"] )

		s["outputs"] = GafferScene.Outputs()
		s["outputs"].addOutput(
			"beauty",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ClientDisplayDriver",
					"displayHost" : "localhost",
					"displayPort" : str( s['catalogue'].displayDriverServer().portNumber() ),
					"remoteDisplayType" : "GafferImage::GafferDisplayDriver",
				}
			)
		)
		s["outputs"]["in"].setInput( s["g"]["out"] )

		s["options"] = GafferScene.StandardOptions()
		s["options"]["in"].setInput( s["outputs"]["out"] )
		s["options"]["options"]["renderCamera"]["enabled"].setValue( True )
		s["options"]["options"]["renderCamera"]["value"].setValue( "/group/camera" )

		s["r"] = self._createInteractiveRender()
		s["r"]["in"].setInput( s["options"]["out"] )

		s["r"]["state"].setValue( s["r"].State.Running )

		self.uiThreadCallHandler.waitFor( 1.0 )

		# Visible to start with

		self.assertAlmostEqual( self._color4fAtUV( s["catalogue"], imath.V2f( 0.5 ) ).r, 1, delta = 0.01 )

		# Move to one side

		s["c"]["transform"]["translate"]["x"].setValue( 2 )
		self.uiThreadCallHandler.waitFor( 1.0 )

		self.assertAlmostEqual( self._color4fAtUV( s["catalogue"], imath.V2f( 0.5 ) ).r, 0, delta = 0.01 )

		# Move back

		s["c"]["transform"]["translate"]["x"].setValue( 0 )
		self.uiThreadCallHandler.waitFor( 1.0 )

		self.assertAlmostEqual( self._color4fAtUV( s["catalogue"], imath.V2f( 0.5 ) ).r, 1, delta = 0.01 )
		s["r"]["state"].setValue( s["r"].State.Stopped )

	def testEditResolution( self ) :

		s = Gaffer.ScriptNode()

		s["sphere"] = GafferScene.Sphere()
		s["camera"] = GafferScene.Camera()

		s["group"] = GafferScene.Group()
		s["group"]["in"][0].setInput( s["sphere"]["out"] )
		s["group"]["in"][1].setInput( s["camera"]["out"] )

		s["outputs"] = GafferScene.Outputs()
		s["outputs"].addOutput(
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
		s["outputs"]["in"].setInput( s["group"]["out"] )

		s["options"] = GafferScene.StandardOptions()
		s["options"]["in"].setInput( s["outputs"]["out"] )
		s["options"]["options"]["renderCamera"]["enabled"].setValue( True )

		s["r"] = self._createInteractiveRender()
		s["r"]["in"].setInput( s["options"]["out"] )

		s["r"]["state"].setValue( s["r"].State.Running )

		for withDefaultCamera in ( True, False ) :

			s["options"]["options"]["renderCamera"]["value"].setValue(
				"" if withDefaultCamera else "/group/camera"
			)

			time.sleep( 1.0 )

			# Use the default resolution to start with

			self.assertEqual(
				IECoreImage.ImageDisplayDriver.storedImage( "myLovelySphere" ).displayWindow,
				imath.Box2i( imath.V2i( 0 ), imath.V2i( 639, 479 ) )
			)

			# Now specify a resolution

			s["options"]["options"]["renderResolution"]["enabled"].setValue( True )
			s["options"]["options"]["renderResolution"]["value"].setValue( imath.V2i( 200, 100 ) )

			time.sleep( 1.0 )

			self.assertEqual(
				IECoreImage.ImageDisplayDriver.storedImage( "myLovelySphere" ).displayWindow,
				imath.Box2i( imath.V2i( 0 ), imath.V2i( 199, 99 ) )
			)

			# And specify another resolution

			s["options"]["options"]["renderResolution"]["value"].setValue( imath.V2i( 300, 100 ) )

			time.sleep( 1.0 )

			self.assertEqual(
				IECoreImage.ImageDisplayDriver.storedImage( "myLovelySphere" ).displayWindow,
				imath.Box2i( imath.V2i( 0 ), imath.V2i( 299, 99 ) )
			)

			# And back to the default

			s["options"]["options"]["renderResolution"]["enabled"].setValue( False )

			time.sleep( 1.0 )

			self.assertEqual(
				IECoreImage.ImageDisplayDriver.storedImage( "myLovelySphere" ).displayWindow,
				imath.Box2i( imath.V2i( 0 ), imath.V2i( 639, 479 ) )
			)

	def testDeleteWhilePaused( self ) :

		s = Gaffer.ScriptNode()

		s["p"] = GafferScene.Plane()

		s["c"] = GafferScene.Camera()
		s["c"]["transform"]["translate"]["z"].setValue( 1 )

		s["g"] = GafferScene.Group()
		s["g"]["in"][0].setInput( s["p"]["out"] )
		s["g"]["in"][1].setInput( s["c"]["out"] )

		s["d"] = GafferScene.Outputs()
		s["d"].addOutput(
			"beauty",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"quantize" : IECore.IntVectorData( [ 0, 0, 0, 0 ] ),
					"driverType" : "ImageDisplayDriver",
					"handle" : "myLovelyPlane",
				}
			)
		)
		s["d"]["in"].setInput( s["g"]["out"] )

		s["o"] = GafferScene.StandardOptions()
		s["o"]["options"]["renderCamera"]["value"].setValue( "/group/camera" )
		s["o"]["options"]["renderCamera"]["enabled"].setValue( True )
		s["o"]["in"].setInput( s["d"]["out"] )

		s["r"] = self._createInteractiveRender()
		s["r"]["in"].setInput( s["o"]["out"] )

		# Start a render, give it time to get going, then pause it.
		s["r"]["state"].setValue( s["r"].State.Running )
		time.sleep( 2 )
		s["r"]["state"].setValue( s["r"].State.Paused )

		# Delete everything, and check that we don't hang.
		del s

	def testChangeInputWhilePaused( self ) :

		s = Gaffer.ScriptNode()

		s["p"] = GafferScene.Plane()

		s["c"] = GafferScene.Camera()
		s["c"]["transform"]["translate"]["z"].setValue( 1 )

		s["g"] = GafferScene.Group()
		s["g"]["in"][0].setInput( s["p"]["out"] )
		s["g"]["in"][1].setInput( s["c"]["out"] )

		s["d"] = GafferScene.Outputs()
		s["d"].addOutput(
			"beauty",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ImageDisplayDriver",
					"handle" : "subdivisionTest",
					"quantize" : IECore.IntVectorData( [ 0, 0, 0, 0 ] ),
				}
			)
		)
		s["d"]["in"].setInput( s["g"]["out"] )

		s["o"] = GafferScene.StandardOptions()
		s["o"]["options"]["renderCamera"]["value"].setValue( "/group/camera" )
		s["o"]["options"]["renderCamera"]["enabled"].setValue( True )
		s["o"]["in"].setInput( s["d"]["out"] )

		s["r"] = self._createInteractiveRender()
		s["r"]["in"].setInput( s["o"]["out"] )

		# Start a render, give it time to get going, then pause it.

		s["r"]["state"].setValue( s["r"].State.Running )
		time.sleep( 2 )
		s["r"]["state"].setValue( s["r"].State.Paused )

		# Change the input to the render node, and check that we don't hang.

		s["o2"] = GafferScene.StandardOptions()
		s["o2"]["in"].setInput( s["o"]["out"] )

		s["r"]["in"].setInput( s["o2"]["out"] )

		# Start the render again, so we know we're not just testing
		# the same thing as testDeleteWhilePaused().
		s["r"]["state"].setValue( s["r"].State.Running )

	def testEditContext( self ) :

		s = Gaffer.ScriptNode()
		s["catalogue"] = GafferImage.Catalogue()
		s["s"] = GafferScene.Sphere()

		# Sphere moves with time.
		s["e"] = Gaffer.Expression()
		s["e"].setExpression( """parent["s"]["transform"]["translate"]["x"] = context.getFrame() - 1""" )

		s["o"] = GafferScene.Outputs()
		s["o"].addOutput(
			"beauty",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ClientDisplayDriver",
					"displayHost" : "localhost",
					"displayPort" : str( s['catalogue'].displayDriverServer().portNumber() ),
					"remoteDisplayType" : "GafferImage::GafferDisplayDriver",
				}
			)
		)
		s["o"]["in"].setInput( s["s"]["out"] )

		s["r"] = self._createInteractiveRender()
		s["r"]["in"].setInput( s["o"]["out"] )

		s["r"]["state"].setValue( s["r"].State.Running )

		self.uiThreadCallHandler.waitFor( 1.0 )

		# Visible to start with

		self.assertAlmostEqual( self._color4fAtUV( s["catalogue"], imath.V2f( 0.5 ) ).r, 1, delta = 0.01 )

		# Move to one side

		s.context().setFrame( 3 )
		self.uiThreadCallHandler.waitFor( 1.0 )

		self.assertAlmostEqual( self._color4fAtUV( s["catalogue"], imath.V2f( 0.5 ) ).r, 0, delta = 0.01 )

		# Move back

		s.context().setFrame( 1 )
		self.uiThreadCallHandler.waitFor( 1.0 )

		self.assertAlmostEqual( self._color4fAtUV( s["catalogue"], imath.V2f( 0.5 ) ).r, 1, delta = 0.01 )

		# Repeat, using a context we set directly ourselves.

		c = Gaffer.Context()
		c.setFrame( 3 )
		s["r"].setContext( c )
		self.uiThreadCallHandler.waitFor( 1.0 )

		self.assertAlmostEqual( self._color4fAtUV( s["catalogue"], imath.V2f( 0.5 ) ).r, 0, delta = 0.01 )

		c.setFrame( 1 )
		self.uiThreadCallHandler.waitFor( 1.0 )

		self.assertAlmostEqual( self._color4fAtUV( s["catalogue"], imath.V2f( 0.5 ) ).r, 1, delta = 0.01 )

		s["r"]["state"].setValue( s["r"].State.Stopped )

	def testLights( self ) :

		s = Gaffer.ScriptNode()
		s["catalogue"] = GafferImage.Catalogue()

		s["l"], colorPlug = self._createPointLight()
		colorPlug.setValue( imath.Color3f( 1, 0.5, 0.25 ) )
		s["l"]["transform"]["translate"]["z"].setValue( 1 )

		s["p"] = GafferScene.Plane()

		s["c"] = GafferScene.Camera()
		s["c"]["transform"]["translate"]["z"].setValue( 1 )

		s["g"] = GafferScene.Group()
		s["g"]["in"][0].setInput( s["l"]["out"] )
		s["g"]["in"][1].setInput( s["p"]["out"] )
		s["g"]["in"][2].setInput( s["c"]["out"] )

		s["s"], unused = self._createMatteShader()
		s["a"] = GafferScene.ShaderAssignment()
		s["a"]["in"].setInput( s["g"]["out"] )
		s["a"]["shader"].setInput( s["s"]["out"] )

		s["d"] = GafferScene.Outputs()
		s["d"].addOutput(
			"beauty",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ClientDisplayDriver",
					"displayHost" : "localhost",
					"displayPort" : str( s['catalogue'].displayDriverServer().portNumber() ),
					"remoteDisplayType" : "GafferImage::GafferDisplayDriver",
					"quantize" : IECore.IntVectorData( [ 0, 0, 0, 0 ] ),
				}
			)
		)
		s["d"]["in"].setInput( s["a"]["out"] )

		s["o"] = GafferScene.StandardOptions()
		s["o"]["options"]["renderCamera"]["value"].setValue( "/group/camera" )
		s["o"]["options"]["renderCamera"]["enabled"].setValue( True )
		s["o"]["in"].setInput( s["d"]["out"] )

		s["r"] = self._createInteractiveRender()
		s["r"]["in"].setInput( s["o"]["out"] )

		# Start a render, give it time to finish, and check the output.

		s["r"]["state"].setValue( s["r"].State.Running )

		self.uiThreadCallHandler.waitFor( 2 )

		c = self._color3fAtUV( s["catalogue"], imath.V2f( 0.5 ) )
		self.assertEqual( c / c[0], imath.Color3f( 1, 0.5, 0.25 ) )

		# Adjust a parameter, give it time to update, and check the output.

		colorPlug.setValue( imath.Color3f( 0.25, 0.5, 1 ) )

		self.uiThreadCallHandler.waitFor( 1 )

		c = self._color3fAtUV( s["catalogue"], imath.V2f( 0.5 ) )
		self.assertEqual( c / c[2], imath.Color3f( 0.25, 0.5, 1 ) )

		# Pause it, adjust a parameter, wait, and check that nothing changed.

		s["r"]["state"].setValue( s["r"].State.Paused )
		colorPlug.setValue( imath.Color3f( 1, 0.5, 0.25 ) )

		self.uiThreadCallHandler.waitFor( 1 )

		c = self._color3fAtUV( s["catalogue"], imath.V2f( 0.5 ) )
		self.assertEqual( c / c[2], imath.Color3f( 0.25, 0.5, 1 ) )

		# Unpause it, wait, and check that the update happened.

		s["r"]["state"].setValue( s["r"].State.Running )
		self.uiThreadCallHandler.waitFor( 1 )

		c = self._color3fAtUV( s["catalogue"], imath.V2f( 0.5 ) )
		self.assertEqual( c / c[0], imath.Color3f( 1, 0.5, 0.25 ) )

		# Stop the render, tweak a parameter and check that nothing happened.

		s["r"]["state"].setValue( s["r"].State.Stopped )
		colorPlug.setValue( imath.Color3f( 0.25, 0.5, 1 ) )
		self.uiThreadCallHandler.waitFor( 1 )

		c = self._color3fAtUV( s["catalogue"], imath.V2f( 0.5 ) )
		self.assertEqual( c / c[0], imath.Color3f( 1, 0.5, 0.25 ) )

		s["r"]["state"].setValue( s["r"].State.Stopped )

	def testAddLight( self ) :

		s = Gaffer.ScriptNode()
		s["catalogue"] = GafferImage.Catalogue()

		s["l"], colorPlug = self._createPointLight()
		colorPlug.setValue( imath.Color3f( 1, 0, 0 ) )
		s["l"]["transform"]["translate"]["z"].setValue( 1 )

		s["p"] = GafferScene.Plane()

		s["c"] = GafferScene.Camera()
		s["c"]["transform"]["translate"]["z"].setValue( 1 )

		s["g"] = GafferScene.Group()
		s["g"]["in"][0].setInput( s["l"]["out"] )
		s["g"]["in"][1].setInput( s["p"]["out"] )
		s["g"]["in"][2].setInput( s["c"]["out"] )

		s["s"], unused = self._createMatteShader()
		s["a"] = GafferScene.ShaderAssignment()
		s["a"]["in"].setInput( s["g"]["out"] )
		s["a"]["shader"].setInput( s["s"]["out"] )

		s["d"] = GafferScene.Outputs()
		s["d"].addOutput(
			"beauty",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ClientDisplayDriver",
					"displayHost" : "localhost",
					"displayPort" : str( s['catalogue'].displayDriverServer().portNumber() ),
					"remoteDisplayType" : "GafferImage::GafferDisplayDriver",
					"quantize" : IECore.IntVectorData( [ 0, 0, 0, 0 ] ),
				}
			)
		)
		s["d"]["in"].setInput( s["a"]["out"] )

		s["o"] = GafferScene.StandardOptions()
		s["o"]["options"]["renderCamera"]["value"].setValue( "/group/camera" )
		s["o"]["options"]["renderCamera"]["enabled"].setValue( True )
		s["o"]["in"].setInput( s["d"]["out"] )

		s["ro"] = self._createOptions()
		s["ro"]["in"].setInput( s["o"]["out"] )

		s["r"] = self._createInteractiveRender()
		s["r"]["in"].setInput( s["ro"]["out"] )

		# Start a render, give it time to finish, and check the output.

		s["r"]["state"].setValue( s["r"].State.Running )

		self.uiThreadCallHandler.waitFor( 2 )

		c = self._color3fAtUV( s["catalogue"], imath.V2f( 0.5 ) )
		self.assertEqual( c / c[0], imath.Color3f( 1, 0, 0 ) )

		# Add a light

		s["l2"], colorPlug = self._createPointLight()
		colorPlug.setValue( imath.Color3f( 0, 1, 0 ) )
		s["l2"]["transform"]["translate"]["z"].setValue( 1 )

		s["g"]["in"][3].setInput( s["l2"]["out"] )

		# Give it time to update, and check the output.

		self.uiThreadCallHandler.waitFor( 2 )

		c = self._color3fAtUV( s["catalogue"], imath.V2f( 0.5 ) )
		# Tolerance is high due to sampling noise in Cycles, but is more than sufficient to
		# be sure that the new light has been added (otherwise there would be no green at all).
		self.assertTrue( ( c / c[0] ).equalWithAbsError( imath.Color3f( 1, 1, 0 ), 0.2 ) )

		s["r"]["state"].setValue( s["r"].State.Stopped )

	def testRemoveLight( self ) :

		s = Gaffer.ScriptNode()
		s["catalogue"] = GafferImage.Catalogue()

		s["l"], unused = self._createPointLight()
		s["l"]["transform"]["translate"]["z"].setValue( 1 )

		s["p"] = GafferScene.Plane()

		s["c"] = GafferScene.Camera()
		s["c"]["transform"]["translate"]["z"].setValue( 1 )

		s["g"] = GafferScene.Group()
		s["g"]["in"][0].setInput( s["l"]["out"] )
		s["g"]["in"][1].setInput( s["p"]["out"] )
		s["g"]["in"][2].setInput( s["c"]["out"] )

		s["s"], unused = self._createMatteShader()
		s["a"] = GafferScene.ShaderAssignment()
		s["a"]["in"].setInput( s["g"]["out"] )
		s["a"]["shader"].setInput( s["s"]["out"] )

		s["d"] = GafferScene.Outputs()
		s["d"].addOutput(
			"beauty",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ClientDisplayDriver",
					"displayHost" : "localhost",
					"displayPort" : str( s['catalogue'].displayDriverServer().portNumber() ),
					"remoteDisplayType" : "GafferImage::GafferDisplayDriver",
					"quantize" : IECore.IntVectorData( [ 0, 0, 0, 0 ] ),
				}
			)
		)
		s["d"]["in"].setInput( s["a"]["out"] )

		s["o"] = GafferScene.StandardOptions()
		s["o"]["options"]["renderCamera"]["value"].setValue( "/group/camera" )
		s["o"]["options"]["renderCamera"]["enabled"].setValue( True )
		s["o"]["in"].setInput( s["d"]["out"] )

		s["r"] = self._createInteractiveRender()
		s["r"]["in"].setInput( s["o"]["out"] )

		# Start a render, give it time to finish, and check the output.

		s["r"]["state"].setValue( s["r"].State.Running )

		self.uiThreadCallHandler.waitFor( 2 )

		c = self._color3fAtUV( s["catalogue"], imath.V2f( 0.5 ) )
		self.assertNotEqual( c[0], 0.0 )

		# Remove the light by disabling it.

		s["l"]["enabled"].setValue( False )
		self.uiThreadCallHandler.waitFor( 2 )

		c = self._color3fAtUV( s["catalogue"], imath.V2f( 0.5 ) )
		self.assertEqual( c[0], 0.0 )

		# Enable it again.

		s["l"]["enabled"].setValue( True )
		self.uiThreadCallHandler.waitFor( 2 )

		c = self._color3fAtUV( s["catalogue"], imath.V2f( 0.5 ) )
		self.assertNotEqual( c[0], 0.0 )

		s["r"]["state"].setValue( s["r"].State.Stopped )

	def testHideLight( self ) :

		s = Gaffer.ScriptNode()
		s["catalogue"] = GafferImage.Catalogue()

		s["l"], unused = self._createPointLight()
		s["l"]["transform"]["translate"]["z"].setValue( 1 )

		s["v"] = GafferScene.StandardAttributes()
		s["v"]["attributes"]["visibility"]["enabled"].setValue( True )
		s["v"]["in"].setInput( s["l"]["out"] )

		s["p"] = GafferScene.Plane()

		s["c"] = GafferScene.Camera()
		s["c"]["transform"]["translate"]["z"].setValue( 1 )

		s["g"] = GafferScene.Group()
		s["g"]["in"][0].setInput( s["v"]["out"] )
		s["g"]["in"][1].setInput( s["p"]["out"] )
		s["g"]["in"][2].setInput( s["c"]["out"] )

		s["s"], unused = self._createMatteShader()
		s["a"] = GafferScene.ShaderAssignment()
		s["a"]["in"].setInput( s["g"]["out"] )
		s["a"]["shader"].setInput( s["s"]["out"] )

		s["d"] = GafferScene.Outputs()
		s["d"].addOutput(
			"beauty",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ClientDisplayDriver",
					"displayHost" : "localhost",
					"displayPort" : str( s['catalogue'].displayDriverServer().portNumber() ),
					"remoteDisplayType" : "GafferImage::GafferDisplayDriver",
					"quantize" : IECore.IntVectorData( [ 0, 0, 0, 0 ] ),
				}
			)
		)
		s["d"]["in"].setInput( s["a"]["out"] )

		s["o"] = GafferScene.StandardOptions()
		s["o"]["options"]["renderCamera"]["value"].setValue( "/group/camera" )
		s["o"]["options"]["renderCamera"]["enabled"].setValue( True )
		s["o"]["in"].setInput( s["d"]["out"] )

		s["r"] = self._createInteractiveRender()
		s["r"]["in"].setInput( s["o"]["out"] )

		# Start a render, give it time to finish, and check the output.

		s["r"]["state"].setValue( s["r"].State.Running )

		self.uiThreadCallHandler.waitFor( 2 )

		c = self._color3fAtUV( s["catalogue"], imath.V2f( 0.5 ) )
		self.assertNotEqual( c[0], 0.0 )

		# Remove the light by hiding it.

		s["v"]["attributes"]["visibility"]["value"].setValue( False )
		self.uiThreadCallHandler.waitFor( 2 )

		c = self._color3fAtUV( s["catalogue"], imath.V2f( 0.5 ) )
		self.assertEqual( c[0], 0.0 )

		# Put the light back by showing it.

		s["v"]["attributes"]["visibility"]["value"].setValue( True )
		self.uiThreadCallHandler.waitFor( 2 )

		c = self._color3fAtUV( s["catalogue"], imath.V2f( 0.5 ) )

		self.assertNotEqual( c[0], 0.0 )

		s["r"]["state"].setValue( s["r"].State.Stopped )

	def testGlobalAttributes( self ) :

		s = Gaffer.ScriptNode()
		s["catalogue"] = GafferImage.Catalogue()
		s["s"] = GafferScene.Sphere()

		s["g"] = GafferScene.Group()
		s["g"]["in"][0].setInput( s["s"]["out"] )

		s["a"] = GafferScene.StandardAttributes()
		s["a"]["in"].setInput( s["g"]["out"] )
		s["a"]["global"].setValue( True )
		s["a"]["attributes"]["visibility"]["enabled"].setValue( True )

		s["o"] = GafferScene.Outputs()
		s["o"].addOutput(
			"beauty",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ClientDisplayDriver",
					"displayHost" : "localhost",
					"displayPort" : str( s['catalogue'].displayDriverServer().portNumber() ),
					"remoteDisplayType" : "GafferImage::GafferDisplayDriver",
				}
			)
		)
		s["o"]["in"].setInput( s["a"]["out"] )

		s["r"] = self._createInteractiveRender()
		s["r"]["in"].setInput( s["o"]["out"] )

		s["r"]["state"].setValue( s["r"].State.Running )

		self.uiThreadCallHandler.waitFor( 1.0 )

		# Visible to start with

		self.assertAlmostEqual( self._color4fAtUV( s["catalogue"], imath.V2f( 0.5 ) ).r, 1, delta = 0.01 )

		# Hide

		s["a"]["attributes"]["visibility"]["value"].setValue( False )
		self.uiThreadCallHandler.waitFor( 1.0 )

		self.assertAlmostEqual( self._color4fAtUV( s["catalogue"], imath.V2f( 0.5 ) ).r, 0, delta = 0.01 )

		# Show again

		s["a"]["attributes"]["visibility"]["value"].setValue( True )
		self.uiThreadCallHandler.waitFor( 1.0 )

		self.assertAlmostEqual( self._color4fAtUV( s["catalogue"], imath.V2f( 0.5 ) ).r, 1, delta = 0.01 )

		s["r"]["state"].setValue( s["r"].State.Stopped )

	def testGlobalCameraVisibility( self ) :

		s = Gaffer.ScriptNode()
		s["catalogue"] = GafferImage.Catalogue()
		s["s"] = GafferScene.Sphere()

		s["g"] = GafferScene.Group()
		s["g"]["in"][0].setInput( s["s"]["out"] )

		s["a"] = GafferScene.CustomAttributes()
		s["a"]["in"].setInput( s["g"]["out"] )
		s["a"]["global"].setValue( True )
		visibilityPlug = Gaffer.NameValuePlug( self._cameraVisibilityAttribute(), True )
		s["a"]["attributes"].addChild( visibilityPlug )

		s["o"] = GafferScene.Outputs()
		s["o"].addOutput(
			"beauty",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ClientDisplayDriver",
					"displayHost" : "localhost",
					"displayPort" : str( s['catalogue'].displayDriverServer().portNumber() ),
					"remoteDisplayType" : "GafferImage::GafferDisplayDriver",
				}
			)
		)
		s["o"]["in"].setInput( s["a"]["out"] )

		s["r"] = self._createInteractiveRender()
		s["r"]["in"].setInput( s["o"]["out"] )

		s["r"]["state"].setValue( s["r"].State.Running )

		self.uiThreadCallHandler.waitFor( 1.0 )

		# Visible to start with

		self.assertAlmostEqual( self._color4fAtUV( s["catalogue"], imath.V2f( 0.5 ) ).r, 1, delta = 0.01 )

		# Hide

		visibilityPlug["value"].setValue( False )
		self.uiThreadCallHandler.waitFor( 1.0 )

		self.assertAlmostEqual( self._color4fAtUV( s["catalogue"], imath.V2f( 0.5 ) ).r, 0, delta = 0.01 )

		# Show again

		visibilityPlug["value"].setValue( True )
		self.uiThreadCallHandler.waitFor( 1.0 )

		self.assertAlmostEqual( self._color4fAtUV( s["catalogue"], imath.V2f( 0.5 ) ).r, 1, delta = 0.01 )

		s["r"]["state"].setValue( s["r"].State.Stopped )

	def testEffectiveContext( self ) :

		s = Gaffer.ScriptNode()

		s["s"] = GafferScene.Sphere()
		s["e"] = Gaffer.Expression()
		s["e"].setExpression(
			inspect.cleandoc(
				"""
				assert( context.getFrame() == 10 )
				parent["s"]["radius"] = 1
				"""
			)
		)

		s["o"] = GafferScene.Outputs()
		s["o"].addOutput(
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
		s["o"]["in"].setInput( s["s"]["out"] )

		s["r"] = self._createInteractiveRender()
		s["r"]["in"].setInput( s["o"]["out"] )

		# No override context.
		self.assertEqual( s["r"].getContext(), None )
		# Meaning we should use the script context.
		# Set the frame to 10 to keep the expression happy.
		s.context().setFrame( 10 )

		# Arrange to catch the error the expression will throw
		# if it isn't happy.
		errors = GafferTest.CapturingSlot( s["r"].errorSignal() )

		# Start the render and assert that we're good.
		s["r"]["state"].setValue( s["r"].State.Running )
		time.sleep( 0.25 )
		self.assertEqual( len( errors ), 0 )
		s["r"]["state"].setValue( s["r"].State.Stopped )

		# Now, do the same using an InteractiveRender node
		# created in a box before parenting to the script

		box = Gaffer.Box()
		box["r"] = self._createInteractiveRender()
		self.assertEqual( box["r"].getContext(), None )
		s["b"] = box
		self.assertEqual( box["r"].getContext(), None )
		p = Gaffer.PlugAlgo.promote( box["r"]["in"] )
		p.setInput( s["o"]["out"] )

		errors = GafferTest.CapturingSlot( box["r"].errorSignal() )

		box["r"]["state"].setValue( box["r"].State.Running )
		time.sleep( 0.25 )
		self.assertEqual( len( errors ), 0 )
		box["r"]["state"].setValue( box["r"].State.Stopped )

		# Now, set the wrong frame on the script context,
		# and instead supply our own context with the right frame.

		s.context().setFrame( 1 )
		context = Gaffer.Context()
		context.setFrame( 10 )
		box["r"].setContext( context )
		self.assertTrue( box["r"].getContext().isSame( context ) )

		box["r"]["state"].setValue( box["r"].State.Running )
		time.sleep( 0.25 )
		self.assertEqual( len( errors ), 0 )
		box["r"]["state"].setValue( box["r"].State.Stopped )

	def testTraceSets( self ) :

		s = Gaffer.ScriptNode()
		s["catalogue"] = GafferImage.Catalogue()

		s["reflector"] = GafferScene.Plane()
		s["reflector"]["name"].setValue( "reflector" )
		s["reflector"]["transform"]["translate"].setValue( imath.V3f( 0, 0, -1 ) )

		s["reflected"] = GafferScene.Plane()
		s["reflected"]["name"].setValue( "reflected" )
		s["reflected"]["transform"]["translate"].setValue( imath.V3f( 0, 0, 1 ) )

		s["group"] = GafferScene.Group()
		s["group"]["in"][0].setInput( s["reflector"]["out"] )
		s["group"]["in"][1].setInput( s["reflected"]["out"] )

		s["constant"], constantParameter = self._createConstantShader()
		s["constantAssignment"] = GafferScene.ShaderAssignment()
		s["constantAssignment"]["in"].setInput( s["group"]["out"] )
		s["constantAssignment"]["shader"].setInput( s["constant"]["out"] )

		traceShader, traceSetParameter = self._createTraceSetShader()
		if traceShader is None :
			self.skipTest( "Trace set shader not available" )

		s["traceShader"] = traceShader

		s["traceAssignmentFilter"] = GafferScene.PathFilter()
		s["traceAssignmentFilter"]["paths"].setValue( IECore.StringVectorData( [ "/group/reflector" ] ) )

		s["traceAssignment"] = GafferScene.ShaderAssignment()
		s["traceAssignment"]["in"].setInput( s["constantAssignment"]["out"] )
		s["traceAssignment"]["shader"].setInput( s["traceShader"]["out"] )
		s["traceAssignment"]["filter"].setInput( s["traceAssignmentFilter"]["out"] )

		s["set"] = GafferScene.Set()
		s["set"]["in"].setInput( s["traceAssignment"]["out"] )
		s["set"]["name"].setValue( "render:myTraceSet" )

		s["options"] = GafferScene.CustomOptions()
		s["options"]["in"].setInput( s["set"]["out"] )
		for o in self._traceDepthOptions() :
			s["options"]["options"].addChild( Gaffer.NameValuePlug( o, IECore.IntData( 1 ) ) )

		s["outputs"] = GafferScene.Outputs()
		s["outputs"].addOutput(
			"beauty",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ClientDisplayDriver",
					"displayHost" : "localhost",
					"displayPort" : str( s['catalogue'].displayDriverServer().portNumber() ),
					"remoteDisplayType" : "GafferImage::GafferDisplayDriver",
				}
			)
		)
		s["outputs"]["in"].setInput( s["options"]["out"] )

		s["render"] = self._createInteractiveRender()
		s["render"]["in"].setInput( s["outputs"]["out"] )
		s["render"]["state"].setValue( s["render"].State.Running )

		self.uiThreadCallHandler.waitFor( 1.0 )

		# We haven't used the trace sets yet, so should be able to see
		# the reflection.

		def assertReflected( reflected ) :

			self.assertGreater( self._color4fAtUV( s["catalogue"], imath.V2f( 0.5 ) ).a, 0.9 )
			if reflected :
				self.assertGreater( self._color4fAtUV( s["catalogue"], imath.V2f( 0.5 ) ).r, 0.9 )
			else :
				self.assertLess( self._color4fAtUV( s["catalogue"], imath.V2f( 0.5 ) ).r, 0.1 )

		assertReflected( True )

		# Ask to use a trace set. Reflection should disappear because
		# we haven't added anything to the set.

		traceSetParameter.setValue( "myTraceSet" )
		self.uiThreadCallHandler.waitFor( 1.0 )
		assertReflected( False )

		# Now add the reflected object into the set. Reflection should
		# come back.

		s["set"]["paths"].setValue( IECore.StringVectorData( [ "/group/reflected" ] ) )
		self.uiThreadCallHandler.waitFor( 1.0 )
		assertReflected( True )

		# Rename the set so that it's not a trace set any more. Reflection
		# should disappear.

		s["set"]["name"].setValue( "myTraceSet" )
		self.uiThreadCallHandler.waitFor( 1.0 )
		assertReflected( False )

		# Rename the set so that it is a trace set, but with a different namer.
		# Reflection should not reappear.

		s["set"]["name"].setValue( "render:myOtherTraceSet" )
		self.uiThreadCallHandler.waitFor( 1.0 )
		assertReflected( False )

		# Update the shader to use this new trace set. Reflection should
		# reappear.

		traceSetParameter.setValue( "myOtherTraceSet" )
		self.uiThreadCallHandler.waitFor( 1.0 )
		assertReflected( True )

		s["render"]["state"].setValue( s["render"].State.Stopped )

	def testRendererContextVariable( self ):

		s = Gaffer.ScriptNode()
		s["s"] = GafferScene.Sphere()

		s["o"] = GafferScene.Outputs()
		s["o"].addOutput(
			"beauty",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ImageDisplayDriver",
					"handle" : "myLovelySphereRenderedIn${scene:renderer}",
				}
			)
		)
		s["o"]["in"].setInput( s["s"]["out"] )

		s["r"] = self._createInteractiveRender()
		s["r"]["in"].setInput( s["o"]["out"] )

		s["r"]["state"].setValue( s["r"].State.Running )

		time.sleep( 1.0 )

		renderer = s["r"]["renderer"].getValue() if "renderer" in s["r"] else s["r"]["__renderer"].getValue()
		image = IECoreImage.ImageDisplayDriver.storedImage( "myLovelySphereRenderedIn" + renderer )
		self.assertTrue( isinstance( image, IECoreImage.ImagePrimitive ) )

	def testLightFilters( self ) :

		script = Gaffer.ScriptNode()
		script["catalogue"] = GafferImage.Catalogue()

		script["light"], colorPlug = self._createSpotLight()
		colorPlug.setValue( imath.Color3f( 1, 1, 0 ) )
		script["light"]["transform"]["translate"]["z"].setValue( 1 )

		script["gobo"], goboColorPlug = self._createGobo()
		goboColorPlug.setValue( imath.Color3f( 0, 1, 1 ) )
		script["gobo"]["enabled"].setValue( False )

		script["goboAssignment"] = GafferScene.ShaderAssignment()
		script["goboAssignment"]["in"].setInput( script["light"]["out"] )
		script["goboAssignment"]["shader"].setInput( script["gobo"]["out"] )

		script["plane"] = GafferScene.Plane()

		script["cam"] = GafferScene.Camera()
		script["cam"]["transform"]["translate"]["z"].setValue( 1 )

		lightFilter, lightFilterDensityPlug = self._createLightFilter()
		script["lightFilter"] = lightFilter
		lightFilterDensityPlug.setValue( 0.0 )  # looking at unfiltered result first

		script["attributes"] = GafferScene.StandardAttributes()
		script["attributes"]["in"].setInput( script["lightFilter"]["out"] )

		# This will link the light filter to just the one spot light.
		script["attributes"]["attributes"]["filteredLights"]["enabled"].setValue( True )
		script["attributes"]["attributes"]["filteredLights"]["value"].setValue( "defaultLights" )

		script["group"] = GafferScene.Group()
		script["group"]["in"][0].setInput( script["goboAssignment"]["out"] )
		script["group"]["in"][1].setInput( script["plane"]["out"] )
		script["group"]["in"][2].setInput( script["cam"]["out"] )
		script["group"]["in"][3].setInput( script["attributes"]["out"] )

		script["shader"], unused = self._createMatteShader()
		script["assignment"] = GafferScene.ShaderAssignment()
		script["assignment"]["in"].setInput( script["group"]["out"] )
		script["assignment"]["shader"].setInput( script["shader"]["out"] )

		script["outputs"] = GafferScene.Outputs()
		script["outputs"].addOutput(
			"beauty",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ClientDisplayDriver",
					"displayHost" : "localhost",
					"displayPort" : str( script['catalogue'].displayDriverServer().portNumber() ),
					"remoteDisplayType" : "GafferImage::GafferDisplayDriver",
				}
			)
		)
		script["outputs"]["in"].setInput( script["assignment"]["out"] )

		script["options"] = GafferScene.StandardOptions()
		script["options"]["options"]["renderCamera"]["value"].setValue( "/group/camera" )
		script["options"]["options"]["renderCamera"]["enabled"].setValue( True )
		script["options"]["in"].setInput( script["outputs"]["out"] )

		script["render"] = self._createInteractiveRender()
		script["render"]["in"].setInput( script["options"]["out"] )

		# Render and give it some time to finish.

		script["render"]["state"].setValue( script["render"].State.Running )

		self.uiThreadCallHandler.waitFor( 1 )

		c = self._color4fAtUV( script["catalogue"], imath.V2f( 0.5 ) )
		unfilteredIntensity = c[0]
		self.__assertColorsAlmostEqual( c, imath.Color4f( unfilteredIntensity, unfilteredIntensity, 0, 1 ), delta = 0.01 )

		# Use a dense light filter and let renderer update

		lightFilterDensityPlug.setValue( 1.0 )

		self.uiThreadCallHandler.waitFor( 1 )
		self.__assertColorsAlmostEqual( self._color4fAtUV( script["catalogue"], imath.V2f( 0.5 ) ), imath.Color4f( 0, 0, 0, 1 ), delta = 0.01 )

		# Disable light filter and let renderer update

		script["lightFilter"]["enabled"].setValue( False )

		self.uiThreadCallHandler.waitFor( 1 )
		self.__assertColorsAlmostEqual( self._color4fAtUV( script["catalogue"], imath.V2f( 0.5 ) ), imath.Color4f( unfilteredIntensity, unfilteredIntensity, 0, 1 ), delta = 0.01 )

		# Enable light filter and let renderer update

		script["lightFilter"]["enabled"].setValue( True )

		self.uiThreadCallHandler.waitFor( 1 )
		self.__assertColorsAlmostEqual( self._color4fAtUV( script["catalogue"], imath.V2f( 0.5 ) ), imath.Color4f( 0, 0, 0, 1 ), delta = 0.01 )

		# Add a gobo and disable light filter

		script["gobo"]["enabled"].setValue( True )
		script["lightFilter"]["enabled"].setValue( False )

		self.uiThreadCallHandler.waitFor( 1 )
		self.__assertColorsAlmostEqual( self._color4fAtUV( script["catalogue"], imath.V2f( 0.5 ) ), imath.Color4f( 0, unfilteredIntensity, 0, 1 ), delta = 0.01 )

		# Look at combined result of light filter and gobo

		script["lightFilter"]["enabled"].setValue( True )
		lightFilterDensityPlug.setValue( 0.5 )

		self.uiThreadCallHandler.waitFor( 1 )
		self.__assertColorsAlmostEqual( self._color4fAtUV( script["catalogue"], imath.V2f( 0.5 ) ), imath.Color4f( 0, unfilteredIntensity * 0.5, 0, 1 ), delta = 0.01 )

		# Change parameter on light

		script["light"]["parameters"]["intensity"].setValue( 2.0 )

		self.uiThreadCallHandler.waitFor( 1 )
		self.__assertColorsAlmostEqual( self._color4fAtUV( script["catalogue"], imath.V2f( 0.5 ) ), imath.Color4f( 0, unfilteredIntensity, 0, 1 ), delta = 0.01 )

		# Change light filter transformation

		script["lightFilter"]["transform"]["rotate"]["x"].setValue( 0.1 )

		self.uiThreadCallHandler.waitFor( 1 )
		self.__assertColorsAlmostEqual( self._color4fAtUV( script["catalogue"], imath.V2f( 0.5 ) ), imath.Color4f( 0, unfilteredIntensity, 0, 1 ), delta = 0.01 )

		# Change light filter parameter

		script["lightFilter"]["parameters"]["geometry_type"].setValue( "sphere" )

		self.uiThreadCallHandler.waitFor( 1 )
		self.__assertColorsAlmostEqual( self._color4fAtUV( script["catalogue"], imath.V2f( 0.5 ) ), imath.Color4f( 0, unfilteredIntensity, 0, 1 ), delta = 0.01 )

		# Disable light

		script["light"]["enabled"].setValue( False )

		self.uiThreadCallHandler.waitFor( 1 )
		self.__assertColorsAlmostEqual( self._color4fAtUV( script["catalogue"], imath.V2f( 0.5 ) ), imath.Color4f( 0, 0, 0, 1 ), delta = 0.01 )

		# Reenable light

		script["light"]["enabled"].setValue( True )

		self.uiThreadCallHandler.waitFor( 1 )
		self.__assertColorsAlmostEqual( self._color4fAtUV( script["catalogue"], imath.V2f( 0.5 ) ), imath.Color4f( 0, unfilteredIntensity, 0, 1 ), delta = 0.01 )

		# Disable gobo, reset light and filter

		script["gobo"]["enabled"].setValue( False )
		script["light"]["parameters"]["intensity"].setValue( 1.0 )
		lightFilterDensityPlug.setValue( 1 )

		self.uiThreadCallHandler.waitFor( 1 )
		self.__assertColorsAlmostEqual( self._color4fAtUV( script["catalogue"], imath.V2f( 0.5 ) ), imath.Color4f( 0, 0, 0, 1 ), delta = 0.01 )

		# Unlink the filter

		script["attributes"]["attributes"]["filteredLights"]["value"].setValue( "" )

		self.uiThreadCallHandler.waitFor( 1 )
		self.__assertColorsAlmostEqual( self._color4fAtUV( script["catalogue"], imath.V2f( 0.5 ) ), imath.Color4f( unfilteredIntensity, unfilteredIntensity, 0, 1 ), delta = 0.01 )

		# Relink the filter

		script["attributes"]["attributes"]["filteredLights"]["value"].setValue( "defaultLights" )

		self.uiThreadCallHandler.waitFor( 1 )
		self.__assertColorsAlmostEqual( self._color4fAtUV( script["catalogue"], imath.V2f( 0.5 ) ), imath.Color4f( 0, 0, 0, 1 ), delta = 0.01 )

		script["render"]["state"].setValue( script["render"].State.Stopped )

	def testLightFiltersAndSetEdits( self ) :

		script = Gaffer.ScriptNode()
		script["catalogue"] = GafferImage.Catalogue()

		script["light"], unused = self._createPointLight()
		script["light"]["transform"]["translate"]["z"].setValue( 1 )

		script["plane"] = GafferScene.Plane()

		script["shader"], unused = self._createMatteShader()
		script["assignment"] = GafferScene.ShaderAssignment()
		script["assignment"]["in"].setInput( script["plane"]["out"] )
		script["assignment"]["shader"].setInput( script["shader"]["out"] )

		script["camera"] = GafferScene.Camera()
		script["camera"]["transform"]["translate"]["z"].setValue( 1 )

		script["lightFilter"], lightFilterDensityPlug = self._createLightFilter()
		lightFilterDensityPlug.setValue( 1 )

		script["group"] = GafferScene.Group()
		script["group"]["in"][0].setInput( script["light"]["out"] )
		script["group"]["in"][1].setInput( script["camera"]["out"] )
		script["group"]["in"][2].setInput( script["assignment"]["out"] )
		script["group"]["in"][3].setInput( script["lightFilter"]["out"] )

		script["outputs"] = GafferScene.Outputs()
		script["outputs"].addOutput(
			"beauty",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ClientDisplayDriver",
					"displayHost" : "localhost",
					"displayPort" : str( script['catalogue'].displayDriverServer().portNumber() ),
					"remoteDisplayType" : "GafferImage::GafferDisplayDriver",
				}
			)
		)
		script["outputs"]["in"].setInput( script["group"]["out"] )

		script["options"] = GafferScene.StandardOptions()
		script["options"]["options"]["renderCamera"]["value"].setValue( "/group/camera" )
		script["options"]["options"]["renderCamera"]["enabled"].setValue( True )
		script["options"]["in"].setInput( script["outputs"]["out"] )

		script["render"] = self._createInteractiveRender()
		script["render"]["in"].setInput( script["options"]["out"] )

		# Render and give it some time to finish. Should be unfiltered, because
		# by default, filters aren't linked.

		script["render"]["state"].setValue( script["render"].State.Running )
		self.uiThreadCallHandler.waitFor( 1 )

		unfilteredColor = self._color4fAtUV( script["catalogue"], imath.V2f( 0.5 ) )
		self.assertGreater( unfilteredColor[0], 0.25 )

		# Try to link the filter. Should still be unfiltered, because the set is
		# empty.

		script["lightFilter"]["filteredLights"].setValue( "mySet" )
		self.uiThreadCallHandler.waitFor( 1 )

		self.__assertColorsAlmostEqual( self._color4fAtUV( script["catalogue"], imath.V2f( 0.5 ) ), unfilteredColor, delta = 0.01 )

		# Add the light into the set. Now the filtering should happen.

		script["light"]["sets"].setValue( "mySet" )
		self.uiThreadCallHandler.waitFor( 1 )

		self.__assertColorsAlmostEqual( self._color4fAtUV( script["catalogue"], imath.V2f( 0.5 ) ), imath.Color4f( 0, 0, 0, 1 ), delta = 0.01 )

		# Take the light out of the set. Goodbye filtering.

		script["light"]["sets"].setValue( "" )
		self.uiThreadCallHandler.waitFor( 1 )

		self.__assertColorsAlmostEqual( self._color4fAtUV( script["catalogue"], imath.V2f( 0.5 ) ), unfilteredColor, delta = 0.01 )
		script["render"]["state"].setValue( script["render"].State.Stopped )

	def testAdaptors( self ) :

		s = Gaffer.ScriptNode()
		s["catalogue"] = GafferImage.Catalogue()
		s["s"] = GafferScene.Sphere()

		def a() :

			result = GafferScene.SceneProcessor()

			result["__shader"], colorPlug = self._createConstantShader()
			colorPlug.setValue( imath.Color3f( 1, 0, 0 ) )

			result["__assignment"] = GafferScene.ShaderAssignment()
			result["__assignment"]["in"].setInput( result["in"] )
			result["__assignment"]["shader"].setInput( result["__shader"]["out"] )

			result["out"].setInput( result["__assignment"]["out"] )

			return result

		GafferScene.SceneAlgo.registerRenderAdaptor( "Test", a )

		s["o"] = GafferScene.Outputs()
		s["o"].addOutput(
			"beauty",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ClientDisplayDriver",
					"displayHost" : "localhost",
					"displayPort" : str( s['catalogue'].displayDriverServer().portNumber() ),
					"remoteDisplayType" : "GafferImage::GafferDisplayDriver",
				}
			)
		)
		s["o"]["in"].setInput( s["s"]["out"] )

		s["r"] = self._createInteractiveRender()
		s["r"]["in"].setInput( s["o"]["out"] )

		s["r"]["state"].setValue( s["r"].State.Running )

		self.uiThreadCallHandler.waitFor( 2.0 )

		# Render red sphere

		self.__assertColorsAlmostEqual( self._color4fAtUV( s["catalogue"], imath.V2f( 0.5 ) ), imath.Color4f( 1, 0, 0, 1 ), delta = 0.01 )
		s["r"]["state"].setValue( s["r"].State.Stopped )

	def testLightLinking( self ) :

		s = Gaffer.ScriptNode()
		s["catalogue"] = GafferImage.Catalogue()

		s["l"], colorPlug = self._createPointLight()
		colorPlug.setValue( imath.Color3f( 1, 0.5, 0.25 ) )
		s["l"]["transform"]["translate"]["z"].setValue( 1 )

		s["p"] = GafferScene.Plane()

		s["c"] = GafferScene.Camera()
		s["c"]["transform"]["translate"]["z"].setValue( 1 )

		s["g"] = GafferScene.Group()
		s["g"]["in"][0].setInput( s["l"]["out"] )
		s["g"]["in"][1].setInput( s["p"]["out"] )
		s["g"]["in"][2].setInput( s["c"]["out"] )

		s["s"], unused = self._createMatteShader()
		s["a"] = GafferScene.ShaderAssignment()
		s["a"]["in"].setInput( s["g"]["out"] )
		s["a"]["shader"].setInput( s["s"]["out"] )

		s["d"] = GafferScene.Outputs()
		s["d"].addOutput(
			"beauty",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ClientDisplayDriver",
					"displayHost" : "localhost",
					"displayPort" : str( s['catalogue'].displayDriverServer().portNumber() ),
					"remoteDisplayType" : "GafferImage::GafferDisplayDriver",
					"quantize" : IECore.IntVectorData( [ 0, 0, 0, 0 ] ),
				}
			)
		)
		s["d"]["in"].setInput( s["a"]["out"] )

		s["o"] = GafferScene.StandardOptions()
		s["o"]["options"]["renderCamera"]["value"].setValue( "/group/camera" )
		s["o"]["options"]["renderCamera"]["enabled"].setValue( True )
		s["o"]["in"].setInput( s["d"]["out"] )

		s["r"] = self._createInteractiveRender()
		s["r"]["in"].setInput( s["o"]["out"] )

		# Start a render, give it time to finish, and check the output.

		s["r"]["state"].setValue( s["r"].State.Running )

		self.uiThreadCallHandler.waitFor( 2 )

		c = self._color3fAtUV( s["catalogue"], imath.V2f( 0.5 ) )
		self.assertEqual( c / c[0], imath.Color3f( 1, 0.5, 0.25 ) )

		# Unlink the light, give it time to update, and check the output.

		s["l"]["defaultLight"].setValue( False )

		self.uiThreadCallHandler.waitFor( 1 )

		c = self._color3fAtUV( s["catalogue"], imath.V2f( 0.5 ) )
		self.assertEqual( c, imath.Color3f( 0, 0, 0 ) )

		# \todo: This should also test the light linking functionaly provided by
		# StandardAttributes

		s["r"]["state"].setValue( s["r"].State.Stopped )

	def testHideLinkedLight( self ) :

		s = Gaffer.ScriptNode()
		s["catalogue"] = GafferImage.Catalogue()

		# One default light and one non-default light, which will
		# result in light links being emitted to the renderer.

		s["defaultLight"], colorPlug = self._createPointLight()
		s["defaultLight"]["name"].setValue( "defaultPointLight" )
		colorPlug.setValue( imath.Color3f( 1, 0, 0 ) )
		s["defaultLight"]["transform"]["translate"]["z"].setValue( 1 )

		s["defaultLightAttributes"] = GafferScene.StandardAttributes()
		s["defaultLightAttributes"]["in"].setInput( s["defaultLight"]["out"] )

		s["nonDefaultLight"], colorPlug = self._createPointLight()
		s["nonDefaultLight"]["name"].setValue( "nonDefaultPointLight" )
		s["nonDefaultLight"]["defaultLight"].setValue( False )
		colorPlug.setValue( imath.Color3f( 0, 1, 0 ) )
		s["nonDefaultLight"]["transform"]["translate"]["z"].setValue( 1 )

		s["plane"] = GafferScene.Plane()

		s["camera"] = GafferScene.Camera()
		s["camera"]["transform"]["translate"]["z"].setValue( 1 )

		s["group"] = GafferScene.Group()
		s["group"]["in"][0].setInput( s["defaultLightAttributes"]["out"] )
		s["group"]["in"][1].setInput( s["nonDefaultLight"]["out"] )
		s["group"]["in"][2].setInput( s["plane"]["out"] )
		s["group"]["in"][3].setInput( s["camera"]["out"] )

		s["shader"], unused = self._createMatteShader()
		s["shaderAssignment"] = GafferScene.ShaderAssignment()
		s["shaderAssignment"]["in"].setInput( s["group"]["out"] )
		s["shaderAssignment"]["shader"].setInput( s["shader"]["out"] )

		s["outputs"] = GafferScene.Outputs()
		s["outputs"].addOutput(
			"beauty",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ClientDisplayDriver",
					"displayHost" : "localhost",
					"displayPort" : str( s['catalogue'].displayDriverServer().portNumber() ),
					"remoteDisplayType" : "GafferImage::GafferDisplayDriver",
					"quantize" : IECore.IntVectorData( [ 0, 0, 0, 0 ] ),
				}
			)
		)
		s["outputs"]["in"].setInput( s["shaderAssignment"]["out"] )

		s["options"] = GafferScene.StandardOptions()
		s["options"]["options"]["renderCamera"]["value"].setValue( "/group/camera" )
		s["options"]["options"]["renderCamera"]["enabled"].setValue( True )
		s["options"]["in"].setInput( s["outputs"]["out"] )

		s["renderer"] = self._createInteractiveRender()
		s["renderer"]["in"].setInput( s["options"]["out"] )

		# Start a render, give it time to finish, and check the output.
		# We should get light only from the default light, and not the
		# other one.

		s["renderer"]["state"].setValue( s["renderer"].State.Running )

		self.uiThreadCallHandler.waitFor( 2 )

		c = self._color3fAtUV( s["catalogue"], imath.V2f( 0.5 ) )
		self.assertNotEqual( c[0], 0 )
		self.assertEqual( c / c[0], imath.Color3f( 1, 0, 0 ) )

		# Hide the default light. We should get a black render.

		s["defaultLightAttributes"]["attributes"]["visibility"]["enabled"].setValue( True )
		s["defaultLightAttributes"]["attributes"]["visibility"]["value"].setValue( False )

		self.uiThreadCallHandler.waitFor( 1 )

		c = self._color3fAtUV( s["catalogue"], imath.V2f( 0.5 ) )
		self.assertEqual( c, imath.Color3f( 0, 0, 0 ) )

		s["renderer"]["state"].setValue( s["renderer"].State.Stopped )

	def testAcceptsInput( self ) :

		r = GafferScene.InteractiveRender()

		p = Gaffer.StringPlug()
		r["renderer"].setInput( p )
		r["renderer"].setInput( None )

		s = GafferTest.StringInOutNode()
		with self.assertRaisesRegex( Exception, 'Plug "%s.renderer" rejects input "StringInOutNode.out".' % r.getName() ) :
			r["renderer"].setInput( s["out"] )

		r = self._createInteractiveRender()

		p = Gaffer.IntPlug()
		r["state"].setInput( p )
		r["state"].setInput( None )

		a = GafferTest.AddNode()
		with self.assertRaisesRegex( Exception, 'Plug "%s.state" rejects input "AddNode.sum".' % r.getName() ) :
			r["state"].setInput( a["sum"] )

	def testEditCropWindow( self ) :

		script = Gaffer.ScriptNode()
		script["catalogue"] = GafferImage.Catalogue()

		script["outputs"] = GafferScene.Outputs()
		script["outputs"].addOutput(
			"beauty",
			IECoreScene.Output(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ClientDisplayDriver",
					"displayHost" : "localhost",
					"displayPort" : str( script["catalogue"].displayDriverServer().portNumber() ),
					"remoteDisplayType" : "GafferImage::GafferDisplayDriver",
				}
			)
		)

		script["options"] = GafferScene.StandardOptions()
		script["options"]["in"].setInput( script["outputs"]["out"] )

		script["renderer"] = self._createInteractiveRender()
		script["renderer"]["in"].setInput( script["options"]["out"] )

		# Start a render, give it time to finish, and check the output.

		script["renderer"]["state"].setValue( script["renderer"].State.Running )
		self.uiThreadCallHandler.waitFor( 1 )

		self.assertEqual( len( script["catalogue"]["images"] ), 1 )
		self.assertEqual( script["catalogue"]["out"].dataWindow(), imath.Box2i( imath.V2i( 0 ), imath.V2i( 640, 480 ) ) )
		self.assertEqual( script["catalogue"]["out"].metadata()["gaffer:isRendering"], IECore.BoolData( True ) )

		# Change the crop. The current image should change its data window,
		# and no new image should be created.

		with Gaffer.DirtyPropagationScope() :
			script["options"]["options"]["renderCropWindow"]["enabled"].setValue( True )
			script["options"]["options"]["renderCropWindow"]["value"].setValue( imath.Box2f( imath.V2f( 0 ), imath.V2f( 0.5 ) ) )

		self.uiThreadCallHandler.waitFor( 1 )

		self.assertEqual( len( script["catalogue"]["images"] ), 1 )
		self.assertEqual( script["catalogue"]["out"].dataWindow(), imath.Box2i( imath.V2i( 0, 240 ), imath.V2i( 320, 480 ) ) )
		self.assertEqual( script["catalogue"]["out"].metadata()["gaffer:isRendering"], IECore.BoolData( True ) )

		script["renderer"]["state"].setValue( script["renderer"].State.Stopped )
		self.uiThreadCallHandler.assertCalled() # Wait for saving to complete

		if script["renderer"].typeName() == "GafferCycles::InteractiveCyclesRender" :
			# Cycles somehow manages to do stuff after we've deleted the CyclesRenderer.
			# Wait for it to finish.
			## \todo Figure out why this is needed, and fix it.
			self.uiThreadCallHandler.waitFor( 1 )

		self.assertNotIn( "gaffer:isRendering", script["catalogue"]["out"].metadata() )

	def tearDown( self ) :

		GafferSceneTest.SceneTestCase.tearDown( self )

		GafferScene.SceneAlgo.deregisterRenderAdaptor( "Test" )

	## Should be used in test cases to create an InteractiveRender node
	# suitably configured for error reporting. If failOnError is
	# True, then the node's error signal will cause the test to fail.
	def _createInteractiveRender( self, failOnError = True ) :

		assert( issubclass( self.interactiveRenderNodeClass, GafferScene.InteractiveRender ) )
		node = self.interactiveRenderNodeClass()

		if failOnError :

			def fail( plug, source, message ) :
				script = plug.ancestor( Gaffer.ScriptNode )
				self.fail( "errorSignal caught : {} [{}] : {}".format(
					plug.relativeName( script ),
					source.relativeName( script ),
					message
				) )

			node.errorSignal().connect( fail, scoped = False )

		return node

	## Should be implemented by derived classes to return an
	# appropriate Shader node with a constant shader loaded,
	# along with the plug for the colour parameter.
	def _createConstantShader( self ) :

		raise NotImplementedError

	## Should be implemented by derived classes to return
	# an appropriate Shader node with a matte shader loaded,
	# along with the plug for the colour parameter.
	def _createMatteShader( self ) :

		raise NotImplementedError

	## Should be implemented by derived classes to return
	# a shader which traces against only geometry in a trace
	# set parameter.
	def _createTraceSetShader( self ) :

		raise NotImplementedError

	## Should be implemented by derived classes to return
	# the name of a bool attribute which controls camera
	# visibility.
	def _cameraVisibilityAttribute( self ) :

		raise NotImplementedError

	## Should be implemented by derived classes to return the
	# names of int options which control trace depth.
	def _traceDepthOptions( self ) :

		raise NotImplementedError

	# Should be implemented by derived classes to return
	# an appropriate Light node with a point light loaded,
	# along with the plug for the colour parameter.
	def _createPointLight( self ) :

		raise NotImplementedError

	# Should be implemented by derived classes to return
	# an appropriate LightFilter node along with the plug
	# controlling the light filter's density
	def _createLightFilter( self ) :

		raise NotImplementedError

	# May be implemented to return a node to set any renderer-specific
	# options that should be used by the tests.
	def _createOptions( self ) :

		return GafferScene.CustomOptions()

	def _color4fAtUV( self, image, uv ) :

		sampler = GafferImage.ImageSampler()
		sampler["image"].setInput( image["out"] )
		dw = image['out']["format"].getValue().getDisplayWindow().size()
		sampler["pixel"].setValue( uv * imath.V2f( dw.x, dw.y ) )

		return sampler["color"].getValue()

	def _color3fAtUV( self, image, uv ) :

		c = self._color4fAtUV( image, uv )
		return imath.Color3f( c.r, c.g, c.b )

	def __assertColorsAlmostEqual( self, c0, c1, **kw ) :

		for i in range( 0, 4 ) :
			self.assertAlmostEqual( c0[i], c1[i], **kw )

if __name__ == "__main__":
	unittest.main()
