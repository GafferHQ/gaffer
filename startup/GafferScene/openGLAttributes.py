##########################################################################
#
#  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
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

import imath

import IECore

import Gaffer

Gaffer.Metadata.registerValues( {

	"attribute:gl:primitive:solid" : {

		"defaultValue" : True,
		"description" :
		"""
		Whether or not the object is rendered solid, in which
		case the assigned GLSL shader will be used to perform
		the shading.
		""",
		"label" : "Shaded",
		"layout:section" : "Drawing",

	},

	"attribute:gl:primitive:wireframe" : {

		"defaultValue" : False,
		"description" :
		"""
		Whether or not the object is rendered as a wireframe.
		Use the `gl:primitive:wireframeColor` and `gl:primitive:wireframeWidth`
		attributes for finer control of the wireframe appearance.
		""",
		"label" : "Wireframe",
		"layout:section" : "Drawing",

	},

	"attribute:gl:primitive:wireframeColor" : {

		"defaultValue" : imath.Color4f( 0.2, 0.2, 0.2, 1.0 ),
		"description" :
		"""
		The colour to use for the wireframe rendering. Only
		meaningful if wireframe rendering is turned on.
		""",
		"label" : "Wireframe Color",
		"layout:section" : "Drawing",

	},

	"attribute:gl:primitive:wireframeWidth" : {

		"defaultValue" : 1.0,
		"minValue" : 0.1,
		"maxValue" : 32.0,
		"description" :
		"""
		The width in pixels of the wireframe rendering. Only
		meaningful if wireframe rendering is turned on.
		""",
		"label" : "Wireframe Width",
		"layout:section" : "Drawing",

	},

	"attribute:gl:primitive:outline" : {

		"defaultValue" : False,
		"description" :
		"""
		Whether or not an outline is drawn around the object.
		Use the `gl:primitive:outlineColor` and `gl:primitive:outlineWidth`
		attributes for finer control of the outline.
		""",
		"label" : "Outline",
		"layout:section" : "Drawing",

	},

	"attribute:gl:primitive:outlineColor" : {

		"defaultValue" : imath.Color4f( 0.85, 0.75, 0.45, 1.0 ),
		"description" :
		"""
		The colour to use for the outline. Only
		meaningful if outline rendering is turned on.
		""",
		"label" : "Outline Color",
		"layout:section" : "Drawing",

	},

	"attribute:gl:primitive:outlineWidth" : {

		"defaultValue" : 1.0,
		"description" :
		"""
		The width in pixels of the outline. Only
		meaningful if outline rendering is turned on.
		""",
		"label" : "Outline Width",
		"layout:section" : "Drawing",

	},

	"attribute:gl:primitive:points" : {

		"defaultValue" : False,
		"description" :
		"""
		Whether or not the individual points (vertices) of the
		object are drawn. Use the `gl:primitive:pointColor` and
		`gl:primitive:pointWidth` attributes for finer control
		of the point rendering.
		""",
		"label" : "Points",
		"layout:section" : "Drawing",

	},

	"attribute:gl:primitive:pointColor" : {

		"defaultValue" : imath.Color4f( 1 ),
		"description" :
		"""
		The colour to use for the point rendering. Only
		meaningful if point rendering is turned on.
		""",
		"label" : "Point Color",
		"layout:section" : "Drawing",

	},

	"attribute:gl:primitive:pointWidth" : {

		"defaultValue" : 1.0,
		"description" :
		"""
		The width in pixels of the points. Only
		meaningful if point rendering is turned on.
		""",
		"label" : "Point Width",
		"layout:section" : "Drawing",

	},

	"attribute:gl:primitive:bound" : {

		"defaultValue" : False,
		"description" :
		"""
		Whether or not the bounding box of the object is drawn.
		This is in addition to any drawing of unexpanded bounding
		boxes that the viewer performs. Use the `gl:primitive:boundColor`
		attribute to change the colour of the bounding box.
		""",
		"label" : "Bound",
		"layout:section" : "Drawing",

	},

	"attribute:gl:primitive:boundColor" : {

		"defaultValue" : imath.Color4f( 0.36, 0.8, 0.85, 1.0 ),
		"description" :
		"""
		The colour to use for the bounding box rendering. Only
		meaningful if bounding box rendering is turned on.
		""",
		"label" : "Bound Color",
		"layout:section" : "Drawing",

	},

	"attribute:gl:pointsPrimitive:useGLPoints" : {

		"defaultValue" : "forGLPoints",
		"description" :
		"""
		Points primitives have a render type (set by the PointsType
		node) which allows them to be rendered as particles, disks,
		spheres etc. This attribute overrides that type for OpenGL
		only, allowing a much faster rendering as raw OpenGL points.
		""",
		"label" : "Use GL Points",
		"layout:section" : "Points Primitives",

		"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",
		"presetNames" : IECore.StringVectorData( [ "For GL Points", "For Particles And Disks", "For All" ] ),
		"presetValues" : IECore.StringVectorData( [ "forGLPoints", "forParticlesAndDisks", "forAll" ] ),

	},

	"attribute:gl:pointsPrimitive:glPointWidth" : {

		"defaultValue" : 1.0,
		"minValue" : 0.1,
		"maxValue" : 128.0,
		"description" :
		"""
		The width in pixels of the GL points rendered when
		the `gl:pointsPrimitive:useGLPoints` attribute has
		overridden the point type.
		""",
		"label" : "GL Point Width",
		"layout:section" : "Points Primitives",

	},

	"attribute:gl:curvesPrimitive:useGLLines" : {

		"defaultValue" : False,
		"description" :
		"""
		Curves primitives are typically rendered as ribbons
		and as such have an associated width in object space.
		This attribute overrides that for OpenGL only, allowing
		a much faster rendering as raw OpenGL lines.
		""",
		"label" : "Use GL Lines",
		"layout:section" : "Curves Primitives",

	},

	"attribute:gl:curvesPrimitive:glLineWidth" : {

		"defaultValue" : 1.0,
		"minValue" : 0.1,
		"maxValue" : 32.0,
		"description" :
		"""
		The width in pixels of the GL lines rendered when
		the `gl:pointsPrimitive:useGLLines` attribute has
		overridden the drawing to use lines.
		""",
		"label" : "GL Line Width",
		"layout:section" : "Curves Primitives",

	},

	"attribute:gl:curvesPrimitive:ignoreBasis" : {

		"defaultValue" : False,
		"description" :
		"""
		Turns off interpolation for cubic curves, just
		rendering straight lines between the vertices
		instead.
		""",
		"label" : "Ignore Basis",
		"layout:section" : "Curves Primitives",

	},

	"attribute:gl:visualiser:scale" : {

		"defaultValue" : 1.0,
		"minValue" : 0.01,
		"description" :
		"""
		Scales non-geometric visualisations in the viewport to make them
		easier to work with.
		""",
		"label" : "Scale",
		"layout:section" : "Visualisers",

	},

	"attribute:gl:visualiser:maxTextureResolution" : {

		"defaultValue" : 512,
		"minValue" : 2,
		"maxValue" : 2048,
		"description" :
		"""
		Visualisers that load textures will respect this setting to
		limit their resolution.
		""",
		"label" : "Max Texture Resolution",
		"layout:section" : "Visualisers",

	},

	"attribute:gl:visualiser:frustum" : {

		"defaultValue" : "whenSelected",
		"description" :
		"""
		Controls whether applicable locations draw a representation of
		their projection or frustum.
		""",
		"label" : "Frustum",
		"layout:section" : "Visualisers",

		"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",
		"presetNames" : IECore.StringVectorData( [ "Off", "When Selected", "On" ] ),
		"presetValues" : IECore.StringVectorData( [ "off", "whenSelected", "on" ] ),

	},

	"attribute:gl:light:drawingMode" : {

		"defaultValue" : "texture",
		"description" :
		"""
		Controls how lights are presented in the Viewer.
		""",
		"label" : "Light Drawing Mode",
		"layout:section" : "Visualisers",

		"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",
		"presetNames" : IECore.StringVectorData( [ "Wireframe", "Color", "Texture" ] ),
		"presetValues" : IECore.StringVectorData( [ "wireframe", "color", "texture" ] ),

	},

	"attribute:gl:light:frustumScale" : {

		"defaultValue" : 1.0,
		"minValue" : 0.01,
		"description" :
		"""
		Allows light projections to be scaled to better suit the scene.
		""",
		"label" : "Light Frustum Scale",
		"layout:section" : "Visualisers",

	},

} )

Gaffer.Metadata.registerValue( "attribute:gl:*", "category", "OpenGL" )
