##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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
import GafferArnold

def __renderingSummary( plug ) :

	info = []
	if plug["bucketSize"]["enabled"].getValue() :
		info.append( "Bucket Size %d" % plug["bucketSize"]["value"].getValue() )
	if plug["bucketScanning"]["enabled"].getValue() :
		info.append( "Bucket Scanning %s" % plug["bucketScanning"]["value"].getValue().capitalize() )
	if plug["parallelNodeInit"]["enabled"].getValue() :
		info.append( "Parallel Init %s" % ( "On" if plug["parallelNodeInit"]["value"].getValue() else "Off" ) )
	if plug["threads"]["enabled"].getValue() :
		info.append( "Threads %d" % plug["threads"]["value"].getValue() )
	return ", ".join( info )

def __samplingSummary( plug ) :

	info = []
	if plug["aaSamples"]["enabled"].getValue() :
		info.append( "AA %d" % plug["aaSamples"]["value"].getValue() )
	if plug["giDiffuseSamples"]["enabled"].getValue() :
		info.append( "Diffuse %d" % plug["giDiffuseSamples"]["value"].getValue() )
	if plug["giSpecularSamples"]["enabled"].getValue() :
		info.append( "Specular %d" % plug["giSpecularSamples"]["value"].getValue() )
	if plug["giTransmissionSamples"]["enabled"].getValue() :
		info.append( "Transmission %d" % plug["giTransmissionSamples"]["value"].getValue() )
	if plug["giSSSSamples"]["enabled"].getValue() :
		info.append( "SSS %d" % plug["giSSSSamples"]["value"].getValue() )
	if plug["giVolumeSamples"]["enabled"].getValue() :
		info.append( "Volume %d" % plug["giVolumeSamples"]["value"].getValue() )
	if plug["aaSeed"]["enabled"].getValue() :
		info.append( "Seed {0}".format( plug["aaSeed"]["value"].getValue() ) )
	if plug["aaSampleClamp"]["enabled"].getValue() :
		info.append( "Clamp {0}".format( GafferUI.NumericWidget.valueToString( plug["aaSampleClamp"]["value"].getValue() ) ) )
	if plug["aaSampleClampAffectsAOVs"]["enabled"].getValue() :
		info.append( "Clamp AOVs {0}".format( "On" if plug["aaSampleClampAffectsAOVs"]["value"].getValue() else "Off" ) )
	if plug["indirectSampleClamp"]["enabled"].getValue() :
		info.append( "Indirect Clamp {0}".format( GafferUI.NumericWidget.valueToString( plug["indirectSampleClamp"]["value"].getValue() ) ) )
	if plug["lowLightThreshold"]["enabled"].getValue() :
		info.append( "Low Light {0}".format( GafferUI.NumericWidget.valueToString( plug["lowLightThreshold"]["value"].getValue() ) ) )
	if plug["dielectricPriorities"]["enabled"].getValue() :
		info.append( "Dielectric Priorities {0}".format( GafferUI.NumericWidget.valueToString( plug["dielectricPriorities"]["value"].getValue() ) ) )
	return ", ".join( info )

def __adaptiveSamplingSummary( plug ) :

	info = []
	if plug["enableAdaptiveSampling"]["enabled"].getValue() :
		info.append( "Enable %d" % plug["enableAdaptiveSampling"]["value"].getValue() )
	if plug["aaSamplesMax"]["enabled"].getValue() :
		info.append( "AA Max %d" % plug["aaSamplesMax"]["value"].getValue() )
	if plug["aaAdaptiveThreshold"]["enabled"].getValue() :
		info.append( "Threshold %s" % GafferUI.NumericWidget.valueToString( plug["aaAdaptiveThreshold"]["value"].getValue() ) )
	return ", ".join( info )

def __interactiveRenderingSummary( plug ) :

	info = []
	if plug["enableProgressiveRender"]["enabled"].getValue() :
		info.append( "Progressive %s" % ( "On" if plug["enableProgressiveRender"]["value"].getValue() else "Off" ) )
	if plug["progressiveMinAASamples"]["enabled"].getValue() :
		info.append( "Min AA %d" % plug["progressiveMinAASamples"]["value"].getValue() )
	return ", ".join( info )

