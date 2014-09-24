##########################################################################
#
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

import unittest
import time
import os

import IECore

import Gaffer
import GafferImage
import GafferScene
import GafferRenderMan
import GafferRenderManTest

@unittest.skipIf( "TRAVIS" in os.environ, "No license available on Travis" )
class InteractiveRenderManRenderTest( GafferRenderManTest.RenderManTestCase ) :

	def __colorAtUV( self, image, uv ) :

		e = IECore.ImagePrimitiveEvaluator( image )
		r = e.createResult()
		e.pointAtUV( uv, r )

		return IECore.Color3f(
			r.floatPrimVar( image["R"] ),
			r.floatPrimVar( image["G"] ),
			r.floatPrimVar( image["B"] ),
		)

	def testLights( self ) :

		s = Gaffer.ScriptNode()

		s["l"] = GafferRenderMan.RenderManLight()
		s["l"].loadShader( "pointlight" )
		s["l"]["parameters"]["lightcolor"].setValue( IECore.Color3f( 1, 0.5, 0.25 ) )
		s["l"]["transform"]["translate"]["z"].setValue( 1 )

		s["p"] = GafferScene.Plane()

		s["c"] = GafferScene.Camera()
		s["c"]["transform"]["translate"]["z"].setValue( 1 )

		s["g"] = GafferScene.Group()
		s["g"]["in"].setInput( s["l"]["out"] )
		s["g"]["in1"].setInput( s["p"]["out"] )
		s["g"]["in2"].setInput( s["c"]["out"] )

		s["s"] = GafferRenderMan.RenderManShader()
		s["s"].loadShader( "matte" )
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

		s["r"] = GafferRenderMan.InteractiveRenderManRender()
		s["r"]["in"].setInput( s["o"]["out"] )

		# start a render, give it time to finish, and check the output

		s["r"]["state"].setValue( s["r"].State.Running )

		time.sleep( 2 )

		c = self.__colorAtUV(
			IECore.ImageDisplayDriver.storedImage( "myLovelyPlane" ),
			IECore.V2f( 0.5 ),
		)
		self.assertEqual( c / c[0], IECore.Color3f( 1, 0.5, 0.25 ) )

		# adjust a parameter, give it time to update, and check the output

		s["l"]["parameters"]["lightcolor"].setValue( IECore.Color3f( 0.25, 0.5, 1 ) )

		time.sleep( 1 )

		c = self.__colorAtUV(
			IECore.ImageDisplayDriver.storedImage( "myLovelyPlane" ),
			IECore.V2f( 0.5 ),
		)
		self.assertEqual( c / c[2], IECore.Color3f( 0.25, 0.5, 1 ) )

		# pause it, adjust a parameter, wait, and check that nothing changed

		s["r"]["state"].setValue( s["r"].State.Paused )
		s["l"]["parameters"]["lightcolor"].setValue( IECore.Color3f( 1, 0.5, 0.25 ) )

		time.sleep( 1 )

		c = self.__colorAtUV(
			IECore.ImageDisplayDriver.storedImage( "myLovelyPlane" ),
			IECore.V2f( 0.5 ),
		)
		self.assertEqual( c / c[2], IECore.Color3f( 0.25, 0.5, 1 ) )

		# unpause it, wait, and check that the update happened

		s["r"]["state"].setValue( s["r"].State.Running )
		time.sleep( 1 )

		c = self.__colorAtUV(
			IECore.ImageDisplayDriver.storedImage( "myLovelyPlane" ),
			IECore.V2f( 0.5 ),
		)
		self.assertEqual( c / c[0], IECore.Color3f( 1, 0.5, 0.25 ) )

		# turn off light updates, adjust a parameter, wait, and check nothing happened

		s["r"]["updateLights"].setValue( False )
		s["l"]["parameters"]["lightcolor"].setValue( IECore.Color3f( 0.25, 0.5, 1 ) )

		time.sleep( 1 )

		c = self.__colorAtUV(
			IECore.ImageDisplayDriver.storedImage( "myLovelyPlane" ),
			IECore.V2f( 0.5 ),
		)
		self.assertEqual( c / c[0], IECore.Color3f( 1, 0.5, 0.25 ) )

		# turn light updates back on and check that it updates

		s["r"]["updateLights"].setValue( True )

		time.sleep( 1 )

		c = self.__colorAtUV(
			IECore.ImageDisplayDriver.storedImage( "myLovelyPlane" ),
			IECore.V2f( 0.5 ),
		)
		self.assertEqual( c / c[2], IECore.Color3f( 0.25, 0.5, 1 ) )

		# stop the render, tweak a parameter and check that nothing happened

		s["r"]["state"].setValue( s["r"].State.Stopped )
		s["l"]["parameters"]["lightcolor"].setValue( IECore.Color3f( 1, 0.5, 0.25 ) )
		time.sleep( 1 )

		c = self.__colorAtUV(
			IECore.ImageDisplayDriver.storedImage( "myLovelyPlane" ),
			IECore.V2f( 0.5 ),
		)
		self.assertEqual( c / c[2], IECore.Color3f( 0.25, 0.5, 1 ) )

	def testShaders( self ) :

		s = Gaffer.ScriptNode()

		s["p"] = GafferScene.Plane()
		s["p"]["transform"]["translate"].setValue( IECore.V3f( -0.1, -0.1, 0 ) )

		s["c"] = GafferScene.Camera()
		s["c"]["transform"]["translate"]["z"].setValue( 1 )

		s["l"] = GafferRenderMan.RenderManLight()
		s["l"].loadShader( "ambientlight" )

		s["g"] = GafferScene.Group()
		s["g"]["in"].setInput( s["p"]["out"] )
		s["g"]["in1"].setInput( s["c"]["out"] )
		s["g"]["in2"].setInput( s["l"]["out"] )

		s["s"] = GafferRenderMan.RenderManShader()
		s["s"].loadShader( "checker" )
		s["s"]["parameters"]["blackcolor"].setValue( IECore.Color3f( 1, 0.5, 0.25 ) )
		s["s"]["parameters"]["Ka"].setValue( 1 )
		s["s"]["parameters"]["frequency"].setValue( 1 )

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

		s["r"] = GafferRenderMan.InteractiveRenderManRender()
		s["r"]["in"].setInput( s["o"]["out"] )

		# start a render, give it time to finish, and check the output

		s["r"]["state"].setValue( s["r"].State.Running )

		time.sleep( 2 )

		c = self.__colorAtUV(
			IECore.ImageDisplayDriver.storedImage( "myLovelyPlane" ),
			IECore.V2f( 0.5 ),
		)
		self.assertEqual( c, IECore.Color3f( 1, 0.5, 0.25 ) )

		# adjust a shader parameter, wait, and check that it changed

		s["s"]["parameters"]["blackcolor"].setValue( IECore.Color3f( 1, 1, 1 ) )
		time.sleep( 1 )
		c = self.__colorAtUV(
			IECore.ImageDisplayDriver.storedImage( "myLovelyPlane" ),
			IECore.V2f( 0.5 ),
		)
		self.assertEqual( c, IECore.Color3f( 1 ) )

		# turn off shader updates, do the same, and check that it hasn't changed

		s["r"]["updateShaders"].setValue( False )
		s["s"]["parameters"]["blackcolor"].setValue( IECore.Color3f( 0.5 ) )
		time.sleep( 1 )
		c = self.__colorAtUV(
			IECore.ImageDisplayDriver.storedImage( "myLovelyPlane" ),
			IECore.V2f( 0.5 ),
		)
		self.assertEqual( c, IECore.Color3f( 1 ) )

		# turn shader updates back on, and check that it updates

		s["r"]["updateShaders"].setValue( True )
		time.sleep( 1 )
		c = self.__colorAtUV(
			IECore.ImageDisplayDriver.storedImage( "myLovelyPlane" ),
			IECore.V2f( 0.5 ),
		)
		self.assertEqual( c, IECore.Color3f( 0.5 ) )

	def testScopesDontLeak( self ) :

		s = Gaffer.ScriptNode()

		s["p"] = GafferScene.Plane()
		s["p"]["transform"]["translate"].setValue( IECore.V3f( -0.6, -0.1, 0 ) )

		s["p1"] = GafferScene.Plane()
		s["p1"]["transform"]["translate"].setValue( IECore.V3f( 0.6, 0.1, 0 ) )

		s["c"] = GafferScene.Camera()
		s["c"]["transform"]["translate"]["z"].setValue( 2 )

		s["l"] = GafferRenderMan.RenderManLight()
		s["l"].loadShader( "ambientlight" )

		s["g"] = GafferScene.Group()
		s["g"]["in"].setInput( s["p"]["out"] )
		s["g"]["in1"].setInput( s["p1"]["out"] )
		s["g"]["in2"].setInput( s["c"]["out"] )
		s["g"]["in3"].setInput( s["l"]["out"] )

		s["s"] = GafferRenderMan.RenderManShader()
		s["s"].loadShader( "checker" )
		s["s"]["parameters"]["blackcolor"].setValue( IECore.Color3f( 1, 0, 0 ) )
		s["s"]["parameters"]["Ka"].setValue( 1 )
		s["s"]["parameters"]["frequency"].setValue( 1 )

		s["f"] = GafferScene.PathFilter()
		s["f"]["paths"].setValue( IECore.StringVectorData( [ "/group/plane" ] ) )

		s["a"] = GafferScene.ShaderAssignment()
		s["a"]["in"].setInput( s["g"]["out"] )
		s["a"]["shader"].setInput( s["s"]["out"] )
		s["a"]["filter"].setInput( s["f"]["match"] )

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
					"handle" : "myLovelyPlanes",
				}
			)
		)
		s["d"]["in"].setInput( s["a"]["out"] )

		s["o"] = GafferScene.StandardOptions()
		s["o"]["options"]["renderCamera"]["value"].setValue( "/group/camera" )
		s["o"]["options"]["renderCamera"]["enabled"].setValue( True )
		s["o"]["options"]["renderResolution"]["value"].setValue( IECore.V2i( 512 ) )
		s["o"]["options"]["renderResolution"]["enabled"].setValue( True )
		s["o"]["in"].setInput( s["d"]["out"] )

		s["r"] = GafferRenderMan.InteractiveRenderManRender()
		s["r"]["in"].setInput( s["o"]["out"] )

		# start a render, give it time to finish, and check the output.
		# we should have a red plane on the left, and a facing ratio
		# shaded plane on the right, because we attached no shader to the
		# second plane.

		s["r"]["state"].setValue( s["r"].State.Running )

		time.sleep( 2 )

		c = self.__colorAtUV(
			IECore.ImageDisplayDriver.storedImage( "myLovelyPlanes" ),
			IECore.V2f( 0.25, 0.5 ),
		)
		self.assertEqual( c, IECore.Color3f( 1, 0, 0 ) )

		c1 = self.__colorAtUV(
			IECore.ImageDisplayDriver.storedImage( "myLovelyPlanes" ),
			IECore.V2f( 0.75, 0.5 ),
		)
		self.assertTrue( c1[0] > 0.9 )
		self.assertEqual( c1[0], c1[1] )
		self.assertEqual( c1[0], c1[2] )

		# adjust a shader parameter, wait, and check that the plane
		# on the left changed. check that the plane on the right didn't
		# change at all.

		s["s"]["parameters"]["blackcolor"].setValue( IECore.Color3f( 0, 1, 0 ) )
		time.sleep( 2 )

		c = self.__colorAtUV(
			IECore.ImageDisplayDriver.storedImage( "myLovelyPlanes" ),
			IECore.V2f( 0.25, 0.5 ),
		)
		self.assertEqual( c, IECore.Color3f( 0, 1, 0 ) )

		c1 = self.__colorAtUV(
			IECore.ImageDisplayDriver.storedImage( "myLovelyPlanes" ),
			IECore.V2f( 0.75, 0.5 ),
		)
		self.assertTrue( c1[0] > 0.9 )
		self.assertEqual( c1[0], c1[1] )
		self.assertEqual( c1[0], c1[2] )

	def testContext( self ):

		s = Gaffer.ScriptNode()

		r = GafferRenderMan.InteractiveRenderManRender()

		self.assertNotEqual( r.getContext(), None )
		self.failIf( r.getContext().isSame( s.context() ) )

		s["r"] = r

		self.failUnless( r.getContext().isSame( s.context() ) )

		s.removeChild( r )

		self.failIf( r.getContext().isSame( s.context() ) )

	def testAddLight( self ) :

		s = Gaffer.ScriptNode()

		s["l"] = GafferRenderMan.RenderManLight()
		s["l"].loadShader( "pointlight" )
		s["l"]["parameters"]["lightcolor"].setValue( IECore.Color3f( 1, 0, 0 ) )
		s["l"]["transform"]["translate"]["z"].setValue( 1 )

		s["p"] = GafferScene.Plane()

		s["c"] = GafferScene.Camera()
		s["c"]["transform"]["translate"]["z"].setValue( 1 )

		s["g"] = GafferScene.Group()
		s["g"]["in"].setInput( s["l"]["out"] )
		s["g"]["in1"].setInput( s["p"]["out"] )
		s["g"]["in2"].setInput( s["c"]["out"] )

		s["s"] = GafferRenderMan.RenderManShader()
		s["s"].loadShader( "matte" )
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

		s["r"] = GafferRenderMan.InteractiveRenderManRender()
		s["r"]["in"].setInput( s["o"]["out"] )

		# start a render, give it time to finish, and check the output

		s["r"]["state"].setValue( s["r"].State.Running )

		time.sleep( 2 )

		c = self.__colorAtUV(
			IECore.ImageDisplayDriver.storedImage( "myLovelyPlane" ),
			IECore.V2f( 0.5 ),
		)
		self.assertEqual( c / c[0], IECore.Color3f( 1, 0, 0 ) )

		# add a light

		s["l2"] = GafferRenderMan.RenderManLight()
		s["l2"].loadShader( "pointlight" )
		s["l2"]["parameters"]["lightcolor"].setValue( IECore.Color3f( 0, 1, 0 ) )
		s["l2"]["transform"]["translate"]["z"].setValue( 1 )

		s["g"]["in3"].setInput( s["l2"]["out"] )

		# give it time to update, and check the output

		time.sleep( 1 )

		c = self.__colorAtUV(
			IECore.ImageDisplayDriver.storedImage( "myLovelyPlane" ),
			IECore.V2f( 0.5 ),
		)
		self.assertEqual( c / c[0], IECore.Color3f( 1, 1, 0 ) )

	def testRemoveLight( self ) :

		s = Gaffer.ScriptNode()

		s["l"] = GafferRenderMan.RenderManLight()
		s["l"].loadShader( "pointlight" )
		s["l"]["transform"]["translate"]["z"].setValue( 1 )

		s["p"] = GafferScene.Plane()

		s["c"] = GafferScene.Camera()
		s["c"]["transform"]["translate"]["z"].setValue( 1 )

		s["g"] = GafferScene.Group()
		s["g"]["in"].setInput( s["l"]["out"] )
		s["g"]["in1"].setInput( s["p"]["out"] )
		s["g"]["in2"].setInput( s["c"]["out"] )

		s["s"] = GafferRenderMan.RenderManShader()
		s["s"].loadShader( "matte" )
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

		s["r"] = GafferRenderMan.InteractiveRenderManRender()
		s["r"]["in"].setInput( s["o"]["out"] )

		# start a render, give it time to finish, and check the output

		s["r"]["state"].setValue( s["r"].State.Running )

		time.sleep( 2 )

		c = self.__colorAtUV(
			IECore.ImageDisplayDriver.storedImage( "myLovelyPlane" ),
			IECore.V2f( 0.5 ),
		)
		self.assertNotEqual( c[0], 0.0 )

		# remove the light by disabling it

		s["l"]["enabled"].setValue( False )
		time.sleep( 2 )

		c = self.__colorAtUV(
			IECore.ImageDisplayDriver.storedImage( "myLovelyPlane" ),
			IECore.V2f( 0.5 ),
		)
		self.assertEqual( c[0], 0.0 )

		# enable it again

		s["l"]["enabled"].setValue( True )
		time.sleep( 2 )

		c = self.__colorAtUV(
			IECore.ImageDisplayDriver.storedImage( "myLovelyPlane" ),
			IECore.V2f( 0.5 ),
		)
		self.assertNotEqual( c[0], 0.0 )

	def testHideLight( self ) :

		s = Gaffer.ScriptNode()

		s["l"] = GafferRenderMan.RenderManLight()
		s["l"].loadShader( "pointlight" )
		s["l"]["transform"]["translate"]["z"].setValue( 1 )

		s["v"] = GafferScene.StandardAttributes()
		s["v"]["attributes"]["visibility"]["enabled"].setValue( True )
		s["v"]["in"].setInput( s["l"]["out"] )

		s["p"] = GafferScene.Plane()

		s["c"] = GafferScene.Camera()
		s["c"]["transform"]["translate"]["z"].setValue( 1 )

		s["g"] = GafferScene.Group()
		s["g"]["in"].setInput( s["v"]["out"] )
		s["g"]["in1"].setInput( s["p"]["out"] )
		s["g"]["in2"].setInput( s["c"]["out"] )

		s["s"] = GafferRenderMan.RenderManShader()
		s["s"].loadShader( "matte" )
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

		s["r"] = GafferRenderMan.InteractiveRenderManRender()
		s["r"]["in"].setInput( s["o"]["out"] )

		# start a render, give it time to finish, and check the output

		s["r"]["state"].setValue( s["r"].State.Running )

		time.sleep( 2 )

		c = self.__colorAtUV(
			IECore.ImageDisplayDriver.storedImage( "myLovelyPlane" ),
			IECore.V2f( 0.5 ),
		)
		self.assertNotEqual( c[0], 0.0 )

		# remove the light by hiding it

		s["v"]["attributes"]["visibility"]["value"].setValue( False )
		time.sleep( 2 )

		c = self.__colorAtUV(
			IECore.ImageDisplayDriver.storedImage( "myLovelyPlane" ),
			IECore.V2f( 0.5 ),
		)
		self.assertEqual( c[0], 0.0 )

		# put the light back by showing it

		s["v"]["attributes"]["visibility"]["value"].setValue( True )
		time.sleep( 2 )

		c = self.__colorAtUV(
			IECore.ImageDisplayDriver.storedImage( "myLovelyPlane" ),
			IECore.V2f( 0.5 ),
		)
		self.assertNotEqual( c[0], 0.0 )

	def testRenderingDuringScriptDeletion( self ) :

		s = Gaffer.ScriptNode()

		s["p"] = GafferScene.Plane()
		s["c"] = GafferScene.Camera()
		s["c"]["transform"]["translate"]["z"].setValue( 1 )

		s["g"] = GafferScene.Group()
		s["g"]["in"].setInput( s["p"]["out"] )
		s["g"]["in1"].setInput( s["c"]["out"] )

		s["d"] = GafferScene.Outputs()
		s["d"].addOutput(
			"beauty",
			IECore.Display(
				"test",
				"ieDisplay",
				"rgba",
				{
					"driverType" : "ClientDisplayDriver",
					"displayHost" : "localhost",
					"displayPort" : "1559",
					"remoteDisplayType" : "GafferImage::GafferDisplayDriver",
					"quantize" : IECore.IntVectorData( [ 0, 0, 0, 0 ] ),
				}
			)
		)

		s["d"]["in"].setInput( s["g"]["out"] )

		s["m"] = GafferImage.Display()

		# connect a python function to the Display node image and data
		# received signals. this emulates what the UI does.
		def __displayCallback( plug ) :
			pass

		c = (
			s["m"].imageReceivedSignal().connect( __displayCallback ),
			s["m"].dataReceivedSignal().connect( __displayCallback ),
		)

		s["o"] = GafferScene.StandardOptions()
		s["o"]["in"].setInput( s["d"]["out"] )
		s["o"]["options"]["renderCamera"]["enabled"].setValue( True )
		s["o"]["options"]["renderCamera"]["value"].setValue( "/group/plane" )

		s["r"] = GafferRenderMan.InteractiveRenderManRender()
		s["r"]["in"].setInput( s["o"]["out"] )

		s["r"]["state"].setValue( s["r"].State.Running )

		time.sleep( 1 )

		# delete the script while the render is still progressing. when
		# this occurs, deletion of the render node will be triggered, which
		# will in turn stop the render. this may flush data to the display,
		# in which case it will emit its data and image received signals
		# on a separate thread. if we're still holding the gil on the main
		# thread when this happens, we'll get a deadlock.
		del s

	def testMoveCamera( self ) :

		s = Gaffer.ScriptNode()

		s["p"] = GafferScene.Plane()

		s["c"] = GafferScene.Camera()
		s["c"]["transform"]["translate"]["z"].setValue( 1 )

		s["g"] = GafferScene.Group()
		s["g"]["in"].setInput( s["p"]["out"] )
		s["g"]["in1"].setInput( s["c"]["out"] )

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

		s["r"] = GafferRenderMan.InteractiveRenderManRender()
		s["r"]["in"].setInput( s["o"]["out"] )

		# start a render, give it time to finish, and check the output

		s["r"]["state"].setValue( s["r"].State.Running )

		time.sleep( 2 )

		c = self.__colorAtUV(
			IECore.ImageDisplayDriver.storedImage( "myLovelyPlane" ),
			IECore.V2f( 0.5 ),
		)
		self.assertAlmostEqual( c[1], 1, delta = 0.001 )

		# move the camera so it can't see the plane, and check the output

		s["c"]["transform"]["translate"]["x"].setValue( 2 )

		time.sleep( 2 )

		c = self.__colorAtUV(
			IECore.ImageDisplayDriver.storedImage( "myLovelyPlane" ),
			IECore.V2f( 0.5 ),
		)
		self.assertAlmostEqual( c[0], 0 )

		# move the camera back and recheck

		s["c"]["transform"]["translate"]["x"].setValue( 0 )

		time.sleep( 2 )

		c = self.__colorAtUV(
			IECore.ImageDisplayDriver.storedImage( "myLovelyPlane" ),
			IECore.V2f( 0.5 ),
		)
		self.assertAlmostEqual( c[1], 1, delta = 0.001 )

	def testMoveCoordinateSystem( self ) :

		shader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/coordSysDot.sl" )

		s = Gaffer.ScriptNode()

		s["plane"] = GafferScene.Plane()

		s["shader"] = GafferRenderMan.RenderManShader()
		s["shader"].loadShader( shader )
		s["shader"]["parameters"]["coordSys"].setValue( "/group/coordinateSystem" )

		s["shaderAssignment"] = GafferScene.ShaderAssignment()
		s["shaderAssignment"]["in"].setInput( s["plane"]["out"] )
		s["shaderAssignment"]["shader"].setInput( s["shader"]["out"] )

		s["camera"] = GafferScene.Camera()
		s["camera"]["transform"]["translate"]["z"].setValue( 1 )

		s["coordSys"] = GafferScene.CoordinateSystem()

		s["g"] = GafferScene.Group()
		s["g"]["in"].setInput( s["shaderAssignment"]["out"] )
		s["g"]["in1"].setInput( s["camera"]["out"] )
		s["g"]["in2"].setInput( s["coordSys"]["out"] )

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

		s["r"] = GafferRenderMan.InteractiveRenderManRender()
		s["r"]["in"].setInput( s["o"]["out"] )

		# start a render, give it time to finish, and check the output

		s["r"]["state"].setValue( s["r"].State.Running )

		time.sleep( 2 )

		c = self.__colorAtUV(
			IECore.ImageDisplayDriver.storedImage( "myLovelyPlane" ),
			IECore.V2f( 0.5 ),
		)
		self.assertAlmostEqual( c[1], 1, delta = 0.001 )

		# move the coordinate system, and check the output

		s["coordSys"]["transform"]["translate"]["x"].setValue( 0.1 )

		time.sleep( 2 )

		c = self.__colorAtUV(
			IECore.ImageDisplayDriver.storedImage( "myLovelyPlane" ),
			IECore.V2f( 0.6, 0.5 ),
		)
		self.assertAlmostEqual( c[0], 1 )

		c = self.__colorAtUV(
			IECore.ImageDisplayDriver.storedImage( "myLovelyPlane" ),
			IECore.V2f( 0.6, 0.7 ),
		)
		self.assertAlmostEqual( c[0], 0 )

		# scale the coordinate system to cover everything, and check again

		s["coordSys"]["transform"]["scale"].setValue( IECore.V3f( 100 ) )

		time.sleep( 2 )

		for p in [
			IECore.V2f( 0.5 ),
			IECore.V2f( 0.1 ),
			IECore.V2f( 0.9 ),
		] :
			c = self.__colorAtUV(
				IECore.ImageDisplayDriver.storedImage( "myLovelyPlane" ),
				p,
			)
			self.assertAlmostEqual( c[0], 1, delta = 0.001 )

if __name__ == "__main__":
	unittest.main()
