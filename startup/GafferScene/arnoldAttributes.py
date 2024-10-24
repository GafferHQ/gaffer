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

import IECore

import Gaffer

Gaffer.Metadata.registerValue( "attribute:ai:visibility:camera", "label", "Camera" )
Gaffer.Metadata.registerValue( "attribute:ai:visibility:camera", "defaultValue", IECore.BoolData( True ) )
Gaffer.Metadata.registerValue(
	"attribute:ai:visibility:camera",
	"description",
	"""
	Whether or not the object is visible to camera
	rays. To hide an object completely, use the
	`scene:visible` attribute instead.
	""",
)

Gaffer.Metadata.registerValue( "attribute:ai:visibility:shadow", "label", "Shadow" )
Gaffer.Metadata.registerValue( "attribute:ai:visibility:shadow", "defaultValue", IECore.BoolData( True ) )
Gaffer.Metadata.registerValue(
	"attribute:ai:visibility:shadow",
	"description",
	"""
	Whether or not the object is visible to shadow
	rays (whether or not it casts shadows).
	""",
)

Gaffer.Metadata.registerValue( "attribute:ai:visibility:shadow_group", "label", "Shadow Group" )
Gaffer.Metadata.registerValue( "attribute:ai:visibility:shadow_group", "defaultValue", IECore.StringData( "" ) )
Gaffer.Metadata.registerValue(
	"attribute:ai:visibility:shadow_group",
	"description",
	"""
	The lights that cause this object to cast shadows.
	Accepts a set expression or a space separated list of
	lights. Use \"defaultLights\" to refer to all lights that
	contribute to illumination by default.
	""",
)

Gaffer.Metadata.registerValue( "attribute:ai:visibility:diffuse_reflect", "label", "Diffuse Reflection" )
Gaffer.Metadata.registerValue( "attribute:ai:visibility:diffuse_reflect", "defaultValue", IECore.BoolData( True ) )
Gaffer.Metadata.registerValue(
	"attribute:ai:visibility:diffuse_reflect",
	"description",
	"""
	Whether or not the object is visible in
	reflected diffuse ( ie. if it casts bounce light )
	""",
)

Gaffer.Metadata.registerValue( "attribute:ai:visibility:specular_reflect", "label", "Specular Reflection" )
Gaffer.Metadata.registerValue( "attribute:ai:visibility:specular_reflect", "defaultValue", IECore.BoolData( True ) )
Gaffer.Metadata.registerValue(
	"attribute:ai:visibility:specular_reflect",
	"description",
	"""
	Whether or not the object is visible in
	reflected specular ( ie. if it is visible in mirrors ).
	""",
)

Gaffer.Metadata.registerValue( "attribute:ai:visibility:diffuse_transmit", "label", "Diffuse Transmission" )
Gaffer.Metadata.registerValue( "attribute:ai:visibility:diffuse_transmit", "defaultValue", IECore.BoolData( True ) )
Gaffer.Metadata.registerValue(
	"attribute:ai:visibility:diffuse_transmit",
	"description",
	"""
	Whether or not the object is visible in
	transmitted diffuse ( ie. if it casts light through leaves ).
	""",
)

Gaffer.Metadata.registerValue( "attribute:ai:visibility:specular_transmit", "label", "Specular Transmission" )
Gaffer.Metadata.registerValue( "attribute:ai:visibility:specular_transmit", "defaultValue", IECore.BoolData( True ) )
Gaffer.Metadata.registerValue(
	"attribute:ai:visibility:specular_transmit",
	"description",
	"""
	Whether or not the object is visible in
	refracted specular ( ie. if it can be seen through glass ).
	""",
)

Gaffer.Metadata.registerValue( "attribute:ai:visibility:volume", "label", "Volume" )
Gaffer.Metadata.registerValue( "attribute:ai:visibility:volume", "defaultValue", IECore.BoolData( True ) )
Gaffer.Metadata.registerValue(
	"attribute:ai:visibility:volume",
	"description",
	"""
	Whether or not the object is visible in
	volume scattering.
	""",
)

Gaffer.Metadata.registerValue( "attribute:ai:visibility:subsurface", "label", "Subsurface" )
Gaffer.Metadata.registerValue( "attribute:ai:visibility:subsurface", "defaultValue", IECore.BoolData( True ) )
Gaffer.Metadata.registerValue(
	"attribute:ai:visibility:subsurface",
	"description",
	"""
	Whether or not the object is visible to subsurface
	rays.
	""",
)

