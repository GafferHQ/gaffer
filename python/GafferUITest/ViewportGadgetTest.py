##########################################################################
#
#  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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
import IECoreScene

import GafferTest
import GafferUI
import GafferUITest

class ViewportGadgetTest( GafferUITest.TestCase ) :

	def testViewportChangedSignal( self ) :

		v = GafferUI.ViewportGadget()

		cs = GafferTest.CapturingSlot( v.viewportChangedSignal() )

		v.setViewport( v.getViewport() )
		self.assertEqual( len( cs ), 0 )

		v.setViewport( v.getViewport() + imath.V2i( 10 ) )
		self.assertEqual( len( cs ), 1 )
		self.assertEqual( cs[0], ( v, ) )

		v.setViewport( v.getViewport() )
		self.assertEqual( len( cs ), 1 )

	def testCameraChangedSignal( self ) :

		v = GafferUI.ViewportGadget()

		cs = GafferTest.CapturingSlot( v.cameraChangedSignal() )

		v.setCamera( v.getCamera() )
		self.assertEqual( len( cs ), 0 )

		c = v.getCamera()
		c.parameters()["perspective:fov"] = IECore.FloatData( 10 )

		v.setCamera( c )
		self.assertEqual( len( cs ), 1 )
		self.assertEqual( cs[0], ( v, ) )

		v.setCamera( v.getCamera() )
		self.assertEqual( len( cs ), 1 )

	def testChangeResolutionPerspective( self ) :

		v = GafferUI.ViewportGadget()
		v.setViewport( imath.V2i( 200, 100 ) )
		v.setPlanarMovement( False )
		v.setCamera(
			IECoreScene.Camera( parameters = {
				"resolution" : imath.V2i( 200, 100 ),
				"screenWindow" : imath.Box2f( imath.V2f( -2, -1 ), imath.V2f( 2, 1 ) ),
				"projection" : "perspective",
				"projection:fov" : 90.0,
			} )
		)

		self.assertEqual( v.getCamera().frustum(), imath.Box2f( imath.V2f( -2, -1 ), imath.V2f( 2, 1 ) ) )

		v.setViewport( imath.V2i( 200, 200 ) )
		self.assertEqual( v.getCamera().frustum(), imath.Box2f( imath.V2f( -2 ), imath.V2f( 2 ) ) )

		v.setViewport( imath.V2i( 200, 100 ) )
		self.assertEqual( v.getCamera().frustum(), imath.Box2f( imath.V2f( -2, -1 ), imath.V2f( 2, 1 ) ) )

	def testChangeResolutionOrthographic( self ) :

		v = GafferUI.ViewportGadget()
		v.setViewport( imath.V2i( 200, 100 ) )
		v.setCamera(
			IECoreScene.Camera( parameters = {
				"resolution" : imath.V2i( 200, 100 ),
				"screenWindow" : imath.Box2f( imath.V2f( -2, -1 ), imath.V2f( 2, 1 ) ),
				"projection" : "orthographic",
			} )
		)

		self.assertEqual( v.getCamera().frustum(), imath.Box2f( imath.V2f( -2, -1 ), imath.V2f( 2, 1 ) ) )

		v.setViewport( imath.V2i( 100, 100 ) )
		self.assertEqual( v.getCamera().frustum(), imath.Box2f( imath.V2f( -1, -1 ), imath.V2f( 1, 1 ) ) )

		v.setViewport( imath.V2i( 100, 200 ) )
		self.assertEqual( v.getCamera().frustum(), imath.Box2f( imath.V2f( -1, -2 ), imath.V2f( 1, 2 ) ) )

	def testChangeResolutionOffsetOrthographic( self ) :

		v = GafferUI.ViewportGadget()
		v.setViewport( imath.V2i( 200, 100 ) )
		v.setCamera(
			IECoreScene.Camera( parameters = {
				"resolution" : imath.V2i( 200, 100 ),
				"screenWindow" : imath.Box2f( imath.V2f( -2, -1 ), imath.V2f( 0, 0 ) ),
				"projection" : "orthographic",
			} )
		)

		self.assertEqual( v.getCamera().frustum(), imath.Box2f( imath.V2f( -2, -1 ), imath.V2f( 0, 0 ) ) )

		v.setViewport( imath.V2i( 100, 100 ) )
		self.assertEqual( v.getCamera().frustum(), imath.Box2f( imath.V2f( -1.5, -1 ), imath.V2f( -0.5, 0 ) ) )

		v.setViewport( imath.V2i( 100, 200 ) )
		self.assertEqual( v.getCamera().frustum(), imath.Box2f( imath.V2f( -1.5, -1.5 ), imath.V2f( -0.5, 0.5 ) ) )

	def testRasterToWorldPlanar( self ) :

		v = GafferUI.ViewportGadget()
		v.setViewport( imath.V2i( 500, 250 ) )
		v.setCamera(
			IECoreScene.Camera( parameters = {
				"resolution" : imath.V2i( 500, 250 ),
				"screenWindow" : imath.Box2f( imath.V2f( -2, -1 ), imath.V2f( 2, 1 ) ),
				"projection" : "orthographic",
				"clippingPlanes" : imath.V2f( .1, 10 ),
			} )
		)

		self.assertEqual(
			v.rasterToWorldSpace( imath.V2f( 0 ) ),
			IECore.LineSegment3f( imath.V3f( -2, 1, -.1 ), imath.V3f( -2, 1, -10 ) )
		)

		self.assertEqual(
			v.rasterToWorldSpace( imath.V2f( 500, 250 ) ),
			IECore.LineSegment3f( imath.V3f( 2, -1, -.1 ), imath.V3f( 2, -1, -10 ) )
		)

		self.assertEqual(
			v.rasterToWorldSpace( imath.V2f( 250, 125 ) ),
			IECore.LineSegment3f( imath.V3f( 0, 0, -.1 ), imath.V3f( 0, 0, -10 ) )
		)

	def testRasterToWorldOrthographic( self ) :

		v = GafferUI.ViewportGadget()
		v.setViewport( imath.V2i( 500, 250 ) )
		v.setPlanarMovement( False )
		v.setCamera(
			IECoreScene.Camera( parameters = {
				"resolution" : imath.V2i( 500, 250 ),
				"screenWindow" : imath.Box2f( imath.V2f( -2, -1 ), imath.V2f( 2, 1 ) ),
				"projection" : "orthographic",
				"clippingPlanes" : imath.V2f( .1, 10 ),
			} )
		)

		self.assertEqual(
			v.rasterToWorldSpace( imath.V2f( 0 ) ),
			IECore.LineSegment3f( imath.V3f( -2, 1, -.1 ), imath.V3f( -2, 1, -10 ) )
		)

		self.assertEqual(
			v.rasterToWorldSpace( imath.V2f( 500, 250 ) ),
			IECore.LineSegment3f( imath.V3f( 2, -1, -.1 ), imath.V3f( 2, -1, -10 ) )
		)

		self.assertEqual(
			v.rasterToWorldSpace( imath.V2f( 250, 125 ) ),
			IECore.LineSegment3f( imath.V3f( 0, 0, -.1 ), imath.V3f( 0, 0, -10 ) )
		)

	def testRasterToWorldPerspective( self ) :

		v = GafferUI.ViewportGadget()
		v.setViewport( imath.V2i( 500, 250 ) )
		v.setPlanarMovement( False )
		v.setCamera(
			IECoreScene.Camera( parameters = {
				"resolution" : imath.V2i( 500, 250 ),
				"screenWindow" : imath.Box2f( imath.V2f( -1, -.5 ), imath.V2f( 1, .5 ) ),
				"projection" : "perspective",
				"projection:fov" : 90.0,
				"clippingPlanes" : imath.V2f( .1, 10 ),
			} )
		)

		self.assertEqual(
			v.rasterToWorldSpace( imath.V2f( 0 ) ),
			IECore.LineSegment3f( imath.V3f( -.1, .05, -.1 ), imath.V3f( -10, 5, -10 ) )
		)

		self.assertEqual(
			v.rasterToWorldSpace( imath.V2f( 500, 250 ) ),
			IECore.LineSegment3f( imath.V3f( .1, -.05, -.1 ), imath.V3f( 10, -5, -10 ) )
		)

		self.assertEqual(
			v.rasterToWorldSpace( imath.V2f( 250, 125 ) ),
			IECore.LineSegment3f( imath.V3f( 0, 0, -.1 ), imath.V3f( 0, 0, -10 ) )
		)

	def testWorldToRasterPlanar( self ) :

		v = GafferUI.ViewportGadget()
		v.setViewport( imath.V2i( 500, 250 ) )
		v.setCamera(
			IECoreScene.Camera( parameters = {
				"resolution" : imath.V2i( 500, 250 ),
				"screenWindow" : imath.Box2f( imath.V2f( -2, -1 ), imath.V2f( 2, 1 ) ),
				"projection" : "orthographic",
				"clippingPlanes" : imath.V2f( .1, 10 ),
			} )
		)

		r = imath.Rand48()
		for i in range( 0, 100 ) :
			rasterPosition = imath.V2f( r.nexti() % 500, r.nexti() % 250 )
			line = v.rasterToWorldSpace( rasterPosition )
			nearProjected = v.worldToRasterSpace( line.p0 )
			farProjected = v.worldToRasterSpace( line.p1 )

			self.assertTrue( nearProjected.equalWithAbsError( farProjected, 0.0001 ) )
			self.assertTrue(
				imath.V2f( rasterPosition.x, rasterPosition.y ).equalWithAbsError(
					nearProjected, 0.0001
				)
			)

	def testWorldToRasterOrthographic( self ) :

		v = GafferUI.ViewportGadget()
		v.setViewport( imath.V2i( 500, 250 ) )
		v.setPlanarMovement( False )
		v.setCamera(
			IECoreScene.Camera( parameters = {
				"resolution" : imath.V2i( 500, 250 ),
				"screenWindow" : imath.Box2f( imath.V2f( -2, -1 ), imath.V2f( 2, 1 ) ),
				"projection" : "orthographic",
				"clippingPlanes" : imath.V2f( .1, 10 ),
			} )
		)

		r = imath.Rand48()
		for i in range( 0, 100 ) :
			rasterPosition = imath.V2f( r.nexti() % 500, r.nexti() % 250 )
			line = v.rasterToWorldSpace( rasterPosition )
			nearProjected = v.worldToRasterSpace( line.p0 )
			farProjected = v.worldToRasterSpace( line.p1 )

			self.assertTrue( nearProjected.equalWithAbsError( farProjected, 0.0001 ) )
			self.assertTrue(
				imath.V2f( rasterPosition.x, rasterPosition.y ).equalWithAbsError(
					nearProjected, 0.0001
				)
			)

	def testWorldToRasterPerspective( self ) :

		v = GafferUI.ViewportGadget()
		v.setViewport( imath.V2i( 500, 250 ) )
		v.setPlanarMovement( False )
		v.setCamera(
			IECoreScene.Camera( parameters = {
				"resolution" : imath.V2i( 500, 250 ),
				"screenWindow" : imath.Box2f( imath.V2f( -1, -.5 ), imath.V2f( 1, .5 ) ),
				"projection" : "perspective",
				"projection:fov" : 50.0,
				"clippingPlanes" : imath.V2f( .1, 10 ),
			} )
		)

		r = imath.Rand48()
		for i in range( 0, 100 ) :
			rasterPosition = imath.V2f( r.nexti() % 500, r.nexti() % 250 )
			line = v.rasterToWorldSpace( rasterPosition )
			nearProjected = v.worldToRasterSpace( line.p0 )
			farProjected = v.worldToRasterSpace( line.p1 )
			self.assertTrue( nearProjected.equalWithAbsError( farProjected, 0.0001 ) )
			self.assertTrue(
				imath.V2f( rasterPosition.x, rasterPosition.y ).equalWithAbsError(
					nearProjected, 0.0001
				)
			)

if __name__ == "__main__":
	unittest.main()