def __rayDepthSummary( plug ) :

	info = []
	if plug["giTotalDepth"]["enabled"].getValue() :
		info.append( "Total %d" % plug["giTotalDepth"]["value"].getValue() )
	if plug["giDiffuseDepth"]["enabled"].getValue() :
		info.append( "Diffuse %d" % plug["giDiffuseDepth"]["value"].getValue() )
	if plug["giSpecularDepth"]["enabled"].getValue() :
		info.append( "Specular %d" % plug["giSpecularDepth"]["value"].getValue() )
	if plug["giTransmissionDepth"]["enabled"].getValue() :
		info.append( "Transmission %d" % plug["giTransmissionDepth"]["value"].getValue() )
	if plug["giVolumeDepth"]["enabled"].getValue() :
		info.append( "Volume %d" % plug["giVolumeDepth"]["value"].getValue() )
	if plug["autoTransparencyDepth"]["enabled"].getValue() :
		info.append( "Transparency %d" % plug["autoTransparencyDepth"]["value"].getValue() )
	return ", ".join( info )

def __subdivisionSummary( plug ) :
	info = []
	if plug["maxSubdivisions"]["enabled"].getValue():
		info.append( "Max Subdivisions  %d" % plug["maxSubdivisions"]["value"].getValue() )
	if plug["subdivDicingCamera"]["enabled"].getValue():
		info.append( "Dicing Camera %s" % plug["subdivDicingCamera"]["value"].getValue() )
	if plug["subdivFrustumCulling"]["enabled"].getValue():
		info.append( "Frustum Culling %s" % ( "On" if plug["subdivFrustumCulling"]["value"].getValue() else "Off" ) )
	if plug["subdivFrustumPadding"]["enabled"].getValue():
		info.append( "Frustum Padding %s" % GafferUI.NumericWidget.valueToString( plug["subdivFrustumPadding"]["value"].getValue() ) )
	return ", ".join( info )

def __texturingSummary( plug ) :

	info = []
	if plug["textureMaxMemoryMB"]["enabled"].getValue() :
		info.append( "Memory {0}".format( GafferUI.NumericWidget.valueToString( plug["textureMaxMemoryMB"]["value"].getValue() ) ) )
	if plug["texturePerFileStats"]["enabled"].getValue() :
		info.append( "Per File Stats {0}".format( "On" if plug["texturePerFileStats"]["value"].getValue() else "Off" ) )
	if plug["textureMaxSharpen"]["enabled"].getValue() :
		info.append( "Sharpen {0}".format( GafferUI.NumericWidget.valueToString( plug["textureMaxSharpen"]["value"].getValue() ) ) )
	return ", ".join( info )

def __featuresSummary( plug ) :

	info = []
	for childName, label in (
		( "ignoreTextures", "Textures" ),
		( "ignoreShaders", "Shaders" ),
		( "ignoreAtmosphere", "Atmos" ),
		( "ignoreLights", "Lights" ),
		( "ignoreShadows", "Shadows" ),
		( "ignoreSubdivision", "Subdivs" ),
		( "ignoreDisplacement", "Disp" ),
		( "ignoreBump", "Bump" ),
		( "ignoreSSS", "SSS" ),
	) :
		if plug[childName]["enabled"].getValue() :
			info.append( label + ( " Off " if plug[childName]["value"].getValue() else " On" ) )

	return ", ".join( info )

def __searchPathsSummary( plug ) :

	info = []
	for prefix in ( "texture", "procedural", "plugin" ) :
		if plug[prefix+"SearchPath"]["enabled"].getValue() :
			info.append( prefix.capitalize() )

	return ", ".join( info )

