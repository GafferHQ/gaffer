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

import Gaffer
import GafferUI

import GafferScene
import GafferSceneUI

##########################################################################
# Metadata
##########################################################################

Gaffer.Metadata.registerNode(

	GafferScene.SubTree,

	"description",
	"""A node for extracting a specific branch from a scene.""",

	plugs = {

		"root" : [

			"description",
			"""
			The location to become the new root for the output scene.
			All locations below this will be kept, and all others will
			be discarded.
			""",

			"plugValueWidget:type", "GafferSceneUI.ScenePathPlugValueWidget",

		],

		"includeRoot" : [

			"description",
			"""
			Causes the root location to also be kept in the
			output scene, in addition to its children. For
			instance, if the scene contains only
			/city/street/house and the root is set to /city/street,
			then the new scene will by default contain only /house -
			but the includeRoot setting will cause it to contain
			/street/house instead.
			""",

		],

		"inheritTransform" : [

			"description",
			"""
			Maintains the subtree's world-space position by applying the `root`
			location's full transform to the subtree's children.
			"""

		],

		"inheritAttributes" : [

			"description",
			"""
			Maintains the subtree's attributes (including shader assignments) by
			applying the `root` location's full attributes to the subtree's
			children.
			"""

		],

		"inheritSetMembership" : [

			"description",
			"""
			Maintains the subtree's membership in sets by transferring the
			`root` location's memberships to the subtree's children.
			"""


		],

	}

)
