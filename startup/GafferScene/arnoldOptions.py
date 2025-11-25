##########################################################################
#
#  Copyright (c) 2023, Cinesite VFX Ltd. All rights reserved.
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

import imath

import IECore

import Gaffer

# Build a dictionary of log and console options to be included in the registration below.
__loggingOptions = {}
for optionPrefix in ( "log", "console" ) :

	for suffix, label, description, consoleDefault in (
		( "info", "Info", "information messages", False ),
		( "warnings", "Warnings", "warning messages", True ),
		( "errors", "Errors", "error messages", True ),
		( "debug", "Debug", "debug messages", False ),
		( "ass_parse", "AssParse", "ass parsing", False ),
		( "plugins", "Plugins", "plugin loading", False ),
		( "progress", "Progress", "progress messages", False ),
		( "nan", "NAN", "pixels with NaNs", False ),
		( "timestamp", "Timestamp", "timestamp prefixes", True ),
		( "stats", "Stats", "statistics", False ),
		( "backtrace", "Backtrace", "stack backtraces from crashes", True ),
		( "memory", "Memory", "memory usage prefixes", True ),
		( "color", "Color", "coloured messages", True ),
	) :

		__loggingOptions[f"option:ai:{optionPrefix}:{suffix}"] = {

			"defaultValue" : consoleDefault if optionPrefix == "console" else True,
			"description" :
			"""
			Whether or not {0} {1} included in the {2} output.
			""".format( description, "are" if description.endswith( "s" ) else "is", optionPrefix ),
			"label" : label,
			"layout:section" : "Logging." + ( "Console " if optionPrefix == "console" else "" ) + "Verbosity",

		}

