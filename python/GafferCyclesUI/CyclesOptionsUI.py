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
import GafferCycles

def __renderingSummary( plug ) :

	info = []

	if plug["numThreads"]["enabled"].getValue() :
		info.append( "Threads {}".format( plug["numThreads"]["value"].getValue() ) )

	if plug["tileOrder"]["enabled"].getValue() :
		info.append(
			"Order {}".format( Gaffer.NodeAlgo.currentPreset( plug["tileOrder"]["value"] ) )
		)

	return ", ".join( info )

def __samplingSummary( plug ) :

	info = []

	if plug["samples"]["enabled"].getValue() :
		info.append( "Samples {}".format( plug["samples"]["value"].getValue() ) )

	for sampleType in ( "Diffuse", "Glossy", "Transmission", "AO", "MeshLight", "Subsurface", "Volume" ) :
		childName = "%sSamples" % sampleType.lower()
		if plug[childName]["enabled"].getValue() :
			info.append(
				"{} {}".format( sampleType, plug[childName]["value"].getValue() )
			)

	return ", ".join( info )

def __rayDepthSummary( plug ) :

	info = []

	if plug["maxBounces"]["enabled"].getValue() :
		info.append( "Max Bounces {}".format( plug["maxBounces"]["value"].getValue() ) )

	for rayType in ( "Diffuse", "Glossy", "Transmission", "Volume" ) :
		childName = "max%sBounce" + rayType
		if plug[childName]["enabled"].getValue() :
			info.append(
				"{} {}".format( rayType, plug[childName]["value"].getValue() )
			)

	if plug["transparentMaxBounce"]["enabled"].getValue() :
		info.append( "Transparency {}".format( plug["transparentMaxBounce"]["value"].getValue() ) )

	return ", ".join( info )

def __texturingSummary( plug ) :

	info = []

	if plug["textureLimit"]["enabled"].getValue() :
		info.append( "Texture Limit - {}".format( plug["textureLimit"]["value"].getValue() ) )

	return ", ".join( info )

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

			"layout:section:Rendering:summary", __renderingSummary,
			"layout:section:Sampling:summary", __samplingSummary,
			"layout:section:Ray Depth:summary", __rayDepthSummary,
			"layout:section:Texturing:summary", __texturingSummary,

		],

		# Rendering

		"options.device" : [

			"description",
			"""
			Device to use for rendering.
			""",

			"layout:section", "Rendering",

		],

		"options.device.value" : [

			"preset:CPU", "CPU",
			"preset:GPU", "GPU",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"options.featureSet" : [

			"description",
			"""
			Feature set to use for rendering.
			- Supported : Only use finished and supported features
			- Experimental : Use experimental and incomplete features
			                 that might be broken or change in the 
							 future.
			""",

			"layout:section", "Rendering",

		],

		"options.featureSet.value" : [

			"preset:Supported", "supported",
			"preset:Experimental", "experimental",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"options.shadingSystem" : [

			"description",
			"""
			Shading system.

			- OSL : Use Open Shading Language (CPU rendering only).
			- SVM : Use Shader Virtual Machine.
			""",

			"layout:section", "Rendering",

		],

		"options.shadingSystem.value" : [

			"preset:OSL", "OSL",
			"preset:SVM", "SVM",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"options.integrator" : [

			"description",
			"""
			Method to sample lights and materials.

			- Branched Path : Path tracing integrator that branches on
			  the first bounce, giving more control over the number of
			  light and material samples.
			- Path Tracing : Pure path tracing integrator.
			""",

			"layout:section", "Rendering",

		],

		"options.integrator.value" : [

			"preset:BranchedPath", "branchedPath",
			"preset:Path", "path",

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

			"layout:section", "Rendering",

		],

		"options.tileOrder" : [

			"description",
			"""
			Tile order for rendering.
			""",

			"layout:section", "Rendering",

		],

		"options.tileOrder.value" : [

			"preset:Center", "center",
			"preset:Right to Left", "rightToLeft",
			"preset:Left to Right", "leftToRight",
			"preset:Top to Bottom", "topToBottom",
			"preset:Bottom to Top", "bottomToTop",
			"preset:Hilbert Spiral", "hilbertSpiral",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		# Sampling

		"options.samples" : [

			"description",
			"""
			Number of samples to render for each pixel.
			""",

			"layout:section", "Sampling",
			"label", "Samples",

		],

		"options.aaSamples" : [

			"description",
			"""
			The number of antialiasing samples to render for 
			each pixel.
			""",

			"layout:section", "Sampling",
			"label", "AntiAlias",

		],

		"options.diffuseSamples" : [

			"description",
			"""
			Number of diffuse bounce samples to render for each 
			AA sample.
			""",

			"layout:section", "Sampling",
			"label", "Diffuse",

		],

		"options.glossySamples" : [

			"description",
			"""
			Number of glossy bounce samples to render for each 
			AA sample.
			""",

			"layout:section", "Sampling",
			"label", "Glossy",

		],

		"options.transmissionSamples" : [

			"description",
			"""
			Number of transmission bounce samples to render for 
			each AA sample.
			""",

			"layout:section", "Sampling",
			"label", "Transmission",

		],

		"options.aoSamples" : [

			"description",
			"""
			Number of ambient occlusion bounce samples to render
			for each AA sample.
			""",

			"layout:section", "Sampling",
			"label", "Ambient Occlusion",

		],

		"options.meshlightSamples" : [

			"description",
			"""
			Number of mesh emission light bounce samples to render
			for each AA sample.
			""",

			"layout:section", "Sampling",
			"label", "Meshlight",

		],

		"options.subsurfaceSamples" : [

			"description",
			"""
			Number of subsurface scattering samples to render for each 
			AA sample.
			""",

			"layout:section", "Sampling",
			"label", "Subsurface",

		],

		"options.volumeSamples" : [

			"description",
			"""
			Number of volume scattering samples to render for each AA sample.
			""",

			"layout:section", "Sampling",

		],

		"options.samplingPattern" : [

			"description",
			"""
			Random sampling pattern used by the integrator.
			""",

			"layout:section", "Sampling",

		],

		"options.samplingPattern.value" : [

			"preset:Sobol", "sobol",
			"preset:Correlated Multi Jitter", "correlatedMultiJitter",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		# Ray Depth

		"options.maxBounces" : [

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

		"options.transparentMaxBounce" : [

			"description",
			"""
			Maximum number of transparent bounces.
			""",

			"layout:section", "Ray Depth",
			"label", "Transparency",

		],

		# Texturing

		"options.textureLimit" : [

			"description",
			"""
			Limit the maximum texture size used by final rendering.
			""",

			"layout:section", "Texturing",
			"label", "Size Limit",

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


	}

)
