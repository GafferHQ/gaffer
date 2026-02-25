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

import Gaffer
import GafferUI
import GafferArnold

def __renderingSummary( plug ) :

	info = []
	if plug["ai:bucket_size"]["enabled"].getValue() :
		info.append( "Bucket Size %d" % plug["ai:bucket_size"]["value"].getValue() )
	if plug["ai:bucket_scanning"]["enabled"].getValue() :
		info.append( "Bucket Scanning %s" % plug["ai:bucket_scanning"]["value"].getValue().capitalize() )
	if plug["ai:parallel_node_init"]["enabled"].getValue() :
		info.append( "Parallel Init %s" % ( "On" if plug["ai:parallel_node_init"]["value"].getValue() else "Off" ) )
	if plug["ai:threads"]["enabled"].getValue() :
		info.append( "Threads %d" % plug["ai:threads"]["value"].getValue() )
	return ", ".join( info )

def __samplingSummary( plug ) :

	info = []
	if plug["ai:AA_samples"]["enabled"].getValue() :
		info.append( "AA %d" % plug["ai:AA_samples"]["value"].getValue() )
	if plug["ai:GI_diffuse_samples"]["enabled"].getValue() :
		info.append( "Diffuse %d" % plug["ai:GI_diffuse_samples"]["value"].getValue() )
	if plug["ai:GI_specular_samples"]["enabled"].getValue() :
		info.append( "Specular %d" % plug["ai:GI_specular_samples"]["value"].getValue() )
	if plug["ai:GI_transmission_samples"]["enabled"].getValue() :
		info.append( "Transmission %d" % plug["ai:GI_transmission_samples"]["value"].getValue() )
	if plug["ai:GI_sss_samples"]["enabled"].getValue() :
		info.append( "SSS %d" % plug["ai:GI_sss_samples"]["value"].getValue() )
	if plug["ai:GI_volume_samples"]["enabled"].getValue() :
		info.append( "Volume %d" % plug["ai:GI_volume_samples"]["value"].getValue() )
	if plug["ai:light_samples"]["enabled"].getValue() :
		info.append( "Light %d" % plug["ai:light_samples"]["value"].getValue() )
	if plug["ai:AA_seed"]["enabled"].getValue() :
		info.append( "Seed {0}".format( plug["ai:AA_seed"]["value"].getValue() ) )
	if plug["ai:AA_sample_clamp"]["enabled"].getValue() :
		info.append( "Clamp {0}".format( GafferUI.NumericWidget.valueToString( plug["ai:AA_sample_clamp"]["value"].getValue() ) ) )
	if plug["ai:AA_sample_clamp_affects_aovs"]["enabled"].getValue() :
		info.append( "Clamp AOVs {0}".format( "On" if plug["ai:AA_sample_clamp_affects_aovs"]["value"].getValue() else "Off" ) )
	if plug["ai:indirect_sample_clamp"]["enabled"].getValue() :
		info.append( "Indirect Clamp {0}".format( GafferUI.NumericWidget.valueToString( plug["ai:indirect_sample_clamp"]["value"].getValue() ) ) )
	if plug["ai:low_light_threshold"]["enabled"].getValue() :
		info.append( "Low Light {0}".format( GafferUI.NumericWidget.valueToString( plug["ai:low_light_threshold"]["value"].getValue() ) ) )
	return ", ".join( info )

def __adaptiveSamplingSummary( plug ) :

	info = []
	if plug["ai:enable_adaptive_sampling"]["enabled"].getValue() :
		info.append( "Enable %d" % plug["ai:enable_adaptive_sampling"]["value"].getValue() )
	if plug["ai:AA_samples_max"]["enabled"].getValue() :
		info.append( "AA Max %d" % plug["ai:AA_samples_max"]["value"].getValue() )
	if plug["ai:AA_adaptive_threshold"]["enabled"].getValue() :
		info.append( "Threshold %s" % GafferUI.NumericWidget.valueToString( plug["ai:AA_adaptive_threshold"]["value"].getValue() ) )
	return ", ".join( info )

