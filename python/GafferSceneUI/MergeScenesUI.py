##########################################################################
#
#  Copyright (c) 2020, Cinesite VFX Ltd. All rights reserved.
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
import GafferScene

Gaffer.Metadata.registerNode(

	GafferScene.MergeScenes,

	"description",
	"""
	Merges multiple input scenes into a single output scene.
	Merging is performed left to right, starting with `in[0]`.

	By default, when more than one input contains the same
	scene location, the location's properties from the leftmost
	input are kept. In this mode, only _new_ locations are merged
	in from the additional inputs. Optionally, the properties
	can be replaced by or merged with the properties of the
	subsequent inputs.

	Sets are always merged from all inputs. Where multiple inputs
	have sets with the same name, the sets are merged into a union.

	> Caution : When `transformMode` and/or `objectMode` is not `Keep`,
	> bounding box computations have significant overhead. Consider
	> not using these operations, or turning off `adjustBounds`.
	""",

	plugs = {

		"transformMode" : [

			"description",
			"""
			The method used to merge transforms when the same location
			exists in multiple input scenes. Keep mode keeps the transform
			from the first input, and Replace mode replaces it with the
			transform of the last input.
			""",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
			"preset:Keep", GafferScene.MergeScenes.Mode.Keep,
			"preset:Replace", GafferScene.MergeScenes.Mode.Replace,

		],

		"attributesMode" : [

			"description",
			"""
			The method used to merge attributes when the same location
			exists in multiple input scenes. Keep mode keeps the attributes
			from the first input, Replace mode replaces them with the attributes
			from the last input, and Merge mode merges all attributes together
			from first to last.
			""",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
			"preset:Keep", GafferScene.MergeScenes.Mode.Keep,
			"preset:Replace", GafferScene.MergeScenes.Mode.Replace,
			"preset:Merge", GafferScene.MergeScenes.Mode.Merge,

		],

		"objectMode" : [

			"description",
			"""
			The method used to merge objects when the same location
			exists in multiple input scenes. Keep mode keeps the object
			from the first input, and Replace mode replaces it with the
			object from the last input which has one.
			""",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
			"preset:Keep", GafferScene.MergeScenes.Mode.Keep,
			"preset:Replace", GafferScene.MergeScenes.Mode.Replace,

		],

		"globalsMode" : [

			"description",
			"""
			The method used to merge scene globals. Keep mode keeps the globals
			from the first input, Replace mode replaces them with the globals
			from the last input, and Merge mode merges all globals together
			from first to last.
			""",

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
			"preset:Keep", GafferScene.MergeScenes.Mode.Keep,
			"preset:Replace", GafferScene.MergeScenes.Mode.Replace,
			"preset:Merge", GafferScene.MergeScenes.Mode.Merge,

		],

		"adjustBounds" : [

			"description",
			"""
			Adjusts bounding boxes to take account of the merging operation.

			> Caution : This has considerable overhead when the `objectsMode` and/or
			> `transformsMode` is not `Keep`.
			""",

		],

	}

)
