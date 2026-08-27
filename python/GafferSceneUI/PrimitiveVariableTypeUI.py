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

import IECore

##########################################################################
# Metadata
##########################################################################

Gaffer.Metadata.registerNode(

	GafferScene.PrimitiveVariableType,

	"layout:activator:typeIsGeometric", lambda node : (
		not node["type"]["enabled"].getValue() or
		node["type"]["value"].getValue() in {
			GafferScene.PrimitiveVariableType.ElementType.V2i,
			GafferScene.PrimitiveVariableType.ElementType.V2f,
			GafferScene.PrimitiveVariableType.ElementType.V2d,
			GafferScene.PrimitiveVariableType.ElementType.V3i,
			GafferScene.PrimitiveVariableType.ElementType.V3f,
			GafferScene.PrimitiveVariableType.ElementType.V3d,
		}
	),

	"description",
	"""
	Converts the type and/or geometric interpretation of primitive variables.
	""",

	plugs = {

		"primitiveVariables" : {

			"description" :
			"""
			The names of the primitive variables to be converted. These should be
			separated by spaces and can use Gaffer's standard wildcards to match
			multiple variables.
			""",

		},

		"type" : {

			"description" :
			"""
			The type the primitive variables are converted to.

			Primitive variables are converted using the following rules :

			- Single-component sources, such as `float` or `int`, are applied
			to every component of the destination. For example, a `float` primitive
			variable with a value of `2` is converted to `V2f( 2, 2 )`,
			`V3f/Color3f( 2, 2, 2 )`, and `Color4f( 2, 2, 2, 2 )`.
			- Multi-component sources, such as `V3f` or `Color4f`, are applied
			per-component. Components missing from the destination are dropped,
			and extra components are set to zero. For example, `Color4f( 1, 2, 3, 4 )`
			becomes `V3f/Color3f( 1, 2, 3 )`, `V2f( 1, 2 )`, and `1`. `V2f( 1, 2 )`
			becomes `V3f/Color3f( 1, 2, 0 )`, and `Color4f( 1, 2, 0, 0 )`.
			- Floating point values are truncated towards zero when converted to an
			integer, so `2.75` becomes `2`, and `-2.75` becomes `-2`.
			- Values converted to integer types are clamped to the range of the
			destination type.
			""",

		},

		"type.value" : {

			"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",

			"preset:Float" : GafferScene.PrimitiveVariableType.ElementType.Float,
			"preset:Int" : GafferScene.PrimitiveVariableType.ElementType.Int,
			"preset:V2i" : GafferScene.PrimitiveVariableType.ElementType.V2i,
			"preset:V2f" : GafferScene.PrimitiveVariableType.ElementType.V2f,
			"preset:V3i" : GafferScene.PrimitiveVariableType.ElementType.V3i,
			"preset:V3f" : GafferScene.PrimitiveVariableType.ElementType.V3f,
			"preset:Color3f" : GafferScene.PrimitiveVariableType.ElementType.Color3f,
			"preset:Color4f" : GafferScene.PrimitiveVariableType.ElementType.Color4f,

			"preset:Other/UChar" : GafferScene.PrimitiveVariableType.ElementType.UChar,
			"preset:Other/UInt" : GafferScene.PrimitiveVariableType.ElementType.UInt,
			"preset:Other/Int64" : GafferScene.PrimitiveVariableType.ElementType.Int64,
			"preset:Other/UInt64" : GafferScene.PrimitiveVariableType.ElementType.UInt64,
			"preset:Other/Half" : GafferScene.PrimitiveVariableType.ElementType.Half,
			"preset:Other/Double" : GafferScene.PrimitiveVariableType.ElementType.Double,
			"preset:Other/V2d" : GafferScene.PrimitiveVariableType.ElementType.V2d,
			"preset:Other/V3d" : GafferScene.PrimitiveVariableType.ElementType.V3d,

		},

		"interpretation" : {

			"description" :
			"""
			The geometric interpretation of each primitive variable. Only relevant
			for geometric types, such as `V2f` and `V3f`.

			> Tip : Geometric types converted from non-geometric types, such as
			> `float` and `Color3f`, default to `None` unless an interpretation
			> is chosen here.
			""",

			"layout:activator" : "typeIsGeometric",

		},

		"interpretation.value" : {

			"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",

			"preset:None" : IECore.GeometricData.Interpretation.None_,
			"preset:Point" : IECore.GeometricData.Interpretation.Point,
			"preset:Normal" : IECore.GeometricData.Interpretation.Normal,
			"preset:Vector" : IECore.GeometricData.Interpretation.Vector,
			"preset:Color" : IECore.GeometricData.Interpretation.Color,
			"preset:UV" : IECore.GeometricData.Interpretation.UV,

		},

	}

)
