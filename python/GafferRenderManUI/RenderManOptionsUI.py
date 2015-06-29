##########################################################################
#
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
import GafferRenderMan

def __qualitySummary( plug ) :

	info = []

	if plug["pixelSamples"]["enabled"].getValue() :
		ps = plug["pixelSamples"]["value"].getValue()
		info.append( "Pixel Samples %dx%d" % ( ps[0], ps[1] ) )

	return ", ".join( info )

def __hiderSummary( plug ) :

	info = []

	if plug["hider"]["enabled"].getValue() :
		info.append( plug["hider"]["value"].getValue().capitalize() )
	if plug["hiderDepthFilter"]["enabled"].getValue() :
		info.append( "Depth Filter : " + plug["hiderDepthFilter"]["value"].getValue().capitalize() )
	if plug["hiderJitter"]["enabled"].getValue() :
		info.append( "Jitter " + ( "On" if plug["hiderJitter"]["value"].getValue() else "Off" ) )
	if plug["hiderSampleMotion"]["enabled"].getValue() :
		info.append( "Sample Motion " + ( "On" if plug["hiderSampleMotion"]["value"].getValue() else "Off" ) )
	if plug["hiderExtremeMotionDOF"]["enabled"].getValue() :
		info.append( "Extreme MDOF " + ( "On" if plug["hiderExtremeMotionDOF"]["value"].getValue() else "Off" ) )
	if plug["hiderProgressive"]["enabled"].getValue() :
		info.append( "Progressive " + ( "On" if plug["hiderProgressive"]["value"].getValue() else "Off" ) )

	return ", ".join( info )

def __statisticsSummary( plug ) :

	info = []
	if plug["statisticsLevel"]["enabled"].getValue() :
		info.append( "Level %d" % plug["statisticsLevel"]["value"].getValue() )
	if plug["statisticsFileName"]["enabled"].getValue() :
		info.append( "File name" )
	if plug["statisticsProgress"]["enabled"].getValue() :
		info.append( "Progress " + ( "On" if plug["statisticsProgress"]["value"].getValue() else "Off" ) )

	return ", ".join( info )

def __searchPathsSummary( plug ) :

	info = []

	for childName, label in (
		( "shaderSearchPath", "Shaders" ),
		( "textureSearchPath", "Textures" ),
		( "displaySearchPath", "Displays" ),
		( "archiveSearchPath", "Archives" ),
		( "proceduralSearchPath", "Procedurals" ),
	) :
		if plug[childName]["enabled"].getValue() :
			info.append( label )

	return ", ".join( info )