Gaffer.Metadata.registerValue( "attribute:ai:disp_autobump", "label", "Autobump" )
Gaffer.Metadata.registerValue( "attribute:ai:disp_autobump", "defaultValue", IECore.BoolData( False ) )
Gaffer.Metadata.registerValue(
	"attribute:ai:disp_autobump",
	"description",
	"""
	Automatically turns the details of the displacement map
	into bump, wherever the mesh is not subdivided enough
	to properly capture them.
	""",
)

Gaffer.Metadata.registerValue( "attribute:ai:autobump_visibility:camera", "label", "Camera" )
Gaffer.Metadata.registerValue( "attribute:ai:autobump_visibility:camera", "defaultValue", IECore.BoolData( True ) )
Gaffer.Metadata.registerValue(
	"attribute:ai:autobump_visibility:camera",
	"description",
	"""
	Whether or not the autobump is visible to camera
	rays.
	""",
)

Gaffer.Metadata.registerValue( "attribute:ai:autobump_visibility:shadow", "label", "Shadow" )
Gaffer.Metadata.registerValue( "attribute:ai:autobump_visibility:shadow", "defaultValue", IECore.BoolData( False ) )
Gaffer.Metadata.registerValue(
	"attribute:ai:autobump_visibility:shadow",
	"description",
	"""
	Whether or not the autobump is visible to shadow
	rays.
	""",
)

Gaffer.Metadata.registerValue( "attribute:ai:autobump_visibility:diffuse_reflect", "label", "Diffuse Reflection" )
Gaffer.Metadata.registerValue( "attribute:ai:autobump_visibility:diffuse_reflect", "defaultValue", IECore.BoolData( False ) )
Gaffer.Metadata.registerValue(
	"attribute:ai:autobump_visibility:diffuse_reflect",
	"description",
	"""
	Whether or not the autobump is visible in
	reflected diffuse ( ie. if it casts bounce light )
	""",
)

Gaffer.Metadata.registerValue( "attribute:ai:autobump_visibility:specular_reflect", "label", "Specular Reflection" )
Gaffer.Metadata.registerValue( "attribute:ai:autobump_visibility:specular_reflect", "defaultValue", IECore.BoolData( False ) )
Gaffer.Metadata.registerValue(
	"attribute:ai:autobump_visibility:specular_reflect",
	"description",
	"""
	Whether or not the autobump is visible in
	reflected specular ( ie. if it is visible in mirrors ).
	""",
)

Gaffer.Metadata.registerValue( "attribute:ai:autobump_visibility:diffuse_transmit", "label", "Diffuse Transmission" )
Gaffer.Metadata.registerValue( "attribute:ai:autobump_visibility:diffuse_transmit", "defaultValue", IECore.BoolData( False ) )
Gaffer.Metadata.registerValue(
	"attribute:ai:autobump_visibility:diffuse_transmit",
	"description",
	"""
	Whether or not the autobump is visible in
	transmitted diffuse ( ie. if it casts light through leaves ).
	""",
)

Gaffer.Metadata.registerValue( "attribute:ai:autobump_visibility:specular_transmit", "label", "Specular Transmission" )
Gaffer.Metadata.registerValue( "attribute:ai:autobump_visibility:specular_transmit", "defaultValue", IECore.BoolData( False ) )
Gaffer.Metadata.registerValue(
	"attribute:ai:autobump_visibility:specular_transmit",
	"description",
	"""
	Whether or not the autobump is visible in
	refracted specular ( ie. if it can be seen through glass ).
	""",
)

Gaffer.Metadata.registerValue( "attribute:ai:autobump_visibility:volume", "label", "Volume" )
Gaffer.Metadata.registerValue( "attribute:ai:autobump_visibility:volume", "defaultValue", IECore.BoolData( False ) )
Gaffer.Metadata.registerValue(
	"attribute:ai:autobump_visibility:volume",
	"description",
	"""
	Whether or not the autobump is visible in
	volume scattering.
	""",
)

Gaffer.Metadata.registerValue( "attribute:ai:autobump_visibility:subsurface", "label", "Subsurface" )
Gaffer.Metadata.registerValue( "attribute:ai:autobump_visibility:subsurface", "defaultValue", IECore.BoolData( False ) )
Gaffer.Metadata.registerValue(
	"attribute:ai:autobump_visibility:subsurface",
	"description",
	"""
	Whether or not the autobump is visible to subsurface
	rays.
	""",
)

