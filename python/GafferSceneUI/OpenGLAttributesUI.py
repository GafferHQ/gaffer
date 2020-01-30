##########################################################################
#
#  Copyright (c) 2012-2013, Image Engine Design Inc. All rights reserved.
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
import GafferScene

##########################################################################
# Metadata
##########################################################################

def __drawingSummary( plug ) :

	info = []
	for name, label in (

		( "Solid", "Shaded" ),
		( "Wireframe", "Wireframe" ),
		( "Outline", "Outline" ),
		( "Point", "Point" ),
		( "Bound", "Bound" ),

	) :

		values = []
		if plug["primitive"+name]["enabled"].getValue() :
			values.append( "On" if plug["primitive"+name]["value"].getValue() else "Off" )
		if name != "Solid" and plug["primitive"+name+"Color"]["enabled"].getValue() :
			values.append( "Color" )
		if name != "Solid" and name != "Bound" and plug["primitive"+name+"Width"]["enabled"].getValue() :
			values.append( "%0gpx" % plug["primitive"+name+"Width"]["value"].getValue() )

		if values :
			info.append( label + " : " + "/".join( values ) )

	return ", ".join( info )

def __pointsPrimitivesSummary( plug ) :

	info = []
	if plug["pointsPrimitiveUseGLPoints"]["enabled"].getValue() :
		info.append( "Points On" if plug["pointsPrimitiveUseGLPoints"]["value"].getValue() else "Points Off" )
	if plug["pointsPrimitiveGLPointWidth"]["enabled"].getValue() :
		info.append( "Width %0gpx" % plug["pointsPrimitiveGLPointWidth"]["value"].getValue() )

	return ", ".join( info )

def __curvesPrimitivesSummary( plug ) :

	info = []
	if plug["curvesPrimitiveUseGLLines"]["enabled"].getValue() :
		info.append( "Lines On" if plug["curvesPrimitiveUseGLLines"]["value"].getValue() else "Lines Off" )
	if plug["curvesPrimitiveGLLineWidth"]["enabled"].getValue() :
		info.append( "Width %0gpx" % plug["curvesPrimitiveGLLineWidth"]["value"].getValue() )
	if plug["curvesPrimitiveIgnoreBasis"]["enabled"].getValue() :
		info.append( "Basis Ignored" if plug["curvesPrimitiveIgnoreBasis"]["value"].getValue() else "Basis On" )

	return ", ".join( info )

