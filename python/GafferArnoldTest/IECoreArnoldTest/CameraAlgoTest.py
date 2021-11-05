##########################################################################
#
#  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#
#     * Neither the name of Image Engine Design nor the names of any
#       other contributors to this software may be used to endorse or
#       promote products derived from this software without specific prior
#       written permission.
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

import math
import random
import unittest

import arnold

import IECore
import IECoreScene

import imath

from GafferArnold.Private import IECoreArnold

class CameraAlgoTest( unittest.TestCase ) :

	def testConvertPerspective( self ) :

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			c = IECoreScene.Camera(
				parameters = {
					"projection" : "perspective",
					"focalLength" : 1 / ( 2.0 * math.tan( 0.5 * math.radians( 45 ) ) ),
					"resolution" : imath.V2i( 512 ),
					"aperture" : imath.V2f( 2, 1 )
				}
			)

			n = IECoreArnold.NodeAlgo.convert( c, universe, "testCamera" )
			screenWindow = c.frustum()

			self.assertTrue( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( n ) ), "persp_camera" )

			screenWindowMult = math.tan( 0.5 * math.radians( arnold.AiNodeGetFlt( n, "fov" ) ) )

			self.assertAlmostEqual( screenWindowMult * arnold.AiNodeGetVec2( n, "screen_window_min" ).x, screenWindow.min()[0], 6 )
			self.assertAlmostEqual( screenWindowMult * arnold.AiNodeGetVec2( n, "screen_window_min" ).y, screenWindow.min()[1], 6 )
			self.assertAlmostEqual( screenWindowMult * arnold.AiNodeGetVec2( n, "screen_window_max" ).x, screenWindow.max()[0], 6 )
			self.assertAlmostEqual( screenWindowMult * arnold.AiNodeGetVec2( n, "screen_window_max" ).y, screenWindow.max()[1], 6 )

			# For perspective cameras, we set a FOV value that drives the effective screen window.
			# As long as pixels aren't distorted, and there is no aperture offset,
			# applying Arnold's automatic screen window computation to a default screen window
			# should give us the correct result
			self.assertEqual( arnold.AiNodeGetVec2( n, "screen_window_min" ).x, -1.0 )
			self.assertEqual( arnold.AiNodeGetVec2( n, "screen_window_min" ).y, -1.0 )
			self.assertEqual( arnold.AiNodeGetVec2( n, "screen_window_max" ).x, 1.0 )
			self.assertEqual( arnold.AiNodeGetVec2( n, "screen_window_max" ).y, 1.0 )

	def testConvertCustomProjection( self ) :

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			n = IECoreArnold.NodeAlgo.convert(
				IECoreScene.Camera(
					parameters = {
						"projection" : "cyl_camera",
						"horizontal_fov" : 45.0,
						"vertical_fov" : 80.0,
					}
				),
				universe,
				"testCamera"
			)

			self.assertTrue( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( n ) ), "cyl_camera" )
			self.assertEqual( arnold.AiNodeGetFlt( n, "horizontal_fov" ), 45.0 )
			self.assertEqual( arnold.AiNodeGetFlt( n, "vertical_fov" ), 80.0 )

	# This test makes sure that for a camera with no focal length defined, but with a fov, the default
	# focal length calculation on the camera results in getting the same projection in Arnold that we
	# had before.
	def testOldRandomCamera( self ) :

		random.seed( 42 )

		with IECoreArnold.UniverseBlock( writable = True ) as universe :
			for i in range( 40 ):
				resolution = imath.V2i( random.randint( 10, 1000 ), random.randint( 10, 1000 ) )
				pixelAspectRatio = random.uniform( 0.5, 2 )
				screenWindow = imath.Box2f(
							imath.V2f( -random.uniform( 0, 2 ), -random.uniform( 0, 2 ) ),
							imath.V2f(  random.uniform( 0, 2 ), random.uniform( 0, 2 ) )
						)

				screenWindowAspectScale = imath.V2f( 1.0, ( screenWindow.size()[0] / screenWindow.size()[1] ) * ( resolution[1] / float(resolution[0]) ) / pixelAspectRatio )
				screenWindow.setMin( screenWindow.min() * screenWindowAspectScale )
				screenWindow.setMax( screenWindow.max() * screenWindowAspectScale )

				c = IECoreScene.Camera(
					parameters = {
						"projection" : "orthographic" if random.random() > 0.5 else "perspective",
						"projection:fov" : random.uniform( 1, 100 ),
						"clippingPlanes" : imath.V2f( random.uniform( 0.001, 100 ) ) + imath.V2f( 0, random.uniform( 0, 1000 ) ),
						"resolution" : resolution,
						"pixelAspectRatio" : pixelAspectRatio
					}
				)

				if i < 20:
					c.parameters()["screenWindow"] = screenWindow

				n = IECoreArnold.NodeAlgo.convert( c, universe, "testCamera" )

				arnoldType = "persp_camera"
				if c.parameters()["projection"].value == "orthographic":
					arnoldType = "ortho_camera"

				self.assertEqual( arnold.AiNodeEntryGetName( arnold.AiNodeGetNodeEntry( n ) ), arnoldType )

				cortexClip = c.parameters()["clippingPlanes"].value
				self.assertEqual( arnold.AiNodeGetFlt( n, "near_clip" ), cortexClip[0] )
				self.assertEqual( arnold.AiNodeGetFlt( n, "far_clip" ), cortexClip[1] )

				resolution = c.parameters()["resolution"].value
				aspect = c.parameters()["pixelAspectRatio"].value * resolution.x / float(resolution.y)

				if "screenWindow" in c.parameters():
					cortexWindow = c.parameters()["screenWindow"].value
				else:
					if aspect > 1.0:
						cortexWindow = imath.Box2f( imath.V2f( -aspect, -1 ), imath.V2f( aspect, 1 ) )
					else:
						cortexWindow = imath.Box2f( imath.V2f( -1, -1 / aspect ), imath.V2f( 1, 1 / aspect ) )


				if c.parameters()["projection"].value != "orthographic":
					windowScale = math.tan( math.radians( 0.5 * arnold.AiNodeGetFlt( n, "fov" ) ) )
					cortexWindowScale = math.tan( math.radians( 0.5 * c.parameters()["projection:fov"].value ) )
				else:
					windowScale = 1.0
					cortexWindowScale = 1.0

				self.assertAlmostEqual( windowScale * arnold.AiNodeGetVec2( n, "screen_window_min" ).x, cortexWindowScale * cortexWindow.min()[0], places = 4 )
				self.assertAlmostEqual( windowScale * arnold.AiNodeGetVec2( n, "screen_window_min" ).y, cortexWindowScale * cortexWindow.min()[1] * aspect, places = 4 )
				self.assertAlmostEqual( windowScale * arnold.AiNodeGetVec2( n, "screen_window_max" ).x, cortexWindowScale * cortexWindow.max()[0], places = 4 )
				self.assertAlmostEqual( windowScale * arnold.AiNodeGetVec2( n, "screen_window_max" ).y, cortexWindowScale * cortexWindow.max()[1] * aspect, places = 4 )

				if c.parameters()["projection"].value == "perspective":
					self.assertAlmostEqual( arnold.AiNodeGetVec2( n, "screen_window_max" ).x - arnold.AiNodeGetVec2( n, "screen_window_min" ).x, 2.0, places = 6 )
					self.assertAlmostEqual( arnold.AiNodeGetVec2( n, "screen_window_max" ).y - arnold.AiNodeGetVec2( n, "screen_window_min" ).y, 2.0, places = 6 )

	def testConvertAnimatedParameters( self ) :

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			samples = []
			for i in range( 0, 2 ) :
				camera = IECoreScene.Camera()
				camera.setProjection( "perspective" )
				camera.setFocalLengthFromFieldOfView( 45 * ( i + 1 ) )
				camera.setAperture( imath.V2f( 10, 10 + i ) )
				camera.setFStop( i + 1 )
				camera.setFocusDistance( i + 100 )
				samples.append( camera )

			animatedNode = IECoreArnold.NodeAlgo.convert( samples, 1.0, 2.0, universe, "samples" )
			nodes = [ IECoreArnold.NodeAlgo.convert( samples[i], universe, "sample{}".format( i ) ) for i, sample in enumerate( samples ) ]

			self.assertEqual( arnold.AiNodeGetFlt( animatedNode, "motion_start" ), 1.0 )
			self.assertEqual( arnold.AiNodeGetFlt( animatedNode, "motion_start" ), 1.0 )

			for i, node in enumerate( nodes ) :

				animatedScreenWindowMin = arnold.AiArrayGetVec2(
					arnold.AiNodeGetArray( animatedNode, "screen_window_min" ), i
				)
				animatedScreenWindowMax = arnold.AiArrayGetVec2(
					arnold.AiNodeGetArray( animatedNode, "screen_window_max" ), i
				)

				self.assertEqual( animatedScreenWindowMin.x, arnold.AiNodeGetVec2( node, "screen_window_min" ).x )
				self.assertEqual( animatedScreenWindowMin.y, arnold.AiNodeGetVec2( node, "screen_window_min" ).y )
				self.assertEqual( animatedScreenWindowMax.x, arnold.AiNodeGetVec2( node, "screen_window_max" ).x )
				self.assertEqual( animatedScreenWindowMax.y, arnold.AiNodeGetVec2( node, "screen_window_max" ).y )

				self.assertEqual(
					arnold.AiArrayGetFlt(
						arnold.AiNodeGetArray( animatedNode, "fov" ), i
					),
					arnold.AiNodeGetFlt( node, "fov" )
				)

				self.assertEqual(
					arnold.AiArrayGetFlt(
						arnold.AiNodeGetArray( animatedNode, "aperture_size" ), i
					),
					arnold.AiNodeGetFlt( node, "aperture_size" )
				)

				self.assertEqual(
					arnold.AiArrayGetFlt(
						arnold.AiNodeGetArray( animatedNode, "focus_distance" ), i
					),
					arnold.AiNodeGetFlt( node, "focus_distance" )
				)

			for parameter in [
				"screen_window_min",
				"screen_window_max",
				"fov",
				"aperture_size",
				"focus_distance",
			] :

				array = arnold.AiNodeGetArray( animatedNode, "fov" )
				self.assertEqual( arnold.AiArrayGetNumElements( array ), 1 )
				self.assertEqual( arnold.AiArrayGetNumKeys( array ), 2 )

	def testSampleDeduplication( self ) :

		camera = IECoreScene.Camera()
		camera.setProjection( "perspective" )

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			animatedNode = IECoreArnold.NodeAlgo.convert( [ camera, camera ], 1.0, 2.0, universe, "samples" )
			node = IECoreArnold.NodeAlgo.convert( camera, universe, "sample" )

			for parameter in [
				"screen_window_min",
				"screen_window_max",
				"fov",
				"aperture_size",
				"focus_distance",
			] :

				if parameter.startswith( "screen_" ) :
					self.assertEqual(
						arnold.AiNodeGetVec2( animatedNode, parameter ).x,
						arnold.AiNodeGetVec2( node, parameter ).x
					)
					self.assertEqual(
						arnold.AiNodeGetVec2( animatedNode, parameter ).y,
						arnold.AiNodeGetVec2( node, parameter ).y
					)
				else :
					self.assertEqual(
						arnold.AiNodeGetFlt( animatedNode, parameter ),
						arnold.AiNodeGetFlt( node, parameter )
					)

				array = arnold.AiNodeGetArray( animatedNode, parameter )
				self.assertEqual( arnold.AiArrayGetNumElements( array ), 1 )
				self.assertEqual( arnold.AiArrayGetNumKeys( array ), 1 )

	def testConvertShutterCurve( self ) :

		with IECoreArnold.UniverseBlock( writable = True ) as universe :

			camera = IECoreScene.Camera()
			camera.setProjection( "perspective" )
			camera.parameters()["shutter_curve"] = IECore.Splineff(
				IECore.CubicBasisf.linear(),
				[
					( 0, -0.1 ),
					( 0.25, 1 ),
					( 0.75, 1.1 ),
					( 1.1, 0 ),
				],
			)

			node = IECoreArnold.NodeAlgo.convert( camera, universe, "camera" )
			curve = arnold.AiNodeGetArray( node, "shutter_curve" )
			self.assertEqual( arnold.AiArrayGetNumElements( curve ), 4 )
			self.assertEqual( arnold.AiArrayGetVec2( curve, 0 ), arnold.AtVector2( 0, 0 ) )
			self.assertEqual( arnold.AiArrayGetVec2( curve, 1 ), arnold.AtVector2( 0.25, 1 ) )
			self.assertEqual( arnold.AiArrayGetVec2( curve, 2 ), arnold.AtVector2( 0.75, 1 ) )
			self.assertEqual( arnold.AiArrayGetVec2( curve, 3 ), arnold.AtVector2( 1, 0 ) )

			camera.parameters()["shutter_curve"] = IECore.Splineff(
				IECore.CubicBasisf.catmullRom(),
				[
					( 0, 0 ),
					( 0, 0 ),
					( 0.25, 1 ),
					( 0.75, 1 ),
					( 1, 0 ),
					( 1, 0 ),
				],
			)

			node = IECoreArnold.NodeAlgo.convert( camera, universe, "camera" )
			curve = arnold.AiNodeGetArray( node, "shutter_curve" )
			self.assertEqual( arnold.AiArrayGetNumElements( curve ), 25 )
			for i in range( 0, 25 ) :
				point = arnold.AiArrayGetVec2( curve, i )
				self.assertAlmostEqual(
					min( camera.parameters()["shutter_curve"].value( point.x ), 1 ),
					point.y,
					delta = 0.0001
				)

if __name__ == "__main__":
	unittest.main()
