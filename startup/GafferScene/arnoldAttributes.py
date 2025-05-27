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

Gaffer.Metadata.registerValues( {

	"attribute:ai:visibility:camera" : [

		"defaultValue", True,
		"description",
		"""
		Whether or not the object is visible to camera
		rays. To hide an object completely, use the
		`scene:visible` attribute instead.
		""",
		"label", "Camera",
		"layout:section", "Visibility",

	],

	"attribute:ai:visibility:shadow" : [

		"defaultValue", True,
		"description",
		"""
		Whether or not the object is visible to shadow
		rays (whether or not it casts shadows).
		""",
		"label", "Shadow",
		"layout:section", "Visibility",

	],

	"attribute:ai:visibility:shadow_group" : [

		"defaultValue", "",
		"description",
		"""
		The lights that cause this object to cast shadows.

		> Caution : This attribute has been superceded and will be removed. Use
		> the standard `shadowedLights` attribute instead.
		""",
		"label", "Shadow Group",
		"layout:section", "Visibility",
		"ui:scene:acceptsSetExpression", True,

		"plugValueWidget:type", "GafferSceneUI.SetExpressionPlugValueWidget",

	],

	"attribute:ai:visibility:diffuse_reflect" : [

		"defaultValue", True,
		"description",
		"""
		Whether or not the object is visible in
		reflected diffuse ( ie. if it casts bounce light )
		""",
		"label", "Diffuse Reflection",
		"layout:section", "Visibility",

	],

	"attribute:ai:visibility:specular_reflect" : [

		"defaultValue", True,
		"description",
		"""
		Whether or not the object is visible in
		reflected specular ( ie. if it is visible in mirrors ).
		""",
		"label", "Specular Reflection",
		"layout:section", "Visibility",

	],

	"attribute:ai:visibility:diffuse_transmit" : [

		"defaultValue", True,
		"description",
		"""
		Whether or not the object is visible in
		transmitted diffuse ( ie. if it casts light through leaves ).
		""",
		"label", "Diffuse Transmission",
		"layout:section", "Visibility",

	],

	"attribute:ai:visibility:specular_transmit" : [

		"defaultValue", True,
		"description",
		"""
		Whether or not the object is visible in
		refracted specular ( ie. if it can be seen through glass ).
		""",
		"label", "Specular Transmission",
		"layout:section", "Visibility",

	],

	"attribute:ai:visibility:volume" : [

		"defaultValue", True,
		"description",
		"""
		Whether or not the object is visible in
		volume scattering.
		""",
		"label", "Volume",
		"layout:section", "Visibility",

	],

	"attribute:ai:visibility:subsurface" : [

		"defaultValue", True,
		"description",
		"""
		Whether or not the object is visible to subsurface
		rays.
		""",
		"label", "Subsurface",
		"layout:section", "Visibility",

	],

	"attribute:ai:disp_autobump" : [

		"defaultValue", False,
		"description",
		"""
		Automatically turns the details of the displacement map
		into bump, wherever the mesh is not subdivided enough
		to properly capture them.
		""",
		"label", "Autobump",
		"layout:section", "Displacement",

	],

	"attribute:ai:autobump_visibility:camera" : [

		"defaultValue", True,
		"description",
		"""
		Whether or not the autobump is visible to camera
		rays.
		""",
		"label", "Camera",
		"layout:section", "Displacement.Auto Bump Visibility",

	],

	"attribute:ai:autobump_visibility:shadow" : [

		"defaultValue", False,
		"description",
		"""
		Whether or not the autobump is visible to shadow
		rays.
		""",
		"label", "Shadow",
		"layout:section", "Displacement.Auto Bump Visibility",

	],

	"attribute:ai:autobump_visibility:diffuse_reflect" : [

		"defaultValue", False,
		"description",
		"""
		Whether or not the autobump is visible in
		reflected diffuse ( ie. if it casts bounce light )
		""",
		"label", "Diffuse Reflection",
		"layout:section", "Displacement.Auto Bump Visibility",

	],

	"attribute:ai:autobump_visibility:specular_reflect" : [

		"defaultValue", False,
		"description",
		"""
		Whether or not the autobump is visible in
		reflected specular ( ie. if it is visible in mirrors ).
		""",
		"label", "Specular Reflection",
		"layout:section", "Displacement.Auto Bump Visibility",

	],

	"attribute:ai:autobump_visibility:diffuse_transmit" : [

		"defaultValue", False,
		"description",
		"""
		Whether or not the autobump is visible in
		transmitted diffuse ( ie. if it casts light through leaves ).
		""",
		"label", "Diffuse Transmission",
		"layout:section", "Displacement.Auto Bump Visibility",

	],

	"attribute:ai:autobump_visibility:specular_transmit" : [

		"defaultValue", False,
		"description",
		"""
		Whether or not the autobump is visible in
		refracted specular ( ie. if it can be seen through glass ).
		""",
		"label", "Specular Transmission",
		"layout:section", "Displacement.Auto Bump Visibility",

	],

	"attribute:ai:autobump_visibility:volume" : [

		"defaultValue", False,
		"description",
		"""
		Whether or not the autobump is visible in
		volume scattering.
		""",
		"label", "Volume",
		"layout:section", "Displacement.Auto Bump Visibility",

	],

	"attribute:ai:autobump_visibility:subsurface" : [

		"defaultValue", False,
		"description",
		"""
		Whether or not the autobump is visible to subsurface
		rays.
		""",
		"label", "Subsurface",
		"layout:section", "Displacement.Auto Bump Visibility",

	],

	"attribute:ai:transform_type" : [

		"defaultValue", "rotate_about_center",
		"description",
		"""
		Choose how transform motion is interpolated. "Linear"
		produces classic linear vertex motion, "RotateAboutOrigin"
		produces curved arcs centred on the object's origin, and
		"RotateAboutCenter", the default, produces curved arcs
		centred on the object's bounding box middle.
		""",
		"label", "Transform Type",
		"layout:section", "Transform",

		"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
		"presetNames", IECore.StringVectorData( [ "Linear", "RotateAboutOrigin", "RotateAboutCenter" ] ),
		"presetValues", IECore.StringVectorData( [ "linear", "rotate_about_origin", "rotate_about_center" ] ),

	],

	"attribute:ai:matte" : [

		"defaultValue", False,
		"description",
		"""
		Turns the object into a holdout matte.
		This only affects primary (camera) rays.
		""",
		"label", "Matte",
		"layout:section", "Shading",

	],

	"attribute:ai:opaque" : [

		"defaultValue", True,
		"description",
		"""
		Flags the object as being opaque.
		""",
		"label", "Opaque",
		"layout:section", "Shading",

	],

	"attribute:ai:receive_shadows" : [

		"defaultValue", True,
		"description",
		"""
		Whether or not the object receives shadows.
		""",
		"label", "Receive Shadows",
		"layout:section", "Shading",

	],

	"attribute:ai:self_shadows" : [

		"defaultValue", True,
		"description",
		"""
		Whether or not the object casts shadows onto itself.
		""",
		"label", "Self Shadows",
		"layout:section", "Shading",

	],

	"attribute:ai:sss_setname" : [

		"defaultValue", "",
		"description",
		"""
		If given, subsurface will be blended across any other objects which share the same sss set name.
		""",
		"label", "SSS Set Name",
		"layout:section", "Shading",

	],

	"attribute:ai:polymesh:subdiv_iterations" : [

		"defaultValue", 1,
		"minValue", 0,
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
		"label", "Iterations",
		"layout:section", "Subdivision",

	],

	"attribute:ai:polymesh:subdiv_adaptive_error" : [

		"defaultValue", 0.0,
		"minValue", 0.0,
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
		> Gaffer's automatic instancing unless `ai:polymesh:subdiv_adaptive_space`
		> is set to "object".
		""",
		"label", "Adaptive Error",
		"layout:section", "Subdivision",

	],

	"attribute:ai:polymesh:subdiv_adaptive_metric" : [

		"defaultValue", "auto",
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
		"label", "Adaptive Metric",
		"layout:section", "Subdivision",

		"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
		"presetNames", IECore.StringVectorData( [ "Auto", "Edge Length", "Flatness" ] ),
		"presetValues", IECore.StringVectorData( [ "auto", "edge_length", "flatness" ] ),

	],

	"attribute:ai:polymesh:subdiv_adaptive_space" : [

		"defaultValue", "raster",
		"description",
		"""
		The space in which the error is measured when
		performing adaptive subdivision. Raster space means
		that the subdivision adapts to size on screen,
		with `ai:polymesh:subdiv_adaptive_error` being
		specified in pixels.
		Object space means that the error is measured in
		object space units and will not be sensitive to
		size on screen.
		""",
		"label", "Adaptive Space",
		"layout:section", "Subdivision",

		"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
		"presetNames", IECore.StringVectorData( [ "Raster", "Object" ] ),
		"presetValues", IECore.StringVectorData( [ "raster", "object" ] ),

	],

	"attribute:ai:polymesh:subdiv_uv_smoothing" : [

		"defaultValue", "pin_corners",
		"description",
		"""
		Determines how UVs are subdivided.
		""",
		"label", "UV Smoothing",
		"layout:section", "Subdivision",

		"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
		"presetNames", IECore.StringVectorData( [ "Pin Corners", "Pin Borders", "Linear", "Smooth" ] ),
		"presetValues", IECore.StringVectorData( [ "pin_corners", "pin_borders", "linear", "smooth" ] ),

	],

	"attribute:ai:polymesh:subdiv_smooth_derivs" : [

		"defaultValue", False,
		"description",
		"""
		Computes smooth UV derivatives (dPdu and dPdv) per
		vertex. This can be needed to remove faceting
		from anisotropic specular and other shading effects
		that use the derivatives.
		""",
		"label", "Smooth Derivatives",
		"layout:section", "Subdivision",

	],

	"attribute:ai:polymesh:subdiv_frustum_ignore" : [

		"defaultValue", False,
		"description",
		"""
		Turns off subdivision culling on a per-object basis. This provides
		finer control on top of the global `ai:subdiv_frustum_culling` option
		provided by the ArnoldOptions node.
		""",
		"label", "Ignore Frustum",
		"layout:section", "Subdivision",

	],

	"attribute:ai:polymesh:subdivide_polygons" : [

		"defaultValue", False,
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
		"label", "Subdivide Polygons (Linear)",
		"layout:section", "Subdivision",

	],

	"attribute:ai:curves:mode" : [

		"defaultValue", "ribbon",
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
		"label", "Mode",
		"layout:section", "Curves",

		"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
		"presetNames", IECore.StringVectorData( [ "Ribbon", "Thick" ] ),
		"presetValues", IECore.StringVectorData( [ "ribbon", "thick" ] ),

	],

	"attribute:ai:curves:min_pixel_width" : [

		"defaultValue", 0.0,
		"minValue", 0.0,
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
		"label", "Min Pixel Width",
		"layout:section", "Curves",

	],

	"attribute:ai:points:min_pixel_width" : [

		"defaultValue", 0.0,
		"minValue", 0.0,
		"description",
		"""
		The minimum width of rendered points primitives, measured in pixels on the screen.
		When rendering very small points, a large number of AA samples are required to avoid
		aliasing. In these cases a minimum pixel width may be specified to artificially enlarge
		the points, meaning that fewer AA samples may be used. The additional size is
		compensated for automatically by lowering the opacity of the points.
		""",
		"label", "Min Pixel Width",
		"layout:section", "Points",

	],

	"attribute:ai:volume:step_size" : [

		"defaultValue", 0.0,
		"minValue", 0.0,
		"description",
		"""
		Override the step size taken when raymarching volumes.
		If this value is disabled or zero then value is calculated from the voxel size.
		""",
		"label", "Volume Step Size",
		"layout:section", "Volume",

	],

	"attribute:ai:volume:step_scale" : [

		"defaultValue", 1.0,
		"minValue", 0.0,
		"description",
		"""
		Raymarching step size is calculated using this value
		multiplied by the volume voxel size or `ai:volume:step_size` if set.
		""",
		"label", "Volume Step Scale",
		"layout:section", "Volume",

	],

	"attribute:ai:shape:step_size" : [

		"defaultValue", 0.0,
		"minValue", 0.0,
		"description",
		"""
		A non-zero value causes an object to be treated
		as a volume container, and a value of 0 causes
		an object to be treated as regular geometry.
		""",
		"label", "Shape Step Size",
		"layout:section", "Volume",

	],

	"attribute:ai:shape:step_scale" : [

		"defaultValue", 1.0,
		"minValue", 0.0,
		"description",
		"""
		Raymarching step size is calculated using this value
		multiplied by `ai:shape:step_size`.
		""",
		"label", "Shape Step Scale",
		"layout:section", "Volume",

	],

	"attribute:ai:shape:volume_padding" : [

		"defaultValue", 0.0,
		"minValue", 0.0,
		"description",
		"""
		Allows a volume to be displaced outside its bounds. When
		rendering a mesh as a volume, this enables displacement.
		""",
		"label", "Padding",
		"layout:section", "Volume",

	],

	"attribute:ai:volume:velocity_scale" : [

		"defaultValue", 1.0,
		"minValue", 0.0,
		"description",
		"""
		Scales the vector used in VDB motion blur computation.
		""",
		"label", "Velocity Scale",
		"layout:section", "Volume",

	],

	"attribute:ai:volume:velocity_fps" : [

		"defaultValue", 24.0,
		"minValue", 0.0,
		"description",
		"""
		Sets the frame rate used in VDB motion blur computation.
		""",
		"label", "Velocity FPS",
		"layout:section", "Volume",

	],

	"attribute:ai:volume:velocity_outlier_threshold" : [

		"defaultValue", 0.001,
		"minValue", 0.0,
		"description",
		"""
		Sets the outlier threshold used in VDB motion blur computation.

		When rendering physics simulations resulting velocities are
		potentially noisy and require some filtering for faster rendering.
		""",
		"label", "Velocity Outlier Threshold",
		"layout:section", "Volume",

	],

	"attribute:ai:toon_id" : [

		"defaultValue", "",
		"description",
		"""
		You can select in the toon shader to skip outlines between objects with the same toon id set.
		""",
		"label", "Toon ID",
		"layout:section", "Toon",

	],

} )
