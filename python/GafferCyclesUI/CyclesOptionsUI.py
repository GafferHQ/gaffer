##########################################################################
#
#  Copyright (c) 2018, Alex Fuller. All rights reserved.
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
import GafferUI
import GafferCycles

def __sessionSummary( plug ) :

	info = []

	if plug["device"]["enabled"].getValue() :
		# We don't have enough space to display the full device string, but the
		# `:00` device indices are kindof confusing. Just strip off the
		# indices so we're showing a list of device types.
		devices = set(
			d.partition( ":" )[0]
			for d in plug["device"]["value"].getValue().split()
		)
		info.append( " + ".join( devices ) )

	if plug["shadingSystem"]["enabled"].getValue() :
		info.append( "Shading System {}".format( plug["shadingSystem"]["value"].getValue() ) )

	if plug["numThreads"]["enabled"].getValue() :
		info.append( "Threads {}".format( plug["numThreads"]["value"].getValue() ) )

	if plug["tileSize"]["enabled"].getValue() :
		info.append(
			"Tile Size {}".format( Gaffer.NodeAlgo.currentPreset( plug["tileSize"]["value"] ) )
		)

	if plug["pixelSize"]["enabled"].getValue() :
		info.append(
			"Pixel Size {}".format( Gaffer.NodeAlgo.currentPreset( plug["pixelSize"]["value"] ) )
		)

	if plug["timeLimit"]["enabled"].getValue() :
		info.append(
			"Time Limit {}".format( Gaffer.NodeAlgo.currentPreset( plug["timeLimit"]["value"] ) )
		)

	return ", ".join( info )

def __sceneSummary( plug ) :

	info = []

	if plug["bvhLayout"]["enabled"].getValue() :
		info.append( "BVH Layout {}".format( Gaffer.NodeAlgo.currentPreset( plug["bvhLayout"]["value"] ) ) )

	if plug["useBvhSpatialSplit"]["enabled"].getValue() :
		info.append( "Use BVH Spatial Splits {}".format( plug["useBvhSpatialSplit"]["value"].getValue() ) )

	if plug["useBvhUnalignedNodes"]["enabled"].getValue() :
		info.append( "Use BVH Unaligned Nodes {}".format( plug["useBvhUnalignedNodes"]["value"].getValue() ) )

	if plug["numBvhTimeSteps"]["enabled"].getValue() :
		info.append( "Num BVH Time Steps {}".format( plug["numBvhTimeSteps"]["value"].getValue() ) )

	if plug["hairSubdivisions"]["enabled"].getValue() :
		info.append( "Num hair subdivisions {}".format( plug["hairSubdivisions"]["value"].getValue() ) )

	if plug["hairShape"]["enabled"].getValue() :
		info.append( "Hair shape {}".format( Gaffer.NodeAlgo.currentPreset( plug["hairShape"]["value"] ) ) )

	if plug["textureLimit"]["enabled"].getValue() :
			info.append( "Texture Limit - {}".format( plug["textureLimit"]["value"].getValue() ) )

	return ", ".join( info )

def __samplingSummary( plug ) :

	info = []

	if plug["useAdaptiveSampling"]["enabled"].getValue() :
		info.append( "Use Adaptive Sampling {}".format( plug["useAdaptiveSampling"]["value"].getValue() ) )

	if plug["samples"]["enabled"].getValue() :
		info.append( "Samples {}".format( plug["samples"]["value"].getValue() ) )

	if plug["lightSamplingThreshold"]["enabled"].getValue() :
		info.append( "Light Sampling Threshold {}".format( plug["lightSamplingThreshold"]["value"].getValue() ) )

	if plug["adaptiveThreshold"]["enabled"].getValue() :
		info.append( "Adaptive Threshold {}".format( plug["adaptiveThreshold"]["value"].getValue() ) )

	if plug["adaptiveMinSamples"]["enabled"].getValue() :
		info.append( "Adaptive Min Samples {}".format( plug["adaptiveMinSamples"]["value"].getValue() ) )

	if plug["filterGlossy"]["enabled"].getValue() :
		info.append( "Filter Glossy {}".format( plug["filterGlossy"]["value"].getValue() ) )

	if plug["seed"]["enabled"].getValue() :
		info.append( "Seed Value {}".format( plug["seed"]["value"].getValue() ) )

	if plug["sampleClampDirect"]["enabled"].getValue() :
		info.append( "Sample Clamp Direct {}".format( plug["sampleClampDirect"]["value"].getValue() ) )

	if plug["sampleClampIndirect"]["enabled"].getValue() :
		info.append( "Sample Clamp Indirect {}".format( plug["sampleClampIndirect"]["value"].getValue() ) )

	if plug["startSample"]["enabled"].getValue() :
		info.append( "Start Sample {}".format( plug["startSample"]["value"].getValue() ) )

	return ", ".join( info )

