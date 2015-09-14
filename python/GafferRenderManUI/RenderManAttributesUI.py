##########################################################################
#
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
import GafferRenderMan

def __visibilitySummary( plug ) :

	info = []
	for childName, label in (

		( "camera", "Camera" ),
		( "transmission", "Trans" ),
		( "diffuse", "Diff" ),
		( "specular", "Spec" ),
		( "photon", "Photon" )

	)	:
		values = []
		if plug[childName+"Visibility"]["enabled"].getValue() :
			values.append( "On" if plug[childName+"Visibility"]["value"].getValue() else "Off" )
		if plug[childName+"HitMode"]["enabled"].getValue() :
			values.append( plug[childName+"HitMode"]["value"].getValue().capitalize() )
		if values :
			info.append( label + " : " + "/".join( values ) )

	return ", ".join( info )

def __shadingSummary( plug ) :

	info = []
	if plug["shadingRate"]["enabled"].getValue() :
		info.append( "Shading Rate %s" % GafferUI.NumericWidget.valueToString( plug["shadingRate"]["value"].getValue() ) )
	if plug["relativeShadingRate"]["enabled"].getValue() :
		info.append( "Relative Shading Rate %s" % GafferUI.NumericWidget.valueToString( plug["relativeShadingRate"]["value"].getValue() ) )
	if plug["matte"]["enabled"].getValue() :
		info.append( "Matte %s" % ( "On" if plug["matte"]["value"].getValue() else "Off" ) )
	if plug["displacementBound"]["enabled"].getValue() :
		info.append( "Displacement Bound %s" % GafferUI.NumericWidget.valueToString( plug["displacementBound"]["value"].getValue() ) )

	return ", ".join( info )

def __raytracingSummary( plug ) :

	info = []
	if plug["maxDiffuseDepth"]["enabled"].getValue() :
		info.append( "Diffuse Depth %d" % plug["maxDiffuseDepth"]["value"].getValue() )
	if plug["maxSpecularDepth"]["enabled"].getValue() :
		info.append( "Specular Depth %d" % plug["maxSpecularDepth"]["value"].getValue() )
	if plug["traceDisplacements"]["enabled"].getValue() :
		info.append( "Displacements %s" % ( "On" if plug["traceDisplacements"]["value"].getValue() else "Off" ) )
	if plug["traceBias"]["enabled"].getValue() :
		info.append( "Trace Bias %s" % GafferUI.NumericWidget.valueToString( plug["traceBias"]["value"].getValue() ) )

	return ", ".join( info )

