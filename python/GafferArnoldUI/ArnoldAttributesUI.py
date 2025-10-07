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

import string

import Gaffer
import GafferUI
import GafferArnold

def __visibilitySummary( plug ) :

	info = []
	for childName, label in (

		( "camera", "Camera" ),
		( "shadow", "Shad" ),
		( "diffuse_reflect", "DiffRefl" ),
		( "specular_reflect", "SpecRefl" ),
		( "diffuse_transmit", "DiffTrans" ),
		( "specular_transmit", "SpecTrans" ),
		( "volume", "Volume" ),
		( "subsurface", "Subsurf" ),

	)	:
		if plug["ai:visibility:" + childName]["enabled"].getValue() :
			info.append( label + ( " On" if plug["ai:visibility:" + childName]["value"].getValue() else " Off" ) )

	if plug["ai:visibility:shadow_group"]["enabled"].getValue() :
		info.append( "ShadowGroup Applied" )

	return ", ".join( info )

__transformTypeEnumNames = { "linear" : "Linear", "rotate_about_origin" : "RotateAboutOrigin",
	"rotate_about_center" : "RotateAboutCenter" }

def __autoBumpVisibilitySummary( plug ) :

	info = []
	for childName, label in (

		( "camera", "Camera" ),
		( "shadow", "Shadow" ),
		( "diffuse_reflect", "DiffRefl" ),
		( "specular_reflect", "SpecRefl" ),
		( "diffuse_transmit", "DiffTrans" ),
		( "specular_transmit", "SpecTrans" ),
		( "volume", "Volume" ),
		( "subsurface", "Subsurf" ),

	)	:
		if plug["ai:autobump_visibility:" + childName]["enabled"].getValue() :
			info.append( label + ( " On" if plug["ai:autobump_visibility:" + childName]["value"].getValue() else " Off" ) )

	return ", ".join( info )

def __transformSummary( plug ) :

	info = []

	if plug["ai:transform_type"]["enabled"].getValue() :
		info.append( "Transform Type " + __transformTypeEnumNames[ plug["ai:transform_type"]["value"].getValue() ] )

	return ", ".join( info )

def __shadingSummary( plug ) :

	info = []
	for childName, label in (
		( "ai:matte", "Matte" ),
		( "ai:opaque", "Opaque" ),
		( "ai:receive_shadows", "Receive Shadows" ),
		( "ai:self_shadows", "Self Shadows" ),
	) :
		if plug[childName]["enabled"].getValue() :
			info.append( label + ( " On" if plug[childName]["value"].getValue() else " Off" ) )

	if plug["ai:sss_setname"]["enabled"].getValue() :
		info.append( "SSS Set Name " + plug["ai:sss_setname"]["value"].getValue() )

	return ", ".join( info )

def __subdivisionSummary( plug ) :

	info = []
	if plug["ai:polymesh:subdiv_iterations"]["enabled"].getValue() :
		info.append( "Iterations %d" % plug["ai:polymesh:subdiv_iterations"]["value"].getValue() )
	if plug["ai:polymesh:subdiv_adaptive_error"]["enabled"].getValue() :
		info.append( "Error %s" % GafferUI.NumericWidget.valueToString( plug["ai:polymesh:subdiv_adaptive_error"]["value"].getValue() ) )
	if plug["ai:polymesh:subdiv_adaptive_metric"]["enabled"].getValue() :
		info.append( string.capwords( plug["ai:polymesh:subdiv_adaptive_metric"]["value"].getValue().replace( "_", " " ) ) + " Metric" )
	if plug["ai:polymesh:subdiv_adaptive_space"]["enabled"].getValue() :
		info.append( string.capwords( plug["ai:polymesh:subdiv_adaptive_space"]["value"].getValue() ) + " Space" )
	if plug["ai:polymesh:subdiv_uv_smoothing"]["enabled"].getValue() :
		info.append(
			{
				"pin_corners" : "Pin UV Corners",
				"pin_borders" : "Pin UV Borders",
				"linear" : "Linear UVs",
				"smooth" : "Smooth UVs",
			}.get( plug["ai:polymesh:subdiv_uv_smoothing"]["value"].getValue() )
		)
	if plug["ai:polymesh:subdiv_smooth_derivs"]["enabled"].getValue() :
		info.append( "Smooth Derivs " + ( "On" if plug["ai:polymesh:subdiv_smooth_derivs"]["value"].getValue() else "Off" ) )
	if plug["ai:polymesh:subdiv_frustum_ignore"]["enabled"].getValue() :
		info.append( "Frustum Ignore " + ( "On" if plug["ai:polymesh:subdiv_frustum_ignore"]["value"].getValue() else "Off" ) )
	if plug["ai:polymesh:subdivide_polygons"]["enabled"].getValue() :
		info.append( "Subdivide Polygons " + ( "On" if plug["ai:polymesh:subdivide_polygons"]["value"].getValue() else "Off" ) )

	return ", ".join( info )

