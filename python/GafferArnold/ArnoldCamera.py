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

import inspect

import IECore

import Gaffer
import GafferScene
import GafferArnold

class ArnoldCamera( GafferScene.SceneNode ) :

	def __init__( self, name = "ArnoldCamera" ) :

		GafferScene.SceneNode.__init__( self, name )

		self["Camera"] = GafferScene.Camera( "Camera" )

		self["PathFilter"] = GafferScene.PathFilter( "PathFilter" )
		self["PathFilter"]["paths"].setInput( self["Camera"]["name"] )

		self["CylindricalTweaks"] = GafferScene.CameraTweaks( "CylindricalTweaks" )
		self["CylindricalTweaks"]["in"].setInput( self["Camera"]["out"] )
		self["CylindricalTweaks"]["filter"].setInput( self["PathFilter"]["out"] )
		self["CylindricalTweaks"]["tweaks"].addChild( Gaffer.TweakPlug( name = "projectionTweak", nameDefault = "projection", modeDefault = Gaffer.TweakPlug.Mode.Create, valuePlug = Gaffer.StringPlug( "value", defaultValue = "cyl_camera" ) ) )
		self["CylindricalTweaks"]["tweaks"].addChild( Gaffer.TweakPlug( name = "horizontalFOVTweak", nameDefault = "ai:horizontal_fov", modeDefault = Gaffer.TweakPlug.Mode.Create, valuePlug = Gaffer.FloatPlug( "value", defaultValue = 60.0, minValue = 0.0 ) ) )
		self["CylindricalTweaks"]["tweaks"].addChild( Gaffer.TweakPlug( name = "verticalFOVTweak", nameDefault = "ai:vertical_fov", modeDefault = Gaffer.TweakPlug.Mode.Create, valuePlug = Gaffer.FloatPlug( "value", defaultValue = 90.0, minValue = 0.0 ) ) )
		self["CylindricalTweaks"]["tweaks"].addChild( Gaffer.TweakPlug( name = "projectiveTweak", nameDefault = "ai:projective", modeDefault = Gaffer.TweakPlug.Mode.Create, valuePlug = Gaffer.BoolPlug( "value", defaultValue = True ) ) )

		self["FisheyeTweaks"] = GafferScene.CameraTweaks( "FisheyeTweaks" )
		self["FisheyeTweaks"]["in"].setInput( self["Camera"]["out"] )
		self["FisheyeTweaks"]["filter"].setInput( self["PathFilter"]["out"] )
		self["FisheyeTweaks"]["tweaks"].addChild( Gaffer.TweakPlug( name = "projectionTweak", nameDefault = "projection", modeDefault = Gaffer.TweakPlug.Mode.Create, valuePlug = Gaffer.StringPlug( "value", defaultValue = "fisheye_camera" ) ) )
		self["FisheyeTweaks"]["tweaks"].addChild( Gaffer.TweakPlug( name = "fovTweak", nameDefault = "ai:fov", modeDefault = Gaffer.TweakPlug.Mode.Create, valuePlug = Gaffer.FloatPlug( "value", defaultValue = 90.0, minValue = 0.0 ) ) )
		self["FisheyeTweaks"]["tweaks"].addChild( Gaffer.TweakPlug( name = "autocropTweak", nameDefault = "ai:autocrop", modeDefault = Gaffer.TweakPlug.Mode.Create, valuePlug = Gaffer.BoolPlug( "value", defaultValue = False ) ) )
		self["FisheyeTweaks"]["tweaks"].addChild( Gaffer.TweakPlug( name = "apertureBladesTweak", nameDefault = "ai:aperture_blades", modeDefault = Gaffer.TweakPlug.Mode.Create, valuePlug = Gaffer.IntPlug( "value", defaultValue = 0, minValue = 0, maxValue = 40 ) ) )
		self["FisheyeTweaks"]["tweaks"].addChild( Gaffer.TweakPlug( name = "apertureBladeCurvatureTweak", nameDefault = "ai:aperture_blade_curvature", modeDefault = Gaffer.TweakPlug.Mode.Create, valuePlug = Gaffer.FloatPlug( "value", defaultValue = 0.0, minValue = -20.0, maxValue = 20.0 ) ) )
		self["FisheyeTweaks"]["tweaks"].addChild( Gaffer.TweakPlug( name = "apertureRotationTweak", nameDefault = "ai:aperture_rotation", modeDefault = Gaffer.TweakPlug.Mode.Create, valuePlug = Gaffer.FloatPlug( "value", defaultValue = 0.0, minValue = 0.0, maxValue = 360.0 ) ) )
		self["FisheyeTweaks"]["tweaks"].addChild( Gaffer.TweakPlug( name = "apertureAspectRatioTweak", nameDefault = "ai:aperture_aspect_ratio", modeDefault = Gaffer.TweakPlug.Mode.Create, valuePlug = Gaffer.FloatPlug( "value", defaultValue = 1.0, minValue = 0.0 ) ) )

		self["SphericalTweaks"] = GafferScene.CameraTweaks( "SphericalTweaks" )
		self["SphericalTweaks"]["in"].setInput( self["Camera"]["out"] )
		self["SphericalTweaks"]["filter"].setInput( self["PathFilter"]["out"] )
		self["SphericalTweaks"]["tweaks"].addChild( Gaffer.TweakPlug( name = "projectionTweak", nameDefault = "projection", modeDefault = Gaffer.TweakPlug.Mode.Create, valuePlug = Gaffer.StringPlug( "value", defaultValue = "spherical_camera" ) ) )

		self["VRTweaks"] = GafferScene.CameraTweaks( "VRTweaks" )
		self["VRTweaks"]["in"].setInput( self["Camera"]["out"] )
		self["VRTweaks"]["filter"].setInput( self["PathFilter"]["out"] )
		self["VRTweaks"]["tweaks"].addChild( Gaffer.TweakPlug( name = "projectionTweak", nameDefault = "projection", modeDefault = Gaffer.TweakPlug.Mode.Create, valuePlug = Gaffer.StringPlug( "value", defaultValue = "vr_camera" ) ) )
		self["VRTweaks"]["tweaks"].addChild( Gaffer.TweakPlug( name = "modeTweak", nameDefault = "ai:mode", modeDefault = Gaffer.TweakPlug.Mode.Create, valuePlug = Gaffer.StringPlug( "value", defaultValue = "side_by_side" ) ) )
		self["VRTweaks"]["tweaks"].addChild( Gaffer.TweakPlug( name = "vrProjectionTweak", nameDefault = "ai:projection", modeDefault = Gaffer.TweakPlug.Mode.Create, valuePlug = Gaffer.StringPlug( "value", defaultValue = "latlong" ) ) )
		self["VRTweaks"]["tweaks"].addChild( Gaffer.TweakPlug( name = "eyeSeparationTweak", nameDefault = "ai:eye_separation", modeDefault = Gaffer.TweakPlug.Mode.Create, valuePlug = Gaffer.FloatPlug( "value", defaultValue = 0.65 ) ) )
		self["VRTweaks"]["tweaks"].addChild( Gaffer.TweakPlug( name = "eyeToNeckTweak", nameDefault = "ai:eye_to_neck", modeDefault = Gaffer.TweakPlug.Mode.Create, valuePlug = Gaffer.FloatPlug( "value", defaultValue = 0.0 ) ) )
		self["VRTweaks"]["tweaks"].addChild( Gaffer.TweakPlug( name = "topMergeModeTweak", nameDefault = "ai:top_merge_mode", modeDefault = Gaffer.TweakPlug.Mode.Create, valuePlug = Gaffer.StringPlug( "value", defaultValue = "cosine" ) ) )
		self["VRTweaks"]["tweaks"].addChild( Gaffer.TweakPlug( name = "topMergeAngleTweak", nameDefault = "ai:top_merge_angle", modeDefault = Gaffer.TweakPlug.Mode.Create, valuePlug = Gaffer.FloatPlug( "value", defaultValue = 90.0, minValue = 0.0, maxValue = 180.0 ) ) )
		self["VRTweaks"]["tweaks"].addChild( Gaffer.TweakPlug( name = "bottomMergeModeTweak", nameDefault = "ai:bottom_merge_mode", modeDefault = Gaffer.TweakPlug.Mode.Create, valuePlug = Gaffer.StringPlug( "value", defaultValue = "cosine" ) ) )
		self["VRTweaks"]["tweaks"].addChild( Gaffer.TweakPlug( name = "bottomMergeAngleTweak", nameDefault = "ai:bottom_merge_angle", modeDefault = Gaffer.TweakPlug.Mode.Create, valuePlug = Gaffer.FloatPlug( "value", defaultValue = 90.0, minValue = 0.0, maxValue = 180.0 ) ) )

		self["VRTweaksEnablerExpression"] = Gaffer.Expression()
		self["VRTweaksEnablerExpression"].setExpression(
			inspect.cleandoc(
				"""
				parent["VRTweaks"]["tweaks"]["topMergeAngleTweak"]["enabled"] = parent["VRTweaks"]["tweaks"]["topMergeModeTweak"]["value"] != "none"
				parent["VRTweaks"]["tweaks"]["bottomMergeAngleTweak"]["enabled"] = parent["VRTweaks"]["tweaks"]["bottomMergeModeTweak"]["value"] != "none"
				"""
			)
		)

		for tweaksName in [ "CylindricalTweaks", "FisheyeTweaks", "SphericalTweaks", "VRTweaks" ] :
			self[tweaksName]["tweaks"].addChild( Gaffer.TweakPlug( name = "fStopTweak", nameDefault = "fStop", modeDefault = Gaffer.TweakPlug.Mode.Remove, valuePlug = Gaffer.FloatPlug() ) )
			self[tweaksName]["tweaks"].addChild( Gaffer.TweakPlug( name = "focalLengthWorldScaleTweak", nameDefault = "focalLengthWorldScale", modeDefault = Gaffer.TweakPlug.Mode.Remove, valuePlug = Gaffer.FloatPlug() ) )
			self[tweaksName]["tweaks"].addChild( Gaffer.TweakPlug( name = "focalLengthTweak", nameDefault = "focalLength", modeDefault = Gaffer.TweakPlug.Mode.Remove, valuePlug = Gaffer.FloatPlug() ) )
			self[tweaksName]["tweaks"].addChild( Gaffer.TweakPlug( name = "focusDistanceTweak", nameDefault = "focusDistance", modeDefault = Gaffer.TweakPlug.Mode.Remove, valuePlug = Gaffer.FloatPlug() ) )

		self["FisheyeTweaksEnablerExpression"] = Gaffer.Expression()
		self["FisheyeTweaksEnablerExpression"].setExpression(
			inspect.cleandoc(
				"""
				dofEnabled = parent["Camera"]["fStop"] != 0.0
				parent["FisheyeTweaks"]["tweaks"]["apertureBladesTweak"]["enabled"] = dofEnabled
				parent["FisheyeTweaks"]["tweaks"]["apertureBladeCurvatureTweak"]["enabled"] = dofEnabled
				parent["FisheyeTweaks"]["tweaks"]["apertureRotationTweak"]["enabled"] = dofEnabled
				parent["FisheyeTweaks"]["tweaks"]["apertureAspectRatioTweak"]["enabled"] = dofEnabled
				# These do deletions, so they are enabled in reverse of those above.
				parent["FisheyeTweaks"]["tweaks"]["fStopTweak"]["enabled"] = not dofEnabled
				parent["FisheyeTweaks"]["tweaks"]["focalLengthWorldScaleTweak"]["enabled"] = not dofEnabled
				parent["FisheyeTweaks"]["tweaks"]["focalLengthTweak"]["enabled"] = not dofEnabled
				parent["FisheyeTweaks"]["tweaks"]["focusDistanceTweak"]["enabled"] = not dofEnabled
				"""
			)
		)

		self["NameSwitch"] = Gaffer.NameSwitch( "NameSwitch" )
		self["NameSwitch"].setup( self["Camera"]["out"] )
		self["NameSwitch"]["in"].resize( 5 )
		self["NameSwitch"]["in"][0]["name"].setValue( "*" )
		self["NameSwitch"]["in"][1]["name"].setValue( "cylindrical" )
		self["NameSwitch"]["in"][1]["value"].setInput( self["CylindricalTweaks"]["out"] )
		self["NameSwitch"]["in"][2]["name"].setValue( 'fisheye' )
		self["NameSwitch"]["in"][2]["value"].setInput( self["FisheyeTweaks"]["out"] )
		self["NameSwitch"]["in"][3]["name"].setValue( 'spherical' )
		self["NameSwitch"]["in"][3]["value"].setInput( self["SphericalTweaks"]["out"] )
		self["NameSwitch"]["in"][4]["name"].setValue( 'vr' )
		self["NameSwitch"]["in"][4]["value"].setInput( self["VRTweaks"]["out"] )

		self["CameraTweaks"] = GafferScene.CameraTweaks( "CameraTweaks" )
		self["CameraTweaks"]["in"].setInput( self["NameSwitch"]["out"]["value"] )
		self["CameraTweaks"]["filter"].setInput( self["PathFilter"]["out"] )
		self["CameraTweaks"]["tweaks"].addChild( Gaffer.TweakPlug( name = "shutterTypeTweak", nameDefault = "ai:shutter_type", modeDefault = Gaffer.TweakPlug.Mode.Create, valuePlug = Gaffer.StringPlug( "value", defaultValue = "box" ) ) )
		self["CameraTweaks"]["tweaks"].addChild(
			Gaffer.TweakPlug(
				name = "shutterCurveTweak",
				nameDefault = "ai:shutter_curve",
				modeDefault = Gaffer.TweakPlug.Mode.Create,
				valuePlug = Gaffer.RampffPlug(
					"value",
					defaultValue = IECore.Rampff( [ ( 0, 0 ), ( 0.25, 1 ), (0.75, 1 ), ( 1, 0 ) ], IECore.RampInterpolation.Linear )
				)
			)
		)
		self["CameraTweaks"]["tweaks"].addChild( Gaffer.TweakPlug( name = "rollingShutterTweak", nameDefault = "ai:rolling_shutter", modeDefault = Gaffer.TweakPlug.Mode.Create, valuePlug = Gaffer.StringPlug( "value", defaultValue = "off" ) ) )
		self["CameraTweaks"]["tweaks"].addChild( Gaffer.TweakPlug( name = "rollingShutterDurationTweak", nameDefault = "ai:rolling_shutter_duration", modeDefault = Gaffer.TweakPlug.Mode.Create, valuePlug = Gaffer.FloatPlug( "value", defaultValue = 0.0, minValue = 0.0, maxValue = 1.0 ) ) )
		self["CameraTweaks"]["tweaks"].addChild( Gaffer.TweakPlug( name = "filmFitTweak", nameDefault = "filmFit", modeDefault = Gaffer.TweakPlug.Mode.Remove, valuePlug = Gaffer.IntPlug() ) )
		self["CameraTweaks"]["tweaks"].addChild( Gaffer.TweakPlug( name = "apertureTweak", nameDefault = "aperture", modeDefault = Gaffer.TweakPlug.Mode.Remove, valuePlug = Gaffer.V2fPlug() ) )
		self["CameraTweaks"]["tweaks"].addChild( Gaffer.TweakPlug( name = "apertureOffsetTweak", nameDefault = "apertureOffset", modeDefault = Gaffer.TweakPlug.Mode.Remove, valuePlug = Gaffer.V2fPlug() ) )

		self["ArnoldCameraShaders"] = GafferArnold.ArnoldCameraShaders( "ArnoldCameraShaders" )

		self["ShaderAssignment"] = GafferScene.ShaderAssignment( "ShaderAssignment" )
		self["ShaderAssignment"]["in"].setInput( self["CameraTweaks"]["out"] )
		self["ShaderAssignment"]["filter"].setInput( self["PathFilter"]["out"] )
		self["ShaderAssignment"]["shader"].setInput( self["ArnoldCameraShaders"]["out"] )

		self["out"].setInput( self["ShaderAssignment"]["out"] )

		for p in [
			self["Camera"]["name"],
			self["Camera"]["sets"],
			self["Camera"]["transform"],
			self["Camera"]["fStop"],
			self["Camera"]["focalLengthWorldScale"],
			self["Camera"]["focusDistance"],
			self["Camera"]["renderSettingOverrides"],
			self["Camera"]["visualiserAttributes"],
		] :
			Gaffer.PlugAlgo.promote( p, excludeMetadata = "" )

		Gaffer.PlugAlgo.promoteWithName( self["NameSwitch"]["selector"], "type", excludeMetadata = "layout:* preset* divider" )

		self["CameraTweaksEnablerExpression"] = Gaffer.Expression()
		self["CameraTweaksEnablerExpression"].setExpression(
			inspect.cleandoc(
				"""
				parent["CameraTweaks"]["tweaks"]["shutterCurveTweak"]["enabled"] = parent["CameraTweaks"]["tweaks"]["shutterTypeTweak"]["value"] == "curve"
				parent["CameraTweaks"]["tweaks"]["rollingShutterDurationTweak"]["enabled"] = parent["CameraTweaks"]["tweaks"]["rollingShutterTweak"]["value"] != "off"
				parent["CameraTweaks"]["tweaks"]["filmFitTweak"]["enabled"] = parent["type"] != "fisheye"
				"""
			)
		)

		excludeMetadata = "layout:* nodule:type"
		Gaffer.PlugAlgo.promoteWithName( self["CylindricalTweaks"]["tweaks"]["horizontalFOVTweak"]["value"], "horizontalFOV", excludeMetadata = excludeMetadata )
		Gaffer.PlugAlgo.promoteWithName( self["CylindricalTweaks"]["tweaks"]["verticalFOVTweak"]["value"], "verticalFOV", excludeMetadata = excludeMetadata )
		Gaffer.PlugAlgo.promoteWithName( self["CylindricalTweaks"]["tweaks"]["projectiveTweak"]["value"], "projective", excludeMetadata = excludeMetadata )

		Gaffer.PlugAlgo.promoteWithName( self["FisheyeTweaks"]["tweaks"]["fovTweak"]["value"], "fov", excludeMetadata = excludeMetadata )
		Gaffer.PlugAlgo.promoteWithName( self["FisheyeTweaks"]["tweaks"]["autocropTweak"]["value"], "autocrop", excludeMetadata = excludeMetadata )
		Gaffer.PlugAlgo.promoteWithName( self["FisheyeTweaks"]["tweaks"]["apertureBladesTweak"]["value"], "apertureBlades", excludeMetadata = excludeMetadata )
		Gaffer.PlugAlgo.promoteWithName( self["FisheyeTweaks"]["tweaks"]["apertureBladeCurvatureTweak"]["value"], "apertureBladeCurvature", excludeMetadata = excludeMetadata )
		Gaffer.PlugAlgo.promoteWithName( self["FisheyeTweaks"]["tweaks"]["apertureRotationTweak"]["value"], "apertureRotation", excludeMetadata = excludeMetadata )
		Gaffer.PlugAlgo.promoteWithName( self["FisheyeTweaks"]["tweaks"]["apertureAspectRatioTweak"]["value"], "apertureAspectRatio", excludeMetadata = excludeMetadata )

		Gaffer.PlugAlgo.promoteWithName( self["VRTweaks"]["tweaks"]["modeTweak"]["value"], "mode", excludeMetadata = excludeMetadata )
		Gaffer.PlugAlgo.promoteWithName( self["VRTweaks"]["tweaks"]["vrProjectionTweak"]["value"], "projection", excludeMetadata = excludeMetadata )
		Gaffer.PlugAlgo.promoteWithName( self["VRTweaks"]["tweaks"]["eyeSeparationTweak"]["value"], "eyeSeparation", excludeMetadata = excludeMetadata )
		Gaffer.PlugAlgo.promoteWithName( self["VRTweaks"]["tweaks"]["eyeToNeckTweak"]["value"], "eyeToNeck", excludeMetadata = excludeMetadata )
		Gaffer.PlugAlgo.promoteWithName( self["VRTweaks"]["tweaks"]["topMergeModeTweak"]["value"], "topMergeMode", excludeMetadata = excludeMetadata )
		Gaffer.PlugAlgo.promoteWithName( self["VRTweaks"]["tweaks"]["topMergeAngleTweak"]["value"], "topMergeAngle", excludeMetadata = excludeMetadata )
		Gaffer.PlugAlgo.promoteWithName( self["VRTweaks"]["tweaks"]["bottomMergeModeTweak"]["value"], "bottomMergeMode", excludeMetadata = excludeMetadata )
		Gaffer.PlugAlgo.promoteWithName( self["VRTweaks"]["tweaks"]["bottomMergeAngleTweak"]["value"], "bottomMergeAngle", excludeMetadata = excludeMetadata )

		Gaffer.PlugAlgo.promoteWithName( self["CameraTweaks"]["tweaks"]["shutterTypeTweak"]["value"], "shutterType", excludeMetadata = excludeMetadata )
		Gaffer.PlugAlgo.promoteWithName( self["CameraTweaks"]["tweaks"]["shutterCurveTweak"]["value"], "shutterCurve", excludeMetadata = excludeMetadata )
		Gaffer.PlugAlgo.promoteWithName( self["CameraTweaks"]["tweaks"]["rollingShutterTweak"]["value"], "rollingShutter", excludeMetadata = excludeMetadata )
		Gaffer.PlugAlgo.promoteWithName( self["CameraTweaks"]["tweaks"]["rollingShutterDurationTweak"]["value"], "rollingShutterDuration", excludeMetadata = excludeMetadata )

		Gaffer.PlugAlgo.promote( self["ArnoldCameraShaders"]["filterMap"] )

		Gaffer.PlugAlgo.promote( self["Camera"]["clippingPlanes"] )


IECore.registerRunTimeTyped( ArnoldCamera, "GafferArnold::ArnoldCamera" )
