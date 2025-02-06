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

def __attributesSummary( plug ) :

	info = []
	if plug["visibility"]["enabled"].getValue() :
		info.append( "Visible" if plug["visibility"]["value"].getValue() else "Invisible" )
	if plug["doubleSided"]["enabled"].getValue() :
		info.append( "Double Sided" if plug["doubleSided"]["value"].getValue() else "Single Sided" )
	if plug["displayColor"]["enabled"].getValue() :
		info.append( "Display Color" )

	return ", ".join( info )

def __instancingSummary( plug ) :

	info = []
	if plug["automaticInstancing"]["enabled"].getValue() :
		info.append( "Automatic Instancing " + ( "On" if plug["automaticInstancing"]["value"].getValue() else "Off" ) )

	return ", ".join( info )

def __motionBlurSummary( plug ) :

	info = []
	for motionType in "transform", "deformation" :
		onOffEnabled = plug[motionType+"Blur"]["enabled"].getValue()
		segmentsEnabled = plug[motionType+"BlurSegments"]["enabled"].getValue()
		if onOffEnabled or segmentsEnabled :
			items = []
			if onOffEnabled :
				items.append( "On" if plug[motionType+"Blur"]["value"].getValue() else "Off" )
			if segmentsEnabled :
				items.append( "%d Segments" % plug[motionType+"BlurSegments"]["value"].getValue() )
			info.append( motionType.capitalize() + " : " + "/".join( items ) )

	return ", ".join( info )

Gaffer.Metadata.registerNode(

	GafferScene.StandardAttributes,

	"description",
	"""
	Modifies the standard attributes on objects - these should
	be respected by all renderers.
	""",

	plugs = {

		# sections

		"attributes" : [

			"layout:section:Attributes:summary", __attributesSummary,
			"layout:section:Instancing:summary", __instancingSummary,
			"layout:section:Motion Blur:summary", __motionBlurSummary,

		],

		# visibility plugs

		"attributes.visibility" : [

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

			"layout:section", "Attributes",

		],

		"attributes.doubleSided" : [

			"description",
			"""
			Whether or not the object can be seen from both sides.
			Single sided objects appear invisible when seen from
			the back.
			""",

			"layout:section", "Attributes",

		],

		"attributes.displayColor" : [

			"description",
			"""
			The default colour used to display the object in the absence
			of a specific shader assignment. Commonly used to control
			basic object appearance in the Viewer.

			> Tip : For more detailed control of object appearance in the
			> Viewer, use the OpenGLAttributes node.
			""",

			"layout:section", "Attributes",

		],

		# motion blur plugs

		"attributes.transformBlur" : [

			"description",
			"""
			Whether or not transformation animation on the
			object is taken into account in the rendered image.
			Use the transformBlurSegments plug to specify the number
			of segments used to represent the motion.
			""",

			"layout:section", "Motion Blur",
			"label", "Transform",

		],

		"attributes.transformBlurSegments" : [

			"description",
			"""
			The number of segments of transform animation to
			pass to the renderer when transformBlur is on.
			""",

			"layout:section", "Motion Blur",
			"label", "Transform Segments",

		],

		"attributes.deformationBlur" : [

			"description",
			"""
			Whether or not deformation animation on the
			object is taken into account in the rendered image.
			Use the deformationBlurSegments plug to specify the
			number of segments used to represent the motion.
			""",

			"layout:section", "Motion Blur",
			"label", "Deformation",

		],

		"attributes.deformationBlurSegments" : [

			"description",
			"""
			The number of segments of deformation animation to
			pass to the renderer when deformationBlur is on.
			""",

			"layout:section", "Motion Blur",
			"label", "Deformation Segments",

		],

		"attributes.linkedLights" : [

			"description",
			"""
			The lights to be linked to this object. Accepts a set expression or
			a space separated list of lights. Use \"defaultLights\" to refer to
			all lights that contribute to illumination by default.

			Examples
			--------

			All the default lights plus the lights in the `characterLights` set
			:

			`defaultLights | characterLights`

			All the default lights, but without the lights in the `interiorLights`
			set :

			`defaultLights - interiorLights`

			> Info : Lights can be added to sets either by using the `sets` plug
			> on the light node itself, or by using a separate Set node.
			""",

			"layout:section", "Light Linking",
			"label", "Linked Lights",

		],

		"attributes.linkedLights.value" : [

			"ui:scene:acceptsSetExpression", True,
			"plugValueWidget:type", "GafferSceneUI.SetExpressionPlugValueWidget",

		],

		"attributes.filteredLights" : [

			"description",
			"""
			The lights to be filtered by this light filter. Accepts a
			set expression or a space separated list of lights.
			Use \"defaultLights\" to refer to all lights that
			contribute to illumination by default.
			""",

			"layout:section", "Light Linking",
			"label", "Filtered Lights",

		],

		"attributes.filteredLights.value" : [

			"ui:scene:acceptsSetExpression", True,
			"plugValueWidget:type", "GafferSceneUI.SetExpressionPlugValueWidget",

		],

		# Instancing

		"attributes.automaticInstancing" : [

			"description",
			"""
			By default, if Gaffer sees two objects are identical, it will pass them
			to the renderer only once, saving a lot of memory. You can set this to
			false to disable that, losing the memory savings. This can be useful
			in certain cases like using world space displacement and wanting multiple
			copies to displace differently. Disabling is currently only supported by
			the Arnold render backend.
			""",

			"layout:section", "Instancing",

		],

	}

)
