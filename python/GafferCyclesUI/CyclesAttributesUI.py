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

import IECore

import Gaffer
import GafferCycles

def __visibilitySummary( plug ) :

	info = []
	for childName in ( "camera", "diffuse", "glossy", "transmission", "shadow", "scatter" ) :
		if plug[childName + "Visibility"]["enabled"].getValue() :
			info.append( IECore.CamelCase.toSpaced( childName ) + ( " On" if plug[childName + "Visibility"]["value"].getValue() else " Off" ) )

	return ", ".join( info )

def __renderingSummary( plug ) :

	info = []
	for childName in ( "useHoldout", "isShadowCatcher", "dupliGenerated", "dupliUV", "lightGroup" ) :
		if plug[childName]["enabled"].getValue() :
			info.append( IECore.CamelCase.toSpaced( childName ) + ( " On" if plug[childName]["value"].getValue() else " Off" ) )

	return ", ".join( info )

def __subdivisionSummary( plug ) :

	info = []
	for childName in ( "maxLevel", "dicingScale" ) :
		if plug[childName]["enabled"].getValue() :
			info.append( IECore.CamelCase.toSpaced( childName ) + ( " On" if plug[childName]["value"].getValue() else " Off" ) )

	return ", ".join( info )

def __volumeSummary( plug ) :

	info = []
	for childName in ( "volumeClipping", "volumeStepSize", "volumeObjectSpace" ) :
		if plug[childName]["enabled"].getValue() :
			info.append( IECore.CamelCase.toSpaced( childName ) + ( " On" if plug[childName]["value"].getValue() else " Off" ) )

	return ", ".join( info )

def __objectSummary( plug ) :

	info = []
	if plug["assetName"]["enabled"].getValue() :
		info.append( IECore.CamelCase.toSpaced( "assetName" ) + ( " On" if plug["assetName"]["value"].getValue() else " Off" ) )

	return ", ".join( info )

def __shaderSummary( plug ) :

	info = []
	for childName in ( "emissionSamplingMethod", "useTransparentShadow", "heterogeneousVolume", "volumeSamplingMethod", "volumeInterpolationMethod", "volumeStepRate", "displacementMethod" ) :
		if plug[childName]["enabled"].getValue() :
			info.append( IECore.CamelCase.toSpaced( childName ) + ( " On" if plug[childName]["value"].getValue() else " Off" ) )

	return ", ".join( info )

