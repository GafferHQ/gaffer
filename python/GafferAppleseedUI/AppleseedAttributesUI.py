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

	if plug["mediumPriority"]["enabled"].getValue() :
		info.append( "Medium Priority %d" % plug["mediumPriority"]["value"].getValue() )

	if plug["doubleSided"]["enabled"].getValue() :
		info.append( "Double Sided %d" % plug["doubleSided"]["value"].getValue() )

	return ", ".join( info )

def __alphaMapSummary( plug ) :

	info = []
	if plug["alphaMap"]["enabled"].getValue() :
		info.append( "Alpha Map %s" % plug["alphaMap"]["value"].getValue() )

	return ", ".join( info )

def __meshSummary( plug ) :

	info = []

	if plug["smoothNormals"]["enabled"].getValue() :
		info.append( "Smooth Normals %s" % plug["smoothNormals"]["value"].getValue() )

	if plug["smoothTangents"]["enabled"].getValue() :
		info.append( "Smooth Tangents %s" % plug["smoothTangents"]["value"].getValue() )

	return ", ".join( info )

Gaffer.Metadata.registerNode(

	GafferAppleseed.AppleseedAttributes,

	"description",
	"""
	Applies appleseed attributes to objects
	in the scene.
	""",

	plugs = {

		# Sections

		"attributes" : [

			"layout:section:Visibility:summary", __visibilitySummary,
			"layout:section:Shading:summary", __shadingSummary,
			"layout:section:Alpha Map:summary", __alphaMapSummary,
			"layout:section:Mesh :summary", __meshSummary,

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

		"attributes.lightVisibility" : [

			"description",
			"""
			Whether or not the object is visible to light
			rays (whether or not it is visible to photons).
			""",

			"layout:section", "Visibility",
			"label", "Light",

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

		"attributes.diffuseVisibility" : [

			"description",
			"""
			Whether or not the object is visible to diffuse
			rays - whether it casts bounce light or not.
			""",

			"layout:section", "Visibility",
			"label", "Diffuse",

		],

		"attributes.specularVisibility" : [

			"description",
			"""
			Whether or not the object is visible in
			tight mirror reflections and refractions.
			""",

			"layout:section", "Visibility",
			"label", "Specular",

		],

		"attributes.glossyVisibility" : [

			"description",
			"""
			Whether or not the object is visible in
			soft specular reflections and refractions.
			""",

			"layout:section", "Visibility",
			"label", "Glossy",

		],

		# Shading

		"attributes.shadingSamples" : [

			"description",
			"""
			Number of samples to use when computing shading for the object.
			""",

			"layout:section", "Shading",

		],

		"attributes.mediumPriority" : [

			"description",
			"""
			Specify the object medium priority.
			When multiple objects share the same volume, appleseed will consider
			only the highest priority one for intersections and shading.
			Sometimes called nested dielectrics in other renderers.
			""",

			"layout:section", "Shading",

		],

		"attributes.doubleSided" : [

			"description",
			"""
			Assign materials to the back side of objects.
			It is important to disable double sided assignments if the material
			has emision closures and emision is not wanted on the inside of objects,
			for example for closed objects, to reduce the amount of noise in the render.
			""",

			"layout:section", "Shading",

		],

		# Alpha Map

		"attributes.alphaMap" : [

			"description",
			"""
			Specifies a grayscale texture than can be used to efficiently discard
			unwanted parts of the surface of the object while computing ray intersections.
			""",

			"layout:section", "Alpha Map",

		],

		"attributes.alphaMap.value" : [

			"path:leaf", True,
			"path:bookmarks", "texture",

		],

		"attributes.smoothNormals" : [

		"description",
		"""
		Compute smooth normals.
		""",

		"layout:section", "Mesh",
		"label", "Smooth Normals",

		],

		"attributes.smoothTangents" : [

		"description",
		"""
		Compute smooth tangents.
		""",

		"layout:section", "Mesh",
		"label", "Smooth Tangents",

		],

	}

)
