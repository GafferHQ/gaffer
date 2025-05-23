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

	import GafferArnold
	# Register Light Editor sections for Arnold before the generic "Visualisation" section
	import GafferArnoldUI

	Gaffer.Metadata.registerValue( GafferSceneUI.LightEditor.Settings, "attribute", "preset:Arnold", "ai:light" )
	# If Arnold is available, then assume it is the renderer of choice.
	Gaffer.Metadata.registerValue( GafferSceneUI.LightEditor.Settings, "attribute", "userDefault", "ai:light" )

	# Register Arnold-specific parameters for USD lights.
	for parameter in [
		"aov", "samples", "volume_samples", "sss", "indirect", "volume", "cast_volumetric_shadows",
		"max_bounces", "camera", "transmission", "spread", "roundness", "soft_edge", "resolution",
		"portal_mode", "aov_indirect"
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