Gaffer.Metadata.registerNode(

	GafferRenderMan.RenderManOptions,

	"description",
	"""
	Sets global scene options applicable to RenderMan
	renderers. Use the StandardOptions node to set
	global options applicable to all renderers.
	""",

	plugs = {

		# Summaries

		"options" : [

			"layout:section:Quality:summary", __qualitySummary,
			"layout:section:Hider:summary", __hiderSummary,
			"layout:section:Statistics:summary", __statisticsSummary,
			"layout:section:Search Paths:summary", __searchPathsSummary,

		],

		# Quality

		"options.pixelSamples" : [

			"description",
			"""
			The number of primary samples to divide each pixel into
			in the X and Y directions. For example, 3x3 gives a total of
			9 samples per pixel. This is the primary quality control for
			geometric antialiasing and motion blur.
			""",

			"layout:section", "Quality",

		],

		# Hider

		"options.hider" : [

			"description",
			"""
			The "Hidden" hider means the classic REYES algorithm
			is used, and the "Raytrace" hider means a more modern
			raytraced algorithm is used.
			""",

			"layout:section", "Hider",

		],

		"options.hider.value" : [

			"preset:Hidden", "hidden",
			"preset:Raytrace", "raytrace",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"options.hiderDepthFilter" : [

			"description",
			"""
			The filter used to compute a single depth
			value per pixel from the depths in each
			pixel sample.
			""",

			"layout:section", "Hider",
			"label", "Depth Filter",

		],

		"options.hiderDepthFilter.value" : [

			"preset:Min", "min",
			"preset:Max", "max",
			"preset:Average", "average",
			"preset:Midpoint", "midpoint",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"options.hiderJitter" : [

			"description",
			"""
			Whether or not each pixel sample is
			jittered about the centre of its subpixel
			position, or if they're aligned in a
			regular grid. If in doubt, leave this on.
			""",

			"layout:section", "Hider",
			"label", "Jitter",

		],

		"options.hiderSampleMotion" : [

			"description",
			"""
			May be turned off to disable the sampling of
			motion blur, but keep motion vectors available
			for use in shaders. This is useful for
			rendering a motion vector pass to allow
			2D motion blur to be applied as a post process.
			If you simply wish to turn off motion blur
			entirely, then use the motion blur settings
			in the StandardOptions node.
			""",


			"layout:section", "Hider",
			"label", "Sample Motion",

		],

		"options.hiderExtremeMotionDOF" : [

			"description",
			"""
			An alternative sampling algorithm which
			is more expensive, but gives higher quality
			results when objects are both moving quickly
			and are out of focus.
			""",

			"layout:section", "Hider",
			"label", "Extreme Motion DOF",

		],

		"options.hiderProgressive" : [

			"description",
			"""
			Renders at progressively increasing levels
			of quality, to give quick low quality feedback
			at the start of an interactive render. Only
			applies when the raytrace hider is used.
			""",

			"layout:section", "Hider",
			"label", "Progressive",

		],

		# Statistics

		"options.statisticsLevel" : [

			"description",
			"""
			Determines the verbosity of statistics
			output.
			""",

			"layout:section", "Statistics",
			"label", "Level",

		],

		"options.statisticsLevel.value" : [

			"preset:0 (Off)", 0,
			"preset:1", 1,
			"preset:2", 2,
			"preset:3 (Most Verbose)", 3,

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"options.statisticsFileName" : [

			"description",
			"""
			The name of a file where the statistics
			will be written.
			""",

			"layout:section", "Statistics",
			"label", "File Name",

		],

		"options.statisticsFileName.value" : [

			"plugValueWidget:type", "GafferUI.FileSystemPathPlugValueWidget",
			"pathPlugValueWidget:leaf", True,
			"pathPlugValueWidget:bookmarks", "statistics",
			"fileSystemPathPlugValueWidget:extensions", IECore.StringVectorData( [ "htm", "html", "txt", "stats" ] ),

		],

		"options.statisticsProgress" : [

			"description",
			"""
			Turning this on causes a render progress
			percentage to be printed out continuously
			during rendering.
			""",

			"layout:section", "Statistics",
			"label", "Progress",

		],

		# Search Paths

		"options.shaderSearchPath" : [

			"description",
			"""
			The filesystem paths where shaders are
			searched for. Paths should be separated
			by ':'.
			""",

			"layout:section", "Search Paths",
			"label", "Shaders",

		],

		"options.textureSearchPath" : [

			"description",
			"""
			The filesystem paths where shaders are
			located. Paths should be separated
			by ':'.
			""",

			"layout:section", "Search Paths",
			"label", "Textures",

		],

		"options.displaySearchPath" : [

			"description",
			"""
			The filesystem paths where display driver
			plugins are located. These will be used when searching
			for drivers specified using the Outputs
			node. Paths should be separated by ':'.
			""",

			"layout:section", "Search Paths",
			"label", "Displays",

		],

		"options.archiveSearchPath" : [

			"description",
			"""
			The filesystem paths where RIB archives
			are located. These will be used when searching
			for archives specified using the ExternalProcedural
			node. Paths should be separated by ':'.
			""",

			"layout:section", "Search Paths",
			"label", "Archives",

		],

		"options.proceduralSearchPath" : [

			"description",
			"""
			The filesystem paths where DSO procedurals
			are located. These will be used when searching
			for procedurals specified using the ExternalProcedural
			node. Paths should be separated by ':'.
			""",

			"layout:section", "Search Paths",
			"label", "Procedurals",

		],

	}

)
