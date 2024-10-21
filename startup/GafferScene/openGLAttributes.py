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

Gaffer.Metadata.registerValue( "attribute:gl:primitive:solid", "label", "Shaded" )
Gaffer.Metadata.registerValue( "attribute:gl:primitive:solid", "defaultValue", IECore.BoolData( True ) )
Gaffer.Metadata.registerValue(
	"attribute:gl:primitive:solid",
	"description",
	"""
	Whether or not the object is rendered solid, in which
	case the assigned GLSL shader will be used to perform
	the shading.
	"""
)

Gaffer.Metadata.registerValue( "attribute:gl:primitive:wireframe", "label", "Wireframe" )
Gaffer.Metadata.registerValue( "attribute:gl:primitive:wireframe", "defaultValue", IECore.BoolData( False ) )
Gaffer.Metadata.registerValue(
	"attribute:gl:primitive:wireframe",
	"description",
	"""
	Whether or not the object is rendered as a wireframe.
	Use the `gl:primitive:wireframeColor` and `gl:primitive:wireframeWidth`
	attributes for finer control of the wireframe appearance.
	"""
)

Gaffer.Metadata.registerValue( "attribute:gl:primitive:wireframeColor", "label", "Wireframe Color" )
Gaffer.Metadata.registerValue( "attribute:gl:primitive:wireframeColor", "defaultValue", IECore.Color4fData( imath.Color4f( 0.2, 0.2, 0.2, 1.0 ) ) )
Gaffer.Metadata.registerValue(
	"attribute:gl:primitive:wireframeColor",
	"description",
	"""
	The colour to use for the wireframe rendering. Only
	meaningful if wireframe rendering is turned on.
	"""
)

Gaffer.Metadata.registerValue( "attribute:gl:primitive:wireframeWidth", "label", "Wireframe Width" )
Gaffer.Metadata.registerValue( "attribute:gl:primitive:wireframeWidth", "defaultValue", IECore.FloatData( 1 ) )
Gaffer.Metadata.registerValue(
	"attribute:gl:primitive:wireframeWidth",
	"description",
	"""
	The width in pixels of the wireframe rendering. Only
	meaningful if wireframe rendering is turned on.
	"""
)

Gaffer.Metadata.registerValue( "attribute:gl:primitive:outline", "label", "Outline" )
Gaffer.Metadata.registerValue( "attribute:gl:primitive:outline", "defaultValue", IECore.BoolData( False ) )
Gaffer.Metadata.registerValue(
	"attribute:gl:primitive:outline",
	"description",
	"""
	Whether or not an outline is drawn around the object.
	Use the `gl:primitive:outlineColor` and `gl:primitive:outlineWidth`
	attributes for finer control of the outline.
	"""
)

Gaffer.Metadata.registerValue( "attribute:gl:primitive:outlineColor", "label", "Outline Color" )
Gaffer.Metadata.registerValue( "attribute:gl:primitive:outlineColor", "defaultValue", IECore.Color4fData( imath.Color4f( 0.85, 0.75, 0.45, 1.0 ) ) )
Gaffer.Metadata.registerValue(
	"attribute:gl:primitive:outlineColor",
	"description",
	"""
	The colour to use for the outline. Only
	meaningful if outline rendering is turned on.
	"""
)

Gaffer.Metadata.registerValue( "attribute:gl:primitive:outlineWidth", "label", "Outline Width" )
Gaffer.Metadata.registerValue( "attribute:gl:primitive:outlineWidth", "defaultValue", IECore.FloatData( 1 ) )
Gaffer.Metadata.registerValue(
	"attribute:gl:primitive:outlineWidth",
	"description",
	"""
	The width in pixels of the outline. Only
	meaningful if outline rendering is turned on.
	"""
)

Gaffer.Metadata.registerValue( "attribute:gl:primitive:points", "label", "Points" )
Gaffer.Metadata.registerValue( "attribute:gl:primitive:points", "defaultValue", IECore.BoolData( False ) )
Gaffer.Metadata.registerValue(
	"attribute:gl:primitive:points",
	"description",
	"""
	Whether or not the individual points (vertices) of the
	object are drawn. Use the `gl:primitive:pointColor` and
	`gl:primitive:pointWidth` attributes for finer control
	of the point rendering.
	"""
)

Gaffer.Metadata.registerValue( "attribute:gl:primitive:pointColor", "label", "Point Color" )
Gaffer.Metadata.registerValue( "attribute:gl:primitive:pointColor", "defaultValue", IECore.Color4fData( imath.Color4f( 1 ) ) )
Gaffer.Metadata.registerValue(
	"attribute:gl:primitive:pointColor",
	"description",
	"""
	The colour to use for the point rendering. Only
	meaningful if point rendering is turned on.
	"""
)

Gaffer.Metadata.registerValue( "attribute:gl:primitive:pointWidth", "label", "Point Width" )
Gaffer.Metadata.registerValue( "attribute:gl:primitive:pointWidth", "defaultValue", IECore.FloatData( 1 ) )
Gaffer.Metadata.registerValue(
	"attribute:gl:primitive:pointWidth",
	"description",
	"""
	The width in pixels of the points. Only
	meaningful if point rendering is turned on.
	"""
)

Gaffer.Metadata.registerValue( "attribute:gl:primitive:bound", "label", "Bound" )
Gaffer.Metadata.registerValue( "attribute:gl:primitive:bound", "defaultValue", IECore.BoolData( False ) )
Gaffer.Metadata.registerValue(
	"attribute:gl:primitive:bound",
	"description",
	"""
	Whether or not the bounding box of the object is drawn.
	This is in addition to any drawing of unexpanded bounding
	boxes that the viewer performs. Use the `gl:primitive:boundColor`
	attribute to change the colour of the bounding box.
	"""
)

