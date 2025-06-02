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

	# Rendering

	"option:dl:bucketorder" : [

		"defaultValue", "horizontal",
		"description",
		"""
		The order that the buckets (image tiles) are rendered in.
		""",
		"label", "Bucket Order",
		"layout:section", "Rendering",

		"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
		"presetNames", IECore.StringVectorData( [ "Horizontal", "Vertical", "ZigZag", "Spiral", "Circle" ] ),
		"presetValues", IECore.StringVectorData( [ "horizontal", "vertical", "zigzag", "spiral", "circle" ] ),

	],

	"option:dl:numberofthreads" : [

		"defaultValue", 0,
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
		"label", "Number Of Threads",
		"layout:section", "Rendering",

	],

	"option:dl:renderatlowpriority" : [

		"defaultValue", False,
		"description",
		"""
		Causes 3Delight to render at a lower thread priority. This
		can make other applications running at the same time more
		responsive.
		""",
		"label", "Render At Low Priority",
		"layout:section", "Rendering",

	],

	# Quality

	"option:dl:oversampling" : [

		"defaultValue", 4,
		"description",
		"""
		The number of camera rays to fire for each pixel of
		the image. Higher values may be needed to resolve fine
		geometric detail such as hair, or to reduce noise in
		heavily motion blurred renders.
		""",
		"label", "Oversampling",
		"layout:section", "Quality",

	],

	"option:dl:quality.shadingsamples" : [

		"defaultValue", 1,
		"description",
		"""
		The number of samples to take when evaluating shading.
		This is the primary means of improving image quality and
		reducing shading noise.
		""",
		"label", "Shading Samples",
		"layout:section", "Quality",

	],

	"option:dl:quality.volumesamples" : [

		"defaultValue", 1,
		"description",
		"""
		The number of samples to take when evaluating volumes.
		""",
		"label", "Volume Samples",
		"layout:section", "Quality",

	],

	"option:dl:clampindirect" : [

		"defaultValue", 2.0,
		"description",
		"""
		The maximum value to clamp indirect light rays to.
		""",
		"label", "Clamp Indirect",
		"layout:section", "Quality",

	],

	"option:dl:importancesamplefilter" : [

		"defaultValue", False,
		"description",
		"""
		Use filter importance sampling (on) or splatting (off)
		for sample filtering.
		""",
		"label", "Importance Sample Filter",
		"layout:section", "Quality",

	],

	# Features

	"option:dl:show.displacement" : [

		"defaultValue", True,
		"description",
		"""
		Enables or disables displacement in the entire scene.
		""",
		"label", "Show Displacement",
		"layout:section", "Features",

	],

	"option:dl:show.osl.subsurface" : [

		"defaultValue", True,
		"description",
		"""
		Enables or disables subsurface shading in the entire scene.
		""",
		"label", "Show Subsurface",
		"layout:section", "Features",

	],

	"option:dl:show.atmosphere" : [

		"defaultValue", True,
		"description",
		"""
		Enables or disables atmosphere shading in the entire scene.
		""",
		"label", "Show Atmosphere",
		"layout:section", "Features",

	],

	"option:dl:show.multiplescattering" : [

		"defaultValue", True,
		"description",
		"""
		Enables or disables multiple scattering shading in the entire scene.
		""",
		"label", "Show Multiple Scattering",
		"layout:section", "Features",

	],

	# Statistics

	"option:dl:statistics.progress" : [

		"defaultValue", False,
		"description",
		"""
		Causes the percentage of pixels rendered to be output
		during rendering.
		""",
		"label", "Show Progress",
		"layout:section", "Statistics",

	],

	"option:dl:statistics.filename" : [

		"defaultValue", "",
		"description",
		"""
		The path to the file where render statistics will be written.
		Using an empty value will output statistics to the terminal.
		A value of \"null\" will disable statistics output.
		""",
		"label", "Statistics File Name",
		"layout:section", "Statistics",

		"plugValueWidget:type", "GafferUI.FileSystemPathPlugValueWidget",
		"path:leaf", True,

	],

	# Ray Depth

	"option:dl:maximumraydepth.diffuse" : [

		"defaultValue", 1,
		"description",
		"""
		The maximum bounce depth a diffuse ray can reach. A depth
		of 1 specifies one additional bounce compared to purely
		local illumination.
		""",
		"label", "Diffuse",
		"layout:section", "Ray Depth",

	],

	"option:dl:maximumraydepth.hair" : [

		"defaultValue", 4,
		"description",
		"""
		The maximum bounce depth a hair ray can reach. Note that hair
		is akin to volumetric primitives and might need elevated ray
		depth to properly capture the illumination.
		""",
		"label", "Hair",
		"layout:section", "Ray Depth",

	],

	"option:dl:maximumraydepth.reflection" : [

		"defaultValue", 1,
		"description",
		"""
		The maximum bounce depth a reflection ray can reach. Setting
		the reflection depth to 0 will only compute local illumination
		meaning that only emissive surfaces will appear in the reflections.
		""",
		"label", "Reflection",
		"layout:section", "Ray Depth",

	],

	"option:dl:maximumraydepth.refraction" : [

		"defaultValue", 4,
		"description",
		"""
		The maximum bounce depth a refraction ray can reach. A value of 4
		allows light to shine through a properly modeled object such as a
		glass.
		""",
		"label", "Refraction",
		"layout:section", "Ray Depth",

	],

	"option:dl:maximumraydepth.volume" : [

		"defaultValue", 0,
		"description",
		"""
		The maximum bounce depth a volume ray can reach.
		""",
		"label", "Volume",
		"layout:section", "Ray Depth",

	],

	# Ray Length

	"option:dl:maximumraylength.diffuse" : [

		"defaultValue", -1.0,
		"description",
		"""
		The maximum distance a ray emitted from a diffuse material
		can travel. Using a relatively low value may improve performance
		without significant image effects by limiting the effect of global
		illumination. Setting it to a negative value disables the limit.
		""",
		"label", "Diffuse",
		"layout:section", "Ray Length",

	],

	"option:dl:maximumraylength.hair" : [

		"defaultValue", -1.0,
		"description",
		"""
		The maximum distance a ray emitted from a hair shader can travel.
		Setting it to a negative value disables the limit.
		""",
		"label", "Hair",
		"layout:section", "Ray Length",

	],

	"option:dl:maximumraylength.reflection" : [

		"defaultValue", -1.0,
		"description",
		"""
		The maximum distance a reflection ray can travel.
		Setting it to a negative value disables the limit.
		""",
		"label", "Reflection",
		"layout:section", "Ray Length",

	],

	"option:dl:maximumraylength.refraction" : [

		"defaultValue", -1.0,
		"description",
		"""
		The maximum distance a refraction ray can travel.
		Setting it to a negative value disables the limit.
		""",
		"label", "Refraction",
		"layout:section", "Ray Length",

	],

	"option:dl:maximumraylength.specular" : [

		"defaultValue", -1.0,
		"description",
		"""
		The maximum distance a specular ray can travel.
		Setting it to a negative value disables the limit.
		""",
		"label", "Specular",
		"layout:section", "Ray Length",

	],

	"option:dl:maximumraylength.volume" : [

		"defaultValue", -1.0,
		"description",
		"""
		The maximum distance a volume ray can travel.
		Setting it to a negative value disables the limit.
		""",
		"label", "Volume",
		"layout:section", "Ray Length",

	],

	# Texturing

	"option:dl:texturememory" : [

		"defaultValue", 250,
		"description",
		"""
		The amount of RAM allocated to caching textures. Specified
		in megabytes.
		""",
		"label", "Memory",
		"layout:section", "Texturing",

	],

	# Network cache

	"option:dl:networkcache.size" : [

		"defaultValue", 15,
		"description",
		"""
		The amount of disk spaced used to cache network files on
		local storage. Specified in gigabytes.
		""",
		"label", "Size",
		"layout:section", "Network Cache",

	],

	"option:dl:networkcache.directory" : [

		"defaultValue", "",
		"description",
		"""
		The local directory used for caching network files.
		""",
		"label", "Directory",
		"layout:section", "Network Cache",

		"plugValueWidget:type", "GafferUI.FileSystemPathPlugValueWidget",
		"path:leaf", False,

	],

	# Licensing

	"option:dl:license.server" : [

		"defaultValue", "",
		"description",
		"""
		The hostname or IP address of the 3Delight license server.
		""",
		"label", "Server",
		"layout:section", "Licensing",

	],

	"option:dl:license.wait" : [

		"defaultValue", True,
		"description",
		"""
		Causes 3Delight to wait for a license to become available.
		When off, 3Delight will exit immediately if no license is
		available.
		""",
		"label", "Wait",
		"layout:section", "Licensing",

	],

} )