Gaffer.Metadata.registerValue( "attribute:ai:transform_type", "label", "Transform Type" )
Gaffer.Metadata.registerValue( "attribute:ai:transform_type", "defaultValue", IECore.StringData( "rotate_about_center" ) )
Gaffer.Metadata.registerValue(
	"attribute:ai:transform_type",
	"description",
	"""
	Choose how transform motion is interpolated. "Linear"
	produces classic linear vertex motion, "RotateAboutOrigin"
	produces curved arcs centred on the object's origin, and
	"RotateAboutCenter", the default, produces curved arcs
	centred on the object's bounding box middle.
	""",
)
Gaffer.Metadata.registerValue( "attribute:ai:transform_type", "plugValueWidget:type", "GafferUI.PresetsPlugValueWidget" )
Gaffer.Metadata.registerValue( "attribute:ai:transform_type", "presetNames", IECore.StringVectorData( [ "Linear", "RotateAboutOrigin", "RotateAboutCenter" ] ) )
Gaffer.Metadata.registerValue( "attribute:ai:transform_type", "presetValues", IECore.StringVectorData( [ "linear", "rotate_about_origin", "rotate_about_center" ] ) )

Gaffer.Metadata.registerValue( "attribute:ai:matte", "label", "Matte" )
Gaffer.Metadata.registerValue( "attribute:ai:matte", "defaultValue", IECore.BoolData( False ) )
Gaffer.Metadata.registerValue(
	"attribute:ai:matte",
	"description",
	"""
	Turns the object into a holdout matte.
	This only affects primary (camera) rays.
	""",
)

Gaffer.Metadata.registerValue( "attribute:ai:opaque", "label", "Opaque" )
Gaffer.Metadata.registerValue( "attribute:ai:opaque", "defaultValue", IECore.BoolData( True ) )
Gaffer.Metadata.registerValue(
	"attribute:ai:opaque",
	"description",
	"""
	Flags the object as being opaque.
	""",
)

Gaffer.Metadata.registerValue( "attribute:ai:receive_shadows", "label", "Receive Shadows" )
Gaffer.Metadata.registerValue( "attribute:ai:receive_shadows", "defaultValue", IECore.BoolData( True ) )
Gaffer.Metadata.registerValue(
	"attribute:ai:receive_shadows",
	"description",
	"""
	Whether or not the object receives shadows.
	""",
)

Gaffer.Metadata.registerValue( "attribute:ai:self_shadows", "label", "Self Shadows" )
Gaffer.Metadata.registerValue( "attribute:ai:self_shadows", "defaultValue", IECore.BoolData( True ) )
Gaffer.Metadata.registerValue(
	"attribute:ai:self_shadows",
	"description",
	"""
	Whether or not the object casts shadows onto itself.
	""",
)

Gaffer.Metadata.registerValue( "attribute:ai:sss_setname", "label", "SSS Set Name" )
Gaffer.Metadata.registerValue( "attribute:ai:sss_setname", "defaultValue", IECore.StringData( "" ) )
Gaffer.Metadata.registerValue(
	"attribute:ai:sss_setname",
	"description",
	"""
	If given, subsurface will be blended across any other objects which share the same sss set name.
	""",
)

Gaffer.Metadata.registerValue( "attribute:ai:polymesh:subdiv_iterations", "label", "Iterations" )
Gaffer.Metadata.registerValue( "attribute:ai:polymesh:subdiv_iterations", "defaultValue", IECore.IntData( 1 ) )
Gaffer.Metadata.registerValue(
	"attribute:ai:polymesh:subdiv_iterations",
	"description",
	"""
	The maximum number of subdivision
	steps to apply when rendering subdivision
	surface. To set an exact number of
	subdivisions, set the adaptive error to
	0 so that the maximum becomes the
	controlling factor.

	Use the MeshType node to ensure that a
	mesh is treated as a subdivision surface
	in the first place.
	""",
)

Gaffer.Metadata.registerValue( "attribute:ai:polymesh:subdiv_adaptive_error", "label", "Adaptive Error" )
Gaffer.Metadata.registerValue( "attribute:ai:polymesh:subdiv_adaptive_error", "defaultValue", IECore.FloatData( 0 ) )
Gaffer.Metadata.registerValue(
	"attribute:ai:polymesh:subdiv_adaptive_error",
	"description",
	"""
	The maximum allowable deviation from the true
	surface and the subdivided approximation. How
	the error is measured is determined by the
	metric below. Note also that the iterations
	value above provides a hard limit on the maximum
	number of subdivision steps, so if changing the
	error setting appears to have no effect,
	you may need to raise the maximum.

	> Note : Objects with a non-zero value will not take part in
	> Gaffer's automatic instancing unless subdivAdaptiveSpace is
	> set to "object".
	""",
)