def __interactiveRenderingSummary( plug ) :

	info = []
	if plug["ai:enable_progressive_render"]["enabled"].getValue() :
		info.append( "Progressive %s" % ( "On" if plug["ai:enable_progressive_render"]["value"].getValue() else "Off" ) )
	if plug["ai:progressive_min_AA_samples"]["enabled"].getValue() :
		info.append( "Min AA %d" % plug["ai:progressive_min_AA_samples"]["value"].getValue() )
	return ", ".join( info )

def __rayDepthSummary( plug ) :

	info = []
	if plug["ai:GI_total_depth"]["enabled"].getValue() :
		info.append( "Total %d" % plug["ai:GI_total_depth"]["value"].getValue() )
	if plug["ai:GI_diffuse_depth"]["enabled"].getValue() :
		info.append( "Diffuse %d" % plug["ai:GI_diffuse_depth"]["value"].getValue() )
	if plug["ai:GI_specular_depth"]["enabled"].getValue() :
		info.append( "Specular %d" % plug["ai:GI_specular_depth"]["value"].getValue() )
	if plug["ai:GI_transmission_depth"]["enabled"].getValue() :
		info.append( "Transmission %d" % plug["ai:GI_transmission_depth"]["value"].getValue() )
	if plug["ai:GI_volume_depth"]["enabled"].getValue() :
		info.append( "Volume %d" % plug["ai:GI_volume_depth"]["value"].getValue() )
	if plug["ai:auto_transparency_depth"]["enabled"].getValue() :
		info.append( "Transparency %d" % plug["ai:auto_transparency_depth"]["value"].getValue() )
	return ", ".join( info )

def __subdivisionSummary( plug ) :
	info = []
	if plug["ai:max_subdivisions"]["enabled"].getValue():
		info.append( "Max Subdivisions  %d" % plug["ai:max_subdivisions"]["value"].getValue() )
	if plug["ai:subdiv_dicing_camera"]["enabled"].getValue():
		info.append( "Dicing Camera %s" % plug["ai:subdiv_dicing_camera"]["value"].getValue() )
	if plug["ai:subdiv_frustum_culling"]["enabled"].getValue():
		info.append( "Frustum Culling %s" % ( "On" if plug["ai:subdiv_frustum_culling"]["value"].getValue() else "Off" ) )
	if plug["ai:subdiv_frustum_padding"]["enabled"].getValue():
		info.append( "Frustum Padding %s" % GafferUI.NumericWidget.valueToString( plug["ai:subdiv_frustum_padding"]["value"].getValue() ) )
	return ", ".join( info )

def __texturingSummary( plug ) :

	info = []
	if plug["ai:texture_max_memory_MB"]["enabled"].getValue() :
		info.append( "Memory {0}".format( GafferUI.NumericWidget.valueToString( plug["ai:texture_max_memory_MB"]["value"].getValue() ) ) )
	if plug["ai:texture_per_file_stats"]["enabled"].getValue() :
		info.append( "Per File Stats {0}".format( "On" if plug["ai:texture_per_file_stats"]["value"].getValue() else "Off" ) )
	if plug["ai:texture_max_sharpen"]["enabled"].getValue() :
		info.append( "Sharpen {0}".format( GafferUI.NumericWidget.valueToString( plug["ai:texture_max_sharpen"]["value"].getValue() ) ) )
	if plug["ai:texture_use_existing_tx"]["enabled"].getValue() :
		info.append( "Use `.tx` {0}".format( "On" if plug["ai:texture_use_existing_tx"]["value"].getValue() else "Off" ) )
	if plug["ai:texture_auto_generate_tx"]["enabled"].getValue() :
		info.append( "Auto `.tx` {0}".format( "On" if plug["ai:texture_auto_generate_tx"]["value"].getValue() else "Off" ) )
	if plug["ai:texture_auto_tx_path"]["enabled"].getValue() :
		info.append( "Auto `.tx` path" )
	return ", ".join( info )

def __featuresSummary( plug ) :

	info = []
	for childName, label in (
		( "ai:ignore_textures", "Textures" ),
		( "ai:ignore_shaders", "Shaders" ),
		( "ai:ignore_atmosphere", "Atmos" ),
		( "ai:ignore_lights", "Lights" ),
		( "ai:ignore_shadows", "Shadows" ),
		( "ai:ignore_subdivision", "Subdivs" ),
		( "ai:ignore_displacement", "Disp" ),
		( "ai:ignore_bump", "Bump" ),
		( "ai:ignore_sss", "SSS" ),
		( "ai:ignore_imagers", "Imagers" ),
	) :
		if plug[childName]["enabled"].getValue() :
			info.append( label + ( " Off " if plug[childName]["value"].getValue() else " On" ) )

	return ", ".join( info )

