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

	GafferScene.PointInstancerCore,

	"description",
	"""
	Utility node containing the core logic for the PointInstancer node.
	Takes an input Primitive and converts it into a PointInstancer object,
	while also defining the contexts required to generate prototype variations
	for the instancer.

	> Caution : This is an internal implementation detail of the PointInstancer
	> node, and as such is subject to change without warning. Do not rely on
	> directly.
	""",

	plugs = {

		"*" : {

			"noduleLayout:visible" : False,

		},

		"inPoints" : {

			"description" :
			"""
			The input Primitive. This must already have `prototypeRoots` and
			`prototypeIndex` primitive variables in the format required of a
			PointInstancer.
			""",

			"noduleLayout:visible" : True,

		},

		"timeOffset" : {

			"description" :
			"""
			The name of a primitive variable specifying per-point time offsets,
			used to generate prototype variation.
			"""

		},

		"contextVariables" : {

			"description" :
			"""
			The names of primitive variables specifying per-point context variable
			values used to generate prototype variation.

			Names should be separated by spaces and may contain Gaffer's standard
			wildcards.
			"""

		},

		"prototypeFormat" : {

			"description" :
			"""
			A format specification used to customise the name of each prototype based on its context variables and time offset. The following format tokens are available :

			- `{name}` : The original prototype name before variation.
			- `{timeOffset}` : The time offset.
			- `{contextVariable}` : The value of a context variable.
			- `{hash}` : A hash value that uniquely identifies the prototype.

			> Note : Each prototype must have a unique name. If the time offset or any context variable is omitted from the format, the hash will be appended automatically to maintain this constraint.
			"""

		},

		"outPoints" : {

			"description" :
			"""
			The output PointInstancer.
			""",

			"noduleLayout:visible" : True,

		},

		"prototypeNames" : {

			"description" :
			"""
			Output defining names for all prototype variations to be collected
			for `outPoints`. These are derived from `timeOffset`, `contextVariables`,
			and `prototypeFormat`. The responsibility for collection lies with the
			PointInstancer node.
			""",

		},

		"prototypeSelector" : {

			"description" :
			"""
			Receives the name of a prototype, which should be present in
			`prototypeNames`. This determines which prototype the `prototypeTimeOffset`
			and `prototypeContext` plugs are being evaluated for.
			""",

		},

		"prototype" : {

			"description" :
			"""
			Outputs the source location for the prototype specified by the
			`prototypeSelector` plug.
			""",

		},

		"prototypeTimeOffset" : {

			"description" :
			"""
			Outputs the required time offset for the prototype specified
			by the `prototypeSelector` plug.
			""",

		},

		"prototypeContext" : {

			"description" :
			"""
			Outputs the required context variables for the prototype specified
			by the `prototypeSelector` plug.
			""",

		},

	}
)
