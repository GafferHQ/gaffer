##########################################################################
#
#  Copyright (c) 2014, Esteban Tovagliari. All rights reserved.
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
import GafferAppleseed

def __visibilitySummary( plug ) :

	info = []
	for childName, label in (

		( "camera", "Camera" ),
		( "light", "Light" ),
		( "shadow", "Shadow" ),
		( "transparency", "Transparency" ),
		( "probe", "Probe" ),
		( "diffuse", "Diffuse" ),
		( "specular", "Specular" ),
		( "glossy", "Glossy" ),
	)	:
		values = []
		if plug[childName+"Visibility"]["enabled"].getValue() :
			values.append( "On" if plug[childName+"Visibility"]["value"].getValue() else "Off" )
		if values :
			info.append( label + " : " + "/".join( values ) )

	return ", ".join( info )

def __shadingSummary( plug ) :

	info = []
	if plug["shadingSamples"]["enabled"].getValue() :
		info.append( "Shading Samples %d" % plug["shadingSamples"]["value"].getValue() )

	return ", ".join( info )

def __alphaMapSummary( plug ) :

	info = []
	if plug["alphaMap"]["enabled"].getValue() :
		info.append( "Alpha Map %s" % plug["alphaMap"]["value"].getValue() )

	return ", ".join( info )

GafferUI.PlugValueWidget.registerCreator(

	GafferAppleseed.AppleseedAttributes,
	"attributes",
	GafferUI.SectionedCompoundDataPlugValueWidget,
	sections = (
		{
			"label" : "Visibility",
			"summary" : __visibilitySummary,
			"namesAndLabels" : (
				( "as:visibility:camera", "Camera" ),
				( "as:visibility:light", "Light" ),
				( "as:visibility:shadow" , "Shadow" ),
				( "as:visibility:transparency" , "Transparency" ),
				( "as:visibility:probe" , "Probe" ),
				( "as:visibility:diffuse", "Diffuse" ),
				( "as:visibility:specular", "Specular" ),
				( "as:visibility:glossy", "Glossy" ),
			),
		},
		{
			"label" : "Shading",
			"summary" : __shadingSummary,
			"namesAndLabels" : (
				( "as:shading_samples", "Shading Samples" ),
			),
		},
		{
			"label" : "Alpha Map",
			"summary" : __alphaMapSummary,
			"namesAndLabels" : (
				( "as:alpha_map", "Alpha Map" ),
			),
		},
	),
)

GafferUI.PlugValueWidget.registerCreator(
	GafferAppleseed.AppleseedAttributes,
	"attributes.alphaMap.value",
	lambda plug : GafferUI.PathPlugValueWidget( plug,
		path = Gaffer.FileSystemPath( "/", filter = Gaffer.FileSystemPath.createStandardFilter() ),
		pathChooserDialogueKeywords = {
			"bookmarks" : GafferUI.Bookmarks.acquire( plug, category = "appleseed" ),
			"leaf" : True,
		},
	),
)
