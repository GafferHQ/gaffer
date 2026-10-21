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
import GafferScene
import GafferArnold

class ArnoldCamera( Gaffer.DependencyNode ) :

	def __init__( self, name = "ArnoldCamera" ) :

		Gaffer.DependencyNode.__init__( self, name )

		# Promote internal camera plugs
		self["Camera"] = GafferScene.Camera( "Camera" )
		for p in [
			self["Camera"]["name"],
			self["Camera"]["sets"],
			self["Camera"]["transform"],
			self["Camera"]["fStop"],
			self["Camera"]["focalLengthWorldScale"],
			self["Camera"]["focusDistance"],
			self["Camera"]["renderSettingOverrides"],
			self["Camera"]["visualiserAttributes"],
			self["Camera"]["enabled"],
		] :
			Gaffer.PlugAlgo.promote( p )

		# ArnoldCamera-specific plugs
		self["cameraType"] = Gaffer.StringPlug( "cameraType", defaultValue = "cylindrical" )
		# Cylindrical
		self["cylindricalHorizontalFOV"] = Gaffer.FloatPlug( "cylindricalHorizontalFOV", defaultValue = 60.0 )
		self["cylindricalVerticalFOV"] = Gaffer.FloatPlug( "cylindricalVerticalFOV", defaultValue = 90.0 )
		self["projective"] = Gaffer.BoolPlug( "projective", defaultValue = True )
		# Fisheye
		self["fisheyeFOV"] = Gaffer.FloatPlug( "fisheyeFOV", defaultValue = 90.0 )
		self["autocrop"] = Gaffer.BoolPlug( "autocrop", defaultValue = False )

		# Spherical has no parameters

		# VR
		self["mode"] = Gaffer.StringPlug( "mode", defaultValue = "side_by_side" )
		self["projection"] = Gaffer.StringPlug( "projection", defaultValue = "latlong" )
		self["eyeSeparation"] = Gaffer.FloatPlug( "eyeSeparation", defaultValue = 0.65 )
		self["eyeToNeck"] = Gaffer.FloatPlug( "eyeToNeck", defaultValue = 0.0 )
		self["topMergeMode"] = Gaffer.StringPlug( "topMergeMode", defaultValue = "cosine" )
		self["topMergeAngle"] = Gaffer.FloatPlug( "topMergeAngle", defaultValue = 90.0, minValue = 0.0, maxValue = 180.0 )
		self["bottomMergeMode"] = Gaffer.StringPlug( "bottomMergeMode", defaultValue = "cosine" )
		self["bottomMergeAngle"] = Gaffer.FloatPlug( "bottomMergeAngle", defaultValue = 90.0, minValue = 0.0, maxValue = 180.0 )

		# Create internal network and connect ArnoldCamera plugs

		self["PathFilter"] = GafferScene.PathFilter( "PathFilter" )
		self["PathFilter"]["paths"].setInput( self["Camera"]["name"] )

		self["CylindricalTweaks"] = GafferScene.CameraTweaks( "CylindricalTweaks" )
		self["CylindricalTweaks"]["in"].setInput( self["Camera"]["out"] )
		self["CylindricalTweaks"]["filter"].setInput( self["PathFilter"]["out"] )
		self["CylindricalTweaks"]["tweaks"].addChild( Gaffer.TweakPlug( name = "projectionTweak", nameDefault = "projection", valuePlug = Gaffer.StringPlug( "value", defaultValue = "cyl_camera" ) ) )
		self["CylindricalTweaks"]["tweaks"].addChild( Gaffer.TweakPlug( name = "projectiveTweak", nameDefault = "ai:projective", valuePlug = Gaffer.BoolPlug( "value", defaultValue = False ) ) )
		self["CylindricalTweaks"]["tweaks"].addChild( Gaffer.TweakPlug( name = "horizontalFOVTweak", nameDefault = "ai:horizontal_fov", valuePlug = Gaffer.FloatPlug( "value", defaultValue = 0.0 ) ) )
		self["CylindricalTweaks"]["tweaks"].addChild( Gaffer.TweakPlug( name = "verticalFOVTweak", nameDefault = "ai:vertical_fov", valuePlug = Gaffer.FloatPlug( "value", defaultValue = 0.0 ) ) )

		self["CylindricalTweaks"]["tweaks"]["projectiveTweak"]["value"].setInput( self["projective"] )
		self["CylindricalTweaks"]["tweaks"]["horizontalFOVTweak"]["value"].setInput( self["cylindricalHorizontalFOV"] )
		self["CylindricalTweaks"]["tweaks"]["verticalFOVTweak"]["value"].setInput( self["cylindricalVerticalFOV"] )

		self["FisheyeTweaks"] = GafferScene.CameraTweaks( "FisheyeTweaks" )
		self["FisheyeTweaks"]["in"].setInput( self["Camera"]["out"] )
		self["FisheyeTweaks"]["filter"].setInput( self["PathFilter"]["out"] )
		self["FisheyeTweaks"]["tweaks"].addChild( Gaffer.TweakPlug( name = "projectionTweak", nameDefault = "projection", valuePlug = Gaffer.StringPlug( "value", defaultValue = "fisheye_camera" ) ) )
		self["FisheyeTweaks"]["tweaks"].addChild( Gaffer.TweakPlug( name = "fovTweak", nameDefault = "ai:fov", valuePlug = Gaffer.FloatPlug( "value", defaultValue = 0.0 ) ) )
		self["FisheyeTweaks"]["tweaks"].addChild( Gaffer.TweakPlug( name = "autocropTweak", nameDefault = "ai:autocrop", valuePlug = Gaffer.BoolPlug( "value", defaultValue = False ) ) )

		self["FisheyeTweaks"]["tweaks"]["fovTweak"]["value"].setInput( self["fisheyeFOV"] )
		self["FisheyeTweaks"]["tweaks"]["autocropTweak"]["value"].setInput( self["autocrop"] )

		self["SphericalTweaks"] = GafferScene.CameraTweaks( "SphericalTweaks" )
		self["SphericalTweaks"]["in"].setInput( self["Camera"]["out"] )
		self["SphericalTweaks"]["filter"].setInput( self["PathFilter"]["out"] )
		self["SphericalTweaks"]["tweaks"].addChild( Gaffer.TweakPlug( name = "projectionTweak", nameDefault = "projection", valuePlug = Gaffer.StringPlug( "value", defaultValue = "spherical_camera" ) ) )

		self["VRTweaks"] = GafferScene.CameraTweaks( "VRTweaks" )
		self["VRTweaks"]["in"].setInput( self["Camera"]["out"] )
		self["VRTweaks"]["filter"].setInput( self["PathFilter"]["out"] )
		self["VRTweaks"]["tweaks"].addChild( Gaffer.TweakPlug( name = "projectionTweak", nameDefault = "projection", valuePlug = Gaffer.StringPlug( "value", defaultValue = "vr_camera" ) ) )
		self["VRTweaks"]["tweaks"].addChild( Gaffer.TweakPlug( name = "modeTweak", nameDefault = "ai:mode", valuePlug = Gaffer.StringPlug( "value", defaultValue = "" ) ) )
		self["VRTweaks"]["tweaks"].addChild( Gaffer.TweakPlug( name = "vrProjectionTweak", nameDefault = "ai:projection", valuePlug = Gaffer.StringPlug( "value", defaultValue = "" ) ) )
		self["VRTweaks"]["tweaks"].addChild( Gaffer.TweakPlug( name = "eyeSeparationTweak", nameDefault = "ai:eye_separation", valuePlug = Gaffer.FloatPlug( "value", defaultValue = 0.0 ) ) )
		self["VRTweaks"]["tweaks"].addChild( Gaffer.TweakPlug( name = "eyeToNeckTweak", nameDefault = "ai:eye_to_neck", valuePlug = Gaffer.FloatPlug( "value", defaultValue = 0.0 ) ) )
		self["VRTweaks"]["tweaks"].addChild( Gaffer.TweakPlug( name = "topMergeModeTweak", nameDefault = "ai:top_merge_mode", valuePlug = Gaffer.StringPlug( "value", defaultValue = "" ) ) )
		self["VRTweaks"]["tweaks"].addChild( Gaffer.TweakPlug( name = "topMergeAngleTweak", nameDefault = "ai:top_merge_angle", valuePlug = Gaffer.FloatPlug( "value", defaultValue = 0.0 ) ) )
		self["VRTweaks"]["tweaks"].addChild( Gaffer.TweakPlug( name = "bottomMergeModeTweak", nameDefault = "ai:bottom_merge_mode", valuePlug = Gaffer.StringPlug( "value", defaultValue = "" ) ) )
		self["VRTweaks"]["tweaks"].addChild( Gaffer.TweakPlug( name = "bottomMergeAngleTweak", nameDefault = "ai:bottom_merge_angle", valuePlug = Gaffer.FloatPlug( "value", defaultValue = 0.0 ) ) )

		self["VRTweaks"]["tweaks"]["modeTweak"]["value"].setInput( self["mode"] )
		self["VRTweaks"]["tweaks"]["vrProjectionTweak"]["value"].setInput( self["projection"] )
		self["VRTweaks"]["tweaks"]["eyeSeparationTweak"]["value"].setInput( self["eyeSeparation"] )
		self["VRTweaks"]["tweaks"]["eyeToNeckTweak"]["value"].setInput( self["eyeToNeck"] )
		self["VRTweaks"]["tweaks"]["topMergeModeTweak"]["value"].setInput( self["topMergeMode"] )
		self["VRTweaks"]["tweaks"]["topMergeAngleTweak"]["value"].setInput( self["topMergeAngle"] )
		self["VRTweaks"]["tweaks"]["bottomMergeModeTweak"]["value"].setInput( self["bottomMergeMode"] )
		self["VRTweaks"]["tweaks"]["bottomMergeAngleTweak"]["value"].setInput( self["bottomMergeAngle"] )

		for t in [ "CylindricalTweaks", "FisheyeTweaks", "SphericalTweaks", "VRTweaks" ] :
			for p in self[t]["tweaks"] :
				p["mode"].setValue( Gaffer.TweakPlug.Mode.Create )

		self["NameSwitch"] = Gaffer.NameSwitch( "NameSwitch" )
		self["NameSwitch"].setup( self["Camera"]["out"] )
		self["NameSwitch"]["selector"].setInput( self["cameraType"] )
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
		# \todo Create tweaks from metadata / CameraTweaks method?

		self["ArnoldCameraShaders"] = GafferArnold.ArnoldCameraShaders( "ArnoldCameraShaders" )
		Gaffer.PlugAlgo.promote( self["ArnoldCameraShaders"]["filterMap"] )

		self["ShaderAssignment"] = GafferScene.ShaderAssignment( "ShaderAssignment" )
		self["ShaderAssignment"]["in"].setInput( self["CameraTweaks"]["out"] )
		self["ShaderAssignment"]["filter"].setInput( self["PathFilter"]["out"] )
		self["ShaderAssignment"]["shader"].setInput( self["ArnoldCameraShaders"]["out"] )

		Gaffer.PlugAlgo.promote( self["Camera"]["clippingPlanes"] )

		Gaffer.PlugAlgo.promote( self["ShaderAssignment"]["out"] )

IECore.registerRunTimeTyped( ArnoldCamera, "GafferArnold::ArnoldCamera" )
