##########################################################################
#
#  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
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

import imath

import Gaffer

Gaffer.Metadata.registerValues( {

	"attribute:scene:visible" : [

		"defaultValue", True,
		"description",
		"""
		Whether or not the object can be seen - invisible objects are
		not sent to the renderer at all. Typically more fine
		grained (camera, reflection etc) visibility can be
		specified using a renderer specific attributes node.
		Note that making a parent location invisible will
		always make all the children invisible too, regardless
		of their visibility settings.
		""",
		"label", "Visible",

	],

	"attribute:doubleSided" : [

		"defaultValue", True,
		"description",
		"""
		Whether or not the object can be seen from both sides.
		Single sided objects appear invisible when seen from
		the back.
		""",
		"label", "Double Sided",

	],

	"attribute:render:displayColor" : [

		"defaultValue", imath.Color3f( 1 ),
		"description",
		"""
		The default colour used to display the object in the absence
		of a specific shader assignment. Commonly used to control
		basic object appearance in the Viewer.

		> Tip : For more detailed control of object appearance in the
		> Viewer, use OpenGL attributes.
		""",
		"label", "Display Color",

	],

	"attribute:gaffer:transformBlur" : [

		"defaultValue", True,
		"description",
		"""
		Whether or not transformation animation on the object
		is taken into account in the rendered image. Use the
		`gaffer:transformBlurSegments` attribute to specify
		the number of segments used to represent the motion.
		""",
		"label", "Transform Blur",

	],

	"attribute:gaffer:transformBlurSegments" : [

		"defaultValue", 1,
		"description",
		"""
		The number of segments of transform animation to
		pass to the renderer when Transform Blur is on.
		""",
		"label", "Transform Segments",

	],

	"attribute:gaffer:deformationBlur" : [

		"defaultValue", True,
		"description",
		"""
		Whether or not deformation animation on the object
		is taken into account in the rendered image. Use the
		`gaffer:deformationBlurSegments` attribute to specify
		the number of segments used to represent the motion.
		""",
		"label", "Deformation Blur",

	],

	"attribute:gaffer:deformationBlurSegments" : [

		"defaultValue", 1,
		"description",
		"""
		The number of segments of deformation animation to
		pass to the renderer when Deformation Blur is on.
		""",
		"label", "Deformation Segments",

	],

	"attribute:light:mute" : [

		"defaultValue", False,
		"description",
		"""
		Whether this light is muted.
		""",
		"label", "Mute",

	],

	"attribute:linkedLights" : [

		"defaultValue", "defaultLights",
		"description",
		"""
		The lights to be linked to this object. Accepts a set expression or
		a space separated list of lights. Use \"defaultLights\" to refer to
		all lights that contribute to illumination by default.
		""",
		"label", "Linked Lights",
		"plugValueWidget:type", "GafferSceneUI.SetExpressionPlugValueWidget",
		"ui:scene:acceptsSetExpression", True

	],

	"attribute:shadowedLights" : [

		"defaultValue", "__lights",
		"description",
		"""
		The lights that cast shadows from this object. Accepts a set
		expression or a space separated list of lights.
		""",
		"label", "Shadowed Lights",
		"plugValueWidget:type", "GafferSceneUI.SetExpressionPlugValueWidget",
		"ui:scene:acceptsSetExpression", True,

	],

	"attribute:filteredLights" : [

		"defaultValue", "",
		"description",
		"""
		The lights to be filtered by this light filter. Accepts a
		set expression or a space separated list of lights.
		Use \"defaultLights\" to refer to all lights that
		contribute to illumination by default.
		""",
		"label", "Filtered Lights",
		"plugValueWidget:type", "GafferSceneUI.SetExpressionPlugValueWidget",
		"ui:scene:acceptsSetExpression", True,

	],

	"attribute:gaffer:automaticInstancing" : [

		"defaultValue", True,
		"description",
		"""
		By default, if Gaffer sees two objects are identical, it will pass them
		to the renderer only once, saving a lot of memory. You can set this to
		false to disable that, losing the memory savings. This can be useful
		in certain cases like using world space displacement and wanting multiple
		copies to displace differently. Disabling is currently only supported by
		the Arnold render backend.
		""",
		"label", "Automatic Instancing",

	],

} )