def __searchPathsSummary( plug ) :

	info = []
	for prefix in ( "texture", "procedural", "plugin" ) :
		if plug["ai:" + prefix + "_searchpath"]["enabled"].getValue() :
			info.append( prefix.capitalize() )

	return ", ".join( info )

def __errorHandlingSummary( plug ) :

	info = []
	if plug["ai:abort_on_error"]["enabled"].getValue() :
		info.append( "Abort on Error " + ( "On" if plug["ai:abort_on_error"]["value"].getValue() else "Off" ) )
	for suffix in ( "texture", "pixel", "shader" ) :
		if plug["ai:error_color_bad_" + suffix]["enabled"].getValue() :
			info.append( suffix.capitalize() )

	return ", ".join( info )

def __loggingSummary( plug ) :

	info = []
	if plug["ai:log:filename"]["enabled"].getValue() :
		info.append( "File name" )
	if plug["ai:log:max_warnings"]["enabled"].getValue() :
		info.append( "Max Warnings %d" % plug["ai:log:max_warnings"]["value"].getValue() )

	return ", ".join( info )

def __statisticsSummary( plug ) :

	info = []
	if plug["ai:statisticsFileName"]["enabled"].getValue() :
		info.append( "Stats File: " + plug["ai:statisticsFileName"]["value"].getValue() )
	if plug["ai:profileFileName"]["enabled"].getValue() :
		info.append( "Profile File: " + plug["ai:profileFileName"]["value"].getValue() )
	if plug["ai:reportFileName"]["enabled"].getValue() :
		info.append( "Report File: " + plug["ai:reportFileName"]["value"].getValue() )

	return ", ".join( info )

def __licensingSummary( plug ) :

	info = []
	for name, label in (
		( "ai:abort_on_license_fail", "Abort on Fail" ),
		( "ai:skip_license_check", "Skip Check" )
	) :
		if plug[name]["enabled"].getValue() :
			info.append( label + " " + ( "On" if plug[name]["value"].getValue() else "Off" ) )

	return ", ".join( info )

def __gpuSummary( plug ) :

	info = []
	if plug["ai:render_device"]["enabled"].getValue() :
		info.append( "Device: %s" %  plug["ai:render_device"]["value"].getValue() )

	if plug["ai:gpu_max_texture_resolution"]["enabled"].getValue() :
		info.append( "Max Res: %i" % plug["ai:gpu_max_texture_resolution"]["value"].getValue() )
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

		"options" : {

			"layout:section:Rendering:summary" : __renderingSummary,
			"layout:section:Sampling:summary" : __samplingSummary,
			"layout:section:Adaptive Sampling:summary" : __adaptiveSamplingSummary,
			"layout:section:Interactive Rendering:summary" : __interactiveRenderingSummary,
			"layout:section:Ray Depth:summary" : __rayDepthSummary,
			"layout:section:Subdivision:summary" : __subdivisionSummary,
			"layout:section:Texturing:summary" : __texturingSummary,
			"layout:section:Features:summary" : __featuresSummary,
			"layout:section:Search Paths:summary" : __searchPathsSummary,
			"layout:section:Error Handling:summary" : __errorHandlingSummary,
			"layout:section:Logging:summary" : __loggingSummary,
			"layout:section:Statistics:summary" : __statisticsSummary,
			"layout:section:Licensing:summary" : __licensingSummary,
			"layout:section:GPU:summary" : __gpuSummary,

			"layout:customWidget:labelSpacer:widgetType" : "GafferUI.PlugLayout.StandardFilterWidget.PlugLabelSpacer",
			"layout:customWidget:labelSpacer:index" : 0,

			"layout:customWidget:optionFilter:widgetType" : "GafferUI.PlugLayout.StandardFilterWidget",
			"layout:customWidget:optionFilter:index" : 1,
			"layout:customWidget:optionFilter:accessory" : True,

		},

	}

)