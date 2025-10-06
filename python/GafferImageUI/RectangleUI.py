##########################################################################
#
#  Copyright (c) 2018, John Haddon. All rights reserved.
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
import GafferImage

## A function suitable as the postCreator in a NodeMenu.append() call. It
# sets the rectangle area relative to the input format.
def postCreate( node, menu ) :

	with node.scriptNode().context() :
		if node["in"].getInput() :
			format = node["in"]["format"].getValue()
		else:
			format = GafferImage.FormatPlug.getDefaultFormat( node.scriptNode().context() )

	node["area"].setValue(
		imath.Box2f(
			imath.V2f( format.getDisplayWindow().min() ) + imath.V2f( 10 ),
			imath.V2f( format.getDisplayWindow().max() ) - imath.V2f( 10 ),
		)
	)

Gaffer.Metadata.registerNode(

	GafferImage.Rectangle,

	"description",
	"""
	Renders a rectangle with adjustable line width, corner radius,
	drop shadow and transform.
	""",

	plugs = {

		"color" : {

			"description" :
			"""
			The colour of the rectangle.
			""",

		},

		"area" : {

			"description" :
			"""
			The area of the rectangle before the transform is applied.
			""",

		},

		"lineWidth" : {

			"description" :
			"""
			The width of the outline, measured in pixels.
			""",

		},

		"cornerRadius" : {

			"description" :
			"""
			Used to give the rectangle rounded corners. A radius of
			0 gives square corners.
			""",

		},

		"transform" : {

			"description" :
			"""
			Transformation applied to the rectangle.
			""",

		},

		"transform" : {

			"description" :
			"""
			A transformation applied to the rectangle. The translate and
			pivot values are specified in pixels, and the rotate value is
			specified in degrees.
			""",

			"plugValueWidget:type" : "GafferUI.LayoutPlugValueWidget",
			"layout:section" : "Transform",

		},

	}

)
