##########################################################################
#
#  Copyright (c) 2023, Image Engine Design Inc. All rights reserved.
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
import imath

import IECore

import Gaffer
import GafferScene
import GafferSceneTest

import math
import random

class FramingConstraintTest( GafferSceneTest.SceneTestCase ) :

	def testBasics( self ) :

		cube = GafferScene.Cube()

		cubeGroup = GafferScene.Group()
		cubeGroup["in"][0].setInput( cube["out"] )

		camera = GafferScene.Camera()
		camera["fieldOfView"].setValue( 90.0 )

		group = GafferScene.Group()
		group["in"][0].setInput( cubeGroup["out"] )
		group["in"][1].setInput( camera["out"] )

		standardOptions = GafferScene.StandardOptions()
		standardOptions["in"].setInput( group["out"] )
		standardOptions["options"]["renderResolution"]["enabled"].setValue( True )
		standardOptions["options"]["renderResolution"]["value"].setValue( imath.V2i( 1024 ) )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/group/camera" ] ) )

		framing = GafferScene.FramingConstraint()
		framing["in"].setInput( standardOptions["out"] )
		framing["filter"].setInput( filter["out"] )
		framing["boundMode"].setValue( "box" )

		# Without a target, does nothing
		self.assertEqual( framing["out"].transform( "/group/camera" ), imath.M44f() )

		# Basic frame
		framing["target"].setValue( "/group/group/cube" )
		self.assertEqual( framing["out"].transform( "/group/camera" ), imath.M44f().translate( imath.V3f( 0, 0, 1 ) ) )

		# Test effect of resolution globals
		standardOptions["options"]["renderResolution"]["value"].setValue( imath.V2i( 1024, 512 ) )
		self.assertEqual( framing["out"].transform( "/group/camera" ), imath.M44f().translate( imath.V3f( 0, 0, 1.5 ) ) )
		standardOptions["options"]["renderResolution"]["value"].setValue( imath.V2i( 1024 ) )

		# Track cube that is transformed
		cube["transform"]["translate"].setValue( imath.V3f( 1, 0, 0 ) )
		self.assertEqual( framing["out"].transform( "/group/camera" ), imath.M44f().translate( imath.V3f( 1, 0, 1 ) ) )

		# Test effect of target size
		cube["dimensions"].setValue( imath.V3f( 2 ) )
		self.assertEqual( framing["out"].transform( "/group/camera" ), imath.M44f().translate( imath.V3f( 1, 0, 2 ) ) )


		# Test evaluating target bound at parent location
		framing["target"].setValue( "/group/group" )
		self.assertEqual( framing["out"].transform( "/group/camera" ), imath.M44f().translate( imath.V3f( 1, 0, 2 ) ) )
		framing["target"].setValue( "/group/group/cube" )
		cube["dimensions"].setValue( imath.V3f( 1 ) )

		# Track cube that is transformed by parent
		cubeGroup["transform"]["translate"].setValue( imath.V3f( 0, 1, 0 ) )
		self.assertLess( ( framing["out"].transform( "/group/camera" ).translation() - imath.V3f( 1, 1, 1 ) ).length(), 2e-6 )

		# Translating camera does nothing
		camera["transform"]["translate"].setValue( imath.V3f( 22 ) )
		self.assertLess( ( framing["out"].transform( "/group/camera" ).translation() - imath.V3f( 1, 1, 1 ) ).length(), 2e-6 )

		# Rotating camera changes angle
		camera["transform"]["rotate"].setValue( imath.V3f( 0, 90, 0 ) )
		self.assertLess( ( framing["out"].transform( "/group/camera" ).translation() - imath.V3f( 2, 1, 0 ) ).length(), 2e-6 )

		# Transforming the top level transform doesn't change the local transform of the camera
		group["transform"]["rotate"].setValue( imath.V3f( 0, -90, 0 ) )
		self.assertLess( ( framing["out"].transform( "/group/camera" ).translation() - imath.V3f( 2, 1, 0 ) ).length(), 2e-6 )
		group["transform"]["translate"].setValue( imath.V3f( 22 ) )
		self.assertLess( ( framing["out"].transform( "/group/camera" ).translation() - imath.V3f( 2, 1, 0 ) ).length(), 2e-6 )
		group["transform"]["rotate"].setValue( imath.V3f( 0, 0, 0 ) )
		self.assertLess( ( framing["out"].transform( "/group/camera" ).translation() - imath.V3f( 2, 1, 0 ) ).length(), 2e-6 )


		# Test targetScene
		group["transform"]["translate"].setValue( imath.V3f( 0) )
		camera["transform"]["rotate"].setValue( imath.V3f( 0 ) )

		framing["target"].setValue( "/group/cube" )
		with self.assertRaisesRegex( RuntimeError, "FramingConstraint target does not exist: \"/group/cube\". Use 'ignoreMissingTarget' option if you want to just skip this constraint" ) :
			framing["out"].transform( "/group/camera" )

		framing["targetScene"].setInput( cubeGroup["out"] )
		self.assertEqual( framing["out"].transform( "/group/camera" ), imath.M44f().translate( imath.V3f( 1, 1, 1 ) ) )

		# Test bound mode
		framing["boundMode"].setValue( "sphere" )
		self.assertLess( ( framing["out"].transform( "/group/camera" ).translation() - imath.V3f( 1, 1, 1.5 ** 0.5 ) ).length(), 2e-6 )
		framing["boundMode"].setValue( "box" )

		# Test padding
		framing["padding"].setValue( 0.5 )
		self.assertEqual( framing["out"].transform( "/group/camera" ), imath.M44f().translate( imath.V3f( 1, 1, 1.5 ) ) )
		framing["padding"].setValue( -1 )
		self.assertEqual( framing["out"].transform( "/group/camera" ), imath.M44f().translate( imath.V3f( 1, 1, 0.75 ) ) )
		framing["padding"].setValue( 0 )

		# Test clipping planes
		camera['clippingPlanes'].setValue( imath.V2f( 5, 5.001 ) )

		self.assertEqual( framing["out"].transform( "/group/camera" ), imath.M44f().translate( imath.V3f( 1, 1, 5.5 ) ) )
		self.assertEqual( framing["out"].object( "/group/camera" ).getClippingPlanes() , imath.V2f( imath.V2f( 5, 6 ) ) )
		framing["extendFarClip"].setValue( False )
		self.assertEqual( framing["out"].object( "/group/camera" ).getClippingPlanes() , imath.V2f( imath.V2f( 5, 5.001 ) ) )

		# Test ortho camera
		camera['projection'].setValue( "orthographic" )
		camera['clippingPlanes'].setValue( imath.V2f( 0.125, 0.5 ) )
		self.assertEqual( framing["out"].transform( "/group/camera" ), imath.M44f().translate( imath.V3f( 1, 1, 0.625 ) ) )
		self.assertEqual( framing["out"].object( "/group/camera" ).getClippingPlanes() , imath.V2f( imath.V2f( 0.125, 0.5 ) ) )
		self.assertEqual( framing["out"].object( "/group/camera" ).getAperture() , imath.V2f( 1 ) )

		framing["extendFarClip"].setValue( True )

		self.assertEqual( framing["out"].object( "/group/camera" ).getClippingPlanes() , imath.V2f( imath.V2f( 0.125, 1.125 ) ) )

		cube["dimensions"].setValue( imath.V3f( 3 ) )
		self.assertEqual( framing["out"].transform( "/group/camera" ), imath.M44f().translate( imath.V3f( 1, 1, 1.625 ) ) )
		self.assertEqual( framing["out"].object( "/group/camera" ).getClippingPlanes() , imath.V2f( imath.V2f( 0.125, 3.125 ) ) )
		self.assertEqual( framing["out"].object( "/group/camera" ).getAperture(), imath.V2f( 3 ) )

		framing["padding"].setValue( 0.5 )
		self.assertEqual( framing["out"].object( "/group/camera" ).getAperture(), imath.V2f( 6 ) )
		framing["padding"].setValue( 0 )

		# Test targetFrame
		cube["expr"] = Gaffer.Expression()
		cube["expr"].setExpression( 'parent["transform"]["translate"] = imath.V3f( 0, context.getFrame(), 0 )' )

		cubeGroup["transform"]["translate"].setValue( imath.V3f( 0 ) )

		c = Gaffer.Context()
		with c:
			c.setFrame( 2 )
			self.assertEqual( framing["out"].transform( "/group/camera" ), imath.M44f().translate( imath.V3f( 0, 2, 1.625 ) ) )
			framing["useTargetFrame"].setValue( True )
			self.assertEqual( framing["out"].transform( "/group/camera" ), imath.M44f().translate( imath.V3f( 0, 0, 1.625 ) ) )
			cube["expr2"] = Gaffer.Expression()
			cube["expr2"].setExpression( 'parent["enabled"] = context.getFrame() > 1' )

			with self.assertRaisesRegex( RuntimeError, "FramingConstraint target does not exist: \"/group/cube\". Use 'ignoreMissingTarget' option if you want to just skip this constraint" ) :
				framing["out"].transform( "/group/camera" )

			framing["targetFrame"].setValue( 5 )
			self.assertEqual( framing["out"].transform( "/group/camera" ), imath.M44f().translate( imath.V3f( 0, 5, 1.625 ) ) )

	def testRandomValues( self ) :

		random.seed( 42 )

		def r3( a, b ):
			return imath.V3f( random.uniform( a, b ), random.uniform( a, b ), random.uniform( a, b ) )

		cube = GafferScene.Cube()

		cubeFilter = GafferScene.PathFilter()
		cubeFilter["paths"].setValue( IECore.StringVectorData( [ "/cube" ] ) )

		freezeTransform = GafferScene.FreezeTransform()
		freezeTransform["in"].setInput( cube["out"] )
		freezeTransform["filter"].setInput( cubeFilter["out"] )

		cubeTransform = GafferScene.Transform()
		cubeTransform["in"].setInput( freezeTransform["out"] )
		cubeTransform["filter"].setInput( cubeFilter["out"] )

		camera = GafferScene.Camera()

		sphere = GafferScene.Sphere()

		group = GafferScene.Group()
		group["in"][0].setInput( cubeTransform["out"] )
		group["in"][1].setInput( camera["out"] )
		group["in"][2].setInput( sphere["out"] )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/group/camera" ] ) )

		cameraTweaks = GafferScene.CameraTweaks()
		cameraTweaks["in"].setInput( group["out"] )
		cameraTweaks["filter"].setInput( filter["out"] )
		cameraTweaks["tweaks"]["resolution"] = Gaffer.TweakPlug( "resolution", Gaffer.V2iPlug( "value" ) )
		cameraTweaks["tweaks"]["apertureOffset"] = Gaffer.TweakPlug( "apertureOffset", Gaffer.V2fPlug( "value" ) )

		framing = GafferScene.FramingConstraint()
		framing["in"].setInput( cameraTweaks["out"] )
		framing["filter"].setInput( filter["out"] )
		framing["target"].setValue( "/group/cube" )

		minThresh = 0.99999
		maxThresh = 1.00001

		def validateFrustumUsage( target, minUsed, maxUsed, centerTolerance, depthTolerance, matchNear ):
			targetToCam = framing["out"].transform( target ) * framing["out"].transform( "/group/camera" ).inverse()
			cam = framing["out"].object( "/group/camera" )
			frustum = cam.frustum()
			ortho = cam.getProjection() == "orthographic"
			usedFrustum = imath.Box2f()
			minDepth = math.inf
			maxDepth = -math.inf
			for p in framing["out"].object( target )["P"].data:
				camP = p * targetToCam
				if ortho:
					usedFrustum.extendBy( imath.V2f( camP[0], camP[1] ) )
				else:
					usedFrustum.extendBy( -imath.V2f( camP[0], camP[1] ) / camP[2] )
				minDepth = min( minDepth, -camP[2] )
				maxDepth = max( maxDepth, -camP[2] )

			relativeUsed = imath.Box2f(
				( usedFrustum.min() - frustum.center() ) / ( frustum.max() - frustum.center() ),
				( usedFrustum.max() - frustum.center() ) / ( frustum.max() - frustum.center() )
			)

			self.assertLess(
				max( [ -relativeUsed.min().x, -relativeUsed.min().y, relativeUsed.max().x, relativeUsed.max().y ] ),
				maxUsed
			)
			self.assertGreater( max( relativeUsed.size().x, relativeUsed.size().y ), 2 * minUsed )

			self.assertLess( max( abs( relativeUsed.center().x ), abs( relativeUsed.center().y ) ), centerTolerance )

			# Far clip should exactly match farthest part of target, because we are setting it
			# low to start with and using extendFarClip
			self.assertLess( maxDepth, cam.getClippingPlanes().y + depthTolerance )
			self.assertGreater( maxDepth, cam.getClippingPlanes().y - depthTolerance )

			# Near clip must at least enclose target
			self.assertGreater( minDepth, cam.getClippingPlanes().x - depthTolerance )

			# Or match exactly if specified
			if matchNear:
				self.assertLess( minDepth, cam.getClippingPlanes().x + depthTolerance )

		for boundMode in [ "sphere", "box" ]:
			framing["boundMode"].setValue( boundMode )
			for projection in [ "perspective", "orthographic" ]:
				camera["projection"].setValue( projection )
				for i in range( 100 ):
					with self.subTest( boundMode = boundMode, projection = projection, i = i ):
						camera["clippingPlanes"].setValue( imath.V2f( 0.0001, 0.0001 ) )

						cube["dimensions"].setValue( r3( 0.1, 3 ) )

						# An offset before the FreezeTransform will test that we are correctly handling
						# non-centered bounds
						cube["transform"]["translate"].setValue( r3( -1, 1 ) )

						cubeTransform["transform"]["translate"].setValue( r3( -4, 4 ) )
						cubeTransform["transform"]["rotate"].setValue( r3( -360, 360 ) )
						cubeTransform["transform"]["scale"].setValue( r3( 0.1, 3 ) )

						camera["transform"]["translate"].setValue( r3( -4, 4 ) )
						camera["transform"]["rotate"].setValue( r3( -360, 360 ) )
						camera["transform"]["scale"].setValue( imath.V3f( random.uniform( 0.5, 1.5 ) ) )


						if boundMode == "sphere":
							cubeTrans = group["out"].transform( "/group/cube" )
							cubeBound = group["out"].bound( "/group/cube" )
							center = cubeBound.center() * cubeTrans
							sphere["transform"]["translate"].setValue( center )
							sphere["radius"].setValue( ( cubeBound.min() * cubeTrans- center ).length() )

						cameraTweaks["tweaks"]["resolution"]["value"].setValue(
							imath.V2i( 1000, random.randint( 500, 2000 ) )
						)
						cameraTweaks["tweaks"]["apertureOffset"]["value"].setValue(
							imath.V2f( random.uniform( -1, 1 ), random.uniform( -1, 1 ) )
						)

						# Check that the target object doesn't exceed the frustum, but also that it uses
						# up the entire frustum on one axis or the other.

						# Note that the 4th parameter, the tolerance for where the center is, is quite large,
						# only checking that the center of the target is within 25% of the center of the frustum.
						# It might make sense to actually center the image exactly on the unconstrained axis, but the
						# current approach instead makes the distance to the frustum in world space equal on both
						# sides of the frustum. This is very close to centering the object in the frame in common
						# cases, but if the object is much closer in Z on one side than the other, this means that the
						# gap to the frustum appears much larger on one side than the other. I've kept the current
						# behaviour because improving it would require a second pass over the target, and it's
						# unclear if making the borders equal in screen space would actually be an improvement ...
						# we are already filling as much of the image as we can, and having the nearer part of the
						# object closer to the center of frame might actually be desirable in some cases.

						if boundMode != "sphere":
							validateFrustumUsage( "/group/cube", 0.99999, 1.00002, 0.25, 0.000005, False )
						else:
							# Testing using a polygon sphere instead of an analytic sphere means we need to accept
							# a slightly lower tolerance for how much we fill the frustum
							validateFrustumUsage( "/group/sphere", 0.99, 1.00002, 0.25, 0.04, False )


						# If we set a large near clip, then the camera will have to back up a lot.
						# We no longer fill the whole frustum, but the target still be close to center,
						# and the near clip now matches
						camera["clippingPlanes"].setValue( imath.V2f( 20, 20.0001 ) )
						if boundMode != "sphere":
							validateFrustumUsage( "/group/cube", 0.03, 1.00002, 0.2, 0.00001, True )
						else:
							validateFrustumUsage( "/group/sphere", 0.03, 1.00002, 0.2, 0.04, True )

	def testConstrainingGeometry( self ) :

		cube = GafferScene.Cube()
		plane = GafferScene.Plane()

		parent = GafferScene.Parent()
		parent["in"].setInput( cube["out"] )
		parent["children"][0].setInput( plane["out"] )

		planeFilter = GafferScene.PathFilter()
		planeFilter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		constraint = GafferScene.FramingConstraint()
		constraint["in"].setInput( parent["out"] )
		constraint["filter"].setInput( planeFilter["out"] )
		constraint["target"].setValue( "/cube" )

		self.assertEqual( constraint["out"].fullTransform( "/plane" ), constraint["in"].fullTransform( "/plane" ) )

if __name__ == "__main__":
	unittest.main()
