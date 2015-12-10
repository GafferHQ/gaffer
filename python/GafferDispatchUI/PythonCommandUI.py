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

Gaffer.Metadata.registerNode(

	Gaffer.PythonCommand,

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
			and the current context as `context`.
			""",

			"nodule:type", "",
			"plugValueWidget:type", "GafferUI.PythonCommandUI._CommandPlugValueWidget",

		),

		"variables" : (

			"description",
			"""
			An arbitrary set of variables which can be referenced
			by name from within the python command.
			""",

			"nodule:type", "",
			"layout:section", "Settings.Variables",

		),

	}

)

class _CommandPlugValueWidget( GafferUI.MultiLineStringPlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		GafferUI.MultiLineStringPlugValueWidget.__init__( self, plug, **kw )

	def hasLabel( self ) :

		## \todo Maybe there should be some metadata we could use
		# to disable the label, rather than having to tell this little
		# porky pie?
		return True
