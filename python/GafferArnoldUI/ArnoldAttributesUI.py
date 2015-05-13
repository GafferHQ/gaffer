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

	"description",
	"""
	Applies Arnold attributes to objects
	in the scene.
	""",

	plugs = {

		# Sections

		"attributes" : [

			"layout:section:Visibility:summary", __visibilitySummary,
			"layout:section:Subdivision:summary", __subdivisionSummary,

		],

		# Visibility

		"attributes.cameraVisibility" : [

			"description",
			"""
			Whether or not the object is visible to camera
			rays. To hide an object completely, use the
			visibility settings on the StandardAttributes
			node instead.
			""",

			"layout:section", "Visibility",
			"label", "Camera",

		],

		"attributes.shadowVisibility" : [

			"description",
			"""
			Whether or not the object is visible to shadow
			rays (whether or not it casts shadows).
			""",

			"layout:section", "Visibility",
			"label", "Shadow",

		],

		"attributes.reflectedVisibility" : [

			"description",
			"""
			Whether or not the object is visible in
			tight mirror reflections.
			""",

			"layout:section", "Visibility",
			"label", "Reflections",

		],

		"attributes.refractedVisibility" : [

			"description",
			"""
			Whether or not the object is visible in
			refractions.
			""",

			"layout:section", "Visibility",
			"label", "Refractions",

		],

		"attributes.diffuseVisibility" : [

			"description",
			"""
			Whether or not the object is visible to diffuse
			rays - whether it casts bounce light or not.
			""",

			"layout:section", "Visibility",
			"label", "Diffuse",

		],

		"attributes.glossyVisibility" : [

			"description",
			"""
			Whether or not the object is visible in
			soft specular reflections.
			""",

			"layout:section", "Visibility",
			"label", "Glossy",

		],

		# Subdivision

		"attributes.subdivIterations" : [

			"description",
			"""
			The maximum number of subdivision
			steps to apply when rendering subdivision
			surface. To set an exact number of
			subdivisions, set the pixel error to
			0 so that the maximum becomes the
			controlling factor.

			Use the MeshType node to ensure that a
			mesh is treated as a subdivision surface
			in the first place.
			""",

			"layout:section", "Subdivision",
			"label", "Iterations",

		],

		"attributes.subdivPixelError" : [

			"description",
			"""
			The maximum allowable deviation from the true
			surface and the subdivided approximation. How
			the error is measured is determined by the
			metric below. Note also that the iterations
			value above provides a hard limit on the maximum
			number of subdivision steps, so if changing the
			pixel error setting appears to have no effect,
			you may need to raise the maximum.
			""",

			"layout:section", "Subdivision",
			"label", "Pixel Error",

		],

		"attributes.subdivAdaptiveMetric" : [

			"description",
			"""
			The metric used when performing adaptive
			subdivision as specified by the pixel error.
			The flatness metric ensures that the subdivided
			surface doesn't deviate from the true surface
			by more than the pixel error, and will tend to
			increase detail in areas of high curvature. The
			edge length metric ensures that the edge length
			of a polygon is never longer than the pixel metric,
			so will tend to subdivide evenly regardless of
			curvature - this can be useful when applying a
			displacement shader. The auto metric automatically
			uses the flatness metric when no displacement
			shader is applied, and the edge length metric when
			a displacement shader is applied.
			""",

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
