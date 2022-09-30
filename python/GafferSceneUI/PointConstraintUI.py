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
import GafferScene

Gaffer.Metadata.registerNode(

	GafferScene.PointConstraint,

	"description",
	"""
	Translates objects so that they are constrained to
	the world space position of the target. Leaves the
	scale and orientation of the object untouched.
	""",

	plugs = {

		"referenceFrame" : [

			"divider", True,

		],

		"xEnabled" : [

			"description",
			"""
			Enables the constraint in the world space x axis.
			""",

		],

		"yEnabled" : [

			"description",
			"""
			Enables the constraint in the world space y axis.
			""",

		],

		"zEnabled" : [

			"description",
			"""
			Enables the constraint in the world space z axis.
			""",

		],

		"offset" : [

			"description",
			"""
			A world space translation offset applied on top
			of the target position.

			> Note : This is ignored when `keepReferencePosition` is on. In this case it is easier
			> to modify the reference position instead.
			""",

			"layout:activator", "keepReferencePositionIsOff",

		],

	}

)