Gaffer.Metadata.registerValue( "attribute:gl:primitive:boundColor", "label", "Bound Color" )
Gaffer.Metadata.registerValue( "attribute:gl:primitive:boundColor", "defaultValue", IECore.Color4fData( imath.Color4f( 0.36, 0.8, 0.85, 1.0 ) ) )
Gaffer.Metadata.registerValue(
	"attribute:gl:primitive:boundColor",
	"description",
	"""
	The colour to use for the bounding box rendering. Only
	meaningful if bounding box rendering is turned on.
	"""
)

Gaffer.Metadata.registerValue( "attribute:gl:pointsPrimitive:useGLPoints", "label", "Use GL Points" )
Gaffer.Metadata.registerValue( "attribute:gl:pointsPrimitive:useGLPoints", "defaultValue", IECore.StringData( "forGLPoints" ) )
Gaffer.Metadata.registerValue(
	"attribute:gl:pointsPrimitive:useGLPoints",
	"description",
	"""
	Points primitives have a render type (set by the PointsType
	node) which allows them to be rendered as particles, disks,
	spheres etc. This attribute overrides that type for OpenGL
	only, allowing a much faster rendering as raw OpenGL points.
	"""
)

Gaffer.Metadata.registerValue( "attribute:gl:pointsPrimitive:glPointWidth", "label", "GL Point Width" )
Gaffer.Metadata.registerValue( "attribute:gl:pointsPrimitive:glPointWidth", "defaultValue", IECore.FloatData( 1 ) )
Gaffer.Metadata.registerValue(
	"attribute:gl:pointsPrimitive:glPointWidth",
	"description",
	"""
	The width in pixels of the GL points rendered when
	the `gl:pointsPrimitive:useGLPoints` attribute has
	overridden the point type.
	"""
)

Gaffer.Metadata.registerValue( "attribute:gl:curvesPrimitive:useGLLines", "label", "Use GL Lines" )
Gaffer.Metadata.registerValue( "attribute:gl:curvesPrimitive:useGLLines", "defaultValue", IECore.BoolData( False ) )
Gaffer.Metadata.registerValue(
	"attribute:gl:curvesPrimitive:useGLLines",
	"description",
	"""
	Curves primitives are typically rendered as ribbons
	and as such have an associated width in object space.
	This attribute overrides that for OpenGL only, allowing
	a much faster rendering as raw OpenGL lines.
	"""
)

Gaffer.Metadata.registerValue( "attribute:gl:curvesPrimitive:glLineWidth", "label", "GL Line Width" )
Gaffer.Metadata.registerValue( "attribute:gl:curvesPrimitive:glLineWidth", "defaultValue", IECore.FloatData( 1 ) )
Gaffer.Metadata.registerValue(
	"attribute:gl:curvesPrimitive:glLineWidth",
	"description",
	"""
	The width in pixels of the GL lines rendered when
	the `gl:pointsPrimitive:useGLLines` attribute has
	overridden the drawing to use lines.
	"""
)

Gaffer.Metadata.registerValue( "attribute:gl:curvesPrimitive:ignoreBasis", "label", "Ignore Basis" )
Gaffer.Metadata.registerValue( "attribute:gl:curvesPrimitive:ignoreBasis", "defaultValue", IECore.BoolData( False ) )
Gaffer.Metadata.registerValue(
	"attribute:gl:curvesPrimitive:ignoreBasis",
	"description",
	"""
	Turns off interpolation for cubic curves, just
	rendering straight lines between the vertices
	instead.
	"""
)

Gaffer.Metadata.registerValue( "attribute:gl:light:drawingMode", "label", "Light Drawing Mode" )
Gaffer.Metadata.registerValue( "attribute:gl:light:drawingMode", "defaultValue", IECore.StringData( "texture" ) )
Gaffer.Metadata.registerValue(
	"attribute:gl:light:drawingMode",
	"description",
	"""
	Controls how lights are presented in the Viewer.
	"""
)

Gaffer.Metadata.registerValue( "attribute:gl:light:frustumScale", "label", "Light Frustum Scale" )
Gaffer.Metadata.registerValue( "attribute:gl:light:frustumScale", "defaultValue", IECore.FloatData( 1 ) )
Gaffer.Metadata.registerValue(
	"attribute:gl:light:frustumScale",
	"description",
	"""
	Allows light projections to be scaled to better suit the scene.
	"""
)

Gaffer.Metadata.registerValue( "attribute:gl:visualiser:frustum", "label", "Frustum" )
Gaffer.Metadata.registerValue( "attribute:gl:visualiser:frustum", "defaultValue", IECore.StringData( "whenSelected" ) )
Gaffer.Metadata.registerValue(
	"attribute:gl:visualiser:frustum",
	"description",
	"""
	Controls whether applicable locations draw a representation of
	their projection or frustum.
	"""
)

Gaffer.Metadata.registerValue( "attribute:gl:visualiser:maxTextureResolution", "label", "Max Texture Resolution" )
Gaffer.Metadata.registerValue( "attribute:gl:visualiser:maxTextureResolution", "defaultValue", IECore.IntData( 512 ) )
Gaffer.Metadata.registerValue(
	"attribute:gl:visualiser:maxTextureResolution",
	"description",
	"""
	Visualisers that load textures will respect this setting to
	limit their resolution.
	"""
)

Gaffer.Metadata.registerValue( "attribute:gl:visualiser:scale", "label", "Scale" )
Gaffer.Metadata.registerValue( "attribute:gl:visualiser:scale", "defaultValue", IECore.FloatData( 1 ) )
Gaffer.Metadata.registerValue(
	"attribute:gl:visualiser:scale",
	"description",
	"""
	Scales non-geometric visualisations in the viewport to make them
	easier to work with.
	"""
)
