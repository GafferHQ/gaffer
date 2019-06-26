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

import imath

import IECore
import IECoreScene

import GafferScene
import GafferSceneTest
import GafferArnold

# LightToCamera is not Arnold specific, but I'm putting this test somewhere
# where we already have lights and metadata set up
class LightToCameraTest( GafferSceneTest.SceneTestCase ) :

	def testBasic( self ) :

		g = GafferScene.Group()

		inputs = []
		for shader, name in [
			("spot_light", "spot1"),
			("spot_light", "spot2"),
			("distant_light", "distant1"),
			("skydome_light", "env1"),
		] :
			l = GafferArnold.ArnoldLight()
			l.loadShader( shader )
			l["name"].setValue( name )
			inputs.append( l )

		inputs.append( GafferScene.Camera() )
		for i in inputs:
			g["in"][-1].setInput( i["out"] )

		f = GafferScene.PathFilter()
		f['paths'].setValue( IECore.StringVectorData( [ "/group/spot1", "/group/env1", "/group/distant1" ] ) )

		lc = GafferScene.LightToCamera()
		lc["in"].setInput( g["out"] )
		lc["filter"].setInput( f["out"] )

		# Test spot to persp cam
		spotCam = lc["out"].object( "/group/spot1" )
		# Equality test fails on Mac: 64.99999237060547 != 65
		calculatedFieldOfView = spotCam.calculateFieldOfView()
		self.assertAlmostEqual( calculatedFieldOfView[0], 65, 4 )
		self.assertAlmostEqual( calculatedFieldOfView[1], 65, 4 )
		self.assertEqual( spotCam.getClippingPlanes(), imath.V2f( 0.01, 100000 ) )
		self.assertEqual( spotCam.getProjection(), 'perspective' )
		self.assertEqual( spotCam.getFilmFit(), IECoreScene.Camera.FilmFit.Fit )
		self.assertEqual( spotCam.hasResolution(), False )

		# Test distant to ortho cam
		distantCam = lc["out"].object( "/group/distant1" )
		self.assertEqual( distantCam.getAperture(), imath.V2f( 2, 2 ) )
		self.assertEqual( distantCam.getClippingPlanes(), imath.V2f( -100000, 100000 ) )
		self.assertEqual( distantCam.getProjection(), 'orthographic' )
		self.assertEqual( distantCam.getFilmFit(), IECoreScene.Camera.FilmFit.Fit )
		self.assertEqual( distantCam.hasResolution(), False )

		# Test light with no corresponding camera ( gets default cam )
		self.assertEqual(
			lc["out"].object( "/group/env1" ).parameters(),
			IECore.CompoundData({
				'projection':IECore.StringData( 'perspective' ),
			} )
		)

		self.assertEqual( lc["out"].set( "__lights" ).value.paths(), [ "/group/spot2" ] )
		self.assertEqual(
			set( lc["out"].set( "__cameras" ).value.paths() ),
			set( [ "/group/camera", "/group/spot1", "/group/distant1", "/group/env1" ] )
		)

if __name__ == "__main__":
	unittest.main()
