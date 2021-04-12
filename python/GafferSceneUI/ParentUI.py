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

##########################################################################
# Metadata
##########################################################################

Gaffer.Metadata.registerNode(

	GafferScene.Parent,

	"description",
	"""
	Parents additional child hierarchies into the main scene hierarchy.
	""",

	plugs = {

		"parent" : [

			"description",
			"""
			The location which the children are parented under. This is
			ignored when a filter is connected, in which case the children
			are parented under all the locations matched by the filter.
			""",

			"userDefault", "/",
			# Base class hides this if its not in use, but it's still
			# pretty useful for the Parent node, so we make it visible
			# unconditionally again.
			"layout:visibilityActivator", "",

		],

		"children" : [

			"description",
			"""
			The child hierarchies to be parented.
			""",

			"plugValueWidget:type", "",
			"nodule:type", "GafferUI::CompoundNodule",
			"noduleLayout:spacing", 0.5,

		],

		"parentVariable" : [

			"description",
			"""
			A context variable used to pass the location of the parent to the
			upstream nodes connected into the `children` plug. This can be used
			to procedurally vary the children at each different parent location.
			""",

		],

		"destination" : [

			"description",
			"""
			The location where the children will be placed in the output scene.
			The default is to place the children under the parent, but they may
			be relocated anywhere while still inheriting the parent's transform.
			This is particularly useful when parenting lights to geometry but
			wanting to group them and control their visibility separately.

			When the destination is evaluated, the `${scene:path}` variable holds
			the source location matched by the filter. This allows the children
			to be placed relative to the "parent". For example, `${scene:path}/..`
			will place the children alongside the "parent" rather than under it.
			""",

		],

	}

)
