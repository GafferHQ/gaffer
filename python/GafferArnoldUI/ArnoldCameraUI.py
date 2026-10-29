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

import Gaffer
import GafferArnold

Gaffer.Metadata.registerNode(

	GafferArnold.ArnoldCamera,

	"description",
	"""
	Produces scenes containing a camera with Arnold-specific
	parameters. To choose which camera is used for rendering,
	use a StandardOptions node.
	""",

	"layout:activator:typeIsVR", 'parent["type"].getValue() == "vr"',
	"layout:activator:typeIsCylindrical", 'parent["type"].getValue() == "cylindrical"',
	"layout:activator:typeIsFisheye", 'parent["type"].getValue() == "fisheye"',
	"layout:activator:shutterIsCurve", 'parent["shutterType"].getValue() == "curve"',
	"layout:activator:rollingShutterIsNotOff", 'parent["rollingShutter"].getValue() != "off"',
	"layout:activator:dof", lambda node : node["fStop"].getValue() != 0,

	plugs = {

		"type" : {

			"description" :
			"""
			The type of camera to create.
			""",
			"userDefault" : "cylindrical",
			"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",
			"presetNames" : IECore.StringVectorData( [ "Cylindrical", "Fisheye", "Spherical", "VR" ] ),
			"presetValues" : IECore.StringVectorData( [ "cylindrical", "fisheye", "spherical", "vr" ] ),

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

		"apertureBlades" : {

			"layout:section" : "Depth of Field",
			"layout:visibilityActivator" : "typeIsFisheye",
			"layout:activator" : "dof",
			"description" :
			"""
			The number of blades of the aperture. A value of zero results in a
			circular aperture.
			""",

		},

		"apertureBladeCurvature" : {

			"layout:section" : "Depth of Field",
			"layout:visibilityActivator" : "typeIsFisheye",
			"layout:activator" : "dof",
			"description" :
			"""
			The curvature of the aperture blades. A value of zero results in
			straight edges. A value of one results in a perfect disk.
			""",

		},

		"apertureRotation" : {

			"layout:section" : "Depth of Field",
			"layout:visibilityActivator" : "typeIsFisheye",
			"layout:activator" : "dof",
			"description" :
			"""
			The amount the aperture is rotated.
			""",

		},

		"apertureAspectRatio" : {

			"layout:section" : "Depth of Field",
			"layout:visibilityActivator" : "typeIsFisheye",
			"layout:activator" : "dof",
			"description" :
			"""
			The aspect ratio of aperture used for depth of field. Values greater
			than one elongate the defocus effect, similar to an anamorphic lens.
			Values less than one squash the defocus effect.
			""",

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
			"presetNames" : IECore.StringVectorData( [ "Side by Side", "Over Under", "Left Eye", "Right Eye" ] ),
			"presetValues" : IECore.StringVectorData( [ "side_by_side", "over_under", "left_eye", "right_eye" ] ),
			"layout:visibilityActivator" : "typeIsVR",

		},

		"projection" : {

			"description" :
			"""
			Determines how the full spherical view surrounding the camera is mapped
			to the image plane.
			""",
			"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",
			"presetNames" : IECore.StringVectorData( [ "LatLong", "Cubemap (6x1)", "Cubemap (3x2)" ] ),
			"presetValues" : IECore.StringVectorData( [ "latlong", "cubemap_6x1", "cubemap_3x2" ] ),
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
			"presetNames" : IECore.StringVectorData( [ "None", "Cosine" ] ),
			"presetValues" : IECore.StringVectorData( [ "none", "cosine" ] ),
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
			"presetNames" : IECore.StringVectorData( [ "None", "Cosine" ] ),
			"presetValues" : IECore.StringVectorData( [ "none", "cosine" ] ),
			"layout:visibilityActivator" : "typeIsVR",

		},

		"bottomMergeAngle" : {

			"description" :
			"""
			The angle, in degrees, where the floor merge effect begins. As this
			value gets higher, the stereoscopic effect increases as well as
			artifacts near the pole.
			""",
			"layout:visibilityActivator" : "typeIsVR",
			"divider" : True,

		},

		"shutterType" : {

			"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",
			"presetNames" : IECore.StringVectorData( [ "Box", "Triangle", "Curve" ] ),
			"presetValues" : IECore.StringVectorData( [ "box", "triangle", "curve" ] ),
			"description" :
			"""
			The filtering applied to time samples.

			- Box : All samples have the same weight.
			- Triangle : Additional weight is given to later time samples, resulting
			in smoother tails.
			- Curve : Weights are determined by a user-defined curve.
			""",

		},

		"shutterCurve" : {

			"layout:visibilityActivator" : "shutterIsCurve",
			"description" :
			"""
			The curve to use to weight time samples.
			""",

		},

		"rollingShutter" : {

			"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",
			"presetNames" : IECore.StringVectorData( [ "Off", "Top", "Bottom", "Left", "Right" ] ),
			"presetValues" : IECore.StringVectorData( [ "off", "top", "bottom", "left", "right" ] ),
			"description" :
			"""
			The direction of the rolling shutter.
			""",

		},

		"rollingShutterDuration" : {

			"description" :
			"""
			The length of time a scanline is exposed by the rolling shutter. A value of zero
			results in instantaneous exposure. A value of one results in each scanline
			exposed for the entire length of the shutter opening interval.
			""",
			"layout:visibilityActivator" : "rollingShutterIsNotOff",

		},

		"filterMap" : {

			"divider" : True,

		},

		"fStop" : {

			"layout:visibilityActivator" : "typeIsFisheye",

		},

		"focalLengthWorldScale" : {

			"layout:visibilityActivator" : "typeIsFisheye",

		},

		"focusDistance" : {

			"layout:visibilityActivator" : "typeIsFisheye",

		},

		"renderSettingOverrides.filmFit" : {

			"layout:visibilityActivator" : lambda plug : plug.node()["type"].getValue() == "fisheye",

		},

	}
)
