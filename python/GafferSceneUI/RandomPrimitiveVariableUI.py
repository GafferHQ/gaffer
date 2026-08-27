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
#      * Neither the name of Image Engine Design Inc nor the names of
#        any other contributors to this software may be used to endorse or
#        promote products derived from this software without specific prior
#        written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
#  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
#  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
#  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAinclude/GafferScene/RandomPrimitiveVariable.inlL, SPECIAL,
#  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
##########################################################################

import IECore
import IECoreScene

import Gaffer
import GafferScene

Gaffer.Metadata.registerNode(

	GafferScene.RandomPrimitiveVariable,

	"description",
	"""
	Creates a primitive variable containing random values, with a
	variety of possible distributions.
	""",

	"layout:activator:nameIsP", lambda node : node["name"].getValue() == "P",
	"layout:activator:distributionIsUniformInt", lambda node : node["distribution"].getValue() == GafferScene.RandomPrimitiveVariable.Distribution.UniformInt,
	"layout:activator:distributionIsUniformFloat", lambda node : node["distribution"].getValue() == GafferScene.RandomPrimitiveVariable.Distribution.UniformFloat,
	"layout:activator:distributionIsGaussian", lambda node : node["distribution"].getValue() == GafferScene.RandomPrimitiveVariable.Distribution.Gaussian,
	"layout:activator:distributionIsHollowSphere", lambda node : node["distribution"].getValue() == GafferScene.RandomPrimitiveVariable.Distribution.HollowSphere,

	"layout:customWidget:setupButton:widgetType", "GafferUI.PlugCreationWidget",
	"layout:customWidget:setupButton:section", "Settings",
	"layout:customWidget:setupButton:index", 8,
	"layout:customWidget:setupButton:visibilityActivator", lambda node : (
		node["distribution"].getValue() == GafferScene.RandomPrimitiveVariable.Distribution.WeightedChoice and
		"values" not in node["choices"]
	),
	"plugCreationWidget:action", "setup",
	"plugCreationWidget:includedTypes", "Gaffer.BoolVectorDataPlug Gaffer.FloatVectorDataPlug Gaffer.IntVectorDataPlug Gaffer.StringVectorDataPlug Gaffer.V2iVectorDataPlug Gaffer.V3fVectorDataPlug Gaffer.Color3fVectorDataPlug",
	"plugCreationWidget:useGeometricInterpretation", True,

	plugs = {

		"name" : {

			"description" :
			"""
			The name of the primitive variable to be created.
			""",

		},

		"adjustBounds" : {

			# This is really esoteric, so hide it completely unless the
			# user really is deforming the object.
			"layout:visibilityActivator" : "nameIsP",
			# And put it directly under the name, to clue people in to
			# why it is activated.
			"layout:index" : 3,

		},

		"interpolation" : {

			"description" :
			"""
			The interpolation of the primitive variable to be created.
			Uniform interpolation yields a value per face for meshes and
			a value per curve for curves.
			""",

			"preset:Uniform" : IECoreScene.PrimitiveVariable.Interpolation.Uniform,
			"preset:Vertex" : IECoreScene.PrimitiveVariable.Interpolation.Vertex,

			"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",

		},

		"seed" : {

			"description" :
			"""
			Seed used to generate the random values. Change this to
			generate a different set of values from the same inputs.
			""",

		},

		"seedPrimitiveVariable" : {

			"description" :
			"""
			The name of a primitive variable used to seed the randomness
			on a per-value basis. Must have the same interpolation as the
			primitive variable being created.

			This is useful for maintaining stable output under changing inputs.
			For example, an `id` primitive variable could be used to provide
			stable results for individual points across a particle simulation where
			points are added and removed over time. Or `P` could be used to provide
			stable results when point order changes.
			""",

			"divider" : True,

		},

		"distribution" : {

			"description" :
			"""
			The distribution used to generate the random values. This also
			dictates the type of primitive variable created.

			- Uniform Int : Generates `IntVectorData`, uniformly distributed
			  between `intRange[0]` and `intRange[1]`.
			- Uniform Float : Generates `FloatVectorData`, uniformly distributed
			  between `floatRange[0]` and `floatRange[1]`.
			- Gaussian : Generates `FloatVectorData`, normally distributed around
			  `mean` with the given `deviation`.
			- Weighted Choice : Chooses from a fixed number of potential values,
			  each weighted by a probability. Supported value types are bool, int,
			  float, string, V2i, V3f and Color3f.
			- Hollow Sphere : Generates `V3fVectorData`, uniformly distributed on
			  the surface of a sphere of the given `radius`.
			""",

			"preset:Uniform Int" : GafferScene.RandomPrimitiveVariable.Distribution.UniformInt,
			"preset:Uniform Float" : GafferScene.RandomPrimitiveVariable.Distribution.UniformFloat,
			"preset:Gaussian" : GafferScene.RandomPrimitiveVariable.Distribution.Gaussian,
			"preset:Weighted Choice" : GafferScene.RandomPrimitiveVariable.Distribution.WeightedChoice,
			"preset:Hollow Sphere" : GafferScene.RandomPrimitiveVariable.Distribution.HollowSphere,

			"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",

		},

		"intRange" : {

			"description" :
			"""
			The range of values generated by the `Uniform Int` distribution,
			inclusive of both ends.
			""",

			"layout:visibilityActivator" : "distributionIsUniformInt",

		},

		"floatRange" : {

			"description" :
			"""
			The range of values generated by the `Uniform Float` distribution.
			""",

			"layout:visibilityActivator" : "distributionIsUniformFloat",

		},

		"mean" : {

			"description" :
			"""
			The mean of the `Gaussian` distribution.
			""",

			"layout:visibilityActivator" : "distributionIsGaussian",

		},

		"deviation" : {

			"description" :
			"""
			The standard deviation of the `Gaussian` distribution.
			""",

			"layout:visibilityActivator" : "distributionIsGaussian",

		},

		"choices" : {

			"description" :
			"""
			The choices that will be randomly selected between based on the seed.
			These are specified as a list of values and a corresponding list of
			weights.
			""",

			"plugValueWidget:type" : "GafferUI.VectorDataPlugValueWidget",
			"layout:visibilityActivator" : lambda plug : (
				plug.parent()["distribution"].getValue() == GafferScene.RandomPrimitiveVariable.Distribution.WeightedChoice and
				"values" in plug
			),

		},

		"choices.values" : {

			"description" :
			"""
			The list of values for the choices. Use the `choices.weights` plug
			to assign a relative probability to each choice.
			""",

			"vectorDataPlugValueWidget:header" : "Value",

		},

		"choices.weights" : {

			"description" :
			"""
			The list of weights for the choices. Choices with a higher weight
			have a greater chance of being chosen.
			""",

			"vectorDataPlugValueWidget:header" : "Weight",
			"vectorDataPlugValueWidget:index" : -1,
			"vectorDataPlugValueWidget:elementDefaultValue" : 1.0,

		},

		"radius" : {

			"description" :
			"""
			The radius of the sphere used by the `Hollow Sphere` distribution.
			""",

			"layout:visibilityActivator" : "distributionIsHollowSphere",

		},

		"interpretation" : {

			"description" :
			"""
			The geometric interpretation of the data generated by the `Hollow
			Sphere` distribution. This determines how it is transformed by
			downstream nodes.
			""",

			"preset:Point" : IECore.GeometricData.Interpretation.Point,
			"preset:Normal" : IECore.GeometricData.Interpretation.Normal,
			"preset:Vector" : IECore.GeometricData.Interpretation.Vector,

			"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",

			"layout:visibilityActivator" : "distributionIsHollowSphere",

		},

	}

)
