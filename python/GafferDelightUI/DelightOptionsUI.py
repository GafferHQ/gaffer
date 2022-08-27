##########################################################################
#
#  Copyright (c) 2017, John Haddon. All rights reserved.
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
import GafferDelight

def __renderingSummary( plug ) :

	info = []

	if plug["numberOfThreads"]["enabled"].getValue() :
		info.append( "Threads {}".format( plug["numberOfThreads"]["value"].getValue() ) )

	if plug["bucketOrder"]["enabled"].getValue() :
		info.append(
			"Order {}".format( Gaffer.NodeAlgo.currentPreset( plug["bucketOrder"]["value"] ) )
		)

	return ", ".join( info )

def __qualitySummary( plug ) :

	info = []

	if plug["oversampling"]["enabled"].getValue() :
		info.append( "Oversampling {}".format( plug["oversampling"]["value"].getValue() ) )

	if plug["shadingSamples"]["enabled"].getValue() :
		info.append( "Shading Samples {}".format( plug["shadingSamples"]["value"].getValue() ) )

	return ", ".join( info )

def __rayDepthSummary( plug ) :

	info = []

	for rayType in ( "Diffuse", "Hair", "Reflection", "Refraction" ) :
		childName = "maximumRayDepth" + rayType
		if plug[childName]["enabled"].getValue() :
			info.append(
				"{} {}".format( rayType, plug[childName]["value"].getValue() )
			)

	return ", ".join( info )

def __texturingSummary( plug ) :

	info = []

	if plug["textureMemory"]["enabled"].getValue() :
		info.append( "Memory {} Mb".format( plug["textureMemory"]["value"].getValue() ) )

	return ", ".join( info )

def __networkCacheSummary( plug ) :

	info = []

	if plug["networkCacheSize"]["enabled"].getValue() :
		info.append( "Size {} gb".format( plug["networkCacheSize"]["value"].getValue() ) )

	return ", ".join( info )

def __licensingSummary( plug ) :

	info = []

	if plug["licenseServer"]["enabled"].getValue() :
		info.append( "Server {}".format( plug["licenseServer"]["value"].getValue() ) )
	if plug["licenseWait"]["enabled"].getValue() :
		info.append( "Wait {}".format( "On" if plug["licenseWait"]["value"].getValue() else "Off" ) )

	return ", ".join( info )

Gaffer.Metadata.registerNode(

	GafferDelight.DelightOptions,

	"description",
	"""
	Sets global scene options applicable to the 3Delight
	renderer. Use the StandardOptions node to set
	global options applicable to all renderers.
	""",

	plugs = {

		# Sections

		"options" : [

			"layout:section:Rendering:summary", __renderingSummary,
			"layout:section:Quality:summary", __qualitySummary,
			"layout:section:Ray Depth:summary", __rayDepthSummary,
			"layout:section:Texturing:summary", __texturingSummary,
			"layout:section:Network Cache:summary", __networkCacheSummary,
			"layout:section:Licensing:summary", __licensingSummary,

		],

		# Rendering

		"options.bucketOrder" : [

			"description",
			"""
			The order that the buckets (image tiles) are rendered in.
			""",

			"layout:section", "Rendering",

		],

		"options.bucketOrder.value" : [

			"preset:Horizontal", "horizontal",
			"preset:Vertical", "vertical",
			"preset:ZigZag", "zigzag",
			"preset:Spiral", "spiral",
			"preset:Circle", "circle",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"options.numberOfThreads" : [

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

		# Quality

		"options.oversampling" : [

			"description",
			"""
			The number of camera rays to fire for each pixel of
			the image. Higher values may be needed to resolve fine
			geometric detail such as hair, or to reduce noise in
			heavily motion blurred renders.
			""",

			"layout:section", "Quality",

		],

		"options.shadingSamples" : [

			"description",
			"""
			The number of samples to take when evaluating shading.
			This is the primary means of improving image quality and
			reducing shading noise.
			""",

			"layout:section", "Quality",

		],

		# Ray Depth

		"options.maximumRayDepthDiffuse" : [

			"description",
			"""
			The maximum bounce depth a diffuse ray can reach. A depth
			of 1 specifies one additional bounce compared to purely
			local illumination.
			""",

			"layout:section", "Ray Depth",
			"label", "Diffuse",

		],

		"options.maximumRayDepthHair" : [

			"description",
			"""
			The maximum bounce depth a hair ray can reach. Note that hair
			is akin to volumetric primitives and might need elevated ray
			depth to properly capture the illumination.
			""",

			"layout:section", "Ray Depth",
			"label", "Hair",

		],

		"options.maximumRayDepthReflection" : [

			"description",
			"""
			The maximum bounce depth a reflection ray can reach. Setting
			the reflection depth to 0 will only compute local illumination
			meaning that only emissive surfaces will appear in the reflections.
			""",

			"layout:section", "Ray Depth",
			"label", "Reflection",

		],

		"options.maximumRayDepthRefraction" : [

			"description",
			"""
			The maximum bounce depth a refraction ray can reach. A value of 4
			allows light to shine through a properly modeled object such as a
			glass.
			""",

			"layout:section", "Ray Depth",
			"label", "Refraction",

		],

		# Texturing

		"options.textureMemory" : [

			"description",
			"""
			The amount of RAM allocated to caching textures. Specified
			in megabytes.
			""",

			"layout:section", "Texturing",
			"label", "Memory",

		],

		# Network cache

		"options.networkCacheSize" : [

			"description",
			"""
			The amount of disk spaced used to cache network files on
			local storage. Specified in gigabytes.
			""",

			"layout:section", "Network Cache",
			"label", "Size",

		],

		"options.networkCacheDirectory" : [

			"description",
			"""
			The local directory used for caching network files.
			""",

			"layout:section", "Network Cache",
			"label", "Directory",

		],

		"options.networkCacheDirectory.value" : [

			"path:leaf", False,

		],

		# Licensing

		"options.licenseServer" : [

			"description",
			"""
			The hostname or IP address of the 3Delight license server.
			""",

			"layout:section", "Licensing",
			"label", "Server",

		],

		"options.licenseWait" : [

			"description",
			"""
			Causes 3Delight to wait for a license to become available.
			When off, 3Delight will exit immediately if no license is
			available.
			""",

			"layout:section", "Licensing",
			"label", "Wait",

		],


	}

)