Gaffer.Metadata.registerNode(

	GafferRenderMan.RenderManAttributes,

	"description",
	"""
	Applies RenderMan specific attributes to the scene.
	""",

	plugs = {

		# Summaries

		"attributes" : [

			"layout:section:Visibility:summary", __visibilitySummary,
			"layout:section:Shading:summary", __shadingSummary,
			"layout:section:Raytracing:summary", __raytracingSummary,

		],

		# Visibility section

		"attributes.cameraVisibility" : [

			"description",
			"""
			Whether or not objects are visible to the camera.
			An object can be invisible to the camera but still
			appear in reflections and shadows etc. To make an
			object totally invisible, prefer the visibility
			setting provided by the StandardAttributes node.
			""",

			"layout:section", "Visibility",
			"label", "Camera",

		],

		"attributes.cameraHitMode" : [

			"description",
			"""
			Specifies if shading is performed when the object
			is hit by a camera ray, or if the primitive colour
			is used as an approximation instead.
			""",

			"layout:section", "Visibility",
			"label", "Camera Mode",

		],

		"attributes.cameraHitMode.value" : [

			"preset:Shader", "shader",
			"preset:Primitive", "primitive",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"attributes.transmissionVisibility" : [

			"description",
			"""
			Whether or not objects are visible to
			transmission rays. Objects that are
			visible to transmission rays will cast
			shadows, and those that aren't won't.
			""",

			"layout:section", "Visibility",
			"label", "Transmission",

		],

		"attributes.transmissionHitMode" : [

			"description",
			"""
			Specifies if shading is performed when the object
			is hit by a tranmission ray, or if the primitive opacity
			is used as an approximation instead.
			""",

			"layout:section", "Visibility",
			"label", "Transmission Mode",

		],

		"attributes.transmissionHitMode.value" : [

			"preset:Shader", "shader",
			"preset:Primitive", "primitive",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"attributes.diffuseVisibility" : [

			"description",
			"""
			Whether or not objects are visible to
			diffuse rays - typically this means whether
			or not they cast occlusion and bounce light.
			""",

			"layout:section", "Visibility",
			"label", "Diffuse",

		],

		"attributes.diffuseHitMode" : [

			"description",
			"""
			Specifies if shading is performed when the object
			is hit by a diffuse ray, or if the primitive colour
			is used as an approximation instead.
			""",

			"layout:section", "Visibility",
			"label", "Diffuse Mode",

		],

		"attributes.diffuseHitMode.value" : [

			"preset:Shader", "shader",
			"preset:Primitive", "primitive",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"attributes.specularVisibility" : [

			"description",
			"""
			Whether or not objects are visible to
			specular rays - typically this means whether
			or not they are visible in reflections and
			refractions.
			""",

			"layout:section", "Visibility",
			"label", "Specular",

		],

		"attributes.specularHitMode" : [

			"description",
			"""
			Specifies if shading is performed when the object
			is hit by a specular ray, or if the primitive colour
			is used as an approximation instead.
			""",

			"layout:section", "Visibility",
			"label", "Specular Mode",

		],

		"attributes.specularHitMode.value" : [

			"preset:Shader", "shader",
			"preset:Primitive", "primitive",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"attributes.photonVisibility" : [

			"description",
			"""
			Whether or not objects are visible to
			photons.
			""",

			"layout:section", "Visibility",
			"label", "Photon",

		],

		"attributes.photonHitMode" : [

			"description",
			"""
			Specifies if shading is performed when the object
			is hit by a photon, or if the primitive colour
			is used as an approximation instead.
			""",

			"layout:section", "Visibility",
			"label", "Photon Mode",

		],

		"attributes.photonHitMode.value" : [

			"preset:Shader", "shader",
			"preset:Primitive", "primitive",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		# Shading section

		"attributes.shadingRate" : [

			"description",
			"""
			Specifies how finely objects are diced before they
			are shaded. Smaller values give higher quality but
			slower rendering.
			""",

			"layout:section", "Shading",

		],

		"attributes.relativeShadingRate" : [

			"description",
			"""
			Specifies a multiplier on the shading rate. Note that
			if shading rate is specified at multiple locations above
			an object in the hierarchy, they are multiplied together
			to arrive at the final shading rate.
			""",

			"layout:section", "Shading",

		],

		"attributes.matte" : [

			"description",
			"""
			Matte objects don't appear in the render, but cut holes
			in the alpha of all objects behind them.
			""",

			"layout:section", "Shading",

		],


		"attributes.displacementBound" : [

			"description",
			"""
			Specifies the maximum amount the displacement shader will
			displace by.
			""",

			"layout:section", "Shading",

		],

		# Raytracing section

		"attributes.maxDiffuseDepth" : [

			"description",
			"""
			The maximum depth for diffuse ray bounces.
			""",

			"layout:section", "Raytracing",

		],

		"attributes.maxSpecularDepth" : [

			"description",
			"""
			The maximum depth for specular (reflection) ray bounces.
			""",

			"layout:section", "Raytracing",

		],

		"attributes.traceDisplacements" : [

			"description",
			"""
			Whether or not displacements are taken into account
			when raytracing. This can be fairly expensive.
			""",

			"layout:section", "Raytracing",

		],

		"attributes.traceBias" : [

			"description",
			"""
			This bias value affects rays. It is an offset applied to the ray origin, moving it slightly away from the surface launch point in the ray direction. This offset can prevent blotchy artifacts resulting from the ray immediately finding an intersection with the surface it just left. Usually, 0.01 is the default scene value.
			""",

			"layout:section", "Raytracing",

		],

	}

)
