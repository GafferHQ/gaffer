##########################################################################
#
#  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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

	GafferScene.CollectTransforms,

	"description",
	"""
	Collects transforms in different Contexts, storing the results as attributes. The
	names of the attributes being collected are provided as a Context Variable,
	which can be used to vary the transforms that are collected.

	By combining this with a TimeWarp, you can create copies of
	the transform at different times, useful for creating trail
	effects.
	""",

	plugs = {

		"attributes" : [

			"description",
			"""
			The names of the new attributes to create.  The new attributes will be
			copied from the transform in different Contexts.
			""",

		],

		"attributeContextVariable" : [

			"description",
			"""
			The name of a Context Variable that is set to the current
			attribute name when evaluating the transform. This can be used
			in upstream expressions and string substitutions to vary
			the transform.

			For example, you could drive a TimeWarp with this
			variable in order create copies of the transform at
			different times.
			""",

		],

		"space" : [

			"description",
			"""
			If you select world space, the created attributes will contain a concatenation
			of all transforms from the root of the scene to the current location.
			""",

			"preset:Local", GafferScene.Transform.Space.Local,
			"preset:World", GafferScene.Transform.Space.World,

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"requireVariation" : [

			"description",
			"""
			If true, new attributes will only be created
			if the transform differs in some of the Contexts.
			If the transform never changes, no new attributes will be created
			( you can just use the transform instead of accessing the new attributes ).
			"""

		],

		"transforms" : [

			"description",
			"""
			This hidden plug is a CompoundObject that contains just the new
			transform attributes.

			It is primarily used for internal computation, but there are
			cases where you can improve performance by naughtily plugging
			it into an expression.
			""",
			"plugValueWidget:type", ""

		],

	}

)
