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
import os

import IECore
import Gaffer
import GafferSceneUI

# UsdLux lights

Gaffer.Metadata.registerValue( GafferSceneUI.LightEditor.Settings, "attribute", "preset:USD", "light" )

GafferSceneUI.LightEditor.registerParameter( "light", "color" )
GafferSceneUI.LightEditor.registerParameter( "light", "intensity" )
GafferSceneUI.LightEditor.registerParameter( "light", "exposure" )
GafferSceneUI.LightEditor.registerParameter( "light", "colorTemperature" )
GafferSceneUI.LightEditor.registerParameter( "light", "enableColorTemperature" )
GafferSceneUI.LightEditor.registerParameter( "light", "normalize" )
GafferSceneUI.LightEditor.registerParameter( "light", "diffuse" )
GafferSceneUI.LightEditor.registerParameter( "light", "specular" )

GafferSceneUI.LightEditor.registerParameter( "light", "width", "Geometry" )
GafferSceneUI.LightEditor.registerParameter( "light", "height", "Geometry" )
GafferSceneUI.LightEditor.registerParameter( "light", "radius", "Geometry" )
GafferSceneUI.LightEditor.registerParameter( "light", "treatAsPoint", "Geometry" )
GafferSceneUI.LightEditor.registerParameter( "light", "length", "Geometry" )
GafferSceneUI.LightEditor.registerParameter( "light", "treatAsLine", "Geometry" )
GafferSceneUI.LightEditor.registerParameter( "light", "angle", "Geometry" )

GafferSceneUI.LightEditor.registerParameter( "light", "texture:file", "Texture" )
GafferSceneUI.LightEditor.registerParameter( "light", "texture:format", "Texture" )

GafferSceneUI.LightEditor.registerParameter( "light", "shaping:cone:angle", "Shaping" )
GafferSceneUI.LightEditor.registerParameter( "light", "shaping:cone:softness", "Shaping" )
GafferSceneUI.LightEditor.registerParameter( "light", "shaping:focus", "Shaping" )
GafferSceneUI.LightEditor.registerParameter( "light", "shaping:focusTint", "Shaping" )
GafferSceneUI.LightEditor.registerParameter( "light", "shaping:ies:file", "Shaping" )
GafferSceneUI.LightEditor.registerParameter( "light", "shaping:ies:angleScale", "Shaping" )
GafferSceneUI.LightEditor.registerParameter( "light", "shaping:ies:normalize", "Shaping" )

GafferSceneUI.LightEditor.registerParameter( "light", "shadow:enable", "Shadow" )
GafferSceneUI.LightEditor.registerParameter( "light", "shadow:color", "Shadow" )
GafferSceneUI.LightEditor.registerParameter( "light", "shadow:distance", "Shadow" )
GafferSceneUI.LightEditor.registerParameter( "light", "shadow:falloff", "Shadow" )
GafferSceneUI.LightEditor.registerParameter( "light", "shadow:falloffGamma", "Shadow" )

