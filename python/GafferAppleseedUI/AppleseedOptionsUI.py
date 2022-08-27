##########################################################################
#
#  Copyright (c) 2014, Esteban Tovagliari. All rights reserved.
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

import appleseed

import IECore

import Gaffer
import GafferScene
import GafferUI
import GafferAppleseed

# Get the render settings metadata dictionary from appleseed
__optionsMetadata = appleseed.Configuration.get_metadata()

def __getDescriptionString( key, extraInfo = None ):

	try :

		d = __optionsMetadata
		for k in key.split( ":" ) :
			d = d[k]
		result = d["help"]

		if extraInfo :
			result += '.' + extraInfo

		return result

	except KeyError :

		return ""

def __getShadingOverridesPresets():

	modes = appleseed.SurfaceShader.get_input_metadata()['diagnostic_surface_shader']['mode']['items']
	presets = ["preset:No Override", "no_override"]

	for k in modes.keys():

		presets.append( "preset:" + k )
		presets.append( modes[k] )

	return presets

def __mainSummary( plug ) :

	info = []
	if plug["renderPasses"]["enabled"].getValue() :
		info.append( "Passes %d" % plug["renderPasses"]["value"].getValue() )
	if plug["sampler"]["enabled"].getValue() :
		info.append( "Sampler %s" % plug["sampler"]["value"].getValue() )
	if plug["maxAASamples"]["enabled"].getValue() :
		info.append( "AA Samples %d" % plug["maxAASamples"]["value"].getValue() )
	if plug["lightingEngine"]["enabled"].getValue() :
		info.append( "Lighting Engine %s" % plug["lightingEngine"]["value"].getValue() )

	return ", ".join( info )

def __environmentSummary( plug ) :

	info = []
	if plug["environmentEDF"]["enabled"].getValue() :
		info.append( "Environment %s" % plug["environmentEDF"]["value"].getValue() )
	if plug["environmentEDFBackground"]["enabled"].getValue() and plug["environmentEDFBackground"]["value"].getValue() :
		info.append( "Visible in Background" )

	return ", ".join( info )

def __ptSummary( plug ) :

	info = []
	if plug["ptDirectLighting"]["enabled"].getValue() and plug["ptDirectLighting"]["value"].getValue() :
		info.append( "Direct Lighting" )
	if plug["ptIBL"]["enabled"].getValue() and plug["ptIBL"]["value"].getValue() :
		info.append( "IBL" )
	if plug["ptCaustics"]["enabled"].getValue() and plug["ptCaustics"]["value"].getValue() :
		info.append( "Caustics" )
	if plug["ptMaxBounces"]["enabled"].getValue() :
		info.append( "Max Bounces %d" % plug["ptMaxBounces"]["value"].getValue() )
	if plug["ptMaxBounces"]["enabled"].getValue() :
		info.append( "Max Bounces %d" % plug["ptMaxBounces"]["value"].getValue() )
	if plug["ptMaxDiffuseBounces"]["enabled"].getValue() :
		info.append( "Max Diffuse Bounces %d" % plug["ptMaxDiffuseBounces"]["value"].getValue() )
	if plug["ptMaxGlossyBounces"]["enabled"].getValue() :
		info.append( "Max Glossy Bounces %d" % plug["ptMaxGlossyBounces"]["value"].getValue() )
	if plug["ptMaxSpecularBounces"]["enabled"].getValue() :
		info.append( "Max Specular Bounces %d" % plug["ptMaxSpecularBounces"]["value"].getValue() )
	if plug["ptLightingSamples"]["enabled"].getValue() :
		info.append( "Lighting Samples %f" % plug["ptLightingSamples"]["value"].getValue() )
	if plug["ptIBLSamples"]["enabled"].getValue() :
		info.append( "IBL Samples %f" % plug["ptIBLSamples"]["value"].getValue() )
	if plug["ptMaxRayIntensity"]["enabled"].getValue() :
		info.append( "Max Ray Intensity %f" % plug["ptMaxRayIntensity"]["value"].getValue() )
	if plug["ptClampRoughness"]["enabled"].getValue() :
		info.append( "Clamp Roughness %f" % plug["ptClampRoughness"]["value"].getValue() )

	return ", ".join( info )

