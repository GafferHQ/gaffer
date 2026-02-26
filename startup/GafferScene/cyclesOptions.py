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

import IECore

import Gaffer

Gaffer.Metadata.registerValues( {

	"option:cycles:log_level" : {

		"defaultValue" : 0,
		"minValue" : 0,
		"maxValue" : 2,
		"description" :
		"""
		Internal Cycles debugging log-level.
		""",
		"label" : "Log Level",
		"layout:section" : "Log",

		"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",
		"presetNames" : IECore.StringVectorData( [ "Error", "Warning", "Info" ] ),
		"presetValues" : IECore.IntVectorData( [ 0, 1, 2 ] ),

	},

	"option:cycles:device" : {

		"defaultValue" : "CPU",
		"description" :
		"""
		Device(s) to use for rendering.
		To specify multiple devices, there's a few examples under presets.

		To render on CPU and the first CUDA device:

			CPU CUDA:00

		To render on the first and second OpenCL device:

			OPENCL:00 OPENCL:01

		To render on every OptiX device found:

			OPTIX:*

		To render on everything found (not recommended, 1 device may have multiple backends!)

			CPU CUDA:* OPTIX:* OPENCL:*
		""",
		"label" : "Device(s)",
		"layout:section" : "Session",

		"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",
		"presetsPlugValueWidget:allowCustom" : True,

	},

	"option:cycles:shadingsystem" : {

		"defaultValue" : "OSL",
		"description" :
		"""
		Shading system.

		- OSL : Use Open Shading Language (CPU rendering only).
		- SVM : Use Shader Virtual Machine.
		""",
		"label" : "Shading System",
		"layout:section" : "Session",

		"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",
		"presetNames" : IECore.StringVectorData( [ "OSL", "SVM" ] ),
		"presetValues" : IECore.StringVectorData( [ "OSL", "SVM" ] ),

	},

	"option:cycles:session:samples" : {

		"defaultValue" : 1024,
		"description" :
		"""
		Number of samples to render for each pixel.
		""",
		"label" : "Samples",
		"layout:section" : "Sampling",

	},

	"option:cycles:session:pixel_size" : {

		"defaultValue" : 1,
		"description" :
		"""
		Pixel Size.
		""",
		"label" : "Pixel Size",
		"layout:section" : "Session",

	},

	"option:cycles:session:threads" : {

		"defaultValue" : 0,
		"description" :
		"""
		The number of threads used for rendering.

		- The default value of 0 lets the renderer choose
			an optimal number of threads based on the available
			hardware.
		- Positive values directly set the number of threads.
		- Negative values can be used to reserve some cores
			while otherwise letting the renderer choose the
			optimal number of threads.
		""",
		"label" : "Threads",
		"layout:section" : "Session",

	},

	"option:cycles:session:time_limit" : {

		"defaultValue" : 0.0,
		"description" :
		"""
		Time-limit.
		""",
		"label" : "Time Limit",
		"layout:section" : "Session",

	},

	"option:cycles:session:use_profiling" : {

		"defaultValue" : False,
		"description" :
		"""
		Use Profiling.
		""",
		"label" : "Use Profiling",
		"layout:section" : "Session",

	},

	"option:cycles:session:use_auto_tile" : {

		"defaultValue" : True,
		"description" :
		"""
		Automatically render high resolution images in tiles to reduce memory usage, using the specified tile size. Tiles are cached to disk while rendering to save memory.
		""",
		"label" : "Use Auto Tile",
		"layout:section" : "Session",

	},

	"option:cycles:session:tile_size" : {

		"defaultValue" : 2048,
		"description" :
		"""
		Tile size for rendering.
		""",
		"label" : "Tile Size",
		"layout:section" : "Session",

	},

	"option:cycles:scene:bvh_layout" : {

		"defaultValue" : "embree",
		"description" :
		"""
		BVH Layout size. This corresponds with CPU architecture
		(the higher the faster, but might not be supported on old CPUs).
		""",
		"label" : "BVH Layout",
		"layout:section" : "Scene",

		"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",
		"presetNames" : IECore.StringVectorData( [ "BVH2", "EMBREE" ] ),
		"presetValues" : IECore.StringVectorData( [ "bvh2", "embree" ] ),

	},

	"option:cycles:scene:use_bvh_spatial_split" : {

		"defaultValue" : False,
		"description" :
		"""
		Use BVH spatial splits: longer builder time, faster render.
		""",
		"label" : "Use Spatial Splits",
		"layout:section" : "Scene",

	},

	"option:cycles:scene:use_bvh_unaligned_nodes" : {

		"defaultValue" : True,
		"description" :
		"""
		Use special type BVH optimized for hair (uses more ram but renders faster).
		""",
		"label" : "Use Hair BVH",
		"layout:section" : "Scene",

	},

	"option:cycles:scene:num_bvh_time_steps" : {

		"defaultValue" : 0,
		"description" :
		"""
		Split BVH primitives by this number of time steps to speed up render time in cost of memory.
		""",
		"label" : "BVH Time Steps",
		"layout:section" : "Scene",

	},

	"option:cycles:scene:hair_subdivisions" : {

		"defaultValue" : 3,
		"description" :
		"""
		Split BVH primitives by this number of time steps to speed up render time in cost of memory.
		""",
		"label" : "Hair Subdivisions",
		"layout:section" : "Scene",

	},

	"option:cycles:scene:hair_shape" : {

		"defaultValue" : "ribbon",
		"description" :
		"""
		Round Ribbons - Render curves as flat ribbon with rounded normals, for fast rendering.
		3D Curves - Render curves as cylindrical 3D geometry, for accurate results when viewing hair close up.
		Linear 3D Curves - Render curves as cylindrical 3D geometry with linear interpolation.
		""",
		"label" : "Hair Shape",
		"layout:section" : "Scene",

		"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",
		"presetNames" : IECore.StringVectorData( [ "Round Ribbons", "3D Curves", "Linear 3D Curves" ] ),
		"presetValues" : IECore.StringVectorData( [ "ribbon", "thick", "thick-linear" ] ),

	},

	"option:cycles:scene:texture_limit" : {

		"defaultValue" : 0,
		"description" :
		"""
		Limit the maximum texture size used by final rendering.
		""",
		"label" : "Texture Size Limit",
		"layout:section" : "Scene",

		"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",
		"presetNames" : IECore.StringVectorData( [ "No Limit", "128", "256", "512", "1024", "2048", "4096", "8192" ] ),
		"presetValues" : IECore.IntVectorData( [ 0, 1, 2, 3, 4, 5, 6, 7 ] ),

	},

	"option:cycles:integrator:min_bounce" : {

		"defaultValue" : 0,
		"description" :
		"""
		Minimum number of light bounces. Setting this higher reduces noise in the first bounces,
		but can also be less efficient for more complex geometry like hair and volumes.
		""",
		"label" : "Min Bounces",
		"layout:section" : "Ray Depth",

	},

	"option:cycles:integrator:max_bounce" : {

		"defaultValue" : 7,
		"description" :
		"""
		Total maximum number of bounces.
		""",
		"label" : "Max Bounces",
		"layout:section" : "Ray Depth",

	},

	"option:cycles:integrator:max_diffuse_bounce" : {

		"defaultValue" : 7,
		"description" :
		"""
		Maximum number of diffuse reflection bounces, bounded by total maximum.
		""",
		"label" : "Diffuse",
		"layout:section" : "Ray Depth",

	},

	"option:cycles:integrator:max_glossy_bounce" : {

		"defaultValue" : 7,
		"description" :
		"""
		Maximum number of glossy reflection bounces, bounded by total maximum.
		""",
		"label" : "Glossy",
		"layout:section" : "Ray Depth",

	},

	"option:cycles:integrator:max_transmission_bounce" : {

		"defaultValue" : 7,
		"description" :
		"""
		Maximum number of transmission reflection bounces, bounded by total maximum.
		""",
		"label" : "Transmission",
		"layout:section" : "Ray Depth",

	},

	"option:cycles:integrator:max_volume_bounce" : {

		"defaultValue" : 7,
		"description" :
		"""
		Maximum number of volumetric scattering events.
		""",
		"label" : "Volume",
		"layout:section" : "Ray Depth",

	},

	"option:cycles:integrator:transparent_min_bounce" : {

		"defaultValue" : 0,
		"description" :
		"""
		Minimum number of transparent bounces. Setting this higher reduces noise in the first bounces,
		but can also be less efficient for more complex geometry like hair and volumes.
		""",
		"label" : "Min Transparency",
		"layout:section" : "Ray Depth",

	},

	"option:cycles:integrator:transparent_max_bounce" : {

		"defaultValue" : 7,
		"description" :
		"""
		Maximum number of transparent bounces.
		""",
		"label" : "Max Transparency",
		"layout:section" : "Ray Depth",

	},

	"option:cycles:integrator:ao_bounces" : {

		"defaultValue" : 0,
		"description" :
		"""
		Maximum number of ambient occlusion bounces.
		""",
		"label" : "Ambient Occlusion",
		"layout:section" : "Ray Depth",

	},

	"option:cycles:integrator:ao_factor" : {

		"defaultValue" : 0.0,
		"description" :
		"""
		Ambient occlusion factor.
		""",
		"label" : "Ambient Occlusion Factor",
		"layout:section" : "Background",

	},

	"option:cycles:integrator:ao_distance" : {

		"defaultValue" : 3.4028234663852886e+38,
		"description" :
		"""
		Ambient occlusion distance.
		""",
		"label" : "Ambient Occlusion Distance",
		"layout:section" : "Background",

	},

	"option:cycles:integrator:volume_max_steps" : {

		"defaultValue" : 1024,
		"description" :
		"""
		Maximum number of steps through the volume before giving up,
		to avoid extremely long render times with big objects or small step
		sizes.
		""",
		"label" : "Volume Max Steps",
		"layout:section" : "Volumes",

	},

	"option:cycles:integrator:volume_step_rate" : {

		"defaultValue" : 0.1,
		"description" :
		"""
		Globally adjust detail for volume rendering, on top of automatically estimated step size.
		Higher values reduce render time, lower values render with more detail.
		""",
		"label" : "Volume Step Rate",
		"layout:section" : "Volumes",

	},

	"option:cycles:integrator:caustics_reflective" : {

		"defaultValue" : True,
		"description" :
		"""
		Use reflective caustics, resulting in a brighter image
		(more noise but added realism).
		""",
		"label" : "Reflective Caustics",
		"layout:section" : "Caustics",

	},

	"option:cycles:integrator:caustics_refractive" : {

		"defaultValue" : True,
		"description" :
		"""
		Use refractive caustics, resulting in a brighter image
		(more noise but added realism).
		""",
		"label" : "Refractive Caustics",
		"layout:section" : "Caustics",

	},

	"option:cycles:integrator:filter_glossy" : {

		"defaultValue" : 0.0,
		"description" :
		"""
		Adaptively blur glossy shaders after blurry bounces, to reduce
		noise at the cost of accuracy.
		""",
		"label" : "Filter Glossy",
		"layout:section" : "Sampling",

	},

	"option:cycles:integrator:seed" : {

		"defaultValue" : 0,
		"description" :
		"""
		Seed value for the sampling pattern. If not specified, the frame number is used instead.
		""",
		"label" : "Seed Value",
		"layout:section" : "Sampling",

	},

	"option:cycles:integrator:sample_clamp_direct" : {

		"defaultValue" : 0.0,
		"description" :
		"""
		Clamp value for sampling direct rays.
		""",
		"label" : "Sample Clamp Direct",
		"layout:section" : "Sampling",

	},

	"option:cycles:integrator:sample_clamp_indirect" : {

		"defaultValue" : 0.0,
		"description" :
		"""
		Clamp value for sampling indirect rays.
		""",
		"label" : "Sample Clamp Indirect",
		"layout:section" : "Sampling",

	},

	"option:cycles:integrator:start_sample" : {

		"defaultValue" : 0,
		"description" :
		"""
		Start sample.
		""",
		"label" : "Start Sample",
		"layout:section" : "Sampling",

	},

	"option:cycles:integrator:use_light_tree" : {

		"defaultValue" : True,
		"description" :
		"""
		Sample multiple lights more efficiently based on estimated contribution at every shading point.
		""",
		"label" : "Use Light Tree",
		"layout:section" : "Sampling",

	},

	"option:cycles:integrator:light_sampling_threshold" : {

		"defaultValue" : 0.05,
		"description" :
		"""
		Probabilistically terminate light samples when the light
		contribution is below this threshold (more noise but faster
		rendering).
		`0` disables the test and never ignores lights.
		""",
		"label" : "Light Sampling Threshold",
		"layout:section" : "Sampling",

	},

	"option:cycles:integrator:use_adaptive_sampling" : {

		"defaultValue" : False,
		"description" :
		"""
		Automatically determine the number of samples
		per pixel based on a variance estimation.
		""",
		"label" : "Adaptive Sampling",
		"layout:section" : "Sampling",

	},

	"option:cycles:integrator:adaptive_threshold" : {

		"defaultValue" : 0.0,
		"description" :
		"""
		Noise level step to stop sampling at, lower values reduce noise the cost of render time.
		`0` for automatic setting based on number of AA samples.
		""",
		"label" : "Adaptive Threshold",
		"layout:section" : "Sampling",

	},

	"option:cycles:integrator:adaptive_min_samples" : {

		"defaultValue" : 0,
		"description" :
		"""
		Minimum AA samples for adaptive sampling, to discover noisy features before stopping sampling.
		`0` for automatic setting based on number of AA samples.
		""",
		"label" : "Adaptive Min Samples",
		"layout:section" : "Sampling",

	},

	"option:cycles:integrator:denoiser_type" : {

		"defaultValue" : "openimagedenoise",
		"description" :
		"""
		Denoise the image with the selected denoiser.

		- OptiX : Use the OptiX AI denoiser with GPU acceleration, only available on NVIDIA GPUs
		- OpenImageDenoise : Use the Intel OpenImageDenoise AI denoiser running on the CPU

		> Tip : Only outputs that include a `denoise` parameter set to `true` will be denoised.
		> Denoised outputs are renamed to include a "denoised" suffix.
		""",
		"label" : "Denoising Type",
		"layout:section" : "Denoising",

		"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",

	},

	"option:cycles:denoise_device" : {

		"defaultValue" : "*",
		"description" :
		"""
		The device to denoise with. If multiple devices are specified, Cycles will denoise with
		the first suitable device from the list.

		`Automatic` mode allows Cycles to choose from all available devices that support the current
		denoiser.
		""",
		"label" : "Denoise Device",
		"layout:section" : "Denoising",

		"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",
		"presetsPlugValueWidget:allowCustom" : True,

	},

	"option:cycles:integrator:denoise_start_sample" : {

		"defaultValue" : 0,
		"description" :
		"""
		Sample to start denoising the preview at.
		""",
		"label" : "Denoising Start Sample",
		"layout:section" : "Denoising",

	},

	"option:cycles:integrator:use_denoise_pass_albedo" : {

		"defaultValue" : True,
		"description" :
		"""
		Use albedo pass for denoising.
		""",
		"label" : "Use Denoise Pass Albedo",
		"layout:section" : "Denoising",

	},

	"option:cycles:integrator:use_denoise_pass_normal" : {

		"defaultValue" : True,
		"description" :
		"""
		Use normal pass for denoising.
		""",
		"label" : "Use Denoise Pass Normal",
		"layout:section" : "Denoising",

	},

	"option:cycles:integrator:denoiser_prefilter" : {

		"defaultValue" : "accurate",
		"description" :
		"""
		None - No prefiltering, use when guiding passes are noise-free.
		Fast - Denoise color and guiding passes together. Improves quality when guiding passes are noisy using least amount of extra processing time.
		Accurate - Prefilter noisy guiding passes before denoising color. Improves quality when guiding passes are noisy using extra processing time.
		""",
		"label" : "Denoising Pre-Filter",
		"layout:section" : "Denoising",

		"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",
		"presetNames" : IECore.StringVectorData( [ "None", "Fast", "Accurate" ] ),
		"presetValues" : IECore.StringVectorData( [ "none", "fast", "accurate" ] ),


	},

	"option:cycles:integrator:use_guiding" : {

		"defaultValue" : False,
		"description" :
		"""
		Use path guiding for sampling paths. Path guiding incrementally
		learns the light distribution of the scene and guides path into directions
		with high direct and indirect light contributions.
		""",
		"label" : "Path Guiding",
		"layout:section" : "Path-Guiding",

	},

	"option:cycles:integrator:use_surface_guiding" : {

		"defaultValue" : True,
		"description" :
		"""
		Use guiding when sampling directions on a surface.
		""",
		"label" : "Use Surface Guiding",
		"layout:section" : "Path-Guiding",

	},

	"option:cycles:integrator:use_volume_guiding" : {

		"defaultValue" : True,
		"description" :
		"""
		Use guiding when sampling directions inside a volume.
		""",
		"label" : "Use Volume Guiding",
		"layout:section" : "Path-Guiding",

	},

	"option:cycles:integrator:guiding_training_samples" : {

		"defaultValue" : 128,
		"description" :
		"""
		The maximum number of samples used for training path guiding.
		Higher samples lead to more accurate guiding, however may also
		unnecessarily slow down rendering once guiding is accurate enough.
		A value of 0 will continue training until the last sample.
		""",
		"label" : "Guiding Training Samples",
		"layout:section" : "Path-Guiding",

	},

	"option:cycles:background:use_shader" : {

		"defaultValue" : True,
		"description" :
		"""
		Use background shader. There must be a CyclesBackground node with
		a shader attached to it.
		""",
		"label" : "Use Shader",
		"layout:section" : "Background",

	},

	"option:cycles:background:visibility:camera" : {

		"defaultValue" : True,
		"description" :
		"""
		Whether or not the background is visible to camera
		rays.
		""",
		"label" : "Camera Visible",
		"layout:section" : "Background",

	},

	"option:cycles:background:visibility:diffuse" : {

		"defaultValue" : True,
		"description" :
		"""
		Whether or not the background is visible to diffuse
		rays.
		""",
		"label" : "Diffuse Visible",
		"layout:section" : "Background",

	},

	"option:cycles:background:visibility:glossy" : {

		"defaultValue" : True,
		"description" :
		"""
		Whether or not the background is visible in
		glossy rays.
		""",
		"label" : "Glossy Visible",
		"layout:section" : "Background",

	},

	"option:cycles:background:visibility:transmission" : {

		"defaultValue" : True,
		"description" :
		"""
		Whether or not the background is visible in
		transmission.
		""",
		"label" : "Transmission Visible",
		"layout:section" : "Background",

	},

	"option:cycles:background:visibility:shadow" : {

		"defaultValue" : True,
		"description" :
		"""
		Whether or not the background is visible to shadow
		rays - whether it casts shadows or not.
		""",
		"label" : "Shadow Visible",
		"layout:section" : "Background",

	},

	"option:cycles:background:visibility:scatter" : {

		"defaultValue" : True,
		"description" :
		"""
		Whether or not the background is visible to
		scatter rays.
		""",
		"label" : "Scatter Visible",
		"layout:section" : "Background",

	},

	"option:cycles:background:transparent" : {

		"defaultValue" : True,
		"description" :
		"""
		Make the background transparent.
		""",
		"label" : "Transparent",
		"layout:section" : "Background",

	},

	"option:cycles:background:transparent_glass" : {

		"defaultValue" : False,
		"description" :
		"""
		Background can be seen through transmissive surfaces.
		""",
		"label" : "Transmission Visible",
		"layout:section" : "Background",

	},

	"option:cycles:background:transparent_roughness_threshold" : {

		"defaultValue" : 0.0,
		"description" :
		"""
		Roughness threshold of background shader in transmissive surfaces.
		""",
		"label" : "Roughness Threshold",
		"layout:section" : "Background",

	},

	"option:cycles:film:exposure" : {

		"defaultValue" : 1.0,
		"description" :
		"""
		Image brightness scale.
		""",
		"label" : "Exposure",
		"layout:section" : "Film",

	},

	"option:cycles:film:pass_alpha_threshold" : {

		"defaultValue" : 0.5,
		"description" :
		"""
		Alpha threshold.
		""",
		"label" : "Pass Alpha Threshold",
		"layout:section" : "Film",

	},

	"option:cycles:film:display_pass" : {

		"defaultValue" : "combined",
		"description" :
		"""
		Render pass to show in the 3D Viewport.
		""",
		"label" : "Display Pass",
		"layout:section" : "Film",

		"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",

	},

	"option:cycles:film:show_active_pixels" : {

		"defaultValue" : False,
		"description" :
		"""
		When using adaptive sampling highlight pixels which are being sampled.
		""",
		"label" : "Show Active Pixels",
		"layout:section" : "Film",

	},

	"option:cycles:film:filter_type" : {

		"defaultValue" : "box",
		"description" :
		"""
		Image filter type.
		""",
		"label" : "Filter Type",
		"layout:section" : "Film",

		"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",
		"presetNames" : IECore.StringVectorData( [ "Box", "Gaussian", "Blackman Harris" ] ),
		"presetValues" : IECore.StringVectorData( [ "box", "gaussian", "blackman_harris" ] ),

	},

	"option:cycles:film:filter_width" : {

		"defaultValue" : 1.0,
		"description" :
		"""
		Pixel width of the filter.
		""",
		"label" : "Filter Width",
		"layout:section" : "Film",

	},

	"option:cycles:film:mist_start" : {

		"defaultValue" : 0.0,
		"description" :
		"""
		Start of the mist/fog.
		""",
		"label" : "Mist Start",
		"layout:section" : "Film",

	},

	"option:cycles:film:mist_depth" : {

		"defaultValue" : 100.0,
		"description" :
		"""
		End of the mist/fog.
		""",
		"label" : "Mist Depth",
		"layout:section" : "Film",

	},

	"option:cycles:film:mist_falloff" : {

		"defaultValue" : 1.0,
		"description" :
		"""
		Falloff of the mist/fog.
		""",
		"label" : "Mist Falloff",
		"layout:section" : "Film",

	},

	"option:cycles:film:cryptomatte_depth" : {

		"defaultValue" : 6,
		"description" :
		"""
		Sets how many unique objects can be distinguished per pixel.
		""",
		"label" : "Cryptomatte Depth",
		"layout:section" : "Film",

	},

	"option:cycles:dicing_camera" : {

		"defaultValue" : "",
		"description" :
		"""
		Camera to use as reference point when subdividing geometry, useful
		to avoid crawling artifacts in animations when the scene camera is
		moving.
		""",
		"label" : "Dicing Camera",
		"layout:section" : "Subdivision",

		"plugValueWidget:type" : "GafferSceneUI.ScenePathPlugValueWidget",
		"path:valid" : True,
		"scenePathPlugValueWidget:setNames" : IECore.StringVectorData( [ "__cameras" ] ),
		"scenePathPlugValueWidget:setsLabel" : "Show only cameras",

	},

} )

Gaffer.Metadata.registerValue( "option:cycles:*", "category", "Cycles" )
