##########################################################################
#
#  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
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

## \todo Investigate alternatives to these manual registrations, perhaps we could register
# "Section" metadata for each attribute and use it here and in the Node Editor UI?

Gaffer.Metadata.registerValue( GafferSceneUI.AttributeEditor.Settings, "tabGroup", "preset:Standard", "Standard" )
Gaffer.Metadata.registerValue( GafferSceneUI.AttributeEditor.Settings, "tabGroup", "userDefault", "Standard" )

GafferSceneUI.AttributeEditor.registerAttribute( "Standard", "scene:visible", "Attributes" )
GafferSceneUI.AttributeEditor.registerAttribute( "Standard", "render:displayColor", "Attributes" )
GafferSceneUI.AttributeEditor.registerAttribute( "Standard", "doubleSided", "Attributes" )

GafferSceneUI.AttributeEditor.registerAttribute( "Standard", "gaffer:transformBlur", "Motion Blur" )
GafferSceneUI.AttributeEditor.registerAttribute( "Standard", "gaffer:transformBlurSegments", "Motion Blur" )
GafferSceneUI.AttributeEditor.registerAttribute( "Standard", "gaffer:deformationBlur", "Motion Blur" )
GafferSceneUI.AttributeEditor.registerAttribute( "Standard", "gaffer:deformationBlurSegments", "Motion Blur" )

GafferSceneUI.AttributeEditor.registerAttribute( "Standard", "linkedLights", "Light Linking" )
GafferSceneUI.AttributeEditor.registerAttribute( "Standard", "filteredLights", "Light Linking" )

GafferSceneUI.AttributeEditor.registerAttribute( "Standard", "gaffer:automaticInstancing", "Instancing" )

GafferSceneUI.AttributeEditor.registerAttribute( "Standard", "light:mute", "Light" )

Gaffer.Metadata.registerValue( GafferSceneUI.AttributeEditor.Settings, "tabGroup", "preset:USD", "USD" )

GafferSceneUI.AttributeEditor.registerAttribute( "USD", "usd:kind", "Attributes" )
GafferSceneUI.AttributeEditor.registerAttribute( "USD", "usd:purpose", "Attributes" )