if os.environ.get( "CYCLES_ROOT" ) and os.environ.get( "GAFFERCYCLES_HIDE_UI", "" ) != "1" :

	Gaffer.Metadata.registerValue( GafferSceneUI.LightEditor.Settings, "attribute", "preset:Cycles", "cycles:light" )

	GafferSceneUI.LightEditor.registerParameter( "cycles:light", "color" )
	GafferSceneUI.LightEditor.registerParameter( "cycles:light", "intensity" )
	GafferSceneUI.LightEditor.registerParameter( "cycles:light", "exposure" )
	GafferSceneUI.LightEditor.registerParameter( "cycles:light", "lightgroup" )

	GafferSceneUI.LightEditor.registerParameter( "cycles:light", "cast_shadow", "Contribution" )
	GafferSceneUI.LightEditor.registerParameter( "cycles:light", "use_diffuse", "Contribution" )
	GafferSceneUI.LightEditor.registerParameter( "cycles:light", "use_glossy", "Contribution" )
	GafferSceneUI.LightEditor.registerParameter( "cycles:light", "use_transmission", "Contribution" )
	GafferSceneUI.LightEditor.registerParameter( "cycles:light", "use_scatter", "Contribution" )
	GafferSceneUI.LightEditor.registerParameter( "cycles:light", "max_bounces", "Contribution" )

	GafferSceneUI.LightEditor.registerParameter( "cycles:light", "size", "Shape" )
	GafferSceneUI.LightEditor.registerParameter( "cycles:light", "spot_angle", "Shape" )
	GafferSceneUI.LightEditor.registerParameter( "cycles:light", "spot_smooth", "Shape" )
	GafferSceneUI.LightEditor.registerParameter( "cycles:light", "spread", "Shape" )
	GafferSceneUI.LightEditor.registerParameter( "cycles:light", "angle", "Shape" )
	GafferSceneUI.LightEditor.registerParameter( "cycles:light", "is_sphere", "Shape" )

	Gaffer.Metadata.registerValue( GafferSceneUI.LightEditor.Settings, "attribute", "userDefault", "cycles:light" )

	# Register Cycles-specific parameters for USD lights.
	for parameter in [
		"lightgroup",
		"use_mis", "use_camera", "use_diffuse", "use_glossy", "use_transmission", "use_scatter", "use_caustics",
		"spread", "map_resolution", "max_bounces"
	] :
		GafferSceneUI.LightEditor.registerParameter(
			"light", f"cycles:{parameter}", "Cycles",
			columnName = parameter.replace( "cycles:", "" )
		)


with IECore.IgnoredExceptions( ImportError ) :

	# This import appears unused, but it is intentional; it prevents us from
	# adding the OSL lights when 3Delight isn't available.
	import GafferDelight
	import GafferOSL

	shader = GafferOSL.OSLShader()

	for light in [
		"pointLight",
		"spotLight",
		"distantLight",
		"environmentLight"
	] :
		shader.loadShader( light )
		for parameter in shader["parameters"] :
			GafferSceneUI.LightEditor.registerParameter(
				"osl:light", parameter.getName(),
				shader.parameterMetadata( parameter, "page" )
			)

	Gaffer.Metadata.registerValue( GafferSceneUI.LightEditor.Settings, "attribute", "preset:OSL", "osl:light" )
	# If 3Delight is available, then assume it will be used in preference to Cycles.
	Gaffer.Metadata.registerValue( GafferSceneUI.LightEditor.Settings, "attribute", "userDefault", "osl:light" )


# Arnold lights

