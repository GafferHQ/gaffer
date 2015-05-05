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

			"layout:section", "Quality",

		],

		# Hider

		"options.hider" : [

			"layout:section", "Hider",

		],

		"options.hider.value" : [

			"preset:Hidden", "hidden",
			"preset:Raytrace", "raytrace",

		],

		"options.hiderDepthFilter" : [

			"layout:section", "Hider",
			"label", "Depth Filter",

		],

		"options.hiderDepthFilter.value" : [

			"preset:Min", "min",
			"preset:Max", "max",
			"preset:Average", "average",
			"preset:Midpoint", "midpoint",

		],

		"options.hiderJitter" : [

			"layout:section", "Hider",
			"label", "Jitter",

		],

		"options.hiderSampleMotion" : [

			"layout:section", "Hider",
			"label", "Sample Motion",

		],

		"options.hiderExtremeMotionDOF" : [

			"layout:section", "Hider",
			"label", "Extreme Motion DOF",

		],

		"options.hiderProgressive" : [

			"layout:section", "Hider",
			"label", "Progressive",

		],

		# Statistics

		"options.statisticsLevel" : [

			"layout:section", "Statistics",
			"label", "Level",

		],

		"options.statisticsLevel.value" : [

			"preset:0 (Off)", 0,
			"preset:1", 1,
			"preset:2", 2,
			"preset:3 (Most Verbose)", 3,

		],

		"options.statisticsFileName" : [

			"layout:section", "Statistics",
			"label", "File Name",

		],

		"options.statisticsProgress" : [

			"layout:section", "Statistics",
			"label", "Progress",

		],

		# Search Paths

		"options.shaderSearchPath" : [

			"layout:section", "Search Paths",
			"label", "Shaders",

		],

		"options.textureSearchPath" : [

			"layout:section", "Search Paths",
			"label", "Textures",

		],

		"options.displaySearchPath" : [

			"layout:section", "Search Paths",
			"label", "Displays",

		],

		"options.archiveSearchPath" : [

			"layout:section", "Search Paths",
			"label", "Archives",

		],

		"options.proceduralSearchPath" : [

			"layout:section", "Search Paths",
			"label", "Procedurals",

		],

	}

)

GafferUI.PlugValueWidget.registerCreator(
	GafferRenderMan.RenderManOptions,
	"options.hider.value",
	GafferUI.PresetsPlugValueWidget,
)

GafferUI.PlugValueWidget.registerCreator(
	GafferRenderMan.RenderManOptions,
	"options.hiderDepthFilter.value",
	GafferUI.PresetsPlugValueWidget,
)

GafferUI.PlugValueWidget.registerCreator(
	GafferRenderMan.RenderManOptions,
	"options.statisticsLevel.value",
	GafferUI.PresetsPlugValueWidget,
)

GafferUI.PlugValueWidget.registerCreator(
	GafferRenderMan.RenderManOptions,
	"options.statisticsFileName.value",
	lambda plug : GafferUI.PathPlugValueWidget( plug,
		path = Gaffer.FileSystemPath( "/", filter = Gaffer.FileSystemPath.createStandardFilter( extensions = ( "htm", "html", "txt", "stats" ) ) ),
		pathChooserDialogueKeywords = {
			"bookmarks" : GafferUI.Bookmarks.acquire( plug, category = "statistics" ),
			"leaf" : True,
		},
	)
)
