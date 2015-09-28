##########################################################################
#
#  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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
import GafferImage

Gaffer.Metadata.registerNode(

	GafferImage.DeepState,

	"description",
	"""
	Modifies the samples of a deep image so that the composited result
	stays the same, but there are additional desirable properties,
	such as being sorted, non-overlapping, or being combined into a
	single sample.
	""",
	"layout:activator:prune", lambda node : node["deepState"].getValue() == GafferImage.DeepState.TargetState.Tidy,
	"layout:activator:pruneOccluded", lambda node : (
		node["deepState"].getValue() == GafferImage.DeepState.TargetState.Tidy and node["pruneOccluded"].getValue()
	),

	plugs = {

		"in" : [

			"description",
			"""
			The input image data.
			""",

		],

		"deepState" : [

			"description",
			"""
			The desired state.
			"Sorted" merely orders the samples.
			"Tidy" performs sorting, splitting, and merging, to produce non-overlapping
			samples, and optionally prunes useless samples.
			"Flat" composites samples into a single sample per pixel.
			""",

			"preset:Sorted", GafferImage.DeepState.TargetState.Sorted,
			"preset:Tidy", GafferImage.DeepState.TargetState.Tidy,
			"preset:Flat", GafferImage.DeepState.TargetState.Flat,

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"pruneTransparent" : [

			"description",
			"""
			When tidying, omits fully transparent samples.  This is usually just an optimization,
			but it could affect the composited result if you start with purely additive samples that have
			zero alpha, but still add to the color.
			""",
			"layout:activator", "prune",

		],

		"pruneOccluded" : [

			"description",
			"""
			When tidying, omits samples which are blocked by samples in front of them ( occluded samples
			have no effect on the composited result.
			""",
			"layout:activator", "prune",

		],

		"occludedThreshold" : [

			"description",
			"""
			How blocked does a sample have to be before it is omitted.  By default, only 100% occluded samples
			are omitted, but if you select 0.99, then samples with only 1% visibility would also be omitted.
			The composited result is preserved by combining the values of any omitted samples with the last
			sample generated.  Using a threshold lower than 0.99 before doing a DeepMerge or DeepHoldout
			could introduce large errors, however.
			""",
			"layout:activator", "pruneOccluded",

		],

	}

)