def __pathGuidingSummary( plug ) :

	info = []

	for label, childName in (
		( "Guiding", "useGuiding" ),
		( "Surface", "useSurfaceGuiding" ),
		( "Volume", "useVolumeGuiding" ),
	) :
		if plug[childName]["enabled"].getValue() :
			info.append( "{} {}".format( label, "On" if plug[childName]["value"].getValue() else "Off" ) )

	if plug["guidingTrainingSamples"]["enabled"].getValue() :
			info.append( "Samples {}".format( plug["guidingTrainingSamples"]["value"].getValue() ) )

	return ", ".join( info )

def __rayDepthSummary( plug ) :

	info = []

	if plug["minBounce"]["enabled"].getValue() :
		info.append( "Min Bounces {}".format( plug["minBounce"]["value"].getValue() ) )

	if plug["maxBounce"]["enabled"].getValue() :
		info.append( "Max Bounces {}".format( plug["maxBounce"]["value"].getValue() ) )

	for rayType in ( "Diffuse", "Glossy", "Transmission", "Volume" ) :
		childName = "max%sBounce" % rayType
		if plug[childName]["enabled"].getValue() :
			info.append(
				"{} {}".format( rayType, plug[childName]["value"].getValue() )
			)

	if plug["transparentMinBounce"]["enabled"].getValue() :
		info.append( "Transparency Min Bounces {}".format( plug["transparentMinBounce"]["value"].getValue() ) )

	if plug["transparentMaxBounce"]["enabled"].getValue() :
		info.append( "Transparency Max Bounces {}".format( plug["transparentMaxBounce"]["value"].getValue() ) )

	return ", ".join( info )

def __volumesSummary( plug ) :

	info = []

	if plug["volumeStepSize"]["enabled"].getValue() :
		info.append( "Step Size {}".format( plug["volumeStepSize"]["value"].getValue() ) )

	if plug["volumeMaxSteps"]["enabled"].getValue() :
		info.append( "Max Steps {}".format( plug["volumeMaxSteps"]["value"].getValue() ) )

	if plug["volumeStepRate"]["enabled"].getValue() :
		info.append( "Step Rate {}".format( plug["volumeStepRate"]["value"].getValue() ) )

	return ", ".join( info )

def __causticsSummary( plug ) :

	info = []

	if plug["causticsReflective"]["enabled"].getValue() :
		info.append( "Reflective Caustics {}".format( plug["causticsReflective"]["value"].getValue() ) )

	if plug["causticsRefractive"]["enabled"].getValue() :
		info.append( "Refractive Caustics {}".format( plug["causticsRefractive"]["value"].getValue() ) )

	return ", ".join( info )

def __subdivisionSummary( plug ) :

	info = []

	#if plug["dicingRate"]["enabled"].getValue() :
	#	info.append( "Dicing Rate {}".format( plug["dicingRate"]["value"].getValue() ) )

	#if plug["maxSubdivisions"]["enabled"].getValue() :
	#	info.append( "Max Subdivisions {}".format( plug["maxSubdivisions"]["value"].getValue() ) )

	if plug["dicingCamera"]["enabled"].getValue() :
		info.append( "Dicing Camera {}".format( plug["dicingCamera"]["value"].getValue() ) )

	#if plug["offscreenDicingScale"]["enabled"].getValue() :
	#	info.append( "Offscreen Dicing Scale {}".format( plug["offscreenDicingScale"]["value"].getValue() ) )

	return ", ".join( info )

