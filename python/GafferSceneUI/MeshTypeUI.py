##########################################################################
#
#  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

import IECoreScene

##########################################################################
# Metadata
##########################################################################

Gaffer.Metadata.registerNode(

	GafferScene.MeshType,

	"description",
	"""
	Changes between polygon and subdivision representations
	for mesh objects, and optionally recalculates vertex
	normals for polygon meshes.

	Note that currently the Gaffer viewport does not display
	subdivision meshes with smoothing, so the results of using
	this node will not be seen until a render is performed.
	""",

	plugs = {

		"meshType" : [

			"description",
			"""
			The interpolation type to apply to the mesh.
			""",

			"preset:Unchanged", "",
			"preset:Polygon", "linear",
			"preset:Subdivision Surface", "catmullClark",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"calculatePolygonNormals" : [

			"description",
			"""
			Causes new vertex normals to be calculated for
			polygon meshes. Has no effect for subdivision
			surfaces, since those are naturally smooth and do
			not require surface normals. Vertex normals are
			represented as primitive variables named "N".
			""",

		],

		"overwriteExistingNormals" : [

			"description",
			"""
			By default, vertex normals will only be calculated for
			polygon meshes which don't already have them. Turning
			this on will force new normals to be calculated even for
			meshes which had them already.
			""",

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

			"preset:Unchanged", "",
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

			"preset:Unchanged", "",
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

			"preset:Unchanged", "",
			"preset:CatmullClark", IECoreScene.MeshPrimitive.triangleSubdivisionRuleCatmullClark,
			"preset:Smooth", IECoreScene.MeshPrimitive.triangleSubdivisionRuleSmooth,

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

	}

)