with IECore.IgnoredExceptions( ImportError ) :

	import arnold
	import GafferArnold

	Gaffer.Metadata.registerValue( GafferSceneUI.LightEditor.Settings, "attribute", "preset:Arnold", "ai:light" )
	# If Arnold is available, then assume it is the renderer of choice.
	Gaffer.Metadata.registerValue( GafferSceneUI.LightEditor.Settings, "attribute", "userDefault", "ai:light" )

	GafferSceneUI.LightEditor.registerParameter( "ai:light", "color" )
	GafferSceneUI.LightEditor.registerParameter( "ai:light", "intensity" )
	GafferSceneUI.LightEditor.registerParameter( "ai:light", "exposure" )
	GafferSceneUI.LightEditor.registerParameter( "ai:light", "normalize" )
	GafferSceneUI.LightEditor.registerParameter( "ai:light", "aov" )
	GafferSceneUI.LightEditor.registerParameter( "ai:light", "portal" )
	GafferSceneUI.LightEditor.registerParameter( "ai:light", "portal_mode" )
	GafferSceneUI.LightEditor.registerParameter( "ai:light", "aov_indirect" )

	GafferSceneUI.LightEditor.registerParameter( "ai:light", "width", "Shape" )
	GafferSceneUI.LightEditor.registerParameter( "ai:light", "height", "Shape" )
	GafferSceneUI.LightEditor.registerParameter( "ai:light", "radius", "Shape" )
	GafferSceneUI.LightEditor.registerParameter( "ai:light", "angle", "Shape" )
	GafferSceneUI.LightEditor.registerParameter( "ai:light", "roundness", "Shape" )
	GafferSceneUI.LightEditor.registerParameter( "ai:light", "soft_edge", "Shape" )
	GafferSceneUI.LightEditor.registerParameter( "ai:light", "spread", "Shape" )
	GafferSceneUI.LightEditor.registerParameter( "ai:light", "lens_radius", "Shape" )
	GafferSceneUI.LightEditor.registerParameter( "ai:light", "cone_angle", "Shape" )
	GafferSceneUI.LightEditor.registerParameter( "ai:light", "penumbra_angle", "Shape" )
	GafferSceneUI.LightEditor.registerParameter( "ai:light", "cosine_power", "Shape" )
	GafferSceneUI.LightEditor.registerParameter( "ai:light", "aspect_ratio", "Shape" )
	GafferSceneUI.LightEditor.registerParameter( "ai:light", "filename", "Shape" )

	GafferSceneUI.LightEditor.registerShaderParameter( "ai:light", "slidemap", "ai:lightFilter:gobo", "Gobo" )
	GafferSceneUI.LightEditor.registerShaderParameter( "ai:light", "rotate", "ai:lightFilter:gobo", "Gobo", "Transform Rotate" )
	GafferSceneUI.LightEditor.registerShaderParameter( "ai:light", "offset", "ai:lightFilter:gobo", "Gobo", "Transform Offset" )
	GafferSceneUI.LightEditor.registerShaderParameter( "ai:light", "density", "ai:lightFilter:gobo", "Gobo" )
	GafferSceneUI.LightEditor.registerShaderParameter( "ai:light", "filter_mode", "ai:lightFilter:gobo", "Gobo" )
	GafferSceneUI.LightEditor.registerShaderParameter( "ai:light", "swrap", "ai:lightFilter:gobo", "Gobo", "UV Coordinates Wrap U" )
	GafferSceneUI.LightEditor.registerShaderParameter( "ai:light", "twrap", "ai:lightFilter:gobo", "Gobo", "UV Coordinates Wrap V" )
	GafferSceneUI.LightEditor.registerShaderParameter( "ai:light", "sscale", "ai:lightFilter:gobo", "Gobo", "UV Coordinates Scale U" )
	GafferSceneUI.LightEditor.registerShaderParameter( "ai:light", "tscale", "ai:lightFilter:gobo", "Gobo", "UV Coordinates Scale V" )

	GafferSceneUI.LightEditor.registerShaderParameter( "ai:light", "barndoor_top_left", "ai:lightFilter:barndoor", "Barndoor", "Top Left" )
	GafferSceneUI.LightEditor.registerShaderParameter( "ai:light", "barndoor_top_right", "ai:lightFilter:barndoor", "Barndoor", "Top Right" )
	GafferSceneUI.LightEditor.registerShaderParameter( "ai:light", "barndoor_top_edge", "ai:lightFilter:barndoor", "Barndoor", "Top Edge" )
	GafferSceneUI.LightEditor.registerShaderParameter( "ai:light", "barndoor_right_top", "ai:lightFilter:barndoor", "Barndoor", "Right Top" )
	GafferSceneUI.LightEditor.registerShaderParameter( "ai:light", "barndoor_right_bottom", "ai:lightFilter:barndoor", "Barndoor", "Right Bottom" )
	GafferSceneUI.LightEditor.registerShaderParameter( "ai:light", "barndoor_right_edge", "ai:lightFilter:barndoor", "Barndoor", "Right Edge" )
	GafferSceneUI.LightEditor.registerShaderParameter( "ai:light", "barndoor_bottom_left", "ai:lightFilter:barndoor", "Barndoor", "Bottom Left" )
	GafferSceneUI.LightEditor.registerShaderParameter( "ai:light", "barndoor_bottom_right", "ai:lightFilter:barndoor", "Barndoor", "Bottom Right" )
	GafferSceneUI.LightEditor.registerShaderParameter( "ai:light", "barndoor_bottom_edge", "ai:lightFilter:barndoor", "Barndoor", "Bottom Edge" )
	GafferSceneUI.LightEditor.registerShaderParameter( "ai:light", "barndoor_left_top", "ai:lightFilter:barndoor", "Barndoor", "Left Top" )
	GafferSceneUI.LightEditor.registerShaderParameter( "ai:light", "barndoor_left_bottom", "ai:lightFilter:barndoor", "Barndoor", "Left Bottom" )
	GafferSceneUI.LightEditor.registerShaderParameter( "ai:light", "barndoor_left_edge", "ai:lightFilter:barndoor", "Barndoor", "Left Edge" )

	GafferSceneUI.LightEditor.registerShaderParameter( "ai:light", "geometry_type", "ai:lightFilter:filter", "Blocker" )
	GafferSceneUI.LightEditor.registerShaderParameter( "ai:light", "density", "ai:lightFilter:filter", "Blocker" )
	GafferSceneUI.LightEditor.registerShaderParameter( "ai:light", "roundness", "ai:lightFilter:filter", "Blocker" )
	GafferSceneUI.LightEditor.registerShaderParameter( "ai:light", "width_edge", "ai:lightFilter:filter", "Blocker", "Falloff Width Edge" )
	GafferSceneUI.LightEditor.registerShaderParameter( "ai:light", "height_edge", "ai:lightFilter:filter", "Blocker", "Falloff Height Edge" )
	GafferSceneUI.LightEditor.registerShaderParameter( "ai:light", "ramp", "ai:lightFilter:filter", "Blocker", "Falloff Ramp" )
	GafferSceneUI.LightEditor.registerShaderParameter( "ai:light", "axis", "ai:lightFilter:filter", "Blocker", "Falloff Axis" )
	GafferSceneUI.LightEditor.registerShaderParameter( "ai:light", "shader", "ai:lightFilter:filter", "Blocker" )
	GafferSceneUI.LightEditor.registerAttribute( "ai:light", "filteredLights", "Blocker" )

	GafferSceneUI.LightEditor.registerShaderParameter( "ai:light", "use_near_atten", "ai:lightFilter:light_decay", "Decay", "Near Enable" )
	GafferSceneUI.LightEditor.registerShaderParameter( "ai:light", "use_far_atten", "ai:lightFilter:light_decay", "Decay", "Far Enable" )
	GafferSceneUI.LightEditor.registerShaderParameter( "ai:light", "near_start", "ai:lightFilter:light_decay", "Decay" )
	GafferSceneUI.LightEditor.registerShaderParameter( "ai:light", "near_end", "ai:lightFilter:light_decay", "Decay" )
	GafferSceneUI.LightEditor.registerShaderParameter( "ai:light", "far_start", "ai:lightFilter:light_decay", "Decay", "Far Start" )
	GafferSceneUI.LightEditor.registerShaderParameter( "ai:light", "far_end", "ai:lightFilter:light_decay", "Decay", "Far End" )

	GafferSceneUI.LightEditor.registerParameter( "ai:light", "samples", "Sampling" )
	GafferSceneUI.LightEditor.registerParameter( "ai:light", "volume_samples", "Sampling" )
	if [ int( x ) for x in arnold.AiGetVersion()[:3] ] >= [ 7, 4, 4 ] :
		GafferSceneUI.LightEditor.registerParameter( "ai:light", "sampling_mode", "Sampling" )

	GafferSceneUI.LightEditor.registerParameter( "ai:light", "cast_shadows", "Shadows" )
	GafferSceneUI.LightEditor.registerParameter( "ai:light", "cast_volumetric_shadows", "Shadows" )
	GafferSceneUI.LightEditor.registerParameter( "ai:light", "shadow_density", "Shadows" )
	GafferSceneUI.LightEditor.registerParameter( "ai:light", "shadow_color", "Shadows" )

	GafferSceneUI.LightEditor.registerParameter( "ai:light", "camera", "Contribution" )
	GafferSceneUI.LightEditor.registerParameter( "ai:light", "transmission", "Contribution" )
	GafferSceneUI.LightEditor.registerParameter( "ai:light", "diffuse", "Contribution" )
	GafferSceneUI.LightEditor.registerParameter( "ai:light", "specular", "Contribution" )
	GafferSceneUI.LightEditor.registerParameter( "ai:light", "sss", "Contribution" )
	GafferSceneUI.LightEditor.registerParameter( "ai:light", "indirect", "Contribution" )
	GafferSceneUI.LightEditor.registerParameter( "ai:light", "volume", "Contribution" )
	GafferSceneUI.LightEditor.registerParameter( "ai:light", "max_bounces", "Contribution" )

	GafferSceneUI.LightEditor.registerParameter( "ai:light", "shader", "Map" )
	GafferSceneUI.LightEditor.registerParameter( "ai:light", "resolution", "Map" )
	GafferSceneUI.LightEditor.registerParameter( "ai:light", "format", "Map" )

	# Register Arnold-specific parameters for USD lights.
	for parameter in [
		"aov", "samples", "volume_samples", "sss", "indirect", "volume", "cast_volumetric_shadows",
		"max_bounces", "camera", "transmission", "spread", "roundness", "soft_edge", "resolution",
		"portal_mode", "aov_indirect", "lens_radius", "aspect_ratio", "shadow_density"
	] :
		GafferSceneUI.LightEditor.registerParameter(
			"light", f"arnold:{parameter}", "Arnold",
			columnName = parameter.replace( "arnold:", "" )
		)

