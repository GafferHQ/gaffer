##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
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

	GafferScene.Options,

	"description",
	"""
	The base type for nodes that apply options to the scene.
	""",

	plugs = {

		"options" : [

			"description",
			"""
			The options to be applied - arbitrary numbers of user defined options may be added
			as children of this plug via the user interface, or using the CompoundDataPlug API via
			python.
			""",

			"compoundDataPlugValueWidget:editable", False,

		],

		"options.*" : [

			"nameValuePlugPlugValueWidget:ignoreNamePlug", True,

		],

		"extraOptions" : [

			"description",
			"""
			An additional set of options to be added. Arbitrary numbers
			of options may be specified within a single `IECore.CompoundObject`,
			where each key/value pair in the object defines an option.
			This is convenient when using an expression to define the options
			and the option count might be dynamic. It can also be used to
			create options whose type cannot be handled by the `options`
			CompoundDataPlug.

			If the same option is defined by both the `options` and the
			`extraOptions` plugs, then the value from the `extraOptions`
			is taken.
			""",

			"plugValueWidget:type", "",
			"layout:section", "Extra",
			"nodule:type", "",

		],

	}

)
