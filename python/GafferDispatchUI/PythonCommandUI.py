##########################################################################
#
#  Copyright (c) 2015, John Haddon. All rights reserved.
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
import GafferDispatch

Gaffer.Metadata.registerNode(

	GafferDispatch.PythonCommand,

	"description",
	"""
	Runs python code.
	""",

	plugs = {

		"command" : (

			"description",
			"""
			The command to run. This may reference any of the
			variables by name, and also the node itself as `self`
			and the current Context as `context`.
			""",

			"plugValueWidget:type", "GafferUI.MultiLineStringPlugValueWidget",
			"multiLineStringPlugValueWidget:role", "code",
			"layout:label", "",

		),

		"variables" : (

			"description",
			"""
			An arbitrary set of variables which can be accessed via
			the `variables` dictionary within the python command.
			""",

			"layout:section", "Variables",

		),

		"sequence" : (

			"description",
			"""
			Calls the command once for each sequence, instead of once
			per frame. In this mode, an additional variable called `frames`
			is available to the command, containing a list of all frame
			numbers for which execution should be performed. The Context may
			be updated to reference any frame from this list, and accessing
			a variable returns the value for the current frame.

			A typical structure for the command might look something like this :

			```
			# Do some one-time initialization
			...
			# Process all frames
			for frame in frames :
				context.setFrame( frame )
				# Read variables after setting the frame to get
				# the right values for that frame.
				v = variables["v"]
				...
			# Do some one-time finalization
			...
			```
			""",

			"layout:section", "Advanced",

		),

	}

)