Gaffer.Metadata.registerNode(

	GafferCycles.CyclesAttributes,

	"description",
	"""
	Applies Cycles attributes to objects in the scene.
	""",

	plugs = {

		# Sections

		"attributes" : [

			"layout:section:Visibility:summary", __visibilitySummary,
			"layout:section:Rendering:summary", __renderingSummary,
			"layout:section:Subdivision:summary", __subdivisionSummary,
			"layout:section:Volume:summary", __volumeSummary,
			"layout:section:Object:summary", __objectSummary,
			"layout:section:Shader:summary", __shaderSummary,

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

		"attributes.diffuseVisibility" : [

			"description",
			"""
			Whether or not the object is visible to diffuse
			rays.
			""",

			"layout:section", "Visibility",
			"label", "Diffuse",

		],

		"attributes.glossyVisibility" : [

			"description",
			"""
			Whether or not the object is visible in
			glossy rays.
			""",

			"layout:section", "Visibility",
			"label", "Glossy",

		],

		"attributes.transmissionVisibility" : [

			"description",
			"""
			Whether or not the object is visible in
			transmission.
			""",

			"layout:section", "Visibility",
			"label", "Transmission",

		],

		"attributes.shadowVisibility" : [

			"description",
			"""
			Whether or not the object is visible to shadow
			rays - whether it casts shadows or not.
			""",

			"layout:section", "Visibility",
			"label", "Shadow",

		],

		"attributes.scatterVisibility" : [

			"description",
			"""
			Whether or not the object is visible to
			scatter rays.
			""",

			"layout:section", "Visibility",
			"label", "Scatter",

		],

		# Rendering

		"attributes.useHoldout" : [

			"description",
			"""
			Turns the object into a holdout matte.
			This only affects primary (camera) rays.
			""",

			"layout:section", "Rendering",

		],

		"attributes.isShadowCatcher" : [

			"description",
			"""
			Turns the object into a shadow catcher.
			""",

			"layout:section", "Rendering",

		],

		"attributes.shadowTerminatorShadingOffset" : [

			"description",
			"""
			Push the shadow terminator towards the light to hide artifacts on low poly geometry.
			""",

			"layout:section", "Rendering",

		],

		"attributes.shadowTerminatorGeometryOffset" : [

			"description",
			"""
			Offset rays from the surface to reduce shadow terminator artifact on low poly geometry. Only affects triangles at grazing angles to light.
			""",

			"layout:section", "Rendering",

		],

		"attributes.dupliGenerated" : [

			"description",
			"""
			Set a unique position offset. Accessible from a texture_coordinate
			via the generated output plug and from_dupli enabled.
			""",

			"layout:section", "Rendering",
		],

		"attributes.dupliUV" : [

			"description",
			"""
			Set a unique UV offset. Accessible from either a texture_coordinate
			or uv_map node via the UV output plug and from_dupli enabled.
			""",

			"layout:section", "Rendering",
		],

		"attributes.lightGroup" : [

			"description",
			"""
			Set the lightgroup of an object with emission.
			""",

			"layout:section", "Rendering",
		],

		# Subdivision

		"attributes.maxLevel" : [

			"description",
			"""
			The max level of subdivision that can be
			applied.
			""",

			"layout:section", "Subdivision",

		],

		"attributes.dicingScale" : [

			"description",
			"""
			Multiplier for scene dicing rate.
			""",

			"layout:section", "Subdivision",

		],

		# Volume

		"attributes.volumeClipping" : [

			"description",
			"""
			Value under which voxels are considered empty space to
			optimize rendering.
			""",

			"layout:section", "Volume",

		],

		"attributes.volumeStepSize" : [

			"description",
			"""
			Distance between volume samples. When zero it is automatically
			estimated based on the voxel size.
			""",

			"layout:section", "Volume",

		],

		"attributes.volumeObjectSpace" : [

			"description",
			"""
			Specify volume density and step size in object or world space.
			By default object space is used, so that the volume opacity and
			detail remains the same regardless of object scale.
			""",

			"layout:section", "Volume",

		],

		"attributes.assetName" : [

			"description",
			"""
			Asset name for cryptomatte.
			""",

			"layout:section", "Object",

		],

		# Shader

		"attributes.emissionSamplingMethod" : [

			"description",
			"""
			Sampling strategy for emissive surfaces.
			""",

			"layout:section", "Shader",

		],

		"attributes.emissionSamplingMethod.value" : [

			"preset:None", "none",
			"preset:Auto", "auto",
			"preset:Front", "front",
			"preset:Back", "back",
			"preset:Front-Back", "front_back",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"attributes.useTransparentShadow" : [

			"description",
			"""
			Use transparent shadows for this material if it contains a Transparent BSDF,
			disabling will render faster but not give accurate shadows.
			""",

			"layout:section", "Shader",

		],

		"attributes.heterogeneousVolume" : [

			"description",
			"""
			Disabling this when using volume rendering, assume volume has the same density
			everywhere (not using any textures), for faster rendering.
			""",

			"layout:section", "Shader",

		],

		"attributes.volumeSamplingMethod" : [

			"description",
			"""
			Sampling method to use for volumes.
			""",

			"layout:section", "Shader",

		],

		"attributes.volumeSamplingMethod.value" : [

			"preset:Distance", "distance",
			"preset:Equiangular", "equiangular",
			"preset:Multiple-Importance", "multiple_importance",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"attributes.volumeInterpolationMethod" : [

			"description",
			"""
			Interpolation method to use for volumes.
			""",

			"layout:section", "Shader",

		],

		"attributes.volumeInterpolationMethod.value" : [

			"preset:Linear", "linear",
			"preset:Cubic", "cubic",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"attributes.volumeStepRate" : [

			"description",
			"""
			Scale the distance between volume shader samples when rendering the volume
			(lower values give more accurate and detailed results, but also increased render time).
			""",

			"layout:section", "Shader",

		],

		"attributes.displacementMethod" : [

			"description",
			"""
			Method to use for the displacement.
			""",

			"layout:section", "Shader",

		],

		"attributes.displacementMethod.value" : [

			"preset:Bump", "bump",
			"preset:True", "true",
			"preset:Both", "both",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

	}

)