Gaffer.Metadata.registerValue( "attribute:ai:polymesh:subdiv_adaptive_metric", "label", "Adaptive Metric" )
Gaffer.Metadata.registerValue( "attribute:ai:polymesh:subdiv_adaptive_metric", "defaultValue", IECore.StringData( "auto" ) )
Gaffer.Metadata.registerValue(
	"attribute:ai:polymesh:subdiv_adaptive_metric",
	"description",
	"""
	The metric used when performing adaptive
	subdivision as specified by the adaptive error.
	The flatness metric ensures that the subdivided
	surface doesn't deviate from the true surface
	by more than the error, and will tend to
	increase detail in areas of high curvature. The
	edge length metric ensures that the edge length
	of a polygon is never longer than the error,
	so will tend to subdivide evenly regardless of
	curvature - this can be useful when applying a
	displacement shader. The auto metric automatically
	uses the flatness metric when no displacement
	shader is applied, and the edge length metric when
	a displacement shader is applied.
	""",
)
Gaffer.Metadata.registerValue( "attribute:ai:polymesh:subdiv_adaptive_metric", "plugValueWidget:type", "GafferUI.PresetsPlugValueWidget" )
Gaffer.Metadata.registerValue( "attribute:ai:polymesh:subdiv_adaptive_metric", "presetNames", IECore.StringVectorData( [ "Auto", "Edge Length", "Flatness" ] ) )
Gaffer.Metadata.registerValue( "attribute:ai:polymesh:subdiv_adaptive_metric", "presetValues", IECore.StringVectorData( [ "auto", "edge_length", "flatness" ] ) )

Gaffer.Metadata.registerValue( "attribute:ai:polymesh:subdiv_adaptive_space", "label", "Adaptive Space" )
Gaffer.Metadata.registerValue( "attribute:ai:polymesh:subdiv_adaptive_space", "defaultValue", IECore.StringData( "raster" ) )
Gaffer.Metadata.registerValue(
	"attribute:ai:polymesh:subdiv_adaptive_space",
	"description",
	"""
	The space in which the error is measured when
	performing adaptive subdivision. Raster space means
	that the subdivision adapts to size on screen,
	with subdivAdaptiveError being specified in pixels.
	Object space means that the error is measured in
	object space units and will not be sensitive to
	size on screen.
	""",
)
Gaffer.Metadata.registerValue( "attribute:ai:polymesh:subdiv_adaptive_space", "plugValueWidget:type", "GafferUI.PresetsPlugValueWidget" )
Gaffer.Metadata.registerValue( "attribute:ai:polymesh:subdiv_adaptive_space", "presetNames", IECore.StringVectorData( [ "Raster", "Object" ] ) )
Gaffer.Metadata.registerValue( "attribute:ai:polymesh:subdiv_adaptive_space", "presetValues", IECore.StringVectorData( [ "raster", "object" ] ) )

Gaffer.Metadata.registerValue( "attribute:ai:polymesh:subdiv_uv_smoothing", "label", "UV Smoothing" )
Gaffer.Metadata.registerValue( "attribute:ai:polymesh:subdiv_uv_smoothing", "defaultValue", IECore.StringData( "pin_corners" ) )
Gaffer.Metadata.registerValue(
	"attribute:ai:polymesh:subdiv_uv_smoothing",
	"description",
	"""
	Determines how UVs are subdivided.
	""",
)
Gaffer.Metadata.registerValue( "attribute:ai:polymesh:subdiv_uv_smoothing", "plugValueWidget:type", "GafferUI.PresetsPlugValueWidget" )
Gaffer.Metadata.registerValue( "attribute:ai:polymesh:subdiv_uv_smoothing", "presetNames", IECore.StringVectorData( [ "Pin Corners", "Pin Borders", "Linear", "Smooth" ] ) )
Gaffer.Metadata.registerValue( "attribute:ai:polymesh:subdiv_uv_smoothing", "presetValues", IECore.StringVectorData( [ "pin_corners", "pin_borders", "linear", "smooth" ] ) )

