##########################################################################
#
#  Copyright (c) 2025, Image Engine Design Inc. All rights reserved.
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

import IECore

import Gaffer
import GafferImage


Gaffer.Metadata.registerNode(

	GafferImage.SATBlur,

	"description",
	"""
	A blur node implemented using Summed Area Tables, which allows for very efficient large and variable
	radius blurs with rectangular kernels. In order to be more widely useful, we also support
	approximating a disk filter.

	Also includes some advanced features for depth layering, which is useful as a building block for FocalBlur.
	""",

	plugs = {

		"radius" : {

			"description" :
			"""
			The radius to blur by in pixels. This can be varied independently
			in the x and y directions, and fractional values are supported for
			fine control.
			""",

		},

		"radiusChannel" : {

			"description" :
			"""
			An optional input image channel which defines a blur radius per pixel, allowing the radius to be
			varied across the image. The per-pixel radius is multiplied with the main radius control.
			""",
			"plugValueWidget:type" : "GafferImageUI.ChannelPlugValueWidget",
			"channelPlugValueWidget:extraChannels" : IECore.StringVectorData( [ "" ] ),
			"channelPlugValueWidget:extraChannelLabels" : IECore.StringVectorData( [ "None" ] ),
		},

		"maxRadius" : {

			"description" :
			"""
			An upper limit on the radius (`radiusChannel * radius`). Larger radii will be clamped to this
			size. Used to accelerate rendering, so higher-than-necessary settings may reduce speed.
			""",

		},

		"boundingMode" : {

			"description" :
			"""
			The method used when a filter references pixels outside the
			input data window.
			""",

			"preset:Black" : GafferImage.SATBlur.BoundingMode.Black,
			"preset:Normalize" : GafferImage.SATBlur.BoundingMode.Normalize,

			"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",

		},

		"filter" : {

			"description" :
			"""
			The filter used to blur. A box filter is supported exactly by
			the summed area table evaluation, whereas a disk must be
			approximated via some number of rectangles.
			""",

			"plugValueWidget:type" : "GafferUI.PresetsPlugValueWidget",

			"preset:Box" : "box",
			"preset:Disk" : "disk",

		},

		"diskRectangles" : {

			"description" :
			"""
			When using a disk filter, the shape of the disk is approximated as some number of rectangles.
			More rectangles give a more accurate shape, but take longer to evaluate.
			Note that even numbers do not have an effect - due to symmetry across the center of the disk,
			the most effective way to use 4 rectangles is an identical shape to using 3 rectangles - you
			must use at least 5 in order to increase quality.
			""",

			"layout:visibilityActivator" : lambda plug : plug.node()["filter"].getValue() == "disk",
		},


		"layerBoundaries" : {

			"description" :
			"""
			Separates the source into layers, based on the depth defined in `depthChannel`. When filtering
			a result, only contributions with a depth greater than `depthLookupChannel` are included.
			This is pretty specifically intended as a component of the infilling algorithm for FocalBlur
			- it allows for infilling which fills in using background colors, but doesn't smear out the
			foreground.

			The way this parameter is specified is the same as `DiskBlur` :

			The layers are defined by the radius values at their boundaries, which must be specified from
			low to high. Negative radii are accepted, allowing blurring to be represented both in front
			of and behind a focal plane. A reasonable value is therefore an exponential
			series from -maxRadius to +maxRadius, for example [ -32, -16, -8, -4, -2, -1, 1, 2, 4, 8, 16, 32 ]
			""",

			"layout:section" : "Advanced"

		},

		"depthChannel" : {

			"description" :
			"""
			Defines the depth of source pixels when doing a multi-layer SATBlur.
			""",
			"plugValueWidget:type" : "GafferImageUI.ChannelPlugValueWidget",
			"channelPlugValueWidget:extraChannels" : IECore.StringVectorData( [ "" ] ),
			"channelPlugValueWidget:extraChannelLabels" : IECore.StringVectorData( [ "None" ] ),

			"layout:section" : "Advanced"
		},

		"depthLookupChannel" : {

			"description" :
			"""
			Defines the depth to read at when doing a multi-layer SATBlur. Source pixels in front
			of this value for each pixel will be ignored.
			""",
			"plugValueWidget:type" : "GafferImageUI.ChannelPlugValueWidget",
			"channelPlugValueWidget:extraChannels" : IECore.StringVectorData( [ "" ] ),
			"channelPlugValueWidget:extraChannelLabels" : IECore.StringVectorData( [ "None" ] ),

			"layout:section" : "Advanced"
		},

	}

)