with IECore.IgnoredExceptions( ImportError ) :

	# This import appears unused, but it is intentional; it prevents us from
	# registering when Arnold isn't available.
	import GafferArnold

	Gaffer.Metadata.registerValue( GafferSceneUI.AttributeEditor.Settings, "tabGroup", "preset:Arnold", "Arnold" )

	GafferSceneUI.AttributeEditor.registerAttribute( "Arnold", "ai:visibility:camera", "Visibility" )
	GafferSceneUI.AttributeEditor.registerAttribute( "Arnold", "ai:visibility:shadow", "Visibility" )
	GafferSceneUI.AttributeEditor.registerAttribute( "Arnold", "ai:visibility:shadow_group", "Visibility" )
	GafferSceneUI.AttributeEditor.registerAttribute( "Arnold", "ai:visibility:diffuse_reflect", "Visibility" )
	GafferSceneUI.AttributeEditor.registerAttribute( "Arnold", "ai:visibility:specular_reflect", "Visibility" )
	GafferSceneUI.AttributeEditor.registerAttribute( "Arnold", "ai:visibility:diffuse_transmit", "Visibility" )
	GafferSceneUI.AttributeEditor.registerAttribute( "Arnold", "ai:visibility:specular_transmit", "Visibility" )
	GafferSceneUI.AttributeEditor.registerAttribute( "Arnold", "ai:visibility:volume", "Visibility" )
	GafferSceneUI.AttributeEditor.registerAttribute( "Arnold", "ai:visibility:subsurface", "Visibility" )

	GafferSceneUI.AttributeEditor.registerAttribute( "Arnold", "ai:disp_autobump", "Displacement" )
	GafferSceneUI.AttributeEditor.registerAttribute( "Arnold", "ai:autobump_visibility:camera", "Displacement" )
	GafferSceneUI.AttributeEditor.registerAttribute( "Arnold", "ai:autobump_visibility:shadow", "Displacement" )
	GafferSceneUI.AttributeEditor.registerAttribute( "Arnold", "ai:autobump_visibility:diffuse_reflect", "Displacement" )
	GafferSceneUI.AttributeEditor.registerAttribute( "Arnold", "ai:autobump_visibility:specular_reflect", "Displacement" )
	GafferSceneUI.AttributeEditor.registerAttribute( "Arnold", "ai:autobump_visibility:diffuse_transmit", "Displacement" )
	GafferSceneUI.AttributeEditor.registerAttribute( "Arnold", "ai:autobump_visibility:specular_transmit", "Displacement" )
	GafferSceneUI.AttributeEditor.registerAttribute( "Arnold", "ai:autobump_visibility:volume", "Displacement" )
	GafferSceneUI.AttributeEditor.registerAttribute( "Arnold", "ai:autobump_visibility:subsurface", "Displacement" )

	GafferSceneUI.AttributeEditor.registerAttribute( "Arnold", "ai:transform_type", "Transform" )

	GafferSceneUI.AttributeEditor.registerAttribute( "Arnold", "ai:matte", "Shading" )
	GafferSceneUI.AttributeEditor.registerAttribute( "Arnold", "ai:opaque", "Shading" )
	GafferSceneUI.AttributeEditor.registerAttribute( "Arnold", "ai:receive_shadows", "Shading" )
	GafferSceneUI.AttributeEditor.registerAttribute( "Arnold", "ai:self_shadows", "Shading" )
	GafferSceneUI.AttributeEditor.registerAttribute( "Arnold", "ai:sss_setname", "Shading" )

	GafferSceneUI.AttributeEditor.registerAttribute( "Arnold", "ai:polymesh:subdiv_iterations", "Subdivision" )
	GafferSceneUI.AttributeEditor.registerAttribute( "Arnold", "ai:polymesh:subdiv_adaptive_error", "Subdivision" )
	GafferSceneUI.AttributeEditor.registerAttribute( "Arnold", "ai:polymesh:subdiv_adaptive_metric", "Subdivision" )
	GafferSceneUI.AttributeEditor.registerAttribute( "Arnold", "ai:polymesh:subdiv_adaptive_space", "Subdivision" )
	GafferSceneUI.AttributeEditor.registerAttribute( "Arnold", "ai:polymesh:subdiv_uv_smoothing", "Subdivision" )
	GafferSceneUI.AttributeEditor.registerAttribute( "Arnold", "ai:polymesh:subdiv_smooth_derivs", "Subdivision" )
	GafferSceneUI.AttributeEditor.registerAttribute( "Arnold", "ai:polymesh:subdiv_frustum_ignore", "Subdivision" )
	GafferSceneUI.AttributeEditor.registerAttribute( "Arnold", "ai:polymesh:subdivide_polygons", "Subdivision" )

	GafferSceneUI.AttributeEditor.registerAttribute( "Arnold", "ai:curves:mode", "Curves" )
	GafferSceneUI.AttributeEditor.registerAttribute( "Arnold", "ai:curves:min_pixel_width", "Curves" )

	GafferSceneUI.AttributeEditor.registerAttribute( "Arnold", "ai:points:min_pixel_width", "Points" )

	GafferSceneUI.AttributeEditor.registerAttribute( "Arnold", "ai:volume:step_size", "Volume" )
	GafferSceneUI.AttributeEditor.registerAttribute( "Arnold", "ai:volume:step_scale", "Volume" )
	GafferSceneUI.AttributeEditor.registerAttribute( "Arnold", "ai:shape:step_size", "Volume" )
	GafferSceneUI.AttributeEditor.registerAttribute( "Arnold", "ai:shape:step_scale", "Volume" )
	GafferSceneUI.AttributeEditor.registerAttribute( "Arnold", "ai:shape:volume_padding", "Volume" )
	GafferSceneUI.AttributeEditor.registerAttribute( "Arnold", "ai:volume:velocity_scale", "Volume" )
	GafferSceneUI.AttributeEditor.registerAttribute( "Arnold", "ai:volume:velocity_fps", "Volume" )
	GafferSceneUI.AttributeEditor.registerAttribute( "Arnold", "ai:volume:velocity_outlier_threshold", "Volume" )

	GafferSceneUI.AttributeEditor.registerAttribute( "Arnold", "ai:toon_id", "Toon" )

