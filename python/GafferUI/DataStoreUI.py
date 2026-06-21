##########################################################################
#
#  Copyright (c) 2026, Image Engine Design Inc. All rights reserved.
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

import functools

import imath

import Gaffer
import GafferUI

Gaffer.Metadata.registerNode(

	Gaffer.DataStore,

	"description",
	"""
	Stores data that will be saved to disk beside the Gaffer script, instead of stored inside
	the Gaffer serialisation. The next time the script is opened, the data will be deferred
	loaded when it is needed.

	Appropriate for any large data associated with a Gaffer script ( for example, if you need
	to store primitive variable values on large meshes ).

	Values are accessed using the setEntry/getEntry methods, and can also be read using regular
	plug evaluations.
	""",

	plugs = {

		"selector" : {

			"description" :
			"""
			Chooses the entry to be output.
			Typically this will refer to a Context Variable using
			the `${variableName}` syntax.
			The `keys` plug outputs all valid keys you might want to use here.
			""",
			"nodule:type" : "",
		},


		"out" : {

			"description" :
			"""
			Outputs the entry corresponding to `selector`.
			""",

			"plugValueWidget:type" : "",
		},

		"keys" : {

			"description" :
			"""
			Outputs all entry keys.
			""",
		},
	}

)
