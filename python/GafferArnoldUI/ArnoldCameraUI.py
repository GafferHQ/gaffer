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

import functools

import Gaffer
import GafferArnold

def __parameterMetadata( plug, key ) :

	node = plug.node()
	camera = node["Camera"]
	return Gaffer.Metadata.value( camera.descendant( plug.relativeName( node ) ), key )

Gaffer.Metadata.registerNode(

	GafferArnold.ArnoldCamera,

	"description",
	"""
	Produces scenes containing a camera with Arnold-specific
	parameters. To choose which camera is used for rendering,
	use a StandardOptions node.
	""",

	"layout:activator:typeIsVR", 'parent["cameraType"].getValue() == "vr"',
	"layout:activator:typeIsCylindrical", 'parent["cameraType"].getValue() == "cylindrical"',
	"layout:activator:typeIsFisheye", 'parent["cameraType"].getValue() == "fisheye"',
	"layout:activator:typeHasFOV", 'parent["cameraType"].getValue() == "cylindrical" or parent["cameraType"].getValue() == "fisheye"',
	"layout:activator:typeHasApertureAspectRatio", 'parent["cameraType"].getValue() == "cylindrical"',
	"layout:activator:shutterIsCurve", 'parent["shutterType"].getValue() == "curve"',
	"layout:activator:rollingShutterIsNotOff", 'parent["rollingShutter"].getValue() != "off"',

	"layout:section:Settings.Cylindrical:collapsed", False,
	"layout:section:Settings.Fisheye:collapsed", False,
	"layout:section:Settings.VR:collapsed", False,

	plugs = {

		"name" : {
			"layout:section" : functools.partial( __parameterMetadata, key = "layout:section" ),
		},

		"sets" : {
			"layout:section" : functools.partial( __parameterMetadata, key = "layout:section" ),
			"divider" : True,
		},

		"transform" : {
			"layout:section" : functools.partial( __parameterMetadata, key = "layout:section" ),
		},

		"fStop" : {
			"layout:section" : functools.partial( __parameterMetadata, key = "layout:section" ),
		},

		"focalLengthWorldScale" : {
			"layout:section" : functools.partial( __parameterMetadata, key = "layout:section" ),
		},

		"focusDistance" : {
			"layout:section" : functools.partial( __parameterMetadata, key = "layout:section" ),
		},

		"renderSettingOverrides" : {
			"layout:section" : functools.partial( __parameterMetadata, key = "layout:section" ),
			"layout:customWidget:addButton:visibilityActivator" : functools.partial( __parameterMetadata, key = "layout:customWidget:addButton:visibilityActivator" ),
		},

		"visualiserAttributes" : {
			"layout:section" : functools.partial( __parameterMetadata, key = "layout:section" ),
			"layout:customWidget:addButton:visibilityActivator" : functools.partial( __parameterMetadata, key = "layout:customWidget:addButton:visibilityActivator" ),
		},

		"enabled" : {
			"layout:section" : functools.partial( __parameterMetadata, key = "layout:section" ),
		},

		"cameraType" : {

			"desription" :
			"""
			The type of camera to create.
			""",
			"label" : "Type",
			"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",
			"preset:Cylindrical" : "cylindrical",
			"preset:Fisheye" : "fisheye",
			"preset:Spherical" : "spherical",
			"preset:VR" : "vr",
			"divider" : True

		},

		"cylindricalHorizontalFOV" : {

			"description" :
			"""
			The horizontal field of view.
			""",
			"label" : "Horizontal FOV",
			"layout:visibilityActivator" : "typeIsCylindrical",

		},

		"cylindricalVerticalFOV" : {

			"description" :
			"""
			The vertical field of view.
			""",
			"label" : "Vertical FOV",
			"layout:visibilityActivator" : "typeIsCylindrical",

		},

		"projective" : {

			"description" :
			"""
			If enabled, the camera acts as an orthographic view in the vertical
			direction and as a spherical camera in the horizontal direction. If
			disabled, all rays have a common origin at the center of the cylinder.
			""",
			"layout:visibilityActivator" : "typeIsCylindrical",

		},

		"fisheyeFOV" : {

			"description" :
			"""
			The field of view in both the horizontal and vertical directions.
			""",
			"label" : "Field of View",
			"layout:visibilityActivator" : "typeIsFisheye",

		},

		"autocrop" : {

			"description" :
			"""
			If enabled, a full-screen image will be cropped from the center of
			the view to remove any border.
			""",
			"layout:visibilityActivator" : "typeIsFisheye",

		},

		"mode" : {

			"description" :
			"""
			The arrangement of the left and right eye images.

			- Side by Side : The left eye is on the left half of the image and
			the right eye is on the right half.
			- Over Under : The left eye is on the top of the image and the
			right eye is on the bottom.
			- Left Eye : The full image is the left eye and the right eye is not shown.
			- Right Eye : The full image is the right eye and the left eye is not shown.
			""",
			"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",
			"preset:Side by Side" : "side_by_side",
			"preset:Over Under" : "over_under",
			"preset:Left Eye" : "left_eye",
			"preset:Right Eye" : "right_eye",
			"layout:visibilityActivator" : "typeIsVR",

		},

		"projection" : {

			"description" :
			"""
			Determines how the full spherical view surrounding the camera is mapped
			to the image plane.
			""",
			"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",
			"preset:LatLong" : "latlong",
			"preset:Cubemap (6x1)" : "cubemap_6x1",
			"preset:Cubemap (3x2)" : "cubemap_3x2",
			"layout:visibilityActivator" : "typeIsVR",

		},

		"eyeSeparation" : {

			"description" :
			"""
			The distance between the left and right cameras.
			""",
			"layout:visibilityActivator" : "typeIsVR",

		},

		"eyeToNeck" : {

			"description" :
			"""
			The horizontal distance from the neck to the eye.
			""",
			"layout:visibilityActivator" : "typeIsVR",

		},

		"topMergeMode" : {

			"description" :
			"""
			The merging function for the sky. Cosine merging will be smoother
			and have fewer artifacts.
			""",
			"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",
			"preset:None" : "none",
			"preset:Cosine" : "cosine",
			"layout:visibilityActivator" : "typeIsVR",

		},

		"topMergeAngle" : {

			"description" :
			"""
			The angle, in degrees, where the sky merge effect begins. As this
			value gets lower, the stereoscopic effect increases as well as
			artifacts near the pole.
			""",
			"layout:visibilityActivator" : "typeIsVR",

		},

		"bottomMergeMode" : {

			"description" :
			"""
			The merging function for the floor. Cosine merging will be smoother
			and have fewer artifacts.
			""",
			"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",
			"preset:None" : "none",
			"preset:Cosine" : "cosine",
			"layout:visibilityActivator" : "typeIsVR",

		},

		"bottomMergeAngle" : {

			"description" :
			"""The angle, in degrees, where the floor merge effect begins. As this
			value gets higher, the stereoscopic effect increases as well as
			artifacts near the pole.
			""",
			"layout:visibilityActivator" : "typeIsVR",

		},

		"filterMap" : {

			"divider" : True,

		},

		"clippingPlanes" : {
			"layout:section" : functools.partial( __parameterMetadata, key = "layout:section" ),
		},

	}
)