def __errorHandlingSummary( plug ) :

	info = []
	if plug["abortOnError"]["enabled"].getValue() :
		info.append( "Abort on Error " + ( "On" if plug['abortOnError']["value"].getValue() else "Off" ) )
	for suffix in ( "Texture", "Pixel", "Shader" ) :
		if plug["errorColorBad"+suffix]["enabled"].getValue() :
			info.append( suffix )

	return ", ".join( info )

def __loggingSummary( plug ) :

	info = []
	if plug["logFileName"]["enabled"].getValue() :
		info.append( "File name" )
	if plug["logMaxWarnings"]["enabled"].getValue() :
		info.append( "Max Warnings %d" % plug["logMaxWarnings"]["value"].getValue() )

	return ", ".join( info )

def __statisticsSummary( plug ) :

	info = []
	if plug["statisticsFileName"]["enabled"].getValue() :
		info.append( "Stats File: " + plug["statisticsFileName"]["value"].getValue() )
	if plug["profileFileName"]["enabled"].getValue() :
		info.append( "Profile File: " + plug["profileFileName"]["value"].getValue() )

	return ", ".join( info )

def __licensingSummary( plug ) :

	info = []
	for name, label in (
		( "abortOnLicenseFail", "Abort on Fail" ),
		( "skipLicenseCheck", "Skip Check" )
	) :
		if plug[name]["enabled"].getValue() :
			info.append( label + " " + ( "On" if plug[name]["value"].getValue() else "Off" ) )

	return ", ".join( info )

def __gpuSummary( plug ) :

	info = []
	if plug["renderDevice"]["enabled"].getValue() :
		info.append( "Device: %s" %  plug["renderDevice"]["value"].getValue() )

	if plug["gpuMaxTextureResolution"]["enabled"].getValue() :
		info.append( "Max Res: %i" % plug["gpuMaxTextureResolution"]["value"].getValue() )
	return ", ".join( info )

