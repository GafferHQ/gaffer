##########################################################################
#
#  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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
import GafferDispatch

Gaffer.Metadata.registerNode(

	GafferDispatch.SystemCommand,

	"description",
	"""
	Runs system commands via a shell.
	""",

	plugs = {

		"command" : {

			"description" :
			"""
			The command to be run. This may reference values
			from substitutions with '{substitutionName}' syntax.
			""",

		},

		"substitutions" : {

			"description" :
			"""
			An arbitrary set of name/value pairs which can be
			referenced in command with '{substitutionsName}' syntax.
			""",

			"layout:section" : "Settings.Substitutions",

		},

		"environmentVariables" : {

			"description" :
			"""
			An arbitrary set of name/value pairs which will be set as
			environment variables when running the command.
			""",

			"layout:section" : "Settings.Environment Variables",

		},

		"shell" : {

			"description" :
			"""
			When enabled, the specified command is interpreted as a shell
			command and run in a child shell. This allows semantics such
			as pipes to be used.  Otherwise the supplied command is invoked
			directly as an executable and its args.

			> Note: On MacOS with System Integrity Protection enabled, child
			> shells will not inherit `DYLD_LIBRARY_PATH` from the Gaffer
			> process. If the executable you are running relies on this,
			> disabling _shell_ should allow it to inherit the full Gaffer
			> environment.
			""",

			"layout:section" : "Advanced",

		}

	}

)
