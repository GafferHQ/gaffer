##########################################################################
#
#  Copyright (c) 2023, Image Engine Design Inc. All rights reserved.
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

	GafferScene.FramingConstraint,

	"description",
	"""
	Position a camera so that all of a target is visible.
	""",

	"layout:activator:useTargetFrame", lambda node : node["useTargetFrame"].getValue(),

	plugs = {

		"targetScene" : [

			"description",
			"""
			The scene containing the target location to which cameras are
			pointed. If this is unconnected, the main input scene
			is used instead.
			""",

		],

		"target" : [

			"description",
			"""
			The scene location to which the cameras are pointed.
			""",

			"plugValueWidget:type", "GafferSceneUI.ScenePathPlugValueWidget",

		],

		"ignoreMissingTarget" : [

			"description",
			"""
			Causes the constraint to do nothing if the target location
			doesn't exist in the scene, instead of erroring.
			""",
			"divider", True,
		],

		"boundMode" : [

			"description",
			"""
			How the camera frustum is fit to the target. `Sphere` approximates the bounding
			box of the target  with a sphere.  `Box` uses the actual bounding box, which
			allows framing closer, but means the camera will move closer or farther depending
			on the exact alignment of the box to the view ( which makes for a bumpy looking
			turntable ).
			""",

			"preset:Box", "box",
			"preset:Sphere", "sphere",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"padding" : [

			"description",
			"""
			Add a border between the edge of the camera frustum and the target.
			0.1 adds a 10% border.  Using negative padding moves the camera closer.
			""",
		],

		"extendFarClip" : [

			"description",
			"""
			If the target is larger than the current clipping planes, increase
			the far clipping plane to enclose it.
			""",
			"divider", True,
		],

		"useTargetFrame" : [

			"description",
			"""
			Use a fixed frame to access the target at.  This can be used to produce a consistent
			framing if the target has high-frequency animation you want to ignore.
			""",
		],

		"targetFrame" : [

			"description",
			"""
			The frame used to access the target when `useTargetFrame` is set.
			""",

			"layout:activator", "useTargetFrame",
		],
	},

)
