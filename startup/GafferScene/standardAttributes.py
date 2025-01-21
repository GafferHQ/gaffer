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

import IECore

import Gaffer

Gaffer.Metadata.registerValue( "attribute:scene:visible", "label", "Visible" )
Gaffer.Metadata.registerValue( "attribute:scene:visible", "defaultValue", IECore.BoolData( True ) )
Gaffer.Metadata.registerValue(
	"attribute:scene:visible",
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
)

Gaffer.Metadata.registerValue( "attribute:doubleSided", "label", "Double Sided" )
Gaffer.Metadata.registerValue( "attribute:doubleSided", "defaultValue", IECore.BoolData( True ) )
Gaffer.Metadata.registerValue(
	"attribute:doubleSided",
	"description",
	"""
	Whether or not the object can be seen from both sides.
	Single sided objects appear invisible when seen from
	the back.
	""",
)

Gaffer.Metadata.registerValue( "attribute:render:displayColor", "label", "Display Color" )
Gaffer.Metadata.registerValue( "attribute:render:displayColor", "defaultValue", IECore.Color3fData( imath.Color3f( 1 ) ) )
Gaffer.Metadata.registerValue(
	"attribute:render:displayColor",
	"description",
	"""
	The default colour used to display the object in the absence
	of a specific shader assignment. Commonly used to control
	basic object appearance in the Viewer.

	> Tip : For more detailed control of object appearance in the
	> Viewer, use OpenGL attributes.
	""",
)

Gaffer.Metadata.registerValue( "attribute:gaffer:transformBlur", "label", "Transform Blur" )
Gaffer.Metadata.registerValue( "attribute:gaffer:transformBlur", "defaultValue", IECore.BoolData( True ) )
Gaffer.Metadata.registerValue(
	"attribute:gaffer:transformBlur",
	"description",
	"""
	Whether or not transformation animation on the object
	is taken into account in the rendered image. Use the
	`gaffer:transformBlurSegments` attribute to specify
	the number of segments used to represent the motion.
	""",
)

Gaffer.Metadata.registerValue( "attribute:gaffer:transformBlurSegments", "label", "Transform Segments" )
Gaffer.Metadata.registerValue( "attribute:gaffer:transformBlurSegments", "defaultValue", IECore.IntData( 1 ) )
Gaffer.Metadata.registerValue(
	"attribute:gaffer:transformBlurSegments",
	"description",
	"""
	The number of segments of transform animation to
	pass to the renderer when Transform Blur is on.
	""",
)

Gaffer.Metadata.registerValue( "attribute:gaffer:deformationBlur", "label", "Deformation Blur" )
Gaffer.Metadata.registerValue( "attribute:gaffer:deformationBlur", "defaultValue", IECore.BoolData( True ) )
Gaffer.Metadata.registerValue(
	"attribute:gaffer:deformationBlur",
	"description",
	"""
	Whether or not deformation animation on the object
	is taken into account in the rendered image. Use the
	`gaffer:deformationBlurSegments` attribute to specify
	the number of segments used to represent the motion.
	""",
)

Gaffer.Metadata.registerValue( "attribute:gaffer:deformationBlurSegments", "label", "Deformation Segments" )
Gaffer.Metadata.registerValue( "attribute:gaffer:deformationBlurSegments", "defaultValue", IECore.IntData( 1 ) )
Gaffer.Metadata.registerValue(
	"attribute:gaffer:deformationBlurSegments",
	"description",
	"""
	The number of segments of deformation animation to
	pass to the renderer when Deformation Blur is on.
	""",
)

Gaffer.Metadata.registerValue( "attribute:light:mute", "label", "Mute" )
Gaffer.Metadata.registerValue( "attribute:light:mute", "defaultValue", IECore.BoolData( False ) )
Gaffer.Metadata.registerValue(
	"attribute:light:mute",
	"description",
	"""
	Whether this light is muted.
	"""
)

Gaffer.Metadata.registerValue( "attribute:linkedLights", "label", "Linked Lights" )
Gaffer.Metadata.registerValue( "attribute:linkedLights", "defaultValue", "defaultLights" )
Gaffer.Metadata.registerValue(
	"attribute:linkedLights",
	"description",
	"""
	The lights to be linked to this object. Accepts a set expression or
	a space separated list of lights. Use \"defaultLights\" to refer to
	all lights that contribute to illumination by default.
	"""
)
Gaffer.Metadata.registerValue( "attribute:linkedLights", "ui:scene:acceptsSetExpression", True )

Gaffer.Metadata.registerValue( "attribute:filteredLights", "label", "Filtered Lights" )
Gaffer.Metadata.registerValue( "attribute:filteredLights", "defaultValue", IECore.StringData( "" ) )
Gaffer.Metadata.registerValue(
	"attribute:filteredLights",
	"description",
	"""
	The lights to be filtered by this light filter. Accepts a
	set expression or a space separated list of lights.
	Use \"defaultLights\" to refer to all lights that
	contribute to illumination by default.
	"""
)

Gaffer.Metadata.registerValue( "attribute:gaffer:automaticInstancing", "label", "Automatic Instancing" )
Gaffer.Metadata.registerValue( "attribute:gaffer:automaticInstancing", "defaultValue", IECore.BoolData( True ) )
Gaffer.Metadata.registerValue(
	"attribute:gaffer:automaticInstancing",
	"description",
	"""
	By default, if Gaffer sees two objects are identical, it will pass them
	to the renderer only once, saving a lot of memory. You can set this to
	false to disable that, losing the memory savings. This can be useful
	in certain cases like using world space displacement and wanting multiple
	copies to displace differently. Disabling is currently only supported by
	the Arnold render backend.
	""",
)
