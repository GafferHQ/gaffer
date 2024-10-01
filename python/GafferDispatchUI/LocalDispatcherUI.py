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

	GafferDispatch.LocalDispatcher,

	"description",
	"""
	Schedules execution of task graphs on the local machine. Tasks
	may be dispatched in the background to keep the UI responsive.
	""",

	"layout:activator:executeInBackgroundIsOn", lambda node : node["executeInBackground"].getValue(),

	plugs = {

		"executeInBackground" : (

			"description",
			"""
			Executes the dispatched tasks in separate processes via a
			background thread.
			""",

		),

		"ignoreScriptLoadErrors" : (

			"description",
			"""
			Ignores errors loading the script when executing in the background.
			This is not recommended - fix the problem instead.
			""",

			"layout:activator", "executeInBackgroundIsOn",

		),

		"environmentCommand" : (

			"description",
			"""
			Optional system command to modify the environment when launching
			tasks in the background. Background tasks are launched in a separate
			process using a `gaffer execute ...` command, and they inherit the
			environment from the launching process. When an environment
			command is specified, tasks are instead launched using `environmentCommand
			gaffer execute ...`, and the environment command is responsible for
			modifying the inherited environment and then launching `gaffer execute ...`.

			For example, the following environment command will use the standard `/usr/bin/env`
			program to set some custom variables :

			```
			/usr/bin/env FOO=BAR TOTO=TATA
			```
			""",

			"layout:activator", "executeInBackgroundIsOn",

		),

	}

)
