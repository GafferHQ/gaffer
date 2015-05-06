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

## \todo This is getting used in a few places now - maybe put it in one
# place? Maybe a static method on NumericWidget?
def __floatToString( f ) :

	return ( "%.4f" % f ).rstrip( '0' ).rstrip( '.' )

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
		info.append( "Shading Rate %s" % __floatToString( plug["shadingRate"]["value"].getValue() ) )
	if plug["relativeShadingRate"]["enabled"].getValue() :
		info.append( "Relative Shading Rate %s" % __floatToString( plug["relativeShadingRate"]["value"].getValue() ) )
	if plug["matte"]["enabled"].getValue() :
		info.append( "Matte %s" % ( "On" if plug["matte"]["value"].getValue() else "Off" ) )
	if plug["displacementBound"]["enabled"].getValue() :
		info.append( "Displacement Bound %s" % __floatToString( plug["displacementBound"]["value"].getValue() ) )

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
		info.append( "Trace Bias %s" % __floatToString( plug["traceBias"]["value"].getValue() ) )

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

			"layout:section", "Visibility",
			"label", "Camera",

		],

		"attributes.cameraHitMode" : [

			"layout:section", "Visibility",
			"label", "Camera Mode",

		],

		"attributes.cameraHitMode.value" : [

			"preset:Shader", "shader",
			"preset:Primitive", "primitive",

		],

		"attributes.transmissionVisibility" : [

			"layout:section", "Visibility",
			"label", "Transmission",

		],

		"attributes.transmissionHitMode" : [

			"layout:section", "Visibility",
			"label", "Transmission Mode",

		],

		"attributes.transmissionHitMode.value" : [

			"preset:Shader", "shader",
			"preset:Primitive", "primitive",

		],

		"attributes.diffuseVisibility" : [

			"layout:section", "Visibility",
			"label", "Diffuse",

		],

		"attributes.diffuseHitMode" : [

			"layout:section", "Visibility",
			"label", "Diffuse Mode",

		],

		"attributes.diffuseHitMode.value" : [

			"preset:Shader", "shader",
			"preset:Primitive", "primitive",

		],

		"attributes.specularVisibility" : [

			"layout:section", "Visibility",
			"label", "Specular",

		],

		"attributes.specularHitMode" : [

			"layout:section", "Visibility",
			"label", "Specular Mode",

		],

		"attributes.specularHitMode.value" : [

			"preset:Shader", "shader",
			"preset:Primitive", "primitive",

		],

		"attributes.photonVisibility" : [

			"layout:section", "Visibility",
			"label", "Photon",

		],

		"attributes.photonHitMode" : [

			"layout:section", "Visibility",
			"label", "Photon Mode",

		],

		"attributes.photonHitMode.value" : [

			"preset:Shader", "shader",
			"preset:Primitive", "primitive",

		],

		# Shading section

		"attributes.shadingRate" : [

			"layout:section", "Shading",

		],

		"attributes.relativeShadingRate" : [

			"layout:section", "Shading",

		],

		"attributes.matte" : [

			"layout:section", "Shading",

		],


		"attributes.displacementBound" : [

			"layout:section", "Shading",

		],

		# Raytracing section

		"attributes.maxDiffuseDepth" : [

			"layout:section", "Raytracing",

		],

		"attributes.maxSpecularDepth" : [

			"layout:section", "Raytracing",

		],

		"attributes.traceDisplacements" : [

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

GafferUI.PlugValueWidget.registerCreator(
	GafferRenderMan.RenderManAttributes,
	"attributes.cameraHitMode.value",
	GafferUI.PresetsPlugValueWidget
)

GafferUI.PlugValueWidget.registerCreator(
	GafferRenderMan.RenderManAttributes,
	"attributes.transmissionHitMode.value",
	GafferUI.PresetsPlugValueWidget
)

GafferUI.PlugValueWidget.registerCreator(
	GafferRenderMan.RenderManAttributes,
	"attributes.transmissionHitMode.value",
	GafferUI.PresetsPlugValueWidget
)

GafferUI.PlugValueWidget.registerCreator(
	GafferRenderMan.RenderManAttributes,
	"attributes.diffuseHitMode.value",
	GafferUI.PresetsPlugValueWidget
)

GafferUI.PlugValueWidget.registerCreator(
	GafferRenderMan.RenderManAttributes,
	"attributes.specularHitMode.value",
	GafferUI.PresetsPlugValueWidget
)

GafferUI.PlugValueWidget.registerCreator(
	GafferRenderMan.RenderManAttributes,
	"attributes.photonHitMode.value",
	GafferUI.PresetsPlugValueWidget
)