Gaffer.Metadata.registerNode(

	GafferArnold.ArnoldOptions,

	"description",
	"""
	Sets global scene options applicable to the Arnold
	renderer. Use the StandardOptions node to set
	global options applicable to all renderers.
	""",

	plugs = {

		# Sections

		"options" : [

			"layout:section:Rendering:summary", __renderingSummary,
			"layout:section:Sampling:summary", __samplingSummary,
			"layout:section:Adaptive Sampling:summary", __adaptiveSamplingSummary,
			"layout:section:Interactive Rendering:summary", __interactiveRenderingSummary,
			"layout:section:Ray Depth:summary", __rayDepthSummary,
			"layout:section:Subdivision:summary", __subdivisionSummary,
			"layout:section:Texturing:summary", __texturingSummary,
			"layout:section:Features:summary", __featuresSummary,
			"layout:section:Search Paths:summary", __searchPathsSummary,
			"layout:section:Error Handling:summary", __errorHandlingSummary,
			"layout:section:Logging:summary", __loggingSummary,
			"layout:section:Statistics:summary", __statisticsSummary,
			"layout:section:Licensing:summary", __licensingSummary,
			"layout:section:GPU:summary", __gpuSummary,

		],

		# Rendering

		"options.bucketSize": [

			"description",
			"""
			Controls the size of the image buckets.
			The default size is 64x64 pixels.
			Bigger buckets will increase memory usage
			while smaller buckets may render slower as
			they need to perform redundant computations
			and filtering.
			""",

			"layout:section", "Rendering",
			"label", "Bucket Size",

		],

		"options.bucketScanning": [

			"description",
			"""
			Controls the order in which buckets are
			processed. A spiral pattern is the default.
			""",

			"layout:section", "Rendering",
			"label", "Bucket Scanning",

		],

		"options.bucketScanning.value": [

			"plugValueWidget:type", 'GafferUI.PresetsPlugValueWidget',
			"presetNames", IECore.StringVectorData( ["Top", "Left", "Random", "Spiral", "Hilbert"] ),
			"presetValues", IECore.StringVectorData( ["top", "left", "random", "spiral", "hilbert"] ),
		],

		"options.parallelNodeInit" : [

			"description",
			"""
			Enables Arnold's parallel node initialization.
			Note that some Arnold features may not be
			thread-safe, in which case enabling this option
			can cause crashes. One such example is Cryptomatte
			and its use in the AlSurface shader.
			""",

			"layout:section", "Rendering",

		],

		"options.threads" : [

			"description",
			"""
			Specifies the number of threads Arnold
			is allowed to use. A value of 0 gives
			Arnold access to all available threads.
			""",

			"layout:section", "Rendering",

		],

		# Sampling

		"options.aaSamples" : [

			"description",
			"""
			Controls the number of rays per pixel
			traced from the camera. The more samples,
			the better the quality of antialiasing,
			motion blur and depth of field. The actual
			number of rays per pixel is the square of
			the AA samples value - so a value of 3
			means 9 rays are traced, 4 means 16 rays are
			traced and so on.
			""",

			"layout:section", "Sampling",
			"label", "AA Samples",

		],

		"options.giDiffuseSamples" : [

			"description",
			"""
			Controls the number of rays traced when
			computing indirect illumination ("bounce light").
			The number of actual diffuse rays traced is the
			square of this number.
			""",

			"layout:section", "Sampling",
			"label", "Diffuse Samples",

		],

		"options.giSpecularSamples" : [

			"description",
			"""
			Controls the number of rays traced when
			computing specular reflections.
			The number of actual specular rays traced
			is the square of this number.
			""",

			"layout:section", "Sampling",
			"label", "Specular Samples",

		],

		"options.giTransmissionSamples" : [

			"description",
			"""
			Controls the number of rays traced when
			computing specular refractions. The number of actual
			transmitted specular rays traced is the square of this number.
			""",

			"layout:section", "Sampling",
			"label", "Transmission Samples",

		],

		"options.giSSSSamples" : [

			"description",
			"""
			Controls the number of rays traced when
			computing subsurface scattering. The number of actual
			subsurface rays traced is the square of this number.
			""",

			"layout:section", "Sampling",
			"label", "SSS Samples",

		],

		"options.giVolumeSamples" : [

			"description",
			"""
			Controls the number of rays traced when
			computing indirect lighting for volumes.
			The number of actual rays traced
			is the square of this number. The volume
			ray depth must be increased from the default
			value of 0 before this setting is of use.
			""",

			"layout:section", "Sampling",
			"label", "Volume Samples",

		],

		"options.aaSeed" : [

			"description",
			"""
			Seeds the randomness used when generating samples.
			By default this is set to the current frame number
			so that the pattern of sampling noise changes every
			frame. It can be locked to a particular value so
			that sampling noise does not change from frame to
			frame.
			""",

			"layout:section", "Sampling",
			"label", "AA Seed",

		],

		"options.aaSampleClamp" : [

			"description",
			"""
			Sets a maximum for the values of individual pixel samples. This
			can help reduce fireflies.
			""",

			"layout:section", "Sampling",
			"label", "Sample Clamp",

		],

		"options.aaSampleClampAffectsAOVs" : [

			"description",
			"""
			Applies the sample clamping settings to all RGB and RGBA
			AOVs, in addition to the beauty image.
			""",

			"layout:section", "Sampling",
			"label", "Clamp AOVs",

		],

		"options.indirectSampleClamp" : [

			"description",
			"""
			Clamp fireflies resulting from indirect calculations.
			May cause problems with dulling highlights in reflections.
			""",

			"layout:section", "Sampling",
			"label", "Indirect Sample Clamp",

		],

		"options.lowLightThreshold" : [

			"description",
			"""
			Light paths with less energy than this will be discarded.  This
			saves tracing shadow rays, but cuts off the light when it gets dim.
			Raising this improves performance, but makes the image potentially
			darker in some areas.
			""",

			"layout:section", "Sampling",
			"label", "Low Light Threshold",

		],

		"options.dielectricPriorities" : [

			"description",
			"""
			Enable or disable dielectric priorities for surface shaders
			""",

			"layout:section", "Sampling",
			"label", "Dielectric Priorities",
		],

		# Adaptive Sampling

		"options.enableAdaptiveSampling" : [

			"description",
			"""
			If adaptive sampling is enabled, Arnold will take a minimum
			of ( aaSamples * aaSamples ) samples per pixel, and will then
			take up to ( aaSamplesMax * aaSamplesMax ) samples per pixel,
			or until the remaining estimated noise gets lower than
			aaAdaptiveThreshold.

			> Note : Arnold's adaptive sampling won't do anything if aaSamples == 1 : you need to set aaSamples to at least 2.
			""",

			"layout:section", "Adaptive Sampling",
			"label", "Enable Adaptive Sampling",

		],

		"options.aaSamplesMax" : [

			"description",
			"""
			The maximum sampling rate during adaptive sampling.  Like
			aaSamples, this value is squared.  So aaSamplesMax == 6 means up to 36 samples per pixel.
			""",

			"layout:section", "Adaptive Sampling",
			"label", "AA Samples Max",

		],

		"options.aaAdaptiveThreshold" : [

			"description",
			"""
			How much leftover noise is acceptable when terminating adaptive sampling.  Higher values
			accept more noise, lower values keep rendering longer to achieve smaller amounts of
			noise.
			""",

			"layout:section", "Adaptive Sampling",
			"label", "AA Adaptive Threshold",

		],

		# Interactive rendering

		"options.enableProgressiveRender" : [

			"description",
			"""
			Enables progressive rendering, with a series of coarse low-resolution
			renders followed by a full quality render updated continuously.
			""",

			"layout:section", "Interactive Rendering",
			"label", "Progressive",

		],

		"options.progressiveMinAASamples" : [

			"description",
			"""
			Controls the coarseness of the first low resolution pass
			of interactive rendering. A value of `-4` starts with 16x16 pixel
			blocks, `-3` gives 8x8 blocks, `-2` gives 4x4, `-1` gives 2x2 and
			`0` disables the low resolution passes completely.
			""",

			"layout:section", "Interactive Rendering",
			"label", "Min AA Samples",

		],

		# Ray Depth

		"options.giTotalDepth" : [

			"description",
			"""
			The maximum depth of any ray (Diffuse + Specular +
			Transmission + Volume).
			""",

			"layout:section", "Ray Depth",
			"label", "Total Depth",

		],

		"options.giDiffuseDepth" : [

			"description",
			"""
			Controls the number of ray bounces when
			computing indirect illumination ("bounce light").
			""",

			"layout:section", "Ray Depth",
			"label", "Diffuse Depth",

		],

		"options.giSpecularDepth" : [

			"description",
			"""
			Controls the number of ray bounces when
			computing specular reflections.
			""",

			"layout:section", "Ray Depth",
			"label", "Specular Depth",

		],

		"options.giTransmissionDepth" : [

			"description",
			"""
			Controls the number of ray bounces when
			computing specular refractions.
			""",

			"layout:section", "Ray Depth",
			"label", "Transmission Depth",

		],

		"options.giVolumeDepth" : [

			"description",
			"""
			Controls the number of ray bounces when
			computing indirect lighting on volumes.
			""",

			"layout:section", "Ray Depth",
			"label", "Volume Depth",

		],

		"options.autoTransparencyDepth" : [

			"description",
			"""
			The number of allowable transparent layers - after
			this the last object will be treated as opaque.
			""",

			"layout:section", "Ray Depth",
			"label", "Transparency Depth",

		],

		# Subdivision

		"options.maxSubdivisions" : [

			"description",
			"""
			A global override for the maximum polymesh.subdiv_iterations.
			""",

			"layout:section", "Subdivision",
			"label", "Max Subdivisions",
		],

		"options.subdivDicingCamera" : [

			"description",
			"""
			If specified, adaptive subdivision will be performed
			relative to this camera, instead of the render camera.
			""",

			"layout:section", "Subdivision",
			"label", "Subdiv Dicing Camera",
		],

		"options.subdivDicingCamera.value" : [
			"plugValueWidget:type", "GafferSceneUI.ScenePathPlugValueWidget",
			"path:valid", True,
			"scenePathPlugValueWidget:setNames", IECore.StringVectorData( [ "__cameras" ] ),
			"scenePathPlugValueWidget:setsLabel", "Show only cameras",
		],

		"options.subdivFrustumCulling" : [

			"description",
			"""
			Disable subdivision of polygons outside the camera frustum.
			( Uses dicing camera if one has been set ).
			Saves performance, at the cost of inaccurate reflections
			and shadows.
			""",

			"layout:section", "Subdivision",
			"label", "Subdiv Frustum Culling",
		],

		"options.subdivFrustumPadding" : [

			"description",
			"""
			When using subdivFrustumCulling, adds a world space bound
			around the frustum where subdivision still occurs.  Can be
			used to improve shadows, reflections, and objects the motion
			blur into frame.
			""",

			"layout:section", "Subdivision",
			"label", "Subdiv Frustum Padding",
		],

		# Texturing

		"options.textureMaxMemoryMB" : [

			"description",
			"""
			The maximum amount of memory to use for caching
			textures. Tiles are loaded on demand and cached,
			and when the memory limit is reached the least
			recently used tiles are discarded to make room
			for more. Measured in megabytes.
			""",

			"layout:section", "Texturing",
			"label", "Max Memory MB",
		],

		"options.texturePerFileStats" : [

			"description",
			"""
			Turns on detailed statistics output for
			each individual texture file used.
			""",

			"layout:section", "Texturing",
			"label", "Per File Stats",

		],

		"options.textureMaxSharpen" : [

			"description",
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

			"layout:section", "Texturing",
			"label", "Max Sharpen",
		],

		# Features

		"options.ignoreTextures" : [

			"description",
			"""
			Ignores all file textures, rendering as
			if they were all white.
			""",

			"layout:section", "Features",

		],

		"options.ignoreShaders" : [

			"description",
			"""
			Ignores all shaders, rendering as a
			simple facing ratio shader instead.
			""",

			"layout:section", "Features",

		],

		"options.ignoreAtmosphere" : [

			"description",
			"""
			Ignores all atmosphere shaders.
			""",

			"layout:section", "Features",

		],

		"options.ignoreLights" : [

			"description",
			"""
			Ignores all lights.
			""",

			"layout:section", "Features",

		],

		"options.ignoreShadows" : [

			"description",
			"""
			Skips all shadow calculations.
			""",

			"layout:section", "Features",

		],

		"options.ignoreSubdivision" : [

			"description",
			"""
			Treats all subdivision surfaces
			as simple polygon meshes instead.
			""",

			"layout:section", "Features",

		],

		"options.ignoreDisplacement" : [

			"description",
			"""
			Ignores all displacement shaders.
			""",

			"layout:section", "Features",

		],

		"options.ignoreBump" : [

			"description",
			"""
			Ignores all bump mapping.
			""",

			"layout:section", "Features",

		],

		"options.ignoreSSS" : [

			"description",
			"""
			Disables all subsurface scattering.
			""",

			"layout:section", "Features",

		],

		# Search Paths

		"options.textureSearchPath" : [

			"description",
			"""
			The locations used to search for texture
			files.
			""",

			"layout:section", "Search Paths",
			"label", "Textures",

		],

		"options.proceduralSearchPath" : [

			"description",
			"""
			The locations used to search for procedural
			DSOs.
			""",

			"layout:section", "Search Paths",
			"label", "Procedurals",

		],

		"options.pluginSearchPath" : [

			"description",
			"""
			The locations used to search for shaders and other plugins.
			""",

			"layout:section", "Search Paths",
			"label", "Plugins (Shaders)",

		],

		# Error Handling

		"options.abortOnError" : [

			"description",
			"""
			Aborts the render if an error is encountered.
			""",

			"layout:section", "Error Handling"

		],

		"options.errorColorBadTexture" : [

			"description",
			"""
			The colour to display if an attempt is
			made to use a bad or non-existent texture.
			""",

			"layout:section", "Error Handling",
			"label", "Bad Texture",

		],

		"options.errorColorBadPixel" : [

			"description",
			"""
			The colour to display for a pixel where
			a NaN is encountered.
			""",

			"layout:section", "Error Handling",
			"label", "Bad Pixel",

		],

		"options.errorColorBadShader" : [

			"description",
			"""
			The colour to display if a problem occurs
			in a shader.
			""",

			"layout:section", "Error Handling",
			"label", "Bad Shader",

		],

		# Logging

		"options.logFileName" : [

			"description",
			"""
			The name of a log file which Arnold will generate
			while rendering.
			""",

			"layout:section", "Logging",
			"label", "File Name",

		],

		"options.logFileName.value" : [

			"plugValueWidget:type", "GafferUI.FileSystemPathPlugValueWidget",
			"path:leaf", True,
			"fileSystemPath:extensions", "txt log",
			"fileSystemPath:extensionsLabel", "Show only log files",

		],

		"options.logMaxWarnings" : [

			"description",
			"""
			The maximum number of warnings that will be reported.
			""",

			"layout:section", "Logging",
			"label", "Max Warnings",

		],

		# Statistics

		"options.statisticsFileName" : [

			"description",
			"""
			The name of a statistics file where Arnold will store structured
			JSON statistics.
			""",

			"layout:section", "Statistics",
			"label", "Statistics File",

		],

		"options.profileFileName" : [

			"description",
			"""
			The name of a profile json file where Arnold will store a
			detailed node performance graph. Use chrome://tracing to
			view the profile.
			""",

			"layout:section", "Statistics",
			"label", "Profile File",

		],

		# Licensing

		"options.abortOnLicenseFail" : [

			"description",
			"""
			Aborts the render if a license is not available,
			instead of rendering with a watermark.
			""",

			"layout:section", "Licensing",

		],

		"options.skipLicenseCheck" : [

			"description",
			"""
			Skips the check for a license, always rendering
			with a watermark.
			""",

			"layout:section", "Licensing",

		],

		# GPU

		"options.renderDevice" : [

			"description",
			"""
			Can be used to put Arnold in GPU rendering mode, using your graphics card instead of CPU.  This is currently a beta with limited stability, and missing support for OSL and volumes.
			""",

			"layout:section", "GPU",

		],

		"options.renderDevice.value": [

			"plugValueWidget:type", 'GafferUI.PresetsPlugValueWidget',
			"presetNames", IECore.StringVectorData( ["CPU", "GPU"] ),
			"presetValues", IECore.StringVectorData( ["CPU", "GPU"] ),
		],

		"options.gpuMaxTextureResolution" : [

			"description",
			"""
			If non-zero, this will omit the high resolution mipmaps when in GPU mode, to avoid running out of GPU memory.
			""",

			"layout:section", "GPU",
			"label", "Max Texture Resolution",

		],

	}

)

for plugPrefix in ( "log", "console" ) :

	for plugSuffix, description in (
		( "Info", "information messages" ),
		( "Warnings", "warning messages" ),
		( "Errors", "error messages" ),
		( "Debug", "debug messages" ),
		( "AssParse", "ass parsing" ),
		( "Plugins", "plugin loading" ),
		( "Progress", "progress messages" ),
		( "NAN", "pixels with NaNs" ),
		( "Timestamp", "timestamp prefixes" ),
		( "Stats", "statistics" ),
		( "Backtrace", "stack backtraces from crashes" ),
		( "Memory", "memory usage prefixes" ),
		( "Color", "coloured messages" ),
	) :

		Gaffer.Metadata.registerNode(

			GafferArnold.ArnoldOptions,

			plugs = {

				"options." + plugPrefix + plugSuffix : [

					"description",
					"""
					Whether or not {0} {1} included in the {2} output.
					""".format( description, "are" if description.endswith( "s" ) else "is", plugPrefix ),

					"label", plugSuffix,
					"layout:section", "Logging." + ( "Console " if plugPrefix == "console" else "" ) + "Verbosity",

				],

			}

		)