def __sppmSummary( plug ) :

	info = []
	if plug["photonType"]["enabled"].getValue() :
		info.append( "Photon Type %s" % plug["photonType"]["value"].getValue() )
	if plug["sppmDirectLighting"]["enabled"].getValue() and plug["sppmDirectLighting"]["value"].getValue() != 'off' :
		info.append( "Direct Lighting %s" % plug["sppmDirectLighting"]["value"].getValue() )
	if plug["sppmIBL"]["enabled"].getValue() and plug["sppmIBL"]["value"].getValue() :
		info.append( "IBL" )
	if plug["sppmCaustics"]["enabled"].getValue() and plug["sppmCaustics"]["value"].getValue() :
		info.append( "Caustics" )
	if plug["sppmPhotonMaxBounces"]["enabled"].getValue() :
		info.append( "Max Photon Bounces %d" % plug["sppmPhotonMaxBounces"]["value"].getValue() )
	if plug["sppmPathMaxBounces"]["enabled"].getValue() :
		info.append( "Max Path Bounces %d" % plug["sppmPathMaxBounces"]["value"].getValue() )
	if plug["sppmLightPhotons"]["enabled"].getValue() :
		info.append( "Light Photons %d" % plug["sppmLightPhotons"]["value"].getValue() )
	if plug["sppmEnvPhotons"]["enabled"].getValue() :
		info.append( "Environment Photons %d" % plug["sppmEnvPhotons"]["value"].getValue() )
	if plug["sppmInitialRadius"]["enabled"].getValue() :
		info.append( "Initial Radius %d" % plug["sppmInitialRadius"]["value"].getValue() )
	if plug["sppmMaxPhotons"]["enabled"].getValue() :
		info.append( "Max Photons %d" % plug["sppmMaxPhotons"]["value"].getValue() )
	if plug["sppmAlpha"]["enabled"].getValue() :
		info.append( "Alpha %f" % plug["sppmAlpha"]["value"].getValue() )

	return ", ".join( info )

def __denoiserSummary( plug ) :

	info = []
	if plug["denoiserMode"]["enabled"].getValue() :
		info.append( "Denoiser %s" % plug["denoiserMode"]["value"].getValue() )
	if plug["denoiserSkipPixels"]["enabled"].getValue() :
		info.append( "Skip Pixels %s" % plug["denoiserSkipPixels"]["value"].getValue() )
	if plug["denoiserRandomPixelOrder"]["enabled"].getValue() :
		info.append( "Random Order %s" % plug["denoiserRandomPixelOrder"]["value"].getValue() )
	if plug["denoiserScales"]["enabled"].getValue() :
		info.append( "Scales %s" % plug["denoiserScales"]["value"].getValue() )

	return ", ".join( info )

def __systemSummary( plug ) :

	info = []
	if plug["searchPath"]["enabled"].getValue() :
		info.append( "Searchpath %s" % plug["searchPath"]["value"].getValue() )
	if plug["numThreads"]["enabled"].getValue() :
		info.append( "Threads %d" % plug["numThreads"]["value"].getValue() )
	if plug["interactiveRenderFps"]["enabled"].getValue() :
		info.append( "Interactive Render Fps %d" % plug["interactiveRenderFps"]["value"].getValue() )
	if plug["textureMem"]["enabled"].getValue() :
		info.append( "Texture Mem %d bytes" % plug["textureMem"]["value"].getValue() )
	if plug["tileOrdering"]["enabled"].getValue() :
		info.append( "Tile Ordering %s" % plug["tileOrdering"]["value"].getValue().capitalize() )

	return ", ".join( info )

def __loggingSummary( plug ) :

	info = []
	if plug["logLevel"]["enabled"].getValue() :
		info.append( "Log Level %s" % plug["logLevel"]["value"].getValue().capitalize() )
	if plug["logFileName"]["enabled"].getValue() :
		info.append( "File name" )

	return ", ".join( info )