Gaffer.Metadata.registerNode(

	GafferScene.OpenGLAttributes,

	"description",
	"""
	Applies attributes to modify the appearance of objects in
	the viewport and in renders done by the OpenGLRender node.
	""",

	plugs = {

		# Section summaries

		"attributes" : [

			"layout:section:Drawing:summary", __drawingSummary,
			"layout:section:Points Primitives:summary", __pointsPrimitivesSummary,
			"layout:section:Curves Primitives:summary", __curvesPrimitivesSummary,

		],

		# General drawing plugs

		"attributes.primitiveSolid" : [

			"description",
			"""
			Whether or not the object is rendered solid, in which
			case the assigned GLSL shader will be used to perform
			the shading.
			""",

			"layout:section", "Drawing",
			"label", "Shaded",

		],

		"attributes.primitiveWireframe" : [

			"description",
			"""
			Whether or not the object is rendered as a wireframe.
			Use the primitiveWireframeColor and primitiveWireframeWidth
			plugs for finer control of the wireframe appearance.
			""",

			"layout:section", "Drawing",
			"label", "Wireframe",

		],

		"attributes.primitiveWireframeColor" : [

			"description",
			"""
			The colour to use for the wireframe rendering. Only
			meaningful if wireframe rendering is turned on.
			""",

			"layout:section", "Drawing",
			"label", "Wireframe Color",

		],

		"attributes.primitiveWireframeWidth" : [

			"description",
			"""
			The width in pixels of the wireframe rendering. Only
			meaningful if wireframe rendering is turned on.
			""",

			"layout:section", "Drawing",
			"label", "Wireframe Width",

		],

		"attributes.primitiveOutline" : [

			"description",
			"""
			Whether or not an outline is drawn around the object.
			Use the primitiveOutlineColor and primitiveOutlineWidth
			plugs for finer control of the outline.
			""",

			"layout:section", "Drawing",
			"label", "Outline",

		],

		"attributes.primitiveOutlineColor" : [

			"description",
			"""
			The colour to use for the outline. Only
			meaningful if outline rendering is turned on.
			""",

			"layout:section", "Drawing",
			"label", "Outline Color",

		],

		"attributes.primitiveOutlineWidth" : [

			"description",
			"""
			The width in pixels of the outline. Only
			meaningful if outline rendering is turned on.
			""",

			"layout:section", "Drawing",
			"label", "Outline Width",

		],

		"attributes.primitivePoint" : [

			"description",
			"""
			Whether or not the individual points (vertices) of the
			object are drawn. Use the primitivePointColor and primitivePointWidth
			plugs for finer control of the point rendering.
			""",

			"layout:section", "Drawing",
			"label", "Points",

		],

		"attributes.primitivePointColor" : [

			"description",
			"""
			The colour to use for the point rendering. Only
			meaningful if point rendering is turned on.
			""",

			"layout:section", "Drawing",
			"label", "Point Color",

		],

		"attributes.primitivePointWidth" : [

			"description",
			"""
			The width in pixels of the points. Only
			meaningful if point rendering is turned on.
			""",

			"layout:section", "Drawing",
			"label", "Point Width",

		],

		"attributes.primitiveBound" : [

			"description",
			"""
			Whether or not the bounding box of the object is drawn.
			This is in addition to any drawing of unexpanded bounding
			boxes that the viewer performs. Use the primitiveBoundColor
			plug to change the colour of the bounding box.
			""",

			"layout:section", "Drawing",
			"label", "Bound",

		],

		"attributes.primitiveBoundColor" : [

			"description",
			"""
			The colour to use for the bounding box rendering. Only
			meaningful if bounding box rendering is turned on.
			""",

			"layout:section", "Drawing",
			"label", "Bound Color",

		],

		# Points primitive drawing plugs

		"attributes.pointsPrimitiveUseGLPoints" : [

			"description",
			"""
			Points primitives have a render type (set by the PointsType
			node) which allows them to be rendered as particles, disks,
			spheres etc. This attribute overrides that type for OpenGL
			only, allowing a much faster rendering as raw OpenGL points.
			""",

			"layout:section", "Points Primitives",
			"label", "Use GL Points",

		],

		"attributes.pointsPrimitiveUseGLPoints.value" : [

			"preset:For GL Points", "forGLPoints",
			"preset:For Particles And Disks", "forParticlesAndDisks",
			"preset:For All", "forAll",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"attributes.pointsPrimitiveGLPointWidth" : [

			"description",
			"""
			The width in pixels of the GL points rendered when
			the pointsPrimitiveUseGLPoints plug has overridden
			the point type.
			""",

			"layout:section", "Points Primitives",
			"label", "GL Point Width",

		],

		# Curves primitive drawing plugs

		"attributes.curvesPrimitiveUseGLLines" : [

			"description",
			"""
			Curves primitives are typically rendered as ribbons
			and as such have an associated width in object space.
			This attribute overrides that for OpenGL only, allowing
			a much faster rendering as raw OpenGL lines.
			""",

			"layout:section", "Curves Primitives",
			"label", "Use GL Lines",

		],

		"attributes.curvesPrimitiveGLLineWidth" : [

			"description",
			"""
			The width in pixels of the GL lines rendered when
			the curvesPrimitiveUseGLLines plug has overridden
			the drawing to use lines.
			""",

			"layout:section", "Curves Primitives",
			"label", "GL Line Width",

		],

		"attributes.curvesPrimitiveIgnoreBasis" : [

			"description",
			"""
			Turns off interpolation for cubic curves, just
			rendering straight lines between the vertices
			instead.
			""",

			"layout:section", "Curves Primitives",
			"label", "Ignore Basis",

		],

		"attributes.visualiserScale" : [

			"description",
			"""
			Scales non-geometric visualisations in the viewport to make them
			easier to work with.
			""",

			"layout:section", "Visualisers",
			"label", "Scale",

		],

		"attributes.visualiserMaxTextureResolution" : [

			"description",
			"""
			Visualisers that load textures will respect this setting to
			limit their resolution.
			""",

			"layout:section", "Visualisers",
			"label", "Max Texture Resolution",

		],

		"attributes.visualiserFrustum" : [

			"description",
			"""
			Controls whether applicable locations draw a representation of
			their projection or frustum.
			""",

			"layout:section", "Visualisers",
			"label", "Frustum",

		],

		"attributes.lightDrawingMode" : [

			"description",
			"""
			Controls how lights are presented in the Viewer.
			""",

			"layout:section", "Visualisers",
			"label", "Light Drawing Mode",

		],

		"attributes.lightDrawingMode.value" : [

			"preset:Wireframe", "wireframe",
			"preset:Color", "color",
			"preset:Texture", "texture",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget"

		],

		"attributes.lightFrustumScale" : [

			"description",
			"""
			Allows light projections to be scaled to better suit the scene.
			""",

			"layout:section", "Visualisers",
		],


	}

)
