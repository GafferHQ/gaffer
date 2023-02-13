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
import GafferUI

import GafferScene
import GafferSceneUI

##########################################################################
# Metadata
##########################################################################

Gaffer.Metadata.registerNode(

	GafferScene.Isolate,

	"description",
	"""
	Isolates objects by removing paths not matching a filter from the scene.

	> Caution : The Isolate node does not work well with the `...` wildcard in
	> PathFilters. Because of the way Gaffer generates scenes progressively
	> from the root, the Isolate node needs to know if the filter matches any
	> descendants (children, grandchildren etc) of the current location; if there
	> are any matches then the current location is kept, otherwise it is removed.
	> When faced with `...`, the Isolate node assumes that there will always be a
	> descendant match because `...` matches anything. This can cause it to keep
	> locations where in fact there may be no true descendant match. The only
	> alternative would be to search the scene recursively looking for a true
	> match, but this would defeat the goal of lazy evaluation and could cause
	> poor performance.
	""",

	plugs = {

		"from" : [

			"description",
			"""
			The ancestor to isolate the objects from. Only locations below
			this will be removed.
			""",

			"plugValueWidget:type", "GafferSceneUI.ScenePathPlugValueWidget",

		],

		"keepLights" : [

			"description",
			"""
			Keeps all lights and light filters, regardless of other settings.
			This is useful when isolating an asset but wanting to render it
			using a light rig located elsewhere in the scene.
			""",

		],

		"keepCameras" : [

			"description",
			"""
			Keeps all cameras, regardless of other settings. This is
			useful when isolating an asset but wanting to render it
			through a camera located elsewhere in the scene.
			""",

		],

		"adjustBounds" : [

			"description",
			"""
			By default, the bounding boxes of ancestor locations are
			automatically updated when children are removed. This can
			be turned off if necessary to get improved performance - in
			this case the bounding boxes will still wholly contain the
			contents at each location, but may be bigger than necessary.
			""",

		],

	}

)