Gaffer.Metadata.registerNode(

	GafferAppleseed.AppleseedOptions,

	"description",
	"""
	Sets global scene options applicable to the appleseed
	renderer. Use the StandardOptions node to set
	global options applicable to all renderers.
	""",

	plugs = {

		# Sections

		"options" : [

			"layout:section:Main:summary", __mainSummary,
			"layout:section:Environment:summary", __environmentSummary,
			"layout:section:Unidirectional Path Tracer:summary", __ptSummary,
			"layout:section:SPPM:summary", __sppmSummary,
			"layout:section:Denoiser:summary", __denoiserSummary,
			"layout:section:System:summary", __systemSummary,
			"layout:section:Logging:summary", __loggingSummary,

		],

		# Main

		"options.renderPasses" : [

			"description",
			__getDescriptionString(
				"passes",
				"""
				When using photon mapping this is the number of
				progressive refinement passes used.
				"""
			),

			"layout:section", "Main",
			"label", "Passes",

		],

		"options.sampler" : [

			"description",
			"Antialiasing sampler",

			"layout:section", "Main",

		],

		"options.sampler.value" : [

			"preset:Uniform", "generic",
			"preset:Adaptive", "adaptive",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"options.minAASamples" : [

			"description",
			__getDescriptionString( "adaptive_tile_renderer:min_samples" ),

			"layout:section", "Main",
			"label", "Min Samples",

		],

		"options.maxAASamples" : [

			"description",
			__getDescriptionString( "adaptive_tile_renderer:max_samples" ),

			"layout:section", "Main",
			"label", "Max Samples",

		],

		"options.aaBatchSampleSize" : [

			"description",
			__getDescriptionString( "adaptive_tile_renderer:batch_size" ),

			"layout:section", "Main",
			"label", "Batch Sample Size",

		],

		"options.aaNoiseThresh" : [

			"description",
			__getDescriptionString( "adaptive_tile_renderer:noise_threshold" ),

			"layout:section", "Main",
			"label", "Noise Threshold",

		],

		"options.lightingEngine" : [

			"description",
			__getDescriptionString( "lighting_engine" ),

			"layout:section", "Main",

		],

		"options.lightingEngine.value" : [

			"preset:Unidirectional Path Tracer", "pt",
			"preset:SPPM", "sppm",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"options.shadingOverride" : [

			"description",
			"""
			Replaces all shaders in the scene by special
			diagnostics shaders that can visualize uvs, normals, ...
			Useful for debugging scenes.
			""",

			"layout:section", "Main",
			"label", "Shading Override",

		],

		"options.shadingOverride.value" : [

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		] + __getShadingOverridesPresets(),


		# Environment

		"options.environmentEDF" : [

			"description",
			"""
			Light to use as the environment.
			""",

			"layout:section", "Environment",
			"label", "Environment Light",

		],

		"options.environmentEDF.value" : [

			"plugValueWidget:type", "GafferSceneUI.ScenePathPlugValueWidget",
			"path:valid", True,
			"scenePathPlugValueWidget:setNames", IECore.StringVectorData( [ "__lights" ] ),
			"scenePathPlugValueWidget:setsLabel", "Show only lights",

		],

		"options.environmentEDFBackground" : [

			"description",
			"""
			Whether or not the environment is visible in the background.
			""",

			"layout:section", "Environment",
			"label", "Visible in Background",

		],

		# Unidirectional Path Tracer

		"options.ptDirectLighting" : [

			"description",
			__getDescriptionString( "pt:enable_dl" ),

			"layout:section", "Unidirectional Path Tracer",
			"label", "Direct Lighting",

		],

		"options.ptIBL" : [

			"description",
			__getDescriptionString( "pt:enable_ibl" ),

			"layout:section", "Unidirectional Path Tracer",
			"label", "Image Based Lighting",

		],

		"options.ptCaustics" : [

			"description",
			__getDescriptionString( "pt:enable_caustics" ),

			"layout:section", "Unidirectional Path Tracer",
			"label", "Caustics",

		],

		"options.ptMaxBounces" : [

			"description",
			__getDescriptionString(
				"pt:max_bounces",
				"If set to a negative number, use an unlimited number of bounces"
			),

			"layout:section", "Unidirectional Path Tracer",
			"label", "Max Bounces",

		],

		"options.ptMaxDiffuseBounces" : [

			"description",
			__getDescriptionString(
				"pt:max_diffuse_bounces",
				"If set to a negative number, use an unlimited number of bounces"
			),

			"layout:section", "Unidirectional Path Tracer",
			"label", "Max Diffuse Bounces",

		],

		"options.ptMaxGlossyBounces" : [

			"description",
			__getDescriptionString(
				"pt:max_glossy_bounces",
				"If set to a negative number, use an unlimited number of bounces"
			),

			"layout:section", "Unidirectional Path Tracer",
			"label", "Max Glossy Bounces",

		],

		"options.ptMaxSpecularBounces" : [

			"description",
			__getDescriptionString(
				"pt:max_specular_bounces",
				"If set to a negative number, use an unlimited number of bounces"
			),

			"layout:section", "Unidirectional Path Tracer",
			"label", "Max Specular Bounces",

		],

		"options.ptLightingSamples" : [

			"description",
			__getDescriptionString( "pt:dl_light_samples" ),

			"layout:section", "Unidirectional Path Tracer",
			"label", "Direct Lighting Samples",

		],

		"options.ptIBLSamples" : [

			"description",
			__getDescriptionString( "pt:ibl_env_samples" ),

			"layout:section", "Unidirectional Path Tracer",
			"label", "IBL Samples",

		],

		"options.ptMaxRayIntensity" : [

			"description",
			__getDescriptionString(
				"pt:max_ray_intensity",
				"Set to zero to disable"
			),

			"layout:section", "Unidirectional Path Tracer",
			"label", "Max Ray Intensity",

		],

		"options.ptClampRoughness" : [

			"description",
			__getDescriptionString("pt:clamp_roughness"),

			"layout:section", "Unidirectional Path Tracer",
			"label", "Clamp Roughness",

		],

		# SPPM

		"options.photonType" : [

			"description",
			__getDescriptionString( "sppm:photon_type" ),

			"layout:section", "SPPM",
			"label", "Photon Type",

		],

		"options.photonType.value" : [

			"preset:Monochromatic", "mono",
			"preset:Polychromatic", "poly",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"options.sppmDirectLighting" : [

			"description",
			__getDescriptionString( "sppm:dl_type" ),

			"layout:section", "SPPM",
			"label", "Direct Lighting",

		],

		"options.sppmDirectLighting.value" : [

			"preset:Ray Tracing", "rt",
			"preset:SPPM", "sppm",
			"preset:None", "off",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"options.sppmIBL" : [

			"description",
			__getDescriptionString( "sppm:enable_ibl" ),

			"layout:section", "SPPM",
			"label", "Image Based Lighting",

		],

		"options.sppmCaustics" : [

			"description",
			__getDescriptionString( "sppm:enable_caustics" ),

			"layout:section", "SPPM",
			"label", "Caustics",

		],

		"options.sppmPhotonMaxBounces" : [

			"description",
			__getDescriptionString(
				"sppm:photon_tracing_max_bounces",
				"If set to a negative number, use an unlimited number of bounces"
			),

			"layout:section", "SPPM",
			"label", "Max Photon Bounces",

		],

		"options.sppmPathMaxBounces" : [

			"description",
			__getDescriptionString(
				"sppm:path_tracing_max_bounces",
				"If set to a negative number, use an unlimited number of bounces"
			),

			"layout:section", "SPPM",
			"label", "Max Path Bounces",

		],

		"options.sppmLightPhotons" : [

			"description",
			__getDescriptionString( "sppm:light_photons_per_pass" ),

			"layout:section", "SPPM",
			"label", "Light Photons",

		],

		"options.sppmEnvPhotons" : [

			"description",
			__getDescriptionString( "sppm:env_photons_per_pass" ),

			"layout:section", "SPPM",
			"label", "Environment Photons",

		],

		"options.sppmInitialRadius" : [

			"description",
			__getDescriptionString( "sppm:initial_radius" ),

			"layout:section", "SPPM",
			"label", "Initial Radius",

		],

		"options.sppmMaxPhotons" : [

			"description",
			__getDescriptionString( "sppm:max_photons_per_estimate" ),

			"layout:section", "SPPM",
			"label", "Max Photons",

		],

		"options.sppmAlpha" : [

			"description",
			__getDescriptionString( "sppm:alpha" ),

			"layout:section", "SPPM",
			"label", "Alpha",

		],

		# Denoiser

		"options.denoiserMode" : [

			"description",
			"""
			Enable the denoiser.
			When choosing Write Outputs, two EXR images with denoising AOVs
			will be written in the same directory as the beauty image.
			The command line denoiser in appleseed can be used with the EXR files
			to produce denoised images.
			""",

			"layout:section", "Denoiser",
			"label", "Denoiser",
		],

		"options.denoiserMode.value" : [

			"preset:Off", "off",
			"preset:On", "on",
			"preset:Write Outputs", "write_outputs",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"options.denoiserSkipPixels" : [

			"description",
			"""
			Disabling this option will produce better results
			at the expense of slower processing time.
			""",

			"layout:section", "Denoiser",
			"label", "Skip Denoised Pixels",

		],

		"options.denoiserRandomPixelOrder" : [

			"description",
			"""
			Process pixels in random order.
			Enabling this option can help reducing artifacts.
			""",

			"layout:section", "Denoiser",
			"label", "Random Pixel Order",

		],

		"options.denoiserScales" : [

			"description",
			"""
			Number of resolution scales used for denoising.
			""",

			"layout:section", "Denoiser",
			"label", "Denoise Scales",

		],

		# System

		"options.searchPath" : [

			"description",
			"""
			The filesystem paths where shaders and textures
			are searched for.
			""",

			"layout:section", "System",

		],

		"options.numThreads" : [

			"description",
			__getDescriptionString(
				"rendering_threads",
				"Set to zero to use all CPU cores"
			),

			"layout:section", "System",
			"label", "Threads",

		],

		"options.interactiveRenderFps" : [

			"description",
			__getDescriptionString( "progressive_frame_renderer:max_fps" ),

			"layout:section", "System",

		],

		"options.interactiveRenderMaxSamples" : [

			"description",
			"""
			Sets the maximum number of samples to use when doing
			interactive rendering.
			""",

			"layout:section", "System",
			"plugValueWidget:type", ""

		],

		"options.textureMem" : [

			"description",
			__getDescriptionString( "texture_store:max_size" ),

			"layout:section", "System",
			"label", "Texture Cache Size",

		],

		"options.tileOrdering" : [

			"description",
			__getDescriptionString( "generic_frame_renderer:tile_ordering" ),

			"layout:section", "System",

		],

		"options.tileOrdering.value" : [

			"preset:Linear", "linear",
			"preset:Spiral", "spiral",
			"preset:Hilbert", "hilbert",
			"preset:Random", "random",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"options.logLevel" : [

			"description",
			"""
			Determines the verbosity of log
			output.
			""",

			"layout:section", "Logging",

		],

		"options.logLevel.value" : [

			"preset:Debug", "debug",
			"preset:Info", "info",
			"preset:Warning", "warning",
			"preset:Error", "error",
			"preset:Fatal", "fata",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"options.logFileName" : [

		"description",
		"""
		The name of a log file which appleseed will generate
		while rendering.
		""",

		"layout:section", "Logging",
		"label", "Log File",

		],

		"options.logFileName.value" : [

		"pathPlugValueWidget:leaf", True,
		"fileSystemPath:extensions", "txt log",
		"fileSystemPath:extensionsLabel", "Show only log files",

		],

}

)
