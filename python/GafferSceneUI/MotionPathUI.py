##########################################################################
#
#  Copyright (c) 2021, Image Engine Design Inc. All rights reserved.
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
#      * Neither the name of Image Engine Design Inc nor the names of
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

import GafferUI

Gaffer.Metadata.registerNode(

	GafferScene.MotionPath,

	"description",
	"""
	Creates a motion path curve over the specified frame range for each filtered location.
	Note the output scene will be isolated to the matching locations only.
	""",

	"layout:activator:variableSampling", lambda node : node["samplingMode"].getValue() == GafferScene.MotionPath.SamplingMode.Variable,
	"layout:activator:fixedSampling", lambda node : node["samplingMode"].getValue() == GafferScene.MotionPath.SamplingMode.Fixed,

	plugs={

		"start" : [

			"description",
			"""
			The first frame of motion tracking can be specified relative to the current frame or as an absolute value.
			""",

			"plugValueWidget:type", "GafferUI.LayoutPlugValueWidget",
			"layoutPlugValueWidget:orientation", "horizontal",

		],

		"start.mode" : [

			"description",
			"""
			Controls whether `start.frame` is relative to the current frame or an absolute value. 
			""",

			"preset:Relative", GafferScene.MotionPath.FrameMode.Relative,
			"preset:Absolute", GafferScene.MotionPath.FrameMode.Absolute,

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
			"layout:label", "",

		],

		"start.frame" : [

			"description",
			"""
			The first frame of motion tracking.
			""",

			"layout:label", "",

		],

		"end" : [

			"description",
			"""
			The last frame of motion tracking can be specified relative to the current frame or as an absolute value.
			""",

			"plugValueWidget:type", "GafferUI.LayoutPlugValueWidget",
			"layoutPlugValueWidget:orientation", "horizontal",

		],

		"end.mode" : [

			"description",
			"""
			Controls whether `end.frame` is relative to the current frame or an absolute value.
			""",

			"preset:Relative", GafferScene.MotionPath.FrameMode.Relative,
			"preset:Absolute", GafferScene.MotionPath.FrameMode.Absolute,

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",
			"layout:label", "",

		],

		"end.frame" : [

			"description",
			"""
			The last frame of motion tracking.
			""",

			"layout:label", "",

		],

		"samplingMode" : [

			"description",
			"""
			Use "Fixed" mode for a curve with a constant vertex count.

			Use "Variable" mode for a curve sampled at regular `step` intervals.

			> Note : This curve may have a changing vertex count over a frame range.

			> Caution : In "Variable" mode it may not be possible to render with
			deformation blur enabled. Be sure to disable it via `StandardAttributes`
			if you want to render a variable sampled curve. 
			""",

			"preset:Variable", GafferScene.MotionPath.SamplingMode.Variable,
			"preset:Fixed", GafferScene.MotionPath.SamplingMode.Fixed,

			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

		],

		"step" : [

			"description",
			"""
			The sampling rate between `start.frame` and `end.frame`.

			> Note : `start.frame` and `end.frame` will always be sampled
			even if the `step` does not exactly fit the range.

			> Caution : With a small `step` size it may not be possible to render
			with deformation blur enabled. 
			""",

			"layout:activator", "variableSampling",

		],

		"samples" : [

			"description",
			"""
			The exact number of samples (including `start.frame` and `end.frame`) when using a "Fixed" `samplingMode`.
			""",

			"layout:activator", "fixedSampling",

		],

		"adjustBounds" : [

			"description",
			"""
			Opt in or out of bounds calculations.
			""",

		],

	}

)