Gaffer.Metadata.registerValue( "attribute:ai:polymesh:subdiv_smooth_derivs", "label", "Smooth Derivatives" )
Gaffer.Metadata.registerValue( "attribute:ai:polymesh:subdiv_smooth_derivs", "defaultValue", IECore.BoolData( False ) )
Gaffer.Metadata.registerValue(
	"attribute:ai:polymesh:subdiv_smooth_derivs",
	"description",
	"""
	Computes smooth UV derivatives (dPdu and dPdv) per
	vertex. This can be needed to remove faceting
	from anisotropic specular and other shading effects
	that use the derivatives.
	""",
)

Gaffer.Metadata.registerValue( "attribute:ai:polymesh:subdiv_frustum_ignore", "label", "Ignore Frustum" )
Gaffer.Metadata.registerValue( "attribute:ai:polymesh:subdiv_frustum_ignore", "defaultValue", IECore.BoolData( False ) )
Gaffer.Metadata.registerValue(
	"attribute:ai:polymesh:subdiv_frustum_ignore",
	"description",
	"""
	Turns off subdivision culling on a per-object basis. This provides
	finer control on top of the global `subdivFrustumCulling` setting
	provided by the ArnoldOptions node.
	""",
)

Gaffer.Metadata.registerValue( "attribute:ai:polymesh:subdivide_polygons", "label", "Subdivide Polygons (Linear)" )
Gaffer.Metadata.registerValue( "attribute:ai:polymesh:subdivide_polygons", "defaultValue", IECore.BoolData( False ) )
Gaffer.Metadata.registerValue(
	"attribute:ai:polymesh:subdivide_polygons",
	"description",
	"""
	Causes polygon meshes to be rendered with Arnold's
	subdiv_type parameter set to "linear" rather than
	"none". This can be used to increase detail when
	using polygons with displacement shaders and/or mesh
	lights.

	> Caution : This is not equivalent to converting a polygon
	> mesh into a subdivision surface. To render with Arnold's
	> subdiv_type set to "catclark", you must use the MeshType
	> node to convert polygon meshes into subdivision surfaces.
	""",
)

Gaffer.Metadata.registerValue( "attribute:ai:curves:mode", "label", "Mode" )
Gaffer.Metadata.registerValue( "attribute:ai:curves:mode", "defaultValue", IECore.StringData( "ribbon" ) )
Gaffer.Metadata.registerValue(
	"attribute:ai:curves:mode",
	"description",
	"""
	How the curves are rendered. Ribbon mode treats
	the curves as flat ribbons facing the camera, and is
	most suited for rendering of thin curves with a
	dedicated hair shader. Thick mode treats the curves
	as tubes, and is suited for use with a regular
	surface shader.

	> Note : To render using Arnold's "oriented" mode, set
	> mode to "ribbon" and add per-vertex normals to the
	> curves as a primitive variable named "N".
	""",
)
Gaffer.Metadata.registerValue( "attribute:ai:curves:mode", "plugValueWidget:type", "GafferUI.PresetsPlugValueWidget" )
Gaffer.Metadata.registerValue( "attribute:ai:curves:mode", "presetNames", IECore.StringVectorData( [ "Ribbon", "Thick" ] ) )
Gaffer.Metadata.registerValue( "attribute:ai:curves:mode", "presetValues", IECore.StringVectorData( [ "ribbon", "thick" ] ) )

Gaffer.Metadata.registerValue( "attribute:ai:curves:min_pixel_width", "label", "Min Pixel Width" )
Gaffer.Metadata.registerValue( "attribute:ai:curves:min_pixel_width", "defaultValue", IECore.FloatData( 0 ) )
Gaffer.Metadata.registerValue(
	"attribute:ai:curves:min_pixel_width",
	"description",
	"""
	The minimum thickness of the curves, measured
	in pixels on the screen. When rendering very thin curves, a
	large number of AA samples are required
	to avoid aliasing. In these cases a minimum pixel
	width may be specified to artificially thicken the curves,
	meaning that fewer AA samples may be used. The additional width is
	compensated for automatically by lowering the opacity
	of the curves.
	""",
)

Gaffer.Metadata.registerValue( "attribute:ai:points:min_pixel_width", "label", "Min Pixel Width" )
Gaffer.Metadata.registerValue( "attribute:ai:points:min_pixel_width", "defaultValue", IECore.FloatData( 0 ) )
Gaffer.Metadata.registerValue(
	"attribute:ai:points:min_pixel_width",
	"description",
	"""
	The minimum width of rendered points primitives, measured in pixels on the screen.
	When rendering very small points, a large number of AA samples are required to avoid
	aliasing. In these cases a minimum pixel width may be specified to artificially enlarge
	the points, meaning that fewer AA samples may be used. The additional size is
	compensated for automatically by lowering the opacity of the points.
	""",
)

