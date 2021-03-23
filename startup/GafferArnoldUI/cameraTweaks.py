##########################################################################
#
#  Copyright (c) 2021, Cinesite VFX Ltd. All rights reserved.
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

import IECore
import Gaffer
import GafferScene
import GafferSceneUI

def __tweakCreator( plugName, parameterName, parameterValue ) :

	tweak = GafferScene.TweakPlug( parameterName, parameterValue )
	tweak.setName( plugName )
	return tweak

def __shutterCurveTweakCreator() :

	tweak = GafferScene.TweakPlug(
		"shutter_curve",
		Gaffer.SplineffPlug(
			defaultValue = Gaffer.SplineDefinitionff(
				[ ( 0, 0 ), ( 0.25, 1 ), (0.75, 1 ), ( 1, 0 ) ],
				Gaffer.SplineDefinitionInterpolation.Linear
			)
		)
	)
	tweak.setName( "shutterCurve" )
	return tweak

GafferSceneUI.CameraTweaksUI.registerTweak( "Arnold/Shutter Type", functools.partial( __tweakCreator, "shutterType", "shutter_type", "box" ) )
GafferSceneUI.CameraTweaksUI.registerTweak( "Arnold/Shutter Curve", __shutterCurveTweakCreator )
GafferSceneUI.CameraTweaksUI.registerTweak( "Arnold/Rolling Shutter", functools.partial( __tweakCreator, "rollingShutter", "rolling_shutter", "off" ) )
GafferSceneUI.CameraTweaksUI.registerTweak( "Arnold/Rolling Shutter Duration", functools.partial( __tweakCreator, "rollingShutterDuration", "rolling_shutter_duration", 0.0 ) )
GafferSceneUI.CameraTweaksUI.registerTweak( "Arnold/Aperture Blades", functools.partial( __tweakCreator, "apertureBlades", "aperture_blades", 6 ) )
GafferSceneUI.CameraTweaksUI.registerTweak( "Arnold/Aperture Blade Curvature", functools.partial( __tweakCreator, "apertureBladeCurvature", "aperture_blade_curvature", 0.0 ) )
GafferSceneUI.CameraTweaksUI.registerTweak( "Arnold/Aperture Rotation", functools.partial( __tweakCreator, "apertureRotation", "aperture_rotation", 0.0 ) )

Gaffer.Metadata.registerNode(

	GafferScene.CameraTweaks,

	plugs = {

		"tweaks.shutterType.name" : [
			"readOnly", True,
		],

		"tweaks.shutterType.value" : [

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
			"preset:Box", "box",
			"preset:Triangle", "triangle",
			"preset:Curve", "curve",

		],

		"tweaks.shutterCurve.name" : [
			"readOnly", True,
		],

		"tweaks.rollingShutter.name" : [
			"readOnly", True,
		],

		"tweaks.rollingShutter.value" : [

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
			"preset:Off", "off",
			"preset:Top", "top",
			"preset:Bottom", "bottom",
			"preset:Left", "left",
			"preset:Right", "right",

		],

		"tweaks.rollingShutterDuration.name" : [
			"readOnly", True,
		],

		"tweaks.apertureBlades.name" : [
			"readOnly", True,
		],

		"tweaks.apertureBladeCurvature.name" : [
			"readOnly", True,
		],

		"tweaks.apertureRotation.name" : [
			"readOnly", True,
		],

	}

)
