##########################################################################
#
#  Copyright (c) 2014, John Haddon. All rights reserved.
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

	GafferScene.Duplicate,

	"description",
	"""
	Duplicates a part of the scene. The duplicates
	are parented alongside the original, and have
	a transform applied to them.
	""",

	"layout:activator:targetInUse", lambda node : not node["target"].isSetToDefault(),

	plugs = {

		"parent" : [

			"description",
			"""
			For internal use only.
			""",

			# we hide the parent (which comes from the base class) because
			# the value for it is computed from the target plug automatically.
			"plugValueWidget:type", "",

		],

		"target" : [

			"description",
			"""
			The part of the scene to be duplicated.

			> Caution : Deprecated. Please connect a filter instead.
			""",

			"plugValueWidget:type", "GafferSceneUI.ScenePathPlugValueWidget",
			# We want people to use filters rather than the `target` plug. So
			# hide it unless it is already being used.
			"layout:visibilityActivator", "targetInUse",

		],

		"copies" : [

			"description",
			"""
			The number of copies to be made.
			""",

		],

		"name" : [

			"description",
			"""
			The name given to the copies. If this
			is left empty, the name from the target
			will be used instead. The names will have
			a numeric suffix applied to distinguish
			between the different copies, unless only a
			single copy is being made. Even in the case
			of a single copy, a suffix will be applied
			if necessary to keep the names unique.
			""",

		],

		"transform" : [

			"description",
			"""
			The transform to be applied to the copies. The transform
			is applied iteratively, so the second copy is transformed
			twice, the third copy is transformed three times and so on.
			""",

		],

		"destination" : [

			"description",
			"""
			The location where the copies will be placed in the output scene.
			The default value places them alongside the original.
			""",

		],

	}
)
