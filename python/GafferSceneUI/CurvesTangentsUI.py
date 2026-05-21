##########################################################################
#
#  Copyright (c) 2026, Cinesite VFX Ltd. All rights reserved.
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

Gaffer.Metadata.registerNode(

	GafferScene.CurvesTangents,

	"description",
	"""
	Adds a tangent primitive variable to curves, giving the direction of travel
	along the curve at each vertex position.
	""",

	plugs = {

		"mode" : {

			"description" :
			"""
			The method used to compute the tangents. Each has its pros and cons.

			- CentralDifference (Vertex) : The vector between the previous vertex and the next one.
			  This is well defined for all values of curve basis and wrap, and is identical in
			  direction to the true derivative for CatmullRom curves. Hence it is a good default.
			- Derivative (Varying) : The true derivative of the curve, calculated at the end of each
			  segment. While exact, this is not always useful, due to not being defined at each
			  vertex position. Best used for pinned curves, where Varying and Vertex values are
			  equivalent.
			- FirstDifference (Vertex) : The vector from one vertex to the next. May be of use for
			  linear curves.
			""",

			"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",
			"preset:Central Difference" : GafferScene.CurvesTangents.Mode.CentralDifference,
			"preset:Derivative" : GafferScene.CurvesTangents.Mode.Derivative,
			"preset:First Difference" : GafferScene.CurvesTangents.Mode.FirstDifference,

		},

		"normalize" : {

			"description" :
			"""
			Normalizes the tangents, so they all have unit length.
			""",

		},

		"position" : {

			"description" :
			"""
			The name of the primitive variable containing the positions used to
			compute tangents. Defaults to `P`, but can be set to an alternative
			such as `Pref` to compute tangents from reference positions.
			""",

			"layout:section" : "Settings.Input",

		},

		"tangent" : {

			"description" :
			"""
			The name of the output primitive variable that will contain the
			computed tangent vectors.
			""",

			"layout:section" : "Settings.Output",

		},

	}

)
