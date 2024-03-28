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


Gaffer.Metadata.registerNode(

	GafferScene.MeshTessellate,

	"description",
	"""
	Subdivides a mesh.
	""",

	plugs={
		"divisions" : [
			"description",
			"""
			The number of vertices to insert in each edge during tessellation. This corresponds to OpenSubdiv's
			"tessellation rate" control, except that tessellation rate is one higher. Divisions == 3 inserts 3
			new vertices into each edge, so one cage edge becomes 4 tessellated edges.
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
		"tessellatePolygons" : [
			"description",
			"""
			Enables tessellation on meshes tagged as simple polygons ( meshes with interpolation set to linear ).
			This adds more divisions without affecting the shape, since we assume it is meant to use a linear shape.

			If you want smooth interpolation of meshes that are tagged as linear, then you also want to turn on
			this and override the scheme to CatmullClark.
			""",
		],
		"scheme" : [
			"description",
			"""
			Overrides the subdivision scheme that determines thet shape of the surface. By default, the
			subdivision scheme used comes from the mesh's interpolation property. Overriding is useful if
			a mesh has not been tagged correctly ( for example, if a mesh is linearly interpolated, but you
			want it to be smooth, you can turn on tessellatePolygons and set scheme to CatmullClark ).
			""",
			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
			"preset:Default", MeshAlgo.SubdivisionScheme.Default,
			"preset:Bilinear", MeshAlgo.SubdivisionScheme.Bilinear,
			"preset:Catmull-Clark", MeshAlgo.SubdivisionScheme.CatmullClark,
			"preset:Loop", MeshAlgo.SubdivisionScheme.Loop
		],
	}

)
