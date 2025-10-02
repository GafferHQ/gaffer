##########################################################################
#
#  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

Gaffer.Metadata.registerNode(

	Gaffer.ContextVariables,

	"description",
	"""
	Adds variables which can be referenced by upstream expressions
	and string substitutions.
	""",

	plugs = {

		"in" : {

			"plugValueWidget:type" : "",

		},

		"out" : {

			"plugValueWidget:type" : "",

		},

		"variables" : {

			"description" :
			"""
			The variables to be added. Each variable is represented
			as a child plug, created either through the UI or using the
			CompoundDataPlug API.
			""",

			"nodule:type" : "",

		},

		"extraVariables" : {

			"description" :
			"""
			An additional set of variables to be added. Arbitrary numbers
			of variables may be specified within a single IECore::CompoundData
			object, where each key/value pair in the object defines a variable.
			This is convenient when using an expression to define the variables
			and the variable count might be dynamic.

			If the same variable is defined by both the variables and the
			extraVariables plugs, then the value from the extraVariables
			is taken.
			""",

			"layout:section" : "Extra",
			"nodule:type" : "",

		},

	}

)