def __filmSummary( plug ) :

	info = []

	if plug["exposure"]["enabled"].getValue() :
		info.append( "Exposure {}".format( plug["exposure"]["value"].getValue() ) )

	if plug["passAlphaThreshold"]["enabled"].getValue() :
		info.append( "Pass Alpha Threshold {}".format( plug["passAlphaThreshold"]["value"].getValue() ) )

	if plug["filterType"]["enabled"].getValue() :
		info.append( "Filter Type {}".format( Gaffer.NodeAlgo.currentPreset( plug["filterType"]["value"] ) ) )

	if plug["filterWidth"]["enabled"].getValue() :
		info.append( "Filter Width {}".format( plug["filterWidth"]["value"].getValue() ) )

	if plug["mistStart"]["enabled"].getValue() :
		info.append( "Mist Start {}".format( plug["mistStart"]["value"].getValue() ) )

	if plug["mistDepth"]["enabled"].getValue() :
		info.append( "Mist Depth {}".format( plug["mistDepth"]["value"].getValue() ) )

	if plug["mistFalloff"]["enabled"].getValue() :
		info.append( "Mist Falloff {}".format( plug["mistFalloff"]["value"].getValue() ) )

	if plug["cryptomatteDepth"]["enabled"].getValue() :
		info.append( "Cryptomatte Depth {}".format( plug["cryptomatteDepth"]["value"].getValue() ) )

	return ", ".join( info )

def __denoisingSummary( plug ) :

	info = []

	if plug["denoiserType"]["enabled"].getValue() :
		info.append( "Denoise Type {}".format( plug["denoiserType"]["value"].getValue() ) )

	if plug["denoiseStartSample"]["enabled"].getValue() :
		info.append( "Denoise Start Sample {}".format( plug["denoiseStartSample"]["value"].getValue() ) )

	if plug["useDenoisePassAlbedo"]["enabled"].getValue() :
		info.append( "Use Denoise Pass Albedo {}".format( plug["useDenoisePassAlbedo"]["value"].getValue() ) )

	if plug["useDenoisePassNormal"]["enabled"].getValue() :
		info.append( "Use Denoise Pass Normal {}".format( plug["useDenoisePassNormal"]["value"].getValue() ) )

	if plug["denoiserPrefilter"]["enabled"].getValue() :
		info.append( "Denoise Pre-Filter {}".format( plug["denoiserPrefilter"]["value"].getValue() ) )

	return ", ".join( info )

def __backgroundSummary( plug ) :

	info = []

	if plug["aoFactor"]["enabled"].getValue() :
		info.append( "AO Factor {}".format( plug["aoFactor"]["value"].getValue() ) )

	if plug["aoDistance"]["enabled"].getValue() :
		info.append( "AO Distance {}".format( plug["aoDistance"]["value"].getValue() ) )

	if plug["bgUseShader"]["enabled"].getValue() :
		info.append( "Use Shader {}".format( plug["bgUseShader"]["value"].getValue() ) )

	if plug["bgTransparent"]["enabled"].getValue() :
		info.append( "Transparent {}".format( plug["bgTransparent"]["value"].getValue() ) )

	if plug["bgTransparentGlass"]["enabled"].getValue() :
		info.append( "Transparent Glass {}".format( plug["bgTransparentGlass"]["value"].getValue() ) )

	if plug["bgTransparentRoughnessThreshold"]["enabled"].getValue() :
		info.append( "Roughness Threshold {}".format( plug["bgTransparentRoughnessThreshold"]["value"].getValue() ) )

	for childName in ( "Camera", "Diffuse", "Glossy", "Transmission", "Shadow", "Scatter" ) :
		if plug["bg" + childName + "Visibility"]["enabled"].getValue() :
			info.append( IECore.CamelCase.toSpaced( childName ) + ( " On" if plug["bg" + childName + "Visibility"]["value"].getValue() else " Off" ) )

	return ", ".join( info )

def __logSummary( plug ) :

	info = []

	if plug["logLevel"]["enabled"].getValue() :
		info.append( "Log level {}".format( plug["logLevel"]["value"].getValue() ) )

	return ", ".join( info )