if os.environ.get( "CYCLES_ROOT" ) and os.environ.get( "GAFFERCYCLES_HIDE_UI", "" ) != "1" :

	Gaffer.Metadata.registerValue( GafferSceneUI.AttributeEditor.Settings, "tabGroup", "preset:Cycles", "Cycles" )

	GafferSceneUI.AttributeEditor.registerAttribute( "Cycles", "cycles:visibility:camera", "Visibility" )
	GafferSceneUI.AttributeEditor.registerAttribute( "Cycles", "cycles:visibility:diffuse", "Visibility" )
	GafferSceneUI.AttributeEditor.registerAttribute( "Cycles", "cycles:visibility:glossy", "Visibility" )
	GafferSceneUI.AttributeEditor.registerAttribute( "Cycles", "cycles:visibility:transmission", "Visibility" )
	GafferSceneUI.AttributeEditor.registerAttribute( "Cycles", "cycles:visibility:shadow", "Visibility" )
	GafferSceneUI.AttributeEditor.registerAttribute( "Cycles", "cycles:visibility:scatter", "Visibility" )

	GafferSceneUI.AttributeEditor.registerAttribute( "Cycles", "cycles:use_holdout", "Rendering" )
	GafferSceneUI.AttributeEditor.registerAttribute( "Cycles", "cycles:is_shadow_catcher", "Rendering" )
	GafferSceneUI.AttributeEditor.registerAttribute( "Cycles", "cycles:shadow_terminator_shading_offset", "Rendering" )
	GafferSceneUI.AttributeEditor.registerAttribute( "Cycles", "cycles:shadow_terminator_geometry_offset", "Rendering" )
	GafferSceneUI.AttributeEditor.registerAttribute( "Cycles", "cycles:is_caustics_caster", "Rendering" )
	GafferSceneUI.AttributeEditor.registerAttribute( "Cycles", "cycles:is_caustics_receiver", "Rendering" )
	GafferSceneUI.AttributeEditor.registerAttribute( "Cycles", "cycles:lightgroup", "Rendering" )

	GafferSceneUI.AttributeEditor.registerAttribute( "Cycles", "cycles:max_level", "Subdivision" )
	GafferSceneUI.AttributeEditor.registerAttribute( "Cycles", "cycles:dicing_rate", "Subdivision" )

	GafferSceneUI.AttributeEditor.registerAttribute( "Cycles", "cycles:volume_clipping", "Volume" )
	GafferSceneUI.AttributeEditor.registerAttribute( "Cycles", "cycles:volume_step_size", "Volume" )
	GafferSceneUI.AttributeEditor.registerAttribute( "Cycles", "cycles:volume_object_space", "Volume" )

	GafferSceneUI.AttributeEditor.registerAttribute( "Cycles", "cycles:asset_name", "Object" )

	GafferSceneUI.AttributeEditor.registerAttribute( "Cycles", "cycles:shader:emission_sampling_method", "Shader" )
	GafferSceneUI.AttributeEditor.registerAttribute( "Cycles", "cycles:shader:use_transparent_shadow", "Shader" )
	GafferSceneUI.AttributeEditor.registerAttribute( "Cycles", "cycles:shader:heterogeneous_volume", "Shader" )
	GafferSceneUI.AttributeEditor.registerAttribute( "Cycles", "cycles:shader:volume_sampling_method", "Shader" )
	GafferSceneUI.AttributeEditor.registerAttribute( "Cycles", "cycles:shader:volume_interpolation_method", "Shader" )
	GafferSceneUI.AttributeEditor.registerAttribute( "Cycles", "cycles:shader:volume_step_rate", "Shader" )
	GafferSceneUI.AttributeEditor.registerAttribute( "Cycles", "cycles:shader:displacement_method", "Shader" )

with IECore.IgnoredExceptions( ImportError ) :

	# This import appears unused, but it is intentional; it prevents us from
	# registering when 3Delight isn't available.
	import GafferDelight

	Gaffer.Metadata.registerValue( GafferSceneUI.AttributeEditor.Settings, "tabGroup", "preset:3Delight", "3Delight" )

	GafferSceneUI.AttributeEditor.registerAttribute( "3Delight", "dl:visibility.camera", "Visibility" )
	GafferSceneUI.AttributeEditor.registerAttribute( "3Delight", "dl:visibility.diffuse", "Visibility" )
	GafferSceneUI.AttributeEditor.registerAttribute( "3Delight", "dl:visibility.hair", "Visibility" )
	GafferSceneUI.AttributeEditor.registerAttribute( "3Delight", "dl:visibility.reflection", "Visibility" )
	GafferSceneUI.AttributeEditor.registerAttribute( "3Delight", "dl:visibility.refraction", "Visibility" )
	GafferSceneUI.AttributeEditor.registerAttribute( "3Delight", "dl:visibility.shadow", "Visibility" )
	GafferSceneUI.AttributeEditor.registerAttribute( "3Delight", "dl:visibility.specular", "Visibility" )

	GafferSceneUI.AttributeEditor.registerAttribute( "3Delight", "dl:matte", "Shading" )

