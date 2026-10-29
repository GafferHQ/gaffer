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

import IECore

import GafferSceneTest
import GafferArnold

class ArnoldCameraTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		for projection, plugin, parameters in [
			( "cylindrical", "cyl_camera", [ ( "cylindricalHorizontalFOV", "ai:horizontal_fov", 110.0 ), ( "rollingShutter", "ai:rolling_shutter", "bottom" ) ] ),
			( "fisheye", "fisheye_camera", [ ( "fisheyeFOV", "ai:fov", 360 ), ( "apertureBlades", "ai:aperture_blades", 11 ) ] ),
			( "spherical", "spherical_camera", [ ( "shutterType", "ai:shutter_type", "triangle" ) ] ),
			( "vr", "vr_camera", [ ( "projection", "ai:projection", "cubemap_6x1" ), ( "mode", "ai:mode", "over_under" ), ( "rollingShutter", "ai:rolling_shutter", "left" ) ] ),
		] :
			with self.subTest( projection = projection ) :
				arnoldCamera = GafferArnold.ArnoldCamera()

				arnoldCamera["type"].setValue( projection )
				for gafferParam, arnoldParam, value in parameters :
					arnoldCamera[gafferParam].setValue( value )

				params = arnoldCamera["out"].object( "/camera" ).parameters()
				self.assertEqual( params["projection"].value, plugin )
				for gafferParam, arnoldParam, value in parameters :
					self.assertEqual( params[arnoldParam].value, value )

	def testRelevantParameters( self ) :

		for projection, parameters in {
			"cylindrical" : {
				"ai:horizontal_fov", "ai:vertical_fov", "ai:projective", "ai:rolling_shutter",
				"ai:shutter_type", "clippingPlanes", "projection"
			},
			"fisheye" : {
				"ai:fov", "ai:autocrop", "ai:aperture_aspect_ratio", "ai:aperture_blade_curvature",
				"ai:aperture_blades", "ai:aperture_rotation", "ai:rolling_shutter", "ai:shutter_type",
				"clippingPlanes", "fStop", "focalLength", "focalLengthWorldScale", "focusDistance", "projection"
			},
			"spherical" : { "ai:rolling_shutter", "ai:shutter_type", "clippingPlanes", "projection" },
			"vr" : {
				"ai:projection", "ai:mode", "ai:eye_to_neck", "ai:eye_separation", "ai:bottom_merge_mode",
				"ai:bottom_merge_angle", "ai:top_merge_mode", "ai:top_merge_angle", "ai:rolling_shutter",
				"ai:shutter_type", "clippingPlanes", "projection"
			},
		}.items() :
			with self.subTest( projection = projection ) :
				arnoldCamera = GafferArnold.ArnoldCamera()

				arnoldCamera["type"].setValue( projection )
				self.assertEqual( set( arnoldCamera["out"].object( "/camera" ).parameters().keys() ), parameters )

				arnoldCamera["shutterType"].setValue( "curve" )
				self.assertEqual( set( arnoldCamera["out"].object( "/camera" ).parameters().keys() ), parameters | { "ai:shutter_curve" } )
				arnoldCamera["shutterType"].setValue( "triangle" )

				arnoldCamera["rollingShutter"].setValue( "top" )
				self.assertEqual( set( arnoldCamera["out"].object( "/camera" ).parameters().keys() ), parameters | { "ai:rolling_shutter_duration" } )
				arnoldCamera["rollingShutter"].setValue( "off" )

				if projection == "fisheye" :
					arnoldCamera["fStop"].setValue( 0.0 )
					self.assertEqual(
						set( arnoldCamera["out"].object( "/camera" ).parameters().keys() ),
						parameters - {
							"ai:aperture_aspect_ratio", "ai:aperture_blade_curvature", "ai:aperture_blades",
							"ai:aperture_rotation", "fStop", "focalLength", "focalLengthWorldScale", "focusDistance",
						}
					)
				elif projection == "vr" :
					arnoldCamera["topMergeMode"].setValue( "none" )
					arnoldCamera["bottomMergeMode"].setValue( "none" )
