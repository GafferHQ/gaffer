##########################################################################
#
#  Copyright (c) 2022, Cinesite VFX Ltd. All rights reserved.
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

	GafferScene.Rename,

	"description",
	"""
	Renames locations in the scene.
	""",

	"layout:activator:nameIsSetToDefault", lambda node : node["name"].isSetToDefault(),

	plugs = {

		"name" : [

			"description",
			"""
			The new name for the location. If this name is non-empty then it
			takes precedence, and all other renaming operations are ignored.

			> Tip : The `${scene:path}` context variable contains the
			> location's original name, and can be used in a Spreadsheet's
			> `selector` to allow each row to define the new name for a
			> particular location.
			""",

			"layout:divider", True,

			"ui:spreadsheet:selectorValue", "${scene:path}",

		],

		"deletePrefix" : [

			"description",
			"""
			A prefix to remove from the start of the original name. Prefixes are removed
			before the suffixes and before the find and replace operation is
			performed.
			""",

			"layout:activator", "nameIsSetToDefault",

		],

		"deleteSuffix" : [

			"description",
			"""
			A suffix to remove from the start of the original name. Suffixes are removed
			before the find and replace operation is performed.
			""",

			"layout:activator", "nameIsSetToDefault",
			"layout:divider", True,

		],

		"find" : [

			"description",
			"""
			A string to search for within the original name. All occurrences of this string
			will be replaced with the value of `replace`. When `useRegularExpressions`
			is on, the search string is treated as a regular expression, with the
			following syntax :

			Matching
			--------

			- `.` : Matches any character.
			- `[aef]` : Matches any character in the set.
			- `[^aef]` : Matches any character not in the set.
			- `[a-z]` : Matches any character in the specified range.
			- `[[:digit:]]` : Matches any numeric digit.
			- `[[:space:]]` : Matches any whitespace character.

			Repetition
			----------

			- `*` : Matches the preceding pattern any number of times (including none).
			- `+` : Matches the preceding pattern 1 or more times.
			- `{N}` : Matches the preceding pattern N times.
			- `{M,N}` : Matches the preceding pattern between M and N times.

			Alternatives
			------------

			- `A|B` : Matches either pattern A or pattern B.

			Captures
			--------

			- `()` : Captures the subgroup of the pattern within the brackets,
			allowing it to be referenced by `{}` in the `replace` string.

			""",

			"layout:activator", "nameIsSetToDefault",

		],

		"replace" : [

			"description",
			"""
			The replacement for strings matched by the `find` plug.
			When `useRegularExpressions` is on, this can refer to
			captured patterns using Python's standard string formatting
			syntax :

			- `{0}` : The entire string matched by the regular expresion.
			- `{1}` : The 1st subgroup captured within `()` brackets by the `find` string.
			- `{N}` : The Nth subgroup captured within `()` brackets by the `find` string.
			- `{1:0>4}` : The 1st subgroup, aligned to the right and padded to width 4.
			""",

			"layout:activator", "nameIsSetToDefault",

		],

		"useRegularExpressions" : [

			"description",
			"""
			When on, the `find` string is treated as a regular expression,
			allowing it to perform complex pattern matching and to capture sections
			of the match to be referenced by the `replace` string.
			""",

			"layout:activator", "nameIsSetToDefault",
			"layout:divider", True,

		],

		"addPrefix" : [

			"description",
			"""
			A string to add at the start of the name. Prefixes are
			added last, after the find and replace operation has
			been performed.
			""",

			"layout:activator", "nameIsSetToDefault",

		],

		"addSuffix" : [

			"description",
			"""
			A string to add at the end of the name. Suffixes are
			added last, after the find and replace operation has
			been performed.
			""",


			"layout:activator", "nameIsSetToDefault",

		],

	}
)
