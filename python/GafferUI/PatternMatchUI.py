##########################################################################
#
#  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
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

import IECore

import Gaffer

Gaffer.Metadata.registerNode(

	Gaffer.PatternMatch,

	"description",
	"""
	Tests an input string against a pattern, outputting true if the string
	matches.
	""",

	"nodeGadget:type", "GafferUI::AuxiliaryNodeGadget",
	"auxiliaryNodeGadget:label", "*",
	"nodeGadget:shape", "oval",
	"nodeGadget:focusGadgetVisible", False,
	"uiEditor:nodeGadgetTypes", IECore.StringVectorData( [ "GafferUI::AuxiliaryNodeGadget", "GafferUI::StandardNodeGadget" ] ),

	plugs = {

		"string" : [

			"description",
			"""
			The string to be tested.
			""",

			"nodule:type", "",

		],

		"pattern" : [

			"description",
			"""
			The pattern to match the string against. This can use any of
			Gaffer's standard wildcards :

			| Pattern   | Usage                                        |
			|:----------|:---------------------------------------------|
			| *         | Matches any string                           |
			| ?         | Matches any single character                 |
			| [ABC]     | Matches any single character from a list     |
			| [!ABC]    | Matches any single character not from a list |
			| [a-z]     | Matches any single character in a range      |
			| [!a-z]    | Matches any single character not in a range  |
			| \\        | Escapes the next character                   |
			""",

			"nodule:type", "",

		],

		"enabled" : [

			"description",
			"""
			Turns the node on and off. When off, `match` always outputs `false`.
			""",

		],

		"match" : [

			"description",
			"""
			Outputs `true` if the string matches the pattern, and `false` otherwise.
			""",

			"nodule:type", "",

		],

	}

)