if os.environ.get( "GAFFERRENDERMAN_HIDE_UI", "" ) != "1" :

	with IECore.IgnoredExceptions( ImportError ) :

		# This import appears unused, but it is intentional; it prevents us from
		# registering when RenderMan isn't available.
		import GafferRenderMan

		Gaffer.Metadata.registerValue( GafferSceneUI.AttributeEditor.Settings, "tabGroup", "preset:RenderMan", "RenderMan" )

		# Register all options we have metadata for.
		## \todo We should probably do things this way for the other renderers too. The
		# AttributeEditor could just read the metadata itself then, and we wouldn't
		# need `registerAttribute()` at all.
		for target in Gaffer.Metadata.targetsWithMetadata( "attribute:ri:*", "defaultValue" ) :
			GafferSceneUI.AttributeEditor.registerAttribute(
				"RenderMan", target[10:], Gaffer.Metadata.value( target, "layout:section" ), Gaffer.Metadata.value( target, "label" )
			)

Gaffer.Metadata.registerValue( GafferSceneUI.AttributeEditor.Settings, "tabGroup", "preset:OpenGL", "OpenGL" )

GafferSceneUI.AttributeEditor.registerAttribute( "OpenGL", "gl:primitive:solid", "Shading" )
GafferSceneUI.AttributeEditor.registerAttribute( "OpenGL", "gl:primitive:wireframe", "Shading" )
GafferSceneUI.AttributeEditor.registerAttribute( "OpenGL", "gl:primitive:wireframeColor", "Shading" )
GafferSceneUI.AttributeEditor.registerAttribute( "OpenGL", "gl:primitive:wireframeWidth", "Shading" )
GafferSceneUI.AttributeEditor.registerAttribute( "OpenGL", "gl:primitive:outline", "Shading" )
GafferSceneUI.AttributeEditor.registerAttribute( "OpenGL", "gl:primitive:outlineColor", "Shading" )
GafferSceneUI.AttributeEditor.registerAttribute( "OpenGL", "gl:primitive:outlineWidth", "Shading" )
GafferSceneUI.AttributeEditor.registerAttribute( "OpenGL", "gl:primitive:points", "Shading" )
GafferSceneUI.AttributeEditor.registerAttribute( "OpenGL", "gl:primitive:pointColor", "Shading" )
GafferSceneUI.AttributeEditor.registerAttribute( "OpenGL", "gl:primitive:pointWidth", "Shading" )
GafferSceneUI.AttributeEditor.registerAttribute( "OpenGL", "gl:primitive:bound", "Shading" )
GafferSceneUI.AttributeEditor.registerAttribute( "OpenGL", "gl:primitive:boundColor", "Shading" )

GafferSceneUI.AttributeEditor.registerAttribute( "OpenGL", "gl:pointsPrimitive:useGLPoints", "Points" )
GafferSceneUI.AttributeEditor.registerAttribute( "OpenGL", "gl:pointsPrimitive:glPointWidth", "Points" )

GafferSceneUI.AttributeEditor.registerAttribute( "OpenGL", "gl:curvesPrimitive:useGLLines", "Curves" )
GafferSceneUI.AttributeEditor.registerAttribute( "OpenGL", "gl:curvesPrimitive:glLineWidth", "Curves" )
GafferSceneUI.AttributeEditor.registerAttribute( "OpenGL", "gl:curvesPrimitive:ignoreBasis", "Curves" )

GafferSceneUI.AttributeEditor.registerAttribute( "OpenGL", "gl:visualiser:scale", "Visualisers" )
GafferSceneUI.AttributeEditor.registerAttribute( "OpenGL", "gl:visualiser:maxTextureResolution", "Visualisers" )
GafferSceneUI.AttributeEditor.registerAttribute( "OpenGL", "gl:visualiser:frustum", "Visualisers" )
GafferSceneUI.AttributeEditor.registerAttribute( "OpenGL", "gl:light:frustumScale", "Visualisers" )
GafferSceneUI.AttributeEditor.registerAttribute( "OpenGL", "gl:light:drawingMode", "Visualisers" )
