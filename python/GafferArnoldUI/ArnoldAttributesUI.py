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
		( "reflected", "Refl" ),
		( "refracted", "Refr" ),
		( "diffuse", "Diff" ),
		( "glossy", "Glossy" ),

	)	:
		if plug[childName+"Visibility"]["enabled"].getValue() :
			info.append( label + ( " On" if plug[childName+"Visibility"]["value"].getValue() else " Off" ) )

	return ", ".join( info )

def __subdivisionSummary( plug ) :

	info = []
	if plug["subdivIterations"]["enabled"].getValue() :
		info.append( "Iterations %d" % plug["subdivIterations"]["value"].getValue() )
	if plug["subdivPixelError"]["enabled"].getValue() :
		info.append( ( "Error %.4f" % plug["subdivPixelError"]["value"].getValue() ).rstrip( '0' ).rstrip( '.' ) )
	if plug["subdivAdaptiveMetric"]["enabled"].getValue() :
		info.append( string.capwords( plug["subdivAdaptiveMetric"]["value"].getValue().replace( "_", " " ) ) + " Metric" )

	return ", ".join( info )

Gaffer.Metadata.registerNode(

	GafferArnold.ArnoldAttributes,

	plugs = {

		# Sections

		"attributes" : [

			"layout:section:Visibility:summary", __visibilitySummary,
			"layout:section:Subdivision:summary", __subdivisionSummary,

		],

		# Visibility

		"attributes.cameraVisibility" : [

			"layout:section", "Visibility",
			"label", "Camera",

		],

		"attributes.shadowVisibility" : [

			"layout:section", "Visibility",
			"label", "Shadow",

		],

		"attributes.reflectedVisibility" : [

			"layout:section", "Visibility",
			"label", "Reflections",

		],

		"attributes.refractedVisibility" : [

			"layout:section", "Visibility",
			"label", "Refractions",

		],

		"attributes.diffuseVisibility" : [

			"layout:section", "Visibility",
			"label", "Diffuse",

		],

		"attributes.glossyVisibility" : [

			"layout:section", "Visibility",
			"label", "Glossy",

		],

		# Subdivision

		"attributes.subdivIterations" : [

			"layout:section", "Subdivision",
			"label", "Iterations",

		],

		"attributes.subdivPixelError" : [

			"layout:section", "Subdivision",
			"label", "Pixel Error",

		],

		"attributes.subdivAdaptiveMetric" : [

			"layout:section", "Subdivision",
			"label", "Adaptive Metric",

		],


		"attributes.subdivAdaptiveMetric.value" : [

			"preset:Auto", "auto",
			"preset:Edge Length", "edge_length",
			"preset:Flatness", "flatness",

		],

	}

)

GafferUI.PlugValueWidget.registerCreator(
	GafferArnold.ArnoldAttributes,
	"attributes.subdivAdaptiveMetric.value",
	GafferUI.PresetsPlugValueWidget
)
