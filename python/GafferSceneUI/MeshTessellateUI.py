##########################################################################
#
#  Copyright (c) 2024, Image Engine Design Inc. All rights reserved.
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
import GafferScene
import GafferScene.Private.IECoreScenePreview.MeshAlgo as MeshAlgo

import IECoreScene


Gaffer.Metadata.registerNode(

	GafferScene.MeshTessellate,

	"description",
	"""
	Tessellates meshes according to their subdivision scheme, converting them into higher polygon meshes
	which follow the limit surface - usually the smooth regular quads of a Catmull-Clark scheme.

	Can be used similiarly to "subdivide" or "smooth" features in other packages, with one distinction:
	because it puts output points directly on the limit surface, using the tessellated result as a subdiv
	surface again will result in the surface shrinking. Tessellation gives the most accurate possible result
	for a given number of divisions in one step, but is not appropriate for doing repeated operations on
	the same mesh.

	This node implements the tessellation schemes described by OpenSubdiv, as described here:
	https://graphics.pixar.com/opensubdiv/docs/bfr_overview.html#bfr-navlink-tessellation
	( Note that OpenSubdiv's "tessellation rate" parameter is the same as our "divisions" parameter,
	except "tessellation rate" is one higher than "divisions. )

	""",

	"layout:activator:schemeNotOverridden", lambda node : node["scheme"].getValue() == "",

	plugs = {
		"divisions" : [
			"description",
			"""
			The number of vertices to insert in each edge during tessellation.
			""",
		],
		"calculateNormals" : [
			"description",
			"""
			Calculate normals based on the limit surface. If there are existing normals, they will be
			overwritten. If this is not set, existing normals will be interpolated like any other primvar.

			Note that we currently output Vertex normals, which makes sense for most subdivs, but does not
			accurately capture infinitely sharp creases.
			""",
		],
		"scheme" : [
			"description",
			"""
			Overrides the subdivision scheme that determines the shape of the surface. By default, the
			subdivision scheme used comes from the mesh's interpolation property, which should be set with
			a MeshType node, so it will apply to rendering the surface, and also this node. Overriding is
			useful if a mesh has not been tagged correctly ( for example, if you want to force a mesh
			to be smooth, you can set scheme to CatmullClark ).
			""",
			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
			"preset:From Mesh", "",
			"preset:Bilinear", "bilinear",
			"preset:Catmull-Clark", "catmullClark",
			"preset:Loop", "loop",
		],
		"tessellatePolygons" : [
			"description",
			"""
			Force bilinear tessellation of meshes without subdivision schemes.

			If there is no subdivision scheme stored on the mesh ( `interpolation = "linear"` ), and you
			haven't overridden the scheme, we interpret that to mean no tessellation is required. Bilinear
			tessellation won't change the shape of the surface, but sometimes forcing tessellation is useful
			anyways ( for example, to apply deformation on a denser mesh ).
			""",
			"layout:activator", "schemeNotOverridden",
		],
		"interpolateBoundary" : [

			"description",
			"""
			Specifies which parts of mesh boundaries are forced to exactly meet the boundary.
			Without this forcing, a subdivision surface will naturally shrink back from the boundary as it
			smooths out.

			Usually, you want to force both edges and corners to exactly meet the boundary. The main reasons to
			change this are to use `Edge Only` if you want to produce curved edges from polygonal boundaries,
			or to use `None` if you're doing something tricky with seamlessly splitting subdiv meshes by
			providing the split meshes with a border of shared polygons in order to get continuous tangents.
			""",

			"preset:From Mesh", "",
			"preset:None", IECoreScene.MeshPrimitive.interpolateBoundaryNone,
			"preset:Edge Only", IECoreScene.MeshPrimitive.interpolateBoundaryEdgeOnly,
			"preset:Edge And Corner", IECoreScene.MeshPrimitive.interpolateBoundaryEdgeAndCorner,

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
		],
		"faceVaryingLinearInterpolation" : [

			# This name is so long it's getting cropped ... better to lose the end than the start.
			"label", "Face Varying Linear Interp..",

			"description",
			"""
			Specifies where face varying primitive variables should use a simple linear interpolation instead
			of being smoothed.

			In order for UVs to correspond to approximately the same texture areas as the original polygons,
			usually you want to, at minimum, pin the outside corners. But pinning the entire boundary causes
			some pretty weird discontinuities, so finding the right compromise is tricky.

			See the OpenSubdiv docs for explanation of the details of options like `Corners Plus 1`:
			https://graphics.pixar.com/opensubdiv/docs/subdivision_surfaces.html#schemes-and-options
			""",

			"preset:From Mesh", "",
			"preset:None", IECoreScene.MeshPrimitive.faceVaryingLinearInterpolationNone,
			"preset:Corners Only", IECoreScene.MeshPrimitive.faceVaryingLinearInterpolationCornersOnly,
			"preset:Corners Plus 1", IECoreScene.MeshPrimitive.faceVaryingLinearInterpolationCornersPlus1,
			"preset:Corners Plus 2", IECoreScene.MeshPrimitive.faceVaryingLinearInterpolationCornersPlus2,
			"preset:Boundaries", IECoreScene.MeshPrimitive.faceVaryingLinearInterpolationBoundaries,
			"preset:All", IECoreScene.MeshPrimitive.faceVaryingLinearInterpolationAll,

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
		],
		"triangleSubdivisionRule" : [

			"description",
			"""
			Option to use a non-standard `Smooth` subdivision rule that provides slightly better results
			at triangular faces in Catmull-Clark meshes than the standard Catmull-Clark algorithm.
			""",

			"preset:From Mesh", "",
			"preset:CatmullClark", IECoreScene.MeshPrimitive.triangleSubdivisionRuleCatmullClark,
			"preset:Smooth", IECoreScene.MeshPrimitive.triangleSubdivisionRuleSmooth,

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
		],
	}

)
