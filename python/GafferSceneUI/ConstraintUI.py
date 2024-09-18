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

	GafferScene.Constraint,

	"description",
	"""
	Base type for nodes which constrain objects to a target
	object by manipulating their transform.
	""",

	"layout:activator:targetModeIsUV", lambda node : node["targetMode"].getValue() == GafferScene.Constraint.TargetMode.UV,
	"layout:activator:targetModeIsVertex", lambda node : node["targetMode"].getValue() == GafferScene.Constraint.TargetMode.Vertex,
	"layout:activator:keepReferencePositionIsOff", lambda node : not node["keepReferencePosition"].getValue(),
	"layout:activator:keepReferencePositionIsOn", lambda node : node["keepReferencePosition"].getValue(),

	plugs = {

		"targetScene" : [

			"description",
			"""
			The scene containing the target location to which objects are
			constrained. If this is unconnected, the main input scene
			is used instead.
			""",

		],

		"target" : [

			"description",
			"""
			The scene location to which the objects are constrained.
			The world space transform of this location forms the basis
			of the constraint target, but is modified by the targetMode
			and targetOffset values before the constraint is applied.
			""",

			"plugValueWidget:type", "GafferSceneUI.ScenePathPlugValueWidget",
			"scenePathPlugValueWidget:scene", "targetScene in",

		],

		"ignoreMissingTarget" : [

			"description",
			"""
			Causes the constraint to do nothing if the target location
			doesn't exist in the scene, instead of erroring.
			""",

		],

		"targetMode" : [

			"description",
			"""
			The precise location of the target transform - this can be
			derived from the origin, bounding box or from a specific primitive
			uv coordinate or vertex id of the target location.
			""",

			"preset:Origin", GafferScene.Constraint.TargetMode.Origin,
			"preset:BoundMin", GafferScene.Constraint.TargetMode.BoundMin,
			"preset:BoundMax", GafferScene.Constraint.TargetMode.BoundMax,
			"preset:BoundCenter", GafferScene.Constraint.TargetMode.BoundCenter,
			"preset:UV", GafferScene.Constraint.TargetMode.UV,
			"preset:Vertex", GafferScene.Constraint.TargetMode.Vertex,

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"targetUV" : [

			"description",
			"""
			UV coordinate used in \"UV\" target mode.
			The node will error if the specified uv coordinate is out of range or does not map unambiguously
			to a single position on the primitive's surface unless ignoreMissingTarget is true.
			""",

			"layout:activator", "targetModeIsUV",
		],

		"targetVertex" : [

			"description",
			"""
			Vertex id used in \"Vertex\" target mode.
			The node will error if the specified vertex id is out of range unless ignoreMissingTarget is true.
			The node will error if the specified primitive does not have a set of uvs named \"uv\" with
			FaceVarying or Vertex interpolation unless ignoreMissingTarget is true. The uvs will be used to
			construct a local coordinate frame.
			""",

			"layout:activator", "targetModeIsVertex",
		],

		"targetOffset" : [

			"description",
			"""
			An offset applied to the target transform before the constraint
			is applied. The offset is measured in the object space of the
			target location unless the target mode is UV or Vertex in which case
			the offset is measured relative to the local surface coordinate frame.
			""",

			"divider", True,

		],

		"keepReferencePosition" : [

			"description",
			"""
			Adjusts the constraint so that the original position of the object
			at the `referenceFrame` is maintained.
			""",

		],

		"referenceFrame" : [

			"description",
			"""
			The reference frame used by the `keepReferencePosition` mode. The constraint
			is adjusted so that the original position at this frame is maintained.
			""",

			"layout:activator", "keepReferencePositionIsOn",

		],

	},

)
