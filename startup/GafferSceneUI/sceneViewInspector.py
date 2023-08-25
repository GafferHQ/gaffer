##########################################################################
#
#  Copyright (c) 2020, Cinesite VFX Ltd. All rights reserved.
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
#      * Neither the name of Cinesite VFX Ltd. nor the names of
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

import GafferSceneUI


# Arnold

for p in [ "exposure", "color", "width", "height", "radius", "roundness", "spread", "cone_angle", "penumbra_angle", "samples", "aov" ] :
	GafferSceneUI._SceneViewInspector.registerShaderParameter( "ai:light", p )

for p in ["geometry_type", "density", "filtered_lights", "shader" ] :
	GafferSceneUI._SceneViewInspector.registerShaderParameter( "ai:lightFilter:filter", p )

for p in [
	"barndoor_top_left", "barndoor_top_right", "barndoor_top_edge", "barndoor_right_top", "barndoor_right_bottom", "barndoor_right_edge",
	"barndoor_bottom_left", "barndoor_bottom_right", "barndoor_bottom_edge", "barndoor_left_top", "barndoor_left_bottom", "barndoor_left_edge"
] :
	GafferSceneUI._SceneViewInspector.registerShaderParameter( "ai:lightFilter:barndoor", p )

for p in [ "filter_mode", "density", "rotate", "offset" ] :
	GafferSceneUI._SceneViewInspector.registerShaderParameter( "ai:lightFilter:gobo", p )

for p in [ "use_near_atten", "near_start", "near_end", "use_far_atten", "far_start", "far_end" ] :
	GafferSceneUI._SceneViewInspector.registerShaderParameter( "ai:lightFilter:light_decay", p )

for p in ["base", "base_color", "diffuse_roughness", "metallness", "specular", "specular_color", "specular_roughness" ] :
	GafferSceneUI._SceneViewInspector.registerShaderParameter( "ai:surface", p )

# OSL

for p in [ "exposure", "i_color", "radius", "roundness", "spread", "coneAngle", "penumbraAngle", "image" ] :
	GafferSceneUI._SceneViewInspector.registerShaderParameter( "osl:light", p )

# Cycles

for p in [ "intensity", "exposure", "color", "size", "spot_angle", "samples" ] :
	GafferSceneUI._SceneViewInspector.registerShaderParameter( "cycles:light", p )

for p in ["base_color", "subsurface_color", "metallic", "subsurface", "subsurface_radius", "specular", "roughness", "specular_tint" ] :
	GafferSceneUI._SceneViewInspector.registerShaderParameter( "cycles:surface", p )

# USD

for p in [ "intensity", "exposure", "color", "enableColorTemperature", "colorTemperature", "width", "height", "radius", "angle", "shaping:cone:angle", "shaping:cone:softness" ] :
	GafferSceneUI._SceneViewInspector.registerShaderParameter( "light", p )

for p in [ "diffuseColor", "emissiveColor", "useSpecularWorkflow", "specularColor", "metallic", "roughness", "clearcoat", "clearcoatRoughness" ] :
	GafferSceneUI._SceneViewInspector.registerShaderParameter( "surface", p )