Gaffer.Metadata.registerValue( "attribute:ai:volume:step_size", "label", "Step Size" )
Gaffer.Metadata.registerValue( "attribute:ai:volume:step_size", "defaultValue", IECore.FloatData( 0 ) )
Gaffer.Metadata.registerValue(
	"attribute:ai:volume:step_size",
	"description",
	"""
	Override the step size taken when raymarching volumes.
	If this value is disabled or zero then value is calculated from the voxel size.
	""",
)

Gaffer.Metadata.registerValue( "attribute:ai:volume:step_scale", "label", "Step Scale" )
Gaffer.Metadata.registerValue( "attribute:ai:volume:step_scale", "defaultValue", IECore.FloatData( 1 ) )
Gaffer.Metadata.registerValue(
	"attribute:ai:volume:step_scale",
	"description",
	"""
	Raymarching step size is calculated using this value
	multiplied by the volume voxel size or `ai:volume:step_size` if set.
	""",
)

Gaffer.Metadata.registerValue( "attribute:ai:shape:step_size", "label", "Shape Step Size" )
Gaffer.Metadata.registerValue( "attribute:ai:shape:step_size", "defaultValue", IECore.FloatData( 0 ) )
Gaffer.Metadata.registerValue(
	"attribute:ai:shape:step_size",
	"description",
	"""
	A non-zero value causes an object to be treated
	as a volume container, and a value of 0 causes
	an object to be treated as regular geometry.
	""",
)

Gaffer.Metadata.registerValue( "attribute:ai:shape:step_scale", "label", "Shape Step Scale" )
Gaffer.Metadata.registerValue( "attribute:ai:shape:step_scale", "defaultValue", IECore.FloatData( 1 ) )
Gaffer.Metadata.registerValue(
	"attribute:ai:shape:step_scale",
	"description",
	"""
	Raymarching step size is calculated using this value
	multiplied by `ai:shape:step_size`.
	""",
)

Gaffer.Metadata.registerValue( "attribute:ai:shape:volume_padding", "label", "Padding" )
Gaffer.Metadata.registerValue( "attribute:ai:shape:volume_padding", "defaultValue", IECore.FloatData( 0 ) )
Gaffer.Metadata.registerValue(
	"attribute:ai:shape:volume_padding",
	"description",
	"""
	Allows a volume to be displaced outside its bounds. When
	rendering a mesh as a volume, this enables displacement.
	""",
)

Gaffer.Metadata.registerValue( "attribute:ai:volume:velocity_scale", "label", "Velocity Scale" )
Gaffer.Metadata.registerValue( "attribute:ai:volume:velocity_scale", "defaultValue", IECore.FloatData( 1 ) )
Gaffer.Metadata.registerValue(
	"attribute:ai:volume:velocity_scale",
	"description",
	"""
	Scales the vector used in VDB motion blur computation.
	""",
)

Gaffer.Metadata.registerValue( "attribute:ai:volume:velocity_fps", "label", "Velocity FPS" )
Gaffer.Metadata.registerValue( "attribute:ai:volume:velocity_fps", "defaultValue", IECore.FloatData( 24 ) )
Gaffer.Metadata.registerValue(
	"attribute:ai:volume:velocity_scale",
	"description",
	"""
	Sets the frame rate used in VDB motion blur computation.
	""",
)

Gaffer.Metadata.registerValue( "attribute:ai:volume:velocity_outlier_threshold", "label", "Velocity Outlier Threshold" )
Gaffer.Metadata.registerValue( "attribute:ai:volume:velocity_outlier_threshold", "defaultValue", IECore.FloatData( 0.001 ) )
Gaffer.Metadata.registerValue(
	"attribute:ai:volume:velocity_outlier_threshold",
	"description",
	"""
	Sets the outlier threshold used in VDB motion blur computation.

	When rendering physics simulations resulting velocities are
	potentially noisy and require some filtering for faster rendering.
	""",
)

Gaffer.Metadata.registerValue( "attribute:ai:toon_id", "label", "Toon ID" )
Gaffer.Metadata.registerValue( "attribute:ai:toon_id", "defaultValue", IECore.StringData( "" ) )
Gaffer.Metadata.registerValue(
	"attribute:ai:toon_id",
	"description",
	"""
	You can select in the toon shader to skip outlines between objects with the same toon id set.
	""",
)
