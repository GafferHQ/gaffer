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
import GafferUI
import GafferScene
import GafferSceneUI

##########################################################################
# Metadata
##########################################################################

Gaffer.Metadata.registerNode(

	GafferScene.BranchCreator,

	"description",
	"""
	Base class for nodes creating a new branch in the scene hierarchy.
	""",

	"layout:activator:filterNotConnected", lambda node : node["filter"].getInput() is None,
	"layout:activator:parentInUse", lambda node : node["parent"].getInput() is not None or node["parent"].getValue() != "",

	plugs = {

		"parent" : [

			# Deliberately not documenting parent plug, so that
			# it is given documentation more specific to each
			# derived class.

			"plugValueWidget:type", "GafferSceneUI.ScenePathPlugValueWidget",
			"layout:activator", "filterNotConnected",
			# We'd prefer users to use the `filter` rather than the `parent` plug.
			# Hide it if it isn't already being used (from a time before the introduction
			# of the filter).
			"layout:visibilityActivator", "parentInUse",

		],

		"destination" : [

			# Deliberately not documenting destination plug, so that
			# it is given documentation more specific to each
			# derived class.

			"plugValueWidget:type", "GafferSceneUI.ScenePathPlugValueWidget",
			"ui:spreadsheet:selectorValue", "${scene:path}",
			"layout:index", -1,

		],

	}
)
