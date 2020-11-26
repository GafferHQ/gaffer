##########################################################################
#
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

	GafferScene.CustomOptions,

	"description",

	"""
	Applies arbitrary user-defined options to the root of the scene. Note
	that for most common cases the StandardOptions or renderer-specific options
	nodes should be preferred, as they provide predefined sets of options with customised
	user interfaces. The CustomOptions node is of most use when needing to set am
	option not supported by the specialised nodes.
	""",

	plugs = {

		"options" : [

			"description",
			"""
			The options to be applied - arbitrary numbers of user defined options may be added
			as children of this plug via the user interface, or using the CompoundDataPlug API via
			python.
			""",

			"compoundDataPlugValueWidget:editable", True,

		],

		"options.*" : [

			"nameValuePlugPlugValueWidget:ignoreNamePlug", False,

		],

		"prefix" : [

			"description",
			"""
			A prefix applied to the name of each option. For example, a prefix
			of "myCategory:" and a name of "test" will create an option named
			"myCategory:test".
			""",

			"layout:section", "Advanced",

		]

	}

)
