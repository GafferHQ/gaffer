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

import Gaffer
import GafferDelight

def __renderingSummary( plug ) :

	info = []

	if plug["dl:numberofthreads"]["enabled"].getValue() :
		info.append( "Threads {}".format( plug["dl:numberofthreads"]["value"].getValue() ) )

	if plug["dl:bucketorder"]["enabled"].getValue() :
		info.append(
			"Order {}".format( Gaffer.NodeAlgo.currentPreset( plug["dl:bucketorder"]["value"] ) )
		)

	if plug["dl:renderatlowpriority"]["enabled"].getValue() :
		info.append( "Low Priority {}".format( "On" if plug["dl:renderatlowpriority"]["value"].getValue() else "Off" ) )

	return ", ".join( info )

def __qualitySummary( plug ) :

	info = []

	if plug["dl:oversampling"]["enabled"].getValue() :
		info.append( "Oversampling {}".format( plug["dl:oversampling"]["value"].getValue() ) )

	for samples in ( "shading", "volume" ) :
		childName = "dl:quality_" + samples + "samples"
		if plug[childName]["enabled"].getValue() :
			info.append( "{} Samples {}".format( samples.capitalize(), plug[childName]["value"].getValue() ) )

	if plug["dl:clampindirect"]["enabled"].getValue() :
		info.append( "Clamp Indirect {}".format( plug["dl:clampindirect"]["value"].getValue() ) )

	if plug["dl:importancesamplefilter"]["enabled"].getValue() :
		info.append( "Importance Sample Filter {}".format( "On" if plug["dl:importancesamplefilter"]["value"].getValue() else "Off" ) )

	return ", ".join( info )

def __featuresSummary( plug ) :

	info = []

	for label, name in ( ( "Displacement", "displacement" ), ( "Subsurface", "osl_subsurface" ) ) :
		childName = "dl:show_" + name
		if plug[childName]["enabled"].getValue() :
			info.append( "Show {} {}".format( label, "On" if plug[childName]["value"].getValue() else "Off" ) )

	return ", ".join( info )

def __statisticsSummary( plug ) :

	info = []

	if plug["dl:statistics_progress"]["enabled"].getValue() :
		info.append( "Progress {}".format( "On" if plug["dl:statistics_progress"]["value"].getValue() else "Off" ) )

	if plug["dl:statistics_filename"]["enabled"].getValue() :
		info.append( "Stats File: {}".format( plug["dl:statistics_filename"]["value"].getValue() ) )

	return ", ".join( info )

def __rayDepthSummary( plug ) :

	info = []

	for rayType in ( "diffuse", "hair", "reflection", "refraction", "volume" ) :
		childName = "dl:maximumraydepth_" + rayType
		if plug[childName]["enabled"].getValue() :
			info.append(
				"{} {}".format( rayType.capitalize(), plug[childName]["value"].getValue() )
			)

	return ", ".join( info )

def __rayLengthSummary( plug ) :

	info = []

	for rayLength in ( "diffuse", "hair", "reflection", "refraction", "specular", "volume" ) :
		childName = "dl:maximumraylength_" + rayLength
		if plug[childName]["enabled"].getValue() :
			info.append(
				"{} {}".format( rayLength.capitalize(), plug[childName]["value"].getValue() )
			)

	return ", ".join( info )

def __texturingSummary( plug ) :

	info = []

	if plug["dl:texturememory"]["enabled"].getValue() :
		info.append( "Memory {} Mb".format( plug["dl:texturememory"]["value"].getValue() ) )

	return ", ".join( info )

def __networkCacheSummary( plug ) :

	info = []

	if plug["dl:networkcache_size"]["enabled"].getValue() :
		info.append( "Size {} gb".format( plug["dl:networkcache_size"]["value"].getValue() ) )

	return ", ".join( info )

def __licensingSummary( plug ) :

	info = []

	if plug["dl:license_server"]["enabled"].getValue() :
		info.append( "Server {}".format( plug["dl:license_server"]["value"].getValue() ) )
	if plug["dl:license_wait"]["enabled"].getValue() :
		info.append( "Wait {}".format( "On" if plug["dl:license_wait"]["value"].getValue() else "Off" ) )

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

		"options" : {

			"layout:section:Rendering:summary" : __renderingSummary,
			"layout:section:Quality:summary" : __qualitySummary,
			"layout:section:Features:summary" : __featuresSummary,
			"layout:section:Statistics:summary" : __statisticsSummary,
			"layout:section:Ray Depth:summary" : __rayDepthSummary,
			"layout:section:Ray Length:summary" : __rayLengthSummary,
			"layout:section:Texturing:summary" : __texturingSummary,
			"layout:section:Network Cache:summary" : __networkCacheSummary,
			"layout:section:Licensing:summary" : __licensingSummary,

			"layout:customWidget:labelSpacer:widgetType" : "GafferUI.PlugLayout.StandardFilterWidget.PlugLabelSpacer",
			"layout:customWidget:labelSpacer:index" : 0,

			"layout:customWidget:optionFilter:widgetType" : "GafferUI.PlugLayout.StandardFilterWidget",
			"layout:customWidget:optionFilter:index" : 1,
			"layout:customWidget:optionFilter:accessory" : True,

		},

	}

)