def __registerDevicePresets() :

	Gaffer.Metadata.registerValue( GafferCycles.CyclesOptions, "options.device.value", "preset:CPU", "CPU" )

	typeIndices = {}
	for device in GafferCycles.devices :

		if device["type"] == "CPU" :
			continue

		typeIndex = typeIndices.setdefault( device["type"], 0 )
		typeIndices[device["type"]] += 1

		Gaffer.Metadata.registerValue(
			GafferCycles.CyclesOptions,
			"options.device.value",
			"preset:{}/{}".format( device["type"], device["description"] ),
			"{}:{:02}".format( device["type"], typeIndex )
		)

		Gaffer.Metadata.registerValue(
			GafferCycles.CyclesOptions,
			"options.device.value",
			"preset:{}/{} + CPU".format( device["type"], device["description"] ),
			"CPU {}:{:02}".format( device["type"], typeIndex )
		)

	for deviceType, count in typeIndices.items() :

		if count <= 1 :
			continue

		Gaffer.Metadata.registerValue(
			GafferCycles.CyclesOptions,
			"options.device.value",
			"preset:{}/All".format( deviceType ),
			"{}:*".format( deviceType )
		)

		Gaffer.Metadata.registerValue(
			GafferCycles.CyclesOptions,
			"options.device.value",
			"preset:{}/All + CPU".format( deviceType ),
			"CPU {}:*".format( deviceType )
		)