def __curvesSummary( plug ) :

	info = []
	if plug["ai:curves:mode"]["enabled"].getValue() :
		info.append( string.capwords( plug["ai:curves:mode"]["value"].getValue() ) )
	if plug["ai:curves:min_pixel_width"]["enabled"].getValue() :
		info.append( "Min Pixel Width %s" % GafferUI.NumericWidget.valueToString( plug["ai:curves:min_pixel_width"]["value"].getValue() ) )

	return ", ".join( info )

def __pointsSummary( plug ) :

	info = []
	if plug["ai:points:min_pixel_width"]["enabled"].getValue() :
		info.append( "Min Pixel Width {}".format( GafferUI.NumericWidget.valueToString( plug["ai:points:min_pixel_width"]["value"].getValue() ) ) )

	return ", ".join( info )

def __volumeSummary( plug ) :

	info = []
	if plug["ai:volume:step_scale"]["enabled"].getValue() :
		info.append( "Volume Step Scale %s" % GafferUI.NumericWidget.valueToString( plug["ai:volume:step_scale"]["value"].getValue() ) )
	if plug["ai:volume:step_size"]["enabled"].getValue() :
		info.append( "Volume Step Size %s" % GafferUI.NumericWidget.valueToString( plug["ai:volume:step_size"]["value"].getValue() ) )
	if plug["ai:shape:step_scale"]["enabled"].getValue() :
		info.append( "Shape Step Scale %s" % GafferUI.NumericWidget.valueToString( plug["ai:shape:step_scale"]["value"].getValue() ) )
	if plug["ai:shape:step_size"]["enabled"].getValue() :
		info.append( "Shape Step Size %s" % GafferUI.NumericWidget.valueToString( plug["ai:shape:step_size"]["value"].getValue() ) )
	if plug["ai:shape:volume_padding"]["enabled"].getValue() :
		info.append( "Padding %s" % GafferUI.NumericWidget.valueToString( plug["ai:shape:volume_padding"]["value"].getValue() ) )
	if plug["ai:volume:velocity_scale"]["enabled"].getValue() :
		info.append( "Velocity Scale %s" % GafferUI.NumericWidget.valueToString( plug["ai:volume:velocity_scale"]["value"].getValue() ) )
	if plug["ai:volume:velocity_fps"]["enabled"].getValue() :
		info.append( "Velocity FPS %s" % GafferUI.NumericWidget.valueToString( plug["ai:volume:velocity_fps"]["value"].getValue() ) )
	if plug["ai:volume:velocity_outlier_threshold"]["enabled"].getValue() :
		info.append( "Velocity Outlier Threshold %s" % GafferUI.NumericWidget.valueToString( plug["ai:volume:velocity_outlier_threshold"]["value"].getValue() ) )

	return ", ".join( info )

def __toonSummary( plug ) :

	info = []
	if plug["ai:toon_id"]["enabled"].getValue() :
		info.append( "Toon Id " + plug["ai:toon_id"]["value"].getValue() )

	return ", ".join( info )

Gaffer.Metadata.registerNode(

	GafferArnold.ArnoldAttributes,

	"description",
	"""
	Applies Arnold attributes to objects in the scene.
	""",

	plugs = {

		# Sections

		"attributes" : {

			"layout:section:Visibility:summary" : __visibilitySummary,
			"layout:section:Displacement.Auto Bump Visibility:summary" : __autoBumpVisibilitySummary,
			"layout:section:Transform:summary" : __transformSummary,
			"layout:section:Shading:summary" : __shadingSummary,
			"layout:section:Subdivision:summary" : __subdivisionSummary,
			"layout:section:Curves:summary" : __curvesSummary,
			"layout:section:Points:summary" : __pointsSummary,
			"layout:section:Volume:summary" : __volumeSummary,
			"layout:section:Toon:summary" : __toonSummary,

		},

	}

)
