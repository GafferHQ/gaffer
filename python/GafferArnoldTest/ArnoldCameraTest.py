##########################################################################
#
#  Copyright (c) 2026, Cinesite VFX Ltd. All rights reserved.
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

import GafferScene
import GafferSceneTest
import GafferArnold

class ArnoldCameraTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		for projection, plugin, parameters in [
			( "cylindrical", "cyl_camera", [ ( "cylindricalHorizontalFOV", "ai:horizontal_fov", 110.0 ), ( "rollingShutter", "ai:rolling_shutter", "bottom" ) ] ),
			( "fisheye", "fisheye_camera", [ ( "fisheyeFOV", "ai:fov", 360 ), ( "apertureBlades", "ai:aperture_blades", 11 ) ] ),
			( "spherical", "spherical_camera", [ ( "rollingShutterDuration", "ai:rolling_shutter_duration", 0.25 ) ] ),
			( "vr", "vr_camera", [ ( "mode", "ai:mode", "over_under" ), ( "rollingShutter", "ai:rolling_shutter", "left" ) ] ),
		] :
			arnoldCamera = GafferArnold.ArnoldCamera()

			arnoldCamera["cameraType"].setValue( projection )
			for gafferParam, arnoldParam, value in parameters :
				arnoldCamera[gafferParam].setValue( value )

			params = arnoldCamera["out"].object( "/camera" ).parameters()
			self.assertEqual( params["projection"].value, plugin )
			for gafferParam, arnoldParam, value in parameters :
				self.assertEqual( params[arnoldParam].value, value )

	def testCustomParameterPrefixed( self ) :

		arnoldCamera = GafferArnold.ArnoldCamera()
		tweakNodes = GafferScene.CameraTweaks.Range( arnoldCamera )

		for n in tweakNodes :
			for p in n["tweaks"] :
				with self.subTest( n = n, p = p ) :
					param = p["name"].getValue()
					if param != "projection" :
						self.assertTrue( p["name"].getValue().startswith( "ai:" ) )
