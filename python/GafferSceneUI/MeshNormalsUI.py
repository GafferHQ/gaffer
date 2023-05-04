##########################################################################
#
#  Copyright (c) 2023, Image Engine Design Inc. All rights reserved.
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
import IECoreScene


Gaffer.Metadata.registerNode(

	GafferScene.MeshNormals,

	"description",
	"""
	Creates a normal primitive variable on a mesh, using the positions of adjacent vertices.
	""",

	"layout:activator:weighting", lambda parent : parent["interpolation"].getValue() != int(IECoreScene.PrimitiveVariable.Interpolation.Uniform),
	"layout:activator:thresholdAngle", lambda parent : parent["interpolation"].getValue() == int(IECoreScene.PrimitiveVariable.Interpolation.FaceVarying),

	plugs = {

		"interpolation" : [
			"description",
			"""
			The interpolation of the normal primitive variable we are creating. Affects the shape of the resulting normals, because Uniform ( Per-Face ) normals are inherently faceted, whereas Vertex normals are always smooth.
			""",

			"preset:Uniform (Faceted)", IECoreScene.PrimitiveVariable.Interpolation.Uniform,
			"preset:Vertex (Smooth)", IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			"preset:FaceVarying (Mixed)", IECoreScene.PrimitiveVariable.Interpolation.FaceVarying,

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
		],

		"weighting" : [
			"description",
			"""
			How to weight the multiple faces that contribute to the normal of a vertex.
			"Equal" averages all faces connected to the vertex - simple to compute, but low quality.
			"Angle" gives good results for most meshes.
			"Area" may give good results on hard edge models with tight chamfers and large flat faces.
			""",

			"preset:Equal", IECoreScene.MeshAlgo.NormalWeighting.Equal,
			"preset:Angle", IECoreScene.MeshAlgo.NormalWeighting.Angle,
			"preset:Area", IECoreScene.MeshAlgo.NormalWeighting.Area,

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

			"layout:activator", "weighting",
		],

		"thresholdAngle" : [
			"description",
			"""
			Used to decide whether edges are smooth or sharp when generating a normal primvar with FaceVarying
			interpolation. FaceVertices with normals that differ by less than this angle will be averaged
			together into a smooth normal.
			""",

			"layout:activator", "thresholdAngle",
		],

		"position" : [
			"description",
			"""
			The name of the position primitive variable that drives everything.
			""",
			"divider", True,
		],

		"normal" : [
			"description",
			"""
			The name of the normal primitive variable to output.
			""",
		]
	}

)
