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

	GafferScene.CollectPrimitiveVariables,

	"description",
	"""
	Make copies of target primitive variables with different suffixes,
	where the new suffixed copies come from different contexts.

	By combining this with a TimeWarp, you can create copies of
	primitive variables at different times, useful for creating trail
	effects.
	""",

	"ui:spreadsheet:activeRowNamesConnection", "suffixes",
	"ui:spreadsheet:selectorContextVariablePlug", "suffixContextVariable",

	plugs = {
		"primitiveVariables" : [

			"description",
			"""
			A match pattern for which primitive variables will be copied.
			"""

		],

		"suffixes" : [

			"description",
			"""
			The names of the new suffixes to add to copies of the target
			primitive variables.  The new suffixed variables will be
			copied from different contexts.
			""",

		],

		"suffixContextVariable" : [

			"description",
			"""
			The name of a context variable that is set to the current
			suffix when evaluating the input object. This can be used
			in upstream expressions and string substitutions to vary
			the object while creating the primvar copies.

			For example, you could drive a TimeWarp with this
			variable in order create copies of a primitive variable at
			different times.
			""",

		],

		"requireVariation" : [

			"description",
			"""
			If true, newly copied primitive variables will only be created
			if the source object is differs in some of the suffix contexts.
			If the source object never changes, it will be passed through
			unchanged ( since there is no variation, you can just use the
			original primitive variables ).
			"""

		],

	}

)