# RenderMan lights

if os.environ.get( "GAFFERRENDERMAN_HIDE_UI", "" ) != "1" :

	with IECore.IgnoredExceptions( ImportError ) :

		# This import appears unused, but it is intentional; it prevents us from
		# registering when RenderMan isn't available.
		import GafferRenderMan

		Gaffer.Metadata.registerValue( GafferSceneUI.LightEditor.Settings, "attribute", "preset:RenderMan", "ri:light" )
		# If RenderMan is available, then assume it is the renderer of choice.
		Gaffer.Metadata.registerValue( GafferSceneUI.LightEditor.Settings, "attribute", "userDefault", "ri:light" )

		GafferSceneUI.LightEditor.registerParameter( "ri:light", "intensity" )
		GafferSceneUI.LightEditor.registerParameter( "ri:light", "exposure" )
		GafferSceneUI.LightEditor.registerParameter( "ri:light", "lightColor" )
		GafferSceneUI.LightEditor.registerParameter( "ri:light", "enableTemperature" )
		GafferSceneUI.LightEditor.registerParameter( "ri:light", "temperature" )
		GafferSceneUI.LightEditor.registerParameter( "ri:light", "lightColorMap" )
		GafferSceneUI.LightEditor.registerParameter( "ri:light", "colorMapGamma" )
		GafferSceneUI.LightEditor.registerParameter( "ri:light", "colorMapSaturation" )
		GafferSceneUI.LightEditor.registerParameter( "ri:light", "angleExtent" )
		GafferSceneUI.LightEditor.registerParameter( "ri:light", "textureColor" )

		GafferSceneUI.LightEditor.registerParameter( "ri:light", "emissionFocus", "Refine" )
		GafferSceneUI.LightEditor.registerParameter( "ri:light", "emissionFocusNormalize", "Refine" )
		GafferSceneUI.LightEditor.registerParameter( "ri:light", "emissionFocusTint", "Refine" )
		GafferSceneUI.LightEditor.registerParameter( "ri:light", "specular", "Refine" )
		GafferSceneUI.LightEditor.registerParameter( "ri:light", "diffuse", "Refine" )
		GafferSceneUI.LightEditor.registerParameter( "ri:light", "intensityNearDist", "Refine" )
		GafferSceneUI.LightEditor.registerParameter( "ri:light", "specularNearDist", "Refine" )
		GafferSceneUI.LightEditor.registerParameter( "ri:light", "diffuseNearDist", "Refine" )
		GafferSceneUI.LightEditor.registerParameter( "ri:light", "coneAngle", "Refine" )
		GafferSceneUI.LightEditor.registerParameter( "ri:light", "coneSoftness", "Refine" )

		GafferSceneUI.LightEditor.registerParameter( "ri:light", "iesProfile", "Light Profile" )
		GafferSceneUI.LightEditor.registerParameter( "ri:light", "iesProfileScale", "Light Profile" )
		GafferSceneUI.LightEditor.registerParameter( "ri:light", "iesProfileNormalize", "Light Profile" )

		GafferSceneUI.LightEditor.registerParameter( "ri:light", "enableShadows", "Shadows" )
		GafferSceneUI.LightEditor.registerParameter( "ri:light", "shadowColor", "Shadows" )
		GafferSceneUI.LightEditor.registerParameter( "ri:light", "shadowDistance", "Shadows" )
		GafferSceneUI.LightEditor.registerParameter( "ri:light", "shadowFalloff", "Shadows" )
		GafferSceneUI.LightEditor.registerParameter( "ri:light", "shadowFalloffGamma", "Shadows" )
		GafferSceneUI.LightEditor.registerParameter( "ri:light", "shadowSubset", "Shadows" )
		GafferSceneUI.LightEditor.registerParameter( "ri:light", "shadowExcludeSubset", "Shadows" )

		GafferSceneUI.LightEditor.registerParameter( "ri:light", "sunDirection", "Day Light" )
		GafferSceneUI.LightEditor.registerParameter( "ri:light", "haziness", "Day Light" )
		GafferSceneUI.LightEditor.registerParameter( "ri:light", "skyTint", "Day Light" )
		GafferSceneUI.LightEditor.registerParameter( "ri:light", "sunTint", "Day Light" )
		GafferSceneUI.LightEditor.registerParameter( "ri:light", "sunSize", "Day Light" )
		GafferSceneUI.LightEditor.registerParameter( "ri:light", "groundMode", "Day Light" )
		GafferSceneUI.LightEditor.registerParameter( "ri:light", "groundColor", "Day Light" )
		GafferSceneUI.LightEditor.registerParameter( "ri:light", "month", "Day Light" )
		GafferSceneUI.LightEditor.registerParameter( "ri:light", "day", "Day Light" )
		GafferSceneUI.LightEditor.registerParameter( "ri:light", "year", "Day Light" )
		GafferSceneUI.LightEditor.registerParameter( "ri:light", "hour", "Day Light" )
		GafferSceneUI.LightEditor.registerParameter( "ri:light", "zone", "Day Light" )
		GafferSceneUI.LightEditor.registerParameter( "ri:light", "latitude", "Day Light" )
		GafferSceneUI.LightEditor.registerParameter( "ri:light", "longitude", "Day Light" )

		GafferSceneUI.LightEditor.registerParameter( "ri:light", "areaNormalize", "Advanced" )
		GafferSceneUI.LightEditor.registerParameter( "ri:light", "traceLightPaths", "Advanced" )
		GafferSceneUI.LightEditor.registerParameter( "ri:light", "thinShadow", "Advanced" )
		GafferSceneUI.LightEditor.registerParameter( "ri:light", "visibleInRefractionPath", "Advanced" )
		GafferSceneUI.LightEditor.registerParameter( "ri:light", "cheapCaustics", "Advanced" )
		GafferSceneUI.LightEditor.registerParameter( "ri:light", "cheapCausticsExcludeGroup", "Advanced" )
		GafferSceneUI.LightEditor.registerParameter( "ri:light", "fixedSampleCount", "Advanced" )
		GafferSceneUI.LightEditor.registerParameter( "ri:light", "lightGroup", "Advanced" )
		GafferSceneUI.LightEditor.registerParameter( "ri:light", "importanceMultiplier", "Advanced" )

		GafferSceneUI.LightEditor.registerParameter( "ri:light", "msApprox", "Multi-Scattering Approx" )
		GafferSceneUI.LightEditor.registerParameter( "ri:light", "msApproxBleed", "Multi-Scattering Approx" )
		GafferSceneUI.LightEditor.registerParameter( "ri:light", "msApproxContribution", "Multi-Scattering Approx" )

# Register generic light attributes
for attributeName in [
	"gl:visualiser:scale",
	"gl:visualiser:maxTextureResolution",
	"gl:visualiser:frustum",
	"gl:light:frustumScale",
	"gl:light:drawingMode",
] :
	GafferSceneUI.LightEditor.registerAttribute( "*", attributeName, "Visualisation" )

# Register transform columns

def transformColumn( scene, editScope, space, component ) :

	inspector = GafferSceneUI.Private.TransformInspector( scene, editScope, space, component )
	return GafferSceneUI.Private.InspectorColumn( inspector )

for space in GafferSceneUI.Private.TransformInspector.Space.values.values() :
	for component in GafferSceneUI.Private.TransformInspector.Component.values.values() :
		if component == GafferSceneUI.Private.TransformInspector.Component.Matrix :
			continue
		GafferSceneUI.LightEditor.registerColumn(
			"*",
			f"{space}.{component}",
			functools.partial( transformColumn, space = space, component = component ),
			"Transform"
		)
