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

import Gaffer
import GafferCycles

def __attributeSummary( plug, attributes ) :

	info = []

	for attribute in attributes :
		if plug[f"cycles:{attribute}"]["enabled"].getValue() :
			if Gaffer.Metadata.value( f"attribute:cycles:{attribute}", "plugValueWidget:type" ) == "GafferUI.PresetsPlugValueWidget" :
				value = Gaffer.NodeAlgo.currentPreset( plug[f"cycles:{attribute}"]["value"] )
			else :
				value = plug[f"cycles:{attribute}"]["value"].getValue()
				if isinstance( value, bool ) :
					value = "On" if value else "Off"

			info.append( "{} {}".format( Gaffer.Metadata.value( f"attribute:cycles:{attribute}", "label" ), value ) )

	return info

def __visibilitySummary( plug ) :

	attributes = [
		"visibility:camera",
		"visibility:diffuse",
		"visibility:glossy",
		"visibility:transmission",
		"visibility:shadow",
		"visibility:scatter",
	]

	return ", ".join( __attributeSummary( plug, attributes ) )

def __renderingSummary( plug ) :

	info = []
	attributes = [
		"use_holdout",
		"is_shadow_catcher",
		"is_caustics_caster",
		"is_caustics_receiver",
		"lightgroup",
	]

	return ", ".join( __attributeSummary( plug, attributes ) )

def __subdivisionSummary( plug ) :

	return ", ".join( __attributeSummary( plug, [ "max_level", "dicing_rate", "adaptive_space" ] ) )

def __volumeSummary( plug ) :

	attributes = [
		"volume_clipping",
		"volume_step_size",
		"volume_object_space",
		"volume_velocity_scale",
		"volume_precision",
	]

	return ", ".join( __attributeSummary( plug, attributes ) )

def __objectSummary( plug ) :

	return ", ".join( __attributeSummary( plug, [ "asset_name" ] ) )

def __shaderSummary( plug ) :

	attributes = [
		"shader:emission_sampling_method",
		"shader:use_transparent_shadow",
		"shader:volume_sampling_method",
		"shader:volume_interpolation_method",
		"shader:volume_step_rate",
		"shader:displacement_method",
	]

	return ", ".join( __attributeSummary( plug, attributes ) )

Gaffer.Metadata.registerNode(

	GafferCycles.CyclesAttributes,

	"description",
	"""
	Applies Cycles attributes to objects in the scene.
	""",

	plugs = {

		# Sections

		"attributes" : {

			"layout:section:Visibility:summary" : __visibilitySummary,
			"layout:section:Rendering:summary" : __renderingSummary,
			"layout:section:Subdivision:summary" : __subdivisionSummary,
			"layout:section:Volume:summary" : __volumeSummary,
			"layout:section:Object:summary" : __objectSummary,
			"layout:section:Shader:summary" : __shaderSummary,

			"layout:customWidget:attributeFilter:widgetType" : "GafferUI.PlugLayout.StandardFilterWidget",
			"layout:customWidget:attributeFilter:index" : 0,

		},

	}

)
