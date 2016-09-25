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

import IECore

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest

# Note that this is for testing subclasses of GafferScene.Preview.InteractiveRender
# rather than GafferScene.InteractiveRender, which we hope to phase out.
class InteractiveRenderTest( GafferSceneTest.SceneTestCase ) :

	@classmethod
	def setUpClass( cls ) :

		GafferSceneTest.SceneTestCase.setUpClass()

		if cls is InteractiveRenderTest :
			# The InteractiveRenderTest class is a base class to
			# derive from when wanting to test specific InteractiveRender
			# subclasses - on its own it has no renderer so can't
			# test anything.
			raise unittest.SkipTest( "No renderer available" )

	def testOutputs( self ):

		s = Gaffer.ScriptNode()
		s["s"] = GafferScene.Sphere()

		s["o"] = GafferScene.Outputs()
		s["o"].addOutput(
			"beauty",
			IECore.Display(
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

		time.sleep( 0.5 )

		image = IECore.ImageDisplayDriver.storedImage( "myLovelySphere" )
		self.assertTrue( isinstance( image, IECore.ImagePrimitive ) )

	def testAddAndRemoveOutput( self ):

		s = Gaffer.ScriptNode()
		s["s"] = GafferScene.Sphere()

		s["o"] = GafferScene.Outputs()

		s["o"].addOutput(
			"beauty1",
			IECore.Display(
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

		time.sleep( 0.5 )

		# Check we have our first image, but not a second one.

		self.assertTrue( isinstance( IECore.ImageDisplayDriver.storedImage( "myLovelySphere1" ), IECore.ImagePrimitive ) )
		self.assertTrue( IECore.ImageDisplayDriver.storedImage( "myLovelySphere2" ) is None )

		# Add a second image and check we can have that too.

		s["o"].addOutput(
			"beauty2",
			IECore.Display(
				"test1",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ImageDisplayDriver",
					"handle" : "myLovelySphere2",
				}
			)
		)

		time.sleep( 0.5 )

		self.assertTrue( isinstance( IECore.ImageDisplayDriver.storedImage( "myLovelySphere1" ), IECore.ImagePrimitive ) )
		self.assertTrue( isinstance( IECore.ImageDisplayDriver.storedImage( "myLovelySphere2" ), IECore.ImagePrimitive ) )

		# Remove the second image and check that it stops updating.

		IECore.ImageDisplayDriver.removeStoredImage( "myLovelySphere2" )
		s["o"]["outputs"][1]["active"].setValue( False )

		time.sleep( 0.5 )

		self.assertTrue( IECore.ImageDisplayDriver.storedImage( "myLovelySphere2" ) is None )

		# Add a third image and check we can have that too.

		s["o"].addOutput(
			"beauty3",
			IECore.Display(
				"test1",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ImageDisplayDriver",
					"handle" : "myLovelySphere3",
				}
			)
		)

		time.sleep( 0.5 )

		self.assertTrue( isinstance( IECore.ImageDisplayDriver.storedImage( "myLovelySphere1" ), IECore.ImagePrimitive ) )
		self.assertTrue( IECore.ImageDisplayDriver.storedImage( "myLovelySphere2" ) is None )
		self.assertTrue( isinstance( IECore.ImageDisplayDriver.storedImage( "myLovelySphere3" ), IECore.ImagePrimitive ) )

	def testAddAndRemoveLocation( self ) :

		s = Gaffer.ScriptNode()
		s["s"] = GafferScene.Sphere()

		s["o"] = GafferScene.Outputs()
		s["o"].addOutput(
			"beauty",
			IECore.Display(
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

		time.sleep( 0.5 )

		image = IECore.ImageDisplayDriver.storedImage( "myLovelySphere" )
		self.assertAlmostEqual( self.__color4fAtUV( image, IECore.V2f( 0.5 ) ).r, 1, delta = 0.01 )

		s["s"]["enabled"].setValue( False )
		time.sleep( 0.5 )

		image = IECore.ImageDisplayDriver.storedImage( "myLovelySphere" )
		self.assertAlmostEqual( self.__color4fAtUV( image, IECore.V2f( 0.5 ) ).r, 0, delta = 0.01 )

		s["s"]["enabled"].setValue( True )
		time.sleep( 0.5 )

		image = IECore.ImageDisplayDriver.storedImage( "myLovelySphere" )
		self.assertAlmostEqual( self.__color4fAtUV( image, IECore.V2f( 0.5 ) ).r, 1, delta = 0.01 )

	def testAddAndRemoveObject( self ) :

		s = Gaffer.ScriptNode()

		# Switch between a sphere and a group, so
		# we can keep the hierarchy the same ( "/thing" )
		# but add and remove the sphere from the location.

		s["s"] = GafferScene.Sphere()
		s["s"]["name"].setValue( "thing" )

		s["g"] = GafferScene.Group()
		s["g"]["name"].setValue( "thing" )

		s["switch"] = GafferScene.SceneSwitch()
		s["switch"]["in"][0].setInput( s["s"]["out"] )
		s["switch"]["in"][1].setInput( s["g"]["out"] )

		s["o"] = GafferScene.Outputs()
		s["o"].addOutput(
			"beauty",
			IECore.Display(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ImageDisplayDriver",
					"handle" : "myLovelySphere",
				}
			)
		)
		s["o"]["in"].setInput( s["switch"]["out"] )

		s["r"] = self._createInteractiveRender()
		s["r"]["in"].setInput( s["o"]["out"] )

		# Render the sphere.

		s["r"]["state"].setValue( s["r"].State.Running )
		time.sleep( 0.5 )

		image = IECore.ImageDisplayDriver.storedImage( "myLovelySphere" )
		self.assertAlmostEqual( self.__color4fAtUV( image, IECore.V2f( 0.5 ) ).r, 1, delta = 0.01 )

		# Switch to the empty group.

		s["switch"]["index"].setValue( 1 )
		time.sleep( 0.5 )

		image = IECore.ImageDisplayDriver.storedImage( "myLovelySphere" )
		self.assertAlmostEqual( self.__color4fAtUV( image, IECore.V2f( 0.5 ) ).r, 0, delta = 0.01 )

		# Switch back to the sphere.

		s["switch"]["index"].setValue( 0 )
		time.sleep( 0.5 )

		image = IECore.ImageDisplayDriver.storedImage( "myLovelySphere" )
		self.assertAlmostEqual( self.__color4fAtUV( image, IECore.V2f( 0.5 ) ).r, 1, delta = 0.01 )

	def testEditObjectVisibility( self ) :

		s = Gaffer.ScriptNode()
		s["s"] = GafferScene.Sphere()

		s["g"] = GafferScene.Group()
		s["g"]["in"].setInput( s["s"]["out"] )

		s["f"] = GafferScene.PathFilter()

		s["a"] = GafferScene.StandardAttributes()
		s["a"]["in"].setInput( s["g"]["out"] )
		s["a"]["filter"].setInput( s["f"]["out"] )
		s["a"]["attributes"]["visibility"]["enabled"].setValue( True )

		s["o"] = GafferScene.Outputs()
		s["o"].addOutput(
			"beauty",
			IECore.Display(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ImageDisplayDriver",
					"handle" : "myLovelySphere",
				}
			)
		)
		s["o"]["in"].setInput( s["a"]["out"] )

		s["r"] = self._createInteractiveRender()
		s["r"]["in"].setInput( s["o"]["out"] )

		s["r"]["state"].setValue( s["r"].State.Running )

		time.sleep( 0.5 )

		# Visible to start with

		image = IECore.ImageDisplayDriver.storedImage( "myLovelySphere" )
		self.assertAlmostEqual( self.__color4fAtUV( image, IECore.V2f( 0.5 ) ).r, 1, delta = 0.01 )

		# Hide /group/sphere

		s["f"]["paths"].setValue( IECore.StringVectorData( [ "/group/sphere" ] ) )
		s["a"]["attributes"]["visibility"]["value"].setValue( False )
		time.sleep( 0.5 )

		image = IECore.ImageDisplayDriver.storedImage( "myLovelySphere" )
		self.assertAlmostEqual( self.__color4fAtUV( image, IECore.V2f( 0.5 ) ).r, 0, delta = 0.01 )

		# Tweak the sphere geometry - it should remain hidden

		s["s"]["radius"].setValue( 1.01 )
		time.sleep( 0.5 )

		image = IECore.ImageDisplayDriver.storedImage( "myLovelySphere" )
		self.assertAlmostEqual( self.__color4fAtUV( image, IECore.V2f( 0.5 ) ).r, 0, delta = 0.01 )

		# Show it again

		s["a"]["attributes"]["visibility"]["value"].setValue( True )
		time.sleep( 0.5 )

		image = IECore.ImageDisplayDriver.storedImage( "myLovelySphere" )
		self.assertAlmostEqual( self.__color4fAtUV( image, IECore.V2f( 0.5 ) ).r, 1, delta = 0.01 )

		# Hide /group

		s["f"]["paths"].setValue( IECore.StringVectorData( [ "/group" ] ) )
		s["a"]["attributes"]["visibility"]["value"].setValue( False )
		time.sleep( 0.5 )

		image = IECore.ImageDisplayDriver.storedImage( "myLovelySphere" )
		self.assertAlmostEqual( self.__color4fAtUV( image, IECore.V2f( 0.5 ) ).r, 0, delta = 0.01 )

		# Show it again

		s["a"]["attributes"]["visibility"]["value"].setValue( True )
		time.sleep( 0.5 )

		image = IECore.ImageDisplayDriver.storedImage( "myLovelySphere" )
		self.assertAlmostEqual( self.__color4fAtUV( image, IECore.V2f( 0.5 ) ).r, 1, delta = 0.01 )

	def testEditCameraVisibility( self ) :

		s = Gaffer.ScriptNode()
		s["s"] = GafferScene.Sphere()

		s["g"] = GafferScene.Group()
		s["g"]["in"].setInput( s["s"]["out"] )

		s["f"] = GafferScene.PathFilter()

		s["a"] = GafferScene.CustomAttributes()
		s["a"]["in"].setInput( s["g"]["out"] )
		s["a"]["filter"].setInput( s["f"]["out"] )
		visibilityPlug = s["a"]["attributes"].addMember( self._cameraVisibilityAttribute(), False )

		s["o"] = GafferScene.Outputs()
		s["o"].addOutput(
			"beauty",
			IECore.Display(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ImageDisplayDriver",
					"handle" : "myLovelySphere",
				}
			)
		)
		s["o"]["in"].setInput( s["a"]["out"] )

		s["r"] = self._createInteractiveRender()
		s["r"]["in"].setInput( s["o"]["out"] )

		s["r"]["state"].setValue( s["r"].State.Running )

		time.sleep( 0.5 )

		# Visible to start with

		image = IECore.ImageDisplayDriver.storedImage( "myLovelySphere" )
		self.assertAlmostEqual( self.__color4fAtUV( image, IECore.V2f( 0.5 ) ).r, 1, delta = 0.01 )

		# Hide /group/sphere

		s["f"]["paths"].setValue( IECore.StringVectorData( [ "/group/sphere" ] ) )
		visibilityPlug["value"].setValue( False )
		time.sleep( 0.5 )

		image = IECore.ImageDisplayDriver.storedImage( "myLovelySphere" )
		self.assertAlmostEqual( self.__color4fAtUV( image, IECore.V2f( 0.5 ) ).r, 0, delta = 0.01 )

		# Show it again

		visibilityPlug["value"].setValue( True )
		time.sleep( 0.5 )

		image = IECore.ImageDisplayDriver.storedImage( "myLovelySphere" )
		self.assertAlmostEqual( self.__color4fAtUV( image, IECore.V2f( 0.5 ) ).r, 1, delta = 0.01 )

		# Hide /group

		s["f"]["paths"].setValue( IECore.StringVectorData( [ "/group" ] ) )
		visibilityPlug["value"].setValue( False )
		time.sleep( 0.5 )

		image = IECore.ImageDisplayDriver.storedImage( "myLovelySphere" )
		self.assertAlmostEqual( self.__color4fAtUV( image, IECore.V2f( 0.5 ) ).r, 0, delta = 0.01 )

		# Show it again

		visibilityPlug["value"].setValue( True )
		time.sleep( 0.5 )

		image = IECore.ImageDisplayDriver.storedImage( "myLovelySphere" )
		self.assertAlmostEqual( self.__color4fAtUV( image, IECore.V2f( 0.5 ) ).r, 1, delta = 0.01 )

	def testEditObjectTransform( self ) :

		s = Gaffer.ScriptNode()
		s["s"] = GafferScene.Sphere()

		s["o"] = GafferScene.Outputs()
		s["o"].addOutput(
			"beauty",
			IECore.Display(
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

		time.sleep( 0.5 )

		# Visible to start with

		image = IECore.ImageDisplayDriver.storedImage( "myLovelySphere" )
		self.assertAlmostEqual( self.__color4fAtUV( image, IECore.V2f( 0.5 ) ).r, 1, delta = 0.01 )

		# Move to one side

		s["s"]["transform"]["translate"]["x"].setValue( 2 )
		time.sleep( 0.5 )

		image = IECore.ImageDisplayDriver.storedImage( "myLovelySphere" )
		self.assertAlmostEqual( self.__color4fAtUV( image, IECore.V2f( 0.5 ) ).r, 0, delta = 0.01 )

		# Move back

		s["s"]["transform"]["translate"]["x"].setValue( 0 )
		time.sleep( 0.5 )

		image = IECore.ImageDisplayDriver.storedImage( "myLovelySphere" )
		self.assertAlmostEqual( self.__color4fAtUV( image, IECore.V2f( 0.5 ) ).r, 1, delta = 0.01 )

	def testShaderEdits( self ) :

		s = Gaffer.ScriptNode()
		s["s"] = GafferScene.Sphere()

		s["shader"], colorPlug = self._createConstantShader()
		colorPlug.setValue( IECore.Color3f( 1, 0, 0 ) )

		s["a"] = GafferScene.ShaderAssignment()
		s["a"]["in"].setInput( s["s"]["out"] )
		s["a"]["shader"].setInput( s["shader"]["out"] )

		s["o"] = GafferScene.Outputs()
		s["o"].addOutput(
			"beauty",
			IECore.Display(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ImageDisplayDriver",
					"handle" : "myLovelySphere",
				}
			)
		)
		s["o"]["in"].setInput( s["a"]["out"] )

		s["r"] = self._createInteractiveRender()
		s["r"]["in"].setInput( s["o"]["out"] )

		s["r"]["state"].setValue( s["r"].State.Running )

		time.sleep( 0.5 )

		# Render red sphere

		image = IECore.ImageDisplayDriver.storedImage( "myLovelySphere" )
		self.__assertColorsAlmostEqual( self.__color4fAtUV( image, IECore.V2f( 0.5 ) ), IECore.Color4f( 1, 0, 0, 1 ), delta = 0.01 )

		# Make it green

		colorPlug.setValue( IECore.Color3f( 0, 1, 0 ) )
		time.sleep( 0.5 )

		image = IECore.ImageDisplayDriver.storedImage( "myLovelySphere" )
		self.__assertColorsAlmostEqual( self.__color4fAtUV( image, IECore.V2f( 0.5 ) ), IECore.Color4f( 0, 1, 0, 1 ), delta = 0.01 )

		# Make it blue

		colorPlug.setValue( IECore.Color3f( 0, 0, 1 ) )
		time.sleep( 0.5 )

		image = IECore.ImageDisplayDriver.storedImage( "myLovelySphere" )
		self.__assertColorsAlmostEqual( self.__color4fAtUV( image, IECore.V2f( 0.5 ) ), IECore.Color4f( 0, 0, 1, 1 ), delta = 0.01 )

	def testEditCameraTransform( self ) :

		s = Gaffer.ScriptNode()

		s["s"] = GafferScene.Sphere()
		s["c"] = GafferScene.Camera()

		s["g"] = GafferScene.Group()
		s["g"]["in"][0].setInput( s["s"]["out"] )
		s["g"]["in"][1].setInput( s["c"]["out"] )

		s["outputs"] = GafferScene.Outputs()
		s["outputs"].addOutput(
			"beauty",
			IECore.Display(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ImageDisplayDriver",
					"handle" : "myLovelySphere",
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

		time.sleep( 0.5 )

		# Visible to start with

		image = IECore.ImageDisplayDriver.storedImage( "myLovelySphere" )
		self.assertAlmostEqual( self.__color4fAtUV( image, IECore.V2f( 0.5 ) ).r, 1, delta = 0.01 )

		# Move to one side

		s["c"]["transform"]["translate"]["x"].setValue( 2 )
		time.sleep( 0.5 )

		image = IECore.ImageDisplayDriver.storedImage( "myLovelySphere" )
		self.assertAlmostEqual( self.__color4fAtUV( image, IECore.V2f( 0.5 ) ).r, 0, delta = 0.01 )

		# Move back

		s["c"]["transform"]["translate"]["x"].setValue( 0 )
		time.sleep( 0.5 )

		image = IECore.ImageDisplayDriver.storedImage( "myLovelySphere" )
		self.assertAlmostEqual( self.__color4fAtUV( image, IECore.V2f( 0.5 ) ).r, 1, delta = 0.01 )

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
			IECore.Display(
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

			time.sleep( 0.5 )

			# Use the default resolution to start with

			self.assertEqual(
				IECore.ImageDisplayDriver.storedImage( "myLovelySphere" ).displayWindow,
				IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 639, 479 ) )
			)

			# Now specify a resolution

			s["options"]["options"]["renderResolution"]["enabled"].setValue( True )
			s["options"]["options"]["renderResolution"]["value"].setValue( IECore.V2i( 200, 100 ) )

			time.sleep( 0.5 )

			self.assertEqual(
				IECore.ImageDisplayDriver.storedImage( "myLovelySphere" ).displayWindow,
				IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 199, 99 ) )
			)

			# And specify another resolution

			s["options"]["options"]["renderResolution"]["value"].setValue( IECore.V2i( 300, 100 ) )

			time.sleep( 0.5 )

			self.assertEqual(
				IECore.ImageDisplayDriver.storedImage( "myLovelySphere" ).displayWindow,
				IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 299, 99 ) )
			)

			# And back to the default

			s["options"]["options"]["renderResolution"]["enabled"].setValue( False )

			time.sleep( 0.5 )

			self.assertEqual(
				IECore.ImageDisplayDriver.storedImage( "myLovelySphere" ).displayWindow,
				IECore.Box2i( IECore.V2i( 0 ), IECore.V2i( 639, 479 ) )
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
			IECore.Display(
				"test",
				"ieDisplay",
				"rgba",
				{
					"quantize" : IECore.FloatVectorData( [ 0, 0, 0, 0 ] ),
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
			IECore.Display(
				"test",
				"ieDisplay",
				"rgba",
				{
					"quantize" : IECore.FloatVectorData( [ 0, 0, 0, 0 ] ),
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

		# Change the input to the render node, and check that we don't hang.

		s["o2"] = GafferScene.StandardOptions()
		s["o2"]["in"].setInput( s["o"]["out"] )

		s["r"]["in"].setInput( s["o2"]["out"] )

		# Start the render again, so we know we're not just testing
		# the same thing as testDeleteWhilePaused().
		s["r"]["state"].setValue( s["r"].State.Running )

	def testEditContext( self ) :

		s = Gaffer.ScriptNode()
		s["s"] = GafferScene.Sphere()

		# Sphere moves with time.
		s["e"] = Gaffer.Expression()
		s["e"].setExpression( """parent["s"]["transform"]["translate"]["x"] = context.getFrame() - 1""" )

		s["o"] = GafferScene.Outputs()
		s["o"].addOutput(
			"beauty",
			IECore.Display(
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

		time.sleep( 0.5 )

		# Visible to start with

		image = IECore.ImageDisplayDriver.storedImage( "myLovelySphere" )
		self.assertAlmostEqual( self.__color4fAtUV( image, IECore.V2f( 0.5 ) ).r, 1, delta = 0.01 )

		# Move to one side

		s.context().setFrame( 3 )
		time.sleep( 0.5 )

		image = IECore.ImageDisplayDriver.storedImage( "myLovelySphere" )
		self.assertAlmostEqual( self.__color4fAtUV( image, IECore.V2f( 0.5 ) ).r, 0, delta = 0.01 )

		# Move back

		s.context().setFrame( 1 )
		time.sleep( 0.5 )

		image = IECore.ImageDisplayDriver.storedImage( "myLovelySphere" )
		self.assertAlmostEqual( self.__color4fAtUV( image, IECore.V2f( 0.5 ) ).r, 1, delta = 0.01 )

		# Repeat, using a context we set directly ourselves.

		c = Gaffer.Context()
		c.setFrame( 3 )
		s["r"].setContext( c )
		time.sleep( 0.5 )

		image = IECore.ImageDisplayDriver.storedImage( "myLovelySphere" )
		self.assertAlmostEqual( self.__color4fAtUV( image, IECore.V2f( 0.5 ) ).r, 0, delta = 0.01 )

		c.setFrame( 1 )
		time.sleep( 0.5 )

		image = IECore.ImageDisplayDriver.storedImage( "myLovelySphere" )
		self.assertAlmostEqual( self.__color4fAtUV( image, IECore.V2f( 0.5 ) ).r, 1, delta = 0.01 )

	def testLights( self ) :

		s = Gaffer.ScriptNode()

		s["l"], colorPlug = self._createPointLight()
		colorPlug.setValue( IECore.Color3f( 1, 0.5, 0.25 ) )
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
			IECore.Display(
				"test",
				"ieDisplay",
				"rgba",
				{
					"quantize" : IECore.FloatVectorData( [ 0, 0, 0, 0 ] ),
					"driverType" : "ImageDisplayDriver",
					"handle" : "myLovelyPlane",
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

		time.sleep( 2 )

		c = self.__color3fAtUV(
			IECore.ImageDisplayDriver.storedImage( "myLovelyPlane" ),
			IECore.V2f( 0.5 ),
		)
		self.assertEqual( c / c[0], IECore.Color3f( 1, 0.5, 0.25 ) )

		# Adjust a parameter, give it time to update, and check the output.

		colorPlug.setValue( IECore.Color3f( 0.25, 0.5, 1 ) )

		time.sleep( 1 )

		c = self.__color3fAtUV(
			IECore.ImageDisplayDriver.storedImage( "myLovelyPlane" ),
			IECore.V2f( 0.5 ),
		)
		self.assertEqual( c / c[2], IECore.Color3f( 0.25, 0.5, 1 ) )

		# Pause it, adjust a parameter, wait, and check that nothing changed.

		s["r"]["state"].setValue( s["r"].State.Paused )
		colorPlug.setValue( IECore.Color3f( 1, 0.5, 0.25 ) )

		time.sleep( 1 )

		c = self.__color3fAtUV(
			IECore.ImageDisplayDriver.storedImage( "myLovelyPlane" ),
			IECore.V2f( 0.5 ),
		)
		self.assertEqual( c / c[2], IECore.Color3f( 0.25, 0.5, 1 ) )

		# Unpause it, wait, and check that the update happened.

		s["r"]["state"].setValue( s["r"].State.Running )
		time.sleep( 1 )

		c = self.__color3fAtUV(
			IECore.ImageDisplayDriver.storedImage( "myLovelyPlane" ),
			IECore.V2f( 0.5 ),
		)
		self.assertEqual( c / c[0], IECore.Color3f( 1, 0.5, 0.25 ) )

		# Stop the render, tweak a parameter and check that nothing happened.

		s["r"]["state"].setValue( s["r"].State.Stopped )
		colorPlug.setValue( IECore.Color3f( 0.25, 0.5, 1 ) )
		time.sleep( 1 )

		c = self.__color3fAtUV(
			IECore.ImageDisplayDriver.storedImage( "myLovelyPlane" ),
			IECore.V2f( 0.5 ),
		)
		self.assertEqual( c / c[0], IECore.Color3f( 1, 0.5, 0.25 ) )

	def testAddLight( self ) :

		s = Gaffer.ScriptNode()

		s["l"], colorPlug = self._createPointLight()
		colorPlug.setValue( IECore.Color3f( 1, 0, 0 ) )
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
			IECore.Display(
				"test",
				"ieDisplay",
				"rgba",
				{
					"quantize" : IECore.FloatVectorData( [ 0, 0, 0, 0 ] ),
					"driverType" : "ImageDisplayDriver",
					"handle" : "myLovelyPlane",
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

		time.sleep( 2 )

		c = self.__color3fAtUV(
			IECore.ImageDisplayDriver.storedImage( "myLovelyPlane" ),
			IECore.V2f( 0.5 ),
		)
		self.assertEqual( c / c[0], IECore.Color3f( 1, 0, 0 ) )

		# Add a light

		s["l2"], colorPlug = self._createPointLight()
		colorPlug.setValue( IECore.Color3f( 0, 1, 0 ) )
		s["l2"]["transform"]["translate"]["z"].setValue( 1 )

		s["g"]["in"][3].setInput( s["l2"]["out"] )

		# Give it time to update, and check the output.

		time.sleep( 1 )

		c = self.__color3fAtUV(
			IECore.ImageDisplayDriver.storedImage( "myLovelyPlane" ),
			IECore.V2f( 0.5 ),
		)
		self.assertEqual( c / c[0], IECore.Color3f( 1, 1, 0 ) )

	def testRemoveLight( self ) :

		s = Gaffer.ScriptNode()

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
			IECore.Display(
				"test",
				"ieDisplay",
				"rgba",
				{
					"quantize" : IECore.FloatVectorData( [ 0, 0, 0, 0 ] ),
					"driverType" : "ImageDisplayDriver",
					"handle" : "myLovelyPlane",
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

		time.sleep( 2 )

		c = self.__color3fAtUV(
			IECore.ImageDisplayDriver.storedImage( "myLovelyPlane" ),
			IECore.V2f( 0.5 ),
		)
		self.assertNotEqual( c[0], 0.0 )

		# Remove the light by disabling it.

		s["l"]["enabled"].setValue( False )
		time.sleep( 2 )

		c = self.__color3fAtUV(
			IECore.ImageDisplayDriver.storedImage( "myLovelyPlane" ),
			IECore.V2f( 0.5 ),
		)
		self.assertEqual( c[0], 0.0 )

		# Enable it again.

		s["l"]["enabled"].setValue( True )
		time.sleep( 2 )

		c = self.__color3fAtUV(
			IECore.ImageDisplayDriver.storedImage( "myLovelyPlane" ),
			IECore.V2f( 0.5 ),
		)
		self.assertNotEqual( c[0], 0.0 )

	def testHideLight( self ) :

		s = Gaffer.ScriptNode()

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
			IECore.Display(
				"test",
				"ieDisplay",
				"rgba",
				{
					"quantize" : IECore.FloatVectorData( [ 0, 0, 0, 0 ] ),
					"driverType" : "ImageDisplayDriver",
					"handle" : "myLovelyPlane",
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

		time.sleep( 2 )

		c = self.__color3fAtUV(
			IECore.ImageDisplayDriver.storedImage( "myLovelyPlane" ),
			IECore.V2f( 0.5 ),
		)
		self.assertNotEqual( c[0], 0.0 )

		IECore.EXRImageWriter( IECore.ImageDisplayDriver.storedImage( "myLovelyPlane" ), "/tmp/test1.exr" ).write()

		# Remove the light by hiding it.

		s["v"]["attributes"]["visibility"]["value"].setValue( False )
		time.sleep( 2 )

		c = self.__color3fAtUV(
			IECore.ImageDisplayDriver.storedImage( "myLovelyPlane" ),
			IECore.V2f( 0.5 ),
		)
		self.assertEqual( c[0], 0.0 )

		# Put the light back by showing it.

		s["v"]["attributes"]["visibility"]["value"].setValue( True )
		time.sleep( 2 )

		c = self.__color3fAtUV(
			IECore.ImageDisplayDriver.storedImage( "myLovelyPlane" ),
			IECore.V2f( 0.5 ),
		)

		IECore.EXRImageWriter( IECore.ImageDisplayDriver.storedImage( "myLovelyPlane" ), "/tmp/test2.exr" ).write()

		self.assertNotEqual( c[0], 0.0 )

	def testGlobalAttributes( self ) :

		s = Gaffer.ScriptNode()
		s["s"] = GafferScene.Sphere()

		s["g"] = GafferScene.Group()
		s["g"]["in"].setInput( s["s"]["out"] )

		s["a"] = GafferScene.StandardAttributes()
		s["a"]["in"].setInput( s["g"]["out"] )
		s["a"]["global"].setValue( True )
		s["a"]["attributes"]["visibility"]["enabled"].setValue( True )

		s["o"] = GafferScene.Outputs()
		s["o"].addOutput(
			"beauty",
			IECore.Display(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ImageDisplayDriver",
					"handle" : "myLovelySphere",
				}
			)
		)
		s["o"]["in"].setInput( s["a"]["out"] )

		s["r"] = self._createInteractiveRender()
		s["r"]["in"].setInput( s["o"]["out"] )

		s["r"]["state"].setValue( s["r"].State.Running )

		time.sleep( 0.5 )

		# Visible to start with

		image = IECore.ImageDisplayDriver.storedImage( "myLovelySphere" )
		self.assertAlmostEqual( self.__color4fAtUV( image, IECore.V2f( 0.5 ) ).r, 1, delta = 0.01 )

		# Hide

		s["a"]["attributes"]["visibility"]["value"].setValue( False )
		time.sleep( 0.5 )

		image = IECore.ImageDisplayDriver.storedImage( "myLovelySphere" )
		self.assertAlmostEqual( self.__color4fAtUV( image, IECore.V2f( 0.5 ) ).r, 0, delta = 0.01 )

		# Show again

		s["a"]["attributes"]["visibility"]["value"].setValue( True )
		time.sleep( 0.5 )

		image = IECore.ImageDisplayDriver.storedImage( "myLovelySphere" )
		self.assertAlmostEqual( self.__color4fAtUV( image, IECore.V2f( 0.5 ) ).r, 1, delta = 0.01 )

	def testGlobalCameraVisibility( self ) :

		s = Gaffer.ScriptNode()
		s["s"] = GafferScene.Sphere()

		s["g"] = GafferScene.Group()
		s["g"]["in"].setInput( s["s"]["out"] )

		s["a"] = GafferScene.CustomAttributes()
		s["a"]["in"].setInput( s["g"]["out"] )
		s["a"]["global"].setValue( True )
		visibilityPlug = s["a"]["attributes"].addMember( self._cameraVisibilityAttribute(), True )

		s["o"] = GafferScene.Outputs()
		s["o"].addOutput(
			"beauty",
			IECore.Display(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ImageDisplayDriver",
					"handle" : "myLovelySphere",
				}
			)
		)
		s["o"]["in"].setInput( s["a"]["out"] )

		s["r"] = self._createInteractiveRender()
		s["r"]["in"].setInput( s["o"]["out"] )

		s["r"]["state"].setValue( s["r"].State.Running )

		time.sleep( 0.5 )

		# Visible to start with

		image = IECore.ImageDisplayDriver.storedImage( "myLovelySphere" )
		self.assertAlmostEqual( self.__color4fAtUV( image, IECore.V2f( 0.5 ) ).r, 1, delta = 0.01 )

		# Hide

		visibilityPlug["value"].setValue( False )
		time.sleep( 0.5 )

		image = IECore.ImageDisplayDriver.storedImage( "myLovelySphere" )
		self.assertAlmostEqual( self.__color4fAtUV( image, IECore.V2f( 0.5 ) ).r, 0, delta = 0.01 )

		# Show again

		visibilityPlug["value"].setValue( True )
		time.sleep( 0.5 )

		image = IECore.ImageDisplayDriver.storedImage( "myLovelySphere" )
		self.assertAlmostEqual( self.__color4fAtUV( image, IECore.V2f( 0.5 ) ).r, 1, delta = 0.01 )

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
			IECore.Display(
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
		p = box.promotePlug( box["r"]["in"] )
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

		s["reflector"] = GafferScene.Plane()
		s["reflector"]["name"].setValue( "reflector" )
		s["reflector"]["transform"]["translate"].setValue( IECore.V3f( 0, 0, -1 ) )

		s["reflected"] = GafferScene.Plane()
		s["reflected"]["name"].setValue( "reflected" )
		s["reflected"]["transform"]["translate"].setValue( IECore.V3f( 0, 0, 1 ) )

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
			s["options"]["options"].addMember( o, IECore.IntData( 1 ) )

		s["outputs"] = GafferScene.Outputs()
		s["outputs"].addOutput(
			"beauty",
			IECore.Display(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ImageDisplayDriver",
					"handle" : "traceSetsTest",
				}
			)
		)
		s["outputs"]["in"].setInput( s["options"]["out"] )

		s["render"] = self._createInteractiveRender()
		s["render"]["in"].setInput( s["outputs"]["out"] )
		s["render"]["state"].setValue( s["render"].State.Running )

		time.sleep( 0.5 )

		# We haven't used the trace sets yet, so should be able to see
		# the reflection.

		def assertReflected( reflected ) :

			image = IECore.ImageDisplayDriver.storedImage( "traceSetsTest" )
			self.assertGreater( self.__color4fAtUV( image, IECore.V2f( 0.5 ) ).a, 0.9 )
			if reflected :
				self.assertGreater( self.__color4fAtUV( image, IECore.V2f( 0.5 ) ).r, 0.9 )
			else :
				self.assertLess( self.__color4fAtUV( image, IECore.V2f( 0.5 ) ).r, 0.1 )

		assertReflected( True )

		# Ask to use a trace set. Reflection should disappear because
		# we haven't added anything to the set.

		traceSetParameter.setValue( "myTraceSet" )
		time.sleep( 0.5 )
		assertReflected( False )

		# Now add the reflected object into the set. Reflection should
		# come back.

		s["set"]["paths"].setValue( IECore.StringVectorData( [ "/group/reflected" ] ) )
		time.sleep( 0.5 )
		assertReflected( True )

		# Rename the set so that it's not a trace set any more. Reflection
		# should disappear.

		s["set"]["name"].setValue( "myTraceSet" )
		time.sleep( 0.5 )
		assertReflected( False )

		# Rename the set so that it is a trace set, but with a different namer.
		# Reflection should not reappear.

		s["set"]["name"].setValue( "render:myOtherTraceSet" )
		time.sleep( 0.5 )
		assertReflected( False )

		# Update the shader to use this new trace set. Reflection should
		# reappear.

		traceSetParameter.setValue( "myOtherTraceSet" )
		time.sleep( 0.5 )
		assertReflected( True )

	## Should be implemented by derived classes to return an
	# appropriate InteractiveRender node.
	def _createInteractiveRender( self ) :

		raise NotImplementedError

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

	def __color4fAtUV( self, image, uv ) :

		e = IECore.ImagePrimitiveEvaluator( image )
		r = e.createResult()
		e.pointAtUV( uv, r )

		return IECore.Color4f(
			r.floatPrimVar( image["R"] ),
			r.floatPrimVar( image["G"] ),
			r.floatPrimVar( image["B"] ),
			r.floatPrimVar( image["A"] ),
		)

	def __color3fAtUV( self, image, uv ) :

		e = IECore.ImagePrimitiveEvaluator( image )
		r = e.createResult()
		e.pointAtUV( uv, r )

		return IECore.Color3f(
			r.floatPrimVar( image["R"] ),
			r.floatPrimVar( image["G"] ),
			r.floatPrimVar( image["B"] ),
		)

	def __assertColorsAlmostEqual( self, c0, c1, **kw ) :

		for i in range( 0, 4 ) :
			self.assertAlmostEqual( c0[i], c1[i], **kw )

if __name__ == "__main__":
	unittest.main()
