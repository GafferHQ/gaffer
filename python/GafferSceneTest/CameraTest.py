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

import unittest
import math
import imath

import IECore
import IECoreScene

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest

class CameraTest( GafferSceneTest.SceneTestCase ) :

	def testConstruct( self ) :

		p = GafferScene.Camera()
		self.assertEqual( p.getName(), "Camera" )
		self.assertEqual( p["name"].getValue(), "camera" )

	def testCompute( self ) :

		p = GafferScene.Camera()
		p["projection"].setValue( "perspective" )
		p["fieldOfView"].setValue( 45 )

		self.assertEqual( p["out"].object( "/" ), IECore.NullObject() )
		self.assertEqual( p["out"].transform( "/" ), imath.M44f() )
		self.assertEqual( p["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "camera" ] ) )

		self.assertEqual( p["out"].transform( "/camera" ), imath.M44f() )
		self.assertEqual( p["out"].childNames( "/camera" ), IECore.InternedStringVectorData() )

		o = p["out"].object( "/camera" )
		self.assertIsInstance( o, IECoreScene.Camera )
		self.assertEqual( o.getProjection(), "perspective" )

		self.assertEqual( o.getAperture(), imath.V2f( 1.0 ) )
		self.assertAlmostEqual( o.getFocalLength(), 1.0 / ( 2.0 * math.tan( IECore.degreesToRadians( 0.5 * 45 ) ) ), places = 6 )

		self.assertSceneValid( p["out"] )

	def testAttributes( self ) :

		c = GafferScene.Camera()
		path = "/%s" % c["name"].getValue()

		a = c["out"].attributes( path )
		self.assertFalse( "gl:visualiser:frustum" in a )
		self.assertFalse( "gl:visualiser:scale" in a )

		c["visualiserAttributes"]["frustum"]["enabled"].setValue( True )

		a = c["out"].attributes( path )
		self.assertEqual( a["gl:visualiser:frustum"], IECore.StringData( "whenSelected" ) )
		self.assertFalse( "gl:visualiser:scale" in a )

		c["visualiserAttributes"]["scale"]["enabled"].setValue( True )
		a = c["out"].attributes( path )

		self.assertEqual( a["gl:visualiser:frustum"], IECore.StringData( "whenSelected" ) )
		self.assertEqual( a["gl:visualiser:scale"], IECore.FloatData( 1.0 ) )

		c["visualiserAttributes"]["frustum"]["value"].setValue( "off" )
		c["visualiserAttributes"]["scale"]["value"].setValue( 12.1 )

		a = c["out"].attributes( path )
		self.assertEqual( a["gl:visualiser:frustum"], IECore.StringData( "off" ) )
		self.assertEqual( a["gl:visualiser:scale"], IECore.FloatData( 12.1 ) )

	def testHashes( self ) :

		p = GafferScene.Camera()
		p["projection"].setValue( "perspective" )
		p["fieldOfView"].setValue( 45 )

		# Disabled by default, enabled for hash testing
		p['visualiserAttributes']['frustum']['enabled'].setValue( True )
		p['visualiserAttributes']['scale']['enabled'].setValue( True )

		for i in p['renderSettingOverrides']:
			i["enabled"].setValue( True )

		with Gaffer.Context() as c :

			c["scene:path"] = IECore.InternedStringVectorData()
			# We ignore the enabled and sets plugs because they aren't hashed (instead
			# their values are used to decide how the hash should be computed). We ignore
			# the transform plug because it isn't affected by any inputs when the path is "/".
			# We ignore the set plug + attr because they needs a different context - we test that below.
			self.assertHashesValid( p, inputsToIgnore = [ p["enabled"], p["sets"] ], outputsToIgnore = [ p["out"]["transform"], p["out"]["set"], p["out"]["attributes"] ])

			c["scene:path"] = IECore.InternedStringVectorData( [ "camera" ] )
			# We ignore the childNames because it doesn't use any inputs to compute when
			# the path is not "/". We ignore the bound plug because although it has a dependency
			# on the transform plug, that is only relevant when the path is "/".
			self.assertHashesValid( p, inputsToIgnore = [ p["enabled"], p["sets"] ], outputsToIgnore = [ p["out"]["childNames"], p["out"]["bound"], p["out"]["set"] ] )

		with Gaffer.Context() as c :

			c["scene:setName"] = IECore.InternedStringData( "__cameras" )
			self.assertHashesValid( p, inputsToIgnore = [ p["enabled"], p["sets"] ], outputsToIgnore = [ c for c in p["out"] if c != p["out"]["set"] ] )

	def testBound( self ) :

		p = GafferScene.Camera()
		p["projection"].setValue( "perspective" )
		p["fieldOfView"].setValue( 45 )

		self.assertFalse( p["out"].bound( "/" ).isEmpty() )
		self.assertFalse( p["out"].bound( "/camera" ).isEmpty() )

	def testClippingPlanes( self ) :

		p = GafferScene.Camera()
		o = p["out"].object( "/camera" )
		self.assertEqual( o.parameters()["clippingPlanes"].value, imath.V2f( 0.01, 100000 ) )

		p["clippingPlanes"].setValue( imath.V2f( 1, 10 ) )
		o = p["out"].object( "/camera" )
		self.assertEqual( o.parameters()["clippingPlanes"].value, imath.V2f( 1, 10 ) )

	def testEnableBehaviour( self ) :

		c = GafferScene.Camera()
		self.assertTrue( c.enabledPlug().isSame( c["enabled"] ) )
		self.assertEqual( c.correspondingInput( c["out"] ), None )
		self.assertEqual( c.correspondingInput( c["enabled"] ), None )
		self.assertEqual( c.correspondingInput( c["projection"] ), None )
		self.assertEqual( c.correspondingInput( c["fieldOfView"] ), None )

	def testCameraSet( self ) :

		c = GafferScene.Camera()

		cameraSet = c["out"].set( "__cameras" )
		self.assertEqual(
			cameraSet,
			IECore.PathMatcherData(
				IECore.PathMatcher( [ "/camera" ] )
			)
		)

		c["name"].setValue( "renderCam" )

		cameraSet = c["out"].set( "__cameras" )
		self.assertEqual(
			cameraSet,
			IECore.PathMatcherData(
				IECore.PathMatcher( [ "/renderCam" ] )
			)
		)

	def testDirtyPropagation( self ) :

		c = GafferScene.Camera()

		dirtied = GafferTest.CapturingSlot( c.plugDirtiedSignal() )
		c["transform"]["translate"]["x"].setValue( 10 )
		self.assertIn( c["out"]["transform"], [ p[0] for p in dirtied ] )

		dirtied = GafferTest.CapturingSlot( c.plugDirtiedSignal() )
		c["name"].setValue( "renderCam" )
		self.assertIn( c["out"]["childNames"], [ p[0] for p in dirtied ] )
		self.assertIn( c["out"]["set"], [ p[0] for p in dirtied ] )

		dirtied = GafferTest.CapturingSlot( c.plugDirtiedSignal() )
		c["projection"].setValue( "orthographic" )
		self.assertIn( c["out"]["object"], [ p[0] for p in dirtied ] )
		self.assertIn( c["out"]["bound"], [ p[0] for p in dirtied ] )

		dirtied = GafferTest.CapturingSlot( c.plugDirtiedSignal() )
		c["fieldOfView"].setValue( 100 )
		self.assertIn( c["out"]["object"], [ p[0] for p in dirtied ] )
		self.assertIn( c["out"]["bound"], [ p[0] for p in dirtied ] )

		dirtied = GafferTest.CapturingSlot( c.plugDirtiedSignal() )
		c["clippingPlanes"]["x"].setValue( 100 )
		self.assertIn( c["out"]["object"], [ p[0] for p in dirtied ] )
		self.assertIn( c["out"]["bound"], [ p[0] for p in dirtied ] )

	def testFrustum( self ) :

		c = GafferScene.Camera()
		self.assertAlmostEqual( c["out"].object( "/camera" ).frustum( IECoreScene.Camera.FilmFit.Distort ).max()[0] * 2.0, 2.0 * math.tan( 0.5 * math.radians( c["fieldOfView"].getValue() ) ), places = 6 )
		c["fieldOfView"].setValue( 100 )
		self.assertAlmostEqual( c["out"].object( "/camera" ).frustum( IECoreScene.Camera.FilmFit.Distort ).max()[0] * 2.0, 2.0 * math.tan( 0.5 * math.radians( c["fieldOfView"].getValue() ) ), places = 6 )
		self.assertAlmostEqual( c["out"].object( "/camera" ).frustum( IECoreScene.Camera.FilmFit.Distort ).max()[1] * 2.0, 2.0 * math.tan( 0.5 * math.radians( c["fieldOfView"].getValue() ) ), places = 6 )
		c["apertureAspectRatio"].setValue( 3 )
		self.assertAlmostEqual( c["out"].object( "/camera" ).frustum( IECoreScene.Camera.FilmFit.Distort ).max()[0] * 2.0, 2.0 * math.tan( 0.5 * math.radians( c["fieldOfView"].getValue() ) ), places = 6 )
		self.assertAlmostEqual( c["out"].object( "/camera" ).frustum( IECoreScene.Camera.FilmFit.Distort ).max()[1] * 2.0, 2.0 / 3.0 * math.tan( 0.5 * math.radians( c["fieldOfView"].getValue() ) ), places = 6 )

		c["perspectiveMode"].setValue( GafferScene.Camera.PerspectiveMode.ApertureFocalLength )
		self.assertNotAlmostEqual( c["out"].object( "/camera" ).frustum( IECoreScene.Camera.FilmFit.Distort ).max()[0] * 2.0, 2.0 * math.tan( 0.5 * math.radians( c["fieldOfView"].getValue() ) ), places = 6 )
		self.assertAlmostEqual( c["out"].object( "/camera" ).frustum( IECoreScene.Camera.FilmFit.Distort ).max()[0] * 2.0, c["aperture"].getValue()[0] / c["focalLength"].getValue(), places = 6 )
		c["aperture"].setValue( imath.V2f( 100 ) )
		self.assertAlmostEqual( c["out"].object( "/camera" ).frustum( IECoreScene.Camera.FilmFit.Distort ).max()[0] * 2.0, c["aperture"].getValue()[0] / c["focalLength"].getValue(), places = 6 )
		c["focalLength"].setValue( 200 )
		self.assertAlmostEqual( c["out"].object( "/camera" ).frustum( IECoreScene.Camera.FilmFit.Distort ).max()[0] * 2.0, c["aperture"].getValue()[0] / c["focalLength"].getValue(), places = 6 )

		c["projection"].setValue( "orthographic" )
		self.assertNotAlmostEqual( c["out"].object( "/camera" ).frustum( IECoreScene.Camera.FilmFit.Distort ).max()[0] * 2.0, c["aperture"].getValue()[0] / c["focalLength"].getValue(), places = 6 )
		self.assertEqual( c["out"].object( "/camera" ).frustum( IECoreScene.Camera.FilmFit.Distort ).max() * 2.0, c["orthographicAperture"].getValue() )
		c["orthographicAperture"].setValue( imath.V2f( 0.1, 12 ) )
		self.assertEqual( c["out"].object( "/camera" ).frustum( IECoreScene.Camera.FilmFit.Distort ).max() * 2.0, c["orthographicAperture"].getValue() )

if __name__ == "__main__":
	unittest.main()
