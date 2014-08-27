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

GafferUI.PlugValueWidget.registerCreator(

	GafferArnold.ArnoldAttributes,
	"attributes",
	GafferUI.SectionedCompoundDataPlugValueWidget,
	sections = (
		{
			"label" : "Visibility",
			"summary" : __visibilitySummary,
			"namesAndLabels" : (
				( "ai:visibility:camera", "Camera" ),
				( "ai:visibility:shadow", "Shadow" ),
				( "ai:visibility:reflected", "Reflections" ),
				( "ai:visibility:refracted", "Refractions" ),
				( "ai:visibility:diffuse", "Diffuse" ),
				( "ai:visibility:glossy", "Glossy" ),
			),
		},
		{
			"label" : "Subdivision",
			"summary" : __subdivisionSummary,
			"namesAndLabels" : (
				( "ai:polymesh:subdiv_iterations", "Iterations" ),
				( "ai:polymesh:subdiv_pixel_error", "Pixel Error" ),
				( "ai:polymesh:subdiv_adaptive_metric", "Adaptive Metric" ),
			),
		},
	),

)

GafferUI.PlugValueWidget.registerCreator(
	GafferArnold.ArnoldAttributes,
	"attributes.subdivAdaptiveMetric.value",
	GafferUI.EnumPlugValueWidget,
	labelsAndValues = (
		( "Auto", "auto" ),
		( "Edge Length", "edge_length" ),
		( "Flatness", "flatness" ),
	),
)
