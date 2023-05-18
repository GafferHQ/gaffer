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

Gaffer.Metadata.registerNode(

	GafferScene.Scatter,

	"description",
	"""
	Scatters points evenly over the surface of meshes.
	This can be particularly useful in conjunction with
	the Instancer, which can then apply instances to
	each point.
	""",

	plugs = {

		"parent" : [

			"description",
			"""
			The location of the mesh to scatter the
			points over. The generated points will
			be parented under this location. This is
			ignored when a filter is connected, in
			which case the filter may specify multiple
			locations containing meshes to scatter points
			over.
			""",

		],

		"name" : [

			"description",
			"""
			The name given to the object generated -
			this will be placed under the parent in
			the scene hierarchy.
			""",

		],

		"density" : [

			"description",
			"""
			The number of points per unit area of the mesh,
			measured in object space.
			""",

		],

		"densityPrimitiveVariable" : [

			"description",
			"""
			A float primitive variable used to specify a varying
			point density across the surface of the mesh. Multiplied
			with the density setting above.
			""",

			"divider", True,
		],

		"referencePosition" : [

			"description",
			"""
			If you want to preserve the uv positions of the points while the mesh animates, you can
			set up an alternate reference position primitive variable ( usually the same as P, but
			not animated ).  This primitive variable will be used to compute the areas of the faces,
			and therefore how many points each face receives.
			""",

		],

		"uv" : [

			"description",
			"""
			The UV set used to distribute points. The size of faces in 3D space is used to determine
			the number of points on each face, so the UV set should not affect the overall look of
			the distribution for a particular seed, but using the UVs provides continuity when
			adjusting density. If polygons that are large in 3D space are small and narrow in UV
			space for the given UV set, you may encounter performance problems.
			""",

			"divider", True,
		],

		"primitiveVariables" : [

			"description",
			"""
			Primitive variables to sample from the source mesh and output on the generated points.
			Supports a Gaffer match pattern, with multiple space seperated variable names, optionally
			using `*` as a wildcard.
			""",

		],

		"pointType" : [

			"description",
			"""
			The render type of the points. This defaults to
			"gl:point" so that the points are rendered in a
			lightweight manner in the viewport.
			""",

			"preset:GL Point", "gl:point",
			"preset:Particle", "particle",
			"preset:Sphere", "sphere",
			"preset:Disk", "disk",
			"preset:Patch", "patch",
			"preset:Blobby", "blobby",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"destination" : [

			"description",
			"""
			The location where the points primitives will be placed in the output scene.
			When the destination is evaluated, the `${scene:path}` variable holds
			the location of the source mesh, so the default value parents the points
			under the mesh.

			> Tip : `${scene:path}/..` may be used to place the points alongside the
			> source mesh.
			""",

		],

	}

)