Gaffer.Metadata.registerValues( {

	# Rendering

	"option:ai:bucket_size" : {

		"defaultValue" : 64,
		"description" :
		"""
		Controls the size of the image buckets.
		The default size is 64x64 pixels.
		Bigger buckets will increase memory usage
		while smaller buckets may render slower as
		they need to perform redundant computations
		and filtering.
		""",
		"label" : "Bucket Size",
		"layout:section" : "Rendering",

	},

	"option:ai:bucket_scanning" : {

		"defaultValue" : "spiral",
		"description" :
		"""
		Controls the order in which buckets are
		processed. A spiral pattern is the default.
		""",
		"label" : "Bucket Scanning",
		"layout:section" : "Rendering",

		"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",
		"presetNames" : IECore.StringVectorData( ["Top", "Left", "Random", "Spiral", "Hilbert"] ),
		"presetValues" : IECore.StringVectorData( ["top", "left", "random", "spiral", "hilbert"] ),

	},

	"option:ai:parallel_node_init" : {

		"defaultValue" : True,
		"description" :
		"""
		Enables Arnold's parallel node initialization.
		Note that some Arnold features may not be
		thread-safe, in which case enabling this option
		can cause crashes. One such example is Cryptomatte
		and its use in the AlSurface shader.
		""",
		"label" : "Parallel Node Init",
		"layout:section" : "Rendering",

	},

	"option:ai:threads" : {

		"defaultValue" : 0,
		"description" :
		"""
		Specifies the number of threads Arnold
		is allowed to use. A value of 0 gives
		Arnold access to all available threads.
		""",
		"label" : "Threads",
		"layout:section" : "Rendering",

	},

	# Sampling

	"option:ai:AA_samples" : {

		"defaultValue" : 3,
		"description" :
		"""
		Controls the number of rays per pixel
		traced from the camera. The more samples,
		the better the quality of antialiasing,
		motion blur and depth of field. The actual
		number of rays per pixel is the square of
		the AA Samples value - so a value of 3
		means 9 rays are traced, 4 means 16 rays are
		traced and so on.
		""",
		"label" : "AA Samples",
		"layout:section" : "Sampling",

	},

	"option:ai:GI_diffuse_samples" : {

		"defaultValue" : 2,
		"description" :
		"""
		Controls the number of rays traced when
		computing indirect illumination ("bounce light").
		The number of actual diffuse rays traced is the
		square of this number.
		""",
		"label" : "Diffuse Samples",
		"columnLayout:label" : "Diffuse",
		"layout:section" : "Sampling",

	},

	"option:ai:GI_specular_samples" : {

		"defaultValue" : 2,
		"description" :
		"""
		Controls the number of rays traced when
		computing specular reflections. The number of actual
		specular rays traced is the square of this number.
		""",
		"label" : "Specular Samples",
		"columnLayout:label" : "Specular",
		"layout:section" : "Sampling",

	},

	"option:ai:GI_transmission_samples" : {

		"defaultValue" : 2,
		"description" :
		"""
		Controls the number of rays traced when
		computing specular refractions. The number of actual
		transmitted specular rays traced is the square of this number.
		""",
		"label" : "Transmission Samples",
		"columnLayout:label" : "Transmission",
		"layout:section" : "Sampling",

	},

	"option:ai:GI_sss_samples" : {

		"defaultValue" : 2,
		"description" :
		"""
		Controls the number of rays traced when
		computing subsurface scattering. The number of actual
		subsurface rays traced is the square of this number.
		""",
		"label" : "SSS Samples",
		"columnLayout:label" : "SSS",
		"layout:section" : "Sampling",

	},

	"option:ai:GI_volume_samples" : {

		"defaultValue" : 2,
		"description" :
		"""
		Controls the number of rays traced when
		computing indirect lighting for volumes.
		The number of actual rays traced
		is the square of this number. The volume
		ray depth must be increased from the default
		value of 0 before this setting is of use.
		""",
		"label" : "Volume Samples",
		"columnLayout:label" : "Volume",
		"layout:section" : "Sampling",

	},

	"option:ai:light_samples" : {

		"defaultValue" : 0,
		"description" :
		"""
		Specifies a fixed number of light samples to be taken at each
		shading point. This enables "Global Light Sampling", which provides
		significantly improved performance for scenes containing large numbers
		of lights. In this mode, the `samples` setting on each light is ignored,
		and instead the fixed number of samples is distributed among all the
		lights according to their contribution at the shading point.

		A value of `0` disables Global Light Sampling, reverting to the original
		per-light sampling algorithm.

		> Note : Global Light Sampling currently has limitations. See
		> https://help.autodesk.com/view/ARNOL/ENU/?guid=arnold_user_guide_ac_render_settings_ac_lights_settings_html
		> for more details.
		""",
		"label" : "Light Samples",
		"columnLayout:label" : "Light",
		"layout:section" : "Sampling",

	},

	"option:ai:AA_seed" : {

		"defaultValue" : 1,
		"description" :
		"""
		Seeds the randomness used when generating samples.
		By default this is set to the current frame number
		so that the pattern of sampling noise changes every
		frame. It can be locked to a particular value so
		that sampling noise does not change from frame to
		frame.
		""",
		"label" : "AA Seed",
		"layout:section" : "Sampling",

	},

	"option:ai:AA_sample_clamp" : {

		"defaultValue" : 10.0,
		"description" :
		"""
		Sets a maximum for the values of individual pixel samples. This
		can help reduce fireflies.
		""",
		"label" : "Sample Clamp",
		"layout:section" : "Sampling",

	},

	"option:ai:AA_sample_clamp_affects_aovs" : {

		"defaultValue" : False,
		"description" :
		"""
		Applies the sample clamping settings to all RGB and RGBA
		AOVs, in addition to the beauty image.
		""",
		"label" : "Clamp AOVs",
		"layout:section" : "Sampling",

	},

	"option:ai:indirect_sample_clamp" : {

		"defaultValue" : 10.0,
		"description" :
		"""
		Clamp fireflies resulting from indirect calculations.
		May cause problems with dulling highlights in reflections.
		""",
		"label" : "Indirect Sample Clamp",
		"layout:section" : "Sampling",

	},

	"option:ai:low_light_threshold" : {

		"defaultValue" : 0.001,
		"description" :
		"""
		Light paths with less energy than this will be discarded. This
		saves tracing shadow rays, but cuts off the light when it gets dim.
		Raising this improves performance, but makes the image potentially
		darker in some areas.
		""",
		"label" : "Low Light Threshold",
		"layout:section" : "Sampling",

	},

	# Adaptive Sampling

	"option:ai:enable_adaptive_sampling" : {

		"defaultValue" : False,
		"description" :
		"""
		If adaptive sampling is enabled, Arnold will
		take a minimum of (AA Samples * AA Samples)
		samples per pixel, and will then take up to
		(AA Samples Max * AA Samples Max) samples per
		pixel, or until the remaining estimated noise
		gets lower than the `ai:AA_adaptive_threshold` option.
		""",
		"label" : "Enable Adaptive Sampling",
		"columnLayout:label" : "Adaptive Sampling",
		"layout:section" : "Adaptive Sampling",

	},

	"option:ai:AA_samples_max" : {

		"defaultValue" : 0,
		"description" :
		"""
		The maximum sampling rate during adaptive
		sampling. Like `ai:AA_samples`, this value is
		squared. So `ai:AA_samples_max` == `6` means up to
		36 samples per pixel.
		""",
		"label" : "AA Samples Max",
		"layout:section" : "Adaptive Sampling",

	},

	"option:ai:AA_adaptive_threshold" : {

		"defaultValue" : 0.05,
		"description" :
		"""
		How much leftover noise is acceptable when
		terminating adaptive sampling. Higher values
		accept more noise, lower values keep rendering
		longer to achieve smaller amounts of noise.
		""",
		"label" : "AA Adaptive Threshold",
		"columnLayout:label" : "Adaptive Threshold",
		"layout:section" : "Adaptive Sampling",

	},

	# Interactive rendering

	"option:ai:enable_progressive_render" : {

		"defaultValue" : True,
		"description" :
		"""
		Enables progressive rendering, with a series of coarse low-resolution
		renders followed by a full quality render updated continuously.
		""",
		"label" : "Progressive",
		"layout:section" : "Interactive Rendering",

	},

	"option:ai:progressive_min_AA_samples" : {

		"defaultValue" : -4,
		"minValue" : -10,
		"maxValue" : 0,
		"description" :
		"""
		Controls the coarseness of the first low resolution pass
		of interactive rendering. A value of `-4` starts with 16x16 pixel
		blocks, `-3` gives 8x8 blocks, `-2` gives 4x4, `-1` gives 2x2 and
		`0` disables the low resolution passes completely.
		""",
		"label" : "Min AA Samples",
		"layout:section" : "Interactive Rendering",

	},

	# Ray Depth

	"option:ai:GI_total_depth" : {

		"defaultValue" : 10,
		"description" :
		"""
		The maximum depth of any ray (Diffuse + Specular +
		Transmission + Volume).
		""",
		"label" : "Total Depth",
		"columnLayout:label" : "Total",
		"layout:section" : "Ray Depth",

	},

	"option:ai:GI_diffuse_depth" : {

		"defaultValue" : 2,
		"description" :
		"""
		Controls the number of ray bounces when
		computing indirect illumination ("bounce light").
		""",
		"label" : "Diffuse Depth",
		"columnLayout:label" : "Diffuse",
		"layout:section" : "Ray Depth",

	},

	"option:ai:GI_specular_depth" : {

		"defaultValue" : 2,
		"description" :
		"""
		Controls the number of ray bounces when
		computing specular reflections.
		""",
		"label" : "Specular Depth",
		"columnLayout:label" : "Specular",
		"layout:section" : "Ray Depth",

	},

	"option:ai:GI_transmission_depth" : {

		"defaultValue" : 2,
		"description" :
		"""
		Controls the number of ray bounces when
		computing specular refractions.
		""",
		"label" : "Transmission Depth",
		"columnLayout:label" : "Transmission",
		"layout:section" : "Ray Depth",

	},

	"option:ai:GI_volume_depth" : {

		"defaultValue" : 0,
		"description" :
		"""
		Controls the number of ray bounces when
		computing indirect lighting on volumes.
		""",
		"label" : "Volume Depth",
		"columnLayout:label" : "Volume",
		"layout:section" : "Ray Depth",

	},

	"option:ai:auto_transparency_depth" : {

		"defaultValue" : 10,
		"description" :
		"""
		The number of allowable transparent layers - after
		this the last object will be treated as opaque.
		""",
		"label" : "Transparency Depth",
		"columnLayout:label" : "Transparency",
		"layout:section" : "Ray Depth",

	},

	# Subdivision

	"option:ai:max_subdivisions" : {

		"defaultValue" : 999,
		"description" :
		"""
		A global override for the maximum polymesh.subdiv_iterations.
		""",
		"layout:section" : "Subdivision",
		"label" : "Max Subdivisions",

	},

	"option:ai:subdiv_dicing_camera" : {

		"defaultValue" : "",
		"description" :
		"""
		If specified, adaptive subdivision will be performed
		relative to this camera, instead of the render camera.
		""",
		"layout:section" : "Subdivision",
		"label" : "Subdiv Dicing Camera",

		"plugValueWidget:type" : "GafferSceneUI.ScenePathPlugValueWidget",
		"path:valid" : True,
		"scenePathPlugValueWidget:setNames" : IECore.StringVectorData( [ "__cameras" ] ),
		"scenePathPlugValueWidget:setsLabel" : "Show only cameras",

	},

	"option:ai:subdiv_frustum_culling" : {

		"defaultValue" : False,
		"description" :
		"""
		Disable subdivision of polygons outside the camera frustum.
		(Uses dicing camera if one has been set).
		Saves performance, at the cost of inaccurate reflections
		and shadows.
		""",
		"label" : "Subdiv Frustum Culling",
		"layout:section" : "Subdivision",

	},

	"option:ai:subdiv_frustum_padding" : {

		"defaultValue" : 0.0,
		"description" :
		"""
		When using subdiv frustum culling, adds a world space bound
		around the frustum where subdivision still occurs. Can be
		used to improve shadows, reflections, and objects that motion
		blur into frame.
		""",
		"label" : "Subdiv Frustum Padding",
		"layout:section" : "Subdivision",

	},

	# Texturing

	"option:ai:texture_max_memory_MB" : {

		"defaultValue" : 4096.0,
		"description" :
		"""
		The maximum amount of memory to use for caching
		textures. Tiles are loaded on demand and cached,
		and when the memory limit is reached the least
		recently used tiles are discarded to make room
		for more. Measured in megabytes.
		""",
		"label" : "Max Memory MB",
		"layout:section" : "Texturing",

	},

	"option:ai:texture_per_file_stats" : {

		"defaultValue" : False,
		"description" :
		"""
		Turns on detailed statistics output for
		each individual texture file used.
		""",
		"label" : "Per File Stats",
		"layout:section" : "Texturing",

	},

	"option:ai:texture_max_sharpen" : {

		"defaultValue" : 1.5,
		"description" :
		"""
		Controls the sharpness of texture lookups,
		providing a tradeoff between sharpness and
		the amount of texture data loaded. If
		textures appear too blurry, then the value
		should be increased to add sharpness.

		The theoretical optimum value is to match the
		number of AA samples, but in practice the
		improvement in sharpness this brings often
		doesn't justify the increased render time and
		memory usage.
		""",
		"label" : "Max Sharpen",
		"layout:section" : "Texturing",

	},

	"option:ai:texture_use_existing_tx" : {

		"defaultValue" : True,
		"description" :
		"""
		Automatically uses a `<filename>.tx` file if it exists, in
		preference to a `<filename>.jpg` (or any other file format) that has
		been specified. Particularly useful when used with the
		`ai:texture_auto_generate_tx` option, which will automatically create the `.tx`
		file as necessary.

		> Info : The `.tx` file format provides improved performance and
		reduced memory usage, because it contains mip-mapped textures.
		""",
		"label" : "Use Existing `.tx`",
		"layout:section" : "Texturing",

	},

	"option:ai:texture_auto_generate_tx" : {

		"defaultValue" : False,
		"description" :
		"""
		Automatically generates a `<filename>.tx` when given
		`<filename>.jpg` (or any other file format). Requires that
		`ai:texture_use_existing_tx` is also turned on. By default, textures
		are generated in the same folder as the source texture. Use the
		`ai:texture_auto_tx_path` option to specify an alternative destination.

		> Caution : This feature might cause problems if multiple render
		farm nodes are trying to convert the same textures in the same
		target folder at the same time, resulting in potential crashes,
		corrupt textures, and poor performance.
		""",
		"label" : "Auto Generate `.tx`",
		"layout:section" : "Texturing",

	},

	"option:ai:texture_auto_tx_path" : {

		"defaultValue" : "",
		"description" :
		"""
		Specifies an alternate destination folder for textures generated
		when the `ai:texture_auto_generate_tx` option is enabled.
		""",
		"label" : "Auto `.tx` Path",
		"layout:section" : "Texturing",

		"plugValueWidget:type" : "GafferUI.FileSystemPathPlugValueWidget",

	},

	# Features

	"option:ai:ignore_textures" : {

		"defaultValue" : False,
		"description" :
		"""
		Ignores all file textures, rendering as
		if they were all white.
		""",
		"label" : "Ignore Textures",
		"layout:section" : "Features",

	},

	"option:ai:ignore_shaders" : {

		"defaultValue" : False,
		"description" :
		"""
		Ignores all shaders, rendering as a
		simple facing ratio shader instead.
		""",
		"label" : "Ignore Shaders",
		"layout:section" : "Features",

	},

	"option:ai:ignore_atmosphere" : {

		"defaultValue" : False,
		"description" :
		"""
		Ignores all atmosphere shaders.
		""",
		"label" : "Ignore Atmosphere",
		"layout:section" : "Features",

	},

	"option:ai:ignore_lights" : {

		"defaultValue" : False,
		"description" :
		"""
		Ignores all lights.
		""",
		"label" : "Ignore Lights",
		"layout:section" : "Features",

	},

	"option:ai:ignore_shadows" : {

		"defaultValue" : False,
		"description" :
		"""
		Skips all shadow calculations.
		""",
		"label" : "Ignore Shadows",
		"layout:section" : "Features",

	},

	"option:ai:ignore_subdivision" : {

		"defaultValue" : False,
		"description" :
		"""
		Treats all subdivision surfaces
		as simple polygon meshes instead.
		""",
		"label" : "Ignore Subdivision",
		"layout:section" : "Features",

	},

	"option:ai:ignore_displacement" : {

		"defaultValue" : False,
		"description" :
		"""
		Ignores all displacement shaders.
		""",
		"label" : "Ignore Displacement",
		"layout:section" : "Features",

	},

	"option:ai:ignore_bump" : {

		"defaultValue" : False,
		"description" :
		"""
		Ignores all bump mapping.
		""",
		"label" : "Ignore Bump",
		"layout:section" : "Features",

	},

	"option:ai:ignore_sss" : {

		"defaultValue" : False,
		"description" :
		"""
		Disables all subsurface scattering.
		""",
		"label" : "Ignore SSS",
		"layout:section" : "Features",

	},

	"option:ai:ignore_imagers" : {

		"defaultValue" : False,
		"description" :
		"""
		Disables all imagers.
		""",
		"label" : "Ignore Imagers",
		"layout:section" : "Features",

	},

	# Search Paths

	"option:ai:texture_searchpath" : {

		"defaultValue" : "",
		"description" :
		"""
		The locations used to search for texture
		files.
		""",
		"label" : "Textures",
		"layout:section" : "Search Paths",

	},

	"option:ai:procedural_searchpath" : {

		"defaultValue" : "",
		"description" :
		"""
		The locations used to search for procedural
		DSOs.
		""",
		"label" : "Procedurals",
		"layout:section" : "Search Paths",

	},

	"option:ai:plugin_searchpath" : {

		"defaultValue" : "",
		"description" :
		"""
		The locations used to search for shaders and other plugins.
		""",
		"label" : "Plugins (Shaders)",
		"layout:section" : "Search Paths",

	},

	# Error Handling

	"option:ai:abort_on_error" : {

		"defaultValue" : True,
		"description" :
		"""
		Aborts the render if an error is encountered.
		""",
		"label" : "Abort On Error",
		"layout:section" : "Error Handling"

	},

	"option:ai:error_color_bad_texture" : {

		"defaultValue" : imath.Color3f( 1, 0, 0 ),
		"description" :
		"""
		The colour to display if an attempt is
		made to use a bad or non-existent texture.
		""",
		"label" : "Bad Texture",
		"layout:section" : "Error Handling",

	},

	"option:ai:error_color_bad_pixel" : {

		"defaultValue" : imath.Color3f( 0, 0, 1 ),
		"description" :
		"""
		The colour to display for a pixel where
		a NaN is encountered.
		""",
		"label" : "Bad Pixel",
		"layout:section" : "Error Handling",

	},

	"option:ai:error_color_bad_shader" : {

		"defaultValue" : imath.Color3f( 1, 0, 1 ),
		"description" :
		"""
		The colour to display if a problem occurs
		in a shader.
		""",

		"layout:section" : "Error Handling",
		"label" : "Bad Shader",

	},

	# Logging

	"option:ai:log:filename" : {

		"defaultValue" : "",
		"description" :
		"""
		The name of a log file which Arnold will generate
		while rendering.
		""",
		"label" : "File Name",
		"layout:section" : "Logging",

		"plugValueWidget:type" : "GafferUI.FileSystemPathPlugValueWidget",
		"path:leaf" : True,
		"fileSystemPath:extensions" : "txt log",
		"fileSystemPath:extensionsLabel" : "Show only log files",

	},

	"option:ai:log:max_warnings" : {

		"defaultValue" : 100,
		"description" :
		"""
		The maximum number of warnings that will be reported.
		""",
		"label" : "Max Warnings",
		"layout:section" : "Logging",

	},

} | __loggingOptions | {

	# Statistics

	"option:ai:statisticsFileName" : {

		"defaultValue" : "",
		"description" :
		"""
		The name of a statistics file where Arnold will store structured
		JSON statistics.
		""",
		"label" : "Statistics File",
		"layout:section" : "Statistics",

	},

	"option:ai:profileFileName" : {

		"defaultValue" : "",
		"description" :
		"""
		The name of a profile json file where Arnold will store a
		detailed node performance graph. Use chrome://tracing to
		view the profile.
		""",
		"label" : "Profile File",
		"layout:section" : "Statistics",

	},

	"option:ai:reportFileName" : {

		"defaultValue" : "",
		"description" :
		"""
		The name of a an HTML file where Arnold will store a
		detailed statistics report in an easily browsable form.
		""",
		"label" : "HTML Report File",
		"layout:section" : "Statistics",

	},

	# Licensing

	"option:ai:abort_on_license_fail" : {

		"defaultValue" : False,
		"description" :
		"""
		Aborts the render if a license is not available,
		instead of rendering with a watermark.
		""",
		"label" : "Abort On License Fail",
		"layout:section" : "Licensing",

	},

	"option:ai:skip_license_check" : {

		"defaultValue" : False,
		"description" :
		"""
		Skips the check for a license, always rendering
		with a watermark.
		""",
		"label" : "Skip License Check",
		"layout:section" : "Licensing",

	},

	# GPU

	"option:ai:render_device" : {

		"defaultValue" : "CPU",
		"description" :
		"""
		Can be used to put Arnold in GPU rendering mode, using your graphics card instead of CPU.

		> Note : GPU rendering supports a limited subset of Arnold features, see
		> https://help.autodesk.com/view/ARNOL/ENU/?guid=arnold_user_guide_ac_arnold_gpu_ac_features_limitations_html
		> for more details.
		""",
		"label" : "Render Device",
		"layout:section" : "GPU",

		"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",
		"presetNames" : IECore.StringVectorData( [ "CPU", "GPU" ] ),
		"presetValues" : IECore.StringVectorData( [ "CPU", "GPU" ] ),

	},

	"option:ai:gpu_max_texture_resolution" : {

		"defaultValue" : 0,
		"description" :
		"""
		If non-zero, this will omit the high resolution mipmaps when in GPU mode, to avoid running out of GPU memory.
		""",

		"layout:section" : "GPU",
		"label" : "Max Texture Resolution",

	},

} )

Gaffer.Metadata.registerValue( "option:ai:*", "category", "Arnold" )