Gaffer.Metadata.registerNode(

	GafferCycles.CyclesOptions,

	"description",
	"""
	Sets global scene options applicable to the Cycles
	renderer. Use the StandardOptions node to set
	global options applicable to all renderers.
	""",

	plugs = {

		# Sections

		"options" : [

			"layout:section:Session:summary", __sessionSummary,
			"layout:section:Scene:summary", __sceneSummary,
			"layout:section:Sampling:summary", __samplingSummary,
			"layout:section:Path-Guiding:summary", __pathGuidingSummary,
			"layout:section:Ray Depth:summary", __rayDepthSummary,
			"layout:section:Volumes:summary", __volumesSummary,
			"layout:section:Caustics:summary", __causticsSummary,
			"layout:section:Subdivision:summary", __subdivisionSummary,
			"layout:section:Film:summary", __filmSummary,
			"layout:section:Denoising:summary", __denoisingSummary,
			"layout:section:Background:summary", __backgroundSummary,
			"layout:section:Log:summary", __logSummary,

		],

		# Session

		"options.device" : [

			"description",
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

			"layout:section", "Session",
			"label", "Device(s)",

		],

		"options.device.value" : [


			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
			"presetsPlugValueWidget:allowCustom", True

		],

		"options.shadingSystem" : [

			"description",
			"""
			Shading system.

			- OSL : Use Open Shading Language (CPU rendering only).
			- SVM : Use Shader Virtual Machine.
			""",

			"layout:section", "Session",

		],

		"options.shadingSystem.value" : [

			"preset:OSL", "OSL",
			"preset:SVM", "SVM",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"options.numThreads" : [

			"description",
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

			"layout:section", "Session",

		],

		"options.tileSize" : [

			"description",
			"""
			Tile size for rendering.
			""",

			"layout:section", "Session",

		],

		"options.pixelSize" : [

			"description",
			"""
			Pixel Size.
			""",

			"layout:section", "Session",

		],

		"options.timeLimit" : [

			"description",
			"""
			Time-limit.
			""",

			"layout:section", "Session",

		],

		"options.useProfiling" : [

			"description",
			"""
			Use Profiling.
			""",

			"layout:section", "Session",

		],

		"options.useAutoTile" : [

			"description",
			"""
			Automatically render high resolution images in tiles to reduce memory usage, using the specified tile size. Tiles are cached to disk while rendering to save memory.
			""",

			"layout:section", "Session",

		],

		# Scene

		"options.bvhLayout" : [

			"description",
			"""
			BVH Layout size. This corresponds with CPU architecture
			(the higher the faster, but might not be supported on old CPUs).
			""",

			"layout:section", "Scene",
			"label", "BVH Layout",

		],

		"options.bvhLayout.value" : [

			"preset:BVH2", "bvh2",
			"preset:EMBREE", "embree",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"options.useBvhSpatialSplit" : [

			"description",
			"""
			Use BVH spatial splits: longer builder time, faster render.
			""",

			"layout:section", "Scene",
			"label", "Use Spatial Splits",

		],

		"options.useBvhUnalignedNodes" : [

			"description",
			"""
			Use special type BVH optimized for hair (uses more ram but renders faster).
			""",

			"layout:section", "Scene",
			"label", "Use Hair BVH",

		],

		"options.numBvhTimeSteps" : [

			"description",
			"""
			Split BVH primitives by this number of time steps to speed up render time in cost of memory.
			""",

			"layout:section", "Scene",
			"label", "BVH Time Steps",

		],

		"options.hairSubdivisions" : [

			"description",
			"""
			Split BVH primitives by this number of time steps to speed up render time in cost of memory.
			""",

			"layout:section", "Scene",
			"label", "Hair Subdivisions",

		],

		"options.hairShape" : [

			"description",
			"""
			Rounded Ribbons -Render hair as flat ribbon with rounded normals, for fast rendering.
			3D Curves - Render hair as 3D curve, for accurate results when viewing hair close up.
			""",

			"layout:section", "Scene",
			"label", "Hair Shape",

		],

		"options.hairShape.value" : [

			"preset:Round Ribbons", "ribbon",
			"preset:3D Curves", "thick",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"options.textureLimit" : [

			"description",
			"""
			Limit the maximum texture size used by final rendering.
			""",

			"layout:section", "Scene",
			"label", "Texture Size Limit",

		],

		"options.textureLimit.value" : [

			"preset:No Limit", 0,
			"preset:128", 1,
			"preset:256", 2,
			"preset:512", 3,
			"preset:1024", 4,
			"preset:2048", 5,
			"preset:4096", 6,
			"preset:8192", 7,

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		# Sampling

		"options.useAdaptiveSampling" : [

			"description",
			"""
			Automatically determine the number of samples per pixel based on a variance estimation.
			""",

			"layout:section", "Sampling",

		],

		"options.samples" : [

			"description",
			"""
			Number of samples to render for each pixel. This is for the
			path integrator, use the other sampling parameters for the
			branched-path integrator.
			""",

			"layout:section", "Sampling",
			"label", "Samples",

		],

		"options.lightSamplingThreshold" : [

			"description",
			"""
			Probabilistically terminate light samples when the light
			contribution is below this threshold (more noise but faster
			rendering).
			Zero disables the test and never ignores lights.
			""",

			"layout:section", "Sampling",

		],

		"options.adaptiveThreshold" : [

			"description",
			"""
			Noise level step to stop sampling at, lower values reduce noise the cost of render time.
			Zero for automatic setting based on number of AA samples.
			""",

			"layout:section", "Sampling",

		],

		"options.adaptiveMinSamples" : [

			"description",
			"""
			Minimum AA samples for adaptive sampling, to discover noisy features before stopping sampling.
			Zero for automatic setting based on number of AA samples.
			""",

			"layout:section", "Sampling",

		],

		"options.filterGlossy" : [

			"description",
			"""
			Adaptively blur glossy shaders after blurry bounces, to reduce
			noise at the cost of accuracy.
			""",

			"layout:section", "Sampling",

		],

		"options.seed" : [

			"description",
			"""
			Seed value for the sampling pattern. If not specified, the frame number is used instead.
			""",

			"layout:section", "Sampling",
			"label", "Seed Value",

		],

		"options.sampleClampDirect" : [

			"description",
			"""
			Clamp value for sampling direct rays.
			""",

			"layout:section", "Sampling",

		],

		"options.sampleClampIndirect" : [

			"description",
			"""
			Clamp value for sampling indirect rays.
			""",

			"layout:section", "Sampling",

		],

		"options.startSample" : [

			"description",
			"""
			Start sample.
			""",

			"layout:section", "Sampling",

		],

		"options.useLightTree" : [

			"description",
			"""
			Sample multiple lights more efficiently based on estimated contribution at every shading point.
			""",

			"layout:section", "Sampling",

		],

		# Path Guiding

		"options.useGuiding" : [

			"description",
			"""
			Use path guiding for sampling paths. Path guiding incrementally
			learns the light distribution of the scene and guides path into directions
			with high direct and indirect light contributions.
			""",

			"layout:section", "Path-Guiding",

		],

		"options.useSurfaceGuiding" : [

			"description",
			"""
			Use guiding when sampling directions on a surface.
			""",

			"layout:section", "Path-Guiding",

		],

		"options.useVolumeGuiding" : [

			"description",
			"""
			Use guiding when sampling directions inside a volume.
			""",

			"layout:section", "Path-Guiding",

		],

		"options.guidingTrainingSamples" : [

			"description",
			"""
			The maximum number of samples used for training path guiding.
			Higher samples lead to more accurate guiding, however may also unnecessarily slow
			down rendering once guiding is accurate enough.
			A value of 0 will continue training until the last sample.
			""",

			"layout:section", "Path-Guiding",

		],

		# Ray Depth

		"options.minBounce" : [

			"description",
			"""
			Minimum number of light bounces. Setting this higher reduces noise in the first bounces,
			but can also be less efficient for more complex geometry like hair and volumes.
			""",

			"layout:section", "Ray Depth",
			"label", "Min Bounces",

		],

		"options.maxBounce" : [

			"description",
			"""
			Total maximum number of bounces.
			""",

			"layout:section", "Ray Depth",
			"label", "Max Bounces",

		],

		"options.maxDiffuseBounce" : [

			"description",
			"""
			Maximum number of diffuse reflection bounces, bounded by total
			maximum.
			""",

			"layout:section", "Ray Depth",
			"label", "Diffuse",

		],

		"options.maxGlossyBounce" : [

			"description",
			"""
			Maximum number of glossy reflection bounces, bounded by total
			maximum.
			""",

			"layout:section", "Ray Depth",
			"label", "Glossy",

		],

		"options.maxTransmissionBounce" : [

			"description",
			"""
			Maximum number of transmission reflection bounces, bounded by total
			maximum.
			""",

			"layout:section", "Ray Depth",
			"label", "Transmission",

		],

		"options.maxVolumeBounce" : [

			"description",
			"""
			Maximum number of volumetric scattering events.
			""",

			"layout:section", "Ray Depth",
			"label", "Volume",

		],

		"options.transparentMinBounce" : [

			"description",
			"""
			Minimum number of transparent bounces. Setting this higher reduces noise in the first bounces,
			but can also be less efficient for more complex geometry like hair and volumes."
			""",

			"layout:section", "Ray Depth",
			"label", "Min Transparency",

		],

		"options.transparentMaxBounce" : [

			"description",
			"""
			Maximum number of transparent bounces.
			""",

			"layout:section", "Ray Depth",
			"label", "Max Transparency",

		],

		"options.aoBounces" : [

			"description",
			"""
			Maximum number of Ambient Occlusion bounces.
			""",

			"layout:section", "Ray Depth",
			"label", "Ambient Occlusion",

		],

		# Volumes

		"options.volumeStepSize" : [

			"description",
			"""
			Distance between volume shader samples when rendering the volume
			(lower values give more accurate and detailed results, but also
			increases render time).
			""",

			"layout:section", "Volumes",

		],

		"options.volumeMaxSteps" : [

			"description",
			"""
			Maximum number of steps through the volume before giving up,
			to avoid extremely long render times with big objects or small step
			sizes.
			""",

			"layout:section", "Volumes",

		],

		"options.volumeStepRate" : [

			"description",
			"""
			"Globally adjust detail for volume rendering, on top of automatically estimated step size."
			"Higher values reduce render time, lower values render with more detail."
			""",

			"layout:section", "Volumes",

		],

		# Caustics

		"options.causticsReflective" : [

			"description",
			"""
			Use reflective caustics, resulting in a brighter image
			(more noise but added realism).
			""",

			"layout:section", "Caustics",
			"label", "Reflective Caustics",

		],

		"options.causticsRefractive" : [

			"description",
			"""
			Use refractive caustics, resulting in a brighter image
			(more noise but added realism).
			""",

			"layout:section", "Caustics",
			"label", "Refractive Caustics",

		],

		# Subdivision

		#"options.dicingRate" : [

		#	"description",
		#	"""
		#	Size of a micropolygon in pixels.
		#	""",

		#	"layout:section", "Subdivision",

		#],

		#"options.maxSubdivisions" : [

		#	"description",
		#	"""
		#	Stop subdividing when this level is reached even if the dice rate
		#	would produce finer tessellation.
		#	""",

		#	"layout:section", "Subdivision",

		#],

		"options.dicingCamera" : [

			"description",
			"""
			Camera to use as reference point when subdividing geometry, useful
			to avoid crawling artifacts in animations when the scene camera is
			moving.
			""",

			"layout:section", "Subdivision",

		],

		"options.dicingCamera.value" : [

			"plugValueWidget:type", "GafferSceneUI.ScenePathPlugValueWidget",
			"path:valid", True,
			"scenePathPlugValueWidget:setNames", IECore.StringVectorData( [ "__cameras" ] ),
			"scenePathPlugValueWidget:setsLabel", "Show only cameras",

		],

		#"options.offscreenDicingScale" : [

		#	"description",
		#	"""
		#	Multiplier for dicing rate of geometry outside of the camera view.
		#	The dicing rate of objects is gradually increased the further they
		#	are outside the camera view. Lower values provide higher quality
		#	reflections and shadows for off screen objects, while higher values
		#	use less memory.
		#	""",

		#	"layout:section", "Subdivision",

		#],

		# Background

		"options.aoFactor" : [

			"description",
			"""
			Ambient Occlusion factor.
			""",

			"layout:section", "Background",
			"label", "Ambient Occlusion Factor",

		],

		"options.aoDistance" : [

			"description",
			"""
			Ambient Occlusion Distance.
			""",

			"layout:section", "Background",
			"label", "Ambient Occlusion Distance",

		],

		"options.bgUseShader" : [

			"description",
			"""
			Use background shader. There must be a CyclesBackground node with
			a shader attached to it.
			""",

			"layout:section", "Background",
			"label", "Use Shader",

		],

		"options.bgTransparent" : [

			"description",
			"""
			Make the background transparent.
			""",

			"layout:section", "Background",
			"label", "Transparent",

		],

		"options.bgTransparentGlass" : [

			"description",
			"""
			Background can be seen through transmissive surfaces.
			""",

			"layout:section", "Background",
			"label", "Transmission Visible",

		],

		"options.bgTransparentRoughnessThreshold" : [

			"description",
			"""
			Roughness threshold of background shader in transmissive surfaces.
			""",

			"layout:section", "Background",
			"label", "Roughness Threshold",

		],

		# BG Visibility

		"options.bgCameraVisibility" : [

			"description",
			"""
			Whether or not the background is visible to camera
			rays.
			""",

			"layout:section", "Background",
			"label", "Camera Visible",

		],

		"options.bgDiffuseVisibility" : [

			"description",
			"""
			Whether or not the background is visible to diffuse
			rays.
			""",

			"layout:section", "Background",
			"label", "Diffuse Visible",

		],

		"options.bgGlossyVisibility" : [

			"description",
			"""
			Whether or not the background is visible in
			glossy rays.
			""",

			"layout:section", "Background",
			"label", "Glossy Visible",

		],

		"options.bgTransmissionVisibility" : [

			"description",
			"""
			Whether or not the background is visible in
			transmission.
			""",

			"layout:section", "Background",
			"label", "Transmission Visible",

		],

		"options.bgShadowVisibility" : [

			"description",
			"""
			Whether or not the background is visible to shadow
			rays - whether it casts shadows or not.
			""",

			"layout:section", "Background",
			"label", "Shadow Visible",

		],

		"options.bgScatterVisibility" : [

			"description",
			"""
			Whether or not the background is visible to
			scatter rays.
			""",

			"layout:section", "Background",
			"label", "Scatter Visible",

		],

		# Film

		"options.exposure" : [

			"description",
			"""
			Image brightness scale.
			""",

			"layout:section", "Film",

		],

		"options.passAlphaThreshold" : [

			"description",
			"""
			Alpha threshold.
			""",

			"layout:section", "Film",

		],

		"options.filterType" : [

			"description",
			"""
			Image filter type.
			""",

			"layout:section", "Film",

		],

		"options.filterType.value" : [

			"preset:Box", "box",
			"preset:Gaussian", "gaussian",
			"preset:Blackman Harris", "blackman_harris",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"options.filterWidth" : [

			"description",
			"""
			Pixel width of the filter.
			""",

			"layout:section", "Film",

		],

		"options.mistStart" : [

			"description",
			"""
			Start of the mist/fog.
			""",

			"layout:section", "Film",

		],

		"options.mistDepth" : [

			"description",
			"""
			End of the mist/fog.
			""",

			"layout:section", "Film",

		],

		"options.mistFalloff" : [

			"description",
			"""
			Falloff of the mist/fog.
			""",

			"layout:section", "Film",

		],

		"options.cryptomatteDepth" : [

			"description",
			"""
			Sets how many unique objects can be distinguished per pixel.
			""",

			"layout:section", "Film",

		],

		"options.displayPass" : [

			"description",
			"""
			Render pass to show in the 3D Viewport.
			""",

			"layout:section", "Film",

		],

		"options.displayPass.value" : [

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"options.showActivePixels" : [

			"description",
			"""
			When using adaptive sampling highlight pixels which are being sampled.
			""",

			"layout:section", "Film",

		],

		# Denoising

		"options.denoiserType" : [

			"description",
			"""
			Denoise the image with the selected denoiser.
			OptiX - Use the OptiX AI denoiser with GPU acceleration, only available on NVIDIA GPUs
			OpenImageDenoise - Use Intel OpenImageDenoise AI denoiser running on the CPU
			""",

			"layout:section", "Denoising",
			"label", "Denoising Type",

		],

		"options.denoiserType.value" : [

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"options.denoiseStartSample" : [

			"description",
			"""
			Sample to start denoising the preview at.
			""",

			"layout:section", "Denoising",
			"label", "Denoising Start Sample",

		],

		"options.useDenoisePassAlbedo" : [

			"description",
			"""
			Use albedo pass for denoising.
			""",

			"layout:section", "Denoising",
			"label", "Use Denoise Pass Albedo",

		],

		"options.useDenoisePassNormal" : [

			"description",
			"""
			Use normal pass for denoising.
			""",

			"layout:section", "Denoising",
			"label", "Use Denoise Pass Normal",

		],

		"options.denoiserPrefilter" : [

			"description",
			"""
			None - No prefiltering, use when guiding passes are noise-free.
			Fast - Denoise color and guiding passes together. Improves quality when guiding passes are noisy using least amount of extra processing time.
			Accurate - Prefilter noisy guiding passes before denoising color. Improves quality when guiding passes are noisy using extra processing time.
			""",

			"layout:section", "Denoising",
			"label", "Denoising Pre-Filter",

		],

		"options.denoiserPrefilter.value" : [

			"preset:None", "none",
			"preset:Fast", "fast",
			"preset:Accurate", "accurate",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		# Log

		"options.logLevel" : [

			"description",
			"""
			Internal Cycles debugging log-level.
			""",

			"layout:section", "Log",
		],

		"options.logLevel.value" : [

			"preset:Off", 0,
			"preset:On", 1,
			"preset:Debug", 2,

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

	}
)

__registerDevicePresets()

if GafferCycles.hasOptixDenoise :

	Gaffer.Metadata.registerValue( GafferCycles.CyclesOptions, "options.denoiserType.value", "preset:OptiX Denoiser", "optix" )

if GafferCycles.hasOpenImageDenoise :

	Gaffer.Metadata.registerValue( GafferCycles.CyclesOptions, "options.denoiserType.value", "preset:Open Image Denoise", "openimagedenoise" )

for _pass in GafferCycles.passes.keys():
	Gaffer.Metadata.registerValue( GafferCycles.CyclesOptions, "options.displayPass.value", "preset:%s" % _pass.replace( "_", " " ).title(), "%s" % _pass )
