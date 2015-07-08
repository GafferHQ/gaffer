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

Gaffer.Metadata.registerNode(

	Gaffer.Wedge,

	"description",
	"""
	Causes upstream nodes to be dispatched multiple times in a range
	of contexts, each time with a different value for a specified variable.
	This variable should be referenced in upstream expressions to apply
	variation to the tasks being performed. For instance, it could be
	used to drive a shader parameter to perform a series of "wedges" to
	demonstrate the results of a range of possible parameter values.
	""",

	"layout:activator:modeIsFloatRange", lambda node : node["mode"].getValue() == int( node.Mode.FloatRange ),
	"layout:activator:modeIsIntRange", lambda node : node["mode"].getValue() == int( node.Mode.IntRange ),
	"layout:activator:modeIsColorRange", lambda node : node["mode"].getValue() == int( node.Mode.ColorRange ),
	"layout:activator:modeIsFloatList", lambda node : node["mode"].getValue() == int( node.Mode.FloatList ),
	"layout:activator:modeIsIntList", lambda node : node["mode"].getValue() == int( node.Mode.IntList ),
	"layout:activator:modeIsStringList", lambda node : node["mode"].getValue() == int( node.Mode.StringList ),

	plugs = {

		"variable" : [

			"description",
			"""
			The name of the context variable defined by the wedge.
			This should be used in upstream expressions to apply the
			wedged value to specific nodes.
			""",

			"nodule:type", "",

		],

		"indexVariable" : [

			"description",
			"""
			The name of an index context variable defined by the wedge.
			This is assigned values starting at 0 and incrementing for
			each new value - for instance a wedged float range might
			assign variable values of `0.25, 0,5, 0.75` or `0.1, 0,2, 0.3`
			but the corresponding index variable would take on values of
			`0, 1, 2` in both cases.

			The index variable is particularly useful for generating
			unique filenames when using a float range to perform
			wedged renders.
			""",

			"nodule:type", "",

		],

		"mode" : [

			"description",
			"""
			The method used to define the range of values used by
			the wedge. It is possible to define numeric or color
			ranges, and also to specify explicit lists of numbers or
			strings.
			""",

			"nodule:type", "",
			"plugValueWidget:type", "GafferUI.PresetsPlugValueWidget",

			"preset:Float Range", int( Gaffer.Wedge.Mode.FloatRange ),
			"preset:Int Range", int( Gaffer.Wedge.Mode.IntRange ),
			"preset:Color Range", int( Gaffer.Wedge.Mode.ColorRange ),
			"preset:Float List", int( Gaffer.Wedge.Mode.FloatList ),
			"preset:Int List", int( Gaffer.Wedge.Mode.IntList ),
			"preset:String List", int( Gaffer.Wedge.Mode.StringList ),

		],

		# Float Ramge

		"floatMin" : [

			"description",
			"""
			The smallest value of the wedge range when the
			mode is set to "Float Range". Has no effect in
			other modes.
			""",

			"nodule:type", "",
			"layout:activator", "modeIsFloatRange",

		],

		"floatMax" : [

			"description",
			"""
			The largest allowable value of the wedge range
			when the mode is set to "Float Range". Has no
			effect in other modes.
			""",

			"nodule:type", "",
			"layout:activator", "modeIsFloatRange",

		],

		"floatStep" : [

			"description",
			"""
			The step between successive values when the
			mode is set to "Float Range". Values are
			generated by adding this step to the minimum
			value until the maximum value is exceeded.
			Note that if (max - min) is not exactly divisible
			by the step then the maximum value may not
			be used at all. Has no effect in other modes.
			""",

			"nodule:type", "",
			"layout:activator", "modeIsFloatRange",

		],

		# Int Range

		"intMin" : [

			"description",
			"""
			The smallest value of the wedge range when the
			mode is set to "Int Range". Has no effect in
			other modes.
			""",

			"nodule:type", "",
			"layout:activator", "modeIsIntRange",

		],

		"intMax" : [

			"description",
			"""
			The largest allowable value of the wedge range
			when the mode is set to "Int Range". Has no
			effect in other modes.
			""",

			"nodule:type", "",
			"layout:activator", "modeIsIntRange",

		],

		"intStep" : [

			"description",
			"""
			The step between successive values when the
			mode is set to "Int Range". Values are
			generated by adding this step to the minimum
			value until the maximum value is exceeded.
			Note that if (max - min) is not exactly divisible
			by the step then the maximum value may not
			be used at all. Has no effect in other modes.
			""",

			"nodule:type", "",
			"layout:activator", "modeIsIntRange",

		],

		# Color Range

		"ramp" : [

			"description",
			"""
			The range of colours used when the mode
			is set to "Colour Range". Has no effect in
			other modes.
			""",

			"nodule:type", "",
			"layout:activator", "modeIsColorRange",

		],

		"colorSteps" : [

			"description",
			"""
			The number of steps in the wedge range
			defined when in "Colour Range" mode. The
			steps are distributed evenly from the start
			to the end of the ramp. Has no effect in
			other modes.
			""",

			"nodule:type", "",
			"layout:activator", "modeIsColorRange",

		],

		# Lists

		"floats" : [

			"description",
			"""
			The list of values used when in "Float List"
			mode. Has no effect in other modes.
			""",

			"nodule:type", "",
			"layout:activator", "modeIsFloatList",

		],

		"ints" : [

			"description",
			"""
			The list of values used when in "Int List"
			mode. Has no effect in other modes.
			""",

			"nodule:type", "",
			"layout:activator", "modeIsIntList",

		],

		"strings" : [

			"description",
			"""
			The list of values used when in "String List"
			mode. Has no effect in other modes.
			""",

			"nodule:type", "",
			"layout:activator", "modeIsStringList",

		],

	}

)
