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

import fnmatch

import Gaffer
import GafferUI
import GafferScene

##########################################################################
# Metadata
##########################################################################

Gaffer.Metadata.registerNode(

	GafferScene.InteractiveRender,

	"description",
	"""
	A base class for nodes which can render scenes interactively, updating
	the render to reflect changes to the node graph.
	""",

	plugs = {

		"*" : [

			"nodule:type", "",

		],

		"in" : [

			"description",
			"""
			The scene to be rendered.
			""",

			"nodule:type", "GafferUI::StandardNodule",

		],

		"out" : [

			"description",
			"""
			A direct pass-through of the input scene.
			""",

		],

		"state" : [

			"description",
			"""
			The interactive state.
			""",

			"preset:Stopped", GafferScene.InteractiveRender.State.Stopped,
			"preset:Running", GafferScene.InteractiveRender.State.Running,
			"preset:Paused", GafferScene.InteractiveRender.State.Paused,

		],

		"updateLights" : [

			"description",
			"""
			When on, changes to lights are reflected in the
			interactive render.
			""",

		],

		"updateAttributes" : [

			"description",
			"""
			When on, changes to attribute (and shaders) are reflected in the
			interactive render. When working with complex scenes, it may be
			worth turning this off to gain increased performance when only
			editing lights.
			""",

		],

		"updateCameras" : [

			"description",
			"""
			When on, changes to the camera are reflected in the
			interactive render.
			""",

		],

		"updateCoordinateSystems" : [

			"description",
			"""
			When on, changes to coordinate systems are reflected in the
			interactive render.
			""",

		],

	}
)

##########################################################################
# Widgets
##########################################################################

## \todo Make a custom UI with play/pause/stop/restart buttons.
GafferUI.PlugValueWidget.registerCreator(
	GafferScene.InteractiveRender,
	"state",
	GafferUI.PresetsPlugValueWidget,
)
